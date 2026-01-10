#!/usr/bin/env python3
"""
Step 4 Validation Runner

Handles validation of weather data from Step 4 of the pipeline.
Includes weather data files and store altitude validation.

Author: Data Pipeline
Date: 2025-01-03
"""

import logging
import glob
from typing import Dict, Any

from ..schemas import WeatherDataSchema, StoreAltitudeSchema
from ..validators import validate_file
from .base_runner import get_validation_summary, find_files_by_pattern

# Set up logging
logger = logging.getLogger(__name__)


def validate_weather_files(sample_size: int = 5) -> Dict[str, Any]:
    """
    Validate weather data files.
    
    Args:
        sample_size: Number of weather files to sample for validation
    
    Returns:
        Dictionary with validation results
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"VALIDATING STEP 4 WEATHER DATA")
    logger.info(f"{'='*60}")
    
    # Find weather data files
    pattern = "output/weather_data/weather_data_*.csv"
    weather_files = find_files_by_pattern(pattern)
    
    if not weather_files:
        logger.warning("No weather data files found!")
        return {'weather_files': 0, 'validated': 0, 'store_altitudes': False}
    
    logger.info(f"Found {len(weather_files)} weather data files")
    
    # Sample files for validation
    sample_files = weather_files[:sample_size]
    logger.info(f"Validating sample of {len(sample_files)} files")
    
    # Validate weather files
    weather_results = {}
    for file_path in sample_files:
        weather_results[file_path] = validate_file(file_path, WeatherDataSchema)
    
    # Validate store altitudes
    altitude_result = validate_store_altitudes()
    
    # Generate summary
    weather_summary = get_validation_summary(list(weather_results.values()))
    
    results = {
        'weather_files': len(weather_files),
        'sample_size': len(sample_files),
        'weather_results': weather_results,
        'weather_summary': weather_summary,
        'store_altitudes': altitude_result
    }
    
    # Log summary
    success_rate = weather_summary['success_rate']
    logger.info(f"\nSUMMARY:")
    logger.info(f"Total weather files: {results['weather_files']}")
    logger.info(f"Sample validated: {weather_summary['passed_tests']}/{weather_summary['total_tests']}")
    logger.info(f"Success rate: {success_rate:.1f}%")
    logger.info(f"Store altitudes: {'✅' if results['store_altitudes'] else '❌'}")
    
    return results


def validate_store_altitudes() -> bool:
    """
    Validate store altitude data.
    
    Returns:
        True if validation passed, False otherwise
    """
    try:
        file_path = "output/store_altitudes.csv"
        result = validate_file(file_path, StoreAltitudeSchema)
        return result.get('status') == 'valid'
    except Exception as e:
        logger.error(f"❌ Store altitudes validation failed: {str(e)}")
        return False


def validate_weather_by_period(period: str, sample_size: int = 3) -> Dict[str, Any]:
    """
    Validate weather data for a specific period.
    
    Args:
        period: Period string (e.g., '202408')
        sample_size: Number of files to sample
    
    Returns:
        Dictionary with validation results
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"VALIDATING WEATHER DATA FOR PERIOD: {period}")
    logger.info(f"{'='*60}")
    
    # Find weather files for the period
    pattern = f"output/weather_data/weather_data_*_{period}*.csv"
    weather_files = find_files_by_pattern(pattern)
    
    if not weather_files:
        logger.warning(f"No weather data files found for period {period}!")
        return {'period': period, 'files_found': 0, 'validated': 0}
    
    logger.info(f"Found {len(weather_files)} weather files for period {period}")
    
    # Sample files for validation
    sample_files = weather_files[:sample_size]
    logger.info(f"Validating sample of {len(sample_files)} files")
    
    # Validate files
    results = {}
    for file_path in sample_files:
        results[file_path] = validate_file(file_path, WeatherDataSchema)
    
    # Generate summary
    summary = get_validation_summary(list(results.values()))
    
    # Log results
    success_rate = summary['success_rate']
    logger.info(f"\nSUMMARY FOR PERIOD {period}:")
    logger.info(f"Files found: {len(weather_files)}")
    logger.info(f"Sample validated: {summary['passed_tests']}/{summary['total_tests']}")
    logger.info(f"Success rate: {success_rate:.1f}%")
    
    return {
        'period': period,
        'files_found': len(weather_files),
        'sample_size': len(sample_files),
        'results': results,
        'summary': summary,
        'success_rate': success_rate
    }


def run_step4_validation(sample_size: int = 5, period: str = None) -> Dict[str, Any]:
    """
    Run Step 4 validation with flexible options.
    
    Args:
        sample_size: Number of weather files to sample
        period: Specific period to validate
    
    Returns:
        Dictionary with validation results
    """
    if period:
        return validate_weather_by_period(period, sample_size)
    else:
        return validate_weather_files(sample_size)

