#!/usr/bin/env python3
"""
Step 29: Supply-Demand Gap Analysis

This step provides comprehensive supply-demand gap analysis across multiple dimensions:
- Category and subcategory gaps
- Price band distribution gaps  
- Style orientation gaps (Fashion vs Basic)
- Product role gaps (CORE/SEASONAL/FILLER/CLEARANCE)
- Capacity utilization gaps

Analyzes at least three representative clusters to ensure product pool
can serve each store group effectively.

Author: Data Pipeline Team
Date: 2025-01-24
Version: 1.0 - Comprehensive Supply-Demand Gap Analysis

 HOW TO RUN (CLI + ENV) — Read this before executing
 ----------------------------------------------------
 Overview
 - Period-aware: pass the loader period via CLI flags --target-yyyymm/--target-period.
 - There is NO --period-label flag here; outputs are labeled based on the loader period.
 - For fast testing, you can analyze a prior period (e.g., 202508A) even if your overall target is 202510A.
 - ✅ DUPLICATE COLUMNS: Now handles duplicate columns gracefully with validation

 Quick Start (fast testing with available data)
   Command:
     PYTHONPATH=. python3 src/step29_supply_demand_gap_analysis.py \
       --target-yyyymm 202508 \
       --target-period A

 Production Run (current period)
   Command:
     PYTHONPATH=. python3 src/step29_supply_demand_gap_analysis.py \
       --target-yyyymm 202510 \
       --target-period A

 COMPLETE PIPELINE EXECUTION SEQUENCE (Steps 29-36) — ✅ TESTED 2025-09-27
   # Step 29: Supply-Demand Gap Analysis ✅ WORKS
   PYTHONPATH=. python3 src/step29_supply_demand_gap_analysis.py --target-yyyymm 202508 --target-period A
   
   # Step 31: Gap Analysis Workbook ✅ WORKS  
   PYTHONPATH=. python3 src/step31_gap_analysis_workbook.py --target-yyyymm 202508 --target-period A
   
   # Step 32: Store Allocation ⚠️ DATA ISSUE (not duplicate column related)
   PYTHONPATH=. python3 src/step32_store_allocation.py --period A --target-yyyymm 202508
   
   # Step 33: Store-Level Merchandising Rules ✅ WORKS
   PYTHONPATH=. python3 src/step33_store_level_merchandising_rules.py --target-yyyymm 202508 --target-period A
   
   # Step 34a: Cluster Strategy Optimization ✅ WORKS
   PYTHONPATH=. python3 src/step34a_cluster_strategy_optimization.py --target-yyyymm 202508 --target-period A
   
   # Step 34b: Unify Outputs ✅ WORKS
   PYTHONPATH=. python3 src/step34b_unify_outputs.py --target-yyyymm 202508 --periods A --source enhanced
   
   # Step 35: Merchandising Strategy Deployment ✅ WORKS
   PYTHONPATH=. python3 src/step35_merchandising_strategy_deployment.py --target-yyyymm 202508 --target-period A
   
   # Step 36: Unified Delivery Builder ✅ WORKS
   PYTHONPATH=. python3 src/step36_unified_delivery_builder.py --target-yyyymm 202508 --target-period A
   
   EXECUTION RESULTS (2025-09-27 00:02-00:03):
   ✅ Step 29: Completed in 0.1s - 3 clusters analyzed, duplicate columns handled correctly
   ✅ Step 31: Completed in 0.2s - Excel workbook created, no duplicate column issues  
   ⚠️ Step 32: Failed on empty allocation data (unrelated to duplicate columns)
   ✅ Step 33: Completed in 0.1s - 56 stores processed, 19 rule dimensions per store
   ✅ Step 34a: Completed - 1 cluster strategy built from 56 store rules
   ✅ Step 34b: Completed - Enhanced Fast Fish format unified successfully
   ✅ Step 35: Completed - 53 records, 87 columns, duplicate column handling working
   ✅ Step 36: Completed in 21s - 8,843 rows output, all integrations successful

 Best Practices & Pitfalls
 - Ensure Step 25 roles, Step 26 price bands, and Step 22 store attributes exist for the chosen period.
 - If you encounter "No valid period-specific sales files ...", choose a prior real period for --target-yyyymm/--target-period.
 - Sales data should be in data/api_data/complete_spu_sales_YYYYMMA.csv format.
 - This script does not accept --period-label; downstream consumers should interpret 202508A outputs as inputs for 202510 planning if desired.
 - ⚠️ CRITICAL: Duplicate column fixes ensure cluster_id is preserved during DataFrame merges.
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from typing import Dict, Tuple, Any, List
import warnings
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import sys
# Robust imports for both package and script execution
try:
    from src.config import get_period_label, get_api_data_files  # when running with -m src.module
    import src.config as cfg
    from src.pipeline_manifest import register_step_output, get_manifest
except Exception:
    try:
        from config import get_period_label, get_api_data_files  # when running from src/ directly
        import config as cfg
        from pipeline_manifest import register_step_output, get_manifest
    except Exception:
        HERE = os.path.dirname(__file__)
        for p in [HERE, os.path.join(HERE, '..'), os.path.join(HERE, '..', 'src')]:
            if p not in sys.path:
                sys.path.append(p)
        from config import get_period_label, get_api_data_files
        import config as cfg
        from pipeline_manifest import register_step_output, get_manifest

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# ===== CONFIGURATION =====
# Input data sources (sales loaded period-aware via cfg.load_sales_df_with_fashion_basic)
CLUSTER_LABELS_FILE = "output/clustering_results_spu.csv"
PRODUCT_ROLES_FILE = "output/product_role_classifications.csv"
PRICE_BANDS_FILE = "output/price_band_analysis.csv"
STORE_ATTRIBUTES_FILE = "output/enriched_store_attributes.csv"

# Output files
SUPPLY_DEMAND_GAP_REPORT = "output/supply_demand_gap_analysis_report.md"
GAP_ANALYSIS_DETAILED = "output/supply_demand_gap_detailed.csv"
GAP_SUMMARY_JSON = "output/supply_demand_gap_summary.json"

# Create output directory
os.makedirs("output", exist_ok=True)

# ===== ANALYSIS CONFIGURATION =====
# Select representative clusters for detailed analysis (minimum 3)
REPRESENTATIVE_CLUSTERS = [0, 2, 4]  # Diverse clusters for comprehensive analysis

# Gap thresholds
GAP_THRESHOLDS = {
    'critical': 20,  # >20% gap is critical
    'significant': 10,  # 10-20% gap is significant
    'moderate': 5    # 5-10% gap is moderate
}

# Expected distributions (business benchmarks)
EXPECTED_DISTRIBUTIONS = {
    'style_orientation': {
        'Fashion-Heavy': {'fashion_ratio': 65, 'basic_ratio': 35},
        'Basic-Focus': {'fashion_ratio': 35, 'basic_ratio': 65},
        'Balanced': {'fashion_ratio': 50, 'basic_ratio': 50}
    },
    'product_roles': {
        'CORE': 25,
        'SEASONAL': 30, 
        'FILLER': 35,
        'CLEARANCE': 10
    },
    'price_bands': {
        'ECONOMY': 20,
        'VALUE': 30,
        'STANDARD': 30,
        'PREMIUM': 15,
        'LUXURY': 5
    }
}

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# ===== CLI PARSING (PERIOD-AWARE) =====
def _parse_args():
    """Parse CLI arguments for period-aware Step 29."""
    parser = argparse.ArgumentParser(description="Step 29: Supply-Demand Gap Analysis (period-aware)")
    parser.add_argument("--target-yyyymm", required=True, help="Target year-month for current run, e.g. 202509")
    parser.add_argument("--target-period", choices=["A", "B"], required=True, help="Target period (A or B)")
    return parser.parse_args()

# ===== DATA LOADING AND PREPARATION =====

def _resolve_first_existing(candidates: List[str]) -> str:
    """Return the first existing path from candidates, or the last candidate if none exist."""
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return candidates[-1] if candidates else ""

def load_analysis_data(target_yyyymm: str, target_period: str, period_label: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all required data for supply-demand gap analysis (period-aware, real data only for sales)."""
    log_progress("📊 Loading data for supply-demand gap analysis...")

    # Load sales using period-aware loader; forbid synthetic combined files (handled inside cfg)
    try:
        sales_source_path, sales_df = cfg.load_sales_df_with_fashion_basic(
            target_yyyymm, target_period,
            require_spu_level=True,
            required_cols=['spu_code', 'fashion_sal_amt', 'basic_sal_amt']
        )
        # Normalize store code column naming
        if 'store_code' in sales_df.columns and 'str_code' not in sales_df.columns:
            sales_df = sales_df.rename(columns={'store_code': 'str_code'})
        log_progress(f"   ✓ Loaded sales data: {len(sales_df):,} records from {sales_source_path}")
    except Exception as e:
        log_progress(f"   ❌ Failed to load period-aware sales data: {e}")
        raise
    # Normalize store code dtype
    if 'str_code' in sales_df.columns:
        sales_df['str_code'] = sales_df['str_code'].astype(str)

    # Load cluster assignments (prefer period-labeled if available)
    cluster_candidates = [
        f"output/clustering_results_spu_{period_label}.csv",
        CLUSTER_LABELS_FILE,
    ]
    cluster_path = _resolve_first_existing(cluster_candidates)
    try:
        cluster_df = pd.read_csv(cluster_path)
        # Standardize cluster column name
        if 'Cluster' in cluster_df.columns:
            cluster_df = cluster_df.rename(columns={'Cluster': 'cluster_id'})
        # Normalize store code column naming
        if 'store_code' in cluster_df.columns and 'str_code' not in cluster_df.columns:
            cluster_df = cluster_df.rename(columns={'store_code': 'str_code'})
        log_progress(f"   ✓ Loaded cluster data: {len(cluster_df):,} rows from {cluster_path}")
    except Exception as e:
        log_progress(f"   ⚠️ Failed to load cluster data from {cluster_path}: {e}. Using empty frame.")
        cluster_df = pd.DataFrame(columns=['str_code', 'cluster_id'])
    # Normalize cluster/store dtypes
    if 'str_code' in cluster_df.columns:
        cluster_df['str_code'] = cluster_df['str_code'].astype(str)
    if 'cluster_id' in cluster_df.columns:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            try:
                cluster_df['cluster_id'] = cluster_df['cluster_id'].astype(int)
            except Exception:
                pass

    # Load product roles (prefer period-labeled if available)
    roles_candidates = [
        f"output/product_role_classifications_{period_label}.csv",
        PRODUCT_ROLES_FILE,
    ]
    roles_path = _resolve_first_existing(roles_candidates)
    try:
        roles_df = pd.read_csv(roles_path)
        log_progress(f"   ✓ Loaded product roles: {len(roles_df):,} rows from {roles_path}")
    except Exception as e:
        log_progress(f"   ⚠️ Failed to load product roles from {roles_path}: {e}. Using empty frame.")
        roles_df = pd.DataFrame(columns=['spu_code', 'product_role', 'category', 'subcategory'])

    # Load price bands (prefer period-labeled if available)
    price_candidates = [
        f"output/price_band_analysis_{period_label}.csv",
        PRICE_BANDS_FILE,
    ]
    price_path = _resolve_first_existing(price_candidates)
    try:
        price_df = pd.read_csv(price_path)
        log_progress(f"   ✓ Loaded price bands: {len(price_df):,} rows from {price_path}")
    except Exception as e:
        log_progress(f"   ⚠️ Failed to load price bands from {price_path}: {e}. Using empty frame.")
        price_df = pd.DataFrame(columns=['spu_code', 'price_band', 'avg_unit_price'])

    # Load enriched store attributes (period-aware via config loader, fallback to manifest-resolved path)
    attrs_path, attrs_df = cfg.load_enriched_store_attributes(period_label)
    if attrs_df is not None:
        store_attrs_df = attrs_df.copy()
        source_path = attrs_path or 'period-aware loader'
        # Normalize store code column naming
        if 'store_code' in store_attrs_df.columns and 'str_code' not in store_attrs_df.columns:
            store_attrs_df = store_attrs_df.rename(columns={'store_code': 'str_code'})
        log_progress(f"   ✓ Loaded store attributes: {len(store_attrs_df):,} stores from {source_path}")
    else:
        try:
            store_attrs_df = pd.read_csv(STORE_ATTRIBUTES_FILE)
            if 'store_code' in store_attrs_df.columns and 'str_code' not in store_attrs_df.columns:
                store_attrs_df = store_attrs_df.rename(columns={'store_code': 'str_code'})
            log_progress(f"   ✓ Loaded store attributes: {len(store_attrs_df):,} stores from {STORE_ATTRIBUTES_FILE}")
        except Exception as e:
            log_progress(f"   ⚠️ Failed to load store attributes from {STORE_ATTRIBUTES_FILE}: {e}. Using empty frame.")
            store_attrs_df = pd.DataFrame(columns=['str_code'])
    if 'str_code' in store_attrs_df.columns:
        store_attrs_df['str_code'] = store_attrs_df['str_code'].astype(str)

    return sales_df, cluster_df, roles_df, price_df, store_attrs_df

