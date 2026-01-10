# Comprehensive Test Suite Guide

**Date**: 2025-09-25
**Version**: 2.0
**Purpose**: Guide for running the test suite safely in the main project directory

---

## 🎯 **Overview**

This guide provides comprehensive instructions for running the enhanced test suite safely in the main project directory. The test suite follows USER_NOTE.md requirements and provides robust validation of the pipeline functionality.

## 📋 **Prerequisites**

### **System Requirements**
- Python 3.12+
- Virtual environment activated
- Sufficient disk space (at least 2GB for test data)
- Memory: 8GB+ recommended for parallel execution

### **Data Requirements**
- Real data available in `data/` directory
- At least one period of data (202508A, 202508B, or 202509A)
- Clustering results in `output/` directory

## 🚀 **Quick Start**

### **1. Activate Virtual Environment**
```bash
# Navigate to project root
cd /path/to/ProducMixClustering_spu_clustering_rules_visualization-copy

# Activate virtual environment
source venv/bin/activate

# Verify activation
which python
```

### **2. Check Test Suite Status**
```bash
# Check available tests and status
python tests/comprehensive_test_suite_runner.py --status
```

### **3. Run Fast Tests (Recommended)**
```bash
# Run all fast tests (Steps 6-9, 12-18) in parallel
python tests/comprehensive_test_suite_runner.py --exclude-slow

# Run with verbose output
python tests/comprehensive_test_suite_runner.py --exclude-slow --verbose
```

### **4. Run Specific Step**
```bash
# Run a specific step
python tests/comprehensive_test_suite_runner.py --step 6

# Run with verbose output
python tests/comprehensive_test_suite_runner.py --step 6 --verbose
```

---

## 📊 **Test Categories**

### **Fast Tests** (Steps 6-9, 12-18)
- **Execution Time**: ~30 seconds for all steps
- **Parallel Execution**: Yes (recommended)
- **Data Requirements**: Subset data (auto-generated)
- **Resource Usage**: Low to moderate

### **Slow Tests** (Steps 10-11)
- **Execution Time**: ~2-3 minutes each
- **Parallel Execution**: No (run separately)
- **Data Requirements**: Full data processing
- **Resource Usage**: High

---

## 🔧 **Advanced Usage**

### **Data Management**

#### **Generate Subset Data**
```bash
# Generate subset data for a specific period
python tests/data_generators/subset_generator.py --period 202508A

# Generate with custom parameters
python tests/data_generators/subset_generator.py --period 202508A --store-count 150 --cluster-count 5
```

#### **Manage Multiple Periods**
```bash
# Detect available periods
python tests/data_generators/period_data_manager.py --detect

# Setup test data for all periods
python tests/data_generators/period_data_manager.py --setup-all

# Check test data status
python tests/data_generators/period_data_manager.py --status
```

### **Test Execution Options**

#### **Sequential Execution**
```bash
# Run tests sequentially (slower but uses less resources)
python tests/comprehensive_test_suite_runner.py --exclude-slow --sequential
```

#### **Verbose Output**
```bash
# Run with detailed output
python tests/comprehensive_test_suite_runner.py --exclude-slow --verbose
```

#### **Specific Step Testing**
```bash
# Test individual steps
python tests/comprehensive_test_suite_runner.py --step 6
python tests/comprehensive_test_suite_runner.py --step 7
python tests/comprehensive_test_suite_runner.py --step 8
# ... etc
```

---

## 🛡️ **Safety Guidelines**

### **Before Running Tests**

1. **Backup Important Data**
   ```bash
   # Backup output directory if it contains important results
   cp -r output output_backup_$(date +%Y%m%d_%H%M%S)
   ```

2. **Check Disk Space**
   ```bash
   # Ensure sufficient disk space
   df -h .
   ```

3. **Verify Data Integrity**
   ```bash
   # Check if required data files exist
   ls -la data/api_data/
   ls -la output/
   ```

### **During Test Execution**

1. **Monitor Resource Usage**
   ```bash
   # Monitor CPU and memory usage
   top -p $(pgrep -f "pytest\|python.*test")
   ```

2. **Check Log Files**
   ```bash
   # Monitor test logs
   tail -f tests/test_logs/*.log
   ```

3. **Interrupt if Necessary**
   ```bash
   # Stop test execution safely
   # Press Ctrl+C to interrupt
   ```

### **After Test Execution**

1. **Check Test Results**
   ```bash
   # View test report
   cat tests/test_logs/comprehensive_test_suite_report.json
   ```

2. **Clean Up if Needed**
   ```bash
   # Clean up generated test data (optional)
   rm -rf tests/test_data/generated_*
   ```

---

## 📁 **Directory Structure**

