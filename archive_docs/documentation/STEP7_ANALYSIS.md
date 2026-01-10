# Step 7 Analysis: Missing Category/SPU Rule with Quantity Recommendations

## Implementation Update (2025-08-10)

The Step 7 script (`src/step7_missing_category_rule.py`) has been refactored to align with pipeline standards and business needs:

- Dynamic period handling via `src.config` (`initialize_pipeline_config()`, `get_current_period()`, `get_period_label()`, `get_api_data_files()`, `get_output_files()`).
- CLI entrypoint with explicit flags: `--yyyymm`, `--period A|B|full`, `--analysis-level spu|subcategory`, optional seasonal blending flags.
- Real quantities and prices using API actuals (`base_sal_qty`, `fashion_sal_qty`, `base_sal_amt`, `fashion_sal_amt`) in `load_quantity_data()`; `avg_unit_price` derived per store.
- Fast Fish sell-through validator integrated (`src.sell_through_validator`). If historical baseline is missing, validator still enforces “only improvements”.
- Cluster-aware analysis with robust fallbacks for clustering/sales sources; prefers period-labeled files.
- Period-labeled outputs for results, opportunities, and summary markdown saved to `output/`.
- Backward-compatible non-period file is only written for subcategory runs (can be removed if not needed): `output/rule7_missing_category_results.csv`.
 - Target period labeling supported via `--target-yyyymm` and `--target-period` (e.g., generate September outputs using August data).

CLI examples (Forecasting September using August actuals):

```bash
# September A output labeled from August A actuals
python3 -m src.step7_missing_category_rule \
  --yyyymm 202508 --period A --analysis-level spu \
  --target-yyyymm 202509 --target-period A

# September B output labeled from August B actuals
python3 -m src.step7_missing_category_rule \
  --yyyymm 202508 --period B --analysis-level spu \
  --target-yyyymm 202509 --target-period B
```

Optional seasonal blending:

```bash
python3 -m src.step7_missing_category_rule \
  --yyyymm 202508 --period B --analysis-level spu \
  --target-yyyymm 202509 --target-period B \
  --seasonal-blending --seasonal-yyyymm 202409 --seasonal-period B --seasonal-weight 0.6
```

Integration Run Summary (202508A/B, SPU):

- Stores analyzed: 2,268
- Stores flagged: 899
- Opportunities: 1,674
- Total quantity: 15,666 units / 15 days
- Total investment: ~$1,045,803
- Validator executed; no historical baseline found in this run (improvement shown as +100pp for approved adds)

Operational notes:

- Inputs and outputs are resolved dynamically per period; outputs suffixed with `<YYYYMMP>`.
- Quantity/pricing derived from actual API amounts/quantities; conservative fallbacks remain for rare gaps.
- Seasonal blending is optional and controlled via CLI flags.

## Hardcoded Values Identified (legacy notes)

### Analysis Configuration
1. **Default Analysis Level**: `ANALYSIS_LEVEL = "spu"` (line 60) - SPU-level analysis
2. **Alternative Option**: Commented option for "subcategory" analysis

### Data Period Configuration (Lines 63-66)
1. **Data Period**: `DATA_PERIOD_DAYS = 15` - API data is for half month (15 days)
2. **Target Period**: `TARGET_PERIOD_DAYS = 15` - Recommendations for same period
3. **Scaling Factor**: `SCALING_FACTOR = TARGET_PERIOD_DAYS / DATA_PERIOD_DAYS` - 1.0 for same period

### File Paths Configuration (Lines 83, 134-150, 193, 230-233)
1. **Base Path**: `base_path = "../data/api_data/"` (line 83)
2. **Cluster Files**: 
   - `"cluster_file": "output/clustering_results_subcategory.csv"` (line 136)
   - `"cluster_file": "output/clustering_results_spu.csv"` (line 144)
3. **Output Files**: 
   - `"output_prefix": "rule7_missing_subcategory"` (line 141)
   - `"output_prefix": "rule7_missing_spu"` (line 149)
4. **Quantity Data**: `quantity_file = 'data/api_data/store_sales_data.csv'` (line 193)
5. **SPU Sales Files**: Multiple hardcoded paths (lines 230-233)

### Rule Parameters (Lines 161-170)
1. **Subcategory Level**:
   - `MIN_CLUSTER_STORES_SELLING = 0.7` (70% of stores)
   - `MIN_CLUSTER_SALES_THRESHOLD = 100`
   - `MIN_OPPORTUNITY_VALUE = 50`
