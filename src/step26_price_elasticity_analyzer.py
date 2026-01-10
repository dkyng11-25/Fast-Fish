#!/usr/bin/env python3
"""
Step 26: Price-Band Classifier + Substitution-Elasticity Calculator

This step analyzes pricing patterns and calculates substitution elasticity
between products, building on the product role classifications from Step 25.

Uses ONLY real sales data and price calculations.
Proceeds cautiously with validation at each step.

Author: Data Pipeline Team
Date: 2025-01-23
Version: 1.0 - Methodical Implementation

 HOW TO RUN (CLI + ENV) — Read this before executing
 ----------------------------------------------------
 Overview
 - This script loads real period-specific SPU-level sales via src.config and outputs
   price-band classifications (always) and optional substitution elasticity (can be skipped).
 - It is period-aware and supports future-period labeling while sourcing sales from a prior period.
 - In day-to-day production you typically process ALL clusters. For fast testing you can scope
   upstream steps to a single cluster (e.g., Cluster 22), then run Step 26 normally.

 Quick Start (fast testing with prior-period sales, label outputs for 202510A)
 - When the target period (e.g., 202510A) has no Step 1 sales yet, source sales from 202509A and
   label outputs for 202510A. Also skip elasticity to save time.

   ENV:
     STEP26_SKIP_ELASTICITY=1 \
     STEP26_SOURCE_YYYYMM=202509 \
     STEP26_SOURCE_PERIOD=A

   Command:
     PYTHONPATH=. python3 src/step26_price_elasticity_analyzer.py \
       --target-yyyymm 202510 \
       --target-period A

 Production Run (all clusters, with real current period sales)
 - If the current period’s sales exist, no special ENV is needed. Elasticity may be enabled.

   Command:
     PYTHONPATH=. python3 src/step26_price_elasticity_analyzer.py \
       --target-yyyymm 202510 \
       --target-period A

 Cluster Scoping Notes (steps 7–36)
 - We often test upstream steps (7–25) on a single cluster (e.g., Cluster 22) to accelerate iteration.
 - Step 26 itself will process all products present in the source sales it loads. If your upstream
   inputs (roles from Step 25) were created for a single cluster, this step will effectively operate
   only on that scope. In production, generate roles for ALL clusters and run Step 26 without scoping.

 Period Handling Patterns
 - Target label (for file naming): pass --target-yyyymm/--target-period
 - Source period (for loading sales when the target period lacks data):
     Prefer STEP26_SOURCE_YYYYMM and STEP26_SOURCE_PERIOD
     Fallback: PIPELINE_YYYYMM and PIPELINE_PERIOD (used by config.get_current_period)

 Examples
 - Test mode: target 202510A, source 202509A, skip elasticity
     STEP26_SKIP_ELASTICITY=1 STEP26_SOURCE_YYYYMM=202509 STEP26_SOURCE_PERIOD=A \
     PYTHONPATH=. python3 src/step26_price_elasticity_analyzer.py --target-yyyymm 202510 --target-period A

 - Production: target 202510A, use its own sales (if present), compute elasticity
     PYTHONPATH=. python3 src/step26_price_elasticity_analyzer.py --target-yyyymm 202510 --target-period A

 Environment Variables (checked by this script)
 - STEP26_SKIP_ELASTICITY=1         -> Skips elasticity and outputs only price bands
 - STEP26_SOURCE_YYYYMM=YYYYMM      -> Explicit sales source year-month
 - STEP26_SOURCE_PERIOD=A|B         -> Explicit sales source half-month
 - (Fallback) PIPELINE_YYYYMM/PIPELINE_PERIOD -> Used by config.get_current_period when STEP26_SOURCE_* not set

 Best Practices & Pitfalls
 - Do NOT use synthetic combined files; this loader forbids them.
 - If the script errors with "No valid period-specific sales files ...", set STEP26_SOURCE_* to a prior real period.
 - To speed up: set STEP26_SKIP_ELASTICITY=1. You can re-run later to compute elasticity.
 - Ensure Step 25 outputs are period-consistent with your target label (use manifest or pass explicit files via env STEP26_PRODUCT_ROLES_FILE if needed).
 - For full production coverage, ensure upstream Steps 7–25 are executed for ALL clusters before running Step 26.

 Why these configurations work (and when they don't)
 - Source-from-prior period works because the loader (via src.config) resolves real, period-pure SPU sales.
   You can compute stable price bands from 202509A, then label outputs 202510A for planning. If you forget to
   set STEP26_SOURCE_YYYYMM/PERIOD when 202510A sales don't exist, the loader will fail with the "No valid
   period-specific sales files" error.
 - Skipping elasticity (STEP26_SKIP_ELASTICITY=1) is useful when price bands are sufficient to unblock
   downstream steps (Step 27/28/29). Elasticity requires a critical mass of overlapping store observations
   across product pairs within a category. Sparse data (few common stores) will naturally yield few pairs
   or "Independent" relationships. This is expected and not a bug.
 - Period label vs. loader period: file naming is driven by the target label you pass on CLI. The loader can
   still use a prior period (via STEP26_SOURCE_*), so you keep consistent filenames for planning while using
   real sales from an earlier period when needed.

HOW TO RUN – Reproduction Example (202508A, elasticity skipped)
----------------------------------------------------------------
To reproduce the 202508A price-band analysis we generated while skipping elasticity:

  STEP26_SKIP_ELASTICITY=1 \
  PIPELINE_YYYYMM=202508 PIPELINE_PERIOD=A \
  STEP26_PRODUCT_ROLES_FILE=output/product_role_classifications_202508A_20250918_173324.csv \
  PYTHONPATH=. python3 src/step26_price_elasticity_analyzer.py --target-yyyymm 202508 --target-period A

Notes:
- Loader uses PIPELINE_YYYYMM/PIPELINE_PERIOD for real sales sourcing; filenames use --target-* for labeling.
- Outputs registered in manifest under step26 with period-specific keys.
 This separation prevents accidental reuse of synthetic or misaligned files.

 Common failure modes (and what to do)
 - Zero or tiny price_df after unit price calc:
   • Cause: missing quantity/amount columns after flexible detection, or extreme filtering upstream.
   • Fix: verify that sales files include either split (fashion/basic) or aggregate (total_amount/quantity) fields.
     Ensure Steps 1/14 produced SPU-level rows with required keys: ['str_code','spu_code'].
 - Roles merge yields many nulls:
   • Cause: Step 25 roles file not aligned to the same SPU universe/period.
   • Fix: resolve roles via manifest for the same period label, or pass STEP26_PRODUCT_ROLES_FILE explicitly.
 - Very few elasticity pairs:
   • Cause: category has too few products with overlapping stores; or min_common_stores too high.
   • Fix: this is acceptable for thin categories; price-bands remain valid. You can adjust ELASTICITY_CONFIG
     thresholds later if the business requires broader pairing.

 Manifest notes
 - This step registers outputs under step26 in output/pipeline_manifest.json. Downstream steps (e.g., Step 27/28)
   can resolve period-labeled versions when present. Prefer manifest lookups over hardcoding paths whenever possible.

"""
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from typing import Dict, Tuple, Any, List, Optional
import warnings
from tqdm import tqdm
from itertools import combinations
from src.config import get_period_label
from src.pipeline_manifest import get_manifest, register_step_output

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# ===== CONFIGURATION =====
# Input data sources (no combined/synthetic files)
SALES_DATA_FILE = None  # Forbidden: combined synthetic files are not used
PRODUCT_ROLES_FILE = "output/product_role_classifications.csv"  # Fallback only; prefer manifest
CLUSTER_LABELS_FILE = "output/clustering_results_spu.csv"

