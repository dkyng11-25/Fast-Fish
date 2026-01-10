#!/usr/bin/env python3
"""
Step 34A: Cluster-Level Merchandising Strategy Optimization (Period-Aware)

Purpose
- Derive cluster-level merchandising strategies from store-level rules and/or allocations
- Produce a compact CSV required by Step 35 (load_cluster_strategies)
- Register outputs in the pipeline manifest

Inputs (preferred order, period-aware):
- output/store_level_merchandising_rules_{YYYYMMP}_*.csv (Step 33 core)
- output/store_level_allocation_results_{YYYYMMP}_*.csv (Step 32)

Output (period-aware):
- output/cluster_level_merchandising_strategies_{YYYYMMP}.csv

Columns produced (subset, stable):
- cluster_id (string)
- operational_tag
- style_tag
- capacity_tag
- geographic_tag
- fashion_allocation_ratio
- basic_allocation_ratio
- capacity_utilization_target
- priority_score
- implementation_notes

This keeps Step 35 happy without forcing heavyweight cluster optimization.
"""
import argparse
import glob
import os
from datetime import datetime
from typing import Dict

import pandas as pd

# Import helpers
try:
    from src.config import get_period_label
    from src.pipeline_manifest import register_step_output, get_manifest
    from src.output_utils import create_output_with_symlinks
