# ROI Filtering Analysis & Re-engineering Proposal

**Date:** 2025-11-07  
**Status:** Analysis Complete - Awaiting Decision  
**Impact:** High - Affects 1,388 opportunities and $100+ threshold filtering

---

## Executive Summary

The legacy ROI filtering logic is **fundamentally flawed** due to:
1. **Dual-quantity calculation** that inflates margin_uplift artificially
2. **Extreme sensitivity to rounding** (failing by cents, not dollars)
3. **Inconsistent business logic** (uses different values for ROI vs recommendations)
4. **Arbitrary threshold effects** caused by the `ceil()` function

**Recommendation:** Re-engineer the filtering to use consistent, business-aligned logic rather than replicating the broken legacy behavior.

---

## Part 1: Legacy Filtering Logic (What It Does)

### Overview

The legacy code calculates ROI metrics using **TWO different quantities**:
1. **`expected_quantity_int`** - Used for the final recommendation output
2. **`expected_units`** - Used ONLY for ROI filtering calculations

This dual-quantity approach creates artificial inflation of `margin_uplift`, allowing more opportunities to pass the $100 threshold.

### Detailed Legacy Flow

#### Step 1: Calculate `expected_quantity_int` (For Recommendations)

**Location:** Legacy line ~920-930

```python
# Calculate robust median with 10th-90th percentile trim + P80 cap
peer_sales = sales_df[sales_df['str_code'].isin(cluster_stores)]['sal_amt']
p10 = peer_sales.quantile(0.10)
p90 = peer_sales.quantile(0.90)
trimmed = peer_sales[(peer_sales >= p10) & (peer_sales <= p90)]
robust_median = trimmed.median()

# Cap at P80 for conservatism
p80 = peer_sales.quantile(0.80)
avg_sales_per_store = min(robust_median, p80)

# Calculate quantity
expected_quantity_int = int(max(1.0, np.ceil(avg_sales_per_store / unit_price)))
```

**Purpose:** Conservative recommendation for stores to order  
**Output:** Used in final CSV as `recommended_quantity`

#### Step 2: Calculate `expected_units` (For ROI Filtering)

**Location:** Legacy line 1002-1005

```python
# Calculate SIMPLE median (no trimming, no capping)
median_amt = pd.to_numeric(comp.get('sal_amt'), errors='coerce').median()
if pd.isna(median_amt):
    median_amt = avg_sales_per_store

# Calculate expected units for ROI
expected_units = int(max(1.0, np.ceil((median_amt * SCALING_FACTOR) / max(1e-6, unit_price))))
```

**Purpose:** Calculate ROI metrics for filtering  
**Output:** Used ONLY for `margin_uplift` and `roi` calculations

#### Step 3: Calculate ROI Metrics Using `expected_units`

**Location:** Legacy line 1006-1009

```python
margin_per_unit = unit_price - unit_cost
margin_uplift = margin_per_unit * expected_units  # Uses expected_units, NOT expected_quantity_int!
investment_required_cost = expected_units * unit_cost
roi_value = (margin_uplift / investment_required_cost) if investment_required_cost > 0 else 0.0
```

#### Step 4: Apply ROI Filters

**Location:** Legacy line 1021-1023

```python
if not (roi_value >= ROI_MIN_THRESHOLD and 
        margin_uplift >= MIN_MARGIN_UPLIFT and 
        n_comparables >= MIN_COMPARABLES):
    continue  # Filter out
```

**Thresholds:**
- `ROI_MIN_THRESHOLD = 0.30` (30%)
- `MIN_MARGIN_UPLIFT = 100.0` ($100)
- `MIN_COMPARABLES = 10` (stores)

### Why This Is Problematic

#### Problem 1: Inconsistent Quantities

**Example:**
```
median_amt = $146.70 (simple median)
avg_sales_per_store = $99.00 (robust median with P80 cap)
unit_price = $116.89

expected_units = ceil(146.70 / 116.89) = ceil(1.255) = 2
expected_quantity_int = ceil(99.00 / 116.89) = ceil(0.847) = 1

margin_per_unit = $52.60
margin_uplift = $52.60 * 2 = $105.20 → PASSES $100 threshold ✅

But the actual recommendation is only 1 unit, not 2!
```

