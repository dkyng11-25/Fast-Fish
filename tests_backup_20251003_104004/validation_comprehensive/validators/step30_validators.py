#!/usr/bin/env python3
"""
Step 30 Sellthrough Optimization Engine Validators

This module contains validators for sellthrough optimization validation from Step 30.

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

def validate_step30_complete(
    output_base_dir: str = "tests/test_output"
) -> Dict[str, Any]:
    """
    Validates the outputs of Step 30: Sellthrough Optimization Engine.
    Checks for optimization results, allocation files, and reports.
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
        "optimization_results": f"{output_dir}/sellthrough_optimization_results_*.json",
        "optimal_allocation": f"{output_dir}/optimal_product_allocation_*.csv",
        "optimization_report": f"{output_dir}/sellthrough_optimization_report_*.md",
        "before_after_comparison": f"{output_dir}/before_after_optimization_comparison_*.csv"
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
                            if file_type == "optimal_allocation":
                                expected_cols = ["str_code", "spu_code", "optimal_quantity", "current_quantity", "allocation_change"]
                                missing_cols = [col for col in expected_cols if col not in df.columns]
                                if missing_cols:
                                    validation_results["warnings"].append(f"Missing expected columns in {file_type}: {missing_cols}")
                                
                                # Validate allocation data
                                if "optimal_quantity" in df.columns:
                                    if not df["optimal_quantity"].dtype in ['int64', 'float64']:
                                        validation_results["warnings"].append("optimal_quantity should be numeric")
                                    if (df["optimal_quantity"] < 0).any():
                                        validation_results["warnings"].append("Found negative optimal_quantity values")
                                
                                if "allocation_change" in df.columns:
                                    if not df["allocation_change"].dtype in ['int64', 'float64']:
                                        validation_results["warnings"].append("allocation_change should be numeric")
                                
                                file_validation["total_allocations"] = len(df)
                                file_validation["unique_stores"] = df["str_code"].nunique() if "str_code" in df.columns else 0
                                file_validation["unique_spus"] = df["spu_code"].nunique() if "spu_code" in df.columns else 0
                                
                            elif file_type == "before_after_comparison":
                                expected_cols = ["str_code", "spu_code", "before_quantity", "after_quantity", "improvement"]
                                missing_cols = [col for col in expected_cols if col not in df.columns]
                                if missing_cols:
                                    validation_results["warnings"].append(f"Missing expected columns in {file_type}: {missing_cols}")
                                
                                # Validate comparison data
                                if "improvement" in df.columns:
                                    if not df["improvement"].dtype in ['int64', 'float64']:
                                        validation_results["warnings"].append("improvement should be numeric")
                                
                                file_validation["total_comparisons"] = len(df)
                                file_validation["avg_improvement"] = df["improvement"].mean() if "improvement" in df.columns else 0
                                
                    except Exception as e:
                        validation_results["validation_passed"] = False
                        validation_results["errors"].append(f"Error reading CSV {file_path.name}: {e}")
                        
                elif file_path.suffix == '.json':
                    try:
                        with open(file_path, 'r') as f:
                            json_data = json.load(f)
                        
                        file_validation["json_keys"] = list(json_data.keys()) if isinstance(json_data, dict) else "Not a dict"
                        
                        # Validate optimization results structure
                        if file_type == "optimization_results":
                            expected_keys = ["optimization_metadata", "objective_function", "constraints", "results"]
                            missing_keys = [key for key in expected_keys if key not in json_data]
                            if missing_keys:
                                validation_results["warnings"].append(f"Missing expected keys in {file_type}: {missing_keys}")
                            
                            # Validate optimization metadata
                            if "optimization_metadata" in json_data:
                                metadata = json_data["optimization_metadata"]
                                if "total_iterations" in metadata:
                                    if not isinstance(metadata["total_iterations"], int):
                                        validation_results["warnings"].append("total_iterations should be integer")
                                if "convergence_status" in metadata:
                                    valid_statuses = ["converged", "max_iterations", "infeasible", "unbounded"]
                                    if metadata["convergence_status"] not in valid_statuses:
                                        validation_results["warnings"].append(f"Invalid convergence_status: {metadata['convergence_status']}")
                            
                            # Validate results
                            if "results" in json_data:
                                results = json_data["results"]
                                if "optimal_value" in results:
                                    if not isinstance(results["optimal_value"], (int, float)):
                                        validation_results["warnings"].append("optimal_value should be numeric")
                                if "total_allocations" in results:
                                    if not isinstance(results["total_allocations"], int):
                                        validation_results["warnings"].append("total_allocations should be integer")
                                
                    except Exception as e:
                        validation_results["validation_passed"] = False
                        validation_results["errors"].append(f"Error reading JSON {file_path.name}: {e}")
                        
                elif file_path.suffix == '.md':
                    content = file_path.read_text()
                    file_validation["content_length"] = len(content)
                    file_validation["content_preview"] = content[:200] + "..." if len(content) > 200 else content
                    
                    # Validate report content
                    if file_type == "optimization_report":
                        expected_sections = ["Optimization Results", "Allocation Summary", "Performance Metrics"]
                        missing_sections = [section for section in expected_sections if section not in content]
                        if missing_sections:
                            validation_results["warnings"].append(f"Missing expected sections in {file_type}: {missing_sections}")
                        
            validation_results["files"][file_type] = file_validation
        else:
            validation_results["validation_passed"] = False
            validation_results["warnings"].append(f"Missing expected Step 30 output: {pattern}")

    # Calculate statistics
    validation_results["statistics"]["files_found"] = sum(1 for f in validation_results["files"].values() if f["exists"])
    validation_results["statistics"]["total_files_expected"] = len(expected_patterns)
    validation_results["statistics"]["validation_timestamp"] = datetime.now().isoformat()
    
    return validation_results

