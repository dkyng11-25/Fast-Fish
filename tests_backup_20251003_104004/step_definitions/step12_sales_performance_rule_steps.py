
import pytest
import pandas as pd
import pandera as pa
from pytest_bdd import scenario, given, when, then, parsers
from unittest.mock import patch, MagicMock
import os
import numpy as np

# Import the main rule function and validators
from src import step12_sales_performance_rule as step12_rule
from tests.validation_comprehensive.schemas.step12_schemas import Step12ResultsSchema, Step12DetailsSchema as Step12OpportunitiesSchema

# Import src.config for mocking
import src.config as config_module


@pytest.fixture
def mock_config():
    """Fixture to mock configuration functions."""
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
    """Fixture to mock file system operations (read_csv, to_csv, exists)."""
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
            "_mock_dataframes": _mock_dataframes,
            "_mock_file_contents": _mock_file_contents # Expose for assertions
        }

@pytest.fixture
def context():
    return {}

# Helper function to generate mock SPU sales data
def _generate_spu_sales_data(str_codes, spu_codes, min_sales_volume=100.0, include_sales_amt=True, include_quantity=True, high_performance=False):
    data = []
    for str_code in str_codes:
        for spu_code in spu_codes:
            sales_amt = np.random.uniform(min_sales_volume, min_sales_volume * 5)
            if high_performance:
                sales_amt *= 2 # Double sales for high performance
            qty = int(sales_amt / np.random.uniform(20, 150)) # Realistic unit price
            record = {
                'str_code': str_code,
                'spu_code': spu_code,
            }
            if include_quantity:
                record['quantity'] = qty
            if include_sales_amt:
                record['spu_sales_amt'] = sales_amt
            data.append(record)
    return pd.DataFrame(data)

# Helper function to generate mock clustering data
def _generate_clustering_data(str_codes, num_clusters):
    data = {
        "str_code": str_codes,
        "cluster_id": [f"C_{i % num_clusters}" for i in range(len(str_codes))],
        "Cluster": [f"C_{i % num_clusters}" for i in range(len(str_codes))]
    }
    return pd.DataFrame(data)

@then('SPU-level sales performance opportunities should be identified only for stores with both sales and clustering data')
def spu_sales_performance_identified_only_for_joined_stores(context, mock_filesystem):
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"output/rule12_sales_performance_spu_results_{context['period_label']}.csv")
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"output/rule12_sales_performance_spu_details_{context['period_label']}.csv")

    assert results_df is not None and not results_df.empty, "Results CSV was not generated or is empty."
    assert opportunities_df is not None and not opportunities_df.empty, "Opportunities CSV was not generated or is empty."

    # The mocked SPU sales data is for 50 stores, while clustering is for 100.
    # With an inner join, we expect only the intersection (50 stores) to be present.
    expected_store_count = 50 # Based on how 'for some stores' is mocked in this scenario

    assert results_df['str_code'].nunique() == expected_store_count, \
        f"Expected {expected_store_count} unique stores in results, but found {results_df['str_code'].nunique()}"
    assert opportunities_df['str_code'].nunique() == expected_store_count, \
        f"Expected {expected_store_count} unique stores in opportunities, but found {opportunities_df['str_code'].nunique()}"
    
    Step12StoreResultsSchema.validate(results_df)
    Step12OpportunitiesSchema.validate(opportunities_df)

@then('SPU-level sales performance opportunities should be identified with a total quantity cap applied')
def spu_sales_performance_identified_with_total_quantity_cap_applied(context, mock_filesystem):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"output/rule12_sales_performance_spu_details_{context['period_label']}.csv")
    results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"output/rule12_sales_performance_spu_results_{context['period_label']}.csv")

    assert opportunities_df is not None and not opportunities_df.empty, "Opportunities CSV was not generated or is empty."
    assert results_df is not None and not results_df.empty, "Results CSV was not generated or is empty."

    max_qty_per_store = float(os.environ.get("MAX_TOTAL_QUANTITY_PER_STORE"))

    # Check if the total recommended quantity for any store does not exceed the cap
    store_total_qty = opportunities_df.groupby('str_code')['recommended_quantity_change'].sum()
    assert (store_total_qty <= max_qty_per_store + 0.01).all(), f"Expected all store total quantities to be less than or equal to {max_qty_per_store}, but found violations."

    Step12StoreResultsSchema.validate(results_df)
    Step12OpportunitiesSchema.validate(opportunities_df)

