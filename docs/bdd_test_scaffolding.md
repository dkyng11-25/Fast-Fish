# Role
You are a senior software engineer. Your task is to create the BDD test scaffolding structure that defines test scenarios and basic framework **before** the refactored code is implemented.

**⚠️ IMPORTANT: This is Phase 1 of 2. Complete this phase first, then proceed to `bdd_test_implementation.md` (Phase 2).**

# Task
This document outlines the **scaffolding phase (Phase 1)** of the testing process. This phase creates the test structure based **only** on the `.feature` files, making **no assumptions** about the actual refactored code implementation.

**This is Phase 1 of 2.** The scaffolding phase **must** be completed before any implementation begins.

**Prerequisites for Phase 1:**
1. ✅ **Feature file exists**: Generated using `behaviour_and_scenario_generation.md` (like `step-1-api-download-merge.feature`)


The developer will provide:
1. The `.feature` file generated in Step 1 (using behavioral analysis document).


Your job is to **generate the scaffold `test_*.py` file** that implements the basic test structure. All tests will fail by default until the testing phase begins.

---

## 1. Test Scaffolding Rules

### Rule 1.1: Mirror Feature File Structure Exactly
The scaffolding must establish the fundamental test framework that **exactly mirrors the feature file structure and sequence**:

* **Scenario Order**: Bind scenarios in the exact same sequence as they appear in the feature file
* **Step Organization**: Group step definitions by scenario, maintaining feature file flow
* **Section Sequence**: For each scenario: `@scenario`, `@fixture` (if needed), `@given`, `@when`, `@then`
* **Background First**: Place background steps (if any) before scenario-specific steps

### Rule 1.2: Per-Scenario Organization Structure
Each scenario must have its own complete section following this exact sequence:

```python
# ============================================================================
# SCENARIO: [Scenario Name]
# ============================================================================

@scenario('feature_file.feature', 'Scenario Name')
def test_scenario_name():
    """Scenario: [Name] - scaffold placeholder."""
    pytest.fail("SCAFFOLDING PHASE: [Scenario] not implemented.")

# Scenario-specific fixtures (if any)
@pytest.fixture
def scenario_specific_fixture():
    """Scenario-specific fixture - scaffold placeholder."""
    pytest.fail("SCAFFOLDING PHASE: Fixture not implemented.")

# Given steps for this scenario
@given('given condition')
def given_condition(test_context):
    """Given: condition - scaffold placeholder."""
    pytest.fail("SCAFFOLDING PHASE: Given step not implemented.")

# When steps for this scenario
@when('when action')
def when_action(test_context):
    """When: action - scaffold placeholder."""
    pytest.fail("SCAFFOLDING PHASE: When step not implemented.")

# Then steps for this scenario
@then('then expectation')
def then_expectation(test_context):
    """Then: expectation - scaffold placeholder."""
    pytest.fail("SCAFFOLDING PHASE: Then step not implemented.")
```

**Structure Requirements:**
- Each scenario gets its own section with clear header comments
- Steps are grouped by scenario (not by step type)
- Order within scenario: `@scenario` → `@fixture` → `@given` → `@when` → `@then`
- Background steps (if any) come before all scenario sections

### Rule 1.3: Bind Scenarios from Feature Files
Use the `@scenario` decorator to bind each scenario from the `.feature` file. These scenarios serve as placeholders for future implementation.

### Rule 1.4: Use Minimal Central Fixture
A single `pytest.fixture` (e.g., `test_context`) **must** be used to share state between `Given/When/Then` steps. This fixture should be a dictionary holding:
* `step`: Placeholder for the future `Step` instance (initially `None`).
* `step_context`: The `StepContext` object (created but minimal).
* `mocks`: **Empty dictionary** - no mock objects or mock data.
* `exception`: A placeholder (`None`) to store any exception caught during execution.

**🚫 NO MOCK DATA**: The fixture must not contain any pandas DataFrames, test data, or mock configurations.

### Rule 1.5: Implement `Given` Steps (Arrange) - Pure Scaffold
* `@given` steps are **pure placeholders** that fail immediately.
* They must:
    1.  **NOT** define any input data or mock structures.
    2.  **NOT** set up any test logic or data manipulation.
    3.  **NOT** store any data in the test context.
    4.  **Immediately fail** with clear scaffolding messages.
    5.  **Do NOT** create any mock objects or test data.

### Rule 1.6: Implement `When` Step (Act) - Fail by Default
* The `@when('...step is executed')` step is responsible for **action**.
* It **must** be implemented to fail immediately with a clear message indicating the step is not yet implemented.
* This ensures tests fail predictably until the testing phase begins.

### Rule 1.7: Implement `Then` Steps (Assert) - Fail by Default
* **`Then` steps must fail by default** with clear messages indicating they are not yet implemented.
* No actual assertions should be performed in the scaffolding phase.
* The scaffolding should only define the structure for future assertions.

