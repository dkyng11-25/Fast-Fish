#!/usr/bin/env python3
"""
Step 8: Imbalanced Allocation Rule with QUANTITY REBALANCING RECOMMENDATIONS

This step identifies stores with imbalanced style allocations using Z-Score analysis
and provides specific UNIT QUANTITY rebalancing recommendations.

ENHANCEMENT: Now includes actual unit quantity rebalancing using real sales data!

Key Features:
- Subcategory-level allocation analysis (traditional approach)
- SPU-level allocation analysis (granular approach)
- 🎯 UNIT QUANTITY REBALANCING (e.g., "Move 3 units from SPU A to SPU B")
- Real sales data integration for accurate quantity calculations
- Z-Score based statistical analysis
- Cluster-aware imbalance detection
- Configurable thresholds and parameters
- Investment-neutral rebalancing (no additional cost)

Author: Data Pipeline
Date: 2025-01-02 (Enhanced with Quantity Rebalancing)
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
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import warnings
from tqdm import tqdm
import time
import gc
import argparse

# Centralized configuration
from src.config import (
    initialize_pipeline_config,
    get_current_period,
    get_period_label,
    get_output_files,
    get_api_data_files,
    OUTPUT_DIR,
)
from src.pipeline_manifest import register_step_output, get_step_input
from src.output_utils import create_output_with_symlinks

# FAST FISH ENHANCEMENT: Import sell-through validation
try:
    from .sell_through_validator import SellThroughValidator, load_historical_data_for_validation
    SELLTHROUGH_VALIDATION_AVAILABLE = True
    print("✅ Fast Fish sell-through validation: ENABLED")
except ImportError:
    SELLTHROUGH_VALIDATION_AVAILABLE = False
    print("⚠️ Fast Fish sell-through validation: DISABLED (validator not found)")

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# Configuration - Analysis Level Selection
# ANALYSIS_LEVEL = "subcategory"  # Options: "subcategory", "spu"
ANALYSIS_LEVEL = "spu"  # Default to SPU-level analysis

# Allow environment override to switch without code edits
_env_level = os.environ.get("ANALYSIS_LEVEL")
if _env_level in {"subcategory", "spu"}:
    ANALYSIS_LEVEL = _env_level

# DATA PERIOD CONFIGURATION - CRITICAL FOR ACCURATE RECOMMENDATIONS
DATA_PERIOD_DAYS = 15  # API data is for half month (15 days)
TARGET_PERIOD_DAYS = 15  # Recommendations should be for same period (15 days)
SCALING_FACTOR = TARGET_PERIOD_DAYS / DATA_PERIOD_DAYS  # 1.0 for same period

# Analysis configurations
ANALYSIS_CONFIGS = {
    "subcategory": {
        "cluster_file": "output/clustering_results_subcategory.csv",
        "description": "Subcategory-Level Imbalanced Allocation Analysis",
        "output_prefix": "rule8_imbalanced_subcategory",
        "grouping_columns": ['season_name', 'sex_name', 'display_location_name', 'big_class_name', 'sub_cate_name'],
        "feature_name": "subcategory"
    },
    "spu": {
        "cluster_file": "output/clustering_results_spu.csv",
        "description": "SPU-Level Imbalanced Allocation Analysis", 
        "output_prefix": "rule8_imbalanced_spu",
        "grouping_columns": ['season_name', 'sex_name', 'display_location_name', 'big_class_name', 'sub_cate_name', 'sty_code'],
        "feature_name": "SPU"
    }
}

# Get current analysis configuration
CURRENT_CONFIG = ANALYSIS_CONFIGS[ANALYSIS_LEVEL]

# File paths based on analysis level
CLUSTER_RESULTS_FILE = CURRENT_CONFIG["cluster_file"]

# SEASONAL BLENDING ENHANCEMENT: Dynamic data loading for seasonal transitions
# For August recommendations, blend recent trends with seasonal patterns
from datetime import datetime
current_month = datetime.now().month

def log_progress(message: str) -> None:
    """
    Log progress with timestamp.
    
    Args:
        message (str): Progress message to log
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

if current_month == 8:  # August - use blended seasonal approach
    log_progress("🍂 AUGUST DETECTED: Using blended seasonal data approach")
    log_progress("   Combining recent trends (current period) + seasonal patterns (same month prior years)")
    # Seasonal files resolved inside load_data() using period-aware helpers (no combined fallbacks)
    SEASONAL_PLANNING_FILE = None
    SEASONAL_QUANTITY_FILE = None
    USE_BLENDED_SEASONAL = True
else:
    # Standard approach for other months
    USE_BLENDED_SEASONAL = False
RESULTS_FILE = f"output/{CURRENT_CONFIG['output_prefix']}_results.csv"  # Back-compat; not used when period label is applied

# Rule parameters - adaptive based on analysis level
if ANALYSIS_LEVEL == "subcategory":
    Z_SCORE_THRESHOLD = 2.0  # Z-Score threshold for imbalance detection
    MIN_CLUSTER_SIZE = 3     # Minimum stores in cluster for valid Z-Score calculation
    MIN_ALLOCATION_THRESHOLD = 0.1  # Minimum allocation to consider for analysis
    # QUANTITY THRESHOLDS for subcategory rebalancing
    MIN_REBALANCE_QUANTITY = 2.0  # Minimum units to recommend rebalancing
    MAX_REBALANCE_PERCENTAGE = 0.3  # Max 30% of current allocation to rebalance
else:  # SPU level - SANITY ADJUSTED FOR ULTRA-SELECTIVE RECOMMENDATIONS
    Z_SCORE_THRESHOLD = 3.0  # Reduced from 5.0 (more moderate outliers - top 10-15%)
    MIN_CLUSTER_SIZE = 5     # Reduced from 8 for more opportunities
    MIN_ALLOCATION_THRESHOLD = 0.05   # Reduced threshold for more inclusivity
    # QUANTITY THRESHOLDS for SPU rebalancing - MORE ACCESSIBLE
    MIN_REBALANCE_QUANTITY = 5.0  # Reduced from 10.0 for smaller meaningful changes
    MAX_TOTAL_ADJUSTMENTS_PER_STORE = None  # No artificial cap by default; can be limited via CLI
    MAX_REBALANCE_PERCENTAGE = 0.5  # Increased to 50% for more flexibility

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Rebalancing strategy: 'increase_only' (suppress reductions) or 'paired' (future enhancement)
REDISTRIBUTION_STRATEGY = os.environ.get("REBALANCE_MODE", "increase_only")

# Output controls for heavy artifacts
# Limit the number of rows saved in z_score_analysis (None means save all)
# Or skip writing the z_score_analysis entirely (write minimal headers)
ZSCORE_OUTPUT_LIMIT: Optional[int] = None
SKIP_ZSCORE_OUTPUT: bool = False

# Recent-period averaging and seasonal controls (overridden by CLI)
RECENT_MONTHS_BACK: int = 0  # 0 = disabled
USE_SEASONAL_BLENDING: bool = False  # explicit toggle; falls back to August auto
SEASONAL_WEIGHT_OVERRIDE: Optional[float] = None
SEASONAL_YEARS_BACK_OVERRIDE: Optional[int] = None

# Force anchor for recent averaging (explicit base period from CLI)
BASE_AVG_YYYMM: Optional[str] = None
BASE_AVG_PERIOD: Optional[str] = None

def blend_seasonal_data(recent_df: pd.DataFrame, seasonal_df: pd.DataFrame, 
                       recent_weight: float, seasonal_weight: float, data_type: str) -> pd.DataFrame:
    """
    Blend recent trends data with seasonal patterns using weighted aggregation.
    
    Args:
        recent_df: Recent trends data (May-July 2025)
        seasonal_df: Seasonal patterns data (August 2024)
        recent_weight: Weight for recent data (e.g., 0.4 = 40%)
        seasonal_weight: Weight for seasonal data (e.g., 0.6 = 60%)
        data_type: Type of data being blended ("planning" or "quantity")
        
    Returns:
        Blended DataFrame with weighted aggregation
    """
    log_progress(f"🔄 Blending {data_type} data: {recent_weight:.0%} recent + {seasonal_weight:.0%} seasonal")
    
    # Identify common columns for blending
    if data_type == "planning":
        # For planning data, blend on store and category dimensions
        blend_cols = ['str_code', 'season_name', 'sex_name', 'display_location_name', 'big_class_name', 'sub_cate_name']
        value_cols = ['target_sty_cnt_avg', 'sty_sal_amt']  # Columns to blend
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
    
    # Prepare recent data with weights
    recent_clean = recent_df[available_blend_cols + available_value_cols].copy()
    for col in available_value_cols:
        recent_clean[col] = pd.to_numeric(recent_clean[col], errors='coerce') * recent_weight
    
    # Prepare seasonal data with weights
    seasonal_clean = seasonal_df[available_blend_cols + available_value_cols].copy()
    for col in available_value_cols:
        seasonal_clean[col] = pd.to_numeric(seasonal_clean[col], errors='coerce') * seasonal_weight
    
    # Missingness diagnostics after coercion (preserve NA)
    recent_na = {c: int(recent_clean[c].isna().sum()) for c in available_value_cols}
    seasonal_na = {c: int(seasonal_clean[c].isna().sum()) for c in available_value_cols}
    log_progress("   NA (recent): " + ", ".join([f"{k}={v:,}" for k, v in recent_na.items()]))
    log_progress("   NA (seasonal): " + ", ".join([f"{k}={v:,}" for k, v in seasonal_na.items()]))
    
    # Combine and aggregate
    combined = pd.concat([recent_clean, seasonal_clean], ignore_index=True)
    
    # Group by blend columns and sum the weighted values
    agg_dict = {col: (lambda s: s.sum(min_count=1)) for col in available_value_cols}
    blended = combined.groupby(available_blend_cols).agg(agg_dict).reset_index()
    
    # Add back any additional columns from recent data that weren't blended
    additional_cols = [col for col in recent_df.columns if col not in available_blend_cols + available_value_cols]
    if additional_cols:
        recent_extra = recent_df[available_blend_cols + additional_cols].drop_duplicates(subset=available_blend_cols)
        blended = blended.merge(recent_extra, on=available_blend_cols, how='left')
    
    log_progress(f"   ✅ Blended {len(blended):,} records from {len(recent_df):,} recent + {len(seasonal_df):,} seasonal")
    
    return blended