**Business Impact:**
- The store is told to order **1 unit** (expected_quantity_int)
- But the ROI calculation assumes **2 units** (expected_units)
- The $105.20 margin_uplift is **inflated** - the real margin is only $52.60!

#### Problem 2: Extreme Rounding Sensitivity

**Example from Debug Output:**
```
margin_uplift = $99.96188620199143
Threshold = $100.00
Difference = -$0.03811 (3.8 cents)

Result: FILTERED OUT ❌

But if rounded to 0 decimals: $100 → PASSES ✅
```

**Business Impact:**
- Opportunities fail by **cents**, not dollars
- A $99.96 opportunity is rejected while a $100.05 opportunity is approved
- The difference is **meaningless** from a business perspective

#### Problem 3: The `ceil()` Amplification Effect

The `ceil()` function creates **discrete jumps** that amplify tiny differences:

```
Scenario A: median_amt / unit_price = 1.0001
  → ceil(1.0001) = 2
  → margin_uplift = $50 * 2 = $100 → PASS ✅

Scenario B: median_amt / unit_price = 0.9999
  → ceil(0.9999) = 1
  → margin_uplift = $50 * 1 = $50 → FAIL ❌
```

**Business Impact:**
- A difference of **0.0002** in the ratio (0.02%) causes a **$50 difference** in margin_uplift
- This is a **2,500x amplification** of the input difference!
- Opportunities near integer boundaries are arbitrarily approved/rejected

#### Problem 4: Misaligned Business Logic

**What the business wants:**
- Filter opportunities with **low expected return** on investment
- Ensure stores order **profitable quantities**
- Use **consistent metrics** for evaluation and recommendation

**What the legacy code does:**
- Uses **inflated quantities** for ROI calculation
- Recommends **different quantities** than what was evaluated
- Creates **artificial threshold effects** due to rounding

---

## Part 2: Proposed Sensible Filtering (What It Should Do)

### Core Principle: Consistency

**Use the SAME quantity for both ROI calculation and recommendations.**

If we recommend a store order 1 unit, the ROI should be calculated based on 1 unit, not 2.

### Proposed Logic

#### Option A: Use `expected_quantity_int` for Everything (Conservative)

**Advantages:**
- ✅ Consistent with actual recommendations
- ✅ Conservative approach (uses P80 cap)
- ✅ No artificial inflation of margin_uplift
- ✅ ROI reflects actual expected return

**Disadvantages:**
- ❌ May filter out more opportunities (lower margin_uplift)
- ❌ More conservative than legacy (fewer opportunities)

**Expected Impact:**
- Opportunity count: ~900-1,000 (vs 1,388 legacy)
- All opportunities have **realistic ROI** based on recommended quantities

#### Option B: Use `expected_units` for Everything (Aggressive)

**Advantages:**
- ✅ Consistent calculation throughout
- ✅ More opportunities approved (higher quantities)
- ✅ Closer to legacy count

**Disadvantages:**
- ❌ Recommends higher quantities than conservative approach
- ❌ May over-recommend to stores
- ❌ Less aligned with business risk tolerance

**Expected Impact:**
- Opportunity count: ~1,300-1,400 (similar to legacy)
- Recommendations may be **too aggressive** for some stores

#### Option C: Adjust Threshold to Match Business Intent (Recommended)

**Approach:**
1. Use `expected_quantity_int` for **both** ROI and recommendations (consistency)
2. **Lower the margin_uplift threshold** to compensate for conservative quantities
3. Add **minimum ROI percentage** as primary filter (e.g., 30%)
4. Use **margin_uplift as secondary filter** (e.g., $50 instead of $100)

**Advantages:**
- ✅ Fully consistent logic
- ✅ Threshold reflects actual business risk tolerance
- ✅ ROI percentage is more meaningful than absolute margin
- ✅ Reduces rounding sensitivity

**Disadvantages:**
- ❌ Requires business stakeholder input on new thresholds
- ❌ Changes opportunity count (needs validation)

**Expected Impact:**
- Opportunity count: ~1,200-1,400 (tunable via threshold)
- All opportunities have **consistent, realistic metrics**

### Recommended Thresholds (Option C)

```python
# Primary filter: ROI percentage (already in place)
ROI_MIN_THRESHOLD = 0.30  # 30% - Keep as-is

# Secondary filter: Margin uplift (REDUCE from $100 to $50)
MIN_MARGIN_UPLIFT = 50.0  # $50 - More realistic for 1-2 unit orders

# Tertiary filter: Comparables (keep as-is)
MIN_COMPARABLES = 10  # 10 stores - Ensures statistical validity
```

