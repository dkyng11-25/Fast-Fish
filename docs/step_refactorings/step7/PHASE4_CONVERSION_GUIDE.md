# Phase 4: Test Conversion Guide

**Date:** 2025-11-03  
**Purpose:** Step-by-step guide for converting test scaffold to functional tests  
**Audience:** Developers implementing Phase 4

---

## 🎯 Overview

This guide provides **complete examples** and **reusable templates** for converting the 34 test scenarios from scaffold (using `pytest.fail()`) to functional tests with real assertions.

**Key Principle:** Replace `pytest.fail("Test not implemented yet")` with actual test logic that validates the Phase 3 implementation.

---

## 📋 Quick Reference

### Test Conversion Checklist

For each test scenario:
- [ ] Remove `pytest.fail()` placeholder
- [ ] Add actual execution logic
- [ ] Add meaningful assertions
- [ ] Verify test passes with implementation
- [ ] Verify test fails when it should

### Common Patterns

| Pattern | Use Case | Example |
|---------|----------|---------|
| **Component Test** | Test individual component | `cluster_analyzer.identify_well_selling_features()` |
| **Phase Test** | Test complete phase | `step_instance.setup(context)` |
| **E2E Test** | Test full execution | `step_instance.execute(context)` |
| **Error Test** | Test error handling | `with pytest.raises(DataValidationError)` |

---

## 🔧 Complete Conversion Examples

### Example 1: SETUP Phase Test (Data Loading)

**BEFORE (Scaffold):**
```python
@when('loading clustering data in setup phase')
def load_clustering(step_instance, test_context):
    """Load clustering data in SETUP phase."""
    # TODO: Implement actual test logic
    pytest.fail("Test not implemented yet - Phase 3 pending")

@then('clustering data is loaded successfully')
def verify_clustering_loaded(test_context):
    """Verify clustering data was loaded."""
    # TODO: Implement actual test logic
    pytest.fail("Test not implemented yet - Phase 3 pending")
```

**AFTER (Functional):**
```python
@when('loading clustering data in setup phase')
def load_clustering(step_instance, test_context):
    """Load clustering data in SETUP phase."""
    # Create context
    context = StepContext()
    
    # Execute SETUP phase
    result_context = step_instance.setup(context)
    
    # Store result for assertions
    test_context['setup_result'] = result_context

@then('clustering data is loaded successfully')
def verify_clustering_loaded(test_context):
    """Verify clustering data was loaded."""
    result_context = test_context['setup_result']
    
    # Assert data was loaded
    assert 'cluster_df' in result_context.data, "Clustering data should be in context"
    cluster_df = result_context.data['cluster_df']
    
    # Assert structure
    assert isinstance(cluster_df, pd.DataFrame), "Should be DataFrame"
    assert len(cluster_df) > 0, "Should have clustering data"
    
    # Assert required columns
    assert 'str_code' in cluster_df.columns, "Should have str_code"
    assert 'cluster_id' in cluster_df.columns, "Should have cluster_id"
    
    # Assert data quality
    assert cluster_df['str_code'].notna().all(), "No null store codes"
    assert cluster_df['cluster_id'].notna().all(), "No null cluster IDs"
```

---

### Example 2: APPLY Phase Test (Component Logic)

**BEFORE (Scaffold):**
```python
@when("the step identifies well-selling features")
def step_identify_well_selling(test_context, step_instance):
    """Identify well-selling features per cluster."""
    # TODO: Implement actual test logic
    pytest.fail("Test not implemented yet - Phase 3 pending")

@then("well-selling features are identified for each cluster")
def verify_well_selling_features(test_context):
    """Verify well-selling features were identified."""
    # TODO: Implement actual test logic
    pytest.fail("Test not implemented yet - Phase 3 pending")
```

