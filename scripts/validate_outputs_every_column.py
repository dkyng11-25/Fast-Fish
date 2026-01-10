#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np


@dataclass
class PeriodPaths:
    period_label: str
    unified_csv: str
    store_lines_csv: Optional[str]
    customer_xlsx: Optional[str]


def _latest(pattern: str) -> Optional[str]:
    cand = sorted(glob.glob(pattern))
    return cand[-1] if cand else None


def resolve_paths(yyyymm: str, period: str) -> PeriodPaths:
    period_label = f"{yyyymm}{period.upper()}"
    unified = _latest(f"output/unified_delivery_{period_label}_*.csv")
    store_lines = _latest(f"output/customer_delivery_{period_label}_*_store_lines.csv")
    xlsx = _latest(f"output/customer_delivery_{period_label}_*.xlsx")
    if not unified:
        raise FileNotFoundError(f"Unified CSV not found for {period_label}")
    return PeriodPaths(period_label, unified, store_lines, xlsx)


# Spec-driven expectations (from docs/step36_unified_delivery_spec.md)
PREFERRED_FINAL_ORDER = [
    "Analysis_Year","Analysis_Month","Analysis_Period","Store_Code","Store_Group_Name",
    "Target_Style_Tags","Category","Subcategory","Target_SPU_Quantity","Allocated_ΔQty_Rounded",
    "Allocated_ΔQty","Group_ΔQty","Action","Instruction","Action_Priority_Rank","Tag_Bundle",
    "Expected_Benefit","Confidence_Score","Current_Sell_Through_Rate","Target_Sell_Through_Rate",
    "Sell_Through_Improvement","Store_Sell_Through_Rate","Constraint_Status","Capacity_Utilization",
    "Store_Temperature_Band","Temperature_Band_Simple","Temperature_Band_Detailed","Temperature_Value_C",
    "Cluster_Temp_C_Mean","Cluster_Temp_Quintile","Temperature_Suitability_Graded","Store_Fashion_Profile",
    "Action_Priority","Performance_Tier","Growth_Potential","Risk_Level","Cluster_ID","Cluster_Name",
    "Operational_Tag","Temperature_Zone","Season","Season_source","Gender","Gender_source","Location",
    "Location_source","Planning_Season","Planning_Year","Planning_Period_Label","Data_Based_Rationale",
    "Priority_Score","Historical_Temp_C_Mean","Historical_Temp_C_P5","Historical_Temp_C_P95",
    "Historical_Temp_Band_Detailed","Historical_Temp_Quintile","Temp_Band_Divergence",
]

# Columns the unified output must always include (strict set for validation)
REQUIRED_UNIFIED = [
    "Analysis_Year","Analysis_Month","Analysis_Period",
    "Store_Code","Store_Group_Name",
    "Target_Style_Tags","Category","Subcategory",
    "Allocated_ΔQty","Allocated_ΔQty_Rounded","Target_SPU_Quantity",
    "Group_ΔQty","Action","Instruction","Action_Priority_Rank","Tag_Bundle",
    "Expected_Benefit","Confidence_Score",
    "Current_Sell_Through_Rate","Target_Sell_Through_Rate","Sell_Through_Improvement",
    "Capacity_Utilization","Constraint_Status",
    "Season","Gender","Location",
    "Planning_Season","Planning_Year","Planning_Period_Label",
    "Priority_Score",
]

# Columns explicitly optional (may be absent due to upstream availability)
OPTIONAL_UNIFIED = [
    "Category_Display","Store_Sell_Through_Rate","Store_Temperature_Band","Temperature_Band_Simple",
    "Temperature_Band_Detailed","Temperature_Value_C","Cluster_Temp_C_Mean","Cluster_Temp_Quintile",
    "Temperature_Suitability_Graded","Store_Fashion_Profile","Action_Priority","Performance_Tier",
    "Growth_Potential","Risk_Level","Cluster_ID","Cluster_Name","Operational_Tag","Temperature_Zone",
    "Season_source","Gender_source","Location_source","Data_Based_Rationale",
    "Historical_Temp_C_Mean","Historical_Temp_C_P5","Historical_Temp_C_P95",
    "Historical_Temp_Band_Detailed","Historical_Temp_Quintile","Temp_Band_Divergence",
]

