# AI Agent Development Methodology - Procedures & Progress Tracking

## Overview

This document establishes **development procedures, methodology, and progress tracking standards** for software development using Behavior-Driven Development (BDD). This is **development-centric documentation** for developers implementing and tracking work.

**For test standards and specifications, see**: `../tests/AGENTS.md`  
**For system requirements and documentation standards, see**: `../docs/AGENTS.md`

---

## 🚀 BDD Development Phases & Procedures

### Four-Phase Development Cycle Overview

All development work follows these four sequential phases:

1. **Phase 1: Behavior Analysis & Use Cases** - Analyze requirements and define expected behavior
2. **Phase 2: Test Scaffolding** - Create test structure before implementation
3. **Phase 3: Code Refactoring** - Implement clean, modular code
4. **Phase 4: Test Implementation** - Convert scaffolds to functional tests

### Phase 1: Behavior Analysis & Use Case Definition

**Objective**: Define expected system behavior using clear, declarative scenarios before implementation.

#### 1.1 Given-When-Then Scenario Format

All use cases must follow the **Given-When-Then** structure:
- **Given**: Initial state (what data exists, what conditions are met)
- **When**: Action performed (what the system does)
- **Then**: Expected outcome (what should result)

#### 1.2 Behavioral Analysis Process

```bash
# 1. Analyze legacy code and document behavior
# Read existing code to understand current functionality
# Document in notes/ with timestamp: notes/behavior_analysis_$(date +%Y%m%d).md

# 2. Create feature files using Given-When-Then format
# Place in tests/features/ following naming: step-N-feature-name.feature
# Example: tests/features/step-2-extract-coordinates.feature

# 3. Write declarative scenarios from business perspective
# Use domain terminology stakeholders understand
# Include both happy path and failure scenarios
```

**Declarative Language (✅ GOOD)**: "Given raw product data with duplicates and null prices"  
**Implementation Details (❌ BAD)**: "Given the source_repo mock is configured to return test data"

#### 1.3 Scenario Generation Rules

- **Declarative Language**: Describe what happens, not how it's implemented
- **Business Context**: Use domain terminology that stakeholders understand
- **Complete Coverage**: Include happy path, error cases, and edge conditions
- **Independent Scenarios**: Each scenario must be able to run in isolation
- **Failure Scenarios**: Every feature must have validation failure tests

---

## 🧪 Phase 2: Test Scaffolding (Pre-Implementation)

**Objective**: Create test structure that mirrors feature files exactly, ensuring all tests fail until real implementation exists.

### Scaffold Structure Requirements

- **Mirror Feature Files**: Test organization must match feature file sequence exactly
- **Per-Scenario Organization**: Each scenario gets complete section with clear boundaries
- **Binary Failure**: All tests must fail with clear "SCAFFOLDING PHASE" messages
- **No Mock Data**: Pure placeholders only - no pandas DataFrames or test data

### Scaffold File Structure

```bash
# Create scaffold test files based on feature files
# Generate: tests/test_stepN_scaffold.py
# All tests should fail with "SCAFFOLDING PHASE" messages

# Each scenario gets its own complete section with clear header comments
# Steps organized by scenario: @scenario → @fixture → @given → @when → @then
# Order within scenario matches feature file sequence exactly
# All functions use pytest.fail() with clear "SCAFFOLDING PHASE" messages
```

### Scaffold Verification

```bash
# Verify all scaffold tests fail as expected
uv run pytest tests/test_*_scaffold.py -v
# Expected: All tests fail with "SCAFFOLDING PHASE" messages

# Verify no real implementation exists
grep -c "pytest.fail" tests/test_*_scaffold.py  # Should match scenario count
```

---

## 💻 Phase 3: Code Refactoring (CUPID Principles)

**Objective**: Transform requirements into clean, maintainable implementation.

### Four-Phase Step Pattern

All refactored code must implement the **setup → apply → validate → persist** execution pattern:

```
1. setup()      → Load and prepare data from repositories
2. apply()      → Transform data according to business rules
3. validate()   → Verify data integrity and business constraints
4. persist()    → Save results to appropriate output repositories
```

### CUPID Compliance Principles

- **Composable**: Modular components that can be combined and reused
- **Unix Philosophy**: Each component does one thing well (single responsibility)
- **Predictable**: Consistent behavior with clear contracts
- **Idiomatic**: Follow Python conventions and best practices
- **Domain-based**: Use business language in code structure and naming

### Dependency Injection & Repository Pattern

- **Repository Pattern**: All I/O through repository abstractions
- **Constructor Injection**: Dependencies injected via constructor parameters
- **Centralized Logging**: Single PipelineLogger instance for all operations
- **Type Safety**: Complete type hints on all public interfaces

---

## ✔️ Phase 4: Test Implementation & Validation

**Objective**: Convert scaffolding into functional tests that validate the refactored implementation.

### Test Implementation Process

```bash
# 1. Convert Scaffolding: Replace pytest.fail() calls with real implementations
cp tests/test_stepN_scaffold.py tests/test_stepN.py

# 2. Add Real Mocks: Replace None values with functional mock objects
# 3. Implement Logic: Add actual test execution and assertions
# 4. Validate Behavior: Ensure implementation matches feature file specifications

# Validate implementation matches feature specifications
uv run pytest tests/test_stepN.py -v
# Expected: All tests pass with real implementation

# Remove scaffold file after successful implementation
rm tests/test_stepN_scaffold.py

# Final verification of 500 LOC compliance for all files
find src/ tests/ -name "*.py" -exec wc -l {} + | awk '$1 > 500 {exit 1}' && echo "✅ All files comply with 500 LOC limit"
```

