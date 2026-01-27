# Step 7–13 Enhancement Changelog

> **Purpose:** Track all changes to Steps 7–13 for auditability and future catch-up  
> **Format:** Date | Step | File/Module | Rationale | Downstream Impact  
> **Last Updated:** 2026-01-27

---

## Changelog

### 2026-01-27 | Step 7 | Core Subcategory Override (CRITICAL FIX)

| Field | Value |
|-------|-------|
| **Date** | 2026-01-27 |
| **Step** | Step 7 (Missing SPU Rule) |
| **Files Modified** | `Evelyn/step7_step13/step7/eligibility_evaluator.py` |
| **Rationale** | **DEVIATION RISK IDENTIFIED:** Climate/season filtering could exclude core subcategories (Straight-Leg, Jogger, Tapered) which client explicitly requires to always be included (Req E-04, W-01, I-05) |
| **Change Summary** | Added `CORE_SUBCATEGORIES` list and `is_core_subcategory()` function. Core subcategories now ALWAYS return `ELIGIBLE` status regardless of climate/season matching. |
| **Client Requirement** | "Core styles for November should receive special attention" (WeChat Oct 2025) |
| **Downstream Impact** | Core subcategories will never be filtered out by eligibility logic in Steps 8-12 |

**Core Subcategories Protected:**
- 直筒裤 / Straight-Leg
- 束脚裤 / Jogger  
- 锥形裤 / Tapered

---

### 2026-01-27 | All Steps | Customer Requirements Extraction Document

| Field | Value |
|-------|-------|
| **Date** | 2026-01-27 |
| **Scope** | Steps 7-13 |
| **Files Added** | `Evelyn/step_7_to_step_13/CUSTOMER_REQUIREMENTS_EXTRACTION.md` |
| **Rationale** | Establish deviation guardrails based on comprehensive review of all Fast Fish meeting history documents |
| **Change Summary** | Created structured requirements document with timeline-based mapping, explicit/implicit requirements, prioritization logic, and step-specific guardrails |
| **Impact** | All future Step 7-13 changes must be validated against this document |

---

### 2026-01-24 | Step 7 | Eligibility Flag Introduction

| Field | Value |
|-------|-------|
| **Date** | 2026-01-24 |
| **Step** | Step 7 (Missing SPU Rule) |
| **Files Modified** | `Evelyn/step7_step13/step7/step7_missing_spu_time_aware.py` |
| **Files Added** | `Evelyn/step7_step13/step7/eligibility_evaluator.py` |
| **Rationale** | Step 7 implicitly evaluates SPU eligibility based on climate/season but does not surface this judgment explicitly. Downstream modules (especially Step 8) assume all SPUs are equally eligible, causing false imbalance signals. |
| **Change Summary** | Added explicit `eligibility_status` enum output at SPU × Store × Period level with values: `ELIGIBLE`, `INELIGIBLE`, `UNKNOWN` |
| **Downstream Impact** | Step 8 can now filter imbalance calculations to only include ELIGIBLE SPUs, reducing false-positive rebalancing recommendations |

**New Output Schema Columns:**
- `eligibility_status`: ELIGIBLE / INELIGIBLE / UNKNOWN
- `eligibility_reason`: Human-readable explanation of eligibility decision
- `climate_match`: Boolean - does SPU climate band match store temperature?
- `season_match`: Boolean - is SPU appropriate for current season phase?

---

### 2026-01-24 | Step 8 | Eligibility-Based Filtering

| Field | Value |
|-------|-------|
| **Date** | 2026-01-24 |
| **Step** | Step 8 (Imbalanced Allocation Rule) |
| **Files Added** | `Evelyn/step_7_to_step_13/step8/step8_imbalanced_eligibility_aware.py` |
| **Rationale** | Original Step 8 assumes all SPUs are valid candidates for imbalance comparison, causing structurally wrong z-scores and seasonally invalid rebalancing suggestions |
| **Change Summary** | Added eligibility-based filtering so only SPUs with `eligibility_status == ELIGIBLE` from Step 7 are included in peer comparison and z-score calculation |
| **What Changed** | WHO is included in imbalance calculation (filtering) |
| **What Did NOT Change** | Z-score formula, thresholds, business definitions |
| **Downstream Impact** | More accurate imbalance detection; reduced false-positive rebalancing recommendations |

---

### 2026-01-22 | Step 7 | Time-Aware & Climate-Aware Enhancement

| Field | Value |
|-------|-------|
| **Date** | 2026-01-22 |
| **Step** | Step 7 (Missing SPU Rule) |
| **Files Added** | `Evelyn/step7_step13/step7/step7_missing_spu_time_aware.py`, `climate_config.py` |
| **Rationale** | Original Step 7 is time-agnostic and climate-blind, recommending winter items in summer and vice versa |
| **Change Summary** | Added climate gate (temperature band matching) and time gate (season phase matching) as gating conditions |
| **Downstream Impact** | 58.8% reduction in false-positive recommendations on 202506A dataset |

---

## Pending Changes

| Step | Planned Change | Priority | Status |
|------|----------------|----------|--------|
| Step 9 | Eligibility-aware minimum threshold | Medium | Planned |
| Step 10 | Eligibility-aware overcapacity detection | Medium | Planned |
| Step 11 | Eligibility-aware missed sales opportunity | Medium | Planned |
| Step 12 | Eligibility-aware sales performance rule | Medium | Planned |
| Step 13 | Consolidation with eligibility metadata | High | Planned |

---

## Client Requirement Alignment

| Requirement | Status | Evidence |
|-------------|--------|----------|
| R4.4: Temperature-Aware Clustering | ✅ MET | Step 7 climate gate uses feels-like temperature |
| R3.3: Rationale Scoring | 🟡 PARTIAL | `eligibility_reason` provides explanation text |
| R1.1: Sell-Through Focus | 🟡 PARTIAL | Eligibility filtering improves recommendation quality |

---

## Version History

| Version | Date | Author | Summary |
|---------|------|--------|---------|
| 1.0 | 2026-01-22 | Data Pipeline Team | Initial time-aware enhancement |
| 1.1 | 2026-01-24 | Data Pipeline Team | Added explicit eligibility output |
| 1.2 | 2026-01-24 | Data Pipeline Team | Step 8 eligibility-based filtering |

---

*Changelog maintained for Fast Fish Demand Forecasting Pipeline*
