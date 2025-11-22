"""
Handles all file-related operations for the Flickr Stats application.

This module is responsible for determining the output CSV filename and
writing the fetched photo statistics to it. It includes error handling
for common file system issues.
"""

import csv
import os
from typing import List, Dict, Any

import ui
from config import CSV_DELIMITER, CSV_COLUMNS


def get_csv_filepath(start_date_str: str, end_date_str: str) -> str:
    """
    Determines the output CSV filename based on the date range.

    Args:
        start_date_str: The start date in 'YYYY-MM-DD' format.
        end_date_str: The end date in 'YYYY-MM-DD' format.

    Returns:
        The generated filepath for the CSV file.
    """
    if start_date_str == end_date_str:
        return f"flickr_stats_{start_date_str}.csv"
    else:
        return f"flickr_stats_{start_date_str}_to_{end_date_str}.csv"


def write_to_csv(filepath: str, data: List[Dict[str, Any]], date_str: str):
    """
    Writes a list of photo statistics to a CSV file.

    This function appends data to the file, creating it and writing the
    header row if it doesn't already exist. It includes error handling
    for file I/O operations.

    Args:
        filepath: The path to the CSV file.
        data: A list of dictionaries, where each dictionary represents a photo's stats.
        date_str: The date for which the stats were fetched.
    """
    file_exists = os.path.exists(filepath)

    try:
        with open(filepath, mode='a', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file, delimiter=CSV_DELIMITER)

            if not file_exists:
                writer.writerow(CSV_COLUMNS)

            for photo in data:
                writer.writerow([
                    date_str,
                    photo.get('id'),
                    photo.get('title'),
                    photo.get('stats', {}).get('views'),
                    photo.get('stats', {}).get('favorites'),
                    photo.get('secret'),
                    photo.get('server')
                ])
        ui.print_success(f"Data for {date_str} successfully written to {filepath}")

    except IOError as e:
        ui.print_error(f"Could not write to file {filepath}. Reason: {e}")
    except Exception as e:
        ui.print_error(f"An unexpected error occurred during file writing: {e}")