### Test Structure

- **Central fixture** holds step, mocks, context, and exception state
- **Given steps** configure mocks and test data
- **When steps** execute the actual step implementation
- **Then steps** validate results and assert expected behavior

### Binary Test Outcomes

- **✅ PASS**: Implementation matches feature file specifications
- **❌ FAIL**: Implementation doesn't match requirements (fix implementation, not tests)
- **🚫 NEVER**: Suppress failures or use conditional pass/fail logic

---

## 🔬 Root Cause Analysis (RCA) Within TDD/BDD Framework

### RCA Principles

Root Cause Analysis is a **systematic investigation technique** that identifies the fundamental cause of problems rather than treating symptoms. In a TDD/BDD context, RCA ensures bugs and failures are understood deeply before fixes are applied.

#### Core RCA Rules

- **Define the Problem Clearly**: Accurately describe the issue, including what happened, when, where, and expected vs. actual behavior
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

### Phase 1: Behavior Analysis
- [ ] Read legacy step2_extract_coordinates.py
- [ ] Analyze setup() phase behavior
- [ ] Analyze apply() phase behavior
- [ ] Analyze validate() phase behavior
- [ ] Analyze persist() phase behavior
- [ ] Create feature file with scenarios

### Phase 2: Test Scaffolding
- [ ] Generate scaffold test file
- [ ] Verify all tests fail appropriately
- [ ] Check for proper test organization

### Phase 3: Code Refactoring
- [ ] Implement ExtractCoordinatesStep class
- [ ] Add setup() method
- [ ] Add apply() method
- [ ] Add validate() method
- [ ] Add persist() method
- [ ] Verify 500 LOC compliance

### Phase 4: Test Implementation
- [ ] Convert scaffold to functional tests
- [ ] Replace pytest.fail() calls
- [ ] Add real mock objects
- [ ] Run all tests and verify pass
- [ ] Remove scaffold file

## Sub-Task Notes (Link to focused documentation)
- See: `../notes/step2_behavior_analysis_$(date +%Y%m%d).md` for Phase 1 details
- See: `../notes/debug_$(date +%Y%m%d)_issue.md` if blockers arise
- See: `../notes/rca_$(date +%Y%m%d)_incident.md` if issues need investigation

## Status Summary
- Total tasks: [X]
- Completed: [Y]
- In progress: [Z]
- Blocked: [W]
- Last updated: $(date +%Y-%m-%d %H:%M:%S)
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

### TODO List Maintenance Ritual

**Every session**: 
1. Update last modified timestamp
2. Add any new tasks discovered
3. Mark completed tasks [x]
4. Update status summary count
5. Review blocked tasks and RCA status

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

## Common Use Cases
- Use case 1: [Example command and result]
- Use case 2: [Example command and result]

## Troubleshooting & Tips
- Common issue 1: [Solution]
- Performance tip 1: [Optimization]

## Related Documentation
- Official docs: [URL]
- Similar tools: See ../notes/learning_tool_[other].md
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
2. [Step 2 with context]

## Best Practices
- [Best practice 1 with reasoning]
- [Best practice 2 with reasoning]

## Common Mistakes to Avoid
- Mistake 1: [Why this is wrong, what to do instead]

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

## Key Findings
1. [Finding 1 with evidence]
2. [Finding 2 with evidence]

## Approaches Compared
### Approach A: [Name]
- Pros: [Pro 1], [Pro 2]
- Cons: [Con 1], [Con 2]
- Best for: [Situations]

## Recommendation
- **Chosen approach**: [Why]
- **Rationale**: [Cost-benefit analysis, trade-offs]
- **Success criteria**: [How to measure success]
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
```

---

## 🧠 Critical Thinking: Feature Design & Testing Code Functionality

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

#### 2. Binary Test Outcomes (MANDATORY)

✅ **GOOD**: Clear binary outcome
```python
def test_coordinate_validation():
    """Test validates coordinates correctly."""
    try:
        fixture.when_extract_coordinates()
        assert fixture.result_is_valid()  # Test either passes or fails
    except Exception as e:
        pytest.fail(f"Coordinate extraction failed: {str(e)}")
```

❌ **BAD**: Conditional or suppressed outcomes
```python
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

---

## 📚 Development Workflow Summary

### Complete BDD Development Process

#### Sequential Phases

1. **Phase 1**: Analyze requirements → Create feature files
2. **Phase 2**: Create failing test scaffold
3. **Phase 3**: Implement code following CUPID principles
4. **Phase 4**: Convert scaffold to functional tests
5. **Validate**: Verify 500 LOC compliance and all tests pass

#### Key Principles

- **Sequential Focus**: Complete one component fully before starting the next
- **Continuous Validation**: Run tests after each method implementation
- **Technical Debt Management**: Address issues immediately, not later
- **Incremental Updates**: Update progress notes and TODO lists as work progresses
- **Real Data Priority**: Use actual data subsets, not synthetic/mock data
- **Binary Outcomes**: Tests must clearly PASS or FAIL - no conditional logic

---

## ✨ Final Methodology Principles

1. **Behavior-Driven**: Specifications define behavior before implementation
2. **Modular Documentation**: Separate notes by responsibility, avoid duplication
3. **Incremental Progress**: Update TODO and worklog progressively, not all at once
4. **Comprehensive RCA**: Systematically analyze root causes with 5 hypotheses
5. **Critical Thinking**: Question assumptions, anticipate edge cases, validate early
6. **Professional Learning**: Document procedures and best practices liberally
7. **Binary Testing**: All tests clearly pass or fail, no conditional logic
8. **Sequential Development**: One component at a time, complete before moving on
