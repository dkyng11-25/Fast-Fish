Feature: Step 17 Augment Recommendations Data Validation

  As a data pipeline operator
  I want to validate that Step 17 augments Fast Fish recommendations correctly with historical and trending data
  So that the augmented recommendations provide comprehensive insights for decision making

  Background:
    Given a target period of "202508A" is set
    And a baseline period of "202407A" is set
    And the augmentation is enabled

  Scenario Outline: Valid recommendation augmentation with complete data
    Given the Step 14 Fast Fish file "output/enhanced_fast_fish_format_202508A.csv" exists
    And the Step 15 historical reference file "output/historical_reference_202407A_20250917_123456.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    And the granular trend data file "output/granular_trend_data_preserved_202508A.csv" exists
    And ENABLE_TREND_UTILS is enabled
    And all input files have valid data structure
    When Step 17 recommendation augmentation is executed
    Then augmented recommendations CSV should be generated
    And the augmented file should contain historical columns
    And the augmented file should contain trending columns
    And the augmented file should have client-compliant formatting
    And the output dataframes should conform to "Step17AugmentedSchema"

    Examples:
      | target_period | baseline_period |
      | 202508A       | 202407A         |
      | 202508B       | 202407B         |

  Scenario: Step 17 handles missing historical data gracefully
    Given the Step 14 Fast Fish file "output/enhanced_fast_fish_format_202508A.csv" exists
    And the Step 15 historical reference file "output/historical_reference_202407A_20250917_123456.csv" does not exist
    And the clustering results file "output/clustering_results_spu.csv" exists
    And all input files have valid data structure
    When Step 17 recommendation augmentation is executed
    Then augmented recommendations CSV should be generated
    And historical columns should be set to NA
    And the output dataframes should conform to "Step17AugmentedSchema"
