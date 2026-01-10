# Step 7: Missing Category/SPU Rule - Behavior Analysis

**Date:** 2025-11-03  
**Status:** ✅ COMPLETE  
**Original File:** `src/step7_missing_category_rule.py` (1,625 LOC)  
**Analysis Method:** Complete code review organized by 4-phase pattern

---

## 📋 Executive Summary

**Step Objective:** Identify stores missing categories/SPUs that are well-selling in their cluster peers, with quantity recommendations and Fast Fish sell-through validation.

**Key Features:**
- Missing category/SPU identification based on cluster peer analysis
- Real quantity recommendations using actual sales data
- Fast Fish sell-through validation (only profitable recommendations)
- ROI calculation with margin rates
- Seasonal data blending support
- Dual analysis modes: subcategory-level and SPU-level

**Inputs:**
- Clustering results (from Step 6)
- Sales data (category or SPU level)
- Quantity data (store sales with units)
- Margin rates (for ROI calculation)

**Outputs:**
- Store-level results CSV (aggregated metrics)
- Detailed opportunities CSV (individual recommendations)
- Markdown summary report (sell-through analysis)

---

## 🔄 Behavior Analysis by Phase

### SETUP Phase Behaviors

#### 1.1 Configuration Loading
**Lines:** 133-262

**Behavior:**
- Load analysis level configuration (subcategory vs SPU)
- Set thresholds based on analysis level:
  - Subcategory: 70% adoption, $100 min sales, $50 min opportunity
  - SPU: 80% adoption, $1,500 min sales, $500 min opportunity
- Configure seasonal blending parameters
- Set ROI calculation parameters
- Load environment variables for fine-tuning

**Data Structures:**
```python
ANALYSIS_CONFIGS = {
    "subcategory": {
        "cluster_file": "output/clustering_results_subcategory.csv",
        "feature_column": "sub_cate_name",
        "sales_column": "sal_amt",
        "output_prefix": "rule7_missing_subcategory"
    },
    "spu": {
        "cluster_file": "output/clustering_results_spu.csv",
        "feature_column": "spu_code",
        "sales_column": "spu_sales_amt",
        "output_prefix": "rule7_missing_spu"
    }
}
```

#### 1.2 Data Loading - Clustering Results
**Lines:** 395-428

**Behavior:**
- Load clustering results from multiple candidate paths
- Fallback chain: period-specific → generic → enhanced → default
- Normalize cluster column names (Cluster → cluster_id)
- Validate cluster_id column exists
- Handle missing cluster assignments (set to NA)

**Validation:**
- File existence checks
- Column name standardization
- Cluster ID validation

#### 1.3 Data Loading - Sales Data
**Lines:** 430-540

**Behavior:**
- Load current period sales data (SPU or category level)
- **Optional:** Seasonal blending with configurable weights
  - Recent data weight (default: 40%)
  - Seasonal data weight (default: 60%)
  - Multi-year seasonal support
- **Optional:** Recent period averaging (multiple half-months)
- Standardize store code column names

**Seasonal Blending Logic:**
```python
if USE_BLENDED_SEASONAL:
    # Load current period sales
    current_sales * RECENT_WEIGHT (0.4)
    
    # Load seasonal period(s) sales
    seasonal_sales * SEASONAL_WEIGHT (0.6)
    
    # Aggregate by (store, feature)
    blended_sales = SUM(weighted sales)
```

#### 1.4 Data Loading - Quantity Data
**Lines:** 274-385

**Behavior:**
- Load store-level quantity data with unit prices
- Calculate average unit price per store
- **Backfill logic:** If current period has no prices:
  - Look back up to 6 half-months
  - Calculate median price from historical data
  - Fill missing prices with historical medians
- Strict mode: Fail if no real prices available (no synthetic fallbacks)

**Price Calculation:**
```python
avg_unit_price = total_amt / total_qty (where total_qty > 0)
```

**Backfill Strategy:**
1. Try store average from current period
2. Try store average from sales data
3. Try cluster median from quantity data
4. Fail if still invalid (strict mode)

#### 1.5 Data Loading - Margin Rates
**Lines:** 737-772

**Behavior:**
- Load period-aware margin rates (SPU or category level)
- Build two-level lookup maps:
  - (store, feature) → margin rate (most specific)
  - store → margin rate (fallback)
- Clamp margin rates to realistic range (0-95%)
- Default margin rate: 45%

**Resolution Priority:**
1. (store, feature) pair
2. (store, parent_category) pair (for subcategories)
3. Store average
4. Default (45%)

#### 1.6 Sell-Through Validator Initialization
**Lines:** 706-714

