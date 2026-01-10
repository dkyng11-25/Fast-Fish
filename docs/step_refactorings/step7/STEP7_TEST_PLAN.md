# Step 7 Refactoring - End-to-End Test Plan

**Date:** 2025-11-04  
**Target:** 202510A  
**Purpose:** Validate refactored Step 7 produces identical results to legacy

---

## 🎯 Test Objective

Compare legacy Step 7 output with refactored Step 7 output to ensure:
1. Same business logic
2. Same data transformations
3. Same output format
4. Compatible with downstream steps

---

## 📋 Test Steps

### Step 1: Copy Downloaded Data ✅

**Script:** `./copy_downloaded_data.sh`

**What it does:**
- Copies API data from `ais-129-issues-found-when-running-main` (Step 1 output)
- Copies weather data from `ais-96-step36-fast-compliance` (Step 4 output)
- Avoids re-downloading data from APIs

**Status:** ✅ Complete (62 API files copied)

---

### Step 2: Run Prerequisite Steps (2, 3, 5, 6)

**Script:** `./run_legacy_steps_2_to_6.sh`

**What it does:**
- **Step 2:** Extract coordinates from store config
- **Step 3:** Calculate feels-like temperature
- **Step 5:** Perform cluster analysis
- **Step 6:** Prepare matrix data

**Status:** ⏳ Ready to run

---

### Step 3: Run Complete Test

**Script:** `./test_step7_refactoring.sh`

**What it does:**
1. Runs prerequisite steps (2, 3, 5, 6)
2. Runs **legacy** Step 7
3. Backs up legacy results with timestamp
4. Runs **refactored** Step 7
5. Compares outputs:
   - Row counts
   - Column names
   - First few rows
   - File sizes

**Status:** ⏳ Ready to run

---

## 🔍 What to Verify

### 1. Row Count Match
```bash
# Should be identical or very close
Legacy:     XXX rows
Refactored: XXX rows
```

### 2. Column Names
```bash
# Should have same columns (order may differ)
Legacy columns:     [list]
Refactored columns: [list]
```

### 3. Business Logic
- Missing categories identified correctly
- Quantity recommendations match
- ROI calculations consistent
- Sell-through validation applied

### 4. Seasonal Blending (if enabled)
- Autumn styles appear in August recommendations
- Seasonal weighting applied correctly (60% seasonal, 40% recent)

---

## 🚀 How to Run

### Quick Test (All-in-One)
```bash
./test_step7_refactoring.sh
```

### Manual Step-by-Step
```bash
# 1. Copy data (already done)
./copy_downloaded_data.sh

# 2. Run prerequisite steps
./run_legacy_steps_2_to_6.sh

# 3. Run legacy Step 7
python src/step7_missing_category_rule.py --target-yyyymm 202510 --target-period A

# 4. Backup results
mkdir -p output/step7_legacy_backup
cp output/*rule7* output/step7_legacy_backup/

# 5. Run refactored Step 7
python src/step7_missing_category_rule_refactored.py \
    --target-yyyymm 202510 \
    --target-period A \
    --verbose

# 6. Compare manually
diff output/step7_legacy_backup/*.csv output/*rule7*.csv
```

---

## 📊 Expected Outputs

### Legacy Step 7 Output
```
output/rule7_missing_category_202510A_YYYYMMDD_HHMMSS.csv
```

### Refactored Step 7 Output
```
output/rule7_missing_category_202510A_YYYYMMDD_HHMMSS.csv
output/rule7_missing_category_202510A_YYYYMMDD_HHMMSS_summary.md
```

---

## ✅ Success Criteria

| Criterion | Expected | Pass/Fail |
|-----------|----------|-----------|
| **Row count** | ±5% tolerance | ⏳ |
| **Column names** | Exact match | ⏳ |
| **Missing categories** | Same categories identified | ⏳ |
| **Quantity recommendations** | Within ±10% | ⏳ |
| **ROI calculations** | Within ±5% | ⏳ |
| **File format** | CSV with headers | ⏳ |
| **No errors** | Clean execution | ⏳ |

---

## 🐛 Known Differences (Expected)

### 1. Seasonal Blending
- **Legacy:** Uses only recent period data
- **Refactored:** Can blend seasonal data (configurable)
- **Impact:** Refactored may show autumn styles in August

### 2. Logging
- **Legacy:** Minimal logging
- **Refactored:** Comprehensive logging with progress tracking

### 3. Output Format
- **Legacy:** CSV only
- **Refactored:** CSV + markdown summary report

### 4. Column Order
- **Legacy:** Fixed order
- **Refactored:** May have different order (same columns)

---

## 📁 File Locations

### Data Sources
```
data/api_data/           # Step 1 output (copied from ais-129)
data/weather_data/       # Step 4 output (copied from ais-96)
```

### Intermediate Outputs
```
output/step2_*.csv       # Coordinates
output/step3_*.csv       # Feels-like temperature
output/step5_*.csv       # Cluster analysis
output/step6_*.csv       # Matrix preparation
```

### Step 7 Outputs
```
output/step7_legacy_backup_TIMESTAMP/    # Legacy results
output/rule7_missing_category_*.csv      # Refactored results
```

---

## 🔧 Troubleshooting

### Issue: "File not found"
**Solution:** Run `./copy_downloaded_data.sh` first

### Issue: "Step 2 fails"
**Solution:** Check that API data exists in `data/api_data/`

### Issue: "Different row counts"
**Possible causes:**
1. Seasonal blending enabled (expected)
2. Different thresholds configured
3. Data filtering differences

### Issue: "Import errors"
**Solution:** Ensure virtual environment is activated:
```bash
source .venv/bin/activate  # or your venv path
```

---

## 📝 Test Results Log

**Test Run:** [Date/Time]  
**Tester:** [Name]  
**Target:** 202510A

### Results:
- [ ] Prerequisite steps completed
- [ ] Legacy Step 7 ran successfully
- [ ] Refactored Step 7 ran successfully
- [ ] Row counts match (within tolerance)
- [ ] Column names match
- [ ] Business logic validated
- [ ] No errors encountered

### Notes:
```
[Add observations here]
```

---

## 🎯 Next Steps After Testing

1. **If tests pass:**
   - Document any acceptable differences
   - Update integration documentation
   - Prepare for production deployment

2. **If tests fail:**
   - Debug differences
   - Fix refactored code
   - Re-run tests
   - Update test documentation

3. **After validation:**
   - Run with different periods (202508A, 202509A, etc.)
   - Test SPU mode vs subcategory mode
   - Test with/without seasonal blending
   - Performance benchmarking

---

**Status:** Ready to execute test plan