# Enumerations / constraints
ENUM_ACTION = {"Add","Reduce","No-Change"}
ENUM_PLANNING_SEASON = {"Winter","Spring","Summer","Autumn"}
ENUM_TEMP_SIMPLE = {"Cold","Moderate","Warm"}
ENUM_TEMP_DETAILED = {"Cold","Cool","Mild","Moderate","Warm","Hot"}
ENUM_TEMP_SUIT = {"High","Medium","Review","Unknown"}
ENUM_QUINTILE = {"Q1-Coldest","Q2","Q3","Q4","Q5-Warmest"}

# Internal columns that must NOT appear in store_lines
STORELINES_INTERNAL_DROP = [
    "Group_ΔQty","Group_ΔQty_source","Target_ST_source","Current_ST_source","Improvement_source",
    "Target_ST_cap_percentile","Target_ST_cap_value","Target_ST_capped_flag",
    "Season_source","Gender_source","Location_source",
    "Historical_Temp_C_Mean","Historical_Temp_C_P5","Historical_Temp_C_P95",
    "Historical_Temp_Band_Detailed","Historical_Temp_Quintile","Temp_Band_Divergence",
    "Data_Based_Rationale","Action_Order","Priority_Score",
]


def _is_int_series(s: pd.Series) -> bool:
    if s.dropna().empty:
        return True
    try:
        coerced = pd.to_numeric(s, errors="coerce")
        return bool(np.all(np.isfinite(coerced.dropna())) and np.all(np.equal(coerced.dropna(), np.floor(coerced.dropna()))))
    except Exception:
        return False


def _ratio_in_range(s: pd.Series, lo: float, hi: float) -> Tuple[int, int]:
    s_num = pd.to_numeric(s, errors="coerce")
    total = len(s_num)
    bad = int(((s_num < lo) | (s_num > hi)).sum())
    return bad, total


def validate_unified(unified_path: str, period_label: str) -> Dict:
    df = pd.read_csv(unified_path)
    issues: List[str] = []

    # Presence checks
    missing = [c for c in REQUIRED_UNIFIED if c not in df.columns]
    if missing:
        issues.append(f"Missing required columns: {missing}")

    # Column-by-column validations
    col_checks: Dict[str, Dict] = {}

    def record(col: str, ok: bool, msg: str = ""):
        col_checks[col] = {"ok": bool(ok), "message": msg}

    # Basic types/constraints
    if "Analysis_Period" in df.columns:
        valid = df["Analysis_Period"].astype(str).isin({"A","B"}).all()
        record("Analysis_Period", bool(valid), "must be A/B")

    if "Allocated_ΔQty_Rounded" in df.columns:
        record("Allocated_ΔQty_Rounded", _is_int_series(df["Allocated_ΔQty_Rounded"]), "must be integer")
    if "Target_SPU_Quantity" in df.columns:
        record("Target_SPU_Quantity", _is_int_series(df["Target_SPU_Quantity"]), "must be integer")
        if "Allocated_ΔQty_Rounded" in df.columns:
            eq = (pd.to_numeric(df["Target_SPU_Quantity"], errors="coerce") == pd.to_numeric(df["Allocated_ΔQty_Rounded"], errors="coerce")).all()
            record("Target_SPU_Quantity=Allocated_ΔQty_Rounded", bool(eq), "must equal exactly")

    if "Action" in df.columns:
        ok = df["Action"].isin(list(ENUM_ACTION)).all()
        record("Action", bool(ok), f"must be in {sorted(ENUM_ACTION)}")

    for ratio_col, rng in [
        ("Current_Sell_Through_Rate", (0.0,1.0)),
        ("Target_Sell_Through_Rate", (0.0,1.0)),
        ("Sell_Through_Improvement", (-1.0,1.0)),
        ("Capacity_Utilization", (0.0,1.0)),
    ]:
        if ratio_col in df.columns:
            bad, total = _ratio_in_range(df[ratio_col], rng[0], rng[1])
            record(ratio_col, bad == 0, f"{bad}/{total} rows out of range {rng}")

    if "Target_Style_Tags" in df.columns:
        # Prefer bracketed string form
        s = df["Target_Style_Tags"].astype(str)
        ok = s.str.startswith("[").fillna(False).all() & s.str.endswith("]").fillna(False).all()
        record("Target_Style_Tags_format", bool(ok), "should look like [Men, Autumn]")

    if "Planning_Season" in df.columns:
        ok = df["Planning_Season"].isin(list(ENUM_PLANNING_SEASON)).all()
        record("Planning_Season", bool(ok), f"must be in {sorted(ENUM_PLANNING_SEASON)}")

    if "Temperature_Band_Simple" in df.columns:
        ok = df["Temperature_Band_Simple"].dropna().isin(list(ENUM_TEMP_SIMPLE)).all()
        record("Temperature_Band_Simple", bool(ok), f"must be in {sorted(ENUM_TEMP_SIMPLE)} when present")

    if "Temperature_Band_Detailed" in df.columns:
        ok = df["Temperature_Band_Detailed"].dropna().isin(list(ENUM_TEMP_DETAILED)).all()
        record("Temperature_Band_Detailed", bool(ok), f"must be in {sorted(ENUM_TEMP_DETAILED)} when present")

    if "Temperature_Suitability_Graded" in df.columns:
        ok = df["Temperature_Suitability_Graded"].dropna().isin(list(ENUM_TEMP_SUIT)).all()
        record("Temperature_Suitability_Graded", bool(ok), f"must be in {sorted(ENUM_TEMP_SUIT)} when present")

    if "Cluster_Temp_Quintile" in df.columns:
        ok = df["Cluster_Temp_Quintile"].dropna().isin(list(ENUM_QUINTILE)).all()
        record("Cluster_Temp_Quintile", bool(ok), f"must be in {sorted(ENUM_QUINTILE)} when present")

    # Overview figures
    overview = {
        "rows": len(df),
        "adds": int((df.get("Action") == "Add").sum()) if "Action" in df.columns else None,
        "reduces": int((df.get("Action") == "Reduce").sum()) if "Action" in df.columns else None,
        "null_counts": {c: int(df[c].isna().sum()) for c in REQUIRED_UNIFIED if c in df.columns},
        "present_columns": sorted(list(df.columns)),
        "missing_required": missing,
        "optional_present": [c for c in OPTIONAL_UNIFIED if c in df.columns],
    }

    return {
        "period": period_label,
        "unified_path": unified_path,
        "issues": issues,
        "column_checks": col_checks,
        "overview": overview,
    }