def prepare_integrated_dataset(sales_df: pd.DataFrame, cluster_df: pd.DataFrame, 
                             roles_df: pd.DataFrame, price_df: pd.DataFrame) -> pd.DataFrame:
    """Create integrated dataset with all dimensions"""
    log_progress("🔗 Integrating data across all dimensions...")
    
    # Start with sales data
    integrated_df = sales_df.copy()
    # Ensure required numeric columns exist to avoid KeyErrors
    for col in ['fashion_sal_amt', 'basic_sal_amt', 'fashion_sal_qty', 'basic_sal_qty']:
        if col not in integrated_df.columns:
            integrated_df[col] = 0
    
    # Add cluster information (ensure no duplicate columns)
    cluster_merge_cols = ['str_code', 'cluster_id']
    available_cluster_cols = [col for col in cluster_merge_cols if col in cluster_df.columns]
    if available_cluster_cols:
        integrated_df = integrated_df.merge(cluster_df[available_cluster_cols], on='str_code', how='inner')
    
    # Add product role information
    role_merge_cols = ['spu_code', 'product_role', 'category', 'subcategory']
    available_role_cols = [col for col in role_merge_cols if col in roles_df.columns]
    if available_role_cols:
        integrated_df = integrated_df.merge(roles_df[available_role_cols], on='spu_code', how='left')
    
    # Add price band information
    price_merge_cols = ['spu_code', 'price_band', 'avg_unit_price']
    available_price_cols = [col for col in price_merge_cols if col in price_df.columns]
    if available_price_cols:
        integrated_df = integrated_df.merge(price_df[available_price_cols], on='spu_code', how='left')
    
    # Remove any duplicate columns that might have been created
    if integrated_df.columns.duplicated().any():
        duplicate_cols = integrated_df.columns[integrated_df.columns.duplicated()].tolist()
        log_progress(f"   ⚠️ Removing duplicate columns: {duplicate_cols}")
        # Keep first occurrence of each column name
        integrated_df = integrated_df.loc[:, ~integrated_df.columns.duplicated(keep='first')]
        
        # Verify we still have cluster_id after deduplication
        if 'cluster_id' not in integrated_df.columns:
            log_progress(f"   ❌ ERROR: cluster_id column was removed during deduplication!")
            log_progress(f"   📋 Available columns after dedup: {list(integrated_df.columns)}")
            raise ValueError("cluster_id column missing after duplicate removal")
    
    # Calculate derived attributes
    integrated_df['total_sales_amt'] = integrated_df['fashion_sal_amt'] + integrated_df['basic_sal_amt']
    integrated_df['total_sales_qty'] = integrated_df['fashion_sal_qty'] + integrated_df['basic_sal_qty']
    
    # Calculate style orientation ratios
    integrated_df['fashion_ratio'] = (integrated_df['fashion_sal_amt'] / integrated_df['total_sales_amt'] * 100).fillna(0)
    integrated_df['basic_ratio'] = (integrated_df['basic_sal_amt'] / integrated_df['total_sales_amt'] * 100).fillna(0)
    
    # Derive style classification from ratios
    def classify_style_orientation(fashion_ratio):
        if fashion_ratio >= 60:
            return 'Fashion-Heavy'
        elif fashion_ratio <= 40:
            return 'Basic-Focus'
        else:
            return 'Balanced'
    
    integrated_df['style_orientation'] = integrated_df['fashion_ratio'].apply(classify_style_orientation)
    
    # Derive seasonal indicator from fashion ratio and timing
    integrated_df['seasonal_indicator'] = integrated_df['fashion_ratio'].apply(
        lambda x: 'Seasonal' if x >= 70 else 'Year-Round'
    )
    
    log_progress(f"   ✓ Created integrated dataset: {len(integrated_df):,} records")
    
    return integrated_df

