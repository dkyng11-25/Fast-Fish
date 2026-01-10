# Requirements vs Reality: Gap Analysis
## What Should Happen vs What Actually Happens

**Document Purpose:** Side-by-side comparison of business requirements and legacy implementation  
**Audience:** Leadership, stakeholders, technical leads  
**Status:** Complete Analysis  
**Date:** 2025-11-07

---

## Executive Summary

**The Gap:** Legacy Step 7 implementation has fundamental misalignment with stated business requirements. While the core opportunity identification logic is sound, the filtering approach optimizes for the wrong objective and lacks required constraint enforcement.

**Impact:** Store 51161 receives 9 SPUs instead of required 14-19, missing 57% of sales (joggers), 46% of sales (winter), and 49% of sales (frontcourt).

**Recommendation:** Use refactoring to implement correctly, not replicate broken logic.

---

## Part 1: Business Requirements (What Should Happen)

### Source Documents:
- Fast Fish AB Test Pipeline Readiness Spec v2
- Fixes Applied for 202510B
- System Requirements Document

### 1.1 Primary Objective

**Requirement:**
> "Unified objective: Every rule and score used for ranking must align to **predicted sell-through uplift** (under constraints). **Replace revenue/Z-score driven decisions where they conflict.**"

**Translation:**
- Maximize how quickly products sell (sell-through rate)
- NOT how much profit they make
- Constraints ensure feasibility (capacity, appropriateness)

**Business Rationale:**
- High sell-through = customer satisfaction (products available when wanted)
- High sell-through = inventory efficiency (less markdown risk)
- High sell-through = operational simplicity (predictable replenishment)

---

### 1.2 Required Input Features

**Requirement (Section 6):**

| Feature | Purpose | Implementation |
|---------|---------|----------------|
| **Climate/Temperature Zone** | Match products to store climate | Already done at cluster level ✅ |
| **Store Type/Style** | Fashion/Basic/Balanced classification | Match product style to store style |
| **Capacity/Size Tier** | Small/Medium/Large store capacity | Prevent over-allocation |

**Business Rationale:**
- Temperature: Don't recommend winter coats to tropical stores
- Store Type: Fashion stores get trendy items, Basic stores get staples
- Capacity: Don't overwhelm small stores with too many SKUs

---

### 1.3 Required Constraints (Business Rules)

**Requirement (Section 7 & Fixes Document):**

```
Hard Constraints (Must be enforced):
┌─────────────────────────────────────────────────────────┐
│ 1. Total SPU Band: 14-19 per store                      │
│    Rationale: Match store capacity and operational plan │
│                                                          │
│ 2. Winter Minimum: ≥5 SPUs if historical winter >20%    │
│    Rationale: Ensure seasonal coverage for demand       │
│                                                          │
│ 3. Frontcourt Minimum: ≥4 SPUs                          │
│    Rationale: High-visibility area drives conversion    │
│                                                          │
│ 4. Jogger Share: ~50% ±15% (35-65% range)               │
│    Rationale: Match historical demand patterns          │
│                                                          │
│ 5. Seasonal Appropriateness: Ban shorts/sets in A/W     │
│    Rationale: Avoid inappropriate inventory              │
│                                                          │
│ 6. Variance Tolerance: ±20% from manual plan            │
│    Rationale: Acceptable deviation for AI optimization  │
└─────────────────────────────────────────────────────────┘
```

**Business Rationale:**
- These constraints ensure recommendations are realistic and actionable
- Violating constraints = stockouts, overstock, or operational chaos

---

### 1.4 Required Output Specification

**Requirement (Section 8):**

