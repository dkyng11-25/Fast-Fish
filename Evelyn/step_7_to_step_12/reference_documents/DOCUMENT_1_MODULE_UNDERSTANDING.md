# Step 7-13 Module Understanding & Fast Fish Business Requirements

> **Document Type:** Technical Analysis & Business Requirements Mapping  
> **Audience:** Data Scientists, Business Analysts, Project Owners  
> **Purpose:** Understand what each module does and identify Fast Fish's core business needs  
> **Last Updated:** January 2026

---

## Executive Summary: The Big Picture

### From Clustering to Demand Forecasting

Steps 1-6 clustered **2,200+ Fast Fish stores** into **30 similar groups** based on their product mix patterns and store characteristics. Now, Steps 7-13 answer the critical business question:

> **"For each store, what products should we ADD, REMOVE, or REBALANCE to maximize sales?"**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DEMAND FORECASTING PIPELINE OVERVIEW                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STEP 1-6: CLUSTERING                    STEP 7-13: BUSINESS RULES          │
│  ─────────────────────                   ──────────────────────────         │
│  • Download API data                     • Step 7: Missing Products (ADD)   │
│  • Extract coordinates                   • Step 8: Imbalanced Mix (REBALANCE)│
│  • Prepare sales matrix                  • Step 9: Below Minimum (BOOST)    │
│  • Download weather                      • Step 10: Overcapacity (REDUCE)   │
│  • Calculate temperature                 • Step 11: Missed Sales (CAPTURE)  │
│  • Cluster stores (30 groups)            • Step 12: Performance Gap (CLOSE) │
│                                          • Step 13: Consolidate All Rules   │
│                                                                             │
│  OUTPUT: Store clusters                  OUTPUT: Actionable recommendations │
│  (which stores are similar)              (what to do for each store)        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fast Fish's Core Business Need

Fast Fish wants to **optimize inventory allocation** across 2,200+ stores by:
1. **Identifying gaps** - Products that should be in a store but aren't
2. **Fixing imbalances** - Products that are over/under-allocated
3. **Capturing opportunities** - Sales potential being missed
4. **Reducing waste** - Products that aren't selling well

---

## Step 7: Missing Category/SPU Rule

### What It Does (Plain English)

Step 7 finds products that are **selling well in peer stores** (same cluster) but are **missing from a specific store**. It's like noticing that all similar coffee shops sell croissants, but one shop doesn't—that's a missed opportunity.

### Business Logic Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STEP 7: MISSING PRODUCT DETECTION                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT:                                                                     │
│  ├── Clustering results (which stores are in which cluster)                 │
│  ├── SPU/Category sales data (what each store sells)                        │
│  └── Quantity data (how many units, at what price)                          │
│                                                                             │
│  PROCESS:                                                                   │
│  1. For each cluster, find "well-selling" products:                         │
│     • ≥80% of stores in cluster sell this product                           │
│     • Total cluster sales ≥ 1,500 RMB                                       │
│                                                                             │
│  2. For each store, find which well-selling products are MISSING            │
│                                                                             │
│  3. Calculate recommended quantity:                                         │
│     • Based on cluster average sales                                        │
│     • Validated against sell-through rate (will it actually sell?)          │
│                                                                             │
│  OUTPUT:                                                                    │
│  ├── rule7_missing_spu_results.csv                                          │
│  ├── rule7_missing_spu_opportunities.csv                                    │
│  └── rule7_missing_spu_summary.md                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Output Columns

| Column | Description | Example |
|--------|-------------|---------|
| `str_code` | Store identifier | "S001234" |
| `spu_code` | Missing product code | "SPU_JACKET_001" |
| `cluster_id` | Store's cluster | 15 |
| `pct_stores_selling` | % of cluster stores selling this | 85% |
| `recommended_quantity` | Units to stock | 5 units |
| `expected_investment` | Cost to stock | ¥500 |
| `predicted_sellthrough` | Expected sell rate | 72% |
| `sell_through_validated` | Passes profitability check | True |

