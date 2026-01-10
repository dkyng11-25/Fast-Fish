import pandas as pd
import numpy as np
import pytest
from pytest_bdd import scenario, given, when, then, parsers
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock
import os

# Import schemas for Pandera validation
from tests.validation_comprehensive.schemas.step7_schemas import (
    Step7ClusteringInputSchema,
    Step7SPUSalesInputSchema,
    Step7CategorySalesInputSchema,
    Step7QuantityInputSchema,
    Step7StoreResultsSchema,
    Step7OpportunitiesSchema,
    Step7SubcategoryOpportunitiesSchema
)

# Import the module under test (assuming it's in src/)
import src.step7_missing_category_rule as step7_rule
import src.config as config_module

# Scenarios
@scenario('../features/step7_missing_category_rule.feature', 'Successful identification of missing SPU opportunities with Fast Fish approval')
def test_successful_spu_opportunities_fast_fish_approval():
    pass

@scenario('../features/step7_missing_category_rule.feature', 'Successful identification of missing Subcategory opportunities without seasonal blending')
def test_successful_subcategory_opportunities_no_seasonal_blending():
    pass

@scenario('../features/step7_missing_category_rule.feature', 'Rule 7 fails due to missing clustering results file')
def test_rule7_fails_missing_clustering_file():
    pass

@scenario('../features/step7_missing_category_rule.feature', 'Rule 7 fails due to missing required sales columns')
def test_rule7_fails_missing_sales_columns():
    pass

@scenario('../features/step7_missing_category_rule.feature', 'No opportunities approved when sell-through validator is unavailable')
def test_no_opportunities_approved_validator_unavailable():
    pass

@scenario('../features/step7_missing_category_rule.feature', 'Missing SPU opportunities pass ROI thresholds with Fast Fish validation')
def test_spu_opportunities_pass_roi_thresholds():
    pass

@scenario('../features/step7_missing_category_rule.feature', 'Missing SPU opportunities fail ROI thresholds and are rejected')
def test_spu_opportunities_fail_roi_thresholds_and_are_rejected():
    pass

# Fixtures
@pytest.fixture
def mock_config():
    with patch('src.config.get_current_period') as mock_get_current_period, \
         patch('src.config.get_period_label') as mock_get_period_label, \
         patch('src.config.get_api_data_files') as mock_get_api_data_files, \
         patch('src.config.get_output_files') as mock_get_output_files:
        # Initialize return values with all expected keys and dummy paths
        mock_get_api_data_files.return_value = {
            'spu_sales': "mocked/path/spu_sales.csv",
            'category_sales': "mocked/path/category_sales.csv",
            'store_config': "mocked/path/store_config.csv",
            'store_sales': "mocked/path/store_sales.csv",
        }
        mock_get_output_files.return_value = {
            'clustering_results': "mocked/output/clustering_results.csv",
            'rule7_missing_spu_sellthrough_results': "mocked/output/rule7_missing_spu_sellthrough_results.csv",
            'rule7_missing_spu_sellthrough_opportunities': "mocked/output/rule7_missing_spu_sellthrough_opportunities.csv",
            'rule7_missing_spu_sellthrough_summary': "mocked/output/rule7_missing_spu_sellthrough_summary.md",
            'rule7_missing_subcategory_sellthrough_results': "mocked/output/rule7_missing_subcategory_sellthrough_results.csv",
            'rule7_missing_subcategory_sellthrough_opportunities': "mocked/output/rule7_missing_subcategory_sellthrough_opportunities.csv",
            'rule7_missing_subcategory_sellthrough_summary': "mocked/output/rule7_missing_subcategory_sellthrough_summary.md",
        }
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
        mock_validator_instance.predict_sell_through.return_value = pd.Series(0.8, index=[f'S{i:03d}' for i in range(100)]) # Default prediction
        mock_validator_instance.check_compliance.return_value = pd.Series(True, index=[f'S{i:03d}' for i in range(100)]) # Default compliance
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
    # Temporarily set environment variable for MATRIX_TYPE if needed by step7 (less likely for step6)
    # os.environ["MATRIX_TYPE"] = analysis_level # This is more relevant for step6

