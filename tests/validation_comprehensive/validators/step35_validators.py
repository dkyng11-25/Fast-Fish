#!/usr/bin/env python3
"""
Step 35 Merchandising Strategy Deployment Validators

This module contains validators for merchandising strategy deployment validation from Step 35.

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

def validate_step35_complete(
    output_base_dir: str = "tests/test_output"
) -> Dict[str, Any]:
    """
    Validates the outputs of Step 35: Merchandising Strategy Deployment.
    Checks for merchandising recommendations CSV, summary report, and additional files.
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
        "merchandising_recommendations": f"{output_dir}/store_level_merchandising_recommendations_*.csv",
        "merchandising_summary": f"{output_dir}/store_level_merchandising_summary_*.md",
        "cluster_summary": f"{output_dir}/store_level_merchandising_cluster_summary_*.csv",
        "by_cluster_json": f"{output_dir}/store_level_merchandising_by_cluster_*.json",
        "schema_json": f"{output_dir}/store_level_merchandising_recommendations_*_schema.json",
        "qa_validation": f"{output_dir}/store_level_merchandising_recommendations_*_qavalidation.json"
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
                            if file_type == "merchandising_recommendations":
                                expected_cols = ["str_code", "store_name", "cluster_id", "merchandising_strategy", "recommendations", "priority_score"]
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
                                    if not df["cluster_id"].dtype in ['int64', 'object']:
                                        validation_results["warnings"].append("cluster_id should be integer or string")
                                    else:
                                        if df["cluster_id"].dtype == 'int64':
                                            if (df["cluster_id"] < 0).any() or (df["cluster_id"] > 50).any():
                                                validation_results["warnings"].append("cluster_id should be between 0 and 50")
                                
                                # Validate priority score
                                if "priority_score" in df.columns:
                                    if not df["priority_score"].dtype in ['int64', 'float64']:
                                        validation_results["warnings"].append("priority_score should be numeric")
                                    else:
                                        if (df["priority_score"] < 0).any() or (df["priority_score"] > 10).any():
                                            validation_results["warnings"].append("priority_score should be between 0 and 10")
                                
                                file_validation["total_stores"] = len(df)
                                file_validation["unique_stores"] = df["str_code"].nunique() if "str_code" in df.columns else 0
                                file_validation["unique_clusters"] = df["cluster_id"].nunique() if "cluster_id" in df.columns else 0
                                
                                # Analyze strategy distribution
                                if "merchandising_strategy" in df.columns:
                                    strategy_dist = df["merchandising_strategy"].value_counts().to_dict()
                                    file_validation["strategy_distribution"] = strategy_dist
                                
                            elif file_type == "cluster_summary":
                                expected_cols = ["cluster_id", "store_count", "avg_priority_score", "strategy_summary"]
                                missing_cols = [col for col in expected_cols if col not in df.columns]
                                if missing_cols:
                                    validation_results["warnings"].append(f"Missing expected columns in {file_type}: {missing_cols}")
                                
                                # Validate cluster summary data
                                if "store_count" in df.columns:
                                    if not df["store_count"].dtype in ['int64']:
                                        validation_results["warnings"].append("store_count should be integer")
                                    if (df["store_count"] < 0).any():
                                        validation_results["warnings"].append("Found negative store_count values")
                                
                                if "avg_priority_score" in df.columns:
                                    if not df["avg_priority_score"].dtype in ['int64', 'float64']:
                                        validation_results["warnings"].append("avg_priority_score should be numeric")
                                
                                file_validation["total_clusters"] = len(df)
                                file_validation["total_stores"] = df["store_count"].sum() if "store_count" in df.columns else 0
                                
                    except Exception as e:
                        validation_results["validation_passed"] = False
                        validation_results["errors"].append(f"Error reading CSV {file_path.name}: {e}")
                        
                elif file_path.suffix == '.json':
                    try:
                        with open(file_path, 'r') as f:
                            json_data = json.load(f)
                        
                        file_validation["json_keys"] = list(json_data.keys()) if isinstance(json_data, dict) else "Not a dict"
                        
                        # Validate specific JSON structure based on file type
                        if file_type == "by_cluster_json":
                            # Should be a nested structure with cluster data
                            if not isinstance(json_data, dict):
                                validation_results["warnings"].append("by_cluster_json should be a dictionary")
                            else:
                                file_validation["cluster_keys"] = list(json_data.keys())
                                file_validation["total_clusters_in_json"] = len(json_data)
                                
                        elif file_type == "schema_json":
                            # Should contain schema information
                            expected_schema_keys = ["columns", "data_types", "constraints"]
                            missing_schema_keys = [key for key in expected_schema_keys if key not in json_data]
                            if missing_schema_keys:
                                validation_results["warnings"].append(f"Missing expected schema keys: {missing_schema_keys}")
                            
                            if "columns" in json_data:
                                file_validation["schema_columns"] = len(json_data["columns"])
                                
                        elif file_type == "qa_validation":
                            # Should contain QA validation results
                            expected_qa_keys = ["validation_summary", "data_quality_metrics", "validation_timestamp"]
                            missing_qa_keys = [key for key in expected_qa_keys if key not in json_data]
                            if missing_qa_keys:
                                validation_results["warnings"].append(f"Missing expected QA keys: {missing_qa_keys}")
                            
                            if "validation_summary" in json_data:
                                file_validation["qa_passed"] = json_data["validation_summary"].get("passed", False)
                                file_validation["qa_errors"] = json_data["validation_summary"].get("error_count", 0)
                                file_validation["qa_warnings"] = json_data["validation_summary"].get("warning_count", 0)
                                
                    except Exception as e:
                        validation_results["validation_passed"] = False
                        validation_results["errors"].append(f"Error reading JSON {file_path.name}: {e}")
                        
                elif file_path.suffix == '.md':
                    content = file_path.read_text()
                    file_validation["content_length"] = len(content)
                    file_validation["content_preview"] = content[:200] + "..." if len(content) > 200 else content
                    
                    # Validate summary report content
                    if file_type == "merchandising_summary":
                        expected_sections = ["Store-Level Merchandising Recommendations", "Cluster Analysis", "Strategy Distribution", "Implementation Notes"]
                        missing_sections = [section for section in expected_sections if section not in content]
                        if missing_sections:
                            validation_results["warnings"].append(f"Missing expected sections in {file_type}: {missing_sections}")
                        
            validation_results["files"][file_type] = file_validation
        else:
            validation_results["validation_passed"] = False
            validation_results["warnings"].append(f"Missing expected Step 35 output: {pattern}")

    # Calculate statistics
    validation_results["statistics"]["files_found"] = sum(1 for f in validation_results["files"].values() if f["exists"])
    validation_results["statistics"]["total_files_expected"] = len(expected_patterns)
    validation_results["statistics"]["validation_timestamp"] = datetime.now().isoformat()
    
    return validation_results

