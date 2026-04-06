# Flickr Photo Stats

A Python tool to fetch and analyze photo statistics from your Flickr account. This tool retrieves daily popular photo data including views, favorites, and metadata for specified date ranges.

## Features

- **Date Range Queries**: Fetch statistics for single days or date ranges
- **Robust Error Handling**: Automatic retry with exponential backoff for API failures
- **Rate Limit Protection**: Built-in handling for Flickr API rate limits
- **Input Validation**: Validates date formats and ranges before processing
- **CSV Export**: Tab-delimited output for easy analysis in Excel or other tools
- **Secure Authentication**: OAuth-based authentication with token caching
- **Cloud-Native Daily Run**: Automated daily extraction via Google Cloud Functions + BigQuery

## Flickr Daily Photo Stats (`flickrGetDailyPhotoViews.py`)

**Purpose:**
This script fetches daily popular photo statistics (views, favorites, photo ID, title, secret, and server) from your Flickr account for a user-specified date range. The collected data is then saved into a CSV file.

**Prerequisites:**
*   Python 3.x
*   pip (Python package installer)

**Setup & Installation:**
1.  **Clone the repository:**
    ```bash
    git clone <repository_url> 
    cd <repository_directory>
    ```
    (Replace `<repository_url>` and `<repository_directory>` with the actual URL and local directory name).

2.  **Navigate to the repository directory** (if not already there).

3.  **Create and activate a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate 
    ```
    (On Windows, use `venv\Scripts\activate`)

4.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **API Credentials:**
    This script requires Flickr API credentials to access your account.
    *   Create a file named `.env` in the root directory of the project.
    *   Add your Flickr API key and secret to the `.env` file as follows:
        ```env
        FLICKR_API_KEY='YOUR_FLICKR_API_KEY'
        FLICKR_API_SECRET='YOUR_FLICKR_API_SECRET'
        ```
    *   **Important:** Replace `YOUR_FLICKR_API_KEY` and `YOUR_FLICKR_API_SECRET` with your actual Flickr API key and secret.
    *   The `.env` file is included in `.gitignore` to prevent accidental committing of your sensitive credentials.

**How to Run:**
1.  Ensure your virtual environment is activated if you are using one.
2.  Execute the script from the root directory of the project using:
    ```bash
    python3 flickrGetDailyPhotoViews.py
    ```
3.  The script will then prompt you to enter the date range:
    *   `Enter start date (YYYY-MM-DD):`
    *   `Enter end date (YYYY-MM-DD):` (Enter the same date as the start date if you want data for a single day).

4.  **Authentication:**
    *   If this is your first time running the script, or if your previous authentication token is invalid or has expired, the script will guide you through an OAuth authentication process:
        1.  It will print a URL to the console.
        2.  Copy and paste this URL into your web browser.
        3.  Authorize the application in Flickr.
        4.  Flickr will provide a verifier code.
        5.  Copy this verifier code and paste it back into the script when prompted: `Verifier code:`
    *   Once authenticated, the script will store the token for future sessions, so you won't need to repeat this process every time unless the token becomes invalid.

**Output:**
*   The script generates a CSV file containing the fetched statistics.
*   The filename is dynamically created based on the input dates:
    *   If the start and end dates are the same: `flickr_stats_YYYY-MM-DD.csv`
    *   If the start and end dates are different: `flickr_stats_YYYY-MM-DD_to_YYYY-MM-DD.csv`
*   **Columns in the CSV file:**
    *   `Date`: The date for which the stats were fetched (YYYY-MM-DD).
    *   `Photo ID`: The unique identifier for the photo.
    *   `Photo Title`: The title of the photo.
    *   `Daily Views`: The number of views the photo received on that date.
    *   `Daily Favorites`: The number of favorites the photo received on that date.
    *   `Secret`: The photo's secret, needed for constructing URLs.
    *   `Server`: The server ID for the photo, needed for constructing URLs.

## Troubleshooting

### Missing API Credentials Error
If you see `ValueError: Missing Flickr API credentials`:
1. Ensure you have created a `.env` file in the project root directory
2. Verify the `.env` file contains both `FLICKR_API_KEY` and `FLICKR_API_SECRET`
3. Check that the values are not wrapped in extra quotes
4. Make sure the `.env` file is in the same directory as the Python scripts

### Rate Limiting
The Flickr API has rate limits (typically 3,600 requests per hour):
- The script automatically retries with exponential backoff when rate limits are hit
- For large date ranges (months or years), consider running in smaller batches
- The script will wait and retry up to 3 times before giving up on a request

### Date Validation Errors
- Dates must be in YYYY-MM-DD format (e.g., 2024-01-15)
- End date cannot be before start date
- Future dates will trigger a warning (data may not be available yet)

### Authentication Issues
- If authentication fails repeatedly, delete the cached token file and try again
- Ensure your Flickr app has 'read' permissions
- Check that your API key and secret are still valid in the Flickr App Garden

---

## Cloud Deployment (Google Cloud Functions + BigQuery)

`main.py` contains a Cloud Function (`main_handler`) that replaces the manual
script with a fully automated, daily, serverless pipeline.

### Architecture

```
Cloud Scheduler (02:00 UTC daily)
        │  HTTP trigger
        ▼
Cloud Function: flickr-daily-extract  (main.py → main_handler)
        │
        │ 1. Fetch yesterday's stats from Flickr API
        ▼
BigQuery: flickrstats.stage_daily_extract
        │
        │ 2. MERGE (upsert on Date + Photo ID)
        ▼
BigQuery: flickrstats.flickrstats_all
        │
        │ 3. TRUNCATE stage table
        ▼
        ✓ Done
