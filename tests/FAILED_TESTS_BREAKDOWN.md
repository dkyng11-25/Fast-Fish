# Failed Tests Breakdown (38 failures)

## Category 1: NEW Dual Output Tests (11 failures)

### Step 13 (1 failure)
- ❌ `test_step13_output_consumable_by_downstream` - Sandbox test, needs full implementation

### Step 14 (3 failures)
- ❌ `test_step14_creates_generic_output` - Sandbox test, needs full implementation
- ❌ `test_step14_generic_file_has_no_timestamp_in_name` - Sandbox test
- ❌ `test_step14_output_consumable_by_downstream` - Sandbox test

### Steps 22, 24-27, 31, 33 (7 failures)
- ❌ `test_step22_creates_output_without_timestamp` - Timestamped files exist
- ❌ `test_step24_creates_output_without_timestamp` - Timestamped files exist
- ❌ `test_step25_creates_output_without_timestamp` - Timestamped files exist
- ❌ `test_step26_creates_output_without_timestamp` - Timestamped files exist
- ❌ `test_step27_creates_output_without_timestamp` - Timestamped files exist
- ❌ `test_step31_creates_output_without_timestamp` - Timestamped files exist
- ❌ `test_step33_creates_output_without_timestamp` - Timestamped files exist

**Root Cause**: These steps create BOTH period-labeled AND timestamped files. The test needs further refinement to check that period-labeled files exist (which they do).

---

## Category 2: OLD Step 7 Synthetic Tests (10 failures)

### test_step7_synthetic_fixture_based.py (5 failures)
- ❌ `test_step7_fixture_basic_execution_isolated`
- ❌ `test_step7_fixture_seasonal_blending_isolated`
- ❌ `test_step7_fixture_output_structure_isolated`
- ❌ `test_step7_fixture_fast_fish_integration_isolated`
- ❌ `test_step7_fixture_cluster_analysis_isolated`

### test_step7_synthetic_missing_category.py (5 failures)
- ❌ `test_step7_synthetic_missing_spu_detection_isolated`
- ❌ `test_step7_synthetic_cluster_based_analysis_isolated`
- ❌ `test_step7_synthetic_seasonal_blending_isolated`
- ❌ `test_step7_synthetic_fast_fish_validation_isolated`
- ❌ `test_step7_synthetic_quantity_recommendations_isolated`

**Root Cause**: Tests use old fixture patterns that don't match current Step 7 implementation. Need to update test fixtures.

---

## Category 3: OLD Step 14 Synthetic Test (1 failure)

- ❌ `test_step14_output_format_validation_synthetic`

**Root Cause**: Missing synthetic input data in sandbox.

---

## Category 4: OLD Step 17 Synthetic Tests (2 failures)

- ❌ `test_step17_execution_with_synthetic_data`
- ❌ `test_step17_synthetic_regression`

**Root Cause**: Missing Step 14 output file in sandbox. Step 17 depends on Step 14 output.

---

## Category 5: OLD Step 32 Synthetic Tests (8 failures)

### test_step32_synthetic_allocation_logic.py (6 failures)
- ❌ `test_weight_based_allocation_distribution`
- ❌ `test_positive_and_negative_allocations`
- ❌ `test_future_oriented_protection_logic`
- ❌ `test_store_group_validation_and_matching`
- ❌ `test_allocation_validation_accuracy`
- ❌ `test_step32_allocation_logic_regression`

### test_step32_synthetic_duplicate_columns.py (2 failures)
- ❌ `test_duplicate_column_detection_and_removal`
- ❌ `test_store_mapping_validation_and_fallback`
- ❌ `test_allocation_accuracy_with_duplicates`
- ❌ `test_step32_duplicate_column_regression`

**Root Cause**: Tests may need updating for current Step 32 implementation or have dependency issues.

---

## Category 6: OLD Step 36 Synthetic Tests (4 failures)

- ❌ `test_step36_category_validation`
- ❌ `test_step36_temperature_mapping`
- ❌ `test_step36_womens_casual_pants_presence`
- ❌ `test_step36_planning_season_mapping`

**Root Cause**: Tests may need updating or have missing dependencies (Step 32 output, etc.).

---

## Summary by Category

| Category | Failures | % of Total | Priority |
|----------|----------|------------|----------|
| **NEW Dual Output** | 11 | 29% | 🟡 Medium (mostly working, need refinement) |
| **OLD Step 7** | 10 | 26% | 🔴 High (need fixture updates) |
| **OLD Step 32** | 8 | 21% | 🔴 High (core allocation logic) |
| **OLD Step 36** | 4 | 11% | 🟡 Medium (delivery builder) |
| **OLD Step 17** | 2 | 5% | 🟡 Medium (need Step 14 fixture) |
| **OLD Step 14** | 1 | 3% | 🟡 Medium (need synthetic inputs) |
| **OLD Step 2b** | 2 | 5% | 🟢 Low |
| **TOTAL** | **38** | **100%** | |

## Fix Priority

### 🔴 HIGH PRIORITY (18 failures)
1. **Step 7 tests** (10) - Update fixtures to match current implementation
2. **Step 32 tests** (8) - Core allocation logic, business critical

### 🟡 MEDIUM PRIORITY (18 failures)
3. **Dual output tests** (11) - Refine test logic for timestamped files
4. **Step 36 tests** (4) - Delivery builder validation
5. **Step 17 tests** (2) - Add Step 14 fixture
6. **Step 14 test** (1) - Add synthetic inputs

### 🟢 LOW PRIORITY (2 failures)
7. **Step 2b tests** (2) - Seasonal consolidation

## Quick Wins

These can be fixed quickly:
1. ✅ Dual output tests (11) - Just refine the assertion logic
2. ✅ Step 17 tests (2) - Create Step 14 output fixture
3. ✅ Step 14 test (1) - Add synthetic inputs

## Recommended Action Plan

1. **Phase 1**: Fix dual output test logic (11 tests) - 1 hour
2. **Phase 2**: Update Step 7 fixtures (10 tests) - 2-3 hours
3. **Phase 3**: Debug Step 32 tests (8 tests) - 2-3 hours
4. **Phase 4**: Fix Step 36 tests (4 tests) - 1-2 hours
5. **Phase 5**: Fix remaining tests (5 tests) - 1 hour

**Total Estimated Time**: 7-10 hours to fix all 38 failures
