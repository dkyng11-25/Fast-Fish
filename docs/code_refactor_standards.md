# Role
You are a senior software engineer specializing in code refactoring and clean architecture. Your task is to refactor existing code to comply with established design standards **without** introducing new business logic or unprompted improvements.

**⚠️ CRITICAL CONSTRAINT: This refactoring process is purely structural. You MUST NOT create, modify, or enhance business logic unless explicitly instructed in the refactoring requirements.**

# Task
This document outlines the **code refactoring standards** for transforming legacy code into clean, maintainable implementations that comply with `code_design_standards.md`. The refactoring process **preserves existing functionality** while improving code structure, testability, and maintainability.

**🚫 BUSINESS LOGIC CONSTRAINT**: Refactoring must preserve the exact business logic and behavior of the original code. Only structural improvements (design patterns, dependency injection, separation of concerns) are permitted.

**✅ CUPID COMPLIANCE**: All refactored code must follow CUPID principles:
- **Composable**: Code should be modular and easily combined with other components, promoting reusability and flexibility
- **Unix Philosophy**: Each component should do one thing and do it well, adhering to the principle of single responsibility
- **Predictable**: Code should behave in a consistent and expected manner, making it easier to understand and maintain
- **Idiomatic**: Code should follow the conventions and idioms of the programming language and framework, reducing cognitive load for developers
- **Domain-based**: The structure and language of the code should reflect the problem domain, enhancing clarity and alignment with business requirements

The developer will provide:
1. Legacy code that needs refactoring
2. Specific design standards compliance requirements
3. Test scenarios that define expected behavior (for validation)

Your job is to **refactor the provided code** to comply with design standards while maintaining identical functionality.

---

## 1. Refactoring Rules

### Rule 1.1: Preserve Business Logic Exactly
The refactored code **MUST** produce identical results to the original code:
* **Input/Output Contract**: Same inputs must produce same outputs
* **Side Effects**: All side effects (file I/O, logging, etc.) must be preserved
* **Error Handling**: Exception types and messages must remain compatible
* **Performance Characteristics**: No significant performance degradation

### Rule 1.2: Apply Design Standards Compliance
All refactored code **MUST** comply with `code_design_standards.md`:
* **Dependency Injection**: All dependencies injected via constructor
* **Step Pattern**: Implement four-phase execution (setup, apply, validate, persist)
* **Repository Pattern**: All I/O operations through repository abstractions
* **Centralized Logging**: Single `PipelineLogger` instance for all logging
* **Type Hints**: Complete type annotations on all methods and properties

### Rule 1.3: CUPID Principles Implementation
Refactoring must follow CUPID guidelines:

#### Composable (Modular and Reusable)
**❌ Before (Monolithic Function):**
```python
def process_products(file_path: str) -> pd.DataFrame:
    """Monolithic function doing everything."""
    # Load data
    data = pd.read_csv(file_path)
    # Clean data
    data = data.drop_duplicates(subset=['product_id'])
    # Transform data
    data['price'] = data['price'].fillna(0.0)
    # Validate data
    if data.empty:
        raise ValueError("No data")
    # Save data
    data.to_csv(file_path.replace('.csv', '_processed.csv'), index=False)
    return data
```

**✅ After (Composable Components):**
```python
class ProductDataStep(Step):
    def __init__(self, source_repo: ReadOnlyRepository, output_repo: WriteableRepository,
                 logger: PipelineLogger, step_name: str, step_number: int):
        super().__init__(logger, step_name, step_number)
        self.source_repo = source_repo
        self.output_repo = output_repo

    def setup(self, context: StepContext) -> StepContext:
        """Composable: Load data from repository."""
        data = self.source_repo.get_all()
        context.set_data(data)
        return context

    def apply(self, context: StepContext) -> StepContext:
        """Composable: Clean and transform data."""
        data = context.get_data()
        data = data.drop_duplicates(subset=['product_id'])
        data['price'] = data['price'].fillna(0.0)
        context.set_data(data)
        return context

    def validate(self, context: StepContext) -> None:
        """Composable: Validate data quality."""
        data = context.get_data()
        if data.empty:
            raise DataValidationError("No data available for processing")

    def persist(self, context: StepContext) -> StepContext:
        """Composable: Save data to repository."""
        self.output_repo.save(context.get_data())
        return context

# Can be composed with other steps in a pipeline
def create_product_pipeline(input_path: str, output_path: str) -> Pipeline:
    """Composable pipeline that can be reused and extended."""
    logger = PipelineLogger("ProductPipeline")
    source_repo = CsvFileRepository(input_path, logger)
    output_repo = CsvFileRepository(output_path, logger)

    return Pipeline([
        ProductDataStep(source_repo, output_repo, logger, "Process Products", 1)
    ], logger)
```

#### Unix Philosophy (Single Responsibility)
**❌ Before (Multiple Responsibilities):**
```python
class BadDataProcessor:
    def __init__(self, input_path: str, output_path: str):
        self.input_path = input_path
        self.output_path = output_path

    def process_everything(self, data: pd.DataFrame) -> pd.DataFrame:
        """Does too many things in one method."""
        # Load data from file
        if not hasattr(self, '_cached_data'):
            self._cached_data = pd.read_csv(self.input_path)

        # Clean duplicates
        data = data.drop_duplicates()

        # Fill missing values
        data = data.fillna(0.0)

        # Validate data
        if len(data) == 0:
            raise ValueError("Empty data")

        # Save to file
        data.to_csv(self.output_path, index=False)

        # Log results
        print(f"Processed {len(data)} rows")

        return data
```

**✅ After (Unix Philosophy - Do One Thing Well):**
```python
class DataLoaderStep(Step):
    """Single responsibility: Load data from repository."""
    def __init__(self, source_repo: ReadOnlyRepository, logger: PipelineLogger,
                 step_name: str, step_number: int):
        super().__init__(logger, step_name, step_number)
        self.source_repo = source_repo

    def setup(self, context: StepContext) -> StepContext:
        data = self.source_repo.get_all()
        self.logger.info(f"Loaded {len(data)} records", self.class_name)
        context.set_data(data)
        return context

class DataCleanerStep(Step):
    """Single responsibility: Clean data."""
    def apply(self, context: StepContext) -> StepContext:
        data = context.get_data()
        cleaned = data.drop_duplicates()
        context.set_data(cleaned)
        self.logger.info(f"Removed {len(data) - len(cleaned)} duplicates", self.class_name)
        return context

class DataValidatorStep(Step):
    """Single responsibility: Validate data."""
    def validate(self, context: StepContext) -> None:
        data = context.get_data()
        if len(data) == 0:
            raise DataValidationError("No data to process")

class DataSaverStep(Step):
    """Single responsibility: Save data."""
    def __init__(self, output_repo: WriteableRepository, logger: PipelineLogger,
                 step_name: str, step_number: int):
        super().__init__(logger, step_name, step_number)
        self.output_repo = output_repo

    def persist(self, context: StepContext) -> StepContext:
        self.output_repo.save(context.get_data())
        return context
```

#### Predictable (Consistent Behavior)
**❌ Before (Unpredictable):**
```python
def unpredictable_processor(data: pd.DataFrame) -> pd.DataFrame:
    """Unpredictable behavior based on external state."""
    import random
    if random.choice([True, False]):  # Random behavior
        return data.dropna()
    else:
        return data.fillna(0.0)  # Different behavior

def another_function(data: pd.DataFrame, mode: str = None) -> pd.DataFrame:
    """Inconsistent behavior based on magic strings."""
    if mode == "strict":
        data = data.dropna()
    elif mode == "lenient":
        data = data.fillna(0.0)
    else:
        # What happens here? Unclear!
        pass
    return data
```

