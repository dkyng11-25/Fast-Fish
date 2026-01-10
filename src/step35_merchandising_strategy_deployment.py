#!/usr/bin/env python3
"""
Step 35: Merchandising Strategy Deployment

This script generates final store-level merchandising recommendations by integrating
real data from all previous pipeline steps including store clustering, weather data,
merchandising rules, cluster strategies, and performance metrics.

The output is ready for downstream deployment and stakeholder review.
- Outputs per period (e.g., 202509A, 202509B):
  * output/store_level_merchandising_recommendations_202509A.csv
"""

print("DEBUG: Starting Step 35 script execution...")

import os
import sys
import glob
import pandas as pd
import argparse
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import json

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
sys.path.append(os.path.join(parent_dir, "src"))

from src.config import get_period_label, OUTPUT_DIR
from src.pipeline_manifest import get_manifest
from src.output_utils import create_output_with_symlinks

# Define directories relative to parent directory
OUTPUT_DIR = os.path.join(parent_dir, "output")
DELIVERY_DIR = os.path.join(OUTPUT_DIR, "delivery_202509")
FF_DIR = os.path.join(OUTPUT_DIR, "FF results")


MANIFEST_PATH = os.path.join(OUTPUT_DIR, "pipeline_manifest.json")


def load_manifest(path: str = MANIFEST_PATH) -> Dict:
    """Load pipeline manifest"""
    if not os.path.exists(path):
        return {"created": datetime.now().isoformat(), "last_updated": datetime.now().isoformat(), "steps": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(manifest: Dict, path: str = MANIFEST_PATH) -> None:
    """Save pipeline manifest"""
    manifest["last_updated"] = datetime.now().isoformat()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def _resolve_manifest_output(manifest: Dict, step: str, period_label: str, fallback_key_prefix: str) -> Optional[str]:
    """Resolve a file path from manifest for a given step and period.
    Prefers exact period-specific key, then matches by metadata, then generic key.
    """
    step_obj = manifest.get("steps", {}).get(step, {})
    outputs = step_obj.get("outputs", {})

    specific_key = f"{fallback_key_prefix}_{period_label}"
    if specific_key in outputs and "file_path" in outputs[specific_key]:
        return outputs[specific_key]["file_path"]

    for key, val in outputs.items():
        meta = (val or {}).get("metadata", {})
        if meta.get("target_period") == period_label[-1:] and meta.get("target_year") and meta.get("target_month"):
            yyyymm = period_label[:-1]
            year = int(yyyymm[:4])
            month = int(yyyymm[4:])
            if meta.get("target_year") == year and meta.get("target_month") == month:
                return val.get("file_path")

    if fallback_key_prefix in outputs and "file_path" in outputs[fallback_key_prefix]:
        return outputs[fallback_key_prefix]["file_path"]

    return None


def load_store_tags(yyyymm: str, period: str) -> pd.DataFrame:
    """Load store tags/enhanced clustering results, preferring Step 32 via manifest."""
    period_label = get_period_label(yyyymm, period)
    manifest = load_manifest()

    path = _resolve_manifest_output(manifest, "step32", period_label, "enhanced_clustering_results")
    if not path or not os.path.exists(path):
        candidates = [
            os.path.join(OUTPUT_DIR, f"enhanced_clustering_results_{period_label}.csv"),
            os.path.join(OUTPUT_DIR, "enhanced_clustering_results.csv"),
            os.path.join(OUTPUT_DIR, f"store_tags_{period_label}.csv"),
            os.path.join(FF_DIR, f"store_tags_{period_label}.csv"),
            os.path.join(OUTPUT_DIR, "store_tags.csv"),
            os.path.join(FF_DIR, "store_tags.csv"),
        ]
        path = next((p for p in candidates if os.path.exists(p)), None)

    if not path:
        raise FileNotFoundError(f"Store tags/enhanced clustering not found for {period_label}")

    df = pd.read_csv(path)
    # Handle different column naming conventions
    if 'Cluster_ID' in df.columns and 'cluster_id' not in df.columns:
        df = df.rename(columns={'Cluster_ID': 'cluster_id'})
    if 'Cluster' in df.columns and 'cluster_id' not in df.columns:
        df = df.rename(columns={'Cluster': 'cluster_id'})
    elif 'cluster' in df.columns and 'cluster_id' not in df.columns:
        df = df.rename(columns={'cluster': 'cluster_id'})
    # Normalize store code column name
    if 'Store_Code' in df.columns and 'str_code' not in df.columns:
        df = df.rename(columns={'Store_Code': 'str_code'})
    
    # Ensure cluster_id is properly formatted as string for consistent merging
    if 'cluster_id' in df.columns:
        df['cluster_id'] = df['cluster_id'].astype(str).str.strip()
    # Ensure str_code is string for consistent joins
    if 'str_code' in df.columns:
        df['str_code'] = df['str_code'].astype(str).str.strip()

    # If cluster_id not present, enrich from Step 24 comprehensive cluster labels via manifest
    if 'cluster_id' not in df.columns:
        man = load_manifest()
        step24 = man.get('steps', {}).get('step24', {}).get('outputs', {})
        cl_path = None
        for key in [f"comprehensive_cluster_labels_{period_label}", "comprehensive_cluster_labels"]:
            meta = step24.get(key)
            if isinstance(meta, dict) and os.path.exists(meta.get('file_path', '')):
                cl_path = meta['file_path']
                break
        if cl_path and os.path.exists(cl_path):
            clusters_df = pd.read_csv(cl_path)
            # Normalize columns
            if 'Cluster' in clusters_df.columns and 'cluster_id' not in clusters_df.columns:
                clusters_df = clusters_df.rename(columns={'Cluster': 'cluster_id'})
            if 'store_codes' in clusters_df.columns and 'str_code' not in clusters_df.columns:
                # Expand store_codes list into rows
                expanded = []
                for _, row in clusters_df.iterrows():
                    codes = str(row['store_codes']).replace(' ', ',').split(',')
                    for c in codes:
                        c = c.strip()
                        if c:
                            expanded.append({'str_code': c, 'cluster_id': row.get('cluster_id', row.get('Cluster'))})
                clusters_df = pd.DataFrame(expanded)
            # Coerce types
            if 'str_code' in clusters_df.columns:
                clusters_df['str_code'] = clusters_df['str_code'].astype(str).str.strip()
            if 'cluster_id' in clusters_df.columns:
                clusters_df['cluster_id'] = clusters_df['cluster_id'].astype(str).str.strip()
            # Merge cluster labels into df if str_code available
            if 'str_code' in df.columns and 'str_code' in clusters_df.columns:
                df = df.merge(clusters_df[['str_code','cluster_id']].drop_duplicates(), on='str_code', how='left')
        
    # Final guard: if still missing cluster_id from allocation results, derive a placeholder from group name
    if 'cluster_id' not in df.columns and 'Store_Group_Name' in df.columns:
        df['cluster_id'] = df['Store_Group_Name'].astype(str)
    
    print(f"  ✓ Loaded store tags from {os.path.basename(path)}: {len(df)} records with {df['cluster_id'].nunique() if 'cluster_id' in df.columns else 'N/A'} clusters")
    return df


def load_weather_data() -> pd.DataFrame:
    """Load real weather data from Step 5 feels-like temperature calculations."""
    # Try multiple possible weather data file paths
    possible_paths = [
        os.path.join(OUTPUT_DIR, "stores_with_feels_like_temperature.csv"),
        os.path.join(OUTPUT_DIR, "weather_data", "stores_with_feels_like_temperature.csv"),
        os.path.join(OUTPUT_DIR, "stores_feels_like_temp.csv"),
        os.path.join(OUTPUT_DIR, "weather", "stores_with_feels_like_temperature.csv")
    ]
    
    file_path = None
    for path in possible_paths:
        if os.path.exists(path):
            file_path = path
            break
    
    if file_path is None:
        raise FileNotFoundError(f"Weather data file not found. Searched paths: {possible_paths}")
    
    weather_df = pd.read_csv(file_path)
    # Rename columns to match expected format (handle various naming conventions)
    column_mapping = {
        'store_code': 'str_code',
        'Store_Code': 'str_code',
        'store_id': 'str_code',
        'str_code': 'str_code',
        'feels_like_temperature': 'avg_feels_like_temp',
        'Feels_Like_Temperature': 'avg_feels_like_temp',
        'feels_like_temp': 'avg_feels_like_temp',
        'temperature_band': 'temperature_band',
        'Temperature_Band': 'temperature_band',
        'temp_band': 'temperature_band'
    }
    
    # Apply column mapping
    for old_col, new_col in column_mapping.items():
        if old_col in weather_df.columns and new_col not in weather_df.columns:
            weather_df = weather_df.rename(columns={old_col: new_col})
    
    return weather_df


def load_merchandising_rules(yyyymm: str, period: str) -> pd.DataFrame:
    """Load store-level merchandising rules from Step 33 via manifest."""
    period_label = get_period_label(yyyymm, period)
    manifest = load_manifest()

    path = _resolve_manifest_output(manifest, "step33", period_label, "store_level_merchandising_rules")
    if not path or not os.path.exists(path):
        candidates = [
            os.path.join(OUTPUT_DIR, f"store_level_merchandising_rules_{period_label}.csv"),
            os.path.join(OUTPUT_DIR, "store_level_merchandising_rules.csv"),
        ]
        pattern = os.path.join(OUTPUT_DIR, f"store_level_merchandising_rules_{period_label}_*.csv")
        matches = sorted(glob.glob(pattern))
        if matches:
            candidates.insert(0, matches[-1])
        path = next((p for p in candidates if os.path.exists(p)), None)

    if not path:
        raise FileNotFoundError(f"Merchandising rules not found for {period_label}")

    df = pd.read_csv(path)
    # Handle different column naming conventions for cluster_id
    if 'Cluster_ID' in df.columns and 'cluster_id' not in df.columns:
        df = df.rename(columns={'Cluster_ID': 'cluster_id'})
    elif 'Cluster' in df.columns and 'cluster_id' not in df.columns:
        df = df.rename(columns={'Cluster': 'cluster_id'})
    elif 'cluster' in df.columns and 'cluster_id' not in df.columns:
        df = df.rename(columns={'cluster': 'cluster_id'})
    
    # Ensure cluster_id is properly formatted as string for consistent merging
    if 'cluster_id' in df.columns:
        df['cluster_id'] = df['cluster_id'].astype(str).str.strip()
    # Ensure str_code is string for consistent joins
    if 'str_code' in df.columns:
        df['str_code'] = df['str_code'].astype(str).str.strip()
    
    print(f"  ✓ Loaded merchandising rules from {os.path.basename(path)}: {len(df)} records with {df['cluster_id'].nunique() if 'cluster_id' in df.columns else 'N/A'} clusters")
    return df


def load_cluster_strategies(yyyymm: str, period: str) -> pd.DataFrame:
    """Load cluster-level merchandising strategies from Step 34 via manifest."""
    period_label = get_period_label(yyyymm, period)
    manifest = load_manifest()

    path = _resolve_manifest_output(manifest, "step34", period_label, "cluster_level_merchandising_strategies")
    if not path or not os.path.exists(path):
        candidates = [
            os.path.join(OUTPUT_DIR, f"cluster_level_merchandising_strategies_{period_label}.csv"),
            os.path.join(OUTPUT_DIR, "cluster_level_merchandising_strategies.csv"),
            os.path.join(DELIVERY_DIR, f"cluster_level_merchandising_strategies_{period_label}.csv"),
        ]
        path = next((p for p in candidates if os.path.exists(p)), None)

    if not path:
        raise FileNotFoundError(f"Cluster strategies not found for {period_label}")

    df = pd.read_csv(path)
    # Ensure cluster_id is properly formatted as string for consistent merging
    if 'cluster_id' in df.columns:
        df['cluster_id'] = df['cluster_id'].astype(str).str.strip()
    
    print(f"  ✓ Loaded cluster strategies from {os.path.basename(path)}: {len(df)} clusters")
    return df


def load_plugin_output(yyyymm: str, period: str) -> pd.DataFrame:
    """Load performance metrics from Step 33 plugin output via manifest (if available)."""
    period_label = get_period_label(yyyymm, period)
    manifest = load_manifest()

    path = _resolve_manifest_output(manifest, "step33", period_label, "store_level_plugin_output")
    if not path or not os.path.exists(path):
        candidates = [
            os.path.join(DELIVERY_DIR, period_label, "store_level_plugin_output.csv"),
            os.path.join(DELIVERY_DIR, "store_level_plugin_output.csv"),
            os.path.join(OUTPUT_DIR, f"store_level_plugin_output_{period_label}.csv"),
            os.path.join(OUTPUT_DIR, "store_level_plugin_output.csv"),
            os.path.join(OUTPUT_DIR, f"plugin_output_{period_label}.csv"),
            os.path.join(OUTPUT_DIR, "plugin_output.csv"),
        ]
        pattern = os.path.join(OUTPUT_DIR, f"store_level_plugin_output_{period_label}_*.csv")
        matches = sorted(glob.glob(pattern))
        if matches:
            candidates.insert(0, matches[-1])
        path = next((p for p in candidates if os.path.exists(p)), None)

    if not path:
        print("  ⚠️  Plugin output file not found; proceeding without plugin data")
        return pd.DataFrame()

    df = pd.read_csv(path)
    print(f"  ✓ Loaded plugin output: {len(df)} records")
    return df


def load_enriched_attributes(yyyymm: str, period: str) -> pd.DataFrame:
    """Load Step 22 enriched store attributes via manifest, normalize aliases for Step 35."""
    period_label = get_period_label(yyyymm, period)
    man = get_manifest().manifest
    step22 = man.get("steps", {}).get("step22", {}).get("outputs", {})
    # Prefer exact period-specific key
    # Only accept exact period-specific key to avoid cross-period contamination
    meta = step22.get(f"enriched_store_attributes_{period_label}")
    path = None
    if isinstance(meta, dict):
        path = meta.get("file_path")
    if not path or not os.path.exists(path):
        # Fallback to latest matching filename for this period only
        import glob
        candidates = sorted(glob.glob(f"output/enriched_store_attributes_{period_label}_*.csv"))
        if candidates:
            path = candidates[-1]
    if not path or not os.path.exists(path):
        print(f"  ⚠️  Enriched attributes not found for {period_label}")
        return pd.DataFrame()
    df = pd.read_csv(path)
    # Normalize key types for safe joins
    if 'str_code' in df.columns:
        df['str_code'] = df['str_code'].astype(str).str.strip()
    if 'cluster_id' in df.columns:
        df['cluster_id'] = df['cluster_id'].astype(str).str.strip()
    # Add/normalize aliases expected by Step 35 mapping
    if 'cluster_id' not in df.columns and 'Cluster' in df.columns:
        df['cluster_id'] = df['Cluster']
    if 'fashion_basic_classification' not in df.columns and 'store_type' in df.columns:
        df['fashion_basic_classification'] = df['store_type']
    # Provide 'temperature_zone' alias expected by final mapping
    if 'temperature_zone' not in df.columns and 'temperature_band' in df.columns:
        df['temperature_zone'] = df['temperature_band']
    # Provide 'Store_Type' for final mapping convenience
    if 'Store_Type' not in df.columns and 'store_type' in df.columns:
        df['Store_Type'] = df['store_type']
    print(f"  ✓ Loaded enriched attributes from {os.path.basename(path)}: {len(df)} rows")
    return df


def load_step18_sell_through_data(yyyymm: str, period: str) -> pd.DataFrame:
    """Load Step 18 sell-through analysis data from manifest or fallback to file lookup."""
    from src.pipeline_manifest import get_manifest
    
    period_label = get_period_label(yyyymm, period)
    manifest = get_manifest().manifest
    step18_outputs = manifest.get("steps", {}).get("step18", {}).get("outputs", {})
    
    # Try to find period-specific output first
    specific_key = f"sell_through_analysis_{period_label}"
    if specific_key in step18_outputs:
        path = step18_outputs[specific_key]["file_path"]
        if os.path.exists(path):
            df = pd.read_csv(path)
            print(f"  ✓ Loaded Step 18 sell-through data from manifest: {len(df)} records")
            return df
    
    # Fallback to generic output
    if "sell_through_analysis" in step18_outputs:
        path = step18_outputs["sell_through_analysis"]["file_path"]
        if os.path.exists(path):
            df = pd.read_csv(path)
            print(f"  ✓ Loaded Step 18 sell-through data from manifest (generic): {len(df)} records")
            return df
    
    # Final fallback: look for files in output directory
    import glob
    pattern = f"output/fast_fish_with_sell_through_analysis_{period_label}_*.csv"
    matches = glob.glob(pattern)
    if matches:
        # Use the most recent file
        path = sorted(matches)[-1]
        df = pd.read_csv(path)
        print(f"  ⚠️  Loaded Step 18 sell-through data from file (not manifest): {len(df)} records")
        return df
    
    print("  ⚠️  No Step 18 sell-through data found")
    return pd.DataFrame()

def create_comprehensive_store_recommendations(store_tags_df: pd.DataFrame, weather_df: pd.DataFrame, merch_rules_df: pd.DataFrame, cluster_strategies_df: pd.DataFrame, plugin_output_df: pd.DataFrame, step18_df: pd.DataFrame = None) -> pd.DataFrame:
    """Create comprehensive store-level merchandising recommendations by merging all real data sources."""
    
    # Start with real store tags as the primary data source (2,268 stores with 44 real clusters)
    print(f"Starting with {len(store_tags_df)} stores and {store_tags_df['cluster_id'].nunique()} real clusters")
    
    # Normalize join keys
    for df_ref in (store_tags_df, weather_df, merch_rules_df, cluster_strategies_df, plugin_output_df):
        try:
            if df_ref is not None and 'str_code' in df_ref.columns:
                df_ref['str_code'] = df_ref['str_code'].astype(str).str.strip()
            if df_ref is not None and 'cluster_id' in df_ref.columns:
                df_ref['cluster_id'] = df_ref['cluster_id'].astype(str).str.strip()
        except Exception:
            pass

    # Remove duplicate columns from store_tags_df before merging
    store_tags_df = store_tags_df.loc[:, ~store_tags_df.columns.duplicated()]
    
    # Merge with weather data
    weather_df = weather_df.loc[:, ~weather_df.columns.duplicated()]
    merged_df = pd.merge(store_tags_df, weather_df, on='str_code', how='left')
    print(f"After weather merge: {len(merged_df)} records")

    # Merge with enriched store attributes (Step 22)
    try:
        enriched_df = load_enriched_attributes(yyyymm=TARGET_YYYYMM if 'TARGET_YYYYMM' in globals() else None, period=TARGET_PERIOD if 'TARGET_PERIOD' in globals() else None)
    except Exception:
        enriched_df = pd.DataFrame()
    if not enriched_df.empty:
        enriched_df = enriched_df.loc[:, ~enriched_df.columns.duplicated()]
        # Avoid clobbering cluster_id during merge
        if 'cluster_id' in enriched_df.columns:
            enriched_df = enriched_df.drop(columns=['cluster_id'])
        merged_df = pd.merge(merged_df, enriched_df, on='str_code', how='left')
        # Backfill convenience columns if needed
        if 'temperature_zone' not in merged_df.columns and 'temperature_band' in merged_df.columns:
            merged_df['temperature_zone'] = merged_df['temperature_band']
        if 'Store_Type' not in merged_df.columns and 'store_type' in merged_df.columns:
            merged_df['Store_Type'] = merged_df['store_type']
        # Restore cluster_id if suffixing occurred elsewhere
        if 'cluster_id' not in merged_df.columns:
            if 'cluster_id_x' in merged_df.columns or 'cluster_id_y' in merged_df.columns:
                merged_df['cluster_id'] = merged_df.get('cluster_id_x', pd.Series(index=merged_df.index)).fillna(
                    merged_df.get('cluster_id_y', pd.Series(index=merged_df.index))
                )
        print(f"After enriched attributes merge: {len(merged_df)} records")
    
    # Merge with merchandising rules (join by str_code only to avoid non-matches on cluster)
    merch_rules_df = merch_rules_df.loc[:, ~merch_rules_df.columns.duplicated()]
    merged_df = pd.merge(merged_df, merch_rules_df, on='str_code', how='left', suffixes=('_tags', '_rules'))
    print(f"After merch rules merge: {len(merged_df)} records")
    
    # Merge with cluster strategies
    cluster_strategies_df = cluster_strategies_df.loc[:, ~cluster_strategies_df.columns.duplicated()]
    if 'cluster_id' not in merged_df.columns:
        # Coalesce from common duplicate columns created by previous merges
        for cand in ['cluster_id_tags', 'cluster_id_x', 'cluster_id_y', 'Cluster', 'Cluster_ID']:
            if cand in merged_df.columns:
                merged_df['cluster_id'] = merged_df[cand].astype(str).str.strip()
                break
    merged_df = pd.merge(merged_df, cluster_strategies_df, on='cluster_id', how='left')
    print(f"After cluster strategies merge: {len(merged_df)} records")
    
    # Merge with plugin output (performance metrics) - only if plugin data exists
    if not plugin_output_df.empty:
        plugin_output_df = plugin_output_df.loc[:, ~plugin_output_df.columns.duplicated()]
        # Check if 'Store_Code' column exists in plugin_output_df
        if 'Store_Code' in plugin_output_df.columns:
            merged_df = pd.merge(merged_df, plugin_output_df, left_on='str_code', right_on='Store_Code', how='left')
        else:
            # Try to merge on str_code directly
            merged_df = pd.merge(merged_df, plugin_output_df, on='str_code', how='left')
        print(f"After plugin output merge: {len(merged_df)} records")
    else:
        print("No plugin output data to merge")
    
    # Merge with Step 18 sell-through data if available
    if step18_df is not None and not step18_df.empty:
        # Normalize Step 18 grouping key and merge on cluster_name
        print(f"  DEBUG: Step 18 data detected with {len(step18_df)} records and {len(step18_df.columns)} columns")
        # Prefer 'store_group'; if missing, rename from 'Store_Group_Name'
        if 'store_group' not in step18_df.columns:
            if 'Store_Group_Name' in step18_df.columns:
                step18_df = step18_df.rename(columns={'Store_Group_Name': 'store_group'})
                print("  DEBUG: Renamed Step 18 column 'Store_Group_Name' -> 'store_group'")
            else:
                print(f"  Step 18 data missing 'store_group'/'Store_Group_Name'; available columns: {list(step18_df.columns)[:20]}")
        
        if 'store_group' in step18_df.columns:
            # Clean key
            step18_df['store_group'] = step18_df['store_group'].astype(str).str.strip()
            # Aggregate key metrics by store group for integration
            step18_summary = step18_df.groupby('store_group').agg({
                'Sell_Through_Rate': 'mean',
                'Current_Sell_Through_Rate': 'mean',
                'Target_Sell_Through_Rate': 'mean',
                'Sell_Through_Improvement': 'mean',
                'Capacity_Utilization': 'mean',
                'Inventory_Velocity_Gain': 'mean'
            }).reset_index()
            step18_summary = step18_summary.rename(columns={'store_group': 'cluster_name'})
            print(f"  DEBUG: Step 18 summary groups: {step18_summary['cluster_name'].nunique()} unique cluster names")
            
            # Ensure merged_df has 'cluster_name' to join on
            if 'cluster_name' not in merged_df.columns:
                if 'Cluster_Name' in merged_df.columns:
                    merged_df = merged_df.rename(columns={'Cluster_Name': 'cluster_name'})
                    print("  DEBUG: Derived 'cluster_name' from 'Cluster_Name' for Step 18 merge")
                elif 'store_group' in merged_df.columns:
                    merged_df = merged_df.rename(columns={'store_group': 'cluster_name'})
                    print("  DEBUG: Derived 'cluster_name' from 'store_group' for Step 18 merge")
            
            if 'cluster_name' in merged_df.columns:
                merged_df['cluster_name'] = merged_df['cluster_name'].astype(str).str.strip()
                merged_df = pd.merge(merged_df, step18_summary, on='cluster_name', how='left')
                print(f"After Step 18 sell-through data merge: {len(merged_df)} records")
            else:
                print("  Cannot merge Step 18 data: 'cluster_name' not found or derivable in merged data")
        else:
            print("  Skipping Step 18 merge: required grouping key not present")

        # Fallback: if KPI coverage remains null, distribute group metrics to stores via Store_Codes_In_Group
        kpi_cols = ['Sell_Through_Rate','Current_Sell_Through_Rate','Target_Sell_Through_Rate','Sell_Through_Improvement','Inventory_Velocity_Gain']
        kpi_null = all((col not in merged_df.columns) or (merged_df[col].notna().sum() == 0) for col in kpi_cols)
        if kpi_null:
            print("  DEBUG: KPI fields missing after Step 18 merge; attempting store-level fallback from Step 18 input")
            try:
                s18 = step18_df.copy()
                if 'Store_Codes_In_Group' in s18.columns:
                    exp = []
                    for _, row in s18.iterrows():
                        codes = str(row['Store_Codes_In_Group']).replace(' ', ',').split(',')
                        # compute current ST fraction
                        cur = None
                        if 'Historical_ST_Frac' in s18.columns:
                            cur = pd.to_numeric(row.get('Historical_ST_Frac'), errors='coerce')
                        elif 'Historical_ST_Pct' in s18.columns:
                            cur = pd.to_numeric(row.get('Historical_ST_Pct'), errors='coerce')
                            if pd.notna(cur):
                                cur = cur / 100.0
                        elif 'Historical_Sell_Through_Rate' in s18.columns:
                            cur = pd.to_numeric(row.get('Historical_Sell_Through_Rate'), errors='coerce')
                            if pd.notna(cur) and cur > 1:
                                cur = cur / 100.0
                        for c in codes:
                            c = c.strip()
                            if not c:
                                continue
                            exp.append({'str_code': str(c), 'Current_Sell_Through_Rate': cur})
                    if exp:
                        exp_df = pd.DataFrame(exp)
                        merged_df = merged_df.merge(exp_df, on='str_code', how='left', suffixes=('', '_s18fb'))
                        # Coalesce current ST from fallback column
                        if 'Current_Sell_Through_Rate_s18fb' in merged_df.columns:
                            if 'Current_Sell_Through_Rate' not in merged_df.columns:
                                merged_df['Current_Sell_Through_Rate'] = merged_df['Current_Sell_Through_Rate_s18fb']
                            else:
                                merged_df['Current_Sell_Through_Rate'] = merged_df['Current_Sell_Through_Rate'].where(
                                    merged_df['Current_Sell_Through_Rate'].notna(), merged_df['Current_Sell_Through_Rate_s18fb']
                                )
                        # Use current as baseline Sell_Through_Rate and Target if still missing
                        if 'Sell_Through_Rate' not in merged_df.columns or merged_df['Sell_Through_Rate'].notna().sum() == 0:
                            merged_df['Sell_Through_Rate'] = merged_df['Current_Sell_Through_Rate']
                        if 'Target_Sell_Through_Rate' not in merged_df.columns or merged_df['Target_Sell_Through_Rate'].notna().sum() == 0:
                            merged_df['Target_Sell_Through_Rate'] = merged_df['Current_Sell_Through_Rate']
                        if 'Sell_Through_Improvement' not in merged_df.columns or merged_df['Sell_Through_Improvement'].notna().sum() == 0:
                            merged_df['Sell_Through_Improvement'] = 0.0
                        if 'Inventory_Velocity_Gain' not in merged_df.columns or merged_df['Inventory_Velocity_Gain'].notna().sum() == 0:
                            merged_df['Inventory_Velocity_Gain'] = 0.0
                        print("  DEBUG: Applied Step 18 store-level KPI fallback from group distributions")
            except Exception as e:
                print("  WARN: Failed Step 18 KPI fallback:", e)
    
    # Remove duplicate columns from the final merged dataframe
    # This includes columns with suffixes like .1, .2 that pandas adds during merges
    print(f"  DEBUG: Total columns before duplicate removal: {len(merged_df.columns)}")
    
    cols_to_drop = []
    
    # Identify columns with suffixes (like Store_Code.1, Cluster_ID.1, etc.)
    for col in merged_df.columns:
        if isinstance(col, str) and '.' in col:
            parts = col.split('.')
            if len(parts) > 1 and parts[-1].isdigit():
                base_name = '.'.join(parts[:-1])
                # If the base column exists, remove the suffixed version
                if base_name in merged_df.columns:
                    cols_to_drop.append(col)
    
    # Also remove columns with _x and _y suffixes that might cause duplicates after mapping
    for col in merged_df.columns:
        if isinstance(col, str) and (col.endswith('_x') or col.endswith('_y')):
            base_name = col[:-2]  # Remove _x or _y suffix
            # Check if there's a plain version of this column
            if base_name in merged_df.columns:
                cols_to_drop.append(col)
    
    if cols_to_drop:
        print(f"  Removing duplicate columns with suffixes: {cols_to_drop}")
        merged_df = merged_df.drop(columns=cols_to_drop)
    
    # Final safety check to remove any remaining truly duplicated columns
    duplicated_mask = merged_df.columns.duplicated()
    if duplicated_mask.any():
        print(f"  DEBUG: Found truly duplicated columns: {merged_df.columns[duplicated_mask].tolist()}")
        merged_df = merged_df.loc[:, ~duplicated_mask]
    
    print(f"  DEBUG: Final column count: {len(merged_df.columns)}")

    # ---- Canonicalization & Coalescing ----
    def _coalesce(dest: str, order: list):
        for src in order:
            if src in merged_df.columns:
                if dest in merged_df.columns:
                    merged_df[dest] = merged_df[dest].where(merged_df[dest].notna(), merged_df[src])
                else:
                    merged_df[dest] = merged_df[src]
        return dest

    # Ensure canonical 'cluster_id'
    if 'cluster_id' not in merged_df.columns:
        for cand in ['cluster_id_x', 'cluster_id_y', 'Cluster_ID', 'Cluster']:
            if cand in merged_df.columns:
                merged_df['cluster_id'] = merged_df[cand].astype(str).str.strip()
                break

    # Prepare canonical bases (will be filled by coalescing)
    for base in ['operational_tag','style_tag','capacity_tag','geographic_tag',
                 'fashion_allocation_ratio','basic_allocation_ratio','capacity_utilization_target',
                 'recommended_fashion_capacity','recommended_basic_capacity','total_recommended_capacity',
                 'seasonal_adjustment_factor','buffer_stock_percentage','priority_score','implementation_notes']:
        if base not in merged_df.columns:
            merged_df[base] = None

    # Prefer rules -> tags/strategies for merchandising fields
    _coalesce('operational_tag', ['operational_tag_rules','operational_tag_y','operational_tag_x','operational_tag'])
    _coalesce('style_tag', ['style_tag_rules','style_tag_y','style_tag_x','style_tag'])
    _coalesce('capacity_tag', ['capacity_tag_rules','capacity_tag_y','capacity_tag_x','capacity_tag'])
    _coalesce('geographic_tag', ['geographic_tag_rules','geographic_tag_y','geographic_tag_x','geographic_tag'])
    _coalesce('fashion_allocation_ratio', ['fashion_allocation_ratio_rules','fashion_allocation_ratio_y','fashion_allocation_ratio_x'])
    _coalesce('basic_allocation_ratio', ['basic_allocation_ratio_rules','basic_allocation_ratio_y','basic_allocation_ratio_x'])
    _coalesce('capacity_utilization_target', ['capacity_utilization_target_rules','capacity_utilization_target_y','capacity_utilization_target_x'])
    _coalesce('recommended_fashion_capacity', ['recommended_fashion_capacity_rules','recommended_fashion_capacity_y','recommended_fashion_capacity_x'])
    _coalesce('recommended_basic_capacity', ['recommended_basic_capacity_rules','recommended_basic_capacity_y','recommended_basic_capacity_x'])
    _coalesce('total_recommended_capacity', ['total_recommended_capacity_rules','total_recommended_capacity_y','total_recommended_capacity_x'])
    _coalesce('seasonal_adjustment_factor', ['seasonal_adjustment_factor_rules','seasonal_adjustment_factor_y','seasonal_adjustment_factor_x'])
    _coalesce('buffer_stock_percentage', ['buffer_stock_percentage_rules','buffer_stock_percentage_y','buffer_stock_percentage_x'])
    _coalesce('priority_score', ['priority_score_rules','priority_score_y','priority_score_x'])
    _coalesce('implementation_notes', ['implementation_notes_rules','implementation_notes_y','implementation_notes_x'])

    # KPIs: prefer Step 18 summary, then plugin
    for base, prefs in {
        'Sell_Through_Rate': ['Sell_Through_Rate'],
        'Current_Sell_Through_Rate': ['Current_Sell_Through_Rate'],
        'Target_Sell_Through_Rate': ['Target_Sell_Through_Rate'],
        'Sell_Through_Improvement': ['Sell_Through_Improvement'],
        'Inventory_Velocity_Gain': ['Inventory_Velocity_Gain'],
        'Actual_Capacity_Utilization': ['Capacity_Utilization'],
        'Actual_Fashion_Ratio': ['Fashion_Ratio'],
        'Actual_Basic_Ratio': ['Basic_Ratio'],
    }.items():
        if base not in merged_df.columns:
            merged_df[base] = None
        _coalesce(base, prefs)

    # Final KPI fallbacks to ensure coverage
    if 'Current_Sell_Through_Rate_s18fb' in merged_df.columns:
        merged_df['Current_Sell_Through_Rate'] = merged_df.get('Current_Sell_Through_Rate')
        merged_df['Current_Sell_Through_Rate'] = merged_df['Current_Sell_Through_Rate'].where(
            merged_df['Current_Sell_Through_Rate'].notna(), merged_df['Current_Sell_Through_Rate_s18fb']
        )
    # If Sell_Through_Rate missing, use Current; if Target missing, use Current
    if 'Sell_Through_Rate' in merged_df.columns:
        merged_df['Sell_Through_Rate'] = merged_df['Sell_Through_Rate'].where(
            merged_df['Sell_Through_Rate'].notna(), merged_df.get('Current_Sell_Through_Rate')
        )
    if 'Target_Sell_Through_Rate' in merged_df.columns:
        merged_df['Target_Sell_Through_Rate'] = merged_df['Target_Sell_Through_Rate'].where(
            merged_df['Target_Sell_Through_Rate'].notna(), merged_df.get('Sell_Through_Rate')
        )
    # Actuals fallback from recommended splits and targets if plugin missing
    if 'Actual_Capacity_Utilization' in merged_df.columns:
        merged_df['Actual_Capacity_Utilization'] = merged_df['Actual_Capacity_Utilization'].where(
            merged_df['Actual_Capacity_Utilization'].notna(), merged_df.get('capacity_utilization_target')
        )
    if 'Actual_Fashion_Ratio' in merged_df.columns:
        merged_df['Actual_Fashion_Ratio'] = merged_df['Actual_Fashion_Ratio'].where(
            merged_df['Actual_Fashion_Ratio'].notna(), merged_df.get('fashion_allocation_ratio')
        )
    if 'Actual_Basic_Ratio' in merged_df.columns:
        merged_df['Actual_Basic_Ratio'] = merged_df['Actual_Basic_Ratio'].where(
            merged_df['Actual_Basic_Ratio'].notna(), merged_df.get('basic_allocation_ratio')
        )

    # Ensure Capacity_Utilization (plugin) is populated for rename mapping
    if 'Capacity_Utilization' not in merged_df.columns or merged_df['Capacity_Utilization'].notna().sum() == 0:
        base_acu = merged_df.get('Actual_Capacity_Utilization', None)
        if base_acu is not None:
            merged_df['Capacity_Utilization'] = base_acu
        else:
            merged_df['Capacity_Utilization'] = merged_df.get('capacity_utilization_target')
    # Clamp utilization and ratios to [0,1]
    for col in ['Capacity_Utilization','Actual_Capacity_Utilization','Actual_Fashion_Ratio','Actual_Basic_Ratio','Sell_Through_Rate','Current_Sell_Through_Rate','Target_Sell_Through_Rate']:
        if col in merged_df.columns:
            merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce').clip(lower=0, upper=1)

    # Derive Store_Size_Tier if available from tags
    if 'Store_Size_Tier' not in merged_df.columns and 'size_tier' in merged_df.columns:
        merged_df['Store_Size_Tier'] = merged_df['size_tier']

    # Derive prioritization fields if absent
    import numpy as _np
    if 'Performance_Tier' not in merged_df.columns:
        sr = pd.to_numeric(merged_df.get('Sell_Through_Rate', pd.Series(0, index=merged_df.index)), errors='coerce').fillna(0)
        try:
            # Use quantiles when variance exists; allow duplicate edges
            if sr.nunique(dropna=True) >= 3:
                merged_df['Performance_Tier'] = pd.qcut(sr, q=3, labels=['Standard','Strong','Elite'], duplicates='drop')
            else:
                # Absolute thresholds fallback
                merged_df['Performance_Tier'] = pd.cut(sr, [-_np.inf, 0.4, 0.7, _np.inf], labels=['Standard','Strong','Elite'], include_lowest=True)
        except Exception:
            merged_df['Performance_Tier'] = pd.cut(sr, [-_np.inf, 0.4, 0.7, _np.inf], labels=['Standard','Strong','Elite'], include_lowest=True)
    if 'Growth_Potential' not in merged_df.columns:
        sti = pd.to_numeric(merged_df.get('Sell_Through_Improvement', pd.Series(0, index=merged_df.index)), errors='coerce').fillna(0)
        merged_df['Growth_Potential'] = pd.cut(sti, [-_np.inf, 0, 0.05, _np.inf], labels=['Maintain','Optimize','Accelerate'], include_lowest=True)
    if 'Risk_Level' not in merged_df.columns:
        ivg = pd.to_numeric(merged_df.get('Inventory_Velocity_Gain', pd.Series(0, index=merged_df.index)), errors='coerce').fillna(0)
        merged_df['Risk_Level'] = pd.cut(ivg, [-_np.inf, 0, 0.05, _np.inf], labels=['High-Risk','Medium-Risk','Low-Risk'], include_lowest=True)
    if 'Action_Priority' not in merged_df.columns:
        ps = pd.to_numeric(merged_df['priority_score'], errors='coerce').fillna(0)
        merged_df['Action_Priority'] = pd.cut(ps, [0,40,70,100], labels=['Monitor','Plan','Execute'], include_lowest=True)

    # ---- End Canonicalization ----

    # Select and rename relevant columns for final output
    # First, let's see what columns we actually have in the merged dataframe
    print(f"  DEBUG: Available columns in merged_df: {list(merged_df.columns)}")

    # Ensure canonical keys exist before mapping: create 'cluster_id' if only suffixed/alternate present
    if 'cluster_id' not in merged_df.columns:
        for cand in ['cluster_id_x', 'cluster_id_y', 'Cluster_ID', 'Cluster']:
            if cand in merged_df.columns:
                merged_df['cluster_id'] = merged_df[cand].astype(str).str.strip()
                break
    # Ensure canonical 'operational_tag', 'style_tag', 'capacity_tag', etc., by preferring _x over _y
    for base in ['operational_tag', 'style_tag', 'capacity_tag', 'geographic_tag',
                 'fashion_allocation_ratio', 'basic_allocation_ratio', 'capacity_utilization_target',
                 'recommended_fashion_capacity', 'recommended_basic_capacity', 'total_recommended_capacity',
                 'seasonal_adjustment_factor', 'buffer_stock_percentage', 'priority_score', 'implementation_notes']:
        if base not in merged_df.columns:
            if f"{base}_x" in merged_df.columns:
                merged_df[base] = merged_df[f"{base}_x"]
            elif f"{base}_y" in merged_df.columns:
                merged_df[base] = merged_df[f"{base}_y"]
    
    column_mapping = {
        # Store identification
        'str_code': 'Store_Code',
        'cluster_id': 'Cluster_ID',
        'cluster_name': 'Cluster_Name',
        'operational_tag': 'Operational_Tag',
        'temperature_zone': 'Temperature_Zone',
        'fashion_basic_classification': 'Fashion_Basic_Classification',
        'temperature_band': 'Temperature_Band',
        'avg_feels_like_temp': 'Avg_Feels_Like_Temp',
        
        # Merchandising rules and allocations
        'fashion_allocation_ratio': 'Fashion_Allocation_Ratio',
        'basic_allocation_ratio': 'Basic_Allocation_Ratio',
        'capacity_utilization_target': 'Capacity_Utilization_Target',
        'recommended_fashion_capacity': 'Recommended_Fashion_Capacity',
        'recommended_basic_capacity': 'Recommended_Basic_Capacity',
        'total_recommended_capacity': 'Total_Recommended_Capacity',
        'seasonal_adjustment_factor': 'Seasonal_Adjustment_Factor',
        'buffer_stock_percentage': 'Buffer_Stock_Percentage',
        'estimated_rack_capacity': 'Estimated_Rack_Capacity',
        'priority_score': 'Priority_Score',
        
        # Performance metrics from plugin output (only if they exist)
        'Store_Type': 'Store_Type',
        'Store_Size_Tier': 'Store_Size_Tier',
        'Sell_Through_Rate': 'Sell_Through_Rate',
        'Capacity_Utilization': 'Actual_Capacity_Utilization',
        'Fashion_Ratio': 'Actual_Fashion_Ratio',
        'Basic_Ratio': 'Actual_Basic_Ratio',
        'Performance_Tier': 'Performance_Tier',
        'Growth_Potential': 'Growth_Potential',
        'Risk_Level': 'Risk_Level',
        'Action_Priority': 'Action_Priority',
        
        # Step 18 sell-through metrics (if merged)
        'Current_Sell_Through_Rate': 'Current_Sell_Through_Rate',
        'Target_Sell_Through_Rate': 'Target_Sell_Through_Rate',
        'Sell_Through_Improvement': 'Sell_Through_Improvement',
        'Inventory_Velocity_Gain': 'Inventory_Velocity_Gain',
        
        # Additional tags
        'geographic_tag': 'Geographic_Tag',
        'style_tag': 'Style_Tag',
        'capacity_tag': 'Capacity_Tag',
        'implementation_notes': 'Implementation_Notes'
    }
    
    # Apply column mapping
    final_df = merged_df.rename(columns=column_mapping)
    
    # Remove any duplicate columns that might have been created during renaming
    # This can happen if multiple source columns map to the same target column
    final_df = final_df.loc[:, ~final_df.columns.duplicated()]
    
    # Select only the columns we want in the final output
    output_columns = list(column_mapping.values())
    available_columns = [col for col in output_columns if col in final_df.columns]
    
    # Remove duplicates from available_columns while preserving order
    seen = set()
    unique_available_columns = []
    for col in available_columns:
        if col not in seen:
            seen.add(col)
            unique_available_columns.append(col)
    
    result_df = final_df[unique_available_columns]

    # Collapse to one row per store deterministically
    if 'Store_Code' in result_df.columns:
        num_cols = [c for c in result_df.columns if pd.api.types.is_numeric_dtype(result_df[c])]
        obj_cols = [c for c in result_df.columns if c not in num_cols]
        agg_spec = {c: 'max' for c in num_cols}
        for c in obj_cols:
            if c != 'Store_Code':
                agg_spec[c] = 'first'
        result_df = result_df.groupby('Store_Code', as_index=False).agg(agg_spec)

    # Enforce types and required coverage
    if 'Cluster_ID' in result_df.columns:
        result_df['Cluster_ID'] = pd.to_numeric(result_df['Cluster_ID'], errors='coerce').fillna(-1).astype(int)

    cluster_col = 'Cluster_ID' if 'Cluster_ID' in result_df.columns else ('cluster_id' if 'cluster_id' in result_df.columns else None)
    if cluster_col:
        print(f"Final output: {len(result_df)} records with {result_df[cluster_col].nunique()} unique clusters")
    else:
        print(f"Final output: {len(result_df)} records")
    
    return result_df


def generate_summary_report(final_df: pd.DataFrame, period_label: str) -> str:
    """Generate a markdown summary report of the recommendations."""
    report = f"""# Store-Level Merchandising Recommendations Summary
Period: {period_label}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview
- Total Stores: {len(final_df)}
"""
    
    # Handle cluster information safely
    cluster_col = None
    for col in ['Cluster_ID', 'cluster_id']:
        if col in final_df.columns:
            cluster_col = col
            break
    
    if cluster_col not in final_df.columns:
        cluster_col = 'cluster_id'
    
    # Ensure the cluster column is 1-dimensional
    cluster_series = final_df[cluster_col]
    # Handle case where cluster_series might be a DataFrame or multi-dimensional
    if hasattr(cluster_series, 'iloc') and hasattr(cluster_series, 'values'):
        if len(cluster_series.values.shape) > 1:
            # If multi-dimensional, take the first column
            cluster_values = cluster_series.iloc[:, 0].values
        else:
            cluster_values = cluster_series.values
    else:
        cluster_values = cluster_series
    
    cluster_dist = pd.Series(cluster_values).value_counts().sort_index()
    cluster_summary = "\nCluster Distribution:\n" + "\n".join([f"  Cluster {k}: {v} stores" for k, v in cluster_dist.items()])
    
    if cluster_col:
        report += f"- Unique Clusters: {final_df[cluster_col].nunique()}\n\n{cluster_summary}"
    else:
        report += "- Unique Clusters: N/A\n\n## Cluster Distribution\n- No cluster data available\n"
    
    report += "\n## Data Quality Metrics\n"
    
    # Handle data quality metrics safely
    metrics = [
        ('Store_Type', 'Store_Type'),
        ('Temperature_Zone', 'Temperature_Zone'),
        ('Fashion_Allocation_Ratio', 'Fashion_Allocation_Ratio'),
        ('Geographic_Tag', 'Geographic_Tag')
    ]
    
    for metric_name, col_name in metrics:
        if col_name in final_df.columns:
            count = final_df[col_name].notna().sum()
            report += f"- Stores with {metric_name} data: {count}/{len(final_df)}\n"
        else:
            report += f"- Stores with {metric_name} data: N/A\n"
    
    report += "\n## Key Statistics\n"
    
    # Handle key statistics safely
    stats = [
        ('Capacity_Utilization_Target', 'Capacity_Utilization_Target'),
        ('Priority_Score', 'Priority_Score'),
        ('Sell_Through_Rate', 'Sell_Through_Rate'),
        ('Actual_Capacity_Utilization', 'Actual_Capacity_Utilization')
    ]
    
    for stat_name, col_name in stats:
        if col_name in final_df.columns and final_df[col_name].notna().sum() > 0:
            avg_val = final_df[col_name].mean()
            report += f"- Average {stat_name}: {avg_val:.4f}\n"
    
    return report


def register_outputs_in_manifest(yyyymm: str, period: str, csv_file: str, md_file: str, final_df: pd.DataFrame, extra_files: Optional[Dict[str, str]] = None):
    """Register the generated outputs in the pipeline manifest."""
    manifest_path = os.path.join(OUTPUT_DIR, "pipeline_manifest.json")
    
    # Load existing manifest
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    else:
        manifest = {}
    
    # Ensure steps section exists
    if 'steps' not in manifest:
        manifest['steps'] = {}
    if 'step35' not in manifest['steps']:
        manifest['steps']['step35'] = {}
    if 'outputs' not in manifest['steps']['step35']:
        manifest['steps']['step35']['outputs'] = {}
    
    period_label = get_period_label(yyyymm, period)
    
    # Register CSV output
    csv_key = f"store_level_merchandising_recommendations_{period_label}"
    manifest['steps']['step35']['outputs'][csv_key] = {
        "file_path": csv_file,
        "created": datetime.now().isoformat(),
        "exists": True,
        "size_mb": int(os.path.getsize(csv_file) / (1024 * 1024)),  # Convert to regular int
        "metadata": {
            "target_year": int(str(yyyymm)[:4]),
            "target_month": int(str(yyyymm)[4:]),
            "target_period": period,
            "period_label": period_label,
            "records": int(len(final_df)),  # Convert to regular int
            "columns": int(len(final_df.columns)),  # Convert to regular int
            "unique_clusters": len(set(final_df['Cluster_ID'].iloc[:, 0].values)) if 'Cluster_ID' in final_df.columns and len(final_df['Cluster_ID'].shape) > 1 else (len(set(final_df['Cluster_ID'].values)) if 'Cluster_ID' in final_df.columns else 0),
            "data_coverage": {
                "store_type": int(final_df['Store_Type'].notna().sum() if 'Store_Type' in final_df.columns else 0),  # Convert to regular int
                "temperature_zone": int(final_df['Temperature_Zone'].notna().sum() if 'Temperature_Zone' in final_df.columns else 0),  # Convert to regular int
                "fashion_allocation": int(final_df['Fashion_Allocation_Ratio'].notna().sum() if 'Fashion_Allocation_Ratio' in final_df.columns else 0)  # Convert to regular int
            }
        }
    }
    # Also register generic CSV key
    manifest['steps']['step35']['outputs']["store_level_merchandising_recommendations"] = {
        "file_path": csv_file,
        "created": datetime.now().isoformat(),
        "exists": True,
        "size_mb": int(os.path.getsize(csv_file) / (1024 * 1024)),
        "metadata": {
            "target_year": int(str(yyyymm)[:4]),
            "target_month": int(str(yyyymm)[4:]),
            "target_period": period,
            "period_label": period_label,
            "records": int(len(final_df)),
            "columns": int(len(final_df.columns)),
            "unique_clusters": len(set(final_df['Cluster_ID'].iloc[:, 0].values)) if 'Cluster_ID' in final_df.columns and len(final_df['Cluster_ID'].shape) > 1 else (len(set(final_df['Cluster_ID'].values)) if 'Cluster_ID' in final_df.columns else 0),
        }
    }
    
    # Register MD output
    md_key = f"store_level_merchandising_summary_{period_label}"
    manifest['steps']['step35']['outputs'][md_key] = {
        "file_path": md_file,
        "created": datetime.now().isoformat(),
        "exists": True,
        "size_mb": int(os.path.getsize(md_file) / (1024 * 1024)),  # Convert to regular int
        "metadata": {
            "target_year": int(str(yyyymm)[:4]),
            "target_month": int(str(yyyymm)[4:]),
            "target_period": period,
            "period_label": period_label,
            "records": int(len(final_df)),  # Convert to regular int
            "columns": int(len(final_df.columns)),  # Convert to regular int
            "unique_clusters": len(set(final_df['Cluster_ID'].iloc[:, 0].values)) if 'Cluster_ID' in final_df.columns and len(final_df['Cluster_ID'].shape) > 1 else (len(set(final_df['Cluster_ID'].values)) if 'Cluster_ID' in final_df.columns else 0)
        }
    }
    # Also register generic MD key
    manifest['steps']['step35']['outputs']["store_level_merchandising_summary"] = {
        "file_path": md_file,
        "created": datetime.now().isoformat(),
        "exists": True,
        "size_mb": int(os.path.getsize(md_file) / (1024 * 1024)),
        "metadata": {
            "target_year": int(str(yyyymm)[:4]),
            "target_month": int(str(yyyymm)[4:]),
            "target_period": period,
            "period_label": period_label,
            "records": int(len(final_df)),
            "columns": int(len(final_df.columns)),
        }
    }
    
    # Register any additional artifacts (optional)
    if extra_files:
        for key, path in extra_files.items():
            manifest['steps']['step35']['outputs'][key] = {
                "file_path": path,
                "created": datetime.now().isoformat(),
                "exists": os.path.exists(path),
                "size_mb": int(os.path.getsize(path) / (1024 * 1024)) if os.path.exists(path) else 0,
                "metadata": {
                    "target_year": int(str(yyyymm)[:4]),
                    "target_month": int(str(yyyymm)[4:]),
                    "target_period": period,
                    "period_label": period_label,
                    "records": int(len(final_df)),
                    "columns": int(len(final_df.columns))
                }
            }
    
    # Write updated manifest
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)


