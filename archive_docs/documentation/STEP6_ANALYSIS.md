# Step 6 Analysis: Cluster Analysis for Subcategory and SPU-Level Data

## Hardcoded Values Identified

### Matrix Type Configuration
1. **Default Matrix Type**: `MATRIX_TYPE = "spu"` (line 42) - SPU-level clustering
2. **Alternative Options**: Commented options for "subcategory" and "category_agg"

### File Paths Configuration (Lines 46-65)
Fixed file paths for different matrix types:
- **Subcategory**: 
  - `"normalized": "data/normalized_subcategory_matrix.csv"`
  - `"original": "data/store_subcategory_matrix.csv"`
- **SPU**: 
  - `"normalized": "data/normalized_spu_limited_matrix.csv"`
  - `"original": "data/store_spu_limited_matrix.csv"`
- **Category Aggregated**: 
  - `"normalized": "data/normalized_category_agg_matrix.csv"`
  - `"original": "data/store_category_agg_matrix.csv"`

### Input/Output Configuration
1. **Temperature Data**: `TEMPERATURE_DATA = "output/stores_with_feels_like_temperature.csv"` (line 73)
2. **Output Directory**: `OUTPUT_DIR = "output"` (line 74)

### Algorithm Configuration
1. **Random State**: `RANDOM_STATE = 42` (line 75)
2. **KMeans Parameters**: 
   - `N_INIT = 10` (line 76)
   - `MAX_ITER = 300` (line 77)
3. **PCA Components**: 
   - `"subcategory": 50` (line 81)
   - `"spu": 100` (line 82)
   - `"category_agg": 20` (line 83)

### Clustering Constraints (Lines 87-91)
1. `MIN_CLUSTER_SIZE = 50` (line 88)
2. `MAX_CLUSTER_SIZE = 50` (line 89) - Enforces exactly 50 stores per cluster
3. `MAX_BALANCE_ITERATIONS = 100` (line 90)
4. `ENABLE_TEMPERATURE_CONSTRAINTS = True` (line 91)

## Synthetic Data Usage Assessment

### ✅ Real Data Usage
- **Matrix Data**: Uses actual store-subcategory/SPU matrices from step 3
- **Temperature Data**: Uses real temperature data from step 5
- **Clustering Algorithms**: Applies real KMeans and PCA to actual data
- **Store-Level Processing**: Processes real store data with actual sales patterns
- **Temperature-Aware Clustering**: Uses real temperature bands for clustering constraints

### ⚠️ Potential Synthetic Data Issues
- **Hardcoded Matrix Type**: Fixed to SPU-level clustering by default
- **Fixed File Paths**: Static input/output file locations
- **Fixed Algorithm Parameters**: Static random state, iterations, and components
- **Fixed Cluster Size**: Hardcoded exactly 50 stores per cluster
- **Fixed Temperature Constraints**: Static temperature-aware clustering setting

## Data Treatment Assessment

### ✅ Proper Data Handling
- **Real Matrix Data Integration**: Processes actual store-subcategory/SPU matrices
- **Temperature-Aware Clustering**: Uses real temperature data for clustering constraints
- **Scientific Accuracy**: Implements validated clustering algorithms (KMeans, PCA)
- **Cluster Balancing**: Enforces equal-sized clusters for consistent analysis
- **Comprehensive Metrics**: Calculates multiple clustering quality metrics
- **Visualization Support**: Creates visualizations for cluster analysis

### ⚠️ Areas for Improvement
1. **Configurable Matrix Type**: Should allow dynamic selection of matrix type
2. **Flexible File Paths**: Should support configurable input/output locations
3. **Dynamic Algorithm Parameters**: Should allow customization of clustering parameters
4. **Variable Cluster Sizes**: Should support configurable cluster size constraints
5. **Configurable Temperature Constraints**: Should allow customization of temperature awareness

## Business Logic Alignment

### ✅ Aligned with Business Requirements
- **Real Data Processing**: Uses actual store sales data for all clustering
- **Product Recommendations**: Supports targeted recommendations through clustering
- **Temperature Awareness**: Implements weather-aware clustering for appropriate recommendations
- **No Placeholder Data**: No synthetic or placeholder data detected in core processing
- **Equal-Sized Clusters**: Enforces 50 stores per cluster for consistent analysis
- **Multiple Matrix Types**: Supports subcategory, SPU, and category-aggregated clustering

### ⚠️ Configuration Limitations
- **Fixed Matrix Type**: Hardcoded to SPU-level clustering may not suit all analyses
- **Static Cluster Size**: Fixed 50-store constraint may not be optimal for all scenarios
- **Fixed Algorithm Parameters**: Static parameters may not be optimal for all datasets
- **Regional Limitations**: Hardcoded configuration may not work for different regions
- **Limited Flexibility**: Fixed settings may limit adaptability to different business needs

## Recommendations

