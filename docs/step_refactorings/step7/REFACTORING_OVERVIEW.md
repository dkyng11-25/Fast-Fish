# Step 7 Refactoring Overview

**Date:** 2025-11-03  
**Status:** 🚀 READY TO START  
**Target:** Refactor Step 7 (Missing Category Rule) using proven protocol

---

## 📋 Refactoring Protocol Summary

This document summarizes the complete refactoring process developed for Steps 4, 5, and 6, which we'll apply to Step 7.

---

## 🎯 The Complete Process: 6 Phases

### **Phase 0: Design Review Gate** (MANDATORY - 15-30 min)
**⚠️ CRITICAL: Do NOT skip this phase!**

**Purpose:** Verify design correctness BEFORE implementation to prevent expensive rework.

**What Step 6 Taught Us:**
- Skipping Phase 0 cost 150 minutes of rework
- A 15-minute design review would have caught all issues
- **ROI: 1000%** (save 150 min by investing 15 min)

**Critical Mistakes Phase 0 Prevents:**
1. ❌ Creating `algorithms/` folder (architecture violation)
2. ❌ Injecting algorithm as dependency (wrong pattern)
3. ❌ VALIDATE calculating instead of validating (wrong purpose)
4. ❌ VALIDATE returning StepContext instead of None (wrong signature)
5. ❌ Using inline imports instead of top-of-file imports

**Deliverables:**
- [ ] Read Steps 4 & 5 implementations completely
- [ ] Complete Reference Comparison Checklist
- [ ] Verify VALIDATE phase design (returns `-> None`, validates not calculates)
- [ ] Verify import standards (all at top of file)
- [ ] Create `REFERENCE_COMPARISON.md`
- [ ] Create `DESIGN_REVIEW_SIGNOFF.md`
- [ ] Get sign-off before proceeding

**STOP Criteria:**
- ❌ Reference comparison not complete → STOP
- ❌ VALIDATE phase design wrong → STOP
- ❌ Inline imports planned → STOP
- ✅ All checks pass → PROCEED to Phase 1

---

### **Phase 1: Analysis & Test Design** (1-2 hours)

**Purpose:** Understand behavior and design tests BEFORE coding.

**Key Activities:**

#### 1.1 Analyze Original Script
- Read `src/step7_missing_category_rule.py`
- List all behaviors organized by 4 phases:
  - **SETUP:** What data is loaded
  - **APPLY:** What transformations are performed
  - **VALIDATE:** What validation checks are performed
  - **PERSIST:** What data is saved

#### 1.2 Check Downstream Dependencies (CRITICAL!)
**⚠️ Step 5 caught missing columns here - don't skip!**

```bash
# Find what files Step 7 creates
grep -r "to_csv\|\.save\|OUTPUT" src/step7_*.py

# Find downstream consumers
grep -r "rule7\|missing_category" src/step*.py

# Check Step 13 (consolidates all rules)
grep -r "rule7" src/step13_*.py
```

**Document:**
- Output files Step 7 creates
- Columns in each file
- Which steps consume these files
- Required columns for downstream steps

#### 1.3 Generate Test Scenarios
- Create Gherkin feature file with Given/When/Then scenarios
- Cover: happy path, edge cases, error conditions
- Add test data convention comments
- Save to: `tests/features/step-7-missing-category-rule.feature`

#### 1.3.2 Design VALIDATE Phase (CRITICAL!)
**🚨 Read Steps 4 & 5 validate() methods FIRST!**

**VALIDATE Phase Must:**
- ✅ Return type: `-> None` (NOT `-> StepContext`)
- ✅ Purpose: Validation (NOT calculation)
- ✅ Behavior: Raise DataValidationError on failure
- ✅ No metrics calculation (metrics go in APPLY phase)

**Common Mistakes:**
```python
# ❌ WRONG
def validate(self, context) -> StepContext:
    silhouette = silhouette_score(data, labels)  # ❌ Calculating
    return context  # ❌ Returning data

# ✅ CORRECT
def validate(self, context) -> None:
    metrics = context.data.get('metrics', {})  # ✅ Using pre-calculated
    if metrics.get('silhouette', -1) < -0.5:  # ✅ Checking threshold
        raise DataValidationError("Poor quality")  # ✅ Raising error
    # ✅ Returns None implicitly
```

