# Pipeline Steps Reference Guide

## Quick Reference Table

| Step | Script | Purpose | Time | Critical | Input | Output |
|------|--------|---------|------|----------|-------|--------|
| 1 | `step1_api_download.py` | Download store/sales data | ~15 min | ✅ | Period spec | 4 CSV files |
| 2 | `step2_coordinate_extraction.py` | Extract coordinates | ~1 min | ✅ | Store config | Coordinates CSV |
| 3 | `step3_matrix_preparation.py` | Create matrices | <1 min | ✅ | Sales data | 12 matrix files |
| 4 | `step4_weather_data_download.py` | Weather data | <1 min | ❌ | Coordinates | Weather files |
| 5 | `step5_feels_like_temperature.py` | Temperature calc | ~14 min | ❌ | Weather data | Temperature CSV |
| 6 | `step6_cluster_analysis.py` | Store clustering | <1 min | ✅ | Matrices + temp | Cluster assignments |
| 7 | `step7_missing_category_rule.py` | Missing categories | ~1 min | ❌ | Clusters + sales | Rule 7 results |
| 8 | `step8_imbalanced_rule.py` | Imbalanced SPUs | ~2 min | ❌ | Clusters + config | Rule 8 results |
| 9 | `step9_below_minimum_rule.py` | Below minimum | ~1 min | ❌ | Clusters + config | Rule 9 results |
| 10 | `step10_smart_overcapacity_rule.py` | Overcapacity | <1 min | ❌ | Clusters + config | Rule 10 results |
| 11 | `step11_missed_sales_opportunity_rule.py` | Missed sales | ~14 min | ❌ | Clusters + config | Rule 11 results |
| 12 | `step12_sales_performance_rule.py` | Performance | ~22 min | ❌ | Clusters + config | Rule 12 results |
| 13 | `step13_consolidate_rules.py` | Consolidation | <1 min | ❌ | All rule results | Consolidated CSV |
| 14 | `step14_global_overview_dashboard.py` | Overview dash | <1 min | ❌ | Consolidated + details | HTML dashboard |
| 15 | `step15_interactive_map_dashboard.py` | Map dashboard | <1 min | ❌ | Consolidated + coords | HTML map |

## Phase 1: Data Collection & Processing

### Step 1: API Data Download
- **Script**: `src/step1_api_download.py`
- **Purpose**: Downloads store configuration and sales data from API
- **Criticality**: Critical (pipeline stops if fails)
- **Typical Time**: ~15 minutes
- **Success Rate**: 97% (2,271/2,336 stores)

**Input**: 
- Period specification (e.g., 202506A for June 2025 first half)

**Output**:
- `store_config_202506A.csv` - Store configurations and metadata
- `store_sales_202506A.csv` - Raw store sales data  
- `complete_category_sales_202506A.csv` - Category-level aggregated sales
- `complete_spu_sales_202506A.csv` - SPU-level detailed sales

**Key Features**:
- Robust error handling with automatic retry logic
- Progress tracking with tqdm for real-time updates
- Automatic data validation and quality checks
- Memory-optimized processing for large datasets

**Common Issues**:
- API timeouts: Automatic retry handles temporary failures
- Network connectivity: Ensure stable internet connection
- Authentication: Verify API credentials if required

### Step 2: Coordinate Extraction  
- **Script**: `src/step2_coordinate_extraction.py`
- **Purpose**: Extracts geographic coordinates from store addresses
- **Criticality**: Critical (needed for clustering and visualization)
- **Typical Time**: ~1 minute
- **Success Rate**: 100% (2,265 stores)

**Input**:
- Store configuration data from Step 1

**Output**:
- `store_coordinates_extended.csv` - Store locations with coordinates

**Key Features**:
- Address parsing and coordinate extraction
- Data quality validation and geographic anomaly detection
- Backup coordinate sources for reliability

**Common Issues**:
- Address parsing: Handles various address formats
- Missing coordinates: Uses fallback methods

### Step 3: Matrix Preparation
- **Script**: `src/step3_matrix_preparation.py` 
- **Purpose**: Creates clustering matrices for analysis
- **Criticality**: Critical (required for clustering)
- **Typical Time**: ~6 seconds
- **Success Rate**: 100%

