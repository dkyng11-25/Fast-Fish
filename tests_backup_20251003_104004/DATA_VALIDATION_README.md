# Data Validation System for SPU Clustering Pipeline

This document provides a comprehensive guide to the data validation system in the `/tests/` directory. The validation system uses **Pandera** for robust data validation and ensures data integrity across all pipeline steps.

## 🎯 **Overview**

The validation system provides:
- **Schema-based validation** using Pandera for all data tables
- **Quality checks** beyond basic schema validation
- **EDA (Exploratory Data Analysis)** for data distribution insights
- **Comprehensive testing** across multiple time periods
- **Business rule validation** for domain-specific constraints

## 📁 **Directory Structure**

```
tests/
├── validation_comprehensive/          # Main validation framework
│   ├── schemas/                      # Pandera schemas for all data types
│   │   ├── common_schemas.py         # Reusable schemas (store codes, coordinates, etc.)
│   │   ├── weather_schemas.py        # Weather data validation
│   │   ├── product_schemas.py        # Product and sales data validation
│   │   ├── step7_schemas.py          # Step 7 business rules validation
│   │   ├── step8_schemas.py          # Step 8 imbalanced SPU rules
│   │   ├── step9_schemas.py          # Step 9 below minimum rules
│   │   └── ...                       # Step-specific schemas
│   ├── runners/                      # Validation runners for each step
│   │   ├── step1_runner.py           # Data download validation
│   │   ├── step2_runner.py           # Coordinate extraction validation
│   │   ├── step3_runner.py           # Matrix preparation validation
│   │   ├── step4_runner.py           # Weather data validation
│   │   ├── step5_runner.py           # Feels-like temperature validation
│   │   ├── step6_runner.py           # Clustering analysis validation
│   │   ├── step7_runner.py           # Missing category rule validation
│   │   ├── step8_runner.py           # Imbalanced SPU rule validation
│   │   ├── step9_runner.py           # Below minimum rule validation
│   │   ├── step10_runner.py          # SPU assortment optimization validation
│   │   ├── step11_runner.py          # Missed sales opportunity validation
│   │   ├── step12_runner.py          # Sales performance rule validation
│   │   ├── step13_runner.py          # Rule consolidation validation
│   │   ├── step14_runner.py          # Fast Fish format validation
│   │   └── steps_15_36_runner.py     # Advanced steps validation
│   ├── eda/                          # Exploratory Data Analysis
│   │   ├── step1_analyzer.py         # EDA for data download
│   │   ├── step2_analyzer.py         # EDA for coordinate extraction
│   │   ├── step3_analyzer.py         # EDA for matrix preparation
│   │   ├── step4_analyzer.py         # EDA for weather data
│   │   ├── step5_analyzer.py         # EDA for feels-like temperature
│   │   └── step6_analyzer.py         # EDA for clustering analysis
│   ├── main.py                       # Main validation runner
│   └── README.md                     # Detailed technical documentation
├── run_comprehensive_validation.py   # Comprehensive validation script
├── run_simple_validation.py          # Simple validation script
├── unified_test_runner.py            # Unified test runner
├── simple_test_runner.py             # Basic functionality tests
└── .venv/                           # Virtual environment
```

## 🚀 **Quick Start**

### **1. Basic Validation**

```bash
# Validate all steps for a specific period
cd /home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/run_comprehensive_validation.py --period 202508A

# Validate specific step
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step 7 --period 202508A
```

### **2. Advanced Validation**

```bash
# Run comprehensive validation with EDA
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step comprehensive --period 202508A

# Run advanced steps validation (15-36)
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step advanced --period 202508A

# Run EDA analysis
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step eda
```

## 📊 **Types of Data Validation**

### **1. Schema Validation (Pandera)**

**Purpose**: Ensures data structure, types, and basic constraints are met.

**Examples**:
```python
# Store codes must be 5-digit integers (10000-99999)
str_code: Series[int] = pa.Field(ge=10000, le=99999)

# Coordinates must be within Earth bounds
latitude: Series[float] = pa.Field(ge=-90, le=90)
longitude: Series[float] = pa.Field(ge=-180, le=180)

# Sales quantities allow returns (-50 to +450 for SPU)
quantity: Series[int] = pa.Field(ge=-50, le=450)

# Prices must be positive
price: Series[float] = pa.Field(gt=0)
```

### **2. Business Rule Validation**

**Purpose**: Validates domain-specific business logic and constraints.

