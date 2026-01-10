# Step 10 SPU Overcapacity: Column Documentation

Source: `src/step10_spu_assortment_optimization.py` → `fast_expand_spu_data()`

Purpose: Define how each output column is derived at SPU level for overcapacity analysis using real SPU codes and real unit quantities.

Version: Fast optimized pipeline with real quantities and margin rates (updated 2025-06-24)

## Column Index (as produced by `fast_expand_spu_data()`)

Base dimensions and category context (from `expanded_record`):
1. str_code
2. str_name
3. Cluster
4. season_name
5. sex_name
6. display_location_name
7. big_class_name
8. sub_cate_name
9. yyyy
10. mm
11. mm_type
12. sal_amt
13. sty_sal_amt
14. category_current_spu_count
15. category_target_spu_count
16. category_excess_spu_count
17. category_overcapacity_percentage
18. category_total_sales
19. spu_code
20. spu_sales
21. spu_sales_share
22. overcapacity_percentage  (legacy compatibility: duplicate of category_overcapacity_percentage)
23. excess_spu_count        (legacy compatibility: duplicate of category_excess_spu_count)

Quantity join (optional, from API quantity files):
24. base_sal_qty (optional)
25. fashion_sal_qty (optional)
26. sal_qty (optional)
27. quantity (optional)
28. spu_sales_amt (optional)
29. quantity_real

Calculated unit economics and scaling:
30. unit_price
31. current_quantity

Reduction mechanics:
32. potential_reduction
33. constrained_reduction
34. recommend_reduction
35. recommended_quantity_change

Margin/ROI:
36. margin_rate
37. retail_value
38. investment_required
39. estimated_cost_savings
40. margin_per_unit
41. expected_margin_uplift
42. roi_percentage

UX/Logging:
43. recommendation_text

Notes:
- Optional columns (24–28) appear only if present in the quantity data source.
- `quantity_real` is computed from available qty columns and is always present after the merge.
- `overcapacity_percentage` and `excess_spu_count` at the SPU level mirror the category metrics for legacy compatibility.

---

## Column 1: str_code
- Definition: Store code identifier.
- Type: string
- Source/Logic: Set directly from the input planning/config row.
  - Code: `expanded_record['str_code'] = row['str_code']`
  - Later cast to string before joins: `expanded_df['str_code'] = expanded_df['str_code'].astype(str)`
- Dependencies: Used to join with quantity and margin data (`['str_code','spu_code']`).
- Edge cases: Must exist in input; not nullable by design in upstream data.
- Validation suggestions:
  - Non-null ratio should be ~100%.
  - Unique pairing with `spu_code` after expansion should make sense (many-to-many across stores).

## Column 2: str_name
- Definition: Store name (human-readable label for `str_code`).
- Type: string (nullable)
- Source/Logic: Optional; copied if present, otherwise NA.
  - Code: `expanded_record['str_name'] = row.get('str_name', pd.NA)`
- Dependencies: None functionally; informational only.
- Edge cases: Missing values allowed and expected when source file lacks `str_name`.
- Validation suggestions:
  - If present, ensure consistency for the same `str_code`.

## Column 3: Cluster
- Definition: Store cluster identifier used for segment-level analysis.
- Type: string (nullable)
- Source/Logic: Prefer `Cluster` if present; otherwise fallback to `cluster_id` from the merged clustering file.
  - Code: `expanded_record['Cluster'] = row.get('Cluster', row.get('cluster_id', pd.NA))`
  - Upstream merge: In `fast_pipeline_analysis()`, the input `df` is `planning_df.merge(cluster_df, on='str_code', how=JOIN_MODE)`, where `cluster_df` is loaded from `output/clustering_results_spu.csv`.
- Dependencies: Depends on successful merge of clustering results by `str_code` ahead of expansion.
- Edge cases:
  - Missing cluster mapping for some stores → value may be NA.
  - If both `Cluster` and `cluster_id` exist, `Cluster` takes precedence.
