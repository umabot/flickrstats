import flickrapi
from flickr_auth import get_authenticated_client

flickr = get_authenticated_client()

todaydate = '2024-01-01'

params = {
    'date': todaydate,
}

response = flickr.stats.getPopularPhotos(**params)
print(f"Page: {response['photos']['page']}")
print(f"Total pages: {response['photos']['pages']}")
print(f"Photos per page: {response['photos']['perpage']}")
print(f"Total photos: {response['photos']['total']}")