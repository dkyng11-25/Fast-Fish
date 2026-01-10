# How to Run Pipeline - Found Instructions

## ✅ Found Existing Pipeline Execution Script

**File**: `setup_and_run_pipeline.sh`

This script was used before and contains the complete pipeline execution sequence.

## What It Does

### Phase 0: Data Setup
- Creates symlinks from source directory
- Links 202410A data as 202510A (for testing)
- Sets up all required data files

### Phase 1-6: Runs All Steps
- Skips Step 1 (uses symlinked data)
- Skips Step 4 (uses symlinked data)
- Runs Steps 2, 2B, 3, 5, 6
- Runs Steps 7-36 in sequence

### Environment Variables Used:
```bash
PIPELINE_TARGET_YYYYMM=202510
PIPELINE_TARGET_PERIOD=A
PYTHONPATH=.
FAST_MODE=1 (for Step 13)
```

## Key Configuration

### Target Period:
- **YYYYMM**: 202510 (October 2025)
- **Period**: A (first half)

### Data Source:
```bash
SOURCE_DIR="/Users/borislavdzodzo/Desktop/Dev/ProducMixClustering_spu_clustering_rules_visualization-copy"
```

Uses real data from 202410A, symlinked as 202510A.

## How to Run

### Option 1: Use Existing Script (Recommended)
```bash
./setup_and_run_pipeline.sh
```

This will:
1. Set up data symlinks
2. Run all steps in sequence
3. Create dual output files
4. Validate outputs

### Option 2: Manual Step-by-Step
```bash
# Set environment
export PIPELINE_TARGET_YYYYMM=202510
export PIPELINE_TARGET_PERIOD=A
export PYTHONPATH=.

# Run each step
python3 src/step2_extract_coordinates.py --target-yyyymm 202510 --target-period A
python3 src/step2b_consolidate_seasonal_data.py --target-yyyymm 202510 --target-period A
# ... etc
```

### Option 3: Test Subset (Quick Validation)
```bash
# Just run a few critical steps to test dual output
export PYTHONPATH=.

python3 src/step6_cluster_analysis.py --target-yyyymm 202510 --target-period A
python3 src/step7_missing_category_rule.py --target-yyyymm 202510 --target-period A
python3 src/step13_consolidate_spu_rules.py --target-yyyymm 202510 --target-period A
```

## Pre-Run Checklist

### ✅ Already Done:
- [x] Output directory cleaned
- [x] Backup created (output_backup_20251002_184407/)

### ⚠️ Need to Verify:
- [ ] Source data directory exists: `/Users/borislavdzodzo/Desktop/Dev/ProducMixClustering_spu_clustering_rules_visualization-copy`
- [ ] Source has 202410A data files
- [ ] Python environment is activated

## Verification Commands

### Check Source Directory:
```bash
ls -lh /Users/borislavdzodzo/Desktop/Dev/ProducMixClustering_spu_clustering_rules_visualization-copy/data/api_data/complete_spu_sales_202410A.csv
```

### Check Python Environment:
```bash
which python3
python3 --version
```

### Check Required Packages:
```bash
python3 -c "import pandas, numpy, sklearn; print('✅ All packages available')"
```

## What to Expect

### During Execution:
- Each step will log progress
- Timestamped files will be created in `output/`
- Symlinks will be created alongside
- Some steps may take several minutes

### After Execution:
- Check `output/` for timestamped files
- Verify symlinks exist
- Run integration test: `pytest tests/test_dual_output_validation.py -v`

## Important Notes

### From Previous Runs:
1. **Step 1 & 4 skipped** - Use symlinked data instead of downloading
2. **Step 13 uses FAST_MODE=1** - Faster execution
3. **Step 32 has special flags** - Future-oriented configuration
4. **Some steps have environment overrides** - Check script for details

### Data Dependencies:
- Steps depend on previous step outputs
- Must run in sequence (can't skip steps)
- Some steps have optional configurations

## Summary

**Found**: Complete pipeline execution script ✅
**Location**: `setup_and_run_pipeline.sh`
**Target**: 202510A (October 2025 first half)
**Data Source**: Symlinked from 202410A real data

**Ready to run when you confirm the source directory exists!**
