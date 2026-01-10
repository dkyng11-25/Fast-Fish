# RUNBOOK: End-to-End Pipeline (202508A)

This runbook documents how to run each pipeline step (1 → 36) to reproduce the 202508A results, including balanced weather integration and forward-oriented allocation.

All commands assume:
- Run from project root
- `PYTHONPATH=.`
- Target period label: 202508A (`--target-yyyymm 202508 --target-period A`)

---

## Prerequisites
- Keep HK VPN on for API downloads (Step 1) to avoid connection resets.
- Ensure period-specific CSVs (not LFS pointers) are present in `output/` or `data/api_data/` when required.
- Keep `str_code` as string in all steps to avoid join loss.

---

## Global Notes
- Target label controls filenames and reporting period.
- Some loaders allow a different data source period via env variables to use prior/YoY periods.

---

## Step-by-Step Commands

### Step 1 – Download API Data
```bash
PYTHONPATH=. python3 src/step1_download_api_data.py --target-yyyymm 202508 --target-period A
```

### Step 2 – Extract Coordinates
```bash
PYTHONPATH=. python3 src/step2_extract_coordinates.py --target-yyyymm 202508 --target-period A
```

### Step 2B – Consolidate Seasonal Data
```bash
PYTHONPATH=. python3 src/step2b_consolidate_seasonal_data.py --target-yyyymm 202508 --target-period A
```

### Step 3 – Prepare Matrix
```bash
# Optional: STEP3_INPUT_PERIODS="202506B,202507A,202507B,202508A,202408B,202409A,202409B,202410A,202410B,202411A"
PYTHONPATH=. python3 src/step3_prepare_matrix.py --target-yyyymm 202508 --target-period A
```

### Step 4 – (If present) Data Cleansing
```bash
PYTHONPATH=. python3 src/step4_*.py --target-yyyymm 202508 --target-period A
```

### Step 5 – Calculate Feels-Like Temperature (Balanced Weather)
```bash
PYTHONPATH=. python3 src/step5_calculate_feels_like_temperature.py --target-yyyymm 202508 --target-period A
```
Outputs: `output/stores_with_feels_like_temperature.csv`

### Steps 6–12 – Clustering and Rules
```bash
PYTHONPATH=. python3 src/step6_*.py --target-yyyymm 202508 --target-period A
# ...
PYTHONPATH=. python3 src/step12_sales_performance_rule.py --target-yyyymm 202508 --target-period A
```

### Step 13 – Consolidate SPU Rules
```bash
PYTHONPATH=. python3 src/step13_consolidate_spu_rules.py --target-yyyymm 202508 --target-period A
```

### Step 14 – Create Enhanced Fast Fish Format (YoY-forward example used)
```bash
STEP14_SPU_SALES_FILE=output/complete_spu_sales_202410A.csv \
STEP14_STORE_CONFIG_FILE=output/store_config_202410A.csv \
STEP14_BASELINE_YYYYMM=202410 \
STEP14_BASELINE_PERIOD=A \
PYTHONPATH=. python3 src/step14_create_fast_fish_format.py --target-yyyymm 202508 --target-period A
```
Output: `output/enhanced_fast_fish_format_202508A.csv`

### Step 15 – Historical Baseline
```bash
PYTHONPATH=. python3 src/step15_download_historical_baseline.py --target-yyyymm 202508 --target-period A
```

### Step 16 – Comparison Tables
```bash
PYTHONPATH=. python3 src/step16_create_comparison_tables.py --target-yyyymm 202508 --target-period A
```

### Step 17 – Augment Recommendations (historical-only used)
```bash
PYTHONPATH=. python3 src/step17_augment_recommendations.py \
  --target-yyyymm 202508 --target-period A \
  --input-file output/enhanced_fast_fish_format_202508A.csv
```

### Step 18 – Sell-Through Analysis
```bash
PYTHONPATH=. python3 src/step18_validate_results.py --target-yyyymm 202508 --target-period A
```

### Step 19 – Detailed SPU Breakdown
```bash
PYTHONPATH=. python3 src/step19_detailed_spu_breakdown.py --target-yyyymm 202508 --target-period A
```

### Step 20 – Data Validation
```bash
PYTHONPATH=. python3 src/step20_data_validation.py --target-yyyymm 202508 --target-period A
```

### Step 21 – Label/Tag Recommendations
```bash
PYTHONPATH=. python3 src/step21_label_tag_recommendations.py --target-yyyymm 202508 --target-period A
```

### Step 22 – Store Attribute Enrichment (uses Step 5)
```bash
PYTHONPATH=. python3 src/step22_store_attribute_enrichment.py --target-yyyymm 202508 --target-period A
```
Outputs: `output/enriched_store_attributes_202508A_<ts>.csv` and alias `output/enriched_store_attributes.csv`

### Step 23 – Update Clustering Features
```bash
PYTHONPATH=. python3 src/step23_update_clustering_features.py --target-yyyymm 202508 --target-period A
```

### Step 24 – Comprehensive Cluster Labeling
```bash
PYTHONPATH=. python3 src/step24_comprehensive_cluster_labeling.py --target-yyyymm 202508 --target-period A
```