- Validation suggestions:
  - Coverage: Non-null ratio should be high (ideally ~100% after the merge).
  - Consistency: `Cluster` should be constant for a given `str_code` within a run.

## Column 4: season_name
- Definition: Season label for the source sales/planning row.
- Type: string (nullable)
- Source/Logic: Copied from input if present; otherwise NA.
  - Code: `expanded_record['season_name'] = row.get('season_name', pd.NA)`
- Dependencies: None for calculation; used as a contextual dimension and for diagnostics.
- Edge cases:
  - May be missing depending on the upstream file; allowed.
- Validation suggestions:
  - If populated, ensure reasonable cardinality and consistency within store/category.

## Column 5: sex_name
- Definition: Gender segment label (e.g., Men, Women, Unisex) for the category/SPU context.
- Type: string (nullable)
- Source/Logic: Copied from input if present; otherwise NA.
  - Code: `expanded_record['sex_name'] = row.get('sex_name', pd.NA)`
- Dependencies: None; used for slicing, reporting, and diagnostics.
- Edge cases:
  - Missing or inconsistent capitalization may occur depending on source systems.
- Validation suggestions:
  - Normalize casing if needed upstream; verify reasonable cardinality.

## Column 6: display_location_name
- Definition: In-store display location label (e.g., Front, Backwall, Promo), describing where the SPU/category is displayed.
- Type: string (nullable)
- Source/Logic: Copied from input if present; otherwise NA.
  - Code: `expanded_record['display_location_name'] = row.get('display_location_name', pd.NA)`
- Dependencies: None; used as context and for optional segmentation.
- Edge cases:
  - May be sparse or missing; acceptable.
- Validation suggestions:
  - If populated, check for consistent mapping across `str_code` and category.

## Column 7: big_class_name
- Definition: High-level merchandise class/category grouping.
- Type: string (nullable)
- Source/Logic: Copied from input if present; otherwise NA.
  - Code: `expanded_record['big_class_name'] = row.get('big_class_name', pd.NA)`
- Dependencies: None; used for hierarchical rollups in reporting/aggregation.
- Edge cases:
  - Missing values acceptable; ensure stable naming conventions upstream if relied upon for grouping.
- Validation suggestions:
  - Verify that `big_class_name` groups a reasonable number of `sub_cate_name` values.

## Column 8: sub_cate_name
- Definition: Subcategory name (child of `big_class_name`) that the SPU belongs to in the source row.
- Type: string (nullable)
- Source/Logic: Copied from input if present; otherwise NA.
  - Code: `expanded_record['sub_cate_name'] = row.get('sub_cate_name', pd.NA)`
- Dependencies: None; used as a key category dimension for analysis.
- Edge cases:
  - Missing values acceptable; ensure relationship with `big_class_name` is consistent.
- Validation suggestions:
  - Check one-to-many hierarchy from `big_class_name` → `sub_cate_name`.

## Column 9: yyyy
- Definition: Year of the source record.
- Type: passthrough from source (int-like or string; nullable)
- Source/Logic: Copied from input if present; otherwise NA.
  - Code: `expanded_record['yyyy'] = row.get('yyyy', pd.NA)`
- Dependencies: None within `fast_expand_spu_data()`; contextual/time dimension.
- Edge cases:
  - May be missing; allowed. Upstream CSV typing may vary (int vs string).
- Validation suggestions:
  - Range-check (e.g., 2000–2100) and consistency with `mm` and `mm_type` if present.

## Column 10: mm
- Definition: Month of the source record (1–12).
- Type: passthrough from source (int-like or string; nullable)
- Source/Logic: Copied from input if present; otherwise NA.
  - Code: `expanded_record['mm'] = row.get('mm', pd.NA)`
- Dependencies: None within `fast_expand_spu_data()`; contextual/time dimension.
- Edge cases:
  - May be missing or typed as string; acceptable.
