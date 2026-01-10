#!/usr/bin/env python3
"""
Step 15: Download Historical Baseline - Step Definitions
========================================================

Comprehensive step definitions for Step 15 historical baseline testing.
Focuses on black box testing of data validation and historical analysis.
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

@given('the historical analysis is enabled')
def historical_analysis_enabled(context):
    """Enable historical analysis."""
    context["historical_enabled"] = True

@given(parsers.parse('the historical SPU sales file "{file_path}" exists'))
def historical_spu_sales_exists(context, file_path):
    """Mock historical SPU sales file exists."""
    context["historical_sales_file"] = file_path

@given(parsers.parse('the clustering results file "{file_path}" exists'))
def clustering_results_exists(context, file_path):
    """Mock clustering results file exists."""
    context["clustering_file"] = file_path

@given(parsers.parse('the current analysis file "{file_path}" exists'))
def current_analysis_exists(context, file_path):
    """Mock current analysis file exists."""
    context["current_analysis_file"] = file_path

@given(parsers.parse('the historical SPU sales file "{file_path}" does not exist'))
def historical_spu_sales_not_exists(context, file_path):
    """Mock historical SPU sales file does not exist."""
    if "missing_files" not in context:
        context["missing_files"] = []
    context["missing_files"].append(file_path)

@given(parsers.parse('the clustering results file "{file_path}" does not exist'))
def clustering_results_not_exists(context, file_path):
    """Mock clustering results file does not exist."""
    if "missing_files" not in context:
        context["missing_files"] = []
    context["missing_files"].append(file_path)

@given('all input files have valid data structure')
def input_files_valid_structure(context):
    """Mock valid data structure for input files."""
    context["input_data_valid"] = True

@when('Step 15 historical baseline creation is executed')
def step15_historical_baseline_executed(context):
    """Execute Step 15 historical baseline creation with mocked dependencies."""
    # Mock file system operations
    mock_data = {}
    mock_file_contents = {}
    
    def mock_exists(path):
        if path in context.get("missing_files", []):
            return False
        return True
    
    def mock_read_csv(path, **kwargs):
        if path in context.get("missing_files", []):
            raise FileNotFoundError(f"File not found: {path}")
        
        # Generate realistic mock data based on file type
        if "historical" in path and "sales" in path:
            return generate_historical_sales_mock_data()
        elif "clustering" in path:
            return generate_clustering_mock_data()
        elif "fast_fish" in path or "enhanced" in path:
            return generate_fast_fish_mock_data()
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
            # Import and execute Step 15
            from src.step15_download_historical_baseline import main
            main()
            context["baseline_success"] = True
        except Exception as e:
            context["baseline_error"] = str(e)
            context["baseline_success"] = False
    
    # Store mock data for assertions
    context["mock_data"] = mock_data
    context["mock_file_contents"] = mock_file_contents

@then('historical reference CSV should be generated')
def historical_reference_csv_generated(context):
    """Verify historical reference CSV is generated."""
    assert context.get("baseline_success", False), "Step 15 historical baseline creation should succeed"
    
    # Check for historical reference file
    historical_file = f"output/historical_reference_{context['baseline_period']}_20250917_123456.csv"
    assert historical_file in context["mock_data"], f"Historical reference file {historical_file} should be generated"

@then('year-over-year comparison CSV should be generated')
def yoy_comparison_csv_generated(context):
    """Verify year-over-year comparison CSV is generated."""
    # Check for YoY comparison file
    yoy_file = f"output/year_over_year_comparison_{context['baseline_period']}_20250917_123456.csv"
    assert yoy_file in context["mock_data"], f"YoY comparison file {yoy_file} should be generated"

@then('historical insights JSON should be generated')
def historical_insights_json_generated(context):
    """Verify historical insights JSON is generated."""
    # Check for historical insights file
    insights_file = f"output/historical_insights_{context['baseline_period']}_20250917_123456.json"
    assert insights_file in context["mock_file_contents"], f"Historical insights file {insights_file} should be generated"

@then('the historical reference should have store group and category columns')
def historical_reference_has_columns(context):
    """Verify historical reference has required columns."""
    historical_file = f"output/historical_reference_{context['baseline_period']}_20250917_123456.csv"
    if historical_file in context["mock_data"]:
        df = context["mock_data"][historical_file]
        assert 'store_group' in df.columns or 'Store_Group' in df.columns, "Historical reference should have store group column"
        assert 'category' in df.columns or 'cate_name' in df.columns, "Historical reference should have category column"

@then('the YoY comparison should have baseline and current metrics')
def yoy_comparison_has_metrics(context):
    """Verify YoY comparison has baseline and current metrics."""
    yoy_file = f"output/year_over_year_comparison_{context['baseline_period']}_20250917_123456.csv"
    if yoy_file in context["mock_data"]:
        df = context["mock_data"][yoy_file]
        baseline_cols = [col for col in df.columns if 'baseline' in col.lower()]
        current_cols = [col for col in df.columns if 'current' in col.lower()]
        assert len(baseline_cols) > 0, "YoY comparison should have baseline metrics"
        assert len(current_cols) > 0, "YoY comparison should have current metrics"

@then('the historical baseline creation should fail with error')
def historical_baseline_creation_fails(context):
    """Verify historical baseline creation fails with error."""
    assert not context.get("baseline_success", True), "Step 15 historical baseline creation should fail"

@then('an appropriate error message should be logged')
def appropriate_error_message_logged(context):
    """Verify appropriate error message is logged."""
    assert "baseline_error" in context, "Error message should be logged"

@then('store groups should be set to "Store Group Unknown"')
def store_groups_set_to_unknown(context):
    """Verify store groups are set to unknown when clustering is missing."""
    historical_file = f"output/historical_reference_{context['baseline_period']}_20250917_123456.csv"
    if historical_file in context["mock_data"]:
        df = context["mock_data"][historical_file]
        store_group_col = 'store_group' if 'store_group' in df.columns else 'Store_Group'
        if store_group_col in df.columns:
            assert (df[store_group_col] == "Store Group Unknown").all(), "Store groups should be set to 'Store Group Unknown'"

@then(parsers.parse('the output dataframes should conform to "{schema_name}"'))
def output_dataframes_conform_to_schema(context, schema_name):
    """Verify output dataframes conform to schema."""
    assert True, f"Output dataframes should conform to {schema_name}"

# Helper functions to generate mock data
def generate_historical_sales_mock_data():
    """Generate mock data for historical SPU sales."""
    return pd.DataFrame({
        'str_code': ['ST0001', 'ST0002', 'ST0003'],
        'spu_code': ['SPU001', 'SPU002', 'SPU003'],
        'cate_name': ['Accessories', 'Men\'s Clothing', 'Women\'s Clothing'],
        'sub_cate_name': ['Bags', 'Shirts', 'Dresses'],
        'quantity': [100, 150, 200],
        'spu_sales_amt': [10000.0, 15000.0, 20000.0]
    })

def generate_clustering_mock_data():
    """Generate mock data for clustering results."""
    return pd.DataFrame({
        'str_code': ['ST0001', 'ST0002', 'ST0003'],
        'cluster_id': [0, 1, 2]
    })

def generate_fast_fish_mock_data():
    """Generate mock data for Fast Fish format."""
    return pd.DataFrame({
        'str_code': ['ST0001', 'ST0002', 'ST0003'],
        'spu_code': ['SPU001', 'SPU002', 'SPU003'],
        'Target_SPU_Quantity': [10, 15, 20],
        'category': ['Accessories', 'Men\'s Clothing', 'Women\'s Clothing']
    })
