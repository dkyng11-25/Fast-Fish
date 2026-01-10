Feature: Rule 7: Missing Category/SPU with Quantity Recommendations

  As a data pipeline operator
  I want to identify missing SPU/subcategory opportunities and recommend quantities
  So that stores can optimize their assortment and improve sales, with sell-through validation

  Scenario Outline: Successful identification of missing SPU opportunities with Fast Fish approval
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And SPU sales data with "str_code", "spu_code", "spu_sales_amt" is available
    And store config data with "str_code" is available
    And quantity data with "base_sal_qty", "fashion_sal_qty", "base_sal_amt", "fashion_sal_amt" is available
    And Fast Fish validation and ROI are enabled with ROI threshold "0.3" and min margin uplift "100"
    When Rule 7 is executed
    Then missing SPU opportunities should be identified
    And store-level results should be generated
    And detailed opportunities should be generated and be Fast Fish compliant
    And a summary report should be created
    And the output dataframes should conform to "Step7StoreResultsSchema" and "Step7OpportunitiesSchema"
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Missing SPU opportunities pass ROI thresholds with Fast Fish validation
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And SPU sales data with "str_code", "spu_code", "spu_sales_amt" is available
    And store config data with "str_code" is available
    And quantity data with "base_sal_qty", "fashion_sal_qty", "base_sal_amt", "fashion_sal_amt" is available
    And Fast Fish validation and ROI are enabled with ROI threshold "0.3" and min margin uplift "100"
    And opportunities are generated that meet all ROI thresholds
    When Rule 7 is executed
    Then missing SPU opportunities should be identified
    And store-level results should be generated
    And detailed opportunities should be generated and be Fast Fish compliant
    And a summary report should be created
    And the output dataframes should conform to "Step7StoreResultsSchema" and "Step7OpportunitiesSchema"
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Missing SPU opportunities fail ROI thresholds and are rejected
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And SPU sales data with "str_code", "spu_code", "spu_sales_amt" is available
    And store config data with "str_code" is available
    And quantity data with "base_sal_qty", "fashion_sal_qty", "base_sal_amt", "fashion_sal_amt" is available
    And Fast Fish validation and ROI are enabled with ROI threshold "0.5" and min margin uplift "1000"
    And opportunities are generated that fail ROI thresholds
    When Rule 7 is executed
    Then no sales performance opportunities should be identified
    And no output files related to opportunities should be generated
    And a summary report should be created and indicate no opportunities were found
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Successful identification of missing Subcategory opportunities without seasonal blending
    Given the analysis level is "subcategory"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And subcategory sales data with "str_code", "sub_cate_name", "sal_amt" is available
    And store config data with "str_code" is available
    And quantity data with "base_sal_qty", "fashion_sal_qty", "base_sal_amt", "fashion_sal_amt" is available
    And seasonal blending is disabled
    When Rule 7 is executed
    Then missing subcategory opportunities should be identified
    And store-level results should be generated
    And detailed subcategory opportunities should be generated
    And a summary report should be created
    And the output dataframes should conform to "Step7StoreResultsSchema" and "Step7SubcategoryOpportunitiesSchema"
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Rule 7 fails due to missing clustering results file
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results file is missing
    When Rule 7 is executed
    Then Rule 7 execution should fail with a "FileNotFoundError"
    And an error message indicating the missing clustering file should be displayed
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Rule 7 fails due to missing required sales columns
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And SPU sales data is available but "spu_sales_amt" column is missing
    And store config data with "str_code" is available
    When Rule 7 is executed
    Then Rule 7 execution should fail with a "ValueError"
    And an error message indicating the missing sales column should be displayed
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: No opportunities approved when sell-through validator is unavailable
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And SPU sales data with "str_code", "spu_code", "spu_sales_amt" is available
    And store config data with "str_code" is available
    And quantity data with "base_sal_qty", "fashion_sal_qty", "base_sal_amt", "fashion_sal_amt" is available
    And the sell-through validator is unavailable
    When Rule 7 is executed
    Then store-level results should be generated with zero Fast Fish approved opportunities
    And detailed opportunities should be generated but not be Fast Fish compliant
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Seasonal blending with recent and historical data
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And SPU sales data with "str_code", "spu_code", "spu_sales_amt" is available
    And store config data with "str_code" is available
    And quantity data with "base_sal_qty", "fashion_sal_qty", "base_sal_amt", "fashion_sal_amt" is available
    And seasonal blending is enabled with seasonal period "<seasonal_period>"
    And seasonal weight is "<seasonal_weight>"
    And Fast Fish validation and ROI are enabled with ROI threshold "0.3" and min margin uplift "100"
    When Rule 7 is executed
    Then missing SPU opportunities should be identified
    And store-level results should be generated
    And detailed opportunities should be generated and be Fast Fish compliant
    And a summary report should be created
    And the output dataframes should conform to "Step7StoreResultsSchema" and "Step7OpportunitiesSchema"
    Examples:
      | period  | seasonal_period | seasonal_weight |
      | 202509A | 202408A        | 0.6             |
      | 202509A | 202408B        | 0.4             |
      | 202508A | 202407A        | 0.5             |
      | 202508B | 202407B        | 0.7             |

  Scenario Outline: Backward compatibility file validation
    Given the analysis level is "subcategory"
    And a current period of "<period>" is set
    And clustering results with "str_code" and "cluster_id" are available
    And subcategory sales data with "str_code", "sub_cate_name", "sal_amt" is available
    And store config data with "str_code" is available
    And quantity data with "base_sal_qty", "fashion_sal_qty", "base_sal_amt", "fashion_sal_amt" is available
    And seasonal blending is disabled
    When Rule 7 is executed
    Then missing subcategory opportunities should be identified
    And store-level results should be generated
    And detailed subcategory opportunities should be generated
    And a summary report should be created
    And backward compatibility file "output/rule7_missing_category_results.csv" should be created
    And the output dataframes should conform to "Step7StoreResultsSchema" and "Step7SubcategoryOpportunitiesSchema"
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: 5-cluster subset validation with high/average consumption spread
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And a 5-cluster subset is selected with high/average consumption spread
    And clustering results with "str_code" and "cluster_id" are available
    And SPU sales data with "str_code", "spu_code", "spu_sales_amt" is available
    And store config data with "str_code" is available
    And quantity data with "base_sal_qty", "fashion_sal_qty", "base_sal_amt", "fashion_sal_amt" is available
    And Fast Fish validation and ROI are enabled with ROI threshold "0.3" and min margin uplift "100"
    When Rule 7 is executed
    Then missing SPU opportunities should be identified
    And store-level results should be generated
    And detailed opportunities should be generated and be Fast Fish compliant
    And a summary report should be created
    And the output dataframes should conform to "Step7StoreResultsSchema" and "Step7OpportunitiesSchema"
    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |
