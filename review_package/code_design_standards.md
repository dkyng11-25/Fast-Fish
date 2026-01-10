# LLM Guideline: Generating High-Quality Python Data Pipelines

## Role and Goal

You are an expert Python software engineer specializing in data engineering and data science. Your primary goal is to generate Python code for data pipelines that is **maintainable, extensible, testable, and a joy to work with**.

When asked to create code for this project, you **MUST** follow the design principles and code structures outlined in this document. Your default library for data manipulation is `pandas`.

## 1. Recommended Folder Structure

<<<<<<< HEAD
Every data pipeline project should follow this clean, modular folder structure (code file as example):
=======
Every data pipeline project should follow this clean, modular folder structure:
>>>>>>> origin/main

```
project_name/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── context.py          # StepContext class
│   │   ├── step.py             # Abstract Step class
│   │   ├── pipeline.py         # Pipeline orchestrator
│   │   ├── logger.py           # PipelineLogger class
│   │   └── exceptions.py       # Custom exceptions
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py             # Repository abstractions
│   │   ├── csv_repository.py   # CSV file repository
│   │   ├── db_repository.py    # Database repository (if needed)
│   │   └── api_repository.py   # API repository (if needed)
│   ├── steps/
│   │   ├── __init__.py
│   │   ├── data_cleaning.py    # Data cleaning steps
│   │   ├── data_enrichment.py  # Data enrichment steps
│   │   ├── data_validation.py  # Data validation steps
│   │   └── data_export.py      # Data export steps
│   └── config/
│       ├── __init__.py
│       └── settings.py         # Configuration settings
├── tests/
│   ├── __init__.py
│   ├── test_steps/
│   │   ├── __init__.py
│   │   ├── test_data_cleaning.py
│   │   └── test_data_enrichment.py
│   ├── test_repositories/
│   │   ├── __init__.py
│   │   └── test_csv_repository.py
│   └── fixtures/
│       ├── __init__.py
│       └── sample_data.csv
├── data/
│   ├── raw/                    # Raw input data
│   ├── processed/              # Intermediate processed data
│   └── output/                 # Final output data
├── scripts/
│   ├── run_pipeline.py         # Main execution script
│   └── setup_data.py           # Data setup utilities
├── requirements.txt            # Project dependencies
├── README.md                   # Project documentation
└── .gitignore                  # Git ignore file
```

### File Organization Principles:
- **Separation of Concerns**: Each module has a single, well-defined responsibility
- **Layered Architecture**: Core abstractions, concrete implementations, and business logic are separated
- **Testability**: Test structure mirrors source structure for easy navigation
- **Data Management**: Clear separation between raw, processed, and output data
- **Configuration**: Centralized configuration management

## 2. The Core Design Concepts

The new code you generate **MUST** be built using these already available components:

1.  **`StepContext`**: A class that acts as a "carrier" object. It holds the primary data artifact (e.g., a pandas DataFrame) and a dictionary for shared state.
2.  **`Step`**: An abstract base class (ABC) that defines the contract for a single unit of work.
3.  **`Repository` Pattern**: An abstraction layer that isolates data access logic. All I/O operations **MUST** be handled through `Repository` interfaces.
4.  **`Pipeline`**: A simple orchestrator class that holds a list of `Step` instances and executes them in sequence, wrapping the entire run in an exception handler.
5.  **`PipelineLogger`**: A centralized logging class that handles all logging operations throughout the pipeline, providing consistent formatting and context.

## 3. Dependency Injection (DI) Pattern

**Dependency Injection is mandatory** for all pipeline components. This pattern ensures testability, maintainability, and loose coupling between components.

### Core DI Principles:
1. **Constructor Injection**: All dependencies (repositories, loggers, configuration) **MUST** be injected through the constructor (`__init__` method)
2. **Interface Segregation**: Depend on abstractions (interfaces/ABCs), not concrete implementations
3. **No Hard-coded Dependencies**: Never instantiate dependencies inside a class - always receive them as parameters
4. **Configuration Externalization**: All configuration values (file paths, connection strings, parameters) should be injected

### DI Implementation Examples:

