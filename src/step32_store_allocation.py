#!/usr/bin/env python3
"""
Step 32: Store-Level Quantity Allocation

Allocates group-level ΔQty recommendations to individual stores using weighted distribution.

Weight Formula: sales^α × capacity^β × suitability^γ
Where:
- α (sales weight): 0.6 - Sales performance importance
- β (capacity weight): 0.3 - Capacity/fixture consideration  
- γ (suitability weight): 0.1 - Style/climate suitability

Author: Data Pipeline Team
Date: 2025-08-20
Version: 1.0 - Initial Implementation

 HOW TO RUN (future-oriented allocation) — Read this before executing
 -------------------------------------------------------------------
 Overview
 - Future-oriented: You can bias allocation toward the upcoming planning window (e.g., October) instead of the immediate past.
 - Why: In late August, we should prepare for the colder incoming months (future-oriented), not reinforce the warmer recent period.

 Quick Start (period-aware)
   Command:
     PYTHONPATH=. python3 src/step32_store_allocation.py \
       --target-yyyymm 202508 \
       --period A

  Example used to produce 202508A results (YoY anchors, forward-biased)
    ENV+Command:
      PIPELINE_TARGET_YYYYMM=202508 PIPELINE_TARGET_PERIOD=A \
      FUTURE_PROTECT=1 FUTURE_FORWARD_HALVES=4 FUTURE_ANCHOR_SOURCE=spu_sales FUTURE_USE_YOY=1 \
      FUTURE_REDUCTION_SCALER=0.4 FUTURE_ADDITION_BOOST=1.25 FUTURE_AUDIT=1 \
      PYTHONPATH=. python3 src/step32_store_allocation.py --target-yyyymm 202508 --period A

 Enable future orientation (env)
 - FUTURE_PROTECT=1                      # turn on future-oriented protection/boosting (default 0)
 - FUTURE_REDUCTION_SCALER=0.5           # scale down reductions for future-oriented items (0.0–1.0)
 - FUTURE_ADDITION_BOOST=1.2             # scale up additions for future-oriented items (>1.0)
 - FUTURE_ANCHOR_MAP=path/to/map.csv     # optional mapping to mark future-oriented rows (fallback: Season labels)
   Map schema (any of these):
     • Subcategory, Future_Oriented_Flag
     • spu_code, Future_Oriented_Flag
     • Category, Subcategory, Future_Oriented_Flag

 Why these controls work (and when they don't)
 - Scaling the group ΔQty before store allocation preserves internal consistency while protecting future-oriented content from over-reduction.
 - If upstream (Step 14/17/18) has very low future-oriented share, Step 32 can only protect what exists; consider raising SEASONAL_WEIGHT upstream using future anchors (e.g., 202410A/B).

 Audit output
 - This step emits an audit CSV comparing future-oriented shares before vs after allocation to verify the policy effect.
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from typing import Dict, Tuple, Any
import argparse

# Period-aware helpers
try:
    from src.config import get_period_label
    from src.pipeline_manifest import get_manifest, register_step_output
except Exception:
    from config import get_period_label
    from pipeline_manifest import get_manifest, register_step_output

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# ===== CONFIGURATION =====
# Weight parameters for allocation
ALLOCATION_WEIGHTS = {
    'sales_alpha': 0.5,      # Sales performance weight (rebalance to reduce over-shrink bias)
    'capacity_beta': 0.3,    # Capacity/fixture weight
    'suitability_gamma': 0.2 # Style/climate suitability weight (raise suitability influence)
}

# Future-oriented allocation controls (env-driven; defaults keep legacy behavior)
FUTURE_PROTECT = os.environ.get("FUTURE_PROTECT", "0") not in ("0", "false", "False", "")
FUTURE_REDUCTION_SCALER = float(os.environ.get("FUTURE_REDUCTION_SCALER", "1.0"))  # e.g., 0.5 to halve reductions
FUTURE_ADDITION_BOOST = float(os.environ.get("FUTURE_ADDITION_BOOST", "1.0"))      # e.g., 1.2 to boost additions
FUTURE_ANCHOR_MAP_PATH = os.environ.get("FUTURE_ANCHOR_MAP", "")
FUTURE_AUDIT = os.environ.get("FUTURE_AUDIT", "0") not in ("0", "false", "False", "")
FUTURE_FORWARD_HALVES = int(os.environ.get("FUTURE_FORWARD_HALVES", "2"))  # how many A/B steps to look ahead if no map provided
FUTURE_ANCHOR_SOURCE = os.environ.get("FUTURE_ANCHOR_SOURCE", "step14")  # step14|step18|spu_sales
FUTURE_USE_YOY = os.environ.get("FUTURE_USE_YOY", "0") not in ("0", "false", "False", "")

# Input files (resolved period-aware at runtime)
ENHANCED_FAST_FISH_FILE_A = None
ENHANCED_FAST_FISH_FILE_B = None
STORE_TAGS_FILE_A = None
STORE_TAGS_FILE_B = None
STORE_ATTRIBUTES_FILE = "output/enriched_store_attributes.csv"
CLUSTER_RESULTS_FILE = "output/enhanced_clustering_results.csv"

# Output files (will be suffixed by period label + timestamp)
STORE_ALLOCATION_OUTPUT = "output/store_level_allocation_results.csv"
ALLOCATION_SUMMARY_REPORT = "output/store_allocation_summary.md"
ALLOCATION_VALIDATION_REPORT = "output/store_allocation_validation.json"

# Create output directory
os.makedirs("output", exist_ok=True)

# ===== DATA LOADING =====

def load_allocation_data(target_yyyymm: str, period: str, period_label: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all data required for store allocation (period-aware, manifest-backed)."""
    log_progress(f"📊 Loading allocation data for period {period_label}...")

    man = get_manifest().manifest if hasattr(get_manifest(), 'manifest') else (get_manifest() or {})
    step14 = (man.get('steps', {}).get('step14', {}) or {}).get('outputs', {})
    step21 = (man.get('steps', {}).get('step21', {}) or {}).get('outputs', {})
    step22 = (man.get('steps', {}).get('step22', {}) or {}).get('outputs', {})
    step32 = (man.get('steps', {}).get('step32', {}) or {}).get('outputs', {})

    # Enhanced fast fish recommendations for the period
    ff_candidates = [
        (step14.get(f"enhanced_fast_fish_format_{period_label}") or {}).get("file_path") if isinstance(step14.get(f"enhanced_fast_fish_format_{period_label}"), dict) else step14.get(f"enhanced_fast_fish_format_{period_label}"),
        (step14.get("enhanced_fast_fish_format") or {}).get("file_path") if isinstance(step14.get("enhanced_fast_fish_format"), dict) else step14.get("enhanced_fast_fish_format"),
        f"output/enhanced_fast_fish_format_{period_label}.csv",  # Fallback path
        "output/enhanced_fast_fish_format.csv"  # Generic fallback
    ]
    fast_fish_file = next((p for p in ff_candidates if p and os.path.exists(p)), None)
    if not fast_fish_file:
        raise FileNotFoundError(f"Enhanced fast fish format not found for allocation. Tried: {ff_candidates}")
    fast_fish_df = pd.read_csv(fast_fish_file)
    log_progress(f"   ✓ Loaded fast fish data: {len(fast_fish_df):,} recommendations from {fast_fish_file}")

    # Store tags CSV from Step 21
    tags_candidates = [
        (step21.get(f"df_label_tag_recommendations_csv_{period_label}") or {}).get("file_path") if isinstance(step21.get(f"df_label_tag_recommendations_csv_{period_label}"), dict) else step21.get(f"df_label_tag_recommendations_csv_{period_label}"),
        (step21.get("df_label_tag_recommendations_csv") or {}).get("file_path") if isinstance(step21.get("df_label_tag_recommendations_csv"), dict) else step21.get("df_label_tag_recommendations_csv"),
        f"output/client_desired_store_group_style_tags_targets_{period_label}_*.csv",  # Fallback pattern
        "output/client_desired_store_group_style_tags_targets.csv"  # Generic fallback
    ]
    
    # Handle glob patterns for fallback files
    import glob
    expanded_candidates = []
    for candidate in tags_candidates:
        if candidate and '*' in candidate:
            expanded_candidates.extend(glob.glob(candidate))
        else:
            expanded_candidates.append(candidate)
    
    store_tags_file = next((p for p in expanded_candidates if p and os.path.exists(p)), None)
    if not store_tags_file:
        raise FileNotFoundError(f"Store tags CSV not found for allocation. Tried: {expanded_candidates}")
    store_tags_df = pd.read_csv(store_tags_file)
    log_progress(f"   ✓ Loaded store tags: {len(store_tags_df):,} stores from {store_tags_file}")

    # Store attributes from Step 22
    attrs_candidates = [
        (step22.get(f"enriched_store_attributes_{period_label}") or {}).get("file_path") if isinstance(step22.get(f"enriched_store_attributes_{period_label}"), dict) else step22.get(f"enriched_store_attributes_{period_label}"),
        (step22.get("enriched_store_attributes") or {}).get("file_path") if isinstance(step22.get("enriched_store_attributes"), dict) else step22.get("enriched_store_attributes"),
        f"output/enriched_store_attributes_{period_label}_*.csv",  # Fallback pattern
        f"output/enriched_store_attributes_{period_label}.csv",
        STORE_ATTRIBUTES_FILE,
    ]
    
    # Handle glob patterns for store attributes
    expanded_attrs_candidates = []
    for candidate in attrs_candidates:
        if candidate and '*' in candidate:
            expanded_attrs_candidates.extend(glob.glob(candidate))
        else:
            expanded_attrs_candidates.append(candidate)
    
    store_attrs_path = next((p for p in expanded_attrs_candidates if p and os.path.exists(p)), None)
    if not store_attrs_path:
        raise FileNotFoundError(f"Store attributes not found for allocation. Tried: {expanded_attrs_candidates}")
    store_attrs_df = pd.read_csv(store_attrs_path)
    log_progress(f"   ✓ Loaded store attributes: {len(store_attrs_df):,} stores from {store_attrs_path}")

    # Cluster results from Step 32
    cluster_candidates = [
        (step32.get(f"enhanced_clustering_results_{period_label}") or {}).get("file_path") if isinstance(step32.get(f"enhanced_clustering_results_{period_label}"), dict) else step32.get(f"enhanced_clustering_results_{period_label}"),
        (step32.get("enhanced_clustering_results") or {}).get("file_path") if isinstance(step32.get("enhanced_clustering_results"), dict) else step32.get("enhanced_clustering_results"),
        CLUSTER_RESULTS_FILE,
    ]
    cluster_path = next((p for p in cluster_candidates if p and os.path.exists(p)), None)
    if not cluster_path:
        raise FileNotFoundError("Enhanced clustering results not found for allocation")
    cluster_results_df = pd.read_csv(cluster_path)
    
    # Fix Issue 1: Handle both 'Cluster' and 'cluster_id' column names
    if 'Cluster' in cluster_results_df.columns and 'cluster_id' not in cluster_results_df.columns:
        cluster_results_df = cluster_results_df.rename(columns={'Cluster': 'cluster_id'})
        log_progress(f"   🔧 Fixed column name: 'Cluster' -> 'cluster_id'")
    elif 'cluster_id' not in cluster_results_df.columns and 'Cluster' not in cluster_results_df.columns:
        available_cols = list(cluster_results_df.columns)
        raise ValueError(f"Neither 'cluster_id' nor 'Cluster' column found in {cluster_path}. Available columns: {available_cols}")
    
    log_progress(f"   ✓ Loaded cluster results: {len(cluster_results_df):,} stores from {cluster_path}")

    return fast_fish_df, store_tags_df, store_attrs_df, cluster_results_df

