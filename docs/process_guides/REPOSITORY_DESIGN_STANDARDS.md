# Repository Design Standards - Implied Standards from Existing Code

**Date:** 2025-10-10  
**Status:** ✅ COMPLETE  
**Purpose:** Document the implied standards discovered by analyzing existing repositories

---

## 🎯 Purpose

This document captures the **implied standards** that exist in the codebase but were not formally documented. These standards were discovered by analyzing existing repositories (Step 1, Step 2) and understanding what quality aspects they embody.

**Key Insight:** "There are undocumented requirements that we encountered before such as having one repository script per file or having test scripts place the given, when and then parts in a sequence in order to reflect intent."

---

## 📋 Analysis Methodology

**Repositories Analyzed:**
- `src/repositories/base.py` - Base repository pattern
- `src/repositories/csv_repository.py` - CSV file operations (4 repository classes)
- `src/repositories/weather_api_repository.py` - API interactions
- `src/repositories/tracking_repository.py` - Progress tracking
- `src/steps/extract_coordinates_step.py` - Step 2 (refactored step)

**Tests Analyzed:**
- `tests/step_definitions/test_step4_weather_data.py` - Test structure and patterns

---

## 🏗️ Repository Structure Standards

### **Standard 1: One Repository Class Per Responsibility**

**Observation:** `csv_repository.py` contains 4 repository classes, but each has a distinct responsibility:
- `CsvFileRepository` - Generic CSV operations
- `MultiPeriodCsvRepository` - Multi-period CSV scanning
- `StoreCoordinatesRepository` - Store coordinates specific
- `SPUMappingRepository` - SPU mapping specific
- `SPUMetadataRepository` - SPU metadata specific

**Implied Standard:**
```
✅ Multiple repository classes in one file are acceptable IF:
   - Each class has a distinct, focused responsibility
   - They are related (all handle CSV files)
   - Each class is small and focused

❌ Do NOT put unrelated repositories in the same file

**Manager's Preference (2025-10-10):**
"One repository per file" is strongly preferred. Multiple repositories in one file should only be used for very closely related classes (like CSV variants).

**Step 4 Example:**
- `WeatherDataRepository` - One file (weather_data_repository.py)
- `WeatherFileRepository` - Separate file (weather_file_repository.py)
- **Reason:** Different responsibilities, better separation of concerns
```

**Example:**
```python
# ✅ GOOD - Related repositories in one file
# File: csv_repository.py
class CsvFileRepository(Repository):
    """Generic CSV operations."""
    
class MultiPeriodCsvRepository(Repository):
    """Multi-period CSV scanning."""

# ❌ BAD - Unrelated repositories in one file
# File: data_repository.py
class CsvFileRepository(Repository):
    """CSV operations."""
    
class WeatherApiRepository(Repository):
    """Weather API calls."""  # Should be in separate file!
```

---

### **Standard 2: Repository Inheritance Pattern**

**Observation:** All repositories inherit from `Repository` base class and follow consistent initialization.

**Implied Standard:**
```python
# ✅ REQUIRED Pattern
class {Name}Repository(Repository):
    def __init__(self, param1: Type1, logger: PipelineLogger):
        Repository.__init__(self, logger)  # Call base init
        # OR
        super().__init__(logger)  # Alternative
        
        self.param1 = param1
```

**Key Points:**
- Always inherit from `Repository`
- Always call base class `__init__` with logger
- Logger is ALWAYS the last parameter
- Store dependencies as instance variables

**Example from `weather_api_repository.py`:**
```python
class WeatherApiRepository(Repository):
    def __init__(self, logger: PipelineLogger, timezone: str = 'Asia/Shanghai'):
        super().__init__(logger)  # ✅ Correct
        self.timezone = timezone
```

---

### **Standard 3: Repository Naming Conventions**

**Observation:** Consistent naming patterns across all repositories.

**Implied Standard:**
```
Class Name:     {Purpose}{Type}Repository
                Example: WeatherApiRepository, StoreCoordinatesRepository

File Name:      {type}_repository.py
                Example: weather_api_repository.py, csv_repository.py

Instance Name:  {purpose}_{type}_repo
                Example: weather_api_repo, store_coords_repo
```

**Naming Rules:**
- Class names are PascalCase
- File names are snake_case
- Always end with `Repository` (class) or `_repository.py` (file)
- Be specific about purpose (WeatherApi, not just Api)

