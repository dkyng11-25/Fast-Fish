# Step 36 — Unified Delivery Builder Specification

Path: `ProducMixClustering_spu_clustering_rules_visualization-copy/src/step36_unified_delivery_builder.py`
Function: `_build_unified(yyyymm, period, period_label, out_ts)`

## Overview
Step 36 consolidates upstream signals (allocation, capacity, sell-through, cluster labels, weather, fashion profile, etc.) into a retailer-ready unified delivery. It:
- Rounds store allocations to exact integers per group.
- Derives action, instruction, tag bundle, and priority.
- Normalizes and caps sell-through fields; recomputes improvement.
- Infers gender when missing and classifies store fashion profile.
- Produces QA and auxiliary reports.

## How to Run
- CLI: `--target-yyyymm YYYYMM` and `--target-period A|B`.
  - Example: `python src/step36_unified_delivery_builder.py --target-yyyymm 202509 --target-period A`

### Environment Switches
- `STEP36_PREFER_STEP14_DQTY` (truthy to prefer Step 14 ΔQty over Step 18).
- `STEP36_ENABLE_ADDS_REBALANCE` (truthy to enable adds-bias rebalancing; see below).

## Allocation Rounding & Reconciliation
- Rounds `Allocated_ΔQty` to `Allocated_ΔQty_Rounded` per group using a largest-remainder method and post-adjust tweak to ensure exact reconciliation to `Group_ΔQty`.
- Grouping keys for rounding/reconciliation:
  - Prefer: `Store_Group_Name × Category × Subcategory` when available.
  - Fallback: `Store_Group_Name × Target_Style_Tags`.
- `Target_SPU_Quantity` is set as an explicit business-facing alias of `Allocated_ΔQty_Rounded` (integer).

## Action, Instruction, Tags, Sorting, Ranking
- `Action`: sign of `Allocated_ΔQty_Rounded` → Add (>0), Reduce (<0), No-Change (=0).
- `Instruction`: concise guidance, e.g. `Add 3 SPUs in Category/Subcategory (Season, Gender, Location)`.
- `Tag_Bundle`: built from `[Season, Planning_Season, Gender, Location, Temperature_Band_Simple, Store_Fashion_Profile]`.
    - Removes NAs, preserves first-occurrence order, and de-duplicates via stable order.
    - Joined with `", "`; returns NA when no parts are available.
- Sorting: `Action_Order` (Add=0, Reduce=1, No-Change=2), then `Priority_Score` desc, then `Allocated_ΔQty_Rounded` desc. Stable mergesort.
- `Action_Priority_Rank`: within each `Action`, dense rank on `Priority_Score` descending.

## ΔQty Provenance & Overrides
- `Group_ΔQty_source` — Row-level provenance of the group ΔQty (initialized from upstream).
- Prefer Step 18 ΔQty unless overridden by env `STEP36_PREFER_STEP14_DQTY` (truthy to prefer Step 14).
  - Merge Step 18 group values on available keys among: `Store_Group_Name`, `Target_Style_Tags`, `Category`, `Subcategory`.
  - If `Group_ΔQty_step18` is present for a row, set `Group_ΔQty` to it and set `Group_ΔQty_source = "step18"`.
  - A side report of mismatches between the pre-override value and Step 18 (`group_dqty_step18_mismatch_{period_label}_{timestamp}.csv`) is written when differences are detected.
  - Adds-bias rebalancing, when enabled, appends `+adds_bias` to `Group_ΔQty_source` (see section below).

## Priority Score
- Columns ensured to exist (filled with NA if absent): `Expected_Benefit`, `Confidence_Score`, `Sell_Through_Improvement`, `Capacity_Utilization`.
- Normalization: min-max per column. Degenerate handling:
  - Constant series (`max == min`) → normalized = `0.5` for all rows.
  - All values NA → normalized = `NA`; the final weighted formula uses `0.5` via fillna for that component.
- Suitability term: `su = 1 - norm(Capacity_Utilization)` (lower utilization → higher suitability).
- Final formula (each component uses `fillna(0.5)` before weighting):
  - `Priority_Score = 0.45*EB + 0.25*CS + 0.20*ST_Improvement + 0.10*su`.

## Planning & Analysis Period Fields
- `Planning_Season` — Derived from `--target-yyyymm` month via explicit mapping:
  - Winter: Dec/Jan/Feb → months 12, 1, 2
  - Spring: Mar/Apr/May → months 3, 4, 5
  - Summer: Jun/Jul/Aug → months 6, 7, 8
  - Autumn: Sep/Oct/Nov → all other months (9, 10, 11)
