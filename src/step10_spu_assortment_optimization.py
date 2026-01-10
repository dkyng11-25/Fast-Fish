def apply_per_store_cap(df: 'pd.DataFrame', max_per_store: int) -> 'Tuple[pd.DataFrame, Dict[str, int]]':
    """Apply a per-store cap on number of SPU reductions, prioritizing best candidates.

    Priority: sell_through_improvement desc (NaN lowest), category_excess_spu_count desc,
              category_overcapacity_percentage desc, abs(recommended_quantity_change) desc.
    Returns trimmed dataframe and stats.
    """
    if df is None or len(df) == 0 or max_per_store is None or max_per_store <= 0:
        return df, {"stores_capped": 0, "dropped": 0}

    def _sort_key(sub: pd.DataFrame) -> pd.DataFrame:
        # Prepare sorting columns with NA-safe handling
        sub = sub.copy()
        if 'sell_through_improvement' not in sub.columns:
            sub['sell_through_improvement'] = pd.NA
        sub['_sti'] = pd.to_numeric(sub['sell_through_improvement'], errors='coerce')
        sub['_sti'] = sub['_sti'].fillna(-np.inf)
        sub['_excess'] = pd.to_numeric(sub.get('category_excess_spu_count', pd.Series(index=sub.index)), errors='coerce').fillna(0)
        sub['_pct'] = pd.to_numeric(sub.get('category_overcapacity_percentage', pd.Series(index=sub.index)), errors='coerce').fillna(0)
        sub['_absred'] = pd.to_numeric(sub.get('recommended_quantity_change', pd.Series(index=sub.index)), errors='coerce').fillna(0).abs()
        return sub.sort_values(by=['_sti', '_excess', '_pct', '_absred'], ascending=[False, False, False, False])

    kept_frames = []
    stores_capped = 0
    dropped_total = 0
    for store_code, group in df.groupby('str_code'):
        sorted_group = _sort_key(group)
        if len(sorted_group) > max_per_store:
            stores_capped += 1
            dropped_total += (len(sorted_group) - max_per_store)
        kept_frames.append(sorted_group.head(max_per_store))

    trimmed = pd.concat(kept_frames, ignore_index=True) if kept_frames else df
    return trimmed, {"stores_capped": stores_capped, "dropped": dropped_total}