# ===== GAP ANALYSIS FUNCTIONS =====

def analyze_category_gaps(integrated_df: pd.DataFrame, cluster_id: int) -> Dict[str, Any]:
    """Analyze category and subcategory distribution gaps for a cluster"""
    
    cluster_data = integrated_df[integrated_df['cluster_id'] == cluster_id]
    
    # Category analysis (support multiple schemas)
    cat_col = 'cate_name' if 'cate_name' in cluster_data.columns else ('category' if 'category' in cluster_data.columns else None)
    subcat_col = 'sub_cate_name' if 'sub_cate_name' in cluster_data.columns else ('subcategory' if 'subcategory' in cluster_data.columns else None)
    
    if cat_col is not None:
        category_dist = cluster_data[cat_col].value_counts(normalize=True) * 100
        category_diversity = len(category_dist)
    else:
        category_dist = pd.Series(dtype=float)
        category_diversity = 0
    
    if subcat_col is not None:
        subcategory_dist = cluster_data[subcat_col].value_counts(normalize=True) * 100
        subcategory_diversity = len(subcategory_dist)
    else:
        subcategory_dist = pd.Series(dtype=float)
        subcategory_diversity = 0
    
    # Calculate concentration risk (Herfindahl index)
    category_concentration = sum((category_dist / 100) ** 2)
    subcategory_concentration = sum((subcategory_dist / 100) ** 2)
    
    # Identify gaps (categories with <5% representation)
    underrepresented_categories = category_dist[category_dist < 5].index.tolist()
    underrepresented_subcategories = subcategory_dist[subcategory_dist < 5].index.tolist()
    
    return {
        'category_diversity': category_diversity,
        'subcategory_diversity': subcategory_diversity,
        'category_concentration': category_concentration,
        'subcategory_concentration': subcategory_concentration,
        'underrepresented_categories': underrepresented_categories,
        'underrepresented_subcategories': underrepresented_subcategories,
        'dominant_category': category_dist.index[0] if len(category_dist) > 0 else None,
        'dominant_category_share': category_dist.iloc[0] if len(category_dist) > 0 else 0
    }

