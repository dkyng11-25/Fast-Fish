#!/usr/bin/env python3
"""
Pipeline Validation Runners

Handles validation of pipeline steps 7, 8, 11, 13, and 14.

Author: Data Pipeline
Date: 2025-01-03
"""

import logging
from typing import Dict, Any

from ..schemas import (
    MissingSPURuleSchema, ImbalancedSPURuleSchema, BelowMinimumRuleSchema,
    BelowMinimumOpportunitiesSchema, MissedSalesOpportunitySchema,
    ConsolidatedSPURulesSchema, FastFishFormatSchema
)
from ..validators import validate_file_flexible

# Set up logging
logger = logging.getLogger(__name__)


def validate_step7_missing_spu_rule() -> Dict[str, Any]:
    """
    Validate Step 7 missing SPU rule outputs.
    
    Returns:
        Dictionary with validation results
    """
    logger.info("Starting Step 7 validation...")
    logger.info("Validating Step 7 missing SPU rule outputs...")
    
    # Find and validate Step 7 files
    import glob
    step7_files = glob.glob("output/rule7_missing_spu_*_results_*.csv")
    
    results = {}
    for file_path in step7_files:
        logger.info(f"Validating {file_path}")
        results[file_path] = validate_file_flexible(file_path, MissingSPURuleSchema)
    
    # Log results
    for file_path, result in results.items():
        status = "✅" if result.get('status') == 'valid' else "❌"
        logger.info(f"{status} {file_path}: {result.get('status', 'unknown')}")
    
    return results


def run_step7_validation() -> Dict[str, Any]:
    """
    Run Step 7 validation.
    
    Returns:
        Dictionary with validation results
    """
    return validate_step7_missing_spu_rule()


def validate_step8_imbalanced_spu_rule() -> Dict[str, Any]:
    """
    Validate Step 8 imbalanced SPU rule outputs.
    
    Returns:
        Dictionary with validation results
    """
    logger.info("Starting Step 8 validation...")
    logger.info("Validating Step 8 imbalanced SPU rule outputs...")
    
    # Find and validate Step 8 files
    import glob
    step8_files = glob.glob("output/rule8_imbalanced_spu_*.csv")
    
    results = {}
    for file_path in step8_files:
        logger.info(f"Validating {file_path}")
        results[file_path] = validate_file_flexible(file_path, ImbalancedSPURuleSchema)
    
    # Log results
    for file_path, result in results.items():
        status = "✅" if result.get('status') == 'valid' else "❌"
        logger.info(f"{status} {file_path}: {result.get('status', 'unknown')}")
    
    return results


def run_step8_validation() -> Dict[str, Any]:
    """
    Run Step 8 validation.
    
    Returns:
        Dictionary with validation results
    """
    return validate_step8_imbalanced_spu_rule()


def validate_step9_below_minimum_rule() -> Dict[str, Any]:
    """
    Validate Step 9 below minimum rule outputs.
    
    Returns:
        Dictionary with validation results
    """
    logger.info("Starting Step 9 validation...")
    logger.info("Validating Step 9 below minimum rule outputs...")
    
    # Find and validate Step 9 files
    import glob
    step9_files = glob.glob("output/rule9_below_minimum_spu_*.csv")
    
    results = {}
    for file_path in step9_files:
        logger.info(f"Validating {file_path}")
        results[file_path] = validate_file_flexible(file_path, BelowMinimumRuleSchema)
    
    # Log results
    for file_path, result in results.items():
        status = "✅" if result.get('status') == 'valid' else "❌"
        logger.info(f"{status} {file_path}: {result.get('status', 'unknown')}")
    
    return results


def run_step9_validation() -> Dict[str, Any]:
    """
    Run Step 9 validation.
    
    Returns:
        Dictionary with validation results
    """
    return validate_step9_below_minimum_rule()


def validate_step11_missed_sales_opportunity() -> Dict[str, Any]:
    """
    Validate Step 11 missed sales opportunity outputs.
    
    Returns:
        Dictionary with validation results
    """
    logger.info("Starting Step 11 validation...")
    logger.info("Validating Step 11 missed sales opportunity outputs...")
    
    # Find and validate Step 11 files
    import glob
    step11_files = glob.glob("output/rule11_*_missed_sales_opportunity_*_results_*.csv")
    
    results = {}
    for file_path in step11_files:
        logger.info(f"Validating {file_path}")
        results[file_path] = validate_file_flexible(file_path, MissedSalesOpportunitySchema)
    
    # Log results
    for file_path, result in results.items():
        status = "✅" if result.get('status') == 'valid' else "❌"
        logger.info(f"{status} {file_path}: {result.get('status', 'unknown')}")
    
    return results


def run_step11_validation() -> Dict[str, Any]:
    """
    Run Step 11 validation.
    
    Returns:
        Dictionary with validation results
    """
    return validate_step11_missed_sales_opportunity()


def validate_step13_consolidated_spu_rules() -> Dict[str, Any]:
    """
    Validate Step 13 consolidated SPU rules outputs.
    
    Returns:
        Dictionary with validation results
    """
    logger.info("Starting Step 13 validation...")
    logger.info("Validating Step 13 consolidated SPU rules outputs...")
    
    # Find and validate Step 13 files
    import glob
    step13_files = glob.glob("output/consolidated_spu_rule_results_*.csv")
    
    results = {}
    for file_path in step13_files:
        logger.info(f"Validating {file_path}")
        results[file_path] = validate_file_flexible(file_path, ConsolidatedSPURulesSchema)
    
    # Log results
    for file_path, result in results.items():
        status = "✅" if result.get('status') == 'valid' else "❌"
        logger.info(f"{status} {file_path}: {result.get('status', 'unknown')}")
    
    return results


def run_step13_validation() -> Dict[str, Any]:
    """
    Run Step 13 validation.
    
    Returns:
        Dictionary with validation results
    """
    return validate_step13_consolidated_spu_rules()


def validate_step14_fast_fish_format() -> Dict[str, Any]:
    """
    Validate Step 14 Fast Fish format outputs.
    
    Returns:
        Dictionary with validation results
    """
    logger.info("Starting Step 14 validation...")
    logger.info("Validating Step 14 Fast Fish format outputs...")
    
    # Find and validate Step 14 files
    import glob
    step14_files = glob.glob("output/enhanced_fast_fish_format_*.csv")
    
    results = {}
    for file_path in step14_files:
        logger.info(f"Validating {file_path}")
        results[file_path] = validate_file_flexible(file_path, FastFishFormatSchema)
    
    # Log results
    for file_path, result in results.items():
        status = "✅" if result.get('status') == 'valid' else "❌"
        logger.info(f"{status} {file_path}: {result.get('status', 'unknown')}")
    
    return results


def run_step14_validation() -> Dict[str, Any]:
    """
    Run Step 14 validation.
    
    Returns:
        Dictionary with validation results
    """
    return validate_step14_fast_fish_format()