**✅ After (Predictable Behavior):**
```python
class DataCleaningStep(Step):
    """Predictable behavior through clear contracts."""
    def __init__(self, strategy: str, fill_value: float, logger: PipelineLogger,
                 step_name: str, step_number: int):
        super().__init__(logger, step_name, step_number)
        self.strategy = strategy  # Clear, typed configuration
        self.fill_value = fill_value

    def apply(self, context: StepContext) -> StepContext:
        """Always behaves the same way with same inputs."""
        data = context.get_data()

        if self.strategy == "drop":
            result = data.dropna()
            context.set_state('rows_removed', len(data) - len(result))
        elif self.strategy == "fill":
            result = data.fillna(self.fill_value)
            context.set_state('rows_filled', data.isnull().sum().sum())
        else:
            raise DataValidationError(f"Unknown strategy: {self.strategy}")

        context.set_data(result)
        return context

    def validate(self, context: StepContext) -> None:
        """Consistent validation behavior."""
        data = context.get_data()
        if len(data) == 0:
            raise DataValidationError("Processing resulted in empty dataset")
```

#### Idiomatic (Python Conventions)
**❌ Before (Non-Idiomatic):**
```python
class BadPythonProcessor:
    def __init__(self, input_file, output_file):
        self.input_file = input_file  # Not using pathlib
        self.output_file = output_file

    def processData(self):  # camelCase instead of snake_case
        data = pd.read_csv(self.input_file)
        # Using old-style string formatting
        print("Processed %d rows" % len(data))
        # Manual loop instead of pandas idioms
        for i in range(len(data)):
            if pd.isna(data.iloc[i]['price']):
                data.iloc[i]['price'] = 0.0
        data.to_csv(self.output_file, index=False)
```

**✅ After (Idiomatic Python):**
```python
from pathlib import Path
from typing import Optional

class ProductProcessorStep(Step):
    """Follows Python idioms and conventions."""
    def __init__(self, source_repo: ReadOnlyRepository, output_repo: WriteableRepository,
                 fill_value: float = 0.0, logger: PipelineLogger = None,
                 step_name: str = "Product Processor", step_number: int = 1):
        super().__init__(logger or PipelineLogger(), step_name, step_number)
        self.source_repo = source_repo
        self.output_repo = output_repo
        self.fill_value = fill_value

    def setup(self, context: StepContext) -> StepContext:
        """Idiomatic: Using context managers and pandas methods."""
        data = self.source_repo.get_all()
        self.logger.info(f"Loaded {len(data)} records", self.class_name)
        context.set_data(data)
        return context

    def apply(self, context: StepContext) -> StepContext:
        """Idiomatic: Using pandas fillna instead of manual loops."""
        data = context.get_data()
        filled_data = data.fillna({'price': self.fill_value})
        context.set_data(filled_data)
        self.logger.info("Applied idiomatic pandas transformations", self.class_name)
        return context

    def validate(self, context: StepContext) -> None:
        """Idiomatic: Using pandas methods for validation."""
        data = context.get_data()
        if data.empty:
            raise DataValidationError("Dataset is empty after processing")
```

#### Domain-based (Business Language)
**❌ Before (Technical Jargon):**
```python
def transform_data(input_path: str, output_path: str) -> pd.DataFrame:
    """Uses technical jargon instead of business language."""
    df = pd.read_csv(input_path)
    df = df.drop_duplicates(subset=['id'])
    df['price'] = df['price'].fillna(0.0)
    df.to_csv(output_path, index=False)
    return df
```

**✅ After (Domain-based Language):**
```python
class ProductInventoryStep(Step):
    """Uses business domain language throughout."""
    def __init__(self, product_repository: ReadOnlyRepository,
                 inventory_repository: WriteableRepository, logger: PipelineLogger,
                 step_name: str, step_number: int):
        super().__init__(logger, step_name, step_number)
        self.product_repository = product_repository
        self.inventory_repository = inventory_repository

    def setup(self, context: StepContext) -> StepContext:
        """Business context: Load product catalog."""
        products = self.product_repository.get_all()
        self.logger.info(f"Loaded {len(products)} products from catalog", self.class_name)
        context.set_data(products)
        return context

    def apply(self, context: StepContext) -> StepContext:
        """Business logic: Standardize product inventory."""
        products = context.get_data()

        # Remove duplicate product entries
        unique_products = products.drop_duplicates(subset=['product_id'])
        duplicates_removed = len(products) - len(unique_products)

        # Ensure all products have valid pricing
        products_with_pricing = unique_products.fillna({'unit_price': 0.0})

        context.set_data(products_with_pricing)
        context.set_state('duplicates_removed', duplicates_removed)
        self.logger.info(f"Standardized {len(products_with_pricing)} products, "
                        f"removed {duplicates_removed} duplicates", self.class_name)
        return context

    def validate(self, context: StepContext) -> None:
        """Business validation: Ensure inventory integrity."""
        products = context.get_data()

        if 'product_id' not in products.columns:
            raise DataValidationError("Product inventory missing product identifiers")

        if products['unit_price'].isnull().any():
            raise DataValidationError("Product inventory contains items without pricing")

    def persist(self, context: StepContext) -> StepContext:
        """Business context: Update inventory system."""
        self.inventory_repository.save(context.get_data())
        self.logger.info("Updated product inventory in business system", self.class_name)
        return context
```

