### Scope

- **Targets**: `src/step12_sales_performance_rule.py` (root vs reference). Read-only: `src/config.py`, `src/pipeline_manifest.py`.
- **Non-goals**: Changing Steps 7–11; introducing trend engines yet; altering downstream column contracts.

### High-level comparison (Root vs Reference)

- **Objective**
  - Both analyze store performance vs cluster top performers and produce quantity increase recommendations.

- **Data sourcing & IO**
  - Root: Period-aware IO, prefers labeled cluster via `get_output_files`, seasonal blending for August, manifests, labeled + legacy outputs, optional testing mode, richer validation and diagnostics.
  - Reference: Period-dynamic quantity path, simpler joins, no manifests, no seasonal blending, lighter execution.

- **Unit handling**
  - Root: Real per‑SPU quantities; no synthetic unit generation; unit price from amounts/units; NA-preserving math.
  - Reference: Falls back to estimated units via amount/price proxy in places (e.g., 100/unit) if quantity column missing.

- **Detection/classification**
  - Both: Compute opportunity gaps vs percentile benchmark, Z-scores, classify performance levels, then compute incremental unit increases with caps and filters.
  - Root: Balanced thresholds, explicit selectivity filters, store-level aggregation with quantity totals and investment.

- **Outputs**
  - Root: Rule results, details, and markdown summary; structured for both subcategory and SPU modes; summary includes quantity metrics.
  - Reference: Similar CSV/MD artifacts but without manifest/labeled outputs and with potential estimation.

### Advantages in the reference to leverage

- Period-dynamic quantity file resolution as a fallback/override.
- Lightweight, fast run profile for ad‑hoc QA.
- Clear classification outputs with simple thresholds suitable for tuning.

### Risks and mitigations

- Synthetic unit estimation in reference
  - Mitigation: Keep root’s real-unit-only policy; skip/flag when missing; never synthesize.

- Join strictness
  - Mitigation: Expose join mode `--join-mode {left,inner}` (default left) to toggle precision vs inclusivity, as done in Steps 10–11.

- Seasonal blending availability
  - Mitigation: Log and fall back; do not synthesize.

### Plan of record

1) Documentation (this plan + spec) before changes.
2) Keep root as canonical: real units, labeled outputs + manifest, seasonal blending toggle, NA-preserving calculations, rich diagnostics.
3) Surface reference advantages as optional toggles: join mode; threshold overrides; test/fast profile. Do not import synthetic unit paths.

### Operational toggles to expose/confirm

- `--join-mode {left,inner}` (default `left`).
- Threshold overrides: top percentile, min cluster size, z-score cutoff, min sales volume, min increase quantity, max increase pct, per-store cap, min investment, min opportunity score.
- Testing mode sampling keep as in root.

### Diagnostics and tests

- Validate labeled + legacy outputs; manifest registration.
- Confirm quantity coverage and NA propagation; verify no synthetic unit creation.
- Ensure performance classification and filters behave under overrides.

### Acceptance criteria

- No synthetic data; real-unit recommendations with clear constraints.
- Parameterized toggles available without changing defaults.
- Outputs preserve contracts and gain period-labeled variants where relevant.


