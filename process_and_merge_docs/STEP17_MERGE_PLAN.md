### Scope

- Targets: `src/step17_augment_recommendations.py` (root) vs reference Step 17 variants:
  - `backup-boris-code/.../src/step17_augment_recommendations.py`
  - `backup-boris-code/.../src/step17_fast_trending_hybrid.py`
  - `backup-boris-code/.../src/step17_fixed_trending.py`
  - `backup-boris-code/.../src/step17_proper_trending.py`
  - `backup-boris-code/.../src/step17_enhanced_trending.py`
- Read-only: `src/pipeline_manifest.py`, Step 14 and Step 15 outputs, `src/trending_analysis/` library.
- Non-goals: Forcing trending on by default; introducing synthetic group mapping or synthetic trend scores.

### High-level comparison (root vs reference)

- Objective
  - Root: Period-aware augmentation of Fast Fish output with historical reference; optional/dormant cluster-level trending, manifest-driven IO, client format fixes, manifest registration.
  - Reference: Multiple variants. One focuses on ultra-fast, vectorized historical augmentation (hard-coded 202408A, modulo grouping). Others add trend scores (often synthetic defaults, reverse-engineered store lists) and faster loops.

- IO and period awareness
  - Root: CLI `--target-yyyymm`, `--target-period`; prefers manifest to locate Step 14/15 outputs; uses period-labeled filenames.
  - Reference: Glob-based latest file; hard-coded historical period; no manifest integration.

- Historical augmentation
  - Root: Real-data lookup Store Group × Subcategory; NA-safe deltas and percents.
  - Reference: Vectorized approach is fast but couples to 202408A and synthetic grouping fallbacks.

- Trending
  - Root: Gated trending that attempts to use preserved granular trend data and cluster mapping; keeps NA when unavailable.
  - Reference: Several scripts synthesize scores and store lists; risk of artificial variation and modulo-based grouping.

### Advantages to leverage from reference

- Vectorized historical augmentation path for speed (use as an optional fast mode; keep real grouping; no hard-coded periods).
- Clear trend-dimension columns and rationale scaffolding (align naming; keep values NA unless backed by real inputs).

### Risks and mitigations

- Synthetic grouping (modulo/hash; default group). Mitigation: use only real clustering; otherwise mark as Unknown/NA and exclude from deltas.
- Synthetic trend scores or reverse-engineered store lists. Mitigation: gate trending; compute only from preserved granular/real data; otherwise leave NA.
- Hard-coded periods and glob race. Mitigation: manifest-first resolution with explicit CLI overrides.

### Plan of record

1) Keep root Step 17 as canonical: period-aware CLI, manifest IO, real historical augmentation, client-format fixes, manifest registration.
2) Surface an optional fast path for historical augmentation (vectorized) that preserves real grouping and period-awareness.
3) Keep trending disabled by default; when enabled, use only real data (granular trend cache + cluster mapping). No synthetic defaults.
4) Ensure outputs remain period-labeled and registered under both generic and period-specific manifest keys.

### Operational toggles to expose (no code changes yet)

- `--fast-mode` for vectorized historical augmentation when inputs are clean.
- `--enable-trending` (default off) to compute trend columns only when real data is present.

### Diagnostics to validate on run

- Historical lookup coverage rate; counts of NA in historical columns; store-group mapping coverage.
- If trending enabled: number of rows with real trend scores; NA counts in each trend dimension; absence of synthetic constants.

### Acceptance criteria

- Augmented CSV produced using real historical data; percent calculations NA-safe; period-labeled filename; manifest updated (generic + period-specific keys).
- No synthetic grouping or manufactured trend values. Where inputs missing, values remain NA with logs.