### Rule 1.4: Maintain Test Compatibility
Refactored code must maintain compatibility with existing tests:
* **Same Public Interface**: Public methods and their signatures must remain compatible
* **Same Exception Types**: Exception classes and hierarchies must be preserved
* **Same Data Contracts**: DataFrame schemas and column names must be maintained
* **Same Configuration Requirements**: Configuration parameters and their meanings must be preserved

### Rule 1.5: No Feature Enhancement
Refactoring **MUST NOT** add new features or capabilities:
* **❌ WRONG**: Adding new validation rules not in original code
* **❌ WRONG**: Adding new data transformations not in original code
* **❌ WRONG**: Adding new configuration options not in original code
* **✅ CORRECT**: Only structural improvements that preserve existing behavior

---

## 2. Refactoring Process

### Phase 1: Analysis and Planning
Before refactoring, analyze the legacy code:

1. **Document Current Behavior**: Create comprehensive tests that capture all existing behavior
2. **Identify Design Violations**: Map current code against design standards requirements
3. **Plan Structural Changes**: Design the refactored architecture without changing business logic
4. **Verify Test Coverage**: Ensure all behavior is captured in tests before refactoring

### Phase 2: Structural Refactoring
Execute the refactoring in small, testable steps:

1. **Extract Dependencies**: Identify all hard-coded dependencies and create repository abstractions
2. **Implement Step Pattern**: Convert procedural code into four-phase Step implementation
3. **Apply Dependency Injection**: Replace hard-coded dependencies with constructor injection
4. **Add Centralized Logging**: Replace print/logging statements with PipelineLogger
5. **Add Type Hints**: Complete type annotations throughout the codebase

### Phase 3: Validation and Testing
After refactoring:

1. **Run Existing Tests**: Verify all existing tests still pass
2. **Compare Outputs**: Ensure identical outputs between legacy and refactored code
3. **Validate Design Compliance**: Confirm adherence to all design standards
4. **Performance Testing**: Ensure no significant performance regressions

---

## 3. Refactoring Examples

### Example 1: Simple Data Processing Function

**❌ Legacy Code (Hard-coded Dependencies):**
```python
def process_products(file_path: str) -> pd.DataFrame:
    """Process product data from CSV file."""
    # Hard-coded file path
    data = pd.read_csv(file_path)

    # Mixed concerns - logging, processing, validation
    print(f"Loaded {len(data)} products")

    # Business logic: clean duplicates
    data = data.drop_duplicates(subset=['product_id'])

    # Hard-coded output path
    data.to_csv(file_path.replace('.csv', '_clean.csv'), index=False)

    return data
```

