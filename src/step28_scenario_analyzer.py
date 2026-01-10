#!/usr/bin/env python3
"""
Step 28: What-If Scenario Analyzer

This step provides interactive scenario analysis capabilities for testing
product portfolio optimization decisions. Returns impact on sell-through,
revenue, and inventory for different optimization scenarios.

Completes the Product Structure Optimization Module.
Uses ONLY real data with methodical validation.

Author: Data Pipeline Team
Date: 2025-01-23
Version: 1.0 - Methodical Implementation

 HOW TO RUN (CLI + ENV)
 ----------------------
 Overview
 - Period-aware loader: sales are loaded using cfg.load_sales_df_with_fashion_basic(target_yyyymm, target_period).
 - Output labeling can be decoupled using --period-label so you can analyze with prior-period sales and label for a future period.
 - For fast testing you may focus inputs (roles, price bands, gap analysis) on a single cluster; production should use ALL clusters.

 Quick Start (fast testing; analyze with 202509A sales, label outputs 202510A)
   ENV (point to period-labeled inputs we already generated):
     SC28_PRODUCT_ROLES_FILE=output/product_role_classifications_202510A_<timestamp>.csv \\
     SC28_PRICE_BANDS_FILE=output/price_band_analysis_202510A_<timestamp>.csv \\
     SC28_GAP_ANALYSIS_FILE=output/gap_analysis_detailed_202510A_<timestamp>.csv \\
     SC28_GAP_SUMMARY_FILE=output/gap_matrix_summary_202510A_<timestamp>.json

   Command (use prior-period loader; label as future period):
     PYTHONPATH=. python3 src/step28_scenario_analyzer.py \
       --target-yyyymm 202509 \
       --target-period A \
       --period-label 202510A \
       --timestamp-suffix

 Production Run (all clusters)
   Command (use current period for both loader and labeling):
     PYTHONPATH=. python3 src/step28_scenario_analyzer.py \
       --target-yyyymm 202510 \
       --target-period A

 Notes on Overrides
 - If you already know the exact files, prefer SC28_* env vars to avoid manifest lookups:
     SC28_PRODUCT_ROLES_FILE, SC28_PRICE_BANDS_FILE, SC28_GAP_ANALYSIS_FILE, SC28_GAP_SUMMARY_FILE
 - Optional: SC28_SALES_FILE can be set, but it must contain columns: spu_code, fashion_sal_amt, basic_sal_amt.
   If missing, the script falls back to the loader for the target period.

 Best Practices & Pitfalls
 - If target period sales do not exist, analyze with the latest prior period and set --period-label to the target.
 - Avoid synthetic combined files; the loader forbids them.
 - If you get "No valid period-specific sales files ...", point --target-yyyymm/--target-period to a prior real period or set SC28_SALES_FILE to a valid SPU-level sales file with required columns.
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from typing import Dict, Tuple, Any, List, Optional
import warnings
from tqdm import tqdm
import copy
import argparse
try:
    from src.pipeline_manifest import get_step_input, register_step_output  # when run as module
except Exception:  # pragma: no cover
    from pipeline_manifest import get_step_input, register_step_output  # fallback when run as script
try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# ===== CONFIGURATION =====
# Input data sources (sales loaded period-aware via cfg.load_sales_df_with_fashion_basic)
PRODUCT_ROLES_FILE = "output/product_role_classifications.csv"
PRICE_BANDS_FILE = "output/price_band_analysis.csv"
GAP_ANALYSIS_FILE = "output/gap_analysis_detailed.csv"
GAP_SUMMARY_FILE = "output/gap_matrix_summary.json"

# Output files
SCENARIO_RESULTS_FILE = "output/scenario_analysis_results.json"
SCENARIO_REPORT_FILE = "output/scenario_analysis_report.md"
SCENARIO_RECOMMENDATIONS_FILE = "output/scenario_recommendations.csv"

# Create output directory
os.makedirs("output", exist_ok=True)

# ===== SCENARIO ANALYSIS CONFIGURATION =====
SCENARIO_TYPES = {
    'ROLE_OPTIMIZATION': 'Adjust product role distribution in clusters',
    'PRICE_STRATEGY': 'Test price band adjustments',
    'GAP_FILLING': 'Address critical product role gaps',
    'PORTFOLIO_REBALANCING': 'Comprehensive portfolio optimization'
}

# Business impact models (conservative estimates)
IMPACT_MODELS = {
    'sell_through_multipliers': {
        'CORE': {'add': 1.15, 'remove': 0.85},     # +15% ST when adding CORE, -15% when removing
        'SEASONAL': {'add': 1.10, 'remove': 0.90}, # +10% ST when adding SEASONAL
        'FILLER': {'add': 1.05, 'remove': 0.95},   # +5% ST when adding FILLER
        'CLEARANCE': {'add': 0.95, 'remove': 1.05} # -5% ST when adding CLEARANCE (but +5% when removing)
    },
    
    'revenue_multipliers': {
        'CORE': {'add': 1.20, 'remove': 0.80},     # +20% revenue impact for CORE products
        'SEASONAL': {'add': 1.15, 'remove': 0.85}, # +15% revenue impact for SEASONAL
        'FILLER': {'add': 1.05, 'remove': 0.95},   # +5% revenue impact for FILLER
        'CLEARANCE': {'add': 0.90, 'remove': 1.10} # -10% revenue when adding CLEARANCE
    },
    
    'inventory_multipliers': {
        'CORE': {'add': 1.10, 'remove': 0.90},     # +10% inventory efficiency for CORE
        'SEASONAL': {'add': 1.05, 'remove': 0.95}, # +5% inventory efficiency for SEASONAL
        'FILLER': {'add': 1.02, 'remove': 0.98},   # +2% inventory efficiency for FILLER
        'CLEARANCE': {'add': 0.95, 'remove': 1.05} # -5% inventory efficiency for CLEARANCE
    }
}

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# ===== DATA LOADING AND PREPARATION =====

# ===== CONFIG & CLI UTILITIES =====

try:
    # Prefer package-style import if available
    from src import config as cfg  # type: ignore
except Exception:  # pragma: no cover
    import config as cfg  # fallback when run as a script

def _parse_role_mods(items: List[str]) -> Dict[str, int]:
    """Parse role modifications like ['CORE:2', 'SEASONAL:1'] -> {'CORE': 2, 'SEASONAL': 1}"""
    mods: Dict[str, int] = {}
    for it in items or []:
        try:
            role, val = it.split(":", 1)
            mods[role.strip().upper()] = int(val.strip())
        except Exception:
            log_progress(f"   ⚠️  Ignoring malformed modifier: {it}")
    return mods

def _parse_price_adjustments(items: List[str]) -> Dict[str, float]:
    """Parse price adjustments like ['ECONOMY:0.95','PREMIUM:1.08'] -> dict."""
    adj: Dict[str, float] = {}
    for it in items or []:
        try:
            band, val = it.split(":", 1)
            adj[band.strip().upper()] = float(val.strip())
        except Exception:
            log_progress(f"   ⚠️  Ignoring malformed adjustment: {it}")
    return adj

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='What-If Scenario Analyzer for Product Mix Optimization')
    
    # Period-aware execution (new period control)
    parser.add_argument('--target-yyyymm', required=False, 
                       help='Target year-month for current run, e.g. 202509')
    parser.add_argument('--target-period', choices=['A', 'B'], required=False,
                       help='Target period (A or B)')
    
    # Input file overrides (backward compatible)
    parser.add_argument('--sales-file', help='Override sales data file path')
    parser.add_argument('--product-roles-file', help='Override product roles file path')
    parser.add_argument('--price-bands-file', help='Override price bands file path')
    parser.add_argument('--gap-analysis-file', help='Override gap analysis file path')
    parser.add_argument('--gap-summary-file', help='Override gap summary file path')
    
    # Output file overrides (backward compatible)
    parser.add_argument('--results-file', help='Override results output file path')
    parser.add_argument('--report-file', help='Override report output file path')
    parser.add_argument('--recommendations-file', help='Override recommendations output file path')
    
    # Period-aware naming (backward compatible)
    parser.add_argument('--period-label', help='Period label for output files (e.g., 202506A)')
    parser.add_argument('--timestamp-suffix', action='store_true', help='Add timestamp suffix to output files')
    
    # Scenario selection
    parser.add_argument('--scenario', choices=['AUTO', 'ROLE_OPTIMIZATION', 'GAP_FILLING', 'PRICE_STRATEGY'], 
                       default='AUTO', help='Scenario type to analyze')
    parser.add_argument('--cluster-id', type=int, help='Cluster ID for targeted scenarios')
    parser.add_argument('--role-add', action='append', help='Add products to role (format: ROLE:COUNT)')
    parser.add_argument('--role-remove', action='append', help='Remove products from role (format: ROLE:COUNT)')
    parser.add_argument('--adjust', action='append', help='Price adjustment (format: BAND:MULTIPLIER)')
    
    return parser.parse_args()

def _load_yaml_config(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    if yaml is None:
        log_progress("   ⚠️  PyYAML not installed; ignoring --config file")
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                return {}
            return data
    except Exception as e:
        log_progress(f"   ⚠️  Could not load YAML config {path}: {e}")
        return {}

def _env_overrides() -> Dict[str, Any]:
    """Environment variable overrides (prefix SC28_)."""
    m = os.environ.get
    return {
        'sales_file': m('SC28_SALES_FILE'),
        'product_roles_file': m('SC28_PRODUCT_ROLES_FILE'),
        'price_bands_file': m('SC28_PRICE_BANDS_FILE'),
        'gap_analysis_file': m('SC28_GAP_ANALYSIS_FILE'),
        'gap_summary_file': m('SC28_GAP_SUMMARY_FILE'),
        'output_dir': m('SC28_OUTPUT_DIR'),
        'period_label': m('SC28_PERIOD_LABEL'),
    }

def _first_non_none(*vals):
    for v in vals:
        if v is not None and v != "":
            return v
    return None

def parse_role_changes(role_changes: Optional[List[str]]) -> Dict[str, int]:
    """Parse role change arguments (format: ROLE:COUNT) into dictionary"""
    if not role_changes:
        return {}
    
    result = {}
    for item in role_changes:
        if not item or ':' not in item:
            continue
        try:
            role, count = item.split(':', 1)
            result[role.strip()] = int(count.strip())
        except ValueError:
            log_progress(f"   ⚠️  Ignoring malformed role change: {item}")
            continue
    return result

def parse_price_adjustments(adjustments: Optional[List[str]]) -> Dict[str, float]:
    """Parse price adjustment arguments (format: BAND:MULTIPLIER) into dictionary"""
    if not adjustments:
        return {}
    
    result = {}
    for item in adjustments:
        if not item or ':' not in item:
            continue
        try:
            band, multiplier = item.split(':', 1)
            result[band.strip()] = float(multiplier.strip())
        except ValueError:
            log_progress(f"   ⚠️  Ignoring malformed price adjustment: {item}")
            continue
    return result

def resolve_input_file(file_type: str, cli_override: Optional[str], default_path: str, 
                      target_yyyymm: Optional[str], target_period: Optional[str]) -> str:
    """Resolve input file path using manifest with fallback to defaults (period-aware)."""
    # CLI override takes highest precedence
    if cli_override:
        return cli_override
    
    # Environment variable override
    env_var = f"SC28_{file_type.upper()}"
    env_override = os.environ.get(env_var)
    if env_override:
        return env_override
    
    # Period-aware manifest resolution (if target period specified)
    if target_yyyymm and target_period:
        try:
            period_label = cfg.get_period_label(target_yyyymm, target_period)
            manifest_key = f"{file_type}_{period_label}"
            
            # Try to get from manifest based on file type
            manifest_input = None
            if 'sales' in file_type:
                manifest_input = get_step_input('step28', 'sales_data')
            elif 'roles' in file_type:
                manifest_input = get_step_input('step28', 'product_roles')
            elif 'price' in file_type:
                manifest_input = get_step_input('step28', 'price_bands')
            elif 'gap_analysis' in file_type:
                manifest_input = get_step_input('step28', 'gap_analysis')
            elif 'gap_summary' in file_type:
                manifest_input = get_step_input('step28', 'gap_summary')
            
            if manifest_input and os.path.exists(manifest_input):
                log_progress(f"   ✓ Resolved {file_type} from manifest: {manifest_input}")
                return manifest_input
        except Exception as e:
            log_progress(f"   ⚠️  Manifest resolution failed for {file_type}: {e}")
    
    # Fallback to default path
    if os.path.exists(default_path):
        log_progress(f"   ✓ Using default {file_type}: {default_path}")
        return default_path
    else:
        raise FileNotFoundError(f"Required input file not found: {default_path}")

def resolve_configuration(args) -> Dict[str, Any]:
    """Resolve all configuration paths and settings (period-aware)"""
    config = {}
    
    # Handle period control (new period-aware logic)
    target_yyyymm = args.target_yyyymm or os.environ.get('PIPELINE_YYYYMM')
    target_period = args.target_period or os.environ.get('PIPELINE_PERIOD')
    
    # Handle period label for output naming (backward compatible)
    period_label = args.period_label or os.environ.get('SC28_PERIOD_LABEL')
    if not period_label and target_yyyymm and target_period:
        period_label = f"{target_yyyymm}{target_period}"
    elif not period_label:
        # Default to current month if no period specified
        period_label = datetime.now().strftime('%Y%m')
    
    # Handle timestamp suffix (backward compatible)
    timestamp_suffix = args.timestamp_suffix or os.environ.get('SC28_TIMESTAMP_SUFFIX')
    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S') if timestamp_suffix else ''
    
    # Resolve input files (period-aware). For sales, DO NOT fallback to synthetic combined.
    # Respect CLI/env override only; otherwise we'll use cfg.load_sales_df_with_fashion_basic at load time.
    config['sales_file'] = (
        args.sales_file or os.environ.get('SC28_SALES_FILE') or None
    )
    
    config['product_roles_file'] = resolve_input_file('product_roles_file', args.product_roles_file, 
                                                     'output/product_role_classifications.csv',
                                                     target_yyyymm, target_period)
    
    config['price_bands_file'] = resolve_input_file('price_bands_file', args.price_bands_file, 
                                                   'output/price_band_analysis.csv',
                                                   target_yyyymm, target_period)
    
    config['gap_analysis_file'] = resolve_input_file('gap_analysis_file', args.gap_analysis_file, 
                                                    'output/gap_analysis_detailed.csv',
                                                    target_yyyymm, target_period)
    
    config['gap_summary_file'] = resolve_input_file('gap_summary_file', args.gap_summary_file, 
                                                   'output/gap_matrix_summary.json',
                                                   target_yyyymm, target_period)
    
    # Resolve output files with DUAL OUTPUT PATTERN (timestamped + generic)
    timestamped_base = f'scenario_analysis_results_{period_label}'
    if timestamp_str:
        timestamped_base += f'_{timestamp_str}'
    
    # Define both timestamped and generic versions
    config['timestamped_results_file'] = f'output/{timestamped_base}.json'
    config['timestamped_report_file'] = f'output/{timestamped_base}_report.md'
    config['timestamped_recommendations_file'] = f'output/{timestamped_base}_recommendations.csv'
    
    config['generic_results_file'] = 'output/scenario_analysis_results.json'
    config['generic_report_file'] = 'output/scenario_analysis_report.md'
    config['generic_recommendations_file'] = 'output/scenario_recommendations.csv'
    
    # Use explicit overrides if provided, otherwise use timestamped for manifest registration
    config['results_file'] = (args.results_file or 
                             os.environ.get('SC28_RESULTS_FILE') or 
                             config['timestamped_results_file'])
    
    config['report_file'] = (args.report_file or 
                            os.environ.get('SC28_REPORT_FILE') or 
                            config['timestamped_report_file'])
    
    config['recommendations_file'] = (args.recommendations_file or 
                                     os.environ.get('SC28_RECOMMENDATIONS_FILE') or 
                                     config['timestamped_recommendations_file'])
    
    # Scenario parameters (backward compatible)
    config['selected_scenario'] = args.scenario
    config['cluster_id'] = args.cluster_id
    config['role_add'] = parse_role_changes(args.role_add)
    config['role_remove'] = parse_role_changes(args.role_remove)
    config['price_adjustments'] = parse_price_adjustments(args.adjust)
    
    # Persist period info for loaders
    config['target_yyyymm'] = target_yyyymm
    config['target_period'] = target_period
    config['period_label'] = period_label
    
    return config

def load_baseline_data(config: Dict[str, Any]) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Load all baseline data for scenario analysis using resolved configuration paths"""
    log_progress("🔍 Loading baseline data for scenario analysis...")
    
    # Validate file existence first (sales handled separately via period-aware loader)
    required_files = [config['product_roles_file'], config['price_bands_file'], 
                     config['gap_analysis_file'], config['gap_summary_file']]
    for file_path in required_files:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Required file not found: {file_path}")
    
    # Load sales data (period-aware, real data only; fail-fast on synthetic combined)
    log_progress("   📊 Loading sales data (period-aware, real-only)...")
    sales_source_path = None
    if config.get('sales_file'):
        sales_source_path = config['sales_file']
        if cfg._is_combined_synthetic(sales_source_path):
            raise RuntimeError(f"Synthetic combined sales file is forbidden: {sales_source_path}")
        tmp_df = pd.read_csv(sales_source_path)
        # If override lacks required splits, fallback to loader for the target period
        if not {'spu_code', 'fashion_sal_amt', 'basic_sal_amt'}.issubset(tmp_df.columns):
            log_progress("      → Override missing required columns; using period-aware loader instead")
            sales_source_path, sales_df = cfg.load_sales_df_with_fashion_basic(
                config.get('target_yyyymm'), config.get('target_period'),
                require_spu_level=True,
                required_cols=['spu_code', 'fashion_sal_amt', 'basic_sal_amt']
            )
        else:
            sales_df = tmp_df
    else:
        sales_source_path, sales_df = cfg.load_sales_df_with_fashion_basic(
            config.get('target_yyyymm'), config.get('target_period'),
            require_spu_level=True,
            required_cols=['spu_code', 'fashion_sal_amt', 'basic_sal_amt']
        )
    log_progress(f"      → Loaded {len(sales_df):,} records from {sales_source_path or 'dataframe override'}")
    
    # Load product roles
    log_progress("   🏷️  Loading product roles...")
    product_roles_df = pd.read_csv(config['product_roles_file'])
    log_progress(f"      → Loaded {len(product_roles_df):,} role classifications from {config['product_roles_file']}")
    
    # Load price bands
    log_progress("   💰 Loading price bands...")
    price_bands_df = pd.read_csv(config['price_bands_file'])
    log_progress(f"      → Loaded {len(price_bands_df):,} price band records from {config['price_bands_file']}")
    log_progress(f"   ✓ Loaded price bands: {len(price_bands_df):,} products")
    
    # Validate price bands columns
    required_price_cols = ['spu_code', 'price_band', 'avg_unit_price']
    missing_price_cols = [col for col in required_price_cols if col not in price_bands_df.columns]
    if missing_price_cols:
        raise ValueError(f"Missing required columns in price bands: {missing_price_cols}")
    
    # Load gap analysis
    gap_analysis_df = pd.read_csv(config['gap_analysis_file'])
    log_progress(f"   ✓ Loaded gap analysis: {len(gap_analysis_df):,} clusters")
    
    # Validate gap analysis columns
    required_gap_cols = ['cluster_id', 'total_products', 'total_stores']
    missing_gap_cols = [col for col in required_gap_cols if col not in gap_analysis_df.columns]
    if missing_gap_cols:
        raise ValueError(f"Missing required columns in gap analysis: {missing_gap_cols}")
    
    # Load gap summary
    with open(config['gap_summary_file'], 'r') as f:
        gap_summary = json.load(f)
    log_progress(f"   ✓ Loaded gap summary")
    
    # Validate gap summary structure
    required_summary_keys = ['gap_severity_counts', 'cluster_summary']
    missing_summary_keys = [key for key in required_summary_keys if key not in gap_summary]
    if missing_summary_keys:
        raise ValueError(f"Missing required keys in gap summary: {missing_summary_keys}")
    
    return sales_df, product_roles_df, price_bands_df, gap_analysis_df, gap_summary

