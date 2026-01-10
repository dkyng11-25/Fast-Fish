Feature: Rule 9: Below Minimum Rule with Quantity Increases

  As a data pipeline operator
  I want to identify items below minimum thresholds and recommend positive-only quantity increases
  So that stores can maintain optimal inventory levels and avoid stockouts, with sell-through validation

  Scenario Outline: Successful SPU-level below minimum identification with positive quantity increases
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" is available
    And SPU sales data with "str_code", "spu_code", "quantity" is available
    And minimum unit rate is "1.0" units per 15 days
    And minimum boost quantity is "0.5"
    And the rule is configured to never decrease below minimum
    And Fast Fish validation is available
    When Rule 9 is executed
    Then below minimum SPU opportunities should be identified
    And store-level results should be generated with positive quantity increases
    And detailed opportunities should be generated and be Fast Fish compliant
    And a summary report should be created
    And the output dataframes should conform to "Step9StoreResultsSchema" and "Step9OpportunitiesSchema"
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Rule 9 fails due to missing spu_code in SPU sales data
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" is available
    And SPU sales data is available but "spu_code" column is missing
    When Rule 9 is executed
    Then Rule 9 execution should fail with a "KeyError"
    And an error message indicating the missing "spu_code" column should be displayed
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: No opportunities identified in SPU mode when all SPUs are above minimum threshold (no valid SPU expansion)
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" is available
    And SPU sales data with all SPUs above minimum threshold is available
    When Rule 9 is executed
    Then store-level results should be generated with zero below minimum SPU count
    And detailed opportunities should be empty
    And the summary report should indicate no below minimum opportunities were found
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Subcategory mode identifies below minimums but generates no unit increases without real unit data
    Given the analysis level is "subcategory"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code", "target_sty_cnt_avg" is available
    And SPU sales data is available but missing quantity column (no real unit data for subcategory mapping)
    And seasonal blending is disabled
    When Rule 9 is executed
    Then below minimum subcategory cases should be identified with count-based flags
    And store-level results should be generated with count-based metrics
    And detailed opportunities should be generated for subcategories but with no quantity increases
    And a summary report should be created
    And the output dataframes should conform to "Step9StoreResultsSchema" and "Step9SubcategoryOpportunitiesSchema"
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Successful subcategory-level below minimum identification with count-based flags
    Given the analysis level is "subcategory"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code", "target_sty_cnt_avg" is available
    And SPU sales data with "str_code", "spu_code", "quantity" is available (for unit mapping)
    And seasonal blending is disabled
    When Rule 9 is executed
    Then below minimum subcategory cases should be identified with count-based flags
    And store-level results should be generated with count-based metrics
    And detailed opportunities should be generated for subcategories (if unit mapping is present)
    And a summary report should be created
    And the output dataframes should conform to "Step9StoreResultsSchema" and "Step9SubcategoryOpportunitiesSchema"
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Rule 9 fails due to missing SPU sales quantity file
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" is available
    And SPU sales data file is missing
    When Rule 9 is executed
    Then Rule 9 execution should fail with a "FileNotFoundError"
    And an error message indicating the missing SPU sales file should be displayed
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Rule 9 fails due to missing required quantity column in SPU sales data
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" is available
    And SPU sales data is available but "quantity" column is missing
    When Rule 9 is executed
    Then Rule 9 execution should fail with a "KeyError"
    And an error message indicating the missing quantity column should be displayed
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: No opportunities identified when no SPUs are below minimum threshold
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" is available
    And SPU sales data with all SPUs above minimum threshold is available
    When Rule 9 is executed
    Then store-level results should be generated with zero below minimum SPU count
    And detailed opportunities should be empty
    And the summary report should indicate no below minimum opportunities were found
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Seasonal blending with recent and historical data
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" is available
    And SPU sales data with "str_code", "spu_code", "quantity" is available
    And seasonal blending is enabled with seasonal period "<seasonal_period>"
    And seasonal weight is "<seasonal_weight>"
    And minimum unit rate is "1.0" units per 15 days
    And minimum boost quantity is "0.5"
    And Fast Fish validation is available
    When Rule 9 is executed
    Then below minimum SPU opportunities should be identified
    And store-level results should be generated with positive quantity increases
    And detailed opportunities should be generated and be Fast Fish compliant
    And a summary report should be created
    And the output dataframes should conform to "Step9StoreResultsSchema" and "Step9OpportunitiesSchema"
    Examples:
      | period  | seasonal_period | seasonal_weight |
      | 202509A | 202408A        | 0.6             |
      | 202509A | 202408B        | 0.4             |
      | 202508A | 202407A        | 0.5             |
      | 202508B | 202407B        | 0.7             |

  Scenario Outline: 5-cluster subset validation with parameter sweeps
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And a 5-cluster subset is selected with high/average consumption spread
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" is available
    And SPU sales data with "str_code", "spu_code", "quantity" is available
    And minimum unit rate is "<min_unit_rate>" units per 15 days
    And minimum boost quantity is "<min_boost_qty>"
    And Fast Fish validation is available
    When Rule 9 is executed
    Then below minimum SPU opportunities should be identified
    And store-level results should be generated with positive quantity increases
    And detailed opportunities should be generated and be Fast Fish compliant
    And a summary report should be created
    And the output dataframes should conform to "Step9StoreResultsSchema" and "Step9OpportunitiesSchema"
    Examples:
      | period  | min_unit_rate | min_boost_qty |
      | 202509A | 0.5          | 0.25          |
      | 202509A | 1.0          | 0.5           |
      | 202509A | 1.5          | 0.75          |
      | 202508A | 1.0          | 0.5           |
      | 202508B | 1.5          | 0.75          |
