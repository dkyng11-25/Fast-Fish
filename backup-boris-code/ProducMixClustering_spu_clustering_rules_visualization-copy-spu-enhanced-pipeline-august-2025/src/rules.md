Perfect! Let me explain each rule with the mathematical equations and technical details for complete clarity.

## **🔬 Technical Deep Dive: How Each Business Rule Works**

### **📋 Rule 7: Missing SPU Opportunities**
**Mathematical Foundation: Cluster-Based Opportunity Detection**

#### **Core Algorithm:**
```
For each cluster C and SPU s:
1. Store_Penetration(C,s) = Stores_Selling(C,s) / Total_Stores(C)
2. Well_Selling_Criteria:
   - Store_Penetration(C,s) ≥ 0.9 (90% adoption threshold)
   - Total_Cluster_Sales(C,s) ≥ 500 (minimum sales threshold)
   - Expected_Sales(s) ≥ 200 (minimum opportunity value)

3. Expected_Sales(s) = Total_Cluster_Sales(C,s) / Stores_Selling(C,s)

4. Missing_Opportunity = TRUE if:
   - Store ∈ Cluster(C) AND
   - Store does NOT sell SPU(s) AND  
   - Well_Selling_Criteria(C,s) = TRUE
```

#### **Threshold Logic:**
- **90% adoption**: Extremely popular products only (vs 70% for subcategories)
- **500 sales minimum**: High-volume opportunities only
- **200 opportunity value**: Significant revenue potential only

#### **Real Example:**
```
SPU 15K0025 in Cluster 43:
- Stores selling: 19/21 = 90.5% adoption ✓
- Total cluster sales: $147,042 ≥ $500 ✓  
- Expected sales per store: $147,042/19 = $7,739 ≥ $200 ✓
- Missing stores: 2 stores flagged for opportunity
```

---

### **⚖️ Rule 8: Imbalanced SPU Allocation**
**Mathematical Foundation: Z-Score Statistical Analysis**

#### **Core Algorithm:**
```
For each SPU s in cluster C:
1. Cluster_Mean(C,s) = Σ(Allocation(store,s)) / |Stores(C)|
2. Cluster_StdDev(C,s) = √(Σ(Allocation(store,s) - Mean)² / (|Stores(C)|-1))

3. Z_Score(store,s) = (Allocation(store,s) - Cluster_Mean(C,s)) / Cluster_StdDev(C,s)

4. Imbalanced = TRUE if:
   - |Z_Score(store,s)| > 4.0 AND
   - Cluster_Size(C) ≥ 5 AND
   - Allocation(store,s) ≥ 0.05
```

#### **Statistical Interpretation:**
- **Z > 4.0**: Over-allocated (99.997th percentile - extremely high)
- **Z < -4.0**: Under-allocated (0.003rd percentile - extremely low)  
- **Normal range**: -2.0 ≤ Z ≤ 2.0 (95% of stores should be here)

#### **Severity Classification:**
```
Severity = {
  EXTREME    if |Z| > 3.0
  HIGH       if 2.5 < |Z| ≤ 3.0  
  MODERATE   if 2.0 < |Z| ≤ 2.5
}
```

#### **Real Example:**
```
SPU 15P5003 in a store:
- Store allocation: 2.5 units
- Cluster mean: 0.3 units
- Cluster std dev: 0.4 units
- Z-score = (2.5 - 0.3) / 0.4 = 5.5 → EXTREME over-allocation
```

---

### **🎯 Rule 10: Smart Overcapacity**
**Mathematical Foundation: Multi-Profile Performance Gap Analysis**

#### **Core Algorithm:**
```
For each SPU s in store i, cluster C:
1. Space_Efficiency(i,s) = SPU_Sales(i,s) / SPU_Implied_Space(i,s)
2. SPU_Implied_Space(i,s) = (SPU_Sales_Share(i,s) × Subcategory_Space(i))
3. SPU_Sales_Share(i,s) = SPU_Sales(i,s) / Total_Subcategory_Sales(i)

4. Local_Performance(i,s) = Space_Efficiency(i,s)
5. Cluster_Performance(C,s) = Percentile_75(Space_Efficiency(stores ∈ C, s))

6. Performance_Gap(i,s) = (Cluster_Performance(C,s) - Local_Performance(i,s)) / Local_Performance(i,s)
```

#### **Multi-Profile Thresholds:**
```
Strict Profile (Conservative):
- Gap_Threshold ≥ 20%
- Local_Performance ≤ 500 efficiency units
- Target_Performance > 900 efficiency units

Standard Profile (Balanced):  
- Gap_Threshold ≥ 15%
- Local_Performance ≤ 400 efficiency units
- Target_Performance > 800 efficiency units

Lenient Profile (Aggressive):
- Gap_Threshold ≥ 10%  
- Local_Performance ≤ 350 efficiency units
- Target_Performance > 700 efficiency units
```

#### **Opportunity Detection:**
```
Overcapacity_Opportunity = TRUE if:
- Performance_Gap(i,s) ≥ Gap_Threshold AND
- Local_Performance(i,s) ≤ Local_Threshold AND  
- Cluster_Performance(C,s) > Target_Threshold AND
- Cluster_Size(C) ≥ 3
```