**Rationale:**
- **30% ROI** ensures profitability regardless of absolute margin
- **$50 margin** is realistic for 1-2 unit recommendations
- **10 comparables** ensures we have enough data for confidence

### Handling Rounding Sensitivity

**Proposed: Round margin_uplift to nearest dollar before comparison**

```python
# Instead of:
if margin_uplift >= MIN_MARGIN_UPLIFT:
    approve()

# Use:
margin_uplift_rounded = round(margin_uplift, 0)  # Round to nearest dollar
if margin_uplift_rounded >= MIN_MARGIN_UPLIFT:
    approve()
```

**Rationale:**
- Eliminates failures by cents
- Business doesn't care about $99.96 vs $100.05
- Reduces arbitrary threshold effects

---

## Part 3: Implementation Changes

### Change 1: Use Single Quantity for All Calculations

**Current (Legacy Replication):**
```python
# In opportunity_identifier.py
median_sales = self._calculate_median_sales(...)  # Simple median
expected_sales = self._calculate_expected_sales(...)  # Robust median

opportunities.append({
    'median_sales': median_sales,  # For ROI
    'recommended_quantity': quantity,  # For output
})

# In roi_calculator.py
enriched['expected_units'] = enriched.apply(
    lambda row: int(max(1.0, np.ceil(row['median_sales'] / row['unit_price']))),
    axis=1
)
enriched['margin_uplift'] = enriched['margin_per_unit'] * enriched['expected_units']
```

**Proposed (Consistent Logic):**
```python
# In opportunity_identifier.py
expected_sales = self._calculate_expected_sales(...)  # Robust median only
quantity = self._calculate_quantity(expected_sales, unit_price)

opportunities.append({
    'recommended_quantity': quantity,  # Use for EVERYTHING
})

# In roi_calculator.py
# Use recommended_quantity directly - no separate expected_units
enriched['margin_uplift'] = enriched['margin_per_unit'] * enriched['recommended_quantity']
enriched['investment_required'] = enriched['unit_cost'] * enriched['recommended_quantity']
```

### Change 2: Adjust Margin Uplift Threshold

**Current:**
```python
# In config.py
min_margin_uplift: float = 100.0  # $100 threshold
```

**Proposed:**
```python
# In config.py
min_margin_uplift: float = 50.0  # $50 threshold (more realistic for 1-2 units)
```

### Change 3: Add Rounding to Threshold Comparison

**Current:**
```python
# In roi_calculator.py
filtered = filtered[
    filtered['margin_uplift'] >= self.config.min_margin_uplift
].copy()
```

**Proposed:**
```python
# In roi_calculator.py
# Round to nearest dollar before comparison
filtered['margin_uplift_rounded'] = filtered['margin_uplift'].round(0)
filtered = filtered[
    filtered['margin_uplift_rounded'] >= self.config.min_margin_uplift
].copy()
```

### Change 4: Remove `median_sales` Calculation

**Files to Modify:**
1. `src/components/missing_category/opportunity_identifier.py`
   - Remove `_calculate_median_sales()` method
   - Remove `median_sales` from opportunity dictionary

2. `src/components/missing_category/roi_calculator.py`
   - Remove `expected_units` calculation
   - Use `recommended_quantity` directly for all calculations

### Change 5: Update Documentation

**Files to Update:**
1. `docs/step_refactorings/step7/REFACTORING_OVERVIEW.md`
   - Document the consistent quantity approach
   - Explain threshold adjustments

2. `src/components/missing_category/config.py`
   - Add comments explaining threshold rationale
   - Document the change from legacy

3. `src/components/missing_category/roi_calculator.py`
   - Add docstring explaining consistent calculation approach

---

## Part 4: Migration Strategy

### Phase 1: Analysis & Validation (Current)

**Status:** ✅ Complete

- [x] Understand legacy logic
- [x] Identify problems with dual-quantity approach
- [x] Document rounding sensitivity
- [x] Propose sensible alternatives

### Phase 2: Stakeholder Review (Next)

**Actions Required:**

1. **Present findings to business stakeholders**
   - Show examples of inflated margin_uplift
   - Demonstrate rounding sensitivity issues
   - Explain inconsistency between ROI and recommendations