- Validation suggestions:
  - Range-check (1–12) and cross-check with `yyyy` and `mm_type` if applicable.

## Column 11: mm_type
- Definition: Period type label for the month (e.g., sub-period indicator).
- Type: passthrough from source (string; nullable)
- Source/Logic: Copied from input if present; otherwise NA.
  - Code: `expanded_record['mm_type'] = row.get('mm_type', pd.NA)`
- Dependencies: None within `fast_expand_spu_data()`; contextual/time dimension.
- Edge cases:
  - May be missing depending on data provider; acceptable.
- Validation suggestions:
  - Check consistency with `yyyy` and `mm` values if used for period grouping.

## Column 12: sal_amt
- Definition: Original row-level sales amount for the subcategory context (pre-expansion).
- Type: numeric (nullable)
- Source/Logic: Copied from input if present; otherwise NA.
  - Code: `expanded_record['sal_amt'] = row.get('sal_amt', pd.NA)`
- Dependencies: None for reduction math; retained for context/reference.
- Edge cases:
  - May be absent in some files; acceptable.
- Validation suggestions:
  - If present, should be non-negative; optional reconciliation with `category_total_sales` for reasonableness.

## Column 13: sty_sal_amt
- Definition: SPU-level sales amount for this specific SPU, extracted from the JSON payload of the source row.
- Type: numeric (float)
- Source/Logic: Set from the parsed JSON value for the current `spu_code`.
  - Code: `expanded_record['sty_sal_amt'] = spu_sales` where `spu_sales = float(spu_data[spu_code])`
  - Note: In the source file, `sty_sal_amt` originally contains a JSON string at the category row; after expansion, this column is repurposed to hold the per-SPU numeric amount.
- Dependencies: Depends on successful JSON parse of `row['sty_sal_amt']` upstream in the loop.
- Edge cases:
  - SPUs with non-positive sales are skipped; values should be > 0 in the expanded set.
- Validation suggestions:
  - Sum by group (store/category) should approximate `category_total_sales` allowing for filtering and positive-value selection.

## Column 14: category_current_spu_count
- Definition: Current number of SPUs in the category context of the source row.
- Type: numeric (float)
- Source/Logic: Taken from `row['ext_sty_cnt_avg']` and cast to float.
  - Code: `current_spu_count = float(row['ext_sty_cnt_avg'])` then `expanded_record['category_current_spu_count'] = current_spu_count`
- Dependencies: Requires `ext_sty_cnt_avg` present in input config.
- Edge cases:
  - If missing/invalid, the row is effectively skipped earlier by logic that only processes valid overcapacity candidates.
- Validation suggestions:
  - Non-negative; in expanded output it will be >= `category_target_spu_count` by construction (only overcapacity expanded).

## Column 15: category_target_spu_count
- Definition: Target number of SPUs for the category context of the source row.
- Type: numeric (float)
- Source/Logic: Taken from `row['target_sty_cnt_avg']` and cast to float.
  - Code: `target_spu_count = float(row['target_sty_cnt_avg'])` then `expanded_record['category_target_spu_count'] = target_spu_count`
- Dependencies: Requires `target_sty_cnt_avg` present in input config.
- Edge cases:
  - Zero or near-zero values are allowed; downstream percentage uses `max(target, 1)` to avoid division by zero.
- Validation suggestions:
  - Non-negative; check basic reasonableness (e.g., small positive values for categories with activity).

## Column 16: category_excess_spu_count
- Definition: The amount of SPU overage at category level.
- Type: numeric (float)
- Source/Logic: Difference between current and target SPU counts.
  - Code: `excess_spu_count = current_spu_count - target_spu_count`
- Dependencies: Columns 14 and 15.
- Edge cases:
  - In expanded output, this is strictly > 0 by construction (non-overcapacity records are skipped).
- Validation suggestions:
  - `category_excess_spu_count >= 0` and equals current − target.

