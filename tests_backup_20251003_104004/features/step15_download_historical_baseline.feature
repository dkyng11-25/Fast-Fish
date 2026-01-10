Feature: Step 15 Download Historical Baseline Data Validation

  As a data pipeline operator
  I want to validate that Step 15 creates historical baselines correctly and produces valid YoY comparisons
  So that the historical analysis provides reliable insights for decision making

  Background:
    Given a target period of "<target_period>" is set
    And a baseline period of "<baseline_period>" is set
    And the historical analysis is enabled

  Scenario Outline: Valid historical baseline creation with complete data
    Given the historical SPU sales file "data/api_data/complete_spu_sales_202407A.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    And the current analysis file "output/enhanced_fast_fish_format_202508A.csv" exists
    And all input files have valid data structure
    When Step 15 historical baseline creation is executed
    Then historical reference CSV should be generated
    And year-over-year comparison CSV should be generated
    And historical insights JSON should be generated
    And the historical reference should have store group and category columns
    And the YoY comparison should have baseline and current metrics
    And the output dataframes should conform to "Step15HistoricalSchema"

    Examples:
      | target_period | baseline_period |
      | 202509A       | 202408A         |
      | 202508A       | 202407A         |
      | 202508B       | 202407B         |

  Scenario Outline: Step 15 fails when historical SPU sales file is missing
    Given a target period of "<target_period>" is set
    And a baseline period of "<baseline_period>" is set
    And the historical SPU sales file "data/api_data/complete_spu_sales_<baseline_period>.csv" does not exist
    And the clustering results file "output/clustering_results_spu.csv" exists
    And the current analysis file "output/enhanced_fast_fish_format_<target_period>.csv" exists
    When Step 15 historical baseline creation is executed
    Then the historical baseline creation should fail with error
    And an appropriate error message should be logged
    Examples:
      | target_period | baseline_period |
      | 202509A       | 202408A         |
      | 202508A       | 202407A         |
      | 202508B       | 202407B         |

  Scenario Outline: Step 15 handles missing clustering results gracefully
    Given a target period of "<target_period>" is set
    And a baseline period of "<baseline_period>" is set
    And the historical SPU sales file "data/api_data/complete_spu_sales_<baseline_period>.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" does not exist
    And the current analysis file "output/enhanced_fast_fish_format_<target_period>.csv" exists
    And all input files have valid data structure
    When Step 15 historical baseline creation is executed
    Then historical reference CSV should be generated
    And store groups should be set to "Store Group Unknown"
    And the output dataframes should conform to "Step15HistoricalSchema"
    Examples:
      | target_period | baseline_period |
      | 202509A       | 202408A         |
      | 202508A       | 202407A         |
      | 202508B       | 202407B         |

  Scenario Outline: 15-store subsample validation with historical data
    Given a target period of "<target_period>" is set
    And a baseline period of "<baseline_period>" is set
    And a 15-store subsample is selected for validation
    And the historical SPU sales file "data/api_data/complete_spu_sales_<baseline_period>.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    And the current analysis file "output/enhanced_fast_fish_format_<target_period>.csv" exists
    And all input files have valid data structure
    When Step 15 historical baseline creation is executed
    Then historical reference CSV should be generated
    And year-over-year comparison CSV should be generated
    And historical insights JSON should be generated
    And the 15-store subsample should be validated
    And the output dataframes should conform to "Step15HistoricalSchema"
    Examples:
      | target_period | baseline_period |
      | 202509A       | 202408A         |
      | 202508A       | 202407A         |
      | 202508B       | 202407B         |

  Scenario Outline: Input/output formatting validation
    Given a target period of "<target_period>" is set
    And a baseline period of "<baseline_period>" is set
    And the historical SPU sales file "data/api_data/complete_spu_sales_<baseline_period>.csv" exists
    And the clustering results file "output/clustering_results_spu.csv" exists
    And the current analysis file "output/enhanced_fast_fish_format_<target_period>.csv" exists
    And all input files have valid data structure
    When Step 15 historical baseline creation is executed
    Then historical reference CSV should be generated with proper formatting
    And year-over-year comparison CSV should be generated with proper formatting
    And historical insights JSON should be generated with proper formatting
    And all output files should have consistent column naming
    And all output files should have proper data types
    And the output dataframes should conform to "Step15HistoricalSchema"
    Examples:
      | target_period | baseline_period |
      | 202509A       | 202408A         |
      | 202508A       | 202407A         |
      | 202508B       | 202407B         |