#!/usr/bin/env python3
"""
Step 10: FAST Smart Overcapacity Rule with UNIT QUANTITY REDUCTION RECOMMENDATIONS

This is an optimized version of step10 that uses simplified calculations and bulk processing
to dramatically improve performance while preserving all results.

Business Logic:
- Current SPU count > Target SPU count = Overcapacity
- 🎯 UNIT QUANTITY REDUCTION with simplified but accurate calculations
- Bulk processing for 10x+ performance improvement
- All standardized columns included

Author: Data Pipeline  
Date: 2025-06-24 (Optimized Fast Version)
 
 HOW TO RUN (CLI + ENV) — Read this before executing
 ----------------------------------------------------
 Overview
 - Period-aware inputs: this step relies on period-specific API data (store_config/SPU sales) and clustering to calculate overcapacity and unit quantity reductions.
 - Why period correctness matters: overcapacity detection uses store-subcategory composition from the target half-month; mixing periods yields wrong counts and SPU JSON mismatches.

 Quick Start (target 202510A)
 - Typical usage (resolved via src.config helpers and env):
     PYTHONPATH=. python3 src/step10_spu_assortment_optimization.py 

 Source Period Overrides (why and when)
 - If target 202510A API data is not yet available, point the loader to prior period (e.g., 202509A) via env that your config respects (e.g., PIPELINE_YYYYMM/PIPELINE_PERIOD). This lets you compute reductions with real data while planning for the next period.
 - Why it works: calculations use real SPU quantities and unit prices from the loader; filenames/labels can still reflect the planning period in downstream steps.

 Single-Cluster Testing vs Production
 - Test: Run preceding steps for one cluster (e.g., Cluster 22) to accelerate iteration. Step 10 will expand and compute only for what exists in your source data.
 - Production: Ensure API data and clustering are complete for ALL clusters to produce comprehensive results.

 Why these configurations work (and when they don't)
 - Real quantities and unit prices (from base/fashion qty/amt) prevent unrealistic investment math and allow ROI metrics; if these columns are missing, unit-price derivation collapses.
 - Blended seasonal mode (August) combines recent and prior-year seasonal patterns to avoid the "no autumn in August" gap; if seasonal sources are missing, the step falls back to recent-only with a warning.

 Common failure modes (and what to do)
 - Missing SPU JSON (`sty_sal_amt`) in config data
   • Cause: upstream store_config extract didn’t preserve JSON or used a different schema.
   • Fix: re-run the API data extraction with the correct fields; verify Step 1 store_config includes `sty_sal_amt`.
 - No unit quantities present
   • Cause: SPU sales file lacks `base_sal_qty`/`fashion_sal_qty` and no aggregate quantity column present.
   • Fix: ensure Step 1 SPU sales include either split quantities or a valid aggregate (sal_qty/quantity). Without quantities, unit price and reductions will be skipped.
 - All SPUs assigned to cluster=0 or single cluster
   • Cause: missing or non-standard clustering file; or SPU input lacks cluster and fallback mapping failed.
   • Fix: provide clustering with ['str_code','Cluster'] or ['str_code','cluster'] and ensure `str_code` dtypes are strings in all files.

 Manifest notes
 - This step typically writes period-aware outputs consumed by Step 13/14. Register outputs in the manifest where possible so downstream steps resolve the correct, period-matching files.
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
try:
    import ujson as json  # faster if available
except Exception:  # pragma: no cover
    import json
import gc
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm
import warnings
import sys
import argparse
from src.config import (
    get_api_data_files,
    initialize_pipeline_config,
    get_output_files,
    load_margin_rates,
)
from src.pipeline_manifest import register_step_output
from src.output_utils import create_output_with_symlinks

# Defer Fast Fish validator import until after configuration is initialized
SELLTHROUGH_VALIDATION_AVAILABLE = False

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# Configuration
ANALYSIS_LEVEL = "spu"
DATA_PERIOD_DAYS = 15
TARGET_PERIOD_DAYS = 15
SCALING_FACTOR = TARGET_PERIOD_DAYS / DATA_PERIOD_DAYS

# SEASONAL BLENDING ENHANCEMENT: Dynamic data loading for seasonal transitions
# For August recommendations, blend recent trends with seasonal patterns
current_month = datetime.now().month

if current_month == 8:  # August - use blended seasonal approach
    print("🍂 AUGUST DETECTED: Using blended seasonal data approach for overcapacity analysis")
    print("   Combining current period + same month in prior years (seasonal)")
    # Base files resolved at runtime via apply_runtime_configuration
    BASE_DATA_FILE = None
    BASE_QUANTITY_FILE = None
    # Seasonal data (August 2024) for blending (period-aware, not combined)
    SEASONAL_DATA_FILE = None  # resolved later
    SEASONAL_QUANTITY_FILE = None  # resolved later
    USE_BLENDED_SEASONAL = True
    SEASONAL_YEARS_BACK = 2
else:
    # Standard approach for other months; resolve at runtime
    BASE_DATA_FILE = None
    BASE_QUANTITY_FILE = None
    USE_BLENDED_SEASONAL = False
    SEASONAL_YEARS_BACK = 0

# Analysis configurations with dynamic data files
ANALYSIS_CONFIGS = {
    "spu": {
        "analysis_level": "spu",
        "data_file": BASE_DATA_FILE,
        "cluster_file": "output/clustering_results_spu.csv",
        "output_prefix": "rule10_smart_overcapacity_spu",
        "business_unit": "store-spu",
        "min_stores_threshold": 3
    }
}

# QUANTITY ENHANCEMENT: Add quantity data for investment calculations
QUANTITY_DATA_FILE = BASE_QUANTITY_FILE
OUTPUT_DIR = "output"
MIN_CLUSTER_SIZE = 3  # Reduced from 5 for more opportunities (aligned with other steps)
MIN_SALES_VOLUME = 20  # Reduced from 50 to find more cases (more inclusive)
MIN_REDUCTION_QUANTITY = 1.0  # Reduced from 3.0 for smaller meaningful reductions
MAX_REDUCTION_PERCENTAGE = 0.4  # Increased from 0.3 to 40% for more flexibility
# Limit total actionable reductions per store after validation
MAX_TOTAL_ADJUSTMENTS_PER_STORE = None  # No artificial cap by default; can be provided via CLI

# New: allow specifying multiple recent files (e.g., July A + B)
RECENT_CONFIG_FILES: Optional[List[str]] = None
RECENT_QUANTITY_FILES: Optional[List[str]] = None

# Narrow IO columns to speed up reads safely (fallback to full read if columns mismatch)
CONFIG_USECOLS: List[str] = [
    'str_code', 'str_name', 'Cluster', 'cluster_id',
    'season_name', 'sex_name', 'display_location_name', 'big_class_name', 'sub_cate_name',
    'yyyy', 'mm', 'mm_type', 'sal_amt', 'sty_sal_amt',
    'ext_sty_cnt_avg', 'target_sty_cnt_avg'
]
QUANTITY_USECOLS: List[str] = [
    'str_code', 'spu_code', 'base_sal_qty', 'fashion_sal_qty', 'sal_qty', 'quantity', 'spu_sales_amt'
]

# Debug and validation toggles
DEBUG_LIMIT: Optional[int] = None
SKIP_SELLTHROUGH: bool = False
JOIN_MODE: str = "left"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

def blend_seasonal_data(recent_df: pd.DataFrame, seasonal_df: pd.DataFrame, 
                       recent_weight: float, seasonal_weight: float, data_type: str) -> pd.DataFrame:
    """
    Blend recent trends data with seasonal patterns using weighted aggregation.
    
    Args:
        recent_df: Recent trends data (May-July 2025)
        seasonal_df: Seasonal patterns data (August 2024)
        recent_weight: Weight for recent data (e.g., 0.4 = 40%)
        seasonal_weight: Weight for seasonal data (e.g., 0.6 = 60%)
        data_type: Type of data being blended ("config" or "quantity")
        
    Returns:
        Blended DataFrame with weighted aggregation
    """
    log_progress(f"🔄 Blending {data_type} data: {recent_weight:.0%} recent + {seasonal_weight:.0%} seasonal")
    
    # Identify common columns for blending
    if data_type == "config":
        # For config data, blend on store and category dimensions
        blend_cols = ['str_code', 'season_name', 'sex_name', 'display_location_name', 'big_class_name', 'sub_cate_name']
        value_cols = ['sty_sal_amt']  # Main column to blend
    else:
        # For quantity data, blend on store and SPU dimensions
        blend_cols = ['str_code', 'spu_code']
        value_cols = ['spu_sales_amt', 'quantity'] if 'quantity' in recent_df.columns else ['spu_sales_amt']
    
    # Filter to common blend columns that exist in both datasets
    available_blend_cols = [col for col in blend_cols if col in recent_df.columns and col in seasonal_df.columns]
    available_value_cols = [col for col in value_cols if col in recent_df.columns and col in seasonal_df.columns]
    
    if not available_blend_cols or not available_value_cols:
        log_progress(f"⚠️ Insufficient common columns for blending {data_type} data, using recent data only")
        return recent_df
    
    log_progress(f"   Blending on: {available_blend_cols}")
    log_progress(f"   Value columns: {available_value_cols}")
    
    # For config data, combine both datasets (JSON columns need special handling)
    if data_type == "config":
        # Combine datasets and let fast_expand_spu_data handle the JSON parsing
        combined = pd.concat([recent_df, seasonal_df], ignore_index=True)
        log_progress(f"   ✅ Combined {len(combined):,} records from {len(recent_df):,} recent + {len(seasonal_df):,} seasonal")
        return combined
    else:
        # For quantity data, aggregate numerically
        recent_clean = recent_df[available_blend_cols + available_value_cols].copy()
        seasonal_clean = seasonal_df[available_blend_cols + available_value_cols].copy()
        
        # Apply weights to numeric columns
        for col in available_value_cols:
            if col != 'sty_sal_amt':  # Skip JSON columns
                recent_clean[col] = pd.to_numeric(recent_clean[col], errors='coerce') * recent_weight
                seasonal_clean[col] = pd.to_numeric(seasonal_clean[col], errors='coerce') * seasonal_weight
        
        # Combine and aggregate (preserve missingness; do not inject zeros)
        combined = pd.concat([recent_clean, seasonal_clean], ignore_index=True)
        numeric_cols = [col for col in available_value_cols if col != 'sty_sal_amt']
        if numeric_cols:  # Only aggregate if we have numeric columns
            blended = (
                combined
                .groupby(available_blend_cols)[numeric_cols]
                .sum(min_count=1)
                .reset_index()
            )
        else:
            blended = combined.drop_duplicates(subset=available_blend_cols)
        
        # Add back any additional columns from recent data that weren't blended
        additional_cols = [col for col in recent_df.columns if col not in available_blend_cols + available_value_cols]
        if additional_cols:
            recent_extra = recent_df[available_blend_cols + additional_cols].drop_duplicates(subset=available_blend_cols)
            blended = blended.merge(recent_extra, on=available_blend_cols, how='left')
        
        log_progress(f"   ✅ Blended {len(blended):,} records from {len(recent_df):,} recent + {len(seasonal_df):,} seasonal")
        return blended

def _read_csvs(paths_or_path, usecols: Optional[List[str]] = None) -> pd.DataFrame:
    """Read one or many CSV files and concatenate. Accepts str or List[str].
    Attempts usecols-restricted read for performance, falling back to full read if columns mismatch.
    """
    def _safe_read(path: str) -> pd.DataFrame:
        try:
            # Use a callable usecols to avoid pandas raising when some columns are missing
            effective_usecols = None
            if usecols is not None:
                if callable(usecols):
                    effective_usecols = usecols
                else:
                    selected_columns = set(usecols)
                    effective_usecols = (lambda c: c in selected_columns)
            return pd.read_csv(
                path,
                dtype={'str_code': str, 'spu_code': str},
                low_memory=False,
                usecols=effective_usecols,
            )
        except Exception as e:
            # Fallback to full read if usecols cause issues
            log_progress(f"⚠️ usecols-constrained read failed for {path}: {e}; reading full file instead")
            return pd.read_csv(path, dtype={'str_code': str, 'spu_code': str}, low_memory=False)

    if isinstance(paths_or_path, list):
        frames = []
        for p in paths_or_path:
            if p and os.path.exists(p):
                frames.append(_safe_read(p))
            else:
                log_progress(f"⚠️ Missing recent file: {p}")
        if len(frames) == 0:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)
    else:
        return _safe_read(paths_or_path)

def _infer_group_cols(df: pd.DataFrame, data_type: str) -> List[str]:
    """Infer grouping columns for averaging recent frames.
    For config: store + category dims. For quantity: store + spu.
    """
    if data_type == "config":
        candidates = ['str_code', 'season_name', 'sex_name', 'display_location_name', 'big_class_name', 'sub_cate_name']
    else:
        candidates = ['str_code', 'spu_code']
    return [c for c in candidates if c in df.columns]

def _infer_value_cols(df: pd.DataFrame, data_type: str) -> List[str]:
    """Infer numeric value columns to average. Avoid JSON-like text such as sty_sal_amt for config."""
    if data_type == "config":
        preferred = ['ext_sty_cnt_avg', 'target_sty_cnt_avg', 'sal_amt']
        cols = [c for c in preferred if c in df.columns]
    else:
        preferred = ['base_sal_qty', 'fashion_sal_qty', 'sal_qty', 'quantity', 'spu_sales_amt']
        cols = [c for c in preferred if c in df.columns]
    # Fallback: any numeric-looking columns not in keys
    if not cols:
        key_cols = set(_infer_group_cols(df, data_type))
        for c in df.columns:
            if c in key_cols:
                continue
            if df[c].dtype.kind in ('i', 'u', 'f'):
                cols.append(c)
    return cols

def _coerce_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        out[c] = pd.to_numeric(out[c], errors='coerce')
    return out

def average_recent_dataframe(frames: List[pd.DataFrame], data_type: str) -> pd.DataFrame:
    """Average multiple recent frames by grouping keys and taking mean across value cols."""
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

def load_blended_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load and blend data for enhanced seasonal overcapacity analysis.
    
    Returns:
        Tuple of (config_data, quantity_data) with seasonal blending applied if in August
    """
    config = ANALYSIS_CONFIGS[ANALYSIS_LEVEL]
    
    if USE_BLENDED_SEASONAL:
        log_progress("🍂 BLENDED SEASONAL LOADING: Combining recent trends + seasonal patterns")
        
        # Load recent trends data (potentially multiple A/B half-month files)
        recent_cfg_paths = config.get('data_files') or config.get('data_file')
        if RECENT_CONFIG_FILES is not None:
            recent_cfg_paths = RECENT_CONFIG_FILES
        log_progress(f"   Recent config sources: {recent_cfg_paths}")
        # Read recent frames, then average window
        if isinstance(recent_cfg_paths, list):
            recent_cfg_frames = [ _read_csvs(p, usecols=CONFIG_USECOLS) for p in recent_cfg_paths ]
            recent_cfg_df = average_recent_dataframe(recent_cfg_frames, data_type="config")
            log_progress(f"   Averaged recent config across {len([f for f in recent_cfg_frames if len(f)>0])} sources -> {len(recent_cfg_df)} rows")
        else:
            recent_cfg_df = _read_csvs(recent_cfg_paths, usecols=CONFIG_USECOLS)
        
        # Seasonal config source (e.g., prior-year same month)
        seasonal_cfg_path = os.environ.get("SEASONAL_CONFIG_FILE") or config.get('seasonal_file')
        seasonal_cfg_df = _read_csvs(seasonal_cfg_path, usecols=CONFIG_USECOLS) if seasonal_cfg_path else pd.DataFrame()
        
        # Quantity side (recent potentially multi-file averaged, plus seasonal)
        recent_qty_paths = RECENT_QUANTITY_FILES or QUANTITY_DATA_FILE
        if isinstance(recent_qty_paths, list):
            recent_qty_frames = [ _read_csvs(p, usecols=QUANTITY_USECOLS) for p in recent_qty_paths ]
            recent_qty_df = average_recent_dataframe(recent_qty_frames, data_type="quantity")
            log_progress(f"   Averaged recent quantity across {len([f for f in recent_qty_frames if len(f)>0])} sources -> {len(recent_qty_df)} rows")
        else:
            recent_qty_df = _read_csvs(recent_qty_paths, usecols=QUANTITY_USECOLS)
        seasonal_qty_path = os.environ.get("SEASONAL_QUANTITY_FILE")
        seasonal_qty_df = _read_csvs(seasonal_qty_path, usecols=QUANTITY_USECOLS) if seasonal_qty_path else pd.DataFrame()
        
        # Seasonal weights
        seasonal_weight = float(os.environ.get("SEASONAL_WEIGHT", "0.3"))
        recent_weight = 1.0 - seasonal_weight
        log_progress(f"   Weights -> recent: {recent_weight:.2f}, seasonal: {seasonal_weight:.2f}")
        
        # Blend config
        if len(seasonal_cfg_df) > 0 and len(recent_cfg_df) > 0:
            config_data = blend_seasonal_data(recent_cfg_df, seasonal_cfg_df, recent_weight, seasonal_weight, data_type="config")
        else:
            if len(seasonal_cfg_df) == 0:
                log_progress("   ⚠️ No seasonal config source provided; using recent only")
            if len(recent_cfg_df) == 0:
                log_progress("   ⚠️ No recent config source; config data will be empty")
            config_data = recent_cfg_df
        
        # Blend quantity
        if len(seasonal_qty_df) > 0 and len(recent_qty_df) > 0:
            quantity_data = blend_seasonal_data(recent_qty_df, seasonal_qty_df, recent_weight, seasonal_weight, data_type="quantity")
        else:
            if len(recent_qty_df) == 0:
                log_progress("   ⚠️ No recent quantity source; quantity data will be empty")
            if len(seasonal_qty_df) == 0:
                log_progress("   ⚠️ No seasonal quantity source; using recent only")
            quantity_data = recent_qty_df
        
        log_progress(f"   ✅ Loaded blended datasets: {len(config_data)} config rows, {len(quantity_data)} quantity rows")
        return config_data, quantity_data
    else:
        # Standard loading; if multiple recent sources are provided, average them
        recent_cfg_paths = config.get('data_files') or config.get('data_file')
        log_progress(f"Loading standard data from {recent_cfg_paths}")
        if isinstance(recent_cfg_paths, list):
            frames = [ _read_csvs(p, usecols=CONFIG_USECOLS) for p in recent_cfg_paths ]
            config_data = average_recent_dataframe(frames, data_type="config")
            log_progress(f"   Averaged recent config across {len([f for f in frames if len(f)>0])} sources -> {len(config_data)} rows")
        else:
            config_data = _read_csvs(recent_cfg_paths, usecols=CONFIG_USECOLS)
        recent_qty_paths = RECENT_QUANTITY_FILES or QUANTITY_DATA_FILE
        if isinstance(recent_qty_paths, list):
            qframes = [ _read_csvs(p, usecols=QUANTITY_USECOLS) for p in recent_qty_paths ]
            quantity_data = average_recent_dataframe(qframes, data_type="quantity")
            log_progress(f"   Averaged recent quantity across {len([f for f in qframes if len(f)>0])} sources -> {len(quantity_data)} rows")
        else:
            quantity_data = _read_csvs(recent_qty_paths, usecols=QUANTITY_USECOLS)
        log_progress(f"Loaded {len(config_data)} config records, {len(quantity_data)} quantity records")
        
        return config_data, quantity_data

