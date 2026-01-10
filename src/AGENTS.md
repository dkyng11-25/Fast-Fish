# AI Agent Source Code Development Guidelines

## 📏 Code Length Limits & Modularization

### Code Size Constraints
**Maximum 500 Lines of Code (LOC) per file** - Both source code and test code must comply.

#### Rationale
- **Maintainability**: Smaller files are easier to understand, review, and modify
- **Cognitive Load**: Developers can hold entire file context in working memory
- **Debugging**: Issues easier to isolate and fix in smaller units
- **Code Reviews**: More focused and effective peer reviews
- **Testing**: Each module can be tested independently

#### Verification Tools
```bash
find src/ tests/ -name "*.py" -exec wc -l {} + | awk '$1 > 500 {print "VIOLATION: " $2 ": " $1 " lines"}'
complexipy src/ tests/ --min 500
```

### CUPID-Based Modularization

When code exceeds 500 LOC, **mandatory modularization** must follow CUPID principles:

#### 1. Composable (Modular and Reusable)
- Modularized into focused components (80-150 lines each)
- DataLoader, DataValidator, DataTransformer, ReportGenerator, DataPipeline orchestrator
- Each component has single responsibility

#### 2. Unix Philosophy (Single Responsibility)
- Each function/class does one thing well
- `process_data()`: 200 lines focused only on processing
- `save_to_database()`: 80 lines focused only on persistence
- `generate_report()`: 120 lines focused only on reporting

#### 3. Predictable (Consistent Behavior)
- FastDataProcessor: Consistent fast behavior
- ThoroughDataProcessor: Consistent thorough behavior
- Clear contracts with no magic parameters

#### 4. Idiomatic (Python Conventions)
- Proper snake_case naming throughout
- Leverages pandas idioms instead of manual loops
- Uses pathlib for file paths and context managers
- Complete type hints and modern Python conventions

#### 5. Domain-based (Business Language)
- ProductCatalogCleaner: Clear business domain context
- `remove_discontinued_products()`: Business logic naming
- `ensure_valid_pricing()`: Business requirement focus
- Method names reflect business processes, not technical jargon

### Modularization Workflow
1. **Identify oversized files**: `find src/ tests/ -name "*.py" -exec wc -l {} + | sort -nr`
2. **Analyze with complexipy**: `complexipy src/path/to/large_file.py --threshold 500`
3. **Extract components**: Create separate classes/functions per responsibility
4. **Define clear interfaces**: Establish contracts between components
5. **Verify composability**: Ensure components can be reused and combined

## 🛠️ Development Environment Setup

### Package Management
- **Use `uv pip install`** for Python packages (not `pip`)
- **Single environment per project** - use `uv` managed environment
- Install all at once: `uv pip install -e ".[dev]" pytest pytest-bdd fireducks complexipy ruff`
- **Homebrew packages** (terminal/OS level): `brew install tealdeer xan tokei eza rip2 skim procs choose`

### Data Processing Acceleration
- **Use `import fireducks.pandas as pd`** for accelerated pandas operations
- Drop-in replacement for pandas with significant speed improvements
- Maintains full pandas API compatibility

## 📁 Directory Structure and Purpose

### @src/ - Source Code (Modular Organization)
- **Location for all source code** with strict modular organization
- **🚫 DO NOT MODIFY legacy code** directly under `src/` starting with "step" + numbers
- **Legacy files are reference-only** for understanding existing functionality
- **All new implementations** go in appropriate subdirectories

### @src/steps/ - Pipeline Steps (1 File Per Step)
- **Exactly 1 file per step** - no duplicate implementations allowed
- **Consolidate duplicate code** into `src/components/` or `src/utils/`
- **Refactored implementations** follow 4-phase Step pattern (setup → apply → validate → persist)

### @src/core/ - Core Infrastructure (Critical Hub)
- **Central hub** for shared infrastructure - treat with extra care
- Core components: context, logger, step base class, exceptions, pipeline orchestrator
- **Dependency injection framework** and base classes for all steps
- **🚫 High impact changes** - modifications affect entire pipeline

### @src/repositories/ - Data Access Layer (Modular I/O)
- **Repository pattern implementations** for all data sources
- **Abstractions** for CSV, API, database, and filesystem operations
- **Modular data access** with clear interfaces and dependency injection

### @src/components/ - Reusable Components
- **Shared business logic** used across multiple steps
- **Extracted monolithic logic** from large implementations
- **Domain-specific logic** organized by business capability

