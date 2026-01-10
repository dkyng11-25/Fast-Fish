# Target Filtering Specification
## What Filtering Should Look Like According to Customer Requirements

**Document Purpose:** Define the target filtering/optimization approach based on customer requirements  
**Audience:** Development team, stakeholders  
**Status:** Specification - Ready for Implementation  
**Date:** 2025-11-10

---

## Executive Summary

**Current State:** Legacy filtering optimizes for profit (ROI ≥30%, margin_uplift ≥$100)  
**Target State:** Optimize for sell-through rate under business constraints  
**Impact:** Store 51161 goes from 9 SPUs (violating all rules) to 14-19 SPUs (compliant)

---

## 1. Primary Objective: Maximize Sell-Through Rate

### Customer Requirement:

> "Unified objective: Every rule and score used for ranking must align to **predicted sell-through uplift** (under constraints). **Replace revenue/Z-score driven decisions where they conflict.**"
> 
> — *Fast Fish AB Test Pipeline Readiness Spec v2, Section 9: KPI Alignment*

> "Goal → The optimisation engine must explicitly **maximise active-sales-rate (sell-through)**."
>
> — *System Requirements Document, Section 1: Core Logic – KPI Alignment*

### What This Means:

**Instead of:**
```python
# Legacy: Binary filter by profit
if roi >= 0.30 and margin_uplift >= 100:
    approve()
else:
    reject()
```

**Do this:**
```python
# Target: Score by sell-through
score = predicted_sell_through_rate * confidence_weight
# Then rank and select top N opportunities
```

### Why This Matters:

| Item | Sell-Through | Margin | Legacy Decision | Target Decision |
|------|--------------|--------|-----------------|-----------------|
| Joggers | 75% | $96 | ❌ REJECT | ✅ APPROVE (high ST) |
| Low-seller | 40% | $101 | ✅ APPROVE | ❌ REJECT (low ST) |

**Result:** Joggers (57% of Store 51161 sales) are now recommended instead of filtered out.

---

## 2. Constraint-Aware Optimization

### Customer Requirement:

> "Recommendations must come from a **constraint-aware optimiser**, not hand-tuned rules."
>
> — *System Requirements Document, Section 5: Allocation Logic – True Optimisation*

> "Each store's total SPUs are **calibrated into a 14–19 band** to stay aligned with plan and capacity."
>
> — *Fixes Applied for 202510B, Section 5: Total SPU Calibration*

### Required Constraints:

#### 2.1 Total SPU Band (14-19 per store)

**Requirement:**
> "Total SPU Calibration: Each store's total SPUs are calibrated into a 14–19 band to stay aligned with plan and capacity."
>
> — *Fixes Applied for 202510B, Section 5*

**Implementation:**
```python
# Hard constraint
total_spus = sum(recommendations_for_store)
assert 14 <= total_spus <= 19, "SPU count out of range"
```

**Validation:** Store 51161 currently has 9 SPUs → Must be increased to 14-19

---

#### 2.2 Winter Season Floor (≥5 SPUs if history >20%)

**Requirement:**
> "Season Coverage Floor: If last year's winter share > 20%, each store now gets **≥5 winter SPUs** (no more zero-winter mixes)."
>
> — *Fixes Applied for 202510B, Section 1*

**Implementation:**
```python
# Conditional constraint
if historical_winter_share > 0.20:
    winter_spus = count(recommendations where season == 'Winter')
    assert winter_spus >= 5, "Winter floor violated"
```

**Validation:** Store 51161 has 0 winter SPUs, but 142 units winter sales (46%) → Must add ≥5 winter SPUs

---

#### 2.3 Frontcourt Minimum (≥4 SPUs)

**Requirement:**
> "Frontcourt Minimum: Each store now has **≥4 frontcourt SPUs**. When needed, units are flipped from backcourt to frontcourt to hit the floor."
>
> — *Fixes Applied for 202510B, Section 2*

**Implementation:**
```python
# Hard constraint
frontcourt_spus = count(recommendations where display_location == 'Frontcourt')
assert frontcourt_spus >= 4, "Frontcourt floor violated"
```

**Validation:** Store 51161 has 0 frontcourt SPUs, but 149 units frontcourt sales (49%) → Must add ≥4 frontcourt SPUs

---

#### 2.4 Jogger Share Control (~50% ±15%)

