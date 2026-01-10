# Step 18 Change Proposal and Rationale

## Executive Summary

Refactor `src/step18_validate_results.py` to compute sell-through rates using real, period-aligned historical baselines and real store-grouping, avoid synthetic fallbacks, and preserve dimensional integrity from upstream steps. Eliminate modulo/hash grouping and revenue-based unit inferences. Use NA-preserving math, maintain count-versus-unit semantics, and register period-aware outputs. This prevents recurrence of Step 14 issues (seasonality bias, incorrect gender/location defaults, synthetic data, unrealistic volumes) at validation time.

## What’s Good (keep)
- Period-aware CLI and period-labeled output filename
- Clear sell-through rate concept using SPU-store-days inventory vs sales
- Uses Step 17 augmented file as the input; registers outputs in manifest

## Gaps and Risks (and why they matter)
1) Synthetic grouping for historical aggregation
- `create_store_groups` uses hash/modulo to assign store groups for historical data.
- Risk: Invented clusters distort store group denominators and mismatch Step 14/15 grouping (Step 14 issue #3).

2) Hard-coded historical window (May 2025)
- Baseline always filtered to 202505; Step 15 is period-aware (e.g., 202409A).
- Risk: Seasonality mismatch and summer bias (Step 14 issue #1); invalid YoY comparisons.

3) Synthetic numerical fallbacks
- When historical match fails, code estimates daily units from `Avg_Sales_Per_SPU` via ¥-based heuristic.
- Risk: Reintroduces synthetic unit inferences (Step 14 issue #3), producing unrealistic rates (#4).

4) Category/subcategory parsing fragility
- Parses `Target_Style_Tags` manually across formats; brittle and may misclassify categories.
- Risk: Misjoins to historical aggregates, yielding incorrect rates.

5) NA handling and denominator safety
- Initializes zeros and computes percentages unconditionally when available; may mask missing data.
- Risk: False precision; divide-by-zero or misleading rates.

6) Confidence/temperature defaults
- Defaults `Confidence_Score` and `Temperature_Suitability` from potentially synthetic trending inputs.
- Risk: Misleading downstream signals (Step 14 issues #2/#5/#3).

## Required Changes

- Use real clusters and period-aligned historical baselines
  - Replace `create_store_groups` modulo logic. If `Store_Group_Name` exists in Step 17 input (from Step 14 clusters), use it directly. For historical baselines, consume Step 15 outputs (historical reference and/or YOY) keyed by the same baseline label (e.g., 202409A).
  - If clusters missing, skip sell-through computation for affected rows and log counts; do not synthesize.

- Source historical from Step 15
  - Prefer Step 15 `historical_reference_{baseline}` to obtain `historical_spu_count`, `historical_total_quantity`, and store counts by `Store_Group_Name × Category × Subcategory`.
  - Compute `avg_daily_spus_sold_per_store = historical_total_quantity / (stores_in_group × PERIOD_DAYS)` using the correct PERIOD_DAYS for the baseline period.
  - If Step 15 artifacts are unavailable, fail with a clear error or run historical-only diagnostics; do not hard-code 202505.

- Strict NA-preserving calculation
  - Only compute Sell_Through_Rate when both numerator (SPU-store-days sales) and denominator (SPU-store-days inventory) are positive and defined.
  - Otherwise leave `Sell_Through_Rate` as NA and log counts of skipped rows. Cap at 100 when computed.

- Preserve upstream dimensional integrity
  - Treat Step 17 `Target_Style_Tags` as authoritative. Do not reformat or enhance season/gender/location here; parse minimally for category/subcategory, with robust parsing that falls back to Step 17 category columns if available.

- Remove synthetic numerical fallbacks
  - Drop revenue→unit heuristics (`Avg_Sales_Per_SPU`/100, etc.). If historical join fails, keep numerator NA.
  - Avoid default 0s for trend-derived fields; prefer NA and explain in logs.

- Visibility fields grounded in real data
  - `Temperature_Suitability`: populate only when a real weather/trend score exists and provenance is known; otherwise set to `Unknown`.
  - `Confidence_Score`: if `cluster_trend_confidence` exists and is numeric, use it; otherwise NA (not hard-coded 50).
  - `Capacity_Utilization`: compute only if both numerator and a real denominator (e.g., cluster store count) exist; otherwise NA.

- Period-aware manifest alignment
  - Resolve Step 17 input via period-specific manifest key; if mismatch with `--target-period`, fail rather than silently using generic keys.
  - Optionally log the matching of baseline from Step 15 to confirm seasonality alignment.

## Acceptance Criteria
- No modulo/hash grouping anywhere; store groups derive from real clusters and Step 14/15 outputs.
- Historical baseline is period-aligned via Step 15; no hard-coded May filters.
- No revenue→unit heuristics; missing historical joins result in NA sell-through rates.
- Sell-through rates are computed only with valid denominators; NA-preserving with clear logging; capped at 100%.
- `Target_Style_Tags` and dimensional fields are not defaulted or altered; no forced summer/unisex/front values.
- Visibility fields (`Temperature_Suitability`, `Confidence_Score`, `Capacity_Utilization`) respect data provenance; Unknown/NA when inputs unavailable.
- Output is saved with the correct period label and registered with metadata indicating sell-through metrics present.

## Test Plan
- Unit tests
  - Grouping provenance: remove cluster info → sell-through computation skipped with logs; no synthetic groups created.
  - Baseline alignment: provide Step 15 `historical_reference_{baseline}` and ensure it is selected; if missing, step fails clearly.
  - NA safety: rows with missing numerator/denominator remain NA; no divide-by-zero; cap at 100 verified.
  - Parsing robustness: when `Target_Style_Tags` is 5-field list vs pipe format, category/subcategory parsed correctly; fallback to explicit columns if present.
  - Visibility provenance: with no trend inputs, `Temperature_Suitability` is `Unknown` and `Confidence_Score` is NA.

- Integration tests
  - End-to-end 202509A target with 202409A baseline: rates computed for rows with matched historical; others NA; logs summarize counts.
  - Mismatch period in manifest: step errors with guidance; no silent fallbacks.

## Rollout
- Implement manifest alignment and historical sourcing first; gate removal of synthetic fallbacks behind a flag if needed for staged rollout.
- Validate across multiple periods (summer vs autumn) to confirm seasonality stability.
- Monitor logs for historical match rates, NA rates in sell-through, and any capacity/temperature/confidence derivations.

## Backward Compatibility
- Output columns preserved; more NA where historical data missing rather than synthetic defaults.
- Rates may decrease in coverage but increase in reliability. Downstream readers should handle NA appropriately.

## References
- Production: `src/step18_validate_results.py`
- Reference: `backup-boris-code/step18_validate_results.py`
- Upstream: Step 17 augmented recommendations; Step 15 historical reference/YOY outputs; Step 14 clustering/grouping