@given(parsers.parse('a current period of "{period}" is set'))
def set_current_period(context, period_label):
    context["period"] = period_label # Use the period_label fixture value
    # The mock_src_config fixture now handles CURRENT_PERIOD_LABEL

@given(parsers.parse('clustering results with "{str_col}" and "{cluster_col}" are available'))
def clustering_results_available(context, mock_config, str_col, cluster_col):
    num_stores = 100
    num_clusters = 5
    # Use realistic store codes based on actual data
    real_store_codes = [f'{31250 + i}' for i in range(num_stores)]
    df_clustering = pd.DataFrame({
        'str_code': real_store_codes,
        'cluster_id': [i % num_clusters for i in range(num_stores)]
    })
    
    file_path = f"output/clustering_results_{context['analysis_level']}_{context['period']}.csv"
    # Store in context for the local mock data
    if "local_mock_data" not in context:
        context["local_mock_data"] = {}
    context["local_mock_data"][file_path] = df_clustering
    mock_config["get_output_files"].return_value['clustering_results'] = file_path # Explicitly set the path
    context["df_clustering"] = df_clustering

@given(parsers.parse('SPU sales data with "{str_col}", "{spu_col}", "{sales_col}" is available'))
def spu_sales_data_available(context, mock_config, str_col, spu_col, sales_col):
    num_stores = 100
    num_spus = 20
    num_clusters = 5

    # Use realistic store codes and SPU codes based on actual data
    stores = [f'{31250 + i}' for i in range(num_stores)]
    # Real SPU codes from actual data
    real_spu_codes = ['15W1053', '15T0010', '15T0016', '25T5029', '0A00002', '0A00003', '0A00004', '0A00005', '0A00008', '0A00010', 
                      '0A00015', '0A00025', '10B1004', '10T5263', '15W1058', '15W1083', '15T5183', '17W1001', '17T1002', '20A1003']

    df_clustering = context["df_clustering"]
    cluster_id_map = df_clustering.set_index(str_col)['cluster_id'].to_dict()

    sales_records = []
    # For each cluster, make some SPUs well-selling in most stores
    for cluster_idx in range(num_clusters):
        cluster_stores = [s for s, c_id in cluster_id_map.items() if c_id == cluster_idx]
        
        # Define a "well-selling" SPU for this cluster
        well_selling_spu = real_spu_codes[cluster_idx % len(real_spu_codes)]
        
        for i, store_code in enumerate(cluster_stores):
            # Simulate stores that *do not* sell the well-selling SPU (missing opportunity)
            if i < 2 and len(cluster_stores) > 2: # First two stores in cluster are missing (if cluster is large enough)
                # These stores will not have the well_selling_spu in their sales records
                # Sell other SPUs occasionally to simulate some activity
                for spu_code in real_spu_codes:
                    if spu_code != well_selling_spu and np.random.rand() < 0.2:
                        sales_records.append({'str_code': store_code, 'spu_code': spu_code, sales_col: np.random.rand() * 50, 'sell_through_rate': np.random.rand() * 0.1 + 0.05})
            else: # Other stores in the cluster sell the well-selling SPU and other SPUs
                sales_records.append({'str_code': store_code, 'spu_code': well_selling_spu, sales_col: np.random.rand() * 1000 + 500, 'sell_through_rate': np.random.rand() * 0.3 + 0.5}) # High sales, good ST
                for spu_code in real_spu_codes:
                    if spu_code != well_selling_spu and np.random.rand() < 0.3:
                        sales_records.append({'str_code': store_code, 'spu_code': spu_code, sales_col: np.random.rand() * 200, 'sell_through_rate': np.random.rand() * 0.2 + 0.2})
    
    df_sales = pd.DataFrame(sales_records)
    file_path = f"data/api_data/complete_spu_sales_{context['period']}.csv"
    # Store in context for the local mock data
    if "local_mock_data" not in context:
        context["local_mock_data"] = {}
    context["local_mock_data"][file_path] = df_sales
    
    # Ensure all expected API data files are present in the mock config
    mock_config["get_api_data_files"].return_value.update({
        'spu_sales': file_path,
        'category_sales': f"data/api_data/complete_category_sales_{context['period']}.csv",
        'store_config': f"data/api_data/store_config_{context['period']}.csv",
        'store_sales': f"data/api_data/store_sales_{context['period']}.csv", # For quantity data
    })
    context["df_sales"] = df_sales