- `Planning_Year` — Integer `YYYY` parsed from `--target-yyyymm`.
- `Planning_Period_Label` — Pass-through of the period label (`A` or `B`) from CLI.
- `Analysis_Year` — String `YYYY` (4-digit, zero-padded) from `--target-yyyymm`.
- `Analysis_Month` — String `MM` (2-digit, zero-padded) from `--target-yyyymm`.
- `Analysis_Period` — String of the input period (typically `"A"` or `"B"`).
- Failure handling: if parsing of `--target-yyyymm` fails, `Planning_Season`/`Planning_Year` are set to NA, `Planning_Period_Label` is still set; `Analysis_Year`/`Analysis_Month` are NA and `Analysis_Period` is still set to the input period.
- Season backfill: when `Season` is missing but `Planning_Season` is present, `Season` is set to `Planning_Season` and `Season_source` is appended with `+planning_fill`.
- Tag hint: when `Planning_Season`/`Planning_Year` differ from `Season`, a hint like `"Autumn 2025"` is appended to `Target_Style_Tags` if not already present.

## Temperature & Historical Temperature
- Source column detection: pick the first column whose name contains both `"temp"` and `("band" or "zone")` (case-insensitive). If none, fall back to `Store_Temperature_Band` when present. This selected column is referred to as `temp_col`.
- `Temperature_Value_C` — Parsed numeric °C from `temp_col` via regex `([\-\d\.]+)\s*°?C` (e.g., `19.3°C (Moderate-Central)` → `19.3`).
- `Temperature_Band_Simple` — Derived from `temp_col` text using heuristics:
  - Contains `Cold` or `冷` → `Cold`
  - Contains `Warm`, `热`, or `Hot` → `Warm`
  - Otherwise → `Moderate`
  - If missing but `Temperature_Zone` exists: derive from zone (`Warm`/`热` → `Warm`; `Cold`/`冷` → `Cold`; else `Moderate`).
- `Temperature_Suitability_Graded` — Combines `Temperature_Band_Simple` with `Temperature_Zone`:
  - Missing either → `Unknown`
  - Zone contains `Cold` and simple is `Cold`, or zone contains `Warm` and simple is `Warm` → `High`
  - Simple is `Moderate` → `Medium`
  - Otherwise → `Review`
- `Temperature_Band_Detailed` — 6 bands from `Temperature_Value_C` (Autumn thresholds):
  - `< 12.0` → `Cold`
  - `12.0–<16.0` → `Cool`
  - `16.0–<18.0` → `Mild`
  - `18.0–<20.0` → `Moderate`
  - `20.0–≤22.5` → `Warm`
  - `> 22.5` → `Hot`
- `Cluster_Temp_C_Mean` — Mean `Temperature_Value_C` per `Cluster_ID` when present.
- `Cluster_Temp_Quintile` — Computed from `Cluster_Temp_C_Mean` via 5-quantiles with labels: `Q1-Coldest`, `Q2`, `Q3`, `Q4`, `Q5-Warmest` (only when enough non-NA values are available).
- Historical profile (best-effort join): if `output/historical_cluster_temperature_profile.csv` exists and `Cluster_ID` is present, it is joined on `Cluster_ID`, contributing fields like `Historical_Temp_C_Mean`, `Historical_Temp_C_P5`, `Historical_Temp_C_P95`, `Historical_Temp_Band_Detailed`, `Historical_Temp_Quintile`.
- `Temp_Band_Divergence` — Boolean flag: `Temperature_Band_Detailed` string differs from `Historical_Temp_Band_Detailed`.

## Constraint Status
- Built from two parts and concatenated as `"{capacity_part}, {temp_part}"`:
  - Capacity part from `Capacity_Utilization` (coerced numeric):
    - Present and `< 0.95` → `Capacity OK`
    - Present and `≥ 0.95` → `Capacity Tight`
    - Missing → `Unknown`
  - Temperature part from `Temperature_Suitability_Graded`:
    - `High` → `Temp OK`
    - `Medium` or `Review` → `Temp Review`
    - Missing/other → `Temp Unknown`

## Sell-Through Fields
- Column coalescing: if both `Sell_Through_Rate` and `Current_Sell_Through_Rate` exist, `Sell_Through_Rate` is renamed to `Store_Sell_Through_Rate` (store-level fallback).
- `Current_Sell_Through_Rate`:
  - Source order and flags (`Current_ST_source`):
    - Step 18 value when present → `step18`.
    - Else `Store_Sell_Through_Rate` → `store_level`.
    - Else baseline fallback 0.67 → `fallback_baseline`.
  - Always clipped to `[0, 1]`.
