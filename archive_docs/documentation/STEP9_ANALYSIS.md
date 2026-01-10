# Step 9 Analysis: Below Minimum Rule - Fixed Version

## Hardcoded Values Identified

### Analysis Configuration
1. **Default Analysis Level**: `ANALYSIS_LEVEL = "spu"` (line 38) - SPU-level analysis

### Data Period Configuration (Lines 39-42)
1. **Data Period**: `DATA_PERIOD_DAYS = 15` - API data is for half month (15 days)
2. **Target Period**: `TARGET_PERIOD_DAYS = 15` - Recommendations for same period
3. **Scaling Factor**: `SCALING_FACTOR = TARGET_PERIOD_DAYS / DATA_PERIOD_DAYS` - 1.0 for same period

### File Paths Configuration (Lines 44-46, 60-70)
1. **Cluster File**: `CLUSTER_RESULTS_FILE = "output/clustering_results_spu.csv"` (line 45)
2. **Output Directory**: `OUTPUT_DIR = "output"` (line 46)
3. **Data Files**:
   - `DATA_FILE = "data/api_data/store_config_data.csv"` (line 60)
   - `QUANTITY_DATA_FILE = "data/api_data/complete_spu_sales_2025Q2_combined.csv"` (line 61)
   - `SEASONAL_DATA_FILE = "data/api_data/store_config_2024Q3_combined.csv"` (line 63)
   - `SEASONAL_QUANTITY_FILE = "data/api_data/complete_spu_sales_2024Q3_combined.csv"` (line 64)

### Rule Parameters (Lines 72-75)
1. **Minimum Style Threshold**: `MINIMUM_STYLE_THRESHOLD = 0.03` (3% vs 5%)
2. **Minimum Boost Quantity**: `MIN_BOOST_QUANTITY = 0.5` (minimum increase for smaller adjustments)
3. **Never Decrease Flag**: `NEVER_DECREASE_BELOW_MINIMUM = True` (Critical: Never recommend decreases)

### Seasonal Configuration (Lines 55-70)
1. **Current Month Detection**: `current_month = datetime.now().month` (line 55)
2. **August Special Handling**: Hardcoded August (month 8) for blended seasonal approach
3. **Seasonal Weighting**: Implicit in blend_seasonal_data function

### Additional Filters (Lines 298-300)
1. **Minimum Sales**: `original_sales_amt >= 25` (Reduced from ¥100 to ¥25 for more inclusivity)
2. **Minimum Cluster Size**: `3 stores minimum` (Reduced from 3 to 2 stores minimum)

## Synthetic Data Usage Assessment

### ✅ Real Data Usage
- **API Data Integration**: Uses real store configuration data
- **Real Sales Data**: Processes actual store sales data for recommendations
- **Real Cluster Data**: Uses actual clustering results from step 6
- **Real Sell-Through Validation**: Integrates with Fast Fish sell-through validator
- **Real Seasonal Data**: Uses actual 2024Q3 and 2025Q2 data for seasonal blending
- **Real Quantity Calculations**: Uses actual sales amounts scaled to target periods

### ⚠️ Potential Synthetic Data Issues
- **Hardcoded Analysis Level**: Fixed to SPU-level analysis by default
- **Fixed File Paths**: Static input/output file locations
- **Fixed Data Periods**: Static 15-day period configuration
- **Fixed Rule Parameters**: Static thresholds for minimum style analysis
- **Fixed Seasonal Months**: Hardcoded August special handling
- **Fixed Unit Price**: Default estimate of `50.0` (line 354) when real data unavailable

## Data Treatment Assessment

### ✅ Proper Data Handling
- **Real Sales Data**: Uses actual store sales data for all recommendations
- **No Negative Quantities**: Fixed to ensure all recommendations are positive increases
- **Correct Business Logic**: Below minimum should INCREASE allocation, not decrease
- **Sell-Through Validation**: Only recommends increases that improve sell-through rate
- **Cluster-Based Analysis**: Uses real cluster assignments for peer comparison
- **Seasonal Data Blending**: Combines recent trends with seasonal patterns
- **Quantity Recommendations**: Provides specific unit quantity increase recommendations

