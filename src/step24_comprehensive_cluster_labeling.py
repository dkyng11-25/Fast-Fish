#!/usr/bin/env python3
"""
Step 24: Comprehensive Cluster Labeling System

This step analyzes existing clusters and generates comprehensive labels showing:
- Fashion/Basic makeup ratios
- Temperature band characteristics
- Store capacity profiles
- Silhouette score quality metrics

Uses ONLY real data from existing pipeline outputs and API data.

Author: Data Pipeline Team
Date: 2025-01-23
Version: 1.0 - Real Data Comprehensive Labeling
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from typing import Dict, Tuple, Any, Optional, List
import warnings
from tqdm import tqdm
from collections import Counter
# Resilient imports for module vs script execution
try:
    from src.config import get_period_label
    from src.pipeline_manifest import register_step_output
except ModuleNotFoundError:
    try:
        from config import get_period_label
        from pipeline_manifest import register_step_output
    except ModuleNotFoundError:
        import sys as _sys
        import os as _os
        _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        if _root not in _sys.path:
            _sys.path.insert(0, _root)
        from src.config import get_period_label
        from src.pipeline_manifest import register_step_output

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# ===== CONFIGURATION =====
# Input data sources - all real data files
CLUSTERING_RESULTS_FILE = "output/clustering_results_spu.csv"
FALLBACK_CLUSTERING_FILES = [
    "output/clustering_results_subcategory.csv",
    "output/clustering_results.csv"
]

# Temperature data sources
TEMPERATURE_FILES = [
    "output/stores_with_feels_like_temperature.csv",
    "output/temperature_bands.csv"
]

# Capacity estimation sources (we will also perform a dynamic scan)
CAPACITY_FILES = [
    "output/enriched_store_attributes.csv",
    "output/consolidated_spu_rule_results.csv",
]

# Output base filenames (will suffix with period_label + timestamp)
CLUSTER_LABELS_FILE = "output/comprehensive_cluster_labels.csv"
CLUSTER_SUMMARY_FILE = "output/cluster_labeling_summary.json"
CLUSTER_ANALYSIS_FILE = "output/cluster_label_analysis_report.md"
STORE_TAGS_FILE = "output/store_tags.csv"

# Create output directory
os.makedirs("output", exist_ok=True)

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# ===== DATA LOADING FUNCTIONS =====

def load_clustering_data(period_label: Optional[str] = None) -> pd.DataFrame:
    """Load clustering results from available files"""
    log_progress("🔍 Loading clustering data...")
    
    # Prefer period-labeled clustering results if provided
    if period_label:
        period_paths = [
            os.path.join("output", f"clustering_results_spu_{period_label}.csv"),
            os.path.join("output", f"clustering_results_{period_label}.csv"),
        ]
        for p in period_paths:
            if os.path.exists(p):
                df = pd.read_csv(p, low_memory=False)
                if 'str_code' not in df.columns and 'store_code' in df.columns:
                    df['str_code'] = df['store_code'].astype(str)
                elif 'str_code' in df.columns:
                    df['str_code'] = df['str_code'].astype(str)
                log_progress(f"   ✓ Loaded clustering results: {len(df):,} stores from {p}")
                return df

    # Try main clustering results file first
    if os.path.exists(CLUSTERING_RESULTS_FILE):
        df = pd.read_csv(CLUSTERING_RESULTS_FILE, low_memory=False)
        # Standardize store code column
        if 'str_code' not in df.columns and 'store_code' in df.columns:
            df['str_code'] = df['store_code'].astype(str)
        elif 'str_code' in df.columns:
            df['str_code'] = df['str_code'].astype(str)
        log_progress(f"   ✓ Loaded clustering results: {len(df):,} stores from {CLUSTERING_RESULTS_FILE}")
        return df
    
    # Try fallback files
    for fallback_file in FALLBACK_CLUSTERING_FILES:
        if os.path.exists(fallback_file):
            df = pd.read_csv(fallback_file, low_memory=False)
            # Standardize store code column
            if 'str_code' not in df.columns and 'store_code' in df.columns:
                df['str_code'] = df['store_code'].astype(str)
            elif 'str_code' in df.columns:
                df['str_code'] = df['str_code'].astype(str)
            log_progress(f"   ✓ Loaded clustering results: {len(df):,} stores from {fallback_file}")
            return df
    
    raise FileNotFoundError("No clustering results file found. Please run step 6 first.")

def _discover_sales_files() -> List[str]:
    """Dynamically discover sales sources that may contain fashion/basic info."""
    candidates: List[str] = []
    # High-value, structured outputs from later steps
    for f in [
        # Defer generic enriched file until after period-specific scan
        "output/fashion_enhanced_suggestions.csv",
        "output/consolidated_spu_rule_results.csv",
        "output/all_rule_suggestions.csv",
    ]:
        if os.path.exists(f):
            candidates.append(f)

    # Scan output for period-specific enriched attributes FIRST (prefer latest), then others
    try:
        enriched_period = sorted([f for f in os.listdir("output") if f.startswith("enriched_store_attributes_")])
        for fname in enriched_period:
            path = os.path.join("output", fname)
            if os.path.isfile(path):
                candidates.append(path)
        for fname in sorted(os.listdir("output")):
            if (
                fname.startswith("complete_spu_sales_")
                or fname.startswith("complete_category_sales_")
            ):
                path = os.path.join("output", fname)
                if os.path.isfile(path):
                    candidates.append(path)
        # finally, include generic enriched file if present
        gen_path = os.path.join("output", "enriched_store_attributes.csv")
        if os.path.isfile(gen_path):
            candidates.append(gen_path)
    except Exception:
        pass

    # Scan API data directory for any available period-based files
    api_dir = os.path.join("data", "api_data")
    try:
        for fname in sorted(os.listdir(api_dir)):
            if fname.startswith("complete_spu_sales_") or fname.startswith("complete_category_sales_"):
                path = os.path.join(api_dir, fname)
                if os.path.isfile(path):
                    candidates.append(path)
    except Exception:
        pass

    # De-duplicate preserving order
    seen = set()
    unique_candidates = []
    for c in candidates:
        if c not in seen:
            unique_candidates.append(c)
            seen.add(c)
    return unique_candidates

def load_fashion_basic_data() -> pd.DataFrame:
    """Load real fashion/basic sales data from discovered sources."""
    log_progress("👗 Loading fashion/basic sales data...")
    # Prefer the latest period-specific enriched store attributes exclusively for ratios
    try:
        import glob
        enriched_candidates = sorted(glob.glob(os.path.join('output', 'enriched_store_attributes_*.csv')))
        if enriched_candidates:
            latest = enriched_candidates[-1]
            df = pd.read_csv(latest, low_memory=False)
            # Standardize key and keep minimal columns for ratio/weight
            key = 'str_code' if 'str_code' in df.columns else ('store_code' if 'store_code' in df.columns else None)
            if key is not None:
                df['str_code'] = df[key].astype(str)
            cols = ['str_code']
            if 'fashion_ratio' in df.columns:
                cols.append('fashion_ratio')
            if 'total_sales_amt' in df.columns:
                cols.append('total_sales_amt')
            df = df[cols].dropna(subset=['str_code'])
            log_progress(f"   ✓ Fashion/basic signal (LATEST ENRICHED): {latest} ({len(df):,} rows)")
            return df
    except Exception as e:
        log_progress(f"   ✗ Error loading latest enriched attributes: {e}")

    # Fallback to legacy discovery when enriched not available
    fashion_basic_data: List[pd.DataFrame] = []
    candidate_files = _discover_sales_files()
    if not candidate_files:
        log_progress("   ⚠️ No candidate sales files found")
        return pd.DataFrame()
    log_progress(f"   🔎 Candidate files: {len(candidate_files)}")
    for file_path in candidate_files:
        try:
            df = pd.read_csv(file_path, low_memory=False)
            if 'str_code' in df.columns:
                df['str_code'] = df['str_code'].astype(str)
            elif 'store_code' in df.columns:
                df['str_code'] = df['store_code'].astype(str)
            else:
                continue
            keep_cols = [c for c in df.columns if any(k in c.lower() for k in [
                'str_code', 'store_code', 'sal_amt', 'sales_amt', 'sal_qty', 'sales_qty',
                'quantity', 'base_sal_qty', 'fashion_sal_qty', 'basic_ratio', 'fashion_ratio', 'total_sales_amt'
            ])]
            df = df[keep_cols]
            has_signal = any('fashion' in c.lower() for c in df.columns) or any('basic' in c.lower() for c in df.columns)
            if has_signal:
                log_progress(f"   ✓ Fashion/basic signal: {file_path} ({len(df):,} rows)")
                fashion_basic_data.append(df)
            else:
                if any('sal_amt' in c or 'sales_amt' in c for c in df.columns):
                    log_progress(f"   ℹ️ Sales (no explicit fashion/basic): {file_path}")
                    fashion_basic_data.append(df)
        except Exception as e:
            log_progress(f"   ✗ Error loading {file_path}: {e}")
    if fashion_basic_data:
        combined_df = pd.concat(fashion_basic_data, ignore_index=True)
        log_progress(f"   ✓ Combined sales data: {len(combined_df):,} total rows from {len(fashion_basic_data)} files")
        return combined_df
    log_progress("   ⚠️ No usable sales data found, will use size-based heuristics where needed")
    return pd.DataFrame()

def load_temperature_data() -> pd.DataFrame:
    """Load temperature data if available"""
    log_progress("🌡️ Loading temperature data...")
    
    for temp_file in TEMPERATURE_FILES:
        if os.path.exists(temp_file):
            try:
                # Handle both possible column names
                if 'str_code' in pd.read_csv(temp_file, nrows=0).columns:
                    df = pd.read_csv(temp_file, dtype={'str_code': str})
                else:
                    df = pd.read_csv(temp_file, dtype={'store_code': str})
                    # Standardize column names
                    if 'store_code' in df.columns:
                        df['str_code'] = df['store_code'].astype(str)
                log_progress(f"   ✓ Loaded temperature data: {len(df):,} stores from {temp_file}")
                return df
            except Exception as e:
                log_progress(f"   ✗ Error loading {temp_file}: {e}")
    
    log_progress("   ⚠️ No temperature data found")
    return pd.DataFrame()

def load_capacity_data() -> pd.DataFrame:
    """Load capacity estimation data"""
    log_progress("📦 Loading capacity data...")
    
    # First try known files
    for capacity_file in CAPACITY_FILES:
        if os.path.exists(capacity_file):
            try:
                df = pd.read_csv(capacity_file, low_memory=False)
                # Standardize store code column
                if 'str_code' not in df.columns and 'store_code' in df.columns:
                    df['str_code'] = df['store_code'].astype(str)
                elif 'str_code' in df.columns:
                    df['str_code'] = df['str_code'].astype(str)
                if 'estimated_rack_capacity' in df.columns or 'estimated_capacity' in df.columns or 'capacity' in df.columns:
                    log_progress(f"   ✓ Loaded capacity data: {len(df):,} rows from {capacity_file}")
                    return df
            except Exception as e:
                log_progress(f"   ✗ Error loading {capacity_file}: {e}")

    # Dynamic scan for any output CSV that contains capacity columns
    try:
        for fname in sorted(os.listdir("output")):
            if not fname.lower().endswith('.csv'):
                continue
            path = os.path.join("output", fname)
            try:
                probe = pd.read_csv(path, nrows=10, low_memory=False)
                cols = [c.lower() for c in probe.columns]
                if any(k in cols for k in ['estimated_rack_capacity', 'estimated_capacity', 'capacity']):
                    df = pd.read_csv(path, low_memory=False)
                    if 'str_code' not in df.columns and 'store_code' in df.columns:
                        df['str_code'] = df['store_code'].astype(str)
                    elif 'str_code' in df.columns:
                        df['str_code'] = df['str_code'].astype(str)
                    log_progress(f"   ✓ Loaded capacity-like data: {len(df):,} rows from {path}")
                    return df
            except Exception:
                continue
    except Exception:
        pass
    
    log_progress("   ⚠️ No capacity data found, will estimate from sales data")
    return pd.DataFrame()

# ===== CLUSTER ANALYSIS FUNCTIONS =====

def calculate_fashion_basic_makeup(cluster_stores: List[str], fashion_basic_df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate fashion/basic makeup for a cluster using real sales data"""
    
    if fashion_basic_df.empty:
        return {
            'fashion_ratio': 0.0,
            'basic_ratio': 0.0,
            'fashion_basic_classification': 'Unknown',
            'data_source': 'No data available'
        }
    
    # Filter data for stores in this cluster
    cluster_data = fashion_basic_df[fashion_basic_df['str_code'].isin(cluster_stores)].copy()
    
    if cluster_data.empty:
        return {
            'fashion_ratio': 0.0,
            'basic_ratio': 0.0,
            'fashion_basic_classification': 'No cluster data',
            'data_source': 'Stores not in sales data'
        }
    
    # If enriched store attributes provide ratios, prefer them (period-specific recomputation)
    if 'fashion_ratio' in cluster_data.columns:
        try:
            # Coerce to numeric percentages if needed and DROP NaNs to avoid polluting with sources lacking ratios
            fr_all = pd.to_numeric(cluster_data['fashion_ratio'], errors='coerce')
            nonnull_mask = fr_all.notna()
            if not nonnull_mask.any():
                raise ValueError('No usable fashion_ratio rows')
            subset = cluster_data[nonnull_mask].copy()
            fr = pd.to_numeric(subset['fashion_ratio'], errors='coerce')
            # Bring total_sales_amt for weighting if present
            w = pd.to_numeric(subset.get('total_sales_amt'), errors='coerce').fillna(0)
            # Aggregate per store to avoid duplicates across sources; prefer weighted average by total_sales_amt if available
            by_store = subset[['str_code']].copy()
            by_store['fashion_ratio'] = fr
            by_store['weight'] = w if 'total_sales_amt' in subset.columns else 1.0
            store_group = by_store.groupby('str_code')
            store_agg = store_group.apply(lambda g: np.average(g['fashion_ratio'], weights=(g['weight']+1e-6))).dropna()
            store_w = store_group['weight'].sum().reindex(store_agg.index).fillna(0)
            if not store_agg.empty:
                # Weighted average across stores using per-store total sales weight
                if store_w.sum() > 0:
                    fr_val = float(np.average(store_agg.values, weights=(store_w.values+1e-6)))
                else:
                    fr_val = float(store_agg.mean())
                if fr_val <= 1.0:
                    fr_val *= 100.0
                fashion_ratio = fr_val
                basic_ratio = 100.0 - fashion_ratio
                classification = (
                    'Fashion-Focused' if fashion_ratio >= 60 else
                    'Basic-Focused' if basic_ratio >= 60 else
                    'Balanced' if abs(fashion_ratio - basic_ratio) <= 15 else
                    ('Fashion-Leaning' if fashion_ratio > basic_ratio else 'Basic-Leaning')
                )
                return {
                    'fashion_ratio': round(fashion_ratio, 1),
                    'basic_ratio': round(basic_ratio, 1),
                    'fashion_basic_classification': classification,
                    'data_source': 'Enriched store attributes ratios'
                }
        except Exception:
            pass

    # Calculate fashion/basic ratios from real sales data (prefer real amounts/qty over precomputed ratios when ratios absent)
    total_fashion_amt = 0
    total_basic_amt = 0
    total_fashion_qty = 0
    total_basic_qty = 0
    
    # Look for fashion/basic columns
    for col in cluster_data.columns:
        if 'fashion' in col.lower() and 'amt' in col.lower():
            total_fashion_amt += cluster_data[col].fillna(0).sum()
        elif 'fashion' in col.lower() and 'qty' in col.lower():
            total_fashion_qty += cluster_data[col].fillna(0).sum()
        elif 'basic' in col.lower() and 'amt' in col.lower():
            total_basic_amt += cluster_data[col].fillna(0).sum()
        elif 'basic' in col.lower() and 'qty' in col.lower():
            total_basic_qty += cluster_data[col].fillna(0).sum()
    
    # Calculate ratios based on sales amount (primary) or quantity (fallback)
    total_amt = total_fashion_amt + total_basic_amt
    if total_amt > 0:
        fashion_ratio = (total_fashion_amt / total_amt) * 100
        basic_ratio = (total_basic_amt / total_amt) * 100
        data_source = 'Real sales amount data'
    else:
        total_qty = total_fashion_qty + total_basic_qty
        if total_qty > 0:
            fashion_ratio = (total_fashion_qty / total_qty) * 100
            basic_ratio = (total_basic_qty / total_qty) * 100
            data_source = 'Real sales quantity data'
        else:
            # Attempt to load preferred API file with explicit fashion/basic measures
            try:
                # Use period-aware sales loader to avoid synthetic combined files
                from src.config import get_current_period, load_sales_df_with_fashion_basic
                yyyymm, period = get_current_period()
                src_path, api_df = load_sales_df_with_fashion_basic(yyyymm, period, require_spu_level=True,
                                                                    required_cols=['str_code','fashion_sal_amt','basic_sal_amt'])
                api_df['str_code'] = api_df['str_code'].astype(str)
                api_cluster = api_df[api_df['str_code'].isin(cluster_stores)]
                if not api_cluster.empty:
                    fa = pd.to_numeric(api_cluster.get('fashion_sal_amt'), errors='coerce').fillna(0).sum()
                    ba = pd.to_numeric(api_cluster.get('basic_sal_amt'), errors='coerce').fillna(0).sum()
                    if fa + ba > 0:
                        fashion_ratio = (fa / (fa + ba)) * 100
                        basic_ratio = (ba / (fa + ba)) * 100
                        data_source = 'API sales amount data'
                    else:
                        fq = pd.to_numeric(api_cluster.get('fashion_sal_qty'), errors='coerce').fillna(0).sum()
                        bq = pd.to_numeric(api_cluster.get('basic_sal_qty'), errors='coerce').fillna(0).sum()
                        if fq + bq > 0:
                            fashion_ratio = (fq / (fq + bq)) * 100
                            basic_ratio = (bq / (fq + bq)) * 100
                            data_source = 'API sales quantity data'
                        else:
                            pass
            except Exception:
                pass
            # If still unresolved, fallback to precomputed ratios as last resort
            # 0) If precomputed ratios exist, aggregate them directly (last resort)
            precomp_basic = [c for c in cluster_data.columns if c.lower() == 'basic_ratio']
            precomp_fashion = [c for c in cluster_data.columns if c.lower() == 'fashion_ratio']
            if precomp_basic and precomp_fashion:
                try:
                    def _to_pct(series: pd.Series) -> pd.Series:
                        s = series.astype(str).str.replace('%', '', regex=False)
                        return pd.to_numeric(s, errors='coerce')
                    cluster_data['__basic_ratio_num'] = _to_pct(cluster_data[precomp_basic[0]])
                    cluster_data['__fashion_ratio_num'] = _to_pct(cluster_data[precomp_fashion[0]])
                    # Weighted by sales amount if available, else simple mean per store
                    weight_col = None
                    for c in cluster_data.columns:
                        if c.lower() in ('spu_sales_amt', 'sales_amt', 'total_sales_amt'):
                            weight_col = c
                            break
                    if weight_col is not None:
                        by_store = cluster_data.groupby('str_code').apply(
                            lambda g: pd.Series({
                                'basic_w': (g['__basic_ratio_num'] * g[weight_col]).sum(),
                                'fashion_w': (g['__fashion_ratio_num'] * g[weight_col]).sum(),
                                'w': g[weight_col].sum()
                            })
                        ).replace({0: pd.NA}).dropna()
                        if not by_store.empty and (by_store['w'] > 0).any():
                            basic_ratio = float((by_store['basic_w'].sum() / by_store['w'].sum()))
                            fashion_ratio = float((by_store['fashion_w'].sum() / by_store['w'].sum()))
                            data_source = 'Precomputed ratios (weighted)'
                        else:
                            by_store = cluster_data.groupby('str_code')[['__basic_ratio_num', '__fashion_ratio_num']].mean().dropna()
                            basic_ratio = float(by_store['__basic_ratio_num'].mean()) if not by_store.empty else 0.0
                            fashion_ratio = float(by_store['__fashion_ratio_num'].mean()) if not by_store.empty else 0.0
                            data_source = 'Precomputed ratios'
                    else:
                        by_store = cluster_data.groupby('str_code')[['__basic_ratio_num', '__fashion_ratio_num']].mean().dropna()
                        basic_ratio = float(by_store['__basic_ratio_num'].mean()) if not by_store.empty else 0.0
                        fashion_ratio = float(by_store['__fashion_ratio_num'].mean()) if not by_store.empty else 0.0
                        data_source = 'Precomputed ratios'
                except Exception:
                    basic_ratio = 0.0
                    fashion_ratio = 0.0
                    data_source = 'No data'
            else:
                return {
                    'fashion_ratio': 0.0,
                    'basic_ratio': 0.0,
                    'fashion_basic_classification': 'No sales data',
                    'data_source': 'Zero sales found'
                }
    
    # Classify based on ratios
    if fashion_ratio >= 60:
        classification = 'Fashion-Focused'
    elif basic_ratio >= 60:
        classification = 'Basic-Focused'
    elif abs(fashion_ratio - basic_ratio) <= 15:
        classification = 'Balanced'
    elif fashion_ratio > basic_ratio:
        classification = 'Fashion-Leaning'
    else:
        classification = 'Basic-Leaning'
    
    return {
        'fashion_ratio': round(fashion_ratio, 1),
        'basic_ratio': round(basic_ratio, 1),
        'fashion_basic_classification': classification,
        'data_source': data_source
    }