---

### **Standard 4: Module-Level Documentation**

**Observation:** All repository files have comprehensive module docstrings.

**Implied Standard:**
```python
#!/usr/bin/env python3
"""
{Repository Name} - {Brief Description}

{Detailed purpose explanation}

This repository {what it does and why}.

Author: Data Pipeline
Date: {Date}
"""
```

**Required Elements:**
1. Shebang line (`#!/usr/bin/env python3`)
2. Triple-quoted docstring at top
3. Brief description on first line
4. Detailed explanation
5. Author and date

**Example from `weather_api_repository.py`:**
```python
#!/usr/bin/env python3
"""
Weather API Repository - Handles Open-Meteo API interactions

This repository abstracts all weather data API calls, including:
- Historical weather data from Open-Meteo Archive API
- Elevation data from Open-Meteo Elevation API
"""
```

---

### **Standard 5: Import Organization**

**Observation:** Consistent import ordering across all files.

**Implied Standard:**
```python
# 1. Future imports
from __future__ import annotations

# 2. Standard library imports (alphabetical)
from typing import Dict, List, Optional, Any
import os
import pandas as pd

# 3. Core framework imports
from core.logger import PipelineLogger
from core.exceptions import DataValidationError

# 4. Repository imports
from .base import Repository
from repositories import OtherRepository

# 5. Local imports (if any)
from .helper_module import HelperClass
```

**Rules:**
- Group imports by category
- Blank line between groups
- Alphabetical within groups
- Use `from __future__ import annotations` for type hints

---

### **Standard 6: Constants at Class Level**

**Observation:** Configuration constants are defined at class level, not module level.

**Implied Standard:**
```python
class WeatherApiRepository(Repository):
    # ✅ Class-level constants (UPPERCASE)
    WEATHER_API_URL = 'https://archive-api.open-meteo.com/v1/archive'
    DEFAULT_TIMEOUT = 30
    HOURLY_VARIABLES = [...]
    
    def __init__(self, logger: PipelineLogger):
        super().__init__(logger)
```

**Rules:**
- Constants in UPPERCASE_WITH_UNDERSCORES
- Defined immediately after class declaration
- Group related constants together
- Add comments for complex constants

---

### **Standard 7: Method Organization and Sections**

**Observation:** Methods are organized into clear sections with comment headers.

**Implied Standard:**
```python
class {Name}Repository(Repository):
    # Constants here
    
    def __init__(self, ...):
        """Initialization."""
        
    # ========================================================================
    # PUBLIC METHODS
    # ========================================================================
    
    def get_data(self, ...):
        """Public method with full docstring."""
        
    def save_data(self, ...):
        """Public method with full docstring."""
    
    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================
    
    def _helper_method(self, ...):
        """Private helper method."""
```

**Rules:**
- Use section headers with `# ===...===`
- Separate PUBLIC and PRIVATE methods
- Public methods first, private methods last
- Private methods start with underscore `_`

**Example from `weather_api_repository.py`:**
```python
# Line 61-149: Public methods (fetch_weather_data, get_elevation)
# Line 206-217: Helper methods (check_rate_limit)
```

---

### **Standard 8: Comprehensive Docstrings**

**Observation:** All public methods have detailed docstrings following Google style.

**Implied Standard:**
```python
def fetch_weather_data(
    self,
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    store_code: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch historical weather data for a location and date range.
    
    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        store_code: Optional store code to add to result
        
    Returns:
        pd.DataFrame: Hourly weather data with all variables
        
    Raises:
        WeatherApiError: If API call fails
    """
```

**Required Elements:**
1. Brief description (one line)
2. Blank line
3. `Args:` section with all parameters
4. `Returns:` section with type and description
5. `Raises:` section if applicable

**Rules:**
- Every public method MUST have docstring
- Private methods SHOULD have brief docstring
- Use Google-style format
- Be specific about types and formats

---

### **Standard 9: Error Handling Patterns**

**Observation:** Consistent error handling with custom exceptions and logging.

**Implied Standard:**
```python
# 1. Define custom exception at module level
class WeatherApiError(Exception):
    """Raised when weather API calls fail."""
    pass

# 2. Use try-except with logging
def fetch_data(self, ...):
    try:
        response = requests.get(...)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.HTTPError as e:
        self.logger.error(f"HTTP error: {e}", self.repo_name)
        raise WeatherApiError(f"HTTP error: {e}") from e
        
    except Exception as e:
        self.logger.error(f"Unexpected error: {e}", self.repo_name)
        raise WeatherApiError(f"Unexpected error: {e}") from e
```

