# AI Agent Development Guidelines

## 🎯 Behavior-Driven Development (BDD) Workflow

### Overview
This document establishes a comprehensive **Behavior-Driven Development (BDD)** methodology that ensures software quality through collaboration, clear specifications, and automated testing. The workflow follows a structured 4-phase approach:

1. **Phase 1: Behavior Analysis & Use Cases** - Define expected behavior using Given-When-Then scenarios
2. **Phase 2: Test Scaffolding** - Create test structure before implementation
3. **Phase 3: Code Refactoring** - Apply CUPID principles and 4-phase Step pattern
4. **Phase 4: Test Implementation** - Convert scaffolds to functional tests

### Core BDD Principles
- **Given-When-Then**: All scenarios follow this declarative format for clear specification
- **Feature Files First**: Gherkin scenarios define behavior before implementation begins
- **Test-Driven**: Tests are written before functional code and guide development
- **Binary Outcomes**: All tests must clearly PASS or FAIL - no conditional results
- **Living Documentation**: Tests serve as both validation and documentation
- **Methodical Sequencing**: Work incrementally, one component at a time with continuous feedback
- **Iterative Enhancement**: Build, test, debug, and improve in focused cycles rather than attempting everything simultaneously

## ⚖️ Balancing Speed and Quality: Methodical Development

### Methodical vs Hasty Development
**❌ Hasty Approach (Avoid):**
- Attempting to implement multiple components simultaneously
- Rushing through testing without proper validation
- Accumulating technical debt through quick fixes
- Making assumptions without verification
- Overloading todo lists with too many parallel tasks

**✅ Methodical Approach (Recommended):**
- **Sequential Focus**: Complete one component fully before starting the next
- **Iterative Enhancement**: Build → Test → Debug → Improve in focused cycles
- **Continuous Feedback**: Regular validation and adjustment based on results
- **Technical Debt Management**: Address issues immediately rather than deferring
- **Clear Communication**: Regular updates on progress and blockers

### Sequential Development Workflow

#### 1. Single-Component Focus
```bash
# Focus on ONE step at a time, not multiple simultaneously
# Example: Complete Step 2 fully before starting Step 3

# Phase 1: Analyze and plan Step 2 only
# - Read legacy step2_extract_coordinates.py
# - Create behavior analysis and feature file
# - Plan modular components needed

# Phase 2: Create scaffold tests for Step 2 only
# - Generate test_step2_scaffold.py
# - Verify all tests fail as expected

# Phase 3: Implement Step 2 components sequentially
# - Create ExtractCoordinatesStep class
# - Add setup() method first, test it
# - Add apply() method, test it
# - Add validate() method, test it
# - Add persist() method, test it

# Phase 4: Convert scaffold to functional tests
# - Replace pytest.fail() with real implementations
# - Add real mocks and test data
# - Validate all scenarios pass

# Only then move to Step 3...
```

#### 2. Continuous Integration and Validation
```bash
# Validate each change immediately, not at the end
uv run pytest tests/test_step2_extract_coordinates.py -v
# ✅ PASS: Continue to next component

# Debug and fix immediately when issues arise
uv run pytest tests/test_step2_extract_coordinates.py::test_coordinate_extraction_fails -v -s
# ❌ FAIL: Debug, fix, retest - don't continue with broken code
```

#### 3. Technical Debt Management
```bash
# Address technical debt immediately, not later
find src/ tests/ -name "*.py" -exec wc -l {} + | awk '$1 > 500 {print "MODULARIZE: " $2 ": " $1 " lines"}'
# If violations found: STOP and modularize before continuing

# Regular refactoring sessions
grep -r "TODO\|FIXME\|HACK" src/  # Address these immediately
```

#### 4. Clear Goals and Scope Definition
```bash
# Define specific, measurable objectives for each session
# ✅ "Complete Step 2 coordinate extraction with full test coverage"
# ❌ "Work on multiple pipeline steps simultaneously"

# Set time-boxed sessions with clear deliverables
# "2-hour session: Complete Step 2 setup() and apply() methods with tests"
```

### Feedback and Enhancement Cycles

#### 1. Regular Validation Points
- **After each method implementation**: Run targeted tests
- **After each component completion**: Full integration test
- **After each step completion**: End-to-end pipeline validation
- **Daily/Weekly**: Technical debt review and refactoring

#### 2. User Feedback Integration
```bash
# Incorporate user requirements systematically
# 1. Document user requirements in notes/requirements_YYYYMMDD.md
# 2. Create feature files based on requirements
# 3. Implement and test against feature specifications
# 4. Validate with user before marking complete
```

#### 3. Automated Quality Gates
```bash
# Essential verification before considering work complete
find src/ tests/ -name "*.py" -exec wc -l {} + | awk '$1 > 500 {exit 1}' && echo "✅ Size compliance"
uv run pytest tests/ -x --tb=short  # Stop on first failure
grep -r "import fireducks.pandas as pd" src/ | wc -l  # Verify pandas acceleration
```

### Communication and Collaboration

#### 1. Progress Transparency
```bash
# Regular status updates in notes/worklog_YYYYMMDD.md
echo "# $(date +%Y-%m-%d %H:%M) - Completed Step 2 apply() method" >> notes/worklog_$(date +%Y%m%d).md
echo "# Next: Step 2 validate() method, estimated 45 minutes" >> notes/worklog_$(date +%Y%m%d).md
```

#### 2. Blocker Documentation
```bash
# Document issues immediately when discovered
echo "# $(date +%Y-%m-%d %H:%M) - BLOCKER: API rate limiting issue" >> notes/debug_$(date +%Y%m%d)_api_issue.md
echo "# Investigation: Need to implement retry logic with exponential backoff" >> notes/debug_$(date +%Y%m%d)_api_issue.md
```

#### 3. Success Criteria Definition
```bash
# Define clear completion criteria for each task
# ✅ "Step 2 coordinate extraction: All tests pass, 100% test coverage, no linting errors"
# ✅ "Performance: Processes 10k records in < 30 seconds"
# ❌ "Work on coordinate extraction" (too vague)
```

## 📏 Code Length Limits & Modularization

### Code Size Constraints
**Maximum 500 Lines of Code (LOC) per file** - This applies to both source code and test code.

#### Rationale
- **Maintainability**: Smaller files are easier to understand, review, and modify
- **Cognitive Load**: Developers can hold the entire file context in working memory
- **Debugging**: Issues are easier to isolate and fix in smaller code units
- **Code Reviews**: More focused and effective peer reviews
- **Testing**: Each module can be tested independently with clear boundaries

#### Verification Tools
```bash
# Check line counts for all Python files
find src/ tests/ -name "*.py" -exec wc -l {} + | sort -nr

# Alternative using tokei (more detailed analysis)
tokei src/ tests/ --sort lines

# Find files exceeding 500 LOC
find src/ tests/ -name "*.py" -exec wc -l {} + | awk '$1 > 500 {print $2 ": " $1 " lines"}'

# Use complexipy to assess readability and suggest modularization
complexipy src/ tests/ --min 500
```

### CUPID-Based Modularization

When code exceeds 500 LOC, **mandatory modularization** must follow CUPID principles:

#### 1. Composable (Modular and Reusable)
**❌ Before (Monolithic > 500 LOC):**
- Single large file with mixed responsibilities
- 1000+ line methods doing everything
- Load configuration, validate data, transform, format output, save results, generate reports, send notifications

**✅ After (Composable Components):**
- Modularized into focused components (80-150 lines each)
- DataLoader: Single responsibility for loading data
- DataValidator: Single responsibility for validation
- DataTransformer: Single responsibility for transformation
- ReportGenerator: Single responsibility for report generation
- DataPipeline: Orchestrates components with dependency injection

#### 2. Unix Philosophy (Single Responsibility)
**❌ Before (Multiple Responsibilities):**
- Function does too many things: process, save, report, notify, log
- 200 lines processing + 100 lines saving + 150 lines reporting + 100 lines notification + 50 lines logging

**✅ After (Unix Philosophy - Do One Thing Well):**
- process_data(): 200 lines focused only on data processing
- save_to_database(): 80 lines focused only on database operations
- generate_report(): 120 lines focused only on report generation
- send_notification(): 60 lines focused only on notification logic

#### 3. Predictable (Consistent Behavior)
**❌ Before (Unpredictable):**
- Behavior depends on magic parameters or external state
- Different execution paths based on mode flags
- Unclear contracts and unpredictable outcomes

**✅ After (Predictable Behavior):**
- FastDataProcessor: Always processes data quickly with consistent behavior
- ThoroughDataProcessor: Always processes data thoroughly with consistent behavior
- Clear contracts and predictable outcomes

#### 4. Idiomatic (Python Conventions)
**❌ Before (Non-Idiomatic):**
- camelCase instead of snake_case, manual loops instead of pandas idioms
- Old-style string formatting and manual iteration patterns
- Non-standard class and method naming conventions

**✅ After (Idiomatic Python):**
- Proper snake_case naming throughout codebase
- Leverages pandas idioms instead of manual loops
- Uses pathlib for file paths and context managers
- Follows Python type hints and modern conventions

#### 5. Domain-based (Business Language)
**❌ Before (Technical Jargon):**
- Generic function names like `transform_data_v1`
- Technical column names without business context
- Method names that don't reflect business processes

**✅ After (Domain-based Language):**
- ProductCatalogCleaner: Clear business domain context
- remove_discontinued_products(): Business logic naming
- ensure_valid_pricing(): Business requirement focus
- clean_product_catalog(): Complete business process description

