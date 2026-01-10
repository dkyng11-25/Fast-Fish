# Data Source Report (2025-09-18)

This report details the data sources used by the validation runners for each step (1-37) of the pipeline. The analysis aims to identify whether tests utilize dummy/synthetic data or real data from the `data/` and `output/` directories, specifically for the 202508A and 202508B data scenarios. Special attention was given to Step 1 and Step 4, which have data schemas based on real data.

## Summary

*   **Steps using Dummy/Synthetic Data:**
    *   Step 19
*   **Steps using Real Data (or derived from real data):**
    *   Steps 1-18 (excluding 19), and 20-37

## Detailed Breakdown by Step

### Step 1: API Data Download Validation
*   **Data Source:** Real Data
*   **Details:** Loads `store_config_{period}.csv`, `complete_category_sales_{period}.csv`, and `complete_spu_sales_{period}.csv` from `data/api_data/`. These files are expected to contain real time-series data. Validation schemas (`StoreConfigSchema`, `CategorySalesSchema`, `SPUSalesSchema`) are based on real data structures.

### Step 2: Coordinate Extraction Validation
*   **Data Source:** Real Data (static input files)
*   **Details:** Validates `store_coordinates_extended.csv`, `spu_store_mapping.csv`, and `spu_metadata.csv` from the `data/` directory.

### Step 2B: Seasonal Data Consolidation Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `seasonal_store_profiles_*.csv`, `seasonal_category_patterns_*.csv`, and `seasonal_clustering_features_*.csv` from the `output/` directory, which are outputs of previous processing steps.

### Step 3: Matrix Preparation Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `subcategory_matrix.csv`, `spu_matrix.csv`, and `category_aggregated_matrix.csv` from the `output/` directory.

### Step 4: Weather Data Validation
*   **Data Source:** Real Data
*   **Details:** Validates weather data files (`weather_data_*.csv`) from `output/weather_data/` and `store_altitudes.csv` from `output/`. These are expected to be real weather and altitude data. Validation uses `WeatherDataSchema` and `StoreAltitudeSchema`.

### Step 5: Feels-Like Temperature Calculation Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `stores_with_feels_like_temperature.csv`, `temperature_bands.csv`, and `temperature_bands_seasonal.csv` from the `output/` directory, derived from real weather data.

### Step 6: Cluster Analysis Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `clustering_results_spu.csv`, `cluster_profiles_spu.csv`, and `per_cluster_metrics_spu.csv` from the `output/` directory.

### Step 7: Missing Category/SPU Rule Validation
*   **Data Source:** Real Data (pipeline input/output)
*   **Details:** Validates various `rule7_missing_spu_sellthrough_*` and `rule7_missing_subcategory_sellthrough_*` files from `output/`, and input files like `complete_spu_sales_{period}.csv` and `complete_category_sales_{period}.csv` from `data/api_data/`.

### Step 8: Imbalanced Allocation Rule Validation
*   **Data Source:** Real Data (pipeline input/output)
*   **Details:** Validates `rule8_imbalanced_*_results.csv`, `rule8_imbalanced_*_cases.csv`, `rule8_imbalanced_*_z_score_analysis.csv` from `output/`, and input from `clustering_results_spu.csv`, `store_config_{period}.csv`, `complete_spu_sales_{period}.csv` from `data/`.

### Step 9: Below Minimum Rule Validation
*   **Data Source:** Real Data (pipeline input/output)
*   **Details:** Validates `rule9_below_minimum_spu_sellthrough_results_{period}.csv`, `rule9_below_minimum_spu_sellthrough_opportunities_{period}.csv` from `output/`, and inputs like `clustering_results_spu.csv`, `store_config_{period}.csv`, `complete_spu_sales_{period}.csv` from `data/`.

### Step 10: Smart Overcapacity (SPU) Validation
*   **Data Source:** Real Data (pipeline input/output)
*   **Details:** Validates `rule10_smart_overcapacity_results_{period}.csv`, `rule10_spu_overcapacity_opportunities_{period}.csv` from `output/`, and inputs like `store_config_{period}.csv`, `complete_spu_sales_{period}.csv`, `clustering_results_spu.csv` from `data/api_data/` and `output/`.

### Step 11: Missed Sales Opportunity (SPU) Validation
*   **Data Source:** Real Data (pipeline input/output)
*   **Details:** Validates `rule11_improved_missed_sales_opportunity_spu_results_{period}.csv`, `rule11_improved_missed_sales_opportunity_spu_details_{period}.csv`, `rule11_improved_top_performers_by_cluster_category_{period}.csv` from `output/`, and inputs like `clustering_results_spu.csv`, `complete_spu_sales_{period}.csv` from `data/`.

### Step 12: Sales Performance (Subcategory/SPU) Validation
*   **Data Source:** Real Data (pipeline input/output)
*   **Details:** Validates `rule12_sales_performance_spu_results_{period}.csv`, `rule12_sales_performance_spu_details_{period}.csv` from `output/`, and inputs like `clustering_results_spu.csv`, `store_config_{period}.csv`, `complete_spu_sales_{period}.csv` from `data/`.

