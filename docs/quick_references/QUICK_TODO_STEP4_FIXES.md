# Step 4 Fixes - Quick To-Do List

**Date:** 2025-10-10  
**Status:** 🔴 BLOCKED - Must fix before proceeding  
**Branch:** `ais-130-refactoring-step-4`

---

## ✅ What to Do Right Now

### 1. Convert Step 4 to Repository (2-3 hours)

```bash
# Create the repository
touch src/repositories/weather_data_repository.py
```

**Move this logic from step to repository:**
- All download logic (`_download_weather_for_store`, etc.)
- All file saving logic (`_save_weather_file`, etc.)
- All API interaction logic
- Keep data formatting in repository

**What stays in repository:**
- `fetch_weather_data()` - Download from API
- `save_weather_data()` - Save to files
- `get_elevation()` - Get altitude data
- `format_weather_data()` - Format for consumption

### 2. Delete Step 4 Step Files (10 minutes)

```bash
# These should not exist as steps
rm src/steps/weather_data_download_step.py
rm src/step4_weather_data_download_refactored.py

# Move factory to utils
mkdir -p src/utils
mv src/steps/weather_data_factory.py src/utils/
```

### 3. Fix Tests to Test Repository (1 hour)

**Update:** `tests/step_definitions/test_step4_weather_data.py`

Change from testing a step to testing a repository:
```python
# Old (testing step)
@when('downloading weather data')
def download(test_context, step_instance):
    result = step_instance.execute()

# New (testing repository)
@when('downloading weather data')
def download(test_context, weather_repo):
    result = weather_repo.fetch_weather_data(store_code='1001', period='202506A')
    test_context['result'] = result
```

### 4. Start Step 5 Refactoring (8-10 hours)

**In Step 5 setup phase:**
```python
def setup(self, context: StepContext) -> None:
    # Use weather repository to get data
    weather_data = self.weather_repo.fetch_weather_data(...)
    context['weather_data'] = weather_data
    
    # Load other data...
```

**In Step 5 apply phase:**
```python
def apply(self, context: StepContext) -> None:
    # Compute feels-like temperature
    weather_data = context['weather_data']
    feels_like = self._compute_feels_like_temperature(weather_data)
    context['processed_weather'] = feels_like
```

---

## 📋 Detailed Checklist

### Priority 1: Architecture Fix (CRITICAL)
- [ ] Create `src/repositories/weather_data_repository.py`
- [ ] Move download logic from step to repository
- [ ] Move file operations to repository
- [ ] Add proper error handling
- [ ] Test repository methods work

### Priority 2: Cleanup (HIGH)
- [ ] Delete `src/steps/weather_data_download_step.py`
- [ ] Delete `src/step4_weather_data_download_refactored.py`
- [ ] Create `src/utils/` folder
- [ ] Move `weather_data_factory.py` to `src/utils/`
- [ ] Update all imports

### Priority 3: Test Fixes (HIGH)
- [ ] Update tests to test repository (not step)
- [ ] Ensure tests call actual repository methods
- [ ] Reorganize tests by scenario
- [ ] Add comment headers for each scenario
- [ ] Verify all tests pass

### Priority 4: Step 5 Refactoring (HIGH)
- [ ] Analyze Step 5 behaviors (Phase 1)
- [ ] Design Step 5 tests (Phase 2)
- [ ] Implement Step 5 using weather repository (Phase 3)
- [ ] Validate Step 5 (Phase 4)
- [ ] Integrate Step 5 (Phase 5)

### Priority 5: Documentation (MEDIUM)
- [ ] Update `REFACTORING_PROCESS_GUIDE.md` ✅ DONE
- [ ] Create `STEP4_CORRECTIONS.md`
- [ ] Update `STEP4_FINAL_SUMMARY.md`
- [ ] Document Step 4→5 approach
- [ ] Update `REFACTORING_PROJECT_MAP.md`

---

## 🎯 Success Criteria

### Step 4 (Repository):
- ✅ `WeatherDataRepository` exists in `src/repositories/`
- ✅ All download logic is in repository
- ✅ Tests test repository methods
- ✅ No step file exists for Step 4
- ✅ Factory moved to `src/utils/`

### Step 5 (Actual Step):
- ✅ Step 5 uses `WeatherDataRepository` in setup
- ✅ Step 5 computes feels-like temperature in apply
- ✅ Tests call `execute()` method
- ✅ Tests organized by scenario
- ✅ All tests pass

### Process Guide:
- ✅ Decision tree for step vs repository ✅ DONE
- ✅ Test quality requirements ✅ DONE
- ✅ File organization standards ✅ DONE
- ✅ LLM prompting best practices ✅ DONE

---

## 💡 Key Commands

```bash
# Create repository
touch src/repositories/weather_data_repository.py

# Create utils folder
mkdir -p src/utils

# Move factory
mv src/steps/weather_data_factory.py src/utils/

# Delete step files
rm src/steps/weather_data_download_step.py
rm src/step4_weather_data_download_refactored.py

# Run tests
pytest tests/step_definitions/test_step4_weather_data.py -v

# Check imports
grep -r "weather_data_download_step" src/
grep -r "weather_data_factory" src/
```

---

## 📞 Questions to Ask Windsurf

### For Repository Creation:
```
Please create a WeatherDataRepository in src/repositories/weather_data_repository.py

Move all download logic from src/steps/weather_data_download_step.py to this repository.

The repository should have these methods:
1. fetch_weather_data(store_code, period) - Download from API
2. save_weather_data(data, output_path) - Save to files
3. get_elevation(latitude, longitude) - Get altitude
4. format_weather_data(raw_data) - Format for consumption

Reference: src/repositories/csv_repository.py for structure
```

### For Test Updates:
```
Please update tests/step_definitions/test_step4_weather_data.py

Change from testing a step to testing a repository.

Requirements:
1. Test repository methods directly (not execute())
2. Organize by scenario (not by decorator)
3. Add comment headers for each scenario
4. Mock only external APIs
5. Test actual repository behavior

Show me the plan first before implementing.
```

### For Step 5 Refactoring:
```
Please refactor Step 5 (Temperature Calculation) following the 5-phase methodology.

Step 5 should:
1. Use WeatherDataRepository in setup phase to get weather data
2. Compute feels-like temperature in apply phase
3. Validate results in validate phase
4. Save processed data in persist phase

Reference:
- /docs/REFACTORING_PROCESS_GUIDE.md
- /docs/code_design_standards.md
- src/steps/api_download_merge_step.py (example)

Show me the plan first.
```

---

## ⏱️ Time Estimates

- **Repository Creation:** 2-3 hours
- **Cleanup & Organization:** 1 hour
- **Test Fixes:** 1-2 hours
- **Step 5 Refactoring:** 8-10 hours
- **Documentation:** 1-2 hours

**Total:** ~15-18 hours

---

## 🚀 Next Steps After This

1. **Review with Vitor** - Show corrected approach
2. **Proceed to Step 6** - Apply learnings
3. **Update Executive Summary** - Include corrections
4. **Create Test Design Standards** - Document test patterns

---

**Remember:** Step 4 should have been a repository from the start. This is a valuable lesson for future refactoring!
