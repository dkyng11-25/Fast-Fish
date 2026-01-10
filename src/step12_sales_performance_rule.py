#!/usr/bin/env python3
"""
Step 12: Sales Performance Rule with UNIT QUANTITY INCREASE RECOMMENDATIONS

This step identifies sales opportunities by comparing each store's category performance
against cluster top performers and provides specific UNIT QUANTITY increase recommendations
to close performance gaps.

ENHANCEMENT: Now includes actual unit quantity increase using real sales data!

Features:
- Multi-Level Analysis: Subcategory and SPU-level analysis
- Opportunity gap analysis vs cluster top quartile performers
- 🎯 UNIT QUANTITY INCREASE (e.g., "Increase 15 units to close performance gap")
- Real sales data integration for accurate quantity calculations
- 5-level performance classification for sales prioritization
- Store-level aggregation via average Z-scores across categories
- Sales team focused insights and recommendations

Author: Data Pipeline
Date: 2025-01-02 (Enhanced with Quantity Increases)

 HOW TO RUN (CLI + ENV) — Read this before executing
 ----------------------------------------------------
 Overview
 - Period-aware: Step 12 measures store performance vs. top cluster performers for a specific half-month, and produces incremental unit quantity recommendations.
 - Why source period correctness matters: store/cluster peer comparisons must reference the same period’s SPU metrics; mixing periods yields inaccurate gaps.

 Quick Start (target 202510A planning, source 202509A)
 - Use your config’s source period env (e.g., PIPELINE_YYYYMM/PIPELINE_PERIOD) to load 202509A SPU/config files while downstream steps label for 202510A.
   Command:
     PYTHONPATH=. python3 src/step12_sales_performance_rule.py

 Single-Cluster Testing vs Production
 - Test: Run recent files for only one cluster (e.g., Cluster 22) to validate logic; Step 12 will still compute store×SPU/category results for the subset.
 - Production: Ensure recent-window files (≥ 3 half-months) and clustering cover ALL stores for stable quartile ranks and adoption rates.

 Why these configurations work (and when they don't)
 - Real per-SPU quantities and unit prices enable meaningful incremental targets and investment math. If quantity columns are missing, unit price and quantity gaps can’t be computed.
 - Recent-window averaging and optional seasonal blending reduce noise and seasonal skew; without enough files, quartile thresholds may be unstable.

 Common failure modes (and what to do)
 - "No configuration/quantity data available after recent averaging/blending"
   • Cause: config couldn’t resolve period-specific `store_config`/`spu_sales` files for the source period.
   • Fix: verify Step 1 outputs exist for the half-month(s) and env variables are set so src.config resolves them.
 - Missing `sty_sal_amt` or SPU JSON expansion fails (SPU mode)
   • Cause: upstream `store_config` lacked the JSON or schema differs.
   • Fix: re-run Step 1 ensuring `sty_sal_amt` is present; confirm `get_api_data_files` points to the correct period-specific file.
 - Cluster join yields many NA clusters
   • Cause: cluster file missing or schema mismatch (`Cluster`/`cluster`).
   • Fix: provide the period-correct clustering file with ['str_code','Cluster'] or ['str_code','cluster'] and ensure `str_code` is string-typed across files.

 Manifest notes
 - Register Step 12 outputs in the manifest so Steps 13/14/17 resolve the correct files for the same planning period. Avoid hardcoded paths to prevent wrong-period inputs.
"""

"""
🎯 NOW USES REAL QUANTITY DATA FROM API!

This step has been updated to use real quantities and unit prices extracted
from the API data instead of treating sales amounts as quantities.

Key improvements:
- Real unit quantities from base_sal_qty and fashion_sal_qty API fields
- Realistic unit prices calculated from API data ($20-$150 range)
- Meaningful investment calculations (quantity_change × unit_price)
- No more fake $1.00 unit prices!
"""

import pandas as pd
import numpy as np
import os
import json
import gc
import argparse
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from tqdm import tqdm
import warnings

from src.pipeline_manifest import register_step_output
from src.config import get_output_files, get_current_period, get_api_data_files
from src.output_utils import create_output_with_symlinks

# FAST FISH ENHANCEMENT: Import sell-through validation
try:
    from src.sell_through_validator import SellThroughValidator, load_historical_data_for_validation
    SELLTHROUGH_VALIDATION_AVAILABLE = True
    print("✅ Fast Fish sell-through validation: ENABLED")
except ImportError:
    SELLTHROUGH_VALIDATION_AVAILABLE = False
    print("⚠️ Fast Fish sell-through validation: DISABLED (validator not found)")

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# Configuration - Analysis Level Selection
# ANALYSIS_LEVEL = "subcategory"  # Options: "subcategory", "spu"
ANALYSIS_LEVEL = "spu"  # Uncomment for SPU-level analysis

# SEASONAL BLENDING ENHANCEMENT: Flag/env-driven blending with recent averaging
# IMPORTANT: Distinguish between SOURCE period (data we analyze) and TARGET period (label for outputs)
# - SOURCE comes from PIPELINE_YYYYMM/PIPELINE_PERIOD (or falls back to TARGET if not set)
# - TARGET comes from PIPELINE_TARGET_YYYYMM/PIPELINE_TARGET_PERIOD (may be set via CLI flags later)
source_yyyymm = os.environ.get("PIPELINE_YYYYMM", os.environ.get("PIPELINE_TARGET_YYYYMM", "202508"))
source_period = os.environ.get("PIPELINE_PERIOD", os.environ.get("PIPELINE_TARGET_PERIOD", "A"))
SOURCE_PERIOD_LABEL = f"{source_yyyymm}{source_period}"

target_yyyymm_env = os.environ.get("PIPELINE_TARGET_YYYYMM", source_yyyymm)
target_period_env = os.environ.get("PIPELINE_TARGET_PERIOD", source_period)
target_period_label = f"{target_yyyymm_env}{target_period_env}"

# Default: ENABLE seasonal blending with weights 0.7 recent / 0.3 seasonal unless disabled
USE_BLENDED_SEASONAL = os.environ.get("SEASONAL_BLENDING", "1") not in ("0", "false", "False")
SEASONAL_WEIGHT_ENV = os.environ.get("SEASONAL_WEIGHT", "0.3")

# DATA PERIOD CONFIGURATION - CRITICAL FOR ACCURATE RECOMMENDATIONS
DATA_PERIOD_DAYS = 15  # API data is for half month (15 days)
TARGET_PERIOD_DAYS = 15  # Recommendations should be for same period (15 days)
SCALING_FACTOR = TARGET_PERIOD_DAYS / DATA_PERIOD_DAYS  # 1.0 for same period

# Analysis configurations
ANALYSIS_CONFIGS = {
    "subcategory": {
        "cluster_file": "output/clustering_results_subcategory.csv",
        "data_file": f"data/api_data/complete_category_sales_{target_period_label}.csv",
        "output_prefix": "rule12_subcategory_sales_performance",
        "grouping_columns": ['sub_cate_name'],
        "sales_column": "sal_amt"
    },
    "spu": {
        "cluster_file": "output/clustering_results_spu.csv", 
        "data_file": f"data/api_data/store_config_{target_period_label}.csv",
        "output_prefix": "rule12_sales_performance_spu",
        "grouping_columns": ['season_name', 'sex_name', 'display_location_name', 'big_class_name', 'sub_cate_name', 'spu_code'],
        "sales_column": "spu_sales"
    }
}

# QUANTITY ENHANCEMENT: Quantity path resolved via get_api_data_files in load_data (SOURCE period)
QUANTITY_DATA_FILE = None

# Configuration
CLUSTER_RESULTS_FILE = ANALYSIS_CONFIGS[ANALYSIS_LEVEL]["cluster_file"]
CATEGORY_SALES_FILE = ANALYSIS_CONFIGS[ANALYSIS_LEVEL]["data_file"]
OUTPUT_DIR = "output"
RESULTS_FILE = f"output/{ANALYSIS_CONFIGS[ANALYSIS_LEVEL]['output_prefix']}_results.csv"

# Rule parameters - Sales team focused opportunity analysis - Adapted for analysis level
if ANALYSIS_LEVEL == "subcategory":
    TOP_QUARTILE_PERCENTILE = 75  # Compare against 75th percentile performers
    MIN_CLUSTER_SIZE = 3         # Minimum stores in cluster for valid analysis
    MIN_SALES_VOLUME = 1         # Minimum sales to consider (avoid noise)
    # QUANTITY THRESHOLDS for subcategory performance improvement
    MIN_INCREASE_QUANTITY = 2.0  # Minimum units to recommend increasing
    MAX_INCREASE_PERCENTAGE = 0.5  # Max 50% increase for practical implementation
else:  # SPU level - SANITY ADJUSTED THRESHOLDS FOR REALISTIC RECOMMENDATIONS
    TOP_QUARTILE_PERCENTILE = 75  # Compare against 75th percentile (more realistic than 90th)
    MIN_CLUSTER_SIZE = 3         # Minimum stores in cluster for valid analysis (reduced from 8 for more opportunities)
    MIN_SALES_VOLUME = 50        # Minimum sales to consider (reduced from 100 for more inclusivity)
    # QUANTITY THRESHOLDS for SPU performance improvement - tuned for actionable but realistic output
    MIN_INCREASE_QUANTITY = 0.10  # Minimum units to recommend increasing (reduced from 0.25 for more inclusivity)
    MAX_INCREASE_PERCENTAGE = 0.75  # Allow up to 75% increase relative to current qty

# VERY RELAXED CONTROLS: Prioritize actionable recommendations
# No artificial caps by default; both can be provided via CLI if desired
MAX_RECOMMENDATIONS_PER_STORE = None   # None = no cap
MAX_TOTAL_QUANTITY_PER_STORE = None    # None = no cap on total units per store
MIN_OPPORTUNITY_SCORE = 0.05  # Minimum opportunity score (reduced from 0.10 for more inclusivity)
MIN_INVESTMENT_THRESHOLD = 15   # Minimum investment per recommendation (¥15, reduced from ¥30 for more inclusivity)
MIN_Z_SCORE_THRESHOLD = 0.5   # Only recommend for Z-score > 0.5 (reduced from 0.8 for more inclusivity)
JOIN_MODE = "left"  # Inclusive by default; allow 'inner' for stricter precision

# Performance classification thresholds (Z-score based) - Adapted for analysis level
if ANALYSIS_LEVEL == "subcategory":
    PERFORMANCE_THRESHOLDS = {
        'top_performer': -1.0,       # Exceeding top quartile (Z < -1.0)
        'performing_well': 0.0,      # Meeting expectations (-1.0 ≤ Z ≤ 0)
        'some_opportunity': 1.0,     # Minor potential (0 < Z ≤ 1.0)
        'good_opportunity': 2.5,     # Solid potential (1.0 < Z ≤ 2.5)
        'major_opportunity': float('inf')  # Huge potential (Z > 2.5)
    }
else:  # SPU level - more selective thresholds
    PERFORMANCE_THRESHOLDS = {
        'top_performer': -0.5,       # Exceeding top quartile (Z < -0.5)
        'performing_well': 0.5,      # Meeting expectations (-0.5 ≤ Z ≤ 0.5) 
        'some_opportunity': 1.5,     # Minor potential (0.5 < Z ≤ 1.5) - No action
        'good_opportunity': 2.5,     # Solid potential (1.5 < Z ≤ 2.5) - Action needed
        'major_opportunity': float('inf')  # Huge potential (Z > 2.5) - Priority action
    }

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def _read_csvs(path: Optional[str], usecols: Optional[List[str]] = None) -> pd.DataFrame:
    if not path:
        return pd.DataFrame()
    try:
        return pd.read_csv(path, low_memory=False, usecols=usecols, dtype={'str_code': str})
    except Exception:
        return pd.DataFrame()

