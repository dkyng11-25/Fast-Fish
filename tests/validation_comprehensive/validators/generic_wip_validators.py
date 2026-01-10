#!/usr/bin/env python3
"""
Generic WIP Validators for Later Steps (16–37)

These validators provide basic, conservative checks for steps without finalized
specs. They are clearly marked WIP and require human review.

Author: Data Pipeline
Date: 2025-09-17
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def validate_generic_results(df: pd.DataFrame, step_name: str) -> Dict[str, Any]:
    """
    WIP: Validate a generic results DataFrame with minimal assumptions.
    - Ensure DataFrame is non-empty
    - If common id-like columns exist, ensure non-null
    - Summarize missing values
    """
    out: Dict[str, Any] = {
        "validation_passed": True,
        "errors": [],
        "warnings": [],
        "statistics": {"step": step_name}
    }
    try:
        if df.empty:
            out["errors"].append("Results DataFrame is empty")
            out["validation_passed"] = False
        # Common id-like columns
        for col in ["str_code", "cluster_id", "spu_code", "subcategory", "category"]:
            if col in df.columns and df[col].isnull().any():
                out["warnings"].append(f"Column '{col}' contains null values")
        # Missing values summary
        mv = df.isnull().sum()
        out["statistics"]["missing_values"] = {k: int(v) for k, v in mv.items()}
        # Basic cardinality
        out["statistics"]["num_rows"] = int(len(df))
        out["statistics"]["num_columns"] = int(len(df.columns))
    except Exception as e:
        out["errors"].append(f"Generic validation error: {str(e)}")
        out["validation_passed"] = False
    return out


essential_columns_by_step = {
    # Extend over time as specs stabilize
    # 'step16': ["str_code", "cluster_id"],
}


def validate_generic_step_complete(step_name: str, output_dir: str) -> Dict[str, Any]:
    """
    WIP: Validate a generic step by reading the standard output file pattern
    written by the modular runner: {step_name}_results.csv
    """
    out_dir = Path(output_dir)
    file_name = f"{step_name}_results.csv"
    csv_path = out_dir / file_name

    result: Dict[str, Any] = {
        "validation_passed": True,
        "errors": [],
        "warnings": [],
        "statistics": {"validation_timestamp": datetime.now().isoformat()},
        "file": str(csv_path)
    }

    if not csv_path.exists():
        result["errors"].append(f"Missing expected generic output: {file_name}")
        result["validation_passed"] = False
        return result

    try:
        df = pd.read_csv(csv_path)
        core = validate_generic_results(df, step_name)
        result.update({
            "validation_passed": core["validation_passed"],
            "errors": core["errors"],
            "warnings": core["warnings"],
            "statistics": {**result["statistics"], **core["statistics"]}
        })
        # Optional: step-specific essentials if defined
        essentials = essential_columns_by_step.get(step_name)
        if essentials:
            missing = [c for c in essentials if c not in df.columns]
            if missing:
                result["warnings"].append(f"Missing suggested columns for {step_name}: {missing}")
    except Exception as e:
        result["errors"].append(f"Failed to read/validate {file_name}: {str(e)}")
        result["validation_passed"] = False

    return result


__all__ = [
    'validate_generic_results',
    'validate_generic_step_complete'
]