**Input**:
- Category and SPU sales data from Step 1

**Output**:
- Subcategory matrix (2,271 stores × 113 subcategories)
- SPU matrix (2,262 stores × 1,000 top SPUs)  
- Category-aggregated matrix (2,262 stores × 24 categories)
- 12 total matrix files (original + normalized versions)

**Key Features**:
- Memory-optimized matrix creation
- Automatic filtering by prevalence and sales volume
- Normalized and original matrix versions
- Multiple analysis levels supported

**Common Issues**:
- Memory usage: Large matrices require sufficient RAM
- Data sparsity: Automatic filtering handles sparse data

## Phase 2: Weather Integration

### Step 4: Weather Data Download
- **Script**: `src/step4_weather_data_download.py`
- **Purpose**: Downloads historical weather data for store locations  
- **Criticality**: Optional (enhances clustering but not required)
- **Typical Time**: <1 minute (uses existing data when available)
- **Success Rate**: 100%

**Input**:
- Store coordinates from Step 2

**Output**:
- Weather data files for each store location
- Altitude data for enhanced weather calculations

**Key Features**:
- Efficient data reuse (avoids re-downloading existing data)
- Multiple weather parameters (temperature, humidity, wind, etc.)
- Data validation and quality checks

### Step 5: Feels-like Temperature Calculation
- **Script**: `src/step5_feels_like_temperature.py`
- **Purpose**: Calculates feels-like temperatures and creates temperature bands
- **Criticality**: Optional (enhances clustering analysis)
- **Typical Time**: ~14 minutes for 1.7M weather records
- **Success Rate**: 100%

**Input**:
- Weather data files from Step 4

**Output**:
- `stores_with_feels_like_temperature.csv` - Store temperature data
- `temperature_bands.csv` - Temperature band summary

**Key Features**:
- Wind chill, heat index, and Steadman formula calculations
- 7 temperature bands (3.8°C to 32.4°C range)
- Data quality validation and outlier detection

**Temperature Bands Created**:
- 0°C to 5°C: 4 stores
- 5°C to 10°C: 66 stores  
- 10°C to 15°C: 355 stores
- 15°C to 20°C: 909 stores
- 20°C to 25°C: 628 stores
- 25°C to 30°C: 329 stores
- 30°C to 35°C: 2 stores

## Phase 3: Clustering Analysis

### Step 6: Cluster Analysis
- **Script**: `src/step6_cluster_analysis.py`
- **Purpose**: Creates temperature-aware clusters for similar stores
- **Criticality**: Critical (required for business rules)
- **Typical Time**: ~3 seconds
- **Success Rate**: 100%

**Input**:
- Normalized matrices from Step 3
- Temperature data from Step 5

**Output**:
- `clustering_results.csv` - Main cluster assignments
- `cluster_profiles_subcategory.csv` - Cluster characteristics
- Visualization and documentation files

**Key Features**:
- Temperature-aware clustering within 5°C bands
- Balanced cluster sizes (~50 stores per cluster)
- Multiple clustering metrics and validation
- 44 clusters created across 7 temperature bands

**Clustering Results**:
- Total stores clustered: 2,263
- Clusters created: 44 across temperature bands
- Cluster size range: 47-75 stores per cluster
- Clustering metrics: Silhouette, Calinski-Harabasz, Davies-Bouldin scores

## Phase 4: Business Rules Analysis

### Step 7: Missing Category Rule
- **Script**: `src/step7_missing_category_rule.py`
- **Purpose**: Identifies missing subcategory opportunities
- **Analysis Level**: Subcategory
- **Criticality**: Optional (business rule analysis)
- **Typical Time**: ~36 seconds
- **Success Rate**: 100%

**Input**:
- Cluster assignments from Step 6
- Subcategory sales data

**Output**:
- `rule7_missing_category_results.csv` - Store-level results
- `rule7_missing_subcategory_opportunities.csv` - Detailed opportunities

