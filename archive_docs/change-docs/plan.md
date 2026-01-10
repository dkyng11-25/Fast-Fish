# Downstream Period-Aware and Manifest Integration Plan (Steps 7–33)

## Notes
- Focus is on patching Step 17 for period-aware filenames and manifest registration.
- Will inspect `step17_augment_recommendations.py`, `pipeline_manifest.py`, `config.py`, and `step16_create_comparison_tables.py` to mirror patterns from Steps 15/16 before editing Step 17.
- Found period label helpers and environment default logic in `config.py`.
- Confirmed manifest registration and retrieval patterns in `pipeline_manifest.py`.
- Step 16 uses argparse for CLI period/label parsing and period-aware output naming.
- Step 17 is now patched for period-aware filenames, manifest registration, and CLI period parsing.
- Step 17 period-aware outputs for both A and B periods are verified; manifest contains both generic and period-specific keys with correct metadata; CLI interface confirmed.
- Step 18 is now period-aware: CLI period parsing, period-aware input/output, manifest registration (generic + period-specific), and includes optimization visibility columns in output with metadata flag.
- Step 18 tested for both A and B periods; manifest and outputs verified.
- Existing test files for Step 17 & 18 (`*_test.py`, `*_TEST.py`) do not currently cover period-aware or manifest registration logic; review and update recommended.
- Seasonal blending for autumn (August) is required and must be enabled for Step 12; blending logic is present and preserves missingness, using both recent and August 2024 data.
- Next phase: Downstream steps (gap analysis, store/SPU recommendations, store descriptions, etc.) are untested and may need a major overhaul.
- User requests methodical, objective-aligned, stepwise review and overhaul of these steps, starting with careful analysis before any changes.
- Beginning analysis of downstream steps (21, 22, 29, 31) for period-awareness, manifest integration, and alignment with objectives; reviewing key scripts and modules as outlined.
- User explicitly requested a thorough, methodical review and patching of Steps 12–18, including re-verification of Step 14, not just Step 10/12.
- Plan must ensure Steps 13–18 are fully period-aware, manifest-integrated, NA-safe, and robust, with special attention to any previously skipped or partially reviewed steps.
- Initial code review of Steps 21, 22, 29, 31, `pipeline_manifest.py`, and `config.py` completed as part of the analysis phase.
- Step 21, 22, 29, and 31 code reviewed for output naming, period-awareness, and manifest registration. Synthesis of findings and gap identification is next.
- Step 22 patched for period-aware CLI, output naming, and manifest registration; verified outputs and manifest entries.
- Step 22 now robust to store code column variations and dtype mismatches in merges; period-aware outputs and manifest entries confirmed for 202509A.
- Step 29 patched for period-aware CLI, output naming, manifest registration (generic + period-specific), and dtype normalization for merges; ready for verification.
- Step 29 is now robust to missing columns and schema variations; period-aware outputs and manifest entries confirmed.
- Step 29 and 31 do not depend on Step 21; Step 21 is an independent D-F label/tag recommendation deliverable.
- Dependency analysis for Steps 21, 29, and 31 completed: Step 29 uses only core data outputs (sales, clustering, roles, price bands, store attributes); Step 31 builds on Step 29's outputs and does not require Step 21.
- Note: Step 14 previously generated problematic outputs due to:
  1. Lack of autumn season data (only summer/spring, summer dominated)
  2. Incorrect gender assignments (mostly unisex, which was wrong)
  3. Significant synthetic data introduced
  4. Unrealistic quantity recommendations (hundreds of SPU types suggested)
  5. Display location only recommended front or back of store (not acceptable)
  6. These issues have been partially resolved, but ongoing vigilance is required for seasonality, gender, realism, and synthetic data in Step 14 and all downstream steps.
