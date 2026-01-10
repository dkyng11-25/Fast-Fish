#!/usr/bin/env python3
"""
Quick profiler/estimator for Step 10 (SPU assortment optimization)

What it does
- Loads a sample of store_config (planning) and SPU sales (quantity) for a given period
- Measures time to parse/expand sty_sal_amt JSON for N rows
- Measures time to join expanded SPUs with quantity panel
- Extrapolates total runtime for the full dataset using simple linear scaling

Usage
  PIPELINE_YYYYMM=202410 PIPELINE_PERIOD=A PYTHONPATH=. \
    python3 tools/profile_step10_runtime.py \
      --yyyymm 202410 --period A \
      --sample-rows 100000

Notes
- Estimation assumes linear scaling. Real runs can vary due to distribution of SPU counts per row,
  I/O caching, and pandas vectorization effectiveness.
- This script does NOT write any outputs; it only prints timings and estimates.
"""

from __future__ import annotations
import os
import sys
import time
import json
import math
import argparse
from typing import Tuple

import pandas as pd
import numpy as np

# Allow importing src.config helpers
try:
    from src.config import get_api_data_files, get_current_period, get_period_label
except Exception:
    print("WARNING: Could not import src.config; will fall back to data/api_data paths", file=sys.stderr)
    get_api_data_files = None
    def get_current_period():
        y = os.getenv('PIPELINE_YYYYMM'); p = os.getenv('PIPELINE_PERIOD', 'A')
        if not y:
            raise SystemExit("Set PIPELINE_YYYYMM and PIPELINE_PERIOD or pass --yyyymm/--period")
        return y, p
    def get_period_label(y, p):
        return f"{y}{p}"


def resolve_paths(yyyymm: str, period: str) -> Tuple[str, str]:
    label = get_period_label(yyyymm, period)
    if get_api_data_files is not None:
        files = get_api_data_files(yyyymm, period)
        cfg = files.get('store_config')
        qty = files.get('spu_sales')
    else:
        cfg = os.path.join('data', 'api_data', f'store_config_{label}.csv')
        qty = os.path.join('data', 'api_data', f'complete_spu_sales_{label}.csv')
    if not (cfg and os.path.exists(cfg)):
        raise FileNotFoundError(f"store_config not found for {label}: {cfg}")
    if not (qty and os.path.exists(qty)):
        raise FileNotFoundError(f"spu_sales not found for {label}: {qty}")
    return cfg, qty


def count_rows(path: str) -> int:
    # Fast row count without loading all columns
    try:
        return sum(1 for _ in open(path, 'rb')) - 1  # minus header
    except Exception:
        try:
            return len(pd.read_csv(path, usecols=[0]))
        except Exception:
            return -1


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description='Profile Step 10 expansion/join and estimate total runtime')
    ap.add_argument('--yyyymm', type=str, help='Source YYYYMM (e.g., 202410)')
    ap.add_argument('--period', type=str, choices=['A','B'], help='Source period (A/B)')
    ap.add_argument('--sample-rows', type=int, default=50000, help='Number of store_config rows to sample for profiling')
    ap.add_argument('--seed', type=int, default=42, help='Random seed for sampling')
    return ap.parse_args()