**Rules:**
- Define custom exceptions for domain errors
- Always log before raising
- Use `raise ... from e` to preserve stack trace
- Catch specific exceptions first, generic last
- Include context in error messages

---

### **Standard 10: Logging Patterns**

**Observation:** Consistent logging with appropriate levels and context.

**Implied Standard:**
```python
# Use self.logger with appropriate levels
self.logger.info("Starting operation", self.repo_name)
self.logger.debug(f"Processing item: {item}", self.repo_name)
self.logger.warning("Potential issue detected", self.repo_name)
self.logger.error(f"Operation failed: {error}", self.repo_name)
```

**Logging Levels:**
- `info` - Major operations, milestones
- `debug` - Detailed progress, data inspection
- `warning` - Recoverable issues, fallbacks
- `error` - Failures, exceptions

**Rules:**
- Always pass `self.repo_name` as second parameter
- Use f-strings for dynamic messages
- Log before and after major operations
- Include relevant context (counts, IDs, etc.)

---

### **Standard 11: Type Hints Everywhere**

**Observation:** All methods have complete type hints.

**Implied Standard:**
```python
from __future__ import annotations  # At top of file
from typing import Dict, List, Optional, Any

def get_data(
    self,
    param1: str,
    param2: Optional[int] = None
) -> Dict[str, Any]:
    """Method with full type hints."""
```

**Rules:**
- Use `from __future__ import annotations` for forward references
- Type hint ALL parameters
- Type hint ALL return values
- Use `Optional[Type]` for optional parameters
- Use `Dict[str, Any]` for flexible dictionaries
- Use `List[Type]` for lists of specific types

---

### **Standard 12: Dataclass for Complex Types**

**Observation:** Complex data structures use `@dataclass` decorator.

**Implied Standard:**
```python
from dataclasses import dataclass

@dataclass
class PeriodInfo:
    """Information about a time period for weather data."""
    period_label: str  # e.g., "202505A"
    yyyymm: str  # e.g., "202505"
    period_half: str  # "A" or "B"
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    weather_period_label: str  # YYYYMMDD_to_YYYYMMDD
```

**Rules:**
- Use `@dataclass` for data containers
- Add docstring explaining purpose
- Add inline comments for field formats
- Keep dataclasses at top of file (after imports)
- Use descriptive field names

---

### **Standard 13: Repository Composition Over Inheritance**

**Observation:** Repositories use other repositories via composition, not inheritance.

**Implied Standard:**
```python
# ✅ GOOD - Composition
class WeatherDataRepository(Repository):
    def __init__(
        self,
        weather_api_repo: WeatherApiRepository,
        csv_repo: CsvFileRepository,
        logger: PipelineLogger
    ):
        super().__init__(logger)
        self.weather_api_repo = weather_api_repo  # Compose
        self.csv_repo = csv_repo  # Compose

# ❌ BAD - Inheritance
class WeatherDataRepository(WeatherApiRepository):
    """Don't inherit from other repositories!"""
```

**Rules:**
- Repositories compose other repositories
- Inject dependencies via constructor
- Store as instance variables
- Call methods on composed repositories

---

### **Standard 14: Method Naming Conventions**

**Observation:** Consistent verb patterns for method names.

**Implied Standard:**
```
get_{something}      - Retrieve data (read-only)
fetch_{something}    - Retrieve from external source (API, network)
save_{something}     - Persist data (write)
load_{something}     - Load from file/storage
check_{something}    - Boolean check (returns True/False)
validate_{something} - Validation (raises exception on failure)
_helper_{action}     - Private helper method
```

**Examples:**
- `get_all()` - Get all records
- `fetch_weather_data()` - Fetch from API
- `save(data)` - Save data
- `load_progress()` - Load from file
- `check_rate_limit()` - Boolean check
- `validate_data()` - Validation
- `_parse_coordinates()` - Private helper

---

### **Standard 15: Return Type Consistency**

**Observation:** Consistent return types for similar operations.