#### 1.4 Review Test Coverage
- Verify all behaviors from analysis are covered
- Check for gaps in edge cases or error conditions

#### 1.5 Critical Sanity Check
- Compare feature file against `code_design_standards.md`
- Compare against Step 1 feature file (reference)
- Check Background focuses on business context
- Check scenarios are outcome-focused
- Create: `SANITY_CHECK_PHASE1.md`
- **Target: 10/10 quality score**

**Deliverables:**
- [ ] `BEHAVIOR_ANALYSIS.md`
- [ ] `testing/TEST_SCENARIOS.md`
- [ ] `testing/TEST_DESIGN.md`
- [ ] `DOWNSTREAM_INTEGRATION_ANALYSIS.md`
- [ ] `SANITY_CHECK_PHASE1.md`
- [ ] `PHASE1_COMPLETE.md`
- [ ] Feature file: `tests/features/step-7-missing-category-rule.feature`

**STOP Criteria:**
- ❌ Quality score < 8/10 → FIX before Phase 2
- ❌ VALIDATE phase has calculations → REDESIGN
- ✅ All deliverables complete → PROCEED to Phase 2

---

### **Phase 2: Test Implementation** (2-4 hours)

**Purpose:** Create failing tests that define expected behavior.

**⚠️ CRITICAL: Use Correct Test Pattern!**

**DO NOT look at:**
- ❌ `tests/step04/isolated/` (pre-refactoring, wrong pattern)
- ❌ `tests/step05/isolated/` (pre-refactoring, wrong pattern)
- ❌ Any tests using `subprocess.run()`

**DO look at:**
- ✅ `tests/step_definitions/test_step4_weather_data.py`
- ✅ `tests/step_definitions/test_step5_feels_like_temperature.py`
- ✅ `tests/features/step-4-weather-data.feature`
- ✅ `tests/features/step-5-feels-like-temperature.feature`

**Required Reading:**
📖 `docs/step_refactorings/step6/CRITICAL_LESSON_TEST_PATTERN.md`

**Key Activities:**

#### 2.1 Create Test File Structure
- Create: `tests/step_definitions/test_step7_missing_category_rule.py`
- Use pytest-bdd framework
- Create fixtures for all test data
- Mock ALL repositories (no real I/O)

#### 2.2 Implement Mock Data
- Create realistic synthetic test data
- Use fixtures to provide test data
- Ensure mocks return correct data structures

#### 2.3 Implement Test Logic
- Implement each @given, @when, @then step
- **CRITICAL:** Tests must call `step_instance.execute()`
- Use mocked repositories
- Assert expected outcomes

#### 2.4 Run Tests (Should Fail)
```bash
pytest tests/step_definitions/test_step7_*.py -v
```
**Expected:** All tests FAIL (no implementation yet)

#### 2.5 Test Quality Verification (CRITICAL!)
**🚨 STOP! Verify tests actually test behavior!**

**Bad Test (Only Mocks):**
```python
@when('processing data')
def process(test_context, mock_api):
    mock_api.fetch.return_value = mock_data  # ❌ Only sets up mock
    test_context['called'] = True

@then('data should be processed')
def verify(test_context):
    assert test_context['called'] is True  # ❌ Only checks mock setup
```

**Good Test (Calls Real Code):**
```python
@when('processing data')
def process(test_context, step_instance):
    result = step_instance.execute()  # ✅ Actually executes step
    test_context['result'] = result

@then('data should be processed')
def verify(test_context):
    assert test_context['result']['status'] == 'success'  # ✅ Checks actual result
```

**Test Organization:**
- ✅ Group by scenario (not by decorator type)
- ✅ Add comment headers separating scenarios
- ✅ Match feature file order

**Checklist:**
- [ ] Zero placeholder assertions (`assert True`)
- [ ] All assertions check actual values
- [ ] All assertions have error messages
- [ ] Tests call `step_instance.execute()`
- [ ] Tests can fail if behavior is wrong
- [ ] Organized by scenario