### Rule 1.8: All Scenario Functions Must Fail by Default
All scenario functions **must** contain `pytest.fail()` calls with clear messages. This ensures tests fail immediately when executed, preventing accidental passes during the scaffolding phase.

### Rule 1.9: All Tests Must Fail by Default
All generated tests **must** fail with clear, informative error messages until the testing phase begins. This ensures the scaffolding doesn't pass accidentally.

---

## 2. Example: Step 2 Scaffolding

### Developer Provides:
1. `features/clean_product_data.feature` (The Gherkin file from Step 1).

### LLM-Generated Test Scaffolding (`tests/test_clean_product_data_scaffold.py`):
```python
#!/usr/bin/env python3
"""
Scaffold test definitions for clean_product_data.feature

This scaffold mirrors the exact structure of the feature file:
- Background steps first (if any)
- Each scenario has its own complete section
- Steps organized by scenario: @scenario, @fixture, @given, @when, @then
- Pure placeholders that fail until implementation phase
"""

import pytest
from pytest_bdd import scenario, given, when, then, parsers

# Import only core components that exist
from src.core.step import StepContext

# Note: NO step-specific imports - they don't exist in scaffolding phase
# Note: NO pandas imports - no mock data in scaffolding phase
# Note: NO mock test logic - scaffold is purely structural

# ============================================================================
# CENTRAL FIXTURES (shared across scenarios)
# ============================================================================

@pytest.fixture
def test_context():
    """Minimal placeholder fixture - no mock data, no mock logic."""
    return {
        "step": None,  # Placeholder - no implementation yet
        "step_context": StepContext(),  # Only core component that exists
        "mocks": {},  # Empty - no mock objects yet
        "exception": None,  # Placeholder - no testing yet
    }

# ============================================================================
# BACKGROUND STEPS (if any in feature file)
# ============================================================================

@given('raw product data')
def given_raw_product_data(test_context):
    """Background: Raw product data - scaffold placeholder."""
    pytest.fail(
        "SCAFFOLDING PHASE: Background Given step not implemented. "
        "No step class exists yet."
    )

# ============================================================================
# SCENARIO: Successful data cleaning (Happy Path)
# ============================================================================

@scenario(
    '../features/clean_product_data.feature',
    'Successful data cleaning (Happy Path)'
)
def test_clean_data_happy_path():
    """Scenario: Successful data cleaning (Happy Path) - scaffold placeholder."""
    pytest.fail(
        "SCAFFOLDING PHASE: Successful data cleaning scenario not implemented. "
        "No step class exists yet. "
        "Run this after the CleanProductDataStep class has been refactored."
    )

@given('raw product data with duplicates and null prices')
def given_raw_data_happy_path(test_context):
    """Given: raw product data with duplicates and null prices - scaffold placeholder."""
    pytest.fail(
        "SCAFFOLDING PHASE: Happy path Given step not implemented. "
        "No step class exists yet."
    )

@when('the clean product data step is executed')
def when_step_is_executed(test_context):
    """When: the clean product data step is executed - scaffold placeholder."""
    pytest.fail(
        "SCAFFOLDING PHASE: When step not implemented. "
        "No step class exists yet."
    )

@then('the final context data is clean and valid')
def then_data_is_clean(test_context):
    """Then: the final context data is clean and valid - scaffold placeholder."""
    pytest.fail(
        "SCAFFOLDING PHASE: Happy path Then step not implemented. "
        "No step class exists yet."
    )

# ============================================================================
# SCENARIO: Validation failure for missing required column
# ============================================================================

@scenario(
    '../features/clean_product_data.feature',
    'Validation failure for missing required column'
)
def test_clean_data_fails_missing_column():
    """Scenario: Validation failure for missing required column - scaffold placeholder."""
    pytest.fail(
        "SCAFFOLDING PHASE: Missing column validation scenario not implemented. "
        "No step class exists yet. "
        "Run this after the CleanProductDataStep class has been refactored."
    )

@given('raw product data missing the "product_id" column')
def given_raw_data_missing_column(test_context):
    """Given: raw product data missing the product_id column - scaffold placeholder."""
    pytest.fail(
        "SCAFFOLDING PHASE: Missing column Given step not implemented. "
        "No step class exists yet."
    )

@when('the clean product data step is executed')
def when_step_is_executed_missing_column(test_context):
    """When: the clean product data step is executed - scaffold placeholder."""
    pytest.fail(
        "SCAFFOLDING PHASE: Missing column When step not implemented. "
        "No step class exists yet."
    )

@then(parsers.parse('a DataValidationError is raised for "{message}"'))
def then_validation_error_raised(test_context, message):
    """Then: a DataValidationError is raised for message - scaffold placeholder."""
    pytest.fail(
        "SCAFFOLDING PHASE: Validation error Then step not implemented. "
        "No step class exists yet."
    )

@then('the data is not persisted')
def then_data_not_persisted(test_context):
    """Then: the data is not persisted - scaffold placeholder."""
    pytest.fail(
        "SCAFFOLDING PHASE: Persistence Then step not implemented. "
        "No step class exists yet."
    )

# ============================================================================
# SCENARIO: Validation failure for null product IDs
# ============================================================================

@scenario(
    '../features/clean_product_data.feature',
    'Validation failure for null product IDs'
)
def test_clean_data_fails_null_ids():
    """Scenario: Validation failure for null product IDs - scaffold placeholder."""
    pytest.fail(
        "SCAFFOLDING PHASE: Null ID validation scenario not implemented. "
        "No step class exists yet. "
        "Run this after the CleanProductDataStep class has been refactored."
    )

@given('raw product data with null product_ids')
def given_raw_data_null_ids(test_context):
    """Given: raw product data with null product_ids - scaffold placeholder."""
    pytest.fail(
        "SCAFFOLDING PHASE: Null IDs Given step not implemented. "
        "No step class exists yet."
    )

@when('the clean product data step is executed')
def when_step_is_executed_null_ids(test_context):
    """When: the clean product data step is executed - scaffold placeholder."""
    pytest.fail(
        "SCAFFOLDING PHASE: Null IDs When step not implemented. "
        "No step class exists yet."
    )

@then(parsers.parse('a DataValidationError is raised for "{message}"'))
def then_validation_error_raised_null_ids(test_context, message):
    """Then: a DataValidationError is raised for null IDs - scaffold placeholder."""
    pytest.fail(
        "SCAFFOLDING PHASE: Null IDs validation error Then step not implemented. "
        "No step class exists yet."
    )

@then('the data is not persisted')
def then_data_not_persisted_null_ids(test_context):
    """Then: the data is not persisted - scaffold placeholder."""
    pytest.fail(
        "SCAFFOLDING PHASE: Null IDs persistence Then step not implemented. "
        "No step class exists yet."
    )
```

