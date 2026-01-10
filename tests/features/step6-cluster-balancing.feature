Feature: Step 6 - Cluster Balancing
  As a merchandising analyst
  I want clusters to be balanced to approximately 50 stores each
  So that each cluster is manageable and operationally efficient

  Background:
    Given the cluster analysis step is configured
    And the target cluster size is 50 stores
    And the minimum cluster size is 30 stores
    And the maximum cluster size is 60 stores

  @critical @balancing
  Scenario: Balance clusters after initial KMeans clustering
    Given I have a dataset with 2274 stores
    And I have performed initial KMeans clustering with 46 clusters
    And the initial clusters are unbalanced with sizes ranging from 1 to 117 stores
    When I apply cluster balancing
    Then all clusters should have between 30 and 60 stores
    And the mean cluster size should be approximately 50 stores
    And the standard deviation should be less than 10 stores
    And no cluster should have fewer than 30 stores
    And no cluster should have more than 60 stores

  @critical @balancing
  Scenario: Balancing converges within maximum iterations
    Given I have a dataset with 2274 stores
    And I have performed initial KMeans clustering with 46 clusters
    And the maximum balance iterations is set to 100
    When I apply cluster balancing
    Then the balancing should converge within 100 iterations
    And the final cluster sizes should meet all constraints

  @balancing @quality
  Scenario: Balancing preserves cluster quality
    Given I have a dataset with 2274 stores
    And I have performed initial KMeans clustering
    And I have calculated the initial silhouette score
    When I apply cluster balancing
    Then the silhouette score should not decrease by more than 0.1
    And stores should be moved to their nearest available cluster
    And the farthest stores from cluster centers should be moved first

  @balancing @configuration
  Scenario: Balancing respects configurable parameters
    Given I have a dataset with 100 stores
    And I configure target cluster size to 25 stores
    And I configure minimum cluster size to 20 stores
    And I configure maximum cluster size to 30 stores
    When I apply cluster balancing
    Then all clusters should have between 20 and 30 stores
    And the mean cluster size should be approximately 25 stores

  @balancing @edge-case
  Scenario: Balancing handles oversized clusters
    Given I have initial clusters with the following sizes:
      | cluster_id | size |
      | 0          | 117  |
      | 1          | 82   |
      | 2          | 73   |
      | 3          | 50   |
    And the maximum cluster size is 60 stores
    When I apply cluster balancing
    Then cluster 0 should have at most 60 stores
    And cluster 1 should have at most 60 stores
    And cluster 2 should have at most 60 stores
    And excess stores should be moved to nearest available clusters

  @balancing @edge-case
  Scenario: Balancing handles undersized clusters
    Given I have initial clusters with the following sizes:
      | cluster_id | size |
      | 0          | 5    |
      | 1          | 11   |
      | 2          | 19   |
      | 3          | 50   |
    And the minimum cluster size is 30 stores
    When I apply cluster balancing
    Then cluster 0 should have at least 30 stores
    And cluster 1 should have at least 30 stores
    And cluster 2 should have at least 30 stores
    And stores should be moved from oversized clusters

  @balancing @distance
  Scenario: Balancing moves stores based on distance
    Given I have a cluster with 80 stores
    And the maximum cluster size is 60 stores
    And I need to move 20 stores out of this cluster
    When I apply cluster balancing
    Then the 20 farthest stores from the cluster center should be moved
    And each store should be moved to its nearest non-full cluster
    And the cluster quality should be minimally impacted

  @balancing @integration
  Scenario: Balancing integrates with temperature-aware clustering
    Given I have 100 stores with temperature data
    And I enable temperature-aware clustering
    And I enable cluster balancing
    When I perform clustering analysis
    Then clusters should be balanced within temperature bands
    And each temperature band should have balanced clusters
    And the overall cluster sizes should meet constraints

  @balancing @validation
  Scenario: Validation fails if clusters are not balanced
    Given I have performed clustering
    And cluster balancing is enabled
    And some clusters have fewer than 30 stores
    When I validate the clustering results
    Then validation should fail with a clear error message
    And the error should list all undersized clusters
    And the error should list all oversized clusters

  @balancing @performance
  Scenario: Balancing completes in reasonable time
    Given I have a dataset with 2274 stores
    And I have 46 clusters to balance
    When I apply cluster balancing
    Then the balancing should complete in less than 10 seconds
    And the algorithm should log progress every 10 iterations

  @balancing @legacy-comparison
  Scenario: Refactored balancing matches legacy behavior
    Given I have the same dataset used in legacy Step 6
    And I use the same clustering parameters as legacy
    When I apply cluster balancing
    Then the cluster size distribution should match legacy within 5 stores
    And at least 90% of stores should be in the same clusters as legacy
    And the mean cluster size should be within 1 store of legacy

  @balancing @disable
  Scenario: Balancing can be disabled
    Given I have a dataset with 2274 stores
    And I disable cluster balancing
    When I perform clustering analysis
    Then the clusters should remain unbalanced
    And the initial KMeans cluster assignments should be used
    And no balancing iterations should occur

  @balancing @logging
  Scenario: Balancing logs detailed progress
    Given I have a dataset with 2274 stores
    And I enable cluster balancing
    When I apply cluster balancing
    Then the log should show initial cluster sizes
    Then the log should show progress every 10 iterations
    And the log should show final cluster sizes
    And the log should show the cluster size range
    And the log should show the number of iterations taken

  @balancing @metrics
  Scenario: Balancing tracks quality metrics
    Given I have performed initial clustering
    And I have calculated initial quality metrics
    When I apply cluster balancing
    Then the system should track silhouette score before and after
    And the system should track Calinski-Harabasz score before and after
    And the system should track Davies-Bouldin score before and after
    And the system should log any significant quality degradation

  @balancing @empty-cluster
  Scenario: Balancing handles empty clusters gracefully
    Given I have initial clustering with an empty cluster
    When I apply cluster balancing
    Then the empty cluster should be filled from oversized clusters
    Or the empty cluster should be removed from the cluster list
    And the algorithm should not crash
    And the final result should have no empty clusters
