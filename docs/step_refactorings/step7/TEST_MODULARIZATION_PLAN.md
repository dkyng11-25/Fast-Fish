# Step 7: Test Modularization Plan

**Date:** 2025-11-03 1:20 PM  
**Status:** conftest.py created (221 LOC), ready for remaining modularization

---

## 🎯 Objective

Modularize `test_step7_missing_category_rule.py` (734 LOC) into 7 files (each <500 LOC) following CUPID principles and established standards from Steps 1, 2, 4-5, 6.

---

## ✅ Completed

### File 1: `tests/step7/conftest.py` (221 LOC) ✅
**Purpose:** Shared fixtures for all Step 7 tests

**Contents:**
- `test_context()` - Test context management
- `mock_logger()` - Mock pipeline logger
- `step_config()` - Step configuration
- `mock_cluster_repo()` - Mock clustering repository (50 stores, 3 clusters)
- `mock_sales_repo()` - Mock sales repository (realistic sales data)
- `mock_quantity_repo()` - Mock quantity repository (unit prices)
- `mock_margin_repo()` - Mock margin repository (ROI calculation)
- `mock_output_repo()` - Mock output repository (file saving)
- `mock_sellthrough_validator()` - Mock sell-through validator
- `step_instance()` - Fully configured step instance

**Status:** ✅ Created and verified

---

## ⏭️ Remaining Files (6 files)

### File 2: `tests/step7/test_e2e.py` (~140 LOC)
**Purpose:** End-to-end integration test

**Test:** `test_successfully_identify_missing_categories_with_quantity_recommendations`

**BDD Steps:**
- `@given` - Step initialized, repos mocked, config set
- `@given` - Clustering results (3 clusters, 50 stores)
- `@given` - Sales data with subcategories
- `@given` - Quantity data with real prices
- `@given` - Margin rates for ROI
- `@given` - Sell-through validator available
- `@when` - Execute complete step
- `@then` - Well-selling categories identified
- `@then` - Missing opportunities found
- `@then` - Quantities calculated using real prices
- `@then` - Sell-through validation approves opportunities
- `@then` - Store results aggregated
- `@then` - Opportunities CSV created with required columns
- `@then` - Store results CSV created
- `@then` - All outputs registered in manifest

**Status:** ✅ PASSING (33 opportunities generated)

---

### File 3: `tests/step7/test_setup_phase.py` (~120 LOC)
**Purpose:** Setup phase tests (data loading)

**Tests (5):**
1. `test_load_clustering_results_with_column_normalization`
   - Verify "Cluster" → "cluster_id" normalization
   - Ensure all stores have cluster assignments

2. `test_load_sales_data_with_seasonal_blending_enabled`
   - Test seasonal blending (40% recent + 60% seasonal)
   - Verify weighted sales aggregation

3. `test_backfill_missing_unit_prices_from_historical_data`
   - Test historical price backfill
   - Verify backfill count logging

4. `test_fail_when_no_real_prices_available_in_strict_mode`
   - Verify DataValidationError when no prices
   - Check error message clarity

5. `test_setup_loads_all_required_data`
   - Verify all data sources loaded
   - Check data completeness

**BDD Steps:**
- Column normalization steps
- Seasonal blending steps
- Price backfill steps
- Error handling steps

---

### File 4: `tests/step7/test_apply_phase.py` (~150 LOC)
**Purpose:** Apply phase tests (business logic)

**Tests (9):**
1. `test_identify_wellselling_subcategories_meeting_adoption_threshold`
   - Verify 70% adoption threshold
   - Check well-selling feature identification

2. `test_apply_higher_thresholds_for_spu_mode`
   - Test SPU-level analysis
   - Verify stricter thresholds

3. `test_calculate_expected_sales_with_outlier_trimming`
   - Test outlier removal (10% trim)
   - Verify expected sales calculation

4. `test_apply_spuspecific_sales_cap`
   - Test SPU sales cap logic
   - Verify capping behavior

5. `test_use_store_average_from_quantity_data_priority_1`
   - Test price resolution priority 1
   - Verify store-specific prices used

6. `test_fallback_to_cluster_median_when_store_price_unavailable`
   - Test price resolution priority 2
   - Verify cluster median fallback

7. `test_skip_opportunity_when_no_valid_price_available`
   - Test price resolution failure
   - Verify opportunity skipped

8. `test_identify_missing_stores_for_well_selling_features`
   - Verify missing store identification
   - Check opportunity generation

9. `test_calculate_expected_sales_for_missing_stores`
   - Test expected sales calculation
   - Verify peer median logic

**BDD Steps:**
- Well-selling identification steps
- Price resolution steps
- Opportunity identification steps
- Sales calculation steps

---

### File 5: `tests/step7/test_quantity_and_roi.py` (~100 LOC)
**Purpose:** Quantity calculation and ROI tests

**Tests (5):**
1. `test_calculate_integer_quantity_from_expected_sales`
   - Test quantity = ceil(expected_sales / unit_price)
   - Verify integer rounding

2. `test_ensure_minimum_quantity_of_1_unit`
   - Test minimum quantity enforcement
   - Verify no zero quantities

3. `test_calculate_roi_with_margin_rates`
   - Test ROI calculation
   - Verify margin rate application

4. `test_filter_opportunity_by_roi_threshold`
   - Test ROI threshold filtering
   - Verify low ROI rejection

