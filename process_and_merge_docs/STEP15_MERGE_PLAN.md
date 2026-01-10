### Scope

- Targets: `src/step15_download_historical_baseline.py` (root vs reference variants). Read-only: `src/pipeline_manifest.py`, `src/config.py`, Step 14 outputs.
- Non-goals: Changing Steps 7–14 logic; introducing synthetic store-grouping or synthetic sales/quantity; enabling dashboards by default.

### High-level comparison (root vs reference)

- Objective
  - Both compute a historical baseline at Store Group × Category × Subcategory and produce YoY comparisons vs current analysis.

- Period handling
  - Root: Period-aware (`--target-yyyymm`, `--target-period`, optional `--baseline-*`), baseline defaults to last-year same month with same A/B. Uses manifest to locate Step 14 output; falls back to latest enhanced file.
  - Reference: Hard-coded example period (202408A); fixed relative paths; limited discovery of current analysis.

- Store grouping
  - Root: Uses real clustering file `output/clustering_results_spu.csv`; if missing or NA, assigns `Store Group Unknown` (no modulo/hash fallback).
  - Reference: Falls back to modulo/hash grouping and default group labels when mapping fails.

- Computation and outputs
  - Root: NA-safe sums/divisions, explicit denominator diagnostics. Produces three outputs (historical FF-like CSV, YoY CSV, insights JSON) and registers all via manifest with generic and period-specific keys.
  - Reference: Similar aggregations but less NA handling and no manifest registration; file names not period-labeled.

- Dashboards
  - Root: None in Step 15.
  - Reference: Separate `step15_interactive_map_dashboard.py` (useful as optional, gated export later).

### Advantages to leverage from reference

- Optional dashboard export pattern (kept gated, real-data only).
- Concise console summaries (root already has insights JSON and console; we retain root and can extend summaries later).

### Risks and mitigations

- Synthetic grouping inflates accuracy. Mitigation: keep root Unknown assignment; never fabricate group IDs.
- Hard-coded periods risk wrong baselines. Mitigation: keep root CLI/manifest; require explicit overrides.
- YoY percent divide-by-zero/NA. Mitigation: preserve NA-safe math and explicit diagnostics.

### Plan of record

1) Keep root Step 15 as canonical (period-aware IO, manifest registration, NA-safe math, real clustering only).
2) Do not import modulo/hash grouping or default "Store Group 1" from reference.
3) Consider an optional `--export-dashboard` path later using only real data (separate step or flag).
4) Ensure outputs are period-labeled and registered under both generic and period-specific manifest keys.

### Operational considerations (no code change now)

- Potential flags (future): `--strict-store-group-only` to drop Unknown groups; `--min-stores` to filter low-sample historical combos.

### Diagnostics to validate on run

- Log counts of rows with `Store Group Unknown` prior to grouping.
- Log unique counts: store groups, categories, subcategories, SPUs.
- Log NA rates for denominators used in YoY percentages.

### Acceptance criteria

- Baseline defaults to T-12 with same A/B unless overridden via CLI; period-aware inputs/outputs are honored.
- Three outputs created and manifest-registered (historical FF-like CSV, YoY CSV, insights JSON) with period-labeled variants.
- No synthetic grouping or quantities; missing groupings are marked Unknown.
- YoY calculations are NA-safe with clear logs on undefined ratios.