```
Required Output Columns (English-only headers):
┌─────────────────────────────────────────────────────────┐
│ Core Identification:                                     │
│ - Store_Code, Cluster_ID, Product_Tags                  │
│                                                          │
│ Optimization Transparency:                               │
│ - Optimization_Target = "Maximize Sell-Through Rate"    │
│ - Current_ST_Pct (current sell-through %)               │
│ - Target_ST_Pct (predicted sell-through %)              │
│ - Delta_ST_Pct (improvement expected)                   │
│                                                          │
│ Constraint Validation:                                   │
│ - Capacity_Utilization_Pct                              │
│ - Store_Type_Alignment                                  │
│ - Temperature_Suitability                               │
│ - Constraint_Status (OK/Warning/Blocked)                │
│                                                          │
│ Confidence & Traceability:                               │
│ - Confidence_Score (0-1)                                │
│ - Trade_Off_Note (explanation of compromises)           │
│ - Run_ID, Spec_Version, Valid_Until_Month               │
│                                                          │
│ Allocation:                                              │
│ - Allocated_Quantity (integer per-store)                │
└─────────────────────────────────────────────────────────┘
```

**Business Rationale:**
- Transparency: Stakeholders understand WHY recommendations were made
- Confidence: Know which recommendations are reliable
- Traceability: Audit trail for decisions
- Actionability: Clear what to do and when

---

## Part 2: Legacy Implementation (What Actually Happens)

### Source: Code Analysis of `step7_missing_category_rule.py`

### 2.1 Actual Objective

**Implementation (Lines 1010-1023):**

```python
# Calculate ROI and margin uplift
roi_value = margin_uplift / investment_required if investment_required > 0 else 0
margin_uplift = margin_per_unit * expected_units

# Filter by profit thresholds
if not (roi_value >= ROI_MIN_THRESHOLD and 
        margin_uplift >= MIN_MARGIN_UPLIFT and 
        n_comparables >= MIN_COMPARABLES):
    continue  # Reject opportunity
```

**Where:**
- `ROI_MIN_THRESHOLD = 0.30` (30% return on investment)
- `MIN_MARGIN_UPLIFT = 100.0` ($100 minimum profit)
- `MIN_COMPARABLES = 10` (10 stores must sell it)

**Translation:**
- System filters for PROFIT, not sell-through
- A product with 80% sell-through but $99 profit → REJECTED
- A product with 40% sell-through but $101 profit → ACCEPTED

**The Problem:**

```
Example: Jogger Pants at Store 51161
────────────────────────────────────────────────────────
Historical Performance:
- Units sold: 175 (57% of total sales!)
- Sell-through rate: 75% (excellent)
- Margin per unit: $8
- Expected quantity: 15 units
- Margin uplift: $8 × 15 = $120 ✅ (passes $100 threshold)

But if expected quantity was 12 units:
- Margin uplift: $8 × 12 = $96 ❌ (fails $100 threshold)
- Result: FILTERED OUT despite being #1 seller!

This is why joggers are missing from recommendations.
```

---

### 2.2 Actual Features Considered

**Implementation:**

| Feature | Status | Evidence |
|---------|--------|----------|
| Climate/Temperature Zone | ✅ Implicit | Stores in same cluster = same temp zone |
| Store Type/Style | ❌ Missing | No Fashion/Basic classification |
| Capacity/Size Tier | ❌ Missing | No capacity consideration |

**The Problem:**

```
Store 51161 Capacity Analysis:
────────────────────────────────────────────────────────
Unknown:
- Store size (Small/Medium/Large?)
- Fixture capacity (how many SKUs can fit?)
- Display space (frontcourt vs backcourt capacity?)

Result:
- System can't tell if 9 SPUs is appropriate or too few
- System can't tell if store can handle 19 SPUs
- No capacity-based filtering or allocation
```

---

### 2.3 Actual Constraints Enforced

**Implementation:**

| Constraint | Required | Enforced? | Evidence |
|------------|----------|-----------|----------|
| Total SPU Band (14-19) | Yes | ❌ No | Store 51161 has 9 |
| Winter Minimum (≥5) | Yes | ❌ No | Store 51161 has 0 |
| Frontcourt Minimum (≥4) | Yes | ❌ No | Store 51161 has 0 |
| Jogger Share (~50%) | Yes | ❌ No | Store 51161 has 0% |
| Ban Shorts/Sets in A/W | Yes | ❌ No | Store 51161 has 2 |
| Variance Tolerance (±20%) | Yes | ❌ No | Store 51161 at -53% |