@given(parsers.parse('subcategory sales data with "{str_col}", "{sub_cate_col}", "{sales_col}" is available'))
def subcategory_sales_data_available(context, mock_config, mock_filesystem, str_col, sub_cate_col, sales_col):
    # Use realistic store codes and subcategory names based on actual data
    real_store_codes = [f'{31250 + i}' for i in range(100)]
    real_subcategories = ['带帽卫衣', '圆领卫衣', '休闲圆领T恤', '合体圆领T恤', '休闲T恤', '合体T恤', '带帽卫衣', '圆领卫衣', '休闲圆领T恤', '合体圆领T恤']
    
    df_sales = pd.DataFrame({
        str_col: real_store_codes,
        sub_cate_col: [real_subcategories[i % len(real_subcategories)] for i in range(100)],
        sales_col: np.random.rand(100) * 500
    })
    file_path = f"data/api_data/complete_category_sales_{context['period']}.csv"
    # Store in context for the local mock data
    if "local_mock_data" not in context:
        context["local_mock_data"] = {}
    context["local_mock_data"][file_path] = df_sales
    
    mock_config["get_api_data_files"].return_value = {
        'category_sales': file_path
    }
    context["df_sales"] = df_sales

@given(parsers.parse('store config data with "{str_col}" is available'))
def store_config_data_available(context, mock_config, mock_filesystem, str_col):
    # Use realistic store codes and names based on actual data
    real_store_codes = [f'{31250 + i}' for i in range(100)]
    real_store_names = [f'Store_{31250 + i}' for i in range(100)]
    
    df_config = pd.DataFrame({
        str_col: real_store_codes,
        'store_name': real_store_names,
        'region': [f'Region_{i%3}' for i in range(100)]
    })
    file_path = f"data/api_data/store_config_{context['period']}.csv"
    # Store in context for the local mock data
    if "local_mock_data" not in context:
        context["local_mock_data"] = {}
    context["local_mock_data"][file_path] = df_config

    mock_config["get_api_data_files"].return_value.update({'store_config': file_path})
    context["df_config"] = df_config

@given(parsers.parse('quantity data with "{base_qty_col}", "{fashion_qty_col}", "{base_amt_col}", "{fashion_amt_col}" is available'))
def quantity_data_available(context, mock_config, mock_filesystem, base_qty_col, fashion_qty_col, base_amt_col, fashion_amt_col):
    num_stores = 100
    # Use realistic store codes based on actual data
    stores = [f'{31250 + i}' for i in range(num_stores)]

    df_quantity = pd.DataFrame({
        'str_code': stores, # Ensure str_code is explicitly present
        'store_cd': stores, # Add store_cd to satisfy strict mode
        base_qty_col: np.random.randint(10, 100, num_stores),
        fashion_qty_col: np.random.randint(5, 50, num_stores),
        base_amt_col: np.random.rand(num_stores) * 10000,
        fashion_amt_col: np.random.rand(num_stores) * 5000,
        'total_qty': np.random.randint(10, 150, num_stores) + 1, # Ensure total_qty is never zero
        'total_amt': np.random.rand(num_stores) * 15000 + 500 # Add total_amt
    })
    df_quantity['avg_unit_price'] = df_quantity['total_amt'] / df_quantity['total_qty'] # Calculate avg_unit_price

    file_path = f"data/api_data/store_sales_{context['period']}.csv"
    # Store in context for the local mock data
    if "local_mock_data" not in context:
        context["local_mock_data"] = {}
    context["local_mock_data"][file_path] = df_quantity

    mock_config["get_api_data_files"].return_value.update({'store_sales': file_path})
    context["df_quantity"] = df_quantity

