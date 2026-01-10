@step2 @coordinates @spu_mapping
Feature: Extract Store Coordinates and Create SPU Mappings
  As a data pipeline operator
  I want to extract store coordinates from multi-period API data
  So that I can create comprehensive SPU-to-store mappings for clustering analysis

  Background:
    Given the system is configured for multi-period coordinate extraction
    And year-over-year periods are calculated based on current configuration
    And available data files are discovered across target periods

  @setup @multi_period
  Scenario: Successfully discover and load multi-period data
    Given store sales data exists in multiple periods with coordinate information
    And SPU sales data is available across the year-over-year periods
    And category sales data exists for validation purposes
    When the system scans all target periods for comprehensive data
    Then the period with maximum valid coordinates should be selected
    And all available SPU and category data should be loaded

  @setup @configuration
  Scenario: Load configuration and determine target periods
    Given the current period is configured via environment variables
    And coordinate months back parameter is set to 3 months by default
    When the system initializes for coordinate extraction
    Then year-over-year periods should be calculated correctly
    And target periods should include both current and previous year data

  @apply @coordinate_extraction
  Scenario: Successfully extract coordinates from store sales data
    Given store sales data contains a "long_lat" column with coordinate strings
    And coordinates are in the format "longitude,latitude"
    And coordinate values are valid numeric strings
    When coordinate extraction processes the data
    Then longitude and latitude should be parsed as float values
    And store coordinates DataFrame should be created with proper schema
    And store codes should be converted to string format

  @apply @spu_mapping
  Scenario: Create comprehensive SPU-to-store mappings
    Given SPU sales data from multiple periods is available
    And SPU data contains spu_code, str_code, and sales information
    When comprehensive SPU mappings are created
    Then unique SPU-store combinations should be identified
    And SPU metadata should be aggregated with sales statistics
    And store count per SPU should be calculated across all periods

  @apply @metadata_generation
  Scenario: Generate SPU metadata with aggregated statistics
    Given SPU sales data across multiple periods
    And sales amounts and store information are available
    When SPU metadata is generated
    Then total sales should be summed across all periods
    And average sales per period should be calculated
    And standard deviation of sales should be computed
    And period count should reflect data availability

  @validate @coordinate_format
  Scenario: Validate coordinate data format and completeness
    Given store sales data with coordinate information
    And coordinates must be in valid longitude,latitude format
    When coordinate validation is performed
    Then coordinates must contain comma separators
    And longitude and latitude must be parseable as floats
    And empty or malformed coordinates should be rejected
    And only stores with valid coordinates should be included

  @validate @data_availability
  Scenario: Validate data availability across periods
    Given the system requires coordinate data for analysis
    And placeholders are prohibited per policy
    When data availability is validated
    Then at least one target period must contain valid coordinates
    And coordinate data must not be synthetic or placeholder
    And sufficient store coverage must be available for analysis

  @validate @store_overlap
  Scenario: Validate overlap between coordinate and SPU data
    Given stores with coordinate data are identified
    And stores with SPU sales data are identified
    When overlap analysis is performed
    Then stores with both coordinates and SPU data should be counted
    And coverage percentage should be calculated
    And missing coordinate stores should be reported

  @persist @coordinate_output
  Scenario: Save extracted coordinates to designated files
    Given valid coordinate data has been extracted
    And output directories are available
    When coordinates are saved to files
    Then coordinates should be saved to the legacy path
    And period-specific coordinates should be saved if configured
    And file paths should match expected naming conventions

  @persist @spu_output
  Scenario: Save comprehensive SPU mappings and metadata
    Given comprehensive SPU mappings have been created
    And SPU metadata has been aggregated
    When SPU data is saved to files
    Then SPU-store mapping should be saved to designated path
    And SPU metadata should be saved with all statistics
    And output files should contain expected schema and data types

  @error @missing_coordinates
  Scenario: Handle missing coordinate data gracefully
    Given no target periods contain valid coordinate data
    And the system policy prohibits placeholders
    When coordinate extraction is attempted
    Then a runtime error should be raised
    And the error should indicate missing coordinate data
    And processing should halt immediately

  @error @malformed_coordinates
  Scenario: Handle malformed coordinate data
    Given store sales data contains malformed coordinates
    And some coordinates cannot be parsed as longitude,latitude
    When coordinate extraction processes the data
    Then parsing errors should be logged with store codes
    And valid coordinates should still be processed
    And invalid coordinates should be excluded from results

  @error @file_access
  Scenario: Handle file access and I/O errors
    Given required data files are not accessible
    And file permissions prevent reading data
    When data loading is attempted
    Then appropriate error messages should be logged
    And the error should include file path information
    And processing should handle the failure gracefully

  @error @empty_data
  Scenario: Handle empty or invalid source data
    Given source data files exist but contain no valid records
    And coordinate fields are empty or null
    When data validation is performed
    Then empty data should be detected
    And appropriate warnings should be logged
    And the system should attempt to use alternative data sources

  @integration @multi_period_coverage
  Scenario: Ensure comprehensive multi-period coverage
    Given data exists across multiple seasonal periods
    And different periods have different store coverage
    When multi-period analysis is performed
    Then the period with maximum coordinate coverage should be selected
    And SPU mappings should include all available periods
    And metadata should reflect comprehensive period analysis

  @integration @backward_compatibility
  Scenario: Maintain backward compatibility with legacy systems
    Given legacy coordinate file formats are expected
    And downstream steps depend on specific file locations
    When coordinate extraction completes successfully
    Then legacy file paths should be populated
    And file formats should match expected schemas
    And period-specific files should be created as needed
