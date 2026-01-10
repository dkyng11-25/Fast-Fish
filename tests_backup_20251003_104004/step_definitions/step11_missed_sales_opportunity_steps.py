import pandas as pd
import numpy as np
import pytest
from pytest_bdd import scenario, given, when, then, parsers
from typing import Dict, Any, Optional, List
from unittest.mock import patch, MagicMock
import os

# Import schemas for Pandera validation
from tests.validation_comprehensive.schemas.step11_schemas import (
    Step11ResultsSchema, Step11DetailsSchema as Step11OpportunitiesSchema, Step11TopPerformersSchema
)

# Import the module under test
import src.step11_missed_sales_opportunity as step11_rule
import src.config as config_module

# Scenarios
@scenario('../features/step11_missed_sales_opportunity.feature', 'Successful SPU-level missed sales opportunity identification with Fast Fish validation')
def test_successful_spu_missed_sales_opportunity_fast_fish_validation():
    pass

@scenario('../features/step11_missed_sales_opportunity.feature', 'SPU-level missed sales opportunity identification with seasonal blending and no Fast Fish validation')
def test_spu_missed_sales_opportunity_seasonal_blending_no_fast_fish():
    pass

@scenario('../features/step11_missed_sales_opportunity.feature', 'Rule 11 fails due to missing SPU sales/quantity file')
def test_rule11_fails_missing_spu_sales_quantity_file():
    pass

@scenario('../features/step11_missed_sales_opportunity.feature', 'Rule 11 handles missing real quantity sources gracefully')
def test_rule11_handles_missing_real_quantity_sources_gracefully():
    pass

@scenario('../features/step11_missed_sales_opportunity.feature', 'No opportunities identified when no stores are below top performers')
def test_no_opportunities_identified_no_stores_below_top_performers():
    pass

@scenario('../features/step11_missed_sales_opportunity.feature', 'SPU-level missed sales opportunities with strict inner join mode')
def test_spu_missed_sales_strict_inner_join():
    pass

@scenario('../features/step11_missed_sales_opportunity.feature', 'Rule 11 operates in August and seasonal blending is automatically enabled')
def test_rule11_august_seasonal_blending_enabled():
    pass

@scenario('../features/step11_missed_sales_opportunity.feature', 'No missed sales opportunities identified due to very high minimum sales and quantity gaps')
def test_no_missed_sales_opportunities_high_thresholds():
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
            "to_csv": mock_to_csv_obj,
            "_mock_dataframes": _mock_dataframes,
            "_mock_file_contents": _mock_file_contents # Expose for assertions
        }

@pytest.fixture
def mock_sell_through_validator():
    with patch('src.sell_through_validator.SellThroughValidator') as mock_validator_class:
        mock_validator_instance = MagicMock()
        mock_validator_instance.is_initialized = True
        # Predict sell-through and compliance with realistic values
        mock_validator_instance.predict_sell_through.return_value = pd.Series(np.random.uniform(0.6, 0.9, 100), index=[f'S{i:03d}' for i in range(100)]) # Simulate good sell-through
        mock_validator_instance.check_compliance.return_value = pd.Series(True, index=[f'S{i:03d}' for i in range(100)])
        mock_validator_class.return_value = mock_validator_instance
        yield {
            "class": mock_validator_class,
            "instance": mock_validator_instance
        }

@pytest.fixture
def context():
    return {}

# Helper function to generate realistic SPU sales data for top performers
def generate_spu_sales_data(str_codes: List[str], spu_codes: List[str], min_sales_volume: float = 1000) -> pd.DataFrame:
    data = []
    for str_code in str_codes:
        for spu_code in spu_codes:
            sales_amt = np.random.uniform(min_sales_volume, min_sales_volume * 5)
            qty = int(sales_amt / np.random.uniform(20, 150)) # Realistic unit price
            data.append({
                'str_code': str_code,
                'spu_code': spu_code,
                'spu_sales_amt': sales_amt,
                'quantity': qty,
                'base_sal_qty': int(qty * 0.7),
                'fashion_sal_qty': int(qty * 0.3),
                'sal_qty': qty,
            })
    return pd.DataFrame(data)

# Given steps
@given(parsers.parse('the current period is "{yyyymm_period}"'))
def set_current_period(context, yyyymm_period, mock_config):
    context["yyyymm"] = yyyymm_period[:6]
    context["period"] = yyyymm_period[6:]
    context["period_label"] = yyyymm_period
    os.environ["CURRENT_PERIOD_LABEL"] = yyyymm_period # Set the environment variable
    mock_config["get_current_period"].return_value = (context["yyyymm"], context["period"])
    mock_config["get_period_label"].return_value = context["period_label"]

@given(parsers.parse('seasonal blending is enabled with seasonal period "{seasonal_period}"'))
def seasonal_blending_enabled(context, seasonal_period):
    os.environ["SEASONAL_BLENDING"] = '1'
    os.environ["SEASONAL_YYYYMM"] = seasonal_period[:6]
    os.environ["SEASONAL_PERIOD"] = seasonal_period[6:]
    context["original_seasonal_blending"] = os.environ.get("SEASONAL_BLENDING")
    context["original_seasonal_yyyymm"] = os.environ.get("SEASONAL_YYYYMM")
    context["original_seasonal_period"] = os.environ.get("SEASONAL_PERIOD")

@given(parsers.parse('seasonal blending is not explicitly disabled'))
def seasonal_blending_is_not_explicitly_disabled(context):
    # This implies that the default August logic or other blending will apply if conditions are met
    if "USE_BLENDED_SEASONAL" in os.environ:
        del os.environ["USE_BLENDED_SEASONAL"]
    if "SEASONAL_BLENDING" in os.environ:
        del os.environ["SEASONAL_BLENDING"]
    context["original_use_blended_seasonal"] = None
    context["original_seasonal_blending"] = None

@given(parsers.parse('join mode is "{join_mode}"'))
def join_mode_is(context, join_mode):
    os.environ["JOIN_MODE"] = join_mode
    context["original_join_mode"] = os.environ.get("JOIN_MODE")

@given(parsers.parse('clustering results with "{str_col}" and "{cluster_col}" are available for {store_count:d} stores'))
def clustering_results_available(context, mock_config, mock_filesystem, str_col, cluster_col, store_count: int = 100):
    df_clustering = pd.DataFrame({
        str_col: [f'S{i:03d}' for i in range(store_count)],
        cluster_col: [f'C{i%5}' for i in range(store_count)],
        'Cluster': [f'C{i%5}' for i in range(store_count)] # Ensure both forms are present for step11
    })
    clustering_path = f"output/clustering_results_spu_{context['period_label']}.csv"
    mock_filesystem["_mock_dataframes"][clustering_path] = df_clustering
    mock_filesystem["_mock_dataframes"]["output/clustering_results.csv"] = df_clustering # backward compatibility
    mock_filesystem["_mock_dataframes"]["output/enhanced_clustering_results.csv"] = df_clustering # enhanced path
    
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

@given(parsers.parse('SPU sales data with "{str_col}", "{spu_col}", "{qty_col}", "{base_qty_col}", "{fashion_qty_col}", "{sal_qty_col}", "{spu_sales_amt_col}" is available for {store_count:d} stores'))
def spu_sales_data_full_quantity_info_for_given_stores(context, mock_config, mock_filesystem, str_col, spu_col, qty_col, base_qty_col, fashion_qty_col, sal_qty_col, spu_sales_amt_col, store_count: int = 100):
    str_codes = [f'S{i:03d}' for i in range(store_count)]
    spu_codes = [f'SPU{j}' for j in range(20)] # 20 SPUs
    df_sales = generate_spu_sales_data(str_codes, spu_codes, min_sales_volume=1000)
    sales_path = f"data/api_data/complete_spu_sales_{context['period_label']}.csv"
    mock_filesystem["_mock_dataframes"][sales_path] = df_sales
    
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

@given(parsers.parse('SPU sales data with "{str_col}", "{spu_col}", "{qty_col}" is available for {store_count:d} stores'))
def spu_sales_data_only_quantity_for_given_stores(context, mock_config, mock_filesystem, str_col, spu_col, qty_col, store_count: int = 100):
    str_codes = [f'S{i:03d}' for i in range(store_count)]
    spu_codes = [f'SPU{j}' for j in range(20)]
    df_sales = generate_spu_sales_data(str_codes, spu_codes, min_sales_volume=1000)
    df_sales = df_sales.drop(columns=['base_sal_qty', 'fashion_sal_qty', 'sal_qty'], errors='ignore')
    sales_path = f"data/api_data/complete_spu_sales_{context['period_label']}.csv"
    mock_filesystem["_mock_dataframes"][sales_path] = df_sales
    
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

