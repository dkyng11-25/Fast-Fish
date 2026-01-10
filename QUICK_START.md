# Quick Start - Pipeline Validation

## 🚀 **Run the Complete Pipeline in 3 Steps**

### **1. Navigate to Directory**
```bash
cd /Users/borislavdzodzo/Desktop/Dev/ais-129-issues-found-when-running-main
```

### **2. Execute Pipeline** (2-4 hours)
```bash
./setup_and_run_pipeline.sh 2>&1 | tee pipeline_execution_log.txt
```

### **3. Validate Results**
```bash
python3 validate_dual_outputs.py
```

## ✅ **What This Does**

1. **Creates symlinks** from working branch (no data download)
2. **Runs 34 steps** (skips Steps 1 & 4 - data download)
3. **Validates** dual output pattern implementation
4. **Confirms** all fixes work correctly

## 📊 **Expected Results**

- ✅ ~100+ output files created
- ✅ ~30 dual output file pairs
- ✅ ~190,000+ final delivery records
- ✅ 100% validation pass rate

## 🎯 **Success Criteria**

- All steps complete without errors
- Both timestamped and generic files exist
- File sizes match between versions
- No manual symlinks needed

## 📝 **Review Logs**

```bash
# View execution log
less pipeline_execution_log.txt

# Check specific step outputs
ls -lh output/fast_fish_with_sell_through_analysis_202510A*
ls -lh output/enriched_store_attributes*
ls -lh output/unified_delivery_202510A*
```

## 🎉 **That's It!**

The pipeline will validate all our dual output pattern fixes automatically.

For detailed information, see `PIPELINE_VALIDATION_PLAN.md`
