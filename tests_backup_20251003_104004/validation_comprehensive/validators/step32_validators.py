#!/usr/bin/env python3
"""
Step 32 Store Allocation Validators

This module contains validators for store allocation validation from Step 32.

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

def validate_step32_complete(
    output_base_dir: str = "tests/test_output"
) -> Dict[str, Any]:
    """
    Validates the outputs of Step 32: Store-Level Quantity Allocation.
    Checks for allocation results, summary report, and validation report.
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
        "store_allocation_results": f"{output_dir}/store_level_allocation_results_*.csv",
        "allocation_summary": f"{output_dir}/store_allocation_summary_*.md",
        "allocation_validation": f"{output_dir}/store_allocation_validation_*.json",
        "allocation_adds": f"{output_dir}/store_level_allocation_adds_*.csv",
        "allocation_reduces": f"{output_dir}/store_level_allocation_reduces_*.csv"
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
                            # Validate specific columns based on file type
                            if file_type == "store_allocation_results":
                                expected_cols = ["str_code", "spu_code", "current_quantity", "allocated_quantity", "quantity_change", "allocation_weight"]
                                missing_cols = [col for col in expected_cols if col not in df.columns]
                                if missing_cols:
                                    validation_results["warnings"].append(f"Missing expected columns in {file_type}: {missing_cols}")
                                
                                # Validate allocation data
                                if "allocated_quantity" in df.columns:
                                    if not df["allocated_quantity"].dtype in ['int64', 'float64']:
                                        validation_results["warnings"].append("allocated_quantity should be numeric")
                                    if (df["allocated_quantity"] < 0).any():
                                        validation_results["warnings"].append("Found negative allocated_quantity values")
                                
                                if "quantity_change" in df.columns:
                                    if not df["quantity_change"].dtype in ['int64', 'float64']:
                                        validation_results["warnings"].append("quantity_change should be numeric")
                                
                                if "allocation_weight" in df.columns:
                                    if not df["allocation_weight"].dtype in ['int64', 'float64']:
                                        validation_results["warnings"].append("allocation_weight should be numeric")
                                    if (df["allocation_weight"] < 0).any() or (df["allocation_weight"] > 1).any():
                                        validation_results["warnings"].append("allocation_weight should be between 0 and 1")
                                
                                file_validation["total_allocations"] = len(df)
                                file_validation["unique_stores"] = df["str_code"].nunique() if "str_code" in df.columns else 0
                                file_validation["unique_spus"] = df["spu_code"].nunique() if "spu_code" in df.columns else 0
                                file_validation["avg_allocation_weight"] = df["allocation_weight"].mean() if "allocation_weight" in df.columns else 0
                                
                            elif file_type in ["allocation_adds", "allocation_reduces"]:
                                expected_cols = ["str_code", "spu_code", "quantity_change", "allocation_weight"]
                                missing_cols = [col for col in expected_cols if col not in df.columns]
                                if missing_cols:
                                    validation_results["warnings"].append(f"Missing expected columns in {file_type}: {missing_cols}")
                                
                                # Validate quantity changes
                                if "quantity_change" in df.columns:
                                    if not df["quantity_change"].dtype in ['int64', 'float64']:
                                        validation_results["warnings"].append("quantity_change should be numeric")
                                    
                                    # For adds, quantity_change should be positive
                                    if file_type == "allocation_adds" and (df["quantity_change"] <= 0).any():
                                        validation_results["warnings"].append("Found non-positive quantity_change in adds file")
                                    
                                    # For reduces, quantity_change should be negative
                                    if file_type == "allocation_reduces" and (df["quantity_change"] >= 0).any():
                                        validation_results["warnings"].append("Found non-negative quantity_change in reduces file")
                                
                                file_validation["total_changes"] = len(df)
                                file_validation["unique_stores"] = df["str_code"].nunique() if "str_code" in df.columns else 0
                                file_validation["unique_spus"] = df["spu_code"].nunique() if "spu_code" in df.columns else 0
                                file_validation["total_quantity_change"] = df["quantity_change"].sum() if "quantity_change" in df.columns else 0
                                
                    except Exception as e:
                        validation_results["validation_passed"] = False
                        validation_results["errors"].append(f"Error reading CSV {file_path.name}: {e}")
                        
                elif file_path.suffix == '.json':
                    try:
                        with open(file_path, 'r') as f:
                            json_data = json.load(f)
                        
                        file_validation["json_keys"] = list(json_data.keys()) if isinstance(json_data, dict) else "Not a dict"
                        
                        # Validate allocation validation structure
                        if file_type == "allocation_validation":
                            expected_keys = ["validation_metadata", "allocation_summary", "constraint_validation", "performance_metrics"]
                            missing_keys = [key for key in expected_keys if key not in json_data]
                            if missing_keys:
                                validation_results["warnings"].append(f"Missing expected keys in {file_type}: {missing_keys}")
                            
                            # Validate allocation summary
                            if "allocation_summary" in json_data:
                                summary = json_data["allocation_summary"]
                                if "total_allocations" in summary:
                                    if not isinstance(summary["total_allocations"], int):
                                        validation_results["warnings"].append("total_allocations should be integer")
                                if "total_stores" in summary:
                                    if not isinstance(summary["total_stores"], int):
                                        validation_results["warnings"].append("total_stores should be integer")
                                if "total_spus" in summary:
                                    if not isinstance(summary["total_spus"], int):
                                        validation_results["warnings"].append("total_spus should be integer")
                            
                            # Validate constraint validation
                            if "constraint_validation" in json_data:
                                constraints = json_data["constraint_validation"]
                                if "capacity_constraints_satisfied" in constraints:
                                    if not isinstance(constraints["capacity_constraints_satisfied"], bool):
                                        validation_results["warnings"].append("capacity_constraints_satisfied should be boolean")
                                if "weight_constraints_satisfied" in constraints:
                                    if not isinstance(constraints["weight_constraints_satisfied"], bool):
                                        validation_results["warnings"].append("weight_constraints_satisfied should be boolean")
                                
                    except Exception as e:
                        validation_results["validation_passed"] = False
                        validation_results["errors"].append(f"Error reading JSON {file_path.name}: {e}")
                        
                elif file_path.suffix == '.md':
                    content = file_path.read_text()
                    file_validation["content_length"] = len(content)
                    file_validation["content_preview"] = content[:200] + "..." if len(content) > 200 else content
                    
                    # Validate summary report content
                    if file_type == "allocation_summary":
                        expected_sections = ["Allocation Summary", "Store Performance", "SPU Distribution", "Validation Results"]
                        missing_sections = [section for section in expected_sections if section not in content]
                        if missing_sections:
                            validation_results["warnings"].append(f"Missing expected sections in {file_type}: {missing_sections}")
                        
            validation_results["files"][file_type] = file_validation
        else:
            validation_results["validation_passed"] = False
            validation_results["warnings"].append(f"Missing expected Step 32 output: {pattern}")

    # Calculate statistics
    validation_results["statistics"]["files_found"] = sum(1 for f in validation_results["files"].values() if f["exists"])
    validation_results["statistics"]["total_files_expected"] = len(expected_patterns)
    validation_results["statistics"]["validation_timestamp"] = datetime.now().isoformat()
    
    return validation_results

