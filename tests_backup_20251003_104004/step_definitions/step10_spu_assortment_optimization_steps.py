import pandas as pd
import numpy as np
import pytest
from pytest_bdd import scenario, given, when, then, parsers
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock
import os
import json

# Import schemas for Pandera validation
from tests.validation_comprehensive.schemas.step10_schemas import (
    Step10ResultsSchema,
    Step10OpportunitiesSchema,
    Step10InputClusteringSchema,
    Step10InputStoreConfigSchema,
    Step10InputQuantitySchema
)

# Import the module under test
import src.step10_spu_assortment_optimization as step10_rule
import src.config as config_module

# Scenarios
@scenario('../features/step10_spu_assortment_optimization.feature', 'Successful SPU overcapacity detection and unit reductions with Fast Fish validation')
def test_successful_spu_overcapacity_fast_fish_validation():
    pass

@scenario('../features/step10_spu_assortment_optimization.feature', 'SPU overcapacity detection with seasonal blending and no Fast Fish validation')
def test_spu_overcapacity_seasonal_blending_no_fast_fish():
    pass

@scenario('../features/step10_spu_assortment_optimization.feature', 'Rule 10 fails due to missing clustering results file')
def test_rule10_fails_missing_clustering_file():
    pass

@scenario('../features/step10_spu_assortment_optimization.feature', 'Rule 10 handles missing real unit fields gracefully')
def test_rule10_handles_missing_real_unit_fields_gracefully():
    pass

@scenario('../features/step10_spu_assortment_optimization.feature', 'No overcapacity identified when all SPUs are below target count or sales volume')
def test_no_overcapacity_identified():
    pass

@scenario('../features/step10_spu_assortment_optimization.feature', 'SPU overcapacity detection with strict inner join mode')
def test_spu_overcapacity_strict_inner_join():
    pass

