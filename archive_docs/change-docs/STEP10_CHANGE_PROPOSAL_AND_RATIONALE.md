# Step 10 Change Proposal and Rationale

## Executive Summary

Update `src/step10_spu_assortment_optimization.py` to remove synthetic estimations and ground reductions in real unit quantities and defensible unit prices, enforce realistic volumes, and keep seasonal/gender/location handling compliant. These changes prevent Step 14–type issues (seasonality bias, incorrect gender defaults, synthetic data, unrealistic volumes, and location bias).

## What’s Good (keep)
- Period-aware, labeled outputs and manifest registration.
- August seasonal blending with explicit recent+seasonal files; July A+B recent fallback.
- Left-join + diagnostics for clusters; preserves unmatched rows.
- Safe JSON parsing, debug-limit, optional Fast Fish skip.
- NA-preserving blended sums.

## Gaps to Fix and Why

1) Replace sales/price heuristics with real unit quantities
- Problem: Reductions use `spu_sales / estimated_unit_price` (estimated from sales/2) → synthetic quantities and prices.
- Fix: Join real SPU-level quantities and compute unit prices from amount/quantity.
  - quantity = base_sal_qty + fashion_sal_qty (preferred) or `sal_qty` fallback.
  - unit_price = total_amount / quantity (NA if quantity ≤ 0); no synthetic price clamps.
- Why: Eliminates synthetic inflation; aligns with Steps 7–9; produces realistic magnitudes.

2) Apply SCALING_FACTOR consistently
- Problem: Recommendation text is “units/15-days” but current math isn’t explicitly scaled to `TARGET_PERIOD_DAYS`.
- Fix: Scale `current_quantity` and `recommended_quantity_change` to the target period.
- Why: Ensures outputs are period-correct and comparable.

3) Enforce a per-store cap on SPU reductions
- Problem: Can emit hundreds of SPUs per store under broad overcapacity.
- Fix: Keep at most `MAX_TOTAL_ADJUSTMENTS_PER_STORE` per `str_code` after validation, prioritized by:
  1. sell_through_improvement (desc, when available)
  2. overcapacity severity (excess_spu_count, overcapacity%)
  3. absolute quantity reduction (desc)
- Why: Keeps recommendations actionable and realistic.

4) Fast Fish validator semantics and clamping
- Problem: Passing unit quantities as “SPU counts” may misalign semantics; unbounded values can distort projections.
- Fix: Confirm contract:
  - If validator expects SKU counts: use 1→0 (per SPU reduction) as counts.
  - If it supports unit quantities: pass integerized units, clamped (e.g., 0–100).
  - Skip when critical fields are NA; do not synthesize defaults.
- Why: Ensures validation meaningfully reflects the action being proposed.

5) Robust gender/location handling (no synthetic defaults)
- Problem: Direct indexing (e.g., `row['sex_name']`) risks KeyErrors and encourages synthetic defaults.
- Fix: Use `row.get(...)` and carry NA; do not inject blanket constants. Exclude missing dims from grouping/logic; log missingness.
- Why: Avoids Step 14’s “mostly unisex” and location bias.

6) Seasonal blending discipline and explicit logging
- Problem: Seasonal blending is optional; need policy for autumn.
- Fix: For August/autumn planning, require `--seasonal-blending` (or implicit month check). Log recent and seasonal file paths and weights; log fallbacks if seasonal files missing.
- Why: Prevents summer-dominated recommendations; improves auditability.

7) Diagnostics and outputs
- Add logs for: quantity join coverage (NA counts), unit price NA counts, per-store cap trimming counts, and reduction distribution (min/median/max).
- Keep period-labeled outputs and manifest entries as-is.

## Acceptance Criteria
- Real quantities joined (or job fails with clear message); no sales/2 price heuristics.
- Quantities and reductions are scaled to `TARGET_PERIOD_DAYS`; text matches math.
- Per-store recommendations ≤ `MAX_TOTAL_ADJUSTMENTS_PER_STORE` after validation.
- Validator inputs aligned to contract; values clamped; NA cases skipped and annotated in logs.
- No synthetic gender/location defaults; missingness logged.
- Seasonal blending required for autumn; all paths and weights logged.

## Test Plan
- Quantity sourcing: with base/fashion qty present; with `sal_qty` only; none present → fail-fast with period + file candidates.
- Period scaling: verify reductions and text reflect 15-day scaling.
- Cap logic: construct store with 50 reducible SPUs → only top N remain; log trimming.
- Validator: confirm counts vs units path; ensure clamping/skips.
- Seasonal: August run with and without seasonal files → logs show source selection/fallback; outputs stable.

## Rollout
- Implement changes behind existing CLI/consts; no interface breaks.
- Validate on staging (summer and August periods) with full logs.
- Deploy; monitor logs for quantity/price NA rates, seasonal source paths, cap trimming, validator summaries.

## Backward Compatibility
- Inputs: Requires SPU-level quantity fields (or fail-fast); removes reliance on synthetic price/quantity.
- Outputs: Columns unchanged; values reflect real units and capping; summaries remain labeled and registered.


