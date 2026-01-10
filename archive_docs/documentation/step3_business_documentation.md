# Step 3: Prepare Store-Product Matrices for Clustering

## 1. Identification

**Name / Path:** `/src/step3_prepare_matrix.py`

**Component:** Data Preparation

**Owner:** Data Engineering Team

**Last Updated:** 2025-07-21

## 2. Purpose & Business Value

Creates normalized store-product matrices for both subcategory-level and SPU-level clustering analysis using comprehensive year-over-year data aggregation. This step transforms raw sales data into mathematical representations suitable for machine learning algorithms, enabling accurate store grouping based on product mix patterns. The system aggregates data from 12 periods (current and historical) to create robust matrices that capture comprehensive store-product relationships across seasonal variations.

## 3. Inputs

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| Subcategory Sales Data | CSV Files | Sales data by subcategory from multiple periods | Output of Step 1 (API data) |
| SPU Sales Data | CSV Files | SPU-level sales data from multiple periods | Output of Step 1 (API data) |
| Store Coordinates | CSV File | Geographic coordinates for all stores | Output of Step 2 |
| Store Codes | List[str] | Unique identifiers for all retail stores | `data/store_codes.csv` |

## 4. Transformation Overview

The script performs comprehensive matrix preparation with the following key processes:

1. **Multi-Period Aggregation**: Combines sales data from 12 periods (6 current + 6 historical) to create robust product matrices
2. **Data Filtering**: Removes anomalous stores and applies minimum prevalence thresholds for products and stores
3. **Matrix Creation**: Generates store-by-product matrices for both subcategory and SPU levels
4. **Normalization**: Applies row-wise normalization to create comparable product mix profiles
5. **Memory Management**: Implements SPU matrix size limiting for computational efficiency
6. **Category Aggregation**: Creates category-level matrices from SPU data for hierarchical analysis

## 5. Outputs & Consumers

**Format / Schema:** CSV files and text files with the following outputs:
- `data/store_subcategory_matrix.csv` - Original store-by-subcategory sales matrix
- `data/normalized_subcategory_matrix.csv` - Normalized store-by-subcategory matrix for clustering
- `data/store_spu_limited_matrix.csv` - Original store-by-SPU sales matrix (size-limited)
- `data/normalized_spu_limited_matrix.csv` - Normalized store-by-SPU matrix for clustering
- `data/store_category_agg_matrix.csv` - Category-aggregated matrix from SPU data
- `data/normalized_category_agg_matrix.csv` - Normalized category-aggregated matrix
- Various list files (store lists, product lists, etc.)

**Primary Consumers:** Step 6 (Clustering Analysis), Business Rule Steps

**Business Use:** Provides mathematical representations of store product mixes for machine learning-based clustering and optimization

## 6. Success Metrics & KPIs

- Matrix completeness ≥ 95% of filtered stores
- Normalization accuracy with proper row-wise sum = 1.0
- Memory efficiency with SPU matrix size management
- Execution time ≤ 10 minutes for large datasets
- Zero data leakage between training and validation periods

## 7. Performance & Cost Notes

- Processes multi-period data efficiently with optimized pandas operations
- Implements memory management for large SPU matrices
- Uses chunked processing for large datasets
- Supports up to 1,000 SPU features for computational efficiency
- Handles 2,000+ stores with comprehensive product coverage

## 8. Dependencies & Risks

**Upstream Data / Services:**
- Step 1 output files (category sales, SPU sales)
- Step 2 output files (store coordinates)

**External Libraries / APIs:**
- pandas, numpy, tqdm

**Risk Mitigation:**
- Fallback to single-period data when multi-period data is unavailable
- Anomaly detection and filtering for data quality
- Memory management for large SPU matrices
- Comprehensive error handling and logging

## 9. Pipeline Integration

**Upstream Step(s):** Steps 1 (Download API Data) and 2 (Extract Coordinates)

**Downstream Step(s):** Step 6 (Cluster Analysis)

**Failure Impact:** Blocks clustering analysis and downstream optimization; affects both subcategory and SPU-level recommendations

## 10. Future Improvements

- Implement dynamic SPU matrix size optimization based on available memory
- Add support for temporal weighting in multi-period aggregation
- Enhance anomaly detection with statistical outlier identification
- Implement incremental matrix updates for real-time analysis
- Add support for custom product hierarchies
- Integration with external demographic data for enriched matrices
- Enhanced normalization techniques (TF-IDF, log normalization)
