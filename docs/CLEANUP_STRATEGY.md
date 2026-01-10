# Cleanup Strategy - Two-Stage Approach

**Date:** 2025-10-30  
**Purpose:** Clarify when to do what type of cleanup

---

## 🎯 Overview

**We have TWO different cleanup stages:**

1. **Phase 6A: Working Branch Cleanup** - During development
2. **Phase 6B: Pre-Main Cleanup** - Before merging to main

**⚠️ CRITICAL: Don't confuse them! They serve different purposes.**

---

## 📋 Phase 6A: Working Branch Cleanup

**When:** During development, after completing each phase

**Purpose:** Keep your working branch organized while preserving detailed documentation

**Document:** `REFACTORING_PROCESS_GUIDE.md` Phase 6A

### What to DO:
- ✅ Remove duplicate files
- ✅ Move misplaced documentation to proper locations
- ✅ Organize scripts into `/scripts/` subdirectories
- ✅ Remove temporary files from root
- ✅ Update INDEX.md
- ✅ Commit to working branch

### What to KEEP:
- ✅ **Detailed phase documents** (PHASE1-6_COMPLETE.md)
- ✅ **Archive directories** (for reference while working)
- ✅ **Compliance check documents**
- ✅ **Detailed testing docs**
- ✅ **All test files**
- ✅ **docs/transient/** (temporary work in progress)

### Why Keep These?
- Useful reference while working
- Track progress through phases
- Document decisions and rationale
- Easy to review what was done
- Can revert if needed

---

## 📋 Phase 6B: Pre-Main Cleanup

**When:** Before merging to main (final step)

**Purpose:** Create clean, professional main branch with only essential documentation

**Document:** `PRE_COMMIT_CHECKLIST.md`

### What to DELETE:
- ❌ **docs/transient/** - Entire directory
- ❌ **docs/step_refactorings/step{N}/archive/** - All archive directories
- ❌ **Detailed phase documents** (PHASE*.md, COMPLIANCE_*.md)
- ❌ **Detailed testing docs** (keep only testing/README.md)
- ❌ **Redundant test files** (after manual review and approval)
- ❌ **Detailed issue files** (consolidate into issues/README.md)

### What to CREATE:
- ✅ **Comprehensive READMEs** for each step
- ✅ **Testing READMEs** with actual test counts
- ✅ **Consolidated issues/README.md**

### What to KEEP:
- ✅ **docs/step_refactorings/step{N}/README.md**
- ✅ **docs/step_refactorings/step{N}/LESSONS_LEARNED.md**
- ✅ **docs/step_refactorings/step{N}/testing/README.md**
- ✅ **docs/step_refactorings/step{N}/issues/** (step-specific)
- ✅ **All actual test code** (in tests/)

### Why Delete These?
- Main branch should be clean and professional
- Archives pollute the repository
- Detailed phase docs are development artifacts
- READMEs provide all essential information
- Easier for new team members to navigate

---

## 🔄 Workflow Example

### During Development (Working Branch):

```
Week 1: Phase 1 Complete
├── Create PHASE1_COMPLETE.md
├── Keep in docs/step_refactorings/step{N}/
└── Commit to working branch

Week 2: Phase 2 Complete
├── Create PHASE2_COMPLETE.md
├── Keep both PHASE1 and PHASE2 docs
└── Commit to working branch

Week 3-4: Continue...
├── Keep accumulating phase docs
├── Keep archive/ for reference
└── Keep transient/ for work in progress
```

### Before Merging to Main:

```
Final Cleanup (Phase 6B):
├── Create comprehensive README.md
├── Delete PHASE1-6_COMPLETE.md
├── Delete archive/ directory
├── Delete docs/transient/
├── Consolidate into READMEs only
└── Merge to main (clean!)
```

---

## 📊 Comparison Table

| Item | Working Branch | Main Branch |
|------|---------------|-------------|
| **PHASE*.md files** | ✅ Keep | ❌ Delete |
| **archive/ directories** | ✅ Keep | ❌ Delete |
| **docs/transient/** | ✅ Keep | ❌ Delete |
| **Detailed testing docs** | ✅ Keep | ❌ Delete (keep README only) |
| **Compliance docs** | ✅ Keep | ❌ Delete |
| **Comprehensive READMEs** | ⚠️ Optional | ✅ Required |
| **Test files (tests/)** | ✅ Keep | ✅ Keep |
| **LESSONS_LEARNED.md** | ✅ Keep | ✅ Keep |
| **issues/ directories** | ✅ Keep | ✅ Keep (consolidated) |

---

## ⚠️ Common Mistakes

### ❌ DON'T:
1. **Delete archives during development**
   - You might need them for reference
   - Wait until pre-main cleanup

2. **Create comprehensive READMEs too early**
   - Wait until work is complete
   - Do it during pre-main cleanup

3. **Delete detailed docs on working branch**
   - Keep them for reference
   - Only delete before merging to main

4. **Forget to delete transient/ before main**
   - It's temporary by definition
   - Must be deleted before merge

5. **Delete test files without review**
   - Always manual review
   - Always get approval
   - Document reasoning

### ✅ DO:
1. **Keep detailed docs during development**
   - Useful for reference
   - Track progress
   - Document decisions

2. **Clean up before merging to main**
   - Professional appearance
   - Easy to navigate
   - Only essential docs

3. **Create comprehensive READMEs**
   - Consolidate all information
   - Make it easy to understand
   - Show actual reality

4. **Update documentation to match reality**
   - Run tests to get counts
   - Show actual status
   - No aspirational claims

---

## 🎯 Quick Reference

**During Development:**
- Keep everything
- Organize files
- Update INDEX.md
- Commit frequently

**Before Merging to Main:**
- Delete archives
- Delete detailed docs
- Delete transient/
- Create READMEs
- Consolidate everything
- Update to reality
- Clean and professional

---

## 📚 Related Documents

- **Working Branch Cleanup:** `REFACTORING_PROCESS_GUIDE.md` Phase 6A
- **Pre-Main Cleanup:** `PRE_COMMIT_CHECKLIST.md`
- **Process Guide:** `REFACTORING_PROCESS_GUIDE.md`

---

**Remember:** Working branch = Keep details, Main branch = Clean and professional!

**Last Updated:** 2025-10-30