### Modularization Workflow

#### Step 1: Identify Oversized Files
```bash
# Find all Python files and their line counts
find src/ tests/ -name "*.py" -exec wc -l {} + | sort -nr

# Identify files over 500 LOC
find src/ tests/ -name "*.py" -exec wc -l {} + | awk '$1 > 500 {print $2 ": " $1 " lines"}'
```

#### Step 2: Analyze with Complexipy
```bash
# Assess readability and suggest modularization points
complexipy src/path/to/large_file.py --threshold 500

# Get detailed complexity metrics
complexipy src/ tests/ --format json | jq '.files[] | select(.lines > 500)'
```

#### Step 3: Apply CUPID Modularization
1. **Identify Responsibilities**: List all distinct responsibilities in the file
2. **Extract Components**: Create separate classes/functions for each responsibility
3. **Define Clear Interfaces**: Establish contracts between components
4. **Apply Domain Language**: Use business terminology in naming and documentation
5. **Verify Composability**: Ensure components can be combined and reused

#### Step 4: Verify Modularization Success
```bash
# Confirm no files exceed 500 LOC
find src/ tests/ -name "*.py" -exec wc -l {} + | awk '$1 > 500 {print "VIOLATION: " $2 ": " $1 " lines"}' | wc -l

# Should return 0 violations

# Verify components are properly separated
find src/ tests/ -name "*.py" -exec wc -l {} + | sort -nr | head -10

# Check for proper imports between modules
grep -r "from src\." src/ | grep -v __init__ | sort | uniq
```

### Integration with BDD Workflow

#### Phase 1: Behavior Analysis
- **Analyze legacy code size** during behavior analysis
- **Document modularization requirements** in behavioral analysis notes
- **Plan component boundaries** based on business domain

#### Phase 2: Test Scaffolding
- **Create scaffold tests** for each planned component
- **Ensure test files** also respect 500 LOC limit
- **Plan test organization** to mirror component structure

#### Phase 3: Code Refactoring
- **Implement modular components** following CUPID principles
- **Apply 4-phase pattern** to each component individually
- **Ensure each file** stays under 500 LOC
- **Use dependency injection** between components

#### Phase 4: Test Implementation
- **Test each component** independently
- **Verify component interactions** through integration tests
- **Ensure test files** also follow 500 LOC limit

## 🛠️ Development Environment Setup

### Package Management
- **Use `uv pip install`** for Python packages (not `pip`)
- **Single environment per project** - use `uv` managed environment
- Install all at once: `uv pip install -e ".[dev]" pytest pytest-bdd fireducks complexipy`
- **Homebrew packages** (terminal/OS level): `brew install tealdeer xan tokei eza rip2 skim procs choose`
- **🚫 CRITICAL: Only one venv per project** - Always use the project's single virtual environment instead of installing packages in the local system to prevent conflicts, version mismatches, and dependency issues. Never create multiple virtual environments or install packages globally.

### Data Processing Acceleration
- **Use `import fireducks.pandas as pd`** for accelerated pandas operations
- Drop-in replacement for pandas with significant speed improvements
- Maintains full pandas API compatibility

### Terminal Best Practices
- **🚫 Never use `python -c`** - use proper test frameworks instead
- **🚫 Never use `rm`** - use `rip2` for safer file deletion (prevents accidental breakage)
- **🚫 Never create one-off test scripts** - use proper BDD test structure
- **🚫 Never do full code deletes** - incrementally modify to preserve progress

### Terminal Tool Reference Procedure
**When learning terminal commands, follow this escalation:**

1. **`tldr command_name`** - Quick practical examples (installed via Homebrew)
2. **`command_name --help`** - Detailed options when `tldr` insufficient
3. **Search online** - Document findings in `notes/learning_$(date +%Y%m%d)_tool.md`

**Benefits:** Reduces docs bloat, encourages self-service, maintains current knowledge, builds terminal literacy

## 📋 BDD Development Phases

### Phase 1: Behavior Analysis & Use Case Definition
**Objective**: Define expected system behavior using clear, declarative scenarios before any implementation begins.

#### 1.1 Given-When-Then Scenario Format
All use cases must follow the **Given-When-Then** structure:

- **Given-When-Then format**: All scenarios follow this declarative structure
- **Business perspective**: Use domain terminology stakeholders understand
- **Complete coverage**: Include happy path, error cases, and edge conditions
- **Independent scenarios**: Each scenario can run in isolation

#### 1.2 Behavioral Analysis Process
1. **Analyze Legacy Code**: Deconstruct existing functionality into four phases:
   - **Setup Analysis**: Where data comes from (e.g., "Loads CSV from repository")
   - **Apply Analysis**: Core transformations (e.g., "Removes duplicates and fills nulls")
   - **Validate Analysis**: Business rules (e.g., "Data must have no nulls in price column")
   - **Persist Analysis**: Where results are saved (e.g., "Saves to output repository")

2. **Create Feature Files**: Write declarative scenarios from business perspective:
   - **✅ GOOD**: `Given raw product data with duplicates and null prices`
   - **❌ BAD**: `Given the source_repo mock is configured to return test data`

3. **Include Failure Scenarios**: Every feature must have validation failure tests to ensure proper error handling.

#### 1.3 Scenario Generation Rules
- **Declarative Language**: Describe what happens, not how it's implemented
- **Business Context**: Use domain terminology that stakeholders understand
- **Complete Coverage**: Include happy path, error cases, and edge conditions
- **Independent Scenarios**: Each scenario must be able to run in isolation

### Phase 2: Test Scaffolding (Pre-Implementation)
**Objective**: Create test structure that mirrors feature files exactly, ensuring all tests fail until real implementation exists.

#### 2.1 Scaffold Structure Requirements
- **Mirror Feature Files**: Test organization must match feature file sequence exactly
- **Per-Scenario Organization**: Each scenario gets complete section with clear boundaries
- **Binary Failure**: All tests must fail with clear "SCAFFOLDING PHASE" messages
- **No Mock Data**: Pure placeholders only - no pandas DataFrames or test data

#### 2.2 Scaffold File Structure
- Each scenario gets its own complete section with clear header comments
- Steps organized by scenario: @scenario → @fixture → @given → @when → @then
- Order within scenario matches feature file sequence exactly
- All functions use `pytest.fail()` with clear "SCAFFOLDING PHASE" messages

#### 2.3 Scaffold Verification
```bash
# Verify all scaffold tests fail as expected
uv run pytest tests/test_*_scaffold.py -v
# Expected: All tests fail with "SCAFFOLDING PHASE" messages

# Verify no real implementation exists
grep -c "pytest.fail" tests/test_*_scaffold.py  # Should match scenario count
```

### Phase 3: Code Refactoring (CUPID Principles)
**Objective**: Transform legacy code into clean, maintainable implementation following established design standards.

#### 3.1 Four-Phase Step Pattern
All refactored code must implement the **setup → apply → validate → persist** execution pattern:
- **setup()**: Load and prepare data from repositories
- **apply()**: Transform data according to business rules
- **validate()**: Verify data integrity and business constraints
- **persist()**: Save results to appropriate output repositories

#### 3.2 CUPID Compliance Principles
- **Composable**: Modular components that can be combined and reused
- **Unix Philosophy**: Each component does one thing well (single responsibility)
- **Predictable**: Consistent behavior with clear contracts
- **Idiomatic**: Follow Python conventions and best practices
- **Domain-based**: Use business language in code structure and naming

#### 3.3 Dependency Injection
- **Repository Pattern**: All I/O through repository abstractions
- **Constructor Injection**: Dependencies injected via constructor parameters
- **Centralized Logging**: Single PipelineLogger instance for all operations
- **Type Safety**: Complete type hints on all public interfaces

### Phase 4: Test Implementation & Validation
**Objective**: Convert scaffolding into functional tests that validate the refactored implementation.

#### 4.1 Implementation Process
1. **Convert Scaffolding**: Replace `pytest.fail()` calls with real implementations
2. **Add Real Mocks**: Replace `None` values with functional mock objects
3. **Implement Logic**: Add actual test execution and assertions
4. **Validate Behavior**: Ensure implementation matches feature file specifications

#### 4.2 Test Structure
- **Central fixture** holds step, mocks, context, and exception state
- **Given steps** configure mocks and test data
- **When steps** execute the actual step implementation
- **Then steps** validate results and assert expected behavior

#### 4.3 Binary Test Outcomes
- **✅ PASS**: Implementation matches feature file specifications
- **❌ FAIL**: Implementation doesn't match requirements (fix implementation, not tests)
- **🚫 NEVER**: Suppress failures or use conditional pass/fail logic

## 📁 Directory Structure and Purpose

### @src/ - Source Code (Modular Organization)
- **Location for all source code** implementation with strict modular organization
- **🚫 DO NOT MODIFY legacy code** in files directly under `src/` that start with "step" followed by numbers (e.g., `step1_download_api_data.py`, `step14_create_fast_fish_format.py`)
- **Legacy files are reference-only** - they serve as documentation of existing functionality
- **All new implementations** must go in appropriate subdirectories (`src/steps/`, `src/core/`, `src/repositories/`, etc.)

### @src/steps/ - Pipeline Steps (1 File Per Step)
- **Exactly 1 file per step** - no duplicate implementations allowed
- **Consolidate duplicate code** into shared utilities when found
- **Refactored step implementations** go here following the 4-phase Step pattern
- **Hub folder for all pipeline step logic** - organize by step number (e.g., `extract_coordinates.py`, `matrix_preparation_step.py`)
- **No legacy step files** should be modified - create new implementations in this folder

