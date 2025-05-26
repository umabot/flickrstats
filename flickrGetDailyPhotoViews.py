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
# this code to extract the daily stats from Flickr is WORKING

import flickrapi
import webbrowser
import json
import csv
import os.path
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Get API credentials from environment variables
api_key = os.getenv('FLICKR_API_KEY')
api_secret = os.getenv('FLICKR_API_SECRET')

flickr = flickrapi.FlickrAPI(api_key, api_secret,format='parsed-json')
# flickr = flickrapi.FlickrAPI(api_key, api_secret) not including format gives error TypeError: 'str' object cannot be interpreted as an integer
# the response is in xml format and we need another way to parse the data

print('Step 1: authenticate')

# Only do this if we don't have a valid token already
if not flickr.token_valid(perms='read'):

    # Get a request token
    flickr.get_request_token(oauth_callback='oob')

    # Open a browser at the authentication URL. Do this however
    # you want, as long as the user visits that URL.
    authorize_url = flickr.auth_url(perms='read')
    webbrowser.open_new_tab(authorize_url)

    # Get the verifier code from the user. Do this however you
    # want, as long as the user gives the application the code.
    verifier = str(input('Verifier code: '))

    # Trade the request token for an access token
    flickr.get_access_token(verifier)

# print('Step 2: use Flickr')

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

while True:
    start_date_str = input("Enter the start date (YYYY-MM-DD): ")
    if not validate_date(start_date_str):
        print("Invalid start date format. Please use YYYY-MM-DD.")
        continue

    end_date_str = input("Enter the end date (YYYY-MM-DD): ")
    if not validate_date(end_date_str):
        print("Invalid end date format. Please use YYYY-MM-DD.")
        continue
    
    # Further validation can be added here, e.g., end_date >= start_date
    # For now, just confirming the input
    print(f"Start Date: {start_date_str}")
    print(f"End Date: {end_date_str}")
    break

from datetime import timedelta

# The following processing loop will be adapted in the next step.
# For now, we are just confirming date input.

# Generate the list of dates to process based on user input
datestouse = []
start_date_dt = datetime.strptime(start_date_str, '%Y-%m-%d') # Convert string to datetime object
end_date_dt = datetime.strptime(end_date_str, '%Y-%m-%d')   # Convert string to datetime object

current_date_dt = start_date_dt
# Loop from start date to end date (inclusive)
while current_date_dt <= end_date_dt:
    datestouse.append(current_date_dt.strftime('%Y-%m-%d')) # Add formatted date string to list
    current_date_dt += timedelta(days=1) # Increment current date by one day

print("Generated list of dates to process:")
print(datestouse)

# Determine CSV filename based on whether the start and end dates are the same
if start_date_str == end_date_str:
    filepath = f"flickr_stats_{start_date_str}.csv"
else:
    filepath = f"flickr_stats_{start_date_str}_to_{end_date_str}.csv"
print(f"Output CSV file will be: {filepath}")

# Check if the CSV file already exists. This is used to decide whether to write the header row.
# The header should only be written if the file is being created for the first time during this script run.
file_exists_for_header = os.path.exists(filepath)

# Main loop: Iterate through each date in the generated 'datestouse' list
for todaydate in datestouse:
    print(f"Processing data for: {todaydate}")
    
    # Parameters for the Flickr API call for the current date
    params = {
        'date': todaydate,
        'per_page': 100,  # Flickr API default, max is 500, but 100 is common
        'page': 1         # Start with page 1
    }

    # Initial API call for the current date to determine total pages and photos
    try:
        response_initial = flickr.stats.getPopularPhotos(**params)
        # Extract total number of photos and pages from the initial response
        total_photos_for_date = response_initial['photos']['total']
        total_pages_for_date = response_initial['photos']['pages']
        print(f"Date: {todaydate} - Total pages: {total_pages_for_date}, Total photos: {total_photos_for_date}")

        # Open the CSV file in append mode ('a').
        # This creates the file if it doesn't exist, or appends to it if it does.
        # 'newline=''' prevents blank rows from being written in the CSV on Windows.
        with open(filepath, mode='a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            
            # Write the header row only if the file did not exist before this script started processing.
            if not file_exists_for_header:
                strheader = 'Date' + '\t' + 'Photo ID' + '\t' + 'Photo Title' + '\t' + 'Daily Views' + '\t' + 'Daily Favorites' + '\t' + 'Secret' + '\t'+ 'Server' + '\n'
                csv_file.write(strheader)
                file_exists_for_header = True # Set flag to True so header isn't written again for subsequent dates

            # Pagination loop: Iterate through all pages of results for the current date
            page_number = 1
            while page_number <= total_pages_for_date:
                params['page'] = page_number # Update the page number for the next API call
                response_page = flickr.stats.getPopularPhotos(**params) # Fetch the current page of results
                
                # Extract data for each photo on the current page
                for photo in response_page['photos']['photo']:
                    idphoto = photo['id']
                    title = photo['title']
                    server = photo['server'] # Needed to construct photo URLs if desired
                    secret = photo['secret'] # Needed to construct photo URLs if desired
                    views = photo['stats']['views']
                    favorites = photo['stats']['favorites']
                    # Prepare data row as a tab-separated string
                    strline = f'{todaydate}\t{idphoto}\t{title}\t{views}\t{favorites}\t{secret}\t{server}'
                    csv_file.write(strline + '\n') # Write the row to the CSV
                
                page_number += 1 # Move to the next page
        print(f"Data for {todaydate} written to {filepath}")

    except flickrapi.exceptions.FlickrError as e:
        # Handle specific Flickr API errors (e.g., rate limits, invalid parameters)
        print(f"Flickr API Error for date {todaydate}: {e}")
    except Exception as e:
        # Handle any other unexpected errors during processing for a specific date
        print(f"An unexpected error occurred for date {todaydate}: {e}")

print(f"All processing complete. Data saved to {filepath}")