### Fast Fish Requirement Identified

> **"Tell me which products I should ADD to each store, with specific quantities, and only if they'll actually sell."**

---

## Step 8: Imbalanced Allocation Rule

### What It Does (Plain English)

Step 8 finds stores where the product mix is **statistically unusual** compared to peer stores. Using Z-Score analysis, it identifies products that are significantly over or under-represented and recommends **rebalancing** (move units from overstocked products to understocked ones).

### Business Logic Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      STEP 8: IMBALANCED ALLOCATION DETECTION                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT:                                                                     │
│  ├── Clustering results                                                     │
│  ├── Store-level allocation data (what % of inventory is each product)     │
│  └── Quantity data                                                          │
│                                                                             │
│  PROCESS:                                                                   │
│  1. Calculate each store's allocation % for each product                    │
│                                                                             │
│  2. Calculate cluster average and standard deviation                        │
│                                                                             │
│  3. Compute Z-Score for each store-product combination:                     │
│     Z = (store_allocation - cluster_mean) / cluster_std                     │
│                                                                             │
│  4. Flag imbalances where |Z-Score| > 3.0 (SPU level)                       │
│                                                                             │
│  5. Recommend rebalancing:                                                  │
│     • DECREASE products with high positive Z-Score (overstocked)            │
│     • INCREASE products with high negative Z-Score (understocked)           │
│                                                                             │
│  OUTPUT:                                                                    │
│  ├── rule8_imbalanced_spu_results.csv                                       │
│  └── Summary statistics                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Output Columns

| Column | Description | Example |
|--------|-------------|---------|
| `str_code` | Store identifier | "S001234" |
| `spu_code` | Product code | "SPU_PANTS_002" |
| `z_score` | Statistical deviation | +3.5 (overstocked) |
| `current_allocation` | Current % of inventory | 15% |
| `cluster_avg_allocation` | Peer average | 8% |
| `recommended_change` | Direction | "DECREASE" |
| `quantity_change` | Units to move | -10 units |

### Fast Fish Requirement Identified

> **"Tell me which products are over/under-stocked compared to similar stores, and how to rebalance without additional investment."**

---

## Step 9: Below Minimum Rule

### What It Does (Plain English)

Step 9 finds products that are **barely stocked** (below a minimum threshold) and recommends **boosting** their allocation. The key insight: if a product exists in a store but at very low levels, it might be underperforming simply due to insufficient visibility/availability.

### Business Logic Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       STEP 9: BELOW MINIMUM DETECTION                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT:                                                                     │
│  ├── Clustering results                                                     │
│  ├── Store-product allocation data                                          │
│  └── Quantity data                                                          │
│                                                                             │
│  PROCESS:                                                                   │
│  1. Identify products with allocation < 3% (MINIMUM_STYLE_THRESHOLD)        │
│                                                                             │
│  2. Compare to cluster peers:                                               │
│     • If peers have higher allocation, this is a "below minimum" case       │
│                                                                             │
│  3. CRITICAL BUSINESS RULE:                                                 │
│     • Below minimum should INCREASE allocation (never decrease!)            │
│     • Minimum boost: 0.5 units                                              │
│                                                                             │
│  OUTPUT:                                                                    │
│  ├── rule9_below_minimum_spu_results.csv                                    │
│  └── Boost recommendations                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Output Columns

| Column | Description | Example |
|--------|-------------|---------|
| `str_code` | Store identifier | "S001234" |
| `spu_code` | Product code | "SPU_SHIRT_003" |
| `current_allocation` | Current % | 2% |
| `cluster_avg_allocation` | Peer average | 8% |
| `recommended_quantity_change` | Units to ADD | +3 units |
| `action` | Always "INCREASE" | "INCREASE" |

### Fast Fish Requirement Identified

> **"Tell me which products are barely stocked and should be boosted to match peer store levels."**

