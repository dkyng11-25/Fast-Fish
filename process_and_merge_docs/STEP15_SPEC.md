### Name

- Step 15: Historical Baseline (period-aware) with real data only

### Purpose

- Build a historical reference at Store Group × Category × Subcategory for a baseline period (default: last-year same month with same A/B), then compare against current Step 14 analysis to produce YoY metrics and insights. Register outputs in the manifest for downstream steps.

### Inputs

- Historical SPU sales: `data/api_data/complete_spu_sales_<YYYYMM><A|B>.csv` (real data, no synthesis). Required columns: `str_code`, `spu_code`, `cate_name`, `sub_cate_name`; optional: `quantity`, `spu_sales_amt`.
- Cluster mapping: `output/clustering_results_spu.csv` with `str_code` and `Cluster` (real clustering). Missing or NA mapping yields `Store Group Unknown`.
- Current analysis (optional, for YoY): Step 14 enhanced output path via manifest preferred; fallback to latest `output/enhanced_fast_fish_format_*.csv`.

### CLI

- `--target-yyyymm` (required): e.g., 202509
- `--target-period` (required): A or B
- `--baseline-yyyymm` (optional): override default (T-12 months)
- `--baseline-period` (optional): override default (same as target period)
- `--current-analysis-file` (optional): explicit Step 14 enhanced file path; otherwise use manifest or latest

### Processing

1) Resolve baseline period: default to last-year same month; baseline period defaults to target period unless overridden.
2) Load historical SPU sales for the baseline period; coerce `str_code`, `spu_code` to string types.
3) Create store groups using real clustering mapping; map `Cluster` → `Store Group {Cluster+1}`; if missing, assign `Store Group Unknown` (no modulo/hash fallback).
4) Aggregate historical metrics by `store_group`, `cate_name`, `sub_cate_name`:
   - Distinct SPUs, NA-safe sums for `quantity` and `spu_sales_amt`, distinct stores.
   - Derive averages: avg sales per SPU, avg quantity per SPU, sales per store (NA-safe divisions).
5) Load current Step 14 analysis (enhanced) if available; prefer period-labeled via manifest; fall back to latest.
6) Create YoY comparison by outer-joining baseline and current on Store Group × Category × Subcategory, computing deltas and NA-safe percent changes; log denominator NA/zero diagnostics.
7) Build a historical Fast Fish-like CSV with period fields (`Year`, `Month`, `Period`) and historical aggregates; filter for minimal viability (SPU count >= 1 and Store count >= 2), sorted by group and sales.
8) Generate insights JSON (counts, totals, top categories/groups by avg sales per SPU).
9) Save outputs with timestamped, period-labeled filenames; register both generic and period-specific keys in the manifest.

### Outputs

- CSV: `output/historical_reference_<BASELINE_LABEL>_<TS>.csv` (historical FF-like)
- CSV: `output/year_over_year_comparison_<BASELINE_LABEL>_<TS>.csv`
- JSON: `output/historical_insights_<BASELINE_LABEL>_<TS>.json`
- Manifest keys (examples):
  - `step15/historical_reference` and `step15/historical_reference_<BASELINE_LABEL>`
  - `step15/yoy_comparison` and `step15/yoy_comparison_<BASELINE_LABEL>`
  - `step15/historical_insights` and `step15/historical_insights_<BASELINE_LABEL>`

### Failure modes

- Missing historical file for baseline period: fail fast with clear error.
- Missing cluster mapping: proceed with `Store Group Unknown`, log counts; still no synthetic grouping.
- Missing current analysis: proceed with historical-only reference and mark period as `<BASELINE_LABEL>_Historical`.

### Invocation examples

```bash
python -m src.step15_download_historical_baseline \
  --target-yyyymm 202509 \
  --target-period A

python -m src.step15_download_historical_baseline \
  --target-yyyymm 202509 \
  --target-period B \
  --baseline-yyyymm 202408 \
  --baseline-period A \
  --current-analysis-file output/enhanced_fast_fish_format_202509A_20250820_101500.csv
```