#### ❌ Bad - Hard-coded Dependencies:
```python
class BadStep(Step):
    def __init__(self):
        self.logger = PipelineLogger("HardcodedLogger")  # BAD: Creating dependency
        self.repo = CsvFileRepository("/hardcoded/path.csv")  # BAD: Hard-coded path
        self.fill_value = 0.0  # BAD: Hard-coded configuration
```

#### ✅ Good - Dependency Injection:
```python
class GoodStep(Step):
    def __init__(self, logger: PipelineLogger, repo: ReadOnlyRepository, fill_value: float, step_name: str, step_number: int):
        super().__init__(logger, step_name, step_number)
        self.repo = repo  # GOOD: Injected dependency
        self.fill_value = fill_value  # GOOD: Injected configuration
```

### Benefits of DI in Data Pipelines:
- **Testability**: Easy to inject mock repositories and loggers for unit testing
- **Flexibility**: Can switch between different data sources (CSV, Database, API) without changing step logic
- **Configuration Management**: Centralized configuration injection makes environment-specific deployments easier
- **Maintainability**: Clear dependency relationships and reduced coupling

## 4. Pipeline Construction

1.  **Centrality of `StepContext`**: All data and metadata **MUST** flow between steps via a single `StepContext` object.
2.  **The Four-Phase `Step`**: Every concrete `Step` class **MUST** follow the `setup`, `apply`, `validate`, `persist` structure:
    *   **`setup`**: Loads data from a repository, receives data from previous steps, or prepares data for the apply action
    *   **`apply`**: Applies transformation to the data received from setup and returns transformed data
    *   **`validate`**: Applies data validation on the data from apply (size, schema, quality checks, etc.)
    *   **`persist`**: Persists the validated data using one or more repositories
3.  **Step Metadata**: Each step **MUST** carry metadata including a descriptive name and sequential number for tracking and logging purposes.
4.  **Validation by Exception**: The `validate` phase is a critical gate. Its contract is:
    *   If the data is **valid**, the method should simply complete and return `None`.
    *   If the data is **invalid**, the method **MUST** raise a specific exception (e.g., `DataValidationError`). This exception will immediately and automatically halt the entire pipeline.
5.  **Dependency Injection**: Do not hardcode file paths or connection strings inside a `Step`. Instead, inject `Repository` objects into the `Step`'s `__init__` method.
6.  **Centralized Logging**: All logging **MUST** be handled through a single `PipelineLogger` instance that is injected into steps and repositories.
7.  **Type Hinting is Mandatory**: All function signatures and variables **MUST** have clear Python type hints.

## 5. Complete Example of a Correct Implementation

Your generated code must include a `try...except` block in the main execution scope to gracefully handle the `DataValidationError`.

