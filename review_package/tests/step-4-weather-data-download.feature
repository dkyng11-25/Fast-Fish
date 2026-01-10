Feature: Step 4 - Download Weather Data for Store Locations

  Background:
    Given a list of store coordinates with latitude and longitude
    And a target period configuration with year-month and half-month period
    And weather API endpoints are available
    And output directories exist for weather data and progress tracking

  Scenario: Dynamic period generation for year-over-year analysis
    Given a base period "202506A" and months-back setting of 3
    When generating dynamic year-over-year periods
    Then generate last 3 months of current year periods
    And generate next 3 months from previous year periods
    And include both A and B halves for complete month coverage
    And skip periods that start in the future
    And clamp end dates to today if they extend into the future
    And create weather period labels in YYYYMMDD_to_YYYYMMDD format

  Scenario: Load existing progress for resume capability
    Given a saved progress file exists with completed periods and stores
    When loading download progress
    Then restore completed periods list
    And restore completed stores list
    And restore failed stores list
    And restore VPN switch count
    And restore last update timestamp

  Scenario: Identify stores needing download for specific period
    Given weather data files exist for some stores in a period
    And a complete list of store coordinates
    When determining stores to download for the period
    Then exclude stores that already have weather data files
    And include stores without weather data files
    And preserve store codes as strings for matching

  Scenario: Download weather data for single store
    Given a store with coordinates and a time period
    And the weather data file does not already exist
    When requesting weather data from Open-Meteo Archive API
    Then include 16 hourly weather variables in request
    And set timezone to Asia/Shanghai
    And use period-specific start and end dates
    And add store_code, latitude, longitude to response data
    And save weather DataFrame to CSV with period-specific filename
    And apply random delay between requests

  Scenario: Handle API rate limiting with exponential backoff
    Given a weather data download request
    When the API returns HTTP 429 (rate limit exceeded)
    Then wait with exponential backoff starting at 5 seconds
    And retry the request up to MAX_RETRIES times
    And reset consecutive rate limit counter on success
    And continue with next store after max retries

  Scenario: VPN switching support for API access issues
    Given multiple consecutive API failures (5+)
    When checking if VPN switch is needed
    Then prompt user to switch VPN location
    And wait for user to type 'continue' or 'abort'
    And reset consecutive failure counter after VPN switch
    And increment VPN switch counter in progress
    And save progress after VPN switch

  Scenario: Collect altitude data for all store locations
    Given store coordinates with unique latitude/longitude pairs
    And existing altitude data file may or may not exist
    When collecting altitude data
    Then identify stores missing altitude data
    And call Open-Meteo elevation API for unique coordinates only
    And merge altitude data with store codes
    And combine new altitude data with existing data
    And save complete altitude dataset to CSV
    And apply small delay (0.1s) between API calls

  Scenario: Validate weather API response data
    Given a weather API response for a store
    When validating the response data
    Then verify response contains 'hourly' data
    And check for 16 required weather columns
    And raise ValueError if hourly data is missing
    And raise ValueError if required columns are missing
    And allow processing to continue if validation passes

  Scenario: Repair weather files missing store_code column
    Given a weather CSV file without store_code column
    When validating and repairing the file
    Then parse store code from filename pattern
    And add store_code column to DataFrame
    And reorder columns to put store_code early
    And save repaired file back to original path
    And log repair action

  Scenario: Save download progress periodically
    Given weather data download is in progress
    When 25 stores have been processed
    Then save progress to JSON file
    And include completed periods list
    And include completed and failed stores lists
    And include VPN switch count
    And update last update timestamp

  Scenario: Process multiple periods with VPN support
    Given a list of periods to download
    And download progress tracking
    When processing each period sequentially
    Then download weather data for all stores in period
    And track consecutive failures for VPN switching
    And prompt for VPN switch when threshold reached
    And mark period as completed when all stores processed
    And save progress after each period
    And calculate success rate for period

  Scenario: Handle specific period download via CLI
    Given a command-line argument for specific period "202505A"
    And a list of all available dynamic periods
    When processing the specific period request
    Then find the matching period in available periods
    And download only that period's weather data
    And collect altitude data if needed
    And save progress after completion
    And exit after single period download

  Scenario: Show download status across all periods
    Given saved download progress
    And a list of all dynamic periods
    When displaying download status
    Then show VPN switches performed
    And show last update timestamp
    And show status for each period (COMPLETE/PENDING/IN PROGRESS)
    And show number of stores downloaded per period
    And show date range for each period

  Scenario: Handle empty or missing data gracefully
    Given some stores have no coordinates
    And some API requests return empty responses
    When processing stores
    Then skip stores with invalid coordinates
    And log errors for failed API requests
    And track failed stores in progress
    And continue processing remaining stores
    And do not halt entire download for single failures

  Scenario: Retry logic for transient API failures
    Given a weather data download request fails
    And the failure is a network timeout or connection error
    When retrying the request
    Then wait with increasing delay (1.5x per attempt)
    And retry up to MAX_RETRIES times (3)
    And log each retry attempt with delay
    And record store as failed after max retries
    And append failure details to download_failed.csv

  Scenario: Skip already-downloaded stores for efficiency
    Given a period with some stores already downloaded
    When starting download for that period
    Then check for existing weather data files
    And extract store codes from existing filenames
    And filter to only stores without existing files
    And log number of already-downloaded vs. to-download stores
    And mark period as complete if all stores already downloaded

  Scenario: Command-line interface for various operations
    Given command-line arguments are provided
    When parsing arguments
    Then support --resume to continue interrupted download
    And support --status to show current progress
    And support --period to download specific period
    And support --list-periods to show all dynamic periods
    And support --months-back to configure lookback window
    And support --base-month and --base-period to override base
    And support --reset-progress to clear saved state
    And execute appropriate action based on arguments

  Scenario: Date range calculation for period halves
    Given a year-month and period half (A or B)
    When calculating date range for the period
    Then for period A use dates 1-15 of the month
    And for period B use dates 16-last_day of the month
    And calculate last day of month correctly for all months
    And handle leap years correctly for February
    And format dates as YYYY-MM-DD for API requests

  Scenario: Comprehensive error logging
    Given various types of errors occur during download
    When logging errors
    Then log to both file (weather_download.log) and console
    And include timestamps in all log messages
    And log API errors with HTTP status codes
    And log API response bodies (truncated to 500 chars)
    And log VPN switch events
    And log period completion summaries
    And log progress updates every 10 stores

  Scenario: Final summary after complete download
    Given all periods have been processed
    When generating final summary
    Then calculate total execution time in minutes
    And show total VPN switches performed
    And show final status for all periods
    And show stores downloaded per period
    And log completion message with statistics
