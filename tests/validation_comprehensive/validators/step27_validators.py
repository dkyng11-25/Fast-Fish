#!/usr/bin/env python3
"""
Step 27: Gap Matrix Generator Validators

Comprehensive validators for Step 27 (Cluster × Role Gap Matrix Generator).
Based on src/step27_gap_matrix_generator.py docstring and actual output files.

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


def validate_step27_gap_matrix_excel(file_path: Path) -> Dict[str, Any]:
    """Validate gap matrix Excel file."""
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
            validation["errors"].append("Excel file is empty")
            return validation
        
        # Try to read Excel file
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            validation["sheet_names"] = excel_file.sheet_names
            validation["num_sheets"] = len(excel_file.sheet_names)
            
            # Check for expected sheets
            expected_sheets = ["Gap Matrix", "Summary", "Analysis"]
            found_sheets = [sheet for sheet in expected_sheets if sheet in excel_file.sheet_names]
            validation["expected_sheets_found"] = found_sheets
            
            if len(found_sheets) < 1:
                validation["warnings"].append("No expected gap matrix sheets found")
            
            # Read main gap matrix sheet
            if "Gap Matrix" in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name="Gap Matrix")
                validation["gap_matrix_rows"] = len(df)
                validation["gap_matrix_columns"] = list(df.columns)
                
                if df.empty:
                    validation["warnings"].append("Gap Matrix sheet is empty")
                else:
                    # Check for cluster and role columns
                    cluster_cols = [col for col in df.columns if "cluster" in col.lower()]
                    role_cols = [col for col in df.columns if "role" in col.lower()]
                    validation["cluster_columns"] = cluster_cols
                    validation["role_columns"] = role_cols
                    
                    if len(cluster_cols) == 0:
                        validation["warnings"].append("No cluster-related columns found")
                    if len(role_cols) == 0:
                        validation["warnings"].append("No role-related columns found")
            
            # Read summary sheet if available
            if "Summary" in excel_file.sheet_names:
                summary_df = pd.read_excel(file_path, sheet_name="Summary")
                validation["summary_rows"] = len(summary_df)
                validation["summary_columns"] = list(summary_df.columns)
            
        except Exception as e:
            validation["validation_passed"] = False
            validation["errors"].append(f"Error reading Excel file: {str(e)}")
    
    except Exception as e:
        validation["validation_passed"] = False
        validation["errors"].append(f"Error accessing file: {str(e)}")
    
    return validation


def validate_step27_gap_analysis_csv(file_path: Path) -> Dict[str, Any]:
    """Validate gap analysis detailed CSV file."""
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
        required_cols = ["cluster_id", "product_role", "gap_score"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            validation["validation_passed"] = False
            validation["errors"].append(f"Missing required columns: {missing_cols}")
        
        # Validate cluster IDs
        if "cluster_id" in df.columns:
            if not pd.api.types.is_numeric_dtype(df["cluster_id"]):
                validation["warnings"].append("cluster_id should be numeric")
            validation["unique_clusters"] = df["cluster_id"].nunique()
        
        # Validate product roles
        if "product_role" in df.columns:
            valid_roles = ["CORE", "SEASONAL", "FILLER", "CLEARANCE"]
            invalid_roles = df[~df["product_role"].isin(valid_roles)]["product_role"].unique()
            if len(invalid_roles) > 0:
                validation["warnings"].append(f"Found invalid product roles: {invalid_roles}")
            validation["unique_roles"] = df["product_role"].nunique()
        
        # Validate gap scores
        if "gap_score" in df.columns:
            gap_scores = df["gap_score"].dropna()
            if len(gap_scores) > 0:
                if not pd.api.types.is_numeric_dtype(gap_scores):
                    validation["warnings"].append("gap_score should be numeric")
                validation["avg_gap_score"] = float(gap_scores.mean())
                validation["min_gap_score"] = float(gap_scores.min())
                validation["max_gap_score"] = float(gap_scores.max())
        
        # Check for gap analysis metrics
        analysis_cols = ["gap_severity", "priority_level", "recommended_action"]
        found_analysis_cols = [col for col in analysis_cols if col in df.columns]
        validation["analysis_metrics_found"] = found_analysis_cols
        
    except Exception as e:
        validation["validation_passed"] = False
        validation["errors"].append(f"Error reading CSV: {str(e)}")
    
    return validation


def validate_step27_analysis_report(file_path: Path) -> Dict[str, Any]:
    """Validate gap matrix analysis report markdown file."""
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
        expected_sections = ["# Gap Matrix Analysis", "## Cluster Analysis", "## Role Gaps"]
        found_sections = [section for section in expected_sections if section in content]
        
        if len(found_sections) < 2:
            validation["warnings"].append(f"Missing expected sections. Found: {found_sections}")
        
        # Check for gap analysis keywords
        gap_keywords = ["gap", "cluster", "role", "matrix", "analysis"]
        found_keywords = [keyword for keyword in gap_keywords if keyword.lower() in content.lower()]
        
        if len(found_keywords) < 3:
            validation["warnings"].append(f"Missing gap analysis keywords. Found: {found_keywords}")
        
        validation["content_length"] = len(content)
        validation["sections_found"] = found_sections
        validation["keywords_found"] = found_keywords
        
    except Exception as e:
        validation["validation_passed"] = False
        validation["errors"].append(f"Error reading markdown file: {str(e)}")
    
    return validation


def validate_step27_summary_json(file_path: Path) -> Dict[str, Any]:
    """Validate gap matrix summary JSON file."""
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
        expected_keys = ["total_clusters", "total_roles", "gap_summary", "matrix_dimensions"]
        found_keys = [key for key in expected_keys if key in data]
        
        if len(found_keys) < 2:
            validation["warnings"].append(f"Missing expected keys. Found: {found_keys}")
        
        validation["json_keys"] = list(data.keys())
        validation["total_clusters"] = data.get("total_clusters", 0)
        validation["total_roles"] = data.get("total_roles", 0)
        
    except json.JSONDecodeError as e:
        validation["validation_passed"] = False
        validation["errors"].append(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        validation["validation_passed"] = False
        validation["errors"].append(f"Error reading JSON file: {str(e)}")
    
    return validation


def validate_step27_comprehensive(data_dir: str = "output") -> Dict[str, Any]:
    """Comprehensive validation for Step 27 outputs."""
    logger.info("Starting Step 27 comprehensive validation using data_dir=%s", data_dir)
    
    base_dir = Path(data_dir)
    validation_results = {
        "validation_passed": False,  # Requires real data validation
        "step": 27,
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
        "gap_matrix_excel": "gap_matrix.xlsx",
        "gap_analysis_csv": "gap_analysis_detailed.csv",
        "analysis_report": "gap_matrix_analysis_report.md",
        "summary_json": "gap_matrix_summary.json"
    }
    
    for file_type, pattern in file_patterns.items():
        full_pattern = str(base_dir / pattern)
        candidate_files = sorted(glob.glob(full_pattern), key=os.path.getctime, reverse=True)
        
        validation_results["statistics"]["total_files_checked"] += 1
        
        if candidate_files:
            latest_file = Path(candidate_files[0])
            
            # Validate based on file type
            if file_type == "gap_matrix_excel":
                file_validation = validate_step27_gap_matrix_excel(latest_file)
            elif file_type == "gap_analysis_csv":
                file_validation = validate_step27_gap_analysis_csv(latest_file)
            elif file_type == "analysis_report":
                file_validation = validate_step27_analysis_report(latest_file)
            elif file_type == "summary_json":
                file_validation = validate_step27_summary_json(latest_file)
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
            if file_type == "gap_analysis_csv":
                if "unique_clusters" in file_validation:
                    validation_results["statistics"]["total_clusters"] = file_validation["unique_clusters"]
                if "unique_roles" in file_validation:
                    validation_results["statistics"]["total_roles"] = file_validation["unique_roles"]
                if "avg_gap_score" in file_validation:
                    validation_results["statistics"]["avg_gap_score"] = file_validation["avg_gap_score"]
        else:
            validation_results["validation_passed"] = False
            validation_results["errors"].append(f"Missing expected {file_type} file: {pattern}")
            validation_results["statistics"]["files_failed"] += 1
    
    # Overall validation summary
    if validation_results["statistics"]["files_failed"] == 0:
        validation_results["warnings"].append("All Step 27 files validated successfully")
    else:
        validation_results["errors"].append(f"Step 27 validation failed: {validation_results['statistics']['files_failed']} files failed")
    
    return validation_results


def validate_step27_complete(data_dir: str = "output") -> Dict[str, Any]:
    """Main validation function for Step 27."""
    return validate_step27_comprehensive(data_dir)


__all__ = [
    'validate_step27_gap_matrix_excel',
    'validate_step27_gap_analysis_csv',
    'validate_step27_analysis_report',
    'validate_step27_summary_json',
    'validate_step27_comprehensive',
    'validate_step27_complete'
]


