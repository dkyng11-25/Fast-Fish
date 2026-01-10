Feature: Step 6 Cluster Analysis Data Validation

  As a data pipeline operator
  I want to validate that Step 6 cluster analysis processes input data correctly and produces valid output
  So that the clustering results are reliable for downstream analysis

  Background:
    Given the analysis level is "spu"
    And a current period of "<period>" is set

  Scenario Outline: Valid SPU-level clustering input data produces valid output
    Given the normalized SPU matrix "data/normalized_spu_limited_matrix.csv" exists
    And the original SPU matrix "data/store_spu_limited_matrix.csv" exists
    And the temperature data "output/stores_with_feels_like_temperature.csv" exists
    And the normalized matrix has valid structure with store codes as index and SPU codes as columns
    And the original matrix has matching structure to normalized matrix
    And the temperature data has "str_code" and temperature band columns
    And all matrices have at least "30" stores
    When Step 6 cluster analysis is executed
    Then clustering results should be generated
    And cluster profiles should be generated
    And the clustering results should have "str_code" and "cluster_id" columns
    And the cluster profiles should have cluster statistics columns
    And all cluster IDs should be non-negative integers
    And all stores should be assigned to exactly one cluster
    And the output dataframes should conform to "Step6ClusteringResultsSchema" and "Step6ClusterProfilesSchema"

    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Valid subcategory-level clustering input data produces valid output
    Given the analysis level is "subcategory"
    And the normalized subcategory matrix "data/normalized_subcategory_matrix.csv" exists
    And the original subcategory matrix "data/store_subcategory_matrix.csv" exists
    And the normalized matrix has valid structure with store codes as index and subcategory codes as columns
    And the original matrix has matching structure to normalized matrix
    And all matrices have at least "30" stores
    When Step 6 cluster analysis is executed
    Then clustering results should be generated
    And cluster profiles should be generated
    And the clustering results should have "str_code" and "cluster_id" columns
    And the cluster profiles should have cluster statistics columns
    And all cluster IDs should be non-negative integers
    And all stores should be assigned to exactly one cluster
    And the output dataframes should conform to "Step6ClusteringResultsSchema" and "Step6ClusterProfilesSchema"

    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Valid category-aggregated clustering input data produces valid output
    Given the analysis level is "category_agg"
    And the normalized category matrix "data/normalized_category_agg_matrix.csv" exists
    And the original category matrix "data/store_category_agg_matrix.csv" exists
    And the normalized matrix has valid structure with store codes as index and category codes as columns
    And the original matrix has matching structure to normalized matrix
    And all matrices have at least "30" stores
    When Step 6 cluster analysis is executed
    Then clustering results should be generated
    And cluster profiles should be generated
    And the clustering results should have "str_code" and "cluster_id" columns
    And the cluster profiles should have cluster statistics columns
    And all cluster IDs should be non-negative integers
    And all stores should be assigned to exactly one cluster
    And the output dataframes should conform to "Step6ClusteringResultsSchema" and "Step6ClusterProfilesSchema"

    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario: Step 6 fails when normalized matrix is missing
    Given the analysis level is "spu"
    And the normalized SPU matrix "data/normalized_spu_limited_matrix.csv" does not exist
    When Step 6 cluster analysis is executed
    Then an error should be reported about missing normalized matrix

  Scenario: Step 6 fails when original matrix is missing
    Given the analysis level is "spu"
    And the normalized SPU matrix "data/normalized_spu_limited_matrix.csv" exists
    And the original SPU matrix "data/store_spu_limited_matrix.csv" does not exist
    When Step 6 cluster analysis is executed
    Then an error should be reported about missing original matrix

  Scenario: Step 6 fails when normalized matrix has invalid structure
    Given the analysis level is "spu"
    And the normalized SPU matrix "data/normalized_spu_limited_matrix.csv" exists
    And the original SPU matrix "data/store_spu_limited_matrix.csv" exists
    And the normalized matrix has invalid structure with missing store codes or SPU codes
    When Step 6 cluster analysis is executed
    Then an error should be reported about invalid matrix structure

  Scenario: Step 6 fails when matrices have mismatched dimensions
    Given the analysis level is "spu"
    And the normalized SPU matrix "data/normalized_spu_limited_matrix.csv" exists
    And the original SPU matrix "data/store_spu_limited_matrix.csv" exists
    And the normalized matrix has "100" stores and "50" SPUs
    And the original matrix has "80" stores and "50" SPUs
    When Step 6 cluster analysis is executed
    Then an error should be reported about mismatched matrix dimensions

  Scenario: Step 6 fails when there are insufficient stores for clustering
    Given the analysis level is "spu"
    And the normalized SPU matrix "data/normalized_spu_limited_matrix.csv" exists
    And the original SPU matrix "data/store_spu_limited_matrix.csv" exists
    And the normalized matrix contains only "5" stores
    And the original matrix contains only "5" stores
    When Step 6 cluster analysis is executed
    Then an error should be reported about insufficient data for clustering

  Scenario: Step 6 continues without temperature data when temperature constraints are disabled
    Given the analysis level is "spu"
    And the normalized SPU matrix "data/normalized_spu_limited_matrix.csv" exists
    And the original SPU matrix "data/store_spu_limited_matrix.csv" exists
    And the temperature data "output/stores_with_feels_like_temperature.csv" does not exist
    And temperature constraints are disabled
    When Step 6 cluster analysis is executed
    Then clustering results should be generated
    And cluster profiles should be generated
    And the output dataframes should conform to "Step6ClusteringResultsSchema" and "Step6ClusterProfilesSchema"

  Scenario: Step 6 warns when temperature data is missing but temperature constraints are enabled
    Given the analysis level is "spu"
    And the normalized SPU matrix "data/normalized_spu_limited_matrix.csv" exists
    And the original SPU matrix "data/store_spu_limited_matrix.csv" exists
    And the temperature data "output/stores_with_feels_like_temperature.csv" does not exist
    And temperature constraints are enabled
    When Step 6 cluster analysis is executed
    Then a warning should be reported about missing temperature data
    And clustering results should be generated
    And cluster profiles should be generated
    And the output dataframes should conform to "Step6ClusteringResultsSchema" and "Step6ClusterProfilesSchema"

  Scenario: Step 6 fails when temperature data has invalid structure
    Given the analysis level is "spu"
    And the normalized SPU matrix "data/normalized_spu_limited_matrix.csv" exists
    And the original SPU matrix "data/store_spu_limited_matrix.csv" exists
    And the temperature data "output/stores_with_feels_like_temperature.csv" exists
    And the temperature data is missing "str_code" column
    And temperature constraints are enabled
    When Step 6 cluster analysis is executed
    Then an error should be reported about invalid temperature data structure

  Scenario Outline: Arbitrary subset of stores maintains clustering compliance
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And an arbitrary subset of "<store_count>" stores is selected
    And the subset selection is non-random and replicable
    And the normalized SPU matrix "data/normalized_spu_limited_matrix.csv" exists
    And the original SPU matrix "data/store_spu_limited_matrix.csv" exists
    And the temperature data "output/stores_with_feels_like_temperature.csv" exists
    When Step 6 cluster analysis is executed on the subset
    Then clustering results should be generated
    And all clusters should have standard sizes between "3" and "50" stores
    And all stores should be assigned to exactly one cluster
    And the output dataframes should conform to "Step6ClusteringResultsSchema" and "Step6ClusterProfilesSchema"

    Examples:
      | period  | store_count |
      | 202509A | 150         |
      | 202509A | 200         |
      | 202509A | 250         |
      | 202508A | 150         |
      | 202508B | 200         |

  Scenario Outline: Weather band compliance validation for clusters
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And the normalized SPU matrix "data/normalized_spu_limited_matrix.csv" exists
    And the original SPU matrix "data/store_spu_limited_matrix.csv" exists
    And the temperature data "output/stores_with_feels_like_temperature.csv" exists
    And temperature constraints are enabled
    When Step 6 cluster analysis is executed
    Then clustering results should be generated
    And each cluster should have weather band compliance
    And all stores within a cluster should have compatible temperature bands
    And the output dataframes should conform to "Step6ClusteringResultsSchema" and "Step6ClusterProfilesSchema"

    Examples:
      | period  |
      | 202509A |
      | 202508A |
      | 202508B |

  Scenario Outline: Different clustering algorithms produce valid results
    Given the analysis level is "spu"
    And a current period of "<period>" is set
    And the clustering algorithm is "<algorithm>"
    And the normalized SPU matrix "data/normalized_spu_limited_matrix.csv" exists
    And the original SPU matrix "data/store_spu_limited_matrix.csv" exists
    And the temperature data "output/stores_with_feels_like_temperature.csv" exists
    When Step 6 cluster analysis is executed
    Then clustering results should be generated
    And cluster profiles should be generated
    And the clustering results should have "str_code" and "cluster_id" columns
    And all cluster IDs should be non-negative integers
    And all stores should be assigned to exactly one cluster
    And the output dataframes should conform to "Step6ClusteringResultsSchema" and "Step6ClusterProfilesSchema"

    Examples:
      | period  | algorithm    |
      | 202509A | kmeans       |
      | 202509A | hierarchical |
      | 202508A | kmeans       |
      | 202508B | hierarchical |