### Step 13: Consolidate SPU Rule Results Validation
*   **Data Source:** Real Data (pipeline input/output)
*   **Details:** Explicitly states it "Preserves real data, avoiding synthesis." Validates various rule output files from Steps 7-12 and `clustering_results_spu.csv` from `output/`. Generates outputs like `consolidated_spu_rule_results_detailed_{period}.csv` in `output/`.

### Step 14: Enhanced Fast Fish Format Validation
*   **Data Source:** Real Data (pipeline output and cross-referenced with Step 13 real data)
*   **Details:** Validates `enhanced_fast_fish_format_{period}.csv`, `enhanced_fast_fish_validation_{period}.json` from `output/`. Performs cross-validation with `consolidated_spu_rule_results_detailed.csv` from Step 13.

### Step 15: Historical Baseline Download Validation
*   **Data Source:** Real Data (downloaded historical data)
*   **Details:** Validates `historical_baseline_{period}.csv`, `baseline_summary_{period}.csv` from `output/`, indicating actual historical data download.

### Step 16: Comparison Tables Creation Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `comparison_tables_{period}.csv`, `summary_comparison_{period}.csv`, `detailed_comparison_{period}.csv` from `output/`, which are outputs based on real data.

### Step 17: Recommendations Augmentation Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `augmented_recommendations_{period}.csv`, `recommendation_summary_{period}.csv` from `output/`, also derived from real data.

### Step 18: Results Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `validate_results_{period}.csv`, `validate_results_summary_{period}.csv` from `output/`, which process and validate real pipeline results.

### Step 19: Detailed SPU Breakdown Runner
*   **Data Source:** **DUMMY/SYNTHETIC DATA**
*   **Details:** This runner explicitly generates mock data using `_generate_mock_fast_fish_data()`, `_generate_mock_store_config()`, and `_generate_mock_clustering_results()`. These mock dataframes are saved to `tests/data/`.

### Step 20: Data Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `data_validation_{period}.csv`, `data_validation_summary_{period}.csv` from `output/`, processing real data.

### Step 21: Label Tag Recommendations Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `label_tag_recommendations_{period}.csv`, `label_tag_recommendations_summary_{period}.csv` from `output/`, derived from real data.

### Step 22: Store Attribute Enrichment Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `store_attribute_enrichment_{period}.csv`, `store_attribute_enrichment_summary_{period}.csv` from `output/`, derived from real data.

### Step 23: Clustering Features Update Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `update_clustering_features_{period}.csv`, `update_clustering_features_summary_{period}.csv` from `output/`, derived from real data.

### Step 24: Comprehensive Cluster Labeling Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `comprehensive_cluster_labeling_{period}.csv`, `comprehensive_cluster_labeling_summary_{period}.csv` from `output/`, derived from real data.

### Step 25: Product Role Classification Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `product_role_classifier_{period}.csv`, `product_role_classifier_summary_{period}.csv` from `output/`, derived from real data.

### Step 26: Price Elasticity Analysis Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `price_elasticity_analyzer_{period}.csv`, `price_elasticity_analyzer_summary_{period}.csv` from `output/`, derived from real data.

### Step 27: Gap Matrix Generation Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `gap_matrix_generator_{period}.csv`, `gap_matrix_generator_summary_{period}.csv` from `output/`, derived from real data.

### Step 28: Scenario Analysis Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `scenario_analyzer_{period}.csv`, `scenario_analyzer_summary_{period}.csv` from `output/`, derived from real data.

### Step 29: Supply Demand Gap Analysis Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `supply_demand_gap_analysis_{period}.csv`, `supply_demand_gap_analysis_summary_{period}.csv` from `output/`, derived from real data.

### Step 30: Sellthrough Optimization Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `sellthrough_optimization_engine_{period}.csv`, `sellthrough_optimization_engine_summary_{period}.csv` from `output/`, derived from real data.

### Step 31: Gap Analysis Workbook Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `gap_analysis_workbook_{period}.csv`, `gap_analysis_workbook_summary_{period}.csv` from `output/`, derived from real data.

### Step 32: Store Allocation Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `store_allocation_{period}.csv`, `store_allocation_summary_{period}.csv` from `output/`, derived from real data.

### Step 33: Store Level Merchandising Rules Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `store_level_merchandising_rules_{period}.csv`, `store_level_merchandising_rules_summary_{period}.csv` from `output/`, derived from real data.

### Step 34: Cluster Strategy Optimization Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `cluster_strategy_optimization_{period}.csv`, `cluster_strategy_optimization_summary_{period}.csv` from `output/`, derived from real data.

### Step 35: Merchandising Strategy Deployment Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `merchandising_strategy_deployment_{period}.csv`, `merchandising_strategy_deployment_summary_{period}.csv` from `output/`, derived from real data.

### Step 36: Unified Delivery Building Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `unified_delivery_builder_{period}.csv`, `unified_delivery_builder_summary_{period}.csv` from `output/`, derived from real data.

### Step 37: Customer Delivery Formatting Validation
*   **Data Source:** Real Data (pipeline output)
*   **Details:** Validates `customer_delivery_formatter_{period}.csv`, `customer_delivery_formatter_summary_{period}.csv` from `output/`, derived from real data.


