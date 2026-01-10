# Sanity Check Best Practices - Critical Quality Gate

**Date:** 2025-10-10 12:55 SGT  
**Status:** ✅ MANDATORY PROCESS  
**Origin:** Lessons from Step 5 Phase 1

---

## 🎯 Purpose

Sanity checks are **mandatory quality gates** that prevent implementing flawed designs. They catch issues early when fixes are cheap (minutes) rather than late when fixes are expensive (hours).

**Key Insight:** Step 5 sanity check found 3 critical issues in 15 minutes, preventing 2-3 hours of rework in Phase 2.

---

## 📊 When to Perform Sanity Checks

**EVERY PHASE NEEDS SANITY CHECKS** - Quality gates at each phase prevent cascading issues.

### **Phase 1: After Test Design** 🔴 **CRITICAL**
- **When:** After creating feature file, before Phase 2
- **What:** Feature file quality, scenario design, integration coverage
- **Why:** Prevents implementing tests for flawed scenarios
- **Time:** 15-30 minutes
- **Value:** Prevents 2-3 hours of rework in Phase 2
- **Document:** `SANITY_CHECK_PHASE1.md`

### **Phase 2: After Test Implementation** 🔴 **CRITICAL**
- **When:** After writing tests, before Phase 3
- **What:** Test quality, fixture design, test execution patterns
- **Why:** Ensures tests actually test real code
- **Time:** 15-20 minutes
- **Value:** Prevents implementing code for flawed tests
- **Document:** `SANITY_CHECK_PHASE2.md`

### **Phase 3: After Code Implementation** 🔴 **CRITICAL**
- **When:** After implementing step, before Phase 4
- **What:** Code standards, dependency injection, repository usage
- **Why:** Ensures code follows design patterns
- **Time:** 15-20 minutes
- **Value:** Prevents validation failures and rework
- **Document:** `SANITY_CHECK_PHASE3.md`

### **Phase 4: After Validation** 🟡 **IMPORTANT**
- **When:** After all tests pass, before Phase 5
- **What:** Test coverage, code quality, standards compliance
- **Why:** Ensures completeness and quality
- **Time:** 10-15 minutes
- **Value:** Catches gaps before integration
- **Document:** `SANITY_CHECK_PHASE4.md`

### **Phase 5: Before Integration** 🟡 **IMPORTANT**
- **When:** Before integrating with pipeline
- **What:** Integration points, factory design, CLI compatibility
- **Why:** Ensures smooth integration
- **Time:** 10-15 minutes
- **Value:** Prevents integration issues
- **Document:** `SANITY_CHECK_PHASE5.md`

---

## 🔍 Phase 1 Sanity Check (MANDATORY)

### **What to Check:**

#### **1. Feature File Background** 🔴
```gherkin
❌ BAD (Technical Setup):
Background:
  Given a WeatherDataRepository with weather data
  And an altitude repository with store elevations
  And a pipeline logger
  And a configuration object

✅ GOOD (Business Context):
Background:
  Given weather data exists for multiple stores
  And altitude data exists for stores
  And a target period "202506A"
  And configuration is set
```

**Why This Matters:**
- Feature files are business documents
- Business stakeholders should understand them
- Technical details belong in test implementation

---

#### **2. Scenario Focus** 🔴
```gherkin
❌ BAD (Implementation Details):
Scenario: Calculate wind chill for cold conditions
  Given weather data with temperature 5°C and wind speed 20 km/h
  When calculating feels-like temperature
  Then wind chill formula should be applied
  And air density correction should be applied to wind speed

✅ GOOD (Business Outcomes):
Scenario: Process stores in cold climates
  Given weather data for stores with cold temperatures and high winds
  When calculating feels-like temperature for all stores
  Then cold climate stores should have lower feels-like temperatures
  And wind chill effects should be accounted for
  And results should reflect cold weather conditions
```

**Why This Matters:**
- Tests should verify "what" not "how"
- Business value should be clear
- Implementation can change without breaking tests

---

#### **3. Integration Scenarios** 🔴
```gherkin
Required integration scenarios (compare to Step 1):
✅ Complete step execution with all phases
✅ Process multiple items with varying conditions
✅ Consolidate data from multiple sources
✅ Handle mixed data quality
✅ Save comprehensive outputs
```