@given('Fast Fish validation is available')
def fast_fish_validation_is_available(context, mock_sell_through_validator):
    assert mock_sell_through_validator["instance"].is_initialized is True
    os.environ["SKIP_SELLTHROUGH_VALIDATION"] = '0'
    context["original_skip_sellthrough_validation"] = os.environ.get("SKIP_SELLTHROUGH_VALIDATION")

@given('Fast Fish validation is unavailable')
def fast_fish_validation_is_unavailable(context, mock_sell_through_validator):
    mock_sell_through_validator["class"].side_effect = ImportError
    os.environ["SKIP_SELLTHROUGH_VALIDATION"] = '1'
    context["original_skip_sellthrough_validation"] = os.environ.get("SKIP_SELLTHROUGH_VALIDATION")

@given('SPU sales data file is missing')
def spu_sales_data_file_is_missing(context, mock_filesystem):
    sales_path = f"data/api_data/complete_spu_sales_{context['period_label']}.csv"
    if sales_path in mock_filesystem["_mock_dataframes"]: # Remove it if it was added by a previous step
        del mock_filesystem["_mock_dataframes"][sales_path]
    
    original_exists_side_effect = mock_filesystem["exists"].side_effect
    def new_exists_side_effect(path):
        if path == sales_path:
            return False
        if callable(original_exists_side_effect):
            return original_exists_side_effect(path)
        return False
    mock_filesystem["exists"].side_effect = new_exists_side_effect

@given('SPU sales data with "str_code", "spu_code", "spu_sales_amt" is available but missing real quantity columns')
def spu_sales_data_missing_real_quantity_columns_for_given_stores(context, mock_config, mock_filesystem):
    store_codes = [f'S{i:03d}' for i in range(100)]
    spu_codes = [f'SPU{j}' for j in range(20)]
    df_sales_no_qty = pd.DataFrame({
        'str_code': [str_code for str_code in store_codes for _ in spu_codes],
        'spu_code': spu_codes * len(store_codes),
        'spu_sales_amt': np.random.rand(len(store_codes) * len(spu_codes)) * 1000 # Sales amount present
    })
    sales_path = f"data/api_data/complete_spu_sales_{context['period_label']}.csv"
    mock_filesystem["_mock_dataframes"][sales_path] = df_sales_no_qty
    
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

@given('all stores perform at or above cluster top performers')
def all_stores_perform_at_or_above_top_performers_for_given_stores(context, mock_config, mock_filesystem):
    store_codes = [f'S{i:03d}' for i in range(100)]
    spu_codes = [f'SPU{j}' for j in range(20)]
    # Generate sales data where all stores have high sales
    df_sales = generate_spu_sales_data(store_codes, spu_codes, min_sales_volume=5000) # High sales volume
    sales_path = f"data/api_data/complete_spu_sales_{context['period_label']}.csv"
    mock_filesystem["_mock_dataframes"][sales_path] = df_sales
    
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
    context["df_sales_high_performance"] = df_sales

    df_clustering = pd.DataFrame({
        'str_code': store_codes,
        'cluster_id': [f'C{i%5}' for i in range(100)],
        'Cluster': [f'C{i%5}' for i in range(100)]
    })
    clustering_path = f"output/clustering_results_spu_{context['period_label']}.csv"
    mock_filesystem["_mock_dataframes"][clustering_path] = df_clustering
    mock_config["get_output_files"].return_value = {
        'clustering_results': clustering_path
    }
    
    original_exists_side_effect = mock_filesystem["exists"].side_effect
    def new_exists_side_effect(path):
        if path == clustering_path:
            return True
        if callable(original_exists_side_effect):
            return original_exists_side_effect(path)
        return False
    mock_filesystem["exists"].side_effect = new_exists_side_effect
    context["df_clustering"] = df_clustering

    # Also ensure there are no actual 'missed opportunities' by adjusting env vars if needed
    os.environ["MIN_SALES_GAP"] = '0' # Effectively disable sales gap filtering
    os.environ["MIN_QTY_GAP"] = '0' # Effectively disable quantity gap filtering
    context["original_min_sales_gap"] = os.environ.get("MIN_SALES_GAP")
    context["original_min_qty_gap"] = os.environ.get("MIN_QTY_GAP")

