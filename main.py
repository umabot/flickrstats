"""Google Cloud Function: Flickr Daily Stats Extractor.

This module is the entry point for a Cloud Function that runs daily (triggered
by Cloud Scheduler) and performs the following steps:

1. Calculates the previous calendar day automatically.
2. Authenticates with the Flickr API using OAuth tokens stored in Secret Manager
   (surfaced as environment variables by the Cloud Functions runtime).
3. Fetches all popular photo statistics for that day via the Flickr Stats API.
4. Constructs the photo Link and Thumbnail URLs from the API response fields.
5. Streams the rows into the BigQuery staging table
   (flickrstats-492309.flickrstats.stage_daily_extract).
6. Executes a MERGE statement to upsert the staged rows into the main table
   (flickrstats-492309.flickrstats.flickrstats_all):
   - MATCHED on (Date, Photo ID) → updates Daily Views, Daily Favorites,
     and updated_at.
   - NOT MATCHED → inserts the full row and sets loaded_at/updated_at.
7. Truncates the staging table to prepare it for the next run.

Environment variables required (recommended via Cloud Secret Manager):
    FLICKR_API_KEY            – Flickr application API key.
    FLICKR_API_SECRET         – Flickr application API secret.
    FLICKR_OAUTH_TOKEN        – OAuth access token (obtained during one-time
                                browser authorisation on the local machine).
    FLICKR_OAUTH_TOKEN_SECRET – OAuth access token secret.

Deployment:
    Deployed automatically by Cloud Build on every push to main (see
    cloudbuild.yaml).  The Cloud Scheduler job at 02:00 UTC calls the HTTPS
    endpoint to kick off the daily run.
"""

import logging
import os
import time
from datetime import datetime, timedelta, timezone

import flickrapi
from google.cloud import bigquery

from flickr_auth import get_cloud_authenticated_client

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GCP_PROJECT_ID = "flickrstats-492309"
BQ_DATASET = "flickrstats"
BQ_STAGE_TABLE = f"{GCP_PROJECT_ID}.{BQ_DATASET}.stage_daily_extract"
BQ_TARGET_TABLE = f"{GCP_PROJECT_ID}.{BQ_DATASET}.flickrstats_all"

FLICKR_PAGE_SIZE = 100  # Photos per page (max 500)
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 2   # seconds
MAX_RETRY_DELAY = 60       # seconds
DATE_FORMAT = "%Y-%m-%d"