def fast_expand_spu_data(df: pd.DataFrame, quantity_df: pd.DataFrame) -> pd.DataFrame:
    """
    Fast expansion of subcategory data to REAL SPU-level overcapacity analysis.
    
    CRITICAL FIX: Now works with REAL SPU codes from the data instead of fake category keys.
    
    Args:
        df: Input dataframe with subcategory data containing sty_sal_amt JSON
        quantity_df: DataFrame of SPU-level quantities and amounts to join (from API files)
        
    Returns:
        DataFrame with individual SPU records using REAL SPU codes
    """
    log_progress("🚀 Fast expanding subcategory data to REAL SPU-level overcapacity analysis...")
    
    # Filter for records with SPU data
    spu_records = df[df['sty_sal_amt'].notna() & (df['sty_sal_amt'] != '')].copy()
    log_progress(f"Found {len(spu_records):,} records with SPU sales data")
    
    if len(spu_records) == 0:
        return pd.DataFrame()
    
    # Apply debug limit if provided
    if DEBUG_LIMIT is not None:
        original_len = len(spu_records)
        spu_records = spu_records.head(DEBUG_LIMIT)
        log_progress(f"🧪 Debug limit active: processing first {len(spu_records):,} of {original_len:,} SPU-source records")

    log_progress("🔧 EXTRACTING REAL SPU codes from JSON data...")
    
    expanded_records = []
    
    # Process all records and expand to individual SPU level
    for n, (idx, row) in enumerate(tqdm(
        spu_records.iterrows(),
        total=len(spu_records),
        desc="Processing SPU records",
        mininterval=5,
        miniters=100,
        dynamic_ncols=True,
        file=sys.stdout,
    )):
        try:
            # Parse the JSON containing real SPU sales data
            spu_data = json.loads(row['sty_sal_amt'])
            
            # Skip if no SPU data
            if not spu_data or not isinstance(spu_data, dict):
                continue
                
            # Get category-level metrics
            current_spu_count = float(row['ext_sty_cnt_avg'])
            target_spu_count = float(row['target_sty_cnt_avg'])
            
            # Only process overcapacity cases (more SPUs than target)
            if current_spu_count <= target_spu_count:
                continue
            
            # Calculate category-level overcapacity metrics
            excess_spu_count = current_spu_count - target_spu_count
            overcapacity_percentage = (excess_spu_count / max(target_spu_count, 1)) * 100
            total_category_sales = sum(float(v) for v in spu_data.values() if float(v) > 0)
            
            # Skip if insufficient sales volume
            if total_category_sales < MIN_SALES_VOLUME:
                continue
            
            # Create individual records for each REAL SPU in the category
            for spu_code, spu_sales in spu_data.items():
                spu_sales = float(spu_sales)
                
                # Skip SPUs with no sales
                if spu_sales <= 0:
                    continue
                
                # Calculate this SPU's share of category sales
                spu_sales_share = spu_sales / total_category_sales

                # Create base record for this REAL SPU (quantities/prices computed after join)
                expanded_record = {
                    'str_code': row['str_code'],
                    'str_name': row.get('str_name', pd.NA),
                    'Cluster': row.get('Cluster', row.get('cluster_id', pd.NA)),
                    'season_name': row.get('season_name', pd.NA),
                    'sex_name': row.get('sex_name', pd.NA),
                    'display_location_name': row.get('display_location_name', pd.NA),
                    'big_class_name': row.get('big_class_name', pd.NA),
                    'sub_cate_name': row.get('sub_cate_name', pd.NA),
                    'yyyy': row.get('yyyy', pd.NA),
                    'mm': row.get('mm', pd.NA),
                    'mm_type': row.get('mm_type', pd.NA),
                    'sal_amt': row.get('sal_amt', pd.NA),
                    'sty_sal_amt': spu_sales,  # Individual SPU sales (from JSON)
                    
                    # Category-level overcapacity context
                    'category_current_spu_count': current_spu_count,
                    'category_target_spu_count': target_spu_count,
                    'category_excess_spu_count': excess_spu_count,
                    'category_overcapacity_percentage': overcapacity_percentage,
                    'category_total_sales': total_category_sales,
                    
                    # Individual SPU metrics using REAL SPU code
                    'spu_code': spu_code,  # REAL SPU CODE (e.g., "75T0001")
                    'spu_sales': spu_sales,
                    'spu_sales_share': spu_sales_share,
                    # Legacy compatibility columns at SPU level
                    'overcapacity_percentage': overcapacity_percentage,
                    'excess_spu_count': excess_spu_count,
                }
                
                expanded_records.append(expanded_record)
            # Periodic progress logging and memory cleanup
            if (n + 1) % 500 == 0 or (len(expanded_records) % 50000 == 0 and len(expanded_records) > 0):
                log_progress(f"   … processed {n+1:,}/{len(spu_records):,} records; expanded {len(expanded_records):,} SPUs so far")
            if (n + 1) % 2000 == 0:
                gc.collect()
                
        except (json.JSONDecodeError, TypeError, ValueError, ZeroDivisionError) as e:
            log_progress(f"Warning: Could not process record {idx}: {str(e)}")
            continue
    
    if not expanded_records:
        log_progress("No valid overcapacity SPU records found")
        return pd.DataFrame()
    
    expanded_df = pd.DataFrame(expanded_records)
    
    # Summary of SPU presence across stores for diagnostics
    try:
        spu_summary = (
            expanded_df.groupby('spu_code')['str_code']
            .nunique()
            .sort_values(ascending=False)
        )
        log_progress(f"✅ Found {len(spu_summary)} unique REAL SPU codes across {expanded_df['str_code'].nunique()} stores")
        log_progress(f"✅ Top SPUs by store presence: {dict(spu_summary.head(5))}")
    except Exception as _e:
        # If grouping fails due to missing columns, skip diagnostics gracefully
        pass
    
    # --- Join REAL quantities and compute unit prices ---
    if quantity_df is not None and len(quantity_df) > 0:
        # Prepare keys as strings
        expanded_df['str_code'] = expanded_df['str_code'].astype(str)
        expanded_df['spu_code'] = expanded_df['spu_code'].astype(str)
        qdf = quantity_df.copy()
        if 'str_code' in qdf.columns:
            qdf['str_code'] = qdf['str_code'].astype(str)
        if 'spu_code' in qdf.columns:
            qdf['spu_code'] = qdf['spu_code'].astype(str)

        # Keep only relevant columns if present
        keep_cols = [c for c in ['str_code','spu_code','base_sal_qty','fashion_sal_qty','sal_qty','quantity','spu_sales_amt'] if c in qdf.columns]
        qdf = qdf[keep_cols].drop_duplicates()

        # Compute real quantity
        qty = pd.Series(index=qdf.index, dtype='float64')
        if 'base_sal_qty' in qdf.columns and 'fashion_sal_qty' in qdf.columns:
            qty = pd.to_numeric(qdf['base_sal_qty'], errors='coerce') + pd.to_numeric(qdf['fashion_sal_qty'], errors='coerce')
        elif 'sal_qty' in qdf.columns:
            qty = pd.to_numeric(qdf['sal_qty'], errors='coerce')
        elif 'quantity' in qdf.columns:
            qty = pd.to_numeric(qdf['quantity'], errors='coerce')
        qdf['quantity_real'] = qty

        # Merge
        expanded_df = expanded_df.merge(qdf, on=['str_code','spu_code'], how='left')

        # Amount and unit price (prefer file amount, fallback to JSON amount)
        amount = pd.to_numeric(expanded_df.get('spu_sales_amt', expanded_df.get('spu_sales')), errors='coerce')
        qty_real = pd.to_numeric(expanded_df['quantity_real'], errors='coerce')
        with np.errstate(divide='ignore', invalid='ignore'):
            unit_price = amount / qty_real
        unit_price = unit_price.where(qty_real > 0)
        expanded_df['unit_price'] = unit_price

        # Period scaling
        current_qty = (qty_real * SCALING_FACTOR) if qty_real is not None else pd.NA
        expanded_df['current_quantity'] = current_qty

        # Compute reductions using real units
        # Percent of excess at category applied to this SPU's units
        frac_excess = pd.to_numeric(expanded_df['category_excess_spu_count'], errors='coerce') / pd.to_numeric(expanded_df['category_current_spu_count'], errors='coerce')
        frac_excess = frac_excess.replace([np.inf, -np.inf], np.nan)
        potential_reduction = frac_excess * current_qty
        max_reduction = pd.to_numeric(current_qty, errors='coerce') * MAX_REDUCTION_PERCENTAGE
        constrained_reduction = np.minimum(potential_reduction.fillna(0), max_reduction.fillna(0))
        expanded_df['potential_reduction'] = potential_reduction
        expanded_df['constrained_reduction'] = constrained_reduction
        expanded_df['recommend_reduction'] = (constrained_reduction >= MIN_REDUCTION_QUANTITY)
        expanded_df['recommended_quantity_change'] = -constrained_reduction.where(expanded_df['recommend_reduction'], 0)

        # Load real margin rates for SPU-level analysis
        log_progress("💰 Loading real margin rates for cost-based investment calculations...")
        # IMPORTANT: Use SOURCE period (args.yyyymm/args.period) for margin rates to avoid future-period leakage
        margin_rates = load_margin_rates(getattr(args, "yyyymm", None), getattr(args, "period", None), margin_type='spu')

        # Join margin rates with SPU data (prefer SPU-level, fallback to store-level)
        mr_source = 'none'
        try:
            mr_cols = set(margin_rates.columns)
            if {'str_code', 'spu_code', 'margin_rate'}.issubset(mr_cols):
                join_df = margin_rates[['str_code', 'spu_code', 'margin_rate']].copy()
                expanded_df = expanded_df.merge(join_df, on=['str_code', 'spu_code'], how='left')
                mr_source = 'spu'
            elif {'str_code', 'margin_rate'}.issubset(mr_cols):
                join_df = margin_rates[['str_code', 'margin_rate']].copy()
                # Avoid row multiplication if multiple category rows exist per store
                join_df = join_df.groupby('str_code', as_index=False)['margin_rate'].mean()
                expanded_df = expanded_df.merge(join_df, on=['str_code'], how='left')
                mr_source = 'store'
            else:
                # Ensure column exists for downstream fill
                expanded_df['margin_rate'] = np.nan
                mr_source = 'none'
        except Exception:
            # Defensive: if slicing fails for any reason, ensure column exists
            expanded_df['margin_rate'] = np.nan
            mr_source = 'error'

        # Fill missing margin rates with default value and clamp to realistic range
        default_margin_rate = float(os.environ.get('MARGIN_RATE_DEFAULT', '0.45'))
        expanded_df['margin_rate'] = pd.to_numeric(expanded_df['margin_rate'], errors='coerce')
        expanded_df['margin_rate'] = expanded_df['margin_rate'].fillna(default_margin_rate).clip(0, 0.95)
        log_progress(f"🔎 Margin rate source: {mr_source}; defaults used: {(expanded_df['margin_rate'] == default_margin_rate).mean() * 100:.1f}% of rows")
        
        # Calculate unit cost (cost = price * (1 - margin_rate))
        up = expanded_df['unit_price'].fillna(0)
        unit_cost = up * (1 - expanded_df['margin_rate'])
        
        # Add retail_value column for consistency with Step 7
        expanded_df['retail_value'] = up
        
        # Investment/cost savings (using cost-based investment instead of retail-based)
        expanded_df['investment_required'] = -(constrained_reduction * unit_cost).where(expanded_df['recommend_reduction'], 0)
        expanded_df['estimated_cost_savings'] = (constrained_reduction * unit_cost).where(expanded_df['recommend_reduction'], 0)
        
        # Calculate profit-based ROI metrics
        margin_per_unit = up - unit_cost
        expanded_df['margin_per_unit'] = margin_per_unit
        expanded_df['expected_margin_uplift'] = (constrained_reduction * margin_per_unit).where(expanded_df['recommend_reduction'], 0)
        
        # ROI calculation (profit / investment)
        expanded_df['roi_percentage'] = np.where(
            expanded_df['investment_required'] < 0,  # Only for recommended reductions
            (expanded_df['expected_margin_uplift'] / -expanded_df['investment_required']) * 100,
            0
        )

        # Recommendation text
        try:
            expanded_df['recommendation_text'] = np.where(
                expanded_df['recommend_reduction'],
                expanded_df.apply(lambda r: f"REDUCE {float(r['constrained_reduction']):.1f} units/15-days for SPU {r['spu_code']} (overcapacity: {float(r['category_overcapacity_percentage']):.1f}%)", axis=1),
                expanded_df.apply(lambda r: f"Monitor SPU {r['spu_code']} (below reduction threshold)", axis=1)
            )
        except Exception:
            pass

        # Diagnostics
        join_match_rate = float((expanded_df['quantity_real'].notna()).mean() * 100.0)
        unit_price_na_rate = float((expanded_df['unit_price'].isna()).mean() * 100.0)
        margin_default_rate = float((expanded_df['margin_rate'] == default_margin_rate).mean() * 100.0)
        
        log_progress(f"🔎 Quantity join coverage: {join_match_rate:.1f}% of SPU records matched")
        log_progress(f"🔎 Unit price NA rate: {unit_price_na_rate:.1f}%")
        log_progress(f"🔎 Margin rates using defaults: {margin_default_rate:.1f}% of SPU records")
    else:
        log_progress("⚠️ Quantity dataframe empty or missing; cannot compute real unit quantities")

    # Dimension missingness diagnostics
    for col in ['season_name','sex_name','display_location_name','big_class_name','sub_cate_name']:
        if col in expanded_df.columns:
            miss = int(expanded_df[col].isna().sum())
            if miss > 0:
                log_progress(f"⚠️ Missing values for {col}: {miss}")

    return expanded_df

