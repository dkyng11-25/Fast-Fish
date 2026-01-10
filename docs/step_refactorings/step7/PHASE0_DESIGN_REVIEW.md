# Phase 0: Design Review Gate - Step 7

**Date:** 2025-11-03  
**Reviewer:** AI Agent  
**Status:** 🔍 IN PROGRESS

---

## 📋 Reference Comparison Checklist

### Step 5 Implementation Review

**File Analyzed:** `src/steps/feels_like_temperature_step.py`

#### ✅ Key Patterns Observed in Step 5:

**1. Import Organization:**
```python
# ✅ ALL imports at top of file (lines 11-21)
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime
import os
from pathlib import Path
from core.step import Step
from core.context import StepContext
from core.logger import PipelineLogger
from core.exceptions import DataValidationError
```
- **NO inline imports**
- **NO imports in functions**
- All imports grouped at top

**2. Class Structure:**
```python
class FeelsLikeTemperatureStep(Step):
    def __init__(self, repos, config, logger, ...):
        # Inject dependencies
        
    def setup(self, context: StepContext) -> StepContext:
        # Load data via repositories
        
    def apply(self, context: StepContext) -> StepContext:
        # Business logic HERE
        # Calculate metrics at END of apply
        
    def validate(self, context: StepContext) -> None:  # ✅ Returns None
        # Validate using pre-calculated metrics
        # Raise DataValidationError on failure
        
    def persist(self, context: StepContext) -> StepContext:
        # Save results via repositories
```

**3. VALIDATE Phase Pattern (CRITICAL):**
```python
def validate(self, context: StepContext) -> None:  # ✅ Returns None
    """
    Validate calculation results.
    
    Raises:
        DataValidationError: If validation fails
    """
    processed_weather = context.data.get('processed_weather')
    
    # ✅ Check 1: Data exists
    if processed_weather is None or processed_weather.empty:
        raise DataValidationError("No processed weather data")
    
    # ✅ Check 2: Required columns
    required_cols = ['store_code', 'feels_like_temperature', 'temperature_band']
    missing_cols = [col for col in required_cols if col not in processed_weather.columns]
    
    if missing_cols:
        raise DataValidationError(f"Missing required columns: {missing_cols}")
    
    # ✅ Check 3: No null values
    null_counts = processed_weather[required_cols].isnull().sum()
    if null_counts.any():
        raise DataValidationError(f"Null values found: {null_counts[null_counts > 0].to_dict()}")
    
    # ✅ Log success
    self.logger.info(f"Validation passed: {len(processed_weather)} stores with valid data")
```

**Key Observations:**
- ✅ Returns `-> None` (NOT `-> StepContext`)
- ✅ Only validates (does NOT calculate)
- ✅ Raises `DataValidationError` on failure
- ✅ Uses pre-calculated data from context
- ✅ No metrics calculation here

**4. Business Logic Location:**
- ✅ ALL business logic in `apply()` method
- ✅ Helper methods are private (`_method_name`)
- ✅ NO separate algorithm classes
- ✅ NO `src/algorithms/` folder

**5. Dependency Injection:**
```python
def __init__(
    self,
    weather_data_repo,      # ✅ Repository
    altitude_repo,          # ✅ Repository
    temperature_output_repo,# ✅ Repository
    bands_output_repo,      # ✅ Repository
    config: FeelsLikeConfig,# ✅ Configuration
    logger: PipelineLogger, # ✅ Logger
    ...
):
```
- ✅ Repositories injected
- ✅ Configuration injected
- ✅ Logger injected
- ❌ NO algorithm classes injected

---

## 🔍 Current Step 7 Analysis

**File:** `src/step7_missing_category_rule.py`  
**Size:** 1,624 lines ⚠️ **3.2x OVER 500 LOC LIMIT**

### ❌ Critical Issues Found:

#### Issue #1: Inline Imports (Lines 1-7)
```python
# ❌ WRONG - Imports scattered throughout file
from typing import Tuple, List, Optional  # Line 2
import pandas as pd  # Line 3
import os  # Line 4
from output_utils import create_output_with_symlinks  # Line 5
import os as _os  # Line 6 (duplicate!)
```

**Problem:** Imports should ALL be at top of file in organized groups.

#### Issue #2: Functions Before Main Class
```python
# ❌ WRONG - Helper functions defined at module level (lines 9-55)
def _previous_half_month(yyyymm: str, period: str) -> Tuple[str, str]:
    # ...

def _average_recent_sales(...) -> Optional[pd.DataFrame]:
    # ...
```

**Problem:** These should be private methods of the Step class or in a separate utility module.

#### Issue #3: File Size Violation
- **Current:** 1,624 lines
- **Limit:** 500 lines
- **Violation:** 1,124 lines over limit (3.2x)

**Required:** Mandatory CUPID-based modularization

#### Issue #4: No 4-Phase Pattern
```python
# ❌ WRONG - No clear setup/apply/validate/persist structure
# File is procedural script, not Step class
```

**Problem:** Must follow 4-phase Step pattern like Step 5.

#### Issue #5: Hard-Coded Paths
```python
# ❌ WRONG - Hard-coded paths (line 170)
base_path = "../data/api_data/"
```

**Problem:** Should use repository pattern for data access.

#### Issue #6: Global Configuration
```python
# ❌ WRONG - Global variables (lines 134-153)
ANALYSIS_LEVEL = "spu"
DATA_PERIOD_DAYS = 15
USE_BLENDED_SEASONAL: bool = False
```

**Problem:** Should be in configuration dataclass injected via constructor.

---

## 🎯 Design Decisions for Step 7

### Decision 1: Modularization Strategy

**Problem:** 1,624 lines → need to reduce to ≤ 500 lines

**Solution:** Extract components following CUPID principles

**Proposed Structure:**
```
src/steps/
  └── missing_category_rule_step.py        (≤500 LOC - main step)

src/components/
  └── missing_category/
      ├── __init__.py
      ├── seasonal_data_loader.py          (≤200 LOC)
      ├── cluster_analyzer.py              (≤200 LOC)
      ├── quantity_calculator.py           (≤200 LOC)
      └── sell_through_validator.py        (≤200 LOC)

src/repositories/
  └── (existing repositories)
```

**Justification:**
- Each component has single responsibility (Unix Philosophy)
- Components are composable and reusable
- Clear business domain naming
- Follows Steps 4 & 5 pattern

### Decision 2: VALIDATE Phase Design

**Pattern from Step 5:**
```python
def validate(self, context: StepContext) -> None:
    """Validate missing category rule results."""
    results = context.data.get('results')
    
    # Check 1: Results exist
    if results is None or results.empty:
        raise DataValidationError("No missing category recommendations generated")
    
    # Check 2: Required columns
    required_cols = ['str_code', 'cluster_id', 'sub_cate_name', 'recommended_quantity']
    missing_cols = [col for col in required_cols if col not in results.columns]
    if missing_cols:
        raise DataValidationError(f"Missing required columns: {missing_cols}")
    
    # Check 3: Data quality
    if results['recommended_quantity'].min() < 0:
        raise DataValidationError("Negative quantities found in recommendations")
    
    self.logger.info(f"Validation passed: {len(results)} recommendations")
```

**Key Points:**
- ✅ Returns `-> None`
- ✅ Only validates
- ✅ Raises DataValidationError
- ✅ No calculations

### Decision 3: Business Logic Location

**Following Step 5 Pattern:**
- ✅ ALL business logic in `apply()` method
- ✅ Private helper methods (`_method_name`)
- ✅ NO separate algorithm classes
- ✅ NO `src/algorithms/` folder

**Justification:** Matches Steps 4 & 5 proven pattern

### Decision 4: Import Organization