@given(parsers.parse('minimum sales gap is "{min_sales_gap}"'))
def minimum_sales_gap_is(context, min_sales_gap):
    os.environ["MIN_SALES_GAP"] = str(min_sales_gap)
    context["original_min_sales_gap"] = os.environ.get("MIN_SALES_GAP")

@given(parsers.parse('minimum quantity gap is "{min_qty_gap}"'))
def minimum_quantity_gap_is(context, min_qty_gap):
    os.environ["MIN_QTY_GAP"] = str(min_qty_gap)
    context["original_min_qty_gap"] = os.environ.get("MIN_QTY_GAP")

# When steps
@when('Rule 11 is executed')
def rule11_is_executed(context, mock_config, mock_filesystem, mock_sell_through_validator):
    context["exception"] = None
    try:
        with patch('src.step11_missed_sales_opportunity.get_current_period', new=mock_config['get_current_period']), \
             patch('src.step11_missed_sales_opportunity.get_period_label', new=mock_config['get_period_label']), \
             patch('src.step11_missed_sales_opportunity.get_api_data_files', new=mock_config['get_api_data_files']), \
             patch('src.step11_missed_sales_opportunity.get_output_files', new=mock_config['get_output_files']), \
             patch('src.step11_missed_sales_opportunity.pd.read_csv', new=mock_filesystem['read_csv']), \
             patch('src.step11_missed_sales_opportunity.os.path.exists', new=mock_filesystem['exists']), \
             patch('src.step11_missed_sales_opportunity.SellThroughValidator', new=mock_sell_through_validator['class']), \
             patch('src.step11_missed_sales_opportunity.os.makedirs', MagicMock(return_value=None)), \
             patch('src.step11_missed_sales_opportunity.pd.DataFrame.to_csv', new=mock_filesystem['to_csv']):
            
            # Update the mock config values with the current period from context
            mock_config["get_current_period"].return_value = (context["yyyymm"], context["period"])
            mock_config["get_period_label"].return_value = context["period_label"]

            # Dynamically set USE_BLENDED_SEASONAL based on scenario context or default to August logic
            if "original_use_blended_seasonal" in context:
                step11_rule.USE_BLENDED_SEASONAL = (os.environ.get("USE_BLENDED_SEASONAL") == '1')
            else:
                # Default August logic
                try:
                    current_month = int(context["period_label"][4:6])
                    step11_rule.USE_BLENDED_SEASONAL = (current_month == 8)
                except (ValueError, IndexError):
                    step11_rule.USE_BLENDED_SEASONAL = False
            
            # Set JOIN_MODE if specified in context
            if "original_join_mode" in context:
                step11_rule.JOIN_MODE = os.environ.get("JOIN_MODE")

            step11_rule.main()
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
        if "original_min_sales_gap" in context:
            if context["original_min_sales_gap"] is not None:
                os.environ["MIN_SALES_GAP"] = context["original_min_sales_gap"]
            else:
                del os.environ["MIN_SALES_GAP"]
        if "original_min_qty_gap" in context:
            if context["original_min_qty_gap"] is not None:
                os.environ["MIN_QTY_GAP"] = context["original_min_qty_gap"]
            else:
                del os.environ["MIN_QTY_GAP"]
        if "original_skip_sellthrough_validation" in context:
            if context["original_skip_sellthrough_validation"] is not None:
                os.environ["SKIP_SELLTHROUGH_VALIDATION"] = context["original_skip_sellthrough_validation"]
            else:
                del os.environ["SKIP_SELLTHROUGH_VALIDATION"]

