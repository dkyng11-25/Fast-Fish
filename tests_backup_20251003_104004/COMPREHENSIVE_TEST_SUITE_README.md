# Comprehensive Test Suite for Steps 6-18

This document describes the organization and usage of the comprehensive test suite that covers all steps from 6 to 18, following the USER_NOTE.md requirements.

## 📁 Test Suite Organization

### Directory Structure

```
tests/
├── comprehensive/                          # Main comprehensive test suite
│   └── comprehensive_test_suite_runner.py  # Main test runner
├── subset_tests/                           # Fast, comprehensive tests for each step (USER_NOTE.md compliant)
│   ├── test_step6_subset_comprehensive.py  # Cluster Analysis (5 clusters, weather compliant)
│   ├── test_step7_subset_comprehensive.py  # Missing Category Rule (SPU/subcategory)
│   ├── test_step8_subset_comprehensive.py  # Imbalanced Rule (z-threshold sweeps)
│   ├── test_step9_subset_comprehensive.py  # Below Minimum Rule (param sweeps)
│   ├── test_step12_subset_comprehensive.py # Sales Performance Rule (join modes/caps)
│   ├── test_step13_subset_comprehensive.py # Consolidate SPU Rules (multi-scenario)
│   ├── test_step14_subset_comprehensive.py # Global Overview Dashboard (metrics visibility)
│   ├── test_step15_subset_comprehensive.py # Historical Baseline (15-store subsample)
│   ├── test_step16_subset_comprehensive.py # Create Comparison Tables (logic validation)
│   ├── test_step17_subset_comprehensive.py # Augment Recommendations (STR correctness)
│   └── test_step18_subset_comprehensive.py # Validate Results (final validation rules)
├── slow_tests/                             # Slow tests (excluded from main suite, USER_NOTE.md compliant)
│   ├── test_step10_subset_comprehensive.py # SPU Assortment Optimization (marked slow)
│   └── test_step11_subset_comprehensive.py # Missed Sales Opportunity (marked slow)
├── utils/                                  # Test utilities (period detection, etc.)
│   ├── periods.py                         # Period detection utilities
│   └── performance_profiler.py           # Performance monitoring
├── validation_comprehensive/              # Validation schemas and utilities (USER_NOTE.md compliant)
│   ├── schemas/                           # Pandera schemas for all steps
│   ├── validators/                        # Validation logic and utilities
│   └── [validation utilities]
├── test_data/                             # Test data files (subsets, 5 clusters)
│   ├── subsample_*.csv                    # 5-cluster subset data files
│   └── [other test data]
├── test_logs/                             # Test execution logs and reports
│   ├── comprehensive_test_suite.log       # Main test suite execution log
│   ├── step*_subset.log                   # Individual step logs
│   └── comprehensive_test_suite_report.json # Detailed execution report
├── features/                              # Gherkin feature files (for reference)
├── step_definitions/                      # BDD step definitions (for reference)
└── [essential utility files only]
```

### ✅ Cleanup Completed - Files Removed (Non-USER_NOTE.md Compliant)

The following files have been successfully removed as they don't align with USER_NOTE.md goals:

**✅ Removed Non-Subset Based Tests:**
- `test_step*_real_data*.py` - Uses full data instead of subsets ❌
- `test_step*_full_data_archived.py` - Old full-data tests ❌
- `test_steps_6_12_comprehensive_202509A.py` - Full data comprehensive tests ❌

**✅ Removed Redundant Runners:**
- `run_all_tests.py` - Superseded by comprehensive test suite ❌
- `run_comprehensive_tests.py` - Superseded by comprehensive test suite ❌
- `run_full_and_subsample_tests.py` - Uses full data ❌
- `run_subsample_tests.py` - Old subset test runner ❌
- `simple_test_runner.py` - Basic runner, not comprehensive ❌
- `proper_test_runner.py` - Legacy runner ❌
- `real_data_test_runner.py` - Full data runner ❌
- `unified_test_runner.py` - Complex legacy runner ❌

**✅ Removed Redundant Utilities:**
- `modular_test_runner.py` - Too complex, superseded by comprehensive runner ❌
- `test_pipeline_manager.py` - Pipeline management not needed for unit tests ❌
- `test_configurations.py` - Configuration testing not needed ❌
- `test_all_validators.py` - Superseded by comprehensive validation ❌
- `test_advanced_validation.py` - Advanced validation not needed ❌
- `test_utility_modules.py` - Utility testing not needed ❌
- `test_validators_simple.py` - Superseded by comprehensive validation ❌