---

## 3. Scaffolding Phase Workflow (Phase 1 of 2)

### Before Refactored Code Exists:
1. **Create Feature Files**: Generate `.feature` files describing the expected behavior.
2. **Generate Scaffolding**: Create `test_*_scaffold.py` files using this specification.
3. **Verify All Tests Fail**: Run tests to confirm they all fail with "SCAFFOLDING PHASE" messages.
4. **DO NOT** attempt to implement actual step logic yet.

### Critical Requirements for Phase 1:
- ✅ **All scenario functions must fail** with `pytest.fail()` calls
- ✅ **All step definitions must fail** with clear "TESTING PHASE NOT YET IMPLEMENTED" messages
- ✅ **No step imports** - they don't exist yet
- ✅ **No actual test logic** - only structure and placeholders

### Transition to Testing Phase (Phase 2):
Only after the refactored step code exists should you proceed to the **Testing Phase** (see separate document `bdd_test_implementation.md`).

**The testing phase will incrementally convert this scaffold:**
1. Replace `pytest.fail()` calls with actual test logic
2. Add real step imports and mock objects
3. Implement step definitions with actual execution and assertions
4. Follow the 6-step incremental process detailed in the implementation document

**🚫 CRITICAL TDD/BDD CONSTRAINT**: In the implementation phase, the feature files remain the specification. The scaffold tests will be populated with real implementations, but the test expectations (assertions, data structures, behavior) must remain faithful to the original feature file requirements.

**✅ EXCEPTIONS - Legitimate Test Modifications Allowed:**
- **Import/Reference Issues**: Fix incorrect imports or source code references that prevent proper testing
- **Gherkin Misrepresentation**: Correct tests that don't accurately reflect feature file requirements

**🚫 NEVER modify tests to accommodate broken implementations**
**🚫 BINARY TEST OUTCOMES**: All tests must clearly FAIL - no conditional results, no suppressed failures

This scaffold serves as the foundation that will be gradually enhanced into a comprehensive test suite similar to `api_download_merge_steps.py`.

---

## 7. Complete Workflow Example (Step 1 Pattern)

### Step 1 Process Mirrored:
1. **Behavioral Analysis**: `behaviour_and_scenario_generation.md` → `step-1-api-download-merge.feature`
2. **Scaffolding**: `bdd_test_scaffolding.md` → `test_step1_api_download_scaffold.py` (fails)
3. **Implementation**: `bdd_test_implementation.md` → `api_download_merge_steps.py` (passes)

