# Step 11 Enhancement Proposal
## Missed Sales Opportunity with 6 Improvement Axes

> **Document Type:** Technical Proposal  
> **Step:** Step 11 (Missed Sales Opportunity)  
> **Date:** January 27, 2026  
> **Prepared For:** Fast Fish Senior Stakeholders

---

## Executive Summary

This proposal outlines the enhancement of Step 11 (Missed Sales Opportunity) with **6 explicit improvement axes** while preserving all existing core functionality.

### Key Principle

> **Step 11 is SUGGESTION-ONLY and MUST NOT override or negate any decision from Step 7-10.**

---

## 1. Design Constraints (NON-NEGOTIABLE)

### 1.1 What Is NOT Changed

| Component | Status | Rationale |
|-----------|--------|-----------|
| Top performer definition | ✅ PRESERVED | Client-defined business rule |
| Quantity ratio logic | ✅ PRESERVED | Core calculation unchanged |
| Opportunity identification mechanism | ✅ PRESERVED | Original algorithm maintained |
| Selectivity thresholds | ✅ PRESERVED | Business-approved parameters |

### 1.2 What IS Enhanced

| Axis | Enhancement | Type |
|------|-------------|------|
| A | Baseline Gate | Hard eligibility constraint |
| B | Store Affinity Score | Soft modifier (ranking only) |
| C | Customer Mix Consistency | Confidence penalty |
| D | Weather/Seasonal Context | Rationale-only (no decisions) |
| E | Opportunity Tiering | Clear confidence buckets |
| F | Suggestion-Only Safeguard | Decision tree lock |

---

## 2. Axis A: Baseline Gate (Hard Eligibility Constraint)

### Purpose
Ensure Step 11 only runs on a stabilized inventory baseline.

### Implementation

```python
# Step 11 logic MUST only evaluate SPU-store pairs that:
# 1. Have already passed through Step 7-9
# 2. Are NOT flagged for reduction in Step 10

baseline_gate_passed = (
    (eligibility_status in ['ELIGIBLE', 'UNKNOWN']) &
    (NOT step10_reduced)
)
```

### Explicit Rule

> **Step 11 evaluates only after baseline inventory alignment is completed.**

This is implemented as an **eligibility gate**, not a scoring adjustment.

---

## 3. Axis B: Store Affinity Score (Soft Modifier)

### Purpose
Improve prioritization without changing decisions.

### Data Source

Uses existing columns from `store_sales_data`:
- `woman_into_str_cnt_avg`
- `male_into_str_cnt_avg`

### Usage Rules

| Action | Allowed? |
|--------|----------|
| Create or remove opportunities | ❌ NO |
| Change quantities | ❌ NO |
| Affect ranking | ✅ YES |
| Affect confidence labeling | ✅ YES |
| Affect explanation text | ✅ YES |

### Output Labels

- **High affinity**: >= 70% alignment
- **Moderate affinity**: >= 40% alignment
- **Low affinity**: < 40% alignment

---

## 4. Axis C: Customer Mix Consistency Check (Confidence Penalty)

### Purpose
Prevent false positives due to demographic mismatch.

### Logic

Compare:
- Top performer store customer mix
- Target store customer mix

If mismatch > 30%:
- Do NOT remove opportunity
- Apply confidence downgrade (max 50%)

### Explicit Separation

> **This is NOT the same as Affinity Score.**
> This is a **risk signal**, not a preference signal.

---

## 5. Axis D: Weather/Seasonal Context (Rationale-Only)

### Purpose
Improve interpretability, not prediction.

### Constraints

| Action | Allowed? |
|--------|----------|
| Trigger recommendations | ❌ NO |
| Change quantities | ❌ NO |
| Appear in business rationale | ✅ YES |
| Appear in interpretation sections | ✅ YES |

### Explicit Statement

> **Weather and seasonal signals are explanatory context only.**

---

## 6. Axis E: Opportunity Tiering (Clear Confidence Buckets)

### Purpose
Make Step 11 actionable without forcing decisions.

### Required Tiers

| Tier | Score Threshold | Description |
|------|-----------------|-------------|
| High Confidence Growth | >= 70% | Strong peer adoption, high affinity |
| Medium Confidence Growth | >= 40% | Moderate signals |
| Exploratory / Test Opportunity | < 40% | Limited evidence, worth testing |

### Tiering Inputs (Allowed)

- Peer adoption strength
- Store Affinity Score (Axis B)
- Consistency Check (Axis C)
- Sell-through validation (if available)

---

## 7. Axis F: Suggestion-Only Safeguard (Decision Tree Lock)

### Purpose
Ensure Step 11 never violates client rules.

### Mandatory Statements

Step 11:
- ✅ Does NOT alter baseline inventory
- ✅ Does NOT conflict with Step 10 reductions
- ✅ Represents optional upside only

### Implementation

These statements are:
- Explicitly stated in MD documentation
- Reinforced in code comments
- Printed at runtime

---

## 8. Output Specification

### Enhanced Output Columns

| Column | Description | Source |
|--------|-------------|--------|
| `opportunity_tier` | High/Medium/Exploratory | Axis E |
| `tier_score` | Composite confidence score | Axis E |
| `tier_justification` | Human-readable explanation | Axis E |
| `affinity_level` | High/Moderate/Low | Axis B |
| `affinity_score` | Numeric alignment score | Axis B |
| `consistency_penalty` | Confidence penalty (0-1) | Axis C |
| `seasonal_context` | Explanatory context | Axis D |
| `baseline_gate_passed` | Boolean gate result | Axis A |
| `baseline_gate_reason` | Gate explanation | Axis A |
| `recommendation_framing` | "Growth Opportunity" | Axis F |
| `is_mandatory` | Always False | Axis F |
| `step11_note` | Suggestion-only disclaimer | Axis F |

---

## 9. Risk Assessment

### Mitigated Risks

| Risk | Mitigation | Status |
|------|------------|--------|
| Step 11 overrides Step 7-10 | Baseline gate blocks conflicts | ✅ Mitigated |
| False positives from demographic mismatch | Consistency penalty applied | ✅ Mitigated |
| Unclear confidence levels | Tiering provides clear buckets | ✅ Mitigated |
| Weather/season drives decisions | Rationale-only constraint | ✅ Mitigated |

### Remaining Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Low opportunity count in some clusters | Medium | Low | Expected behavior for selective thresholds |
| Affinity data unavailable | Low | Low | Default to Moderate affinity |

---

## 10. Validation Protocol

### Pre-Deployment Checklist

- [ ] No Step 7-10 decision is overridden
- [ ] No inventory increased in Step 7-9 is later reduced by Step 11
- [ ] Step 11 outputs are clearly labeled as optional
- [ ] All A-F axes are implemented and documented
- [ ] MD format is fully consistent across steps

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Data Science Lead | | | |
| Product Owner | | | |
| Client Representative | | | |
