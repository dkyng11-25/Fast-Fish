### Scope

- Targets: `src/step18_validate_results.py` (root vs reference). Read-only: `src/pipeline_manifest.py`, Step 15 historical outputs, Step 17 augmented outputs.
- Non-goals: Changing Steps 7–17 logic; introducing synthetic grouping or synthetic sell-through estimates; altering upstream file naming beyond documented period-labeled outputs.

### High-level comparison (root vs reference)

- Objective
  - Both add sell-through calculations to the Step 17 augmented recommendations for the target period.

- IO and period handling
  - Root: Period-aware CLI, resolves Step 17 input via manifest using period-specific key; loads Step 15 historical via manifest matching baseline; saves period-labeled output; registers outputs (generic + period-specific) in manifest.
  - Reference: Glob-based “latest” augmented file; historical source fixed to 202408A; no manifest integration.

- Grouping and data quality
  - Root: Uses real cluster mapping already baked into inputs (“Store_Group_Name” present); no fabricated group IDs; NA-safe math; preserves NA when historical match missing.
  - Reference: Builds store groups via modulo/hash fallback; may estimate sales when history missing using ad-hoc ratios (synthetic); not NA-preserving.

- Calculations
  - Root: SPU-Store-Days Inventory = Target_SPU_Quantity × Stores_In_Group × 15; SPU-Store-Days Sales from Step 15 historical per group/category/day; Sell-through emitted as fraction and percent, clipped, NA-safe.
  - Reference: Similar form but with modulo grouping; falls back to derived estimates from current sales when history missing.

- Extras
  - Root: Adds optimization-visibility columns (capacity utilization, suitability, confidence, rationale) with safe fallbacks.
  - Reference: Progress bars (tqdm) and one-pass loops; simpler console report.

### Advantages to leverage from reference

- UX improvements: progress bar on long loops (optional), concise console summaries. Can adopt progress bars guarded by a flag.
- Simpler top/bottom distributions in summary (already partially present in root; keep root’s richer, period-aware metadata).

### Risks and mitigations

- Synthetic grouping and estimates inflate accuracy. Mitigation: keep root’s real-data only policy; leave NA when unavailable.
- Wrong-period inputs via glob. Mitigation: keep manifest-first resolution with baseline checks.
- Divide-by-zero/NA. Mitigation: keep NA-safe clipping and explicit guards.

### Plan of record

1) Keep root as canonical: period-aware inputs via manifest, real-data calculations, NA-preserving outputs, manifest registration.
2) Do not port modulo/hash grouping or synthetic sales estimation. Where history is missing, keep NA.
3) Optionally add a progress-bar flag for user feedback without changing logic.
4) Ensure outputs remain period-labeled and registered under both generic and period-specific keys.

### Diagnostics to validate on run

- Historical join coverage for Store Group × Category × Subcategory.
- Count and rate of NA sell-through; distribution stats for valid rates.
- Manifest entries recorded with correct period label and row/column counts.

### Acceptance criteria

- Output CSV saved to `output/fast_fish_with_sell_through_analysis_<TARGET_LABEL>_<TS>.csv` and manifest-registered (`step18/sell_through_analysis`, `step18/sell_through_analysis_<TARGET_LABEL>`).
- No synthetic grouping or ad-hoc sales estimates; NA preserved where inputs absent.
- Sell-through metrics provided as both fraction and percent; legacy `Sell_Through_Rate` retained as percent.

