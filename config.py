"""
Configuration settings for the Flickr Stats application.

This module centralizes all static configuration variables, making them
easily accessible and manageable.
"""

# Constants for API configuration
FLICKR_PAGE_SIZE: int = 100  # Photos per page (max: 500)
MAX_RETRIES: int = 3  # Maximum retry attempts for failed API calls
INITIAL_RETRY_DELAY: int = 2  # Initial delay in seconds before retry
MAX_RETRY_DELAY: int = 60  # Maximum delay in seconds between retries

# Constants for date formatting
DATE_FORMAT: str = '%Y-%m-%d'

# Constants for CSV configuration
CSV_DELIMITER: str = '\t'
CSV_COLUMNS: list[str] = [
    'Date',
    'Photo ID',
    'Photo Title',
    'Daily Views',
    'Daily Favorites',
    'Secret',
    'Server'
]
