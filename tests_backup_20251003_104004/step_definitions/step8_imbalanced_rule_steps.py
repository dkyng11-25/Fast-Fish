import pandas as pd
import numpy as np
import pytest
from pytest_bdd import scenario, given, when, then, parsers
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock
import os

# Import schemas for Pandera validation
from tests.validation_comprehensive.schemas.step8_schemas import (
    Step8InputClusteringSchema,
    Step8InputStoreConfigSchema,
    Step8InputQuantitySchema,
    Step8ResultsSchema,
    Step8CasesSchema,
    Step8ZScoreAnalysisSchema
)

# Import the module under test
import src.step8_imbalanced_rule as step8_rule
import src.config as config_module

# Scenarios
@scenario('../features/step8_imbalanced_rule.feature', 'Successful SPU-level quantity rebalancing with Z-score threshold')
def test_successful_spu_rebalancing():
    pass

@scenario('../features/step8_imbalanced_rule.feature', 'Successful subcategory-level quantity rebalancing without seasonal blending')
def test_successful_subcategory_rebalancing_no_seasonal_blending():
    pass

@scenario('../features/step8_imbalanced_rule.feature', 'Rule 8 fails due to missing clustering results file')
def test_rule8_fails_missing_clustering_file():
    pass

@scenario('../features/step8_imbalanced_rule.feature', 'Rule 8 fails due to missing required quantity columns')
def test_rule8_fails_missing_quantity_columns():
    pass

@scenario('../features/step8_imbalanced_rule.feature', 'No rebalancing recommendations when no valid Z-score groups are found')
def test_no_rebalancing_recommendations_no_valid_z_score_groups():
    pass

# Fixtures
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

# Given steps
@given(parsers.parse('the analysis level is "{analysis_level}"'))
def set_analysis_level(context, analysis_level):
    context["analysis_level"] = analysis_level
    # Set environment variable for analysis level if needed by step8 (e.g., for thresholds)
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
        'Cluster': [f'C{i%5}' for i in range(100)] # Ensure both forms are present for step8
    })
    clustering_path = f"output/clustering_results_{context['analysis_level']}_{context['period']}.csv"
    mock_filesystem["_data"][clustering_path] = df_clustering
    mock_filesystem["_data"]["output/clustering_results.csv"] = df_clustering # backward compatibility
    mock_filesystem["_data"]["output/enhanced_clustering_results.csv"] = df_clustering # enhanced path
    

    mock_config["get_output_files"].return_value = {
        'clustering_results': clustering_path
    }
    context["df_clustering"] = df_clustering

@given(parsers.parse('store config data with "{str_col}" is available'))
def store_config_data_available(context, mock_config, mock_filesystem, str_col):
    # Generate comprehensive store config data with all required columns for both subcategory and SPU analysis
    n_stores = 100
    df_config = pd.DataFrame({
        str_col: [f'S{i:03d}' for i in range(n_stores)],
        'store_name': [f'Store {i}' for i in range(n_stores)],
        'region': [f'Region {i%3}' for i in range(n_stores)],
        'target_sty_cnt_avg': np.random.randint(5, 20, n_stores), # For subcategory analysis
        # Required columns for SPU analysis
        'sty_sal_amt': np.random.rand(n_stores) * 1000,  # Sales amount per store
        'season_name': np.random.choice(['Spring', 'Summer', 'Fall', 'Winter'], n_stores),
        'sex_name': np.random.choice(['Men', 'Women', 'Unisex'], n_stores),
        'display_location_name': np.random.choice(['Front', 'Back', 'Center', 'Side'], n_stores),
        'big_class_name': np.random.choice(['Apparel', 'Accessories', 'Footwear', 'Home'], n_stores),
        'sub_cate_name': np.random.choice(['Tops', 'Bottoms', 'Dresses', 'Shoes', 'Bags'], n_stores)
    })
    config_path = f"data/api_data/store_config_{context['period']}.csv"
    mock_filesystem["_data"][config_path] = df_config
    
    mock_config["get_api_data_files"].return_value = {
        'store_config': config_path
    }
    context["df_config"] = df_config