### ⚠️ Areas for Improvement
1. **Configurable Analysis Level**: Should allow dynamic selection of analysis type
2. **Flexible File Paths**: Should support configurable input/output locations
3. **Dynamic Data Periods**: Should allow customization of analysis periods
4. **Configurable Rule Parameters**: Should allow customization of thresholds
5. **Configurable Seasonal Handling**: Should allow customization of seasonal approaches
6. **Dynamic Month Selection**: Should support different months/seasons
7. **Configurable Unit Prices**: Should allow customization of default unit prices

## Business Logic Alignment

### Aligned with Business Requirements
- **Real Data Processing**: Uses actual store sales data for all recommendations
- **Product Recommendations**: Provides specific unit quantity increase targets
- **Sell-Through Validation**: Only recommends increases that improve sell-through rate
- **No Placeholder Data**: No synthetic or placeholder data detected in core processing
- **Correct Business Logic**: Below minimum should INCREASE allocation (fixed)
- **No Negative Quantities**: All recommendations are positive increases (fixed)
- **Investment Calculations**: Provides realistic investment estimates
- **Cluster-Based Analysis**: Uses peer store analysis for appropriate recommendations
- **Seasonal Awareness**: Incorporates seasonal patterns with recent trends

### Configuration Limitations
- **Fixed Analysis Level**: Hardcoded to SPU-level analysis may not suit all scenarios
- **Static Rule Parameters**: Fixed thresholds may not be optimal for all datasets
- **Fixed Data Periods**: Static periods may not work for different analysis windows
- **Regional Limitations**: Hardcoded configuration may not work for different regions
- **Limited Flexibility**: Fixed settings may limit adaptability to different business needs
- **Seasonal Constraints**: Fixed August handling may not work for other seasonal transitions

## Target Output Labeling Overrides and Backward Compatibility

Step 9 supports target output labeling overrides to align with Step 8. When provided, the CLI flags `--target-yyyymm` and `--target-period` set the environment variables `PIPELINE_TARGET_YYYYMM` and `PIPELINE_TARGET_PERIOD`. These are used to compute the period label for outputs without changing the input data month.

Labeled outputs written by Step 9:
- `output/rule9_below_minimum_spu_sellthrough_results_{YYYYMMX}.csv`
- `output/rule9_below_minimum_spu_sellthrough_opportunities_{YYYYMMX}.csv`
- `output/rule9_below_minimum_spu_sellthrough_summary_{YYYYMMX}.md`

Backward-compatible unlabeled copies (for Step 13):
- `output/rule9_below_minimum_spu_sellthrough_results.csv`
- `output/rule9_below_minimum_spu_sellthrough_opportunities.csv`

Example: generate September-labeled outputs (202509A/B) using August inputs (202508A/B):

```bash
python3 -m src.step9_below_minimum_rule \
  --yyyymm 202508 --period A --analysis-level spu \
  --target-yyyymm 202509 --target-period A

python3 -m src.step9_below_minimum_rule \
  --yyyymm 202508 --period B --analysis-level spu \
  --target-yyyymm 202509 --target-period B
```

Integration note: Step 13 (`src/step13_consolidate_spu_rules.py`) expects unlabeled Rule 9 inputs and will read the backward-compatible files above.

## Recommendations

1. **Configurable Analysis Selection**: Allow dynamic selection of analysis level via parameters
2. **Environment Variable Support**: Move hardcoded values to configuration/environment variables
3. **Flexible Data Periods**: Allow customization of analysis periods
4. **Dynamic Rule Parameters**: Support configurable thresholds and parameters
5. **Configurable Seasonal Handling**: Allow customization of seasonal blending approaches
6. **Dynamic Month Support**: Support different months/seasons for analysis
7. **Regional Adaptation**: Support different configurations for different regions
8. **Flexible File Paths**: Allow customization of input/output locations
9. **Configurable Unit Prices**: Allow customization of default unit price estimates
10. **Enhanced Documentation**: Document all configuration parameters and their business impact
