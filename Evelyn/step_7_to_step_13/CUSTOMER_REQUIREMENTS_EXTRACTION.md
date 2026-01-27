# Fast Fish Customer Requirements Extraction & Deviation Guardrails

> **Document Type:** Senior Data Science Lead Review  
> **Purpose:** Extract customer requirements from meeting history and establish guardrails for Step 7–13 changes  
> **Scope:** All changes to Steps 7–13 must be validated against this document  
> **Last Updated:** January 27, 2026  
> **Review Mode:** ACTIVE - All proposed changes require validation

---

## Executive Summary

This document extracts customer requirements from Fast Fish meeting history and establishes **deviation guardrails** to ensure all Step 7–13 module changes remain within the client's requirement boundary.

### Core Principle

> **Performance optimization is ALWAYS secondary to requirement alignment.**  
> A high-performing solution that deviates from customer intent is considered a **FAILURE**.

---

## Part A: Timeline-Based Requirement Mapping

### Phase 1: Contract & Initial Requirements (Sep 2025)

**Source:** `FF contract 264d33600a2680d5aafdee4459a4333f.md`

| Req ID | Requirement | Priority | Status |
|--------|-------------|----------|--------|
| **C-01** | Recommended quantity must be AI-optimized, not simple forecast | CRITICAL | ⚠️ Partial |
| **C-02** | Optimization must consider: demand forecast, store capacity, sell-through rate, profitability, inventory constraints, product lifecycle, business rules | CRITICAL | ⚠️ Partial |
| **C-03** | Store clustering limited to 20-40 clusters | HIGH | ✅ Met |
| **C-04** | Temperature zone optimization beyond administrative boundaries | HIGH | ✅ Met |
| **C-05** | Validate store type tags (Basic vs Fashion) | HIGH | ❌ Not Met |
| **C-06** | Incorporate store capacity into clustering | CRITICAL | ❌ Not Met |
| **C-07** | Implement dynamic clustering to adapt to changes | MEDIUM | ⚠️ Partial |
| **C-08** | A/B testing framework for validation | CRITICAL | ⚠️ In Progress |

### Phase 2: Business Meeting Feedback (Nov 25, 2025)

**Source:** `Fast Fish Meeting NOV 25 2025`

| Req ID | Requirement | Priority | Client Concern |
|--------|-------------|----------|----------------|
| **M-01** | AI recommendation quantities must NOT exactly match manual planning | HIGH | "Is this intentional or did something go wrong?" |
| **M-02** | Temperature zone data must use correct/up-to-date version | CRITICAL | Version mismatch identified |
| **M-03** | Cluster size balance - merge small clusters, consider splitting large ones | HIGH | Cluster 16, 43 too small |
| **M-04** | Clear A/B testing methodology needed | CRITICAL | "How do we test this data?" |
| **M-05** | Front-of-store vs Back-of-store distinction must be maintained | CRITICAL | Business strategy difference |
| **M-06** | Temperature zones currently used for lifecycle stages, not temperature targeting | HIGH | Disconnect with business usage |
| **M-07** | Need clear guidance on how to apply temperature zone configurations | HIGH | "Without guidance, they won't know how to proceed" |

### Phase 3: WeChat Issues & Operational Feedback (Oct-Nov 2025)

**Source:** `fast fish wechat issues`

| Req ID | Issue | Priority | Client Statement |
|--------|-------|----------|------------------|
| **W-01** | Missing subcategory data (Straight-Leg, Jogger) | CRITICAL | "Core styles for November should receive special attention" |
| **W-02** | Missing Front Display data | CRITICAL | "Front-display items drive conversion" |
| **W-03** | Inconsistent category/big_class fields | HIGH | "Casual Pants and Jeans are distinct categories" |
| **W-04** | Over-allocation (3-5x higher than manual/historical) | CRITICAL | "May lead to potential resource waste" |
| **W-05** | Negative configuration values | CRITICAL | "Inconsistent with actual business structure" |
| **W-06** | Imbalanced subcategory allocation | HIGH | "Over-allocation in Slim-Fit and Wide-Leg not in business plan" |
| **W-07** | Display location tag inconsistency | HIGH | "Mix of Front Display and 后台 within same tag" |