**The Problem:**

```
Store 51161 Constraint Violations:
────────────────────────────────────────────────────────
Total SPUs:        9 (should be 14-19)     ❌ -36% below minimum
Winter SPUs:       0 (should be ≥5)        ❌ 100% gap
Frontcourt SPUs:   0 (should be ≥4)        ❌ 100% gap
Jogger Share:      0% (should be 35-65%)   ❌ 100% gap
Inappropriate:     2 (should be 0)         ❌ Shorts/sets present
Variance:          -53% (should be ±20%)   ❌ 2.6× tolerance

Result: Store violates ALL business rules!
```

---

### 2.4 Actual Output Columns

**Implementation:**

```
Legacy Output Columns:
┌─────────────────────────────────────────────────────────┐
│ Present:                                                 │
│ - str_code, cluster_id, sub_cate_name                   │
│ - recommended_quantity_change                           │
│ - unit_price, investment_required                       │
│ - roi, margin_uplift                                    │
│ - fast_fish_compliant (boolean)                         │
│                                                          │
│ Missing (ALL required columns):                          │
│ ❌ Optimization_Target                                  │
│ ❌ Current_ST_Pct, Target_ST_Pct, Delta_ST_Pct          │
│ ❌ Capacity_Utilization_Pct                             │
│ ❌ Store_Type_Alignment                                 │
│ ❌ Temperature_Suitability                              │
│ ❌ Constraint_Status                                    │
│ ❌ Confidence_Score                                     │
│ ❌ Trade_Off_Note                                       │
│ ❌ Run_ID, Spec_Version, Valid_Until_Month              │
└─────────────────────────────────────────────────────────┘
```

**The Problem:**

- No transparency: Can't see WHY recommendations were made
- No confidence: Don't know which recommendations are reliable
- No traceability: Can't audit decisions
- No constraint status: Don't know if rules were violated

---

## Part 3: Side-by-Side Comparison

### 3.1 Objective Function

| Aspect | Required | Legacy | Gap |
|--------|----------|--------|-----|
| **Primary Goal** | Maximize sell-through rate | Maximize profit (ROI/margin) | ❌ Wrong objective |
| **Scoring Method** | Predicted sell-through × confidence | Binary filter (pass/fail) | ❌ No scoring |
| **Optimization** | Constraint-aware solver | Hard threshold filters | ❌ No optimization |
| **Trade-offs** | Explicit (documented in output) | Implicit (hidden in code) | ❌ No transparency |

**Impact:** High-selling, low-margin items filtered out (e.g., joggers)

---

### 3.2 Input Features

| Feature | Required | Legacy | Gap |
|---------|----------|--------|-----|
| **Temperature** | Yes (via clustering) | ✅ Yes (implicit) | ✅ OK |
| **Store Type** | Yes (Fashion/Basic/Balanced) | ❌ No | ❌ Missing |
| **Capacity** | Yes (Small/Medium/Large) | ❌ No | ❌ Missing |
| **Sales History** | Yes | ✅ Yes | ✅ OK |
| **Cluster Membership** | Yes | ✅ Yes | ✅ OK |

**Impact:** Can't prevent over-allocation or style mismatches

---

### 3.3 Constraint Enforcement

| Constraint | Required | Legacy | Gap |
|------------|----------|--------|-----|
| **Total SPU Band** | 14-19 per store | No enforcement | ❌ Missing |
| **Winter Minimum** | ≥5 if history >20% | No enforcement | ❌ Missing |
| **Frontcourt Minimum** | ≥4 per store | No enforcement | ❌ Missing |
| **Jogger Share** | ~50% ±15% | No enforcement | ❌ Missing |
| **Seasonal Ban** | No shorts/sets in A/W | No enforcement | ❌ Missing |
| **Variance Tolerance** | ±20% from plan | No enforcement | ❌ Missing |