@then('a summary report should be created and indicate no opportunities were found')
def summary_report_no_opportunities_found(context, mock_filesystem):
    summary_file_path = f"output/rule12_sales_performance_spu_summary_{context['period_label']}.md"
    assert summary_file_path in mock_filesystem["_mock_file_contents"], "Summary markdown report was not created."
    summary_content = mock_filesystem["_mock_file_contents"][summary_file_path]
    assert "No sales performance opportunities were identified" in str(summary_content) or \
           "Total quantity increase needed: 0.0 units" in str(summary_content), \
           f"Summary report did not indicate no opportunities. Content: {summary_content}"

def get_dataframe_from_mocked_to_csv(mock_filesystem, filename_substring):
    for filepath, df in mock_filesystem["_mock_dataframes"].items():
        if filename_substring in filepath:
            return df
    return None

@scenario("../features/step12_sales_performance_rule.feature", "Rule 12 handles missing real quantity sources gracefully for SPU data")
def test_rule12_handles_missing_real_quantity_sources_gracefully_for_spu_data():
    pass

@scenario("../features/step12_sales_performance_rule.feature", "No opportunities identified when no stores underperform against cluster benchmarks")
def test_no_opportunities_identified_no_stores_underperform_against_cluster_benchmarks():
    pass

@scenario('../features/step12_sales_performance_rule.feature', 'No sales performance opportunities when all stores perform at or above cluster benchmarks with high quantity cap')
def test_no_sales_performance_high_qty_cap():
    pass

@scenario('../features/step12_sales_performance_rule.feature', 'SPU-level sales performance with strict inner join mode')
def test_spu_sales_performance_strict_inner_join():
    pass

@scenario('../features/step12_sales_performance_rule.feature', 'SPU-level sales performance with optional total quantity cap per store')
def test_spu_sales_performance_total_quantity_cap():
    pass

@scenario("../features/step12_sales_performance_rule.feature", "Successful SPU-level sales performance evaluation with positive quantity increases")
def test_successful_spu_level_sales_performance_evaluation_with_positive_quantity_increases():
    pass

@scenario("../features/step12_sales_performance_rule.feature", "Rule 12 fails due to missing SPU sales/quantity data file")
def test_rule12_fails_due_to_missing_spu_sales_quantity_data_file():
    pass

@given(parsers.parse('the current period is "{period_label}"'))
def set_current_period(context, period_label, mock_config):
    context["period_label"] = period_label
    context["yyyymm"] = period_label[:6]
    context["period"] = period_label[6:]
    os.environ["CURRENT_PERIOD_LABEL"] = period_label # Set the environment variable
    mock_config["get_current_period"].return_value = (context["yyyymm"], context["period"])
    mock_config["get_period_label"].return_value = context["period_label"]

@given(parsers.parse('minimum quantity gap is "{min_qty_gap}"'))
def minimum_quantity_gap_is(context, min_qty_gap):
    os.environ["MIN_QTY_GAP"] = str(min_qty_gap)
    context["original_min_qty_gap"] = os.environ.get("MIN_QTY_GAP")

@given(parsers.parse('maximum total quantity per store is "{max_qty:d}"'))
def maximum_total_quantity_per_store_is(context, max_qty):
    os.environ["MAX_TOTAL_QUANTITY_PER_STORE"] = str(max_qty)
    context["original_max_total_quantity_per_store"] = os.environ.get("MAX_TOTAL_QUANTITY_PER_STORE")

@given(parsers.parse('SPU sales data with "{str_col}", "{spu_col}", "{qty_col}", "{spu_sales_amt_col}" is available for {store_count:d} stores'))
def spu_sales_data_available(context, mock_config, mock_filesystem, str_col, spu_col, qty_col, spu_sales_amt_col, store_count: int = 100):
    str_codes = [f'S{i:03d}' for i in range(store_count)]
    spu_codes = [f'SPU{j}' for j in range(20)] # 20 SPUs
    df_sales = _generate_spu_sales_data(str_codes, spu_codes)
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

