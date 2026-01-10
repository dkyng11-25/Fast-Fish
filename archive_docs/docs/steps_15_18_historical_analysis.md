# Steps 15-18: Enhanced Historical Analysis Workflow with Store Group Cluster Trending

## Overview
This enhanced workflow creates comprehensive business intelligence for Fast Fish recommendations by combining:
1. **Historical reference baselines** (comparing current 202506B with historical 202407A data)
2. **Store group aggregated trending analysis** (real store cluster intelligence from step 13 pipeline)

## Enhanced Business Value

### 🎯 What's New
- **Store group cluster trending analysis**: Aggregated 10-dimension trend analysis across real stores within each store group
- **Real store data aggregation**: Analysis of actual individual stores (not synthetic data)
- **Business priority scoring**: Cluster-level data-driven priority assessment for each recommendation
- **Enhanced rationale**: Rich contextual explanations combining historical baselines with cluster trends
- **Confidence scoring**: Cluster-level reliability metrics for recommendation quality assessment

### 📊 Output Enhancement
- **Original**: 12 columns with basic recommendations
- **Enhanced**: 30 columns with historical context + store group cluster trending analysis
- **Business-friendly language**: Actionable insights with cluster-level confidence metrics

## Data Flow

### Input Data
- `data/api_data/complete_spu_sales_202407A.csv` - Historical SPU sales (July 2024 H1)
- `data/api_data/complete_spu_sales_202506B.csv` - Current SPU sales (June 2025 H2)
- `output/fast_fish_spu_count_recommendations_20250702_124006.csv` - Current Fast Fish recommendations
- **NEW**: Real individual store analysis within each store group for trending

### Processing Steps

#### Step 15: Download Historical Baseline
**Script:** `src/step15_download_historical_baseline.py`
**Purpose:** Analyze historical 202407A data and create baseline SPU counts by Store Group × Sub-Category
**Outputs:**
- `output/historical_reference_202407A_YYYYMMDD_HHMMSS.csv`
- `output/historical_insights_202407A_YYYYMMDD_HHMMSS.json`
- `output/year_over_year_comparison_YYYYMMDD_HHMMSS.csv`

#### Step 16: Create Comparison Tables
**Script:** `src/step16_create_comparison_tables.py`
**Purpose:** Generate Excel-compatible comparison tables between historical and current data
**Outputs:**
- `output/spreadsheet_comparison_analysis_YYYYMMDD_HHMMSS.xlsx`

#### Step 17: **ENHANCED** Store Group Cluster Augmentation
**Script:** `src/step17_augment_recommendations.py` ⭐ **ENHANCED**
**Purpose:** Add historical reference + store group aggregated 10-dimension trending analysis
**NEW Features:**
- **Real Store Analysis**: Analyzes actual individual stores within each store group
- **Aggregated Sales Performance**: Sales trends aggregated across store cluster
- **Aggregated Weather Impact**: Climate correlation with store group performance
- **Store Group Cluster Performance**: Peer group comparative analysis within clusters
- **Aggregated Price Point Strategy**: Market positioning insights by store group
- **Aggregated Category Performance**: Category-specific market intelligence by cluster
- **Regional Market Analysis**: Geographic performance context by store group
- **Cluster Business Priority Scoring**: Data-driven recommendation prioritization
- **Cluster Confidence Metrics**: Reliability assessment based on store group analysis

**Outputs:**
- `output/fast_fish_with_historical_and_cluster_trending_analysis_YYYYMMDD_HHMMSS.csv` ⭐ **ENHANCED**

#### Step 18: Validate Results
**Script:** `src/step18_validate_results.py`
**Purpose:** Comprehensive sanity check of enhanced augmented data
**Outputs:** Console validation report

### Enhanced Output Columns

#### Historical Reference Columns (Existing)
- `Historical_SPU_Quantity_202407A` - July 2024 baseline SPU count
- `Historical_Total_Sales_202407A` - July 2024 sales performance
- `Historical_Store_Count_202407A` - Historical store participation
- `SPU_Change_vs_Historical` - Absolute change vs historical
- `SPU_Change_vs_Historical_Pct` - Percentage change vs historical

#### **NEW** Store Group Cluster Trending Columns
- `cluster_trend_summary` - Business-friendly summary of store group trends
- `cluster_trend_score` / `cluster_trend_confidence` - Overall cluster trend assessment (0-100)
- `stores_analyzed` / `dominant_trend` - Analysis scope and trend classification
- `cluster_sales_score` / `cluster_weather_score` / `cluster_cluster_score` - Individual dimension scores
- `cluster_category_score` / `cluster_regional_score` - Category and regional trend scores
- `cluster_business_priority` / `cluster_data_quality` - Business priority and data quality metrics