### @src/core/ - Core Infrastructure (Critical Hub)
- **Central hub for shared infrastructure** - treat with extra care during development
- Core components: `context.py`, `logger.py`, `step.py`, `exceptions.py`, `pipeline.py`
- **Dependency injection framework** and base classes for all pipeline steps
- **Pipeline orchestration logic** and execution framework
- **Error handling and logging infrastructure** shared across all steps
- **🚫 High impact changes** - modifications here affect the entire pipeline

### @src/repositories/ - Data Access Layer (Modular I/O)
- **Repository pattern implementations** for all data sources and destinations
- **Abstractions for CSV, API, database, and file system operations**
- **Modular data access** with clear interfaces and dependency injection
- **Centralized configuration** for data paths and connection parameters
- **Hub folder for all I/O operations** - organize by data source type

### @src/components/ - Reusable Components
- **Shared business logic components** that can be used across multiple steps
- **Utility functions and classes** extracted from monolithic step implementations
- **Domain-specific logic** organized by business capability
- **Composable building blocks** for complex pipeline operations

### @src/utils/ - Utility Functions
- **Pure utility functions** with no business logic dependencies
- **Helper functions for data manipulation, validation, and formatting**
- **Common operations** used across multiple components
- **Keep this folder lean** - avoid business logic, use `src/components/` instead

### @src/config_new/ - Configuration Management (Hub)
- **Centralized configuration management** - treat with extra care
- **Environment-specific settings** and pipeline parameters
- **Data source configuration** and connection parameters
- **🚫 High impact folder** - changes here affect the entire pipeline system

### @tests/ - BDD Testing (Modular Test Organization)
- **Location for all Behavior-Driven Development (BDD) tests**
- Feature files in `tests/features/` define expected behavior using Gherkin syntax
- Step definitions in `tests/step_definitions/` implement the actual test logic
- **Test organization**: Fast unit tests vs slow integration tests
- **Data validation**: Use real data subsets, minimize synthetic/mock data
- **Coverage**: Every pipeline step must have comprehensive BDD test coverage
- **1 test file per step** - maintain the same modular organization as source code

### @docs/ - Human-Driven Documentation
- **Human-centric documentation** and procedures
- Process guides, refactoring standards, and operational procedures
- Code standards, architectural decisions, and design documentation
- **Keep procedural documentation here** (e.g., "how to run the pipeline", "deployment guides")

### @notes/ - Technical Development Notes (Comprehensive Standards)

#### Note-Taking Standards
**Every note must include creation and modification dates using CLI `date` command:**
```bash
# Always include in note headers
echo "# $(date +%Y-%m-%d) - Note Title" >> notes/note_name_$(date +%Y%m%d).md
echo "# Last modified: $(date +%Y-%m-%d %H:%M:%S)" >> notes/existing_note.md
```

**Dates are MANDATORY - Document for traceability and knowledge management:**
- **Creation Date**: Record when analysis began (use `date +%Y-%m-%d`)
- **Last Modified Timestamp**: Update every time you edit (use `date +%Y-%m-%d %H:%M:%S`)
- **Purpose**: Prevents outdated information from being used, enables time-based filtering, aids knowledge lifecycle management
- **CLI Command**: Always use `date` command in terminal for consistency across team

#### Note Categories and Organization

**1. Todo Lists and Work Logs (Store Separately)**
- **Todo lists**: `notes/todo_YYYYMMDD_description.md` - comprehensive, self-expanding based on added details
- **Work logs**: `notes/worklog_YYYYMMDD_activity.md` - progressive tracking of development activities
- **Meeting notes**: `notes/meeting_YYYYMMDD_topic.md` - decisions, action items, and follow-ups
- **CRITICAL**: Never mix todo lists with work logs - maintain separate files for each responsibility

**2. Brainstorming, Research, and Planning (Stored in @notes/)**
- **Brainstorming**: `notes/brainstorm_YYYYMMDD_topic.md` - ideas, alternatives, and creative solutions
  - Free-form exploration of possibilities
  - Multiple competing ideas documented side-by-side
  - Links to supporting research and evidence
  
- **Research notes**: `notes/research_YYYYMMDD_topic.md` - field notes from online searches and best practices
  - Online search terms and sources consulted
  - Key findings with URLs and references
  - Comparison of multiple approaches
  - Evidence supporting each approach
  
- **Planning documents**: `notes/plan_YYYYMMDD_initiative.md` - detailed project plans and feasibility analysis
  - Goals and objectives clearly stated
  - Resource requirements identified
  - Timeline and milestones defined
  - Risk analysis and mitigation strategies
  
- **Proposals**: `notes/proposal_YYYYMMDD_solution.md` - solution proposals with rationale and constraints
  - **Solution Feasibility**: Technical viability assessment
  - **Implementation Rationale**: Why this solution over alternatives
  - **Observable Constraints**: Technical limitations, performance requirements, compatibility needs
  - **Cost-Benefit Analysis**: Trade-offs between different approaches
  - **User Requirements Context**: Why requirements exist and their business context

**3. Debugging and Issue Tracking (Comprehensive for Traceback)**
- **Bug reports**: `notes/bug_YYYYMMDD_issue.md` - comprehensive logs for issue traceback
  - Issue Description: What, When, Where, Expected vs Actual
  - Reproduction Steps: Numbered sequence with specific parameters
  - Environment Context: Python versions, system config, data state
  - Initial Analysis: Error messages, stack traces, system state
  - Investigation Plan: Hypotheses, tools, expected outcomes
  - Resolution and Prevention: Root cause, solution, prevention measures
  - **CRITICAL**: Bug logs must be comprehensive enough for updates to plans and todo lists
  - **CRITICAL**: Bug logs must enable fast issue traceback with first/last 50-150 characters if entries too long
  
- **Debug sessions**: `notes/debug_YYYYMMDD_session.md` - step-by-step debugging process and findings
  - Chronological record of investigation steps
  - Tools used and output observed
  - Hypotheses tested and eliminated
  - Key findings and evidence collected
  
- **Root Cause Analysis**: `notes/rca_YYYYMMDD_incident.md` - systematic analysis with 5 possible causes
  - Issue definition
  - Data gathered
  - 5 possible root causes analyzed
  - Non-causes eliminated with evidence
  - Primary root cause confirmed
  - Prevention strategy
  
- **Error patterns**: `notes/error_pattern_YYYYMMDD_type.md` - recurring issues and prevention strategies
  - Error signature and symptoms
  - When and where it occurs
  - Affected components
  - Prevention measures
  - Related RCA references

**4. Learning and Tool Documentation**
- **Tool learning**: `notes/learning_tool_YYYYMMDD.md` - HomeBrew packages and SOTA Python libraries
- **API documentation**: `notes/api_YYYYMMDD_service.md` - API endpoints, parameters, and usage patterns
- **Library research**: `notes/library_YYYYMMDD_package.md` - package capabilities, alternatives, and selection rationale

#### Writing Format Standards

**Concise and Plain Writing**
- **Break complex items** into smaller, digestible parts for comprehensive coverage
- **Use clear section headers** and bullet points for easy scanning
- **Include timestamps** for all significant events and decisions
- **Document reasoning** behind technical choices and trade-offs
- **Single responsibility**: Each note focuses on ONE topic (not mixing concerns)

**Brainstorming Format (Free-Form Exploration)**
```markdown
# $(date +%Y-%m-%d) - Brainstorm: [Topic Name]
# Last modified: $(date +%Y-%m-%d %H:%M:%S)

## Problem Statement
[What are we trying to solve]

## Possible Solutions
### Idea 1: [Name]
- Concept: [Description]
- Pros: [Advantages]
- Cons: [Disadvantages]
- Feasibility: [Quick assessment]
- Research needed: See ../notes/research_YYYYMMDD_topic.md

### Idea 2: [Name]
...

### Idea 3: [Name]
...

## Evaluation
- [Comparative analysis]
- [Consensus on best approach]

## Next Steps
- [ ] Research Idea 1 feasibility
- [ ] Prototype Idea 2
- [ ] Validate with stakeholders
```

**Research Format (Field Notes from Online Research)**
```markdown
# $(date +%Y-%m-%d) - Research: [Topic/Pattern Name]
# Last modified: $(date +%Y-%m-%d %H:%M:%S)

## Research Objective
[What question were we trying to answer]

## Search Terms Used
- [Search term 1]
- [Search term 2]
- [Search term 3]

## Sources Consulted
- Source 1: [URL/Reference with key points]
- Source 2: [URL/Reference with key points]
- Source 3: [URL/Reference with key points]

## Key Findings
1. [Finding 1 with evidence and URL]
2. [Finding 2 with evidence and URL]
3. [Finding 3 with evidence and URL]

## Approaches Compared
[Detailed comparison of multiple approaches]

## Solution Feasibility Assessment
- Technical Viability: [Can we build this]
- Resource Requirements: [What do we need]
- Timeline: [How long will it take]
- Risks: [What could go wrong]

## Recommendation
- **Chosen approach**: [Why]
- **Implementation Rationale**: [Why this over alternatives]
- **Success criteria**: [How to measure success]

## Related Documentation
- Brainstorm: See ../notes/brainstorm_YYYYMMDD_topic.md
- Plan: See ../notes/plan_YYYYMMDD_initiative.md
```

