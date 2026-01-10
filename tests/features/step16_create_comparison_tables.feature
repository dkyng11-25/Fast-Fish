Feature: Step 16 Create Comparison Tables Data Validation

  As a data pipeline operator
  I want to validate that Step 16 creates Excel comparison tables correctly
  So that the comparison analysis provides reliable insights for decision making

  Background:
    Given a target period of "202508A" is set
    And a baseline period of "202407A" is set
    And the comparison analysis is enabled

  Scenario Outline: Valid Excel workbook generation with all required data
    Given the YOY comparison file "output/year_over_year_comparison_202407A_20250917_123456.csv" exists
    And the historical reference file "output/historical_reference_202407A_20250917_123456.csv" exists
    And all input files have valid data structure
    When Step 16 comparison table creation is executed
    Then Excel workbook should be generated
    And the workbook should contain summary sheet
    And the workbook should contain category comparison sheet
    And the workbook should contain store group comparison sheet
    And the workbook should have proper formatting and filters
    And the output dataframes should conform to "Step16ComparisonSchema"

    Examples:
      | target_period | baseline_period |
      | 202508A       | 202407A         |
      | 202508B       | 202407B         |

  Scenario: Step 16 fails when YOY comparison file is missing
    Given the YOY comparison file "output/year_over_year_comparison_202407A_20250917_123456.csv" does not exist
    And the historical reference file "output/historical_reference_202407A_20250917_123456.csv" exists
    When Step 16 comparison table creation is executed
    Then the comparison table creation should fail with error
    And an appropriate error message should be logged
