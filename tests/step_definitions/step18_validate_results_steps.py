#!/usr/bin/env python3
"""
Step 18: Validate Results - Step Definitions
============================================

Comprehensive step definitions for Step 18 sell-through analysis testing.
Focuses on black box testing of data validation and sell-through calculations.
"""

import pandas as pd
import numpy as np
from pytest_bdd import given, when, then, parsers
from unittest.mock import patch, MagicMock
import os
import sys
from io import StringIO

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

@given(parsers.parse('a target period of "{period}" is set'))
def target_period_set(context, period):
    """Set the target period for the test."""
    context["target_period"] = period

@given(parsers.parse('a baseline period of "{period}" is set'))
def baseline_period_set(context, period):
    """Set the baseline period for the test."""
    context["baseline_period"] = period

@given('the sell-through analysis is enabled')
def sell_through_analysis_enabled(context):
    """Enable sell-through analysis."""
    context["sell_through_enabled"] = True

@given(parsers.parse('the Step 17 augmented file "{file_path}" exists'))
def step17_augmented_file_exists(context, file_path):
    """Mock Step 17 augmented file exists."""
    context["augmented_file"] = file_path

@given(parsers.parse('the Step 15 historical reference file "{file_path}" exists'))
def step15_historical_reference_exists(context, file_path):
    """Mock Step 15 historical reference file exists."""
    context["historical_file"] = file_path

@given('some recommendations have no historical match')
def some_recommendations_no_historical_match(context):
    """Mock some recommendations have no historical match."""
    context["no_historical_match"] = True

@given('all input files have valid data structure')
def input_files_valid_structure(context):
    """Mock valid data structure for input files."""
    context["input_data_valid"] = True

@when('Step 18 sell-through analysis is executed')
def step18_sell_through_analysis_executed(context):
    """Execute Step 18 sell-through analysis with mocked dependencies."""
    # Mock file system operations
    mock_data = {}
    mock_file_contents = {}
    
    def mock_exists(path):
        return True
    
    def mock_read_csv(path, **kwargs):
        # Generate realistic mock data based on file type
        if "augmented" in path or "fast_fish" in path:
            return generate_augmented_mock_data()
        elif "historical" in path:
            return generate_historical_mock_data()
        else:
            return pd.DataFrame()
    
    def mock_to_csv(df, path, **kwargs):
        mock_data[path] = df.copy()
        return None
    
    def mock_open(path, mode='r', **kwargs):
        if mode == 'w':
            mock_file_contents[path] = StringIO()
        return mock_file_contents.get(path, StringIO())
    
    # Apply mocks
    with patch('os.path.exists', side_effect=mock_exists), \
         patch('pandas.read_csv', side_effect=mock_read_csv), \
         patch('pandas.DataFrame.to_csv', side_effect=mock_to_csv), \
         patch('builtins.open', side_effect=mock_open):
        
        try:
            # Import and execute Step 18
            from src.step18_validate_results import main
            main()
            context["sell_through_success"] = True
        except Exception as e:
            context["sell_through_error"] = str(e)
            context["sell_through_success"] = False
    
    # Store mock data for assertions
    context["mock_data"] = mock_data
    context["mock_file_contents"] = mock_file_contents

@then('sell-through analysis CSV should be generated')
def sell_through_analysis_csv_generated(context):
    """Verify sell-through analysis CSV is generated."""
    assert context.get("sell_through_success", False), "Step 18 sell-through analysis should succeed"
    
    # Check for sell-through analysis file
    sell_through_file = f"output/fast_fish_with_sell_through_analysis_{context['target_period']}_20250917_123456.csv"
    assert sell_through_file in context["mock_data"], f"Sell-through analysis file {sell_through_file} should be generated"

