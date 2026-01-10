# Step 11 Analysis: Missed Sales Opportunity Rule with Quantity Recommendations

## Hardcoded Values Identified

### Analysis Configuration
1. **Default Analysis Level**: `ANALYSIS_LEVEL = "spu"` (line 60) - SPU-level analysis

### Data Period Configuration (Lines 84-87)
1. **Data Period**: `DATA_PERIOD_DAYS = 15` - API data is for half month (15 days)
2. **Target Period**: `TARGET_PERIOD_DAYS = 15` - Recommendations for same period
3. **Scaling Factor**: `SCALING_FACTOR = TARGET_PERIOD_DAYS / DATA_PERIOD_DAYS` - 1.0 for same period

### File Paths Configuration (Lines 62, 72-77, 80-82)
1. **Cluster File**: `CLUSTER_RESULTS_FILE = "output/clustering_results_spu.csv"` (line 62)
2. **Base Data Files**:
   - `BASE_DATA_FILE = "data/api_data/store_config_2025Q2_combined.csv"` (line 72)
   - `BASE_QUANTITY_FILE = "data/api_data/complete_spu_sales_2025Q2_combined.csv"` (line 73)
3. **Seasonal Data Files**:
   - `SEASONAL_DATA_FILE = "data/api_data/store_config_2024Q3_combined.csv"` (line 75)
   - `SEASONAL_QUANTITY_FILE = "data/api_data/complete_spu_sales_2024Q3_combined.csv"` (line 76)
4. **Output Directory**: `OUTPUT_DIR = "output"` (line 61)

### Rule Parameters (Lines 89-102)
1. **Top Performer Threshold**: `TOP_PERFORMER_THRESHOLD = 0.95` (Top 5% of SPUs)
2. **Minimum Cluster Stores**: `MIN_CLUSTER_STORES = 8` (Minimum stores in cluster)
3. **Minimum Stores Selling**: `MIN_STORES_SELLING = 5` (Minimum stores selling SPU)
4. **Minimum SPU Sales**: `MIN_SPU_SALES = 200` (Minimum sales to avoid noise)
5. **Adoption Threshold**: `ADOPTION_THRESHOLD = 0.75` (75% of cluster stores)
6. **Maximum Recommendations Per Store**: `MAX_RECOMMENDATIONS_PER_STORE = 10`
7. **Minimum Opportunity Score**: `MIN_OPPORTUNITY_SCORE = 0.15`
8. **Minimum Sales Gap**: `MIN_SALES_GAP = 100`
9. **Minimum Quantity Gap**: `MIN_QTY_GAP = 2.0`
10. **Minimum Adoption Rate**: `MIN_ADOPTION_RATE = 0.70`
11. **Minimum Investment Threshold**: `MIN_INVESTMENT_THRESHOLD = 150`

### Seasonal Configuration (Lines 66-82)
1. **Current Month Detection**: `current_month = datetime.now().month` (line 66)
2. **August Special Handling**: Hardcoded August (month 8) for blended seasonal approach
3. **Seasonal Weighting**: Default weights of 0.4 recent + 0.6 seasonal in blend_seasonal_data function

### Testing Configuration (Line 105)
1. **Testing Mode**: `TESTING_MODE = False` - Can be overridden by command line argument

## Synthetic Data Usage Assessment

### ✅ Real Data Usage
- **API Data Integration**: Uses real `base_sal_qty` and `fashion_sal_qty` from API fields
- **Real Sales Data**: Processes actual store sales data for missed sales detection
- **Real SPU Codes**: Uses actual SPU codes from the data
- **Real Unit Prices**: Calculates actual unit prices from API data ($20-$150 range)
- **Real Investment Calculations**: Uses real quantity × unit_price for investment calculations
- **Real Cluster Data**: Uses actual clustering results from step 6
- **Real Sell-Through Validation**: Integrates with Fast Fish sell-through validator
- **Real Seasonal Data**: Uses actual 2024Q3 and 2025Q2 data for seasonal blending
- **Real Quantity Calculations**: Uses actual estimated SPU quantities from API data