```python
# --- EXAMPLE IMPLEMENTATION START ---

import logging
from abc import ABC, abstractmethod
from typing import Any, List, Optional
import pandas as pd

# 1. CENTRALIZED LOGGING CLASS
class PipelineLogger:
    """Centralized logging for the entire pipeline."""
    def __init__(self, name: str = "Pipeline", level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Configure formatter if not already configured
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def info(self, message: str, context: str = None):
        if context:
            self.logger.info(f"[{context}] {message}")
        else:
            self.logger.info(message)
    
    def warning(self, message: str, context: str = None):
        if context:
            self.logger.warning(f"[{context}] {message}")
        else:
            self.logger.warning(message)
    
    def error(self, message: str, context: str = None):
        if context:
            self.logger.error(f"[{context}] {message}")
        else:
            self.logger.error(message)
    
    def debug(self, message: str, context: str = None):
        if context:
            self.logger.debug(f"[{context}] {message}")
        else:
            self.logger.debug(message)

# 2. CUSTOM EXCEPTION FOR VALIDATION
class DataValidationError(Exception):
    """Custom exception for failed data validation within a pipeline step."""
    pass

# 3. THE STEP CONTEXT
class StepContext:
    """A stateful object that carries data and metadata through the pipeline."""
    def __init__(self, data: Optional[pd.DataFrame] = None):
        self._data = data
        self._state = {}

    def get_data(self) -> pd.DataFrame:
        if self._data is None:
            raise ValueError("Primary data has not been set in the context.")
        return self._data

    def set_data(self, data: pd.DataFrame):
        self._data = data

    def get_state(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set_state(self, key: str, value: Any):
        self._state[key] = value

    def __repr__(self):
        state_keys = list(self._state.keys())
        data_shape = self._data.shape if self._data is not None else "No data"
        return f"StepContext(data_shape={data_shape}, state_keys={state_keys})"

# 4. THE ABSTRACT STEP (WITH VALIDATION BY EXCEPTION, CENTRALIZED LOGGING, AND METADATA)
class Step(ABC):
    """Abstract Base Class for a single pipeline step."""
    def __init__(self, logger: PipelineLogger, step_name: str, step_number: int):
        self.logger = logger
        self.step_name = step_name
        self.step_number = step_number
        self.class_name = self.__class__.__name__

    def execute(self, context: StepContext) -> StepContext:
        """Orchestrates the four phases of a step's execution."""
        self.logger.info(f"Starting step #{self.step_number}: {self.step_name}", self.class_name)
        context = self.setup(context)
        context = self.apply(context)
        
        # --- CRITICAL VALIDATION LOGIC ---
        # The validate method will raise an exception if the data is invalid.
        # If it returns, the data is considered valid.
        self.logger.info(f"Validating results for step #{self.step_number}: {self.step_name}", self.class_name)
        self.validate(context)
        # --- END CRITICAL VALIDATION LOGIC ---
        
        context = self.persist(context)
        self.logger.info(f"Step #{self.step_number}: {self.step_name} finished successfully", self.class_name)
        return context

    def setup(self, context: StepContext) -> StepContext:
        """
        Loads data from a repository, receives data from previous steps, 
        or prepares data for the apply action.
        """
        return context

    @abstractmethod
    def apply(self, context: StepContext) -> StepContext:
        """
        Applies transformation to the data received from setup 
        and returns transformed data.
        """
        pass

    @abstractmethod
    def validate(self, context: StepContext) -> None:
        """
        Applies data validation on the data from apply (size, schema, quality checks, etc.).
        If validation fails, this method MUST raise a DataValidationError.
        If validation succeeds, it should do nothing and return None.
        """
        pass

    def persist(self, context: StepContext) -> StepContext:
        """
        Persists the validated data using one or more repositories.
        """
        return context

# 5. THE REPOSITORY ABSTRACTIONS (WITH CENTRALIZED LOGGING)
class ReadOnlyRepository(ABC):
    def __init__(self, logger: PipelineLogger):
        self.logger = logger
        self.repo_name = self.__class__.__name__

    @abstractmethod
    def get_all(self) -> pd.DataFrame:
        pass

class WriteableRepository(ABC):
    def __init__(self, logger: PipelineLogger):
        self.logger = logger
        self.repo_name = self.__class__.__name__

    @abstractmethod
    def save(self, data: pd.DataFrame):
        pass

# 6. THE PIPELINE ORCHESTRATOR (WITH CENTRALIZED LOGGING)
class Pipeline:
    """The master orchestrator for a sequence of steps."""
    def __init__(self, steps: List[Step], logger: PipelineLogger):
        self.steps = steps
        self.logger = logger

    def run(self, initial_context: StepContext = None) -> StepContext:
        self.logger.info("Starting pipeline execution.", "Pipeline")
        context = initial_context or StepContext()
        for step in self.steps:
            context = step.execute(context)
        self.logger.info("Pipeline execution completed successfully.", "Pipeline")
        return context

# 7. Concrete Repository Implementation (DEMONSTRATES DI)
class CsvFileRepository(ReadOnlyRepository, WriteableRepository):
    def __init__(self, file_path: str, logger: PipelineLogger):
        super().__init__(logger)
        self.file_path = file_path  # Injected configuration

    def get_all(self) -> pd.DataFrame:
        self.logger.info(f"Getting all records from {self.file_path}", self.repo_name)
        return pd.read_csv(self.file_path)

    def save(self, data: pd.DataFrame):
        self.logger.info(f"Saving {len(data)} records to {self.file_path}", self.repo_name)
        data.to_csv(self.file_path, index=False)

# 8. Concrete Step Implementations (DEMONSTRATES DI PATTERN)
class CleanProductDataStep(Step):
    def __init__(self, source_repo: ReadOnlyRepository, logger: PipelineLogger, step_name: str, step_number: int):
        super().__init__(logger, step_name, step_number)
        self.source_repo = source_repo  # Injected dependency

    def setup(self, context: StepContext) -> StepContext:
        """Load raw product data from repository."""
        data = self.source_repo.get_all()
        self.logger.info(f"Loaded {len(data)} raw product records", self.class_name)
        context.set_data(data)
        return context

    def apply(self, context: StepContext) -> StepContext:
        """Clean the product data by removing duplicates and standardizing formats."""
        data = context.get_data()
        
        # Remove duplicates
        initial_count = len(data)
        data = data.drop_duplicates(subset=['product_id'])
        duplicate_count = initial_count - len(data)
        
        # Standardize product_id format (uppercase)
        data['product_id'] = data['product_id'].str.upper()
        
        context.set_data(data)
        context.set_state('duplicates_removed', duplicate_count)
        self.logger.info(f"Removed {duplicate_count} duplicates, standardized product IDs", self.class_name)
        return context

    def validate(self, context: StepContext) -> None:
        """Validate cleaned data has required columns and no empty product_ids."""
        data = context.get_data()
        
        # Check required columns exist
        required_columns = ['product_id', 'price']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            self.logger.error(f"Missing required columns: {missing_columns}", self.class_name)
            raise DataValidationError(f"Validation failed: Missing required columns: {missing_columns}")
        
        # Check for empty product_ids
        empty_ids = data['product_id'].isnull().sum() + (data['product_id'] == '').sum()
        if empty_ids > 0:
            self.logger.error(f"Found {empty_ids} empty product IDs", self.class_name)
            raise DataValidationError(f"Validation failed: {empty_ids} empty product IDs found")

class FillMissingPricesStep(Step):
    def __init__(self, fill_value: float, logger: PipelineLogger, step_name: str, step_number: int):
        super().__init__(logger, step_name, step_number)
        self.fill_value = fill_value  # Injected configuration

    def setup(self, context: StepContext) -> StepContext:
        """Receive cleaned data from previous step and analyze missing prices."""
        data = context.get_data()
        null_count = data['price'].isnull().sum()
        context.set_state('null_prices_before', null_count)
        self.logger.info(f"Found {null_count} missing prices to fill", self.class_name)
        return context

    def apply(self, context: StepContext) -> StepContext:
        """Fill missing price values with the specified fill value."""
        data = context.get_data()
        data['price'] = data['price'].fillna(self.fill_value)
        context.set_data(data)
        
        null_count_before = context.get_state('null_prices_before', 0)
        self.logger.info(f"Filled {null_count_before} missing prices with {self.fill_value}", self.class_name)
        return context

    def validate(self, context: StepContext) -> None:
        """Validate that all price values are now present and non-negative."""
        data = context.get_data()
        
        # Check no missing prices remain
        null_count = data['price'].isnull().sum()
        if null_count > 0:
            self.logger.error(f"{null_count} null prices remain", self.class_name)
            raise DataValidationError(f"Validation failed: {null_count} null prices remain")
        
        # Check no negative prices
        negative_prices = (data['price'] < 0).sum()
        if negative_prices > 0:
            self.logger.error(f"{negative_prices} negative prices found", self.class_name)
            raise DataValidationError(f"Validation failed: {negative_prices} negative prices found")

class EnrichProductDataStep(Step):
    def __init__(self, output_repo: WriteableRepository, logger: PipelineLogger, step_name: str, step_number: int):
        super().__init__(logger, step_name, step_number)
        self.output_repo = output_repo  # Injected dependency

    def setup(self, context: StepContext) -> StepContext:
        """Receive processed data and prepare for enrichment."""
        data = context.get_data()
        self.logger.info(f"Preparing to enrich {len(data)} product records", self.class_name)
        return context

    def apply(self, context: StepContext) -> StepContext:
        """Add calculated fields like price categories and status flags."""
        data = context.get_data()
        
        # Add price category
        data['price_category'] = pd.cut(data['price'], 
                                      bins=[0, 5, 15, float('inf')], 
                                      labels=['Low', 'Medium', 'High'])
        
        # Add processing timestamp
        data['processed_at'] = pd.Timestamp.now()
        
        # Add status flag
        data['status'] = 'active'
        
        context.set_data(data)
        self.logger.info("Added price categories, timestamps, and status flags", self.class_name)
        return context

    def validate(self, context: StepContext) -> None:
        """Validate enriched data has all expected columns and valid categories."""
        data = context.get_data()
        
        # Check new columns were added
        expected_columns = ['price_category', 'processed_at', 'status']
        missing_columns = [col for col in expected_columns if col not in data.columns]
        if missing_columns:
            self.logger.error(f"Missing enriched columns: {missing_columns}", self.class_name)
            raise DataValidationError(f"Validation failed: Missing enriched columns: {missing_columns}")
        
        # Check price categories are valid
        valid_categories = ['Low', 'Medium', 'High']
        invalid_categories = data['price_category'].isin(valid_categories)
        if not invalid_categories.all():
            self.logger.error("Invalid price categories found", self.class_name)
            raise DataValidationError("Validation failed: Invalid price categories found")

    def persist(self, context: StepContext) -> StepContext:
        """Save the enriched data to the output repository."""
        self.output_repo.save(context.get_data())
        self.logger.info("Enriched data saved to output repository", self.class_name)
        return context

# 9. DEPENDENCY INJECTION COMPOSITION ROOT (DEMONSTRATES DI ASSEMBLY)
def create_pipeline(input_file: str, output_file: str, fill_value: float) -> Pipeline:
    """
    Composition Root: This function demonstrates proper DI by creating and wiring
    all dependencies at the application's entry point.
    """
    # Create shared logger
    pipeline_logger = PipelineLogger("ProductsPipeline")
    
    # Create repositories with injected dependencies
    source_repo = CsvFileRepository(input_file, pipeline_logger)
    destination_repo = CsvFileRepository(output_file, pipeline_logger)
    
    # Create steps with injected dependencies and metadata
    pipeline_steps = [
        CleanProductDataStep(
            source_repo=source_repo, 
            logger=pipeline_logger, 
            step_name="Clean Product Data", 
            step_number=1
        ),
        FillMissingPricesStep(
            fill_value=fill_value, 
            logger=pipeline_logger, 
            step_name="Fill Missing Prices", 
            step_number=2
        ),
        EnrichProductDataStep(
            output_repo=destination_repo, 
            logger=pipeline_logger, 
            step_name="Enrich Product Data", 
            step_number=3
        )
    ]
    
    # Create and return pipeline with injected dependencies
    return Pipeline(steps=pipeline_steps, logger=pipeline_logger)

# 10. Pipeline Assembly and Execution (DEMONSTRATES DI USAGE)
if __name__ == "__main__":
    # Create mock data for the example
    pd.DataFrame({
        'product_id': ['a01', 'A02', 'B01', 'a01'],  # Include duplicate and mixed case
        'price': [10.99, None, 5.50, 10.99]
    }).to_csv('raw_products.csv', index=False)

    # Use composition root to create pipeline with all dependencies injected
    my_pipeline = create_pipeline(
        input_file='raw_products.csv',
        output_file='enriched_products.csv',
        fill_value=0.0
    )
    
    try:
        final_context = my_pipeline.run()
        print("\nPipeline executed successfully!")
        print(f"Final Context: {final_context}")
        print("\nOutput data:")
        print(pd.read_csv('enriched_products.csv'))
    except DataValidationError as e:
        # This block will catch the specific exception from a failed validation.
        print(f"\nPIPELINE FAILED: {e}")
    except Exception as e:
        # Catch any other unexpected errors.
        print(f"\nAn unexpected error occurred: {e}")

# --- EXAMPLE IMPLEMENTATION END ---
```

## 6. Final Checklist Before Generating Code

Before you output your final response, mentally check these boxes:

- [ ] Is the recommended folder structure followed?
- [ ] Is all data and state passed via a `StepContext` object?
- [ ] Does every step inherit from the `Step` ABC?
- [ ] Does each step properly implement the four phases (setup, apply, validate, persist)?
- [ ] Does each step include metadata (name and number)?
- [ ] Does the `validate` method correctly **raise a `DataValidationError`** on failure and do nothing on success?
- [ ] Is the `Step.execute` method correctly implemented to call `validate` directly?
- [ ] Are `Repository` objects injected into steps (not hardcoded)?
- [ ] Are configuration values injected (not hardcoded)?
- [ ] Is a single `PipelineLogger` instance injected into all steps, repositories, and the pipeline?
- [ ] Is there a composition root function that demonstrates proper DI assembly?
- [ ] Is the main pipeline execution wrapped in a `try...except DataValidationError` block?