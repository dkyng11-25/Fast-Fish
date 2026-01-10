Feature: Step 5 - Calculate Feels-Like Temperature for Stores
  
  This step follows the refactored pattern (Steps 1 & 2):
  - Separate repository per output file
  - Period included in filename (e.g., stores_with_feels_like_temperature_202506A.csv)
  - No timestamps or symlinks
  - Simple, clean persistence

  Background:
    Given weather data exists for multiple stores
    And altitude data exists for stores
    And a target period "202506A"
    And feels-like temperature configuration is set

  Scenario: Load and prepare weather data
    Given weather data files exist for multiple stores
    When the step loads weather data in setup phase
    Then weather data should be loaded successfully
    And data should include all required weather parameters
    And altitude data should be merged with weather data
    And data should be ready for processing

  Scenario: Process stores in cold climates
    Given weather data for stores with cold temperatures and high winds
    When calculating feels-like temperature for all stores
    Then cold climate stores should have lower feels-like temperatures than actual
    And wind chill effects should be accounted for
    And results should reflect cold weather conditions

  Scenario: Process stores in hot climates
    Given weather data for stores with high temperatures and humidity
    When calculating feels-like temperature for all stores
    Then hot climate stores should have higher feels-like temperatures than actual
    And heat index effects should be accounted for
    And results should reflect hot weather conditions

  Scenario: Process stores in moderate climates
    Given weather data for stores with moderate temperatures
    When calculating feels-like temperature for all stores
    Then moderate climate stores should have appropriate feels-like temperatures
    And all weather factors should be considered
    And results should reflect moderate weather conditions

  Scenario: Validate and clean weather data
    Given weather data with some outlier values
    When validating and cleaning data in apply phase
    Then outliers should be identified and logged
    And values should be adjusted to reasonable limits
    And data quality should be ensured for calculations

  Scenario: Account for store elevation differences
    Given stores at various elevations from sea level to mountains
    When calculating feels-like temperature
    Then elevation should affect air density calculations
    And high-elevation stores should have adjusted wind effects
    And results should reflect elevation differences

  Scenario: Aggregate weather data by store
    Given hourly weather data for multiple stores
    When aggregating data by store in apply phase
    Then each store should have average feels-like temperature
    And each store should have temperature range statistics
    And each store should have weather condition summaries
    And aggregated data should be ready for band creation

  Scenario: Create temperature bands for clustering
    Given stores with calculated feels-like temperatures
    When creating temperature bands in apply phase
    Then stores should be grouped into temperature bands
    And bands should be suitable for clustering constraints
    And band statistics should be calculated
    And bands should cover the full temperature range

  Scenario: Calculate seasonal temperature metrics
    Given weather data spanning multiple years
    And seasonal focus months configured
    When calculating seasonal feels-like temperature in apply phase
    Then seasonal data should be filtered appropriately
    And seasonal averages should be calculated per store
    And seasonal temperature bands should be created
    And seasonal metrics should complement overall metrics

  Scenario: Handle missing altitude data
    Given weather data exists
    But altitude data file is missing
    When loading altitude data
    Then a warning should be logged
    And elevation should default to 0 meters for all stores
    And calculation should continue without errors

  Scenario: Handle missing weather data files
    Given weather data directory does not exist
    When attempting to load weather data
    Then an error should be raised
    And a helpful message should indicate to run Step 4 first

  Scenario: Handle empty weather data directory
    Given weather data directory exists but is empty
    When attempting to load weather data
    Then a FileNotFoundError should be raised
    And the error message should indicate no files found

  Scenario: Handle corrupted weather data files
    Given some weather data files are corrupted
    When loading weather data files
    Then corrupted files should be logged and skipped
    And valid files should be loaded successfully
    And processing should continue with available data

  Scenario: Save feels-like temperature results
    Given calculated feels-like temperatures for all stores
    When persisting results
    Then main output should be saved to stores_with_feels_like_temperature_202506A.csv
    And output should include all calculated fields
    And output should include temperature bands
    And period should be included in filename for explicit tracking

  Scenario: Save temperature band summary
    Given temperature bands have been created
    When persisting band summary
    Then band summary should be saved to temperature_bands_202506A.csv
    And summary should include band labels, store counts, and temperature ranges
    And period should be included in filename for explicit tracking

  Scenario: Save seasonal temperature band summary
    Given seasonal temperature bands have been created
    When persisting seasonal band summary
    Then seasonal summary should be saved to temperature_bands_202506A.csv
    And summary should include seasonal band statistics
    And period should be included in filename for explicit tracking

  Scenario: Validate calculation results
    Given feels-like temperatures have been calculated
    When validating results
    Then all stores should have valid feels-like temperatures
    And feels-like temperatures should be within reasonable range
    And no stores should have null values for required fields

  Scenario: Log execution statistics
    Given the step has completed successfully
    When generating execution summary
    Then total stores processed should be logged
    And temperature range should be logged
    And number of temperature bands should be logged
    And execution time should be logged

  Scenario: Process multiple stores with different conditions
    Given weather data for stores in various climates
    When calculating feels-like temperature for all stores
    Then cold climate stores should use wind chill
    And hot climate stores should use heat index
    And moderate climate stores should use Steadman's formula
    And all stores should be assigned to appropriate temperature bands

  Scenario: Handle stores with extreme elevations
    Given stores at sea level and high elevation (e.g., 3000m)
    When calculating air density and feels-like temperature
    Then station pressure should be adjusted for elevation
    And air density should be lower at high elevations
    And wind speed correction should account for density difference

  Scenario: Extract year and month from datetime column
    Given weather data with a datetime column
    When extracting year and month
    Then year and month columns should be added
    And seasonal filtering should use these columns

  Scenario: Handle weather data without datetime column
    Given weather data without year/month information
    When attempting seasonal analysis
    Then seasonal filtering should be skipped gracefully
    And overall feels-like temperature should still be calculated

  Scenario: Complete step execution with all phases
    Given all prerequisites are met
    When executing the complete step
    Then setup phase should load weather and altitude data
    And apply phase should calculate feels-like temperatures for all stores
    And apply phase should create temperature bands
    And validate phase should verify data quality and results
    And persist phase should save all outputs
    And step should complete successfully with summary statistics

  Scenario: Process multiple stores with varying conditions
    Given weather data for stores across different climate zones
    When processing all stores through the step
    Then each store should be processed according to its conditions
    And cold climate stores should use appropriate calculations
    And hot climate stores should use appropriate calculations
    And moderate climate stores should use appropriate calculations
    And all stores should be assigned to temperature bands
    And results should be saved for all stores

  Scenario: Consolidate weather data from multiple files
    Given weather data split across multiple CSV files
    When loading weather data in setup phase
    Then all files should be discovered and loaded
    And data from all files should be combined
    And combined data should be aggregated by store
    And consolidated data should be used for all calculations

  Scenario: Handle mixed data quality across stores
    Given some stores have complete data and some have missing values
    When processing all stores
    Then stores with complete data should be processed normally
    And stores with missing values should use fallback logic
    And all stores should produce valid results
    And data quality issues should be logged

  Scenario: Save comprehensive output files
    Given calculated feels-like temperatures and temperature bands
    When persisting results
    Then main temperature data should be saved with all metrics
    And temperature band summary should be saved
    And seasonal band summary should be saved if applicable
    And execution log should be saved with statistics
    And all outputs should be ready for next step
