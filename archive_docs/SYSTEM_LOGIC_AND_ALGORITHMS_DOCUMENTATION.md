# System Logic and Algorithms Documentation
## Retail Product Mix Optimization System

**Generated:** July 23, 2025  
**Version:** 2.0  
**System:** 20-Step Product Mix Clustering Pipeline

---

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Data Collection & Processing](#data-collection--processing)
3. [Weather Integration Logic](#weather-integration-logic)
4. [Clustering Algorithms](#clustering-algorithms)
5. [Business Rules Logic](#business-rules-logic)
6. [Optimization & Validation](#optimization--validation)
7. [Output Generation](#output-generation)
8. [Mathematical Models](#mathematical-models)

---

## System Architecture Overview

### Pipeline Flow Logic
```
Data Collection → Weather Integration → Matrix Preparation → Clustering → Business Rules → Optimization → Validation → Output Generation
```

### Core Processing Phases
1. **Data Ingestion** (Steps 1-3): API data collection and matrix preparation
2. **Environmental Analysis** (Steps 4-5): Weather data integration and temperature analysis
3. **Clustering** (Step 6): Temperature-aware store clustering
4. **Business Logic** (Steps 7-12): Six optimization rules application
5. **Consolidation** (Steps 13-15): Results aggregation and formatting
6. **Advanced Analysis** (Steps 16-20): Validation, trending, and reporting

---

## Data Collection & Processing

### 1. API Data Collection Algorithm (Step 1)

**Purpose:** Collect sales and configuration data from FastFish API

**Key Logic:**
```python
def collect_api_data(period_config):
    # 1. Period Configuration
    period_ranges = generate_period_ranges(period_config)
    
    # 2. Parallel Data Collection with Retry
    for period in period_ranges:
        sales_data = fetch_sales_data(period, retry_count=3)
        store_config = fetch_store_config(period)
        validated_data = validate_and_deduplicate(sales_data, store_config)
    
    # 3. Data Consolidation
    return merge_period_data(all_periods)
```

**Features:**
- **Retry Logic:** 3-attempt retry with exponential backoff
- **Deduplication:** Remove duplicates based on (str_code, spu_code) pairs
- **Period Handling:** Support for A/B period splits and full month analysis

### 2. Matrix Preparation Algorithm (Step 3)

**Purpose:** Transform sales data into clustering-ready matrices

**Matrix Types:**
- **SPU Matrix:** Top 1000 SPUs by sales volume
- **Subcategory Matrix:** Store × subcategory sales matrix
- **Category Aggregated Matrix:** Store × category sales matrix

**Normalization Methods:**
- **Min-Max Scaling:** Scale values to [0,1] range
- **Z-Score Normalization:** Center around mean with unit variance

---

## Weather Integration Logic

### Feels-Like Temperature Calculation (Step 5)

**Purpose:** Calculate perceived temperature for clustering constraints

**Algorithm:**
```python
def calculate_feels_like_temperature(temp, humidity, wind_speed, altitude):
    # 1. Base Calculation
    if temp >= 27:  # Hot conditions
        feels_like = calculate_heat_index(temp, humidity)
    elif temp <= 10:  # Cold conditions
        feels_like = calculate_wind_chill(temp, wind_speed)
    else:  # Moderate conditions
        feels_like = temp
    
    # 2. Altitude Adjustment
    altitude_adjustment = (altitude / 1000) * -0.65  # Lapse rate
    feels_like_adjusted = feels_like + altitude_adjustment
    
    # 3. Temperature Band Classification (5-degree bands)
    return classify_temperature_band(feels_like_adjusted)
```

**Formulas:**
- **Heat Index:** `HI = c1 + c2*T + c3*RH + c4*T*RH + c5*T² + c6*RH² + ...`
- **Wind Chill:** `WC = 13.12 + 0.6215*T - 11.37*V^0.16 + 0.3965*T*V^0.16`

---

## Clustering Algorithms

### Temperature-Aware K-Means Clustering (Step 6)

**Purpose:** Group similar stores while respecting temperature constraints

**Algorithm Logic:**
```python
def temperature_aware_clustering(normalized_data, temperature_data, n_clusters):
    # 1. PCA Dimensionality Reduction
    pca_components = get_pca_components(matrix_type)
    pca_data = pca.fit_transform(normalized_data)
    
    # 2. Temperature Band Grouping
    temp_groups = group_by_temperature_bands(temperature_data)
    
    # 3. Constrained Clustering within Temperature Bands
    final_labels = []
    for temp_band, stores_in_band in temp_groups.items():
        band_data = pca_data[stores_in_band]
        band_clusters = determine_optimal_clusters(band_data)
        
        kmeans = KMeans(n_clusters=band_clusters, random_state=42)
        band_labels = kmeans.fit_predict(band_data)
        final_labels.extend(adjust_labels(band_labels))
    
    # 4. Cluster Balance Enforcement (50 stores per cluster)
    return enforce_cluster_balance(final_labels, min_size=50, max_size=50)
```

**PCA Configuration:**
- **SPU Matrix:** 100 components
- **Subcategory Matrix:** 50 components
- **Category Matrix:** 20 components

### Cluster Quality Metrics

**Assessment Methods:**
- **Silhouette Score:** Cluster separation quality
- **Calinski-Harabasz Index:** Cluster definition quality
- **Davies-Bouldin Index:** Cluster compactness
- **Temperature Constraint Compliance:** Constraint satisfaction rate

---

## Business Rules Logic

### 1. Missing Category/SPU Rule (Step 7)

**Purpose:** Identify stores missing well-selling products from their cluster

**Logic:**
```python
def identify_missing_opportunities(sales_data, cluster_data):
    # 1. Identify Well-Selling Features per Cluster
    for cluster_id in clusters:
        cluster_sales = get_cluster_sales(cluster_id)
        
        # Define well-selling criteria
        min_store_coverage = 30%  # Present in 30% of cluster stores
        min_sales_performance = top_30%  # Top 30% by sales
        
        well_selling_features = apply_criteria(cluster_sales)
    
    # 2. Find Missing Opportunities
    for store in cluster_stores:
        missing_features = well_selling_features - store_features
        for missing in missing_features:
            recommend_quantity = calculate_cluster_average(missing)
```

**Criteria:**
- **Store Coverage:** Feature present in ≥30% of cluster stores
- **Sales Performance:** Feature in top 30% by sales volume
- **Quantity Recommendation:** Based on cluster average with minimum 1 unit

### 2. Imbalanced Allocation Rule (Step 8)

**Purpose:** Identify and correct allocation imbalances using Z-score analysis

**Statistical Method:**
```python
def identify_imbalanced_allocations(sales_data, cluster_data):
    for cluster_id in clusters:
        for feature in cluster_features:
            quantities = get_feature_quantities(feature, cluster_id)
            z_scores = calculate_z_scores(quantities)
            
            # Identify imbalances (|Z-score| > 2)
            imbalanced_stores = stores_where(abs(z_score) > 2)
            
            for store in imbalanced_stores:
                if z_score > 2:  # Over-allocated
                    recommend_quantity = cluster_mean
                else:  # Under-allocated
                    recommend_quantity = cluster_mean + cluster_std
```

**Thresholds:**
- **Imbalance Detection:** |Z-score| > 2.0
- **Rebalancing Target:** Cluster mean ± standard deviation

### 3. Below Minimum Threshold Rule (Step 9)

**Purpose:** Identify stores with quantities below minimum viable thresholds

**Thresholds:**
- **SPU Level:** Minimum 2 units, ¥100 sales
- **Subcategory Level:** Minimum 5 units, ¥500 sales

**Logic:**
```python
def identify_below_minimum_opportunities(sales_data):
    for store in stores:
        store_performance = calculate_performance(store)
        below_minimum = filter_below_thresholds(store_performance)
        
        for feature in below_minimum:
            cluster_benchmark = get_cluster_benchmark(feature)
            recommend_quantity = max(minimum_threshold, cluster_benchmark * 0.8)
```

### 4. Smart Overcapacity Rule (Step 10)

**Purpose:** Identify strategic overcapacity opportunities for high-performers

**Selection Criteria:**
- **High Performance:** Sales velocity in top 20%
- **Above Average:** Already 20% above cluster average
- **Capacity Available:** Store utilization < 85%

**Logic:**
```python
def identify_smart_overcapacity_opportunities(sales_data):
    high_performers = select_top_performers(sales_data, percentile=80)
    
    for performer in high_performers:
        if current_qty >= cluster_avg * 1.2:  # Already above average
            if capacity_utilization < 0.85:  # Has capacity
                strategic_increase = current_qty * 0.15  # 15% increase
                recommend_quantity = current_qty + strategic_increase
```

### 5. Missed Sales Opportunity Rule (Step 11)

**Purpose:** Identify missed sales opportunities through comparative analysis

**Method:**
```python
def identify_missed_sales_opportunities(sales_data):
    for category in categories:
        top_performers = identify_top_performers(category, percentile=80)
        
        for cluster in clusters:
            cluster_avg = calculate_cluster_average(category, cluster)
            underperformers = find_underperformers(cluster, threshold=0.7)
            
            for underperformer in underperformers:
                sales_gap = cluster_avg - current_sales
                qty_increase = estimate_qty_needed(sales_gap)
```

### 6. Sales Performance Gap Rule (Step 12)

**Purpose:** Identify performance gaps using statistical deviation analysis

**Method:**
```python
def identify_sales_performance_gaps(sales_data):
    for cluster in clusters:
        for feature in cluster_features:
            sales_data = get_feature_sales(feature, cluster)
            z_scores = calculate_z_scores(sales_data)
            
            # Underperformers: Z-score < -1.5
            underperformers = filter_underperformers(z_scores, threshold=-1.5)
            
            for underperformer in underperformers:
                target_sales = cluster_mean
                qty_increase = calculate_qty_needed(target_sales - current_sales)
```

---

## Optimization & Validation

### Sell-Through Rate Calculation (Step 18)

**Purpose:** Calculate inventory turnover metrics for optimization focus

**Formula:**
```python
def calculate_sell_through_rate(spu_data, sales_data):
    # SPU-store-days calculation
    spu_store_days_inventory = target_quantity * stores_in_group * period_days
    spu_store_days_sales = historical_sales_sum
    
    # Sell-through rate
    sell_through_rate = (spu_store_days_sales / spu_store_days_inventory) * 100
    
    return sell_through_rate
```

**Enhancement Logic:**
```python
def add_sell_through_calculations(recommendations):
    for recommendation in recommendations:
        current_st_rate = calculate_current_sell_through(recommendation)
        target_st_rate = calculate_target_sell_through(recommendation)
        improvement = target_st_rate - current_st_rate
        
        recommendation.update({
            'current_sell_through_rate': current_st_rate,
            'target_sell_through_rate': target_st_rate,
            'sell_through_improvement': improvement
        })
```

### Data Validation Logic (Step 20)

**Validation Types:**
1. **Mathematical Consistency:** SPU → Store → Cluster aggregation validation
2. **Data Completeness:** Missing value and duplicate detection
3. **Business Logic Validation:** Reasonable quantities and investments
4. **Constraint Compliance:** Temperature and capacity constraint checking

---

## Output Generation

### Enhanced Fast Fish Format (Step 14)

**Purpose:** Create standardized output format with dimensional aggregation

**Logic:**
```python
def create_enhanced_fast_fish_format(api_data):
    # 1. Dimensional Aggregation
    grouped = api_data.groupby(['Store_Group_Name', 'cate_name', 'sub_cate_name'])
    
    for group_key, group_data in grouped:
        # 2. Customer Mix Calculation
        customer_mix = calculate_customer_mix_percentages(group_data)
        
        # 3. Target Style Tags Generation
        target_style_tags = create_dimensional_target_style_tags(
            season, gender, location, category, subcategory
        )
        
        # 4. SPU Quantity Recommendations
        current_spu_quantity = group_data['spu_code'].nunique()
        target_spu_quantity = apply_business_rules(current_spu_quantity)
        
        # 5. Record Creation
        record = create_enhanced_record(group_key, customer_mix, target_style_tags, quantities)
```

### Label Tag Recommendations (Step 21)

**Purpose:** Generate professional bilingual tag recommendations

**Features:**
- **Multi-sheet Excel format** with summary and detailed views
- **Bilingual headers** (Chinese/English)
- **Constraint analysis** and optimization opportunities
- **Professional formatting** with conditional formatting

---

## Mathematical Models

### Temperature Band Classification

**Formula:**
```python
def classify_temperature_band(temp):
    band_size = 5  # 5-degree bands
    band_lower = int(np.floor(temp / band_size) * band_size)
    band_upper = band_lower + band_size
    return f"{band_lower}°C to {band_upper}°C"
```

### Z-Score Analysis

**Formula:**
```python
def calculate_z_score(value, mean, std):
    return (value - mean) / std if std > 0 else 0
```

**Interpretation:**
- **|Z-score| > 2.0:** Significant deviation (imbalance)
- **Z-score < -1.5:** Underperformance
- **Z-score > 2.0:** Overallocation

### Cluster Balance Enforcement

**Algorithm:**
```python
def enforce_cluster_balance(labels, min_size=50, max_size=50):
    for iteration in range(max_iterations):
        cluster_sizes = calculate_cluster_sizes(labels)
        oversized = find_oversized_clusters(cluster_sizes, max_size)
        undersized = find_undersized_clusters(cluster_sizes, min_size)
        
        if not oversized and not undersized:
            break  # Balanced
        
        labels = rebalance_clusters(labels, oversized, undersized)
    
    return labels
```

### Performance Metrics

**System Performance:**
- **Processing Speed:** ~65 minutes for 2,000+ stores
- **Data Volume:** Handles 2.3MB+ result files
- **Accuracy:** Silhouette scores ≥ 0.5 for cluster quality
- **Coverage:** 100% store coverage with constraint compliance

**Business Metrics:**
- **Sell-Through Rate:** Primary optimization KPI
- **Revenue Impact:** Secondary consideration
- **Inventory Velocity:** Turnover optimization
- **Constraint Satisfaction:** Capacity, temperature, style alignment

---

## Algorithm Complexity

### Time Complexity
- **Data Collection:** O(n) where n = number of API calls
- **Matrix Preparation:** O(m × s) where m = products, s = stores
- **Clustering:** O(k × i × s × d) where k = clusters, i = iterations, s = stores, d = dimensions
- **Business Rules:** O(r × s × p) where r = rules, s = stores, p = products

### Space Complexity
- **Matrix Storage:** O(s × p) for store-product matrices
- **Clustering Data:** O(s × d) for PCA-transformed data
- **Results Storage:** O(s × r × p) for all recommendations

This documentation provides a comprehensive overview of all logic and algorithms used in the retail product mix optimization system. Each component is designed for scalability, accuracy, and business relevance.
