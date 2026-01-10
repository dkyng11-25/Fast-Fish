# Product Mix Clustering & Rule Analysis Pipeline - Complete Documentation

## Overview

This pipeline provides a comprehensive solution for retail product mix optimization through clustering analysis and business rule validation. The system processes store sales data, applies weather-aware clustering, and identifies optimization opportunities through 6 business rules.

## Pipeline Architecture

### 15-Step Pipeline Structure

The pipeline is organized into 4 main phases:

1. **Data Collection & Processing (Steps 1-3)**: API data download, coordinate extraction, matrix preparation
2. **Weather Integration (Steps 4-5)**: Weather data collection and feels-like temperature calculation
3. **Clustering Analysis (Step 6)**: Temperature-aware clustering with balanced cluster sizes
4. **Business Rules Analysis (Steps 7-12)**: Six business rules for optimization opportunities
5. **Consolidation & Visualization (Steps 13-15)**: Rule consolidation and dashboard generation

### System Requirements

- **Memory**: 32GB to 64GB RAM recommended
- **Python**: 3.12+ with required dependencies
- **Storage**: ~2GB for data files per period
- **Processing Time**: 60-90 minutes for complete pipeline

## Step-by-Step Documentation

### Phase 1: Data Collection & Processing

#### Step 1: API Data Download
- **Script**: `src/step1_api_download.py`
- **Purpose**: Downloads store configuration and sales data from API
- **Input**: Period specification (e.g., 202506A for June 2025 first half)
- **Output**: 
  - `store_config_202506A.csv` (store configurations)
  - `store_sales_202506A.csv` (store sales data)
  - `complete_category_sales_202506A.csv` (category-level sales)
  - `complete_spu_sales_202506A.csv` (SPU-level sales)
- **Performance**: ~15 minutes, 97% success rate (2,271/2,336 stores)
- **Key Features**:
  - Robust error handling and retry logic
  - Progress tracking with tqdm
  - Automatic data validation

#### Step 2: Coordinate Extraction
- **Script**: `src/step2_coordinate_extraction.py`
- **Purpose**: Extracts geographic coordinates from store addresses
- **Input**: Store configuration data
- **Output**: `store_coordinates_extended.csv` with coordinates
- **Performance**: ~1 minute for 2,265 stores
- **Key Features**:
  - Address parsing and coordinate extraction
  - Data quality validation
  - Geographic anomaly detection

#### Step 3: Matrix Preparation
- **Script**: `src/step3_matrix_preparation.py`
- **Purpose**: Creates clustering matrices for analysis
- **Input**: Category and SPU sales data
- **Output**:
  - Subcategory matrix (2,271 stores × 113 subcategories)
  - SPU matrix (2,262 stores × 1,000 top SPUs)
  - Category-aggregated matrix (2,262 stores × 24 categories)
- **Performance**: ~6 seconds
- **Key Features**:
  - Memory-optimized matrix creation
  - Automatic filtering by prevalence and sales volume
  - Normalized and original matrices

### Phase 2: Weather Integration

#### Step 4: Weather Data Download
- **Script**: `src/step4_weather_data_download.py`
- **Purpose**: Downloads historical weather data for store locations
- **Input**: Store coordinates
- **Output**: Weather data files for each store
- **Performance**: Uses existing data when available
- **Key Features**:
  - Efficient data reuse
  - Multiple weather parameters
  - Data validation and quality checks

#### Step 5: Feels-like Temperature Calculation
- **Script**: `src/step5_feels_like_temperature.py`
- **Purpose**: Calculates feels-like temperatures and creates temperature bands
- **Input**: Weather data files
- **Output**: 
  - `stores_with_feels_like_temperature.csv`
  - `temperature_bands.csv`
- **Performance**: ~14 minutes for 1.7M weather records
- **Key Features**:
  - Wind chill, heat index, and Steadman calculations
  - 7 temperature bands (3.8°C to 32.4°C range)
  - Data quality validation

### Phase 3: Clustering Analysis

