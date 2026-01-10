Feature: Rule 10: Smart Overcapacity (SPU) with Unit Reductions

  As a data pipeline operator
  I want to detect SPU overcapacity and recommend real-unit quantity reductions
  So that stores can optimize inventory, reduce costs, and improve efficiency

  Scenario: Successful SPU overcapacity detection and unit reductions with Fast Fish validation
    Given the current period is "<period>"
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" and SPU sales JSON in "sty_sal_amt" is available for 100 stores
    And SPU sales data with "str_code", "spu_code", "quantity", "base_sal_qty", "fashion_qty_col", "sal_qty_col", "spu_sales_amt_col" is available
    And minimum sales volume is "20"
    And minimum reduction quantity is "1.0"
    And maximum reduction percentage is "0.4"
    And Fast Fish validation is available
    When Rule 10 is executed
    Then SPU overcapacity should be identified
    And store-level results should be generated with negative quantity changes (reductions)
    And detailed opportunities should be generated and be Fast Fish compliant
    And a summary report should be created
    And the output dataframes should conform to "Step10StoreResultsSchema" and "Step10OpportunitiesSchema"

  Scenario: SPU overcapacity detection with seasonal blending and no Fast Fish validation
    Given the current period is "202509B"
    And seasonal blending is enabled with seasonal period "202409B"
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" and SPU sales JSON in "sty_sal_amt" is available for 100 stores
    And SPU sales data with "str_code", "spu_code", "quantity" is available for 100 stores
    And Fast Fish validation is unavailable
    When Rule 10 is executed
    Then SPU overcapacity should be identified
    And store-level results should be generated with quantity reductions
    And detailed opportunities should be generated but not necessarily Fast Fish compliant
    And a summary report should be created
    And the output dataframes should conform to "Step10StoreResultsSchema" and "Step10OpportunitiesSchema"

  Scenario: Rule 10 fails due to missing clustering results file
    Given the current period is "202509A"
    And clustering results file is missing
    When Rule 10 is executed
    Then Rule 10 execution should fail with a "FileNotFoundError"
    And an error message indicating the missing clustering file should be displayed

  Scenario: Rule 10 handles missing real unit fields gracefully
    Given the current period is "202509A"
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" and SPU sales JSON in "sty_sal_amt" is available for 100 stores
    And SPU sales data is available but missing real unit quantity columns (e.g., "quantity", "base_sal_qty") for 100 stores
    When Rule 10 is executed
    Then Rule 10 execution should complete without error
    And log warnings should indicate missing real unit fields
    And opportunities should have null or zero quantity changes where real units are absent
    And the output dataframes should conform to "Step10StoreResultsSchema" and "Step10OpportunitiesSchema" (allowing nulls for quantity fields)

  Scenario: No overcapacity identified when all SPUs are below target count or sales volume
    Given the current period is "202509A"
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" and SPU sales JSON in "sty_sal_amt" is available for 100 stores
    And SPU sales data with "str_code", "spu_code", "quantity" is available for 100 stores
    And all categories have current SPU count less than or equal to target SPU count
    When Rule 10 is executed
    Then store-level results should be generated with zero total quantity adjustments
    And detailed opportunities should be empty
    And the summary report should indicate no overcapacity opportunities were found

  Scenario: SPU overcapacity detection with strict inner join mode
    Given the current period is "<period>"
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" and SPU sales JSON in "sty_sal_amt" is available for 50 stores
    And SPU sales data with "str_code", "spu_code", "quantity" is available for 50 stores
    And join mode is "inner"
    When Rule 10 is executed
    Then SPU overcapacity should be identified only for stores with both planning and clustering data
    And store-level results should be generated with quantity reductions
    And detailed opportunities should be generated
    And a summary report should be created
    And the output dataframes should conform to "Step10StoreResultsSchema" and "Step10OpportunitiesSchema"

  Scenario: Rule 10 operates in August with seasonal blending explicitly disabled
    Given the current period is "202508A"
    And seasonal blending is explicitly disabled
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" and SPU sales JSON in "sty_sal_amt" is available for 100 stores
    And SPU sales data with "str_code", "spu_code", "quantity" is available for 100 stores
    When Rule 10 is executed
    Then SPU overcapacity should be identified without seasonal blending
    And store-level results should be generated with quantity reductions
    And detailed opportunities should be generated
    And a summary report should be created
    And the output dataframes should conform to "Step10StoreResultsSchema" and "Step10OpportunitiesSchema"
