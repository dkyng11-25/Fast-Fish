Feature: Apply section - Download, transform, and prepare API data

  Background:
    Given a target period "202508A" and a list of store codes
    And smart incremental mode may be enabled or disabled
    And batch size is configured to "10"

  Scenario: Smart incremental selection of stores
    Given processed and failed store tracking files exist
    When selecting stores to process
    Then skip already processed stores
    And include previously failed stores for retry
    And include never-attempted stores
    And optionally include all stores when force-full mode is enabled

  Scenario: Batch processing loop
    Given a batch of selected stores
    When fetching store configuration for the batch
    Then request the config endpoint with the batch payload
    And filter results to the requested half-month when applicable
    And log missing store codes from the response

    When fetching store sales for the batch
    Then request the sales endpoint with the batch payload
    And filter results to the requested half-month when applicable
    And log missing store codes from the response

  Scenario: Merge and transform per batch
    Given fetched sales and configuration data for the batch
    When computing store-level metrics
    Then calculate real total quantities and unit prices from base/fashion amounts and quantities

    When producing category-level output
    Then preserve all product assortment rows
    And map store-level unit prices to estimate category quantities
    And merge store-level metrics when available

    When producing SPU-level output
    Then deduplicate configuration to prevent repeated SPUs per store/subcategory
    And expand SPUs from JSON payloads
    And estimate per-category unit prices
    And compute SPU quantities from sales amounts and estimated unit prices

  Scenario: Intermediate persistence during apply
    Given partial results across multiple batches
    When a save interval is reached
    Then write partial CSVs for config, sales, category, and SPU

  Scenario: Tracking success and failure per batch
    Given processed stores for the current batch
    When determining outcomes
    Then record successfully processed stores to the success tracking file
    And record attempted-but-missing stores to the failure tracking file

  Scenario: Multi-period (last N months)
    Given a set of missing periods across the last "3" months
    When iterating periods sequentially
    Then repeat store selection, batching, fetching, and merging for each period

  Scenario: Year-over-year periods
    Given a combined list of current and historical-future periods from last year
    When iterating combined periods sequentially
    Then repeat store selection, batching, fetching, and merging for each combined period

  Scenario: Multi-batch data processing
    Given multiple batches of config and sales data from API
    When processing each batch sequentially in apply phase
    Then merge and transform data for each batch
    And consolidate results from all batches
    And track processing success across all batches

  Scenario: Data consolidation and context management
    Given processed category and SPU data from multiple batches
    When consolidating data in apply phase
    Then combine all category data into single dataframe
    And combine all SPU data into single dataframe
    And set consolidated category data as primary context data
    And update context state with all processed results

  Scenario: Empty batch handling
    Given some batches have empty config or sales data
    When processing batches in apply phase
    Then skip empty batches gracefully
    And continue processing valid batches
    And record appropriate success/failure tracking

  Scenario: Mixed batch success and failure
    Given batches with varying data quality and completeness
    When processing all batches in apply phase
    Then successfully process valid data batches
    And track stores that failed processing
    And maintain accurate counts of processed vs failed stores
    And consolidate only successful batch results