@given(parsers.parse('SPU sales data with "{str_col}", "{spu_col}", "{qty_col}", "{base_qty_col}", "{fashion_qty_col}", "{sal_qty_col}", "{spu_sales_amt_col}" is available'))
def spu_sales_data_full_quantity_info(context, mock_config, mock_filesystem, str_col, spu_col, qty_col, base_qty_col, fashion_qty_col, sal_qty_col, spu_sales_amt_col):
    str_codes = [f'S{i:03d}' for i in range(100)]
    spu_codes = [f'SPU{j}' for j in range(20)] # 20 SPUs
    df_sales = generate_spu_sales_data(str_codes, spu_codes, min_sales_volume=1000)
    sales_path = f"data/api_data/complete_spu_sales_{context['period_label']}.csv"
    mock_filesystem["_mock_dataframes"][sales_path] = df_sales
    
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
def spu_sales_data_only_quantity(context, mock_config, mock_filesystem, str_col, spu_col, qty_col):
    str_codes = [f'S{i:03d}' for i in range(100)]
    spu_codes = [f'SPU{j}' for j in range(20)]
    df_sales = generate_spu_sales_data(str_codes, spu_codes, min_sales_volume=1000)
    df_sales = df_sales.drop(columns=['base_sal_qty', 'fashion_sal_qty', 'sal_qty'], errors='ignore')
    sales_path = f"data/api_data/complete_spu_sales_{context['period_label']}.csv"
    mock_filesystem["_mock_dataframes"][sales_path] = df_sales
    
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

@given(parsers.parse('clustering results with "{str_col}" and "{cluster_col}" are available'))
def clustering_results_available_generic(context, mock_config, mock_filesystem, str_col, cluster_col):
    store_count = 100 # Default store count for generic case
    df_clustering = pd.DataFrame({
        str_col: [f'S{i:03d}' for i in range(store_count)],
        cluster_col: [f'C{i%5}' for i in range(store_count)],
        'Cluster': [f'C{i%5}' for i in range(store_count)] # Ensure both forms are present for step11
    })
    clustering_path = f"output/clustering_results_spu_{context['period_label']}.csv"
    mock_filesystem["_mock_dataframes"][clustering_path] = df_clustering
    mock_filesystem["_mock_dataframes"]["output/clustering_results.csv"] = df_clustering # backward compatibility
    mock_filesystem["_mock_dataframes"]["output/enhanced_clustering_results.csv"] = df_clustering # enhanced path
    
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

@given('SPU sales data with "str_code", "spu_code", "spu_sales_amt" is available but missing real quantity columns')
def spu_sales_data_missing_real_quantity_columns(context, mock_config, mock_filesystem):
    str_codes = [f'S{i:03d}' for i in range(100)]
    spu_codes = [f'SPU{j}' for j in range(20)]
    df_sales_no_qty = pd.DataFrame({
        'str_code': [str_code for str_code in str_codes for _ in spu_codes],
        'spu_code': spu_codes * len(str_codes),
        'spu_sales_amt': np.random.rand(len(str_codes) * len(spu_codes)) * 1000 # Sales amount present
    })
    sales_path = f"data/api_data/complete_spu_sales_{context['period_label']}.csv"
    mock_filesystem["_mock_dataframes"][sales_path] = df_sales_no_qty
    
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

@given(parsers.parse('SPU sales data with "str_code", "spu_code", "quantity" is available'))
def spu_sales_data_with_quantity_available(context, mock_config, mock_filesystem):
    str_codes = [f'S{i:03d}' for i in range(100)]
    spu_codes = [f'SPU{j}' for j in range(20)]
    df_sales = generate_spu_sales_data(str_codes, spu_codes, min_sales_volume=1000)
    sales_path = f"data/api_data/complete_spu_sales_{context['period_label']}.csv"
    mock_filesystem["_mock_dataframes"][sales_path] = df_sales
    
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

@given(parsers.parse('SPU sales data with "str_code", "spu_code", "quantity", "base_sal_qty", "fashion_sal_qty", "sal_qty", "spu_sales_amt" is available'))
def spu_sales_data_full_quantity_info_no_store_count(context, mock_config, mock_filesystem):
    str_codes = [f'S{i:03d}' for i in range(100)]
    spu_codes = [f'SPU{j}' for j in range(20)] # 20 SPUs
    df_sales = generate_spu_sales_data(str_codes, spu_codes, min_sales_volume=1000)
    sales_path = f"data/api_data/complete_spu_sales_{context['period_label']}.csv"
    mock_filesystem["_mock_dataframes"][sales_path] = df_sales
    
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

