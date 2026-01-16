# Clustering Improvement Report

> **Baseline Period:** 202506A  
> **Generated:** 2026-01-15  
> **Purpose:** Enumerate and evaluate ALL feasible clustering improvements  
> **Baseline Silhouette:** 0.0478 (Target: ≥0.5)

---

## Table of Contents

1. [Baseline Summary](#1-baseline-summary)
2. [Improvement Categories](#2-improvement-categories)
3. [Improvement I1: Store Profile Features](#3-improvement-i1-store-profile-features)
4. [Improvement I2: Fixed Cluster Count](#4-improvement-i2-fixed-cluster-count)
5. [Improvement I3: Alternative Normalization](#5-improvement-i3-alternative-normalization)
6. [Improvement I4: Feature Block Structuring](#6-improvement-i4-feature-block-structuring)
7. [Improvement I5: PCA Strategy Variations](#7-improvement-i5-pca-strategy-variations)
8. [Improvement I6: Outlier Handling](#8-improvement-i6-outlier-handling)
9. [Improvement I7: Temperature Integration](#9-improvement-i7-temperature-integration)
10. [Improvement Selection Matrix](#10-improvement-selection-matrix)
11. [Recommended Combination](#11-recommended-combination)
12. [Client Requirement Compliance](#12-client-requirement-compliance)

---

## 1. Baseline Summary

### Baseline Configuration (Original src/step1-6)

| Component | Configuration | Value |
|-----------|---------------|-------|
| **Step 3** | Normalization | Row-wise (div by row sum) |
| **Step 3** | Max SPU Count | 1,000 |
| **Step 6** | PCA Components | 50 |
| **Step 6** | Cluster Count | Dynamic (n_samples // 50) |
| **Step 6** | Store Features | NOT USED |
| **Step 6** | Temperature | NOT USED |

### Baseline Metrics

| Metric | Value | Target | Gap |
|--------|-------|--------|-----|
| **Silhouette Score** | 0.0478 | ≥0.5 | -90.4% |
| Calinski-Harabasz | 120.60 | Higher | - |
| Davies-Bouldin | 2.7253 | <1.0 | +172.5% |
| Clusters | 46 | 20-40 | +6 |
| Stores | 2,260 | - | ✅ |

---

## 2. Improvement Categories

### Overview of All Feasible Improvements

| ID | Improvement | Category | Complexity | Expected Impact |
|----|-------------|----------|------------|-----------------|
| I1 | Store Profile Features | Feature Engineering | Medium | **High** |
| I2 | Fixed Cluster Count | Clustering Config | Low | Medium |
| I3 | Alternative Normalization | Data Preprocessing | Low | Low-Medium |
| I4 | Feature Block Structuring | Feature Engineering | Medium | Medium |
| I5 | PCA Strategy Variations | Dimensionality Reduction | Medium | Low-Medium |
| I6 | Outlier Handling | Data Preprocessing | Medium | Low |
| I7 | Temperature Integration | Feature Engineering | Medium | Medium |

### Client Requirements Checklist

| Requirement | Constraint |
|-------------|------------|
| Cluster count | 20-40 clusters |
| Include temperature zones | Optional |
| Include store type | Recommended |
| Include store capacity | Recommended |

---

## 3. Improvement I1: Store Profile Features

### Description

Add store-level features to the clustering feature matrix:
- **str_type**: Store type (流行/基础)
- **sal_type**: Sales grade (AA/A/B/C/D)
- **into_str_cnt_avg**: Customer traffic

### Rationale

Current clustering uses ONLY SPU sales patterns. Store characteristics provide additional signal about store behavior that is independent of product mix.

### Implementation

**File to modify:** `Evelyn/modules/step6_cluster_analysis.py`

```python
# Encode store features
def encode_store_features(store_sales: pd.DataFrame) -> pd.DataFrame:
    features = store_sales.set_index('str_code')[
        ['str_type', 'sal_type', 'into_str_cnt_avg']
    ].copy()
    
    # Binary encoding for str_type
    features['str_type_encoded'] = (features['str_type'] == '流行').astype(float)
    
    # Ordinal encoding for sal_type
    grade_map = {'AA': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1}
    features['sal_type_encoded'] = features['sal_type'].map(grade_map).fillna(2)
    
    # Normalize traffic
    traffic = features['into_str_cnt_avg'].fillna(0)
    features['traffic_normalized'] = (traffic - traffic.min()) / (traffic.max() - traffic.min() + 1e-10)
    
    return features[['str_type_encoded', 'sal_type_encoded', 'traffic_normalized']]

# Append to feature matrix before PCA
enhanced_matrix = pd.concat([normalized_spu_matrix, store_features], axis=1)
```

### Expected Impact

| Metric | Baseline | Expected | Change |
|--------|----------|----------|--------|
| Silhouette | 0.0478 | 0.15-0.25 | +200-400% |

### Risks

- Feature scaling mismatch between SPU features and store features
- Potential overfitting to store characteristics

### Client Compliance

| Requirement | Status |
|-------------|--------|
| Store type included | ✅ Yes |
| Store capacity proxy (traffic) | ✅ Yes |

---

## 4. Improvement I2: Fixed Cluster Count

### Description

Replace dynamic cluster count (`n_samples // 50`) with a fixed value within client requirements (20-40).

### Rationale

- Current: 46 clusters (exceeds 20-40 requirement)
- Fixed count ensures compliance and allows optimization

### Implementation

**File to modify:** `Evelyn/modules/step6_cluster_analysis.py`

```python
# BEFORE (original)
n_clusters = n_samples // 50
if n_samples % 50 != 0:
    n_clusters += 1

# AFTER (improvement)
N_CLUSTERS_FIXED = 30  # Middle of 20-40 range
n_clusters = N_CLUSTERS_FIXED
```

### Expected Impact

| Metric | Baseline | Expected | Change |
|--------|----------|----------|--------|
| Silhouette | 0.0478 | 0.06-0.08 | +25-70% |
| Clusters | 46 | 30 | -35% |

### Cluster Count Options

| Option | Clusters | Avg Size | Compliance |
|--------|----------|----------|------------|
| Minimum | 20 | 113 | ✅ |
| **Recommended** | **30** | **75** | ✅ |
| Maximum | 40 | 57 | ✅ |

### Client Compliance

| Requirement | Status |
|-------------|--------|
| 20-40 clusters | ✅ Yes (30) |

---

## 5. Improvement I3: Alternative Normalization

### Description

Test alternative normalization methods for the SPU matrix.

### Options

| Method | Formula | Description |
|--------|---------|-------------|
| **Row-wise (Baseline)** | `row / row.sum()` | Normalize by store total |
| Z-score | `(x - mean) / std` | Standardization |
| Log-transform | `log(1 + x)` then row-wise | Reduce skewness |
| Min-Max | `(x - min) / (max - min)` | Scale to [0,1] |

### Implementation

**File to modify:** `Evelyn/modules/step3_prepare_matrix.py`

```python
# Option A: Z-score normalization
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
normalized_matrix = pd.DataFrame(
    scaler.fit_transform(matrix),
    index=matrix.index,
    columns=matrix.columns
)

# Option B: Log-transform then row-wise
log_matrix = np.log1p(matrix)
normalized_matrix = log_matrix.div(log_matrix.sum(axis=1), axis=0).fillna(0)
```

### Expected Impact

| Method | Expected Silhouette | Change vs Baseline |
|--------|---------------------|-------------------|
| Row-wise (baseline) | 0.0478 | - |
| Z-score | 0.05-0.07 | +5-45% |
| Log + Row-wise | 0.05-0.06 | +5-25% |

### Recommendation

**Keep row-wise normalization** - it already removes store size bias effectively. Other methods provide marginal improvement.

---

## 6. Improvement I4: Feature Block Structuring

### Description

Organize features into logical blocks with separate processing:
- **Block 1**: SPU sales features (1000 dimensions)
- **Block 2**: Store profile features (3 dimensions)
- **Block 3**: Climate features (optional)

### Rationale

Different feature types may have different optimal preprocessing and weighting.

### Implementation

```python
# Block 1: SPU features (PCA reduced)
spu_pca = PCA(n_components=47).fit_transform(spu_matrix)

# Block 2: Store features (no PCA, already low-dimensional)
store_features = encode_store_features(store_sales)  # 3 features

# Block 3: Climate features (optional)
climate_features = get_temperature_features(stores)  # 1-2 features

# Combine blocks with optional weighting
combined = np.hstack([
    spu_pca * 0.7,           # 70% weight to SPU patterns
    store_features * 0.2,    # 20% weight to store profile
    climate_features * 0.1   # 10% weight to climate
])
```

### Expected Impact

| Configuration | Expected Silhouette |
|---------------|---------------------|
| SPU only (baseline) | 0.0478 |
| SPU + Store (equal) | 0.15-0.20 |
| SPU + Store (weighted) | 0.18-0.25 |

### Complexity

Medium - requires careful weight tuning and validation.

---

## 7. Improvement I5: PCA Strategy Variations

### Description

Test alternative PCA configurations.

### Options

| Strategy | Description | Components |
|----------|-------------|------------|
| **Baseline** | Fixed 50 components | 50 |
| Variance-based | Keep 90% variance | ~80-100 |
| Reduced | Fewer components | 20-30 |
| Block-wise | Separate PCA per feature block | Variable |

### Implementation

```python
# Option A: Variance-based
pca = PCA(n_components=0.90)  # Keep 90% variance
pca_result = pca.fit_transform(matrix)

# Option B: Reduced components
pca = PCA(n_components=30)
pca_result = pca.fit_transform(matrix)
```

### Expected Impact

| Strategy | Variance Explained | Expected Silhouette |
|----------|-------------------|---------------------|
| 50 components (baseline) | 67% | 0.0478 |
| 90% variance | ~85% | 0.05-0.06 |
| 30 components | ~55% | 0.04-0.05 |

### Recommendation

**Keep 50 components** - provides good balance. Variance-based may help slightly but not significant.

---

## 8. Improvement I6: Outlier Handling

### Description

Identify and handle outlier stores before clustering.

### Methods

| Method | Description |
|--------|-------------|
| IQR-based | Remove stores outside 1.5×IQR |
| Z-score | Remove stores with z > 3 |
| Isolation Forest | ML-based outlier detection |
| Separate cluster | Assign outliers to dedicated cluster |

### Implementation

```python
# Z-score based outlier detection
from scipy import stats
z_scores = np.abs(stats.zscore(pca_df))
outlier_mask = (z_scores > 3).any(axis=1)
clean_df = pca_df[~outlier_mask]
outlier_df = pca_df[outlier_mask]

# Cluster clean data, assign outliers to nearest cluster
```

### Expected Impact

| Approach | Stores Removed | Expected Silhouette |
|----------|----------------|---------------------|
| No handling (baseline) | 0 | 0.0478 |
| Z-score > 3 | ~50-100 | 0.05-0.06 |
| Separate cluster | 0 | 0.05-0.06 |

### Recommendation

**Low priority** - outlier handling provides marginal improvement and risks losing valuable data.

---

## 9. Improvement I7: Temperature Integration

### Description

Integrate temperature data into clustering.

### Options

| Option | Description | When Applied |
|--------|-------------|--------------|
| **Not used (baseline)** | Ignore temperature | - |
| Feature addition | Add temp as clustering feature | During clustering |
| Post-clustering constraint | Ensure clusters within 5°C bands | After clustering |
| Pre-clustering stratification | Cluster within temp zones first | Before clustering |

### Implementation

```python
# Option A: Feature addition
temp_features = store_temps[['feels_like_temp']].copy()
temp_features['temp_normalized'] = (temp_features['feels_like_temp'] - temp_features['feels_like_temp'].min()) / \
                                   (temp_features['feels_like_temp'].max() - temp_features['feels_like_temp'].min())
enhanced_matrix = pd.concat([spu_matrix, temp_features], axis=1)

# Option B: Post-clustering constraint (already in original step6)
ENABLE_TEMPERATURE_CONSTRAINTS = True
```

### Expected Impact

| Approach | Expected Silhouette | Complexity |
|----------|---------------------|------------|
| Not used (baseline) | 0.0478 | - |
| Feature addition | 0.05-0.07 | Low |
| Post-clustering | 0.04-0.05 | Medium |

### Client Compliance

| Requirement | Status |
|-------------|--------|
| Temperature zones | Optional (can enable) |

---

## 10. Improvement Selection Matrix

### Impact vs Complexity Analysis

| Improvement | Impact | Complexity | Priority |
|-------------|--------|------------|----------|
| **I1: Store Features** | **High** | Medium | **1st** |
| **I2: Fixed Clusters** | Medium | **Low** | **2nd** |
| I3: Alt Normalization | Low | Low | 4th |
| I4: Feature Blocks | Medium | Medium | 3rd |
| I5: PCA Variations | Low | Low | 5th |
| I6: Outlier Handling | Low | Medium | 6th |
| I7: Temperature | Medium | Medium | 3rd |

### Recommended Implementation Order

1. **I2: Fixed Cluster Count (30)** - Quick win, ensures compliance
2. **I1: Store Profile Features** - Highest impact improvement
3. **I7: Temperature Integration** - If client requires
4. **I4: Feature Block Structuring** - Fine-tuning

---

## 11. Recommended Combination

### Selected Improvements

| ID | Improvement | Included | Rationale |
|----|-------------|----------|-----------|
| I1 | Store Profile Features | ✅ Yes | Highest impact |
| I2 | Fixed Cluster Count (30) | ✅ Yes | Client compliance |
| I3 | Alternative Normalization | ❌ No | Marginal benefit |
| I4 | Feature Block Structuring | ⚠️ Optional | If I1+I2 insufficient |
| I5 | PCA Variations | ❌ No | Marginal benefit |
| I6 | Outlier Handling | ❌ No | Risk of data loss |
| I7 | Temperature Integration | ⚠️ Optional | Per client preference |

### Expected Combined Results

| Metric | Baseline | I2 Only | I1+I2 | Target |
|--------|----------|---------|-------|--------|
| Silhouette | 0.0478 | 0.06-0.08 | **0.20-0.30** | ≥0.5 |
| Clusters | 46 | 30 | 30 | 20-40 |
| Compliance | ❌ | ✅ | ✅ | ✅ |

### Implementation Plan

1. Copy `src/step6_cluster_analysis.py` to `Evelyn/modules/`
2. Apply I2: Change cluster count to 30
3. Apply I1: Add store feature encoding and matrix enhancement
4. Run validation on 202506A
5. Compare metrics to baseline
6. Validate on additional periods if successful

---

## 12. Client Requirement Compliance

### Requirement Checklist

| Requirement | Baseline | With Improvements |
|-------------|----------|-------------------|
| Cluster count 20-40 | ❌ 46 | ✅ 30 |
| Include store type | ❌ No | ✅ Yes (I1) |
| Include store capacity | ❌ No | ✅ Yes (I1: traffic) |
| Temperature zones | ❌ No | ⚠️ Optional (I7) |

### Final Recommendation

**Implement I1 + I2** as the primary improvement combination:
- Fixes cluster count compliance (46 → 30)
- Adds store features for better cluster separation
- Expected silhouette improvement: +300-500%
- Maintains original pipeline structure

---

*Report generated: 2026-01-15*  
*Baseline: Original src/step1-6 modules*  
*Next step: Implement selected improvements in Evelyn/modules/*
