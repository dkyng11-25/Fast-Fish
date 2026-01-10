# Steps 7 and 8 Change Proposal and Rationale

## Executive Summary

This document proposes targeted edits to `step8_imbalanced_rule.py` and documents the current status of `step7_missing_category_rule.py`. The goals are to:

- Prevent regressions related to seasonality, gender assignment, synthetic data, unrealistic recommendation volumes, and location bias that were previously observed in Step 14.
- Ensure unit-quantity–driven logic is strictly based on real quantity fields, not inferred or synthetic values.
- Make outputs auditable, period-aware, and realistic by enforcing per-store caps and using constrained recommendations.

Step 7 requires no functional change at this time; Step 8 requires specific edits detailed below.

## Scope

- In-scope: `src/step8_imbalanced_rule.py` (edits), `src/step7_missing_category_rule.py` (documentation of current position; optional diagnostics only).
- Out-of-scope: Code modifications to other steps; however, cross-step implications (including Step 14) are called out to ensure alignment.

## Background and Risks

Recent issues (most pronounced in Step 14) included:

1. Lack of autumn season data (summer/spring dominated inputs).
2. Incorrect gender assignments (defaulting to unisex).
3. Significant synthetic data introduced (over-use of fill defaults and synthetic dimensions).
4. Unrealistic quantity recommendations (hundreds of SPUs per store).
5. Display location bias (front/back-only recommendations).
6. Partial mitigations exist, but ongoing vigilance is required.

The production Step 8 already improves period-awareness, blending, NA preservation, and diagnostics. The remaining risks are addressed via the changes below.

## Step 7: Current Position and Optional Enhancements

Production file: `src/step7_missing_category_rule.py`

- Status: Functionally robust. Uses `src.config` for period-aware I/O, left-join diagnostics, NA preservation, optional sell-through validation, and period-labeled outputs.
- Keep as-is. Optional low-risk enhancements (not required):
  - Log blended data composition when seasonal blending is explicitly enabled.
  - Log top category names from the chosen sales dataset for transparency.

No mandatory edits proposed for Step 7.

## Step 8: Required Changes

Production file: `src/step8_imbalanced_rule.py`

### 1) Enforce real unit quantities; derive conservatively or fail fast

- Problem: The loader validates only `['str_code', 'spu_code', 'spu_sales_amt']`, yet downstream uses `quantity` as a core metric. If `quantity` is absent, logic can fail or silently produce NaNs.
- Change:
  - After loading `quantity_df` in `load_data()`, if `quantity` is missing, try to derive strictly from actual quantity fields:
    - If both `base_sal_qty` and `fashion_sal_qty` exist, set `quantity = base_sal_qty + fashion_sal_qty`.
    - Else if `sal_qty` exists, set `quantity = sal_qty`.
    - Else: raise a clear error including period label and file path candidates, instructing to supply a dataset with real quantities.
  - Preserve NA; do not backfill with zeros or infer quantities from monetary values to avoid synthetic artifacts.
