# Pipeline Data Flow Analysis Report

**Generated:** 2025-06-21 17:43:07

## Executive Summary

This report analyzes the data flow between all 15 pipeline steps to ensure proper file handoffs.

### Issues Summary
- **Steps with issues:** 0
- **Total issues:** 0

## Detailed Analysis


### Step 1: Download API Data
**Script:** `src/step1_download_api_data.py`

**Required Inputs:**
- ✅ `data/store_codes.csv` - Exists (0.0 MB)

**Outputs:**
- ✅ `data/api_data/store_config_202506A.csv` - Exists (36.7 MB)
- ✅ `data/api_data/store_sales_202506A.csv` - Exists (0.4 MB)
- ✅ `data/api_data/complete_category_sales_202506A.csv` - Exists (11.4 MB)
- ✅ `data/api_data/complete_spu_sales_202506A.csv` - Exists (26.2 MB)

**Status:** ✅ No issues detected


### Step 2: Extract Coordinates
**Script:** `src/step2_extract_coordinates.py`

**Dependencies:** step1

**Required Inputs:**
- ✅ `data/api_data/complete_category_sales_202506A.csv` - Exists (11.4 MB)
- ✅ `data/api_data/complete_spu_sales_202506A.csv` - Exists (26.2 MB)
- ✅ `data/api_data/store_sales_202506A.csv` - Exists (0.4 MB)

**Outputs:**
- ✅ `data/store_coordinates_extended.csv` - Exists (0.1 MB)
- ✅ `data/spu_store_mapping.csv` - Exists (26.2 MB)
- ✅ `data/spu_metadata.csv` - Exists (0.3 MB)

**Status:** ✅ No issues detected


### Step 3: Prepare Matrix
**Script:** `src/step3_prepare_matrix.py`

**Dependencies:** step1, step2

**Required Inputs:**
- ✅ `data/api_data/complete_category_sales_202506A.csv` - Exists (11.4 MB)
- ✅ `data/api_data/complete_spu_sales_202506A.csv` - Exists (26.2 MB)
- ✅ `data/store_coordinates_extended.csv` - Exists (0.1 MB)

**Outputs:**
- ✅ `data/store_subcategory_matrix.csv` - Exists (1.4 MB)
- ✅ `data/normalized_subcategory_matrix.csv` - Exists (2.6 MB)
- ✅ `data/store_spu_limited_matrix.csv` - Exists (9.5 MB)
- ✅ `data/normalized_spu_limited_matrix.csv` - Exists (15.9 MB)
- ✅ `data/store_category_agg_matrix.csv` - Exists (0.3 MB)
- ✅ `data/normalized_category_agg_matrix.csv` - Exists (0.7 MB)
- ✅ `data/subcategory_store_list.txt` - Exists (0.0 MB)
- ✅ `data/spu_limited_store_list.txt` - Exists (0.0 MB)
- ✅ `data/category_agg_store_list.txt` - Exists (0.0 MB)
- ✅ `data/store_list.txt` - Exists (0.0 MB)
- ✅ `data/subcategory_list.txt` - Exists (0.0 MB)
- ✅ `data/category_list.txt` - Exists (0.0 MB)

**Status:** ✅ No issues detected


### Step 4: Download Weather Data
**Script:** `src/step4_download_weather_data.py`

**Dependencies:** step2

**Required Inputs:**
- ✅ `data/store_coordinates_extended.csv` - Exists (0.1 MB)

**Outputs:**
- ✅ `output/weather_data/weather_data_*.csv` - Found 2293 files matching pattern
- ✅ `output/store_altitudes.csv` - Exists (0.0 MB)

**Status:** ✅ No issues detected


### Step 5: Calculate Feels Like Temperature
**Script:** `src/step5_calculate_feels_like_temperature.py`

**Dependencies:** step4

**Required Inputs:**
- ✅ `output/weather_data/weather_data_*.csv` - Found 2293 files matching pattern
- ✅ `output/store_altitudes.csv` - Exists (0.0 MB)

**Outputs:**
- ✅ `output/stores_with_feels_like_temperature.csv` - Exists (0.4 MB)
- ✅ `output/temperature_bands.csv` - Exists (0.0 MB)

**Status:** ✅ No issues detected


### Step 6: Cluster Analysis
**Script:** `src/step6_cluster_analysis.py`

**Dependencies:** step3

