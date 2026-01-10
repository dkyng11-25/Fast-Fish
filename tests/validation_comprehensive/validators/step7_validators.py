#!/usr/bin/env python3
"""
Step 7: Missing Category Rule Validators

Validation functions for Step 7 - Missing Category/SPU with Quantity Recommendations.
Provides comprehensive validation for missing category rule processing.

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


def validate_step7_inputs(df_clustering: pd.DataFrame, df_sales: pd.DataFrame, df_config: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate Step 7 input data.
    
    Args:
        df_clustering: Clustering results DataFrame
        df_sales: Sales data DataFrame
        df_config: Store config DataFrame
        
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
        
        # Validate sales data
        required_sales_cols = ['str_code', 'spu_code', 'spu_sales_amt']
        missing_sales_cols = [col for col in required_sales_cols if col not in df_sales.columns]
        if missing_sales_cols:
            results["errors"].append(f"Missing required sales columns: {missing_sales_cols}")
            results["validation_passed"] = False
        
        # Validate store config data
        if 'str_code' not in df_config.columns:
            results["errors"].append("Missing 'str_code' column in store config data")
            results["validation_passed"] = False
        
        # Check data consistency
        clustering_stores = set(df_clustering['str_code'].unique())
        sales_stores = set(df_sales['str_code'].unique())
        config_stores = set(df_config['str_code'].unique())
        
        results["statistics"]["clustering_stores"] = len(clustering_stores)
        results["statistics"]["sales_stores"] = len(sales_stores)
        results["statistics"]["config_stores"] = len(config_stores)
        
        # Check store overlap
        common_stores = clustering_stores.intersection(sales_stores).intersection(config_stores)
        results["statistics"]["common_stores"] = len(common_stores)
        
        if len(common_stores) < len(clustering_stores) * 0.8:
            results["warnings"].append("Low store overlap between input datasets")
        
        # Check sales data quality
        if 'spu_sales_amt' in df_sales.columns:
            sales_stats = df_sales['spu_sales_amt'].describe()
            results["statistics"]["sales_amount_range"] = {
                "min": sales_stats['min'],
                "max": sales_stats['max'],
                "mean": sales_stats['mean'],
                "std": sales_stats['std']
            }
            
            if sales_stats['min'] < 0:
                results["warnings"].append("Negative sales amounts found")
            
            if sales_stats['max'] > 1e6:
                results["warnings"].append("Very large sales amounts found")
        
    except Exception as e:
        results["errors"].append(f"Input validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_step7_results(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate Step 7 results data.
    
    Args:
        df: Step 7 results DataFrame
        
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
        required_cols = ['str_code', 'cluster_id', 'missing_spus_count', 'total_opportunity_value', 'total_quantity_needed']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            results["errors"].append(f"Missing required columns: {missing_cols}")
            results["validation_passed"] = False
        
        # Check data types
        if 'missing_spus_count' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['missing_spus_count']):
                results["errors"].append("missing_spus_count must be numeric")
                results["validation_passed"] = False
        
        if 'total_opportunity_value' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['total_opportunity_value']):
                results["errors"].append("total_opportunity_value must be numeric")
                results["validation_passed"] = False
        
        # Check value ranges
        if 'missing_spus_count' in df.columns:
            missing_count_stats = df['missing_spus_count'].describe()
            results["statistics"]["missing_spus_count_range"] = {
                "min": missing_count_stats['min'],
                "max": missing_count_stats['max'],
                "mean": missing_count_stats['mean']
            }
            
            if missing_count_stats['min'] < 0:
                results["errors"].append("Negative missing_spus_count found")
                results["validation_passed"] = False
        
        if 'total_opportunity_value' in df.columns:
            opportunity_stats = df['total_opportunity_value'].describe()
            results["statistics"]["opportunity_value_range"] = {
                "min": opportunity_stats['min'],
                "max": opportunity_stats['max'],
                "mean": opportunity_stats['mean']
            }
            
            if opportunity_stats['min'] < 0:
                results["warnings"].append("Negative opportunity values found")
        
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


def validate_step7_opportunities(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate Step 7 opportunities data.
    
    Args:
        df: Step 7 opportunities DataFrame
        
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
        required_cols = ['str_code', 'cluster_id', 'spu_code', 'opportunity_type', 'expected_sales_opportunity', 'recommended_quantity_change']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            results["errors"].append(f"Missing required columns: {missing_cols}")
            results["validation_passed"] = False
        
        # Check opportunity types
        if 'opportunity_type' in df.columns:
            valid_types = ['missing_spu', 'missing_category']
            invalid_types = df[~df['opportunity_type'].isin(valid_types)]['opportunity_type'].unique()
            if len(invalid_types) > 0:
                results["errors"].append(f"Invalid opportunity types: {invalid_types}")
                results["validation_passed"] = False
            
            type_counts = df['opportunity_type'].value_counts()
            results["statistics"]["opportunity_type_distribution"] = type_counts.to_dict()
        
        # Check quantity changes
        if 'recommended_quantity_change' in df.columns:
            qty_stats = df['recommended_quantity_change'].describe()
            results["statistics"]["quantity_change_range"] = {
                "min": qty_stats['min'],
                "max": qty_stats['max'],
                "mean": qty_stats['mean']
            }
            
            # Check for negative quantity changes (should be positive for missing opportunities)
            negative_qty = df[df['recommended_quantity_change'] < 0]
            if len(negative_qty) > 0:
                results["warnings"].append(f"Found {len(negative_qty)} negative quantity changes")
        
        # Check sales opportunities
        if 'expected_sales_opportunity' in df.columns:
            sales_opp_stats = df['expected_sales_opportunity'].describe()
            results["statistics"]["sales_opportunity_range"] = {
                "min": sales_opp_stats['min'],
                "max": sales_opp_stats['max'],
                "mean": sales_opp_stats['mean']
            }
            
            if sales_opp_stats['min'] < 0:
                results["warnings"].append("Negative sales opportunities found")
        
        # Check SPU code format
        if 'spu_code' in df.columns:
            spu_codes = df['spu_code'].unique()
            results["statistics"]["unique_spus"] = len(spu_codes)
            
            # Check for valid SPU code format (should start with 'SPU')
            invalid_spus = df[~df['spu_code'].str.startswith('SPU', na=False)]['spu_code'].unique()
            if len(invalid_spus) > 0:
                results["warnings"].append(f"Found {len(invalid_spus)} SPU codes not starting with 'SPU'")
        
    except Exception as e:
        results["errors"].append(f"Opportunities validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_step7_files(period_label: str, analysis_level: str = "spu", data_dir: str = "output") -> Dict[str, Any]:
    """
    Validate Step 7 output files.
    
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
            f"rule7_missing_{analysis_level}_sellthrough_results_{period_label}.csv",
            f"rule7_missing_{analysis_level}_sellthrough_opportunities_{period_label}.csv",
            f"rule7_missing_{analysis_level}_sellthrough_summary_{period_label}.md"
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
                            validation_result = validate_step7_results(df)
                            file_results["validation"] = validation_result
                        elif "opportunities" in filename:
                            validation_result = validate_step7_opportunities(df)
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


