Feature: Step 13 Consolidate SPU Rules Data Validation

  As a data pipeline operator
  I want to validate that Step 13 consolidates SPU-level rule outputs correctly and produces valid consolidated results
  So that the consolidated data is reliable for downstream analysis

  Background:
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And FAST_MODE is enabled
    And ENABLE_TREND_UTILS is disabled

  Scenario Outline: Valid SPU rule consolidation with all rule outputs available
    Given the rule 7 output file "output/rule7_missing_spu_sellthrough_opportunities.csv" exists
    And the rule 8 output file "output/rule8_imbalanced_spu_cases.csv" exists
    And the rule 9 output file "output/rule9_below_minimum_spu_sellthrough_opportunities.csv" exists
    And the rule 10 output file "output/rule10_spu_overcapacity_opportunities.csv" exists
    And the rule 11 output file "output/rule11_improved_missed_sales_opportunity_spu_details.csv" exists
    And the rule 12 output file "output/rule12_sales_performance_spu_details.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    And all rule output files have valid SPU-level data structure
    And the clustering results have "str_code" and "cluster_id" columns
    When Step 13 consolidation is executed
    Then consolidated SPU detailed results should be generated
    And consolidated store-level summary should be generated
    And the detailed results should have "str_code" and "spu_code" columns
    And the detailed results should have cluster mapping columns
    And the detailed results should have subcategory mapping columns
    And all SPU records should be deduplicated by (str_code, spu_code)
    And the output dataframes should conform to "Step13ConsolidatedSchema"

    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |
      | 202508B |

  Scenario Outline: Valid SPU rule consolidation with some rule outputs missing
    Given the rule 7 output file "output/rule7_missing_spu_sellthrough_opportunities.csv" exists
    And the rule 8 output file "output/rule8_imbalanced_spu_cases.csv" does not exist
    And the rule 9 output file "output/rule9_below_minimum_spu_sellthrough_opportunities.csv" exists
    And the rule 10 output file "output/rule10_spu_overcapacity_opportunities.csv" exists
    And the rule 11 output file "output/rule11_improved_missed_sales_opportunity_spu_details.csv" exists
    And the rule 12 output file "output/rule12_sales_performance_spu_details.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    And all available rule output files have valid SPU-level data structure
    When Step 13 consolidation is executed
    Then consolidated SPU detailed results should be generated
    And consolidated store-level summary should be generated
    And missing rule outputs should be logged
    And the output dataframes should conform to "Step13ConsolidatedSchema"

    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |
      | 202508B |

  Scenario Outline: Valid SPU rule consolidation with legacy fallback files
    Given the rule 7 detailed file "output/rule7_missing_spu_sellthrough_opportunities.csv" does not exist
    And the rule 7 results file "output/rule7_missing_spu_results.csv" exists
    And the rule 8 detailed file "output/rule8_imbalanced_spu_cases.csv" does not exist
    And the rule 8 results file "output/rule8_imbalanced_spu_results.csv" exists
    And the rule 9 detailed file "output/rule9_below_minimum_spu_sellthrough_opportunities.csv" does not exist
    And the rule 9 results file "output/rule9_below_minimum_spu_results.csv" exists
    And the rule 10 output file "output/rule10_spu_overcapacity_opportunities.csv" exists
    And the rule 11 detailed file "output/rule11_improved_missed_sales_opportunity_spu_details.csv" does not exist
    And the rule 11 results file "output/rule11_missed_sales_opportunity_spu_results.csv" exists
    And the rule 12 detailed file "output/rule12_sales_performance_spu_details.csv" does not exist
    And the rule 12 results file "output/rule12_sales_performance_spu_results.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    And all available rule output files have valid SPU-level data structure
    When Step 13 consolidation is executed
    Then consolidated SPU detailed results should be generated
    And consolidated store-level summary should be generated
    And legacy fallback files should be used
    And the output dataframes should conform to "Step13ConsolidatedSchema"

    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |
      | 202508B |

  Scenario Outline: Valid SPU rule consolidation with trend utilities enabled
    Given the rule 7 output file "output/rule7_missing_spu_sellthrough_opportunities.csv" exists
    And the rule 8 output file "output/rule8_imbalanced_spu_cases.csv" exists
    And the rule 9 output file "output/rule9_below_minimum_spu_sellthrough_opportunities.csv" exists
    And the rule 10 output file "output/rule10_spu_overcapacity_opportunities.csv" exists
    And the rule 11 output file "output/rule11_improved_missed_sales_opportunity_spu_details.csv" exists
    And the rule 12 output file "output/rule12_sales_performance_spu_details.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    And the weather data file "output/stores_with_feels_like_temperature.csv" exists
    And ENABLE_TREND_UTILS is enabled
    And all rule output files have valid SPU-level data structure
    When Step 13 consolidation is executed
    Then consolidated SPU detailed results should be generated
    And consolidated store-level summary should be generated
    And fashion enhanced suggestions should be generated
    And comprehensive trend enhanced suggestions should be generated
    And the output dataframes should conform to "Step13ConsolidatedSchema"

    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |
      | 202508B |

  Scenario: Step 13 consolidation fails when all rule output files are missing
    Given the rule 7 output file "output/rule7_missing_spu_sellthrough_opportunities.csv" does not exist
    And the rule 8 output file "output/rule8_imbalanced_spu_cases.csv" does not exist
    And the rule 9 output file "output/rule9_below_minimum_spu_sellthrough_opportunities.csv" does not exist
    And the rule 10 output file "output/rule10_spu_overcapacity_opportunities.csv" does not exist
    And the rule 11 output file "output/rule11_improved_missed_sales_opportunity_spu_details.csv" does not exist
    And the rule 12 output file "output/rule12_sales_performance_spu_details.csv" does not exist
    And the clustering results file "output/clustering_results_spu.csv" does not exist
    When Step 13 consolidation is executed
    Then the consolidation should fail with error
    And an appropriate error message should be logged

  Scenario: Step 13 consolidation fails when clustering results file is missing
    Given the rule 7 output file "output/rule7_missing_spu_sellthrough_opportunities.csv" exists
    And the rule 8 output file "output/rule8_imbalanced_spu_cases.csv" exists
    And the rule 9 output file "output/rule9_below_minimum_spu_sellthrough_opportunities.csv" exists
    And the rule 10 output file "output/rule10_spu_overcapacity_opportunities.csv" exists
    And the rule 11 output file "output/rule11_improved_missed_sales_opportunity_spu_details.csv" exists
    And the rule 12 output file "output/rule12_sales_performance_spu_details.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" does not exist
    And all rule output files have valid SPU-level data structure
    When Step 13 consolidation is executed
    Then consolidated SPU detailed results should be generated
    And consolidated store-level summary should be generated
    And cluster mapping should be set to NA
    And the output dataframes should conform to "Step13ConsolidatedSchema"

  Scenario: Step 13 consolidation handles missing columns gracefully
    Given the rule 7 output file "output/rule7_missing_spu_sellthrough_opportunities.csv" exists
    And the rule 8 output file "output/rule8_imbalanced_spu_cases.csv" exists
    And the rule 9 output file "output/rule9_below_minimum_spu_sellthrough_opportunities.csv" exists
    And the rule 10 output file "output/rule10_spu_overcapacity_opportunities.csv" exists
    And the rule 11 output file "output/rule11_improved_missed_sales_opportunity_spu_details.csv" exists
    And the rule 12 output file "output/rule12_sales_performance_spu_details.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    And some rule output files have missing required columns
    When Step 13 consolidation is executed
    Then consolidated SPU detailed results should be generated
    And consolidated store-level summary should be generated
    And missing columns should be set to NA
    And the output dataframes should conform to "Step13ConsolidatedSchema"

  Scenario: Step 13 consolidation handles duplicate SPU records correctly
    Given the rule 7 output file "output/rule7_missing_spu_sellthrough_opportunities.csv" exists
    And the rule 8 output file "output/rule8_imbalanced_spu_cases.csv" exists
    And the rule 9 output file "output/rule9_below_minimum_spu_sellthrough_opportunities.csv" exists
    And the rule 10 output file "output/rule10_spu_overcapacity_opportunities.csv" exists
    And the rule 11 output file "output/rule11_improved_missed_sales_opportunity_spu_details.csv" exists
    And the rule 12 output file "output/rule12_sales_performance_spu_details.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    And some rule output files contain duplicate (str_code, spu_code) records
    When Step 13 consolidation is executed
    Then consolidated SPU detailed results should be generated
    And consolidated store-level summary should be generated
    And duplicate records should be removed
    And each (str_code, spu_code) combination should appear only once
    And the output dataframes should conform to "Step13ConsolidatedSchema"

  Scenario: Step 13 consolidation generates period-labeled outputs
    Given the rule 7 output file "output/rule7_missing_spu_sellthrough_opportunities.csv" exists
    And the rule 8 output file "output/rule8_imbalanced_spu_cases.csv" exists
    And the rule 9 output file "output/rule9_below_minimum_spu_sellthrough_opportunities.csv" exists
    And the rule 10 output file "output/rule10_spu_overcapacity_opportunities.csv" exists
    And the rule 11 output file "output/rule11_improved_missed_sales_opportunity_spu_details.csv" exists
    And the rule 12 output file "output/rule12_sales_performance_spu_details.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    And all rule output files have valid SPU-level data structure
    When Step 13 consolidation is executed
    Then consolidated SPU detailed results should be generated
    And period-labeled detailed results should be generated
    And the period-labeled file should contain the current period in the filename
    And the output dataframes should conform to "Step13ConsolidatedSchema"