**Implied Standard:**
```python
# get_all() always returns List[Dict[str, Any]]
def get_all(self) -> List[Dict[str, Any]]:
    df = pd.read_csv(self.file_path)
    return df.to_dict('records')  # Convert to list of dicts

# save() always returns None
def save(self, data: pd.DataFrame) -> None:
    data.to_csv(self.file_path, index=False)

# fetch methods return DataFrames
def fetch_weather_data(self, ...) -> pd.DataFrame:
    return pd.DataFrame(...)
```

**Rules:**
- `get_all()` → `List[Dict[str, Any]]`
- `save()` → `None`
- `fetch_*()` → `pd.DataFrame` (for data retrieval)
- `check_*()` → `bool`
- `validate_*()` → `None` (raises on failure)

---

## 🧪 Test Design Standards

### **Standard 16: Test File Organization**

**Observation:** Tests follow specific organizational patterns.

**Implied Standard:**
```python
#!/usr/bin/env python3
"""
Test definitions for Step {N} - {Name}

This module implements pytest-bdd test scenarios for {purpose}.
All tests use mocked repositories - no real API calls or file I/O.
"""

# 1. Imports
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

# 2. Load scenarios
scenarios('../features/step-{N}-{name}.feature')

# 3. Fixtures section
# ============================================================================
# FIXTURES - Mock Repositories and Test Data
# ============================================================================

@pytest.fixture
def mock_repo():
    """Mock repository."""

# 4. Test steps organized by SCENARIO
# ============================================================================
# Scenario 1: {Scenario Name}
# ============================================================================

@given('precondition')
def setup():
    """Setup for scenario 1."""

@when('action')
def action():
    """Action for scenario 1."""

@then('expected result')
def verify():
    """Verification for scenario 1."""

# ============================================================================
# Scenario 2: {Scenario Name}
# ============================================================================
# ... next scenario ...
```

**Key Rules:**
- Module docstring explains purpose
- Load scenarios at top
- Fixtures grouped together with header
- **Test steps organized by SCENARIO** (not by decorator type!)
- Section headers separate scenarios
- Given/When/Then in sequence for each scenario

---

### **Standard 17: Test Steps Reflect Intent**

**Observation:** Test steps are organized to reflect the scenario flow, not grouped by decorator type.

**Implied Standard:**
```python
# ✅ CORRECT - Organized by scenario (reflects intent)
# ============================================================================
# Scenario: Download weather data for multiple stores
# ============================================================================

@given('a list of store coordinates')
def setup_stores(test_context):
    test_context['stores'] = [...]

@when('downloading weather data for all stores')
def download_weather(test_context, weather_repo):
    result = weather_repo.get_weather_data_for_period(...)
    test_context['result'] = result

@then('weather data should be downloaded for each store')
def verify_download(test_context):
    assert len(test_context['result']) > 0

# ============================================================================
# Scenario: Handle API rate limiting
# ============================================================================

@given('API rate limit is reached')
def setup_rate_limit(test_context, mock_api):
    mock_api.fetch_weather_data.side_effect = RateLimitError()

@when('downloading weather data')
def download_with_rate_limit(test_context, weather_repo):
    # Test rate limit handling

@then('should retry with backoff')
def verify_retry(test_context):
    # Verify retry logic


# ❌ WRONG - Organized by decorator type (hard to follow intent)
# All @given together
@given('a list of store coordinates')
def setup_stores():
    pass

@given('API rate limit is reached')
def setup_rate_limit():
    pass

# All @when together
@when('downloading weather data for all stores')
def download_weather():
    pass

@when('downloading weather data')
def download_with_rate_limit():
    pass

# All @then together
@then('weather data should be downloaded for each store')
def verify_download():
    pass

@then('should retry with backoff')
def verify_retry():
    pass
```

**Why This Matters:**
- **Readability:** Easy to understand each scenario's flow
- **Maintainability:** Changes to one scenario don't affect others
- **Intent:** Clear what each scenario tests
- **Debugging:** Easy to find which scenario failed

---

### **Standard 18: Fixture Naming Conventions**

**Observation:** Consistent fixture naming patterns.

**Implied Standard:**
```
mock_{repository_name}_repo  - Mock repository
test_{component}             - Test component/config
{component}_instance         - Actual instance for testing
test_context                 - Shared test context
```

**Examples:**
```python
@pytest.fixture
def mock_weather_api_repo(mocker):
    """Mock Weather API repository."""

@pytest.fixture
def test_logger():
    """Create test logger."""

@pytest.fixture
def test_config():
    """Create test configuration."""

@pytest.fixture
def weather_step(mock_weather_api_repo, test_logger):
    """Create weather step instance."""
```

