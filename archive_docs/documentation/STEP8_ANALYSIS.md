# Step 8 Analysis: Imbalanced Allocation Rule with Quantity Rebalancing

## Hardcoded Values Identified

### Analysis Configuration
1. **Default Analysis Level**: `ANALYSIS_LEVEL = "spu"` (line 61) - SPU-level analysis
2. **Alternative Option**: Commented option for "subcategory" analysis

### Data Period Configuration (Lines 63-66)
1. **Data Period**: `DATA_PERIOD_DAYS = 15` - API data is for half month (15 days)
2. **Target Period**: `TARGET_PERIOD_DAYS = 15` - Recommendations for same period
3. **Scaling Factor**: `SCALING_FACTOR = TARGET_PERIOD_DAYS / DATA_PERIOD_DAYS` - 1.0 for same period

### File Paths Configuration (Lines 70-83, 110-122)
1. **Cluster Files**: 
   - `"cluster_file": "output/clustering_results_subcategory.csv"` (line 71)
   - `"cluster_file": "output/clustering_results_spu.csv"` (line 78)
2. **Output Files**: 
   - `"output_prefix": "rule8_imbalanced_subcategory"` (line 73)
   - `"output_prefix": "rule8_imbalanced_spu"` (line 80)
3. **Planning Data Files**:
   - `PLANNING_DATA_FILE = "data/api_data/store_config_2025Q2_combined.csv"` (line 110)
   - `SEASONAL_PLANNING_FILE = "data/api_data/store_config_2024Q3_combined.csv"` (line 113)
4. **Quantity Data Files**:
   - `QUANTITY_DATA_FILE = "data/api_data/complete_spu_sales_2025Q2_combined.csv"` (line 111)
   - `SEASONAL_QUANTITY_FILE = "data/api_data/complete_spu_sales_2024Q3_combined.csv"` (line 114)
5. **Output Directory**: `OUTPUT_DIR = "output"` (line 121)

### Rule Parameters (Lines 124-140)
1. **Subcategory Level**:
   - `Z_SCORE_THRESHOLD = 2.0`
   - `MIN_CLUSTER_SIZE = 3`
   - `MIN_ALLOCATION_THRESHOLD = 0.1`
   - `MIN_REBALANCE_QUANTITY = 2.0`
   - `MAX_REBALANCE_PERCENTAGE = 0.3`
2. **SPU Level**:
   - `Z_SCORE_THRESHOLD = 3.0`
   - `MIN_CLUSTER_SIZE = 5`
   - `MIN_ALLOCATION_THRESHOLD = 0.05`
   - `MIN_REBALANCE_QUANTITY = 5.0`
   - `MAX_TOTAL_ADJUSTMENTS_PER_STORE = 8`
   - `MAX_REBALANCE_PERCENTAGE = 0.5`

### Seasonal Configuration (Lines 107-120)
1. **Current Month Detection**: `current_month = datetime.now().month` (line 95)
2. **August Special Handling**: Hardcoded August (month 8) for blended seasonal approach
3. **Seasonal Weighting**: Implicit in blend_seasonal_data function

### Grouping Configuration (Lines 74, 81)
1. **Subcategory Grouping**: `['season_name', 'sex_name', 'display_location_name', 'big_class_name', 'sub_cate_name']`
2. **SPU Grouping**: `['season_name', 'sex_name', 'display_location_name', 'big_class_name', 'sub_cate_name', 'sty_code']`

## Synthetic Data Usage Assessment

### ✅ Real Data Usage
- **API Data Integration**: Uses real `base_sal_qty` and `fashion_sal_qty` from API fields
- **Real Sales Data**: Processes actual store sales data for rebalancing recommendations
- **Real Unit Prices**: Calculates actual unit prices from API data ($20-$150 range)
- **Real Investment Calculations**: Uses real quantity × unit_price for investment calculations
- **Real Cluster Data**: Uses actual clustering results from step 6
- **Real Sell-Through Validation**: Integrates with Fast Fish sell-through validator
- **Real Seasonal Data**: Uses actual 2024Q3 and 2025Q2 data for seasonal blending

### ⚠️ Potential Synthetic Data Issues
- **Hardcoded Analysis Level**: Fixed to SPU-level analysis by default
- **Fixed File Paths**: Static input/output file locations
- **Fixed Data Periods**: Static 15-day period configuration
- **Fixed Rule Parameters**: Static thresholds for Z-Score analysis
- **Fixed Seasonal Months**: Hardcoded August special handling
- **Fixed Grouping Columns**: Static grouping columns for analysis

## Data Treatment Assessment

### ✅ Proper Data Handling
- **Real Quantity Data**: Uses actual `base_sal_qty` and `fashion_sal_qty` API fields
- **Real Unit Price Calculation**: Calculates realistic unit prices from API data
- **Meaningful Investment Calculations**: Uses real quantity × unit_price for investments
- **No Fake Prices**: Eliminated fake $1.00 unit prices
- **Sell-Through Validation**: Only recommends rebalancing that improves sell-through rate
- **Cluster-Based Analysis**: Uses real cluster assignments for peer comparison
- **Seasonal Data Blending**: Combines recent trends with seasonal patterns
- **Z-Score Analysis**: Uses statistical methods for imbalance detection
- **Quantity Rebalancing**: Provides specific unit quantity rebalancing recommendations

### ⚠️ Areas for Improvement
1. **Configurable Analysis Level**: Should allow dynamic selection of analysis type
2. **Flexible File Paths**: Should support configurable input/output locations
3. **Dynamic Data Periods**: Should allow customization of analysis periods
4. **Configurable Rule Parameters**: Should allow customization of thresholds
5. **Configurable Seasonal Handling**: Should allow customization of seasonal approaches
6. **Dynamic Month Selection**: Should support different months/seasons

## Business Logic Alignment

### ✅ Aligned with Business Requirements
- **Real Data Processing**: Uses actual store sales data for all recommendations
- **Product Recommendations**: Provides specific unit quantity rebalancing targets
- **Sell-Through Validation**: Only recommends rebalancing that improves sell-through rate
- **No Placeholder Data**: No synthetic or placeholder data detected in core processing
- **Investment-Neutral Rebalancing**: Provides rebalancing without additional cost
- **Cluster-Based Analysis**: Uses peer store analysis for appropriate recommendations
- **Seasonal Awareness**: Incorporates seasonal patterns with recent trends
- **Statistical Rigor**: Uses Z-Score analysis for scientific imbalance detection

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
9. **Configurable Grouping**: Allow customization of grouping columns for analysis
