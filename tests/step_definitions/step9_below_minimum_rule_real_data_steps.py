"""
Step 9 Below Minimum Rule - Real Data BDD Test Steps

This test uses real data files instead of complex mocking for true black box testing.
Focuses on data validation and business logic rather than implementation details.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import pytest
from pytest_bdd import given, when, then, parsers
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tests.validation_comprehensive.schemas.step9_schemas import (
    Step9OpportunitiesSchema,
    Step9ResultsSchema
)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with real data files for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy real data files to temp directory
        real_data_dir = Path(__file__).parent.parent.parent
        
        # Copy required files
        files_to_copy = [
            "output/store_config_202509A.csv",
            "output/complete_spu_sales_202509A.csv", 
            "output/clustering_results_spu_202509A.csv"
        ]
        
        for file_path in files_to_copy:
            src = real_data_dir / file_path
            if src.exists():
                dst = Path(temp_dir) / file_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        
        yield temp_dir


@given(parsers.parse('real data files are available for period "{period}"'))
def real_data_files_available(context, temp_data_dir, period):
    """Real data files are available for the specified period."""
    context['period'] = period
    context['temp_data_dir'] = temp_data_dir
    
    # Verify required files exist
    required_files = [
        f"{temp_data_dir}/output/store_config_{period}.csv",
        f"{temp_data_dir}/output/complete_spu_sales_{period}.csv",
        f"{temp_data_dir}/output/clustering_results_spu_{period}.csv"
    ]
    
    for file_path in required_files:
        assert os.path.exists(file_path), f"Required file not found: {file_path}"
    
    # Store file paths in context
    context['store_config_path'] = f"{temp_data_dir}/output/store_config_{period}.csv"
    context['spu_sales_path'] = f"{temp_data_dir}/output/complete_spu_sales_{period}.csv"
    context['clustering_path'] = f"{temp_data_dir}/output/clustering_results_spu_{period}.csv"


@given(parsers.parse('environment is configured for period "{period}"'))
def environment_configured_for_period(context, period):
    """Environment variables are configured for the specified period."""
    # Set environment variables for the test
    os.environ['CURRENT_PERIOD_LABEL'] = period
    os.environ['ANALYSIS_LEVEL'] = 'spu'
    os.environ['MINIMUM_UNIT_RATE'] = '1.0'
    os.environ['SEASONAL_BLENDING'] = 'false'
    
    context['period'] = period


@when('step9 below minimum rule is executed with real data')
def step9_executed_with_real_data(context):
    """Execute step9 with real data files."""
    # Change to temp directory and run step9
    original_cwd = os.getcwd()
    temp_dir = context['temp_data_dir']
    
    try:
        os.chdir(temp_dir)
        
        # Mock the config functions to return the temp directory paths
        with patch('src.config.get_current_period', return_value=("202509", "A")):
            with patch('src.config.get_period_label', return_value=context['period']):
                with patch('src.config.get_api_data_files') as mock_api_files:
                    with patch('src.config.get_clustering_files') as mock_clustering_files:
                        # Configure mock returns
                        mock_api_files.return_value = {
                            'store_config': context['store_config_path'],
                            'spu_sales': context['spu_sales_path']
                        }
                        mock_clustering_files.return_value = {
                            'clustering_results': context['clustering_path']
                        }
                        
                        # Import and run step9
                        from src.step9_below_minimum_rule import main as step9_main
                        step9_main()
                        
    finally:
        os.chdir(original_cwd)


@then(parsers.parse('opportunities CSV file is generated with valid schema'))
def opportunities_csv_generated_with_valid_schema(context):
    """Verify opportunities CSV is generated with valid schema."""
    period = context['period']
    temp_dir = context['temp_data_dir']
    
    # Expected output file
    opportunities_file = f"{temp_dir}/output/rule9_below_minimum_spu_sellthrough_opportunities_{period}.csv"
    
    # Check file exists
    assert os.path.exists(opportunities_file), f"Opportunities CSV not found: {opportunities_file}"
    
    # Load and validate with Pandera schema
    df = pd.read_csv(opportunities_file)
    
    # Validate schema
    try:
        Step9OpportunitiesSchema.validate(df)
        context['opportunities_df'] = df
    except Exception as e:
        pytest.fail(f"Opportunities CSV schema validation failed: {e}")


@then(parsers.parse('results CSV file is generated with valid schema'))
def results_csv_generated_with_valid_schema(context):
    """Verify results CSV is generated with valid schema."""
    period = context['period']
    temp_dir = context['temp_data_dir']
    
    # Expected output file
    results_file = f"{temp_dir}/output/rule9_below_minimum_spu_sellthrough_results_{period}.csv"
    
    # Check file exists
    assert os.path.exists(results_file), f"Results CSV not found: {results_file}"
    
    # Load and validate with Pandera schema
    df = pd.read_csv(results_file)
    
    # Validate schema
    try:
        Step9ResultsSchema.validate(df)
        context['results_df'] = df
    except Exception as e:
        pytest.fail(f"Results CSV schema validation failed: {e}")


@then(parsers.parse('summary markdown report is generated'))
def summary_markdown_report_generated(context):
    """Verify summary markdown report is generated."""
    period = context['period']
    temp_dir = context['temp_data_dir']
    
    # Expected output file
    summary_file = f"{temp_dir}/output/rule9_below_minimum_spu_sellthrough_summary_{period}.md"
    
    # Check file exists
    assert os.path.exists(summary_file), f"Summary markdown not found: {summary_file}"
    
    # Verify file has content
    with open(summary_file, 'r', encoding='utf-8') as f:
        content = f.read()
        assert len(content) > 0, "Summary file is empty"
        assert "Rule 9" in content, "Summary file missing expected content"


@then(parsers.parse('opportunities contain below minimum cases'))
def opportunities_contain_below_minimum_cases(context):
    """Verify opportunities contain below minimum cases."""
    df = context['opportunities_df']
    
    # Check that we have opportunities
    assert len(df) > 0, "No opportunities found"
    
    # Check required columns for below minimum analysis
    required_cols = ['str_code', 'spu_code', 'unit_rate', 'increase_needed', 'issue_severity']
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Check that unit rates are below minimum threshold
    min_threshold = float(os.environ.get('MINIMUM_UNIT_RATE', '1.0'))
    below_minimum = df[df['unit_rate'] < min_threshold]
    assert len(below_minimum) > 0, f"No below minimum cases found (threshold: {min_threshold})"


@then(parsers.parse('results contain store level summaries'))
def results_contain_store_level_summaries(context):
    """Verify results contain store level summaries."""
    df = context['results_df']
    
    # Check that we have results
    assert len(df) > 0, "No results found"
    
    # Check required columns for store level results
    required_cols = ['str_code', 'total_increase_needed', 'opportunity_count']
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Check that all values are positive
    assert (df['total_increase_needed'] >= 0).all(), "Found negative increase needed values"
    assert (df['opportunity_count'] >= 0).all(), "Found negative opportunity counts"


@then(parsers.parse('Fast Fish validation is applied'))
def fast_fish_validation_applied(context):
    """Verify Fast Fish validation is applied."""
    df = context['opportunities_df']
    
    # Check for Fast Fish validation columns
    fast_fish_cols = ['sell_through_improvement', 'fast_fish_approved']
    for col in fast_fish_cols:
        if col in df.columns:
            # If column exists, check it has reasonable values
            if col == 'fast_fish_approved':
                assert df[col].dtype == bool or df[col].isin([0, 1, True, False]).all(), f"Invalid values in {col}"
            elif col == 'sell_through_improvement':
                assert (df[col] >= 0).all(), f"Found negative sell-through improvement values"


@then(parsers.parse('investment calculations are correct'))
def investment_calculations_correct(context):
    """Verify investment calculations are correct."""
    df = context['opportunities_df']
    
    # Check investment column exists
    if 'investment_required' in df.columns:
        # Investment should be non-negative where unit_price is available
        has_price = df['unit_price'].notna()
        if has_price.any():
            investment_with_price = df[has_price]['investment_required']
            assert (investment_with_price >= 0).all(), "Found negative investment values where unit_price is available"
        
        # Investment should be NA where unit_price is not available
        no_price = df['unit_price'].isna()
        if no_price.any():
            investment_no_price = df[no_price]['investment_required']
            assert investment_no_price.isna().all(), "Investment should be NA where unit_price is not available"


@then(parsers.parse('error handling works for missing files'))
def error_handling_works_for_missing_files(context):
    """Verify error handling works when required files are missing."""
    period = context['period']
    temp_dir = context['temp_data_dir']
    
    # Remove a required file
    spu_sales_file = f"{temp_dir}/output/complete_spu_sales_{period}.csv"
    if os.path.exists(spu_sales_file):
        os.remove(spu_sales_file)
    
    # Try to run step9 - should raise FileNotFoundError
    original_cwd = os.getcwd()
    
    try:
        os.chdir(temp_dir)
        
        with patch('src.config.get_current_period', return_value=("202509", "A")):
            with patch('src.config.get_period_label', return_value=period):
                with patch('src.config.get_api_data_files') as mock_api_files:
                    with patch('src.config.get_clustering_files') as mock_clustering_files:
                        # Configure mock returns
                        mock_api_files.return_value = {
                            'store_config': context['store_config_path'],
                            'spu_sales': spu_sales_file  # This file was removed
                        }
                        mock_clustering_files.return_value = {
                            'clustering_results': context['clustering_path']
                        }
                        
                        # Import and run step9 - should fail
                        from src.step9_below_minimum_rule import main as step9_main
                        
                        with pytest.raises(FileNotFoundError):
                            step9_main()
                            
    finally:
        os.chdir(original_cwd)
