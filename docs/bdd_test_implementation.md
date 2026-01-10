# Role
You are a senior software engineer. Your task is to implement the actual BDD test logic **after** the refactored code has been completed and the test scaffolding exists.

**⚠️ CRITICAL SAFETY CONSTRAINT: This is Phase 2 of 2. You must complete `bdd_test_scaffolding.md` (Phase 1) before starting this phase.**

**🚫 NEVER PASS TESTS WITHOUT PROPER IMPLEMENTATION**: Tests MUST fail until real, functional step code exists and is properly tested.

# Task
This document outlines the **testing/implementation phase** (Phase 2) of the testing process. This phase takes the existing test scaffolding from **Phase 1** and **populates it with functional test code** that validates the refactored implementation.

**🚫 CRITICAL PREREQUISITES - NO EXCEPTIONS:**
1. ✅ **Refactored Code Exists**: The `Step` class must be implemented and functional (not mocked or placeholder).
2. ✅ **Scaffolding Complete**: The test scaffolding (`test_*_scaffold.py`) must exist and all tests must fail.
3. ✅ **Real Implementation Ready**: Must have actual step code that can be imported and executed.
4. 🚫 **NO MOCK IMPLEMENTATIONS**: Step implementations must be real, functional code.
5. 🚫 **NO PLACEHOLDER CODE**: All step methods must have complete implementations.
6. 🚫 **GHERKIN IS SPECIFICATION**: Feature files define expected behavior - implementation must conform to them.
7. 🚫 **NEVER CHANGE TESTS**: If implementation doesn't match feature files, fix implementation, not tests.

The developer will provide:
1. The refactored `Step` class implementation.
2. The existing test scaffolding from the scaffolding phase.

Your job is to **convert the scaffold `test_*_scaffold.py` file** into a fully functional `test_*.py` file that implements the Gherkin scenarios.

---

## 1. Test Implementation Rules

### Rule 2.1: Convert Scaffolding to Implementation
Take the existing scaffold file and populate it with actual test logic while preserving the scenario bindings and overall structure.

**🚫 MAINTAIN FEATURE FILE STRUCTURE**: The implementation must preserve the exact organization from the scaffold, which mirrors the feature file sequence and sections.

### Rule 2.2: Use a Central Fixture for State
A single `pytest.fixture` (e.g., `test_context`) **must** be used to share state between `Given/When/Then` steps. This fixture should be a dictionary holding:
* `step`: The actual `Step` instance being tested.
* `step_context`: The `StepContext` object.
* `mocks`: A dictionary of all mock objects (e.g., `{'source_repo': ..., 'output_repo': ...}`).
* `exception`: A placeholder (`None`) to store any exception caught during execution.

### Rule 2.3: Implement `Given` Steps (Arrange)
* `@given` steps are responsible for **setup**.
* They must:
    1.  Create all mocks (using `mocker`).
    2.  Create the `Step` instance, **injecting the mocks**.
    3.  Define the input `pd.DataFrame` for the scenario.
    4.  Configure the `mock_source_repo.get_all.return_value`.
    5.  Store the `step`, `step_context`, and `mocks` in the central `test_context` fixture.

### Rule 2.4: Implement `When` Step (Act)
* The `@when('...step is executed')` step is responsible for **action**.
* It **must** call `step.execute()`.
* It **must** wrap the call in a `try...except DataValidationError as e:` block.
* If an exception is caught, it must be stored (e.g., `test_context['exception'] = e`).

### Rule 2.5: Implement `Then` Steps (Assert)
* **`Then` (Success):**
    * Assert `test_context['exception'] is None`.
    * Get the resulting data: `result_data = test_context['step_context'].get_data()`.
    * Use `pandas.testing.assert_frame_equal(result_data, expected_data)` to verify the `apply` phase.
* **`Then` (Failure):**
    * Assert `test_context['exception'] is not None` and `isinstance(test_context['exception'], DataValidationError)`.
    * Assert the exception message: `assert "..." in str(test_context['exception'])`.
    * Assert the `persist` mock was **not** called: `test_context['mocks']['output_repo'].save.assert_not_called()`.

### Rule 2.6: All Tests Must Pass ONLY With Real Implementation
After the testing phase implementation, all tests **must** pass, validating that the refactored step works correctly.

**🚫 CRITICAL CONSTRAINT**: Tests MUST NOT pass with mock implementations, placeholder code, or incomplete step functionality. Only real, functional step implementations can make tests pass.

**🚫 NEVER MODIFY TESTS TO MATCH BROKEN CODE**: The Gherkin feature files are the specification. Fix the implementation to match the tests, never modify tests to match broken implementations.

**✅ EXCEPTIONS - When Test Modification IS Allowed:**
- **Import/Reference Issues**: Fix incorrect imports or source code references that prevent proper testing
- **Gherkin Misrepresentation**: Correct tests that don't accurately reflect feature file requirements

**🚫 BINARY TEST OUTCOMES - NO EXCEPTIONS:**
- **Every test must PASS or FAIL** - no middle ground, no "partial" success
- **No conditional pass/fail** based on implementation state
- **No test suppression** or skipping when issues are discovered
- **Clear failure reporting** when implementation doesn't match specification