def validate_store_lines(store_lines_csv: Optional[str], unified_df: pd.DataFrame) -> Dict:
    if not store_lines_csv or not os.path.exists(store_lines_csv):
        return {
            "store_lines_path": store_lines_csv,
            "issues": ["store_lines CSV not found"],
            "overview": {},
            "column_checks": {},
        }
    st = pd.read_csv(store_lines_csv)
    issues: List[str] = []
    checks: Dict[str, Dict] = {}

    def record(col: str, ok: bool, msg: str = ""):
        checks[col] = {"ok": bool(ok), "message": msg}

    # Size consistency
    record("row_count_matches_unified", len(st) == len(unified_df), f"store_lines={len(st)} vs unified={len(unified_df)}")

    # Internal columns should be absent
    internal_present = [c for c in STORELINES_INTERNAL_DROP if c in st.columns]
    if internal_present:
        issues.append(f"Internal columns present in store_lines (should have been dropped): {internal_present}")

    # Basic fields
    for c in ["Action","Allocated_ΔQty_Rounded","Target_SPU_Quantity","Store_Code","Store_Group_Name","Category","Subcategory"]:
        if c not in st.columns:
            issues.append(f"Missing store_lines column: {c}")

    if "Allocated_ΔQty_Rounded" in st.columns:
        record("Allocated_ΔQty_Rounded", _is_int_series(st["Allocated_ΔQty_Rounded"]), "must be integer")
    if "Target_SPU_Quantity" in st.columns:
        record("Target_SPU_Quantity", _is_int_series(st["Target_SPU_Quantity"]), "must be integer")
        if "Allocated_ΔQty_Rounded" in st.columns:
            eq = (pd.to_numeric(st["Target_SPU_Quantity"], errors="coerce") == pd.to_numeric(st["Allocated_ΔQty_Rounded"], errors="coerce")).all()
            record("Target_SPU_Quantity=Allocated_ΔQty_Rounded", bool(eq), "must equal exactly")

    if "Action" in st.columns:
        ok = st["Action"].isin(list(ENUM_ACTION)).all()
        record("Action", bool(ok), f"must be in {sorted(ENUM_ACTION)}")

    overview = {
        "rows": len(st),
        "adds": int((st.get("Action") == "Add").sum()) if "Action" in st.columns else None,
        "reduces": int((st.get("Action") == "Reduce").sum()) if "Action" in st.columns else None,
        "present_columns": sorted(list(st.columns)),
        "internal_columns_present": internal_present,
    }

    return {
        "store_lines_path": store_lines_csv,
        "issues": issues,
        "overview": overview,
        "column_checks": checks,
    }


