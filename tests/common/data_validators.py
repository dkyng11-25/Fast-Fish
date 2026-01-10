"""
Data validation utilities for test data.

This module provides functions to validate test data against production data schemas
and constraints to ensure test data accurately represents production scenarios.
"""
import re
from typing import Dict, Any, List, Optional
import pandas as pd

# Regex patterns for different ID formats
STORE_CODE_PATTERN = r'^\d{5}$'  # 5-digit store codes
SPU_CODE_PATTERN = r'^[A-Z0-9]{7}$'  # 7-character alphanumeric SPU codes

class DataValidationError(ValueError):
    """Raised when data validation fails."""
    pass

def validate_store_code(store_code: str) -> bool:
    """Validate store code format.
    
    Args:
        store_code: The store code to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return bool(re.match(STORE_CODE_PATTERN, str(store_code)))

def validate_spu_code(spu_code: str) -> bool:
    """Validate SPU code format.
    
    Args:
        spu_code: The SPU code to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return bool(re.match(SPU_CODE_PATTERN, str(spu_code)))

def validate_sales_data(df: pd.DataFrame) -> List[str]:
    """Validate sales data DataFrame against expected schema and constraints.
    
    Args:
        df: DataFrame containing sales data
        
    Returns:
        List of validation error messages, empty if valid
    """
    errors = []
    
    # Check required columns
    required_columns = {'str_code', 'spu_code', 'sales_amount', 'quantity'}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}")
    
    # Validate store codes if present
    if 'str_code' in df.columns:
        invalid_store_codes = df[~df['str_code'].astype(str).str.match(STORE_CODE_PATTERN)]
        if not invalid_store_codes.empty:
            errors.append(f"Invalid store codes found: {invalid_store_codes['str_code'].tolist()}")
    
    # Validate SPU codes if present
    if 'spu_code' in df.columns:
        invalid_spu_codes = df[~df['spu_code'].astype(str).str.match(SPU_CODE_PATTERN)]
        if not invalid_spu_codes.empty:
            errors.append(f"Invalid SPU codes found: {invalid_spu_codes['spu_code'].tolist()}")
    
    # Validate numeric fields
    numeric_columns = {'sales_amount', 'quantity'}
    for col in numeric_columns.intersection(df.columns):
        if pd.api.types.is_numeric_dtype(df[col]):
            if (df[col] < 0).any():
                errors.append(f"Negative values found in {col}")
        else:
            errors.append(f"Non-numeric values found in {col}")
    
    return errors

def validate_dataframe_against_schema(
    df: pd.DataFrame, 
    schema: Dict[str, Dict[str, Any]]
) -> List[str]:
    """Validate a DataFrame against a schema definition.
    
    Args:
        df: DataFrame to validate
        schema: Dictionary defining expected columns and their properties
            Example: {
                'column_name': {
                    'type': type,
                    'nullable': bool,
                    'unique': bool,
                    'regex': str  # optional regex pattern
                }
            }
            
    Returns:
        List of validation error messages, empty if valid
    """
    errors = []
    
    # Check for missing columns
    missing_columns = set(schema.keys()) - set(df.columns)
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}")
    
    # Validate each column
    for col, col_schema in schema.items():
        if col not in df.columns:
            continue
            
        # Check type
        expected_type = col_schema.get('type')
        if expected_type and not all(isinstance(x, expected_type) or pd.isna(x) for x in df[col]):
            errors.append(f"Column '{col}' contains values not of type {expected_type.__name__}")
        
        # Check for nulls if not allowed
        if not col_schema.get('nullable', True) and df[col].isnull().any():
            errors.append(f"Column '{col}' contains null values but is marked as non-nullable")
        
        # Check uniqueness if required
        if col_schema.get('unique', False) and not df[col].is_unique:
            errors.append(f"Column '{col}' contains duplicate values but is marked as unique")
        
        # Check regex pattern if provided
        if 'regex' in col_schema and not df[col].astype(str).str.match(col_schema['regex']).all():
            errors.append(f"Column '{col}' contains values that don't match pattern: {col_schema['regex']}")
    
    return errors
