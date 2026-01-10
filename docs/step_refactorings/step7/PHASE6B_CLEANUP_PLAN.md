# Phase 6B: Pre-Merge Cleanup Plan
## Consolidating Step 7 Documentation

**Date:** 2025-11-10  
**Purpose:** Move all Step 7 related files to proper location before merge  
**Status:** 🚀 READY TO EXECUTE

---

## Files to Move to `docs/step_refactorings/step7/`

### Root Directory Markdown Files (Step 7 Related):
```
./STEP7_TEST_PLAN.md                    → docs/step_refactorings/step7/
./STEP7_TEST_STATUS.md                  → docs/step_refactorings/step7/
./STEP7_EXECUTION_SUMMARY.md            → docs/step_refactorings/step7/
./STEP7_COMPARISON.md                   → docs/step_refactorings/step7/
```

### Root Directory Scripts (Step 7 Testing):
```
./run_legacy_step7.sh                   → scripts/step7/ (create if needed)
./run_legacy_step7_subcategory.sh       → scripts/step7/
./run_refactored_step7_subcategory.sh   → scripts/step7/
./test_step7_refactoring.sh             → scripts/step7/
./test_refactored_step7_only.sh         → scripts/step7/
```

### Root Directory Debug Scripts (Step 7 Related):
```
./debug_feature_count.py                → scripts/debug/step7/ (create if needed)
./debug_legacy_data.py                  → scripts/debug/step7/
./debug_merge_investigation.py          → scripts/debug/step7/
./debug_september_data.py               → scripts/debug/step7/
./debug_spu_cluster_file.py             → scripts/debug/step7/
./debug_threshold_filtering.py          → scripts/debug/step7/
./debug_unique_subcategories.py         → scripts/debug/step7/
```

---

## Files to Keep in Root (General Purpose):

```
./README.md                             ✅ Keep (project readme)
./AGENTS.md                             ✅ Keep (development guidelines)
./QUICK_START.md                        ✅ Keep (general quickstart)
./README_START_HERE.md                  ✅ Keep (general guide)
./RUST_TOOLS_INSTALLER_README.md        ✅ Keep (tools setup)
./REFACTORING_STATUS_SUMMARY.md         ✅ Keep (overall status)
./CURRENT_STATUS_AND_NEXT_STEPS.md      ✅ Keep (overall status)
./COMPREHENSIVE_STEP_SPECS_COMPLETION.md ✅ Keep (overall specs)
./REFACTORING_PROJECT_MAP.md            ✅ Keep (overall map)
./SRC_REORGANIZATION_COMPLETE.md        ✅ Keep (overall reorg)
./continue_pipeline_from_step7.sh       ✅ Keep (general pipeline)
./run_legacy_steps_2_to_6.sh            ✅ Keep (general pipeline)
./copy_downloaded_data.sh               ✅ Keep (general utility)
```

---

## Mock Files to Delete:

```
"<Mock name='mock.file_path' id='4772675216'>"  → DELETE
"<Mock name='mock.file_path' id='4846293296'>"  → DELETE
"<Mock name='mock.file_path' id='4874841712'>"  → DELETE
"<Mock name='mock.file_path' id='4923955328'>"  → DELETE
"<Mock name='mock.file_path' id='4928807008'>"  → DELETE
"<Mock name='mock.file_path' id='4953047008'>"  → DELETE
```

---

## Execution Plan:

### Step 1: Create Directories
```bash
mkdir -p scripts/step7
mkdir -p scripts/debug/step7
```

### Step 2: Move Step 7 Docs
```bash
mv STEP7_*.md docs/step_refactorings/step7/
```

### Step 3: Move Step 7 Scripts
```bash
mv run_legacy_step7*.sh scripts/step7/
mv run_refactored_step7*.sh scripts/step7/
mv test_step7*.sh scripts/step7/
mv test_refactored_step7*.sh scripts/step7/
```

### Step 4: Move Debug Scripts
```bash
mv debug_*.py scripts/debug/step7/
```

### Step 5: Delete Mock Files
```bash
rm -f "<Mock name='mock.file_path' id='*'>"
```

### Step 6: Verify Clean Root
```bash
ls -la *.md | grep -i step7  # Should return nothing
ls -la *step7* | grep -v docs  # Should return nothing
```

---

## Expected Result:

### Root Directory:
- Only general project documentation
- No Step 7 specific files
- No debug scripts
- No mock files

### `docs/step_refactorings/step7/`:
- All Step 7 markdown documentation (122 files)
- Organized and complete

### `scripts/step7/`:
- All Step 7 test/run scripts
- Easy to find and use

### `scripts/debug/step7/`:
- All Step 7 debug scripts
- Separated from production code

---

## Validation Checklist:

- [ ] All STEP7_*.md files moved
- [ ] All *step7*.sh files moved
- [ ] All debug_*.py files moved
- [ ] Mock files deleted
- [ ] Root directory clean
- [ ] Documentation accessible
- [ ] Scripts still runnable

---

**Status:** Ready to execute  
**Estimated Time:** 5 minutes  
**Risk:** Low (just moving files)
