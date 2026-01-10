# Step 7 Validation Analysis - What Actually Happens

**Date:** 2025-11-07  
**Status:** BROKEN BUT MUST REPLICATE EXACTLY

## The Validation Process (As It Actually Works)

### Fast Fish Validator Behavior

The `SellThroughValidator` for Step 7 (Missing Category = ADD action):

**Input:**
- `current_spu_count = 0` (missing category)
- `recommended_spu_count = 1` (add 1 category)
- `action = 'ADD'`

**Calculation:**
- Current sell-through: 0% (0 SPUs)
- Predicted sell-through: ~50-60% (default performance for 1 SPU)
- Improvement: +50-60pp

**Approval Logic** (lines 297-310 in `sell_through_validator.py`):
1. Predicted ST >= 25%? YES (50% >= 25%) ✅
2. Improvement >= -10%? YES (+50pp >= -10pp) ✅
3. Result: **ALWAYS APPROVES**

### Legacy Approval Gates (Line 938-943)

```python
should_approve = (
    validator_ok and                                    # ALWAYS TRUE
    well_selling_row['stores_selling'] >= 5 and        # Feature-level check
    well_selling_row['pct_stores_selling'] >= 0.25 and # Feature-level check
    predicted_from_adoption >= 30                       # Feature-level check
)
```

**The Problem:**
- The validator ALWAYS returns True for Step 7
- The real filters are the last 3 conditions
- BUT these are checked at the FEATURE level, not OPPORTUNITY level
- So they don't explain why legacy creates fewer opportunities

## The Real Difference

Both versions:
- ✅ Identify same 2,246 well-selling features
- ✅ Apply same feature-level filters

But:
- ❌ Legacy creates 1,388 opportunities from those features
- ❌ Refactored creates 2,956 opportunities from those features

**Hypothesis:** There's additional filtering happening DURING opportunity creation that we're missing.

## What We Need to Do

**STOP trying to understand it. Just COPY it exactly.**

1. Copy the EXACT opportunity creation loop from legacy
2. Copy the EXACT validation logic from legacy
3. Copy the EXACT approval gates from legacy
4. Don't try to "fix" or "improve" anything
5. Replicate the broken validator behavior exactly

## Implementation Plan

1. **Remove our refactored opportunity identification logic**
2. **Copy the legacy loop structure exactly** (lines 790-1050)
3. **Copy the legacy validation calls exactly**
4. **Copy the legacy approval conditions exactly**
5. **Test and verify we get 1,388 opportunities**

---

**Key Insight:** The system is fundamentally broken, but it produces consistent results. Our job is to replicate those exact results, not to fix the system.