### Phase 4: In-Person Meeting Key Takeaways (Recent)

**Source:** `Key takeaway from Fast Fish in-person.txt`

| Req ID | Requirement | Priority | Blocking A/B? |
|--------|-------------|----------|---------------|
| **K-01** | Gap-Analysis Workbook for ≥3 flagship clusters | TOP PRIORITY | ✅ YES |
| **K-02** | Store style & capacity attributes in clustering | TOP PRIORITY | ✅ YES |
| **K-03** | Run new clusters with store lists + all tags | TOP PRIORITY | ✅ YES |
| **K-04** | Store-level plug-and-play output | TOP PRIORITY | ✅ YES |
| **K-05** | Sell-through as primary optimization objective | HIGH | ✅ YES |
| **K-06** | Back-testing module on blind historical data | MEDIUM | ✅ YES |

---

## Part B: Explicit vs Implicit Requirements

### Explicit Requirements (Direct Instructions)

| ID | Requirement | Source | Date |
|----|-------------|--------|------|
| **E-01** | Sell-through rate must be primary KPI | Contract, Meetings | Sep-Nov 2025 |
| **E-02** | Store capacity must be considered | Contract, In-person | Sep 2025, Recent |
| **E-03** | Front/Back display location must be preserved | WeChat, Nov Meeting | Oct-Nov 2025 |
| **E-04** | Core subcategories (Straight-Leg, Jogger, Tapered) must be included | WeChat | Oct 2025 |
| **E-05** | Allocation must stay within ±20% of manual/historical | WeChat | Oct 2025 |
| **E-06** | No negative configuration values | WeChat | Oct 2025 |
| **E-07** | Temperature zones must be correctly versioned | Nov Meeting | Nov 2025 |

### Implicit Requirements (Repeated Concerns & Hesitations)

| ID | Concern Pattern | Interpretation | Risk Level |
|----|-----------------|----------------|------------|
| **I-01** | "Is this intentional or did something go wrong?" | Client distrusts unexplained outputs | HIGH |
| **I-02** | "Without guidance, they won't know how to proceed" | Need explainability, not black-box | HIGH |
| **I-03** | "May lead to potential resource waste" | Conservative allocation preferred over aggressive | HIGH |
| **I-04** | Repeated questions about data consistency | Client values data integrity over speed | MEDIUM |
| **I-05** | "Core styles should receive special attention" | Business priorities must override algorithmic optimization | CRITICAL |
| **I-06** | Multiple version/data mismatch complaints | Client sensitive to data quality issues | HIGH |

---

## Part C: Requirement Prioritization Logic

### Conflict Resolution Rules

When requirements conflict, apply in this order:

1. **More recent > older** (unless older explicitly not revoked)
2. **Explicit > implicit**
3. **Risk-avoidance > performance ambition**
4. **Business controllability > algorithmic autonomy**
5. **Core business categories > edge cases**

### Priority Matrix for Step 7–13

| Priority | Requirements | Rationale |
|----------|--------------|-----------|
| **P0 - Non-Negotiable** | E-03 (Front/Back), E-04 (Core subcategories), E-06 (No negatives) | Direct business operations |
| **P1 - Critical** | E-01 (Sell-through KPI), E-05 (±20% range), W-04 (No over-allocation) | A/B test validity |
| **P2 - High** | E-02 (Capacity), E-07 (Version control), I-05 (Business priorities) | Clustering quality |
| **P3 - Medium** | I-01 (Explainability), I-02 (Guidance), I-04 (Data consistency) | Trust building |

---

## Part D: Deviation Guardrails for Step 7–13

### A. Allowed System Behaviors ✅

| Behavior | Rationale | Applicable Steps |
|----------|-----------|------------------|
| **Recommend** products for stores | Core function | 7, 8, 9, 10, 11, 12 |
| **Flag** opportunities or gaps | Informational | 7, 11, 12 |
| **Highlight** imbalances with rationale | Transparency | 8 |
| **Suggest** quantity adjustments with explanation | Actionable | All |
| **Filter** by eligibility (climate/season) | Prevent invalid recommendations | 7, 8 |
| **Rank** by sell-through potential | KPI alignment | All |
| **Consolidate** results with metadata | Traceability | 13 |

