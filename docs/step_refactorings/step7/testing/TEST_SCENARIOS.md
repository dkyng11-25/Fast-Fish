# Step 7: Missing Category/SPU Rule - Test Scenarios

**Date:** 2025-11-03  
**Status:** ✅ COMPLETE  
**Framework:** pytest-bdd (Gherkin format)  
**Coverage:** Happy path, error cases, edge cases, business rules

---

## 📋 Test Scenario Categories

1. **SETUP Phase** - Data loading and initialization
2. **APPLY Phase** - Business logic and calculations
3. **VALIDATE Phase** - Data validation and error handling
4. **PERSIST Phase** - Output generation and manifest registration
5. **Integration** - End-to-end scenarios
6. **Edge Cases** - Boundary conditions and special cases

---

## 🎯 Scenario 1: Happy Path - Complete Missing Category Analysis

**Feature:** Missing Category Rule with Sell-Through Validation

**Scenario:** Successfully identify missing categories with quantity recommendations

```gherkin
Given clustering results with 3 clusters and 50 stores
And sales data with subcategories for current period
And quantity data with real unit prices
And margin rates for ROI calculation
And sell-through validator is available
When executing the missing category rule step
Then well-selling categories are identified per cluster
And missing opportunities are found for stores
And quantities are calculated using real prices
And sell-through validation approves profitable opportunities
And ROI metrics are calculated
And store results are aggregated
And opportunities CSV is created with all required columns
And store results CSV is created
And summary report MD is created
And all outputs are registered in manifest
```

**Expected Results:**
- Opportunities CSV with columns: str_code, cluster_id, spu_code, sub_cate_name, recommended_quantity_change
- Store results CSV with aggregated metrics
- All files have timestamped and symlinked versions
- Manifest contains all output keys

---

## 🎯 Scenario 2: SETUP - Load Clustering Results

**Scenario:** Load clustering results with column normalization

```gherkin
Given a clustering results file exists with "Cluster" column
When loading clustering data
Then the "Cluster" column is normalized to "cluster_id"
And all stores have cluster assignments
And cluster_id is validated
```

**Scenario:** Handle missing clustering results

```gherkin
Given no clustering results file exists
When loading clustering data
Then a FileNotFoundError is raised
And the error message lists all checked paths
```

---

## 🎯 Scenario 3: SETUP - Load Sales Data with Seasonal Blending

**Scenario:** Load sales data without seasonal blending

```gherkin
Given current period sales data exists
And seasonal blending is disabled
When loading sales data
Then only current period data is loaded
And sales data has required columns
```

**Scenario:** Load sales data with seasonal blending

```gherkin
Given current period sales data exists (202510A)
And seasonal period data exists (202409A from last year)
And seasonal blending is enabled with 60% seasonal weight
When loading sales data
Then current period sales are weighted by 40%
And seasonal period sales are weighted by 60%
And sales are aggregated by (store, feature)
And blended sales data is returned
```

**Scenario:** Load sales data with multi-year seasonal blending

```gherkin
Given current period sales data exists (202510A)
And seasonal data exists for 2024, 2023, 2022 (same month/period)
And seasonal_years_back is set to 3
When loading sales data
Then all 3 seasonal periods are loaded
And seasonal weight (60%) is distributed equally across 3 periods
And all periods are aggregated by (store, feature)
```

---

## 🎯 Scenario 4: SETUP - Load Quantity Data with Price Backfill

**Scenario:** Load quantity data with valid prices

```gherkin
Given store sales data with total_qty and total_amt columns
When loading quantity data
Then average unit price is calculated as total_amt / total_qty
And all stores have valid unit prices
And quantity data is returned
```

**Scenario:** Backfill missing unit prices from historical data

```gherkin
Given current period has no unit prices (all NA)
And historical data exists for previous 6 half-months
When loading quantity data
Then historical periods are loaded
And median prices are calculated per store
And missing prices are filled with historical medians
And backfill count is logged
```

**Scenario:** Fail when no real prices available (strict mode)

```gherkin
Given current period has no unit prices
And no historical data exists
When loading quantity data
Then a FileNotFoundError is raised
And error message indicates strict mode requirement
```

---

## 🎯 Scenario 5: APPLY - Identify Well-Selling Features

