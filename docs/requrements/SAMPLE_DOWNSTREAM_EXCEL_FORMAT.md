# Sample Excel Format for Downstream Teams

## Sheet 1: Store-Level Recommendations
**File:** `ProductMix_Recommendations_2025M08A_YYYYMMDD_HHMMSS.xlsx`

### Required Columns:
| Column | Description | Example |
|--------|-------------|---------|
| Analysis_Year | Year of analysis | 2025 |
| Analysis_Month | Month of analysis | 8 |
| Analysis_Period | Half-month period (A/B) | A |
| Store_Code | Individual store identifier | STR001 |
| Store_Group_ID | Cluster identifier | Cluster_0 |
| Store_Group_Name | Descriptive cluster name | 北京温带集群 |
| SPU_Code | Product SKU identifier | SPU12345 |
| Season | Product season | 夏 |
| Gender | Target gender | 中/男/女 |
| Location | Display location | 前台/后台 |
| Category | Product category | 上装 |
| Subcategory | Product subcategory | T恤 |
| Style_Code | Style classification | CAS001 |
| Price_Band | Price range | ¥50-100 |
| Current_Quantity | Current SPU quantity | 5 |
| Recommended_Quantity | Target SPU quantity | 8 |
| Quantity_Change | Difference (Target - Current) | 3 |
| Investment_Amount | Financial impact (¥) | 150.00 |
| Business_Rule | Applied rule identifier | Rule7_Missing |
| Rationale | Explanation for recommendation | Missing category opportunity... |
| Expected_Benefit | Projected sales increase (¥) | 75.50 |
| Clustering_Date | When clustering was performed | 2025-07-16 10:12:03 |
| Recommendation_Date | When recommendation was generated | 2025-07-23 15:25:51 |
| Valid_Until | Recommendation expiry date | 2025-08-15 23:59:59 |
| Store_Count_In_Group | Number of stores in cluster | 50 |
| Explicit_Store_List | Complete store codes in group | STR001,STR002,STR003... |
| Sell_Through_Rate | Historical sell-through % | 85.2 |
| Temperature_Zone | Climate classification | 温带 |

## Sheet 2: Store Group Metadata
| Store_Group_ID | Store_Group_Name | Store_Count | Store_Codes_List | Temperature_Zone | Clustering_Quality_Score |
|----------------|------------------|-------------|------------------|------------------|-------------------------|
| Cluster_0 | 北京温带集群 | 50 | STR001,STR002,STR003... | 温带 | 0.65 |
| Cluster_1 | 上海亚热带集群 | 50 | STR051,STR052,STR053... | 亚热带 | 0.72 |

## Sheet 3: Analysis Summary
| Metric | Value |
|--------|-------|
| Total Recommendations | 307,896 |
| Unique Stores Affected | 2,247 |
| Unique SPUs Affected | 4,850 |
| Total Investment Required | ¥-30,517,600 |
| Analysis Period | 2025-08-A |
| Clustering Method | Temperature-aware K-means |
| Clustering Quality (Silhouette) | 0.45 |
| Generated Timestamp | 2025-07-23 15:25:51 |

## Usage Instructions for Downstream Teams:

### 1. **Inventory Management Teams:**
- Filter by `Store_Code` for individual store recommendations
- Use `Quantity_Change` for inventory adjustments
- Check `Valid_Until` for recommendation freshness

### 2. **Merchandising Teams:**
- Filter by `Category` and `Subcategory` for product-level insights
- Use `Expected_Benefit` for ROI calculations
- Reference `Business_Rule` for understanding recommendation logic

### 3. **Store Operations:**
- Use `Store_Group_ID` for cluster-level strategies
- Reference `Explicit_Store_List` for peer store comparisons
- Check `Temperature_Zone` for climate-appropriate decisions

### 4. **Finance Teams:**
- Sum `Investment_Amount` for budget planning
- Use `Expected_Benefit` for financial projections
- Filter by `Analysis_Period` for period-specific analysis
