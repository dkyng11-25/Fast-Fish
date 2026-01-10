#!/usr/bin/env python3
"""
Tests for scripts/export_step36_canonical_views.py without modifying pipeline code.

Checks:
- Uniqueness on (Store_Code, Store_Group_Name, Target_Style_Tags) after aggregation
- Sum reconciliation for Allocated_ΔQty_Rounded (raw vs aggregated store view)
- Basic cluster view sanity (non-empty when Cluster_ID present, sum consistency)

Run:
  python test_export_step36_canonical_views.py
Optionally set environment for period:
  export PIPELINE_TARGET_YYYYMM=202509; export PIPELINE_TARGET_PERIOD=B
"""
import os
import sys
import glob

# Ensure project root and subdirs are importable
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.append(os.path.join(project_root, "src"))
sys.path.append(os.path.join(project_root, "scripts"))

import pandas as pd

from src.config import get_period_label
from src.pipeline_manifest import get_manifest

from scripts.export_step36_canonical_views import build_store_view, build_cluster_view


DUP_KEYS = ["Store_Code", "Store_Group_Name", "Target_Style_Tags"]


def _resolve_unified_csv(period_label: str) -> str:
    man = get_manifest()
    path = None
    try:
        path = man.get_latest_output("step36", key_prefix="unified_delivery_csv", period_label=period_label)
    except Exception:
        path = None
    if path and os.path.exists(path):
        return path
    cands = sorted(glob.glob(os.path.join("output", f"unified_delivery_{period_label}_*.csv")))
    if not cands:
        raise FileNotFoundError(f"Unified delivery CSV not found for {period_label}")
    return cands[-1]


def _has_columns(df: pd.DataFrame, cols) -> bool:
    return all(c in df.columns for c in cols)


def main() -> int:
    yyyymm = os.environ.get("PIPELINE_TARGET_YYYYMM", "202509")
    period = os.environ.get("PIPELINE_TARGET_PERIOD", "B")
    period_label = get_period_label(yyyymm, period)

    csv_path = _resolve_unified_csv(period_label)
    print(f"[TEST] Using CSV: {csv_path}")

    # Load a minimal set of columns required for tests; let builder handle missing dims
    base_cols = list(set(DUP_KEYS + [
        "Allocated_ΔQty_Rounded", "Group_ΔQty", "Cluster_ID", "Cluster_Name"
    ]))

    try:
        head = pd.read_csv(csv_path, nrows=0)
        usecols = [c for c in base_cols if c in head.columns]
    except Exception:
        usecols = None

    df = pd.read_csv(csv_path, usecols=usecols) if usecols else pd.read_csv(csv_path)

    # Preconditions
    assert _has_columns(df, ["Allocated_ΔQty_Rounded"]) , "Allocated_ΔQty_Rounded missing in unified delivery"
    assert _has_columns(df, ["Store_Code", "Store_Group_Name", "Target_Style_Tags"]), "Store-line key columns missing"

    # Check raw duplicates on store-line key (informational)
    raw_dups = int(df.duplicated(subset=DUP_KEYS, keep=False).sum())
    print(f"[TEST] Raw duplicate rows on store-line key: {raw_dups}")

    # Build aggregated views
    store_view = build_store_view(df)
    cluster_view = build_cluster_view(df)

    # 1) Uniqueness on store-line key
    if not _has_columns(store_view, DUP_KEYS):
        raise AssertionError("Store view is missing store-line key columns")
    store_dups = int(store_view.duplicated(subset=DUP_KEYS, keep=False).sum())
    assert store_dups == 0, f"Store view contains duplicates on {DUP_KEYS}: {store_dups} rows"
    print(f"[TEST] Store view unique rows: {len(store_view)} (no duplicates)")

    # 2) Sum reconciliation
    raw_sum = pd.to_numeric(df["Allocated_ΔQty_Rounded"], errors="coerce").sum()
    agg_sum = pd.to_numeric(store_view["Allocated_ΔQty_Rounded"], errors="coerce").sum()
    assert pd.isna(raw_sum) is False and pd.isna(agg_sum) is False, "Sums should be numeric"
    # exact equality expected for integer rounded totals
    assert int(round(raw_sum)) == int(round(agg_sum)), f"Sum mismatch: raw={raw_sum} agg={agg_sum}"
    print(f"[TEST] Sum reconciliation OK: total {int(round(agg_sum))}")

    # 3) Cluster view sanity
    if "Cluster_ID" in df.columns and df["Cluster_ID"].notna().any():
        assert len(cluster_view) > 0, "Cluster view is empty despite Cluster_ID present"
        if "Allocated_ΔQty_Rounded" in cluster_view.columns:
            clus_sum = pd.to_numeric(cluster_view["Allocated_ΔQty_Rounded"], errors="coerce").sum()
            assert int(round(clus_sum)) == int(round(agg_sum)), f"Cluster sum mismatch: clusters={clus_sum} stores={agg_sum}"
        print(f"[TEST] Cluster view rows: {len(cluster_view)}")
    else:
        print("[TEST] Cluster_ID not present; cluster view sanity skipped")

    print("[TEST] All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