## Column 17: category_overcapacity_percentage
- Definition: Percentage over target at category level.
- Type: numeric (float, percent)
- Source/Logic: Ratio of excess to target, multiplied by 100; denominator guarded.
  - Code: `overcapacity_percentage = (excess_spu_count / max(target_spu_count, 1)) * 100`
- Dependencies: Columns 15 and 16.
- Edge cases:
  - For `target_spu_count == 0`, denominator becomes 1 to avoid division by zero, producing a large but finite percentage.
- Validation suggestions:
  - Non-negative; recompute from 14–16 to confirm.

## Column 18: category_total_sales
- Definition: Sum of positive SPU sales (from JSON) within the category/source row used for share calculations.
- Type: numeric (float)
- Source/Logic: Sum over positive values in the parsed `sty_sal_amt` JSON dict.
  - Code: `total_category_sales = sum(float(v) for v in spu_data.values() if float(v) > 0)`
- Dependencies: Successful JSON parsing of `sty_sal_amt`.
- Edge cases:
  - Records with `total_category_sales < MIN_SALES_VOLUME` are skipped prior to expansion.
- Validation suggestions:
  - Positive; should be >= sum of `sty_sal_amt` assigned to SPUs kept for that row (since non-positive SPUs are filtered).

## Column 19: spu_code
- Definition: REAL SPU identifier from the JSON payload (e.g., "75T0001").
- Type: string
- Source/Logic: Key from parsed `sty_sal_amt` JSON dict while expanding.
  - Code: `for spu_code, spu_sales in spu_data.items(): ... expanded_record['spu_code'] = spu_code`
- Dependencies: Successful JSON parse.
- Edge cases:
  - None expected; non-null for all expanded records.
- Validation suggestions:
  - Non-null; string type; reasonable length/format.

## Column 20: spu_sales
- Definition: SPU-level sales amount (same numeric value assigned to `sty_sal_amt` at SPU level).
- Type: numeric (float)
- Source/Logic: Value from parsed JSON for the current `spu_code`.
  - Code: `spu_sales = float(spu_data[spu_code]); expanded_record['spu_sales'] = spu_sales`
- Dependencies: Column 19 and JSON parsing.
- Edge cases:
  - Only positive `spu_sales` are kept; non-positive skipped.
- Validation suggestions:
  - Non-negative; should sum (over kept SPUs) close to `category_total_sales` per group.

## Column 21: spu_sales_share
- Definition: Share of the category's total sales contributed by this SPU.
- Type: numeric (float in [0,1])
- Source/Logic: `spu_sales / category_total_sales` where total is sum of positive SPU sales.
  - Code: `spu_sales_share = spu_sales / total_category_sales`
- Dependencies: Columns 18 and 20.
- Edge cases:
  - Sums to ~1.0 across kept SPUs per category row (floating error allowed).
- Validation suggestions:
  - Group-wise sum by (`str_code`, category dims) ~ 1.0

## Column 22: overcapacity_percentage (legacy duplicate)
- Definition: Duplicate of `category_overcapacity_percentage` for backward-compatibility at SPU level.
- Type: numeric (float, percent)
- Source/Logic: Direct copy of Column 17.
  - Code: `expanded_record['overcapacity_percentage'] = overcapacity_percentage`
- Dependencies: Columns 15–17.
- Validation suggestions:
  - Equals Column 17 for all rows.

## Column 23: excess_spu_count (legacy duplicate)
- Definition: Duplicate of `category_excess_spu_count` for backward-compatibility at SPU level.
- Type: numeric (float)
- Source/Logic: Direct copy of Column 16.
  - Code: `expanded_record['excess_spu_count'] = excess_spu_count`
- Dependencies: Columns 14–16.
- Validation suggestions:
  - Equals Column 16 for all rows.

## Column 24: base_sal_qty
- Definition: Base sales quantity component for the SPU from the API quantity dataset.
- Type: numeric (float)
- Source/Logic: Passed through from quantity data merge on `['str_code','spu_code']`.
  - Used in `quantity_real` computation when paired with `fashion_sal_qty`.
