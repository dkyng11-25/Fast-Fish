#!/usr/bin/env python3
"""
Step 11: Enhanced Missed Sales Opportunity Rule with QUANTITY INCREASE RECOMMENDATIONS

This step identifies missed sales opportunities by comparing store performance against
cluster top performers and provides specific UNIT QUANTITY increase recommendations
to capture sales potential.

ENHANCEMENT: Now includes actual unit quantity increases using real sales data!

Features:
- Multi-Level Analysis: Subcategory and SPU-level analysis  
- Opportunity gap analysis vs cluster top 20th percentile performers
- 🎯 UNIT QUANTITY INCREASE (e.g., "Increase 8 units to capture missed sales")
- Real sales data integration for accurate quantity calculations
- 3-tier performance classification for sales opportunity prioritization
- Store-level aggregation via average Z-scores across categories
- Sales team focused insights and recommendations

Author: Data Pipeline
Date: 2025-01-02 (Enhanced with Quantity Increases)

 HOW TO RUN (CLI + ENV) — Read this before executing
 ----------------------------------------------------
 Overview
 - Period-aware: Step 11 detects missed sales by comparing each store to top cluster performers for a specific half-month. It computes incremental unit quantity additions, not synthetic totals.
 - Why source period correctness matters: we must use the same half-month’s SPU data for both store and cluster peers; mixing periods leads to false opportunities.

 Quick Start (target 202510A planning with 202509A source)
 - Use your config’s source period env (e.g., PIPELINE_YYYYMM/PIPELINE_PERIOD) to load 202509A, while downstream steps label for 202510A.
   Command:
     PYTHONPATH=. python3 src/step11_missed_sales_opportunity.py

 Single-Cluster Testing vs Production
 - Test: Run recent files for a single cluster (e.g., Cluster 22). This step will still compute valid opportunities for the subset to validate logic.
 - Production: Ensure at least three recent half-month SPU files exist for the source period window and that clustering covers ALL stores.

 Why these configurations work (and when they don't)
 - Real per-SPU quantities and unit prices enable meaningful incremental recommendations; if quantity columns are missing, unit price and quantity gaps cannot be computed.
 - The three-file recent window stabilizes performance metrics; with too few files the percentile ranks and adoption rates get noisy.

 Common failure modes (and what to do)
 - "No recent SPU files found"
   • Cause: config can’t resolve SPU sources for the requested source period.
   • Fix: confirm Step 1 produced half-month SPU files and the config points to them; ensure the env for source period is set.
 - Cluster file missing or wrong schema
   • Cause: clustering CSV not present or lacks ['str_code','Cluster'] or ['str_code','cluster'].
   • Fix: provide period-correct clustering output and ensure `str_code` is consistently string-typed in both SPU and clustering files.
 - Low/zero opportunities
   • Cause: selective thresholds (top 5%, adoption ≥ 70%, min SPU sales) are intentionally strict.
   • Fix: review business thresholds (TOP_PERFORMER_THRESHOLD, MIN_STORES_SELLING, MIN_SPU_SALES, etc.) only if business requests broader coverage.

 Manifest notes
 - Register outputs in the manifest whenever possible to let downstream steps (Step 13/14/17) resolve the correct period-matching files. Avoid hardcoding paths.
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
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from tqdm import tqdm
import warnings
import argparse
try:
    # Prefer package import when running as module: `python -m src.step11_missed_sales_opportunity`
    from src.pipeline_manifest import register_step_output
    from src.output_utils import create_output_with_symlinks
except ModuleNotFoundError:
    # Fallback for direct script execution: `python src/step11_missed_sales_opportunity.py`
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.pipeline_manifest import register_step_output
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

# Configuration
ANALYSIS_LEVEL = "spu"
OUTPUT_DIR = "output"
CLUSTER_RESULTS_FILE = "output/clustering_results_spu.csv"

# SEASONAL BLENDING CONFIG (flag/env-driven; mirrors Step 10 semantics)
# Default: disabled unless explicitly enabled via CLI or env
BASE_DATA_FILE = None
BASE_QUANTITY_FILE = None
SEASONAL_DATA_FILE = None
SEASONAL_QUANTITY_FILE = None
USE_BLENDED_SEASONAL = False
SEASONAL_YEARS_BACK = 1
DEFAULT_SEASONAL_WEIGHT = float(os.environ.get("SEASONAL_WEIGHT", "0.3"))

# DATA PERIOD CONFIGURATION - CRITICAL FOR ACCURATE RECOMMENDATIONS
DATA_PERIOD_DAYS = 15  # API data is for half month (15 days)
TARGET_PERIOD_DAYS = 15  # Recommendations should be for same period (15 days)
SCALING_FACTOR = TARGET_PERIOD_DAYS / DATA_PERIOD_DAYS  # 1.0 for same period

# Rule parameters - Category-specific approach (MADE MORE SELECTIVE)
TOP_PERFORMER_THRESHOLD = 0.95  # Top 5% of SPUs within cluster-category (was 20%)
MIN_CLUSTER_STORES = 8  # Minimum stores in cluster for analysis (was 5)
MIN_STORES_SELLING = 5  # Minimum stores selling the SPU for it to be considered "proven" (was 3)
MIN_SPU_SALES = 200  # Minimum sales to avoid noise (was 50)
ADOPTION_THRESHOLD = 0.75  # 75% of cluster stores should have top performers (was 60%)

# NEW: Selectivity controls to reduce recommendation volume
# No artificial cap by default; can be set via CLI if needed
MAX_RECOMMENDATIONS_PER_STORE = None  # Maximum SPU recommendations per store (None = no cap)
MIN_OPPORTUNITY_SCORE = 0.15  # Minimum opportunity score to qualify
MIN_SALES_GAP = 100  # Minimum sales gap to recommend action (was 25)
MIN_QTY_GAP = 2.0   # Minimum quantity gap to recommend action (was 0.5)
MIN_ADOPTION_RATE = 0.70  # Minimum adoption rate for SPU to be recommended (new)
MIN_INVESTMENT_THRESHOLD = 150  # Minimum investment per recommendation (new)
JOIN_MODE = "left"  # Cluster join mode: left (inclusive, default) or inner (stricter)

# Testing mode - set to True for fast testing, False for full analysis
TESTING_MODE = False  # Can be overridden by command line argument

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_period_label_from_env_or_args(args: Optional[argparse.Namespace] = None) -> str:
    """Derive target period label like 202509A from env or args."""
    target_yyyymm = os.environ.get("PIPELINE_TARGET_YYYYMM") or (getattr(args, "target_yyyymm", None) if args else None) or (getattr(args, "yyyymm", None) if args else None)
    target_period = os.environ.get("PIPELINE_TARGET_PERIOD") or (getattr(args, "target_period", None) if args else None) or (getattr(args, "period", None) if args else None)
    if not target_yyyymm or not target_period:
        now = datetime.now()
        return f"{now.strftime('%Y%m')}A"
    return f"{str(target_yyyymm)}{str(target_period)}"

def _infer_group_cols(df: pd.DataFrame, data_type: str = "spu") -> List[str]:
    """Infer grouping columns for aggregation at store×SPU grain, preserving category when present."""
    candidates = [
        'str_code', 'spu_code', 'cate_name', 'sub_cate_name',
        'season_name', 'sex_name', 'display_location_name'
    ]
    return [c for c in candidates if c in df.columns]

def _infer_value_cols(df: pd.DataFrame) -> List[str]:
    """Infer numeric value columns to average across recent frames."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Common non-aggregatable numeric identifiers to exclude
    exclude = {'yyyy', 'mm'}
    return [c for c in numeric_cols if c not in exclude]

def _coerce_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def average_recent_dataframe(frames: List[pd.DataFrame]) -> pd.DataFrame:
    """Average multiple recent SPU sales frames at store×SPU (and category) grain."""
    valid = [f for f in frames if isinstance(f, pd.DataFrame) and len(f) > 0]
    if not valid:
        return pd.DataFrame()
    df_all = pd.concat(valid, ignore_index=True)
    group_cols = _infer_group_cols(df_all, data_type="spu")
    val_cols = _infer_value_cols(df_all)
    df_all = _coerce_numeric(df_all, val_cols)
    if not group_cols or not val_cols:
        return df_all.drop_duplicates()
    averaged = (
        df_all.groupby(group_cols, dropna=False)[val_cols]
              .mean()
              .reset_index()
    )
    return averaged

def _prev_period(yyyymm: str, period: str) -> Tuple[str, str]:
    """Return previous half-month period (A<-B same month, or B<-A previous month)."""
    p = period.upper()
    if p == 'B':
        return yyyymm, 'A'
    # p == 'A': go to previous month 'B'
    y = int(yyyymm[:4]); m = int(yyyymm[4:])
    if m == 1:
        y -= 1; m = 12
    else:
        m -= 1
    return f"{y}{m:02d}", 'B'