**AFTER (Functional):**
```python
@when("the step identifies well-selling features")
def step_identify_well_selling(test_context, step_instance):
    """Identify well-selling features per cluster."""
    # Get mock data from fixtures
    cluster_df = step_instance.cluster_repo.load_clustering_results()
    sales_df = step_instance.sales_repo.load_current_sales(
        step_instance.config.period_label
    )
    
    # Execute component directly
    well_selling = step_instance.cluster_analyzer.identify_well_selling_features(
        sales_df=sales_df,
        cluster_df=cluster_df
    )
    
    # Store result
    test_context['well_selling_features'] = well_selling

@then("well-selling features are identified for each cluster")
def verify_well_selling_features(test_context):
    """Verify well-selling features were identified."""
    well_selling = test_context['well_selling_features']
    
    # Assert structure
    assert isinstance(well_selling, pd.DataFrame), "Should be DataFrame"
    assert len(well_selling) > 0, "Should identify some well-selling features"
    
    # Assert required columns
    required_cols = [
        'cluster_id', 
        'sub_cate_name',  # or spu_code depending on config
        'stores_selling',
        'total_cluster_sales',
        'pct_stores_selling',
        'cluster_size'
    ]
    for col in required_cols:
        assert col in well_selling.columns, f"Missing column: {col}"
    
    # Assert business logic (thresholds applied)
    assert (well_selling['pct_stores_selling'] >= 0.70).all(), \
        "All features should meet 70% adoption threshold"
    assert (well_selling['total_cluster_sales'] >= 100.0).all(), \
        "All features should meet $100 sales threshold"
    
    # Assert data quality
    assert well_selling['stores_selling'].notna().all(), "No null values"
    assert (well_selling['stores_selling'] > 0).all(), "All positive"
```

---

### Example 3: Error Handling Test

**BEFORE (Scaffold):**
```python
@when('loading clustering data with missing file')
def load_missing_clustering(step_instance, test_context, mock_cluster_repo):
    """Attempt to load missing clustering data."""
    # TODO: Implement actual test logic
    pytest.fail("Test not implemented yet - Phase 3 pending")

@then('a FileNotFoundError is raised')
def verify_file_not_found_error(test_context):
    """Verify error was raised."""
    # TODO: Implement actual test logic
    pytest.fail("Test not implemented yet - Phase 3 pending")
```

**AFTER (Functional):**
```python
@when('loading clustering data with missing file')
def load_missing_clustering(step_instance, test_context, mock_cluster_repo):
    """Attempt to load missing clustering data."""
    # Configure mock to raise FileNotFoundError
    mock_cluster_repo.load_clustering_results.side_effect = FileNotFoundError(
        "clustering_202510A.csv not found"
    )
    
    # Attempt to execute SETUP phase
    context = StepContext()
    
    # Store the exception
    try:
        step_instance.setup(context)
        test_context['exception'] = None
    except FileNotFoundError as e:
        test_context['exception'] = e

@then('a FileNotFoundError is raised')
def verify_file_not_found_error(test_context):
    """Verify error was raised."""
    exception = test_context['exception']
    
    # Assert exception was raised
    assert exception is not None, "Should raise FileNotFoundError"
    assert isinstance(exception, FileNotFoundError), "Should be FileNotFoundError"
    
    # Assert error message is informative
    error_msg = str(exception)
    assert 'clustering' in error_msg.lower(), "Error should mention clustering"
```

---

## 📝 Conversion Templates

### Template 1: SETUP Phase Test

```python
@when('loading [DATA_TYPE] data in setup phase')
def load_[data_type](step_instance, test_context):
    """Load [DATA_TYPE] data in SETUP phase."""
    # Create context
    context = StepContext()
    
    # Execute SETUP phase
    result_context = step_instance.setup(context)
    
    # Store result
    test_context['setup_result'] = result_context

@then('[DATA_TYPE] data is loaded successfully')
def verify_[data_type]_loaded(test_context):
    """Verify [DATA_TYPE] data was loaded."""
    result_context = test_context['setup_result']
    
    # Assert data present
    assert '[data_key]' in result_context.data
    data_df = result_context.data['[data_key]']
    
    # Assert structure
    assert isinstance(data_df, pd.DataFrame)
    assert len(data_df) > 0
    
    # Assert required columns
    required_cols = ['col1', 'col2', 'col3']
    for col in required_cols:
        assert col in data_df.columns
    
    # Assert data quality
    assert data_df['key_column'].notna().all()
```

**Usage:**
- Replace `[DATA_TYPE]` with: clustering, sales, quantity, margin
- Replace `[data_type]` with lowercase version
- Replace `[data_key]` with: cluster_df, sales_df, quantity_df, margin_df
- Update `required_cols` list

---

### Template 2: APPLY Phase Component Test

```python
@when("the step [ACTION_DESCRIPTION]")
def step_[action_name](test_context, step_instance):
    """[ACTION_DESCRIPTION]."""
    # Get input data
    input_df = test_context.get('[input_key]', 
                                 step_instance.[repo].[load_method]())
    
    # Execute component
    result = step_instance.[component].[method](
        param1=input_df,
        param2=test_context.get('[param_key]')
    )
    
    # Store result
    test_context['[result_key]'] = result

@then("[EXPECTED_OUTCOME]")
def verify_[outcome_name](test_context):
    """Verify [EXPECTED_OUTCOME]."""
    result = test_context['[result_key]']
    
    # Assert structure
    assert isinstance(result, pd.DataFrame)
    assert len(result) > 0
    
    # Assert required columns
    required_cols = ['col1', 'col2']
    for col in required_cols:
        assert col in result.columns
    
    # Assert business logic
    assert (result['metric'] >= threshold).all()
    
    # Assert data quality
    assert result['key_col'].notna().all()
```