**✅ Refactored Code (Design Standards Compliant):**
```python
class ProductCatalogStep(Step):
    """Standardize product catalog by removing duplicates and ensuring data quality."""

    def __init__(self, product_repository: ReadOnlyRepository, catalog_repository: WriteableRepository,
                 logger: PipelineLogger, step_name: str, step_number: int):
        super().__init__(logger, step_name, step_number)
        self.product_repository = product_repository
        self.catalog_repository = catalog_repository

    def setup(self, context: StepContext) -> StepContext:
        """Load product catalog from business repository."""
        catalog_data = self.product_repository.get_all()
        self.logger.info(f"Loaded {len(catalog_data)} products from catalog", self.class_name)
        context.set_data(catalog_data)
        return context

    def apply(self, context: StepContext) -> StepContext:
        """Standardize product catalog entries."""
        catalog_data = context.get_data()

        initial_count = len(catalog_data)
        standardized_catalog = catalog_data.drop_duplicates(subset=['product_id'])
        duplicates_removed = initial_count - len(standardized_catalog)

        context.set_data(standardized_catalog)
        context.set_state('duplicates_removed', duplicates_removed)
        self.logger.info(f"Standardized {len(standardized_catalog)} products, "
                        f"removed {duplicates_removed} duplicates", self.class_name)
        return context

    def validate(self, context: StepContext) -> None:
        """Ensure catalog integrity and completeness."""
        catalog_data = context.get_data()

        if 'product_id' not in catalog_data.columns:
            raise DataValidationError("Product catalog missing product identifiers")

        if len(catalog_data) == 0:
            raise DataValidationError("Product catalog is empty after standardization")

    def persist(self, context: StepContext) -> StepContext:
        """Update standardized catalog in business system."""
        self.catalog_repository.save(context.get_data())
        self.logger.info("Updated product catalog in business system", self.class_name)
        return context
```

### Example 2: Configuration Management

**❌ Legacy Code (Hard-coded Configuration):**
```python
class LegacyAnalyzer:
    def __init__(self):
        self.fill_value = 0.0  # Hard-coded
        self.batch_size = 100  # Hard-coded
        self.log_level = "INFO"  # Hard-coded

    def analyze(self, data: pd.DataFrame) -> pd.DataFrame:
        # Uses hard-coded configuration
        return data.fillna(self.fill_value)
```

**✅ Refactored Code (Injected Configuration):**
```python
class ProductAnalysisStep(Step):
    def __init__(self, fill_value: float, batch_size: int, logger: PipelineLogger,
                 step_name: str, step_number: int):
        super().__init__(logger, step_name, step_number)
        self.fill_value = fill_value  # Injected configuration
        self.batch_size = batch_size  # Injected configuration

    def apply(self, context: StepContext) -> StepContext:
        """Fill missing values with configured fill value."""
        data = context.get_data()

        # Log configuration usage
        self.logger.info(f"Filling missing values with {self.fill_value}, "
                        f"processing in batches of {self.batch_size}", self.class_name)

        result = data.fillna(self.fill_value)
        context.set_data(result)
        return context
```

---

## 4. Dependency Injection Implementation

### Repository Extraction Pattern

**❌ Before (Hard-coded I/O):**
```python
def export_data(data: pd.DataFrame, output_path: str):
    """Export data to hard-coded file path."""
    data.to_csv(output_path, index=False)
```

**✅ After (Repository Pattern):**
```python
class DataExportStep(Step):
    def __init__(self, output_repo: WriteableRepository, logger: PipelineLogger,
                 step_name: str, step_number: int):
        super().__init__(logger, step_name, step_number)
        self.output_repo = output_repo

    def persist(self, context: StepContext) -> StepContext:
        """Export data using injected repository."""
        self.output_repo.save(context.get_data())
        return context
```

### Factory Pattern for Testability

**Composition Root Example:**
```python
def create_product_inventory_pipeline(product_catalog_path: str, inventory_output_path: str,
                                    default_pricing: float = 0.0) -> Pipeline:
    """Composition root demonstrating proper dependency injection and domain-based naming."""

    # Create shared logger with business context
    logger = PipelineLogger("ProductInventoryPipeline", level="INFO")

    # Create repositories using business domain terminology
    product_repository = CsvFileRepository(product_catalog_path, logger)
    inventory_repository = CsvFileRepository(inventory_output_path, logger)

    # Create steps with business-focused names and responsibilities
    steps = [
        ProductInventoryStep(
            product_repository=product_repository,
            inventory_repository=inventory_repository,
            logger=logger,
            step_name="Standardize Product Inventory",
            step_number=1
        ),
        ProductPricingStep(
            fill_value=default_pricing,
            logger=logger,
            step_name="Apply Product Pricing",
            step_number=2
        )
    ]

    return Pipeline(steps=steps, logger=logger)
```

---

## 5. Validation and Error Handling

