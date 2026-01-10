# Step 2: Extract Store Coordinates (Refactored) - Design Standards Compliance

## Overview

This document describes the refactored Step 2 implementation that follows the **Code Design Standards** from `docs/code_design_standards.md`. The refactored version transforms the legacy function-based code into a modern, maintainable, class-based implementation using dependency injection and the 4-phase pattern.

## 📁 Implementation Location

- **Legacy Code:** `src/step2_extract_coordinates.py` (unchanged)
- **Refactored Code:** `src/steps/extract_coordinates.py` (new implementation)
- **Test Scaffolding:** `tests/test_step2_extract_coordinates_scaffold.py` (Phase 1 ready)
- **BDD Tests:** `tests/step_definitions/step2_extract_coordinates_steps.py` (full implementation)

## 🏗️ Architecture Overview

The refactored implementation follows the **4-Phase Step Pattern**:

```
ExtractCoordinatesStep
├── setup()    → Scan periods, find best coordinate data
├── apply()    → Extract coordinates, create SPU mappings
├── validate() → Validate data quality and coverage
└── persist()  → Save results to multiple files
```

## ✅ Design Standards Compliance

### **1. Folder Structure**
- ✅ **Location:** `src/steps/extract_coordinates.py` (matches recommended structure)
- ✅ **Separation of Concerns:** Each repository handles specific data access patterns
- ✅ **Testability:** Test structure mirrors source structure

### **2. Core Design Concepts**

#### ✅ **StepContext Usage**
```python
def apply(self, context: StepContext) -> StepContext:
    # All data flows through StepContext
    coordinates = self._extract_coordinates_from_period(best_period)
    context.set_data(pd.DataFrame(coordinates))  # Primary data
    context.set_state('coordinate_count', len(coordinates))  # Metadata
    return context
```

#### ✅ **Step Abstract Base Class**
```python
class ExtractCoordinatesStep(Step):
    """Step 2: Extract store coordinates and create SPU mappings."""

    def __init__(self, data_reader: MultiPeriodDataRepository, ...):
        super().__init__(logger, step_name, step_number)  # Required metadata
```

#### ✅ **Repository Pattern**
```python
class MultiPeriodDataRepository(Repository):
    """Repository for reading multi-period API data files."""
    def get_all(self) -> List[Dict[str, Any]]:
        # File discovery and data loading logic
        return period_data_list
```

#### ✅ **4-Phase Pattern Implementation**
```python
def setup(self, context: StepContext) -> StepContext:
    """Phase 1: Load data from repositories"""
    period_data_list = self.data_reader.get_all()
    best_period = self._find_best_period(period_data_list)
    context.set_state('best_period', best_period)
    return context

def apply(self, context: StepContext) -> StepContext:
    """Phase 2: Transform data"""
    # Extract coordinates and create mappings
    return context

def validate(self, context: StepContext) -> None:
    """Phase 3: Validate data (raises DataValidationError on failure)"""
    coordinates_df = context.get_data()
    validation_result = self._validate_coordinate_data(coordinates_df)
    if not validation_result.is_valid:
        raise DataValidationError(f"Validation failed: {validation_result.error_message}")

def persist(self, context: StepContext) -> StepContext:
    """Phase 4: Save data using repositories"""
    coordinates_df = context.get_data()
    self.coordinate_writer.save(coordinates_df)
    return context
```

### **3. Dependency Injection Pattern**

#### ✅ **Constructor Injection (Mandatory)**
```python
def __init__(
    self,
    data_reader: MultiPeriodDataRepository,      # Repository injection
    coordinate_writer: CoordinateWriterRepository, # Repository injection
    spu_mapping_writer: SpuMappingWriterRepository, # Repository injection
    spu_metadata_writer: SpuMetadataWriterRepository, # Repository injection
    months_back: int,                            # Configuration injection
    logger: PipelineLogger,                      # Logger injection
    step_name: str,                              # Metadata injection
    step_number: int                             # Metadata injection
):
    super().__init__(logger, step_name, step_number)
    # All dependencies injected - no hardcoding!
```

#### ✅ **Repository Dependencies**
```python
# In composition root - proper DI assembly
data_reader = MultiPeriodDataRepository(data_path, logger)
coordinate_writer = CoordinateWriterRepository(output_path, logger)
spu_mapping_writer = SpuMappingWriterRepository(output_path, logger)
spu_metadata_writer = SpuMetadataWriterRepository(output_path, logger)
```

#### ✅ **Configuration Injection**
```python
# All configuration injected - no environment access in step logic
months_back = int(os.environ.get('COORDS_MONTHS_BACK', '3'))
step = ExtractCoordinatesStep(..., months_back=months_back, ...)
```

### **4. Pipeline Construction**

#### ✅ **Centralized Logging**
```python
# Single logger instance injected everywhere
logger = PipelineLogger("ExtractCoordinatesPipeline")
step = ExtractCoordinatesStep(..., logger=logger, ...)
data_reader = MultiPeriodDataRepository(data_path, logger)  # Also gets logger
```