### Rule 2.8: TDD/BDD Specification Priority
The feature files (Gherkin scenarios) are the **source of truth** and define the expected behavior. The implementation must conform to these specifications:

* **✅ CORRECT**: Modify implementation to pass existing tests
* **❌ WRONG**: Modify tests to accommodate broken or incomplete implementations
* **✅ CORRECT**: Tests fail when implementation doesn't match feature requirements
* **❌ WRONG**: Tests pass with incomplete or incorrect implementations
* **🚫 NO EXCEPTIONS**: Every test must clearly PASS or FAIL - no conditional outcomes

---

## 2. Incremental Implementation Process

The testing phase is **not** a direct replacement of scaffold code. Instead, it's an **incremental process** where you gradually convert the scaffold into functional tests. This approach mirrors how real-world test implementations like `api_download_merge_steps.py` are built.

### Step-by-Step Implementation Process:

#### Step 1: Update Imports (Replace Mock Imports with Real Ones)
**Before (Scaffolding):**
```python
# Note: NO step-specific imports yet - they don't exist in scaffolding phase
```

**After (Implementation):**
```python
# Import components (now they exist!)
from src.steps.data_cleaning import CleanProductDataStep
from src.core.step import StepContext
from src.core.exceptions import DataValidationError
from src.core.logger import PipelineLogger
```

#### Step 2: Update Scenario Functions (Replace `pytest.fail()` with `pass`)
**Before (Scaffolding):**
```python
@scenario('../features/clean_product_data.feature', 'Successful data cleaning (Happy Path)')
def test_clean_data_happy_path():
    """Scaffold test - will fail until implementation phase."""
    pytest.fail(
        "SCAFFOLDING PHASE: This test scenario is not yet implemented. "
        "The step implementation does not exist yet. "
        "Run this again after the CleanProductDataStep class has been refactored."
    )
```

**After (Implementation):**
```python
@scenario('../features/clean_product_data.feature', 'Successful data cleaning (Happy Path)')
def test_clean_data_happy_path():
    """Now functional test - validates the implemented step."""
    # The setup is already done in the fixture
    pass
```

#### Step 3: Update Fixtures (Replace `None` Values with Real Mocks)
**Before (Scaffolding):**
```python
@pytest.fixture
def test_context():
    """Holds state (step, mocks, context, exception) between steps.
    In scaffolding phase, this creates minimal structure only."""
    test_logger = PipelineLogger("TestLogger", level="DEBUG")

    return {
        "step": None,  # Will be populated in testing phase
        "step_context": StepContext(),
        "mocks": {
            "source_repo": None,  # Will be populated in testing phase
            "output_repo": None   # Will be populated in testing phase
        },
        "exception": None,  # Placeholder for catching exceptions
        "expected_data": None,  # Placeholder for expected results
        "input_data": None  # Placeholder for input data
    }
```

**After (Implementation):**
```python
@pytest.fixture
def test_context(mocker):
    """Holds state (step, mocks, context, exception) between steps.
    Now creates actual implementations instead of placeholders."""
    # Create mocks
    mock_source_repo = mocker.MagicMock()
    mock_output_repo = mocker.MagicMock()
    test_logger = PipelineLogger("TestLogger", level="DEBUG")

    # Create the Step with injected mocks (now this class exists!)
    step = CleanProductDataStep(
        source_repo=mock_source_repo,
        output_repo=mock_output_repo,
        logger=test_logger,
        fill_value=0.0
    )

    return {
        "step": step,
        "step_context": StepContext(),
        "mocks": {
            "source_repo": mock_source_repo,
            "output_repo": mock_output_repo
        },
        "exception": None  # Placeholder for catching exceptions
    }
```

#### Step 4: Update Given Steps (Replace Placeholders with Real Mock Configuration)
**Before (Scaffolding):**
```python
@given('raw product data with duplicates and null prices')
def given_raw_data_happy_path(test_context):
    """Scaffolding: Define input and expected data structure only."""
    input_data = pd.DataFrame({
        'product_id': ['A', 'B', 'A'],
        'price': [10.0, None, 10.0]
    })
    test_context['input_data'] = input_data

    # Store expected result for future implementation
    test_context['expected_data'] = pd.DataFrame({
        'product_id': ['A', 'B'],
        'price': [10.0, 0.0]  # Based on feature file expectations
    })
```

**After (Implementation):**
```python
@given('raw product data with duplicates and null prices')
def given_raw_data_happy_path(test_context):
    """Now creates actual step instance and configures mocks."""
    input_data = pd.DataFrame({
        'product_id': ['A', 'B', 'A'],
        'price': [10.0, None, 10.0]
    })
    test_context['mocks']['source_repo'].get_all.return_value = input_data

    # Store expected result for the 'Then' step
    test_context['expected_data'] = pd.DataFrame({
        'product_id': ['A', 'B'],
        'price': [10.0, 0.0]
    })
```