@given(parsers.parse('SPU quantity data with "{str_col}", "{spu_col}", "{qty_col}" is available'))
def spu_quantity_data_available(context, mock_config, mock_filesystem, str_col, spu_col, qty_col):
    df_qty = pd.DataFrame({
        str_col: [f'S{i:03d}' for i in range(100) for _ in range(3)], # Multiple SPUs per store
        spu_col: [f'SPU{j%20}' for i in range(100) for j in range(3)],
        qty_col: np.random.randint(1, 20, 300), # Quantity values
        'spu_sales_amt': np.random.rand(300) * 1000, # Also needed for SPU path
        'base_sal_qty': np.random.randint(1, 15, 300),
        'fashion_sal_qty': np.random.randint(0, 5, 300),
        'sal_qty': np.random.randint(1, 20, 300)
    })
    qty_path = f"data/api_data/complete_spu_sales_{context['period']}.csv"
    mock_filesystem["_data"][qty_path] = df_qty
    
    mock_config["get_api_data_files"].return_value.update({
        'spu_sales': qty_path, # Path for spu sales
        'store_sales': qty_path # Path for store sales (for quantity derivation)
    })
    context["df_quantity"] = df_qty

@given(parsers.parse('subcategory quantity data with "{str_col}", "{sub_cate_col}", "{qty_col}" is available'))
def subcategory_quantity_data_available(context, mock_config, mock_filesystem, str_col, sub_cate_col, qty_col):
    df_qty = pd.DataFrame({
        str_col: [f'S{i:03d}' for i in range(100) for _ in range(2)],
        sub_cate_col: [f'SubCat{j%10}' for i in range(100) for j in range(2)],
        qty_col: np.random.randint(5, 50, 200),
        'sal_amt': np.random.rand(200) * 500
    })
    qty_path = f"data/api_data/complete_category_sales_{context['period']}.csv"
    mock_filesystem["_data"][qty_path] = df_qty
    
    mock_config["get_api_data_files"].return_value.update({
        'category_sales': qty_path, # Path for category sales
        'store_sales': qty_path # Path for store sales (for quantity derivation)
    })
    context["df_quantity"] = df_qty

@given(parsers.parse('the Z-score threshold for SPU is "{z_threshold}"'))
def spu_z_score_threshold_set(context, z_threshold):
    context["Z_SCORE_THRESHOLD_SPU"] = str(z_threshold)

@given(parsers.parse('the Z-score threshold for subcategory is "{z_threshold}"'))
def subcategory_z_score_threshold_set(context, z_threshold):
    context["Z_SCORE_THRESHOLD_SUBCATEGORY"] = str(z_threshold)

@given(parsers.parse('rebalance mode is "{rebalance_mode}"'))
def rebalance_mode_set(context, rebalance_mode):
    context["REBALANCE_MODE"] = rebalance_mode

@given('seasonal blending is disabled for quantity data')
def seasonal_blending_disabled_for_quantity_data(context):
    context['RECENT_MONTHS_BACK'] = '0'

@given('clustering results file is missing')
def clustering_results_file_is_missing(context, mock_filesystem):
    clustering_path_base = f"output/clustering_results_{context['analysis_level']}_{context['period']}.csv"
    clustering_path_compat = "output/clustering_results.csv"
    clustering_path_enhanced = "output/enhanced_clustering_results.csv"

    for path_to_remove in [clustering_path_base, clustering_path_compat, clustering_path_enhanced]:
        if path_to_remove in mock_filesystem["_data"]: # Remove it if it was added by a previous step
            del mock_filesystem["_data"][path_to_remove]

@given(parsers.parse('SPU quantity data is available but "{missing_col}" column is missing'))
def spu_quantity_data_missing_column(context, mock_config, mock_filesystem, missing_col):
    df_qty_incomplete = pd.DataFrame({
        'str_code': [f'S{i:03d}' for i in range(100)],
        'spu_code': [f'SPU{i%20}' for i in range(100)],
        'other_qty_col': np.random.randint(1, 20, 100)
    })
    qty_path = f"data/api_data/complete_spu_sales_{context['period']}.csv"
    mock_filesystem["_data"][qty_path] = df_qty_incomplete
    
    mock_config["get_api_data_files"].return_value.update({
        'spu_sales': qty_path,
        'store_sales': qty_path
    })
    context["df_quantity_incomplete"] = df_qty_incomplete

@given(parsers.parse('SPU sales data is available but missing all quantity sources'))
def spu_sales_data_missing_all_quantity_sources(context, mock_config, mock_filesystem):
    num_stores = 5
    num_spus = 3
    # Generate sales data with sales_amt but no quantity columns
    df_sales_no_qty = _generate_spu_sales_data(context, num_stores, num_spus, include_quantity=False, all_qty_missing=True)
    sales_path = f"data/api_data/complete_spu_sales_{context['period']}.csv"
    mock_filesystem["_data"][sales_path] = df_sales_no_qty
    
    mock_config["get_api_data_files"].return_value.update({
        'spu_sales': sales_path,
        'store_sales': sales_path
    })
    context["df_sales_no_qty_sources"] = df_sales_no_qty