def validate_allocation_results_csv(file_path: str) -> Dict[str, Any]:
    """
    Validates the store allocation results CSV file specifically.
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
        required_columns = ["str_code", "spu_code", "current_quantity", "allocated_quantity", "quantity_change", "allocation_weight"]
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
        
        # Validate SPU codes
        if not df["spu_code"].dtype in ['int64', 'object']:
            validation_results["warnings"].append("spu_code should be integer or string")
        
        # Validate quantities
        quantity_columns = ["current_quantity", "allocated_quantity", "quantity_change"]
        for col in quantity_columns:
            if col in df.columns:
                if not df[col].dtype in ['int64', 'float64']:
                    validation_results["warnings"].append(f"{col} should be numeric")
                else:
                    if (df[col] < 0).any():
                        validation_results["warnings"].append(f"Found negative {col} values")
        
        # Validate allocation weight
        if "allocation_weight" in df.columns:
            if not df["allocation_weight"].dtype in ['int64', 'float64']:
                validation_results["warnings"].append("allocation_weight should be numeric")
            else:
                if (df["allocation_weight"] < 0).any() or (df["allocation_weight"] > 1).any():
                    validation_results["warnings"].append("allocation_weight should be between 0 and 1")
        
        # Validate quantity change consistency
        if "current_quantity" in df.columns and "allocated_quantity" in df.columns and "quantity_change" in df.columns:
            calculated_change = df["allocated_quantity"] - df["current_quantity"]
            if not np.allclose(calculated_change, df["quantity_change"], rtol=1e-10):
                validation_results["warnings"].append("quantity_change does not match allocated_quantity - current_quantity")
        
        # Statistics
        validation_results["statistics"]["total_allocations"] = len(df)
        validation_results["statistics"]["unique_stores"] = df["str_code"].nunique()
        validation_results["statistics"]["unique_spus"] = df["spu_code"].nunique()
        validation_results["statistics"]["avg_allocation_weight"] = df["allocation_weight"].mean() if "allocation_weight" in df.columns else 0
        validation_results["statistics"]["total_quantity_change"] = df["quantity_change"].sum() if "quantity_change" in df.columns else 0
        
    except Exception as e:
        validation_results["validation_passed"] = False
        validation_results["errors"].append(f"Error reading CSV file: {e}")
    
    return validation_results

def validate_allocation_validation_json(file_path: str) -> Dict[str, Any]:
    """
    Validates the allocation validation JSON file specifically.
    """
    validation_results = {
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Check required structure
        required_keys = ["validation_metadata", "allocation_summary", "constraint_validation", "performance_metrics"]
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            validation_results["validation_passed"] = False
            validation_results["errors"].append(f"Missing required keys: {missing_keys}")
            return validation_results
        
        # Validate allocation summary
        summary = data.get("allocation_summary", {})
        if "total_allocations" in summary:
            if not isinstance(summary["total_allocations"], int) or summary["total_allocations"] < 0:
                validation_results["warnings"].append("total_allocations should be non-negative integer")
        
        if "total_stores" in summary:
            if not isinstance(summary["total_stores"], int) or summary["total_stores"] < 0:
                validation_results["warnings"].append("total_stores should be non-negative integer")
        
        # Validate constraint validation
        constraints = data.get("constraint_validation", {})
        if "capacity_constraints_satisfied" in constraints:
            if not isinstance(constraints["capacity_constraints_satisfied"], bool):
                validation_results["warnings"].append("capacity_constraints_satisfied should be boolean")
        
        if "weight_constraints_satisfied" in constraints:
            if not isinstance(constraints["weight_constraints_satisfied"], bool):
                validation_results["warnings"].append("weight_constraints_satisfied should be boolean")
        
        # Statistics
        validation_results["statistics"]["total_keys"] = len(data)
        validation_results["statistics"]["has_metadata"] = "validation_metadata" in data
        validation_results["statistics"]["has_summary"] = "allocation_summary" in data
        validation_results["statistics"]["has_constraints"] = "constraint_validation" in data
        validation_results["statistics"]["has_performance"] = "performance_metrics" in data
        
    except Exception as e:
        validation_results["validation_passed"] = False
        validation_results["errors"].append(f"Error reading JSON file: {e}")
    
    return validation_results

if __name__ == "__main__":
    print("Testing Step 32 Store Allocation Validator...")
    results = validate_step32_complete("output")
    print(f"Validation passed: {results['validation_passed']}")
    print(f"Files found: {results['statistics']['files_found']}/{results['statistics']['total_files_expected']}")
    if results['errors']:
        print(f"Errors: {results['errors']}")
    if results['warnings']:
        print(f"Warnings: {results['warnings']}")