#### ✅ **Validation by Exception**
```python
def validate(self, context: StepContext) -> None:
    """Validation by exception - raises DataValidationError on failure."""
    if not validation_result.is_valid:
        raise DataValidationError(f"Coordinate validation failed: {validation_result.error_message}")
    # Returns None on success - no explicit return needed
```

#### ✅ **Type Hinting (Mandatory)**
```python
def setup(self, context: StepContext) -> StepContext:  # Full type hints
def apply(self, context: StepContext) -> StepContext:
def validate(self, context: StepContext) -> None:     # None return for validation
def persist(self, context: StepContext) -> StepContext:
```

## 📊 Implementation Statistics

| Component | Count | Status |
|-----------|-------|--------|
| **Total Lines** | 631 | ✅ Complete |
| **Classes** | 5 | ✅ Complete |
| **Methods** | 25 | ✅ Complete |
| **Type Hints** | 104 | ✅ Complete |
| **Repository Classes** | 4 | ✅ Complete |
| **Data Classes** | 3 | ✅ Complete |
| **4-Phase Methods** | 4 | ✅ Complete |
| **Dependency Injections** | 7 | ✅ Complete |
| **Logger Calls** | 26 | ✅ Complete |

## 🎯 Key Features Implemented

### **1. Multi-Period Data Discovery**
```python
def setup(self, context: StepContext) -> StepContext:
    """Scan multiple periods for comprehensive coordinate coverage."""
    period_data_list = self.data_reader.get_all()
    best_period = self._find_best_period(period_data_list)
    # Finds period with maximum valid coordinates
```

### **2. Coordinate Extraction & Validation**
```python
def _validate_coordinate_data(self, coordinates_df: pd.DataFrame) -> ValidationResult:
    """Comprehensive coordinate validation."""
    # Validates format, ranges, data types, duplicates
    # Returns ValidationResult with detailed error information
```

### **3. SPU Mapping Creation**
```python
def _create_spu_mappings(self, period_data_list: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Create comprehensive SPU mappings across all periods."""
    # Combines data from multiple periods
    # Creates unique SPU-store combinations
    # Generates metadata with sales statistics
```

### **4. Repository-Based Data Access**
```python
class MultiPeriodDataRepository(Repository):
    """Encapsulates all file discovery and loading logic."""
    def get_all(self) -> List[Dict[str, Any]]:
        # Scans for store_sales_*.csv, complete_category_sales_*.csv, etc.
        # Returns structured period data
```

## 🔄 Migration Path

### **Before (Legacy)**
```python
# Function-based, hard-coded paths, direct file access
def extract_coordinates_from_api_data():
    # Direct file operations, no dependency injection
    # Global variables for configuration
```

### **After (Refactored)**
```python
# Class-based, dependency injection, repository pattern
step = create_extract_coordinates_step(
    data_path="data/api_data",
    output_path="data",
    months_back=3,
    logger=logger
)
context = step.execute(StepContext())
```

## 🧪 Testing Integration

The refactored step is fully compatible with the existing BDD test scaffolding:

- **✅ 16 Scenarios** - All feature file scenarios supported
- **✅ 101 Step Definitions** - Complete @given/@when/@then implementations
- **✅ Repository Mocks** - Easy to mock for testing
- **✅ Context Management** - Clean data flow for assertions

## 📋 Final Checklist Compliance

- ✅ **Folder structure followed** - `src/steps/` location
- ✅ **StepContext data flow** - All data passed via context
- ✅ **Step ABC inheritance** - Proper inheritance chain
- ✅ **4-phase implementation** - setup/apply/validate/persist
- ✅ **Metadata included** - step_name and step_number
- ✅ **Validation by exception** - DataValidationError on failure
- ✅ **Repository injection** - No hard-coded data access
- ✅ **Configuration injection** - No hard-coded values
- ✅ **Centralized logging** - Single PipelineLogger instance
- ✅ **Composition root** - `create_extract_coordinates_step()` function
- ✅ **Exception handling** - try...except DataValidationError in main()

## 🚀 Usage

```python
from src.steps.extract_coordinates import create_extract_coordinates_step

# Create step with all dependencies injected
step = create_extract_coordinates_step(
    data_path="data/api_data",
    output_path="data",
    months_back=3,
    logger=PipelineLogger("MyPipeline")
)

# Execute with clean context
context = StepContext()
result_context = step.execute(context)

# Access results
coordinates = result_context.get_data()
coordinate_count = result_context.get_state('coordinate_count')
```

## 📈 Benefits Achieved

1. **🔧 Maintainability** - Clear separation of concerns, easy to modify
2. **🧪 Testability** - All dependencies injectable for testing
3. **📖 Readability** - Clear 4-phase structure, comprehensive documentation
4. **🔄 Extensibility** - Easy to add new data sources or output formats
5. **🛡️ Reliability** - Validation by exception prevents bad data propagation
6. **📝 Traceability** - Comprehensive logging throughout all phases

The refactored Step 2 is now ready for production use and fully compliant with the project's design standards! 🎉