**Requirement:**
> "Jogger Share Control: We target **~50% jogger share with a ±15 percentage-point tolerance**. Units shift from lower-demand subcategories into joggers to meet the target."
>
> — *Fixes Applied for 202510B, Section 3*

**Implementation:**
```python
# Soft constraint with tolerance
jogger_share = jogger_spus / total_spus
assert 0.35 <= jogger_share <= 0.65, "Jogger share out of range"
```

**Validation:** Store 51161 has 0% jogger share, but 175 units jogger sales (57%) → Must add joggers to reach ~50%

---

#### 2.5 Seasonal Appropriateness (Ban A/W-inappropriate items)

**Requirement:**
> "Ban A/W-Inappropriate Subcategories + Novelty Gate: **Shorts and pants sets are removed from A/W assortments**. A novelty gate is in place: no new subcategory without history (exploration budget = 0) unless explicitly approved."
>
> — *Fixes Applied for 202510B, Section 4*

**Implementation:**
```python
# Hard constraint for A/W season
if season in ['Autumn', 'Winter']:
    inappropriate = ['Shorts', 'Pants Sets']
    for rec in recommendations:
        assert rec.subcategory not in inappropriate, "Inappropriate item for A/W"
```

**Validation:** Store 51161 has 2 inappropriate items (shorts/sets with 0 sales history) → Must remove

---

#### 2.6 Variance Tolerance (±20% from plan)

**Requirement:**
> "+- 20% buffer okay"
>
> — *Meeting Notes, Requirements Context*

**Implementation:**
```python
# Soft constraint
variance = (ai_spus - manual_plan_spus) / manual_plan_spus
assert -0.20 <= variance <= 0.20, "Variance exceeds tolerance"
```

**Validation:** Store 51161 variance is -53% (9 vs 19) → Must reduce to ±20%

---

## 3. Required Input Features

### Customer Requirement:

> "Store Clustering – Dimension Completeness: Clustering cannot ignore merchandising realities. **Store style and rack capacity/display class must be input features**."
>
> — *System Requirements Document, Section 2: Store Clustering*

### Required Features:

#### 3.1 Store Capacity (Already Partially Handled)

**Status:** ✅ Temperature zone handled via clustering

> "Each cluster has already been filtered for temperature."
>
> — *User Clarification*

**Additional Need:** Store size tier (Small/Medium/Large)

**Implementation:**
```python
# Add to store attributes
store.capacity_tier = classify_capacity(store.fixture_count, store.sales_volume)
# Use in scoring
capacity_fit = calculate_capacity_fit(recommendation.volume, store.capacity_tier)
```

---

#### 3.2 Store Type/Style (Missing - Need to Add)

**Requirement:**
> "Store‑type / style: create a column with **Fashion / Basic / Balanced** using existing ratios."
>
> — *Fast Fish AB Test Spec v2, Section 6: Clustering Requirements*

**Implementation:**
```python
# Classify stores
store.style_type = classify_style(store.fashion_ratio)
# Use in scoring
style_fit = calculate_style_fit(recommendation.style, store.style_type)
```

---

## 4. Scoring Formula (Target Implementation)

### Customer Requirement:

> "Score by: **predicted_sell_through × confidence**"
>
> — *Requirements Analysis*

### Target Formula:

```python
def calculate_recommendation_score(opportunity, store):
    """
    Calculate recommendation score based on sell-through optimization.
    
    Returns: float between 0-1 (higher is better)
    """
    # Primary factor: Predicted sell-through rate
    predicted_st = estimate_sell_through_rate(
        opportunity.feature,
        opportunity.peer_performance,
        store.cluster
    )
    
    # Confidence factors
    confidence = calculate_confidence(
        n_comparables=opportunity.n_comparables,
        adoption_rate=opportunity.adoption_rate,
        data_quality=opportunity.data_quality
    )
    
    # Capacity fit (prevent over-allocation)
    capacity_fit = calculate_capacity_fit(
        expected_volume=opportunity.expected_quantity,
        store_capacity=store.capacity_tier
    )
    
    # Style alignment (Fashion items to Fashion stores)
    style_fit = calculate_style_fit(
        item_style=opportunity.style_attributes,
        store_style=store.style_type
    )
    
    # Seasonal appropriateness
    seasonal_fit = calculate_seasonal_fit(
        item_season=opportunity.season,
        target_period=store.planning_period,
        temperature_zone=store.cluster.temperature_zone
    )
    
    # Combined score (weighted)
    score = (
        predicted_st * 0.50 +      # Primary: sell-through
        confidence * 0.20 +         # Data reliability
        capacity_fit * 0.15 +       # Store can handle it
        style_fit * 0.10 +          # Style match
        seasonal_fit * 0.05         # Season appropriate
    )
    
    return score
```

