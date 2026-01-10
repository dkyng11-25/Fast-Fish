#!/usr/bin/env python3
"""
Step 25: Product Role Classifier Validators

Comprehensive validators for Step 25 (Product Role Classifier).
Based on src/step25_product_role_classifier.py docstring and actual output files.

Author: Data Pipeline
Date: 2025-09-17
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
import os
import glob
from datetime import datetime
import json

logger = logging.getLogger(__name__)


def validate_step25_product_roles_csv(file_path: Path) -> Dict[str, Any]:
    """Validate product role classifications CSV file."""
    validation = {
        "file_exists": file_path.exists(),
        "file_size_bytes": 0,
        "rows": 0,
        "columns": [],
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": []
    }
    
    if not validation["file_exists"]:
        validation["validation_passed"] = False
        validation["errors"].append(f"File not found: {file_path}")
        return validation
    
    try:
        df = pd.read_csv(file_path)
        validation["file_size_bytes"] = file_path.stat().st_size
        validation["rows"] = len(df)
        validation["columns"] = list(df.columns)
        
        if df.empty:
            validation["validation_passed"] = False
            validation["errors"].append("CSV file is empty")
            return validation
        
        # Check required columns
        required_cols = ["spu_code", "product_role", "cluster_id"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            validation["validation_passed"] = False
            validation["errors"].append(f"Missing required columns: {missing_cols}")
        
        # Validate product roles
        if "product_role" in df.columns:
            valid_roles = ["CORE", "SEASONAL", "FILLER", "CLEARANCE"]
            invalid_roles = df[~df["product_role"].isin(valid_roles)]["product_role"].unique()
            if len(invalid_roles) > 0:
                validation["warnings"].append(f"Found invalid product roles: {invalid_roles}")
            
            # Count role distribution
            role_counts = df["product_role"].value_counts()
            validation["role_distribution"] = role_counts.to_dict()
            validation["unique_roles"] = len(role_counts)
        
        # Validate SPU codes
        if "spu_code" in df.columns:
            validation["unique_spus"] = df["spu_code"].nunique()
            if df["spu_code"].isnull().any():
                validation["warnings"].append("Found null values in spu_code")
        
        # Validate cluster IDs
        if "cluster_id" in df.columns:
            if not pd.api.types.is_numeric_dtype(df["cluster_id"]):
                validation["warnings"].append("cluster_id should be numeric")
            validation["unique_clusters"] = df["cluster_id"].nunique()
        
        # Check for performance metrics
        perf_cols = ["total_sales", "avg_daily_sales", "sales_velocity", "sell_through_rate"]
        found_perf_cols = [col for col in perf_cols if col in df.columns]
        validation["performance_metrics_found"] = found_perf_cols
        
        if "total_sales" in df.columns:
            sales = df["total_sales"].dropna()
            if len(sales) > 0:
                if (sales < 0).any():
                    validation["warnings"].append("Found negative sales values")
                validation["avg_total_sales"] = float(sales.mean())
                validation["max_total_sales"] = float(sales.max())
        
        # Check for confidence scores
        if "confidence_score" in df.columns:
            confidence = df["confidence_score"].dropna()
            if len(confidence) > 0:
                if (confidence < 0).any() or (confidence > 1).any():
                    validation["warnings"].append("confidence_score should be between 0-1")
                validation["avg_confidence"] = float(confidence.mean())
        
    except Exception as e:
        validation["validation_passed"] = False
        validation["errors"].append(f"Error reading CSV: {str(e)}")
    
    return validation


def validate_step25_analysis_report(file_path: Path) -> Dict[str, Any]:
    """Validate product role analysis report markdown file."""
    validation = {
        "file_exists": file_path.exists(),
        "file_size_bytes": 0,
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": []
    }
    
    if not validation["file_exists"]:
        validation["validation_passed"] = False
        validation["errors"].append(f"File not found: {file_path}")
        return validation
    
    try:
        validation["file_size_bytes"] = file_path.stat().st_size
        
        if validation["file_size_bytes"] == 0:
            validation["validation_passed"] = False
            validation["errors"].append("Markdown file is empty")
            return validation
        
        # Read and validate markdown content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for expected sections
        expected_sections = ["# Product Role Analysis", "## Role Distribution", "## Performance Analysis"]
        found_sections = [section for section in expected_sections if section in content]
        
        if len(found_sections) < 2:
            validation["warnings"].append(f"Missing expected sections. Found: {found_sections}")
        
        # Check for role mentions
        role_mentions = ["CORE", "SEASONAL", "FILLER", "CLEARANCE"]
        found_roles = [role for role in role_mentions if role in content]
        
        if len(found_roles) < 2:
            validation["warnings"].append(f"Missing role mentions. Found: {found_roles}")
        
        validation["content_length"] = len(content)
        validation["sections_found"] = found_sections
        validation["roles_mentioned"] = found_roles
        
    except Exception as e:
        validation["validation_passed"] = False
        validation["errors"].append(f"Error reading markdown file: {str(e)}")
    
    return validation


def validate_step25_summary_json(file_path: Path) -> Dict[str, Any]:
    """Validate product role summary JSON file."""
    validation = {
        "file_exists": file_path.exists(),
        "file_size_bytes": 0,
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": []
    }
    
    if not validation["file_exists"]:
        validation["validation_passed"] = False
        validation["errors"].append(f"File not found: {file_path}")
        return validation
    
    try:
        validation["file_size_bytes"] = file_path.stat().st_size
        
        if validation["file_size_bytes"] == 0:
            validation["validation_passed"] = False
            validation["errors"].append("JSON file is empty")
            return validation
        
        # Read and validate JSON content
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check for expected keys
        expected_keys = ["total_products", "role_distribution", "classification_accuracy"]
        found_keys = [key for key in expected_keys if key in data]
        
        if len(found_keys) < 2:
            validation["warnings"].append(f"Missing expected keys. Found: {found_keys}")
        
        validation["json_keys"] = list(data.keys())
        validation["total_products"] = data.get("total_products", 0)
        validation["role_distribution"] = data.get("role_distribution", {})
        
    except json.JSONDecodeError as e:
        validation["validation_passed"] = False
        validation["errors"].append(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        validation["validation_passed"] = False
        validation["errors"].append(f"Error reading JSON file: {str(e)}")
    
    return validation


def validate_step25_comprehensive(data_dir: str = "output") -> Dict[str, Any]:
    """Comprehensive validation for Step 25 outputs."""
    logger.info("Starting Step 25 comprehensive validation using data_dir=%s", data_dir)
    
    base_dir = Path(data_dir)
    validation_results = {
        "validation_passed": False,  # Requires real data validation
        "step": 25,
        "files": {},
        "errors": [],
        "warnings": [],
        "statistics": {
            "validation_timestamp": datetime.now().isoformat(),
            "total_files_checked": 0,
            "files_passed": 0,
            "files_failed": 0
        }
    }
    
    # Expected files and their patterns
    file_patterns = {
        "product_roles": "product_role_classifications.csv",
        "analysis_report": "product_role_analysis_report.md",
        "summary_json": "product_role_summary.json"
    }
    
    for file_type, pattern in file_patterns.items():
        full_pattern = str(base_dir / pattern)
        candidate_files = sorted(glob.glob(full_pattern), key=os.path.getctime, reverse=True)
        
        validation_results["statistics"]["total_files_checked"] += 1
        
        if candidate_files:
            latest_file = Path(candidate_files[0])
            
            # Validate based on file type
            if file_type == "product_roles":
                file_validation = validate_step25_product_roles_csv(latest_file)
            elif file_type == "analysis_report":
                file_validation = validate_step25_analysis_report(latest_file)
            elif file_type == "summary_json":
                file_validation = validate_step25_summary_json(latest_file)
            else:
                file_validation = {"validation_passed": False, "errors": [f"Unknown file type: {file_type}"]}
            
            validation_results["files"][file_type] = file_validation
            
            if file_validation["validation_passed"]:
                validation_results["statistics"]["files_passed"] += 1
            else:
                validation_results["statistics"]["files_failed"] += 1
                validation_results["validation_passed"] = False
            
            # Collect errors and warnings
            validation_results["errors"].extend(file_validation.get("errors", []))
            validation_results["warnings"].extend(file_validation.get("warnings", []))
            
            # Add file-specific statistics
            if file_type == "product_roles":
                if "unique_spus" in file_validation:
                    validation_results["statistics"]["total_spus"] = file_validation["unique_spus"]
                if "unique_clusters" in file_validation:
                    validation_results["statistics"]["total_clusters"] = file_validation["unique_clusters"]
                if "role_distribution" in file_validation:
                    validation_results["statistics"]["role_distribution"] = file_validation["role_distribution"]
                if "avg_confidence" in file_validation:
                    validation_results["statistics"]["avg_confidence"] = file_validation["avg_confidence"]
        else:
            validation_results["validation_passed"] = False
            validation_results["errors"].append(f"Missing expected {file_type} file: {pattern}")
            validation_results["statistics"]["files_failed"] += 1
    
    # Overall validation summary
    if validation_results["statistics"]["files_failed"] == 0:
        validation_results["warnings"].append("All Step 25 files validated successfully")
    else:
        validation_results["errors"].append(f"Step 25 validation failed: {validation_results['statistics']['files_failed']} files failed")
    
    return validation_results


def validate_step25_complete(data_dir: str = "output") -> Dict[str, Any]:
    """Main validation function for Step 25."""
    return validate_step25_comprehensive(data_dir)


__all__ = [
    'validate_step25_product_roles_csv',
    'validate_step25_analysis_report',
    'validate_step25_summary_json',
    'validate_step25_comprehensive',
    'validate_step25_complete'
]


