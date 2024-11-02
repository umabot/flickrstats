# this code to extract the daily stats from Flickr is WORKING

import flickrapi
import webbrowser
# json library is not needed
# import json
import pprint
import csv
import os.path

api_key = u'992c50d09d7a04d5877798a549aa6bc6'
api_secret = u'0fb9aa30fc229463'

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

# define an array with all the dates to use
# datestouse = ['2023-05-17', '2023-05-18', '2023-05-19', '2023-05-20', '2023-05-21', '2023-05-22', '2023-05-23', '2023-05-24', '2023-05-25', '2023-05-26', '2023-05-27', '2023-05-28', '2023-05-29', '2023-05-30', '2023-05-31']
# datestouse = ['2023-06-01','2023-06-02','2023-06-03','2023-06-04','2023-06-05','2023-06-06','2023-06-07','2023-06-08','2023-06-09','2023-06-10','2023-06-11','2023-06-12','2023-06-13','2023-06-14','2023-06-15','2023-06-16','2023-06-17','2023-06-18','2023-06-19','2023-06-20','2023-06-21','2023-06-22','2023-06-23','2023-06-24','2023-06-25','2023-06-26','2023-06-27','2023-06-28','2023-06-29','2023-06-30']
# datestouse = ['2023-07-01','2023-07-02','2023-07-03','2023-07-04','2023-07-05','2023-07-06','2023-07-07','2023-07-08','2023-07-09','2023-07-10','2023-07-11','2023-07-12','2023-07-13','2023-07-14','2023-07-15','2023-07-16','2023-07-17','2023-07-18','2023-07-19','2023-07-20','2023-07-21','2023-07-22','2023-07-23','2023-07-24','2023-07-25','2023-07-26','2023-07-27','2023-07-28','2023-07-29','2023-07-30','2023-07-31']
# datestouse = ['2023-08-10','2023-08-11','2023-08-12','2023-08-13','2023-08-14','2023-08-15','2023-08-16','2023-08-17','2023-08-18','2023-08-19','2023-08-20','2023-08-21','2023-08-22','2023-08-23','2023-08-24','2023-08-25','2023-08-26','2023-08-27','2023-08-28','2023-08-29','2023-08-30','2023-08-31']
# datestouse = ['2023-09-01','2023-09-02','2023-09-03','2023-09-04','2023-09-05','2023-09-06','2023-09-07','2023-09-08','2023-09-09','2023-09-10','2023-09-11','2023-09-12','2023-09-13','2023-09-14','2023-09-15','2023-09-16','2023-09-17','2023-09-18','2023-09-19','2023-09-20','2023-09-21','2023-09-22','2023-09-23','2023-09-24','2023-09-25','2023-09-26','2023-09-27','2023-09-28','2023-09-29','2023-09-30']
# datestouse = ['2023-10-01','2023-10-02','2023-10-03','2023-10-04','2023-10-05','2023-10-06','2023-10-07','2023-10-08','2023-10-09','2023-10-10','2023-10-11','2023-10-12','2023-10-13','2023-10-14','2023-10-15','2023-10-16','2023-10-17','2023-10-18','2023-10-19','2023-10-20','2023-10-21','2023-10-22','2023-10-23','2023-10-24','2023-10-25','2023-10-26','2023-10-27','2023-10-28','2023-10-29','2023-10-30','2023-10-31']
# datestouse = ['2023-11-01','2023-11-02','2023-11-03','2023-11-04','2023-11-05','2023-11-06','2023-11-07','2023-11-08','2023-11-09','2023-11-10','2023-11-11','2023-11-12','2023-11-13','2023-11-14','2023-11-15','2023-11-16','2023-11-17','2023-11-18','2023-11-19','2023-11-20','2023-11-21','2023-11-22','2023-11-23','2023-11-24','2023-11-25','2023-11-26','2023-11-27','2023-11-28','2023-11-29','2023-11-30']
# datestouse = ['2023-12-01','2023-12-02','2023-12-03','2023-12-04','2023-12-05','2023-12-06','2023-12-07','2023-12-08','2023-12-09','2023-12-10','2023-12-11','2023-12-12','2023-12-13','2023-12-14','2023-12-15','2023-12-16','2023-12-17','2023-12-18','2023-12-19','2023-12-20','2023-12-21','2023-12-22','2023-12-23','2023-12-24','2023-12-25','2023-12-26','2023-12-27','2023-12-28','2023-12-29','2023-12-30']
datestouse = ['2024-01-01']

# Define the parameters for the API method call
# and set the start date

for todaydate in datestouse:
    #todaydate = '2023-05-16'

    params = {
        'dates': todaydate,
        'per_page': 2,
    }

    # Call the API method
    response = flickr.stats.getPopularPhotos(**params)
    pprint.pprint(response)
    # json_str = json.dumps(response, indent=4)

    # Process the response as needed
    # print(type(response))
    # print(f"Total pages: {response['photos']['pages']}")
    # print(f"Total photos: {response['photos']['total']}")
    # print(json_str)
    # print(params)

    # Path to CSV file
    filepath = 'my_flickr_daily_stats3.csv'

    # Check if file exists
    file_exists = os.path.exists(filepath)

    # Open the file in append mode
    # If file does not exist, create it
    # If file exists, append to it
    with open(filepath, mode='a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        if not file_exists:
            # Write the header row when creating a new file
            strheader = 'Date,Photo ID,Photo Title,Daily Views,Daily Favorites' + '\n'
            csv_file.write(strheader) 

        # Write the data rows
        for photo in response['photos']['photo']:
            idphoto = photo['id']
            title = photo['title']
            views = photo['stats']['views']
            favorites = photo['stats']['favorites']
            # strline = todaydate + "," + idphoto + "," +  title + "," +  str(views) + "," +  str(favorites)
            # print(f'ID: {idphoto} - Title: {title} - Views: {views} - Favorites: {favorites}')
            strline = f'{todaydate},{idphoto},{title},{views},{favorites}'
            csv_file.write(strline + '\n')

    # Print confirmation message
    if file_exists:
        print(f"Data appended to {filepath}!")
    else:
        print(f"New file created: {filepath}!")

    csv_file.close()