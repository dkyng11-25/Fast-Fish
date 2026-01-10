# Step 6: Clustering Analysis

## Overview
This step performs the core clustering analysis on the normalized store-subcategory matrix, identifying patterns and groupings in store performance data.

## Functionality

### Key Features
1. Clustering Algorithm
   - Implements K-means clustering
   - Optimizes cluster number
   - Handles high-dimensional data

2. Dimensionality Reduction
   - Applies PCA for visualization
   - Reduces feature space
   - Maintains data variance

## Input Requirements
- Normalized matrix from Step 3
- Clustering parameters

## Output Files
1. Clustering Results
   - Location: output/clustering_results.csv
   - Contains: Store cluster assignments
   - Format: CSV with columns: str_code, cluster, PC1, PC2

2. Cluster Profiles
   - Location: output/cluster_profiles.csv
   - Contains: Cluster characteristics
   - Format: CSV with cluster statistics

## Configuration
- Number of clusters
- PCA components
- Clustering parameters
- Optimization criteria

## Error Handling
1. Algorithm Issues
   - Convergence problems
   - Memory constraints
   - Numerical stability

2. Data Processing
   - Missing values
   - Invalid clusters
   - Dimensionality issues

## Performance Considerations
- Efficient clustering
- Memory optimization
- Progress tracking
- Parallel processing

## Dependencies
- scikit-learn
- pandas
- numpy
- typing

## Usage
python src/step6_cluster_analysis.py

## Troubleshooting
1. Clustering Problems
   - Check convergence
   - Verify cluster quality
   - Review optimization

2. Performance
   - Monitor memory usage
   - Check processing time
   - Review cluster stability