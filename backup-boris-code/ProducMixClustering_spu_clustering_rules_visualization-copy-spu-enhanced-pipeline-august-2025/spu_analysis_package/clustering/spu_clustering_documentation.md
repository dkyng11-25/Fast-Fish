# SPU-Level Clustering (Top 1000 SPUs) Results

## Overview
This document contains the results of spu clustering analysis performed on 2263 stores.

## Configuration
- **Matrix Type**: spu
- **Input Matrix**: data/normalized_spu_limited_matrix.csv
- **Original Matrix**: data/store_spu_limited_matrix.csv
- **Feature Type**: SPU
- **PCA Components**: 100
- **Target Cluster Size**: 50 stores per cluster

## Clustering Results
- **Number of Clusters**: 44
- **Total Stores**: 2263
- **Cluster Size Range**: 47 - 75 stores
- **Average Cluster Size**: 51.4 stores

## Quality Metrics
- **Silhouette Score**: -0.193
- **Calinski-Harabasz Score**: 9.8
- **Davies-Bouldin Score**: 7.251

## Cluster Size Distribution
[52, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 47, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 73, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 75, 50, 50, 50, 50, 50, 66]

## Files Generated
- `clustering_results_spu.csv`: Store-to-cluster assignments
- `cluster_profiles_spu.csv`: Detailed cluster profiles
- `per_cluster_metrics_spu.csv`: Quality metrics for each cluster
- `cluster_visualization_spu.png`: Cluster visualization plots

## Interpretation

This analysis clusters stores based on their SPU (Stock Keeping Unit) sales patterns. This provides
the most granular view of store similarities and can inform:
- Precise product allocation
- SKU-level inventory management
- Detailed customer preference analysis

## Usage
The main output file `clustering_results_spu.csv` contains store codes and their cluster assignments.
This can be used in downstream analysis steps for business rule validation and strategy development.

Generated on: 2025-06-14 21:52:28
Matrix Type: spu