@given(parsers.parse('Fast Fish validation and ROI are enabled with ROI threshold "{roi_threshold}" and min margin uplift "{min_margin_uplift}"'))
def fast_fish_and_roi_enabled(context, roi_threshold, min_margin_uplift):
    # These environment variables will be handled by the mock_src_config fixture or specific patches
    # For now, we will simply set them in the context for potential verification.
    context['RULE7_USE_ROI'] = '1'
    context['ROI_MIN_THRESHOLD'] = str(roi_threshold)
    context['MIN_MARGIN_UPLIFT'] = str(min_margin_uplift)

@given(parsers.parse('opportunities are generated that meet all ROI thresholds'))
def opportunities_meet_roi_thresholds(context, mock_filesystem, mock_sell_through_validator):
    # This will generate mock data that, when processed, should pass ROI thresholds.
    # We need to ensure that the mocked SellThroughValidator and the initial sales data
    # result in calculated ROI values above the thresholds set in the environment variables.
    # For simplicity, we'll set the mock validator to always return True for compliance
    # and ensure predicted sell-through is high enough for ROI to pass.
    mock_sell_through_validator["instance"].check_compliance.return_value = pd.Series(True, index=[f'S{i:03d}' for i in range(100)])
    mock_sell_through_validator["instance"].predict_sell_through.return_value = pd.Series(0.9, index=[f'S{i:03d}' for i in range(100)]) # High sell-through

    # Ensure sales data is such that when unit price is calculated, ROI will be positive and above threshold
    # This is more complex and depends on the internal logic of step7, which we are not mocking here.
    # The assumption is that with high sell-through and default settings, opportunities will pass.
    pass # Actual data generation for ROI passing is implicitly handled by other 'given' steps and validator mock

@given(parsers.parse('opportunities are generated that fail ROI thresholds'))
def opportunities_fail_roi_thresholds(context, mock_filesystem, mock_sell_through_validator):
    # This will generate mock data that, when processed, should fail ROI thresholds.
    # We can simulate this by setting a very low margin rate or very high ROI threshold
    # that makes most opportunities non-viable, or by making sell-through predictions very low.
    context['ROI_MIN_THRESHOLD'] = '1000.0' # Set an impossibly high ROI threshold
    context['MIN_MARGIN_UPLIFT'] = '1000000.0' # Set an impossibly high margin uplift

    # Mock validator to ensure it doesn't override our failure condition if it's based on ROI
    mock_sell_through_validator["instance"].check_compliance.return_value = pd.Series(True, index=[f'S{i:03d}' for i in range(100)])
    mock_sell_through_validator["instance"].predict_sell_through.return_value = pd.Series(0.8, index=[f'S{i:03d}' for i in range(100)])

@given('seasonal blending is disabled')
def seasonal_blending_is_disabled(context):
    context['RECENT_MONTHS_BACK'] = '0' # Disables seasonal blending through this env var

@given('clustering results file is missing')
def clustering_results_file_is_missing(context, mock_filesystem):
    # Ensure the file path for clustering results is marked as not existing
    file_path = f"output/clustering_results_{context['analysis_level']}_{context['period']}.csv"
    # Mark the file as not existing in the mock filesystem
    if file_path in mock_filesystem["_data"]:
        del mock_filesystem["_data"][file_path]

@given(parsers.parse('SPU sales data is available but "{missing_col}" column is missing'))
def spu_sales_data_missing_column(context, mock_config, mock_filesystem, missing_col):
    df_sales_incomplete = pd.DataFrame({
        'str_code': [f'S{i:03d}' for i in range(100)],
        'spu_code': [f'SPU{i%20}' for i in range(100)],
        'other_sales_col': np.random.rand(100) * 1000 # Missing the expected sales_col
    })
    file_path = f"data/api_data/complete_spu_sales_{context['period']}.csv"
    mock_filesystem["_data"][file_path] = df_sales_incomplete

    mock_config["get_api_data_files"].return_value.update({'spu_sales': file_path})
    context["df_sales_incomplete"] = df_sales_incomplete

@given('the sell-through validator is unavailable')
def sell_through_validator_unavailable(context, mock_sell_through_validator):
    mock_sell_through_validator["class"].side_effect = ImportError # Simulate import error

