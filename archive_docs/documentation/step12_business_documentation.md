# Step 12: Sales Performance Gap Rule with Quantity Increase Recommendations

## Identification
**File:** `src/step12_sales_performance_rule.py`
**Type:** Business Rule Implementation
**Execution Order:** Step 12 in the 20-step pipeline

## Purpose / Business Value

### Core Objective
Identifies sales opportunities by comparing each store's category performance against cluster top performers and provides specific UNIT QUANTITY INCREASE recommendations to close performance gaps.

### Business Impact
- **Performance Optimization:** Closes sales performance gaps through targeted inventory increases
- **Peer Benchmarking:** Aligns store performance with cluster top quartile benchmarks
- **Z-Score Analysis:** Uses statistical methods to identify significant performance gaps
- **Actionable Insights:** Provides specific quantity recommendations for sales teams

### Key Enhancements
1. **Real Quantity Data:** Uses actual unit quantities from API fields (`base_sal_qty`, `fashion_sal_qty`) instead of treating sales amounts as quantities
2. **Unit Price Realism:** Calculates realistic unit prices ($20-$150 range) from API data for accurate investment calculations
3. **Fast Fish Validation:** Integrates sell-through validation to ensure recommendations improve sell-through rates
4. **Seasonal Blending:** For August, combines recent trends (May-July) with seasonal patterns (Aug 2024) for balanced recommendations
5. **Multi-Level Analysis:** Supports both subcategory and SPU-level analysis

## Inputs

### Primary Data Sources
1. **Store Configuration Data:** `data/api_data/store_config_2025Q2_combined.csv`
   - Store codes, cluster assignments, category sales data
   - SPU sales data in JSON format (`sty_sal_amt` field)

2. **Clustering Results:** `output/clustering_results_spu.csv`
   - Store-to-cluster assignments for peer group analysis

3. **Seasonal Data (August Enhancement):**
   - Recent trends: `data/api_data/store_config_2025Q2_combined.csv` (May-July 2025)
   - Seasonal patterns: `data/api_data/store_config_2024Q3_combined.csv` (August 2024)

### Configuration Parameters
- `ANALYSIS_LEVEL = "spu"` - SPU-level analysis (alternative: subcategory)
- `DATA_PERIOD_DAYS = 15` - Analysis period (15 days)
- `TARGET_PERIOD_DAYS = 15` - Recommendation period (15 days)
- `SCALING_FACTOR = 1.0` - Quantity scaling factor
- `MIN_SALES_VOLUME = 50` - Minimum sales volume for SPU inclusion
- `MIN_CLUSTER_SIZE = 5` - Minimum stores per cluster
- `MAX_INCREASE_PERCENTAGE = 0.5` - Maximum 50% quantity increase limit

## Transformation Overview

### 1. Data Loading & Preparation
1. Load store configuration data with SPU sales information
2. Load clustering results for peer group analysis
3. For August: Blend recent trends with seasonal patterns (40% recent + 60% seasonal)
4. Extract real SPU codes and sales data from JSON fields
5. Calculate realistic unit prices from sales data

### 2. Performance Gap Analysis
1. Calculate category performance metrics for each store:
   - Total sales, average sales per SPU
   - SPU count, category diversity
2. Calculate cluster-level performance benchmarks:
   - Top quartile (75th percentile) performance
   - Average and standard deviation metrics
3. Compute Z-scores for each store-category combination:
   - Z = (Store Performance - Cluster Average) / Cluster Standard Deviation
4. Classify performance levels based on Z-scores:
   - Top Performer: Z < -0.8 (exceeding top quartile)
   - Performing Well: -0.8 ≤ Z ≤ 0 (meeting expectations)
   - Some Opportunity: 0 < Z ≤ 0.8 (minor improvement potential)
   - Good Opportunity: 0.8 < Z ≤ 2.0 (solid growth potential)
   - Major Opportunity: Z > 2.0 (significant underperformance)

### 3. Quantity Recommendation Calculation
1. For stores with performance gaps (Z > 0):
   - Calculate target performance levels based on cluster top quartile
   - Determine quantity increases needed to close gaps
   - Scale recommendations to 15-day period matching API data
2. Apply business constraints:
   - Maximum 50% quantity increase limit
   - Minimum sales volume thresholds
   - Cluster size requirements
