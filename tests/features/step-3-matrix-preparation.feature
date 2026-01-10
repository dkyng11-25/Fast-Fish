Feature: Matrix Preparation - Create normalized matrices for clustering analysis

  Background:
    Given aggregated data from previous pipeline steps
    And store coordinates and SPU mappings are available
    And target period configuration is set
    And matrix filtering parameters are configured

  Scenario: Load and aggregate multi-period data
    Given multiple periods of category and SPU data are available
    When loading data for matrix preparation
    Then aggregate category data across all periods
    And aggregate SPU data across all periods
    And handle missing periods gracefully with fallback mechanisms

  Scenario: Filter data based on prevalence criteria
    Given raw aggregated category and SPU data
    When applying filtering rules for matrix creation
    Then filter subcategories by minimum store prevalence (default: 5 stores)
    And filter stores by minimum subcategory count (default: 3 subcategories)
    And filter SPUs by minimum store prevalence (default: 3 stores)
    And filter SPUs by minimum sales volume (bottom 10% threshold)
    And filter stores by minimum SPU count (default: 10 SPUs)

  Scenario: Create subcategory-level matrices
    Given filtered subcategory data
    When creating subcategory matrices for clustering
    Then generate original sales amount matrix (stores × subcategories)
    And generate normalized matrix (row-normalized for clustering)
    And handle memory management for large subcategory counts
    And save subcategory store list and subcategory list metadata

  Scenario: Create SPU-level matrices
    Given filtered SPU data
    When creating SPU matrices for clustering
    Then generate original sales amount matrix (stores × SPUs)
    And apply memory management for large SPU counts (limit to top 1000)
    And generate normalized matrix for clustering analysis
    And save SPU store list and category list metadata

  Scenario: Create category-aggregated matrices
    Given filtered SPU data
    When aggregating SPUs to category level
    Then group SPU sales by category for each store
    And generate category-level sales matrix
    And normalize category matrix for clustering
    And save category-aggregated store list and category list

  Scenario: Handle anomaly store filtering
    Given store coordinates data with potential anomalies
    When identifying anomalous coordinate locations
    Then detect stores at predefined anomaly coordinates (21.9178, 110.854)
    And exclude anomaly stores from all matrix calculations
    And maintain data integrity across all matrix types

  Scenario: Validate matrix creation results
    Given generated matrices and metadata files
    When validating matrix preparation outputs
    Then confirm all required matrix files exist and are non-empty
    And verify matrix dimensions match expected store and product counts
    And validate normalization produces valid probability distributions
    And ensure no division by zero or invalid values

  Scenario: Memory management for large datasets
    Given large SPU datasets exceeding memory limits
    When processing SPU data for matrix creation
    Then limit SPU matrix to top 1000 SPUs by sales volume
    And create both limited SPU matrix and category-aggregated matrix
    And maintain data quality while managing memory constraints
    And log memory management decisions for transparency

  Scenario: Multi-period data aggregation
    Given data from multiple time periods
    When aggregating for comprehensive analysis
    Then combine data across current and year-over-year periods
    And handle varying data availability across periods
    And maintain period-level granularity when needed
    And aggregate to store-level metrics for clustering

  Scenario: Error handling and recovery
    Given potential failures in data loading or matrix creation
    When encountering errors during matrix preparation
    Then log detailed error information with context
    And attempt graceful degradation where possible
    And maintain partial results when full processing fails
    And provide clear error messages for troubleshooting

  Scenario: Output file organization and naming
    Given matrix creation completion
    When saving all matrix outputs and metadata
    Then create consistent file naming convention
    And save matrices in both original and normalized formats
    And generate store lists for each matrix type
    And generate product lists for each matrix type
    And organize files for easy downstream consumption

  Scenario: Performance optimization for large datasets
    Given large-scale store and product datasets
    When optimizing matrix creation performance
    Then use efficient pandas operations for pivot tables
    And minimize memory usage through strategic filtering
    And process data in manageable chunks when needed
    And provide progress logging for long-running operations