**Planning Format (Project Plans with Feasibility)**
```markdown
# $(date +%Y-%m-%d) - Plan: [Initiative Name]
# Last modified: $(date +%Y-%m-%d %H:%M:%S)

## Objective
[What are we planning to accomplish]

## Goals
- Goal 1: [Specific outcome]
- Goal 2: [Specific outcome]

## User Requirements Context
[Why these requirements exist and their business context]

## Observable Constraints
[Technical limitations, performance requirements, compatibility needs]

## Resource Requirements
- People: [Skills needed]
- Tools: [Software/hardware]
- Time: [Estimated duration]

## Timeline & Milestones
- [Date range] - [Phase/milestone]
- [Date range] - [Phase/milestone]

## Risk Analysis
- Risk 1: [Impact, Likelihood, Mitigation]
- Risk 2: [Impact, Likelihood, Mitigation]

## Success Criteria
- Metric 1: [How to measure]
- Metric 2: [How to measure]

## Related Research
See: ../notes/research_YYYYMMDD_solution.md
```

**Bug-Related Logs (Comprehensive for Traceback & Planning Updates)**
- **Issue Description**: What, When, Where, Expected vs Actual
- **Reproduction Steps**: Numbered sequence with specific parameters
- **Environment Context**: Python versions, system config, data state
- **Initial Analysis**: Error messages, stack traces (first/last 50-150 chars if too long), system state
- **Investigation Plan**: Hypotheses, tools, expected outcomes
- **Findings**: Evidence collected, patterns observed
- **Resolution and Prevention**: Root cause, solution, prevention measures
- **TODO List Updates**: What tasks should be added/modified based on findings
- **Plan Updates**: What plans need revision based on this issue

**User Requirements Documentation**
- **User reasoning**: Document why requirements exist and their business context
- **Observable constraints**: Technical limitations, performance requirements, compatibility needs
- **Success criteria**: Clear definition of what constitutes successful implementation
- **Acceptance conditions**: Specific conditions that must be met for approval

#### Note Management Best Practices

**File Naming Convention**
```bash
# Consistent naming for easy discovery
notes/todo_YYYYMMDD_descriptive_name.md
notes/worklog_YYYYMMDD_activity_type.md
notes/debug_YYYYMMDD_component_issue.md
notes/rca_YYYYMMDD_incident_description.md
notes/research_YYYYMMDD_topic_area.md
notes/learning_YYYYMMDD_tool_library.md
notes/brainstorm_YYYYMMDD_topic_name.md
notes/plan_YYYYMMDD_initiative_name.md
notes/proposal_YYYYMMDD_solution_name.md
```

**Cross-Reference System**
- **Link related notes** using relative paths: `../notes/debug_20241227_api_timeout.md`
- **Reference requirements** from user requests in technical notes
- **Update todo lists** when new information affects priorities
- **Version progression** by creating new notes rather than overwriting old ones

**Maintenance and Cleanup**
- **Regular review**: Weekly review of notes for consolidation opportunities
- **Archive old notes**: Move completed items to `notes/archive/` after 90 days
- **Update modification dates**: Always update when making changes
- **Search and discovery**: Use consistent keywords and categories for easy finding
- **Problem pattern tracking**: If certain problem persists across multiple points in codebase, create pattern note and plan clearer solutions

### Legacy Code Preservation Rules
- **🚫 DO NOT MODIFY** files directly under `src/` that start with "step" + numbers
- **🚫 DO NOT DELETE** legacy implementations - they serve as reference and documentation
- **✅ CREATE NEW IMPLEMENTATIONS** in appropriate subdirectories (`src/steps/`, `src/components/`)
- **✅ REFACTOR LOGIC** into modular components while preserving legacy as documentation
- **✅ USE LEGACY CODE** only for understanding requirements and behavior analysis

## 🚀 Development Workflow

### Complete BDD Development Process

#### Phase 1: Behavior Analysis & Use Case Definition
```bash
# 1. Analyze legacy code and define expected behavior
# Read existing code to understand current functionality
# Document in notes/ with timestamp: notes/behavior_analysis_$(date +%Y%m%d).md

# 2. Create feature files using Given-When-Then format
# Place in tests/features/ following naming: step-N-feature-name.feature
# Example: tests/features/step-2-extract-coordinates.feature

# 3. Write declarative scenarios from business perspective
# Use domain terminology stakeholders understand
# Include both happy path and failure scenarios
```

#### Phase 2: Test Scaffolding (Pre-Implementation)
```bash
# 4. Create scaffold test files based on feature files
# Generate: tests/test_stepN_scaffold.py
# All tests should fail with "SCAFFOLDING PHASE" messages

# 5. Verify scaffold structure matches feature files exactly
uv run pytest tests/test_stepN_scaffold.py -v
# Expected: All tests fail with clear scaffolding messages

# 6. Ensure no real implementation exists yet
grep -c "pytest.fail" tests/test_stepN_scaffold.py  # Should match scenario count
```

#### Phase 3: Code Refactoring (CUPID Principles)
```bash
# 7. Implement refactored Step class following 4-phase pattern
# Create in src/steps/ using domain-based naming
# Apply dependency injection and repository pattern
# Use 'import fireducks.pandas as pd' for all data operations

# 8. Follow CUPID principles:
# - Composable: Modular components for reusability
# - Unix Philosophy: Single responsibility per class
# - Predictable: Consistent behavior and contracts
# - Idiomatic: Python conventions and best practices
# - Domain-based: Business language in structure and naming

# 9. Add comprehensive type hints and documentation
# Ensure all dependencies are injected via constructor
# Implement centralized logging with PipelineLogger

# 10. Verify 500 LOC compliance during refactoring
find src/ tests/ -name "*.py" -exec wc -l {} + | awk '$1 > 500 {print "MODULARIZE: " $2 ": " $1 " lines"}'
# If any files exceed 500 LOC, apply CUPID-based modularization immediately

# 11. Check for proper fireducks pandas usage
grep -r "import fireducks.pandas as pd" src/ | wc -l
# Ensure all data manipulation uses accelerated pandas
```

#### Phase 4: Test Implementation & Validation
```bash
# 10. Convert scaffold to functional tests
cp tests/test_stepN_scaffold.py tests/test_stepN.py

# 11. Replace pytest.fail() calls with real implementations
# Add real mock objects and test data
# Implement actual step execution and assertions

# 12. Validate implementation matches feature specifications
uv run pytest tests/test_stepN.py -v
# Expected: All tests pass with real implementation

# 13. Remove scaffold file after successful implementation
rm tests/test_stepN_scaffold.py

# 14. Final verification of 500 LOC compliance for all files
find src/ tests/ -name "*.py" -exec wc -l {} + | awk '$1 > 500 {exit 1}' && echo "✅ All files comply with 500 LOC limit"
```

### Data Investigation (Integrated with BDD)
```bash
# Examine CSV files to understand data issues (Phase 1 context)
xan view data/api_data/store_config_202508A.csv
xan info data/api_data/store_sales_202508A.csv

# Check for data quality issues (inform scenario requirements)
xan schema data/api_data/complete_category_sales_202508A.csv
xan stats data/api_data/complete_spu_sales_202508A.csv

# Use data insights to inform Given-When-Then scenarios
# Document data patterns in feature files and test expectations
```

### Documentation (Aligned with BDD)
```bash
# Technical progress and experiments -> notes/ (comprehensive standards)
echo "# $(date +%Y-%m-%d) - BDD Implementation Progress" >> notes/bdd_progress_$(date +%Y%m%d).md
echo "# Last modified: $(date +%Y-%m-%d %H:%M:%S)" >> notes/bdd_progress_$(date +%Y%m%d).md

# Feature file rationale and business requirements (with detailed context)
echo "# $(date +%Y-%m-%d) - Behavioral Analysis - Step N" >> notes/stepN_behavior_analysis_$(date +%Y%m%d).md
echo "# Last modified: $(date +%Y-%m-%d %H:%M:%S)" >> notes/stepN_behavior_analysis_$(date +%Y%m%d).md

# Debug sessions and RCA (when issues arise)
echo "# $(date +%Y-%m-%d) - Debug Session - Component Issue" >> notes/debug_$(date +%Y%m%d)_component_issue.md
echo "# Last modified: $(date +%Y-%m-%d %H:%M:%S)" >> notes/debug_$(date +%Y%m%d)_component_issue.md

# Research and tool learning notes (when implementing new solutions)
echo "# $(date +%Y-%m-%d) - Research - Solution Approach" >> notes/research_$(date +%Y%m%d)_solution_approach.md
echo "# Last modified: $(date +%Y-%m-%d %H:%M:%S)" >> notes/research_$(date +%Y%m%d)_solution_approach.md

# Human procedures and guides -> docs/ (updated for BDD workflow)
# Update docs/ with comprehensive BDD process documentation and standards
```

### Testing Strategy (BDD-Driven)
- **Phase 1**: Define behavior with feature files before implementation
- **Phase 2**: Create failing scaffolds to ensure test structure is correct
- **Phase 3**: Implement code that satisfies the predefined test specifications
- **Phase 4**: Convert scaffolds to functional tests validating implementation
- **Binary Outcomes**: All tests must clearly PASS or FAIL - no conditional results
- **Real Data Priority**: Use actual data subsets for validation, minimize synthetic data
- **Living Documentation**: Feature files and tests serve as both specification and documentation

## 🔍 Debugging and Investigation (BDD-Aligned)

### Data Issues (Phase 1 Context)
1. **Use `xan` for visual inspection** to inform Given-When-Then scenarios
2. **Check data schemas** and distributions to define validation rules
3. **Validate period consistency** across files to ensure test data integrity
4. **Document findings** in `notes/` with timestamps and BDD implications
5. **Update feature files** when data insights reveal new validation requirements

