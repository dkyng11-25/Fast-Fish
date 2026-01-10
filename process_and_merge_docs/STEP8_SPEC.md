### Name

- Rule 8: Imbalanced Allocation with Quantity Rebalancing Recommendations (cluster Z-score based)

### Purpose

- Detect over- and under-allocation at subcategory or SPU level within clusters using Z-scores.
- Recommend unit quantity rebalancing (integer) with neutral investment (redistribution).
- Optionally validate recommendations using Fast Fish sell-through when available.

### Inputs

- Period resolution via `src/config.py`
  - `get_current_period()` → `(yyyymm, period)`
  - `get_period_label(yyyymm, period)`
  - `get_api_data_files(yyyymm, period)` → `store_config`, `spu_sales`
  - `get_output_files(analysis_level, yyyymm, period)['clustering_results']`

- Required files
  - Clustering results: must contain `str_code` and either `Cluster` or `cluster_id`.
  - Planning data:
    - Subcategory: `store_config_{period_label}.csv` with `target_sty_cnt_avg` and grouping columns.
    - SPU: `store_config_{period_label}.csv` with `sty_sal_amt` and grouping columns (SPU path expands with quantity data).
  - Quantity data (SPU path mandatory, subcategory path used for aggregation):
    - `complete_spu_sales_{period_label}.csv` with `str_code`, `spu_code`, `spu_sales_amt`, and authoritative quantity fields.

- Quantity derivation (strict)
  - Priority order: `quantity` → `base_sal_qty + fashion_sal_qty` → `sal_qty` → fail.
  - If none available: Step fails with explicit error. No proxy by default.

### Parameters and Flags

- CLI arguments (root implementation)
  - `--yyyymm YYYYMM`
  - `--period {A,B}`
  - `--analysis-level {spu,subcategory}`
  - `--target-yyyymm YYYYMM` (labeling only)
  - `--target-period {A,B}` (labeling only)
  - `--z-threshold <float>` (override; defaults depend on analysis level)

- Analysis level and thresholds (effective defaults)
  - Subcategory:
    - Z_SCORE_THRESHOLD: 2.0
    - MIN_CLUSTER_SIZE: 3
    - MIN_ALLOCATION_THRESHOLD: 0.1
    - MIN_REBALANCE_QUANTITY: 2.0
    - MAX_REBALANCE_PERCENTAGE: 0.3
  - SPU:
    - Z_SCORE_THRESHOLD: 3.0
    - MIN_CLUSTER_SIZE: 5
    - MIN_ALLOCATION_THRESHOLD: 0.05
    - MIN_REBALANCE_QUANTITY: 5.0
    - MAX_REBALANCE_PERCENTAGE: 0.5
    - MAX_TOTAL_ADJUSTMENTS_PER_STORE: 8

- Redistribution strategy
  - `REBALANCE_MODE` env: `increase_only` (default) or future `paired`.

### Processing Overview

1) Load configuration and data
  - Resolve period and candidate paths via `src.config`; pick first existing for clusters/planning/quantity.
  - For August, optionally blend recent vs prior-year seasonal for both planning and quantity (weighted).
  - Enforce strict quantity presence/derivation; fail if not resolvable.
  - Cluster normalization: when loading clusters, ensure both `Cluster` and `cluster_id` are present (mirrored) to support all downstream joins/groupbys. Results continue to use `cluster_id`; cases/z-score grouping continues to use `Cluster`.

2) Prepare allocation data
  - Subcategory: merge planning with clusters (safe left join), compute `allocation_value = target_sty_cnt_avg`, attach aggregated `current_quantity` and `current_sales_value` from quantity data by `(str_code, sub_cate_name)`, build `category_key` from grouping columns; do not threshold before z-score (avoid bias).
  - SPU: work primarily from quantity data joined to clusters, set `sty_code = spu_code`, set `allocation_value = quantity * SCALING_FACTOR`, `current_quantity` and `current_sales_value` likewise, build `category_key` from available grouping columns present in data (fallback to `['sub_cate_name','sty_code']` or `['spu_code']`).

3) Calculate cluster Z-scores
  - Group by `(cluster, category_key)`; compute mean, std (ddof=1), size; zero z-scores if std=0.
  - Skip groups with size < `MIN_CLUSTER_SIZE`.

4) Identify imbalanced cases and compute rebalancing
  - Classify by |Z| threshold and severity tier.
  - Compute target allocation = cluster mean, and quantity adjustment needed.
  - Constrain to `MAX_REBALANCE_PERCENTAGE` of current; apply `MIN_REBALANCE_QUANTITY`.
  - Compute `unit_price` when possible; set standardized columns: `spu_code`, `recommended_quantity_change` (integer-ceiled in root), `investment_required` (neutral by default in store results; case-level includes estimated value).
  - Apply optional Fast Fish validation: keep only compliant cases; prioritize by sell-through improvement; apply per-store cap after validation.

5) Apply rule and produce store-level results
  - Aggregate counts and totals per store; compute z-score summaries, totals, counts of over/under allocated, quantity totals.
  - Set rule flags and standard metadata.

### Outputs

- Period-labeled files
  - Results per store: `output/rule8_imbalanced_{analysis}_{period_label}_results.csv`
  - Cases detail: `output/rule8_imbalanced_{analysis}_{period_label}_cases.csv`
  - Z-score analysis: `output/rule8_imbalanced_{analysis}_{period_label}_z_score_analysis.csv`
  - Summary: `output/rule8_imbalanced_{analysis}_{period_label}_summary.md`

- Backward-compatible files
  - Subcategory: `output/rule8_imbalanced_results.csv`
  - SPU: `output/rule8_imbalanced_spu_results.csv`, `..._cases.csv`, `..._z_score_analysis.csv`

### Failure Modes

- Missing cluster or planning/quantity files → explicit FileNotFoundError with candidates listed.
- Missing required planning/quantity columns → explicit ValueError.
- No valid z-score groups → create empty-but-structured outputs for consistency.
- Validator unavailable → skip validation with log; keep cases but approvals are not implicitly granted.

### Invocation examples

- SPU-level with labels:
  - `python src/step8_imbalanced_rule.py --yyyymm 202509 --period A --analysis-level spu --target-yyyymm 202509 --target-period A`
- Subcategory-level standard:
  - `python src/step8_imbalanced_rule.py --yyyymm 202509 --period B --analysis-level subcategory`