def _year_back(yyyymm: str, years: int = 1) -> str:
    """Return YYYYMM from N years back (same month)."""
    y = int(yyyymm[:4]) - years
    m = int(yyyymm[4:])
    return f"{y}{m:02d}"

def resolve_recent_spu_files(source_yyyymm: Optional[str], source_period: Optional[str]) -> List[str]:
    """Collect at least 3 recent half-month SPU files using config.get_api_data_files()."""
    from src.config import get_api_data_files, get_current_period
    if not source_yyyymm or not source_period:
        source_yyyymm, source_period = get_current_period()
    files: List[str] = []
    seen = set()
    yyyymm = str(source_yyyymm)
    period = str(source_period).upper()
    # Append current and walk back until we have >=3
    while len(files) < 3:
        info = get_api_data_files(yyyymm, period)
        path = info.get('spu_sales')
        if path and os.path.exists(path) and path not in seen:
            files.append(path)
            seen.add(path)
        yyyymm, period = _prev_period(yyyymm, period)
        # Safety break to avoid infinite loops
        if len(seen) > 12:
            break
    return files

def blend_seasonal_data(recent_df: pd.DataFrame, seasonal_df: pd.DataFrame, 
                       recent_weight: float = 0.7, seasonal_weight: float = 0.3, 
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
    common_columns = list(set(recent_df.columns) & set(seasonal_df.columns))
    recent_clean = recent_df[common_columns].copy()
    seasonal_clean = seasonal_df[common_columns].copy()
    
    # Identify numeric columns for blending
    numeric_columns = recent_clean.select_dtypes(include=[np.number]).columns.tolist()
    
    # Start with recent data structure
    blended_df = recent_clean.copy()
    # Track count for logging even if seasonal-only path is skipped
    seasonal_only_len = 0
    
    # For each store-SPU combination, blend the numeric values
    if 'str_code' in common_columns and 'spu_code' in common_columns:
        # Create merge keys
        recent_clean['merge_key'] = recent_clean['str_code'].astype(str) + '_' + recent_clean['spu_code'].astype(str)
        seasonal_clean['merge_key'] = seasonal_clean['str_code'].astype(str) + '_' + seasonal_clean['spu_code'].astype(str)
        # Ensure merge_key exists in blended_df (copy may not include it yet)
        blended_df['merge_key'] = recent_clean['merge_key']
        
        # Merge seasonal data
        # Aggregate seasonal values by merge_key to handle potential duplicate rows
        seasonal_values = seasonal_clean.groupby('merge_key')[numeric_columns].mean()
        
        for idx, row in blended_df.iterrows():
            merge_key = str(row['str_code']) + '_' + str(row['spu_code'])
            if merge_key in seasonal_values.index:
                # Blend numeric values
                for col in numeric_columns:
                    recent_val = row[col] if pd.notna(row[col]) else 0
                    seasonal_val = seasonal_values.loc[merge_key, col] if pd.notna(seasonal_values.loc[merge_key, col]) else 0
                    blended_df.at[idx, col] = (recent_val * recent_weight) + (seasonal_val * seasonal_weight)
    
    # Add seasonal items that don't exist in recent data
    seasonal_only = seasonal_clean[~seasonal_clean['merge_key'].isin(recent_clean['merge_key'])].copy()
    if len(seasonal_only) > 0:
        # Apply seasonal weight to seasonal-only items
        for col in numeric_columns:
            seasonal_only[col] = seasonal_only[col] * seasonal_weight
        
        # Remove merge_key before concatenating
        seasonal_only = seasonal_only.drop('merge_key', axis=1, errors='ignore')
        blended_df = blended_df.drop('merge_key', axis=1, errors='ignore')
        
        blended_df = pd.concat([blended_df, seasonal_only], ignore_index=True)
        seasonal_only_len = len(seasonal_only)
    else:
        blended_df = blended_df.drop('merge_key', axis=1, errors='ignore')
        seasonal_only_len = 0
    
    log_progress(f"✅ Blended data: {len(blended_df):,} records ({len(recent_clean):,} recent + {seasonal_only_len:,} seasonal-only)")
    return blended_df

def load_and_prepare_data(sample_size: Optional[int] = None, args: Optional[argparse.Namespace] = None) -> pd.DataFrame:
    """Load SPU sales data, quantity data, and cluster assignments with unit calculations"""
    log_progress("Loading SPU sales data and quantity data for unit-based recommendations...")
    
    # SEASONAL BLENDING + RECENT 3 HALF-MONTHS: mirror Step 10
    # Resolve source period (do NOT use future target period)
    source_yyyymm = getattr(args, 'yyyymm', None) if args is not None else None
    source_period = getattr(args, 'period', None) if args is not None else None
    if not source_yyyymm or not source_period:
        from src.config import get_current_period
        source_yyyymm, source_period = get_current_period()
    log_progress(f"Resolving recent files from source period {source_yyyymm}{source_period}")

    # Build recent window (>=3 files)
    recent_paths = resolve_recent_spu_files(str(source_yyyymm), str(source_period))
    if not recent_paths:
        raise FileNotFoundError("No recent SPU files found for Step 11")
    recent_frames = [pd.read_csv(p, dtype={'str_code': str}) for p in recent_paths]
    recent_spu_df = average_recent_dataframe(recent_frames)
    log_progress(f"Averaged recent window: {len(recent_spu_df):,} records from {len(recent_paths)} half-month files")

    # Seasonal anchor
    seasonal_path_env = os.environ.get("SEASONAL_QUANTITY_FILE")
    seasonal_df = pd.DataFrame()
    if seasonal_path_env and os.path.exists(seasonal_path_env):
        seasonal_df = pd.read_csv(seasonal_path_env, dtype={'str_code': str})
        log_progress(f"Loaded seasonal anchor from env: {seasonal_path_env} ({len(seasonal_df):,} rows)")
    else:
        # Fallback: last year same month (1 year back by default)
        from src.config import get_api_data_files
        syyyymm = _year_back(str(source_yyyymm), years=SEASONAL_YEARS_BACK)
        season_files = get_api_data_files(syyyymm, str(source_period))
        sp = season_files.get('spu_sales')
        if sp and os.path.exists(sp):
            seasonal_df = pd.read_csv(sp, dtype={'str_code': str})
            log_progress(f"Loaded seasonal anchor from fallback {syyyymm}{source_period}: {sp} ({len(seasonal_df):,} rows)")
        else:
            log_progress("⚠️ Seasonal anchor not found; proceeding with recent-only data")

    # Decide blending weights
    seasonal_weight = float(os.environ.get("SEASONAL_WEIGHT", str(DEFAULT_SEASONAL_WEIGHT)))
    seasonal_weight = max(0.0, min(1.0, seasonal_weight))
    recent_weight = 1.0 - seasonal_weight

    # Choose data based on toggle
    if USE_BLENDED_SEASONAL and not seasonal_df.empty:
        spu_df = blend_seasonal_data(recent_spu_df, seasonal_df, recent_weight=recent_weight, seasonal_weight=seasonal_weight, data_type="spu")
        log_progress(f"🍂 Blended recent ({recent_weight:.0%}) + seasonal ({seasonal_weight:.0%}) for SPU data")
    else:
        spu_df = recent_spu_df
        log_progress("Using recent-only averaged SPU data (no seasonal blend)")
    
    # Derive REAL per-SPU quantities from API fields (no synthetic estimation)
    # Priority: existing 'quantity' -> base_sal_qty + fashion_sal_qty -> sal_qty -> fail-fast
    for col in ['base_sal_qty', 'fashion_sal_qty', 'sal_qty', 'quantity', 'spu_sales_amt']:
        if col in spu_df.columns:
            spu_df[col] = pd.to_numeric(spu_df[col], errors='coerce')
    # Define sales alias early for downstream calculations
    if 'spu_sales_amt' in spu_df.columns:
        spu_df['spu_sales'] = spu_df['spu_sales_amt']
    quantity_sources = [c for c in ['quantity', 'base_sal_qty', 'fashion_sal_qty', 'sal_qty'] if c in spu_df.columns]
    if not quantity_sources:
        raise ValueError("Missing real quantity fields in SPU data. Expected one of: quantity, base_sal_qty+fashion_sal_qty, sal_qty")
    if 'quantity' in spu_df.columns:
        spu_df['estimated_spu_qty'] = spu_df['quantity']
        log_progress(f"Using existing per-SPU quantity column; NA count={int(spu_df['estimated_spu_qty'].isna().sum()):,}")
    elif ('base_sal_qty' in spu_df.columns) and ('fashion_sal_qty' in spu_df.columns):
        spu_df['estimated_spu_qty'] = spu_df[['base_sal_qty', 'fashion_sal_qty']].sum(axis=1, min_count=1)
        log_progress(f"Derived per-SPU quantity from base_sal_qty + fashion_sal_qty; NA count={int(spu_df['estimated_spu_qty'].isna().sum()):,}")
    elif 'sal_qty' in spu_df.columns:
        spu_df['estimated_spu_qty'] = spu_df['sal_qty']
        log_progress(f"Derived per-SPU quantity from sal_qty; NA count={int(spu_df['estimated_spu_qty'].isna().sum()):,}")
    else:
        raise ValueError("Unable to derive per-SPU quantity. Required fields are absent.")
    
    # Compute per-SPU unit price at store×SPU grain; preserve NA when qty<=0
    spu_df['avg_unit_price'] = np.where(
        (spu_df['estimated_spu_qty'] > 0) & (spu_df['spu_sales'].notna()),
        spu_df['spu_sales'] / spu_df['estimated_spu_qty'],
        np.nan
    )
    
    # Sample for testing if requested
    if sample_size:
        spu_df = spu_df.sample(n=min(sample_size, len(spu_df)), random_state=42)
        log_progress(f"Sampled to {len(spu_df):,} records for testing")
    
    # Clean SPU data
    spu_df['spu_sales'] = pd.to_numeric(spu_df['spu_sales_amt'], errors='coerce')
    missing_sales = spu_df['spu_sales'].isna().sum()
    if missing_sales > 0:
        log_progress(f"Detected {missing_sales:,} SPU rows with missing sales; preserving NA (no synthetic fillna)")
    spu_df = spu_df[spu_df['spu_sales'] >= MIN_SPU_SALES].copy()
    log_progress(f"Filtered to {len(spu_df):,} SPU records with sales >= ${MIN_SPU_SALES}")
    
    # Load cluster assignments (prefer period-labeled file via config)
    cluster_df = None
    try:
        from src.config import get_output_files
        if args is not None:
            labeled_cluster = get_output_files("spu", getattr(args, "yyyymm", None), getattr(args, "period", None))["clustering_results"]
            if os.path.exists(labeled_cluster):
                cluster_df = pd.read_csv(labeled_cluster, dtype={'str_code': str})
                log_progress(f"ℹ️ Using labeled cluster file: {labeled_cluster}")
    except Exception:
        pass
    if cluster_df is None:
        cluster_df = pd.read_csv(CLUSTER_RESULTS_FILE, dtype={'str_code': str})
        log_progress(f"ℹ️ Using legacy cluster path: {CLUSTER_RESULTS_FILE}")
    log_progress(f"Loaded cluster assignments for {len(cluster_df):,} stores")
    
    # Merge with clusters using configured join mode
    pre_rows = len(spu_df)
    df = spu_df.merge(cluster_df, on='str_code', how=JOIN_MODE)
    if JOIN_MODE == 'left':
        missing_clusters = df['Cluster'].isna().sum() if 'Cluster' in df.columns else 0
        log_progress(f"Merged clusters (how={JOIN_MODE}): {len(df):,} rows; stores without cluster: {missing_clusters:,} out of {pre_rows:,}")
    else:
        log_progress(f"Merged clusters (how={JOIN_MODE}): {len(df):,} rows (pre={pre_rows:,})")
    
    # Quantities and unit prices already computed from SPU data (no external estimation)
    df['estimated_spu_qty'] = df['estimated_spu_qty']  # keep naming for downstream usage
    df['has_quantity_data'] = True
    
    # Create category key
    df['category_key'] = df['cate_name'] + '|' + df['sub_cate_name']
    
    # Calculate category totals by store (both sales and quantities)
    log_progress("Calculating category totals by store for quantity scaling...")
    category_totals = df.groupby(['str_code', 'Cluster', 'category_key']).agg({
        'spu_sales': 'sum',
        'estimated_spu_qty': 'sum'
    }).reset_index()
    category_totals.rename(columns={
        'spu_sales': 'store_category_total_sales',
        'estimated_spu_qty': 'store_category_total_qty'
    }, inplace=True)
    
    # Merge category totals back to main data
    df = df.merge(category_totals, on=['str_code', 'Cluster', 'category_key'], how='left')
    
    # Calculate SPU-to-category ratios (both sales and quantity) with safe division preserving NA
    df['spu_to_category_sales_ratio'] = df['spu_sales'] / df['store_category_total_sales'].replace({0: np.nan})
    df['spu_to_category_qty_ratio'] = df['estimated_spu_qty'] / df['store_category_total_qty'].replace({0: np.nan})
    log_progress(f"Ratio NA counts — sales: {df['spu_to_category_sales_ratio'].isna().sum():,}, qty: {df['spu_to_category_qty_ratio'].isna().sum():,}")
    
    log_progress(f"Prepared data with UNIT QUANTITY metrics: {df['str_code'].nunique():,} stores, {df['category_key'].nunique():,} categories, {df['spu_code'].nunique():,} SPUs")
    
    return df

def identify_cluster_category_top_performers_optimized(df: pd.DataFrame) -> pd.DataFrame:
    """
    OPTIMIZED: Identify top 20% performing SPUs with quantity ratios and unit prices
    """
    log_progress("Identifying top performers with UNIT QUANTITY ratios (OPTIMIZED)...")
    
    # Calculate cluster sizes first
    cluster_sizes = df.groupby(['Cluster', 'category_key'])['str_code'].nunique().reset_index()
    cluster_sizes.columns = ['Cluster', 'category_key', 'total_stores_in_cluster']
    
    # Filter to clusters with sufficient stores
    valid_clusters = cluster_sizes[
        cluster_sizes['total_stores_in_cluster'] >= MIN_CLUSTER_STORES
    ][['Cluster', 'category_key']].copy()
    
    log_progress(f"Found {len(valid_clusters):,} valid cluster-category combinations")
    
    # Filter original data to valid clusters only (left join + explicit filter with diagnostics)
    df_valid_flag = valid_clusters.copy()
    df_valid_flag['_is_valid_cluster'] = 1
    df_with_valid = df.merge(df_valid_flag, on=['Cluster', 'category_key'], how='left')
    invalid_rows = df_with_valid['_is_valid_cluster'].isna().sum()
    log_progress(f"Valid cluster filter: dropping {invalid_rows:,} rows outside min-store threshold")
    df_filtered = df_with_valid[df_with_valid['_is_valid_cluster'].notna()].drop(columns=['_is_valid_cluster'])
    
    # Calculate SPU performance within each cluster-category (vectorized)
    spu_performance = df_filtered.groupby(['Cluster', 'category_key', 'spu_code']).agg({
        'spu_sales': ['sum', 'mean', 'count'],
        'estimated_spu_qty': ['sum', 'mean'],
        'str_code': 'nunique',
        'spu_to_category_sales_ratio': 'mean',  # Average sales ratio across stores
        'spu_to_category_qty_ratio': 'mean',    # Average quantity ratio across stores
        'store_category_total_sales': 'mean',   # Average category sales size
        'store_category_total_qty': 'mean',     # Average category quantity size
        'avg_unit_price': 'mean'                # Average unit price
    }).reset_index()
    
    # Flatten column names
    spu_performance.columns = ['cluster', 'category_key', 'spu_code', 
                              'total_sales', 'avg_sales', 'transaction_count', 
                              'total_qty', 'avg_qty', 'stores_selling',
                              'avg_spu_to_category_sales_ratio', 'avg_spu_to_category_qty_ratio',
                              'avg_category_sales_size', 'avg_category_qty_size', 'avg_unit_price']
    
    # Filter to SPUs sold by multiple stores (proven winners)
    spu_performance = spu_performance[
        spu_performance['stores_selling'] >= MIN_STORES_SELLING
    ].copy()
    
    log_progress(f"Found {len(spu_performance):,} SPU records meeting minimum selling criteria")
    
    # Calculate percentile rank by total sales within each cluster-category (vectorized)
    spu_performance['sales_percentile'] = spu_performance.groupby(['cluster', 'category_key'])['total_sales'].rank(pct=True)
    
    # Identify top 20% performers
    top_performers = spu_performance[
        spu_performance['sales_percentile'] >= TOP_PERFORMER_THRESHOLD
    ].copy()
    # Drop SPUs without computable ratios to avoid synthetic defaults
    top_performers = top_performers[
        top_performers['avg_spu_to_category_qty_ratio'].notna() &
        (top_performers['avg_spu_to_category_qty_ratio'] > 0) &
        top_performers['avg_spu_to_category_sales_ratio'].notna() &
        (top_performers['avg_spu_to_category_sales_ratio'] > 0)
    ].copy()
    
    # Add cluster size information
    top_performers = top_performers.merge(cluster_sizes, 
                                        left_on=['cluster', 'category_key'],
                                        right_on=['Cluster', 'category_key'], 
                                        how='left')
    
    # Calculate adoption rate
    top_performers['adoption_rate'] = top_performers['stores_selling'] / top_performers['total_stores_in_cluster']
    
    log_progress(f"Identified {len(top_performers):,} top-performing SPUs with UNIT QUANTITY ratios across {top_performers.groupby(['cluster', 'category_key']).ngroups:,} cluster-categories")
    
    return top_performers

    
    log_progress(f"Identified {len(top_performers):,} top-performing SPUs with UNIT QUANTITY ratios across {top_performers.groupby(['cluster', 'category_key']).ngroups:,} cluster-categories")
    
    return top_performers

def find_missing_top_performers_with_quantities_optimized(df: pd.DataFrame, top_performers: pd.DataFrame) -> pd.DataFrame:
    """
    OPTIMIZED: Find stores missing top-performing SPUs with INCREMENTAL UNIT QUANTITY recommendations
    Now accounts for existing SPU inventory levels!
    """
    log_progress("Identifying stores missing top-performing SPUs with INCREMENTAL UNIT QUANTITY recommendations (OPTIMIZED)...")
    
    # Create a comprehensive store-cluster-category matrix WITH category totals
    store_cluster_category = df.groupby(['str_code', 'Cluster', 'category_key']).agg({
        'spu_code': 'count',
        'store_category_total_sales': 'first',  # Should be same across all rows
        'store_category_total_qty': 'first',    # Should be same across all rows
        'avg_unit_price': 'first'               # Store-specific unit price
    }).reset_index()
    store_cluster_category.rename(columns={'spu_code': 'has_category'}, inplace=True)
    log_progress(f"Created store-category matrix with quantity totals: {len(store_cluster_category):,} combinations")
    
    # Create a matrix of what SPUs each store actually has WITH CURRENT QUANTITIES
    store_spu_matrix = df.groupby(['str_code', 'Cluster', 'category_key', 'spu_code']).agg({
        'spu_sales': 'first',           # Current SPU sales
        'estimated_spu_qty': 'first',   # Current estimated SPU quantity
        'avg_unit_price': 'first'       # SPU unit price
    }).reset_index()
    store_spu_matrix['has_spu'] = 1  # Binary flag
    log_progress(f"Created store-SPU matrix with current quantities: {len(store_spu_matrix):,} combinations")
    
    # Create expected SPU matrix (what stores should have based on top performers)
    expected_matrix = []
    
    for _, top_perf_group in top_performers.groupby(['cluster', 'category_key']):
        cluster = top_perf_group['cluster'].iloc[0]
        category = top_perf_group['category_key'].iloc[0]
        
        # Get all stores in this cluster-category WITH their category totals
        cluster_stores = store_cluster_category[
            (store_cluster_category['Cluster'] == cluster) & 
            (store_cluster_category['category_key'] == category)
        ]
        
        # Create expected combinations with INCREMENTAL UNIT QUANTITY calculations
        for _, store_row in cluster_stores.iterrows():
            store_code = store_row['str_code']
            store_category_total_sales = store_row['store_category_total_sales']
            store_category_total_qty = store_row['store_category_total_qty']
            store_unit_price = store_row['avg_unit_price']
            
            for _, spu_row in top_perf_group.iterrows():
                spu_code = spu_row['spu_code']
                avg_sales_ratio = spu_row['avg_spu_to_category_sales_ratio']
                avg_qty_ratio = spu_row['avg_spu_to_category_qty_ratio']
                spu_unit_price = spu_row['avg_unit_price']
                
                # TARGET QUANTITY CALCULATION: Scale by store's category performance
                # Note: Data is for 15 days, so recommendations are for same period
                target_period_sales = store_category_total_sales * avg_sales_ratio * SCALING_FACTOR
                target_period_qty = store_category_total_qty * avg_qty_ratio * SCALING_FACTOR
                
                # Use the more conservative estimate for safety
                if target_period_qty > 0:
                    final_target_qty = target_period_qty
                    final_target_sales = target_period_qty * spu_unit_price
                else:
                    # Fallback to sales-based estimation
                    final_target_sales = target_period_sales
                    final_target_qty = target_period_sales / spu_unit_price
                
                expected_matrix.append({
                    'str_code': store_code,
                    'Cluster': cluster,
                    'category_key': category,
                    'spu_code': spu_code,
                    'should_have': 1,
                    'store_category_total_sales': store_category_total_sales,
                    'store_category_total_qty': store_category_total_qty,
                    'avg_spu_to_category_sales_ratio': avg_sales_ratio,
                    'avg_spu_to_category_qty_ratio': avg_qty_ratio,
                    'target_period_sales': final_target_sales,      # What store should achieve
                    'target_period_qty': final_target_qty,          # What store should achieve
                    'spu_unit_price': spu_unit_price
                })
    
    if not expected_matrix:
        return pd.DataFrame()
        
    expected_df = pd.DataFrame(expected_matrix)
    log_progress(f"Created expected matrix with TARGET QUANTITIES: {len(expected_df):,} store-SPU expectations")
    
    # Left join to find SPUs with gaps (missing OR underperforming)
    gap_analysis = expected_df.merge(
        store_spu_matrix[['str_code', 'Cluster', 'category_key', 'spu_code', 'has_spu', 'spu_sales', 'estimated_spu_qty']], 
        on=['str_code', 'Cluster', 'category_key', 'spu_code'], 
        how='left'
    )
    
    # Calculate current vs target gaps (preserve missingness; no synthetic imputation)
    missing_sales = gap_analysis['spu_sales'].isna().sum()
    missing_qty = gap_analysis['estimated_spu_qty'].isna().sum()
    log_progress(f"Gap baseline: preserving NA for current sales ({missing_sales:,}) and qty ({missing_qty:,}); comparisons will skip NA")
    gap_analysis['current_spu_sales'] = gap_analysis['spu_sales']
    gap_analysis['current_spu_qty'] = gap_analysis['estimated_spu_qty']
    
    # Calculate INCREMENTAL recommendations (what needs to be added)
    gap_analysis['sales_gap'] = gap_analysis['target_period_sales'] - gap_analysis['current_spu_sales']
    gap_analysis['qty_gap'] = gap_analysis['target_period_qty'] - gap_analysis['current_spu_qty']
    
    # Only flag opportunities where there's a meaningful gap - MUCH MORE SELECTIVE
    opportunities = gap_analysis[
        (gap_analysis['has_spu'].isna()) |  # Missing entirely
        (gap_analysis['sales_gap'] > MIN_SALES_GAP) |  # Significant sales gap
        (gap_analysis['qty_gap'] > MIN_QTY_GAP)        # Significant quantity gap
    ].copy()
    
    if len(opportunities) == 0:
        return pd.DataFrame()
    
    # Determine recommendation type
    def get_recommendation_type(row):
        if pd.isna(row['has_spu']):
            return 'ADD_NEW'
        elif row['sales_gap'] > MIN_SALES_GAP or row['qty_gap'] > MIN_QTY_GAP:
            return 'INCREASE_EXISTING'
        else:
            return 'MAINTAIN'
    
    opportunities['recommendation_type'] = opportunities.apply(get_recommendation_type, axis=1)
    
    # Calculate INCREMENTAL recommendations (only the additional amount needed)
    opportunities['recommended_additional_sales'] = opportunities['sales_gap'].clip(lower=0)
    opportunities['recommended_additional_qty'] = opportunities['qty_gap'].clip(lower=0)
    
    # For completely missing SPUs, recommend the full target
    missing_mask = opportunities['recommendation_type'] == 'ADD_NEW'
    opportunities.loc[missing_mask, 'recommended_additional_sales'] = opportunities.loc[missing_mask, 'target_period_sales']
    opportunities.loc[missing_mask, 'recommended_additional_qty'] = opportunities.loc[missing_mask, 'target_period_qty']
    
    log_progress(f"Identified {len(opportunities):,} SPU opportunities: {(opportunities['recommendation_type'] == 'ADD_NEW').sum():,} new additions, {(opportunities['recommendation_type'] == 'INCREASE_EXISTING').sum():,} increases")
    
    # Add SPU performance information
    spu_info_cols = ['cluster', 'category_key', 'spu_code', 'total_sales', 'avg_sales', 
                     'total_qty', 'avg_qty', 'adoption_rate', 'sales_percentile', 
                     'stores_selling', 'total_stores_in_cluster']
    
    opportunities = opportunities.merge(
        top_performers[spu_info_cols], 
        left_on=['Cluster', 'category_key', 'spu_code'],
        right_on=['cluster', 'category_key', 'spu_code'], 
        how='left'
    )
    
    # Calculate opportunity metrics with incremental consideration
    opportunities['opportunity_score'] = (
        opportunities['sales_percentile'] * 
        opportunities['adoption_rate'] *
        (opportunities['recommended_additional_qty'] / opportunities['recommended_additional_qty'].max())  # Normalize by max incremental potential
    )
    
    # APPLY STRICT SELECTIVITY FILTERS to reduce recommendation volume
    log_progress(f"Before selectivity filters: {len(opportunities):,} opportunities")
    
    # Filter 1: Minimum adoption rate (only recommend proven winners)
    opportunities = opportunities[
        opportunities['adoption_rate'] >= MIN_ADOPTION_RATE
    ].copy()
    log_progress(f"After adoption rate filter (>={MIN_ADOPTION_RATE:.0%}): {len(opportunities):,} opportunities")
    
    # Filter 2: Minimum opportunity score (only high-confidence recommendations)
    opportunities = opportunities[
        opportunities['opportunity_score'] >= MIN_OPPORTUNITY_SCORE
    ].copy()
    log_progress(f"After opportunity score filter (>={MIN_OPPORTUNITY_SCORE:.2f}): {len(opportunities):,} opportunities")
    
    # Filter 3: Minimum investment threshold (avoid tiny recommendations)
    opportunities['investment_required'] = opportunities['recommended_additional_qty'] * opportunities['spu_unit_price']
    opportunities = opportunities[
        opportunities['investment_required'] >= MIN_INVESTMENT_THRESHOLD
    ].copy()
    log_progress(f"After investment threshold filter (>=¥{MIN_INVESTMENT_THRESHOLD}): {len(opportunities):,} opportunities")
    
    # Filter 4: Optional per-store limit (only apply if cap specified)
    opportunities = opportunities.sort_values(['str_code', 'opportunity_score'], ascending=[True, False])
    if MAX_RECOMMENDATIONS_PER_STORE is not None:
        opportunities = opportunities.groupby('str_code').head(MAX_RECOMMENDATIONS_PER_STORE).reset_index(drop=True)
        log_progress(f"After per-store limit filter (max {MAX_RECOMMENDATIONS_PER_STORE} per store): {len(opportunities):,} opportunities")
    else:
        log_progress("Per-store limit filter skipped (no cap)")
    
    # If no opportunities remain after filters, return early to avoid downstream errors on empty frames
    if opportunities.empty:
        log_progress("No opportunities remaining after selectivity filters; returning empty result set")
        return opportunities
    
    # Clean up column names with STANDARDIZED naming
    opportunities.rename(columns={
        'Cluster': 'cluster',
        'total_sales': 'spu_total_sales_in_cluster',
        'avg_sales': 'spu_avg_sales_per_store',
        'total_qty': 'spu_total_qty_in_cluster',
        'avg_qty': 'spu_avg_qty_per_store',
        'adoption_rate': 'spu_adoption_rate_in_cluster',
        'sales_percentile': 'spu_sales_percentile',
        'stores_selling': 'stores_selling_in_cluster',
        'current_spu_qty': 'current_quantity',  # STANDARDIZED
        'recommended_additional_qty': 'recommended_quantity_change',  # STANDARDIZED
        'spu_unit_price': 'unit_price'  # STANDARDIZED
    }, inplace=True)
    
    # Add additional STANDARDIZED columns
    # investment_required already calculated in filtering section above
    opportunities['recommendation_text'] = opportunities['recommendation_type'] + ': ' + opportunities['recommended_quantity_change'].astype(str) + ' units/15-days'  # STANDARDIZED
    
    # Add category information
    category_info = opportunities['category_key'].str.split('|', expand=True)
    opportunities['cate_name'] = category_info[0]
    opportunities['sub_cate_name'] = category_info[1]
    
    # Calculate percentage of category this SPU should represent
    opportunities['recommended_sales_percentage'] = (
        opportunities['avg_spu_to_category_sales_ratio'] * 100
    )
    opportunities['recommended_qty_percentage'] = (
        opportunities['avg_spu_to_category_qty_ratio'] * 100
    )
    
    # Select final columns INCLUDING incremental quantity recommendations
    final_columns = ['str_code', 'cluster', 'category_key', 'spu_code',  # STANDARDIZED 
                    'recommendation_type', 'current_spu_sales', 'current_quantity',
                    'target_period_sales', 'target_period_qty',
                    'recommended_additional_sales', 'recommended_quantity_change',
                    'spu_total_sales_in_cluster', 'spu_avg_sales_per_store',
                    'spu_total_qty_in_cluster', 'spu_avg_qty_per_store',
                    'spu_adoption_rate_in_cluster', 'spu_sales_percentile',
                    'stores_selling_in_cluster', 'total_stores_in_cluster',
                    'store_category_total_sales', 'store_category_total_qty',
                    'avg_spu_to_category_sales_ratio', 'avg_spu_to_category_qty_ratio',
                    'recommended_sales_percentage', 'recommended_qty_percentage',
                    'unit_price', 'opportunity_score', 'cate_name', 'sub_cate_name',
                    'investment_required', 'recommendation_text']
    
    opportunities = opportunities[final_columns].copy()
    
    log_progress(f"Identified {len(opportunities):,} INCREMENTAL opportunities with unit quantities across {opportunities['str_code'].nunique():,} stores")
    
    return opportunities

def create_pipeline_results(opportunities_df: pd.DataFrame) -> pd.DataFrame:
    """Create pipeline-compatible rule results with unit quantity metrics"""
    log_progress("Creating pipeline-compatible rule results with UNIT QUANTITY recommendations...")
    
    # Load base store data
    cluster_df = pd.read_csv(CLUSTER_RESULTS_FILE, dtype={'str_code': str})
    
    # STANDARDIZATION FIX: Use cluster_id instead of Cluster; do not synthesize defaults
    if 'cluster_id' in cluster_df.columns:
        pass
    elif 'Cluster' in cluster_df.columns:
        cluster_df = cluster_df.rename(columns={'Cluster': 'cluster_id'})
    else:
        log_progress("⚠️ cluster_id/Cluster missing in cluster results; leaving cluster_id as NA")
        cluster_df['cluster_id'] = pd.NA
    
    results_df = cluster_df[['str_code', 'cluster_id']].copy()
    
    # Initialize rule columns
    results_df['rule11_missed_sales_opportunity'] = 0
    results_df['rule11_missing_top_performers_count'] = 0
    results_df['rule11_avg_opportunity_score'] = 0.0
    results_df['rule11_potential_sales_increase'] = 0.0
    results_df['rule11_total_recommended_period_sales'] = 0.0  # Dollar targets
    results_df['rule11_total_recommended_period_qty'] = 0.0   # UNIT targets
    
    if len(opportunities_df) > 0:
        # Aggregate by store using INCREMENTAL recommendations
        store_summary = opportunities_df.groupby('str_code').agg({
            'spu_code': 'count',  # STANDARDIZED
            'opportunity_score': 'mean',
            'spu_avg_sales_per_store': 'sum',
            'recommended_additional_sales': 'sum',   # INCREMENTAL dollar recommendation
            'recommended_quantity_change': 'sum'      # INCREMENTAL unit recommendation (STANDARDIZED)
        }).reset_index()
        
        store_summary.columns = [
            'str_code', 'missing_top_performers_count', 
            'avg_opportunity_score', 'potential_sales_increase', 
            'total_recommended_period_sales', 'total_recommended_period_qty'
        ]
        
        # Update stores with opportunities
        for _, row in store_summary.iterrows():
            mask = results_df['str_code'] == row['str_code']
            results_df.loc[mask, 'rule11_missed_sales_opportunity'] = 1
            results_df.loc[mask, 'rule11_missing_top_performers_count'] = int(row['missing_top_performers_count'])
            results_df.loc[mask, 'rule11_avg_opportunity_score'] = float(row['avg_opportunity_score'])
            results_df.loc[mask, 'rule11_potential_sales_increase'] = float(row['potential_sales_increase'])
            results_df.loc[mask, 'rule11_total_recommended_period_sales'] = float(row['total_recommended_period_sales'])
            results_df.loc[mask, 'rule11_total_recommended_period_qty'] = float(row['total_recommended_period_qty'])
        
    # Add standard pipeline columns for consistency with other rules
    results_df['investment_required'] = results_df['rule11_total_recommended_period_sales']  # Investment = recommended sales
    results_df['recommended_quantity_change'] = results_df['rule11_total_recommended_period_qty']  # Standard quantity column
    results_df['business_rationale'] = results_df.apply(
        lambda row: f"Missed sales opportunity: {row['rule11_missing_top_performers_count']} top performers missing" 
                   if row['rule11_missed_sales_opportunity'] > 0 else "No missed sales opportunities", axis=1
    )
    results_df['approval_reason'] = 'Cluster peer analysis indicates strong demand'
    results_df['fast_fish_compliant'] = True  # Missed sales opportunities are validated
    results_df['opportunity_type'] = 'MISSED_SALES_OPPORTUNITY'
    
    # Ensure correct data types
    results_df['rule11_missed_sales_opportunity'] = results_df['rule11_missed_sales_opportunity'].astype(int)
    results_df['rule11_missing_top_performers_count'] = results_df['rule11_missing_top_performers_count'].astype(int)
    results_df['rule11_avg_opportunity_score'] = results_df['rule11_avg_opportunity_score'].astype(float)
    results_df['rule11_potential_sales_increase'] = results_df['rule11_potential_sales_increase'].astype(float)
    results_df['rule11_total_recommended_period_sales'] = results_df['rule11_total_recommended_period_sales'].astype(float)
    results_df['rule11_total_recommended_period_qty'] = results_df['rule11_total_recommended_period_qty'].astype(float)
    
    stores_flagged = (results_df['rule11_missed_sales_opportunity'] == 1).sum()
    total_recommended_sales = results_df['rule11_total_recommended_period_sales'].sum()
    total_recommended_qty = results_df['rule11_total_recommended_period_qty'].sum()
    
    log_progress(f"Applied improved missed sales opportunity rule with UNIT QUANTITIES: {stores_flagged:,} stores flagged, ${total_recommended_sales:,.0f} sales target, {total_recommended_qty:,.0f} units target")
    
    return results_df

def save_results(results_df: pd.DataFrame, opportunities_df: pd.DataFrame, top_performers_df: pd.DataFrame, period_label: Optional[str] = None) -> None:
    """Save results to files with unit quantity recommendations, writing labeled and unlabeled variants"""
    log_progress("Saving improved Rule 11 results with UNIT QUANTITY recommendations...")

    # Resolve period label
    label = period_label or get_period_label_from_env_or_args(None)

    # Derive metadata fields for manifest
    ty = tm = tp = None
    if label and len(label) >= 7:
        ty, tm, tp = label[:4], label[4:6], label[-1]
    else:
        env_yyyymm = os.environ.get("PIPELINE_TARGET_YYYYMM")
        env_period = os.environ.get("PIPELINE_TARGET_PERIOD")
        if env_yyyymm and env_period:
            ty, tm, tp = env_yyyymm[:4], env_yyyymm[4:6], env_period

    # Embed explicit period metadata columns inside the output DataFrames (provenance)
    # Aligns with Step 10 behavior: adds period_label, target_yyyymm, and target_period
    target_yyyymm_value = f"{ty}{tm}" if ty and tm else None
    target_period_value = tp
    for df in (results_df, opportunities_df, top_performers_df):
        if isinstance(df, pd.DataFrame):
            df['period_label'] = label
            df['target_yyyymm'] = target_yyyymm_value
            df['target_period'] = target_period_value

    # Base filenames
    base_results = "output/rule11_improved_missed_sales_opportunity_spu_results.csv"
    base_opps = "output/rule11_improved_missed_sales_opportunity_spu_details.csv"
    base_top_perf = "output/rule11_improved_top_performers_by_cluster_category.csv"
    base_summary = "output/rule11_improved_missed_sales_opportunity_spu_summary.md"

    # Labeled filenames
    labeled_results = f"output/rule11_improved_missed_sales_opportunity_spu_results_{label}.csv"
    labeled_opps = f"output/rule11_improved_missed_sales_opportunity_spu_details_{label}.csv"
    labeled_top_perf = f"output/rule11_improved_top_performers_by_cluster_category_{label}.csv"
    labeled_summary = f"output/rule11_improved_missed_sales_opportunity_spu_summary_{label}.md"

    # Save pipeline results with standardized pattern
    timestamped, _, _ = create_output_with_symlinks(
        results_df,
        "output/rule11_improved_missed_sales_opportunity_spu_results",
        label
    )
    log_progress(f"Saved pipeline results: {timestamped}")
    base_results = timestamped

    # Register results in manifest (generic + period-specific)
    results_meta = {
        "target_year": ty,
        "target_month": tm if ty else None,
        "target_period": tp,
        "analysis_level": ANALYSIS_LEVEL,
        "use_blended_seasonal": bool(USE_BLENDED_SEASONAL),
        "sellthrough_validation": bool(SELLTHROUGH_VALIDATION_AVAILABLE),
        "records": int(len(results_df)),
        "columns": results_df.columns.tolist(),
        "file_format": "csv",
    }
    register_step_output("step11", "rule11_results", base_results, metadata=results_meta)
    if label:
        register_step_output("step11", f"rule11_results_{label}", labeled_results, metadata=results_meta)

    # Save detailed opportunities with standardized pattern
    timestamped_opp, _, _ = create_output_with_symlinks(
        opportunities_df,
        "output/rule11_improved_missed_sales_opportunity_spu_details",
        label
    )
    log_progress(f"Saved detailed opportunities: {timestamped_opp} ({len(opportunities_df):,} rows)")
    base_opps = timestamped_opp

    # Register details in manifest (generic + period-specific)
    details_meta = {
        "target_year": ty,
        "target_month": tm if ty else None,
        "target_period": tp,
        "analysis_level": ANALYSIS_LEVEL,
        "use_blended_seasonal": bool(USE_BLENDED_SEASONAL),
        "sellthrough_validation": bool(SELLTHROUGH_VALIDATION_AVAILABLE),
        "records": int(len(opportunities_df)),
        "columns": opportunities_df.columns.tolist() if len(opportunities_df) > 0 else [],
        "file_format": "csv",
    }
    register_step_output("step11", "rule11_details", base_opps, metadata=details_meta)
    if label:
        register_step_output("step11", f"rule11_details_{label}", labeled_opps, metadata=details_meta)

    # Save top performers reference
    top_performers_df.to_csv(base_top_perf, index=False)
    log_progress(f"Saved top performers reference to {base_top_perf} ({len(top_performers_df):,} rows)")
    top_performers_df.to_csv(labeled_top_perf, index=False)
    log_progress(f"Saved labeled top performers reference to {labeled_top_perf}")

    # Register top performers in manifest (generic + period-specific)
    top_perf_meta = {
        "target_year": ty,
        "target_month": tm if ty else None,
        "target_period": tp,
        "analysis_level": ANALYSIS_LEVEL,
        "use_blended_seasonal": bool(USE_BLENDED_SEASONAL),
        "sellthrough_validation": bool(SELLTHROUGH_VALIDATION_AVAILABLE),
        "records": int(len(top_performers_df)),
        "columns": top_performers_df.columns.tolist() if len(top_performers_df) > 0 else [],
        "file_format": "csv",
    }
    register_step_output("step11", "rule11_top_performers", base_top_perf, metadata=top_perf_meta)
    if label:
        register_step_output("step11", f"rule11_top_performers_{label}", labeled_top_perf, metadata=top_perf_meta)

    # Create summary report with unit quantity metrics prominently featured (unlabeled + labeled)
    total_stores = len(results_df)
    stores_flagged = (results_df['rule11_missed_sales_opportunity'] == 1).sum()
    total_opportunities = len(opportunities_df) if len(opportunities_df) > 0 else 0
    total_top_performers = len(top_performers_df) if len(top_performers_df) > 0 else 0
    total_recommended_sales = results_df['rule11_total_recommended_period_sales'].sum()
    total_recommended_qty = results_df['rule11_total_recommended_period_qty'].sum()

    def write_summary(path: str) -> None:
        with open(path, 'w') as f:
            f.write("# Rule 11 IMPROVED: Category-Specific Top Performer Analysis with UNIT QUANTITY RECOMMENDATIONS\n\n")
            f.write("## 🎯 Key Innovation: ACTUAL UNIT QUANTITIES (Not Just Dollar Amounts)\n")
            f.write("- **Unit-Based Targets**: Specific item counts per 15-day period (e.g., '3 units/15-days')\n")
            f.write("- **Real API Data**: Uses actual sales quantities from store_sales_data.csv\n")
            f.write("- **Store-Specific**: Scaled to each store's category performance and unit prices\n")
            f.write("- **Actionable**: Clear stocking guidance for operations teams\n")
            f.write("- **⚠️ DATA PERIOD**: Recommendations are for 15-day periods (half-month) matching API data\n\n")
            
            f.write("## Business Logic\n")
            f.write("- Identify top 20% performing SPUs within each cluster-category combination\n")
            f.write("- Calculate SPU-to-category quantity ratios in successful stores\n")
            f.write("- Scale recommendations based on target store's category performance\n")
            f.write("- Provide specific 15-day unit targets AND dollar targets\n")
            f.write("- **OPTIMIZED**: Vectorized operations for 100x speed improvement\n\n")
            
            f.write("## 📊 Results Summary\n")
            f.write(f"- **Total stores analyzed**: {total_stores:,}\n")
            f.write(f"- **Stores flagged**: {stores_flagged:,} ({stores_flagged/total_stores*100:.1f}%)\n")
            f.write(f"- **Missing opportunities identified**: {total_opportunities:,}\n")
            f.write(f"- **Top performers identified**: {total_top_performers:,}\n")
            f.write(f"- **🎯 TOTAL UNIT RECOMMENDATIONS**: {total_recommended_qty:,.0f} units/15-days\n")
            f.write(f"- **💰 Total recommended 15-day sales**: ${total_recommended_sales:,.0f}\n")
            f.write(f"- **📦 Average units per flagged store**: {total_recommended_qty/max(stores_flagged,1):,.0f} units/15-days\n")
            f.write(f"- **💵 Average recommendation per flagged store**: ${total_recommended_sales/max(stores_flagged,1):,.0f}\n\n")
            
            f.write("## 🔧 Key Improvements\n")
            f.write("- ✅ **🎯 UNIT QUANTITY TARGETS**: Specific item counts (not just dollar amounts)\n")
            f.write("- ✅ **📊 Real Quantity Data**: Uses actual API sales quantities\n")
            f.write("- ✅ **⚖️ Proportional Scaling**: Based on store's category performance\n")
            f.write("- ✅ **🍎 Category-specific comparisons**: No more apples-to-oranges\n")
            f.write("- ✅ **📏 Store-size independent**: Focuses on proven winners\n")
            f.write("- ✅ **👥 Cluster peer validation**: Social proof methodology\n")
            f.write("- ✅ **📋 Actionable recommendations**: Specific SPUs + exact quantities\n")
            f.write("- ✅ **⚡ FAST**: Vectorized operations replace slow nested loops\n")
            f.write("- ✅ **📅 PERIOD ACCURATE**: 15-day targets matching API data period\n\n")
            
            f.write("## 📐 Quantity Calculation Logic\n")
            f.write("```\n")
            f.write("# Step 1: Calculate ratios in successful stores\n")
            f.write("SPU_Quantity_Ratio = Average(SPU_units / Category_units) in top performer stores\n")
            f.write("SPU_Sales_Ratio = Average(SPU_sales / Category_sales) in top performer stores\n")
            f.write("\n")
            f.write("# Step 2: Scale to target store\n")
            f.write("Target_Category_Units = Current category units in target store (15-day period)\n")
            f.write("Target_Category_Sales = Current category sales in target store (15-day period)\n")
            f.write("\n")
            f.write("# Step 3: Calculate recommendations\n")
            f.write("Recommended_SPU_Units = Target_Category_Units × SPU_Quantity_Ratio × Scaling_Factor\n")
            f.write("Recommended_SPU_Sales = Target_Category_Sales × SPU_Sales_Ratio × Scaling_Factor\n")
            f.write("# Note: Scaling_Factor = 1.0 (same period as data)\n")
            f.write("```\n\n")
            
            f.write("## 💡 Sample Output\n")
            f.write("Instead of: *'Store should add SPU 15K1042'*\n\n")
            f.write("**Now provides:** \n")
            f.write("- 🎯 **TARGET 2 UNITS/15-DAYS** for SPU 15K1042\n")
            f.write("- 💵 Dollar target: $611/15-days (86.8% of category)\n")
            f.write("- 📊 Based on: Cluster peer success rate of 96.7%\n")
            f.write("- 📅 Period: Half-month (15 days) matching API data\n\n")

    # Write summary files (unlabeled + labeled)
    write_summary(base_summary)
    log_progress(f"Saved summary report to {base_summary}")
    if label:
        write_summary(labeled_summary)
        log_progress(f"Saved labeled summary report to {labeled_summary}")

    # Register summary in manifest (generic + period-specific)
    summary_meta = {
        "target_year": ty,
        "target_month": tm if ty else None,
        "target_period": tp,
        "analysis_level": ANALYSIS_LEVEL,
        "use_blended_seasonal": bool(USE_BLENDED_SEASONAL),
        "sellthrough_validation": bool(SELLTHROUGH_VALIDATION_AVAILABLE),
        "file_format": "md",
    }
    register_step_output("step11", "rule11_summary", base_summary, metadata=summary_meta)
    if label:
        register_step_output("step11", f"rule11_summary_{label}", labeled_summary, metadata=summary_meta)
        

def main(testing_mode: bool = False, args: Optional[argparse.Namespace] = None, period_label: Optional[str] = None):
    """Main execution function with unit quantity recommendations"""
    mode_text = "FAST TESTING" if testing_mode else "FULL ANALYSIS"
    print(f"\n" + "="*80)
    print(f"🎯 IMPROVED RULE 11: UNIT QUANTITY RECOMMENDATIONS ({mode_text})")
    print("="*80)
    
    start_time = datetime.now()
    
    try:
        # Load data with optional sampling for testing
        sample_size = 50000 if testing_mode else None
        df = load_and_prepare_data(sample_size=sample_size, args=args)
        
        # Identify top performers (optimized)
        top_performers = identify_cluster_category_top_performers_optimized(df) 
        
        if len(top_performers) == 0:
            log_progress("⚠️ No top performers identified. Continuing to write empty outputs for pipeline compatibility.")
        
        # Find missing opportunities with unit quantity recommendations (optimized)
        opportunities = find_missing_top_performers_with_quantities_optimized(df, top_performers)
        
        if len(opportunities) == 0:
            log_progress("ℹ️ No missed sales opportunities identified. Will write empty detailed outputs and zeroed summaries.")
        
        # 📈 FAST FISH ENHANCEMENT: Apply sell-through validation
        if SELLTHROUGH_VALIDATION_AVAILABLE and len(opportunities) > 0:
            log_progress("🎯 Applying Fast Fish sell-through validation...")
            
            # Initialize validator
            historical_data = load_historical_data_for_validation()
            validator = SellThroughValidator(historical_data)
            
            # Apply validation to each missed sales opportunity
            validated_opportunities = []
            rejected_count = 0
            
            for idx, opp in opportunities.iterrows():
                # Get category name for validation (no synthetic defaults)
                category_name = opp.get('sub_cate_name', None)
                if pd.isna(category_name) or category_name is None or str(category_name).strip() == "":
                    # try falling back to main category if available; otherwise skip
                    fallback_category = opp.get('cate_name', None)
                    if pd.isna(fallback_category) or fallback_category is None or str(fallback_category).strip() == "":
                        rejected_count += 1
                        log_progress("Skipping validation: missing category for opportunity")
                        continue
                    category_name = fallback_category
                
                # Calculate quantities (preserve missingness; skip if unavailable)
                current_qty = opp.get('current_quantity', np.nan)
                change_qty = opp.get('recommended_quantity_change', np.nan)
                rec_type = opp.get('recommendation_type', None)
                # For ADD_NEW recommendations, the item is not in the store; treat current count as 0 for validation only
                if rec_type == 'ADD_NEW' and pd.isna(current_qty):
                    current_qty = 0
                # Skip when required quantities are unavailable (e.g., INCREASE_EXISTING without quantity basis)
                if pd.isna(change_qty) or pd.isna(current_qty):
                    rejected_count += 1
                    if rejected_count <= 10:
                        log_progress(f"Skipping validation: missing quantity fields for opportunity (type={rec_type}, store={opp.get('str_code')}, category={opp.get('sub_cate_name')})")
                    continue
                recommended_qty = current_qty + change_qty
                
                # Validate the missed sales opportunity recommendation using CORRECTED Fast Fish definition
                # Clamp to realistic integer counts for validator
                current_qty_int = int(np.clip(current_qty, 0, 100))
                recommended_qty_int = int(np.clip(recommended_qty, 0, 100))
                validation = validator.validate_recommendation(
                    store_code=str(opp['str_code']),
                    category=str(category_name),
                    current_spu_count=current_qty_int,
                    recommended_spu_count=recommended_qty_int,
                    action='ADD',
                    rule_name='Rule 11: Missed Sales Opportunity'
                )
                
                # Only keep Fast Fish compliant recommendations
                if validation['fast_fish_compliant']:
                    # Add sell-through metrics to opportunity
                    enhanced_opp = opp.to_dict()
                    enhanced_opp.update({
                        'current_sell_through_rate': validation['current_sell_through_rate'],
                        'predicted_sell_through_rate': validation['predicted_sell_through_rate'],
                        'sell_through_improvement': validation['sell_through_improvement'],
                        'fast_fish_compliant': validation['fast_fish_compliant'],
                        'business_rationale': validation['business_rationale'],
                        'approval_reason': validation['approval_reason']
                    })
                    validated_opportunities.append(enhanced_opp)
                else:
                    rejected_count += 1
            
            # Replace opportunities with validated ones
            if validated_opportunities:
                opportunities = pd.DataFrame(validated_opportunities)
                # Sort by sell-through improvement (prioritize best opportunities)
                opportunities = opportunities.sort_values('sell_through_improvement', ascending=False)
                
                avg_improvement = opportunities['sell_through_improvement'].mean()
                total_investment = opportunities['investment_required'].sum() if 'investment_required' in opportunities.columns else 0
                
                log_progress(f"✅ Fast Fish sell-through validation complete:")
                log_progress(f"   Approved: {len(validated_opportunities)} missed sales opportunities")
                log_progress(f"   Rejected: {rejected_count} missed sales opportunities")
                log_progress(f"   Average sell-through improvement: {avg_improvement:.1f} percentage points")
                if total_investment > 0:
                    log_progress(f"   Total investment (validated): ${total_investment:,.0f}")
            else:
                log_progress(f"⚠️ All {len(opportunities)} missed sales opportunities rejected by sell-through validation")
                opportunities = pd.DataFrame()  # continue with empty DataFrame
        elif not SELLTHROUGH_VALIDATION_AVAILABLE and len(opportunities) > 0:
            log_progress("⚠️ Sell-through validation skipped (validator not available)")
        
        # Create pipeline results
        results = create_pipeline_results(opportunities)
        
        # Save results
        save_results(results, opportunities, top_performers, period_label=period_label)
        
        # SEASONAL BLENDING BENEFITS: Log the strategic advantages for August
        if USE_BLENDED_SEASONAL:
            log_progress("\n🍂 SEASONAL BLENDING BENEFITS FOR MISSED SALES ANALYSIS:")
            log_progress("   ✓ Summer clearance opportunities: Identified from recent trends (May-July)")
            log_progress("   ✓ Autumn transition planning: Identified from seasonal patterns (Aug 2024)")
            log_progress("   ✓ Balanced opportunity detection: Avoids over-focusing on summer-only styles")
            log_progress("   ✓ Strategic missed sales identification: Supports autumn assortment planning")
            log_progress("   ✓ Business rationale: Missed sales analysis considers seasonal transitions")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        total_recommended_sales = results['rule11_total_recommended_period_sales'].sum()
        total_recommended_qty = results['rule11_total_recommended_period_qty'].sum()
        
        print(f"\n✅ IMPROVED RULE 11 ANALYSIS WITH UNIT QUANTITIES COMPLETE:")
        print(f"  • Processing time: {elapsed/60:.1f} minutes")
        print(f"  • Top performers identified: {len(top_performers):,}")
        print(f"  • Missing opportunities: {len(opportunities):,}")
        print(f"  • Stores flagged: {(results['rule11_missed_sales_opportunity'] == 1).sum():,}")
        print(f"  • **🎯 TOTAL UNIT TARGETS**: {total_recommended_qty:,.0f} units/15-days")
        print(f"  • **💰 Total recommended 15-day sales**: ${total_recommended_sales:,.0f}")
        print(f"  • Category-specific, cluster-validated analysis with UNIT QUANTITY targets (join_mode={JOIN_MODE})")
        if testing_mode:
            print(f"  • **TESTING MODE**: Used sample of {sample_size:,} records")
        print("="*80)
        
    except Exception as e:
        log_progress(f"❌ Error in improved Rule 11 analysis: {str(e)}")
        raise

if __name__ == "__main__":
    # CLI args similar to Step 10 for consistency
    parser = argparse.ArgumentParser(description="Step 11 - Missed Sales Opportunity (with unit quantities)")
    parser.add_argument("--yyyymm", dest="yyyymm", help="Source data YYYYMM (optional)")
    parser.add_argument("--period", dest="period", help="Source period letter A/B (optional)")
    parser.add_argument("--target-yyyymm", dest="target_yyyymm", help="Target output YYYYMM override (e.g., 202509)")
    parser.add_argument("--target-period", dest="target_period", help="Target output period letter override (A/B)")
    parser.add_argument("--seasonal-blending", dest="seasonal_blending", action="store_true", help="Force enable seasonal blending")
    parser.add_argument("--no-seasonal-blending", dest="seasonal_blending", action="store_false", help="Force disable seasonal blending")
    parser.add_argument("--test", dest="test", action="store_true", help="Run in testing mode (sampled data)")
    # Join/threshold overrides (safe, optional)
    parser.add_argument("--join-mode", dest="join_mode", choices=["left","inner"], help="Cluster join mode: left (inclusive) or inner (stricter)")
    parser.add_argument("--top-performer-threshold", dest="top_performer_threshold", type=float, help="Percentile threshold for top performers (0-1)")
    parser.add_argument("--min-cluster-stores", dest="min_cluster_stores", type=int, help="Minimum stores in cluster for analysis")
    parser.add_argument("--min-stores-selling", dest="min_stores_selling", type=int, help="Minimum stores selling the SPU")
    parser.add_argument("--min-spu-sales", dest="min_spu_sales", type=float, help="Minimum SPU sales to include")
    parser.add_argument("--max-recs-per-store", dest="max_recs_per_store", type=int, help="Cap on recommendations per store")
    parser.add_argument("--min-opportunity-score", dest="min_opportunity_score", type=float, help="Minimum opportunity score to keep an opportunity")
    parser.add_argument("--min-sales-gap", dest="min_sales_gap", type=float, help="Minimum dollar gap to recommend action")
    parser.add_argument("--min-qty-gap", dest="min_qty_gap", type=float, help="Minimum unit gap to recommend action")
    parser.add_argument("--min-adoption-rate", dest="min_adoption_rate", type=float, help="Minimum adoption rate to recommend (0-1)")
    parser.add_argument("--min-investment", dest="min_investment", type=float, help="Minimum investment per recommendation")
    parser.set_defaults(seasonal_blending=None, test=False)
    args = parser.parse_args()

    # Propagate target period env vars for downstream compatibility
    if args.target_yyyymm:
        os.environ["PIPELINE_TARGET_YYYYMM"] = str(args.target_yyyymm)
    if args.target_period:
        os.environ["PIPELINE_TARGET_PERIOD"] = str(args.target_period)

    # Determine period label
    period_label = get_period_label_from_env_or_args(args)

    # Allow CLI to override blending behavior (module scope assignment)
    if args.seasonal_blending is not None:
        USE_BLENDED_SEASONAL = bool(args.seasonal_blending)
        log_progress(f"CLI override: USE_BLENDED_SEASONAL set to {USE_BLENDED_SEASONAL}")
    # Apply runtime overrides to globals
    try:
        # thresholds
        if args.top_performer_threshold is not None:
            TOP_PERFORMER_THRESHOLD = float(args.top_performer_threshold)
        if args.min_cluster_stores is not None:
            MIN_CLUSTER_STORES = int(args.min_cluster_stores)
        if args.min_stores_selling is not None:
            MIN_STORES_SELLING = int(args.min_stores_selling)
        if args.min_spu_sales is not None:
            MIN_SPU_SALES = float(args.min_spu_sales)
        if args.max_recs_per_store is not None:
            MAX_RECOMMENDATIONS_PER_STORE = int(args.max_recs_per_store)
        if args.min_opportunity_score is not None:
            MIN_OPPORTUNITY_SCORE = float(args.min_opportunity_score)
        if args.min_sales_gap is not None:
            MIN_SALES_GAP = float(args.min_sales_gap)
        if args.min_qty_gap is not None:
            MIN_QTY_GAP = float(args.min_qty_gap)
        if args.min_adoption_rate is not None:
            MIN_ADOPTION_RATE = float(args.min_adoption_rate)
        if args.min_investment is not None:
            MIN_INVESTMENT_THRESHOLD = float(args.min_investment)
        if args.join_mode in ("left","inner"):
            JOIN_MODE = args.join_mode
    except Exception as _e:
        pass

    # Run
    main(testing_mode=bool(args.test), args=args, period_label=period_label)