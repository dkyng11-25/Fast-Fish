### Name

- Step 16: Spreadsheet Comparison Analysis (period-aware)

### Purpose

- Produce an Excel workbook comparing a historical baseline vs current period at multiple levels (summary, category, store group), using Step 15 outputs; optionally include Top SPUs and Category Growth from raw SPU CSVs, and a Fashion/Basic segmentation view. Register the workbook in the manifest.

### Inputs

- Step 15 outputs (preferred via manifest):
  - YOY comparison CSV: `step15/yoy_comparison_<BASELINE_LABEL>` preferred, else `step15/yoy_comparison`
  - Historical reference CSV: `step15/historical_reference_<BASELINE_LABEL>` preferred, else `step15/historical_reference`
- Optional raw SPU CSVs:
  - Baseline: `data/api_data/complete_spu_sales_<BASELINE_LABEL>.csv`
  - Current: `data/api_data/complete_spu_sales_<TARGET_YYYMM><TARGET_PERIOD>.csv`

### CLI

- `--target-yyyymm` (required), `--target-period` (required)
- `--baseline-yyyymm` (optional), `--baseline-period` (optional)
- `--yoy-file` (optional override), `--historical-file` (optional override)
- `--historical-raw-file` (optional), `--current-raw-file` (optional)
- `--fashion-keywords` (optional), `--basic-keywords` (optional), `--hybrid-threshold` (default 0.15)

### Processing

1) Resolve labels: `target_label=<TARGET_YYYMM><TARGET_PERIOD>`, `baseline_label=<BASELINE_YYYMM><BASELINE_PERIOD>` (baseline defaults to T-12, same A/B).
2) Load YOY and historical reference using manifest period-specific keys first; fall back to generic; finally by filename pattern.
3) Create three core DataFrames using YOY/historical reference:
   - Summary (period-aware overall aggregates and a change row)
   - Category comparison (SPU count/sales change and pct change)
   - Store group comparison (SPU count/sales change and pct change) with Unknown group preserved
4) Optional sheets:
   - Top performers and Category growth from raw SPU CSVs if available (50 rows each)
   - Fashion vs Basic segmentation sheets driven by keyword lists and a hybrid threshold around 50%
5) Save Excel workbook to `output/spreadsheet_comparison_analysis_<TARGET_LABEL>_<TS>.xlsx`, polish sheets (headers, widths, filters, conditional formatting).
6) Register in manifest (generic `comparison_workbook` and period-labeled `comparison_workbook_<TARGET_LABEL>`), including row-count metadata.

### Outputs

- XLSX: `output/spreadsheet_comparison_analysis_<TARGET_LABEL>_<TS>.xlsx`
- Manifest metadata (example): rows per sheet, target year/month/period, baseline label.

### Failure modes

- Missing Step 15 files for requested baseline: fail fast with guidance (`--yoy-file`, `--historical-file` overrides).
- Raw SPU files missing: skip optional Top SPUs sheets; add Info sheet with the looked-for paths.
- Manifest baseline mismatch: ignore manifest entries that don’t match requested baseline.

### Invocation examples

```bash
python -m src.step16_create_comparison_tables \
  --target-yyyymm 202509 \
  --target-period A

python -m src.step16_create_comparison_tables \
  --target-yyyymm 202509 \
  --target-period B \
  --baseline-yyyymm 202408 \
  --baseline-period A \
  --historical-raw-file data/api_data/complete_spu_sales_202408A.csv \
  --current-raw-file data/api_data/complete_spu_sales_202509B.csv \
  --fashion-keywords "时尚,衬衫,牛仔" \
  --basic-keywords "基础,基本款" \
  --hybrid-threshold 0.20
```

