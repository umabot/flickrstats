# NOT WORKING

# Authentication in Requests with HTTPBasicAuth
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup

auth = HTTPBasicAuth('scasagra', 'y$7piH1aFS%Npass')

session = requests.get('https://identity.flickr.com/', auth=auth)
print(session)
# Use the session object to make requests to authenticated pages
data_url = 'https://flickr.com/photos/scasagra/stats/2023-04-18/allphotos/'

session2 = requests.get(data_url,auth=('scasagra', 'y$7piH1aFS%Npass'))

# Process the response as needed
soup = BeautifulSoup(session2.content, 'html.parser')

title = soup.title.string

print(title)