### Code Issues (BDD-Driven Debugging)
1. **Run targeted tests** to isolate problems (start with Phase 4 tests)
2. **Check code size compliance** - ensure no files exceed 500 LOC during debugging
3. **Verify modular organization** - ensure no legacy files modified and proper folder structure
4. **Check fireducks pandas usage** - ensure all data operations use accelerated pandas
5. **Use real data** for debugging, ensuring feature files reflect actual data patterns
6. **Document comprehensive debug sessions** in `notes/debug_YYYYMMDD_issue.md` with full traceback
7. **Conduct systematic RCA** in `notes/rca_YYYYMMDD_incident.md` with 5 possible root causes
8. **Document user requirements context** - understand why issues occur and their business impact
9. **Research best practices** and document findings in `notes/research_YYYYMMDD_solution.md`
10. **Check feature file alignment** - ensure failing tests match business requirements
11. **Update implementation** to match feature specifications, not vice versa
12. **Verify binary outcomes** - tests must clearly PASS or FAIL
13. **Use `eza --tree --level 2`** for examining file structures during debugging
14. **Use `skim`** for fuzzy finding error patterns or specific issues in logs
15. **Use `procs --pager disable`** to monitor background test processes

**Debugging Documentation Standards:**
```bash
# Create comprehensive debug notes with full context
echo "# $(date +%Y-%m-%d) - Debug Session - Component Issue" >> notes/debug_$(date +%Y%m%d)_component_issue.md
echo "# Last modified: $(date +%Y-%m-%d %H:%M:%S)" >> notes/debug_$(date +%Y%m%d)_component_issue.md

# Document RCA with systematic analysis
echo "# $(date +%Y-%m-%d) - RCA - Incident Analysis" >> notes/rca_$(date +%Y%m%d)_incident_analysis.md
echo "# Last modified: $(date +%Y-%m-%d %H:%M:%S)" >> notes/rca_$(date +%Y%m%d)_incident_analysis.md

# Research solutions and document findings
echo "# $(date +%Y-%m-%d) - Research - Solution Feasibility" >> notes/research_$(date +%Y%m%d)_solution_feasibility.md
echo "# Last modified: $(date +%Y-%m-%d %H:%M:%S)" >> notes/research_$(date +%Y%m%d)_solution_feasibility.md
```

**Code Size Check During Debugging:**
```bash
# Always verify code size compliance when debugging
find src/ tests/ -name "*.py" -exec wc -l {} + | awk '$1 > 500 {print "SIZE VIOLATION: " $2 ": " $1 " lines"}'

# Check for modular organization violations
find src/ -maxdepth 1 -name "step[0-9]*.py" | wc -l  # Should be 0 (no legacy modifications)

# Verify fireducks pandas usage in all data operations
grep -r "import fireducks.pandas as pd" src/ | wc -l

# If violations found, modularize immediately using CUPID principles
# before continuing with debugging
```

### BDD-Specific Debugging Commands
```bash
# Check if implementation matches feature specifications
uv run pytest tests/test_stepN.py::test_scenario_name -v -s

# Verify all scenarios in feature file are implemented
grep -c "Scenario:" tests/features/step-N-*.feature
grep -c "@scenario" tests/test_stepN.py

# Check for test suppression or conditional logic (should be 0)
grep -c "pytest.skip\|try:.*except.*pass\|return.*fail" tests/test_stepN.py

# Validate step imports are working
grep -n "from src.steps" tests/test_stepN.py

# Check for real mock usage vs placeholder code
grep -c "mocker.MagicMock" tests/test_stepN.py
```

## 🔬 Root Cause Analysis (RCA) Within TDD/BDD Framework

### RCA Principles
Root Cause Analysis is a **systematic investigation technique** that identifies the fundamental cause of problems rather than treating symptoms. In a TDD/BDD context, RCA ensures bugs and failures are understood deeply before fixes are applied.

#### Core RCA Rules
- **Define the Problem Clearly**: Accurately describe the issue, including what happened, when it happened, where it occurred, and the expected vs. actual behavior
- **Gather Comprehensive Data**: Collect all relevant information (logs, error messages, system state, data snapshots) before analysis begins
- **5 Possible Root Causes**: Always enumerate and evaluate exactly 5 hypotheses systematically
- **Evidence-Based Analysis**: Support or refute each hypothesis with concrete evidence, not speculation
- **Eliminate Non-Causes**: Document why each non-cause was eliminated
- **Identify Primary Cause**: Clear identification of the actual root cause after systematic elimination
- **Prevention Strategy**: Define measures to prevent recurrence
- **Document Thoroughly**: Comprehensive documentation in `notes/rca_YYYYMMDD_incident.md` for future reference

### RCA Process Within BDD

#### Step 1: Problem Definition (Comprehensive Context)
```bash
# Document immediately when issue discovered
echo "# $(date +%Y-%m-%d %H:%M:%S) - RCA: [Problem Title]" >> notes/rca_$(date +%Y%m%d)_incident.md
echo "## Issue Description" >> notes/rca_$(date +%Y%m%d)_incident.md
echo "- What: [Specific observable behavior/failure]" >> notes/rca_$(date +%Y%m%d)_incident.md
echo "- When: [Time/trigger of occurrence]" >> notes/rca_$(date +%Y%m%d)_incident.md
echo "- Where: [Component/module/test]" >> notes/rca_$(date +%Y%m%d)_incident.md
echo "- Expected: [What should have happened]" >> notes/rca_$(date +%Y%m%d)_incident.md
echo "- Actual: [What actually happened]" >> notes/rca_$(date +%Y%m%d)_incident.md
```

#### Step 2: Data Gathering & Evidence Collection
1. **Collect Error Logs**: Full stack traces, error messages, and surrounding context (first/last 50-150 chars if too long)
2. **System State**: Python version, package versions, data state at time of failure
3. **Reproduction Steps**: Exact sequence to reproduce the issue with specific parameters
4. **Related Artifacts**: Feature files, test code, implementation code involved
5. **Timeline**: When did this first occur? Does it happen consistently or intermittently?

#### Step 3: Generate 5 Possible Root Causes
Always enumerate exactly 5 hypotheses:
```markdown
## 5 Possible Root Causes

### Hypothesis 1: [Specific technical cause]
- Mechanism: [How this would cause the observed behavior]
- Evidence supporting: [Specific evidence for this hypothesis]
- Evidence against: [Specific evidence against this hypothesis]
- Status: ELIMINATED / INVESTIGATING / CONFIRMED

### Hypothesis 2: [Specific technical cause]
...

### Hypothesis 3: [Specific technical cause]
...

### Hypothesis 4: [Specific technical cause]
...

### Hypothesis 5: [Specific technical cause]
...
```

#### Step 4: Systematic Evaluation
- **Run targeted tests** to test each hypothesis
- **Use `skim` and `ripgrep`** to find error patterns in logs
- **Examine related code** for each hypothesis
- **Document findings** for each hypothesis with specific evidence
- **Update status** as ELIMINATED, INVESTIGATING, or CONFIRMED

#### Step 5: Eliminate Non-Causes
```markdown
## Non-Cause Elimination

### Hypothesis 2 - ELIMINATED
Reason: [Specific evidence that rules this out]
Timeline: [When was this determined]

### Hypothesis 4 - ELIMINATED
Reason: [Specific evidence that rules this out]
Timeline: [When was this determined]
```

#### Step 6: Confirm Primary Root Cause
```markdown
## Root Cause Confirmation

**Primary Root Cause**: [Clear identification of actual cause]

**Evidence**:
- [Specific evidence piece 1]
- [Specific evidence piece 2]
- [Specific evidence piece 3]

**Why This Explains All Observations**: [Narrative connecting root cause to observed behavior]

**Prevention Strategy**:
- [Preventive measure 1]
- [Preventive measure 2]
- [Update to test/feature file to catch this]
```

#### Step 7: Implement Fix & Update Tests
1. **Fix Implementation**: Address the root cause
2. **Update Feature Files**: Add scenario to prevent recurrence
3. **Add Test Coverage**: Create test scenario that would catch this bug
4. **Verify Fix**: Confirm all related tests now pass
5. **Document**: Update notes with resolution and lessons learned

### RCA Documentation Template
```markdown
# $(date +%Y-%m-%d) - RCA: [Incident Title]
# Last modified: $(date +%Y-%m-%d %H:%M:%S)

## Issue Description
- What: 
- When: 
- Where: 
- Expected vs Actual:

## Reproduction Steps
1. [Step 1]
2. [Step 2]
...

## Data Gathered
- Error logs: [Location/summary]
- System state: [Python version, packages]
- Related code: [Files involved]

## 5 Possible Root Causes
[See above template]

## Non-Cause Elimination
[See above template]

## Root Cause Confirmation
[See above template]

## Implementation
- Fix applied: [What was changed]
- Tests updated: [Which tests/features]
- Verification: [Results of verification]

## Lessons Learned
- [Learning 1]
- [Learning 2]
```

---

## 📝 Incremental Progress Logging (Comprehensive & Non-Duplicating)

### Progress Logging Principles
Incremental Progress Logging tracks development work systematically **without duplicating effort or information across documents**. The key is **modularizing documentation by responsibility** rather than creating separate versions of the same information.