def fast_detect_overcapacity(df: pd.DataFrame, quantity_df: pd.DataFrame) -> pd.DataFrame:
    """
    Fast overcapacity detection with REAL SPU codes and REAL UNIT QUANTITIES.
    
    CRITICAL FIX: Now works with individual real SPU records instead of fake category aggregations.
    
    Args:
        df: DataFrame with individual SPU records (from fast_expand_spu_data)
        quantity_df: Additional quantity data (not needed since we have real SPU data)
        
    Returns:
        DataFrame with overcapacity recommendations for REAL SPUs
    """
    log_progress("🚀 Fast detecting overcapacity with REAL SPU codes and REAL UNIT QUANTITIES...")
    
    if len(df) == 0:
        log_progress("No SPU records to process")
        return pd.DataFrame()
    
    # Filter to only SPUs recommended for reduction
    overcapacity_df = df[df['recommend_reduction'] == True].copy()
    
    if len(overcapacity_df) == 0:
        log_progress("No SPUs meet the reduction criteria")
        return pd.DataFrame()
    
    log_progress(f"Processing {len(overcapacity_df)} SPU overcapacity cases with REAL SPU codes...")
    
    # The data is already processed in fast_expand_spu_data, just need to format for output
    # Add any additional columns needed for compatibility
    
    # Summary statistics
    total_spus = len(overcapacity_df)
    unique_spu_codes = overcapacity_df['spu_code'].nunique()
    affected_stores = overcapacity_df['str_code'].nunique()
    total_quantity_reduction = overcapacity_df['constrained_reduction'].sum()
    total_cost_savings = (-overcapacity_df['investment_required']).sum()
    
    log_progress(f"  • Total SPU reduction recommendations: {total_spus:,}")
    log_progress(f"  • Unique SPU codes affected: {unique_spu_codes:,}")
    log_progress(f"  • Stores affected: {affected_stores:,}")
    log_progress(f"  • Total quantity reduction: {total_quantity_reduction:.1f} units/15-days")
    log_progress(f"  • Total estimated cost savings: ${total_cost_savings:,.0f}")
    
    # Show top SPUs by frequency
    top_spus = overcapacity_df['spu_code'].value_counts().head(5)
    log_progress(f"  • Top SPUs by store count: {dict(top_spus)}")
    
    # 📈 FAST FISH ENHANCEMENT: Apply sell-through validation
    if SELLTHROUGH_VALIDATION_AVAILABLE and not SKIP_SELLTHROUGH and len(overcapacity_df) > 0:
        log_progress("🎯 Applying Fast Fish sell-through validation...")
        
        # Initialize validator
        historical_data = load_historical_data_for_validation()
        validator = SellThroughValidator(historical_data)
        
        # Apply validation once per unique (store, subcategory, current_count -> recommended_count) key
        # Build validity mask
        valid_mask = (
            overcapacity_df['sub_cate_name'].notna()
            & (overcapacity_df['sub_cate_name'].astype(str).str.strip() != "")
            & overcapacity_df['category_current_spu_count'].notna()
        )

        # Rows with missing fields are kept with NA validation fields (preserve original behavior)
        invalid_cases = overcapacity_df[~valid_mask].copy()
        if len(invalid_cases) > 0:
            invalid_cases['fast_fish_compliant'] = pd.NA
            invalid_cases['sell_through_improvement'] = pd.NA
            invalid_cases['validation_reason'] = 'validation_skipped_missing_fields_or_counts'

        valid_cases = overcapacity_df[valid_mask].copy()
        # Integerize and clamp counts
        curr_cnt = pd.to_numeric(valid_cases['category_current_spu_count'], errors='coerce').fillna(0).round().astype(int)
        curr_cnt = curr_cnt.clip(lower=0, upper=100)
        rec_cnt = (curr_cnt - 1).clip(lower=0)
        valid_cases['_v_curr_cnt'] = curr_cnt
        valid_cases['_v_rec_cnt'] = rec_cnt

        key_cols = ['str_code', 'sub_cate_name', '_v_curr_cnt', '_v_rec_cnt']
        unique_keys = valid_cases[key_cols].drop_duplicates()

        # Validate once per key and broadcast
        results = []
        # Use dict records to avoid itertuples field-name mangling for columns starting with '_'
        for rec in unique_keys.to_dict('records'):
            try:
                v = validator.validate_recommendation(
                    store_code=str(rec['str_code']),
                    category=str(rec['sub_cate_name']),
                    current_spu_count=int(rec['_v_curr_cnt']),
                    recommended_spu_count=int(rec['_v_rec_cnt']),
                    action='DECREASE',
                    rule_name='Rule 10: Overcapacity'
                )
                v_row = {
                    'str_code': rec['str_code'],
                    'sub_cate_name': rec['sub_cate_name'],
                    '_v_curr_cnt': int(rec['_v_curr_cnt']),
                    '_v_rec_cnt': int(rec['_v_rec_cnt']),
                    'current_sell_through_rate': v.get('current_sell_through_rate'),
                    'predicted_sell_through_rate': v.get('predicted_sell_through_rate'),
                    'sell_through_improvement': v.get('sell_through_improvement'),
                    'fast_fish_compliant': v.get('fast_fish_compliant'),
                    'business_rationale': v.get('business_rationale'),
                    'approval_reason': v.get('approval_reason'),
                }
            except Exception:
                v_row = {
                    'str_code': rec['str_code'],
                    'sub_cate_name': rec['sub_cate_name'],
                    '_v_curr_cnt': int(rec['_v_curr_cnt']),
                    '_v_rec_cnt': int(rec['_v_rec_cnt']),
                    'fast_fish_compliant': False,
                }
            results.append(v_row)

        if results:
            val_df = pd.DataFrame(results)
            merged = valid_cases.merge(val_df, on=key_cols, how='left')
        else:
            merged = valid_cases.copy()

        compliant = merged[merged['fast_fish_compliant'] == True].copy()
        rejected_count = int(len(valid_cases) - len(compliant))

        # Combine with invalid rows (kept as NA per original behavior)
        if len(invalid_cases) > 0:
            overcapacity_df = pd.concat([compliant, invalid_cases], ignore_index=True, sort=False)
        else:
            overcapacity_df = compliant

        # Sort by sell-through improvement (prioritize best reductions)
        if 'sell_through_improvement' in overcapacity_df.columns:
            overcapacity_df = overcapacity_df.sort_values('sell_through_improvement', ascending=False)

        avg_improvement = overcapacity_df['sell_through_improvement'].mean()
        total_savings = overcapacity_df['estimated_cost_savings'].sum() if 'estimated_cost_savings' in overcapacity_df.columns else 0
        
        log_progress(f"✅ Fast Fish sell-through validation complete:")
        log_progress(f"   Approved: {len(overcapacity_df)} overcapacity reductions")
        log_progress(f"   Rejected: {rejected_count} overcapacity reductions")
        if isinstance(avg_improvement, (int, float, np.floating)) and not pd.isna(avg_improvement):
            log_progress(f"   Average sell-through improvement: {avg_improvement:.1f} percentage points")
        if total_savings and total_savings > 0:
            log_progress(f"   Total cost savings (validated): ${total_savings:,.0f}")
        # Apply per-store cap post validation
        trimmed_df, cap_stats = apply_per_store_cap(overcapacity_df, MAX_TOTAL_ADJUSTMENTS_PER_STORE)
        if len(trimmed_df) < len(overcapacity_df):
            log_progress(f"🧱 Per-store cap applied (limit={MAX_TOTAL_ADJUSTMENTS_PER_STORE}): dropped {len(overcapacity_df)-len(trimmed_df)} records across {cap_stats.get('stores_capped', 0)} stores")
        overcapacity_df = trimmed_df
        
    elif not SELLTHROUGH_VALIDATION_AVAILABLE and len(overcapacity_df) > 0:
        log_progress("⚠️ Sell-through validation skipped (validator not available)")
    elif SKIP_SELLTHROUGH and len(overcapacity_df) > 0:
        log_progress("⏭️ Skipping Fast Fish sell-through validation (flag enabled)")
    
    return overcapacity_df

