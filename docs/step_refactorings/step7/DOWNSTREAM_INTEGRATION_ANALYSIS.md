# Step 7: Downstream Integration Analysis

**Date:** 2025-11-03  
**Status:** ✅ COMPLETE  
**Downstream Consumer:** Step 13 (Consolidate SPU Rules)

---

## 📋 Output Files Produced by Step 7

### 1. Store Results CSV
**File Pattern:**
```
output/rule7_missing_{analysis_level}_sellthrough_results_{timestamp}.csv
output/rule7_missing_{analysis_level}_sellthrough_results_{period_label}.csv (symlink)
output/rule7_missing_{analysis_level}_sellthrough_results.csv (symlink)
```

**Purpose:** Aggregated store-level metrics for rule flagging

**Key Columns:**
- `str_code` - Store identifier
- `cluster_id` - Cluster assignment
- `missing_categories_count` OR `missing_spus_count` - Count of opportunities
- `total_quantity_needed` - Sum of recommended quantities
- `total_investment_required` - Sum of cost-based investment
- `total_retail_value` - Sum of retail values
- `avg_sellthrough_improvement` - Average improvement percentage
- `rule7_missing_category` OR `rule7_missing_spu` - Binary flag (0/1)

### 2. Opportunities CSV (PRIMARY for Step 13)
**File Pattern:**
```
output/rule7_missing_{analysis_level}_sellthrough_opportunities_{timestamp}.csv
output/rule7_missing_{analysis_level}_sellthrough_opportunities_{period_label}.csv (symlink)
output/rule7_missing_{analysis_level}_sellthrough_opportunities.csv (symlink)
```

**Purpose:** Detailed individual recommendations for consolidation

**Key Columns (REQUIRED by Step 13):**
- `str_code` - Store identifier ✅ REQUIRED
- `cluster_id` - Cluster assignment ✅ REQUIRED
- `spu_code` - Product identifier ✅ REQUIRED
- `sub_cate_name` - Subcategory name ✅ REQUIRED
- `recommended_quantity_change` - Quantity delta ✅ REQUIRED
- `unit_price` - Real unit price
- `investment_required` - Cost-based investment
- `business_rationale` - Explanation text
- `sell_through_improvement` - Improvement percentage
- `fast_fish_compliant` - Boolean flag

### 3. Summary Report MD
**File Pattern:**
```
output/rule7_missing_{analysis_level}_sellthrough_summary_{period_label}.md
```

**Purpose:** Human-readable analysis report (not consumed by Step 13)

---

## 🔗 Step 13 Integration Requirements

### File Resolution Strategy
**Step 13 uses manifest-backed resolution with fallbacks:**

```python
# Step 13 looks for Step 7 outputs in this order:
rule7_keys = [
    f"opportunities_{period_label}",  # Preferred: period-specific opportunities
    "opportunities",                   # Fallback: generic opportunities
    f"store_results_{period_label}",  # Alternative: period-specific results
    "store_results",                   # Alternative: generic results
]

# Fallback file paths (if manifest fails):
fallback_paths = [
    f"output/rule7_missing_spu_sellthrough_opportunities_{period_label}.csv",
    "output/rule7_missing_spu_sellthrough_opportunities.csv",
    f"output/rule7_missing_spu_sellthrough_results_{period_label}.csv",
    "output/rule7_missing_spu_sellthrough_results.csv",
]
```

### Required Columns for Consolidation

**CRITICAL:** Step 13 expects these columns (lines 1683-1684):
```python
required_cols = [
    'str_code',                    # Store identifier
    'spu_code',                    # Product identifier
    'sub_cate_name',              # Subcategory name
    'recommended_quantity_change'  # Quantity delta
]
```

**Column Handling in Step 13:**
- If `sub_cate_name` missing: Tries `category_key`, else sets to NA
- If `recommended_quantity_change` missing: Looks for other quantity columns, else sets to NA
- If `spu_code` missing: Cannot consolidate (critical failure)

### Column Naming Standards

**MUST USE:**
- ✅ `cluster_id` (NOT `Cluster`)
- ✅ `sub_cate_name` (standardized subcategory column)
- ✅ `recommended_quantity_change` (standardized quantity column)
- ✅ `str_code` (standardized store column)

**Step 13 Column Mapping:**
```python
standard_cols = {
    'str_code': 'str_code',
    'spu_code': 'spu_code', 
    'sub_cate_name': 'sub_cate_name',
    'recommended_quantity_change': 'recommended_quantity_change',
    'unit_price': 'unit_price',
    'investment_required': 'investment_required'
}
```

---

