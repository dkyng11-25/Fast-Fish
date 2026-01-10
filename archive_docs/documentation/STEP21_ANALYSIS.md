# Step 21 Analysis: D-F Label/Tag Recommendation Sheet

## Hardcoded Values Identified

### Configuration Parameters (Lines 35-37)
1. **Minimum Cluster Size**: `MIN_CLUSTER_SIZE = 5` (line 35)
2. **Target SPUs Per Cluster**: `TARGET_SPUS_PER_CLUSTER = 20` (line 36)
3. **Rationale Threshold**: `RATIONALE_THRESHOLD = 0.30` (line 37)

### File Paths Configuration (Lines 137-142, 170-172, 222-225, 514-515)
1. **Cluster Files**: Multiple fixed paths including `"output/clustering_results_spu.csv"`, `"data/store_cluster_assignments.csv"` (lines 137-142)
2. **SPU Files**: `"output/corrected_detailed_spu_recommendations_*.csv"`, `"output/consolidated_spu_rule_results.csv"` (lines 170-172)
3. **Store Files**: Multiple fixed paths including `"data/api_data/store_config_2025Q2_combined.csv"` (lines 222-225)
4. **Excel Output File**: `f"output/D_F_Label_Tag_Recommendation_Sheet_{timestamp}.xlsx"` (line 514)
5. **CSV Output File**: `f"output/client_desired_store_group_style_tags_targets_{timestamp}.csv"` (line 515)

### Output Directory (Multiple Lines)
1. **Fixed Output Directory**: `"output/"` (used in multiple file paths)

### Translation Dictionary (Lines 40-125)
1. **TAG_TRANSLATIONS**: Extensive hardcoded bilingual translation dictionary with 85+ entries

### Normalization Values (Lines 329, 335, 359, 363)
1. **SPU Diversity Normalization**: `10` (line 329)
2. **Quantity Change Normalization**: `10` (line 335)
3. **Daily Quantity Caps**: `3.0` (growth) and `2.0` (optimization) (lines 359, 363)
4. **Period Days**: `15` (growth) and `30` (optimization) (lines 358, 362)

### Rationale Score Weights (Lines 338-339)
1. **Store Coverage Weight**: `0.4` (40%) (line 338)
2. **SPU Diversity Weight**: `0.3` (30%) (line 338)
3. **Investment Score Weight**: `0.2` (20%) (line 339)
4. **Quantity Score Weight**: `0.1` (10%) (line 339)

### Threshold Calculations (Lines 313-315)
1. **Investment Percentile**: `0.80` (80th percentile) (line 313)
2. **Minimum Investment Threshold**: `1000` (¥1k) (line 314)
3. **Maximum Investment Threshold**: `20000` (¥20k) (line 315)

### Constraint Thresholds (Lines 375, 387, 391)
1. **Store Coverage Threshold**: `0.5` (50%) (line 375)
2. **Large Reduction Threshold**: `-5` units (line 387)
3. **Large Increase Threshold**: `5` units (line 389)
4. **Minimal Impact Threshold**: `1` unit (line 391)

### SPU Diversity Constraint (Line 383)
1. **Low Diversity Threshold**: `3` SPUs (line 383)

## Synthetic Data Usage Assessment

### ⚠️ Potential Synthetic Data Issues
- **Dummy Cluster Data**: Creates dummy cluster data with random assignments when files not found (lines 158-161)
- **Minimal Store Data**: Creates minimal store data when files not found (lines 239-241)
- **Fixed File Paths**: Static input/output file locations
- **Fixed Output Directory**: Static output directory location
- **Fixed Configuration Values**: Static thresholds and parameters
- **Fixed Translation Dictionary**: Static bilingual translations
- **Fixed Normalization Values**: Static normalization parameters
- **Fixed Weights**: Static rationale score weights
- **Fixed Period Days**: Static time period calculations

### ✅ Real Data Usage
- **API Data Integration**: Uses actual SPU recommendation data from previous steps
- **Real Cluster Assignments**: Uses actual cluster assignment data
- **Real Store Metadata**: Uses actual store configuration data
- **Real Business Rules**: Applies actual pipeline recommendations
- **Real Translation Logic**: Uses actual bilingual translation mappings
- **Real Rationale Scoring**: Calculates scores based on actual data metrics
- **Real Constraint Analysis**: Applies constraints based on actual data characteristics

## Data Treatment Assessment

### ✅ Proper Data Handling
- **Real Data Integration**: Uses actual pipeline outputs and store data
- **Bilingual Translation**: Provides proper Chinese/English translations
- **Rationale Scoring**: Calculates meaningful scores based on real data
- **Constraint Analysis**: Applies realistic business constraints
- **Target Quantity Calculation**: Derives quantities from actual pipeline recommendations
- **Comprehensive Reporting**: Generates detailed Excel/CSV outputs
- **Validation**: Includes output validation mechanisms

### ⚠️ Areas for Improvement
1. **Configurable Dummy Data**: Should provide better error handling instead of dummy data
2. **Flexible File Paths**: Should allow customization of input/output locations
3. **Configurable Parameters**: Should support configurable thresholds and weights
4. **Enhanced Documentation**: Should document all configuration parameters
5. **Configurable Output Directory**: Should allow customization of output locations
6. **Regional Adaptation**: Should support different configurations for different regions

## Business Logic Alignment

### ✅ Aligned with Business Requirements
- **Real Data Processing**: Uses actual pipeline outputs and recommendations
- **Bilingual Delivery**: Provides proper Chinese/English formatted output
- **No Placeholder Data**: No synthetic or placeholder data in normal operation
- **Business Scoring**: Applies meaningful rationale scoring system
- **Constraint Awareness**: Considers realistic business constraints
- **Target Quantities**: Derives actionable target quantities
- **Excel Compliance**: Generates Fast Fish template-compliant output

### ⚠️ Configuration Limitations
- **Static Parameters**: Fixed configuration values may not suit all business needs
- **Fixed File Paths**: Static locations may not work in all environments
- **Static Weights**: Fixed rationale score weights may not be optimal
- **Fixed Translation Dictionary**: Static translations may not cover all cases
- **Static Period Days**: Fixed time periods for quantity calculations
- **Dummy Data Fallback**: Creates synthetic data when real data missing

## Recommendations

1. **Environment Variable Support**: Move hardcoded values to configuration/environment variables
2. **Flexible File Paths**: Allow customization of input/output locations
3. **Configurable Parameters**: Allow customization of thresholds, weights, and normalization values
4. **Enhanced Documentation**: Document all configuration parameters and their business impact
5. **Configurable Output Directory**: Allow customization of output locations
6. **Regional Adaptation**: Support different configurations for different regions
7. **Improved Error Handling**: Replace dummy data creation with proper error handling
8. **Dynamic Translation**: Support external translation dictionaries
9. **Configurable Time Periods**: Allow customization of calculation periods