**Examples**:
- **Step 7**: Missing category/SPU sellthrough rules
- **Step 8**: Imbalanced SPU distribution rules  
- **Step 9**: Below minimum SPU count rules
- **Step 10**: SPU assortment optimization rules
- **Step 11**: Missed sales opportunity rules
- **Step 12**: Sales performance rules

### **3. Quality Checks**

**Purpose**: Validates data quality beyond basic schema constraints.

**Examples**:
```python
# Missing data percentage
missing_data_pct = (df.isnull().sum() / len(df)) * 100

# Duplicate rows
duplicate_rows = df.duplicated().sum()

# Time series continuity
time_gaps = check_time_series_continuity(df, 'date_column')

# Coordinate consistency
coordinate_consistency = validate_coordinate_consistency(df)
```

### **4. EDA (Exploratory Data Analysis)**

**Purpose**: Provides insights into data distribution and patterns.

**Examples**:
- **Numerical data**: Histograms, box plots, summary statistics
- **Categorical data**: Frequency tables, bar charts
- **Time series**: Trend analysis, seasonality patterns
- **Geographic data**: Coordinate distribution, altitude analysis

## 🔧 **Validation Schemas**

### **Common Schemas**

| Schema | Purpose | Key Fields | Constraints |
|--------|---------|------------|-------------|
| `StoreCodeSchema` | Store identification | `str_code` | 5-digit integer (10000-99999) |
| `GeographicSchema` | Coordinates | `latitude`, `longitude`, `altitude` | Earth bounds, altitude 0-9000m |
| `SalesAmountSchema` | Sales amounts | `amount` | Allows negative (returns) |
| `QuantitySchema` | Quantities | `quantity` | -50 to +450 (SPU), -50 to +1000 (category) |
| `PriceSchema` | Prices | `price` | Always positive |
| `CountSchema` | Count fields | `count` | Non-negative integers |

### **Weather Schemas**

| Schema | Purpose | Key Fields | Constraints |
|--------|---------|------------|-------------|
| `WeatherDataSchema` | Individual store weather | `temperature`, `humidity`, `pressure` | Temperature -50°C to +60°C |
| `TemperatureSchema` | Temperature validation | `temp`, `feels_like` | -50°C to +60°C, feels-like -60°C to +70°C |
| `PrecipitationSchema` | Precipitation data | `precipitation` | 0 to 500mm (extreme daily) |
| `WindSchema` | Wind data | `wind_speed`, `wind_direction` | 0 to 100 m/s (hurricane force) |
| `HumiditySchema` | Humidity data | `humidity`, `dew_point` | 0 to 100% relative humidity |

### **Product Schemas**

| Schema | Purpose | Key Fields | Constraints |
|--------|---------|------------|-------------|
| `StoreConfigSchema` | Store configuration | `store_code`, `latitude`, `longitude` | Store codes, coordinates |
| `CategorySalesSchema` | Category sales | `category`, `sales_amount`, `quantity` | Category names, sales data |
| `SPUSalesSchema` | SPU sales | `spu_code`, `sales_amount`, `quantity` | SPU codes, sales data |
| `ProductClassificationSchema` | Product classification | `category`, `subcategory`, `spu` | Hierarchical product structure |

### **Step-Specific Schemas**

| Step | Schema | Purpose | Key Fields |
|------|--------|---------|------------|
| 7 | `Step7InputSchema` | Missing category rule inputs | `clustering`, `store_config`, `category_sales` |
| 7 | `Step7ResultsSchema` | Missing category rule outputs | `missing_categories`, `recommendations` |
| 8 | `Step8InputSchema` | Imbalanced SPU rule inputs | `clustering`, `spu_sales`, `store_config` |
| 8 | `Step8ResultsSchema` | Imbalanced SPU rule outputs | `imbalanced_spus`, `recommendations` |
| 9 | `Step9InputSchema` | Below minimum rule inputs | `clustering`, `store_config`, `quantity` |
| 9 | `Step9ResultsSchema` | Below minimum rule outputs | `below_minimum_spus`, `recommendations` |

## 🎯 **Validation Commands**

### **Step-by-Step Validation**

```bash
# Step 1: Data Download
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step 1 --period 202508A

# Step 2: Coordinate Extraction
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step 2

# Step 3: Matrix Preparation
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step 3

# Step 4: Weather Data
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step 4 --sample-size 5

# Step 5: Feels-Like Temperature
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step 5

# Step 6: Clustering Analysis
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step 6

# Steps 7-14: Business Rules
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step 7 --period 202508A
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step 8 --period 202508A
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step 9 --period 202508A
# ... and so on for steps 10-14

# Steps 15-36: Advanced Steps
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step 15 --period 202508A
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step 16 --period 202508A
# ... and so on for steps 17-36
```

