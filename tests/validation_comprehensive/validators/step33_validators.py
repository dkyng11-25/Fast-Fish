#!/usr/bin/env python3
"""
Step 33 Store-Level Merchandising Rules Validators

This module contains validators for store-level merchandising rules validation from Step 33.

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

def validate_step33_complete(
    output_base_dir: str = "tests/test_output"
) -> Dict[str, Any]:
    """
    Validates the outputs of Step 33: Store-Level Merchandising Rule Generation.
    Checks for merchandising rules CSV and report.
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
    
    # Expected output files (with period patterns)
    expected_patterns = {
        "merchandising_rules": f"{output_dir}/store_level_merchandising_rules_*.csv",
        "rules_report": f"{output_dir}/store_level_merchandising_rules_report_*.md"
    }

    for file_type, pattern in expected_patterns.items():
        candidate_files = sorted(glob.glob(str(pattern)), key=os.path.getctime, reverse=True)
        
        file_validation = {"exists": False, "count": len(candidate_files)}
        
        if candidate_files:
            file_path = Path(candidate_files[0])
            file_validation["exists"] = True
            file_validation["latest"] = str(file_path)
            
            if file_path.stat().st_size == 0:
                validation_results["validation_passed"] = False
                validation_results["warnings"].append(f"Empty file found for {file_type}: {file_path.name}")
                file_validation["size_bytes"] = 0
            else:
                file_validation["size_bytes"] = file_path.stat().st_size
                file_validation["size_mb"] = round(file_path.stat().st_size / (1024 * 1024), 3)
                
                # File-specific validation
                if file_path.suffix == '.csv':
                    try:
                        df = pd.read_csv(file_path)
                        file_validation["rows"] = len(df)
                        file_validation["columns"] = list(df.columns)
                        
                        if df.empty:
                            validation_results["validation_passed"] = False
                            validation_results["warnings"].append(f"CSV file is empty: {file_path.name}")
                        else:
                            # Validate specific columns for merchandising rules
                            if file_type == "merchandising_rules":
                                expected_cols = ["str_code", "cluster_id", "style_allocation", "capacity_guideline", "temperature_adjustment", "merchandising_rule"]
                                missing_cols = [col for col in expected_cols if col not in df.columns]
                                if missing_cols:
                                    validation_results["warnings"].append(f"Missing expected columns in {file_type}: {missing_cols}")
                                
                                # Validate store codes
                                if "str_code" in df.columns:
                                    if not df["str_code"].dtype in ['int64', 'object']:
                                        validation_results["warnings"].append("str_code should be integer or string")
                                    else:
                                        if df["str_code"].dtype == 'int64':
                                            if (df["str_code"] < 10000).any() or (df["str_code"] > 99999).any():
                                                validation_results["warnings"].append("str_code should be between 10000 and 99999")
                                
                                # Validate cluster IDs
                                if "cluster_id" in df.columns:
                                    if not df["cluster_id"].dtype in ['int64']:
                                        validation_results["warnings"].append("cluster_id should be integer")
                                    else:
                                        if (df["cluster_id"] < 0).any() or (df["cluster_id"] > 50).any():
                                            validation_results["warnings"].append("cluster_id should be between 0 and 50")
                                
                                # Validate style allocation
                                if "style_allocation" in df.columns:
                                    valid_allocations = ["Fashion-Heavy", "Balanced-Mix", "Basic-Focus"]
                                    invalid_allocations = df[~df["style_allocation"].isin(valid_allocations)]["style_allocation"].unique()
                                    if len(invalid_allocations) > 0:
                                        validation_results["warnings"].append(f"Invalid style_allocation values: {invalid_allocations}")
                                
                                # Validate capacity guidelines
                                if "capacity_guideline" in df.columns:
                                    valid_guidelines = ["Large-Volume", "High-Capacity", "Efficient-Size"]
                                    invalid_guidelines = df[~df["capacity_guideline"].isin(valid_guidelines)]["capacity_guideline"].unique()
                                    if len(invalid_guidelines) > 0:
                                        validation_results["warnings"].append(f"Invalid capacity_guideline values: {invalid_guidelines}")
                                
                                # Validate temperature adjustments
                                if "temperature_adjustment" in df.columns:
                                    valid_adjustments = ["Warm-South", "Moderate-Central", "Cool-North"]
                                    invalid_adjustments = df[~df["temperature_adjustment"].isin(valid_adjustments)]["temperature_adjustment"].unique()
                                    if len(invalid_adjustments) > 0:
                                        validation_results["warnings"].append(f"Invalid temperature_adjustment values: {invalid_adjustments}")
                                
                                file_validation["total_stores"] = len(df)
                                file_validation["unique_clusters"] = df["cluster_id"].nunique() if "cluster_id" in df.columns else 0
                                file_validation["unique_stores"] = df["str_code"].nunique() if "str_code" in df.columns else 0
                                
                                # Analyze rule distribution
                                if "style_allocation" in df.columns:
                                    style_dist = df["style_allocation"].value_counts().to_dict()
                                    file_validation["style_allocation_distribution"] = style_dist
                                
                                if "capacity_guideline" in df.columns:
                                    capacity_dist = df["capacity_guideline"].value_counts().to_dict()
                                    file_validation["capacity_guideline_distribution"] = capacity_dist
                                
                    except Exception as e:
                        validation_results["validation_passed"] = False
                        validation_results["errors"].append(f"Error reading CSV {file_path.name}: {e}")
                        
                elif file_path.suffix == '.md':
                    content = file_path.read_text()
                    file_validation["content_length"] = len(content)
                    file_validation["content_preview"] = content[:200] + "..." if len(content) > 200 else content
                    
                    # Validate report content
                    if file_type == "rules_report":
                        expected_sections = ["Store-Level Merchandising Rules", "Rule Distribution", "Cluster Analysis", "Recommendations"]
                        missing_sections = [section for section in expected_sections if section not in content]
                        if missing_sections:
                            validation_results["warnings"].append(f"Missing expected sections in {file_type}: {missing_sections}")
                        
            validation_results["files"][file_type] = file_validation
        else:
            validation_results["validation_passed"] = False
            validation_results["warnings"].append(f"Missing expected Step 33 output: {pattern}")

    # Calculate statistics
    validation_results["statistics"]["files_found"] = sum(1 for f in validation_results["files"].values() if f["exists"])
    validation_results["statistics"]["total_files_expected"] = len(expected_patterns)
    validation_results["statistics"]["validation_timestamp"] = datetime.now().isoformat()
    
    return validation_results

