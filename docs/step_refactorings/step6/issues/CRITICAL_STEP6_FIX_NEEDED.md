# 🚨 CRITICAL: Step 6 Output Pattern Fix Required

## Problem Identified

**Step 6 (Cluster Analysis) does NOT use the dual output pattern**, creating a critical risk:
- Downstream steps (Step 7+) may read stale clustering files
- No audit trail of clustering results
- Pipeline continuity broken

## Current Behavior (WRONG)

```python
# Step 6 currently does this:
clustering_results.to_csv(f"output/clustering_results_{MATRIX_TYPE}.csv")
cluster_profiles.to_csv(f"output/cluster_profiles_{MATRIX_TYPE}.csv")
# ... etc
```

**Problems:**
1. ❌ No timestamped files (no audit trail)
2. ❌ Overwrites previous results
3. ❌ Downstream steps may use stale data if files aren't updated

## Required Fix

### Update Step 6 to use `create_output_with_symlinks()`

```python
from output_utils import create_output_with_symlinks

# Get period label
from config import get_current_period, get_period_label
yyyymm, period = get_current_period()
period_label = get_period_label(yyyymm, period) if yyyymm and period else ""

# For clustering results
timestamped, period_file, generic = create_output_with_symlinks(
    clustering_results,
    f"output/clustering_results_{MATRIX_TYPE}",
    period_label
)

# For cluster profiles
timestamped, period_file, generic = create_output_with_symlinks(
    cluster_profiles,
    f"output/cluster_profiles_{MATRIX_TYPE}",
    period_label
)

# For per-cluster metrics
timestamped, period_file, generic = create_output_with_symlinks(
    per_cluster_metrics,
    f"output/per_cluster_metrics_{MATRIX_TYPE}",
    period_label
)
```

## Expected Output After Fix

### Files Created:
1. **Timestamped (audit trail):**
   - `output/clustering_results_subcategory_20251004_180954.csv`
   - `output/cluster_profiles_subcategory_20251004_180954.csv`
   - `output/per_cluster_metrics_subcategory_20251004_180954.csv`

2. **Period-specific symlinks:**
   - `output/clustering_results_subcategory_202410A.csv` → timestamped file
   - `output/cluster_profiles_subcategory_202410A.csv` → timestamped file
   - `output/per_cluster_metrics_subcategory_202410A.csv` → timestamped file

3. **Generic symlinks (for downstream steps):**
   - `output/clustering_results_subcategory.csv` → period-specific symlink
   - `output/cluster_profiles_subcategory.csv` → period-specific symlink
   - `output/per_cluster_metrics_subcategory.csv` → period-specific symlink

## Impact on Downstream Steps

### Before Fix:
- Step 7 reads: `output/clustering_results_subcategory.csv` (may be stale)
- No way to know when clustering was last run
- Risk of using outdated cluster assignments

### After Fix:
- Step 7 reads: `output/clustering_results_subcategory.csv` (symlink to latest)
- Timestamped files provide audit trail
- Period-specific symlinks enable period-aware processing
- Pipeline runs reliably without manual file management

## Verification Steps

After implementing the fix:

1. **Run Step 6:**
   ```bash
   PIPELINE_TARGET_YYYYMM=202410 PIPELINE_TARGET_PERIOD=A python src/step6_cluster_analysis.py
   ```

2. **Check files created:**
   ```bash
   ls -la output/clustering_results*
   # Should see:
   # - clustering_results_subcategory_YYYYMMDD_HHMMSS.csv (timestamped)
   # - clustering_results_subcategory_202410A.csv (symlink)
   # - clustering_results_subcategory.csv (symlink)
   ```

3. **Verify symlinks:**
   ```bash
   readlink output/clustering_results_subcategory.csv
   # Should point to: clustering_results_subcategory_202410A.csv
   
   readlink output/clustering_results_subcategory_202410A.csv
   # Should point to: clustering_results_subcategory_YYYYMMDD_HHMMSS.csv
   ```

4. **Test Step 7 integration:**
   ```bash
   # Run Step 7 - should read from generic symlink
   PIPELINE_TARGET_YYYYMM=202410 PIPELINE_TARGET_PERIOD=A python src/step7_missing_category_rule.py
   # Check logs for: "Using cluster file: output/clustering_results_subcategory.csv"
   ```

## Synthetic Test to Create

After fixing Step 6, create: `tests/step06/isolated/test_step6_generic_inputs.py`

**Test cases:**
1. `test_step6_uses_generic_matrix_inputs` - Validates reads from generic matrix symlinks
2. `test_step6_creates_dual_outputs` - Validates timestamped + symlink creation
3. `test_step6_input_fallback_chain` - Validates matrix file fallback logic

**Pattern:** Follow `tests/step07/isolated/test_step7_generic_inputs.py` as template

## Priority

🚨 **CRITICAL - HIGH PRIORITY**

This fix is essential for:
- Pipeline reliability
- Data freshness guarantee
- Audit trail compliance
- Downstream step correctness

## Files to Modify

1. **src/step6_cluster_analysis.py**
   - Add import: `from output_utils import create_output_with_symlinks`
   - Replace all `.to_csv()` calls with `create_output_with_symlinks()`
   - Add period label resolution

2. **tests/step06/isolated/test_step6_generic_inputs.py** (create new)
   - Synthetic test to validate generic input usage
   - Validate dual output pattern

## Related Issues

This is the same issue we found and fixed in Step 7:
- Step 7 was using generic inputs ✅ (already correct)
- Step 7 was creating dual outputs ✅ (already correct)
- Step 6 is using generic inputs ✅ (already correct)
- Step 6 is NOT creating dual outputs ❌ (needs fix)

## Success Criteria

- [ ] Step 6 creates timestamped clustering files
- [ ] Step 6 creates period-specific symlinks
- [ ] Step 6 creates generic symlinks
- [ ] Step 7 reads from Step 6 generic symlinks
- [ ] Step 6 synthetic test passes (2+ tests)
- [ ] Integration tests still pass
- [ ] Pipeline runs end-to-end without manual intervention
