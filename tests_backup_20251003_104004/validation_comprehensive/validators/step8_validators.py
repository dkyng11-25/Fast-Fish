#!/usr/bin/env python3
"""
Step 8: Imbalanced Category Rule Validators

Validation functions for Step 8 - Imbalanced Category/SPU with Quantity Recommendations.
Provides comprehensive validation for imbalanced category rule processing.

Author: Data Pipeline
Date: 2025-09-16
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def validate_step8_inputs(df_clustering: pd.DataFrame, df_config: pd.DataFrame, df_quantity: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate Step 8 input data.
    
    Args:
        df_clustering: Clustering results DataFrame
        df_config: Store config DataFrame
        df_quantity: Quantity data DataFrame
        
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
        # Validate clustering data
        if 'str_code' not in df_clustering.columns:
            results["errors"].append("Missing 'str_code' column in clustering data")
            results["validation_passed"] = False
        
        if 'cluster_id' not in df_clustering.columns and 'Cluster' not in df_clustering.columns:
            results["errors"].append("Missing cluster identification columns in clustering data")
            results["validation_passed"] = False
        
        # Validate store config data
        required_config_cols = ['str_code', 'store_type', 'store_size']
        missing_config_cols = [col for col in required_config_cols if col not in df_config.columns]
        if missing_config_cols:
            results["warnings"].append(f"Missing recommended config columns: {missing_config_cols}")
        
        # Validate quantity data
        required_qty_cols = ['str_code', 'spu_code', 'quantity']
        missing_qty_cols = [col for col in required_qty_cols if col not in df_quantity.columns]
        if missing_qty_cols:
            results["errors"].append(f"Missing required quantity columns: {missing_qty_cols}")
            results["validation_passed"] = False
        
        # Check data consistency
        clustering_stores = set(df_clustering['str_code'].unique())
        config_stores = set(df_config['str_code'].unique())
        quantity_stores = set(df_quantity['str_code'].unique())
        
        results["statistics"]["clustering_stores"] = len(clustering_stores)
        results["statistics"]["config_stores"] = len(config_stores)
        results["statistics"]["quantity_stores"] = len(quantity_stores)
        
        # Check store overlap
        common_stores = clustering_stores.intersection(config_stores).intersection(quantity_stores)
        results["statistics"]["common_stores"] = len(common_stores)
        
        if len(common_stores) < len(clustering_stores) * 0.8:
            results["warnings"].append("Low store overlap between input datasets")
        
        # Check quantity data quality
        if 'quantity' in df_quantity.columns:
            qty_stats = df_quantity['quantity'].describe()
            results["statistics"]["quantity_range"] = {
                "min": qty_stats['min'],
                "max": qty_stats['max'],
                "mean": qty_stats['mean'],
                "std": qty_stats['std']
            }
            
            if qty_stats['min'] < 0:
                results["errors"].append("Negative quantities found")
                results["validation_passed"] = False
            
            if qty_stats['max'] > 1e6:
                results["warnings"].append("Very large quantities found")
        
        # Check for missing values
        missing_counts = df_quantity.isnull().sum()
        results["statistics"]["missing_values"] = missing_counts.to_dict()
        
        if missing_counts.sum() > 0:
            results["warnings"].append(f"Found {missing_counts.sum()} missing values in quantity data")
        
    except Exception as e:
        results["errors"].append(f"Input validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_step8_results(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate Step 8 results data.
    
    Args:
        df: Step 8 results DataFrame
        
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
        required_cols = ['str_code', 'cluster_id', 'imbalanced_categories_count', 'total_imbalance_value', 'total_quantity_adjustment']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            results["errors"].append(f"Missing required columns: {missing_cols}")
            results["validation_passed"] = False
        
        # Check data types
        if 'imbalanced_categories_count' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['imbalanced_categories_count']):
                results["errors"].append("imbalanced_categories_count must be numeric")
                results["validation_passed"] = False
        
        if 'total_imbalance_value' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['total_imbalance_value']):
                results["errors"].append("total_imbalance_value must be numeric")
                results["validation_passed"] = False
        
        # Check value ranges
        if 'imbalanced_categories_count' in df.columns:
            imbalance_count_stats = df['imbalanced_categories_count'].describe()
            results["statistics"]["imbalance_count_range"] = {
                "min": imbalance_count_stats['min'],
                "max": imbalance_count_stats['max'],
                "mean": imbalance_count_stats['mean']
            }
            
            if imbalance_count_stats['min'] < 0:
                results["errors"].append("Negative imbalanced_categories_count found")
                results["validation_passed"] = False
        
        if 'total_imbalance_value' in df.columns:
            imbalance_value_stats = df['total_imbalance_value'].describe()
            results["statistics"]["imbalance_value_range"] = {
                "min": imbalance_value_stats['min'],
                "max": imbalance_value_stats['max'],
                "mean": imbalance_value_stats['mean']
            }
            
            if imbalance_value_stats['min'] < 0:
                results["warnings"].append("Negative imbalance values found")
        
        # Check quantity adjustments
        if 'total_quantity_adjustment' in df.columns:
            qty_adj_stats = df['total_quantity_adjustment'].describe()
            results["statistics"]["quantity_adjustment_range"] = {
                "min": qty_adj_stats['min'],
                "max": qty_adj_stats['max'],
                "mean": qty_adj_stats['mean']
            }
            
            # Check for extreme adjustments
            extreme_increases = df[df['total_quantity_adjustment'] > 1000]
            extreme_decreases = df[df['total_quantity_adjustment'] < -1000]
            
            if len(extreme_increases) > 0:
                results["warnings"].append(f"Found {len(extreme_increases)} stores with extreme quantity increases")
            
            if len(extreme_decreases) > 0:
                results["warnings"].append(f"Found {len(extreme_decreases)} stores with extreme quantity decreases")
        
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
                results["warnings"].append(f"Only {unique_stores} stores in results")
        
    except Exception as e:
        results["errors"].append(f"Results validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_step8_imbalances(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate Step 8 imbalances data.
    
    Args:
        df: Step 8 imbalances DataFrame
        
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
        required_cols = ['str_code', 'cluster_id', 'category', 'imbalance_type', 'current_quantity', 'recommended_quantity', 'quantity_adjustment']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            results["errors"].append(f"Missing required columns: {missing_cols}")
            results["validation_passed"] = False
        
        # Check imbalance types
        if 'imbalance_type' in df.columns:
            valid_types = ['overstocked', 'understocked', 'balanced']
            invalid_types = df[~df['imbalance_type'].isin(valid_types)]['imbalance_type'].unique()
            if len(invalid_types) > 0:
                results["errors"].append(f"Invalid imbalance types: {invalid_types}")
                results["validation_passed"] = False
            
            type_counts = df['imbalance_type'].value_counts()
            results["statistics"]["imbalance_type_distribution"] = type_counts.to_dict()
        
        # Check quantity relationships
        if all(col in df.columns for col in ['current_quantity', 'recommended_quantity', 'quantity_adjustment']):
            # Verify quantity_adjustment = recommended_quantity - current_quantity
            calculated_adjustment = df['recommended_quantity'] - df['current_quantity']
            adjustment_diff = abs(df['quantity_adjustment'] - calculated_adjustment)
            
            if adjustment_diff.max() > 0.01:  # Allow small floating point differences
                results["warnings"].append("Quantity adjustment calculations may be inconsistent")
            
            # Check for negative quantities
            negative_current = df[df['current_quantity'] < 0]
            negative_recommended = df[df['recommended_quantity'] < 0]
            
            if len(negative_current) > 0:
                results["errors"].append(f"Found {len(negative_current)} negative current quantities")
                results["validation_passed"] = False
            
            if len(negative_recommended) > 0:
                results["errors"].append(f"Found {len(negative_recommended)} negative recommended quantities")
                results["validation_passed"] = False
        
        # Check quantity ranges
        if 'current_quantity' in df.columns:
            current_qty_stats = df['current_quantity'].describe()
            results["statistics"]["current_quantity_range"] = {
                "min": current_qty_stats['min'],
                "max": current_qty_stats['max'],
                "mean": current_qty_stats['mean']
            }
        
        if 'recommended_quantity' in df.columns:
            recommended_qty_stats = df['recommended_quantity'].describe()
            results["statistics"]["recommended_quantity_range"] = {
                "min": recommended_qty_stats['min'],
                "max": recommended_qty_stats['max'],
                "mean": recommended_qty_stats['mean']
            }
        
        if 'quantity_adjustment' in df.columns:
            adjustment_stats = df['quantity_adjustment'].describe()
            results["statistics"]["quantity_adjustment_range"] = {
                "min": adjustment_stats['min'],
                "max": adjustment_stats['max'],
                "mean": adjustment_stats['mean']
            }
        
        # Check category distribution
        if 'category' in df.columns:
            category_counts = df['category'].value_counts()
            results["statistics"]["category_distribution"] = category_counts.to_dict()
            
            if len(category_counts) < 3:
                results["warnings"].append(f"Only {len(category_counts)} categories found")
        
        # Check for extreme adjustments
        if 'quantity_adjustment' in df.columns:
            extreme_increases = df[df['quantity_adjustment'] > 500]
            extreme_decreases = df[df['quantity_adjustment'] < -500]
            
            if len(extreme_increases) > 0:
                results["warnings"].append(f"Found {len(extreme_increases)} extreme quantity increases")
            
            if len(extreme_decreases) > 0:
                results["warnings"].append(f"Found {len(extreme_decreases)} extreme quantity decreases")
        
    except Exception as e:
        results["errors"].append(f"Imbalances validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_step8_files(period_label: str, analysis_level: str = "spu", data_dir: str = "output") -> Dict[str, Any]:
    """
    Validate Step 8 output files.
    
    Args:
        period_label: Period label for file naming
        analysis_level: Analysis level (spu or subcategory)
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
            f"rule8_imbalanced_{analysis_level}_results_{period_label}.csv",
            f"rule8_imbalanced_{analysis_level}_imbalances_{period_label}.csv",
            f"rule8_imbalanced_{analysis_level}_summary_{period_label}.md"
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
                        if "results" in filename:
                            validation_result = validate_step8_results(df)
                            file_results["validation"] = validation_result
                        elif "imbalances" in filename:
                            validation_result = validate_step8_imbalances(df)
                            file_results["validation"] = validation_result
                        
                        results["file_validation"][filename] = file_results
                        
                        if file_results.get("validation", {}).get("validation_passed", True) == False:
                            results["warnings"].append(f"Validation issues in {filename}")
                    
                    elif filename.endswith('.md'):
                        file_results = {
                            "exists": True,
                            "file_size_mb": file_path.stat().st_size / (1024 * 1024),
                            "data_type": "markdown"
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


def validate_step8_complete(period_label: str, analysis_level: str = "spu", data_dir: str = "output") -> Dict[str, Any]:
    """
    Complete validation for Step 8.
    
    Args:
        period_label: Period label for validation
        analysis_level: Analysis level (spu or subcategory)
        data_dir: Directory containing output files
        
    Returns:
        Complete validation results
    """
    logger.info(f"Starting complete Step 8 validation for period {period_label}, level {analysis_level}")
    
    # Initialize validation results
    validation_results = {
        "validation_passed": False,  # Requires real data validation
        "input_validation": {},
        "output_validation": {},
        "file_validation": {},
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        # File validation
        file_validation = validate_step8_files(period_label, analysis_level, data_dir)
        validation_results["file_validation"] = file_validation
        validation_results["validation_passed"] = file_validation["validation_passed"]
        validation_results["errors"].extend(file_validation["errors"])
        validation_results["warnings"].extend(file_validation["warnings"])
        
        # Load and validate output data
        data_path = Path(data_dir)
        results_file = data_path / f"rule8_imbalanced_{analysis_level}_results_{period_label}.csv"
        imbalances_file = data_path / f"rule8_imbalanced_{analysis_level}_imbalances_{period_label}.csv"
        
        if results_file.exists():
            df_results = pd.read_csv(results_file)
            results_validation = validate_step8_results(df_results)
            validation_results["output_validation"]["results"] = results_validation
            validation_results["statistics"]["results_records"] = len(df_results)
            
            if not results_validation["validation_passed"]:
                validation_results["validation_passed"] = False
        
        if imbalances_file.exists():
            df_imbalances = pd.read_csv(imbalances_file)
            imbalances_validation = validate_step8_imbalances(df_imbalances)
            validation_results["output_validation"]["imbalances"] = imbalances_validation
            validation_results["statistics"]["imbalances_records"] = len(df_imbalances)
            
            if not imbalances_validation["validation_passed"]:
                validation_results["validation_passed"] = False
        
        # Overall statistics
        validation_results["statistics"]["total_errors"] = len(validation_results["errors"])
        validation_results["statistics"]["total_warnings"] = len(validation_results["warnings"])
        validation_results["statistics"]["validation_timestamp"] = datetime.now().isoformat()
        
    except Exception as e:
        validation_results["errors"].append(f"Complete validation error: {str(e)}")
        validation_results["validation_passed"] = False
        logger.error(f"Step 8 validation failed: {str(e)}")
    
    return validation_results


# Export all validators
__all__ = [
    'validate_step8_inputs',
    'validate_step8_results',
    'validate_step8_imbalances',
    'validate_step8_files',
    'validate_step8_complete'
]


