#!/usr/bin/env python3
"""
Export canonical JSON views from Step 36 unified delivery output without modifying the pipeline.

- Store-Tag canonical view (unique on Store_Code, Store_Group_Name, Target_Style_Tags)
- Cluster summary view (aggregated by Cluster_ID)

This matches the simple JSON inputs used by the proven fixed dashboard generator pattern
(fixed_stores_data.json, fixed_clusters_data.json).

Usage examples:
  python3 scripts/export_step36_canonical_views.py --period-label 202509B
  python3 scripts/export_step36_canonical_views.py --input output/unified_delivery_202509B_20250829_083824.csv --period-label 202509B

Outputs:
  output/fixed_stores_data.json
  output/fixed_clusters_data.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from typing import Dict, List, Optional

import pandas as pd


DUP_KEYS = ["Store_Code", "Store_Group_Name", "Target_Style_Tags"]


def _get_manifest_resolver():
    try:
        from src.pipeline_manifest import get_manifest  # type: ignore
        return get_manifest
    except Exception:
        try:
            from pipeline_manifest import get_manifest  # type: ignore
            return get_manifest
        except Exception:
            return None


def _resolve_unified_csv(period_label: str) -> Optional[str]:
    get_manifest = _get_manifest_resolver()
    if get_manifest:
        try:
            man = get_manifest()
            path = man.get_latest_output("step36", key_prefix="unified_delivery_csv", period_label=period_label)
            if path and os.path.exists(path):
                return path
        except Exception:
            pass
    candidates = sorted(glob.glob(f"output/unified_delivery_{period_label}_*.csv"))
    return candidates[-1] if candidates else None


def _numeric(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _first_nonnull(df: pd.DataFrame, cols: List[str], default=None):
    for c in cols:
        if c in df.columns:
            v = df[c].dropna()
            if not v.empty:
                return v.iloc[0]
    return default


def build_store_view(df: pd.DataFrame) -> pd.DataFrame:
    # Ensure keys are strings
    for k in DUP_KEYS:
        if k in df.columns:
            df[k] = df[k].astype(str)

    # Select useful columns (if present)
    keep = [c for c in [
        # keys
        "Store_Code", "Store_Group_Name", "Target_Style_Tags",
        # period fields
        "Analysis_Year", "Analysis_Month", "Analysis_Period", "Planning_Season", "Planning_Year", "Planning_Period_Label",
        # dimensions
        "Season", "Gender", "Location", "Cluster_ID", "Cluster_Name", "Operational_Tag_Label", "Temperature_Zone_Label",
        # metrics
        "Allocated_ΔQty_Rounded", "Group_ΔQty", "Expected_Benefit", "Sell_Through_Improvement",
        "Capacity_Utilization", "Priority_Score", "Coverage_Index", "Priority_Index"
    ] if c in df.columns]
    base = df[keep].copy()

    # Coerce numerics
    for col in ["Allocated_ΔQty_Rounded", "Group_ΔQty", "Expected_Benefit", "Sell_Through_Improvement", "Capacity_Utilization", "Priority_Score", "Coverage_Index", "Priority_Index"]:
        if col in base.columns:
            base[col] = _numeric(base[col])

    agg_map: Dict[str, str] = {}
    for col in ["Allocated_ΔQty_Rounded", "Group_ΔQty", "Expected_Benefit", "Sell_Through_Improvement", "Capacity_Utilization", "Priority_Score", "Coverage_Index", "Priority_Index"]:
        if col in base.columns:
            agg_map[col] = "sum"  # aggregate across category/subcategory lines

    # First for dims and period fields (if present)
    for col in [
        "Analysis_Year", "Analysis_Month", "Analysis_Period", "Planning_Season", "Planning_Year", "Planning_Period_Label",
        "Season", "Gender", "Location", "Cluster_ID", "Cluster_Name", "Operational_Tag_Label", "Temperature_Zone_Label",
    ]:
        if col in base.columns:
            agg_map[col] = "first"

    grp = base.groupby(DUP_KEYS, dropna=False).agg(agg_map).reset_index()

    # Sanity: ensure integer for rounded qty after aggregation
    if "Allocated_ΔQty_Rounded" in grp.columns:
        grp["Allocated_ΔQty_Rounded"] = grp["Allocated_ΔQty_Rounded"].round().astype("Int64")

    return grp


def build_cluster_view(df: pd.DataFrame) -> pd.DataFrame:
    keep = [c for c in [
        "Cluster_ID", "Cluster_Name", "Operational_Tag_Label", "Temperature_Zone_Label",
        "Store_Code", "Allocated_ΔQty_Rounded", "Group_ΔQty",
        "Cluster_Fashion_Profile", "Cluster_Fashion_Ratio", "cold_share", "warm_share", "moderate_share",
    ] if c in df.columns]
    base = df[keep].copy()

    if "Allocated_ΔQty_Rounded" in base.columns:
        base["Allocated_ΔQty_Rounded"] = _numeric(base["Allocated_ΔQty_Rounded"]).round()
    if "Group_ΔQty" in base.columns:
        base["Group_ΔQty"] = _numeric(base["Group_ΔQty"]) 

    # Cluster_ID may be missing on some rows; dropna for cluster grouping stability
    if "Cluster_ID" not in base.columns:
        # create a placeholder cluster to avoid empty group
        base["Cluster_ID"] = "unknown"

    # counts and sums
    agg = {
        "Allocated_ΔQty_Rounded": "sum",
        "Group_ΔQty": "sum",
    }
    if "Store_Code" in base.columns:
        # unique stores contributing
        base["__store_key__"] = base["Store_Code"].astype(str)
        agg["__store_key__"] = lambda s: len(set(s.dropna().astype(str)))

    # Add 'first' for labels if present
    for col in ["Cluster_Name", "Operational_Tag_Label", "Temperature_Zone_Label", "Cluster_Fashion_Profile", "Cluster_Fashion_Ratio", "cold_share", "warm_share", "moderate_share"]:
        if col in base.columns:
            agg[col] = "first"

    cluster = base.groupby(["Cluster_ID"], dropna=False).agg(agg).reset_index()
    if "__store_key__" in cluster.columns:
        cluster = cluster.rename(columns={"__store_key__": "Store_Count"})

    # Ensure integer rounded qty
    if "Allocated_ΔQty_Rounded" in cluster.columns:
        cluster["Allocated_ΔQty_Rounded"] = cluster["Allocated_ΔQty_Rounded"].round().astype("Int64")

    return cluster


def save_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def main() -> int:
    ap = argparse.ArgumentParser(description="Export canonical JSON views from Step36 unified delivery")
    ap.add_argument("--input", help="Path to unified_delivery CSV; if omitted, resolved from manifest by period label")
    ap.add_argument("--period-label", required=True, help="Period label e.g. 202509B")
    ap.add_argument("--out-dir", default="output", help="Output directory for JSON files")
    ap.add_argument("--stores-json", default="fixed_stores_data.json")
    ap.add_argument("--clusters-json", default="fixed_clusters_data.json")
    args = ap.parse_args()

    csv_path = args.input or _resolve_unified_csv(args.period_label)
    if not csv_path or not os.path.exists(csv_path):
        print(json.dumps({"error": "Unified CSV not found", "period_label": args.period_label}))
        return 2

    # Load CSV — only necessary columns to reduce memory
    necessary = list(set(DUP_KEYS + [
        # dims/period fields
        "Analysis_Year", "Analysis_Month", "Analysis_Period", "Planning_Season", "Planning_Year", "Planning_Period_Label",
        "Season", "Gender", "Location", "Cluster_ID", "Cluster_Name", "Operational_Tag_Label", "Temperature_Zone_Label",
        # metrics
        "Allocated_ΔQty_Rounded", "Group_ΔQty", "Expected_Benefit", "Sell_Through_Improvement",
        "Capacity_Utilization", "Priority_Score", "Coverage_Index", "Priority_Index",
        # optional cluster meta
        "Cluster_Fashion_Profile", "Cluster_Fashion_Ratio", "cold_share", "warm_share", "moderate_share",
    ]))

    try:
        df_head = pd.read_csv(csv_path, nrows=0)
        cols = [c for c in necessary if c in df_head.columns]
    except Exception:
        cols = None  # fallback to reading full CSV

    df = pd.read_csv(csv_path, usecols=cols, low_memory=False) if cols else pd.read_csv(csv_path, low_memory=False)

    store_view = build_store_view(df)
    cluster_view = build_cluster_view(df)

    # Validate uniqueness on store view
    if all(k in store_view.columns for k in DUP_KEYS):
        dup = store_view.duplicated(subset=DUP_KEYS, keep=False).sum()
        if dup > 0:
            print(json.dumps({"error": "Store view not unique on store-line key", "duplicates": int(dup)}))
            return 2

    out_stores = os.path.join(args.out_dir, args.stores_json)
    out_clusters = os.path.join(args.out_dir, args.clusters_json)

    save_json(out_stores, store_view.to_dict(orient="records"))
    save_json(out_clusters, cluster_view.to_dict(orient="records"))

    summary = {
        "period_label": args.period_label,
        "input_csv": csv_path,
        "outputs": {"stores_json": out_stores, "clusters_json": out_clusters},
        "counts": {"store_rows": int(len(store_view)), "cluster_rows": int(len(cluster_view))},
        "totals": {
            "allocated_sum_csv": float(pd.to_numeric(df.get("Allocated_ΔQty_Rounded"), errors="coerce").sum()) if "Allocated_ΔQty_Rounded" in df.columns else None,
            "allocated_sum_stores": float(pd.to_numeric(store_view.get("Allocated_ΔQty_Rounded"), errors="coerce").sum()) if "Allocated_ΔQty_Rounded" in store_view.columns else None,
            "allocated_sum_clusters": float(pd.to_numeric(cluster_view.get("Allocated_ΔQty_Rounded"), errors="coerce").sum()) if "Allocated_ΔQty_Rounded" in cluster_view.columns else None,
        },
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