**Behavior:**
- Load historical data for validation
- Initialize SellThroughValidator instance
- **Strict mode:** Fail if validator unavailable
- Validator used to predict sell-through rates

---

### APPLY Phase Behaviors

#### 2.1 Identify Well-Selling Features
**Lines:** 631-688

**Behavior:**
- Merge sales data with cluster assignments
- Group by (cluster_id, feature) to calculate:
  - Number of stores selling (nunique)
  - Total cluster sales (sum)
- Calculate percentage of stores selling in cluster
- **Filter criteria:**
  - pct_stores_selling ≥ MIN_CLUSTER_STORES_SELLING (70% or 80%)
  - total_cluster_sales ≥ MIN_CLUSTER_SALES_THRESHOLD ($100 or $1,500)

**Output:** DataFrame of well-selling features per cluster

**Example:**
```
cluster_id | feature      | stores_selling | total_sales | pct_selling
1          | 直筒裤        | 45             | 125,000     | 0.90
1          | 锥形裤        | 38             | 98,000      | 0.76
```

#### 2.2 Identify Missing Opportunities
**Lines:** 689-1132 (443 lines - largest function!)

**Sub-behaviors:**

**2.2.1 Find Missing Stores**
- For each well-selling feature in a cluster:
  - Get all stores in that cluster
  - Get stores currently selling that feature
  - Find missing stores = cluster stores - selling stores

**2.2.2 Calculate Expected Sales**
- Use robust peer median (not mean to avoid outliers)
- Trim extremes (10th-90th percentile)
- Cap at P80 for realism
- Apply minimum opportunity value threshold
- SPU-specific cap: $2,000 per store

**2.2.3 Calculate Unit Price**
**Lines:** 842-886

Priority chain:
1. Store average from quantity_df (real store totals)
2. Store average from sales_df (amount/quantity)
3. Cluster median from quantity_df
4. **Fail if invalid** (strict mode - no synthetic prices)

**2.2.4 Calculate Quantity Recommendation**
**Lines:** 889-890

```python
expected_quantity = (avg_sales * SCALING_FACTOR) / unit_price
expected_quantity_int = ceil(expected_quantity)  # Round up to integer
```

**2.2.5 Sell-Through Validation**
**Lines:** 892-956

**Prediction Methods:**
1. **Adoption-based prediction:**
   - Logistic curve: 10% + 60% * sigmoid(adoption_rate)
   - Range: 10-70% sell-through

2. **Blended prediction** (if ROI enabled):
   - 35% weight: Adoption estimate
   - 30% weight: Cluster P50 sell-through
   - 25% weight: Store category baseline
   - 10% weight: Seasonal adjustment
   - Shrink weights when few comparables

**Approval Logic:**
```python
should_approve = (
    validator_ok AND
    stores_selling ≥ MIN_STORES_SELLING (5) AND
    pct_stores_selling ≥ MIN_ADOPTION (0.25) AND
    predicted_sellthrough ≥ MIN_PREDICTED_ST (30%)
)
```

**2.2.6 ROI Calculation** (Optional)
**Lines:** 976-1011

**If USE_ROI enabled:**
```python
unit_cost = unit_price * (1 - margin_rate)
expected_units = ceil(median_sales / unit_price)
margin_per_unit = unit_price - unit_cost
margin_uplift = margin_per_unit * expected_units
investment_required = expected_units * unit_cost
roi = margin_uplift / investment_required

# Filter by ROI thresholds:
roi ≥ ROI_MIN_THRESHOLD (0.3 = 30%)
margin_uplift ≥ MIN_MARGIN_UPLIFT ($100)
n_comparables ≥ MIN_COMPARABLES (10)
```

**2.2.7 Create Opportunity Record**
**Lines:** 1024-1054

**Each approved opportunity includes:**
- Store and cluster identification
- Feature name (category or SPU)
- Opportunity metrics (sales, adoption %)
- **Quantity metrics:**
  - current_quantity: 0 (missing)
  - recommended_quantity_change: integer units
  - unit_price: real price from data
  - investment_required: cost-based (units * unit_cost)
  - retail_value: units * unit_price
- **Sell-through metrics:**
  - current_sell_through_rate: 0% (missing)
  - predicted_sell_through_rate: predicted %
  - sell_through_improvement: predicted - 0
  - fast_fish_compliant: boolean
  - business_rationale: text explanation
- **ROI metrics** (if enabled):
  - roi: ratio
  - margin_uplift: dollars
  - n_comparables: count
  - margin_rate_used: rate

**2.2.8 Enrich with Category Names**
**Lines:** 1059-1088

