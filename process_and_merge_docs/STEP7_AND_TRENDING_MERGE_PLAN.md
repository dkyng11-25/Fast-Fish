### Scope

- **Targets**: `src/step7_missing_category_rule.py`, `src/config.py`, `src/sell_through_validator.py`, and reference `backup-boris-code/ProducMixClustering_spu_clustering_rules_visualization-copy-spu-enhanced-pipeline-august-2025/trending_analysis/**` with associated step-17 drivers.
- **Non-goals**: Changing unrelated steps, data schemas, or pipeline entrypoints beyond wiring trending engines.

### Principles

- **Safety-first**: Prefer additive, gated changes; preserve existing behavior when optional modules are unavailable.
- **Determinism**: All file paths resolved via `src.config` with explicit `yyyymm`/`period` to avoid drift.
- **Compatibility**: Maintain legacy outputs where present; avoid breaking downstream steps (Step 13/14).
- **Small surface area**: Consolidate logic in one canonical step per concern (Step 7, Step 17), expose libraries for the rest.

### Current State Snapshot (relevant deltas)

- Root Step 7 includes: period-aware file resolution via `src.config`, safe merges, Fast Fish sell-through validation, optional ROI gating, seasonal blending, rich period-labeled outputs.
- Reference Step 7 is simpler (no sell-through gate), looser joins, and less robust file resolution.
- Reference includes a full `trending_analysis` module and multiple step-17 variants (engines + drivers). Root has a single `step17_augment_recommendations.py` entrypoint.

### Risks and Mitigations

- **Validator unavailability → zero opportunities**: When Fast Fish cannot initialize, root Step 7 will approve none by design. Mitigation: keep the strict gate; if business requires fallback, introduce an explicit opt-in flag in a separate, controlled change.
- **Cluster schema drift**: Some clustering results may lack `Cluster` or use `cluster_id`. Root normalizes; preserve this behavior.
- **Period mismatch**: Reference defaults (`202509A`) vs root defaults (`202506B`). Mitigation: always pass `--yyyymm`/`--period` via runners/scripts; do not change defaults during this merge.
- **Import path conflicts for trending**: Reference imports `trending_analysis.*`. Mitigation: vendor under `src/trending_analysis/` and update imports to `from src.trending_analysis ...` within drivers.

### Plan of Record

1) Baseline and Freeze
- Run a dry read of Step 7 and config without edits; confirm current default period and output naming.
- Ensure `output/` and `data/api_data/` contain current-period artifacts or that CLI will be used.

2) Step 7 Strategy (Root as Base)
- Keep root `src/step7_missing_category_rule.py` as the canonical implementation.
- Do not import reference Step 7. Instead, review any reference-only heuristics worth porting later behind flags (none are required for this merge).
- Preserve: safe left-join, cluster column normalization, period-aware file resolution, optional seasonal blending, integer quantity rounding, ROI env-gates, Fast Fish validation and period-labeled outputs + summary.

3) Add Trending Engines (Library-first)
- Create `src/trending_analysis/` and copy reference files:
  - `config.py`, `core_trend_analysis_engine.py`, `enhanced_trendiness_analyzer.py`, `trend_analyzer.py`, `trendiness_data_loader.py`, `fashion_basic_analyzer.py`, `sales_performance_trend_analyzer.py`.
- Make imports package-absolute when we wire: `from src.trending_analysis...`.
- Keep root `src/step17_augment_recommendations.py` as entrypoint; wire it to call the engines conditionally (feature flag) without removing existing logic.

4) Wiring and Flags
- Introduce env flags (read-only initially; default to current behavior):
  - `TRENDING_ENABLE_ENGINES=0|1` to activate trending engines path.
  - `RULE7_USE_ROI`, `ROI_MIN_THRESHOLD`, `MARGIN_RATE_DEFAULT` already exist; document and keep defaults.
  - Optional later: `RULE7_ALLOW_NO_VALIDATOR_FALLBACK=0|1` to permit approvals without validator.

5) Tests and Diagnostics
- Execute existing tests for config and Step 7 if present; verify no regressions. Add smoke checks:
  - Can load clustering and sales for a specified `yyyymm/period`.
  - Step 7 produces period-labeled results with either validator present or absent (no crash, deterministic logging).
- Add simple trending engine import/run smoke test behind `TRENDING_ENABLE_ENGINES=1` with synthetic data, but do not enable by default.

6) Outputs & Backward Compatibility
- Confirm Step 7 writes:
  - `output/rule7_missing_{analysis}_sellthrough_results_{period_label}.csv`
  - `output/rule7_missing_{analysis}_sellthrough_opportunities_{period_label}.csv`
  - `output/rule7_missing_{analysis}_sellthrough_summary_{period_label}.md`
  - Backward-compatible `output/rule7_missing_category_results.csv` only for subcategory analysis.

7) Rollout Procedure
- Land trending engines under `src/trending_analysis/` (no behavior change until flagged on).
- Keep Step 7 unchanged functionally in first commit; only documentation added so far.
- In a follow-up guarded commit, add the `TRENDING_ENABLE_ENGINES` plumbing and minimal glue in step 17.

8) Acceptance Criteria
- Step 7 runs end-to-end for both `analysis-level=spu|subcategory` with specified periods, producing period-labeled outputs.
- When sell-through validator is available, only compliant opportunities are saved; when unavailable, script completes with clear logs and zero approvals (existing behavior).
- No breaking changes to downstream Steps 13/14 (column names preserved).
- Trending engines vendored and importable, but dormant unless flagged.

### Operational Notes

- Always run Step 7 with explicit period parameters (example):
  - `python src/step7_missing_category_rule.py --yyyymm 202509 --period A --analysis-level spu`
- Ensure `src/config.py` initializes and logs the resolved `period_label` and paths.
- Preserve logs as part of delivery artifacts for quick forensics.


