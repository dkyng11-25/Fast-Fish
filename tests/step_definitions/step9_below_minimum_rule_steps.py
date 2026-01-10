import pandas as pd
import numpy as np
import pytest
from pytest_bdd import scenario, given, when, then, parsers
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock
import os

# Import schemas for Pandera validation
from tests.validation_comprehensive.schemas.step9_schemas import (
    Step9ResultsSchema,
    Step9OpportunitiesSchema,
)

# Import the module under test
import src.step9_below_minimum_rule as step9_rule
import src.config as config_module

# Scenarios
@scenario('../features/step9_below_minimum_rule.feature', 'Successful SPU-level below minimum identification with positive quantity increases')
def test_successful_spu_below_minimum_positive_quantity_increases():
    pass

@scenario('../features/step9_below_minimum_rule.feature', 'Successful subcategory-level below minimum identification with count-based flags')
def test_successful_subcategory_below_minimum_count_based_flags():
    pass

@scenario('../features/step9_below_minimum_rule.feature', 'Rule 9 fails due to missing SPU sales quantity file')
def test_rule9_fails_missing_spu_sales_quantity_file():
    pass

@scenario('../features/step9_below_minimum_rule.feature', 'Rule 9 fails due to missing required quantity column in SPU sales data')
def test_rule9_fails_missing_quantity_column_in_spu_sales_data():
    pass

@scenario('../features/step9_below_minimum_rule.feature', 'No opportunities identified when no SPUs are below minimum threshold')
def test_no_opportunities_identified_no_spus_below_minimum_threshold():
    pass

@scenario('../features/step9_below_minimum_rule.feature', 'Rule 9 fails due to missing spu_code in SPU sales data')
def test_rule9_fails_missing_spu_code():
    pass

@scenario('../features/step9_below_minimum_rule.feature', 'No opportunities identified in SPU mode when all SPUs are above minimum threshold (no valid SPU expansion)')
def test_no_opportunities_identified_in_spu_mode_all_above_minimum():
    pass

@scenario('../features/step9_below_minimum_rule.feature', 'Subcategory mode identifies below minimums but generates no unit increases without real unit data')
def test_subcategory_mode_no_unit_increases_without_real_unit_data():
    pass

# Fixtures (reusing from step8 with modifications if needed)
@pytest.fixture
def mock_config():
    with patch('src.config.get_current_period') as mock_get_current_period, \
         patch('src.config.get_period_label') as mock_get_period_label, \
         patch('src.config.get_api_data_files') as mock_get_api_data_files, \
         patch('src.config.get_output_files') as mock_get_output_files:
        yield {
            "get_current_period": mock_get_current_period,
            "get_period_label": mock_get_period_label,
            "get_api_data_files": mock_get_api_data_files,
            "get_output_files": mock_get_output_files
        }

@pytest.fixture
def mock_filesystem():
    _mock_dataframes = {}
    
    def mock_read_csv(filepath, **kwargs):
        if filepath in _mock_dataframes:
            return _mock_dataframes[filepath]
        return pd.DataFrame()

    def mock_to_csv(df, filepath, **kwargs):
        _mock_dataframes[filepath] = df.copy()

    def mock_exists(filepath):
        return filepath in _mock_dataframes

    def mock_open(filepath, mode='r', encoding=None):
        if 'w' in mode or 'a' in mode:
            # For write modes, capture content
            mock_file = MagicMock()
            def write_side_effect(content):
                _mock_dataframes[filepath] = content
            mock_file.write.side_effect = write_side_effect
            return mock_file
        elif 'r' in mode:
            # For read modes, return content if available
            if filepath in _mock_dataframes:
                mock_file = MagicMock()
                mock_file.read.return_value = _mock_dataframes[filepath]
                return mock_file
            else:
                raise FileNotFoundError(f"Mock file not found: {filepath}")
        return MagicMock()

    with patch("pandas.read_csv", side_effect=mock_read_csv) as mock_read_csv_obj, \
         patch("pandas.DataFrame.to_csv", side_effect=mock_to_csv) as mock_to_csv_obj, \
         patch("os.path.exists") as mock_exists_obj, \
         patch("builtins.open", side_effect=mock_open) as mock_open_obj:
        
        mock_exists_obj.side_effect = mock_exists # Set the initial side effect
        yield {
            "exists": mock_exists_obj, # Pass the MagicMock object
            "read_csv": mock_read_csv,
            "to_csv": mock_to_csv,
            "open": mock_open_obj,
            "_data": _mock_dataframes,
            "_file_contents": {}  # Add missing key for markdown file content
        }

