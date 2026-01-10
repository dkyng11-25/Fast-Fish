#!/usr/bin/env python3
"""
Step 18: Sell-Through Rate Analysis Validators (WIP)

WIP validators for Step 18. Checks presence and basic integrity of the sell-through
analysis CSV written by Step 18.

Author: Data Pipeline
Date: 2025-09-17
"""

import glob
import pandas as pd
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


PATTERN = "fast_fish_with_sell_through_analysis_*_*.csv"


def validate_step18_files(data_dir: str = "output") -> Dict[str, Any]:
    base = Path(data_dir)
    pattern = str(base / PATTERN)
    matches = sorted(glob.glob(pattern), key=lambda p: Path(p).stat().st_mtime, reverse=True)

    out: Dict[str, Any] = {
        "validation_passed": False,  # Requires real data validation
        "files": {
            "csv": matches[0] if matches else None,
            "count": len(matches)
        },
        "errors": [],
        "warnings": [],
        "statistics": {"validation_timestamp": datetime.now().isoformat()}
    }

    if not matches:
        out["warnings"].append(f"No Step 18 CSV found matching {PATTERN}")
        return out

    csv_path = Path(matches[0])
    try:
        size_mb = round(csv_path.stat().st_size / (1024 * 1024), 3)
        out["statistics"]["csv_file_size_mb"] = size_mb
        df = pd.read_csv(csv_path)
        out["statistics"]["rows"] = int(len(df))
        out["statistics"]["columns"] = list(df.columns)
        if df.empty:
            out["errors"].append("Sell-through analysis CSV is empty")
            out["validation_passed"] = False
        # Spot-check expected sell-through columns (WIP, conservative)
        expected_any = [
            "SPU_Store_Days_Inventory", "SPU_Store_Days_Sales",
            "Sell_Through_Rate_Frac", "Sell_Through_Rate_Pct", "Sell_Through_Rate",
            "Historical_Avg_Daily_SPUs_Sold_Per_Store"
        ]
        present = [c for c in expected_any if c in df.columns]
        if len(present) == 0:
            out["warnings"].append("No expected sell-through columns spotted; verify schema as specs solidify")
        else:
            out["statistics"]["sell_through_columns_found"] = present
    except Exception as e:
        out["errors"].append(f"Failed to read/validate CSV: {str(e)}")
        out["validation_passed"] = False

    return out


def validate_step18_complete(data_dir: str = "output") -> Dict[str, Any]:
    logger.info("Starting Step 18 WIP validation using data_dir=%s", data_dir)
    return validate_step18_files(data_dir)


__all__ = [
    'validate_step18_files',
    'validate_step18_complete'
]