---

### **Standard 19: Mock Data Realism**

**Observation:** Mock data is realistic and comprehensive.

**Implied Standard:**
```python
@pytest.fixture
def mock_weather_api_repo(mocker):
    """Mock with realistic data."""
    repo = mocker.Mock()
    
    # ✅ Realistic data with proper structure
    weather_data = pd.DataFrame({
        'time': pd.date_range('2025-05-01', periods=360, freq='H'),
        'temperature_2m': [20.5 + i * 0.1 for i in range(360)],
        'relative_humidity_2m': [65.0 + i * 0.05 for i in range(360)],
        # ... all required columns ...
    })
    
    repo.fetch_weather_data.return_value = weather_data
    return repo
```

**Rules:**
- Mock data should match real data structure
- Include all required columns
- Use realistic values and ranges
- Use proper data types (dates, floats, etc.)
- Add comments explaining mock behavior

---

## 📊 Summary of Implied Standards

### **File Organization:**
1. ✅ One responsibility per repository class
2. ✅ Related repositories can share a file
3. ✅ Consistent file naming: `{type}_repository.py`

### **Code Structure:**
4. ✅ Module docstring with purpose
5. ✅ Organized imports (future, stdlib, core, local)
6. ✅ Constants at class level
7. ✅ Methods organized into PUBLIC/PRIVATE sections
8. ✅ Comprehensive docstrings (Google style)

### **Design Patterns:**
9. ✅ Inherit from `Repository` base class
10. ✅ Composition over inheritance
11. ✅ Dependency injection via constructor
12. ✅ Logger always last parameter

### **Code Quality:**
13. ✅ Type hints everywhere
14. ✅ Dataclasses for complex types
15. ✅ Custom exceptions for domain errors
16. ✅ Consistent error handling with logging
17. ✅ Appropriate logging levels

### **Naming Conventions:**
18. ✅ Class: `{Purpose}{Type}Repository`
19. ✅ File: `{type}_repository.py`
20. ✅ Methods: `get_`, `fetch_`, `save_`, `load_`, `check_`, `validate_`
21. ✅ Private methods: `_method_name`

### **Test Organization:**
22. ✅ Tests organized by SCENARIO (not decorator type)
23. ✅ Section headers separate scenarios
24. ✅ Given/When/Then in sequence per scenario
25. ✅ Realistic mock data
26. ✅ Consistent fixture naming

---

## ✅ Checklist for New Repositories

Use this checklist when creating or reviewing repositories:

**File Structure:**
- [ ] Module docstring with purpose
- [ ] Shebang line (`#!/usr/bin/env python3`)
- [ ] Organized imports (future, stdlib, core, local)
- [ ] Custom exceptions defined (if needed)
- [ ] Dataclasses defined (if needed)

**Class Structure:**
- [ ] Inherits from `Repository`
- [ ] Class-level constants (if needed)
- [ ] `__init__` calls `super().__init__(logger)`
- [ ] Logger is last parameter
- [ ] Dependencies stored as instance variables

**Method Organization:**
- [ ] PUBLIC METHODS section with header
- [ ] PRIVATE HELPER METHODS section with header
- [ ] Public methods have full docstrings
- [ ] Private methods have brief docstrings
- [ ] Methods follow naming conventions

**Code Quality:**
- [ ] Type hints on all parameters and returns
- [ ] Error handling with logging
- [ ] Custom exceptions raised appropriately
- [ ] Logging at appropriate levels
- [ ] No hardcoded values (use constants)

**Testing:**
- [ ] Tests organized by scenario
- [ ] Section headers separate scenarios
- [ ] Given/When/Then in sequence
- [ ] Realistic mock data
- [ ] All scenarios covered
- [ ] **Tests call repository methods** (not just manipulate test_context)
- [ ] **Use real repository instance** (not mocked)
- [ ] **Mock only external dependencies** (APIs, file I/O)

---

## 🧪 Repository Testing Standards (Added 2025-10-10)

### **Standard 20: Repository Tests Must Call Real Methods**

**Observation:** Step 4 repository tests achieved 10/10 quality by calling actual repository methods.

