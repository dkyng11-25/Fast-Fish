#!/usr/bin/env python3
"""
Step 34 Cluster Strategy Optimization Validators

This module contains validators for cluster strategy optimization validation from Step 34.

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

def validate_step34_complete(
    output_base_dir: str = "tests/test_output"
) -> Dict[str, Any]:
    """
    Validates the outputs of Step 34: Cluster-Level Merchandising Strategy Optimization.
    Checks for cluster strategies CSV file.
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
        "cluster_strategies": f"{output_dir}/cluster_level_merchandising_strategies_*.csv"
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
                            # Validate specific columns for cluster strategies
                            if file_type == "cluster_strategies":
                                expected_cols = ["cluster_id", "operational_tag", "style_tag", "capacity_tag", "geographic_tag", "fashion_allocation_ratio", "basic_allocation_ratio", "capacity_utilization_target", "priority_score", "implementation_notes"]
                                missing_cols = [col for col in expected_cols if col not in df.columns]
                                if missing_cols:
                                    validation_results["warnings"].append(f"Missing expected columns in {file_type}: {missing_cols}")
                                
                                # Validate cluster IDs
                                if "cluster_id" in df.columns:
                                    if not df["cluster_id"].dtype in ['int64', 'object']:
                                        validation_results["warnings"].append("cluster_id should be integer or string")
                                    else:
                                        if df["cluster_id"].dtype == 'int64':
                                            if (df["cluster_id"] < 0).any() or (df["cluster_id"] > 50).any():
                                                validation_results["warnings"].append("cluster_id should be between 0 and 50")
                                
                                # Validate allocation ratios
                                if "fashion_allocation_ratio" in df.columns:
                                    if not df["fashion_allocation_ratio"].dtype in ['int64', 'float64']:
                                        validation_results["warnings"].append("fashion_allocation_ratio should be numeric")
                                    else:
                                        if (df["fashion_allocation_ratio"] < 0).any() or (df["fashion_allocation_ratio"] > 1).any():
                                            validation_results["warnings"].append("fashion_allocation_ratio should be between 0 and 1")
                                
                                if "basic_allocation_ratio" in df.columns:
                                    if not df["basic_allocation_ratio"].dtype in ['int64', 'float64']:
                                        validation_results["warnings"].append("basic_allocation_ratio should be numeric")
                                    else:
                                        if (df["basic_allocation_ratio"] < 0).any() or (df["basic_allocation_ratio"] > 1).any():
                                            validation_results["warnings"].append("basic_allocation_ratio should be between 0 and 1")
                                
                                # Validate capacity utilization target
                                if "capacity_utilization_target" in df.columns:
                                    if not df["capacity_utilization_target"].dtype in ['int64', 'float64']:
                                        validation_results["warnings"].append("capacity_utilization_target should be numeric")
                                    else:
                                        if (df["capacity_utilization_target"] < 0).any() or (df["capacity_utilization_target"] > 1).any():
                                            validation_results["warnings"].append("capacity_utilization_target should be between 0 and 1")
                                
                                # Validate priority score
                                if "priority_score" in df.columns:
                                    if not df["priority_score"].dtype in ['int64', 'float64']:
                                        validation_results["warnings"].append("priority_score should be numeric")
                                    else:
                                        if (df["priority_score"] < 0).any() or (df["priority_score"] > 10).any():
                                            validation_results["warnings"].append("priority_score should be between 0 and 10")
                                
                                # Check ratio consistency
                                if "fashion_allocation_ratio" in df.columns and "basic_allocation_ratio" in df.columns:
                                    total_ratio = df["fashion_allocation_ratio"] + df["basic_allocation_ratio"]
                                    if not np.allclose(total_ratio, 1.0, rtol=1e-10):
                                        validation_results["warnings"].append("fashion_allocation_ratio + basic_allocation_ratio should sum to 1.0")
                                
                                file_validation["total_clusters"] = len(df)
                                file_validation["unique_clusters"] = df["cluster_id"].nunique() if "cluster_id" in df.columns else 0
                                
                                # Analyze strategy distribution
                                if "operational_tag" in df.columns:
                                    op_dist = df["operational_tag"].value_counts().to_dict()
                                    file_validation["operational_tag_distribution"] = op_dist
                                
                                if "style_tag" in df.columns:
                                    style_dist = df["style_tag"].value_counts().to_dict()
                                    file_validation["style_tag_distribution"] = style_dist
                                
                                if "capacity_tag" in df.columns:
                                    capacity_dist = df["capacity_tag"].value_counts().to_dict()
                                    file_validation["capacity_tag_distribution"] = capacity_dist
                                
                                # Calculate average ratios
                                if "fashion_allocation_ratio" in df.columns:
                                    file_validation["avg_fashion_ratio"] = df["fashion_allocation_ratio"].mean()
                                if "basic_allocation_ratio" in df.columns:
                                    file_validation["avg_basic_ratio"] = df["basic_allocation_ratio"].mean()
                                if "capacity_utilization_target" in df.columns:
                                    file_validation["avg_capacity_target"] = df["capacity_utilization_target"].mean()
                                if "priority_score" in df.columns:
                                    file_validation["avg_priority_score"] = df["priority_score"].mean()
                                
                    except Exception as e:
                        validation_results["validation_passed"] = False
                        validation_results["errors"].append(f"Error reading CSV {file_path.name}: {e}")
                        
            validation_results["files"][file_type] = file_validation
        else:
            validation_results["validation_passed"] = False
            validation_results["warnings"].append(f"Missing expected Step 34 output: {pattern}")

    # Calculate statistics
    validation_results["statistics"]["files_found"] = sum(1 for f in validation_results["files"].values() if f["exists"])
    validation_results["statistics"]["total_files_expected"] = len(expected_patterns)
    validation_results["statistics"]["validation_timestamp"] = datetime.now().isoformat()
    
    return validation_results

