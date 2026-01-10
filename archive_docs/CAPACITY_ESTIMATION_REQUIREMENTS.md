# Store Capacity & Tier Estimation Requirements
## Rigorous, Real Data-Based Implementation

**Generated:** July 23, 2025  
**Version:** 2.0 - Comprehensive Real Data Requirements  
**Status:** MANDATORY - No Synthetic Data Allowed

---

## Executive Summary

The current capacity estimation logic is inadequate and relies on heuristic guesses rather than rigorous data analysis. This document defines the exact requirements for implementing a comprehensive, real data-based store capacity and tier estimation system that meets business standards.

---

## 1. EXACT REQUIREMENTS DEFINITION

### 1.1 Store Capacity Estimation Requirements

**REQUIREMENT 1-1A: Physical Capacity Estimation**
- **Input Data:** Real sales volume (`spu_sales_amt`, `spu_sales_qty`), SKU diversity (`spu_code` count), category breadth
- **Logic:** Capacity = f(Sales_Velocity, SKU_Turnover, Category_Density, Historical_Performance)
- **Formula:** `Physical_Capacity = (Peak_Sales_Volume / Turnover_Rate) × Safety_Factor`
- **Validation:** Must correlate with actual store performance metrics
- **Output:** `estimated_physical_capacity` (units), `capacity_confidence_score` (0-1)

**REQUIREMENT 1-1B: Operational Capacity Estimation**
- **Input Data:** SPU-store-days inventory calculations, sell-through rates, historical sales patterns
- **Logic:** Operational_Capacity = f(Inventory_Days, Sales_Velocity, Replenishment_Cycle)
- **Formula:** `Operational_Capacity = (Average_Daily_Sales × Inventory_Cycle_Days) × Efficiency_Factor`
- **Validation:** Must align with business rule recommendations and overcapacity analysis
- **Output:** `operational_capacity` (units/period), `capacity_utilization_rate` (%)

### 1.2 Store Tier Classification Requirements

**REQUIREMENT 1-2A: Size Tier Classification**
- **Input Data:** Total sales volume, SKU diversity, category coverage, store performance metrics
- **Logic:** Multi-dimensional classification using real performance data
- **Tiers:** 
  - **Tier 1 (Large):** Top 20% by composite capacity score
  - **Tier 2 (Medium):** Middle 60% by composite capacity score
  - **Tier 3 (Small):** Bottom 20% by composite capacity score
- **Validation:** Tier distribution must reflect actual business performance patterns
- **Output:** `size_tier`, `tier_percentile`, `tier_justification`

**REQUIREMENT 1-2B: Performance Tier Classification**
- **Input Data:** Sell-through rates, sales per SKU, inventory turnover, revenue per square meter equivalent
- **Logic:** Performance-based tiering using efficiency metrics
- **Tiers:**
  - **High-Performance:** Top 25% by efficiency composite score
  - **Standard-Performance:** Middle 50% by efficiency composite score
  - **Low-Performance:** Bottom 25% by efficiency composite score
- **Output:** `performance_tier`, `efficiency_score`, `performance_ranking`

---

## 2. REAL DATA SOURCES AVAILABLE

### 2.1 Primary Data Sources (Verified Available)

**Sales Volume Data:**
- `spu_sales_amt`: Total sales amount per store-SPU combination
- `spu_sales_qty`: Total quantity sold per store-SPU combination
- `base_sal_qty` / `fashion_sal_qty`: Category-specific quantities
- `base_sal_amt` / `fashion_sal_amt`: Category-specific sales amounts

**Inventory & Performance Data:**
- SPU-store-days inventory calculations (from step18_validate_results.py)
- Sell-through rate calculations: `(Sales / Inventory) × 100`
- Historical sales patterns and trends
- Average daily SPUs sold per store

**Product Diversity Data:**
- `spu_code`: Unique product identifiers per store
- `cate_name`: Category diversity per store
- `sub_cate_name`: Subcategory diversity per store
- Product mix ratios (fashion/basic percentages)

**Business Rule Data:**
- Overcapacity analysis results (step10_spu_assortment_optimization.py)
- Below minimum threshold analysis (step9_below_minimum_rule.py)
- Target vs. actual SPU counts per category

### 2.2 Derived Metrics (Calculable from Real Data)

**Capacity Indicators:**
- Sales velocity: `Total_Sales / Time_Period`
- SKU turnover rate: `Sales_Quantity / SKU_Count`
- Category density: `Categories / Total_SKUs`
- Inventory efficiency: `Sell_Through_Rate`