5. `test_filter_opportunity_by_margin_uplift_threshold`
   - Test margin uplift filtering
   - Verify threshold application

**BDD Steps:**
- Quantity calculation steps
- ROI calculation steps
- Filtering steps

---

### File 6: `tests/step7/test_validation_and_aggregation.py` (~120 LOC)
**Purpose:** Validation and aggregation tests

**Tests (7):**
1. `test_approve_opportunity_meeting_all_validation_criteria`
   - Test sell-through validation approval
   - Verify all criteria met

2. `test_reject_opportunity_with_low_predicted_sellthrough`
   - Test sell-through rejection
   - Verify threshold enforcement

3. `test_reject_opportunity_with_low_cluster_adoption`
   - Test adoption threshold rejection
   - Verify cluster-level filtering

4. `test_aggregate_multiple_opportunities_per_store`
   - Test store-level aggregation
   - Verify quantity summation

5. `test_handle_stores_with_no_opportunities`
   - Test zero-opportunity stores
   - Verify graceful handling

6. `test_validate_results_have_required_columns`
   - Test schema validation
   - Verify required columns present

7. `test_fail_validation_when_required_columns_missing`
   - Test validation failure
   - Verify DataValidationError

**BDD Steps:**
- Validation steps
- Aggregation steps
- Schema validation steps

---

### File 7: `tests/step7/test_persist_and_edge_cases.py` (~120 LOC)
**Purpose:** Persist phase and edge case tests

**Tests (8):**
1. `test_fail_validation_with_negative_quantities`
   - Test negative quantity detection
   - Verify DataValidationError

2. `test_validate_opportunities_have_required_columns`
   - Test opportunity schema validation
   - Verify column requirements

3. `test_save_opportunities_csv_with_timestamped_filename`
   - Test CSV file saving
   - Verify timestamp format

4. `test_register_outputs_in_manifest`
   - Test output registration
   - Verify manifest update

5. `test_generate_markdown_summary_report`
   - Test report generation
   - Verify report content

6. `test_complete_spulevel_analysis_with_all_features`
   - Test SPU-level E2E
   - Verify complete workflow

7. `test_handle_empty_sales_data`
   - Test empty data handling
   - Verify graceful failure

8. `test_handle_cluster_with_single_store`
   - Test edge case: 1 store per cluster
   - Verify threshold behavior

9. `test_handle_all_opportunities_rejected_by_sellthrough`
   - Test all rejections scenario
   - Verify empty results handling

10. `test_handle_missing_sellthrough_validator`
    - Test missing validator
    - Verify fallback behavior

**BDD Steps:**
- Persist phase steps
- Edge case steps
- Error handling steps

---

## 📊 File Size Summary

| File | Purpose | LOC | Status |
|------|---------|-----|--------|
| `conftest.py` | Shared fixtures | 221 | ✅ Created |
| `test_e2e.py` | E2E integration | ~140 | ⏭️ Pending |
| `test_setup_phase.py` | Setup phase | ~120 | ⏭️ Pending |
| `test_apply_phase.py` | Apply phase | ~150 | ⏭️ Pending |
| `test_quantity_and_roi.py` | Quantity/ROI | ~100 | ⏭️ Pending |
| `test_validation_and_aggregation.py` | Validation | ~120 | ⏭️ Pending |
| `test_persist_and_edge_cases.py` | Persist/Edge | ~120 | ⏭️ Pending |
| **TOTAL** | | **~971** | **221 done** |

**Original:** 734 LOC (single file)  
**Modularized:** ~971 LOC (7 files, avg 139 LOC/file)  
**Overhead:** ~237 LOC (imports, docstrings, organization)

---

## 🔧 Implementation Strategy

### Option A: Complete Modularization Now (2-3 hours)
**Pros:**
- 100% standards compliance immediately
- All tests organized by phase
- Easy to maintain and extend

**Cons:**
- Time-intensive
- 24 tests still failing
- May need to fix tests during split

### Option B: Fix Failing Tests First, Then Modularize (Recommended)
**Pros:**
- Get to 100% test pass rate faster
- Understand test patterns before splitting
- Less rework if tests need changes

**Cons:**
- Temporary non-compliance with 500 LOC limit
- Need to track modularization as debt

### Option C: Hybrid Approach
**Pros:**
- Create structure now (conftest.py ✅)
- Move passing tests to new files
- Fix failing tests in place
- Move fixed tests to appropriate files

**Cons:**
- Tests split across old and new structure temporarily
- Need to track which tests moved

---

## 💡 Recommendation

**Proceed with Option B: Fix Failing Tests First**

**Rationale:**
1. E2E test is passing (main goal achieved)
2. Implementation is 100% compliant
3. Test modularization is organizational, not functional
4. Faster path to 100% test pass rate
5. Better understanding of test patterns before splitting

**Timeline:**
- Fix 24 failing tests: 2-4 hours
- Modularize after all pass: 1-2 hours
- **Total: 3-6 hours to complete Phase 4**

---

## 📋 Next Steps

1. ✅ conftest.py created (221 LOC)
2. ⏭️ Fix remaining 24 failing tests
3. ⏭️ Achieve 100% test pass rate (34/34)
4. ⏭️ Modularize tests into 7 files
5. ⏭️ Verify all tests still pass
6. ⏭️ Final compliance check

---

**Status:** Ready to proceed with fixing remaining tests! 🚀