def validate_cluster_strategies_csv(file_path: str) -> Dict[str, Any]:
    """
    Validates the cluster strategies CSV file specifically.
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
        required_columns = ["cluster_id", "operational_tag", "style_tag", "capacity_tag", "geographic_tag", "fashion_allocation_ratio", "basic_allocation_ratio", "capacity_utilization_target", "priority_score", "implementation_notes"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            validation_results["validation_passed"] = False
            validation_results["errors"].append(f"Missing required columns: {missing_columns}")
            return validation_results
        
        # Validate cluster IDs
        if not df["cluster_id"].dtype in ['int64', 'object']:
            validation_results["warnings"].append("cluster_id should be integer or string")
        else:
            if df["cluster_id"].dtype == 'int64':
                if (df["cluster_id"] < 0).any() or (df["cluster_id"] > 50).any():
                    validation_results["warnings"].append("cluster_id should be between 0 and 50")
        
        # Validate allocation ratios
        ratio_columns = ["fashion_allocation_ratio", "basic_allocation_ratio"]
        for col in ratio_columns:
            if col in df.columns:
                if not df[col].dtype in ['int64', 'float64']:
                    validation_results["warnings"].append(f"{col} should be numeric")
                else:
                    if (df[col] < 0).any() or (df[col] > 1).any():
                        validation_results["warnings"].append(f"{col} should be between 0 and 1")
        
        # Validate capacity utilization target
        if "capacity_utilization_target" in df.columns:
            if not df["capacity_utilization_target"].dtype in ['int64', 'float64']:
                validation_results["warnings"].append("capacity_utilization_target should be numeric")
            else:
                if (df["capacity_utilization_target"] < 0).any() or (df["capacity_utilization_target"] > 1).any():
                    validation_results["warnings"].append("capacity_utilization_target should be between 0 and 1")
        
        # Validate priority score
        if "priority_score" in df.columns:
            if not df["priority_score"].dtype in ['int64', 'float64']:
                validation_results["warnings"].append("priority_score should be numeric")
            else:
                if (df["priority_score"] < 0).any() or (df["priority_score"] > 10).any():
                    validation_results["warnings"].append("priority_score should be between 0 and 10")
        
        # Check ratio consistency
        if "fashion_allocation_ratio" in df.columns and "basic_allocation_ratio" in df.columns:
            total_ratio = df["fashion_allocation_ratio"] + df["basic_allocation_ratio"]
            if not np.allclose(total_ratio, 1.0, rtol=1e-10):
                validation_results["warnings"].append("fashion_allocation_ratio + basic_allocation_ratio should sum to 1.0")
        
        # Check for duplicate cluster IDs
        if df["cluster_id"].duplicated().any():
            validation_results["warnings"].append("Found duplicate cluster IDs in strategies")
        
        # Statistics
        validation_results["statistics"]["total_clusters"] = len(df)
        validation_results["statistics"]["unique_clusters"] = df["cluster_id"].nunique()
        validation_results["statistics"]["operational_tag_distribution"] = df["operational_tag"].value_counts().to_dict() if "operational_tag" in df.columns else {}
        validation_results["statistics"]["style_tag_distribution"] = df["style_tag"].value_counts().to_dict() if "style_tag" in df.columns else {}
        validation_results["statistics"]["capacity_tag_distribution"] = df["capacity_tag"].value_counts().to_dict() if "capacity_tag" in df.columns else {}
        validation_results["statistics"]["avg_fashion_ratio"] = df["fashion_allocation_ratio"].mean() if "fashion_allocation_ratio" in df.columns else 0
        validation_results["statistics"]["avg_basic_ratio"] = df["basic_allocation_ratio"].mean() if "basic_allocation_ratio" in df.columns else 0
        validation_results["statistics"]["avg_capacity_target"] = df["capacity_utilization_target"].mean() if "capacity_utilization_target" in df.columns else 0
        validation_results["statistics"]["avg_priority_score"] = df["priority_score"].mean() if "priority_score" in df.columns else 0
        
    except Exception as e:
        validation_results["validation_passed"] = False
        validation_results["errors"].append(f"Error reading CSV file: {e}")
    
    return validation_results

if __name__ == "__main__":
    print("Testing Step 34 Cluster Strategy Optimization Validator...")
    results = validate_step34_complete("output")
    print(f"Validation passed: {results['validation_passed']}")
    print(f"Files found: {results['statistics']['files_found']}/{results['statistics']['total_files_expected']}")
    if results['errors']:
        print(f"Errors: {results['errors']}")
    if results['warnings']:
        print(f"Warnings: {results['warnings']}")
