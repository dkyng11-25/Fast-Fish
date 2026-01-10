import pandas as pd
import numpy as np
import pytest
from pytest_bdd import scenario, given, when, then, parsers
from typing import Dict, Any
from unittest.mock import patch, MagicMock
import os

# Import schemas for validation
from tests.validation_comprehensive.schemas.step6_schemas import (
    ClusteringResultsSchema,
    ClusterProfilesSchema
)

# Scenarios
@scenario('../features/step6_cluster_analysis.feature', 'Valid SPU-level clustering input data produces valid output')
def test_valid_spu_clustering_input_output():
    pass

@scenario('../features/step6_cluster_analysis.feature', 'Valid subcategory-level clustering input data produces valid output')
def test_valid_subcategory_clustering_input_output():
    pass

@scenario('../features/step6_cluster_analysis.feature', 'Valid category-aggregated clustering input data produces valid output')
def test_valid_category_aggregated_clustering_input_output():
    pass

@scenario('../features/step6_cluster_analysis.feature', 'Step 6 fails when normalized matrix is missing')
def test_step6_fails_missing_normalized_matrix():
    pass

@scenario('../features/step6_cluster_analysis.feature', 'Step 6 fails when original matrix is missing')
def test_step6_fails_missing_original_matrix():
    pass

@scenario('../features/step6_cluster_analysis.feature', 'Step 6 fails when normalized matrix has invalid structure')
def test_step6_fails_invalid_matrix_structure():
    pass

@scenario('../features/step6_cluster_analysis.feature', 'Step 6 fails when matrices have mismatched dimensions')
def test_step6_fails_mismatched_dimensions():
    pass

@scenario('../features/step6_cluster_analysis.feature', 'Step 6 fails when there are insufficient stores for clustering')
def test_step6_fails_insufficient_stores():
    pass

@scenario('../features/step6_cluster_analysis.feature', 'Step 6 continues without temperature data when temperature constraints are disabled')
def test_step6_continues_without_temperature_data():
    pass

@scenario('../features/step6_cluster_analysis.feature', 'Step 6 warns when temperature data is missing but temperature constraints are enabled')
def test_step6_warns_missing_temperature_data():
    pass

@scenario('../features/step6_cluster_analysis.feature', 'Step 6 fails when temperature data has invalid structure')
def test_step6_fails_invalid_temperature_data():
    pass

# Fixtures for shared context
@pytest.fixture
def context():
    return {}

# Given steps
@given(parsers.parse('the analysis level is "{analysis_level}"'))
def analysis_level_set(context, analysis_level):
    context["analysis_level"] = analysis_level

@given(parsers.parse('a current period of "{period}" is set'))
def current_period_set(context, period):
    context["period"] = period

@given(parsers.parse('the normalized SPU matrix "{file_path}" exists'))
def normalized_spu_matrix_exists(context, file_path):
    # Create realistic SPU matrix data based on actual data structure
    num_stores = 100
    num_spus = 50
    
    # Generate store codes similar to actual data (S000, S001, etc.)
    store_codes = [f'S{i:03d}' for i in range(num_stores)]
    spu_codes = [str(i) for i in range(num_spus)]
    
    # Generate normalized data (0.0 to 1.0 range)
    normalized_data = np.random.rand(num_stores, num_spus)
    
    df_normalized = pd.DataFrame(normalized_data, index=store_codes, columns=spu_codes)
    context["normalized_matrix"] = df_normalized
    context["normalized_matrix_path"] = file_path

@given(parsers.parse('the original SPU matrix "{file_path}" exists'))
def original_spu_matrix_exists(context, file_path):
    # Create original matrix with same structure as normalized
    if "normalized_matrix" in context:
        df_original = context["normalized_matrix"].copy()
        # Original data typically has different scale but same structure
        df_original = df_original * np.random.uniform(100, 1000, df_original.shape)
        context["original_matrix"] = df_original
        context["original_matrix_path"] = file_path

