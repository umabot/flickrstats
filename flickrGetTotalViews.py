# DO NOT USE
# this code to extract the daily stats from Flickr is WORKING
# import needed libraries
import flickrapi
import webbrowser
# import json
import pprint
import csv
import os.path

from dotenv import load_dotenv

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
# set params for API call

todaydate ='2024-01-01'

params = {
    'date': todaydate,
    }

# Call the API method
response = flickr.stats.getTotalViews(**params)
# Process the response as needed
# Print the values of the first section in the response
# total_views
# photos views
# photostream views
# collection views
# galleries views
pprint.pprint(response) # it formats the json ouput, more readable
# print(f"Stats: {response}")
print(f"Total Views: {response['stats']['total']['views']}")
print(f"Photos Views: {response['stats']['photos']['views']}")
print(f"Photostreams Views: {response['stats']['photostream']['views']}")
print(f"Collection Views: {response['stats']['collections']['views']}")
print(f"Galleries Views: {response['stats']['galleries']['views']}")