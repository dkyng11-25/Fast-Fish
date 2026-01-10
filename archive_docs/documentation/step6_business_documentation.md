# Step 6: Cluster Analysis for Subcategory and SPU-Level Data

## 1. Identification

**Name / Path:** `/src/step6_cluster_analysis.py`

**Component:** Machine Learning Analysis

**Owner:** Data Science Team

**Last Updated:** 2025-06-14

## 2. Purpose & Business Value

Performs sophisticated clustering analysis on store-product matrices to group similar stores based on their product mix patterns. This step enables targeted business rules and optimization strategies by identifying stores with comparable sales behaviors, environmental conditions, and product preferences. The system supports multiple clustering approaches for different analysis granularities.

## 3. Inputs

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| Normalized Matrices | CSV Files | Store-by-product matrices (subcategory, SPU, category) | Output of Step 3 |
| Original Matrices | CSV Files | Raw sales data matrices | Output of Step 3 |
| Temperature Data | CSV File | Feels-like temperature data for stores | Output of Step 5 (optional) |
| Store Coordinates | CSV File | Geographic coordinates for stores | Output of Step 2 |

## 4. Transformation Overview

The script performs advanced machine learning clustering with the following key processes:

1. **Multi-Level Clustering**: Supports subcategory-level, SPU-level, and category-aggregated clustering approaches
2. **PCA Dimensionality Reduction**: Reduces feature space while preserving variance for computational efficiency
3. **Temperature-Aware Clustering**: Optional clustering within temperature bands for environmental context
4. **Cluster Balancing**: Enforces minimum/maximum cluster size constraints for practical groupings
5. **Quality Metrics Calculation**: Computes comprehensive clustering evaluation metrics
6. **Cluster Profiling**: Creates detailed profiles of each cluster's characteristics
7. **Visualization Generation**: Produces 2D visualizations of cluster relationships

## 5. Outputs & Consumers

**Format / Schema:** CSV files, PNG visualizations, and Markdown documentation:
- `output/clustering_results_{matrix_type}.csv` - Store-level cluster assignments
- `output/cluster_profiles_{matrix_type}.csv` - Detailed cluster characteristic profiles
- `output/per_cluster_metrics_{matrix_type}.csv` - Quality metrics for each cluster
- `output/cluster_visualization_{matrix_type}.png` - 2D visualization of clusters
- `output/clustering_documentation_{matrix_type}.md` - Comprehensive clustering analysis
- `output/comprehensive_cluster_labels.csv` - Enhanced cluster descriptions

**Primary Consumers:** Steps 7-12 (Business Rules), Steps 13-15 (Consolidation and Visualization)

**Business Use:** Enables targeted optimization strategies by grouping similar stores for comparative analysis

## 6. Success Metrics & KPIs

- Silhouette score ≥ 0.5 for quality clustering
- Cluster size balance within configured constraints (50 stores per cluster)
- PCA variance retention ≥ 80% for dimensionality reduction
- Execution time ≤ 15 minutes for large datasets
- Zero data leakage between training and validation sets

## 7. Performance & Cost Notes

- Efficient PCA implementation for large feature spaces (1,000+ SPU features)
- Memory-optimized processing with batch operations
- Parallel computation for cluster balancing algorithms
- Handles up to 2,000+ stores with comprehensive product coverage
- Configurable cluster size constraints for practical groupings

## 8. Dependencies & Risks

**Upstream Data / Services:**
- Step 3 output files (normalized and original matrices)
- Step 5 output files (temperature data, optional)

**External Libraries / APIs:**
- scikit-learn, pandas, numpy, matplotlib

**Risk Mitigation:**
- Fallback to standard clustering when temperature data is unavailable
- Comprehensive error handling and logging
- Configurable cluster size constraints
- Quality metrics for clustering validation

## 9. Pipeline Integration

**Upstream Step(s):** Steps 3 (Prepare Matrices) and 5 (Calculate Feels-Like Temperature)

**Downstream Step(s):** Steps 7-12 (Business Rules), Steps 13-15 (Consolidation)

**Failure Impact:** Blocks all downstream business rules and optimization strategies; affects targeted recommendations

## 10. Future Improvements

- Integration with real-time sales data for dynamic clustering
- Enhanced clustering algorithms (hierarchical, DBSCAN, spectral)
- Geographic clustering constraints based on store proximity
- Temporal clustering for seasonal pattern analysis
- Ensemble clustering with multiple algorithm combinations
- Automated optimal cluster count determination
- Integration with demographic data for enriched clustering
