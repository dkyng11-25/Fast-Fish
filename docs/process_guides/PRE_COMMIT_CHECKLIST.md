# Pre-Commit Checklist - Before Merging to Main

**Date Created:** 2025-10-30  
**Purpose:** Ensure clean, production-ready state before committing to main  
**Status:** 🚨 MANDATORY - DO NOT SKIP

**⚠️ IMPORTANT: This is DIFFERENT from working branch cleanup!**

---

## 🎯 Overview

**Two Types of Cleanup:**

### Working Branch Cleanup (Phase 6A)
- Done during development
- Organize files and remove duplicates
- Keep detailed phase docs and archives
- See `REFACTORING_PROCESS_GUIDE.md` Phase 6A

### Pre-Main Cleanup (Phase 6B) ⭐ **THIS DOCUMENT**
- Done before merging to main
- Delete archives and detailed docs
- Consolidate into READMEs only
- Professional, clean main branch

---

This checklist ensures that:
1. All temporary documentation is removed
2. All archive directories are deleted
3. Detailed phase docs are consolidated
4. Code is production-ready
5. Tests pass
6. Documentation is complete and accurate
7. No debugging artifacts remain

---

## ✅ Phase 1: Delete Transient Documentation

### 1.1 Delete ALL transient/ Directory

**🚨 CRITICAL: Everything in `docs/transient/` must be deleted!**

```bash
# Verify what will be deleted
ls -la docs/transient/

# Delete the entire transient directory
rm -rf docs/transient/

# Verify deletion
ls docs/transient/  # Should error: No such file or directory
```

**What gets deleted:**
- ✅ `docs/transient/status/` - All status updates (93 files)
- ✅ `docs/transient/testing/` - All test results (52 files)
- ✅ `docs/transient/compliance/` - All compliance checks (6 files)
- ✅ `docs/transient/cleanup/` - All cleanup logs
- ✅ `docs/transient/*.md` - Any other temporary docs

**Why delete?**
- These are development artifacts
- Only relevant during refactoring
- Clutters the repository
- No value after merge

---

## ✅ Phase 2: Clean Root Directory

### 2.1 Remove Temporary Root Files

**Check for temporary files in root:**

```bash
# List all markdown files in root
ls -1 *.md

# Common temporary files to remove:
rm -f CLEANUP_*.md
rm -f PROCESS_GUIDE_ENFORCEMENT.md
rm -f DOCUMENTATION_CLEANUP_*.md
rm -f PHASE6_*.md
rm -f *_SUMMARY_FOR_USER.md
```

**Keep only essential root files:**
- ✅ `README.md` - Project overview
- ✅ `REFACTORING_PROJECT_MAP.md` - Project status
- ✅ Other permanent documentation

---

## ✅ Phase 3: Documentation Consolidation & Cleanup

### 3.1 Consolidate Step Refactoring Documentation

**⚠️ ONLY applies to: `docs/step_refactorings/step{N}/` directories**

**DO NOT touch:**
- ❌ `docs/process_guides/` - Leave as-is
- ❌ `docs/issues/` - Leave as-is (project-wide issues)
- ❌ `docs/reviews/` - Leave as-is
- ❌ `tests/` - NEVER auto-delete (see Phase 4)
- ❌ Any other directories

**Required structure for EACH refactored step:**
```
docs/step_refactorings/step{N}/
├── README.md          ⭐ REQUIRED - Comprehensive guide
├── LESSONS_LEARNED.md (optional but recommended)
├── testing/
│   └── README.md      ⭐ REQUIRED - Actual test status
└── issues/            (if step-specific issues exist)
    └── [issue files]
```

**README.md must include:**
- Overview of what was refactored
- Architecture and design patterns
- Testing status (ACTUAL test counts, not aspirational)
- Validation results (head-to-head comparison)
- Key decisions and rationale
- Lessons learned
- How to use and verify

**What to DELETE from `docs/step_refactorings/step{N}/` ONLY:**
- ❌ `docs/step_refactorings/step{N}/archive/` subdirectory (if it exists)
- ❌ `docs/step_refactorings/step{N}/PHASE*.md` files (detailed phase documents)
- ❌ `docs/step_refactorings/step{N}/COMPLIANCE_*.md` files
- ❌ `docs/step_refactorings/step{N}/testing/*.md` (keep ONLY README.md)

**⚠️ IMPORTANT - Two different "testing" locations:**
- ✅ `docs/step_refactorings/step{N}/testing/` - Documentation about tests (clean up here)
- ❌ `tests/` - Actual test code (NEVER auto-delete - see Phase 4)

**What to KEEP in `docs/step_refactorings/step{N}/`:**
- ✅ `docs/step_refactorings/step{N}/README.md` (comprehensive guide)
- ✅ `docs/step_refactorings/step{N}/LESSONS_LEARNED.md` (if exists)
- ✅ `docs/step_refactorings/step{N}/testing/README.md` (actual test status)
- ✅ `docs/step_refactorings/step{N}/issues/` subdirectory (step-specific issues)

