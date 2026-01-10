# API Documentation

## Pipeline Steps API Reference

This document provides detailed API documentation for each pipeline step module.

### Step 1: Data Download (`step1_download_api_data.py`)

Downloads raw sales data from API endpoints.

#### Functions:
- `download_data()` - Main entry point for data download
- `process_api_response(response)` - Processes API response data
- `save_raw_data(data, filename)` - Saves data to file

#### Parameters:
- API endpoint configuration
- Authentication credentials
- Data format specifications

### Step 2: Coordinate Extraction (`step2_extract_coordinates.py`)

Extracts store geographic coordinates for mapping.

#### Functions:
- `extract_coordinates()` - Main coordinate extraction
- `geocode_store(store_data)` - Geocodes individual store
- `validate_coordinates(lat, lon)` - Validates coordinate data

### Step 3: Matrix Preparation (`step3_prepare_matrix.py`)

Creates normalized store-product matrices for analysis.

#### Functions:
- `prepare_matrix()` - Main matrix preparation
- `normalize_data(matrix)` - Applies normalization
- `handle_missing_values(matrix)` - Handles missing data

### Step 4: Cluster Analysis (`step4_cluster_analysis.py`)

Performs K-means clustering with PCA dimensionality reduction.

#### Functions:
- `perform_clustering()` - Main clustering analysis
- `determine_optimal_clusters(data)` - Finds optimal cluster count
- `apply_pca(data, n_components)` - Applies PCA transformation

### Step 5: Missing Category Rule (`step5_missing_category_rule.py`)

Identifies missing product category opportunities.

#### Functions:
- `apply_missing_category_rule()` - Main rule application
- `calculate_cluster_averages(data, clusters)` - Calculates averages
- `identify_missing_opportunities(store, cluster_data)` - Finds opportunities

### Step 6: Imbalanced Rule (`step6_imbalanced_rule.py`)

Detects allocation imbalances using Z-score analysis.

#### Functions:
- `apply_imbalanced_rule()` - Main rule application
- `calculate_z_scores(data)` - Calculates Z-scores
- `flag_imbalanced_allocations(z_scores, threshold)` - Flags imbalances

### Step 7: Below Minimum Rule (`step7_below_minimum_rule.py`)

Flags allocations below minimum thresholds.

#### Functions:
- `apply_below_minimum_rule()` - Main rule application
- `check_minimum_thresholds(data, threshold)` - Checks thresholds
- `calculate_required_increases(data)` - Calculates increases needed

### Step 8: Smart Overcapacity Rule (`step8_smart_overcapacity_rule.py`)

Finds reallocation opportunities based on performance gaps.

#### Functions:
- `apply_smart_overcapacity_rule()` - Main rule application
- `identify_reallocation_opportunities(data)` - Finds opportunities
- `calculate_performance_gaps(local, cluster)` - Calculates gaps

### Step 9: Rule Consolidation (`step9_consolidate_rules.py`)

Consolidates all rule results into unified output.

#### Functions:
- `consolidate_rules()` - Main consolidation
- `merge_rule_results(rule_data_list)` - Merges results
- `generate_summary_statistics(consolidated_data)` - Generates summaries

### Step 10: Global Dashboard (`step10_global_overview_dashboard.py`)

Creates executive-level overview dashboard.

#### Functions:
- `create_global_dashboard()` - Main dashboard creation
- `generate_kpi_cards(data)` - Creates KPI visualizations
- `create_interactive_charts(data)` - Creates interactive charts

### Step 11: Interactive Map (`step11_interactive_map_dashboard.py`)

Generates geographic visualization with interactive features.

#### Functions:
- `create_interactive_map()` - Main map creation
- `add_store_markers(map_obj, store_data)` - Adds store markers
- `create_popup_content(store)` - Creates popup content

## Data Formats

### Input Data Structure
```python
{
    'store_id': str,
    'category': str,
    'allocated_styles': float,
    'sales_performance': float,
    'cluster_id': int
}
```

### Output Data Structure
```python
{
    'store_id': str,
    'total_violations': int,
    'rule5_missing_category': int,
    'rule6_imbalanced': int,
    'rule7_below_minimum': int,
    'rule8_smart_overcapacity': int,
    'cluster_id': int
}
```

## Error Handling

All modules implement comprehensive error handling:
- Input validation
- Graceful failure recovery
- Detailed error logging
- Rollback mechanisms

## Performance Considerations

- Memory optimization for large datasets
- Progress tracking with tqdm
- Configurable batch processing
- Caching mechanisms for repeated operations
