# Step 10 Enhancement Proposal
## Overcapacity Reduction with Prior Increase Protection

> **Document Type:** Technical Proposal  
> **Author:** Data Pipeline Team  
> **Date:** January 27, 2026  
> **Status:** Ready for Review

---

## 1. Executive Summary

This proposal describes the enhancement of Step 10 (Overcapacity Reduction) with strict adherence to the layered decision system (Step 7 → Step 8 → Step 9 → Step 10).

### ⚠️ CRITICAL RULE (Non-Negotiable)

```
Any SPU that was increased or flagged for increase in Step 7, 8, or 9
❌ MUST NOT be reduced in Step 10.

reduction_allowed = NOT(step7_increase OR step8_increase OR step9_increase)
```

### Key Enhancement Goals

1. **Reduction Eligibility Gate** - Block reductions for SPUs increased by Step 7/8/9
2. **Core Subcategory Protection** - Reduced cap (20%) for core products
3. **Full Explainability** - Clear reasons for blocked/allowed reductions
4. **Decision Tree Completion** - Step 10 as cleanup layer after needs satisfied

### Why This Enhancement Matters

**Problem with Original Step 10:**
- No awareness of Step 7/8/9 decisions
- Could reduce SPUs that were just increased (logical conflict)
- No integration with the layered decision system

**Solution:**
- Explicit reduction eligibility gate
- Merge Step 7/8/9 outputs before applying reductions
- Block any SPU with prior increase flag

---

## 2. Design Constraints (Non-Negotiable)

### 2.1 Layered Decision System

Step 10 is **Layer 2 - Constraint & Risk Control**, applied AFTER needs are satisfied:

```
Layer 1 – Need Definition (Steps 7-9)
├── Step 7: Eligibility (can this SPU be sold here?)
├── Step 8: Relative shortage (is this SPU under-allocated vs peers?)
└── Step 9: Absolute shortage (is this SPU below minimum viable level?)
    → Output: NEED_TO_INCREASE (True/False) at store–SPU level

Layer 2 – Constraint & Risk Control (Step 10)
└── Step 10: Overcapacity reduction
    ⚠️ CRITICAL: Cannot reduce SPUs flagged for increase in Layer 1
```

### 2.2 Reduction Eligibility Gate (Mandatory)

```python
def check_reduction_eligibility(spu_store):
    """
    CRITICAL RULE: SPUs increased by Step 7/8/9 cannot be reduced.
    """
    reduction_allowed = NOT(
        step7_increase OR 
        step8_increase OR 
        step9_increase
    )
    return reduction_allowed
```

### 2.3 Customer Requirement Alignment

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| **CRITICAL**: No conflict with Step 7-9 | Reduction eligibility gate | ✅ |
| **E-04**: Core subcategories protected | Reduced cap (20% vs 40%) | ✅ |
| **I-01**: Explainability | `rule10_reason` column | ✅ |
| **I-02**: Guidance | Clear blocked/allowed status | ✅ |

---

## 3. Technical Implementation

### 3.1 Module Structure

```
step10/
├── step10_config.py              # Configuration and core subcategory loading
├── step10_reduction_gate.py      # Reduction eligibility gate (CRITICAL)
├── step10_overcapacity_enhanced.py  # Main orchestrator
├── run_step10_comparison.py      # Comparison script
├── proposal_step10_overcapacity.md  # This document
├── evaluation_step10_comparison.md  # Evaluation report
└── figures/                      # Visualizations
```

### 3.2 Reduction Eligibility Gate

**File:** `step10_reduction_gate.py`

```python
def apply_reduction_gate(
    overcapacity_df: pd.DataFrame,
    step7_df: pd.DataFrame,
    step8_df: pd.DataFrame,
    step9_df: pd.DataFrame,
) -> Tuple[eligible_df, blocked_df, summary]:
    """
    Apply reduction eligibility gate to overcapacity candidates.
    
    CRITICAL RULE:
    reduction_allowed = NOT(step7_increase OR step8_increase OR step9_increase)
    """
    # Merge Step 7 ADD recommendations
    df = merge_step7_increases(overcapacity_df, step7_df)
    
    # Merge Step 8 increases
    df = merge_step8_increases(df, step8_df)
    
    # Merge Step 9 increases
    df = merge_step9_increases(df, step9_df)
    
    # Apply gate
    df['reduction_allowed'] = ~(
        df['step7_increase'] | 
        df['step8_increase'] | 
        df['step9_increase']
    )
    
    eligible_df = df[df['reduction_allowed'] == True]
    blocked_df = df[df['reduction_allowed'] == False]
    
    return eligible_df, blocked_df, summary
```

### 3.3 Core Subcategory Protection

