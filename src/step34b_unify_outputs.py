#!/usr/bin/env python3
"""
Step 34: Unify period-specific outputs into a single CSV with all tags.

- Default source: Step 14 enhanced Fast Fish outputs (period-specific files without timestamps)
  output/enhanced_fast_fish_format_{YYYYMM}A.csv
  output/enhanced_fast_fish_format_{YYYYMM}B.csv

- Optional sources via --source:
  * enhanced     -> Step 14 period CSVs (default)
  * retagged     -> Step 14 period CSVs with _retagged suffix
  * for_step17   -> Step 14 period CSVs prepared for Step 17 (_for_step17 suffix)
  * step17       -> Uses pipeline_manifest.json to locate Step 17 period outputs
  * step18       -> Uses pipeline_manifest.json to locate Step 18 period outputs

- Output: output/enhanced_fast_fish_format_{YYYYMM}{PERIODS}_unified.csv
  where PERIODS is the concatenated string of included periods, e.g., AB

- Also registers the unified output in output/pipeline_manifest.json under step34.

 HOW TO RUN (CLI)
 ----------------
 Overview
 - This script unifies one or both half-month period files for a given YYYYMM.
 - Valid flags: --target-yyyymm, --periods, --source. There is NO --target-period flag.

 Examples
 - Unify only A for 202510 using Step 18 outputs (common for testing a single half):
     PYTHONPATH=. python3 src/step34b_unify_outputs.py \
       --target-yyyymm 202510 \
       --periods A \
       --source step18

 - Unify both A and B for 202510 from default Step 14 enhanced outputs:
     PYTHONPATH=. python3 src/step34b_unify_outputs.py \
       --target-yyyymm 202510 \
       --periods A,B \
       --source enhanced

 Pitfalls & Best Practices
 - Do NOT pass --target-period (unsupported). Use --periods to specify A and/or B.
 - Ensure the selected source files exist for each requested half; otherwise the script will error.
 - When using manifest-based sources (step17/step18), make sure those steps have registered period outputs.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

import pandas as pd

try:
    from src.output_utils import create_output_with_symlinks
except ImportError:
    from output_utils import create_output_with_symlinks

MANIFEST_PATH = os.path.join("output", "pipeline_manifest.json")


def _load_manifest(path: str = MANIFEST_PATH) -> Dict:
    if not os.path.exists(path):
        return {"created": datetime.now(timezone.utc).isoformat(), "last_updated": datetime.now(timezone.utc).isoformat(), "steps": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_manifest(manifest: Dict, path: str = MANIFEST_PATH) -> None:
    manifest["last_updated"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def _resolve_manifest_output(manifest: Dict, step: str, period_label: str, fallback_key_prefix: str) -> Optional[str]:
    """Find file path for a period-specific output from manifest.
    - period_label like '202509A'
    - fallback_key_prefix like 'augmented_recommendations' or 'sell_through_analysis'
    """
    step_obj = manifest.get("steps", {}).get(step, {})
    outputs = step_obj.get("outputs", {})

    # Prefer exact key match e.g., augmented_recommendations_202509A
    candidate_key = f"{fallback_key_prefix}_{period_label}"
    if candidate_key in outputs and "file_path" in outputs[candidate_key]:
        return outputs[candidate_key]["file_path"]

    # Else search by metadata.target_period & target_month/year when available
    for key, val in outputs.items():
        meta = (val or {}).get("metadata", {})
        if meta.get("target_period") == period_label[-1:] and meta.get("target_year") and meta.get("target_month"):
            # Ensure year-month match period_label prefix
            yyyymm = period_label[:-1]
            year = int(yyyymm[:4])
            month = int(yyyymm[4:])
            if meta.get("target_year") == year and meta.get("target_month") == month:
                return val.get("file_path")

    # As a last resort, use generic key if exists (may not be correct period)
    if fallback_key_prefix in outputs and "file_path" in outputs[fallback_key_prefix]:
        return outputs[fallback_key_prefix]["file_path"]

    return None


def _input_paths_for_period(yyyymm: str, period: str, source: str, manifest: Dict) -> Optional[str]:
    period_label = f"{yyyymm}{period}"
    if source == "enhanced":
        return os.path.join("output", f"enhanced_fast_fish_format_{period_label}.csv")
    if source == "retagged":
        return os.path.join("output", f"enhanced_fast_fish_format_{period_label}_retagged.csv")
    if source == "for_step17":
        return os.path.join("output", f"enhanced_fast_fish_format_{period_label}_for_step17.csv")
    if source == "step17":
        return _resolve_manifest_output(manifest, "step17", period_label, "augmented_recommendations")
    if source == "step18":
        return _resolve_manifest_output(manifest, "step18", period_label, "sell_through_analysis")
    raise ValueError(f"Unknown source: {source}")


def _read_csv_with_period(path: str, period: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing input file: {path}")
    df = pd.read_csv(path)
    # Ensure Period column exists and matches
    if "Period" not in df.columns:
        df["Period"] = period
    else:
        df["Period"] = df["Period"].fillna(period)
    return df


def _write_qavalidation(unified: pd.DataFrame, out_csv: str):
    """Create a lightweight QA validation JSON next to the unified CSV.
    Returns (qa_path, qa_dict).
    """
    # Basic metrics
    row_count = int(len(unified))
    column_count = int(len(unified.columns))

    # Critical columns to check
    critical_cols = [
        "Store_Group_Name",
        "Target_Style_Tags",
        "Current_SPU_Quantity",
        "Target_SPU_Quantity",
        "Period",
    ]

    missing_counts = {c: int(unified[c].isna().sum()) for c in critical_cols if c in unified.columns}

    # Duplicate check on composite key when available
    key_cols = [c for c in ["Store_Group_Name", "Target_Style_Tags", "Period"] if c in unified.columns]
    if key_cols:
        dupes_count = int(unified.duplicated(subset=key_cols, keep=False).sum())
    else:
        dupes_count = None

    # Step 18 optimization visibility fields presence
    step18_fields = [
        "Optimization_Target",
        "Current_Sell_Through_Rate",
        "Target_Sell_Through_Rate",
        "Sell_Through_Improvement",
        "Constraint_Status",
        "Capacity_Utilization",
        "Store_Type_Alignment",
        "Temperature_Suitability",
        "Optimization_Rationale",
        "Trade_Off_Analysis",
        "Confidence_Score",
        "Inventory_Velocity_Gain",
        # common sell-through column variants
        "Sell_Through_Rate",
        "Sell_Through_Rate_Fraction",
        "Sell_Through_Rate_Percent",
        "Legacy_Sell_Through_Rate",
    ]
    present_step18_fields = [c for c in step18_fields if c in unified.columns]
    missing_step18_fields = [c for c in step18_fields if c not in unified.columns]

    qa = {
        "unified_csv": out_csv,
        "row_count": row_count,
        "column_count": column_count,
        "critical_missing_counts": missing_counts,
        "duplicate_records_on_key": dupes_count,
        "step18_fields_present_count": len(present_step18_fields),
        "step18_fields_present": present_step18_fields,
        "step18_fields_missing": missing_step18_fields,
        "created": datetime.now(timezone.utc).isoformat(),
    }

    qa_path = out_csv.replace(".csv", "_qavalidation.json")
    with open(qa_path, "w", encoding="utf-8") as f:
        json.dump(qa, f, indent=2, ensure_ascii=False)

    return qa_path, qa


def _write_runbook(yyyymm: str, periods: List[str], source: str, out_csv: str, summary: Dict, qa: Dict) -> str:
    """Write a concise runbook markdown summarizing Step 34 unification."""
    periods_str = "".join([p.upper() for p in periods])
    docs_dir = os.path.join("output", "docs")
    os.makedirs(docs_dir, exist_ok=True)
    runbook_path = os.path.join(docs_dir, f"step34_runbook_{yyyymm}{periods_str}.md")

    lines = []
    lines.append(f"# Step 34 Unification Runbook — {yyyymm}{periods_str}")
    lines.append("")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    lines.append("")
    lines.append("## Inputs")
    lines.append(f"- Source: {source}")
    lines.append(f"- Periods: {', '.join(periods)}")
    lines.append("")
    lines.append("## Outputs")
    lines.append(f"- Unified CSV: `{out_csv}`")
    lines.append(f"- Summary JSON: `{out_csv.replace('.csv', '_summary.json')}`")
    lines.append(f"- QA Validation JSON: `{out_csv.replace('.csv', '_qavalidation.json')}`")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Records: {summary.get('records')}")
    lines.append(f"- Unique Store Groups: {summary.get('unique_store_groups')}")
    lines.append(f"- Unique Target_Style_Tags Rows: {summary.get('unique_target_style_tags_rows')}")
    lines.append(f"- Columns: {summary.get('columns')}")
    lines.append("")
    lines.append("## QA Highlights")
    lines.append(f"- Duplicate records on composite key: {qa.get('duplicate_records_on_key')}")
    lines.append(f"- Missing counts (critical): {qa.get('critical_missing_counts')}")
    lines.append(f"- Step 18 fields present: {qa.get('step18_fields_present_count')} / {len(qa.get('step18_fields_present', []) + qa.get('step18_fields_missing', []))}")
    lines.append("")
    # Reference Step 35 artifacts (Step 30 summaries) if available
    lines.append("## Related Step 35 (Step 30) Artifacts")
    lines.append(f"- Target: {yyyymm}, Periods: {', '.join(periods)}")
    manifest = _load_manifest()
    step35_outputs = manifest.get("steps", {}).get("step35", {}).get("outputs", {})

    def _counts_for_path(path: Optional[str]):
        if not path:
            return None, None
        for _k, val in step35_outputs.items():
            if (val or {}).get("file_path") == path:
                meta = (val or {}).get("metadata", {})
                return meta.get("records"), meta.get("columns")
        return None, None
    for p in [pp.upper().strip() for pp in periods]:
        period_label = f"{yyyymm}{p}"
        sb_path = _resolve_manifest_output(manifest, "step35", period_label, "store_baseline")
        kpi_path = _resolve_manifest_output(manifest, "step35", period_label, "kpi_summary")
        if sb_path or kpi_path:
            if sb_path:
                sb_rec, sb_cols = _counts_for_path(sb_path)
                sb_suffix = f" (records: {sb_rec if sb_rec is not None else 'n/a'}, columns: {sb_cols if sb_cols is not None else 'n/a'})"
                lines.append(f"  - {period_label} Store Baseline CSV: `{sb_path}`{sb_suffix}")
            else:
                lines.append(f"  - {period_label} Store Baseline CSV: not found")
            if kpi_path:
                kpi_rec, kpi_cols = _counts_for_path(kpi_path)
                kpi_suffix = f" (records: {kpi_rec if kpi_rec is not None else 'n/a'}, columns: {kpi_cols if kpi_cols is not None else 'n/a'})"
                lines.append(f"  - {period_label} KPI Summary CSV: `{kpi_path}`{kpi_suffix}")
            else:
                lines.append(f"  - {period_label} KPI Summary CSV: not found")
        else:
            lines.append(f"  - {period_label}: No Step 35 outputs found")
    lines.append("")
    lines.append("This runbook is auto-generated by Step 34 for traceability and QA.")

    with open(runbook_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return runbook_path


def unify_outputs(yyyymm: str, periods: List[str], source: str = "enhanced") -> str:
    manifest = _load_manifest()

    input_paths: List[str] = []
    for p in periods:
        p = p.upper().strip()
        if p not in ("A", "B"):
            raise ValueError(f"Unsupported period: {p}")
        path = _input_paths_for_period(yyyymm, p, source, manifest)
        if not path:
            raise FileNotFoundError(f"Could not resolve input path for {yyyymm}{p} using source '{source}'.")
        input_paths.append(path)

    dataframes: List[pd.DataFrame] = []
    for path, p in zip(input_paths, periods):
        df = _read_csv_with_period(path, p.upper())
        dataframes.append(df)

    # Concatenate with union of columns
    unified = pd.concat(dataframes, axis=0, ignore_index=True, sort=False)

    # Basic normalization: if both Year/Month missing, derive from YYYYMM
    if "Year" not in unified.columns:
        unified["Year"] = int(yyyymm[:4])
    if "Month" not in unified.columns:
        unified["Month"] = int(yyyymm[4:])

    # Ensure Parsed_* columns exist and are filled for all rows using base columns if missing
    parsed_backfill_map = {
        "Parsed_Season": "Season",
        "Parsed_Gender": "Gender",
        "Parsed_Location": "Location",
        "Parsed_Category": "Category",
        "Parsed_Subcategory": "Subcategory",
    }
    for parsed_col, base_col in parsed_backfill_map.items():
        if parsed_col not in unified.columns:
            if base_col in unified.columns:
                unified[parsed_col] = unified[base_col]
            else:
                unified[parsed_col] = pd.NA
        else:
            if base_col in unified.columns:
                unified[parsed_col] = unified[parsed_col].fillna(unified[base_col])

    # Canonical column ordering: preferred order first, then any remaining columns (alphabetical for determinism)
    preferred_order = [
        "Year",
        "Month",
        "Period",
        "Store_Group_Name",
        "Target_Style_Tags",
        "Current_SPU_Quantity",
        "Target_SPU_Quantity",
        "ΔQty",
        "Data_Based_Rationale",
        "Expected_Benefit",
        "Stores_In_Group_Selling_This_Category",
        "Total_Current_Sales",
        "Avg_Sales_Per_SPU",
        "men_percentage",
        "women_percentage",
        "unisex_percentage",
        "front_store_percentage",
        "back_store_percentage",
        "summer_percentage",
        "spring_percentage",
        "autumn_percentage",
        "winter_percentage",
        "Display_Location",
        "Temp_14d_Avg",
        "Historical_ST%",
        "FeelsLike_Temp_Period_Avg",
        "Historical_Sell_Through_Rate",
        "Season",
        "Gender",
        "Location",
        "Category",
        "Subcategory",
        "Store_Codes_In_Group",
        "Store_Count_In_Group",
        # Step 18 optimization visibility fields (explicit ordering if present)
        "Optimization_Target",
        "Current_Sell_Through_Rate",
        "Target_Sell_Through_Rate",
        "Sell_Through_Improvement",
        "Constraint_Status",
        "Capacity_Utilization",
        "Store_Type_Alignment",
        "Temperature_Suitability",
        "Optimization_Rationale",
        "Trade_Off_Analysis",
        "Confidence_Score",
        "Inventory_Velocity_Gain",
        # Common sell-through variants from Step 18
        "Sell_Through_Rate",
        "Sell_Through_Rate_Fraction",
        "Sell_Through_Rate_Percent",
        "Legacy_Sell_Through_Rate",
        "Parsed_Season",
        "Parsed_Gender",
        "Parsed_Location",
        "Parsed_Category",
        "Parsed_Subcategory",
    ]
    existing_preferred = [c for c in preferred_order if c in unified.columns]
    remaining = [c for c in unified.columns if c not in existing_preferred]
    final_columns = existing_preferred + sorted(remaining)
    unified = unified.loc[:, final_columns]

    # Metadata summary
    records = len(unified)
    unique_store_groups = unified["Store_Group_Name"].nunique() if "Store_Group_Name" in unified.columns else None
    unique_target_style_tags_rows = unified["Target_Style_Tags"].nunique() if "Target_Style_Tags" in unified.columns else None

    # Output path with dual output pattern
    periods_str = "".join([p.upper() for p in periods])
    period_label = f"{yyyymm}{periods_str}"
    base_path = os.path.join("output", f"enhanced_fast_fish_format_{yyyymm}{periods_str}_unified")
    
    # Create all three outputs: timestamped, period symlink, generic symlink
    timestamped_file, period_file, generic_file = create_output_with_symlinks(
        df=unified,
        base_path=base_path,
        period_label=period_label
    )
    
    # Use timestamped file for manifest registration
    out_csv = timestamped_file
    
    # Register in manifest
    size_mb = round(os.path.getsize(out_csv) / (1024 * 1024), 2)
    step_key = "step34"
    out_key = f"unified_enhanced_fast_fish_format_{yyyymm}{periods_str}"
    manifest.setdefault("steps", {}).setdefault(step_key, {}).setdefault("outputs", {})[out_key] = {
        "file_path": out_csv.replace("\\", "/"),
        "created": datetime.now(timezone.utc).isoformat(),
        "exists": True,
        "size_mb": size_mb,
        "metadata": {
            "target_year": int(yyyymm[:4]),
            "target_month": int(yyyymm[4:]),
            "included_periods": periods,
            "source": source,
            "records": records,
            **({"unique_store_groups": unique_store_groups} if unique_store_groups is not None else {}),
            **({"unique_target_style_tags_rows": unique_target_style_tags_rows} if unique_target_style_tags_rows is not None else {}),
        },
    }

    _save_manifest(manifest)

    # Also write a small JSON summary next to CSV
    summary_path = out_csv.replace(".csv", "_summary.json")
    summary = {
        "unified_output": out_csv,
        "yyyymm": yyyymm,
        "included_periods": periods,
        "source": source,
        "records": records,
        "unique_store_groups": unique_store_groups,
        "unique_target_style_tags_rows": unique_target_style_tags_rows,
        "columns": len(unified.columns),
        "created": datetime.now(timezone.utc).isoformat(),
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Create QA validation and runbook
    qa_path, qa = _write_qavalidation(unified, out_csv)
    runbook_path = _write_runbook(yyyymm, periods, source, out_csv, summary, qa)

    # Register summary, QA, and runbook in manifest as additional outputs
    manifest_extras = _load_manifest()
    outputs = manifest_extras.setdefault("steps", {}).setdefault(step_key, {}).setdefault("outputs", {})
    now_iso = datetime.now(timezone.utc).isoformat()
    outputs[f"{out_key}_summary"] = {
        "file_path": summary_path.replace("\\", "/"),
        "created": now_iso,
        "exists": True,
        "size_mb": round(os.path.getsize(summary_path) / (1024 * 1024), 3),
        "metadata": {
            "target_year": int(yyyymm[:4]),
            "target_month": int(yyyymm[4:]),
            "included_periods": periods,
            "source": source,
            "records": records,
        },
    }
    outputs[f"{out_key}_qavalidation"] = {
        "file_path": qa_path.replace("\\", "/"),
        "created": now_iso,
        "exists": True,
        "size_mb": round(os.path.getsize(qa_path) / (1024 * 1024), 3),
        "metadata": {
            "target_year": int(yyyymm[:4]),
            "target_month": int(yyyymm[4:]),
            "included_periods": periods,
            "source": source,
            "checks": {
                "row_count": qa.get("row_count"),
                "column_count": qa.get("column_count"),
                "duplicate_records_on_key": qa.get("duplicate_records_on_key"),
                "step18_fields_present_count": qa.get("step18_fields_present_count"),
            },
        },
    }
    outputs[f"{out_key}_runbook"] = {
        "file_path": runbook_path.replace("\\", "/"),
        "created": now_iso,
        "exists": True,
        "size_mb": round(os.path.getsize(runbook_path) / (1024 * 1024), 3),
        "metadata": {
            "target_year": int(yyyymm[:4]),
            "target_month": int(yyyymm[4:]),
            "included_periods": periods,
            "source": source,
            "format": "markdown",
        },
    }
    _save_manifest(manifest_extras)

    return out_csv


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Unify period-specific outputs into a single CSV")
    parser.add_argument("--target-yyyymm", required=True, help="Target year-month, e.g., 202509")
    parser.add_argument(
        "--periods",
        default="A,B",
        help="Comma-separated periods to include (A,B). Default: A,B",
    )
    parser.add_argument(
        "--source",
        default="enhanced",
        choices=["enhanced", "retagged", "for_step17", "step17", "step18"],
        help="Which source to unify. Default: enhanced (Step 14 outputs)",
    )
    return parser.parse_args()


def main():
    args = _parse_args()
    yyyymm = args.target_yyyymm
    periods = [p.strip().upper() for p in args.periods.split(",") if p.strip()]
    out = unify_outputs(yyyymm, periods, args.source)
    print(f"Unified output written: {out}")


if __name__ == "__main__":
    main()
