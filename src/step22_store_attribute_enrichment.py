#!/usr/bin/env python3
"""
Step 22: Store Attribute Enrichment with Real Data

This step enriches store data with comprehensive attributes using ONLY real data:
- Store Type/Style Classification (Fashion/Basic/Balanced) from real fashion/basic sales ratios
- Rack Capacity/Size Tier estimation from real sales volume and SKU diversity
- Temperature zone integration from existing weather data

NO SYNTHETIC OR PLACEHOLDER DATA - Uses only available real business data.

Author: Data Pipeline Team
Date: 2025-07-23
Version: 1.0 - Real Data Only Implementation

 HOW TO RUN (CLI + ENV) — Read this before executing
 ----------------------------------------------------
 Overview
 - Period-aware: labels outputs by the target period while allowing sourcing of real sales from a prior period.
 - Upstream cluster scope: For fast testing (Steps 7–21), it’s common to prepare data only for a single cluster
   (e.g., Cluster 22). Step 22 will enrich all stores present in the source data you provide.

 Quick Start (fast testing; target 202510A, source 202509A)
 - Use the latest available real sales period as source when the target is not yet available.

   Command:
     PYTHONPATH=. python3 src/step22_store_attribute_enrichment.py \
       --target-yyyymm 202510 \
       --target-period A \
       --source-yyyymm 202509 \
       --source-period A

 Production Run (all clusters)
 - When the target period’s Step 1 outputs already exist, omit source overrides.

   Command:
     PYTHONPATH=. python3 src/step22_store_attribute_enrichment.py \
       --target-yyyymm 202510 \
       --target-period A

 Options you may need
 - --force-taxonomy-split: recomputes fashion/basic ratios when API splits look constant or noisy
 - --subcategory-mapping <CSV>: optional mapping to improve taxonomy-based split

 Period Handling Patterns
 - Target label: use --target-yyyymm/--target-period
 - Source real sales: use --source-yyyymm/--source-period to pull from a prior period (recommended if target is future)

 Best Practices & Pitfalls
 - Do NOT rely on synthetic/combined files; this step expects period-specific Step 1 outputs.
 - If you see "Missing required source store sales ...", provide --source-yyyymm/--source-period or (re)run Step 1 for the target.
 - For production, ensure upstream Steps 7–21 have been prepared for ALL clusters so enrichment covers all stores.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
from typing import Dict, Tuple, Any, Optional
import warnings
from tqdm import tqdm
import argparse

# Period and manifest utilities (resilient imports for module vs script execution)
try:
    from src.config import get_period_label, get_api_data_files, get_output_files
    from src.pipeline_manifest import register_step_output
except ModuleNotFoundError:
    try:
        from config import get_period_label, get_api_data_files, get_output_files
        from pipeline_manifest import register_step_output
    except ModuleNotFoundError:
        import sys as _sys
        import os as _os
        _root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        if _root not in _sys.path:
            _sys.path.insert(0, _root)
        from src.config import get_period_label, get_api_data_files, get_output_files
        from src.pipeline_manifest import register_step_output

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# ===== CONFIGURATION =====
# Input data sources (period-aware; combined synthetic files are forbidden)
SALES_DATA_FILE = None  # DO NOT USE combined/synthetic defaults
CATEGORY_DATA_FILE = None  # DO NOT USE combined/synthetic defaults
STORE_CONFIG_FILE = None  # Resolved via get_api_data_files(yyyymm, period)
CLUSTERING_RESULTS_FILE = None  # Resolved via get_output_files('spu', yyyymm, period)
TEMPERATURE_DATA_FILE = "output/stores_with_feels_like_temperature.csv"

# Alternative data sources (fallback)
FALLBACK_SALES_FILES = [
    "output/consolidated_spu_rule_results.csv",
    "data/store_codes.csv"
]

# Output files
ENRICHED_STORE_ATTRIBUTES_FILE = "output/enriched_store_attributes.csv"
STORE_TYPE_ANALYSIS_FILE = "output/store_type_analysis_report.md"

# Create output directory
os.makedirs("output", exist_ok=True)

# Target period context (set in main)
_TARGET_YYYYMM: Optional[str] = None
_TARGET_PERIOD: Optional[str] = None

# ===== CLI PARSING (PERIOD-AWARE) =====
def _parse_args():
    """Parse CLI arguments for period-aware Step 22."""
    parser = argparse.ArgumentParser(description="Step 22: Store Attribute Enrichment (period-aware)")
    parser.add_argument("--target-yyyymm", required=True, help="Target year-month for current run, e.g. 202509")
    parser.add_argument("--target-period", choices=["A", "B"], required=True, help="Target period (A or B)")
    parser.add_argument("--source-yyyymm", required=False, help="Source year-month for real store splits (defaults to target-1 month)")
    parser.add_argument("--source-period", choices=["A", "B"], required=False, help="Source period for real store splits (defaults to target period)")
    parser.add_argument("--force-taxonomy-split", action="store_true", help="Ignore API fashion/basic split and recompute from taxonomy")
    parser.add_argument("--subcategory-mapping", default=os.environ.get("STEP22_SUBCATEGORY_MAPPING_FILE", "data/api_data/subcategory_fashion_mapping.csv"), help="Optional CSV mapping of sub_cate_name to fashion/basic/neutral")
    return parser.parse_args()

# ===== STORE TYPE CLASSIFICATION LOGIC =====
def classify_store_type_from_real_data(fashion_ratio: float, basic_ratio: float, 
                                     total_sales: float, sku_diversity: int) -> Tuple[str, str, float]:
    """
    Classify store type using real fashion/basic sales ratios and business metrics.
    
    Args:
        fashion_ratio: Percentage of fashion sales (0-100)
        basic_ratio: Percentage of basic sales (0-100)
        total_sales: Total sales volume for the store
        sku_diversity: Number of unique SKUs/SPUs sold
        
    Returns:
        Tuple of (store_type, store_style_profile, confidence_score)
    """
    # Calculate confidence based on data quality
    data_completeness = min(100, (fashion_ratio + basic_ratio))
    volume_factor = min(100, total_sales / 10000 * 100)  # Scale based on sales volume
    diversity_factor = min(100, sku_diversity / 50 * 100)  # Scale based on SKU count
    confidence_score = (data_completeness * 0.5 + volume_factor * 0.3 + diversity_factor * 0.2) / 100
    
    # Store type classification based on real ratios
    # Use a higher bar for Fashion to avoid over-classification when API splits are noisy/constant
    if fashion_ratio >= 70:
        store_type = "Fashion"
        if fashion_ratio >= 80:
            store_style_profile = "Fashion-Heavy"
        else:
            store_style_profile = "Fashion-Focused"
    elif basic_ratio >= 55:
        store_type = "Basic"
        if basic_ratio >= 80:
            store_style_profile = "Basic-Heavy"
        else:
            store_style_profile = "Basic-Focused"
    else:
        store_type = "Balanced"
        if abs(fashion_ratio - basic_ratio) <= 10:
            store_style_profile = "Perfectly-Balanced"
        elif fashion_ratio > basic_ratio:
            store_style_profile = "Fashion-Leaning"
        else:
            store_style_profile = "Basic-Leaning"
    
    return store_type, store_style_profile, confidence_score

# ===== CAPACITY ESTIMATION LOGIC =====
def estimate_store_capacity_from_real_data(total_sales: float, total_qty: float, 
                                         sku_count: int, category_count: int) -> Tuple[str, int, str]:
    """
    Estimate store capacity using real sales data and SKU diversity.
    
    Args:
        total_sales: Total sales amount
        total_qty: Total quantity sold
        sku_count: Number of unique SKUs
        category_count: Number of categories
        
    Returns:
        Tuple of (size_tier, estimated_rack_capacity, capacity_rationale)
    """
    # Calculate capacity indicators from real data
    avg_price_per_unit = total_sales / total_qty if total_qty > 0 else 50
    sales_per_sku = total_sales / sku_count if sku_count > 0 else 0
    qty_per_sku = total_qty / sku_count if sku_count > 0 else 0
    
    # Estimate rack capacity based on SKU diversity and sales patterns
    # Higher SKU count + reasonable sales per SKU = larger store capacity
    base_capacity = sku_count * 2  # Assume 2 units per SKU on average
    
    # Adjust based on sales velocity (high velocity = higher capacity needed)
    if sales_per_sku > 1000:  # High-performing SKUs
        capacity_multiplier = 1.5
    elif sales_per_sku > 500:  # Medium-performing SKUs
        capacity_multiplier = 1.2
    else:  # Lower-performing SKUs
        capacity_multiplier = 1.0
    
    estimated_capacity = int(base_capacity * capacity_multiplier)
    
    # Size tier classification
    if estimated_capacity >= 500:
        size_tier = "Large"
        capacity_rationale = f"High SKU diversity ({sku_count} SKUs) + strong sales velocity"
    elif estimated_capacity >= 200:
        size_tier = "Medium"
        capacity_rationale = f"Moderate SKU diversity ({sku_count} SKUs) + decent sales"
    else:
        size_tier = "Small"
        capacity_rationale = f"Limited SKU diversity ({sku_count} SKUs) + lower sales volume"
    
    return size_tier, estimated_capacity, capacity_rationale

# ===== Fashion/Basic Mapping Heuristics (real subcategory-based fallback) =====
FASHION_KEYWORDS = [
    '连衣裙', '裙', 'V领', '修身', '时尚', '潮鞋', '防晒衣', '开衫', '毛衣', '圆领', 'A版', 'H版', 'X版',
    # common English signals if present
    'dress', 'skirt', 'cardigan', 'sweater', 'fashion', 'trend', 'coat', 'jacket', 'outerwear'
]

def _is_fashion_subcategory(name: str) -> bool:
    try:
        s = str(name)
        return any(k in s for k in FASHION_KEYWORDS)
    except Exception:
        return False

# ===== DATA LOADING FUNCTIONS =====
def load_real_sales_data(target_yyyymm: Optional[str] = None, target_period: Optional[str] = None,
                        source_yyyymm: Optional[str] = None, source_period: Optional[str] = None) -> pd.DataFrame:
    """Load real sales data strictly from period-specific outputs, avoiding synthetic combined files.
    Strategy:
      1) Prefer Step 1 store-level splits: output/store_sales_{YYYYMMP}.csv (for ratios, includes base/fashion amt+qty and str_type)
      2) Merge in minimal SPU-level data for SKU diversity: output/complete_spu_sales_{YYYYMMP}.csv or data/api_data/complete_spu_sales_{YYYYMMP}.csv
      3) If target period not available, fallback to previous month same half (e.g., 202508A for 202509A) with explicit notice.
      4) Never load 2025Q2 combined synthetic files here.
    """
    print("Loading real sales data...")
    
    # Resolve primary and fallback period labels
    period_label = f"{target_yyyymm}{target_period}" if (target_yyyymm and target_period) else None
    # If a source override is provided, use that label to load store splits
    load_label = f"{source_yyyymm}{source_period}" if (source_yyyymm and source_period) else period_label
    
    def _load_store_sales(label: str) -> Optional[pd.DataFrame]:
        for path in [
            os.path.join("output", f"store_sales_{label}.csv"),
            os.path.join("data", "api_data", f"store_sales_{label}.csv"),
        ]:
            if os.path.exists(path):
                print(f"✓ Loading store-level sales (for ratios): {path}")
                return pd.read_csv(path, dtype={'str_code': str})
        return None
    
    def _load_spu_sales(label: str) -> Optional[pd.DataFrame]:
        for path in [
            os.path.join("output", f"complete_spu_sales_{label}.csv"),
            os.path.join("data", "api_data", f"complete_spu_sales_{label}.csv"),
        ]:
            if os.path.exists(path):
                print(f"✓ Loading SPU-level sales (for SKU diversity): {path}")
                return pd.read_csv(path, dtype={'str_code': str})
        return None
    
    # Require primary period store-level sales; do not fallback
    store_df = _load_store_sales(load_label) if load_label else None
    spu_df = _load_spu_sales(load_label) if load_label else None
    if store_df is None:
        raise FileNotFoundError(f"Missing required source store sales: output/store_sales_{load_label}.csv. Provide --source-yyyymm/--source-period or run Step 1.")
    
    # Prepare merged frame: use store_df for ratios; append minimal SPU rows for SKU diversity without affecting amounts
    frames = []
    if store_df is not None:
        frames.append(store_df)
    if spu_df is not None:
        keep_cols = [c for c in ['str_code','spu_code','cate_name','sub_cate_name'] if c in spu_df.columns]
        if keep_cols:
            frames.append(spu_df[keep_cols])
    df = pd.concat(frames, ignore_index=True, sort=False)
    print(f"  Loaded {len(df):,} sales records (combined store-level ratios + SPU diversity)")
    return df

def load_store_configuration_data(target_yyyymm: Optional[str] = None, target_period: Optional[str] = None) -> pd.DataFrame:
    """Load store configuration data (period-aware via config helpers)."""
    print("Loading store configuration data...")
    try:
        yyyymm = target_yyyymm or _TARGET_YYYYMM
        period = target_period or _TARGET_PERIOD
        if yyyymm and period:
            api = get_api_data_files(yyyymm, period)
            path = api.get('store_config') or os.path.join('data', 'api_data', f"store_config_{yyyymm}{period}.csv")
            if path and os.path.exists(path):
                print(f"✓ Loading store config: {path}")
                df = pd.read_csv(path, dtype={'str_code': str})
                print(f"  Loaded {len(df):,} store config records")
                return df
    except Exception as e:
        print(f"✗ Period-aware store config resolution failed: {e}")
    print("✗ Store configuration file not found")
    return pd.DataFrame()

def load_temperature_data() -> pd.DataFrame:
    """Load temperature data if available."""
    print("Loading temperature data...")
    
    if os.path.exists(TEMPERATURE_DATA_FILE):
        print(f"✓ Loading temperature data: {TEMPERATURE_DATA_FILE}")
        df = pd.read_csv(TEMPERATURE_DATA_FILE)
        # Normalize store code column if different naming is used
        if 'str_code' not in df.columns:
            for alt in [
                'store_code', 'Store_Code', 'STORE_CODE', 'str_cd', 'STR_CD',
                'store_cd', 'StoreID', 'Store_ID', 'store_id'
            ]:
                if alt in df.columns:
                    df = df.rename(columns={alt: 'str_code'})
                    print(f"  ✓ Normalized store code column '{alt}' -> 'str_code'")
                    break
        # Ensure string dtype for merge compatibility
        if 'str_code' in df.columns:
            df['str_code'] = df['str_code'].astype(str)
        print(f"  Loaded {len(df):,} temperature records")
        return df
    
    print("✗ Temperature data file not found")
    return pd.DataFrame()

def load_clustering_data(target_yyyymm: Optional[str] = None, target_period: Optional[str] = None) -> pd.DataFrame:
    """Load clustering results (prefer period-aware outputs)."""
    print("Loading clustering data...")
    yyyymm = target_yyyymm or _TARGET_YYYYMM
    period = target_period or _TARGET_PERIOD
    candidates = []
    try:
        if yyyymm and period:
            out = get_output_files('spu', yyyymm, period)
            for key in ['clustering_results', 'clustering_results_spu', 'cluster_assignments']:
                p = out.get(key)
                if p:
                    candidates.append(p)
    except Exception:
        pass
    # Generic fallbacks (avoid combined/synthetic)
    candidates.extend([
        os.path.join('output', 'clustering_results_spu.csv'),
        os.path.join('output', 'clustering_results.csv'),
    ])
    for path in candidates:
        try:
            if path and os.path.exists(path):
                print(f"✓ Loading clustering results: {path}")
                df = pd.read_csv(path)
                if 'str_code' not in df.columns:
                    for alt in ['store_code', 'Store_Code', 'STORE_CODE', 'str_cd', 'STR_CD', 'store_cd', 'StoreID', 'Store_ID', 'store_id']:
                        if alt in df.columns:
                            df = df.rename(columns={alt: 'str_code'})
                            print(f"  ✓ Normalized store code column '{alt}' -> 'str_code'")
                            break
                if 'str_code' in df.columns:
                    df['str_code'] = df['str_code'].astype(str)
                print(f"  Loaded {len(df):,} clustering records")
                return df
        except Exception:
            continue
    print("✗ Clustering results file not found")
    return pd.DataFrame()

# ===== MAIN ENRICHMENT FUNCTION =====
def calculate_store_attributes_from_real_data(sales_df: pd.DataFrame, *, force_taxonomy_split: bool = False, subcategory_mapping_file: Optional[str] = None) -> pd.DataFrame:
    """
    Calculate comprehensive store attributes using only real sales data.
    
    Args:
        sales_df: Real sales data from API
        
    Returns:
        DataFrame with enriched store attributes
    """
    print("Calculating store attributes from real data...")
    
    # Detect if API provides a constant 50/50 split; if so we will recompute from taxonomy
    constant_api_split = False
    try:
        if force_taxonomy_split:
            constant_api_split = True
        elif 'fashion_ratio' in sales_df.columns:
            fr = pd.to_numeric(sales_df['fashion_ratio'], errors='coerce')
            uniq = fr.dropna().unique()
            if len(uniq) == 1 and abs(float(uniq[0]) - 0.5) < 1e-6:
                constant_api_split = True
        else:
            # Support either 'basic' or 'base' naming from Step 1
            cols = set(sales_df.columns)
            has_amt = ('fashion_sal_amt' in cols) and (('basic_sal_amt' in cols) or ('base_sal_amt' in cols))
            has_qty = ('fashion_sal_qty' in cols) and (('basic_sal_qty' in cols) or ('base_sal_qty' in cols))
            if has_amt:
                fa = pd.to_numeric(sales_df['fashion_sal_amt'], errors='coerce').fillna(0)
                ba_col = 'basic_sal_amt' if 'basic_sal_amt' in cols else 'base_sal_amt'
                ba = pd.to_numeric(sales_df[ba_col], errors='coerce').fillna(0)
            if len(fa) > 0 and (fa.round(6) == ba.round(6)).mean() > 0.95:
                constant_api_split = True
    except Exception:
        constant_api_split = False

    # Build subcategory-level fashion propensity (data-driven) for taxonomy-based recomputation
    subcat_fashion_flag = {}
    try:
        # Load explicit mapping if provided
        if subcategory_mapping_file and os.path.exists(subcategory_mapping_file):
            try:
                map_df = pd.read_csv(subcategory_mapping_file)
                if {'sub_cate_name','tag'}.issubset(set(map_df.columns)):
                    for _, r in map_df.iterrows():
                        subcat_fashion_flag[r['sub_cate_name']] = str(r['tag']).strip().lower()  # fashion/basic/neutral
            except Exception:
                pass
        # Derive data-driven propensity if API split is constant or forced
        if constant_api_split and {'sub_cate_name', 'unit_price', 'spu_code'}.issubset(set(sales_df.columns)):
            tmp = sales_df[['sub_cate_name', 'unit_price', 'spu_code']].copy()
            tmp['unit_price'] = pd.to_numeric(tmp['unit_price'], errors='coerce')
            # Aggregate metrics per subcategory
            agg = tmp.groupby('sub_cate_name').agg(
                median_price=('unit_price', 'median'),
                spu_diversity=('spu_code', 'nunique'),
                obs=('spu_code', 'size')
            ).reset_index()
            # Rank metrics into [0,1]
            agg['price_rank'] = agg['median_price'].rank(pct=True)
            agg['div_rank'] = agg['spu_diversity'].rank(pct=True)
            agg['fashion_score'] = (agg['price_rank'] + agg['div_rank']) / 2.0
            # Thresholds derived from data percentiles
            hi = agg['fashion_score'].quantile(0.7)
            lo = agg['fashion_score'].quantile(0.3)
            for _, r in agg.iterrows():
                score = float(r['fashion_score']) if pd.notna(r['fashion_score']) else 0.0
                if score >= hi:
                    subcat_fashion_flag[r['sub_cate_name']] = 'fashion'
                elif score <= lo:
                    subcat_fashion_flag[r['sub_cate_name']] = 'basic'
                else:
                    subcat_fashion_flag[r['sub_cate_name']] = 'basic'  # neutral -> basic for conservative split
    except Exception:
        subcat_fashion_flag = {}

    # Group by store to calculate store-level metrics
    store_metrics = []
    
    # Get unique stores
    unique_stores = sales_df['str_code'].unique()
    print(f"Processing {len(unique_stores):,} unique stores...")
    
    for store_code in tqdm(unique_stores, desc="Calculating store attributes"):
        store_data = sales_df[sales_df['str_code'] == store_code]

        # Calculate real fashion/basic ratios (store-level only for splits)
        lower_cols = {c.lower(): c for c in store_data.columns}
        fashion_amt = 0.0
        basic_amt = 0.0
        fashion_qty = 0.0
        basic_qty = 0.0

        # Identify store-level split rows to avoid contamination from SPU rows
        split_amt_fashion_col = lower_cols.get('fashion_sal_amt')
        split_amt_basic_col = lower_cols.get('basic_sal_amt') or lower_cols.get('base_sal_amt')
        split_qty_fashion_col = lower_cols.get('fashion_sal_qty')
        split_qty_basic_col = lower_cols.get('basic_sal_qty') or lower_cols.get('base_sal_qty')
        has_store_split = (
            (split_amt_fashion_col is not None and split_amt_basic_col is not None) or
            (split_qty_fashion_col is not None and split_qty_basic_col is not None)
        )

        if has_store_split:
            if split_amt_fashion_col and split_amt_basic_col:
                fashion_amt = pd.to_numeric(store_data[split_amt_fashion_col], errors='coerce').fillna(0).sum()
                basic_amt = pd.to_numeric(store_data[split_amt_basic_col], errors='coerce').fillna(0).sum()
            if split_qty_fashion_col and split_qty_basic_col:
                fashion_qty = pd.to_numeric(store_data[split_qty_fashion_col], errors='coerce').fillna(0).sum()
                basic_qty = pd.to_numeric(store_data[split_qty_basic_col], errors='coerce').fillna(0).sum()
        elif constant_api_split:
            # Recompute by taxonomy: allocate by subcategory using real amounts/qty
            sales_amt_col = lower_cols.get('spu_sales_amt') or lower_cols.get('sales_amt') or lower_cols.get('sal_amt')
            qty_col = lower_cols.get('quantity') or lower_cols.get('sales_qty') or lower_cols.get('sal_qty')
            if 'sub_cate_name' in store_data.columns and (sales_amt_col or qty_col):
                if sales_amt_col:
                    for _, r in store_data.iterrows():
                        amt_f = float(r.get(sales_amt_col, 0) or 0)
                        subname = r.get('sub_cate_name')
                        flag = subcat_fashion_flag.get(subname)
                        if flag == 'fashion' or (flag is None and _is_fashion_subcategory(subname)):
                            fashion_amt += amt_f
                        else:
                            basic_amt += amt_f
                if qty_col and fashion_amt == 0.0 and basic_amt == 0.0:
                    for _, r in store_data.iterrows():
                        qty_f = float(r.get(qty_col, 0) or 0)
                        subname = r.get('sub_cate_name')
                        flag = subcat_fashion_flag.get(subname)
                        if flag == 'fashion' or (flag is None and _is_fashion_subcategory(subname)):
                            fashion_qty += qty_f
                        else:
                            basic_qty += qty_f
            else:
                # Fallback to sums of any explicit columns (last resort)
                for col in store_data.columns:
                    col_l = col.lower()
                    if 'fashion' in col_l and ('amt' in col_l or 'sales_amt' in col_l):
                        fashion_amt += pd.to_numeric(store_data[col], errors='coerce').fillna(0).sum()
                    elif 'basic' in col_l and ('amt' in col_l or 'sales_amt' in col_l):
                        basic_amt += pd.to_numeric(store_data[col], errors='coerce').fillna(0).sum()
                    elif 'fashion' in col_l and ('qty' in col_l or 'quantity' in col_l):
                        fashion_qty += pd.to_numeric(store_data[col], errors='coerce').fillna(0).sum()
                    elif 'basic' in col_l and ('qty' in col_l or 'quantity' in col_l):
                        basic_qty += pd.to_numeric(store_data[col], errors='coerce').fillna(0).sum()
        else:
            # Use any explicit column naming variants (amt/qty)
            for col in store_data.columns:
                col_l = col.lower()
                if 'fashion' in col_l and ('amt' in col_l or 'sales_amt' in col_l):
                    fashion_amt += pd.to_numeric(store_data[col], errors='coerce').fillna(0).sum()
                elif (('basic' in col_l) or ('base' in col_l)) and ('amt' in col_l or 'sales_amt' in col_l):
                    basic_amt += pd.to_numeric(store_data[col], errors='coerce').fillna(0).sum()
                elif 'fashion' in col_l and ('qty' in col_l or 'quantity' in col_l):
                    fashion_qty += pd.to_numeric(store_data[col], errors='coerce').fillna(0).sum()
                elif (('basic' in col_l) or ('base' in col_l)) and ('qty' in col_l or 'quantity' in col_l):
                    basic_qty += pd.to_numeric(store_data[col], errors='coerce').fillna(0).sum()
            # Heuristic fallback via subcategory when explicit columns are missing or zero
            if fashion_amt == 0.0 and basic_amt == 0.0 and 'sub_cate_name' in store_data.columns:
                sales_amt_col = None
                for probe in ['spu_sales_amt', 'sales_amt', 'sal_amt']:
                    if probe in lower_cols:
                        sales_amt_col = lower_cols[probe]
                        break
                qty_col = None
                for probe in ['quantity', 'sales_qty', 'sal_qty']:
                    if probe in lower_cols:
                        qty_col = lower_cols[probe]
                        break
                if sales_amt_col is not None:
                    for _, r in store_data.iterrows():
                        amt = float(r.get(sales_amt_col, 0) or 0)
                        if _is_fashion_subcategory(r.get('sub_cate_name')):
                            fashion_amt += amt
                        else:
                            basic_amt += amt
                if (fashion_qty == 0.0 and basic_qty == 0.0) and qty_col is not None:
                    for _, r in store_data.iterrows():
                        qty = float(r.get(qty_col, 0) or 0)
                        if _is_fashion_subcategory(r.get('sub_cate_name')):
                            fashion_qty += qty
                        else:
                            basic_qty += qty
        
        total_qty = basic_qty + fashion_qty
        total_amt = basic_amt + fashion_amt
        
        # Calculate blended ratios (amount and quantity) to avoid price bias
        amt_ratio = None
        qty_ratio = None
        if total_amt > 0:
            amt_ratio = fashion_amt / total_amt
        if total_qty > 0:
            qty_ratio = fashion_qty / total_qty
        if amt_ratio is not None and qty_ratio is not None:
            blended = 0.5 * amt_ratio + 0.5 * qty_ratio
        elif amt_ratio is not None:
            blended = amt_ratio
        elif qty_ratio is not None:
            blended = qty_ratio
        else:
            blended = 0.0
        fashion_ratio = blended * 100.0
        basic_ratio = 100.0 - fashion_ratio
        
        # Calculate SKU diversity metrics
        sku_count = store_data['spu_code'].nunique() if 'spu_code' in store_data.columns else 0
        category_count = store_data['cate_name'].nunique() if 'cate_name' in store_data.columns else 0
        subcategory_count = store_data['sub_cate_name'].nunique() if 'sub_cate_name' in store_data.columns else 0
        
        # Primary classification policy (NO synthetic/fallback):
        # 1) Compute ratio-based class using blended fashion_ratio with symmetric thresholds.
        # 2) Use API label 'str_type' (基础=Basic, 流行=Fashion) only as a tie-breaker in the gray band.
        # 3) Balanced is assigned for blended ratios in [35, 65].
        # 4) Profiles are derived from final class and ratio magnitude.
        #    This ensures Fashion/Basic/Balanced all appear when supported by actual data.
        #    API label does not override a strong opposing ratio.

        # Derive API class (if present)
        api_class = None
        if 'str_type' in store_data.columns:
            try:
                hint_mode = store_data['str_type'].dropna().astype(str).mode().iat[0]
                hint_l = hint_mode.lower()
                if ('基础' in hint_mode) or ('basic' in hint_l):
                    api_class = 'Basic'
                elif ('流行' in hint_mode) or ('fashion' in hint_l):
                    api_class = 'Fashion'
            except Exception:
                api_class = None

        # Classification policy: ratio-first with explicit Balanced band; API label only breaks ties near boundaries
        upper_fashion_cut = 65.0
        lower_basic_cut = 35.0
        if fashion_ratio >= upper_fashion_cut:
            store_type = 'Fashion'
        elif fashion_ratio <= lower_basic_cut:
            store_type = 'Basic'
        else:
            store_type = 'Balanced'
        # Tie-breaker: if within 5% of a boundary, align to API label when present
        if api_class in ['Fashion','Basic']:
            near_upper = abs(fashion_ratio - upper_fashion_cut) <= 5.0
            near_lower = abs(fashion_ratio - lower_basic_cut) <= 5.0
            if store_type == 'Balanced' and (near_upper or near_lower):
                store_type = api_class

        # Derive profile from final class and ratio
        if store_type == 'Fashion':
            store_style_profile = 'Fashion-Heavy' if fashion_ratio >= 80.0 else 'Fashion-Focused'
        elif store_type == 'Basic':
            store_style_profile = 'Basic-Heavy' if basic_ratio >= 80.0 else 'Basic-Focused'
        else:
            if abs(fashion_ratio - 50.0) <= 10.0:
                store_style_profile = 'Perfectly-Balanced'
            else:
                store_style_profile = 'Fashion-Leaning' if fashion_ratio > 50.0 else 'Basic-Leaning'

        # Compute confidence: higher when API label present and when ratio far from 50%
        distance = abs(fashion_ratio - 50.0) / 50.0  # 0..1
        if api_class in ['Fashion', 'Basic']:
            type_confidence = min(1.0, 0.6 + 0.4 * distance)
        else:
            type_confidence = min(1.0, 0.4 + 0.6 * distance)
        
        # Estimate capacity using real data
        size_tier, estimated_capacity, capacity_rationale = estimate_store_capacity_from_real_data(
            total_amt, total_qty, sku_count, category_count
        )
        
        # Calculate additional metrics
        avg_price_per_unit = total_amt / total_qty if total_qty > 0 else 0
        sales_per_sku = total_amt / sku_count if sku_count > 0 else 0
        
        store_metrics.append({
            'str_code': store_code,
            'store_type': store_type,
            'store_style_profile': store_style_profile,
            'fashion_ratio': round(fashion_ratio, 2),
            'basic_ratio': round(basic_ratio, 2),
            'size_tier': size_tier,
            'estimated_rack_capacity': estimated_capacity,
            'capacity_rationale': capacity_rationale,
            'total_sales_amt': round(total_amt, 2),
            'total_sales_qty': round(total_qty, 2),
            'sku_diversity': sku_count,
            'category_count': category_count,
            'subcategory_count': subcategory_count,
            'avg_price_per_unit': round(avg_price_per_unit, 2),
            'sales_per_sku': round(sales_per_sku, 2),
            'type_confidence_score': round(type_confidence, 3),
            'data_source': 'Real API Sales Data',
            'calculation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return pd.DataFrame(store_metrics)

def merge_with_existing_data(enriched_df: pd.DataFrame, temp_df: pd.DataFrame, 
                           cluster_df: pd.DataFrame) -> pd.DataFrame:
    """Merge enriched attributes with existing temperature and clustering data."""
    print("Merging with existing data sources...")
    
    # Start with enriched data
    merged_df = enriched_df.copy()
    # Normalize dtypes for merge keys
    if 'str_code' in merged_df.columns:
        merged_df['str_code'] = merged_df['str_code'].astype(str)
    if 'str_code' in temp_df.columns:
        temp_df['str_code'] = temp_df['str_code'].astype(str)
    if 'str_code' in cluster_df.columns:
        cluster_df['str_code'] = cluster_df['str_code'].astype(str)
    
    # Merge temperature data if available
    if not temp_df.empty:
        temp_cols = ['str_code', 'feels_like_temperature', 'temperature_band']
        available_temp_cols = [col for col in temp_cols if col in temp_df.columns]
        if available_temp_cols:
            merged_df = merged_df.merge(
                temp_df[available_temp_cols], 
                on='str_code', 
                how='left'
            )
            print(f"  ✓ Merged temperature data: {len(available_temp_cols)} columns")
    
    # Merge clustering data if available
    if not cluster_df.empty:
        cluster_cols = ['str_code', 'Cluster']
        available_cluster_cols = [col for col in cluster_cols if col in cluster_df.columns]
        if available_cluster_cols:
            merged_df = merged_df.merge(
                cluster_df[available_cluster_cols], 
                on='str_code', 
                how='left'
            )
            print(f"  ✓ Merged clustering data: {len(available_cluster_cols)} columns")
    
    return merged_df

def generate_analysis_report(enriched_df: pd.DataFrame, report_file: str) -> None:
    """Generate comprehensive analysis report."""
    print("Generating store attribute analysis report...")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Store Attribute Enrichment Analysis Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Stores Analyzed:** {len(enriched_df):,}\n\n")
        
        # Store Type Distribution
        f.write("## Store Type Distribution\n\n")
        type_dist = enriched_df['store_type'].value_counts()
        for store_type, count in type_dist.items():
            percentage = (count / len(enriched_df)) * 100
            f.write(f"- **{store_type}:** {count:,} stores ({percentage:.1f}%)\n")
        
        # Store Style Profile Distribution
        f.write("\n## Store Style Profile Distribution\n\n")
        style_dist = enriched_df['store_style_profile'].value_counts()
        for style, count in style_dist.items():
            percentage = (count / len(enriched_df)) * 100
            f.write(f"- **{style}:** {count:,} stores ({percentage:.1f}%)\n")
        
        # Size Tier Distribution
        f.write("\n## Store Size Tier Distribution\n\n")
        size_dist = enriched_df['size_tier'].value_counts()
        for size, count in size_dist.items():
            percentage = (count / len(enriched_df)) * 100
            f.write(f"- **{size}:** {count:,} stores ({percentage:.1f}%)\n")
        
        # Fashion/Basic Ratio Statistics
        f.write("\n## Fashion/Basic Ratio Statistics\n\n")
        f.write(f"- **Average Fashion Ratio:** {enriched_df['fashion_ratio'].mean():.1f}%\n")
        f.write(f"- **Average Basic Ratio:** {enriched_df['basic_ratio'].mean():.1f}%\n")
        f.write(f"- **Fashion Ratio Range:** {enriched_df['fashion_ratio'].min():.1f}% - {enriched_df['fashion_ratio'].max():.1f}%\n")
        f.write(f"- **Basic Ratio Range:** {enriched_df['basic_ratio'].min():.1f}% - {enriched_df['basic_ratio'].max():.1f}%\n")
        
        # Capacity Statistics
        f.write("\n## Store Capacity Statistics\n\n")
        f.write(f"- **Average Estimated Capacity:** {enriched_df['estimated_rack_capacity'].mean():.0f} units\n")
        f.write(f"- **Capacity Range:** {enriched_df['estimated_rack_capacity'].min()} - {enriched_df['estimated_rack_capacity'].max()} units\n")
        f.write(f"- **Average SKU Diversity:** {enriched_df['sku_diversity'].mean():.0f} SKUs per store\n")
        
        # Data Quality Metrics
        f.write("\n## Data Quality Metrics\n\n")
        f.write(f"- **Average Type Confidence Score:** {enriched_df['type_confidence_score'].mean():.3f}\n")
        f.write(f"- **Stores with High Confidence (>0.8):** {(enriched_df['type_confidence_score'] > 0.8).sum():,}\n")
        f.write(f"- **Stores with Medium Confidence (0.5-0.8):** {((enriched_df['type_confidence_score'] >= 0.5) & (enriched_df['type_confidence_score'] <= 0.8)).sum():,}\n")
        f.write(f"- **Stores with Low Confidence (<0.5):** {(enriched_df['type_confidence_score'] < 0.5).sum():,}\n")
        
        # Sample Records
        f.write("\n## Sample Store Records\n\n")
        sample_stores = enriched_df.head(5)
        for _, store in sample_stores.iterrows():
            f.write(f"### Store {store['str_code']}\n")
            f.write(f"- **Type:** {store['store_type']} ({store['store_style_profile']})\n")
            f.write(f"- **Fashion/Basic Ratio:** {store['fashion_ratio']:.1f}% / {store['basic_ratio']:.1f}%\n")
            f.write(f"- **Size Tier:** {store['size_tier']} (Capacity: {store['estimated_rack_capacity']} units)\n")
            f.write(f"- **SKU Diversity:** {store['sku_diversity']} SKUs across {store['category_count']} categories\n")
            f.write(f"- **Confidence Score:** {store['type_confidence_score']:.3f}\n\n")

def main():
    """Main execution function."""
    print("=" * 60)
    print("STORE ATTRIBUTE ENRICHMENT - REAL DATA ONLY")
    print("=" * 60)
    
    # Parse CLI for period-awareness
    args = _parse_args()
    target_yyyymm = args.target_yyyymm
    target_period = args.target_period
    period_label = get_period_label(target_yyyymm, target_period)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Load real data sources
    sales_df = load_real_sales_data(
        target_yyyymm=target_yyyymm,
        target_period=target_period,
        source_yyyymm=getattr(args, 'source_yyyymm', None),
        source_period=getattr(args, 'source_period', None),
    )
    if sales_df.empty:
        print("❌ ERROR: No sales data available. Cannot proceed with enrichment.")
        return
    
    # Set module-level period context for helpers
    global _TARGET_YYYYMM, _TARGET_PERIOD
    _TARGET_YYYYMM, _TARGET_PERIOD = target_yyyymm, target_period

    temp_df = load_temperature_data()
    cluster_df = load_clustering_data(target_yyyymm, target_period)
    
    # Calculate store attributes from real data
    enriched_df = calculate_store_attributes_from_real_data(
        sales_df,
        force_taxonomy_split=getattr(args, 'force_taxonomy_split', False),
        subcategory_mapping_file=getattr(args, 'subcategory_mapping', None)
    )
    
    if enriched_df.empty:
        print("❌ ERROR: Failed to calculate store attributes.")
        return
    
    # Merge with existing data
    final_df = merge_with_existing_data(enriched_df, temp_df, cluster_df)
    
    # Add stable alias columns for downstream compatibility
    try:
        if 'cluster_id' not in final_df.columns and 'Cluster' in final_df.columns:
            final_df['cluster_id'] = final_df['Cluster']
        if 'fashion_basic_classification' not in final_df.columns and 'store_type' in final_df.columns:
            final_df['fashion_basic_classification'] = final_df['store_type']
    except Exception:
        pass

    # Save enriched store attributes with period-aware filename
    enriched_file = f"output/enriched_store_attributes_{period_label}_{timestamp}.csv"
    final_df.to_csv(enriched_file, index=False)
    print(f"✅ Saved enriched store attributes: {enriched_file}")
    # Create symlink for generic path for downstream steps
    try:
        if os.path.exists(ENRICHED_STORE_ATTRIBUTES_FILE) or os.path.islink(ENRICHED_STORE_ATTRIBUTES_FILE):
            os.remove(ENRICHED_STORE_ATTRIBUTES_FILE)
        os.symlink(os.path.basename(enriched_file), ENRICHED_STORE_ATTRIBUTES_FILE)
        print(f"   ✓ Created generic symlink: {ENRICHED_STORE_ATTRIBUTES_FILE} -> {enriched_file}")
    except Exception as e:
        print(f"   ⚠️ Could not create symlink: {e}")
    print(f"   Period: {period_label}")
    print(f"   Total stores: {len(final_df):,}")
    print(f"   Total attributes: {len(final_df.columns)} columns")
    
    # Generate analysis report with DUAL OUTPUT PATTERN
    # Timestamped version (for backup/inspection)
    timestamped_analysis_file = f"output/store_type_analysis_report_{period_label}_{timestamp}.md"
    generate_analysis_report(final_df, timestamped_analysis_file)
    print(f"✅ Generated timestamped analysis report: {timestamped_analysis_file}")
    
    # Generic version (for pipeline flow)
    generic_analysis_file = STORE_TYPE_ANALYSIS_FILE
    generate_analysis_report(final_df, generic_analysis_file)
    print(f"✅ Generated generic analysis report: {generic_analysis_file}")
    
    # Use timestamped version for manifest registration
    analysis_file = timestamped_analysis_file
    
    # Register outputs in pipeline manifest (generic + period-specific)
    metadata = {
        "target_year": int(target_yyyymm[:4]),
        "target_month": int(target_yyyymm[4:]),
        "target_period": target_period,
        "records": len(final_df),
        "columns": len(final_df.columns)
    }
    register_step_output("step22", "enriched_store_attributes", enriched_file, metadata)
    register_step_output("step22", f"enriched_store_attributes_{period_label}", enriched_file, metadata)
    register_step_output("step22", "store_type_analysis_report", analysis_file, metadata)
    register_step_output("step22", f"store_type_analysis_report_{period_label}", analysis_file, metadata)
    
    # Display summary statistics
    print("\n" + "=" * 60)
    print("ENRICHMENT SUMMARY")
    print("=" * 60)
    print(f"Stores Processed: {len(final_df):,}")
    print(f"Store Types: {final_df['store_type'].nunique()} unique types")
    print(f"Size Tiers: {final_df['size_tier'].nunique()} unique tiers")
    print(f"Average Confidence Score: {final_df['type_confidence_score'].mean():.3f}")
    
    # Store type breakdown
    print("\nStore Type Distribution:")
    type_counts = final_df['store_type'].value_counts()
    for store_type, count in type_counts.items():
        percentage = (count / len(final_df)) * 100
        print(f"  {store_type}: {count:,} ({percentage:.1f}%)")
    
    print("\n✅ Store attribute enrichment completed successfully!")

if __name__ == "__main__":
    main()