#### Core Rules
- **Separate by Responsibility**: Different documents serve different purposes (worklog, todo, brainstorm, debug)
- **No Information Duplication**: Reference existing notes from other documents rather than repeating content
- **Sub-Task Modularization**: Break complex work into sub-documents for focused documentation
- **Progressive Updates**: Add new information incrementally rather than rewriting entire sections
- **Cross-References**: Link related notes using relative paths for navigation
- **Single Source of Truth**: Each piece of information exists in exactly one primary location

### Progress Logging Structure

#### 1. Work Logs (Progressive Activity Tracking)
**Purpose**: Chronological record of what was done, how long it took, and what's next
**File**: `notes/worklog_YYYYMMDD_activity.md`

```markdown
# $(date +%Y-%m-%d) - Work Log: [Activity Type]
# Last modified: $(date +%Y-%m-%d %H:%M:%S)

## Session Start
- Start time: $(date +%H:%M:%S)
- Objective: [Clear goal for this session]
- Context: [What was completed before, what's blocking]

## Progress Log (Add incrementally)
- **10:30** - Started Phase 1 analysis for Step 2
  - Reading legacy_step2_extract_coordinates.py
  - Documenting current behavior

- **11:00** - Completed Phase 1 analysis
  - Duration: 30 minutes
  - Findings: [Key insights]
  - Next: Moving to feature file creation

- **11:45** - Feature file created
  - Scenarios: [Count and list]
  - Time spent: 45 minutes

## Session End
- End time: $(date +%H:%M:%S)
- Total duration: [X hours Y minutes]
- Completed tasks: [List of what was accomplished]
- Blockers encountered: [Any issues]
- Next session: [What to do next]
```

#### 2. TODO Lists (Comprehensive & Updated Incrementally)
**Purpose**: Complete breakdown of all work needed, updated as tasks are discovered
**File**: `notes/todo_YYYYMMDD_description.md`

```markdown
# $(date +%Y-%m-%d) - TODO List: [Initiative Name]
# Last modified: $(date +%Y-%m-%d %H:%M:%S)

## Overview
- Objective: [What needs to be completed]
- Context: [Why this is important]
- Scope: [What's included/excluded]
- Estimated duration: [Overall timeline]

## Tasks (Update incrementally - only mark done when verified)

### Phase 1: Analysis & Planning
- [ ] Read legacy code
- [ ] Create feature file
- [ ] Document findings

### Phase 2: Implementation
- [ ] Write scaffolding tests
- [ ] Implement core logic
- [ ] Add validation

### Phase 3: Testing & Verification
- [ ] Convert scaffolds to functional tests
- [ ] Run full test suite
- [ ] Verify 500 LOC compliance

## Status Tracking
- Total: [X] tasks
- Complete: [Y] tasks
- In Progress: [Z] tasks
- Blocked: [W] tasks

## Blocked Tasks Reference
- Task name - See: ../notes/debug_YYYYMMDD_issue.md
- Task name - See: ../notes/rca_YYYYMMDD_incident.md

## Last Update
- When: $(date +%Y-%m-%d %H:%M:%S)
- By whom: [Your name/AI]
- Next planned update: [When to review]
```

#### 3. Detailed Phase/Component Notes (Modular Sub-Documentation)
**Purpose**: In-depth analysis for specific phases or components
**Files**: `notes/step2_behavior_analysis_YYYYMMDD.md`, `notes/component_design_YYYYMMDD.md`

```markdown
# $(date +%Y-%m-%d) - Behavior Analysis: Step 2 Extract Coordinates
# Last modified: $(date +%Y-%m-%d %H:%M:%S)

## Legacy Code Analysis
[Specific findings about current implementation]

## Setup Phase
- Input: [Where data comes from]
- Behavior: [What happens]
- Output: [What's prepared]

## Apply Phase
[Detailed analysis]

## Validate Phase
[Detailed analysis]

## Persist Phase
[Detailed analysis]

## Related Documentation
- TODO: See `../notes/todo_$(date +%Y%m%d)_step2.md`
- Work log: See `../notes/worklog_$(date +%Y%m%d)_step2.md`
```

#### 4. Blocking Issues & Investigations (Reference, Don't Duplicate)
**Purpose**: Detailed investigation of specific problems
**Files**: `notes/debug_YYYYMMDD_issue.md`, `notes/rca_YYYYMMDD_incident.md`

When a blocker is discovered:
1. **Create issue-specific note** with full investigation
2. **Link from TODO list**: Add reference line: "Blocked by: See ../notes/debug_YYYYMMDD_issue.md"
3. **Update TODO**: Mark task as "BLOCKED - [issue ref]" instead of repeating investigation
4. **Link from worklog**: Record when blocker was discovered and reference

**DO NOT** duplicate issue details across multiple notes. Instead:
```markdown
# In TODO list
- [ ] Add setup() method - BLOCKED (See ../notes/debug_20251028_repository_import.md)

# In worklog
- **14:00** - Blocked on setup() implementation
  - Issue: Repository import failing
  - Investigation: See ../notes/debug_20251028_repository_import.md
  - Next: Resume after resolution
```

### Progress Logging Best Practices

#### ✅ DO: Modularize by Responsibility
```markdown
# Worklog references detailed analysis
- **11:00** - Completed Phase 1 analysis
  - Detailed findings: See ../notes/step2_behavior_analysis_20251028.md

# Detailed analysis file has its own focus
# (Not repeating what's in worklog)
```

#### ❌ DON'T: Duplicate Information Across Documents
```markdown
# DON'T do this in multiple places:
- Phase 1 analysis details in BOTH worklog AND separate analysis file
- Investigation details in BOTH debug file AND todo list
```

#### ✅ DO: Use Cross-References
```markdown
# Link related notes for navigation
See: ../notes/rca_20251028_import_error.md for root cause analysis
See: ../notes/todo_20251028_step2_tasks.md for task tracking
```

#### ✅ DO: Update Incrementally
```markdown
## Progress Log (Add incrementally)
- **10:30** - Started analysis
- **11:00** - Completed step 1 (duration: 30 min)
- **11:15** - Started step 2 (in progress...)
```

#### ❌ DON'T: Rewrite Entire Sections
```markdown
# DON'T rewrite the entire log with corrected information
# DO: Add correction note with timestamp and link to related docs
```

---

## ✅ Comprehensive TODO List Management

### TODO List Principles
A comprehensive TODO list serves as the **single source of truth** for all work needed. It must be **maintained incrementally** and **organized hierarchically** for clarity.

#### Core Rules
- **Comprehensive Scope**: Include all work items, not just current tasks
- **Hierarchical Organization**: Group related tasks into phases/sections
- **Incremental Updates**: Add new tasks as they're discovered, mark done when verified
- **Binary States Only**: Tasks are either [ ] (not done) or [x] (verified complete)
- **No Partial Completion**: Don't mark tasks done until fully verified and tested
- **Reference External Details**: Link to detailed notes rather than duplicating information
- **Status Summary**: Maintain count of total/completed/blocked tasks

### TODO List Structure

#### Session-Based Organization
```markdown
# $(date +%Y-%m-%d) - TODO List: [Component/Step Name]
# Last modified: $(date +%Y-%m-%d %H:%M:%S)

## Overview & Context
- Component: [Name]
- Objective: [Clear goal]
- Related requirements: [Links to user requirements or feature files]
- Estimated scope: [Time/effort estimate]

## Tasks by Phase

### Phase 1: Analysis & Planning
- [ ] Read legacy code
- [ ] Create feature file
- [ ] Document findings

### Phase 2: Implementation
- [ ] Write scaffolding tests
- [ ] Implement core logic
- [ ] Add validation

### Phase 3: Testing & Verification
- [ ] Convert scaffolds to functional tests
- [ ] Run full test suite
- [ ] Verify 500 LOC compliance

## Status Tracking
- Total: [X] tasks
- Complete: [Y] tasks
- In Progress: [Z] tasks
- Blocked: [W] tasks

## Blocked Tasks Reference
- Task name - See: ../notes/debug_YYYYMMDD_issue.md
- Task name - See: ../notes/rca_YYYYMMDD_incident.md

## Last Update
- When: $(date +%Y-%m-%d %H:%M:%S)
- By whom: [Your name/AI]
- Next planned update: [When to review]
```

### Incremental Checklist Updates
```bash
# When starting a task
echo "- [x] Task name - completed $(date +%Y-%m-%d)" >> notes/todo_YYYYMMDD.md

# When discovering new tasks
echo "- [ ] New task discovered during implementation" >> notes/todo_YYYYMMDD.md

# When encountering blocker
echo "- [ ] Task name - BLOCKED (See ../notes/debug_YYYYMMDD_issue.md)" >> notes/todo_YYYYMMDD.md

# When unblocking
sed -i 's/BLOCKED.*/NOW UNBLOCKED - resuming/' notes/todo_YYYYMMDD.md
```

### TODO List Maintenance Ritual
**Every session**: 
1. Update last modified timestamp
2. Add any new tasks discovered
3. Mark completed tasks [x]
4. Update status summary count
5. Review blocked tasks and RCA status

---

## 🎓 Professional Development: Liberally Document Procedures & Best Practices

### Documentation Principles
Professional development requires **systematic documentation of procedures and best practices** discovered during implementation. This creates a **knowledge repository** for future reference and team development.

#### Core Rules
- **Document Everything Discovered**: New procedures, workarounds, best practices
- **Use Plain Language**: Write for developers who will use this later
- **Include Examples**: Practical examples improve understanding
- **Link to Theory**: Reference documentation, standards, or research
- **Version by Date**: Create new notes rather than overwriting, preserving historical context
- **Tag for Discovery**: Use consistent keywords for searching
- **Review Regularly**: Weekly review consolidates learning into practices

