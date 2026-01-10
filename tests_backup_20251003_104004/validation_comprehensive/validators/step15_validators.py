#!/usr/bin/env python3
"""
Step 15: Historical Baseline Download Validators

Validation functions for Step 15 - Download Historical Baseline Data.
Provides comprehensive validation for historical data download and processing.

Author: Data Pipeline
Date: 2025-09-16
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime, timedelta

from ..schemas.step15_schemas import (
    HistoricalBaselineSchema, HistoricalInsightsSchema, BaselineComparisonSchema,
    Step15InputSchema, Step15OutputSchema, Step15ValidationSchema, HistoricalDataQualitySchema
)

logger = logging.getLogger(__name__)


def validate_historical_baseline_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate historical baseline data quality and consistency.
    
    Args:
        df: Historical baseline DataFrame
        
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
        required_cols = ['str_code', 'period', 'baseline_sales', 'category']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            results["errors"].append(f"Missing required columns: {missing_cols}")
            results["validation_passed"] = False
        
        # Check data types
        if 'baseline_sales' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['baseline_sales']):
                results["errors"].append("Baseline sales column must be numeric")
                results["validation_passed"] = False
        
        # Check sales data ranges
        if 'baseline_sales' in df.columns:
            sales_stats = df['baseline_sales'].describe()
            results["statistics"]["baseline_sales_range"] = {
                "min": sales_stats['min'],
                "max": sales_stats['max'],
                "mean": sales_stats['mean'],
                "std": sales_stats['std']
            }
            
            if sales_stats['min'] < 0:
                results["errors"].append("Baseline sales cannot be negative")
                results["validation_passed"] = False
            
            if sales_stats['max'] > 1e8:
                results["warnings"].append("Very large baseline sales values detected")
        
        # Check period format consistency
        if 'period' in df.columns:
            periods = df['period'].unique()
            results["statistics"]["unique_periods"] = len(periods)
            
            # Check period format (should be YYYYMM)
            invalid_periods = []
            for period in periods:
                if not isinstance(period, str) or len(period) < 6 or not period.isdigit():
                    invalid_periods.append(period)
            
            if invalid_periods:
                results["warnings"].append(f"Invalid period formats found: {invalid_periods[:5]}")
        
        # Check year and month consistency
        if 'year' in df.columns and 'month' in df.columns:
            year_stats = df['year'].describe()
            month_stats = df['month'].describe()
            
            results["statistics"]["year_range"] = {
                "min": year_stats['min'],
                "max": year_stats['max']
            }
            
            results["statistics"]["month_range"] = {
                "min": month_stats['min'],
                "max": month_stats['max']
            }
            
            if year_stats['min'] < 2020 or year_stats['max'] > 2025:
                results["warnings"].append("Year values outside expected range (2020-2025)")
            
            if month_stats['min'] < 1 or month_stats['max'] > 12:
                results["errors"].append("Month values must be between 1 and 12")
                results["validation_passed"] = False
        
        # Check for missing values
        missing_counts = df.isnull().sum()
        results["statistics"]["missing_values"] = missing_counts.to_dict()
        
        if missing_counts.sum() > 0:
            results["warnings"].append(f"Found {missing_counts.sum()} missing values")
        
        # Check store code consistency
        if 'str_code' in df.columns:
            unique_stores = df['str_code'].nunique()
            results["statistics"]["unique_stores"] = unique_stores
            
            if unique_stores < 10:
                results["warnings"].append(f"Only {unique_stores} stores in historical baseline data")
        
    except Exception as e:
        results["errors"].append(f"Historical baseline validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_historical_insights(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate historical insights data.
    
    Args:
        df: Historical insights DataFrame
        
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
        required_cols = ['str_code', 'insight_type', 'insight_value', 'comparison_period']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            results["errors"].append(f"Missing required columns: {missing_cols}")
            results["validation_passed"] = False
        
        # Check insight types
        if 'insight_type' in df.columns:
            valid_types = ['sales_trend', 'seasonal_pattern', 'growth_rate', 'volatility', 'peak_performance']
            invalid_types = df[~df['insight_type'].isin(valid_types)]['insight_type'].unique()
            if len(invalid_types) > 0:
                results["errors"].append(f"Invalid insight types: {invalid_types}")
                results["validation_passed"] = False
            
            insight_counts = df['insight_type'].value_counts()
            results["statistics"]["insight_type_distribution"] = insight_counts.to_dict()
        
        # Check insight values
        if 'insight_value' in df.columns:
            insight_stats = df['insight_value'].describe()
            results["statistics"]["insight_value_range"] = {
                "min": insight_stats['min'],
                "max": insight_stats['max'],
                "mean": insight_stats['mean'],
                "std": insight_stats['std']
            }
            
            # Check for extreme values
            extreme_values = df[abs(df['insight_value']) > 1000]
            if len(extreme_values) > 0:
                results["warnings"].append(f"Found {len(extreme_values)} extreme insight values")
        
        # Check confidence scores
        if 'confidence_score' in df.columns:
            confidence_stats = df['confidence_score'].describe()
            results["statistics"]["confidence_score_range"] = {
                "min": confidence_stats['min'],
                "max": confidence_stats['max'],
                "mean": confidence_stats['mean']
            }
            
            low_confidence = df[df['confidence_score'] < 0.5]
            if len(low_confidence) > 0:
                results["warnings"].append(f"Found {len(low_confidence)} insights with low confidence scores")
        
        # Check trend directions
        if 'trend_direction' in df.columns:
            valid_directions = ['increasing', 'decreasing', 'stable', 'volatile']
            invalid_directions = df[~df['trend_direction'].isin(valid_directions)]['trend_direction'].unique()
            if len(invalid_directions) > 0:
                results["warnings"].append(f"Invalid trend directions: {invalid_directions}")
        
    except Exception as e:
        results["errors"].append(f"Historical insights validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_baseline_comparison(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate baseline comparison data.
    
    Args:
        df: Baseline comparison DataFrame
        
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
        required_cols = ['str_code', 'current_period', 'historical_period', 'current_sales', 'historical_sales']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            results["errors"].append(f"Missing required columns: {missing_cols}")
            results["validation_passed"] = False
        
        # Check sales data consistency
        if 'current_sales' in df.columns and 'historical_sales' in df.columns:
            current_stats = df['current_sales'].describe()
            historical_stats = df['historical_sales'].describe()
            
            results["statistics"]["current_sales_range"] = {
                "min": current_stats['min'],
                "max": current_stats['max'],
                "mean": current_stats['mean']
            }
            
            results["statistics"]["historical_sales_range"] = {
                "min": historical_stats['min'],
                "max": historical_stats['max'],
                "mean": historical_stats['mean']
            }
            
            # Check for negative sales
            negative_current = df[df['current_sales'] < 0]
            negative_historical = df[df['historical_sales'] < 0]
            
            if len(negative_current) > 0:
                results["errors"].append(f"Found {len(negative_current)} records with negative current sales")
                results["validation_passed"] = False
            
            if len(negative_historical) > 0:
                results["errors"].append(f"Found {len(negative_historical)} records with negative historical sales")
                results["validation_passed"] = False
        
        # Check sales change calculations
        if 'sales_change' in df.columns and 'sales_change_pct' in df.columns:
            if 'current_sales' in df.columns and 'historical_sales' in df.columns:
                df['calculated_change'] = df['current_sales'] - df['historical_sales']
                df['calculated_pct'] = (df['calculated_change'] / df['historical_sales']) * 100
                
                change_errors = abs(df['sales_change'] - df['calculated_change']) > 0.01
                pct_errors = abs(df['sales_change_pct'] - df['calculated_pct']) > 0.01
                
                if change_errors.any():
                    results["warnings"].append(f"Sales change calculation mismatch in {change_errors.sum()} records")
                
                if pct_errors.any():
                    results["warnings"].append(f"Sales change percentage calculation mismatch in {pct_errors.sum()} records")
        
        # Check performance indicators
        if 'performance_indicator' in df.columns:
            valid_indicators = ['outperforming', 'underperforming', 'stable', 'volatile', 'trending_up', 'trending_down']
            invalid_indicators = df[~df['performance_indicator'].isin(valid_indicators)]['performance_indicator'].unique()
            if len(invalid_indicators) > 0:
                results["errors"].append(f"Invalid performance indicators: {invalid_indicators}")
                results["validation_passed"] = False
            
            indicator_counts = df['performance_indicator'].value_counts()
            results["statistics"]["performance_indicator_distribution"] = indicator_counts.to_dict()
        
    except Exception as e:
        results["errors"].append(f"Baseline comparison validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_historical_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate historical data quality metrics.
    
    Args:
        df: Historical data quality DataFrame
        
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
        required_cols = ['period', 'completeness_score', 'consistency_score', 'accuracy_score']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            results["errors"].append(f"Missing required columns: {missing_cols}")
            results["validation_passed"] = False
        
        # Check quality scores
        quality_columns = ['completeness_score', 'consistency_score', 'accuracy_score']
        for col in quality_columns:
            if col in df.columns:
                score_stats = df[col].describe()
                results["statistics"][f"{col}_range"] = {
                    "min": score_stats['min'],
                    "max": score_stats['max'],
                    "mean": score_stats['mean']
                }
                
                # Check for low quality scores
                low_scores = df[df[col] < 0.5]
                if len(low_scores) > 0:
                    results["warnings"].append(f"Found {len(low_scores)} periods with low {col} (<0.5)")
        
        # Check missing data counts
        if 'missing_data_count' in df.columns:
            missing_stats = df['missing_data_count'].describe()
            results["statistics"]["missing_data_range"] = {
                "min": missing_stats['min'],
                "max": missing_stats['max'],
                "mean": missing_stats['mean']
            }
            
            high_missing = df[df['missing_data_count'] > 100]
            if len(high_missing) > 0:
                results["warnings"].append(f"Found {len(high_missing)} periods with high missing data counts")
        
        # Check outlier counts
        if 'outlier_count' in df.columns:
            outlier_stats = df['outlier_count'].describe()
            results["statistics"]["outlier_range"] = {
                "min": outlier_stats['min'],
                "max": outlier_stats['max'],
                "mean": outlier_stats['mean']
            }
            
            high_outliers = df[df['outlier_count'] > 50]
            if len(high_outliers) > 0:
                results["warnings"].append(f"Found {len(high_outliers)} periods with high outlier counts")
        
        # Check quality issues
        if 'quality_issues' in df.columns:
            all_issues = []
            for issues_list in df['quality_issues']:
                if isinstance(issues_list, list):
                    all_issues.extend(issues_list)
            
            if all_issues:
                issue_counts = pd.Series(all_issues).value_counts()
                results["statistics"]["quality_issues_distribution"] = issue_counts.to_dict()
                results["warnings"].append(f"Found {len(all_issues)} quality issues across all periods")
        
    except Exception as e:
        results["errors"].append(f"Historical data quality validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_step15_files(period_label: str, data_dir: str = "output") -> Dict[str, Any]:
    """
    Validate Step 15 output files.
    
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
            f"historical_baseline_{period_label}.csv",
            f"historical_insights_{period_label}.json",
            f"baseline_comparison_{period_label}.csv"
        ]
        
        for filename in expected_files:
            file_path = data_path / filename
            results["files_checked"].append(str(file_path))
            
            if file_path.exists():
                try:
                    if filename.endswith('.csv'):
                        df = pd.read_csv(file_path)
                        file_results = {
                            "exists": True,
                            "rows": len(df),
                            "columns": list(df.columns),
                            "file_size_mb": file_path.stat().st_size / (1024 * 1024)
                        }
                        
                        # Validate specific file content
                        if "historical_baseline" in filename:
                            validation_result = validate_historical_baseline_data(df)
                            file_results["validation"] = validation_result
                        elif "baseline_comparison" in filename:
                            validation_result = validate_baseline_comparison(df)
                            file_results["validation"] = validation_result
                        
                        results["file_validation"][filename] = file_results
                        
                        if file_results.get("validation", {}).get("validation_passed", True) == False:
                            results["warnings"].append(f"Validation issues in {filename}")
                    
                    elif filename.endswith('.json'):
                        import json
                        with open(file_path, 'r') as f:
                            json_data = json.load(f)
                        file_results = {
                            "exists": True,
                            "file_size_mb": file_path.stat().st_size / (1024 * 1024),
                            "data_type": "json"
                        }
                        results["file_validation"][filename] = file_results
                    
                except Exception as e:
                    results["errors"].append(f"Error reading {filename}: {str(e)}")
                    results["validation_passed"] = False
            else:
                results["warnings"].append(f"Missing expected file: {filename}")
                results["file_validation"][filename] = {"exists": False}
        
    except Exception as e:
        results["errors"].append(f"File validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_step15_complete(period_label: str, data_dir: str = "output") -> Step15ValidationSchema:
    """
    Complete validation for Step 15.
    
    Args:
        period_label: Period label for validation
        data_dir: Directory containing output files
        
    Returns:
        Complete validation results
    """
    logger.info(f"Starting complete Step 15 validation for period {period_label}")
    
    # Initialize validation results
    validation_results = {
        "validation_passed": False,  # Requires real data validation
        "input_validation": {},
        "output_validation": {},
        "download_validation": {},
        "data_quality_validation": {},
        "file_validation": {},
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        # File validation
        file_validation = validate_step15_files(period_label, data_dir)
        validation_results["file_validation"] = file_validation
        validation_results["validation_passed"] = file_validation["validation_passed"]
        validation_results["errors"].extend(file_validation["errors"])
        validation_results["warnings"].extend(file_validation["warnings"])
        
        # Load and validate output data
        data_path = Path(data_dir)
        baseline_file = data_path / f"historical_baseline_{period_label}.csv"
        comparison_file = data_path / f"baseline_comparison_{period_label}.csv"
        
        if baseline_file.exists():
            df_baseline = pd.read_csv(baseline_file)
            baseline_validation = validate_historical_baseline_data(df_baseline)
            validation_results["output_validation"]["historical_baseline"] = baseline_validation
            validation_results["statistics"]["baseline_records"] = len(df_baseline)
            
            if not baseline_validation["validation_passed"]:
                validation_results["validation_passed"] = False
        
        if comparison_file.exists():
            df_comparison = pd.read_csv(comparison_file)
            comparison_validation = validate_baseline_comparison(df_comparison)
            validation_results["output_validation"]["baseline_comparison"] = comparison_validation
            validation_results["statistics"]["comparison_records"] = len(df_comparison)
            
            if not comparison_validation["validation_passed"]:
                validation_results["validation_passed"] = False
        
        # Overall statistics
        validation_results["statistics"]["total_errors"] = len(validation_results["errors"])
        validation_results["statistics"]["total_warnings"] = len(validation_results["warnings"])
        validation_results["statistics"]["validation_timestamp"] = datetime.now().isoformat()
        
    except Exception as e:
        validation_results["errors"].append(f"Complete validation error: {str(e)}")
        validation_results["validation_passed"] = False
        logger.error(f"Step 15 validation failed: {str(e)}")
    
    return Step15ValidationSchema(**validation_results)


# Export all validators
__all__ = [
    'validate_historical_baseline_data',
    'validate_historical_insights',
    'validate_baseline_comparison',
    'validate_historical_data_quality',
    'validate_step15_files',
    'validate_step15_complete'
]


