#!/usr/bin/env python3
"""
Step 17: Augment Recommendations Validators (WIP)

WIP validators for Step 17. Checks presence and basic integrity of the augmented
CSV written by Step 17.

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


PATTERN = "fast_fish_with_historical_and_cluster_trending_analysis_*_*.csv"


def validate_step17_files(data_dir: str = "output") -> Dict[str, Any]:
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
        out["warnings"].append(f"No Step 17 CSV found matching {PATTERN}")
        return out

    csv_path = Path(matches[0])
    try:
        size_mb = round(csv_path.stat().st_size / (1024 * 1024), 3)
        out["statistics"]["csv_file_size_mb"] = size_mb
        df = pd.read_csv(csv_path)
        out["statistics"]["rows"] = int(len(df))
        out["statistics"]["columns"] = list(df.columns)
        if df.empty:
            out["errors"].append("Augmented CSV is empty")
            out["validation_passed"] = False
        # Spot-check expected columns (WIP, conservative)
        expected_any = [
            "str_code", "cluster_id", "spu_code",
            "historical_sales", "cluster_trending_score", "fast_fish_flag"
        ]
        present = [c for c in expected_any if c in df.columns]
        if len(present) == 0:
            out["warnings"].append("No expected columns spotted; verify schema as specs solidify")
    except Exception as e:
        out["errors"].append(f"Failed to read/validate CSV: {str(e)}")
        out["validation_passed"] = False

    return out


def validate_step17_complete(data_dir: str = "output") -> Dict[str, Any]:
    logger.info("Starting Step 17 WIP validation using data_dir=%s", data_dir)
    return validate_step17_files(data_dir)


__all__ = [
    'validate_step17_files',
    'validate_step17_complete'
]
