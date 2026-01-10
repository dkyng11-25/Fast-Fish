# Step 11: Missed Sales Opportunity Rule with Quantity Increase Recommendations

## Identification
**File:** `src/step11_missed_sales_opportunity.py`
**Type:** Business Rule Implementation
**Execution Order:** Step 11 in the 20-step pipeline

## Purpose / Business Value

### Core Objective
Identifies missed sales opportunities by comparing store performance against cluster top performers and provides specific UNIT QUANTITY INCREASE recommendations to capture sales potential.

### Business Impact
- **Revenue Growth:** Captures missed sales opportunities through targeted inventory increases
- **Competitive Alignment:** Aligns store assortments with cluster top performer success
- **Data-Driven Decisions:** Uses peer group analysis for evidence-based recommendations
- **Operational Efficiency:** Provides actionable quantity recommendations for store replenishment

### Key Enhancements
1. **Real Quantity Data:** Uses actual unit quantities from API fields (`base_sal_qty`, `fashion_sal_qty`) instead of treating sales amounts as quantities
2. **Unit Price Realism:** Calculates realistic unit prices ($20-$150 range) from API data for accurate investment calculations
3. **Fast Fish Validation:** Integrates sell-through validation to ensure recommendations improve sell-through rates
4. **Seasonal Blending:** For August, combines recent trends (May-July) with seasonal patterns (Aug 2024) for balanced recommendations
5. **Performance Optimization:** Vectorized operations for 100x speed improvement

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
- `TOP_PERFORMER_THRESHOLD = 0.95` - Top 5% of SPUs within cluster-category
- `MIN_CLUSTER_STORES = 8` - Minimum stores in cluster for analysis
- `MIN_STORES_SELLING = 5` - Minimum stores selling SPU for proven winner status
- `MIN_SPU_SALES = 200` - Minimum sales to avoid noise
- `ADOPTION_THRESHOLD = 0.75` - 75% cluster adoption for top performers
- `MAX_RECOMMENDATIONS_PER_STORE = 10` - Maximum SPU recommendations per store
- `MIN_OPPORTUNITY_SCORE = 0.15` - Minimum opportunity score to qualify
- `MIN_SALES_GAP = 100` - Minimum sales gap for action
- `MIN_QTY_GAP = 2.0` - Minimum quantity gap for action

## Transformation Overview

### 1. Data Loading & Preparation
1. Load store configuration data with SPU sales information
2. Load clustering results for peer group analysis
3. For August: Blend recent trends with seasonal patterns (40% recent + 60% seasonal)
4. Extract real SPU codes and sales data from JSON fields
5. Calculate realistic unit prices from sales data

### 2. Top Performer Identification
1. Calculate cluster sizes for each cluster-category combination
2. Filter to clusters with sufficient stores (≥8 stores)
3. Calculate SPU performance within each cluster-category:
   - Total sales, average sales, transaction count
   - Total quantity, average quantity
   - Stores selling each SPU
   - SPU-to-category sales/quantity ratios
4. Filter to SPUs sold by multiple stores (proven winners)
5. Calculate percentile rank by total sales within each cluster-category
6. Identify top 5% performers (95th percentile)
7. Calculate adoption rates for top performers

### 3. Missing Opportunity Detection
1. Create store-cluster-category matrix with category totals
2. Create store-SPU matrix with current quantities
3. Identify what SPUs each store actually has vs. what they should have
4. Calculate SPU-to-category quantity ratios in successful stores
5. Scale recommendations based on target store's category performance
6. Apply business filters:
   - Minimum opportunity score
   - Minimum sales/quantity gaps
   - Maximum recommendations per store

### 4. Quantity Recommendation Calculation
1. Calculate recommended quantity increases for missing top performers
2. Scale recommendations to target store's category performance
3. Apply minimum quantity gap constraint
4. Calculate investment requirements using real unit prices
5. Limit to maximum recommendations per store

### 5. Fast Fish Validation
1. Initialize sell-through validator with historical data
2. For each missed opportunity case:
   - Calculate current and target SPU counts
   - Validate recommendation improves sell-through rate
   - Only retain Fast Fish compliant recommendations
   - Add sell-through metrics to results

