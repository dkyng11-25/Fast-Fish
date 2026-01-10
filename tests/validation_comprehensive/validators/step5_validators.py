#!/usr/bin/env python3
"""
Step 5: Feels Like Temperature Validators

Validation functions for Step 5 - Calculate Feels-Like Temperature for Stores.
Provides comprehensive validation for weather data, temperature calculations, and output files.

Author: Data Pipeline
Date: 2025-09-16
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime, timedelta

from ..schemas.step5_schemas import (
    WeatherDataSchema, StoreAltitudeSchema, FeelsLikeTemperatureSchema,
    TemperatureBandsSchema, Step5InputSchema, Step5OutputSchema, Step5ValidationSchema
)

logger = logging.getLogger(__name__)


def validate_weather_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate weather data quality and consistency.
    
    Args:
        df: Weather data DataFrame
        
    Returns:
        Dictionary with validation results
    """
    results = {
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        # Check required columns
        required_cols = ['str_code', 'date', 'temperature', 'humidity', 'wind_speed', 'pressure']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            results["errors"].append(f"Missing required columns: {missing_cols}")
            results["validation_passed"] = False
        
        # Check data types
        if 'temperature' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['temperature']):
                results["errors"].append("Temperature column must be numeric")
                results["validation_passed"] = False
        
        # Check temperature range
        if 'temperature' in df.columns:
            temp_stats = df['temperature'].describe()
            results["statistics"]["temperature_range"] = {
                "min": temp_stats['min'],
                "max": temp_stats['max'],
                "mean": temp_stats['mean']
            }
            
            if temp_stats['min'] < -50 or temp_stats['max'] > 60:
                results["warnings"].append("Temperature values outside reasonable range (-50°C to 60°C)")
        
        # Check humidity range
        if 'humidity' in df.columns:
            humidity_stats = df['humidity'].describe()
            results["statistics"]["humidity_range"] = {
                "min": humidity_stats['min'],
                "max": humidity_stats['max'],
                "mean": humidity_stats['mean']
            }
            
            if humidity_stats['min'] < 0 or humidity_stats['max'] > 100:
                results["errors"].append("Humidity values outside valid range (0-100%)")
                results["validation_passed"] = False
        
        # Check for missing values
        missing_counts = df.isnull().sum()
        results["statistics"]["missing_values"] = missing_counts.to_dict()
        
        if missing_counts.sum() > 0:
            results["warnings"].append(f"Found {missing_counts.sum()} missing values")
        
        # Check date consistency
        if 'date' in df.columns:
            try:
                dates = pd.to_datetime(df['date'])
                date_range = dates.max() - dates.min()
                results["statistics"]["date_range_days"] = date_range.days
                
                if date_range.days < 30:
                    results["warnings"].append("Weather data spans less than 30 days")
            except Exception as e:
                results["errors"].append(f"Invalid date format: {str(e)}")
                results["validation_passed"] = False
        
    except Exception as e:
        results["errors"].append(f"Weather data validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_feels_like_calculation(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate feels-like temperature calculations.
    
    Args:
        df: Feels-like temperature results DataFrame
        
    Returns:
        Dictionary with validation results
    """
    results = {
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        # Check required columns
        required_cols = ['str_code', 'date', 'temperature', 'feels_like_temperature', 'humidity', 'wind_speed']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            results["errors"].append(f"Missing required columns: {missing_cols}")
            results["validation_passed"] = False
        
        # Validate temperature difference calculation
        if 'temperature' in df.columns and 'feels_like_temperature' in df.columns:
            df['calculated_diff'] = df['feels_like_temperature'] - df['temperature']
            if 'temperature_difference' in df.columns:
                diff_errors = abs(df['calculated_diff'] - df['temperature_difference']) > 0.1
                if diff_errors.any():
                    results["warnings"].append(f"Temperature difference calculation mismatch in {diff_errors.sum()} records")
            
            # Check feels-like temperature range
            feels_like_stats = df['feels_like_temperature'].describe()
            results["statistics"]["feels_like_range"] = {
                "min": feels_like_stats['min'],
                "max": feels_like_stats['max'],
                "mean": feels_like_stats['mean']
            }
            
            if feels_like_stats['min'] < -60 or feels_like_stats['max'] > 70:
                results["warnings"].append("Feels-like temperature values outside reasonable range (-60°C to 70°C)")
        
        # Check for unrealistic temperature differences
        if 'temperature_difference' in df.columns:
            diff_stats = df['temperature_difference'].describe()
            results["statistics"]["temperature_difference_range"] = {
                "min": diff_stats['min'],
                "max": diff_stats['max'],
                "mean": diff_stats['mean']
            }
            
            # Feels-like should not be more than 10°C different from actual temperature
            extreme_diffs = abs(df['temperature_difference']) > 10
            if extreme_diffs.any():
                results["warnings"].append(f"Extreme temperature differences (>10°C) in {extreme_diffs.sum()} records")
        
        # Check data consistency
        if 'str_code' in df.columns:
            unique_stores = df['str_code'].nunique()
            results["statistics"]["unique_stores"] = unique_stores
            
            if unique_stores < 10:
                results["warnings"].append(f"Only {unique_stores} stores in feels-like temperature data")
        
    except Exception as e:
        results["errors"].append(f"Feels-like calculation validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_temperature_bands(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate temperature bands classification.
    
    Args:
        df: Temperature bands DataFrame
        
    Returns:
        Dictionary with validation results
    """
    results = {
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        # Check required columns
        required_cols = ['str_code', 'temperature_band', 'band_min_temp', 'band_max_temp', 'feels_like_temperature_avg']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            results["errors"].append(f"Missing required columns: {missing_cols}")
            results["validation_passed"] = False
        
        # Validate temperature band values
        if 'temperature_band' in df.columns:
            valid_bands = ['very_cold', 'cold', 'cool', 'mild', 'warm', 'hot', 'very_hot']
            invalid_bands = df[~df['temperature_band'].isin(valid_bands)]['temperature_band'].unique()
            if len(invalid_bands) > 0:
                results["errors"].append(f"Invalid temperature bands: {invalid_bands}")
                results["validation_passed"] = False
            
            band_counts = df['temperature_band'].value_counts()
            results["statistics"]["band_distribution"] = band_counts.to_dict()
        
        # Validate temperature ranges
        if 'band_min_temp' in df.columns and 'band_max_temp' in df.columns:
            invalid_ranges = df[df['band_min_temp'] >= df['band_max_temp']]
            if len(invalid_ranges) > 0:
                results["errors"].append(f"Invalid temperature ranges in {len(invalid_ranges)} records")
                results["validation_passed"] = False
            
            temp_range_stats = {
                "min_temp_min": df['band_min_temp'].min(),
                "min_temp_max": df['band_min_temp'].max(),
                "max_temp_min": df['band_max_temp'].min(),
                "max_temp_max": df['band_max_temp'].max()
            }
            results["statistics"]["temperature_ranges"] = temp_range_stats
        
        # Check band consistency
        if 'feels_like_temperature_avg' in df.columns:
            feels_like_stats = df['feels_like_temperature_avg'].describe()
            results["statistics"]["feels_like_avg_range"] = {
                "min": feels_like_stats['min'],
                "max": feels_like_stats['max'],
                "mean": feels_like_stats['mean']
            }
        
        # Check record counts
        if 'record_count' in df.columns:
            record_count_stats = df['record_count'].describe()
            results["statistics"]["record_count_range"] = {
                "min": record_count_stats['min'],
                "max": record_count_stats['max'],
                "mean": record_count_stats['mean']
            }
            
            if record_count_stats['min'] < 1:
                results["errors"].append("Some bands have zero or negative record counts")
                results["validation_passed"] = False
        
    except Exception as e:
        results["errors"].append(f"Temperature bands validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_step5_files(period_label: str, data_dir: str = "output") -> Dict[str, Any]:
    """
    Validate Step 5 output files.
    
    Args:
        period_label: Period label for file naming
        data_dir: Directory containing output files
        
    Returns:
        Dictionary with file validation results
    """
    results = {
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": [],
        "files_checked": [],
        "file_validation": {}
    }
    
    try:
        data_path = Path(data_dir)
        
        # Check main output files
        expected_files = [
            "stores_with_feels_like_temperature.csv",
            "temperature_bands.csv"
        ]
        
        for filename in expected_files:
            file_path = data_path / filename
            results["files_checked"].append(str(file_path))
            
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    file_results = {
                        "exists": True,
                        "rows": len(df),
                        "columns": list(df.columns),
                        "file_size_mb": file_path.stat().st_size / (1024 * 1024)
                    }
                    
                    # Validate specific file content
                    if filename == "stores_with_feels_like_temperature.csv":
                        validation_result = validate_feels_like_calculation(df)
                        file_results["validation"] = validation_result
                    elif filename == "temperature_bands.csv":
                        validation_result = validate_temperature_bands(df)
                        file_results["validation"] = validation_result
                    
                    results["file_validation"][filename] = file_results
                    
                    if file_results.get("validation", {}).get("validation_passed", True) == False:
                        results["warnings"].append(f"Validation issues in {filename}")
                    
                except Exception as e:
                    results["errors"].append(f"Error reading {filename}: {str(e)}")
                    results["validation_passed"] = False
            else:
                results["errors"].append(f"Missing required file: {filename}")
                results["validation_passed"] = False
                results["file_validation"][filename] = {"exists": False}
        
        # Check for log files
        log_files = list(data_path.glob("feels_like_calculation.log"))
        if log_files:
            results["files_checked"].extend([str(f) for f in log_files])
            results["statistics"]["log_files_found"] = len(log_files)
        
    except Exception as e:
        results["errors"].append(f"File validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_step5_complete(period_label: str, data_dir: str = "output") -> Step5ValidationSchema:
    """
    Complete validation for Step 5.
    
    Args:
        period_label: Period label for validation
        data_dir: Directory containing output files
        
    Returns:
        Complete validation results
    """
    logger.info(f"Starting complete Step 5 validation for period {period_label}")
    
    # Initialize validation results
    validation_results = {
        "validation_passed": False,  # Requires real data validation
        "input_validation": {},
        "output_validation": {},
        "calculation_validation": {},
        "file_validation": {},
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        # File validation
        file_validation = validate_step5_files(period_label, data_dir)
        validation_results["file_validation"] = file_validation
        validation_results["validation_passed"] = file_validation["validation_passed"]
        validation_results["errors"].extend(file_validation["errors"])
        validation_results["warnings"].extend(file_validation["warnings"])
        
        # Load and validate output data
        data_path = Path(data_dir)
        feels_like_file = data_path / "stores_with_feels_like_temperature.csv"
        bands_file = data_path / "temperature_bands.csv"
        
        if feels_like_file.exists():
            df_feels_like = pd.read_csv(feels_like_file)
            feels_like_validation = validate_feels_like_calculation(df_feels_like)
            validation_results["output_validation"]["feels_like_temperature"] = feels_like_validation
            validation_results["statistics"]["feels_like_records"] = len(df_feels_like)
            
            if not feels_like_validation["validation_passed"]:
                validation_results["validation_passed"] = False
        
        if bands_file.exists():
            df_bands = pd.read_csv(bands_file)
            bands_validation = validate_temperature_bands(df_bands)
            validation_results["output_validation"]["temperature_bands"] = bands_validation
            validation_results["statistics"]["temperature_bands"] = len(df_bands)
            
            if not bands_validation["validation_passed"]:
                validation_results["validation_passed"] = False
        
        # Overall statistics
        validation_results["statistics"]["total_errors"] = len(validation_results["errors"])
        validation_results["statistics"]["total_warnings"] = len(validation_results["warnings"])
        validation_results["statistics"]["validation_timestamp"] = datetime.now().isoformat()
        
    except Exception as e:
        validation_results["errors"].append(f"Complete validation error: {str(e)}")
        validation_results["validation_passed"] = False
        logger.error(f"Step 5 validation failed: {str(e)}")
    
    return Step5ValidationSchema(**validation_results)


# Export all validators
__all__ = [
    'validate_weather_data_quality',
    'validate_feels_like_calculation',
    'validate_temperature_bands',
    'validate_step5_files',
    'validate_step5_complete'
]