**Impact:** Store 51161 violates ALL constraints

---

### 3.4 Output Specification

| Column Category | Required Columns | Legacy Columns | Gap |
|-----------------|------------------|----------------|-----|
| **Optimization** | Optimization_Target, ST metrics | roi, margin_uplift | ❌ Wrong metrics |
| **Constraints** | Constraint_Status, capacity, alignment | None | ❌ All missing |
| **Confidence** | Confidence_Score, Trade_Off_Note | None | ❌ All missing |
| **Traceability** | Run_ID, Spec_Version, Valid_Until | None | ❌ All missing |

**Impact:** No transparency, no auditability, no confidence assessment

---

## Part 4: Real-World Impact - Store 51161 Case Study

### 4.1 The Numbers

| Metric | Required | Legacy | Gap | Impact |
|--------|----------|--------|-----|--------|
| **Total SPUs** | 14-19 | 9 | -36% | Below minimum capacity |
| **Winter SPUs** | ≥5 | 0 | -100% | Missing 142 units sales |
| **Frontcourt SPUs** | ≥4 | 0 | -100% | Missing 149 units sales |
| **Jogger SPUs** | ~50% share | 0 | -100% | Missing 175 units sales (57%!) |
| **Inappropriate** | 0 | 2 | +2 | Shorts/sets in autumn |
| **Variance** | ±20% | -53% | -33pp | 2.6× tolerance exceeded |

### 4.2 Sales Impact Analysis

**2024 Actual Sales: 306 units total**

```
Missing Sales by Dimension:
────────────────────────────────────────────────────────
By Subcategory:
- Jogger Pants:    175 units (57% of total) ❌ MISSING
- Straight Pants:  112 units (37% of total) ⚠️ UNDERREPRESENTED (3 SPUs)
- Other:            19 units (6% of total)  ✅ OK

By Season:
- Autumn:          162 units (53% of total) ✅ OK (9 SPUs)
- Winter:          142 units (46% of total) ❌ MISSING (0 SPUs)
- Spring:            2 units (1% of total)  ✅ OK (ignore)

By Display Location:
- Frontcourt:      149 units (49% of total) ❌ MISSING (0 SPUs)
- Backcourt:       157 units (51% of total) ✅ OK (9 SPUs)

Total Missing Sales Opportunity: 175 + 142 + 149 = 466 units
(Note: Overlap exists, but each dimension shows critical gaps)
```

### 4.3 Business Consequences

**Stockout Risk:**
- Joggers: 175 units unmet demand → Customer dissatisfaction
- Winter: 142 units unmet demand → Seasonal gap
- Frontcourt: 149 units unmet demand → Lost impulse purchases

**Inventory Risk:**
- Shorts: 0 historical sales → Dead stock
- Pants Sets: 0 historical sales → Dead stock

**Operational Impact:**
- Only 9 SPUs vs 14-19 required → Underutilized store capacity
- -53% variance from plan → Misalignment with merchandising strategy

**Financial Impact (Estimated):**
- Lost sales: 466 units × avg margin → Significant revenue loss
- Markdown risk: 2 inappropriate SPUs → Clearance losses

---

## Part 5: Root Cause Analysis

### 5.1 Why Did This Happen?

#### Cause 1: Wrong Objective Function

**Root Cause:**
```python
# Legacy filters by profit
if roi >= 0.30 and margin_uplift >= 100:
    approve()

# Should optimize by sell-through
score = predicted_sell_through * confidence
rank_and_select(top_N)
```

**Why This Causes Problems:**
- Joggers have high sell-through (75%) but moderate margin ($8/unit)
- At 12 units: margin_uplift = $96 → FILTERED OUT
- At 15 units: margin_uplift = $120 → APPROVED
- Result: Arbitrary threshold determines if #1 seller gets recommended!