### Step 25 – Product Role Classification
```bash
PIPELINE_YYYYMM=202508 PIPELINE_PERIOD=A \
PYTHONPATH=. python3 src/step25_product_role_classifier.py --target-yyyymm 202508 --target-period A
```

### Step 26 – Price Bands (Elasticity skipped)
```bash
STEP26_SKIP_ELASTICITY=1 \
PIPELINE_YYYYMM=202508 PIPELINE_PERIOD=A \
STEP26_PRODUCT_ROLES_FILE=output/product_role_classifications_202508A_20250918_173324.csv \
PYTHONPATH=. python3 src/step26_price_elasticity_analyzer.py --target-yyyymm 202508 --target-period A
```

### Step 27 – Gap Matrix
```bash
PIPELINE_YYYYMM=202508 PIPELINE_PERIOD=A \
PYTHONPATH=. python3 src/step27_gap_matrix_generator.py --target-yyyymm 202508 --target-period A
```

### Step 28 – Scenario Analyzer
```bash
PIPELINE_YYYYMM=202508 PIPELINE_PERIOD=A \
PYTHONPATH=. python3 src/step28_scenario_analyzer.py --target-yyyymm 202508 --target-period A
```

### Step 29 – Supply-Demand Gap Analysis
```bash
PIPELINE_YYYYMM=202508 PIPELINE_PERIOD=A \
PYTHONPATH=. python3 src/step29_supply_demand_gap_analysis.py --target-yyyymm 202508 --target-period A
```

### Step 30 – Sell-through Optimization Engine
```bash
PIPELINE_YYYYMM=202508 PIPELINE_PERIOD=A \
PYTHONPATH=. python3 src/step30_sellthrough_optimization_engine.py --target-yyyymm 202508 --target-period A
```

### Step 31 – Gap Analysis Workbook
```bash
PIPELINE_YYYYMM=202508 PIPELINE_PERIOD=A \
PYTHONPATH=. python3 src/step31_gap_analysis_workbook.py --target-yyyymm 202508 --target-period A
```

### Step 32 – Store-Level Allocation (Future-Oriented; uses balanced weather)
```bash
PIPELINE_TARGET_YYYYMM=202508 PIPELINE_TARGET_PERIOD=A \
FUTURE_PROTECT=1 FUTURE_FORWARD_HALVES=4 FUTURE_ANCHOR_SOURCE=spu_sales FUTURE_USE_YOY=1 \
FUTURE_REDUCTION_SCALER=0.4 FUTURE_ADDITION_BOOST=1.25 FUTURE_AUDIT=1 \
PYTHONPATH=. python3 src/step32_store_allocation.py --target-yyyymm 202508 --period A
```

### Step 33 – Store-Level Merchandising Rules
```bash
PYTHONPATH=. python3 src/step33_store_level_merchandising_rules.py --target-yyyymm 202508 --target-period A
```

### Step 34A – Cluster Strategy Optimization
```bash
PYTHONPATH=. python3 src/step34a_cluster_strategy_optimization.py --target-yyyymm 202508 --target-period A
```

### Step 34B – Unify Outputs (reads Step 18)
```bash
PYTHONPATH=. python3 src/step34b_unify_outputs.py --target-yyyymm 202508 --periods A --source step18
```

### Step 35 – Merchandising Strategy Deployment
```bash
PYTHONPATH=. python3 src/step35_merchandising_strategy_deployment.py --target-yyyymm 202508 --target-period A
```

### Step 36 – Unified Delivery Builder (final outputs)
```bash
PYTHONPATH=. python3 src/step36_unified_delivery_builder.py --target-yyyymm 202508 --target-period A
```
Outputs:
- `output/unified_delivery_202508A_*.csv` / `.xlsx`
- `output/unified_delivery_202508A_*_validation.json`

---

## Critical Steps & Pitfalls
- **Step 5 (Weather)**: Produces `stores_with_feels_like_temperature.csv` → must exist and have `feels_like_temperature`, `temperature_band`.
- **Step 14 (YoY-forward)**: Use the env overrides shown to bias mix toward upcoming AW without hardcoding season.
- **Step 22 (Enrichment)**: Generates `enriched_store_attributes_...` with `temperature_zone_tags` and related fields used downstream.
- **Step 25/26/27+ (Period-aware)**: If loaders complain about missing sales, set `PIPELINE_YYYYMM` and `PIPELINE_PERIOD` to real available periods.
- **Step 32 (Future-Oriented)**: `FUTURE_PROTECT`, `FUTURE_FORWARD_HALVES`, `FUTURE_USE_YOY` control anchor derivation and protection/boosting.
- **Step 36 (Final QA)**: Check season distribution and validation JSON for reconciliation mismatches.

---

## Season Mix (for reference)
- 2025-08 A (final unified): AW 48.0%, Summer 47.7%, Spring 1.2%, Universal 3.1% (`output/unified_delivery_202508A_*.csv`)
- 2024-08 A (store_config reference): AW 47.7%, Summer 47.3%, Spring 3.9%, Universal 1.2% (`output/store_config_202408A.csv`)

---

## Testing
- Run specific tests we added:
```bash
pytest -q tests/step32/test_step32_future_orientation.py tests/step17/test_step17_imports_and_smoke.py
```

---

## Contacts
- Pipeline team: see repo README and code owners in `CODEOWNERS` (if present).
