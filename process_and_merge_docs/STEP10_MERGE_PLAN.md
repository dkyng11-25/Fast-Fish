### Scope

- **Targets**: `src/step10_spu_assortment_optimization.py` (root vs reference) and `src/config.py` (read-only).
- **Non-goals**: Enabling unrelated rules; changing Steps 7–9; altering downstream file names beyond documented labeled + legacy outputs.

### High-level comparison (Root vs Reference)

- **Analysis Level and Objective**
  - Both: SPU overcapacity detection (current SPU count > target) with unit quantity reductions.

- **Data sourcing and seasonality**
  - Root: Period-aware IO via `src.config`, optional seasonal blending, July A+B recency support, manifest registration, Fast Fish validation available, per-store cap.
  - Reference: Simpler direct file paths; no manifest; no validation; relies on estimated unit pricing during expansion.

- **Unit handling**
  - Root: Joins REAL unit quantities from SPU sales (base/fashion qty, sal_qty, or `quantity`), computes `current_quantity`, `unit_price` from real amounts; reductions and savings computed on real units; standard columns.
  - Reference: During expansion, estimates unit price as `spu_sales/2` (clipped) and derives quantities, then reductions; more permissive but synthetic.

- **Expansion and detection**
  - Both expand `sty_sal_amt` JSON to SPU-level records, using category-level target vs current counts to derive per-SPU reductions.
  - Root: Strictly pivot to real units after join; clamps and validates; optional sell-through validation with per-store cap.

- **Outputs**
  - Root: Both unlabeled (legacy) and period-labeled results/opportunities/summary; manifest entries.
  - Reference: Unlabeled outputs only.

### Risks and mitigations

- Synthetic quantities in reference expansion
  - Risk: Estimation (`spu_sales/2`) introduces bias.
  - Mitigation: Keep root’s strict real-unit join; do not import synthetic logic. If quantity join coverage is low, log diagnostics rather than synthesize.

- Cluster column inconsistency
  - Risk: `Cluster` vs `cluster_id` mismatch.
  - Mitigation: Mirror columns after cluster load (as in Steps 8–9); use `cluster_id` in results, keep `Cluster` for analysis.

- Seasonal blending data gaps
  - Risk: Blending enabled without seasonal files.
  - Mitigation: Log and fall back to recent-only; no silent synthesis.

- Validator unavailability
  - Risk: No Fast Fish validator.
  - Mitigation: Keep behavior: run without gating when skipped or unavailable; keep fields NA.

### Plan of record

1) Documentation (this plan + spec) before code edits.
2) Keep root as canonical; ensure cluster mirroring early; retain real-unit join and diagnostics; preserve per-store cap and labeled outputs + manifest.
3) Do not port synthetic unit estimation from reference.
4) If needed, add a clear log for quantity join coverage and NA rates (already present).

### Operational toggles surfaced

- Join mode: `--join-mode {left,inner}` (default `left`) to switch between inclusive (left) and stricter (inner) cluster joins for diagnostics vs precision.
- Threshold overrides for exploration vs production strictness: `--min-sales-volume`, `--min-reduction-qty`, `--max-reduction-pct`, `--min-cluster-size`.

### Diagnostics and tests

- Run with explicit `--yyyymm/--period`; confirm labeled + legacy outputs.
- Verify quantity join coverage and unit_price NA rates are logged.
- If validator is enabled, ensure compliant-only prioritization and per-store cap post-validation.

### Acceptance criteria

- End-to-end success with real-unit reductions and period-labeled outputs.
- No synthetic quantities introduced; diagnostics present; downstream steps consume standard columns without change.