```

### BigQuery Tables

Both tables share the same schema defined in `my_schema.json`:

| Column | Type | Mode | Notes |
|---|---|---|---|
| Date | DATE | NULLABLE | Composite PK (with Photo ID) |
| Photo ID | INTEGER | NULLABLE | Composite PK |
| Photo Title | STRING | NULLABLE | |
| Daily Views | INTEGER | NULLABLE | Updated on match |
| Daily Favorites | INTEGER | NULLABLE | Updated on match |
| Secret | STRING | NULLABLE | Used to construct URLs |
| Server | INTEGER | NULLABLE | Used to construct URLs |
| Link | STRING | NULLABLE | Full Flickr photo page URL |
| thumbnail | STRING | NULLABLE | 75 x 75 px square-crop URL |

Create both tables in the Google Cloud Console using `my_schema.json`:
```
flickrstats-492309.flickrstats.flickrstats_all
flickrstats-492309.flickrstats.stage_daily_extract
```

### One-Time Local Setup — Obtain OAuth Tokens

The Cloud Function uses pre-obtained OAuth tokens (no browser).  Run the
interactive script **once** on your local machine to generate them:

```bash
python3 flickrGetDailyPhotoViews.py
```

After authorising in the browser, flickrapi caches the token locally (usually
in `~/.flickr/`).  Note down the `oauth_token` and `oauth_token_secret` values
from that file.

### Store Secrets in Cloud Secret Manager

In the Google Cloud Console, create four secrets:

| Secret name | Value |
|---|---|
| `flickr-api-key` | Your Flickr API key |
| `flickr-api-secret` | Your Flickr API secret |
| `flickr-oauth-token` | OAuth access token from local run |
| `flickr-oauth-token-secret` | OAuth access token secret from local run |

Grant the Cloud Function's service account the role
`roles/secretmanager.secretAccessor` on each secret.

### Deploy via Cloud Build (CI/CD)

`cloudbuild.yaml` automates deployment whenever you push to `main`.

**One-time setup in Google Cloud Console:**

1. Enable APIs: **Cloud Build**, **Cloud Functions**, **Secret Manager**, **BigQuery**.
2. Create a service account `flickr-extractor@flickrstats-492309.iam.gserviceaccount.com`
   and grant it:
   - `roles/bigquery.dataEditor` on the `flickrstats` dataset
   - `roles/bigquery.jobUser` on the project
   - `roles/secretmanager.secretAccessor` on each secret
3. Grant the **Cloud Build** service account:
   - `roles/cloudfunctions.developer`
   - `roles/iam.serviceAccountUser` (to act as the function's service account)
4. In **Cloud Build → Triggers**, connect your GitHub repository and create a
   trigger on push to `main` using the `cloudbuild.yaml` configuration file.

### Configure Cloud Scheduler

In the Google Cloud Console, create a Cloud Scheduler job:

| Setting | Value |
|---|---|
| Frequency | `0 2 * * *` (02:00 UTC daily) |
| Target type | HTTP |
| URL | The Cloud Function HTTPS URL |
| Auth header | Add OIDC token — service account: `flickr-extractor@…` |

### Manual Invocation

To trigger the function manually (e.g. for testing):

```bash
gcloud functions call flickr-daily-extract --region=us-central1
```

You can also test the deployed HTTP endpoint with an optional JSON payload.
If `Date` is supplied in `YYYY-MM-DD` format, the function will use that date;
otherwise it falls back to **yesterday**. Any other payload fields are ignored.

```bash
curl -X POST "https://flickr-daily-extract-781796249121.europe-west9.run.app" \
  -H "Authorization: bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "Date": "2026-04-01"
  }'
```

## Project Structure

```
flickrstats/
├── main.py                      # Cloud Function entry point
├── flickrGetDailyPhotoViews.py  # Local interactive script
├── flickr_auth.py               # Shared authentication module (local + cloud)
├── my_schema.json               # BigQuery table schema
├── requirements.txt             # Python dependencies
├── cloudbuild.yaml              # CI/CD: GitHub → Cloud Build → Cloud Functions
├── README.md                    # This file
├── .env                         # API credentials (not in git)
├── .gitignore                   # Git ignore patterns
├── archive/                     # Deprecated/experimental scripts
│   ├── README.md
│   ├── flickrDailyStats.py
│   ├── flickrGetTotalViews.py
│   ├── flickrGetTotalPhotoViews.py
│   └── iterateDates.py
├── notebooks/                   # Jupyter exploration notebooks
│   ├── flickrStats.ipynb
│   └── flickrTest.ipynb
└── examples/                    # Example API responses
    ├── flick_output.json
    └── response.json
```

## Technical Details

### API Configuration
- Default page size: 100 photos per request (max: 500)
- Retry attempts: 3 with exponential backoff (2s, 4s, 8s delays)
- CSV delimiter: Tab character for better compatibility with titles containing commas

### Error Handling
The script includes comprehensive error handling:
- Network failures: Automatic retry with exponential backoff
- Rate limiting: Detects and waits before retrying
- Invalid dates: Validates format and logical consistency
- Missing credentials: Clear error messages with setup guidance

## Author & Project Notes

**Data Backup & Personal Documentation (Author-Specific):**
*   The author periodically saves a full set of generated data to Google Drive (personal account, file `Flickr Stats v2`).
*   Additional project documentation and notes by the author may be found in their Obsidian vault (note titled `Flickr Photo Project - my stats`).

**Repository Notes:**
*   The `.gitignore` file is configured to exclude sensitive files (`.env`), generated data (`*.csv`), and Python artifacts (`venv/`, `__pycache__/`).
*   Deprecated scripts are preserved in the `archive/` directory for reference.