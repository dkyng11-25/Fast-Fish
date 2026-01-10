Feature: Rule 8: Imbalanced Allocation with Quantity Rebalancing

  As a data pipeline operator
  I want to detect and rebalance imbalanced style allocations at SPU/subcategory level
  So that stores have optimal inventory distribution and maximized sales potential

  Scenario Outline: Successful SPU-level quantity rebalancing with Z-score threshold
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" is available
    And SPU quantity data with "str_code", "spu_code", "quantity" is available
    And the Z-score threshold for SPU is "3.0"
    And rebalance mode is "increase_only"
    When Rule 8 is executed
    Then imbalanced SPU cases should be identified
    And store-level results should be generated with quantity adjustments
    And detailed imbalance cases should be generated
    And a summary report should be created
    And the output dataframes should conform to "Step8StoreResultsSchema" and "Step8ImbalancesSchema"
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Rule 8 fails due to strict quantity derivation requirement
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" is available
    And SPU sales data is available but missing all quantity sources
    When Rule 8 is executed
    Then Rule 8 execution should fail with a "ValueError"
    And an error message indicating missing quantity sources should be displayed
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Fast Fish validation rejects some imbalanced allocation opportunities
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" is available
    And SPU quantity data with "str_code", "spu_code", "quantity" is available
    And the Z-score threshold for SPU is "3.0"
    And rebalance mode is "increase_only"
    And Fast Fish validation is available but rejects some opportunities
    When Rule 8 is executed
    Then imbalanced SPU cases should be identified with some Fast Fish rejections
    And store-level results should be generated with quantity adjustments
    And detailed imbalance cases should be generated
    And a summary report should be created
    And the output dataframes should conform to "Step8StoreResultsSchema" and "Step8ImbalancesSchema"
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Successful subcategory-level quantity rebalancing without seasonal blending
    Given the analysis level is "subcategory"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code", "target_sty_cnt_avg" is available
    And subcategory quantity data with "str_code", "sub_cate_name", "quantity" is available
    And seasonal blending is disabled for quantity data
    And the Z-score threshold for subcategory is "2.0"
    When Rule 8 is executed
    Then imbalanced subcategory cases should be identified
    And store-level results should be generated with quantity adjustments
    And detailed imbalance cases should be generated
    And a summary report should be created
    And the output dataframes should conform to "Step8StoreResultsSchema" and "Step8SubcategoryImbalancesSchema"
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Rule 8 fails due to missing clustering results file
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results file is missing
    When Rule 8 is executed
    Then Rule 8 execution should fail with a "FileNotFoundError"
    And an error message indicating the missing clustering file should be displayed
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Rule 8 fails due to missing required quantity columns
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" is available
    And SPU quantity data is available but "quantity" column is missing
    When Rule 8 is executed
    Then Rule 8 execution should fail with a "ValueError"
    And an error message indicating the missing quantity column should be displayed
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: No rebalancing recommendations when no valid Z-score groups are found
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" is available
    And SPU quantity data with "str_code", "spu_code", "quantity" is available
    And all clusters are too small to form valid Z-score groups
    When Rule 8 is executed
    Then store-level results should be generated with zero total quantity adjustments
    And detailed imbalance cases should be empty or contain no adjustments
    And the summary report should indicate no valid Z-score groups were found
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
    And SPU quantity data with "str_code", "spu_code", "quantity" is available
    And seasonal blending is enabled with seasonal period "<seasonal_period>"
    And seasonal weight is "<seasonal_weight>"
    And the Z-score threshold for SPU is "3.0"
    And rebalance mode is "increase_only"
    When Rule 8 is executed
    Then imbalanced SPU cases should be identified
    And store-level results should be generated with quantity adjustments
    And detailed imbalance cases should be generated
    And a summary report should be created
    And the output dataframes should conform to "Step8StoreResultsSchema" and "Step8ImbalancesSchema"
    Examples:
      | period  | seasonal_period | seasonal_weight |
      | 202509A | 202408A        | 0.6             |
      | 202509A | 202408B        | 0.4             |
      | 202508A | 202407A        | 0.5             |
      | 202508B | 202407B        | 0.7             |

  Scenario Outline: 5-cluster subset validation with Z-score threshold sweeps
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And a 5-cluster subset is selected with high/average consumption spread
    And clustering results with "str_code" and "cluster_id" are available
    And store config data with "str_code" is available
    And SPU quantity data with "str_code", "spu_code", "quantity" is available
    And the Z-score threshold for SPU is "<z_threshold>"
    And rebalance mode is "increase_only"
    When Rule 8 is executed
    Then imbalanced SPU cases should be identified
    And store-level results should be generated with quantity adjustments
    And detailed imbalance cases should be generated
    And a summary report should be created
    And the output dataframes should conform to "Step8StoreResultsSchema" and "Step8ImbalancesSchema"
    Examples:
      | period  | z_threshold |
      | 202509A | 2.0         |
      | 202509A | 2.5         |
      | 202509A | 3.0         |
      | 202508A | 2.0         |
      | 202508B | 3.0         |
