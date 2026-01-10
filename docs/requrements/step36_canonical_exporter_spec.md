# Step 36 Canonical Exporter Specification (Draft)

Status: Draft for approval
Owner: scripts/export_step36_canonical_views.py
Tests: test_export_step36_canonical_views.py
Scope: Non-invasive exporter; no pipeline code changes

## Overview
Produce clean, aggregated canonical JSON views from the Step 36 unified delivery output to feed the working fixed dashboard pattern. Preserves raw duplicates in Step 36 output but provides unique, validated dashboard inputs.

Inputs resolved via manifest when possible, else filename pattern:
- CSV: output/unified_delivery_{YYYYMM(A|B)}_*.csv

Outputs (JSON, records lists):
- output/fixed_stores_data.json
- output/fixed_clusters_data.json

## Duplicates Policy (for dashboard inputs)
- Preserve raw multi-line duplicates in pipeline outputs (no changes to existing CSV/XLSX).
- Export a canonical store-tag view unique on store-line key by aggregating duplicates:
  - Key: (Store_Code, Store_Group_Name, Target_Style_Tags)
- Rationale: Dashboard requires single unique rows per store/tag to avoid conflicting totals and inconsistent UI behavior. Canonical view aggregates category/subcategory/SPU lines contributing to the same store/tag.

## Store-Tag Canonical View
- Key: (Store_Code, Store_Group_Name, Target_Style_Tags)
- Dimensions carried with first value (if present):
  - Analysis_Year, Analysis_Month, Analysis_Period
  - Planning_Season, Planning_Year, Planning_Period_Label
  - Season, Gender, Location
  - Cluster_ID, Cluster_Name
  - Operational_Tag_Label, Temperature_Zone_Label
- Metrics aggregated by sum (if present):
  - Allocated_ΔQty_Rounded (rounded post-aggregation; Int64)
  - Group_ΔQty
  - Expected_Benefit
  - Sell_Through_Improvement
  - Capacity_Utilization
  - Priority_Score
  - Coverage_Index
  - Priority_Index
- Behavior:
  - Non-present columns are ignored gracefully for backward compatibility.
  - All key fields coerced to string prior to grouping.
  - Data types: numeric columns coerced with to_numeric(errors='coerce'); totals use float sum; allocated rounded to Int64 at the end.

## Cluster Summary View
- Key: Cluster_ID (placeholder "unknown" used if column missing).
- Aggregations:
  - Sum: Allocated_ΔQty_Rounded (rounded Int64), Group_ΔQty.
  - Store_Count: count of unique Store_Code contributing to the cluster.
  - First: Cluster_Name, Operational_Tag_Label, Temperature_Zone_Label,
    Cluster_Fashion_Profile, Cluster_Fashion_Ratio, cold_share, warm_share, moderate_share (if present).

## Validation and Tests
Automated tests in `test_export_step36_canonical_views.py` verify:
- Uniqueness: store view has no duplicates on (Store_Code, Store_Group_Name, Target_Style_Tags).
- Sum reconciliation: sum(Allocated_ΔQty_Rounded) matches between raw CSV and aggregated store view (integer-rounded totals expected to match exactly).
- Cluster sanity: cluster view non-empty when Cluster_ID present; optional sum consistency with store view.

Current results (202509B, 202509A):
- 202509B: raw duplicates on store-line key = 66,933; store view rows = 229,121; total Allocated_ΔQty_Rounded = 16,137; cluster rows = 48. All checks passed.
- 202509A: raw duplicates on store-line key = 234,661; store view rows = 109,628; total Allocated_ΔQty_Rounded = 14,892; cluster rows = 44. All checks passed.

## Non-Goals
- No modifications to upstream pipeline or Step 36 generation.
- No enforcement of duplicates policy in raw unified delivery outputs.
- No schema expansion beyond fields listed here (others are safely ignored).

## Acceptance Criteria
- Tests pass for target periods (A and B) with uniqueness and sum reconciliation OK.
- Canonical exports generate without errors via:
  - python3 scripts/export_step36_canonical_views.py --period-label 202509B
  - python3 scripts/export_step36_canonical_views.py --period-label 202509A
- JSON outputs contain unique store-line keys and cluster-level summaries suitable for direct loading by the fixed dashboard pattern.

## Next Steps
- Approve this duplicates policy and aggregation rules.
- Generate JSON for the approved target period(s) and store under `output/`.
- Wire into the dashboard generator (simple, single-file pattern) when we enter the dashboard phase.
