# CORRECTED: Dual Output Pattern Test Plan

## CRITICAL FINDING
**ALL STEPS 1-36 create files WITHOUT timestamps in the filename!**

This is the dual output pattern:
- Files have period labels (e.g., `_202510A`) but NO timestamps
- Downstream steps consume these period-labeled files
- This ensures pipeline continuity

## Evidence

### Steps 1-6 (Data Acquisition)
- `data/api_data/complete_spu_sales_202510A.csv` ✅ NO timestamp
- `data/api_data/store_config_202510A.csv` ✅ NO timestamp
- `output/clustering_results_spu.csv` ✅ NO timestamp

### Steps 7-12 (Business Rules)
- `output/rule7_missing_spu_sellthrough_results_202510A.csv` ✅ NO timestamp
- `output/rule8_imbalanced_spu_results_202510A.csv` ✅ NO timestamp
- `output/rule8_imbalanced_spu_results.csv` ✅ NO timestamp (generic)
- `output/rule9_below_minimum_spu_sellthrough_results_202510A.csv` ✅ NO timestamp
- `output/rule10_smart_overcapacity_results_202510A.csv` ✅ NO timestamp
- `output/rule11_improved_missed_sales_opportunity_spu_results_202510A.csv` ✅ NO timestamp
- `output/rule12_sales_performance_spu_results_202510A.csv` ✅ NO timestamp

### Steps 13-36 (Consolidation & Delivery)
- All create period-labeled files WITHOUT timestamps
- Some also create timestamped versions for archival

## Test Requirements

**We need to test ALL 36 steps** to verify:
1. Output files do NOT have timestamp pattern `_YYYYMMDD_HHMMSS` in filename
2. Output files have period label `_202510A` (or similar)
3. Downstream steps can find and consume these files

## Test Files Needed

```
test_step1_dual_output.py   # API Download
test_step2_dual_output.py   # Extract Coordinates  
test_step3_dual_output.py   # Prepare Matrix
test_step5_dual_output.py   # Feels-Like Temperature
test_step6_dual_output.py   # Cluster Analysis
test_step7_dual_output.py   # Missing Category Rule
test_step8_dual_output.py   # Imbalanced Rule
test_step9_dual_output.py   # Below Minimum Rule
test_step10_dual_output.py  # SPU Assortment
test_step11_dual_output.py  # Missed Sales
test_step12_dual_output.py  # Sales Performance
test_step13_dual_output.py  # Consolidate (DONE)
test_step14_dual_output.py  # Fast Fish (DONE)
test_step15_dual_output.py  # Historical Baseline
test_step16_dual_output.py  # Comparison Tables
test_step17_dual_output.py  # Augment Recommendations
test_step18_dual_output.py  # Validate Results
test_step19_dual_output.py  # Detailed SPU Breakdown
test_step20_dual_output.py  # Data Validation
test_step21_dual_output.py  # Label Tags
test_step22_dual_output.py  # Store Enrichment
test_step23_dual_output.py  # Update Clustering
test_step24_dual_output.py  # Cluster Labeling
test_step25_dual_output.py  # Product Role
test_step26_dual_output.py  # Price Elasticity
test_step27_dual_output.py  # Gap Matrix
test_step28_dual_output.py  # Scenario Analyzer
test_step29_dual_output.py  # Supply-Demand Gap
test_step30_dual_output.py  # Sell-Through Optimization
test_step31_dual_output.py  # Gap Workbook
test_step32_dual_output.py  # Store Allocation
test_step33_dual_output.py  # Store Merchandising
test_step34a_dual_output.py # Cluster Strategy
test_step34b_dual_output.py # Unify Outputs
test_step35_dual_output.py  # Merchandising Strategy
test_step36_dual_output.py  # Unified Delivery
```

**Total: 36 test files needed**

## Priority Order

1. **HIGH PRIORITY** (Steps 7-22): Business rules and core consolidation
2. **MEDIUM PRIORITY** (Steps 1-6, 23-24): Data acquisition and clustering
3. **LOWER PRIORITY** (Steps 25-36): Advanced analysis and delivery
