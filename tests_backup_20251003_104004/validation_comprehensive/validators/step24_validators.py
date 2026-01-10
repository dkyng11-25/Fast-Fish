#!/usr/bin/env python3
"""
Step 24: Comprehensive Cluster Labeling Validators

Comprehensive validators for Step 24 (Comprehensive Cluster Labeling System).
Based on src/step24_comprehensive_cluster_labeling.py docstring and actual output files.

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


def validate_step24_cluster_labels_csv(file_path: Path) -> Dict[str, Any]:
    """Validate comprehensive cluster labels CSV file."""
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
        required_cols = ["cluster_id", "cluster_name", "str_code", "store_group"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            validation["validation_passed"] = False
            validation["errors"].append(f"Missing required columns: {missing_cols}")
        
        # Validate cluster IDs
        if "cluster_id" in df.columns:
            if not pd.api.types.is_numeric_dtype(df["cluster_id"]):
                validation["warnings"].append("cluster_id should be numeric")
            if (df["cluster_id"] < 0).any():
                validation["warnings"].append("Found negative cluster_id values")
            validation["unique_clusters"] = df["cluster_id"].nunique()
        
        # Validate store codes
        if "str_code" in df.columns:
            if not pd.api.types.is_numeric_dtype(df["str_code"]):
                validation["warnings"].append("str_code should be numeric")
            validation["unique_stores"] = df["str_code"].nunique()
        
        # Check for labeling quality metrics
        quality_cols = ["labeling_confidence", "cluster_density", "cluster_cohesion"]
        found_quality_cols = [col for col in quality_cols if col in df.columns]
        validation["quality_metrics_found"] = found_quality_cols
        
        if "labeling_confidence" in df.columns:
            confidence = df["labeling_confidence"].dropna()
            if len(confidence) > 0:
                if (confidence < 0).any() or (confidence > 1).any():
                    validation["warnings"].append("labeling_confidence should be between 0-1")
                validation["avg_confidence"] = float(confidence.mean())
        
        # Check for demographic labels
        demo_cols = ["primary_demographic", "income_level", "age_group"]
        found_demo_cols = [col for col in demo_cols if col in df.columns]
        validation["demographic_labels_found"] = found_demo_cols
        
        # Check for performance labels
        perf_cols = ["performance_tier", "sales_volume_tier", "growth_potential"]
        found_perf_cols = [col for col in perf_cols if col in df.columns]
        validation["performance_labels_found"] = found_perf_cols
        
    except Exception as e:
        validation["validation_passed"] = False
        validation["errors"].append(f"Error reading CSV: {str(e)}")
    
    return validation


def validate_step24_analysis_report(file_path: Path) -> Dict[str, Any]:
    """Validate cluster label analysis report markdown file."""
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
        expected_sections = ["# Cluster Label Analysis", "## Summary", "## Cluster Characteristics"]
        found_sections = [section for section in expected_sections if section in content]
        
        if len(found_sections) < 2:
            validation["warnings"].append(f"Missing expected sections. Found: {found_sections}")
        
        # Check for key metrics
        key_metrics = ["Total Clusters", "Labeling Accuracy", "Cluster Distribution"]
        found_metrics = [metric for metric in key_metrics if metric in content]
        
        if len(found_metrics) < 2:
            validation["warnings"].append(f"Missing key metrics. Found: {found_metrics}")
        
        validation["content_length"] = len(content)
        validation["sections_found"] = found_sections
        
    except Exception as e:
        validation["validation_passed"] = False
        validation["errors"].append(f"Error reading markdown file: {str(e)}")
    
    return validation


def validate_step24_summary_json(file_path: Path) -> Dict[str, Any]:
    """Validate cluster labeling summary JSON file."""
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
        expected_keys = ["total_clusters", "labeling_accuracy", "cluster_distribution"]
        found_keys = [key for key in expected_keys if key in data]
        
        if len(found_keys) < 2:
            validation["warnings"].append(f"Missing expected keys. Found: {found_keys}")
        
        validation["json_keys"] = list(data.keys())
        validation["total_clusters"] = data.get("total_clusters", 0)
        validation["labeling_accuracy"] = data.get("labeling_accuracy", 0.0)
        
    except json.JSONDecodeError as e:
        validation["validation_passed"] = False
        validation["errors"].append(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        validation["validation_passed"] = False
        validation["errors"].append(f"Error reading JSON file: {str(e)}")
    
    return validation


def validate_step24_comprehensive(data_dir: str = "output") -> Dict[str, Any]:
    """Comprehensive validation for Step 24 outputs."""
    logger.info("Starting Step 24 comprehensive validation using data_dir=%s", data_dir)
    
    base_dir = Path(data_dir)
    validation_results = {
        "validation_passed": False,  # Requires real data validation
        "step": 24,
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
        "cluster_labels": "comprehensive_cluster_labels_*.csv",
        "analysis_report": "cluster_label_analysis_report_*.md",
        "summary_json": "cluster_labeling_summary_*.json"
    }
    
    for file_type, pattern in file_patterns.items():
        full_pattern = str(base_dir / pattern)
        candidate_files = sorted(glob.glob(full_pattern), key=os.path.getctime, reverse=True)
        
        validation_results["statistics"]["total_files_checked"] += 1
        
        if candidate_files:
            latest_file = Path(candidate_files[0])
            
            # Validate based on file type
            if file_type == "cluster_labels":
                file_validation = validate_step24_cluster_labels_csv(latest_file)
            elif file_type == "analysis_report":
                file_validation = validate_step24_analysis_report(latest_file)
            elif file_type == "summary_json":
                file_validation = validate_step24_summary_json(latest_file)
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
            if file_type == "cluster_labels":
                if "unique_clusters" in file_validation:
                    validation_results["statistics"]["total_clusters"] = file_validation["unique_clusters"]
                if "unique_stores" in file_validation:
                    validation_results["statistics"]["total_stores"] = file_validation["unique_stores"]
                if "avg_confidence" in file_validation:
                    validation_results["statistics"]["avg_labeling_confidence"] = file_validation["avg_confidence"]
        else:
            validation_results["validation_passed"] = False
            validation_results["errors"].append(f"Missing expected {file_type} file: {pattern}")
            validation_results["statistics"]["files_failed"] += 1
    
    # Overall validation summary
    if validation_results["statistics"]["files_failed"] == 0:
        validation_results["warnings"].append("All Step 24 files validated successfully")
    else:
        validation_results["errors"].append(f"Step 24 validation failed: {validation_results['statistics']['files_failed']} files failed")
    
    return validation_results


def validate_step24_complete(data_dir: str = "output") -> Dict[str, Any]:
    """Main validation function for Step 24."""
    return validate_step24_comprehensive(data_dir)


__all__ = [
    'validate_step24_cluster_labels_csv',
    'validate_step24_analysis_report',
    'validate_step24_summary_json',
    'validate_step24_comprehensive',
    'validate_step24_complete'
]


