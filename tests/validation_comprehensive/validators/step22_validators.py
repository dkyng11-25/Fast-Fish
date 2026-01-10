#!/usr/bin/env python3
"""
Step 22: Store Attribute Enrichment Validators (WIP)

WIP validators for Step 22 (store attribute enrichment with real data).
Based on src/step22_store_attribute_enrichment.py docstring requirements.

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


def validate_step22_files(data_dir: str = "output") -> Dict[str, Any]:
    """Validate presence of Step 22 store attribute enrichment outputs (WIP)."""
    base = Path(data_dir)
    
    # Step 22 creates enriched store attributes with real data
    patterns = {
        "enriched_store_attributes": "enriched_store_attributes_*.csv",
        "store_classifications": "store_type_classifications_*.csv",
        "rack_capacity_analysis": "rack_capacity_analysis_*.csv",
        "temperature_zone_mapping": "temperature_zone_mapping_*.csv"
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
                        
                    # Check for expected store attribute columns
                    expected_cols = ["str_code", "store_type", "rack_capacity", "temperature_zone"]
                    present_cols = [c for c in expected_cols if c in df.columns]
                    if present_cols:
                        file_validation["expected_columns_found"] = present_cols
                        
            except Exception as e:
                out["errors"].append(f"Error reading {latest_file.name}: {str(e)}")
                out["validation_passed"] = False
        else:
            out["warnings"].append(f"Missing expected Step 22 output: {pattern}")
            
        out["files"][file_type] = file_validation

    return out


def validate_step22_complete(data_dir: str = "output") -> Dict[str, Any]:
    logger.info("Starting Step 22 WIP validation using data_dir=%s", data_dir)
    return validate_step22_files(data_dir)


__all__ = [
    'validate_step22_files',
    'validate_step22_complete'
]