def _previous_half_month(yyyymm: str, period: str) -> Tuple[str, str]:
    """
    Given a YYYYMM and half-month period 'A' or 'B', return the previous half-month.
    Example: (202508, 'A') -> (202507, 'B'); (202501, 'A') -> (202412, 'B')
    """
    y = int(str(yyyymm)[:4])
    m = int(str(yyyymm)[4:6])
    if period == 'B':
        return f"{y}{m:02d}", 'A'
    # period == 'A' => go to previous month B
    m -= 1
    if m == 0:
        y -= 1
        m = 12
    return f"{y}{m:02d}", 'B'

def _load_api_planning_quantity(yyyymm: str, period: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    files = get_api_data_files(yyyymm, period)
    plan = files.get('store_config')
    qty = files.get('spu_sales')
    if not plan or not os.path.exists(plan):
        raise FileNotFoundError(f"Planning data not found for {yyyymm}{period}: {plan}")
    if not qty or not os.path.exists(qty):
        raise FileNotFoundError(f"Quantity data not found for {yyyymm}{period}: {qty}")
    planning_df = pd.read_csv(plan, dtype={'str_code': str}, low_memory=False)
    quantity_df = pd.read_csv(qty, dtype={'str_code': str}, low_memory=False)
    return planning_df, quantity_df

def _average_recent_panels(base_yyyymm: str, base_period: str, n_back: int) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """
    Build averaged planning and quantity panels over the last n_back half-month periods,
    including the base period as the most recent. Uses equal weights.
    Returns the averaged planning_df, quantity_df, and the list of period labels used.
    """
    periods: List[Tuple[str, str]] = []
    yyyymm, period = base_yyyymm, base_period
    periods.append((yyyymm, period))
    for _ in range(max(0, n_back - 1)):
        yyyymm, period = _previous_half_month(yyyymm, period)
        periods.append((yyyymm, period))
    used_labels = [f"{ym}{p}" for (ym, p) in periods]
    log_progress(f"📊 Averaging recent panels over {len(periods)} half-months: {used_labels}")

    # Collect frames
    planning_frames: List[pd.DataFrame] = []
    quantity_frames: List[pd.DataFrame] = []
    for (ym, p) in periods:
        try:
            plan_df, qty_df = _load_api_planning_quantity(ym, p)
            planning_frames.append(plan_df)
            quantity_frames.append(qty_df)
        except Exception as e:
            log_progress(f"⚠️ Skipping {ym}{p}: {e}")

    if not planning_frames or not quantity_frames:
        raise FileNotFoundError("No recent frames could be loaded for averaging")

    # Averaging strategy
    # Planning: average target_sty_cnt_avg and sty_sal_amt by store/category dims
    p_concat = []
    for df in planning_frames:
        df2 = df.copy()
        # keep only columns we can aggregate reliably
        keep_cols = [c for c in ['str_code','season_name','sex_name','display_location_name','big_class_name','sub_cate_name','target_sty_cnt_avg','sty_sal_amt'] if c in df2.columns]
        df2 = df2[keep_cols]
        p_concat.append(df2)
    p_all = pd.concat(p_concat, ignore_index=True)
    p_group_cols = [c for c in ['str_code','season_name','sex_name','display_location_name','big_class_name','sub_cate_name'] if c in p_all.columns]
    p_val_cols = [c for c in ['target_sty_cnt_avg','sty_sal_amt'] if c in p_all.columns]
    # Coerce planning numeric fields to numeric to avoid object-dtype mean errors
    for col in p_val_cols:
        if col in p_all.columns:
            p_all[col] = pd.to_numeric(p_all[col], errors='coerce')
    p_agg = p_all.groupby(p_group_cols)[p_val_cols].mean().reset_index() if p_group_cols and p_val_cols else planning_frames[0]

    # Quantity: average by (str_code, spu_code), sum numeric then divide by N
    q_concat = []
    for df in quantity_frames:
        df2 = df.copy()
        keep_cols = [c for c in ['str_code','spu_code','spu_sales_amt','quantity','sub_cate_name','season_name','sex_name','display_location_name','big_class_name'] if c in df2.columns]
        df2 = df2[keep_cols]
        q_concat.append(df2)
    q_all = pd.concat(q_concat, ignore_index=True)
    # ensure numeric types
    for col in ['spu_sales_amt','quantity']:
        if col in q_all.columns:
            q_all[col] = pd.to_numeric(q_all[col], errors='coerce')
    q_group_cols = [c for c in ['str_code','spu_code'] if c in q_all.columns]
    if q_group_cols:
        agg_dict = {}
        if 'spu_sales_amt' in q_all.columns:
            agg_dict['spu_sales_amt'] = 'sum'
        if 'quantity' in q_all.columns:
            agg_dict['quantity'] = 'sum'
        q_agg = q_all.groupby(q_group_cols).agg(agg_dict).reset_index()
        n_periods = len(planning_frames)  # same count for averaging
        for col in ['spu_sales_amt','quantity']:
            if col in q_agg.columns and n_periods > 0:
                q_agg[col] = q_agg[col] / n_periods
        # Recover optional category dims from the most recent quantity frame (left merge on keys)
        recent_q = quantity_frames[0]
        extra_cols = [c for c in ['sub_cate_name','season_name','sex_name','display_location_name','big_class_name'] if c in recent_q.columns]
        if extra_cols:
            recent_q_small = recent_q[q_group_cols + extra_cols].drop_duplicates(q_group_cols)
            q_agg = q_agg.merge(recent_q_small, on=q_group_cols, how='left')
    else:
        q_agg = quantity_frames[0]

    log_progress(f"✅ Averaged panels: planning={len(p_agg):,} rows, quantity={len(q_agg):,} rows")
    return p_agg, q_agg, used_labels

def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load clustering results, planning data, and quantity data for rebalancing analysis.
    Enhanced with blended seasonal data loading for August recommendations.
    
    Returns:
        Tuple containing cluster assignments, planning data, and quantity data
    """
    try:
        log_progress(f"Loading data for {CURRENT_CONFIG['description']} with quantity rebalancing...")

        # Resolve base period strictly from CLI anchor for averaging
        if BASE_AVG_YYYMM and BASE_AVG_PERIOD:
            yyyymm, period = BASE_AVG_YYYMM, BASE_AVG_PERIOD
        else:
            yyyymm, period = get_current_period()
        period_label = get_period_label(yyyymm, period)

        # Resolve clustering results dynamically with fallbacks
        cluster_candidates: List[str] = []
        try:
            cfg_out = get_output_files(ANALYSIS_LEVEL, yyyymm, period)
            cluster_candidates.append(cfg_out['clustering_results'])
        except Exception:
            pass
        # Original defaults
        cluster_candidates.extend([
            CLUSTER_RESULTS_FILE,
            "output/clustering_results.csv",
        ])
        # Step 7 precedent: if subcategory clusters are absent, fall back to SPU clusters
        if ANALYSIS_LEVEL == "subcategory":
            cluster_candidates.append("output/clustering_results_spu.csv")
        CLUSTER_RESULTS_FILE_ACTUAL = next((p for p in cluster_candidates if p and os.path.exists(p)), None)
        if not CLUSTER_RESULTS_FILE_ACTUAL:
            raise FileNotFoundError(
                f"Clustering results not found in candidates: {cluster_candidates}"
            )
        log_progress(f"Using clustering results: {CLUSTER_RESULTS_FILE_ACTUAL}")

        # Determine base recent panels
        if RECENT_MONTHS_BACK and RECENT_MONTHS_BACK > 0:
            planning_df_recent, quantity_df_recent, used = _average_recent_panels(yyyymm, period, RECENT_MONTHS_BACK)
            log_progress(f"Using averaged recent panels across: {used}")
        else:
            # Single-period fallback
            api_files = get_api_data_files(yyyymm, period)
            planning_path = api_files.get('store_config')
            quantity_path = api_files.get('spu_sales')
            planning_candidates = [planning_path]
            quantity_candidates = [quantity_path]
            planning_path = next((p for p in planning_candidates if p and os.path.exists(p)), None)
            quantity_path = next((p for p in quantity_candidates if p and os.path.exists(p)), None)
            if not planning_path:
                raise FileNotFoundError(f"Planning data not found in: {planning_candidates}")
            if not quantity_path:
                raise FileNotFoundError(f"Quantity data not found in: {quantity_candidates}")
            log_progress(f"Loading recent trends from {planning_path} and {quantity_path}")
            planning_df_recent = pd.read_csv(planning_path, dtype={'str_code': str}, low_memory=False)
            quantity_df_recent = pd.read_csv(quantity_path, dtype={'str_code': str}, low_memory=False)

        # Load cluster assignments
        cluster_df = pd.read_csv(CLUSTER_RESULTS_FILE_ACTUAL, dtype={'str_code': str})
        log_progress(f"Loaded cluster assignments for {len(cluster_df)} stores")
        # Normalize cluster column names for downstream compatibility
        if 'Cluster' not in cluster_df.columns and 'cluster_id' in cluster_df.columns:
            cluster_df['Cluster'] = cluster_df['cluster_id']
            log_progress("Detected 'cluster_id' without 'Cluster'; created 'Cluster' for compatibility")
        if 'cluster_id' not in cluster_df.columns and 'Cluster' in cluster_df.columns:
            cluster_df['cluster_id'] = cluster_df['Cluster']
            log_progress("Detected 'Cluster' without 'cluster_id'; created 'cluster_id' for standardized outputs")
        
        # SEASONAL BLENDING: Explicit toggle OR August auto
        seasonal_active = USE_SEASONAL_BLENDING or USE_BLENDED_SEASONAL
        if seasonal_active:
            log_progress("🍂 BLENDED SEASONAL LOADING: Combining recent trends + seasonal patterns")
            recent_planning = planning_df_recent
            recent_quantity = quantity_df_recent
            log_progress(f"Recent trends: {len(recent_planning)} planning + {len(recent_quantity)} quantity records")
            
            # Resolve seasonal periods from environment (period-aware), support multi-year blending
            import math
            seasonal_yyyymm_env = os.environ.get("SEASONAL_YYYYMM")
            seasonal_period_env = os.environ.get("SEASONAL_PERIOD")
            seasonal_weight_env = os.environ.get("SEASONAL_WEIGHT")
            years_back_env = os.environ.get("SEASONAL_YEARS_BACK")

            # Allow CLI overrides
            seasonal_weight_total = (
                SEASONAL_WEIGHT_OVERRIDE if SEASONAL_WEIGHT_OVERRIDE is not None
                else float(seasonal_weight_env) if seasonal_weight_env else 0.6
            )
            recent_weight = 1.0 - seasonal_weight_total
            years_back = (
                SEASONAL_YEARS_BACK_OVERRIDE if SEASONAL_YEARS_BACK_OVERRIDE is not None
                else int(years_back_env) if years_back_env and years_back_env.isdigit() else 2
            )
            if years_back < 1:
                years_back = 1

            # Default seasonal to same month last year with same period if not provided
            base_year = int(str(yyyymm)[:4])
            base_month = int(str(yyyymm)[4:6])
            base_period = period
            target_period_for_seasonal = (seasonal_period_env or base_period)

            seasonal_frames_planning: List[pd.DataFrame] = []
            seasonal_frames_quantity: List[pd.DataFrame] = []
            added_labels: List[str] = []

            for i in range(1, years_back + 1):
                y = base_year - i
                yyyymm_i = f"{y}{base_month:02d}"
                if seasonal_yyyymm_env and i == 1:
                    yyyymm_i = seasonal_yyyymm_env  # allow override for first year
                try:
                    files_i = get_api_data_files(yyyymm_i, target_period_for_seasonal)
                    plan_i = files_i.get('store_config')
                    qty_i = files_i.get('spu_sales')
                    if plan_i and os.path.exists(plan_i) and qty_i and os.path.exists(qty_i):
                        seasonal_frames_planning.append(pd.read_csv(plan_i, dtype={'str_code': str}, low_memory=False))
                        seasonal_frames_quantity.append(pd.read_csv(qty_i, dtype={'str_code': str}, low_memory=False))
                        added_labels.append(f"{yyyymm_i}{target_period_for_seasonal}")
                except Exception:
                    continue

            if seasonal_frames_planning and seasonal_frames_quantity:
                per_year_weight = seasonal_weight_total / max(1, len(seasonal_frames_planning))
                log_progress(
                    f"🔄 BLENDING: {recent_weight:.0%} recent + {seasonal_weight_total:.0%} seasonal across {len(seasonal_frames_planning)} year(s): {added_labels}"
                )
                # Start with scaled recent data
                planning_df = recent_planning.copy()
                quantity_df = recent_quantity.copy()
                for dfp in seasonal_frames_planning:
                    planning_df = blend_seasonal_data(planning_df, dfp, recent_weight=recent_weight, seasonal_weight=per_year_weight, data_type="planning")
                    # After first blend, treat result as new 'recent' for chaining
                    recent_weight = 1.0  # subsequent blends: keep accumulated weights stable
                # Reset weights for quantity chaining
                recent_weight_q = 1.0 - seasonal_weight_total
                for dfq in seasonal_frames_quantity:
                    quantity_df = blend_seasonal_data(quantity_df, dfq, recent_weight=recent_weight_q, seasonal_weight=per_year_weight, data_type="quantity")
                    recent_weight_q = 1.0
                log_progress(f"✅ BLENDED RESULT: {len(planning_df)} planning + {len(quantity_df)} quantity records")
            else:
                log_progress("⚠️ FALLBACK: Seasonal period files not found; using recent data only")
                planning_df = recent_planning
                quantity_df = recent_quantity
        else:
            # Use recent panels without seasonal blending
            planning_df = planning_df_recent
            quantity_df = quantity_df_recent
            log_progress(f"Using recent panels without seasonal blending: planning={len(planning_df):,}, quantity={len(quantity_df):,}")

        # ===== REAL QUANTITY DERIVATION (FAIL-FAST IF ABSENT) =====
        # Ensure a real 'quantity' column exists from authoritative sources
        # Priority: existing 'quantity' -> base_sal_qty + fashion_sal_qty -> sal_qty -> error
        if 'quantity' in quantity_df.columns:
            quantity_df['quantity'] = pd.to_numeric(quantity_df['quantity'], errors='coerce')
            log_progress(
                f"Using existing quantity column; NA count={int(quantity_df['quantity'].isna().sum()):,}"
            )
        else:
            base_qty = pd.to_numeric(quantity_df.get('base_sal_qty'), errors='coerce') if 'base_sal_qty' in quantity_df.columns else None
            fashion_qty = pd.to_numeric(quantity_df.get('fashion_sal_qty'), errors='coerce') if 'fashion_sal_qty' in quantity_df.columns else None
            sal_qty = pd.to_numeric(quantity_df.get('sal_qty'), errors='coerce') if 'sal_qty' in quantity_df.columns else None

            if base_qty is not None and fashion_qty is not None:
                quantity_df['quantity'] = base_qty.add(fashion_qty, fill_value=np.nan)
                log_progress(
                    f"Derived quantity from base_sal_qty + fashion_sal_qty; NA count={int(quantity_df['quantity'].isna().sum()):,}"
                )
            elif sal_qty is not None:
                quantity_df['quantity'] = sal_qty
                log_progress(
                    f"Derived quantity from sal_qty; NA count={int(quantity_df['quantity'].isna().sum()):,}"
                )
            else:
                raise ValueError(
                    "Missing real quantity fields in quantity data. Expected quantity or base_sal_qty+fashion_sal_qty or sal_qty. "
                    f"File: {quantity_path} | Period: {period_label}"
                )

        # Basic diagnostics for key fields used later
        if 'spu_sales_amt' in quantity_df.columns:
            quantity_df['spu_sales_amt'] = pd.to_numeric(quantity_df['spu_sales_amt'], errors='coerce')
            log_progress(
                f"Quantity diagnostics: quantity_NA={int(quantity_df['quantity'].isna().sum()):,}, "
                f"spu_sales_amt_NA={int(quantity_df['spu_sales_amt'].isna().sum()):,}"
            )
        
        # Ensure str_code is string for consistent joining
        cluster_df['str_code'] = cluster_df['str_code'].astype(str)
        planning_df['str_code'] = planning_df['str_code'].astype(str)
        quantity_df['str_code'] = quantity_df['str_code'].astype(str)
        
        # Validate required columns based on analysis level
        if ANALYSIS_LEVEL == "subcategory":
            required_cols = ['str_code', 'target_sty_cnt_avg'] + CURRENT_CONFIG['grouping_columns']
        else:
            # For SPU analysis, we need sty_sal_amt and base grouping columns (sty_code will be created)
            base_grouping_cols = [col for col in CURRENT_CONFIG['grouping_columns'] if col != 'sty_code']
            required_cols = ['str_code', 'sty_sal_amt'] + base_grouping_cols
        
        missing_cols = [col for col in required_cols if col not in planning_df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in planning data: {missing_cols}")
        
        # Validate quantity data columns (updated for actual SPU sales file)
        quantity_required_cols = ['str_code', 'spu_code', 'spu_sales_amt', 'quantity']
        quantity_missing_cols = [col for col in quantity_required_cols if col not in quantity_df.columns]
        if quantity_missing_cols:
            raise ValueError(f"Missing required columns in quantity data: {quantity_missing_cols}")
        
        log_progress(f"Data validation successful for {ANALYSIS_LEVEL} analysis with quantity data")
        
        return cluster_df, planning_df, quantity_df
        
    except Exception as e:
        log_progress(f"Error loading data: {str(e)}")
        raise

def prepare_allocation_data(planning_df: pd.DataFrame, cluster_df: pd.DataFrame, quantity_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare store allocation data with cluster information and quantity data for rebalancing analysis.
    
    Args:
        planning_df: Planning data with target_sty_cnt_avg or sty_sal_amt
        cluster_df: Cluster assignments
        quantity_df: Quantity data with actual unit sales for rebalancing calculations
        
    Returns:
        DataFrame with allocation data, cluster information, and quantity metrics
    """
    feature_type = "subcategories" if ANALYSIS_LEVEL == "subcategory" else "SPUs"
    log_progress(f"Preparing {ANALYSIS_LEVEL} allocation data with quantity integration...")
    
    if ANALYSIS_LEVEL == "subcategory":
        # Use traditional planning data approach
        data_with_clusters = planning_df.merge(
            cluster_df[['str_code', 'Cluster']], on='str_code', how='left', indicator=True
        )
        left_only = int((data_with_clusters['_merge'] == 'left_only').sum())
        matched = int((data_with_clusters['_merge'] == 'both').sum())
        log_progress(
            f"Safe left merge on str_code (planning x clusters): total={len(data_with_clusters):,}, matched={matched:,}, left_only={left_only:,}"
        )
        data_with_clusters = data_with_clusters.drop(columns=['_merge'])
        
        # Clean and prepare allocation data
        data_with_clusters['target_sty_cnt_avg'] = pd.to_numeric(
            data_with_clusters['target_sty_cnt_avg'], errors='coerce'
        )
        log_progress(
            f"NA after coercion: target_sty_cnt_avg={int(data_with_clusters['target_sty_cnt_avg'].isna().sum()):,}"
        )
        data_with_clusters['allocation_value'] = data_with_clusters['target_sty_cnt_avg']
        
        # Create category key for grouping
        grouping_cols = CURRENT_CONFIG['grouping_columns']
        data_with_clusters['category_key'] = data_with_clusters[grouping_cols].apply(
            lambda x: '|'.join(x.astype(str)), axis=1
        )
        
        # QUANTITY ENHANCEMENT: Add quantity data for subcategory rebalancing
        log_progress("Integrating quantity data for subcategory rebalancing...")
        quantity_clean = quantity_df[quantity_df['quantity'].notna() & (quantity_df['quantity'] > 0)].copy()
        quantity_clean['quantity'] = pd.to_numeric(quantity_clean['quantity'], errors='coerce')
        quantity_clean['spu_sales_amt'] = pd.to_numeric(quantity_clean['spu_sales_amt'], errors='coerce')
        log_progress(
            "Quantity NA diagnostics (subcategory): "
            + f"quantity={int(quantity_clean['quantity'].isna().sum()):,}, "
            + f"spu_sales_amt={int(quantity_clean['spu_sales_amt'].isna().sum()):,}"
        )
        
        # Aggregate actual quantity by store and subcategory
        subcategory_quantity = quantity_clean.groupby(['str_code', 'sub_cate_name']).agg({
            'quantity': (lambda s: s.sum(min_count=1)),
            'spu_sales_amt': (lambda s: s.sum(min_count=1))
        }).reset_index()
        
        # Merge with allocation data
        data_with_clusters = data_with_clusters.merge(
            subcategory_quantity,
            on=['str_code', 'sub_cate_name'],
            how='left'
        )
        # Use actual quantity data (scaled to target period)
        data_with_clusters['current_quantity'] = data_with_clusters['quantity'] * SCALING_FACTOR
        data_with_clusters['current_sales_value'] = data_with_clusters['spu_sales_amt'] * SCALING_FACTOR
        log_progress(
            "Current metrics NA (subcategory): "
            + f"current_quantity={int(data_with_clusters['current_quantity'].isna().sum()):,}, "
            + f"current_sales_value={int(data_with_clusters['current_sales_value'].isna().sum()):,}"
        )
        
        # Do not threshold before Z-score; include all allocations to avoid biasing toward over-allocation only
        allocation_data = data_with_clusters.copy()
        
    else:
        # SPU analysis: Use sales data as proxy for allocation patterns
        log_progress("Expanding SPU sales data for allocation analysis with quantity integration...")
        
        # Filter records with SPU sales data
        spu_records = planning_df[planning_df['sty_sal_amt'].notna() & (planning_df['sty_sal_amt'] != '')].copy()
        log_progress(f"Found {len(spu_records)} records with SPU sales data")
        
        # QUANTITY ENHANCEMENT: Integrate quantity data directly for SPU analysis
        log_progress("Processing quantity data for SPU rebalancing...")
        # Include zero/NA sales amounts to avoid biasing toward over-allocation only; coerce numerics NA-safely
        quantity_clean = quantity_df.copy()
        quantity_clean['spu_sales_amt'] = pd.to_numeric(quantity_clean['spu_sales_amt'], errors='coerce')
        log_progress(
            f"Quantity NA diagnostics (spu): spu_sales_amt={int(quantity_clean['spu_sales_amt'].isna().sum()):,}"
        )
        
        log_progress(f"Clean quantity data: {len(quantity_clean)} records")
        
        # QUANTITY ENHANCEMENT: Use quantity data directly for SPU analysis
        log_progress("Using quantity data directly for SPU rebalancing analysis...")
        
        # Use quantity data as the primary source for SPU allocation analysis
        quantity_with_clusters = quantity_clean.merge(
            cluster_df[['str_code', 'Cluster']], on='str_code', how='left', indicator=True
        )
        left_only_q = int((quantity_with_clusters['_merge'] == 'left_only').sum())
        matched_q = int((quantity_with_clusters['_merge'] == 'both').sum())
        log_progress(
            f"Safe left merge on str_code (quantity x clusters): total={len(quantity_with_clusters):,}, matched={matched_q:,}, left_only={left_only_q:,}"
        )
        quantity_with_clusters = quantity_with_clusters.drop(columns=['_merge'])
        
        # The SPU sales data already has the category information we need
        # Map the column names to match our expected structure
        data_with_clusters = quantity_with_clusters.copy()
        
        # Add sty_code column (same as spu_code for SPU analysis)
        data_with_clusters['sty_code'] = data_with_clusters['spu_code']
        
        # Use real quantity as allocation value (scaled to target period)
        data_with_clusters['allocation_value'] = data_with_clusters['quantity'] * SCALING_FACTOR
        data_with_clusters['current_quantity'] = data_with_clusters['quantity'] * SCALING_FACTOR
        data_with_clusters['current_sales_value'] = data_with_clusters['spu_sales_amt'] * SCALING_FACTOR
        
        log_progress(f"Prepared data: {len(data_with_clusters)} records with complete information")
        
        # Create category key for grouping from available, real columns only (no synthetic defaults)
        all_candidate_cols = CURRENT_CONFIG['grouping_columns']
        available_grouping_cols = [c for c in all_candidate_cols if c in data_with_clusters.columns]

        # Minimal real fallback if none of the optional dimensions exist
        if not available_grouping_cols:
            fallback_cols = [c for c in ['sub_cate_name', 'sty_code'] if c in data_with_clusters.columns]
            available_grouping_cols = fallback_cols if fallback_cols else ['spu_code']

        data_with_clusters['category_key'] = data_with_clusters[available_grouping_cols].apply(
            lambda x: '|'.join(x.astype(str)), axis=1
        )
        
        # Only consider allocations above minimum threshold
        allocation_data = data_with_clusters[
            data_with_clusters['allocation_value'] >= MIN_ALLOCATION_THRESHOLD
        ].copy()
    
    log_progress(f"Prepared {len(allocation_data)} store-{ANALYSIS_LEVEL} allocations")
    log_progress(f"Analysis covers {allocation_data['category_key'].nunique()} unique {feature_type}")
    
    return allocation_data

def calculate_cluster_z_scores(allocation_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Z-Scores for each store's allocation within their cluster using
    a vectorized approach (groupby + transform) to avoid Python-level loops.
    
    Args:
        allocation_data: Store allocation data (subcategory or SPU level)
        
    Returns:
        DataFrame with Z-Scores calculated
    """
    feature_type = "subcategories" if ANALYSIS_LEVEL == "subcategory" else "SPUs"
    log_progress(f"Calculating cluster-based Z-Scores for {ANALYSIS_LEVEL} allocations (vectorized)...")

    if allocation_data is None or len(allocation_data) == 0:
        log_progress(f"No allocation data available for Z-Score calculation")
        return pd.DataFrame()

    # Determine valid groups (size >= MIN_CLUSTER_SIZE) first to reduce work
    group_sizes = (
        allocation_data
        .groupby(['Cluster', 'category_key'])['allocation_value']
        .size()
        .reset_index(name='cluster_size')
    )
    valid_groups = group_sizes[group_sizes['cluster_size'] >= MIN_CLUSTER_SIZE]

    if len(valid_groups) == 0:
        log_progress(f"No valid cluster-{ANALYSIS_LEVEL} combinations found (size < {MIN_CLUSTER_SIZE})")
        return pd.DataFrame()

    log_progress(f"Processing {len(valid_groups):,} valid cluster-{ANALYSIS_LEVEL} combinations (out of {group_sizes.shape[0]:,} total)...")

    # Filter allocation data to only valid groups via merge (efficient inner join)
    valid_alloc = allocation_data.merge(valid_groups[['Cluster', 'category_key']], on=['Cluster', 'category_key'], how='inner')

    # Compute group statistics via transform (ddof=1 for sample std)
    grp = valid_alloc.groupby(['Cluster', 'category_key'])['allocation_value']
    valid_alloc['cluster_mean'] = grp.transform('mean')
    valid_alloc['cluster_std'] = grp.transform('std')  # ddof=1 by default
    valid_alloc['cluster_size'] = grp.transform('size')

    # Handle zero/NaN std safely: z-score = 0 when no variation
    std_nonzero = valid_alloc['cluster_std'].replace(0, np.nan)
    valid_alloc['z_score'] = (valid_alloc['allocation_value'] - valid_alloc['cluster_mean']) / std_nonzero
    valid_alloc['z_score'] = valid_alloc['z_score'].fillna(0.0)

    log_progress(f"Calculated Z-Scores for {len(valid_alloc):,} allocations across {valid_groups.shape[0]:,} cluster-{ANALYSIS_LEVEL} combinations")
    return valid_alloc

def identify_imbalanced_cases(z_score_data: pd.DataFrame) -> pd.DataFrame:
    """
    Identify imbalanced cases with QUANTITY REBALANCING RECOMMENDATIONS.
    
    Args:
        z_score_data: Data with Z-Scores calculated
        
    Returns:
        DataFrame with imbalanced cases and quantity rebalancing recommendations
    """
    feature_type = "subcategories" if ANALYSIS_LEVEL == "subcategory" else "SPUs"
    log_progress(f"Identifying imbalanced {ANALYSIS_LEVEL} cases with quantity rebalancing...")
    
    # Find cases where absolute Z-Score exceeds threshold
    imbalanced = z_score_data[
        np.abs(z_score_data['z_score']) > Z_SCORE_THRESHOLD
    ].copy()
    
    if len(imbalanced) == 0:
        log_progress("No imbalanced cases found")
        return imbalanced
    
    # Classify imbalance type
    imbalanced['imbalance_type'] = np.where(
        imbalanced['z_score'] > 0, 'OVER_ALLOCATED', 'UNDER_ALLOCATED'
    )
    
    # Calculate imbalance severity (adapted for analysis level)
    if ANALYSIS_LEVEL == "subcategory":
        # Traditional thresholds for subcategory
        imbalanced['imbalance_severity'] = np.where(
            np.abs(imbalanced['z_score']) > 3.0, 'EXTREME',
            np.where(np.abs(imbalanced['z_score']) > 2.5, 'HIGH', 'MODERATE')
        )
    else:
        # Adjusted thresholds for SPU (more granular)
        imbalanced['imbalance_severity'] = np.where(
            np.abs(imbalanced['z_score']) > 2.5, 'EXTREME',
            np.where(np.abs(imbalanced['z_score']) > 2.0, 'HIGH', 'MODERATE')
        )
    
    # Calculate suggested adjustment
    imbalanced['suggested_allocation'] = imbalanced['cluster_mean']
    imbalanced['adjustment_needed'] = imbalanced['suggested_allocation'] - imbalanced['allocation_value']
    
    # 🎯 QUANTITY REBALANCING CALCULATIONS
    log_progress("Calculating quantity-based rebalancing recommendations...")
    
    # Calculate current quantity (already scaled to target period)
    if 'current_quantity' in imbalanced.columns:
        imbalanced['current_quantity_15days'] = imbalanced['current_quantity']
    else:
        # Fallback: use allocation_value as quantity proxy
        imbalanced['current_quantity_15days'] = imbalanced['allocation_value']
    
    # Calculate target quantity based on cluster mean
    imbalanced['target_quantity_15days'] = imbalanced['suggested_allocation']
    
    # Calculate quantity adjustment needed
    imbalanced['quantity_adjustment_needed'] = (
        imbalanced['target_quantity_15days'] - imbalanced['current_quantity_15days']
    )
    
    # Apply rebalancing constraints
    imbalanced['max_rebalance_quantity'] = (
        imbalanced['current_quantity_15days'] * MAX_REBALANCE_PERCENTAGE
    )
    
    # Constrain quantity adjustments to reasonable limits
    imbalanced['constrained_quantity_adjustment'] = np.where(
        np.abs(imbalanced['quantity_adjustment_needed']) > imbalanced['max_rebalance_quantity'],
        np.sign(imbalanced['quantity_adjustment_needed']) * imbalanced['max_rebalance_quantity'],
        imbalanced['quantity_adjustment_needed']
    )
    
    # Only recommend rebalancing for significant quantities
    if REDISTRIBUTION_STRATEGY == "increase_only":
        # Suppress reductions; only recommend increases where current < target
        imbalanced['recommend_rebalancing'] = (
            (imbalanced['constrained_quantity_adjustment'] > 0) &
            (imbalanced['constrained_quantity_adjustment'].abs() >= MIN_REBALANCE_QUANTITY)
        )
    else:
        imbalanced['recommend_rebalancing'] = (
            np.abs(imbalanced['constrained_quantity_adjustment']) >= MIN_REBALANCE_QUANTITY
        )
    
    # Calculate unit price for cost estimates (if sales value available)
    if 'current_sales_value' in imbalanced.columns:
        imbalanced['unit_price'] = np.where(
            imbalanced['current_quantity_15days'] > 0,
            imbalanced['current_sales_value'] / imbalanced['current_quantity_15days'],
            np.nan
        )
    else:
        imbalanced['unit_price'] = np.nan
    
    # Add STANDARDIZED columns (align to constrained values)
    if ANALYSIS_LEVEL == "spu":
        if 'sty_code' in imbalanced.columns:
            imbalanced['spu_code'] = imbalanced['sty_code']
        elif 'spu_code' in imbalanced.columns:
            # Ensure standardized column exists if already present
            imbalanced['spu_code'] = imbalanced['spu_code']
    else:
        # Subcategory analysis does not have sty_code; ensure placeholder exists for downstream compatibility
        if 'spu_code' not in imbalanced.columns:
            imbalanced['spu_code'] = np.nan
    # Round recommended quantity changes to integers for real-world feasibility
    # Handle NaN/Inf safely: fill NaN/Inf with 0 before casting to int
    _rec_adj = pd.to_numeric(
        imbalanced['constrained_quantity_adjustment'], errors='coerce'
    ).replace([np.inf, -np.inf], 0).fillna(0)
    imbalanced['recommended_quantity_change'] = np.rint(_rec_adj).astype(int)

    # Refine gating after rounding: ensure minimum threshold still holds
    # If running in increase-only mode, suppress negative (reduction) recommendations
    min_units_threshold = int(np.ceil(MIN_REBALANCE_QUANTITY))
    imbalanced['recommend_rebalancing'] = (
        imbalanced['recommend_rebalancing']
        & (imbalanced['recommended_quantity_change'].abs() >= min_units_threshold)
    )
    if REDISTRIBUTION_STRATEGY == "increase_only":
        imbalanced.loc[
            imbalanced['recommended_quantity_change'] < 0, 'recommend_rebalancing'
        ] = False

    # Recompute investment based on rounded quantities
    imbalanced['investment_required'] = (
        imbalanced['recommended_quantity_change'].abs() * imbalanced['unit_price']
    ).fillna(0.0)
    
    # Generate quantity rebalancing recommendations
    def create_rebalancing_recommendation(row):
        flag = row.get('recommend_rebalancing')
        if (pd.isna(flag)) or (flag is False):
            return "No rebalancing needed (below minimum threshold)"
        
        # Use rounded, recommended quantity change for user-facing guidance
        adjustment = row['recommended_quantity_change']
        current_qty = row['current_quantity_15days']
        target_qty = current_qty + adjustment
        unit_price = row['unit_price']
        
        if adjustment > 0:
            action = "INCREASE"
            direction = "to"
        else:
            if REDISTRIBUTION_STRATEGY == "increase_only":
                return "No rebalancing needed (increase-only mode)"
            action = "REDUCE"
            direction = "to"
            adjustment = abs(adjustment)
        
        if (pd.notna(unit_price)) and (unit_price > 0):
            cost_info = f" @ ~${unit_price:.0f}/unit"
        else:
            cost_info = ""
        
        return f"{action} {int(adjustment)} UNITS/15-DAYS {direction} {target_qty:.1f} (current: {current_qty:.1f}){cost_info}"
    
    imbalanced['recommendation_text'] = imbalanced.apply(  # STANDARDIZED: Use recommendation_text
        create_rebalancing_recommendation, axis=1
    )
    
    log_progress(f"Identified {len(imbalanced)} imbalanced {ANALYSIS_LEVEL} cases")
    
    if len(imbalanced) > 0:
        over_allocated = len(imbalanced[imbalanced['imbalance_type'] == 'OVER_ALLOCATED'])
        under_allocated = len(imbalanced[imbalanced['imbalance_type'] == 'UNDER_ALLOCATED'])
        # Treat NA flags as False for counting without mutating stored values
        mask = imbalanced['recommend_rebalancing'].fillna(False)
        rebalancing_recommended = mask.sum()
        total_quantity_adjustment = imbalanced.loc[mask, 'constrained_quantity_adjustment'].abs().sum()
        
        log_progress(f"  • Over-allocated: {over_allocated}")
        log_progress(f"  • Under-allocated: {under_allocated}")
        if under_allocated == 0:
            log_progress("  ⚠️ No under-allocated cases detected. This may indicate data skew or grouping-level effects; proceeding but recommend review of grouping and thresholds.")
        log_progress(f"  • Rebalancing recommended: {rebalancing_recommended}")
        log_progress(f"  • Total quantity adjustment needed: {total_quantity_adjustment:.1f} units/15-days")
        
        # Log severity breakdown
        severity_counts = imbalanced['imbalance_severity'].value_counts()
        log_progress(f"  • Severity breakdown: {dict(severity_counts)}")
    
    # 📈 FAST FISH ENHANCEMENT: Apply sell-through validation
    if SELLTHROUGH_VALIDATION_AVAILABLE and len(imbalanced) > 0:
        log_progress("🎯 Applying Fast Fish sell-through validation...")
        
        # Initialize validator
        historical_data = load_historical_data_for_validation()
        validator = SellThroughValidator(historical_data)
        
        # Apply validation to each imbalanced case
        validated_cases = []
        rejected_count = 0
        
        skipped_count = 0
        for idx, case in imbalanced.iterrows():
            # Get category name for validation (preserve missingness; no synthetic 'Unknown')
            category_name = case.get('sub_cate_name', None)
            if pd.isna(category_name) or category_name in [None, '']:
                skipped_count += 1
                continue
            
            # Use period-aware quantity fields; skip if missing (no synthetic numeric defaults)
            current_qty = case.get('current_quantity_15days', np.nan)
            target_qty = case.get('target_quantity_15days', np.nan)
            if pd.isna(current_qty):
                skipped_count += 1
                continue
            if pd.isna(target_qty):
                # Derive from constrained adjustment if available
                adj = case.get('constrained_quantity_adjustment', np.nan)
                if pd.isna(adj):
                    skipped_count += 1
                    continue
                target_qty = current_qty + adj
            
            # Validate the rebalancing recommendation using CORRECTED Fast Fish definition
            # Clamp inputs to realistic integer ranges and cast to int
            current_qty_clamped = int(np.clip(current_qty, 0, 100))
            target_qty_clamped = int(np.clip(target_qty, 0, 100))
            validation = validator.validate_recommendation(
                store_code=str(case['str_code']),
                category=str(category_name),
                current_spu_count=current_qty_clamped,
                recommended_spu_count=target_qty_clamped,
                action='REBALANCE',
                rule_name='Rule 8: Imbalanced Allocation'
            )
            
            # Only keep Fast Fish compliant recommendations
            if validation['fast_fish_compliant']:
                # Add sell-through metrics to case
                enhanced_case = case.to_dict()
                enhanced_case.update({
                    'current_sell_through_rate': validation['current_sell_through_rate'],
                    'predicted_sell_through_rate': validation['predicted_sell_through_rate'],
                    'sell_through_improvement': validation['sell_through_improvement'],
                    'fast_fish_compliant': validation['fast_fish_compliant'],
                    'business_rationale': validation['business_rationale'],
                    'approval_reason': validation['approval_reason']
                })
                validated_cases.append(enhanced_case)
            else:
                rejected_count += 1
        
        # Replace imbalanced cases with validated ones
        if validated_cases:
            imbalanced = pd.DataFrame(validated_cases)
            # Ensure gating reflects approved recommendations
            imbalanced['recommend_rebalancing'] = True
            # Sort by sell-through improvement (prioritize best rebalancing opportunities)
            imbalanced = imbalanced.sort_values('sell_through_improvement', ascending=False)
            
            avg_improvement = imbalanced['sell_through_improvement'].mean()
            
            log_progress(f"Fast Fish sell-through validation complete:")
            log_progress(f"   Approved: {len(validated_cases)} rebalancing cases")
            log_progress(f"   Rejected: {rejected_count} rebalancing cases")
            log_progress(f"   Skipped (missing inputs): {skipped_count} rebalancing cases")
            log_progress(f"   Average sell-through improvement: {avg_improvement:.1f} percentage points")
        else:
            log_progress(f"⚠️ All {len(imbalanced)} rebalancing cases rejected by sell-through validation")
            imbalanced = pd.DataFrame()  # Return empty DataFrame
    elif not SELLTHROUGH_VALIDATION_AVAILABLE and len(imbalanced) > 0:
        log_progress("⚠️ Sell-through validation skipped (validator not available)")
    
    # ===== PER-STORE CAP AFTER VALIDATION =====
    if len(imbalanced) > 0:
        # Sort by priority: sell_through_improvement desc, |z_score| desc, |constrained_quantity_adjustment| desc
        imbalanced['abs_z'] = imbalanced['z_score'].abs()
        imbalanced['abs_cqa'] = imbalanced['constrained_quantity_adjustment'].abs()
        sort_cols = []
        if 'sell_through_improvement' in imbalanced.columns:
            sort_cols.append(('sell_through_improvement', False))
        sort_cols.extend([('abs_z', False), ('abs_cqa', False)])

        if sort_cols:
            imbalanced = imbalanced.sort_values([c for c, _ in sort_cols], ascending=[a for _, a in sort_cols])

        before_rows = len(imbalanced)
        # Apply per-store cap only when configured (>0)
        if (MAX_TOTAL_ADJUSTMENTS_PER_STORE is not None) and (MAX_TOTAL_ADJUSTMENTS_PER_STORE > 0):
            imbalanced = (
                imbalanced.groupby('str_code', group_keys=False)
                .head(MAX_TOTAL_ADJUSTMENTS_PER_STORE)
            )
        after_rows = len(imbalanced)
        trimmed = before_rows - after_rows
        if trimmed > 0:
            stores_trimmed = (before_rows != after_rows)
            log_progress(
                f"Applied per-store cap: kept top {MAX_TOTAL_ADJUSTMENTS_PER_STORE} per store; "
                f"trimmed {trimmed} cases across all stores"
            )

        # Drop helper columns
        imbalanced = imbalanced.drop(columns=[c for c in ['abs_z', 'abs_cqa'] if c in imbalanced.columns])

    return imbalanced

def apply_imbalanced_rule(cluster_df: pd.DataFrame, imbalanced_cases: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the imbalanced rule to all stores and create rule results.
    
    Args:
        cluster_df: Cluster assignments
        imbalanced_cases: Imbalanced cases
        
    Returns:
        DataFrame with rule results for all stores
    """
    feature_type = "categories" if ANALYSIS_LEVEL == "subcategory" else "SPUs"
    log_progress(f"Applying imbalanced {feature_type} rule to all stores...")
    
    # STANDARDIZATION FIX: Use cluster_id instead of Cluster for consistency
    cluster_df_standardized = cluster_df.copy()
    if 'Cluster' in cluster_df_standardized.columns:
        cluster_df_standardized['cluster_id'] = cluster_df_standardized['Cluster']
        cluster_df_standardized = cluster_df_standardized.drop('Cluster', axis=1)
    
    # Create base results for all stores
    results_df = cluster_df_standardized[['str_code', 'cluster_id']].copy()
    
    # Count imbalanced cases per store with quantity metrics
    if len(imbalanced_cases) > 0:
        store_imbalance_stats = imbalanced_cases.groupby('str_code').agg({
            'category_key': 'count',
            'z_score': ['mean', lambda x: np.mean(np.abs(x))],  # Mean and absolute mean Z-Score
            'adjustment_needed': 'sum',
            'imbalance_type': lambda x: (x == 'OVER_ALLOCATED').sum(),  # Count over-allocations
            'recommend_rebalancing': 'sum',  # Count rebalancing recommendations
            'constrained_quantity_adjustment': lambda x: np.abs(x).sum(),  # Total quantity adjustment (pre-rounding)
            'recommended_quantity_change': lambda x: np.abs(x).sum(),     # Total rebalance units (rounded)
            'investment_required': 'sum'                                   # Total rebalance investment
        }).reset_index()
        
        # Flatten column names with quantity metrics
        if ANALYSIS_LEVEL == "subcategory":
            store_imbalance_stats.columns = [
                'str_code', 'imbalanced_categories_count', 'avg_z_score', 'avg_abs_z_score', 
                'total_adjustment_needed', 'over_allocated_count', 'rebalancing_recommended_count',
                'total_quantity_adjustment_needed', 'total_rebalance_units', 'total_rebalance_investment'
            ]
            count_col = 'imbalanced_categories_count'
            rule_col = 'rule8_imbalanced'
        else:
            store_imbalance_stats.columns = [
                'str_code', 'imbalanced_spus_count', 'avg_z_score', 'avg_abs_z_score', 
                'total_adjustment_needed', 'over_allocated_count', 'rebalancing_recommended_count',
                'total_quantity_adjustment_needed', 'total_rebalance_units', 'total_rebalance_investment'
            ]
            count_col = 'imbalanced_spus_count'
            rule_col = 'rule8_imbalanced_spu'
        
        # Calculate under-allocated count
        store_imbalance_stats['under_allocated_count'] = (
            store_imbalance_stats[count_col] - 
            store_imbalance_stats['over_allocated_count']
        )
        
        # Merge with results
        results_df = results_df.merge(store_imbalance_stats, on='str_code', how='left')
        
        # Preserve NA and report missingness instead of filling with zeros
        fill_cols = [count_col, 'avg_z_score', 'avg_abs_z_score', 
                    'total_adjustment_needed', 'over_allocated_count', 'under_allocated_count',
                    'rebalancing_recommended_count', 'total_quantity_adjustment_needed',
                    'total_rebalance_units', 'total_rebalance_investment']
        na_report = {c: int(results_df[c].isna().sum()) for c in fill_cols if c in results_df.columns}
        if na_report:
            log_progress("Results NA diagnostics: " + ", ".join([f"{k}={v:,}" for k, v in na_report.items()]))
        
        # Create rule flag
        results_df[rule_col] = (results_df[count_col] > 0).astype(int)
    else:
        # No imbalanced cases found
        if ANALYSIS_LEVEL == "subcategory":
            results_df['imbalanced_categories_count'] = 0
            rule_col = 'rule8_imbalanced'
        else:
            results_df['imbalanced_spus_count'] = 0
            rule_col = 'rule8_imbalanced_spu'
        
        results_df['avg_z_score'] = 0
        results_df['avg_abs_z_score'] = 0
        results_df['total_adjustment_needed'] = 0
        results_df['over_allocated_count'] = 0
        results_df['under_allocated_count'] = 0
        results_df['rebalancing_recommended_count'] = 0
        results_df['total_quantity_adjustment_needed'] = 0
        results_df[rule_col] = 0
    
    # STANDARDIZATION FIX: Add missing standard columns for pipeline compatibility
    # Map total_quantity_adjustment_needed to recommended_quantity_change (standard column name)
    # Keep backward compatibility: recommended_quantity_change reflects pre-round total
    results_df['recommended_quantity_change'] = results_df['total_quantity_adjustment_needed']
    # For imbalanced allocation, investment is neutral (rebalancing only); keep backward compatibility
    results_df['investment_required'] = 0.0
    
    # Add standard business rationale and approval columns
    results_df['business_rationale'] = results_df.apply(
        lambda row: f"Imbalanced allocation detected: {row.get('imbalanced_spus_count', row.get('imbalanced_categories_count', 0))} items need rebalancing" 
                   if row.get('rule8_imbalanced_spu', row.get('rule8_imbalanced', 0)) > 0 else "No imbalance issues", axis=1
    )
    results_df['approval_reason'] = 'Automatic approval for allocation rebalancing'
    results_df['fast_fish_compliant'] = True  # Rebalancing is always compliant
    results_df['opportunity_type'] = 'IMBALANCED_ALLOCATION'
    
    # Add metadata with quantity rebalancing
    if ANALYSIS_LEVEL == "subcategory":
        results_df['rule8_description'] = 'Store has imbalanced subcategory allocations with unit quantity rebalancing recommendations'
    else:
        results_df['rule8_description'] = 'Store has imbalanced SPU allocations with unit quantity rebalancing recommendations'
    
    results_df['rule8_threshold'] = f"|Z-Score| > {Z_SCORE_THRESHOLD}"
    results_df['rule8_analysis_level'] = ANALYSIS_LEVEL
    
    flagged_stores = results_df[rule_col].sum()
    log_progress(f"Applied imbalanced {feature_type} rule: {flagged_stores} stores flagged")
    
    return results_df

def save_results(results_df: pd.DataFrame, imbalanced_cases: pd.DataFrame, z_score_data: pd.DataFrame) -> None:
    """
    Save rule results and detailed analysis.
    
    Args:
        results_df: Rule results for all stores
{{ ... }}
        imbalanced_cases: Detailed imbalanced cases
        z_score_data: Complete Z-Score analysis
    """
    feature_type = "categories" if ANALYSIS_LEVEL == "subcategory" else "SPUs"
    
    # Determine period label for outputs (support target labeling via environment)
    cur_yyyymm, cur_period = get_current_period()
    target_yyyymm = os.environ.get("PIPELINE_TARGET_YYYYMM")
    target_period = os.environ.get("PIPELINE_TARGET_PERIOD")
    period_label = get_period_label(target_yyyymm or cur_yyyymm, target_period if target_yyyymm else cur_period)

    prefix = CURRENT_CONFIG['output_prefix']
    timestamped, period_file, generic = create_output_with_symlinks(
        results_df,
        f"{OUTPUT_DIR}/{prefix}_results",
        period_label
    )
    log_progress(f"Saved {ANALYSIS_LEVEL} rule results: {timestamped}")
    results_file = timestamped
    
    # Save detailed imbalanced cases (always create file; add minimal headers if empty)
    if imbalanced_cases is None or len(imbalanced_cases) == 0:
        imbalanced_cases = pd.DataFrame(columns=['str_code', 'category_key', 'z_score', 'imbalance_type'])
    timestamped_cases, _, _ = create_output_with_symlinks(
        imbalanced_cases,
        f"{OUTPUT_DIR}/{prefix}_cases",
        period_label
    )
    log_progress(f"Saved detailed imbalanced cases: {timestamped_cases}")
    cases_file = timestamped_cases

    # Save Z-Score analysis (optionally limited or skipped; always create a file)
    z_score_file = f"{OUTPUT_DIR}/{prefix}_z_score_analysis_{period_label}.csv"
    if SKIP_ZSCORE_OUTPUT:
        z_df_to_save = pd.DataFrame(columns=['str_code', 'Cluster', 'category_key', 'allocation_value', 'z_score', 'cluster_mean', 'cluster_std', 'cluster_size'])
        log_progress("Skipping detailed Z-Score analysis output per configuration; writing headers only")
    else:
        if z_score_data is None or len(z_score_data) == 0:
            z_df_to_save = pd.DataFrame(columns=['str_code', 'Cluster', 'category_key', 'allocation_value', 'z_score', 'cluster_mean', 'cluster_std', 'cluster_size'])
        else:
            z_df_to_save = z_score_data
            if ZSCORE_OUTPUT_LIMIT is not None and ZSCORE_OUTPUT_LIMIT > 0 and len(z_df_to_save) > ZSCORE_OUTPUT_LIMIT:
                # Keep top-N rows by |z_score| to reduce file size/I-O
                if 'z_score' in z_df_to_save.columns:
                    _tmp = z_df_to_save.copy()
                    _tmp['_abs_z'] = _tmp['z_score'].abs()
                    z_df_to_save = _tmp.sort_values('_abs_z', ascending=False).head(ZSCORE_OUTPUT_LIMIT).drop(columns=['_abs_z'])
                    log_progress(f"Limiting Z-Score analysis output to top {ZSCORE_OUTPUT_LIMIT:,} rows by |z| (from {len(z_score_data):,})")
                else:
                    z_df_to_save = z_df_to_save.head(ZSCORE_OUTPUT_LIMIT)
                    log_progress(f"Limiting Z-Score analysis output to first {ZSCORE_OUTPUT_LIMIT:,} rows (no z_score column found)")
    timestamped_z, _, _ = create_output_with_symlinks(
        z_df_to_save,
        f"{OUTPUT_DIR}/{prefix}_z_score_analysis",
        period_label
    )
    log_progress(f"Saved Z-Score analysis: {timestamped_z}")
    z_score_file = timestamped_z
    
    # Register outputs in manifest (generic and period-specific keys)
    try:
        register_step_output(
            "step8",
            "results",
            results_file,
            metadata={
                "rows": int(len(results_df)),
                "analysis_level": ANALYSIS_LEVEL,
                "period_label": period_label,
            },
        )
        register_step_output(
            "step8",
            f"results_{period_label}",
            results_file,
            metadata={
                "rows": int(len(results_df)),
                "analysis_level": ANALYSIS_LEVEL,
                "period_label": period_label,
            },
        )
        register_step_output(
            "step8",
            "cases",
            cases_file,
            metadata={
                "rows": int(len(imbalanced_cases) if imbalanced_cases is not None else 0),
                "analysis_level": ANALYSIS_LEVEL,
                "period_label": period_label,
            },
        )
        register_step_output(
            "step8",
            f"cases_{period_label}",
            cases_file,
            metadata={
                "rows": int(len(imbalanced_cases) if imbalanced_cases is not None else 0),
                "analysis_level": ANALYSIS_LEVEL,
                "period_label": period_label,
            },
        )
        register_step_output(
            "step8",
            "z_score_analysis",
            z_score_file,
            metadata={
                "rows": int(len(z_score_data) if z_score_data is not None else 0),
                "analysis_level": ANALYSIS_LEVEL,
                "period_label": period_label,
            },
        )
        register_step_output(
            "step8",
            f"z_score_analysis_{period_label}",
            z_score_file,
            metadata={
                "rows": int(len(z_score_data) if z_score_data is not None else 0),
                "analysis_level": ANALYSIS_LEVEL,
                "period_label": period_label,
            },
        )
    except Exception as e:
        log_progress(f"⚠️ Manifest registration error: {e}")
    
    # Generate summary report
    summary_file = f"{OUTPUT_DIR}/{prefix}_summary_{period_label}.md"
    with open(summary_file, 'w') as f:
        f.write(f"# Rule 8: Imbalanced {feature_type.title()} Allocation Analysis Summary\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Analysis Level**: {ANALYSIS_LEVEL.title()}\n\n")
        
        f.write("## Rule Definition\n")
        f.write(f"Identifies stores with imbalanced {ANALYSIS_LEVEL} allocations using Z-Score analysis within cluster peers.\n")
        f.write(f"**ENHANCEMENT**: Provides specific UNIT QUANTITY rebalancing recommendations for investment-neutral optimization.\n\n")
        
        f.write("## Parameters\n")
        f.write(f"- Analysis Level: {ANALYSIS_LEVEL}\n")
        f.write(f"- Z-Score threshold: |Z| > {Z_SCORE_THRESHOLD}\n")
        f.write(f"- Minimum cluster size: ≥{MIN_CLUSTER_SIZE} stores\n")
        f.write(f"- Minimum allocation threshold: ≥{MIN_ALLOCATION_THRESHOLD} styles\n")
        f.write(f"- Data period: {DATA_PERIOD_DAYS} days (half-month)\n")
        f.write(f"- Target period: {TARGET_PERIOD_DAYS} days\n")
        f.write(f"- Minimum rebalance quantity: ≥{MIN_REBALANCE_QUANTITY} units\n")
        f.write(f"- Maximum rebalance percentage: {MAX_REBALANCE_PERCENTAGE*100:.0f}% of current allocation\n\n")
        
        f.write("## Results\n")
        f.write(f"- Total stores analyzed: {len(results_df):,}\n")
        
        rule_col = 'rule8_imbalanced' if ANALYSIS_LEVEL == "subcategory" else 'rule8_imbalanced_spu'
        flagged_stores = results_df[rule_col].sum()
        f.write(f"- Stores with imbalanced allocations: {flagged_stores:,}\n")
        f.write(f"- Total imbalanced {feature_type}: {len(imbalanced_cases):,}\n")
        
        if len(imbalanced_cases) > 0:
            over_allocated = len(imbalanced_cases[imbalanced_cases['imbalance_type'] == 'OVER_ALLOCATED'])
            under_allocated = len(imbalanced_cases[imbalanced_cases['imbalance_type'] == 'UNDER_ALLOCATED'])
            avg_z_score = imbalanced_cases['z_score'].abs().mean()
            
            # Quantity rebalancing metrics
            if 'recommend_rebalancing' in imbalanced_cases.columns:
                _mask = imbalanced_cases['recommend_rebalancing'].fillna(False)
                rebalancing_recommended = _mask.sum()
                total_quantity_adjustment = imbalanced_cases.loc[_mask, 'constrained_quantity_adjustment'].abs().sum()
            else:
                rebalancing_recommended = 0
                total_quantity_adjustment = 0
            
            f.write(f"- Over-allocated cases: {over_allocated:,}\n")
            f.write(f"- Under-allocated cases: {under_allocated:,}\n")
            f.write(f"- Average |Z-Score|: {avg_z_score:.2f}\n")
            f.write(f"\n## Quantity Rebalancing Metrics\n")
            f.write(f"- Cases with rebalancing recommended: {rebalancing_recommended:,}\n")
            f.write(f"- Total quantity adjustment needed (pre-round): {total_quantity_adjustment:.1f} units/15-days\n")
            # Integer rounding diagnostics
            if 'recommended_quantity_change' in imbalanced_cases.columns:
                int_share = float((imbalanced_cases['recommended_quantity_change'] == np.rint(imbalanced_cases['recommended_quantity_change'])).mean())
                total_rounded_units = imbalanced_cases['recommended_quantity_change'].abs().sum()
                total_investment = 0.0
                if 'investment_required' in imbalanced_cases.columns:
                    total_investment = imbalanced_cases['investment_required'].sum()
                f.write(f"- Integer rounding applied to quantity recommendations: {int_share*100:.1f}% integer\n")
                f.write(f"- Total rebalance units (rounded): {int(total_rounded_units):,} units/15-days\n")
                f.write(f"- Total rebalance inventory value: ${total_investment:,.0f}\n")
            f.write(f"- Investment impact: **NEUTRAL** (rebalancing existing inventory)\n")
            
            # Severity breakdown
            severity_counts = imbalanced_cases['imbalance_severity'].value_counts()
            f.write("\n## Severity Breakdown\n")
            for severity, count in severity_counts.items():
                f.write(f"- {severity}: {count:,} cases\n")
            
            # Top categories with imbalances
            feature_col = 'sub_cate_name' if ANALYSIS_LEVEL == "subcategory" else 'sty_code'
            if feature_col in imbalanced_cases.columns:
                f.write(f"\n## Top {CURRENT_CONFIG['feature_name']}s with Imbalances\n")
                top_features = imbalanced_cases[feature_col].value_counts().head(10)
                for feature, count in top_features.items():
                    f.write(f"- {feature}: {count} cases\n")
            
            # Cluster-level insights
            f.write(f"\n## Cluster-Level Insights\n")
            cluster_summary = imbalanced_cases.groupby('Cluster').agg({
                'str_code': 'nunique',
                'z_score': lambda x: np.mean(np.abs(x))
            }).sort_values('z_score', ascending=False).head(5)
            
            f.write("Top 5 clusters by average |Z-Score|:\n")
            for cluster_id, row in cluster_summary.iterrows():
                f.write(f"- Cluster {cluster_id}: {row['str_code']} stores, avg |Z-Score| {row['z_score']:.2f}\n")
        else:
            f.write(f"No imbalanced {feature_type} identified.\n")
    
    log_progress(f"Saved summary report to {summary_file}")
    
    # Backward-compatible files are now created as symlinks by create_output_with_symlinks
    # No additional action needed

def main() -> None:
    """Main function to execute imbalanced allocation rule analysis"""
    # CLI to set periods and analysis level dynamically
    parser = argparse.ArgumentParser(description="Step 8: Imbalanced Allocation Rule")
    parser.add_argument("--yyyymm", type=str, help="Base YYYYMM for inputs (e.g., 202508)")
    parser.add_argument("--period", type=str, choices=["A", "B"], help="Half-month period: A or B")
    parser.add_argument("--analysis-level", type=str, choices=["subcategory", "spu"], help="Analysis level override")
    parser.add_argument("--recent-months-back", type=int, default=0, help="Average over last N half-month periods (including base). 0=disabled")
    parser.add_argument("--target-yyyymm", type=str, help="Target YYYYMM label for outputs (e.g., 202509)")
    parser.add_argument("--target-period", type=str, choices=["A", "B"], help="Target half-month label for outputs")
    parser.add_argument("--z-threshold", type=float, help="Override Z-score threshold (default depends on analysis level)")
    parser.add_argument("--seasonal-blending", action="store_true", help="Enable seasonal blending (August-style blending)")
    parser.add_argument("--seasonal-yyyymm", type=str, help="Seasonal data YYYYMM (e.g., 202408)")
    parser.add_argument("--seasonal-period", type=str, choices=["A","B","full"], help="Seasonal period")
    parser.add_argument("--seasonal-weight", type=float, help="Seasonal weight (0-1)")
    parser.add_argument("--seasonal-years-back", type=int, default=2, help="Number of prior years (same month/period) to include when seasonal blending is enabled (default 2)")
    parser.add_argument("--max-adj-per-store", type=int, help="Optional per-store cap on adjustments; omit for no cap")
    # Threshold configuration arguments
    parser.add_argument("--min-cluster-size", type=int, help="Minimum stores in cluster for valid Z-Score (default: 5 for SPU, 3 for subcategory)")
    parser.add_argument("--min-allocation-threshold", type=float, help="Minimum allocation value to consider (default: 0.05 for SPU, 0.1 for subcategory)")
    parser.add_argument("--min-rebalance-qty", type=float, help="Minimum units to recommend rebalancing (default: 5.0 for SPU, 2.0 for subcategory)")
    parser.add_argument("--max-rebalance-pct", type=float, help="Maximum percentage of allocation to rebalance (default: 0.3)")
    # Output control flags
    parser.add_argument("--zscore-output-limit", type=int, help="Limit rows written to z_score_analysis CSV (top-|z|). Omit for all.")
    parser.add_argument("--skip-zscore-output", action="store_true", help="Do not write detailed z_score_analysis rows; write headers only.")
    args, unknown = parser.parse_known_args()

    # Initialize pipeline configuration and update globals
    initialize_pipeline_config(args.yyyymm, args.period, args.analysis_level)
    global ANALYSIS_LEVEL, CURRENT_CONFIG, CLUSTER_RESULTS_FILE, Z_SCORE_THRESHOLD
    if getattr(args, "analysis_level", None):
        global ANALYSIS_LEVEL, CURRENT_CONFIG, CLUSTER_RESULTS_FILE
        ANALYSIS_LEVEL = args.analysis_level
        CURRENT_CONFIG = ANALYSIS_CONFIGS[ANALYSIS_LEVEL]
        CLUSTER_RESULTS_FILE = CURRENT_CONFIG["cluster_file"]
        log_progress(f"Config: analysis-level set to {ANALYSIS_LEVEL}")

    # Apply recent/seasonal CLI overrides
    global RECENT_MONTHS_BACK, USE_SEASONAL_BLENDING, SEASONAL_WEIGHT_OVERRIDE, SEASONAL_YEARS_BACK_OVERRIDE, BASE_AVG_YYYMM, BASE_AVG_PERIOD
    if getattr(args, "recent_months_back", None) is not None:
        RECENT_MONTHS_BACK = max(0, int(args.recent_months_back))
        if RECENT_MONTHS_BACK > 0:
            log_progress(f"Config: recent-months-back = {RECENT_MONTHS_BACK}")
            # Set strict base anchor for averaging
            if args.yyyymm and args.period:
                BASE_AVG_YYYMM = args.yyyymm
                BASE_AVG_PERIOD = args.period
                log_progress(f"Anchoring recent averaging to base period: {BASE_AVG_YYYMM}{BASE_AVG_PERIOD}")
    if getattr(args, "seasonal_blending", False):
        USE_SEASONAL_BLENDING = True
        log_progress("Config: seasonal blending ENABLED via CLI")
    if getattr(args, "seasonal_weight", None) is not None:
        SEASONAL_WEIGHT_OVERRIDE = float(args.seasonal_weight)
        log_progress(f"Config: seasonal weight override = {SEASONAL_WEIGHT_OVERRIDE}")
    if getattr(args, "seasonal_years_back", None) is not None:
        SEASONAL_YEARS_BACK_OVERRIDE = int(args.seasonal_years_back)
        log_progress(f"Config: seasonal years-back override = {SEASONAL_YEARS_BACK_OVERRIDE}")

    # Map explicit seasonal anchor from CLI to env so load_data() uses it
    if getattr(args, "seasonal_yyyymm", None):
        os.environ["SEASONAL_YYYYMM"] = str(args.seasonal_yyyymm)
        log_progress(f"Config: seasonal anchor yyyymm = {os.environ['SEASONAL_YYYYMM']}")
    if getattr(args, "seasonal_period", None):
        os.environ["SEASONAL_PERIOD"] = str(args.seasonal_period)
        log_progress(f"Config: seasonal anchor period = {os.environ['SEASONAL_PERIOD']}")

    # Optionally override Z-score threshold from CLI
    if args.z_threshold is not None:
        try:
            Z_SCORE_THRESHOLD = float(args.z_threshold)
            log_progress(f"Overriding Z-score threshold via CLI: Z_SCORE_THRESHOLD={Z_SCORE_THRESHOLD}")
        except Exception:
            log_progress("Ignoring invalid --z-threshold value; using defaults")

    # Set target period label via environment for save_results()
    if args.target_yyyymm:
        os.environ["PIPELINE_TARGET_YYYYMM"] = args.target_yyyymm
    if args.target_period:
        os.environ["PIPELINE_TARGET_PERIOD"] = args.target_period
    
    # Seasonal blending via CLI (override August auto-detect as needed)
    if args.seasonal_blending:
        global USE_BLENDED_SEASONAL
        USE_BLENDED_SEASONAL = True
    if args.seasonal_yyyymm:
        os.environ["SEASONAL_YYYYMM"] = args.seasonal_yyyymm
    if args.seasonal_period:
        os.environ["SEASONAL_PERIOD"] = "" if args.seasonal_period == "full" else args.seasonal_period
    if args.seasonal_weight is not None:
        os.environ["SEASONAL_WEIGHT"] = str(args.seasonal_weight)
    if args.seasonal_years_back is not None:
        os.environ["SEASONAL_YEARS_BACK"] = str(max(1, int(args.seasonal_years_back)))
    
    # Optional per-store cap from CLI
    global MAX_TOTAL_ADJUSTMENTS_PER_STORE
    if args.max_adj_per_store is not None:
        try:
            MAX_TOTAL_ADJUSTMENTS_PER_STORE = int(args.max_adj_per_store)
        except Exception:
            MAX_TOTAL_ADJUSTMENTS_PER_STORE = None

    # Output controls from CLI
    global ZSCORE_OUTPUT_LIMIT, SKIP_ZSCORE_OUTPUT
    if getattr(args, "zscore_output_limit", None) is not None:
        try:
            ZSCORE_OUTPUT_LIMIT = max(1, int(args.zscore_output_limit))
            log_progress(f"Config: Z-score output limited to top {ZSCORE_OUTPUT_LIMIT:,} rows")
        except Exception:
            ZSCORE_OUTPUT_LIMIT = None
    if getattr(args, "skip_zscore_output", False):
        SKIP_ZSCORE_OUTPUT = True
    
    # Override threshold module-level variables from CLI arguments using globals() dict
    if args.min_cluster_size is not None:
        globals()['MIN_CLUSTER_SIZE'] = int(args.min_cluster_size)
        log_progress(f"Overriding MIN_CLUSTER_SIZE via CLI: {globals()['MIN_CLUSTER_SIZE']}")
    if args.min_allocation_threshold is not None:
        globals()['MIN_ALLOCATION_THRESHOLD'] = float(args.min_allocation_threshold)
        log_progress(f"Overriding MIN_ALLOCATION_THRESHOLD via CLI: {globals()['MIN_ALLOCATION_THRESHOLD']}")
    if args.min_rebalance_qty is not None:
        globals()['MIN_REBALANCE_QUANTITY'] = float(args.min_rebalance_qty)
        log_progress(f"Overriding MIN_REBALANCE_QUANTITY via CLI: {globals()['MIN_REBALANCE_QUANTITY']}")
    if args.max_rebalance_pct is not None:
        globals()['MAX_REBALANCE_PERCENTAGE'] = float(args.max_rebalance_pct)
        log_progress(f"Overriding MAX_REBALANCE_PERCENTAGE via CLI: {globals()['MAX_REBALANCE_PERCENTAGE']}")
        log_progress("Config: Skipping detailed Z-Score analysis output (headers only)")

    start_time = datetime.now()
    log_progress(f"Starting Rule 8: {CURRENT_CONFIG['description']}...")
    
    # Log seasonal blending approach
    if USE_SEASONAL_BLENDING or USE_BLENDED_SEASONAL:
        log_progress("🍂 SEASONAL BLENDING ACTIVE")
        if SEASONAL_WEIGHT_OVERRIDE is not None:
            log_progress(f"   • Seasonal weight: {SEASONAL_WEIGHT_OVERRIDE}")
        if SEASONAL_YEARS_BACK_OVERRIDE is not None:
            log_progress(f"   • Seasonal years back: {SEASONAL_YEARS_BACK_OVERRIDE}")
    if RECENT_MONTHS_BACK and RECENT_MONTHS_BACK > 0:
        log_progress(f"📊 Recent averaging enabled: last {RECENT_MONTHS_BACK} half-months")
    
    try:
        # Load data
        cluster_df, planning_df, quantity_df = load_data()
        
        # Prepare allocation data
        allocation_data = prepare_allocation_data(planning_df, cluster_df, quantity_df)
        
        # Calculate Z-Scores
        z_score_data = calculate_cluster_z_scores(allocation_data)
        
        if len(z_score_data) == 0:
            log_progress(f"No valid data for {ANALYSIS_LEVEL} Z-Score analysis. Creating empty results.")
            results_df = cluster_df[['str_code', 'Cluster']].copy()
            
            if ANALYSIS_LEVEL == "subcategory":
                results_df['rule8_imbalanced'] = 0
                results_df['imbalanced_categories_count'] = 0
            else:
                results_df['rule8_imbalanced_spu'] = 0
                results_df['imbalanced_spus_count'] = 0
            
            results_df['avg_z_score'] = 0
            results_df['avg_abs_z_score'] = 0
            results_df['total_adjustment_needed'] = 0
            results_df['over_allocated_count'] = 0
            results_df['under_allocated_count'] = 0
            results_df['rule8_description'] = f'No valid data for {ANALYSIS_LEVEL} Z-Score analysis'
            results_df['rule8_threshold'] = 'N/A'
            results_df['rule8_analysis_level'] = ANALYSIS_LEVEL
            
            # Save all standard outputs (results, cases, z-score) for consistency
            empty_cases = pd.DataFrame(columns=['str_code', 'category_key', 'z_score', 'imbalance_type'])
            empty_z = pd.DataFrame(columns=['str_code', 'Cluster', 'category_key', 'allocation_value', 'z_score', 'cluster_mean', 'cluster_std', 'cluster_size'])
            save_results(results_df, empty_cases, empty_z)
            return
        
        # Identify imbalanced cases
        imbalanced_cases = identify_imbalanced_cases(z_score_data)
        
        # Apply rule and create results
        results_df = apply_imbalanced_rule(cluster_df, imbalanced_cases)
        
        # Save results
        save_results(results_df, imbalanced_cases, z_score_data)
        
        # Calculate completion time
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Summary
        rule_col = 'rule8_imbalanced' if ANALYSIS_LEVEL == "subcategory" else 'rule8_imbalanced_spu'
        flagged_stores = results_df[rule_col].sum()
        feature_type = "categories" if ANALYSIS_LEVEL == "subcategory" else "SPUs"
        
        log_progress("\n" + "="*70)
        log_progress(f"RULE 8: IMBALANCED {feature_type.upper()} ALLOCATION ANALYSIS COMPLETE")
        log_progress("="*70)
        log_progress(f"Analysis Level: {ANALYSIS_LEVEL.upper()}")
        log_progress(f"Process completed in {duration:.2f} seconds")
        log_progress(f"✓ Stores analyzed: {len(results_df):,}")
        log_progress(f"✓ Stores flagged: {flagged_stores:,}")
        log_progress(f"✓ Imbalanced {feature_type}: {len(imbalanced_cases):,}")
        
        if len(imbalanced_cases) > 0:
            avg_adjustment = imbalanced_cases['adjustment_needed'].abs().mean()
            log_progress(f"✓ Average adjustment needed: {avg_adjustment:.2f} styles")
            
            avg_z_score = imbalanced_cases['z_score'].abs().mean()
            log_progress(f"✓ Average |Z-Score|: {avg_z_score:.2f}")
            
            # Quantity rebalancing metrics
            if 'recommend_rebalancing' in imbalanced_cases.columns:
                mask = imbalanced_cases['recommend_rebalancing'].fillna(False)
                rebalancing_recommended = mask.sum()
                total_quantity_adjustment = imbalanced_cases.loc[mask, 'constrained_quantity_adjustment'].abs().sum()
                log_progress(f"✓ Rebalancing recommended: {rebalancing_recommended:,} cases")
                log_progress(f"✓ Total quantity adjustment: {total_quantity_adjustment:.1f} units/15-days")
                log_progress(f"✓ Investment impact: NEUTRAL (rebalancing only)")
        
        log_progress(f"\nNext step: Run python src/step9_*.py for additional business rule analysis")
        
    except Exception as e:
        log_progress(f"Error in imbalanced {ANALYSIS_LEVEL} allocation rule analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main() 