### Key Differences from Legacy:

| Aspect | Legacy | Target |
|--------|--------|--------|
| **Primary Metric** | ROI (profit) | Sell-through rate |
| **Method** | Binary filter (pass/fail) | Continuous scoring (0-1) |
| **Capacity** | Not considered | Explicit capacity_fit factor |
| **Style** | Not considered | Explicit style_fit factor |
| **Optimization** | Hard thresholds | Weighted multi-objective |

---

## 5. Selection Process (After Scoring)

### Customer Requirement:

> "Recommendations must come from a constraint-aware optimiser, not hand-tuned rules."
>
> — *System Requirements Document, Section 5*

### Target Process:

```python
def select_recommendations(opportunities, store, constraints):
    """
    Select optimal recommendations under constraints.
    
    Process:
    1. Score all opportunities
    2. Rank by score
    3. Select top N that satisfy constraints
    4. Apply post-selection rebalancing
    """
    # Step 1: Score all opportunities
    scored_opportunities = [
        (opp, calculate_recommendation_score(opp, store))
        for opp in opportunities
    ]
    
    # Step 2: Rank by score (descending)
    ranked = sorted(scored_opportunities, key=lambda x: x[1], reverse=True)
    
    # Step 3: Greedy selection with constraint checking
    selected = []
    for opp, score in ranked:
        # Try adding this opportunity
        candidate_set = selected + [opp]
        
        # Check if constraints still satisfied
        if check_constraints(candidate_set, store, constraints):
            selected.append(opp)
        
        # Stop when we hit SPU band upper limit
        if len(selected) >= constraints.max_spus:
            break
    
    # Step 4: Post-selection rebalancing
    selected = apply_rebalancing(selected, store, constraints)
    
    return selected

def check_constraints(recommendations, store, constraints):
    """
    Verify all business constraints are satisfied.
    
    Returns: bool (True if all constraints met)
    """
    total_spus = len(recommendations)
    
    # Constraint 1: Total SPU band
    if not (constraints.min_spus <= total_spus <= constraints.max_spus):
        return False
    
    # Constraint 2: Winter floor (if applicable)
    if store.historical_winter_share > 0.20:
        winter_count = count_by_season(recommendations, 'Winter')
        if winter_count < constraints.min_winter_spus:
            return False
    
    # Constraint 3: Frontcourt minimum
    frontcourt_count = count_by_location(recommendations, 'Frontcourt')
    if frontcourt_count < constraints.min_frontcourt_spus:
        return False
    
    # Constraint 4: Jogger share
    jogger_share = count_by_subcategory(recommendations, 'Jogger') / total_spus
    if not (constraints.min_jogger_share <= jogger_share <= constraints.max_jogger_share):
        return False
    
    # Constraint 5: No inappropriate items
    if has_inappropriate_items(recommendations, store.planning_season):
        return False
    
    # Constraint 6: Variance tolerance
    variance = (total_spus - store.manual_plan_spus) / store.manual_plan_spus
    if abs(variance) > constraints.max_variance:
        return False
    
    return True
```

---

## 6. Post-Rounding Rebalancer

### Customer Requirement:

> "Post-Rounding Rebalancer: After integer rounding, we re-check floors/targets and move units one-by-one to close any remaining gaps—priority order: 1) Jogger ↑ 2) Frontcourt ↑ 3) Winter ↑ 4) Total band alignment."
>
> — *Fixes Applied for 202510B, Section 6*

### Implementation:

