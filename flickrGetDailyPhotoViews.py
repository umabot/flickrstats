"""
Main script for the Flickr Stats application.

This script uses the 'click' library to provide a command-line interface for
fetching daily popular photo statistics from Flickr. It orchestrates the user
interface, API handling, and file writing modules.

Execution Examples:
    - Interactive mode (prompts for dates):
        python flickrGetDailyPhotoViews.py
    - Command-line mode:
        python flickrGetDailyPhotoViews.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD
"""

from datetime import datetime, timedelta
from typing import Tuple

import click
import flickrapi

import api_handler
import file_handler
import ui
from config import DATE_FORMAT
from flickr_auth import get_authenticated_client


def _validate_date_format(
    ctx: click.Context, param: click.Parameter, value: str
) -> datetime:
    """Callback to validate date format for click options."""
    if not value:
        return None
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        raise click.BadParameter("Date must be in YYYY-MM-DD format.")


def _generate_date_list(start_date: datetime, end_date: datetime) -> list[str]:
    """Generates a list of date strings from a start to an end date."""
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime(DATE_FORMAT))
        current_date += timedelta(days=1)
    return dates


@click.command()
@click.option(
    "--start-date",
    prompt="Enter the start date (YYYY-MM-DD)",
    help="The start date for fetching stats.",
    callback=_validate_date_format,
)
@click.option(
    "--end-date",
    prompt="Enter the end date (YYYY-MM-DD)",
    help="The end date for fetching stats.",
    callback=_validate_date_format,
)
def main(start_date: datetime, end_date: datetime):
    """
    Main function to run the Flickr stats fetching process.
    """
    # Validate that end_date is not before start_date
    if end_date < start_date:
        ui.print_error("End date cannot be before start date.")
        return

    # Warn about future dates
    today = datetime.now()
    if start_date > today or end_date > today:
        if not click.confirm(
            click.style(
                "You've entered future dates. Data may not be available yet. Continue anyway?",
                fg="yellow",
            )
        ):
            return

    start_date_str = start_date.strftime(DATE_FORMAT)
    end_date_str = end_date.strftime(DATE_FORMAT)

    ui.print_progress(f"Processing dates from {start_date_str} to {end_date_str}")

    try:
        # Authenticate with Flickr
        flickr: flickrapi.FlickrAPI = get_authenticated_client()

        # Determine the output file path
        filepath = file_handler.get_csv_filepath(start_date_str, end_date_str)
        ui.print_progress(f"Output CSV file will be: {filepath}")

        # Generate and display the list of dates to process
        dates_to_process = _generate_date_list(start_date, end_date)
        ui.print_progress("Generated list of dates to process:")
        ui.print_progress(str(dates_to_process))

        # Process each date
        for date_str in dates_to_process:
            photos = api_handler.fetch_popular_photos_for_date(flickr, date_str)

            if photos is not None and photos:
                file_handler.write_to_csv(filepath, photos, date_str)
            elif photos is None:
                ui.print_error(f"Skipping date {date_str} due to an API error.")

        ui.print_success(f"All processing complete. Data saved to {filepath}")

    except ValueError as ve:
        # Catches credential loading errors
        ui.print_error(str(ve))
    except Exception as e:
        ui.print_error(f"An unexpected error occurred in the main process: {e}")


if __name__ == "__main__":
    main()