- Dependencies: Present in quantity files (`QUANTITY_USECOLS`).
- Edge cases:
  - May be missing; then `quantity_real` falls back to `sal_qty` or `quantity`.
- Validation suggestions:
  - Non-negative. If both base and fashion exist, `quantity_real ≈ base_sal_qty + fashion_sal_qty`.

## Column 25: fashion_sal_qty
- Definition: Fashion sales quantity component for the SPU from the API quantity dataset.
- Type: numeric (float)
- Source/Logic: Passed through from quantity data merge on `['str_code','spu_code']`.
  - Used with `base_sal_qty` to compute `quantity_real`.
- Dependencies: Present in quantity files (`QUANTITY_USECOLS`).
- Edge cases:
  - May be missing; then `quantity_real` uses fallbacks.
- Validation suggestions:
  - Non-negative. `quantity_real` equals sum of base + fashion when both present.

## Column 26: sal_qty
- Definition: Total sales quantity from API when base/fashion split is not available.
- Type: numeric (float)
- Source/Logic: Passed through from quantity data; used as fallback for `quantity_real`.
  - Code path: if no `base_sal_qty` and `fashion_sal_qty`, use `sal_qty`.
- Dependencies: Present in some quantity files.
- Edge cases:
  - May be missing; then fall back to `quantity`.
- Validation suggestions:
  - Non-negative. If used, `quantity_real ≈ sal_qty`.

## Column 27: quantity
- Definition: Generic quantity field from API quantity dataset used as last fallback.
- Type: numeric (float)
- Source/Logic: Passed through from quantity data; used if neither base/fashion nor `sal_qty` exist.
- Dependencies: Present in some quantity files or blended quantity.
- Edge cases:
  - May be missing; then `quantity_real` may be NaN after merge.
- Validation suggestions:
  - Non-negative. If used, `quantity_real ≈ quantity`.

## Column 28: spu_sales_amt
- Definition: SPU-level sales amount from quantity dataset; preferred for price/ROI.
- Type: numeric (float)
- Source/Logic: Passed through from quantity data; preferred `amount` in unit price calc.
  - Code: `amount = expanded_df.get('spu_sales_amt', expanded_df.get('spu_sales'))`
- Dependencies: Quantity merge; fallback uses JSON `spu_sales` when missing.
- Edge cases:
  - If missing, `unit_price` uses `spu_sales` from JSON.
- Validation suggestions:
  - Non-negative. Reasonable range vs `spu_sales` after join.

## Column 29: quantity_real
- Definition: Real unit quantity used for pricing and reductions.
- Type: numeric (float)
- Source/Logic: Deterministic precedence from quantity data:
  - If both `base_sal_qty` and `fashion_sal_qty` present: `quantity_real = base_sal_qty + fashion_sal_qty`
  - Else if `sal_qty` present: `quantity_real = sal_qty`
  - Else if `quantity` present: `quantity_real = quantity`
- Dependencies: Columns 24–27.
- Edge cases:
  - May be NaN if no quantity fields were available/matched.
- Validation suggestions:
  - Non-negative. If `quantity_real <= 0`, `unit_price` becomes NA by design.

## Column 30: unit_price
- Definition: Estimated unit retail price for the SPU in the period.
- Type: numeric (float)
- Source/Logic: `unit_price = amount / quantity_real` with guards; masked when `quantity_real <= 0`.
  - `amount` prefers `spu_sales_amt`, falls back to `spu_sales` (from JSON).
- Dependencies: Columns 20 or 28 and 29.
- Edge cases:
  - If `quantity_real` is 0/NaN, `unit_price` is NA.
- Validation suggestions:
  - Positive and plausible (typical $20–$150). NA where `quantity_real` <= 0.

## Column 31: current_quantity
- Definition: Period-adjusted current unit quantity used for reductions.
- Type: numeric (float)
- Source/Logic: `current_quantity = quantity_real * SCALING_FACTOR`
  - With defaults `TARGET_PERIOD_DAYS = DATA_PERIOD_DAYS = 15`, `SCALING_FACTOR = 1.0`.