### @src/utils/ - Utility Functions
- **Pure utility functions** with no business logic dependencies
- **Helper functions** for data manipulation, validation, formatting
- **Keep this lean** - avoid business logic

### @src/config_new/ - Configuration Management (Hub)
- **Centralized configuration** - treat with extra care
- **Environment-specific settings** and pipeline parameters
- **🚫 High impact folder** - changes affect entire system

### Legacy Code Preservation Rules
- **🚫 DO NOT MODIFY** files under `src/` starting with "step" + numbers
- **🚫 DO NOT DELETE** legacy implementations - they serve as reference
- **✅ CREATE NEW** implementations in appropriate subdirectories
- **✅ REFACTOR** logic into modular components while preserving legacy

## 📋 Best Practices

### Code Quality (CUPID Compliance & Size Limits)
- **500 LOC Limit**: No file may exceed 500 lines of code
- **Mandatory Modularization**: When limits exceeded, apply CUPID-based refactoring
- **Follow 4-phase Step pattern**: setup → apply → validate → persist for all pipeline steps
- **CUPID Principles**: Composable, Unix Philosophy, Predictable, Idiomatic, Domain-based
- **Dependency Injection**: All dependencies injected via constructor, never hard-coded
- **Repository Pattern**: All I/O operations through repository abstractions
- **Centralized Logging**: Single PipelineLogger instance for all operations
- **Type Safety**: Complete type hints on all public interfaces
- **Comprehensive Docstrings**: Inputs/dependencies, goal/process, outputs/results
- **Incremental Modification**: Always incrementally modify code to preserve progress
- **No Silent Failures**: Fail fast with comprehensive error logs and context

### Data Handling (Performance Optimized)
- **Pandas Acceleration**: Always use `import fireducks.pandas as pd` for data operations
- **Performance Monitoring**: Track processing bottlenecks and optimize with fireducks
- **Schema Validation**: Use pandera schemas for data validation at each step
- **Real Data Priority**: Prefer actual data subsets over synthetic for validation
- **Memory Efficiency**: Data transformations optimized for large-scale processing

### Modular Organization & Code Consolidation
- **1 File Per Step**: Exactly one implementation file per pipeline step in `src/steps/`
- **No Duplicate Code**: Consolidate duplicate implementations into shared components
- **Hub Folder Protection**: Treat `src/core/` and `src/config_new/` with extra care
- **Component Extraction**: Move reusable logic to `src/components/` and `src/utils/`
- **Clean Separation**: Maintain clear boundaries between business logic and infrastructure

## 🏗️ Architecture Principles

### Pipeline Design (4-Phase Pattern)
- **Setup Phase**: Load and prepare data from repositories
- **Apply Phase**: Transform data according to business rules
- **Validate Phase**: Verify data integrity and business constraints
- **Persist Phase**: Save results to appropriate output repositories
- **Context Management**: State passed between phases for predictable execution
- **Dependency Injection**: All external dependencies injected via constructors

### Error Handling (Fail Fast)
- **Feature-Driven Validation**: Error scenarios defined before implementation
- **Fail Fast**: Comprehensive error logs with immediate failure on validation errors
- **No Silent Failures**: All errors must be logged and tracked with full context
- **DataValidationError**: Standard exception type for all business rule violations
- **Retry Logic**: Only for transient API failures, never for validation errors

### Performance (Tested & Validated)
- **Batch Processing**: Efficient handling of large datasets with memory management
- **Incremental Processing**: Progress tracking and resumable operations
- **Monitoring Integration**: Processing times and bottlenecks tracked in logs

## 📚 Code Quality Reference

### Size Compliance Verification
```bash
# Find files exceeding 500 LOC
find src/ tests/ -name "*.py" -exec wc -l {} + | awk '$1 > 500 {print "VIOLATION: " $2 ": " $1 " lines"}'

# Detailed analysis
complexipy src/ tests/ --min 500
```

### Modular Organization Verification
```bash
# Verify 1 file per step (should be in subdirectories only)
find src/ -maxdepth 1 -name "step*.py" | wc -l  # Should be 0
find src/steps/ -name "*.py" | sort

# Check fireducks pandas usage
grep -r "import fireducks.pandas as pd" src/ | wc -l
```

### Code Quality Tools
- **`complexipy`**: Assess file readability and suggest modularization points
- **`ruff`**: Lint and format Python code
- **`tldr command_name`**: Quick reference for any tool (use this for details)