**Scenario:** Identify well-selling subcategories in clusters

```gherkin
Given sales data with 100 stores in cluster 1
And 90 stores sell "直筒裤" with total sales of $150,000
And 75 stores sell "锥形裤" with total sales of $120,000
And 40 stores sell "喇叭裤" with total sales of $60,000
And MIN_CLUSTER_STORES_SELLING is 70% (subcategory mode)
And MIN_CLUSTER_SALES_THRESHOLD is $100
When identifying well-selling features
Then "直筒裤" is identified as well-selling (90% adoption, $150k sales)
And "锥形裤" is identified as well-selling (75% adoption, $120k sales)
And "喇叭裤" is NOT identified (40% adoption < 70% threshold)
```

**Scenario:** Apply different thresholds for SPU mode

```gherkin
Given sales data in SPU analysis mode
And MIN_CLUSTER_STORES_SELLING is 80% (SPU mode)
And MIN_CLUSTER_SALES_THRESHOLD is $1,500
When identifying well-selling features
Then only features meeting 80% adoption and $1,500 sales are identified
```

---

## 🎯 Scenario 6: APPLY - Calculate Expected Sales Using Robust Median

**Scenario:** Calculate expected sales with outlier trimming

```gherkin
Given a well-selling feature with peer sales: [100, 150, 200, 250, 300, 5000]
When calculating expected sales per store
Then extreme values are trimmed (10th-90th percentile)
And robust median is calculated from trimmed data
And result is capped at P80 for realism
And expected sales is between $150-$300
```

**Scenario:** Apply SPU-specific cap

```gherkin
Given a well-selling SPU with peer median of $3,500
And analysis level is "spu"
When calculating expected sales per store
Then expected sales is capped at $2,000 (SPU limit)
```

---

## 🎯 Scenario 7: APPLY - Calculate Unit Price with Fallback Chain

**Scenario:** Use store average from quantity data (priority 1)

```gherkin
Given quantity_df has avg_unit_price for store "1001"
When calculating unit price for store "1001"
Then store average from quantity_df is used
And price source is "store_avg_qty_df"
```

**Scenario:** Fallback to store average from sales data (priority 2)

```gherkin
Given quantity_df has no price for store "1001"
And sales_df has amount and quantity columns for store "1001"
When calculating unit price for store "1001"
Then unit price is calculated as total_amt / total_qty from sales_df
And price source is "store_avg_from_spu_sales"
```

**Scenario:** Fallback to cluster median (priority 3)

```gherkin
Given quantity_df has no price for store "1001"
And sales_df has no price data for store "1001"
And store "1001" is in cluster 5
And cluster 5 has median price of $45.00 from other stores
When calculating unit price for store "1001"
Then cluster median price is used
And price source is "cluster_median_avg_price"
```

**Scenario:** Fail when no valid price available (strict mode)

```gherkin
Given no price data available for store "1001"
When calculating unit price for store "1001"
Then the opportunity is skipped
And a warning is logged about missing price
```

---

## 🎯 Scenario 8: APPLY - Calculate Quantity Recommendations

**Scenario:** Calculate integer quantity from expected sales

```gherkin
Given expected sales of $450 for a missing opportunity
And unit price of $35.00
And scaling factor of 1.0 (15-day period)
When calculating quantity recommendation
Then expected quantity is 450 / 35 = 12.86
And recommended quantity is ceil(12.86) = 13 units
```

**Scenario:** Ensure minimum quantity of 1

```gherkin
Given expected sales of $10 for a missing opportunity
And unit price of $50.00
When calculating quantity recommendation
Then expected quantity is 0.2
And recommended quantity is max(1, ceil(0.2)) = 1 unit
```

---

## 🎯 Scenario 9: APPLY - Sell-Through Validation with Approval Gates

**Scenario:** Approve opportunity meeting all criteria

```gherkin
Given a missing opportunity for store "1001"
And 45 stores in cluster sell this feature (90% adoption)
And sell-through validator predicts 55% sell-through
And MIN_STORES_SELLING is 5
And MIN_ADOPTION is 0.25 (25%)
And MIN_PREDICTED_ST is 30%
When validating with sell-through
Then validator approves (55% > 30%)
And adoption check passes (90% > 25%)
And store count check passes (45 > 5)
And opportunity is approved
And fast_fish_compliant is True
```

