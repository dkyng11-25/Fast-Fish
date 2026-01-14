# Parameter Groups Definition for Weight Tuning Experiments

**Project:** Fast Fish Clustering Optimization  
**Date:** January 14, 2026  
**Context:** Post-C3 baseline validation (Silhouette ~0.27-0.32)

---

## Overview

This document defines the parameter groups used in weight tuning experiments to optimize the Silhouette score for store clustering. The goal is to identify which feature groups most affect clustering quality and find optimal weight allocations.

---

## Parameter Group Definitions

| Group ID | Group Name | Features Included | Source | Preprocessing |
|----------|------------|-------------------|--------|---------------|
| **SPU** | SPU Behavior Group | PCA components from row-normalized SPU sales matrix | `data/normalized_spu_limited_matrix.csv` | PCA (50-100 components) |
| **STYLE** | Store Style Group | `fashion_ratio`, `basic_ratio`, `store_type_encoded` | Step 22 enrichment | StandardScaler |
| **CAPACITY** | Store Capacity Group | `estimated_rack_capacity`, `size_tier_encoded`, `sku_diversity` | Step 22 enrichment | StandardScaler |
| **TRAFFIC** | Traffic/Conversion Group | `total_sales_amt`, `total_sales_qty`, `sales_per_sku` | Step 22 enrichment | StandardScaler |
| **TEMP** | Temperature Feature Group | `feels_like_temperature`, `temperature_band_encoded` | Step 5 output | StandardScaler |

---

## Detailed Group Descriptions

### 1. SPU Behavior Group (w_spu)

**What it is:**  
Principal Component Analysis (PCA) components derived from the row-normalized SPU sales matrix. Each store is represented by its sales pattern across the top 1000 SPUs.

**Why it affects Silhouette (distance geometry):**  
- SPU features capture *what* each store sells, not *how much*
- Row normalization removes store size bias, focusing on product mix similarity
- PCA reduces dimensionality while preserving variance structure
- Stores with similar product portfolios cluster together in PCA space

**Fast Fish Requirement Alignment:**
| Requirement | Relevant? | Notes |
|-------------|-----------|-------|
| Silhouette ≥ 0.5 | ✅ Primary driver | Core feature for clustering quality |
| Temperature 5°C rule | ❌ No | Not temperature-related |
| Store type | ⚠️ Indirect | Product mix correlates with store type |
| Store capacity | ⚠️ Indirect | Larger stores may have different SPU patterns |

---

### 2. Store Style Group (w_style)

**What it is:**  
Features describing the store's fashion vs. basic product orientation:
- `fashion_ratio`: Percentage of sales from fashion items (0-100)
- `basic_ratio`: Percentage of sales from basic items (0-100)
- `store_type_encoded`: Categorical encoding (Fashion=2, Balanced=1, Basic=0)

**Why it affects Silhouette (distance geometry):**  
- Creates clear separation between fashion-focused and basic-focused stores
- Reduces overlap between fundamentally different store types
- Adds business-meaningful dimensions to the feature space

**Fast Fish Requirement Alignment:**
| Requirement | Relevant? | Notes |
|-------------|-----------|-------|
| Silhouette ≥ 0.5 | ✅ Yes | Improves cluster separation |
| Temperature 5°C rule | ❌ No | Not temperature-related |
| Store type | ✅ **Required** | Directly addresses C-03 requirement |
| Store capacity | ❌ No | Not capacity-related |

---

### 3. Store Capacity Group (w_capacity)

**What it is:**  
Features describing the store's size and operational capacity:
- `estimated_rack_capacity`: Estimated number of rack units
- `size_tier_encoded`: Large=2, Medium=1, Small=0
- `sku_diversity`: Number of unique SKUs sold

**Why it affects Silhouette (distance geometry):**  
- Prevents mixing of large and small stores in same cluster
- Capacity-similar stores have similar operational constraints
- SKU diversity indicates store complexity