@pytest.fixture
def mock_sell_through_validator():
    with patch('src.sell_through_validator.SellThroughValidator') as mock_validator_class:
        mock_validator_instance = MagicMock()
        mock_validator_instance.is_initialized = True
        mock_validator_instance.predict_sell_through.return_value = pd.Series(0.8, index=[f'S{i:03d}' for i in range(100)])
        mock_validator_instance.check_compliance.return_value = pd.Series(True, index=[f'S{i:03d}' for i in range(100)])
        mock_validator_class.return_value = mock_validator_instance
        yield {
            "class": mock_validator_class,
            "instance": mock_validator_instance
        }

@pytest.fixture
def context():
    return {}

# Helper function to generate mock SPU sales data
def _generate_spu_sales_data(context, num_stores, num_spus, include_quantity=True, include_spu_code=True, all_spus_above_min=False):
    data = {
        'str_code': [f'S{i:03d}' for i in range(num_stores) for _ in range(num_spus)],
        'spu_sales_amt': np.random.rand(num_stores * num_spus) * 1000
    }
    if include_spu_code:
        data['spu_code'] = [f'SPU{j%20}' for i in range(num_stores) for j in range(num_spus)]
    if include_quantity:
        min_qty = 2 if all_spus_above_min else 1
        max_qty = 20
        data['quantity'] = np.random.randint(min_qty, max_qty, num_stores * num_spus)
    return pd.DataFrame(data)

# Given steps
@given(parsers.parse('the analysis level is "{analysis_level}"'))
def set_analysis_level(context, analysis_level):
    context["analysis_level"] = analysis_level
    os.environ["ANALYSIS_LEVEL"] = analysis_level
    context["original_analysis_level"] = os.environ.get("ANALYSIS_LEVEL")

@given(parsers.parse('a current period of "{period}" is set'))
def set_current_period(context, period, mock_config):
    context["period"] = period
    # The mock_src_config fixture handles CURRENT_PERIOD_LABEL
    mock_config["get_current_period"].return_value = (context["period"][:6], context["period"])
    mock_config["get_period_label"].return_value = context["period"]

@given(parsers.parse('clustering results with "{str_col}" and "{cluster_col}" are available'))
def clustering_results_available(context, mock_config, mock_filesystem, str_col, cluster_col):
    df_clustering = pd.DataFrame({
        str_col: [f'S{i:03d}' for i in range(100)],
        cluster_col: [f'C{i%5}' for i in range(100)],
        'Cluster': [f'C{i%5}' for i in range(100)] # Ensure both forms are present for step9
    })
    clustering_path = f"output/clustering_results_{context['analysis_level']}_{context['period']}.csv"
    mock_filesystem["_data"][clustering_path] = df_clustering
    mock_filesystem["_data"]["output/clustering_results.csv"] = df_clustering
    mock_filesystem["_data"]["output/enhanced_clustering_results.csv"] = df_clustering
    

    mock_config["get_output_files"].return_value = {
        'clustering_results': clustering_path
    }
    context["df_clustering"] = df_clustering

