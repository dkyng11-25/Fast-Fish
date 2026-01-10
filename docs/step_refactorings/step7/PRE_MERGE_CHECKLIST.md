# Pre-Merge Checklist: AIS-163 → Main
## Safe Merge Strategy with Backups

**Date:** 2025-11-10  
**Branch:** `ais-163-refactor-step-7` → `main`  
**Status:** 🚀 READY TO START

---

## ⚠️ Critical Safety Principles

1. **Never merge without backups**
2. **Test everything before merging**
3. **One step at a time**
4. **Verify after each step**
5. **Have rollback plan ready**

---

## Step 1: Pre-Merge Backups ⚠️ CRITICAL

### 1.1 Create Local Backup Branch
```bash
# Create backup of current work
git checkout ais-163-refactor-step-7
git branch ais-163-refactor-step-7-backup-20251110
git push origin ais-163-refactor-step-7-backup-20251110

# Verify backup exists
git branch -a | grep backup
```

**Expected Output:**
```
  ais-163-refactor-step-7-backup-20251110
  remotes/origin/ais-163-refactor-step-7-backup-20251110
```

**Status:** [ ] Complete

---

### 1.2 Backup Main Branch
```bash
# Create backup of main before merge
git checkout main
git pull origin main
git branch main-backup-pre-ais163-20251110
git push origin main-backup-pre-ais163-20251110

# Verify backup exists
git branch -a | grep main-backup
```

**Expected Output:**
```
  main-backup-pre-ais163-20251110
  remotes/origin/main-backup-pre-ais163-20251110
```

**Status:** [ ] Complete

---

### 1.3 Tag Current State
```bash
# Tag the current state for easy recovery
git checkout main
git tag -a pre-ais163-merge-20251110 -m "Main branch state before AIS-163 merge"
git push origin pre-ais163-merge-20251110

git checkout ais-163-refactor-step-7
git tag -a ais163-ready-for-merge-20251110 -m "AIS-163 branch ready for merge"
git push origin ais163-ready-for-merge-20251110

# Verify tags exist
git tag | grep 20251110
```

**Expected Output:**
```
ais163-ready-for-merge-20251110
pre-ais163-merge-20251110
```

**Status:** [ ] Complete

---

## Step 2: Pre-Merge Validation

### 2.1 Verify Working Branch is Clean
```bash
git checkout ais-163-refactor-step-7
git status
```

**Expected Output:**
```
On branch ais-163-refactor-step-7
Your branch is up to date with 'origin/ais-163-refactor-step-7'.

nothing to commit, working tree clean
```

**Status:** [ ] Complete

---

### 2.2 Run All Tests
```bash
# Run Step 7 tests
python -m pytest tests/step_definitions/test_step7_missing_category_rule.py -v

# Expected: 34/34 passing
```

**Expected Output:**
```
============================= 34 passed in XX.XXs ==============================
```

**Status:** [ ] Complete

---

### 2.3 Verify Output Format
```bash
# Check that output files exist and are valid
ls -lh output/rule7_missing_spu_sellthrough_results_*.csv | head -3

# Verify column count (should be 16)
head -1 output/rule7_missing_spu_sellthrough_results_202510A*.csv | tr ',' '\n' | wc -l
```

**Expected Output:**
```
16
```

**Status:** [ ] Complete

---

### 2.4 Check for Uncommitted Changes
```bash
git status --short
```

**Expected Output:**
```
(empty - no output)
```

**Status:** [ ] Complete

---

## Step 3: Update from Main

### 3.1 Fetch Latest Main
```bash
git checkout main
git fetch origin main
git pull origin main

# Check what's new in main
git log --oneline -10
```

**Status:** [ ] Complete

---

### 3.2 Check for Conflicts (Dry Run)
```bash
# Switch back to feature branch
git checkout ais-163-refactor-step-7

# Simulate merge to see conflicts
git merge --no-commit --no-ff main

# If conflicts, note them here:
# Conflicts:
# - 
# - 

# Abort the dry run
git merge --abort
```

**Conflicts Found:** [ ] None / [ ] Yes (list below)

**Status:** [ ] Complete

---

## Step 4: Resolve Conflicts (If Any)

### 4.1 Create Conflict Resolution Branch
```bash
# Only if conflicts found in Step 3.2
git checkout ais-163-refactor-step-7
git checkout -b ais-163-merge-conflicts-resolution
git merge main

# Resolve conflicts manually
# Then:
git add <resolved-files>
git commit -m "resolve: Merge conflicts from main into AIS-163"
```

**Status:** [ ] N/A / [ ] Complete

---

### 4.2 Test After Conflict Resolution
```bash
# Run tests again after resolving conflicts
python -m pytest tests/step_definitions/test_step7_missing_category_rule.py -v

# Expected: 34/34 passing
```

**Status:** [ ] N/A / [ ] Complete

---

## Step 5: Create Pull Request

### 5.1 Push Final Changes
```bash
git checkout ais-163-refactor-step-7
git push origin ais-163-refactor-step-7
```

**Status:** [ ] Complete

---

### 5.2 Create PR on GitHub
1. Go to: https://github.com/AIsle8-ai/ProducMixClustering_spu_clustering_rules_visualization-copy
2. Click "Pull Requests" → "New Pull Request"
3. Base: `main` ← Compare: `ais-163-refactor-step-7`
4. Title: `AIS-163: Step 7 Refactoring - Clean Architecture + Analysis Documentation`
5. Description: (see template below)