#### Step 6: Cluster Analysis
- **Script**: `src/step6_cluster_analysis.py`
- **Purpose**: Creates temperature-aware clusters for similar stores
- **Input**: Normalized matrices and temperature data
- **Output**: 
  - `clustering_results.csv` (main results)
  - `cluster_profiles_subcategory.csv`
  - Visualization and documentation files
- **Performance**: ~3 seconds for 44 clusters
- **Key Features**:
  - Temperature-aware clustering within 5°C bands
  - Balanced cluster sizes (~50 stores per cluster)
  - Multiple clustering metrics and validation

### Phase 4: Business Rules Analysis

#### Step 7: Missing Category Rule
- **Script**: `src/step7_missing_category_rule.py`
- **Purpose**: Identifies missing subcategory opportunities
- **Analysis Level**: Subcategory
- **Input**: Cluster assignments and subcategory sales data
- **Output**: 
  - `rule7_missing_category_results.csv`
  - `rule7_missing_subcategory_opportunities.csv`
- **Results**: 1,611 stores flagged, 3,878 opportunities
- **Performance**: ~36 seconds
- **Threshold**: ≥70% adoption, ≥100 sales

#### Step 8: Imbalanced Rule
- **Script**: `src/step8_imbalanced_rule.py`
- **Purpose**: Detects imbalanced SPU allocations using Z-score analysis
- **Analysis Level**: SPU
- **Input**: Cluster assignments and SPU planning data
- **Output**: 
  - `rule8_imbalanced_results.csv`
  - `rule8_imbalanced_spu_cases.csv`
  - `rule8_imbalanced_spu_z_score_analysis.csv`
- **Results**: 2,254 stores flagged, 43,170 imbalanced SPUs
- **Performance**: ~112 seconds
- **Threshold**: Z-score > |2.0|

#### Step 9: Below Minimum Rule
- **Script**: `src/step9_below_minimum_rule.py`
- **Purpose**: Identifies subcategories below minimum thresholds
- **Analysis Level**: Subcategory
- **Input**: Cluster assignments and subcategory data
- **Output**: 
  - `rule9_below_minimum_results.csv`
  - `rule9_below_minimum_subcategory_cases.csv`
- **Results**: 2,263 stores flagged, 54,698 cases
- **Performance**: ~22 seconds
- **Threshold**: < 2 styles per subcategory

#### Step 10: Smart Overcapacity Rule
- **Script**: `src/step10_smart_overcapacity_rule.py`
- **Purpose**: Identifies smart reallocation opportunities
- **Analysis Level**: Subcategory
- **Input**: Cluster assignments and subcategory data
- **Output**: 
  - `rule10_smart_overcapacity_results.csv`
  - Multi-profile opportunity files (strict/standard/lenient)
- **Results**: 601 stores flagged, 1,219 cases
- **Performance**: ~6 seconds
- **Key Features**: Multi-profile analysis with different risk tolerances

#### Step 11: Missed Sales Opportunity Rule
- **Script**: `src/step11_missed_sales_opportunity_rule.py`
- **Purpose**: Identifies missed sales opportunities through peer comparison
- **Analysis Level**: SPU
- **Input**: Cluster assignments and SPU sales data
- **Output**: 
  - `rule11_missed_sales_opportunity_results.csv`
  - Supplementary measures for cluster analysis
- **Results**: 0 stores flagged (no major issues detected)
- **Performance**: ~13.5 minutes
- **Threshold**: < 15% sell-through rate

#### Step 12: Sales Performance Rule
- **Script**: `src/step12_sales_performance_rule.py`
- **Purpose**: Analyzes sales performance vs cluster top performers
- **Analysis Level**: SPU
- **Input**: Cluster assignments and SPU sales data
- **Output**: 
  - `rule12_sales_performance_results.csv`
  - `rule12_sales_performance_spu_details.csv`
- **Results**: 1,326 stores with opportunities
- **Performance**: ~22 minutes
- **Key Features**: Performance level classification and gap analysis

### Phase 5: Consolidation & Visualization

#### Step 13: Rule Consolidation
- **Script**: `src/step13_consolidate_rules.py`
- **Purpose**: Consolidates all rule results into unified output
- **Input**: All individual rule results
- **Output**: 
  - `consolidated_rule_results.csv` (main consolidated file)
  - `consolidated_rule_summary.md` (executive summary)
