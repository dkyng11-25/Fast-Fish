#!/usr/bin/env python3
"""
Step 2 Validation Runner

Handles validation of coordinate extraction from Step 2 of the pipeline.

Author: Data Pipeline
Date: 2025-01-03
"""

import logging
from typing import Dict, Any

from ..schemas import StoreCoordinatesSchema, SPUStoreMappingSchema, SPUMetadataSchema
from ..validators import validate_file

# Set up logging
logger = logging.getLogger(__name__)


def validate_step2_coordinates() -> Dict[str, Any]:
    """
    Validate Step 2 coordinate extraction outputs.
    
    Returns:
        Dictionary with validation results
    """
    logger.info("Starting Step 2 validation...")
    logger.info("Validating Step 2 coordinate extraction outputs...")
    
    # Define files to validate
    files_to_validate = {
        'store_coordinates': "data/store_coordinates_extended.csv",
        'spu_store_mapping': "data/spu_store_mapping.csv",
        'spu_metadata': "data/spu_metadata.csv"
    }
    
    # Define schemas
    schemas = {
        'store_coordinates': StoreCoordinatesSchema,
        'spu_store_mapping': SPUStoreMappingSchema,
        'spu_metadata': SPUMetadataSchema
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


def run_step2_validation() -> Dict[str, Any]:
    """
    Run Step 2 validation.
    
    Returns:
        Dictionary with validation results
    """
    return validate_step2_coordinates()

