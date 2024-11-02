# NOT WORKING
import requests
from bs4 import BeautifulSoup

# Replace YOUR_API_KEY with your Flickr API key
API_KEY = '992c50d09d7a04d5877798a549aa6bc6'

# Set up the URL for the stats page
url = 'http://www.flickr.com/photos/{username}/stats/{page}/'

# Replace {username} and {page} with the appropriate values
username = 'scasagra'
page = '2023-04-17/allphotos'

# Construct the full URL with API key and parameters
params = {'api_key': API_KEY}
full_url = url.format(username=username, page=page) + '?' + \
           '&'.join(['{}={}'.format(key, value) for key, value in params.items()])

print(full_url)

# Send the GET request and create a BeautifulSoup object
response = requests.get(full_url)
soup = BeautifulSoup(response.content, 'html.parser')

print(soup.title)

# Extract the statistics from the soup object
# views = soup.find('span', {'class': 'stats-views'}).text
# comments = soup.find('span', {'class': 'stats-comments'}).text
# favorites = soup.find('span', {'class': 'stats-favorites'}).text

# Print the statistics
# print 'Views:', views
# print 'Comments:', comments
# print 'Favorites:', favorites