"""
Handles all interactions with the Flickr API.

This module is responsible for making API calls, handling retries with
exponential backoff, and fetching photo statistics. It also includes
validation for API responses.
"""

import time
from typing import Dict, Any, List, Optional

import flickrapi

import ui
from config import (
    MAX_RETRIES,
    INITIAL_RETRY_DELAY,
    MAX_RETRY_DELAY,
    FLICKR_PAGE_SIZE,
)


def _make_api_call(
    flickr: flickrapi.FlickrAPI, method_name: str, **params: Any
) -> Optional[Dict[str, Any]]:
    """
    Makes a single Flickr API call with retry logic for rate limiting and errors.

    Args:
        flickr: An authenticated FlickrAPI instance.
        method_name: The API method to call (e.g., 'stats.getPopularPhotos').
        **params: Parameters for the API call.

    Returns:
        The API response as a dictionary, or None if all retries fail.
    """
    retry_delay = INITIAL_RETRY_DELAY
    for attempt in range(MAX_RETRIES):
        try:
            method = flickr
            for part in method_name.split("."):
                method = getattr(method, part)
            response = method(**params)

            # Basic validation for a successful response structure
            if response and isinstance(response, dict) and response.get("stat") == "ok":
                return response
            else:
                ui.print_warning(f"API call successful, but response format is unexpected: {response}")
                return None

        except flickrapi.exceptions.FlickrError as e:
            # Rate limit error codes can vary, checking for common ones
            if e.code in [105, "Rate Limit Exceeded"]:
                if attempt < MAX_RETRIES - 1:
                    ui.print_warning(
                        f"Rate limit hit. Retrying in {retry_delay} seconds... "
                        f"(Attempt {attempt + 1}/{MAX_RETRIES})"
                    )
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
                else:
                    ui.print_error(f"Flickr API rate limit error after {MAX_RETRIES} attempts: {e}")
                    return None
            else:
                ui.print_error(f"Flickr API error: {e}")
                return None
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                ui.print_warning(
                    f"An unexpected error occurred: {e}. Retrying in {retry_delay}s..."
                )
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
            else:
                ui.print_error(f"An unexpected error occurred after multiple retries: {e}")
                return None
    return None


def fetch_popular_photos_for_date(
    flickr: flickrapi.FlickrAPI, date_str: str
) -> Optional[List[Dict[str, Any]]]:
    """
    Fetches all popular photo statistics for a specific date, handling pagination.

    Args:
        flickr: An authenticated FlickrAPI instance.
        date_str: The date for which to fetch stats, in 'YYYY-MM-DD' format.

    Returns:
        A list of photo data dictionaries, or None if the fetch fails.
    """
    all_photos: List[Dict[str, Any]] = []
    params = {"date": date_str, "per_page": FLICKR_PAGE_SIZE, "page": 1}

    ui.print_progress(f"Fetching data for: {date_str}")

    # Initial call to get total pages
    initial_response = _make_api_call(flickr, "stats.getPopularPhotos", **params)

    if not initial_response or "photos" not in initial_response:
        ui.print_warning(f"Could not retrieve initial photo data for {date_str}.")
        return None

    total_pages = initial_response["photos"].get("pages", 0)
    total_photos = initial_response["photos"].get("total", 0)
    ui.print_progress(f"Date: {date_str} - Found {total_photos} photos across {total_pages} pages.")

    if total_photos == 0:
        ui.print_progress(f"No popular photos found for {date_str}.")
        return []

    # Add photos from the first page
    all_photos.extend(initial_response["photos"].get("photo", []))

    # Fetch remaining pages
    for page_num in range(2, total_pages + 1):
        params["page"] = page_num
        ui.print_progress(f"Fetching page {page_num}/{total_pages} for {date_str}...")
        response = _make_api_call(flickr, "stats.getPopularPhotos", **params)

        if response and "photos" in response and "photo" in response["photos"]:
            all_photos.extend(response["photos"]["photo"])
        else:
            ui.print_warning(f"Failed to fetch page {page_num} for {date_str}. Skipping remaining pages.")
            break

    return all_photos