### B. Disallowed / High-Risk Behaviors ❌

| Behavior | Risk | Mitigation |
|----------|------|------------|
| **Forced exclusion** of core subcategories | Violates E-04 | Always include Straight-Leg, Jogger, Tapered |
| **Automatic decrease** below minimum | Violates E-06 | Step 9 must never decrease |
| **Opaque decision logic** | Violates I-01, I-02 | Always provide `eligibility_reason` |
| **Over-allocation** (>20% above manual) | Violates E-05, W-04 | Cap recommendations |
| **Negative quantities** | Violates E-06 | Fail-fast validation |
| **Ignoring Front/Back distinction** | Violates E-03, W-02 | Preserve display_location |
| **Using outdated temperature data** | Violates E-07, M-02 | Version check mandatory |
| **Recommending non-core styles over core** | Violates I-05 | Priority weighting |

### C. Sensitive Areas Where Deviation Is Most Likely ⚠️

| Area | Risk Description | Guardrail |
|------|------------------|-----------|
| **Seasonality/Climate Logic** | May filter out core products inappropriately | Never filter core subcategories |
| **Temperature Band Matching** | May exclude stores incorrectly | UNKNOWN status = conservative (include) |
| **Z-Score Imbalance Detection** | May flag valid business decisions | Only flag ELIGIBLE SPUs |
| **Lifecycle Mismatch** | May recommend end-of-life products | Check lifecycle stage |
| **Cluster Interpretation** | Small clusters may be merged incorrectly | Preserve business-meaningful clusters |
| **Quantity Recommendations** | May exceed capacity or business plan | Cap at ±20% of manual/historical |

---

## Part E: Step 7–13 Specific Guardrails

### Step 7: Missing SPU Rule

| Guardrail | Requirement Source | Status |
|-----------|-------------------|--------|
| Must include core subcategories | E-04, W-01 | ⚠️ RISK |
| Eligibility must be explicit | I-01, I-02 | ✅ Implemented |
| Climate filtering must not exclude core products | I-05 | ⚠️ RISK |
| Front/Back display must be preserved | E-03, W-02 | ✅ OK |

**⚠️ DEVIATION RISK IDENTIFIED:**

The current Step 7 eligibility enhancement filters by climate/season. This could potentially filter out **core subcategories** (Straight-Leg, Jogger, Tapered) if they are classified as "winter" products in a "summer" period.

**REQUIRED MITIGATION:**
```python
# Core subcategories must NEVER be filtered by eligibility
CORE_SUBCATEGORIES = ['直筒裤', '束脚裤', '锥形裤', 'Straight-Leg', 'Jogger', 'Tapered']

if sub_cate_name in CORE_SUBCATEGORIES:
    eligibility_status = 'ELIGIBLE'  # Override climate/season filtering
    eligibility_reason = 'Core subcategory - always eligible per business requirement'
```

### Step 8: Imbalanced Allocation Rule

| Guardrail | Requirement Source | Status |
|-----------|-------------------|--------|
| Only analyze ELIGIBLE SPUs | Current enhancement | ✅ Implemented |
| Z-score formula unchanged | Business logic preservation | ✅ Verified |
| No automatic rebalancing of core products | I-05 | ⚠️ Need verification |
| Recommendations within ±20% | E-05 | ⚠️ Need cap |

### Step 9: Below Minimum Rule

| Guardrail | Requirement Source | Status |
|-----------|-------------------|--------|
| NEVER decrease below minimum | E-06, Business logic | ✅ Critical |
| No negative quantities | E-06 | ✅ Validation required |

### Step 10: Over-Capacity Rule

| Guardrail | Requirement Source | Status |
|-----------|-------------------|--------|
| Capacity data must be available | E-02, C-06 | ❌ Not implemented |
| Reductions must preserve core products | I-05 | ⚠️ Need verification |

### Step 11: Missed Sales Opportunity

| Guardrail | Requirement Source | Status |
|-----------|-------------------|--------|
| Focus on sell-through, not just revenue | E-01 | ⚠️ Need verification |
| Core subcategories prioritized | I-05 | ⚠️ Need verification |