def analyze_price_band_gaps(integrated_df: pd.DataFrame, cluster_id: int) -> Dict[str, Any]:
    """Analyze price band distribution gaps for a cluster"""
    
    cluster_data = integrated_df[integrated_df['cluster_id'] == cluster_id]
    
    # Price band distribution (guard for missing column)
    if 'price_band' in cluster_data.columns:
        price_band_dist = cluster_data['price_band'].value_counts(normalize=True) * 100
    else:
        price_band_dist = pd.Series(dtype=float)
    
    gaps = {}
    gap_severity = {}
    
    for band, expected_pct in EXPECTED_DISTRIBUTIONS['price_bands'].items():
        actual_pct = price_band_dist.get(band, 0)
        gap = expected_pct - actual_pct
        
        gaps[band] = gap
        
        if abs(gap) >= GAP_THRESHOLDS['critical']:
            gap_severity[band] = 'critical'
        elif abs(gap) >= GAP_THRESHOLDS['significant']:
            gap_severity[band] = 'significant'
        elif abs(gap) >= GAP_THRESHOLDS['moderate']:
            gap_severity[band] = 'moderate'
        else:
            gap_severity[band] = 'optimal'
    
    # Price range analysis
    if 'avg_unit_price' in cluster_data.columns:
        price_stats = cluster_data['avg_unit_price'].describe()
        min_price = price_stats.get('min', 0)
        max_price = price_stats.get('max', 0)
        mean_price = price_stats.get('mean', 0)
        std_price = price_stats.get('std', 0)
    else:
        min_price = max_price = mean_price = std_price = 0
    
    return {
        'price_band_distribution': price_band_dist.to_dict() if not price_band_dist.empty else {},
        'price_band_gaps': gaps,
        'price_band_gap_severity': gap_severity,
        'price_range_stats': {
            'min_price': min_price,
            'max_price': max_price,
            'avg_price': mean_price,
            'price_std': std_price
        },
        'missing_price_bands': [band for band, gap in gaps.items() if gap > GAP_THRESHOLDS['significant']]
    }

def analyze_style_orientation_gaps(integrated_df: pd.DataFrame, cluster_id: int) -> Dict[str, Any]:
    """Analyze style orientation and fashion/basic balance gaps"""
    
    cluster_data = integrated_df[integrated_df['cluster_id'] == cluster_id]
    
    # Calculate actual style distribution
    style_dist = cluster_data['style_orientation'].value_counts(normalize=True) * 100
    
    # Calculate average fashion/basic ratios
    avg_fashion_ratio = cluster_data['fashion_ratio'].mean()
    avg_basic_ratio = cluster_data['basic_ratio'].mean()
    
    # Determine expected style for this cluster based on ratios
    if avg_fashion_ratio >= 55:
        expected_style = 'Fashion-Heavy'
    elif avg_fashion_ratio <= 45:
        expected_style = 'Basic-Focus'
    else:
        expected_style = 'Balanced'
    
    expected_dist = EXPECTED_DISTRIBUTIONS['style_orientation'][expected_style]
    
    # Calculate gaps
    fashion_gap = expected_dist['fashion_ratio'] - avg_fashion_ratio
    basic_gap = expected_dist['basic_ratio'] - avg_basic_ratio
    
    return {
        'actual_style_distribution': style_dist.to_dict(),
        'expected_style_profile': expected_style,
        'avg_fashion_ratio': avg_fashion_ratio,
        'avg_basic_ratio': avg_basic_ratio,
        'fashion_gap': fashion_gap,
        'basic_gap': basic_gap,
        'style_consistency': style_dist.get(expected_style, 0),
        'style_gap_severity': 'critical' if abs(fashion_gap) > 15 else 'moderate' if abs(fashion_gap) > 8 else 'optimal'
    }

def analyze_product_role_gaps(integrated_df: pd.DataFrame, cluster_id: int) -> Dict[str, Any]:
    """Analyze product role distribution gaps (CORE/SEASONAL/FILLER/CLEARANCE)"""
    
    cluster_data = integrated_df[integrated_df['cluster_id'] == cluster_id]
    
    # Role distribution
    if 'product_role' in cluster_data.columns:
        role_dist = cluster_data['product_role'].value_counts(normalize=True) * 100
    else:
        role_dist = pd.Series(dtype=float)
    
    gaps = {}
    gap_severity = {}
    
    for role, expected_pct in EXPECTED_DISTRIBUTIONS['product_roles'].items():
        actual_pct = role_dist.get(role, 0)
        gap = expected_pct - actual_pct
        
        gaps[role] = gap
        
        if abs(gap) >= GAP_THRESHOLDS['critical']:
            gap_severity[role] = 'critical'
        elif abs(gap) >= GAP_THRESHOLDS['significant']:
            gap_severity[role] = 'significant'
        elif abs(gap) >= GAP_THRESHOLDS['moderate']:
            gap_severity[role] = 'moderate'
        else:
            gap_severity[role] = 'optimal'
    
    return {
        'role_distribution': role_dist.to_dict() if not role_dist.empty else {},
        'role_gaps': gaps,
        'role_gap_severity': gap_severity,
        'missing_roles': [role for role, gap in gaps.items() if gap > GAP_THRESHOLDS['significant']],
        'oversupplied_roles': [role for role, gap in gaps.items() if gap < -GAP_THRESHOLDS['significant']]
    }