# ===== ALLOCATION LOGIC =====

def _load_future_anchor_map() -> Tuple[pd.DataFrame, bool]:
    """Load optional future anchor mapping CSV and return (df, available_flag)."""
    if FUTURE_ANCHOR_MAP_PATH and os.path.exists(FUTURE_ANCHOR_MAP_PATH):
        try:
            df = pd.read_csv(FUTURE_ANCHOR_MAP_PATH)
            return df, True
        except Exception as e:
            log_progress(f"⚠️ Could not read FUTURE_ANCHOR_MAP: {e}")
    return pd.DataFrame(), False

def _is_future_oriented(rec: pd.Series, anchor_df: pd.DataFrame, anchor_available: bool) -> bool:
    """Heuristic: use anchor map if available; else fallback to Season labels containing Autumn/Winter tokens."""
    try:
        if anchor_available and not anchor_df.empty:
            # Try SPU or Subcategory keys
            if 'spu_code' in rec.index and 'spu_code' in anchor_df.columns:
                key = str(rec.get('spu_code'))
                if key and key != 'nan':
                    m = anchor_df.loc[anchor_df['spu_code'].astype(str) == key]
                    if len(m) > 0:
                        val = m.iloc[0].get('Future_Oriented_Flag', 0)
                        return bool(int(val) == 1)
            if 'Subcategory' in rec.index and 'Subcategory' in anchor_df.columns:
                key = str(rec.get('Subcategory'))
                if key and key != 'nan':
                    m = anchor_df.loc[anchor_df['Subcategory'].astype(str) == key]
                    if len(m) > 0:
                        val = m.iloc[0].get('Future_Oriented_Flag', 0)
                        return bool(int(val) == 1)
        # Fallback: Season tokens
        season_val = str(rec.get('Season')) if 'Season' in rec.index else ''
        if season_val and season_val != 'nan':
            return any(tok in season_val for tok in ['Autumn', 'Winter', '秋', '冬'])
    except Exception:
        pass
    return False