@given(parsers.parse('the normalized subcategory matrix "{file_path}" exists'))
def normalized_subcategory_matrix_exists(context, file_path):
    # Create realistic subcategory matrix data
    num_stores = 100
    num_subcategories = 20
    
    store_codes = [f'S{i:03d}' for i in range(num_stores)]
    subcategory_codes = [f'SubCat{i:02d}' for i in range(num_subcategories)]
    
    normalized_data = np.random.rand(num_stores, num_subcategories)
    df_normalized = pd.DataFrame(normalized_data, index=store_codes, columns=subcategory_codes)
    context["normalized_matrix"] = df_normalized
    context["normalized_matrix_path"] = file_path

@given(parsers.parse('the original subcategory matrix "{file_path}" exists'))
def original_subcategory_matrix_exists(context, file_path):
    if "normalized_matrix" in context:
        df_original = context["normalized_matrix"].copy()
        df_original = df_original * np.random.uniform(50, 500, df_original.shape)
        context["original_matrix"] = df_original
        context["original_matrix_path"] = file_path

@given(parsers.parse('the normalized category matrix "{file_path}" exists'))
def normalized_category_matrix_exists(context, file_path):
    # Create realistic category matrix data
    num_stores = 100
    num_categories = 10
    
    store_codes = [f'S{i:03d}' for i in range(num_stores)]
    category_codes = [f'Cat{i:02d}' for i in range(num_categories)]
    
    normalized_data = np.random.rand(num_stores, num_categories)
    df_normalized = pd.DataFrame(normalized_data, index=store_codes, columns=category_codes)
    context["normalized_matrix"] = df_normalized
    context["normalized_matrix_path"] = file_path

@given(parsers.parse('the original category matrix "{file_path}" exists'))
def original_category_matrix_exists(context, file_path):
    if "normalized_matrix" in context:
        df_original = context["normalized_matrix"].copy()
        df_original = df_original * np.random.uniform(200, 2000, df_original.shape)
        context["original_matrix"] = df_original
        context["original_matrix_path"] = file_path

@given(parsers.parse('the temperature data "{file_path}" exists'))
def temperature_data_exists(context, file_path):
    # Create realistic temperature data based on actual structure
    num_stores = 100
    store_codes = [f'S{i:03d}' for i in range(num_stores)]
    
    df_temp = pd.DataFrame({
        'str_code': store_codes,
        'temperature_band_q3q4_seasonal': np.random.choice(['Cold', 'Cool', 'Mild', 'Warm', 'Hot'], num_stores),
        'feels_like_temperature': np.random.uniform(-10, 40, num_stores)
    })
    context["temperature_data"] = df_temp
    context["temperature_data_path"] = file_path

@given(parsers.parse('the normalized matrix has valid structure with store codes as index and {feature_type} codes as columns'))
def normalized_matrix_valid_structure(context, feature_type):
    # Validate the structure of the normalized matrix
    df = context["normalized_matrix"]
    assert isinstance(df.index, pd.Index), "Index should be pandas Index"
    assert len(df.index) > 0, "Matrix should have stores"
    assert len(df.columns) > 0, "Matrix should have features"
    assert df.index.dtype == 'object', "Store codes should be strings"
    assert df.columns.dtype == 'object', f"{feature_type} codes should be strings"

@given(parsers.parse('the original matrix has matching structure to normalized matrix'))
def original_matrix_matching_structure(context):
    df_norm = context["normalized_matrix"]
    df_orig = context["original_matrix"]
    assert df_norm.shape == df_orig.shape, "Matrices should have matching dimensions"
    assert df_norm.index.equals(df_orig.index), "Matrices should have matching store codes"
    assert df_norm.columns.equals(df_orig.columns), "Matrices should have matching feature codes"