#### **Real Example:**
```
SPU in Standard Profile:
- Local efficiency: 300 units/space
- Cluster 75th percentile: 850 units/space  
- Performance gap: (850-300)/300 = 183% > 15% ✓
- Local: 300 ≤ 400 ✓
- Target: 850 > 800 ✓
→ REALLOCATION OPPORTUNITY
```

---

### **📈 Rule 11: Missed Sales Opportunities**
**Mathematical Foundation: Volume-Based Peer Performance Analysis**

#### **Core Algorithm:**
```
For each SPU s in store i, cluster C:
1. Store_Volume(i,s) = SPU_Sales(i,s)
2. Peer_Success_Rate(C,s) = |{stores ∈ C : SPU_Sales(store,s) ≥ High_Sales_Target}| / |C|
3. Cluster_Average(C,s) = Σ(SPU_Sales(store,s)) / |C|

4. Missed_Opportunity = TRUE if:
   - Store_Volume(i,s) < Low_Volume_Threshold AND
   - Peer_Success_Rate(C,s) ≥ Cluster_Success_Threshold AND
   - |C| ≥ Min_Cluster_Peers
```

#### **Threshold Parameters:**
```
Low_Volume_Threshold = $50
High_Sales_Target = $200  
Cluster_Success_Threshold = 60%
Min_Cluster_Peers = 3
Cluster_Underperformance_Margin = $100
```

#### **Supplementary Measures:**
```
1. Cluster_Relative_Underperformance = TRUE if:
   Store_Volume(i,s) < (Cluster_Average(C,s) - Underperformance_Margin)

2. Cluster_Misjudgment = TRUE if:
   (Cluster_Average(C,s) / Global_Average(s)) < (1 - Misjudgment_Threshold)
   OR StdDev(C,s) / Mean(C,s) > Variability_Threshold
```

#### **Recommendation Logic:**
```
Recommendation = {
  "Increase facing count"           if Gap ≤ 2×High_Sales_Target
  "Increase facing + Promotion"     if Gap > 2×High_Sales_Target
}
where Gap = High_Sales_Target - Store_Volume(i,s)
```

#### **Real Example:**
```
SPU 休闲圆领T恤 in store:
- Store sales: $45 < $50 ✓ (underperforming)
- Cluster peers with >$200: 15/20 = 75% ≥ 60% ✓ (proven market)
- Opportunity gap: $200 - $45 = $155
- Recommendation: "Increase facing count" (Gap ≤ $400)
```

---

### **🏆 Rule 12: Sales Performance Analysis**
**Mathematical Foundation: Opportunity Gap Z-Score Analysis**

#### **Core Algorithm:**
```
For each SPU s in store i, cluster C:
1. Cluster_Benchmark(C,s) = Percentile_70(SPU_Sales(stores ∈ C, s))
2. Opportunity_Gap(i,s) = max(0, Cluster_Benchmark(C,s) - SPU_Sales(i,s))

3. Cluster_Gap_Mean(C,s) = Σ(Opportunity_Gap(store,s)) / |C|
4. Cluster_Gap_StdDev(C,s) = √(Σ(Gap - Mean)² / (|C|-1))

5. Z_Score(i,s) = (Opportunity_Gap(i,s) - Cluster_Gap_Mean(C,s)) / Cluster_Gap_StdDev(C,s)
```

#### **Performance Classification:**
```
Performance_Level(i,s) = {
  "Top Performer"      if Z_Score(i,s) < -0.8
  "Performing Well"    if -0.8 ≤ Z_Score(i,s) ≤ 0
  "Some Opportunity"   if 0 < Z_Score(i,s) ≤ 0.8  
  "Good Opportunity"   if 0.8 < Z_Score(i,s) ≤ 2.0
  "Major Opportunity"  if Z_Score(i,s) > 2.0
}
```

#### **Store-Level Aggregation:**
```
Store_Average_Z_Score(i) = Σ(Z_Score(i,s)) / |SPUs(i)|

Store_Performance_Level(i) = {
  "Top Performer"      if Avg_Z < -0.5
  "Performing Well"    if -0.5 ≤ Avg_Z ≤ 0.2
  "Some Opportunity"   if 0.2 < Avg_Z ≤ 0.8
  "Good Opportunity"   if 0.8 < Avg_Z ≤ 1.5  
  "Major Opportunity"  if Avg_Z > 1.5
}
```

#### **Real Example:**
```
SPU performance calculation:
- Store sales: $150
- Cluster 70th percentile: $300
- Opportunity gap: max(0, 300-150) = $150
- Cluster gap mean: $80
- Cluster gap std dev: $45
- Z-score: (150-80)/45 = 1.56 → "Good Opportunity"
```

---

## **📊 Mathematical Summary**

| Rule | Core Equation | Key Threshold | Statistical Method |
|------|---------------|---------------|-------------------|
| **7** | `Penetration = Selling_Stores/Total_Stores` | ≥90% adoption | Frequency analysis |
| **8** | `Z = (Allocation - Mean)/StdDev` | \|Z\| > 4.0 | Z-score distribution |
| **10** | `Gap = (Target - Local)/Local` | ≥15% gap | Performance gap analysis |
| **11** | `Success_Rate = High_Performers/Total` | ≥60% success | Volume-based comparison |
| **12** | `Z = (Gap - Gap_Mean)/Gap_StdDev` | 70th percentile benchmark | Opportunity gap Z-score |

Each rule uses **rigorous statistical methods** to ensure **mathematically sound** and **business-actionable** insights!