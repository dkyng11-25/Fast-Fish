# Step 13 Change Proposal and Rationale

## Executive Summary

Constrain `src/step13_consolidate_spu_rules.py` to be a pure consolidation and data-quality step. Eliminate synthetic enrichments (random variability, defaulted gender/location/seasonality, synthetic clusters, fabricated prices/ratios) and avoid creating derived suggestions from summaries. Keep period-aware outputs and manifest registration. This prevents Step 14–style issues: seasonality bias, incorrect gender defaults, synthetic data, and misleading investment/volume signals.

## What’s Good (keep)
- Period-aware CLI and manifest registration (`get_current_period`, `get_period_label`)
- Robust file resolution with legacy fallbacks for rule outputs
- Left-as-NA investment when `unit_price` absent (no silent zeroing)
- Duplicate removal and column standardization prior to aggregation
- Detailed SPU-level consolidation plus backward-compatible store-level summary

## Gaps and Risks (why this matters)
1) Synthetic enrichments inside consolidation
- Randomness (`np.random.uniform`, synthetic cluster temperatures/elevations)
- Synthetic clusters when cluster file is missing
- Defaulted fields like `gender_mix = 'UNISEX'`, `seasonality_factor = 'NEUTRAL'`, price tiers from hardcoded maps
- “Enhanced default ratios” and store-hash variability when real sales are unavailable
- Risk: Reintroduces Step 14 failures (#2 incorrect gender, #3 synthetic data, #1 seasonality distortions) into a step that should be mechanical.

2) Suggestion fabrication from summaries
- Creation of `ALL_RULES_FILE` from store-level totals with placeholder `unit_price = 100` and generic explanation
- Risk: Invents items not sourced from rules; downstream may misinterpret as validated suggestions (#3 synthetic data, #4 unrealistic volumes).

3) Output path inconsistency for fashion file
- `FASHION_ENHANCED_FILE` is under `script_dir/output` while other outputs use project `output/`
- Risk: Files spread across `src/output` vs project `output/` causing confusion and missed inputs.

4) Seasonality/gender/location fields
- Defaults injected when missing; included in trend/granular outputs
- Risk: Step 14 issues (#1 seasonality bias, #2 gender) propagate downstream when missing data should stay NA.

5) Price/ratio synthesis in trend utilities
- Price tiers and unit prices derived from fixed maps and variability; fashion ratios defaulted with variability
- Risk: Misleading investment and trend analytics (#3 synthetic).

## Required Changes

- Consolidation-only contract
  - Run only: load rule outputs → standardize columns → deduplicate → optional cluster/subcategory joins (real data only) → aggregate → write outputs.
  - Disable/gate non-essential generators by default: `generate_fashion_enhanced_suggestions`, `generate_comprehensive_trend_suggestions`, `generate_granular_trend_data`.
  - If kept, they must operate on real inputs only and produce NA when inputs are missing; no randomness or hardcoded price/seasonality/gender defaults.

- Remove synthetic defaults and randomness
  - Delete or guard code paths that set: `gender_mix`, `seasonality_factor`, `dominant_seasonality`, `price_tier`, synthetic `unit_price`, variable `spu_count_fashion` by randomness, synthetic cluster IDs and random weather/elevation.
  - Where needed, carry NA; do not backfill with fabricated values.

- Cluster handling
  - Use real clustering results when available (`output/clustering_results_spu.csv`).
  - If absent, leave `cluster` as NA; do not synthesize from store codes.

- Fashion ratios and seasonality
  - Compute fashion ratios only from real sales when available; else omit columns (leave NA). Remove “enhanced defaults” and store-hash variability.
  - Do not compute or inject seasonality labels here; if required, must come from upstream validated data.

- Investment semantics
  - Keep `investment_required = quantity_change * unit_price` only when both are present and numeric; otherwise NA.
  - Never set `investment_required` to 0 as a fallback.

- Stop fabricating `ALL_RULES_FILE` from summaries
  - Do not generate `output/all_rule_suggestions.csv` from store-level totals with placeholder prices.
  - If a consolidated suggestion list is required, it must be a union of real per-SPU suggestions from rules 7–12, not derived.

- Output paths
  - Align `FASHION_ENHANCED_FILE` path with the project `output/` directory (consistent with other outputs).

- Diagnostics and safeguards
  - Log NA rates for key columns after consolidation (`str_code`, `spu_code`, `recommended_quantity_change`, `investment_required`).
  - Log which rule files were actually used (including legacy fallback resolution).
  - For trend utilities (if gated on), log that they are disabled by default in production.

## Acceptance Criteria
- No synthetic data generation in Step 13: no randomness, no synthetic clusters, no default gender/location/seasonality, no fabricated prices/tiers/ratios.
- `ALL_RULES_FILE` is not created from store summaries; only real SPU-level suggestions are consolidated.
- `investment_required` remains NA unless both operands are present.
- `cluster` remains NA if clustering file is missing; never synthesized.
- `FASHION_ENHANCED_FILE` (if produced at all) writes to project `output/` path.
- Consolidation succeeds when any subset of rules 7–12 exists; missing files are logged, not fatal.
- Period-labeled detailed and corrected outputs are written and registered in manifest as today.

## Test Plan
- Unit tests
  - Synthetic-off: assert no columns introduced by trend utilities when disabled; no `gender_mix`, `dominant_seasonality`, synthetic `unit_price` appear unless present upstream.
  - Investment NA semantics: with missing `unit_price`, `investment_required` is NA, not 0.
  - Cluster NA: remove clustering file → `cluster` col exists but contains NA only; no synthetic values.
  - Path consistency: verify `fashion_enhanced_suggestions.csv` (if enabled) lives under project `output/`, not `src/output/`.
- Integration tests
  - Run with only a subset of rule files present; verify consolidation completes with logs listing used files and NA diagnostics.
  - Verify manifest registration records period info and file sizes for detailed and corrected outputs.
  - Confirm no `all_rule_suggestions.csv` is produced from store summaries.

## Rollout
- Ship behind flags to keep compatibility: trend/enhancement utilities disabled by default; enable only for exploratory runs.
- Validate on recent periods (summer and August) and confirm no synthetic columns appear; verify NA diagnostics and manifest entries.
- Monitor for downstream reliance on previously fabricated files; update downstream steps if needed to consume only real, per-SPU suggestions.

## Backward Compatibility
- Consolidation outputs (detailed SPU and store-level CSVs) remain, but no synthetic enrichments are added.
- If any downstream expects `all_rule_suggestions.csv` fabricated from summaries, migrate it to consume the detailed SPU consolidated file instead.

## References
- Production file: `src/step13_consolidate_spu_rules.py`
- Reference file: `backup-boris-code/step13_consolidate_spu_rules.py`
- Related steps: 7–12 outputs consumed; Step 14 sensitivity to gender/seasonality/synthetic data
