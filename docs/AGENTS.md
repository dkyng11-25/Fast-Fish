# AI Agent Development Guidelines - Specification & Requirements

## Overview

This document establishes the **specifications, requirements, and standards** for software development using Behavior-Driven Development (BDD) methodology. This is **human-centric documentation** for team reference and understanding.

**For development methodology, progress tracking, and debugging procedures, see**: `../notes/AGENTS.md`

---

## 🎯 Development Methodology: BDD Workflow

### What is BDD?

**Behavior-Driven Development (BDD)** is a methodology that ensures software quality through:
1. Clear specifications written **before** implementation begins
2. Automated tests that validate business requirements
3. Living documentation that reflects actual system behavior
4. Strong collaboration between technical and non-technical stakeholders

### Four-Phase Development Cycle

All development work follows these four sequential phases:

| Phase | Purpose | Deliverable | Timeline |
|-------|---------|------------|----------|
| **Phase 1: Behavior Analysis** | Define expected behavior from business perspective | Feature files with Given-When-Then scenarios | Planning |
| **Phase 2: Test Scaffolding** | Create test structure before implementation | Failing test scaffold that mirrors feature files | Pre-implementation |
| **Phase 3: Code Refactoring** | Implement clean, modular code following CUPID | Working implementation matching test specifications | Development |
| **Phase 4: Test Implementation** | Convert scaffold tests to functional validation | All tests passing, documenting actual behavior | Validation |

---

## 📋 User Requirements vs System Requirements

### User Requirements (Expected Output)

**What the business expects the system to produce:**

- Business objectives and outcomes
- User stories and acceptance criteria
- Data transformations and business rules
- Performance targets (e.g., "process 10k records in < 30 seconds")
- Success metrics and KPIs
- Error handling and validation rules
- Feature scope and boundaries

**Example**:
```
User Requirement: "Extract store coordinates from raw data"
- Input: CSV files with store location data
- Output: Cleaned data with valid (latitude, longitude) pairs
- Success: All stores have coordinates, no data loss
- Performance: Complete within 30 seconds for 100k records
- Error handling: Fail fast on missing/invalid coordinates
```

### System Requirements (How We Build It)

**What the technical team implements to satisfy user requirements:**

- Architecture patterns (BDD, CUPID, 4-phase Step pattern)
- Technology stack (Python, fireducks/pandas, pytest)
- Code organization (src/steps/, src/core/, src/repositories/)
- Testing framework (pytest-bdd, BDD test structure)
- Data handling (repository pattern, dependency injection)
- Performance optimizations (fireducks acceleration)
- Code quality standards (500 LOC limit, type hints, modular design)

**Example (for same requirement)**:
```
System Requirements:
- Create ExtractCoordinatesStep class in src/steps/
- Implement 4-phase pattern: setup() → apply() → validate() → persist()
- Use fireducks.pandas for data operations
- Validate coordinates: -90 ≤ lat ≤ 90, -180 ≤ lon ≤ 180
- Use repository pattern for CSV file I/O
- Create comprehensive BDD tests with real data
```

---

## 🏗️ Architecture & Design Principles

### CUPID Principles (Code Organization)

All code must follow **CUPID** principles for maintainability:

| Principle | Definition | What It Means |
|-----------|-----------|---------------|
| **Composable** | Modular, reusable components | Small classes/functions that work together |
| **Unix Philosophy** | Do one thing well | Single responsibility per class/function |
| **Predictable** | Consistent behavior | Clear contracts, no magic or surprises |
| **Idiomatic** | Follows language conventions | Python snake_case, standard patterns |
| **Domain-based** | Business language | Names reflect business concepts, not technical jargon |

### Four-Phase Step Pattern

**Every pipeline step must implement this pattern:**

```
1. setup()      → Load data from repositories, prepare for processing
2. apply()      → Transform data according to business rules
3. validate()   → Verify data meets business constraints
4. persist()    → Save results to appropriate output locations
```

### Dependency Injection & Repository Pattern

**Core principles for all components:**

- **No hard-coded dependencies**: All external dependencies injected via constructor
- **Repository abstraction**: All I/O operations through repository interfaces
- **Centralized logging**: Single PipelineLogger for all operations
- **Type safety**: Complete type hints on public interfaces

---

## 📏 Code Quality Standards

### Size Limits & Modularization

| Constraint | Limit | Reason |
|-----------|-------|--------|
| **Maximum file size** | 500 LOC | Maintainability, cognitive load |
| **Maximum function size** | 200 LOC | Readability, testability |
| **Maximum nesting depth** | 3 levels | Complexity management |

**When a file exceeds 500 LOC**, apply CUPID-based modularization:
1. Identify distinct responsibilities
2. Extract each into separate classes/modules
3. Define clear interfaces between components
4. Use business terminology in names

### Data Processing Requirements

- **Always use**: `import fireducks.pandas as pd` for data operations
- **Never use**: Standard pandas when fireducks is available
- **Rationale**: Performance optimization for large datasets