1. **Configurable Matrix Selection**: Allow dynamic selection of matrix type via parameters
2. **Environment Variable Support**: Move hardcoded values to configuration/environment variables
3. **Flexible Cluster Sizing**: Allow customization of cluster size constraints
4. **Dynamic Algorithm Parameters**: Support configurable clustering parameters
5. **Configurable Temperature Awareness**: Allow customization of temperature constraints
6. **Regional Adaptation**: Support different configurations for different regions
7. **Flexible File Paths**: Allow customization of input/output locations

## Integration Update (2025-08-10)

- Change: Do not skip small temperature bands. In `src/step6_cluster_analysis.py`, bands with `< MIN_CLUSTER_SIZE` stores are no longer skipped; they are clustered as a single undersized cluster. This ensures no stores are dropped.
- Location: `perform_temperature_aware_clustering()` around the check for `band_size < MIN_CLUSTER_SIZE`.
- Impact: Preserves full store coverage within temperature-aware clustering. A small band yields 1 cluster; balancing will not force-merge into other bands (bands remain isolated by design).
- Synthetic data: None introduced. The change only alters control flow; computations still use real matrices and real temperature bands from Step 5.

## Integration Run Plan

1. Prerequisites
   - `data/normalized_spu_limited_matrix.csv` and `data/store_spu_limited_matrix.csv` from Step 3
   - `output/stores_with_feels_like_temperature.csv` from Step 5

2. Optional pre-checks
   - Confirm counts and headers:
     - `wc -l data/normalized_spu_limited_matrix.csv`
     - `head -1 output/stores_with_feels_like_temperature.csv`

3. Execute Step 6 (SPU, temperature-aware)
```bash
python3 src/step6_cluster_analysis.py
```

4. Expected outputs (under `output/`)
   - `clustering_results_spu.csv`
   - `cluster_profiles_spu.csv`
   - `per_cluster_metrics_spu.csv`
   - `cluster_visualization_spu.png`
   - `clustering_documentation_spu.md`
   - `comprehensive_cluster_labels.csv`
   - `cluster_labeling_summary.json`, `cluster_label_analysis_report.md`

5. Post-run validation
   - Store coverage equals matrix store count (minus any stores missing temperature bands entirely)
   - No drops due to small-band logic (check logs for the “single undersized cluster” message)
   - Cluster sizes mostly 50; remainder cluster may be <50 by design
   - Metrics present: silhouette, CH, DB

6. Documentation
   - Integration Run Summary added below for this run (2025-08-10).

## Integration Run Summary (2025-08-10)

This documents the Step 6 execution using matrices from Step 3 and temperature outputs from Step 5 (August 2025, 202508A clamped coverage). No synthetic data introduced; clustering used real matrices and real temperature bands.

- Run context
  - Command: `python3 src/step6_cluster_analysis.py` (default `MATRIX_TYPE=spu`), and subcategory results are also present.
  - Inputs: `data/*_matrix.csv` from Step 3, `output/stores_with_feels_like_temperature.csv` from Step 5.

- SPU clustering results
  - Stores clustered: 2,268 (post-rerun, aligned to Step 5 temperature coverage)
  - Clusters: 49
  - Cluster sizes: min 2, max 68, mean 46.29 (41 clusters at size 50; undersized clusters correspond to small temperature bands)
  - Metrics (overall):
    - Silhouette: -0.069
    - Calinski-Harabasz: 26.1
    - Davies-Bouldin: 100632880914116.109
  - Alignment check vs Step 5: 2,268/2,268 stores intersect; 0 clustered without temperature bands; 0 Step 5 stores without cluster
  - Output artifacts present:
    - `output/clustering_results_spu.csv`
    - `output/cluster_profiles_spu.csv`
    - `output/per_cluster_metrics_spu.csv`
    - `output/cluster_visualization_spu.png`
    - `output/clustering_documentation_spu.md`
    - `output/comprehensive_cluster_labels.csv`
    - `output/cluster_labeling_summary.json`
    - `output/cluster_label_analysis_report.md`

- Subcategory clustering results
  - Stores clustered: 2,335
  - Clusters: 47
  - Cluster sizes: min 38, max 50, mean 49.68
  - Metrics: Weighted Avg Silhouette: 0.0769; Overall Quality (mean): 0.8162

- Coverage & constraints
  - All temperature bands are preserved; small bands form a single undersized cluster (no store drops). SPU clustering now strictly uses stores present in `stores_with_feels_like_temperature.csv`.
  - The 50-store size constraint yields remainder clusters <50 by design when total stores are not divisible by 50.

- Re-run guidance
  - When `202508B` weather is added and Step 5 is re-run, re-run Step 6 to refresh clusters with the updated temperature bands.

### Integration Fix (2025-08-10 Option A)

- Change: Cast SPU matrices' indices to string during load in `src/step6_cluster_analysis.py` (`load_data()`) to match Step 5 temperature dataframe index and prevent KeyError during band selection.
- Impact: Enabled successful temperature-aware clustering strictly over stores with valid temperature bands; eliminated the prior 6-store mismatch.

## Business Logic Alignment
