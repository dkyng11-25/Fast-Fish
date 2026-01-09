# ❌ C-04: Store Capacity in Clustering - NOT DONE

**Requirement ID:** C-04  
**Status:** ❌ NOT DONE  
**Source:** FF Contract (Phase 1)  
**Priority:** 🔴 CRITICAL  
**Deadline:** 2025-04-30 (OVERDUE)

---

## 📋 Requirement Description

Include store capacity (batch count / sales volume) as a feature in the clustering matrix so that stores of similar size cluster together.

**Client Expectation:**
- Each store should have a `capacity_tier` attribute: `S`, `M`, `L`, `XL`
- This attribute should influence clustering decisions
- Large stores shouldn't cluster with small stores

---

## ❌ Current State

### What Exists
- Raw sales data contains `spu_sales_amt` (sales amount) field
- Total sales per store can be calculated
- No implementation exists to calculate store capacity tier

### What's Missing
1. **Capacity Calculation** - No function to compute total sales volume per store
2. **Tier Classification** - No quartile-based tier assignment
3. **Matrix Integration** - No `capacity_tier` or `total_sales` column in clustering matrix

---

## 🔧 What is Needed to Get it Done

### 1. Python Code Required ✅

**Location:** `src/step3_prepare_matrix.py` (or new component)

**Implementation:**

```python
def calculate_store_capacity(sales_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate capacity tier based on total sales volume.
    
    Args:
        sales_df: DataFrame with columns [str_code, spu_sales_amt]
    
    Returns:
        DataFrame with columns [str_code, total_sales, capacity_tier, capacity_normalized]
        - total_sales: Sum of all sales for the store
        - capacity_tier: 'S' (bottom 25%), 'M' (25-50%), 'L' (50-75%), 'XL' (top 25%)
        - capacity_normalized: 0.0 to 1.0 scale for clustering
    """
    # Calculate total sales per store
    total_sales = sales_df.groupby('str_code')['spu_sales_amt'].sum()
    
    # Assign capacity tier using quartiles
    capacity_tier = pd.qcut(
        total_sales, 
        q=4, 
        labels=['S', 'M', 'L', 'XL']
    )
    
    # Normalize to 0-1 scale for clustering
    min_sales = total_sales.min()
    max_sales = total_sales.max()
    capacity_normalized = (total_sales - min_sales) / (max_sales - min_sales)
    
    return pd.DataFrame({
        'str_code': total_sales.index,
        'total_sales': total_sales.values,
        'capacity_tier': capacity_tier.values,
        'capacity_normalized': capacity_normalized.values
    })
```

### 2. No External Dependencies Required ✅

This requirement can be implemented entirely with existing data:
- Sales data is already downloaded in Step 1
- No additional API calls or datasets needed

### 3. Integration with Matrix

After calculating store capacity, add to the clustering matrix:

```python
# In step3_prepare_matrix.py, after creating the matrix:
store_capacity = calculate_store_capacity(spu_sales_df)

# Add capacity_normalized as a feature column (0-1 scale)
matrix['capacity_normalized'] = matrix.index.map(
    store_capacity.set_index('str_code')['capacity_normalized']
).fillna(0.5)

# Optionally: one-hot encode capacity_tier
# matrix['is_small'] = (store_capacity['capacity_tier'] == 'S').astype(int)
# matrix['is_medium'] = (store_capacity['capacity_tier'] == 'M').astype(int)
# matrix['is_large'] = (store_capacity['capacity_tier'] == 'L').astype(int)
# matrix['is_xlarge'] = (store_capacity['capacity_tier'] == 'XL').astype(int)
```

---

## 📊 Impact Analysis

### If Implemented
- Stores will cluster by both sales pattern AND size
- Large flagship stores won't be grouped with small boutiques
- Better alignment with client's operational model

### If Not Implemented
- Clustering ignores store size differences
- Very different sized stores may cluster together
- Client requirement C-04 remains unsatisfied

---

## ✅ Action Items

| # | Action | Owner | Status |
|---|--------|-------|--------|
| 1 | Implement `calculate_store_capacity()` function | Data Intern | ⏳ Pending |
| 2 | Add `capacity_normalized` to clustering matrix | Data Intern | ⏳ Pending |
| 3 | Re-run Step 3 and Step 6 | Data Intern | ⏳ Pending |
| 4 | Verify clustering results include capacity | Data Intern | ⏳ Pending |

---

## 🔄 Improvement Loop

**Current Iteration:** 1  
**Status:** Ready to implement - No blockers

**Next Steps:**
1. Implement Python code (no external dependencies)
2. Add to Step 3 matrix creation
3. Re-evaluate requirement status
