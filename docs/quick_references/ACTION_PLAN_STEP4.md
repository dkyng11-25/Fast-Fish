# Step 4 Refactoring - Action Plan from Management Review

**Date:** 2025-10-10  
**Meeting:** Management review with Vitor (Boss)  
**Status:** Step 4 needs corrections before proceeding to Step 5

---

## 📋 Executive Summary

Management review identified several critical issues with Step 4 refactoring approach:

1. **Step 4 should be a Repository, not a Step** - It only retrieves/formats data for Step 5
2. **Tests are not actually testing** - They mock everything but don't call `execute()`
3. **Download logic should be in Repository** - Not in the step implementation
4. **File organization needs improvement** - Utils/factories should be in separate folder
5. **Test organization needs improvement** - Should match feature file order

**Decision:** Refactor Step 4 and Step 5 together in the same branch.

---

## 🎯 Immediate Action Items

### Priority 1: Fix Step 4 Architecture (CRITICAL)

#### 1.1 Convert Step 4 to Repository Pattern
- [ ] **Create `WeatherDataRepository`** in `src/repositories/`
- [ ] **Move all download logic** from `weather_data_download_step.py` to repository
- [ ] **Move all file saving logic** to repository
- [ ] **Keep only data formatting logic** in repository
- [ ] **Delete `weather_data_download_step.py`** (no longer needed as a step)

**Rationale:** Step 4 only retrieves and formats data for Step 5. This is repository responsibility, not step responsibility.

#### 1.2 Refactor Step 5 to Use Weather Repository
- [ ] **Start refactoring Step 5** using the 5-phase methodology
- [ ] **In Step 5 setup phase**, call `WeatherDataRepository` to get data
- [ ] **Step 5 apply phase** will compute "feels-like" temperature
- [ ] **Step 5 will be the actual step** that processes weather data

**Rationale:** Step 5 is where weather data is actually processed and used for clustering.

---

### Priority 2: Fix Test Implementation (CRITICAL)

#### 2.1 Tests Must Call `execute()` Method
- [ ] **Review all test scenarios** in `test_step4_weather_data.py`
- [ ] **Ensure tests call `step_instance.execute()`** to run actual code
- [ ] **Remove tests that only mock without testing** real behavior
- [ ] **Verify tests actually fail** when implementation is broken

**Current Problem:** Tests mock everything but never call the actual implementation.

**Example Fix:**
```python
# ❌ WRONG - Only tests mocks
@when('downloading weather data')
def download_weather(test_context):
    # Just sets up mocks, doesn't run code
    test_context['mock_api'].fetch_weather_data.return_value = mock_data

# ✅ CORRECT - Actually runs code
@when('downloading weather data')
def download_weather(test_context, step_instance):
    # Actually executes the step
    result = step_instance.execute()
    test_context['result'] = result
```

#### 2.2 Organize Tests to Match Feature File
- [ ] **Reorganize test functions** to match feature file order
- [ ] **Group by scenario** instead of by decorator type (@given/@when/@then)
- [ ] **Add comments** separating each scenario
- [ ] **Make tests readable** by following feature file structure

**Prompt for LLM:**
```
Please reorganize the test code to match the feature file structure.
Instead of grouping all @given together, all @when together, etc.,
organize the code by scenario in the same order as the feature file.

This makes it easier to read and validate tests.
```

---

### Priority 3: File Organization (HIGH)

#### 3.1 Create Utils Folder
- [ ] **Create `src/utils/` folder**
- [ ] **Move factory files** to `src/utils/`:
  - `weather_data_factory.py`
  - Any other factory files
- [ ] **Move extractor files** to `src/utils/`:
  - `coordinate_extractor.py`
  - `matrix_processor.py`
  - `spu_metadata_processor.py`
- [ ] **Keep only step files** in `src/steps/`

**Rationale:** Steps folder should only contain step implementations, not utilities.

#### 3.2 Standardize File Naming
- [ ] **Review all step files** for consistent naming
- [ ] **Ensure step files end with `_step.py`** (e.g., `api_download_merge_step.py`)
- [ ] **Document naming convention** in process guide

---

### Priority 4: Update Process Guide (HIGH)

#### 4.1 Add Repository-First Decision Tree
- [ ] **Add section**: "Is This a Step or a Repository?"
- [ ] **Decision criteria**:
  - If it only retrieves/formats data → Repository
  - If it processes/transforms data → Step
  - If it's used by multiple steps → Repository
  - If it's a standalone process → Step