**Performance Indicators:**
- Revenue per SKU: `Total_Sales / SKU_Count`
- Sales per category: `Category_Sales / Category_Count`
- Capacity utilization: `Current_Performance / Estimated_Capacity`
- Efficiency score: Composite of turnover, sell-through, and revenue metrics

---

## 3. RIGOROUS ESTIMATION ALGORITHMS

### 3.1 Physical Capacity Estimation Algorithm

```python
def calculate_physical_capacity(store_sales_data, historical_data):
    """
    Calculate physical store capacity using real sales and performance data.
    
    Algorithm:
    1. Calculate peak sales volume (95th percentile of daily sales)
    2. Determine average inventory turnover rate from sell-through data
    3. Estimate space efficiency from SKU density patterns
    4. Apply safety factor based on category mix and seasonality
    
    Formula:
    Physical_Capacity = (Peak_Daily_Sales × Inventory_Cycle_Days) × (1 + Safety_Factor)
    
    Where:
    - Peak_Daily_Sales = 95th percentile of daily sales volume
    - Inventory_Cycle_Days = Average days to sell through inventory
    - Safety_Factor = 0.2-0.5 based on category volatility
    """
    
    # Step 1: Calculate peak sales performance
    daily_sales = store_sales_data.groupby('date')['spu_sales_qty'].sum()
    peak_daily_sales = daily_sales.quantile(0.95)
    
    # Step 2: Calculate inventory turnover from real data
    total_inventory_days = calculate_inventory_days(store_sales_data)
    avg_turnover_days = total_inventory_days.mean()
    
    # Step 3: Calculate space efficiency
    sku_density = len(store_sales_data['spu_code'].unique())
    category_density = len(store_sales_data['cate_name'].unique())
    space_efficiency = sku_density / max(category_density, 1)
    
    # Step 4: Apply safety factor based on category mix
    fashion_ratio = calculate_fashion_ratio(store_sales_data)
    safety_factor = 0.2 + (fashion_ratio * 0.3)  # Fashion items need more buffer
    
    # Calculate physical capacity
    base_capacity = peak_daily_sales * avg_turnover_days
    physical_capacity = base_capacity * (1 + safety_factor)
    
    # Calculate confidence score
    confidence_score = calculate_confidence_score(
        data_completeness=len(daily_sales) / 90,  # 90 days ideal
        performance_consistency=1 - daily_sales.std() / daily_sales.mean(),
        category_coverage=category_density / 10  # 10 categories ideal
    )
    
    return physical_capacity, confidence_score
```

### 3.2 Operational Capacity Estimation Algorithm

```python
def calculate_operational_capacity(store_data, business_rules_data):
    """
    Calculate operational capacity using business performance metrics.
    
    Algorithm:
    1. Analyze current capacity utilization from business rules
    2. Calculate optimal capacity from sell-through targets
    3. Adjust for seasonal and category-specific factors
    4. Validate against overcapacity/undercapacity analysis
    
    Formula:
    Operational_Capacity = Target_Sell_Through_Volume / Target_Sell_Through_Rate
    """
    
    # Step 1: Get current performance metrics
    current_sell_through = store_data['sell_through_rate'].mean()
    current_inventory = store_data['spu_store_days_inventory'].sum()
    current_sales = store_data['spu_store_days_sales'].sum()
    
    # Step 2: Calculate target performance (80% sell-through rate)
    target_sell_through_rate = 0.80
    target_inventory_level = current_sales / target_sell_through_rate
    
    # Step 3: Adjust for business rule findings
    overcapacity_adjustment = get_overcapacity_adjustment(business_rules_data)
    undercapacity_adjustment = get_undercapacity_adjustment(business_rules_data)
    
    # Step 4: Calculate operational capacity
    operational_capacity = target_inventory_level * (1 + overcapacity_adjustment - undercapacity_adjustment)
    
    # Step 5: Calculate utilization rate
    utilization_rate = current_inventory / operational_capacity
    
    return operational_capacity, utilization_rate
```

### 3.3 Store Tier Classification Algorithm