def analyze_seasonal_capacity_gaps(integrated_df: pd.DataFrame, store_attrs_df: pd.DataFrame, cluster_id: int) -> Dict[str, Any]:
    """Analyze seasonal and capacity-related gaps"""
    
    cluster_data = integrated_df[integrated_df['cluster_id'] == cluster_id]
    
    # Get cluster stores for capacity analysis
    cluster_stores = cluster_data['str_code'].unique()
    cluster_store_attrs = store_attrs_df[store_attrs_df['str_code'].isin(cluster_stores)]
    
    # Seasonal analysis
    seasonal_dist = cluster_data['seasonal_indicator'].value_counts(normalize=True) * 100
    
    # Capacity utilization
    num_stores = max(1, len(cluster_stores))
    if not cluster_store_attrs.empty and 'estimated_rack_capacity' in cluster_store_attrs.columns:
        avg_capacity = cluster_store_attrs['estimated_rack_capacity'].mean()
        total_products = len(cluster_data)
        capacity_utilization = (total_products / num_stores) / avg_capacity if avg_capacity > 0 else 0
        # Capacity gaps by category
        products_per_store = total_products / num_stores
        capacity_pressure = 'high' if capacity_utilization > 0.8 else 'medium' if capacity_utilization > 0.6 else 'low'
    else:
        avg_capacity = 0
        capacity_utilization = 0
        products_per_store = 0
        capacity_pressure = 'unknown'
    
    return {
        'seasonal_distribution': seasonal_dist.to_dict(),
        'avg_capacity': avg_capacity,
        'capacity_utilization': capacity_utilization,
        'products_per_store': products_per_store,
        'capacity_pressure': capacity_pressure,
        'seasonal_capacity_balance': seasonal_dist.get('Seasonal', 0) / max(capacity_utilization, 0.1)
    }

def perform_comprehensive_cluster_analysis(integrated_df: pd.DataFrame, store_attrs_df: pd.DataFrame, cluster_id: int) -> Dict[str, Any]:
    """Perform comprehensive supply-demand gap analysis for a cluster"""
    
    log_progress(f"   🔍 Analyzing Cluster {cluster_id}...")
    
    # Debug: Check for duplicate columns and fix them
    if integrated_df.columns.duplicated().any():
        duplicate_cols = integrated_df.columns[integrated_df.columns.duplicated()].tolist()
        log_progress(f"   ⚠️ Found duplicate columns: {duplicate_cols}")
        # Remove duplicate columns by keeping only the first occurrence
        integrated_df = integrated_df.loc[:, ~integrated_df.columns.duplicated(keep='first')]
        
        # Verify we still have cluster_id after deduplication
        if 'cluster_id' not in integrated_df.columns:
            log_progress(f"   ❌ ERROR: cluster_id column was removed during deduplication!")
            log_progress(f"   📋 Available columns after dedup: {list(integrated_df.columns)}")
            raise ValueError("cluster_id column missing after duplicate removal")
    
    cluster_data = integrated_df[integrated_df['cluster_id'] == cluster_id]
    
    analysis = {
        'cluster_id': cluster_id,
        'cluster_size': len(cluster_data['str_code'].unique()),
        'total_products': len(cluster_data),
        'unique_spus': cluster_data['spu_code'].nunique(),
        
        # Dimensional gap analyses
        'category_gaps': analyze_category_gaps(integrated_df, cluster_id),
        'price_band_gaps': analyze_price_band_gaps(integrated_df, cluster_id),
        'style_orientation_gaps': analyze_style_orientation_gaps(integrated_df, cluster_id),
        'product_role_gaps': analyze_product_role_gaps(integrated_df, cluster_id),
        'seasonal_capacity_gaps': analyze_seasonal_capacity_gaps(integrated_df, store_attrs_df, cluster_id)
    }
    
    # Calculate overall gap severity score
    gap_scores = []
    
    # Price band gap score
    price_critical = sum(1 for severity in analysis['price_band_gaps']['price_band_gap_severity'].values() if severity == 'critical')
    gap_scores.append(price_critical * 3)
    
    # Role gap score
    role_critical = sum(1 for severity in analysis['product_role_gaps']['role_gap_severity'].values() if severity == 'critical')
    gap_scores.append(role_critical * 3)
    
    # Style gap score
    style_severity = analysis['style_orientation_gaps']['style_gap_severity']
    style_score = 3 if style_severity == 'critical' else 1 if style_severity == 'moderate' else 0
    gap_scores.append(style_score)
    
    overall_gap_severity = sum(gap_scores)
    analysis['overall_gap_severity'] = 'critical' if overall_gap_severity >= 9 else 'significant' if overall_gap_severity >= 5 else 'moderate'
    
    return analysis

# ===== REPORTING FUNCTIONS =====