**✅ Removed Legacy Files:**
- `mock_validation_fix.py` - Legacy mock fixes ❌
- `mock_production_trendiness_integration.py` - Legacy mock ❌
- `step*_runner_standalone.py` - Individual step runners (use comprehensive suite) ❌
- `generate_missing_test_runners.py` - Legacy generator ❌
- `generate_test_data.py` - Data generation not needed ❌

**✅ Removed Output/Test Result Files:**
- `test_results/` - Old test results directory ❌
- `test_output/` - Old test outputs directory ❌
- `all_tests.log` - Legacy logs ❌
- `simple_test.log` - Legacy logs ❌
- `unified_test.log` - Legacy logs ❌
- `test_pipeline_results.log` - Legacy logs ❌
- `parallel_test_results.json` - Legacy results ❌
- `comprehensive_validator_test_results.json` - Legacy results ❌
- `validator_test_results*.json` - Legacy results ❌

**✅ Documentation Kept:**
- `README.md` - Main test documentation ✅
- `COMPREHENSIVE_TEST_SUITE_README.md` - New comprehensive documentation ✅
- `DATA_VALIDATION_README.md` - Data validation guide ✅
- `REAL_DATA_VALIDATION_GUIDE.md` - Real data validation ✅
- `MOCK_DATA_POLICY.md` - Mock data policy ✅
- `TEST_COVERAGE_REPORT.md` - Coverage reports ✅
- `COMPREHENSIVE_TEST_UPDATE_SUMMARY.md` - Update summaries ✅
- `data_source_report_20250918.md` - Data source reports ✅

## 🎯 USER_NOTE.md Compliance

This test suite follows all USER_NOTE.md requirements:

### ✅ Subset-Based Testing
- All tests use subset data (5 clusters) instead of full data
- Tests 5 clusters with high/average consumption spread
- Focus on black-box testing with minimal assumptions

### ✅ Multiple Parameter Settings
- Steps 7, 8, 9, 12, 13, 14, 15, 16, 17, 18 run multiple parameter variations
- Parameter sweeps capture anomalies and edge cases
- Comprehensive validation framework integration

### ✅ Parallel Execution
- Fast steps (6, 7, 8, 9, 12, 13, 14, 15, 16, 17, 18) run in parallel
- Configurable number of parallel workers
- Improved testing speed and efficiency

### ✅ Dynamic Period Detection
- Tests automatically detect available periods (202509A → 202508B → 202508A)
- Graceful fallback when data is unavailable
- Environment variable configuration for test periods

### ✅ Performance Metrics Visibility
- Step 14 specifically validates performance metrics visibility
- Comprehensive logging of test execution times
- Detailed reporting of test results

### ✅ Proper Exclusion of Slow Steps
- Steps 10 and 11 are properly marked as slow and excluded from main suite
- Can be run individually when needed
- Clear documentation of slow step status

## 🚀 How to Run the Test Suite

### Option 1: Run Full Comprehensive Suite (Excluding Slow Steps)

```bash
# From project root
cd /path/to/project
python -m pytest tests/comprehensive_test_suite_runner.py --status

# Run the comprehensive test suite
python tests/comprehensive_test_suite_runner.py

# Or using pytest
python -m pytest tests/comprehensive_test_suite_runner.py::ComprehensiveTestSuiteRunner::run_comprehensive_test_suite -v
```

### Option 2: Run Specific Step

```bash
# Run specific step (e.g., Step 7)
python tests/comprehensive_test_suite_runner.py --step 7

# Run with verbose output
python tests/comprehensive_test_suite_runner.py --step 7 --verbose
```

### Option 3: Run Individual Test Files

```bash
# Run individual step test
python -m pytest tests/subset_tests/test_step7_subset_comprehensive.py -v

# Run with coverage
python -m pytest tests/subset_tests/test_step7_subset_comprehensive.py --cov=src --cov-report=html
```

### Option 4: Run in Sequential Mode

```bash
# Run tests sequentially instead of parallel
python tests/comprehensive_test_suite_runner.py --sequential
```

### Option 5: Include Slow Steps

```bash
# Include slow steps (10 and 11) in the test suite
python tests/comprehensive_test_suite_runner.py --exclude-slow=false
```

## 📊 Test Suite Configuration

### Steps Configuration