```python
def classify_store_tier(store_metrics):
    """
    Classify store tier using multi-dimensional real data analysis.
    
    Algorithm:
    1. Calculate composite capacity score from multiple metrics
    2. Normalize scores across all stores
    3. Apply percentile-based tier classification
    4. Validate tier assignment against business performance
    """
    
    # Step 1: Calculate composite metrics
    capacity_score = (
        store_metrics['physical_capacity'] * 0.4 +
        store_metrics['operational_capacity'] * 0.3 +
        store_metrics['sales_volume'] * 0.2 +
        store_metrics['sku_diversity'] * 0.1
    )
    
    # Step 2: Calculate performance score
    performance_score = (
        store_metrics['sell_through_rate'] * 0.3 +
        store_metrics['revenue_per_sku'] * 0.3 +
        store_metrics['inventory_turnover'] * 0.2 +
        store_metrics['capacity_utilization'] * 0.2
    )
    
    # Step 3: Determine tier based on percentiles
    capacity_percentile = calculate_percentile(capacity_score)
    performance_percentile = calculate_percentile(performance_score)
    
    # Size tier classification
    if capacity_percentile >= 80:
        size_tier = "Large"
    elif capacity_percentile >= 40:
        size_tier = "Medium"
    else:
        size_tier = "Small"
    
    # Performance tier classification
    if performance_percentile >= 75:
        performance_tier = "High-Performance"
    elif performance_percentile >= 25:
        performance_tier = "Standard-Performance"
    else:
        performance_tier = "Low-Performance"
    
    return size_tier, performance_tier, capacity_percentile, performance_percentile
```

---

## 4. VALIDATION REQUIREMENTS

### 4.1 Data Quality Validation

**REQUIREMENT 4-1A: Input Data Validation**
- Minimum 30 days of sales data per store
- At least 10 SKUs per store for meaningful analysis
- Non-zero sales volume and inventory data
- Complete category and subcategory information

**REQUIREMENT 4-1B: Calculation Validation**
- Capacity estimates must be positive and realistic (10-10,000 units)
- Tier classifications must have reasonable distribution (not all stores in one tier)
- Confidence scores must reflect actual data quality
- Results must be reproducible with same input data

### 4.2 Business Logic Validation

**REQUIREMENT 4-2A: Business Rule Consistency**
- Capacity estimates must align with overcapacity analysis findings
- High-capacity stores should not appear in "below minimum" analysis
- Tier classifications must correlate with actual sales performance
- Fashion/basic ratios must influence capacity calculations appropriately

**REQUIREMENT 4-2B: Performance Validation**
- Large stores must have higher average sales than small stores
- High-performance stores must have better sell-through rates
- Capacity utilization must correlate with business rule recommendations
- Tier assignments must be stable across similar stores

---

## 5. IMPLEMENTATION DELIVERABLES

### 5.1 Required Code Deliverables

1. **Enhanced Capacity Estimation Engine**
   - File: `step22_enhanced_capacity_estimation.py`
   - Functions: Physical capacity, operational capacity, tier classification
   - Validation: Comprehensive data quality and business logic checks

2. **Capacity Validation Framework**
   - File: `capacity_validation_framework.py`
   - Functions: Data validation, business rule consistency, performance testing
   - Output: Validation reports and quality metrics

3. **Updated Store Attribute Integration**
   - File: Updated `step22_store_attribute_enrichment.py`
   - Integration: Enhanced capacity logic with existing attribute calculation
   - Output: Comprehensive store attributes with rigorous capacity estimates

### 5.2 Required Documentation Deliverables

1. **Capacity Estimation Methodology Report**
   - Detailed explanation of all algorithms and formulas
   - Data source documentation and validation criteria
   - Business justification for all parameters and thresholds

2. **Validation Results Report**
   - Comprehensive testing results for all stores
   - Data quality assessment and confidence scoring
   - Business rule consistency analysis

3. **Implementation Guide**
   - Step-by-step implementation instructions
   - Integration requirements with existing pipeline
   - Maintenance and update procedures

---

## 6. SUCCESS CRITERIA

### 6.1 Technical Success Criteria

- **Data Coverage:** 95%+ of stores have valid capacity estimates
- **Confidence Scores:** 80%+ of estimates have confidence ≥ 0.7
- **Tier Distribution:** Reasonable distribution across all tiers (not skewed)
- **Validation Pass Rate:** 90%+ of estimates pass business logic validation

### 6.2 Business Success Criteria

- **Business Rule Alignment:** Capacity estimates align with business rule findings
- **Performance Correlation:** Tier classifications correlate with actual performance
- **Actionable Insights:** Results provide clear guidance for inventory allocation
- **Stakeholder Acceptance:** Business users can understand and trust the results

---

## 7. IMPLEMENTATION TIMELINE

1. **Phase 1:** Enhanced capacity estimation algorithms (2-3 hours)
2. **Phase 2:** Comprehensive validation framework (1-2 hours)
3. **Phase 3:** Integration and testing (1 hour)
4. **Phase 4:** Documentation and validation reports (1 hour)

**Total Estimated Time:** 5-7 hours for complete implementation

---

This document provides the exact requirements for implementing rigorous, real data-based store capacity and tier estimation. No synthetic data, no guesses, no placeholders - only comprehensive analysis using available business data.
