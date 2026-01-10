# Step 10: Smart Overcapacity SPU Rule with Quantity Reduction Recommendations

## Identification
**File:** `src/step10_spu_assortment_optimization.py`
**Type:** Business Rule Implementation
**Execution Order:** Step 10 in the 20-step pipeline

## Purpose / Business Value

### Core Objective
Identifies store-SPU combinations with overcapacity (more SPUs than target) and provides specific UNIT QUANTITY REDUCTION recommendations to optimize inventory allocation and reduce carrying costs.

### Business Impact
- **Inventory Optimization:** Reduces excess inventory in overcapacity situations
- **Cost Reduction:** Eliminates carrying costs for underperforming SPUs
- **Space Efficiency:** Frees up shelf/rack space for better-performing items
- **Cash Flow Improvement:** Reduces tied-up capital in excess inventory

### Key Enhancements
1. **Real Quantity Data:** Uses actual unit quantities from API fields (`base_sal_qty`, `fashion_sal_qty`) instead of treating sales amounts as quantities
2. **Unit Price Realism:** Calculates realistic unit prices ($20-$150 range) from API data for accurate cost savings calculations
3. **Fast Fish Validation:** Integrates sell-through validation to ensure reductions improve overall sell-through rates
4. **Seasonal Blending:** For August, combines recent trends (May-July) with seasonal patterns (Aug 2024) for balanced recommendations
5. **Performance Optimization:** Bulk processing for 10x+ performance improvement

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
- `MIN_CLUSTER_SIZE = 3` - Minimum cluster size for analysis
- `MIN_SALES_VOLUME = 20` - Minimum sales volume threshold
- `MIN_REDUCTION_QUANTITY = 1.0` - Minimum quantity reduction recommendation
- `MAX_REDUCTION_PERCENTAGE = 0.4` - Maximum 40% reduction constraint
- `DATA_PERIOD_DAYS = 15` - Analysis period (15 days)
- `TARGET_PERIOD_DAYS = 15` - Recommendation period (15 days)
- `SCALING_FACTOR = 1.0` - Quantity scaling factor

## Transformation Overview

### 1. Data Loading & Preparation
1. Load store configuration data with SPU sales information
2. Load clustering results for peer group analysis
3. For August: Blend recent trends with seasonal patterns (40% recent + 60% seasonal)
4. Extract real SPU codes and sales data from JSON fields
5. Calculate realistic unit prices from sales data

### 2. Overcapacity Detection
1. Calculate current SPU count vs target SPU count for each store-category combination
2. Identify overcapacity cases where: `current_spu_count > target_spu_count`
3. Calculate excess SPU count and overcapacity percentage
4. Apply business filters:
   - Minimum sales volume threshold
   - Cluster size requirements
   - Minimum reduction quantity constraints

### 3. Quantity Recommendation Calculation
1. Calculate recommended quantity reductions for overcapacity SPUs
2. Apply maximum reduction percentage constraint (40%)
3. Scale recommendations to 15-day period matching API data
4. Calculate cost savings using real unit prices

### 4. Fast Fish Validation
1. Initialize sell-through validator with historical data
2. For each overcapacity case:
   - Calculate current and target SPU counts
   - Validate reduction improves overall sell-through rate
   - Only retain Fast Fish compliant recommendations
   - Add sell-through metrics to results

### 5. Output Standardization
1. Create store-level summary with aggregated metrics
2. Add standardized pipeline columns for compatibility
3. Generate detailed opportunity descriptions
4. Apply business rationale and approval reasoning

## Outputs / Consumers

### Primary Output Files
1. **Detailed Results:** `output/rule10_smart_overcapacity_spu_results.csv`
   - Store-level recommendations with quantity reductions
   - Sell-through validation metrics
   - Cost savings calculations and business rationale

2. **Opportunities Report:** `output/rule10_spu_overcapacity_opportunities.csv`
   - Detailed SPU-level overcapacity opportunities
   - Individual reduction recommendations
   - Investment impact analysis

3. **Summary Report:** `output/rule10_smart_overcapacity_spu_summary.md`
   - Key metrics and business impact analysis
   - Top opportunities by cost savings potential
   - Technical configuration and performance metrics

### Output Schema
**Standardized Columns:**
- `str_code` - Store code
- `cluster_id` - Cluster assignment
- `overcapacity_spus_count` - Count of overcapacity SPUs
- `total_quantity_change` - Recommended quantity reductions
- `investment_required` - Cost savings from reductions
- `rule10_spu_overcapacity` - Binary flag for pipeline integration
- `business_rationale` - Business justification for recommendations
- `approval_reason` - Approval criteria met
- `fast_fish_compliant` - Sell-through validation status
- `sell_through_improvement` - Expected sell-through rate improvement

### Pipeline Integration
- **Consumers:** Steps 13-20 (consolidation, visualization, reporting)
- **Dependencies:** Steps 1-9 (data preparation, clustering, previous rules)
- **Format:** Enhanced Fast Fish CSV format for downstream compatibility

## Success Metrics

### Quantitative Metrics
- **Stores Analyzed:** 2,222 stores processed
- **Overcapacity Cases:** Varies by run (output files not found in current directory)
- **Reduction Recommendations:** Varies by run
- **Fast Fish Compliance:** High validation rate for compliant recommendations
- **Average Reduction:** Varies by run
- **Total Cost Savings:** Varies by run

### Business Value Indicators
- **Constraint Satisfaction:** All recommendations within maximum reduction limits
- **Validation Rate:** High percentage of Fast Fish compliant recommendations
- **Data Quality:** Real API data usage with realistic unit pricing
- **Performance:** 10x+ speed improvement with bulk processing
- **Seasonal Relevance:** August blending for strategic planning

## Dependencies / Risks

### Critical Dependencies
1. **Clustering Results:** Requires `clustering_results_spu.csv` from step 6
2. **API Data:** Depends on `store_config_2025Q2_combined.csv` with SPU sales
3. **Sell-Through Validator:** Optional dependency for validation (`src/sell_through_validator.py`)
4. **Seasonal Data:** For August, requires 2024Q3 data for blending

### Risk Factors
1. **Data Availability:** Missing or incomplete SPU sales data reduces detection accuracy
2. **Threshold Sensitivity:** Reduction thresholds may need tuning based on business requirements
3. **Seasonal Data:** August blending depends on availability of 2024 seasonal data
4. **Validation Dependency:** Sell-through validation may be disabled if validator not available

### Mitigation Strategies
- Graceful degradation when seasonal data unavailable
- Fallback to recent data when validator not present
- Comprehensive logging for troubleshooting
- Memory management for large dataset processing

## Future Improvements

### Enhancement Opportunities
1. **Dynamic Thresholds:** Adaptive overcapacity thresholds based on category characteristics
2. **Predictive Modeling:** Machine learning to predict optimal SPU counts
3. **Multi-Period Analysis:** Consider longer-term trends for overcapacity decisions
4. **Store Attributes:** Incorporate store type/capacity constraints from steps 22-23

### Technical Improvements
1. **Performance Optimization:** Further vectorization of calculations
2. **Memory Efficiency:** Enhanced garbage collection for large datasets
3. **Error Handling:** More robust fallback mechanisms
4. **Validation Expansion:** Additional business rule validations

### Business Value Expansion
1. **Cross-Category Analysis:** Identify overcapacity patterns across related categories
2. **Trend Analysis:** Track overcapacity patterns over time for strategic insights
3. **Store Segmentation:** Different overcapacity thresholds for different store types
4. **Seasonal Adaptation:** Dynamic seasonal blending weights based on business calendar