def main():
    args = parse_args()

    yyyymm = args.yyyymm
    period = args.period
    if not yyyymm or not period:
        try:
            yyyymm, period = get_current_period()
        except Exception:
            raise SystemExit('Provide --yyyymm and --period or set PIPELINE_YYYYMM/PIPELINE_PERIOD')

    cfg_path, qty_path = resolve_paths(yyyymm, period)
    label = get_period_label(yyyymm, period)

    print(f"[CONFIG] Profiling period: {label}")
    print(f"[PATHS] store_config: {cfg_path}")
    print(f"[PATHS] spu_sales   : {qty_path}")

    total_cfg_rows = count_rows(cfg_path)
    total_qty_rows = count_rows(qty_path)
    print(f"[SIZES] store_config rows ~ {total_cfg_rows:,}")
    print(f"[SIZES] spu_sales rows    ~ {total_qty_rows:,}")

    # Load sample of store_config with columns needed for Step 10 expansion
    usecols_cfg = [
        'str_code','Cluster','cluster_id',
        'season_name','sex_name','display_location_name','big_class_name','sub_cate_name',
        'yyyy','mm','mm_type','sal_amt','sty_sal_amt','ext_sty_cnt_avg','target_sty_cnt_avg'
    ]
    t0 = time.time()
    cfg_df = pd.read_csv(cfg_path, dtype={'str_code': str}, low_memory=False, usecols=lambda c: c in usecols_cfg if c is not None else False)
    # Prefer Cluster; create if only cluster_id present
    if 'Cluster' not in cfg_df.columns and 'cluster_id' in cfg_df.columns:
        cfg_df['Cluster'] = cfg_df['cluster_id']
    # Rows with JSON present
    cfg_df = cfg_df[cfg_df['sty_sal_amt'].notna() & (cfg_df['sty_sal_amt'] != '')]
    # Overcapacity-only categories (where ext > target)
    with np.errstate(invalid='ignore'):
        mask_over = (pd.to_numeric(cfg_df['ext_sty_cnt_avg'], errors='coerce') > pd.to_numeric(cfg_df['target_sty_cnt_avg'], errors='coerce'))
    cfg_df = cfg_df[mask_over]
    load_cfg_sec = time.time() - t0

    # Sample
    n = min(args.sample_rows, len(cfg_df))
    if n <= 0:
        print("[WARN] No overcapacity rows with SPU JSON found in store_config sample; cannot profile expansion.")
        return
    sample = cfg_df.sample(n=n, random_state=args.seed).reset_index(drop=True)

    print(f"[DATA] Candidate overcapacity rows with JSON: {len(cfg_df):,}")
    print(f"[DATA] Profiling on sample rows: {n:,}")
    print(f"[TIME] Read/filtered store_config in {load_cfg_sec:.2f}s")

    # Time JSON parsing/expansion
    expanded_records = []
    t1 = time.time()
    for idx, row in sample.iterrows():
        try:
            d = json.loads(row['sty_sal_amt'])
            if not d or not isinstance(d, dict):
                continue
            # category metrics
            try:
                cur = float(row['ext_sty_cnt_avg']); tgt = float(row['target_sty_cnt_avg'])
            except Exception:
                continue
            excess = max(0.0, cur - tgt)
            if excess <= 0:
                continue
            total_sales = 0.0
            # quick sum
            for v in d.values():
                try:
                    fv = float(v)
                    if fv > 0:
                        total_sales += fv
                except Exception:
                    continue
            if total_sales <= 0:
                continue
            for spu_code, spu_sales in d.items():
                try:
                    fv = float(spu_sales)
                except Exception:
                    continue
                if fv <= 0:
                    continue
                expanded_records.append((row['str_code'], str(spu_code), fv))
        except Exception:
            continue
    expand_sec = time.time() - t1
    expanded_len = len(expanded_records)
    rows_per_sec = n / expand_sec if expand_sec > 0 else float('inf')
    spus_per_sec = expanded_len / expand_sec if expand_sec > 0 else float('inf')

    print(f"[EXPAND] Expanded {expanded_len:,} SPU rows from {n:,} category rows in {expand_sec:.2f}s")
    print(f"[EXPAND] Rate: {rows_per_sec:,.0f} cfg-rows/s, {spus_per_sec:,.0f} spu-rows/s")

    # Prepare small DataFrame and measure join with quantity sample (first M rows to simulate index/cache)
    expanded_df = pd.DataFrame(expanded_records, columns=['str_code','spu_code','spu_sales'])

    # Load quantity (only necessary columns) — we can also sample to speed up
    usecols_qty = ['str_code','spu_code','base_sal_qty','fashion_sal_qty','sal_qty','quantity','spu_sales_amt']
    t2 = time.time()
    qty_df = pd.read_csv(qty_path, dtype={'str_code': str, 'spu_code': str}, low_memory=False, usecols=lambda c: c in usecols_qty if c is not None else False)
    load_qty_sec = time.time() - t2

    # Simple join timing
    t3 = time.time()
    merged = expanded_df.merge(qty_df, on=['str_code','spu_code'], how='left')
    join_sec = time.time() - t3

    print(f"[JOIN] Joined expanded SPUs ({len(expanded_df):,}) with quantity ({len(qty_df):,}) in {join_sec:.2f}s")
    print(f"[TIME] Quantity load took {load_qty_sec:.2f}s")

    # Estimation: scale by (candidate overcapacity rows with JSON / sample_rows)
    # We use len(cfg_df) as a proxy for total rows to process in expansion phase.
    if len(cfg_df) > 0 and n > 0:
        scale = len(cfg_df) / float(n)
        est_expand_total = expand_sec * scale
        est_join_total = join_sec * scale  # approximate; the actual join scales with expanded length
        est_total = load_cfg_sec + load_qty_sec + est_expand_total + est_join_total
        print("\n=== Estimated Full-Run Timings (linear scaling) ===")
        print(f"- Candidate rows (overcapacity+JSON): {len(cfg_df):,}")
        print(f"- Expansion time: ~{est_expand_total/60:.1f} min")
        print(f"- Join time     : ~{est_join_total/60:.1f} min")
        print(f"- File I/O (obs): ~{(load_cfg_sec+load_qty_sec):.1f} s")
        print(f"- Total estimate: ~{est_total/60:.1f} min (~{est_total/3600:.2f} h)")
    else:
        print("[WARN] Insufficient sample to estimate total time.")


if __name__ == '__main__':
    main()