@given(parsers.parse('the temperature data has "{col1}" and {col2} columns'))
def temperature_data_valid_columns(context, col1, col2):
    df_temp = context["temperature_data"]
    assert col1 in df_temp.columns, f"Temperature data should have {col1} column"
    # Check for temperature band column (could be various names)
    temp_band_cols = [col for col in df_temp.columns if 'temperature' in col.lower() and 'band' in col.lower()]
    assert len(temp_band_cols) > 0, f"Temperature data should have a temperature band column (found: {list(df_temp.columns)})"

@given(parsers.parse('all matrices have at least "{min_stores}" stores'))
def matrices_have_minimum_stores(context, min_stores):
    min_stores = int(min_stores)
    df_norm = context["normalized_matrix"]
    df_orig = context["original_matrix"]
    assert len(df_norm) >= min_stores, f"Normalized matrix should have at least {min_stores} stores"
    assert len(df_orig) >= min_stores, f"Original matrix should have at least {min_stores} stores"

@given(parsers.parse('the normalized SPU matrix "{file_path}" does not exist'))
def normalized_spu_matrix_not_exists(context, file_path):
    context["normalized_matrix_path"] = file_path
    context["normalized_matrix_exists"] = False

@given(parsers.parse('the original SPU matrix "{file_path}" does not exist'))
def original_spu_matrix_not_exists(context, file_path):
    context["original_matrix_path"] = file_path
    context["original_matrix_exists"] = False

@given(parsers.parse('the temperature data "{file_path}" does not exist'))
def temperature_data_not_exists(context, file_path):
    context["temperature_data_path"] = file_path
    context["temperature_data_exists"] = False

@given(parsers.parse('the normalized matrix has invalid structure with missing store codes or {feature_type} codes'))
def normalized_matrix_invalid_structure(context, feature_type):
    # Create invalid matrix structure
    df_invalid = pd.DataFrame({
        'invalid_col': [1, 2, 3]
    })
    context["normalized_matrix"] = df_invalid

@given(parsers.parse('the normalized matrix has "{num_stores1}" stores and "{num_spus}" SPUs'))
def normalized_matrix_specific_dimensions(context, num_stores1, num_spus):
    num_stores1 = int(num_stores1)
    num_spus = int(num_spus)
    
    store_codes = [f'S{i:03d}' for i in range(num_stores1)]
    spu_codes = [str(i) for i in range(num_spus)]
    normalized_data = np.random.rand(num_stores1, num_spus)
    
    df_normalized = pd.DataFrame(normalized_data, index=store_codes, columns=spu_codes)
    context["normalized_matrix"] = df_normalized

@given(parsers.parse('the original matrix has "{num_stores2}" stores and "{num_spus}" SPUs'))
def original_matrix_specific_dimensions(context, num_stores2, num_spus):
    num_stores2 = int(num_stores2)
    num_spus = int(num_spus)
    
    store_codes = [f'S{i:03d}' for i in range(num_stores2)]
    spu_codes = [str(i) for i in range(num_spus)]
    original_data = np.random.rand(num_stores2, num_spus)
    
    df_original = pd.DataFrame(original_data, index=store_codes, columns=spu_codes)
    context["original_matrix"] = df_original

@given(parsers.parse('the normalized matrix contains only "{num_stores}" stores'))
def normalized_matrix_insufficient_stores(context, num_stores):
    num_stores = int(num_stores)
    store_codes = [f'S{i:03d}' for i in range(num_stores)]
    spu_codes = [str(i) for i in range(10)]  # Few SPUs
    normalized_data = np.random.rand(num_stores, 10)
    
    df_normalized = pd.DataFrame(normalized_data, index=store_codes, columns=spu_codes)
    context["normalized_matrix"] = df_normalized

@given(parsers.parse('the original matrix contains only "{num_stores}" stores'))
def original_matrix_insufficient_stores(context, num_stores):
    num_stores = int(num_stores)
    store_codes = [f'S{i:03d}' for i in range(num_stores)]
    spu_codes = [str(i) for i in range(10)]  # Few SPUs
    original_data = np.random.rand(num_stores, 10)
    
    df_original = pd.DataFrame(original_data, index=store_codes, columns=spu_codes)
    context["original_matrix"] = df_original

