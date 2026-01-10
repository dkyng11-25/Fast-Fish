### Scope

- **Targets**: `src/step14_create_fast_fish_format.py` (root) vs `backup-boris-code/.../src/step14_global_overview_dashboard.py` (reference). Read-only: Step 13 consolidated outputs, `output/clustering_results_spu.csv`, weather and historical sales inputs.
- **Non-goals**: Changing Steps 7–13; introducing synthetic data; enabling reference dashboards by default.

### High-level comparison (Root vs Reference)

- **Objective**
  - Root: Build a complete, compliance-ready Fast Fish format CSV using only real data; add validation/mismatch reports; register outputs with period labels.
  - Reference: Generate a global overview dashboard/visualization; less emphasis on the Fast Fish schema and manifest, more on presentation.

- **Data handling**
  - Root: Loads detailed SPU results (from Step 13), real dimensional attributes, cluster mapping, weather, and historical sales; avoids synthetic fills; performs NA-preserving merges; writes validation JSON and mismatch CSV.
  - Reference: Strong on visualization output, lighter on period-labeling/manifest and compliance checks.

- **Outputs**
  - Root: `enhanced_fast_fish_format_{timestamp}.csv`, labeled `enhanced_fast_fish_format_{period}.csv`, validation JSON, optional mismatch report; manifest entries.
  - Reference: Dashboard artifacts (e.g., HTML/plots), no manifest, fewer period-labeled assets.

### Advantages in the reference to leverage (safely)

- Presentation-ready summaries and dashboards for stakeholders (add as optional gated export later).
- Operator-friendly overview metrics; can be ported as an optional report using the same real-data sources.

### Risks and mitigations

- Synthetic defaults in presentation code (e.g., hard-coded mixes/price proxies):
  - Mitigation: Keep root’s real-data policy; any dashboard/report export must remain NA-preserving; never fabricate.

- Period/manifest consistency:
  - Mitigation: Continue root’s period-labeled copies and manifest registration; any optional exports also registered.

- Dependency creep and performance:
  - Mitigation: Keep visualization/reporting behind a feature flag; default off; retain chunked IO and caching.

### Plan of record

1) Documentation (this plan + spec) first.
2) Keep root as canonical: Fast Fish compliance, validation, labeled outputs, manifest, real-data only.
3) Consider adding optional “overview report” export (gated, default off) later, using only real data and registered outputs.
4) Do not introduce synthetic ratios/prices/quantities anywhere.

### Diagnostics and tests

- Verify detailed SPU input exists (from Step 13) or fail with clear messages.
- Validate dimensional parsing and mismatch report creation.
- Confirm labeled CSV and manifest registrations.
- Ensure weather/historical inputs are optional and NA-preserving when missing.

### Acceptance criteria

- Fast Fish CSV produced with required columns, labeled variant saved, manifest updated.
- No synthetic data; NA preserved with logs.
- Validation JSON and mismatch report generated where applicable.


