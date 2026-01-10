# Step 18 Gender Preservation Fix

## Problem Identified
Step 18 was losing ALL neutral gender (中性) values, causing the gender distribution to change significantly from Step 14 to Step 36.

### Root Cause
Two bugs in `src/step18_validate_results.py`:

1. **Incomplete gender mapping (Line 252)**
   - Original: `gender_map = {'男': 'Men', '女': 'Women', '中': 'Unisex'}`
   - Problem: '中性' not in map, so treated as ambiguous

2. **Neutral marked as ambiguous (Line 312)**
   - Original: `amb_gender = {'Unisex', '中性', 'Unknown'}`
   - Problem: '中性' treated as ambiguous → gets replaced with store_config lookup

### Impact
- Step 14: 376 neutral records (5.90%)
- Step 18: 0 neutral records (0.00%) ❌
- Step 36: 1,521 neutral records (0.50%) ❌

Gender distribution skewed:
- Female: 75.63% → 86.78% (+11%)
- Male: 18.48% → 12.72% (-6%)
- Neutral: 5.90% → 0.50% (-5%)

## Fix Applied

### Changes to `src/step18_validate_results.py`

**Line 252 - Preserve Chinese gender values:**
```python
# BEFORE
gender_map = {'男': 'Men', '女': 'Women', '中': 'Unisex'}

# AFTER
gender_map = {'男': '男', '女': '女', '中': '中性', '中性': '中性'}
```

**Line 312 - Remove neutral from ambiguous set:**
```python
# BEFORE
amb_gender = {'Unisex', '中性', 'Unknown'}

# AFTER
amb_gender = {'Unknown', ''}
```

## Test Coverage

### Isolated Unit Test
**File:** `tests/step18/isolated/test_step18_gender_preservation_isolated.py`

**What it tests:**
1. Gender mapping logic preserves Chinese values
2. Neutral gender (中性) is not treated as ambiguous
3. Gender distribution is maintained
4. Edge cases (empty, None, Unknown values)

**How to run:**
```bash
cd tests/step18/isolated
python3 test_step18_gender_preservation_isolated.py
```

**Expected output:**
```
✅ ALL TESTS PASSED

The fixed gender mapping logic correctly:
  1. Preserves neutral gender (中性)
  2. Maintains gender distribution
  3. Handles edge cases properly
```

## Validation Steps

### 1. Run the isolated test
```bash
cd tests/step18/isolated
python3 test_step18_gender_preservation_isolated.py
```

### 2. Run Step 18 with the fix
```bash
PYTHONPATH=. python3 src/step18_validate_results.py --target-yyyymm 202511 --target-period A
```

### 3. Verify gender distribution
```python
import pandas as pd

# Load Step 14 output
df14 = pd.read_csv('output/enhanced_fast_fish_format_202511A_*.csv')
print("Step 14 Gender:", df14['Gender'].value_counts())

# Load Step 18 output (after fix)
df18 = pd.read_csv('output/fast_fish_with_sell_through_analysis_202511A_*.csv')
print("Step 18 Gender:", df18['Gender'].value_counts())

# Should match!
```

### 4. Run full pipeline validation
```bash
# Run Steps 18-36 to verify no regressions
PYTHONPATH=. python3 src/step18_validate_results.py --target-yyyymm 202511 --target-period A
# ... continue with remaining steps
```

## Success Criteria

✅ Neutral gender (中性) preserved in Step 18 output
✅ Gender distribution matches Step 14 (±1% tolerance)
✅ No regressions in downstream steps (19-36)

**Target distribution (from Step 14):**
- Female (女): ~75-76%
- Male (男): ~18-19%
- Neutral (中性): ~5-6%

## Files Modified

1. `src/step18_validate_results.py` - Applied fix
2. `tests/step18/isolated/test_step18_gender_preservation_isolated.py` - New test

## Date
October 16, 2025
