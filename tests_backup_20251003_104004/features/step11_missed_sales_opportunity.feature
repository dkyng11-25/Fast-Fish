Feature: Rule 11: Missed Sales Opportunity with Quantity Increase Recommendations

  As a data pipeline operator
  I want to identify missed sales opportunities and recommend real-unit quantity increases
  So that stores can capture sales potential and improve performance against cluster top performers

  Scenario: Successful SPU-level missed sales opportunity identification with Fast Fish validation
    Given the current period is "<period>"
    And SPU sales data with "str_code", "spu_code", "quantity", "base_sal_qty", "fashion_sal_qty", "sal_qty", "spu_sales_amt" is available
    And clustering results with "str_code" and "cluster_id" are available
    And Fast Fish validation is available
    When Rule 11 is executed
    Then missed sales opportunities should be identified
    And store-level results should be generated with positive quantity increases
    And detailed opportunities should be generated and be Fast Fish compliant
    And a summary report should be created
    And top performers reference data should be generated
    And the output dataframes should conform to "Step11StoreResultsSchema" and "Step11OpportunitiesSchema" and "Step11TopPerformersSchema"

  Scenario: SPU-level missed sales opportunity identification with seasonal blending and no Fast Fish validation
    Given the current period is "<period>"
    And seasonal blending is enabled with seasonal period "202409B"
    And SPU sales data with "str_code", "spu_code", "quantity" is available
    And clustering results with "str_code" and "cluster_id" are available
    And Fast Fish validation is unavailable
    When Rule 11 is executed
    Then missed sales opportunities should be identified
    And store-level results should be generated with positive quantity increases
    And detailed opportunities should be generated but not necessarily Fast Fish compliant
    And a summary report should be created
    And top performers reference data should be generated
    And the output dataframes should conform to "Step11StoreResultsSchema" and "Step11OpportunitiesSchema" and "Step11TopPerformersSchema"

  Scenario: Rule 11 fails due to missing SPU sales/quantity file
    Given the current period is "<period>"
    And SPU sales data file is missing
    And clustering results with "str_code" and "cluster_id" are available
    When Rule 11 is executed
    Then Rule 11 execution should fail with a "FileNotFoundError"
    And an error message indicating the missing SPU sales file should be displayed

  Scenario: Rule 11 handles missing real quantity sources gracefully
    Given the current period is "<period>"
    And SPU sales data with "str_code", "spu_code", "spu_sales_amt" is available but missing real quantity columns
    And clustering results with "str_code" and "cluster_id" are available
    When Rule 11 is executed
    Then Rule 11 execution should complete without error
    And log warnings should indicate missing real quantity sources
    And opportunities should have null or zero quantity changes where real units are absent
    And the output dataframes should conform to "Step11StoreResultsSchema" and "Step11OpportunitiesSchema" and "Step11TopPerformersSchema" (allowing nulls for quantity fields)

  Scenario: No opportunities identified when no stores are below top performers
    Given the current period is "<period>"
    And SPU sales data with "str_code", "spu_code", "quantity" is available
    And clustering results with "str_code" and "cluster_id" are available
    And all stores perform at or above cluster top performers
    When Rule 11 is executed
    Then store-level results should be generated with zero total quantity increases
    And detailed opportunities should be empty
    And the summary report should indicate no missed sales opportunities were found

  Scenario: SPU-level missed sales opportunities with strict inner join mode
    Given the current period is "<period>"
    And SPU sales data with "str_code", "spu_code", "quantity" is available for 50 stores
    And clustering results with "str_code" and "cluster_id" are available for 100 stores
    And join mode is "inner"
    When Rule 11 is executed
    Then SPU-level missed sales opportunities should be identified only for stores with both sales and clustering data
    And store-level results should be generated
    And detailed opportunities should be generated
    And a summary report should be created
    And the output dataframes should conform to "Step11StoreResultsSchema" and "Step11OpportunitiesSchema"

  Scenario: Rule 11 operates in August and seasonal blending is automatically enabled
    Given the current period is "202508A"
    And SPU sales data with "str_code", "spu_code", "quantity" is available
    And clustering results with "str_code" and "cluster_id" are available
    And seasonal blending is not explicitly disabled
    When Rule 11 is executed
    Then SPU-level missed sales opportunities should be identified with seasonal blending applied
    And store-level results should be generated
    And detailed opportunities should be generated
    And a summary report should be created
    And the output dataframes should conform to "Step11StoreResultsSchema" and "Step11OpportunitiesSchema"

  Scenario: No missed sales opportunities identified due to very high minimum sales and quantity gaps
    Given the current period is "<period>"
    And SPU sales data with "str_code", "spu_code", "quantity" is available
    And clustering results with "str_code" and "cluster_id" are available
    And minimum sales gap is "100000.0"
    And minimum quantity gap is "5000.0"
    When Rule 11 is executed
    Then no missed sales performance opportunities should be identified
    And no output files related to opportunities should be generated
    And a summary report should be created and indicate no opportunities were found