@given(parsers.parse('store config data with "{str_col}" is available'))
def store_config_data_available(context, mock_config, mock_filesystem, str_col):
    """Store configuration data with SPU sales information for below-minimum analysis."""
    # Create store config data that will trigger below-minimum cases
    # The step processes sty_sal_amt JSON data and expands it into SPU records
    sty_sal_amt_data = []
    for i in range(100):
        spu_sales = {}
        # Create SPU sales data where some stores have below-minimum quantities
        for j in range(3):  # 3 SPUs per store
            spu_code = f"SPU{j:03d}"
            if i < 30:  # First 30 stores have below-minimum quantities
                # These will trigger below-minimum logic (quantities < MINIMUM_UNIT_RATE)
                quantity = 0.05 + (j * 0.01)  # 0.05, 0.06, 0.07 (all below 1.0)
            else:  # Rest have normal quantities
                quantity = 2.0 + i + j  # Above minimum threshold
            spu_sales[spu_code] = round(quantity, 2)
        
        import json
        sty_sal_amt_data.append(json.dumps(spu_sales))
    
    df_config = pd.DataFrame({
        str_col: [f'S{i:03d}' for i in range(100)],
        'store_name': [f'Store {i}' for i in range(100)],
        'big_class_name': ['Clothing'] * 100,
        'sub_cate_name': ['Shirts'] * 50 + ['Pants'] * 50,
        'target_sty_cnt_avg': np.random.randint(5, 20, 100),
        'sty_sal_amt': sty_sal_amt_data
    })
    
    config_path = f"data/api_data/store_config_{context['period']}.csv"
    mock_filesystem["_data"][config_path] = df_config
    
    mock_config["get_api_data_files"].return_value = {
        'store_config': config_path
    }
    context["df_config"] = df_config

@given(parsers.parse('SPU sales data with "{str_col}", "{spu_col}", "{qty_col}" is available'))
def spu_sales_data_available_generic(context, mock_config, mock_filesystem, str_col, spu_col, qty_col):
    """SPU sales data for below-minimum analysis - simplified for black box testing."""
    # Create SPU sales data that matches the store config data
    # The step will primarily use the store config data, but this provides fallback
    df_sales = pd.DataFrame({
        str_col: [f'S{i:03d}' for i in range(100) for _ in range(3)],
        spu_col: [f'SPU{j:03d}' for i in range(100) for j in range(3)],
        qty_col: [0.05 + (i % 10) * 0.01 for i in range(300)],  # Below minimum quantities
        'spu_sales_amt': [100.0 + i for i in range(300)]
    })
    
    sales_path = f"data/api_data/complete_spu_sales_{context['period']}.csv"
    mock_filesystem["_data"][sales_path] = df_sales
    
    mock_config["get_api_data_files"].return_value.update({
        'spu_sales': sales_path,
        'store_sales': sales_path
    })
    context["df_sales"] = df_sales

@given(parsers.parse('SPU sales data with "{str_col}", "{spu_col}", "{qty_col}" is available (for unit mapping)'))
def spu_sales_data_available_for_unit_mapping(context, mock_config, mock_filesystem, str_col, spu_col, qty_col):
    # This calls the generic version
    spu_sales_data_available_generic(context, mock_config, mock_filesystem, str_col, spu_col, qty_col)

@given(parsers.parse('SPU sales data with "{str_col}", "{spu_col}", "{qty_col}" is available'))
def spu_sales_data_available(context, mock_config, mock_filesystem, str_col, spu_col, qty_col):
    # Re-adding the original generic step definition
    spu_sales_data_available_generic(context, mock_config, mock_filesystem, str_col, spu_col, qty_col)

@given('SPU sales data file is missing')
def spu_sales_data_file_is_missing(context, mock_filesystem):
    sales_path = f"data/api_data/complete_spu_sales_{context['period']}.csv"
    if sales_path in mock_filesystem["_data"]:
        del mock_filesystem["_data"][sales_path]

@given(parsers.parse('minimum unit rate is "{min_unit_rate}" units per 15 days'))
def minimum_unit_rate_set(context, min_unit_rate):
    context["MINIMUM_UNIT_RATE"] = str(min_unit_rate)

@given(parsers.parse('minimum boost quantity is "{min_boost_qty}"'))
def minimum_boost_quantity_set(context, min_boost_qty):
    context["MIN_BOOST_QUANTITY"] = str(min_boost_qty)

@given('the rule is configured to never decrease below minimum')
def rule_never_decrease_below_minimum(context):
    context["NEVER_DECREASE_BELOW_MINIMUM"] = 'True'

@given('Fast Fish validation is available')
def fast_fish_validation_is_available(context, mock_sell_through_validator):
    # This fixture already ensures the validator is available and initialized by default
    assert mock_sell_through_validator["instance"].is_initialized is True