**Usage:**
- Replace `[ACTION_DESCRIPTION]` with action (e.g., "identifies well-selling features")
- Replace `[action_name]` with snake_case version
- Replace `[component]` with: cluster_analyzer, opportunity_identifier, etc.
- Replace `[method]` with component method name
- Update assertions based on business logic

---

### Template 3: VALIDATE Phase Test

```python
@when('validating [VALIDATION_TYPE]')
def validate_[validation_type](step_instance, test_context):
    """Validate [VALIDATION_TYPE]."""
    # Create context with data
    context = StepContext()
    context.data['results'] = test_context['[results_key]']
    context.data['opportunities'] = test_context.get('[opportunities_key]', pd.DataFrame())
    
    # Execute VALIDATE phase (should return None!)
    result = step_instance.validate(context)
    
    # Store result
    test_context['validate_result'] = result
    test_context['validate_exception'] = None

@then('[VALIDATION_OUTCOME]')
def verify_[validation_outcome](test_context):
    """Verify [VALIDATION_OUTCOME]."""
    # Assert VALIDATE returned None (critical!)
    assert test_context['validate_result'] is None, \
        "VALIDATE must return None, not StepContext"
    
    # Assert no exception was raised
    assert test_context['validate_exception'] is None, \
        "VALIDATE should not raise exception for valid data"
```

**Usage:**
- Replace `[VALIDATION_TYPE]` with what's being validated
- Replace `[VALIDATION_OUTCOME]` with expected outcome
- **CRITICAL:** Always assert VALIDATE returns None

---

### Template 4: Error Handling Test

```python
@when('[ACTION_THAT_CAUSES_ERROR]')
def trigger_[error_type](step_instance, test_context, [mock_fixture]):
    """Trigger [ERROR_TYPE] by [ACTION]."""
    # Configure mock to cause error
    [mock_fixture].[method].side_effect = [ErrorType]("[error message]")
    
    # Attempt action
    context = StepContext()
    
    try:
        step_instance.[phase_method](context)
        test_context['exception'] = None
    except [ErrorType] as e:
        test_context['exception'] = e

@then('a [ERROR_TYPE] is raised with [ERROR_DETAILS]')
def verify_[error_type]_raised(test_context):
    """Verify [ERROR_TYPE] was raised."""
    exception = test_context['exception']
    
    # Assert exception raised
    assert exception is not None, "Should raise [ERROR_TYPE]"
    assert isinstance(exception, [ErrorType])
    
    # Assert error message
    error_msg = str(exception)
    assert '[keyword]' in error_msg.lower()
```

**Usage:**
- Replace `[ERROR_TYPE]` with: FileNotFoundError, DataValidationError, ValueError
- Replace `[error_type]` with lowercase version
- Update error message assertions

---

### Template 5: End-to-End Test

```python
@when("executing the complete missing category rule step")
def execute_complete_step(step_instance, test_context):
    """Execute the complete step end-to-end."""
    # Create fresh context
    context = StepContext()
    
    # Execute complete step (all 4 phases)
    result_context = step_instance.execute(context)
    
    # Store result
    test_context['final_result'] = result_context

@then("all outputs are generated successfully")
def verify_complete_execution(test_context):
    """Verify complete execution produced all outputs."""
    result = test_context['final_result']
    
    # Assert all expected data present
    expected_keys = [
        'cluster_df',
        'sales_df',
        'well_selling_features',
        'opportunities',
        'results'
    ]
    
    for key in expected_keys:
        assert key in result.data, f"Missing output: {key}"
    
    # Assert final results structure
    results = result.data['results']
    assert len(results) > 0, "Should have store results"
    
    # Assert required output columns
    required_cols = [
        'str_code',
        'cluster_id',
        'total_quantity_needed'
    ]
    for col in required_cols:
        assert col in results.columns
```

---

## 🔍 Common Conversion Patterns

### Pattern 1: Testing Component Methods Directly

```python
# Access component through step instance
result = step_instance.cluster_analyzer.identify_well_selling_features(
    sales_df=mock_sales_df,
    cluster_df=mock_cluster_df
)

# Assert on result
assert len(result) > 0
assert 'cluster_id' in result.columns
```

