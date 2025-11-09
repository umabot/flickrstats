"""
Fetches daily popular photo statistics from Flickr for a user-defined date range.

This script authenticates with the Flickr API, prompts the user for a start
and end date (inclusive), and then retrieves data for popular photos for each
day in that range. The data includes photo ID, title, views, favorites,
secret, and server.

Execution:
    python flickrGetDailyPhotoViews.py

Inputs:
    - Start Date: Prompts the user to enter the start date in YYYY-MM-DD format.
    - End Date: Prompts the user to enter the end date in YYYY-MM-DD format.
      (If the same as the start date, data for a single day is fetched).

Outputs:
    - A CSV file named dynamically based on the input dates:
        - flickr_stats_YYYY-MM-DD.csv (if start and end dates are the same)
        - flickr_stats_YYYY-MM-DD_to_YYYY-MM-DD.csv (if dates differ)
    - This CSV file contains columns: Date, Photo ID, Photo Title, Daily Views,
      Daily Favorites, Secret, Server.
    - Progress messages are printed to the console during execution.
"""

import flickrapi
import csv
import os
import time
from datetime import datetime, timedelta
from flickr_auth import get_authenticated_client

# Constants for API retry logic
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 2  # seconds
MAX_RETRY_DELAY = 60  # seconds

# Get authenticated Flickr client
flickr = get_authenticated_client()

# Function to validate date format
def validate_date(date_string: str) -> bool:
    """
    Validates if the given string is a date in 'YYYY-MM-DD' format.

    Args:
        date_string: The string to validate.

    Returns:
        True if the string matches the format, False otherwise.
    """
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def make_api_call_with_retry(flickr, method_name: str, **params):
    """
    Make Flickr API call with exponential backoff retry logic.

    Args:
        flickr: FlickrAPI instance
        method_name: API method (e.g., 'stats.getPopularPhotos')
        **params: API parameters

    Returns:
        API response dict or None if all retries failed
    """
    retry_delay = INITIAL_RETRY_DELAY

    for attempt in range(MAX_RETRIES):
        try:
            # Get the method from flickr object dynamically
            method_parts = method_name.split('.')
            method = flickr
            for part in method_parts:
                method = getattr(method, part)

            return method(**params)

        except flickrapi.exceptions.FlickrError as e:
            error_code = getattr(e, 'code', None)

            # Check if it's a rate limit error
            if error_code in [105, 'Rate Limit Exceeded']:
                if attempt < MAX_RETRIES - 1:
                    print(f"Rate limit hit. Retrying in {retry_delay} seconds... "
                          f"(Attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
                    continue

            # For other Flickr errors, raise immediately
            raise

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"Error occurred: {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
                continue
            raise

    return None


while True:
    start_date_str = input("Enter the start date (YYYY-MM-DD): ")
    if not validate_date(start_date_str):
        print("Invalid start date format. Please use YYYY-MM-DD.")
        continue

    end_date_str = input("Enter the end date (YYYY-MM-DD): ")
    if not validate_date(end_date_str):
        print("Invalid end date format. Please use YYYY-MM-DD.")
        continue

    # Validate that end_date is not before start_date
    start_date_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date_dt = datetime.strptime(end_date_str, '%Y-%m-%d')

    if end_date_dt < start_date_dt:
        print("Error: End date cannot be before start date. Please try again.")
        continue

    # Warn about future dates
    today = datetime.now().date()
    if start_date_dt.date() > today or end_date_dt.date() > today:
        print(f"Warning: You've entered future dates. Data may not be available yet.")
        confirm = input("Continue anyway? (y/n): ")
        if confirm.lower() != 'y':
            continue

    print(f"Start Date: {start_date_str}")
    print(f"End Date: {end_date_str}")
    break

# Generate the list of dates to process based on user input
datestouse = []
current_date_dt = start_date_dt
while current_date_dt <= end_date_dt:
    datestouse.append(current_date_dt.strftime('%Y-%m-%d'))
    current_date_dt += timedelta(days=1)

print("Generated list of dates to process:")
print(datestouse)

# Determine CSV filename based on whether the start and end dates are the same
if start_date_str == end_date_str:
    filepath = f"flickr_stats_{start_date_str}.csv"
else:
    filepath = f"flickr_stats_{start_date_str}_to_{end_date_str}.csv"
print(f"Output CSV file will be: {filepath}")

file_exists_for_header = os.path.exists(filepath)

for todaydate in datestouse:
    print(f"Processing data for: {todaydate}")

    params = {
        'date': todaydate,
        'per_page': 100,
        'page': 1
    }

    # Initial API call for the current date to determine total pages and photos
    try:
        response_initial = make_api_call_with_retry(flickr, 'stats.getPopularPhotos', **params)
        if not response_initial:
            print(f"Failed to fetch data for {todaydate} after {MAX_RETRIES} retries. Skipping this date.")
            continue

        total_photos_for_date = response_initial['photos']['total']
        total_pages_for_date = response_initial['photos']['pages']
        print(f"Date: {todaydate} - Total pages: {total_pages_for_date}, Total photos: {total_photos_for_date}")

        with open(filepath, mode='a', newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter='\t')

            if not file_exists_for_header:
                writer.writerow(['Date', 'Photo ID', 'Photo Title', 'Daily Views',
                                'Daily Favorites', 'Secret', 'Server'])
                file_exists_for_header = True

            page_number = 1
            while page_number <= total_pages_for_date:
                params['page'] = page_number
                response_page = make_api_call_with_retry(flickr, 'stats.getPopularPhotos', **params)

                if not response_page:
                    print(f"Failed to fetch page {page_number} for {todaydate}. Skipping remaining pages.")
                    break

                for photo in response_page['photos']['photo']:
                    idphoto = photo['id']
                    title = photo['title']
                    server = photo['server']
                    secret = photo['secret']
                    views = photo['stats']['views']
                    favorites = photo['stats']['favorites']
                    writer.writerow([todaydate, idphoto, title, views, favorites, secret, server])

                page_number += 1
        print(f"Data for {todaydate} written to {filepath}")

    except flickrapi.exceptions.FlickrError as e:
        print(f"Flickr API Error for date {todaydate}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred for date {todaydate}: {e}")

print(f"All processing complete. Data saved to {filepath}")