- **Results**: 2,263 stores with 6,104 total violations
- **Performance**: ~0.2 seconds

#### Step 14: Global Overview Dashboard
- **Script**: `src/step14_global_overview_dashboard.py`
- **Purpose**: Creates executive-level HTML dashboard
- **Input**: Consolidated results and rule details
- **Output**: `global_overview_spu_dashboard.html`
- **Performance**: ~1 second
- **Features**:
  - Executive KPIs for 2,264 stores
  - 4 interactive visualizations
  - Strategic insights and recommendations
  - SPU-level granular analysis

#### Step 15: Interactive Map Dashboard
- **Script**: `src/step15_interactive_map_dashboard.py`
- **Purpose**: Creates geographic visualization dashboard
- **Input**: Consolidated results, coordinates, and rule details
- **Output**: `interactive_map_spu_dashboard.html`
- **Performance**: ~1 second
- **Features**:
  - Interactive map with 2,259 store locations
  - Color-coded markers by violation severity
  - Rule-based filtering (8 filter options)
  - Real-time statistics panel
  - Geographic distribution visualization

## Pipeline Execution

### Command-Line Interface

The pipeline is executed through a single `pipeline.py` script with comprehensive options:

```bash
# Complete pipeline execution
python pipeline.py --month 202506 --period A --validate-data

# Step control execution
python pipeline.py --month 202506 --period A --start-step 7 --end-step 12

# List available options
python pipeline.py --list-steps
python pipeline.py --list-periods
```

### Key Parameters

- `--month YYYYMM`: Target month (e.g., 202506 for June 2025)
- `--period {A,B,full}`: Period within month (A=first half, B=second half, full=entire month)
- `--start-step N`: Start from specific step (1-15)
- `--end-step N`: End at specific step (1-15)
- `--strict`: Stop on any error (vs continue on non-critical failures)
- `--validate-data`: Enable data validation after each step
- `--clear-all` or `--clear-period`: Clear previous data before execution

### Step Control System

Steps are categorized by criticality:
- **Critical Steps (1,2,3,6)**: Data Collection, Processing, Clustering - pipeline stops if these fail
- **Optional Steps (4,5,7-15)**: Weather, Business Rules, Visualization - pipeline continues if these fail

### Error Handling

- **Strict Mode**: Stops on any error for debugging
- **Normal Mode**: Continues on non-critical failures for production
- **Enhanced Logging**: Timestamps, progress tracking, and context
- **Data Validation**: File existence, size, and content quality checks

## Performance Metrics

### Recent Execution Results (June 2025 First Half - 202506A)

| Step | Component | Time | Records Processed | Success Rate |
|------|-----------|------|------------------|--------------|
| 1 | API Download | 14.6 min | 2,271/2,336 stores | 97% |
| 2 | Coordinates | 1.0 min | 2,265 stores | 100% |
| 3 | Matrix Prep | 0.1 min | 113 subcategories, 1,000 SPUs | 100% |
| 4 | Weather Data | 0.0 min | 2,293 stores (existing) | 100% |
| 5 | Temperature | 14.0 min | 1,705,992 records | 100% |
| 6 | Clustering | 0.1 min | 44 clusters, 2,263 stores | 100% |
| 7 | Missing Cat. | 0.6 min | 1,611 stores flagged | 100% |
| 8 | Imbalanced | 1.9 min | 2,254 stores flagged | 100% |
| 9 | Below Min. | 0.4 min | 2,263 stores flagged | 100% |
| 10 | Overcapacity | 0.1 min | 601 stores flagged | 100% |
| 11 | Missed Sales | 13.5 min | 0 stores flagged | 100% |
| 12 | Performance | 22.1 min | 1,326 stores flagged | 100% |
| 13 | Consolidation | 0.0 min | 6,104 violations | 100% |
| 14 | Overview Dash | 0.0 min | 2,264 stores | 100% |
| 15 | Map Dashboard | 0.0 min | 2,259 stores | 100% |
| **Total** | **Complete Pipeline** | **65.2 min** | **2,263 stores** | **100%** |