def validate_merchandising_recommendations_csv(file_path: str) -> Dict[str, Any]:
    """
    Validates the store-level merchandising recommendations CSV file specifically.
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
        required_columns = ["str_code", "store_name", "cluster_id", "merchandising_strategy", "recommendations", "priority_score"]
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
        if not df["cluster_id"].dtype in ['int64', 'object']:
            validation_results["warnings"].append("cluster_id should be integer or string")
        else:
            if df["cluster_id"].dtype == 'int64':
                if (df["cluster_id"] < 0).any() or (df["cluster_id"] > 50).any():
                    validation_results["warnings"].append("cluster_id should be between 0 and 50")
        
        # Validate priority score
        if not df["priority_score"].dtype in ['int64', 'float64']:
            validation_results["warnings"].append("priority_score should be numeric")
        else:
            if (df["priority_score"] < 0).any() or (df["priority_score"] > 10).any():
                validation_results["warnings"].append("priority_score should be between 0 and 10")
        
        # Check for duplicate store codes
        if df["str_code"].duplicated().any():
            validation_results["warnings"].append("Found duplicate store codes in recommendations")
        
        # Check for missing store names
        if "store_name" in df.columns and df["store_name"].isnull().any():
            validation_results["warnings"].append("Found missing store names")
        
        # Check for missing recommendations
        if "recommendations" in df.columns and df["recommendations"].isnull().any():
            validation_results["warnings"].append("Found missing recommendations")
        
        # Statistics
        validation_results["statistics"]["total_stores"] = len(df)
        validation_results["statistics"]["unique_stores"] = df["str_code"].nunique()
        validation_results["statistics"]["unique_clusters"] = df["cluster_id"].nunique()
        validation_results["statistics"]["strategy_distribution"] = df["merchandising_strategy"].value_counts().to_dict() if "merchandising_strategy" in df.columns else {}
        validation_results["statistics"]["avg_priority_score"] = df["priority_score"].mean() if "priority_score" in df.columns else 0
        validation_results["statistics"]["stores_with_recommendations"] = df["recommendations"].notnull().sum() if "recommendations" in df.columns else 0
        
    except Exception as e:
        validation_results["validation_passed"] = False
        validation_results["errors"].append(f"Error reading CSV file: {e}")
    
    return validation_results

if __name__ == "__main__":
    print("Testing Step 35 Merchandising Strategy Deployment Validator...")
    results = validate_step35_complete("output")
    print(f"Validation passed: {results['validation_passed']}")
    print(f"Files found: {results['statistics']['files_found']}/{results['statistics']['total_files_expected']}")
    if results['errors']:
        print(f"Errors: {results['errors']}")
    if results['warnings']:
        print(f"Warnings: {results['warnings']}")


