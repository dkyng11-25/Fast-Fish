#!/usr/bin/env python3
"""
Step 3 Validation Runner

Handles validation of matrix preparation from Step 3 of the pipeline.

Author: Data Pipeline
Date: 2025-01-03
"""

import logging
from typing import Dict, Any

from ..schemas import StoreMatrixSchema, SubcategoryMatrixSchema, SPUMatrixSchema, CategoryAggregatedMatrixSchema
from ..validators import validate_file

# Set up logging
logger = logging.getLogger(__name__)


def validate_step3_matrices() -> Dict[str, Any]:
    """
    Validate Step 3 matrix preparation outputs.
    
    Returns:
        Dictionary with validation results
    """
    logger.info("Starting Step 3 validation...")
    logger.info("Validating Step 3 matrix preparation outputs...")
    
    # Define files to validate
    files_to_validate = {
        'subcategory_matrix': "output/subcategory_matrix.csv",
        'spu_matrix': "output/spu_matrix.csv",
        'category_matrix': "output/category_aggregated_matrix.csv"
    }
    
    # Define schemas
    schemas = {
        'subcategory_matrix': SubcategoryMatrixSchema,
        'spu_matrix': SPUMatrixSchema,
        'category_matrix': CategoryAggregatedMatrixSchema
    }
    
    # Validate each file
    results = {}
    for file_type, file_path in files_to_validate.items():
        logger.info(f"Validating {file_type}: {file_path}")
        results[file_type] = validate_file(file_path, schemas[file_type])
    
    # Log results
    for file_type, result in results.items():
        status = "✅" if result.get('status') == 'valid' else "❌"
        logger.info(f"{status} {file_type} validation: {result.get('status', 'unknown')}")
    
    return results


def run_step3_validation() -> Dict[str, Any]:
    """
    Run Step 3 validation.
    
    Returns:
        Dictionary with validation results
    """
    return validate_step3_matrices()