def _advance_half_periods(yyyymm: str, half: str, steps: int) -> Tuple[str, str]:
    """Advance period label by N half-month steps (A/B). Returns (yyyymm, period)."""
    y = int(yyyymm[:4]); m = int(yyyymm[4:]); h = half.upper()
    for _ in range(max(0, steps)):
        if h == 'A':
            h = 'B'
        else:
            # move to next month's A
            h = 'A'
            m += 1
            if m > 12:
                m = 1
                y += 1
    return f"{y:04d}{m:02d}", h

def _try_load_period_file_for_anchor(period_label: str) -> pd.DataFrame:
    """Load a period-specific file for anchor determination based on FUTURE_ANCHOR_SOURCE.
    Priority default: step14 enhanced file; fallback to step18; as last resort empty.
    """
    try:
        src = FUTURE_ANCHOR_SOURCE.lower().strip()
        # Prefer manifest when available
        from src.pipeline_manifest import get_manifest
        man = get_manifest().manifest if hasattr(get_manifest(), 'manifest') else (get_manifest() or {})
        df = pd.DataFrame()
        if src == 'step14':
            step14 = (man.get('steps', {}).get('step14', {}) or {}).get('outputs', {})
            meta = step14.get(f"enhanced_fast_fish_format_{period_label}")
            path = None
            if isinstance(meta, dict):
                path = meta.get('file_path')
            candidates = [path, f"output/enhanced_fast_fish_format_{period_label}.csv"]
        elif src == 'step18':
            step18 = (man.get('steps', {}).get('step18', {}) or {}).get('outputs', {})
            meta = step18.get(f"sell_through_analysis_{period_label}")
            path = None
            if isinstance(meta, dict):
                path = meta.get('file_path')
            candidates = [path, f"output/fast_fish_with_sell_through_analysis_{period_label}.csv"]
        else:
            # Placeholder for future SPU sales anchors; no-op here
            candidates = []
        for p in candidates:
            if p and os.path.exists(p):
                try:
                    df = pd.read_csv(p, low_memory=False)
                    if len(df) > 0:
                        return df
                except Exception:
                    continue
    except Exception:
        pass
    return pd.DataFrame()

def _derive_future_anchor_map(target_yyyymm: str, period: str) -> Tuple[pd.DataFrame, bool]:
    """Derive a simple anchor map of future-oriented items by scanning K forward half-months.
    Mark Subcategory and SPU presence from anchor sources as future-oriented (no season hardcoding).
    """
    if FUTURE_FORWARD_HALVES <= 0:
        return pd.DataFrame(), False
    anchors: list = []
    yyyymm = str(target_yyyymm)
    half = str(period).upper()
    for k in range(1, FUTURE_FORWARD_HALVES + 1):
        yyyymm_k, half_k = _advance_half_periods(yyyymm, half, k)
        # Optionally use last-year analog for anchor loading (YoY)
        if FUTURE_USE_YOY:
            try:
                y_k = int(yyyymm_k[:4]) - 1
                m_k = int(yyyymm_k[4:6])
                yyyymm_k = f"{y_k:04d}{m_k:02d}"
            except Exception:
                pass
        period_label_k = f"{yyyymm_k}{half_k}"
        dfk = _try_load_period_file_for_anchor(period_label_k)
        if len(dfk) > 0:
            anchors.append((period_label_k, dfk))
    if not anchors:
        return pd.DataFrame(), False
    # Build map with any match across anchors
    records = []
    seen_sub = set()
    seen_spu = set()
    for lbl, dfk in anchors:
        if 'Subcategory' in dfk.columns:
            subs = dfk['Subcategory'].dropna().astype(str).unique().tolist()
            for s in subs:
                if s not in seen_sub:
                    records.append({'Subcategory': s, 'Future_Oriented_Flag': 1, 'Anchor_Source': lbl})
                    seen_sub.add(s)
        if 'spu_code' in dfk.columns:
            spus = dfk['spu_code'].dropna().astype(str).unique().tolist()
            for s in spus:
                if s not in seen_spu:
                    records.append({'spu_code': s, 'Future_Oriented_Flag': 1, 'Anchor_Source': lbl})
                    seen_spu.add(s)
    if not records:
        return pd.DataFrame(), False
    anchor_df = pd.DataFrame(records)
    # Deduplicate by key
    if 'Subcategory' in anchor_df.columns:
        anchor_df = anchor_df.drop_duplicates(subset=[c for c in ['Subcategory','spu_code'] if c in anchor_df.columns])
    return anchor_df, True

