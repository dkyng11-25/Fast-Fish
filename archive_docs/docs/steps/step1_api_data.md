# Step 1: API Data Download

## Overview
This step handles the download and processing of store sales data from the FastFish API. It implements robust error handling, retry mechanisms, and data validation to ensure reliable data collection.

## Functionality

### API Endpoints
- Store Configuration: https://fdapidb.fastfish.com:8089/api/sale/getAdsAiStrCfg
- Store Sales Data: https://fdapidb.fastfish.com:8089/api/sale/getAdsAiStrSal

### Key Features
1. Batch Processing
   - Processes stores in batches of 10 to prevent API overload
   - Maintains state of processed stores for resumability

2. Error Handling
   - Comprehensive error logging with timestamps
   - Detailed error reports stored in data/api_data/notes/
   - Automatic retry mechanism for failed requests

3. Data Validation
   - Validates store codes against input file
   - Ensures data completeness and consistency
   - Handles missing or malformed responses

## Input Requirements
- data/store_codes.csv: CSV file containing store codes
  - Required column: str_code

## Output Files
1. Store Configuration Data
   - Location: data/api_data/store_config_{YYYYMM}.csv
   - Contains: Store configuration details including categories and subcategories

2. Store Sales Data
   - Location: data/api_data/store_sales_{YYYYMM}.csv
   - Contains: Sales data for each store

3. Category Sales Data
   - Location: data/api_data/complete_category_sales_{YYYYMM}.csv
   - Contains: Aggregated sales data by category

4. Error Logs
   - Location: data/api_data/notes/api_error_{TIMESTAMP}.md
   - Format: Markdown files with detailed error information

## Configuration
- API_BASE = https://fdapidb.fastfish.com:8089/api/sale
- BATCH_SIZE = 10
- TIMEOUT = 30 seconds
- RETRY_COUNT = 3
- RETRY_DELAY = 5 seconds
- RETRY_BACKOFF = 2 seconds

## Error Handling
The script implements a sophisticated error handling system:
1. API Errors
   - Network timeouts
   - Server errors (500, 502, 503, 504)
   - Rate limiting (429)

2. Data Validation
   - Missing store codes
   - Incomplete API responses
   - Data format inconsistencies

3. File System
   - Missing input files
   - Permission issues
   - Disk space problems

## Performance Considerations
- Memory usage is optimized by processing stores in batches
- Network efficiency through connection pooling
- Automatic retry with exponential backoff
- Progress tracking for long-running operations

## Dependencies
- requests
- pandas
- urllib3
- typing

## Usage
python src/step1_download_api_data.py

## Troubleshooting
1. API Connection Issues
   - Check network connectivity
   - Verify API credentials
   - Review API endpoint availability

2. Data Quality Issues
   - Check error logs in data/api_data/notes/
   - Verify input file format
   - Review API response format

3. Performance Issues
   - Adjust batch size if needed
   - Monitor memory usage
   - Check network latency