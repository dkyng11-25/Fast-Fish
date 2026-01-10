Feature: Rule 12: Sales Performance with Quantity Increase Recommendations

  As a data pipeline operator
  I want to evaluate store performance against cluster benchmarks and recommend real-unit quantity increases
  So that stores can close performance gaps and maximize sales potential

  Scenario Outline: Successful SPU-level sales performance evaluation with positive quantity increases
    Given the current period is "<period>"
    And SPU sales data with "str_code", "spu_code", "quantity", "spu_sales_amt" is available
    And clustering results with "str_code" and "cluster_id" are available
    And the join mode is "left"
    When Rule 12 is executed
    Then sales performance opportunities should be identified
    And store-level results should be generated with positive quantity increases
    And detailed opportunities should be generated
    And a summary report should be created
    And the output dataframes should conform to "Step12StoreResultsSchema" and "Step12OpportunitiesSchema"
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Subcategory-level sales performance evaluation with count-based metrics (no synthetic units)
    Given the current period is "<period>"
    And subcategory sales data with "str_code", "sub_cate_name", "sal_amt" is available
    And clustering results with "str_code" and "cluster_id" are available
    And the join mode is "inner"
    When Rule 12 is executed
    Then sales performance opportunities should be identified with count-based metrics
    And store-level results should be generated with count-based metrics
    And detailed opportunities should be generated (without synthetic unit increases)
    And a summary report should be created
    And the output dataframes should conform to "Step12StoreResultsSchema" and "Step12OpportunitiesSchema"
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Rule 12 fails due to missing SPU sales/quantity data file
    Given the current period is "<period>"
    And SPU sales data file is missing
    And clustering results with "str_code" and "cluster_id" are available
    When Rule 12 is executed
    Then Rule 12 execution should fail with a "FileNotFoundError"
    And an error message indicating the missing SPU sales file should be displayed
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Rule 12 handles missing real quantity sources gracefully for SPU data
    Given the current period is "<period>"
    And SPU sales data with "str_code", "spu_code", "spu_sales_amt" is available but missing real quantity columns
    And clustering results with "str_code" and "cluster_id" are available
    When Rule 12 is executed
    Then Rule 12 execution should complete without error
    And log warnings should indicate missing real quantity sources
    And opportunities should have null or zero quantity changes where real units are absent
    And the output dataframes should conform to "Step12StoreResultsSchema" and "Step12OpportunitiesSchema" (allowing nulls for quantity fields)
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: No opportunities identified when no stores underperform against cluster benchmarks
    Given the current period is "<period>"
    And SPU sales data with "str_code", "spu_code", "quantity" is available
    And clustering results with "str_code" and "cluster_id" are available
    And all stores perform at or above cluster top performers
    When Rule 12 is executed
    Then store-level results should be generated with zero total quantity increases
    And detailed opportunities should be empty
    And the summary report should indicate no sales performance opportunities were found
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: SPU-level sales performance with strict inner join mode
    Given the current period is "<period>"
    And SPU sales data with "str_code", "spu_code", "quantity" is available for 50 stores
    And clustering results with "str_code" and "cluster_id" are available for 100 stores
    And join mode is "inner"
    When Rule 12 is executed
    Then SPU-level sales performance opportunities should be identified only for stores with both sales and clustering data
    And store-level results should be generated with positive quantity increases
    And detailed opportunities should be generated
    And a summary report should be created
    And the output dataframes should conform to "Step12StoreResultsSchema" and "Step12OpportunitiesSchema"
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: SPU-level sales performance with optional total quantity cap per store
    Given the current period is "<period>"
    And SPU sales data with "str_code", "spu_code", "quantity" is available
    And clustering results with "str_code" and "cluster_id" are available
    And maximum total quantity per store is "10"
    When Rule 12 is executed
    Then SPU-level sales performance opportunities should be identified with a total quantity cap applied
    And store-level results should be generated with positive quantity increases
    And detailed opportunities should be generated
    And a summary report should be created
    And the output dataframes should conform to "Step12StoreResultsSchema" and "Step12OpportunitiesSchema"
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: No sales performance opportunities when all stores perform at or above cluster benchmarks with high quantity cap
    Given the current period is "<period>"
    And all stores perform at or above cluster benchmarks
    And maximum total quantity per store is "1000"
    When Rule 12 is executed
    Then no sales performance opportunities should be identified
    And no output files related to opportunities should be generated
    And a summary report should be created and indicate no opportunities were found
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Seasonal blending with recent and historical data
    Given the current period is "<period>"
    And SPU sales data with "str_code", "spu_code", "quantity", "spu_sales_amt" is available
    And clustering results with "str_code" and "cluster_id" are available
    And seasonal blending is enabled with seasonal period "<seasonal_period>"
    And seasonal weight is "<seasonal_weight>"
    And the join mode is "left"
    When Rule 12 is executed
    Then sales performance opportunities should be identified
    And store-level results should be generated with positive quantity increases
    And detailed opportunities should be generated
    And a summary report should be created
    And the output dataframes should conform to "Step12StoreResultsSchema" and "Step12OpportunitiesSchema"
    Examples:
      | period  | seasonal_period | seasonal_weight |
      | 202509A | 202408A        | 0.6             |
      | 202509A | 202408B        | 0.4             |
      | 202508A | 202407A        | 0.5             |
      | 202508B | 202407B        | 0.7             |

  Scenario Outline: 5-cluster subset validation with parameter sweeps
    Given the current period is "<period>"
    And a 5-cluster subset is selected with high/average consumption spread
    And SPU sales data with "str_code", "spu_code", "quantity", "spu_sales_amt" is available
    And clustering results with "str_code" and "cluster_id" are available
    And the join mode is "<join_mode>"
    And maximum total quantity per store is "<max_qty>"
    When Rule 12 is executed
    Then sales performance opportunities should be identified
    And store-level results should be generated with positive quantity increases
    And detailed opportunities should be generated
    And a summary report should be created
    And the output dataframes should conform to "Step12StoreResultsSchema" and "Step12OpportunitiesSchema"
    Examples:
      | period  | join_mode | max_qty |
      | 202509A | left      | 5       |
      | 202509A | inner     | 10      |
      | 202509A | left      | 15      |
      | 202508A | inner     | 5       |
      | 202508B | left      | 10      |