- Dependencies: Column 29 and configuration constants.
- Edge cases:
  - If `quantity_real` NaN, remains NaN.
- Validation suggestions:
  - Should equal `quantity_real` under default config; otherwise scaled.

## Column 32: potential_reduction
- Definition: Uncapped unit reduction proportional to category overcapacity.
- Type: numeric (float)
- Source/Logic: `potential_reduction = (category_excess_spu_count / category_current_spu_count) * current_quantity`
  - With division-by-zero guard (NaN when denom 0).
- Dependencies: Columns 14, 16, 31.
- Edge cases:
  - NaNs produced when counts invalid; later capped to 0 in constrained step.
- Validation suggestions:
  - `0 <= potential_reduction <= current_quantity` when inputs valid.

## Column 33: constrained_reduction
- Definition: Capped unit reduction respecting maximum reduction policy.
- Type: numeric (float)
- Source/Logic: `constrained_reduction = min(potential_reduction, current_quantity * MAX_REDUCTION_PERCENTAGE)`
  - `MAX_REDUCTION_PERCENTAGE = 0.4` (40%).
- Dependencies: Columns 31–32 and configuration constants.
- Edge cases:
  - NaNs in `potential_reduction` treated as 0 before min.
- Validation suggestions:
  - `0 <= constrained_reduction <= current_quantity * 0.4`.

## Column 34: recommend_reduction
- Definition: Flag indicating whether a reduction is recommended for this SPU.
- Type: boolean
- Source/Logic: `recommend_reduction = (constrained_reduction >= MIN_REDUCTION_QUANTITY)`
  - `MIN_REDUCTION_QUANTITY = 1.0`.
- Dependencies: Column 33 and configuration constants.
- Edge cases:
  - Exactly equal to threshold evaluates to True.
- Validation suggestions:
  - Consistent with sign and magnitude of `recommended_quantity_change`.

## Column 35: recommended_quantity_change
- Definition: Signed quantity change recommendation (negative values = reduce units).
- Type: numeric (float)
- Source/Logic: `recommended_quantity_change = -constrained_reduction.where(recommend_reduction, 0)`
- Dependencies: Columns 33–34.
- Edge cases:
  - 0 when `recommend_reduction` is False.
- Validation suggestions:
  - `recommended_quantity_change <= 0` and `abs(recommended_quantity_change) == constrained_reduction` when recommended.

## Column 36: margin_rate
- Definition: Margin rate used for cost and ROI calculations.
- Type: numeric (float in [0, 0.95])
- Source/Logic: Joined from `load_margin_rates(margin_type='spu')` by (`str_code`,`spu_code`) else by `str_code` average; missing filled with env default.
  - Default: `MARGIN_RATE_DEFAULT` from env, defaulting to 0.45; clipped to [0, 0.95].
- Dependencies: External margin rates data and environment variable.
- Edge cases:
  - If join fails, falls back to default; ensure column exists.
- Validation suggestions:
  - In-range and not null after fill.

## Column 37: retail_value
- Definition: Unit retail value proxy (equals unit price).
- Type: numeric (float)
- Source/Logic: `retail_value = unit_price` (via `up = expanded_df['unit_price'].fillna(0)`).
- Dependencies: Column 30.
- Edge cases:
  - 0 when `unit_price` is NA.
- Validation suggestions:
  - Equals `unit_price` where present.

## Column 38: investment_required
- Definition: Cost-based investment required for the reduction (negative value when spend required).
- Type: numeric (float)
- Source/Logic: `investment_required = -(constrained_reduction * unit_cost).where(recommend_reduction, 0)`
  - `unit_cost = unit_price * (1 - margin_rate)`.
- Dependencies: Columns 30, 33–36.
- Edge cases:
  - 0 when not recommended; negative when recommended.
