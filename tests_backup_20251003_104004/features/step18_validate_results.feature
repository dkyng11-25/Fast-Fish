Feature: Step 18 Validate Results Data Validation

  As a data pipeline operator
  I want to validate that Step 18 computes sell-through KPIs correctly and produces valid analysis
  So that the sell-through analysis provides reliable insights for decision making

  Background:
    Given a target period of "202508A" is set
    And a baseline period of "202407A" is set
    And the sell-through analysis is enabled

  Scenario Outline: Valid sell-through analysis with complete data
    Given the Step 17 augmented file "output/fast_fish_with_historical_and_cluster_trending_analysis_202508A_20250917_123456.csv" exists
    And the Step 15 historical reference file "output/historical_reference_202407A_20250917_123456.csv" exists
    And all input files have valid data structure
    When Step 18 sell-through analysis is executed
    Then sell-through analysis CSV should be generated
    And the analysis should contain SPU_Store_Days_Inventory calculations
    And the analysis should contain SPU_Store_Days_Sales calculations
    And the analysis should contain Sell_Through_Rate_Frac calculations
    And the analysis should contain Sell_Through_Rate_Pct calculations
    And the output dataframes should conform to "Step18SellThroughSchema"

    Examples:
      | target_period | baseline_period |
      | 202508A       | 202407A         |
      | 202508B       | 202407B         |

  Scenario: Step 18 handles missing historical match gracefully
    Given the Step 17 augmented file "output/fast_fish_with_historical_and_cluster_trending_analysis_202508A_20250917_123456.csv" exists
    And the Step 15 historical reference file "output/historical_reference_202407A_20250917_123456.csv" exists
    And some recommendations have no historical match
    When Step 18 sell-through analysis is executed
    Then sell-through analysis CSV should be generated
    And sell-through rates should be set to NA for unmatched records
    And the output dataframes should conform to "Step18SellThroughSchema"