- Map sub_cate_name from sales data (for SPU mode)
- Map cate_name from sales data (if available)
- Left join to preserve all opportunities

#### 2.3 Aggregate to Store Results
**Lines:** 1134-1251

**Behavior:**
- Group opportunities by store
- Aggregate metrics:
  - Count of missing features
  - Sum of opportunity values
  - Sum of quantities needed
  - Sum of investment required
  - Sum of retail values
  - Average sell-through improvement
  - Average predicted sell-through
  - Count of Fast Fish approved
- Create rule flag (1 if any opportunities, 0 otherwise)
- Add metadata columns
- Fill NA with 0 for stores with no opportunities

**Output Columns:**
- str_code, cluster_id
- missing_categories_count OR missing_spus_count
- total_opportunity_value
- total_quantity_needed
- total_investment_required
- total_retail_value
- avg_sellthrough_improvement
- avg_predicted_sellthrough
- fastfish_approved_count
- rule7_missing_category OR rule7_missing_spu (flag)
- rule7_description
- rule7_threshold
- rule7_analysis_level
- rule7_sellthrough_validation
- rule7_fastfish_compliant

---

### VALIDATE Phase Behaviors

#### 3.1 Preflight Validation
**Lines:** 1253-1304

**Behavior:**
- Check output files exist
- Check output files are non-empty
- Validate required columns present in results:
  - str_code, cluster_id
  - total_quantity_needed
  - total_investment_required
  - total_retail_value
- Validate required columns present in opportunities:
  - str_code, cluster_id, spu_code
  - recommended_quantity_change
  - unit_price, investment_required, retail_value
  - margin_rate_used
- Check filenames include period label
- **Raise RuntimeError** if validation fails

**Note:** This is currently in PERSIST phase but should move to VALIDATE phase in refactoring.

---

### PERSIST Phase Behaviors

#### 4.1 Save Store Results
**Lines:** 1306-1350

**Behavior:**
- Create timestamped filename
- Create period-specific symlink
- Create generic symlink (backward compatibility)
- Save main results CSV
- **Register in manifest:**
  - Key: "store_results"
  - Key: "store_results_{period_label}"
  - Metadata: rows, columns, analysis_level, period_label

**Output Pattern:**
```
output/rule7_missing_{analysis_level}_sellthrough_results_20251103_094500.csv
output/rule7_missing_{analysis_level}_sellthrough_results_202510A.csv (symlink)
output/rule7_missing_{analysis_level}_sellthrough_results.csv (symlink)
```

#### 4.2 Save Detailed Opportunities
**Lines:** 1353-1390

**Behavior:**
- Only if opportunities exist (len > 0)
- Create timestamped filename
- Create period-specific symlink
- Create generic symlink
- Save opportunities CSV
- **Register in manifest:**
  - Key: "opportunities"
  - Key: "opportunities_{period_label}"
  - Metadata: rows, columns, analysis_level, period_label

#### 4.3 Generate Summary Report
**Lines:** 1392-1511

**Behavior:**
- Create markdown summary report
- Include:
  - Analysis metadata (date, level, Fast Fish status)
  - Seasonal blending provenance
  - Executive summary (opportunities, stores, investment)
  - Sell-through distribution (>5pp, >3pp, >1pp improvements)
  - Quantity & price diagnostics
  - Fast Fish compliance confirmation
  - Top 10 opportunities by sell-through improvement
- **Register in manifest:**
  - Key: "summary_report_md"
  - Key: "summary_report_md_{period_label}"

**Report Sections:**
1. Header with metadata
2. Seasonal blending info
3. Executive summary
4. Sell-through distribution
5. Quantity & price diagnostics
6. Fast Fish compliance
7. Top opportunities table

#### 4.4 Backward Compatibility
**Lines:** 1421-1435

**Behavior:**
- Check if backward-compatible file exists
- Register in manifest if found
- Maintains compatibility with legacy consumers

---

## 🔗 Downstream Dependencies

### Step 13: Consolidate SPU Rules

**Required Outputs:**
- `output/rule7_missing_{analysis_level}_sellthrough_results.csv`
- `output/rule7_missing_{analysis_level}_sellthrough_opportunities.csv`

**Required Columns (for consolidation):**
- str_code (store identifier)
- cluster_id (cluster assignment)
- spu_code (product identifier)
- sub_cate_name (subcategory name)
- recommended_quantity_change (quantity delta)
- unit_price (real unit price)
- investment_required (cost-based investment)
- business_rationale (explanation text)

