# Step 7: Missing Category Rule

## Overview
This step implements the Missing Category Rule analysis, identifying stores that are missing key product categories in their assortment.

## Functionality

### Key capabilities
- Cluster-aware detection of missing subcategories or SPUs that are well-selling in peer stores.
- Unit quantity recommendations for the 15-day target window.
- Fast Fish sell-through validation gate (approve only if predicted sell-through improves).
- Optional seasonal blending with a historical period.

## Inputs
- Clustering results:
  - `output/clustering_results_spu.csv` or `output/clustering_results_subcategory.csv`
- Sales (period-resolved via `src.config`):
  - SPU: `data/api_data/complete_spu_sales_{YYYYMMP}.csv`
  - Subcategory: `data/api_data/complete_category_sales_{YYYYMMP}.csv`
- Quantities and prices (from API actuals):
  - `data/api_data/store_sales_{YYYYMMP}.csv` (derives `avg_unit_price` per store)
- Optional seasonal set (if blending is enabled):
  - `*_sales_{SEASONAL_YYYYMMP}.csv`

## Output Files
- Results: `output/rule7_missing_{analysis}_sellthrough_results_{YYYYMMP}.csv`
- Opportunities: `output/rule7_missing_{analysis}_sellthrough_opportunities_{YYYYMMP}.csv`
- Summary: `output/rule7_missing_{analysis}_sellthrough_summary_{YYYYMMP}.md`
- Deprecated (compatibility): `output/rule7_missing_category_results.csv` (may be written if legacy consumers exist)

## Configuration
- Thresholds (defaults in `src/step7_missing_category_rule.py`):
  - Subcategory: adoption ≥ 70%, cluster sales ≥ 100
  - SPU: adoption ≥ 80%, cluster sales ≥ 1500, max missing SPUs per store = 5
- Period handling: resolved dynamically via `src.config` (`get_current_period`, `get_period_label`)
- Target window: 15 days (aligned to bi-weekly periods)
- Seasonal blending (optional): seasonal yyyymm/period and weight

## Dependencies
- `pandas`, `numpy`
- `src.config`
- `src.sell_through_validator`

## Usage
Run via module with period and analysis level:

```bash
python3 -m src.step7_missing_category_rule --yyyymm 202508 --period A --analysis-level spu
python3 -m src.step7_missing_category_rule --yyyymm 202508 --period B --analysis-level spu
```

Optional seasonal blending:

```bash
python3 -m src.step7_missing_category_rule \
  --yyyymm 202508 --period B --analysis-level spu \
  --seasonal-blending --seasonal-yyyymm 202408 --seasonal-period B --seasonal-weight 0.6
```

## Troubleshooting
1. Analysis Problems
   - Check category data
   - Verify thresholds
   - Review recommendations

2. Data Quality
   - Validate categories
   - Check importance scores
   - Review missing items