# Step 12 Enhancement Proposal
## Performance Gap Scaling with Strict Step 11 Boundary

> **Document Type:** Technical Proposal  
> **Step:** Step 12 (Performance Gap Scaling)  
> **Date:** January 27, 2026  
> **Prepared For:** Fast Fish Senior Stakeholders

---

## Executive Summary

This proposal outlines the enhancement of Step 12 (Performance Gap Scaling) with **strict boundary separation from Step 11** and implementation of **5 improvement axes (A-E)**.

### Critical Boundary Definition

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STEP 11 vs STEP 12 SEPARATION                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  STEP 11: Growth Opportunity Discovery                              │
│  ─────────────────────────────────────                              │
│  Output: is_growth_candidate (boolean), opportunity_score           │
│  Purpose: Decides WHAT to grow                                      │
│  ❌ MUST NOT determine or recommend quantities                      │
│                                                                     │
│  STEP 12: Performance Gap Scaling                                   │
│  ────────────────────────────────                                   │
│  Input: ONLY SPUs already marked as candidates by Step 11           │
│  Output: recommended_adjustment_quantity                            │
│  Purpose: Decides HOW MUCH to grow                                  │
│  ❌ MUST NOT decide whether to scale                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. Design Constraints (NON-NEGOTIABLE)

### 1.1 What Step 12 MUST Do

| Requirement | Implementation |
|-------------|----------------|
| Scale ONLY Step 11-approved SPUs | Input filtering enforced |
| Quantify performance gaps | Cluster P75 benchmark comparison |
| Recommend bounded adjustments | Hard safety caps (Axis D) |
| Avoid Step 9 conflicts | Dampening if Step 9 boosted |
| Avoid Step 10 conflicts | Block if Step 10 reduced |
| Provide traceability | Full explanation per recommendation |

### 1.2 What Step 12 MUST NOT Do

| Prohibited Action | Reason |
|-------------------|--------|
| Re-decide eligibility | That's Step 11's job |
| Identify new opportunities | That's Step 11's job |
| Override Step 9 protection | Business rule violation |
| Conflict with Step 10 | Logical inconsistency |
| Scale without Step 11 approval | Boundary violation |

---

## 2. Axis A: Clear Performance Gap Definition

### Purpose
Define performance gap as difference between store-level metrics and cluster-level peer benchmark.

### Implementation

```python
# Performance Gap = Cluster P75 - Store Sales
# Positive gap = store underperforming vs peers
performance_gap = cluster_p75_sales - store_sales
gap_ratio = performance_gap / cluster_p75_sales
```

### Why This Gap Indicates Underperformance

1. **Store sells less than 75% of cluster peers** for this SPU
2. **Gap represents missed sales potential** within similar stores
3. **Scaling is justified** because Step 11 already validated growth potential

### Data Sources (Existing Metrics Only)

- `current_spu_count` - Store's current SPU quantity
- `cluster_p75` - 75th percentile of cluster peers
- `cluster_median` - Median of cluster peers
- No new client-unapproved KPIs introduced

---

## 3. Axis B: Controlled Scaling Logic (No Re-eligibility)

### Scaling Sequence

```
1. Confirm SPU ∈ Step 11 candidates ✓ (input filtering)
2. Confirm SPU NOT forcibly increased in Step 9 ✓ (dampening)
3. Confirm SPU NOT recently reduced in Step 10 ✓ (blocking)
4. Apply scaling only if gap >= 10% threshold ✓
5. No binary decisions - only magnitude decisions ✓
```

### Explicit Rule

> **Step 12 makes ONLY magnitude decisions, never eligibility decisions.**

If any logic implicitly re-decides eligibility, it has been removed.

---

## 4. Axis C: Multi-factor Scaling (Within Bounds)

### Approved Modulation Factors

| Factor | Data Source | Usage |
|--------|-------------|-------|
| Store traffic composition | `woman_into_str_cnt_avg`, `male_into_str_cnt_avg` | Affinity modifier |
| Cluster elasticity | Cluster performance variance | Scaling dampener |
| Historical sell-through | If available | Confidence boost |

### Usage Rules

| Action | Allowed? |
|--------|----------|
| Use as multipliers/dampeners | ✅ YES |
| Create new eligibility conditions | ❌ NO |
| Override Step 11 decisions | ❌ NO |

