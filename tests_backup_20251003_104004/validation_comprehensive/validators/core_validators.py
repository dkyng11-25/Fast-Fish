#!/usr/bin/env python3
"""
Core Validation Functions

This module contains the fundamental validation functions for DataFrames and files.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandas as pd
import logging
import os
from typing import Dict, Any, List
import pandera as pa

# Set up logging
logger = logging.getLogger(__name__)


def validate_dataframe(df: pd.DataFrame, schema: pa.DataFrameModel, file_name: str = "data") -> Dict[str, Any]:
    """
    Validate a DataFrame against a Pandera schema.
    
    Args:
        df: DataFrame to validate
        schema: Pandera schema to validate against
        file_name: Name of the file being validated (for logging)
    
    Returns:
        Dictionary with validation results
    """
    try:
        validated_df = schema.validate(df)
        logger.info(f"✅ Validation passed for {file_name}")
        return {
            'status': 'valid',
            'rows': len(df),
            'columns': list(df.columns),
            'validated_df': validated_df
        }
    except pa.errors.SchemaError as e:
        logger.error(f"❌ Validation failed for {file_name}: {str(e)}")
        return {
            'status': 'invalid',
            'error': str(e),
            'failure_cases': e.failure_cases if hasattr(e, 'failure_cases') else None,
            'rows': len(df),
            'columns': list(df.columns)
        }


def validate_dataframe_flexible(df: pd.DataFrame, schema: pa.DataFrameModel, file_name: str = "data") -> Dict[str, Any]:
    """
    Validate a DataFrame against a Pandera schema with flexible column handling.
    Only validates columns that exist in the DataFrame.
    
    Args:
        df: DataFrame to validate
        schema: Pandera schema to validate against
        file_name: Name of the file being validated (for logging)
    
    Returns:
        Dictionary with validation results
    """
    try:
        # Get the schema columns
        schema_columns = schema.to_schema().columns.keys()
        
        # Filter DataFrame to only include columns that exist in both DataFrame and schema
        common_columns = [col for col in df.columns if col in schema_columns]
        
        if not common_columns:
            logger.warning(f"⚠️ No common columns found between DataFrame and schema for {file_name}")
            return {
                'status': 'skipped',
                'reason': 'no_common_columns',
                'rows': len(df),
                'columns': list(df.columns),
                'schema_columns': list(schema_columns)
            }
        
        # Create a subset DataFrame with only common columns
        df_subset = df[common_columns].copy()
        
        # Create a dynamic schema that only includes the common columns
        from pandera import DataFrameSchema
        original_schema = schema.to_schema()
        dynamic_columns = {col: original_schema.columns[col] for col in common_columns}
        dynamic_schema = DataFrameSchema(columns=dynamic_columns)
        
        # Validate the subset with the dynamic schema
        validated_df = dynamic_schema.validate(df_subset)
        logger.info(f"✅ Validation passed for {file_name} (validated {len(common_columns)} columns)")
        return {
            'status': 'valid',
            'rows': len(df),
            'columns': list(df.columns),
            'validated_columns': common_columns,
            'validated_df': validated_df
        }
    except pa.errors.SchemaError as e:
        logger.error(f"❌ Validation failed for {file_name}: {str(e)}")
        return {
            'status': 'invalid',
            'error': str(e),
            'failure_cases': e.failure_cases if hasattr(e, 'failure_cases') else None,
            'rows': len(df),
            'columns': list(df.columns)
        }
    except Exception as e:
        logger.error(f"❌ Unexpected error validating {file_name}: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'rows': len(df),
            'columns': list(df.columns)
        }


def validate_file(file_path: str, schema: pa.DataFrameModel, **read_csv_kwargs) -> Dict[str, Any]:
    """
    Validate a CSV file against a Pandera schema.
    
    Args:
        file_path: Path to the CSV file
        schema: Pandera schema to validate against
        **read_csv_kwargs: Additional arguments for pd.read_csv
    
    Returns:
        Dictionary with validation results
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return {
                'status': 'file_not_found',
                'file_path': file_path
            }
        
        df = pd.read_csv(file_path, **read_csv_kwargs)
        logger.info(f"Validating file: {file_path}")
        logger.info(f"Data shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        
        return validate_dataframe(df, schema, os.path.basename(file_path))
        
    except Exception as e:
        logger.error(f"❌ Error reading file {file_path}: {str(e)}")
        return {
            'status': 'read_error',
            'error': str(e),
            'file_path': file_path
        }


def validate_file_flexible(file_path: str, schema: pa.DataFrameModel, **read_csv_kwargs) -> Dict[str, Any]:
    """
    Validate a CSV file against a Pandera schema with flexible column handling.
    
    Args:
        file_path: Path to the CSV file
        schema: Pandera schema to validate against
        **read_csv_kwargs: Additional arguments for pd.read_csv
    
    Returns:
        Dictionary with validation results
    """
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return {
                'status': 'file_not_found',
                'file_path': file_path
            }
        
        df = pd.read_csv(file_path, **read_csv_kwargs)
        logger.info(f"Validating file: {file_path}")
        logger.info(f"Data shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        
        return validate_dataframe_flexible(df, schema, os.path.basename(file_path))
        
    except Exception as e:
        logger.error(f"❌ Error reading file {file_path}: {str(e)}")
        return {
            'status': 'read_error',
            'error': str(e),
            'file_path': file_path
        }


def validate_multiple_files(file_paths: List[str], schema: pa.DataFrameModel, **read_csv_kwargs) -> Dict[str, Dict[str, Any]]:
    """
    Validate multiple CSV files against a Pandera schema.
    
    Args:
        file_paths: List of paths to CSV files
        schema: Pandera schema to validate against
        **read_csv_kwargs: Additional arguments for pd.read_csv
    
    Returns:
        Dictionary mapping file paths to validation results
    """
    results = {}
    
    for file_path in file_paths:
        results[file_path] = validate_file(file_path, schema, **read_csv_kwargs)
    
    return results