@given(parsers.parse('clustering results with "{str_col}" and "{cluster_col}" are available for {store_count:d} stores'))
def clustering_results_available(context, mock_config, mock_filesystem, str_col, cluster_col, store_count: int = 100):
    str_codes = [f'S{i:03d}' for i in range(store_count)]
    df_clustering = _generate_clustering_data(str_codes, 5)
    clustering_path = f"output/clustering_results_spu_{context['period_label']}.csv"
    mock_filesystem["_mock_dataframes"][clustering_path] = df_clustering
    
    original_exists_side_effect = mock_filesystem["exists"].side_effect
    def new_exists_side_effect(path):
        if path == clustering_path:
            return True
        if callable(original_exists_side_effect):
            return original_exists_side_effect(path)
        return False
    mock_filesystem["exists"].side_effect = new_exists_side_effect

    mock_config["get_output_files"].return_value = {
        'clustering_results': clustering_path
    }
    context["df_clustering"] = df_clustering

@given(parsers.parse('the join mode is "{join_mode}"'))
def set_join_mode(context, join_mode):
    os.environ["JOIN_MODE"] = join_mode
    context["original_join_mode"] = os.environ.get("JOIN_MODE")

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
def spu_sales_data_missing_real_quantity_columns(context, mock_filesystem, mock_config):
    str_codes = [f'S{i:03d}' for i in range(100)]
    spu_codes = [f'SPU{j}' for j in range(20)]
    df_sales_no_qty = _generate_spu_sales_data(str_codes, spu_codes, include_sales_amt=True, include_quantity=False)
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

@given('all stores perform at or above cluster benchmarks')
def all_stores_perform_at_or_above_cluster_benchmarks(context, mock_filesystem, mock_config):
    str_codes = [f'S{i:03d}' for i in range(100)]
    spu_codes = [f'SPU{j}' for j in range(20)]
    df_sales = _generate_spu_sales_data(str_codes, spu_codes, high_performance=True) # Generate high performing sales
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

    str_codes = [f'S{i:03d}' for i in range(100)]
    df_clustering = _generate_clustering_data(str_codes, 2)
    clustering_path = f"output/clustering_results_spu_{context['period_label']}.csv"
    mock_filesystem["_mock_dataframes"][clustering_path] = df_clustering
    
    original_exists_side_effect = mock_filesystem["exists"].side_effect
    def new_exists_side_effect(path):
        if path == clustering_path:
            return True
        if callable(original_exists_side_effect):
            return original_exists_side_effect(path)
        return False
    mock_filesystem["exists"].side_effect = new_exists_side_effect

    mock_config["get_output_files"].return_value = {
        'clustering_results': clustering_path
    }
    context["df_clustering"] = df_clustering

    # Also ensure no opportunities are found by adjusting env vars if needed
    os.environ["SALES_PERFORMANCE_THRESHOLD"] = '1.0' # Set a high threshold
    context["original_sales_performance_threshold"] = os.environ.get("SALES_PERFORMANCE_THRESHOLD")