# When steps
@when('Rule 7 is executed')
def rule7_is_executed(context, mock_filesystem, mock_config, mock_sell_through_validator):
    # Clear mock filesystem data for a clean test run
    mock_filesystem["_data"].clear()
    mock_filesystem["_file_contents"].clear()
    
    context["exception"] = None
    try:
        # Patching the environment variables with values from context
        with patch.dict('os.environ', {
            "ANALYSIS_LEVEL": context.get("analysis_level", "spu"),
            "RULE7_USE_ROI": context.get("RULE7_USE_ROI", "0"),
            "ROI_MIN_THRESHOLD": context.get("ROI_MIN_THRESHOLD", "0.3"),
            "MIN_MARGIN_UPLIFT": context.get("MIN_MARGIN_UPLIFT", "100"),
            "RECENT_MONTHS_BACK": context.get("RECENT_MONTHS_BACK", "0"),
        }, clear=False): # clear=False to not remove existing env vars
            # Configure mocks for config module based on context
            mock_config["get_current_period"].return_value = (context["period"][:6], context["period"])
            mock_config["get_period_label"].return_value = context["period"]
            
            # Expose mock for assertions
            context["mock_register_step_output"] = mock_filesystem["register_step_output"]

            # Apply the local mock data from 'Given' steps to the mock_filesystem fixture
            # This ensures that files expected by the rule are available in the mocked environment.
            for file_path, df_or_content in context.get("local_mock_data", {}).items():
                if isinstance(df_or_content, pd.DataFrame):
                    mock_filesystem["_data"][file_path] = df_or_content.copy()
                else:
                    mock_filesystem["_file_contents"][file_path] = df_or_content

            # Debug: Print current state of mocked config and filesystem before execution
            print(f"DEBUG: mock_config get_api_data_files return_value: {mock_config["get_api_data_files"].return_value}")
            print(f"DEBUG: mock_config get_output_files return_value: {mock_config["get_output_files"].return_value}")
            print(f"DEBUG: Initial mock_filesystem[_data]: {list(mock_filesystem["_data"].keys())}")
            print(f"DEBUG: Initial mock_filesystem[_file_contents]: {list(mock_filesystem["_file_contents"].keys())}")

            # Patch to_csv directly in the step7 module
            with patch.object(pd.DataFrame, 'to_csv', side_effect=lambda self, *args, **kwargs: print(f"DEBUG: to_csv called with args={args}, kwargs={kwargs}") or mock_filesystem["_data"].__setitem__(args[0], self.copy()) if args else None):
                step7_rule.main()

            # Debug: Check what files were saved
            print(f"DEBUG: Files in mock_filesystem[_data] AFTER main: {list(mock_filesystem["_data"].keys())}")
            print(f"DEBUG: Files in mock_filesystem[_file_contents] AFTER main: {list(mock_filesystem["_file_contents"].keys())}")
    except Exception as e:
        context["exception"] = e
    finally:
        # Ensure register_step_output is not mistaken for an exception
        if "register_step_output" in mock_filesystem and context["exception"] == mock_filesystem["register_step_output"]:
            context["exception"] = None # Clear if it's the mock object itself

# Then steps
@then('missing SPU opportunities should be identified')
def missing_spu_opportunities_identified(context, mock_filesystem):
    opportunities_df = mock_filesystem["_data"].get(f"output/rule7_missing_spu_sellthrough_opportunities_{context['period']}.csv")
    assert opportunities_df is not None, "Opportunities CSV was not generated."
    assert not opportunities_df.empty, "Opportunities DataFrame is empty."
    assert 'recommended_quantity_change' in opportunities_df.columns
    assert (opportunities_df['recommended_quantity_change'] > 0).any(), "No positive quantity increases recommended."
    Step7OpportunitiesSchema.validate(opportunities_df)

@then('store-level results should be generated')
def store_level_results_generated(context, mock_filesystem):
    results_df = mock_filesystem["_data"].get(f"output/rule7_missing_spu_sellthrough_results_{context['period']}.csv")
    assert results_df is not None, "Store-level results CSV was not generated."
    assert not results_df.empty, "Store-level results DataFrame is empty."
    assert 'total_opportunity_value' in results_df.columns
    assert (results_df['total_opportunity_value'] > 0).any(), "No positive total opportunity value found."
    Step7StoreResultsSchema.validate(results_df)