#### Step 5: Update When Steps (Replace `pytest.fail()` with Real Execution)
**Before (Scaffolding):**
```python
@when('the clean product data step is executed')
def when_step_is_executed(test_context):
    """
    Scaffolding: This will fail until the testing phase begins.
    The actual step implementation doesn't exist yet.
    """
    pytest.fail(
        "SCAFFOLDING PHASE: This step implementation is not yet available. "
        "The step class does not exist yet. "
        "Run this again after the CleanProductDataStep class has been refactored."
    )
```

**After (Implementation):**
```python
@when('the clean product data step is executed')
def when_step_is_executed(test_context):
    """
    Now executes the actual step implementation and catches any DataValidationError,
    storing it in the context.
    """
    try:
        test_context['step'].execute(test_context['step_context'])
    except DataValidationError as e:
        test_context['exception'] = e
    except Exception as e:
        # Catch any other unexpected exception
        test_context['exception'] = e
```

#### Step 6: Update Then Steps (Replace `pytest.fail()` with Real Assertions)
**Before (Scaffolding):**
```python
@then('the final context data is clean and valid')
def then_data_is_clean(test_context):
    """
    Scaffolding: This will fail until the testing phase begins.
    Actual assertions will be implemented in the testing phase.
    """
    pytest.fail(
        "SCAFFOLDING PHASE: This assertion is not yet implemented. "
        "The step implementation does not exist yet. "
        "Run this again after the step has been implemented and tested."
    )
```

**After (Implementation):**
```python
@then('the final context data is clean and valid')
def then_data_is_clean(test_context):
    """Now performs actual assertions on the step results."""
    # Assert validation passed (no exception)
    assert test_context['exception'] is None, \
        f"Step failed unexpectedly: {test_context['exception']}"

    # Assert 'apply' was correct
    result_data = test_context['step_context'].get_data()
    expected_data = test_context['expected_data']
    pd_testing.assert_frame_equal(result_data, expected_data)
```

### 3. Final Implementation Example

After all incremental steps are complete, your final test file should maintain the exact structure from the scaffold while replacing `pytest.fail()` with real implementations:

```python
#!/usr/bin/env python3
"""
Implementation test definitions for clean_product_data.feature

This implementation maintains the exact structure of the scaffold:
- Background steps first (if any)
- Each scenario has its own complete section
- Steps organized by scenario: @scenario, @fixture, @given, @when, @then
- Real implementations that validate the step functionality
"""

import pytest
import pandas as pd
import pandas.testing as pd_testing
from pytest_bdd import scenario, given, when, then, parsers

# Import components (now they exist!)
from src.steps.data_cleaning import CleanProductDataStep
from src.core.step import StepContext
from src.core.exceptions import DataValidationError
from src.core.logger import PipelineLogger

# ============================================================================
# SCENARIO BINDERS (in exact feature file order)
# ============================================================================

# Scenario: Successful data cleaning (Happy Path)
@scenario('../features/clean_product_data.feature', 'Successful data cleaning (Happy Path)')
def test_clean_data_happy_path():
    """Scenario: Successful data cleaning (Happy Path) - validates implemented step."""
    pass

# Scenario: Validation failure for missing required column
@scenario('../features/clean_product_data.feature', 'Validation failure for missing required column')
def test_clean_data_fails_missing_column():
    """Scenario: Validation failure for missing required column - validates error handling."""
    pass

# Scenario: Validation failure for null product IDs
@scenario('../features/clean_product_data.feature', 'Validation failure for null product IDs')
def test_clean_data_fails_null_ids():
    """Scenario: Validation failure for null product IDs - validates null handling."""
    pass

# ============================================================================
# FIXTURES (converted from scaffold)
# ============================================================================

# --- Central Fixture for State (fully implemented) ---

@pytest.fixture
def test_context(mocker):
    """Holds state (step, mocks, context, exception) between steps."""
    # Create mocks
    mock_source_repo = mocker.MagicMock()
    mock_output_repo = mocker.MagicMock()
    test_logger = PipelineLogger("TestLogger", level="DEBUG")

    # Create the Step with injected mocks
    step = CleanProductDataStep(
        source_repo=mock_source_repo,
        output_repo=mock_output_repo,
        logger=test_logger,
        fill_value=0.0
    )

    return {
        "step": step,
        "step_context": StepContext(),
        "mocks": {
            "source_repo": mock_source_repo,
            "output_repo": mock_output_repo
        },
        "exception": None
    }

# ============================================================================
# STEP DEFINITIONS (organized by scenario: @scenario, @fixture, @given, @when, @then)
# ============================================================================

# ============================================================================
# BACKGROUND STEPS (if any in feature file)
# ============================================================================

@given('raw product data')
def given_raw_product_data(test_context):
    """Background: Raw product data - creates actual step instance and configures mocks."""
    pytest.fail("Background step not implemented yet.")

# ============================================================================
# SCENARIO: Successful data cleaning (Happy Path)
# ============================================================================

@scenario('../features/clean_product_data.feature', 'Successful data cleaning (Happy Path)')
def test_clean_data_happy_path():
    """Scenario: Successful data cleaning (Happy Path) - validates implemented step."""
    pass

@given('raw product data with duplicates and null prices')
def given_raw_data_happy_path(test_context):
    """Given: raw product data with duplicates and null prices - creates actual step instance and configures mocks."""
    input_data = pd.DataFrame({
        'product_id': ['A', 'B', 'A'],
        'price': [10.0, None, 10.0]
    })
    test_context['mocks']['source_repo'].get_all.return_value = input_data
    test_context['expected_data'] = pd.DataFrame({
        'product_id': ['A', 'B'],
        'price': [10.0, 0.0]
    })

@when('the clean product data step is executed')
def when_step_is_executed(test_context):
    """When: the clean product data step is executed - executes the actual step implementation."""
    try:
        test_context['step'].execute(test_context['step_context'])
    except DataValidationError as e:
        test_context['exception'] = e

@then('the final context data is clean and valid')
def then_data_is_clean(test_context):
    """Then: the final context data is clean and valid - performs actual assertions on the step results."""
    assert test_context['exception'] is None
    result_data = test_context['step_context'].get_data()
    expected_data = test_context['expected_data']
    pd_testing.assert_frame_equal(result_data, expected_data)

# ============================================================================
# SCENARIO: Validation failure for missing required column
# ============================================================================

@scenario('../features/clean_product_data.feature', 'Validation failure for missing required column')
def test_clean_data_fails_missing_column():
    """Scenario: Validation failure for missing required column - validates error handling."""
    pass

@given('raw product data missing the "product_id" column')
def given_raw_data_missing_column(test_context):
    """Given: raw product data missing the product_id column - creates actual step instance and configures mocks."""
    input_data = pd.DataFrame({
        'name': ['Item A', 'Item B'],
        'price': [10.0, 20.0]
    })
    test_context['mocks']['source_repo'].get_all.return_value = input_data

@when('the clean product data step is executed')
def when_step_is_executed_error_scenario(test_context):
    """When: the clean product data step is executed - executes step expecting validation error."""
    try:
        test_context['step'].execute(test_context['step_context'])
    except DataValidationError as e:
        test_context['exception'] = e

@then(parsers.parse('a DataValidationError is raised for "{message}"'))
def then_validation_error_raised_missing_column(test_context, message):
    """Then: a DataValidationError is raised for missing column - performs actual error validation."""
    assert test_context['exception'] is not None
    assert isinstance(test_context['exception'], DataValidationError)
    assert message in str(test_context['exception'])

@then('the data is not persisted')
def then_data_not_persisted_missing_column(test_context):
    """Then: the data is not persisted - performs actual persistence validation for missing column scenario."""
    test_context['mocks']['output_repo'].save.assert_not_called()

# ============================================================================
# SCENARIO: Validation failure for null product IDs
# ============================================================================

@scenario('../features/clean_product_data.feature', 'Validation failure for null product IDs')
def test_clean_data_fails_null_ids():
    """Scenario: Validation failure for null product IDs - validates null handling."""
    pass

@given('raw product data with null product_ids')
def given_raw_data_null_ids(test_context):
    """Given: raw product data with null product_ids - creates actual step instance and configures mocks."""
    input_data = pd.DataFrame({
        'product_id': ['A', None],
        'price': [10.0, 20.0]
    })
    test_context['mocks']['source_repo'].get_all.return_value = input_data

@when('the clean product data step is executed')
def when_step_is_executed_null_ids_scenario(test_context):
    """When: the clean product data step is executed - executes step expecting validation error."""
    try:
        test_context['step'].execute(test_context['step_context'])
    except DataValidationError as e:
        test_context['exception'] = e

@then(parsers.parse('a DataValidationError is raised for "{message}"'))
def then_validation_error_raised_null_ids(test_context, message):
    """Then: a DataValidationError is raised for null IDs - performs actual error validation."""
    assert test_context['exception'] is not None
    assert isinstance(test_context['exception'], DataValidationError)
    assert message in str(test_context['exception'])

@then('the data is not persisted')
def then_data_not_persisted_null_ids(test_context):
    """Then: the data is not persisted - performs actual persistence validation for null IDs scenario."""
    test_context['mocks']['output_repo'].save.assert_not_called()
```

---

## 3. Testing Phase Workflow (Phase 2 of 2)

### Prerequisites for Phase 2:
1. ✅ **Phase 1 Complete**: The `Step` class must be implemented and functional.
2. ✅ **Scaffolding Ready**: The `test_*_scaffold.py` file must exist and all tests must fail with "SCAFFOLDING PHASE" messages.
3. ✅ **Clear Transition**: All scaffold tests should fail with `pytest.fail()` calls indicating they're ready for implementation.

### Implementation Steps (Direct Conversion Process):

#### Step 1: Direct File Conversion
Start by copying the scaffold and converting it directly to the implementation:

```bash
# Copy scaffold to implementation file
cp tests/test_step2_extract_coordinates_scaffold.py tests/test_step2_extract_coordinates.py

# Edit the implementation file directly (similar to how api_download_merge_steps.py was created)
# Follow the incremental steps below within the same file
```