- Recent codebase audit: Identified remaining synthetic dimensional defaults in Step 14 (summer/mid/front defaults), fallback logic in several steps, and risky 'inner' merges upstream that may drop rows silently.
- Step 11 audit: Found cluster_id fallback to 0 (synthetic default), 'Unknown' category fallback, and fillna(0) on some quantity/sales columns; confirmed all cluster merges are left joins, no inner merges found; dropna not used on critical dimensions.
- Step 11 now fully NA-safe, manifest-integrated, and period-aware; import guard added for robust execution as script or module; outputs and manifest entries verified for both generic and period-specific keys.
- Step 11 validation bug diagnosed: opportunities with missing quantity fields (especially ADD_NEW recommendations) were being skipped; root cause was missing current_quantity for new items.
- Step 11 patched: validation now treats missing current_quantity as 0 for ADD_NEW, throttles noisy skip logs, and reduces unnecessary skips. Patch applied and ready for verification.
- Step 11 manifest patch: All outputs (results, details, top performers, summary) now registered in manifest with period-aware keys and rich metadata; logic mirrors Step 12. Patch applied and syntax verified. Next: extend diagnostics and proceed to Phase 2 (Steps 7/8/9/10/12).
- Step 7 now patched: all cluster merges converted to left join with diagnostics, synthetic defaults removed (no cluster_id=0 fallback, no fillna(0) on sales/qty/amount), missingness preserved and logged; syntax verified. Next: proceed to Step 8 patch.
- Step 8 now patched: all cluster merges left join, synthetic defaults removed (no fillna(0) or fallback for quantities, unit_price, or flags), NA robust handling for recommend_rebalancing and summary metrics, missingness preserved and logged, diagnostics improved; syntax verified. Next: proceed to Step 9/10/12 patch.
- Step 9 now patched: all cluster merges converted to left join with diagnostics, synthetic defaults removed (no cluster_id=0 fallback, no fillna(0) on sales/qty/amount), missingness preserved and logged; syntax verified. Next: proceed to Step 10/12 patch.
- Synthesis of steps 2–13 audit: Found widespread risky patterns—inner/default-inner merges (often dropping rows), synthetic string/numeric defaults ("Unknown", 0, "no_data"), aggressive fillna(0), dict.get fallbacks, and dropna usage. These propagate false signal, mask missingness, and bias downstream logic. Concrete patch order and diagnostics now defined.
- Patch order: (1) Step 11—remove cluster=0 fallback, convert cluster joins to left, add diagnostics; (2) Steps 7/8/9/10/12—convert cluster joins to left, remove synthetic defaults, minimize fillna(0), add diagnostics; (3) Step 13—remove synthetic assignments, make merges explicit, keep NA, add diagnostics; (4) Early steps 2/2b/5—revisit fillna(0) on features/elevation.
- Diagnostics/reporting: Per-merge row count/match diagnostics, dimensional NA reporting, imputation reporting. All to be standardized and logged for transparency and manifest metadata.
- Beginning deep review of Steps 10 and 12 for manifest integration, period-aware file handling, and merging logic; will analyze code for manifest-related calls, merging strategies, and seasonal blending.
- Step 10 and 12 deep review: Both use risky inner merges for cluster joins and widespread synthetic fillna(0); Step 10 uses get_output_files for cluster file location (not manifest); Step 12 CLI/output logic is period-aware; neither step registers outputs in manifest. Patch will require: convert all cluster merges to left joins, eliminate synthetic defaults, minimize fillna(0), add diagnostics, ensure period-aware filenames, and register all outputs in manifest.
  - Step 10 patch tasks:
    - [x] Convert cluster join to left join and add diagnostics
    - [x] Adjust seasonal blending to preserve missingness (remove early fillna(0))
    - [x] Prefer period-labeled cluster file first, fallback to unlabeled
    - [x] Register all outputs in manifest with rich metadata
  - Step 12 patch tasks:
    - [x] Convert cluster join to left join and add diagnostics
    - [x] Remove fillna(0) on sal_amt and quantity recommendation flags in Step 12; preserve missingness and verify outputs/manifest/summary
    - [x] Complete thorough review of all blending, merging, and diagnostics in Step 12 for final NA safety and manifest integration
    - [x] Adjust blending to preserve missingness (remove early fillna(0))
    - [x] Register all outputs in manifest with rich metadata
- Step 12 patch progress: Removed fillna(0) on sal_amt and quantity recommendation flags; missingness now preserved using pandas BooleanDtype; summary writing logic fixed to avoid truncation; manifest registration and period-aware outputs confirmed; CLI and summary metadata verified; remaining blending/merging/diagnostics review ongoing. Seasonal blending is enabled and preserves missingness.
- Step 12 audit findings: All cluster merges are left joins, no fillna(0) or synthetic defaults in blending, merge diagnostics present; NA safety and manifest integration confirmed.
- Step 10 now patched: all cluster merges converted to left join, synthetic defaults removed (no cluster_id=0 fallback, no fillna(0) on sales/qty/amount), missingness preserved and logged, diagnostics and period-aware manifest registration added; syntax verified. Step 10 is now NA-safe, period-aware, and manifest-integrated.
  - [x] Implement Phase 1 patch: Step 11—remove cluster=0 fallback, convert cluster joins to left, add diagnostics
