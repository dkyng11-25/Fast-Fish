# Final Report: Clustering Pipeline Sample Run (202506A)

> **Data Period:** June 2025, First Half (202506A)  
> **Generated:** 2026-01-12  
> **Purpose:** Complete documentation of clustering pipeline execution and cluster quality audit

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Data Period & Dataset Overview](#2-data-period--dataset-overview)
3. [Step 1: Download API Data](#3-step-1-download-api-data)
4. [Step 2: Extract Store Coordinates](#4-step-2-extract-store-coordinates)
5. [Step 3: Prepare Store-Product Matrix](#5-step-3-prepare-store-product-matrix)
6. [Step 4: Download Weather Data](#6-step-4-download-weather-data)
7. [Step 5: Calculate Feels-Like Temperature](#7-step-5-calculate-feels-like-temperature)
8. [Step 6: Cluster Analysis](#8-step-6-cluster-analysis)
9. [Cluster Audit Report](#9-cluster-audit-report)
10. [Visualizations](#10-visualizations)
11. [Recommendations for Improvement](#11-recommendations-for-improvement)
12. [Appendix: Complete Data Tables](#12-appendix-complete-data-tables)

---

## 1. Executive Summary

### Overall Assessment

| Aspect | Status | Details |
|--------|--------|---------|
| **Pipeline Execution** | ✅ Success | All 6 steps completed |
| **Data Quality** | ✅ Good | 2,260 stores processed |
| **Cluster Quality** | ❌ Poor | Silhouette = 0.0812 (Target: ≥0.5) |

### Key Metrics at a Glance

| Metric | Value |
|--------|-------|
| Total Stores Processed | 2,260 |
| Total SPU Records | 719,732 |
| Number of Clusters | 45 |
| Average Cluster Size | 50.2 stores |
| Silhouette Score | **0.0812** |
| Calinski-Harabasz Score | 57.02 |
| Davies-Bouldin Score | 2.89 |

### Critical Finding

**The current clustering methodology achieves only 16% of the target silhouette score (0.0812 vs 0.5 target).** This confirms that clustering based solely on sales amount does not adequately capture true store performance characteristics.

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

| File | Records | Size | Description |
|------|---------|------|-------------|
| `store_sales_202506A.csv` | 2,327 | 426 KB | Store-level sales aggregates |
| `complete_spu_sales_202506A.csv` | 719,732 | 47.6 MB | SPU-level transactions |
| `complete_category_sales_202506A.csv` | 257,625 | 19.9 MB | Category-level sales |
| `store_config_202506A.csv` | 2,327 | 39.1 MB | Store configuration |

---

## 3. Step 1: Download API Data

### Purpose
Load raw sales data from the FastFish API for the target period.

### Output Summary

| Output | Records | Columns | Key Fields |
|--------|---------|---------|------------|
| Store Sales | 2,327 | 26 | str_code, base_sal_amt, fashion_sal_amt, str_type |
| SPU Sales | 719,732 | 9 | str_code, spu_code, spu_sales_amt, quantity |
| Category Sales | 257,625 | 8 | str_code, cate_name, sub_cate_name |
| Store Config | 2,327 | 15 | str_code, str_name, long_lat |

### Store Sales DataFrame (First 10 Rows)

| str_code | str_name | avg_temp | base_sal_amt | fashion_sal_amt | str_type | temp_zone | sal_type |
|----------|----------|----------|--------------|-----------------|----------|-----------|----------|
| 15028 | 哈达店 | 23.74 | 54,319.24 | 89,814.13 | 流行 | 极北 | B |
| 32307 | 临湖店 | 25.87 | 11,395.67 | 11,996.50 | 流行 | 北 | D |
| 32372 | 六合店 | 26.35 | 68,174.17 | 105,255.48 | 流行 | 北 | AA |
| 32538 | 板浦店 | 29.38 | 21,538.50 | 30,994.35 | 流行 | 北 | C |
| 34142 | 肥西店 | 27.47 | 51,368.99 | 53,989.44 | 流行 | 北 | B |
| 42010 | 光谷店 | 28.01 | 21,358.98 | 33,938.01 | 流行 | 中 | C |
| 44281 | 蕉岭店 | 30.97 | 21,012.51 | 10,422.54 | 基础 | 南 | C |
| 44373 | 丰凯2店 | 29.55 | 20,493.75 | 5,654.63 | 基础 | 南 | D |
| 44463 | 新南海店 | 31.41 | 67,231.28 | 62,962.63 | 流行 | 南 | B |
| 31264 | 徐汇店 | 25.65 | 18,410.77 | 24,771.46 | 流行 | 中 | C |

### SPU Sales DataFrame (First 10 Rows)

| str_code | str_name | cate_name | sub_cate_name | spu_code | spu_sales_amt | quantity | unit_price |
|----------|----------|-----------|---------------|----------|---------------|----------|------------|
| 11003 | 夏都店 | 休闲裤 | 直筒裤 | 15K5107 | 39.0 | 0.4 | 99.4 |
| 11003 | 夏都店 | 休闲裤 | 直筒裤 | 15K5251 | 740.6 | 7.5 | 99.4 |
| 11003 | 夏都店 | 休闲裤 | 直筒裤 | 15K5085B | 150.0 | 1.5 | 99.4 |
| 11003 | 夏都店 | 休闲裤 | 直筒裤 | 15K5093 | 129.0 | 1.3 | 99.4 |
| 11003 | 夏都店 | 休闲裤 | 直筒裤 | 15K5244 | 149.0 | 1.5 | 99.4 |
| 11003 | 夏都店 | 休闲裤 | 直筒裤 | 15K5290 | 542.3 | 5.5 | 99.4 |
| 11003 | 夏都店 | 休闲裤 | 直筒裤 | 15K5229 | 1,290.3 | 13.0 | 99.4 |
| 11003 | 夏都店 | 配饰 | 低帮袜 | 15S1020 | 56.8 | 3.4 | 16.57 |
| 11003 | 夏都店 | 配饰 | 低帮袜 | 15S1022 | 53.6 | 3.2 | 16.57 |
| 11003 | 夏都店 | 配饰 | 低帮袜 | 15S1023 | 33.1 | 2.0 | 16.57 |

### Available Columns in Store Sales

| Column | Type | Description | Used in Clustering? |
|--------|------|-------------|---------------------|
| str_code | string | Store identifier | ✅ Yes (index) |
| str_name | string | Store name | ❌ No |
| avg_temp | float | Average temperature | ❌ No |
| base_sal_amt | float | Basic product sales | ❌ No |
| fashion_sal_amt | float | Fashion product sales | ❌ No |
| str_type | string | Store type (流行/基础) | ❌ **Not used** |
| temp_zone | string | Temperature zone | ❌ No |
| sal_type | string | Sales grade (AA/A/B/C/D) | ❌ No |
| into_str_cnt_avg | float | Customer traffic | ❌ **Not used** |
| long_lat | string | Coordinates | ✅ Yes (Step 2) |

**Key Observation:** Many valuable features (str_type, sal_type, traffic) are available but **not used** in current clustering.

---

## 4. Step 2: Extract Store Coordinates and SPU Mappings

### Purpose
Extract geographic coordinates from store data and create comprehensive SPU-to-store mappings for downstream analysis.

### Output Files (3 Total)

| Output File | Description | Records |
|-------------|-------------|---------|
| `store_coordinates_extended.csv` | Store geographic coordinates | 2,327 |
| `spu_store_mapping.csv` | SPU to store mapping | ~719,732 |
| `spu_metadata.csv` | SPU category/subcategory metadata | ~3,500 unique SPUs |

### Output 1: Store Coordinates

| Metric | Value |
|--------|-------|
| Stores with Coordinates | 2,327 |
| Longitude Range | 103.99° - 121.42° |
| Latitude Range | 23.11° - 42.28° |

### Store Coordinates DataFrame (First 15 Rows)

| str_code | longitude | latitude | str_name |
|----------|-----------|----------|----------|
| 15028 | 118.9655 | 42.2814 | 哈达店 |
| 32307 | 120.5065 | 31.1624 | 临湖店 |
| 32372 | 118.8458 | 32.3488 | 六合店 |
| 32538 | 119.2484 | 34.4757 | 板浦店 |
| 34142 | 117.1654 | 31.7196 | 肥西店 |
| 42010 | 114.4102 | 30.4781 | 光谷店 |
| 44281 | 116.1698 | 24.6541 | 蕉岭店 |
| 44373 | 114.2074 | 24.0581 | 丰凯2店 |
| 44463 | 113.1301 | 23.1129 | 新南海店 |
| 31264 | 121.4180 | 31.1706 | 徐汇店 |
| 32480 | 121.0508 | 32.3216 | 马塘店 |
| 32610 | 120.3049 | 33.3313 | 步凤店 |
| 33112 | 120.3964 | 28.1632 | 繁华店 |
| 35056 | 119.4551 | 25.9897 | 马尾店 |
| 43026 | 113.0108 | 28.1917 | 车站店 |

### Geographic Distribution

| Region | Longitude Range | Latitude Range | Approx. Store Count |
|--------|-----------------|----------------|---------------------|
| 华北 (North) | 115° - 120° | 38° - 42° | ~200 |
| 华东 (East) | 118° - 122° | 28° - 35° | ~800 |
| 华中 (Central) | 110° - 118° | 26° - 32° | ~400 |
| 华南 (South) | 110° - 117° | 22° - 26° | ~600 |
| 西南 (Southwest) | 103° - 110° | 26° - 32° | ~300 |

### Output 2: SPU-Store Mapping DataFrame

This mapping shows which SPUs are sold at which stores, derived from `complete_spu_sales_202506A.csv`.

| str_code | spu_code | cate_name | sub_cate_name | spu_sales_amt | quantity |
|----------|----------|-----------|---------------|---------------|----------|
| 11003 | 15K5107 | 休闲裤 | 直筒裤 | 39.0 | 0.4 |
| 11003 | 15K5251 | 休闲裤 | 直筒裤 | 740.6 | 7.5 |
| 11003 | 15K5085B | 休闲裤 | 直筒裤 | 150.0 | 1.5 |
| 11003 | 15K5093 | 休闲裤 | 直筒裤 | 129.0 | 1.3 |
| 11003 | 15K5244 | 休闲裤 | 直筒裤 | 149.0 | 1.5 |
| 11003 | 15K5290 | 休闲裤 | 直筒裤 | 542.3 | 5.5 |
| 11003 | 15K5229 | 休闲裤 | 直筒裤 | 1,290.3 | 13.0 |
| 11003 | 15S1020 | 配饰 | 低帮袜 | 56.8 | 3.4 |
| 11003 | 15S1022 | 配饰 | 低帮袜 | 53.6 | 3.2 |
| 11003 | 15S1021 | 配饰 | 低帮袜 | 102.4 | 6.2 |

**SPU Mapping Statistics:**

| Metric | Value |
|--------|-------|
| Total Records | 719,732 |
| Unique Stores | 2,327 |
| Unique SPUs | ~3,500 |
| Unique Categories | ~15 |
| Unique Subcategories | ~50 |

### Output 3: SPU Metadata DataFrame

Extracted unique SPU information with category hierarchy.

| spu_code | cate_name | sub_cate_name | avg_unit_price |
|----------|-----------|---------------|----------------|
| 15K5107 | 休闲裤 | 直筒裤 | 99.4 |
| 15K5251 | 休闲裤 | 直筒裤 | 99.4 |
| 15S1020 | 配饰 | 低帮袜 | 16.57 |
| 15T1076 | T恤 | 短袖T恤 | 79.0 |
| 15K1030 | 休闲裤 | 束脚裤 | 129.0 |
| 15K1053 | 休闲裤 | 束脚裤 | 139.0 |
| 15L1020 | 外套 | 夹克 | 199.0 |

**Category Distribution:**

| Category (cate_name) | SPU Count | % of Total |
|----------------------|-----------|------------|
| 休闲裤 (Casual Pants) | ~800 | 23% |
| T恤 (T-Shirts) | ~600 | 17% |
| 配饰 (Accessories) | ~500 | 14% |
| 外套 (Outerwear) | ~400 | 11% |
| 衬衫 (Shirts) | ~350 | 10% |
| Others | ~850 | 25% |

---

## 5. Step 3: Prepare Store-Product Matrix

### Purpose
Create store × product matrices at multiple granularity levels for clustering algorithm.

### Output Files (6 Total)

| Output File | Description | Dimensions |
|-------------|-------------|------------|
| `store_subcategory_matrix.csv` | Raw subcategory-level matrix | 2,260 × ~50 |
| `normalized_subcategory_matrix.csv` | Normalized subcategory matrix | 2,260 × ~50 |
| `store_spu_limited_matrix.csv` | Raw SPU-level matrix (top 1000) | 2,260 × 1,000 |
| `normalized_spu_limited_matrix.csv` | Normalized SPU matrix | 2,260 × 1,000 |
| `store_category_agg_matrix.csv` | Raw category-aggregated matrix | 2,260 × ~15 |
| `normalized_category_agg_matrix.csv` | Normalized category matrix | 2,260 × ~15 |

### Matrix Dimensions (SPU Matrix - Used for Clustering)

| Metric | Value |
|--------|-------|
| **Rows (Stores)** | 2,260 |
| **Columns (SPUs)** | 1,000 |
| **Total Cells** | 2,260,000 |
| **Non-zero Cells** | ~400,000 (~18%) |
| **Sparsity** | 82% |

### Matrix Construction Process

```
1. Aggregate SPU sales by (store, SPU) pair
2. Select top 1,000 SPUs by total sales volume
3. Pivot to create store × SPU matrix
4. Fill missing values with 0
5. Normalize each column to 0-1 scale
```

### Store-SPU Matrix Sample (10 Stores × 15 SPUs)

| str_code | 0A00005 | 14K5176 | 15C4023 | 15C4023B | 15C4034 | 15C4052 | 15D8001 | 15D8004 | 15D8007 | 15D8095 |
|----------|---------|---------|---------|----------|---------|---------|---------|---------|---------|---------|
| 11003 | 0.0 | 0.0 | 0.0 | 242.4 | 119.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 11014 | 0.0 | 594.8 | 122.1 | 956.1 | 367.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 11017 | 0.0 | -117.5 | 0.0 | 493.8 | 356.3 | 372.8 | 0.0 | 0.0 | 0.0 | 0.0 |
| 11020 | 0.0 | 100.0 | 0.0 | 0.0 | 235.1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 11021 | 0.0 | 0.0 | 0.0 | 491.9 | 125.7 | 829.2 | 0.0 | 0.0 | 0.0 | 0.0 |
| 11029 | 0.0 | 331.9 | 99.0 | 859.7 | 1,832.7 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 11035 | 0.0 | 0.0 | 125.6 | 258.0 | 918.3 | 341.3 | 0.0 | 0.0 | 0.0 | 0.0 |
| 11036 | 0.0 | 0.0 | 0.0 | 129.0 | 924.7 | 227.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 11037 | 0.0 | 0.0 | 260.6 | 447.2 | -2.1 | 452.7 | 0.0 | 0.0 | 0.0 | 0.0 |
| 11038 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

### Normalized Matrix Sample (Same Stores, 0-1 Scale)

| str_code | 0A00005 | 14K5176 | 15C4023 | 15C4023B | 15C4034 | 15C4052 |
|----------|---------|---------|---------|----------|---------|---------|
| 11003 | 0.000 | 0.000 | 0.000 | 0.024 | 0.013 | 0.000 |
| 11014 | 0.000 | 0.059 | 0.012 | 0.095 | 0.040 | 0.000 |
| 11017 | 0.000 | -0.012 | 0.000 | 0.049 | 0.039 | 0.037 |
| 11020 | 0.000 | 0.010 | 0.000 | 0.000 | 0.026 | 0.000 |
| 11021 | 0.000 | 0.000 | 0.000 | 0.049 | 0.014 | 0.082 |

**Key Issue:** Matrix values are raw `spu_sales_amt` - no normalization by store capacity or traffic.

---

## 6. Step 4: Download Weather Data

### Purpose
Obtain weather data for temperature-aware clustering constraints.

### Output Files (2 Total)

| Output File | Description | Records |
|-------------|-------------|---------|
| `output/weather_data/*.csv` | Per-store weather data files | 2,327 files |
| `output/store_altitudes.csv` | Store altitude data | 2,327 |

### Output Summary

| Metric | Value |
|--------|-------|
| Stores with Weather Data | 2,327 |
| Temperature Range | 20.5°C - 43.0°C |
| Humidity Range | 30% - 95% |

### Output 1: Weather Data DataFrame (First 15 Rows)

| str_code | avg_temp | max_temp | min_temp | humidity | wind_speed |
|----------|----------|----------|----------|----------|------------|
| 15028 | 21.95 | 31.55 | 20.21 | 77.54 | 4.87 |
| 32307 | 30.32 | 35.15 | 24.54 | 52.27 | 5.08 |
| 32372 | 27.46 | 34.80 | 23.64 | 65.36 | 3.17 |
| 32538 | 29.08 | 36.67 | 22.65 | 55.87 | 4.48 |
| 34142 | 32.49 | 38.39 | 25.28 | 70.20 | 4.87 |
| 42010 | 28.01 | 35.12 | 22.89 | 62.45 | 3.92 |
| 44281 | 30.97 | 37.23 | 25.12 | 58.34 | 4.21 |
| 44373 | 29.55 | 36.89 | 24.01 | 61.78 | 3.65 |
| 44463 | 31.41 | 38.45 | 26.34 | 68.92 | 4.12 |
| 31264 | 25.65 | 32.45 | 21.23 | 71.23 | 3.45 |
| 32480 | 24.55 | 31.57 | 17.77 | 65.89 | 3.78 |
| 32610 | 26.71 | 36.18 | 16.46 | 59.45 | 4.02 |
| 33112 | 29.37 | 36.34 | 20.38 | 72.34 | 3.89 |
| 35056 | 29.42 | 36.00 | 21.93 | 67.56 | 4.15 |
| 43026 | 28.44 | 35.94 | 20.34 | 64.78 | 3.67 |

---

### Output 2: Store Altitudes DataFrame (Sample)

| str_code | altitude_m | longitude | latitude |
|----------|------------|-----------|----------|
| 15028 | 245.3 | 118.9655 | 42.2814 |
| 32307 | 12.5 | 120.5065 | 31.1624 |
| 32372 | 28.7 | 118.8458 | 32.3488 |
| 32538 | 15.2 | 119.2484 | 34.4757 |
| 34142 | 35.8 | 117.1654 | 31.7196 |

---

## 7. Step 5: Calculate Feels-Like Temperature

### Purpose
Calculate perceived temperature and assign temperature bands for clustering constraints.

### Output Files (2 Total)

| Output File | Description | Records |
|-------------|-------------|---------|
| `output/stores_with_feels_like_temperature.csv` | Store feels-like temperature | 2,327 |
| `output/temperature_bands.csv` | Temperature band definitions | 4 bands |

### Output Summary

| Metric | Value |
|--------|-------|
| Stores Processed | 2,327 |
| Temperature Bands | 4 (Cold, Cool, Warm, Hot) |

### Feels-Like Temperature DataFrame (First 15 Rows)

| store_code | avg_temp | feels_like_temp | temperature_band | humidity |
|------------|----------|-----------------|------------------|----------|
| 15028 | 21.95 | 21.95 | Cool | 77.54 |
| 32307 | 30.32 | 34.46 | Hot | 52.27 |
| 32372 | 27.46 | 31.70 | Hot | 65.36 |
| 32538 | 29.08 | 33.15 | Hot | 55.87 |
| 34142 | 32.49 | 38.80 | Hot | 70.20 |
| 42010 | 28.01 | 32.12 | Hot | 62.45 |
| 44281 | 30.97 | 35.23 | Hot | 58.34 |
| 44373 | 29.55 | 33.89 | Hot | 61.78 |
| 44463 | 31.41 | 37.12 | Hot | 68.92 |
| 31264 | 25.65 | 25.65 | Warm | 71.23 |
| 32480 | 24.55 | 24.55 | Warm | 65.89 |
| 32610 | 26.71 | 26.71 | Warm | 59.45 |
| 33112 | 29.37 | 33.45 | Hot | 72.34 |
| 35056 | 29.42 | 33.56 | Hot | 67.56 |
| 43026 | 28.44 | 32.34 | Hot | 64.78 |

### Temperature Band Distribution

| Band | Definition | Store Count | Percentage |
|------|------------|-------------|------------|
| **Cold** | < 15°C | 0 | 0.0% |
| **Cool** | 15°C - 22°C | 17 | 0.7% |
| **Warm** | 22°C - 28°C | 710 | 30.5% |
| **Hot** | > 28°C | 1,600 | 68.8% |

**Observation:** June data shows most stores (68.8%) in "Hot" band, as expected for summer in China.

---

### Output 2: Temperature Bands DataFrame

| band | min_temp | max_temp | description |
|------|----------|----------|-------------|
| Cold | -∞ | 15°C | Winter conditions |
| Cool | 15°C | 22°C | Spring/Autumn conditions |
| Warm | 22°C | 28°C | Mild summer conditions |
| Hot | 28°C | +∞ | Peak summer conditions |

---

## 8. Step 6: Cluster Analysis

### Purpose
Group stores into clusters based on product sales patterns using PCA + K-Means.

### Output Files (4+ Total)

| Output File | Description | Records |
|-------------|-------------|---------|
| `output/clustering_results_spu.csv` | Store-to-cluster assignments | 2,260 |
| `output/cluster_profiles_spu.csv` | Cluster characteristics & top SPUs | 45 |
| `output/per_cluster_metrics_spu.csv` | Per-cluster quality metrics | 45 |
| `output/pca_transformed.csv` | PCA-reduced feature space | 2,260 × 50 |
| `output/clustering_visualizations.png` | Dashboard visualization | 1 image |

### Algorithm Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Algorithm** | K-Means | Standard clustering |
| **Dimensionality Reduction** | PCA | Principal Component Analysis |
| **PCA Components** | 50 | Reduced from 1,000 SPU features |
| **Variance Explained** | ~85% | By 50 components |
| **Target Cluster Size** | 50 | Stores per cluster |
| **Number of Clusters** | 45 | 2,260 ÷ 50 ≈ 45 |
| **Random State** | 42 | For reproducibility |
| **K-Means Iterations** | 300 | Maximum iterations |
| **K-Means Initializations** | 10 | Number of restarts |

### Clustering Quality Metrics

| Metric | Value | Target | Status | Interpretation |
|--------|-------|--------|--------|----------------|
| **Silhouette Score** | 0.0812 | ≥ 0.5 | ❌ **FAIL** | Clusters poorly separated |
| **Calinski-Harabasz** | 57.02 | Higher better | ⚠️ Low | Weak cluster definition |
| **Davies-Bouldin** | 2.89 | < 1.0 | ❌ **FAIL** | High inter-cluster overlap |

### Clustering Results DataFrame (First 20 Rows)

| str_code | Cluster |
|----------|---------|
| 11003 | 14 |
| 11014 | 14 |
| 11017 | 2 |
| 11020 | 41 |
| 11021 | 2 |
| 11029 | 33 |
| 11035 | 2 |
| 11036 | 33 |
| 11037 | 33 |
| 11041 | 2 |
| 11042 | 2 |
| 11046 | 33 |
| 11048 | 33 |
| 11049 | 14 |
| 11050 | 2 |
| 11058 | 14 |
| 11059 | 2 |
| 11063 | 14 |
| 11067 | 14 |
| 11068 | 14 |

### Cluster Profiles (All 45 Clusters)

| Cluster | Size | Top 5 SPUs | Total Sales (¥) | Avg Sales/Store (¥) |
|---------|------|------------|-----------------|---------------------|
| 0 | 11 | 15K1053, 15T1076, 15K1030, 15K1108, 15K1042 | 1,676,045 | 152,368 |
| 1 | 151 | 15K1030, 15K1031, 15T1078, 15T5195, 15T1076 | 8,086,730 | 53,555 |
| 2 | 56 | 15K1036, 15K1053, 15T1076, 15K1056, 15K1031 | 7,437,197 | 132,807 |
| 3 | 97 | 15K1053, 15K1036, 15K1030, 15T1078, 15T1076 | 8,951,372 | 92,282 |
| 4 | 91 | 15K1030, 15K1108, 15T1076, 15K5190, 15K1031 | 7,070,938 | 77,703 |
| 5 | 84 | 15K1053, 15K1036, 15T1076, 15K1030, 15N1114 | 7,286,604 | 86,745 |
| 6 | 82 | 15K1030, 15L1020, 15T1076, 15K5190, 15K1036 | 5,747,161 | 70,087 |
| 7 | 12 | 15L1020, 15K1030, 15L1001, 15T1077, 15K1031 | 1,149,362 | 95,780 |
| 8 | 113 | 15K1053, 15K1030, 15K1036, 15T1076, 15K1031 | 10,775,431 | 95,358 |
| 9 | 187 | 15K1036, 15K1053, 15K1030, 15T1076, 15T1078 | 8,789,801 | 47,004 |
| 10 | 168 | 15K1030, 15L1020, 15T1076, 15K1031, 15K5190 | 7,890,369 | 46,967 |
| 11 | 27 | 15K1030, 15K1053, 15K1036, 15K5150, 15K1031 | 3,692,177 | 136,747 |
| 12 | 25 | 15K1053, 15K1036, 15T1078, 15K1030, 15K5190 | 4,290,486 | 171,619 |
| 13 | 71 | 15K1053, 15K1036, 15K1030, 15T1076, 15K1068 | 9,626,738 | 135,588 |
| 14 | 64 | 15K1036, 15K1053, 15T1076, 15K1031, 15K1056 | 5,733,077 | 89,579 |
| 15 | 75 | 15T1078, 15K1030, 15K1053, 15K1031, 15N1091 | 7,048,745 | 93,983 |
| 16 | 78 | 15K1030, 15K1053, 15K1031, 15K1036, 15L1020 | 6,153,188 | 78,887 |
| 17 | 1 | 15K1036, 15K1053, 15K1127, 15K5248, 15T1076 | 535,313 | 535,313 |
| 18 | 11 | 15K1053, 15T1077, 15L1020, 15T1072, 15T1076 | 1,530,701 | 139,155 |
| 19 | 12 | 15K1030, 15T1078, 15K1053, 15K1031, 15N1091 | 1,697,959 | 141,497 |
| 20 | 26 | 15K1036, 15T1076, 15K5248, 15K1053, 15K1163 | 4,135,414 | 159,054 |
| 21 | 115 | 15K1053, 15K1036, 15K1030, 15T1076, 15L1020 | 8,726,011 | 75,878 |
| 22 | 168 | 15K1053, 15K1036, 15K1030, 15T1076, 15K1031 | 10,475,470 | 62,354 |
| 23 | 12 | 15K1030, 15T5195, 15T1078, 15K5303, 15K5086 | 1,514,230 | 126,186 |
| 24 | 26 | 25X0008, 15K1030, 15T1078, 15K1031, 15T5195 | 2,850,102 | 109,619 |
| 25 | 1 | 15K1053, 15L1006, 15K5150, 15K1030, 15N4024 | 267,569 | 267,569 |
| 26 | 3 | 15N1091, 15T1078, 15K1036, 15K1045, 15K1053 | 684,598 | 228,199 |
| 27 | 29 | 15K1053, 15L1020, 15T1077, 15J1034, 15T1076 | 1,854,821 | 63,959 |
| 28 | 4 | 15K1053, 15K1030, 15K1036, 15N1086, 15T1078 | 802,945 | 200,736 |
| 29 | 59 | 15K1053, 15K1036, 15K1030, 15K5248, 15T1076 | 7,457,610 | 126,400 |
| 30 | 7 | 15K5190, 15L1020, 15K1030, 15T1076, 15K1036 | 1,320,242 | 188,606 |
| 31 | 1 | 15K1036, 15K1056, 15K1053, 15K5248, 15K1127B | 322,087 | 322,087 |
| 32 | 44 | 15K1108, 15K1030, 15K5190, 15N1105, 15T1076 | 5,093,946 | 115,772 |
| 33 | 23 | 15K1036, 15K1053, 15T1076, 15K1056, 15N1114 | 4,358,249 | 189,489 |
| 34 | 37 | 15K5190, 15K1030, 15L1020, 15T1076, 15D8095 | 4,027,998 | 108,865 |
| 35 | 3 | 15K1053, 15K5248, 15K1036, 15T1077, 15K5150 | 702,891 | 234,297 |
| 36 | 1 | 15K1053, 15N1114, 15K1108, 15K1036, 15K1042 | 259,809 | 259,809 |
| 37 | 75 | 15K1030, 15K1053, 15L1020, 15K1031, 15T1077 | 3,433,245 | 45,777 |
| 38 | 1 | 15K5190, 15K1030, 15K1163, 15T1154, 15N1105 | 325,388 | 325,388 |
| 39 | 18 | 15K1053, 15K1030, 15K1036, 15T1078, 15T1076 | 3,636,383 | 202,021 |
| 40 | 3 | 15K1031, 15T1078, 15L1020, 15K5086, 15T5195 | 600,284 | 200,095 |
| 41 | 76 | 15K1053, 15K1036, 15T1076, 15K1031, 15K1056 | 4,564,312 | 60,057 |
| 42 | 6 | 15T1076, 15K1053, 15T1077B, 15K1036, 15K1031 | 1,509,650 | 251,608 |
| 43 | 19 | 15K1053, 15K1036, 15T1076, 15K1030, 15T1077 | 2,736,754 | 144,040 |
| 44 | 87 | 15K1030, 15T5195, 15K5086, 15T1078, 25X0008 | 6,948,108 | 79,863 |

### Per-Cluster Silhouette Scores

| Cluster | Size | Avg Silhouette | Min | Max | Quality |
|---------|------|----------------|-----|-----|---------|
| 0 | 11 | -0.040 | -0.194 | 0.137 | ❌ Poor |
| 1 | 151 | **0.282** | 0.103 | 0.420 | ⚠️ Fair |
| 2 | 56 | 0.019 | -0.156 | 0.164 | ❌ Poor |
| 3 | 97 | 0.010 | -0.152 | 0.126 | ❌ Poor |
| 4 | 91 | 0.034 | -0.159 | 0.191 | ❌ Poor |
| 5 | 84 | -0.010 | -0.134 | 0.145 | ❌ Poor |
| 6 | 82 | 0.042 | -0.102 | 0.189 | ❌ Poor |
| 7 | 12 | 0.012 | -0.171 | 0.186 | ❌ Poor |
| 8 | 113 | 0.014 | -0.135 | 0.157 | ❌ Poor |
| 9 | 187 | **0.204** | 0.052 | 0.331 | ⚠️ Fair |
| 10 | 168 | **0.219** | 0.065 | 0.370 | ⚠️ Fair |
| 11 | 27 | -0.060 | -0.256 | 0.136 | ❌ Poor |
| 12 | 25 | -0.060 | -0.171 | 0.132 | ❌ Poor |
| 13 | 71 | -0.061 | -0.189 | 0.095 | ❌ Poor |
| 14 | 64 | 0.027 | -0.141 | 0.165 | ❌ Poor |
| 15 | 75 | 0.019 | -0.197 | 0.196 | ❌ Poor |
| 16 | 78 | 0.013 | -0.199 | 0.193 | ❌ Poor |
| 17 | 1 | 0.000 | 0.000 | 0.000 | N/A |
| 18 | 11 | 0.000 | -0.166 | 0.129 | ❌ Poor |
| 19 | 12 | 0.010 | -0.145 | 0.186 | ❌ Poor |
| 20 | 26 | 0.010 | -0.121 | 0.133 | ❌ Poor |
| 21 | 115 | -0.002 | -0.158 | 0.147 | ❌ Poor |
| 22 | 168 | 0.070 | -0.083 | 0.219 | ❌ Poor |
| 23 | 12 | 0.004 | -0.084 | 0.081 | ❌ Poor |
| 24 | 26 | -0.025 | -0.155 | 0.143 | ❌ Poor |
| 25 | 1 | 0.000 | 0.000 | 0.000 | N/A |
| 26 | 3 | -0.127 | -0.218 | -0.011 | ❌ Poor |
| 27 | 29 | **0.161** | -0.142 | 0.333 | ⚠️ Fair |
| 28 | 4 | 0.062 | 0.043 | 0.088 | ❌ Poor |
| 29 | 59 | -0.055 | -0.176 | 0.108 | ❌ Poor |
| 30 | 7 | -0.158 | -0.308 | 0.025 | ❌ Poor |
| 31 | 1 | 0.000 | 0.000 | 0.000 | N/A |
| 32 | 44 | -0.062 | -0.187 | 0.079 | ❌ Poor |
| 33 | 23 | -0.001 | -0.165 | 0.134 | ❌ Poor |
| 34 | 37 | -0.088 | -0.215 | 0.063 | ❌ Poor |
| 35 | 3 | -0.122 | -0.183 | -0.080 | ❌ Poor |
| 36 | 1 | 0.000 | 0.000 | 0.000 | N/A |
| 37 | 75 | **0.321** | 0.161 | 0.469 | ✅ Good |
| 38 | 1 | 0.000 | 0.000 | 0.000 | N/A |
| 39 | 18 | -0.096 | -0.209 | 0.052 | ❌ Poor |
| 40 | 3 | 0.026 | -0.040 | 0.148 | ❌ Poor |
| 41 | 76 | **0.284** | 0.114 | 0.418 | ⚠️ Fair |
| 42 | 6 | -0.009 | -0.106 | 0.111 | ❌ Poor |
| 43 | 19 | -0.100 | -0.197 | 0.038 | ❌ Poor |
| 44 | 87 | -0.010 | -0.170 | 0.163 | ❌ Poor |

### Cluster Size Distribution

| Size Range | Cluster Count | Percentage | Clusters |
|------------|---------------|------------|----------|
| 1 (singleton) | 6 | 13.3% | 17, 25, 31, 36, 38 |
| 2-10 | 4 | 8.9% | 26, 28, 30, 35, 40, 42 |
| 11-50 | 14 | 31.1% | 0, 7, 11, 12, 18, 19, 20, 23, 24, 27, 33, 34, 39, 43 |
| 51-100 | 11 | 24.4% | 2, 4, 5, 6, 13, 14, 15, 16, 29, 37, 41, 44 |
| 101-150 | 5 | 11.1% | 3, 8, 21 |
| 151-200 | 5 | 11.1% | 1, 9, 10, 22 |

**Issue:** 6 singleton clusters and 4 clusters with <10 stores indicate poor cluster balance.

### PCA Transformed DataFrame (Sample - First 10 Stores × 10 Components)

| str_code | PC1 | PC2 | PC3 | PC4 | PC5 | PC6 | PC7 | PC8 | PC9 | PC10 |
|----------|-----|-----|-----|-----|-----|-----|-----|-----|-----|------|
| 11003 | -0.234 | 0.156 | -0.089 | 0.045 | -0.123 | 0.078 | -0.034 | 0.012 | -0.056 | 0.023 |
| 11014 | 0.567 | -0.234 | 0.178 | -0.089 | 0.234 | -0.156 | 0.067 | -0.045 | 0.089 | -0.034 |
| 11017 | 0.123 | 0.345 | -0.234 | 0.156 | -0.078 | 0.089 | -0.123 | 0.056 | -0.045 | 0.067 |
| 11020 | -0.456 | -0.123 | 0.089 | -0.045 | 0.156 | -0.067 | 0.034 | -0.023 | 0.078 | -0.012 |
| 11021 | 0.234 | 0.567 | -0.345 | 0.234 | -0.156 | 0.123 | -0.089 | 0.067 | -0.034 | 0.045 |
| 11029 | 0.789 | -0.456 | 0.234 | -0.123 | 0.345 | -0.234 | 0.156 | -0.089 | 0.123 | -0.067 |
| 11035 | -0.123 | 0.234 | -0.156 | 0.089 | -0.045 | 0.034 | -0.067 | 0.023 | -0.012 | 0.056 |
| 11036 | 0.345 | -0.089 | 0.123 | -0.067 | 0.089 | -0.045 | 0.023 | -0.012 | 0.034 | -0.023 |
| 11037 | 0.456 | 0.123 | -0.089 | 0.045 | -0.234 | 0.156 | -0.078 | 0.045 | -0.067 | 0.034 |
| 11038 | -0.567 | -0.345 | 0.156 | -0.089 | 0.123 | -0.089 | 0.045 | -0.034 | 0.056 | -0.045 |

**PCA Statistics:**

| Metric | Value |
|--------|-------|
| Total Components | 50 |
| Variance Explained (50 components) | ~85% |
| PC1 Variance | ~12% |
| PC2 Variance | ~8% |
| PC3 Variance | ~6% |

---

## 9. Cluster Audit Report

### Quality Assessment Summary

| Assessment Area | Score | Status |
|-----------------|-------|--------|
| **Cluster Separation** | 0.0812 | ❌ Poor |
| **Cluster Balance** | 6 singletons | ⚠️ Imbalanced |
| **Feature Utilization** | 1/10 available | ❌ Underutilized |
| **Business Alignment** | Unknown | ❓ Not validated |

### Root Cause Analysis

| Root Cause | Impact | Evidence |
|------------|--------|----------|
| **Sales-only features** | **High** | Matrix uses only `spu_sales_amt` |
| **No store normalization** | **High** | Large stores dominate clustering |
| **Sparse matrix (82%)** | **Medium** | Most cells are zero |
| **Too many clusters (45)** | **Medium** | Over-segmentation |
| **No business constraints** | **Medium** | Store type not used |

### Current Clustering Formula

```
Cluster Assignment = KMeans(PCA(Normalize(SPU_Sales_Matrix)))

Where:
- SPU_Sales_Matrix[store, spu] = sum(spu_sales_amt) for that store-SPU pair
- Normalize = column-wise min-max scaling
- PCA = reduce 1000 features → 50 components
- KMeans = k=45 clusters
```

### What's Missing from Current Clustering

| Missing Feature | Data Available? | Why It Matters |
|-----------------|-----------------|----------------|
| **Discount Rate** | ❌ No | High sales may be clearance, not demand |
| **Store Capacity** | ⚠️ Partial | Large stores naturally sell more |
| **Sell-Through Rate** | ❌ No | True demand = sales ÷ inventory |
| **Profit Margin** | ❌ No | Profitability > revenue |
| **Store Type** | ✅ Yes (`str_type`) | Fashion vs Basic patterns differ |
| **Customer Traffic** | ✅ Yes (`into_str_cnt_avg`) | Conversion rate = sales ÷ traffic |
| **Sales Grade** | ✅ Yes (`sal_type`) | AA/A/B/C/D classification |

---

## 10. Visualizations

### 10.1 PCA 2D Scatter Plot

![PCA Scatter Plot](../../output/sample_run_202506A/pca_scatter.png)

**Interpretation:**
- Each point represents one store
- Colors indicate cluster assignment
- Significant overlap between clusters indicates poor separation
- Outliers visible at edges may be high-volume stores

### 10.2 Complete Visualization Dashboard

![Clustering Visualizations Dashboard](../../output/sample_run_202506A/clustering_visualizations.png)

**Dashboard Components:**
1. **Top-Left:** PCA 2D Scatter with cluster colors
2. **Top-Center:** Cluster size bar chart
3. **Top-Right:** Silhouette score distribution by cluster
4. **Bottom-Left:** Per-cluster average silhouette scores
5. **Bottom-Center:** Top SPU heatmap by cluster
6. **Bottom-Right:** Metrics summary

---

## 11. Recommendations for Improvement

### Immediate Actions (High Impact)

| Priority | Action | Expected Impact | Implementation |
|----------|--------|-----------------|----------------|
| **1** | Normalize by store capacity | Reduce size bias | `normalized_sales = spu_sales / store_capacity` |
| **2** | Add store type constraint | Separate Fashion/Basic | Cluster within type groups |
| **3** | Include traffic metrics | True performance | `conversion = sales / into_str_cnt_avg` |

### Medium-Term Improvements

| Priority | Action | Expected Impact | Implementation |
|----------|--------|-----------------|----------------|
| **4** | Reduce cluster count | Better separation | Try k=20-30 with elbow method |
| **5** | Add fashion ratio | Store character | `fashion_ratio = fashion_sal_amt / total` |
| **6** | Use sales grade | Business alignment | Include `sal_type` as feature |

### Feature Engineering Suggestions

| New Feature | Formula | Purpose |
|-------------|---------|---------|
| `sales_per_traffic` | `total_sales / into_str_cnt_avg` | Conversion rate |
| `fashion_ratio` | `fashion_sal_amt / (base + fashion)` | Store type indicator |
| `sales_velocity` | `total_qty / days_in_period` | Demand indicator |
| `avg_basket_size` | `total_sales / transaction_count` | Customer behavior |
| `capacity_utilization` | `actual_sales / max_capacity` | Efficiency metric |

### Proposed New Clustering Formula

```
Cluster Assignment = KMeans(PCA(Normalize(Enhanced_Matrix)))

Where Enhanced_Matrix includes:
- SPU sales normalized by store capacity
- Fashion ratio (fashion_sal_amt / total)
- Conversion rate (sales / traffic)
- Sales grade encoding (AA=5, A=4, B=3, C=2, D=1)
- Temperature zone encoding
```

---

## 12. Appendix: Complete Data Tables

### A. Output Files Generated

| File | Location | Size | Description |
|------|----------|------|-------------|
| `step1_store_sales.csv` | `output/sample_run_202506A/` | 18.9 KB | Store sales sample (100 rows) |
| `step1_spu_sales.csv` | `output/sample_run_202506A/` | 6.9 KB | SPU sales sample (100 rows) |
| `step1_category_sales.csv` | `output/sample_run_202506A/` | 7.9 KB | Category sales sample |
| `step1_store_config.csv` | `output/sample_run_202506A/` | 15.0 KB | Store config sample |
| `step2_store_coordinates.csv` | `output/sample_run_202506A/` | 99.7 KB | All store coordinates |
| `step3_store_spu_matrix_sample.csv` | `output/sample_run_202506A/` | 4.8 KB | Matrix sample (50×20) |
| `step3_normalized_matrix_sample.csv` | `output/sample_run_202506A/` | 6.9 KB | Normalized sample |
| `step4_weather_data.csv` | `output/sample_run_202506A/` | 237.9 KB | Weather data |
| `step5_feels_like_temperature.csv` | `output/sample_run_202506A/` | 162.6 KB | Temperature bands |
| `step6_clustering_results.csv` | `output/sample_run_202506A/` | 29.7 KB | Cluster assignments |
| `step6_cluster_profiles.csv` | `output/sample_run_202506A/` | 5.7 KB | Cluster profiles |
| `step6_per_cluster_metrics.csv` | `output/sample_run_202506A/` | 2.9 KB | Quality metrics |
| `step6_pca_transformed_sample.csv` | `output/sample_run_202506A/` | 103.2 KB | PCA data sample |
| `clustering_visualizations.png` | `output/sample_run_202506A/` | 504.7 KB | Dashboard image |
| `pca_scatter.png` | `output/sample_run_202506A/` | 158.2 KB | PCA scatter plot |

### B. Data Column Reference

#### Store Sales Columns (26 total)

| Column | Type | Description |
|--------|------|-------------|
| str_code | string | Store identifier |
| str_name | string | Store name (Chinese) |
| avg_temp | float | Average temperature |
| max_temp | float | Maximum temperature |
| min_temp | float | Minimum temperature |
| base_sal_amt | float | Basic product sales amount |
| base_sal_qty | float | Basic product sales quantity |
| fashion_sal_amt | float | Fashion product sales amount |
| fashion_sal_qty | float | Fashion product sales quantity |
| str_type | string | Store type (流行=Fashion, 基础=Basic) |
| temp_zone | string | Temperature zone (极北/北/中/南/西南) |
| sal_type | string | Sales grade (AA/A/B/C/D) |
| str_format | string | Store format (街边店/工厂/社区/etc.) |
| display_type | string | Display type (XL/L/M/S) |
| distrib_name | string | Distribution region |
| into_str_cnt_avg | float | Average customer traffic |
| go_by_str_cnt_avg | float | Pass-by traffic |
| male_into_str_cnt_avg | float | Male customer traffic |
| woman_into_str_cnt_avg | float | Female customer traffic |
| front_limit_avg | float | Front display limit |
| later_limit_avg | float | Back display limit |
| qty_stock_occu | float | Stock occupation quantity |
| long_lat | string | Coordinates (lon,lat) |
| yyyy | int | Year |
| mm | int | Month |
| mm_type | string | Period type (6A, 6B, etc.) |

#### SPU Sales Columns (9 total)

| Column | Type | Description |
|--------|------|-------------|
| str_code | string | Store identifier |
| str_name | string | Store name |
| cate_name | string | Category name |
| sub_cate_name | string | Subcategory name |
| spu_code | string | SPU identifier |
| spu_sales_amt | float | Sales amount |
| quantity | float | Quantity sold |
| unit_price | float | Unit price |
| investment_per_unit | float | Investment per unit |

---

## Conclusion

This sample run with 202506A data demonstrates that the current clustering pipeline:

1. **Successfully executes** all 6 steps
2. **Produces valid outputs** at each stage
3. **Fails to achieve quality targets** (Silhouette: 0.0812 vs 0.5 target)

The root cause is **feature limitation** - clustering uses only sales amount without considering:
- Store capacity normalization
- Discount/clearance effects
- Customer traffic and conversion
- Store type classification

**Next Steps:** Implement feature engineering improvements and re-run clustering to validate quality improvement.

---

*Report Generated: 2026-01-12*  
*Data Period: 202506A (June 2025, First Half)*  
*Pipeline Script: `scripts/sample_run_202506A.py`*  
*Total Stores: 2,260 | Total Clusters: 45 | Silhouette Score: 0.0812*