### Affinity Modifier Calculation

```python
# High alignment (>60%) = boost up to 1.2x
# Low alignment (<40%) = dampen down to 0.7x
# Neutral = 1.0x
modifier = calculate_affinity_modifier(woman_cnt, male_cnt, spu_gender)
```

---

## 5. Axis D: Hard Safety Caps (Client-safe)

### Implemented Caps

| Cap | Value | Justification |
|-----|-------|---------------|
| Max % of current quantity | 50% | Prevent over-scaling |
| Max % of cluster median | 30% | Stay within peer range |
| Max absolute increase | 50 units | Practical implementation limit |
| Min increase quantity | 1 unit | Avoid noise |

### Dampening Rules

| Condition | Dampening |
|-----------|-----------|
| Step 9 already applied boost | 50% reduction |
| Step 10 flagged volatility | BLOCK (no scaling) |

### Documentation

All caps are:
- ✅ Documented in code
- ✅ Explained in markdown
- ✅ Justified as risk control, not strategy change

---

## 6. Axis E: Decision Traceability

### For Every Recommendation

| Field | Content |
|-------|---------|
| `gap_justification` | Why this SPU was scaled |
| `cluster_p75` | Which peer benchmark it lagged |
| `scaling_explanation` | Which factors affected quantity |
| `no_conflict_reason` | Why result doesn't conflict with Steps 9-11 |
| `full_explanation` | Complete decision trace |

### Example Traceability Record

```
WHY SCALED: Step 11 identified this as a High Confidence Growth opportunity
BENCHMARK LAG: Store sells 15.2 units below cluster P75 (35.8)
FACTORS: base=7.6, affinity=1.05x, step9_dampen=1.0x
RECOMMENDATION: +7.5 units (Moderate Adjustment)
NO CONFLICT: ✓ Step 11 approved | ✓ No Step 9 boost | ✓ No Step 10 reduction
```

---

## 7. Output Specification

### Enhanced Output Columns

| Column | Description | Source |
|--------|-------------|--------|
| `recommended_adjustment_quantity` | Final scaling amount | Axis B, C, D |
| `performance_gap` | Gap vs cluster P75 | Axis A |
| `gap_ratio` | Normalized gap | Axis A |
| `scaling_tier` | Minimal/Moderate/Aggressive | Axis D |
| `affinity_modifier` | Traffic-based modifier | Axis C |
| `step9_dampener` | Step 9 conflict dampening | Axis B |
| `cap_applied` | Which safety cap triggered | Axis D |
| `gap_justification` | Why gap indicates underperformance | Axis E |
| `no_conflict_reason` | Step 9-11 conflict verification | Axis E |
| `full_explanation` | Complete decision trace | Axis E |

---

## 8. Validation Protocol

### Pre-Delivery Checklist

- [x] No logic duplicates Step 11
- [x] No inventory scaled twice
- [x] Graph labels render correctly
- [x] Sample run uses same dataset as Steps 9-11
- [x] All changes inside client requirement boundaries

### Boundary Verification

| Check | Status |
|-------|--------|
| Step 12 only processes Step 11 candidates | ✅ VERIFIED |
| No independent opportunity identification | ✅ VERIFIED |
| Step 9 conflicts checked | ✅ VERIFIED |
| Step 10 conflicts checked | ✅ VERIFIED |
| Hard safety caps applied | ✅ VERIFIED |
| Full traceability provided | ✅ VERIFIED |

---

## 9. Risk Assessment

### Mitigated Risks

| Risk | Mitigation | Status |
|------|------------|--------|
| Step 12 re-decides eligibility | Input filtering enforced | ✅ Mitigated |
| Conflict with Step 9 | Dampening applied | ✅ Mitigated |
| Conflict with Step 10 | Blocking enforced | ✅ Mitigated |
| Over-scaling | Hard safety caps | ✅ Mitigated |
| Unexplainable recommendations | Full traceability | ✅ Mitigated |

---

## 10. Conclusion

The enhanced Step 12 makes it **immediately obvious** that:

1. **Step 11 decides what to grow** - opportunity identification
2. **Step 12 decides how much to grow** - quantity scaling
3. **No step contradicts another** - conflict checking enforced
4. **All improvements enhance precision, not policy** - business rules preserved

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Data Science Lead | | | |
| Product Owner | | | |
| Client Representative | | | |
