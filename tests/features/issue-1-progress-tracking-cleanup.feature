Feature: Issue #1 - Progress Tracking with Different Store Sets

  # NOTE: Test Data Conventions
  # - Period format: YYYYMM[A|B] where A=days 1-15, B=days 16-end
  # - Example periods (e.g., "202508A") are ARBITRARY test values
  # - Store codes (e.g., "11014", "11041") are ARBITRARY test values
  # - Tests are data-agnostic and work with any valid format
  # - The code has NO special logic for specific test values

  Background:
    Given a weather data repository with progress tracking
    And a temporary test directory for weather files
    And a progress tracking file

  # ============================================================================
  # ISSUE DESCRIPTION
  # ============================================================================
  # Problem: Running Step 5 with 2 stores, then with 100 stores fails
  # Root Cause: Progress marks period as "completed" but only tracks specific stores
  # When running with different store set, system thinks all stores are done
  # But only the original stores have data, causing "No weather data" error
  # ============================================================================

  Scenario: Progress marks period as completed after downloading stores
    Given I have downloaded weather data for 2 stores for period "202508A"
    And the stores are "11014" and "11041"
    When I save the progress
    Then the progress file should mark period "202508A" as completed
    And the progress file should list 2 completed stores
    And the completed stores should be "11014" and "11041"

  Scenario: Progress shows only completed stores, not all requested stores
    Given I have downloaded weather data for 2 stores for period "202508A"
    And the progress marks period "202508A" as completed
    And the progress lists only stores "11014" and "11041" as completed
    When I request weather data for 100 stores for the same period
    Then the system should see period "202508A" as completed
    But only 2 stores should have actual weather files
    And 98 stores should be missing weather data

  Scenario: Different store sets cause data mismatch (the bug)
    # This scenario documents the actual bug we discovered
    Given I have completed a run with 2 stores for period "202508A"
    And weather files exist for stores "11014" and "11041"
    And the progress file marks period "202508A" as completed
    When I run Step 5 again with 100 stores for period "202508A"
    Then the system should check the progress file
    And the system should see period "202508A" as completed
    And the system should try to load weather files for all 100 stores
    But only 2 weather files should exist
    And the system should fail with "No weather data returned from repository"

  Scenario: Cleanup fixes the issue (the workaround)
    Given I have completed a run with 2 stores for period "202508A"
    And weather files exist for stores "11014" and "11041"
    And the progress file marks period "202508A" as completed
    When I delete the progress file
    And I delete all weather data files
    And I delete the altitude file
    And I run Step 5 again with 100 stores for period "202508A"
    Then the system should see no existing progress
    And the system should download weather data for all 100 stores
    And the system should succeed with 100 stores processed

  Scenario: Progress tracking should be per-store, not per-period (recommended fix)
    # This scenario describes the recommended improvement
    Given a better progress tracking system that tracks individual stores
    And I have downloaded weather data for stores "11014" and "11041" for period "202508A"
    When I save the progress
    Then the progress should record that stores "11014" and "11041" are completed for period "202508A"
    And the progress should NOT mark the entire period as completed
    When I run Step 5 again with 100 stores for period "202508A"
    Then the system should load the progress
    And the system should see that 2 stores are already completed
    And the system should identify 98 missing stores
    And the system should download only the 98 missing stores
    And the system should succeed with all 100 stores

  Scenario: Cleanup flag should automate the workaround (recommended feature)
    # This scenario describes the recommended --clean flag
    Given I have completed a run with 2 stores for period "202508A"
    And weather files exist for stores "11014" and "11041"
    And the progress file marks period "202508A" as completed
    When I run Step 5 with the --clean flag for 100 stores for period "202508A"
    Then the system should automatically delete the progress file
    And the system should automatically delete all weather data files
    And the system should automatically delete the altitude file
    And the system should download weather data for all 100 stores
    And the system should succeed with 100 stores processed

  # ============================================================================
  # VALIDATION SCENARIOS
  # ============================================================================

  Scenario: Verify progress file structure after download
    Given I have downloaded weather data for 2 stores for period "202508A"
    When I load the progress file
    Then the progress should contain a "completed_periods" list
    And the progress should contain a "completed_stores" list
    And the progress should contain a "current_period" field
    And "202508A" should be in the completed_periods list
    And the completed_stores list should have exactly 2 entries

  Scenario: Verify cleanup removes all relevant files
    Given I have weather data files in the weather_data directory
    And I have a progress file
    And I have an altitude file
    When I perform cleanup
    Then the progress file should not exist
    And the altitude file should not exist
    And the weather_data directory should be empty

  # ============================================================================
  # ERROR SCENARIOS
  # ============================================================================

  Scenario: System fails when trying to load non-existent weather files
    Given the progress marks period "202508A" as completed
    But no weather files exist for period "202508A"
    When I try to load weather data for period "202508A"
    Then the system should find 0 weather files
    And the system should raise a DataValidationError
    And the error message should mention "No weather data returned from repository"