@then('detailed opportunities should be generated and be Fast Fish compliant')
def detailed_opportunities_generated_and_fast_fish_compliant(context, mock_filesystem):
    opportunities_df = mock_filesystem["_data"].get(f"output/rule7_missing_spu_sellthrough_opportunities_{context['period']}.csv")
    assert opportunities_df is not None, "Detailed opportunities CSV was not generated."
    assert not opportunities_df.empty, "Detailed opportunities DataFrame is empty."
    assert 'fast_fish_compliant' in opportunities_df.columns
    assert opportunities_df['fast_fish_compliant'].any(), "No Fast Fish compliant opportunities found."
    Step7OpportunitiesSchema.validate(opportunities_df)

@then('a summary report should be created')
def summary_report_created(context, mock_filesystem):
    summary_file_path = f"output/rule7_missing_spu_sellthrough_summary_{context['period']}.md"
    assert summary_file_path in mock_filesystem["_file_contents"], "Summary markdown report was not created."
    # Further checks on content can be added here if needed

@then(parsers.parse('the output dataframes should conform to "{schema1}" and "{schema2}"'))
def output_dataframes_conform_to_schemas(context, mock_filesystem, schema1, schema2):
    # This step validates that the output dataframes conform to the specified schemas
    results_df = mock_filesystem["_data"].get(f"output/rule7_missing_spu_sellthrough_results_{context['period']}.csv")
    opportunities_df = mock_filesystem["_data"].get(f"output/rule7_missing_spu_sellthrough_opportunities_{context['period']}.csv")

    assert results_df is not None, f"Could not find results dataframe for schema {schema1}"
    assert opportunities_df is not None, f"Could not find opportunities dataframe for schema {schema2}"

    results_schema_class = globals()[schema1]
    opportunities_schema_class = globals()[schema2]

    results_schema_class.validate(results_df)
    opportunities_schema_class.validate(opportunities_df)

@then('missing subcategory opportunities should be identified')
def missing_subcategory_opportunities_identified(context, mock_filesystem):
    opportunities_df = mock_filesystem["_data"].get(f"output/rule7_missing_subcategory_opportunities_{context['period']}.csv")
    assert opportunities_df is not None, "Opportunities CSV was not generated."
    assert not opportunities_df.empty, "Opportunities DataFrame is empty."
    assert 'recommended_quantity_change' in opportunities_df.columns
    assert (opportunities_df['recommended_quantity_change'] > 0).any(), "No positive quantity increases recommended."
    Step7SubcategoryOpportunitiesSchema.validate(opportunities_df)

@then('detailed subcategory opportunities should be generated')
def detailed_subcategory_opportunities_generated(context, mock_filesystem):
    opportunities_df = mock_filesystem["_data"].get(f"output/rule7_missing_subcategory_opportunities_{context['period']}.csv")
    assert opportunities_df is not None, "Detailed subcategory opportunities CSV was not generated."
    assert not opportunities_df.empty, "Detailed subcategory opportunities DataFrame is empty."
    assert 'recommended_quantity_change' in opportunities_df.columns
    assert (opportunities_df['recommended_quantity_change'] > 0).any(), "No positive quantity increases recommended."
    Step7SubcategoryOpportunitiesSchema.validate(opportunities_df)

@then(parsers.parse('Rule 7 execution should fail with a "{error_type}"'))
def rule7_execution_should_fail_with_error(context, error_type):
    assert context["exception"] is not None, "Expected an exception but none was raised."
    # Assert that the exception type or its message contains the expected error information
    exception_message = str(context["exception"])
    if error_type == "FileNotFoundError":
        assert "Clustering results not found" in exception_message or "Sales data not found" in exception_message, \
               f"Expected FileNotFoundError or related message, but got: {exception_message}"
    elif error_type == "ValueError":
        assert "Missing required columns" in exception_message or "Quantity data missing" in exception_message, \
               f"Expected ValueError or related message, but got: {exception_message}"
    elif error_type == "RuntimeError":
        assert "Sell-through validator" in exception_message, \
               f"Expected RuntimeError related to validator, but got: {exception_message}"
    else:
        assert context["exception"].__class__.__name__ == error_type, \
            f"Expected exception type {error_type}, but got {context['exception'].__class__.__name__}"

