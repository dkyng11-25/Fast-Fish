#!/usr/bin/env python3
"""
Step 36 Unified Delivery Builder Validators

This module contains validators for unified delivery builder validation from Step 36.

Author: Data Pipeline
Date: 2025-01-16
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import json

logger = logging.getLogger(__name__)

def validate_step36_complete(
    output_base_dir: str = "tests/test_output"
) -> Dict[str, Any]:
    """
    Validates the outputs of Step 36: Unified Delivery Builder.
    Checks for unified delivery CSV, Excel, validation JSON, and additional files.
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
        "unified_delivery_csv": f"{output_dir}/unified_delivery_*.csv",
        "unified_delivery_xlsx": f"{output_dir}/unified_delivery_*.xlsx",
        "unified_delivery_validation": f"{output_dir}/unified_delivery_*_validation.json",
        "top_adds": f"{output_dir}/unified_delivery_*_top_adds.csv",
        "top_reduces": f"{output_dir}/unified_delivery_*_top_reduces.csv",
        "cluster_level": f"{output_dir}/unified_delivery_cluster_level_*.csv"
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
                            if file_type == "unified_delivery_csv":
                                expected_cols = ["str_code", "spu_code", "recommended_quantity", "current_quantity", "quantity_change", "allocation_weight"]
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
                                
                                # Validate SPU codes
                                if "spu_code" in df.columns:
                                    if not df["spu_code"].dtype in ['int64', 'object']:
                                        validation_results["warnings"].append("spu_code should be integer or string")
                                
                                # Validate quantities
                                quantity_columns = ["recommended_quantity", "current_quantity", "quantity_change"]
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
                                
                                file_validation["total_allocations"] = len(df)
                                file_validation["unique_stores"] = df["str_code"].nunique() if "str_code" in df.columns else 0
                                file_validation["unique_spus"] = df["spu_code"].nunique() if "spu_code" in df.columns else 0
                                
                    except Exception as e:
                        validation_results["validation_passed"] = False
                        validation_results["errors"].append(f"Error reading CSV {file_path.name}: {e}")
                        
            validation_results["files"][file_type] = file_validation
        else:
            validation_results["validation_passed"] = False
            validation_results["warnings"].append(f"Missing expected Step 36 output: {pattern}")

    # Calculate statistics
    validation_results["statistics"]["files_found"] = sum(1 for f in validation_results["files"].values() if f["exists"])
    validation_results["statistics"]["total_files_expected"] = len(expected_patterns)
    validation_results["statistics"]["validation_timestamp"] = datetime.now().isoformat()
    
    return validation_results

if __name__ == "__main__":
    print("Testing Step 36 Unified Delivery Builder Validator...")
    results = validate_step36_complete("output")
    print(f"Validation passed: {results['validation_passed']}")
    print(f"Files found: {results['statistics']['files_found']}/{results['statistics']['total_files_expected']}")
    if results['errors']:
        print(f"Errors: {results['errors']}")
    if results['warnings']:
        print(f"Warnings: {results['warnings']}")