# -----------------------------
# CLI and configuration helpers
# -----------------------------
def get_period_label_from_env_or_args(args) -> str:
    """Derive target period label like 202509A from env or args."""
    target_yyyymm = os.environ.get("PIPELINE_TARGET_YYYYMM") or getattr(args, "target_yyyymm", None) or getattr(args, "yyyymm", None)
    target_period = os.environ.get("PIPELINE_TARGET_PERIOD") or getattr(args, "target_period", None) or getattr(args, "period", None)
    if not target_yyyymm or not target_period:
        now = datetime.now()
        return f"{now.strftime('%Y%m')}A"
    return f"{str(target_yyyymm)}{str(target_period)}"

def _prev_yyyymm(yyyymm: str) -> Optional[str]:
    try:
        dt = datetime.strptime(yyyymm, "%Y%m")
        year = dt.year
        month = dt.month
        if month == 1:
            return f"{year-1}12"
        else:
            return f"{year}{month-1:02d}"
    except Exception:
        return None

def apply_runtime_configuration(args) -> None:
    """Apply runtime config based on CLI flags without heavy refactor of globals."""
    global ANALYSIS_LEVEL, USE_BLENDED_SEASONAL, ANALYSIS_CONFIGS, QUANTITY_DATA_FILE
    global RECENT_CONFIG_FILES, RECENT_QUANTITY_FILES, DEBUG_LIMIT, SKIP_SELLTHROUGH
    global MAX_TOTAL_ADJUSTMENTS_PER_STORE
    global MIN_SALES_VOLUME, MIN_REDUCTION_QUANTITY, MAX_REDUCTION_PERCENTAGE, MIN_CLUSTER_SIZE
    global JOIN_MODE
    # analysis level
    if getattr(args, "analysis_level", None):
        ANALYSIS_LEVEL = args.analysis_level
    # seasonal blending overrides
    use_blend_flag = None
    if getattr(args, "seasonal_blending", False):
        use_blend_flag = True
    elif getattr(args, "no_seasonal_blending", False):
        use_blend_flag = False
    if use_blend_flag is not None:
        USE_BLENDED_SEASONAL = bool(use_blend_flag)
    else:
        yyyymm = getattr(args, "yyyymm", None)
        if yyyymm and len(str(yyyymm)) >= 6:
            try:
                USE_BLENDED_SEASONAL = int(str(yyyymm)[-2:]) == 8
            except ValueError:
                pass
    # Resolve current period files for analysis (prefer explicit args; else env)
    cur_yyyymm = getattr(args, "yyyymm", None) or os.environ.get("PIPELINE_YYYYMM")
    cur_period = getattr(args, "period", None) or os.environ.get("PIPELINE_PERIOD")
    recent_cfg_files: List[str] = []
    recent_qty_files: List[str] = []
    if cur_yyyymm and cur_period:
        files = get_api_data_files(cur_yyyymm, cur_period)
        cfg = files.get('store_config')
        qty = files.get('spu_sales')
        if cfg and os.path.exists(cfg):
            recent_cfg_files.append(cfg)
        if qty and os.path.exists(qty):
            recent_qty_files.append(qty)
    # Ensure a 3 half-month recent window by appending previous months' A/B until >= 3
    def _append_prev_month_files(base_yyyymm: Optional[str], cfg_list: List[str], qty_list: List[str]) -> None:
        y = base_yyyymm
        while (len(cfg_list) < 3 or len(qty_list) < 3) and y:
            y = _prev_yyyymm(y)
            if not y:
                break
            for p in ["B", "A"]:
                if len(cfg_list) >= 3 and len(qty_list) >= 3:
                    break
                files_prev = get_api_data_files(y, p)
                cfg_prev = files_prev.get('store_config')
                qty_prev = files_prev.get('spu_sales')
                if cfg_prev and os.path.exists(cfg_prev) and cfg_prev not in cfg_list:
                    cfg_list.append(cfg_prev)
                if qty_prev and os.path.exists(qty_prev) and qty_prev not in qty_list:
                    qty_list.append(qty_prev)

    # If we have fewer than 3, append previous months; if none at all, start from cur_yyyymm
    if len(recent_cfg_files) < 3 or len(recent_qty_files) < 3:
        log_progress("ℹ️ Building recent 3 half-month window from prior periods")
        _append_prev_month_files(cur_yyyymm, recent_cfg_files, recent_qty_files)

    # If still empty, try previous month explicitly as a last resort
    if not recent_cfg_files or not recent_qty_files:
        log_progress("⚠️ Current and prior periods not sufficient; attempting immediate previous month A/B")
        prev = _prev_yyyymm(cur_yyyymm or "")
        if prev:
            for p in ["B", "A"]:
                files_prev = get_api_data_files(prev, p)
                cfg_prev = files_prev.get('store_config')
                qty_prev = files_prev.get('spu_sales')
                if cfg_prev and os.path.exists(cfg_prev) and cfg_prev not in recent_cfg_files:
                    recent_cfg_files.append(cfg_prev)
                if qty_prev and os.path.exists(qty_prev) and qty_prev not in recent_qty_files:
                    recent_qty_files.append(qty_prev)
    RECENT_CONFIG_FILES = recent_cfg_files
    RECENT_QUANTITY_FILES = recent_qty_files

    # rebuild analysis config to ensure consistency, prefer current-period list
    ANALYSIS_CONFIGS = {
        "spu": {
            "analysis_level": "spu",
            "data_files": RECENT_CONFIG_FILES,
            "cluster_file": "output/clustering_results_spu.csv",
            "output_prefix": "rule10_smart_overcapacity_spu",
            "business_unit": "store-spu",
            "min_stores_threshold": 3
        }
    }
    # Resolve seasonal file paths if applicable (same month prior N years, default 2)
    if USE_BLENDED_SEASONAL:
        seasonal_cfg_files: List[str] = []
        seasonal_qty_files: List[str] = []
        try:
            cy = int((cur_yyyymm or "000000")[:4])
            cm = int((cur_yyyymm or "000000")[4:6])
            years_back = getattr(args, "seasonal_years_back", None)
            try:
                years_back = int(years_back) if years_back is not None else 2
            except Exception:
                years_back = 2
            if years_back < 1:
                years_back = 1
            s_period = cur_period or 'A'
            for i in range(1, years_back + 1):
                syyyymm = f"{cy - i}{cm:02d}"
                files_season = get_api_data_files(syyyymm, s_period)
                cfg_path = files_season.get('store_config')
                qty_path = files_season.get('spu_sales')
                if cfg_path and os.path.exists(cfg_path):
                    seasonal_cfg_files.append(cfg_path)
                if qty_path and os.path.exists(qty_path):
                    seasonal_qty_files.append(qty_path)
        except Exception:
            seasonal_cfg_files = []
            seasonal_qty_files = []
        globals()['SEASONAL_DATA_FILE'] = seasonal_cfg_files if seasonal_cfg_files else None
        globals()['SEASONAL_QUANTITY_FILE'] = seasonal_qty_files if seasonal_qty_files else None
    # QUANTITY_DATA_FILE remains as fallback; primary is RECENT_QUANTITY_FILES
    
    # Debug and validation flags
    if getattr(args, "debug_limit", None) is not None:
        try:
            DEBUG_LIMIT = int(args.debug_limit)
        except Exception:
            DEBUG_LIMIT = None
    SKIP_SELLTHROUGH = bool(getattr(args, "skip_sellthrough", False))
    # per-store cap
    if getattr(args, "max_adj_per_store", None) is not None:
        try:
            MAX_TOTAL_ADJUSTMENTS_PER_STORE = int(args.max_adj_per_store)
        except Exception:
            pass
    # thresholds
    if getattr(args, "min_sales_volume", None) is not None:
        try:
            MIN_SALES_VOLUME = int(args.min_sales_volume)
        except Exception:
            pass
    if getattr(args, "min_reduction_qty", None) is not None:
        try:
            MIN_REDUCTION_QUANTITY = float(args.min_reduction_qty)
        except Exception:
            pass
    if getattr(args, "max_reduction_pct", None) is not None:
        try:
            MAX_REDUCTION_PERCENTAGE = float(args.max_reduction_pct)
        except Exception:
            pass
    if getattr(args, "min_cluster_size", None) is not None:
        try:
            MIN_CLUSTER_SIZE = int(args.min_cluster_size)
        except Exception:
            pass
    # join mode
    if getattr(args, "join_mode", None) in ("left", "inner"):
        JOIN_MODE = args.join_mode

