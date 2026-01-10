#!/usr/bin/env python3
"""
Step 2B Validation Runner

Handles validation of seasonal data consolidation from Step 2B of the pipeline.

Author: Data Pipeline
Date: 2025-01-03
"""

import logging
from typing import Dict, Any

from ..schemas import SeasonalStoreProfilesSchema, SeasonalCategoryPatternsSchema, SeasonalClusteringFeaturesSchema
from ..validators import validate_file

# Set up logging
logger = logging.getLogger(__name__)


def validate_step2b_seasonal_data() -> Dict[str, Any]:
    """
    Validate Step 2B seasonal data consolidation outputs.
    
    Returns:
        Dictionary with validation results
    """
    logger.info("Starting Step 2B validation...")
    logger.info("Validating Step 2B seasonal data consolidation outputs...")
    
    # Define files to validate
    files_to_validate = {
        'seasonal_store_profiles': "output/seasonal_store_profiles_*.csv",
        'seasonal_category_patterns': "output/seasonal_category_patterns_*.csv",
        'seasonal_clustering_features': "output/seasonal_clustering_features_*.csv"
    }
    
    # Define schemas
    schemas = {
        'seasonal_store_profiles': SeasonalStoreProfilesSchema,
        'seasonal_category_patterns': SeasonalCategoryPatternsSchema,
        'seasonal_clustering_features': SeasonalClusteringFeaturesSchema
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


def run_step2b_validation() -> Dict[str, Any]:
    """
    Run Step 2B validation.
    
    Returns:
        Dictionary with validation results
    """
    return validate_step2b_seasonal_data()

