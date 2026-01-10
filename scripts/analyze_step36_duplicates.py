#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime
from typing import List, Optional

import pandas as pd


DUP_KEYS = ["Store_Code", "Store_Group_Name", "Target_Style_Tags"]


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def load_csv(path: str, usecols: Optional[List[str]] = None) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    # Read all columns but ensure keys are strings to preserve exactness
    dtype = {c: str for c in DUP_KEYS}
    df = pd.read_csv(path, low_memory=False, dtype=dtype, usecols=usecols)
    return df


def profile_duplicates(df: pd.DataFrame):
    keys = [c for c in DUP_KEYS if c in df.columns]
    if len(keys) < 3:
        return {
            "keys_present": keys,
            "duplicate_rows": 0,
            "unique_duplicate_keys": 0,
            "note": "Not all duplicate keys present; skipping duplicate analysis."
        }, None, None, None

    dup_mask = df.duplicated(subset=keys, keep=False)
    duplicate_rows = int(dup_mask.sum())

    # Unique duplicated key combinations
    unique_duplicate_keys = int(df.loc[dup_mask, keys].drop_duplicates().shape[0])

    # Top duplicated combinations
    top_dups = (
        df.loc[dup_mask]
        .groupby(keys, dropna=False)
        .size()
        .sort_values(ascending=False)
        .head(25)
        .reset_index(name="rows")
    )

    # Distribution by Category/Subcategory (if present)
    by_cat = None
    have_cat = all(c in df.columns for c in ["Category", "Subcategory"])
    if have_cat:
        by_cat = (
            df.loc[dup_mask]
            .groupby(["Category", "Subcategory"], dropna=False)
            .size()
            .sort_values(ascending=False)
            .reset_index(name="duplicate_rows")
        )

    # Distribution by Cluster (if present)
    by_cluster = None
    if "Cluster_ID" in df.columns:
        by_cluster = (
            df.loc[dup_mask]
            .groupby(["Cluster_ID"], dropna=False)
            .size()
            .sort_values(ascending=False)
            .reset_index(name="duplicate_rows")
        )

    stats = {
        "keys_present": keys,
        "duplicate_rows": duplicate_rows,
        "unique_duplicate_keys": unique_duplicate_keys,
    }
    return stats, top_dups, by_cat, by_cluster


def save_reports(prefix: str, period_label: str, stats: dict, top_dups: Optional[pd.DataFrame], by_cat: Optional[pd.DataFrame], by_cluster: Optional[pd.DataFrame], validation_json: Optional[str] = None) -> str:
    out_dir = os.path.dirname(prefix) or "."
    os.makedirs(out_dir, exist_ok=True)

    # JSON stats
    stats_path = f"{prefix}_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump({"period_label": period_label, **stats}, f, ensure_ascii=False, indent=2)

    # CSV tables
    if top_dups is not None:
        top_dups.to_csv(f"{prefix}_top_dups.csv", index=False)
    if by_cat is not None:
        by_cat.to_csv(f"{prefix}_dups_by_category.csv", index=False)
    if by_cluster is not None:
        by_cluster.to_csv(f"{prefix}_dups_by_cluster.csv", index=False)

    # Markdown summary
    md_path = f"{prefix}_summary.md"
    val_note = ""
    if validation_json and os.path.exists(validation_json):
        try:
            with open(validation_json, "r", encoding="utf-8") as f:
                v = json.load(f)
                reported = v.get("checks", {}).get("duplicate_on_store_line_key", {}).get("duplicate_rows")
                val_note = f"\n- Validation JSON duplicate_rows: {reported}"
        except Exception:
            pass

    md = [
        f"# Step36 Duplicates Profile — {period_label}",
        "",
        f"- Duplicate key: (Store_Code, Store_Group_Name, Target_Style_Tags)",
        f"- Keys present in data: {', '.join(stats.get('keys_present', []))}",
        f"- Duplicate rows: {stats.get('duplicate_rows', 0)}" + val_note,
        f"- Unique duplicated keys: {stats.get('unique_duplicate_keys', 0)}",
        "",
        "## Files",
        f"- Stats JSON: {os.path.basename(stats_path)}",
    ]
    if top_dups is not None:
        md.append(f"- Top duplicates CSV: {os.path.basename(prefix)}_top_dups.csv")
    if by_cat is not None:
        md.append(f"- Duplicates by Category/Subcategory: {os.path.basename(prefix)}_dups_by_category.csv")
    if by_cluster is not None:
        md.append(f"- Duplicates by Cluster: {os.path.basename(prefix)}_dups_by_cluster.csv")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    return md_path


def run_one(input_path: str, period_label: str, validation_json: Optional[str]) -> dict:
    df = load_csv(input_path)
    stats, top_dups, by_cat, by_cluster = profile_duplicates(df)
    prefix = os.path.join(
        "output",
        f"step36_duplicates_profile_{period_label}_{_ts()}"
    )
    summary_md = save_reports(prefix, period_label, stats, top_dups, by_cat, by_cluster, validation_json)
    print(f"[OK] {period_label}: duplicates={stats.get('duplicate_rows', 0)}, unique_keys={stats.get('unique_duplicate_keys', 0)} -> {summary_md}")
    return {
        "period_label": period_label,
        "duplicate_rows": stats.get("duplicate_rows", 0),
        "summary_md": summary_md,
    }


def main():
    p = argparse.ArgumentParser(description="Profile Step36 duplicates for unified delivery output")
    p.add_argument("--input", required=True, help="Path to unified delivery CSV")
    p.add_argument("--period-label", required=True, help="Period label, e.g., 202509B")
    p.add_argument("--validation-json", default=None, help="Path to validation JSON (optional)")
    p.add_argument("--compare-input", default=None, help="Optional: compare another period CSV")
    p.add_argument("--compare-period-label", default=None)
    p.add_argument("--compare-validation-json", default=None)
    args = p.parse_args()

    # Run primary
    res1 = run_one(args.input, args.period_label, args.validation_json)

    # Optional comparison
    if args.compare_input and args.compare_period_label:
        res2 = run_one(args.compare_input, args.compare_period_label, args.compare_validation_json)
        print(
            f"[COMPARE] {res1['period_label']} duplicates={res1['duplicate_rows']} vs "
            f"{res2['period_label']} duplicates={res2['duplicate_rows']}"
        )


if __name__ == "__main__":
    main()