def validate_excel_focus_sheet(xlsx_path: Optional[str]) -> Dict:
    if not xlsx_path or not os.path.exists(xlsx_path):
        return {"xlsx_path": xlsx_path, "issues": ["xlsx not found"], "focus_sheet_rows": None}
    try:
        # Only load sheet names and the focus sheet count cheaply
        xl = pd.ExcelFile(xlsx_path)
        sheets = xl.sheet_names
        focus_rows = None
        if "Women Casual Pants" in sheets:
            df_focus = xl.parse("Women Casual Pants", nrows=5)  # sample first rows for sanity
            focus_rows = int(len(df_focus))  # at least exists
        return {"xlsx_path": xlsx_path, "issues": [], "sheets": sheets, "focus_sheet_rows_sample": focus_rows}
    except Exception as e:
        return {"xlsx_path": xlsx_path, "issues": [str(e)], "focus_sheet_rows": None}


def run_validation(yyyymm: str, period: str) -> Dict:
    paths = resolve_paths(yyyymm, period)
    uni = pd.read_csv(paths.unified_csv)
    unified_report = validate_unified(paths.unified_csv, paths.period_label)
    store_report = validate_store_lines(paths.store_lines_csv, uni)
    excel_report = validate_excel_focus_sheet(paths.customer_xlsx)
    return {
        "period": paths.period_label,
        "unified": unified_report,
        "store_lines": store_report,
        "excel": excel_report,
    }


def save_reports(report: Dict, out_dir: str = "output/qa") -> Tuple[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    period = report.get("period", "unknown")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    jpath = os.path.join(out_dir, f"validation_{period}_{ts}.json")
    mpath = os.path.join(out_dir, f"validation_{period}_{ts}.md")

    with open(jpath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Lightweight Markdown summary
    lines = []
    lines.append(f"# Validation Report — {period}")
    lines.append("")
    lines.append("## Unified")
    lines.append(f"Path: `{report['unified']['unified_path']}`")
    lines.append(f"Rows: {report['unified']['overview']['rows']}")
    if report['unified']['issues']:
        lines.append(f"Issues: {report['unified']['issues']}")
    missing = report['unified']['overview'].get('missing_required', [])
    if missing:
        lines.append(f"Missing required columns: {missing}")
    lines.append("")

    lines.append("## Store Lines")
    lines.append(f"Path: `{report['store_lines']['store_lines_path']}`")
    if report['store_lines']['issues']:
        lines.append(f"Issues: {report['store_lines']['issues']}")
    lines.append("")

    lines.append("## Excel Package")
    lines.append(f"Path: `{report['excel'].get('xlsx_path')}`")
    if report['excel'].get('issues'):
        lines.append(f"Issues: {report['excel'].get('issues')}")
    sheets = report['excel'].get('sheets')
    if sheets:
        lines.append(f"Sheets: {', '.join(sheets)}")
    lines.append("")

    with open(mpath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return jpath, mpath


def main():
    p = argparse.ArgumentParser(description="Validate Step36/37 outputs for every column")
    p.add_argument("--target-yyyymm", required=True)
    p.add_argument("--period", choices=["A","B","both"], default="both")
    args = p.parse_args()

    periods = ["A","B"] if args.period == "both" else [args.period]
    overall: Dict[str, Dict] = {}
    for per in periods:
        try:
            rep = run_validation(args.target_yyyymm, per)
            save_reports(rep)
            overall[per] = rep
            print(f"[OK] Validated {args.target_yyyymm}{per}")
        except Exception as e:
            overall[per] = {"error": str(e)}
            print(f"[ERR] Validation failed for {args.target_yyyymm}{per}: {e}")

    # Write a combined summary JSON for convenience
    os.makedirs("output/qa", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"output/qa/validation_summary_{args.target_yyyymm}_{ts}.json", "w", encoding="utf-8") as f:
        json.dump(overall, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
