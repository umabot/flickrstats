# Activate the virtual environment
source ~/development/venvs/flickrscrap/bin/activate

# Run your script
python flickrGetDailyPhotoViews.py

The script will connect to my Flickr account and download for each day in the variable `datestouse` the views and favorites for each photo in that day.

All the stats are added to the file `my_flickr_daily_stats_allpages_secretserver.csv`

A full set of data is saved in my Google Drive, personal account, file `Flickr Stats v2`