### Procedure Documentation Categories

#### 1. Tool & Command Learning
**File**: `notes/learning_tool_YYYYMMDD.md`
**When**: When mastering a new terminal command, package, or tool

```markdown
# $(date +%Y-%m-%d) - Learning: [Tool Name]
# Last modified: $(date +%Y-%m-%d %H:%M:%S)

## Tool Overview
- Purpose: [What does it do]
- Installation: [How to install]
- Version: [Current stable version]
- Website/Docs: [Link to official documentation]

## Key Features
1. Feature with example:
   ```bash
   command_example --flag value
   # Output: [what happens]
   ```

2. Feature with example:
   ```bash
   command_example --other-flag
   # Output: [what happens]
   ```

## Common Use Cases
- Use case 1: [Example command and result]
- Use case 2: [Example command and result]
- Use case 3: [Example command and result]

## Comparison with Alternatives
| Tool | Pros | Cons | When to use |
|------|------|------|------------|
| This tool | [Pro 1] | [Con 1] | [Situation] |
| Alternative | [Pro] | [Con] | [Situation] |

## Troubleshooting & Tips
- Common issue 1: [Solution]
- Performance tip 1: [Optimization]
- Debugging tip: [How to debug issues]

## Usage Examples
### Basic Usage
[Example with explanation]

### Advanced Usage
[Example with explanation]

## Related Documentation
- Official docs: [URL]
- Similar tools: See ../notes/learning_tool_[other].md
- Integration with project: [How this applies to project]
```

#### 2. Code Pattern & Procedure Documentation
**File**: `notes/procedure_YYYYMMDD_description.md`
**When**: When establishing a new development procedure or code pattern

```markdown
# $(date +%Y-%m-%d) - Procedure: [Procedure Name]
# Last modified: $(date +%Y-%m-%d %H:%M:%S)

## Purpose
[Why this procedure matters]

## When to Use
[Specific situations where this applies]

## Step-by-Step Procedure
1. [Step 1 with context]
   ```python
   # Code example for step 1
   ```

2. [Step 2 with context]
   ```python
   # Code example for step 2
   ```

3. [Step 3 with context]

## Best Practices
- [Best practice 1 with reasoning]
- [Best practice 2 with reasoning]
- [Best practice 3 with reasoning]

## Common Mistakes to Avoid
- Mistake 1: [Why this is wrong, what to do instead]
- Mistake 2: [Why this is wrong, what to do instead]

## Performance Considerations
- [Performance tip 1]
- [Performance optimization]

## Debugging This Procedure
- Issue 1: [Solution]
- Issue 2: [Solution]

## Related Procedures
See: ../notes/procedure_YYYYMMDD_related.md
```

#### 3. Best Practice Research & Rationale
**File**: `notes/research_YYYYMMDD_topic.md`
**When**: After researching industry best practices or architectural patterns

```markdown
# $(date +%Y-%m-%d) - Research: [Topic/Pattern Name]
# Last modified: $(date +%Y-%m-%d %H:%M:%S)

## Research Objective
[What question were we trying to answer]

## Sources Consulted
- Source 1: [URL/Reference with key points]
- Source 2: [URL/Reference with key points]
- Source 3: [URL/Reference with key points]

## Key Findings
1. [Finding 1 with evidence]
2. [Finding 2 with evidence]
3. [Finding 3 with evidence]

## Approaches Compared
### Approach A: [Name]
- Pros: [Pro 1], [Pro 2]
- Cons: [Con 1], [Con 2]
- Best for: [Situations]

### Approach B: [Name]
- Pros: [Pro 1], [Pro 2]
- Cons: [Con 1], [Con 2]
- Best for: [Situations]

### Approach C: [Name]
- Pros: [Pro 1], [Pro 2]
- Cons: [Con 1], [Con 2]
- Best for: [Situations]

## Recommendation
- **Chosen approach**: [Why]
- **Rationale**: [Cost-benefit analysis, trade-offs]
- **Implementation plan**: [How to implement]
- **Success criteria**: [How to measure success]

## Implementation Status
- Started: [Date]
- In progress: [What's being done]
- Completed: [What's done]

## Lessons Learned
- [Learning 1]
- [Learning 2]

## Future Improvements
- [Improvement 1]
- [Improvement 2]
```

### Professional Development Review Cycle
```bash
# Weekly professional development review
echo "# $(date +%Y-%m-%d) - Weekly Professional Review" >> notes/weekly_review_$(date +%Y%m%d).md

# 1. List all learning notes from past week
ls -lt notes/learning_* | head -5

# 2. List all procedure documentation created
ls -lt notes/procedure_* | head -5

# 3. Review research conducted
ls -lt notes/research_* | head -5

# 4. Consolidate insights into patterns
# (Look for recurring themes or best practices)

# 5. Update related documentation
# (Link new learnings to existing docs)

# 6. Share knowledge
# (Add to team wiki or shared knowledge base)
```

---

## 🧠 Critical Thinking: Feature Design & Test Functionality

### Critical Thinking Principles
Critical thinking in software development ensures **features are necessary, tests are comprehensive, and edge cases are handled**. It requires **questioning assumptions** and **anticipating failure modes** before implementation.

#### Core Rules
- **Question Assumptions**: Challenge why each feature is needed before building
- **Define Clear Success Criteria**: Know exactly what "working" means
- **Anticipate Edge Cases**: Consider boundary conditions and error scenarios
- **Test Comprehensively**: Write scenarios for happy path, error cases, and edge conditions
- **Validate Before Coding**: Ensure requirements are clear before implementation
- **Document Rationale**: Explain the "why" behind features and tests

### Critical Thinking for Feature Design

#### 1. Requirements Analysis (Chesterton's Fence)
Before implementing ANY feature, apply **Chesterton's Fence principle**: "Do not remove a fence until you know why it was put up in the first place."

```markdown
# Questions to Ask About Every Feature

## Purpose & Context
- [ ] Why does this feature exist?
- [ ] What business need does it address?
- [ ] Who requested this feature?
- [ ] What problem does it solve?

## Scope & Boundaries
- [ ] What exactly should this feature do?
- [ ] What should it NOT do?
- [ ] What are the exact success criteria?
- [ ] Are there any constraints?

## Dependencies & Impact
- [ ] What does this feature depend on?
- [ ] What other components depend on this?
- [ ] What happens if this feature fails?
- [ ] Can it be done incrementally?

## Alternatives & Trade-offs
- [ ] Are there alternative implementations?
- [ ] What are the trade-offs?
- [ ] Why is the chosen approach better?
- [ ] What would be the cost of not building this?

## Risk Analysis
- [ ] What could go wrong?
- [ ] How likely is each risk?
- [ ] What's the impact if it fails?
- [ ] How can we mitigate risks?
```

#### 2. Feature Specification (Clear & Measurable)
```markdown
# Feature Specification Template

## Feature Name
[Descriptive name]

## Business Objective
[Why this matters to the business]

## User Story
As a [user type], I want to [action], so that [benefit]

## Acceptance Criteria
- [ ] Criterion 1: [Specific, measurable outcome]
- [ ] Criterion 2: [Specific, measurable outcome]
- [ ] Criterion 3: [Specific, measurable outcome]

## Edge Cases & Error Scenarios
- [ ] Edge case 1: [Scenario and expected behavior]
- [ ] Edge case 2: [Scenario and expected behavior]
- [ ] Error scenario 1: [How should system handle error]
- [ ] Error scenario 2: [How should system handle error]

## Performance Requirements
- [ ] Speed: [Must process X records in Y seconds]
- [ ] Memory: [Must handle Z MB dataset]
- [ ] Concurrency: [Must handle N simultaneous users]

## Testing Strategy
- [ ] Happy path test scenarios
- [ ] Error case test scenarios
- [ ] Edge case test scenarios
- [ ] Performance tests
- [ ] Integration tests

## Success Metrics
- Metric 1: [How to measure]
- Metric 2: [How to measure]
- Metric 3: [How to measure]
```

### Critical Thinking for Test Functionality

#### 1. Comprehensive Test Planning
```markdown
# Critical Questions for Every Test

## Test Purpose
- [ ] What exactly is this test checking?
- [ ] Why is this scenario important?
- [ ] What would break if we didn't test this?
- [ ] Does this test align with feature acceptance criteria?

## Scenario Coverage
- [ ] Happy path: [Normal operation with valid data]
- [ ] Error cases: [What happens with invalid data]
- [ ] Edge cases: [Boundary conditions]
- [ ] Stress scenarios: [Large datasets, high concurrency]

## Test Data Strategy
- [ ] Using real data or synthetic?
- [ ] Is data representative of production?
- [ ] Do we have edge case data?
- [ ] Are we testing with actual constraints?

## Test Isolation
- [ ] Is this test independent of others?
- [ ] Does it have no hidden dependencies?
- [ ] Can it run alone successfully?
- [ ] Does it clean up after itself?

## Assertion Strategy
- [ ] Are assertions specific and meaningful?
- [ ] Do they check the right outcomes?
- [ ] Could assertions be more comprehensive?
- [ ] Do they provide good error messages?

## Failure Analysis
- [ ] What does test failure mean?
- [ ] Is the error message clear?
- [ ] Can a developer quickly debug?
- [ ] Does it point to the root issue?
```

