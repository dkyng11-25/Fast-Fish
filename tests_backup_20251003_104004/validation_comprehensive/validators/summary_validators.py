#!/usr/bin/env python3
"""
Summary Validation Functions

This module contains functions for generating and logging validation summaries.

Author: Data Pipeline
Date: 2025-01-03
"""

import logging
from typing import Dict, Any

# Set up logging
logger = logging.getLogger(__name__)


def get_validation_summary(results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a summary of validation results.
    
    Args:
        results: Dictionary of validation results from validate_multiple_files
    
    Returns:
        Summary statistics
    """
    total_files = len(results)
    valid_files = sum(1 for r in results.values() if r.get('status') == 'valid')
    invalid_files = sum(1 for r in results.values() if r.get('status') == 'invalid')
    error_files = sum(1 for r in results.values() if r.get('status') in ['error', 'read_error', 'file_not_found'])
    
    success_rate = (valid_files / total_files * 100) if total_files > 0 else 0
    
    return {
        'total_files': total_files,
        'valid_files': valid_files,
        'invalid_files': invalid_files,
        'error_files': error_files,
        'success_rate': success_rate
    }


def log_validation_summary(summary: Dict[str, Any], step_name: str = "Validation"):
    """
    Log validation summary in a formatted way.
    
    Args:
        summary: Summary from get_validation_summary
        step_name: Name of the validation step
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"{step_name.upper()} SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total files: {summary['total_files']}")
    logger.info(f"Valid files: {summary['valid_files']}")
    logger.info(f"Invalid files: {summary['invalid_files']}")
    logger.info(f"Error files: {summary['error_files']}")
    logger.info(f"Success rate: {summary['success_rate']:.1f}%")

