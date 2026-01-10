# Step 7: Missing Category/SPU Rule with Quantity Recommendations

## Purpose
Identify stores that are missing subcategories or SPUs that are well-selling in their peer stores within the same cluster and provide specific unit quantity targets. This step includes actual unit quantity recommendations using real sales data and Fast Fish sell-through validation to ensure only profitable recommendations are made.

## Inputs
- Clustering results (resolved via `src.config` with fallbacks):
  - `output/clustering_results_spu.csv` or `output/clustering_results_subcategory.csv`
- Sales (period-resolved via `src.config`):
  - SPU: `data/api_data/complete_spu_sales_{YYYYMMP}.csv`
  - Subcategory: `data/api_data/complete_category_sales_{YYYYMMP}.csv`
- Quantities and prices (API actuals per store):
  - `data/api_data/store_sales_{YYYYMMP}.csv` (derives `avg_unit_price`)
- Optional seasonal dataset (if blending enabled): `*_sales_{SEASONAL_YYYYMMP}.csv`
- Historical data for sell-through validation (if available)

## Transformations
1. **Period & Path Resolution**: Use `src.config` to resolve inputs/outputs per `--yyyymm` and `--period`.
2. **Seasonal Blending (optional)**: Blend current period with seasonal period using CLI weights.
3. **Quantity & Price Derivation**: Compute `avg_unit_price` from API amounts/quantities per store.
4. **Well-Selling Identification**: Find cluster well-selling SPUs/subcategories.
5. **Missing Opportunity Analysis**: Detect missing items per store; estimate quantities and investment.
6. **Fast Fish Validation**: Approve only opportunities predicted to improve sell-through.
7. **Results Saving**: Save period-labeled results, opportunities, and summary.

## Outputs
- Results: `output/rule7_missing_{analysis}_sellthrough_results_{YYYYMMP}.csv`
- Opportunities: `output/rule7_missing_{analysis}_sellthrough_opportunities_{YYYYMMP}.csv`
- Summary: `output/rule7_missing_{analysis}_sellthrough_summary_{YYYYMMP}.md`
- Unit quantity recommendations with investment planning
- Fast Fish compliant recommendations that improve sell-through rate
- Deprecated (compatibility, subcategory only): `output/rule7_missing_category_results.csv`

## Dependencies
- Successful completion of step 6 (cluster assignments)
- `src.config` for period/path resolution
- `src.sell_through_validator` for sell-through checks
- Sales and store-level API data for the selected period
- Optional historical data for validator baselines

## Success Metrics
- Inputs resolved per period; clustering and sales data loaded
- Optional seasonal blending executed if enabled via CLI
- Real quantity and unit price derived per store
- Well-selling features identified per cluster
- Missing opportunities with quantity recommendations identified
- Fast Fish sell-through validation completed
- Results/opportunities/summary saved with period label

## CLI Usage

Forecast September outputs using August actuals (SPU-level):

```bash
# September A output labeled from August A inputs
python3 -m src.step7_missing_category_rule \
  --yyyymm 202508 --period A --analysis-level spu \
  --target-yyyymm 202509 --target-period A

# September B output labeled from August B inputs
python3 -m src.step7_missing_category_rule \
  --yyyymm 202508 --period B --analysis-level spu \
  --target-yyyymm 202509 --target-period B
```

Optional seasonal blending (e.g., blend with last year September):

```bash
python3 -m src.step7_missing_category_rule \
  --yyyymm 202508 --period B --analysis-level spu \
  --target-yyyymm 202509 --target-period B \
  --seasonal-blending --seasonal-yyyymm 202409 --seasonal-period B --seasonal-weight 0.6
```

## Integration Run Summary (202508A/B, SPU)

- Stores analyzed: 2,268
- Stores flagged: 899
- Opportunities: 1,674
- Total quantity: 15,666 units / 15 days
- Total investment: ~$1,045,803
- Fast Fish validator executed; no historical baseline found in this run (improvement shows +100pp for approved adds)

## Error Handling
- Missing clustering results files
- Sales data loading failures
- Quantity data loading errors
- Price data loading errors
- Feature identification errors
- Opportunity analysis failures
- Rule application errors
- File saving errors

## Performance
- Efficient loading of clustering and sales data
- Optimized seasonal data blending
- Memory-efficient quantity data processing
- Fast feature identification algorithms

## Business Value
- Identifies missing subcategories/SPUs with specific unit quantity targets
- Provides actionable recommendations using real sales data
- Ensures recommendations improve sell-through rate (Fast Fish compliance)
- Enables investment planning with realistic unit prices
- Supports data-driven inventory decisions

## Future Improvements
- Enhanced seasonal pattern recognition
- Additional validation metrics
- Real-time opportunity identification
- Integration with external market data
- Advanced statistical analysis methods