#### 2. Test Scenarios: Happy Path, Errors, Edge Cases
```gherkin
# Feature: Step 2 - Extract Coordinates
# Critical thinking applied to comprehensive test coverage

Scenario: Happy Path - Extract valid coordinates from data
  Given raw store data with complete coordinates
  When the coordinate extraction step is executed
  Then all stores should have valid (latitude, longitude) pairs
  And no data should be lost in extraction

Scenario: Error Case - Missing latitude field
  Given raw data with missing latitude field
  When the coordinate extraction step is executed
  Then the step should fail with DataValidationError
  And the error should indicate which field is missing
  And the error log should include the first problematic record

Scenario: Error Case - Invalid coordinate values
  Given raw data with non-numeric coordinate values
  When the coordinate extraction step is executed
  Then the step should fail with DataValidationError
  And the error should indicate which values are invalid
  And coordinates outside valid ranges should be rejected

Scenario: Edge Case - Zero coordinates (equator/prime meridian)
  Given data with latitude=0 and longitude=0
  When the coordinate extraction step is executed
  Then coordinates should be accepted as valid
  And zero coordinates should not be treated as missing data

Scenario: Edge Case - Extreme coordinates (poles)
  Given data with latitude=90 and latitude=-90
  When the coordinate extraction step is executed
  Then coordinates should be accepted as valid
  And pole coordinates should be treated normally

Scenario: Edge Case - Large dataset (1M+ records)
  Given a large CSV with 1,000,000 store records
  When the coordinate extraction step is executed
  Then extraction should complete in < 30 seconds
  And all coordinates should be correctly extracted
  And no memory issues should occur

Scenario: Edge Case - Empty dataset
  Given an empty CSV with only headers
  When the coordinate extraction step is executed
  Then the step should complete without error
  And the output should be empty
  And no records should be lost
```

#### 3. Test Code: Critical Assertions
```python
# Critical thinking in test assertions

def test_coordinate_extraction_happy_path():
    """Extract coordinates: verify complete extraction of valid data."""
    # Setup with REAL data (not synthetic)
    fixture.given_store_data_with_complete_coordinates()
    
    # Execute
    fixture.when_extract_coordinates()
    
    # Assert with critical thinking
    assert fixture.result is not None, "Result should not be None"
    assert len(fixture.result) == fixture.expected_count, \
        f"Should extract all {fixture.expected_count} records, got {len(fixture.result)}"
    
    # Critical: Check each coordinate is valid
    for idx, record in fixture.result.iterrows():
        assert -90 <= record['latitude'] <= 90, \
            f"Row {idx}: Latitude {record['latitude']} out of range"
        assert -180 <= record['longitude'] <= 180, \
            f"Row {idx}: Longitude {record['longitude']} out of range"
        assert not pd.isna(record['latitude']), \
            f"Row {idx}: Latitude should not be NaN"
        assert not pd.isna(record['longitude']), \
            f"Row {idx}: Longitude should not be NaN"
    
    # Critical: Verify no data loss
    original_count = fixture.source_data.shape[0]
    extracted_count = fixture.result.shape[0]
    assert extracted_count == original_count, \
        f"Data loss: {original_count} inputs, {extracted_count} outputs"
```

#### 4. Binary Test Outcomes (PASS/FAIL Only)
```python
# ✅ GOOD: Clear binary outcome
def test_coordinate_validation():
    """Test validates coordinates correctly."""
    try:
        fixture.when_extract_coordinates()
        assert fixture.result_is_valid()  # Test either passes or fails
    except Exception as e:
        pytest.fail(f"Coordinate extraction failed: {str(e)}")

# ❌ BAD: Conditional or suppressed outcomes
def test_coordinate_validation_bad():
    """Test with conditional/suppressed outcomes."""
    try:
        fixture.when_extract_coordinates()
        # Bad: Test might pass even if something is wrong
        if fixture.result_is_valid():
            assert True  # Pointless
        else:
            pass  # Silent failure
    except Exception:
        pass  # Suppressed error - test still passes!
```

---

## 📋 Best Practices

### Code Quality (CUPID Compliance & Size Limits)
- **500 LOC Limit**: No file may exceed 500 lines of code (source or test)
- **Mandatory Modularization**: When limits exceeded, apply CUPID-based refactoring
- **Follow 4-phase Step pattern**: setup → apply → validate → persist for all pipeline steps
- **CUPID Principles**: Ensure all code is Composable, follows Unix Philosophy, Predictable, Idiomatic, and Domain-based
- **Dependency Injection**: All dependencies injected via constructor, never hard-coded
- **Repository Pattern**: All I/O operations through repository abstractions
- **Centralized Logging**: Single PipelineLogger instance for all operations
- **Type Safety**: Complete type hints on all public interfaces
- **Incremental Modification**: Always incrementally modify code rather than full deletes to prevent breakage or loss of progress
- **Preserve Progress**: Use version control or backups when refactoring to maintain work history

### Data Handling (BDD-Informed & Performance Optimized)
- **Phase 1 Data Analysis**: Use `xan` for investigation to inform Given-When-Then scenarios
- **Schema Validation**: Use pandera schemas for data validation at each step
- **Real Data Priority**: Prefer actual data subsets over synthetic for validation
- **Data-Driven Scenarios**: Update feature files when data insights reveal new requirements
- **Lineage Documentation**: Maintain transformation documentation in feature files and tests
- **Pandas Acceleration**: Always use `import fireducks.pandas as pd` for maximum performance
- **Performance Monitoring**: Track data processing bottlenecks and optimize with fireducks
- **Fireducks Installation**: Ensure `uv pip install fireducks` is run in development environment
- **Import Verification**: All data manipulation code must use `import fireducks.pandas as pd`

### Modular Organization & Code Consolidation
- **1 File Per Step**: Exactly one implementation file per pipeline step in `src/steps/`
- **No Duplicate Code**: Consolidate duplicate implementations into shared components
- **Legacy Code Preservation**: Never modify legacy step files directly under `src/`
- **Hub Folder Protection**: Treat `src/core/` and `src/config_new/` with extra care
- **Component Extraction**: Move reusable logic to `src/components/` and `src/utils/`
- **Clean Separation**: Maintain clear boundaries between business logic and infrastructure

### Testing (BDD-Driven & Size Compliant)
- **Feature Files First**: Write Gherkin scenarios before any implementation (Phase 1)
- **Test Scaffolding**: Create failing test structure before implementation (Phase 2)
- **Implementation to Specification**: Code must satisfy predefined test specifications (Phase 3)
- **Functional Test Validation**: Convert scaffolds to passing tests (Phase 4)
- **Binary Outcomes**: All tests must clearly PASS or FAIL - no conditional results
- **Living Documentation**: Tests serve as both validation and business requirement documentation
- **Test Size Limits**: Test files must also respect 500 LOC limit
- **Component Testing**: Test each modular component independently
- **Test Organization**: Maintain same modular structure as source code (1 test file per step)
- **Sequential Testing**: Test one component fully before moving to the next
- **Immediate Validation**: Run tests after each method implementation, not just at the end
- **🚫 Never use `python -c`** for testing - use proper BDD test framework
- **🚫 Don't create one-off testing scripts** - use structured BDD test files instead

## 🏗️ Architecture Principles (BDD & CUPID Aligned)

### Pipeline Design (4-Phase Pattern)
- **Setup Phase**: Load and prepare data from repositories
- **Apply Phase**: Transform and process data according to business rules
- **Validate Phase**: Verify data integrity and business constraints
- **Persist Phase**: Save results to appropriate output repositories
- **Context Management**: State passed between phases for predictable execution
- **Dependency Injection**: All external dependencies injected via constructors

### Error Handling (BDD-Specified)
- **Feature-Driven Validation**: Error scenarios defined in feature files before implementation
- **Fail Fast**: Comprehensive error logs with immediate failure on validation errors
- **No Silent Failures**: All errors must be logged and tracked with full context
- **DataValidationError**: Standard exception type for all business rule violations
- **Retry Logic**: Only for transient API failures, never for validation errors
- **Error Documentation**: Patterns documented in `notes/` with BDD scenario context

### Performance (Tested & Validated)
- **Batch Processing**: Efficient handling of large datasets with memory management
- **Incremental Processing**: Progress tracking and resumable operations
- **Memory Efficiency**: Data transformations optimized for large-scale processing
- **Performance Testing**: Benchmarks included in BDD scenarios for critical paths
- **Monitoring Integration**: Processing times and bottlenecks tracked in logs

## 📚 Reference Commands

### Essential Setup
```bash
uv pip install -e ".[dev]" pytest pytest-bdd fireducks complexipy
uv run pytest --version
```

### Code Quality Verification
```bash
# Size compliance (must be ≤ 500 LOC)
find src/ tests/ -name "*.py" -exec wc -l {} + | awk '$1 > 500 {print "VIOLATION: " $2 ": " $1 " lines"}'

# Modularization assessment
complexipy src/ tests/ --min 500

# Component verification
find src/ -maxdepth 1 -name "step*.py" | wc -l  # Should be 0
find src/steps/ -name "*.py" | sort
grep -r "import fireducks.pandas as pd" src/ | wc -l
```

### Testing & Debugging
```bash
# Run tests with background monitoring
uv run pytest tests/test_stepN.py -v &
procs --pager disable

# Targeted debugging
uv run pytest tests/test_stepN.py::test_scenario_name -v -s

# Integration testing
uv run pytest tests/ -x --tb=short
```

### Data Investigation
```bash
xan view data/file.csv
```

**Use `tldr` for command details** - `tldr xan`, `tldr find`, `tldr grep`, etc.
