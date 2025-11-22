"""
Handles Flickr API authentication.

This module provides functions to authenticate with the Flickr API using OAuth.
It securely loads credentials from environment variables and manages the
authentication flow, including token validation and user authorization.
"""

import os
import webbrowser
from typing import Tuple

import flickrapi
from dotenv import load_dotenv

import ui


def _load_credentials() -> Tuple[str, str]:
    """
    Loads Flickr API key and secret from environment variables.

    This function uses python-dotenv to load variables from a .env file.

    Returns:
        A tuple containing the API key and secret.

    Raises:
        ValueError: If either the API key or secret is not found.
    """
    load_dotenv()

    api_key = os.getenv("FLICKR_API_KEY")
    api_secret = os.getenv("FLICKR_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError(
            "Missing Flickr API credentials. Ensure FLICKR_API_KEY and "
            "FLICKR_API_SECRET are set in your .env file."
        )

    return api_key, api_secret


def _perform_oauth(flickr: flickrapi.FlickrAPI) -> flickrapi.FlickrAPI:
    """
    Guides the user through the OAuth authentication process.

    Args:
        flickr: A FlickrAPI instance.

    Returns:
        The authenticated FlickrAPI instance.
    """
    ui.print_progress("First-time setup: You need to authorize this app with Flickr.")

    try:
        # Get a request token
        flickr.get_request_token(oauth_callback="oob")

        # Open a browser for the user to authorize
        authorize_url = flickr.auth_url(perms="read")
        ui.print_progress(f"A browser window will now open to this URL: {authorize_url}")
        webbrowser.open_new_tab(authorize_url)

        # Get the verifier code from the user
        verifier = input("Please enter the verifier code from Flickr: ").strip()

        # Trade the request token for an access token
        flickr.get_access_token(verifier)
        ui.print_success("Authentication successful! Your token is now cached.")

    except Exception as e:
        ui.print_error(f"An error occurred during authentication: {e}")
        raise

    return flickr


def get_authenticated_client() -> flickrapi.FlickrAPI:
    """
    Provides an authenticated Flickr API client.

    This function loads credentials, initializes the FlickrAPI client, and
    checks for a valid cached token. If no valid token is found, it
    initiates the OAuth process.

    Returns:
        An authenticated FlickrAPI instance.

    Raises:
        ValueError: If API credentials are not configured correctly.
    """
    api_key, api_secret = _load_credentials()
    flickr = flickrapi.FlickrAPI(api_key, api_secret, format="parsed-json")

    # If the token is not valid, initiate the authentication process
    if not flickr.token_valid(perms="read"):
        flickr = _perform_oauth(flickr)

    ui.print_progress("Flickr client authenticated.")
    return flickr