@given(parsers.parse('Fast Fish validation is available but rejects some opportunities'))
def fast_fish_validation_rejects_some_opportunities(context, mock_sell_through_validator):
    context["SKIP_SELLTHROUGH_VALIDATION"] = '0' # Ensure validation is NOT skipped
    
    # Simulate some opportunities being rejected by the validator
    # This might require some knowledge of how many opportunities are generated
    # For now, let's assume 100 entries and reject a few randomly
    compliance_series = pd.Series(np.random.choice([True, False], size=100, p=[0.7, 0.3]), index=[f'S{i:03d}' for i in range(100)])
    mock_sell_through_validator["instance"].check_compliance.return_value = compliance_series

@given('all clusters are too small to form valid Z-score groups')
def all_clusters_too_small_for_z_score(context, mock_config, mock_filesystem):
    # Simulate small clusters by providing a small clustering_results dataframe
    df_clustering_small = pd.DataFrame({
        'str_code': [f'S{i:03d}' for i in range(5)], # Only 5 stores
        'cluster_id': [0, 0, 1, 1, 2],
        'Cluster': ['C0', 'C0', 'C1', 'C1', 'C2']
    })
    # Set MIN_CLUSTER_SIZE to a value larger than any cluster size here
    context["MIN_CLUSTER_SIZE_SPU"] = '10' # Assuming SPU level for this scenario
    clustering_path = f"output/clustering_results_{context['analysis_level']}_{context['period']}.csv"
    mock_filesystem["_data"][clustering_path] = df_clustering_small
    mock_config["get_output_files"].return_value['clustering_results'] = clustering_path
    context["df_clustering_small"] = df_clustering_small

# When steps
@when('Rule 8 is executed')
def rule8_is_executed(context, mock_config, mock_filesystem, mock_sell_through_validator):
    context["exception"] = None
    try:
        # Patching the environment variables with values from context
        with patch.dict('os.environ', {
            "ANALYSIS_LEVEL": context.get("analysis_level", "spu"),
            "Z_SCORE_THRESHOLD_SPU": context.get("Z_SCORE_THRESHOLD_SPU", "1.5"),
            "Z_SCORE_THRESHOLD_SUBCATEGORY": context.get("Z_SCORE_THRESHOLD_SUBCATEGORY", "1.5"),
            "REBALANCE_MODE": context.get("REBALANCE_MODE", "equal_distribution"),
            "RECENT_MONTHS_BACK": context.get("RECENT_MONTHS_BACK", "3"),
            "MIN_CLUSTER_SIZE_SPU": context.get("MIN_CLUSTER_SIZE_SPU", "2"),
            "SKIP_SELLTHROUGH_VALIDATION": context.get("SKIP_SELLTHROUGH_VALIDATION", "False"),
        }, clear=False): # clear=False to not remove existing env vars
            with patch('src.step8_imbalanced_rule.get_current_period', new=mock_config['get_current_period']), \
                 patch('src.step8_imbalanced_rule.get_period_label', new=mock_config['get_period_label']), \
                 patch('src.step8_imbalanced_rule.get_api_data_files', new=mock_config['get_api_data_files']), \
                 patch('src.step8_imbalanced_rule.get_output_files', new=mock_config['get_output_files']), \
                 patch('src.step8_imbalanced_rule.pd.read_csv', new=mock_filesystem['read_csv']), \
                 patch('src.step8_imbalanced_rule.os.path.exists', new=mock_filesystem['exists']), \
                 patch('src.step8_imbalanced_rule.SellThroughValidator', new=mock_sell_through_validator['class']), \
                 patch('src.step8_imbalanced_rule.os.makedirs', MagicMock(return_value=None)), \
                 patch('src.step8_imbalanced_rule.pd.DataFrame.to_csv', new=mock_filesystem['to_csv']) as to_csv_mock, \
                 patch('src.step8_imbalanced_rule.open', new=mock_filesystem["open"]) as open_mock:
                
                # Configure the to_csv mock to store dataframes
                to_csv_mock.side_effect = lambda df, path, **kwargs: mock_filesystem["_data"].__setitem__(path, df.copy())
                # Configure the open mock for markdown files
                open_mock.side_effect = mock_filesystem["open"].side_effect
                
                step8_rule.main()
    except Exception as e:
        context["exception"] = e
    finally:
        # The patch.dict context manager handles cleanup of os.environ
        pass

