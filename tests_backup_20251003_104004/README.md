# Comprehensive Test Suite for SPU Clustering Pipeline

This directory contains a comprehensive test suite for the SPU Clustering pipeline, designed to validate all pipeline steps (5-37) with minimal duplication and maximum coverage.

## Test Structure

```
tests/
├── unified_test_runner.py          # Main unified test runner
├── simple_test_runner.py           # Basic functionality tests
├── run_comprehensive_tests.py      # Comprehensive test suite
├── common/                         # Shared test utilities
│   ├── data_validators.py         # Data validation utilities
│   └── test_utils.py              # Common test helpers
├── data_generators/               # Test data generation
│   ├── realistic_data.py          # Realistic data generator
│   ├── store_data.py              # Store data generator
│   ├── spu_data.py                # SPU data generator
│   └── sales_data.py              # Sales data generator
├── validation_comprehensive/      # Detailed validation framework
│   ├── runners/                   # Step-specific runners
│   ├── schemas/                   # Pandera schemas
│   └── main.py                    # Validation main runner
├── test_results/                  # Test output directory
└── .venv/                         # UV virtual environment
```

## Key Features

### 1. Unified Test Runner (`unified_test_runner.py`)
- **Single entry point** for all pipeline testing
- **Pandera schema validation** for all data flows
- **Real data validation** (minimizes synthetic data)
- **Flexible period handling** - works with any time period
- **Comprehensive coverage** - tests all steps 5-37
- **Minimal duplication** - shared validation logic

### 2. Pandera Schema Validation
- **Column schemas** for shared columns (store_code, spu_code, etc.)
- **Table schemas** for step-specific outputs
- **Data type validation** with proper constraints
- **Business rule validation** (e.g., positive sales amounts)

### 3. Real Data Focus
- **Uses actual production data** when available
- **Minimizes synthetic data** generation
- **Validates against real patterns** and distributions
- **Respects existing data structure**

### 4. Flexible Period Handling
- **Any time period support** - not hardcoded to specific periods
- **Automatic data availability checking**
- **Smart data download recommendations**
- **Period-aware file validation**

## Usage

### Basic Testing
```bash
# Run unified tests for current period
uv run python unified_test_runner.py --period 202508A

# Run tests for specific steps
uv run python unified_test_runner.py --period 202508A --steps step5 step6 step7

# Verbose output
uv run python unified_test_runner.py --period 202508A --verbose
```

### Simple Functionality Testing
```bash
# Test basic imports and functionality
uv run python simple_test_runner.py --period 202508A
```

### Comprehensive Testing
```bash
# Run full comprehensive test suite
uv run python run_comprehensive_tests.py --period 202508A
```

## Test Coverage

### Steps 5-14 (Core Pipeline)
- ✅ Step 5: Calculate Feels Like Temperature
- ✅ Step 6: Cluster Analysis  
- ✅ Step 7: Missing Category Rule
- ✅ Step 8: Imbalanced Rule
- ✅ Step 9: Below Minimum Rule
- ✅ Step 10: SPU Assortment Optimization
- ✅ Step 11: Missed Sales Opportunity Rule
- ✅ Step 12: Sales Performance Rule
- ✅ Step 13: Consolidate SPU Rules
- ✅ Step 14: Create Fast Fish Format

### Steps 15-37 (Advanced Pipeline)
- ✅ Steps 15-24: Covered by steps_13_24_runner.py
- ✅ Steps 25-37: Covered by comprehensive framework

## Validation Features

### Data Quality Validation
- **Schema compliance** - All outputs match expected schemas
- **Data integrity** - No null values in critical columns
- **Business logic** - Values within expected ranges
- **File structure** - All expected files present

### Performance Validation
- **Execution time** tracking
- **Memory usage** monitoring
- **Complexity analysis** with radon/pylint
- **Bottleneck identification**

### EDA Validation
- **Data distribution** analysis
- **Column frequency** analysis
- **Outlier detection**
- **Data quality metrics**

## Dependencies

All dependencies are managed via `uv` in the `pyproject.toml` file:

```toml
[project]
dependencies = [
    "pandas>=2.3.2",
    "numpy>=2.3.3",
    "scikit-learn>=1.7.2",
    "pandera>=0.26.1",
    "pytest>=8.4.2",
    "pytest-cov>=7.0.0",
    "pytest-mock>=3.15.0",
    "psutil>=7.0.0",
    "radon>=6.0.1",
    "pylint>=3.3.8",
    # ... and more
]
```

## Test Results

Test results are saved to `test_results/` directory with timestamps:
- `unified_test_results_YYYYMMDD_HHMMSS.json`
- `simple_test_results_YYYYMMDD_HHMMSS.json`
- `comprehensive_test_results_YYYYMMDD_HHMMSS.json`

## Best Practices

1. **Always use real data** when available
2. **Minimize synthetic data** generation
3. **Respect existing folder structure**
4. **Use pandera for schema validation**
5. **Test with multiple periods**
6. **Validate business logic, not just data types**
7. **Keep tests fast and focused**
8. **Document test failures clearly**

## Troubleshooting

### Missing Data Files
If tests fail due to missing data files:
1. Check if the pipeline has been run for the target period
2. Run data download steps if needed (step1, step4)
3. Verify the period format matches expected pattern (YYYYMM + period)

### Schema Validation Errors
If pandera validation fails:
1. Check the actual data structure against expected schema
2. Verify column names and data types
3. Check for null values in non-nullable columns
4. Validate business rule constraints

### Import Errors
If module import fails:
1. Ensure you're running from the tests directory
2. Check that the virtual environment is activated
3. Verify all dependencies are installed via `uv sync`

## Contributing

When adding new tests:
1. Follow the existing folder structure
2. Use pandera schemas for data validation
3. Minimize code duplication
4. Add comprehensive docstrings
5. Test with multiple periods
6. Update this README if needed