**Deliverables:**
- [ ] `tests/step_definitions/test_step7_missing_category_rule.py`
- [ ] All tests implemented (failing)
- [ ] Test quality verified (100% real assertions)
- [ ] `testing/PHASE2_TEST_DESIGN.md`
- [ ] `PHASE2_COMPLETE.md`

**STOP Criteria:**
- ❌ Tests don't call `execute()` → FIX
- ❌ Placeholder assertions found → REPLACE
- ❌ Tests organized by decorator → REORGANIZE
- ✅ All checks pass → PROCEED to Phase 3

---

### **Phase 3: Code Implementation** (4-8 hours)

**Purpose:** Implement the refactored step following design standards.

**⚠️ CRITICAL Architecture Rules:**

**DO NOT Create:**
- ❌ `src/algorithms/` folder
- ❌ `src/services/` folder for business logic
- ❌ `src/utils/` for business logic

**DO Create:**
- ✅ `src/steps/missing_category_rule_step.py` (main step)
- ✅ `src/factories/step7_factory.py` (dependency injection)
- ✅ Business logic IN the step's `apply()` method

**What to Inject:**
- ✅ Repositories (data access)
- ✅ Configuration (parameters)
- ✅ Logger (infrastructure)

**What NOT to Inject:**
- ❌ Algorithms (business logic)
- ❌ Transformations (business logic)
- ❌ Calculations (business logic)

**Key Activities:**

#### 3.1 Create Repository Interfaces (if needed)
- Identify data sources Step 7 needs
- Create repository interfaces in `src/repositories/`
- Follow existing repository patterns

#### 3.2 Implement Step Class
**File:** `src/steps/missing_category_rule_step.py`

**Structure:**
```python
import fireducks.pandas as pd  # ✅ At top of file
from src.core.step import Step
from src.core.context import StepContext
from src.core.exceptions import DataValidationError  # ✅ At top

class MissingCategoryRuleStep(Step):
    def __init__(self, repos, config, logger):
        # Inject dependencies
        
    def setup(self, context: StepContext) -> StepContext:
        # Load data via repositories
        
    def apply(self, context: StepContext) -> StepContext:
        # Business logic HERE (not in separate algorithm class)
        # Calculate metrics at END of apply
        
    def validate(self, context: StepContext) -> None:  # ✅ Returns None
        # Validate using pre-calculated metrics
        # Raise DataValidationError on failure
        # NO calculations here
        
    def persist(self, context: StepContext) -> StepContext:
        # Save results via repositories
```

#### 3.3 Create Factory
**File:** `src/factories/step7_factory.py`

- Centralized dependency injection
- Configuration management
- Simplified testing setup

#### 3.4 Implement CLI Entry Point
- Add `if __name__ == '__main__':` block
- Parse command-line arguments
- Call factory to create step
- Execute step

#### 3.5 Code Quality Checks
- [ ] All imports at top of file (NO inline imports)
- [ ] All files ≤ 500 LOC
- [ ] All functions ≤ 200 LOC
- [ ] Uses `fireducks.pandas` (not standard pandas)
- [ ] Complete type hints on public interfaces
- [ ] Docstrings on all classes and methods
- [ ] No hard-coded values or paths
- [ ] No print() statements (use logger)

**Deliverables:**
- [ ] `src/steps/missing_category_rule_step.py`
- [ ] `src/factories/step7_factory.py`
- [ ] Code matches design exactly
- [ ] All imports at top of file
- [ ] `PHASE3_COMPLETE.md`

**STOP Criteria:**
- ❌ Code doesn't match design → FIX
- ❌ Inline imports used → MOVE to top
- ❌ VALIDATE calculates → MOVE to APPLY
- ❌ File > 500 LOC → MODULARIZE
- ✅ All checks pass → PROCEED to Phase 4

---

### **Phase 4: Validation & Testing** (2-4 hours)

**Purpose:** Verify implementation matches design and all tests pass.

**Key Activities:**

#### 4.1 Run Tests
```bash
pytest tests/step_definitions/test_step7_*.py -v
```

