# Step 7 Debug Findings - ROI Calculation Discrepancy

**Date:** 2025-11-07  
**Issue:** Refactored produces 898 opportunities vs Legacy 1,388

## Root Cause Identified

The legacy code uses **TWO DIFFERENT quantities** in its calculations:

### 1. `expected_quantity_int` - For Recommendations
- Calculated from `avg_sales_per_store` (robust median with 10th-90th percentile trim + P80 cap)
- Used in the final output as the recommended quantity
- This is what stores should order

### 2. `expected_units` - For ROI Filtering  
- Calculated from `median_amt` (simple median of peer sales)
- Used ONLY for ROI calculation: `margin_uplift = margin_per_unit * expected_units`
- This determines if the opportunity passes the $100 margin_uplift threshold

## Example from Debug Log

```
DEBUG ROI: store=41249, feature=休闲圆领T恤, cluster=2
  median_amt=$146.70, avg_sales_per_store=$99.00
  unit_price=$116.89, margin_rate=45.00%
  expected_units=2, expected_quantity_int=1    ← DIFFERENT!
  margin_per_unit=$52.60, margin_uplift=$105.20  ← Passes $100 threshold
  roi=81.82%, n_comparables=49
  PASS: roi>=30%? True, margin>=$100.0? True, comp>=10? True
  APPROVED!
```

**Key Insight:**
- `expected_units = 2` (from median_amt $146.70 / unit_price $116.89)
- `expected_quantity_int = 1` (from avg_sales_per_store $99.00 / unit_price $116.89)
- `margin_uplift = $52.60 * 2 = $105.20` → **PASSES** $100 threshold
- But if we used `expected_quantity_int`: `$52.60 * 1 = $52.60` → **FAILS**

## Why This Matters

When `median_amt > avg_sales_per_store`:
- ROI calculation uses higher quantity (`expected_units`)
- This inflates `margin_uplift`
- More opportunities pass the $100 threshold
- Result: 1,388 opportunities instead of 898

## Refactored Code Issue

Our refactored code uses `recommended_quantity` for BOTH:
1. The output recommendation ✅ Correct
2. The ROI calculation ❌ **Wrong - should use different value!**

## Fix Required

The `ROICalculator` needs to:
1. Calculate `expected_units` from median peer sales (not robust median)
2. Use `expected_units` for `margin_uplift` calculation
3. Keep `recommended_quantity` for the output

## Legacy Code Flow (lines 1002-1007)

```python
# For ROI calculation - uses simple median
median_amt = pd.to_numeric(comp.get(CURRENT_CONFIG['sales_column']), errors='coerce').median()
if pd.isna(median_amt):
    median_amt = avg_sales_per_store
expected_units = int(max(1.0, np.ceil((median_amt * SCALING_FACTOR) / max(1e-6, unit_price))))

# Calculate ROI metrics
margin_per_unit = unit_price - unit_cost
margin_uplift = margin_per_unit * expected_units  # Uses expected_units, not expected_quantity_int!
```

## Impact

- **Current refactored:** 898 opportunities (using recommended_quantity for ROI)
- **Legacy:** 1,388 opportunities (using expected_units for ROI)
- **Difference:** 490 opportunities (35% fewer)

All 490 filtered opportunities have `margin_uplift < $100` when calculated with `recommended_quantity`, but would have `margin_uplift >= $100` if calculated with `expected_units`.

---

**Next Step:** Update `ROICalculator` to calculate `expected_units` separately and use it for ROI filtering while keeping `recommended_quantity` for output.