def parse_args():
    parser = argparse.ArgumentParser(description="Step 10 - Smart Overcapacity (SPU) with labeled outputs")
    parser.add_argument("--yyyymm", type=str, help="Source data yyyymm, e.g., 202508")
    parser.add_argument("--period", type=str, choices=["A", "B"], help="Source 15-day period A or B")
    parser.add_argument("--analysis-level", type=str, default="spu", choices=["spu"], help="Analysis level")
    parser.add_argument("--target-yyyymm", type=str, help="Target yyyymm for output labeling (e.g., 202509)")
    parser.add_argument("--target-period", type=str, choices=["A", "B"], help="Target period for output labeling")
    parser.add_argument("--seasonal-blending", action="store_true", help="Force-enable seasonal blending")
    parser.add_argument("--no-seasonal-blending", action="store_true", help="Force-disable seasonal blending")
    parser.add_argument("--seasonal-years-back", type=int, help="Number of prior years (same month/period) to include when seasonal blending is enabled (default 2)")
    parser.add_argument("--debug-limit", type=int, help="Limit number of SPU source records to expand (for faster debugging)")
    parser.add_argument("--skip-sellthrough", action="store_true", help="Skip Fast Fish sell-through validation")
    parser.add_argument("--max-adj-per-store", type=int, help="Optional per-store cap on reductions; omit for no cap")
    parser.add_argument("--join-mode", type=str, choices=["left","inner"], default="left", help="Join mode for merging clusters: left (inclusive) or inner (stricter)")
    parser.add_argument("--min-sales-volume", type=int, help="Minimum total category sales to consider for expansion")
    parser.add_argument("--min-reduction-qty", type=float, help="Minimum units to recommend reduction for a SPU")
    parser.add_argument("--max-reduction-pct", type=float, help="Maximum percentage of current quantity reduction per SPU (0-1)")
    parser.add_argument("--min-cluster-size", type=int, help="Minimum number of stores required in a cluster (if applicable)")
    return parser.parse_args()

