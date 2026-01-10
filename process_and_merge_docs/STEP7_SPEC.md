### Name

- Rule 7: Missing Category/SPU with Quantity Recommendations and Fast Fish Sell-Through Validation

### Purpose

- Identify stores missing subcategories or SPUs that sell well in their cluster peers.
- Recommend concrete unit quantities for a 15-day target period.
- Gate recommendations with Fast Fish sell-through validation and optional ROI thresholds.

### Inputs

- Period Resolution (via `src/config.py`)
  - `get_current_period()` → `(yyyymm, period)`; defaults can be overridden by CLI or env.
  - `get_period_label(yyyymm, period)` → `"YYYYMMA|B|YYYYMM"`.
  - `get_api_data_files(yyyymm, period)` returns:
    - `store_config`: `data/api_data/store_config_{period_label}.csv`
    - `store_sales`: `data/api_data/store_sales_{period_label}.csv`
    - `category_sales`: `data/api_data/complete_category_sales_{period_label}.csv`
    - `spu_sales`: `data/api_data/complete_spu_sales_{period_label}.csv`
  - `get_output_files(analysis_level, yyyymm, period)['clustering_results']` → clustering results path.

- Required Data Files
  - Clustering results (SPU or subcategory pipeline output)
    - Path: resolved as above; fallback checks: `output/clustering_results_{analysis_level}_{period_label}.csv`, `output/enhanced_clustering_results.csv`, `output/clustering_results.csv`.
    - Required columns: `str_code` (string), either `Cluster` or `cluster_id`.
  - Sales data (choose by `--analysis-level`)
    - SPU: `complete_spu_sales_{period_label}.csv`; required columns: `str_code`, `spu_code`, `spu_sales_amt`.
    - Subcategory: `complete_category_sales_{period_label}.csv`; required columns: `str_code`, `sub_cate_name`, `sal_amt`.
  - Optional quantity data
    - `store_sales_{period_label}.csv` (preferred) or `data/api_data/store_sales_data.csv`.
    - Expected fields if present: `base_sal_qty`, `fashion_sal_qty`, `base_sal_amt`, `fashion_sal_amt`.
    - Derived fields used: `total_qty`, `total_amt`, `avg_unit_price`.
  - Optional category price estimates (SPU analysis)
    - Derived from SPU sales samples to estimate `estimated_unit_price` by `(cate_name, sub_cate_name)`.

- Optional Historical Data for Validator
  - Loaded via `src/sell_through_validator.py` helper; used to predict sell-through and compliance.

### Parameters and Flags

• CLI arguments (exact)
  - `--yyyymm YYYYMM`
  - `--period {A,B,full}` (full treated as None)
  - `--analysis-level {spu,subcategory}` (default: `spu`)
  - `--seasonal-blending`
  - `--seasonal-yyyymm YYYYMM`
  - `--seasonal-period {A,B,full}` (full treated as None)
  - `--seasonal-weight <float>` (default 0.6; recent weight = 1 - seasonal)
  - `--target-yyyymm YYYYMM` (labeling only)
  - `--target-period {A,B,full}` (labeling only; full treated as None)

• Thresholds (internally set; effective defaults)
  - Subcategory: `MIN_CLUSTER_STORES_SELLING = 0.70`, `MIN_CLUSTER_SALES_THRESHOLD = 100`, `MIN_OPPORTUNITY_VALUE = 50`.
  - SPU: `MIN_CLUSTER_STORES_SELLING = 0.80`, `MIN_CLUSTER_SALES_THRESHOLD = 1500`, `MIN_OPPORTUNITY_VALUE = 500`.
  - Note: `MAX_MISSING_SPUS_PER_STORE = 5` is defined but not actively enforced in the current code path.
  - Quantities scaled to a 15-day target period by `SCALING_FACTOR = TARGET_PERIOD_DAYS / DATA_PERIOD_DAYS` (both default 15).

- Fast Fish and ROI Flags (environment variables)
  - `RULE7_USE_ROI=1|0` (default on).
  - `ROI_MIN_THRESHOLD` (default `0.3`).
  - `MIN_MARGIN_UPLIFT` (default `100`).
  - `MIN_COMPARABLES` (default `10`).
  - `MARGIN_RATE_DEFAULT` (default `0.45`).

### Processing Overview

1) Load Configuration and Data
  - Resolve period and file paths via `src.config`.
  - Load clustering and sales; validate required columns.
  - Optionally apply seasonal-recent blending for sales; weight and aggregate.
  - Load quantity data; compute `avg_unit_price` per store; compute category price estimates when needed (SPU).

