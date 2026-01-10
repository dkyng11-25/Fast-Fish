# Converting a Step to a Repository - Process Guide

**Date:** 2025-10-10  
**Status:** 🚧 IN PROGRESS (Being created during Step 4 conversion)  
**Purpose:** Document the process of converting a step implementation to a repository

---

## 🎯 When to Use This Guide

Use this guide when you discover that a "step" is actually just data retrieval/formatting with no business logic.

**Signs a Step Should Be a Repository:**
- ✅ Only retrieves and formats data
- ✅ No business logic or transformation
- ✅ Data is used by another step
- ✅ All APPLY phase is just I/O operations
- ✅ Could be called from multiple steps

**Example:** Step 4 (Weather Data Download) - only retrieves weather data for Step 5 to process.

---

## 📋 Prerequisites

Before starting:
- [ ] Read the step implementation completely
- [ ] Identify all behaviors (SETUP/APPLY/VALIDATE/PERSIST)
- [ ] Confirm it's pure data retrieval (no business logic)
- [ ] Identify which step(s) will use this repository
- [ ] Review existing repositories it depends on
- [ ] **Read [`REPOSITORY_DESIGN_STANDARDS.md`](REPOSITORY_DESIGN_STANDARDS.md)** - Understand implied standards

---

## 🔄 The Conversion Process

### **Phase 1: Analysis (30-60 minutes)**

#### **Step 1.1: Analyze Current Step Implementation**

**What to document:**
1. What data does it retrieve?
2. What repositories does it use?
3. What is the public interface needed?
4. What private helper methods exist?
5. What configuration is needed?

**Create:** `docs/step_refactorings/step{N}/STEP{N}_BEHAVIOR_ANALYSIS_FOR_REPO.md`

**Template:**
```markdown
# Step {N} Behavior Analysis - For Repository Conversion

## What Step {N} Does
[Purpose and overview]

## Behavior by Phase
### SETUP Phase
- What data is loaded
- What is initialized

### APPLY Phase
- What operations are performed
- What data is retrieved

### VALIDATE Phase
- What validations are performed

### PERSIST Phase
- What data is saved

## Repository Design Decision
[Which repository structure to use]

## What Goes Where
[What goes in new repository vs existing repos]
```

**Example:** See `docs/step_refactorings/step4/STEP4_BEHAVIOR_ANALYSIS_FOR_REPO.md`

---

#### **Step 1.2: Design Repository Interface**

**Questions to answer:**
1. What will the main public method be called?
2. What parameters does it need?
3. What does it return?
4. What dependencies (other repos) does it need?

**Document the interface:**
```python
class {Name}Repository(Repository):
    """Repository for {purpose}."""
    
    def __init__(
        self,
        dependency_repo_1: Type1,
        dependency_repo_2: Type2,
        logger: PipelineLogger
    ):
        """Initialize with dependencies."""
        
    def get_{data}_for_{context}(
        self,
        param1: str,
        param2: str
    ) -> Dict[str, Any]:
        """
        Main public method.
        
        Args:
            param1: Description
            param2: Description
            
        Returns:
            Dictionary with retrieved data
        """
```

**Approval Point:** Review interface design before proceeding.

---

### **Phase 2: Create Repository Structure (30-60 minutes)**

#### **Step 2.1: Create Repository File**

```bash
touch src/repositories/{name}_repository.py
```

#### **Step 2.2: Set Up Basic Structure**

**Template to start with:**
```python
#!/usr/bin/env python3
"""
{Name} Repository

Purpose: {Brief description of what data this repository manages}

This repository was converted from Step {N} because it only performs
data retrieval with no business logic.

Author: Data Pipeline
Date: {Date}
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
import pandas as pd

from core.logger import PipelineLogger
from repositories.base import Repository
# Import other dependencies


class {Name}Repository(Repository):
    """Repository for {purpose}."""
    
    def __init__(
        self,
        # Dependencies
        logger: PipelineLogger
    ):
        """
        Initialize {Name} Repository.
        
        Args:
            logger: Pipeline logger
        """
        super().__init__(logger)
        # Store dependencies
    
    # ========================================================================
    # PUBLIC METHODS
    # ========================================================================
    
    def get_{data}_for_{context}(
        self,
        param1: str,
        param2: str
    ) -> Dict[str, Any]:
        """
        Main public method for retrieving data.
        
        Args:
            param1: Description
            param2: Description
            
        Returns:
            Dictionary containing:
            - key1: Description
            - key2: Description
        """
        # Implementation will go here
        pass
    
    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================
    
    # Helper methods will go here
```

