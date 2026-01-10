### Name

- Rule 14: Enhanced Fast Fish Format (real-data, compliance-ready) with optional overview export (gated)

### Purpose

- Transform Step 13 consolidated SPU recommendations and real dimensional attributes into the complete Fast Fish CSV schema, with validation/mismatch reporting and period-labeled outputs. Optional overview/dashboard export can be added later behind a flag (real-data only).

### Inputs

- Consolidated SPU recommendations from Step 13 (prefer detailed):
  - `output/consolidated_spu_rule_results_detailed.csv` (preferred)
  - Fallbacks: corrected cluster aggregation files; otherwise fail fast
- Dimensional attributes: SPU sales + store config for `season_name`, `sex_name`, `display_location_name` (NA-preserving when missing)
- Cluster mapping: `output/clustering_results_spu.csv`
- Weather (optional): `output/stores_with_feels_like_temperature.csv`
- Historical sales (optional): `data/api_data/complete_spu_sales_202409{A/B}.csv` or fallback `...2025Q2_combined.csv`

### Parameters and Flags

- Internal flags (default off):
  - `ENABLE_ADAPTIVE_CAPS`, `ENABLE_SCORED_SELECTION` (rule-integration behavior)
  - Optional future: `--enable-overview-export` (gated, not implemented yet)

### Processing Overview

1) Load Step 13 detailed SPU outputs; if missing, try corrected aggregations; otherwise error.
2) Load SPU sales and (if available) store config to attach dimensional attributes; prefer store×subcategory mapping; fallback to store-level modes; never synthesize; leave NA when absent.
3) Map to store groups (cluster-based); group by store-group×category×subcategory.
4) Compute required Fast Fish fields:
  - Counts: `Current_SPU_Quantity`, `Target_SPU_Quantity` (init equal; Δ via rule adjustments)
  - Dimensional tags: `Target_Style_Tags = [Season, Gender, Location, Category, Subcategory]` with NA-preserving mapping
  - Customer Mix percentages (men/women/unisex/front/back store/season shares)
  - Optional metrics: Temp_14d_Avg, Historical ST%
5) Integrate rule-based add/remove counts from detailed SPU recommendations (caps, optional scoring).
6) Validate and build mismatch report (structured vs parsed tags); optionally auto-repair via env flag; save mismatch CSV.
7) Save main CSV and period-labeled variant; write validation JSON; register in manifest.

### Outputs

- `output/enhanced_fast_fish_format_{timestamp}.csv`
- `output/enhanced_fast_fish_format_{period_label}.csv`
- `output/enhanced_fast_fish_validation_{timestamp}.json`
- Optional mismatch report: `output/enhanced_fast_fish_dim_mismatches_{timestamp}.csv`
- Manifest entries for both CSVs (and validation metadata).

### Failure Modes

- Missing Step 13 detailed input → error; request upstream run.
- Missing cluster or dimensional data → log and leave NA; continue.
- Missing weather/historical → log and leave NA; continue.

### Invocation example

- `python src/step14_create_fast_fish_format.py` (env `PIPELINE_TARGET_YYYYMM`/`PIPELINE_TARGET_PERIOD` set)