def generate_cluster_summary(final_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate store-level recommendations by cluster to produce a cluster summary."""
    # Choose cluster column flexibly
    cluster_col = 'Cluster_ID' if 'Cluster_ID' in final_df.columns else ('cluster_id' if 'cluster_id' in final_df.columns else None)
    if not cluster_col:
        return pd.DataFrame()
    # Candidate numeric columns to average if present
    candidates = [
        'Capacity_Utilization_Target',
        'Priority_Score',
        'Sell_Through_Rate',
        'Actual_Capacity_Utilization',
        'Fashion_Allocation_Ratio',
        'Basic_Allocation_Ratio',
        'Estimated_Rack_Capacity',
        'Current_Sell_Through_Rate',
        'Target_Sell_Through_Rate',
        'Sell_Through_Improvement',
        'Inventory_Velocity_Gain'
    ]
    present = [c for c in candidates if c in final_df.columns]
    agg_spec: Dict[str, str] = {col: 'mean' for col in present}
    summary = final_df.groupby(cluster_col).agg(agg_spec)
    summary['Store_Count'] = final_df.groupby(cluster_col).size()
    summary = summary.reset_index()
    # Move Store_Count next to cluster col
    cols = [cluster_col, 'Store_Count'] + [c for c in summary.columns if c not in [cluster_col, 'Store_Count']]
    return summary[cols]


def build_nested_by_cluster(final_df: pd.DataFrame) -> Dict:
    """Build nested JSON of store recommendations grouped by cluster."""
    cluster_col = 'Cluster_ID' if 'Cluster_ID' in final_df.columns else ('cluster_id' if 'cluster_id' in final_df.columns else None)
    if not cluster_col:
        return {"clusters": {}, "cluster_count": 0, "store_count": int(len(final_df))}
    # Select a concise set of fields for each store
    preferred_fields = [
        'Store_Code', 'Operational_Tag', 'Fashion_Allocation_Ratio', 'Basic_Allocation_Ratio',
        'Capacity_Utilization_Target', 'Estimated_Rack_Capacity', 'Priority_Score',
        'Sell_Through_Rate', 'Actual_Capacity_Utilization',
        'Current_Sell_Through_Rate', 'Target_Sell_Through_Rate', 'Sell_Through_Improvement', 'Inventory_Velocity_Gain'
    ]
    fields = [f for f in preferred_fields if f in final_df.columns]
    clusters: Dict[str, List[Dict]] = {}
    for cid, group in final_df.groupby(cluster_col):
        clusters[str(cid)] = group[fields].to_dict(orient='records') if fields else group.to_dict(orient='records')
    return {"clusters": clusters, "cluster_count": int(len(clusters)), "store_count": int(len(final_df))}


def generate_schema_info(final_df: pd.DataFrame) -> Dict:
    """Generate a JSON-serializable schema summary for the final dataframe."""
    schema = []
    for col in final_df.columns:
        s = final_df[col]
        try:
            sample_vals = s.dropna().astype(str).unique().tolist()[:5]
        except Exception:
            sample_vals = []
        schema.append({
            "name": col,
            "dtype": str(s.dtype),
            "non_nulls": int(s.notna().sum()),
            "nulls": int(s.isna().sum()),
            "unique": int(s.nunique(dropna=True)),
            "sample": sample_vals
        })
    return {"records": int(len(final_df)), "columns": int(len(final_df.columns)), "schema": schema}


def run_data_quality_checks(final_df: pd.DataFrame) -> Dict:
    """Run basic QA checks and return warnings/errors."""
    warnings: List[str] = []
    errors: List[str] = []

    # Duplicate column names
    seen = set()
    dup_cols = []
    for c in final_df.columns:
        if c in seen:
            dup_cols.append(c)
        seen.add(c)
    if dup_cols:
        warnings.append(f"Duplicate columns detected after processing: {dup_cols}")

    # Residual _x/_y columns
    suf_cols = [c for c in final_df.columns if isinstance(c, str) and (c.endswith('_x') or c.endswith('_y'))]
    if suf_cols:
        warnings.append(f"Residual suffix columns remain: {suf_cols}")

    # Step 18 fields presence (soft requirement)
    step18_fields = [
        'Current_Sell_Through_Rate', 'Target_Sell_Through_Rate',
        'Sell_Through_Improvement', 'Inventory_Velocity_Gain'
    ]
    missing = [f for f in step18_fields if f not in final_df.columns]
    if missing:
        warnings.append(f"Step 18 fields missing (may be expected if Step 18 not available): {missing}")

    # Cluster coverage
    cluster_col = 'Cluster_ID' if 'Cluster_ID' in final_df.columns else ('cluster_id' if 'cluster_id' in final_df.columns else None)
    if cluster_col:
        missing_clusters = int(final_df[cluster_col].isna().sum())
        if missing_clusters > 0:
            warnings.append(f"Rows missing cluster id: {missing_clusters}")
    else:
        errors.append("Cluster column missing in final output")

    return {"warnings": warnings, "errors": errors, "warning_count": len(warnings), "error_count": len(errors)}


def create_additional_outputs(period_label: str, final_df: pd.DataFrame) -> Dict[str, str]:
    """Create cluster summary CSV, nested JSON, schema JSON, and QA validation JSON."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Cluster summary CSV
    cluster_summary_df = generate_cluster_summary(final_df)
    cluster_csv = os.path.join(OUTPUT_DIR, f"store_level_merchandising_cluster_summary_{period_label}.csv")
    if not cluster_summary_df.empty:
        cluster_summary_df.to_csv(cluster_csv, index=False)
    else:
        # Ensure file exists even if empty
        pd.DataFrame().to_csv(cluster_csv, index=False)

    # Nested-by-cluster JSON
    nested_obj = build_nested_by_cluster(final_df)
    nested_json = os.path.join(OUTPUT_DIR, f"store_level_merchandising_by_cluster_{period_label}.json")
    with open(nested_json, 'w', encoding='utf-8') as f:
        json.dump(nested_obj, f, indent=2, ensure_ascii=False)

    # Schema JSON
    schema_obj = generate_schema_info(final_df)
    schema_json = os.path.join(OUTPUT_DIR, f"store_level_merchandising_recommendations_{period_label}_schema.json")
    with open(schema_json, 'w', encoding='utf-8') as f:
        json.dump(schema_obj, f, indent=2, ensure_ascii=False)

    # QA validation JSON
    qa_obj = run_data_quality_checks(final_df)
    qa_json = os.path.join(OUTPUT_DIR, f"store_level_merchandising_recommendations_{period_label}_qavalidation.json")
    with open(qa_json, 'w', encoding='utf-8') as f:
        json.dump(qa_obj, f, indent=2, ensure_ascii=False)

    # Return period-aware manifest keys mapping to file paths
    return {
        f"cluster_summary_{period_label}": cluster_csv,
        f"nested_recommendations_by_cluster_{period_label}": nested_json,
        f"schema_store_level_merchandising_{period_label}": schema_json,
        f"qavalidation_store_level_merchandising_{period_label}": qa_json,
    }


def verify_outputs_and_manifest(yyyymm: str, period: str, paths: Dict[str, str]) -> None:
    """Print verification of file existence and manifest registrations for this period."""
    period_label = get_period_label(yyyymm, period)
    missing_files = [name for name, p in paths.items() if not os.path.exists(p)]
    if missing_files:
        print(f"[WARN] Missing files for {period_label}: {missing_files}")
    else:
        print(f"[INFO] All files exist for {period_label}")

    # Verify manifest registrations
    manifest_path = os.path.join(OUTPUT_DIR, "pipeline_manifest.json")
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        outputs = manifest.get('steps', {}).get('step35', {}).get('outputs', {})
        expected_keys = [
            f"store_level_merchandising_recommendations_{period_label}",
            f"store_level_merchandising_summary_{period_label}",
            f"cluster_summary_{period_label}",
            f"nested_recommendations_by_cluster_{period_label}",
            f"schema_store_level_merchandising_{period_label}",
            f"qavalidation_store_level_merchandising_{period_label}"
        ]
        missing_keys = [k for k in expected_keys if k not in outputs]
        if missing_keys:
            print(f"[WARN] Missing manifest entries for {period_label}: {missing_keys}")
        else:
            print(f"[INFO] Manifest includes all expected entries for {period_label}")
    except Exception as e:
        print(f"[WARN] Could not verify manifest for {period_label}: {e}")


def generate_merchandising_recommendations(yyyymm: str, period: str) -> Tuple[str, str]:
    """Generate comprehensive store-level merchandising recommendations for deployment"""
    period_label = get_period_label(yyyymm, period)
    print(f"[INFO] Starting Step 35: Merchandising Strategy Deployment Preparation for {period_label}")

    # Load all required input files
    print(f"[INFO] Loading store-level merchandising rules for {period_label}...")
    store_rules_df = load_merchandising_rules(yyyymm, period)
    print(f"[INFO] Loaded {len(store_rules_df):,} store-level rules")

    print(f"[INFO] Loading store-level plugin output for {yyyymm}...")
    plugin_output_df = load_plugin_output(yyyymm, period)
    print(f"[INFO] Loaded {len(plugin_output_df):,} store records from plugin output")

    print(f"[INFO] Loading cluster strategies for {period_label}...")
    cluster_strategies_df = load_cluster_strategies(yyyymm, period)
    print(f"[INFO] Loaded {len(cluster_strategies_df):,} cluster strategies")

    print(f"[INFO] Loading Step 18 sell-through data for {period_label}...")
    step18_df = load_step18_sell_through_data(yyyymm, period)
    print(f"[INFO] Loaded Step 18 rows: {len(step18_df):,}" if not step18_df.empty else "[WARN] No Step 18 data found; proceeding without sell-through metrics")

    # Create comprehensive recommendations
    print(f"[INFO] Creating comprehensive store-level recommendations...")
    store_tags_df = load_store_tags(yyyymm, period)
    weather_df = load_weather_data()
    # Provide globals to allow enriched attributes loader to resolve period
    global TARGET_YYYYMM, TARGET_PERIOD
    TARGET_YYYYMM, TARGET_PERIOD = yyyymm, period
    final_df = create_comprehensive_store_recommendations(store_tags_df, weather_df, store_rules_df, cluster_strategies_df, plugin_output_df, step18_df)
    print(f"[INFO] Generated {len(final_df):,} comprehensive recommendations")

    # DUAL OUTPUT PATTERN - Save both timestamped and generic versions
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Define file paths
    timestamped_csv_filename = f"store_level_merchandising_recommendations_{period_label}_{ts}.csv"
    timestamped_csv_path = os.path.join(OUTPUT_DIR, timestamped_csv_filename)
    generic_csv_path = os.path.join(OUTPUT_DIR, "store_level_merchandising_recommendations.csv")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save timestamped version (for backup/inspection)
    final_df.to_csv(timestamped_csv_path, index=False)
    print(f"[INFO] Saved timestamped recommendations CSV: {timestamped_csv_path}")
    
    # Save generic version (for pipeline flow)
    if os.path.exists(generic_csv_path) or os.path.islink(generic_csv_path):
        os.remove(generic_csv_path)
    os.symlink(os.path.basename(timestamped_csv_path), generic_csv_path)
    print(f"[INFO] Saved generic recommendations CSV: {generic_csv_path}")

    # Create and save summary report (DUAL OUTPUT PATTERN)
    print(f"[INFO] Creating summary report...")
    report_content = generate_summary_report(final_df, period_label)
    
    timestamped_report_filename = f"store_level_merchandising_summary_{period_label}_{ts}.md"
    timestamped_report_path = os.path.join(OUTPUT_DIR, timestamped_report_filename)
    generic_report_path = os.path.join(OUTPUT_DIR, "store_level_merchandising_summary.md")
    
    # Use timestamped path for manifest registration
    csv_path = timestamped_csv_path
    report_path = timestamped_report_path
    
    # Save timestamped version (for backup/inspection)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    print(f"[INFO] Saved timestamped summary report: {report_path}")
    
    # Save generic version (for pipeline flow)
    with open(generic_report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    print(f"[INFO] Saved generic summary report: {generic_report_path}")

    # Generate additional artifacts
    extra_files = create_additional_outputs(period_label, final_df)

    # Register outputs in manifest
    print(f"[INFO] Registering outputs in pipeline manifest...")
    register_outputs_in_manifest(yyyymm, period, csv_path, report_path, final_df, extra_files=extra_files)

    # Verify outputs and manifest
    verify_map = {"csv": csv_path, "md": report_path}
    verify_map.update(extra_files)
    verify_outputs_and_manifest(yyyymm, period, verify_map)

    print(f"[INFO] Step 35 completed successfully for {period_label}!")
    return csv_path, report_path


def main(argv=None):
    """Main function to run the merchandising strategy deployment pipeline."""
    print("DEBUG: Starting Step 35 main function...")
    print(f"DEBUG: Arguments received: {argv}")

    parser = argparse.ArgumentParser(description='Generate store-level merchandising recommendations')
    parser.add_argument('--target-yyyymm', required=True, help='Target year-month (YYYYMM)')
    parser.add_argument('--target-period', required=True, help='Target period (A or B)')

    print("DEBUG: About to parse arguments...")
    args = parser.parse_args(argv)
    print(f"DEBUG: Parsed arguments: target_yyyymm={args.target_yyyymm}, target_period={args.target_period}")

    yyyymm = args.target_yyyymm
    period = args.target_period
    print(f"DEBUG: Variables set: yyyymm={yyyymm}, period={period}")

    print(f"Step 35: Generating merchandising recommendations for {yyyymm} periods {period}")
    print("Integrating real data from all 34 previous pipeline steps...")

    for period in [period]:
        try:
            period_label = get_period_label(yyyymm, period)
            print(f"\nProcessing period: {period_label}")

            # Load all required real data sources from previous pipeline steps
            print("Loading real store tags with clustering data from Step 6...")
            store_tags_df = load_store_tags(yyyymm, period)

            print("Loading real weather data from Step 5...")
            weather_df = load_weather_data()

            print("Loading real merchandising rules from Step 32...")
            merch_rules_df = load_merchandising_rules(yyyymm, period)

            print("Loading real cluster strategies from Step 33...")
            cluster_strategies_df = load_cluster_strategies(yyyymm, period)

            print("Loading real performance metrics from plugin output...")
            plugin_output_df = load_plugin_output(yyyymm, period)

            print("Loading Step 18 sell-through analysis data...")
            step18_df = load_step18_sell_through_data(yyyymm, period)

            # Provide globals to allow downstream loaders to resolve exact period
            global TARGET_YYYYMM, TARGET_PERIOD
            TARGET_YYYYMM, TARGET_PERIOD = yyyymm, period

            # Create comprehensive recommendations using ALL real data
            final_df = create_comprehensive_store_recommendations(
                store_tags_df, weather_df, merch_rules_df, cluster_strategies_df, plugin_output_df, step18_df
            )

            # Generate output files with dual output pattern
            base_path = os.path.join(OUTPUT_DIR, "store_level_merchandising_recommendations")
            timestamped_file, period_file, generic_file = create_output_with_symlinks(
                df=final_df,
                base_path=base_path,
                period_label=period_label
            )
            csv_file = timestamped_file  # Use timestamped file for manifest registration
            print(f"CSV output saved with dual output pattern:")
            print(f"  Timestamped: {timestamped_file}")
            print(f"  Period: {period_file}")
            print(f"  Generic: {generic_file}")
            
            # Generate summary report (keep as timestamped only)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            md_file = os.path.join(OUTPUT_DIR, f"store_level_merchandising_summary_{period_label}_{ts}.md")

            summary_report = generate_summary_report(final_df, period_label)
            with open(md_file, 'w') as f:
                f.write(summary_report)
            print(f"Summary report saved to: {md_file}")

            # Generate additional artifacts
            extra_files = create_additional_outputs(period_label, final_df)

            # Register outputs in manifest (including extra artifacts)
            register_outputs_in_manifest(yyyymm, period, csv_file, md_file, final_df, extra_files=extra_files)
            print(f"Outputs registered in manifest for period {period_label}")

            # Verify outputs and manifest
            verify_map = {"csv": csv_file, "md": md_file}
            verify_map.update(extra_files)
            verify_outputs_and_manifest(yyyymm, period, verify_map)

        except Exception as e:
            print(f"Error processing period {period}: {str(e)}")
            raise

    print("\nStep 35 completed successfully with ALL real pipeline data!")


if __name__ == "__main__":
    main()
