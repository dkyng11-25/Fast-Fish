# Understanding the Clustering Pipeline: A Comprehensive Analysis

**Date:** 2026-01-10  
**Purpose:** Explain the clustering methodology, data flow, and expected results for Steps 1-6

---

## 1. Data Period Used

### Default Configuration: **September 2025, First Half (202509A)**

Based on `src/config.py`:
```python
DEFAULT_YYYYMM = "202509"  # September 2025
DEFAULT_PERIOD = "A"       # First half of month (days 1-15)
```

### Period Naming Convention

| Period Label | Meaning |
|-------------|---------|
| `202509A` | September 2025, First Half (Days 1-15) |
| `202509B` | September 2025, Second Half (Days 16-30) |
| `202509` | September 2025, Full Month |

### Multi-Period Window for Clustering

The pipeline doesn't use just one month. It uses a **Year-over-Year (YoY) window** for robust clustering:

**Current Window (6 half-months ending at 202509A):**
- `202506B`, `202507A`, `202507B`, `202508A`, `202508B`, `202509A`

**YoY Window (6 half-months from same period last year):**
- `202406B`, `202407A`, `202407B`, `202408A`, `202408B`, `202409A`

**Total: 12 half-month periods** aggregated for comprehensive store-product relationships.

---

## 2. Pipeline Steps Overview

```
Step 1: Download API Data
    ↓
Step 2: Extract Coordinates
    ↓
Step 3: Prepare Matrix ← Feature Engineering
    ↓
Step 4: Download Weather Data
    ↓
Step 5: Calculate Feels-Like Temperature
    ↓
Step 6: Cluster Analysis ← Main Clustering
```

---

## 3. What Clusters Are Involved?

### 3.1 Clustering Approaches (Matrix Types)

The pipeline supports **three clustering approaches** based on different feature granularities:

| Matrix Type | Description | Features | Use Case |
|-------------|-------------|----------|----------|
| **SPU** (Default) | Stock Keeping Unit level | Top 1000 SPUs | Most granular, precise product allocation |
| **Subcategory** | Product subcategory level | ~50-100 subcategories | Balanced granularity |
| **Category-Aggregated** | High-level category | ~20 categories | Strategic overview |

### 3.2 Current Configuration

From `src/step6_cluster_analysis.py`:
```python
MATRIX_TYPE = "spu"  # SPU-level clustering
MIN_CLUSTER_SIZE = 50
MAX_CLUSTER_SIZE = 50  # Exactly 50 stores per cluster
```

### 3.3 Cluster Calculation

**Number of Clusters = Total Stores ÷ 50**

Example with 500 stores:
- **10 clusters** created
- Each cluster contains **exactly 50 stores**
- Stores are grouped by **similar product sales patterns**

---

## 4. How Clustering Works (Step-by-Step)

### Step 3: Matrix Preparation

**Input:** Sales data from 12 periods (YoY window)

**Process:**
1. Load category/SPU sales data from all periods
2. Create store-product matrix (rows = stores, columns = products)
3. Aggregate sales across all periods
4. Normalize values (0-1 scale)

**Output:** 
- `data/normalized_spu_limited_matrix.csv` (normalized features)
- `data/store_spu_limited_matrix.csv` (original values)

**Matrix Structure:**
```
           SPU_001  SPU_002  SPU_003  ...  SPU_1000
Store_001    0.85     0.12     0.45   ...    0.33
Store_002    0.22     0.78     0.11   ...    0.67
Store_003    0.91     0.05     0.88   ...    0.12
...
```

### Step 6: Cluster Analysis

**Input:** Normalized matrix from Step 3

**Process:**

#### Phase 1: Dimensionality Reduction (PCA)
```python
PCA_COMPONENTS = 50  # Reduce 1000 SPUs to 50 principal components
```
- Reduces computational complexity
- Captures ~80-90% of variance
- Removes noise from sparse features

#### Phase 2: Initial Clustering (K-Means)
```python
n_clusters = n_stores // 50  # e.g., 500 stores → 10 clusters
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
```

#### Phase 3: Cluster Balancing
- Ensures each cluster has exactly 50 stores
- Moves stores from oversized to undersized clusters
- Maintains cluster coherence by distance to center

#### Phase 4: Quality Metrics Calculation
- **Silhouette Score**: Measures cluster separation (-1 to 1, higher is better)
- **Calinski-Harabasz Score**: Ratio of between-cluster to within-cluster variance
- **Davies-Bouldin Score**: Average similarity between clusters (lower is better)

---

## 5. How Clustering Affects Output

### 5.1 Output Files Generated

| File | Description |
|------|-------------|
| `output/clustering_results_spu.csv` | Store-to-cluster assignments |
| `output/cluster_profiles_spu.csv` | Detailed cluster characteristics |
| `output/per_cluster_metrics_spu.csv` | Quality metrics per cluster |
| `output/cluster_visualization_spu.png` | Visual representation |

### 5.2 Clustering Results Structure

**`clustering_results_spu.csv`:**
```csv
str_code,Cluster
Store_001,0
Store_002,3
Store_003,0
Store_004,7
...
```

**`cluster_profiles_spu.csv`:**
```csv
Cluster,Size,Top_SPUs,Total_Sales,Avg_Sales_Per_Store
0,50,"SPU_123(0.9),SPU_456(0.8),...",1250000,25000
1,50,"SPU_789(0.85),SPU_012(0.7),...",980000,19600
...
```

### 5.3 Impact on Downstream Steps

