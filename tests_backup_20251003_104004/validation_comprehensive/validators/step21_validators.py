#!/usr/bin/env python3
"""
Step 21: Label Tag Recommendations Validators

Comprehensive validators for Step 21 (D-F Label/Tag Recommendation Sheet).
Based on src/step21_label_tag_recommendations.py docstring and actual output files.

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


def validate_step21_excel_file(file_path: Path) -> Dict[str, Any]:
    """Validate D-F Label Tag Recommendation Excel file."""
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
            df = pd.read_excel(file_path)
            validation["rows"] = len(df)
            validation["columns"] = list(df.columns)
            
            if df.empty:
                validation["validation_passed"] = False
                validation["errors"].append("Excel file contains no data")
                return validation
            
            # Check for expected columns based on D-F requirements
            expected_cols = [
                "Cluster/Store", "Chinese_Tag", "English_Tag", "Target_Quantity", 
                "Rationale_Score", "Capacity_Constraint", "Lifecycle_Stage"
            ]
            found_cols = [col for col in expected_cols if col in df.columns]
            validation["expected_columns_found"] = found_cols
            
            if len(found_cols) < 5:  # At least 5 of 7 expected columns
                validation["warnings"].append(f"Missing expected D-F columns. Found: {found_cols}")
            
            # Validate bilingual tags
            if "Chinese_Tag" in df.columns and "English_Tag" in df.columns:
                chinese_tags = df["Chinese_Tag"].dropna()
                english_tags = df["English_Tag"].dropna()
                
                if len(chinese_tags) == 0:
                    validation["warnings"].append("No Chinese tags found")
                if len(english_tags) == 0:
                    validation["warnings"].append("No English tags found")
                
                validation["chinese_tag_count"] = len(chinese_tags)
                validation["english_tag_count"] = len(english_tags)
            
            # Validate target quantities
            if "Target_Quantity" in df.columns:
                quantities = df["Target_Quantity"].dropna()
                if len(quantities) > 0:
                    if not pd.api.types.is_numeric_dtype(quantities):
                        validation["warnings"].append("Target_Quantity should be numeric")
                    if (quantities < 0).any():
                        validation["warnings"].append("Found negative target quantities")
                    validation["avg_target_quantity"] = float(quantities.mean())
            
            # Validate rationale scores
            if "Rationale_Score" in df.columns:
                scores = df["Rationale_Score"].dropna()
                if len(scores) > 0:
                    if not pd.api.types.is_numeric_dtype(scores):
                        validation["warnings"].append("Rationale_Score should be numeric")
                    if (scores < 0).any() or (scores > 10).any():
                        validation["warnings"].append("Rationale_Score should be between 0-10")
                    validation["avg_rationale_score"] = float(scores.mean())
            
        except Exception as e:
            validation["validation_passed"] = False
            validation["errors"].append(f"Error reading Excel file: {str(e)}")
    
    except Exception as e:
        validation["validation_passed"] = False
        validation["errors"].append(f"Error accessing file: {str(e)}")
    
    return validation


def validate_step21_comprehensive(data_dir: str = "output") -> Dict[str, Any]:
    """Comprehensive validation for Step 21 outputs."""
    logger.info("Starting Step 21 comprehensive validation using data_dir=%s", data_dir)
    
    base_dir = Path(data_dir)
    validation_results = {
        "validation_passed": False,  # Requires real data validation
        "step": 21,
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
    
    # Look for D-F Label Tag Recommendation Excel files
    excel_pattern = str(base_dir / "D_F_Label_Tag_Recommendation_Sheet_*.xlsx")
    candidate_files = sorted(glob.glob(excel_pattern), key=os.path.getctime, reverse=True)
    
    validation_results["statistics"]["total_files_checked"] += 1
    
    if candidate_files:
        latest_file = Path(candidate_files[0])
        file_validation = validate_step21_excel_file(latest_file)
        
        validation_results["files"]["excel"] = file_validation
        
        if file_validation["validation_passed"]:
            validation_results["statistics"]["files_passed"] += 1
        else:
            validation_results["statistics"]["files_failed"] += 1
            validation_results["validation_passed"] = False
        
        # Collect errors and warnings
        validation_results["errors"].extend(file_validation.get("errors", []))
        validation_results["warnings"].extend(file_validation.get("warnings", []))
        
        # Add file statistics
        if "rows" in file_validation:
            validation_results["statistics"]["total_recommendations"] = file_validation["rows"]
        if "chinese_tag_count" in file_validation:
            validation_results["statistics"]["chinese_tags"] = file_validation["chinese_tag_count"]
        if "english_tag_count" in file_validation:
            validation_results["statistics"]["english_tags"] = file_validation["english_tag_count"]
        if "avg_target_quantity" in file_validation:
            validation_results["statistics"]["avg_target_quantity"] = file_validation["avg_target_quantity"]
        if "avg_rationale_score" in file_validation:
            validation_results["statistics"]["avg_rationale_score"] = file_validation["avg_rationale_score"]
    else:
        validation_results["validation_passed"] = False
        validation_results["errors"].append(f"Missing expected Step 21 output: D_F_Label_Tag_Recommendation_Sheet_*.xlsx")
        validation_results["statistics"]["files_failed"] += 1
    
    # Overall validation summary
    if validation_results["statistics"]["files_failed"] == 0:
        validation_results["warnings"].append("All Step 21 files validated successfully")
    else:
        validation_results["errors"].append(f"Step 21 validation failed: {validation_results['statistics']['files_failed']} files failed")
    
    return validation_results


def validate_step21_complete(data_dir: str = "output") -> Dict[str, Any]:
    """Main validation function for Step 21."""
    return validate_step21_comprehensive(data_dir)


__all__ = [
    'validate_step21_excel_file',
    'validate_step21_comprehensive',
    'validate_step21_complete'
]