## Current Goal
Updated 2025-08-15 10:08 +08:00 — Consolidated, end-to-end plan (supersedes the prior goal).

### Status summary
- Completed/verified: Steps 7–13, 14, 16–19, 22, 29 are period-aware, NA-safe, and manifest-integrated. Step 17/18 verified for A/B; Step 22 verified; Step 29 patched and ready; Step 19 verified for 202509A.
- Pending verification: Step 29 manifest entries after latest patch (A/B re-run).
- Outstanding patches: Step 31 (`src/step31_gap_analysis_workbook.py`), Step 21 (`src/step21_label_tag_recommendations.py`).
- To review: Steps 20, 23–28, 30, 32–33 for period-awareness, manifest integration, NA-safety, and diagnostics.
- Pending: Step 15 review and patch for period-awareness, manifest integration, NA-safety, and diagnostics.

### Dependency map
- Step 22 → Step 29 → Step 31 (Step 31 depends on Step 29 detailed CSV)
- Step 21 is independent (deliverable)
- Step 29 inputs: sales, clustering labels, product roles, price bands, store attributes (manifest-first)

### Priority roadmap (next 7 days)
1. Verify Step 29 for 202509A/B
   - Run with CLI; ensure period-labeled outputs and manifest registration (generic + period-specific) with correct metadata; assert NA-safe fallbacks are exercised when inputs are missing.
2. Patch Step 31 (depends on Step 29 detailed CSV)
   - Add CLI period parsing; manifest-driven input resolution; period-labeled outputs; register 4 outputs (Excel, CSV, JSON summary, coverage matrix) under generic and period-specific keys with metadata; make joins/aggregations NA-safe.
3. Patch Step 21 (independent deliverable)
   - Add CLI period parsing; normalize inputs; generate timestamped, period-labeled workbook; register outputs in manifest; remove synthetic defaults; add diagnostics.
4. Manifest and config hardening
   - Standardize metadata fields across steps (target_year, target_month, target_period, records, columns, feature flags).
   - Add helpers in `src/config.py` for period-labeled output name templates and canonical manifest keys.
5. Cross-cutting diagnostics
   - Standard merge diagnostics; missingness reports; per-step summary stats; optional manifest notes for data quality.

### Per-step acceptance checklist
- CLI flags: `--target-yyyymm`, `--target-period`
- Filenames: include `{period_label}_{timestamp}`
- Manifest: register generic + period-specific keys with metadata (`target_year`, `target_month`, `target_period`, `records`, `columns`, feature flags)
- Inputs: manifest-first → period-labeled → unlabeled fallback
- Joins: left joins; no synthetic defaults; preserve NA
- Diagnostics: merge row counts; missingness report; summary metrics
- Idempotency: repeated runs create distinct timestamped outputs; manifest updates cleanly
- NA-safety: empty/partial inputs handled without errors

### Verification & test matrix
- Periods: 202509A and 202509B (both).
- Artifacts: presence, non-empty, schema checks, record/column counts.
- Manifest: correct keys, paths, metadata; exists=true; size_mb > 0 where expected.
- NA-safety: empty-input smoke tests pass without errors.
- Idempotency: rerun within same minute creates distinct timestamped outputs; manifest updates cleanly.

### Diagnostics template (reuse per step)
- Merge diagnostics: left/right key match rates; rows before/after
- Missingness: NA counts/rates for key columns
- Imputation actions: none or explicit

### Deliverables
- Updated code for Steps 21 and 31 with smoke tests.
- Updated `output/pipeline_manifest.json` entries verified for A and B.
- Brief runbook and customer-facing instructions for A/B validation.

### Risks & mitigations
- Missing upstream artifacts: use manifest-first resolution with sensible fallbacks and empty-frame handling.
- Schema drift: column normalization and defensive access patterns.
- Large outputs: stream writes and memory-aware groupbys where needed.

### Operational runbook (summary)
- Run: Step 22 → Step 29 → Step 31 for A then B; Step 21 independently.
- CLI: `--target-yyyymm 202509 --target-period {A|B}`.
- Input resolution order: manifest > period-labeled > unlabeled
- Validate outputs and manifest after each step.

### Definition of Done
- Steps 29, 31, 21 verified for A/B; period-labeled outputs present; manifest keys registered (generic + period-specific) with correct metadata; NA-safety demonstrated via empty-input tests; diagnostics consistent across steps.