#### 4.2 Add Test Quality Requirements
- [ ] **Add section**: "Test Quality Checklist"
- [ ] **Requirement**: Tests must call `execute()` method
- [ ] **Requirement**: Tests must be organized by scenario
- [ ] **Requirement**: Tests must actually fail when code is broken
- [ ] **Add example**: Good vs bad test implementation

#### 4.3 Add File Organization Standards
- [ ] **Document folder structure**:
  - `src/steps/` - Only step implementations
  - `src/repositories/` - Data access and retrieval
  - `src/utils/` - Factories, extractors, processors
  - `src/core/` - Base classes and shared logic
- [ ] **Document naming conventions** for each folder

#### 4.4 Add LLM Prompting Best Practices
- [ ] **Add section**: "How to Prompt LLMs Effectively"
- [ ] **Key principle**: "Treat LLM like a 5-year-old - be very specific"
- [ ] **Always ask LLM to show plan first** before implementing
- [ ] **Always validate plan** before proceeding
- [ ] **Add common prompts** for each phase

---

### Priority 5: Create Test Documentation Standard (HIGH)

#### 5.1 Create Test Guide Document
- [ ] **Create `docs/TEST_DESIGN_STANDARDS.md`**
- [ ] **Document BDD test structure** (Given/When/Then)
- [ ] **Document test organization** (match feature file order)
- [ ] **Document test quality requirements** (must call execute())
- [ ] **Provide examples** of good vs bad tests
- [ ] **Add prompts** for LLM to generate correct tests

#### 5.2 Test Template
- [ ] **Create test template** that LLMs can follow
- [ ] **Include fixture setup** examples
- [ ] **Include scenario structure** examples
- [ ] **Include assertion** examples

---

## 📚 Key Learnings from Review

### Critical Insights:

1. **Not Everything is a Step**
   - Steps process data
   - Repositories retrieve/store data
   - If it only downloads/formats → Repository

2. **Tests Must Test Real Code**
   - Mocking is for dependencies, not the code under test
   - Tests must call `execute()` to run actual implementation
   - Tests that only mock are worthless

3. **Organization Matters**
   - Steps folder = only steps
   - Utils folder = factories, extractors, processors
   - Tests should match feature file structure

4. **LLM Prompting is Critical**
   - Be extremely specific
   - Ask for plan first, then validate
   - Reference standard documents
   - Treat LLM like a 5-year-old

5. **Refactor Related Steps Together**
   - Step 4 feeds Step 5
   - Refactor both in same branch
   - Convert Step 4 to repository
   - Use repository in Step 5 setup

---

## 🔄 Revised Workflow for Step 4 + Step 5

### Phase 1: Convert Step 4 to Repository (2 hours)

1. **Create `WeatherDataRepository`**
   - Move download logic from step to repository
   - Move file saving logic to repository
   - Keep data formatting in repository
   - Add proper error handling

2. **Update Tests**
   - Tests should test repository methods
   - Mock only external APIs (weather API)
   - Test actual data retrieval and formatting

3. **Delete Step 4 Step File**
   - Remove `weather_data_download_step.py`
   - Remove `weather_data_factory.py` (or move to utils)
   - Update imports

### Phase 2: Refactor Step 5 (8-10 hours)

1. **Follow 5-Phase Methodology**
   - Phase 1: Analyze Step 5 behaviors
   - Phase 2: Design and implement tests
   - Phase 3: Implement Step 5 using repository
   - Phase 4: Validate implementation
   - Phase 5: Integration and documentation

2. **Step 5 Setup Phase**
   - Call `WeatherDataRepository` to get weather data
   - Load other required data
   - Initialize processing

3. **Step 5 Apply Phase**
   - Compute "feels-like" temperature
   - Add humidity, wind chill effects
   - Prepare data for clustering

4. **Step 5 Tests**
   - Must call `step_instance.execute()`
   - Organized by scenario
   - Test actual temperature calculations

---

## 📋 Detailed To-Do List

### Immediate (This Week)

#### Step 4 Corrections:
- [ ] Create `src/repositories/weather_data_repository.py`
- [ ] Move download logic from step to repository
- [ ] Move file operations to repository
- [ ] Update tests to test repository (not step)
- [ ] Delete `src/steps/weather_data_download_step.py`
- [ ] Move `weather_data_factory.py` to `src/utils/`