2. **Get approval for proposed changes**
   - Confirm threshold adjustments ($50 vs $100)
   - Validate expected opportunity count change
   - Agree on rounding approach

3. **Define success criteria**
   - What opportunity count is acceptable?
   - What ROI metrics should we target?
   - How do we validate the new logic?

### Phase 3: Implementation (After Approval)

**Estimated Effort:** 4-6 hours

1. **Remove dual-quantity logic** (2 hours)
   - Update `opportunity_identifier.py`
   - Update `roi_calculator.py`
   - Remove `median_sales` calculation

2. **Adjust thresholds** (1 hour)
   - Update `config.py`
   - Add rounding logic

3. **Update tests** (2 hours)
   - Modify expected opportunity counts
   - Update ROI calculation tests
   - Add rounding sensitivity tests

4. **Update documentation** (1 hour)
   - Document changes in REFACTORING_OVERVIEW.md
   - Update inline comments
   - Add migration notes

### Phase 4: Validation (After Implementation)

**Validation Steps:**

1. **Run refactored code with new logic**
   ```bash
   python src/step7_missing_category_rule_refactored.py \
     --target-yyyymm 202510 --target-period A \
     --data-dir output --output-dir output
   ```

2. **Compare opportunity counts**
   - Expected: ~1,200-1,400 opportunities (with $50 threshold)
   - Validate: All have consistent ROI metrics

3. **Spot-check opportunities**
   - Verify `margin_uplift` matches `margin_per_unit * recommended_quantity`
   - Confirm no artificial inflation
   - Check rounding behavior near threshold

4. **Business review**
   - Sample 10-20 opportunities for business validation
   - Confirm recommendations are sensible
   - Validate ROI metrics are realistic

---

## Part 5: Risk Assessment

### Risks of Keeping Legacy Logic

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Inflated ROI metrics** | High - Business makes decisions on false data | Certain | Re-engineer with consistent logic |
| **Arbitrary filtering** | Medium - Good opportunities rejected by cents | High | Add rounding to threshold comparison |
| **Inconsistent recommendations** | High - Stores confused by mismatched metrics | Certain | Use single quantity for all calculations |
| **Technical debt** | Medium - Future developers confused by dual logic | High | Document and simplify |

### Risks of Re-engineering

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Opportunity count change** | Medium - Business expects ~1,388 opportunities | High | Adjust threshold to compensate |
| **Stakeholder pushback** | Low - May resist change from "working" system | Medium | Present clear evidence of problems |
| **Implementation bugs** | Low - New logic may have edge cases | Low | Comprehensive testing |
| **Validation effort** | Low - Requires business review | Medium | Plan validation sessions |

### Recommendation

**Re-engineer the filtering logic.** The risks of keeping the legacy approach far outweigh the risks of fixing it:

1. **Data integrity** - Current metrics are misleading
2. **Business trust** - Inconsistent logic undermines confidence
3. **Maintainability** - Dual-quantity approach is confusing
4. **Correctness** - Rounding sensitivity is arbitrary

---

## Part 6: Decision Matrix

### Option Comparison

| Criterion | Legacy (Current) | Option A (Conservative) | Option B (Aggressive) | Option C (Recommended) |
|-----------|------------------|-------------------------|----------------------|------------------------|
| **Consistency** | ❌ Dual quantities | ✅ Single quantity | ✅ Single quantity | ✅ Single quantity |
| **ROI Accuracy** | ❌ Inflated | ✅ Accurate | ✅ Accurate | ✅ Accurate |
| **Rounding Sensitivity** | ❌ Extreme | ⚠️ Still present | ⚠️ Still present | ✅ Mitigated |
| **Opportunity Count** | 1,388 | ~900-1,000 | ~1,300-1,400 | ~1,200-1,400 (tunable) |
| **Business Alignment** | ❌ Misaligned | ✅ Conservative | ⚠️ Aggressive | ✅ Balanced |
| **Implementation Effort** | 0 (done) | Low | Low | Medium |
| **Stakeholder Buy-in** | ✅ Familiar | ⚠️ May resist | ⚠️ May resist | ✅ Evidence-based |

### Recommended Path Forward

**Implement Option C with stakeholder approval:**

