# Comprehensive Data Validation System

This directory contains a complete, modular validation system for the Product Mix Clustering pipeline using Pandera. All validation components are organized in a single, comprehensive structure with no redundancy.

## Directory Structure

```
tests/validation_comprehensive/
├── __init__.py              # Package initialization and exports
├── schemas.py               # Main schemas module (imports from schemas/)
├── schemas/                 # Modular schema package
│   ├── __init__.py         # Schema package initialization
│   ├── common_schemas.py   # Common reusable schemas
│   ├── time_schemas.py     # Time-related schemas
│   ├── weather_schemas.py  # Comprehensive weather schemas
│   └── product_schemas.py  # Product and sales schemas
├── validators.py            # Validation utility functions and quality checks
├── runners.py               # Validation runners for different steps
├── main.py                  # Main validation runner script
└── README.md               # This documentation
```

## Key Features

### 🔄 **Comprehensive Design**
- **All Schemas**: Common and step-specific schemas in one place
- **Quality Checks**: Advanced data quality validation beyond basic schema validation
- **Flexible Runners**: Support for single periods, multiple periods, and comprehensive validation
- **No Redundancy**: Single source of truth for all validation logic

### 🎯 **Modularity**
- **Reusable Components**: Common schemas can be imported and used across steps
- **Consistent Interface**: Standardized validation patterns across all pipeline steps
- **Easy Extension**: Simple to add new validation rules and quality checks

### 🛠️ **Maintainability**
- **Centralized Logic**: All validation code in one organized structure
- **Clear Separation**: Schemas, validators, and runners are clearly separated
- **Comprehensive Documentation**: Detailed documentation for all components

## Components

### 1. Schemas (Modular Structure)

#### Common Schemas (`schemas/common_schemas.py`)
- **StoreCodeSchema**: Store identification (5-digit codes)
- **GeographicSchema**: Coordinates and altitude validation
- **SalesAmountSchema**: Sales amounts (allows negative for returns)
- **QuantitySchema**: Quantities with reasonable bounds
- **PriceSchema**: Prices (always positive)
- **CountSchema**: Count fields (non-negative)
- **CategoricalSchema**: Chinese seasons, gender, month types

#### Time Schemas (`schemas/time_schemas.py`)
- **TimeSeriesSchema**: Time-related fields (year, month)
- **PeriodSchema**: Period validation with enhanced constraints
- **DateRangeSchema**: Date range validation

#### Weather Schemas (`schemas/weather_schemas.py`)
- **WeatherDataSchema**: Individual store weather data (comprehensive)
- **WeatherMetricsSchema**: Core weather measurements
- **TemperatureSchema**: Temperature validation with extreme ranges
- **PrecipitationSchema**: Precipitation with comprehensive ranges
- **WindSchema**: Wind speed and direction validation
- **HumiditySchema**: Humidity and dew point validation
- **PressureSchema**: Atmospheric pressure validation
- **RadiationSchema**: Solar radiation metrics
- **VisibilitySchema**: Visibility validation
- **WeatherExtremesSchema**: Weather extremes based on 2024-2025 research
- **StoreAltitudeSchema**: Store altitude data

#### Step 5 Schemas (`schemas/weather_schemas.py`)
- **FeelsLikeTemperatureSchema**: Feels-like temperature calculation output
- **TemperatureBandsSchema**: Temperature bands summary output
- **FeelsLikeCalculationSchema**: Comprehensive feels-like temperature validation

#### Step 2 Schemas (`schemas/weather_schemas.py`)
- **StoreCoordinatesSchema**: Store coordinate extraction output
- **SPUStoreMappingSchema**: SPU-store mapping data
- **SPUMetadataSchema**: SPU metadata and statistics

#### Step 2B Schemas (`schemas/weather_schemas.py`)
- **SeasonalStoreProfilesSchema**: Seasonal store performance profiles
- **SeasonalCategoryPatternsSchema**: Category seasonal patterns
- **SeasonalClusteringFeaturesSchema**: Seasonal clustering features

#### Step 3 Schemas (`schemas/weather_schemas.py`)
- **StoreMatrixSchema**: Base store-product matrix validation
- **SubcategoryMatrixSchema**: Subcategory matrix validation
- **SPUMatrixSchema**: SPU matrix validation
- **CategoryAggregatedMatrixSchema**: Category-aggregated matrix validation

#### Step 6 Schemas (`schemas/weather_schemas.py`)
- **ClusteringResultsSchema**: Clustering results validation
- **ClusterProfilesSchema**: Cluster profile validation
- **PerClusterMetricsSchema**: Per-cluster quality metrics validation