3. Calculate investment requirements using real unit prices

### 4. Fast Fish Validation
1. Initialize sell-through validator with historical data
2. For each performance gap case:
   - Calculate current and target SPU counts
   - Validate recommendation improves sell-through rate
   - Only retain Fast Fish compliant recommendations
   - Add sell-through metrics to results

### 5. Output Standardization
1. Create store-level summary with aggregated metrics
2. Add standardized pipeline columns for compatibility
3. Generate detailed opportunity descriptions
4. Apply business rationale and approval reasoning

## Outputs / Consumers

### Primary Output Files
1. **Detailed Results:** `output/rule12_sales_performance_spu_results.csv`
   - Store-level recommendations with quantity increases
   - Sell-through validation metrics
   - Investment calculations and business rationale

2. **Summary Report:** `output/rule12_sales_performance_spu_summary.md`
   - Key metrics and business impact analysis
   - Performance classification breakdown
   - Technical configuration and business recommendations

### Output Schema
**Standardized Columns:**
- `str_code` - Store code
- `cluster_id` - Cluster assignment
- `performance_gap_score` - Z-score indicating performance gap
- `total_quantity_change` - Recommended quantity increases
- `investment_required` - Investment needed for recommendations
- `rule12_sales_performance_gap` - Binary flag for pipeline integration
- `business_rationale` - Business justification for recommendations
- `approval_reason` - Approval criteria met
- `fast_fish_compliant` - Sell-through validation status
- `sell_through_improvement` - Expected sell-through rate improvement
- `performance_classification` - Categorical performance level

### Pipeline Integration
- **Consumers:** Steps 13-20 (consolidation, visualization, reporting)
- **Dependencies:** Steps 1-11 (data preparation, clustering, previous rules)
- **Format:** Enhanced Fast Fish CSV format for downstream compatibility

## Success Metrics

### Quantitative Metrics
- **Stores Analyzed:** 47 stores processed (limited data in current run)
- **Performance Classifications:** Not available in current run
- **Quantity Recommendations:** Not available in current run
- **Fast Fish Compliance:** Dependent on validator availability
- **Investment Requirements:** Not calculated in current run

### Business Value Indicators
- **Constraint Satisfaction:** All recommendations within maximum increase limits
- **Validation Rate:** Dependent on Fast Fish validator availability
- **Data Quality:** Real API data usage with realistic unit pricing
- **Seasonal Relevance:** August blending for strategic planning

## Dependencies / Risks

### Critical Dependencies
1. **Clustering Results:** Requires `clustering_results_spu.csv` from step 6
2. **API Data:** Depends on `store_config_2025Q2_combined.csv` with SPU sales
3. **Sell-Through Validator:** Optional dependency for validation (`src/sell_through_validator.py`)
4. **Seasonal Data:** For August, requires 2024Q3 data for blending

### Risk Factors
1. **Data Availability:** Missing or incomplete SPU sales data reduces detection accuracy
2. **Threshold Sensitivity:** Performance thresholds may need tuning based on business requirements
3. **Seasonal Data:** August blending depends on availability of 2024 seasonal data
4. **Validation Dependency:** Sell-through validation may be disabled if validator not available

### Mitigation Strategies
- Graceful degradation when seasonal data unavailable
- Fallback to recent data when validator not present
- Comprehensive logging for troubleshooting
- Memory management for large dataset processing

## Future Improvements

### Enhancement Opportunities
1. **Dynamic Thresholds:** Adaptive performance thresholds based on category characteristics
2. **Predictive Modeling:** Machine learning to predict future performance gaps
3. **Multi-Period Analysis:** Consider longer-term trends for performance benchmarking
4. **Store Attributes:** Incorporate store type/capacity constraints from steps 22-23

### Technical Improvements
1. **Performance Optimization:** Further vectorization of calculations
2. **Memory Efficiency:** Enhanced garbage collection for large datasets
3. **Error Handling:** More robust fallback mechanisms
4. **Validation Expansion:** Additional business rule validations

### Business Value Expansion
1. **Cross-Category Analysis:** Identify performance gaps across related categories
2. **Trend Analysis:** Track performance gap patterns over time for strategic insights
3. **Store Segmentation:** Different performance thresholds for different store types
4. **Seasonal Adaptation:** Dynamic seasonal blending weights based on business calendar
