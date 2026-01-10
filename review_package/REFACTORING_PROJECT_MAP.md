# Refactoring Project Map - Complete Overview

**Last Updated:** 2025-10-09 09:45  
**Project:** Product Mix Clustering Pipeline Refactoring  
**Lead:** Vitor Queiroz  
**Latest:** Step 4 complete + Process guide enhanced!

---

## 📋 Executive Summary

This document maps the complete refactoring effort described by Vitor, showing where everything is located in the codebase and explaining the big picture of the transformation from monolithic scripts to modular, testable pipeline components.

---

## 🎯 The Big Picture

### What is Being Refactored?

The project is transforming a **36-step data pipeline** from large monolithic scripts (1,600+ lines each) into **modular, testable, maintainable components** using modern software engineering patterns.

### Refactoring Philosophy

**From:** Large procedural scripts with hardcoded dependencies  
**To:** Modular components with dependency injection, clear separation of concerns, and comprehensive test coverage

### Current Status

- ✅ **Step 1** (API Download): Fully refactored with 11 test scenarios
- ✅ **Step 2** (Coordinate Extraction): Refactored with test coverage
- ✅ **Step 3** (Matrix Preparation): Refactored with test coverage
- ✅ **Step 4** (Weather Data Download): Phase 4 complete - Quality validated, ready for integration!
- 🔄 **Steps 5-36**: Awaiting refactoring using the same pattern

---

## 📁 Key Documentation Locations

### 1. **Master Design Document** ⭐ MOST IMPORTANT
**Location:** `/docs/code_design_standards.md`

**What it contains:**
- LLM guidelines for generating refactored code
- Complete design patterns and principles
- Dependency injection examples
- The 4-phase step pattern (setup → apply → validate → persist)
- Repository pattern specifications
- Complete working example implementation
- Checklist for code generation

**Why it matters:** This is the **blueprint** for the entire refactoring effort. Every refactored step must follow these patterns.

---

### 2. **Test Scenario Definitions** (Feature Files)
**Location:** `/tests/features/*.feature`

**What they contain:**
- Plain-language test scenarios for each step
- Background setup steps that run before each test
- Scenario descriptions using Gherkin syntax (Given/When/Then)
- Business logic documentation in human-readable format

**Key Feature Files:**
- `step-1-api-download-merge.feature` - 11 test scenarios for Step 1
- `step-2-extract-coordinates.feature` - Test scenarios for Step 2
- `step-3-matrix-preparation.feature` - Test scenarios for Step 3
- `step6_cluster_analysis.feature` - Test scenarios for Step 6
- `step7_missing_category_rule.feature` - Test scenarios for Step 7
- ... (17 feature files total covering various steps)

**Why they matter:** These serve **dual purpose**:
1. Test specifications for automated testing
2. **Documentation** explaining what each step does in plain language

---

### 3. **Project README**
**Location:** `/README.md`

**What it contains:**
- Pipeline overview (36 steps organized in 5 phases)
- Quick start commands
- Step breakdown with timing estimates
- Output file descriptions
- System requirements
- Recent performance metrics

**Why it matters:** This is the **entry point** for understanding the overall pipeline architecture.

---

### 4. **Test Suite Documentation**
**Location:** `/tests/README.md` and related test docs

**Additional test documentation:**
- `/tests/COMPREHENSIVE_TEST_SUITE_README.md` - Complete test suite overview
- `/tests/TEST_SUITE_GUIDE.md` - Guide for running tests
- `/tests/TEST_COVERAGE_REPORT.md` - Test coverage analysis
- `/tests/DATA_VALIDATION_README.md` - Data validation approach

**Why they matter:** Explain how to run tests, interpret results, and extend test coverage.

---

### 5. **Merge Planning Documents**
**Location:** `/process_and_merge_docs/*.md`

**What they contain:**
- Step-by-step merge plans for integrating refactored code
- Specifications for each step's behavior
- Column documentation for data outputs

