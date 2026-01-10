# Step 9 Change Proposal and Rationale

## Executive Summary

This document proposes targeted edits to `src/step9_below_minimum_rule.py` to eliminate synthetic data pathways, anchor recommendations in real unit quantities, keep outputs realistic, and align with Fast Fish sell-through principles. These changes directly address previously observed failure modes (notably from Step 14): seasonality gaps, incorrect gender defaults, synthetic data inflation, unrealistic recommendation volumes, and location bias.

## Current Strengths in Production

- Period-aware inputs/outputs using `src.config`, with period-labeled artifacts.
- Safe parsing of `sty_sal_amt` (no insecure `eval`).
- Left-join diagnostics with clusters; preserves unmatched rows.
- Optional seasonal blending (via CLI) for August planning.
- Fast Fish validation integrated; NA-preserving defaults when validator unavailable.
- SPU-level guardrails (min sales and min cluster size) to reduce noise.

## Gaps and Risks to Address

1) Synthetic style/quantity derivations
- Current logic derives `style_count` from monetary sales amounts, and computes “current/target quantity” from monetary values.
- Risk: Recreates synthetic data issues and magnifies values; not grounded in true units.

2) No per-store cap on SPU recommendations
- Risk: Hundreds of SPUs per store can be recommended, repeating the Step 14 symptom of unrealistic volume.

3) Validator input semantics
- Unit-like values derived from amounts are treated as counts in the validator call, potentially distorting sell-through predictions.

4) Investment reporting
- `unit_price` is set to NA; per-store sums use default behavior that can produce 0 rather than NA, misrepresenting unknown investment as zero.

5) Seasonality usage discipline
- Seasonal blending exists but is optional; for autumn planning runs, it should be used deliberately with explicit file-path logging.

6) Gender and display location defaults
- Better than Step 14 (no blanket constants), but fields default to empty strings when absent. We should avoid letting empty placeholders sneak into grouping/logic.

## Proposed Changes

### 1) Use real unit quantities; remove monetary proxies

- Replace the monetary-derived `style_count` and “quantity” calculations with unit-based metrics.
- Load SPU-level quantities from the API data (same source used in Step 8):
  - Prefer: `quantity = base_sal_qty + fashion_sal_qty` (SPU-level file).
  - Fallback: `sal_qty` (if provided by API at SPU-level).
  - If none exist: fail-fast with a clear error listing period and candidate files. Do not infer units from money.
- Rationale: Eliminates synthetic inflation, anchors recommendations to real units, keeps quantities comparable across stores and time.

Implementation guidance:
- After loading store config (planning) rows and expanding SPUs via `sty_sal_amt`, join real quantities by `['str_code', 'spu_code']` (map to `sty_code` nomenclature where necessary).
- Keep NA quantities as NA (no zero backfills). Log NA counts.

### 2) Define the “below minimum” metric on units, not money

- Replace `style_count` from `sal_amt/1000` with `unit_rate` such as:
  - Option A (simple): units per 15 days (`quantity_15d = quantity * SCALING_FACTOR`), and set a fixed minimum threshold `MINIMUM_UNIT_RATE`.
  - Option B (peer-normalized): ratio to cluster mean or target (e.g., `units_15d / cluster_mean_units_15d`) with a dimension-aware threshold.
- Keep current threshold semantics (single scalar) at first for minimal blast radius; document it as “minimum unit rate per 15 days”.
- Rationale: A unit-based minimum is interpretable and stable; normalizing to peer mean can be considered in a second iteration.

### 3) Compute positive increases using unit math only

- Define:
  - `current_units_15d = quantity * SCALING_FACTOR`.
  - `target_units_15d = max(current_units_15d, MINIMUM_UNIT_RATE)` or if using normalized metric: `cluster_mean_units_15d`.
  - `recommended_quantity_change = max(target_units_15d - current_units_15d, MIN_BOOST_QUANTITY)`.
- Keep the existing invariant: never negative, always non-zero positive when below minimum.
- Rationale: Ensures recommendations reflect real unit needs and remain positive.

### 4) Enforce a per-store cap on SPU recommendations

- After generating validated opportunities, enforce `MAX_TOTAL_ADJUSTMENTS_PER_STORE` across SPUs per store.
- Prioritize by:
  1. Highest `sell_through_improvement` (when available)
  2. Highest severity (issue_severity ordering: CRITICAL > HIGH > MEDIUM > LOW)
  3. Largest absolute `recommended_quantity_change`
- Drop excess rows (do not merely flip flags), and log trimming stats (stores affected, rows dropped).
- Rationale: Prevents unrealistic volumes and focuses on highest-impact actions.

### 5) Validator input semantics and bounds