1. **Present this analysis** to business stakeholders
2. **Get agreement** on threshold adjustments
3. **Implement changes** with comprehensive testing
4. **Validate results** with business review
5. **Document migration** for future reference

---

## Appendix A: Code Examples

### Legacy Dual-Quantity Calculation

```python
# Step 1: Calculate conservative quantity for recommendation
avg_sales_per_store = calculate_robust_median_with_p80_cap(peer_sales)
expected_quantity_int = int(max(1.0, np.ceil(avg_sales_per_store / unit_price)))

# Step 2: Calculate aggressive quantity for ROI
median_amt = peer_sales.median()  # Simple median, no capping
expected_units = int(max(1.0, np.ceil(median_amt / unit_price)))

# Step 3: Use different quantities for different purposes
margin_uplift = margin_per_unit * expected_units  # Uses aggressive quantity
recommended_quantity = expected_quantity_int  # Output uses conservative quantity

# Result: margin_uplift is inflated relative to actual recommendation!
```

### Proposed Consistent Calculation

```python
# Step 1: Calculate quantity ONCE using robust method
expected_sales = calculate_robust_median_with_p80_cap(peer_sales)
recommended_quantity = int(max(1.0, np.ceil(expected_sales / unit_price)))

# Step 2: Use SAME quantity for everything
margin_uplift = margin_per_unit * recommended_quantity
investment_required = unit_cost * recommended_quantity
roi = margin_uplift / investment_required

# Step 3: Apply threshold with rounding
margin_uplift_rounded = round(margin_uplift, 0)
if (roi >= 0.30 and 
    margin_uplift_rounded >= 50.0 and 
    n_comparables >= 10):
    approve_opportunity()

# Result: Consistent, accurate metrics throughout!
```

---

## Appendix B: Real-World Examples

### Example 1: Inflated Margin Uplift

**Legacy Calculation:**
```
Store: 41249, Feature: 休闲圆领T恤, Cluster: 2

median_amt = $146.70 (simple median)
avg_sales_per_store = $99.00 (robust median with P80 cap)
unit_price = $116.89

expected_units = ceil(146.70 / 116.89) = 2
expected_quantity_int = ceil(99.00 / 116.89) = 1

margin_per_unit = $52.60
margin_uplift = $52.60 * 2 = $105.20 ✅ PASSES $100 threshold

Recommendation to store: Order 1 unit
ROI calculation assumes: 2 units
Actual margin if store orders 1 unit: $52.60 (NOT $105.20!)
```

**Proposed Calculation:**
```
Store: 41249, Feature: 休闲圆领T恤, Cluster: 2

expected_sales = $99.00 (robust median with P80 cap)
unit_price = $116.89
recommended_quantity = ceil(99.00 / 116.89) = 1

margin_per_unit = $52.60
margin_uplift = $52.60 * 1 = $52.60
margin_uplift_rounded = $53

With $100 threshold: ❌ FAILS
With $50 threshold: ✅ PASSES

Recommendation to store: Order 1 unit
ROI calculation assumes: 1 unit (CONSISTENT!)
Actual margin if store orders 1 unit: $52.60 (ACCURATE!)
```

### Example 2: Rounding Sensitivity

**Legacy Calculation:**
```
Store: 33721, Feature: 休闲POLO, Cluster: 0

margin_uplift = $99.96188620199143
Threshold = $100.00
Difference = -$0.03811 (3.8 cents)

Result: ❌ FILTERED OUT

Business impact: Opportunity with 30% ROI rejected over 4 cents!
```

**Proposed Calculation:**
```
Store: 33721, Feature: 休闲POLO, Cluster: 0

margin_uplift = $99.96188620199143
margin_uplift_rounded = $100.00
Threshold = $100.00

Result: ✅ APPROVED

Business impact: Sensible threshold behavior, no arbitrary rejections
```

---

## Conclusion

The legacy ROI filtering logic is **fundamentally broken** and should be re-engineered rather than replicated. The proposed changes will:

1. ✅ **Eliminate artificial inflation** of margin_uplift
2. ✅ **Ensure consistency** between ROI calculation and recommendations
3. ✅ **Reduce rounding sensitivity** through dollar-level rounding
4. ✅ **Align with business intent** through adjusted thresholds
5. ✅ **Improve maintainability** by simplifying the logic

**Next Step:** Present this analysis to stakeholders and get approval for Option C implementation.