**Required Inputs:**
- ✅ `data/normalized_subcategory_matrix.csv` - Exists (2.6 MB)
- ✅ `data/store_subcategory_matrix.csv` - Exists (1.4 MB)

**Optional Inputs:**
- ✅ `data/normalized_spu_limited_matrix.csv` - Exists (15.9 MB)
- ✅ `data/store_spu_limited_matrix.csv` - Exists (9.5 MB)
- ✅ `data/normalized_category_agg_matrix.csv` - Exists (0.7 MB)
- ✅ `data/store_category_agg_matrix.csv` - Exists (0.3 MB)
- ✅ `output/stores_with_feels_like_temperature.csv` - Exists (0.4 MB)

**Outputs:**
- ✅ `output/clustering_results.csv` - Exists (0.0 MB)
- ✅ `output/clustering_results_subcategory.csv` - Exists (0.0 MB)
- ✅ `output/clustering_results_spu.csv` - Exists (0.0 MB)
- ✅ `output/clustering_results_category_agg.csv` - Exists (0.0 MB)
- ✅ `output/cluster_profiles_*.csv` - Found 3 files matching pattern
- ✅ `output/per_cluster_metrics_*.csv` - Found 3 files matching pattern
- ✅ `output/cluster_visualization_*.png` - Found 3 files matching pattern

**Status:** ✅ No issues detected


### Step 7: Missing Category Rule
**Script:** `src/step7_missing_category_rule.py`

**Dependencies:** step6, step1

**Required Inputs:**
- ✅ `output/clustering_results_spu.csv` - Exists (0.0 MB)
- ✅ `data/api_data/complete_spu_sales_202506A.csv` - Exists (26.2 MB)

**Outputs:**
- ✅ `output/rule7_missing_spu_results.csv` - Exists (0.3 MB)
- ✅ `output/rule7_missing_spu_opportunities.csv` - Exists (0.2 MB)
- ✅ `output/rule7_missing_spu_summary.md` - Exists (0.0 MB)

**Status:** ✅ No issues detected


### Step 8: Imbalanced Rule
**Script:** `src/step8_imbalanced_rule.py`

**Dependencies:** step6, step1

**Required Inputs:**
- ✅ `output/clustering_results_spu.csv` - Exists (0.0 MB)
- ✅ `data/api_data/store_config_202506A.csv` - Exists (36.7 MB)

**Outputs:**
- ✅ `output/rule8_imbalanced_spu_results.csv` - Exists (0.3 MB)
- ✅ `output/rule8_imbalanced_spu_cases.csv` - Exists (0.1 MB)
- ✅ `output/rule8_imbalanced_spu_summary.md` - Exists (0.0 MB)

**Status:** ✅ No issues detected


### Step 9: Below Minimum Rule
**Script:** `src/step9_below_minimum_rule.py`

**Dependencies:** step6, step1

**Required Inputs:**
- ✅ `output/clustering_results_spu.csv` - Exists (0.0 MB)
- ✅ `data/api_data/store_config_202506A.csv` - Exists (36.7 MB)

**Outputs:**
- ✅ `output/rule9_below_minimum_spu_results.csv` - Exists (0.3 MB)
- ✅ `output/rule9_below_minimum_spu_cases.csv` - Exists (12.1 MB)
- ✅ `output/rule9_below_minimum_spu_summary.md` - Exists (0.0 MB)

**Status:** ✅ No issues detected


### Step 10: SPU Assortment Optimization
**Script:** `src/step10_spu_assortment_optimization.py`

**Dependencies:** step6, step1

**Required Inputs:**
- ✅ `output/clustering_results.csv` - Exists (0.0 MB)
- ✅ `data/api_data/store_config_202506A.csv` - Exists (36.7 MB)

**Outputs:**
- ✅ `output/rule10_spu_overcapacity_results.csv` - Exists (0.4 MB)
- ✅ `output/rule10_spu_overcapacity_opportunities.csv` - Exists (40.4 MB)

**Status:** ✅ No issues detected


### Step 11: Improved Category Logic
**Script:** `src/step11_improved_category_logic.py`

**Dependencies:** step6, step1

**Required Inputs:**
- ✅ `output/clustering_results_spu.csv` - Exists (0.0 MB)
- ✅ `data/api_data/complete_spu_sales_202506A.csv` - Exists (26.2 MB)
- ✅ `data/api_data/store_sales_data.csv` - Exists (0.4 MB)