---

## Step 10: Overcapacity Rule (SPU Assortment Optimization)

### What It Does (Plain English)

Step 10 is the **opposite of Step 7**. It finds stores that have **too many products** in a category compared to the optimal target. If a store has 50 different jacket styles but should only have 30, Step 10 recommends which 20 to reduce.

### Business Logic Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      STEP 10: OVERCAPACITY DETECTION                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT:                                                                     │
│  ├── Clustering results                                                     │
│  ├── Store configuration (current SPU count per category)                   │
│  ├── Target SPU counts (optimal assortment size)                            │
│  └── Quantity data                                                          │
│                                                                             │
│  PROCESS:                                                                   │
│  1. Compare current SPU count vs target SPU count per category              │
│                                                                             │
│  2. If current > target → OVERCAPACITY                                      │
│     • Calculate excess: current - target                                    │
│                                                                             │
│  3. Prioritize which SPUs to reduce:                                        │
│     • Lowest sell-through rate first                                        │
│     • Lowest sales volume first                                             │
│                                                                             │
│  4. Calculate quantity reduction per SPU                                    │
│                                                                             │
│  OUTPUT:                                                                    │
│  ├── rule10_overcapacity_spu_results.csv                                    │
│  └── Reduction recommendations with sell-through validation                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Output Columns

| Column | Description | Example |
|--------|-------------|---------|
| `str_code` | Store identifier | "S001234" |
| `sub_cate_name` | Category | "Jackets" |
| `current_spu_count` | Current # of styles | 50 |
| `target_spu_count` | Optimal # of styles | 30 |
| `excess_spu_count` | Overcapacity | 20 |
| `spu_code` | SPU to reduce | "SPU_JACKET_045" |
| `recommended_quantity_change` | Units to REMOVE | -5 units |

### Fast Fish Requirement Identified

> **"Tell me which stores have too many product styles and which specific styles should be reduced."**

---

## Step 11: Missed Sales Opportunity Rule

### What It Does (Plain English)

Step 11 compares each store's performance against the **top performers in its cluster** (top 5%). If Store A sells 100 units of jackets but the top stores in its cluster sell 200 units, that's a **missed sales opportunity** of 100 units.

### Business Logic Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STEP 11: MISSED SALES OPPORTUNITY                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT:                                                                     │
│  ├── Clustering results                                                     │
│  ├── SPU sales data per store                                               │
│  └── Quantity data                                                          │
│                                                                             │
│  PROCESS:                                                                   │
│  1. For each cluster-SPU combination:                                       │
│     • Calculate top 5% performer threshold (95th percentile)                │
│                                                                             │
│  2. For each store:                                                         │
│     • Compare store sales vs top performer threshold                        │
│     • Gap = top_performer_sales - store_sales                               │
│                                                                             │
│  3. Filter for actionable opportunities:                                    │
│     • Minimum sales gap: ¥100                                               │
│     • Minimum quantity gap: 2 units                                         │
│     • Minimum adoption rate: 70% of cluster stores sell this SPU            │
│                                                                             │
│  OUTPUT:                                                                    │
│  ├── rule11_missed_sales_spu_results.csv                                    │
│  └── Opportunity scores and quantity recommendations                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Output Columns

| Column | Description | Example |
|--------|-------------|---------|
| `str_code` | Store identifier | "S001234" |
| `spu_code` | Product code | "SPU_DRESS_007" |
| `store_sales` | Current sales | ¥5,000 |
| `top_performer_sales` | Top 5% threshold | ¥12,000 |
| `sales_gap` | Missed opportunity | ¥7,000 |
| `quantity_gap` | Units to add | +15 units |
| `opportunity_score` | Priority ranking | 0.85 |

### Fast Fish Requirement Identified

> **"Tell me where each store is underperforming compared to the best stores in its cluster, and how much sales potential is being missed."**

---

## Step 12: Sales Performance Rule

