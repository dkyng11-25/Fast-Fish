# Product Structure Optimization Module Design

## **Current Status: ❌ ALL MISSING - Complete Implementation Required**

The system currently **lacks all three critical components** of the Product Structure Optimisation Module:

### **1. Cluster × Role Gap Analysis (店群×角色供需差距) - ❌ MISSING**

**Required Implementation:**
```python
# Product Role Classification
PRODUCT_ROLES = {
    'CORE': 'Core bestsellers (>80% sell-through)',
    'SEASONAL': 'Seasonal drivers (40-80% sell-through)', 
    'FILLER': 'Gap fillers (20-40% sell-through)',
    'CLEARANCE': 'Clearance items (<20% sell-through)'
}

def analyze_cluster_role_gaps(cluster_data, sales_data):
    for cluster in clusters:
        for role in PRODUCT_ROLES:
            supply = calculate_current_supply(cluster, role)
            demand = calculate_predicted_demand(cluster, role)
            gap = demand - supply
            priority = classify_gap_priority(gap)
            recommendation = generate_action_plan(gap, role)
```

**Output Format:**
```csv
Cluster_ID,Cluster_Name,Product_Role,Current_Supply,Predicted_Demand,Gap,Gap_Percentage,Priority,Recommended_Action
Cluster_0,北京温带时尚集群,CORE,2,5,3,60%,HIGH,增加3个核心爆款产品
Cluster_1,上海亚热带基础集群,SEASONAL,8,5,-3,-37.5%,MEDIUM,减少3个季节驱动产品
```

### **2. Price-Band & Substitution Analysis (价格带&替代性分析) - ❌ MISSING**

**Required Implementation:**
```python
# Price Band Classification
PRICE_BANDS = {
    'PREMIUM': '¥200+',
    'MID_HIGH': '¥100-200',
    'MID': '¥50-100', 
    'ECONOMY': '¥0-50'
}

def analyze_substitution_effects(spu_data, sales_data):
    for spu1, spu2 in product_pairs:
        elasticity = calculate_cross_elasticity(spu1, spu2)
        substitution_strength = classify_substitution(elasticity)
        price_impact = analyze_price_sensitivity(spu1, spu2)
        recommendation = generate_substitution_strategy(elasticity, price_impact)
```

**Output Format:**
```csv
SPU_1,SPU_2,Substitution_Elasticity,Substitution_Strength,Price_Band_1,Price_Band_2,Category_Overlap,Recommendation
SPU001,SPU002,-0.75,STRONG,PREMIUM,MID_HIGH,true,考虑合并或差异化定位
SPU003,SPU004,-0.35,MODERATE,MID,MID,false,监控价格竞争
```

### **3. What-If Scenario Analysis (情景模拟) - ❌ MISSING**

**Required Implementation:**
```python
# Scenario Framework
SCENARIO_TYPES = {
    'CAPACITY_CHANGE': '店铺容量变化',
    'PRICE_ADJUSTMENT': '价格调整',
    'PRODUCT_INTRODUCTION': '新品引入',
    'SEASONAL_SHIFT': '季节变化'
}

class WhatIfScenarioAnalyzer:
    def simulate_scenario(self, scenario_config):
        modified_data = apply_scenario_changes(base_data, scenario_config)
        impacts = calculate_all_impacts(modified_data)
        feasibility = assess_feasibility(impacts)
        return ScenarioResult(impacts, feasibility, recommendations)
```

**Output Format:**
```csv
Scenario_Name,Scenario_Type,Sell_Through_Impact,Revenue_Impact,Inventory_Impact,Feasibility_Score,Recommendation
店铺容量增加20%,CAPACITY_CHANGE,-3.2%,+18.5%,+24.0%,85.2,推荐实施
高端产品价格下调10%,PRICE_ADJUSTMENT,+12.8%,-2.1%,-8.5%,92.7,推荐实施
```

## **Implementation Priority:**

### **Phase 1: Cluster × Role Gap Analysis (2 days)**
1. **Product Role Classification Engine**
   - Implement sell-through based role classification
   - Create role-specific demand prediction models
   - Build gap analysis and priority scoring

2. **Gap Analysis Dashboard**
   - Cluster × role matrix visualization
   - Priority-based action recommendations
   - Supply-demand balance reporting

### **Phase 2: Price-Band & Substitution Analysis (2 days)**
1. **Price Band Classification System**
   - Implement dynamic price band boundaries
   - Create price elasticity analysis
   - Build cross-price impact models

2. **Substitution Analysis Engine**
   - Calculate substitution elasticity between products
   - Identify cannibalization risks
   - Generate portfolio optimization recommendations

### **Phase 3: What-If Scenario Analysis (2 days)**
1. **Scenario Simulation Framework**
   - Build configurable scenario engine
   - Implement impact calculation models
   - Create feasibility assessment logic

2. **Interactive Scenario Dashboard**
   - User-friendly scenario configuration
   - Real-time impact visualization
   - Sensitivity analysis tools

## **Key Benefits:**

### **Business Value:**
- **Optimize Product Mix**: Identify gaps and oversupply by cluster and role
- **Reduce Cannibalization**: Understand substitution effects between products
- **Strategic Planning**: Test scenarios before implementation
- **Inventory Efficiency**: Balance supply and demand across clusters

### **Technical Features:**
- **Real-time Analysis**: Dynamic gap detection and scenario simulation
- **Constraint-Aware**: Respects capacity, budget, and operational limits
- **Data-Driven**: Uses historical sales and clustering data
- **Actionable Insights**: Provides specific recommendations with priorities

## **Success Metrics:**
- **Gap Reduction**: Minimize supply-demand mismatches across clusters
- **Substitution Optimization**: Reduce cannibalization while maximizing coverage
- **Scenario Accuracy**: Validate scenario predictions against actual outcomes
- **Decision Support**: Improve strategic planning effectiveness

This module will transform the system from reactive analysis to proactive optimization with comprehensive what-if capabilities.