- `Target_Sell_Through_Rate`:
  - Source order and flags (`Target_ST_source`):
    - Step 18 value when present → `step18`.
    - Else computed as `(Current_Sell_Through_Rate + 0.10).clip(0, 1)` → `computed+10pp`.
  - Always clipped to `[0, 1]`.
  - Historical capping (when any historical distribution is available from one of: `Historical_ST_Frac`, `Historical_ST_Pct/100`, `Historical_Sell_Through_Rate/100`, `Store_Sell_Through_Rate`):
    - Compute global cap at `p95` of the available historical series; default cap value `0.95` if quantile not computable.
    - If `Target_Sell_Through_Rate > cap`, set to `cap` and record:
      - `Target_ST_cap_percentile = 0.95`, `Target_ST_cap_value = cap`, `Target_ST_capped_flag = True`.
      - Append `+capped_p95_hist` to `Target_ST_source` (or set to `capped_p95_hist` if previously NA).
    - Otherwise record the same `cap` metadata with `Target_ST_capped_flag = False`.
- `Sell_Through_Improvement`:
  - If present from Step 18, mark `Improvement_source = step18` where not NA.
  - Compute default improvement `imp = (tgt - cur).clip(-1, 1)` with `cur = current.fillna(0.67)` and `tgt = target.fillna((cur + 0.10).clip(0,1))` and fill only where missing; set `Improvement_source = computed_target_minus_current` for those rows.
  - Later, after clipping current/target to `[0,1]`, recompute strictly for all rows: `Sell_Through_Improvement = Target_Sell_Through_Rate - Current_Sell_Through_Rate` (clipped to `[-1, 1]`). If `Sell_Through_Improvement_source` column exists, it is set to `recomputed_target_minus_current`.
  - If `Target_ST_capped_flag` is True, append `+target_capped_p95_hist` to `Improvement_source`.
- `Confidence_Score`:
  - If present, `Confidence_Score_source = step18` where not NA.
  - Else fallback composite when missing (`Confidence_Score_source = composite_fallback`):
    - `0.4 * norm(Expected_Benefit) + 0.3 * norm(|Sell_Through_Improvement|) + 0.3 * (1 - norm(Capacity_Utilization))`, clipped to `[0,1]`.
- Validated views/flags (do not alter raw fields):
  - `Expected_Benefit_valid`, `Expected_Benefit_range_flag`.
  - `Current_Sell_Through_Rate_valid`, `Current_ST_range_flag`.
  - `Target_Sell_Through_Rate_valid`, `Target_ST_range_flag`.
  - `Sell_Through_Improvement_valid`, `ST_Improvement_range_flag`.
  - `Capacity_Utilization_valid`, `Capacity_range_flag`.

## Fashion Profile & Gender
- `Store_Fashion_Ratio_Normalized`: selected from store/group-level signals when available; otherwise tried from Step 14 cluster fashion makeup; final fallback from fashion/basic counts when present.
- `Store_Fashion_Profile` buckets: default thresholds 0.35/0.65 with auto-tuning to q20/q80 if a single bucket dominates (>90%) and sample size > 100. Thresholds recorded in `Store_Fashion_Profile_thresholds`.
- Gender backfill (only when missing):
  - From percentage columns: `women_percentage(_ff14)`, `men_percentage(_ff14)`, `unisex_percentage(_ff14)` when any present and dominant share ≥ 0.55.
  - From `Subcategory`/`Category` text heuristics (中/女/男, unisex/men/women tokens).
  - From tokens parsed out of `Target_Style_Tags`.
  - Provenance appended to `Gender_source`. If profile is `Balanced` and `Gender` missing, backfill to `Unisex`.

## Cluster Mapping & Labels
- Coalesces multiple possible cluster ID columns to a single `Cluster_ID` (typed `Int64` when possible) and drops alternates.
- Prefers Step 24 labels to fill missing: `Cluster_Name`, `Operational_Tag`, `Temperature_Zone`.

## Growth Potential
- Recomputed from quantiles of `Sell_Through_Improvement` and `Capacity_Utilization`:
  - High-Growth, Growth-Ready, Constrained, Maintain (quantile thresholds are recorded in an external report).
- Distribution report written (see Outputs).

## Adds-Bias Rebalancing (optional)
- Enabled with `STEP36_ENABLE_ADDS_REBALANCE`.
- Ensures at least ~35% of groups are positive by promoting up to N negative groups meeting basic criteria (`Sell_Through_Improvement ≥ 0.08` or `Capacity_Utilization ≤ 0.80`).
- Positive amount heuristic base 2 SPUs (+1 if improvement ≥ 0.15; +1 if capacity ≤ 0.70). Provenance annotated in `Group_ΔQty_source` with `+adds_bias`.
- Grouping keys match rounding grain.

## Final Column Order
Preferred final ordering (columns missing upstream are skipped; any extras are appended at the end):

