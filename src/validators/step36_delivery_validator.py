"""
Validator logic for Step 36 unified delivery.
Exposes:
  - validate(df, args)
  - find_latest_unified_csv(yyyymm, period)

This lives under src/ so pytest tests can import it following the
"tests mirror src" philosophy.
"""
from typing import Dict
import glob
import os
import pandas as pd


def find_latest_unified_csv(yyyymm: str, period: str) -> str:
    period_label = f"{yyyymm}{period}"
    pattern = os.path.join("output", f"unified_delivery_{period_label}_*.csv")
    matches = sorted(glob.glob(pattern))
    return matches[-1] if matches else ""


def validate(df: pd.DataFrame, args) -> Dict:
    """Validate unified delivery DataFrame against customer-facing invariants.

    Required fields: period metadata, store identifier, temperature_band
    Thresholds via args: min_columns, min_temp_coverage
    """
    results = {"pass": True, "errors": [], "warnings": [], "stats": {}}

    # Basic stats
    results["stats"]["row_count"] = int(len(df))
    results["stats"]["column_count"] = int(len(df.columns))

    # Critical: non-empty
    if len(df) == 0:
        results["pass"] = False
        results["errors"].append("Unified CSV has 0 rows")

    # Critical: no duplicate column names
    dup_cols = df.columns[df.columns.duplicated()].tolist()
    if dup_cols:
        results["pass"] = False
        results["errors"].append(f"Duplicate columns present: {dup_cols}")

    # Critical: period metadata
    required_period_cols = ["period_label", "target_yyyymm", "target_period"]
    missing_period = [c for c in required_period_cols if c not in df.columns]
    if missing_period:
        results["pass"] = False
        results["errors"].append(f"Missing period metadata columns: {missing_period}")

    # Critical: store identifier present
    has_store_code = ("Store_Code" in df.columns) or ("str_code" in df.columns)
    if not has_store_code:
        results["pass"] = False
        results["errors"].append("Missing store identifier: expected 'Store_Code' or 'str_code'")

    # Critical: temperature_band present
    if "temperature_band" not in df.columns:
        results["pass"] = False
        results["errors"].append("Missing required temperature field: 'temperature_band'")
    else:
        non_null = int(df["temperature_band"].notna().sum())
        total = max(1, len(df))
        coverage = non_null / total
        results["stats"]["temperature_band_non_null"] = non_null
        results["stats"]["temperature_band_coverage"] = round(coverage, 4)
        if coverage < getattr(args, "min_temp_coverage", 0.95):
            results["pass"] = False
            results["errors"].append(
                f"temperature_band coverage {coverage:.1%} < required {getattr(args, 'min_temp_coverage', 0.95):.1%}"
            )

    # Soft requirement: at least one additional temperature helper column
    temp_helpers = [
        "Temperature_Zone",
        "Temperature_Band_Simple",
        "Temperature_Band_Detailed",
    ]
    if not any(c in df.columns for c in temp_helpers):
        results["warnings"].append(
            "No auxiliary temperature fields found (Temperature_Zone/Temperature_Band_Simple/Temperature_Band_Detailed)"
        )

    # Critical: minimum column count
    if len(df.columns) < getattr(args, "min_columns", 60):
        results["pass"] = False
        results["errors"].append(
            f"Column count {len(df.columns)} < min required {getattr(args, 'min_columns', 60)}"
        )

    return results


__all__ = ["validate", "find_latest_unified_csv"]
