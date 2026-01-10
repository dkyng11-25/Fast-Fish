#!/usr/bin/env python3
"""
QA validator for Step 34 unified outputs.

Checks performed:
- Row count equals sum of source period files (A + B)
- Period distribution matches source period row counts and contains only allowed periods
- Duplicates within each period on key ['Store_Group_Name','Target_Style_Tags']
- Column differences between A and B (reported as warnings)
- NaN distribution by period for asymmetric columns
- Year/Month consistency with target YYYYMM (when columns exist)
- Optional comparison with manifest's recorded records

Outputs a JSON report next to the unified CSV and returns non-zero on critical failures.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Tuple

import pandas as pd

MANIFEST_PATH = os.path.join("output", "pipeline_manifest.json")


def _load_manifest(path: str = MANIFEST_PATH) -> Dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_manifest_output(manifest: Dict, step: str, period_label: str, fallback_key_prefix: str) -> Optional[str]:
    step_obj = manifest.get("steps", {}).get(step, {})
    outputs = step_obj.get("outputs", {})

    candidate_key = f"{fallback_key_prefix}_{period_label}"
    if candidate_key in outputs and "file_path" in outputs[candidate_key]:
        return outputs[candidate_key]["file_path"]

    for _, val in outputs.items():
        meta = (val or {}).get("metadata", {})
        if meta.get("target_period") == period_label[-1:] and meta.get("target_year") and meta.get("target_month"):
            yyyymm = period_label[:-1]
            try:
                year = int(yyyymm[:4])
                month = int(yyyymm[4:])
            except Exception:
                continue
            if meta.get("target_year") == year and meta.get("target_month") == month:
                return val.get("file_path")

    if fallback_key_prefix in outputs and "file_path" in outputs[fallback_key_prefix]:
        return outputs[fallback_key_prefix]["file_path"]
    return None


def _input_path_for_period(yyyymm: str, period: str, source: str, manifest: Dict) -> Optional[str]:
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


def _read_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing input file: {path}")
    return pd.read_csv(path)


def _build_unified_default_path(yyyymm: str, periods: List[str]) -> str:
    periods_str = "".join([p.upper() for p in periods])
    return os.path.join("output", f"enhanced_fast_fish_format_{yyyymm}{periods_str}_unified.csv")


def _validate(
    yyyymm: str,
    periods: List[str],
    source: str,
    unified_csv: str,
    manifest: Dict,
) -> Tuple[Dict, bool]:
    report: Dict = {
        "target_yyyymm": yyyymm,
        "periods": periods,
        "source": source,
        "unified_csv": unified_csv,
        "checks": {},
        "warnings": [],
        "errors": [],
    }

    # Load sources
    period_dfs: Dict[str, pd.DataFrame] = {}
    for p in periods:
        p = p.upper()
        in_path = _input_path_for_period(yyyymm, p, source, manifest)
        if not in_path:
            report["errors"].append(f"Could not resolve source path for {yyyymm}{p} (source={source})")
            return report, False
        try:
            period_dfs[p] = _read_csv(in_path)
        except Exception as e:
            report["errors"].append(f"Failed reading {in_path}: {e}")
            return report, False

    # Load unified
    if not os.path.exists(unified_csv):
        report["errors"].append(f"Unified CSV not found: {unified_csv}")
        return report, False
    unified = _read_csv(unified_csv)

    # Check 1: row count equals sum
    src_rows = {p: len(df) for p, df in period_dfs.items()}
    unified_rows = len(unified)
    sum_src_rows = sum(src_rows.values())
    report["checks"]["row_counts"] = {
        "source_rows": src_rows,
        "unified_rows": unified_rows,
        "sum_source_rows": sum_src_rows,
        "match": unified_rows == sum_src_rows,
    }

    # Check 2: period distribution
    period_counts = (
        unified["Period"].astype(str).str.upper().value_counts().to_dict()
        if "Period" in unified.columns
        else {}
    )
    extra_periods = [k for k in period_counts.keys() if k not in periods]
    period_match = all(period_counts.get(p, 0) == src_rows.get(p, -1) for p in periods) and not extra_periods
    report["checks"]["period_distribution"] = {
        "period_counts": period_counts,
        "expected": src_rows,
        "extra_periods": extra_periods,
        "match": period_match,
    }

    # Check 3: duplicates within each period on keys
    dup_keys = [c for c in ["Store_Group_Name", "Target_Style_Tags"] if c in unified.columns]
    dup_result: Dict[str, Dict] = {}
    dup_fail = False
    if len(dup_keys) == 2 and "Period" in unified.columns:
        for p in periods:
            part = unified[unified["Period"].astype(str).str.upper() == p]
            dups_mask = part.duplicated(subset=dup_keys, keep=False)
            dup_count = int(dups_mask.sum())
            dup_rows_sample = part.loc[dups_mask, dup_keys].drop_duplicates().head(10).to_dict(orient="records")
            dup_result[p] = {
                "duplicate_rows": dup_count,
                "sample": dup_rows_sample,
            }
            if dup_count > 0:
                dup_fail = True
    else:
        report["warnings"].append(
            "Duplicate check skipped: required columns missing (Need Period, Store_Group_Name, Target_Style_Tags)."
        )
    report["checks"]["duplicates_within_period"] = dup_result

    # Check 4: column differences between A and B and NaN distribution by period for asymmetric columns
    if len(periods) == 2 and all(p in period_dfs for p in periods):
        cols_a = set(period_dfs[periods[0]].columns)
        cols_b = set(period_dfs[periods[1]].columns)
        a_only = sorted(list(cols_a - cols_b))
        b_only = sorted(list(cols_b - cols_a))
        report["checks"]["column_differences"] = {
            f"{periods[0]}_only": a_only,
            f"{periods[1]}_only": b_only,
        }
        # NaN distribution for asymmetric columns
        nan_stats: Dict[str, Dict[str, int]] = {}
        if "Period" in unified.columns:
            for col in a_only + b_only:
                if col in unified.columns:
                    counts = (
                        unified.groupby(unified["Period"].astype(str).str.upper())[col]
                        .apply(lambda s: int(s.isna().sum()))
                        .to_dict()
                    )
                    nan_stats[col] = counts
        report["checks"]["nan_by_period_for_asymmetric_columns"] = nan_stats
        if a_only or b_only:
            report["warnings"].append(
                f"Asymmetric columns detected: {periods[0]} only={a_only} | {periods[1]} only={b_only}"
            )
    else:
        report["warnings"].append("Column difference check skipped: expected two periods")

    # Check 5: Year/Month consistency
    ym_ok = True
    ym_issues: List[str] = []
    try:
        year = int(yyyymm[:4])
        month = int(yyyymm[4:])
    except Exception:
        year = month = None
    if year is not None and "Year" in unified.columns:
        bad_year = int((unified["Year"] != year).sum())
        if bad_year > 0:
            ym_ok = False
            ym_issues.append(f"Year mismatches: {bad_year}")
    if month is not None and "Month" in unified.columns:
        bad_month = int((unified["Month"] != month).sum())
        if bad_month > 0:
            ym_ok = False
            ym_issues.append(f"Month mismatches: {bad_month}")
    report["checks"]["year_month_consistency"] = {
        "target_year": year,
        "target_month": month,
        "ok": ym_ok,
        "issues": ym_issues,
    }

    # Compare manifest (if present)
    step34_meta = (
        manifest.get("steps", {})
        .get("step34", {})
        .get("outputs", {})
    )
    manifest_records = None
    for k, v in step34_meta.items():
        if isinstance(v, dict) and v.get("file_path") == unified_csv:
            manifest_records = (v.get("metadata") or {}).get("records")
            break
    if manifest_records is not None:
        report["checks"]["manifest_records_match"] = {
            "manifest_records": manifest_records,
            "unified_rows": unified_rows,
            "match": int(manifest_records) == int(unified_rows),
        }

    # Determine pass/fail
    critical_fail = False
    if not report["checks"]["row_counts"]["match"]:
        critical_fail = True
        report["errors"].append("Row count mismatch between unified and sources.")
    if not report["checks"]["period_distribution"]["match"]:
        critical_fail = True
        report["errors"].append("Period distribution mismatch or unexpected Period values.")
    if dup_fail:
        critical_fail = True
        report["errors"].append("Duplicates detected within period on (Store_Group_Name, Target_Style_Tags).")
    if not report["checks"]["year_month_consistency"]["ok"]:
        critical_fail = True
        report["errors"].append("Year/Month mismatch with target YYYYMM.")

    return report, (not critical_fail)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Step 34 unified CSV integrity")
    p.add_argument("--target-yyyymm", required=True, help="Target YYYYMM, e.g., 202509")
    p.add_argument("--periods", default="A,B", help="Comma-separated periods, e.g., A,B")
    p.add_argument(
        "--source",
        default="enhanced",
        choices=["enhanced", "retagged", "for_step17", "step17", "step18"],
        help="Source used to build unified CSV",
    )
    p.add_argument("--manifest", default=MANIFEST_PATH, help="Path to pipeline_manifest.json")
    p.add_argument(
        "--unified-file",
        default=None,
        help="Override unified CSV path; default is derived from target and periods",
    )
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    periods = [p.strip().upper() for p in args.periods.split(",") if p.strip()]
    manifest = _load_manifest(args.manifest)

    unified_csv = args.unified_file or _build_unified_default_path(args.target_yyyymm, periods)

    report, ok = _validate(args.target_yyyymm, periods, args.source, unified_csv, manifest)

    # Write report JSON next to unified CSV
    out_report = unified_csv.replace(".csv", "_qavalidation.json")
    try:
        os.makedirs(os.path.dirname(out_report), exist_ok=True)
        with open(out_report, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"QA report written: {out_report}")
    except Exception as e:
        print(f"Failed writing QA report: {e}")

    # Print concise summary
    print(json.dumps({
        "unified_csv": unified_csv,
        "row_counts": report.get("checks", {}).get("row_counts", {}),
        "period_distribution": report.get("checks", {}).get("period_distribution", {}),
        "duplicates_within_period": report.get("checks", {}).get("duplicates_within_period", {}),
        "year_month_consistency": report.get("checks", {}).get("year_month_consistency", {}),
        "warnings": report.get("warnings", []),
        "errors": report.get("errors", []),
    }, ensure_ascii=False))

    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