@given('seasonal blending is disabled')
def seasonal_blending_is_disabled(context):
    context['RECENT_MONTHS_BACK'] = '0'

@given('clustering results file is missing')
def clustering_results_file_is_missing(context, mock_filesystem):
    clustering_path_base = f"output/clustering_results_{context['analysis_level']}_{context['period']}.csv"
    clustering_path_compat = "output/clustering_results.csv"
    clustering_path_enhanced = "output/enhanced_clustering_results.csv"

    for path_to_remove in [clustering_path_base, clustering_path_compat, clustering_path_enhanced]:
        if path_to_remove in mock_filesystem["_data"]: # Remove it if it was added by a previous step
            del mock_filesystem["_data"][path_to_remove]
    mock_filesystem["exists"].side_effect = lambda path: path not in (
        clustering_path_base, clustering_path_compat, clustering_path_enhanced
    ) and mock_filesystem["original_exists"](path) # Ensure to use original_exists as fallback

@given(parsers.parse('SPU sales data with "{missing_col}" column is missing'))
def spu_sales_data_missing_column(context, mock_config, mock_filesystem, missing_col):
    df_sales_incomplete = pd.DataFrame({
        'str_code': [f'S{i:03d}' for i in range(100)],
        'spu_code': [f'SPU{i%20}' for i in range(100)] if missing_col != 'spu_code' else [], # Exclude spu_code if it's the missing column
        'other_qty_col': np.random.randint(1, 20, 100) # Missing the expected quantity column
    })
    if missing_col != 'quantity': # Add quantity if it's not the missing column
        df_sales_incomplete['quantity'] = np.random.randint(1, 20, 100)

    sales_path = f"data/api_data/complete_spu_sales_{context['period']}.csv"
    mock_filesystem["_data"][sales_path] = df_sales_incomplete
    
    mock_config["get_api_data_files"].return_value.update({
        'spu_sales': sales_path,
        'store_sales': sales_path
    })
    context["df_sales_incomplete"] = df_sales_incomplete

@given(parsers.parse('SPU sales data is available but "spu_code" column is missing'))
def spu_sales_data_missing_spu_code_column(context, mock_config, mock_filesystem):
    df_sales_no_spu_code = _generate_spu_sales_data(context, 100, 3, include_spu_code=False, include_quantity=True)
    sales_path = f"data/api_data/complete_spu_sales_{context['period']}.csv"
    mock_filesystem["_data"][sales_path] = df_sales_no_spu_code
    mock_filesystem["exists"].side_effect = lambda path: path in mock_filesystem["_data"] or mock_filesystem["original_exists"](path)

    mock_config["get_api_data_files"].return_value.update({
        'spu_sales': sales_path,
        'store_sales': sales_path
    })
    context["df_sales_no_spu_code"] = df_sales_no_spu_code

@given(parsers.parse('SPU sales data with all SPUs above minimum threshold is available'))
def spu_sales_data_all_above_minimum(context, mock_config, mock_filesystem):
    df_sales = _generate_spu_sales_data(context, 100, 3, all_spus_above_min=True)
    sales_path = f"data/api_data/complete_spu_sales_{context['period']}.csv"
    mock_filesystem["_data"][sales_path] = df_sales
    mock_filesystem["exists"].side_effect = lambda path: path in mock_filesystem["_data"] or mock_filesystem["original_exists"](path)

    mock_config["get_api_data_files"].return_value.update({
        'spu_sales': sales_path,
        'store_sales': sales_path
    })
    context["df_sales_above_min"] = df_sales

@given(parsers.parse('SPU sales data is available but missing quantity column (no real unit data for subcategory mapping)'))
def spu_sales_data_missing_quantity_for_subcategory_mapping(context, mock_config, mock_filesystem):
    df_sales_no_qty_subcat = _generate_spu_sales_data(context, 100, 3, include_quantity=False)
    sales_path = f"data/api_data/complete_spu_sales_{context['period']}.csv"
    mock_filesystem["_data"][sales_path] = df_sales_no_qty_subcat
    mock_filesystem["exists"].side_effect = lambda path: path in mock_filesystem["_data"] or mock_filesystem["original_exists"](path)

    mock_config["get_api_data_files"].return_value.update({
        'spu_sales': sales_path,
        'store_sales': sales_path
    })
    context["df_sales_no_qty_subcat"] = df_sales_no_qty_subcat

