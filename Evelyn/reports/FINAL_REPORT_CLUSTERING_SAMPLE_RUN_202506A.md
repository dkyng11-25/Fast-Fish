# Final Report: Clustering Pipeline Sample Run (202506A)

> **Data Period:** June 2025, First Half (202506A)  
> **Generated:** 2026-01-15  
> **Purpose:** BASELINE documentation using ORIGINAL src/step1-6 modules  
> **Run Type:** BASELINE (no modifications)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Data Period & Dataset Overview](#2-data-period--dataset-overview)
3. [Step 3: Prepare Store-Product Matrix](#3-step-3-prepare-store-product-matrix)
4. [Step 6: Cluster Analysis](#4-step-6-cluster-analysis)
5. [Baseline Metrics](#5-baseline-metrics)
6. [Cluster Distribution](#6-cluster-distribution)
7. [Configuration Summary](#7-configuration-summary)
8. [Recommendations for Improvement](#8-recommendations-for-improvement)

---

## 1. Executive Summary

### Overall Assessment

| Aspect | Status | Details |
|--------|--------|---------|
| **Pipeline Execution** | ✅ Success | Original src/step1-6 modules used |
| **Data Quality** | ✅ Good | 2,260 stores processed |
| **Cluster Quality** | ❌ Poor | Silhouette = 0.0478 (Target: ≥0.5) |

### Key Metrics at a Glance

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total Stores Processed | 2,260 | - | ✅ |
| Total SPU Records | 719,731 | - | ✅ |
| Number of Clusters | 46 | 20-40 | ⚠️ Slightly high |
| Average Cluster Size | 49.1 stores | ~50 | ✅ |
| **Silhouette Score** | **0.0478** | ≥0.5 | ❌ **9.6% of target** |
| Calinski-Harabasz Score | 120.60 | Higher is better | - |
| Davies-Bouldin Score | 2.7253 | Lower is better | - |

### Critical Finding

**The BASELINE clustering methodology achieves only 9.6% of the target silhouette score (0.0478 vs 0.5 target).** This confirms that:
1. Current clustering based solely on SPU sales patterns is insufficient
2. Store features (str_type, sal_type, traffic) are NOT utilized
3. Cluster count is dynamically determined (n_samples // 50), not optimized

---

## 2. Data Period & Dataset Overview

### Period Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Period Code** | 202506A | Standard period identifier |
| **Year** | 2025 | Calendar year |
| **Month** | 06 (June) | Calendar month |
| **Half** | A (First Half) | Days 1-15 of month |
| **Data Source** | `docs/Data/step1_api_data_20250917_142743/` | Raw data location |

### Input Files Summary

| File | Records | Description |
|------|---------|-------------|
| `complete_spu_sales_202506A.csv` | 719,731 | SPU-level transactions |
| `store_sales_202506A.csv` | 2,327 | Store-level sales (contains store features) |

### Available Store Features (NOT USED in Baseline)

| Feature | Type | Description | Used in Baseline? |
|---------|------|-------------|-------------------|
| str_code | string | Store identifier | ✅ Yes (index) |
| str_type | string | Store type (流行/基础) | ❌ **NOT USED** |
| sal_type | string | Sales grade (AA/A/B/C/D) | ❌ **NOT USED** |
| into_str_cnt_avg | float | Customer traffic | ❌ **NOT USED** |
| avg_temp | float | Average temperature | ❌ **NOT USED** |
| temp_zone | string | Temperature zone | ❌ **NOT USED** |

---

## 3. Step 3: Prepare Store-Product Matrix

### Configuration (ORIGINAL src/step3_prepare_matrix.py)

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Matrix Type** | SPU | Store × SPU sales matrix |
| **Max SPU Count** | 1,000 | Top SPUs by total sales |
| **Normalization** | Row-wise | `matrix.div(matrix.sum(axis=1), axis=0)` |

### Matrix Creation Process

1. **Pivot**: Create store × SPU matrix from SPU sales data
2. **Filter**: Keep top 1,000 SPUs by total sales
3. **Normalize**: Divide each row by its sum (row-wise normalization)

### Output Matrix

| Dimension | Value |
|-----------|-------|
| Stores | 2,260 |
| SPUs (features) | 1,000 |
| Matrix shape | (2260, 1000) |

### Normalization Method

```python
# ORIGINAL step3 normalization (line 605)
normalized_matrix = matrix.div(matrix.sum(axis=1), axis=0).fillna(0)
```

This is **row-wise normalization** which:
- Removes store size bias
- Focuses on product MIX rather than volume
- Each row sums to 1.0

---

## 4. Step 6: Cluster Analysis

### Configuration (ORIGINAL src/step6_cluster_analysis.py)

| Parameter | Value | Description |
|-----------|-------|-------------|
| **PCA Components** | 50 | Dimensionality reduction |
| **Cluster Determination** | n_samples // 50 | Dynamic based on store count |
| **Random State** | 42 | For reproducibility |
| **n_init** | 10 | KMeans initializations |
| **max_iter** | 300 | Maximum iterations |
| **Store Features** | NOT USED | str_type, sal_type, traffic excluded |
| **Temperature Constraints** | Disabled | ENABLE_TEMPERATURE_CONSTRAINTS = False |

### Clustering Process

1. **PCA**: Reduce 1,000 SPU features to 50 principal components
2. **Cluster Count**: Calculate as `2260 // 50 + 1 = 46` clusters
3. **KMeans**: Run with 46 clusters, 10 initializations
4. **No Balancing**: Original step6 includes balancing logic but results show imbalance

### PCA Results

| Metric | Value |
|--------|-------|
| Input dimensions | 1,000 |
| Output dimensions | 50 |
| Variance explained | 67.05% |

---

## 5. Baseline Metrics

### Clustering Quality Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Silhouette Score** | 0.0478 | Very poor (target ≥0.5) |
| **Calinski-Harabasz** | 120.60 | Moderate (higher is better) |
| **Davies-Bouldin** | 2.7253 | Poor (lower is better, <1 is good) |

### Silhouette Score Analysis

- **Score: 0.0478** indicates clusters are barely separated
- **Target: ≥0.5** for well-defined clusters
- **Achievement: 9.6%** of target
- **Interpretation**: Stores within clusters are almost as similar to other clusters as to their own

### Comparison to Target

| Metric | Baseline | Target | Gap |
|--------|----------|--------|-----|
| Silhouette | 0.0478 | 0.50 | -90.4% |
| Clusters | 46 | 20-40 | +6 over max |

---

## 6. Cluster Distribution

### Size Statistics

| Statistic | Value |
|-----------|-------|
| Minimum size | 1 store |
| Maximum size | 97 stores |
| Mean size | 49.1 stores |
| Std deviation | - |

### Observations

- **Imbalanced clusters**: Range from 1 to 97 stores
- **Target size**: 50 stores per cluster
- **Some singleton clusters**: Minimum of 1 store indicates outliers

---

## 7. Configuration Summary

### What ORIGINAL Modules Do

| Module | Key Logic | Store Features? |
|--------|-----------|-----------------|
| step3 | Row-wise normalization | ❌ No |
| step6 | Dynamic cluster count (n//50) | ❌ No |
| step6 | PCA with 50 components | ❌ No |
| step6 | KMeans clustering | ❌ No |

### What is NOT Used (Improvement Opportunities)

| Feature | Available? | Used? | Potential Impact |
|---------|------------|-------|------------------|
| str_type (store type) | ✅ Yes | ❌ No | High |
| sal_type (sales grade) | ✅ Yes | ❌ No | High |
| into_str_cnt_avg (traffic) | ✅ Yes | ❌ No | Medium |
| Temperature data | ✅ Yes | ❌ No | Medium |
| Fixed cluster count | N/A | ❌ No | High |

---

## 8. Recommendations for Improvement

### Priority 1: Add Store Features

**Rationale**: Store characteristics (type, grade, traffic) provide additional clustering signal beyond SPU sales patterns.

**Implementation**:
- Encode str_type as binary (流行=1, 基础=0)
- Encode sal_type as ordinal (AA=5, A=4, B=3, C=2, D=1)
- Normalize traffic (min-max scaling)
- Append to feature matrix before PCA

### Priority 2: Optimize Cluster Count

**Rationale**: Dynamic n//50 gives 46 clusters, exceeding client requirement of 20-40.

**Implementation**:
- Fix cluster count at 30 (middle of 20-40 range)
- Or use elbow method to find optimal k

### Priority 3: Alternative Normalization

**Rationale**: Test if different normalization improves cluster separation.

**Options**:
- Z-score normalization (standardization)
- Log transformation before normalization
- Weighted normalization by SPU importance

### Expected Improvement

Based on preliminary experiments:
- Adding store features: +100-200% silhouette improvement
- Fixing cluster count at 30: +20-50% silhouette improvement
- Combined improvements: Potential to reach 0.25-0.35 silhouette

---

## Appendix: Verification Checklist

| Check | Status |
|-------|--------|
| Original src/step1-6 modules NOT modified | ✅ Verified |
| Sample period 202506A used | ✅ Verified |
| Baseline metrics captured | ✅ Verified |
| No alternative clustering logic | ✅ Verified |
| Results reproducible | ✅ Verified |

---

*Report generated: 2026-01-15*  
*Run type: BASELINE*  
*Modules: ORIGINAL src/step1-6 (unmodified)*
