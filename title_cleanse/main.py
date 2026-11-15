"""Scheduled BigQuery photo-title cleansing function."""

import logging
from pathlib import Path


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
PROJECT_ID = "flickrstats-492309"
SQL_DIRECTORY = Path(__file__).parent


def run_cleanse(client):
    choices = (SQL_DIRECTORY / "select_title_changes.sql").read_text(
        encoding="utf-8"
    )
    script = (SQL_DIRECTORY / "cleanse_titles.sql").read_text(encoding="utf-8")
    marker = "-- TITLE_CHOICES_QUERY"
    if script.count(marker) != 1:
        raise ValueError("The cleansing SQL must contain exactly one query marker.")
    script = script.replace(marker, choices)
    return next(iter(client.query(script, location="europe-west9").result()))


def main_handler(request):
    from google.cloud import bigquery

    result = run_cleanse(bigquery.Client(project=PROJECT_ID))
    summary = (
        f"Title cleanse {result['run_id']}: "
        f"{result['candidate_count']} candidates, "
        f"{result['cleansed_count']} cleansed, "
        f"{result['updated_rows']} rows updated, "
        f"{result['no_valid_title_count']} without a valid dated title, "
        f"{result['ambiguous_count']} ambiguous."
    )
    if result["no_valid_title_count"] or result["ambiguous_count"]:
        logger.warning(
            "%s Skipped IDs without a valid dated title: %s; ambiguous IDs: %s",
            summary, result["no_valid_title_ids"], result["ambiguous_ids"],
        )
    else:
        logger.info(summary)
    return summary, 200