### Pattern 2: Testing Phase Methods

```python
# Create context
context = StepContext()

# Execute specific phase
result_context = step_instance.setup(context)
# or
result_context = step_instance.apply(context)
# or
step_instance.validate(context)  # Returns None!
# or
result_context = step_instance.persist(context)

# Assert on context data
assert 'expected_key' in result_context.data
```

### Pattern 3: Testing with Mock Data

```python
# Configure mock to return specific data
mock_repo.load_data.return_value = pd.DataFrame({
    'col1': [1, 2, 3],
    'col2': ['a', 'b', 'c']
})

# Execute
result = step_instance.component.method()

# Verify mock was called
assert mock_repo.load_data.called
assert mock_repo.load_data.call_count == 1
```

### Pattern 4: Testing Error Conditions

```python
# Configure mock to raise error
mock_repo.load_data.side_effect = FileNotFoundError("File not found")

# Use pytest.raises
with pytest.raises(FileNotFoundError) as exc_info:
    step_instance.setup(StepContext())

# Assert error details
assert "File not found" in str(exc_info.value)
```

### Pattern 5: Testing Empty/Edge Cases

```python
# Configure mock to return empty data
mock_repo.load_data.return_value = pd.DataFrame()

# Execute
result = step_instance.component.method()

# Assert graceful handling
assert isinstance(result, pd.DataFrame)
assert len(result) == 0  # Empty is valid
```

---

## 🎯 Step-by-Step Conversion Process

### For Each Test Scenario:

**Step 1: Identify Test Type**
- SETUP test? → Use Template 1
- APPLY test? → Use Template 2
- VALIDATE test? → Use Template 3
- Error test? → Use Template 4
- E2E test? → Use Template 5

**Step 2: Remove Scaffold**
```python
# DELETE THIS:
pytest.fail("Test not implemented yet - Phase 3 pending")
```

**Step 3: Add Execution Logic**
```python
# ADD THIS:
context = StepContext()
result = step_instance.[method](context)
test_context['result'] = result
```

**Step 4: Add Assertions**
```python
# ADD THIS:
result = test_context['result']
assert isinstance(result, pd.DataFrame)
assert len(result) > 0
assert 'required_column' in result.columns
```

**Step 5: Verify Test**
```bash
# Run the test
uv run pytest tests/step_definitions/test_step7_missing_category_rule.py::test_scenario_name -v

# Should PASS if implementation correct
# Should FAIL if implementation has bugs
```

---

## 📊 Test Scenario Mapping

### SETUP Phase (5 scenarios)

| Scenario | Template | Key Assertions |
|----------|----------|----------------|
| Load clustering data | Template 1 | cluster_df present, has str_code & cluster_id |
| Load sales data | Template 1 | sales_df present, has sub_cate_name & sal_amt |
| Handle missing clustering | Template 4 | FileNotFoundError raised |
| Handle missing sales | Template 4 | FileNotFoundError raised |
| Blend seasonal sales | Template 1 | Blended data has correct weights |

### APPLY Phase (18 scenarios)

| Scenario | Template | Key Assertions |
|----------|----------|----------------|
| Identify well-selling features | Template 2 | Thresholds applied, columns present |
| Handle no well-selling features | Template 5 | Empty DataFrame, no error |
| Identify opportunities | Template 2 | Missing stores found, prices resolved |
| Calculate quantities | Template 2 | Quantities > 0, realistic values |
| Validate sell-through | Template 2 | Predictions applied, approval flags |
| Calculate ROI | Template 2 | Financial metrics correct |
| Aggregate to store level | Template 2 | Counts, sums, averages correct |

### VALIDATE Phase (6 scenarios)

| Scenario | Template | Key Assertions |
|----------|----------|----------------|
| Validate required columns | Template 3 | Returns None, no exception |
| Validate no negatives | Template 3 | Returns None, no exception |
| Handle missing columns | Template 4 | DataValidationError raised |
| Handle negative quantities | Template 4 | DataValidationError raised |

### PERSIST Phase (5 scenarios)

| Scenario | Template | Key Assertions |
|----------|----------|----------------|
| Save store results | Template 2 | Mock save called, filename stored |
| Save opportunities | Template 2 | Mock save called, filename stored |
| Generate report | Template 2 | Report content generated |
| Handle empty results | Template 5 | No error, appropriate handling |

---

## ⚠️ Critical Reminders

### 1. VALIDATE Must Return None