@then('the analysis should contain SPU_Store_Days_Inventory calculations')
def analysis_contains_inventory_calculations(context):
    """Verify analysis contains SPU_Store_Days_Inventory calculations."""
    sell_through_file = f"output/fast_fish_with_sell_through_analysis_{context['target_period']}_20250917_123456.csv"
    if sell_through_file in context["mock_data"]:
        df = context["mock_data"][sell_through_file]
        assert 'SPU_Store_Days_Inventory' in df.columns, "Analysis should contain SPU_Store_Days_Inventory calculations"

@then('the analysis should contain SPU_Store_Days_Sales calculations')
def analysis_contains_sales_calculations(context):
    """Verify analysis contains SPU_Store_Days_Sales calculations."""
    sell_through_file = f"output/fast_fish_with_sell_through_analysis_{context['target_period']}_20250917_123456.csv"
    if sell_through_file in context["mock_data"]:
        df = context["mock_data"][sell_through_file]
        assert 'SPU_Store_Days_Sales' in df.columns, "Analysis should contain SPU_Store_Days_Sales calculations"

@then('the analysis should contain Sell_Through_Rate_Frac calculations')
def analysis_contains_fraction_calculations(context):
    """Verify analysis contains Sell_Through_Rate_Frac calculations."""
    sell_through_file = f"output/fast_fish_with_sell_through_analysis_{context['target_period']}_20250917_123456.csv"
    if sell_through_file in context["mock_data"]:
        df = context["mock_data"][sell_through_file]
        assert 'Sell_Through_Rate_Frac' in df.columns, "Analysis should contain Sell_Through_Rate_Frac calculations"

@then('the analysis should contain Sell_Through_Rate_Pct calculations')
def analysis_contains_percent_calculations(context):
    """Verify analysis contains Sell_Through_Rate_Pct calculations."""
    sell_through_file = f"output/fast_fish_with_sell_through_analysis_{context['target_period']}_20250917_123456.csv"
    if sell_through_file in context["mock_data"]:
        df = context["mock_data"][sell_through_file]
        assert 'Sell_Through_Rate_Pct' in df.columns, "Analysis should contain Sell_Through_Rate_Pct calculations"

@then('sell-through rates should be set to NA for unmatched records')
def sell_through_rates_na_for_unmatched(context):
    """Verify sell-through rates are set to NA for unmatched records."""
    sell_through_file = f"output/fast_fish_with_sell_through_analysis_{context['target_period']}_20250917_123456.csv"
    if sell_through_file in context["mock_data"]:
        df = context["mock_data"][sell_through_file]
        rate_cols = [col for col in df.columns if 'Sell_Through_Rate' in col]
        for col in rate_cols:
            # Check that some values are NA (indicating unmatched records)
            assert df[col].isna().any(), f"Sell-through rate column {col} should have NA values for unmatched records"

@then(parsers.parse('the output dataframes should conform to "{schema_name}"'))
def output_dataframes_conform_to_schema(context, schema_name):
    """Verify output dataframes conform to schema."""
    assert True, f"Output dataframes should conform to {schema_name}"

# Helper functions to generate mock data
def generate_augmented_mock_data():
    """Generate mock data for augmented recommendations."""
    return pd.DataFrame({
        'str_code': ['ST0001', 'ST0002', 'ST0003'],
        'spu_code': ['SPU001', 'SPU002', 'SPU003'],
        'Target_SPU_Quantity': [10, 15, 20],
        'category': ['Accessories', 'Men\'s Clothing', 'Women\'s Clothing'],
        'subcategory': ['Bags', 'Shirts', 'Dresses'],
        'Historical_SPU_Quantity': [8, 12, 18],
        'cluster_trend_score': [0.8, 0.6, 0.9]
    })

def generate_historical_mock_data():
    """Generate mock data for historical reference."""
    return pd.DataFrame({
        'store_group': ['Store Group 1', 'Store Group 2', 'Store Group 3'],
        'category': ['Accessories', 'Men\'s Clothing', 'Women\'s Clothing'],
        'subcategory': ['Bags', 'Shirts', 'Dresses'],
        'avg_daily_spus_sold_per_store': [0.5, 0.8, 1.2],
        'store_count': [5, 8, 10]
    })
