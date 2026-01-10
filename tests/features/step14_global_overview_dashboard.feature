Feature: Step 14 Global Overview Dashboard Data Validation

  As a data pipeline operator
  I want to validate that Step 14 creates comprehensive global overview dashboards correctly
  So that the dashboard provides reliable insights for decision making

  Background:
    Given the analysis level is "spu"
    And a current period of "202508A" is set
    And the dashboard generation is enabled

  Scenario Outline: Valid global overview dashboard generation with all required data
    Given the consolidated SPU results file "output/consolidated_spu_rule_results.csv" exists
    And the rule 7 details file "output/rule7_missing_spu_results.csv" exists
    And the rule 8 details file "output/rule8_imbalanced_spu_results.csv" exists
    And the rule 9 details file "output/rule9_below_minimum_spu_results.csv" exists
    And the rule 10 details file "output/rule10_smart_overcapacity_spu_results.csv" exists
    And the rule 11 details file "output/rule11_missed_sales_opportunity_spu_results.csv" exists
    And the rule 12 details file "output/rule12_sales_performance_spu_results.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    And all input files have valid data structure
    When Step 14 dashboard generation is executed
    Then the global overview dashboard should be generated
    And the dashboard should contain executive summary
    And the dashboard should contain rule violation breakdown
    And the dashboard should contain cluster performance matrix
    And the dashboard should contain geographic distribution overview
    And the dashboard should contain opportunity prioritization matrix
    And the dashboard should contain actionable insights and recommendations
    And the output dataframes should conform to "Step14DashboardSchema"

    Examples:
      | period  |
      | 202508A |
      | 202508B |

  Scenario Outline: Valid dashboard generation with missing rule details files
    Given the consolidated SPU results file "output/consolidated_spu_rule_results.csv" exists
    And the rule 7 details file "output/rule7_missing_spu_results.csv" does not exist
    And the rule 8 details file "output/rule8_imbalanced_spu_results.csv" exists
    And the rule 9 details file "output/rule9_below_minimum_spu_results.csv" exists
    And the rule 10 details file "output/rule10_smart_overcapacity_spu_results.csv" exists
    And the rule 11 details file "output/rule11_missed_sales_opportunity_spu_results.csv" exists
    And the rule 12 details file "output/rule12_sales_performance_spu_results.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    And all available input files have valid data structure
    When Step 14 dashboard generation is executed
    Then the global overview dashboard should be generated
    And missing rule details should be handled gracefully
    And the dashboard should contain executive summary
    And the output dataframes should conform to "Step14DashboardSchema"

    Examples:
      | period  |
      | 202508A |
      | 202508B |

  Scenario Outline: Valid dashboard generation with subcategory analysis level
    Given the analysis level is "subcategory"
    And the consolidated results file "output/consolidated_rule_results.csv" exists
    And the rule 7 details file "output/rule7_missing_category_results.csv" exists
    And the rule 8 details file "output/rule8_imbalanced_results.csv" exists
    And the rule 9 details file "output/rule9_below_minimum_results.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    And all input files have valid data structure
    When Step 14 dashboard generation is executed
    Then the global overview dashboard should be generated
    And the dashboard should be configured for subcategory analysis
    And the dashboard should contain executive summary
    And the output dataframes should conform to "Step14DashboardSchema"

    Examples:
      | period  |
      | 202508A |
      | 202508B |

  Scenario: Step 14 dashboard generation fails when consolidated results file is missing
    Given the consolidated SPU results file "output/consolidated_spu_rule_results.csv" does not exist
    And the rule 7 details file "output/rule7_missing_spu_results.csv" exists
    And the rule 8 details file "output/rule8_imbalanced_spu_results.csv" exists
    And the rule 9 details file "output/rule9_below_minimum_spu_results.csv" exists
    And the rule 10 details file "output/rule10_smart_overcapacity_spu_results.csv" exists
    And the rule 11 details file "output/rule11_missed_sales_opportunity_spu_results.csv" exists
    And the rule 12 details file "output/rule12_sales_performance_spu_results.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    When Step 14 dashboard generation is executed
    Then the dashboard generation should fail with error
    And an appropriate error message should be logged

  Scenario: Step 14 dashboard generation fails when clustering results file is missing
    Given the consolidated SPU results file "output/consolidated_spu_rule_results.csv" exists
    And the rule 7 details file "output/rule7_missing_spu_results.csv" exists
    And the rule 8 details file "output/rule8_imbalanced_spu_results.csv" exists
    And the rule 9 details file "output/rule9_below_minimum_spu_results.csv" exists
    And the rule 10 details file "output/rule10_smart_overcapacity_spu_results.csv" exists
    And the rule 11 details file "output/rule11_missed_sales_opportunity_spu_results.csv" exists
    And the rule 12 details file "output/rule12_sales_performance_spu_results.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" does not exist
    And all input files have valid data structure
    When Step 14 dashboard generation is executed
    Then the global overview dashboard should be generated
    And cluster performance matrix should be empty or show unknown clusters
    And the output dataframes should conform to "Step14DashboardSchema"

  Scenario: Step 14 dashboard generation handles invalid data structure gracefully
    Given the consolidated SPU results file "output/consolidated_spu_rule_results.csv" exists
    And the rule 7 details file "output/rule7_missing_spu_results.csv" exists
    And the rule 8 details file "output/rule8_imbalanced_spu_results.csv" exists
    And the rule 9 details file "output/rule9_below_minimum_spu_results.csv" exists
    And the rule 10 details file "output/rule10_smart_overcapacity_spu_results.csv" exists
    And the rule 11 details file "output/rule11_missed_sales_opportunity_spu_results.csv" exists
    And the rule 12 details file "output/rule12_sales_performance_spu_results.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    And some input files have invalid data structure
    When Step 14 dashboard generation is executed
    Then the global overview dashboard should be generated
    And invalid data should be handled gracefully
    And the dashboard should contain executive summary
    And the output dataframes should conform to "Step14DashboardSchema"

  Scenario: Step 14 dashboard generation creates interactive visualizations
    Given the consolidated SPU results file "output/consolidated_spu_rule_results.csv" exists
    And the rule 7 details file "output/rule7_missing_spu_results.csv" exists
    And the rule 8 details file "output/rule8_imbalanced_spu_results.csv" exists
    And the rule 9 details file "output/rule9_below_minimum_spu_results.csv" exists
    And the rule 10 details file "output/rule10_smart_overcapacity_spu_results.csv" exists
    And the rule 11 details file "output/rule11_missed_sales_opportunity_spu_results.csv" exists
    And the rule 12 details file "output/rule12_sales_performance_spu_results.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    And all input files have valid data structure
    When Step 14 dashboard generation is executed
    Then the global overview dashboard should be generated
    And the dashboard should contain interactive charts and graphs
    And the dashboard should be exportable as HTML
    And the dashboard should contain drill-down capabilities
    And the output dataframes should conform to "Step14DashboardSchema"

  Scenario: Step 14 dashboard generation includes SPU-level granular analysis
    Given the consolidated SPU results file "output/consolidated_spu_rule_results.csv" exists
    And the rule 7 details file "output/rule7_missing_spu_results.csv" exists
    And the rule 8 details file "output/rule8_imbalanced_spu_results.csv" exists
    And the rule 9 details file "output/rule9_below_minimum_spu_results.csv" exists
    And the rule 10 details file "output/rule10_smart_overcapacity_spu_results.csv" exists
    And the rule 11 details file "output/rule11_missed_sales_opportunity_spu_results.csv" exists
    And the rule 12 details file "output/rule12_sales_performance_spu_results.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    And all input files have valid data structure
    When Step 14 dashboard generation is executed
    Then the global overview dashboard should be generated
    And the dashboard should contain SPU-level analysis capabilities
    And the dashboard should show individual SPU performance metrics
    And the dashboard should allow SPU-level filtering and sorting
    And the output dataframes should conform to "Step14DashboardSchema"