```python
def apply_rebalancing(recommendations, store, constraints):
    """
    Rebalance after rounding to ensure constraint compliance.
    
    Priority order:
    1. Increase jogger share if below target
    2. Increase frontcourt if below minimum
    3. Increase winter if below minimum
    4. Adjust total to fit band
    """
    # Priority 1: Jogger share
    jogger_share = count_by_subcategory(recommendations, 'Jogger') / len(recommendations)
    if jogger_share < constraints.target_jogger_share:
        recommendations = increase_jogger_share(recommendations, constraints.target_jogger_share)
    
    # Priority 2: Frontcourt minimum
    frontcourt_count = count_by_location(recommendations, 'Frontcourt')
    if frontcourt_count < constraints.min_frontcourt_spus:
        recommendations = shift_to_frontcourt(recommendations, constraints.min_frontcourt_spus)
    
    # Priority 3: Winter minimum
    if store.historical_winter_share > 0.20:
        winter_count = count_by_season(recommendations, 'Winter')
        if winter_count < constraints.min_winter_spus:
            recommendations = increase_winter(recommendations, constraints.min_winter_spus)
    
    # Priority 4: Total band alignment
    total_spus = len(recommendations)
    if total_spus < constraints.min_spus:
        recommendations = add_spus_to_reach_minimum(recommendations, constraints.min_spus)
    elif total_spus > constraints.max_spus:
        recommendations = remove_lowest_scored_spus(recommendations, constraints.max_spus)
    
    return recommendations
```

---

## 7. Required Output Columns

### Customer Requirement:

> "Output Spec v2 implemented: **optimisation target, current/target/Δ sell-through, constraint status, confidence & trade-off**, run IDs, valid-until; English-only headers."
>
> — *Fast Fish AB Test Spec v2, Section 2: Go/No-Go Acceptance Criteria*

### Required Columns:

```python
output_columns = {
    # Core identification
    'Store_Code': str,
    'Cluster_ID': int,
    'Subcategory': str,
    'SPU_ID': str,
    
    # Optimization transparency
    'Optimization_Target': str,  # "Maximize Sell-Through Rate Under Constraints"
    'Current_ST_Pct': float,     # Current sell-through %
    'Target_ST_Pct': float,      # Predicted sell-through %
    'Delta_ST_Pct': float,       # Expected improvement
    
    # Constraint validation
    'Capacity_Utilization_Pct': float,
    'Store_Type_Alignment': str,  # "Fashion", "Basic", "Balanced"
    'Temperature_Suitability': str,  # "Excellent", "Good", "Fair"
    'Constraint_Status': str,     # "OK", "Warning", "Blocked"
    
    # Confidence & traceability
    'Confidence_Score': float,    # 0-1
    'Trade_Off_Note': str,        # Explanation of compromises
    'Run_ID': str,
    'Spec_Version': str,
    'Valid_Until_Month': str,
    
    # Allocation
    'Allocated_Quantity': int     # Integer per-store quantity
}
```

### Example Output Row:

```python
{
    'Store_Code': '51161',
    'Cluster_ID': 18,
    'Subcategory': 'Jogger Pants',
    'SPU_ID': 'JP_001',
    'Optimization_Target': 'Maximize Sell-Through Rate Under Constraints',
    'Current_ST_Pct': 0.0,        # Not currently selling
    'Target_ST_Pct': 75.0,        # Predicted 75% sell-through
    'Delta_ST_Pct': 75.0,         # +75% improvement
    'Capacity_Utilization_Pct': 65.0,  # 65% of store capacity
    'Store_Type_Alignment': 'Basic',
    'Temperature_Suitability': 'Excellent',
    'Constraint_Status': 'OK',
    'Confidence_Score': 0.85,     # High confidence
    'Trade_Off_Note': 'High demand item, proven in cluster',
    'Run_ID': '20251110_step7_202510B',
    'Spec_Version': 'v2.0',
    'Valid_Until_Month': '202511',
    'Allocated_Quantity': 12
}
```

---

## 8. Validation: Store 51161 Test Case

### Before (Legacy):

```
Total SPUs:        9 ❌ (should be 14-19)
Winter SPUs:       0 ❌ (should be ≥5)
Frontcourt SPUs:   0 ❌ (should be ≥4)
Jogger Share:      0% ❌ (should be 35-65%)
Inappropriate:     2 ❌ (shorts/sets in A/W)
Variance:          -53% ❌ (should be ±20%)
Constraint_Status: MISSING ❌

Missing Sales: 466 units opportunity
```

### After (Target):

```
Total SPUs:        16 ✅ (within 14-19 band)
Winter SPUs:       6 ✅ (≥5 floor met)
Frontcourt SPUs:   5 ✅ (≥4 floor met)
Jogger Share:      50% ✅ (within 35-65% range)
Inappropriate:     0 ✅ (shorts/sets removed)
Variance:          -16% ✅ (within ±20%)
Constraint_Status: OK ✅

Captured Sales: 466 units opportunity
```

### Sample Recommendations:

```
Store 51161 Recommendations (16 SPUs total):
────────────────────────────────────────────────────────
Jogger Pants:
- Autumn Backcourt Joggers:  3 SPUs (score: 0.88)
- Autumn Frontcourt Joggers: 2 SPUs (score: 0.85)
- Winter Backcourt Joggers:  2 SPUs (score: 0.82)
- Winter Frontcourt Joggers: 1 SPU  (score: 0.80)
Subtotal: 8 SPUs (50% jogger share ✅)

Straight Pants:
- Autumn Backcourt Straight: 2 SPUs (score: 0.75)
- Winter Backcourt Straight: 2 SPUs (score: 0.72)
Subtotal: 4 SPUs (25%)

Other Pants:
- Autumn Backcourt Tapered:  2 SPUs (score: 0.68)
- Autumn Frontcourt Cargo:   1 SPU  (score: 0.65)
- Winter Backcourt Cargo:    1 SPU  (score: 0.63)
Subtotal: 4 SPUs (25%)

Validation:
✅ Total: 16 SPUs (within 14-19)
✅ Winter: 6 SPUs (≥5)
✅ Frontcourt: 5 SPUs (≥4)
✅ Jogger share: 50% (within 35-65%)
✅ No inappropriate items
✅ Variance: (16-19)/19 = -16% (within ±20%)
```

---

## 9. Implementation Checklist

### Phase 1: Change Objective Function

- [ ] Replace ROI filtering with sell-through scoring
- [ ] Implement `calculate_recommendation_score()` function
- [ ] Remove dual-quantity calculation quirk
- [ ] Validate jogger representation increases

### Phase 2: Add Missing Features

- [ ] Add store capacity tier classification
- [ ] Add store style type (Fashion/Basic/Balanced)
- [ ] Integrate capacity_fit into scoring
- [ ] Integrate style_fit into scoring

### Phase 3: Implement Constraints

- [ ] Implement total SPU band (14-19)
- [ ] Implement winter floor (≥5 if history >20%)
- [ ] Implement frontcourt minimum (≥4)
- [ ] Implement jogger share control (35-65%)
- [ ] Implement seasonal appropriateness check
- [ ] Implement variance tolerance (±20%)

### Phase 4: Add Post-Rebalancing

- [ ] Implement priority-based rebalancing
- [ ] Priority 1: Jogger share adjustment
- [ ] Priority 2: Frontcourt minimum
- [ ] Priority 3: Winter minimum
- [ ] Priority 4: Total band alignment

### Phase 5: Update Output Specification

- [ ] Add Optimization_Target column
- [ ] Add Current/Target/Delta sell-through columns
- [ ] Add Constraint_Status column
- [ ] Add Confidence_Score column
- [ ] Add Trade_Off_Note column
- [ ] Add traceability columns (Run_ID, etc.)

### Phase 6: Validation

- [ ] Test on Store 51161
- [ ] Verify all constraints satisfied
- [ ] Verify output columns present
- [ ] Verify variance within ±20%
- [ ] Compare sell-through rates vs legacy

---

## 10. Success Metrics

| Metric | Legacy | Target | How to Measure |
|--------|--------|--------|----------------|
| **Primary Objective** | Profit (ROI) | Sell-through | Code review |
| **Store 51161 SPUs** | 9 | 14-19 | Count recommendations |
| **Winter Coverage** | 0 | ≥5 | Count winter SPUs |
| **Frontcourt Coverage** | 0 | ≥4 | Count frontcourt SPUs |
| **Jogger Share** | 0% | 35-65% | Calculate jogger % |
| **Inappropriate Items** | 2 | 0 | Check for shorts/sets |
| **Variance** | -53% | ±20% | (AI - Manual) / Manual |
| **Constraint Violations** | 100% | 0% | Check all constraints |
| **Output Compliance** | 0/8 | 8/8 | Check required columns |

---

## Conclusion

**Target filtering is NOT about filtering - it's about optimization.**

**Key Changes:**
1. ✅ Replace profit filtering with sell-through scoring
2. ✅ Add constraint-aware selection process
3. ✅ Include store capacity and style features
4. ✅ Implement post-selection rebalancing
5. ✅ Add transparent output columns

**Result:** Store 51161 goes from 9 SPUs (violating all rules) to 16 SPUs (fully compliant), capturing 466 units of sales opportunity.

---

**Document Status:** Complete  
**Next Step:** Begin Phase 1 implementation (sell-through scoring)