def validate_optimization_results_json(file_path: str) -> Dict[str, Any]:
    """
    Validates the optimization results JSON file specifically.
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
        required_keys = ["optimization_metadata", "objective_function", "constraints", "results"]
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            validation_results["validation_passed"] = False
            validation_results["errors"].append(f"Missing required keys: {missing_keys}")
            return validation_results
        
        # Validate optimization metadata
        metadata = data.get("optimization_metadata", {})
        if "total_iterations" in metadata:
            if not isinstance(metadata["total_iterations"], int) or metadata["total_iterations"] < 0:
                validation_results["warnings"].append("total_iterations should be non-negative integer")
        
        if "convergence_status" in metadata:
            valid_statuses = ["converged", "max_iterations", "infeasible", "unbounded"]
            if metadata["convergence_status"] not in valid_statuses:
                validation_results["warnings"].append(f"Invalid convergence_status: {metadata['convergence_status']}")
        
        # Validate objective function
        obj_func = data.get("objective_function", {})
        if "weights" in obj_func:
            weights = obj_func["weights"]
            if not isinstance(weights, dict):
                validation_results["warnings"].append("objective_function.weights should be a dictionary")
            else:
                total_weight = sum(weights.values())
                if abs(total_weight - 1.0) > 0.01:  # Allow small floating point errors
                    validation_results["warnings"].append(f"Objective function weights should sum to 1.0, got {total_weight}")
        
        # Validate results
        results = data.get("results", {})
        if "optimal_value" in results:
            if not isinstance(results["optimal_value"], (int, float)):
                validation_results["warnings"].append("results.optimal_value should be numeric")
        
        if "total_allocations" in results:
            if not isinstance(results["total_allocations"], int) or results["total_allocations"] < 0:
                validation_results["warnings"].append("results.total_allocations should be non-negative integer")
        
        # Statistics
        validation_results["statistics"]["total_keys"] = len(data)
        validation_results["statistics"]["has_metadata"] = "optimization_metadata" in data
        validation_results["statistics"]["has_objective"] = "objective_function" in data
        validation_results["statistics"]["has_results"] = "results" in data
        
    except Exception as e:
        validation_results["validation_passed"] = False
        validation_results["errors"].append(f"Error reading JSON file: {e}")
    
    return validation_results

def validate_optimal_allocation_csv(file_path: str) -> Dict[str, Any]:
    """
    Validates the optimal allocation CSV file specifically.
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
        required_columns = ["str_code", "spu_code", "optimal_quantity", "current_quantity", "allocation_change"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            validation_results["validation_passed"] = False
            validation_results["errors"].append(f"Missing required columns: {missing_columns}")
            return validation_results
        
        # Validate data types
        if not df["str_code"].dtype in ['int64', 'object']:
            validation_results["warnings"].append("str_code should be integer or string")
        
        if not df["spu_code"].dtype in ['int64', 'object']:
            validation_results["warnings"].append("spu_code should be integer or string")
        
        # Validate optimal quantity
        if not df["optimal_quantity"].dtype in ['int64', 'float64']:
            validation_results["validation_passed"] = False
            validation_results["errors"].append("optimal_quantity should be numeric")
        else:
            if (df["optimal_quantity"] < 0).any():
                validation_results["validation_passed"] = False
                validation_results["errors"].append("Found negative optimal_quantity values")
        
        # Validate current quantity
        if not df["current_quantity"].dtype in ['int64', 'float64']:
            validation_results["warnings"].append("current_quantity should be numeric")
        else:
            if (df["current_quantity"] < 0).any():
                validation_results["warnings"].append("Found negative current_quantity values")
        
        # Validate allocation change
        if not df["allocation_change"].dtype in ['int64', 'float64']:
            validation_results["warnings"].append("allocation_change should be numeric")
        
        # Statistics
        validation_results["statistics"]["total_allocations"] = len(df)
        validation_results["statistics"]["unique_stores"] = df["str_code"].nunique()
        validation_results["statistics"]["unique_spus"] = df["spu_code"].nunique()
        validation_results["statistics"]["avg_optimal_quantity"] = df["optimal_quantity"].mean()
        validation_results["statistics"]["avg_allocation_change"] = df["allocation_change"].mean()
        
    except Exception as e:
        validation_results["validation_passed"] = False
        validation_results["errors"].append(f"Error reading CSV file: {e}")
    
    return validation_results

if __name__ == "__main__":
    print("Testing Step 30 Sellthrough Optimization Engine Validator...")
    results = validate_step30_complete("output")
    print(f"Validation passed: {results['validation_passed']}")
    print(f"Files found: {results['statistics']['files_found']}/{results['statistics']['total_files_expected']}")
    if results['errors']:
        print(f"Errors: {results['errors']}")
    if results['warnings']:
        print(f"Warnings: {results['warnings']}")