**Why This Matters:**
- Tests full step lifecycle
- Catches integration issues
- Verifies context management
- Follows proven patterns

---

#### **4. Domain Language** 🟡
```gherkin
❌ BAD (Technical Jargon):
- "Repository should return DataFrame"
- "Apply transformation function"
- "Validate schema compliance"

✅ GOOD (Domain Language):
- "Weather data should be loaded"
- "Calculate feels-like temperature"
- "Verify data quality"
```

**Why This Matters:**
- Aligns with business terminology
- Easier to understand
- Matches domain model

---

#### **5. Formula/Algorithm Exposure** 🟡
```gherkin
❌ BAD (Exposes Implementation):
Then wind chill formula should be applied
And formula: WC = 13.12 + 0.6215*T - 11.37*V^0.16
And air density correction: V_eff = V * sqrt(rho/rho0)

✅ GOOD (Abstracts Implementation):
Then wind chill effects should be accounted for
And feels-like temperature should reflect wind conditions
```

**Why This Matters:**
- Formulas belong in behavior analysis
- Tests verify outcomes, not calculations
- Implementation details can change

---

### **Comparison Checklist:**

**Against Design Standards:**
- [ ] Background is business-focused (not technical)
- [ ] Scenarios test outcomes (not implementation)
- [ ] Domain language used (not technical jargon)
- [ ] Formulas abstracted (not exposed)
- [ ] Four phases covered (SETUP/APPLY/VALIDATE/PERSIST)

**Against Step 1 (Reference):**
- [ ] Background style matches Step 1
- [ ] Scenario style matches Step 1
- [ ] Integration scenarios included
- [ ] Business language consistent
- [ ] Similar level of abstraction

**Integration Coverage:**
- [ ] Complete step execution scenario
- [ ] Multi-item processing scenario
- [ ] Data consolidation scenario
- [ ] Mixed quality handling scenario
- [ ] Comprehensive output scenario

---

## 📝 Sanity Check Document Template

**Create:** `docs/step_refactorings/step{N}/SANITY_CHECK_PHASE1.md`

```markdown
# Step {N} Phase 1 Sanity Check

**Date:** [DATE]
**Status:** [IN PROGRESS / COMPLETE]

## Checks Performed

### 1. Design Standards Compliance
- [ ] Background: Business-focused
- [ ] Scenarios: Outcome-focused
- [ ] Language: Domain-focused
- [ ] Formulas: Abstracted

### 2. Step 1 Comparison
- [ ] Background style matches
- [ ] Scenario style matches
- [ ] Integration scenarios included
- [ ] Language consistency

### 3. Issues Found

#### Issue 1: [Title]
- **Problem:** [Description]
- **Example:** [Code/Text]
- **Impact:** [Severity]
- **Fix:** [Solution]

### 4. Fixes Applied

#### Fix 1: [Title]
- **Before:** [Original]
- **After:** [Fixed]
- **Improvement:** [Benefit]

### 5. Quality Score

| Criterion | Before | After |
|-----------|--------|-------|
| Background | X/10 | 10/10 |
| Scenarios | X/10 | 10/10 |
| Integration | X/10 | 10/10 |
| Overall | X/10 | 10/10 |

## Recommendation

[PROCEED / FIX REQUIRED / MAJOR REVISION]

## Next Steps

[Actions to take]
```

---

## 🎯 Quality Scoring Guide

### **Background (0-10):**
- **10:** Business context, domain language, no technical details
- **8:** Mostly business, minor technical details
- **6:** Mixed business and technical
- **4:** Mostly technical, some business
- **2:** Pure technical setup
- **0:** No background or completely wrong

### **Scenarios (0-10):**
- **10:** All outcome-focused, business language, proper abstraction
- **8:** Mostly outcome-focused, minor implementation details
- **6:** Mixed outcomes and implementation
- **4:** Mostly implementation-focused
- **2:** Pure implementation details
- **0:** No scenarios or completely wrong

### **Integration (0-10):**
- **10:** 5+ integration scenarios, full coverage
- **8:** 3-4 integration scenarios, good coverage
- **6:** 1-2 integration scenarios, partial coverage
- **4:** Integration mentioned but not tested
- **2:** No integration scenarios
- **0:** No integration consideration