@given(parsers.parse('SPU sales data is available but "{missing_col}" column is missing'))
def spu_sales_data_available_but_column_missing(context, mock_config, mock_filesystem, missing_col):
    """SPU sales data available but specific column is missing."""
    # Create base data with all columns
    base_data = {
        'str_code': [f'S{i:03d}' for i in range(100)],
        'spu_code': [f'SPU{i%20}' for i in range(100)],
        'quantity': [10 + i for i in range(100)]
    }
    
    # Remove the missing column
    if missing_col in base_data:
        del base_data[missing_col]
    
    df_sales_incomplete = pd.DataFrame(base_data)
    
    sales_path = f"data/api_data/complete_spu_sales_{context['period']}.csv"
    mock_filesystem["_data"][sales_path] = df_sales_incomplete
    mock_filesystem["exists"].side_effect = lambda path: path in mock_filesystem["_data"] or mock_filesystem["original_exists"](path)

    mock_config["get_api_data_files"].return_value.update({
        'spu_sales': sales_path,
        'store_sales': sales_path
    })
    context["spu_sales_data"] = df_sales_incomplete

# When steps
@when('Rule 9 is executed')
def rule9_is_executed(context, mock_config, mock_filesystem, mock_sell_through_validator):
    context["exception"] = None
    try:
        # Patching the environment variables with values from context
        with patch.dict('os.environ', {
            "ANALYSIS_LEVEL": context.get("analysis_level", "spu"),
            "MINIMUM_UNIT_RATE": context.get("MINIMUM_UNIT_RATE", "1.0"),
            "MIN_BOOST_QUANTITY": context.get("MIN_BOOST_QUANTITY", "0.5"),
            "NEVER_DECREASE_BELOW_MINIMUM": context.get("NEVER_DECREASE_BELOW_MINIMUM", "False"),
            "RECENT_MONTHS_BACK": context.get("RECENT_MONTHS_BACK", "3"),
        }, clear=False): # clear=False to not remove existing env vars
            with patch('src.step9_below_minimum_rule.get_current_period', new=mock_config['get_current_period']), \
                 patch('src.step9_below_minimum_rule.get_period_label', new=mock_config['get_period_label']), \
                 patch('src.step9_below_minimum_rule.get_api_data_files', new=mock_config['get_api_data_files']), \
                 patch('src.step9_below_minimum_rule.get_output_files', new=mock_config['get_output_files']), \
                 patch('src.step9_below_minimum_rule.pd.read_csv', new=mock_filesystem['read_csv']), \
                 patch('src.step9_below_minimum_rule.os.path.exists', new=mock_filesystem['exists']), \
                 patch('src.step9_below_minimum_rule.SellThroughValidator', new=mock_sell_through_validator['class']), \
                 patch('src.step9_below_minimum_rule.os.makedirs', MagicMock(return_value=None)), \
                 patch('src.step9_below_minimum_rule.pd.DataFrame.to_csv', new=mock_filesystem['to_csv']) as to_csv_mock, \
                 patch('builtins.open', new=mock_filesystem["open"]) as open_mock:
                
                # Configure the to_csv mock to store dataframes
                to_csv_mock.side_effect = lambda df, path, **kwargs: mock_filesystem["_data"].__setitem__(path, df.copy())
                # Configure the open mock for markdown files
                open_mock.side_effect = mock_filesystem["open"].side_effect
                
                # Import and execute the step
                from src.step9_below_minimum_rule import main as step9_main
                step9_main()
    except Exception as e:
        context["exception"] = e
    finally:
        pass

# Then steps
@then('below minimum SPU opportunities should be identified')
def below_minimum_spu_opportunities_identified(context, mock_filesystem, get_dataframe_from_mocked_to_csv):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule9_below_minimum_{context['analysis_level']}_sellthrough_opportunities_{context['period']}.csv")
    assert opportunities_df is not None, "Opportunities CSV was not generated."
    assert not opportunities_df.empty, "Opportunities DataFrame is empty."
    Step9OpportunitiesSchema.validate(opportunities_df)

