# AI Agent Testing Guidelines - Test Standards & Specifications

## Overview

This document establishes **test standards, data validation requirements, and testing specifications** for pipeline components. This is **human-centric documentation** for test organization and quality assurance.

**For BDD methodology, testing procedures, and progress tracking, see**: `../notes/AGENTS.md`

---

## 🎯 Testing Principles

### Core Testing Requirements

- **Every pipeline step must have comprehensive test coverage** - No exceptions
- **Real data prioritized over synthetic** - Minimize mock/synthetic data to prevent distribution assumptions
- **Binary outcomes only** - All tests must clearly PASS or FAIL (no conditional logic)
- **Living documentation** - Tests and feature files serve as specification documentation
- **Independent scenarios** - Each test scenario can run in isolation
- **Data validation emphasis** - Use pandera schemas for all data integrity checks

---

## 📊 Test Types & Organization

### Two-Tier Testing Strategy

| Test Type | Purpose | Dataset | Speed | When to Run |
|-----------|---------|---------|-------|------------|
| **Fast Tests** | Unit tests for components | Subset of real data (1-5% sampling) | Seconds | After each code change |
| **Slow Tests** | Integration/E2E tests | Complete dataset or 90%+ coverage | Minutes | Before deployment |

### Test Organization Structure

```
tests/
├── features/                  → Gherkin feature files (Given-When-Then scenarios)
├── step_definitions/          → BDD step implementations
├── conftest.py               → Shared fixtures and configuration
└── test_step[N]_*.py         → One file per pipeline step
```

**Key Rules**:
- **1 test file per step** - Maintain modular organization matching `src/steps/`
- **Feature files describe business requirements** - Not implementation details
- **Real data only** - Never use synthetic/mock data except for infrastructure setup

---

## 🔍 Data Validation Standards

### Pandera Schema Requirements

**Every reusable column must have a dedicated schema definition:**

```python
import pandera as pa

# Good: Dedicated schema for reused columns
store_id_schema = pa.Column(
    int,
    checks=pa.Check.str_matches(r"^\d+$"),
    nullable=False
)

# Every output table must have complete schema
output_schema = pa.DataFrameSchema({
    "store_id": store_id_schema,
    "latitude": pa.Column(float, checks=pa.Check.in_range(-90, 90)),
    "longitude": pa.Column(float, checks=pa.Check.in_range(-180, 180)),
})
```

### Column Type Standards

#### Categorical Columns
- **< 90 options**: Create dedicated options list
  ```python
  region = pa.Column(
      str,
      checks=pa.Check.isin(["North", "South", "East", "West"]),
      nullable=False
  )
  ```
- **> 90 options**: Very likely an ID - use regex validation
  ```python
  customer_id = pa.Column(
      str,
      checks=pa.Check.str_matches(r"^CUST_\d{6}$"),
      nullable=False
  )
  ```

#### Numerical Columns
- **Reasonable range validation required**
  ```python
  price = pa.Column(
      float,
      checks=[
          pa.Check.ge(0),           # Non-negative
          pa.Check.le(100000),      # Max reasonable price
      ],
      nullable=False
  )
  ```
- **Default display**: 3 decimal places in terminal/CLI output

---

## 📈 Distribution & Quality Checks

### Data Distribution Visualization

**Required for all inputs and outputs:**

1. **Categorical data** - Show frequency of occurrence for each category
   ```
   Region Distribution:
   - North: 35%
   - South: 30%
   - East: 20%
   - West: 15%
   ```

2. **Numerical data** - Visualize distribution patterns
   ```
   Price Distribution:
   - Min: 10.50
   - Q1: 45.25
   - Median: 125.75
   - Q3: 250.00
   - Max: 9999.99
   ```

3. **Missing data** - Track null/missing patterns
   ```
   Data Completeness:
   - store_id: 100% (0 nulls)
   - price: 98.5% (15 nulls)
   - category: 100% (0 nulls)
   ```

### EDA Without Web Servers

- Use markdown reports for distribution analysis
- Use `complexipy` to check test code readability
- Document findings in `notes/` with timestamps
- Update test specifications when data insights reveal new validation rules