**Results**:
- Stores flagged: 1,611
- Opportunities identified: 3,878
- Threshold: ≥70% adoption, ≥100 sales within cluster

**Top Missing Subcategories**:
- 弯刀裤: 344 stores
- 内衣: 300 stores
- 家饰: 279 stores
- 喇叭裤: 269 stores
- 潮鞋: 256 stores

### Step 8: Imbalanced Rule
- **Script**: `src/step8_imbalanced_rule.py`
- **Purpose**: Detects imbalanced SPU allocations using Z-score analysis
- **Analysis Level**: SPU
- **Criticality**: Optional (business rule analysis)
- **Typical Time**: ~112 seconds  
- **Success Rate**: 100%

**Input**:
- Cluster assignments from Step 6
- SPU planning data (store configuration)

**Output**:
- `rule8_imbalanced_results.csv` - Store-level results
- `rule8_imbalanced_spu_cases.csv` - Detailed imbalanced cases
- `rule8_imbalanced_spu_z_score_analysis.csv` - Statistical analysis

**Results**:
- Stores flagged: 2,254
- Imbalanced SPUs: 43,170
- Threshold: Z-score > |2.0|
- Severity breakdown: MODERATE (22,811), HIGH (11,160), EXTREME (9,199)

### Step 9: Below Minimum Rule
- **Script**: `src/step9_below_minimum_rule.py`
- **Purpose**: Identifies subcategories below minimum thresholds
- **Analysis Level**: Subcategory
- **Criticality**: Optional (business rule analysis)
- **Typical Time**: ~22 seconds
- **Success Rate**: 100%

**Input**:
- Cluster assignments from Step 6
- Subcategory data from store configuration

**Output**:
- `rule9_below_minimum_results.csv` - Store-level results
- `rule9_below_minimum_subcategory_cases.csv` - Detailed cases

**Results**:
- Stores flagged: 2,263 (all stores)
- Below minimum cases: 54,698
- Threshold: < 2 styles per subcategory
- Total increase needed: 27,349 styles

### Step 10: Smart Overcapacity Rule
- **Script**: `src/step10_smart_overcapacity_rule.py`
- **Purpose**: Identifies smart reallocation opportunities
- **Analysis Level**: Subcategory
- **Criticality**: Optional (business rule analysis)
- **Typical Time**: ~6 seconds
- **Success Rate**: 100%

**Input**:
- Cluster assignments from Step 6
- Subcategory data from store configuration

**Output**:
- `rule10_smart_overcapacity_results.csv` - Store-level results
- Multi-profile opportunity files (strict/standard/lenient)

**Results**:
- Stores flagged: 601
- Reallocation cases: 1,219
- Multi-profile analysis with different risk tolerances

**Key Features**:
- Three optimization profiles: Strict (Conservative), Standard (Balanced), Lenient (Aggressive)
- Performance-based reallocation recommendations

### Step 11: Missed Sales Opportunity Rule
- **Script**: `src/step11_missed_sales_opportunity_rule.py`
- **Purpose**: Identifies missed sales opportunities through peer comparison
- **Analysis Level**: SPU
- **Criticality**: Optional (business rule analysis)
- **Typical Time**: ~13.5 minutes
- **Success Rate**: 100%

**Input**:
- Cluster assignments from Step 6
- SPU sales data from store configuration

**Output**:
- `rule11_missed_sales_opportunity_results.csv` - Store-level results
- Supplementary measures for cluster analysis

**Results**:
- Stores flagged: 0 (no major issues detected)
- Threshold: < 15% sell-through rate
- Supplementary measures: Cluster relative underperformance and misjudgment analysis

### Step 12: Sales Performance Rule
- **Script**: `src/step12_sales_performance_rule.py`
- **Purpose**: Analyzes sales performance vs cluster top performers
- **Analysis Level**: SPU
- **Criticality**: Optional (business rule analysis)
- **Typical Time**: ~22 minutes
- **Success Rate**: 100%

**Input**:
- Cluster assignments from Step 6
- SPU sales data from store configuration

**Output**:
- `rule12_sales_performance_results.csv` - Store-level results
- `rule12_sales_performance_spu_details.csv` - Detailed analysis