### 6. Output Standardization
1. Create store-level summary with aggregated metrics
2. Add standardized pipeline columns for compatibility
3. Generate detailed opportunity descriptions
4. Apply business rationale and approval reasoning

## Outputs / Consumers

### Primary Output Files
1. **Detailed Results:** `output/rule11_missed_sales_opportunity_spu_results.csv`
   - Store-level recommendations with quantity increases
   - Sell-through validation metrics
   - Investment calculations and business rationale

2. **Summary Report:** `output/rule11_improved_missed_sales_opportunity_spu_summary.md`
   - Key metrics and business impact analysis
   - Top opportunities by investment potential
   - Technical configuration and performance metrics

### Output Schema
**Standardized Columns:**
- `str_code` - Store code
- `cluster_id` - Cluster assignment
- `missed_opportunities_count` - Count of missed sales opportunities
- `total_quantity_change` - Recommended quantity increases
- `investment_required` - Investment needed for recommendations
- `rule11_missed_sales_opportunity` - Binary flag for pipeline integration
- `business_rationale` - Business justification for recommendations
- `approval_reason` - Approval criteria met
- `fast_fish_compliant` - Sell-through validation status
- `sell_through_improvement` - Expected sell-through rate improvement

### Pipeline Integration
- **Consumers:** Steps 13-20 (consolidation, visualization, reporting)
- **Dependencies:** Steps 1-10 (data preparation, clustering, previous rules)
- **Format:** Enhanced Fast Fish CSV format for downstream compatibility

## Success Metrics

### Quantitative Metrics
- **Stores Analyzed:** 2,222 stores processed
- **Stores Flagged:** 312 stores (14.0%)
- **Missing Opportunities:** 650 opportunities identified
- **Top Performers:** 3,280 top performing SPUs identified
- **Total Unit Recommendations:** 67,625 units/15-days
- **Total Recommended Sales:** $5,320,227
- **Average Units per Flagged Store:** 217 units/15-days
- **Average Recommendation per Flagged Store:** $17,052

### Business Value Indicators
- **Constraint Satisfaction:** Recommendations scaled to store category performance
- **Validation Rate:** High percentage of Fast Fish compliant recommendations
- **Data Quality:** Real API data usage with realistic unit pricing
- **Performance:** 100x speed improvement with vectorized operations
- **Seasonal Relevance:** August blending for strategic planning

## Dependencies / Risks

### Critical Dependencies
1. **Clustering Results:** Requires `clustering_results_spu.csv` from step 6
2. **API Data:** Depends on `store_config_2025Q2_combined.csv` with SPU sales
3. **Sell-Through Validator:** Optional dependency for validation (`src/sell_through_validator.py`)
4. **Seasonal Data:** For August, requires 2024Q3 data for blending

### Risk Factors
1. **Data Availability:** Missing or incomplete SPU sales data reduces detection accuracy
2. **Threshold Sensitivity:** Top performer thresholds may need tuning based on business requirements
3. **Seasonal Data:** August blending depends on availability of 2024 seasonal data
4. **Validation Dependency:** Sell-through validation may be disabled if validator not available

### Mitigation Strategies
- Graceful degradation when seasonal data unavailable
- Fallback to recent data when validator not present
- Comprehensive logging for troubleshooting
- Memory management for large dataset processing

## Future Improvements

### Enhancement Opportunities
1. **Dynamic Thresholds:** Adaptive top performer thresholds based on category characteristics
2. **Predictive Modeling:** Machine learning to predict future top performers
3. **Multi-Period Analysis:** Consider longer-term trends for opportunity identification
4. **Store Attributes:** Incorporate store type/capacity constraints from steps 22-23

### Technical Improvements
1. **Performance Optimization:** Further vectorization of calculations
2. **Memory Efficiency:** Enhanced garbage collection for large datasets
3. **Error Handling:** More robust fallback mechanisms
4. **Validation Expansion:** Additional business rule validations

### Business Value Expansion
1. **Cross-Category Analysis:** Identify missed opportunities across related categories
2. **Trend Analysis:** Track missed opportunity patterns over time for strategic insights
3. **Store Segmentation:** Different opportunity thresholds for different store types
4. **Seasonal Adaptation:** Dynamic seasonal blending weights based on business calendar