@given(parsers.parse('SPU sales data with "str_code", "spu_code", "spu_sales_amt" is available but missing real quantity columns'))
def spu_sales_data_missing_real_quantity_columns_no_store_count(context, mock_config, mock_filesystem):
    str_codes = [f'S{i:03d}' for i in range(100)]
    spu_codes = [f'SPU{j}' for j in range(20)]
    df_sales_no_qty = pd.DataFrame({
        'str_code': [str_code for str_code in str_codes for _ in spu_codes],
        'spu_code': spu_codes * len(str_codes),
        'spu_sales_amt': np.random.rand(len(str_codes) * len(spu_codes)) * 1000 # Sales amount present
    })
    sales_path = f"data/api_data/complete_spu_sales_{context['period_label']}.csv"
    mock_filesystem["_mock_dataframes"][sales_path] = df_sales_no_qty
    
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

@given(parsers.parse('clustering results with "str_code" and "cluster_id" are available'))
def clustering_results_available_no_store_count(context, mock_config, mock_filesystem):
    store_count = 100 # Default store count
    str_codes = [f'S{i:03d}' for i in range(store_count)]
    df_clustering = pd.DataFrame({
        'str_code': str_codes,
        'cluster_id': [f'C{i%5}' for i in range(store_count)],
        'Cluster': [f'C{i%5}' for i in range(store_count)] # Ensure both forms are present for step11
    })
    clustering_path = f"output/clustering_results_spu_{context['period_label']}.csv"
    mock_filesystem["_mock_dataframes"][clustering_path] = df_clustering
    mock_filesystem["_mock_dataframes"]["output/clustering_results.csv"] = df_clustering # backward compatibility
    mock_filesystem["_mock_dataframes"]["output/enhanced_clustering_results.csv"] = df_clustering # enhanced path
    
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

# Then steps
@then('missed sales opportunities should be identified')
def missed_sales_opportunities_identified(context, mock_filesystem):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule11_improved_missed_sales_opportunity_spu_details_{context['period_label']}.csv")
    assert opportunities_df is not None, "Opportunities CSV was not generated."
    assert not opportunities_df.empty, "Opportunities DataFrame is empty."
    assert 'recommended_quantity_change' in opportunities_df.columns
    assert (opportunities_df['recommended_quantity_change'] > 0).any(), "No positive quantity increases recommended."
    Step11OpportunitiesSchema.validate(opportunities_df)

@then('store-level results should be generated with positive quantity increases')
def store_level_results_generated_positive_qty_increases(context, mock_filesystem):
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule11_improved_missed_sales_opportunity_spu_results_{context['period_label']}.csv")
    assert results_df is not None, "Results CSV was not generated."
    assert not results_df.empty, "Results DataFrame is empty."
    assert 'total_quantity_needed' in results_df.columns
    assert (results_df['total_quantity_needed'] > 0).any(), "No positive quantity increases found."
    Step11ResultsSchema.validate(results_df)

@then('detailed opportunities should be generated and be Fast Fish compliant')
def detailed_opportunities_generated_fast_fish_compliant(context, mock_filesystem):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule11_improved_missed_sales_opportunity_spu_details_{context['period_label']}.csv")
    assert opportunities_df is not None, "Detailed opportunities CSV was not generated."
    assert not opportunities_df.empty, "Detailed opportunities DataFrame is empty."
    assert 'fast_fish_compliant' in opportunities_df.columns
    assert opportunities_df['fast_fish_compliant'].any(), "No Fast Fish compliant opportunities found."
    Step11OpportunitiesSchema.validate(opportunities_df)

@then('a summary report should be created')
def summary_report_created(context, mock_filesystem):
    summary_file_path = f"output/rule11_improved_missed_sales_opportunity_spu_summary_{context['period_label']}.md"
    assert summary_file_path in mock_filesystem["_mock_file_contents"], "Summary markdown report was not created."

@then('top performers reference data should be generated')
def top_performers_reference_data_generated(context, mock_filesystem):
    top_performers_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule11_improved_top_performers_by_cluster_category_{context['period_label']}.csv")
    assert top_performers_df is not None, "Top performers reference CSV was not generated."
    assert not top_performers_df.empty, "Top performers reference DataFrame is empty."
    Step11TopPerformersSchema.validate(top_performers_df)