```
tests/
├── comprehensive_test_suite_runner.py    # Main test runner
├── conftest.py                          # Test configuration
├── data_generators/                     # Data generation scripts
│   ├── subset_generator.py             # Generate subset data
│   └── period_data_manager.py          # Manage multiple periods
├── subset_tests/                        # Fast tests (Steps 6-9, 12-18)
│   ├── test_step6_subset_comprehensive.py
│   ├── test_step7_subset_comprehensive.py
│   └── ...
├── slow_tests/                          # Slow tests (Steps 10-11)
│   ├── test_step10_subset_comprehensive.py
│   └── test_step11_subset_comprehensive.py
├── validation_comprehensive/            # Validation framework
│   ├── schemas/                        # Data schemas
│   └── validators/                     # Validation functions
├── test_data/                          # Generated test data
├── test_logs/                          # Test execution logs
└── features/                           # Gherkin feature files
```

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **1. Import Errors**
```bash
# Error: ModuleNotFoundError: No module named 'validation_comprehensive'
# Solution: Ensure you're in the project root directory
pwd
# Should show: /path/to/ProducMixClustering_spu_clustering_rules_visualization-copy
```

#### **2. Data Not Found**
```bash
# Error: Store data not found for period 202508A
# Solution: Generate subset data
python tests/data_generators/subset_generator.py --period 202508A
```

#### **3. Permission Errors**
```bash
# Error: Permission denied
# Solution: Check file permissions
chmod +x tests/data_generators/*.py
```

#### **4. Memory Issues**
```bash
# Error: Out of memory
# Solution: Run tests sequentially
python tests/comprehensive_test_suite_runner.py --exclude-slow --sequential
```

### **Debug Mode**

#### **Run Individual Test Files**
```bash
# Run specific test file with debug output
python -m pytest tests/subset_tests/test_step6_subset_comprehensive.py -v -s --tb=long
```

#### **Check Test Data**
```bash
# Verify generated test data
ls -la tests/test_data/
head -5 tests/test_data/generated_*.csv
```

---

## 📈 **Performance Optimization**

### **Parallel Execution**
- **Default**: Fast tests run in parallel (4 workers)
- **Custom**: Modify `max_parallel_workers` in `comprehensive_test_suite_runner.py`
- **Sequential**: Use `--sequential` flag for resource-constrained environments

### **Resource Management**
- **Memory**: Monitor usage with `top` or `htop`
- **Disk**: Ensure 2GB+ free space for test data
- **CPU**: Parallel execution uses multiple cores

### **Data Optimization**
- **Subset Data**: Tests use 150-250 store subsets (auto-generated)
- **Period Selection**: Tests automatically detect best available period
- **Cleanup**: Old test data can be cleaned up after execution

---

## 📋 **Test Validation**

### **Schema Validation**
- All tests use comprehensive Pandera schemas
- Data type validation and constraint checking
- Business logic validation

### **Black-Box Testing**
- Tests focus on input/output behavior
- Minimal assumptions about internal implementation
- Real data validation

### **USER_NOTE.md Compliance**
- **Step 6**: Arbitrary subset handling, weather compliance
- **Steps 7-12**: 5-cluster subset, seasonal blending, parameter sweeps
- **Steps 13-14**: Input/output format compliance, performance metrics
- **Steps 15-18**: 15-store subsample validation, historical data validation

---

## 🎯 **Best Practices**

### **Regular Testing**
1. **Before Code Changes**: Run fast tests to ensure nothing is broken
2. **After Code Changes**: Run full test suite to validate changes
3. **Periodic Validation**: Run slow tests weekly or before releases

### **Data Management**
1. **Keep Real Data**: Don't delete original data files
2. **Generate Subsets**: Use subset data for fast testing
3. **Clean Up**: Remove old generated test data periodically

### **Monitoring**
1. **Check Logs**: Review test logs for warnings and errors
2. **Monitor Performance**: Track test execution times
3. **Validate Results**: Ensure test results make sense

---

## 🆘 **Support**

### **Getting Help**
1. **Check Logs**: Review `tests/test_logs/` for error details
2. **Verify Setup**: Ensure all prerequisites are met
3. **Run Status Check**: Use `--status` flag to check test suite status

### **Common Commands**
```bash
# Check test suite status
python tests/comprehensive_test_suite_runner.py --status

# Generate subset data
python tests/data_generators/subset_generator.py --period 202508A

# Run fast tests
python tests/comprehensive_test_suite_runner.py --exclude-slow

# Run specific step
python tests/comprehensive_test_suite_runner.py --step 6
```

---

## 📝 **Notes**

- **Test Data**: All tests use real data subsets, not mock data
- **Period Flexibility**: Tests work with 202508A, 202508B, 202509A data
- **Black-Box Approach**: Tests validate functionality, not implementation
- **Comprehensive Validation**: All tests use schema and validator patterns
- **Performance**: Fast tests run in parallel for efficiency

---

**Last Updated**: 2025-09-25
**Version**: 2.0
**Status**: Production Ready









