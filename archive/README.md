# Archived Scripts

This directory contains deprecated and experimental scripts that are no longer actively maintained but are kept for reference.

## Files

### flickrDailyStats.py
Early prototype for fetching daily statistics. **DO NOT USE** - superseded by `flickrGetDailyPhotoViews.py`.

### flickrGetTotalViews.py
Script to get total views across all categories. **DO NOT USE** - experimental only.

### flickrGetTotalPhotoViews.py
Early version with incomplete pagination loop. **DO NOT USE** - superseded by `flickrGetDailyPhotoViews.py`.

### iterateDates.py
Experimental code for date iteration. Functionality has been integrated into the main script.

## Production Script

For production use, please use `../flickrGetDailyPhotoViews.py` which includes:
- Proper error handling with retry logic
- Complete pagination support
- Date range validation
- User input for date ranges
- Comprehensive CSV export
