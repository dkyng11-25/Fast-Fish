#!/usr/bin/env python3
"""
Quality Validation Functions

This module contains functions for advanced data quality validation and checks.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandas as pd
import logging
from typing import Dict, Any, Optional, Tuple
import pandera as pa

from .core_validators import validate_dataframe

# Set up logging
logger = logging.getLogger(__name__)


def safe_validate(df: pd.DataFrame, schema: pa.DataFrameModel, file_name: str = "data") -> Tuple[Optional[pd.DataFrame], Optional[Exception]]:
    """
    Validate data with graceful error handling.
    
    Args:
        df: DataFrame to validate
        schema: Pandera schema to validate against
        file_name: Name of the file being validated
    
    Returns:
        Tuple of (validated_df, error)
    """
    try:
        validated_df = schema.validate(df)
        return validated_df, None
    except pa.errors.SchemaError as e:
        return None, e
    except Exception as e:
        return None, e


def validate_with_quality_checks(df: pd.DataFrame, schema: pa.DataFrameModel, file_name: str = "data") -> Dict[str, Any]:
    """
    Validate a DataFrame with additional data quality checks.
    
    Args:
        df: DataFrame to validate
        schema: Pandera schema to validate against
        file_name: Name of the file being validated
    
    Returns:
        Dictionary with validation results and quality checks
    """
    # Basic schema validation
    validation_result = validate_dataframe(df, schema, file_name)
    
    if validation_result['status'] != 'valid':
        return validation_result
    
    # Additional quality checks
    quality_checks = {}
    
    # Check for missing data patterns
    missing_data = df.isnull().sum()
    quality_checks['missing_data'] = {
        'columns_with_missing': missing_data[missing_data > 0].to_dict(),
        'total_missing_pct': df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
    }
    
    # Check for duplicate rows
    duplicates = df.duplicated().sum()
    quality_checks['duplicates'] = {
        'duplicate_rows': duplicates,
        'duplicate_pct': duplicates / len(df) * 100
    }
    
    # Check data types consistency
    quality_checks['data_types'] = {
        'column_types': df.dtypes.to_dict(),
        'numeric_columns': df.select_dtypes(include=['number']).columns.tolist(),
        'text_columns': df.select_dtypes(include=['object']).columns.tolist()
    }
    
    # Add quality checks to result
    validation_result['quality_checks'] = quality_checks
    
    return validation_result

