### Name

- Rule 12: Sales Performance (subcategory/SPU) with real-unit, incremental quantity recommendations

### Purpose

- Evaluate store performance against cluster benchmarks, identify underperformance, and recommend INCREMENTAL unit increases using real per‑SPU quantities; support testing profile, period‑labeled outputs, and manifest registration.

### Inputs

- Cluster assignments: `output/clustering_results_spu.csv` with `str_code` and `Cluster` (or `cluster_id` mirrored post‑load).
- Planning/sales inputs:
  - SPU mode: `store_config_data.csv` or period-resolved `get_api_data_files(...)["store_config"]` fallback.
  - Subcategory mode: `complete_category_sales_YYYYMM?.csv` or equivalent.
- Quantity data: `complete_spu_sales_{period}.csv` with real quantities: `quantity` or `base_sal_qty`+`fashion_sal_qty` or `sal_qty`; `spu_sales_amt` present for prices.

### Parameters and Flags

- CLI (align to Steps 10–11)
  - `--yyyymm`, `--period`, optional `--test` sampling
  - Join/precision: `--join-mode {left,inner}` (default `left`)
  - Threshold overrides: `--top-quartile`, `--min-cluster-size`, `--min-sales-volume`, `--min-increase-qty`, `--max-increase-pct`, `--max-recs-per-store`, `--min-investment`, `--min-opportunity-score`, `--min-z`
  - Seasonal blending: explicit policy not required here; keep logging hooks if used

### Processing Overview

1) Load cluster, planning, and quantity data (prefer labeled cluster via config; fall back to legacy paths). Validate required columns.
2) Prepare sales data (expand SPU JSON if SPU mode) and filter to meaningful sales. Build `category_key` in SPU mode.
3) Compute opportunity gaps vs cluster top percentile and Z-scores.
4) Classify performance levels per thresholds.
5) Compute unit increases:
  - Build store×SPU quantity lookup from quantity data; for subcategory, avoid synthetic units (omit or restrict unit math to where real data maps); compute unit price as amount/units where valid; convert opportunity gaps to units; cap by `max_increase_pct`; apply minimums.
6) Apply filters: performance levels, Z-score minimum, min units, min investment, min opportunity score; per-store top-N.
7) Aggregate to store level with totals: `total_quantity_increase_needed`, `total_investment_required`, counts, averages; add standardized columns and rationale.
8) Save results: results CSV, detailed CSV, and summary MD; register manifest where applicable; include period-labeled variants if present.

### Outputs

- Results (store-level): `output/rule12_sales_performance_spu_results.csv` (and subcategory variant name), plus period-labeled if configured.
- Details: `output/rule12_sales_performance_spu_details.csv` (or subcategory variant), plus period-labeled if configured.
- Summary: `output/rule12_sales_performance_spu_summary.md` (or subcategory), plus period-labeled if configured.

### Failure Modes

- Missing real quantity sources → SPU unit computations limited; do not synthesize; subcategory path should avoid unit math unless mapping available.
- Missing clusters → diagnostics; `inner` join mode excludes by design.
- No opportunities → write empty detailed outputs and zeroed summaries.

### Invocation example

- SPU mode fast run (stricter join): `python src/step12_sales_performance_rule.py --yyyymm 202509 --period A --join-mode inner --test`
- SPU mode production-like: `python src/step12_sales_performance_rule.py --yyyymm 202509 --period A --join-mode left`