## 📊 Data Quality Requirements

### 1. Store Code Consistency
**Requirement:** `str_code` must be string type
```python
dtype={'str_code': str}  # Step 13 loads with this dtype
```

### 2. SPU Code Presence
**Requirement:** Every opportunity must have `spu_code`
- Used for counting unique SPUs per store
- Used for grouping and aggregation
- Cannot be NA or missing

### 3. Subcategory Name
**Requirement:** `sub_cate_name` should be present
- Used for sales aggregation
- Used for ratio calculations
- Can be NA but affects downstream analytics

### 4. Quantity Change
**Requirement:** `recommended_quantity_change` must be numeric
- Used for total quantity calculations
- Used for investment calculations
- Should be integer (units)

### 5. Investment Required
**Requirement:** Should be cost-based (not retail)
```python
investment_required = quantity * unit_cost
# where unit_cost = unit_price * (1 - margin_rate)
```

---

## 🎯 Integration Test Scenarios

### Scenario 1: Happy Path
**Given:** Step 7 produces opportunities CSV with all required columns  
**When:** Step 13 consolidates rules  
**Then:** Rule 7 data successfully integrated

**Validation:**
- All required columns present
- Column names match standards
- Data types correct
- No missing critical values

### Scenario 2: Missing Subcategory
**Given:** Step 7 opportunities missing `sub_cate_name`  
**When:** Step 13 consolidates rules  
**Then:** Step 13 sets `sub_cate_name` to NA and continues

**Expected Behavior:**
- Warning logged
- Consolidation continues
- Downstream analytics may be limited

### Scenario 3: Missing Quantity Change
**Given:** Step 7 opportunities missing `recommended_quantity_change`  
**When:** Step 13 consolidates rules  
**Then:** Step 13 sets quantity to NA and continues

**Expected Behavior:**
- Warning logged
- Consolidation continues
- Investment calculations may fail

### Scenario 4: Column Name Mismatch
**Given:** Step 7 uses `Cluster` instead of `cluster_id`  
**When:** Step 13 consolidates rules  
**Then:** Integration may fail or produce incorrect results

**Prevention:** Standardize column names in Step 7 output

---

## ✅ Compliance Checklist

### Output Files:
- [ ] Opportunities CSV created with timestamped filename
- [ ] Period-specific symlink created
- [ ] Generic symlink created
- [ ] Registered in pipeline manifest

### Required Columns:
- [ ] `str_code` (string type)
- [ ] `spu_code` (present, not NA)
- [ ] `sub_cate_name` (present, can be NA)
- [ ] `recommended_quantity_change` (numeric, integer)
- [ ] `cluster_id` (NOT `Cluster`)

### Data Quality:
- [ ] All store codes are strings
- [ ] All SPU codes are present
- [ ] Quantities are integers
- [ ] Investment is cost-based
- [ ] Unit prices are real (not synthetic)

### Manifest Registration:
- [ ] Key: `opportunities_{period_label}`
- [ ] Key: `opportunities` (generic)
- [ ] Metadata includes: rows, columns, analysis_level, period_label

---

## 🚨 Critical Integration Points

### 1. Column Naming
**Issue:** Step 13 expects exact column names  
**Solution:** Use standardized names in Step 7 output  
**Impact:** High - wrong names cause integration failure

### 2. SPU Code Presence
**Issue:** Step 13 requires `spu_code` for all opportunities  
**Solution:** Ensure every opportunity has SPU code  
**Impact:** Critical - missing SPU codes break consolidation

### 3. Manifest Registration
**Issue:** Step 13 prefers manifest-backed resolution  
**Solution:** Register all outputs in manifest  
**Impact:** Medium - fallback to file paths works but less robust

### 4. Data Types
**Issue:** Step 13 loads with specific dtypes  
**Solution:** Ensure `str_code` is string in output  
**Impact:** Medium - type mismatches cause merge issues

---

## 📝 Recommendations for Refactoring

### 1. Standardize Column Names Early
- Use `cluster_id` from the start (not `Cluster`)
- Use `sub_cate_name` consistently
- Use `recommended_quantity_change` for quantities

### 2. Validate Before Persist
- Check all required columns present
- Check data types correct
- Check no missing critical values
- Raise `DataValidationError` if validation fails

### 3. Manifest Registration
- Register opportunities with period-specific key
- Register opportunities with generic key
- Include complete metadata

### 4. Backward Compatibility
- Maintain symlink structure
- Support both SPU and subcategory modes
- Preserve all existing column names

---

**Analysis Complete:** ✅  
**Next Step:** Create test scenarios  
**Date:** 2025-11-03
