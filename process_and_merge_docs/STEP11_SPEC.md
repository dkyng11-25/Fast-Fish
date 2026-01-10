### Name

- Rule 11: Missed Sales Opportunity (SPU) with real-unit, incremental quantity recommendations

### Purpose

- Identify missed sales opportunities by comparing stores to cluster top performers at the category level, and recommend INCREMENTAL unit increases per SPU using real per‑SPU quantities; optionally validate with Fast Fish; support period‑labeled outputs and manifest.

### Inputs

- SPU sales/quantity file: must include `str_code`, `spu_code`, and at least one real quantity source among `quantity`, `base_sal_qty`+`fashion_sal_qty`, or `sal_qty`; amounts in `spu_sales_amt`.
- Cluster assignments: `output/clustering_results_spu.csv` with `str_code` and `Cluster` or `cluster_id` (both mirrored on load).
- Environment/CLI period info for labeled outputs.

### Parameters and Flags

- CLI (align to Step 10 style)
  - `--yyyymm`, `--period`, `--target-yyyymm`, `--target-period`
  - Seasonal blending: `--seasonal-blending` | `--no-seasonal-blending`
  - Join/precision: `--join-mode {left,inner}` (default `left`)
  - Debug/testing: `--test` (sampling), and optional threshold overrides

- Thresholds (effective defaults in root)
  - Percentile threshold for top performers (e.g., `0.95`)
  - `MIN_CLUSTER_STORES`, `MIN_STORES_SELLING`, `MIN_SPU_SALES`
  - Selectivity: `MAX_RECOMMENDATIONS_PER_STORE`, `MIN_OPPORTUNITY_SCORE`, `MIN_SALES_GAP`, `MIN_QTY_GAP`, `MIN_ADOPTION_RATE`, `MIN_INVESTMENT_THRESHOLD`

### Processing Overview

1) Load SPU data (optionally blended for August)
  - Prefer recent period; blend with seasonal sources when enabled; do not synthesize values.
  - Derive real `estimated_spu_qty` from `quantity` or `base_sal_qty + fashion_sal_qty` or `sal_qty`; compute `avg_unit_price = spu_sales_amt / estimated_spu_qty` where valid.

2) Merge clusters and build category keys
  - Join with clusters via `--join-mode`; build `category_key = cate_name|sub_cate_name`; compute per-store category totals (sales and quantity); compute SPU/category ratios with NA-safe division.

3) Identify cluster-category top performers
  - Compute performance metrics and percentile ranks; keep SPUs meeting `MIN_STORES_SELLING` and percentile threshold; compute `adoption_rate` using cluster store counts.

4) Build expected store×SPU targets and gaps
  - For each (cluster, category), scale ratios to each store’s category totals; compute target 15‑day sales/quantity; left-join actual store×SPU; compute gaps; classify as `ADD_NEW` or `INCREASE_EXISTING`.

5) Compute incremental recommendations and filters
  - `recommended_quantity_change` = max(qty_gap, 0); `investment_required` = units × unit_price; apply selectivity filters and per‑store cap if configured.

6) Optional Fast Fish validation
  - Validate opportunities when validator available; clamp realistic integer counts for validator inputs; preserve NA and skip when quantities missing.

7) Aggregate and save outputs
  - Store-level results: counts, average score, total recommended 15‑day sales/units, standardized columns including `recommended_quantity_change`, `investment_required`, rationale/approval, flags. Save unlabeled and period-labeled CSV/MD; register manifest entries.

### Outputs

- Results (store-level):
  - Unlabeled: `output/rule11_improved_missed_sales_opportunity_spu_results.csv`
  - Labeled: `output/rule11_improved_missed_sales_opportunity_spu_results_{period_label}.csv`

- Details (opportunities, SPU-level):
  - Unlabeled: `output/rule11_improved_missed_sales_opportunity_spu_details.csv`
  - Labeled: `output/rule11_improved_missed_sales_opportunity_spu_details_{period_label}.csv`

- Top performers reference:
  - Unlabeled: `output/rule11_improved_top_performers_by_cluster_category.csv`
  - Labeled: `output/rule11_improved_top_performers_by_cluster_category_{period_label}.csv`

- Summary (markdown):
  - Unlabeled: `output/rule11_improved_missed_sales_opportunity_spu_summary.md`
  - Labeled: `output/rule11_improved_missed_sales_opportunity_spu_summary_{period_label}.md`

### Failure Modes

- Missing real quantity sources → raise or emit empty outputs; do not synthesize units.
- Missing clusters → diagnostics; with `inner` join mode these stores are excluded by design.
- No top performers/gaps → write empty detailed outputs and zeroed summaries; manifest still updated.

### Invocation example

- `python src/step11_missed_sales_opportunity.py --yyyymm 202509 --period A --target-yyyymm 202509 --target-period A --seasonal-blending --join-mode left`