except Exception:
    from config import get_period_label
    from output_utils import create_output_with_symlinks
    def register_step_output(step: str, key: str, file_path: str, metadata: Dict):
        # Best-effort manifest registration if import unavailable
        try:
            import json
            man_path = os.path.join('output', 'pipeline_manifest.json')
            if os.path.exists(man_path):
                with open(man_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
            else:
                manifest = {"steps": {}}
            steps = manifest.setdefault('steps', {})
            s = steps.setdefault(step, {"outputs": {}})
            s['outputs'][key] = {"file_path": file_path, "metadata": metadata}
            with open(man_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

OUTPUT_DIR = 'output'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def find_input_file(patterns):
    for pat in patterns:
        matches = sorted(glob.glob(pat))
        if matches:
            return matches[-1]
    return None


def load_store_rules(period_label: str) -> pd.DataFrame:
    # Prefer exact period-labeled rules
    patterns = [
        os.path.join(OUTPUT_DIR, f"store_level_merchandising_rules_{period_label}_*.csv"),
        os.path.join(OUTPUT_DIR, f"store_level_merchandising_rules_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, "store_level_merchandising_rules.csv"),
    ]
    path = find_input_file(patterns)
    if not path:
        return pd.DataFrame()
    df = pd.read_csv(path)
    # Normalize keys
    if 'Cluster_ID' in df.columns and 'cluster_id' not in df.columns:
        df = df.rename(columns={'Cluster_ID': 'cluster_id'})
    if 'cluster' in df.columns and 'cluster_id' not in df.columns:
        df = df.rename(columns={'cluster': 'cluster_id'})
    if 'Cluster' in df.columns and 'cluster_id' not in df.columns:
        df = df.rename(columns={'Cluster': 'cluster_id'})
    if 'cluster_id' in df.columns:
        df['cluster_id'] = df['cluster_id'].astype(str).str.strip()
    return df


def build_cluster_strategies(rules_df: pd.DataFrame) -> pd.DataFrame:
    if rules_df is None or rules_df.empty:
        # Create a safe empty strategy set so Step 35 can still proceed if needed
        return pd.DataFrame(columns=[
            'cluster_id','operational_tag','style_tag','capacity_tag','geographic_tag',
            'fashion_allocation_ratio','basic_allocation_ratio','capacity_utilization_target',
            'priority_score','implementation_notes'
        ])

    # Candidate columns from rules to promote to cluster strategies
    # We take majority/mean where appropriate
    tag_cols = ['operational_tag','style_tag','capacity_tag','geographic_tag']
    ratio_cols = ['fashion_allocation_ratio','basic_allocation_ratio','capacity_utilization_target','priority_score']

    # Ensure presence
    for c in tag_cols + ratio_cols:
        if c not in rules_df.columns:
            rules_df[c] = None

    # Aggregate: mode for tags, mean for ratios
    def _mode(series: pd.Series):
        try:
            vc = series.dropna().astype(str).value_counts()
            return vc.idxmax() if len(vc) > 0 else None
        except Exception:
            return None

    agg_spec = {c: _mode for c in tag_cols}
    for c in ratio_cols:
        agg_spec[c] = 'mean'

    grouped = rules_df.groupby('cluster_id').agg(agg_spec).reset_index()

    # Final touch: fill defaults if still NA
    grouped['operational_tag'] = grouped['operational_tag'].fillna('standard')
    grouped['style_tag'] = grouped['style_tag'].fillna('baseline')
    grouped['capacity_tag'] = grouped['capacity_tag'].fillna('nominal')
    grouped['geographic_tag'] = grouped['geographic_tag'].fillna('N/A')
    for c in ['fashion_allocation_ratio','basic_allocation_ratio']:
        grouped[c] = pd.to_numeric(grouped[c], errors='coerce')
    # Default safe split 0.5/0.5 if both null
    mask_both_null = grouped['fashion_allocation_ratio'].isna() & grouped['basic_allocation_ratio'].isna()
    grouped.loc[mask_both_null, 'fashion_allocation_ratio'] = 0.5
    grouped.loc[mask_both_null, 'basic_allocation_ratio'] = 0.5

    grouped['capacity_utilization_target'] = pd.to_numeric(grouped['capacity_utilization_target'], errors='coerce').fillna(0.75)
    grouped['priority_score'] = pd.to_numeric(grouped['priority_score'], errors='coerce').fillna(0.5)
    grouped['implementation_notes'] = 'auto-derived from store-level rules'
    return grouped


def main():
    parser = argparse.ArgumentParser(description='Step 34A: Cluster Strategy Optimization (period-aware)')
    parser.add_argument('--target-yyyymm', required=True, help='Target year-month (YYYYMM)')
    parser.add_argument('--target-period', required=True, choices=['A','B'], help='Target period (A/B)')
    args = parser.parse_args()

    period_label = get_period_label(args.target_yyyymm, args.target_period)
    print(f"[INFO] Step 34A: Building cluster strategies for {period_label}...")

    rules_df = load_store_rules(period_label)
    print(f"[INFO] Loaded store-level rules: {len(rules_df)} rows")

    strategies_df = build_cluster_strategies(rules_df)
    print(f"[INFO] Built cluster strategies: {len(strategies_df)} clusters")

    # Save with dual output pattern
    base_path = os.path.join(OUTPUT_DIR, "cluster_level_merchandising_strategies")
    timestamped_file, period_file, generic_file = create_output_with_symlinks(
        df=strategies_df,
        base_path=base_path,
        period_label=period_label
    )
    print(f"[INFO] Saved strategies with dual output pattern:")
    print(f"   Timestamped: {timestamped_file}")
    print(f"   Period: {period_file}")
    print(f"   Generic: {generic_file}")

    # Register in manifest so Step 35 can resolve it
    meta = {
        'target_year': int(args.target_yyyymm[:4]),
        'target_month': int(args.target_yyyymm[4:]),
        'target_period': args.target_period,
        'records': int(len(strategies_df)),
    }
    try:
        register_step_output('step34', f'cluster_level_merchandising_strategies_{period_label}', timestamped_file, meta)
        register_step_output('step34', 'cluster_level_merchandising_strategies', generic_file, meta)
        print("[INFO] Registered strategies in manifest (step34)")
    except Exception as e:
        print(f"[WARN] Could not register strategies in manifest: {e}")

    print("[INFO] Step 34A complete.")


if __name__ == '__main__':
    main()