2. **SPU Level**:
   - `MIN_CLUSTER_STORES_SELLING = 0.80` (80% of stores)
   - `MIN_CLUSTER_SALES_THRESHOLD = 1500`
   - `MIN_OPPORTUNITY_VALUE = 500`
   - `MAX_MISSING_SPUS_PER_STORE = 5`

### Output Configuration
1. **Output Directory**: `OUTPUT_DIR = "output"` (line 158)
2. **Results File**: Dynamic based on analysis level (line 159)

### Price Calculation Configuration (Lines 256-260, 488)
1. **Price Clipping**: `np.clip(category_prices['spu_sales'] / 2.0, 50, 800)` (lines 257-259)
2. **Default Price**: `store_unit_price = 50` (line 488) - Conservative default
3. **Default Price Fallback**: `300` (line 259) - Default price

### Date Configuration
1. **Current Month**: `current_month: int = 8` (line 68) - Defaults to August

## Synthetic Data Usage Assessment

### ✅ Real Data Usage
- **API Data Integration**: Uses real `base_sal_qty` and `fashion_sal_qty` from API fields
- **Real Sales Data**: Processes actual store sales data for recommendations
- **Real Unit Prices**: Calculates actual unit prices from API data ($20-$150 range)
- **Real Investment Calculations**: Uses real quantity × unit_price for investment calculations
- **Real Cluster Data**: Uses actual clustering results from step 6
- **Real Sell-Through Validation**: Integrates with Fast Fish sell-through validator

### ⚠️ Potential Synthetic Data Issues
- **Hardcoded Analysis Level**: Fixed to SPU-level analysis by default
- **Fixed File Paths**: Static input/output file locations
- **Fixed Data Periods**: Static 15-day period configuration
- **Fixed Rule Parameters**: Static thresholds for cluster analysis
- **Fixed Price Defaults**: Conservative default prices when real data unavailable
- **Fixed Month**: Hardcoded August as current month

## Data Treatment Assessment

### ✅ Proper Data Handling
- **Real Quantity Data**: Uses actual `base_sal_qty` and `fashion_sal_qty` API fields
- **Real Unit Price Calculation**: Calculates realistic unit prices from API data
- **Meaningful Investment Calculations**: Uses real quantity × unit_price for investments
- **No Fake Prices**: Eliminated fake $1.00 unit prices
- **Sell-Through Validation**: Only recommends additions that improve sell-through rate
- **Cluster-Based Analysis**: Uses real cluster assignments for peer comparison
- **Seasonal Data Blending**: Combines recent trends with seasonal patterns

### ⚠️ Areas for Improvement
1. **Configurable Analysis Level**: Should allow dynamic selection of analysis type
2. **Flexible File Paths**: Should support configurable input/output locations
3. **Dynamic Data Periods**: Should allow customization of analysis periods
4. **Configurable Rule Parameters**: Should allow customization of thresholds
5. **Configurable Default Prices**: Should allow customization of fallback prices
6. **Dynamic Month Selection**: Should support different months/seasons

## Business Logic Alignment

### ✅ Aligned with Business Requirements
- **Real Data Processing**: Uses actual store sales data for all recommendations
- **Product Recommendations**: Provides specific unit quantity targets for missing products
- **Sell-Through Validation**: Only recommends additions that improve sell-through rate
- **No Placeholder Data**: No synthetic or placeholder data detected in core processing
- **Investment Planning**: Provides realistic investment calculations
- **Cluster-Based Analysis**: Uses peer store analysis for appropriate recommendations
- **Seasonal Awareness**: Incorporates seasonal patterns with recent trends

### ⚠️ Configuration Limitations
- **Fixed Analysis Level**: Hardcoded to SPU-level analysis may not suit all scenarios
- **Static Rule Parameters**: Fixed thresholds may not be optimal for all datasets
- **Fixed Data Periods**: Static periods may not work for different analysis windows
- **Regional Limitations**: Hardcoded configuration may not work for different regions
- **Limited Flexibility**: Fixed settings may limit adaptability to different business needs

## Recommendations

1. **Configurable Analysis Selection**: Allow dynamic selection of analysis level via parameters
2. **Environment Variable Support**: Move hardcoded values to configuration/environment variables
3. **Flexible Data Periods**: Allow customization of analysis periods
4. **Dynamic Rule Parameters**: Support configurable thresholds and parameters
5. **Configurable Default Prices**: Allow customization of fallback price values
6. **Dynamic Month Support**: Support different months/seasons for analysis
7. **Regional Adaptation**: Support different configurations for different regions
8. **Flexible File Paths**: Allow customization of input/output locations
