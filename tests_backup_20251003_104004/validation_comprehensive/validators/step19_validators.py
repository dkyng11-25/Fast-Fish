#!/usr/bin/env python3
"""
Step 19: Detailed SPU Breakdown Validators (WIP)

WIP validators for Step 19. Checks presence and basic integrity of the detailed
SPU breakdown files written by Step 19.

Author: Data Pipeline
Date: 2025-09-17
"""

import glob
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def validate_step19_files(data_dir: str = "output") -> Dict[str, Any]:
    base = Path(data_dir)
    
    # Step 19 creates multiple files with period_label pattern
    patterns = {
        "detailed_spu_recommendations": "detailed_spu_recommendations_*_*.csv",
        "store_level_aggregation": "store_level_aggregation_*_*.csv", 
        "cluster_subcategory_aggregation": "cluster_subcategory_aggregation_*_*.csv",
        "spu_breakdown_summary": "spu_breakdown_summary_*_*.md"
    }
    
    out: Dict[str, Any] = {
        "validation_passed": False,  # Requires real data validation
        "files": {},
        "errors": [],
        "warnings": [],
        "statistics": {"validation_timestamp": datetime.now().isoformat()}
    }

    for file_type, pattern in patterns.items():
        full_pattern = str(base / pattern)
        matches = sorted(glob.glob(full_pattern), key=lambda p: Path(p).stat().st_mtime, reverse=True)
        
        file_validation = {
            "exists": len(matches) > 0,
            "count": len(matches),
            "latest": matches[0] if matches else None
        }
        
        if matches:
            latest_file = Path(matches[0])
            try:
                file_validation["size_bytes"] = latest_file.stat().st_size
                file_validation["size_mb"] = round(file_validation["size_bytes"] / (1024 * 1024), 3)
                
                # For CSV files, check basic structure
                if latest_file.suffix == '.csv':
                    df = pd.read_csv(latest_file)
                    file_validation["rows"] = int(len(df))
                    file_validation["columns"] = list(df.columns)
                    if df.empty:
                        out["warnings"].append(f"Empty CSV file: {latest_file.name}")
                        out["validation_passed"] = False
                elif latest_file.suffix == '.md':
                    # For markdown files, just check size
                    if file_validation["size_bytes"] == 0:
                        out["warnings"].append(f"Empty markdown file: {latest_file.name}")
                        out["validation_passed"] = False
                        
            except Exception as e:
                out["errors"].append(f"Error reading {latest_file.name}: {str(e)}")
                out["validation_passed"] = False
        else:
            out["warnings"].append(f"Missing expected Step 19 output: {pattern}")
            
        out["files"][file_type] = file_validation

    # Enhanced validation for detailed SPU recommendations
    detailed_file = out["files"].get("detailed_spu_recommendations", {}).get("latest")
    if detailed_file and Path(detailed_file).exists():
        try:
            df = pd.read_csv(detailed_file)
            expected_cols = [
                "str_code", "spu_code", "recommended_quantity_change", 
                "investment_required", "rule_source"
            ]
            present_cols = [c for c in expected_cols if c in df.columns]
            out["statistics"]["expected_columns_found"] = present_cols
            
            if len(present_cols) == 0:
                out["warnings"].append("No expected SPU breakdown columns found; verify schema")
            else:
                # Validate data quality
                if "recommended_quantity_change" in df.columns:
                    if not df["recommended_quantity_change"].dtype in ['int64', 'float64']:
                        out["warnings"].append("recommended_quantity_change should be numeric")
                    if (df["recommended_quantity_change"] < 0).any():
                        out["warnings"].append("Found negative recommended_quantity_change values")
                
                if "investment_required" in df.columns:
                    if not df["investment_required"].dtype in ['int64', 'float64']:
                        out["warnings"].append("investment_required should be numeric")
                    if (df["investment_required"] < 0).any():
                        out["warnings"].append("Found negative investment_required values")
                
                # Check for null values in critical columns
                critical_cols = ["str_code", "spu_code"]
                for col in critical_cols:
                    if col in df.columns and df[col].isnull().any():
                        out["warnings"].append(f"Found null values in critical column: {col}")
                
                out["statistics"]["total_recommendations"] = len(df)
                out["statistics"]["unique_stores"] = df["str_code"].nunique() if "str_code" in df.columns else 0
                out["statistics"]["unique_spus"] = df["spu_code"].nunique() if "spu_code" in df.columns else 0
                
        except Exception as e:
            out["warnings"].append(f"Could not validate detailed SPU columns: {str(e)}")

    # Enhanced validation for store level aggregation
    store_file = out["files"].get("store_level_aggregation", {}).get("latest")
    if store_file and Path(store_file).exists():
        try:
            df = pd.read_csv(store_file)
            required_cols = ["str_code", "total_spus", "total_current_quantity", "total_recommended_quantity"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                out["warnings"].append(f"Missing required columns in store aggregation: {missing_cols}")
            else:
                out["statistics"]["total_stores"] = len(df)
                out["statistics"]["total_store_spus"] = df["total_spus"].sum() if "total_spus" in df.columns else 0
        except Exception as e:
            out["warnings"].append(f"Could not validate store aggregation: {str(e)}")

    # Enhanced validation for cluster aggregation
    cluster_file = out["files"].get("cluster_subcategory_aggregation", {}).get("latest")
    if cluster_file and Path(cluster_file).exists():
        try:
            df = pd.read_csv(cluster_file)
            required_cols = ["cluster_id", "subcategory", "total_stores", "total_current_quantity"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                out["warnings"].append(f"Missing required columns in cluster aggregation: {missing_cols}")
            else:
                out["statistics"]["total_clusters"] = df["cluster_id"].nunique() if "cluster_id" in df.columns else 0
                out["statistics"]["total_subcategories"] = df["subcategory"].nunique() if "subcategory" in df.columns else 0
        except Exception as e:
            out["warnings"].append(f"Could not validate cluster aggregation: {str(e)}")

    return out


def validate_step19_complete(data_dir: str = "output") -> Dict[str, Any]:
    logger.info("Starting Step 19 WIP validation using data_dir=%s", data_dir)
    return validate_step19_files(data_dir)


__all__ = [
    'validate_step19_files',
    'validate_step19_complete'
]