def calculate_baseline_metrics(sales_df: pd.DataFrame, product_roles_df: pd.DataFrame, 
                              price_bands_df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate baseline performance metrics"""
    log_progress("📊 Calculating baseline performance metrics...")
    
    # Merge all data
    enhanced_sales = sales_df.merge(
        product_roles_df[['spu_code', 'product_role', 'category', 'subcategory']], 
        on='spu_code', 
        how='left'
    ).merge(
        price_bands_df[['spu_code', 'price_band', 'avg_unit_price']], 
        on='spu_code', 
        how='left'
    )
    
    # Calculate baseline metrics
    # Robust quantity handling (qty columns may be absent)
    total_amt = pd.to_numeric(enhanced_sales.get('fashion_sal_amt'), errors='coerce').fillna(0).sum() + \
                pd.to_numeric(enhanced_sales.get('basic_sal_amt'), errors='coerce').fillna(0).sum()
    if {'fashion_sal_qty', 'basic_sal_qty'}.issubset(enhanced_sales.columns):
        total_qty = pd.to_numeric(enhanced_sales['fashion_sal_qty'], errors='coerce').fillna(0).sum() + \
                    pd.to_numeric(enhanced_sales['basic_sal_qty'], errors='coerce').fillna(0).sum()
    else:
        total_qty = None
    
    baseline = {
        'total_products': len(enhanced_sales),
        'total_sales_amount': total_amt,
        'total_sales_quantity': total_qty if total_qty is not None else 0,
        'avg_sell_through_rate': 75.0,  # Conservative baseline estimate
        'avg_inventory_days': 45.0,     # Conservative baseline estimate
        
        'role_distribution': {},
        'price_band_distribution': {},
        'performance_by_role': {},
        'performance_by_price_band': {}
    }
    
    # Role distribution and performance
    total_products = len(enhanced_sales)
    for role in ['CORE', 'SEASONAL', 'FILLER', 'CLEARANCE']:
        role_data = enhanced_sales[enhanced_sales['product_role'] == role]
        count = len(role_data)
        percentage = (count / total_products) * 100 if total_products > 0 else 0
        
        role_sales = pd.to_numeric(role_data.get('fashion_sal_amt'), errors='coerce').fillna(0).sum() + \
                     pd.to_numeric(role_data.get('basic_sal_amt'), errors='coerce').fillna(0).sum()
        if {'fashion_sal_qty', 'basic_sal_qty'}.issubset(role_data.columns):
            role_qty = pd.to_numeric(role_data['fashion_sal_qty'], errors='coerce').fillna(0).sum() + \
                       pd.to_numeric(role_data['basic_sal_qty'], errors='coerce').fillna(0).sum()
        else:
            role_qty = 0
        
        baseline['role_distribution'][role] = {
            'count': count,
            'percentage': percentage,
            'total_sales': role_sales,
            'total_quantity': role_qty,
            'avg_unit_price': role_sales / role_qty if role_qty > 0 else 0
        }
    
    # Price band distribution
    for band in ['ECONOMY', 'VALUE', 'PREMIUM', 'LUXURY']:
        band_data = enhanced_sales[enhanced_sales['price_band'] == band]
        count = len(band_data)
        percentage = (count / total_products) * 100 if total_products > 0 else 0
        
        baseline['price_band_distribution'][band] = {
            'count': count,
            'percentage': percentage
        }
    
    log_progress(f"   ✓ Calculated baseline metrics for {total_products} products")
    return baseline

# ===== SCENARIO ANALYSIS ENGINE =====

class WhatIfScenarioAnalyzer:
    """Main scenario analysis engine"""
    
    def __init__(self, baseline_data: Dict[str, Any]):
        # Accept either a flat baseline dict or a wrapper dict containing
        # a 'baseline_metrics' key. Older callers passed a flat dict with
        # keys like 'avg_sell_through_rate' while newer code may pass a
        # structure that includes additional frames (sales_data, roles, etc.)
        # and nests the actual baseline under 'baseline_metrics'.
        if isinstance(baseline_data, dict) and 'baseline_metrics' in baseline_data:
            # Unwrap to the metrics so analyzer methods can access expected keys
            # such as 'avg_sell_through_rate' and 'price_band_distribution'.
            self.baseline = baseline_data.get('baseline_metrics', {})
        else:
            self.baseline = baseline_data
        self.impact_models = IMPACT_MODELS
        log_progress("   ✓ Initialized What-If Scenario Analyzer")
    
    def analyze_role_optimization_scenario(self, cluster_id: int, role_changes: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """
        Analyze scenario where product roles are adjusted in a specific cluster
        
        Args:
            cluster_id: Target cluster for optimization
            role_changes: {'CORE': {'add': 2, 'remove': 0}, 'SEASONAL': {'add': 1, 'remove': 3}}
        """
        log_progress(f"   🔄 Analyzing role optimization for Cluster {cluster_id}...")
        
        # Calculate impacts for each role change
        total_st_impact = 1.0
        total_revenue_impact = 1.0
        total_inventory_impact = 1.0
        
        changes_summary = []
        
        for role, changes in role_changes.items():
            add_count = changes.get('add', 0)
            remove_count = changes.get('remove', 0)
            
            if add_count > 0:
                st_mult = self.impact_models['sell_through_multipliers'][role]['add']
                rev_mult = self.impact_models['revenue_multipliers'][role]['add']
                inv_mult = self.impact_models['inventory_multipliers'][role]['add']
                
                # Scale impact by number of products changed
                scaled_st = 1 + (st_mult - 1) * (add_count / 10)  # Scale factor
                scaled_rev = 1 + (rev_mult - 1) * (add_count / 10)
                scaled_inv = 1 + (inv_mult - 1) * (add_count / 10)
                
                total_st_impact *= scaled_st
                total_revenue_impact *= scaled_rev
                total_inventory_impact *= scaled_inv
                
                changes_summary.append(f"Add {add_count} {role} products")
            
            if remove_count > 0:
                st_mult = self.impact_models['sell_through_multipliers'][role]['remove']
                rev_mult = self.impact_models['revenue_multipliers'][role]['remove']
                inv_mult = self.impact_models['inventory_multipliers'][role]['remove']
                
                # Scale impact by number of products changed
                scaled_st = 1 + (st_mult - 1) * (remove_count / 10)
                scaled_rev = 1 + (rev_mult - 1) * (remove_count / 10)
                scaled_inv = 1 + (inv_mult - 1) * (remove_count / 10)
                
                total_st_impact *= scaled_st
                total_revenue_impact *= scaled_rev
                total_inventory_impact *= scaled_inv
                
                changes_summary.append(f"Remove {remove_count} {role} products")
        
        # Calculate absolute impacts
        baseline_st = self.baseline['avg_sell_through_rate']
        baseline_revenue = self.baseline['total_sales_amount']
        baseline_inventory = self.baseline['avg_inventory_days']
        
        new_st = baseline_st * total_st_impact
        new_revenue = baseline_revenue * total_revenue_impact
        new_inventory = baseline_inventory * total_inventory_impact
        
        # Calculate deltas
        delta_st_pct = ((new_st - baseline_st) / baseline_st) * 100
        delta_revenue = new_revenue - baseline_revenue
        delta_inventory_days = new_inventory - baseline_inventory
        
        # Calculate confidence and risk
        total_products_changed = sum([
            changes.get('add', 0) + changes.get('remove', 0) 
            for changes in role_changes.values()
        ])
        
        confidence = max(0.5, min(0.95, 1 - (total_products_changed / 20)))  # Lower confidence for bigger changes
        
        risk_factors = []
        if abs(delta_st_pct) > 10:
            risk_factors.append("High sell-through impact")
        if abs(delta_revenue / baseline_revenue) > 0.15:
            risk_factors.append("High revenue impact")
        if total_products_changed > 10:
            risk_factors.append("Large portfolio change")
        
        return {
            'scenario_type': 'ROLE_OPTIMIZATION',
            'cluster_id': cluster_id,
            'changes_summary': changes_summary,
            'delta_sell_through_pct': round(delta_st_pct, 2),
            'delta_revenue': round(delta_revenue, 2),
            'delta_inventory_days': round(delta_inventory_days, 1),
            'new_sell_through_rate': round(new_st, 1),
            'new_revenue': round(new_revenue, 2),
            'new_inventory_days': round(new_inventory, 1),
            'confidence_score': round(confidence, 3),
            'risk_factors': risk_factors,
            'products_changed': total_products_changed
        }
    
    def analyze_gap_filling_scenario(self, cluster_id: int, gap_fixes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze scenario where critical gaps are addressed
        
        Args:
            cluster_id: Target cluster
            gap_fixes: [{'role': 'CORE', 'gap_percentage': 15, 'products_to_add': 3}]
        """
        log_progress(f"   🔧 Analyzing gap-filling scenario for Cluster {cluster_id}...")
        
        # Convert gap fixes to role changes
        role_changes = {}
        for fix in gap_fixes:
            role = fix['role']
            products_to_add = fix['products_to_add']
            
            if role not in role_changes:
                role_changes[role] = {'add': 0, 'remove': 0}
            
            role_changes[role]['add'] += products_to_add
        
        # Use role optimization analysis with gap context
        result = self.analyze_role_optimization_scenario(cluster_id, role_changes)
        result['scenario_type'] = 'GAP_FILLING'
        result['gap_fixes_applied'] = gap_fixes
        
        # Adjust confidence for gap-filling (typically higher confidence)
        result['confidence_score'] = min(0.95, result['confidence_score'] * 1.2)
        
        return result
    
    def analyze_price_strategy_scenario(self, price_adjustments: Dict[str, float]) -> Dict[str, Any]:
        """
        Analyze scenario where price bands are adjusted
        
        Args:
            price_adjustments: {'ECONOMY': 0.95, 'PREMIUM': 1.10}  # 5% decrease, 10% increase
        """
        log_progress(f"   💰 Analyzing price strategy scenario...")
        
        # Calculate price elasticity impacts
        total_revenue_impact = 1.0
        total_st_impact = 1.0
        
        changes_summary = []
        
        for band, multiplier in price_adjustments.items():
            # Price elasticity: typically -1.5 for retail (1% price increase = 1.5% demand decrease)
            elasticity = -1.5
            price_change_pct = (multiplier - 1) * 100
            demand_change_pct = elasticity * price_change_pct
            
            # Impact calculations
            revenue_impact = multiplier * (1 + demand_change_pct / 100)
            st_impact = 1 + demand_change_pct / 100
            
            # Weight by band's share of portfolio
            band_weight = self.baseline['price_band_distribution'].get(band, {}).get('percentage', 0) / 100
            
            total_revenue_impact += (revenue_impact - 1) * band_weight
            total_st_impact += (st_impact - 1) * band_weight
            
            changes_summary.append(f"{band}: {price_change_pct:+.1f}% price change")
        
        # Calculate absolute impacts
        baseline_st = self.baseline['avg_sell_through_rate']
        baseline_revenue = self.baseline['total_sales_amount']
        baseline_inventory = self.baseline['avg_inventory_days']
        
        new_st = baseline_st * total_st_impact
        new_revenue = baseline_revenue * total_revenue_impact
        new_inventory = baseline_inventory / total_st_impact  # Better ST = faster inventory turnover
        
        # Calculate deltas
        delta_st_pct = ((new_st - baseline_st) / baseline_st) * 100
        delta_revenue = new_revenue - baseline_revenue
        delta_inventory_days = new_inventory - baseline_inventory
        
        # Risk assessment for price changes
        risk_factors = []
        if any(abs(mult - 1) > 0.2 for mult in price_adjustments.values()):
            risk_factors.append("Large price adjustments")
        if delta_st_pct < -10:
            risk_factors.append("Significant demand reduction")
        
        confidence = 0.8  # Price elasticity estimates have moderate confidence
        
        return {
            'scenario_type': 'PRICE_STRATEGY',
            'changes_summary': changes_summary,
            'delta_sell_through_pct': round(delta_st_pct, 2),
            'delta_revenue': round(delta_revenue, 2),
            'delta_inventory_days': round(delta_inventory_days, 1),
            'new_sell_through_rate': round(new_st, 1),
            'new_revenue': round(new_revenue, 2),
            'new_inventory_days': round(new_inventory, 1),
            'confidence_score': round(confidence, 3),
            'risk_factors': risk_factors,
            'price_adjustments': price_adjustments
        }

# ===== AUTOMATED SCENARIO GENERATION =====

def generate_recommended_scenarios(gap_analysis_df: pd.DataFrame, gap_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate recommended scenarios based on gap analysis"""
    log_progress("🎯 Generating recommended optimization scenarios...")
    
    scenarios = []
    
    # Generate gap-filling scenarios for critical gaps
    critical_gaps = []
    for cluster_id, cluster_data in gap_summary['cluster_summary'].items():
        if cluster_data['significant_gaps'] > 0:
            cluster_num = int(cluster_id.replace('Cluster_', ''))
            
            gap_fixes = []
            for gap in cluster_data['gaps_detail']:
                if gap['severity'] == 'CRITICAL' and gap['gap'] > 0:  # Need to add products
                    products_needed = max(1, int(gap['gap'] / 5))  # Conservative: 1 product per 5% gap
                    gap_fixes.append({
                        'role': gap['role'],
                        'gap_percentage': gap['gap'],
                        'products_to_add': products_needed
                    })
            
            if gap_fixes:
                scenarios.append({
                    'type': 'GAP_FILLING',
                    'cluster_id': cluster_num,
                    'gap_fixes': gap_fixes,
                    'priority': 'HIGH' if len(gap_fixes) >= 3 else 'MEDIUM'
                })
    
    # Generate price optimization scenarios
    scenarios.append({
        'type': 'PRICE_STRATEGY',
        'price_adjustments': {'ECONOMY': 0.95, 'LUXURY': 1.05},  # Conservative adjustments
        'priority': 'LOW'
    })
    
    scenarios.append({
        'type': 'PRICE_STRATEGY',
        'price_adjustments': {'VALUE': 0.98, 'PREMIUM': 1.08},
        'priority': 'MEDIUM'
    })
    
    log_progress(f"   ✓ Generated {len(scenarios)} recommended scenarios")
    return scenarios

def run_scenario_analysis(analyzer: WhatIfScenarioAnalyzer, scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run analysis on all scenarios"""
    log_progress("🚀 Running scenario analysis...")
    
    results = []
    
    for scenario in tqdm(scenarios, desc="Analyzing scenarios"):
        try:
            if scenario['type'] == 'GAP_FILLING':
                result = analyzer.analyze_gap_filling_scenario(
                    scenario['cluster_id'], 
                    scenario['gap_fixes']
                )
            elif scenario['type'] == 'PRICE_STRATEGY':
                result = analyzer.analyze_price_strategy_scenario(
                    scenario['price_adjustments']
                )
            else:
                continue  # Skip unsupported scenario types
            
            result['priority'] = scenario['priority']
            result['scenario_id'] = len(results) + 1
            results.append(result)
            
        except Exception as e:
            log_progress(f"   ⚠️ Error analyzing scenario: {e}")
            continue
    
    log_progress(f"   ✓ Completed analysis of {len(results)} scenarios")
    return results

# ===== REPORTING FUNCTIONS =====

def create_scenario_summary(results: List[Dict[str, Any]], baseline: Dict[str, Any]) -> Dict[str, Any]:
    """Create comprehensive scenario analysis summary"""
    
    summary = {
        'analysis_metadata': {
            'total_scenarios_analyzed': len(results),
            'analysis_timestamp': datetime.now().isoformat(),
            'baseline_metrics': baseline
        },
        
        'scenario_performance': {
            'best_sell_through_improvement': None,
            'best_revenue_improvement': None,
            'best_inventory_improvement': None,
            'lowest_risk_option': None
        },
        
        'scenario_results': results,
        
        'recommendations': {
            'immediate_actions': [],
            'medium_term_strategies': [],
            'high_impact_low_risk': []
        }
    }
    
    if results:
        # Find best performing scenarios
        best_st = max(results, key=lambda x: x.get('delta_sell_through_pct', -999))
        best_revenue = max(results, key=lambda x: x.get('delta_revenue', -999999))
        best_inventory = min(results, key=lambda x: x.get('delta_inventory_days', 999))
        lowest_risk = max(results, key=lambda x: x.get('confidence_score', 0))
        
        summary['scenario_performance']['best_sell_through_improvement'] = best_st
        summary['scenario_performance']['best_revenue_improvement'] = best_revenue
        summary['scenario_performance']['best_inventory_improvement'] = best_inventory
        summary['scenario_performance']['lowest_risk_option'] = lowest_risk
        
        # Generate recommendations
        high_impact_scenarios = [r for r in results if r.get('delta_revenue', 0) > 10000]
        low_risk_scenarios = [r for r in results if r.get('confidence_score', 0) > 0.8 and len(r.get('risk_factors', [])) <= 1]
        
        summary['recommendations']['high_impact_low_risk'] = [
            r for r in results 
            if r in high_impact_scenarios and r in low_risk_scenarios
        ]
        
        summary['recommendations']['immediate_actions'] = [
            r for r in results 
            if r.get('priority') == 'HIGH' and r.get('confidence_score', 0) > 0.7
        ]
    
    return summary

def create_detailed_report(summary: Dict[str, Any], output_file: str = SCENARIO_REPORT_FILE) -> None:
    """Create detailed scenario analysis report"""
    
    report_content = f"""# What-If Scenario Analysis Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Scenarios Analyzed:** {summary['analysis_metadata']['total_scenarios_analyzed']}

## Executive Summary

This report provides impact analysis for various product portfolio optimization scenarios,
including product role adjustments, gap-filling strategies, and price optimization.

## Baseline Performance

- **Current Sell-Through Rate:** {summary['analysis_metadata']['baseline_metrics']['avg_sell_through_rate']:.1f}%
- **Total Revenue:** ¥{summary['analysis_metadata']['baseline_metrics']['total_sales_amount']:,.0f}
- **Average Inventory Days:** {summary['analysis_metadata']['baseline_metrics']['avg_inventory_days']:.0f} days
- **Total Products:** {summary['analysis_metadata']['baseline_metrics']['total_products']}

## Best Performance Scenarios

"""
    
    if summary['scenario_performance']['best_sell_through_improvement']:
        best_st = summary['scenario_performance']['best_sell_through_improvement']
        report_content += f"""### Best Sell-Through Improvement
**Scenario #{best_st['scenario_id']} - {best_st['scenario_type']}**
- **Impact:** {best_st['delta_sell_through_pct']:+.1f}% sell-through improvement
- **Revenue Impact:** ¥{best_st['delta_revenue']:+,.0f}
- **Confidence:** {best_st['confidence_score']:.1%}
- **Changes:** {', '.join(best_st['changes_summary'])}

"""
    
    if summary['scenario_performance']['best_revenue_improvement']:
        best_rev = summary['scenario_performance']['best_revenue_improvement']
        report_content += f"""### Best Revenue Improvement
**Scenario #{best_rev['scenario_id']} - {best_rev['scenario_type']}**
- **Revenue Impact:** ¥{best_rev['delta_revenue']:+,.0f}
- **Sell-Through Impact:** {best_rev['delta_sell_through_pct']:+.1f}%
- **Confidence:** {best_rev['confidence_score']:.1%}
- **Changes:** {', '.join(best_rev['changes_summary'])}

"""
    
    # Add recommendations section
    report_content += f"""
## Recommended Actions

### High-Impact, Low-Risk Opportunities
"""
    
    if summary['recommendations']['high_impact_low_risk']:
        for scenario in summary['recommendations']['high_impact_low_risk'][:3]:
            report_content += f"""
**Scenario #{scenario['scenario_id']}**
- **Type:** {scenario['scenario_type']}
- **Impact:** ¥{scenario['delta_revenue']:+,.0f} revenue, {scenario['delta_sell_through_pct']:+.1f}% sell-through
- **Risk Level:** Low (confidence: {scenario['confidence_score']:.1%})
- **Action:** {', '.join(scenario['changes_summary'])}
"""
    else:
        report_content += "\nNo high-impact, low-risk scenarios identified. Consider more conservative approaches.\n"
    
    report_content += f"""
### Immediate Priority Actions
"""
    
    if summary['recommendations']['immediate_actions']:
        for scenario in summary['recommendations']['immediate_actions'][:3]:
            report_content += f"""
**Scenario #{scenario['scenario_id']}**
- **Type:** {scenario['scenario_type']}
- **Urgency:** {scenario['priority']}
- **Impact:** ¥{scenario['delta_revenue']:+,.0f} revenue
- **Action Required:** {', '.join(scenario['changes_summary'])}
"""
    else:
        report_content += "\nNo immediate critical actions identified.\n"
    
    report_content += """
## Risk Assessment

All scenarios include confidence scores and risk factors. Higher confidence scores (>80%) 
indicate more reliable projections. Consider risk factors when implementing changes.

## Methodology

- **Sell-Through Impact:** Based on product role performance multipliers
- **Revenue Impact:** Combines volume and price effects
- **Inventory Impact:** Reflects turnover rate changes
- **Confidence Scoring:** Based on change magnitude and historical patterns

---
*Generated by What-If Scenario Analyzer v1.0*
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    log_progress(f"   ✓ Saved detailed report: {output_file}")

def main() -> None:
    """Main function for what-if scenario analysis (period-aware with manifest integration)"""
    start_time = datetime.now()
    log_progress("🚀 Starting What-If Scenario Analysis (Step 28)... (period-aware)")
    
    try:
        # Step 1: Parse arguments
        args = parse_args()
        log_progress("   ✓ Parsed command line arguments")
        
        # Step 2: Resolve configuration (period-aware)
        resolved = resolve_configuration(args)
        log_progress("   ✓ Resolved configuration settings")
        
        # Step 3: Load baseline data using resolved paths
        sales_df, product_roles_df, price_bands_df, gap_analysis_df, gap_summary = load_baseline_data(resolved)
        log_progress("   ✓ Loaded all baseline data")
        
        # Step 4: Calculate baseline metrics
        baseline_metrics = calculate_baseline_metrics(sales_df, product_roles_df, price_bands_df)
        log_progress("   ✓ Calculated baseline performance metrics")
        
        # Step 5: Initialize scenario analyzer
        analyzer = WhatIfScenarioAnalyzer({
            'sales_data': sales_df,
            'product_roles': product_roles_df,
            'price_bands': price_bands_df,
            'gap_analysis': gap_analysis_df,
            'baseline_metrics': baseline_metrics
        })
        log_progress("   ✓ Initialized scenario analyzer")
        
        # Step 6: Generate scenarios (CLI-driven or recommended)
        if resolved['selected_scenario'] == 'AUTO':
            scenarios = generate_recommended_scenarios(gap_analysis_df, gap_summary)
        elif resolved['selected_scenario'] == 'ROLE_OPTIMIZATION':
            role_changes: Dict[str, Dict[str, int]] = {}
            for role, cnt in (resolved['role_add'] or {}).items():
                role_changes.setdefault(role, {'add': 0, 'remove': 0})
                role_changes[role]['add'] += cnt
            for role, cnt in (resolved['role_remove'] or {}).items():
                role_changes.setdefault(role, {'add': 0, 'remove': 0})
                role_changes[role]['remove'] += cnt
            if not resolved['cluster_id'] or not role_changes:
                log_progress("   ⚠️  ROLE_OPTIMIZATION requires --cluster-id and --add/--remove; falling back to AUTO")
                scenarios = generate_recommended_scenarios(gap_analysis_df, gap_summary)
            else:
                scenarios = [{
                    'type': 'GAP_FILLING' if any(v.get('add',0)>0 for v in role_changes.values()) else 'ROLE_OPTIMIZATION',
                    'cluster_id': int(resolved['cluster_id']),
                    'gap_fixes': [{'role': r, 'gap_percentage': 0, 'products_to_add': v.get('add',0)} for r, v in role_changes.items()],
                    'role_changes': role_changes,
                    'priority': 'MEDIUM'
                }]
        elif resolved['selected_scenario'] == 'GAP_FILLING':
            if not resolved['cluster_id'] or not resolved['role_add']:
                log_progress("   ⚠️  GAP_FILLING requires --cluster-id and --add ROLE:COUNT; falling back to AUTO")
                scenarios = generate_recommended_scenarios(gap_analysis_df, gap_summary)
            else:
                gap_fixes = [{'role': r, 'gap_percentage': 0, 'products_to_add': c} for r, c in resolved['role_add'].items()]
                scenarios = [{
                    'type': 'GAP_FILLING',
                    'cluster_id': int(resolved['cluster_id']),
                    'gap_fixes': gap_fixes,
                    'priority': 'MEDIUM'
                }]
        elif resolved['selected_scenario'] == 'PRICE_STRATEGY':
            if not resolved['price_adjustments']:
                log_progress("   ⚠️  PRICE_STRATEGY requires --adjust BAND:MULTIPLIER; falling back to AUTO")
                scenarios = generate_recommended_scenarios(gap_analysis_df, gap_summary)
            else:
                scenarios = [{
                    'type': 'PRICE_STRATEGY',
                    'price_adjustments': resolved['price_adjustments'],
                    'priority': 'MEDIUM'
                }]
        else:
            scenarios = generate_recommended_scenarios(gap_analysis_df, gap_summary)
        
        # Step 7: Run scenario analysis
        scenario_results = run_scenario_analysis(analyzer, scenarios)
        
        # Step 8: Create summary and reports
        summary = create_scenario_summary(scenario_results, baseline_metrics)
        
        # Convert numpy types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            return obj
        
        summary_clean = convert_numpy_types(summary)
        
        # Save results using DUAL OUTPUT PATTERN
        # Save timestamped version (for backup/inspection)
        with open(resolved['results_file'], 'w') as f:
            json.dump(summary_clean, f, indent=2)
        log_progress(f"✅ Saved timestamped scenario results: {resolved['results_file']}")
        
        # Save generic version (for pipeline flow)
        with open(resolved['generic_results_file'], 'w') as f:
            json.dump(summary_clean, f, indent=2)
        log_progress(f"✅ Saved generic scenario results: {resolved['generic_results_file']}")
        
        # Create detailed report (DUAL OUTPUT PATTERN)
        # Save timestamped version (for backup/inspection)
        create_detailed_report(summary, resolved['report_file'])
        log_progress(f"✅ Saved timestamped detailed report: {resolved['report_file']}")
        
        # Save generic version (for pipeline flow)
        create_detailed_report(summary, resolved['generic_report_file'])
        log_progress(f"✅ Saved generic detailed report: {resolved['generic_report_file']}")
        
        # Create recommendations CSV (DUAL OUTPUT PATTERN)
        if scenario_results:
            recommendations_data = []
            for result in scenario_results:
                recommendations_data.append({
                    'scenario_id': result['scenario_id'],
                    'scenario_type': result['scenario_type'],
                    'priority': result['priority'],
                    'delta_sell_through_pct': result['delta_sell_through_pct'],
                    'delta_revenue': result['delta_revenue'],
                    'delta_inventory_days': result['delta_inventory_days'],
                    'confidence_score': result['confidence_score'],
                    'risk_level': 'Low' if len(result['risk_factors']) == 0 else 'Medium' if len(result['risk_factors']) <= 2 else 'High',
                    'changes_summary': '; '.join(result['changes_summary'])
                })
            
            recommendations_df = pd.DataFrame(recommendations_data)
            
            # Save timestamped version (for backup/inspection)
            recommendations_df.to_csv(resolved['recommendations_file'], index=False)
            log_progress(f"✅ Saved timestamped recommendations: {resolved['recommendations_file']}")
            
            # Create symlink for generic version (for pipeline flow)
            if os.path.exists(resolved['generic_recommendations_file']) or os.path.islink(resolved['generic_recommendations_file']):
                os.remove(resolved['generic_recommendations_file'])
            os.symlink(os.path.basename(resolved['recommendations_file']), resolved['generic_recommendations_file'])
            log_progress(f"✅ Created symlink: {resolved['generic_recommendations_file']} -> {resolved['recommendations_file']}")
        
        # Register outputs in manifest (period-aware)
        try:
            # Extract period information for manifest registration
            target_yyyymm = args.target_yyyymm or os.environ.get('PIPELINE_YYYYMM')
            target_period = args.target_period or os.environ.get('PIPELINE_PERIOD')
            period_label = args.period_label or os.environ.get('SC28_PERIOD_LABEL')
            
            if target_yyyymm and target_period:
                period_label = f"{target_yyyymm}{target_period}"
            elif not period_label:
                period_label = datetime.now().strftime('%Y%m')
            
            # Register generic outputs
            register_step_output('step28', 'scenario_results', resolved['results_file'], {
                'file_type': 'json',
                'description': 'What-if scenario analysis results',
                'records': len(scenario_results),
                'target_year': int(target_yyyymm[:4]) if target_yyyymm else datetime.now().year,
                'target_month': int(target_yyyymm[4:]) if target_yyyymm and len(target_yyyymm) >= 6 else datetime.now().month,
                'target_period': target_period or 'default'
            })
            
            register_step_output('step28', 'scenario_report', resolved['report_file'], {
                'file_type': 'markdown',
                'description': 'Detailed scenario analysis report',
                'target_year': int(target_yyyymm[:4]) if target_yyyymm else datetime.now().year,
                'target_month': int(target_yyyymm[4:]) if target_yyyymm and len(target_yyyymm) >= 6 else datetime.now().month,
                'target_period': target_period or 'default'
            })
            
            if scenario_results:
                register_step_output('step28', 'scenario_recommendations', resolved['recommendations_file'], {
                    'file_type': 'csv',
                    'description': 'Scenario recommendations summary',
                    'records': len(recommendations_data),
                    'columns': len(recommendations_data[0]) if recommendations_data else 0,
                    'target_year': int(target_yyyymm[:4]) if target_yyyymm else datetime.now().year,
                    'target_month': int(target_yyyymm[4:]) if target_yyyymm and len(target_yyyymm) >= 6 else datetime.now().month,
                    'target_period': target_period or 'default'
                })
            
            # Register period-specific outputs if period is specified
            if period_label:
                register_step_output('step28', f'scenario_results_{period_label}', resolved['results_file'], {
                    'file_type': 'json',
                    'description': f'What-if scenario analysis results for {period_label}',
                    'records': len(scenario_results),
                    'target_year': int(target_yyyymm[:4]) if target_yyyymm else datetime.now().year,
                    'target_month': int(target_yyyymm[4:]) if target_yyyymm and len(target_yyyymm) >= 6 else datetime.now().month,
                    'target_period': target_period or 'default',
                    'period_label': period_label
                })
                
                register_step_output('step28', f'scenario_report_{period_label}', resolved['report_file'], {
                    'file_type': 'markdown',
                    'description': f'Detailed scenario analysis report for {period_label}',
                    'target_year': int(target_yyyymm[:4]) if target_yyyymm else datetime.now().year,
                    'target_month': int(target_yyyymm[4:]) if target_yyyymm and len(target_yyyymm) >= 6 else datetime.now().month,
                    'target_period': target_period or 'default',
                    'period_label': period_label
                })
                
                if scenario_results:
                    register_step_output('step28', f'scenario_recommendations_{period_label}', resolved['recommendations_file'], {
                        'file_type': 'csv',
                        'description': f'Scenario recommendations summary for {period_label}',
                        'records': len(recommendations_data),
                        'columns': len(recommendations_data[0]) if recommendations_data else 0,
                        'target_year': int(target_yyyymm[:4]) if target_yyyymm else datetime.now().year,
                        'target_month': int(target_yyyymm[4:]) if target_yyyymm and len(target_yyyymm) >= 6 else datetime.now().month,
                        'target_period': target_period or 'default',
                        'period_label': period_label
                    })
            
            log_progress("   ✓ Registered outputs in pipeline manifest")
            
        except Exception as e:
            log_progress(f"   ⚠️  Failed to register outputs in manifest: {e}")
        
        # Print final results
        execution_time = (datetime.now() - start_time).total_seconds()
        log_progress(f"\n🎯 WHAT-IF SCENARIO ANALYSIS RESULTS:")
        log_progress(f"   📊 Scenarios Analyzed: {len(scenario_results)}")
        
        if scenario_results:
            best_revenue = max(scenario_results, key=lambda x: x.get('delta_revenue', -999999))
            best_st = max(scenario_results, key=lambda x: x.get('delta_sell_through_pct', -999))
            
            log_progress(f"   💰 Best Revenue Impact: ¥{best_revenue['delta_revenue']:+,.0f}")
            log_progress(f"   📈 Best Sell-Through Impact: {best_st['delta_sell_through_pct']:+.1f}%")
            log_progress(f"   🎯 High-Impact Low-Risk Scenarios: {len(summary['recommendations']['high_impact_low_risk'])}")
        
        log_progress(f"   ⚡ Execution Time: {execution_time:.1f} seconds")
        log_progress(f"\n📁 Generated Files:")
        log_progress(f"   • {resolved['results_file']}")
        log_progress(f"   • {resolved['report_file']}")
        if scenario_results:
            log_progress(f"   • {resolved['recommendations_file']}")
        
        log_progress(f"\n✅ What-If Scenario Analysis completed successfully")
        
        # Final module completion message
        log_progress(f"\n🎉 PRODUCT STRUCTURE OPTIMIZATION MODULE COMPLETED!")
        log_progress(f"   ✅ Step 25: Product Role Classification")
        log_progress(f"   ✅ Step 26: Price-Band + Elasticity Analysis")
        log_progress(f"   ✅ Step 27: Gap Matrix Generation")
        log_progress(f"   ✅ Step 28: What-If Scenario Analysis")
        
    except Exception as e:
        log_progress(f"❌ Error in scenario analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main() 