**Target: 100% pass rate**

#### 4.2 Debug Failures
- For each failing test:
  - Identify root cause
  - Fix implementation (not test)
  - Re-run tests
  - Repeat until passing

**NO "good enough" acceptance!**
- ❌ 91% passing is NOT acceptable
- ✅ 100% passing is required

#### 4.3 Integration Testing
```bash
# Run Step 7 with real data
PYTHONPATH=. python3 src/steps/missing_category_rule_step.py \
  --target-yyyymm 202510 \
  --target-period A
```

#### 4.4 Compare with Legacy
- Run legacy Step 7
- Run refactored Step 7
- Compare outputs
- Document differences (if any)
- Justify differences (if any)

**Deliverables:**
- [ ] All tests passing (100%)
- [ ] Integration test successful
- [ ] Legacy comparison complete
- [ ] `PHASE4_COMPLETE.md`

**STOP Criteria:**
- ❌ Test pass rate < 100% → DEBUG and FIX
- ❌ Integration test fails → DEBUG and FIX
- ❌ Unexplained differences from legacy → INVESTIGATE
- ✅ All checks pass → PROCEED to Phase 5

---

### **Phase 5: Integration & Documentation** (1-2 hours)

**Purpose:** Integrate with pipeline and finalize documentation.

**Key Activities:**

#### 5.1 Factory Integration
- Verify factory creates step correctly
- Test error handling
- Test configuration

#### 5.2 CLI Integration
- Test command-line interface
- Verify argument parsing
- Test error messages

#### 5.3 Pipeline Integration
- Test Step 7 in full pipeline context
- Verify downstream steps work
- Check Step 13 consolidation

#### 5.4 Documentation
- Update `README.md` with usage instructions
- Document any deviations from design
- Capture lessons learned
- Update project map

**Deliverables:**
- [ ] Factory integration verified
- [ ] CLI integration verified
- [ ] Pipeline integration verified
- [ ] `README.md` complete
- [ ] `LESSONS_LEARNED.md` complete
- [ ] `PHASE5_COMPLETE.md`
- [ ] Update `REFACTORING_PROJECT_MAP.md`

---

### **Phase 6: Final Review & Cleanup** (30 min - 1 hour)

**Purpose:** Final quality check and cleanup.

**Key Activities:**

#### 6.1 Final Quality Check
- [ ] All tests passing
- [ ] All documentation complete
- [ ] All deliverables in correct locations
- [ ] Code quality standards met
- [ ] No TODO or FIXME comments

#### 6.2 Cleanup Transient Files
```bash
# Move temporary files to transient/
mv docs/step_refactorings/step7/*_PROGRESS.md docs/transient/status/
mv docs/step_refactorings/step7/*_STATUS.md docs/transient/status/
```

#### 6.3 Final Sign-Off
- Create final summary document
- Get approval to merge
- Tag completion in project map

**Deliverables:**
- [ ] Final quality check complete
- [ ] Transient files moved
- [ ] Final sign-off obtained

---

## 📁 Documentation Structure

### Permanent Files (Keep Forever)
```
docs/step_refactorings/step7/
├── REFACTORING_OVERVIEW.md          ← This file
├── BEHAVIOR_ANALYSIS.md             ← Phase 1
├── REFERENCE_COMPARISON.md          ← Phase 0
├── DESIGN_REVIEW_SIGNOFF.md         ← Phase 0
├── DOWNSTREAM_INTEGRATION_ANALYSIS.md ← Phase 1
├── PHASE1_COMPLETE.md
├── PHASE2_COMPLETE.md
├── PHASE3_COMPLETE.md
├── PHASE4_COMPLETE.md
├── PHASE5_COMPLETE.md
├── LESSONS_LEARNED.md
├── README.md                        ← Final documentation
└── testing/
    ├── TEST_SCENARIOS.md
    ├── TEST_DESIGN.md
    └── PHASE2_TEST_DESIGN.md
```