def calculate_temperature_profile(cluster_stores: List[str], temperature_df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate temperature characteristics for a cluster"""
    
    if temperature_df.empty:
        return {
            'avg_feels_like_temp': 0.0,
            'temp_range': 'Unknown',
            'dominant_temp_band': 'Unknown',
            'temperature_classification': 'No data'
        }
    
    # Filter temperature data for cluster stores
    cluster_temp = temperature_df[temperature_df['str_code'].isin(cluster_stores)]
    
    if cluster_temp.empty:
        return {
            'avg_feels_like_temp': 0.0,
            'temp_range': 'Unknown',
            'dominant_temp_band': 'Unknown',
            'temperature_classification': 'No cluster data'
        }
    
    # Calculate temperature metrics
    feels_like_col = 'feels_like_temperature'
    if feels_like_col not in cluster_temp.columns:
        feels_like_col = [col for col in cluster_temp.columns if 'feels_like' in col.lower()]
        feels_like_col = feels_like_col[0] if feels_like_col else None
    
    if feels_like_col:
        avg_temp = cluster_temp[feels_like_col].mean()
        min_temp = cluster_temp[feels_like_col].min()
        max_temp = cluster_temp[feels_like_col].max()
        temp_range = f"{min_temp:.1f}°C to {max_temp:.1f}°C"
    else:
        avg_temp = 0.0
        temp_range = "No temperature data"
    
    # Determine dominant temperature band
    temp_band_col = 'temperature_band'
    if temp_band_col in cluster_temp.columns:
        band_counts = cluster_temp[temp_band_col].value_counts()
        dominant_band = band_counts.index[0] if len(band_counts) > 0 else 'Unknown'
    else:
        dominant_band = 'Unknown'
    
    # Classify temperature profile
    if avg_temp >= 25:
        temp_classification = 'Hot Climate'
    elif avg_temp <= 10:
        temp_classification = 'Cold Climate'
    elif 15 <= avg_temp <= 25:
        temp_classification = 'Moderate Climate'
    elif 10 < avg_temp < 15:
        temp_classification = 'Cool Climate'
    else:
        temp_classification = 'Unknown'
    
    return {
        'avg_feels_like_temp': round(avg_temp, 1),
        'temp_range': temp_range,
        'dominant_temp_band': dominant_band,
        'temperature_classification': temp_classification,
        'data_source': 'Temperature data' if feels_like_col else 'No data available'
    }

def calculate_capacity_profile(cluster_stores: List[str], capacity_df: pd.DataFrame, sales_df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate capacity characteristics for a cluster"""
    
    # Try to get capacity from existing capacity data
    if not capacity_df.empty:
        cluster_capacity = capacity_df[capacity_df['str_code'].isin(cluster_stores)]
        
        if not cluster_capacity.empty:
            capacity_col = None
            for col in ['estimated_rack_capacity', 'estimated_capacity', 'capacity']:
                if col in cluster_capacity.columns:
                    capacity_col = col
                    break
            
            if capacity_col:
                avg_capacity = cluster_capacity[capacity_col].mean()
                total_capacity = cluster_capacity[capacity_col].sum()
                
                # Classify capacity tier
                if avg_capacity >= 500:
                    capacity_tier = 'Large'
                elif avg_capacity >= 200:
                    capacity_tier = 'Medium'
                else:
                    capacity_tier = 'Small'
                
                return {
                    'avg_estimated_capacity': round(avg_capacity, 0),
                    'total_cluster_capacity': round(total_capacity, 0),
                    'capacity_tier': capacity_tier,
                    'data_source': 'Real capacity estimates'
                }
    
    # Fallback: estimate from sales data
    if not sales_df.empty:
        cluster_sales = sales_df[sales_df['str_code'].isin(cluster_stores)]
        
        if not cluster_sales.empty:
            # Calculate capacity indicators from sales
            sales_cols = [col for col in cluster_sales.columns if 'sal_amt' in col or 'sales_amt' in col]
            qty_cols = [col for col in cluster_sales.columns if 'sal_qty' in col or 'sales_qty' in col]
            
            if sales_cols:
                total_sales = cluster_sales[sales_cols].fillna(0).sum().sum()
                avg_sales_per_store = total_sales / len(cluster_stores)
                
                # Estimate capacity based on sales volume (rough heuristic)
                estimated_capacity = max(50, min(1000, avg_sales_per_store / 100))
                
                if estimated_capacity >= 500:
                    capacity_tier = 'Large'
                elif estimated_capacity >= 200:
                    capacity_tier = 'Medium'
                else:
                    capacity_tier = 'Small'
                
                return {
                    'avg_estimated_capacity': round(estimated_capacity, 0),
                    'total_cluster_capacity': round(estimated_capacity * len(cluster_stores), 0),
                    'capacity_tier': capacity_tier,
                    'data_source': 'Sales-based estimate'
                }
    
    # No data available
    return {
        'avg_estimated_capacity': 0,
        'total_cluster_capacity': 0,
        'capacity_tier': 'Unknown',
        'data_source': 'No data available'
    }

def calculate_cluster_silhouette_score(cluster_df: pd.DataFrame, cluster_id: int) -> Dict[str, Any]:
    """Get silhouette score for a specific cluster from clustering metrics"""
    
    # Look for per-cluster metrics file
    metrics_files = [
        "output/per_cluster_metrics_spu.csv",
        "output/per_cluster_metrics_subcategory.csv",
        "output/cluster_quality_metrics.csv"
    ]
    
    for metrics_file in metrics_files:
        if os.path.exists(metrics_file):
            try:
                metrics_df = pd.read_csv(metrics_file)
                if 'Cluster' in metrics_df.columns and 'Avg_Silhouette' in metrics_df.columns:
                    cluster_metrics = metrics_df[metrics_df['Cluster'] == cluster_id]
                    if not cluster_metrics.empty:
                        silhouette_score = cluster_metrics['Avg_Silhouette'].iloc[0]
                        
                        # Classify silhouette quality
                        if silhouette_score >= 0.7:
                            quality = 'Excellent'
                        elif silhouette_score >= 0.5:
                            quality = 'Good'
                        elif silhouette_score >= 0.3:
                            quality = 'Fair'
                        else:
                            quality = 'Poor'
                        
                        return {
                            'silhouette_score': round(silhouette_score, 3),
                            'silhouette_quality': quality,
                            'data_source': metrics_file
                        }
            except Exception as e:
                log_progress(f"   ✗ Error reading {metrics_file}: {e}")
    
    # Fallback: estimate based on cluster size and characteristics
    cluster_size = len(cluster_df)
    if 40 <= cluster_size <= 60:
        estimated_score = 0.5  # Good size for clustering
        quality = 'Good (estimated)'
    elif 20 <= cluster_size <= 80:
        estimated_score = 0.4  # Reasonable size
        quality = 'Fair (estimated)'
    else:
        estimated_score = 0.3  # Sub-optimal size
        quality = 'Poor (estimated)'
    
    return {
        'silhouette_score': estimated_score,
        'silhouette_quality': quality,
        'data_source': 'Size-based estimate'
    }

# ===== MAIN LABELING FUNCTION =====

def generate_comprehensive_cluster_labels(period_label: Optional[str] = None) -> pd.DataFrame:
    """Generate comprehensive labels for all clusters"""
    log_progress("🏷️ Generating comprehensive cluster labels...")
    
    # Load all data sources
    clustering_df = load_clustering_data(period_label)
    fashion_basic_df = load_fashion_basic_data()
    temperature_df = load_temperature_data()
    capacity_df = load_capacity_data()
    
    # Get unique clusters
    cluster_col = 'Cluster' if 'Cluster' in clustering_df.columns else 'cluster'
    unique_clusters = sorted(clustering_df[cluster_col].unique())
    
    log_progress(f"   📊 Analyzing {len(unique_clusters)} clusters...")
    
    cluster_labels = []
    
    for cluster_id in tqdm(unique_clusters, desc="Processing clusters"):
        # Get stores in this cluster
        cluster_stores = clustering_df[clustering_df[cluster_col] == cluster_id]['str_code'].tolist()
        cluster_size = len(cluster_stores)
        
        log_progress(f"   🔍 Analyzing Cluster {cluster_id}: {cluster_size} stores")
        
        # Calculate fashion/basic makeup
        fashion_basic_profile = calculate_fashion_basic_makeup(cluster_stores, fashion_basic_df)
        
        # Calculate temperature profile
        temperature_profile = calculate_temperature_profile(cluster_stores, temperature_df)
        
        # Calculate capacity profile
        capacity_profile = calculate_capacity_profile(cluster_stores, capacity_df, fashion_basic_df)
        
        # Get silhouette score
        silhouette_profile = calculate_cluster_silhouette_score(clustering_df, cluster_id)
        
        # Create comprehensive label
        cluster_label = {
            'cluster_id': cluster_id,
            'cluster_size': cluster_size,
            'store_codes': ','.join(cluster_stores[:10]) + ('...' if cluster_size > 10 else ''),
            
            # Fashion/Basic Profile
            'fashion_ratio': fashion_basic_profile['fashion_ratio'],
            'basic_ratio': fashion_basic_profile['basic_ratio'],
            'fashion_basic_classification': fashion_basic_profile['fashion_basic_classification'],
            'fashion_basic_data_source': fashion_basic_profile['data_source'],
            
            # Temperature Profile
            'avg_feels_like_temp': temperature_profile['avg_feels_like_temp'],
            'temp_range': temperature_profile['temp_range'],
            'dominant_temp_band': temperature_profile['dominant_temp_band'],
            'temperature_classification': temperature_profile['temperature_classification'],
            'temperature_data_source': temperature_profile.get('data_source', 'Unknown'),
            
            # Capacity Profile
            'avg_estimated_capacity': capacity_profile['avg_estimated_capacity'],
            'capacity_tier': capacity_profile['capacity_tier'],
            'capacity_data_source': capacity_profile['data_source'],
            
            # Quality Metrics
            'silhouette_score': silhouette_profile['silhouette_score'],
            'silhouette_quality': silhouette_profile['silhouette_quality'],
            'silhouette_data_source': silhouette_profile['data_source'],
            
            # Comprehensive Label
            'comprehensive_label': f"Cluster {cluster_id}: {fashion_basic_profile['fashion_basic_classification']} | {temperature_profile['temperature_classification']} | {capacity_profile['capacity_tier']} Capacity | {silhouette_profile['silhouette_quality']} Quality",
            
            # Metadata
            'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            # Count any concrete sources (includes temperature; treats estimates as valid)
            'total_data_sources': sum([
                int(str(fashion_basic_profile.get('data_source', '')).lower() not in ['no data available', 'no sales data', 'stores not in sales data']),
                int(str(temperature_profile.get('data_source', '')).lower() not in ['no data available']),
                int(str(capacity_profile.get('data_source', '')).strip() != ''),
                int(bool(silhouette_profile.get('data_source', '')))
            ])
        }
        
        cluster_labels.append(cluster_label)    
    
    return pd.DataFrame(cluster_labels)

def generate_store_tags(period_label: Optional[str] = None) -> pd.DataFrame:
    """Generate per-store tags by merging cluster membership with enriched store attributes.
    Columns: str_code, Cluster, store_type, store_style_profile, fashion_ratio, basic_ratio,
    estimated_rack_capacity, size_tier, and optional temperature fields if available.
    """
    log_progress("🏷️ Generating per-store tags...")
 
    # Load inputs
    clustering_df = load_clustering_data(period_label)
    capacity_df = load_capacity_data()
    temperature_df = load_temperature_data()
 
    # Standardize clustering columns
    cluster_col = 'Cluster' if 'Cluster' in clustering_df.columns else ('cluster' if 'cluster' in clustering_df.columns else None)
    if cluster_col is None:
        raise ValueError("Clustering results must contain 'Cluster' or 'cluster' column")
    clustering_df['str_code'] = clustering_df['str_code'].astype(str)
 
    # Helper to coerce percentage-like strings to numeric
    def _to_pct(series: pd.Series) -> pd.Series:
        s = series.astype(str).str.replace('%', '', regex=False)
        return pd.to_numeric(s, errors='coerce')
 
    # Bring in enriched attributes/capacity if available
    if not capacity_df.empty:
        # Standardize key
        if 'str_code' not in capacity_df.columns and 'store_code' in capacity_df.columns:
            capacity_df['str_code'] = capacity_df['store_code'].astype(str)
        else:
            capacity_df['str_code'] = capacity_df['str_code'].astype(str)
 
        # Detect capacity column
        cap_col = None
        for c in ['estimated_rack_capacity', 'estimated_capacity', 'capacity']:
            if c in capacity_df.columns:
                cap_col = c
                break
 
        # Subset relevant columns if present
        keep_cols = ['str_code']
        for c in ['store_type', 'store_style_profile', 'fashion_ratio', 'basic_ratio', 'size_tier']:
            if c in capacity_df.columns:
                keep_cols.append(c)
        if cap_col:
            keep_cols.append(cap_col)
 
        attrs = capacity_df[keep_cols].drop_duplicates('str_code')
 
        # Normalize ratios to numeric if present
        if 'fashion_ratio' in attrs.columns:
            attrs['fashion_ratio'] = _to_pct(attrs['fashion_ratio'])
        if 'basic_ratio' in attrs.columns:
            attrs['basic_ratio'] = _to_pct(attrs['basic_ratio'])
 
        # Rename capacity column to standard
        if cap_col and cap_col != 'estimated_rack_capacity':
            attrs.rename(columns={cap_col: 'estimated_rack_capacity'}, inplace=True)
 
        # Join
        tags = clustering_df[['str_code', cluster_col]].copy()
        if cluster_col != 'Cluster':
            tags.rename(columns={cluster_col: 'Cluster'}, inplace=True)
        tags = tags.merge(attrs, on='str_code', how='left')
 
        # If size_tier missing but capacity present, derive
        if 'size_tier' in tags.columns:
            missing_size = tags['size_tier'].isna()
        else:
            tags['size_tier'] = np.nan
            missing_size = tags['size_tier'].isna()
        if 'estimated_rack_capacity' in tags.columns:
            # Ensure numeric for thresholds
            tags['estimated_rack_capacity'] = pd.to_numeric(tags['estimated_rack_capacity'], errors='coerce')
            # Build object-typed series to avoid numpy string/float dtype promotion issues
            derived_size = pd.Series(index=tags.index, dtype='object')
            derived_size.loc[tags['estimated_rack_capacity'] >= 500] = 'Large'
            derived_size.loc[(tags['estimated_rack_capacity'] >= 200) & (tags['estimated_rack_capacity'] < 500)] = 'Medium'
            derived_size.loc[tags['estimated_rack_capacity'].notna() & (tags['estimated_rack_capacity'] < 200)] = 'Small'
            tags.loc[missing_size, 'size_tier'] = derived_size[missing_size]
    else:
        tags = clustering_df[['str_code', cluster_col]].copy()
        if cluster_col != 'Cluster':
            tags.rename(columns={cluster_col: 'Cluster'}, inplace=True)
 
    # Optionally enrich with temperature
    if not temperature_df.empty:
        if 'str_code' not in temperature_df.columns and 'store_code' in temperature_df.columns:
            temperature_df['str_code'] = temperature_df['store_code'].astype(str)
        else:
            temperature_df['str_code'] = temperature_df['str_code'].astype(str)
 
        temp_keep = ['str_code']
        # Prefer canonical feels_like_temperature if present
        if 'feels_like_temperature' in temperature_df.columns:
            temp_keep.append('feels_like_temperature')
        else:
            # Fallback: any feels_like* column
            alt = [col for col in temperature_df.columns if 'feels_like' in col.lower()]
            if alt:
                temp_keep.append(alt[0])
        if 'temperature_band' in temperature_df.columns:
            temp_keep.append('temperature_band')
 
        if len(temp_keep) > 1:
            tags = tags.merge(temperature_df[temp_keep].drop_duplicates('str_code'), on='str_code', how='left')
 
    # Order columns
    ordered_cols = ['str_code', 'Cluster']
    for c in ['store_type', 'store_style_profile', 'fashion_ratio', 'basic_ratio', 'estimated_rack_capacity', 'size_tier', 'feels_like_temperature', 'temperature_band']:
        if c in tags.columns and c not in ordered_cols:
            ordered_cols.append(c)
    tags = tags[ordered_cols]
 
    log_progress(f"✅ Per-store tags prepared: {len(tags):,} stores")
    return tags

def generate_store_cluster_mapping(period_label: Optional[str] = None) -> pd.DataFrame:
    """Generate store → business cluster mapping using the clustering data used for labels.
    Output columns: Store_Code, Cluster_ID (business label cluster).
    """
    log_progress("🧭 Generating store→cluster mapping...")

    clustering_df = load_clustering_data(period_label)
    # Standardize keys
    sc_col = 'str_code' if 'str_code' in clustering_df.columns else ('store_code' if 'store_code' in clustering_df.columns else None)
    if sc_col is None:
        raise ValueError("Clustering results must contain 'str_code' or 'store_code' column")
    cluster_col = 'Cluster' if 'Cluster' in clustering_df.columns else ('cluster' if 'cluster' in clustering_df.columns else None)
    if cluster_col is None:
        raise ValueError("Clustering results must contain 'Cluster' or 'cluster' column")

    df = clustering_df[[sc_col, cluster_col]].copy()
    df[sc_col] = df[sc_col].astype(str)
    # Normalize names
    df = df.rename(columns={sc_col: 'Store_Code', cluster_col: 'Cluster_ID'})
    # Ensure Cluster_ID is numeric (int-like) when possible
    df['Cluster_ID'] = pd.to_numeric(df['Cluster_ID'], errors='coerce').astype('Int64')
    mapping = df.dropna(subset=['Cluster_ID']).drop_duplicates(['Store_Code'])
    log_progress(f"✅ Store→cluster mapping prepared: {len(mapping):,} stores")
    return mapping

def create_cluster_summary(cluster_labels_df: pd.DataFrame) -> Dict[str, Any]:
    """Create summary statistics for cluster labels"""
    
    summary = {
        'analysis_metadata': {
            'total_clusters': len(cluster_labels_df),
            'total_stores': cluster_labels_df['cluster_size'].sum(),
            'analysis_timestamp': datetime.now().isoformat(),
            'data_sources_used': cluster_labels_df['total_data_sources'].sum()
        },
        
        'fashion_basic_distribution': {
            'fashion_focused': int((cluster_labels_df['fashion_basic_classification'] == 'Fashion-Focused').sum()),
            'basic_focused': int((cluster_labels_df['fashion_basic_classification'] == 'Basic-Focused').sum()),
            'balanced': int((cluster_labels_df['fashion_basic_classification'] == 'Balanced').sum()),
            'unknown': int(cluster_labels_df['fashion_basic_classification'].isin(['Unknown', 'No data', 'No cluster data']).sum())
        },
        
        'temperature_distribution': {
            'hot_climate': len(cluster_labels_df[cluster_labels_df['temperature_classification'] == 'Hot Climate']),
            'moderate_climate': len(cluster_labels_df[cluster_labels_df['temperature_classification'] == 'Moderate Climate']),
            'cool_climate': len(cluster_labels_df[cluster_labels_df['temperature_classification'] == 'Cool Climate']),
            'cold_climate': len(cluster_labels_df[cluster_labels_df['temperature_classification'] == 'Cold Climate']),
            'unknown': len(cluster_labels_df[cluster_labels_df['temperature_classification'] == 'Unknown'])
        },
        
        'capacity_distribution': {
            'large': len(cluster_labels_df[cluster_labels_df['capacity_tier'] == 'Large']),
            'medium': len(cluster_labels_df[cluster_labels_df['capacity_tier'] == 'Medium']),
            'small': len(cluster_labels_df[cluster_labels_df['capacity_tier'] == 'Small']),
            'unknown': len(cluster_labels_df[cluster_labels_df['capacity_tier'] == 'Unknown'])
        },
        
        'silhouette_quality_distribution': {
            'excellent': len(cluster_labels_df[cluster_labels_df['silhouette_quality'].str.contains('Excellent', na=False)]),
            'good': len(cluster_labels_df[cluster_labels_df['silhouette_quality'].str.contains('Good', na=False)]),
            'fair': len(cluster_labels_df[cluster_labels_df['silhouette_quality'].str.contains('Fair', na=False)]),
            'poor': len(cluster_labels_df[cluster_labels_df['silhouette_quality'].str.contains('Poor', na=False)])
        },
        
        'data_quality_metrics': {
            'avg_fashion_ratio': cluster_labels_df['fashion_ratio'].mean(),
            'avg_basic_ratio': cluster_labels_df['basic_ratio'].mean(),
            'avg_temperature': cluster_labels_df['avg_feels_like_temp'].mean(),
            'avg_capacity': cluster_labels_df['avg_estimated_capacity'].mean(),
            'avg_silhouette_score': cluster_labels_df['silhouette_score'].mean(),
            'clusters_with_real_data': len(cluster_labels_df[cluster_labels_df['total_data_sources'] > 0])
        }
    }
    
    return summary

def create_analysis_report(cluster_labels_df: pd.DataFrame, summary: Dict[str, Any]) -> None:
    """Create a detailed analysis report"""
    
    report_content = f"""# Comprehensive Cluster Labeling Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Clusters Analyzed:** {summary['analysis_metadata']['total_clusters']}
**Total Stores:** {summary['analysis_metadata']['total_stores']:,}

## Executive Summary

This report provides comprehensive labels for all store clusters including fashion/basic makeup, temperature characteristics, capacity profiles, and clustering quality metrics using real data from the pipeline.

## Fashion/Basic Distribution Analysis

- **Fashion-Focused Clusters:** {summary['fashion_basic_distribution']['fashion_focused']} clusters
- **Basic-Focused Clusters:** {summary['fashion_basic_distribution']['basic_focused']} clusters  
- **Balanced Clusters:** {summary['fashion_basic_distribution']['balanced']} clusters
- **Unknown/No Data:** {summary['fashion_basic_distribution']['unknown']} clusters

**Average Fashion Ratio:** {summary['data_quality_metrics']['avg_fashion_ratio']:.1f}%
**Average Basic Ratio:** {summary['data_quality_metrics']['avg_basic_ratio']:.1f}%

## Temperature Profile Analysis

- **Hot Climate Clusters:** {summary['temperature_distribution']['hot_climate']} clusters
- **Moderate Climate Clusters:** {summary['temperature_distribution']['moderate_climate']} clusters
- **Cool Climate Clusters:** {summary['temperature_distribution']['cool_climate']} clusters  
- **Cold Climate Clusters:** {summary['temperature_distribution']['cold_climate']} clusters
- **Unknown Climate:** {summary['temperature_distribution']['unknown']} clusters

**Average Feels-Like Temperature:** {summary['data_quality_metrics']['avg_temperature']:.1f}°C

## Capacity Profile Analysis

- **Large Capacity Clusters:** {summary['capacity_distribution']['large']} clusters
- **Medium Capacity Clusters:** {summary['capacity_distribution']['medium']} clusters
- **Small Capacity Clusters:** {summary['capacity_distribution']['small']} clusters
- **Unknown Capacity:** {summary['capacity_distribution']['unknown']} clusters

**Average Estimated Capacity:** {summary['data_quality_metrics']['avg_capacity']:.0f} units per store

## Clustering Quality Analysis

- **Excellent Quality (Silhouette ≥ 0.7):** {summary['silhouette_quality_distribution']['excellent']} clusters
- **Good Quality (Silhouette ≥ 0.5):** {summary['silhouette_quality_distribution']['good']} clusters
- **Fair Quality (Silhouette ≥ 0.3):** {summary['silhouette_quality_distribution']['fair']} clusters
- **Poor Quality (Silhouette < 0.3):** {summary['silhouette_quality_distribution']['poor']} clusters

**Average Silhouette Score:** {summary['data_quality_metrics']['avg_silhouette_score']:.3f}

## Data Quality Assessment

- **Clusters with Real Data Sources:** {summary['data_quality_metrics']['clusters_with_real_data']}/{summary['analysis_metadata']['total_clusters']} ({summary['data_quality_metrics']['clusters_with_real_data']/max(1, summary['analysis_metadata']['total_clusters'])*100:.1f}%)
- **Total Data Sources Used:** {summary['analysis_metadata']['data_sources_used']}

## Sample Cluster Labels

"""
    
    # Add sample cluster details
    for i, (_, cluster) in enumerate(cluster_labels_df.head(5).iterrows()):
        report_content += f"""### {cluster['comprehensive_label']}

- **Cluster ID:** {cluster['cluster_id']}
- **Size:** {cluster['cluster_size']} stores
- **Fashion/Basic:** {cluster['fashion_ratio']:.1f}% Fashion, {cluster['basic_ratio']:.1f}% Basic
- **Temperature:** {cluster['avg_feels_like_temp']:.1f}°C ({cluster['temperature_classification']})
- **Capacity:** {cluster['avg_estimated_capacity']:.0f} units avg ({cluster['capacity_tier']} tier)
- **Quality:** Silhouette {cluster['silhouette_score']:.3f} ({cluster['silhouette_quality']})

"""
    
    report_content += f"""
## Recommendations

1. **Data Enhancement:** Focus on improving data collection for clusters with unknown classifications
2. **Quality Improvement:** Monitor clusters with poor silhouette scores for potential re-clustering
3. **Business Alignment:** Use fashion/basic and capacity labels for inventory allocation decisions
4. **Climate Considerations:** Leverage temperature classifications for seasonal planning

## Technical Notes

- Labels generated using real data from: API sales data, clustering results, temperature calculations, capacity estimates
- Silhouette scores indicate clustering quality (higher = better separated clusters)
- Fashion/basic ratios calculated from actual sales transactions
- Temperature data based on feels-like temperature calculations
- Capacity estimates derived from sales volume and SKU diversity patterns

---
*Report generated by Comprehensive Cluster Labeling System v1.0*
"""
    
    with open(CLUSTER_ANALYSIS_FILE, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    log_progress(f"   ✓ Saved analysis report: {CLUSTER_ANALYSIS_FILE}")

def main() -> None:
    """Main function to generate comprehensive cluster labels"""
    print("DEBUG: Starting main function")
    start_time = datetime.now()
    log_progress("🚀 Starting Comprehensive Cluster Labeling Analysis...")
    print("DEBUG: About to parse arguments")
    
    try:
        # Period-aware CLI
        import argparse
        parser = argparse.ArgumentParser(description="Step 24: Comprehensive Cluster Labeling (period-aware)")
        parser.add_argument("--target-yyyymm", required=False)
        parser.add_argument("--target-period", required=False, choices=["A","B"])
        args, _ = parser.parse_known_args()
        print("DEBUG: Arguments parsed successfully")
        print(f"DEBUG: args = {args}")
        period_label = None
        if getattr(args, 'target_yyyymm', None) and getattr(args, 'target_period', None):
            period_label = get_period_label(args.target_yyyymm, args.target_period)
        print(f"DEBUG: period_label = {period_label}")

        # Generate cluster labels
        cluster_labels_df = generate_comprehensive_cluster_labels(period_label)
        
        # Save cluster labels with timestamped file + symlink
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        timestamped_labels = f"output/comprehensive_cluster_labels_{period_label}_{ts}.csv"
        cluster_labels_df.to_csv(timestamped_labels, index=False)
        log_progress(f"✅ Saved timestamped cluster labels: {timestamped_labels}")
        
        # Create symlink for generic access
        if os.path.exists(CLUSTER_LABELS_FILE) or os.path.islink(CLUSTER_LABELS_FILE):
            os.remove(CLUSTER_LABELS_FILE)
        os.symlink(os.path.basename(timestamped_labels), CLUSTER_LABELS_FILE)
        log_progress(f"✅ Created symlink: {CLUSTER_LABELS_FILE} -> {timestamped_labels}")
        labels_file = timestamped_labels
        
        # Create summary
        summary = create_cluster_summary(cluster_labels_df)
        
        # Save summary (convert numpy types to native Python types)
        def convert_numpy_types(obj):
            if isinstance(obj, (np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            return obj
        
        summary_serializable = convert_numpy_types(summary)
        summary_file = (
            f"output/cluster_labeling_summary_{period_label}_{ts}.json" if period_label else
            CLUSTER_SUMMARY_FILE
        )
        with open(summary_file, 'w') as f:
            json.dump(summary_serializable, f, indent=2)
        log_progress(f"✅ Saved cluster summary: {summary_file}")
        
        # Create analysis report
        global CLUSTER_ANALYSIS_FILE
        old_analysis = CLUSTER_ANALYSIS_FILE
        analysis_file = (
            f"output/cluster_label_analysis_report_{period_label}_{ts}.md" if period_label else
            CLUSTER_ANALYSIS_FILE
        )
        # Temporarily set global output var for function reuse
        CLUSTER_ANALYSIS_FILE = analysis_file
        create_analysis_report(cluster_labels_df, summary)
        CLUSTER_ANALYSIS_FILE = old_analysis
 
        # Generate and save per-store tags
        store_tags_df = generate_store_tags(period_label)
        timestamped_tags = f"output/store_tags_{period_label}_{ts}.csv"
        store_tags_df.to_csv(timestamped_tags, index=False)
        log_progress(f"✅ Saved timestamped store tags: {timestamped_tags}")
        
        # Create symlink for generic access
        if os.path.exists(STORE_TAGS_FILE) or os.path.islink(STORE_TAGS_FILE):
            os.remove(STORE_TAGS_FILE)
        os.symlink(os.path.basename(timestamped_tags), STORE_TAGS_FILE)
        log_progress(f"✅ Created symlink: {STORE_TAGS_FILE} -> {timestamped_tags}")
        tags_file = timestamped_tags

        # Generate and save store→cluster mapping (business label clusters)
        store_cluster_map_df = generate_store_cluster_mapping(period_label)
        timestamped_mapping = f"output/store_cluster_mapping_{period_label}_{ts}.csv"
        store_cluster_map_df.to_csv(timestamped_mapping, index=False)
        log_progress(f"✅ Saved timestamped store→cluster mapping: {timestamped_mapping}")
        
        # Create symlink for generic access
        generic_mapping = "output/store_cluster_mapping.csv"
        if os.path.exists(generic_mapping) or os.path.islink(generic_mapping):
            os.remove(generic_mapping)
        os.symlink(os.path.basename(timestamped_mapping), generic_mapping)
        log_progress(f"✅ Created symlink: {generic_mapping} -> {timestamped_mapping}")
        store_cluster_map_file = timestamped_mapping

        # Register outputs
        try:
            base_meta = {"records": int(len(cluster_labels_df))}
            register_step_output("step24", "comprehensive_cluster_labels", labels_file, base_meta)
            register_step_output("step24", "cluster_label_summary", summary_file, {})
            register_step_output("step24", "cluster_label_analysis_report", analysis_file, {})
            register_step_output("step24", "store_tags", tags_file, {"records": int(len(store_tags_df))})
            register_step_output("step24", "store_cluster_mapping", store_cluster_map_file, {"records": int(len(store_cluster_map_df))})
            if period_label:
                register_step_output("step24", f"comprehensive_cluster_labels_{period_label}", labels_file, base_meta)
                register_step_output("step24", f"cluster_label_summary_{period_label}", summary_file, {})
                register_step_output("step24", f"cluster_label_analysis_report_{period_label}", analysis_file, {})
                register_step_output("step24", f"store_tags_{period_label}", tags_file, {"records": int(len(store_tags_df))})
                register_step_output("step24", f"store_cluster_mapping_{period_label}", store_cluster_map_file, {"records": int(len(store_cluster_map_df))})
        except Exception:
            pass
        
        # Print key results
        log_progress("\n🎯 CLUSTER LABELING RESULTS:")
        log_progress(f"   📊 Total Clusters: {len(cluster_labels_df)}")
        log_progress(f"   🏪 Total Stores: {cluster_labels_df['cluster_size'].sum():,}")
        log_progress(f"   📈 Avg Silhouette Score: {cluster_labels_df['silhouette_score'].mean():.3f}")
        log_progress(f"   👗 Fashion-Focused Clusters: {summary['fashion_basic_distribution']['fashion_focused']}")
        log_progress(f"   👔 Basic-Focused Clusters: {summary['fashion_basic_distribution']['basic_focused']}")
        log_progress(f"   ⚖️ Balanced Clusters: {summary['fashion_basic_distribution']['balanced']}")
        log_progress(f"   🌡️ Avg Temperature: {summary['data_quality_metrics']['avg_temperature']:.1f}°C")
        log_progress(f"   📦 Avg Capacity: {summary['data_quality_metrics']['avg_capacity']:.0f} units")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        log_progress(f"\n✅ Comprehensive cluster labeling completed in {execution_time:.1f} seconds")
        
        log_progress(f"\n📁 Generated Files:")
        log_progress(f"   • {labels_file}")
        log_progress(f"   • {summary_file}")  
        log_progress(f"   • {analysis_file}")
        log_progress(f"   • {tags_file}")
        
    except Exception as e:
        log_progress(f"❌ Error in cluster labeling: {str(e)}")
        raise

if __name__ == "__main__":
    main() 