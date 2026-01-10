### Name

- Rule 13: Consolidate SPU rule outputs with SPU-detail preservation, labeled outputs, and optional real-data trend exports

### Purpose

- Combine SPU-level outputs from Steps 7–12 into consolidated store-level and detailed SPU-level artifacts, preserving real data, avoiding synthesis, and registering labeled outputs for traceability. Offer optional trend export formats (real-data only) behind a feature flag.

### Inputs

- Rule outputs (prefer detailed where available; otherwise legacy):
  - Step 7: `output/rule7_missing_spu_sellthrough_opportunities.csv` (fallback: results)
  - Step 8: `output/rule8_imbalanced_spu_cases.csv` (fallback: results)
  - Step 9: `output/rule9_below_minimum_spu_sellthrough_opportunities.csv` (fallback: results)
  - Step 10: `output/rule10_spu_overcapacity_opportunities.csv`
  - Step 11: `output/rule11_improved_missed_sales_opportunity_spu_details.csv` (fallback: results)
  - Step 12: `output/rule12_sales_performance_spu_details.csv` (fallback: results)
- Clusters: `output/clustering_results_spu.csv`
- Period label via `src.config.get_current_period` and `get_period_label` (for period-labeled copies and manifest).

### Parameters and Flags

- Performance: `FAST_MODE` (default True), `TREND_SAMPLE_SIZE`, `CHUNK_SIZE_SMALL`.
- Enrichment: `ENABLE_TREND_UTILS` (default False) to emit fashion/comprehensive/granular outputs; must use real data; skip when missing.

### Processing Overview

1) Resolve input files: choose preferred detailed filenames; fall back to legacy names if preferred missing; log chosen set.
2) Load each rule file chunked; standardize column names; map quantity/investment columns; keep NA; avoid synthetic fills.
3) Preserve SPU-level detail: concatenate standardized SPU records; deduplicate by (`str_code`,`spu_code`); add `cluster` mapping if available; add or map `sub_cate_name` if available.
4) Save detailed SPU consolidated outputs (unlabeled and period-labeled) and register in manifest.
5) Aggregate to store-level and optional cluster×subcategory summaries; save and register; keep legacy filenames for back-compat.
6) Optional trend enrichment (if `ENABLE_TREND_UTILS=True`):
  - Fashion enhanced (20-col) and comprehensive trends (51-col) emitted using only real data sources; NA when missing; no synthetic defaults.

### Outputs

- Detailed SPU consolidated (primary):
  - `output/consolidated_spu_rule_results_detailed.csv`
  - `output/consolidated_spu_rule_results_detailed_{period_label}.csv`
- Store-level summary (back-compat): `output/consolidated_spu_rule_results.csv`
- Cluster×subcategory summary (optional): `output/consolidated_cluster_subcategory_results.csv`
- Trend exports (optional, real-data only):
  - Fashion enhanced: `output/fashion_enhanced_suggestions.csv`
  - Comprehensive trends: `output/comprehensive_trend_enhanced_suggestions.csv`
- Manifest: entries for detailed and period-labeled files; optional entries for trend exports when enabled.

### Failure Modes

- Missing files for some rules → proceed with remaining; log missing; ensure outputs still generated.
- Missing columns per rule → attempt safe mapping; otherwise leave NA; avoid fabricating values.
- Cluster/subcategory mapping unavailable → leave NA, continue.

### Invocation example

- Default (consolidation only): `python src/step13_consolidate_spu_rules.py --target-yyyymm 202509 --target-period A`
- With enrichment (dev/QA only): set `ENABLE_TREND_UTILS=True` in code or via env, ensuring required real data sources exist.


