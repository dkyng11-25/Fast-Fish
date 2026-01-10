#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd

try:
    from src.pipeline_manifest import get_manifest
    from src.config import get_period_label
except Exception:
    from pipeline_manifest import get_manifest
    from config import get_period_label


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")


def _latest_from_manifest(step: str, key_prefix: str, period_label: str) -> Optional[str]:
    try:
        man = get_manifest()
        return man.get_latest_output(step, key_prefix=key_prefix, period_label=period_label)
    except Exception:
        return None


def _resolve_unified(period_label: str) -> str:
    # Prefer manifest registration from step36
    path = _latest_from_manifest("step36", "unified_delivery_csv", period_label)
    if path and os.path.exists(path):
        return path
    # Fallback to most recent file pattern
    import glob
    cand = sorted(glob.glob(f"output/unified_delivery_{period_label}_*.csv"))
    if not cand:
        raise FileNotFoundError(f"Unified delivery not found for {period_label}")
    return cand[-1]


def _resolve_cluster(period_label: str) -> Optional[str]:
    path = _latest_from_manifest("step36", "unified_delivery_cluster_csv", period_label)
    if path and os.path.exists(path):
        return path
    import glob
    cand = sorted(glob.glob(f"output/unified_delivery_cluster_level_{period_label}_*.csv"))
    return cand[-1] if cand else None


def _format_store_sheet(df: pd.DataFrame) -> pd.DataFrame:
    # Drop low-utility/internal columns for customer-facing view
    drop_cols = [
        "Allocated_ΔQty","Group_ΔQty","Group_ΔQty_source",
        "Target_ST_source","Current_ST_source","Improvement_source",
        "Target_ST_cap_percentile","Target_ST_cap_value","Target_ST_capped_flag",
        "Season_source","Gender_source","Location_source",
        "Historical_Temp_C_Mean","Historical_Temp_C_P5","Historical_Temp_C_P95",
        "Historical_Temp_Band_Detailed","Historical_Temp_Quintile","Temp_Band_Divergence",
        "Data_Based_Rationale","Action_Order","Priority_Score",  # keep Action_Priority_Rank only
    ]
    keep_df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore").copy()

    # Group related columns together for readability
    preferred = [
        # Identification
        "Analysis_Year","Analysis_Month","Analysis_Period","Planning_Season","Planning_Year","Planning_Period_Label",
        # Store/cluster
        "Store_Code","Store_Group_Name","Cluster_ID","Cluster_Name",
        # Action & instruction
        "Action","Allocated_ΔQty_Rounded","Target_SPU_Quantity","Action_Priority_Rank","Instruction",
        # Product attributes
        "Category","Category_Display","Subcategory","Gender","Season","Location",
        # Tags
        "Target_Style_Tags","Tag_Bundle",
        # Performance (sell-through & benefit)
        "Expected_Benefit","Confidence_Score","Current_Sell_Through_Rate","Target_Sell_Through_Rate","Sell_Through_Improvement",
        # Capacity & constraints
        "Capacity_Utilization","Constraint_Status",
        # Climate
        "Store_Temperature_Band","Temperature_Band_Simple","Temperature_Band_Detailed","Temperature_Zone","Temperature_Value_C","Cluster_Temp_C_Mean","Cluster_Temp_Quintile","Temperature_Suitability_Graded",
        # Fashion & operations
        "Store_Fashion_Profile","Cluster_Fashion_Profile","Operational_Tag",
    ]
    cols = [c for c in preferred if c in keep_df.columns] + [c for c in keep_df.columns if c not in preferred]
    out = keep_df.loc[:, cols].copy()

    # Basic sanitization
    if "Allocated_ΔQty_Rounded" in out.columns:
        out["Allocated_ΔQty_Rounded"] = pd.to_numeric(out["Allocated_ΔQty_Rounded"], errors="coerce").fillna(0).astype(int)
    if "Target_SPU_Quantity" in out.columns:
        out["Target_SPU_Quantity"] = pd.to_numeric(out["Target_SPU_Quantity"], errors="coerce").fillna(0).astype(int)

    # Priority sort: Adds first, then priority rank, then quantity desc
    if "Action" in out.columns:
        order_map = {"Add": 0, "Reduce": 1, "No-Change": 2}
        out["__A__"] = out["Action"].map(order_map).fillna(3)
    else:
        out["__A__"] = 3
    if "Action_Priority_Rank" in out.columns:
        out = out.sort_values(["__A__","Action_Priority_Rank","Allocated_ΔQty_Rounded"], ascending=[True, True, False], kind="mergesort")
    else:
        out = out.sort_values(["__A__","Allocated_ΔQty_Rounded"], ascending=[True, False], kind="mergesort")
    out = out.drop(columns=[c for c in ["__A__"] if c in out.columns])
    return out


def _pants_mask(df: pd.DataFrame) -> pd.Series:
    pats = ["裤","牛仔裤","休闲裤","直筒裤","阔腿裤","短裤","中裤","束脚裤","锥形裤","工装裤","喇叭裤","烟管裤","pant","pants","trouser","trousers"]
    mask = pd.Series(False, index=df.index)
    for c in ["Category","Subcategory","Target_Style_Tags","Category_Display"]:
        if c in df.columns:
            s = df[c].astype(str).str.lower()
            for kw in pats:
                mask |= s.str.contains(kw.lower(), na=False)
    return mask


def _women_mask(df: pd.DataFrame) -> pd.Series:
    m = pd.Series(False, index=df.index)
    if "Gender" in df.columns:
        m = m | df["Gender"].astype(str).str.contains("women|女|女士|女装|女款", case=False, na=False)
    if "Target_Style_Tags" in df.columns:
        m = m | df["Target_Style_Tags"].astype(str).str.contains("女|women|女士|女装|女款", case=False, na=False)
    return m