---

## ✅ Test Quality Checklist

### Test Code Standards

- [ ] All test files ≤ 500 LOC
- [ ] All test functions ≤ 200 LOC
- [ ] Complete type hints on fixtures and functions
- [ ] Docstrings on all test classes and methods
- [ ] No hard-coded test data or file paths
- [ ] All dependencies injected via fixtures
- [ ] Use real data, never synthetic/mock data (except infrastructure setup)
- [ ] No print() statements (use logging)
- [ ] Binary pass/fail outcomes only
- [ ] No test suppression (pytest.skip, try/except pass, etc.)

### Data Validation Standards

- [ ] Every output table has dedicated pandera schema
- [ ] Every reusable column has dedicated schema definition
- [ ] Categorical columns < 90 options have predefined lists
- [ ] Categorical columns > 90 options validated with regex
- [ ] Numerical columns have reasonable min/max ranges
- [ ] All null/missing values accounted for
- [ ] Distribution analysis documented for inputs/outputs

### Test Scenario Coverage

- [ ] Happy path scenario - Normal operation with valid data
- [ ] Error cases - Invalid/missing data handling
- [ ] Edge cases - Boundary conditions, empty data, extreme values
- [ ] Performance case - Large dataset (slow test)
- [ ] Data completeness - No data loss through transformation

### Feature File Standards

- [ ] Declarative language (describe what, not how)
- [ ] Business perspective and domain terminology
- [ ] Independent scenarios (can run in isolation)
- [ ] Clear Given-When-Then structure
- [ ] Validation failure scenarios included
- [ ] No implementation details in feature files

---

## 📁 Per-Step Test Requirements

### Test File Organization

Each pipeline step should have:

#### Feature File (`tests/features/step-N-*.feature`)
- Business-focused Given-When-Then scenarios
- Independent test scenarios
- Error and edge case coverage
- Data completeness validation

#### Test Implementation (`tests/test_stepN_*.py`)
- One file per pipeline step
- Real data from project datasets
- Pandera schema validation
- Distribution analysis

#### Data Validation Schema (`tests/conftest.py` or dedicated schema file)
- Column definitions (type, constraints, nullability)
- Table schemas for all outputs
- Categorical options lists
- Numerical value ranges

### Example Test Structure

```python
# tests/test_step2_extract_coordinates.py
import pandera as pa
import pytest

# Schema definitions
coordinate_schema = pa.DataFrameSchema({
    "store_id": pa.Column(int, nullable=False),
    "latitude": pa.Column(float, checks=pa.Check.in_range(-90, 90), nullable=False),
    "longitude": pa.Column(float, checks=pa.Check.in_range(-180, 180), nullable=False),
})

def test_happy_path_coordinate_extraction(real_data_fixture):
    """Extract valid coordinates from real store data."""
    # Execute step
    result = real_data_fixture.step.apply(real_data_fixture.input_data)
    
    # Validate schema
    coordinate_schema.validate(result)
    
    # Assert business rules
    assert len(result) == len(real_data_fixture.input_data), "No data loss"
    assert result["latitude"].notna().all(), "All latitudes present"

def test_error_case_missing_coordinates(invalid_data_fixture):
    """Handle missing coordinate data appropriately."""
    with pytest.raises(DataValidationError) as exc_info:
        invalid_data_fixture.step.apply(invalid_data_fixture.input_data)
    
    assert "latitude" in str(exc_info.value), "Error identifies missing field"

def test_edge_case_zero_coordinates():
    """Accept zero as valid coordinate (equator/prime meridian)."""
    data = pd.DataFrame({
        "store_id": [1, 2],
        "latitude": [0.0, 90.0],
        "longitude": [0.0, -180.0],
    })
    
    result = step.apply(data)
    coordinate_schema.validate(result)
    assert len(result) == 2, "Zero coordinates not treated as missing"
```

---

## 🚀 Incremental Testing Procedure

### Sequential Component Testing

**Before E2E/Integration Testing:**

1. **Component-level tests first** - Test individual functions in isolation
2. **Step-level tests next** - Test complete step (setup → apply → validate → persist)
3. **Integration tests last** - Test step interactions and full pipeline flow