- Why: Prevents synthetic data introduction (Risk #3) and ensures all subsequent quantity-based rebalancing is grounded in real units.

### 2) Remove synthetic defaults for season, gender, and display location

- Problem: The SPU branch applies blanket defaults:
  - `season_name = 'ALL_SEASONS'`, `sex_name = 'UNISEX'`, `display_location_name = 'ALL_LOCATIONS'`.
  - This creates synthetic dimensions and can recreate Step 14’s incorrect gender assignment (Risk #2) and obscure seasonality (Risk #1).
- Change:
  - Remove blanket defaults. Instead:
    - Use these fields only if they exist in the source; otherwise, omit them from the grouping key.
    - If needed, map `big_class_name = cate_name` only when `cate_name` exists.
  - Build grouping keys dynamically from available columns (see Change 3).
- Why: Eliminates synthetic dimensions (Risk #3), avoids incorrect gender assignment (Risk #2), and respects actual data availability.

### 3) Build grouping keys from real, available columns only

- Problem: Current key includes columns that may be absent, prompting synthetic defaults.
- Change:
  - Compute `available_grouping_columns = [c for c in CURRENT_CONFIG['grouping_columns'] if c in data_with_clusters.columns]`.
  - Set `category_key` from `available_grouping_columns` only.
  - If none of the optional dimensions exist, fall back to a minimal real key (`['sub_cate_name', 'sty_code']` when present) to preserve analytical signal.
- Why: Prevents forced synthetic labels, maintains analytical fidelity, and stabilizes Z-Score grouping.

### 4) Enforce a per-store cap on recommendations

- Problem: Without a cap, output can include hundreds of SPUs per store (Risk #4).
- Change:
  - After generating `imbalanced` cases and applying sell-through validation, limit per-store recommendations to `MAX_TOTAL_ADJUSTMENTS_PER_STORE`.
  - Selection order per store:
    1. Highest `sell_through_improvement` (if present), then
    2. Highest `abs(z_score)`, then
    3. Highest `abs(constrained_quantity_adjustment)`.
  - Drop over-cap rows (do not just flip flags) before passing to `apply_imbalanced_rule()`.
  - Log the number of stores trimmed and total dropped cases.
- Why: Ensures realistic volumes (Risk #4) and better business prioritization.

### 5) Align recommended quantity with constrained recommendation

- Problem: `recommended_quantity_change` is currently set from pre-constrained `quantity_adjustment_needed`.
- Change:
  - Set `recommended_quantity_change = constrained_quantity_adjustment`.
  - Ensure `recommendation_text` uses the constrained value (already calculated but confirm usage).
- Why: Keeps outputs consistent with enforced constraints, prevents over-promising inventory moves.

### 6) Validate Fast Fish API semantics and clamp inputs

- Problem: Validator parameters use unit quantities as `current_spu_count` and `recommended_spu_count`. If the validator expects SKU counts, this may misrepresent intent.
- Change:
  - Clamp both `current_qty` and `target_qty` to realistic integer bounds (e.g., `[0, 100]`) when calling the validator.
  - If either value is NA after all derivations, skip the case (do not synthesize values). Ensure this skip is consistently applied across branches.
  - Confirm validator semantics (SKU count vs unit quantity). If it expects counts of SKUs, pass counts; otherwise document that unit quantities are used by design.
- Why: Avoids unstable projections and aligns with Fast Fish intent.

### 7) Maintain NA-preserving numerics and diagnostics

- Problem: Overuse of `.fillna(0)` historically introduced synthetic data.
- Change:
  - Keep current NA-preserving coercions and avoid introducing `.fillna(0)` on analytic fields (`quantity`, `spu_sales_amt`, Z-score inputs).
  - Add diagnostics after quantity derivation: NA counts for `quantity` and `spu_sales_amt`.
- Why: Prevents synthetic inflation (Risk #3) and improves debuggability.

### 8) Seasonal blending continuity and logging

- Current: Step 8 blends August recommendations using prior-year Q3 data with fallbacks.
- Change: No functional change; add explicit logs for missing seasonal files listing exact paths checked.
- Why: Improves auditability, addresses Risk #1 (visibility into seasonal coverage).

### 9) Outputs and period labeling

- Current: Period-labeled outputs are in place; empty artifacts are created when needed.
- Change: No change required.
- Why: Already addresses auditability and repeatability.

## Acceptance Criteria

1. Data integrity
   - If `quantity` cannot be sourced from `base_sal_qty + fashion_sal_qty` or `sal_qty`, the job fails with a clear error (file + period details). No synthetic derivations from monetary amounts.
   - NA diagnostics for `quantity` and `spu_sales_amt` are logged.

2. Realism of recommendations
   - Per-store recommendations are capped at `MAX_TOTAL_ADJUSTMENTS_PER_STORE` post-validation.
   - `recommended_quantity_change` equals `constrained_quantity_adjustment`.
   - `recommendation_text` reflects constrained quantities.

3. Dimensional correctness
   - No synthetic default assignments for `season_name`, `sex_name`, or `display_location_name`.
   - Grouping keys use only columns that actually exist; fallback to minimal real key where necessary.

4. Seasonal coverage
   - For August, logs explicitly show whether seasonal 2024 Q3 files were used or whether the job fell back to recent-only data, with paths reported.

5. Validator semantics
   - Inputs to validator are clamped and integerized; NA cases are skipped (logged). If SKU-count semantics differ, document the chosen approach and rationale.

## Test Plan

- Unit-level checks (offline):
  - Supply `quantity_df` variants: with `quantity`, with `base_sal_qty`/`fashion_sal_qty`, with `sal_qty` only, and with none (expect fail-fast).
  - Verify grouping key construction with/without optional columns. Ensure no synthetic default columns are created.
  - Validate per-store cap logic on crafted data (e.g., 50 imbalanced cases per store) with and without `sell_through_improvement` present.

- Integration checks:
  - Run Step 8 in August mode with and without seasonal files present; verify logging and blended behavior.
  - Confirm outputs are period-labeled and that empty artifacts are generated when applicable.

- Regression checks vs Step 14 failure modes:
  - Confirm no blanket `UNISEX` or `ALL_SEASONS` appears in outputs unless sourced from input data.
  - Confirm per-store recommendation counts never exceed the cap.
  - Confirm display location is not hard-coded; use only when present in inputs.

## Rollout Plan

1. Implement Step 8 changes behind existing constants (no new flags required). Keep `MAX_TOTAL_ADJUSTMENTS_PER_STORE` programmable via constant or env variable if desired.
2. Validate in a staging run across representative periods (summer and autumn), capture logs and output metrics.
3. Merge and release; monitor the first production run’s logs for:
   - Quantity derivation diagnostics
   - Seasonal blending path messages
   - Per-store trimming counts
4. If validator semantics need adjustment (SKU vs units), plan a follow-up iteration with minimal blast radius.

## Backward Compatibility and Data Contracts

- Inputs:
  - `quantity_df` must include one of: `quantity`, or both `base_sal_qty`/`fashion_sal_qty`, or `sal_qty`.
  - `spu_sales_amt` remains required.
- Outputs:
  - Columns remain as in production with corrected values:
    - `recommended_quantity_change` reflects constrained values.
    - Counts and sums respect per-store caps.
- Behavior:
  - Fail-fast if real quantities are absent rather than synthesizing quantities from monetary values.

## Implementation Notes (for developers)

- `load_data()`:
  - Derive `quantity` as described; log NA counts; raise error if unsatisfied.
- `prepare_allocation_data()`:
  - Remove blanket defaults for season/sex/display_location; compute `available_grouping_columns`; build `category_key` accordingly; apply minimal fallback key only if needed.
- `identify_imbalanced_cases()`:
  - Ensure `recommended_quantity_change = constrained_quantity_adjustment`.
  - Clamp validator inputs; skip NA cases uniformly; sort by `sell_through_improvement` then `abs(z_score)` then `abs(constrained_quantity_adjustment)` for prioritization.
  - Apply per-store cap and log trimming stats.
- `apply_imbalanced_rule()` and `save_results()` remain unchanged besides downstream effects of filtered/capped cases.

## Monitoring & Reporting

- Add summary logs:
  - Quantity derivation source used and NA stats.
  - Seasonal blending status and file paths used.
  - Number of stores trimmed by cap and total cases dropped.
  - Distribution of `recommended_quantity_change` (e.g., min/median/max) for sanity.

## Appendix

- Key files:
  - `src/step7_missing_category_rule.py` (no changes required)
  - `src/step8_imbalanced_rule.py` (changes as above)

- Environment/config references used by Step 8:
  - `initialize_pipeline_config`, `get_current_period`, `get_period_label`, `get_api_data_files`, `get_output_files` from `src.config`
  - Env overrides: `ANALYSIS_LEVEL`, `PIPELINE_TARGET_YYYYMM`, `PIPELINE_TARGET_PERIOD`

- Required columns (Step 8):
  - Planning (SPU mode): `['str_code', 'sty_sal_amt']` plus available grouping columns
  - Quantity: `['str_code', 'spu_code', 'spu_sales_amt']` and one of: `quantity`, `sal_qty`, or both `base_sal_qty` and `fashion_sal_qty`