**Approval Point:** Review basic structure before adding logic.

---

#### **Step 2.3: Move Logic from Step to Repository**

**Process:**
1. **Start with SETUP logic** → Move to initialization or private setup method
2. **Move APPLY logic** → Move to main public method
3. **Move VALIDATE logic** → Move to validation method or inline
4. **Move PERSIST logic** → Move to save method or inline
5. **Move all private helper methods** → Keep as private methods

**Key Changes:**
- ❌ Remove `Step` inheritance → ✅ Use `Repository` inheritance
- ❌ Remove `execute()` method → ✅ Create specific public methods
- ❌ Remove `StepContext` → ✅ Return data directly
- ❌ Remove step-specific config → ✅ Use method parameters

**Example Transformation:**

**Before (Step):**
```python
class WeatherDataDownloadStep(Step):
    def setup(self, context: StepContext) -> StepContext:
        coordinates = self.coordinates_repo.get_all()
        context['coordinates'] = coordinates
        return context
    
    def apply(self, context: StepContext) -> StepContext:
        coordinates = context['coordinates']
        weather_data = self._download_weather(coordinates)
        context['weather_data'] = weather_data
        return context
```

**After (Repository):**
```python
class WeatherDataRepository(Repository):
    def get_weather_data_for_period(
        self,
        target_yyyymm: str,
        target_period: str
    ) -> Dict[str, Any]:
        # Setup logic inline
        coordinates = self.coordinates_repo.get_all()
        
        # Apply logic inline
        weather_data = self._download_weather(coordinates)
        
        # Return directly
        return {
            'weather_data': weather_data,
            'coordinates': coordinates
        }
```

**Approval Point:** Review each section of moved logic before proceeding.

---

### **Phase 3: Update Tests (1-2 hours)**

#### **Step 3.1: Analyze Current Tests**

**Questions:**
1. What are the tests currently testing?
2. Do they test the step's execute() method?
3. What fixtures are used?
4. What scenarios are covered?

#### **Step 3.2: Update Test Structure**

**Changes needed:**
- ❌ Remove step instance fixture → ✅ Create repository instance fixture
- ❌ Remove context fixture → ✅ Test returns directly
- ❌ Test execute() method → ✅ Test repository methods

**Example Transformation:**

**Before (Testing Step):**
```python
@pytest.fixture
def step_instance(mock_coords_repo, mock_weather_api):
    return WeatherDataDownloadStep(
        coordinates_repo=mock_coords_repo,
        weather_api_repo=mock_weather_api,
        ...
    )

@when('downloading weather data')
def download_weather(test_context, step_instance):
    result = step_instance.execute()
    test_context['result'] = result

@then('weather data should be downloaded')
def verify_download(test_context):
    assert test_context['result']['weather_data'] is not None
```

**After (Testing Repository):**
```python
@pytest.fixture
def weather_repo(mock_coords_repo, mock_weather_api):
    return WeatherDataRepository(
        coordinates_repo=mock_coords_repo,
        weather_api_repo=mock_weather_api,
        ...
    )

@when('downloading weather data')
def download_weather(test_context, weather_repo):
    result = weather_repo.get_weather_data_for_period('202506', 'A')
    test_context['result'] = result

@then('weather data should be downloaded')
def verify_download(test_context):
    assert test_context['result']['weather_data'] is not None
```

**Approval Point:** Review test changes before running.

---

#### **Step 3.3: Run Tests**

```bash
pytest tests/step_definitions/test_step{N}_*.py -v
```

**Expected:** Tests should pass with new repository structure.

**If tests fail:**
1. Review error messages
2. Check fixture setup
3. Verify method signatures
4. Check return values

---

### **Phase 4: Cleanup (30 minutes)**

#### **Step 4.1: Delete Step Files**

**Files to delete:**
```bash
# Delete step implementation
rm src/steps/{name}_step.py

# Delete CLI script (if exists)
rm src/step{N}_{name}_refactored.py

# Delete __pycache__
rm -rf src/steps/__pycache__/{name}_step*.pyc
```

**Approval Point:** Confirm files to delete before removing.

---

#### **Step 4.2: Move Factory to Utils**

```bash
# Create utils folder if it doesn't exist
mkdir -p src/utils

# Move factory
mv src/steps/{name}_factory.py src/utils/

# Update imports in factory
# Change: from steps.{name}_step import ...
# To: from repositories.{name}_repository import ...
```

**Approval Point:** Review factory changes before committing.

---