# Output files
PRICE_BANDS_FILE = "output/price_band_analysis.csv"
ELASTICITY_MATRIX_FILE = "output/substitution_elasticity_matrix.csv"
PRICE_ANALYSIS_REPORT_FILE = "output/price_elasticity_analysis_report.md"
PRICE_SUMMARY_FILE = "output/price_elasticity_summary.json"

# Create output directory
os.makedirs("output", exist_ok=True)

# ===== PRICE BAND CONFIGURATION =====
# Dynamic price bands based on data distribution
PRICE_BAND_STRATEGY = {
    'method': 'percentile_based',  # Use data-driven percentiles
    'bands': {
        'ECONOMY': {'range': '0-25th percentile', 'label': 'Economy'},
        'VALUE': {'range': '25th-50th percentile', 'label': 'Value'},
        'PREMIUM': {'range': '50th-75th percentile', 'label': 'Premium'},
        'LUXURY': {'range': '75th-100th percentile', 'label': 'Luxury'}
    }
}

# Elasticity calculation parameters
ELASTICITY_CONFIG = {
    'method': 'within_category',  # Calculate within same category/subcategory
    'min_common_stores': 3,  # Minimum stores both products must be sold in
    'correlation_threshold': 0.3  # Minimum correlation for substitution relationship
}

# Optional runtime control via environment variables
# If STEP26_SKIP_ELASTICITY=1 is set, the elasticity calculation will be skipped
SKIP_ELASTICITY = os.getenv("STEP26_SKIP_ELASTICITY", "0") == "1"

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# ===== DATA LOADING FUNCTIONS =====