#### Product Schemas (`schemas/product_schemas.py`)
- **StoreConfigSchema**: Store configuration data
- **CategorySalesSchema**: Category-level sales data
- **SPUSalesSchema**: SPU-level sales data
- **ProductClassificationSchema**: Product classification validation
- **SalesSummarySchema**: Sales summary with enhanced validation
- **InventorySchema**: Inventory data validation

### 2. Validators (`validators.py`)

#### Core Validation Functions
- **validate_dataframe()**: Validate DataFrames with detailed results
- **validate_file()**: Validate CSV files
- **validate_multiple_files()**: Batch validation
- **get_validation_summary()**: Generate summary statistics
- **safe_validate()**: Graceful error handling

#### Quality Check Functions
- **validate_with_quality_checks()**: Schema validation + quality checks
- **validate_time_series_continuity()**: Time series analysis
- **validate_coordinate_consistency()**: Geographic data analysis
- **validate_sales_consistency()**: Cross-dataset consistency checks

### 3. Runners (`runners.py`)

#### Step 1 Runners
- **validate_step1_period()**: Validate single period
- **validate_multiple_periods()**: Validate multiple periods
- **run_step1_validation()**: Flexible Step 1 validation

#### Step 4 Runners
- **validate_weather_files()**: Validate weather data files
- **validate_weather_by_period()**: Validate specific period
- **validate_store_altitudes()**: Validate altitude data
- **run_step4_validation()**: Flexible Step 4 validation

#### Step 5 Runners
- **validate_step5_feels_like_temperature()**: Validate feels-like temperature output
- **validate_feels_like_calculation_quality()**: Validate calculation quality and consistency
- **run_step5_validation()**: Flexible Step 5 validation with quality checks

#### Comprehensive Runner
- **run_comprehensive_validation()**: Full pipeline validation

### 4. Main Runner (`main.py`)

Unified command-line interface for all validation operations.

## Usage Examples

### Command Line Usage

```bash
# Validate specific step
python tests/validation_comprehensive/main.py --step 1 --period 202401

# Validate multiple periods
python tests/validation_comprehensive/main.py --step 1 --periods 202401 202402 202405

# Run comprehensive validation
python tests/validation_comprehensive/main.py --comprehensive

# Validate weather data
python tests/validation_comprehensive/main.py --step 4 --sample-size 10

# Validate specific weather period
python tests/validation_comprehensive/main.py --step 4 --weather-period 202408

# Validate feels-like temperature calculation
python tests/validation_comprehensive/main.py --step 5

# Validate feels-like temperature without quality checks
python tests/validation_comprehensive/main.py --step 5 --no-include-quality
```

### Programmatic Usage

```python
from validation_comprehensive import (
    validate_step1_period,
    validate_weather_files,
    run_comprehensive_validation,
    StoreConfigSchema,
    validate_file
)

# Validate single period
result = validate_step1_period('202401')

# Validate weather data
weather_result = validate_weather_files(sample_size=5)

# Validate feels-like temperature calculation
feels_like_result = run_step5_validation(include_quality=True)

# Run comprehensive validation
comprehensive_result = run_comprehensive_validation()

# Use schemas directly
from validation_comprehensive.schemas import StoreConfigSchema
from validation_comprehensive.validators import validate_file

result = validate_file("data/store_config.csv", StoreConfigSchema)
```

### Advanced Usage with Quality Checks

```python
from validation_comprehensive.validators import validate_with_quality_checks
from validation_comprehensive.schemas import WeatherDataSchema
import pandas as pd

# Load data
df = pd.read_csv("weather_data.csv")

# Validate with quality checks
result = validate_with_quality_checks(df, WeatherDataSchema, "weather_data")

# Access quality check results
if result['status'] == 'valid':
    quality_checks = result['quality_checks']
    print(f"Missing data: {quality_checks['missing_data']['total_missing_pct']:.1f}%")
    print(f"Duplicates: {quality_checks['duplicates']['duplicate_rows']}")
```

## Validation Rules

### Business Rules
- **Year Range**: 2010-2040
- **Month Range**: 1-12
- **Store Codes**: 5-digit integers (10000-99999)
- **Coordinates**: Latitude (-90 to +90), Longitude (-180 to +180)
- **Altitude**: 0 to 9000m (Mount Everest height)
- **Prices**: Always positive
- **Quantities**: Allow returns (-50 to +450 for SPU, -50 to +1000 for category)

