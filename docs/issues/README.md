# Project-Wide Issues

**Date:** 2025-10-30  
**Purpose:** Document project-wide issues that affect multiple steps or the entire pipeline  
**Note:** Step-specific issues are in `step_refactorings/step{N}/issues/`

---

## 📋 Overview

This directory contains documentation for issues that affect:
- Multiple pipeline steps
- The entire project structure
- Cross-cutting concerns (testing, file naming, etc.)
- Project-wide standards and conventions

**For step-specific issues (e.g., bugs in Step 5 or Step 6), see:**
- `docs/step_refactorings/step5/issues/`
- `docs/step_refactorings/step6/issues/`
- `docs/step_refactorings/step13/issues/`

---

## ✅ Issues Resolved

### 1. Test Infrastructure Issues
**Files:** `FIXES_APPLIED_SUMMARY.md`, `CRITICAL_TEST_AUDIT_ALL_STEPS.md`

**Problems Fixed:**
- ✅ **PROJECT_ROOT Path Issues** - 32 isolated test files had wrong path
  - Changed from `parents[1]` to `parents[2]`
  - All isolated tests can now find correct project root
  
- ✅ **Dual Output Pattern Tests** - 5 test files had incorrect expectations
  - Updated to validate new dual output pattern (timestamped + symlinks)
  - Tests now correctly validate: timestamped file + period symlink + generic symlink

- ⚠️ **Mock Tests Giving False Positives** - Steps 1-7 had mock tests
  - Identified that tests validate pattern theory, not actual implementation
  - Step 6 mock test disabled (has real tests)
  - Other steps need real tests created

**Impact:** Improved test reliability and accuracy

**How to Verify:**
```bash
# Run isolated tests
pytest tests/step*/isolated/ -v

# Check dual output pattern
pytest tests/step24/test_step24_dual_output.py -v
```

---

### 2. Filename and Period Handling
**Files:** `FILENAME_STANDARD_FIX.md`, `FIX_ALL_FILENAME_REFERENCES.md`, `PERIOD_GENERATION_ISSUE.md`, `FIX_COMPLETE_PERIOD_GENERATION.md`

**Problems Fixed:**
- ✅ **Filename Standard Inconsistencies** - Different steps used different naming conventions
  - Standardized to: `{step_name}_{yyyymm}{period}.csv`
  - Added symlinks for backward compatibility
  
- ✅ **Period Generation Issues** - Incorrect period calculation logic
  - Fixed period A/B generation
  - Corrected date range calculations
  
- ✅ **Filename References** - Hardcoded filenames throughout codebase
  - Updated to use dynamic filename generation
  - Consistent pattern across all steps

**Impact:** Consistent file naming, correct period handling

**How to Verify:**
```bash
# Check output files follow standard
ls -1 output/*_202510A.csv

# Check symlinks exist
ls -1 output/*.csv | grep -v "_202"
```

---

### 3. Design Changes
**Files:** `SINGLE_PERIOD_DESIGN_CHANGE.md`

**Change Made:**
- ✅ **Single Period Design** - Changed from multi-period to single-period execution
  - Each pipeline run processes one period (e.g., 202510A)
  - Simplified architecture and data flow
  - Clearer separation of concerns

**Rationale:**
- Easier to understand and maintain
- Better error handling per period
- Clearer data lineage
- Simpler testing

**Impact:** Simplified pipeline architecture

---

### 4. Data and Integration Issues
**Files:** `CRITICAL_ISSUE_CLUSTERING_DATA.md`

**Problem Fixed:**
- ✅ **Clustering Data Quality Issues** - Data inconsistencies affecting clustering
  - Identified data quality problems
  - Implemented validation checks
  - Added error handling

**Impact:** Improved data quality and clustering reliability

---

### 5. Merge and Integration
**Files:** `AIS130_MERGE_INVESTIGATION.md`

**Investigation:**
- ✅ **AIS-130 Merge Analysis** - Investigated merge conflicts and integration issues
  - Documented merge strategy
  - Identified conflicts
  - Resolved integration issues

**Impact:** Successful branch merges

---

## 📊 Issue Summary

### By Category:

**Testing (3 issues):**
- PROJECT_ROOT path corrections
- Dual output pattern validation
- Mock test identification

**File Naming (4 issues):**
- Filename standardization
- Period generation fixes
- Reference updates
- Backward compatibility

**Architecture (1 issue):**
- Single period design change

**Data Quality (1 issue):**
- Clustering data validation