**PR Description Template:**
```markdown
## Summary
Refactored Step 7 (Missing Category Rule) with clean architecture and comprehensive analysis of legacy filtering issues.

## Changes
- ✅ Refactored Step 7 into modular components (CUPID compliant)
- ✅ All 34 tests passing
- ✅ Output format 100% compatible with legacy
- ✅ Comprehensive analysis documentation (122 files)
- ✅ Identified filtering dysfunction (profit vs sell-through)

## Testing
- 34/34 tests passing
- Output validated against legacy
- Downstream Step 13 compatibility confirmed

## Documentation
- EXECUTIVE_SUMMARY_FOR_LEADERSHIP.md
- TARGET_FILTERING_SPECIFICATION.md
- OUTPUT_COMPARISON_RESULTS.md
- 119 additional analysis documents

## Known Issues
- opportunity_identifier.py at 558 LOC (58 over 500 limit) - documented technical debt

## Recommendation
- Merge to preserve refactored code
- Implement Option B fixes in follow-up PR (7 weeks)

## Related
Closes #163
```

**Status:** [ ] Complete

---

## Step 6: Code Review

### 6.1 Self-Review Checklist
- [ ] All tests passing
- [ ] No debug code left in
- [ ] No commented-out code
- [ ] Documentation complete
- [ ] Output validated
- [ ] Known issues documented

**Status:** [ ] Complete

---

### 6.2 Request Review
- [ ] Assign reviewer (boss/team lead)
- [ ] Add labels: `refactoring`, `step-7`, `ready-for-review`
- [ ] Link to analysis docs

**Status:** [ ] Complete

---

## Step 7: Merge to Main (After Approval)

### 7.1 Final Pre-Merge Check
```bash
# Ensure branch is up to date
git checkout ais-163-refactor-step-7
git fetch origin main
git merge origin/main

# Run tests one more time
python -m pytest tests/step_definitions/test_step7_missing_category_rule.py -v
```

**Status:** [ ] Complete

---

### 7.2 Merge via GitHub
1. Go to PR on GitHub
2. Click "Merge Pull Request"
3. Choose: **"Create a merge commit"** (preserves history)
4. Confirm merge

**Status:** [ ] Complete

---

### 7.3 Verify Merge Success
```bash
# Switch to main and pull
git checkout main
git pull origin main

# Verify latest commit
git log --oneline -1

# Run tests on main
python -m pytest tests/step_definitions/test_step7_missing_category_rule.py -v
```

**Expected Output:**
```
============================= 34 passed in XX.XXs ==============================
```

**Status:** [ ] Complete

---

## Step 8: Post-Merge Cleanup

### 8.1 Keep Backup Branches (For Safety)
```bash
# List all backup branches
git branch -a | grep backup

# DO NOT DELETE - keep for 30 days
```

**Backup Branches to Keep:**
- ais-163-refactor-step-7-backup-20251110
- main-backup-pre-ais163-20251110

**Status:** [ ] Verified

---

### 8.2 Update Local Repository
```bash
# Clean up local branches (optional)
git branch -d ais-163-refactor-step-7

# Verify main is current
git checkout main
git pull origin main
```

**Status:** [ ] Complete

---

## Rollback Procedures (If Something Goes Wrong)

### Rollback Option 1: Revert Merge Commit
```bash
# If merge causes issues, revert it
git checkout main
git revert -m 1 <merge-commit-hash>
git push origin main
```

### Rollback Option 2: Reset to Backup Tag
```bash
# Nuclear option - reset to pre-merge state
git checkout main
git reset --hard pre-ais163-merge-20251110
git push origin main --force

# ⚠️ ONLY USE IF ABSOLUTELY NECESSARY
```

### Rollback Option 3: Restore from Backup Branch
```bash
# Restore main from backup
git checkout main
git reset --hard origin/main-backup-pre-ais163-20251110
git push origin main --force

# ⚠️ ONLY USE IF ABSOLUTELY NECESSARY
```

---

## Emergency Contacts

**If merge goes wrong:**
1. **STOP** - Don't make more changes
2. **Document** - Note what went wrong
3. **Notify** - Contact team lead/boss
4. **Rollback** - Use procedures above if approved

---

## Success Criteria

### Merge is Successful When:
- [x] All backups created
- [ ] All tests passing on main
- [ ] Output files generated correctly
- [ ] No conflicts or errors
- [ ] Documentation accessible
- [ ] Team notified of merge

---

## Timeline

**Estimated Time:** 30-45 minutes

- Step 1 (Backups): 5 minutes
- Step 2 (Validation): 5 minutes
- Step 3 (Update from main): 5 minutes
- Step 4 (Conflicts): 0-15 minutes (if any)
- Step 5 (PR Creation): 5 minutes
- Step 6 (Review): Variable (wait for approval)
- Step 7 (Merge): 5 minutes
- Step 8 (Cleanup): 5 minutes

---

## Current Status

**Phase:** Pre-Merge Preparation  
**Ready to Start:** ✅ Yes  
**Backups Created:** ⏳ Pending  
**Tests Passing:** ✅ Yes (34/34)  
**Conflicts Expected:** ❓ Unknown

---

**Document Status:** Complete  
**Next Action:** Execute Step 1 (Create Backups)