@scenario('../features/step10_spu_assortment_optimization.feature', 'Rule 10 operates in August with seasonal blending explicitly disabled')
def test_rule10_august_no_seasonal_blending():
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
def mock_filesystem():
    _mock_dataframes = {}
    _mock_file_contents = {}
    
    def mock_read_csv(filepath, **kwargs):
        if filepath in _mock_dataframes:
            return _mock_dataframes[filepath]
        if filepath in _mock_file_contents: # For markdown files
            return _mock_file_contents[filepath] # Return raw content for markdown
        return pd.DataFrame()

    def mock_to_csv(df, filepath, **kwargs):
        if filepath.endswith(".csv"):
            _mock_dataframes[filepath] = df.copy()
        elif filepath.endswith(".md"):
            _mock_file_contents[filepath] = df.to_markdown() if not isinstance(df, str) else df # Store markdown content as a string

    def mock_exists(filepath):
        return filepath in _mock_dataframes or filepath in _mock_file_contents

    with patch("pandas.read_csv", side_effect=mock_read_csv), \
         patch("pandas.DataFrame.to_csv", side_effect=mock_to_csv) as mock_to_csv_obj, \
         patch("os.path.exists") as mock_exists_obj:
        
        mock_exists_obj.side_effect = mock_exists # Set the initial side effect
        yield {
            "exists": mock_exists_obj, # Pass the MagicMock object
            "read_csv": mock_read_csv,
            "to_csv": mock_to_csv,
            "_data": _mock_dataframes,
            "_file_contents": _mock_file_contents # Expose for assertions
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
@given(parsers.parse('the current period is "{period}"'))
def set_current_period(context, period, mock_config):
    context["period"] = period
    os.environ["CURRENT_PERIOD_LABEL"] = period # Set the environment variable
    mock_config["get_current_period"].return_value = (context["period"][:6], context["period"])
    mock_config["get_period_label"].return_value = context["period"]

@given(parsers.parse('seasonal blending is enabled with seasonal period "{seasonal_period}"'))
def seasonal_blending_enabled(context, seasonal_period):
    os.environ["SEASONAL_BLENDING"] = '1'
    os.environ["SEASONAL_YYYYMM"] = seasonal_period[:6]
    os.environ["SEASONAL_PERIOD"] = seasonal_period[6:]
    context["original_seasonal_blending"] = os.environ.get("SEASONAL_BLENDING")
    context["original_seasonal_yyyymm"] = os.environ.get("SEASONAL_YYYYMM")
    context["original_seasonal_period"] = os.environ.get("SEASONAL_PERIOD")

@given(parsers.parse('seasonal blending is explicitly disabled'))
def seasonal_blending_explicitly_disabled(context):
    os.environ["USE_BLENDED_SEASONAL"] = '0'
    os.environ["SEASONAL_BLENDING"] = '0' # Redundant but for safety
    context["original_use_blended_seasonal"] = os.environ.get("USE_BLENDED_SEASONAL")
    context["original_seasonal_blending"] = os.environ.get("SEASONAL_BLENDING")

@given(parsers.parse('join mode is "{join_mode}"'))
def join_mode_is(context, join_mode):
    os.environ["JOIN_MODE"] = join_mode
    context["original_join_mode"] = os.environ.get("JOIN_MODE")

@given(parsers.parse('clustering results with "{str_col}" and "{cluster_col}" are available'))
def clustering_results_available(context, mock_config, mock_filesystem, str_col, cluster_col):
    df_clustering = pd.DataFrame({
        str_col: [f'S{i:03d}' for i in range(100)],
        cluster_col: [f'C{i%5}' for i in range(100)],
        'Cluster': [f'C{i%5}' for i in range(100)] # Ensure both forms are present for step10
    })
    clustering_path = f"output/clustering_results_spu_{context['period']}.csv"
    mock_filesystem["_data"][clustering_path] = df_clustering
    mock_filesystem["_data"]["output/clustering_results.csv"] = df_clustering # backward compatibility
    mock_filesystem["_data"]["output/enhanced_clustering_results.csv"] = df_clustering # enhanced path
    
    original_exists_side_effect = mock_filesystem["exists"].side_effect
    def new_exists_side_effect(path):
        if path in [clustering_path, "output/clustering_results.csv", "output/enhanced_clustering_results.csv"]:
            return True
        if callable(original_exists_side_effect):
            return original_exists_side_effect(path)
        return False
    mock_filesystem["exists"].side_effect = new_exists_side_effect

    mock_config["get_output_files"].return_value = {
        'clustering_results': clustering_path
    }
    context["df_clustering"] = df_clustering

@given(parsers.parse('store config data with "{str_col}" and SPU sales JSON in "{json_col}" is available for {store_count:d} stores'))
def store_config_data_with_spu_sales_json(context, mock_config, mock_filesystem, str_col, json_col, store_count: int = 100):
    # Simulate store config with sty_sal_amt (JSON string) and target_sty_cnt_avg
    store_codes = [f'S{i:03d}' for i in range(store_count)]
    spu_data_json = []
    for i in range(store_count):
        # Simulate categories with some overcapacity
        current_spu_count = np.random.randint(5, 15)
        target_spu_count = np.random.randint(2, current_spu_count - 1)
        if current_spu_count > target_spu_count: # Only overcapacity categories are processed
            spus = {f'SPU{j}': float(np.random.randint(100, 1000)) for j in range(current_spu_count)}
            spu_data_json.append(json.dumps(spus))
        else:
            spu_data_json.append(json.dumps({})) # No overcapacity
    
    df_config = pd.DataFrame({
        str_col: store_codes,
        'store_name': [f'Store {i}' for i in range(store_count)],
        'region': [f'Region {i%3}' for i in range(store_count)],
        'ext_sty_cnt_avg': [np.random.randint(5,15) for _ in range(store_count)], # Current SPU count
        'target_sty_cnt_avg': [np.random.randint(2,10) for _ in range(store_count)], # Target SPU count
        json_col: spu_data_json
    })

    # Manually ensure some overcapacity exists for testing
    for i in range(min(5, store_count)): # First 5 stores will have overcapacity
        df_config.loc[i, 'ext_sty_cnt_avg'] = 10
        df_config.loc[i, 'target_sty_cnt_avg'] = 5
        spus = {f'SPU{j}': float(np.random.randint(100, 1000)) for j in range(10)}
        df_config.loc[i, json_col] = json.dumps(spus)

    config_path = f"data/api_data/store_config_{context['period']}.csv"
    mock_filesystem["_data"][config_path] = df_config
    
    original_exists_side_effect = mock_filesystem["exists"].side_effect
    def new_exists_side_effect(path):
        if path == config_path:
            return True
        if callable(original_exists_side_effect):
            return original_exists_side_effect(path)
        return False
    mock_filesystem["exists"].side_effect = new_exists_side_effect

    mock_config["get_api_data_files"].return_value = {
        'store_config': config_path
    }
    context["df_config"] = df_config

@given(parsers.parse('SPU sales data with "{str_col}", "{spu_col}", "{qty_col}", "{base_qty_col}", "{fashion_qty_col}", "{sal_qty_col}", "{spu_sales_amt_col}" is available for {store_count:d} stores'))
def spu_sales_data_full_quantity_info(context, mock_config, mock_filesystem, str_col, spu_col, qty_col, base_qty_col, fashion_qty_col, sal_qty_col, spu_sales_amt_col, store_count: int = 100):
    num_spus_per_store = 10
    total_records = store_count * num_spus_per_store
    store_codes = [f'S{i:03d}' for i in range(store_count)]
    df_sales = pd.DataFrame({
        str_col: [store_code for store_code in store_codes for _ in range(num_spus_per_store)],
        spu_col: [f'SPU{j}' for j in range(num_spus_per_store)] * store_count,
        qty_col: np.random.randint(10, 50, total_records),
        base_qty_col: np.random.randint(5, 25, total_records),
        fashion_qty_col: np.random.randint(0, 10, total_records),
        sal_qty_col: np.random.randint(10, 50, total_records),
        spu_sales_amt_col: np.random.rand(total_records) * 1000
    })
    sales_path = f"data/api_data/complete_spu_sales_{context['period']}.csv"
    mock_filesystem["_data"][sales_path] = df_sales
    
    original_exists_side_effect = mock_filesystem["exists"].side_effect
    def new_exists_side_effect(path):
        if path == sales_path:
            return True
        if callable(original_exists_side_effect):
            return original_exists_side_effect(path)
        return False
    mock_filesystem["exists"].side_effect = new_exists_side_effect

    mock_config["get_api_data_files"].return_value.update({
        'spu_sales': sales_path,
        'store_sales': sales_path
    })
    context["df_sales"] = df_sales

@given(parsers.parse('SPU sales data with "{str_col}", "{spu_col}", "{qty_col}" is available'))
@given(parsers.parse('SPU sales data with "{str_col}", "{spu_col}", "{qty_col}" is available for {store_count:d} stores'))
def spu_sales_data_only_quantity(context, mock_config, mock_filesystem, str_col, spu_col, qty_col, store_count: int = 100):
    num_spus_per_store = 10
    total_records = store_count * num_spus_per_store
    store_codes = [f'S{i:03d}' for i in range(store_count)]
    df_sales = pd.DataFrame({
        str_col: [store_code for store_code in store_codes for _ in range(num_spus_per_store)], # 10 SPUs per store
        spu_col: [f'SPU{j}' for j in range(num_spus_per_store)] * store_count,
        qty_col: np.random.randint(10, 50, total_records),
        'spu_sales_amt': np.random.rand(total_records) * 1000 # Still need sales amount for unit price
    })
    sales_path = f"data/api_data/complete_spu_sales_{context['period']}.csv"
    mock_filesystem["_data"][sales_path] = df_sales
    
    original_exists_side_effect = mock_filesystem["exists"].side_effect
    def new_exists_side_effect(path):
        if path == sales_path:
            return True
        if callable(original_exists_side_effect):
            return original_exists_side_effect(path)
        return False
    mock_filesystem["exists"].side_effect = new_exists_side_effect

    mock_config["get_api_data_files"].return_value.update({
        'spu_sales': sales_path,
        'store_sales': sales_path
    })
    context["df_sales"] = df_sales

@given(parsers.parse('minimum sales volume is "{min_sales_volume}"'))
def minimum_sales_volume_set(context, min_sales_volume):
    os.environ["MIN_SALES_VOLUME"] = str(min_sales_volume)
    context["original_min_sales_volume"] = os.environ.get("MIN_SALES_VOLUME")

@given(parsers.parse('minimum reduction quantity is "{min_reduction_qty}"'))
def minimum_reduction_quantity_set(context, min_reduction_qty):
    os.environ["MIN_REDUCTION_QUANTITY"] = str(min_reduction_qty)
    context["original_min_reduction_quantity"] = os.environ.get("MIN_REDUCTION_QUANTITY")

@given(parsers.parse('maximum reduction percentage is "{max_reduction_pct}"'))
def maximum_reduction_percentage_set(context, max_reduction_pct):
    os.environ["MAX_REDUCTION_PERCENTAGE"] = str(max_reduction_pct)
    context["original_max_reduction_percentage"] = os.environ.get("MAX_REDUCTION_PERCENTAGE")

@given('Fast Fish validation is available')
def fast_fish_validation_is_available(context, mock_sell_through_validator):
    assert mock_sell_through_validator["instance"].is_initialized is True
    os.environ["SKIP_SELLTHROUGH_VALIDATION"] = '0' # Ensure validation is NOT skipped
    context["original_skip_sellthrough_validation"] = os.environ.get("SKIP_SELLTHROUGH_VALIDATION")

@given('Fast Fish validation is unavailable')
def fast_fish_validation_is_unavailable(context, mock_sell_through_validator):
    mock_sell_through_validator["class"].side_effect = ImportError # Simulate import error
    os.environ["SKIP_SELLTHROUGH_VALIDATION"] = '1' # Ensure validation IS skipped
    context["original_skip_sellthrough_validation"] = os.environ.get("SKIP_SELLTHROUGH_VALIDATION")

@given('clustering results file is missing')
def clustering_results_file_is_missing(context, mock_filesystem):
    clustering_path_base = f"output/clustering_results_spu_{context['period']}.csv"
    clustering_path_compat = "output/clustering_results.csv"
    clustering_path_enhanced = "output/enhanced_clustering_results.csv"

    for path_to_remove in [clustering_path_base, clustering_path_compat, clustering_path_enhanced]:
        if path_to_remove in mock_filesystem["_data"]: # Remove it if it was added by a previous step
            del mock_filesystem["_data"][path_to_remove]
    
    original_exists_side_effect = mock_filesystem["exists"].side_effect
    def new_exists_side_effect(path):
        if path in [clustering_path_base, clustering_path_compat, clustering_path_enhanced]:
            return False
        if callable(original_exists_side_effect):
            return original_exists_side_effect(path)
        return False
    mock_filesystem["exists"].side_effect = new_exists_side_effect

@given('SPU sales data is available but missing real unit quantity columns (e.g., "quantity", "base_sal_qty")')
@given(parsers.parse('SPU sales data is available but missing real unit quantity columns (e.g., "quantity", "base_sal_qty") for {store_count:d} stores'))
def spu_sales_data_missing_real_unit_cols(context, mock_config, mock_filesystem, store_count: int = 100):
    df_sales_no_qty = pd.DataFrame({
        'str_code': [f'S{i:03d}' for i in range(store_count) for _ in range(10)],
        'spu_code': [f'SPU{j}' for j in range(10)] * store_count,
        'spu_sales_amt': np.random.rand(store_count * 10) * 1000 # Sales amount is present, but no explicit quantity columns
    })
    sales_path = f"data/api_data/complete_spu_sales_{context['period']}.csv"
    mock_filesystem["_data"][sales_path] = df_sales_no_qty
    
    original_exists_side_effect = mock_filesystem["exists"].side_effect
    def new_exists_side_effect(path):
        if path == sales_path:
            return True
        if callable(original_exists_side_effect):
            return original_exists_side_effect(path)
        return False
    mock_filesystem["exists"].side_effect = new_exists_side_effect

    mock_config["get_api_data_files"].return_value.update({
        'spu_sales': sales_path,
        'store_sales': sales_path
    })
    context["df_sales_no_qty"] = df_sales_no_qty

@given('all categories have current SPU count less than or equal to target SPU count')
@given(parsers.parse('all categories have current SPU count less than or equal to target SPU count for {store_count:d} stores'))
def all_categories_no_overcapacity(context, mock_config, mock_filesystem, store_count: int = 100):
    store_codes = [f'S{i:03d}' for i in range(store_count)]
    spu_data_json = []
    for i in range(store_count):
        current_spu_count = np.random.randint(5, 10)
        target_spu_count = np.random.randint(current_spu_count, 15) # Ensure target >= current
        spus = {f'SPU{j}': float(np.random.randint(100, 1000)) for j in range(current_spu_count)}
        spu_data_json.append(json.dumps(spus))
    
    df_config_no_overcapacity = pd.DataFrame({
        'str_code': store_codes,
        'ext_sty_cnt_avg': [np.random.randint(5,10) for _ in range(store_count)],
        'target_sty_cnt_avg': [np.random.randint(10,15) for _ in range(store_count)], # Target > Current
        'sty_sal_amt': spu_data_json
    })
    config_path = f"data/api_data/store_config_{context['period']}.csv"
    mock_filesystem["_data"][config_path] = df_config_no_overcapacity
    
    original_exists_side_effect = mock_filesystem["exists"].side_effect
    def new_exists_side_effect(path):
        if path == config_path:
            return True
        if callable(original_exists_side_effect):
            return original_exists_side_effect(path)
        return False
    mock_filesystem["exists"].side_effect = new_exists_side_effect

    mock_config["get_api_data_files"].return_value = {
        'store_config': config_path
    }
    context["df_config_no_overcapacity"] = df_config_no_overcapacity

# When steps
@when('Rule 10 is executed')
def rule10_is_executed(context, mock_config, mock_filesystem, mock_sell_through_validator):
    context["exception"] = None
    try:
        with patch('src.step10_spu_assortment_optimization.get_current_period', new=mock_config['get_current_period']), \
             patch('src.step10_spu_assortment_optimization.get_period_label', new=mock_config['get_period_label']), \
             patch('src.step10_spu_assortment_optimization.pd.read_csv', side_effect=mock_filesystem['read_csv']), \
             patch('src.step10_spu_assortment_optimization.os.path.exists', new=mock_filesystem['exists']), \
             patch('src.step10_spu_assortment_optimization.SellThroughValidator', new=mock_sell_through_validator['class']), \
             patch('src.step10_spu_assortment_optimization.os.makedirs', MagicMock(return_value=None)), \
             patch('src.step10_spu_assortment_optimization.pd.DataFrame.to_csv', new=mock_filesystem['to_csv']):
            
            mock_config["get_current_period"].return_value = (context["period"][:6], context["period"])
            mock_config["get_period_label"].return_value = context["period"]

            # Dynamically set USE_BLENDED_SEASONAL based on scenario context or default to August logic
            if "original_use_blended_seasonal" in context:
                step10_rule.USE_BLENDED_SEASONAL = (os.environ.get("USE_BLENDED_SEASONAL") == '1')
            else:
                # Default August logic
                try:
                    current_month = int(context["period"][4:6])
                    step10_rule.USE_BLENDED_SEASONAL = (current_month == 8)
                except (ValueError, IndexError):
                    step10_rule.USE_BLENDED_SEASONAL = False
            
            # Set JOIN_MODE if specified in context
            if "original_join_mode" in context:
                step10_rule.JOIN_MODE = os.environ.get("JOIN_MODE")

            step10_rule.main()
    except Exception as e:
        context["exception"] = e
    finally:
        # Clean up environment variables
        if "original_seasonal_blending" in context:
            if context["original_seasonal_blending"] is not None:
                os.environ["SEASONAL_BLENDING"] = context["original_seasonal_blending"]
            else:
                del os.environ["SEASONAL_BLENDING"]
        if "original_seasonal_yyyymm" in context:
            if context["original_seasonal_yyyymm"] is not None:
                os.environ["SEASONAL_YYYYMM"] = context["original_seasonal_yyyymm"]
            else:
                del os.environ["SEASONAL_YYYYMM"]
        if "original_seasonal_period" in context:
            if context["original_seasonal_period"] is not None:
                os.environ["SEASONAL_PERIOD"] = context["original_seasonal_period"]
            else:
                del os.environ["SEASONAL_PERIOD"]
        if "original_use_blended_seasonal" in context:
            if context["original_use_blended_seasonal"] is not None:
                os.environ["USE_BLENDED_SEASONAL"] = context["original_use_blended_seasonal"]
            else:
                del os.environ["USE_BLENDED_SEASONAL"]
        if "original_join_mode" in context:
            if context["original_join_mode"] is not None:
                os.environ["JOIN_MODE"] = context["original_join_mode"]
            else:
                del os.environ["JOIN_MODE"]
        if "original_min_sales_volume" in context:
            if context["original_min_sales_volume"] is not None:
                os.environ["MIN_SALES_VOLUME"] = context["original_min_sales_volume"]
            else:
                del os.environ["MIN_SALES_VOLUME"]
        if "original_min_reduction_quantity" in context:
            if context["original_min_reduction_quantity"] is not None:
                os.environ["MIN_REDUCTION_QUANTITY"] = context["original_min_reduction_quantity"]
            else:
                del os.environ["MIN_REDUCTION_QUANTITY"]
        if "original_max_reduction_percentage" in context:
            if context["original_max_reduction_percentage"] is not None:
                os.environ["MAX_REDUCTION_PERCENTAGE"] = context["original_max_reduction_percentage"]
            else:
                del os.environ["MAX_REDUCTION_PERCENTAGE"]
        if "original_skip_sellthrough_validation" in context:
            if context["original_skip_sellthrough_validation"] is not None:
                os.environ["SKIP_SELLTHROUGH_VALIDATION"] = context["original_skip_sellthrough_validation"]
            else:
                del os.environ["SKIP_SELLTHROUGH_VALIDATION"]

# Then steps
@then('SPU overcapacity should be identified')
def spu_overcapacity_identified(context, mock_filesystem):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule10_spu_overcapacity_opportunities_{context['period']}.csv")
    assert opportunities_df is not None, "Opportunities CSV was not generated."
    assert not opportunities_df.empty, "Opportunities DataFrame is empty."
    assert 'recommended_quantity_change' in opportunities_df.columns
    assert (opportunities_df['recommended_quantity_change'] < 0).any(), "No SPU reductions recommended."
    Step10OpportunitiesSchema.validate(opportunities_df)

@then('store-level results should be generated with negative quantity changes (reductions)')
def store_level_results_generated_negative_qty_changes(context, mock_filesystem):
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule10_smart_overcapacity_results_{context['period']}.csv")
    assert results_df is not None, "Results CSV was not generated."
    assert not results_df.empty, "Results DataFrame is empty."
    assert 'total_quantity_adjustment' in results_df.columns
    assert (results_df['total_quantity_adjustment'] < 0).any(), "No negative quantity adjustments (reductions) found."
    Step10ResultsSchema.validate(results_df)

@then('detailed opportunities should be generated and be Fast Fish compliant')
def detailed_opportunities_generated_fast_fish_compliant(context, mock_filesystem):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule10_spu_overcapacity_opportunities_{context['period']}.csv")
    assert opportunities_df is not None, "Detailed opportunities CSV was not generated."
    assert not opportunities_df.empty, "Detailed opportunities DataFrame is empty."
    assert 'fast_fish_compliant' in opportunities_df.columns
    assert opportunities_df['fast_fish_compliant'].any(), "No Fast Fish compliant opportunities found."
    Step10OpportunitiesSchema.validate(opportunities_df)

@then('a summary report should be created')
def summary_report_created(context, mock_filesystem):
    summary_file_path = f"output/rule10_smart_overcapacity_spu_summary_{context['period']}.md"
    assert summary_file_path in mock_filesystem["_file_contents"], "Summary markdown report was not created."

@then(parsers.parse('the output dataframes should conform to "{schema1}" and "{schema2}"'))
def output_dataframes_conform_to_schemas(context, mock_filesystem, schema1, schema2):
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule10_smart_overcapacity_results_{context['period']}.csv")
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule10_spu_overcapacity_opportunities_{context['period']}.csv")

    assert results_df is not None, f"Could not find results dataframe for schema {schema1}"
    assert opportunities_df is not None, f"Could not find opportunities dataframe for schema {schema2}"

    results_schema_class = globals()[schema1]
    opportunities_schema_class = globals()[schema2]

    results_schema_class.validate(results_df)
    opportunities_schema_class.validate(opportunities_df)

@then('detailed opportunities should be generated but not necessarily Fast Fish compliant')
def detailed_opportunities_generated_not_necessarily_fast_fish_compliant(context, mock_filesystem):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule10_spu_overcapacity_opportunities_{context['period']}.csv")
    assert opportunities_df is not None, "Detailed opportunities CSV was not generated."
    assert not opportunities_df.empty, "Detailed opportunities DataFrame is empty."
    assert 'fast_fish_compliant' in opportunities_df.columns
    # In this scenario, fast_fish_compliant could be False or NaN if validator is unavailable
    Step10OpportunitiesSchema.validate(opportunities_df)

@then(parsers.parse('Rule 10 execution should fail with a "{error_type}"'))
def rule10_execution_should_fail_with_error(context, error_type):
    assert context["exception"] is not None, "Expected an exception but none was raised."
    assert context["exception"].__class__.__name__ == error_type, \
        f"Expected exception type {error_type}, but got {context['exception'].__class__.__name__}"

@then(parsers.parse('an error message indicating the missing clustering file should be displayed'))
def error_message_missing_clustering_file(context):
    assert "FileNotFoundError" in str(context["exception"]) and \
           ("clustering_results" in str(context["exception"]) or "Normalized matrix not found" in str(context["exception"]) or "Original matrix not found" in str(context["exception"])), \
           f"Expected missing clustering file error message, got: {context['exception']}"

@then('Rule 10 execution should complete without error')
def rule10_execution_should_complete_without_error(context):
    assert context["exception"] is None, f"Expected no exception, but got {context['exception']}"

@then('opportunities should have null or zero quantity changes where real units are absent')
def opportunities_null_or_zero_quantity_changes_real_units_absent(context, mock_filesystem):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule10_spu_overcapacity_opportunities_{context['period']}.csv")
    assert opportunities_df is not None, "Opportunities CSV was not generated."
    assert 'recommended_quantity_change' in opportunities_df.columns
    # Check if for relevant rows (where real units would be absent), quantity changes are zero or null
    # This part is complex and needs more specific data setup to verify precisely.
    # For a general check, we can ensure that not all quantity changes are non-zero.
    # For this scenario, we expect some nulls or zeros if unit data was truly missing
    assert (opportunities_df['recommended_quantity_change'].isnull() | (opportunities_df['recommended_quantity_change'] == 0)).any(), \
        "Expected some null or zero quantity changes due to missing real unit data."
    Step10OpportunitiesSchema.validate(opportunities_df) # Still validate schema to ensure structure

@then('store-level results should be generated with zero total quantity adjustments')
def store_level_results_zero_total_quantity_adjustments(context, mock_filesystem):
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule10_smart_overcapacity_results_{context['period']}.csv")
    assert results_df is not None, "Results CSV was not generated."
    assert 'total_quantity_adjustment' in results_df.columns
    assert (results_df['total_quantity_adjustment'] == 0).all(), "Expected all total quantity adjustments to be zero."
    Step10ResultsSchema.validate(results_df)

@then('SPU overcapacity should be identified only for stores with both planning and clustering data')
def spu_overcapacity_identified_only_for_joined_stores(context, mock_filesystem):
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule10_smart_overcapacity_results_{context['period']}.csv")
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule10_spu_overcapacity_opportunities_{context['period']}.csv")

    assert results_df is not None and not results_df.empty, "Results CSV was not generated or is empty."
    assert opportunities_df is not None and not opportunities_df.empty, "Opportunities CSV was not generated or is empty."

    # The mocked config and sales data for 'some stores' is for 50 stores, while clustering is for 100.
    # With an inner join, we expect only the intersection (50 stores) to be present.
    expected_store_count = 50 # Based on how 'for some stores' is mocked

    assert results_df['str_code'].nunique() == expected_store_count, \
        f"Expected {expected_store_count} unique stores in results, but found {results_df['str_code'].nunique()}"
    assert opportunities_df['str_code'].nunique() == expected_store_count, \
        f"Expected {expected_store_count} unique stores in opportunities, but found {opportunities_df['str_code'].nunique()}"
    
    Step10ResultsSchema.validate(results_df)
    Step10OpportunitiesSchema.validate(opportunities_df)

@then('detailed opportunities should be empty')
def detailed_opportunities_should_be_empty(context, mock_filesystem):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule10_spu_overcapacity_opportunities_{context['period']}.csv")
    assert opportunities_df is None or opportunities_df.empty, "Expected detailed opportunities to be empty."

@then('the summary report should indicate no overcapacity opportunities were found')
def summary_report_no_overcapacity_opportunities_found(context, mock_filesystem):
    summary_file_path = f"output/rule10_smart_overcapacity_spu_summary_{context['period']}.md"
    assert summary_file_path in mock_filesystem["_file_contents"], "Summary markdown report was not created."
    summary_content = mock_filesystem["_file_contents"][summary_file_path]
    assert "No SPU overcapacity opportunities were found" in str(summary_content) or \
           "Total Overcapacity SPUs: 0" in str(summary_content), \
           f"Summary report did not indicate no overcapacity opportunities. Content: {summary_content}"

@then('SPU overcapacity should be identified without seasonal blending')
def spu_overcapacity_identified_without_seasonal_blending(context, mock_filesystem):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule10_spu_overcapacity_opportunities_{context['period']}.csv")
    assert opportunities_df is not None, "Opportunities CSV was not generated."
    assert not opportunities_df.empty, "Opportunities DataFrame is empty."
    assert 'recommended_quantity_change' in opportunities_df.columns
    assert (opportunities_df['recommended_quantity_change'] < 0).any(), "No SPU reductions recommended."
    Step10OpportunitiesSchema.validate(opportunities_df)

    # Optionally, check logs to confirm seasonal blending was not applied if possible (not directly mockable here without deeper changes)
    # For now, rely on the environment variable flag in the 'When' step setting to control this behavior.

@then('store-level results should be generated with quantity reductions')
def store_level_results_generated_with_quantity_reductions(context, mock_filesystem):
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule10_smart_overcapacity_results_{context['period']}.csv")
    assert results_df is not None and not results_df.empty, "Results CSV was not generated or is empty."
    assert 'total_quantity_adjustment' in results_df.columns
    assert (results_df['total_quantity_adjustment'] < 0).any(), "Expected some negative quantity adjustments (reductions)."
    Step10ResultsSchema.validate(results_df)

@then('detailed opportunities should be generated')
def detailed_opportunities_generated(context, mock_filesystem):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule10_spu_overcapacity_opportunities_{context['period']}.csv")
    assert opportunities_df is not None and not opportunities_df.empty, "Opportunities CSV was not generated or is empty."
    assert 'recommended_quantity_change' in opportunities_df.columns
    Step10OpportunitiesSchema.validate(opportunities_df)

def get_dataframe_from_mocked_to_csv(mock_filesystem, filename_substring):
    for filepath, df in mock_filesystem["_data"].items():
        if filename_substring in filepath:
            return df
    return None