### What It Does (Plain English)

Step 12 is similar to Step 11 but uses **top quartile (25%)** instead of top 5%. It provides a broader view of performance gaps and classifies stores into 5 performance tiers.

### Business Logic Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      STEP 12: SALES PERFORMANCE ANALYSIS                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT:                                                                     │
│  ├── Clustering results                                                     │
│  ├── Category/SPU sales data                                                │
│  └── Quantity data                                                          │
│                                                                             │
│  PROCESS:                                                                   │
│  1. Calculate performance percentiles within each cluster                   │
│                                                                             │
│  2. Classify stores into 5 tiers:                                           │
│     • Tier 1: Top 20% (Excellent)                                           │
│     • Tier 2: 20-40% (Good)                                                 │
│     • Tier 3: 40-60% (Average)                                              │
│     • Tier 4: 60-80% (Below Average)                                        │
│     • Tier 5: Bottom 20% (Needs Improvement)                                │
│                                                                             │
│  3. Calculate gap to top quartile for each store-SPU                        │
│                                                                             │
│  OUTPUT:                                                                    │
│  ├── rule12_sales_performance_spu_results.csv                               │
│  └── Performance tier classifications                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Output Columns

| Column | Description | Example |
|--------|-------------|---------|
| `str_code` | Store identifier | "S001234" |
| `spu_code` | Product code | "SPU_COAT_009" |
| `performance_tier` | Store tier | 4 (Below Average) |
| `store_percentile` | Within cluster | 35th percentile |
| `gap_to_top_quartile` | Sales gap | ¥3,500 |
| `recommended_quantity_increase` | Units to add | +8 units |

### Fast Fish Requirement Identified

> **"Classify each store's performance and tell me how much they need to improve to reach top quartile."**

---

## Step 13: Consolidate All SPU Rules

### What It Does (Plain English)

Step 13 is the **aggregation layer** that combines all recommendations from Steps 7-12 into a single, actionable output. It handles:
- Deduplication (same SPU might appear in multiple rules)
- Conflict resolution (one rule says ADD, another says REMOVE)
- Data quality correction
- Final prioritization

### Business Logic Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STEP 13: CONSOLIDATE ALL RULES                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT:                                                                     │
│  ├── Rule 7 results (Missing products → ADD)                                │
│  ├── Rule 8 results (Imbalanced → REBALANCE)                                │
│  ├── Rule 9 results (Below minimum → BOOST)                                 │
│  ├── Rule 10 results (Overcapacity → REDUCE)                                │
│  ├── Rule 11 results (Missed sales → INCREASE)                              │
│  └── Rule 12 results (Performance gap → INCREASE)                           │
│                                                                             │
│  PROCESS:                                                                   │
│  1. Load all rule outputs                                                   │
│                                                                             │
│  2. Standardize columns across rules                                        │
│                                                                             │
│  3. Handle conflicts:                                                       │
│     • If Rule 7 says ADD and Rule 10 says REDUCE → Use sell-through to decide│
│     • Prioritize rules with higher confidence                               │
│                                                                             │
│  4. Data quality corrections:                                               │
│     • Fix missing cluster assignments                                       │
│     • Remove duplicate records                                              │
│     • Validate mathematical consistency                                     │
│                                                                             │
│  5. Aggregate to store level and cluster level                              │
│                                                                             │
│  OUTPUT:                                                                    │
│  ├── consolidated_spu_rule_results.csv (all recommendations)                │
│  ├── corrected_detailed_spu_recommendations_*.csv                           │
│  ├── corrected_store_level_aggregation_*.csv                                │
│  └── corrected_cluster_subcategory_aggregation_*.csv                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Output Columns

| Column | Description | Example |
|--------|-------------|---------|
| `str_code` | Store identifier | "S001234" |
| `spu_code` | Product code | "SPU_SHIRT_010" |
| `rule_source` | Which rule generated this | "Rule 7" |
| `action` | Final recommendation | "ADD" |
| `quantity_change` | Units to change | +5 |
| `investment_required` | Cost | ¥750 |
| `expected_return` | Projected sales | ¥1,200 |
| `priority_score` | Ranking | 0.92 |