def _infer_group_cols(df: pd.DataFrame, data_type: str) -> List[str]:
    # Heuristics: identify keys based on expected schemas
    if data_type == "config":
        keys = ['str_code','season_name','sex_name','display_location_name','big_class_name','sub_cate_name']
    else:
        keys = ['str_code','spu_code']
    return [c for c in keys if c in df.columns]

def _infer_value_cols(df: pd.DataFrame, data_type: str) -> List[str]:
    if data_type == "config":
        candidates = ['spu_sales','sal_amt','spu_sales_amt']
    else:
        candidates = ['quantity','base_sal_qty','fashion_sal_qty','spu_sales_amt']
    cols = [c for c in candidates if c in df.columns]
    # Include numeric columns that are not keys
    key_cols = _infer_group_cols(df, data_type)
    numeric_auto = [c for c in df.select_dtypes(include=[np.number]).columns if c not in key_cols]
    for c in numeric_auto:
        if c not in cols:
            cols.append(c)
    return cols

def _coerce_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def average_recent_dataframe(frames: List[pd.DataFrame], data_type: str) -> pd.DataFrame:
    valid = [f for f in frames if isinstance(f, pd.DataFrame) and len(f) > 0]
    if len(valid) == 0:
        return pd.DataFrame()
    df_all = pd.concat(valid, ignore_index=True)
    group_cols = _infer_group_cols(df_all, data_type)
    val_cols = _infer_value_cols(df_all, data_type)
    df_all = _coerce_numeric(df_all, val_cols)
    if not group_cols or not val_cols:
        return df_all.drop_duplicates()
    averaged = (
        df_all
        .groupby(group_cols, dropna=False)[val_cols]
        .mean()
        .reset_index()
    )
    # Preserve JSON-like detail fields for config (e.g., 'sty_sal_amt') from the most recent frame
    if data_type == "config" and group_cols:
        json_cols = ['sty_sal_amt']
        latest = frames[0] if len(frames) > 0 else None
        if latest is not None:
            keep = [c for c in json_cols if c in latest.columns]
            if keep:
                attach = latest[group_cols + keep].drop_duplicates()
                averaged = averaged.merge(attach, on=group_cols, how='left')
    return averaged

def _prev_periods(n: int, yyyymm: str, period: str) -> List[Tuple[str,str]]:
    # Return list including current and previous n-1 half-month periods
    out: List[Tuple[str,str]] = []
    y = int(yyyymm[:4])
    m = int(yyyymm[4:])
    p = period
    for _ in range(n):
        out.append((f"{y:04d}{m:02d}", p))
        if p == 'B':
            p = 'A'
        else:
            # Move to previous month B
            m -= 1
            if m == 0:
                m = 12
                y -= 1
            p = 'B'
    return out

def _resolve_recent_files(n: int = 3) -> Tuple[List[str], List[str]]:
    periods = _prev_periods(n, source_yyyymm, source_period)
    config_paths: List[str] = []
    qty_paths: List[str] = []
    for yyyymm_i, period_i in periods:
        try:
            files_i = get_api_data_files(yyyymm_i, period_i)
        except Exception:
            files_i = {}
        cfg = files_i.get('store_config')
        qty = files_i.get('spu_sales')
        if cfg and os.path.exists(cfg):
            config_paths.append(cfg)
        if qty and os.path.exists(qty):
            qty_paths.append(qty)
    return config_paths, qty_paths

def load_blended_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    # Resolve recent files (most-recent first) and average
    recent_cfg_paths, recent_qty_paths = _resolve_recent_files(n=3)
    if not recent_cfg_paths or not recent_qty_paths:
        # Fallback to current SOURCE period
        try:
            files_src = get_api_data_files(source_yyyymm, source_period)
        except Exception:
            files_src = {}
        if not recent_cfg_paths:
            cfg = files_src.get('store_config')
            if cfg and os.path.exists(cfg):
                recent_cfg_paths = [cfg]
        if not recent_qty_paths:
            qty = files_src.get('spu_sales')
            if qty and os.path.exists(qty):
                recent_qty_paths = [qty]

    recent_cfg_frames = [_read_csvs(p) for p in recent_cfg_paths]
    recent_qty_frames = [_read_csvs(p) for p in recent_qty_paths]
    recent_cfg_df = average_recent_dataframe(recent_cfg_frames, data_type="config")
    recent_qty_df = average_recent_dataframe(recent_qty_frames, data_type="quantity")

    if not USE_BLENDED_SEASONAL:
        return recent_cfg_df, recent_qty_df

    # Seasonal anchors from ENV or fallback to last-year same month
    seasonal_cfg_path = os.environ.get("SEASONAL_CONFIG_FILE")
    seasonal_qty_path = os.environ.get("SEASONAL_QUANTITY_FILE")
    if not seasonal_cfg_path or not os.path.exists(seasonal_cfg_path):
        try:
            sy, sm = int(source_yyyymm[:4]), int(source_yyyymm[4:])
            files_seas = get_api_data_files(f"{sy-1}{sm:02d}", source_period)
        except Exception:
            files_seas = {}
        seasonal_cfg_path = files_seas.get('store_config')
    if not seasonal_qty_path or not os.path.exists(seasonal_qty_path):
        try:
            sy, sm = int(source_yyyymm[:4]), int(source_yyyymm[4:])
            files_seas = get_api_data_files(f"{sy-1}{sm:02d}", source_period)
        except Exception:
            files_seas = {}
        seasonal_qty_path = files_seas.get('spu_sales')

    seasonal_cfg_df = _read_csvs(seasonal_cfg_path)
    seasonal_qty_df = _read_csvs(seasonal_qty_path)

    seasonal_weight = float(SEASONAL_WEIGHT_ENV)
    recent_weight = 1.0 - seasonal_weight
    cfg_blended = blend_seasonal_data(recent_cfg_df, seasonal_cfg_df, recent_weight, seasonal_weight, data_type="config")
    qty_blended = blend_seasonal_data(recent_qty_df, seasonal_qty_df, recent_weight, seasonal_weight, data_type="quantity")
    return cfg_blended, qty_blended

def blend_seasonal_data(recent_df: pd.DataFrame, seasonal_df: pd.DataFrame, 
                       recent_weight: float = 0.4, seasonal_weight: float = 0.6, 
                       data_type: str = "sales") -> pd.DataFrame:
    """
    Blend recent trends data with seasonal patterns using weighted aggregation.
    
    Args:
        recent_df: Recent trends data (May-July 2025)
        seasonal_df: Seasonal patterns data (August 2024)
        recent_weight: Weight for recent data (default 0.4)
        seasonal_weight: Weight for seasonal data (default 0.6)
        data_type: Type of data being blended (for logging)
        
    Returns:
        Blended DataFrame with weighted aggregation
    """
    log_progress(f"🍂 Blending {data_type} data: {recent_weight:.0%} recent + {seasonal_weight:.0%} seasonal")
    
    # Ensure both dataframes have the same structure
    if seasonal_df is None or len(seasonal_df) == 0 or len(seasonal_df.columns) == 0:
        log_progress("Seasonal frame empty or missing; using recent data only")
        return recent_df.copy()
    common_columns = list(set(recent_df.columns) & set(seasonal_df.columns))
    if not common_columns:
        log_progress("No common columns found between recent and seasonal; using recent data only")
        return recent_df.copy()
    recent_clean = recent_df[common_columns].copy()
    seasonal_clean = seasonal_df[common_columns].copy()
    
    # Identify numeric/non-numeric columns for blending
    numeric_columns = recent_clean.select_dtypes(include=[np.number]).columns.tolist()
    non_numeric_columns = [c for c in common_columns if c not in numeric_columns]
    
    # Create merge keys when possible
    blended_df = recent_clean.copy()
    if 'str_code' in common_columns and 'spu_code' in common_columns:
        recent_clean['merge_key'] = recent_clean['str_code'].astype(str) + '_' + recent_clean['spu_code'].astype(str)
        seasonal_clean['merge_key'] = seasonal_clean['str_code'].astype(str) + '_' + seasonal_clean['spu_code'].astype(str)
        blended_df['merge_key'] = recent_clean['merge_key']

        # Aggregate seasonal values by merge_key to avoid ambiguous lookups
        seasonal_grouped_numeric = seasonal_clean.groupby('merge_key')[numeric_columns].mean()
        # Prepare non-numeric seasonal reference (first non-null per group)
        if non_numeric_columns:
            seasonal_grouped_nonnum = (
                seasonal_clean.groupby('merge_key')[non_numeric_columns]
                .agg(lambda x: x.dropna().iloc[0] if x.dropna().shape[0] > 0 else np.nan)
            )
        else:
            seasonal_grouped_nonnum = pd.DataFrame(index=seasonal_grouped_numeric.index)

        # Vectorized blend for overlapping keys
        if numeric_columns:
            seasonal_aligned = seasonal_grouped_numeric.reindex(blended_df['merge_key'])
            # Reset index to ensure positional alignment (avoids reindex errors with duplicate labels)
            seasonal_aligned = seasonal_aligned.reset_index(drop=True)
            # Compute blended values preserving missingness: use weights of available values only
            recent_numeric = blended_df[numeric_columns].apply(pd.to_numeric, errors='coerce').to_numpy()
            seasonal_numeric = seasonal_aligned[numeric_columns].apply(pd.to_numeric, errors='coerce').to_numpy()
            recent_mask = ~np.isnan(recent_numeric)
            seasonal_mask = ~np.isnan(seasonal_numeric)
            denom = (recent_mask * recent_weight) + (seasonal_mask * seasonal_weight)
            # Replace NaNs with 0 for arithmetic, but multiply by masks so NaNs don't contribute
            recent_num = np.nan_to_num(recent_numeric) * recent_mask * recent_weight
            seasonal_num = np.nan_to_num(seasonal_numeric) * seasonal_mask * seasonal_weight
            with np.errstate(invalid='ignore', divide='ignore'):
                blended_numeric = (recent_num + seasonal_num) / denom
            # Where denom is 0 (both missing), keep NaN
            blended_numeric[denom == 0] = np.nan
            blended_df[numeric_columns] = blended_numeric

        # Add seasonal-only items (keys not present in recent)
        recent_keys = set(recent_clean['merge_key'].dropna().unique())
        seasonal_keys = set(seasonal_clean['merge_key'].dropna().unique())
        seasonal_only_keys = list(seasonal_keys - recent_keys)
        if len(seasonal_only_keys) > 0:
            seasonal_only_numeric = seasonal_grouped_numeric.loc[seasonal_only_keys]
            seasonal_only_nonnum = seasonal_grouped_nonnum.loc[seasonal_only_keys]
            seasonal_only_df = seasonal_only_nonnum.join(seasonal_only_numeric)
            seasonal_only_df = seasonal_only_df.reset_index()

            # Ensure str_code/spu_code exist for seasonal-only records
            if 'str_code' not in seasonal_only_df.columns or 'spu_code' not in seasonal_only_df.columns:
                seasonal_only_df['str_code'] = seasonal_only_df['merge_key'].astype(str).str.split('_').str[0]
                seasonal_only_df['spu_code'] = seasonal_only_df['merge_key'].astype(str).str.split('_').str[1]

            # Apply seasonal weight to seasonal-only numeric columns
            for col in numeric_columns:
                seasonal_only_df[col] = pd.to_numeric(seasonal_only_df[col], errors='coerce') * seasonal_weight

            # Drop merge_key for final concat
            seasonal_only_df = seasonal_only_df.drop(columns=['merge_key'], errors='ignore')
            blended_df = blended_df.drop(columns=['merge_key'], errors='ignore')

            # Align columns for concat
            missing_cols_in_seasonal = [c for c in blended_df.columns if c not in seasonal_only_df.columns]
            for c in missing_cols_in_seasonal:
                seasonal_only_df[c] = np.nan
            seasonal_only_df = seasonal_only_df[blended_df.columns.tolist()]

            blended_df = pd.concat([blended_df, seasonal_only_df], ignore_index=True)
            seasonal_only_count = len(seasonal_only_df)
        else:
            # Remove merge_key column if present
            blended_df = blended_df.drop(columns=['merge_key'], errors='ignore')
            seasonal_only_count = 0
    else:
        # If no merge keys, just return the recent data as baseline
        seasonal_only_count = 0

    log_progress(f"✅ Blended data: {len(blended_df):,} records ({len(recent_clean):,} recent + {seasonal_only_count:,} seasonal-only)")
    return blended_df

