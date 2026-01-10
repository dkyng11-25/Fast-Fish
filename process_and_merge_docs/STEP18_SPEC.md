### Name

- Step 18: Sell-Through Rate Enhancement (period-aware, real-data only)

### Purpose

- Compute sell-through KPIs for Step 17 augmented recommendations using real historical data from Step 15 and period-aware inputs; preserve NA when history is missing; emit fraction and percent forms; register outputs in manifest.

### Inputs

- Step 17 augmented CSV: preferred via manifest `step17/augmented_recommendations_<TARGET_LABEL>`; no globbing. CLI `--input-file` override allowed.
- Step 15 historical reference CSV: manifest `step15/historical_reference_<BASELINE_LABEL>` preferred; generic entry only if its metadata baseline matches.

### CLI

- `--target-yyyymm` (required), `--target-period` (required)
- `--input-file` (optional override)

### Processing

1) Resolve `target_label` and `baseline_label` (T-12, same A/B). Load Step 17 augmented and Step 15 historical via manifest.
2) Build historical summary keyed by `Store_Group_Name × Category × Subcategory` with NA-safe daily averages per store.
3) For each recommendation, compute:
   - `SPU_Store_Days_Inventory` = `Target_SPU_Quantity × Stores_In_Group_Selling_This_Category × 15`
   - `SPU_Store_Days_Sales` = `Avg_Daily_SPUs_Sold_Per_Store × Stores_In_Group_Selling_This_Category × 15` (from history)
   - `Sell_Through_Rate_Frac` = clip01(`Sales`/`Inventory`); `Sell_Through_Rate_Pct` = fraction × 100; legacy `Sell_Through_Rate` mirrors percent
4) Add optimization-visibility fields (capacity utilization, suitability, confidence, rationale) with safe NA-preserving fallbacks.
5) Save to `output/fast_fish_with_sell_through_analysis_<TARGET_LABEL>_<TS>.csv`; register outputs under generic and period-specific manifest keys with metadata (records, columns, flags).

### Outputs

- CSV with sell-through metrics and visibility fields
- Manifest entries: `step18/sell_through_analysis` and `step18/sell_through_analysis_<TARGET_LABEL>`

### Failure modes

- Missing Step 17 period-specific file: fail fast; require correct manifest state or CLI override.
- Missing Step 15 baseline file: fail fast; enforce baseline alignment.
- Missing historical match for a row: keep sell-through NA (no estimation).

### Invocation example

```bash
python -m src.step18_validate_results \
  --target-yyyymm 202509 \
  --target-period A
```