### Fast Fish Requirement Identified

> **"Give me ONE consolidated list of all actions for each store, with conflicts resolved and priorities assigned."**

---

## Summary: How Steps 7-13 Connect to Demand Forecasting

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DEMAND FORECASTING DECISION FRAMEWORK                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  QUESTION                          ANSWERED BY                              │
│  ────────                          ───────────                              │
│  "What products should we ADD?"    Step 7 (Missing) + Step 11 (Missed Sales)│
│                                                                             │
│  "What products should we REDUCE?" Step 10 (Overcapacity)                   │
│                                                                             │
│  "What products need REBALANCING?" Step 8 (Imbalanced) + Step 9 (Below Min) │
│                                                                             │
│  "How much should we change?"      All steps provide QUANTITY recommendations│
│                                                                             │
│  "Will it actually sell?"          Sell-through validation in all steps     │
│                                                                             │
│  "What's the final action plan?"   Step 13 (Consolidation)                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The Complete Fast Fish Business Need

> **"Based on how similar stores perform, tell me exactly what inventory changes to make at each store—what to add, what to remove, what to rebalance—with specific quantities, expected costs, and confidence that the changes will improve sales."**

---

## Appendix: Input/Output File Reference

### Step 7 Files
| Type | File | Description |
|------|------|-------------|
| Input | `output/clustering_results_spu.csv` | Store cluster assignments |
| Input | `complete_spu_sales_*.csv` | SPU sales data |
| Input | `store_sales_*.csv` | Quantity and price data |
| Output | `rule7_missing_spu_results.csv` | Missing product recommendations |
| Output | `rule7_missing_spu_opportunities.csv` | Detailed opportunities |

### Step 8 Files
| Type | File | Description |
|------|------|-------------|
| Input | `output/clustering_results_spu.csv` | Store cluster assignments |
| Input | `store_config_*.csv` | Store allocation data |
| Output | `rule8_imbalanced_spu_results.csv` | Rebalancing recommendations |

### Step 9 Files
| Type | File | Description |
|------|------|-------------|
| Input | `output/clustering_results_spu.csv` | Store cluster assignments |
| Input | `complete_spu_sales_*.csv` | SPU sales data |
| Output | `rule9_below_minimum_spu_results.csv` | Boost recommendations |

### Step 10 Files
| Type | File | Description |
|------|------|-------------|
| Input | `output/clustering_results_spu.csv` | Store cluster assignments |
| Input | `store_config_*.csv` | Current SPU counts |
| Output | `rule10_overcapacity_spu_results.csv` | Reduction recommendations |

### Step 11 Files
| Type | File | Description |
|------|------|-------------|
| Input | `output/clustering_results_spu.csv` | Store cluster assignments |
| Input | `complete_spu_sales_*.csv` | SPU sales data |
| Output | `rule11_missed_sales_spu_results.csv` | Opportunity recommendations |

### Step 12 Files
| Type | File | Description |
|------|------|-------------|
| Input | `output/clustering_results_spu.csv` | Store cluster assignments |
| Input | `store_config_*.csv` | Store performance data |
| Output | `rule12_sales_performance_spu_results.csv` | Performance gap recommendations |

### Step 13 Files
| Type | File | Description |
|------|------|-------------|
| Input | All Rule 7-12 outputs | Individual rule results |
| Output | `consolidated_spu_rule_results.csv` | Final consolidated recommendations |
| Output | `corrected_detailed_spu_recommendations_*.csv` | Cleaned detailed data |
| Output | `corrected_store_level_aggregation_*.csv` | Store-level summary |

---

*Document prepared for Fast Fish Demand Forecasting Project*  
*For questions, contact the Data Science Team*