### **Overall Score:**
- **10:** Perfect, proceed immediately
- **8-9:** Good, minor fixes acceptable
- **6-7:** Issues found, fixes required
- **4-5:** Major issues, significant revision needed
- **0-3:** Fundamentally flawed, restart Phase 1

---

## 🚨 Stop Criteria

### **MUST FIX (Score < 8):**
- Background is technical (not business)
- Scenarios expose implementation details
- Missing integration scenarios
- Technical jargon throughout
- Formulas exposed in scenarios

### **SHOULD FIX (Score 8-9):**
- Minor technical details in background
- Some scenarios too implementation-focused
- Integration scenarios incomplete
- Inconsistent language

### **PROCEED (Score 10):**
- Background is business-focused
- Scenarios test outcomes
- Integration scenarios complete
- Domain language throughout
- Matches Step 1 pattern

---

## 🔍 Phase 2 Sanity Check (MANDATORY)

### **What to Check:**

#### **1. Tests Call Real Code** 🔴
```python
❌ BAD (Only Tests Mocks):
@when('processing data')
def process(test_context, mock_repo):
    mock_repo.get_all.return_value = test_data
    test_context['result'] = test_data  # Never calls actual code!

✅ GOOD (Tests Real Step):
@when('processing data')
def process(test_context, step_instance):
    result = step_instance.execute()  # Actually runs step!
    test_context['result'] = result
```

#### **2. Real Instance Used** 🔴
```python
❌ BAD (Mocks the Step):
@pytest.fixture
def step_instance(mocker):
    return mocker.Mock()  # Mocking the code under test!

✅ GOOD (Real Step Instance):
@pytest.fixture
def step_instance(mock_repo, logger):
    return MyStep(
        repo=mock_repo,  # Mock dependencies
        logger=logger
    )  # Real step instance
```

#### **3. Test Organization** 🔴
```python
❌ BAD (Grouped by Decorator):
# All @given together
@given('condition 1')
@given('condition 2')

# All @when together
@when('action 1')
@when('action 2')

✅ GOOD (Grouped by Scenario):
# ============================================================================
# Scenario: Process stores in cold climates
# ============================================================================
@given('weather data for cold stores')
@when('calculating feels-like temperature')
@then('cold stores should have lower temperatures')
```

#### **4. Mock Only Dependencies** 🔴
```python
✅ What to Mock:
- External APIs
- File I/O (repositories)
- Database access
- Network calls

❌ What NOT to Mock:
- The step itself
- The code under test
- Business logic
- Calculations
```

#### **5. Fixtures Provide Real Data** 🟡
```python
❌ BAD (Minimal/Fake Data):
@pytest.fixture
def test_data():
    return pd.DataFrame({'col': [1]})  # Too simple

✅ GOOD (Realistic Data):
@pytest.fixture
def test_data():
    return pd.DataFrame({
        'store_code': ['1001', '1002', '1003'],
        'temperature': [5.0, 30.0, 20.0],
        'humidity': [60, 80, 50],
        'wind_speed': [20, 5, 10]
    })  # Realistic test data
```

### **Checklist:**
- [ ] All tests call `step.execute()` or repository methods
- [ ] Step/repository instance is real (not mocked)
- [ ] Only dependencies are mocked
- [ ] Tests organized by scenario (not decorator)
- [ ] Scenario headers added
- [ ] Fixtures provide realistic data
- [ ] Tests would fail if implementation broken

---

## 🔍 Phase 3 Sanity Check (MANDATORY)

### **What to Check:**

#### **1. Dependency Injection** 🔴
```python
❌ BAD (Hard-coded Dependencies):
class MyStep(Step):
    def __init__(self):
        self.logger = PipelineLogger("Hardcoded")  # BAD
        self.repo = CsvFileRepository("/path")  # BAD

✅ GOOD (Injected Dependencies):
class MyStep(Step):
    def __init__(self, repo, logger, config):
        super().__init__(logger, "My Step", 5)
        self.repo = repo  # Injected
        self.config = config  # Injected
```