@when('Rule 12 is executed')
def rule12_is_executed(context, mock_config, mock_filesystem):
    context["exception"] = None
    try:
        with patch('src.step12_sales_performance_rule.get_current_period', new=mock_config['get_current_period']), \
             patch('src.step12_sales_performance_rule.get_period_label', new=mock_config['get_period_label']), \
             patch('src.step12_sales_performance_rule.get_api_data_files', new=mock_config['get_api_data_files']), \
             patch('src.step12_sales_performance_rule.get_output_files', new=mock_config['get_output_files']), \
             patch('src.step12_sales_performance_rule.pd.read_csv', new=mock_filesystem['read_csv']), \
             patch('src.step12_sales_performance_rule.os.path.exists', new=mock_filesystem['exists']), \
             patch('src.step12_sales_performance_rule.os.makedirs', MagicMock(return_value=None)), \
             patch('src.step12_sales_performance_rule.pd.DataFrame.to_csv', new=mock_filesystem['to_csv']):
            
            # Update the mock config values with the current period from context
            mock_config["get_current_period"].return_value = (context["yyyymm"], context["period"])
            mock_config["get_period_label"].return_value = context["period_label"]
            
            # Dynamically set JOIN_MODE if specified in context
            if "original_join_mode" in context:
                step12_rule.JOIN_MODE = os.environ.get("JOIN_MODE")
            # Dynamically set MAX_TOTAL_QUANTITY_PER_STORE if specified in context
            if "original_max_total_quantity_per_store" in context:
                step12_rule.MAX_TOTAL_QUANTITY_PER_STORE = float(os.environ.get("MAX_TOTAL_QUANTITY_PER_STORE"))

            step12_rule.main()
    except Exception as e:
        context["exception"] = e
    finally:
        # Clean up environment variables
        if "original_join_mode" in context:
            if context["original_join_mode"] is not None:
                os.environ["JOIN_MODE"] = context["original_join_mode"]
            else:
                del os.environ["JOIN_MODE"]
        if "original_sales_performance_threshold" in context:
            if context["original_sales_performance_threshold"] is not None:
                os.environ["SALES_PERFORMANCE_THRESHOLD"] = context["original_sales_performance_threshold"]
            else:
                del os.environ["SALES_PERFORMANCE_THRESHOLD"]
        if "original_max_total_quantity_per_store" in context:
            if context["original_max_total_quantity_per_store"] is not None:
                os.environ["MAX_TOTAL_QUANTITY_PER_STORE"] = context["original_max_total_quantity_per_store"]
            else:
                del os.environ["MAX_TOTAL_QUANTITY_PER_STORE"]

@then('sales performance opportunities should be identified')
def opportunities_identified(context, mock_filesystem):
    opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"step12_sales_performance_opportunities_{context['period_label']}.csv")
    assert opportunities_df is not None, "Opportunities CSV was not generated."
    assert not opportunities_df.empty
    assert 'recommended_quantity_change' in opportunities_df.columns
    assert (opportunities_df['recommended_quantity_change'] > 0).any()
    Step12OpportunitiesSchema.validate(opportunities_df)

@then('store-level results should be generated with positive quantity increases')
def store_level_results_generated(context, mock_filesystem):
    store_results_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"step12_sales_performance_store_results_{context['period_label']}.csv")
    assert store_results_df is not None, "Store results CSV was not generated."
    assert not store_results_df.empty
    assert 'recommended_quantity_change' in store_results_df.columns
    assert (store_results_df["recommended_quantity_change"] >= 0).all()
    Step12StoreResultsSchema.validate(store_results_df)

@then('detailed opportunities should be generated')
def detailed_opportunities_generated(context, mock_filesystem):
    detailed_opportunities_df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"step12_sales_performance_detailed_opportunities_{context['period_label']}.csv")
    assert detailed_opportunities_df is not None, "Detailed opportunities CSV was not generated."
    assert not detailed_opportunities_df.empty
    assert 'recommended_quantity_change' in detailed_opportunities_df.columns
    assert (detailed_opportunities_df['recommended_quantity_change'] > 0).any()
    Step12OpportunitiesSchema.validate(detailed_opportunities_df)

@then('a summary report should be created')
def summary_report_created(context, mock_filesystem):
    summary_file_path = f"output/step12_sales_performance_summary_report_{context['period_label']}.md"
    assert summary_file_path in mock_filesystem["_mock_file_contents"], "Summary markdown report was not created."
    summary_content = mock_filesystem["_mock_file_contents"][summary_file_path]
    assert isinstance(summary_content, str) # Now stores as raw string
    assert summary_content # Check if content is not empty

@then(parsers.parse('the output dataframes should conform to "{schema_names}"'))
def output_dataframes_conform_to_schemas(context, mock_filesystem, schema_names):
    schema_map = {
        "Step12StoreResultsSchema": Step12StoreResultsSchema,
        "Step12OpportunitiesSchema": Step12OpportunitiesSchema,
    }
    for schema_name in schema_names.split(" and "):
        schema_name = schema_name.strip()
        if schema_name == "Step12StoreResultsSchema":
            df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"step12_sales_performance_store_results_{context['period_label']}.csv")
        elif schema_name == "Step12OpportunitiesSchema":
            df = get_dataframe_from_mocked_to_csv(mock_filesystem, f"step12_sales_performance_opportunities_{context['period_label']}.csv")
        else:
            raise ValueError(f"Unknown schema name: {schema_name}")

        assert df is not None, f"DataFrame for schema {schema_name} was not found."
        schema = schema_map[schema_name]
        schema.validate(df, lazy=True)

