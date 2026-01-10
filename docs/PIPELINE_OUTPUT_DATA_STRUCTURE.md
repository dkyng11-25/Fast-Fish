# 📊 Pipeline Output Data Structure Documentation

**Created:** 2025-01-08  
**Purpose:** Document the output data structure after each pipeline step for understanding code structure and overall framework

---

## 📋 Table of Contents

1. [Pipeline Overview](#1-pipeline-overview)
2. [Step 1: Download API Data](#2-step-1-download-api-data)
3. [Step 2: Extract Coordinates](#3-step-2-extract-coordinates)
4. [Step 3: Prepare Matrix](#4-step-3-prepare-matrix)
5. [Step 4: Determine Optimal Clusters](#5-step-4-determine-optimal-clusters)
6. [Step 5: K-Means Clustering](#6-step-5-k-means-clustering)
7. [Step 6: Cluster Analysis](#7-step-6-cluster-analysis)
8. [Step 7: Product Mix Rules](#8-step-7-product-mix-rules)
9. [Step 8: Visualization Dashboard](#9-step-8-visualization-dashboard)
10. [Extended Steps (9+)](#10-extended-steps)

---

## 1. Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Fast Fish Pipeline Data Flow                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: API Data     ──►  Step 2: Coordinates  ──►  Step 3: Matrix         │
│  (Raw Sales Data)          (Store Locations)         (Feature Matrix)       │
│       │                          │                        │                 │
│       ▼                          ▼                        ▼                 │
│  data/api_data/            data/                     data/                  │
│  ├─ store_config_*.csv     ├─ store_coordinates_     ├─ normalized_*_       │
│  ├─ store_sales_*.csv      │   extended.csv          │   matrix.csv         │
│  ├─ complete_category_     ├─ spu_store_mapping.csv  └─ store_*_matrix.csv  │
│  │   sales_*.csv           └─ spu_metadata.csv                              │
│  └─ complete_spu_                                                           │
│      sales_*.csv                                                            │
│                                                                             │
│  Step 4: Optimal K    ──►  Step 5: K-Means     ──►  Step 6: Analysis        │
│  (Elbow/Silhouette)        (Clustering)             (PCA + Quality)         │
│       │                          │                        │                 │
│       ▼                          ▼                        ▼                 │
│  output/                   output/                   output/                │
│  └─ optimal_k_analysis.csv └─ clustering_results_    ├─ clustering_results_ │
│                               *.csv                  │   spu_*.csv          │
│                                                      ├─ cluster_profiles_   │
│                                                      │   *.csv              │
│                                                      └─ cluster_metrics.csv │
│                                                                             │
│  Step 7: Rules        ──►  Step 8: Dashboard                                │
│  (Product Mix Rules)       (Visualization)                                  │
│       │                          │                                          │
│       ▼                          ▼                                          │
│  output/                   output/                                          │
│  ├─ spu_rules_*.csv        ├─ cluster_map.html                              │
│  ├─ category_rules_*.csv   └─ dashboard_*.html                              │
│  └─ consolidated_rules.csv                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Step 1: Download API Data

### Purpose
Download raw sales data from Fast Fish API for a specific period (half-month or full month).

### Input
- API endpoint: `fdapidb.fastfish.com:8089`
- Period parameters: `--month YYYYMM --period A|B`

### Output Files

#### `data/api_data/store_config_YYYYMMP.csv`
Store configuration and attributes.

| Column | Type | Description |
|--------|------|-------------|
| `str_code` | string | Store unique identifier |
| `str_name` | string | Store name (Chinese) |
| `long_lat` | string | Longitude,Latitude (comma-separated) |
| `yyyy` | int | Year |
| `mm` | int | Month |
| `mm_type` | string | Period type ("6A", "06B", etc.) |
| `province` | string | Province name |
| `city` | string | City name |
| `district` | string | District name |

#### `data/api_data/store_sales_YYYYMMP.csv`
Store-level sales aggregates.

| Column | Type | Description |
|--------|------|-------------|
| `str_code` | string | Store unique identifier |
| `total_sal_amt` | float | Total sales amount |
| `total_sal_qty` | float | Total sales quantity |
| `base_sal_amt` | float | Basic category sales amount |
| `fashion_sal_amt` | float | Fashion category sales amount |
| `yyyy` | int | Year |
| `mm` | int | Month |
| `mm_type` | string | Period type |

#### `data/api_data/complete_category_sales_YYYYMMP.csv`
Category-level sales breakdown.

| Column | Type | Description |
|--------|------|-------------|
| `str_code` | string | Store unique identifier |
| `str_name` | string | Store name |
| `cate_name` | string | Category name (e.g., "牛仔裤") |
| `sub_cate_name` | string | Subcategory name (e.g., "弯刀裤") |
| `spu_sales_amt` | float | Sales amount for this category |
| `quantity` | float | Sales quantity |
| `unit_price` | float | Average unit price |

#### `data/api_data/complete_spu_sales_YYYYMMP.csv`
SPU-level sales breakdown (most granular).

| Column | Type | Description |
|--------|------|-------------|
| `str_code` | string | Store unique identifier |
| `str_name` | string | Store name |
| `cate_name` | string | Category name |
| `sub_cate_name` | string | Subcategory name |
| `spu_code` | string | SPU unique identifier |
| `spu_sales_amt` | float | Sales amount for this SPU |
| `quantity` | float | Sales quantity |
| `unit_price` | float | Unit price |
| `investment_per_unit` | float | Investment per unit |

---

## 3. Step 2: Extract Coordinates

### Purpose
Extract store coordinates from multiple periods and create SPU mappings.

### Input
- `data/api_data/store_config_*.csv` (multiple periods)
- `data/api_data/complete_spu_sales_*.csv` (multiple periods)

### Output Files

#### `data/store_coordinates_extended.csv`
Consolidated store coordinates from all periods.

| Column | Type | Description |
|--------|------|-------------|
| `str_code` | string | Store unique identifier |
| `str_name` | string | Store name |
| `longitude` | float | Store longitude |
| `latitude` | float | Store latitude |
| `province` | string | Province name |
| `city` | string | City name |
| `district` | string | District name |
| `source_period` | string | Period from which coordinates were extracted |

#### `data/spu_store_mapping.csv`
SPU-to-store mapping across all periods.

| Column | Type | Description |
|--------|------|-------------|
| `spu_code` | string | SPU unique identifier |
| `str_code` | string | Store unique identifier |
| `total_sales_amt` | float | Total sales amount across periods |
| `total_quantity` | float | Total quantity across periods |
| `period_count` | int | Number of periods with sales |

#### `data/spu_metadata.csv`
SPU metadata and category information.

| Column | Type | Description |
|--------|------|-------------|
| `spu_code` | string | SPU unique identifier |
| `cate_name` | string | Category name |
| `sub_cate_name` | string | Subcategory name |
| `avg_unit_price` | float | Average unit price |
| `total_stores` | int | Number of stores selling this SPU |

---

## 4. Step 3: Prepare Matrix

### Purpose
Create normalized store-product matrices for clustering.

### Input
- `data/api_data/complete_category_sales_*.csv`
- `data/api_data/complete_spu_sales_*.csv`

### Output Files

#### `data/store_subcategory_matrix_YYYYMMP.csv`
Store × Subcategory sales matrix.

| Column | Type | Description |
|--------|------|-------------|
| `str_code` | string | Store unique identifier (index) |
| `[subcategory_1]` | float | Sales amount for subcategory 1 |
| `[subcategory_2]` | float | Sales amount for subcategory 2 |
| ... | ... | One column per subcategory |

#### `data/normalized_subcategory_matrix.csv`
Normalized (0-1 scaled) subcategory matrix.

| Column | Type | Description |
|--------|------|-------------|
| `str_code` | string | Store unique identifier (index) |
| `[subcategory_1]` | float | Normalized sales (0-1) |
| ... | ... | One column per subcategory |

#### `data/store_spu_limited_matrix.csv`
Store × Top-N SPU sales matrix.

| Column | Type | Description |
|--------|------|-------------|
| `str_code` | string | Store unique identifier (index) |
| `[spu_code_1]` | float | Sales amount for SPU 1 |
| ... | ... | One column per top SPU (default: top 1000) |

#### `data/normalized_spu_limited_matrix.csv`
Normalized SPU matrix for clustering.

| Column | Type | Description |
|--------|------|-------------|
| `str_code` | string | Store unique identifier (index) |
| `[spu_code_1]` | float | Normalized sales (0-1) |
| ... | ... | One column per top SPU |

---

## 5. Step 4: Determine Optimal Clusters

### Purpose
Analyze optimal number of clusters using Elbow method and Silhouette scores.

### Input
- `data/normalized_*_matrix.csv`

### Output Files

#### `output/optimal_k_analysis.csv`
Cluster count analysis results.

| Column | Type | Description |
|--------|------|-------------|
| `k` | int | Number of clusters tested |
| `inertia` | float | Within-cluster sum of squares |
| `silhouette_score` | float | Silhouette coefficient |
| `calinski_harabasz` | float | Calinski-Harabasz index |
| `davies_bouldin` | float | Davies-Bouldin index |

---

## 6. Step 5: K-Means Clustering

### Purpose
Perform K-Means clustering on normalized matrix.

### Input
- `data/normalized_*_matrix.csv`
- Optimal K from Step 4

### Output Files

#### `output/clustering_results_subcategory_YYYYMMP.csv`
Subcategory-level clustering results.

| Column | Type | Description |
|--------|------|-------------|
| `str_code` | string | Store unique identifier |
| `cluster_id` | int | Assigned cluster (0 to K-1) |
| `distance_to_centroid` | float | Distance to cluster center |

---

## 7. Step 6: Cluster Analysis

### Purpose
Perform PCA dimensionality reduction, K-Means clustering with quality metrics, and optional temperature-aware clustering.

### Input
- `data/normalized_spu_limited_matrix.csv`
- `output/stores_with_feels_like_temperature.csv` (optional)

### Output Files

#### `output/clustering_results_spu_YYYYMMP.csv`
SPU-level clustering results with PCA.

| Column | Type | Description |
|--------|------|-------------|
| `str_code` | string | Store unique identifier |
| `cluster_id` | int | Assigned cluster (0 to K-1) |
| `PC1` | float | First principal component |
| `PC2` | float | Second principal component |
| ... | ... | Up to PC50 (configurable) |
| `distance_to_centroid` | float | Distance to cluster center |

#### `output/cluster_profiles_spu_YYYYMMP.csv`
Cluster profile summaries.

| Column | Type | Description |
|--------|------|-------------|
| `cluster_id` | int | Cluster identifier |
| `store_count` | int | Number of stores in cluster |
| `avg_total_sales` | float | Average total sales |
| `top_categories` | string | Top selling categories |
| `temperature_zone` | string | Dominant temperature zone (if enabled) |

#### `output/cluster_metrics.csv`
Clustering quality metrics.

| Column | Type | Description |
|--------|------|-------------|
| `metric` | string | Metric name |
| `value` | float | Metric value |
| `interpretation` | string | Quality interpretation |

**Metrics included:**
- `silhouette_score`: Cluster separation quality (-1 to 1, higher is better)
- `calinski_harabasz_score`: Cluster density ratio (higher is better)
- `davies_bouldin_score`: Cluster similarity (lower is better)
- `pca_explained_variance`: Variance explained by PCA components

---

## 8. Step 7: Product Mix Rules

### Purpose
Generate product mix rules based on cluster analysis.

### Input
- `output/clustering_results_spu_*.csv`
- `data/api_data/complete_spu_sales_*.csv`

### Output Files

#### `output/spu_rules_YYYYMMP.csv`
SPU-level product mix rules.

| Column | Type | Description |
|--------|------|-------------|
| `cluster_id` | int | Cluster identifier |
| `spu_code` | string | SPU identifier |
| `rule_type` | string | Rule type (MUST_HAVE, RECOMMENDED, AVOID) |
| `confidence` | float | Rule confidence (0-1) |
| `support` | float | Rule support (% of stores) |
| `avg_sales` | float | Average sales in cluster |
| `penetration_rate` | float | % of cluster stores with this SPU |

#### `output/category_rules_YYYYMMP.csv`
Category-level aggregated rules.

| Column | Type | Description |
|--------|------|-------------|
| `cluster_id` | int | Cluster identifier |
| `cate_name` | string | Category name |
| `sub_cate_name` | string | Subcategory name |
| `recommended_spu_count` | int | Number of recommended SPUs |
| `avg_category_sales` | float | Average category sales |
| `category_penetration` | float | Category penetration rate |

#### `output/consolidated_rules.csv`
All rules consolidated for downstream use.

| Column | Type | Description |
|--------|------|-------------|
| `cluster_id` | int | Cluster identifier |
| `rule_id` | string | Unique rule identifier |
| `rule_type` | string | Rule type |
| `target_type` | string | SPU or CATEGORY |
| `target_code` | string | SPU code or category name |
| `action` | string | ADD, REMOVE, MAINTAIN |
| `priority` | int | Rule priority (1=highest) |

---

## 9. Step 8: Visualization Dashboard

### Purpose
Create interactive visualizations and maps.

### Input
- `output/clustering_results_*.csv`
- `data/store_coordinates_extended.csv`
- `output/cluster_profiles_*.csv`

### Output Files

#### `output/cluster_map.html`
Interactive Folium map showing store clusters.

**Features:**
- Color-coded markers by cluster
- Popup with store details
- Cluster boundaries
- Temperature zone overlays (if enabled)

#### `output/dashboard_YYYYMMP.html`
Comprehensive dashboard with charts.

**Sections:**
- Cluster distribution pie chart
- Sales by cluster bar chart
- Geographic distribution map
- Category breakdown by cluster
- Quality metrics summary

---

## 10. Extended Steps

### Step 10-14: SPU Assortment Optimization

| Step | Output | Description |
|------|--------|-------------|
| Step 10 | `spu_assortment_optimization.csv` | Optimized SPU assortment per cluster |
| Step 11 | `missed_sales_opportunities.csv` | Identified missed sales opportunities |
| Step 12 | `sales_performance_rules.csv` | Performance-based rules |
| Step 13 | `consolidated_spu_rules.csv` | All SPU rules merged |
| Step 14 | `fast_fish_format_output.csv` | Client-ready format |

### Step 15-20: Validation & Enrichment

| Step | Output | Description |
|------|--------|-------------|
| Step 15 | `historical_baseline.csv` | Historical baseline data |
| Step 16 | `comparison_tables.xlsx` | Period comparison tables |
| Step 17 | `augmented_recommendations.csv` | Enhanced recommendations |
| Step 18 | `validation_report.csv` | Data validation results |
| Step 19 | `detailed_spu_breakdown.csv` | Detailed SPU analysis |
| Step 20 | `data_validation_summary.csv` | Validation summary |

### Step 21-30: Advanced Analytics

| Step | Output | Description |
|------|--------|-------------|
| Step 21 | `label_tag_recommendations.csv` | Label/tag recommendations |
| Step 22 | `store_attributes_enriched.csv` | Enriched store attributes |
| Step 23 | `updated_clustering_features.csv` | Updated features |
| Step 24 | `cluster_labels.csv` | Comprehensive cluster labels |
| Step 25 | `product_roles.csv` | Product role classifications |
| Step 26 | `price_elasticity.csv` | Price elasticity analysis |
| Step 27 | `gap_matrix.csv` | Supply-demand gap matrix |
| Step 28 | `scenario_analysis.csv` | What-if scenarios |
| Step 29 | `supply_demand_gaps.csv` | Gap analysis results |
| Step 30 | `optimization_results.csv` | MILP optimization output |

---

## 11. Data Type Standards

### String Identifiers
- `str_code`: Always string, never integer
- `spu_code`: Always string
- `cluster_id`: Integer (0-indexed)

### Numeric Values
- Sales amounts: float64
- Quantities: float64
- Coordinates: float64 (longitude: -180 to 180, latitude: -90 to 90)
- Percentages: float64 (0.0 to 1.0)

### Date/Period Formats
- `YYYYMM`: 6-digit year-month (e.g., "202509")
- `YYYYMMP`: 7-character period (e.g., "202509A", "202509B")
- `yyyy`: 4-digit year integer
- `mm`: 1-2 digit month integer
- `mm_type`: Period indicator ("6A", "06B", etc.)

---

## 12. File Naming Conventions

```
[output_type]_[analysis_level]_[period].csv

Examples:
- clustering_results_spu_202509A.csv
- cluster_profiles_subcategory_202509A.csv
- normalized_spu_limited_matrix.csv
- store_coordinates_extended.csv
```

---

**Document Version:** 1.0  
**Author:** Data Pipeline Team
