# DO NOT USE
import flickrapi
import pprint
from flickr_auth import get_authenticated_client

flickr = get_authenticated_client()

todaydate = '2024-01-01'

params = {
    'date': todaydate,
}

response = flickr.stats.getTotalViews(**params)
pprint.pprint(response)
print(f"Total Views: {response['stats']['total']['views']}")
print(f"Photos Views: {response['stats']['photos']['views']}")
print(f"Photostreams Views: {response['stats']['photostream']['views']}")
print(f"Collection Views: {response['stats']['collections']['views']}")
print(f"Galleries Views: {response['stats']['galleries']['views']}")