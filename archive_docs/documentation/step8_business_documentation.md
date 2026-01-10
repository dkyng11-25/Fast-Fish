# Step 8: Imbalanced Allocation Rule with Quantity Rebalancing

## Purpose
Identify stores with imbalanced style allocations using Z-Score analysis and provide specific unit quantity rebalancing recommendations. This step includes actual unit quantity rebalancing using real sales data for investment-neutral rebalancing (no additional cost).

## Inputs
- Clustering results file (clustering_results_subcategory.csv)
- Planning data files (store_config_2025Q2_combined.csv)
- Quantity data from API (complete_spu_sales_2025Q2_combined.csv)
- Historical data for validation

## Transformations
1. **Data Loading**: Load clustering results, planning data, and quantity data for rebalancing analysis
2. **Seasonal Data Loading**: Load and blend recent trends with seasonal patterns using weighted aggregation
3. **Allocation Data Preparation**: Prepare store allocation data with cluster information and quantity data
4. **Z-Score Calculation**: Calculate Z-Scores for each store's allocation within their cluster
5. **Imbalanced Case Identification**: Identify imbalanced cases with quantity rebalancing recommendations
6. **Rule Application**: Apply the imbalanced rule to all stores and create rule results
7. **Results Saving**: Save rule results and detailed analysis

## Outputs
- Imbalanced rule results CSV (imbalanced_rule_results.csv)
- Detailed imbalanced cases CSV (imbalanced_detailed_cases.csv)
- Complete Z-Score analysis CSV (imbalanced_zscore_analysis.csv)
- Unit quantity rebalancing recommendations
- Investment-neutral rebalancing suggestions
- Cluster-aware imbalance detection results

## Dependencies
- Successful completion of step 7 (Missing Category Rule)
- Availability of clustering results files
- Planning data files
- Quantity data from API
- Historical data for validation

## Success Metrics
- Clustering results and planning data loaded successfully
- Seasonal data blended for August recommendations
- Real quantity data loaded for rebalancing calculations
- Allocation data prepared with cluster information
- Z-Scores calculated for all stores
- Imbalanced cases identified with quantity recommendations
- Rule results created for all stores
- Results saved with proper formatting

## Error Handling
- Missing clustering results files
- Planning data loading failures
- Quantity data loading errors
- Allocation data preparation errors
- Z-Score calculation errors
- Imbalanced case identification failures
- Rule application errors
- File saving errors

## Performance
- Efficient loading of clustering and planning data
- Optimized seasonal data blending
- Memory-efficient allocation data processing
- Fast Z-Score calculation algorithms

## Business Value
- Identifies imbalanced style allocations with specific unit quantity rebalancing
- Provides actionable rebalancing recommendations using real sales data
- Enables investment-neutral rebalancing (no additional cost)
- Supports data-driven inventory optimization
- Improves allocation efficiency across clusters

## Future Improvements
- Enhanced Z-Score analysis methods
- Additional rebalancing algorithms
- Real-time imbalance detection
- Integration with external market data
- Advanced statistical modeling methods