- Validation suggestions:
  - `investment_required <= 0` when recommended; 0 otherwise.

## Column 39: estimated_cost_savings
- Definition: Estimated cost savings from the reduction.
- Type: numeric (float)
- Source/Logic: `estimated_cost_savings = (constrained_reduction * unit_cost).where(recommend_reduction, 0)`
- Dependencies: Columns 30, 33–36.
- Edge cases:
  - 0 when not recommended.
- Validation suggestions:
  - `estimated_cost_savings >= 0` and equals `-investment_required` when recommended.

## Column 40: margin_per_unit
- Definition: Profit contribution per unit.
- Type: numeric (float)
- Source/Logic: `margin_per_unit = unit_price - unit_cost`
- Dependencies: Columns 30 and 36.
- Edge cases:
  - 0 when unit_price is 0.
- Validation suggestions:
  - Non-negative if margin_rate in [0,1) and unit_price >= 0.

## Column 41: expected_margin_uplift
- Definition: Expected incremental profit from the reduction.
- Type: numeric (float)
- Source/Logic: `expected_margin_uplift = (constrained_reduction * margin_per_unit).where(recommend_reduction, 0)`
- Dependencies: Columns 33, 34, 40.
- Edge cases:
  - 0 when not recommended.
- Validation suggestions:
  - `expected_margin_uplift >= 0` and equals `constrained_reduction * margin_per_unit` when recommended.

## Column 42: roi_percentage
- Definition: ROI percentage for the recommended reduction.
- Type: numeric (float, percent)
- Source/Logic: `roi_percentage = (expected_margin_uplift / -investment_required) * 100` when `investment_required < 0`, else 0.
- Dependencies: Columns 38–41.
- Edge cases:
  - Avoid division by zero via conditional; 0 when no investment.
- Validation suggestions:
  - Non-negative where defined.

## Column 43: recommendation_text
- Definition: Human-readable recommendation summary per SPU.
- Type: string
- Source/Logic: If recommended: `"REDUCE {constrained_reduction:.1f} units/15-days for SPU {spu_code} (overcapacity: {category_overcapacity_percentage:.1f}%)"`; else: `"Monitor SPU {spu_code} (below reduction threshold)"`.
- Dependencies: Columns 17, 33–35, 19.
- Edge cases:
  - Robust to NA via try/except; may be absent if formatting fails.
- Validation suggestions:
  - Matches underlying numeric fields.

---

## Placeholders for subsequent detailed documentation
For each of the following columns, fill in the same structure: Definition, Type, Source/Logic, Dependencies, Edge cases, Validation suggestions.

3. Cluster — DONE
4. season_name — DONE
5. sex_name — DONE
6. display_location_name — DONE
7. big_class_name — DONE
8. sub_cate_name — DONE
9. yyyy — DONE
10. mm — DONE
11. mm_type — DONE
12. sal_amt — DONE
13. sty_sal_amt — DONE
14. category_current_spu_count — DONE
15. category_target_spu_count — DONE
16. category_excess_spu_count — DONE
17. category_overcapacity_percentage — DONE
18. category_total_sales — DONE
19. spu_code — DONE
20. spu_sales — DONE
21. spu_sales_share — DONE
22. overcapacity_percentage — DONE
23. excess_spu_count — DONE
24. base_sal_qty — DONE
25. fashion_sal_qty — DONE
26. sal_qty — DONE
27. quantity — DONE
28. spu_sales_amt — DONE
29. quantity_real — DONE
30. unit_price — DONE
31. current_quantity — DONE
32. potential_reduction — DONE
33. constrained_reduction — DONE
34. recommend_reduction — DONE
35. recommended_quantity_change — DONE
36. margin_rate — DONE
37. retail_value — DONE
38. investment_required — DONE
39. estimated_cost_savings — DONE
40. margin_per_unit — DONE
41. expected_margin_uplift — DONE
42. roi_percentage — DONE
43. recommendation_text — DONE