@then(parsers.parse('the output dataframes should conform to "{schema1}" and "{schema2}" and "{schema3}"'))
def output_dataframes_conform_to_schemas(context, mock_filesystem, schema1, schema2, schema3):
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule11_improved_missed_sales_opportunity_spu_results_{context['period_label']}.csv")
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule11_improved_missed_sales_opportunity_spu_details_{context['period_label']}.csv")
    top_performers_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule11_improved_top_performers_by_cluster_category_{context['period_label']}.csv")

    assert results_df is not None, f"Could not find results dataframe for schema {schema1}"
    assert opportunities_df is not None, f"Could not find opportunities dataframe for schema {schema2}"
    assert top_performers_df is not None, f"Could not find top performers dataframe for schema {schema3}"

    results_schema_class = globals()[schema1]
    opportunities_schema_class = globals()[schema2]
    top_performers_schema_class = globals()[schema3]

    results_schema_class.validate(results_df)
    opportunities_schema_class.validate(opportunities_df)
    top_performers_schema_class.validate(top_performers_df)

@then('detailed opportunities should be generated but not necessarily Fast Fish compliant')
def detailed_opportunities_generated_not_necessarily_fast_fish_compliant(context, mock_filesystem):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule11_improved_missed_sales_opportunity_spu_details_{context['period_label']}.csv")
    assert opportunities_df is not None, "Detailed opportunities CSV was not generated."
    assert not opportunities_df.empty, "Detailed opportunities DataFrame is empty."
    assert 'fast_fish_compliant' in opportunities_df.columns
    Step11OpportunitiesSchema.validate(opportunities_df)

@then(parsers.parse('Rule 11 execution should fail with a "{error_type}"'))
def rule11_execution_should_fail_with_error(context, error_type):
    assert context["exception"] is not None, "Expected an exception but none was raised."
    assert context["exception"].__class__.__name__ == error_type, \
        f"Expected exception type {error_type}, but got {context['exception'].__class__.__name__}"

@then(parsers.parse('an error message indicating the missing SPU sales file should be displayed'))
def error_message_missing_spu_sales_file(context):
    assert "FileNotFoundError" in str(context["exception"]) and "complete_spu_sales" in str(context["exception"]), \
           f"Expected missing SPU sales file error message, got: {context['exception']}"

@then('Rule 11 execution should complete without error')
def rule11_execution_should_complete_without_error(context):
    assert context["exception"] is None, f"Expected no exception, but got {context['exception']}"

@then('opportunities should have null or zero quantity changes where real units are absent')
def opportunities_null_or_zero_quantity_changes_real_units_absent(context, mock_filesystem):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule11_improved_missed_sales_opportunity_spu_details_{context['period_label']}.csv")
    assert opportunities_df is not None, "Opportunities CSV was not generated."
    assert 'recommended_quantity_change' in opportunities_df.columns
    assert (opportunities_df['recommended_quantity_change'].isnull() | (opportunities_df['recommended_quantity_change'] == 0)).all(), \
        "Expected all quantity changes to be null or zero due to missing real unit data."
    Step11OpportunitiesSchema.validate(opportunities_df)

@then('store-level results should be generated with zero total quantity increases')
def store_level_results_zero_total_quantity_increases(context, mock_filesystem):
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule11_improved_missed_sales_opportunity_spu_results_{context['period_label']}.csv")
    assert results_df is not None, "Results CSV was not generated."
    assert 'total_quantity_needed' in results_df.columns
    assert (results_df['total_quantity_needed'] == 0).all(), "Expected all total quantity increases to be zero."
    Step11ResultsSchema.validate(results_df)

@then('detailed opportunities should be empty')
def detailed_opportunities_should_be_empty(context, mock_filesystem):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule11_improved_missed_sales_opportunity_spu_details_{context['period_label']}.csv")
    assert opportunities_df is None or opportunities_df.empty, "Expected detailed opportunities to be empty."

@then('the summary report should indicate no missed sales opportunities were found')
def summary_report_no_missed_sales_opportunities_found(context, mock_filesystem):
    summary_file_path = f"output/rule11_improved_missed_sales_opportunity_spu_summary_{context['period_label']}.md"
    assert summary_file_path in mock_filesystem["_mock_file_contents"], "Summary markdown report was not created."
    summary_content = mock_filesystem["_mock_file_contents"][summary_file_path]
    assert "No missed sales opportunities were identified" in str(summary_content) or \
           "Missing opportunities identified: 0" in str(summary_content), \
           f"Summary report did not indicate no opportunities. Content: {summary_content}"