### Test Coverage Requirements

- **Every user requirement** must have corresponding feature files (Given-When-Then scenarios)
- **Happy path scenarios**: Normal operation with valid data
- **Error scenarios**: Invalid/missing data handling
- **Edge cases**: Boundary conditions, empty data, extreme values
- **Real data**: Use actual data subsets, not synthetic test data

---

## 📁 Directory Structure & Responsibilities

### Source Code Organization (`src/`)

```
src/
├── steps/                 → One file per pipeline step
├── core/                  → Shared infrastructure (logger, step base, context)
├── repositories/          → Data access abstraction layer
├── components/            → Reusable business logic components
├── utils/                 → Pure utility functions
└── config_new/            → Configuration management
```

**Important**: Legacy step files (e.g., `step1_download_api_data.py`) in `src/` root are **reference only**. Do not modify them.

### Test Organization (`tests/`)

```
tests/
├── features/              → Gherkin feature files (Given-When-Then scenarios)
├── step_definitions/      → BDD step implementations
└── [One test file per pipeline step]
```

### Documentation Organization (`docs/`)

```
docs/
├── AGENTS.md              → This file (specifications & requirements)
├── bdd_test_*.md          → BDD testing procedures
├── behaviour_*.md         → Business behavior documentation
└── [One doc per major process]
```

**Note**: Every pipeline step should have its own documentation file explaining inputs, outputs, transformations, and business rules.

### Development Notes Organization (`notes/`)

```
notes/
├── todo_YYYYMMDD_*.md        → Task checklists (incremental updates)
├── worklog_YYYYMMDD_*.md     → Session progress logs
├── debug_YYYYMMDD_*.md       → Issue investigation logs
├── rca_YYYYMMDD_*.md         → Root cause analysis (5 hypotheses)
├── research_YYYYMMDD_*.md    → Best practices & solutions research
├── brainstorm_YYYYMMDD_*.md  → Creative ideation & alternatives
├── plan_YYYYMMDD_*.md        → Project planning & feasibility
├── learning_YYYYMMDD_*.md    → Tool & library documentation
└── procedure_YYYYMMDD_*.md   → Established development procedures
```

**See**: `../notes/AGENTS.md` for development methodology and progress tracking.

---

## ✅ Quality Assurance Standards

### Code Review Checklist

- [ ] All files ≤ 500 LOC
- [ ] All functions ≤ 200 LOC
- [ ] Complete type hints on public interfaces
- [ ] Docstrings on all classes and methods
- [ ] No hard-coded values or paths
- [ ] All dependencies injected via constructor
- [ ] Uses fireducks.pandas (not standard pandas)
- [ ] No print() statements (use logger)
- [ ] Error handling with DataValidationError
- [ ] Follows naming conventions (snake_case for Python)

### Test Review Checklist

- [ ] Feature files describe business requirements clearly
- [ ] Tests use real data, not synthetic/mock data
- [ ] Happy path scenario documented
- [ ] Error cases covered with validation failures
- [ ] Edge cases identified and tested
- [ ] All tests have binary outcomes (PASS/FAIL only)
- [ ] No conditional or suppressed test logic
- [ ] Test assertions are specific and meaningful
- [ ] Test fixture properly initializes and cleans up

### Integration Checklist

- [ ] Code compiles/syntax is valid
- [ ] All imports resolve correctly
- [ ] Tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors
- [ ] 500 LOC compliance verified
- [ ] Fireducks pandas usage verified
- [ ] Feature files align with code behavior
- [ ] Documentation updated for new features

---

## 🚀 Development Workflow

### Before You Code

1. **Analyze Requirements**: Understand the business problem
2. **Write Feature Files**: Document expected behavior in Gherkin
3. **Create Test Scaffold**: Build failing test structure
4. **Plan Components**: Design modular architecture

### During Development

1. **One component at a time**: Complete, test, move on
2. **Continuous validation**: Run tests after each method
3. **Monitor file size**: Stop if approaching 500 LOC limits
4. **Document as you go**: Docstrings, comments, type hints

### After Implementation

1. **Convert test scaffolds**: Replace placeholders with real tests
2. **Verify test coverage**: All scenarios should pass
3. **Code review**: Check against quality standards
4. **Integration testing**: Verify pipeline end-to-end
5. **Documentation**: Update feature documentation

---

## 🎓 Pipeline Steps Documentation

### Per-Step Documentation Requirements

Each pipeline step should have documentation covering:

#### User Requirements (What)
- **Step objective**: What business problem does it solve?
- **Input data**: What data comes in? Where from?
- **Output data**: What is produced? Where does it go?
- **Business rules**: What transformations or validations apply?
- **Success criteria**: How do we know it worked?
- **Error handling**: What goes wrong? How should it fail?

#### System Requirements (How)
- **Implementation location**: Which file in `src/steps/`?
- **Dependencies**: What other steps or components does it depend on?
- **Performance targets**: Processing time for typical dataset sizes
- **Testing approach**: What scenarios must be tested?
- **Error conditions**: What exceptions can be thrown?