### ⚠️ Potential Synthetic Data Issues
- **Hardcoded Analysis Level**: Fixed to SPU-level analysis by default
- **Fixed File Paths**: Static input/output file locations
- **Fixed Data Periods**: Static 15-day period configuration
- **Fixed Rule Parameters**: Static thresholds for missed sales analysis
- **Fixed Seasonal Months**: Hardcoded August special handling
- **Fixed Testing Mode**: Static testing mode configuration
- **Fixed Weights**: Static seasonal blending weights

## Data Treatment Assessment

### ✅ Proper Data Handling
- **Real Quantity Data**: Uses actual `base_sal_qty` and `fashion_sal_qty` API fields
- **Real Unit Price Calculation**: Calculates realistic unit prices from API data
- **Meaningful Investment Calculations**: Uses real quantity × unit_price for investments
- **No Fake Prices**: Eliminated fake $1.00 unit prices
- **Sell-Through Validation**: Only recommends additions that improve sell-through rate
- **Cluster-Based Analysis**: Uses real cluster assignments for peer comparison
- **Seasonal Data Blending**: Combines recent trends with seasonal patterns
- **Quantity Recommendations**: Provides specific unit quantity addition recommendations
- **Incremental Calculations**: Calculates incremental additions needed (not absolute targets)
- **Performance-Based Filtering**: Uses adoption rates and performance percentiles

### ⚠️ Areas for Improvement
1. **Configurable Analysis Level**: Should allow dynamic selection of analysis type
2. **Flexible File Paths**: Should support configurable input/output locations
3. **Dynamic Data Periods**: Should allow customization of analysis periods
4. **Configurable Rule Parameters**: Should allow customization of thresholds
5. **Configurable Seasonal Handling**: Should allow customization of seasonal approaches
6. **Dynamic Month Selection**: Should support different months/seasons
7. **Configurable Weights**: Should allow customization of seasonal blending weights
8. **Configurable Testing Mode**: Should allow dynamic testing mode selection

## Business Logic Alignment

### ✅ Aligned with Business Requirements
- **Real Data Processing**: Uses actual store sales data for all recommendations
- **Product Recommendations**: Provides specific unit quantity addition targets
- **Sell-Through Validation**: Only recommends additions that improve sell-through rate
- **No Placeholder Data**: No synthetic or placeholder data detected in core processing
- **Investment Calculations**: Provides realistic investment estimates
- **Cluster-Based Analysis**: Uses peer store analysis for appropriate recommendations
- **Seasonal Awareness**: Incorporates seasonal patterns with recent trends
- **Performance Optimization**: Fast processing with optimized algorithms
- **Selectivity Controls**: Strict filtering to reduce recommendation volume
- **Incremental Recommendations**: Provides additional amounts needed (not absolute targets)

### ⚠️ Configuration Limitations
- **Fixed Analysis Level**: Hardcoded to SPU-level analysis may not suit all scenarios
- **Static Rule Parameters**: Fixed thresholds may not be optimal for all datasets
- **Fixed Data Periods**: Static periods may not work for different analysis windows
- **Regional Limitations**: Hardcoded configuration may not work for different regions
- **Limited Flexibility**: Fixed settings may limit adaptability to different business needs
- **Seasonal Constraints**: Fixed August handling may not work for other seasonal transitions

## Recommendations

1. **Configurable Analysis Selection**: Allow dynamic selection of analysis level via parameters
2. **Environment Variable Support**: Move hardcoded values to configuration/environment variables
3. **Flexible Data Periods**: Allow customization of analysis periods
4. **Dynamic Rule Parameters**: Support configurable thresholds and parameters
5. **Configurable Seasonal Handling**: Allow customization of seasonal blending approaches
6. **Dynamic Month Support**: Support different months/seasons for analysis
7. **Regional Adaptation**: Support different configurations for different regions
8. **Flexible File Paths**: Allow customization of input/output locations
9. **Configurable Weights**: Allow customization of seasonal blending weights
10. **Enhanced Documentation**: Document all configuration parameters and their business impact