### Terminal Workflow Verification:
```bash
# Phase 1: Verify scaffold fails correctly
uv run pytest tests/test_step1_api_download_scaffold.py -v
# Expected: All tests fail with "SCAFFOLDING PHASE" messages

# Phase 2: Convert scaffold to implementation
cp tests/test_step1_api_download_scaffold.py tests/step_definitions/api_download_merge_steps.py

# Edit the file directly, replacing all pytest.fail() with real implementations
# (This is how api_download_merge_steps.py was created)

# Phase 2: Verify implementation passes
uv run pytest tests/step_definitions/api_download_merge_steps.py -v
# Expected: All tests pass

# Cleanup: Remove scaffold file
rm tests/test_step1_api_download_scaffold.py
```

---

## 8. Important Notes for Scaffolding Phase

- **🚫 No Step Imports**: Do not import any step classes that don't exist yet.
- **❌ Clear Failure Messages**: All step definitions and scenario functions must fail with informative messages.
- **🚫 No Mock Data**: Do NOT include pandas DataFrames, test data, or mock configurations.
- **🚫 No Test Logic**: Do NOT include any data manipulation, validation, or test assertions.
- **📋 Pure Structure Only**: Only scenario bindings, fixtures, and pytest.fail() calls.
- **📋 Mirror Feature Structure**: Organize scaffold to match feature file sequence and sections exactly.
- **🎯 Preserve Feature Intent**: Ensure the scaffolding captures all scenarios from the feature files.
- **⚡ Ready for Implementation**: The scaffold should be structured to easily accept the real implementation.

## 9. Phase 1 Verification - Terminal Commands

### Quick Scaffold Verification (One-Liner)
Run this command to verify all scaffold tests fail as expected:

```bash
# From project root - verify scaffold fails correctly
uv run pytest tests/test_step2_extract_coordinates_scaffold.py -v

# Expected output: All tests should fail with "SCAFFOLDING PHASE" messages
# If any test passes, the scaffold is incorrectly implemented
```

### Detailed Verification Commands
```bash
# 1. Check that all tests fail (should be non-zero exit code)
uv run pytest tests/test_step2_extract_coordinates_scaffold.py --tb=short

# 2. Verify specific failure messages
uv run pytest tests/test_step2_extract_coordinates_scaffold.py -k "test_smart_incremental_selection" -v -s

# 3. Count failing tests (should match number of scenarios in feature file)
uv run pytest tests/test_step2_extract_coordinates_scaffold.py --tb=no -q | grep FAILED | wc -l
```

### Manual Review by Eye
If tests don't fail as expected, review the scaffold file manually:
```bash
# Check scenario bindings
grep -n "@scenario" tests/test_step2_extract_coordinates_scaffold.py

# Check for pytest.fail calls
grep -n "pytest.fail" tests/test_step2_extract_coordinates_scaffold.py

# Check for step imports (should be minimal)
grep -n "from src.steps" tests/test_step2_extract_coordinates_scaffold.py

# Check for pandas imports (should be none)
grep -n "import pandas\|from pandas" tests/test_step2_extract_coordinates_scaffold.py

# Check for mock data or test logic (should be none)
grep -n "pd\.DataFrame\|test_context\[.*\] =\|expected_data\|input_data" tests/test_step2_extract_coordinates_scaffold.py

# Check for proper structure organization (should find section headers)
grep -n "SCENARIO:\|Background:\|Given:\|When:\|Then:" tests/test_step2_extract_coordinates_scaffold.py

# Check scenario order matches feature file (should be in same sequence)
grep -A 1 "@scenario" tests/test_step2_extract_coordinates_scaffold.py

# Check for proper scenario sections (should find scenario section headers)
grep -c "SCENARIO:" tests/test_step2_extract_coordinates_scaffold.py

# Verify step organization by scenario (should show steps grouped under each scenario)
grep -A 10 "SCENARIO:" tests/test_step2_extract_coordinates_scaffold.py
```

### Phase 1 Verification Checklist

Before proceeding to Phase 2, verify:
- [ ] All scenario functions contain `pytest.fail()` calls
- [ ] All step definitions fail with "SCAFFOLDING PHASE" messages
- [ ] No step-specific imports exist in the code
- [ ] **No pandas imports** or DataFrame usage in scaffold
- [ ] **No mock data** or test data in fixtures or step definitions
- [ ] **No test logic** or data manipulation in any step definitions
- [ ] **Feature file structure mirrored**: Scenarios and steps organized in same order as feature file
- [ ] **Section organization maintained**: Clear comments indicating feature file sections
- [ ] **Per-scenario structure**: Each scenario has @scenario → @fixture → @given → @when → @then sequence
- [ ] **Scenario isolation**: Steps are grouped by scenario, not by step type
- [ ] Terminal command `uv run pytest tests/test_*_scaffold.py -v` shows all tests failing
- [ ] Feature file scenarios are all represented
- [ ] Clear transition path to implementation phase exists
- [ ] Binary outcomes enforced: All tests clearly fail (no conditional failures or suppressed errors)
