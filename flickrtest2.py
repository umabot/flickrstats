# NOT WORKING
import requests
from bs4 import BeautifulSoup

# Replace these values with your authentication credentials
USERNAME = 'scasagra'
PASSWORD = 'y$7piH1aFS%N'

# Define the URL of the page to scrape
date = '2023-04-18'
url = f'https://www.flickr.com/photos/scasagra/stats/{date}/allphotos/'

# Send a POST request to the login page with your credentials
login_url = 'https://www.flickr.com/signin/'
session = requests.Session()
response = session.get(login_url)
soup = BeautifulSoup(response.content, 'html.parser')
form = soup.find('form', class_='yahoo-login-form')

data = {}
for input_tag in form.find_all('input'):
    name = input_tag.get('name')
    value = input_tag.get('value', '')
    data[name] = value
data['login'] = USERNAME
data['passwd'] = PASSWORD

response = session.post(login_url, data=data)

# Check if the login was successful
if 'logout' in response.url:
    # Use the session object to make requests to authenticated pages
    response = session.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    # Extract the photo view stats from the page
    photo_views = soup.find_all('span', class_='view-count')
    # Process the stats as needed
    for i, view_count in enumerate(photo_views):
        print(f'Photo {i+1}: {view_count.get_text()} views')
else:
    print('Login failed')