**Key documents:**
- `STEP7_SPEC.md`, `STEP8_SPEC.md`, etc. - Specifications for each step
- `STEP7_AND_TRENDING_MERGE_PLAN.md` - Merge strategy documents
- `STEP10_COLUMN_DOC.md` - Detailed column documentation

**Why they matter:** These guide the **integration** of refactored code back into the main pipeline.

---

## 🏗️ Code Structure

### Core Framework Components

**Location:** `/src/core/`

```
src/core/
├── __init__.py          # Package initialization
├── context.py           # StepContext class (data carrier)
├── step.py              # Abstract Step base class
├── pipeline.py          # Pipeline orchestrator
├── logger.py            # PipelineLogger (centralized logging)
└── exceptions.py        # Custom exception classes
```

**What they do:**
- **`context.py`**: Defines `StepContext` - the data carrier that flows between steps
- **`step.py`**: Defines the abstract `Step` class with the 4-phase pattern
- **`pipeline.py`**: Orchestrates execution of multiple steps in sequence
- **`logger.py`**: Provides centralized logging with consistent formatting
- **`exceptions.py`**: Custom exceptions like `DataValidationError`

---

### Repository Layer (Data Access Abstraction)

**Location:** `/src/repositories/`

```
src/repositories/
├── __init__.py              # Package initialization
├── base.py                  # Repository abstractions (interfaces)
├── csv_repository.py        # CSV file I/O repository
├── api_repository.py        # FastFish API repository
├── tracking_repository.py   # Store tracking repository
└── matrix_data_repository.py # Matrix data repository
```

**What they do:**
- **`base.py`**: Defines `ReadOnlyRepository` and `WriteableRepository` interfaces
- **`csv_repository.py`**: Handles all CSV file reading/writing
- **`api_repository.py`**: Handles all API calls to FastFish
- **`tracking_repository.py`**: Tracks processed/failed stores
- **`matrix_data_repository.py`**: Handles matrix data operations

**Why this matters:** All I/O operations are **isolated** here. Steps never directly read files or call APIs - they use repositories. This makes testing easy (mock the repositories).

---

### Refactored Step Implementations

**Location:** `/src/steps/`

```
src/steps/
├── __init__.py                    # Package initialization
├── api_download_merge.py          # Step 1 (refactored)
├── coordinate_extractor.py        # Step 2 helper
├── extract_coordinates_step.py    # Step 2 (refactored)
├── matrix_processor.py            # Step 3 helper
├── matrix_preparation_step.py     # Step 3 (refactored)
└── spu_metadata_processor.py      # SPU processing helper
```

**What they do:**
- **`api_download_merge.py`**: Refactored Step 1 - downloads and merges API data
- **`extract_coordinates_step.py`**: Refactored Step 2 - extracts store coordinates
- **`matrix_preparation_step.py`**: Refactored Step 3 - prepares clustering matrices
- Helper modules provide specialized processing logic

**Structure of each refactored step:**
1. **Type definitions** - Clear data structures using `@dataclass`
2. **Constants** - Business constants (no magic numbers)
3. **Setup phase** - Load data from repositories
4. **Apply phase** - Transform and process data
5. **Validate phase** - Validate results (raise exception on failure)
6. **Persist phase** - Save results via repositories

---

### Original (Legacy) Scripts

**Location:** `/src/step*.py` (root level)

```
src/
├── step1_download_api_data.py              # Original Step 1 (1,600+ lines)
├── step2_extract_coordinates.py            # Original Step 2
├── step3_prepare_matrix.py                 # Original Step 3
├── step4_download_weather_data.py          # Original Step 4
├── step5_calculate_feels_like_temperature.py
├── step6_cluster_analysis.py
├── step7_missing_category_rule.py
├── step8_imbalanced_rule.py
├── step9_below_minimum_rule.py
├── step10_spu_assortment_optimization.py
├── step11_missed_sales_opportunity.py
├── step12_sales_performance_rule.py
├── step13_consolidate_spu_rules.py
├── step14_create_fast_fish_format.py
... (continues through step36)
```