@then(parsers.parse('an error message indicating the missing clustering file should be displayed'))
def error_message_missing_clustering_file(context):
    exception_message = str(context["exception"])
    assert "FileNotFoundError" in exception_message or "Clustering results not found" in exception_message, \
           f"Expected missing clustering file error message, got: {exception_message}"

@then(parsers.parse('an error message indicating the missing sales column should be displayed'))
def error_message_missing_sales_column(context):
    exception_message = str(context["exception"])
    assert "ValueError" in exception_message or "Missing real quantity data" in exception_message or "Quantity data missing" in exception_message, \
           f"Expected missing sales column error message, got: {exception_message}"

@then('store-level results should be generated with zero Fast Fish approved opportunities')
def store_level_results_zero_fast_fish_approved(context, mock_filesystem):
    results_df = mock_filesystem["_data"].get(f"output/rule7_missing_spu_sellthrough_results_{context['period']}.csv")
    assert results_df is not None, "Store-level results CSV was not generated."
    assert not results_df.empty, "Store-level results DataFrame is empty."
    assert 'fastfish_approved_count' in results_df.columns
    assert (results_df['fastfish_approved_count'] == 0).all(), "Expected zero Fast Fish approved opportunities."
    Step7StoreResultsSchema.validate(results_df)

@then('detailed opportunities should be generated but not be Fast Fish compliant')
def detailed_opportunities_not_fast_fish_compliant(context, mock_filesystem):
    opportunities_df = mock_filesystem["_data"].get(f"output/rule7_missing_spu_sellthrough_opportunities_{context['period']}.csv")
    assert opportunities_df is not None, "Detailed opportunities CSV was not generated."
    assert not opportunities_df.empty, "Detailed opportunities DataFrame is empty."
    assert 'fast_fish_compliant' in opportunities_df.columns
    assert not opportunities_df['fast_fish_compliant'].any(), "Expected no Fast Fish compliant opportunities."
    Step7OpportunitiesSchema.validate(opportunities_df)

@then('no sales performance opportunities should be identified')
def no_sales_performance_opportunities_identified(context, mock_filesystem):
    opportunities_df = mock_filesystem["_data"].get(f"output/rule7_missing_spu_sellthrough_opportunities_{context['period']}.csv")
    assert opportunities_df is None or opportunities_df.empty, "Expected no opportunities or an empty opportunities dataframe."
    results_df = mock_filesystem["_data"].get(f"output/rule7_missing_spu_sellthrough_results_{context['period']}.csv")
    assert results_df is None or results_df.empty, "Expected no results or an empty results dataframe."

@then('no output files related to opportunities should be generated')
def no_output_files_related_to_opportunities_should_be_generated(context, mock_filesystem):
    assert mock_filesystem["_data"].get(f"output/rule7_missing_spu_sellthrough_opportunities_{context['period']}.csv") is None
    assert mock_filesystem["_data"].get(f"output/rule7_missing_spu_sellthrough_results_{context['period']}.csv") is None
    summary_file_path = f"output/rule7_missing_spu_sellthrough_summary_{context['period']}.md"
    assert summary_file_path not in mock_filesystem["_file_contents"]

@then('a summary report should be created and indicate no opportunities were found')
def summary_report_no_opportunities_found(context, mock_filesystem):
    summary_file_path = f"output/rule7_missing_spu_sellthrough_summary_{context['period']}.md"
    assert summary_file_path in mock_filesystem["_file_contents"], "Summary markdown report was not created."
    summary_content = mock_filesystem["_file_contents"][summary_file_path]
    assert "No missing SPU opportunities were found" in str(summary_content) or \
           "Total Opportunities: 0" in str(summary_content), \
           f"Summary report did not indicate no opportunities. Content: {summary_content}"