**⚠️ CRITICAL - Test Files in `tests/` directory:**
- **NEVER automatically delete test files**
- **ALWAYS verify tests are redundant before deleting**
- **ALWAYS run tests to confirm they pass**
- **Document why tests were deleted if you do**
- **Get team approval before deleting any tests**

**Example - What was cleaned in this project:**
```
DELETED from docs/step_refactorings/ ONLY:
- docs/step_refactorings/step4/archive/ (7 files)
- docs/step_refactorings/step5/archive/ (~60 files)
- docs/step_refactorings/step6/archive/ (~90 files)
- docs/step_refactorings/step5/testing/STEP5_*.md (3 files, kept README.md)
- docs/step_refactorings/step6/testing/PHASE*.md (11 files, kept README.md)
- docs/step_refactorings/step6/testing/TEST_*.md (kept README.md)

DELETED from tests/ (after manual verification):
- tests/step06/isolated/ (10 redundant tests - verified with BDD coverage)

KEPT (unchanged):
- docs/step_refactorings/step{N}/README.md
- docs/step_refactorings/step{N}/LESSONS_LEARNED.md
- docs/step_refactorings/step{N}/testing/README.md
- docs/step_refactorings/step{N}/issues/
- docs/process_guides/ (all files)
- docs/issues/ (all files)
- docs/reviews/ (all files)
- tests/ (all other test files)
```

---

### 3.2 Verify Documentation Structure

**Check that permanent docs are in correct locations:**

```bash
# Step-specific refactoring docs
ls docs/step_refactorings/step5/
ls docs/step_refactorings/step6/
ls docs/step_refactorings/step13/

# Process guides
ls docs/process_guides/

# Issues
ls docs/issues/

# Reviews
ls docs/reviews/
```

**Verify structure:**
```
docs/
├── step_refactorings/
│   ├── step5/
│   │   ├── *.md (refactoring decisions)
│   │   ├── testing/ (test design)
│   │   └── issues/ (step-specific issues)
│   ├── step6/
│   └── step13/
│
├── process_guides/
│   ├── REFACTORING_PROCESS_GUIDE.md
│   └── [other guides]
│
├── issues/
│   └── [project-wide issues only]
│
└── reviews/
    └── [management reviews]
```

### 3.2 Update INDEX.md

**Verify `docs/INDEX.md` is accurate:**

```bash
# Check file counts
find docs/step_refactorings/step5 -name "*.md" | wc -l
find docs/step_refactorings/step6 -name "*.md" | wc -l

# Update INDEX.md with correct counts
# Remove references to transient/ directory
```

---

## ✅ Phase 4: Code Quality Checks

### 4.1 Run All Tests

```bash
# Run full test suite
pytest tests/ -v

# Verify all tests pass
# Fix any failing tests before committing

# Count integration tests
pytest tests/integration/ --co -q | grep "test_" | wc -l
```

**Update documentation to match:**
- Check `step{N}/README.md` test counts
- Check `step{N}/testing/README.md` test counts
- Check `docs/INDEX.md` test counts
- **NEVER inflate numbers - show actual reality**

---

### 4.2 Identify Redundant Tests (Manual Review Required)

**⚠️ NEVER automatically delete tests!**

**Process for identifying redundant tests:**

1. **Compare test coverage:**
   ```bash
   # List all test files
   find tests/ -name "test_*.py" -type f
   
   # Check for isolated test directories
   find tests/ -name "isolated" -type d
   ```

2. **Manual review required:**
   - Read what each test does
   - Compare with BDD test coverage
   - Verify tests are truly redundant
   - Document reasoning

3. **If tests are redundant:**
   - Run tests to confirm they pass
   - Document why they're redundant
   - Get team approval before deleting
   - Delete and update documentation

**Example from this project:**
- `tests/step06/isolated/` had 10 tests
- All scenarios covered by 53 BDD tests
- Verified redundancy manually
- Deleted after confirmation

---

### 4.3 Run Complete Test Suite

```bash
# Run all tests
pytest tests/ -v

# Check for failures
# If any tests fail, DO NOT COMMIT

# Verify test counts match documentation
pytest tests/ --co -q | grep "test_" | wc -l
```

**Expected results (update for your project):**
- Step 5: 35 tests (32 BDD + 3 integration)
- Step 6: 53 BDD tests
- All tests passing (100%)

---

### 4.4 Remove Debug Code

**Search for and remove:**
- ❌ `print()` statements used for debugging
- ❌ `import pdb; pdb.set_trace()`
- ❌ Commented-out code blocks
- ❌ TODO comments that should be done
- ❌ Temporary test files

```bash
# Search for debug statements
grep -r "print(" src/
grep -r "pdb.set_trace" src/
grep -r "TODO" src/
```

### 4.3 Verify Code Standards

**Check compliance with:**
- ✅ PEP 8 style guide
- ✅ Type hints present
- ✅ Docstrings complete
- ✅ No unused imports
- ✅ No hardcoded paths

---