**Results**:
- Stores with opportunities: 1,326
- Performance level classification and gap analysis

**Performance Level Distribution**:
- Top Performer: 29 stores (1.3%)
- Performing Well: 904 stores (39.9%)
- Some Opportunity: 1,313 stores (58.0%)
- Good Opportunity: 13 stores (0.6%)
- No Data: 4 stores (0.2%)

## Phase 5: Consolidation & Visualization

### Step 13: Rule Consolidation
- **Script**: `src/step13_consolidate_rules.py`
- **Purpose**: Consolidates all rule results into unified output
- **Criticality**: Optional (creates summary)
- **Typical Time**: ~0.2 seconds
- **Success Rate**: 100%

**Input**:
- All individual rule results from Steps 7-12

**Output**:
- `consolidated_rule_results.csv` - Main consolidated file (2.3MB)
- `consolidated_rule_summary.md` - Executive summary report

**Results**:
- Stores consolidated: 2,263
- Total violations: 6,104 across 6 rules
- Stores with violations: 2,263 (100%)

### Step 14: Global Overview Dashboard
- **Script**: `src/step14_global_overview_dashboard.py`
- **Purpose**: Creates executive-level HTML dashboard
- **Criticality**: Optional (visualization)
- **Typical Time**: ~1 second
- **Success Rate**: 100%

**Input**:
- Consolidated results from Step 13
- Individual rule details from Steps 7-12

**Output**:
- `global_overview_spu_dashboard.html` - Executive dashboard (11KB)

**Features**:
- Executive KPIs for 2,264 stores
- SPU-level rule violation analysis across 6 rules
- 4 interactive visualizations
- Strategic insights and recommendations
- SPU-level granular analysis

### Step 15: Interactive Map Dashboard
- **Script**: `src/step15_interactive_map_dashboard.py`
- **Purpose**: Creates geographic visualization dashboard
- **Criticality**: Optional (visualization)
- **Typical Time**: ~1 second
- **Success Rate**: 100%

**Input**:
- Consolidated results from Step 13
- Store coordinates from Step 2
- Individual rule details from Steps 7-12

**Output**:
- `interactive_map_spu_dashboard.html` - Geographic dashboard (7.1MB)

**Features**:
- Interactive map with 2,259 store locations
- Color-coded markers by violation severity (0-6 violations)
- Detailed SPU-level popups with rule-specific insights
- Rule-based filtering (8 filter options: All + Rules 7-12)
- Cluster and violation count filtering
- Geographic distribution visualization
- Real-time statistics panel with SPU-level metrics

## Error Handling & Recovery

### Critical Step Failures
If any critical step (1, 2, 3, 6) fails:
- Pipeline stops execution
- Error details logged with context
- Use `--strict` mode for detailed debugging
- Clear data with `--clear-period` and restart

### Optional Step Failures
If any optional step (4, 5, 7-15) fails:
- Pipeline continues to next step
- Warning logged but execution proceeds
- Final summary reports which steps failed
- Individual steps can be re-run separately

### Data Validation
Use `--validate-data` flag to enable:
- File existence checks after each step
- Data size and content validation
- Progress tracking and quality reporting
- Early detection of data issues

### Common Recovery Patterns
1. **Memory Issues**: Ensure 32GB+ RAM, close other applications
2. **Network Issues**: Check internet connection, retry failed steps
3. **File Permissions**: Ensure write access to data/ and output/ directories
4. **Corrupted Data**: Use `--clear-period` to reset and restart

## Performance Optimization

### Memory Management
- Use efficient data types (int16, int32) where appropriate
- Chunked processing for large datasets
- Memory profiling and debugging capabilities
- Optimized matrix operations

### Processing Speed
- Parallel processing where possible
- Vectorized operations for data analysis
- Efficient algorithms for clustering and rule analysis
- Progress tracking with time estimation

### Storage Optimization
- Compressed file formats where appropriate
- Efficient data serialization
- Temporary file cleanup
- Organized output structure

---

*This reference guide provides detailed information for each pipeline step. For complete documentation, see COMPLETE_PIPELINE_DOCUMENTATION.md* 