**Requirement:** Core subcategories receive reduced cap (20% vs 40%).

```python
if is_core_subcategory(category_name):
    max_reduction_percentage = 0.20  # 20% cap for core
else:
    max_reduction_percentage = 0.40  # 40% cap for others
```

### 3.4 Integration with Step 7-9

**Step 7 Integration:**
- Load `recommendation` column
- Flag `step7_increase = True` if recommendation == 'ADD'

**Step 8 Integration:**
- Load `recommended_quantity_change` column
- Flag `step8_increase = True` if change > 0

**Step 9 Integration:**
- Load `rule9_applied` column
- Flag `step9_increase = True` if rule9_applied == True

---

## 4. Output Specification

### 4.1 Required Output Columns

| Column | Description | Requirement |
|--------|-------------|-------------|
| `rule10_applied` | True/False | Explainability |
| `rule10_reason` | Human-readable reason | I-01, I-02 |
| `reduction_allowed` | Gate result | CRITICAL |
| `step7_increase` | From Step 7 | Integration |
| `step8_increase` | From Step 8 | Integration |
| `step9_increase` | From Step 9 | Integration |
| `recommended_quantity_change` | Negative for reduction | Output |
| `is_core_subcategory` | True/False | E-04 verification |

### 4.2 Status Codes

| Status | Description | Action |
|--------|-------------|--------|
| `ELIGIBLE_FOR_REDUCTION` | Can be reduced | Apply reduction |
| `BLOCKED_STEP7_INCREASE` | Step 7 recommended ADD | No reduction |
| `BLOCKED_STEP8_INCREASE` | Step 8 increased | No reduction |
| `BLOCKED_STEP9_INCREASE` | Step 9 increased | No reduction |

---

## 5. Validation Protocol

### 5.1 Pre-Deployment Checklist

- [ ] Reduction eligibility gate implemented
- [ ] Step 7/8/9 outputs merged correctly
- [ ] No SPU with prior increase is reduced
- [ ] Core subcategories have reduced cap
- [ ] `rule10_reason` populated for all records

### 5.2 Critical Rule Verification

```python
# This assertion MUST pass
assert (
    blocked_df['step7_increase'] | 
    blocked_df['step8_increase'] | 
    blocked_df['step9_increase']
).all(), "CRITICAL: Blocked records must have prior increase"

assert not (
    eligible_df['step7_increase'] | 
    eligible_df['step8_increase'] | 
    eligible_df['step9_increase']
).any(), "CRITICAL: Eligible records must NOT have prior increase"
```

---

## 6. Role of Step 10 in Decision System

### 6.1 Step 10 is NOT an Optimizer

**Wrong Understanding:**
> "Step 10 optimizes inventory by reducing overcapacity"

**Correct Understanding:**
> "Step 10 is a cleanup layer that reduces overcapacity ONLY for SPUs that don't need more inventory"

### 6.2 Why No Double-Counting

```
SPU X @ Store Y:
├── Step 7: Recommended ADD (need more)
├── Step 8: Not adjusted
├── Step 9: Not applied
└── Step 10: BLOCKED (Step 7 recommended ADD)
    → No reduction because Step 7 said "need more"

SPU Z @ Store Y:
├── Step 7: ELIGIBLE (no ADD recommendation)
├── Step 8: Not adjusted
├── Step 9: Not applied
└── Step 10: ELIGIBLE FOR REDUCTION
    → Can reduce because no prior increase
```

---

## 7. Risk Assessment

### 7.1 Mitigated Risks

| Risk | Mitigation | Status |
|------|------------|--------|
| Reduce SPU increased by Step 7 | Reduction gate | ✅ |
| Reduce SPU increased by Step 8 | Reduction gate | ✅ |
| Reduce SPU increased by Step 9 | Reduction gate | ✅ |
| Aggressive reduction of core | Reduced cap (20%) | ✅ |
| Unexplained decisions | rule10_reason column | ✅ |

### 7.2 Remaining Considerations

| Area | Status | Note |
|------|--------|------|
| Step 7/8/9 output availability | ⚠️ Required | Gate needs prior outputs |
| Performance with large datasets | ✅ OK | Merge operations optimized |

---

## 8. Conclusion

The enhanced Step 10 module:

1. **Implements** the CRITICAL reduction eligibility gate
2. **Respects** Step 7/8/9 decisions (no conflicts)
3. **Protects** core subcategories (reduced cap)
4. **Provides** full explainability (rule10_reason)
5. **Completes** the layered decision system

**Recommendation:** Approve for deployment after validation with 202506A dataset.

---

*Proposal prepared for Fast Fish Demand Forecasting Project*  
*January 2026*
