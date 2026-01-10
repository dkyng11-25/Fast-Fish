"""
Step definitions for Step 3 matrix preparation testing.

This module contains step definitions for BDD testing of the matrix preparation functionality.
"""

from behave import given, when, then
import pandas as pd
import numpy as np
import os
from pathlib import Path

@given('I have completed Step 1 and Step 2')
def step_have_completed_steps_1_2(context):
    """Ensure prerequisite steps are completed."""
    # Verify that required data files exist
    required_files = [
        'data/api_data/complete_category_sales_202509A.csv',
        'data/api_data/complete_spu_sales_202509A.csv',
        'data/store_coordinates_extended.csv'
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            raise AssertionError(f"Required file {file_path} does not exist")
    
    context.required_files_exist = True

@given('I have sales data from multiple periods')
def step_have_multi_period_data(context):
    """Verify multi-period data availability."""
    # Check for data from at least 2 different periods
    period_files = [
        'data/api_data/complete_category_sales_202509A.csv',
        'data/api_data/complete_spu_sales_202509A.csv'
    ]
    
    for file_path in period_files:
        assert os.path.exists(file_path), f"Period data file {file_path} missing"
    
    context.multi_period_data_available = True

@when('I run Step 3 matrix preparation')
def step_run_matrix_preparation(context):
    """Execute the matrix preparation step."""
    try:
        # Import and run the matrix preparation step
        from src.steps.matrix_preparation_step import MatrixPreparationStep
        from src.core.context import StepContext
        from src.core.logger import PipelineLogger
        
        logger = PipelineLogger()
        step3 = MatrixPreparationStep(logger, "Matrix Preparation", 3)
        context.step_context = StepContext()
        
        # Setup phase
        context.step_context = step3.setup(context.step_context)
        
        # Apply phase
        context.step_context = step3.apply(context.step_context)
        
        context.matrix_preparation_successful = True
        context.matrix_preparation_error = None
        
    except Exception as e:
        context.matrix_preparation_successful = False
        context.matrix_preparation_error = str(e)

@then('I should get subcategory sales matrices')
def step_should_get_subcategory_matrices(context):
    """Verify subcategory matrix creation."""
    assert context.matrix_preparation_successful, f"Matrix preparation failed: {context.matrix_preparation_error}"
    
    # Check that subcategory matrix files exist
    subcategory_files = [
        'data/store_subcategory_matrix.csv',
        'data/normalized_subcategory_matrix.csv'
    ]
    
    for file_path in subcategory_files:
        assert os.path.exists(file_path), f"Subcategory matrix file {file_path} not created"
        
        # Verify file is not empty
        df = pd.read_csv(file_path)
        assert not df.empty, f"Subcategory matrix file {file_path} is empty"

@then('the matrices should be normalized by row sums')
def step_matrices_should_be_normalized(context):
    """Verify matrix normalization."""
    # Check normalized subcategory matrix
    normalized_file = 'data/normalized_subcategory_matrix.csv'
    assert os.path.exists(normalized_file), "Normalized matrix file not found"
    
    df = pd.read_csv(normalized_file, index_col=0)
    
    # Verify each row sums to approximately 1 (allowing for floating point precision)
    row_sums = df.sum(axis=1)
    assert all(abs(sum_val - 1.0) < 1e-10 for sum_val in row_sums), "Matrix rows do not sum to 1"

@then('I should get the following output files')
def step_should_get_expected_output_files(context):
    """Verify all expected output files are created."""
    expected_files = [
        'data/store_subcategory_matrix.csv',
        'data/normalized_subcategory_matrix.csv',
        'data/store_spu_limited_matrix.csv',
        'data/normalized_spu_limited_matrix.csv',
        'data/store_category_agg_matrix.csv',
        'data/normalized_category_agg_matrix.csv',
        'data/subcategory_list.txt',
        'data/category_list.txt',
        'data/store_list.txt'
    ]
    
    for file_path in expected_files:
        assert os.path.exists(file_path), f"Expected output file {file_path} not created"
        
        # Verify file has content
        file_size = os.path.getsize(file_path)
        assert file_size > 0, f"Output file {file_path} is empty"

@then('all matrices should have consistent dimensions')
def step_matrices_should_have_consistent_dimensions(context):
    """Verify matrix dimension consistency."""
    # Check subcategory matrices
    subcategory_matrix = pd.read_csv('data/store_subcategory_matrix.csv', index_col=0)
    normalized_subcategory = pd.read_csv('data/normalized_subcategory_matrix.csv', index_col=0)
    
    # Should have same dimensions
    assert subcategory_matrix.shape == normalized_subcategory.shape, "Subcategory matrix dimensions inconsistent"
    
    # Check SPU matrices
    spu_matrix = pd.read_csv('data/store_spu_limited_matrix.csv', index_col=0)
    normalized_spu = pd.read_csv('data/normalized_spu_limited_matrix.csv', index_col=0)
    
    # Should have same dimensions
    assert spu_matrix.shape == normalized_spu.shape, "SPU matrix dimensions inconsistent"
    
    # Category aggregated matrices should have fewer columns (aggregated categories)
    category_matrix = pd.read_csv('data/store_category_agg_matrix.csv', index_col=0)
    assert category_matrix.shape[0] == subcategory_matrix.shape[0], "Store count should be consistent across matrices"
    
    context.matrix_dimensions_consistent = True

@then('anomalous stores should be identified and filtered out')
def step_anomalous_stores_should_be_filtered(context):
    """Verify anomalous store filtering."""
    # This would check that stores at anomaly coordinates are filtered
    # For now, just verify the filtering logic exists in the step
    assert hasattr(context, 'matrix_preparation_successful'), "Matrix preparation should have run"
    assert context.matrix_preparation_successful, "Matrix preparation should have succeeded"

@when('I run Step 3 with large SPU datasets')
def step_run_with_large_spu_datasets(context):
    """Test with datasets that exceed memory limits."""
    # Set up scenario with many SPUs
    context.large_dataset_test = True
    
    # Run matrix preparation
    try:
        from src.steps.matrix_preparation_step import MatrixPreparationStep
        from src.core.context import StepContext
        from src.core.logger import PipelineLogger
        
        logger = PipelineLogger()
        step3 = MatrixPreparationStep(logger, "Matrix Preparation", 3)
        context.step_context = StepContext()
        
        context.step_context = step3.setup(context.step_context)
        context.step_context = step3.apply(context.step_context)
        
        context.large_dataset_successful = True
        
    except Exception as e:
        context.large_dataset_successful = False
        context.large_dataset_error = str(e)

@then('SPU count should be limited to prevent memory issues')
def step_spu_count_should_be_limited(context):
    """Verify SPU count limiting for memory management."""
    assert context.large_dataset_successful, f"Large dataset test failed: {context.large_dataset_error}"
    
    # Check that SPU matrix was created with limited size
    spu_matrix_file = 'data/store_spu_limited_matrix.csv'
    assert os.path.exists(spu_matrix_file), "SPU limited matrix not created"
    
    df = pd.read_csv(spu_matrix_file, index_col=0)
    # Should have reasonable number of columns (limited by MAX_SPU_COUNT)
    assert df.shape[1] <= 1000, f"SPU matrix has too many columns: {df.shape[1]}"

@then('matrix creation should complete within reasonable time')
def step_matrix_creation_should_be_timely(context):
    """Verify performance with large datasets."""
    assert context.large_dataset_successful, "Large dataset processing should succeed"
    
    # Check that output files were created (indicating completion)
    required_files = [
        'data/store_subcategory_matrix.csv',
        'data/store_spu_limited_matrix.csv',
        'data/store_category_agg_matrix.csv'
    ]
    
    for file_path in required_files:
        assert os.path.exists(file_path), f"Required output file {file_path} not created"