**Outputs:**
- ✅ `output/rule11_improved_missed_sales_opportunity_spu_results.csv` - Exists (0.2 MB)
- ✅ `output/rule11_improved_missed_sales_opportunity_spu_details.csv` - Exists (82.4 MB)
- ✅ `output/rule11_improved_top_performers_by_cluster_category.csv` - Exists (1.5 MB)
- ✅ `output/rule11_improved_missed_sales_opportunity_spu_summary.md` - Exists (0.0 MB)

**Status:** ✅ No issues detected


### Step 12: Sales Performance Rule
**Script:** `src/step12_sales_performance_rule.py`

**Dependencies:** step6, step1

**Required Inputs:**
- ✅ `output/clustering_results.csv` - Exists (0.0 MB)
- ✅ `data/api_data/complete_category_sales_202506A.csv` - Exists (11.4 MB)

**Outputs:**
- ✅ `output/rule12_sales_performance_results.csv` - Exists (0.4 MB)
- ✅ `output/rule12_sales_performance_details.csv` - Exists (70.3 MB)
- ✅ `output/rule12_sales_performance_summary.md` - Exists (0.0 MB)

**Status:** ✅ No issues detected


### Step 13: Consolidate SPU Rules
**Script:** `src/step13_consolidate_spu_rules.py`

**Dependencies:** step6, step7, step8, step9, step10, step11, step12

**Required Inputs:**
- ✅ `output/clustering_results.csv` - Exists (0.0 MB)
- ✅ `output/rule7_missing_spu_results.csv` - Exists (0.3 MB)
- ✅ `output/rule8_imbalanced_spu_results.csv` - Exists (0.3 MB)
- ✅ `output/rule9_below_minimum_spu_results.csv` - Exists (0.3 MB)
- ✅ `output/rule10_spu_overcapacity_results.csv` - Exists (0.4 MB)
- ✅ `output/rule11_improved_missed_sales_opportunity_spu_results.csv` - Exists (0.2 MB)
- ✅ `output/rule12_sales_performance_spu_results.csv` - Exists (0.4 MB)

**Outputs:**
- ✅ `output/consolidated_spu_rule_results.csv` - Exists (1.1 MB)
- ✅ `output/consolidated_spu_rule_summary.md` - Exists (0.0 MB)

**Status:** ✅ No issues detected


### Step 14: Global Overview Dashboard
**Script:** `src/step14_global_overview_dashboard.py`

**Dependencies:** step13

**Required Inputs:**
- ✅ `output/consolidated_spu_rule_results.csv` - Exists (1.1 MB)

**Outputs:**
- ✅ `output/global_overview_spu_dashboard.html` - Exists (0.0 MB)

**Status:** ✅ No issues detected


### Step 15: Interactive Map Dashboard
**Script:** `src/step15_interactive_map_dashboard.py`

**Dependencies:** step13, step2, step7, step9, step11, step12

**Required Inputs:**
- ✅ `output/consolidated_spu_rule_results.csv` - Exists (1.1 MB)
- ✅ `data/store_coordinates_extended.csv` - Exists (0.1 MB)
- ✅ `output/rule7_missing_spu_opportunities.csv` - Exists (0.2 MB)
- ✅ `output/rule9_below_minimum_spu_cases.csv` - Exists (12.1 MB)
- ✅ `output/rule11_improved_missed_sales_opportunity_spu_results.csv` - Exists (0.2 MB)
- ✅ `output/rule12_sales_performance_results.csv` - Exists (0.4 MB)

**Outputs:**
- ✅ `output/interactive_map_spu_dashboard.html` - Exists (426.8 MB)

**Status:** ✅ No issues detected


## Recommendations

### Critical Issues to Fix:
1. **Missing Required Inputs**: These will cause pipeline steps to fail
2. **Missing Outputs**: Previous steps may not have run successfully

### File Naming Consistency:
- Some steps use different naming conventions (e.g., `202505` vs `202506A`)
- Consider standardizing period labels across all steps

### Dependency Management:
- Run steps in the correct order based on dependencies
- Consider creating a master pipeline script to orchestrate execution

## Next Steps

1. **Fix Critical Issues**: Address all missing required inputs first
2. **Run Missing Steps**: Execute steps that haven't produced their expected outputs
3. **Validate Outputs**: Ensure all output files contain expected data
4. **Test End-to-End**: Run the complete pipeline to verify data flow

