### Name

- Rule 10: Smart Overcapacity (SPU) with Real-Unit Reductions and Optional Fast Fish Validation

### Purpose

- Detect SPU overcapacity (current SPU count > target SPU count) within categories and recommend unit quantity reductions using only real unit data. Optimize recency/seasonality via optional blending; optionally validate with Fast Fish.

### Inputs

- Period resolution via `src/config.py` and `get_output_files()` for clustering.
- Store config data with `sty_sal_amt` JSON-like SPU sales embedded; used for expansion and context.
- SPU sales data with real unit fields: `base_sal_qty`, `fashion_sal_qty`, `sal_qty`, or `quantity` and `spu_code`.
- Clustering results with `str_code` and either `Cluster` or `cluster_id` (both mirrored on load).

### Parameters and Flags

- CLI (root implementation)
  - `--yyyymm`, `--period`, `--target-yyyymm`, `--target-period`
  - Seasonal blending: `--seasonal-blending` or disabled; July A+B recency preferred
  - Join/precision: `--join-mode {left,inner}` (default `left`)
  - Debug/speed: `--debug-limit`, `--skip-sellthrough`, `--max-adj-per-store`
  - Threshold overrides: `--min-sales-volume`, `--min-reduction-qty`, `--max-reduction-pct`, `--min-cluster-size`

- Thresholds and caps (effective defaults)
  - `MIN_CLUSTER_SIZE = 3`, `MIN_SALES_VOLUME = 20`, `MIN_REDUCTION_QUANTITY = 1.0`, `MAX_REDUCTION_PERCENTAGE = 0.4`, `MAX_TOTAL_ADJUSTMENTS_PER_STORE = 30`

### Processing Overview

1) Load data (optionally blended)
  - Load recent config and quantity; if August and enabled, blend with seasonal sources (weighted) without synthesizing values.
  - Load cluster results; mirror `Cluster` and `cluster_id`.

2) Expand to SPU level (real SPU codes)
  - Parse `sty_sal_amt` JSON per store-category; keep only categories with current > target SPU count and sufficient sales; construct SPU-level records with category overcapacity context.

3) Join real-unit quantities and compute metrics
  - Join SPU sales file by `(str_code, spu_code)`; derive `quantity_real`, `unit_price`, and `current_quantity = quantity_real * SCALING_FACTOR`.
  - Compute proportional per-SPU reduction from category excess; constrain by `MAX_REDUCTION_PERCENTAGE`; set `recommended_quantity_change` negative for reductions; compute `investment_required` (negative = savings).

4) Optional Fast Fish validation and per-store cap
  - Validate reductions per (store, subcategory, current_count → recommended_count) key; keep compliant rows; prioritize by sell-through improvement; apply per-store cap; keep NA rows for missing fields.

5) Aggregate and save outputs
  - Store-level results aggregating counts, quantities, savings; standardize `recommended_quantity_change` and `investment_required`.
  - Save unlabeled legacy and period-labeled results/opportunities/summary; register in manifest with metadata.

### Outputs

- Unlabeled legacy
  - Results: `output/rule10_spu_overcapacity_results.csv`
  - Opportunities: `output/rule10_spu_overcapacity_opportunities.csv`

- Period-labeled
  - Results: `output/rule10_smart_overcapacity_results_{period_label}.csv`
  - Opportunities: `output/rule10_spu_overcapacity_opportunities_{period_label}.csv`
  - Summary: `output/rule10_smart_overcapacity_spu_summary_{period_label}.md`
  - Manifest entries for all outputs with period/components and column lists.

### Failure Modes

- Missing config/quantity/cluster files → logged and fail with explicit message.
- Missing real unit fields in SPU sales → no unit join; log coverage and NA rates; do not synthesize quantities.
- No SPU expansions or reductions → write no-op outputs and return.

### Invocation example

- `python src/step10_spu_assortment_optimization.py --yyyymm 202509 --period A --target-yyyymm 202509 --target-period A --seasonal-blending`