#### **2. Four-Phase Pattern** 🔴
```python
✅ Required Methods:
class MyStep(Step):
    def setup(self, context):
        # Load data using repositories
        pass
    
    def apply(self, context):
        # Process/transform data
        pass
    
    def validate(self, context):
        # Validate results
        pass
    
    def persist(self, context):
        # Save outputs using repositories
        pass
```

#### **3. Repository Usage** 🔴
```python
❌ BAD (Direct File I/O):
def setup(self, context):
    df = pd.read_csv('data.csv')  # Direct I/O!

✅ GOOD (Through Repository):
def setup(self, context):
    df = self.repo.get_all()  # Through repository
```

#### **4. No Hard-coded Values** 🔴
```python
❌ BAD (Hard-coded):
def apply(self, context):
    threshold = 0.5  # Hard-coded
    output_path = "output/data.csv"  # Hard-coded

✅ GOOD (Configured):
def apply(self, context):
    threshold = self.config.threshold
    # Output path in repository, not here
```

#### **5. Type Hints** 🟡
```python
✅ GOOD (Full Type Hints):
def setup(self, context: StepContext) -> StepContext:
    data: pd.DataFrame = self.repo.get_all()
    context.data = data
    return context
```

### **Checklist:**
- [ ] All dependencies injected (no hard-coding)
- [ ] Four-phase pattern implemented
- [ ] All I/O through repositories
- [ ] No hard-coded values
- [ ] Type hints on all methods
- [ ] Custom exceptions used
- [ ] Logging before raising exceptions
- [ ] Follows Step 1 pattern

---

## 🔍 Phase 4 Sanity Check (IMPORTANT)

### **What to Check:**

#### **1. Test Coverage** 🔴
```bash
# Run coverage report
pytest tests/step_definitions/test_step5_*.py --cov=src/steps --cov-report=html

# Check coverage
- [ ] Overall coverage > 90%
- [ ] All public methods covered
- [ ] All branches covered
- [ ] Edge cases tested
```

#### **2. Code Standards Compliance** 🔴
```python
# Check against code_design_standards.md
- [ ] Dependency injection: ✅
- [ ] Four-phase pattern: ✅
- [ ] Repository pattern: ✅
- [ ] Type hints: ✅
- [ ] Error handling: ✅
- [ ] Logging: ✅
- [ ] No hard-coded values: ✅
```

#### **3. All Tests Pass** 🔴
```bash
# Run all tests
pytest tests/step_definitions/test_step5_*.py -v

# Verify
- [ ] All tests pass
- [ ] No skipped tests (except CLI tests for repositories)
- [ ] No warnings
- [ ] Execution time reasonable
```

#### **4. Documentation Complete** 🟡
```
- [ ] Behavior analysis document
- [ ] Feature file
- [ ] Test implementation
- [ ] Code implementation
- [ ] Phase completion summaries
- [ ] Sanity check documents
```

### **Checklist:**
- [ ] Test coverage > 90%
- [ ] All tests pass
- [ ] Code standards: 19/19 met
- [ ] Documentation complete
- [ ] No TODO comments
- [ ] No debug code
- [ ] Ready for integration

---

## 🔍 Phase 5 Sanity Check (IMPORTANT)

### **What to Check:**

#### **1. Factory Function** 🔴
```python
✅ GOOD (Composition Root):
def create_my_step(
    target_yyyymm: str,
    target_period: str,
    logger: PipelineLogger
) -> MyStep:
    """Factory function for MyStep."""
    # Create repositories
    repo1 = CsvFileRepository(...)
    repo2 = WeatherDataRepository(...)
    
    # Create config
    config = MyStepConfig(...)
    
    # Create and return step
    return MyStep(
        repo1=repo1,
        repo2=repo2,
        config=config,
        logger=logger,
        step_name="My Step",
        step_number=5
    )
```

#### **2. CLI Script** 🟡
```python
✅ GOOD (CLI Entry Point):
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--yyyymm', required=True)
    parser.add_argument('--period', required=True)
    args = parser.parse_args()
    
    logger = PipelineLogger("MyStep")
    step = create_my_step(args.yyyymm, args.period, logger)
    
    context = StepContext()
    step.execute(context)
```

#### **3. Integration Points** 🔴
```python
# Check integration with:
- [ ] Previous step outputs (inputs exist)
- [ ] Next step inputs (outputs compatible)
- [ ] Pipeline orchestrator
- [ ] Shared repositories
- [ ] Configuration system
```