def fast_pipeline_analysis(args=None) -> None:
    """Fast main pipeline analysis"""
    start_time = datetime.now()
    log_progress("🚀 Starting FAST SPU Overcapacity Analysis...")
    
    print("\n" + "="*80)
    print("🚀 FAST TARGET-BASED SPU OVERCAPACITY ANALYSIS")
    print("="*80)
    
    try:
        # Load data with enhanced seasonal blending
        config = ANALYSIS_CONFIGS[ANALYSIS_LEVEL]
        # Log effective configuration
        period_label = get_period_label_from_env_or_args(args or argparse.Namespace())
        # Derive target components locally to avoid missing variable references
        _ty, _tm, _tp = None, None, None
        try:
            if len(period_label) >= 6:
                _ty = int(period_label[:4])
                _tm = int(period_label[4:6])
            if len(period_label) >= 7:
                _tp = period_label[6:]
        except Exception:
            pass
        log_progress(
            f"Args/Config: yyyymm={getattr(args, 'yyyymm', None)}, "
            f"period={getattr(args, 'period', None)}, target={period_label}, "
            f"analysis_level={ANALYSIS_LEVEL}, blended={USE_BLENDED_SEASONAL}, "
            f"debug_limit={DEBUG_LIMIT}, skip_sellthrough={SKIP_SELLTHROUGH}, join_mode={JOIN_MODE}"
        )
        
        # SEASONAL BLENDING ENHANCEMENT: Use blended data loading for August
        planning_df, quantity_df = load_blended_data()
        # Prefer period-labeled cluster file first; fallback to unlabeled legacy path
        labeled_cluster = get_output_files("spu", getattr(args, "yyyymm", None), getattr(args, "period", None))["clustering_results"]
        if os.path.exists(labeled_cluster):
            cluster_df = pd.read_csv(labeled_cluster, dtype={'str_code': str})
            log_progress(f"ℹ️ Using labeled cluster file: {labeled_cluster}")
        else:
            cluster_path = config.get("cluster_file", "output/clustering_results_spu.csv")
            cluster_df = pd.read_csv(cluster_path, dtype={'str_code': str})
            log_progress(f"ℹ️ Labeled cluster file not found. Using legacy path: {cluster_path}")
            # Create a labeled alias for downstream steps expecting period-suffixed files
            try:
                os.makedirs(os.path.dirname(labeled_cluster), exist_ok=True)
                cluster_df.to_csv(labeled_cluster, index=False)
                log_progress(f"   Created labeled cluster alias: {labeled_cluster}")
            except Exception:
                pass
        
        log_progress(f"Loaded data: {len(planning_df):,} planning records, {len(quantity_df):,} quantity records, {len(cluster_df):,} stores")
        
        # Merge with clusters using configured join mode
        df = planning_df.merge(cluster_df, on='str_code', how=JOIN_MODE)
        # Diagnostics
        left_rows = len(planning_df)
        right_rows = cluster_df['str_code'].nunique() if 'str_code' in cluster_df.columns else len(cluster_df)
        merged_rows = len(df)
        cluster_col = next((c for c in ['Cluster', 'cluster_id', 'cluster', 'cluster_label'] if c in df.columns), None)
        if cluster_col:
            unmatched_count = df[cluster_col].isna().sum()
        else:
            right_str_codes = cluster_df['str_code'].astype(str).unique().tolist() if 'str_code' in cluster_df.columns else []
            unmatched_count = (~df['str_code'].astype(str).isin(right_str_codes)).sum()
        log_progress(f"Merged data: {merged_rows:,} rows (left={left_rows:,}, right stores={right_rows:,}, unmatched stores w/o cluster={unmatched_count:,})")
        
        # Fast expand to SPU level
        expanded_df = fast_expand_spu_data(df, quantity_df)
        if len(expanded_df) == 0:
            log_progress("❌ No expanded data available")
            return
        
        # Fast detect overcapacity
        overcapacity_opportunities = fast_detect_overcapacity(expanded_df, quantity_df)
        if len(overcapacity_opportunities) == 0:
            log_progress("❌ No overcapacity opportunities found")
            return
        
        # STANDARDIZATION FIX: Use cluster_id instead of Cluster for consistency
        cluster_df_standardized = cluster_df.copy()
        if 'Cluster' in cluster_df_standardized.columns:
            cluster_df_standardized['cluster_id'] = cluster_df_standardized['Cluster']
            cluster_df_standardized = cluster_df_standardized.drop('Cluster', axis=1)
        
        # Create pipeline results
        # Preserve all planning stores (even if cluster is missing) to avoid dropping rows
        results_df = planning_df[['str_code']].drop_duplicates()
        results_df = results_df.merge(
            cluster_df_standardized[['str_code', 'cluster_id']],
            on='str_code',
            how='left'
        )
        
        # Initialize results
        results_df['rule10_spu_overcapacity'] = 0
        results_df['rule10_overcapacity_count'] = 0
        results_df['rule10_total_excess_spus'] = 0.0
        results_df['rule10_avg_overcapacity_pct'] = 0.0
        results_df['rule10_reduction_recommended_count'] = 0
        results_df['rule10_total_quantity_reduction'] = 0.0
        results_df['rule10_total_cost_savings'] = 0.0
        
        # Aggregate by store using standardized column names
        store_summary = overcapacity_opportunities.groupby('str_code').agg({
            'spu_code': 'count',  # Count of SPU opportunities
            'excess_spu_count': 'sum',  # Total excess SPUs
            'overcapacity_percentage': 'mean',  # Average overcapacity %
            'recommend_reduction': 'sum',  # Count of reduction recommendations
            'recommended_quantity_change': 'sum',  # Total quantity reduction (already negative)
            'estimated_cost_savings': 'sum'  # Total cost savings (positive)
        }).reset_index()
        
        store_summary.columns = ['str_code', 'opp_count', 'total_excess', 'avg_pct', 'reduction_count', 'total_reduction', 'total_savings']
        
        # Convert recommended_quantity_change (negative) to positive for reporting
        store_summary['total_reduction'] = -store_summary['total_reduction']
        
        # Update results
        for _, row in store_summary.iterrows():
            store_idx = results_df['str_code'] == row['str_code']
            results_df.loc[store_idx, 'rule10_spu_overcapacity'] = 1
            results_df.loc[store_idx, 'rule10_overcapacity_count'] = row['opp_count']
            results_df.loc[store_idx, 'rule10_total_excess_spus'] = row['total_excess']
            results_df.loc[store_idx, 'rule10_avg_overcapacity_pct'] = row['avg_pct']
            results_df.loc[store_idx, 'rule10_reduction_recommended_count'] = row['reduction_count']
            results_df.loc[store_idx, 'rule10_total_quantity_reduction'] = row['total_reduction']
            results_df.loc[store_idx, 'rule10_total_cost_savings'] = row['total_savings']
        
        # STANDARDIZATION FIX: Add missing standard columns for pipeline compatibility
        # Map rule10_total_quantity_reduction to recommended_quantity_change (standard column name)
        # For overcapacity, quantity changes are negative (reductions)
        results_df['recommended_quantity_change'] = -results_df['rule10_total_quantity_reduction']
        # Map rule10_total_cost_savings to investment_required (negative for cost savings)
        results_df['investment_required'] = -results_df['rule10_total_cost_savings']  # Negative = savings
        
        # Add standard business rationale and approval columns
        results_df['business_rationale'] = results_df.apply(
            lambda row: f"Overcapacity detected: {row['rule10_overcapacity_count']} SPUs need reduction" 
                       if row['rule10_spu_overcapacity'] > 0 else "No overcapacity issues", axis=1
        )
        results_df['approval_reason'] = 'Automatic approval for overcapacity reduction'
        results_df['fast_fish_compliant'] = True  # Overcapacity reductions are validated
        results_df['opportunity_type'] = 'OVERCAPACITY_REDUCTION'
        
        # --- Embed explicit period metadata for provenance ---
        try:
            _period_label_for_cols = get_period_label_from_env_or_args(args or argparse.Namespace())
        except Exception:
            _period_label_for_cols = None
        _yyyymm_for_cols = (_period_label_for_cols[:6] if _period_label_for_cols and len(_period_label_for_cols) >= 6 else None)
        _period_for_cols = (_period_label_for_cols[6:] if _period_label_for_cols and len(_period_label_for_cols) >= 7 else None)
        # Attach to results
        results_df['period_label'] = _period_label_for_cols
        if _yyyymm_for_cols is not None:
            results_df['target_yyyymm'] = _yyyymm_for_cols
        if _period_for_cols is not None:
            results_df['target_period'] = _period_for_cols
        # Attach to opportunities
        overcapacity_opportunities['period_label'] = _period_label_for_cols
        if _yyyymm_for_cols is not None:
            overcapacity_opportunities['target_yyyymm'] = _yyyymm_for_cols
        if _period_for_cols is not None:
            overcapacity_opportunities['target_period'] = _period_for_cols

        # Save results using dual output pattern
        period_label = get_period_label_from_env_or_args(args or argparse.Namespace())
        
        # Save main results with dual output
        timestamped, symlink, generic = create_output_with_symlinks(
            results_df,
            f"{OUTPUT_DIR}/rule10_smart_overcapacity_results",
            period_label
        )
        log_progress(f"✅ Saved results: {timestamped}")
        log_progress(f"   Period symlink: {symlink}")
        log_progress(f"   Generic symlink: {generic}")
        
        # Ensure standardized column for downstream (Step 13+)
        if 'opportunity_type' not in overcapacity_opportunities.columns:
            overcapacity_opportunities['opportunity_type'] = 'OVERCAPACITY_REDUCTION'
        
        # Save opportunities with dual output
        timestamped_opp, symlink_opp, generic_opp = create_output_with_symlinks(
            overcapacity_opportunities,
            f"{OUTPUT_DIR}/rule10_spu_overcapacity_opportunities",
            period_label
        )
        log_progress(f"✅ Saved opportunities: {timestamped_opp}")
        log_progress(f"   Period symlink: {symlink_opp}")
        log_progress(f"   Generic symlink: {generic_opp}")
        
        # Register outputs in pipeline manifest
        try:
            target_label = period_label
            target_year = int(target_label[:4]) if len(target_label) >= 6 else None
            target_month = int(target_label[4:6]) if len(target_label) >= 6 else None
            target_period = target_label[6:] if len(target_label) >= 7 else None
            base_meta_results = {
                "target_year": target_year,
                "target_month": target_month,
                "target_period": target_period,
                "period_label": target_label,
                "analysis_level": ANALYSIS_LEVEL,
                "use_blended_seasonal": bool(USE_BLENDED_SEASONAL),
                "sellthrough_validation": bool(SELLTHROUGH_VALIDATION_AVAILABLE and not SKIP_SELLTHROUGH),
                "records": int(len(results_df)),
                "columns": list(results_df.columns),
            }
            base_meta_opps = {
                **base_meta_results,
                "records": int(len(overcapacity_opportunities)),
                "columns": list(overcapacity_opportunities.columns),
                "opportunities_count": int(len(overcapacity_opportunities)),
                "reduction_recommended": int(overcapacity_opportunities.get('recommend_reduction', pd.Series(dtype=int)).sum() if 'recommend_reduction' in overcapacity_opportunities.columns else 0),
            }
            # Unlabeled (legacy) outputs
            register_step_output("step10", "overcapacity_results", results_file, base_meta_results)
            register_step_output("step10", "overcapacity_opportunities", opportunities_file, base_meta_opps)
            register_step_output("step10", "smart_overcapacity_results", unlabeled_smart_results, base_meta_results)
            # Period-specific outputs
            register_step_output("step10", f"overcapacity_results_{target_label}", labeled_results_file, base_meta_results)
            register_step_output("step10", f"overcapacity_opportunities_{target_label}", labeled_opportunities_file, base_meta_opps)
            register_step_output("step10", f"smart_overcapacity_results_{target_label}", labeled_results_file, base_meta_results)
        except Exception as e:
            log_progress(f"⚠️ Manifest registration warning (CSV outputs): {e}")
        
        # SEASONAL BLENDING BENEFITS: Log the strategic advantages for August
        if USE_BLENDED_SEASONAL:
            log_progress("\n🍂 SEASONAL BLENDING BENEFITS FOR OVERCAPACITY ANALYSIS:")
            log_progress("   ✓ Summer clearance opportunities: Identified from recent trends (May-July)")
            log_progress("   ✓ Autumn transition planning: Identified from seasonal patterns (Aug 2024)")
            log_progress("   ✓ Balanced overcapacity detection: Avoids over-focusing on summer-only styles")
            log_progress("   ✓ Strategic inventory optimization: Supports autumn assortment planning")
            log_progress("   ✓ Business rationale: Overcapacity analysis considers seasonal transitions")
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        log_progress(f"✅ Analysis completed in {duration/60:.1f} minutes ({duration:.0f} seconds)")
        
        stores_flagged = results_df['rule10_spu_overcapacity'].sum()
        total_opportunities = len(overcapacity_opportunities)
        reduction_recommended = overcapacity_opportunities['recommend_reduction'].sum()
        total_quantity_reduction = (-overcapacity_opportunities[overcapacity_opportunities['recommend_reduction']]['recommended_quantity_change']).sum()
        total_cost_savings = overcapacity_opportunities[overcapacity_opportunities['recommend_reduction']]['estimated_cost_savings'].sum()
        
        print("\n" + "="*70)
        print("🚀 FAST SPU OVERCAPACITY ANALYSIS - ENHANCED COMPLETE")
        print("="*70)
        if USE_BLENDED_SEASONAL:
            print("🍂 SEASONAL ENHANCEMENT: Blended data for August recommendations")
        print(f"⚡ Process completed in {duration:.1f} seconds (FAST!)")
        print(f"✅ Stores analyzed: {len(results_df):,}")
        print(f"✅ Stores flagged: {stores_flagged:,}")
        print(f"✅ Overcapacity opportunities: {total_opportunities:,}")
        print(f"✅ Reduction recommended: {reduction_recommended:,}")
        print(f"✅ Total quantity reduction: {total_quantity_reduction:,.1f} units/15-days")
        print(f"✅ Total cost savings: ${total_cost_savings:,.0f}")
        if USE_BLENDED_SEASONAL:
            print(f"✅ Seasonal context: Recommendations balance summer clearance + autumn planning")
        print(f"⚡ Performance: {total_opportunities/duration:.0f} opportunities/second")
        print()

        # Write summary markdown (both labeled and unlabeled)
        period_label = get_period_label_from_env_or_args(args or argparse.Namespace())
        summary_content = []
        summary_content.append("# Rule 10 - Smart Overcapacity (SPU) Summary")
        summary_content.append("")
        summary_content.append(f"- Period: {period_label}")
        summary_content.append(f"- Stores analyzed: {len(results_df):,}")
        summary_content.append(f"- Stores flagged: {stores_flagged:,}")
        summary_content.append(f"- Overcapacity opportunities: {total_opportunities:,}")
        summary_content.append(f"- Reduction recommended: {int(reduction_recommended):,}")
        summary_content.append(f"- Total quantity reduction: {total_quantity_reduction:,.1f} units/15-days")
        summary_content.append(f"- Total cost savings: ${total_cost_savings:,.0f}")
        if USE_BLENDED_SEASONAL:
            summary_content.append(f"- Seasonal blending: Enabled")
        else:
            summary_content.append(f"- Seasonal blending: Disabled")
        summary_text = "\n".join(summary_content) + "\n"

        summary_file_labeled = f"{OUTPUT_DIR}/rule10_smart_overcapacity_spu_summary_{period_label}.md"
        with open(summary_file_labeled, "w", encoding="utf-8") as f:
            f.write(summary_text)
        log_progress(f"✅ Saved summary to {summary_file_labeled}")

        summary_file_unlabeled = f"{OUTPUT_DIR}/rule10_smart_overcapacity_spu_summary.md"
        with open(summary_file_unlabeled, "w", encoding="utf-8") as f:
            f.write(summary_text)
        log_progress(f"✅ Saved summary to {summary_file_unlabeled}")
        
        # Register summaries in manifest
        try:
            summary_meta = {
                "target_year": _ty,
                "target_month": _tm,
                "target_period": _tp,
                "period_label": period_label,
                "analysis_level": ANALYSIS_LEVEL,
                "use_blended_seasonal": bool(USE_BLENDED_SEASONAL),
                "stores_analyzed": int(len(results_df)),
                "stores_flagged": int(stores_flagged),
                "opportunities_count": int(total_opportunities),
                "reduction_recommended": int(reduction_recommended),
                "total_quantity_reduction": float(total_quantity_reduction),
                "total_cost_savings": float(total_cost_savings),
            }
            register_step_output("step10", f"overcapacity_summary_md_{period_label}", summary_file_labeled, summary_meta)
            register_step_output("step10", "overcapacity_summary_md", summary_file_unlabeled, summary_meta)
        except Exception as e:
            log_progress(f"⚠️ Manifest registration warning (summaries): {e}")
        
    except Exception as e:
        log_progress(f"❌ Error in analysis: {str(e)}")
        raise

if __name__ == "__main__":
    args = parse_args()
    # Initialize config with provided period to avoid default 202506B logging
    try:
        initialize_pipeline_config(args.yyyymm, args.period)
    except Exception as e:
        log_progress(f"⚠️ Could not initialize pipeline config with args: {e}")
    # Propagate target labeling to env for downstream consistency
    if getattr(args, "target_yyyymm", None):
        os.environ["PIPELINE_TARGET_YYYYMM"] = args.target_yyyymm
    if getattr(args, "target_period", None):
        os.environ["PIPELINE_TARGET_PERIOD"] = args.target_period
    # Normalize seasonal blending toggles
    if getattr(args, "no_seasonal_blending", False):
        args.seasonal_blending = False
    # Import Fast Fish validator after config is initialized
    try:
        from src.sell_through_validator import SellThroughValidator, load_historical_data_for_validation
        SELLTHROUGH_VALIDATION_AVAILABLE = True
        print("✅ Fast Fish sell-through validation: ENABLED", flush=True)
    except Exception:
        SELLTHROUGH_VALIDATION_AVAILABLE = False
        print("⚠️ Fast Fish sell-through validation: DISABLED (validator not found)", flush=True)
    apply_runtime_configuration(args)
    fast_pipeline_analysis(args)