@then('store-level results should be generated with positive quantity increases')
def store_level_results_generated_positive_qty_increases(context, mock_filesystem, get_dataframe_from_mocked_to_csv):
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule9_below_minimum_{context['analysis_level']}_sellthrough_results_{context['period']}.csv")
    assert results_df is not None, "Results CSV was not generated."
    assert not results_df.empty, "Results DataFrame is empty."
    assert 'total_increase_needed' in results_df.columns, "'total_increase_needed' column missing."
    assert (results_df['total_increase_needed'] > 0).any(), "No positive quantity increases found."
    Step9ResultsSchema.validate(results_df)

@then('detailed opportunities should be generated and be Fast Fish compliant')
def detailed_opportunities_generated_and_fast_fish_compliant(context, mock_filesystem, get_dataframe_from_mocked_to_csv):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule9_below_minimum_{context['analysis_level']}_sellthrough_opportunities_{context['period']}.csv")
    assert opportunities_df is not None, "Detailed opportunities CSV was not generated."
    assert not opportunities_df.empty, "Detailed opportunities DataFrame is empty."
    assert 'fast_fish_compliant' in opportunities_df.columns, "'fast_fish_compliant' column missing."
    assert opportunities_df['fast_fish_compliant'].any(), "No Fast Fish compliant opportunities found."
    Step9OpportunitiesSchema.validate(opportunities_df)

@then('a summary report should be created')
def summary_report_created(context, mock_filesystem):
    summary_file_path = f"output/rule9_below_minimum_{context['analysis_level']}_sellthrough_summary_{context['period']}.md"
    assert summary_file_path in mock_filesystem["_file_contents"], "Summary markdown report was not created."

@then(parsers.parse('the output dataframes should conform to "{schema1}" and "{schema2}"'))
def output_dataframes_conform_to_schemas(context, mock_filesystem, schema1, schema2, get_dataframe_from_mocked_to_csv):
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule9_below_minimum_{context['analysis_level']}_sellthrough_results_{context['period']}.csv")
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule9_below_minimum_{context['analysis_level']}_sellthrough_opportunities_{context['period']}.csv")

    assert results_df is not None, f"Could not find results dataframe for schema {schema1}"
    assert opportunities_df is not None, f"Could not find opportunities dataframe for schema {schema2}"

    results_schema_class = globals()[schema1]
    opportunities_schema_class = globals()[schema2]

    results_schema_class.validate(results_df)
    opportunities_schema_class.validate(opportunities_df)

@then('below minimum subcategory cases should be identified with count-based flags')
def below_minimum_subcategory_cases_identified_count_based_flags(context, mock_filesystem, get_dataframe_from_mocked_to_csv):
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule9_below_minimum_{context['analysis_level']}_sellthrough_results_{context['period']}.csv")
    assert results_df is not None, "Results CSV was not generated."
    assert not results_df.empty, "Results DataFrame is empty."
    assert 'below_minimum_spus_count' in results_df.columns, "Expected count-based flags (e.g., below_minimum_spus_count) missing."
    Step9ResultsSchema.validate(results_df)

@then('store-level results should be generated with count-based metrics')
def store_level_results_generated_count_based_metrics(context, mock_filesystem, get_dataframe_from_mocked_to_csv):
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule9_below_minimum_{context['analysis_level']}_sellthrough_results_{context['period']}.csv")
    assert results_df is not None, "Results CSV was not generated."
    assert not results_df.empty, "Results DataFrame is empty."
    assert 'total_quantity_needed' not in results_df.columns or (results_df['total_quantity_needed'].isnull().all()), \
        "Expected quantity fields to be omitted or null for count-based metrics."
    Step9ResultsSchema.validate(results_df)

@then('detailed opportunities should be generated for subcategories (if unit mapping is present)')
def detailed_opportunities_generated_for_subcategories(context, mock_filesystem, get_dataframe_from_mocked_to_csv):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule9_below_minimum_{context['analysis_level']}_sellthrough_opportunities_{context['period']}.csv")
    # This assertion needs to be conditional based on whether unit mapping was expected
    # For this scenario, assuming it might be empty or contain subcategory names
    if opportunities_df is not None and not opportunities_df.empty:
        assert 'sub_cate_name' in opportunities_df.columns or 'spu_code' in opportunities_df.columns
        Step9OpportunitiesSchema.validate(opportunities_df)
    else:
        # It's acceptable for it to be empty if no unit mapping or opportunities were found
        pass

