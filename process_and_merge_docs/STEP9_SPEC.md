### Name

- Rule 9: Below Minimum (Dual-Mode: Subcategory and SPU) with Positive-Only Quantity Increases and Fast Fish Sell-Through Validation

### Purpose

- Identify below-minimum cases at both subcategory and SPU levels using only real signals.
- Produce positive-only unit increases where and only where real unit data exists (SPU). For subcategory, flag below-minimum categories using real planning counts; only emit unit increases if backed by real unit signals (no synthetic estimation).
- Optionally blend seasonal configuration and validate with Fast Fish to optimize quality of recommendations.

### Inputs

- Period resolution via `src/config.py`
  - `get_current_period()`, `get_period_label()`
  - `get_api_data_files(yyyymm, period)['store_config']`, `['spu_sales']`
  - `get_output_files(analysis_level, yyyymm, period)['clustering_results']`

- Required files
  - Clustering results with `str_code` and either `Cluster` or `cluster_id` (both will be mirrored if one is missing).
  - Store config (subcategory: uses real `target_sty_cnt_avg`; SPU: provides `sty_sal_amt` JSON-like sales breakdown used only for expansion and provenance, not for synthetic unit creation).
  - SPU sales with real `quantity` column and `spu_code` (or `sty_code`, renamed). If missing, SPU unit recommendations are skipped (no synthetic proxies).

### Parameters and Flags

- CLI (root implementation)
  - `--yyyymm YYYYMM`, `--period {A,B,full}` (full treated as None)
  - `--analysis-level {spu,subcategory}` (default: spu)
  - Seasonal blending: `--seasonal-blending`, `--seasonal-yyyymm YYYYMM`, `--seasonal-period {A,B,full}`, `--seasonal-weight <float>`
  - Output labeling: `--target-yyyymm`, `--target-period`
  - Thresholds: `--min-threshold <float>` (default 0.03), `--min-boost <float>` (default 0.5), `--unit-price <float>` (default 50.0)

- Effective defaults (SPU)
  - MINIMUM_UNIT_RATE = 1.0 units/15 days (when > 0)
  - MIN_BOOST_QUANTITY = 0.5 (ceil to integer for recommendation)
  - MAX_TOTAL_ADJUSTMENTS_PER_STORE = 50
  - NEVER_DECREASE_BELOW_MINIMUM = True

### Processing Overview

1) Load configuration and data
  - Resolve cluster file with layered fallbacks; read store config; optionally blend config for August when enabled.
  - Read SPU sales for current-period quantities; require `quantity` and map `sty_code`→`spu_code` if needed. No synthetic quantity estimation.
  - Mirror cluster columns so both `Cluster` and `cluster_id` exist; use `Cluster` for grouping and `cluster_id` in store results.

2) Prepare SPU data
  - Left-join store config to clusters; expand `sty_sal_amt` JSON-like content to `(str_code, sty_code, spu_sales_amt)` rows; sample if excessively large.
  - Merge SPU quantities by `(str_code, sty_code)`; compute `unit_rate = quantity * SCALING_FACTOR`; retain `style_count = unit_rate` for compatibility.

2b) Prepare Subcategory data
  - Left-join store config to clusters; use real `target_sty_cnt_avg` as the planning count signal; build `category_key` from grouping columns.
  - Do not derive unit quantities from monetary sales or other proxies. If unit signals are not available for subcategory, recommendations remain count-based flags; no unit increase values are emitted unless backed by real SPU unit mappings.

3) Identify below-minimum cases (SPU)
  - Filter `(unit_rate > 0) and (unit_rate < MINIMUM_UNIT_RATE)`; apply additional filters (e.g., min units and min cluster size) where present in code.
  - Compute target `MINIMUM_UNIT_RATE` and `increase_needed`.
  - Classify issue severity by thresholds.

4) Compute recommendations (positive-only)
  - `recommended_quantity_change = ceil(max(target - current, MIN_BOOST_QUANTITY))` → strictly positive integers.
  - Preserve NA `unit_price` when unknown; compute `investment_required = recommended_quantity_change * unit_price` when available.
  - Apply Fast Fish validation when available; keep only compliant cases; log aggregates.
  - Apply per-store cap with priority by compliance, sell-through improvement, severity, and quantity change.

4b) Subcategory recommendations policy
  - If real SPU unit signals can be reliably mapped to the subcategory, aggregate only real unit-based increases to inform subcategory recommendations; otherwise, emit flags and severity without synthetic unit counts.

5) Store-level summary
  - Aggregate counts, totals, averages; set rule flag `rule9_below_minimum_spu`; standardize `investment_required` and `recommended_quantity_change` columns.

### Outputs

- Period-labeled
  - Results: `output/rule9_below_minimum_spu_sellthrough_results_{period_label}.csv`
  - Opportunities: `output/rule9_below_minimum_spu_sellthrough_opportunities_{period_label}.csv`
  - Summary: `output/rule9_below_minimum_spu_sellthrough_summary_{period_label}.md`
  - All also saved as unlabeled backward-compatible files for downstream steps.
  - Manifest: entries for results/opportunities/summary with metadata (period label, columns, counts, quantity diagnostics).

- Subcategory mode outputs (when enabled)
  - Store-level results and summary use real planning counts; unit increases are included only if backed by real unit data (no synthetic estimation). Otherwise, quantity fields are omitted or NA.

### Failure Modes

- Missing cluster/store config/SPU sales files → explicit FileNotFoundError with candidates listed.
- Missing `quantity` or `spu_code` in SPU sales → explicit KeyError.
- No valid SPU expansion → write empty-but-structured results and exit.

### Invocation Examples

- `python src/step9_below_minimum_rule.py --yyyymm 202509 --period A --analysis-level spu --target-yyyymm 202509 --target-period A`


