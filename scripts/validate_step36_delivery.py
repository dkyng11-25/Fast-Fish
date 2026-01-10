#!/usr/bin/env python3
"""
Validate Step 36 unified delivery output against expected customer-facing schema features.

Usage:
  python scripts/validate_step36_delivery.py --target-yyyymm 202509 --target-period A \
      [--file output/unified_delivery_202509A_20250911_170804.csv] \
      [--min-columns 60] [--min-temp-coverage 0.95]

What it checks (baseline):
- File exists and is readable (auto-discovers the latest for the period if --file not provided)
- Row count > 0
- Presence of key columns:
  * Period metadata: period_label, target_yyyymm, target_period (added by _embed_period_metadata_columns)
  * Store identifier: either Store_Code or str_code
  * Temperature fields: temperature_band (required), plus at least one of
    [Temperature_Zone, Temperature_Band_Simple, Temperature_Band_Detailed]
- Temperature coverage: non-null ratio for temperature_band ≥ min-temp-coverage (default 95%)
- Column count ≥ min-columns (default 60)
- No duplicate column names

Exit code:
- 0 if all critical checks PASS (warnings allowed)
- 1 if any critical check FAILS

This script does not hardcode every column; it validates the important invariants customers depend on,
while allowing step36 to evolve additional fields safely.
"""
import argparse
import json
import sys
import pandas as pd
from src.validators.step36_delivery_validator import validate, find_latest_unified_csv


def main():
    parser = argparse.ArgumentParser(description="Validate Step 36 unified delivery CSV against customer spec invariants")
    parser.add_argument("--target-yyyymm", required=True)
    parser.add_argument("--target-period", required=True, choices=["A", "B"])
    parser.add_argument("--file", default="", help="Explicit path to unified CSV (optional)")
    parser.add_argument("--min-columns", type=int, default=60)
    parser.add_argument("--min-temp-coverage", dest="min_temp_coverage", type=float, default=0.95)
    args = parser.parse_args()

    path = args.file or find_latest_unified_csv(args.target_yyyymm, args.target_period)
    if not path:
        print(json.dumps({"pass": False, "errors": ["Unified CSV not found"], "warnings": []}, ensure_ascii=False))
        sys.exit(1)

    try:
        df = pd.read_csv(path)
    except Exception as e:
        print(json.dumps({"pass": False, "errors": [f"Failed to read CSV: {e}"], "warnings": [], "path": path}, ensure_ascii=False))
        sys.exit(1)

    results = validate(df, args)
    results["path"] = path

    print(json.dumps(results, ensure_ascii=False, indent=2))
    sys.exit(0 if results["pass"] else 1)


if __name__ == "__main__":
    main()
