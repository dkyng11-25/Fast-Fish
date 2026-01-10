Feature: Step 6 - Cluster Analysis
  As a data scientist
  I want to cluster stores based on their sales patterns
  So that I can identify similar store groups for targeted merchandising

  # NOTE: Test Data Conventions
  # - Matrix types: "spu", "subcategory", "category_agg"
  # - Store codes: Format "store_NNNN" (e.g., "store_0001")
  # - Feature names: Format "feature_NNN" or "spu_NNN" (arbitrary test values)
  # - Temperature bands: "Cold (<10°C)", "Cool (10-18°C)", "Moderate (18-23°C)", "Warm (23-28°C)", "Hot (≥28°C)"
  # - Cluster sizes: Target 50 stores/cluster, bounds [30, 60]
  # - Tests are data-agnostic and work with any valid format

  Background:
    Given normalized and original matrices are available for stores
    And clustering configuration is set with target size and bounds
    And PCA components are configured based on matrix type

  # ============================================================================
  # SETUP Phase: Data Loading & Configuration
  # ============================================================================

  Scenario: Load matrices successfully
    Given a normalized matrix with 100 stores and 50 features
    And an original matrix with matching dimensions
    When the cluster analysis step loads the data
    Then both matrices should be loaded successfully
    And matrix indices should be string type
    And matrix shapes should match

  Scenario: Handle missing normalized matrix
    Given the normalized matrix file does not exist
    When the cluster analysis step attempts to load data
    Then a FileNotFoundError should be raised
    And the error message should mention "Normalized matrix not found"

  Scenario: Handle missing original matrix
    Given the original matrix file does not exist
    When the cluster analysis step attempts to load data
    Then a FileNotFoundError should be raised
    And the error message should mention "Original matrix not found"

  Scenario: Handle matrix shape mismatch
    Given a normalized matrix with 100 stores and 50 features
    And an original matrix with 80 stores and 50 features
    When the cluster analysis step loads the data
    Then a warning should be logged about shape mismatch
    But processing should continue

  Scenario: Load temperature data when constraints enabled
    Given temperature constraints are enabled
    And temperature data is available for stores
    When the cluster analysis step loads the data
    Then temperature data should be loaded successfully
    And temperature band column should be identified
    And store indices should be aligned

  Scenario: Handle missing temperature data gracefully
    Given temperature constraints are enabled
    But temperature data file does not exist
    When the cluster analysis step loads the data
    Then a warning should be logged
    And clustering should proceed without temperature constraints

  Scenario: Support multiple temperature column names
    Given temperature data with "str_code" column
    When the cluster analysis step loads the data
    Then temperature data should be indexed by str_code
    
  Scenario: Support alternative temperature column names
    Given temperature data with "store_code" column
    When the cluster analysis step loads the data
    Then temperature data should be indexed by store_code

  # ============================================================================
  # APPLY Phase: PCA Transformation
  # ============================================================================

  Scenario: Apply PCA transformation successfully
    Given a normalized matrix with 100 stores and 50 features
    And PCA components set to 20
    When PCA transformation is applied
    Then dimensionality should be reduced to 20 components
    And variance explained should be calculated
    And PCA DataFrame should have PC1 through PC20 columns

  Scenario: Handle PCA with more components than features
    Given a normalized matrix with 100 stores and 30 features
    And PCA components set to 50
    When PCA transformation is applied
    Then PCA should use 30 components (min of requested and available)
    And transformation should complete successfully

  Scenario: Handle PCA with more components than stores
    Given a normalized matrix with 20 stores and 50 features
    And PCA components set to 50
    When PCA transformation is applied
    Then PCA should use 20 components (min of requested and stores)
    And transformation should complete successfully

  # ============================================================================
  # APPLY Phase: Clustering
  # ============================================================================

  Scenario: Determine optimal cluster count
    Given 150 stores are available
    And target cluster size is 50
    When optimal cluster count is calculated
    Then 3 clusters should be determined
    And calculation should round up for uneven division

  Scenario: Perform initial KMeans clustering
    Given PCA-transformed data with 100 stores
    And 2 clusters are requested
    When initial clustering is performed
    Then all stores should be assigned to clusters
    And cluster labels should be 0 and 1
    And cluster statistics should be calculated

  Scenario: Balance clusters to respect size bounds
    Given initial clusters with sizes [80, 20]
    And cluster size bounds are [30, 60]
    When cluster balancing is performed
    Then all clusters should be within bounds
    And stores should be reassigned as needed
    And balancing should converge within iterations

  Scenario: Handle undersized clusters
    Given a cluster with 15 stores (below minimum of 30)
    When cluster balancing is performed
    Then stores from larger clusters should be reassigned
    And the cluster should reach minimum size

  Scenario: Handle oversized clusters
    Given a cluster with 80 stores (above maximum of 60)
    When cluster balancing is performed
    Then farthest stores should be reassigned to other clusters
    And the cluster should be within maximum size

  # ============================================================================
  # APPLY Phase: Temperature-Aware Clustering
  # ============================================================================

  Scenario: Apply temperature-aware clustering when enabled
    Given temperature constraints are enabled
    And temperature data is available
    And initial clusters are created
    When temperature-aware clustering is applied
    Then stores should be regrouped by temperature band
    And each temperature band should have its own clusters
    And cluster IDs should be unique across bands

  Scenario: Skip temperature-aware clustering when disabled
    Given temperature constraints are disabled
    And initial clusters are created
    When clustering is finalized
    Then temperature-aware regrouping should be skipped
    And original cluster assignments should be preserved

  Scenario: Handle stores without temperature data
    Given temperature constraints are enabled
    And some stores lack temperature data
    When temperature-aware clustering is applied
    Then stores without temperature data should be excluded
    And only stores with temperature data should be regrouped

  # ============================================================================
  # APPLY Phase: Cluster Analysis
  # ============================================================================

  Scenario: Calculate cluster profiles
    Given clusters are assigned
    And original matrix data is available
    When cluster profiles are calculated
    Then mean values should be computed for each feature
    And profiles should be created for each cluster
    And top features should be identified

  Scenario: Identify top features per cluster
    Given cluster profiles are calculated
    When top features are identified
    Then features should be ranked by mean value
    And top 10 features should be selected per cluster

  # ============================================================================
  # VALIDATE Phase: Quality Metrics
  # ============================================================================

  Scenario: Calculate overall clustering metrics
    Given clustering is complete
    When overall metrics are calculated
    Then silhouette score should be computed
    And Davies-Bouldin index should be computed
    And Calinski-Harabasz score should be computed
    And metrics should be within valid ranges

  Scenario: Calculate per-cluster metrics
    Given clustering is complete
    When per-cluster metrics are calculated
    Then cluster sizes should be reported
    And intra-cluster distances should be computed
    And cluster cohesion should be measured
    And metrics should be calculated for each cluster

  # ============================================================================
  # PERSIST Phase: Save Results
  # ============================================================================

  Scenario: Save clustering results with dual output pattern
    Given clustering is complete
    And period label is "202501A"
    When clustering results are saved
    Then timestamped file should be created
    And period-labeled symlink should be created
    And generic symlink should be created
    And all three should point to same data

  Scenario: Output both Cluster and cluster_id columns
    Given clustering results are ready
    When results are saved to CSV
    Then output should contain "Cluster" column
    And output should contain "cluster_id" column
    And both columns should have identical values
    And this ensures downstream compatibility

  Scenario: Save cluster profiles
    Given cluster profiles are calculated
    When profiles are saved
    Then profile file should be created with dual output pattern
    And profiles should include mean values per feature
    And profiles should include cluster metadata

  Scenario: Save per-cluster metrics
    Given per-cluster metrics are calculated
    When metrics are saved
    Then metrics file should be created with dual output pattern
    And metrics should include size, cohesion, separation

  # ============================================================================
  # PERSIST Phase: Visualizations
  # ============================================================================

  Scenario: Create cluster visualization
    Given PCA-transformed data is available
    And cluster assignments are complete
    When cluster visualization is created
    Then scatter plot should be generated
    And clusters should be color-coded
    And plot should be saved to output directory

  Scenario: Create cluster size distribution chart
    Given cluster assignments are complete
    When size distribution chart is created
    Then bar chart should show stores per cluster
    And chart should be saved to output directory

  # ============================================================================
  # Integration Scenarios
  # ============================================================================

  Scenario: Complete clustering workflow for SPU matrix
    Given matrix type is "spu"
    And normalized and original SPU matrices are available
    And PCA components are set to 20
    And target cluster size is 50
    When the cluster analysis step is executed
    Then clustering should complete successfully
    And clustering results should be saved
    And cluster profiles should be saved
    And visualizations should be created
    And output should be compatible with Step 7

  Scenario: Complete clustering workflow with temperature constraints
    Given matrix type is "spu"
    And temperature constraints are enabled
    And temperature data is available
    When the cluster analysis step is executed
    Then temperature-aware clustering should be applied
    And stores should be grouped by temperature band
    And results should include temperature metadata
    And output should be compatible with downstream steps

  Scenario: Handle subcategory matrix type
    Given matrix type is "subcategory"
    And normalized and original subcategory matrices are available
    And PCA components are set to 50
    When the cluster analysis step is executed
    Then clustering should use subcategory-specific configuration
    And results should be saved with "subcategory" in filename
    And output should be compatible with downstream steps

  # ============================================================================
  # Edge Cases
  # ============================================================================

  Scenario: Handle very small dataset
    Given a normalized matrix with 20 stores and 10 features
    When the cluster analysis step is executed
    Then PCA components should be adjusted to dataset size
    And cluster count should be adjusted to dataset size
    And clustering should complete without errors

  Scenario: Handle very large dataset
    Given a normalized matrix with 1000 stores and 500 features
    When the cluster analysis step is executed
    Then progress messages should be logged
    And PCA should handle high dimensionality
    And clustering should complete within reasonable time

  Scenario: Handle dataset with missing values
    Given a normalized matrix with some NaN values
    When the cluster analysis step is executed
    Then missing values should be handled appropriately
    And clustering should complete or raise clear error

  Scenario: Handle single cluster scenario
    Given a normalized matrix with 40 stores
    And target cluster size is 50
    When the cluster analysis step is executed
    Then a single cluster should be created
    And all stores should be in that cluster
    And metrics should be calculated appropriately

  # ============================================================================
  # VALIDATE Phase: Validation & Error Raising (Added 2025-10-23)
  # ============================================================================
  # NOTE: VALIDATE phase redesigned to validate and raise errors, not calculate metrics
  # Metrics are now calculated at END of APPLY phase

  Scenario: Validation passes with valid clustering results
    Given a step instance with valid configuration
    And the context has valid clustering results with all required data
    When the step validation is executed
    Then no error should be raised
    And validation success should be logged

  Scenario: Validation fails when no clustering results exist
    Given a step instance with valid configuration
    And the context has no clustering results
    When the step validation is executed
    Then a DataValidationError should be raised
    And the error message should contain "No clustering results generated"

  Scenario: Validation fails when results DataFrame is None
    Given a step instance with valid configuration
    And the context results DataFrame is None
    When the step validation is executed
    Then a DataValidationError should be raised
    And the error message should mention clustering results

  Scenario: Validation fails when results DataFrame is empty
    Given a step instance with valid configuration
    And the context results DataFrame is empty
    When the step validation is executed
    Then a DataValidationError should be raised
    And the error message should mention clustering results

  Scenario: Validation fails when no clusters generated
    Given a step instance with valid configuration
    And the context has results with zero clusters
    When the step validation is executed
    Then a DataValidationError should be raised
    And the error message should contain "No clusters generated"

  Scenario: Validation passes when ONE cluster is undersized (remainder cluster)
    Given a step instance with min_cluster_size of 30
    And the context has clusters with only 20 stores
    When the step validation is executed
    Then no error should be raised
    # Note: AIS-153 allows ONE undersized cluster to handle remainder when stores not perfectly divisible

  Scenario: Validation fails when multiple clusters are undersized
    Given a step instance with min_cluster_size of 30
    And the context has multiple clusters smaller than 30 stores
    When the step validation is executed
    Then a DataValidationError should be raised
    And the error message should list all undersized clusters

  Scenario: Validation fails when clusters are oversized
    Given a step instance with max_cluster_size of 60
    And the context has clusters with 80 stores
    When the step validation is executed
    Then a DataValidationError should be raised
    And the error message should mention "larger than maximum size"
    And the error message should include cluster details

  Scenario: Validation fails when multiple clusters are oversized
    Given a step instance with max_cluster_size of 60
    And the context has multiple clusters larger than 60 stores
    When the step validation is executed
    Then a DataValidationError should be raised
    And the error message should list all oversized clusters

  Scenario: Validation fails when stores have no cluster assignment
    Given a step instance with valid configuration
    And the context has results with null cluster values
    When the step validation is executed
    Then a DataValidationError should be raised
    And the error message should contain "Stores without cluster assignment"

  Scenario: Validation fails when clustering quality is very poor
    Given a step instance with valid configuration
    And the context has clustering with silhouette score of -0.6
    When the step validation is executed
    Then a DataValidationError should be raised
    And the error message should contain "Poor clustering quality"
    And the error message should include the actual silhouette score

  Scenario: Validation passes with poor but acceptable silhouette score
    Given a step instance with valid configuration
    And the context has clustering with silhouette score of -0.4
    When the step validation is executed
    Then no error should be raised
    And validation success should be logged

  Scenario: Validation passes with good silhouette score
    Given a step instance with valid configuration
    And the context has clustering with silhouette score of 0.5
    When the step validation is executed
    Then no error should be raised
    And validation success should be logged

  Scenario: Validation fails when str_code column is missing
    Given a step instance with valid configuration
    And the context has results missing the str_code column
    When the step validation is executed
    Then a DataValidationError should be raised
    And the error message should mention "Missing required columns"
    And the error message should list str_code

  Scenario: Validation fails when Cluster column is missing
    Given a step instance with valid configuration
    And the context has results missing the Cluster column
    When the step validation is executed
    Then a DataValidationError should be raised
    And the error message should mention "Missing required columns"
    And the error message should list Cluster

  Scenario: Validation fails when cluster_id column is missing
    Given a step instance with valid configuration
    And the context has results missing the cluster_id column
    When the step validation is executed
    Then a DataValidationError should be raised
    And the error message should mention "Missing required columns"
    And the error message should list cluster_id

  Scenario: Validation fails when multiple required columns are missing
    Given a step instance with valid configuration
    And the context has results missing str_code and Cluster columns
    When the step validation is executed
    Then a DataValidationError should be raised
    And the error message should mention "Missing required columns"
    And the error message should list all missing columns