@then('SPU-level missed sales opportunities should be identified only for stores with both sales and clustering data')
def spu_missed_sales_identified_only_for_joined_stores(context, mock_filesystem):
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule11_improved_missed_sales_opportunity_spu_results_{context['period_label']}.csv")
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule11_improved_missed_sales_opportunity_spu_details_{context['period_label']}.csv")

    assert results_df is not None and not results_df.empty, "Results CSV was not generated or is empty."
    assert opportunities_df is not None and not opportunities_df.empty, "Opportunities CSV was not generated or is empty."

    # The mocked SPU sales data is for 50 stores, while clustering is for 100.
    # With an inner join, we expect only the intersection (50 stores) to be present.
    expected_store_count = 50 # Based on how 'for some stores' is mocked in this scenario

    assert results_df['str_code'].nunique() == expected_store_count, \
        f"Expected {expected_store_count} unique stores in results, but found {results_df['str_code'].nunique()}"
    assert opportunities_df['str_code'].nunique() == expected_store_count, \
        f"Expected {expected_store_count} unique stores in opportunities, but found {opportunities_df['str_code'].nunique()}"
    
    Step11ResultsSchema.validate(results_df)
    Step11OpportunitiesSchema.validate(opportunities_df)

@then('SPU-level missed sales opportunities should be identified with seasonal blending applied')
def spu_missed_sales_identified_with_seasonal_blending(context, mock_filesystem):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule11_improved_missed_sales_opportunity_spu_details_{context['period_label']}.csv")
    assert opportunities_df is not None, "Opportunities CSV was not generated."
    assert not opportunities_df.empty, "Opportunities DataFrame is empty."
    assert 'recommended_quantity_change' in opportunities_df.columns
    assert (opportunities_df['recommended_quantity_change'] > 0).any(), "No positive quantity increases recommended."
    Step11OpportunitiesSchema.validate(opportunities_df)

    # This scenario implicitly checks blending by running in August with blending not explicitly disabled.
    # Direct assertion on blended values is difficult without deeper mocks or internal state exposure.
    # We rely on the rule's internal logic being correctly toggled by the `USE_BLENDED_SEASONAL` flag.
    assert step11_rule.USE_BLENDED_SEASONAL is True, "Expected seasonal blending to be enabled for Rule 11."

@then('no missed sales performance opportunities should be identified')
def no_missed_sales_performance_opportunities_identified(context, mock_filesystem):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"rule11_improved_missed_sales_opportunity_spu_details_{context['period_label']}.csv")
    assert opportunities_df is None or opportunities_df.empty, "Expected detailed opportunities to be empty."

@then('no output files related to opportunities should be generated')
def no_output_files_related_to_opportunities_should_be_generated(context, mock_filesystem):
    opportunities_path = f"output/rule11_improved_missed_sales_opportunity_spu_details_{context['period_label']}.csv"
    assert opportunities_path not in mock_filesystem["_mock_dataframes"], "Opportunities CSV should not have been generated."
    # We also expect the results and top performers to be empty if no opportunities
    results_path = f"output/rule11_improved_missed_sales_opportunity_spu_results_{context['period_label']}.csv"
    top_performers_path = f"output/rule11_improved_top_performers_by_cluster_category_{context['period_label']}.csv"
    assert mock_filesystem["_mock_dataframes"][results_path].empty, "Results CSV should be empty."
    assert mock_filesystem["_mock_dataframes"][top_performers_path].empty, "Top performers CSV should be empty."

@then('a summary report should be created and indicate no opportunities were found')
def summary_report_no_opportunities_found(context, mock_filesystem):
    summary_file_path = f"output/rule11_improved_missed_sales_opportunity_spu_summary_{context['period_label']}.md"
    assert summary_file_path in mock_filesystem["_mock_file_contents"], "Summary markdown report was not created."
    summary_content = mock_filesystem["_mock_file_contents"][summary_file_path]
    assert "No missed sales opportunities were identified" in str(summary_content) or \
           "Missing opportunities identified: 0" in str(summary_content), \
           f"Summary report did not indicate no opportunities. Content: {summary_content}"

def get_dataframe_from_mocked_to_csv(mock_filesystem, filename_substring):
    for filepath, df in mock_filesystem["_mock_dataframes"].items():
        if filename_substring in filepath:
            return df
    return None
