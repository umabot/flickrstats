"""Flickr API authentication utilities.

This module provides functions to authenticate with the Flickr API using OAuth.
It handles credential loading from environment variables and manages the
authentication flow.
"""

import os
import webbrowser
import flickrapi
from dotenv import load_dotenv
from typing import Tuple


def load_credentials() -> Tuple[str, str]:
    """
    Load and validate Flickr API credentials from environment variables.

    Returns:
        Tuple of (api_key, api_secret)

    Raises:
        ValueError: If credentials are missing from environment
    """
    load_dotenv()

    api_key = os.getenv('FLICKR_API_KEY')
    api_secret = os.getenv('FLICKR_API_SECRET')

    if not api_key or not api_secret:
        raise ValueError(
            "Missing Flickr API credentials. Please ensure FLICKR_API_KEY and "
            "FLICKR_API_SECRET are set in your .env file. See README for setup instructions."
        )

    return api_key, api_secret


def authenticate_flickr(api_key: str, api_secret: str) -> flickrapi.FlickrAPI:
    """
    Authenticate with Flickr API using OAuth.

    If a valid token already exists, it will be reused. Otherwise, opens a browser
    for the user to authorize the application and provide a verifier code.

    Args:
        api_key: Flickr API key
        api_secret: Flickr API secret

    Returns:
        Authenticated FlickrAPI instance with parsed-json format
    """
    flickr = flickrapi.FlickrAPI(api_key, api_secret, format='parsed-json')

    # Only authenticate if we don't have a valid token already
    if not flickr.token_valid(perms='read'):
        print('Step 1: authenticate')

        # Get a request token
        flickr.get_request_token(oauth_callback='oob')

        # Open a browser at the authentication URL
        authorize_url = flickr.auth_url(perms='read')
        print('Opening browser for authorization...')
        webbrowser.open_new_tab(authorize_url)

        # Get the verifier code from the user
        verifier = input('Verifier code: ').strip()

        # Trade the request token for an access token
        flickr.get_access_token(verifier)
        print('Authentication successful!')

    return flickr


def get_authenticated_client() -> flickrapi.FlickrAPI:
    """
    Get an authenticated Flickr API client.

    This is a convenience function that combines credential loading and authentication.

    Returns:
        Authenticated FlickrAPI instance

    Raises:
        ValueError: If credentials are missing from environment
    """
    api_key, api_secret = load_credentials()
    return authenticate_flickr(api_key, api_secret)
