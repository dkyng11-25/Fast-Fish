# Rule 11 IMPROVED: Mathematical Formulas and Algorithms

## 📊 **Core Mathematical Framework**

### **1. Data Preparation & Filtering**

**Input Data Cleaning:**
```
S_filtered = {s ∈ S | sales(s) ≥ MIN_SPU_SALES}
```
Where:
- `S` = Set of all SPU sales records
- `MIN_SPU_SALES = 50` (minimum sales threshold)

**Category Key Generation:**
```
category_key(i) = cate_name(i) ⊕ "|" ⊕ sub_cate_name(i)
```
Where `⊕` denotes string concatenation.

---

### **2. Top Performer Identification Algorithm**

**Cluster-Category Grouping:**
```
G_{c,k} = {s ∈ S | cluster(s) = c ∧ category_key(s) = k}
```
Where:
- `c` = cluster identifier
- `k` = category key
- `G_{c,k}` = set of all SPU records in cluster `c` and category `k`

**SPU Performance Aggregation:**
For each SPU `p` in cluster-category `(c,k)`:

```
total_sales(p,c,k) = Σ_{s∈G_{c,k},spu(s)=p} sales(s)

avg_sales(p,c,k) = total_sales(p,c,k) / |{s ∈ G_{c,k} | spu(s) = p}|

stores_selling(p,c,k) = |{store(s) | s ∈ G_{c,k} ∧ spu(s) = p}|

total_stores(c,k) = |{store(s) | s ∈ G_{c,k}}|
```

**Adoption Rate Calculation:**
```
adoption_rate(p,c,k) = stores_selling(p,c,k) / total_stores(c,k)
```

**Sales Percentile Ranking:**
```
sales_percentile(p,c,k) = rank(total_sales(p,c,k)) / |P_{c,k}|
```
Where `P_{c,k}` = set of all SPUs in cluster-category `(c,k)` with `stores_selling ≥ MIN_STORES_SELLING`

**Top Performer Threshold:**
```
TOP_PERFORMERS_{c,k} = {p ∈ P_{c,k} | sales_percentile(p,c,k) ≥ TOP_PERFORMER_THRESHOLD}
```
Where `TOP_PERFORMER_THRESHOLD = 0.80` (top 20%)

---

### **3. Missing Opportunity Detection**

**Store SPU Set:**
```
SPU_STORE(st,c,k) = {spu(s) | s ∈ G_{c,k} ∧ store(s) = st}
```

**Missing SPUs per Store:**
```
MISSING(st,c,k) = TOP_PERFORMERS_{c,k} \ SPU_STORE(st,c,k)
```

**Opportunity Score Calculation:**
For each missing SPU `p` at store `st`:
```
opportunity_score(p,st,c,k) = sales_percentile(p,c,k) × adoption_rate(p,c,k)
```

**Range:** `opportunity_score ∈ [0.48, 1.0]` 
- Minimum: `0.80 × 0.60 = 0.48` (80th percentile × 60% adoption)
- Maximum: `1.00 × 1.00 = 1.00` (100th percentile × 100% adoption)

---

### **4. Store-Level Aggregation**

**Missing Top Performers Count:**
```
missing_count(st) = Σ_{c,k} |MISSING(st,c,k)|
```

**Average Opportunity Score:**
```
avg_opportunity_score(st) = (Σ_{c,k} Σ_{p∈MISSING(st,c,k)} opportunity_score(p,st,c,k)) / missing_count(st)
```

**Potential Sales Increase:**
```
potential_sales(st) = Σ_{c,k} Σ_{p∈MISSING(st,c,k)} avg_sales(p,c,k)
```

**Binary Flagging Rule:**
```
rule11_flag(st) = {
    1, if missing_count(st) > 0
    0, otherwise
}
```

---

### **5. Key Parameters & Thresholds**

| **Parameter** | **Value** | **Mathematical Symbol** | **Purpose** |
|---------------|-----------|-------------------------|-------------|
| Top Performer Threshold | 0.80 | `τ_top` | Top 20% by sales percentile |
| Minimum Cluster Stores | 5 | `n_min` | Statistical significance |
| Minimum Stores Selling | 3 | `s_min` | "Proven winner" validation |
| Minimum SPU Sales | 50 | `$_min` | Noise reduction |
| Adoption Threshold | 0.60 | `α_adopt` | Expected adoption rate |

---

### **6. Algorithm Complexity**

**Time Complexity:**
```
O(|S| × log|S| + |C| × |K| × |P|)
```
Where:
- `|S|` = number of SPU sales records
- `|C|` = number of clusters  
- `|K|` = number of categories
- `|P|` = average SPUs per cluster-category

**Space Complexity:**
```
O(|S| + |C| × |K| × |P|)
```

---

### **7. Statistical Properties**

**Expected Output Distribution:**
- **Top Performers per cluster-category:** ~20% of SPUs (by design)
- **Opportunity score distribution:** Right-skewed toward high scores
- **Store flagging rate:** Varies by cluster homogeneity

**Validation Metrics:**
```
precision = |{relevant top performers}| / |{identified top performers}|
recall = |{identified opportunities}| / |{actual opportunities}|
```

---

### **8. Business Logic Translation**

**Mathematical Interpretation → Business Meaning:**

1. **High Adoption Rate (`adoption_rate ≈ 1.0`):**
   - Mathematical: Nearly all stores in cluster carry this SPU
   - Business: "Proven winner with peer validation"

2. **High Sales Percentile (`sales_percentile ≥ 0.80`):**
   - Mathematical: Top 20% performer within category
   - Business: "Category champion by revenue"

3. **High Opportunity Score (`opportunity_score ≈ 1.0`):**
   - Mathematical: `sales_percentile × adoption_rate ≈ 1.0`
   - Business: "Low-risk, high-potential recommendation"

---

### **9. Example Calculation**

**Given:**
- Cluster 37, Category "T恤|休闲圆领T恤"
- SPU "15T1078": $172,991 total sales, 74/75 stores carry it
- 172 total SPUs in this cluster-category

**Calculations:**
```
adoption_rate = 74/75 = 0.987 (98.7%)
sales_percentile = rank($172,991) / 172 ≈ 0.99 (top performer)
opportunity_score = 0.99 × 0.987 = 0.977

Business Translation:
"SPU 15T1078 is a 97.7% confident recommendation:
 - 99th percentile performer (proven success)
 - 98.7% peer adoption (social proof)
 - Low risk, high potential opportunity"
```

---

### **10. Formula Validation**

**Sanity Checks:**
1. `0 ≤ adoption_rate ≤ 1` ✓
2. `0 ≤ sales_percentile ≤ 1` ✓  
3. `0 ≤ opportunity_score ≤ 1` ✓
4. `missing_count ≥ 0` ✓
5. `rule11_flag ∈ {0,1}` ✓

**Edge Cases:**
- **Empty cluster-category:** No top performers identified
- **All stores carry all SPUs:** No missing opportunities
- **Single-store cluster:** Excluded by `MIN_CLUSTER_STORES`

This mathematical framework ensures **rigorous, peer-validated, category-specific recommendations** with clear business interpretability. 