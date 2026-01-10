# Step 12 Analysis: Sales Performance Rule with Quantity Increase Recommendations

## Hardcoded Values Identified

### Analysis Configuration (Lines 59-61)
1. **Default Analysis Level**: `ANALYSIS_LEVEL = "spu"` - SPU-level analysis by default

### Data Period Configuration (Lines 83-86)
1. **Data Period**: `DATA_PERIOD_DAYS = 15` - API data is for half month (15 days)
2. **Target Period**: `TARGET_PERIOD_DAYS = 15` - Recommendations for same period
3. **Scaling Factor**: `SCALING_FACTOR = TARGET_PERIOD_DAYS / DATA_PERIOD_DAYS` - 1.0 for same period

### File Paths Configuration (Lines 71-81, 90-103, 110-113)
1. **Base Data Files**:
   - `BASE_DATA_FILE = "data/api_data/store_config_2025Q2_combined.csv"` (line 71)
   - `BASE_QUANTITY_FILE = "data/api_data/complete_spu_sales_2025Q2_combined.csv"` (line 72)
2. **Seasonal Data Files**:
   - `SEASONAL_DATA_FILE = "data/api_data/store_config_2024Q3_combined.csv"` (line 74)
   - `SEASONAL_QUANTITY_FILE = "data/api_data/complete_spu_sales_2024Q3_combined.csv"` (line 75)
3. **Cluster Files**: Configured in ANALYSIS_CONFIGS dictionary (lines 91, 98)
4. **Data Files**: Configured in ANALYSIS_CONFIGS dictionary (lines 92, 99)
5. **Output Files**: Configured in ANALYSIS_CONFIGS dictionary (lines 93, 100)
6. **Output Directory**: `OUTPUT_DIR = "output"` (line 112)
7. **Results File**: Dynamically generated from ANALYSIS_CONFIGS (line 113)

### Rule Parameters (Lines 115-136)
1. **Subcategory Level**:
   - `TOP_QUARTILE_PERCENTILE = 75` (Compare against 75th percentile performers)
   - `MIN_CLUSTER_SIZE = 3` (Minimum stores in cluster)
   - `MIN_SALES_VOLUME = 1` (Minimum sales to consider)
   - `MIN_INCREASE_QUANTITY = 2.0` (Minimum units to recommend increasing)
   - `MAX_INCREASE_PERCENTAGE = 0.5` (Max 50% increase)
2. **SPU Level**:
   - `TOP_QUARTILE_PERCENTILE = 75` (Compare against 75th percentile)
   - `MIN_CLUSTER_SIZE = 3` (Minimum stores in cluster)
   - `MIN_SALES_VOLUME = 50` (Minimum sales to consider)
   - `MIN_INCREASE_QUANTITY = 0.5` (Minimum units to recommend increasing)
   - `MAX_INCREASE_PERCENTAGE = 0.5` (Max 50% increase)
3. **General Controls**:
   - `MAX_RECOMMENDATIONS_PER_STORE = 8` (Maximum recommendations per store)
   - `MAX_TOTAL_QUANTITY_PER_STORE = 80` (Maximum units total per store)
   - `MIN_OPPORTUNITY_SCORE = 0.10` (Minimum opportunity score)
   - `MIN_INVESTMENT_THRESHOLD = 50` (Minimum investment per recommendation)
   - `MIN_Z_SCORE_THRESHOLD = 1.0` (Only recommend for Z-score > 1.0)

### Performance Classification Thresholds (Lines 138-154)
1. **Subcategory Level**:
   - `top_performer: -1.0` (Z < -1.0)
   - `performing_well: 0.0` (-1.0 ≤ Z ≤ 0)
   - `some_opportunity: 1.0` (0 < Z ≤ 1.0)
   - `good_opportunity: 2.5` (1.0 < Z ≤ 2.5)
   - `major_opportunity: float('inf')` (Z > 2.5)
2. **SPU Level**:
   - `top_performer: -0.5` (Z < -0.5)
   - `performing_well: 0.5` (-0.5 ≤ Z ≤ 0.5)
   - `some_opportunity: 1.5` (0.5 < Z ≤ 1.5)
   - `good_opportunity: 2.5` (1.5 < Z ≤ 2.5)
   - `major_opportunity: float('inf')` (Z > 2.5)

### Seasonal Configuration (Lines 65-82)
1. **Current Month Detection**: `current_month = datetime.now().month` (line 65)
2. **August Special Handling**: Hardcoded August (month 8) for blended seasonal approach
3. **Seasonal Weighting**: Default weights of 0.4 recent + 0.6 seasonal in blend_seasonal_data function

## Synthetic Data Usage Assessment

### ✅ Real Data Usage
- **API Data Integration**: Uses real `base_sal_qty` and `fashion_sal_qty` from API fields
- **Real Sales Data**: Processes actual store sales data for performance analysis
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
- **Fixed Rule Parameters**: Static thresholds for sales performance analysis
- **Fixed Seasonal Months**: Hardcoded August special handling
- **Fixed Testing Mode**: Static testing mode configuration
- **Fixed Weights**: Static seasonal blending weights
- **Fallback Unit Price**: Default estimate of ¥100 when real data unavailable (line 623)
- **Subcategory Estimation**: Rough estimate of $100 per unit for subcategory analysis (line 626)

## Data Treatment Assessment

### ✅ Proper Data Handling
- **Real Quantity Data**: Uses actual `base_sal_qty` and `fashion_sal_qty` API fields
- **Real Unit Price Calculation**: Calculates realistic unit prices from API data
- **Meaningful Investment Calculations**: Uses real quantity × unit_price for investments
- **No Fake Prices**: Eliminated fake $1.00 unit prices
- **Sell-Through Validation**: Only recommends increases that improve sell-through rate
- **Cluster-Based Analysis**: Uses real cluster assignments for peer comparison
- **Seasonal Data Blending**: Combines recent trends with seasonal patterns
- **Quantity Recommendations**: Provides specific unit quantity increase recommendations
- **Performance-Based Filtering**: Uses Z-scores and performance classifications

### ⚠️ Areas for Improvement
1. **Configurable Analysis Level**: Should allow dynamic selection of analysis type
2. **Flexible File Paths**: Should support configurable input/output locations
3. **Dynamic Data Periods**: Should allow customization of analysis periods
4. **Configurable Rule Parameters**: Should allow customization of thresholds
5. **Configurable Seasonal Handling**: Should allow customization of seasonal approaches
6. **Dynamic Month Selection**: Should support different months/seasons
7. **Configurable Weights**: Should allow customization of seasonal blending weights
8. **Better Fallback Handling**: Should improve fallback unit price estimation

## Business Logic Alignment

### ✅ Aligned with Business Requirements
- **Real Data Processing**: Uses actual store sales data for all recommendations
- **Product Recommendations**: Provides specific unit quantity increase targets
- **Sell-Through Validation**: Only recommends increases that improve sell-through rate
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
