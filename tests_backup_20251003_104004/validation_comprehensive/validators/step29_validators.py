#!/usr/bin/env python3
"""
Step 29 Supply-Demand Gap Analysis Validators

This module contains validators for supply-demand gap analysis validation from Step 29.

Author: Data Pipeline
Date: 2025-01-16
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import os
import glob
from datetime import datetime
import json

logger = logging.getLogger(__name__)

def validate_step29_complete(
    output_base_dir: str = "tests/test_output"
) -> Dict[str, Any]:
    """
    Validates the outputs of Step 29: Supply-Demand Gap Analysis.
    Checks for SPU variety gaps analysis, gap analysis detailed, and reports.
    """
    validation_results = {
        "validation_passed": False,  # Default to False - requires real data validation
        "files": {},
        "errors": ["No real data validation performed"],
        "warnings": ["Using default validation - real data required"],
        "statistics": {
            "validation_type": "default",
            "data_source": "unknown",
            "reliability": "low"
        }
    }

    output_dir = Path(output_base_dir)
    
    # Expected output files (based on actual Step 29 output)
    expected_files = {
        "spu_variety_gaps_analysis": f"{output_dir}/spu_variety_gaps_analysis.csv",
        "gap_analysis_detailed": f"{output_dir}/gap_analysis_detailed.csv",
        "supply_demand_gap_analysis_report": f"{output_dir}/supply_demand_gap_analysis_report.md"
    }

    for file_type, file_path in expected_files.items():
        file_validation = {"exists": False, "path": str(file_path)}
        
        if Path(file_path).exists():
            file_validation["exists"] = True
            file_validation["size_bytes"] = Path(file_path).stat().st_size
            file_validation["size_mb"] = round(file_validation["size_bytes"] / (1024 * 1024), 3)
            
            if file_validation["size_bytes"] == 0:
                validation_results["validation_passed"] = False
                validation_results["warnings"].append(f"Empty file found: {file_type}")
            else:
                # Validate file content based on type
                try:
                    if file_path.endswith('.csv'):
                        # Try different encodings for CSV files
                        try:
                            df = pd.read_csv(file_path, encoding='utf-8')
                        except UnicodeDecodeError:
                            try:
                                df = pd.read_csv(file_path, encoding='iso-8859-1')
                            except UnicodeDecodeError:
                                df = pd.read_csv(file_path, encoding='latin-1')
                        file_validation["rows"] = len(df)
                        file_validation["columns"] = list(df.columns)
                        
                        if df.empty:
                            validation_results["validation_passed"] = False
                            validation_results["warnings"].append(f"CSV file is empty: {file_type}")
                        else:
                            # Validate specific columns based on file type
                            if file_type == "spu_variety_gaps_analysis":
                                expected_cols = ["str_code", "cluster", "big_class_name", "sub_cate_name", "missing_spu_count"]
                                missing_cols = [col for col in expected_cols if col not in df.columns]
                                if missing_cols:
                                    validation_results["warnings"].append(f"Missing expected columns in {file_type}: {missing_cols}")
                                
                                # Validate data quality
                                if "missing_spu_count" in df.columns:
                                    if not df["missing_spu_count"].dtype in ['int64', 'float64']:
                                        validation_results["warnings"].append("missing_spu_count should be numeric")
                                    if (df["missing_spu_count"] < 0).any():
                                        validation_results["warnings"].append("Found negative missing_spu_count values")
                                
                                if "str_code" in df.columns:
                                    if not df["str_code"].dtype in ['int64']:
                                        validation_results["warnings"].append("str_code should be integer")
                                    if (df["str_code"] < 10000).any() or (df["str_code"] > 99999).any():
                                        validation_results["warnings"].append("str_code should be between 10000 and 99999")
                                
                                file_validation["unique_stores"] = df["str_code"].nunique() if "str_code" in df.columns else 0
                                file_validation["unique_clusters"] = df["cluster"].nunique() if "cluster" in df.columns else 0
                                file_validation["total_gaps"] = df["missing_spu_count"].sum() if "missing_spu_count" in df.columns else 0
                                
                            elif file_type == "gap_analysis_detailed":
                                # Based on actual output: cluster_id,total_products,total_stores,core_count,core_percentage,core_gap,core_gap_severity,seasonal_count,seasonal_percentage,seasonal_gap,seasonal_gap_severity,filler_count,filler_percentage,filler_gap,filler_gap_severity,clearance_count,clearance_percentage,clearance_gap,clearance_gap_severity,category_count,subcategory_count
                                expected_cols = ["cluster_id", "total_products", "core_gap", "seasonal_gap", "filler_gap", "clearance_gap"]
                                missing_cols = [col for col in expected_cols if col not in df.columns]
                                if missing_cols:
                                    validation_results["warnings"].append(f"Missing expected columns in {file_type}: {missing_cols}")
                                
                                # Validate gap analysis data
                                gap_columns = ["core_gap", "seasonal_gap", "filler_gap", "clearance_gap"]
                                for col in gap_columns:
                                    if col in df.columns:
                                        if not df[col].dtype in ['int64', 'float64']:
                                            validation_results["warnings"].append(f"{col} should be numeric")
                                
                                # Validate cluster IDs
                                if "cluster_id" in df.columns:
                                    if not df["cluster_id"].dtype in ['int64']:
                                        validation_results["warnings"].append("cluster_id should be integer")
                                    if (df["cluster_id"] < 0).any() or (df["cluster_id"] > 50).any():
                                        validation_results["warnings"].append("cluster_id should be between 0 and 50")
                                
                                # Validate gap severity values
                                severity_columns = ["core_gap_severity", "seasonal_gap_severity", "filler_gap_severity", "clearance_gap_severity"]
                                valid_severities = ["CRITICAL", "SIGNIFICANT", "MODERATE", "OPTIMAL"]
                                for col in severity_columns:
                                    if col in df.columns:
                                        invalid_severities = df[~df[col].isin(valid_severities)][col].unique()
                                        if len(invalid_severities) > 0:
                                            validation_results["warnings"].append(f"Invalid {col} values found: {invalid_severities}")
                                
                                file_validation["total_clusters"] = df["cluster_id"].nunique() if "cluster_id" in df.columns else 0
                                file_validation["total_products"] = df["total_products"].sum() if "total_products" in df.columns else 0
                                file_validation["total_stores"] = df["total_stores"].sum() if "total_stores" in df.columns else 0
                                
                                # Calculate gap statistics
                                gap_stats = {}
                                for col in gap_columns:
                                    if col in df.columns:
                                        gap_stats[f"{col}_total"] = df[col].sum()
                                        gap_stats[f"{col}_avg"] = df[col].mean()
                                        gap_stats[f"{col}_min"] = df[col].min()
                                        gap_stats[f"{col}_max"] = df[col].max()
                                file_validation["gap_statistics"] = gap_stats
                                
                    elif file_path.endswith('.md'):
                        content = Path(file_path).read_text()
                        file_validation["content_length"] = len(content)
                        file_validation["content_preview"] = content[:200] + "..." if len(content) > 200 else content
                        
                        # Check for key content
                        if "gap" not in content.lower():
                            validation_results["warnings"].append(f"Missing gap content in {file_type}")
                        if "analysis" not in content.lower():
                            validation_results["warnings"].append(f"Missing analysis content in {file_type}")
                            
                except Exception as e:
                    validation_results["validation_passed"] = False
                    validation_results["errors"].append(f"Error reading {file_type}: {str(e)}")
        else:
            validation_results["validation_passed"] = False
            validation_results["warnings"].append(f"Missing expected Step 29 output: {file_type}")
        
        validation_results["files"][file_type] = file_validation

    # Overall validation summary
    validation_results["statistics"]["total_files_expected"] = len(expected_files)
    validation_results["statistics"]["files_found"] = sum(1 for f in validation_results["files"].values() if f["exists"])
    validation_results["statistics"]["validation_timestamp"] = datetime.now().isoformat()
    
    return validation_results

def validate_spu_variety_gaps_analysis(file_path: str) -> Dict[str, Any]:
    """
    Validates SPU variety gaps analysis CSV file specifically.
    """
    validation_results = {
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        # Try different encodings for CSV files
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file_path, encoding='iso-8859-1')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='latin-1')
        
        # Check required columns
        required_columns = ["str_code", "cluster", "big_class_name", "sub_cate_name", "missing_spu_count"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            validation_results["validation_passed"] = False
            validation_results["errors"].append(f"Missing required columns: {missing_columns}")
            return validation_results
        
        # Validate data types
        if not df["str_code"].dtype in ['int64']:
            validation_results["validation_passed"] = False
            validation_results["errors"].append("str_code should be integer")
        
        if not df["missing_spu_count"].dtype in ['int64', 'float64']:
            validation_results["validation_passed"] = False
            validation_results["errors"].append("missing_spu_count should be numeric")
        
        # Validate store codes
        if (df["str_code"] < 10000).any() or (df["str_code"] > 99999).any():
            validation_results["validation_passed"] = False
            validation_results["errors"].append("str_code should be between 10000 and 99999")
        
        # Validate cluster IDs
        if (df["cluster"] < 0).any() or (df["cluster"] > 50).any():
            validation_results["warnings"].append("cluster should be between 0 and 50")
        
        # Validate missing SPU counts
        if (df["missing_spu_count"] < 0).any():
            validation_results["validation_passed"] = False
            validation_results["errors"].append("Found negative missing_spu_count values")
        
        # Statistics
        validation_results["statistics"]["total_records"] = len(df)
        validation_results["statistics"]["unique_stores"] = df["str_code"].nunique()
        validation_results["statistics"]["unique_clusters"] = df["cluster"].nunique()
        validation_results["statistics"]["total_gaps"] = df["missing_spu_count"].sum()
        validation_results["statistics"]["avg_gaps_per_store"] = df["missing_spu_count"].mean()
        validation_results["statistics"]["max_gaps"] = df["missing_spu_count"].max()
        
        # Category analysis
        if "big_class_name" in df.columns:
            validation_results["statistics"]["unique_categories"] = df["big_class_name"].nunique()
            validation_results["statistics"]["category_distribution"] = df["big_class_name"].value_counts().to_dict()
        
        if "sub_cate_name" in df.columns:
            validation_results["statistics"]["unique_subcategories"] = df["sub_cate_name"].nunique()
        
    except Exception as e:
        validation_results["validation_passed"] = False
        validation_results["errors"].append(f"Error reading file: {str(e)}")
    
    return validation_results

def validate_gap_analysis_detailed(file_path: str) -> Dict[str, Any]:
    """
    Validates gap analysis detailed CSV file specifically.
    """
    validation_results = {
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        # Try different encodings for CSV files
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file_path, encoding='iso-8859-1')
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding='latin-1')
        
        # Check required columns (based on actual output structure)
        required_columns = ["cluster_id", "total_products", "core_gap", "seasonal_gap", "filler_gap", "clearance_gap"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            validation_results["validation_passed"] = False
            validation_results["errors"].append(f"Missing required columns: {missing_columns}")
            return validation_results
        
        # Validate data types
        if not df["cluster_id"].dtype in ['int64']:
            validation_results["validation_passed"] = False
            validation_results["errors"].append("cluster_id should be integer")
        
        if not df["total_products"].dtype in ['int64']:
            validation_results["validation_passed"] = False
            validation_results["errors"].append("total_products should be integer")
        
        # Validate cluster IDs
        if (df["cluster_id"] < 0).any() or (df["cluster_id"] > 50).any():
            validation_results["warnings"].append("cluster_id should be between 0 and 50")
        
        # Validate total products
        if (df["total_products"] < 0).any():
            validation_results["validation_passed"] = False
            validation_results["errors"].append("Found negative total_products values")
        
        # Validate gap columns
        gap_columns = ["core_gap", "seasonal_gap", "filler_gap", "clearance_gap"]
        for col in gap_columns:
            if col in df.columns:
                if not df[col].dtype in ['int64', 'float64']:
                    validation_results["warnings"].append(f"{col} should be numeric")
        
        # Validate gap severity columns
        severity_columns = ["core_gap_severity", "seasonal_gap_severity", "filler_gap_severity", "clearance_gap_severity"]
        valid_severities = ["CRITICAL", "SIGNIFICANT", "MODERATE", "OPTIMAL"]
        for col in severity_columns:
            if col in df.columns:
                invalid_severities = df[~df[col].isin(valid_severities)][col].unique()
                if len(invalid_severities) > 0:
                    validation_results["warnings"].append(f"Invalid {col} values found: {invalid_severities}")
        
        # Statistics
        validation_results["statistics"]["total_clusters"] = len(df)
        validation_results["statistics"]["unique_clusters"] = df["cluster_id"].nunique()
        validation_results["statistics"]["total_products"] = df["total_products"].sum()
        validation_results["statistics"]["avg_products_per_cluster"] = df["total_products"].mean()
        
        # Gap analysis
        gap_stats = {}
        for col in gap_columns:
            if col in df.columns:
                gap_stats[f"{col}_total"] = df[col].sum()
                gap_stats[f"{col}_avg"] = df[col].mean()
                gap_stats[f"{col}_min"] = df[col].min()
                gap_stats[f"{col}_max"] = df[col].max()
        validation_results["statistics"]["gap_analysis"] = gap_stats
        
        # Cluster analysis
        validation_results["statistics"]["cluster_analysis"] = {
            "cluster_sizes": df["total_products"].tolist(),
            "cluster_ids": df["cluster_id"].tolist()
        }
        
    except Exception as e:
        validation_results["validation_passed"] = False
        validation_results["errors"].append(f"Error reading file: {str(e)}")
    
    return validation_results

if __name__ == "__main__":
    # Test the validator
    print("Testing Step 29 Supply-Demand Gap Analysis Validator...")
    results = validate_step29_complete("output")
    print(f"Validation passed: {results['validation_passed']}")
    print(f"Files found: {results['statistics']['files_found']}/{results['statistics']['total_files_expected']}")
    if results['errors']:
        print(f"Errors: {results['errors']}")
    if results['warnings']:
        print(f"Warnings: {results['warnings']}")
    
    # Test specific CSV validations
    if Path("output/spu_variety_gaps_analysis.csv").exists():
        print(f"\nTesting SPU variety gaps analysis validation...")
        spu_results = validate_spu_variety_gaps_analysis("output/spu_variety_gaps_analysis.csv")
        print(f"SPU validation passed: {spu_results['validation_passed']}")
        if spu_results['errors']:
            print(f"SPU errors: {spu_results['errors']}")
        if spu_results['warnings']:
            print(f"SPU warnings: {spu_results['warnings']}")
        print(f"SPU statistics: {spu_results['statistics']}")
    
    if Path("output/gap_analysis_detailed.csv").exists():
        print(f"\nTesting gap analysis detailed validation...")
        gap_results = validate_gap_analysis_detailed("output/gap_analysis_detailed.csv")
        print(f"Gap validation passed: {gap_results['validation_passed']}")
        if gap_results['errors']:
            print(f"Gap errors: {gap_results['errors']}")
        if gap_results['warnings']:
            print(f"Gap warnings: {gap_results['warnings']}")
        print(f"Gap statistics: {gap_results['statistics']}")