2) Identify Well-Selling Features
  - Merge sales with clusters using a safe left join; log merge diagnostics; compute per-cluster counts and totals.
  - Filter by adoption rate and sales thresholds to get candidate `(cluster_id, feature)`.

3) Compute Missing Opportunities
  - For each candidate `(cluster_id, feature)`, find stores in cluster not selling the feature.
  - Compute `avg_sales_per_store` from cluster totals; derive recommended quantities using unit-price estimates.
  - Quantities are integer-ceiled for practicality (SPU path); record `investment_required` and provenance (`price_source`).

4) Fast Fish Validation and ROI (if enabled)
  - Initialize `SellThroughValidator` if import and data succeed.
  - Derive conservative adoption-based predicted sell-through; optionally override with validator prediction.
  - Approval criteria (all must be met when validator is available):
    - Validator compliance is True
    - Peer stores selling count ≥ 5
    - Peer adoption ≥ 25%
    - Predicted sell-through from adoption ≥ 30%
  - Optional ROI gates (when `RULE7_USE_ROI=1`): enforce `ROI_MIN_THRESHOLD`, `MIN_MARGIN_UPLIFT`, and `MIN_COMPARABLES`.

5) Aggregate Store Results
  - Sum quantities and investments per store; compute averages for sell-through metrics where available.
  - Set rule flags per store and attach metadata fields (thresholds, analysis level, fast fish tag).

### Outputs

- Period-Labeled Files (always written)
  - Results per store:
    - `output/rule7_missing_{analysis}_sellthrough_results_{period_label}.csv`
    - Columns include: `str_code`, `cluster_id`, counts (`missing_categories_count`|`missing_spus_count`), `total_opportunity_value`, `total_quantity_needed`, `total_investment_required`, `avg_sellthrough_improvement`, `avg_predicted_sellthrough`, `fastfish_approved_count`, plus metadata columns including `rule7_description`, `rule7_threshold`, `rule7_analysis_level`, `rule7_sellthrough_validation`, `rule7_fastfish_compliant`.
  - Opportunities detail (when any approved):
    - `output/rule7_missing_{analysis}_sellthrough_opportunities_{period_label}.csv`
    - Columns include per recommendation: `str_code`, `cluster_id`, feature column (`sub_cate_name`|`spu_code`), `opportunity_type`, `cluster_total_sales`, `stores_selling_in_cluster`, `cluster_size`, `pct_stores_selling`, `expected_sales_opportunity`, `current_quantity`, `recommended_quantity_change` (integer-ceiled), `unit_price`, `investment_required`, `recommendation_text`, `price_source`, sell-through metrics (`current_sell_through_rate`, `predicted_sell_through_rate`, `sell_through_improvement`, `fast_fish_compliant`), ROI fields (`roi`, `margin_uplift`, `n_comparables`) when enabled.
  - Summary report:
    - `output/rule7_missing_{analysis}_sellthrough_summary_{period_label}.md` (includes counts, investment, sell-through distribution, diagnostics, top opportunities).

- Backward-Compatible File (subcategory analysis only)
  - `output/rule7_missing_category_results.csv` (same store-level results, without period suffix), to avoid breaking downstream consumers.

### Failure Modes and Behavior

- Missing clustering or sales files → explicit `FileNotFoundError` with list of checked paths.
- Missing required sales columns → explicit `ValueError` listing missing columns.
- Missing validator or failure to initialize → script continues; opportunities require validator for approval (default strict gate).
  - Note: With validator unavailable, the script will typically produce zero approved opportunities by design (no silent fallback approvals).
- Seasonal blending files not found → logged warning; proceed with current-period sales only.

### Invocation Examples

- SPU-level, with seasonal blending and labeled outputs
  - `python src/step7_missing_category_rule.py --yyyymm 202509 --period A --analysis-level spu --seasonal-blending --seasonal-yyyymm 202408 --seasonal-period B --seasonal-weight 0.6 --target-yyyymm 202509 --target-period A`

- Subcategory-level, current-period only
  - `python src/step7_missing_category_rule.py --yyyymm 202509 --period B --analysis-level subcategory`

### Upstream/Downstream Contracts

- Upstream: clustering step produces `str_code` and either `Cluster` or `cluster_id`; sales exports for the chosen level include required columns.
- Downstream (Steps 13/14): rely on standardized quantity columns and rule flags; preserve column names and types to avoid breaking aggregations and Fast Fish formatting.


