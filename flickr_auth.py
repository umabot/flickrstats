"""Flickr API authentication utilities.

This module provides functions to authenticate with the Flickr API using OAuth.
It handles credential loading from environment variables and manages the
authentication flow.

Two authentication modes are supported:

* **Interactive** (``get_authenticated_client``): Opens a browser for the user
  to authorise the app and stores the resulting token locally.  Use this when
  running the script on a local machine for the first time.

* **Non-interactive / Cloud** (``get_cloud_authenticated_client``): Reads an
  already-obtained OAuth access token from environment variables
  (``FLICKR_OAUTH_TOKEN`` and ``FLICKR_OAUTH_TOKEN_SECRET``).  Use this for
  headless environments such as Google Cloud Functions where browser interaction
  is impossible.  The token is injected at runtime via Cloud Secret Manager.
"""

import os
import webbrowser
import flickrapi
from dotenv import load_dotenv
from flickrapi.auth import FlickrAccessToken
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


def get_cloud_authenticated_client() -> flickrapi.FlickrAPI:
    """Get an authenticated Flickr API client for headless / cloud environments.

    Instead of launching a browser, this function reconstructs the OAuth
    session from an access token and token secret that were previously obtained
    via ``get_authenticated_client()`` on a local machine and stored in
    Google Cloud Secret Manager (surfaced as environment variables by the
    Cloud Functions runtime).

    Required environment variables:
        FLICKR_API_KEY            – Flickr application API key.
        FLICKR_API_SECRET         – Flickr application API secret.
        FLICKR_OAUTH_TOKEN        – OAuth access token.
        FLICKR_OAUTH_TOKEN_SECRET – OAuth access token secret.

    Returns:
        Authenticated FlickrAPI instance with parsed-json format.

    Raises:
        ValueError: If any of the four required environment variables are absent.
    """
    api_key, api_secret = load_credentials()

    oauth_token = os.getenv("FLICKR_OAUTH_TOKEN")
    oauth_token_secret = os.getenv("FLICKR_OAUTH_TOKEN_SECRET")

    if not oauth_token or not oauth_token_secret:
        raise ValueError(
            "Missing Flickr OAuth token credentials for cloud deployment. "
            "Ensure FLICKR_OAUTH_TOKEN and FLICKR_OAUTH_TOKEN_SECRET are set "
            "as environment variables (via Cloud Secret Manager)."
        )

    flickr = flickrapi.FlickrAPI(api_key, api_secret, format="parsed-json")
    flickr.token_cache.token = FlickrAccessToken(
        oauth_token, oauth_token_secret, "read"
    )
    return flickr
