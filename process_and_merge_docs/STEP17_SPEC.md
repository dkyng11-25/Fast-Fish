### Name

- Step 17: Augment Fast Fish with Historical Reference (period-aware) and optional real-data Trending

### Purpose

- Enrich Step 14 Fast Fish recommendations with historical baseline metrics (from Step 15) and, if explicitly enabled and available, cluster-level trend scores derived only from real, preserved granular data. Outputs are client-compliant and manifest-registered.

### Inputs

- Step 14 output (Fast Fish enhanced CSV): resolved via manifest preferred, or `--input-file`.
- Step 15 historical reference: preferred manifest key `historical_reference_<BASELINE_LABEL>`; fallback to generic when metadata matches requested baseline.
- Cluster mapping: `output/clustering_results_spu.csv` for store→cluster to derive `Store_Group_Name` when needed (no synthetic fallbacks).
- Optional preserved granular trend data from Step 13: `output/granular_trend_data_preserved_*.csv`.

### CLI

- `--target-yyyymm` (required), `--target-period` (required)
- `--input-file` (optional override for Step 14 output)
- Future toggles (documented, not necessarily implemented): `--fast-mode`, `--enable-trending`

### Processing

1) Resolve `target_label=<TARGET_YYYMM><TARGET_PERIOD>` and `baseline_label=<T-12><TARGET_PERIOD>`.
2) Load Step 14 Fast Fish and Step 15 historical reference (manifest-first). Normalize category/subcategory naming where needed.
3) Historical augmentation (real data only):
   - Build lookup by Store Group × Subcategory from Step 15; join to Fast Fish.
   - Add columns: `Historical_SPU_Quantity`, `SPU_Change_vs_Historical`, `SPU_Change_vs_Historical_Pct`, `Historical_Store_Count`, `Historical_Total_Sales`.
   - Keep NA when no match; percent changes are NA-safe.
4) Optional trending (default off):
   - Use preserved granular trend cache + cluster mapping; aggregate to store-group × subcategory.
   - Add trend columns only when computed from real inputs; otherwise keep NA. No synthetic defaults.
5) Apply client format fixes (e.g., Month zero-padding, Target_Style_Tags normalization where appropriate).
6) Save to `output/fast_fish_with_historical_and_cluster_trending_analysis_<TARGET_LABEL>_<TS>.csv` and register in manifest under generic and period-specific keys.

### Outputs

- CSV: augmented recommendations with historical columns, and trend columns when enabled and real data is present.
- Manifest: `step17/augmented_recommendations` and `step17/augmented_recommendations_<TARGET_LABEL>` with metadata (records, columns, includes_historical, includes_trending, client_compliant).

### Failure modes

- Missing Step 15 historical file for the requested baseline: skip historical augmentation with a warning or fail fast per run policy.
- Missing cluster mapping or granular trends: trend columns remain NA; logged as informational, not synthesized.
- Mismatched period files: detect via manifest metadata; ignore entries that do not match the requested baseline.

### Invocation example

```bash
python -m src.step17_augment_recommendations \
  --target-yyyymm 202509 \
  --target-period A \
  --input-file output/enhanced_fast_fish_format_202509A_20250820_101500.csv
```