def calculate_store_weights(store_attrs_df: pd.DataFrame, cluster_results_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate allocation weights for each store based on sales, capacity, and suitability"""
    log_progress("⚖️ Calculating store allocation weights...")
    
    # Merge store attributes with cluster results
    # Handle potential duplicate column names by renaming in cluster_results_df
    cluster_subset = cluster_results_df[['str_code', 'cluster_id']].copy()
    cluster_subset = cluster_subset.rename(columns={'cluster_id': 'cluster_id_cluster'})
    weights_df = store_attrs_df.merge(cluster_subset, on='str_code', how='inner')
    # If cluster_id_cluster exists and cluster_id doesn't, use cluster_id_cluster
    if 'cluster_id_cluster' in weights_df.columns and 'cluster_id' not in weights_df.columns:
        weights_df['cluster_id'] = weights_df['cluster_id_cluster']
        weights_df = weights_df.drop(columns=['cluster_id_cluster'])
    
    # Fill missing values
    weights_df['total_sales_amt'] = weights_df['total_sales_amt'].fillna(0)
    weights_df['estimated_rack_capacity'] = weights_df['estimated_rack_capacity'].fillna(
        weights_df['estimated_rack_capacity'].median())
    weights_df['fashion_ratio'] = weights_df['fashion_ratio'].fillna(0.5)
    
    # Calculate normalized weights (0-1 range)
    # Sales weight - higher sales = higher weight
    sales_max = weights_df['total_sales_amt'].max()
    weights_df['sales_weight'] = np.where(sales_max > 0, 
                                         weights_df['total_sales_amt'] / sales_max, 
                                         0.5)
    
    # Capacity weight - higher capacity = higher weight
    capacity_max = weights_df['estimated_rack_capacity'].max()
    weights_df['capacity_weight'] = np.where(capacity_max > 0,
                                            weights_df['estimated_rack_capacity'] / capacity_max,
                                            0.5)
    
    # Suitability weight - incorporate optional climate/style suitability if available; fallback neutral 0.5
    weights_df['suitability_weight'] = 0.5
    candidate_cols = [
        'temperature_suitability',
        'climate_suitability_score',
        'style_match_score',
        'assortment_suitability_score',
        'cluster_style_suitability'
    ]
    present_candidates = [c for c in candidate_cols if c in weights_df.columns]
    if present_candidates:
        normed_list = []
        for col in present_candidates:
            series = weights_df[col].astype(float)
            # Normalize to [0,1] robustly
            s_min, s_max = series.min(), series.max()
            if pd.notna(s_min) and pd.notna(s_max) and s_max > s_min:
                normed = (series - s_min) / (s_max - s_min)
            elif s_max > 0:
                normed = series / s_max
            else:
                normed = pd.Series(0.5, index=series.index)
            normed_list.append(normed.fillna(0.5))
        if normed_list:
            weights_df['suitability_weight'] = pd.concat(normed_list, axis=1).mean(axis=1).clip(0, 1)
    
    # Apply power weights
    alpha = ALLOCATION_WEIGHTS['sales_alpha']
    beta = ALLOCATION_WEIGHTS['capacity_beta']
    gamma = ALLOCATION_WEIGHTS['suitability_gamma']
    
    weights_df['allocation_weight'] = (
        (weights_df['sales_weight'] ** alpha) *
        (weights_df['capacity_weight'] ** beta) *
        (weights_df['suitability_weight'] ** gamma)
    )
    
    # Handle any NaN or zero weights
    weights_df['allocation_weight'] = weights_df['allocation_weight'].fillna(0.01)
    weights_df['allocation_weight'] = np.maximum(weights_df['allocation_weight'], 0.001)
    
    log_progress(f"   ✓ Calculated weights for {len(weights_df)} stores")
    log_progress(f"   📊 Weight distribution: min={weights_df['allocation_weight'].min():.4f}, "
                f"max={weights_df['allocation_weight'].max():.4f}, "
                f"mean={weights_df['allocation_weight'].mean():.4f}")
    
    return weights_df

def allocate_quantities_to_stores(fast_fish_df: pd.DataFrame, store_tags_df: pd.DataFrame, 
                                 weights_df: pd.DataFrame, period: str) -> pd.DataFrame:
    """Allocate group-level ΔQty to individual stores using calculated weights"""
    log_progress(f"📦 Allocating quantities to stores for period {period}...")
    
    # ===== DUPLICATE COLUMN HANDLING =====
    # Handle duplicate columns in input DataFrames
    for df_name, df in [("fast_fish_df", fast_fish_df), ("store_tags_df", store_tags_df), ("weights_df", weights_df)]:
        if df.columns.duplicated().any():
            duplicate_cols = df.columns[df.columns.duplicated()].tolist()
            log_progress(f"   ⚠️ Removing duplicate columns from {df_name}: {duplicate_cols}")
            # Keep first occurrence of each column name
            if df_name == "fast_fish_df":
                fast_fish_df = df.loc[:, ~df.columns.duplicated(keep='first')]
            elif df_name == "store_tags_df":
                store_tags_df = df.loc[:, ~df.columns.duplicated(keep='first')]
            elif df_name == "weights_df":
                weights_df = df.loc[:, ~df.columns.duplicated(keep='first')]
    
    # ===== STORE MAPPING VALIDATION =====
    # Check for store code mismatches between Fast Fish and weights data
    if len(fast_fish_df) > 0 and 'Store_Codes_In_Group' in fast_fish_df.columns:
        # Sample some store codes from Fast Fish
        sample_ff_stores = []
        for store_codes_str in fast_fish_df['Store_Codes_In_Group'].dropna().head(3):
            try:
                codes = [int(code.strip()) for code in str(store_codes_str).split(',') if code.strip()]
                sample_ff_stores.extend(codes[:5])  # Take first 5 from each group
                if len(sample_ff_stores) >= 10:  # Enough samples
                    break
            except:
                continue
        
        if sample_ff_stores and 'str_code' in weights_df.columns:
            available_stores = set(weights_df['str_code'].unique())
            ff_stores = set(sample_ff_stores)
            overlap = ff_stores & available_stores
            
            if len(overlap) == 0:
                log_progress(f"   ⚠️ WARNING: No store code overlap between Fast Fish and weights data")
                log_progress(f"   📋 Fast Fish sample stores: {list(ff_stores)[:10]}")
                log_progress(f"   📋 Available weight stores: {list(available_stores)[:10]}")
                log_progress(f"   🔄 Will attempt allocation with available stores as fallback")
    
    # Prepare allocation results
    allocation_results = []
    # Load optional future anchor mapping or derive anchors from period labels when absent
    anchor_df, anchor_available = _load_future_anchor_map()
    if FUTURE_PROTECT and not anchor_available:
        try:
            derived_df, ok = _derive_future_anchor_map(target_yyyymm=fast_fish_df.get('PeriodYyyymm', [None])[0] if 'PeriodYyyymm' in fast_fish_df.columns else None or '',
                                                       period=period)
        except Exception:
            # Fallback: use provided args
            derived_df, ok = _derive_future_anchor_map(target_yyyymm=str(os.environ.get('PIPELINE_TARGET_YYYYMM', '')) or '', period=period)
        if ok:
            anchor_df = derived_df
            anchor_available = True
    
    # Process each recommendation
    for _, rec in fast_fish_df.iterrows():
        store_group = rec['Store_Group_Name']
        target_style_tags = rec['Target_Style_Tags']
        delta_qty = rec['ΔQty'] if 'ΔQty' in rec else 0
        
        # Skip if no change needed
        if pd.isna(delta_qty) or delta_qty == 0:
            continue
        
        # Extract store codes directly from the fast fish file
        store_codes_str = rec['Store_Codes_In_Group'] if 'Store_Codes_In_Group' in rec else ''
        if not store_codes_str or pd.isna(store_codes_str):
            log_progress(f"   ⚠️ No store codes found for group: {store_group}")
            continue
        
        # Parse store codes from comma-separated string
        try:
            store_codes = [int(code.strip()) for code in store_codes_str.split(',') if code.strip()]
        except Exception as e:
            log_progress(f"   ⚠️ Could not parse store codes for group {store_group}: {e}")
            continue
        
        if len(store_codes) == 0:
            log_progress(f"   ⚠️ No valid store codes found for group: {store_group}")
            continue
        
        # Get weights for these specific stores
        store_weights = weights_df[weights_df['str_code'].isin(store_codes)].copy()
        
        if len(store_weights) == 0:
            log_progress(f"   ⚠️ No weights found for stores in group: {store_group}")
            
            # ===== FALLBACK ALLOCATION STRATEGY =====
            # If no exact store matches, use available stores as fallback
            if len(weights_df) > 0:
                log_progress(f"   🔄 Using fallback allocation with {len(weights_df)} available stores")
                # Use a subset of available stores (e.g., top stores by weight)
                store_weights = weights_df.nlargest(min(10, len(weights_df)), 'allocation_weight').copy()
                # Update store codes to match the fallback stores
                store_codes = store_weights['str_code'].tolist()
            else:
                continue
        
        # Compute effective group ΔQty with future-oriented protection/boosting
        effective_group_delta = float(delta_qty)
        if FUTURE_PROTECT:
            try:
                is_future = _is_future_oriented(rec, anchor_df, anchor_available)
                if is_future and effective_group_delta < 0:
                    effective_group_delta = effective_group_delta * FUTURE_REDUCTION_SCALER
                elif is_future and effective_group_delta > 0:
                    effective_group_delta = effective_group_delta * FUTURE_ADDITION_BOOST
            except Exception:
                pass

        # Normalize weights to sum to 1
        total_weight = store_weights['allocation_weight'].sum()
        if total_weight > 0:
            store_weights['normalized_weight'] = store_weights['allocation_weight'] / total_weight
        else:
            store_weights['normalized_weight'] = 1.0 / len(store_weights)
        
        # Allocate quantity based on weights
        for _, store in store_weights.iterrows():
            store_code = store['str_code']
            weight = store['normalized_weight']
            allocated_qty = effective_group_delta * weight
            
            # Keep fractional allocations for accurate sum validation
            # Only include non-zero allocations (smaller than 0.01 are considered zero)
            if abs(allocated_qty) >= 0.01:
                allocation_results.append({
                    'Period': period,
                    'Store_Code': store_code,
                    'Store_Group_Name': store_group,
                    'Target_Style_Tags': target_style_tags,
                    'Category': rec.get('Category') if 'Category' in rec.index else None,
                    'Subcategory': rec.get('Subcategory') if 'Subcategory' in rec.index else None,
                    'Season': rec.get('Season') if 'Season' in rec.index else None,
                    'Gender': rec.get('Gender') if 'Gender' in rec.index else None,
                    'Location': rec.get('Location') if 'Location' in rec.index else None,
                    'Group_ΔQty': delta_qty,
                    'Effective_Group_ΔQty': effective_group_delta,
                    'Store_Allocation_Weight': weight,
                    'Allocated_ΔQty': allocated_qty,
                    'Allocation_Rationale': f"{weight:.1%} of group ΔQty={delta_qty:.0f}",
                    'Cluster_ID': store['cluster_id'],
                    'Store_Sales_Amount': store['total_sales_amt'],
                    'Store_Capacity': store['estimated_rack_capacity'],
                    'Store_Fashion_Ratio': store['fashion_ratio']
                })
    
    allocation_df = pd.DataFrame(allocation_results)
    log_progress(f"   ✅ Allocated quantities to {len(allocation_df)} store-item combinations")
    
    return allocation_df

# ===== VALIDATION AND REPORTING =====

def validate_allocations(allocation_df: pd.DataFrame, fast_fish_df: pd.DataFrame) -> Dict[str, Any]:
    """Validate that allocations sum correctly per recommendation (group + style tags) and meet business rules"""
    log_progress("🔍 Validating allocations...")
    
    validation_results = {}
    
    # Precompute allocations per (group, style tags)
    key_cols = ['Store_Group_Name', 'Target_Style_Tags']
    have_all_cols = all(c in allocation_df.columns for c in key_cols) and all(c in fast_fish_df.columns for c in key_cols)
    alloc_by_pair = None
    if have_all_cols:
        alloc_by_pair = allocation_df.groupby(key_cols)['Allocated_ΔQty'].sum()
    else:
        # Fallback to group-only validation
        alloc_by_pair = allocation_df.groupby(['Store_Group_Name'])['Allocated_ΔQty'].sum()
        key_cols = ['Store_Group_Name']

    # Check allocation accuracy - per recommendation
    group_validation = []
    for _, rec in fast_fish_df.iterrows():
        if 'ΔQty' not in rec or pd.isna(rec['ΔQty']) or rec['ΔQty'] == 0:
            continue
        key = tuple(rec[c] for c in key_cols)
        original_delta = float(rec['ΔQty'])
        # When future protection/boosting is enabled, target sum is Effective_Group_ΔQty
        if FUTURE_PROTECT and 'Effective_Group_ΔQty' in allocation_df.columns:
            # Find an example row for this key to obtain effective group delta (they are identical per group rec)
            try:
                eff = allocation_df.loc[
                    (allocation_df[key_cols[0]] == key[0]) &
                    ((len(key_cols) == 1) | (allocation_df[key_cols[1]] == key[1]))
                ].iloc[0]["Effective_Group_ΔQty"]
                original_delta = float(eff)
            except Exception:
                pass
        allocated_sum = float(alloc_by_pair.get(key, 0.0))
        difference = abs(original_delta - allocated_sum)
        accuracy = 1 - (difference / abs(original_delta)) if original_delta != 0 else 1.0

        entry = {
            'Store_Group_Name': rec['Store_Group_Name'],
            'Target_Style_Tags': rec.get('Target_Style_Tags', None),
            'Original_ΔQty': original_delta,
            'Allocated_Sum': allocated_sum,
            'Difference': difference,
            'Accuracy': accuracy,
            'Status': 'PASS' if accuracy > 0.95 else 'WARNING' if accuracy > 0.90 else 'FAIL'
        }
        group_validation.append(entry)
    
    # Overall validation metrics
    valid_groups = [g for g in group_validation if g['Status'] == 'PASS']
    warning_groups = [g for g in group_validation if g['Status'] == 'WARNING']
    failed_groups = [g for g in group_validation if g['Status'] == 'FAIL']
    
    overall_accuracy = np.mean([g['Accuracy'] for g in group_validation]) if group_validation else 1.0
    
    validation_results = {
        'total_recommendations': len(fast_fish_df),
        'total_allocations': len(allocation_df),
        'unique_stores_affected': allocation_df['Store_Code'].nunique() if len(allocation_df) > 0 else 0,
        'total_allocated_qty': allocation_df['Allocated_ΔQty'].sum() if len(allocation_df) > 0 else 0,
        'overall_accuracy': overall_accuracy,
        'groups_validated': len(group_validation),
        'groups_passed': len(valid_groups),
        'groups_warning': len(warning_groups),
        'groups_failed': len(failed_groups),
        'validation_grade': 'Excellent' if overall_accuracy >= 0.98 else 
                           'Good' if overall_accuracy >= 0.95 else 
                           'Acceptable' if overall_accuracy >= 0.90 else 'Needs Review',
        'group_level_validation': group_validation
    }
    
    log_progress(f"   📊 Allocation validation: {validation_results['validation_grade']} "
                f"({overall_accuracy:.1%} accuracy)")
    log_progress(f"   ✅ {len(valid_groups)} groups passed, {len(warning_groups)} warnings, {len(failed_groups)} failed")
    
    return validation_results

def create_future_orientation_audit(fast_fish_df: pd.DataFrame, allocation_df: pd.DataFrame, period_label: str, ts: str) -> str:
    """Emit a CSV audit comparing future-oriented shares before vs after allocation."""
    try:
        audit_rows = []
        def is_aw(season: Any) -> bool:
            s = str(season)
            return any(tok in s for tok in ['Autumn', 'Winter', '秋', '冬'])

        # Before (group-level, weighted by Group_ΔQty magnitude)
        if 'Season' in fast_fish_df.columns and 'ΔQty' in fast_fish_df.columns:
            fr = fast_fish_df.copy()
            fr['is_aw'] = fr['Season'].apply(is_aw)
            total_groups = len(fr)
            aw_groups = int(fr['is_aw'].sum())
            audit_rows.append({'stage': 'before_step32_groups', 'rows': total_groups, 'aw_groups': aw_groups, 'aw_share': aw_groups / total_groups if total_groups else 0.0})

        # After (store-level, weighted by absolute Allocated_ΔQty)
        if 'Season' in allocation_df.columns and 'Allocated_ΔQty' in allocation_df.columns:
            ar = allocation_df.copy()
            ar['is_aw'] = ar['Season'].apply(is_aw)
            total_rows = len(ar)
            aw_rows = int(ar['is_aw'].sum())
            # Quantity-weighted share
            qty = ar['Allocated_ΔQty'].abs()
            aw_qty_share = (qty[ar['is_aw']].sum() / qty.sum()) if qty.sum() else 0.0
            audit_rows.append({'stage': 'after_step32_store', 'rows': total_rows, 'aw_rows': aw_rows, 'aw_share_qty_weighted': aw_qty_share})

        audit_df = pd.DataFrame(audit_rows)
        path = f"output/allocation_season_audit_{period_label}_{ts}.csv"
        audit_df.to_csv(path, index=False)
        log_progress(f"✅ Wrote future-orientation audit: {path}")
        return path
    except Exception as e:
        log_progress(f"⚠️ Failed to write future-orientation audit: {e}")
        return ""

def create_allocation_report(allocation_df: pd.DataFrame, validation_results: Dict[str, Any], period: str) -> None:
    """Create comprehensive allocation summary report"""
    log_progress("📝 Creating allocation summary report...")
    
    # Define generic summary report path
    generic_summary_report = "output/store_allocation_summary.md"
    
    report_content = f"""# Store-Level Allocation Summary Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Period:** {period}  
**Allocation Method:** Weighted Distribution (sales^α × capacity^β × suitability^γ)

## 🎯 **ALLOCATION OVERVIEW**

- **Total Allocations:** {validation_results['total_allocations']:,}
- **Stores Affected:** {validation_results['unique_stores_affected']:,}
- **Total ΔQty Allocated:** {validation_results['total_allocated_qty']:+,.0f}
- **Validation Accuracy:** {validation_results['overall_accuracy']:.1%} ({validation_results['validation_grade']})

## ⚖️ **ALLOCATION WEIGHTS APPLIED**

- **Sales Performance (α):** {ALLOCATION_WEIGHTS['sales_alpha']:.1f} - Primary driver
- **Capacity/Fixture (β):** {ALLOCATION_WEIGHTS['capacity_beta']:.1f} - Capacity consideration
- **Style/Suitability (γ):** {ALLOCATION_WEIGHTS['suitability_gamma']:.1f} - Style alignment

## 📊 **VALIDATION RESULTS**

- **Groups Validated:** {validation_results['groups_validated']}
- **Groups Passed:** {validation_results['groups_passed']} ({validation_results['groups_passed']/validation_results['groups_validated']*100:.0f}%)
- **Groups with Warnings:** {validation_results['groups_warning']} ({validation_results['groups_warning']/validation_results['groups_validated']*100:.0f}%)
- **Groups Failed:** {validation_results['groups_failed']} ({validation_results['groups_failed']/validation_results['groups_validated']*100:.0f}%)

## 📦 **TOP STORE ALLOCATIONS**

"""
    
    # Top allocations by absolute quantity
    if len(allocation_df) > 0:
        top_allocations = allocation_df.copy()
        top_allocations['Abs_Allocated_ΔQty'] = abs(top_allocations['Allocated_ΔQty'])
        top_allocations = top_allocations.nlargest(10, 'Abs_Allocated_ΔQty')
        
        report_content += "| Store | Group | Style Tags | ΔQty | Weight | Rationale |\n"
        report_content += "|-------|-------|------------|------|--------|-----------|\n"
        
        for _, alloc in top_allocations.iterrows():
            report_content += f"| {alloc['Store_Code']} | {alloc['Store_Group_Name']} | {alloc['Target_Style_Tags']} | {alloc['Allocated_ΔQty']:+.0f} | {alloc['Store_Allocation_Weight']:.1%} | {alloc['Allocation_Rationale']} |\n"
    
    report_content += f"""

## 📈 **ALLOCATION DISTRIBUTION**

- **Average Allocation per Store:** {allocation_df['Allocated_ΔQty'].mean():+.1f} units
- **Median Allocation:** {allocation_df['Allocated_ΔQty'].median():+.1f} units
- **Max Positive Allocation:** {allocation_df['Allocated_ΔQty'].max():+.0f} units
- **Max Negative Allocation:** {allocation_df['Allocated_ΔQty'].min():+.0f} units

## 🚀 **IMPLEMENTATION READY**

### **Deliverables Generated:**
- ✅ Store-level allocation results
- ✅ Allocation validation metrics
- ✅ Business-ready summary report

### **Next Steps:**
1. Review allocations for business logic alignment
2. Validate with store managers for high-impact changes
3. Integrate with inventory management systems
4. Monitor implementation results

---

*Report generated by Store Allocation System v1.0*
"""
    
    # Save timestamped version (for backup/inspection)
    with open(ALLOCATION_SUMMARY_REPORT, 'w') as f:
        f.write(report_content)
    log_progress(f"✅ Created timestamped allocation report: {ALLOCATION_SUMMARY_REPORT}")
    
    # Save generic version (for pipeline flow)
    with open(generic_summary_report, 'w') as f:
        f.write(report_content)
    log_progress(f"✅ Created generic allocation report: {generic_summary_report}")

# ===== MAIN EXECUTION =====

def process_period_allocation(target_yyyymm: str, period: str) -> pd.DataFrame:
    """Process allocation for a single period (period-aware)."""
    period_label = get_period_label(target_yyyymm, period)
    log_progress(f"🚀 Starting Step 32 Store Allocation for Period {period_label}...")
    
    # Load data
    fast_fish_df, store_tags_df, store_attrs_df, cluster_results_df = load_allocation_data(target_yyyymm, period, period_label)
    
    # Calculate weights
    weights_df = calculate_store_weights(store_attrs_df, cluster_results_df)
    
    # Allocate quantities
    allocation_df = allocate_quantities_to_stores(fast_fish_df, store_tags_df, weights_df, period)
    
    # Validate allocations
    validation_results = validate_allocations(allocation_df, fast_fish_df)
    
    # Save validation results (DUAL OUTPUT PATTERN)
    # Define generic validation report path
    generic_validation_report = "output/store_allocation_validation.json"
    
    # Save timestamped version (for backup/inspection)
    with open(ALLOCATION_VALIDATION_REPORT, 'w') as f:
        json.dump(validation_results, f, indent=2, default=str)
    log_progress(f"✅ Saved timestamped validation results: {ALLOCATION_VALIDATION_REPORT}")
    
    # Save generic version (for pipeline flow)
    with open(generic_validation_report, 'w') as f:
        json.dump(validation_results, f, indent=2, default=str)
    log_progress(f"✅ Saved generic validation results: {generic_validation_report}")
    
    # Create report
    create_allocation_report(allocation_df, validation_results, period)
    # Audit future orientation
    if FUTURE_AUDIT:
        try:
            period_label = get_period_label(target_yyyymm, period)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            create_future_orientation_audit(fast_fish_df, allocation_df, period_label, ts)
        except Exception:
            pass
    
    return allocation_df, validation_results

def main():
    """Main function for store allocation (period-aware)"""
    parser = argparse.ArgumentParser(description='Allocate group-level recommendations to individual stores (period-aware)')
    parser.add_argument('--period', choices=['A', 'B'], required=True, help='Target period for allocation (A or B)')
    parser.add_argument('--target-yyyymm', required=True, help='Target year-month (YYYYMM)')
    args = parser.parse_args()

    period_label = get_period_label(args.target_yyyymm, args.period)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    # DUAL OUTPUT PATTERN - Define both timestamped and generic versions
    global STORE_ALLOCATION_OUTPUT, ALLOCATION_SUMMARY_REPORT, ALLOCATION_VALIDATION_REPORT
    
    # Timestamped versions (for backup/inspection)
    timestamped_allocation_output = f"output/store_level_allocation_results_{period_label}_{ts}.csv"
    timestamped_summary_report = f"output/store_allocation_summary_{period_label}_{ts}.md"
    timestamped_validation_report = f"output/store_allocation_validation_{period_label}_{ts}.json"
    
    # Generic versions (for pipeline flow)
    generic_allocation_output = "output/store_level_allocation_results.csv"
    generic_summary_report = "output/store_allocation_summary.md"
    generic_validation_report = "output/store_allocation_validation.json"
    
    # Use timestamped versions for manifest registration
    STORE_ALLOCATION_OUTPUT = timestamped_allocation_output
    ALLOCATION_SUMMARY_REPORT = timestamped_summary_report
    ALLOCATION_VALIDATION_REPORT = timestamped_validation_report

    # Process allocation
    allocation_df, validation_results = process_period_allocation(args.target_yyyymm, args.period)

    # Create adds-only and reduces-only diagnostic views (do not alter main output schema)
    if len(allocation_df) > 0:
        sign = np.where(allocation_df['Allocated_ΔQty'] > 0, 'Add', np.where(allocation_df['Allocated_ΔQty'] < 0, 'Reduce', 'No-Change'))
        adds_df = allocation_df[sign == 'Add']
        reduces_df = allocation_df[sign == 'Reduce']
        adds_path = f"output/store_level_allocation_adds_{period_label}_{ts}.csv"
        reduces_path = f"output/store_level_allocation_reduces_{period_label}_{ts}.csv"
        try:
            # Persist schema-compatible views (drop helper columns)
            adds_df.drop(columns=['Effective_Group_ΔQty'], errors='ignore').to_csv(adds_path, index=False)
            reduces_df.drop(columns=['Effective_Group_ΔQty'], errors='ignore').to_csv(reduces_path, index=False)
            log_progress(f"✅ Saved adds-only view: {adds_path}")
            log_progress(f"✅ Saved reduces-only view: {reduces_path}")
        except Exception as e:
            log_progress(f"⚠️ Could not save adds/reduces views: {e}")

    # Save results (DUAL OUTPUT PATTERN)
    # Persist main results without helper columns to keep schema unchanged
    clean_allocation_df = allocation_df.drop(columns=['Effective_Group_ΔQty'], errors='ignore')
    
    # Save timestamped version (for backup/inspection)
    clean_allocation_df.to_csv(STORE_ALLOCATION_OUTPUT, index=False)
    log_progress(f"✅ Saved timestamped allocation results: {STORE_ALLOCATION_OUTPUT}")
    
    # Create symlink for generic version (for pipeline flow)
    if os.path.exists(generic_allocation_output) or os.path.islink(generic_allocation_output):
        os.remove(generic_allocation_output)
    os.symlink(os.path.basename(STORE_ALLOCATION_OUTPUT), generic_allocation_output)
    log_progress(f"✅ Created symlink: {generic_allocation_output} -> {STORE_ALLOCATION_OUTPUT}")

    # Register outputs in manifest
    try:
        meta = {
            'target_year': int(args.target_yyyymm[:4]),
            'target_month': int(args.target_yyyymm[4:]),
            'target_period': args.period,
            'records': len(allocation_df)
        }
        register_step_output('step32', 'store_level_allocation_results', STORE_ALLOCATION_OUTPUT, meta)
        register_step_output('step32', f'store_level_allocation_results_{period_label}', STORE_ALLOCATION_OUTPUT, meta)
        register_step_output('step32', 'store_allocation_summary', ALLOCATION_SUMMARY_REPORT, meta)
        register_step_output('step32', f'store_allocation_summary_{period_label}', ALLOCATION_SUMMARY_REPORT, meta)
        register_step_output('step32', 'store_allocation_validation', ALLOCATION_VALIDATION_REPORT, meta)
        register_step_output('step32', f'store_allocation_validation_{period_label}', ALLOCATION_VALIDATION_REPORT, meta)
        # Register diagnostic views if they exist
        try:
            if os.path.exists(adds_path):
                register_step_output('step32', 'store_level_allocation_adds', adds_path, meta)
                register_step_output('step32', f'store_level_allocation_adds_{period_label}', adds_path, meta)
            if os.path.exists(reduces_path):
                register_step_output('step32', 'store_level_allocation_reduces', reduces_path, meta)
                register_step_output('step32', f'store_level_allocation_reduces_{period_label}', reduces_path, meta)
        except Exception:
            pass
    except Exception:
        pass

    # Summary
    log_progress(f"\n🎯 ALLOCATION SUMMARY FOR PERIOD {period_label}:")
    log_progress(f"   📦 Total allocations: {len(allocation_df):,}")
    log_progress(f"   🏪 Unique stores affected: {allocation_df['Store_Code'].nunique() if len(allocation_df) > 0 else 0:,}")
    log_progress(f"   📈 Total ΔQty allocated: {allocation_df['Allocated_ΔQty'].sum() if len(allocation_df) > 0 else 0:+,.0f}")
    log_progress(f"   📊 Validation accuracy: {validation_results['overall_accuracy']:.1%} ({validation_results['validation_grade']})")
    
    log_progress(f"\n📁 Generated Files:")
    log_progress(f"   • {STORE_ALLOCATION_OUTPUT}")
    log_progress(f"   • {ALLOCATION_SUMMARY_REPORT}")
    log_progress(f"   • {ALLOCATION_VALIDATION_REPORT}")

if __name__ == "__main__":
    main()