#### Example Documentation Structure

```markdown
# Step 2: Extract Coordinates

## What (User Requirements)
- **Objective**: Validate and extract store location coordinates
- **Input**: Raw CSV with store data including lat/lon fields
- **Output**: Cleaned data with validated (latitude, longitude) pairs
- **Rules**: 
  - Latitude: -90 to +90 degrees
  - Longitude: -180 to +180 degrees
  - No null values allowed
- **Success**: All stores have valid coordinates, zero data loss
- **Errors**: Missing/invalid coordinates → DataValidationError

## How (System Requirements)
- **File**: `src/steps/extract_coordinates.py`
- **Class**: `ExtractCoordinatesStep`
- **Pattern**: 4-phase (setup → apply → validate → persist)
- **Dependencies**: CSVRepository, PipelineLogger
- **Performance**: 100k records in < 30 seconds
- **Tests**: 7 scenarios covering happy path, errors, edge cases
- **Exceptions**: 
  - DataValidationError (missing/invalid coordinates)
  - RepositoryError (file I/O issues)
```

---

## 📚 Environment & Tools

### Required Software

| Tool | Purpose | Installation |
|------|---------|--------------|
| Python 3.10+ | Programming language | System package manager |
| uv | Package & environment management | Homebrew |
| pytest | Test framework | `uv pip install pytest` |
| pytest-bdd | BDD test framework | `uv pip install pytest-bdd` |
| fireducks | Accelerated pandas | `uv pip install fireducks` |
| Git | Version control | System package manager |

### Terminal Tools

| Tool | Purpose | When to Use |
|------|---------|------------|
| `eza` | File listing | Exploring directory structure |
| `skim` | Fuzzy finder | Finding files or log patterns |
| `xan` | CSV inspection | Analyzing data files |
| `tokei` | Line counting | Checking code metrics |
| `tldr` | Command reference | Learning command usage |

---

## 🔄 Change Management

### Making Changes to Existing Code

**Principle**: "Chesterton's Fence" - Understand why something exists before changing it.

1. **Before modifying code**:
   - Read the feature file (understand the requirement)
   - Check the test file (understand current behavior)
   - Review comments/docstrings (understand the logic)
   - Ask: "Why was this done this way?"

2. **When modifying code**:
   - Make incremental changes (never full rewrites)
   - Preserve all docstrings and comments
   - Keep functions under 200 LOC
   - Update tests to match new behavior
   - Never suppress test failures

3. **After modifying code**:
   - Run all related tests
   - Verify file size compliance (≤ 500 LOC)
   - Update documentation
   - Document rationale in code comments

### Adding New Features

1. **Start with Phase 1**: Write feature file with Given-When-Then scenarios
2. **Move to Phase 2**: Create failing test scaffold
3. **Proceed to Phase 3**: Implement clean code following CUPID
4. **Complete with Phase 4**: Convert scaffold to functional tests
5. **Document**: Write human-centric documentation

---

## 🆘 Getting Help & Escalation

### Questions to Ask Before Starting

- **"What is the user requirement here?"** → Read the feature file
- **"How should this behave?"** → Check existing tests
- **"Why was it done this way?"** → Read code comments
- **"How do I run tests?"** → `uv run pytest tests/ -v`
- **"What's the current status?"** → Check notes/ for progress logs

### Where to Find Information

| Question | Location |
|----------|----------|
| Expected behavior | Feature files in `tests/features/` |
| How to implement | Reference existing step in `src/steps/` |
| Progress tracking | Notes in `notes/` folder |
| Tool usage | `tldr command_name` or `learning_*.md` files |
| Debugging help | `rca_*.md` and `debug_*.md` files |

---

## 📖 Summary: Documentation vs Notes

### This File (Specifications & Requirements)

**Audience**: Team members, stakeholders, code reviewers  
**Purpose**: Understand WHAT to build and WHY  
**Content**:
- User requirements and business objectives
- Architecture and design principles
- Quality standards and best practices
- Directory structure and organization
- Integration procedures
- Step-specific documentation

### Development Notes (Methodology & Progress)

**Audience**: Developers doing the work  
**Purpose**: Document HOW to build and track progress  
**Content**:
- BDD methodology and procedures
- RCA (5 hypotheses analysis)
- TODO lists and progress tracking
- Debug sessions and findings
- Research and learning notes
- Brainstorming and planning

---

## ✨ Final Principles

1. **Separate concerns**: Specifications separate from progress/methodology
2. **Human-centric**: Documentation written for team understanding, not for parsing
3. **Requirements clarity**: Every feature has clear user and system requirements
4. **Binary outcomes**: Tests either PASS or FAIL - no conditional logic
5. **Incremental development**: One component at a time, not everything simultaneously
6. **Comprehensive documentation**: Every change is documented with rationale
7. **Real-world testing**: Use real data, real scenarios, real constraints