#### **Step 4.3: Update Imports Across Codebase**

**Find all files that import the step:**
```bash
grep -r "from steps.{name}_step import" src/
grep -r "from src.steps.{name}_step import" .
```

**Update each file:**
- Change: `from steps.{name}_step import {Name}Step`
- To: `from repositories.{name}_repository import {Name}Repository`

**Approval Point:** Review all import changes.

---

### **Phase 5: Integration & Documentation (30-60 minutes)**

#### **Step 5.1: Update Repository Exports**

**File:** `src/repositories/__init__.py`

```python
from .{name}_repository import {Name}Repository

__all__ = [
    # ... existing exports ...
    "{Name}Repository",
]
```

#### **Step 5.2: Create Usage Example**

**Document how to use the repository:**

```python
# Example: Using WeatherDataRepository in Step 5

class TemperatureCalculationStep(Step):
    def __init__(
        self,
        weather_data_repo: WeatherDataRepository,  # Inject repository
        ...
    ):
        super().__init__(...)
        self.weather_data_repo = weather_data_repo
    
    def setup(self, context: StepContext) -> StepContext:
        # Use repository to get weather data
        result = self.weather_data_repo.get_weather_data_for_period(
            target_yyyymm='202506',
            target_period='A',
            months_back=3
        )
        
        # Store in context for apply phase
        context['weather_data'] = result['weather_data']
        context['altitude_data'] = result['altitude_data']
        
        return context
    
    def apply(self, context: StepContext) -> StepContext:
        # Process the weather data (business logic)
        weather_data = context['weather_data']
        feels_like = self._calculate_feels_like_temperature(weather_data)
        context['processed_weather'] = feels_like
        return context
```

#### **Step 5.3: Update Documentation**

**Create/Update these documents:**

1. **Conversion Summary:**
   - `docs/step_refactorings/step{N}/CONVERSION_TO_REPOSITORY.md`
   - What was changed
   - Why it was changed
   - How to use the repository

2. **Update Master Index:**
   - `docs/INDEX.md`
   - Add note about repository conversion

3. **Update Process Guide:**
   - This document!
   - Add any lessons learned

**Template for Conversion Summary:**
```markdown
# Step {N} Conversion to Repository

**Date:** {Date}
**Status:** ✅ COMPLETE

## Why Converted
[Explanation of why this was a repository, not a step]

## What Changed
- Removed: Step implementation
- Created: {Name}Repository
- Updated: Tests to test repository
- Moved: Factory to utils

## How to Use
[Code example showing usage in consuming step]

## Lessons Learned
[Any insights or challenges encountered]
```

---

## ✅ Completion Checklist

**Conversion is complete when:**

- [ ] **Phase 1: Analysis**
  - [ ] Behavior analysis document created
  - [ ] Repository interface designed
  - [ ] Design approved

- [ ] **Phase 2: Repository Creation**
  - [ ] Repository file created
  - [ ] Basic structure approved
  - [ ] Logic moved from step to repository
  - [ ] Each section approved

- [ ] **Phase 3: Tests**
  - [ ] Test structure updated
  - [ ] Tests run and pass
  - [ ] Test changes approved

- [ ] **Phase 4: Cleanup**
  - [ ] Step files deleted
  - [ ] Factory moved to utils
  - [ ] Imports updated across codebase
  - [ ] All changes approved

- [ ] **Phase 5: Documentation**
  - [ ] Repository exported in __init__.py
  - [ ] Usage example created
  - [ ] Conversion summary documented
  - [ ] Master index updated
  - [ ] Process guide updated

---

## 🎯 Success Criteria

**Repository is successful when:**
- ✅ Provides clear public interface
- ✅ Uses existing repositories (composition)
- ✅ No Step inheritance
- ✅ No execute() method
- ✅ Returns data directly (not via context)
- ✅ Tests pass
- ✅ Can be used by consuming steps
- ✅ Documentation complete

---

## 📝 Lessons Learned

**This section will be updated as we complete the Step 4 conversion.**

### **What Worked Well:**
- [To be filled in]

### **Challenges Encountered:**
- [To be filled in]

### **Best Practices:**
- [To be filled in]

### **Things to Avoid:**
- [To be filled in]

---

## 🚀 Next Steps After Conversion

1. Test the repository in isolation
2. Integrate into consuming step (e.g., Step 5)
3. Test end-to-end in pipeline
4. Document any issues or improvements
5. Update this guide with lessons learned

---

**Status:** 🚧 This guide is being created during Step 4 conversion and will be finalized when complete.
