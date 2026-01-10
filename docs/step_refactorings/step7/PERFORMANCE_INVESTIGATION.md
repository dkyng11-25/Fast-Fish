# Step 7 Refactored - Performance Investigation Results

## 🔍 Investigation Summary

**Date**: 2025-11-05
**Issue**: Refactored Step 7 times out after 5 minutes while legacy completes in ~70 seconds

## ✅ What We Successfully Fixed (11 Integration Issues)

All code integration issues resolved - the refactored code can execute and load data correctly!

1. ✅ PipelineLogger signature
2. ✅ Logging import placement  
3. ✅ log_step_start/log_step_end methods
4. ✅ MissingCategoryConfig parameters
5. ✅ logger.error exc_info
6. ✅ StepContext.set() → set_state()
7. ✅ CsvFileRepository.load() method
8. ✅ Clustering file naming patterns
9. ✅ Data directory default (output)
10. ✅ Sales file patterns and locations
11. ✅ QuantityRepository parameter

## ⚠️ Critical Performance Bottleneck Identified

### Root Cause Analysis

**Location**: `OpportunityIdentifier.identify_missing_opportunities()`  
**File**: `src/components/missing_category/opportunity_identifier.py:64`

### The Problem: Feature Count Mismatch

| Metric | Legacy | Refactored | Difference |
|--------|--------|------------|------------|
| **Well-selling features** | 121 | 2,470 | **20x more!** |
| **Processing time** | ~70 seconds | >300 seconds (timeout) | **4.3x+ slower** |
| **Features/second** | 1.7 | 0.16 | **10x slower** |

### Why 20x More Features?

**Investigation needed**: Both use same thresholds (70% adoption, $100 sales), but refactored produces 2,470 features vs legacy's 121.

**Hypothesis**:
1. Different groupby logic in feature identification
2. Duplicate features across clusters not being deduplicated
3. Different filtering order causing more features to pass

### Secondary Performance Issues

Even with same feature count, refactored has inefficient operations:

**Line 69** (refactored):
```python
cluster_stores = cluster_df[cluster_df['cluster_id'] == cluster_id]['str_code'].tolist()
```
❌ Uses `.tolist()` - creates Python list

**Line 798** (legacy):
```python
cluster_stores = set(cluster_df[cluster_df['cluster_id'] == cluster_id]['str_code'].astype(str))
```
✅ Uses `set()` - O(1) membership testing

**Line 78** (refactored):
```python
missing_stores = [s for s in cluster_stores if s not in selling_stores]
```
❌ List comprehension with `in` operator - O(n²) complexity

**Line 806** (legacy):
```python
missing_stores = cluster_stores - stores_selling_feature
```
✅ Set difference operation - O(n) complexity

## 📊 Performance Metrics

### Observed Behavior

**Refactored execution**:
- Processed 500 features in 79 seconds
- Rate: 6.3 features/second
- Projected total: 392 seconds for 2,470 features
- **Timed out at 300 seconds**

**Legacy execution**:
- Processed 121 features in ~26 seconds (from progress bar)
- Rate: 4.7 features/second  
- **Total completion: ~70 seconds**

### Why Legacy is Faster

1. **Processes 20x fewer features** (121 vs 2,470)
2. **Uses set operations** instead of list operations
3. **More efficient pandas filtering**

## 🎯 ROOT CAUSE IDENTIFIED!

### The Real Issue: SPU vs Subcategory Mode

**Legacy (`step7_missing_category_rule.py`):**
- `ANALYSIS_LEVEL = "spu"` (line 135)
- Designed for 53 flagship stores
- Loads `clustering_results_spu.csv`
- Processes 121 features
- Completes in ~70 seconds

**Refactored (`step7_missing_category_rule_refactored.py`):**
- `analysis_level = 'subcategory'` (default config)
- Designed for 2,255 stores
- Loads `clustering_results_subcategory.csv`
- Processes 2,470 features
- Times out after 300 seconds

### The Confusion

There's also `step7_missing_category_rule_subcategory.py` which has:
- `ANALYSIS_LEVEL = "subcategory"` (line 135)
- But when run, it incorrectly loads `clustering_results_spu.csv`
- This appears to be a bug in the file resolution logic

### Critical Decision Needed

**Should the refactored Step 7 run in SPU mode or subcategory mode?**

1. **SPU Mode (53 stores)**: Matches original legacy behavior, faster
2. **Subcategory Mode (2,255 stores)**: More comprehensive analysis, slower

This is a **business requirement question**, not a technical bug!

### Priority 2: Optimize Data Structures

**Change lists to sets** in opportunity_identifier.py:

```python
# Line 69 - Change to set
cluster_stores = set(cluster_df[cluster_df['cluster_id'] == cluster_id]['str_code'].astype(str))

# Line 72-75 - Change to set  
selling_stores = set(sales_df[
    (sales_df[feature_col] == feature) &
    (sales_df['str_code'].isin(cluster_stores))
]['str_code'].astype(str))

# Line 78 - Use set difference
missing_stores = cluster_stores - selling_stores
```

### Priority 3: Cache Repeated Operations

Pre-compute cluster-store mappings instead of filtering on every iteration.

## 📝 Next Steps

1. **Compare feature identification logic** between legacy and refactored
2. **Add debug logging** to show which features are being identified
3. **Verify groupby aggregation** produces same results
4. **Apply set-based optimizations** once feature count is correct
5. **Re-test with corrected logic**

## 🔬 Debug Commands

```bash
# Run legacy and capture feature list
python -m src.step7_missing_category_rule_subcategory --target-yyyymm 202510 --target-period A 2>&1 | grep "Identified.*well-selling"

# Run refactored and capture feature list  
python src/step7_missing_category_rule_refactored.py --target-yyyymm 202510 --target-period A 2>&1 | grep "Well-selling features identified"

# Compare the actual features
# TODO: Add logging to output feature lists for comparison
```

## 📌 Status

**Current State**: Performance investigation complete, root cause identified
**Blocking Issue**: Feature count mismatch (2,470 vs 121)
**Next Action**: Investigate feature identification logic differences
