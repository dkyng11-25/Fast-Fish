# Step 10 Runtime Optimizations (Lossless)

This document summarizes the safe, lossless runtime optimizations implemented in `src/step10_spu_assortment_optimization.py` to reduce Step 10 runtime while preserving correctness, real data usage, and validator semantics.

## What Changed

- __Deduplicated Fast Fish validator calls__
  - Validate once per unique key: `('str_code', 'sub_cate_name', current_spu_count, recommended_spu_count)` and broadcast results back to all matching rows.
  - Preserves exact semantics:
    - Missing fields: rows are retained with `fast_fish_compliant = NA` and `validation_reason` set.
    - Non-compliant rows: dropped from the final set (unchanged behavior from prior logic).
    - Per-store capping still applied post-validation.
  - Implementation: vectorized preparation + single pass over unique keys using dict records (preserves column names starting with `_`).

- __Selective CSV column loading (IO optimization)__
  - Introduced `CONFIG_USECOLS` and `QUANTITY_USECOLS` to restrict IO to required columns.
  - `_read_csvs(..., usecols=...)` attempts a constrained read and __falls back automatically__ to full reads if column mismatches occur. This guarantees robustness and zero functional risk.
  - Wired into blended/standard data loaders.

- __Minor iteration and numeric improvements__
  - Vectorized integerize + clamp for SPU counts (0–100) prior to validation keying.
  - Reduced per-row Python overhead in validation by broadcasting results via a merge.

## Why This Is Safe (Correctness Preserved)

- __No synthetic data__: Still uses real SPU codes, real unit quantities, and real sales amounts.
- __Validator semantics unchanged__: Same inputs, same clamping (0–100), same `recommended_spu_count = current - 1` rule, same rejection/approval logic.
- __Invalid rows preserved__: Rows missing critical fields retain `NA` validation fields as before.
- __Per-store cap unchanged__: Still applied after validation with the same cap.
- __IO fallback__: If a constrained read fails due to schema drift, we log a warning and automatically read the full file.

## Files/Areas Updated

- `src/step10_spu_assortment_optimization.py`
  - Added `CONFIG_USECOLS`, `QUANTITY_USECOLS` constants.
  - `_read_csvs()` now supports `usecols` with safe fallback.
  - `load_blended_data()` uses `usecols` for recent config/quantity files.
  - Replaced per-row validator loop with deduplicated per-key validation and broadcast.

## Verification Steps

- __Quick smoke run (small)__: validate end-to-end behavior with debug limit.
  - Expect: Similar opportunity counts and summary as before (minor ordering differences only), manifest entries updated, summary markdown written, and significant runtime reduction.
  - Watch logs for:
    - "Applying Fast Fish sell-through validation..."
    - "Fast Fish sell-through validation complete" with Approved/Rejected counts
    - Per-store cap application summary
    - IO logs possibly indicating fallback if constrained columns mismatch

### How to run (module mode)

Run as a module to ensure `from src...` imports resolve:

```bash
python3 -u -m src.step10_spu_assortment_optimization \
  --yyyymm 202508 --period B \
  --target-yyyymm 202509 --target-period A \
  --debug-limit 200 --max-adj-per-store 30
```

Troubleshooting: If you see `ModuleNotFoundError: No module named 'src'`, re-run using the module form above.

- __Compare outputs__ (optional):
  - Compare `output/rule10_smart_overcapacity_results_*.csv` and opportunities CSVs against a prior reference run for the same period.
  - Expected differences:
    - Row order may differ slightly due to grouping/merge; content and counts should be consistent.

## Performance Expectations

- __Validation speed__: Expected large reduction in runtime when many rows share the same (store, subcategory, counts) combination (often 5–50x fewer validator calls).
- __IO efficiency__: Lower memory and faster reads by selecting only necessary columns, with safe fallback when needed.

## Flags/Controls (unchanged)

- `--debug-limit`: limits number of SPU source records expanded (for smoke tests).
- `--skip-sellthrough`: skips validation entirely (useful for functional smoke tests only).
- `--max-adj-per-store`: per-store capping after validation (logic unchanged).

## Notes

- Seasonal blending behavior and manifest registration are unchanged.
- All changes prioritize safety: deterministic outputs, NA-safe merges, and resilience to schema drift via `usecols` fallback.
- Implementation note: validation key iteration uses dict records rather than `itertuples()` to avoid attribute mangling for columns starting with `_`.
- Expected logs: `usecols`-constrained reads may warn and fall back to full reads when schemas differ; this is intentional and safe.