#### Test Fixes:
- [ ] Review all test scenarios in `test_step4_weather_data.py`
- [ ] Ensure tests call actual code (not just mocks)
- [ ] Reorganize tests to match feature file order
- [ ] Add comments separating scenarios
- [ ] Verify tests can actually fail

#### File Organization:
- [ ] Create `src/utils/` folder
- [ ] Move factory files to utils
- [ ] Move extractor files to utils
- [ ] Update all imports
- [ ] Document folder structure

### Short-Term (Next Week)

#### Process Guide Updates:
- [ ] Add "Is This a Step or Repository?" decision tree
- [ ] Add test quality requirements section
- [ ] Add file organization standards
- [ ] Add LLM prompting best practices
- [ ] Add examples of good vs bad tests

#### Test Documentation:
- [ ] Create `docs/TEST_DESIGN_STANDARDS.md`
- [ ] Document BDD structure
- [ ] Document test organization
- [ ] Provide test examples
- [ ] Add LLM prompts for tests

#### Step 5 Refactoring:
- [ ] Start Step 5 analysis (Phase 1)
- [ ] Design Step 5 tests (Phase 2)
- [ ] Implement Step 5 using weather repository (Phase 3)
- [ ] Validate Step 5 (Phase 4)
- [ ] Integrate Step 5 (Phase 5)

### Medium-Term (Next 2 Weeks)

#### Documentation:
- [ ] Update `REFACTORING_PROJECT_MAP.md` with learnings
- [ ] Create `STEP5_FINAL_SUMMARY.md`
- [ ] Update executive summary with Step 5 results
- [ ] Document Step 4→5 refactoring approach

#### Process Improvements:
- [ ] Create reusable test templates
- [ ] Create reusable LLM prompts
- [ ] Document common pitfalls
- [ ] Create decision trees for common questions

---

## 🎯 Success Criteria

### Step 4 (Repository):
- ✅ `WeatherDataRepository` exists and works
- ✅ All download logic is in repository
- ✅ Tests test repository methods
- ✅ No step file exists for Step 4
- ✅ Files organized in correct folders

### Step 5 (Actual Step):
- ✅ Step 5 uses `WeatherDataRepository` in setup
- ✅ Step 5 computes feels-like temperature
- ✅ Tests call `execute()` method
- ✅ Tests organized by scenario
- ✅ All tests pass
- ✅ 100% test coverage

### Process Guide:
- ✅ Decision tree for step vs repository
- ✅ Test quality requirements documented
- ✅ File organization standards documented
- ✅ LLM prompting best practices documented
- ✅ Test design standards document created

### Documentation:
- ✅ All required documents created
- ✅ Lessons learned captured
- ✅ Process improvements documented
- ✅ Executive summary updated

---

## 🚨 Critical Mistakes to Avoid

Based on Step 4 review:

1. **Don't create steps for data retrieval** - Use repositories
2. **Don't write tests that only mock** - Tests must call real code
3. **Don't organize tests by decorator type** - Organize by scenario
4. **Don't put utilities in steps folder** - Use utils folder
5. **Don't refactor steps in isolation** - Refactor related steps together
6. **Don't skip asking LLM for plan first** - Always validate plan
7. **Don't assume LLM did it right** - Always validate implementation

---

## 📞 Questions for Next Review

1. Is the repository approach for Step 4 correct?
2. Does Step 5 implementation make sense?
3. Are the tests now testing actual code?
4. Is the file organization acceptable?
5. Are the process guide updates sufficient?
6. Should we proceed with Step 6 or fix anything else?

---

## 🎓 Key Quotes from Review

> "Maybe this whole thing here is just a repository that is called in step 5."  
> — Vitor (on Step 4 architecture)

> "When you test, you need to run the method that runs that code. Execute."  
> — Vitor (on test quality)

> "Imagine LLMs as a five year old kid. If you don't say exactly what you want to do, it would do whatever it thinks is right."  
> — Vitor (on LLM prompting)

> "Let's create a folder that is just utils."  
> — Vitor (on file organization)

> "Maybe what we need is a similar one for testing."  
> — Vitor (on test documentation)

---

**Next Steps:** Execute Priority 1 and Priority 2 items immediately. These are blocking issues that must be fixed before proceeding.

**Timeline:** Aim to complete Step 4 corrections and Step 5 refactoring within 1 week.

**Status:** 🔴 BLOCKED - Must fix Step 4 architecture before proceeding