@then(parsers.parse('Rule 9 execution should fail with a "{error_type}"'))
def rule9_execution_should_fail_with_error(context, error_type):
    assert context["exception"] is not None, "Expected an exception but none was raised."
    assert context["exception"].__class__.__name__ == error_type, \
        f"Expected exception type {error_type}, but got {context['exception'].__class__.__name__}"

@then(parsers.parse('an error message indicating the missing SPU sales file should be displayed'))
def error_message_missing_spu_sales_file(context):
    assert "FileNotFoundError" in str(context["exception"]) and "complete_spu_sales" in str(context["exception"]), \
           f"Expected missing SPU sales file error message, got: {context['exception']}"

@then(parsers.parse('an error message indicating the missing quantity column should be displayed'))
def error_message_missing_quantity_column(context):
    assert "KeyError" in str(context["exception"]) and ("quantity" in str(context["exception"]) or "spu_code" in str(context["exception"])), \
           f"Expected missing quantity or spu_code column error message, got: {context['exception']}"

@then(parsers.parse('an error message indicating the missing "spu_code" column should be displayed'))
def error_message_missing_spu_code_column(context):
    exception_message = str(context["exception"])
    assert "KeyError" in exception_message or "spu_code" in exception_message, \
           f"Expected missing spu_code column error message, got: {exception_message}"

@then('store-level results should be generated with zero below minimum SPU count')
def store_level_results_zero_below_minimum_spu_count(context, mock_filesystem, get_dataframe_from_mocked_to_csv):
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule9_below_minimum_{context['analysis_level']}_sellthrough_results_{context['period']}.csv")
    assert results_df is not None, "Results CSV was not generated."
    assert 'below_minimum_spus_count' in results_df.columns, "'below_minimum_spus_count' column missing."
    assert (results_df['below_minimum_spus_count'] == 0).all(), "Expected all below minimum SPU counts to be zero."
    Step9ResultsSchema.validate(results_df)

@then('detailed opportunities should be empty')
def detailed_opportunities_should_be_empty(context, mock_filesystem, get_dataframe_from_mocked_to_csv):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule9_below_minimum_{context['analysis_level']}_sellthrough_opportunities_{context['period']}.csv")
    assert opportunities_df is None or opportunities_df.empty, "Expected detailed opportunities to be empty."

@then('the summary report should indicate no below minimum opportunities were found')
def summary_report_no_below_minimum_opportunities_found(context, mock_filesystem):
    summary_file_path = f"output/rule9_below_minimum_{context['analysis_level']}_sellthrough_summary_{context['period']}.md"
    assert summary_file_path in mock_filesystem["_file_contents"], "Summary markdown report was not created."
    summary_content = mock_filesystem["_file_contents"][summary_file_path]
    assert "No below minimum opportunities were found" in str(summary_content) or \
           "Total Below Minimum SPUs: 0" in str(summary_content), \
           f"Summary report did not indicate no below minimum opportunities. Content: {summary_content}"

@then('detailed opportunities should be generated for subcategories but with no quantity increases')
def detailed_opportunities_generated_for_subcategories_no_quantity_increases(context, mock_filesystem, get_dataframe_from_mocked_to_csv):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule9_below_minimum_{context['analysis_level']}_sellthrough_opportunities_{context['period']}.csv")
    assert opportunities_df is not None, "Detailed opportunities CSV was not generated."
    assert not opportunities_df.empty, "Detailed opportunities DataFrame is empty."
    assert 'recommended_quantity_change' in opportunities_df.columns, "'recommended_quantity_change' column missing."
    assert (opportunities_df['recommended_quantity_change'].isnull().all() | (opportunities_df['recommended_quantity_change'] == 0).all()), \
        "Expected all quantity changes to be null or zero due to missing real unit data for subcategory mapping."
    Step9OpportunitiesSchema.validate(opportunities_df)