### Exception Preservation

**❌ Before (Generic Exceptions):**
```python
def validate_data(data: pd.DataFrame):
    if data.empty:
        raise ValueError("Data is empty")  # Generic exception
```

**✅ After (Design Standard Exceptions):**
```python
def validate(self, context: StepContext) -> None:
    """Validate data using design standard exceptions."""
    data = context.get_data()

    if data.empty:
        self.logger.error("Validation failed: data is empty", self.class_name)
        raise DataValidationError("No data available for processing")
```

### Error Context Preservation

**❌ Before (Lost Context):**
```python
try:
    result = process_data(data)
except Exception as e:
    print(f"Error: {e}")  # Lost original context
    raise
```

**✅ After (Preserved Context):**
```python
def execute(self, context: StepContext) -> StepContext:
    """Execute with full error context preservation."""
    try:
        self.logger.info(f"Starting step #{self.step_number}: {self.step_name}", self.class_name)
        context = self.setup(context)
        context = self.apply(context)
        self.validate(context)  # Validation by exception
        context = self.persist(context)
        return context
    except DataValidationError:
        # Re-raise validation errors with context
        self.logger.error(f"Step #{self.step_number} failed validation", self.class_name)
        raise  # Preserve original exception and context
    except Exception as e:
        # Log unexpected errors with full context
        self.logger.error(f"Unexpected error in step #{self.step_number}: {str(e)}", self.class_name)
        raise  # Preserve original exception type and message
```

---

## 6. Testing Compatibility

### Interface Preservation

**❌ Before (Breaking Change):**
```python
# Legacy interface
def process_data(file_path: str, fill_value: float = 0.0) -> pd.DataFrame:
    return pd.read_csv(file_path).fillna(fill_value)
```

**✅ After (Compatible Interface):**
```python
# Maintain compatibility through wrapper or factory
def process_data(file_path: str, fill_value: float = 0.0) -> pd.DataFrame:
    """Maintain exact same interface for backward compatibility."""
    # Create pipeline with same interface
    pipeline = create_product_processing_pipeline(file_path, file_path.replace('.csv', '_out.csv'), fill_value)
    context = pipeline.run()
    return context.get_data()

def create_product_processing_pipeline(catalog_path: str, output_path: str, fill_value: float) -> Pipeline:
    """Internal implementation using design standards and domain terminology."""
    logger = PipelineLogger("ProductProcessing")
    product_repo = CsvFileRepository(catalog_path, logger)
    inventory_repo = CsvFileRepository(output_path, logger)

    return Pipeline([
        ProductInventoryStep(product_repo, inventory_repo, logger, "Process Products", 1)
    ], logger)
```

---

## 7. Refactoring Workflow

### Pre-Refactoring Checklist
- [ ] **Document Current Behavior**: Create tests that capture all existing functionality
- [ ] **Analyze Dependencies**: Identify all hard-coded dependencies and I/O operations
- [ ] **Map Design Violations**: Document specific design standards violations to address
- [ ] **Plan Migration Path**: Design refactored architecture that preserves behavior
- [ ] **Verify Test Coverage**: Ensure all code paths are tested before refactoring

### Refactoring Steps
1. **Create Repository Abstractions**: Extract all I/O operations into repository interfaces
2. **Implement Step Pattern**: Convert procedural code into Step classes with four phases
3. **Apply Dependency Injection**: Replace hard-coded dependencies with constructor injection
4. **Add Centralized Logging**: Replace all logging/print statements with PipelineLogger
5. **Complete Type Hints**: Add comprehensive type annotations
6. **Update Tests**: Modify tests to work with new dependency injection pattern

### Post-Refactoring Validation
- [ ] **Behavioral Equivalence**: Verify identical outputs for identical inputs
- [ ] **Test Compatibility**: Ensure all existing tests pass (or are updated appropriately)
- [ ] **Design Compliance**: Confirm adherence to all design standards
- [ ] **Performance Validation**: Ensure no significant performance regressions
- [ ] **Error Handling**: Verify exception types and messages are preserved

---

## 8. Verification Commands