```python
# CORRECT ✅
def validate(self, context: StepContext) -> None:
    # ... validation logic ...
    return  # Implicitly returns None

# WRONG ❌
def validate(self, context: StepContext) -> StepContext:
    # ... validation logic ...
    return context  # WRONG!
```

**In tests:**
```python
result = step_instance.validate(context)
assert result is None, "VALIDATE must return None!"
```

### 2. Use Mock Data Appropriately

```python
# GOOD ✅ - Realistic structure
mock_data = pd.DataFrame({
    'str_code': [f'{i:04d}' for i in range(1, 51)],
    'cluster_id': [1]*20 + [2]*20 + [3]*10,
    'sal_amt': np.random.lognormal(5, 1, 50)
})

# BAD ❌ - Too simplistic
mock_data = pd.DataFrame({
    'str_code': ['0001'],
    'cluster_id': [1],
    'sal_amt': [100]
})
```

### 3. Binary Outcomes Only

```python
# GOOD ✅
assert len(result) > 0, "Should have results"
assert 'column' in result.columns, "Column required"

# BAD ❌
if len(result) > 0:
    assert True
else:
    pass  # Silent failure
```

### 4. Test Both Success and Failure

```python
# Test success case
def test_valid_data():
    result = step.apply(valid_data)
    assert len(result) > 0

# Test failure case
def test_invalid_data():
    with pytest.raises(DataValidationError):
        step.apply(invalid_data)
```

---

## 🚀 Quick Start Guide

### Convert Your First Test in 5 Minutes

**1. Pick a simple SETUP test:**
```python
@when('loading clustering data in setup phase')
def load_clustering(step_instance, test_context):
    pytest.fail("Test not implemented yet")  # DELETE THIS
```

**2. Add execution:**
```python
@when('loading clustering data in setup phase')
def load_clustering(step_instance, test_context):
    context = StepContext()
    result = step_instance.setup(context)
    test_context['setup_result'] = result
```

**3. Add assertions:**
```python
@then('clustering data is loaded successfully')
def verify_clustering_loaded(test_context):
    result = test_context['setup_result']
    assert 'cluster_df' in result.data
    assert len(result.data['cluster_df']) > 0
```

**4. Run test:**
```bash
uv run pytest tests/step_definitions/test_step7_missing_category_rule.py -k "clustering" -v
```

**5. Debug if needed, then move to next test!**

---

## 📚 Additional Resources

### Useful Commands

```bash
# Run all Step 7 tests
uv run pytest tests/step_definitions/test_step7_missing_category_rule.py -v

# Run specific scenario
uv run pytest tests/step_definitions/test_step7_missing_category_rule.py -k "well_selling" -v

# Run with verbose output
uv run pytest tests/step_definitions/test_step7_missing_category_rule.py -v -s

# Stop on first failure
uv run pytest tests/step_definitions/test_step7_missing_category_rule.py -x

# Show local variables on failure
uv run pytest tests/step_definitions/test_step7_missing_category_rule.py -l
```

### Debugging Tips

```python
# Add print statements (temporarily)
print(f"DEBUG: result type = {type(result)}")
print(f"DEBUG: result columns = {result.columns.tolist()}")
print(f"DEBUG: result length = {len(result)}")

# Use pytest -s to see prints
# Remember to remove prints before committing!
```

### Common Issues

**Issue:** Test fails with "KeyError: 'cluster_df'"
- **Solution:** Check that SETUP phase actually loads the data

**Issue:** Test fails with "AttributeError: 'Mock' object has no attribute 'X'"
- **Solution:** Configure mock properly: `mock.X.return_value = ...`

**Issue:** Test passes when it shouldn't
- **Solution:** Add more specific assertions, check edge cases

**Issue:** "VALIDATE returned StepContext instead of None"
- **Solution:** Check implementation - VALIDATE must return None!

---

## ✅ Success Criteria

You've successfully converted a test when:

1. ✅ `pytest.fail()` removed
2. ✅ Actual execution logic added
3. ✅ Meaningful assertions added
4. ✅ Test passes with correct implementation
5. ✅ Test fails when it should (try breaking implementation)
6. ✅ No conditional logic in test
7. ✅ Clear error messages in assertions

---

**Phase 4 Conversion Guide Complete**

**Next Steps:**
1. Start with SETUP tests (easiest)
2. Use templates for each test type
3. Convert 2-3 tests, verify they work
4. Continue methodically through all 34 scenarios
5. Run full test suite when complete

**Estimated Time:** 8-12 hours total (2-3 hours per session)

**Good luck! You have everything you need to complete Phase 4!** 🚀