#### Enhanced Rationale
- `Enhanced_Rationale` - Rich contextual explanation combining historical + store group cluster insights

## Usage

### Quick Start
```bash
# Run complete enhanced workflow
./run_steps_15_18_historical_analysis.sh
```

### Step-by-Step Execution
```bash
# Step 15: Create historical baseline
python src/step15_download_historical_baseline.py

# Step 16: Create comparison tables (optional)
python src/step16_create_comparison_tables.py

# Step 17: ⭐ ENHANCED store group cluster augmentation
python src/step17_augment_recommendations.py

# Step 18: Validate enhanced results
python src/step18_validate_results.py
```

## Key Metrics & Business Impact

### Historical Context
- Historical period: 202407A (July 2024 H1)
- Current period: 202506B (June 2025 H2)
- Match rate: ~83% of current recommendations have historical baselines

### **NEW** Store Group Cluster Intelligence
- **20 store groups** analyzed with real individual store data
- **20,000+ individual stores** analyzed across all groups
- **10 trend dimensions** analyzed per store group
- **Cluster-level business priority scoring** for strategic decision making
- **Store group confidence assessment** for risk management
- **Real data aggregation** eliminates synthetic data weaknesses

### Enhanced Business Value
- ✅ **Year-over-year context** for growth assessment
- ✅ **Store group cluster trend awareness** for strategic timing
- ✅ **Real store data analysis** across entire store groups
- ✅ **Risk assessment** through cluster confidence scoring
- ✅ **Priority guidance** for resource allocation at store group level
- ✅ **Rich contextual rationale** for stakeholder communication
- ✅ **Data-driven decision support** with comprehensive store group intelligence

## Output Example

### Before (Original Fast Fish)
```
Store Group 1 | T恤 | 休闲圆领T恤: Expand from 252 to 255 SPUs
```

### After (Enhanced with Historical + Store Group Cluster Trending)
```
Store Group 1 | T恤 | 休闲圆领T恤: Expand from 252 to 255 SPUs
HISTORICAL: Historical baseline: 195 SPUs (July 2024). Expanding by 60 SPUs (+30.8%)
CLUSTER TRENDS: 📊 MODERATE CLUSTER TREND (Score: 41, 10 stores) | 📈 Moderate Sales Performance (avg: 66) | ☀️ Favorable Weather Conditions (avg: 75) | 📊 Average Cluster Performance (avg: 51)
Cluster Trend Score: 41/100 | Business Priority: 45/100 | Confidence: 90/100
```

## Technical Integration

The enhanced Step 3 integrates with the main pipeline's `ComprehensiveTrendAnalyzer` from `src/step13_consolidate_spu_rules.py`, but now:

1. **Identifies real stores** within each store group using the same grouping logic
2. **Analyzes individual stores** within each group using Andy's full trending system
3. **Aggregates results** across the store group for meaningful cluster insights
4. **Provides business-friendly summaries** suitable for Fast Fish strategic decisions

**Key Improvements**:
- Real store data instead of synthetic store codes
- Meaningful confidence scores based on actual store sample sizes
- Business intelligence at the appropriate aggregation level for Fast Fish decisions
- Eliminates "weak trend support" issues from synthetic data

**Dependencies**: Enhanced functionality requires the main pipeline's trending analysis components to be available.

## **🆕 TARGET_STYLE_TAGS CLIENT FORMAT FIX**

**Issue**: Client complained that `Target_Style_Tags` only included 2 fields (category | subcategory) instead of the required 5 fields.

**Solution**: Step 3 now automatically enhances `Target_Style_Tags` format using store configuration data:

**Before**: `"T恤 | 休闲圆领T恤"`
**After**: `"T恤 | 休闲圆领T恤 | 店铺前区 | 夏季 | 女装"`

**Enhancement Details**:
- Loads store configuration data with all 5 required fields
- Creates mapping from old 2-field format to new 5-field format
- Applies enhancement automatically during Step 3 processing
- Maintains backward compatibility for unmapped entries
- Provides detailed enhancement statistics

**Required Fields**:
1. `big_class_name` (e.g., "Casual Pants")
2. `sub_cate_name` (e.g., "Cargo Pants") 
3. `display_location_name` (e.g., "Back-of-store")
4. `season_name` (e.g., "Summer")
5. `sex_name` (e.g., "Women")

**Format**: `"big_class_name | sub_cate_name | display_location_name | season_name | sex_name"`
