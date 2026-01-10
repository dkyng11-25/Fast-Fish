Feature: Apply section - Extract store coordinates and create SPU mappings

  Background:
    Given a target period "202508A" with available API data from Step 1
    And multi-period data scanning is enabled for comprehensive coverage
    And coordinate extraction requires geographic positioning data
    And SPU metadata requires product assortment and sales information

  Scenario: Multi-period coordinate data discovery
    Given multiple periods with API data from the last 3 months
    When scanning all available periods for coordinate data
    Then identify the period with the most comprehensive coordinate coverage
    And select that period as the primary coordinate source
    And log the coordinate coverage statistics per period

  Scenario: Coordinate extraction from API data format
    Given sales data containing "long_lat" column with "longitude,latitude" format
    When parsing coordinate strings from the selected period
    Then validate longitude range is between -180 and 180
    And validate latitude range is between -90 and 90
    And handle coordinate parsing errors gracefully
    And create standardized coordinate DataFrame with str_code, longitude, latitude

  Scenario: SPU data aggregation across multiple periods
    Given SPU sales data available across multiple periods
    When combining SPU data from all periods
    Then deduplicate SPU records to prevent repeated products per store
    And aggregate sales statistics across time periods
    And create comprehensive SPU-to-store mappings
    And generate SPU metadata with store counts and sales statistics

  Scenario: Coordinate and SPU data cross-validation
    Given extracted coordinates and processed SPU data
    When validating data consistency
    Then ensure all SPU stores have corresponding coordinates
    And identify stores with coordinates but no SPU data
    And calculate data coverage percentage
    And log comprehensive data consistency statistics

  Scenario: Output file generation and persistence
    Given validated coordinate and SPU data
    When saving results to persistent storage
    Then create store_coordinates_extended.csv with coordinate data
    And create spu_store_mapping.csv with SPU-to-store relationships
    And create spu_metadata.csv with aggregated SPU statistics
    And ensure all output files follow expected naming conventions

  Scenario: Coordinate data quality validation
    Given extracted coordinate data from API responses
    When validating coordinate data quality
    Then ensure all coordinates have valid longitude/latitude values
    And check for duplicate store coordinates
    And validate coordinate ranges and precision
    And handle coordinate parsing edge cases

  Scenario: SPU metadata statistical validation
    Given aggregated SPU data across multiple periods
    When validating SPU metadata quality
    Then ensure store counts are positive integers
    And validate sales amount calculations
    And check for reasonable standard deviation values
    And verify period count accuracy

  Scenario: Multi-period data consolidation
    Given data from multiple time periods
    When consolidating period-specific results
    Then combine coordinate data from the best period
    And aggregate SPU data across all periods
    And maintain data integrity during consolidation
    And preserve temporal information where relevant

  Scenario: Error handling for missing coordinate data
    Given periods without coordinate information
    When attempting coordinate extraction
    Then scan all available periods for coordinate data
    And raise appropriate errors when no coordinates are found
    And provide clear error messages about missing coordinate requirements
    And maintain compliance with no-placeholder policy

  Scenario: SPU data processing with coordinate filtering
    Given SPU data from multiple periods and coordinate data
    When processing SPU information
    Then filter SPU data to only include stores with valid coordinates
    And create SPU mappings only for coordinate-validated stores
    And generate metadata statistics for coordinate-eligible SPUs
    And maintain data consistency between coordinates and SPU data

  Scenario: Performance optimization for large datasets
    Given potentially large datasets across multiple periods
    When processing coordinate and SPU data
    Then use efficient data structures for memory management
    And implement chunked processing for large files
    And provide progress indicators for long-running operations
    And optimize duplicate detection and removal operations