### **Comprehensive Validation**

```bash
# All steps (1-14)
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/run_comprehensive_validation.py --period 202508A

# All steps (1-36) with comprehensive analysis
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step comprehensive --period 202508A

# Advanced steps only (15-36)
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step advanced --period 202508A
```

### **EDA Analysis**

```bash
# Run EDA for all steps
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step eda

# EDA results are saved to: tests/output/eda_reports/
```

## 📈 **Validation Results**

### **Success Metrics**

- **Schema Validation**: Pass/Fail for each data table
- **Quality Checks**: Percentage of missing data, duplicates, etc.
- **Business Rules**: Pass/Fail for each business rule
- **Overall Success Rate**: Percentage of validations passed

### **Example Output**

```json
{
  "step": "7",
  "period": "202508A",
  "validation_passed": true,
  "success_rate": 100.0,
  "schema_validation": {
    "clustering": "passed",
    "store_config": "passed",
    "category_sales": "passed"
  },
  "quality_checks": {
    "missing_data": 0.5,
    "duplicates": 0,
    "data_consistency": "passed"
  },
  "business_rules": {
    "missing_category_rule": "passed",
    "recommendations_generated": 15
  }
}
```

## 🔍 **Data Quality Standards**

### **Missing Data Tolerance**
- **Critical fields**: 0% missing allowed
- **Optional fields**: <5% missing acceptable
- **Weather data**: <10% missing acceptable (due to API limitations)

### **Data Consistency**
- **Store codes**: Must be consistent across all datasets
- **Coordinates**: Must be within Earth bounds
- **Time periods**: Must be valid YYYYMM format
- **Sales data**: Must be consistent between category and SPU levels

### **Business Rule Compliance**
- **Step 7**: Missing categories must be identified and flagged
- **Step 8**: Imbalanced SPUs must be detected and corrected
- **Step 9**: Below minimum SPUs must be identified and addressed
- **Steps 10-12**: Optimization rules must be applied correctly

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **Module Import Errors**
   ```bash
   # Solution: Set PYTHONPATH
   export PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy
   ```

2. **Missing Dependencies**
   ```bash
   # Solution: Install missing packages
   uv add pandera numpy pandas matplotlib scikit-learn
   ```

3. **File Not Found Errors**
   ```bash
   # Solution: Ensure data is downloaded first
   uv run python src/step1_download_api_data.py --month 202508 --period A
   ```

4. **Schema Validation Failures**
   ```bash
   # Solution: Check data quality and fix issues
   # Use verbose mode for detailed error messages
   --verbose
   ```

### **Debug Mode**

```bash
# Enable verbose logging for detailed debugging
PYTHONPATH=/home/andyk/value/ProducMixClustering_spu_clustering_rules_visualization-copy uv run python tests/validation_comprehensive/main.py --step 7 --period 202508A --verbose
```

## 📚 **Advanced Usage**

### **Custom Validation**

```python
from validation_comprehensive.schemas import StoreConfigSchema
from validation_comprehensive.validators import validate_with_quality_checks
import pandas as pd

# Load your data
df = pd.read_csv("your_data.csv")

# Validate with custom quality checks
result = validate_with_quality_checks(df, StoreConfigSchema, "custom_data")

# Check results
if result['status'] == 'valid':
    print("✅ Validation passed")
else:
    print(f"❌ Validation failed: {result['errors']}")
```

### **Batch Validation**

```python
from validation_comprehensive.runners import run_step1_validation

# Validate multiple periods
periods = ["202508A", "202508B", "202507A", "202507B"]
for period in periods:
    result = run_step1_validation(period=period)
    print(f"Period {period}: {result['success_rate']:.1f}% success")
```

## 🎯 **Best Practices**

1. **Always validate data before processing**
2. **Use appropriate validation levels for your use case**
3. **Check quality metrics, not just schema validation**
4. **Run EDA analysis to understand data distribution**
5. **Validate across multiple time periods for robustness**
6. **Use verbose mode for debugging validation failures**

## 📞 **Support**

For issues or questions:
1. Check the validation logs for detailed error messages
2. Review the EDA reports for data quality insights
3. Use verbose mode for comprehensive debugging
4. Check the comprehensive documentation in `tests/validation_comprehensive/README.md`

---

**The validation system ensures data integrity and quality across all pipeline steps, providing confidence in the SPU clustering analysis results.**