def create_supply_demand_gap_report(cluster_analyses: List[Dict[str, Any]], generic_report: str = "output/supply_demand_gap_analysis_report.md") -> None:
    """Create comprehensive supply-demand gap analysis report"""
    
    report_content = f"""# Supply-Demand Gap Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Analysis Scope:** {len(cluster_analyses)} Representative Clusters  
**Analysis Dimensions:** Category, Price Band, Style Orientation, Product Roles, Seasonal/Capacity

---

## 🎯 **EXECUTIVE SUMMARY**

This report analyzes supply-demand gaps across multiple product dimensions to ensure 
our product pool can effectively serve each store group. Analysis covers representative 
clusters to identify critical gaps that may impact customer satisfaction and sales performance.

### **Overall Gap Assessment**

"""
    
    # Summary statistics
    critical_clusters = len([c for c in cluster_analyses if c['overall_gap_severity'] == 'critical'])
    significant_clusters = len([c for c in cluster_analyses if c['overall_gap_severity'] == 'significant'])
    
    report_content += f"""- **Critical Gap Clusters:** {critical_clusters}/{len(cluster_analyses)} clusters
- **Significant Gap Clusters:** {significant_clusters}/{len(cluster_analyses)} clusters
- **Total Products Analyzed:** {sum(c['total_products'] for c in cluster_analyses):,}
- **Total Stores Covered:** {sum(c['cluster_size'] for c in cluster_analyses)}

---

## 📊 **DETAILED CLUSTER ANALYSIS**

"""
    
    for analysis in cluster_analyses:
        cluster_id = analysis['cluster_id']
        
        report_content += f"""### **CLUSTER {cluster_id} - Gap Analysis**

**Cluster Profile:**
- **Size:** {analysis['cluster_size']} stores
- **Products:** {analysis['total_products']} total, {analysis['unique_spus']} unique SPUs
- **Overall Gap Severity:** {analysis['overall_gap_severity'].upper()}

#### **Category Dimension Analysis**
"""
        
        cat_gaps = analysis['category_gaps']
        report_content += f"""- **Category Diversity:** {cat_gaps['category_diversity']} categories
- **Subcategory Diversity:** {cat_gaps['subcategory_diversity']} subcategories
- **Concentration Risk:** {cat_gaps['category_concentration']:.3f} (lower = more diverse)
- **Dominant Category:** {cat_gaps['dominant_category']} ({cat_gaps['dominant_category_share']:.1f}%)
- **Underrepresented Categories:** {len(cat_gaps['underrepresented_categories'])} categories
"""
        
        if cat_gaps['underrepresented_categories']:
            report_content += f"  - Missing: {', '.join(cat_gaps['underrepresented_categories'][:5])}\n"
        
        report_content += f"""
#### **Price Band Dimension Analysis**
"""
        
        price_gaps = analysis['price_band_gaps']
        critical_price_gaps = [band for band, severity in price_gaps['price_band_gap_severity'].items() if severity == 'critical']
        
        report_content += f"""- **Price Range:** ¥{price_gaps['price_range_stats']['min_price']:.0f} - ¥{price_gaps['price_range_stats']['max_price']:.0f}
- **Average Price:** ¥{price_gaps['price_range_stats']['avg_price']:.0f}
- **Critical Price Gaps:** {len(critical_price_gaps)} bands
"""
        
        if critical_price_gaps:
            report_content += f"  - Critical Gaps: {', '.join(critical_price_gaps)}\n"
        
        for band, gap in price_gaps['price_band_gaps'].items():
            severity = price_gaps['price_band_gap_severity'][band]
            if severity in ['critical', 'significant']:
                direction = 'shortage' if gap > 0 else 'excess'
                report_content += f"  - **{band}:** {abs(gap):.1f}% {direction} ({severity})\n"
        
        report_content += f"""
#### **Style Orientation Analysis**
"""
        
        style_gaps = analysis['style_orientation_gaps']
        report_content += f"""- **Expected Style:** {style_gaps['expected_style_profile']}
- **Actual Fashion Ratio:** {style_gaps['avg_fashion_ratio']:.1f}%
- **Actual Basic Ratio:** {style_gaps['avg_basic_ratio']:.1f}%
- **Fashion Gap:** {style_gaps['fashion_gap']:.1f}% ({'shortage' if style_gaps['fashion_gap'] > 0 else 'excess'})
- **Style Gap Severity:** {style_gaps['style_gap_severity'].upper()}
"""
        
        report_content += f"""
#### **Product Role Analysis**
"""
        
        role_gaps = analysis['product_role_gaps']
        missing_roles = role_gaps['missing_roles']
        oversupplied_roles = role_gaps['oversupplied_roles']
        
        if missing_roles:
            report_content += f"- **Missing Roles:** {', '.join(missing_roles)}\n"
        if oversupplied_roles:
            report_content += f"- **Oversupplied Roles:** {', '.join(oversupplied_roles)}\n"
        
        for role, gap in role_gaps['role_gaps'].items():
            severity = role_gaps['role_gap_severity'][role]
            if severity in ['critical', 'significant']:
                direction = 'shortage' if gap > 0 else 'excess'
                report_content += f"- **{role}:** {abs(gap):.1f}% {direction} ({severity})\n"
        
        report_content += f"""
#### **Seasonal & Capacity Analysis**
"""
        
        seasonal_gaps = analysis['seasonal_capacity_gaps']
        report_content += f"""- **Capacity Utilization:** {seasonal_gaps['capacity_utilization']:.1%}
- **Products per Store:** {seasonal_gaps['products_per_store']:.1f}
- **Capacity Pressure:** {seasonal_gaps['capacity_pressure'].upper()}
- **Seasonal Balance:** {seasonal_gaps['seasonal_distribution'].get('Seasonal', 0):.1f}% seasonal items

---

"""
    
    report_content += f"""## 🎯 **ACTIONABLE RECOMMENDATIONS**

### **High Priority Actions**

1. **Address Critical Price Gaps**
   - Focus on missing price bands identified in analysis
   - Rebalance oversupplied price segments

2. **Optimize Product Role Distribution**
   - Add missing CORE and SEASONAL products
   - Reduce FILLER oversupply where identified

3. **Enhance Category Diversity**
   - Address underrepresented categories
   - Monitor concentration risk

### **Medium Priority Actions**

1. **Style Orientation Alignment**
   - Adjust fashion/basic ratios per cluster expectations
   - Ensure style consistency within clusters

2. **Capacity Optimization**
   - Monitor high-pressure clusters for inventory management
   - Optimize space allocation for seasonal items

### **Implementation Guidelines**

- **Phase 1 (Immediate):** Address critical gaps in price bands and product roles
- **Phase 2 (Short-term):** Improve category diversity and style alignment  
- **Phase 3 (Medium-term):** Optimize seasonal and capacity utilization

---

*Analysis based on Q2 2025 real sales data across {sum(c['cluster_size'] for c in cluster_analyses)} stores and {sum(c['unique_spus'] for c in cluster_analyses)} unique products.*
"""
    
    with open(SUPPLY_DEMAND_GAP_REPORT, 'w') as f:
        f.write(report_content)
    log_progress(f"✅ Created timestamped supply-demand gap report: {SUPPLY_DEMAND_GAP_REPORT}")
    
    # Also create generic version (for pipeline flow)
    with open(generic_report, 'w') as f:
        f.write(report_content)
    log_progress(f"✅ Created generic supply-demand gap report: {generic_report}")

