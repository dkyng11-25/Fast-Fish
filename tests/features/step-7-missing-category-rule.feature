Feature: Step 7 - Missing Category/SPU Rule with Sell-Through Validation

  # NOTE: Test Data Conventions
  # - Period format: YYYYMM[A|B] where A=days 1-15, B=days 16-end
  # - Example periods (e.g., "202510A") are ARBITRARY test values
  # - Store codes (e.g., "0001", "1001") are ARBITRARY test identifiers
  # - Category names (e.g., "直筒裤") are ARBITRARY test examples
  # - Tests are data-agnostic and work with any valid format
  # - The code has NO special logic for specific example values

  Background:
    Given the missing category rule step is initialized
    And all repositories are mocked with test data
    And the step configuration is set for subcategory analysis

  # ============================================================
  # HAPPY PATH: Complete Analysis Flow
  # ============================================================

  Scenario: Successfully identify missing categories with quantity recommendations
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
    And store results are aggregated
    And opportunities CSV is created with required columns
    And store results CSV is created
    And all outputs are registered in manifest

  # ============================================================
  # SETUP PHASE: Data Loading
  # ============================================================

  Scenario: Load clustering results with column normalization
    Given a clustering results file with "Cluster" column
    When loading clustering data in setup phase
    Then the "Cluster" column is normalized to "cluster_id"
    And all stores have cluster assignments

  Scenario: Load sales data with seasonal blending enabled
    # NOTE: "202510A" and "202409A" are arbitrary test periods
    Given current period sales data exists for "202510A"
    And seasonal period data exists for "202409A"
    And seasonal blending is enabled with 60% seasonal weight
    When loading sales data in setup phase
    Then current period sales are weighted by 40%
    And seasonal period sales are weighted by 60%
    And sales are aggregated by store and feature

  Scenario: Backfill missing unit prices from historical data
    Given current period has no unit prices
    And historical data exists for previous 6 half-months
    When loading quantity data in setup phase
    Then missing prices are filled with historical medians
    And backfill count is logged

  Scenario: Fail when no real prices available in strict mode
    Given current period has no unit prices
    And no historical data exists
    When loading quantity data in setup phase
    Then a DataValidationError is raised
    And error message indicates strict mode requirement

  # ============================================================
  # APPLY PHASE: Well-Selling Feature Identification
  # ============================================================

  Scenario: Identify well-selling subcategories meeting adoption threshold
    # NOTE: "直筒裤" and "锥形裤" are arbitrary category examples
    Given 100 stores in cluster 1
    And 90 stores sell "直筒裤" with total sales of $150,000
    And 75 stores sell "锥形裤" with total sales of $120,000
    And 40 stores sell "喇叭裤" with total sales of $60,000
    And MIN_CLUSTER_STORES_SELLING is 70% for subcategory mode
    And MIN_CLUSTER_SALES_THRESHOLD is $100
    When identifying well-selling features in apply phase
    Then "直筒裤" is identified as well-selling
    And "锥形裤" is identified as well-selling
    And "喇叭裤" is NOT identified as well-selling

  Scenario: Apply higher thresholds for SPU mode
    Given analysis level is set to "spu"
    And MIN_CLUSTER_STORES_SELLING is 80% for SPU mode
    And MIN_CLUSTER_SALES_THRESHOLD is $1,500
    When identifying well-selling features in apply phase
    Then only features meeting 80% adoption and $1,500 sales are identified

  # ============================================================
  # APPLY PHASE: Expected Sales Calculation
  # ============================================================

  Scenario: Calculate expected sales with outlier trimming
    Given a well-selling feature with peer sales [100, 150, 200, 250, 300, 5000]
    When calculating expected sales per store in apply phase
    Then extreme values are trimmed to 10th-90th percentile
    And robust median is calculated from trimmed data
    And result is capped at P80 for realism

  Scenario: Apply SPU-specific sales cap
    Given a well-selling SPU with peer median of $3,500
    And analysis level is "spu"
    When calculating expected sales per store in apply phase
    Then expected sales is capped at $2,000

  # ============================================================
  # APPLY PHASE: Unit Price Resolution
  # ============================================================

  Scenario: Use store average from quantity data (priority 1)
    # NOTE: "1001" is an arbitrary store code
    Given quantity_df has avg_unit_price for store "1001"
    When calculating unit price for store "1001" in apply phase
    Then store average from quantity_df is used
    And price source is "store_avg_qty_df"

  Scenario: Fallback to cluster median when store price unavailable
    Given quantity_df has no price for store "1001"
    And store "1001" is in cluster 5
    And cluster 5 has median price of $45.00
    When calculating unit price for store "1001" in apply phase
    Then cluster median price is used
    And price source is "cluster_median_avg_price"

  Scenario: Skip opportunity when no valid price available
    Given no price data available for store "1001"
    When calculating unit price for store "1001" in apply phase
    Then the opportunity is skipped
    And a warning is logged about missing price

  # ============================================================
  # APPLY PHASE: Quantity Calculation
  # ============================================================

  Scenario: Calculate integer quantity from expected sales
    Given expected sales of $450 for a missing opportunity
    And unit price of $35.00
    And scaling factor of 1.0
    When calculating quantity recommendation in apply phase
    Then recommended quantity is 13 units

  Scenario: Ensure minimum quantity of 1 unit
    Given expected sales of $10 for a missing opportunity
    And unit price of $50.00
    When calculating quantity recommendation in apply phase
    Then recommended quantity is 1 unit

  # ============================================================
  # APPLY PHASE: Sell-Through Validation
  # ============================================================

  Scenario: Approve opportunity meeting all validation criteria
    Given a missing opportunity for store "1001"
    And 45 stores in cluster sell this feature
    And sell-through validator predicts 55% sell-through
    And MIN_STORES_SELLING is 5
    And MIN_ADOPTION is 25%
    And MIN_PREDICTED_ST is 30%
    When validating with sell-through in apply phase
    Then opportunity is approved
    And fast_fish_compliant is True

  Scenario: Reject opportunity with low predicted sell-through
    Given a missing opportunity for store "1001"
    And sell-through validator predicts 20% sell-through
    And MIN_PREDICTED_ST is 30%
    When validating with sell-through in apply phase
    Then opportunity is rejected
    And opportunity is NOT added to results

  Scenario: Reject opportunity with low cluster adoption
    Given a missing opportunity for store "1001"
    And only 20% of cluster stores sell this feature
    And MIN_ADOPTION is 25%
    When validating with sell-through in apply phase
    Then opportunity is rejected due to low adoption

  # ============================================================
  # APPLY PHASE: ROI Calculation
  # ============================================================

  Scenario: Calculate ROI with margin rates
    Given a missing opportunity with 10 units recommended
    And unit price of $50.00
    And margin rate of 40%
    When calculating ROI metrics in apply phase
    Then unit cost is $30.00
    And margin per unit is $20.00
    And margin uplift is $200.00
    And investment required is $300.00
    And ROI is 67%

  Scenario: Filter opportunity by ROI threshold
    Given ROI filtering is enabled
    And an opportunity has ROI of 25%
    And ROI_MIN_THRESHOLD is 30%
    When applying ROI filter in apply phase
    Then opportunity is rejected due to low ROI

  Scenario: Filter opportunity by margin uplift threshold
    Given ROI filtering is enabled
    And an opportunity has margin uplift of $75
    And MIN_MARGIN_UPLIFT is $100
    When applying ROI filter in apply phase
    Then opportunity is rejected due to low margin uplift

  # ============================================================
  # APPLY PHASE: Store-Level Aggregation
  # ============================================================

  Scenario: Aggregate multiple opportunities per store
    Given store "1001" has 3 missing category opportunities
    And opportunity 1 has quantity=5, investment=$150, predicted_st=45%
    And opportunity 2 has quantity=8, investment=$240, predicted_st=50%
    And opportunity 3 has quantity=3, investment=$90, predicted_st=40%
    When aggregating to store results in apply phase
    Then missing_categories_count is 3
    And total_quantity_needed is 16
    And total_investment_required is $480
    And avg_predicted_sellthrough is 45%
    And rule7_missing_category flag is 1

  Scenario: Handle stores with no opportunities
    Given store "1002" has no missing opportunities
    When aggregating to store results in apply phase
    Then missing_categories_count is 0
    And total_quantity_needed is 0
    And rule7_missing_category flag is 0

  # ============================================================
  # VALIDATE PHASE: Data Quality Checks
  # ============================================================

  Scenario: Validate results have required columns
    Given store results DataFrame is generated
    When validating results in validate phase
    Then required columns are present: str_code, cluster_id, total_quantity_needed
    And no DataValidationError is raised

  Scenario: Fail validation when required columns missing
    Given store results DataFrame is missing "cluster_id" column
    When validating results in validate phase
    Then DataValidationError is raised
    And error message lists missing columns

  Scenario: Fail validation with negative quantities
    Given store results with negative quantity for store "1001"
    When validating results in validate phase
    Then DataValidationError is raised
    And error message indicates negative quantities found

  Scenario: Validate opportunities have required columns
    Given opportunities DataFrame is generated
    When validating opportunities in validate phase
    Then required columns are present: str_code, spu_code, recommended_quantity_change
    And no DataValidationError is raised

  # ============================================================
  # PERSIST PHASE: Output Generation
  # ============================================================

  Scenario: Save opportunities CSV with timestamped filename
    # NOTE: Timestamp format is YYYYMMDD_HHMMSS (arbitrary example)
    Given opportunities DataFrame with 150 records
    And current timestamp is "20251103_095000"
    And period label is "202510A"
    And analysis level is "spu"
    When persisting opportunities in persist phase
    Then timestamped file is created with pattern "rule7_missing_spu_sellthrough_opportunities_20251103_095000.csv"
    And period symlink is created with pattern "rule7_missing_spu_sellthrough_opportunities_202510A.csv"
    And generic symlink is created with pattern "rule7_missing_spu_sellthrough_opportunities.csv"

  Scenario: Register outputs in manifest
    Given opportunities CSV is saved successfully
    When registering in manifest in persist phase
    Then key "opportunities_202510A" is registered
    And key "opportunities" is registered
    And metadata includes rows, columns, analysis_level, period_label

  Scenario: Generate markdown summary report
    Given 150 opportunities with avg sell-through improvement of 12.5pp
    And total investment of $45,000
    When generating summary report in persist phase
    Then markdown file is created
    And report includes executive summary
    And report includes sell-through distribution
    And report includes top 10 opportunities table

  # ============================================================
  # INTEGRATION: End-to-End Flow
  # ============================================================

  Scenario: Complete SPU-level analysis with all features
    Given analysis level is "spu"
    And clustering results exist with 5 clusters
    And SPU sales data exists for current period
    And seasonal blending is enabled
    And quantity data exists with real prices
    And margin rates are available
    And sell-through validator is initialized
    When executing the complete step end-to-end
    Then well-selling SPUs are identified with 80% threshold
    And missing opportunities are found and validated
    And quantities are calculated with real prices
    And sell-through validation filters unprofitable opportunities
    And ROI metrics are calculated
    And opportunities are aggregated to store level
    And all outputs are saved and registered
    And Step 13 can consume the outputs

  # ============================================================
  # EDGE CASES: Boundary Conditions
  # ============================================================

  Scenario: Handle empty sales data
    Given sales data is empty with 0 records
    When executing the step
    Then no well-selling features are identified
    And no opportunities are generated
    And store results show all zeros
    And outputs are still created

  Scenario: Handle cluster with single store
    Given a cluster has only 1 store
    When identifying well-selling features
    Then no features meet adoption threshold
    And no opportunities are generated for that cluster

  Scenario: Handle all opportunities rejected by sell-through
    Given 50 potential opportunities are identified
    And all 50 are rejected by sell-through validation
    When completing the analysis
    Then opportunities DataFrame is empty
    And store results show all zeros
    And warning is logged about no compliant opportunities

  Scenario: Handle missing sell-through validator
    Given sell-through validator module is not available
    When initializing the step
    Then RuntimeError is raised
    And error message indicates validator is required

  # ============================================================
  # NOTE: Regression tests moved to step-7-regression-tests.feature
  # See: tests/features/step-7-regression-tests.feature
  # See: tests/step_definitions/test_step7_regression.py
  # ============================================================
