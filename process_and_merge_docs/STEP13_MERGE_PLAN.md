### Scope

- **Targets**: `src/step13_consolidate_spu_rules.py` (root vs reference). Read-only: `src/config.py`, `src/pipeline_manifest.py`, Step 7–12 outputs.
- **Non-goals**: Changing business logic in Steps 7–12; introducing synthetic data; forcing trend enrichment on by default.

### High-level comparison (Root vs Reference)

- **Objective**
  - Both consolidate SPU-level rule outputs into store-level summaries; reference integrates a larger “trend enrichment” suite; root focuses on consolidation + data quality, with trend utilities dormant by default.

- **Data handling**
  - Root: SPU-detail preservation; NA-preserving transforms; duplicate removal; missing `cluster`/`sub_cate_name` mapping; period-labeled outputs; manifest; chunked IO; FAST mode; trend utils gated.
  - Reference: Integrated 20-col “fashion enhanced” and 51-col “comprehensive trends”; some synthetic defaults; faster end-to-end run profile.

- **Outputs**
  - Root: Detailed SPU consolidated file, store-level summary, optional cluster-subcategory aggregation, period-labeled variants, manifest entries.
  - Reference: Adds fashion/comprehensive suggestion formats; no manifest; fewer period labels.

### Advantages in the reference to leverage (safely)

- Fast profile for large datasets.
- Additional export formats (fashion enhanced, comprehensive trends) behind a flag; real-data only.
- Operator-friendly logs/summaries.

### Risks and mitigations

- Synthetic defaults in enrichment (e.g., fixed fashion ratios, default unit prices): keep enrichment optional and real-data only; NA where inputs are missing.
- IO variance across rule outputs: standardize/match columns per rule; robust aggregation; log optional/missing columns.
- Period/manifest consistency: reuse root’s period label and register all final outputs; keep legacy filenames.

### Plan of record

1) Documentation (this plan + spec) first.
2) Keep root as canonical: SPU-detail preservation, NA-preserving data corrections, labeled outputs, manifest registration, chunked IO.
3) Surface reference’s extra exports as optional feature flags (disabled by default) using only real data.
4) No synthetic ratios/prices/quantities.

### Operational toggles to expose/confirm

- Performance: `FAST_MODE`, `TREND_SAMPLE_SIZE`, `CHUNK_SIZE_SMALL`.
- Enrichment: `ENABLE_TREND_UTILS` (default False); when enabled, require real-data availability; skip on gaps.

### Diagnostics and tests

- Confirm preferred detailed files for rules 7–12; fall back to legacy names when needed.
- Validate column mappings; no unintended duplicates after dedup.
- Verify period-labeled outputs and manifest registrations.
- If enrichment enabled, assert real-data only; NA on missing inputs.

### Acceptance criteria

- SPU-detail consolidation preserved; store-level summary correct; optional cluster-subcategory aggregation.
- No synthetic data in any output; NA preserved with clear logs.
- Period-labeled outputs created; manifest updated; legacy filenames supported.


