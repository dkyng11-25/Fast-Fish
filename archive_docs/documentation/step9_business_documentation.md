# Step 9: Below Minimum SPU Rule with Quantity Increase Recommendations

## Identification
**File:** `src/step9_below_minimum_rule.py`
**Type:** Business Rule Implementation
**Execution Order:** Step 9 in the 20-step pipeline

## Purpose / Business Value

### Core Objective
Identifies store-SPU combinations with positive but below minimum viable allocation levels and provides specific UNIT QUANTITY INCREASE recommendations to optimize inventory levels.

### Business Impact
- **Inventory Optimization:** Ensures stores maintain minimum viable SPU allocations for optimal product mix
- **Revenue Protection:** Prevents lost sales opportunities from under-stocked popular items
- **Operational Efficiency:** Provides actionable quantity recommendations for store replenishment
- **Constraint Satisfaction:** Only recommends positive quantity increases, never decreases

### Key Enhancements
1. **Real Quantity Data:** Uses actual unit quantities from API fields (`base_sal_qty`, `fashion_sal_qty`) instead of treating sales amounts as quantities
2. **Unit Price Realism:** Calculates realistic unit prices ($20-$150 range) from API data for accurate investment calculations
3. **Fast Fish Validation:** Integrates sell-through validation to ensure recommendations improve sell-through rates
4. **Seasonal Blending:** For August, combines recent trends (May-July) with seasonal patterns (Aug 2024) for balanced recommendations
5. **Pipeline Standardization:** Outputs follow enhanced Fast Fish format with standardized column names

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
- `MINIMUM_STYLE_THRESHOLD = 0.8` - Minimum viable allocation threshold
- `MIN_BOOST_QUANTITY = 10.0` - Minimum quantity increase recommendation
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

### 2. Below Minimum Detection
1. Calculate current SPU allocation levels for each store-SPU combination
2. Identify cases where: `0 < current_allocation < MINIMUM_STYLE_THRESHOLD`
3. Apply business filters:
   - Minimum sales volume threshold
   - Cluster size requirements
   - Discontinuation threshold (recommend discontinuation below 0.1 allocation)

### 3. Quantity Recommendation Calculation
1. Calculate increase needed to reach minimum viable allocation
2. Apply minimum boost quantity constraint
3. Scale recommendations to 15-day period matching API data
4. Calculate investment requirements using real unit prices

### 4. Fast Fish Validation
1. Initialize sell-through validator with historical data
2. For each below minimum case:
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
1. **Detailed Results (period-labeled):** `output/rule9_below_minimum_spu_sellthrough_results_{YYYYMMX}.csv`
   - Example: `..._202509A.csv`, `..._202509B.csv`
   - Store-level recommendations with quantity increases
   - Sell-through validation metrics
   - Investment calculations and business rationale

2. **Detailed Opportunities (period-labeled):** `output/rule9_below_minimum_spu_sellthrough_opportunities_{YYYYMMX}.csv`
   - Per-store-SPU opportunities with Fast Fish metrics
   - Example: `..._202509A.csv`, `..._202509B.csv`

3. **Summary Report (period-labeled):** `output/rule9_below_minimum_spu_sellthrough_summary_{YYYYMMX}.md`
   - Key metrics and business impact analysis
   - Top opportunities by investment potential
   - Technical configuration and critical fixes applied

4. **Backward-Compatible (unlabeled) Copies for Step 13:**
   - `output/rule9_below_minimum_spu_sellthrough_results.csv`
   - `output/rule9_below_minimum_spu_sellthrough_opportunities.csv`

### Output Schema
**Standardized Columns:**
- `str_code` - Store code
- `cluster_id` - Cluster assignment
- `below_minimum_spus_count` - Count of below minimum SPUs
- `total_quantity_change` - Recommended quantity increases
- `investment_required` - Investment needed for recommendations
- `rule9_below_minimum_spu` - Binary flag for pipeline integration
- `business_rationale` - Business justification for recommendations
- `approval_reason` - Approval criteria met
- `fast_fish_compliant` - Sell-through validation status
- `sell_through_improvement` - Expected sell-through rate improvement

### Pipeline Integration
- **Consumers:** Steps 13-20 (consolidation, visualization, reporting)
- **Dependencies:** Steps 1-8 (data preparation, clustering, previous rules)
- **Format:** Enhanced Fast Fish CSV format for downstream compatibility
- **Compatibility Note:** Step 13 expects unlabeled filenames for Rule 9; this step now writes both period-labeled and unlabeled files to ensure seamless consolidation.

### Target Labeling Overrides (Aligns with Step 8)
- Use current inputs (e.g., August 2025) while labeling outputs for a target month (e.g., September 2025).
- New CLI flags:
  - `--target-yyyymm` (e.g., 202509)
  - `--target-period` (A or B)

#### Example: Generate September-labeled outputs using August inputs
```bash
python3 -m src.step9_below_minimum_rule \
  --yyyymm 202508 --period A --analysis-level spu \
  --target-yyyymm 202509 --target-period A

python3 -m src.step9_below_minimum_rule \
  --yyyymm 202508 --period B --analysis-level spu \
  --target-yyyymm 202509 --target-period B
```

## Success Metrics

### Quantitative Metrics
- **Stores Analyzed:** 2,222 stores processed
- **Below Minimum Cases:** 0 cases identified (in current run)
- **Recommendations Generated:** 0 quantity increases recommended
- **Fast Fish Compliance:** 100% validation rate (when applicable)
- **Average Increase:** N/A (no cases identified)
- **Total Investment:** $0 (no cases identified)

### Business Value Indicators
- **Constraint Satisfaction:** 100% positive quantity increases only
- **Validation Rate:** All recommendations validated for sell-through improvement
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
2. **Threshold Sensitivity:** Minimum allocation threshold may need tuning based on business requirements
3. **Seasonal Data:** August blending depends on availability of 2024 seasonal data
4. **Validation Dependency:** Sell-through validation may be disabled if validator not available

### Mitigation Strategies
- Graceful degradation when seasonal data unavailable
- Fallback to recent data when validator not present
- Comprehensive logging for troubleshooting
- Memory management for large dataset processing

## Future Improvements

### Enhancement Opportunities
1. **Dynamic Thresholds:** Adaptive minimum allocation thresholds based on category characteristics
2. **Predictive Modeling:** Machine learning to predict optimal minimum allocations
3. **Multi-Period Analysis:** Consider longer-term trends for minimum allocation decisions
4. **Store Attributes:** Incorporate store type/capacity constraints from steps 22-23

### Technical Improvements
1. **Performance Optimization:** Further vectorization of calculations
2. **Memory Efficiency:** Enhanced garbage collection for large datasets
3. **Error Handling:** More robust fallback mechanisms
4. **Validation Expansion:** Additional business rule validations

### Business Value Expansion
1. **Cross-Category Analysis:** Identify below minimum patterns across related categories
2. **Trend Analysis:** Track below minimum patterns over time for strategic insights
3. **Store Segmentation:** Different minimum thresholds for different store types
4. **Seasonal Adaptation:** Dynamic seasonal blending weights based on business calendar
