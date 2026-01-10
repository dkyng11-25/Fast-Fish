#!/usr/bin/env python3
"""
Export column-by-column inventory for Step 36 unified delivery outputs.

Generates, per period:
- CSV: detailed inventory with dtype, nulls, uniques, sample values, numeric min/max
- Markdown: readable summary table
"""
from __future__ import annotations

import argparse
import glob
import os
from typing import Dict, List, Optional

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


def _profile_columns(df: pd.DataFrame, sample_values: int = 5) -> pd.DataFrame:
    records: List[Dict] = []
    n = len(df)
    for col in df.columns:
        s = df[col]
        dtype = str(s.dtype)
        nn = int(s.notna().sum())
        na = int(n - nn)
        uniq = int(s.nunique(dropna=True))
        # sample values
        try:
            samples = [str(v) for v in s.dropna().astype(str).unique()[:sample_values]]
        except Exception:
            samples = []
        # numeric min/max
        numeric_min = None
        numeric_max = None
        if dtype.startswith("int") or dtype.startswith("float"):
            try:
                numeric_min = float(pd.to_numeric(s, errors="coerce").min())
                numeric_max = float(pd.to_numeric(s, errors="coerce").max())
            except Exception:
                numeric_min = None
                numeric_max = None
        records.append({
            "column": col,
            "dtype": dtype,
            "non_null_count": nn,
            "null_count": na,
            "pct_null": round(na / n, 6) if n else 0.0,
            "unique_count": uniq,
            "sample_values": ", ".join(samples),
            "numeric_min": numeric_min,
            "numeric_max": numeric_max,
        })
    inv = pd.DataFrame.from_records(records)
    inv = inv.sort_values(by=["column"]).reset_index(drop=True)
    return inv


def _write_markdown(inv: pd.DataFrame, md_path: str) -> None:
    lines: List[str] = []
    lines.append(f"# Column Inventory\n")
    lines.append("| Column | Dtype | Non-Null | Null | % Null | Unique | Numeric Min | Numeric Max | Sample Values |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for _, r in inv.iterrows():
        lines.append(
            f"| {r['column']} | {r['dtype']} | {r['non_null_count']} | {r['null_count']} | {r['pct_null']:.4f} | {r['unique_count']} | "
            f"{'' if pd.isna(r['numeric_min']) else r['numeric_min']} | {'' if pd.isna(r['numeric_max']) else r['numeric_max']} | {r['sample_values']} |"
        )
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Export Step 36 unified output column inventory")
    p.add_argument("--target-yyyymm", required=True)
    p.add_argument("--periods", default="A,B")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    periods = [p.strip().upper() for p in args.periods.split(",") if p.strip()]
    os.makedirs("output", exist_ok=True)

    for p in periods:
        pl = get_period_label(args.target_yyyymm, p)
        csv_path = _resolve_unified_csv(pl)
        if not csv_path:
            print(f"[WARN] Unified CSV not found for {pl}")
            continue
        df = pd.read_csv(csv_path)
        inv = _profile_columns(df)
        inv_csv = csv_path.replace(".csv", "_inventory.csv")
        inv_md = csv_path.replace(".csv", "_inventory.md")
        inv.to_csv(inv_csv, index=False)
        _write_markdown(inv, inv_md)
        print(f"Inventory written: {inv_csv} and {inv_md}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