**Scenario:** Reject opportunity with low predicted sell-through

```gherkin
Given a missing opportunity for store "1001"
And sell-through validator predicts 20% sell-through
And MIN_PREDICTED_ST is 30%
When validating with sell-through
Then validator rejects (20% < 30%)
And opportunity is NOT added to results
```

**Scenario:** Reject opportunity with low adoption

```gherkin
Given a missing opportunity for store "1001"
And only 20% of cluster stores sell this feature
And MIN_ADOPTION is 0.25 (25%)
When validating with sell-through
Then adoption check fails (20% < 25%)
And opportunity is NOT added to results
```

---

## 🎯 Scenario 10: APPLY - ROI Calculation and Filtering

**Scenario:** Calculate ROI with margin rates

```gherkin
Given a missing opportunity with 10 units recommended
And unit price of $50.00
And margin rate of 40% for this (store, feature) pair
When calculating ROI metrics
Then unit cost is $50 * (1 - 0.40) = $30.00
And margin per unit is $50 - $30 = $20.00
And margin uplift is $20 * 10 = $200.00
And investment required is 10 * $30 = $300.00
And ROI is $200 / $300 = 0.67 (67%)
```

**Scenario:** Filter by ROI thresholds

```gherkin
Given ROI filtering is enabled
And an opportunity has ROI of 25%
And ROI_MIN_THRESHOLD is 30%
When applying ROI filter
Then opportunity is rejected (25% < 30%)
And opportunity is NOT added to results
```

**Scenario:** Filter by margin uplift threshold

```gherkin
Given ROI filtering is enabled
And an opportunity has margin uplift of $75
And MIN_MARGIN_UPLIFT is $100
When applying ROI filter
Then opportunity is rejected ($75 < $100)
And opportunity is NOT added to results
```

**Scenario:** Filter by minimum comparables

```gherkin
Given ROI filtering is enabled
And an opportunity has only 5 comparable stores
And MIN_COMPARABLES is 10
When applying ROI filter
Then opportunity is rejected (5 < 10)
And opportunity is NOT added to results
```

---

## 🎯 Scenario 11: APPLY - Aggregate to Store Results

**Scenario:** Aggregate multiple opportunities per store

```gherkin
Given store "1001" has 3 missing category opportunities
And opportunity 1: quantity=5, investment=$150, predicted_st=45%
And opportunity 2: quantity=8, investment=$240, predicted_st=50%
And opportunity 3: quantity=3, investment=$90, predicted_st=40%
When aggregating to store results
Then missing_categories_count is 3
And total_quantity_needed is 5 + 8 + 3 = 16
And total_investment_required is $150 + $240 + $90 = $480
And avg_predicted_sellthrough is (45 + 50 + 40) / 3 = 45%
And rule7_missing_category flag is 1
```

**Scenario:** Handle stores with no opportunities

```gherkin
Given store "1002" has no missing opportunities
When aggregating to store results
Then missing_categories_count is 0
And total_quantity_needed is 0
And total_investment_required is 0
And avg_predicted_sellthrough is 0
And rule7_missing_category flag is 0
```

---

## 🎯 Scenario 12: VALIDATE - Check Required Columns

**Scenario:** Validate results have required columns

```gherkin
Given store results DataFrame is generated
When validating results
Then required columns are present:
  | str_code |
  | cluster_id |
  | total_quantity_needed |
  | total_investment_required |
  | total_retail_value |
And no DataValidationError is raised
```

**Scenario:** Fail validation when required columns missing

```gherkin
Given store results DataFrame is missing "cluster_id" column
When validating results
Then DataValidationError is raised
And error message lists missing columns
```

---

## 🎯 Scenario 13: VALIDATE - Check Data Quality

**Scenario:** Validate no negative quantities

```gherkin
Given store results with all positive quantities
When validating results
Then no DataValidationError is raised
```

**Scenario:** Fail validation with negative quantities

```gherkin
Given store results with negative quantity for store "1001"
When validating results
Then DataValidationError is raised
And error message indicates negative quantities found
```

**Scenario:** Validate opportunities have required columns

