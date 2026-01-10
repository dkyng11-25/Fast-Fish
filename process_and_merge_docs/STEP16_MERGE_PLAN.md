### Scope

- Targets: `src/step16_create_comparison_tables.py` (root vs reference). Read-only: `src/step15_download_historical_baseline.py`, `src/pipeline_manifest.py`.
- Non-goals: Changing Steps 7–15 logic; introducing synthetic grouping; enabling additional evaluators by default.

### High-level comparison (root vs reference)

- Objective
  - Both create an Excel workbook of comparison tables between a historical baseline and current period for Fast Fish review.

- Period handling & IO
  - Root (`src/step16_create_comparison_tables.py`): Period-aware CLI (`--target-yyyymm`, `--target-period`, optional baseline overrides), loads Step 15 outputs via manifest with period-specific keys; graceful fallbacks by glob if manifest missing.
  - Reference (`backup-boris-code/.../src/step16_create_comparison_tables.py`): Hard-coded periods and file paths (e.g., 202408A vs 202506B); no manifest.

- Store grouping
  - Root: Uses existing `Store_Group_Name` if present in YOY; otherwise marks `Store Group Unknown`. No modulo/hash fallback.
  - Reference: Uses `get_actual_store_group` with modulo/hash fallback and default group names when mapping fails.

- Features and outputs
  - Root: Builds Summary, Category, Store Group comparisons from Step 15 YOY; optional Top SPUs/Category Growth from raw SPU CSVs; Fashion/Basic segmentation sheets; Excel polishing; registers workbook in manifest (generic and period-labeled keys).
  - Reference: Similar tables but fixed periods, simpler Excel saving, no manifest.

- Additional reference capability
  - `backup-boris-code/.../src/step16_strategy_evaluation.py`: store–SPU level evaluator comparing rule vs default strategy (MAPE, stockout, service-level). Useful as an optional, gated analysis (real-data only) separable from Step 16 workbook generation.

### Advantages to leverage from reference

- Idea: strategy evaluation at store–SPU level as an optional companion tool (not default), using real data only and clear flags.
- Simpler top-performers views (already covered in root via optional raw-SPU paths).

### Risks and mitigations

- Synthetic grouping (modulo/hash) degrades accuracy. Mitigation: keep root’s Unknown labeling; no fabrication.
- Hard-coded period paths. Mitigation: keep period-aware CLI + manifest resolution.
- Division by zero/NA in percent changes. Mitigation: keep root NA-safe calculations and logs.
- Workbook drift without provenance. Mitigation: keep manifest registration with period labels and row counts.

### Plan of record

1) Keep root Step 16 as canonical (period-aware, manifest, NA-safe, Excel polish, optional raw-SPU & segmentation sheets).
2) Do not import modulo/hash grouping from reference.
3) Consider adding a separate, gated tool (later) inspired by `step16_strategy_evaluation.py` for store–SPU performance evaluation, real-data only.
4) Ensure the workbook filename includes the `target_label` and is registered under both generic and period-specific manifest keys.

### Operational toggles surfaced (already present in root)

- `--historical-raw-file`, `--current-raw-file` for Top SPUs sheets (optional).
- `--fashion-keywords`, `--basic-keywords`, `--hybrid-threshold` for Fashion/Basic segmentation.

### Diagnostics to validate on run

- Manifest entries selected (period-specific vs generic) and baseline alignment.
- Sheet row counts (Summary, Category, Store_Group, YOY raw, Historical raw) and presence of optional sheets.
- NA/Inf handling in percent change columns.

### Acceptance criteria

- Workbook saved to `output/spreadsheet_comparison_analysis_<TARGET_LABEL>_<TS>.xlsx` and registered in manifest under `step16/comparison_workbook` and `step16/comparison_workbook_<TARGET_LABEL>`.
- No synthetic grouping; Unknown groups remain explicit.
- Period-aware baselines match Step 15’s `baseline_label`; calculations are NA-safe.