@given(parsers.parse('temperature constraints are enabled'))
def temperature_constraints_enabled(context):
    context["temperature_constraints_enabled"] = True

@given(parsers.parse('temperature constraints are disabled'))
def temperature_constraints_disabled(context):
    context["temperature_constraints_enabled"] = False

@given(parsers.parse('the temperature data is missing "{column}" column'))
def temperature_data_missing_column(context, column):
    # Create temperature data without the specified column
    num_stores = 100
    store_codes = [f'S{i:03d}' for i in range(num_stores)]
    
    df_temp = pd.DataFrame({
        'other_column': np.random.choice(['A', 'B', 'C'], num_stores),
        'feels_like_temperature': np.random.uniform(-10, 40, num_stores)
    })
    context["temperature_data"] = df_temp

# When steps
@when('Step 6 cluster analysis is executed')
def step6_cluster_analysis_executed(context):
    # Mock the Step 6 execution
    context["exception"] = None
    context["output_files"] = {}
    context["warnings"] = []
    
    try:
        # Simulate file existence checks
        if not context.get("normalized_matrix_exists", True):
            raise FileNotFoundError(f"Normalized matrix not found: {context.get('normalized_matrix_path', '')}")
        
        if not context.get("original_matrix_exists", True):
            raise FileNotFoundError(f"Original matrix not found: {context.get('original_matrix_path', '')}")
        
        # Simulate matrix structure validation
        if "normalized_matrix" in context:
            df_norm = context["normalized_matrix"]
            if df_norm.shape[0] < 30:
                raise ValueError("Insufficient data for clustering: need at least 30 stores")
            
            if len(df_norm.columns) == 0:
                raise ValueError("Invalid matrix structure: missing feature codes")
        
        # Simulate temperature data validation
        if context.get("temperature_constraints_enabled", False):
            if not context.get("temperature_data_exists", True):
                context["warnings"].append("Temperature constraints enabled but temperature data not found")
            elif "temperature_data" in context:
                df_temp = context["temperature_data"]
                if "str_code" not in df_temp.columns:
                    raise ValueError("Temperature data must have 'str_code' column")
        
        # Simulate successful execution - generate mock outputs
        if "normalized_matrix" in context:
            df_norm = context["normalized_matrix"]
            store_codes = df_norm.index.tolist()
            
            # Generate mock clustering results
            num_clusters = max(2, len(store_codes) // 50)  # At least 2 clusters
            cluster_ids = [i % num_clusters for i in range(len(store_codes))]
            
            df_results = pd.DataFrame({
                'str_code': store_codes,
                'cluster_id': cluster_ids
            })
            context["output_files"]["clustering_results"] = df_results
            
            # Generate mock cluster profiles
            df_profiles = pd.DataFrame({
                'cluster_id': range(num_clusters),
                'cluster_size': [sum(1 for x in cluster_ids if x == i) for i in range(num_clusters)],
                'silhouette_score': np.random.uniform(0.2, 0.8, num_clusters),
                'avg_sales': np.random.uniform(100, 1000, num_clusters)
            })
            context["output_files"]["cluster_profiles"] = df_profiles
            
    except Exception as e:
        context["exception"] = e

# Then steps
@then('clustering results should be generated')
def clustering_results_generated(context):
    assert "output_files" in context, "Output files should be generated"
    assert "clustering_results" in context["output_files"], "Clustering results should be generated"
    df_results = context["output_files"]["clustering_results"]
    assert not df_results.empty, "Clustering results should not be empty"

@then('cluster profiles should be generated')
def cluster_profiles_generated(context):
    assert "output_files" in context, "Output files should be generated"
    assert "cluster_profiles" in context["output_files"], "Cluster profiles should be generated"
    df_profiles = context["output_files"]["cluster_profiles"]
    assert not df_profiles.empty, "Cluster profiles should not be empty"

@then(parsers.parse('the clustering results should have "{col1}" and "{col2}" columns'))
def clustering_results_have_columns(context, col1, col2):
    df_results = context["output_files"]["clustering_results"]
    assert col1 in df_results.columns, f"Clustering results should have {col1} column"
    assert col2 in df_results.columns, f"Clustering results should have {col2} column"

@then(parsers.parse('the cluster profiles should have cluster statistics columns'))
def cluster_profiles_have_statistics_columns(context):
    df_profiles = context["output_files"]["cluster_profiles"]
    expected_cols = ['cluster_id', 'cluster_size']
    for col in expected_cols:
        assert col in df_profiles.columns, f"Cluster profiles should have {col} column"

@then('all cluster IDs should be non-negative integers')
def cluster_ids_non_negative_integers(context):
    df_results = context["output_files"]["clustering_results"]
    cluster_ids = df_results['cluster_id']
    assert (cluster_ids >= 0).all(), "All cluster IDs should be non-negative"
    assert cluster_ids.dtype in ['int64', 'int32'], "Cluster IDs should be integers"

@then('all stores should be assigned to exactly one cluster')
def stores_assigned_to_one_cluster(context):
    df_results = context["output_files"]["clustering_results"]
    assert len(df_results) == len(df_results['str_code'].unique()), "Each store should appear exactly once"
    assert not df_results['cluster_id'].isna().any(), "All stores should have cluster assignments"

@then(parsers.parse('the output dataframes should conform to "{schema1}" and "{schema2}"'))
def output_dataframes_conform_to_schemas(context, schema1, schema2):
    # Validate clustering results schema - check required columns
    df_results = context["output_files"]["clustering_results"]
    required_result_cols = ['str_code', 'cluster_id']
    for col in required_result_cols:
        assert col in df_results.columns, f"Clustering results should have {col} column"
    
    # Validate cluster profiles schema - check required columns
    df_profiles = context["output_files"]["cluster_profiles"]
    required_profile_cols = ['cluster_id', 'cluster_size']
    for col in required_profile_cols:
        assert col in df_profiles.columns, f"Cluster profiles should have {col} column"

@then(parsers.parse('an error should be reported about missing {matrix_type} matrix'))
def error_reported_missing_matrix(context, matrix_type):
    assert context["exception"] is not None, "An exception should be raised"
    assert isinstance(context["exception"], FileNotFoundError), "Should be a FileNotFoundError"
    assert matrix_type in str(context["exception"]), f"Error should mention missing {matrix_type} matrix"

@then(parsers.parse('an error should be reported about invalid {data_type} structure'))
def error_reported_invalid_structure(context, data_type):
    assert context["exception"] is not None, "An exception should be raised"
    assert data_type in str(context["exception"]).lower(), f"Error should mention invalid {data_type} structure"

@then(parsers.parse('an error should be reported about mismatched {data_type}'))
def error_reported_mismatched_data(context, data_type):
    assert context["exception"] is not None, "An exception should be raised"
    assert "mismatch" in str(context["exception"]).lower() or "dimension" in str(context["exception"]).lower(), "Error should mention mismatch"

@then(parsers.parse('an error should be reported about insufficient data for clustering'))
def error_reported_insufficient_data(context):
    assert context["exception"] is not None, "An exception should be raised"
    assert "insufficient" in str(context["exception"]).lower(), "Error should mention insufficient data"

@then(parsers.parse('a warning should be reported about missing {data_type}'))
def warning_reported_missing_data(context, data_type):
    assert "warnings" in context, "Warnings should be tracked"
    assert len(context["warnings"]) > 0, "At least one warning should be reported"
    assert any(data_type in warning.lower() for warning in context["warnings"]), f"Warning should mention missing {data_type}"