| Step | Name | Test File Location | Slow | Description |
|------|------|-------------------|------|-------------|
| 6 | Cluster Analysis | `subset_tests/` | ❌ | Clustering algorithm validation |
| 7 | Missing Category Rule | `subset_tests/` | ❌ | Missing category detection |
| 8 | Imbalanced Rule | `subset_tests/` | ❌ | Store imbalance analysis |
| 9 | Below Minimum Rule | `subset_tests/` | ❌ | Minimum threshold validation |
| 10 | SPU Assortment Optimization | `slow_tests/` | ✅ | Slow optimization algorithms |
| 11 | Missed Sales Opportunity | `slow_tests/` | ✅ | Slow opportunity detection |
| 12 | Sales Performance Rule | `subset_tests/` | ❌ | Performance benchmarking |
| 13 | Consolidate SPU Rules | `subset_tests/` | ❌ | Rule consolidation |
| 14 | Global Overview Dashboard | `subset_tests/` | ❌ | Dashboard generation |
| 15 | Historical Baseline Download | `subset_tests/` | ❌ | Data download and validation |
| 16 | Create Comparison Tables | `subset_tests/` | ❌ | Excel comparison tables |
| 17 | Augment Recommendations | `subset_tests/` | ❌ | STR augmentation |
| 18 | Validate Results | `subset_tests/` | ❌ | Final validation rules |

### Parallel Groups

- **Fast Steps**: [6, 7, 8, 9, 12, 13, 14, 15, 16, 17, 18]
- **Slow Steps**: [10, 11]

### Execution Configuration

- Max parallel workers: 3
- Timeout per test: 600 seconds (10 minutes)
- Retry failed tests: Enabled
- Generate reports: Enabled

## 📈 Monitoring and Reporting

### Test Logs

All test execution logs are stored in `tests/test_logs/`:
- `comprehensive_test_suite.log` - Main test suite execution log
- `step*_subset.log` - Individual step logs
- `comprehensive_test_suite_report.json` - Detailed execution report

### Test Reports

The comprehensive test suite generates detailed reports:

```bash
# View test status
python tests/comprehensive_test_suite_runner.py --status

# Check logs after execution
tail -f tests/test_logs/comprehensive_test_suite.log
```

### Performance Monitoring

Each test execution includes timing information:
- Individual step execution times
- Parallel vs sequential execution comparison
- Resource usage monitoring
- Bottleneck identification

## 🛠️ Troubleshooting

### Common Issues

1. **Missing Test Data**
   ```
   Error: Subset file not found: /path/to/test_data/file.csv
   Solution: Ensure test data files exist in tests/test_data/
   ```

2. **Import Errors**
   ```
   Error: ModuleNotFoundError: No module named 'validation_comprehensive...'
   Solution: Ensure you're running from project root with proper PYTHONPATH
   ```

3. **Timeout Issues**
   ```
   Error: Test timed out after 600 seconds
   Solution: Increase timeout in test configuration or run slow steps individually
   ```

4. **Permission Errors**
   ```
   Error: Permission denied: /path/to/output/file.csv
   Solution: Check write permissions in output directory
   ```

### Debug Mode

Run tests in debug mode for detailed output:

```bash
# Enable debug logging
export PYTHONPATH=/path/to/project:$PYTHONPATH
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from tests.comprehensive_test_suite_runner import ComprehensiveTestSuiteRunner
runner = ComprehensiveTestSuiteRunner()
runner.run_specific_step(7, verbose=True)
"
```

## 📋 Test Development Guidelines

### Adding New Tests

1. Create test file in appropriate directory:
   - Fast tests: `tests/subset_tests/`
   - Slow tests: `tests/slow_tests/`

2. Follow naming convention:
   - `test_step{N}_subset_comprehensive.py`

3. Include comprehensive validation:
   ```python
   from validation_comprehensive.validators import validate_dataframe
   from validation_comprehensive.schemas.step{N}_schemas import SchemaName
   ```

4. Add to test configuration:
   ```python
   # In comprehensive_test_suite_runner.py
   'steps': {
       N: {'name': 'Step Name', 'test_file': 'path/to/test_file.py', 'slow': False}
   }
   ```

### Best Practices

- Use subset data (5 clusters) for testing
- Implement black-box testing approach
- Include multiple parameter sweeps
- Add comprehensive logging
- Follow naming conventions
- Include proper error handling
- Document test assumptions and limitations

## 📚 Additional Resources

- [USER_NOTE.md](notes/USER_NOTE.md) - Requirements and guidelines
- [Test Coverage Report](tests/TEST_COVERAGE_REPORT.md) - Coverage analysis
- [Data Validation Guide](tests/REAL_DATA_VALIDATION_GUIDE.md) - Data validation procedures
- [Mock Data Policy](tests/MOCK_DATA_POLICY.md) - Mock data usage guidelines

---

**Last Updated**: $(date)
**Test Suite Version**: 1.0
**USER_NOTE.md Compliant**: ✅