### Weather Validation Rules (Based on 2024-2025 Research)
- **Temperature**: -50°C to +60°C (extreme conditions)
- **Precipitation**: 0 to 500mm (extreme daily precipitation)
- **Wind Speed**: 0 to 100 m/s (hurricane force winds)
- **Humidity**: 0 to 100% (relative humidity)
- **Pressure**: 800 to 1100 hPa (extreme pressure systems)
- **Solar Radiation**: 0 to 1500 W/m² (maximum solar radiation)
- **Terrestrial Radiation**: 0 to 1500 W/m² (based on actual data observations)

### Step 5 Validation Rules (Feels-Like Temperature)
- **Feels-Like Temperature**: -60°C to +70°C (extreme conditions)
- **Min/Max Feels-Like**: -80°C to +80°C (extreme ranges)
- **Elevation**: 0 to 9000m (Mount Everest height)
- **Condition Hours**: Non-negative integers
- **Temperature Bands**: Format "X°C to Y°C" (5-degree bands)
- **Quality Checks**: Temperature consistency, condition hours validation, elevation checks

### Categorical Values
- **Seasons**: 春, 夏, 秋, 冬, 四季
- **Gender**: 男, 女, 中
- **Month Types**: 1A, 1B, 2A, 2B, ..., 12A, 12B

### Quality Checks
- **Missing Data**: Percentage of missing values per column
- **Duplicates**: Number and percentage of duplicate rows
- **Time Series**: Continuity analysis for weather data
- **Coordinates**: Consistency checks for geographic data
- **Sales Consistency**: Cross-validation between category and SPU data

## Migration from Previous Systems

### From Simple Validation Scripts
1. **Replace imports**: Use `validation_comprehensive` instead of individual scripts
2. **Update function calls**: Use the new runner functions
3. **Add quality checks**: Leverage the enhanced validation capabilities

### From Modular Validation
1. **Consolidate imports**: All schemas and utilities in one package
2. **Use comprehensive runners**: Leverage the enhanced runner functions
3. **Add quality checks**: Use the new quality check functions

## Best Practices

### 1. Use Comprehensive Runners
```python
# Good: Use comprehensive runners
from validation_comprehensive import run_step1_validation
result = run_step1_validation(period='202401')

# Avoid: Manual validation setup
# (Complex manual setup code)
```

### 2. Leverage Quality Checks
```python
# Good: Use quality checks
from validation_comprehensive.validators import validate_with_quality_checks
result = validate_with_quality_checks(df, schema, "data")

# Avoid: Basic validation only
# result = schema.validate(df)
```

### 3. Use Appropriate Validation Levels
```python
# For development: Comprehensive validation
run_comprehensive_validation()

# For production: Specific period validation
validate_step1_period('202401')

# For testing: Sample validation
validate_weather_files(sample_size=3)
```

### 4. Handle Results Properly
```python
result = validate_step1_period('202401')

if result['success_rate'] == 100.0:
    print("✅ All validations passed")
else:
    print(f"❌ {result['success_rate']:.1f}% success rate")
    # Handle failures appropriately
```

## Error Handling

The system provides comprehensive error handling:

- **File Not Found**: Graceful handling of missing files
- **Schema Errors**: Detailed error messages with failure cases
- **Data Quality Issues**: Quality check results with specific metrics
- **Validation Failures**: Clear reporting of what failed and why

## Performance Considerations

- **Sampling**: Weather data validation uses sampling for performance
- **Batch Processing**: Multiple files validated efficiently
- **Memory Management**: Large datasets handled appropriately
- **Logging**: Comprehensive logging for debugging and monitoring

## Extending the System

### Adding New Schemas
1. Add to `schemas.py` in appropriate section
2. Update `__init__.py` exports
3. Document in this README

### Adding New Quality Checks
1. Add function to `validators.py`
2. Integrate with `validate_with_quality_checks()`
3. Document usage and purpose

### Adding New Runners
1. Add function to `runners.py`
2. Update `main.py` command-line interface
3. Document usage examples

## Testing

The comprehensive validation system is tested using:

```bash
# Test specific components
python tests/validation_comprehensive/main.py --step 1 --period 202401
python tests/validation_comprehensive/main.py --step 4 --sample-size 3

# Test comprehensive validation
python tests/validation_comprehensive/main.py --comprehensive

# Test with verbose output
python tests/validation_comprehensive/main.py --step 1 --period 202401 --verbose
```

## Support

For issues or questions:
1. Check the comprehensive logging output
2. Review the quality check results
3. Examine the validation summary statistics
4. Use verbose mode for detailed debugging information

This comprehensive validation system provides a complete, maintainable, and extensible solution for all pipeline data validation needs.