### Test Development Workflow

1. **Start with lax (or no) timeout** - Ensure test pipelines work functionally first
2. **Never modify src/ code to make tests pass** - Fix tests or step implementation instead
3. **Use real data subsets** - Start with 1-5% sample, scale up to 100%
4. **Document findings** - Record data insights and validation rules discovered

### Background Test Execution

- Use `&` to run long-running tests in background
- Keep detailed logs of background tests
- Run parallel integration tests to accelerate feedback
- Monitor with `procs --pager disable` (not `top` or `ps`)

---

## 📚 Testing Tools & Dependencies

### Required Testing Packages

```bash
# Core testing
uv pip install pytest pytest-bdd

# Data validation
uv pip install pandera

# Performance profiling
uv pip install py-spy memory-profiler

# Code quality
uv pip install complexipy
```

### Essential Commands

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_step2_extract_coordinates.py -v

# Run fast tests only
uv run pytest tests/ -m "not slow" -v

# Run with performance profiling
uv run pytest tests/ --profile -v

# Check test code quality
complexipy tests/ --min 200
```

---

## 🔄 Test Maintenance & Evolution

### When to Update Tests

- **New data validation rules discovered** - Update pandera schemas
- **Edge cases found in production** - Add test scenario for edge case
- **Distribution changes observed** - Update expected range validation
- **Business rules clarified** - Update feature file scenarios

### Test Documentation Updates

- **Feature files** - Update when business requirements change
- **Pandera schemas** - Update when data constraints discovered
- **Test fixtures** - Update when test data patterns change
- **Distribution analysis** - Document in `notes/` with timestamps

### Code Cleanliness

- Regularly check test code size with `complexipy`
- Maintain ≤ 500 LOC per test file
- Maintain ≤ 200 LOC per test function
- Remove dead test code and obsolete fixtures

---

## ⚠️ Critical Testing Rules

### Binary Test Outcomes (MANDATORY)

✅ **GOOD** - Tests clearly pass or fail:
```python
def test_coordinate_validation():
    result = step.apply(data)
    schema.validate(result)  # Pass if valid, raise if not
    assert result.notna().all()  # Clear assertion
```

❌ **BAD** - Conditional or suppressed outcomes:
```python
def test_coordinate_validation():
    try:
        result = step.apply(data)
        if result is not None:
            assert True  # Pointless
        else:
            pass  # Silent failure
    except:
        pass  # Suppressed error
```

### Real Data Only

✅ **GOOD** - Use real project data:
```python
def test_with_real_data(csv_repository):
    data = csv_repository.load("data/store_data.csv")
    result = step.apply(data)
```

❌ **BAD** - Synthetic/mock data:
```python
def test_with_synthetic_data():
    data = pd.DataFrame({
        "store_id": [1, 2, 3],
        "price": [100, 200, 300]  # Made up values
    })
```

---

## 📖 Summary: Test Documentation vs Procedures

### This File (Test Standards & Specifications)

**Audience**: QA engineers, code reviewers, test maintainers  
**Content**:
- Test types and organization structure
- Data validation requirements (pandera schemas)
- Categorical and numerical column standards
- Distribution and quality check requirements
- Per-step test requirements and examples
- Test quality checklist
- Binary outcome requirements

### Development Notes (Testing Procedures)

**Audience**: Developers implementing tests  
**Content**:
- BDD 4-phase workflow with procedures
- Feature file creation steps
- Test scaffolding process
- Test implementation procedures
- Debugging procedures for failing tests
- Background test execution procedures

---

## ✨ Final Testing Principles

1. **Real data priority** - Use actual project datasets, minimize synthetic/mock data
2. **Comprehensive schemas** - Define pandera schemas for every output table
3. **Distribution awareness** - Understand and document data patterns
4. **Binary outcomes** - All tests clearly PASS or FAIL, no conditional logic
5. **Incremental approach** - Component tests before integration tests
6. **Living documentation** - Tests serve as specification documentation
7. **Code quality** - Keep test files clean and maintainable (≤ 500 LOC)