#### Step 2: Update Imports (Add Real Step Imports)
```python
# Replace comment-only imports with actual imports
from src.steps.extract_coordinates import ExtractCoordinatesStep  # Real import
from src.core.step import StepContext
from src.core.exceptions import DataValidationError
from src.core.logger import PipelineLogger
```

#### Step 3: Update Scenario Functions (Replace pytest.fail with pass)
```python
# Replace all scenario functions like this:
@scenario('../features/step-2-extract-coordinates.feature', 'Successful coordinate extraction')
def test_successful_coordinate_extraction():
    """Now functional test - validates the implemented step."""
    pass  # Instead of pytest.fail()
```

#### Step 4: Implement Fixtures (Replace None with Real Mocks)
```python
@pytest.fixture
def test_context(mocker):  # Add mocker parameter
    """Holds state between steps with real implementations."""
    # Create real mocks
    mock_source_repo = mocker.MagicMock()
    mock_output_repo = mocker.MagicMock()
    test_logger = PipelineLogger("TestLogger", level="DEBUG")

    # Create real step instance
    step = ExtractCoordinatesStep(
        source_repo=mock_source_repo,
        output_repo=mock_output_repo,
        logger=test_logger,
        # ... other parameters based on step constructor
    )

    return {
        "step": step,  # Real step instead of None
        "step_context": StepContext(),
        "mocks": {
            "source_repo": mock_source_repo,  # Real mock
            "output_repo": mock_output_repo   # Real mock
        },
        "exception": None
    }
```

#### Step 5: Implement Step Definitions (Replace All pytest.fail with Real Logic)
```python
# Given steps: Configure real mocks based on feature file requirements
@given('raw coordinate data with valid coordinates')
def given_raw_coordinate_data(test_context):
    """Configure mocks with real test data that matches feature file expectations."""
    # The test data MUST match what the feature file specifies
    # Do NOT modify this to match broken implementations
    input_data = pd.DataFrame({
        'store_code': ['S001', 'S002'],
        'latitude': [40.7128, 34.0522],
        'longitude': [-74.0060, -118.2437]
    })
    test_context['mocks']['source_repo'].get_all.return_value = input_data

# When steps: Execute real step (implementation must work correctly)
@when('the extract coordinates step is executed')
def when_step_is_executed(test_context):
    """Execute the real step implementation."""
    # If this fails, fix the implementation, not the test
    try:
        test_context['step'].execute(test_context['step_context'])
    except DataValidationError as e:
        test_context['exception'] = e

# Then steps: Real assertions (test implementation against feature specification)
@then('the coordinates are successfully extracted and validated')
def then_coordinates_extracted(test_context):
    """Verify real step execution results match feature file expectations."""
    # These assertions validate that implementation matches the feature file
    # If implementation doesn't pass these, fix implementation, not assertions
    assert test_context['exception'] is None, "Implementation must handle valid input without errors"
    result_data = test_context['step_context'].get_data()
    assert not result_data.empty, "Implementation must produce output data"
    # ... additional assertions based on feature file requirements
```

#### Step 6: Terminal Verification Commands
```bash
# Test incrementally as you implement (must show clear PASS/FAIL)
uv run pytest tests/test_step2_extract_coordinates.py::test_successful_coordinate_extraction -v

# Run all tests in the implementation file (binary outcomes only)
uv run pytest tests/test_step2_extract_coordinates.py -v

# Check for any remaining pytest.fail calls (should be none)
grep -n "pytest.fail" tests/test_step2_extract_coordinates.py

# Verify step imports are working
grep -n "from src.steps" tests/test_step2_extract_coordinates.py

# Verify no failure suppression mechanisms (should find none)
grep -n "pytest.skip\|try:.*except\|return.*#.*suppress" tests/test_step2_extract_coordinates.py
```

#### Step 7: Final Cleanup and Rename
```bash
# Remove the scaffold file once implementation is complete and tested
rm tests/test_step2_extract_coordinates_scaffold.py

# Final implementation file should be: tests/test_step2_extract_coordinates.py
# (similar to how api_download_merge_steps.py is the final implementation)
```

### After Implementation:
- All tests should pass, validating the refactored step implementation.
- The test file should be renamed from `*_scaffold.py` to `*.py`.
- Tests serve as both validation and documentation of the step behavior.

---

## 3. TDD/BDD Implementation Strategy

### When Tests Fail During Implementation:
**🚫 DO NOT MODIFY TESTS TO ACCOMMODATE BROKEN IMPLEMENTATIONS**. Instead:

1. **Review Feature Files**: Confirm the expected behavior in the Gherkin scenarios
2. **Check Implementation**: Verify the step implementation matches feature requirements
3. **Fix Implementation**: Modify the step code to conform to the feature specifications
4. **Re-run Tests**: Verify tests pass after implementation fixes

**🚫 BINARY OUTCOME REQUIREMENT**: Every test run must result in clear PASS or FAIL - no conditional results, no suppressed failures, no "partial" success.

