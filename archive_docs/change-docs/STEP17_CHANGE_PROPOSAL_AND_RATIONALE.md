# Step 17 Change Proposal and Rationale

## Executive Summary

Refocus `src/step17_augment_recommendations.py` on safe augmentation: join historical reference and (optionally) real-data trending without introducing synthetic clusters, seasonality/gender defaults, or heuristic scores. Align inputs with manifest (Step 14 output, Step 15 baseline), ensure count-vs-unit semantics, and avoid modifying `Target_Style_Tags` unless authoritative data exists. This prevents reintroduction of Step 14 failure modes: seasonality bias, incorrect gender defaults, synthetic data, unrealistic volumes, and front/back-only bias.

## What’s Good (keep)
- Period-aware CLI; period-labeled output filename and manifest registration
- Historical SPU comparison vs reference (difference in SPU counts)
- Optional use of trend analyzer from Step 13; explanation columns for transparency
- Attempts to parse `Target_Style_Tags` to extract subcategory

## Gaps and Risks (and why they matter)
1) Synthetic store grouping and cluster usage
- `create_store_groups` and `get_stores_in_group` rebuild groups via hash/modulo on `str_code`, even when `Cluster` is available. 
- Risk: Synthetic clusters distort group-level trending and historical joins (Step 14 issue #3); inconsistent with Step 14/15 group logic.

2) Trending uses synthetic or defaulted features
- Fallback paths `_aggregate_per_store_trends` and parts of granular aggregation generate heuristic scores (seasonal boosts, category bonuses, default temperatures, etc.).
- Risk: Reintroduces synthetic trends (Step 14 issue #3), seasonality bias (#1), and misleading confidence.

3) Granular trend data provenance
- Granular dataset from Step 13 can include synthetic columns (elevation, cluster_size, fashion ratios with defaults). 
- Risk: Synthetic signal contaminates Step 17 outputs unless gated by provenance checks.

4) Manifest/key mismatch for Step 14 input
- Uses `get_step_input("step17", "fast_fish_format")`; Step 14 registers `enhanced_fast_fish_format` under step14.
- Risk: Wrong or missing input selection; period misalignment (Step 14 issue #1).

5) `Target_Style_Tags` mutation
- Rewrites tag format and enhances tags from store config mapping regardless of Step 14 authority.
- Risk: Overwrites Step 14’s curated tags; can introduce stale/summer-heavy dims (Step 14 issue #1/#2/#5).

6) Hard-coded historical window
- Historical loads May 2025 (202505) subset; Step 15 defines period-aware baseline (e.g., 202409A).
- Risk: Baseline drift vs Step 15; seasonality mismatch (Step 14 issue #1).

## Required Changes

- Use real clusters and Step 14 grouping
  - Remove modulo/hash grouping. For store groups, derive `Store_Group_Name` from Step 14/cluster file: `Cluster + 1`. If clusters missing, skip trending and proceed with historical-only augmentation.

- Gate trending on real provenance; remove synthetic scoring
  - Disable `_aggregate_per_store_trends` and `get_synthetic_trend_scores` in production. 
  - When granular data is present, use only metrics sourced from real data; drop synthetic-derived features (elevation, synthetic seasonality, synthetic price tiers). If provenance unknown, skip those dimensions or leave NA.

- Align inputs with manifest
  - Read Step 14 via manifest: step="step14", key="enhanced_fast_fish_format"; require period match.
  - Read historical via Step 15 artifacts (YOY/historical) when needed instead of hard-coded May 2025.

- Preserve `Target_Style_Tags`
  - Treat Step 14 `Target_Style_Tags` as authoritative. Do not reformat or enhance unless mapping is exact and audited; otherwise leave as-is. Never inject defaults for season/gender/location; carry NA.

- Count vs unit semantics
  - Maintain SPU count comparisons only (`Target_SPU_Quantity` vs historical SPU count). Do not convert unit deltas to counts or vice versa.

- NA-preserving behavior and diagnostics
  - When trend inputs are missing, set NA (not default scores). Log counts of skipped trend dimensions and reasons (missing clusters, missing granular data).

## Acceptance Criteria
- No synthetic cluster/grouping used anywhere; groups derive from real `Cluster` IDs or trending is skipped.
- No heuristic/synthetic trend scores; only real-data-derived dimensions included, others NA.
- Step 14 input resolved via manifest with period match; no ad-hoc fallbacks. Historical context sourced from Step 15 baselines where required.
- `Target_Style_Tags` not overwritten unless a verified, one-to-one mapping exists; no forced season/gender/location defaults.
- SPU counts remain counts; no mixing with unit quantities.
- Logs report provenance decisions and NA/skipped trend dimensions; output registered with period label.

## Test Plan
- Unit tests
  - Manifest selection: ensure step14/`enhanced_fast_fish_format` is used; mismatch periods → fail with clear error.
  - Cluster dependency: remove cluster file → trending skipped; historical augmentation proceeds; logs reflect reason.
  - Tag preservation: when `Target_Style_Tags` already in 5-field format, no mutation occurs; when mapping incomplete, tags remain unchanged.
  - NA-preserving: trending dimensions absent → columns NA without defaulting; explanations express “not available”.

- Integration tests
  - Full pipeline with 202509A target and 202409A baseline: Step 17 consumes Step 14 + Step 15; produces augmented CSV with period label; no synthetic columns.
  - Granular data present but with synthetic-only columns → those dimensions excluded/NA; others computed.

## Rollout
- Stage with trending disabled-by-default flag; enable only when real-data provenance confirmed. 
- Verify against multiple periods (summer and autumn) for seasonality stability and absence of synthetic boosts.
- Monitor logs for cluster availability, manifest alignment, NA rates in trend columns, and any tag mutation counts.

## Backward Compatibility
- Output schema preserved (trend columns remain), but many values may become NA where previously defaulted/synthetic.
- Consumers relying on synthetic trend numbers must adapt to NA or real-data-driven values. Historical augmentation unaffected.

## References
- Production: `src/step17_augment_recommendations.py`
- Reference: `backup-boris-code/step17_augment_recommendations.py`
- Upstream: Step 14 `enhanced_fast_fish_format`; Step 15 historical baselines and YOY outputs
