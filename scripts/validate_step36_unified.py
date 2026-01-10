#!/usr/bin/env python3
"""
Validator for Step 36 unified delivery outputs.

Checks per period:
- File existence (CSV/XLSX/validation JSON)
- Column inventory, data types, and null counts
- Critical columns presence and type conformance
- Integer and reconciliation checks for allocations
- Duplicate detection on store-line key and group-line key
- Cross-period consistency (when run for multiple periods)

Outputs JSON reports next to the CSV; prints concise summary to stdout.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from typing import Dict, List, Optional, Tuple

import pandas as pd

try:
    from src.pipeline_manifest import get_manifest
    from src.config import get_period_label
except Exception:
    from pipeline_manifest import get_manifest
    from config import get_period_label


def _resolve_unified_csv(period_label: str) -> Optional[str]:
    man = get_manifest()
    try:
        path = man.get_latest_output("step36", key_prefix="unified_delivery_csv", period_label=period_label)
        if path and os.path.exists(path):
            return path
    except Exception:
        pass
    candidates = sorted(glob.glob(f"output/unified_delivery_{period_label}_*.csv"))
    return candidates[-1] if candidates else None


def _resolve_companions(csv_path: str) -> Tuple[Optional[str], Optional[str]]:
    xlsx = csv_path.replace(".csv", ".xlsx")
    qa = csv_path.replace(".csv", "_validation.json")
    return (xlsx if os.path.exists(xlsx) else None, qa if os.path.exists(qa) else None)


def _profile_df(df: pd.DataFrame) -> Dict:
    dtypes = {c: str(t) for c, t in df.dtypes.items()}
    null_counts = {c: int(df[c].isna().sum()) for c in df.columns}
    return {"columns": list(df.columns), "dtypes": dtypes, "null_counts": null_counts}


def _is_integer_series(s: pd.Series) -> Tuple[bool, int]:
    values = pd.to_numeric(s, errors="coerce")
    non_int = int((values != values.round()).sum())
    return (non_int == 0, non_int)


def _run_checks(period_label: str, csv_path: str) -> Dict:
    report: Dict = {"period_label": period_label, "csv_path": csv_path, "checks": {}, "warnings": [], "errors": []}

    df = pd.read_csv(csv_path)
    prof = _profile_df(df)
    report["profile"] = prof

    # Canonical schema expectations (presence optionality indicated by lists)
    expected_required = [
        "Store_Code",
        "Store_Group_Name",
        "Target_Style_Tags",
        "Allocated_ΔQty_Rounded",
        "Allocated_ΔQty",
        "Group_ΔQty",
        "Category",
        "Subcategory",
    ]
    expected_optional = [
        "Expected_Benefit",
        "Confidence_Score",
        "Current_Sell_Through_Rate",
        "Target_Sell_Through_Rate",
        "Sell_Through_Improvement",
        "Constraint_Status",
        "Capacity_Utilization",
        "Action_Priority",
        "Performance_Tier",
        "Growth_Potential",
        "Risk_Level",
        "Cluster_ID",
        "Cluster_Name",
        "Operational_Tag",
        "Temperature_Zone",
        "Season",
        "Gender",
        "Location",
        "Data_Based_Rationale",
        "Priority_Score",
        "Gap_Intensity",
        "Coverage_Index",
        "Priority_Index",
    ]

    # Presence of critical columns
    missing = [c for c in expected_required if c not in df.columns]
    report["checks"]["critical_columns_present"] = {"ok": len(missing) == 0, "missing_columns": missing}
    if missing:
        report["errors"].append(f"Missing critical columns: {missing}")

    # Integer check for Allocated_ΔQty_Rounded
    if "Allocated_ΔQty_Rounded" in df.columns:
        ok, n_nonint = _is_integer_series(df["Allocated_ΔQty_Rounded"])
        report["checks"]["allocated_qty_integer"] = {"ok": ok, "non_integer_count": n_nonint}
        if not ok:
            report["errors"].append("Allocated_ΔQty_Rounded contains non-integer values")

    # Group reconciliation: sum of rounded equals Group_ΔQty (rounded)
    if all(c in df.columns for c in ["Store_Group_Name", "Target_Style_Tags", "Group_ΔQty", "Allocated_ΔQty_Rounded"]):
        grp = df.groupby(["Store_Group_Name", "Target_Style_Tags"], dropna=False).agg({
            "Group_ΔQty": "first",
            "Allocated_ΔQty_Rounded": "sum",
        }).reset_index()
        grp["match"] = grp["Group_ΔQty"].round().astype(int) == grp["Allocated_ΔQty_Rounded"].astype(int)
        ok = bool(grp["match"].all()) if not grp.empty else True
        mismatches = grp.loc[~grp["match"], ["Store_Group_Name", "Target_Style_Tags", "Group_ΔQty", "Allocated_ΔQty_Rounded"]].head(50).to_dict(orient="records")
        report["checks"]["group_sum_reconciliation"] = {"ok": ok, "mismatch_samples": mismatches, "checked_groups": int(len(grp))}
        if not ok:
            report["errors"].append("Group sum reconciliation failed for some groups")

    # Duplicate detection on store-line key
    store_key = [c for c in ["Store_Code", "Store_Group_Name", "Target_Style_Tags"] if c in df.columns]
    if len(store_key) == 3:
        dup_mask = df.duplicated(subset=store_key, keep=False)
        dup_count = int(dup_mask.sum())
        report["checks"]["duplicates_store_line_key"] = {"duplicate_rows": dup_count}
        if dup_count > 0:
            samples = df.loc[dup_mask, store_key].drop_duplicates().head(20).to_dict(orient="records")
            report["warnings"].append("Duplicates detected on store-line key")
            report["checks"]["duplicates_store_line_key"]["samples"] = samples

    # Type guidance for numeric columns
    numeric_expected = [
        "Allocated_ΔQty_Rounded",
        "Allocated_ΔQty",
        "Group_ΔQty",
        "Expected_Benefit",
        "Confidence_Score",
        "Current_Sell_Through_Rate",
        "Target_Sell_Through_Rate",
        "Sell_Through_Improvement",
        "Capacity_Utilization",
        "Priority_Score",
        "Coverage_Index",
        "Priority_Index",
    ]
    type_issues: List[str] = []
    for col in numeric_expected:
        if col in df.columns:
            vals = pd.to_numeric(df[col], errors="coerce")
            if vals.notna().sum() > 0 and str(df[col].dtype) not in ("int64", "float64"):
                type_issues.append(col)
    report["checks"]["numeric_type_conformance"] = {"ok": len(type_issues) == 0, "non_numeric_columns": type_issues}
    if type_issues:
        report["warnings"].append(f"Columns not parsed as numeric: {type_issues}")

    # Range checks
    range_issues: Dict[str, Dict] = {}
    def _check_range(col: str, lo: float, hi: float, allow_null: bool = True):
        if col in df.columns:
            vals = pd.to_numeric(df[col], errors="coerce")
            mask = vals.notna() if allow_null else pd.Series([True] * len(vals))
            too_low = int(((vals < lo) & mask).sum())
            too_high = int(((vals > hi) & mask).sum())
            if too_low > 0 or too_high > 0:
                range_issues[col] = {"min_allowed": lo, "max_allowed": hi, "too_low": too_low, "too_high": too_high}

    _check_range("Capacity_Utilization", 0.0, 1.5)  # utilization can exceed 1 slightly
    _check_range("Current_Sell_Through_Rate", 0.0, 1.0)
    _check_range("Target_Sell_Through_Rate", 0.0, 1.0)
    _check_range("Sell_Through_Improvement", -1.0, 1.0)
    _check_range("Priority_Score", 0.0, 1.0)
    _check_range("Expected_Benefit", 0.0, 1e12)
    report["checks"]["range_checks"] = {"ok": len(range_issues) == 0, "issues": range_issues}
    if range_issues:
        report["warnings"].append("Range issues detected in numeric columns")

    # Enum/label checks
    enum_issues: Dict[str, Dict] = {}
    enums = {
        "Season": {"spring", "summer", "autumn", "winter", "Spring", "Summer", "Autumn", "Winter"},
        "Gender": {"men", "women", "unisex", "Men", "Women", "Unisex"},
        "Location": {"front", "back", "Front", "Back"},
        "Constraint_Status": {"Normal", "Minor-Constraint", "Critical-Constraint", "Under-Utilized"},
        "Action_Priority": {"Immediate", "High-Priority", "Medium-Priority", "Monitor"},
    }
    for col, allowed in enums.items():
        if col in df.columns:
            vals = df[col].dropna().astype(str)
            bad = sorted(list(set(vals.unique()) - allowed))
            if bad:
                enum_issues[col] = {"unexpected_values": bad[:50], "count": int(vals.isin(bad).sum())}
    report["checks"]["enum_checks"] = {"ok": len(enum_issues) == 0, "issues": enum_issues}
    if enum_issues:
        report["warnings"].append("Unexpected enum values detected")

    # Whitespace checks for string columns
    ws_issues: Dict[str, Dict] = {}
    for col in df.columns:
        if df[col].dtype == object:
            s = df[col].dropna().astype(str)
            leading = int(s.str.match(r"^\s+").sum())
            trailing = int(s.str.match(r".*\s+$").sum())
            if leading > 0 or trailing > 0:
                ws_issues[col] = {"leading": leading, "trailing": trailing}
    report["checks"]["whitespace_checks"] = {"ok": len(ws_issues) == 0, "issues": ws_issues}
    if ws_issues:
        report["warnings"].append("Whitespace issues detected in string columns")

    return report


def _cross_period(report_a: Dict, report_b: Dict) -> Dict:
    cols_a = set(report_a.get("profile", {}).get("columns", []))
    cols_b = set(report_b.get("profile", {}).get("columns", []))
    a_only = sorted(list(cols_a - cols_b))
    b_only = sorted(list(cols_b - cols_a))
    return {"A_only": a_only, "B_only": b_only, "ok": len(a_only) == 0 and len(b_only) == 0}


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Step 36 unified outputs")
    p.add_argument("--target-yyyymm", required=True)
    p.add_argument("--periods", default="A,B")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    periods = [p.strip().upper() for p in args.periods.split(",") if p.strip()]
    outputs: Dict[str, Dict] = {}

    for p in periods:
        pl = get_period_label(args.target_yyyymm, p)
        csv_path = _resolve_unified_csv(pl)
        if not csv_path:
            print(json.dumps({"period": pl, "error": "Unified CSV not found"}))
            return 2
        xlsx_path, qa_path = _resolve_companions(csv_path)
        rep = _run_checks(pl, csv_path)
        rep["files"] = {"csv": csv_path, "xlsx": xlsx_path, "qa": qa_path}
        outputs[p] = rep

        # Write per-period detailed report
        out_json = csv_path.replace(".csv", "_validation_full.json")
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(rep, f, indent=2, ensure_ascii=False)

    summary: Dict = {"periods": periods, "reports": {}}
    for p, rep in outputs.items():
        errs = rep.get("errors", [])
        warns = rep.get("warnings", [])
        checks = rep.get("checks", {})
        summary["reports"][p] = {
            "csv": rep.get("files", {}).get("csv"),
            "xlsx": rep.get("files", {}).get("xlsx"),
            "qa": rep.get("files", {}).get("qa"),
            "errors": errs,
            "warnings": warns,
            "checks": {
                k: v for k, v in checks.items() if k in [
                    "critical_columns_present",
                    "allocated_qty_integer",
                    "group_sum_reconciliation",
                    "duplicates_store_line_key",
                    "numeric_type_conformance",
                ]
            },
        }

    if set(periods) == {"A", "B"}:
        summary["cross_period"] = _cross_period(outputs["A"], outputs["B"]) if "A" in outputs and "B" in outputs else {}

    # Write markdown audit alongside each CSV
    for p, rep in outputs.items():
        csv_path = rep.get("files", {}).get("csv") if rep.get("files") else None
        if not csv_path:
            continue
        md_path = csv_path.replace(".csv", "_audit.md")
        lines: List[str] = []
        lines.append(f"# Step 36 Unified Output Audit — {rep.get('period_label', '')}")
        lines.append("")
        lines.append(f"CSV: `{csv_path}`")
        lines.append("")
        lines.append("## Checks")
        for k, v in rep.get("checks", {}).items():
            lines.append(f"- {k}: {json.dumps(v, ensure_ascii=False)}")
        if rep.get("warnings"):
            lines.append("")
            lines.append("## Warnings")
            for w in rep["warnings"]:
                lines.append(f"- {w}")
        if rep.get("errors"):
            lines.append("")
            lines.append("## Errors")
            for e in rep["errors"]:
                lines.append(f"- {e}")
        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except Exception:
            pass

    print(json.dumps(summary, ensure_ascii=False))
    # Non-zero exit on any errors
    has_errors = any(outputs[p].get("errors") for p in outputs)
    return 0 if not has_errors else 2


if __name__ == "__main__":
    raise SystemExit(main())