**Compounding Factor: Dual-Quantity Quirk**
```python
# Two different quantities used:
expected_quantity_int = int(max(1, ceil(avg_sales / unit_price)))  # Conservative
expected_units = int(max(1, ceil(median_amt / unit_price)))        # Aggressive

# ROI uses aggressive quantity (inflates margin_uplift)
margin_uplift = margin_per_unit * expected_units

# But recommendation uses conservative quantity
recommended_quantity = expected_quantity_int

# This creates inconsistency and unpredictability
```

---

#### Cause 2: Missing Input Features

**Root Cause:**
- Store capacity not in data → Can't prevent over-allocation
- Store type not classified → Can't match style appropriateness

**Why This Causes Problems:**
- System doesn't know if 9 SPUs is too few or appropriate for store size
- System can't tell if Fashion items suit a Basic store
- No capacity-based filtering or allocation logic

---

#### Cause 3: No Constraint Enforcement

**Root Cause:**
- Step 7 produces opportunities but doesn't enforce business rules
- Step 13 should enforce but doesn't (or rules not implemented)

**Why This Causes Problems:**
- Store 51161 violates ALL 6 constraints
- No feedback loop to adjust when constraints violated
- System can produce invalid assortments without detection

---

#### Cause 4: Architectural Mismatch

**Root Cause:**
```
Requirements say: "Constraint-aware optimization solver"
Legacy implements: "Hard threshold filters"

Requirements say: "Maximize sell-through"
Legacy implements: "Filter by profit"

Requirements say: "Explainable recommendations"
Legacy implements: "Black box filtering"
```

**Why This Causes Problems:**
- Fundamental architecture doesn't support required functionality
- Can't bolt on optimization to a filtering system
- Can't add transparency to opaque logic

---

## Part 6: What to Preserve vs What to Fix

### 6.1 ✅ PRESERVE (These Are Sound)

**Opportunity Identification Logic:**

```
Step 7 Core Logic (KEEP THIS):
┌─────────────────────────────────────────────────────────┐
│ 1. Identify Well-Selling Features                       │
│    ✅ Adoption rate calculation                         │
│    ✅ Statistical significance checks                   │
│    ✅ Cluster-based comparison                          │
│                                                          │
│ 2. Find Missing Opportunities                           │
│    ✅ Store vs cluster peer comparison                  │
│    ✅ Gap analysis                                      │
│                                                          │
│ 3. Calculate Expected Quantity                          │
│    ✅ Peer median sales                                 │
│    ✅ Unit price adjustment                             │
│                                                          │
│ 4. Temperature Handling                                 │
│    ✅ Already done at cluster level                     │
│    ✅ No additional filtering needed                    │
└─────────────────────────────────────────────────────────┘
```

**Why Preserve:**
- Logic is fundamentally sound
- Produces valid opportunities (~3,583 raw opportunities)
- Temperature already handled correctly via clustering
- Well-tested and understood

---

### 6.2 ❌ FIX (These Are Broken)

**Filtering & Optimization:**

```
Step 7 Filtering (REPLACE THIS):
┌─────────────────────────────────────────────────────────┐
│ Current: Filter by profit                                │
│ - roi >= 30%                                            │
│ - margin_uplift >= $100                                 │
│ - Dual-quantity calculation quirk                       │
│                                                          │
│ Replace with: Score by sell-through                     │
│ - predicted_sell_through × confidence                   │
│ - Store capacity fit                                    │
│ - Store type alignment                                  │
│ - Seasonal appropriateness                              │
└─────────────────────────────────────────────────────────┘

Step 13 Constraints (ADD THIS):
┌─────────────────────────────────────────────────────────┐
│ Missing: Constraint enforcement                          │
│ - Total SPU band (14-19)                                │
│ - Winter minimum (≥5)                                   │
│ - Frontcourt minimum (≥4)                               │
│ - Jogger share (~50%)                                   │
│ - Ban inappropriate categories                          │
│ - Post-rounding rebalance                               │
└─────────────────────────────────────────────────────────┘

Output Specification (ADD THIS):
┌─────────────────────────────────────────────────────────┐
│ Missing: Required columns                                │
│ - Optimization_Target                                   │
│ - Sell-through metrics                                  │
│ - Constraint_Status                                     │
│ - Confidence_Score                                      │
│ - Trade_Off_Note                                        │
└─────────────────────────────────────────────────────────┘
```