**Pattern:**
```python
# ✅ CORRECT - Tests real repository
@when("retrieving weather data")
def retrieve_data(test_context, weather_data_repo, config):
    result = weather_data_repo.get_weather_data_for_period(
        target_yyyymm="202506",
        target_period="A",
        config=config
    )  # Actually runs repository code
    test_context['result'] = result

# ❌ WRONG - Only manipulates test_context
@when("retrieving weather data")
def retrieve_data(test_context):
    test_context['result'] = {'mock': 'data'}
    # Never calls actual repository!
```

**Key Difference from Step Testing:**
- **Steps:** Call `step.execute()`
- **Repositories:** Call specific repository methods
- **Both:** Test real code execution

---

### **Standard 21: Use Real Repository Instance**

**Pattern:**
```python
@pytest.fixture
def weather_data_repo(
    mock_csv_repo,
    mock_weather_api_repo,
    mock_weather_file_repo,
    test_logger
):
    """Create WeatherDataRepository with mocked dependencies."""
    # ✅ Create REAL repository instance
    repo = WeatherDataRepository(
        coordinates_repo=mock_csv_repo,
        weather_api_repo=mock_weather_api_repo,
        weather_file_repo=mock_weather_file_repo,
        logger=test_logger
    )
    return repo  # Real instance, not mocked!
```

**What to Mock:**
- ✅ External APIs (weather API, elevation API)
- ✅ File I/O operations (CSV, JSON)
- ✅ Database access
- ❌ The repository itself
- ❌ Repository logic

---

### **Standard 22: Configure Mocks Per-Scenario**

**Pattern:**
```python
@pytest.fixture
def mock_weather_file_repo(mocker):
    """Mock WeatherFileRepository."""
    repo = mocker.Mock()
    # Default configuration
    repo.get_downloaded_stores.return_value = set()
    return repo

@given("weather data files exist for some stores")
def setup_existing_files(test_context, mock_weather_file_repo):
    """Configure mock for this specific scenario."""
    # ✅ Configure mock to match scenario
    mock_weather_file_repo.get_downloaded_stores.return_value = {'1001', '1002'}
    test_context['existing_files'] = ['1001', '1002']
```

**Key Insight:** Mocks need scenario-specific configuration to enable proper testing.

---

### **Standard 23: Implement Abstract Methods**

**Problem:** Repository inherits from base class with abstract methods.

**Solution:**
```python
class MyRepository(Repository):
    def get_all(self) -> List[Dict[str, Any]]:
        """Required by base class but not used by this repository."""
        self.logger.warning(
            "get_all() called - use specific_method() instead",
            self.repo_name
        )
        return []
    
    def save(self, data: pd.DataFrame) -> None:
        """Required by base class but not used by this repository."""
        self.logger.warning(
            "save() called - data is saved incrementally",
            self.repo_name
        )
```

**Key Points:**
- Implement even if not used
- Log warnings to guide users
- Return safe defaults

---

### **Standard 24: Test Quality Checklist**

**Use for every repository test file:**

✅ **Tests call real code**
- Call repository methods directly
- Don't just manipulate test_context

✅ **Use real instances**
- Create real repository instances
- Don't mock the repository itself

✅ **Mock only dependencies**
- External APIs
- File I/O
- Database access

✅ **Organize by scenario**
- Add scenario headers
- Group related functions
- Match feature file order

✅ **Configure mocks properly**
- Return appropriate test data
- Configure per-scenario in @given steps

✅ **Verify actual behavior**
- Check real results
- Not just mock calls
- Verify repository logic

---

## 📚 References

**Analyzed Files:**
- `src/repositories/base.py` - Base pattern
- `src/repositories/csv_repository.py` - Multiple repositories
- `src/repositories/weather_api_repository.py` - API interactions
- `src/repositories/tracking_repository.py` - File tracking
- `src/steps/extract_coordinates_step.py` - Step pattern
- `tests/step_definitions/test_step4_weather_data.py` - Test pattern

**Related Documents:**
- [`docs/process_guides/code_design_standards.md`](code_design_standards.md) - Overall design standards
- [`docs/process_guides/CONVERTING_STEP_TO_REPOSITORY.md`](CONVERTING_STEP_TO_REPOSITORY.md) - Conversion process
- [`docs/process_guides/REFACTORING_PROCESS_GUIDE.md`](REFACTORING_PROCESS_GUIDE.md) - Refactoring workflow

---

**Status:** ✅ COMPLETE - Ready to use for Step 4 repository conversion
