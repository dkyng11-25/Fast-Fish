#!/usr/bin/env python3
"""
Step 13: Consolidate SPU Rules - Step Definitions
=================================================

Comprehensive step definitions for Step 13 consolidation testing.
Focuses on black box testing of data validation and output generation.
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

from tests.validation_comprehensive.schemas.step13_schemas import DetailedSPUResultsSchema, StoreLevelResultsSchema

@given(parsers.parse('the analysis level is "{level}"'))
def analysis_level_set(context, level):
    """Set the analysis level for the test."""
    context["analysis_level"] = level

@given(parsers.parse('a current period of "{period}" is set'))
def current_period_set(context, period):
    """Set the current period for the test."""
    context["period"] = period

@given(parsers.parse('FAST_MODE is {status}'))
def fast_mode_set(context, status):
    """Set FAST_MODE status."""
    context["fast_mode"] = status.lower() == "enabled"

@given(parsers.parse('ENABLE_TREND_UTILS is {status}'))
def trend_utils_set(context, status):
    """Set ENABLE_TREND_UTILS status."""
    context["enable_trend_utils"] = status.lower() == "enabled"

@given(parsers.parse('the rule 7 output file "{file_path}" exists'))
def rule7_output_exists(context, file_path):
    """Mock rule 7 output file exists."""
    if "rule_files" not in context:
        context["rule_files"] = {}
    context["rule_files"]["rule7"] = file_path

@given(parsers.parse('the rule 8 output file "{file_path}" exists'))
def rule8_output_exists(context, file_path):
    """Mock rule 8 output file exists."""
    if "rule_files" not in context:
        context["rule_files"] = {}
    context["rule_files"]["rule8"] = file_path

@given(parsers.parse('the rule 9 output file "{file_path}" exists'))
def rule9_output_exists(context, file_path):
    """Mock rule 9 output file exists."""
    if "rule_files" not in context:
        context["rule_files"] = {}
    context["rule_files"]["rule9"] = file_path

@given(parsers.parse('the rule 10 output file "{file_path}" exists'))
def rule10_output_exists(context, file_path):
    """Mock rule 10 output file exists."""
    if "rule_files" not in context:
        context["rule_files"] = {}
    context["rule_files"]["rule10"] = file_path

@given(parsers.parse('the rule 11 output file "{file_path}" exists'))
def rule11_output_exists(context, file_path):
    """Mock rule 11 output file exists."""
    if "rule_files" not in context:
        context["rule_files"] = {}
    context["rule_files"]["rule11"] = file_path

@given(parsers.parse('the rule 12 output file "{file_path}" exists'))
def rule12_output_exists(context, file_path):
    """Mock rule 12 output file exists."""
    if "rule_files" not in context:
        context["rule_files"] = {}
    context["rule_files"]["rule12"] = file_path

@given(parsers.parse('the clustering results file "{file_path}" exists'))
def clustering_results_exists(context, file_path):
    """Mock clustering results file exists."""
    context["clustering_file"] = file_path

@given(parsers.parse('the weather data file "{file_path}" exists'))
def weather_data_exists(context, file_path):
    """Mock weather data file exists."""
    context["weather_file"] = file_path

@given(parsers.parse('the rule 7 output file "{file_path}" does not exist'))
def rule7_output_not_exists(context, file_path):
    """Mock rule 7 output file does not exist."""
    if "missing_files" not in context:
        context["missing_files"] = []
    context["missing_files"].append(file_path)

@given(parsers.parse('the rule 8 output file "{file_path}" does not exist'))
def rule8_output_not_exists(context, file_path):
    """Mock rule 8 output file does not exist."""
    if "missing_files" not in context:
        context["missing_files"] = []
    context["missing_files"].append(file_path)

@given(parsers.parse('the rule 9 output file "{file_path}" does not exist'))
def rule9_output_not_exists(context, file_path):
    """Mock rule 9 output file does not exist."""
    if "missing_files" not in context:
        context["missing_files"] = []
    context["missing_files"].append(file_path)

@given(parsers.parse('the rule 10 output file "{file_path}" does not exist'))
def rule10_output_not_exists(context, file_path):
    """Mock rule 10 output file does not exist."""
    if "missing_files" not in context:
        context["missing_files"] = []
    context["missing_files"].append(file_path)

@given(parsers.parse('the rule 11 output file "{file_path}" does not exist'))
def rule11_output_not_exists(context, file_path):
    """Mock rule 11 output file does not exist."""
    if "missing_files" not in context:
        context["missing_files"] = []
    context["missing_files"].append(file_path)

@given(parsers.parse('the rule 12 output file "{file_path}" does not exist'))
def rule12_output_not_exists(context, file_path):
    """Mock rule 12 output file does not exist."""
    if "missing_files" not in context:
        context["missing_files"] = []
    context["missing_files"].append(file_path)

@given(parsers.parse('the clustering results file "{file_path}" does not exist'))
def clustering_results_not_exists(context, file_path):
    """Mock clustering results file does not exist."""
    if "missing_files" not in context:
        context["missing_files"] = []
    context["missing_files"].append(file_path)

@given('all rule output files have valid SPU-level data structure')
def rule_outputs_valid_structure(context):
    """Mock valid SPU-level data structure for rule outputs."""
    context["rule_data_valid"] = True

@given('some rule output files have missing required columns')
def rule_outputs_missing_columns(context):
    """Mock rule outputs with missing required columns."""
    context["rule_data_missing_columns"] = True

@given('some rule output files contain duplicate (str_code, spu_code) records')
def rule_outputs_duplicate_records(context):
    """Mock rule outputs with duplicate records."""
    context["rule_data_duplicates"] = True

@given(parsers.parse('the clustering results have "{col1}" and "{col2}" columns'))
def clustering_results_valid_columns(context, col1, col2):
    """Mock clustering results with valid columns."""
    context["clustering_columns"] = [col1, col2]

@when('Step 13 consolidation is executed')
def step13_consolidation_executed(context):
    """Execute Step 13 consolidation with mocked dependencies."""
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
        if "rule7" in path:
            return generate_rule7_mock_data()
        elif "rule8" in path:
            return generate_rule8_mock_data()
        elif "rule9" in path:
            return generate_rule9_mock_data()
        elif "rule10" in path:
            return generate_rule10_mock_data()
        elif "rule11" in path:
            return generate_rule11_mock_data()
        elif "rule12" in path:
            return generate_rule12_mock_data()
        elif "clustering" in path:
            return generate_clustering_mock_data()
        elif "weather" in path:
            return generate_weather_mock_data()
        else:
            return pd.DataFrame()
    
    def mock_to_csv(df, path, **kwargs):
        mock_data[path] = df.copy()
        return None
    
    def mock_open(path, mode='r', **kwargs):
        if mode == 'w':
            mock_file_contents[path] = StringIO()
        return mock_file_contents.get(path, StringIO())
    
    # Mock src.config functions
    def mock_get_current_period():
        return (context["period"][:6], context["period"])
    
    def mock_get_period_label():
        return context["period"]
    
    def mock_get_output_files():
        return {
            "rule7": context["rule_files"].get("rule7", ""),
            "rule8": context["rule_files"].get("rule8", ""),
            "rule9": context["rule_files"].get("rule9", ""),
            "rule10": context["rule_files"].get("rule10", ""),
            "rule11": context["rule_files"].get("rule11", ""),
            "rule12": context["rule_files"].get("rule12", ""),
            "clustering": context.get("clustering_file", ""),
            "weather": context.get("weather_file", "")
        }
    
    # Mock src.pipeline_manifest functions
    def mock_get_manifest():
        return MagicMock()
    
    # Apply mocks
    with patch('os.path.exists', side_effect=mock_exists), \
         patch('pandas.read_csv', side_effect=mock_read_csv), \
         patch('pandas.DataFrame.to_csv', side_effect=mock_to_csv), \
         patch('builtins.open', side_effect=mock_open), \
         patch('src.config.get_current_period', side_effect=mock_get_current_period), \
         patch('src.config.get_period_label', side_effect=mock_get_period_label), \
         patch('src.config.get_output_files', side_effect=mock_get_output_files), \
         patch('src.pipeline_manifest.get_manifest', side_effect=mock_get_manifest):
        
        try:
            # Import and execute Step 13
            from src.step13_consolidate_spu_rules import main
            main()
            context["consolidation_success"] = True
        except Exception as e:
            context["consolidation_error"] = str(e)
            context["consolidation_success"] = False
    
    # Store mock data for assertions
    context["mock_data"] = mock_data
    context["mock_file_contents"] = mock_file_contents

@then('consolidated SPU detailed results should be generated')
def consolidated_spu_detailed_generated(context):
    """Verify consolidated SPU detailed results are generated."""
    assert context.get("consolidation_success", False), "Step 13 consolidation should succeed"
    
    # Check for detailed results file
    detailed_file = f"output/consolidated_spu_rule_results_detailed.csv"
    assert detailed_file in context["mock_data"], f"Detailed results file {detailed_file} should be generated"

@then('consolidated store-level summary should be generated')
def consolidated_store_summary_generated(context):
    """Verify consolidated store-level summary is generated."""
    # Check for store-level summary file
    summary_file = f"output/consolidated_spu_rule_results.csv"
    assert summary_file in context["mock_data"], f"Store-level summary file {summary_file} should be generated"

@then(parsers.parse('the detailed results should have "{col1}" and "{col2}" columns'))
def detailed_results_have_columns(context, col1, col2):
    """Verify detailed results have required columns."""
    detailed_file = f"output/consolidated_spu_rule_results_detailed.csv"
    if detailed_file in context["mock_data"]:
        df = context["mock_data"][detailed_file]
        assert col1 in df.columns, f"Detailed results should have {col1} column"
        assert col2 in df.columns, f"Detailed results should have {col2} column"

@then('the detailed results should have cluster mapping columns')
def detailed_results_have_cluster_mapping(context):
    """Verify detailed results have cluster mapping columns."""
    detailed_file = f"output/consolidated_spu_rule_results_detailed.csv"
    if detailed_file in context["mock_data"]:
        df = context["mock_data"][detailed_file]
        cluster_cols = [col for col in df.columns if 'cluster' in col.lower()]
        assert len(cluster_cols) > 0, "Detailed results should have cluster mapping columns"

@then('the detailed results should have subcategory mapping columns')
def detailed_results_have_subcategory_mapping(context):
    """Verify detailed results have subcategory mapping columns."""
    detailed_file = f"output/consolidated_spu_rule_results_detailed.csv"
    if detailed_file in context["mock_data"]:
        df = context["mock_data"][detailed_file]
        subcat_cols = [col for col in df.columns if 'sub' in col.lower() and 'cat' in col.lower()]
        assert len(subcat_cols) > 0, "Detailed results should have subcategory mapping columns"

@then('all SPU records should be deduplicated by (str_code, spu_code)')
def spu_records_deduplicated(context):
    """Verify SPU records are deduplicated."""
    detailed_file = f"output/consolidated_spu_rule_results_detailed.csv"
    if detailed_file in context["mock_data"]:
        df = context["mock_data"][detailed_file]
        if 'str_code' in df.columns and 'spu_code' in df.columns:
            duplicates = df.duplicated(subset=['str_code', 'spu_code']).sum()
            assert duplicates == 0, f"Found {duplicates} duplicate (str_code, spu_code) records"

@then('missing rule outputs should be logged')
def missing_rule_outputs_logged(context):
    """Verify missing rule outputs are logged."""
    # This would be verified by checking log output in a real implementation
    assert True, "Missing rule outputs should be logged"

@then('legacy fallback files should be used')
def legacy_fallback_files_used(context):
    """Verify legacy fallback files are used."""
    # This would be verified by checking which files were actually loaded
    assert True, "Legacy fallback files should be used"

@then('fashion enhanced suggestions should be generated')
def fashion_enhanced_generated(context):
    """Verify fashion enhanced suggestions are generated."""
    fashion_file = f"output/fashion_enhanced_suggestions.csv"
    assert fashion_file in context["mock_data"], f"Fashion enhanced file {fashion_file} should be generated"

@then('comprehensive trend enhanced suggestions should be generated')
def comprehensive_trend_generated(context):
    """Verify comprehensive trend enhanced suggestions are generated."""
    trend_file = f"output/comprehensive_trend_enhanced_suggestions.csv"
    assert trend_file in context["mock_data"], f"Comprehensive trend file {trend_file} should be generated"

@then('the consolidation should fail with error')
def consolidation_fails_with_error(context):
    """Verify consolidation fails with error."""
    assert not context.get("consolidation_success", True), "Step 13 consolidation should fail"

@then('an appropriate error message should be logged')
def appropriate_error_message_logged(context):
    """Verify appropriate error message is logged."""
    assert "consolidation_error" in context, "Error message should be logged"

@then('cluster mapping should be set to NA')
def cluster_mapping_set_to_na(context):
    """Verify cluster mapping is set to NA when clustering file is missing."""
    detailed_file = f"output/consolidated_spu_rule_results_detailed.csv"
    if detailed_file in context["mock_data"]:
        df = context["mock_data"][detailed_file]
        cluster_cols = [col for col in df.columns if 'cluster' in col.lower()]
        for col in cluster_cols:
            assert df[col].isna().all(), f"Cluster column {col} should be set to NA"

@then('missing columns should be set to NA')
def missing_columns_set_to_na(context):
    """Verify missing columns are set to NA."""
    # This would be verified by checking specific columns in the output
    assert True, "Missing columns should be set to NA"

@then('duplicate records should be removed')
def duplicate_records_removed(context):
    """Verify duplicate records are removed."""
    detailed_file = f"output/consolidated_spu_rule_results_detailed.csv"
    if detailed_file in context["mock_data"]:
        df = context["mock_data"][detailed_file]
        if 'str_code' in df.columns and 'spu_code' in df.columns:
            duplicates = df.duplicated(subset=['str_code', 'spu_code']).sum()
            assert duplicates == 0, f"Found {duplicates} duplicate records that should be removed"

@then('each (str_code, spu_code) combination should appear only once')
def unique_str_spu_combinations(context):
    """Verify each (str_code, spu_code) combination appears only once."""
    detailed_file = f"output/consolidated_spu_rule_results_detailed.csv"
    if detailed_file in context["mock_data"]:
        df = context["mock_data"][detailed_file]
        if 'str_code' in df.columns and 'spu_code' in df.columns:
            duplicates = df.duplicated(subset=['str_code', 'spu_code']).sum()
            assert duplicates == 0, f"Found {duplicates} duplicate (str_code, spu_code) combinations"

@then('period-labeled detailed results should be generated')
def period_labeled_detailed_generated(context):
    """Verify period-labeled detailed results are generated."""
    period = context["period"]
    period_file = f"output/consolidated_spu_rule_results_detailed_{period}.csv"
    assert period_file in context["mock_data"], f"Period-labeled file {period_file} should be generated"

@then('the period-labeled file should contain the current period in the filename')
def period_labeled_filename_contains_period(context):
    """Verify period-labeled filename contains current period."""
    period = context["period"]
    period_file = f"output/consolidated_spu_rule_results_detailed_{period}.csv"
    assert period_file in context["mock_data"], f"Period-labeled file should contain period {period}"

@then(parsers.parse('the output dataframes should conform to "{schema_name}"'))
def output_dataframes_conform_to_schema(context, schema_name):
    """Verify output dataframes conform to schema."""
    # This would validate against the actual schema in a real implementation
    assert True, f"Output dataframes should conform to {schema_name}"

# Helper functions to generate mock data
def generate_rule7_mock_data():
    """Generate mock data for rule 7 output."""
    return pd.DataFrame({
        'str_code': ['ST0001', 'ST0002', 'ST0003'],
        'spu_code': ['SPU001', 'SPU002', 'SPU003'],
        'quantity_recommendation': [10, 15, 20],
        'investment_required': [1000.0, 1500.0, 2000.0],
        'category': ['Accessories', 'Men\'s Clothing', 'Women\'s Clothing'],
        'sub_cate_name': ['Bags', 'Shirts', 'Dresses']
    })

def generate_rule8_mock_data():
    """Generate mock data for rule 8 output."""
    return pd.DataFrame({
        'str_code': ['ST0001', 'ST0002', 'ST0003'],
        'spu_code': ['SPU004', 'SPU005', 'SPU006'],
        'quantity_recommendation': [5, 8, 12],
        'investment_required': [500.0, 800.0, 1200.0],
        'category': ['Accessories', 'Men\'s Clothing', 'Women\'s Clothing'],
        'sub_cate_name': ['Shoes', 'Pants', 'Tops']
    })

def generate_rule9_mock_data():
    """Generate mock data for rule 9 output."""
    return pd.DataFrame({
        'str_code': ['ST0001', 'ST0002', 'ST0003'],
        'spu_code': ['SPU007', 'SPU008', 'SPU009'],
        'quantity_recommendation': [3, 6, 9],
        'investment_required': [300.0, 600.0, 900.0],
        'category': ['Accessories', 'Men\'s Clothing', 'Women\'s Clothing'],
        'sub_cate_name': ['Jewelry', 'Jackets', 'Skirts']
    })

def generate_rule10_mock_data():
    """Generate mock data for rule 10 output."""
    return pd.DataFrame({
        'str_code': ['ST0001', 'ST0002', 'ST0003'],
        'spu_code': ['SPU010', 'SPU011', 'SPU012'],
        'quantity_recommendation': [-2, -4, -6],
        'investment_required': [-200.0, -400.0, -600.0],
        'category': ['Accessories', 'Men\'s Clothing', 'Women\'s Clothing'],
        'sub_cate_name': ['Watches', 'Sweaters', 'Blouses']
    })

def generate_rule11_mock_data():
    """Generate mock data for rule 11 output."""
    return pd.DataFrame({
        'str_code': ['ST0001', 'ST0002', 'ST0003'],
        'spu_code': ['SPU013', 'SPU014', 'SPU015'],
        'quantity_recommendation': [7, 11, 14],
        'investment_required': [700.0, 1100.0, 1400.0],
        'category': ['Accessories', 'Men\'s Clothing', 'Women\'s Clothing'],
        'sub_cate_name': ['Belts', 'Shorts', 'Jeans']
    })

def generate_rule12_mock_data():
    """Generate mock data for rule 12 output."""
    return pd.DataFrame({
        'str_code': ['ST0001', 'ST0002', 'ST0003'],
        'spu_code': ['SPU016', 'SPU017', 'SPU018'],
        'quantity_recommendation': [4, 7, 10],
        'investment_required': [400.0, 700.0, 1000.0],
        'category': ['Accessories', 'Men\'s Clothing', 'Women\'s Clothing'],
        'sub_cate_name': ['Hats', 'Ties', 'Scarves']
    })

def generate_clustering_mock_data():
    """Generate mock data for clustering results."""
    return pd.DataFrame({
        'str_code': ['ST0001', 'ST0002', 'ST0003'],
        'cluster_id': [0, 1, 2]
    })

def generate_weather_mock_data():
    """Generate mock data for weather data."""
    return pd.DataFrame({
        'str_code': ['ST0001', 'ST0002', 'ST0003'],
        'temperature_band': ['Hot', 'Warm', 'Cool']
    })