---

## Part 7: Recommendations

### 7.1 Do NOT Replicate Legacy Exactly

**Why:**
- ❌ Perpetuates wrong objective (profit vs sell-through)
- ❌ Continues Store 51161 failures
- ❌ Violates go/no-go acceptance criteria
- ❌ Increases technical debt
- ❌ Erodes stakeholder trust

**Even though:**
- ✅ Faster to implement (2 weeks vs 7 weeks)
- ✅ Lower risk of behavior changes

**Verdict:** ⛔ **NOT RECOMMENDED**

---

### 7.2 Fix Incrementally During Refactoring

**Approach:**

```
Phase 1 (Weeks 1-2): Fix Objective Function
├── Replace ROI filtering with sell-through scoring
├── Remove dual-quantity quirk
├── Validate jogger representation increases
└── Test on Store 51161

Phase 2 (Weeks 3-4): Add Missing Features
├── Add store capacity data
├── Add store type classification
├── Integrate into scoring
└── Validate no over-capacity

Phase 3 (Weeks 5-6): Enforce Constraints
├── Implement winter floor
├── Implement frontcourt minimum
├── Implement jogger share control
├── Implement SPU band calibration
└── Validate Store 51161 compliance

Phase 4 (Week 7): Output Specification
├── Add required columns
├── Implement constraint status
├── Implement confidence scoring
└── Final validation
```

**Why:**
- ✅ Meets business requirements
- ✅ Fixes Store 51161 issues
- ✅ Reduces technical debt
- ✅ Builds stakeholder trust
- ✅ Preserves sound opportunity identification logic

**Verdict:** ✅ **RECOMMENDED**

---

## Part 8: Success Criteria

### 8.1 Store 51161 Validation

**Before (Legacy):**
- Total SPUs: 9 ❌
- Winter SPUs: 0 ❌
- Frontcourt SPUs: 0 ❌
- Jogger share: 0% ❌
- Inappropriate items: 2 ❌
- Variance: -53% ❌

**After (Target):**
- Total SPUs: 14-19 ✅
- Winter SPUs: ≥5 ✅
- Frontcourt SPUs: ≥4 ✅
- Jogger share: 35-65% ✅
- Inappropriate items: 0 ✅
- Variance: ±20% ✅

### 8.2 System-Wide Metrics

| Metric | Legacy | Target | Validation Method |
|--------|--------|--------|-------------------|
| **Objective Alignment** | Profit | Sell-through | Code review |
| **Feature Completeness** | 1/3 | 3/3 | Capacity, type in data |
| **Constraint Violations** | 100% | 0% | Store 51161 test |
| **Output Compliance** | 0/8 | 8/8 | Required columns present |
| **Jogger Representation** | 0% | ~50% | Store 51161 jogger share |

---

## Conclusion

**The legacy Step 7 is not just broken - it's fundamentally misaligned with business requirements.**

**What's Good:**
- ✅ Opportunity identification logic is sound
- ✅ Temperature handling via clustering is correct
- ✅ Expected quantity calculation is reasonable

**What's Broken:**
- ❌ Wrong objective (profit instead of sell-through)
- ❌ Missing features (capacity, store type)
- ❌ No constraint enforcement
- ❌ Missing required output columns

**Recommendation:**
Use refactoring as opportunity to implement correctly. Preserve sound opportunity identification logic, replace broken filtering with sell-through optimization, add missing features, and enforce business constraints.

**Next Steps:**
1. Review this analysis with stakeholders
2. Get alignment on incremental fix approach
3. Begin Phase 1 implementation

---

**Document Status:** Complete  
**Next Document:** Read `OPPORTUNITY_IDENTIFICATION_ANALYSIS.md` to validate core logic soundness