#### **4. End-to-End Test** 🟡
```bash
# Run step standalone
python src/steps/my_step.py --yyyymm 202506 --period A

# Verify:
- [ ] Runs without errors
- [ ] Produces expected outputs
- [ ] Logs appropriately
- [ ] Completes successfully
```

### **Checklist:**
- [ ] Factory function created
- [ ] CLI script works
- [ ] Integration points verified
- [ ] End-to-end test passes
- [ ] Documentation updated
- [ ] Ready for pipeline integration

---

## 💡 Common Issues & Fixes

### **Issue 1: Technical Background**

**Problem:**
```gherkin
Given a WeatherDataRepository with weather data
And a pipeline logger
```

**Fix:**
```gherkin
Given weather data exists for multiple stores
And a target period "202506A"
```

**Why:** Business stakeholders understand "weather data exists" not "WeatherDataRepository"

---

### **Issue 2: Implementation-Focused Scenarios**

**Problem:**
```gherkin
Scenario: Calculate wind chill formula
  Then wind chill formula should be applied
  And formula: WC = 13.12 + 0.6215*T - 11.37*V^0.16
```

**Fix:**
```gherkin
Scenario: Process stores in cold climates
  Then cold climate stores should have lower feels-like temperatures
  And wind chill effects should be accounted for
```

**Why:** Tests verify outcomes (lower temperatures) not implementation (formula)

---

### **Issue 3: Missing Integration Scenarios**

**Problem:**
- Only unit-level scenarios
- No full step execution
- No data consolidation
- No mixed quality handling

**Fix:**
Add these scenarios:
1. Complete step execution with all phases
2. Process multiple items with varying conditions
3. Consolidate data from multiple sources
4. Handle mixed data quality
5. Save comprehensive outputs

**Why:** Integration scenarios catch issues that unit tests miss

---

### **Issue 4: Technical Jargon**

**Problem:**
```gherkin
Then DataFrame should be returned
And schema should be validated
And transformation function should be applied
```

**Fix:**
```gherkin
Then weather data should be loaded successfully
And data quality should be verified
And temperatures should be calculated
```

**Why:** Domain language is clearer and more maintainable

---

## 🎓 Lessons from Step 5

### **What We Did Wrong:**
1. ❌ Background focused on technical setup (repositories, logger)
2. ❌ Scenarios exposed formulas (wind chill, heat index)
3. ❌ Only 1 integration scenario (should have 5+)
4. ❌ Mixed technical and business language
5. ❌ Didn't compare to Step 1 initially

### **What We Did Right:**
1. ✅ Comprehensive behavior analysis (28 behaviors)
2. ✅ Good test coverage (24 scenarios)
3. ✅ Clear data flow documentation
4. ✅ Performed sanity check before Phase 2
5. ✅ Fixed issues immediately (15 minutes)

### **Impact:**
- **Time to find issues:** 15 minutes (sanity check)
- **Time to fix issues:** 15 minutes (rewrites)
- **Time saved:** 2-3 hours (would have spent in Phase 2)
- **Quality improvement:** 7/10 → 10/10

### **Key Insight:**
> "Sanity checks are not optional. They are mandatory quality gates that prevent expensive rework."

---

## 📊 Sanity Check ROI

### **Time Investment:**
- Phase 1 sanity check: 15-30 minutes
- Phase 2 sanity check: 15-20 minutes
- Phase 3 sanity check: 15-20 minutes
- Phase 4 sanity check: 10-15 minutes
- Phase 5 sanity check: 10-15 minutes
- **Total:** 65-100 minutes (~1.5 hours)

### **Time Saved:**
- Prevents flawed test design: 2-3 hours
- Prevents incorrect test implementation: 1-2 hours
- Prevents code pattern violations: 1-2 hours
- Prevents validation failures: 1 hour
- Prevents integration issues: 1 hour
- **Total:** 6-9 hours

### **ROI:**
- **Investment:** 1.5 hours
- **Savings:** 7.5 hours (average)
- **Return:** 5:1 ratio
- **Quality:** 10/10 vs 7/10
- **Confidence:** High vs Low

---

## ✅ Best Practices Summary