def expand_spu_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expand SPU sales data from JSON strings into individual records.
    
    Args:
        df (pd.DataFrame): Input dataframe with sty_sal_amt JSON column
        
    Returns:
        pd.DataFrame: Expanded dataframe with individual SPU records
    """
    log_progress("Expanding SPU sales data for sales performance analysis...")
    
    # Filter records with SPU sales data
    spu_records = df[df['sty_sal_amt'].notna() & (df['sty_sal_amt'] != '')].copy()
    log_progress(f"Found {len(spu_records):,} records with SPU sales data")
    
    if len(spu_records) == 0:
        return pd.DataFrame()
    
    expanded_records = []
    batch_size = 1000
    total_batches = (len(spu_records) + batch_size - 1) // batch_size
    
    log_progress(f"Processing {len(spu_records):,} records in {total_batches:,} batches...")
    
    with tqdm(total=total_batches, desc="Expanding SPU data") as pbar:
        for i in range(0, len(spu_records), batch_size):
            batch = spu_records.iloc[i:i+batch_size]
            
            for _, row in batch.iterrows():
                try:
                    spu_data = json.loads(row['sty_sal_amt'])
                    for spu_code, sales_amount in spu_data.items():
                        if sales_amount >= MIN_SALES_VOLUME:  # Only include SPUs with meaningful sales
                            expanded_record = row.copy()
                            expanded_record['spu_code'] = spu_code
                            expanded_record['spu_sales'] = float(sales_amount)
                            expanded_records.append(expanded_record)
                except (json.JSONDecodeError, TypeError, ValueError):
                    continue
            
            pbar.update(1)
            
            # Progress logging every 10 batches
            if (i // batch_size + 1) % 10 == 0:
                log_progress(f"Processed {i//batch_size + 1:,}/{total_batches:,} batches, generated {len(expanded_records):,} SPU records so far")
            
            # Memory cleanup every 50 batches
            if (i // batch_size + 1) % 50 == 0:
                gc.collect()
    
    if not expanded_records:
        log_progress("No valid SPU records found after expansion")
        return pd.DataFrame()
    
    expanded_df = pd.DataFrame(expanded_records)
    log_progress(f"Expanded to {len(expanded_df):,} SPU records")
    
    return expanded_df

def load_data(join_mode: str = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load clustering results, category sales data, and quantity data"""
    config = ANALYSIS_CONFIGS[ANALYSIS_LEVEL]
    
    try:
        # Load cluster assignments (prefer period-aware file, fallback to legacy path)
        # Resolve period from environment (set by CLI) or config helper
        env_yyyymm = os.environ.get("PIPELINE_TARGET_YYYYMM")
        env_period = os.environ.get("PIPELINE_TARGET_PERIOD")
        if env_yyyymm and env_period:
            yyyymm, period = env_yyyymm, env_period
        else:
            yyyymm, period = get_current_period()
        period_out_files = get_output_files(analysis_level=ANALYSIS_LEVEL, yyyymm=yyyymm, period=period)
        clustered_period_path = period_out_files.get('clustering_results')
        legacy_cluster_path = config["cluster_file"]
        cluster_path = clustered_period_path if clustered_period_path and os.path.exists(clustered_period_path) else legacy_cluster_path
        if not os.path.exists(cluster_path):
            raise FileNotFoundError(f"Cluster results not found at {cluster_path}")
        cluster_df = pd.read_csv(cluster_path, dtype={'str_code': str})
        log_progress(f"Loaded cluster assignments for {len(cluster_df):,} stores from {os.path.basename(cluster_path)}")
        
        # Unified recent averaging + optional seasonal blending
        cfg_df, qty_df = load_blended_data()
        if cfg_df is None or len(cfg_df) == 0:
            raise ValueError("No configuration data available after recent averaging/blending")
        if qty_df is None or len(qty_df) == 0:
            raise ValueError("No quantity data available after recent averaging/blending")
        category_df = cfg_df
        quantity_df = qty_df
        
        # Ensure str_code is string for consistent joining
        cluster_df['str_code'] = cluster_df['str_code'].astype(str)
        category_df['str_code'] = category_df['str_code'].astype(str)
        quantity_df['str_code'] = quantity_df['str_code'].astype(str)
        
        # Validate quantity data columns
        quantity_required_cols = ['str_code', 'spu_code', 'spu_sales_amt']
        quantity_missing_cols = [col for col in quantity_required_cols if col not in quantity_df.columns]
        if quantity_missing_cols:
            raise ValueError(f"Missing required columns in quantity data: {quantity_missing_cols}")

        # Derive REAL per-SPU quantities and unit prices (no synthetic estimation)
        for col in ['base_sal_qty', 'fashion_sal_qty', 'sal_qty', 'quantity', 'spu_sales_amt']:
            if col in quantity_df.columns:
                quantity_df[col] = pd.to_numeric(quantity_df[col], errors='coerce')
        if 'quantity' not in quantity_df.columns:
            if ('base_sal_qty' in quantity_df.columns) and ('fashion_sal_qty' in quantity_df.columns):
                quantity_df['quantity'] = quantity_df[['base_sal_qty', 'fashion_sal_qty']].sum(axis=1, min_count=1)
                log_progress(f"Derived per-SPU quantity from base_sal_qty + fashion_sal_qty; NA count={int(quantity_df['quantity'].isna().sum()):,}")
            elif 'sal_qty' in quantity_df.columns:
                quantity_df['quantity'] = quantity_df['sal_qty']
                log_progress(f"Derived per-SPU quantity from sal_qty; NA count={int(quantity_df['quantity'].isna().sum()):,}")
            else:
                raise ValueError("Unable to derive per-SPU quantity. Expected: quantity or base_sal_qty+fashion_sal_qty or sal_qty")
        # Compute per-SPU unit price at store×SPU; preserve NA when qty<=0
        quantity_df['unit_price'] = np.where(
            quantity_df['quantity'] > 0,
            quantity_df['spu_sales_amt'] / quantity_df['quantity'],
            np.nan
        )
        
        log_progress(f"Data validation successful for sales performance analysis with quantity data")
        
        return cluster_df, category_df, quantity_df
        
    except Exception as e:
        log_progress(f"Error loading data: {str(e)}")
        raise