### Step 12: Sales Performance Rule

| Guardrail | Requirement Source | Status |
|-----------|-------------------|--------|
| Sell-through gap, not sales gap | E-01 | ⚠️ Need verification |

### Step 13: Consolidation

| Guardrail | Requirement Source | Status |
|-----------|-------------------|--------|
| All metadata preserved | Traceability | ✅ OK |
| Eligibility status included | I-01, I-02 | ✅ OK |
| No data loss | Data integrity | ✅ OK |

---

## Part F: Validation Protocol for All Changes

### Pre-Implementation Checklist

Before implementing any Step 7–13 change:

- [ ] Does this change affect core subcategories (Straight-Leg, Jogger, Tapered)?
- [ ] Does this change affect Front/Back display location logic?
- [ ] Does this change introduce automatic exclusion or decrease?
- [ ] Does this change have explicit rationale output?
- [ ] Is the change within ±20% of manual/historical baseline?
- [ ] Does this change use correct/current data versions?

### Post-Implementation Checklist

After implementing any change:

- [ ] Run on 202506A dataset and verify core subcategories are present
- [ ] Verify no negative quantities in output
- [ ] Verify Front/Back display locations are preserved
- [ ] Verify eligibility_reason is populated for all records
- [ ] Compare total allocation against manual baseline (must be within ±20%)
- [ ] Document change in STEP_7_TO_13_CHANGELOG.md

---

## Part G: Current Step 7-8 Enhancement Validation

### Step 7 Eligibility Enhancement - Validation

| Requirement | Status | Evidence | Risk |
|-------------|--------|----------|------|
| ✅ E-01: Sell-through focus | PARTIAL | Eligibility improves recommendation quality | LOW |
| ⚠️ E-04: Core subcategories | AT RISK | Climate filtering may exclude core products | **HIGH** |
| ✅ I-01: Explainability | MET | `eligibility_reason` column added | LOW |
| ✅ I-02: Guidance | MET | Clear ELIGIBLE/INELIGIBLE/UNKNOWN status | LOW |

**VERDICT:** Step 7 enhancement is **AT RISK** due to potential filtering of core subcategories.

**REQUIRED ACTION:** Add core subcategory override to eligibility logic.

### Step 8 Eligibility-Based Filtering - Validation

| Requirement | Status | Evidence | Risk |
|-------------|--------|----------|------|
| ✅ Business logic preserved | MET | Z-score formula unchanged | LOW |
| ✅ I-01: Explainability | MET | `eligibility_filtered` column added | LOW |
| ⚠️ E-05: ±20% range | NOT CHECKED | No cap on recommendations | MEDIUM |
| ⚠️ I-05: Core products | INHERITED | Depends on Step 7 eligibility | **HIGH** |

**VERDICT:** Step 8 enhancement is **CONDITIONALLY OK** - depends on Step 7 fix.

---

## Part H: Ongoing Review Mode

I will remain in **ACTIVE REVIEW MODE** for all future Step 7–13 changes.

For every proposed or implemented change, I will:

1. **Check** if it deviates from ANY known customer requirement
2. **Explicitly state:**
   - ✅ Which requirements are satisfied
   - ⚠️ Which requirements are at risk
   - ❌ Which requirements are violated (if any)
3. **If deviation exists:**
   - Explain WHY it is a deviation
   - Propose a concrete alternative that stays within the requirement boundary

---

## Appendix: Source Documents

| Document | Location | Key Content |
|----------|----------|-------------|
| FF Contract | `docs/Fast Fish Meeting History/FF contract...md` | Original requirements |
| Nov 25 Meeting | `docs/Fast Fish Meeting History/Fast Fish Meeting NOV 25...md` | Business feedback |
| WeChat Issues | `docs/Fast Fish Meeting History/fast fish wechat issues...md` | Operational issues |
| In-Person Takeaways | `docs/Fast Fish Meeting History/Key takeaway...txt` | Priority tasks |
| Discussion Points | `docs/Fast Fish Meeting History/Fast Fish meeting discussion points.txt` | Detailed checklist |

---

*Document prepared for Fast Fish Demand Forecasting Project*  
*Review Mode: ACTIVE for Step 7–13 lifecycle*
