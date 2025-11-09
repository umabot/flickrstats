# DO NOT USE
import flickrapi
import pprint
import csv
import os.path
from flickr_auth import get_authenticated_client

flickr = get_authenticated_client()

datestouse = ['2024-01-01']

for todaydate in datestouse:
    params = {
        'date': todaydate,
        'per_page': 2,
    }

    response = flickr.stats.getPopularPhotos(**params)
    pprint.pprint(response)

    filepath = 'my_flickr_daily_stats3.csv'
    file_exists = os.path.exists(filepath)

    with open(filepath, mode='a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        if not file_exists:
            strheader = 'Date,Photo ID,Photo Title,Daily Views,Daily Favorites' + '\n'
            csv_file.write(strheader)

        for photo in response['photos']['photo']:
            idphoto = photo['id']
            title = photo['title']
            views = photo['stats']['views']
            favorites = photo['stats']['favorites']
            strline = f'{todaydate},{idphoto},{title},{views},{favorites}'
            csv_file.write(strline + '\n')

    if file_exists:
        print(f"Data appended to {filepath}!")
    else:
        print(f"New file created: {filepath}!")