## ✅ Phase 5: Git Cleanup

### 5.1 Review Git Status

```bash
# Check what will be committed
git status

# Review changes
git diff

# Check for untracked files
git ls-files --others --exclude-standard
```

### 5.2 Remove Unnecessary Files from Git

```bash
# Remove files that shouldn't be tracked
git rm --cached <file>

# Update .gitignore if needed
```

### 5.3 Verify .gitignore

**Ensure these are ignored:**
```
# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/

# IDE
.vscode/
.idea/

# Data
data/
output/
*.csv
*.xlsx

# Temporary
*.tmp
*.log
.DS_Store
```

---

## ✅ Phase 6: Final Documentation Review

### 6.1 Update Key Documents

**Update these files with final information:**

1. **`README.md`**
   - Current project status
   - How to run the pipeline
   - Dependencies

2. **`REFACTORING_PROJECT_MAP.md`**
   - Mark completed steps as ✅
   - Update status
   - Remove in-progress notes

3. **`docs/INDEX.md`**
   - Remove transient/ section
   - Update file counts
   - Verify all links work

### 6.2 Verify Process Guide

**Check `docs/process_guides/REFACTORING_PROCESS_GUIDE.md`:**
- ✅ All lessons learned incorporated
- ✅ Examples are accurate
- ✅ No references to deleted files
- ✅ Decision tree is correct

---

## ✅ Phase 7: Final Verification

### 7.1 Pre-Commit Checklist

**Run through this final checklist:**

```
[ ] All tests pass (pytest)
[ ] docs/transient/ directory deleted
[ ] Root directory cleaned of temporary files
[ ] No debug code in src/
[ ] No TODO comments unresolved
[ ] Git status reviewed
[ ] .gitignore updated
[ ] README.md updated
[ ] REFACTORING_PROJECT_MAP.md updated
[ ] docs/INDEX.md updated (no transient/ references)
[ ] All documentation links verified
[ ] Code follows standards
[ ] No hardcoded paths
[ ] No sensitive data in code
```

### 7.2 Run Final Tests

```bash
# Full test suite
pytest tests/ -v --cov=src

# Verify coverage
# Fix any issues
```

### 7.3 Create Clean Commit

```bash
# Stage changes
git add .

# Create meaningful commit message
git commit -m "feat: Complete Step X refactoring

- Refactored Step X to use repository pattern
- Added comprehensive test suite
- Updated documentation
- Removed all temporary artifacts

Closes #XXX"

# Push to main
git push origin main
```

---

## 📋 Quick Reference Commands

### Delete Transient Documentation
```bash
rm -rf docs/transient/
```

### Clean Root Directory
```bash
rm -f CLEANUP_*.md PROCESS_GUIDE_*.md DOCUMENTATION_*.md PHASE6_*.md
```

### Verify Tests
```bash
pytest tests/ -v
```

### Check Git Status
```bash
git status
git diff
```

### Final Commit
```bash
git add .
git commit -m "feat: [description]"
git push origin main
```

---

## 🚨 Common Mistakes to Avoid

### ❌ DON'T:
1. **Commit transient/ directory**
   - It's temporary by definition
   - Clutters the repository
   - No value after merge

2. **Leave debug code**
   - print() statements
   - pdb breakpoints
   - Commented-out blocks

3. **Automatically delete test files**
   - Always manually review first
   - Verify tests are truly redundant
   - Document why tests were deleted
   - Get team approval

4. **Commit archive directories**
   - Archive directories pollute main
   - Detailed phase docs should be deleted
   - Keep only comprehensive READMEs

5. **Inflate test counts in documentation**
   - Show actual test counts
   - Run tests to verify numbers
   - Update docs to match reality

3. **Commit with failing tests**
   - Always run full test suite
   - Fix all failures first

4. **Skip documentation updates**
   - README.md must be current
   - INDEX.md must be accurate
   - No broken links

5. **Commit large data files**
   - Check .gitignore
   - Remove from staging if needed

---

## ✅ Success Criteria

**Before committing, verify:**

1. ✅ **Clean Repository**
   - No transient/ directory
   - No temporary files in root
   - No debug code

2. ✅ **Working Code**
   - All tests pass
   - No errors or warnings
   - Code follows standards

3. ✅ **Complete Documentation**
   - README.md updated
   - INDEX.md accurate
   - Process guide current

4. ✅ **Clean Git State**
   - Only production files staged
   - Meaningful commit message
   - No sensitive data

---

## 📝 Post-Commit Actions

**After successful commit:**

1. ✅ Verify CI/CD pipeline passes
2. ✅ Tag release if appropriate
3. ✅ Update project board
4. ✅ Notify team
5. ✅ Archive any external notes

---

## 🎯 Remember

> **The transient/ directory is called "transient" for a reason.**
> 
> **It's temporary. It's ephemeral. It's meant to be deleted.**
> 
> **Don't commit it to main!**

---

**Last Updated:** 2025-10-30  
**Next Review:** Before each merge to main  
**Owner:** Development Team