- If the validator represents counts of SKUs: pass SKU counts rather than unit quantities (e.g., number of SPUs affected). For Step 9, we are recommending unit increases for specific SPUs; counts should likely be 1→1. Confirm contract.
- If validator is designed for unit quantities: clamp integerized quantities to a reasonable bound (e.g., 0–100) and document the use of unit quantities.
- Skip validation for rows with NA quantities; do not synthesize inputs.
- Rationale: Aligns validation semantics, avoids unrealistic or unstable projections.

### 6) Investment: preserve unknown explicitly

- Keep `unit_price` as NA unless a defensible source exists (e.g., store- or category-level average unit price from API-derived amounts/units in the same period).
- Aggregate investments using NA-aware sums with `min_count=1` semantics so totals remain NA if all inputs are unknown.
- Add diagnostics: count cases with known vs unknown price.
- Rationale: Avoids presenting zero as a false “known” total and maintains analytical integrity.

### 7) Seasonality discipline and logging

- For August/autumn planning flows, require `--seasonal-blending` with explicit `--seasonal-yyyymm/--seasonal-period/--seasonal-weight`.
- Log exact seasonal and recent file paths used; log fallback to recent-only when seasonal files are missing.
- Rationale: Prevents summer-only dominance and provides auditability.

### 8) Gender and display location handling

- Continue to propagate `sex_name` and `display_location_name` from source data when present.
- When missing, do not inject synthetic constants; carry NA and exclude from grouping. Record missingness diagnostics in logs.
- Rationale: Avoids incorrect mass “UNISEX” or biased location assumptions.

### 9) Outputs and diagnostics

- Maintain period-labeled outputs and backward-compatible unlabeled copies where needed.
- Add diagnostics to logs and summary markdown:
  - Quantity derivation source and NA counts.
  - Seasonal blending input paths and weights.
  - Count of stores trimmed by cap and number of rows trimmed.
  - Distribution of `recommended_quantity_change` (min/median/max).
  - Count of opportunities with known vs unknown `unit_price`.

## Acceptance Criteria

- No monetary-to-unit proxies remain for core metrics; quantities are sourced from real API unit fields or the job fails with a clear message.
- `recommended_quantity_change` is strictly positive where flagged; computed from unit quantities.
- Per-store recommendations are capped at `MAX_TOTAL_ADJUSTMENTS_PER_STORE` after sell-through filtering.
- Validator inputs are semantically aligned (counts vs units) and clamped to reasonable integer ranges; NA inputs are skipped.
- Investment totals reflect NA when prices are unknown (no silent zeroing).
- Seasonal blending is required for autumn planning with explicit file-path logging.
- No synthetic gender or location defaults are introduced; missingness is logged.

## Test Plan

Unit tests (offline):
- Quantity sourcing:
  - Case A: quantities available via `base_sal_qty` + `fashion_sal_qty` → derived `quantity` equals sum.
  - Case B: only `sal_qty` available → `quantity = sal_qty`.
  - Case C: no quantity fields → fail-fast with message including period and file candidates.
- Recommendation math:
  - Verify positive non-zero recommendations when below threshold; zero recommendations when above.
  - Verify `recommended_quantity_change` uses unit math only.
- Cap logic:
  - Construct a store with 50 flagged SPUs; confirm only top N remain and trimming logs appear.
- Investment aggregation:
  - All NA unit prices → store totals NA; mix of known/unknown → totals reflect known portion; include counts.
- Validator semantics:
  - Confirm clamping and skipping behavior; if counts expected, switch to 1→1 for SPU recommendations.

Integration tests:
- August run with and without seasonal files; confirm blending logs, fallbacks, and outputs.
- Pipeline compatibility: downstream steps consume period-labeled outputs; columns preserved.

## Rollout Plan

1. Implement changes behind existing constants and CLI flags; do not alter interfaces unexpectedly.
2. Validate on staging periods (summer and August) with full logs.
3. Release to production; monitor logs for quantity NA counts, seasonal file usage, cap trimming, and validator summaries.
4. If validator contract requires counts only, follow-up iteration to pass SKU counts and document rationale.

## Backward Compatibility

- Inputs: Requires SPU-level quantity fields. If absent, job fails clearly rather than synthesizing units. This is intentional to prevent reintroduction of synthetic data.
- Outputs: Column names retained; `recommended_quantity_change` now unit-based and aligns with positive-only rule. Investment totals may show NA rather than 0 when unit prices are unknown.

## Appendix

- Production file: `src/step9_below_minimum_rule.py`
- Related references: `src/step8_imbalanced_rule.py` (quantity sourcing and seasonal blending patterns)
- Config functions used: `initialize_pipeline_config`, `get_current_period`, `get_api_data_files`, `get_output_files`, `get_period_label`


