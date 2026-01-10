# Step 10 Analysis: SPU Assortment Optimization (Smart Overcapacity Rule)

## Hardcoded Values Identified

### Analysis Configuration
1. **Default Analysis Level**: `ANALYSIS_LEVEL = "spu"` (line 54) - SPU-level analysis

### Data Period Configuration (Lines 55-57)
1. **Data Period**: `DATA_PERIOD_DAYS = 15` - API data is for half month (15 days)
2. **Target Period**: `TARGET_PERIOD_DAYS = 15` - Recommendations for same period
3. **Scaling Factor**: `SCALING_FACTOR = TARGET_PERIOD_DAYS / DATA_PERIOD_DAYS` - 1.0 for same period

### File Paths Configuration (Lines 67-77, 80-89, 92, 99)
1. **Base Data Files**:
   - `BASE_DATA_FILE = "data/api_data/store_config_2025Q2_combined.csv"` (line 67)
   - `BASE_QUANTITY_FILE = "data/api_data/complete_spu_sales_2025Q2_combined.csv"` (line 68)
2. **Seasonal Data Files**:
   - `SEASONAL_DATA_FILE = "data/api_data/store_config_2024Q3_combined.csv"` (line 70)
   - `SEASONAL_QUANTITY_FILE = "data/api_data/complete_spu_sales_2024Q3_combined.csv"` (line 71)
3. **Cluster Files**: `"cluster_file": "output/clustering_results_spu.csv"` (line 84)
4. **Output Files**: `"output_prefix": "rule10_smart_overcapacity_spu"` (line 85)
5. **Quantity Data**: `QUANTITY_DATA_FILE = BASE_QUANTITY_FILE` (line 92)
6. **Output Directory**: `OUTPUT_DIR = "output"` (line 93)

### Rule Parameters (Lines 94-97)
1. **Minimum Cluster Size**: `MIN_CLUSTER_SIZE = 3` (Reduced from 5 for more opportunities)
2. **Minimum Sales Volume**: `MIN_SALES_VOLUME = 20` (Reduced from 50 to find more cases)
3. **Minimum Reduction Quantity**: `MIN_REDUCTION_QUANTITY = 1.0` (Reduced from 3.0 for smaller reductions)
4. **Maximum Reduction Percentage**: `MAX_REDUCTION_PERCENTAGE = 0.4` (Increased to 40% for flexibility)

### Seasonal Configuration (Lines 61-77)
1. **Current Month Detection**: `current_month = datetime.now().month` (line 61)
2. **August Special Handling**: Hardcoded August (month 8) for blended seasonal approach
3. **Seasonal Weighting**: Implicit in blend_seasonal_data function

### Analysis Configurations (Lines 80-88)
1. **Business Unit**: `"business_unit": "store-spu"` (line 86)
2. **Minimum Stores Threshold**: `"min_stores_threshold": 3` (line 87)

## Synthetic Data Usage Assessment

### ✅ Real Data Usage
- **API Data Integration**: Uses real `base_sal_qty` and `fashion_sal_qty` from API fields
- **Real Sales Data**: Processes actual store sales data for overcapacity detection
- **Real SPU Codes**: Uses actual SPU codes from the data instead of fake category keys
- **Real Unit Prices**: Calculates actual unit prices from API data ($20-$150 range)
- **Real Investment Calculations**: Uses real quantity × unit_price for cost savings
- **Real Cluster Data**: Uses actual clustering results from step 6
- **Real Sell-Through Validation**: Integrates with Fast Fish sell-through validator
- **Real Seasonal Data**: Uses actual 2024Q3 and 2025Q2 data for seasonal blending

### ⚠️ Potential Synthetic Data Issues
- **Hardcoded Analysis Level**: Fixed to SPU-level analysis by default
- **Fixed File Paths**: Static input/output file locations
- **Fixed Data Periods**: Static 15-day period configuration
- **Fixed Rule Parameters**: Static thresholds for overcapacity analysis
- **Fixed Seasonal Months**: Hardcoded August special handling
- **Fixed Business Unit**: Static business unit configuration
- **Fixed Minimum Stores Threshold**: Static threshold configuration

## Data Treatment Assessment

### ✅ Proper Data Handling
- **Real Quantity Data**: Uses actual `base_sal_qty` and `fashion_sal_qty` API fields
- **Real Unit Price Calculation**: Calculates realistic unit prices from API data
- **Meaningful Investment Calculations**: Uses real quantity × unit_price for cost savings
- **No Fake Prices**: Eliminated fake $1.00 unit prices
- **Sell-Through Validation**: Only recommends reductions that improve sell-through rate
- **Real SPU Processing**: Uses actual SPU codes instead of fake category aggregations
- **Cluster-Based Analysis**: Uses real cluster assignments for peer comparison
- **Seasonal Data Blending**: Combines recent trends with seasonal patterns
- **Quantity Reductions**: Provides specific unit quantity reduction recommendations

### ⚠️ Areas for Improvement
1. **Configurable Analysis Level**: Should allow dynamic selection of analysis type
2. **Flexible File Paths**: Should support configurable input/output locations
3. **Dynamic Data Periods**: Should allow customization of analysis periods
4. **Configurable Rule Parameters**: Should allow customization of thresholds
5. **Configurable Seasonal Handling**: Should allow customization of seasonal approaches
6. **Dynamic Month Selection**: Should support different months/seasons
7. **Configurable Business Unit**: Should allow customization of business unit settings

## Business Logic Alignment

### ✅ Aligned with Business Requirements
- **Real Data Processing**: Uses actual store sales data for all recommendations
- **Product Recommendations**: Provides specific unit quantity reduction targets
- **Sell-Through Validation**: Only recommends reductions that improve sell-through rate
- **No Placeholder Data**: No synthetic or placeholder data detected in core processing
- **Cost Savings Focus**: Provides realistic cost savings estimates
- **Cluster-Based Analysis**: Uses peer store analysis for appropriate recommendations
- **Seasonal Awareness**: Incorporates seasonal patterns with recent trends
- **Performance Optimization**: Fast processing with bulk operations

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
9. **Configurable Business Unit**: Allow customization of business unit settings
10. **Enhanced Documentation**: Document all configuration parameters and their business impact