def validate_merchandising_rules_csv(file_path: str) -> Dict[str, Any]:
    """
    Validates the store-level merchandising rules CSV file specifically.
    """
    validation_results = {
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        df = pd.read_csv(file_path)
        
        # Check required columns
        required_columns = ["str_code", "cluster_id", "style_allocation", "capacity_guideline", "temperature_adjustment", "merchandising_rule"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            validation_results["validation_passed"] = False
            validation_results["errors"].append(f"Missing required columns: {missing_columns}")
            return validation_results
        
        # Validate store codes
        if not df["str_code"].dtype in ['int64', 'object']:
            validation_results["warnings"].append("str_code should be integer or string")
        else:
            if df["str_code"].dtype == 'int64':
                if (df["str_code"] < 10000).any() or (df["str_code"] > 99999).any():
                    validation_results["warnings"].append("str_code should be between 10000 and 99999")
        
        # Validate cluster IDs
        if not df["cluster_id"].dtype in ['int64']:
            validation_results["warnings"].append("cluster_id should be integer")
        else:
            if (df["cluster_id"] < 0).any() or (df["cluster_id"] > 50).any():
                validation_results["warnings"].append("cluster_id should be between 0 and 50")
        
        # Validate style allocation values
        valid_allocations = ["Fashion-Heavy", "Balanced-Mix", "Basic-Focus"]
        invalid_allocations = df[~df["style_allocation"].isin(valid_allocations)]["style_allocation"].unique()
        if len(invalid_allocations) > 0:
            validation_results["warnings"].append(f"Invalid style_allocation values: {invalid_allocations}")
        
        # Validate capacity guidelines
        valid_guidelines = ["Large-Volume", "High-Capacity", "Efficient-Size"]
        invalid_guidelines = df[~df["capacity_guideline"].isin(valid_guidelines)]["capacity_guideline"].unique()
        if len(invalid_guidelines) > 0:
            validation_results["warnings"].append(f"Invalid capacity_guideline values: {invalid_guidelines}")
        
        # Validate temperature adjustments
        valid_adjustments = ["Warm-South", "Moderate-Central", "Cool-North"]
        invalid_adjustments = df[~df["temperature_adjustment"].isin(valid_adjustments)]["temperature_adjustment"].unique()
        if len(invalid_adjustments) > 0:
            validation_results["warnings"].append(f"Invalid temperature_adjustment values: {invalid_adjustments}")
        
        # Check for duplicate store codes
        if df["str_code"].duplicated().any():
            validation_results["warnings"].append("Found duplicate store codes in merchandising rules")
        
        # Statistics
        validation_results["statistics"]["total_stores"] = len(df)
        validation_results["statistics"]["unique_stores"] = df["str_code"].nunique()
        validation_results["statistics"]["unique_clusters"] = df["cluster_id"].nunique()
        validation_results["statistics"]["style_allocation_distribution"] = df["style_allocation"].value_counts().to_dict()
        validation_results["statistics"]["capacity_guideline_distribution"] = df["capacity_guideline"].value_counts().to_dict()
        validation_results["statistics"]["temperature_adjustment_distribution"] = df["temperature_adjustment"].value_counts().to_dict()
        
    except Exception as e:
        validation_results["validation_passed"] = False
        validation_results["errors"].append(f"Error reading CSV file: {e}")
    
    return validation_results

if __name__ == "__main__":
    print("Testing Step 33 Store-Level Merchandising Rules Validator...")
    results = validate_step33_complete("output")
    print(f"Validation passed: {results['validation_passed']}")
    print(f"Files found: {results['statistics']['files_found']}/{results['statistics']['total_files_expected']}")
    if results['errors']:
        print(f"Errors: {results['errors']}")
    if results['warnings']:
        print(f"Warnings: {results['warnings']}")


