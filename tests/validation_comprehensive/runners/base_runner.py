#!/usr/bin/env python3
"""
Base Runner Utilities

Common utilities and imports for all validation runners.

Author: Data Pipeline
Date: 2025-01-03
"""

import logging
import glob
import os
from typing import Dict, Any, List

# Set up logging
logger = logging.getLogger(__name__)


def get_validation_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get validation summary from a list of results.
    
    Args:
        results: List of validation results
        
    Returns:
        Dictionary with summary statistics
    """
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.get('status') == 'valid')
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    return {
        'total_tests': total_tests,
        'passed_tests': passed_tests,
        'success_rate': success_rate
    }


def log_validation_summary(summary: Dict[str, Any], step_name: str = "Validation"):
    """
    Log validation summary.
    
    Args:
        summary: Validation summary dictionary
        step_name: Name of the validation step
    """
    logger.info(f"\nSUMMARY FOR {step_name}:")
    logger.info(f"Passed: {summary['passed_tests']}/{summary['total_tests']} tests")
    logger.info(f"Success rate: {summary['success_rate']:.1f}%")


def find_files_by_pattern(pattern: str, sample_size: int = None) -> List[str]:
    """
    Find files matching a pattern, optionally limiting to a sample.
    
    Args:
        pattern: File pattern to match
        sample_size: Maximum number of files to return
        
    Returns:
        List of matching file paths
    """
    files = glob.glob(pattern)
    if sample_size and len(files) > sample_size:
        files = files[:sample_size]
    return files