def _resolve_product_roles_path(period_label: Optional[str]) -> str:
    """Resolve product roles CSV via manifest, with optional period-specific preference.

    Order of preference:
    1) Explicit env override STEP26_PRODUCT_ROLES_FILE
    2) Manifest: step25 -> product_role_classifications_{period_label}
    3) Manifest: step25 -> product_role_classifications
    4) Fallback: PRODUCT_ROLES_FILE
    """
    override = os.getenv("STEP26_PRODUCT_ROLES_FILE")
    if override and os.path.exists(override):
        return override
    try:
        manifest = get_manifest()
        if isinstance(manifest, dict):
            step = manifest.get("step25") or {}
            if period_label:
                key = f"product_role_classifications_{period_label}"
                path = step.get(key, {}).get("path") if isinstance(step.get(key), dict) else step.get(key)
                if path and os.path.exists(path):
                    return path
            key = "product_role_classifications"
            path = step.get(key, {}).get("path") if isinstance(step.get(key), dict) else step.get(key)
            if path and os.path.exists(path):
                return path
    except Exception:
        pass
    return PRODUCT_ROLES_FILE

def load_and_validate_data(period_label: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load and validate all required data sources"""
    log_progress("🔍 Loading data for price-band and elasticity analysis...")
    
    # Load period-specific SPU-level sales with real fashion/basic splits
    try:
        from src.config import get_current_period, load_sales_df_with_fashion_basic
    except Exception:
        from config import get_current_period, load_sales_df_with_fashion_basic
    # Allow explicit source-period override via env (prefer current if not provided)
    env_src_yyyymm = os.getenv("STEP26_SOURCE_YYYYMM") or os.getenv("PIPELINE_SOURCE_YYYYMM")
    env_src_period = os.getenv("STEP26_SOURCE_PERIOD") or os.getenv("PIPELINE_SOURCE_PERIOD")
    if env_src_yyyymm and env_src_period:
        yyyymm, period = env_src_yyyymm, env_src_period
        log_progress(f"   Using source period override: {yyyymm}{period}")
    else:
        yyyymm, period = get_current_period()
    src_path, sales_df = load_sales_df_with_fashion_basic(
        yyyymm, period, require_spu_level=True,
        required_cols=['str_code','spu_code']
    )
    log_progress(f"   ✓ Loaded period-specific sales: {src_path} ({len(sales_df):,} records)")
    
    # Load product role classifications (manifest- and period-aware)
    roles_path = _resolve_product_roles_path(period_label)
    if not roles_path or not os.path.exists(roles_path):
        raise FileNotFoundError(f"Product roles not found (resolved): {roles_path}")
    product_roles_df = pd.read_csv(roles_path)
    log_progress(f"   ✓ Loaded product roles: {len(product_roles_df):,} products")
    
    # Validate minimally required columns with flexible fallbacks
    cols = set(sales_df.columns)
    has_keys = {'str_code','spu_code'}.issubset(cols)
    has_split_amt = {'fashion_sal_amt','basic_sal_amt'}.issubset(cols)
    has_split_qty = {'fashion_sal_qty','basic_sal_qty'}.issubset(cols)
    has_total_amt = any(c in cols for c in ['total_amount','spu_sales_amt','sales_amt','sal_amt'])
    has_total_qty = any(c in cols for c in ['total_quantity','quantity','sales_qty','sal_qty'])
    if not has_keys or not ((has_split_amt or has_total_amt) and (has_split_qty or has_total_qty)):
        missing_parts = []
        if not has_keys:
            missing_parts.append("['str_code','spu_code'] keys")
        if not (has_split_amt or has_total_amt):
            missing_parts.append("amount columns (either split: fashion/basic or aggregate: total_amount/spu_sales_amt/sales_amt/sal_amt)")
        if not (has_split_qty or has_total_qty):
            missing_parts.append("quantity columns (either split: fashion/basic or aggregate: total_quantity/quantity/sales_qty/sal_qty)")
        raise ValueError(f"Missing required sales fields: {', '.join(missing_parts)}")
    
    roles_required = ['spu_code', 'product_role', 'category', 'subcategory']
    roles_missing = [col for col in roles_required if col not in product_roles_df.columns]
    if roles_missing:
        raise ValueError(f"Missing columns in product roles: {roles_missing}")
    
    log_progress(f"   ✓ Data validation passed")
    
    return sales_df, product_roles_df

# ===== PRICE CALCULATION FUNCTIONS =====

def calculate_unit_prices(sales_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate unit prices for each product at each store"""
    log_progress("💰 Calculating unit prices from sales data...")
    
    price_data = []
    
    # Precompute available columns to avoid per-row set lookups
    cols = set(sales_df.columns)
    has_split_amt = {'fashion_sal_amt','basic_sal_amt'}.issubset(cols)
    has_split_qty = {'fashion_sal_qty','basic_sal_qty'}.issubset(cols)

    def _get_total_amount(r: pd.Series) -> float:
        if has_split_amt:
            return float(r.get('fashion_sal_amt', 0) or 0) + float(r.get('basic_sal_amt', 0) or 0)
        for c in ['total_amount','spu_sales_amt','sales_amt','sal_amt']:
            if c in cols:
                try:
                    return float(r.get(c, 0) or 0)
                except Exception:
                    continue
        return 0.0

    def _get_total_quantity(r: pd.Series) -> float:
        if has_split_qty:
            return float(r.get('fashion_sal_qty', 0) or 0) + float(r.get('basic_sal_qty', 0) or 0)
        for c in ['total_quantity','quantity','sales_qty','sal_qty']:
            if c in cols:
                try:
                    return float(r.get(c, 0) or 0)
                except Exception:
                    continue
        return 0.0

    for _, row in tqdm(sales_df.iterrows(), desc="Calculating prices", total=len(sales_df)):
        # Calculate total amounts and quantities with flexible fallbacks
        total_amount = _get_total_amount(row)
        total_quantity = _get_total_quantity(row)
        
        # Calculate unit price (avoid division by zero)
        if total_quantity > 0 and total_amount > 0:
            unit_price = total_amount / total_quantity
            
            # Validate reasonable price range (basic sanity check)
            if 1 <= unit_price <= 1000:  # Reasonable price range for retail items
                price_data.append({
                    'str_code': row['str_code'],
                    'spu_code': row['spu_code'],
                    'unit_price': unit_price,
                    'total_amount': total_amount,
                    'total_quantity': total_quantity,
                    'fashion_amount': float(row.get('fashion_sal_amt', 0) or 0),
                    'basic_amount': float(row.get('basic_sal_amt', 0) or 0),
                    'fashion_quantity': float(row.get('fashion_sal_qty', 0) or 0),
                    'basic_quantity': float(row.get('basic_sal_qty', 0) or 0)
                })
    
    price_df = pd.DataFrame(price_data)
    log_progress(f"   ✓ Calculated prices for {len(price_df):,} store-product combinations")
    
    if len(price_df) == 0:
        raise ValueError("No valid price data could be calculated")
    
    return price_df

def classify_price_bands(price_df: pd.DataFrame, product_roles_df: pd.DataFrame) -> pd.DataFrame:
    """Classify products into price bands using data-driven percentiles"""
    log_progress("🏷️ Classifying products into price bands...")
    
    # Calculate average unit price for each product
    product_prices = price_df.groupby('spu_code').agg({
        'unit_price': ['mean', 'std', 'count'],
        'total_amount': 'sum',
        'total_quantity': 'sum'
    }).reset_index()
    
    # Flatten column names
    product_prices.columns = ['spu_code', 'avg_unit_price', 'price_std', 'price_observations', 
                             'total_sales_amount', 'total_sales_quantity']
    
    # Calculate price percentiles for band classification
    percentiles = np.percentile(product_prices['avg_unit_price'], [25, 50, 75])
    p25, p50, p75 = percentiles
    
    log_progress(f"   📊 Price percentiles: 25th=¥{p25:.2f}, 50th=¥{p50:.2f}, 75th=¥{p75:.2f}")
    
    # Classify into price bands
    def classify_price_band(price):
        if price <= p25:
            return 'ECONOMY'
        elif price <= p50:
            return 'VALUE'
        elif price <= p75:
            return 'PREMIUM'
        else:
            return 'LUXURY'
    
    product_prices['price_band'] = product_prices['avg_unit_price'].apply(classify_price_band)
    product_prices['price_band_range'] = product_prices['price_band'].map({
        'ECONOMY': f'¥1-{p25:.0f}',
        'VALUE': f'¥{p25:.0f}-{p50:.0f}',
        'PREMIUM': f'¥{p50:.0f}-{p75:.0f}',
        'LUXURY': f'¥{p75:.0f}+'
    })
    
    # Merge with product role information
    enhanced_price_data = product_prices.merge(
        product_roles_df[['spu_code', 'product_role', 'category', 'subcategory']], 
        on='spu_code', 
        how='left'
    )
    
    # Calculate price positioning within role
    enhanced_price_data['price_vs_role_avg'] = enhanced_price_data.groupby('product_role')['avg_unit_price'].transform(
        lambda x: (enhanced_price_data.loc[x.index, 'avg_unit_price'] - x.mean()) / x.std() if x.std() > 0 else 0
    )
    
    # Log band distribution
    band_counts = enhanced_price_data['price_band'].value_counts()
    log_progress(f"   ✓ Price band distribution:")
    for band, count in band_counts.items():
        percentage = (count / len(enhanced_price_data)) * 100
        avg_price = enhanced_price_data[enhanced_price_data['price_band'] == band]['avg_unit_price'].mean()
        log_progress(f"     • {band}: {count} products ({percentage:.1f}%) - avg ¥{avg_price:.2f}")
    
    return enhanced_price_data

# ===== SUBSTITUTION ELASTICITY FUNCTIONS =====

def calculate_substitution_elasticity(price_df: pd.DataFrame, product_roles_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate substitution elasticity between products within categories"""
    log_progress("🔄 Calculating substitution elasticity relationships...")
    
    # Merge price data with product information
    price_with_info = price_df.merge(
        product_roles_df[['spu_code', 'category', 'subcategory', 'product_role']], 
        on='spu_code', 
        how='left'
    )
    
    elasticity_results = []
    
    # Group by category for within-category analysis
    for category in tqdm(price_with_info['category'].unique(), desc="Analyzing categories"):
        category_data = price_with_info[price_with_info['category'] == category]
        category_products = category_data['spu_code'].unique()
        
        if len(category_products) < 2:
            continue  # Need at least 2 products for comparison
        
        # Analyze pairs of products within the category
        for product1, product2 in combinations(category_products, 2):
            try:
                p1_data = category_data[category_data['spu_code'] == product1]
                p2_data = category_data[category_data['spu_code'] == product2]
                
                # Find common stores
                common_stores = set(p1_data['str_code']).intersection(set(p2_data['str_code']))
                
                if len(common_stores) >= ELASTICITY_CONFIG['min_common_stores']:
                    # Calculate price and quantity correlations in common stores
                    p1_prices = []
                    p2_prices = []
                    p1_quantities = []
                    p2_quantities = []
                    
                    for store in common_stores:
                        p1_store = p1_data[p1_data['str_code'] == store]
                        p2_store = p2_data[p2_data['str_code'] == store]
                        
                        if len(p1_store) > 0 and len(p2_store) > 0:
                            p1_prices.append(p1_store['unit_price'].iloc[0])
                            p2_prices.append(p2_store['unit_price'].iloc[0])
                            p1_quantities.append(p1_store['total_quantity'].iloc[0])
                            p2_quantities.append(p2_store['total_quantity'].iloc[0])
                    
                    if len(p1_prices) >= 3:  # Need minimum data points
                        # Calculate correlation coefficients
                        price_correlation = np.corrcoef(p1_prices, p2_prices)[0, 1] if len(set(p1_prices)) > 1 and len(set(p2_prices)) > 1 else 0
                        quantity_correlation = np.corrcoef(p1_quantities, p2_quantities)[0, 1] if len(set(p1_quantities)) > 1 and len(set(p2_quantities)) > 1 else 0
                        
                        # Calculate substitution score (inverse of quantity correlation)
                        # High negative correlation suggests substitution
                        substitution_score = -quantity_correlation if not np.isnan(quantity_correlation) else 0
                        
                        # Classify relationship strength
                        if abs(substitution_score) >= 0.7:
                            relationship = 'Strong Substitutes'
                        elif abs(substitution_score) >= 0.4:
                            relationship = 'Moderate Substitutes'
                        elif abs(substitution_score) >= 0.2:
                            relationship = 'Weak Substitutes'
                        else:
                            relationship = 'Independent'
                        
                        elasticity_results.append({
                            'product_1': product1,
                            'product_2': product2,
                            'category': category,
                            'common_stores': len(common_stores),
                            'price_correlation': price_correlation,
                            'quantity_correlation': quantity_correlation,
                            'substitution_score': substitution_score,
                            'relationship_strength': relationship,
                            'avg_price_diff': np.mean(p1_prices) - np.mean(p2_prices),
                            'avg_quantity_diff': np.mean(p1_quantities) - np.mean(p2_quantities)
                        })
            
            except Exception as e:
                # Skip pairs that cause calculation errors
                continue
    
    elasticity_df = pd.DataFrame(elasticity_results)
    
    if len(elasticity_df) > 0:
        # Log elasticity analysis results
        relationship_counts = elasticity_df['relationship_strength'].value_counts()
        log_progress(f"   ✓ Analyzed {len(elasticity_df):,} product pairs:")
        for relationship, count in relationship_counts.items():
            percentage = (count / len(elasticity_df)) * 100
            log_progress(f"     • {relationship}: {count} pairs ({percentage:.1f}%)")
    else:
        log_progress(f"   ⚠️ No valid substitution relationships found")
    
    return elasticity_df

# ===== REPORTING FUNCTIONS =====

def create_price_analysis_summary(price_bands_df: pd.DataFrame, elasticity_df: pd.DataFrame) -> Dict[str, Any]:
    """Create comprehensive summary of price and elasticity analysis"""
    
    summary = {
        'analysis_metadata': {
            'total_products_analyzed': len(price_bands_df),
            'total_product_pairs': len(elasticity_df),
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_method': 'percentile_based_price_bands_with_substitution_elasticity'
        },
        
        'price_band_distribution': {
            band: len(price_bands_df[price_bands_df['price_band'] == band])
            for band in ['ECONOMY', 'VALUE', 'PREMIUM', 'LUXURY']
        },
        
        'price_statistics': {
            'min_price': float(price_bands_df['avg_unit_price'].min()),
            'max_price': float(price_bands_df['avg_unit_price'].max()),
            'median_price': float(price_bands_df['avg_unit_price'].median()),
            'mean_price': float(price_bands_df['avg_unit_price'].mean())
        },
        
        'role_price_analysis': {},
        
        'substitution_analysis': {
            'total_relationships_analyzed': len(elasticity_df),
            'strong_substitutes': len(elasticity_df[elasticity_df['relationship_strength'] == 'Strong Substitutes']) if len(elasticity_df) > 0 and 'relationship_strength' in elasticity_df.columns else 0,
            'moderate_substitutes': len(elasticity_df[elasticity_df['relationship_strength'] == 'Moderate Substitutes']) if len(elasticity_df) > 0 and 'relationship_strength' in elasticity_df.columns else 0,
            'weak_substitutes': len(elasticity_df[elasticity_df['relationship_strength'] == 'Weak Substitutes']) if len(elasticity_df) > 0 and 'relationship_strength' in elasticity_df.columns else 0,
            'independent_products': len(elasticity_df[elasticity_df['relationship_strength'] == 'Independent']) if len(elasticity_df) > 0 and 'relationship_strength' in elasticity_df.columns else 0
        }
    }
    
    # Add role-specific price analysis
    for role in price_bands_df['product_role'].unique():
        if pd.notna(role):
            role_data = price_bands_df[price_bands_df['product_role'] == role]
            summary['role_price_analysis'][role] = {
                'count': len(role_data),
                'avg_price': float(role_data['avg_unit_price'].mean()),
                'price_range': f"¥{role_data['avg_unit_price'].min():.2f}-¥{role_data['avg_unit_price'].max():.2f}",
                'most_common_band': role_data['price_band'].mode().iloc[0] if len(role_data) > 0 else 'N/A'
            }
    
    return summary

def create_detailed_report(price_bands_df: pd.DataFrame, elasticity_df: pd.DataFrame, summary: Dict[str, Any]) -> None:
    """Create detailed analysis report"""
    
    report_content = f"""# Price-Band & Substitution-Elasticity Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Products Analyzed:** {summary['analysis_metadata']['total_products_analyzed']}  
**Product Pairs Analyzed:** {summary['analysis_metadata']['total_product_pairs']}

## Executive Summary

This report provides price-band classifications and substitution-elasticity analysis 
for all products based on real sales data and calculated unit prices.

## Price Band Analysis

### Distribution by Price Band
"""
    
    for band, count in summary['price_band_distribution'].items():
        percentage = (count / summary['analysis_metadata']['total_products_analyzed']) * 100 if summary['analysis_metadata']['total_products_analyzed'] > 0 else 0
        band_data = price_bands_df[price_bands_df['price_band'] == band]
        avg_price = band_data['avg_unit_price'].mean() if len(band_data) > 0 else 0
        
        report_content += f"""
**{band}**
- Count: {count} products ({percentage:.1f}%)
- Average Price: ¥{avg_price:.2f}
- Price Range: {band_data['price_band_range'].iloc[0] if len(band_data) > 0 else 'N/A'}
"""
    
    report_content += f"""
### Price Statistics
- **Minimum Price:** ¥{summary['price_statistics']['min_price']:.2f}
- **Maximum Price:** ¥{summary['price_statistics']['max_price']:.2f}
- **Median Price:** ¥{summary['price_statistics']['median_price']:.2f}
- **Mean Price:** ¥{summary['price_statistics']['mean_price']:.2f}

## Product Role vs Price Band Analysis

"""
    
    for role, role_data in summary['role_price_analysis'].items():
        report_content += f"""### {role} Products
- **Count:** {role_data['count']} products
- **Average Price:** ¥{role_data['avg_price']:.2f}
- **Price Range:** {role_data['price_range']}
- **Most Common Band:** {role_data['most_common_band']}

"""
    
    if len(elasticity_df) > 0:
        report_content += f"""
## Substitution-Elasticity Analysis

### Relationship Distribution
- **Strong Substitutes:** {summary['substitution_analysis']['strong_substitutes']} pairs
- **Moderate Substitutes:** {summary['substitution_analysis']['moderate_substitutes']} pairs  
- **Weak Substitutes:** {summary['substitution_analysis']['weak_substitutes']} pairs
- **Independent Products:** {summary['substitution_analysis']['independent_products']} pairs

### Sample Strong Substitution Relationships

"""
        
        strong_subs = elasticity_df[elasticity_df['relationship_strength'] == 'Strong Substitutes'].head(5)
        for _, pair in strong_subs.iterrows():
            report_content += f"""**{pair['product_1']} ↔ {pair['product_2']}**
- Category: {pair['category']}
- Substitution Score: {pair['substitution_score']:.3f}
- Common Stores: {pair['common_stores']}
- Avg Price Difference: ¥{pair['avg_price_diff']:.2f}

"""
    
    report_content += """
## Methodology

### Price Band Classification
- Uses data-driven percentile approach (25th, 50th, 75th percentiles)
- Based on calculated unit prices from real sales data
- Validated against reasonable price ranges

### Substitution-Elasticity Calculation
- Analyzes product pairs within same categories
- Calculates price and quantity correlations across common stores
- Classifies relationship strength based on correlation thresholds

---
*Generated by Price-Band & Elasticity Analyzer v1.0*
"""
    
    with open(PRICE_ANALYSIS_REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    log_progress(f"   ✓ Saved detailed report: {PRICE_ANALYSIS_REPORT_FILE}")

def main() -> None:
    """Main function for price-band and elasticity analysis"""
    global PRICE_ANALYSIS_REPORT_FILE  # Fix: Move global declaration to the beginning
    start_time = datetime.now()
    log_progress("🚀 Starting Price-Band & Elasticity Analysis (Step 26)...")
    
    try:
        # Period-aware CLI
        import argparse
        parser = argparse.ArgumentParser(description="Step 26: Price & Elasticity (period-aware)")
        parser.add_argument("--target-yyyymm", required=False)
        parser.add_argument("--target-period", required=False, choices=["A","B"])
        args, _ = parser.parse_known_args()
        period_label = None
        if getattr(args, 'target_yyyymm', None) and getattr(args, 'target_period', None):
            period_label = get_period_label(args.target_yyyymm, args.target_period)

        # Step 1: Load and validate data
        sales_df, product_roles_df = load_and_validate_data(period_label=period_label)
        
        # Step 2: Calculate unit prices
        price_df = calculate_unit_prices(sales_df)
        
        # Step 3: Classify price bands
        price_bands_df = classify_price_bands(price_df, product_roles_df)
        
        # Save price bands (DUAL OUTPUT PATTERN - both timestamped and generic)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Always create timestamped version (for backup/inspection)
        if period_label:
            timestamped_price_bands_out = f"output/price_band_analysis_{period_label}_{ts}.csv"
            price_bands_df.to_csv(timestamped_price_bands_out, index=False)
            log_progress(f"✅ Saved timestamped price bands: {timestamped_price_bands_out}")
        
        # Create symlink for generic version (for pipeline flow)
        generic_price_bands_out = PRICE_BANDS_FILE
        if os.path.exists(generic_price_bands_out) or os.path.islink(generic_price_bands_out):
            os.remove(generic_price_bands_out)
        os.symlink(os.path.basename(timestamped_price_bands_out), generic_price_bands_out)
        log_progress(f"✅ Created symlink: {generic_price_bands_out} -> {timestamped_price_bands_out}")
        
        # Use timestamped version for manifest registration if available, otherwise generic
        price_bands_out = timestamped_price_bands_out if period_label else generic_price_bands_out
        
        # Step 4: Calculate substitution elasticity (unless skipped)
        if SKIP_ELASTICITY:
            log_progress("⏭️ Skipping elasticity calculation due to STEP26_SKIP_ELASTICITY=1")
            elasticity_df = pd.DataFrame()
        else:
            elasticity_df = calculate_substitution_elasticity(price_df, product_roles_df)
        
        # Step 5: Save elasticity results (DUAL OUTPUT PATTERN if elasticity calculated)
        elasticity_out = None
        if len(elasticity_df) > 0:
            # Always create timestamped version (for backup/inspection)
            if period_label:
                timestamped_elasticity_out = f"output/substitution_elasticity_matrix_{period_label}_{ts}.csv"
                elasticity_df.to_csv(timestamped_elasticity_out, index=False)
                log_progress(f"✅ Saved timestamped elasticity matrix: {timestamped_elasticity_out}")
            
            # Create symlink for generic version (for pipeline flow)
            generic_elasticity_out = ELASTICITY_MATRIX_FILE
            if os.path.exists(generic_elasticity_out) or os.path.islink(generic_elasticity_out):
                os.remove(generic_elasticity_out)
            os.symlink(os.path.basename(timestamped_elasticity_out), generic_elasticity_out)
            log_progress(f"✅ Created symlink: {generic_elasticity_out} -> {timestamped_elasticity_out}")
            
            # Use timestamped version for manifest registration if available, otherwise generic
            elasticity_out = timestamped_elasticity_out if period_label else generic_elasticity_out
        
        # Step 6: Create summary and report (DUAL OUTPUT PATTERN)
        summary = create_price_analysis_summary(price_bands_df, elasticity_df)
        
        # Always create timestamped version (for backup/inspection)
        if period_label:
            timestamped_summary_out = f"output/price_elasticity_summary_{period_label}_{ts}.json"
            with open(timestamped_summary_out, 'w') as f:
                json.dump(summary, f, indent=2)
            log_progress(f"✅ Saved timestamped summary: {timestamped_summary_out}")
        
        # Always create generic version (for pipeline flow)
        generic_summary_out = PRICE_SUMMARY_FILE
        with open(generic_summary_out, 'w') as f:
            json.dump(summary, f, indent=2)
        log_progress(f"✅ Saved generic summary: {generic_summary_out}")
        
        # Use timestamped version for manifest registration if available, otherwise generic
        summary_out = timestamped_summary_out if period_label else generic_summary_out
        
        # Create analysis report (DUAL OUTPUT PATTERN)
        # Always create timestamped version (for backup/inspection)
        if period_label:
            timestamped_report_out = f"output/price_elasticity_analysis_report_{period_label}_{ts}.md"
            _old_report = PRICE_ANALYSIS_REPORT_FILE
            PRICE_ANALYSIS_REPORT_FILE = timestamped_report_out
            create_detailed_report(price_bands_df, elasticity_df, summary)
            PRICE_ANALYSIS_REPORT_FILE = _old_report
            log_progress(f"✅ Saved timestamped analysis report: {timestamped_report_out}")
        
        # Always create generic version (for pipeline flow)
        generic_report_out = PRICE_ANALYSIS_REPORT_FILE
        _old_report = PRICE_ANALYSIS_REPORT_FILE
        PRICE_ANALYSIS_REPORT_FILE = generic_report_out
        create_detailed_report(price_bands_df, elasticity_df, summary)
        PRICE_ANALYSIS_REPORT_FILE = _old_report
        log_progress(f"✅ Saved generic analysis report: {generic_report_out}")
        
        # Use timestamped version for manifest registration if available, otherwise generic
        report_out = timestamped_report_out if period_label else generic_report_out
        
        # Register outputs in manifest
        try:
            base_meta = {"products_analyzed": int(len(price_bands_df))}
            register_step_output("step26", "price_band_analysis", price_bands_out, base_meta)
            register_step_output("step26", "price_elasticity_summary", summary_out, {})
            register_step_output("step26", "price_elasticity_analysis_report", report_out, {})
            if elasticity_out:
                register_step_output("step26", "substitution_elasticity_matrix", elasticity_out, {"pairs": int(len(elasticity_df))})
            if period_label:
                register_step_output("step26", f"price_band_analysis_{period_label}", price_bands_out, base_meta)
                register_step_output("step26", f"price_elasticity_summary_{period_label}", summary_out, {})
                register_step_output("step26", f"price_elasticity_analysis_report_{period_label}", report_out, {})
                if elasticity_out:
                    register_step_output("step26", f"substitution_elasticity_matrix_{period_label}", elasticity_out, {"pairs": int(len(elasticity_df))})
        except Exception:
            pass
        
        # Print final results
        execution_time = (datetime.now() - start_time).total_seconds()
        log_progress(f"\n🎯 PRICE-BAND & ELASTICITY ANALYSIS RESULTS:")
        log_progress(f"   📊 Products Analyzed: {len(price_bands_df):,}")
        log_progress(f"   💰 Price Bands Assigned:")
        
        band_counts = price_bands_df['price_band'].value_counts()
        for band, count in band_counts.items():
            percentage = (count / len(price_bands_df)) * 100
            log_progress(f"     • {band}: {count} products ({percentage:.1f}%)")
        
        if len(elasticity_df) > 0 and 'relationship_strength' in elasticity_df.columns:
            log_progress(f"   🔄 Substitution Relationships: {len(elasticity_df):,} pairs analyzed")
            strong_subs = len(elasticity_df[elasticity_df['relationship_strength'] == 'Strong Substitutes'])
            log_progress(f"     • Strong Substitutes: {strong_subs} pairs")
        else:
            if SKIP_ELASTICITY:
                log_progress(f"   ℹ️ Elasticity calculation skipped by configuration")
            else:
                log_progress(f"   ⚠️ No substitution relationships found (insufficient common store data)")
        
        log_progress(f"   ⚡ Execution Time: {execution_time:.1f} seconds")
        log_progress(f"\n📁 Generated Files:")
        log_progress(f"   • {price_bands_out}")
        if elasticity_out:
            log_progress(f"   • {elasticity_out}")
        log_progress(f"   • {summary_out}")
        log_progress(f"   • {report_out}")
        
        log_progress(f"\n✅ Price-Band & Elasticity Analysis completed successfully")
        
    except Exception as e:
        log_progress(f"❌ Error in price-band analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main() 