**✅ WHEN TO MODIFY TESTS (Legitimate Exceptions):**
- **Import/Reference Issues**: Fix incorrect module imports or source code references that prevent proper testing
- **Gherkin Misrepresentation**: Correct tests that don't accurately reflect feature file requirements
- **Setup Issues**: Fix test configuration problems that prevent proper testing

**🚫 NEVER modify tests to make broken implementations pass**
**🚫 NEVER suppress test failures** when implementation issues are discovered

### Example of Correct vs Incorrect Approach:

**✅ CORRECT (TDD/BDD Compliant):**
```python
# Feature file says: "Given valid coordinate data, When step executed, Then coordinates extracted"
# Test expects: result_data should have coordinates
result_data = step_context.get_data()
assert not result_data.empty  # Test validates feature requirement

# If this fails, fix the step implementation, not the assertion
# Implementation must produce non-empty result_data
```

**✅ LEGITIMATE TEST FIX (Import Issue):**
```python
# Wrong import prevents testing
from src.steps.coordinate_extraction import ExtractCoordinatesStep  # WRONG module name

# Fixed to correct import
from src.steps.extract_coordinates import ExtractCoordinatesStep  # CORRECT module name
```

**✅ LEGITIMATE TEST FIX (Gherkin Misrepresentation):**
```python
# Feature file says: "Then coordinates are extracted and validated"
# But test only checks extraction, missing validation requirement
assert not result_data.empty  # Only checks extraction

# Fixed to match actual Gherkin requirement
assert not result_data.empty  # Checks extraction
assert all(result_data['latitude'].between(-90, 90))  # Checks validation requirement
```

**❌ WRONG (Anti-TDD/BDD):**
```python
# Feature file says: "Then coordinates extracted" (expects data)
# But implementation is broken and returns empty data
result_data = step_context.get_data()
assert result_data.empty  # CHANGED TEST to match broken implementation - WRONG!

# Instead, fix the implementation to return proper data
```

**❌ WRONG (Suppressing Failures):**
```python
# Implementation has bugs but tests are modified to avoid clear failure
try:
    result_data = step_context.get_data()
    if result_data.empty:
        return  # SUPPRESSING FAILURE - WRONG!
    assert not result_data.empty
except Exception as e:
    pytest.skip(f"Implementation not ready: {e}")  # SUPPRESSING FAILURE - WRONG!

# CORRECT: Let tests fail clearly so implementation can be fixed
result_data = step_context.get_data()
assert not result_data.empty  # Clear PASS/FAIL outcome
```

### Validation Process:
1. **Run Tests**: `uv run pytest tests/test_*.py -v`
2. **Check Failures**: If tests fail, review feature files for expected behavior
3. **Fix Implementation**: Modify step code to match feature requirements
4. **Re-validate**: Run tests again to confirm implementation matches specification
5. **Document**: Tests serve as living documentation of expected behavior

---

## 6. Complete Implementation Workflow (Step 1 Pattern)

### End-to-End Process Mirroring Step 1:

#### Phase 1: Create Feature File (Behavioral Analysis)
```bash
# 1. Analyze legacy code behavior
# Using: docs/behaviour_and_scenario_generation.md
# Creates: tests/features/step-1-api-download-merge.feature
```

#### Phase 2: Create Scaffold (This Document)
```bash
# 2. Create scaffold from feature file
# Creates: tests/test_step1_api_download_scaffold.py
# Command: uv run pytest tests/test_step1_api_download_scaffold.py -v
# Expected: All tests fail with "SCAFFOLDING PHASE" messages
```

#### Phase 3: Convert to Implementation (This Document)
```bash
# 3. Copy scaffold to implementation location
cp tests/test_step1_api_download_scaffold.py tests/step_definitions/api_download_merge_steps.py

# 4. Edit implementation file directly:
# - Replace comment imports with real imports
# - Replace pytest.fail() in scenarios with pass
# - Replace None values in fixtures with mocker.MagicMock()
# - Replace pytest.fail() in step definitions with real logic
# - Add real assertions in Then steps

# 5. Verify implementation works
uv run pytest tests/step_definitions/api_download_merge_steps.py -v
# Expected: All tests pass

# 6. Clean up scaffold file
rm tests/test_step1_api_download_scaffold.py
```

#### Current State Check:
```bash
# Verify current implementation matches expected pattern
uv run pytest tests/step_definitions/api_download_merge_steps.py -v

# Check that no scaffold files remain
find tests/ -name "*scaffold*" -type f

# Verify step imports are working
grep -n "from src.steps" tests/step_definitions/api_download_merge_steps.py
```

### Direct File Editing Approach:
The implementation phase is **not** about creating new files, but **editing the scaffold file directly** to convert it from failing tests to passing tests. This mirrors exactly how `api_download_merge_steps.py` was created from its scaffold.

---

## 4. Best Practices for Incremental Implementation

### Pattern Matching Real-World Examples
The incremental approach mirrors how comprehensive test suites like `api_download_merge_steps.py` are developed:

1. **Start Simple**: Begin with basic scenario bindings and minimal fixtures
2. **Add Complexity Gradually**: Incrementally add sophisticated mocking and assertions
3. **Test Frequently**: Run tests after each incremental change to catch issues early
4. **Follow Existing Patterns**: Use similar fixture and mocking patterns from existing tests

### Common Implementation Patterns from `api_download_merge_steps.py`:

#### Complex Fixture Setup
```python
@pytest.fixture
def api_download_step(mock_logger, mock_repositories):
    """Create ApiDownloadStep instance with mocked dependencies."""
    return ApiDownloadStep(
        store_codes_repo=mock_repositories['store_codes_repo'],
        api_repo=mock_repositories['api_repo'],
        tracking_repo=mock_repositories['tracking_repo'],
        config_output_repo=mock_repositories['config_output_repo'],
        sales_output_repo=mock_repositories['sales_output_repo'],
        category_output_repo=mock_repositories['category_output_repo'],
        spu_output_repo=mock_repositories['spu_output_repo'],
        yyyymm='202508',
        period='A',
        batch_size=10,
        force_full_download=False,
        logger=mock_logger,
        step_name='Test API Download Step',
        step_number=1
    )
```

#### Sophisticated Mock Configuration
```python
@pytest.fixture
def mock_repositories():
    """Create mock repositories."""
    # Create tracking repo with proper methods
    tracking_repo = Mock(spec=StoreTrackingRepository)
    tracking_repo.save_processed_stores = Mock()
    tracking_repo.save_failed_stores = Mock()
    tracking_repo.get_processed_stores = Mock(return_value=[])
    tracking_repo.get_failed_stores = Mock(return_value=[])
    tracking_repo.get_stores_to_process = Mock()

    # Create API repo with proper methods
    api_repo = Mock(spec=FastFishApiRepository)
    api_repo.fetch_store_config = Mock()
    api_repo.fetch_store_sales = Mock()

    # ... additional repository mocks
```

#### Comprehensive Step Definitions
```python
@when('selecting stores to process')
def selecting_stores_to_process(context, smart_incremental_scenario_setup):
    """Execute store selection logic - lean implementation using fixture setup."""
    setup_data = smart_incremental_scenario_setup
    api_download_step = setup_data['api_download_step']

    # Create empty context - let setup phase populate it
    from src.core.context import StepContext
    real_context = StepContext()

    # Execute the complete 4-phase workflow
    result_context = api_download_step.execute(real_context)

    # Store results for verification
    context['execute_result'] = result_context
    context['real_context'] = real_context
    context['api_download_step'] = api_download_step
    context['selected_stores'] = setup_data['expected_stores']
```

### Incremental Development Workflow
1. **Copy and Modify**: Start by copying patterns from existing comprehensive tests
2. **Adapt to Your Step**: Modify the fixtures and mocks to match your step's dependencies
3. **Implement Step by Step**: Add one step definition at a time, testing as you go
4. **Refactor Gradually**: Clean up and optimize once all functionality is working
5. **Document Patterns**: Comment complex mocking logic for future maintainers

### Testing Strategy During Implementation
- **Run tests frequently** after each incremental change
- **Focus on one scenario at a time** to avoid overwhelming complexity
- **Use existing test patterns** as templates for consistency
- **Validate mock configurations** by checking if the step executes without errors
- **Add assertions incrementally** starting with basic execution validation

### TDD/BDD Compliance Rules
- **🚫 NEVER modify test assertions** to make failing tests pass (except to fix Gherkin misrepresentation)
- **🚫 NEVER change test data** to accommodate broken implementations
- **🚫 NEVER suppress test failures** or use conditional pass/fail logic
- **✅ ALWAYS fix implementation** to match feature file requirements
- **✅ ALWAYS validate** that tests reflect actual business requirements
- **✅ ALWAYS use feature files** as the source of truth for expected behavior
- **✅ FIX import issues** and source code references when they prevent proper testing
- **✅ CORRECT Gherkin misrepresentation** when tests don't match feature file requirements
- **🚫 BINARY OUTCOMES ONLY**: Every test must clearly PASS or FAIL - no middle ground

---

## 8. Important Notes for Testing Phase

- **🔄 Preserve Structure**: Maintain the scenario bindings and overall structure from scaffolding.
- **📦 Add Real Imports**: Import the actual step classes that now exist.
- **🎭 Create Real Mocks**: Replace placeholder mocks with functional mock objects.
- **⚙️ Implement Logic**: Replace failing assertions with real validation logic.
- **✅ Comprehensive Testing**: Ensure all scenarios from the feature files are properly tested.

**🚫 TDD/BDD CONSTRAINTS - NEVER VIOLATE:**
- **Feature files are specification**: Gherkin scenarios define what the implementation must do
- **Tests are immutable**: Never modify tests to match broken implementations (see exceptions below)
- **Implementation must conform**: Fix the step code to pass the tests, not vice versa
- **Real functionality required**: Tests must validate actual working code, not mocks or placeholders
- **Business requirements first**: Tests reflect business needs, implementation must satisfy them
- **Binary test outcomes**: Every test must clearly PASS or FAIL - no conditional results, no suppressed failures