### Code Quality Verification
```bash
# Verify dependency injection compliance
grep -r "self\..*_repo\s*=" src/ | head -10

# Check for hard-coded file paths
grep -r "pd\.read_\|to_csv\|open(" src/ | grep -v "self\..*_repo"

# Verify centralized logging
grep -r "PipelineLogger" src/ | wc -l

# Check type hints coverage
grep -n "def.*)" src/ | grep -c ":"

# Verify Step pattern implementation
grep -n "def setup\|def apply\|def validate\|def persist" src/ | wc -l
```

### Design Standards Compliance
```bash
# Check for proper inheritance
grep -n "class.*Step)" src/

# Verify constructor injection
grep -n "__init__.*logger.*PipelineLogger" src/

# Check exception handling
grep -n "DataValidationError" src/ | wc -l

# Verify repository pattern usage
grep -n "self\..*_repo\." src/ | wc -l
```

### CUPID Principles Verification
```bash
# Verify composable design (multiple small classes vs few large ones)
find src/ -name "*.py" -exec wc -l {} + | awk '$1 < 100 {print $2}' | wc -l

# Check Unix philosophy (single responsibility) - classes with focused methods
grep -n "class.*Step" src/ | wc -l

# Verify predictable behavior (consistent patterns)
grep -n "def setup\|def apply\|def validate\|def persist" src/ | wc -l

# Check idiomatic Python (snake_case, type hints, proper imports)
grep -n "from typing import\|def.*:" src/ | wc -l

# Verify domain-based naming (business terms in class/method names)
grep -n "class.*Product\|class.*Inventory\|class.*Order" src/ | wc -l
```

---

## 9. Important Refactoring Constraints

**🚫 NEVER VIOLATE:**
- **Business Logic Preservation**: Never modify what the code does, only how it's structured
- **Interface Compatibility**: Never break existing public APIs or contracts
- **Test Compatibility**: Never break existing tests without proper migration
- **Performance Requirements**: Never introduce significant performance regressions
- **Error Handling**: Never change exception types or error handling behavior

**✅ ALWAYS ENFORCE:**
- **Design Standards Compliance**: Follow `code_design_standards.md` exactly
- **CUPID Principles**: Apply Composable, Unix Philosophy, Predictable, Idiomatic, Domain-based principles
- **Dependency Injection**: All dependencies must be injected, never hard-coded
- **Centralized Logging**: All logging through single PipelineLogger instance
- **Type Safety**: Complete type hints on all public interfaces

**🔄 STRUCTURAL IMPROVEMENTS ONLY:**
- Convert hard-coded dependencies to dependency injection (Composable)
- Extract I/O operations into repository pattern (Unix Philosophy)
- Implement four-phase Step execution pattern (Predictable)
- Add comprehensive type hints (Idiomatic)
- Centralize logging through PipelineLogger (Composable)
- Separate concerns into distinct classes/modules using business domain language (Domain-based)

---

## 10. Refactoring Verification Checklist

Before considering refactoring complete, verify:

- [ ] **Behavioral Equivalence**: Refactored code produces identical results to legacy code
- [ ] **Design Standards Compliance**: All requirements from `code_design_standards.md` are met
- [ ] **CUPID Principles**: Code follows Composable, Unix Philosophy, Predictable, Idiomatic, Domain-based guidelines
- [ ] **Dependency Injection**: All dependencies are properly injected via constructors
- [ ] **Repository Pattern**: All I/O operations use repository abstractions
- [ ] **Centralized Logging**: Single PipelineLogger instance handles all logging
- [ ] **Type Hints**: Complete type annotations throughout codebase
- [ ] **Step Pattern**: Four-phase execution (setup, apply, validate, persist) implemented
- [ ] **Test Compatibility**: All existing tests pass with refactored code
- [ ] **Exception Handling**: DataValidationError used for validation failures
- [ ] **Performance**: No significant performance regressions introduced
- [ ] **Code Quality**: Improved maintainability and testability achieved
- [ ] **Documentation**: Clear docstrings and comments explaining refactored structure

**🚫 REMEMBER**: Refactoring is about improving structure, not adding features or changing behavior. The refactored code must be functionally identical to the original while being more maintainable and testable.
