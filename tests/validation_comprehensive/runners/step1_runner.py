#!/usr/bin/env python3
"""
Step 1 Validation Runner

Handles validation of API data from Step 1 of the pipeline.
Includes store configuration, category sales, and SPU sales data validation.

Author: Data Pipeline
Date: 2025-01-03
"""

import logging
from typing import Dict, Any, List

from ..schemas import StoreConfigSchema, CategorySalesSchema, SPUSalesSchema
from ..validators import validate_file
from .base_runner import get_validation_summary, log_validation_summary

# Set up logging
logger = logging.getLogger(__name__)


def validate_step1_period(period: str) -> Dict[str, Any]:
    """
    Validate Step 1 data for a specific period.
    
    Args:
        period: Period string (e.g., '202401')
    
    Returns:
        Dictionary with validation results
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"VALIDATING STEP 1 DATA FOR PERIOD: {period}")
    logger.info(f"{'='*60}")
    
    # Define file paths
    files_to_validate = {
        'store_config': f"data/api_data/store_config_{period}.csv",
        'category_sales': f"data/api_data/complete_category_sales_{period}.csv", 
        'spu_sales': f"data/api_data/complete_spu_sales_{period}.csv"
    }
    
    # Define schemas
    schemas = {
        'store_config': StoreConfigSchema,
        'category_sales': CategorySalesSchema,
        'spu_sales': SPUSalesSchema
    }
    
    # Validate each file
    results = {}
    for file_type, file_path in files_to_validate.items():
        logger.info(f"Validating {file_type} data: {file_path}")
        results[file_type] = validate_file(file_path, schemas[file_type])
    
    # Generate summary
    summary = get_validation_summary(list(results.values()))
    
    # Log results
    passed_tests = sum(1 for r in results.values() if r.get('status') == 'valid')
    total_tests = len(results)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    logger.info(f"\nSUMMARY FOR {period}:")
    logger.info(f"Passed: {passed_tests}/{total_tests} tests")
    logger.info(f"Success rate: {success_rate:.1f}%")
    
    return {
        'period': period,
        'results': results,
        'summary': summary,
        'passed_tests': passed_tests,
        'total_tests': total_tests,
        'success_rate': success_rate
    }


def validate_multiple_periods(periods: List[str]) -> Dict[str, Any]:
    """
    Validate Step 1 data for multiple periods.
    
    Args:
        periods: List of period strings
    
    Returns:
        Dictionary with validation results for all periods
    """
    all_results = {}
    
    for period in periods:
        all_results[period] = validate_step1_period(period)
    
    # Overall summary
    total_passed = sum(r['passed_tests'] for r in all_results.values())
    total_tests = sum(r['total_tests'] for r in all_results.values())
    overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    logger.info(f"\n{'='*60}")
    logger.info(f"OVERALL SUMMARY FOR {len(periods)} PERIODS")
    logger.info(f"{'='*60}")
    logger.info(f"Total tests: {total_tests}")
    logger.info(f"Total passed: {total_passed}")
    logger.info(f"Overall success rate: {overall_success_rate:.1f}%")
    
    return {
        'periods': all_results,
        'total_passed': total_passed,
        'total_tests': total_tests,
        'overall_success_rate': overall_success_rate
    }


def run_step1_validation(period: str = None, periods: List[str] = None, comprehensive: bool = False) -> Dict[str, Any]:
    """
    Run Step 1 validation with flexible options.
    
    Args:
        period: Single period to validate
        periods: Multiple periods to validate
        comprehensive: Run comprehensive validation on key periods
    
    Returns:
        Dictionary with validation results
    """
    if comprehensive:
        # Test key periods: Chinese New Year, Golden Weeks, hot/cold months
        key_periods = ['202401', '202402', '202405', '202407', '202410', '202412', 
                      '202501', '202502', '202505', '202507']
        return validate_multiple_periods(key_periods)
    elif periods:
        return validate_multiple_periods(periods)
    elif period:
        return validate_step1_period(period)
    else:
        # Default: validate current month
        return validate_step1_period('202401')