# Then steps
@then('imbalanced SPU cases should be identified')
def imbalanced_spu_cases_identified(context, mock_filesystem, get_dataframe_from_mocked_to_csv):
    imbalances_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule8_imbalanced_{context['analysis_level']}_imbalances_{context['period']}.csv")
    assert imbalances_df is not None, "Imbalances CSV was not generated."
    assert not imbalances_df.empty, "Imbalances DataFrame is empty."
    # Optional: validate schema
    Step8CasesSchema.validate(imbalances_df)

@then('store-level results should be generated with quantity adjustments')
def store_level_results_generated_with_adjustments(context, mock_filesystem, get_dataframe_from_mocked_to_csv):
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule8_imbalanced_{context['analysis_level']}_results_{context['period']}.csv")
    assert results_df is not None, "Results CSV was not generated."
    assert not results_df.empty, "Results DataFrame is empty."
    assert 'total_quantity_adjustment' in results_df.columns, "'total_quantity_adjustment' column missing in results."
    assert (results_df['total_quantity_adjustment'] != 0).any(), "No quantity adjustments found in results."
    # Optional: validate schema
    Step8ResultsSchema.validate(results_df)

@then('detailed imbalance cases should be generated')
def detailed_imbalance_cases_generated(context, mock_filesystem, get_dataframe_from_mocked_to_csv):
    imbalances_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule8_imbalanced_{context['analysis_level']}_imbalances_{context['period']}.csv")
    assert imbalances_df is not None, "Detailed imbalances CSV was not generated."
    assert not imbalances_df.empty, "Detailed imbalances DataFrame is empty."
    # Optional: validate schema (already done in imbalanced_spu_cases_identified for SPU)
    # For subcategory, it would be Step8SubcategoryImbalancesSchema

@then('a summary report should be created')
def summary_report_created(context, mock_filesystem):
    summary_file_path = f"output/rule8_imbalanced_{context['analysis_level']}_summary_{context['period']}.md"
    assert summary_file_path in mock_filesystem["_file_contents"], "Summary markdown report was not created."
    # Optionally, read and assert content of the markdown file

@then(parsers.parse('the output dataframes should conform to "{schema1}" and "{schema2}"'))
def output_dataframes_conform_to_schemas(context, mock_filesystem, schema1, schema2, get_dataframe_from_mocked_to_csv):
    # Retrieve the actual dataframes from the mock_filesystem
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule8_imbalanced_{context['analysis_level']}_results_{context['period']}.csv")
    imbalances_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule8_imbalanced_{context['analysis_level']}_imbalances_{context['period']}.csv")

    assert results_df is not None, f"Could not find results dataframe for schema {schema1}"
    assert imbalances_df is not None, f"Could not find imbalances dataframe for schema {schema2}"

    # Dynamically get schema classes
    results_schema_class = globals()[schema1]
    imbalances_schema_class = globals()[schema2]

    results_schema_class.validate(results_df)
    imbalances_schema_class.validate(imbalances_df)

@then('imbalanced subcategory cases should be identified')
def imbalanced_subcategory_cases_identified(context, mock_filesystem, get_dataframe_from_mocked_to_csv):
    imbalances_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule8_imbalanced_{context['analysis_level']}_imbalances_{context['period']}.csv")
    assert imbalances_df is not None, "Subcategory imbalances CSV was not generated."
    assert not imbalances_df.empty, "Subcategory imbalances DataFrame is empty."
    Step8ZScoreAnalysisSchema.validate(imbalances_df)

@then(parsers.parse('Rule 8 execution should fail with a "{error_type}"'))
def rule8_execution_should_fail_with_error(context, error_type):
    assert context["exception"] is not None, "Expected an exception but none was raised."
    assert context["exception"].__class__.__name__ == error_type, \
        f"Expected exception type {error_type}, but got {context['exception'].__class__.__name__}"

@then(parsers.parse('an error message indicating the missing clustering file should be displayed'))
def error_message_missing_clustering_file(context):
    exception_message = str(context["exception"])
    assert "FileNotFoundError" in exception_message or "Clustering results not found" in exception_message, \
           f"Expected missing clustering file error message, got: {exception_message}"