def save_detailed_analysis(cluster_analyses: List[Dict[str, Any]], generic_detailed: str = "output/supply_demand_gap_detailed.csv", generic_summary: str = "output/supply_demand_gap_summary.json") -> None:
    """Save detailed gap analysis data"""
    
    # Flatten analysis data for CSV export
    detailed_records = []
    
    for analysis in cluster_analyses:
        cluster_id = analysis['cluster_id']
        
        # Base record
        record = {
            'cluster_id': cluster_id,
            'cluster_size': analysis['cluster_size'],
            'total_products': analysis['total_products'],
            'unique_spus': analysis['unique_spus'],
            'overall_gap_severity': analysis['overall_gap_severity']
        }
        
        # Add category gap metrics
        cat_gaps = analysis['category_gaps']
        record.update({
            'category_diversity': cat_gaps['category_diversity'],
            'subcategory_diversity': cat_gaps['subcategory_diversity'],
            'category_concentration': cat_gaps['category_concentration'],
            'dominant_category': cat_gaps['dominant_category'],
            'dominant_category_share': cat_gaps['dominant_category_share']
        })
        
        # Add price band gaps
        price_gaps = analysis['price_band_gaps']
        for band in ['ECONOMY', 'VALUE', 'STANDARD', 'PREMIUM', 'LUXURY']:
            record[f'price_gap_{band.lower()}'] = price_gaps['price_band_gaps'].get(band, 0)
            record[f'price_severity_{band.lower()}'] = price_gaps['price_band_gap_severity'].get(band, 'optimal')
        
        # Add style gaps
        style_gaps = analysis['style_orientation_gaps']
        record.update({
            'fashion_ratio': style_gaps['avg_fashion_ratio'],
            'basic_ratio': style_gaps['avg_basic_ratio'],
            'fashion_gap': style_gaps['fashion_gap'],
            'style_gap_severity': style_gaps['style_gap_severity']
        })
        
        # Add role gaps
        role_gaps = analysis['product_role_gaps']
        for role in ['CORE', 'SEASONAL', 'FILLER', 'CLEARANCE']:
            record[f'role_gap_{role.lower()}'] = role_gaps['role_gaps'].get(role, 0)
            record[f'role_severity_{role.lower()}'] = role_gaps['role_gap_severity'].get(role, 'optimal')
        
        # Add capacity metrics
        seasonal_gaps = analysis['seasonal_capacity_gaps']
        record.update({
            'capacity_utilization': seasonal_gaps['capacity_utilization'],
            'capacity_pressure': seasonal_gaps['capacity_pressure']
        })
        
        detailed_records.append(record)
    
    # Save to CSV (DUAL OUTPUT PATTERN)
    detailed_df = pd.DataFrame(detailed_records)
    detailed_df.to_csv(GAP_ANALYSIS_DETAILED, index=False)
    log_progress(f"✅ Saved timestamped detailed gap analysis: {GAP_ANALYSIS_DETAILED}")
    
    # Create symlink for generic version (for pipeline flow)
    if os.path.exists(generic_detailed) or os.path.islink(generic_detailed):
        os.remove(generic_detailed)
    os.symlink(os.path.basename(GAP_ANALYSIS_DETAILED), generic_detailed)
    log_progress(f"✅ Created symlink: {generic_detailed} -> {GAP_ANALYSIS_DETAILED}")
    
    # Create summary JSON
    summary = {
        'analysis_metadata': {
            'total_clusters_analyzed': len(cluster_analyses),
            'representative_clusters': REPRESENTATIVE_CLUSTERS,
            'analysis_timestamp': datetime.now().isoformat(),
            'gap_analysis_dimensions': [
                'category_diversity',
                'price_band_distribution', 
                'style_orientation',
                'product_role_balance',
                'seasonal_capacity_utilization'
            ]
        },
        'gap_severity_summary': {
            'critical_clusters': len([c for c in cluster_analyses if c['overall_gap_severity'] == 'critical']),
            'significant_clusters': len([c for c in cluster_analyses if c['overall_gap_severity'] == 'significant']),
            'moderate_clusters': len([c for c in cluster_analyses if c['overall_gap_severity'] == 'moderate'])
        },
        'cluster_summaries': {
            f"cluster_{c['cluster_id']}": {
                'overall_severity': c['overall_gap_severity'],
                'category_diversity': c['category_gaps']['category_diversity'],
                'price_band_critical_gaps': len([s for s in c['price_band_gaps']['price_band_gap_severity'].values() if s == 'critical']),
                'missing_product_roles': c['product_role_gaps']['missing_roles'],
                'style_alignment': c['style_orientation_gaps']['style_gap_severity']
            }
            for c in cluster_analyses
        }
    }
    
    with open(GAP_SUMMARY_JSON, 'w') as f:
        json.dump(summary, f, indent=2)
    log_progress(f"✅ Saved timestamped gap summary: {GAP_SUMMARY_JSON}")
    
    # Also create generic version (for pipeline flow)
    with open(generic_summary, 'w') as f:
        json.dump(summary, f, indent=2)
    log_progress(f"✅ Saved generic gap summary: {generic_summary}")