**Fast Fish Requirement Alignment:**
| Requirement | Relevant? | Notes |
|-------------|-----------|-------|
| Silhouette ≥ 0.5 | ✅ Yes | Adds meaningful separation dimension |
| Temperature 5°C rule | ❌ No | Not temperature-related |
| Store type | ⚠️ Indirect | Capacity may correlate with type |
| Store capacity | ✅ **Required** | Directly addresses C-04 requirement |

---

### 4. Traffic/Conversion Group (w_traffic)

**What it is:**  
Features describing store sales volume and efficiency:
- `total_sales_amt`: Total sales amount in period
- `total_sales_qty`: Total quantity sold
- `sales_per_sku`: Average sales per SKU (efficiency metric)

**Why it affects Silhouette (distance geometry):**  
- Groups stores by sales velocity and performance tier
- High-traffic stores may have different inventory needs
- Efficiency metrics capture operational patterns

**Fast Fish Requirement Alignment:**
| Requirement | Relevant? | Notes |
|-------------|-----------|-------|
| Silhouette ≥ 0.5 | ⚠️ Moderate | May add noise if not normalized properly |
| Temperature 5°C rule | ❌ No | Not temperature-related |
| Store type | ⚠️ Indirect | Traffic patterns vary by type |
| Store capacity | ⚠️ Indirect | Larger stores typically have more traffic |

---

### 5. Temperature Feature Group (w_temp)

**What it is:**  
Features describing the store's climate zone:
- `feels_like_temperature`: Average feels-like temperature for the period
- `temperature_band_encoded`: Numeric encoding of temperature band (e.g., 15°C, 20°C)

**Why it affects Silhouette (distance geometry):**  
- **WARNING:** Temperature constraint (5°C rule) severely degrades Silhouette
- When used as hard constraint: Silhouette drops from ~0.27 to negative values
- When used as soft feature: May add useful climate-based separation

**Fast Fish Requirement Alignment:**
| Requirement | Relevant? | Notes |
|-------------|-----------|-------|
| Silhouette ≥ 0.5 | ❌ **Negative impact** | Constraint destroys clustering quality |
| Temperature 5°C rule | ✅ **Required** | Must be evaluated separately |
| Store type | ❌ No | Not type-related |
| Store capacity | ❌ No | Not capacity-related |

---

## Summary Table: Group Impact Assessment

| Group | Expected Silhouette Impact | Required by Fast Fish | Recommended Weight Range |
|-------|---------------------------|----------------------|-------------------------|
| **SPU** | ✅ High (primary driver) | Indirect | 0.50 - 0.80 |
| **STYLE** | ✅ Medium-High | Yes (C-03) | 0.10 - 0.30 |
| **CAPACITY** | ✅ Medium | Yes (C-04) | 0.05 - 0.20 |
| **TRAFFIC** | ⚠️ Low-Medium | No | 0.00 - 0.10 |
| **TEMP** | ❌ Negative (as constraint) | Yes (5°C rule) | 0.00 - 0.05 |

---

## Experimental Strategy

1. **Start with SPU-heavy weights** (0.70, 0.20, 0.10, 0.00, 0.00)
2. **Gradually shift weight to STYLE and CAPACITY** to meet requirements
3. **Keep TRAFFIC and TEMP low** unless data shows benefit
4. **Evaluate temperature constraint separately** (not during optimization)

---

## Data Availability Notes

| Feature | Available | Source File | Notes |
|---------|-----------|-------------|-------|
| SPU PCA | ✅ Yes | `data/normalized_spu_limited_matrix.csv` | Requires matrix file |
| fashion_ratio | ✅ Yes | Step 22 output | From store enrichment |
| basic_ratio | ✅ Yes | Step 22 output | From store enrichment |
| estimated_rack_capacity | ✅ Yes | Step 22 output | Estimated from sales |
| feels_like_temperature | ⚠️ Conditional | Step 5 output | May not exist for all stores |
| temperature_band | ⚠️ Conditional | Step 5 output | May not exist for all stores |

---

*Document prepared for Fast Fish Clustering Optimization Project*
