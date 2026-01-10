Feature: Issue #2 - No Nested Directory Structure

  # NOTE: Test Data Conventions
  # - Directory paths (e.g., "output/weather_data") are ARBITRARY test values
  # - Store codes (e.g., "11014") are ARBITRARY test values
  # - Coordinates (e.g., 116.289163, 39.835836) are ARBITRARY test values
  # - Period labels (e.g., "20250801_to_20250815") are ARBITRARY test values
  # - Tests are data-agnostic and work with any valid format
  # - The code has NO special logic for specific test values

  Background:
    Given a weather file repository
    And a temporary test directory

  # ============================================================================
  # ISSUE DESCRIPTION
  # ============================================================================
  # Problem: Files were being saved to output/weather_data/weather_data/
  # Root Cause: Repository was adding another "weather_data" folder to the path
  # Factory passes output_dir="output/weather_data"
  # Repository was doing: output_dir / "weather_data" (creating nesting)
  # Result: Double nesting - output/weather_data/weather_data/
  # Fix: Repository now uses output_dir directly without adding another folder
  # ============================================================================

  Scenario: Repository should not create nested weather_data directories
    Given the factory passes output_dir as "output/weather_data"
    When I initialize the WeatherFileRepository with this output_dir
    Then the repository's weather_dir should equal the output_dir
    And the repository should NOT create a nested "weather_data" folder
    And the path should be "output/weather_data" not "output/weather_data/weather_data"

  Scenario: Files should be saved to correct location without nesting
    Given a WeatherFileRepository initialized with output_dir "output/weather_data"
    And I have weather data for store "11014" at coordinates (116.289163, 39.835836)
    And the period label is "20250801_to_20250815"
    When I save the weather file
    Then the file should be saved to "output/weather_data/weather_data_11014_116.289163_39.835836_20250801_to_20250815.csv"
    And the file should NOT be saved to "output/weather_data/weather_data/weather_data_11014_*.csv"
    And no nested "weather_data" subdirectory should exist

  Scenario: Directory structure should be flat (no subdirectories)
    Given a WeatherFileRepository initialized with output_dir "output/weather_data"
    When I save weather files for 3 different stores
    Then all files should be in "output/weather_data/" directory
    And no subdirectories should exist in "output/weather_data/"
    And the directory structure should be flat

  Scenario: Repository initialization should use output_dir directly
    Given the factory passes output_dir as "output/weather_data"
    When I initialize the WeatherFileRepository
    Then the repository's output_dir should be "output/weather_data"
    And the repository's weather_dir should be "output/weather_data"
    And output_dir should equal weather_dir (no nesting)

  # ============================================================================
  # REGRESSION TESTS (Prevent bug from returning)
  # ============================================================================

  Scenario: Bug should not return when path contains "weather_data"
    # This is a regression test to ensure the bug doesn't come back
    Given the factory passes output_dir as "output/weather_data"
    When I initialize the WeatherFileRepository
    Then the buggy nested directory "output/weather_data/weather_data/" should NOT exist
    And the repository should use output_dir directly
    And weather_dir should equal output_dir

  Scenario: Files should not be saved to nested location after fix
    # This is a regression test to verify files are in correct location
    Given a WeatherFileRepository initialized with output_dir "output/weather_data"
    When I save a weather file for store "11014"
    Then the file should exist at "output/weather_data/weather_data_11014_*.csv"
    And the file should NOT exist at "output/weather_data/weather_data/weather_data_11014_*.csv"
    And the buggy nested location should NOT contain any files

  # ============================================================================
  # VALIDATION SCENARIOS
  # ============================================================================

  Scenario: Verify correct file path construction
    Given a WeatherFileRepository with output_dir "output/weather_data"
    And store code "11014"
    And coordinates (116.289163, 39.835836)
    And period label "20250801_to_20250815"
    When I construct the file path
    Then the path should be "output/weather_data/weather_data_11014_116.289163_39.835836_20250801_to_20250815.csv"
    And the path should NOT contain "weather_data/weather_data/"

  Scenario: Verify directory creation is correct
    Given a WeatherFileRepository with output_dir "output/weather_data"
    When the repository initializes
    Then the directory "output/weather_data" should be created
    And no nested "weather_data" subdirectory should be created
    And the directory structure should be flat

  Scenario: Multiple files should all be in same directory
    Given a WeatherFileRepository with output_dir "output/weather_data"
    When I save files for stores "11014", "11041", and "11050"
    Then all 3 files should be in "output/weather_data/" directory
    And no files should be in any subdirectory
    And the directory should contain exactly 3 CSV files

  # ============================================================================
  # ERROR PREVENTION SCENARIOS
  # ============================================================================

  Scenario: Prevent accidental double nesting in future changes
    # This scenario documents what NOT to do
    Given a WeatherFileRepository with output_dir "output/weather_data"
    When I check the weather_dir property
    Then weather_dir should NOT be "output_dir / 'weather_data'"
    And weather_dir should be "output_dir" (used directly)
    And this prevents the double nesting bug

  Scenario: Verify factory and repository path handling is consistent
    # This scenario ensures factory and repository agree on paths
    Given the factory creates a WeatherFileRepository
    And the factory passes output_dir as "output/weather_data"
    When the repository initializes
    Then the repository should use the path exactly as provided
    And the repository should NOT modify or extend the path
    And the repository should NOT add additional directory levels

  # ============================================================================
  # COMPARISON: Before vs After Fix
  # ============================================================================

  Scenario: Before fix - Files were in wrong location (HISTORICAL)
    # This documents the OLD buggy behavior (for reference only)
    # NOTE: This scenario should FAIL with current code (which is correct!)
    Given the OLD buggy implementation (before fix)
    And output_dir is "output/weather_data"
    When files were saved
    Then files WERE in "output/weather_data/weather_data/" (WRONG!)
    And this caused confusion and integration issues

  Scenario: After fix - Files are in correct location (CURRENT)
    # This documents the NEW correct behavior
    Given the FIXED implementation (current code)
    And output_dir is "output/weather_data"
    When files are saved
    Then files ARE in "output/weather_data/" (CORRECT!)
    And no nested directories exist
    And this matches expected behavior