# ===== MAIN EXECUTION =====

def main() -> None:
    """Main function for supply-demand gap analysis"""
    start_time = datetime.now()
    log_progress("🚀 Starting Supply-Demand Gap Analysis...")
    # Declare globals before any reference/assignment in this function
    global STORE_ATTRIBUTES_FILE, SUPPLY_DEMAND_GAP_REPORT, GAP_ANALYSIS_DETAILED, GAP_SUMMARY_JSON
    
    # Parse CLI and derive period label
    args = _parse_args()
    target_yyyymm = args.target_yyyymm
    target_period = args.target_period
    period_label = get_period_label(target_yyyymm, target_period)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Resolve Step 22 store attributes from manifest (prefer period-specific)
    manifest = get_manifest().manifest
    step22_outputs = manifest.get("steps", {}).get("step22", {}).get("outputs", {})
    store_attrs_path = None
    if f"enriched_store_attributes_{period_label}" in step22_outputs:
        store_attrs_path = step22_outputs[f"enriched_store_attributes_{period_label}"]["file_path"]
    elif "enriched_store_attributes" in step22_outputs:
        store_attrs_path = step22_outputs["enriched_store_attributes"]["file_path"]
    else:
        store_attrs_path = STORE_ATTRIBUTES_FILE

    # Set period-aware outputs and selected inputs (DUAL OUTPUT PATTERN)
    STORE_ATTRIBUTES_FILE = store_attrs_path
    
    # Define both timestamped and generic output paths
    timestamped_report = f"output/supply_demand_gap_analysis_report_{period_label}_{timestamp}.md"
    timestamped_detailed = f"output/supply_demand_gap_detailed_{period_label}_{timestamp}.csv"
    timestamped_summary = f"output/supply_demand_gap_summary_{period_label}_{timestamp}.json"
    
    generic_report = "output/supply_demand_gap_analysis_report.md"
    generic_detailed = "output/supply_demand_gap_detailed.csv"
    generic_summary = "output/supply_demand_gap_summary.json"
    
    # Set the timestamped versions for initial creation
    SUPPLY_DEMAND_GAP_REPORT = timestamped_report
    GAP_ANALYSIS_DETAILED = timestamped_detailed
    GAP_SUMMARY_JSON = timestamped_summary

    log_progress(f"   Period: {period_label}")
    log_progress(f"   Using store attributes: {STORE_ATTRIBUTES_FILE}")
    
    try:
        # Load data (NA-safe with robust fallbacks)
        sales_df, cluster_df, roles_df, price_df, store_attrs_df = load_analysis_data(target_yyyymm, target_period, period_label)
        
        # Prepare integrated dataset
        integrated_df = prepare_integrated_dataset(sales_df, cluster_df, roles_df, price_df)
        
        # Perform analysis on representative clusters
        log_progress(f"🔍 Analyzing {len(REPRESENTATIVE_CLUSTERS)} representative clusters...")
        
        cluster_analyses = []
        for cluster_id in REPRESENTATIVE_CLUSTERS:
            analysis = perform_comprehensive_cluster_analysis(integrated_df, store_attrs_df, cluster_id)
            cluster_analyses.append(analysis)
        
        # Create reports
        create_supply_demand_gap_report(cluster_analyses, generic_report)
        save_detailed_analysis(cluster_analyses, generic_detailed, generic_summary)
        
        # Summary results
        log_progress("\n🎯 SUPPLY-DEMAND GAP ANALYSIS RESULTS:")
        log_progress(f"   📊 Clusters Analyzed: {len(cluster_analyses)}")
        log_progress(f"   🏪 Total Stores: {sum(c['cluster_size'] for c in cluster_analyses)}")
        log_progress(f"   📦 Total Products: {sum(c['total_products'] for c in cluster_analyses):,}")
        
        critical_clusters = [c for c in cluster_analyses if c['overall_gap_severity'] == 'critical']
        if critical_clusters:
            log_progress(f"   🚨 Critical Gap Clusters: {len(critical_clusters)} clusters need immediate attention")
        
        log_progress(f"✅ Supply-demand gap analysis completed in {(datetime.now() - start_time).total_seconds():.1f} seconds")
        
        log_progress("\n📁 Generated Files:")
        log_progress(f"   • {SUPPLY_DEMAND_GAP_REPORT}")
        log_progress(f"   • {GAP_ANALYSIS_DETAILED}")
        log_progress(f"   • {GAP_SUMMARY_JSON}")

        # Register outputs in pipeline manifest (generic + period-specific)
        try:
            detailed_df = pd.read_csv(GAP_ANALYSIS_DETAILED)
            records = len(detailed_df)
            columns = len(detailed_df.columns)
        except Exception:
            records, columns = 0, 0

        metadata = {
            "target_year": int(target_yyyymm[:4]),
            "target_month": int(target_yyyymm[4:]),
            "target_period": target_period,
            "records": records,
            "columns": columns
        }
        register_step_output("step29", "supply_demand_gap_report", SUPPLY_DEMAND_GAP_REPORT, metadata)
        register_step_output("step29", f"supply_demand_gap_report_{period_label}", SUPPLY_DEMAND_GAP_REPORT, metadata)
        register_step_output("step29", "supply_demand_gap_detailed", GAP_ANALYSIS_DETAILED, metadata)
        register_step_output("step29", f"supply_demand_gap_detailed_{period_label}", GAP_ANALYSIS_DETAILED, metadata)
        register_step_output("step29", "supply_demand_gap_summary", GAP_SUMMARY_JSON, metadata)
        register_step_output("step29", f"supply_demand_gap_summary_{period_label}", GAP_SUMMARY_JSON, metadata)
        log_progress("📋 Manifest updated with Step 29 outputs (generic + period-specific)")
        
    except Exception as e:
        log_progress(f"❌ Error in supply-demand gap analysis: {e}")
        raise

if __name__ == "__main__":
    main() 