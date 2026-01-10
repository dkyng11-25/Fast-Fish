# ❌ C-03: Store Type Classification (Fashion/Basic) - NOT DONE

**Requirement ID:** C-03  
**Status:** ❌ NOT DONE  
**Source:** FF Contract (Phase 1)  
**Priority:** 🔴 CRITICAL  
**Deadline:** 2025-04-30 (OVERDUE)

---

## 📋 Requirement Description

Classify each store as **Fashion-oriented** or **Basic-oriented** based on their sales patterns, and include this classification as a feature in the clustering matrix.

**Client Expectation:**
- Each store should have a `store_type` attribute: `FASHION`, `BASIC`, or `BALANCED`
- This attribute should influence clustering decisions
- Stores with similar style preferences should cluster together

---

## ❌ Current State

### What Exists
- Raw sales data contains `cate_name` (category name) field
- Categories can be classified as Fashion or Basic
- No implementation exists to calculate store-level Fashion/Basic ratio

### What's Missing
1. **Category Classification List** - No defined list of Fashion vs Basic categories
2. **Store Type Calculation** - No function to compute Fashion/Basic ratio per store
3. **Matrix Integration** - No `store_type` or `fashion_ratio` column in clustering matrix

---

## 🔧 What is Needed to Get it Done

### 1. Python Code Required ✅

**Location:** `src/step3_prepare_matrix.py` (or new component)

**Implementation:**

```python
# Category classification (needs validation with domain expert)
FASHION_CATEGORIES = [
    '牛仔裤',      # Jeans
    '卫衣',        # Sweatshirts
    '外套',        # Outerwear
    '夹克',        # Jackets
    '羽绒服',      # Down jackets
    '连衣裙',      # Dresses
    '半身裙',      # Skirts
    '西装',        # Suits
    '风衣',        # Trench coats
]

BASIC_CATEGORIES = [
    'T恤',         # T-shirts
    '内衣',        # Underwear
    '袜子',        # Socks
    '家居服',      # Loungewear
    '打底衫',      # Base layers
    '背心',        # Vests
]

def calculate_store_type(category_sales_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Fashion/Basic ratio for each store.
    
    Args:
        category_sales_df: DataFrame with columns [str_code, cate_name, spu_sales_amt]
    
    Returns:
        DataFrame with columns [str_code, fashion_ratio, store_type]
        - fashion_ratio: 0.0 (pure Basic) to 1.0 (pure Fashion)
        - store_type: 'FASHION' (>0.6), 'BASIC' (<0.4), 'BALANCED' (0.4-0.6)
    """
    # Filter to Fashion categories
    fashion_sales = category_sales_df[
        category_sales_df['cate_name'].isin(FASHION_CATEGORIES)
    ].groupby('str_code')['spu_sales_amt'].sum()
    
    # Filter to Basic categories
    basic_sales = category_sales_df[
        category_sales_df['cate_name'].isin(BASIC_CATEGORIES)
    ].groupby('str_code')['spu_sales_amt'].sum()
    
    # Calculate ratio
    total = fashion_sales.add(basic_sales, fill_value=0)
    fashion_ratio = fashion_sales.div(total, fill_value=0).fillna(0.5)
    
    # Classify store type
    def classify(ratio):
        if ratio > 0.6:
            return 'FASHION'
        elif ratio < 0.4:
            return 'BASIC'
        else:
            return 'BALANCED'
    
    store_type = fashion_ratio.apply(classify)
    
    return pd.DataFrame({
        'str_code': fashion_ratio.index,
        'fashion_ratio': fashion_ratio.values,
        'store_type': store_type.values
    })
```

### 2. Clarification Needed from Boris/Domain Expert ⚠️

**Question:** What is the complete list of Fashion vs Basic categories?

The categories listed above are **estimated** based on common retail classification. We need:
- Validated list of all 126 categories
- Classification of each into Fashion, Basic, or Neutral
- Threshold values for FASHION/BASIC/BALANCED classification (currently 0.4/0.6)

### 3. Integration with Matrix

After calculating store type, add to the clustering matrix:

```python
# In step3_prepare_matrix.py, after creating the matrix:
store_types = calculate_store_type(category_sales_df)

# Add fashion_ratio as a feature column (normalized 0-1)
matrix['fashion_ratio'] = matrix.index.map(
    store_types.set_index('str_code')['fashion_ratio']
).fillna(0.5)

# Optionally: one-hot encode store_type
# matrix['is_fashion'] = (store_types['store_type'] == 'FASHION').astype(int)
# matrix['is_basic'] = (store_types['store_type'] == 'BASIC').astype(int)
```

---

## 📊 Impact Analysis

### If Implemented
- Stores will cluster by both sales pattern AND style preference
- Fashion stores won't be grouped with Basic stores
- Better alignment with client's business model

### If Not Implemented
- Clustering ignores store style differences
- Fashion-heavy and Basic-heavy stores may cluster together
- Client requirement C-03 remains unsatisfied

---

## ✅ Action Items

| # | Action | Owner | Status |
|---|--------|-------|--------|
| 1 | Get validated Fashion/Basic category list | Ask Boris | ⏳ Pending |
| 2 | Implement `calculate_store_type()` function | Data Intern | ⏳ Pending |
| 3 | Add `fashion_ratio` to clustering matrix | Data Intern | ⏳ Pending |
| 4 | Re-run Step 3 and Step 6 | Data Intern | ⏳ Pending |
| 5 | Verify clustering results include store type | Data Intern | ⏳ Pending |

---

## 🔄 Improvement Loop

**Current Iteration:** 1  
**Status:** Blocked - Need category classification list

**Next Steps:**
1. Request category list from Boris
2. Implement Python code
3. Re-evaluate requirement status