```gherkin
Given opportunities DataFrame is generated
When validating opportunities
Then required columns are present:
  | str_code |
  | spu_code |
  | recommended_quantity_change |
  | unit_price |
  | investment_required |
And no DataValidationError is raised
```

---

## 🎯 Scenario 14: PERSIST - Save Outputs with Symlinks

**Scenario:** Save opportunities CSV with timestamped filename

```gherkin
Given opportunities DataFrame with 150 records
And current timestamp is "20251103_095000"
And period label is "202510A"
And analysis level is "spu"
When persisting opportunities
Then timestamped file is created: "output/rule7_missing_spu_sellthrough_opportunities_20251103_095000.csv"
And period symlink is created: "output/rule7_missing_spu_sellthrough_opportunities_202510A.csv"
And generic symlink is created: "output/rule7_missing_spu_sellthrough_opportunities.csv"
And all 150 records are saved
```

**Scenario:** Register outputs in manifest

```gherkin
Given opportunities CSV is saved successfully
When registering in manifest
Then key "opportunities_202510A" is registered
And key "opportunities" is registered
And metadata includes: rows=150, columns=[list], analysis_level="spu", period_label="202510A"
```

---

## 🎯 Scenario 15: PERSIST - Generate Summary Report

**Scenario:** Create markdown summary with sell-through analysis

```gherkin
Given 150 opportunities with avg sell-through improvement of 12.5pp
And total investment of $45,000
And total retail value of $75,000
When generating summary report
Then markdown file is created
And report includes executive summary
And report includes sell-through distribution
And report includes top 10 opportunities table
And report includes Fast Fish compliance confirmation
```

---

## 🎯 Scenario 16: Integration - End-to-End SPU Analysis

**Scenario:** Complete SPU-level analysis with all features

```gherkin
Given analysis level is "spu"
And clustering results exist with 5 clusters
And SPU sales data exists for current period
And seasonal blending is enabled
And quantity data exists with real prices
And margin rates are available
And sell-through validator is initialized
When executing the complete step
Then well-selling SPUs are identified (80% threshold)
And missing opportunities are found
And quantities are calculated
And sell-through validation filters opportunities
And ROI metrics are calculated
And opportunities are aggregated to store level
And all outputs are saved and registered
And Step 13 can consume the outputs
```

---

## 🎯 Scenario 17: Edge Cases

**Scenario:** Handle empty sales data

```gherkin
Given sales data is empty (0 records)
When executing the step
Then no well-selling features are identified
And no opportunities are generated
And store results show all zeros
And outputs are still created (empty)
```

**Scenario:** Handle cluster with single store

```gherkin
Given a cluster has only 1 store
When identifying well-selling features
Then no features meet adoption threshold (100% of 1 store)
And no opportunities are generated for that cluster
```

**Scenario:** Handle missing sell-through validator

```gherkin
Given sell-through validator module is not available
When initializing the step
Then RuntimeError is raised
And error message indicates validator is required in strict mode
```

**Scenario:** Handle all opportunities rejected by sell-through

```gherkin
Given 50 potential opportunities are identified
And all 50 are rejected by sell-through validation
When completing the analysis
Then opportunities DataFrame is empty
And store results show all zeros
And warning is logged about no compliant opportunities
```

---

## 📊 Test Coverage Summary

### SETUP Phase: 8 scenarios
- Clustering data loading (2)
- Sales data loading (3)
- Quantity data loading (3)

### APPLY Phase: 15 scenarios
- Well-selling identification (2)
- Expected sales calculation (2)
- Unit price calculation (4)
- Quantity calculation (2)
- Sell-through validation (3)
- ROI calculation (4)
- Aggregation (2)

### VALIDATE Phase: 4 scenarios
- Required columns (2)
- Data quality (2)

### PERSIST Phase: 3 scenarios
- File saving (1)
- Manifest registration (1)
- Report generation (1)

### Integration: 1 scenario
- End-to-end flow

### Edge Cases: 4 scenarios
- Empty data
- Single store cluster
- Missing validator
- All rejected

**Total Scenarios:** 35  
**Coverage:** Happy path, error cases, edge cases, business rules

---

**Test Scenarios Complete:** ✅  
**Next Step:** Create TEST_DESIGN.md  
**Date:** 2025-11-03