```
Analysis_Year, Analysis_Month, Analysis_Period, Store_Code, Store_Group_Name,
Target_Style_Tags, Category, Subcategory, Target_SPU_Quantity, Allocated_ΔQty_Rounded,
Allocated_ΔQty, Group_ΔQty, Action, Instruction, Action_Priority_Rank, Tag_Bundle,
Expected_Benefit, Confidence_Score, Current_Sell_Through_Rate, Target_Sell_Through_Rate,
Sell_Through_Improvement, Store_Sell_Through_Rate, Constraint_Status, Capacity_Utilization,
Store_Temperature_Band, Temperature_Band_Simple, Temperature_Band_Detailed, Temperature_Value_C,
Cluster_Temp_C_Mean, Cluster_Temp_Quintile, Temperature_Suitability_Graded, Store_Fashion_Profile,
Action_Priority, Performance_Tier, Growth_Potential, Risk_Level, Cluster_ID, Cluster_Name,
Operational_Tag, Temperature_Zone, Season, Season_source, Gender, Gender_source, Location,
Location_source, Planning_Season, Planning_Year, Planning_Period_Label, Data_Based_Rationale,
Priority_Score, Historical_Temp_C_Mean, Historical_Temp_C_P5, Historical_Temp_C_P95,
Historical_Temp_Band_Detailed, Historical_Temp_Quintile, Temp_Band_Divergence
```

Additional formatting:
- `Target_Style_Tags` coerced to bracketed string form (e.g., `[Men, Autumn]`).
- `Allocated_ΔQty_Rounded` coerced to integer; `Target_SPU_Quantity` mirrors it exactly.

## Outputs
Files are written under `output/` with base `unified_delivery_{period_label}_{timestamp}`:
- Primary: `... .csv` (always)
- Optional: `... .xlsx` with a “Unified Data” sheet and minimalist data dictionary sheet (requires `openpyxl`).
- QA JSON: `... _validation.json`.
- Top lists: `... _top_adds.csv`, `... _top_reduces.csv`; Autumn-only: `... _top_adds_autumn.csv`, `... _top_reduces_autumn.csv` (filtered by `Season` or `Planning_Season` containing `Autumn|秋`).
- Cluster-level summary: `unified_delivery_cluster_level_{period_label}_{timestamp}.csv`.
- Side reports (best-effort):
  - `group_dqty_step18_mismatch_{period_label}_{timestamp}.csv` (when Step 18 ΔQty overrides differ).
  - `... _adds_rebalance_summary.md` (when adds-bias is applied).
  - `... _growth_distribution.md` (quantiles and category counts for Growth Potential).
  - `... _group_reconciliation_mismatches.csv` (when group sums don’t reconcile after rounding).
### Excel Data Dictionary Contents
When the optional Excel is written, the "Data Dictionary" sheet currently includes the following columns and descriptions (source: `src/step36_unified_delivery_builder.py`):

- Analysis_Year — 4-digit year for analysis window (string)
- Analysis_Month — 2-digit month for analysis window (string, zero-padded)
- Analysis_Period — Period within month: "A" or "B"
- Target_SPU_Quantity — Integer target SPU quantity per store line (alias of `Allocated_ΔQty_Rounded`)
- Allocated_ΔQty_Rounded — Integer store allocation reconciled to `Group_ΔQty`
- Allocated_ΔQty — Raw fractional store allocation from Step 32
- Group_ΔQty — Group-level ΔQty from Step 18/14
- Priority_Score — Composite score of benefit, confidence, trend, suitability
- Constraint_Status — Store constraint status from Step 33
- Capacity_Utilization — Store capacity utilization (0..1) from Step 33

Outputs are registered to the step manifest via `register_step_output(...)`.

## QA Checks (written to JSON)
- `group_sum_reconciliation`: per rounding grain, check sum of `Allocated_ΔQty_Rounded` equals rounded `Group_ΔQty`.
- `required_columns_missing_counts`: presence/null counts for core columns.
- `allocated_qty_integer_check`: integer coercion check for `Allocated_ΔQty_Rounded`.
- `target_qty_consistency`: `Target_SPU_Quantity` equals `Allocated_ΔQty_Rounded`.
- `duplicate_on_store_line_key`: duplicates on (`Store_Code`, `Store_Group_Name`, `Target_Style_Tags`).

## Notes
- Some columns are pass-through from upstream steps and may be absent depending on data availability (e.g., `Action_Priority`, `Performance_Tier`, `Risk_Level`, temperature band details).
- `Group_ΔQty_source`, `Current_ST_source`, `Target_ST_source`, `Improvement_source`, and `Confidence_Score_source` track provenance.