# Flickr URL templates (standard static-image CDN)
PHOTO_URL_TEMPLATE = "https://www.flickr.com/photos/{owner}/{photo_id}"
THUMBNAIL_URL_TEMPLATE = (
    "https://live.staticflickr.com/{server}/{photo_id}_{secret}_q.jpg"
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Flickr helpers
# ---------------------------------------------------------------------------

def make_api_call_with_retry(flickr_client, method_name: str, **params):
    """Make a Flickr API call with exponential-backoff retry.

    Args:
        flickr_client: Authenticated FlickrAPI instance.
        method_name:   Dot-separated method name (e.g. 'stats.getPopularPhotos').
        **params:      Keyword arguments forwarded to the API method.

    Returns:
        Parsed-JSON API response, or None if all retries were exhausted.

    Raises:
        flickrapi.exceptions.FlickrError: For non-rate-limit Flickr errors.
        Exception: For persistent non-Flickr errors after all retries.
    """
    retry_delay = INITIAL_RETRY_DELAY

    for attempt in range(MAX_RETRIES):
        try:
            method = flickr_client
            for part in method_name.split("."):
                method = getattr(method, part)
            return method(**params)

        except flickrapi.exceptions.FlickrError as exc:
            if getattr(exc, "code", None) in [105, "Rate Limit Exceeded"]:
                if attempt < MAX_RETRIES - 1:
                    logger.warning(
                        "Rate limit hit. Retrying in %ds (attempt %d/%d).",
                        retry_delay, attempt + 1, MAX_RETRIES,
                    )
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
                    continue
            raise

        except Exception as exc:  # noqa: BLE001
            if attempt < MAX_RETRIES - 1:
                logger.warning(
                    "Error: %s. Retrying in %ds (attempt %d/%d).",
                    exc, retry_delay, attempt + 1, MAX_RETRIES,
                )
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
                continue
            raise

    return None


def fetch_flickr_stats(flickr_client, date: str) -> list:
    """Fetch all popular photo statistics for a given date from Flickr.

    Iterates over all pages returned by stats.getPopularPhotos and builds
    the list of row dictionaries matching the BigQuery schema (my_schema.json),
    including the constructed Link and Thumbnail URLs.

    Args:
        flickr_client: Authenticated FlickrAPI instance.
        date:          Date string in YYYY-MM-DD format.

    Returns:
        List of row dicts ready for BigQuery insertion.
    """
    rows = []
    params = {"date": date, "per_page": FLICKR_PAGE_SIZE, "page": 1}

    try:
        initial = make_api_call_with_retry(
            flickr_client, "stats.getPopularPhotos", **params
        )
        if not initial:
            logger.error("Failed to fetch initial page for %s.", date)
            return rows

        total_pages = initial["photos"]["pages"]
        logger.info(
            "Date: %s — pages: %d, total photos: %s",
            date, total_pages, initial["photos"]["total"],
        )

        for page in range(1, total_pages + 1):
            params["page"] = page
            response = make_api_call_with_retry(
                flickr_client, "stats.getPopularPhotos", **params
            )
            if not response:
                logger.error("Failed to fetch page %d for %s. Stopping.", page, date)
                break

            for photo in response["photos"]["photo"]:
                photo_id = photo["id"]
                owner = photo.get("owner", "")
                rows.append(
                    {
                        "Date": date,
                        "Photo ID": int(photo_id),
                        "Photo Title": photo["title"],
                        "Daily Views": int(photo["stats"]["views"]),
                        "Daily Favorites": int(photo["stats"]["favorites"]),
                        "Secret": photo["secret"],
                        "Server": int(photo["server"]),
                        "Link": PHOTO_URL_TEMPLATE.format(
                            owner=owner, photo_id=photo_id
                        ),
                        "thumbnail": THUMBNAIL_URL_TEMPLATE.format(
                            server=photo["server"],
                            photo_id=photo_id,
                            secret=photo["secret"],
                        ),
                    }
                )

    except flickrapi.exceptions.FlickrError as exc:
        logger.error("Flickr API error for %s: %s", date, exc)
    except Exception as exc:
        logger.error("Unexpected error for %s: %s", date, exc)
        raise

    return rows


# ---------------------------------------------------------------------------
# BigQuery helpers
# ---------------------------------------------------------------------------

def load_to_stage(bq_client: bigquery.Client, rows: list) -> None:
    """Stream rows into the BigQuery staging table.

    Args:
        bq_client: Authenticated BigQuery client.
        rows:      List of row dicts to insert.

    Raises:
        RuntimeError: If the BigQuery streaming insert returns errors.
    """
    if not rows:
        logger.info("No rows to load into the staging table.")
        return

    errors = bq_client.insert_rows_json(BQ_STAGE_TABLE, rows)
    if errors:
        raise RuntimeError(f"BigQuery insert errors: {errors}")

    logger.info("Inserted %d rows into %s.", len(rows), BQ_STAGE_TABLE)


def run_merge(bq_client: bigquery.Client) -> None:
    """Upsert staged rows into the main table using a BigQuery MERGE.

    Composite PK: Date + Photo ID
    - MATCHED     → update Daily Views, Daily Favorites, and updated_at.
    - NOT MATCHED → insert the full row and set loaded_at/updated_at.

    Args:
        bq_client: Authenticated BigQuery client.
    """
    merge_sql = f"""
    MERGE `{BQ_TARGET_TABLE}` T
    USING `{BQ_STAGE_TABLE}` S
      ON T.Date = S.Date AND T.`Photo ID` = S.`Photo ID`
    WHEN MATCHED THEN
      UPDATE SET
        T.`Daily Views`     = S.`Daily Views`,
        T.`Daily Favorites` = S.`Daily Favorites`,
        T.updated_at        = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
      INSERT (
        `Date`, `Photo ID`, `Photo Title`, `Daily Views`, `Daily Favorites`,
        `Secret`, `Server`, `Link`, `thumbnail`, `loaded_at`, `updated_at`
      )
      VALUES (
        S.Date, S.`Photo ID`, S.`Photo Title`, S.`Daily Views`, S.`Daily Favorites`,
        S.Secret, S.Server, S.Link, S.thumbnail, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
      )
    """
    query_job = bq_client.query(merge_sql)
    query_job.result()
    logger.info("MERGE completed successfully.")


def truncate_stage(bq_client: bigquery.Client) -> None:
    """Truncate the staging table after a successful MERGE.

    Args:
        bq_client: Authenticated BigQuery client.
    """
    truncate_sql = f"TRUNCATE TABLE `{BQ_STAGE_TABLE}`"
    query_job = bq_client.query(truncate_sql)
    query_job.result()
    logger.info("Staging table %s truncated.", BQ_STAGE_TABLE)


def resolve_requested_date(request) -> str:
    """Resolve the date to process from the optional request JSON payload.

    Uses the payload field `Date` when present and valid in YYYY-MM-DD format.
    Otherwise, falls back to yesterday in UTC. Any other payload keys are
    ignored.

    Args:
        request: Flask Request object.

    Returns:
        Date string in YYYY-MM-DD format.
    """
    default_date = (
        datetime.now(timezone.utc) - timedelta(days=1)
    ).strftime(DATE_FORMAT)

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        logger.info("No JSON payload supplied. Using default date: %s", default_date)
        return default_date

    requested_date = payload.get("Date")
    if requested_date is None:
        logger.info("No Date provided in payload. Using default date: %s", default_date)
        return default_date

    if not isinstance(requested_date, str):
        logger.warning(
            "Ignoring non-string Date value %r. Using default date: %s",
            requested_date,
            default_date,
        )
        return default_date

    try:
        resolved_date = datetime.strptime(requested_date, DATE_FORMAT).strftime(
            DATE_FORMAT
        )
        logger.info("Using requested date from payload: %s", resolved_date)
        return resolved_date
    except ValueError:
        logger.warning(
            "Ignoring invalid Date value %r. Expected format %s. Using default "
            "date: %s",
            requested_date,
            DATE_FORMAT,
            default_date,
        )
        return default_date


# ---------------------------------------------------------------------------
# Cloud Function entry point
# ---------------------------------------------------------------------------

def main_handler(request):
    """HTTP Cloud Function entry point.

    Intended to be called by Cloud Scheduler once per day. Processes the
    previous calendar day's Flickr stats by default and upserts them into
    BigQuery.

    When manually testing the function, the request JSON payload may include
    an optional `Date` field in YYYY-MM-DD format. If it is missing or invalid,
    the function falls back to yesterday in UTC.

    Args:
        request: Flask Request object with an optional JSON payload.

    Returns:
        Tuple of (message, HTTP status code).
    """
    processing_date = resolve_requested_date(request)
    logger.info("Starting Flickr stats extraction for: %s", processing_date)

    flickr_client = get_cloud_authenticated_client()
    rows = fetch_flickr_stats(flickr_client, processing_date)

    if not rows:
        msg = f"No data returned from Flickr for {processing_date}."
        logger.warning(msg)
        return msg, 200

    bq_client = bigquery.Client(project=GCP_PROJECT_ID)
    load_to_stage(bq_client, rows)
    run_merge(bq_client)
    truncate_stage(bq_client)

    msg = f"Successfully processed {len(rows)} rows for {processing_date}."
    logger.info(msg)
    return msg, 200