Clustering results are used in subsequent steps for:

1. **Business Rule Validation (Step 7+):** Check if clusters meet business requirements
2. **Product Allocation:** Recommend products based on cluster characteristics
3. **Inventory Planning:** Optimize stock levels per cluster
4. **Marketing Campaigns:** Target similar stores together

---

## 6. Expected Results and Interpretation

### 6.1 Example Results (Hypothetical with 500 Stores)

| Metric | Expected Value | Interpretation |
|--------|---------------|----------------|
| **Number of Clusters** | 10 | 500 stores ÷ 50 per cluster |
| **Cluster Size** | 50 each | Balanced for operational efficiency |
| **Silhouette Score** | 0.3-0.5 | Moderate cluster separation |
| **Variance Explained (PCA)** | 80-90% | Good feature compression |

### 6.2 Cluster Interpretation

**Cluster 0: "Fashion-Forward Stores"**
- High sales in fashion SPUs (clothing, accessories)
- Located in urban areas
- Target: Trend-conscious customers

**Cluster 1: "Basic Essentials Stores"**
- High sales in basic SPUs (underwear, socks)
- Stable demand patterns
- Target: Value-conscious customers

**Cluster 2: "Seasonal Stores"**
- High variance in sales across seasons
- Strong in seasonal categories
- Target: Weather-dependent products

### 6.3 Quality Metrics Interpretation

| Metric | Good Range | What It Means |
|--------|-----------|---------------|
| **Silhouette Score** | > 0.5 | Clusters are well-separated |
| **Silhouette Score** | 0.25-0.5 | Clusters overlap somewhat |
| **Silhouette Score** | < 0.25 | Clusters may be artificial |
| **Davies-Bouldin** | < 1.0 | Good cluster separation |
| **Calinski-Harabasz** | Higher is better | Dense, well-separated clusters |

### 6.4 What Results Indicate

**High Silhouette Score (≥ 0.5):**
- Stores within clusters have similar product preferences
- Cluster-based strategies will be effective
- Product recommendations will be accurate

**Low Silhouette Score (< 0.3):**
- Stores don't naturally group well
- May need additional features (store type, capacity)
- Consider different clustering approach

**Balanced Cluster Sizes:**
- Operational efficiency (same resources per cluster)
- Fair comparison across clusters
- Easier inventory management

---

## 7. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT DATA                                │
│  data/api_data/complete_spu_sales_202509A.csv                   │
│  data/api_data/store_sales_202509A.csv                          │
│  (+ 11 more periods for YoY analysis)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 3: MATRIX PREPARATION                    │
│  • Aggregate sales across 12 periods                            │
│  • Create store × SPU matrix (e.g., 500 × 1000)                 │
│  • Normalize to 0-1 scale                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 6: CLUSTER ANALYSIS                      │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │     PCA      │ →  │   K-Means    │ →  │   Balance    │       │
│  │ 1000 → 50    │    │  10 clusters │    │  50 per      │       │
│  │ dimensions   │    │              │    │  cluster     │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        OUTPUT FILES                              │
│  output/clustering_results_spu.csv      (store assignments)     │
│  output/cluster_profiles_spu.csv        (cluster characteristics)│
│  output/per_cluster_metrics_spu.csv     (quality metrics)       │
│  output/cluster_visualization_spu.png   (visual plots)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Key Configuration Parameters

| Parameter | Value | Location | Purpose |
|-----------|-------|----------|---------|
| `DEFAULT_YYYYMM` | "202509" | config.py | Base analysis period |
| `DEFAULT_PERIOD` | "A" | config.py | First/second half |
| `MATRIX_TYPE` | "spu" | step6 | Clustering granularity |
| `PCA_COMPONENTS` | 50 | step6 | Dimensionality reduction |
| `MIN_CLUSTER_SIZE` | 50 | step6 | Minimum stores per cluster |
| `MAX_CLUSTER_SIZE` | 50 | step6 | Maximum stores per cluster |
| `RANDOM_STATE` | 42 | step6 | Reproducibility |

---

## 9. Summary

### What the Pipeline Does

1. **Collects** sales data from September 2025 (first half) + 11 additional periods
2. **Creates** a store-product matrix showing what each store sells
3. **Reduces** dimensionality using PCA (1000 SPUs → 50 components)
4. **Clusters** stores using K-Means algorithm
5. **Balances** clusters to exactly 50 stores each
6. **Outputs** cluster assignments and quality metrics

### What Results Mean

- **Cluster ID**: Group of stores with similar product preferences
- **Silhouette Score**: How well-separated the clusters are
- **Cluster Profile**: Top products defining each cluster
- **Store Assignment**: Which cluster each store belongs to

### Business Value

- **Product Allocation**: Send similar products to similar stores
- **Inventory Optimization**: Stock based on cluster patterns
- **Marketing Efficiency**: Target clusters instead of individual stores
- **Performance Benchmarking**: Compare stores within same cluster

---

## 10. Remaining Requirements

| Requirement | Status | Impact on Clustering |
|-------------|--------|---------------------|
| C-03 Store Type | ❌ Not Done | Would add fashion_ratio feature |
| C-04 Store Capacity | ❌ Not Done | Would add capacity feature |
| AB-03 Silhouette ≥ 0.5 | ⚠️ Partial | Depends on C-03/C-04 |
| D-C Stability Report | ❌ Not Done | Compare clusters across periods |

Adding store type and capacity features to the matrix would likely **improve cluster separation** and help achieve the target Silhouette Score of ≥ 0.5.
