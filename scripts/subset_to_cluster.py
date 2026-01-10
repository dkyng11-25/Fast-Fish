#!/usr/bin/env python3
"""
Subset pipeline inputs/outputs to a single cluster to accelerate downstream steps (7-36).

- Reads output/clustering_results_spu.csv to get stores (str_code) for a target cluster.
- For specified periods, filters API data files to only those stores and writes back in-place
  while moving originals to a backup directory.
- Also filters selected outputs like stores_with_feels_like_temperature.csv and clustering_results_spu.csv.

Usage:
  PYTHONPATH=. python3 scripts/subset_to_cluster.py \
    --cluster-id 0 \
    --periods 202508B \
    --backup-dir backup/cluster_subset_0_202508B

Notes:
- This script is reversible: originals are moved into the backup dir before writing filtered copies.
- It is conservative and will skip files that are missing.
"""
from __future__ import annotations
import argparse
import os
import shutil
from pathlib import Path
from typing import List
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / 'data' / 'api_data'
OUT_DIR = ROOT / 'output'

API_TEMPLATES = [
    'complete_spu_sales_{label}.csv',
    'complete_category_sales_{label}.csv',
    'store_config_{label}.csv',
    # store_sales_{label}.csv could be filtered as well, but not strictly necessary for steps 7-12
]

OTHER_FILES = [
    # (relative_path, key_column, output)
    ('output/stores_with_feels_like_temperature.csv', 'store_code', True),
    ('output/clustering_results_spu.csv', 'Cluster', True),
]


def backup_then_write(df: pd.DataFrame, target: Path, backup_root: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not target.is_symlink():
        rel = target.relative_to(ROOT)
        backup_path = backup_root / rel
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(target), str(backup_path))
    df.to_csv(target, index=False)


def load_cluster_store_list(cluster_id: int) -> pd.DataFrame:
    path = OUT_DIR / 'clustering_results_spu.csv'
    if not path.exists():
        raise FileNotFoundError(f"Missing clustering results: {path}")
    df = pd.read_csv(path, dtype=str, low_memory=False)
    # Normalize cluster column detection
    if 'Cluster' in df.columns:
        cluster_col = 'Cluster'
    elif 'cluster' in df.columns:
        cluster_col = 'cluster'
    elif 'cluster_id' in df.columns:
        cluster_col = 'cluster_id'
    else:
        raise RuntimeError('Cannot find Cluster/cluster/cluster_id column in clustering_results_spu.csv')
    # Normalize store code column
    store_col = 'str_code' if 'str_code' in df.columns else ('store_code' if 'store_code' in df.columns else None)
    if store_col is None:
        raise RuntimeError('clustering_results_spu.csv does not contain str_code/store_code column')
    stores = df[df[cluster_col].astype(str) == str(cluster_id)][[store_col]].dropna().drop_duplicates()
    stores.columns = ['str_code']
    if stores.empty:
        raise RuntimeError(f"No stores found for cluster_id={cluster_id}")
    return stores


def filter_api_file(path: Path, stores: pd.DataFrame, key_col: str = 'str_code') -> pd.DataFrame | None:
    if not path.exists():
        return None
    df = pd.read_csv(path, dtype={key_col: str}, low_memory=False)
    if key_col not in df.columns:
        return None
    before = len(df)
    keep = df[key_col].astype(str).isin(stores['str_code'].astype(str))
    fdf = df.loc[keep].copy()
    print(f"Filtered {path.name}: {before} -> {len(fdf)} rows")
    return fdf


def filter_other_file(rel_path: str, stores: pd.DataFrame, backup_root: Path):
    target = ROOT / rel_path
    if not target.exists():
        print(f"Skip missing {rel_path}")
        return
    if rel_path.endswith('stores_with_feels_like_temperature.csv'):
        key_col = 'store_code'
        df = pd.read_csv(target, dtype={key_col: str}, low_memory=False)
        before = len(df)
        fdf = df[df[key_col].astype(str).isin(stores['str_code'].astype(str))].copy()
        print(f"Filtered {rel_path}: {before} -> {len(fdf)} rows")
        backup_then_write(fdf, target, backup_root)
    elif rel_path.endswith('clustering_results_spu.csv'):
        df = pd.read_csv(target, dtype=str, low_memory=False)
        before = len(df)
        store_col = 'str_code' if 'str_code' in df.columns else ('store_code' if 'store_code' in df.columns else None)
        if store_col is None:
            print('Cannot find str_code/store_code in clustering_results_spu.csv, skipping filter')
            return
        fdf = df[df[store_col].astype(str).isin(stores['str_code'].astype(str))].copy()
        print(f"Filtered {rel_path}: {before} -> {len(fdf)} rows")
        backup_then_write(fdf, target, backup_root)
    else:
        print(f"No filter rule for {rel_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cluster-id', type=int, required=True, help='Cluster id to keep')
    ap.add_argument('--periods', type=str, required=True, help='Comma-separated list of period labels, e.g. 202508B,202508A')
    ap.add_argument('--backup-dir', type=str, required=True, help='Backup directory relative to repo root, e.g. backup/cluster_subset_0_202508B')
    args = ap.parse_args()

    backup_root = (ROOT / args.backup_dir).resolve()
    print(f"Backup directory: {backup_root}")
    stores = load_cluster_store_list(args.cluster_id)
    print(f"Stores in cluster {args.cluster_id}: {len(stores)}")

    labels: List[str] = [x.strip() for x in args.periods.split(',') if x.strip()]
    for label in labels:
        print(f"\nProcessing period {label}...")
        for tmpl in API_TEMPLATES:
            fname = tmpl.format(label=label)
            path = API_DIR / fname
            fdf = filter_api_file(path, stores, key_col='str_code')
            if fdf is None:
                print(f"Skip missing or incompatible {fname}")
                continue
            backup_then_write(fdf, path, backup_root)
            # Also mirror into output/ if the same file lives there
            out_path = OUT_DIR / fname
            if out_path.exists() and not out_path.is_symlink():
                backup_then_write(fdf, out_path, backup_root)

    # Filter other common outputs
    print("\nFiltering non-API files...")
    for rel, _, _ in OTHER_FILES:
        filter_other_file(rel, stores, backup_root)

    print("\nSubset complete. You can now run Steps 7-36 faster for the selected cluster.")

if __name__ == '__main__':
    main()