**Column Naming:**
- Must use `cluster_id` (not `Cluster`)
- Must use `sub_cate_name` (standardized)
- Must include all fields for consolidation

---

## 🎯 Key Business Rules

### Rule 1: Cluster Peer Analysis
**Logic:** A feature is "well-selling" if:
- ≥70% (subcategory) or ≥80% (SPU) of cluster stores sell it
- Total cluster sales ≥ $100 (subcategory) or ≥$1,500 (SPU)

### Rule 2: Missing Opportunity
**Logic:** A store has a missing opportunity if:
- Store is in a cluster where feature is well-selling
- Store does NOT currently sell that feature
- Expected sales ≥ minimum opportunity value

### Rule 3: Quantity Calculation
**Logic:**
```
expected_quantity = (peer_median_sales * scaling_factor) / unit_price
recommended_quantity = ceil(expected_quantity)  # Round up
```

### Rule 4: Fast Fish Validation
**Logic:** Only recommend if:
- Sell-through validator approves
- ≥5 stores in cluster sell it
- ≥25% cluster adoption
- ≥30% predicted sell-through rate

### Rule 5: ROI Filtering (Optional)
**Logic:** If enabled, only recommend if:
- ROI ≥ 30%
- Margin uplift ≥ $100
- ≥10 comparable stores

### Rule 6: Seasonal Blending (Optional)
**Logic:** If enabled:
- Blend recent data (40%) with seasonal data (60%)
- Support multi-year seasonal patterns
- Aggregate by (store, feature) after weighting

### Rule 7: Price Resolution
**Priority:**
1. Store average from quantity data
2. Store average from sales data
3. Cluster median from quantity data
4. **Fail** (no synthetic prices)

---

## 📊 Data Flow Summary

```
INPUT:
├── Clustering Results (Step 6)
├── Sales Data (API)
├── Quantity Data (API)
└── Margin Rates (Config)

PROCESSING:
├── Identify well-selling features per cluster
├── Find missing opportunities
├── Calculate quantities using real prices
├── Validate with sell-through predictor
├── Filter by ROI (optional)
└── Aggregate to store level

OUTPUT:
├── Store Results CSV (aggregated)
├── Opportunities CSV (detailed)
└── Summary Report MD (analysis)
```

---

## 🚨 Critical Behaviors to Preserve

### 1. Strict Real Data Mode
- **NO synthetic prices** - fail if unavailable
- **NO synthetic quantities** - use real sales data
- **NO assumptions** - backfill from historical only

### 2. Fast Fish Compliance
- **Only profitable recommendations** - sell-through validated
- **Approval gates** - multiple criteria must pass
- **Transparency** - business rationale for each

### 3. Dual Analysis Support
- **Subcategory mode** - broader categories
- **SPU mode** - granular products
- **Different thresholds** - appropriate for each level

### 4. Seasonal Intelligence
- **Blended approach** - recent + seasonal data
- **Multi-year support** - multiple seasonal periods
- **Configurable weights** - flexible blending

### 5. Investment Planning
- **Real unit prices** - from actual sales
- **Cost-based investment** - units * unit_cost
- **ROI calculation** - margin uplift / investment

### 6. Downstream Compatibility
- **Standardized columns** - cluster_id, sub_cate_name
- **Complete metadata** - all fields for Step 13
- **Manifest registration** - pipeline tracking

---

## 📝 Notes for Refactoring

### Complexity Hotspots:
1. **Lines 689-1132:** 443-line function needs extraction into components
2. **Lines 1-55:** Helper functions should be class methods or utilities
3. **Lines 133-262:** Global config should be dataclass

### Modularization Opportunities:
1. **DataLoader:** Lines 263-585 (data loading logic)
2. **ClusterAnalyzer:** Lines 631-688 (well-selling identification)
3. **OpportunityIdentifier:** Lines 689-890 (missing opportunity detection)
4. **SellThroughValidator:** Lines 892-956 (validation logic)
5. **ROICalculator:** Lines 729-785, 976-1011 (ROI calculation)
6. **ResultsAggregator:** Lines 1134-1251 (aggregation logic)
7. **ReportGenerator:** Lines 1446-1511 (report generation)

### Testing Priorities:
1. **Happy path:** Normal operation with valid data
2. **Seasonal blending:** Weighted data combination
3. **Price backfill:** Historical price fallback
4. **Sell-through validation:** Approval/rejection logic
5. **ROI filtering:** Threshold enforcement
6. **Edge cases:** Empty data, missing prices, no opportunities

---

**Analysis Complete:** ✅  
**Next Step:** Check downstream dependencies (Step 13)  
**Date:** 2025-11-03