### **DO:**
1. ✅ Perform sanity checks at every phase gate
2. ✅ Compare against design standards
3. ✅ Compare against Step 1 (reference)
4. ✅ Document findings and fixes
5. ✅ Fix issues before proceeding
6. ✅ Aim for 10/10 quality
7. ✅ Use business language
8. ✅ Focus on outcomes
9. ✅ Include integration scenarios
10. ✅ Abstract implementation details

### **DON'T:**
1. ❌ Skip sanity checks ("we'll fix it later")
2. ❌ Proceed with score < 8/10
3. ❌ Expose technical details in scenarios
4. ❌ Use technical jargon
5. ❌ Focus on implementation
6. ❌ Omit integration scenarios
7. ❌ Ignore Step 1 patterns
8. ❌ Rush through checks
9. ❌ Assume LLM output is perfect
10. ❌ Skip documentation

---

## 🎯 Sanity Check Workflow

```
Phase 1 Complete
       ↓
   Sanity Check 1 (Test Design)
       ↓
   Issues? ──YES──→ Fix ──→ Re-check
       ↓ NO
Phase 2 Complete
       ↓
   Sanity Check 2 (Test Implementation)
       ↓
   Issues? ──YES──→ Fix ──→ Re-check
       ↓ NO
Phase 3 Complete
       ↓
   Sanity Check 3 (Code Implementation)
       ↓
   Issues? ──YES──→ Fix ──→ Re-check
       ↓ NO
Phase 4 Complete
       ↓
   Sanity Check 4 (Validation)
       ↓
   Issues? ──YES──→ Fix ──→ Re-check
       ↓ NO
Phase 5 Complete
       ↓
   Sanity Check 5 (Integration)
       ↓
   Issues? ──YES──→ Fix ──→ Re-check
       ↓ NO
   COMPLETE
```

---

## 📝 Checklist for Every Step

**After Phase 1 (Test Design):**
- [ ] Behavior analysis complete
- [ ] Feature file created
- [ ] Sanity check 1 performed
- [ ] Background is business-focused
- [ ] Scenarios are outcome-focused
- [ ] Integration scenarios included
- [ ] Quality score = 10/10
- [ ] SANITY_CHECK_PHASE1.md created
- [ ] Ready for Phase 2

**After Phase 2 (Test Implementation):**
- [ ] Test file created
- [ ] Fixtures implemented
- [ ] Tests implemented
- [ ] Sanity check 2 performed
- [ ] Tests call step.execute()
- [ ] Real instance used (not mocked)
- [ ] Tests organized by scenario
- [ ] SANITY_CHECK_PHASE2.md created
- [ ] Ready for Phase 3

**After Phase 3 (Code Implementation):**
- [ ] Step class implemented
- [ ] Four phases implemented
- [ ] Sanity check 3 performed
- [ ] Dependency injection used
- [ ] All I/O through repositories
- [ ] No hard-coded values
- [ ] SANITY_CHECK_PHASE3.md created
- [ ] Ready for Phase 4

**After Phase 4 (Validation):**
- [ ] All tests pass
- [ ] Coverage > 90%
- [ ] Sanity check 4 performed
- [ ] Code standards: 19/19 met
- [ ] Documentation complete
- [ ] SANITY_CHECK_PHASE4.md created
- [ ] Ready for Phase 5

**After Phase 5 (Integration):**
- [ ] Factory function created
- [ ] CLI script works
- [ ] Sanity check 5 performed
- [ ] Integration points verified
- [ ] End-to-end test passes
- [ ] SANITY_CHECK_PHASE5.md created
- [ ] Ready for production

---

## 🎉 Success Criteria

**Phase 1 is complete when:**
- ✅ Behavior analysis: Comprehensive
- ✅ Feature file: Business-focused
- ✅ Sanity check: Performed
- ✅ Issues: Fixed
- ✅ Quality score: 10/10
- ✅ Documentation: Complete
- ✅ Ready: For Phase 2

---

**Status:** ✅ **MANDATORY PROCESS**  
**Adoption:** Immediate (all future steps)  
**Value:** High (5:1 ROI)  
**Quality Impact:** Critical (7/10 → 10/10)

---

*Sanity checks are not optional. They are the difference between good and perfect.* 🎯