**Integration (1 issue):**
- Merge investigation and resolution

### By Status (for Steps 4-6):

- ✅ **Resolved:** All issues resolved for this project
- ⚠️ **Outstanding for other steps:** Mock tests in Steps 1-3, 7 (outside project scope)
- ❌ **Outstanding for Steps 4-6:** 0 issues

---

## 🔍 How to Verify Fixes

### Test Infrastructure:
```bash
# Run all tests
pytest tests/ -v

# Run isolated tests specifically
pytest tests/step*/isolated/ -v

# Check for mock tests
grep -r "create mock output" tests/
```

### Filename Standards:
```bash
# Check output files follow pattern
ls -1 output/ | grep -E "_[0-9]{6}[AB]\.csv$"

# Check symlinks exist
find output/ -type l -name "*.csv"

# Verify symlink targets
ls -lh output/*.csv | grep -v "_202"
```

### Period Generation:
```bash
# Test period generation
python3 -c "
from datetime import datetime
# Add your period generation test code
"
```

### Data Quality:
```bash
# Run data validation
pytest tests/step6/test_data_quality.py -v

# Check clustering results
python3 -c "
import pandas as pd
df = pd.read_csv('output/clustering_results_sales_quantity_202510A.csv')
print(df.describe())
print(df['cluster_id'].value_counts())
"
```

---

## ⚠️ Outstanding Items

### Mock Tests (Not Applicable to This Project):
**Steps 1-3, 7:** Have mock tests that give false positives

**Status for This Project (Steps 4-6):**
- ✅ **Step 4:** Merged into Step 5 (resolved)
- ✅ **Step 5:** Has 32 BDD tests + 3 integration tests (comprehensive coverage)
- ✅ **Step 6:** Has 53 BDD tests (comprehensive coverage)
- ✅ **All issues resolved for Steps 4-6**

**Note:** Steps 1-3 and 7 are outside the scope of this refactoring project (Steps 4-6). If those steps are refactored in the future, they will need real tests to replace mock tests.

---

## 📚 Related Documentation

### Step-Specific Issues:
- **Step 5:** `../step_refactorings/step5/issues/` (if exists)
- **Step 6:** `../step_refactorings/step6/issues/` (step-specific bugs and fixes)
- **Step 13:** `../step_refactorings/step13/issues/` (cluster ID fixes, duplicate data)

### Process Documentation:
- **Testing Guide:** `../process_guides/REFACTORING_PROCESS_GUIDE.md`
- **Standards:** `../process_guides/code_design_standards.md`
- **Pre-Commit:** `../process_guides/PRE_COMMIT_CHECKLIST.md`

---

## 📝 Documentation

**All detailed issue documents have been consolidated into this README.**

This README contains summaries of all resolved issues:
- Test infrastructure fixes
- Filename standardization
- Period generation fixes
- Architecture changes
- Data quality improvements
- Integration resolutions

**Historical detail files were removed to keep the repository clean.**

---

## 🎯 Best Practices

### When to Create Project-Wide Issue:
✅ **Create here if:**
- Affects multiple steps (3+)
- Affects project structure or standards
- Cross-cutting concern (testing, naming, etc.)
- Infrastructure or tooling issue

❌ **Don't create here if:**
- Specific to one step → Use `step_refactorings/step{N}/issues/`
- Specific to one feature → Document in that feature's directory
- Temporary development note → Use `transient/`

### Issue Documentation Template:
```markdown
# [Issue Title]

**Date:** YYYY-MM-DD
**Status:** ✅ Resolved / ⚠️ Partial / ❌ Outstanding
**Affects:** Steps X, Y, Z / All Steps / Project Structure

## Problem
[Clear description of the issue]

## Root Cause
[Why it happened]

## Solution
[How it was fixed]

## Verification
[How to verify the fix works]

## Impact
[What changed as a result]
```

---

## 🚀 Future Improvements

### Recommended:
1. **Create real integration tests** for Steps 1-5, 7
2. **Automate filename validation** in CI/CD
3. **Add data quality checks** to pipeline
4. **Document testing standards** more clearly

### Nice to Have:
1. Automated issue tracking integration
2. Issue impact analysis tools
3. Regression test suite for fixed issues

---

**Last Updated:** 2025-10-30  
**Total Issues Documented:** 9 (all resolved for Steps 4-6)  
**Status:** ✅ All issues resolved for this project (Steps 4-6)  
**Files:** 1 (README.md only - detailed files removed for cleanliness)
