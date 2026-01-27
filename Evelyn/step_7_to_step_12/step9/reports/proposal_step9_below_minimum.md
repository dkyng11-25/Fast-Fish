# Step 9 Enhancement Proposal
## Below Minimum SPU Rule with Customer Deviation Guardrails

> **Document Type:** Technical Proposal  
> **Author:** Data Pipeline Team  
> **Date:** January 27, 2026  
> **Status:** Ready for Review

---

## 1. Executive Summary

This proposal describes the enhancement of Step 9 (Below Minimum SPU Rule) with strict adherence to customer requirements and deviation guardrails.

### Key Enhancement Goals

1. **Decision Tree Integration** - Enforce execution order: Step 7 → Step 8 → Step 9
2. **Core Subcategory Protection** - Always evaluate core products (configurable)
3. **3-Level Minimum Fallback** - Manual → Cluster P10 → Global
4. **Sell-Through Validation** - Require demand signal before increasing
5. **Conservative Increases** - Never decrease, never negative

### Why This Enhancement Matters

**Problem with Original Step 9:**
- No integration with Step 7 eligibility
- No check for Step 8 adjustments (potential double-counting)
- Core subcategories could be missed
- Minimum threshold was fixed (not configurable)
- No sell-through validation

**Solution:**
- Explicit decision tree with skip conditions
- Core subcategories always evaluated per client requirement
- 3-level fallback for minimum threshold
- Sell-through gate prevents increasing zero-demand SPUs

---

## 2. Design Constraints (Non-Negotiable)

### 2.1 Customer Requirement Alignment

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| **E-04**: Core subcategories included | Loaded from config file, always evaluated | ✅ |
| **E-05**: ±20% of manual/historical | Max increase capped at 20% | ✅ |
| **E-06**: Never decrease, no negatives | `never_decrease=True`, validation gate | ✅ |
| **I-01**: Explainability | `rule9_reason` column in output | ✅ |
| **I-02**: Guidance | Clear status codes and reasons | ✅ |
| **I-05**: Business priorities override | Core subcategories bypass filters | ✅ |

### 2.2 Decision Tree (Mandatory)

```
SPU @ Store
│
├─ Step 7: Eligibility Check
│    ├─ INELIGIBLE → STOP (never process)
│    │   Exception: Core subcategories always continue
│    └─ ELIGIBLE / UNKNOWN → continue
│
├─ Step 8: Cross-Store Balance Check
│    ├─ adjusted_by_step8 == True → SKIP Step 9
│    └─ adjusted_by_step8 == False → continue
│
├─ Sell-Through Validation
│    ├─ No demand signal → SKIP (unless core subcategory)
│    └─ Has demand signal → continue
│
└─ Step 9: Below Minimum Check (Store-Specific)
     ├─ current >= minimum → ABOVE_MINIMUM (no action)
     └─ current < minimum → BELOW_MINIMUM (recommend increase)
```

---

## 3. Technical Implementation

### 3.1 Module Structure

```
step9/
├── step9_config.py              # Configuration and core subcategory loading
├── step9_minimum_evaluator.py   # 3-level fallback and evaluation logic
├── step9_below_minimum_enhanced.py  # Main orchestrator
├── run_step9_comparison.py      # Comparison script
├── proposal_step9_below_minimum.md  # This document
├── evaluation_step9_comparison.md   # Evaluation report
└── figures/                     # Visualizations
```

### 3.2 Core Subcategory Handling

**Requirement:** Core subcategories must NOT be hardcoded.

**Implementation:**
```python
# Loaded from config file (shared with Step 7)
STEP7_CONFIG_PATH = "step7/core_subcategories_config.json"
STEP9_CONFIG_PATH = "step9/step9_core_subcategories_config.json"

def load_core_subcategories() -> Set[str]:
    # Priority: Step 9 config → Step 7 config → Default fallback
    ...
```

**Config File Format:**
```json
{
  "core_subcategories": [
    "直筒裤", "束脚裤", "锥形裤",
    "Straight-Leg", "Jogger", "Tapered"
  ]
}
```

### 3.3 3-Level Minimum Fallback

**Requirement:** Use first NON-NULL value in priority order.

```python
def get_minimum_reference(
    manual_plan_minimum: Optional[float],
    cluster_p10_rate: Optional[float],
    config: Step9Config
) -> tuple:
    """
    Priority order:
    1. Manual Plan Minimum (customer-provided)
    2. Cluster-level P10 unit rate
    3. Global fallback minimum (e.g., 1.0)
    """
    if manual_plan_minimum is not None and manual_plan_minimum > 0:
        return (manual_plan_minimum, MinimumReferenceSource.MANUAL_PLAN)
    
    if cluster_p10_rate is not None and cluster_p10_rate > 0:
        return (cluster_p10_rate, MinimumReferenceSource.CLUSTER_P10)
    
    return (config.global_minimum_unit_rate, MinimumReferenceSource.GLOBAL_FALLBACK)
```

### 3.4 Sell-Through Validation

**Requirement:** Step 9 MUST NOT increase SPUs with zero demand signal.