def prepare_sales_data(category_df: pd.DataFrame, cluster_df: pd.DataFrame, quantity_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare store-category sales data with cluster information and quantity data.
    
    Args:
        category_df: Category sales data
        cluster_df: Cluster assignments
        quantity_df: Quantity data with actual unit sales for performance calculations
        
    Returns:
        DataFrame with store-category sales, cluster information, and quantity metrics
    """
    config = ANALYSIS_CONFIGS[ANALYSIS_LEVEL]
    log_progress(f"Preparing sales data for {ANALYSIS_LEVEL.title()}-Level Sales Performance Analysis with quantity integration...")
    
    # Merge with cluster information using configured join mode + diagnostics
    sales_with_clusters = category_df.merge(
        cluster_df[['str_code', 'Cluster']], on='str_code', how=JOIN_MODE, indicator=(JOIN_MODE == 'left')
    )
    if JOIN_MODE == 'left':
        total_rows = len(category_df)
        matched = sales_with_clusters['Cluster'].notna().sum()
        unmatched = total_rows - matched
        if unmatched > 0:
            missing_samples = (
                sales_with_clusters.loc[sales_with_clusters['Cluster'].isna(), 'str_code']
                .dropna().astype(str).unique().tolist()[:10]
            )
            log_progress(
                f"LEFT JOIN diagnostics: total={total_rows:,}, matched={matched:,}, unmatched={unmatched:,} (sample missing str_code: {missing_samples})"
            )
        else:
            log_progress(f"LEFT JOIN diagnostics: total={total_rows:,}, matched={matched:,}, unmatched=0")
        # Drop merge indicator column
        sales_with_clusters = sales_with_clusters.drop(columns=['_merge'])
    else:
        log_progress(f"INNER JOIN used: resulting rows={len(sales_with_clusters):,}")

    # STANDARDIZATION: Ensure cluster_id column exists without synthetic defaults
    if 'Cluster' in sales_with_clusters.columns and 'cluster_id' not in sales_with_clusters.columns:
        sales_with_clusters['cluster_id'] = sales_with_clusters['Cluster']
    
    log_progress(f"Merged data prepared: {len(sales_with_clusters):,} records (cluster_id may be NA for unmatched stores)")
    
    # QUANTITY ENHANCEMENT: Process quantity data for performance analysis (keep zero/NA sales)
    log_progress("Processing quantity data for performance improvement calculations...")
    quantity_clean = quantity_df.copy()
    quantity_clean['spu_sales_amt'] = pd.to_numeric(quantity_clean['spu_sales_amt'], errors='coerce')
    
    # Data validation - check base columns first
    base_required_columns = ['str_code', 'Cluster']
    if ANALYSIS_LEVEL == "subcategory":
        base_required_columns.extend(['sub_cate_name', 'sal_amt'])
    else:
        base_required_columns.extend(['season_name', 'sex_name', 'display_location_name', 'big_class_name', 'sub_cate_name', 'sty_sal_amt'])
    
    missing_columns = [col for col in base_required_columns if col not in sales_with_clusters.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns for {ANALYSIS_LEVEL} analysis: {missing_columns}")
    
    log_progress(f"Data validation successful for {ANALYSIS_LEVEL} analysis")
    
    if ANALYSIS_LEVEL == "spu":
        # Expand SPU data
        sales_with_clusters = expand_spu_data(sales_with_clusters)
        if len(sales_with_clusters) == 0:
            raise ValueError("No valid SPU data found after expansion")
        sales_col = 'spu_sales'
        grouping_cols = ['str_code', 'cluster_id'] + config["grouping_columns"]
    else:
        # Clean and prepare subcategory data
        sales_with_clusters['sal_amt'] = pd.to_numeric(sales_with_clusters['sal_amt'], errors='coerce')
        sales_col = 'sal_amt'
        grouping_cols = ['str_code', 'cluster_id', 'sub_cate_name']
    
    # Filter to meaningful sales data
    sales_data = sales_with_clusters[
        sales_with_clusters[sales_col] >= MIN_SALES_VOLUME
    ].copy()
    
    # Group by store-category to get total sales per combination
    if ANALYSIS_LEVEL == "subcategory":
        store_category_sales = sales_data.groupby(grouping_cols).agg({
            sales_col: 'sum',
            'cate_name': 'first'  # Keep category name for reference
        }).reset_index()
    else:
        # For SPU level, create category key and aggregate
        sales_data['category_key'] = (sales_data['season_name'] + '|' + sales_data['sex_name'] + '|' + 
                                     sales_data['display_location_name'] + '|' + sales_data['big_class_name'] + '|' + 
                                     sales_data['sub_cate_name'] + '|' + sales_data['spu_code'])
        
        store_category_sales = sales_data.groupby(['str_code', 'cluster_id', 'category_key']).agg({
            sales_col: 'sum',
            'sub_cate_name': 'first',  # Keep subcategory name for reference
            'spu_code': 'first'
        }).reset_index()
    
    log_progress(f"Prepared {len(store_category_sales):,} store-category combinations from {store_category_sales['str_code'].nunique():,} stores")
    
    # DEBUG: Show sample of store-category sales data
    if len(store_category_sales) > 0:
        sample_sales = store_category_sales.head(5)
        log_progress(f"Sample store-category sales data:")
        for _, row in sample_sales.iterrows():
            if ANALYSIS_LEVEL == "spu":
                log_progress(f"  Store: {row['str_code']}, SPU: {row.get('spu_code', 'N/A')}, Sales: {row.get('spu_sales', 'N/A')}")
            else:
                log_progress(f"  Store: {row['str_code']}, Category: {row.get('sub_cate_name', 'N/A')}, Sales: {row.get('sal_amt', 'N/A')}")
    
    return store_category_sales

def calculate_opportunity_gaps(sales_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate opportunity gaps by comparing each store's category performance
    against cluster top quartile performers.
    
    Args:
        sales_data: Store-category sales data with clusters
        
    Returns:
        DataFrame with opportunity gap analysis
    """
    log_progress("Calculating opportunity gaps vs cluster top performers...")
    
    config = ANALYSIS_CONFIGS[ANALYSIS_LEVEL]
    sales_col = config["sales_column"] if ANALYSIS_LEVEL == "subcategory" else "spu_sales"
    
    results = []
    
    # Group by cluster and category to analyze peer performance
    if ANALYSIS_LEVEL == "subcategory":
        groupby_cols = ['cluster_id', 'sub_cate_name']
    else:
        groupby_cols = ['cluster_id', 'category_key']
    
    for group_key, group in sales_data.groupby(groupby_cols):
        
        # Skip if cluster too small for meaningful analysis
        if len(group) < MIN_CLUSTER_SIZE:
            continue
            
        # Calculate cluster performance statistics
        cluster_sales = group[sales_col].values
        top_quartile_sales = np.percentile(cluster_sales, TOP_QUARTILE_PERCENTILE)
        
        # Calculate opportunity gaps for each store in this cluster-category
        for _, store_row in group.iterrows():
            store_sales = store_row[sales_col]
            
            # Opportunity gap: positive = opportunity, negative = exceeding top quartile
            opportunity_gap = top_quartile_sales - store_sales
            
            # Add opportunity gap information to store data
            store_data = store_row.copy()
            store_data['opportunity_gap'] = opportunity_gap
            store_data['cluster_top_quartile'] = top_quartile_sales
            store_data['cluster_size'] = len(group)
            
            results.append(store_data)
    
    if results:
        opportunity_data = pd.DataFrame(results)
        log_progress(f"Calculated opportunity gaps for {len(opportunity_data):,} store-category combinations across {len(results):,} valid cluster-category groups")
    else:
        opportunity_data = pd.DataFrame()
    
    # DEBUG: Show sample of opportunity gap data
    if len(opportunity_data) > 0:
        sample_gaps = opportunity_data.head(5)
        log_progress(f"Sample opportunity gap data:")
        for _, row in sample_gaps.iterrows():
            if ANALYSIS_LEVEL == "spu":
                log_progress(f"  Store: {row['str_code']}, SPU: {row.get('spu_code', 'N/A')}, Gap: {row.get('opportunity_gap', 'N/A'):.2f}")
            else:
                log_progress(f"  Store: {row['str_code']}, Category: {row.get('sub_cate_name', 'N/A')}, Gap: {row.get('opportunity_gap', 'N/A'):.2f}")
    
    return opportunity_data

def calculate_opportunity_z_scores(opportunity_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Z-scores for opportunity gaps to enable classification.
    
    Args:
        opportunity_data: Data with opportunity gaps calculated
        
    Returns:
        DataFrame with Z-scores for opportunity gaps
    """
    log_progress("Calculating Z-scores for opportunity gaps...")
    
    if len(opportunity_data) == 0:
        return pd.DataFrame()
    
    # Calculate Z-scores for opportunity gaps across all data
    gaps = opportunity_data['opportunity_gap'].values
    gap_mean = np.mean(gaps)
    gap_std = np.std(gaps, ddof=1)
    
    # Handle case where all gaps are identical (std = 0)
    if gap_std == 0:
        opportunity_data['opportunity_gap_z_score'] = 0
        log_progress("All opportunity gaps are identical, setting Z-scores to 0")
    else:
        opportunity_data['opportunity_gap_z_score'] = (gaps - gap_mean) / gap_std
        log_progress(f"Calculated Z-scores with mean gap: {gap_mean:.2f}, std: {gap_std:.2f}")
    
    return opportunity_data

def classify_performance_levels(z_score_data: pd.DataFrame, quantity_df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify stores into 5 performance levels based on opportunity gap Z-scores
    and calculate UNIT QUANTITY INCREASE recommendations to close performance gaps.
    
    Args:
        z_score_data: Data with Z-scores calculated
        quantity_df: Quantity data for unit increase calculations
        
    Returns:
        DataFrame with performance level classifications and quantity increase recommendations
    """
    log_progress("Classifying performance levels and calculating UNIT QUANTITY INCREASE recommendations...")
    
    if len(z_score_data) == 0:
        return pd.DataFrame()
    
    # QUANTITY ENHANCEMENT: Prepare quantity lookup for unit increase calculations
    log_progress("Preparing quantity data for performance improvement calculations...")
    quantity_lookup = {}
    unit_price_lookup = {}
    # Create SPU-level quantity and unit price lookups
    for _, row in quantity_df.iterrows():
        key = f"{row['str_code']}_{row['spu_code']}"
        qty_val = row.get('quantity', np.nan)
        price_val = row.get('unit_price', np.nan)
        if pd.notna(qty_val):
            quantity_lookup[key] = float(qty_val)
        if pd.notna(price_val):
            unit_price_lookup[key] = float(price_val)
    
    # DEBUG: Show sample of quantity lookup keys
    sample_keys = list(quantity_lookup.keys())[:10]
    log_progress(f"Created quantity lookup with {len(quantity_lookup):,} store-SPU combinations; unit prices for {len(unit_price_lookup):,}")
    log_progress(f"Sample quantity lookup keys: {sample_keys}")
    
    # Classify based on Z-score thresholds
    def classify_performance(z_score):
        if z_score < PERFORMANCE_THRESHOLDS['top_performer']:
            return 'top_performer'
        elif z_score <= PERFORMANCE_THRESHOLDS['performing_well']:
            return 'performing_well'
        elif z_score <= PERFORMANCE_THRESHOLDS['some_opportunity']:
            return 'some_opportunity'
        elif z_score <= PERFORMANCE_THRESHOLDS['good_opportunity']:
            return 'good_opportunity'
        else:
            return 'major_opportunity'
    
    z_score_data['performance_level'] = z_score_data['opportunity_gap_z_score'].apply(classify_performance)
    
    # Create binary flags for each performance level
    for level in ['top_performer', 'performing_well', 'some_opportunity', 'good_opportunity', 'major_opportunity']:
        z_score_data[f'rule12_{level}'] = (z_score_data['performance_level'] == level).astype(int)
    
    # Add business insights
    z_score_data['opportunity_value'] = np.maximum(0, z_score_data['opportunity_gap'])  # Only positive gaps are opportunities
    z_score_data['exceeds_top_quartile'] = (z_score_data['opportunity_gap'] < 0).astype(int)
    
    # QUANTITY ENHANCEMENT: Calculate unit quantity increase recommendations
    log_progress("Calculating unit quantity increase recommendations for performance improvement...")
    
    # Initialize quantity columns
    z_score_data['current_quantity'] = 0.0
    z_score_data['recommended_quantity_increase'] = 0.0
    z_score_data['recommended_quantity_change'] = 0.0  # STANDARDIZED
    z_score_data['unit_price'] = 0.0  # STANDARDIZED: Use standard column name
    z_score_data['investment_required'] = 0.0
    z_score_data['current_quantity'] = 0.0  # STANDARDIZED: Current quantity
    z_score_data['recommendation_text'] = ""  # STANDARDIZED: Text recommendation
    z_score_data['quantity_recommendation_text'] = ""
    
    quantity_increases = []
    
    # DEBUG: Add counter to track progress
    debug_count = 0
    
    for idx, row in z_score_data.iterrows():
        # Only calculate increases for stores with opportunities (positive gaps)
        if row['opportunity_gap'] <= 0:
            continue
            
        # DEBUG: Show first few records
        debug_count += 1
        if debug_count <= 5:
            print(f"DEBUG GAP: store={row.get('str_code', 'N/A')}, spu={row.get('spu_code', 'N/A')}, opportunity_gap={row['opportunity_gap']:.2f}")
            
        # Get current quantity for this store-SPU combination
        if ANALYSIS_LEVEL == "spu":
            quantity_key = f"{row['str_code']}_{row['spu_code']}"
            current_qty = quantity_lookup.get(quantity_key, np.nan)
            if debug_count <= 5:
                print(f"DEBUG QTY: store={row.get('str_code', 'N/A')}, spu={row.get('spu_code', 'N/A')}, quantity_key={quantity_key}, current_qty={current_qty}")
            if pd.isna(current_qty) or current_qty <= 0:
                if debug_count <= 5:
                    print(f"DEBUG SKIP: No valid quantity for {quantity_key}")
                continue
        else:
            # Subcategory path not enabled; skip when no defensible quantity
            continue
        
        # More lenient quantity check - allow very small quantities
        if current_qty <= 0.01:  # Changed from <= 0 to <= 0.01
            continue
            
        # Calculate unit price estimate
        if ANALYSIS_LEVEL == "spu":
            sales_col = 'spu_sales'
        else:
            sales_col = 'sal_amt'
            
        unit_price = unit_price_lookup.get(quantity_key, np.nan)
        if (pd.isna(unit_price) or unit_price <= 0) and ('spu_sales' in row):
            unit_price = row['spu_sales'] / current_qty if current_qty > 0 else np.nan
        if pd.isna(unit_price) or unit_price <= 0:
            continue
        
        # Calculate recommended quantity increase based on opportunity gap
        # Opportunity gap represents sales difference, convert to units
        gap_in_units = row['opportunity_gap'] / unit_price if unit_price > 0 else 0
        
        # Apply constraints
        max_increase = current_qty * MAX_INCREASE_PERCENTAGE
        recommended_increase = min(gap_in_units, max_increase)
        
        # DEBUG: Log some values to understand the distribution
        # Log first 12 records that pass initial filters for debugging
        if len(quantity_increases) < 12:
            print(f"DEBUG: store={row.get('str_code', 'N/A')}, spu={row.get('spu_code', 'N/A')}, opportunity_gap={row['opportunity_gap']:.2f}, unit_price={unit_price:.2f}, current_qty={current_qty:.2f}, gap_in_units={gap_in_units:.4f}, max_increase={max_increase:.4f}, recommended_increase={recommended_increase:.4f}, investment={recommended_increase * unit_price:.2f}")
        
        # Only recommend if above minimum threshold
        if recommended_increase >= MIN_INCREASE_QUANTITY:
            z_score_data.at[idx, 'current_quantity'] = current_qty
            z_score_data.at[idx, 'recommended_quantity_increase'] = recommended_increase
            z_score_data.at[idx, 'recommended_quantity_change'] = recommended_increase  # STANDARDIZED
            z_score_data.at[idx, 'unit_price'] = unit_price  # STANDARDIZED: Use standard column name
            z_score_data.at[idx, 'investment_required'] = recommended_increase * unit_price
            z_score_data.at[idx, 'current_quantity'] = current_qty  # STANDARDIZED: Current quantity
            
            # Create recommendation text
            recommendation_text = f"INCREASE {recommended_increase:.1f} UNITS/{TARGET_PERIOD_DAYS}-DAYS (current: {current_qty:.1f} → target: {current_qty + recommended_increase:.1f}) @ ~¥{unit_price:.0f}/unit"
            z_score_data.at[idx, 'quantity_recommendation_text'] = recommendation_text
            # STANDARDIZED: Add recommendation_text column for integration compatibility
            z_score_data.at[idx, 'recommendation_text'] = recommendation_text
            
            quantity_increases.append({
                'str_code': row['str_code'],
                'performance_level': row['performance_level'],
                'current_quantity': current_qty,
                'recommended_increase': recommended_increase,
                'investment_required': recommended_increase * unit_price
            })
    
    # Log quantity increase summary
    if quantity_increases:
        total_increases = sum(item['recommended_increase'] for item in quantity_increases)
        total_investment = sum(item['investment_required'] for item in quantity_increases)
        
        log_progress(f"Quantity increase recommendations generated:")
        log_progress(f"  - {len(quantity_increases):,} opportunities identified")
        log_progress(f"  - {total_increases:,.1f} total units/{TARGET_PERIOD_DAYS}-days increase needed")
        log_progress(f"  - ¥{total_investment:,.0f} total investment required")
        
        # Performance level breakdown
        level_breakdown = {}
        for item in quantity_increases:
            level = item['performance_level']
            if level not in level_breakdown:
                level_breakdown[level] = {'count': 0, 'units': 0, 'investment': 0}
            level_breakdown[level]['count'] += 1
            level_breakdown[level]['units'] += item['recommended_increase']
            level_breakdown[level]['investment'] += item['investment_required']
        
        for level, stats in level_breakdown.items():
            log_progress(f"  - {level}: {stats['count']} cases, {stats['units']:.1f} units, ¥{stats['investment']:.0f}")
    
    # APPLY STRICT SELECTIVITY FILTERS to reduce recommendation volume
    log_progress(f"Before selectivity filters: {len(z_score_data):,} records")
    
    # Filter 1: Include strong and moderate opportunities; still exclude top/performing-well
    actionable_levels = ['some_opportunity', 'good_opportunity', 'major_opportunity']
    z_score_data = z_score_data[
        z_score_data['performance_level'].isin(actionable_levels)
    ].copy()
    log_progress(f"After performance level filter (only {actionable_levels}): {len(z_score_data):,} records")
    
    # Filter 2: Only include records with significant Z-scores
    z_score_data = z_score_data[
        z_score_data['opportunity_gap_z_score'] >= MIN_Z_SCORE_THRESHOLD
    ].copy()
    log_progress(f"After Z-score filter (>={MIN_Z_SCORE_THRESHOLD}): {len(z_score_data):,} records")
    
    # Filter 3: Only include records with meaningful quantity recommendations
    # Additional guardrails: require plausible unit price range to avoid noisy items
    z_score_data = z_score_data[
        (z_score_data['recommended_quantity_increase'] >= MIN_INCREASE_QUANTITY)
        & (z_score_data['unit_price'].between(10, 800))
    ].copy()
    log_progress(f"After quantity filter (>={MIN_INCREASE_QUANTITY} units): {len(z_score_data):,} records")
    
    # Filter 4: Minimum investment threshold
    z_score_data = z_score_data[
        z_score_data['investment_required'] >= MIN_INVESTMENT_THRESHOLD
    ].copy()
    log_progress(f"After investment filter (>=¥{MIN_INVESTMENT_THRESHOLD}): {len(z_score_data):,} records")
    
    # Filter 5: Calculate opportunity score and filter
    if len(z_score_data) > 0:
        z_score_data['opportunity_score'] = (
            z_score_data['opportunity_gap_z_score'] / 3.0  # Normalize Z-score to 0-1 range
        ).clip(0, 1)
        
        z_score_data = z_score_data[
            z_score_data['opportunity_score'] >= MIN_OPPORTUNITY_SCORE
        ].copy()
        log_progress(f"After opportunity score filter (>={MIN_OPPORTUNITY_SCORE}): {len(z_score_data):,} records")
    
    # Filter 6: Optional per-store recommendation limit (apply only if cap provided)
    if len(z_score_data) > 0:
        z_score_data = z_score_data.sort_values(['str_code', 'opportunity_gap_z_score'], ascending=[True, False])
        if MAX_RECOMMENDATIONS_PER_STORE is not None:
            z_score_data = z_score_data.groupby('str_code').head(MAX_RECOMMENDATIONS_PER_STORE).reset_index(drop=True)
            log_progress(f"After per-store limit filter (max {MAX_RECOMMENDATIONS_PER_STORE} per store): {len(z_score_data):,} records")
        else:
            log_progress("Per-store limit filter skipped (no cap)")
    
    # Performance level distribution (after filtering)
    if len(z_score_data) > 0:
        level_counts = z_score_data['performance_level'].value_counts()
        log_progress(f"Performance level distribution (after filtering):")
        for level, count in level_counts.items():
            log_progress(f"  • {level}: {count} ({count/len(z_score_data)*100:.1f}%)")
        
        stores_with_recs = z_score_data['str_code'].nunique()
        avg_recs_per_store = len(z_score_data) / stores_with_recs if stores_with_recs > 0 else 0
        log_progress(f"Final result: {len(z_score_data):,} recommendations across {stores_with_recs:,} stores (avg {avg_recs_per_store:.1f} per store)")
    else:
        log_progress("No records remain after filtering")
    
    # 📈 FAST FISH ENHANCEMENT: Apply sell-through validation
    if SELLTHROUGH_VALIDATION_AVAILABLE and len(z_score_data) > 0:
        log_progress("🎯 Applying Fast Fish sell-through validation...")
        
        # Initialize validator
        historical_data = load_historical_data_for_validation()
        validator = SellThroughValidator(historical_data)
        
        # Apply validation to each performance improvement recommendation
        validated_recommendations = []
        rejected_count = 0
        
        for idx, rec in z_score_data.iterrows():
            # Get category name for validation (no synthetic defaults)
            category_name = rec.get('sub_cate_name', None)
            if pd.isna(category_name) or category_name is None or str(category_name).strip() == "":
                continue
            
            # Calculate quantities
            current_qty = rec.get('current_quantity', np.nan)
            # Map recommended_quantity_increase to standardized name for validation and downstream consistency
            change_qty = rec.get('recommended_quantity_change', rec.get('recommended_quantity_increase', np.nan))
            if pd.isna(current_qty) or pd.isna(change_qty):
                continue
            recommended_qty = current_qty + change_qty
            
            # Validate the performance improvement recommendation using CORRECTED Fast Fish definition
            # Clamp integerized counts to validator's expected range
            current_qty_int = int(np.clip(current_qty, 0, 100))
            recommended_qty_int = int(np.clip(recommended_qty, 0, 100))
            validation = validator.validate_recommendation(
                store_code=str(rec['str_code']),
                category=str(category_name),
                current_spu_count=current_qty_int,
                recommended_spu_count=recommended_qty_int,
                action='IMPROVE',
                rule_name='Rule 12: Sales Performance'
            )
            
            # Only keep Fast Fish compliant recommendations
            if validation['fast_fish_compliant']:
                # Add sell-through metrics to recommendation
                enhanced_rec = rec.to_dict()
                enhanced_rec.update({
                    'current_sell_through_rate': validation['current_sell_through_rate'],
                    'predicted_sell_through_rate': validation['predicted_sell_through_rate'],
                    'sell_through_improvement': validation['sell_through_improvement'],
                    'fast_fish_compliant': validation['fast_fish_compliant'],
                    'business_rationale': validation['business_rationale'],
                    'approval_reason': validation['approval_reason']
                })
                validated_recommendations.append(enhanced_rec)
            else:
                rejected_count += 1
        
        # Replace recommendations with validated ones
        if validated_recommendations:
            z_score_data = pd.DataFrame(validated_recommendations)
            # Sort by sell-through improvement (prioritize best improvements)
            z_score_data = z_score_data.sort_values('sell_through_improvement', ascending=False)
            
            avg_improvement = z_score_data['sell_through_improvement'].mean()
            total_investment = z_score_data['investment_required'].sum() if 'investment_required' in z_score_data.columns else 0
            
            log_progress(f"✅ Fast Fish sell-through validation complete:")
            log_progress(f"   Approved: {len(validated_recommendations)} performance improvements")
            log_progress(f"   Rejected: {rejected_count} performance improvements")
            log_progress(f"   Average sell-through improvement: {avg_improvement:.1f} percentage points")
            if total_investment > 0:
                log_progress(f"   Total investment (validated): ${total_investment:,.0f}")
        else:
            log_progress(f"⚠️ All {len(z_score_data)} performance improvements rejected by sell-through validation")
            z_score_data = pd.DataFrame()  # Return empty DataFrame
    elif not SELLTHROUGH_VALIDATION_AVAILABLE and len(z_score_data) > 0:
        log_progress("⚠️ Sell-through validation skipped (validator not available)")
    
    # Optional per-store total unit cap post-validation
    if len(z_score_data) > 0 and MAX_TOTAL_QUANTITY_PER_STORE is not None:
        if 'opportunity_score' not in z_score_data.columns:
            z_score_data['opportunity_score'] = z_score_data.get('opportunity_gap_z_score', 0).abs()
        z_score_data = z_score_data.sort_values(['str_code', 'opportunity_score'], ascending=[True, False])
        def _cap_store(group: pd.DataFrame) -> pd.DataFrame:
            # Ensure standardized column exists
            if 'recommended_quantity_change' not in group.columns and 'recommended_quantity_increase' in group.columns:
                group = group.rename(columns={'recommended_quantity_increase': 'recommended_quantity_change'})
            csum = group['recommended_quantity_change'].cumsum()
            return group[csum <= MAX_TOTAL_QUANTITY_PER_STORE]
        before = len(z_score_data)
        z_score_data = z_score_data.groupby('str_code', group_keys=False).apply(_cap_store)
        after = len(z_score_data)
        trimmed = before - after
        if trimmed > 0:
            log_progress(f"Applied per-store total unit cap: kept ≤{MAX_TOTAL_QUANTITY_PER_STORE} units; trimmed {trimmed} recommendations across all stores")
    elif len(z_score_data) > 0 and MAX_TOTAL_QUANTITY_PER_STORE is None:
        log_progress("Per-store total unit cap skipped (no cap)")
    return z_score_data

def aggregate_store_performance(classified_data: pd.DataFrame, cluster_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate category-level performance to store level with quantity increase recommendations.
    
    Args:
        classified_data: Category-level performance data with quantity recommendations
        cluster_df: Store cluster assignments
        
    Returns:
        DataFrame with store-level performance aggregation and total quantity increases
    """
    log_progress("Aggregating performance to store level with quantity increase totals...")
    
    # Create base results from cluster data - STANDARDIZATION FIX: Use cluster_id
    if 'Cluster' in cluster_df.columns and 'cluster_id' not in cluster_df.columns:
        cluster_df['cluster_id'] = cluster_df['Cluster']
    elif 'cluster_id' not in cluster_df.columns:
        cluster_df['cluster_id'] = cluster_df.get('Cluster', 0)
    
    results_df = cluster_df[['str_code', 'cluster_id']].copy()
    
    if len(classified_data) == 0:
        log_progress("No classified data available for aggregation")
        # Populate standardized columns even when no classified data remains
        # Determine column names based on analysis level
        if ANALYSIS_LEVEL == "subcategory":
            analyzed_col = 'subcategories_analyzed'
            top_quartile_col = 'top_quartile_subcategories'
        else:
            analyzed_col = 'categories_analyzed'
            top_quartile_col = 'top_quartile_categories'

        # Initialize numeric columns with zeros
        results_df['avg_opportunity_z_score'] = 0.0
        results_df['total_opportunity_value'] = 0.0
        results_df[analyzed_col] = 0
        results_df[top_quartile_col] = 0
        results_df['total_quantity_increase_needed'] = 0.0
        results_df['total_investment_required'] = 0.0
        results_df['total_current_quantity'] = 0.0
        results_df['quantity_opportunities_count'] = 0
        # Boolean flags and performance labels
        results_df['has_quantity_recommendations'] = pd.Series([pd.NA] * len(results_df), dtype='boolean')
        results_df['store_performance_level'] = 'no_data'
        for level in ['top_performer', 'performing_well', 'some_opportunity', 'good_opportunity', 'major_opportunity']:
            results_df[f'rule12_{level}'] = 0
        results_df['rule12_quantity_increase_recommended'] = pd.Series([pd.NA] * len(results_df), dtype='boolean')

        # Metadata and compatibility columns
        results_df['rule12_description'] = f'Sales performance vs cluster top {TOP_QUARTILE_PERCENTILE}th percentile with quantity increase recommendations'
        results_df['rule12_analysis_method'] = 'Opportunity gap Z-score analysis with unit quantity increases'
        results_df['rule_flag'] = 'rule12_sales_performance'
        results_df['opportunity_type'] = 'sales_performance_improvement'
        results_df['unit_price'] = 0.0
        results_df['fast_fish_compliant'] = 'unknown'
        results_df['business_rationale'] = 'Performance gap analysis vs cluster top quartile with quantity recommendations'
        results_df['approval_reason'] = 'Systematic underperformance identified through Z-score analysis'
        # Standardized downstream fields
        results_df['investment_required'] = results_df['total_investment_required']
        results_df['recommended_quantity_change'] = results_df['total_quantity_increase_needed']
        
        return results_df
    
    # Determine column names based on analysis level
    if ANALYSIS_LEVEL == "subcategory":
        count_col = 'sub_cate_name'
        analyzed_col = 'subcategories_analyzed'
        top_quartile_col = 'top_quartile_subcategories'
    else:
        count_col = 'category_key'
        analyzed_col = 'categories_analyzed'
        top_quartile_col = 'top_quartile_categories'
    
    # QUANTITY ENHANCEMENT: Aggregate both performance and quantity metrics
    store_aggregation = classified_data.groupby('str_code').agg({
        'opportunity_gap_z_score': 'mean',          # Average Z-score across categories
        'opportunity_value': 'sum',                 # Total opportunity value
        count_col: 'count',                        # Number of categories analyzed
        'exceeds_top_quartile': 'sum',             # Number of categories exceeding top quartile
        'recommended_quantity_increase': 'sum',     # Total quantity increase needed
        'investment_required': 'sum',      # Total investment required
        'current_quantity': 'sum'                   # Total current quantity
    }).reset_index()
    
    store_aggregation.columns = [
        'str_code', 'avg_opportunity_z_score', 'total_opportunity_value', 
        analyzed_col, top_quartile_col, 'total_quantity_increase_needed',
        'total_investment_required', 'total_current_quantity'
    ]
    
    # QUANTITY ENHANCEMENT: Count stores with quantity recommendations
    stores_with_recommendations = classified_data[
        classified_data['recommended_quantity_increase'] > 0
    ]['str_code'].nunique()
    
    # Add quantity recommendation flags at store level
    store_quantity_flags = classified_data[
        classified_data['recommended_quantity_increase'] > 0
    ].groupby('str_code').size().reset_index(name='quantity_opportunities_count')
    
    store_aggregation = store_aggregation.merge(
        store_quantity_flags, on='str_code', how='left'
    )
    # Preserve missingness for stores without quantity flags using pandas BooleanDtype (allows <NA>)
    store_aggregation['has_quantity_recommendations'] = (
        store_aggregation['quantity_opportunities_count'].gt(0).astype('boolean')
    )
    
    # Classify stores based on average Z-score
    def classify_store_performance(avg_z_score):
        if avg_z_score < PERFORMANCE_THRESHOLDS['top_performer']:
            return 'top_performer'
        elif avg_z_score <= PERFORMANCE_THRESHOLDS['performing_well']:
            return 'performing_well'
        elif avg_z_score <= PERFORMANCE_THRESHOLDS['some_opportunity']:
            return 'some_opportunity'
        elif avg_z_score <= PERFORMANCE_THRESHOLDS['good_opportunity']:
            return 'good_opportunity'
        else:
            return 'major_opportunity'
    
    store_aggregation['store_performance_level'] = store_aggregation['avg_opportunity_z_score'].apply(classify_store_performance)
    
    # Create binary flags for store-level performance
    for level in ['top_performer', 'performing_well', 'some_opportunity', 'good_opportunity', 'major_opportunity']:
        store_aggregation[f'rule12_{level}'] = (store_aggregation['store_performance_level'] == level).astype(int)
    
    # QUANTITY ENHANCEMENT: Add quantity-specific flags
    store_aggregation['rule12_quantity_increase_recommended'] = store_aggregation['has_quantity_recommendations']
    
    # Merge with base results
    results_df = results_df.merge(store_aggregation, on='str_code', how='left')
    
    # Preserve missingness: avoid synthetic defaults or coercion to 0/"no_data".
    # Downstream summaries already guard against NaN.
    
    # Add metadata
    results_df['rule12_description'] = f'Sales performance vs cluster top {TOP_QUARTILE_PERCENTILE}th percentile with quantity increase recommendations'
    results_df['rule12_analysis_method'] = 'Opportunity gap Z-score analysis with unit quantity increases'
    
    # PIPELINE COMPATIBILITY: Add missing standard columns for downstream processing
    results_df['rule_flag'] = 'rule12_sales_performance'
    results_df['opportunity_type'] = 'sales_performance_improvement'
    results_df['unit_price'] = results_df.get('unit_price', 0.0)
    results_df['fast_fish_compliant'] = results_df.get('fast_fish_compliant', 'unknown')
    results_df['business_rationale'] = 'Performance gap analysis vs cluster top quartile with quantity recommendations'
    results_df['approval_reason'] = 'Systematic underperformance identified through Z-score analysis'
    
    # Map existing columns to standard names for compatibility
    if 'total_investment_required' not in results_df.columns:
        results_df['investment_required'] = 0.0
    else:
        results_df['investment_required'] = results_df['total_investment_required']
    
    if 'total_quantity_increase_needed' not in results_df.columns:
        results_df['recommended_quantity_change'] = 0.0
    else:
        results_df['recommended_quantity_change'] = results_df['total_quantity_increase_needed']
    
    # QUANTITY ENHANCEMENT: Log quantity summary (with error handling)
    if all(col in results_df.columns for col in ['rule12_quantity_increase_recommended', 'total_quantity_increase_needed', 'total_investment_required']):
        total_stores_with_qty_recs = results_df['rule12_quantity_increase_recommended'].sum()
        total_qty_increase = results_df['total_quantity_increase_needed'].sum()
        total_investment = results_df['total_investment_required'].sum()
        
        log_progress(f"Aggregated performance for {len(results_df)} stores with quantity enhancement:")
        log_progress(f"  - {total_stores_with_qty_recs:,} stores with quantity increase recommendations")
        log_progress(f"  - {total_qty_increase:,.1f} total units/{TARGET_PERIOD_DAYS}-days increase needed")
        log_progress(f"  - ¥{total_investment:,.0f} total investment required for quantity increases")
    else:
        log_progress(f"Aggregated performance for {len(results_df)} stores (no quantity data available)")
    
    # Store-level performance distribution (with error handling)
    if 'store_performance_level' in results_df.columns and len(results_df) > 0:
        store_level_counts = results_df['store_performance_level'].value_counts()
        log_progress(f"Store-level performance distribution:")
        for level, count in store_level_counts.items():
            log_progress(f"  • {level}: {count} stores ({count/len(results_df)*100:.1f}%)")
    else:
        log_progress("Store-level performance distribution: No data available")
    
    return results_df

def save_results(results_df: pd.DataFrame, classified_data: pd.DataFrame, period_label: Optional[str] = None) -> None:
    """Save rule results and detailed analysis (both unlabeled and labeled outputs)"""
    prefix = ANALYSIS_CONFIGS[ANALYSIS_LEVEL]['output_prefix']

    # Resolve period label and derive metadata fields
    label = period_label
    ty = tm = tp = None
    if not label:
        env_yyyymm = os.environ.get("PIPELINE_TARGET_YYYYMM")
        env_period = os.environ.get("PIPELINE_TARGET_PERIOD")
        if env_yyyymm and env_period:
            label = f"{env_yyyymm}{env_period}"
            ty, tm, tp = env_yyyymm[:4], env_yyyymm[4:6], env_period
    if label and (ty is None or tm is None or tp is None):
        if len(label) >= 7:
            ty, tm, tp = label[:4], label[4:6], label[-1]

    # Embed explicit period metadata columns inside the output DataFrames (provenance)
    target_yyyymm_value = f"{ty}{tm}" if ty and tm else None
    target_period_value = tp
    for df in (results_df, classified_data):
        if isinstance(df, pd.DataFrame):
            df['period_label'] = label
            df['target_yyyymm'] = target_yyyymm_value
            df['target_period'] = target_period_value

    # Compute paths
    base_results = f"output/{prefix}_results.csv"
    labeled_results = f"output/{prefix}_results_{label}.csv" if label else None

    # Save results with standardized pattern
    timestamped, _, _ = create_output_with_symlinks(
        results_df,
        f"output/{prefix}_results",
        label if label else "unlabeled"
    )
    log_progress(f"Saved rule results: {timestamped} ({len(results_df):,} rows)")
    base_results = timestamped

    # Register in manifest (generic + period-specific)
    base_meta = {
        "target_year": ty,
        "target_month": tm if ty else None,
        "target_period": tp,
        "analysis_level": ANALYSIS_LEVEL,
        "seasonal_blending_enabled": bool(USE_BLENDED_SEASONAL),
        "records": int(len(results_df)),
        "columns": results_df.columns.tolist(),
        "file_format": "csv",
    }
    register_step_output("step12", "rule12_results", base_results, metadata=base_meta)
    if labeled_results:
        register_step_output("step12", f"rule12_results_{label}", labeled_results, metadata=base_meta)

    # Save backward-compatible results (subcategory legacy filename)
    if ANALYSIS_LEVEL == "subcategory":
        backward_compatible_file = "output/rule12_sales_performance_results.csv"
        results_df.to_csv(backward_compatible_file, index=False)
        log_progress(f"Saved backward-compatible results to {backward_compatible_file}")
    
    # Detailed analysis (write file even if empty to keep pipeline compatibility)
    base_details = f"output/{prefix}_details.csv"
    labeled_details = f"output/{prefix}_details_{label}.csv" if label else None
    classified_data.to_csv(base_details, index=False)
    log_progress(f"Saved detailed {ANALYSIS_LEVEL} analysis to {base_details} ({len(classified_data):,} rows)")
    if labeled_details:
        classified_data.to_csv(labeled_details, index=False)
        log_progress(f"Saved labeled detailed {ANALYSIS_LEVEL} analysis to {labeled_details}")

    # Register details in manifest
    details_meta = {
        "target_year": ty,
        "target_month": tm if ty else None,
        "target_period": tp,
        "analysis_level": ANALYSIS_LEVEL,
        "seasonal_blending_enabled": bool(USE_BLENDED_SEASONAL),
        "records": int(len(classified_data)),
        "columns": classified_data.columns.tolist(),
        "file_format": "csv",
    }
    register_step_output("step12", "rule12_details", base_details, metadata=details_meta)
    if labeled_details:
        register_step_output("step12", f"rule12_details_{label}", labeled_details, metadata=details_meta)
    
    # Save backward-compatible details for subcategory analysis
    if ANALYSIS_LEVEL == "subcategory":
        backward_details_file = "output/rule12_subcategory_performance_details.csv"
        classified_data.to_csv(backward_details_file, index=False)
        log_progress(f"Saved backward-compatible details to {backward_details_file}")
    
    # Generate summary report (unlabeled + labeled)
    summary_file = f"output/{prefix}_summary.md"
    labeled_summary_file = f"output/{prefix}_summary_{label}.md" if label else None
    with open(summary_file, 'w') as f:
        f.write(f"# Rule 12: Sales Performance Rule with UNIT QUANTITY INCREASE RECOMMENDATIONS ({ANALYSIS_LEVEL.title()}-Level)\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Analysis Level**: {ANALYSIS_LEVEL.title()}\n\n")
        f.write(f"**ENHANCEMENT**: Now includes specific unit quantity increase recommendations! 🎯\n\n")
        # Explicit seasonal blending and target period lines for consistency with other steps
        f.write(f"**Seasonal blending**: {'Enabled' if USE_BLENDED_SEASONAL else 'Disabled'}\n")
        if label:
            f.write(f"**Target period**: {label}\n")
        f.write("\n")
        
        f.write("## Rule Definition\n")
        f.write(f"**Purpose**: Identify sales opportunities by comparing store {ANALYSIS_LEVEL} performance against cluster top {TOP_QUARTILE_PERCENTILE}th percentile and provide specific unit quantity increase recommendations\n\n")
        f.write("**Method**: Opportunity gap Z-score analysis with unit quantity increase calculations\n")
        f.write("**Target Users**: Sales teams for revenue optimization with actionable quantity targets\n\n")
        
        f.write("## Performance Classification\n")
        if ANALYSIS_LEVEL == "subcategory":
            f.write("- **Top Performer** (Z < -1.0): Exceeding cluster top quartile\n")
            f.write("- **Performing Well** (-1.0 ≤ Z ≤ 0): Meeting expectations\n")
            f.write("- **Some Opportunity** (0 < Z ≤ 1.0): Minor improvement potential\n")
            f.write("- **Good Opportunity** (1.0 < Z ≤ 2.5): Solid growth potential\n")
            f.write("- **Major Opportunity** (Z > 2.5): Significant underperformance\n\n")
        else:
            f.write("- **Top Performer** (Z < -0.8): Exceeding cluster top quartile\n")
            f.write("- **Performing Well** (-0.8 ≤ Z ≤ 0): Meeting expectations\n")
            f.write("- **Some Opportunity** (0 < Z ≤ 0.8): Minor improvement potential\n")
            f.write("- **Good Opportunity** (0.8 < Z ≤ 2.0): Solid growth potential\n")
            f.write("- **Major Opportunity** (Z > 2.0): Significant underperformance\n\n")
        
        f.write("## Store-Level Results\n")
        f.write(f"- Total stores analyzed: {len(results_df):,}\n")
        
        # Performance level distribution (with error handling)
        if 'store_performance_level' in results_df.columns and len(results_df) > 0:
            performance_counts = results_df['store_performance_level'].value_counts()
            for level, count in performance_counts.items():
                if level != 'no_data':
                    f.write(f"- {level.replace('_', ' ').title()}: {count} stores ({count/len(results_df)*100:.1f}%)\n")
        else:
            f.write("- No performance level data available\n")
        
        f.write(f"\n")
        
        # QUANTITY ENHANCEMENT: Add quantity metrics to summary (with error handling)
        f.write("## 🎯 UNIT QUANTITY INCREASE RECOMMENDATIONS\n")
        
        if all(col in results_df.columns for col in ['rule12_quantity_increase_recommended', 'total_quantity_increase_needed', 'total_investment_required']):
            total_stores_with_qty_recs = results_df['rule12_quantity_increase_recommended'].sum()
            total_qty_increase = results_df['total_quantity_increase_needed'].sum()
            total_investment = results_df['total_investment_required'].sum()
            
            f.write(f"- **Stores with quantity recommendations**: {total_stores_with_qty_recs:,} stores\n")
            f.write(f"- **Total quantity increase needed**: {total_qty_increase:,.1f} units/{TARGET_PERIOD_DAYS}-days\n")
            f.write(f"- **Total investment required**: ¥{total_investment:,.0f}\n")
            
            if total_stores_with_qty_recs > 0:
                avg_qty_per_store = total_qty_increase / total_stores_with_qty_recs
                avg_investment_per_store = total_investment / total_stores_with_qty_recs
                f.write(f"- **Average per store**: {avg_qty_per_store:.1f} units, ¥{avg_investment_per_store:.0f} investment\n")
        else:
            f.write("- No quantity recommendation data available\n")
    
    # Continue writing to summary file (append), after initial section
    with open(summary_file, 'a') as f:
        f.write(f"\n**Calculation Method**: Opportunity gaps converted to unit quantities using real sales data and constrained by maximum {int(MAX_INCREASE_PERCENTAGE*100)}% increase limits\n\n")
        
        if len(classified_data) > 0:
            f.write("## Key Insights\n")
            
            # Top opportunities with quantity focus (guarded against missing columns)
            major_opportunities = pd.DataFrame()
            if 'rule12_major_opportunity' in results_df.columns:
                major_opportunities = results_df[results_df['rule12_major_opportunity'] == 1]
            if len(major_opportunities) > 0:
                f.write(f"- **Major opportunity stores**: {len(major_opportunities)} stores with significant underperformance\n")
                if 'total_opportunity_value' in major_opportunities.columns:
                    f.write(f"- **Average opportunity value**: {major_opportunities['total_opportunity_value'].mean():.1f} units per store\n")
                
                # Quantity focus for major opportunities (guarded)
                if 'rule12_quantity_increase_recommended' in major_opportunities.columns:
                    major_with_qty = major_opportunities[major_opportunities['rule12_quantity_increase_recommended'].eq(True)]
                    if len(major_with_qty) > 0 and all(c in major_with_qty.columns for c in ['total_quantity_increase_needed','total_investment_required']):
                        avg_qty_major = major_with_qty['total_quantity_increase_needed'].mean()
                        avg_investment_major = major_with_qty['total_investment_required'].mean()
                        f.write(f"- **Major opportunity quantity needs**: {avg_qty_major:.1f} units/store, ¥{avg_investment_major:.0f}/store\n")
            
            # Top performers (guarded)
            top_performers = pd.DataFrame()
            if 'rule12_top_performer' in results_df.columns:
                top_performers = results_df[results_df['rule12_top_performer'] == 1]
            if len(top_performers) > 0:
                f.write(f"- **Top performers**: {len(top_performers)} stores exceeding cluster benchmarks\n")
                f.write(f"- **Learning opportunities**: Study practices from top performers\n")
            
            # Category insights
            if len(classified_data) > 0:
                major_opp_categories = classified_data[classified_data['performance_level'] == 'major_opportunity']
                if len(major_opp_categories) > 0:
                    if ANALYSIS_LEVEL == "subcategory":
                        category_col = 'sub_cate_name'
                        category_label = "subcategories"
                    else:
                        category_col = 'category_key'
                        category_label = "categories"
                    
                    top_opp_categories = major_opp_categories[category_col].value_counts().head(5)
                    f.write(f"\n**Top {category_label} with major opportunities**:\n")
                    for category, count in top_opp_categories.items():
                        f.write(f"- {category}: {count} stores\n")
        
        f.write(f"\n## 🎯 Recommendations for Sales Teams\n")
        if 'total_stores_with_qty_recs' in locals() and total_stores_with_qty_recs > 0:
            f.write(f"1. **Prioritize quantity increases** for {total_stores_with_qty_recs:,} stores with specific unit targets\n")
            f.write(f"2. **Focus on major opportunity {ANALYSIS_LEVEL}s** for immediate attention\n")
        else:
            f.write(f"1. **Review data availability** to generate quantity recommendations\n")
            f.write(f"2. **Focus on improving {ANALYSIS_LEVEL} performance** for opportunities\n")
        f.write("3. **Study top performer practices** for replication strategies\n")
        f.write(f"4. **Use realistic targets** based on cluster top {TOP_QUARTILE_PERCENTILE}th percentile performance\n")
        f.write("5. **Monitor progress** using quarterly re-analysis\n")
        f.write("6. **Budget planning**: Use investment requirements for procurement decisions\n")
        
        if ANALYSIS_LEVEL == "spu":
            f.write("7. **SPU-Level Precision**: Use granular SPU quantity data for precise inventory decisions\n")
            f.write("8. **Cross-Reference with Subcategory**: Compare SPU findings with subcategory trends\n")
    
    log_progress(f"Saved enhanced summary report with quantity metrics to {summary_file}")
    if labeled_summary_file:
        with open(labeled_summary_file, 'w') as lf:
            with open(summary_file, 'r') as src:
                lf.write(src.read())
        log_progress(f"Saved labeled summary report to {labeled_summary_file}")
    # Register summary(s) in manifest
    summary_meta = {
        "target_year": ty,
        "target_month": tm if ty else None,
        "target_period": tp,
        "analysis_level": ANALYSIS_LEVEL,
        "seasonal_blending_enabled": bool(USE_BLENDED_SEASONAL),
        "file_format": "md",
    }
    register_step_output("step12", "rule12_summary", summary_file, metadata=summary_meta)
    if labeled_summary_file:
        register_step_output("step12", f"rule12_summary_{label}", labeled_summary_file, metadata=summary_meta)
    
    # Save backward-compatible summary for subcategory analysis
    if ANALYSIS_LEVEL == "subcategory":
        backward_summary_file = "output/rule12_sales_performance_summary.md"
        with open(backward_summary_file, 'w') as f:
            f.write("# Rule 12: Sales Performance Deviation Analysis Summary\n\n")
            f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Rule Definition\n")
            f.write("**Purpose**: Identify sales opportunities by comparing store subcategory performance against cluster top quartile (75th percentile)\n\n")
            f.write("**Method**: Opportunity gap Z-score analysis\n")
            f.write("**Target Users**: Sales teams for revenue optimization\n\n")
            
            f.write("## Performance Classification\n")
            f.write("- **Top Performer** (Z < -1.0): Exceeding cluster top quartile\n")
            f.write("- **Performing Well** (-1.0 ≤ Z ≤ 0): Meeting expectations\n")
            f.write("- **Some Opportunity** (0 < Z ≤ 1.0): Minor improvement potential\n")
            f.write("- **Good Opportunity** (1.0 < Z ≤ 2.5): Solid growth potential\n")
            f.write("- **Major Opportunity** (Z > 2.5): Significant underperformance\n\n")
            
            f.write("## Store-Level Results\n")
            f.write(f"- Total stores analyzed: {len(results_df):,}\n")
            
            # Performance level distribution (with error handling)
            if 'store_performance_level' in results_df.columns and len(results_df) > 0:
                performance_counts = results_df['store_performance_level'].value_counts()
            else:
                performance_counts = {}
            for level, count in performance_counts.items():
                if level != 'no_data':
                    f.write(f"- {level.replace('_', ' ').title()}: {count} stores ({count/len(results_df)*100:.1f}%)\n")
            
            f.write(f"\n")
            
            if len(classified_data) > 0:
                f.write("## Key Insights\n")
                
                # Top opportunities
                major_opportunities = results_df[results_df['rule12_major_opportunity'] == 1]
                if len(major_opportunities) > 0:
                    f.write(f"- **Major opportunity stores**: {len(major_opportunities)} stores with significant underperformance\n")
                    f.write(f"- **Average opportunity value**: {major_opportunities['total_opportunity_value'].mean():.1f} units per store\n")
                
                # Top performers
                top_performers = results_df[results_df['rule12_top_performer'] == 1]
                if len(top_performers) > 0:
                    f.write(f"- **Top performers**: {len(top_performers)} stores exceeding cluster benchmarks\n")
                    f.write(f"- **Learning opportunities**: Study practices from top performers\n")
                
                # Subcategory insights
                major_opp_subcats = classified_data[classified_data['performance_level'] == 'major_opportunity']
                if len(major_opp_subcats) > 0:
                    top_opp_subcats = major_opp_subcats['sub_cate_name'].value_counts().head(5)
                    f.write(f"\n**Top subcategories with major opportunities**:\n")
                    for subcat, count in top_opp_subcats.items():
                        f.write(f"- {subcat}: {count} stores\n")
            
            f.write(f"\n## Recommendations for Sales Teams\n")
            f.write("1. **Prioritize major opportunity subcategories** for immediate attention\n")
            f.write("2. **Study top performer practices** for replication strategies\n")
            f.write("3. **Focus on realistic targets** based on cluster top quartile performance\n")
            f.write("4. **Monitor progress** using quarterly re-analysis\n")
        
        log_progress(f"Saved backward-compatible summary to {backward_summary_file}")

def main(testing_mode: bool = False, args: Optional[argparse.Namespace] = None, period_label: Optional[str] = None) -> None:
    """Main function to execute the sales performance deviation analysis"""
    mode_text = "FAST TESTING" if testing_mode else "FULL ANALYSIS"
    log_progress(f"Starting Rule 12: Sales Performance Deviation Analysis ({ANALYSIS_LEVEL.title()}-Level) — {mode_text}...")
    
    try:
        # Load data
        cluster_df, category_df, quantity_df = load_data()

        # Optional testing-mode sampling to speed up runs
        if testing_mode:
            try:
                unique_stores = pd.Series(cluster_df['str_code'].astype(str).unique())
                sample_n = min(200, len(unique_stores))
                sampled = set(unique_stores.sample(n=sample_n, random_state=42).tolist())
                cluster_df = cluster_df[cluster_df['str_code'].astype(str).isin(sampled)].copy()
                category_df = category_df[category_df['str_code'].astype(str).isin(sampled)].copy()
                quantity_df = quantity_df[quantity_df['str_code'].astype(str).isin(sampled)].copy()
                log_progress(f"TEST MODE: Sampled {len(sampled)} stores for quick run")
            except Exception as _:
                log_progress("TEST MODE: Sampling skipped due to data constraints")
        
        # Prepare sales data
        sales_data = prepare_sales_data(category_df, cluster_df, quantity_df)
        
        if len(sales_data) == 0:
            log_progress("No valid sales data found. Creating empty results.")
            
            # STANDARDIZATION FIX: Use cluster_id instead of Cluster for consistency
            if 'Cluster' in cluster_df.columns and 'cluster_id' not in cluster_df.columns:
                cluster_df['cluster_id'] = cluster_df['Cluster']
            elif 'cluster_id' not in cluster_df.columns:
                cluster_df['cluster_id'] = cluster_df.get('Cluster', 0)
            
            results_df = cluster_df[['str_code', 'cluster_id']].copy()
            
            # Create empty results
            for level in ['top_performer', 'performing_well', 'some_opportunity', 'good_opportunity', 'major_opportunity']:
                results_df[f'rule12_{level}'] = 0
            
            results_df['avg_opportunity_z_score'] = 0
            results_df['total_opportunity_value'] = 0
            
            if ANALYSIS_LEVEL == "subcategory":
                results_df['subcategories_analyzed'] = 0
                results_df['top_quartile_subcategories'] = 0
            else:
                results_df['categories_analyzed'] = 0
                results_df['top_quartile_categories'] = 0
            
            results_df['store_performance_level'] = 'no_data'
            results_df['rule12_description'] = f'Sales performance vs cluster top {TOP_QUARTILE_PERCENTILE}th percentile'
            results_df['rule12_analysis_method'] = 'Opportunity gap Z-score analysis'
            
            save_results(results_df, pd.DataFrame(), period_label=period_label)
            return
        
        # Calculate opportunity gaps
        opportunity_data = calculate_opportunity_gaps(sales_data)
        
        if len(opportunity_data) == 0:
            log_progress("No valid opportunity data found. Creating empty results.")
            results_df = aggregate_store_performance(pd.DataFrame(), cluster_df)
            save_results(results_df, pd.DataFrame(), period_label=period_label)
            return
        
        # Calculate Z-scores
        z_score_data = calculate_opportunity_z_scores(opportunity_data)
        
        # Classify performance levels
        classified_data = classify_performance_levels(z_score_data, quantity_df)
        
        # Aggregate to store level
        results_df = aggregate_store_performance(classified_data, cluster_df)
        
        # Save results
        save_results(results_df, classified_data, period_label=period_label)
        
        # SEASONAL BLENDING BENEFITS: Log the strategic advantages for August
        if USE_BLENDED_SEASONAL:
            log_progress("\n🍂 SEASONAL BLENDING BENEFITS FOR SALES PERFORMANCE ANALYSIS:")
            log_progress("   ✓ Summer clearance opportunities: Identified from recent trends (May-July)")
            log_progress("   ✓ Autumn transition planning: Identified from seasonal patterns (Aug 2024)")
            log_progress("   ✓ Balanced performance analysis: Avoids over-focusing on summer-only styles")
            log_progress("   ✓ Strategic sales optimization: Supports autumn assortment planning")
            log_progress("   ✓ Business rationale: Performance analysis considers seasonal transitions")
        
        log_progress(f"Rule 12: Sales Performance Deviation Analysis ({ANALYSIS_LEVEL.title()}-Level) completed successfully!")
        
    except Exception as e:
        log_progress(f"Error in Rule 12 analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rule 12: Sales Performance with Quantity Recommendations")
    parser.add_argument("--yyyymm", type=str, help="Source year-month label (e.g., 202508)")
    parser.add_argument("--period", type=str, choices=["A", "B"], help="Source period within month: A or B")
    parser.add_argument("--target-yyyymm", dest="target_yyyymm", type=str, help="Target year-month label for outputs (e.g., 202509)")
    parser.add_argument("--target-period", dest="target_period", type=str, choices=["A", "B"], help="Target period label for outputs: A or B")
    parser.add_argument("--seasonal-blending", dest="seasonal_blending", action="store_true", help="Force enable seasonal blending")
    parser.add_argument("--no-seasonal-blending", dest="no_seasonal_blending", action="store_true", help="Disable seasonal blending")
    parser.add_argument("--seasonal-weight", dest="seasonal_weight", type=float, help="Seasonal blending weight (0-1). Recent weight = 1 - seasonal_weight")
    parser.add_argument("--seasonal-quantity-file", dest="seasonal_quantity_file", type=str, help="Path to seasonal quantity anchor CSV (overrides SEASONAL_QUANTITY_FILE)")
    parser.add_argument("--test", action="store_true", help="Run in test mode with sampled data for speed")
    # Join/threshold overrides (optional)
    parser.add_argument("--join-mode", type=str, choices=["left","inner"], help="Cluster join mode: left (inclusive) or inner (stricter)")
    parser.add_argument("--top-quartile", type=int, help="Top percentile benchmark (e.g., 75 or 80)")
    parser.add_argument("--min-cluster-size", type=int, help="Minimum stores in cluster for analysis")
    parser.add_argument("--min-sales-volume", type=float, help="Minimum sales to include in analysis")
    parser.add_argument("--min-increase-qty", type=float, help="Minimum unit increase to recommend")
    parser.add_argument("--max-increase-pct", type=float, help="Maximum percentage increase per case (0-1)")
    parser.add_argument("--max-recs-per-store", type=int, help="Cap recommendations per store")
    parser.add_argument("--min-investment", type=float, help="Minimum investment (currency) to keep a case")
    parser.add_argument("--min-opportunity-score", type=float, help="Minimum opportunity score (0-1)")
    parser.add_argument("--min-z", type=float, help="Minimum Z-score for actionability")
    parser.add_argument("--max-total-qty-per-store", dest="max_total_qty_per_store", type=float, help="Optional total unit cap per store; omit for no cap")
    return parser.parse_args()

def _derive_period_label(args: argparse.Namespace) -> str:
    # Prefer explicit target flags, then env, then source flags, then defaults
    yyyymm = (
        (args.target_yyyymm if hasattr(args, 'target_yyyymm') else None)
        or os.environ.get("PIPELINE_TARGET_YYYYMM")
        or (args.yyyymm if hasattr(args, 'yyyymm') else None)
        or datetime.now().strftime("%Y%m")
    )
    period = (
        (args.target_period if hasattr(args, 'target_period') else None)
        or os.environ.get("PIPELINE_TARGET_PERIOD")
        or (args.period if hasattr(args, 'period') else None)
        or "A"
    )
    os.environ["PIPELINE_TARGET_YYYYMM"] = yyyymm
    os.environ["PIPELINE_TARGET_PERIOD"] = period
    return f"{yyyymm}{period}"

if __name__ == "__main__":
    args = _parse_args()
    # Seasonal blending override
    if getattr(args, 'seasonal_blending', False) and getattr(args, 'no_seasonal_blending', False):
        log_progress("⚠️ Both --seasonal-blending and --no-seasonal-blending provided; using default detection")
    else:
        if getattr(args, 'seasonal_blending', False):
            USE_BLENDED_SEASONAL = True
        elif getattr(args, 'no_seasonal_blending', False):
            USE_BLENDED_SEASONAL = False
    # Seasonal parameter overrides
    if getattr(args, 'seasonal_weight', None) is not None:
        os.environ["SEASONAL_WEIGHT"] = str(args.seasonal_weight)
    if getattr(args, 'seasonal_quantity_file', None):
        os.environ["SEASONAL_QUANTITY_FILE"] = args.seasonal_quantity_file
    label = _derive_period_label(args)
    log_progress(f"Using TARGET PERIOD label: {label}")
    log_progress(f"Seasonal blending: {'ENABLED' if USE_BLENDED_SEASONAL else 'DISABLED'}")
    # Apply optional runtime overrides
    try:
        if getattr(args, 'join_mode', None) in ('left','inner'):
            JOIN_MODE = args.join_mode
        if getattr(args, 'top_quartile', None) is not None:
            TOP_QUARTILE_PERCENTILE = int(args.top_quartile)
        if getattr(args, 'min_cluster_size', None) is not None:
            MIN_CLUSTER_SIZE = int(args.min_cluster_size)
        if getattr(args, 'min_sales_volume', None) is not None:
            MIN_SALES_VOLUME = float(args.min_sales_volume)
        if getattr(args, 'min_increase_qty', None) is not None:
            MIN_INCREASE_QUANTITY = float(args.min_increase_qty)
        if getattr(args, 'max_increase_pct', None) is not None:
            MAX_INCREASE_PERCENTAGE = float(args.max_increase_pct)
        if getattr(args, 'max_recs_per_store', None) is not None:
            MAX_RECOMMENDATIONS_PER_STORE = int(args.max_recs_per_store)
        # optional total quantity cap override
        if hasattr(args, 'max_total_qty_per_store') and getattr(args, 'max_total_qty_per_store') is not None:
            MAX_TOTAL_QUANTITY_PER_STORE = float(getattr(args, 'max_total_qty_per_store'))
        if getattr(args, 'min_investment', None) is not None:
            MIN_INVESTMENT_THRESHOLD = float(args.min_investment)
        if getattr(args, 'min_opportunity_score', None) is not None:
            MIN_OPPORTUNITY_SCORE = float(args.min_opportunity_score)
        if getattr(args, 'min_z', None) is not None:
            MIN_Z_SCORE_THRESHOLD = float(args.min_z)
    except Exception:
        pass
    main(testing_mode=getattr(args, 'test', False), args=args, period_label=label)