def _build_overview(df: pd.DataFrame) -> pd.DataFrame:
    total = len(df)
    adds = int((df.get("Action") == "Add").sum()) if "Action" in df.columns else 0
    reduces = int((df.get("Action") == "Reduce").sum()) if "Action" in df.columns else 0
    pants = _pants_mask(df)
    women = _women_mask(df)
    pants_rows = int(pants.sum())
    women_pants_rows = int((pants & women).sum())
    women_share = round(100 * women_pants_rows / max(1, pants_rows), 2)
    nulls = {k: int(df[k].isna().sum()) for k in [c for c in ["Season","Gender","Location"] if c in df.columns]}
    rows = [
        {"Metric": "Total Rows", "Value": total},
        {"Metric": "Adds", "Value": adds},
        {"Metric": "Reduces", "Value": reduces},
        {"Metric": "Pants Rows", "Value": pants_rows},
        {"Metric": "Women Pants Rows", "Value": women_pants_rows},
        {"Metric": "Women Pants Share %", "Value": women_share},
    ]
    for k, v in nulls.items():
        rows.append({"Metric": f"Nulls {k}", "Value": v})
    return pd.DataFrame(rows)


def _top_adds_by_cluster(df: pd.DataFrame) -> pd.DataFrame:
    if not all(c in df.columns for c in ["Cluster_ID","Action","Allocated_ΔQty_Rounded","Category","Subcategory"]):
        return pd.DataFrame()
    adds = df[df["Action"] == "Add"].copy()
    adds["Allocated_ΔQty_Rounded"] = pd.to_numeric(adds["Allocated_ΔQty_Rounded"], errors="coerce").fillna(0).astype(int)
    adds = adds.sort_values(["Cluster_ID","Allocated_ΔQty_Rounded"], ascending=[True, False])
    # Keep top N per cluster (e.g., 20)
    adds["rank"] = adds.groupby("Cluster_ID")["Allocated_ΔQty_Rounded"].rank(ascending=False, method="first")
    adds = adds[adds["rank"] <= 20]
    return adds.drop(columns=["rank"]) if "rank" in adds.columns else adds


def _cluster_summary(cluster_path: Optional[str]) -> pd.DataFrame:
    if not cluster_path or not os.path.exists(cluster_path):
        return pd.DataFrame()
    try:
        cl = pd.read_csv(cluster_path)
        keep = [c for c in [
            "Cluster_ID","Cluster_Name","Operational_Tag","Temperature_Zone",
            "Allocated_ΔQty_Rounded","Allocated_ΔQty","Group_ΔQty",
            "Capacity_Utilization","Cluster_Fashion_Profile","Cluster_Fashion_Ratio"
        ] if c in cl.columns]
        return cl[keep].copy()
    except Exception:
        return pd.DataFrame()


def build_customer_delivery(yyyymm: str, period: str) -> str:
    period_label = get_period_label(yyyymm, period)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    unified_path = _resolve_unified(period_label)
    cluster_path = _resolve_cluster(period_label)
    log(f"✓ Using unified: {unified_path}")
    if cluster_path:
        log(f"✓ Using cluster-level: {cluster_path}")

    df = pd.read_csv(unified_path)
    store = _format_store_sheet(df)
    overview = _build_overview(store)
    cluster_top_adds = _top_adds_by_cluster(store)
    cluster_summary = _cluster_summary(cluster_path)

    # Focus sheet: Women Casual Pants
    pants = _pants_mask(store)
    women = _women_mask(store)
    focus_women_pants = store[pants & women].copy()
    focus_women_pants = focus_women_pants.sort_values(["Allocated_ΔQty_Rounded"], ascending=[False])

    # Output paths
    base = f"output/customer_delivery_{period_label}_{ts}"
    xlsx = base + ".xlsx"
    csv_main = base + "_store_lines.csv"
    os.makedirs("output", exist_ok=True)

    # Write Excel package
    try:
        import openpyxl  # noqa: F401
        with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
            overview.to_excel(writer, index=False, sheet_name="Overview")
            if not cluster_summary.empty:
                cluster_summary.to_excel(writer, index=False, sheet_name="Cluster Summary")
            if not cluster_top_adds.empty:
                cluster_top_adds.to_excel(writer, index=False, sheet_name="Top Adds by Cluster")
            focus_women_pants.to_excel(writer, index=False, sheet_name="Women Casual Pants")
            store.to_excel(writer, index=False, sheet_name="Store Lines")
        log(f"✅ Wrote Excel package: {xlsx}")
    except Exception as e:
        log(f"⚠️ Excel package not written ({e}); CSVs will be provided")

    # Always write main store-lines CSV
    store.to_csv(csv_main, index=False)
    log(f"✅ Wrote store lines CSV: {csv_main} [{len(store):,} rows]")

    return xlsx if os.path.exists(xlsx) else csv_main


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Step 37: Customer Delivery Formatter")
    p.add_argument("--target-yyyymm", required=True, help="Target year-month, e.g., 202509")
    p.add_argument("--target-period", required=True, choices=["A","B"], help="Target period (A/B)")
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    yyyymm = args.target_yyyymm
    period = args.target_period.upper()
    log(f"🚀 Step 37 Customer Delivery Formatter for {get_period_label(yyyymm, period)}")
    out = build_customer_delivery(yyyymm, period)
    log(f"📦 Output: {out}")
    log("✅ Step 37 completed")


if __name__ == "__main__":
    main()