```python
def evaluate_sell_through(
    recent_sales_units: Optional[float],
    sell_through_rate: Optional[float],
    cluster_median_sellthrough: Optional[float]
) -> tuple:
    """
    sell_through_valid = (
        recent_sales_units > 0
        OR sell_through_rate >= cluster_median_sellthrough * 0.5
    )
    """
    has_sales = recent_sales_units is not None and recent_sales_units > 0
    has_sellthrough = sell_through_rate >= (cluster_median_sellthrough * 0.5)
    
    return (has_sales or has_sellthrough, reason)
```

### 3.5 Conservative Quantity Increase

**Requirement:** Choose minimum of positive candidates.

```python
def calculate_conservative_increase(
    current_quantity: float,
    minimum_threshold: float,
    historical_baseline: Optional[float],
    config: Step9Config
) -> int:
    """
    Candidate sources:
    1. Gap to minimum threshold
    2. Minimum boost quantity (floor)
    3. Case pack size (if available)
    4. 10% of remaining capacity (if available)
    5. Max 20% of historical baseline (per E-05)
    
    recommended_increase = min(positive_candidates)
    """
    candidates = [gap, min_boost, case_pack, capacity_based, max_20pct]
    return max(1, int(np.ceil(min(positive_candidates))))
```

---

## 4. Output Specification

### 4.1 Required Output Columns

| Column | Description | Requirement |
|--------|-------------|-------------|
| `rule9_applied` | True/False | Explainability |
| `rule9_reason` | Human-readable reason | I-01, I-02 |
| `minimum_reference_used` | manual_plan / cluster_p10 / global | Traceability |
| `eligibility_status` | From Step 7 | Decision tree |
| `adjusted_by_step8` | From Step 8 | No double-counting |
| `recommended_quantity_change` | Integer increase | E-06 (always positive) |
| `is_core_subcategory` | True/False | E-04 verification |
| `sell_through_valid` | True/False | Demand validation |

### 4.2 Status Codes

| Status | Description | Action |
|--------|-------------|--------|
| `BELOW_MINIMUM` | Below threshold, action required | Recommend increase |
| `ABOVE_MINIMUM` | Above threshold | No action |
| `SKIPPED_STEP8` | Already adjusted by Step 8 | No action (avoid double-counting) |
| `SKIPPED_INELIGIBLE` | Ineligible per Step 7 | No action |
| `SKIPPED_NO_DEMAND` | No demand signal | No action |

---

## 5. Validation Protocol

### 5.1 Pre-Deployment Checklist

- [ ] Core subcategories loaded from config (not hardcoded)
- [ ] Decision tree enforced (Step 7 → Step 8 → Step 9)
- [ ] No negative quantities in output
- [ ] No decreases recommended
- [ ] All increases within ±20% of baseline
- [ ] `rule9_reason` populated for all records

### 5.2 Customer Requirement Boundary Check

| Check | Requirement | Validation |
|-------|-------------|------------|
| No core subcategory excluded | E-04 | Count core in output |
| No over-allocation | E-05 | Max increase ≤ 20% |
| No negative values | E-06 | Min(recommended_change) ≥ 0 |
| No unexplained logic | I-01, I-02 | All records have reason |

---

## 6. Differences from Step 8

| Aspect | Step 8 | Step 9 |
|--------|--------|--------|
| **Scope** | Cross-store comparison | Store-specific threshold |
| **Method** | Z-score imbalance | Absolute minimum check |
| **Trigger** | Deviation from cluster mean | Below minimum threshold |
| **Action** | Rebalance (increase or decrease) | Increase only |
| **Risk Level** | Medium (rebalancing) | Low (conservative boost) |

**Why No Double-Counting:**
- Step 9 explicitly checks `adjusted_by_step8 == False`
- If Step 8 already adjusted, Step 9 skips
- Each SPU × Store is processed by at most one rule

---

## 7. Risk Assessment

### 7.1 Mitigated Risks

| Risk | Mitigation | Status |
|------|------------|--------|
| Core subcategories filtered | Config-based loading, always evaluate | ✅ |
| Double-counting with Step 8 | Explicit skip condition | ✅ |
| Negative quantities | Validation gate, never_decrease flag | ✅ |
| Over-allocation | 20% cap on increases | ✅ |
| Unexplained recommendations | rule9_reason column | ✅ |

### 7.2 Remaining Considerations

| Area | Status | Note |
|------|--------|------|
| Manual plan minimum data | ⚠️ Optional | Falls back to cluster P10 or global |
| Store capacity data | ⚠️ Optional | Not required for Step 9 |
| Historical baseline | ⚠️ Optional | Used for 20% cap if available |

---

## 8. Conclusion

The enhanced Step 9 module:

1. **Strictly adheres** to customer requirements (E-04, E-05, E-06, I-01, I-02, I-05)
2. **Integrates** with Step 7 and Step 8 via decision tree
3. **Protects** core subcategories (configurable, not hardcoded)
4. **Uses** 3-level fallback for minimum threshold
5. **Validates** sell-through before recommending increases
6. **Ensures** conservative, positive-only recommendations

**Recommendation:** Approve for deployment after validation with 202506A dataset.

---

*Proposal prepared for Fast Fish Demand Forecasting Project*  
*January 2026*