## Output Files Structure

### Main Result Files
```
output/
├── consolidated_rule_results.csv          # Main consolidated results (2.3MB)
├── consolidated_rule_summary.md           # Executive summary
├── clustering_results.csv                 # Store cluster assignments (19KB)
├── global_overview_spu_dashboard.html     # Executive dashboard (11KB)
└── interactive_map_spu_dashboard.html     # Geographic dashboard (7.1MB)
```

### Individual Rule Results
```
output/
├── rule7_missing_category_results.csv     # Missing categories
├── rule8_imbalanced_results.csv          # Imbalanced allocations
├── rule9_below_minimum_results.csv       # Below minimum thresholds
├── rule10_smart_overcapacity_results.csv # Smart overcapacity
├── rule11_missed_sales_opportunity_results.csv # Missed opportunities
└── rule12_sales_performance_results.csv  # Sales performance
```

### Supporting Data Files
```
data/
├── store_subcategory_matrix.csv          # Original subcategory matrix (1.4MB)
├── normalized_subcategory_matrix.csv     # Normalized subcategory matrix (2.6MB)
├── store_spu_limited_matrix.csv          # SPU matrix (9.5MB)
├── normalized_spu_limited_matrix.csv     # Normalized SPU matrix (15.9MB)
├── stores_with_feels_like_temperature.csv # Temperature data
└── temperature_bands.csv                 # Temperature band summary
```

## Business Rules Summary

| Rule | Name | Analysis Level | Purpose | Threshold | Typical Results |
|------|------|---------------|---------|-----------|-----------------|
| 7 | Missing Categories | Subcategory | Find missing subcategory opportunities | ≥70% adoption, ≥100 sales | 1,611 stores, 3,878 opportunities |
| 8 | Imbalanced Allocation | SPU | Detect over/under-allocated SPUs | Z-score > \|2.0\| | 2,254 stores, 43,170 cases |
| 9 | Below Minimum | Subcategory | Find subcategories below thresholds | < 2 styles | All stores, 54,698 cases |
| 10 | Smart Overcapacity | Subcategory | Identify reallocation opportunities | Performance-based | 601 stores, 1,219 cases |
| 11 | Missed Sales | SPU | Detect low-performing SPUs | < 15% sell-through | 0 stores (no issues) |
| 12 | Sales Performance | SPU | Analyze vs top performers | Gap analysis | 1,326 stores with opportunities |

## Configuration Management

The pipeline uses `config.py` for centralized configuration:

- **Period Management**: Automatic period calculation and labeling
- **File Path Generation**: Dynamic path generation based on periods
- **Backward Compatibility**: Support for legacy file naming
- **Environment Variables**: Flexible configuration options

## Data Quality & Validation

### Validation Features
- File existence and size checks
- Content quality validation
- Progress tracking and logging
- Error detection and reporting

### Memory Optimization
- Efficient data structures (int16, int32 for appropriate data)
- Chunked processing for large datasets
- Memory profiling and debugging
- Optimized matrix operations

## Troubleshooting

### Common Issues
1. **Memory Issues**: Ensure 32GB+ RAM, use chunked processing
2. **API Timeouts**: Automatic retry logic handles temporary failures
3. **Missing Dependencies**: Install requirements from requirements.txt
4. **File Permissions**: Ensure write access to data/ and output/ directories

### Debug Mode
Use `--strict` mode for detailed error reporting and step-by-step debugging.

## Future Enhancements

### Planned Features
- Additional business rules for specific retail scenarios
- Real-time API integration for live data processing
- Advanced visualization with drill-down capabilities
- Machine learning models for predictive analysis

### Scalability Improvements
- Distributed processing for large datasets
- Cloud deployment capabilities
- API endpoint for external integration
- Automated scheduling and monitoring

## Version History

- **v2.0** (Current): Complete 15-step pipeline with comprehensive documentation
- **v1.5**: Enhanced error handling and step control system
- **v1.0**: Initial consolidated pipeline implementation

## Contact & Support

For technical support or feature requests, refer to the project documentation or contact the development team. 