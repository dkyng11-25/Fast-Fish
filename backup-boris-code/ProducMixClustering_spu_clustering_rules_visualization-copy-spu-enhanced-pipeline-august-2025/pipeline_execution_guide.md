# Pipeline Execution Order Guide

**Generated:** 2025-06-21 17:43:07

## Recommended Execution Order

Run the pipeline steps in this order to ensure proper data flow:


### 1. Step 1: Download API Data
```bash
python src/step1_download_api_data.py
```
**Key Outputs:** `data/api_data/store_config_202506A.csv`, `data/api_data/store_sales_202506A.csv`, `data/api_data/complete_category_sales_202506A.csv`

### 2. Step 2: Extract Coordinates
```bash
python src/step2_extract_coordinates.py
```
**Requires:** Step 1: Download API Data
**Key Outputs:** `data/store_coordinates_extended.csv`, `data/spu_store_mapping.csv`, `data/spu_metadata.csv`

### 3. Step 3: Prepare Matrix
```bash
python src/step3_prepare_matrix.py
```
**Requires:** Step 1: Download API Data, Step 2: Extract Coordinates
**Key Outputs:** `data/store_subcategory_matrix.csv`, `data/normalized_subcategory_matrix.csv`, `data/store_spu_limited_matrix.csv`

### 4. Step 4: Download Weather Data
```bash
python src/step4_download_weather_data.py
```
**Requires:** Step 2: Extract Coordinates
**Key Outputs:** `output/store_altitudes.csv`

### 5. Step 5: Calculate Feels Like Temperature
```bash
python src/step5_calculate_feels_like_temperature.py
```
**Requires:** Step 4: Download Weather Data
**Key Outputs:** `output/stores_with_feels_like_temperature.csv`, `output/temperature_bands.csv`

### 6. Step 6: Cluster Analysis
```bash
python src/step6_cluster_analysis.py
```
**Requires:** Step 3: Prepare Matrix
**Key Outputs:** `output/clustering_results.csv`, `output/clustering_results_subcategory.csv`, `output/clustering_results_spu.csv`

### 7. Step 10: SPU Assortment Optimization
```bash
python src/step10_spu_assortment_optimization.py
```
**Requires:** Step 6: Cluster Analysis, Step 1: Download API Data
**Key Outputs:** `output/rule10_spu_overcapacity_results.csv`, `output/rule10_spu_overcapacity_opportunities.csv`

### 8. Step 11: Improved Category Logic
```bash
python src/step11_improved_category_logic.py
```
**Requires:** Step 6: Cluster Analysis, Step 1: Download API Data
**Key Outputs:** `output/rule11_improved_missed_sales_opportunity_spu_results.csv`, `output/rule11_improved_missed_sales_opportunity_spu_details.csv`, `output/rule11_improved_top_performers_by_cluster_category.csv`

### 9. Step 12: Sales Performance Rule
```bash
python src/step12_sales_performance_rule.py
```
**Requires:** Step 6: Cluster Analysis, Step 1: Download API Data
**Key Outputs:** `output/rule12_sales_performance_results.csv`, `output/rule12_sales_performance_details.csv`, `output/rule12_sales_performance_summary.md`

### 10. Step 7: Missing Category Rule
```bash
python src/step7_missing_category_rule.py
```
**Requires:** Step 6: Cluster Analysis, Step 1: Download API Data
**Key Outputs:** `output/rule7_missing_spu_results.csv`, `output/rule7_missing_spu_opportunities.csv`, `output/rule7_missing_spu_summary.md`

### 11. Step 8: Imbalanced Rule
```bash
python src/step8_imbalanced_rule.py
```
**Requires:** Step 6: Cluster Analysis, Step 1: Download API Data
**Key Outputs:** `output/rule8_imbalanced_spu_results.csv`, `output/rule8_imbalanced_spu_cases.csv`, `output/rule8_imbalanced_spu_summary.md`

### 12. Step 9: Below Minimum Rule
```bash
python src/step9_below_minimum_rule.py
```
**Requires:** Step 6: Cluster Analysis, Step 1: Download API Data
**Key Outputs:** `output/rule9_below_minimum_spu_results.csv`, `output/rule9_below_minimum_spu_cases.csv`, `output/rule9_below_minimum_spu_summary.md`

### 13. Step 13: Consolidate SPU Rules
```bash
python src/step13_consolidate_spu_rules.py
```
**Requires:** Step 6: Cluster Analysis, Step 7: Missing Category Rule, Step 8: Imbalanced Rule, Step 9: Below Minimum Rule, Step 10: SPU Assortment Optimization, Step 11: Improved Category Logic, Step 12: Sales Performance Rule
**Key Outputs:** `output/consolidated_spu_rule_results.csv`, `output/consolidated_spu_rule_summary.md`

### 14. Step 14: Global Overview Dashboard
```bash
python src/step14_global_overview_dashboard.py
```
**Requires:** Step 13: Consolidate SPU Rules
**Key Outputs:** `output/global_overview_spu_dashboard.html`

### 15. Step 15: Interactive Map Dashboard
```bash
python src/step15_interactive_map_dashboard.py
```
**Requires:** Step 13: Consolidate SPU Rules, Step 2: Extract Coordinates, Step 7: Missing Category Rule, Step 9: Below Minimum Rule, Step 11: Improved Category Logic, Step 12: Sales Performance Rule
**Key Outputs:** `output/interactive_map_spu_dashboard.html`

## Quick Start Commands

Run all steps in sequence:
```bash
# Core data preparation
python src/step1_download_api_data.py
python src/step2_extract_coordinates.py
python src/step3_prepare_matrix.py

# Weather data (optional but recommended)
python src/step4_download_weather_data.py
python src/step5_calculate_feels_like_temperature.py

# Clustering analysis
python src/step6_cluster_analysis.py

# Business rules analysis
python src/step7_missing_category_rule.py
python src/step8_imbalanced_rule.py
python src/step9_below_minimum_rule.py
python src/step10_spu_assortment_optimization.py
python src/step11_improved_category_logic.py
python src/step12_sales_performance_rule.py

# Consolidation and dashboards
python src/step13_consolidate_spu_rules.py
python src/step14_global_overview_dashboard.py
python src/step15_interactive_map_dashboard.py
```

## Troubleshooting

If a step fails:
1. Check the previous step completed successfully
2. Verify all required input files exist
3. Check the step's specific error messages
4. Ensure sufficient disk space and memory

