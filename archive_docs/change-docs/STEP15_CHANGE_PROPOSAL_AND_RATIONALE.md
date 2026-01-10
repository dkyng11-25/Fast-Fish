# Step 15 Change Proposal and Rationale

## Executive Summary

Align `src/step15_download_historical_baseline.py` to provide a period-accurate, audit-ready baseline without introducing synthetic structures. Enforce real clustering for store-group creation, handle missing metrics with NA (not fabricated defaults), align manifest keying with Step 14, and make YoY calculations robust. This prevents propagation of Step 14 issues (seasonality bias, synthetic data) and keeps historical comparisons reliable.

## What’s Good (keep)
- Period-aware CLI for target and baseline periods (e.g., 202509A → 202409A)
- Baseline loaded from year-over-year same month and A/B period
- Merges current Step 14 output for YoY; parses category/subcategory from `Target_Style_Tags` when needed
- Writes multiple labeled outputs and registers them in the manifest
- Uses cluster mapping when available for consistent `Store_Group_Name`

## Gaps and Risks (and why they matter)
1) Synthetic grouping fallback
- Hash/modulo-based grouping when clustering is missing invents store groups.
- Risk: Synthetic clusters distort group-level counts and comparisons; contradicts our no-synthetic policy.

2) Manifest key mismatch
- Attempts `get_step_input("step15", "fast_fish_format")`, while Step 14 registers `enhanced_fast_fish_format` under step14.
- Risk: Falls back to “latest file” heuristics, weakening period alignment/auditability.

3) NA handling and defaults
- Historical files may lack `spu_sales_amt` or `quantity`; YoY arithmetic can divide by zero/NA.
- Risk: NaN/inf in YoY percent columns or silent coercions; misleading results.

4) Period alignment and selection
- When manifest selection fails, falls back to latest enhanced file; only shallow period filtering is attempted.
- Risk: Comparing against a mismatched period reintroduces seasonality bias (Step 14 issue #1).

5) Semantics of SPU counts vs units
- Joins Step 14 columns like `Current_SPU_Quantity`, `Target_SPU_Quantity` that must be treated as counts, not units.
- Risk: If upstream semantics change, Step 15 must not mix unit deltas into count-based YoY metrics.

## Required Changes

- Grouping discipline
  - Require real clustering (`output/clustering_results_spu.csv`). If unavailable, either:
    - Fail-fast with a clear message, or
    - Produce ungrouped outputs by setting a neutral group (e.g., `Store Group Unknown`) without hash/modulo synthesis, and log the limitation.

- Manifest alignment
  - Query the manifest for Step 14 outputs using the correct producer and key, e.g., step="step14", key="enhanced_fast_fish_format".
  - Prefer period-labeled entries when multiple exist; validate `Period` matches `--target-period`.

- Robust NA math
  - When computing YoY deltas and percentages, use NA-safe math:
    - If historical denominator is 0/NA, leave percent as NA and log count of affected rows.
    - Ensure numeric columns are coerced with errors='coerce' and retain NA (no zero backfills).

- Historical schema resilience
  - If `spu_sales_amt` or `quantity` missing in baseline file, compute only metrics available from present columns. Do not fabricate amounts; leave derived fields NA.
  - Validate presence of `cate_name`, `sub_cate_name`, `str_code`, `spu_code`; fail-fast if missing.

- Period alignment safeguards
  - If a Step 14 file is provided but its `Period` column mismatches `--target-period`, search for a matching file; if none found, warn and proceed without current comparison (historical-only reference).

- Count semantics
  - Treat `Current_SPU_Quantity` and `Target_SPU_Quantity` strictly as counts in reporting. Do not interpret unit deltas as SPU counts anywhere in Step 15.

- Diagnostics and logging
  - Log which historical file was used, and which Step 14 file (with period) was selected.
  - Log NA rates for key numeric fields and how many YoY rows were skipped or set to NA due to missing denominators.

## Acceptance Criteria
- No synthetic cluster/group generation: either real clusters or a single explicit unknown group; no hash/modulo clustering.
- Manifest lookup correctly finds Step 14 enhanced output; period-matching selection used; if not found, comparison is skipped.
- YoY percent changes are NA-safe; no inf/-inf; zero-denominator cases are logged.
- No fabricated monetary or quantity defaults; missing historical metrics remain NA.
- SPU counts are treated as counts; no unit→count mixing.
- Outputs are saved and registered with clear metadata, including baseline and target periods.

## Test Plan
- Unit tests
  - Manifest selection: provide multiple Step 14 files; ensure correct period file selected; if none, returns None and historical-only path taken.
  - Grouping: remove clustering file → either fail-fast or produce unknown group only; no modulo grouping present.
  - YoY math: cases with historical_spu_count=0 or NA → YoY percent is NA; counts logged.
  - Schema missing: drop `spu_sales_amt` from historical → sales-derived metrics become NA; step completes.

- Integration tests
  - Baseline 202409A with Step 14 period A file: validate alignment and correct merge cardinality.
  - Baseline present, current missing: historical-only outputs generated and registered.
  - Mixed data types in historical file (strings in numeric cols): coercion works; NA preserved.

## Rollout
- Implement grouping policy and manifest alignment; keep CLI overrides intact.
- Validate on summer and September periods; verify YoY distributions and NA diagnostics.
- Monitor logs for: clustering availability, manifest hit-rate for correct period, NA/zero-denominator counts, and output sizes.

## Backward Compatibility
- File schemas remain; values become more conservative and NA where data is missing rather than fabricated.
- Downstream consumers relying on hash-based groups should be updated to expect either real clusters or a single unknown group.

## References
- Production: `src/step15_download_historical_baseline.py`
- Reference: `backup-boris-code/step15_download_historical_baseline.py`
- Upstream: Step 14 enhanced output; clustering results; API sales files for baseline
