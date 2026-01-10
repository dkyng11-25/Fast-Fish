# Step 16 Change Proposal and Rationale

## Executive Summary

Make `src/step16_create_comparison_tables.py` strictly period-aware and audit-safe by consuming only Step 15 outputs (YOY + historical), avoiding synthetic grouping, keeping NA-preserving math for percent changes, and maintaining clear count-vs-unit semantics. This prevents reintroduction of Step 14–style problems (seasonality bias, synthetic data, unrealistic volumes) at the reporting stage.

## What’s Good (keep)
- Period-aware CLI and labels (`target_yyyymm`, `target_period`, computed `baseline_label`)
- Uses Step 15 outputs via manifest with period-specific keys when present
- Category and store-group comparisons computed from YOY data (preferred)
- Period-labeled Excel output; manifest registration for downstream access

## Gaps and Risks (and why they matter)
1) Synthetic grouping utility remains
- `create_store_groups` uses hash/modulo grouping; while not used in main YOY path, it’s still callable and used in legacy functions.
- Risk: Accidental use reintroduces synthetic clusters (Step 14 issue #3), skewing comparisons.

2) NA handling and zero denominators
- Several calculations fill with 0 before percent math. This can mask missing data and create false stability.
- Risk: Misleading percentages (Step 14 issue #3 synthetic stability) and divide-by-zero artifacts.

3) Schema robustness for YOY inputs
- Assumes presence of specific columns from Step 15; graceful degradation is partial.
- Risk: Breaks or silently misreports if upstream columns are renamed or absent.

4) Count vs unit semantics
- Aggregates `Current_SPU_Quantity` and historical SPU counts across groups. That is fine for “across groups” totals, but must never mix unit deltas into counts.
- Risk: If upstream changes, Step 16 must not reinterpret units as counts (Step 14 issue #4 unrealistic volumes).

5) Period alignment assurance
- Manifest filtering is good, but some fallbacks still match by filename pattern only.
- Risk: Wrong-period files could slip in if naming conventions diverge (Step 14 issue #1 seasonality mismatch).

## Required Changes

- Disable synthetic grouping
  - Remove or gate `create_store_groups` to test-only. In production, require group columns from Step 15 (e.g., `Store_Group_Name`) and skip group comparison if absent.

- NA-preserving percent math
  - For percent changes, compute only when denominators > 0; otherwise set NA. Do not pre-fill with 0 before ratios. Apply after-aggregation fills only for display (not for math).
  - Replace generic `fillna(0)` in YOY pathways with targeted casting and NA-aware ops; keep `replace([inf,-inf], np.nan)` where appropriate.

- Input schema validation
  - Validate required Step 15 columns exist before each comparison block. If missing, log and skip only that block (continue others). Example required columns:
    - Summary: `historical_total_sales`, `Current_SPU_Quantity`, `Total_Current_Sales`
    - Category: `category`, `historical_spu_count`, `Current_SPU_Quantity`, `historical_total_sales`, `Total_Current_Sales`
    - Store-group: `Store_Group_Name` (or `store_group`), same numeric columns as category level

- Period alignment hardening
  - When manifest entries are found but baselines differ from requested, skip them (already done) and fail-fast if no period-matching files exist rather than falling back to non-matching files by name pattern.

- Count vs unit guardrails
  - Document and assert that Step 16 treats SPU counts as counts only. If YOY contains unit deltas fields, they must not be combined with count metrics.

- Output clarity
  - In the Summary sheet, clearly label metrics that are NA due to missing denominators or inputs; do not silently coerce to zero.

## Acceptance Criteria
- No synthetic clustering is used anywhere; group comparisons rely solely on group identifiers from Step 15 or are skipped with a log.
- Percent changes are NA-safe and computed only with positive denominators; no divide-by-zero or masked NA via zero fills.
- Schema checks protect each comparison block; missing inputs skip that block with an informative log, not a crash.
- Only period-matching Step 15 outputs are accepted; otherwise, the job fails with a clear error instead of using mismatched data.
- SPU counts are never derived from unit quantities or mixed with unit deltas.
- Excel output remains period-labeled and registered in the manifest with row counts per sheet in metadata.

## Test Plan
- Unit tests
  - Percent math: provide YOY rows with zero historical metrics → percent columns are NA; verify no inf values.
  - Schema guard: remove category column from YOY → category sheet skipped; others produced.
  - Group reliance: remove group column → store-group sheet skipped with log; process completes.
  - Period enforcement: manifest contains non-matching baseline → step fails rather than pattern-fallback to mismatched files.

- Integration tests
  - End-to-end with Step 15 outputs for 202409A baseline and 202509A target → all sheets generate and metrics align with Step 15 aggregates.
  - Missing Step 15 YOY file → step fails with explicit message listing expected keys.

## Rollout
- Implement NA-safe math and schema guards first; then gate/remove synthetic grouping utility.
- Validate against multiple baselines and targets; check logs for skipped blocks and NA rates.
- Confirm downstream Step 17/18 do not rely on synthetic groupings or zero-filled percent columns.

## Backward Compatibility
- Workbook schema (sheet names and primary columns) unchanged; value semantics improve via NA preservation.
- If consumers relied on zero-filled percentages, they must accept NA where denominators are zero or missing.

## References
- Production: `src/step16_create_comparison_tables.py`
- Reference: `backup-boris-code/step16_create_comparison_tables.py`
- Upstream: Step 15 YOY and historical outputs with baseline- and period-specific manifest keys