def validate_step7_complete(period_label: str, analysis_level: str = "spu", data_dir: str = "output") -> Dict[str, Any]:
    """
    Complete validation for Step 7.
    
    Args:
        period_label: Period label for validation
        analysis_level: Analysis level (spu or subcategory)
        data_dir: Directory containing output files
        
    Returns:
        Complete validation results
    """
    logger.info(f"Starting complete Step 7 validation for period {period_label}, level {analysis_level}")
    
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
        file_validation = validate_step7_files(period_label, analysis_level, data_dir)
        validation_results["file_validation"] = file_validation
        validation_results["validation_passed"] = file_validation["validation_passed"]
        validation_results["errors"].extend(file_validation["errors"])
        validation_results["warnings"].extend(file_validation["warnings"])
        
        # Load and validate output data
        data_path = Path(data_dir)
        results_file = data_path / f"rule7_missing_{analysis_level}_sellthrough_results_{period_label}.csv"
        opportunities_file = data_path / f"rule7_missing_{analysis_level}_sellthrough_opportunities_{period_label}.csv"
        
        if results_file.exists():
            df_results = pd.read_csv(results_file)
            results_validation = validate_step7_results(df_results)
            validation_results["output_validation"]["results"] = results_validation
            validation_results["statistics"]["results_records"] = len(df_results)
            
            if not results_validation["validation_passed"]:
                validation_results["validation_passed"] = False
        
        if opportunities_file.exists():
            df_opportunities = pd.read_csv(opportunities_file)
            opportunities_validation = validate_step7_opportunities(df_opportunities)
            validation_results["output_validation"]["opportunities"] = opportunities_validation
            validation_results["statistics"]["opportunities_records"] = len(df_opportunities)
            
            if not opportunities_validation["validation_passed"]:
                validation_results["validation_passed"] = False
        
        # Overall statistics
        validation_results["statistics"]["total_errors"] = len(validation_results["errors"])
        validation_results["statistics"]["total_warnings"] = len(validation_results["warnings"])
        validation_results["statistics"]["validation_timestamp"] = datetime.now().isoformat()
        
    except Exception as e:
        validation_results["errors"].append(f"Complete validation error: {str(e)}")
        validation_results["validation_passed"] = False
        logger.error(f"Step 7 validation failed: {str(e)}")
    
    return validation_results


# Export all validators
__all__ = [
    'validate_step7_inputs',
    'validate_step7_results',
    'validate_step7_opportunities',
    'validate_step7_files',
    'validate_step7_complete'
]