**Following Step 5 Pattern:**
```python
# Standard library
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import os

# Third-party
import pandas as pd
import numpy as np

# Internal
from core.step import Step
from core.context import StepContext
from core.logger import PipelineLogger
from core.exceptions import DataValidationError
from repositories.csv_file_repository import CsvFileRepository
```

**Key Points:**
- ✅ ALL imports at top
- ✅ Grouped by category
- ✅ NO inline imports
- ✅ NO imports in functions

### Decision 5: Configuration Management

**Following Step 5 Pattern:**
```python
@dataclass
class MissingCategoryConfig:
    """Configuration for missing category rule."""
    analysis_level: str  # "subcategory" or "spu"
    min_cluster_stores_selling: float
    min_cluster_sales_threshold: float
    min_opportunity_value: float
    data_period_days: int = 15
    target_period_days: int = 15
    use_blended_seasonal: bool = False
    seasonal_weight: float = 0.6
    recent_weight: float = 0.4
```

**Justification:** Matches Step 5 configuration pattern

---

## 📊 Comparison Summary

| Aspect | Step 5 (Reference) | Current Step 7 | Step 7 Refactored Design |
|--------|-------------------|----------------|--------------------------|
| **File Size** | 599 LOC | 1,624 LOC ❌ | ≤500 LOC ✅ |
| **Import Location** | Top of file ✅ | Scattered ❌ | Top of file ✅ |
| **VALIDATE Returns** | `-> None` ✅ | N/A (no class) ❌ | `-> None` ✅ |
| **VALIDATE Purpose** | Validates ✅ | N/A ❌ | Validates ✅ |
| **Business Logic** | In apply() ✅ | Procedural ❌ | In apply() ✅ |
| **Algorithms Folder** | NO ✅ | N/A | NO ✅ |
| **Dependency Injection** | YES ✅ | NO ❌ | YES ✅ |
| **Repository Pattern** | YES ✅ | NO ❌ | YES ✅ |
| **4-Phase Pattern** | YES ✅ | NO ❌ | YES ✅ |

---

## ⚠️ STOP Criteria Check

### ❌ STOP - Issues Found:

- ❌ File size: 1,624 LOC (3.2x over limit)
- ❌ No 4-phase Step pattern
- ❌ Inline imports used
- ❌ No VALIDATE phase design
- ❌ Hard-coded paths (no repository pattern)
- ❌ Global configuration variables

### ✅ Required Actions Before Phase 1:

1. **Design modularization strategy** (extract components)
2. **Design VALIDATE phase** (returns None, validates only)
3. **Design repository interfaces** (for data access)
4. **Design configuration dataclass** (no globals)
5. **Plan import organization** (all at top)
6. **Document all design decisions**

---

## 📝 Next Steps

**Before proceeding to Phase 1:**

1. ✅ Complete this design review document
2. ⏳ Create `REFERENCE_COMPARISON.md` with detailed comparison
3. ⏳ Create `DESIGN_DECISIONS.md` with modularization plan
4. ⏳ Create `COMPONENT_EXTRACTION_PLAN.md` for CUPID modularization
5. ⏳ Get sign-off on design

**Only proceed to Phase 1 after ALL design documents are complete and approved.**

---

## 🎯 Key Takeaways

### What We Learned from Step 5:

1. **VALIDATE returns None** - not StepContext
2. **VALIDATE validates** - doesn't calculate
3. **Business logic in apply()** - not separate classes
4. **All imports at top** - no inline imports
5. **Repository pattern** - no hard-coded paths
6. **Configuration dataclass** - no global variables
7. **File size ≤ 500 LOC** - mandatory modularization

### Critical Mistakes to Avoid:

1. ❌ Creating `src/algorithms/` folder
2. ❌ Making VALIDATE calculate metrics
3. ❌ Using inline imports
4. ❌ Exceeding 500 LOC limit
5. ❌ Hard-coding file paths
6. ❌ Using global configuration

---

**Status:** Phase 0 design review identifies significant refactoring required. Must complete design documents before Phase 1.
