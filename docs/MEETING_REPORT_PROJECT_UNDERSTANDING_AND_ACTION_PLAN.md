# 🐟 Fast Fish Project Meeting Report

**Date:** 2025-01-09  
**Prepared by:** Data Intern  
**Purpose:** Present project understanding, requirements status, and proposed action plan

---

## 📋 Executive Summary

This report summarizes my understanding of the Fast Fish Product Mix Clustering project, the current status of client requirements, and a proposed action plan for addressing critical gaps. The project aims to optimize **sell-through rate** through AI-based store clustering and product mix recommendations.

### Key Findings

| Metric | Value |
|--------|-------|
| **Total Requirements** | 41 |
| **Satisfied** | 18 (44%) |
| **Partially Satisfied** | 13 (32%) |
| **Not Satisfied** | 10 (24%) |
| **Data Intern Actionable Items** | 4 critical requirements |

---

## 1. Project Understanding

### 1.1 Core Objective

**Primary KPI:** Sell-Through Rate = Sold SPU Count ÷ Inventory SPU Count

The project clusters stores based on sales patterns and generates product mix recommendations to maximize sell-through rate across ~2,300 stores.

### 1.2 Pipeline Architecture (Steps 1-6)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DATA PREPARATION PIPELINE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STEP 1: Download API Data                                                  │
│  ├─ Input: Fast Fish API (fdapidb.fastfish.com:8089)                       │
│  ├─ Output: store_config, store_sales, category_sales, spu_sales           │
│  └─ Purpose: Raw data acquisition for specific period (YYYYMM + A/B)       │
│                                                                             │
│  STEP 2: Extract Coordinates                                                │
│  ├─ Input: store_config from Step 1                                        │
│  ├─ Output: store_coordinates_extended.csv, spu_store_mapping.csv          │
│  └─ Purpose: Extract lat/lon for geographic analysis                       │
│                                                                             │
│  STEP 3: Prepare Matrix                                                     │
│  ├─ Input: category_sales, spu_sales from Step 1                           │
│  ├─ Output: normalized_spu_limited_matrix.csv (Store × SPU matrix)         │
│  └─ Purpose: Create feature matrix for clustering                          │
│                                                                             │
│  STEP 4: Download Weather Data                                              │
│  ├─ Input: Coordinates from Step 2                                         │
│  ├─ Output: weather_data/*.csv, store_altitudes.csv                        │
│  └─ Purpose: Get temperature/humidity for each store location              │
│                                                                             │
│  STEP 5: Calculate Feels-Like Temperature                                   │
│  ├─ Input: Weather data from Step 4                                        │
│  ├─ Output: stores_with_feels_like_temperature.csv                         │
│  └─ Purpose: Create temperature bands for clustering constraints           │
│                                                                             │
│  STEP 6: Cluster Analysis                                                   │
│  ├─ Input: Matrix from Step 3, Temperature from Step 5 (optional)          │
│  ├─ Process: PCA (50 components) → K-Means (46 clusters)                   │
│  ├─ Output: clustering_results_spu_*.csv, cluster_profiles_*.csv           │
│  └─ Purpose: Assign each store to a cluster                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Post-Clustering Pipeline (Steps 7-36)

| Step Range | Purpose |
|------------|---------|
| **Step 7-14** | Rule generation, SPU assortment optimization |
| **Step 15-20** | Validation, historical baseline, comparison |
| **Step 21-24** | Label/tag recommendations, cluster labeling |
| **Step 25-30** | Product role classification, gap analysis, optimization |
| **Step 31-36** | Store allocation, merchandising rules, visualization |

---

## 2. Analytical Framework

### 2.1 Multi-Perspective Approach (from Protocol)

The project uses a **multi-perspective analytical approach** with five expert lenses:

| Perspective | Focus | Application |
|-------------|-------|-------------|
| **Retail Strategist** | Business value | Evaluating sell-through and revenue |
| **Data Scientist** | Pattern analysis | Clustering algorithms, trend identification |
| **Operations Research** | Optimization | SPU allocation, capacity constraints |
| **Store Manager** | Feasibility | Practical implementation validation |
| **Customer** | Demand | Assortment breadth and depth |

### 2.2 Key Principles

1. **Sell-Through Optimization** - Primary objective for all decisions
2. **Temperature-Aware Clustering** - Climate-appropriate product assortment
3. **Constraint-Based Allocation** - Respect capacity and lifecycle limits
4. **Data-Driven Decisions** - Patterns from historical sales data

---

## 3. Client Requirements Status

### 3.1 Requirements by Phase

| Phase | Source | Total | ✅ | ⚠️ | ❌ |
|-------|--------|-------|-----|-----|-----|
| Phase 1: Initial Contract | FF Contract | 5 | 2 | 2 | 1 |
| Phase 2: Product Structure | FF Contract | 5 | 1 | 2 | 2 |
| Phase 3: Store-Product Matching | FF Contract | 3 | 1 | 1 | 1 |
| Phase 4: July Deliverables | Deliverables Doc | 8 | 3 | 3 | 2 |
| Phase 5: AB Test Prep | Meeting Notes | 6 | 1 | 3 | 2 |
| Phase 6: Latest Issues | Sept 2025 Issues | 6 | 2 | 2 | 2 |

### 3.2 Critical Unsatisfied Requirements

| Priority | ID | Requirement | Gap |
|----------|-----|-------------|-----|
| 🔴 1 | C-03 | Store Type Classification (Fashion/Basic) | Not implemented |
| 🔴 2 | C-04 | Store Capacity in Clustering | Not implemented |
| 🔴 3 | AB-03 | Silhouette Score ≥ 0.5 | Currently below target |
| 🔴 4 | D-C | Cluster Stability Report | Not implemented |

### 3.3 Partially Satisfied Requirements

| ID | Requirement | Current State | Missing |
|----|-------------|---------------|---------|
| C-05 | Dynamic Clustering | Seasonal snapshots exist | Automated triggers |
| AB-01 | Sell-Through KPI | Calculated in Step 30 | Not in rule generation |
| AB-02 | Store Attributes | 33% complete (temp only) | Style, Capacity |
| D-D | Back-test Pack | Historical data exists | Formal framework |

---

## 4. Data Intern Actionable Items

### 4.1 Scope Definition

As a data intern, I can work on **data preparation and feature engineering** (Steps 1-6). The following requirements fall within this scope:

| Requirement | Implementation Location | Complexity |
|-------------|------------------------|------------|
| C-03: Store Type | **Step 3** (matrix preparation) | Medium |
| C-04: Store Capacity | **Step 3** (matrix preparation) | Medium |
| AB-03: Silhouette ≥ 0.5 | **Step 6** (clustering) | High |
| D-C: Cluster Stability | **New analysis** (post Step 6) | Medium |

### 4.2 Why Step 3 (Not Step 6)?

**Key Insight:** Store Type and Capacity must be calculated in **Step 3** because:

```
Step 1: Raw sales data (has category info: Fashion vs Basic)
   ↓
Step 3: Creates matrix from raw data → ACCESS TO CATEGORY INFO HERE
   ↓
Step 6: Only sees normalized matrix (category info LOST)
```

Step 6 receives a matrix like:
```
str_code | SPU_001 | SPU_002 | SPU_003 | ...
---------|---------|---------|---------|----
31273    | 0.45    | 0.12    | 0.78    | ...
```

By Step 6, the original category breakdown (Fashion vs Basic) is no longer available.

---

## 5. Proposed Action Plan

### 5.1 Phase 1: Store Attribute Enrichment (Week 1)

#### Task 1.1: Store Type Classification (C-03)
**Location:** `src/step3_prepare_matrix.py`

```python
# Proposed Implementation
FASHION_CATEGORIES = ['牛仔裤', '卫衣', '外套', '夹克', '羽绒服', ...]
BASIC_CATEGORIES = ['T恤', '内衣', '袜子', '家居服', ...]

def calculate_store_type(sales_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Fashion/Basic ratio for each store.
    
    Returns:
        DataFrame with columns: str_code, fashion_ratio, store_type
        store_type: 'FASHION' (>0.6), 'BASIC' (<0.4), 'BALANCED' (0.4-0.6)
    """
    fashion_sales = sales_df[sales_df['cate_name'].isin(FASHION_CATEGORIES)]
    basic_sales = sales_df[sales_df['cate_name'].isin(BASIC_CATEGORIES)]
    
    fashion_by_store = fashion_sales.groupby('str_code')['spu_sales_amt'].sum()
    basic_by_store = basic_sales.groupby('str_code')['spu_sales_amt'].sum()
    
    total = fashion_by_store + basic_by_store
    fashion_ratio = fashion_by_store / total
    
    store_type = pd.cut(fashion_ratio, 
                        bins=[0, 0.4, 0.6, 1.0],
                        labels=['BASIC', 'BALANCED', 'FASHION'])
    
    return pd.DataFrame({
        'str_code': fashion_ratio.index,
        'fashion_ratio': fashion_ratio.values,
        'store_type': store_type.values
    })
```

**Output:** Add `fashion_ratio` and `store_type` columns to clustering matrix

#### Task 1.2: Store Capacity Estimation (C-04)
**Location:** `src/step3_prepare_matrix.py`

```python
def calculate_store_capacity(sales_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate capacity tier based on total sales volume.
    
    Returns:
        DataFrame with columns: str_code, total_sales, capacity_tier
        capacity_tier: 'S' (bottom 25%), 'M' (25-50%), 'L' (50-75%), 'XL' (top 25%)
    """
    total_sales = sales_df.groupby('str_code')['spu_sales_amt'].sum()
    
    capacity_tier = pd.qcut(total_sales, 
                            q=4, 
                            labels=['S', 'M', 'L', 'XL'])
    
    return pd.DataFrame({
        'str_code': total_sales.index,
        'total_sales': total_sales.values,
        'capacity_tier': capacity_tier.values
    })
```

**Output:** Add `total_sales` and `capacity_tier` columns to clustering matrix

### 5.2 Phase 2: Clustering Quality Improvement (Week 2)

#### Task 2.1: Silhouette Score Optimization (AB-03)
**Location:** `src/step6_cluster_analysis.py`

**Approach:**
1. Experiment with PCA components: 10, 20, 30, 50
2. Test different K values: 30, 40, 46, 50
3. Include new features (store_type, capacity_tier)
4. Document optimal configuration

**Target:** Silhouette Score ≥ 0.5

#### Task 2.2: Cluster Stability Report (D-C)
**Location:** New analysis script or Step 6 extension

```python
def calculate_cluster_stability(
    current_results: pd.DataFrame,
    previous_results: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate Jaccard similarity between clustering results across periods.
    
    Returns:
        DataFrame with cluster stability metrics
    """
    # For each cluster in current period
    # Find best matching cluster in previous period
    # Calculate Jaccard similarity = |A ∩ B| / |A ∪ B|
    
    stability_metrics = []
    for cluster_id in current_results['cluster_id'].unique():
        current_stores = set(current_results[current_results['cluster_id'] == cluster_id]['str_code'])
        
        best_jaccard = 0
        for prev_cluster in previous_results['cluster_id'].unique():
            prev_stores = set(previous_results[previous_results['cluster_id'] == prev_cluster]['str_code'])
            jaccard = len(current_stores & prev_stores) / len(current_stores | prev_stores)
            best_jaccard = max(best_jaccard, jaccard)
        
        stability_metrics.append({
            'cluster_id': cluster_id,
            'jaccard_similarity': best_jaccard,
            'is_stable': best_jaccard >= 0.7
        })
    
    return pd.DataFrame(stability_metrics)
```

**Output:** `cluster_stability_report.csv` with Jaccard similarity per cluster

---

## 6. Timeline

```
Week 1 (Jan 9-15)
├── Day 1-2: Store Type Classification
│   ├── Define Fashion/Basic category lists
│   ├── Implement calculate_store_type()
│   └── Add to Step 3 matrix output
│
├── Day 3-4: Store Capacity Estimation
│   ├── Implement calculate_store_capacity()
│   ├── Add to Step 3 matrix output
│   └── Test with sample data
│
└── Day 5: Integration & Testing
    ├── Run full Step 3 with new features
    └── Verify matrix output includes new columns

Week 2 (Jan 16-22)
├── Day 1-3: Silhouette Optimization
│   ├── Experiment with PCA components
│   ├── Test different K values
│   └── Document optimal configuration
│
├── Day 4-5: Cluster Stability Analysis
│   ├── Implement Jaccard similarity calculation
│   ├── Compare seasonal snapshots
│   └── Generate stability report
│
└── Day 5: Documentation & Review
    └── Update documentation with findings
```

---

## 7. Success Criteria

| Requirement | Success Metric | Target |
|-------------|----------------|--------|
| C-03: Store Type | `store_type` column in matrix | 100% stores classified |
| C-04: Store Capacity | `capacity_tier` column in matrix | 100% stores classified |
| AB-03: Silhouette | Silhouette score | ≥ 0.5 |
| D-C: Stability | Jaccard similarity report | Generated for 2+ periods |

---

## 8. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Category list incomplete | Incorrect store type classification | Review with domain expert |
| Silhouette target unachievable | Clustering quality concern | Document best achievable score |
| Historical data unavailable | Cannot calculate stability | Use available periods |
| Feature engineering impacts existing clusters | Downstream rule changes | Compare before/after results |

---

## 9. Questions for Discussion

1. **Category Classification:** Can we get a validated list of Fashion vs Basic categories?
2. **Capacity Definition:** Should capacity be based on sales volume, SKU count, or both?
3. **Silhouette Target:** Is 0.5 a hard requirement or a target to optimize toward?
4. **Stability Threshold:** What Jaccard similarity indicates "stable" cluster (0.7? 0.8?)?
5. **Timeline:** Is the 2-week timeline realistic given other priorities?

---

## 10. Appendix: Reference Documents

| Document | Location | Content |
|----------|----------|---------|
| Client Requirements Timeline | `docs/CLIENT_REQUIREMENTS_TIMELINE.md` | Full requirement history (Korean) |
| Requirements Verification | `docs/REQUIREMENTS_VERIFICATION_REPORT.md` | Gap analysis |
| Pipeline Output Structure | `docs/PIPELINE_OUTPUT_DATA_STRUCTURE.md` | Data flow documentation |
| Thinking Strategy | `protocols/FAST_FISH_THINKING_STRATEGY.md` | Analytical approach |
| Step 3 Documentation | `docs/workflow/04_STEP3_MATRIX.md` | Matrix creation details |

---

**Document Version:** 1.0  
**Author:** Data Intern  
**Next Review:** After meeting discussion
