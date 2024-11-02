# NOT WORKING 

import requests
from bs4 import BeautifulSoup

# Replace these values with your authentication credentials
USERNAME = 'scasagra@gmail.com'
PASSWORD = 'y$7piH1aFS%N'

# Send a POST request to the login page with your credentials
login_url = 'https://identity.flickr.com/'
session = requests.Session()
response = session.post(login_url, data={'username': USERNAME, 'password': PASSWORD})

# Check if the login was successful
if response.status_code == 200:
    # Use the session object to make requests to authenticated pages
    data_url = 'https://flickr.com/photos/scasagra/stats/2023-04-17/allphotos/'
    data_response = session.get(data_url)
    # Process the response as needed
    soup = BeautifulSoup(data_response.content, 'html.parser')
    # Extract the table from the page
table = soup.find('table')

# Extract the rows from the table
rows = table.find_all('tr')

# Loop over the rows and extract the data from each column
for row in rows:
    columns = row.find_all('td')
    if columns:
        column_data = [column.get_text() for column in columns]
        # Do something with the column data, e.g. print it
        print(column_data)
else:
    print('Login failed')