### Temporary Files (Delete After Merge)
```
docs/transient/
├── status/
│   ├── STEP7_PROGRESS_UPDATE.md
│   └── STEP7_CURRENT_STATUS.md
├── testing/
│   └── STEP7_TEST_RESULTS.md
└── compliance/
    └── STEP7_COMPLIANCE_CHECK.md
```

---

## 🎯 Success Criteria

### Phase 0 Success:
- ✅ Reference comparison complete
- ✅ VALIDATE phase design correct
- ✅ Design review sign-off obtained

### Phase 1 Success:
- ✅ Behavior analysis complete
- ✅ Test scenarios comprehensive
- ✅ Downstream dependencies documented
- ✅ Quality score 10/10

### Phase 2 Success:
- ✅ All tests implemented
- ✅ Tests call `execute()` method
- ✅ 100% real assertions (no placeholders)
- ✅ Tests organized by scenario

### Phase 3 Success:
- ✅ Code matches design
- ✅ All imports at top of file
- ✅ Business logic in `apply()` method
- ✅ VALIDATE returns `-> None`
- ✅ All files ≤ 500 LOC

### Phase 4 Success:
- ✅ 100% test pass rate
- ✅ Integration test passes
- ✅ Legacy comparison complete

### Phase 5 Success:
- ✅ Factory integration verified
- ✅ CLI integration verified
- ✅ Pipeline integration verified
- ✅ Documentation complete

---

## ⚠️ Critical Warnings

### DO NOT:
1. ❌ Skip Phase 0 design review
2. ❌ Create `algorithms/` folder
3. ❌ Inject algorithms as dependencies
4. ❌ Make VALIDATE calculate metrics
5. ❌ Use inline imports
6. ❌ Look at pre-refactoring test examples
7. ❌ Accept < 100% test pass rate
8. ❌ Skip downstream dependency check

### DO:
1. ✅ Complete Phase 0 before coding
2. ✅ Keep business logic in step's `apply()` method
3. ✅ Make VALIDATE only validate
4. ✅ Put all imports at top of file
5. ✅ Use refactored test examples (step_definitions/)
6. ✅ Achieve 100% test pass rate
7. ✅ Document downstream dependencies

---

## 📚 Key Reference Documents

### Must Read Before Starting:
1. `docs/process_guides/REFACTORING_PROCESS_GUIDE.md` - Complete process
2. `docs/process_guides/code_design_standards.md` - Design standards
3. `docs/step_refactorings/step6/CRITICAL_LESSON_TEST_PATTERN.md` - Test pattern
4. `src/steps/weather_data_step.py` - Step 4 reference
5. `src/steps/temperature_analysis_step.py` - Step 5 reference
6. `tests/step_definitions/test_step5_feels_like_temperature.py` - Test reference

### Reference During Work:
- `docs/step_refactorings/step5/README.md` - Step 5 example
- `docs/step_refactorings/step6/README.md` - Step 6 example
- `docs/step_refactorings/step6/LESSONS_LEARNED.md` - Mistakes to avoid

---

## 💡 Time Estimates

| Phase | Estimated Time | Critical? |
|-------|---------------|-----------|
| Phase 0: Design Review | 15-30 min | ⚠️ MANDATORY |
| Phase 1: Analysis | 1-2 hours | Required |
| Phase 2: Tests | 2-4 hours | Required |
| Phase 3: Code | 4-8 hours | Required |
| Phase 4: Validation | 2-4 hours | Required |
| Phase 5: Integration | 1-2 hours | Required |
| Phase 6: Cleanup | 30 min - 1 hour | Required |
| **Total** | **11-21 hours** | |

**Time Saved by Following Process:**
- Phase 0 prevents 150 min of rework (ROI: 1000%)
- Correct test pattern saves 2-3 hours
- Downstream check prevents integration failures

---

## ✅ Ready to Start?

**Before beginning Phase 0, verify:**
- [ ] Read this overview completely
- [ ] Understand all 6 phases
- [ ] Know what NOT to do (critical warnings)
- [ ] Have reference documents accessible
- [ ] Ready to follow process strictly

**Next Step:** Begin Phase 0 - Design Review Gate

---

**Good luck with the refactoring! Follow the process, and you'll succeed! 🚀**