**📝 Note**: The "tests are immutable" rule has specific exceptions for import issues and Gherkin misrepresentation corrections. These are not violations of TDD/BDD principles but rather corrections to ensure tests properly reflect the intended specification.

**🚫 NO FAILURE SUPPRESSION**: Tests must not use try/catch, pytest.skip, or other mechanisms to avoid clear failure reporting when implementation issues are discovered.

**✅ LEGITIMATE TEST MODIFICATIONS (Exceptions):**
- **Import/Reference Corrections**: Fix incorrect module imports or source code references
- **Gherkin Alignment**: Correct tests that misrepresent feature file requirements
- **Test Setup Issues**: Fix configuration problems that prevent proper testing
- **Always verify**: Ensure changes align with actual feature file specifications

## 9. Phase 2 Verification - Terminal Commands

### Direct Conversion Verification (One-Liners)

```bash
# 1. Verify implementation file exists and runs
uv run pytest tests/test_step2_extract_coordinates.py -v

# 2. Check no pytest.fail calls remain (should be 0 matches)
grep -c "pytest.fail" tests/test_step2_extract_coordinates.py

# 3. Verify step imports are working (should find real imports)
grep -c "from src.steps" tests/test_step2_extract_coordinates.py

# 4. Run specific test scenario
uv run pytest tests/test_step2_extract_coordinates.py::test_successful_coordinate_extraction -v

# 5. Check for any remaining None values in fixtures (should be 0)
grep -c "None.*#" tests/test_step2_extract_coordinates.py

# 6. Verify binary outcomes - no failure suppression (should be 0 matches)
grep -c "pytest.skip\|try:.*except.*pass\|return.*fail" tests/test_step2_extract_coordinates.py

# 7. Verify structure preservation (should find section headers)
grep -c "SCENARIO:\|Background:\|Given:\|When:\|Then:" tests/test_step2_extract_coordinates.py

# 8. Verify per-scenario organization (should show steps grouped by scenario)
grep -A 10 "SCENARIO:" tests/test_step2_extract_coordinates.py
```

### Manual Review by Eye
If tests don't pass as expected, review by eye:

```bash
# Check scenario bindings match feature file
grep -A 2 "@scenario" tests/test_step2_extract_coordinates.py

# Verify step definitions have real implementations
grep -A 5 "def when_step_is_executed" tests/test_step2_extract_coordinates.py

# Check fixtures create real step instances
grep -A 10 "def test_context" tests/test_step2_extract_coordinates.py

# Compare with api_download_merge_steps.py pattern
diff tests/step_definitions/api_download_merge_steps.py tests/test_step2_extract_coordinates.py | head -20

# Verify scenario organization matches feature file sequence
grep -A 1 "@scenario" tests/test_step2_extract_coordinates.py

# Check that each scenario has complete structure (should show all step types per scenario)
grep -A 15 "SCENARIO:" tests/test_step2_extract_coordinates.py
```

### Phase 2 Verification Checklist

After completing Phase 2, verify:
- [ ] **Terminal verification**: `uv run pytest tests/test_*_extract_coordinates.py -v` shows all tests passing
- [ ] **No scaffold remnants**: `grep -c "pytest.fail" tests/test_*_extract_coordinates.py` returns 0
- [ ] **Real step imports**: `grep -c "from src.steps" tests/test_*_extract_coordinates.py` finds imports
- [ ] **Real step instances**: All fixtures create actual step objects (no `None` values)
- [ ] **Real mock objects**: All mocks use `mocker.MagicMock()` instead of `None`
- [ ] **Real assertions**: All `Then` steps have actual assertions, not `pytest.fail()`
- [ ] **Feature alignment**: Test scenarios match the `.feature` file scenarios
- [ ] **Structure preservation**: Implementation maintains scaffold's feature file structure and sequence
- [ ] **Per-scenario organization**: Each scenario section follows @scenario → @fixture → @given → @when → @then
- [ ] **Step grouping**: Steps are organized by scenario, not by step type
- [ ] **Step execution**: `When` steps call `step.execute()` with real context
- [ ] **Error handling**: Tests properly catch and validate `DataValidationError`
- [ ] **Pattern matching**: Implementation follows `api_download_merge_steps.py` structure
- [ ] **File cleanup**: Scaffold file removed, implementation file renamed properly
- [ ] **TDD/BDD compliance**: Tests were NOT modified to match implementation (except legitimate exceptions)
- [ ] **Feature file priority**: Implementation was fixed to match feature requirements
- [ ] **No test compromises**: All assertions reflect actual feature file expectations
- [ ] **Import verification**: All imports and references are correct and functional
- [ ] **Gherkin alignment**: Tests accurately represent feature file requirements
- [ ] **Binary outcomes**: All tests clearly PASS or FAIL with no conditional logic
- [ ] **No failure suppression**: No try/catch, pytest.skip, or other failure avoidance mechanisms
- [ ] **Clear failure reporting**: Tests fail explicitly when implementation doesn't match specification