@then(parsers.parse('an error message indicating the missing quantity column should be displayed'))
def error_message_missing_quantity_column(context):
    exception_message = str(context["exception"])
    assert "ValueError" in exception_message and (
        "Missing required columns" in exception_message or 
        "Missing real quantity fields" in exception_message or
        "Quantity data missing" in exception_message
    ), f"Expected missing quantity column error message, got: {exception_message}"

@then(parsers.parse('an error message indicating missing quantity sources should be displayed'))
def error_message_missing_quantity_sources(context):
    assert "ValueError" in str(context["exception"]) and "No valid quantity column found" in str(context["exception"]), \
           f"Expected missing quantity sources error message, got: {context['exception']}"

@then('store-level results should be generated with zero total quantity adjustments')
def store_level_results_zero_total_quantity_adjustments(context, mock_filesystem, get_dataframe_from_mocked_to_csv):
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule8_imbalanced_{context['analysis_level']}_results_{context['period']}.csv")
    assert results_df is not None, "Results CSV was not generated."
    assert 'total_quantity_adjustment' in results_df.columns, "'total_quantity_adjustment' column missing in results."
    assert (results_df['total_quantity_adjustment'] == 0).all(), "Expected all quantity adjustments to be zero."
    Step8ResultsSchema.validate(results_df)

@then('detailed imbalance cases should be empty or contain no adjustments')
def detailed_imbalance_cases_empty_or_no_adjustments(context, mock_filesystem, get_dataframe_from_mocked_to_csv):
    imbalances_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule8_imbalanced_{context['analysis_level']}_imbalances_{context['period']}.csv")
    assert imbalances_df is None or imbalances_df.empty or (imbalances_df['quantity_adjustment'] == 0).all(), \
        "Expected detailed imbalance cases to be empty or have no adjustments."
    if imbalances_df is not None and not imbalances_df.empty:
        if context["analysis_level"] == "spu":
            Step8CasesSchema.validate(imbalances_df)
        else:
            Step8ZScoreAnalysisSchema.validate(imbalances_df)

@then('the summary report should indicate no valid Z-score groups were found')
def summary_report_no_valid_z_score_groups(context, mock_filesystem, get_dataframe_from_mocked_to_csv):
    summary_file_path = f"output/rule8_imbalanced_{context['analysis_level']}_summary_{context['period']}.md"
    assert summary_file_path in mock_filesystem["_file_contents"], "Summary markdown report was not created."
    summary_content = mock_filesystem["_file_contents"][summary_file_path]
    assert "No valid Z-score groups found" in str(summary_content), "Summary report did not indicate no valid Z-score groups."

@then('imbalanced SPU cases should be identified with some Fast Fish rejections')
def imbalanced_spu_cases_identified_with_fast_fish_rejections(context, mock_filesystem, get_dataframe_from_mocked_to_csv):
    imbalances_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule8_imbalanced_{context['analysis_level']}_imbalances_{context['period']}.csv")
    assert imbalances_df is not None, "Imbalances CSV was not generated."
    assert not imbalances_df.empty, "Imbalances DataFrame is empty."
    assert 'fast_fish_compliant' in imbalances_df.columns, "'fast_fish_compliant' column missing."
    assert (imbalances_df['fast_fish_compliant'] == False).any(), "Expected some Fast Fish non-compliant opportunities."
    assert (imbalances_df['quantity_adjustment'] != 0).any(), "Expected some quantity adjustments."
    Step8CasesSchema.validate(imbalances_df)

def _generate_spu_sales_data(context, num_stores, num_spus, include_sales_amt=True, include_quantity=True, high_performance=False, all_qty_missing=False):
    data = {
        "str_code": [f"STR_{i}" for i in range(num_stores) for _ in range(num_spus)],
        "spu_code": [f"SPU_{j}" for _ in range(num_stores) for j in range(num_spus)],
    }
    if include_quantity and not all_qty_missing:
        data["quantity"] = [float(i % 10 + 1) * (5 if high_performance else 1) for i in range(num_stores * num_spus)]
        data["base_sal_qty"] = [float(i % 5 + 1) * (5 if high_performance else 1) for i in range(num_stores * num_spus)]
        data["fashion_sal_qty"] = [float(i % 3 + 1) * (5 if high_performance else 1) for i in range(num_stores * num_spus)]
        data["sal_qty"] = [float(i % 10 + 1) * (5 if high_performance else 1) for i in range(num_stores * num_spus)]
    if include_sales_amt:
        data["spu_sales_amt"] = [float((i % 10 + 1) * 100) * (5 if high_performance else 1) for i in range(num_stores * num_spus)]
    return pd.DataFrame(data)
