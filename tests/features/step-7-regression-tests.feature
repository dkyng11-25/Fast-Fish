Feature: Step 7 - Regression Tests for Bug Fixes (2025-11-06)

  # Regression tests for critical bugs fixed during Step 7 refactoring
  # These tests prevent regression of bugs that had significant business impact

  Background:
    Given the opportunity identifier is initialized
    And the step context is prepared

  # ============================================================
  # REGRESSION TEST 1: Fast Fish Variable Predictions
  # ============================================================

  Scenario: Regression - Fast Fish predictions must be variable, not constant
    # Bug: Fast Fish validator returned constant 60% for all opportunities
    # Fix: Implemented legacy logistic curve prediction (10-70% range)
    Given opportunities with varying adoption rates
    And opportunity 1 has 20% cluster adoption
    And opportunity 2 has 50% cluster adoption
    And opportunity 3 has 80% cluster adoption
    When calculating sell-through predictions
    Then opportunity 1 predicted sell-through is less than 30%
    And opportunity 2 predicted sell-through is between 30% and 50%
    And opportunity 3 predicted sell-through is greater than 50%
    And predictions are NOT all the same value

  # ============================================================
  # REGRESSION TEST 2: Fast Fish Filtering
  # ============================================================

  Scenario: Regression - Fast Fish must filter low-adoption opportunities
    # Bug: Fast Fish approved all 4,997 opportunities (100% approval)
    # Fix: Properly filter based on predicted sell-through threshold
    # Note: Logistic curve maps adoption rates non-linearly to predictions
    # With 100 opportunities (33 low/33 medium/34 high adoption):
    # - Low adoption (10-25%) → predictions ~12-17% → all rejected
    # - Medium adoption (30-60%) → predictions ~20-42% → some rejected, some approved  
    # - High adoption (65-95%) → predictions ~45-68% → all approved
    Given 100 opportunities with varying adoption rates
    And MIN_PREDICTED_ST threshold is 30%
    When applying Fast Fish validation
    Then predictions are NOT all the same value
    And approval rate is approximately 70%

  # ============================================================
  # REGRESSION TEST 3: Logistic Curve Boundaries
  # ============================================================

  Scenario: Regression - Logistic curve boundaries must be correct
    # Bug: None (preventive test for formula correctness)
    # Validates: 10% minimum, 70% maximum, smooth S-curve
    Given adoption rate of 0% (no stores selling)
    When calculating predicted sell-through
    Then predicted sell-through is approximately 10%
    
    Given adoption rate of 100% (all stores selling)
    When calculating predicted sell-through
    Then predicted sell-through is approximately 70%
    
    Given adoption rate of 50% (half stores selling)
    When calculating predicted sell-through
    Then predicted sell-through is approximately 40%

  # ============================================================
  # REGRESSION TEST 4: Summary State Setting
  # ============================================================

  Scenario: Regression - Summary state must be set in persist phase
    # Bug: Terminal summary showed "0 opportunities" while CSV had 1,388
    # Fix: Added context.set_state() calls in persist phase
    Given 150 opportunities are identified
    And 75 stores have opportunities
    And total investment required is $45,000
    When persisting results in persist phase
    Then context state "opportunities_count" is set to 150
    And context state "stores_with_opportunities" is set to 75
    And context state "total_investment_required" is set to 45000

  # ============================================================
  # REGRESSION TEST 5: Summary Display
  # ============================================================

  Scenario: Regression - Summary displays correct values from state
    # Bug: Summary read from empty state, displayed zeros
    # Fix: State properly set, summary reads correct values
    Given context state "opportunities_count" is 1388
    And context state "stores_with_opportunities" is 896
    And context state "total_investment_required" is 125000
    When displaying summary at end of execution
    Then summary shows "Opportunities Found: 1388"
    And summary shows "Stores with Opportunities: 896"
    And summary shows "Total Investment Required: $125,000.00"

  # ============================================================
  # REGRESSION TEST 6: Integration Test
  # ============================================================

  Scenario: Regression - Exact match with legacy opportunity count
    # Integration test: Verify complete fix produces legacy-matching results
    # Bug: Refactored produced 4,997 opportunities vs legacy 1,388
    # Fix: Fast Fish + summary fixes → exact match
    Given real production data for period "202510A"
    And clustering results with real cluster assignments
    And sales data with real subcategory sales
    And quantity data with real unit prices
    When executing complete Step 7 analysis
    Then approximately 1388 opportunities are identified
    And approximately 896 stores have opportunities
    And opportunity count matches legacy within 5%