@then('no sales performance opportunities should be identified')
def no_opportunities_identified(context, mock_filesystem):
    assert get_dataframe_from_mocked_to_csv(mock_filesystem, f"step12_sales_performance_opportunities_{context['period_label']}.csv") is None or \
           get_dataframe_from_mocked_to_csv(mock_filesystem, f"step12_sales_performance_opportunities_{context['period_label']}.csv").empty
    assert get_dataframe_from_mocked_to_csv(mock_filesystem, f"step12_sales_performance_store_results_{context['period_label']}.csv") is None or \
           get_dataframe_from_mocked_to_csv(mock_filesystem, f"step12_sales_performance_store_results_{context['period_label']}.csv").empty
    assert get_dataframe_from_mocked_to_csv(mock_filesystem, f"step12_sales_performance_detailed_opportunities_{context['period_label']}.csv") is None or \
           get_dataframe_from_mocked_to_csv(mock_filesystem, f"step12_sales_performance_detailed_opportunities_{context['period_label']}.csv").empty

@then('no output files related to opportunities should be generated')
def no_output_files_generated(context, mock_filesystem):
    assert get_dataframe_from_mocked_to_csv(mock_filesystem, f"step12_sales_performance_opportunities_{context['period_label']}.csv") is None
    assert get_dataframe_from_mocked_to_csv(mock_filesystem, f"step12_sales_performance_store_results_{context['period_label']}.csv") is None
    assert get_dataframe_from_mocked_to_csv(mock_filesystem, f"step12_sales_performance_detailed_opportunities_{context['period_label']}.csv") is None
    summary_file_path = f"output/step12_sales_performance_summary_report_{context['period_label']}.md"
    assert summary_file_path not in mock_filesystem["_mock_file_contents"]

@given(parsers.parse('SPU sales data with "{str_col}", "{spu_col}", "{qty_col}" is available'))
def spu_sales_data_with_three_columns_available(context, mock_config, mock_filesystem, str_col, spu_col, qty_col):
    """SPU sales data with three specified columns is available."""
    df_sales = pd.DataFrame({
        str_col: [f'S{i:03d}' for i in range(100)],
        spu_col: [f'SPU{i%20}' for i in range(100)],
        qty_col: [10 + i for i in range(100)]
    })
    
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
def spu_sales_data_with_three_columns_available_for_store_count(context, mock_config, mock_filesystem, str_col, spu_col, qty_col, store_count):
    """SPU sales data with three specified columns is available for specified store count."""
    df_sales = pd.DataFrame({
        str_col: [f'S{i:03d}' for i in range(store_count)],
        spu_col: [f'SPU{i%20}' for i in range(store_count)],
        qty_col: [10 + i for i in range(store_count)]
    })
    
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
def clustering_results_with_two_columns_available(context, mock_config, mock_filesystem, str_col, cluster_col):
    """Clustering results with two specified columns are available."""
    df_clustering = pd.DataFrame({
        str_col: [f'S{i:03d}' for i in range(100)],
        cluster_col: [i % 5 for i in range(100)]  # 5 clusters
    })
    
    clustering_path = f"output/step6_cluster_analysis_{context['period_label']}.csv"
    mock_filesystem["_mock_dataframes"][clustering_path] = df_clustering
    
    original_exists_side_effect = mock_filesystem["exists"].side_effect
    def new_exists_side_effect(path):
        if path == clustering_path:
            return True
        if callable(original_exists_side_effect):
            return original_exists_side_effect(path)
        return False
    mock_filesystem["exists"].side_effect = new_exists_side_effect

    mock_config["get_clustering_files"].return_value.update({
        'clustering_results': clustering_path
    })
    context["df_clustering"] = df_clustering