**Status:** These are the **original monolithic scripts** being refactored. They remain in place until refactored versions are validated and merged.

---

## 🧪 Test Structure

### Test Organization

**Location:** `/tests/`

```
tests/
├── features/                    # BDD feature files (test scenarios)
│   ├── step-1-api-download-merge.feature
│   ├── step-2-extract-coordinates.feature
│   ├── step-3-matrix-preparation.feature
│   └── ... (17 feature files)
│
├── step_definitions/            # Test implementation code
│   ├── test_step1_*.py         # Step 1 test implementations
│   ├── test_step2_*.py         # Step 2 test implementations
│   └── ...
│
├── data_generators/             # Mock data generation utilities
├── common/                      # Shared test utilities
├── conftest.py                  # Pytest configuration
└── comprehensive_test_suite_runner.py
```

**How tests work:**
1. **Feature files** define test scenarios in plain language
2. **Step definitions** implement the test logic using pytest-bdd
3. **Data generators** create synthetic test data
4. **All tests use mocked repositories** - no real API calls or file I/O

---

## 🔄 The Refactoring Process (Vitor's Workflow)

### Step-by-Step Process for Each Pipeline Step

#### Phase 1: Analysis & Test Design
1. **Take the original script** (e.g., `step1_download_api_data.py` - 1,600 lines)
2. **Send to LLM with design doc** - Ask it to analyze and list behaviors
3. **Generate test scenarios** - LLM creates plain-language test cases
4. **Create feature file** - Test scenarios written in Gherkin format
5. **Review test coverage** - Verify all behaviors are tested

#### Phase 2: Test Implementation
6. **Create test file structure** - Generate pytest-bdd test files
7. **Implement tests one by one** - Each scenario gets implemented
8. **Mock all I/O** - No real API calls, no real file operations
9. **Run tests** - They fail (no implementation yet)

#### Phase 3: Refactoring
10. **Split original code** - Divide into setup/apply/validate/persist
11. **Extract to repositories** - Move all I/O to repository classes
12. **Apply design patterns** - Use dependency injection, type hints
13. **Implement step class** - Create new refactored step following patterns
14. **Run tests iteratively** - Implement → test → fix → repeat

#### Phase 4: Validation
15. **All tests pass** - Verify complete test coverage
16. **Code review** - Check adherence to design standards
17. **Reduce line count** - Original 1,600 lines → ~600 lines
18. **Document changes** - Update documentation

#### Phase 5: Integration
19. **Keep both versions** - Original and refactored coexist
20. **Update pipeline.py** - Switch to call refactored version
21. **Run full pipeline** - Validate end-to-end
22. **Remove original** - Only after full validation

---

## 📊 Refactoring Benefits

### Code Quality Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Lines of Code** | 1,600+ | ~600 | 62% reduction |
| **Testability** | Manual only | Automated tests | 100% coverage |
| **Maintainability** | Low (monolithic) | High (modular) | Significant |
| **Readability** | Complex | Clear | Much improved |
| **Dependencies** | Hardcoded | Injected | Fully flexible |

### Technical Improvements

✅ **Dependency Injection** - All dependencies injected, easy to swap  
✅ **Repository Pattern** - All I/O isolated and mockable  
✅ **Type Safety** - Full type hints throughout  
✅ **Error Handling** - Validation by exception pattern  
✅ **Logging** - Centralized, consistent logging  
✅ **Testing** - Comprehensive automated test coverage  
✅ **Documentation** - Self-documenting code + feature files  

---

## 🎓 Understanding the Design Patterns

### The 4-Phase Step Pattern

Every refactored step follows this structure:

```python
class MyStep(Step):
    def setup(self, context: StepContext) -> StepContext:
        """Load data from repositories"""
        # Load input data
        # Prepare for processing
        return context
    
    def apply(self, context: StepContext) -> StepContext:
        """Transform and process data"""
        # Core business logic here
        # Transform data
        return context
    
    def validate(self, context: StepContext) -> None:
        """Validate results - raise exception if invalid"""
        # Check data quality
        # Raise DataValidationError if problems found
        # Return None if valid
    
    def persist(self, context: StepContext) -> StepContext:
        """Save results via repositories"""
        # Save to files/database
        return context
```

### Dependency Injection Pattern

**Bad (hardcoded):**
```python
class BadStep:
    def __init__(self):
        self.repo = CsvFileRepository("/hardcoded/path.csv")  # BAD
```

**Good (injected):**
```python
class GoodStep(Step):
    def __init__(self, repo: ReadOnlyRepository, logger: PipelineLogger, ...):
        super().__init__(logger, step_name, step_number)
        self.repo = repo  # GOOD - injected
```

### Repository Pattern

All data access goes through repositories:

```python
# Instead of this:
df = pd.read_csv("data/file.csv")  # BAD - direct I/O

# Do this:
df = self.csv_repo.get_all()  # GOOD - via repository
```

---

## 🚀 Next Steps for the Team

### For Brett (Current Task)
1. **Replace Step 1 call** in `pipeline.py` with refactored version
2. **Push changes** and open PR for review
3. **Validate** with Boris that test scenarios are correct
4. **Merge** after approval

### For Step 2 Refactoring (Next)
1. **Open new branch** for Step 2 refactoring
2. **Follow same process** as Step 1:
   - Analyze original script
   - Generate test scenarios
   - Implement tests
   - Refactor code
   - Validate
3. **Repeat** for each subsequent step

### Long-term Vision
- **All 36 steps refactored** using this pattern
- **Complete test coverage** for entire pipeline
- **Pipeline orchestrator** replaces `pipeline.py` script
- **Modular, maintainable codebase** that's easy to extend

---

## 📚 Additional Resources

### Important Files to Read

1. **`/docs/code_design_standards.md`** ⭐ - Start here for design patterns
2. **`/README.md`** - Pipeline overview
3. **`/tests/features/step-1-api-download-merge.feature`** - Example test scenarios
4. **`/src/steps/api_download_merge.py`** - Example refactored step
5. **`/src/core/step.py`** - Abstract Step base class

### Key Concepts to Understand

- **StepContext** - Data carrier between steps
- **Repository Pattern** - Data access abstraction
- **Dependency Injection** - Constructor injection of dependencies
- **4-Phase Pattern** - setup → apply → validate → persist
- **Validation by Exception** - Raise exception on validation failure
- **pytest-bdd** - Behavior-driven development testing framework

---

## 🎯 Summary

### What Vitor Built

1. **Design framework** (`/docs/code_design_standards.md`) - Blueprint for all refactoring
2. **Core infrastructure** (`/src/core/`) - Reusable framework components
3. **Repository layer** (`/src/repositories/`) - Data access abstraction
4. **Refactored Steps 1-3** (`/src/steps/`) - Working examples
5. **Test infrastructure** (`/tests/`) - Comprehensive test framework
6. **Test scenarios** (`/tests/features/*.feature`) - 17 feature files with test cases

### Where Everything Lives

- **📘 Design docs**: `/docs/code_design_standards.md`
- **🏗️ Core framework**: `/src/core/`
- **💾 Repositories**: `/src/repositories/`
- **✨ Refactored steps**: `/src/steps/`
- **🧪 Tests**: `/tests/`
- **📝 Test scenarios**: `/tests/features/*.feature`
- **📊 Merge plans**: `/process_and_merge_docs/`
- **🗂️ Original scripts**: `/src/step*.py`

### The Big Picture

This is a **systematic transformation** of a complex data pipeline from monolithic scripts to a modern, modular, testable architecture. The design document provides the blueprint, the core framework provides the foundation, and each step is being refactored one at a time following the same proven pattern.

---

**Questions?** Refer to `/docs/code_design_standards.md` for detailed design patterns and examples.
