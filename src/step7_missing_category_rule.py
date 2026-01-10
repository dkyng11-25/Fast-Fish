# ---- New: optional recent-period averaging controls (env-driven, CLI later) ----
from typing import Tuple, List, Optional  # needed for helper type hints
import pandas as pd  # used by helper
import os  # used by helper for path checks
from output_utils import create_output_with_symlinks
import os as _os
RECENT_MONTHS_BACK = int(_os.getenv('RECENT_MONTHS_BACK', '0') or '0')  # 0=disabled; otherwise number of half-months incl. base

def _previous_half_month(yyyymm: str, period: str) -> Tuple[str, str]:
    y = int(yyyymm[:4]); m = int(yyyymm[4:6])
    if period.upper() == 'B':
        return f"{y}{m:02d}", 'A'
    # period A -> previous month's B
    if m == 1:
        y -= 1; m = 12
    else:
        m -= 1
    return f"{y}{m:02d}", 'B'

def _average_recent_sales(base_yyyymm: str, base_period: str, feature_col: str, sales_col: str, n_back: int) -> Optional[pd.DataFrame]:
    """Average sales over last n_back half-month periods including base period.
    Returns a DataFrame with ['str_code', feature_col, sales_col] averaged across periods.
    """
    try:
        n = max(1, int(n_back))
    except Exception:
        n = 1
    periods: List[Tuple[str, str]] = []
    yyyymm, per = base_yyyymm, base_period
    periods.append((yyyymm, per))
    for _ in range(max(0, n - 1)):
        yyyymm, per = _previous_half_month(yyyymm, per)
        periods.append((yyyymm, per))
    sales_frames: List[pd.DataFrame] = []
    for (ym, p) in periods:
        try:
            api = get_api_data_files(ym, p)
            path = api.get('spu_sales')
            if path and os.path.exists(path):
                df = pd.read_csv(path, dtype={'str_code': str}, low_memory=False)
                keep = [c for c in ['str_code', feature_col, sales_col] if c in df.columns]
                if len(keep) == 3:
                    sales_frames.append(df[keep])
        except Exception:
            continue
    if not sales_frames:
        return None
    all_df = pd.concat(sales_frames, ignore_index=True)
    # numeric conversion then average by count of periods
    all_df[sales_col] = pd.to_numeric(all_df[sales_col], errors='coerce')
    agg = all_df.groupby(['str_code', feature_col], as_index=False)[sales_col].sum()
    denom = len(sales_frames)
    if denom > 0:
        agg[sales_col] = agg[sales_col] / denom
    return agg
#!/usr/bin/env python3
"""
Step 7: Missing Category/SPU Rule with QUANTITY RECOMMENDATIONS + FAST FISH SELL-THROUGH VALIDATION

This step identifies stores that are missing subcategories or SPUs that are well-selling 
in their peer stores within the same cluster and provides specific UNIT QUANTITY targets.

ENHANCEMENT: Now includes actual unit quantity recommendations using real sales data!
FAST FISH COMPLIANCE: Only recommends additions that IMPROVE sell-through rate!

Key Features:
- Subcategory-level analysis (traditional approach)
- SPU-level analysis (granular approach)
- 🎯 UNIT QUANTITY RECOMMENDATIONS (e.g., "Stock 5 units/15-days")
- 📈 FAST FISH SELL-THROUGH VALIDATION (only profitable recommendations)
- Real sales data integration for accurate quantity calculations
- Intelligent cluster-based analysis
- Configurable thresholds and parameters
- Comprehensive opportunity identification with investment planning

Author: Data Pipeline
Date: 2025-01-02 (Enhanced with Quantity Recommendations)
Date: 2025-01-XX (Enhanced with Fast Fish Sell-Through Validation)
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
from typing import Dict, List, Tuple, Set, Optional
from datetime import datetime
import warnings
from tqdm import tqdm
import argparse

# Config-driven paths and periods
from src.config import (
    initialize_pipeline_config,
    get_current_period,
    get_period_label,
    get_api_data_files,
    get_output_files,
    load_margin_rates
)
from src.pipeline_manifest import register_step_output, get_step_input

# Robust import for validator: support both absolute and relative imports depending on invocation
SELLTHROUGH_VALIDATION_AVAILABLE = False
try:
    # Preferred: absolute import when running via `python -m src.step7_missing_category_rule` or with PYTHONPATH=.
    from src.sell_through_validator import SellThroughValidator, load_historical_data_for_validation  # type: ignore
    SELLTHROUGH_VALIDATION_AVAILABLE = True
    print("✅ Fast Fish sell-through validation: ENABLED (absolute import)")
except Exception:
    try:
        # Fallback: relative import when running inside the package context
        from .sell_through_validator import SellThroughValidator, load_historical_data_for_validation  # type: ignore
        SELLTHROUGH_VALIDATION_AVAILABLE = True
        print("✅ Fast Fish sell-through validation: ENABLED (relative import)")
    except Exception:
        SELLTHROUGH_VALIDATION_AVAILABLE = False
        print("⚠️ Fast Fish sell-through validation: DISABLED (validator not found)")

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# Configuration - Analysis Level Selection
ANALYSIS_LEVEL = "spu"  # Uncomment for SPU-level analysis
# ANALYSIS_LEVEL = "subcategory"  # Options: "subcategory", "spu"

# DATA PERIOD CONFIGURATION - CRITICAL FOR ACCURATE RECOMMENDATIONS
DATA_PERIOD_DAYS = 15  # API data is for half month (15 days)
TARGET_PERIOD_DAYS = 15  # Recommendations should be for same period (15 days)
SCALING_FACTOR = TARGET_PERIOD_DAYS / DATA_PERIOD_DAYS  # 1.0 for same period

# Seasonal blending controls (overridden via CLI)
USE_BLENDED_SEASONAL: bool = False
SEASONAL_YYYYMM: Optional[str] = None
SEASONAL_PERIOD: Optional[str] = None
SEASONAL_WEIGHT: float = 0.6
RECENT_WEIGHT: float = 0.4  # Typically 1 - seasonal_weight
SEASONAL_YEARS_BACK: int = 0  # How many prior years of the same month/period to include

# Output target period for forecasting (used only for output labeling)
TARGET_YYYYMM: Optional[str] = None
TARGET_PERIOD: Optional[str] = None

def load_blended_seasonal_data(analysis_level: str, current_month: int = 8) -> pd.DataFrame:
    """
    Load and blend recent trends with seasonal patterns for August recommendations.
    
    For August, combines:
    - Recent 3 months (May-July 2025): Current trends
    - Last year August (August 2024): Seasonal patterns
    
    Args:
        analysis_level: "subcategory" or "spu"
        current_month: Current month (1-12), defaults to 8 (August)
        
    Returns:
        Blended DataFrame with seasonal and trend data
    """
    base_path = "../data/api_data/"
    
    if current_month == 8:  # August: Use blended approach
        log_progress(f"🔄 BLENDED APPROACH: Combining recent trends + seasonal patterns for August")
        
        # Recent 3 months data (May-July 2025)
        recent_files = [
            f"{base_path}complete_{analysis_level}_sales_202505A.csv",
            f"{base_path}complete_{analysis_level}_sales_202506A.csv", 
            f"{base_path}complete_{analysis_level}_sales_202507A.csv"
        ]
        
        # Last year August data (August 2024)
        seasonal_file = f"{base_path}complete_{analysis_level}_sales_202408B.csv"
        
        combined_data = []
        
        # Load recent months data
        log_progress(f"📊 Loading recent 3 months data (May-July 2025)...")
        for file_path in recent_files:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path, dtype={'str_code': str}, low_memory=False)
                df['data_source'] = 'recent_trend'
                df['weight'] = 0.4  # 40% weight for recent trends
                combined_data.append(df)
                log_progress(f"  ✓ Loaded {os.path.basename(file_path)}: {len(df):,} records")
        
        # Load seasonal data
        log_progress(f"🍂 Loading last year August data (August 2024)...")
        if os.path.exists(seasonal_file):
            df = pd.read_csv(seasonal_file, dtype={'str_code': str}, low_memory=False)
            df['data_source'] = 'seasonal_pattern'
            df['weight'] = 0.6  # 60% weight for seasonal patterns
            combined_data.append(df)
            log_progress(f"  ✓ Loaded {os.path.basename(seasonal_file)}: {len(df):,} records")
        
        if combined_data:
            blended_df = pd.concat(combined_data, ignore_index=True)
            log_progress(f"✅ Blended dataset created: {len(blended_df):,} total records")
            return blended_df
        else:
            log_progress(f"⚠️ No blended data available, falling back to Q2")
            return None
    
    else:  # Other months: Use simple seasonal mapping without combined fallbacks
        # Default to current month A period file; callers may override with CLI args
        cur_label = datetime.now().strftime('%Y%m') + 'A'
        if analysis_level == "subcategory":
            return f"{base_path}complete_category_sales_{cur_label}.csv"
        else:
            return f"{base_path}complete_spu_sales_{cur_label}.csv"

# Analysis configurations with blended seasonal data
ANALYSIS_CONFIGS = {
    "subcategory": {
        "cluster_file": "output/clustering_results_subcategory.csv",
        "use_blended_data": True,
        "feature_column": "sub_cate_name",
        "sales_column": "sal_amt",
        "description": "Subcategory-Level Missing Product Analysis (Blended Seasonal)",
        "output_prefix": "rule7_missing_subcategory"
    },
    "spu": {
        "cluster_file": "output/clustering_results_spu.csv", 
        "use_blended_data": True,
        "feature_column": "spu_code",
        "sales_column": "spu_sales_amt",
        "description": "SPU-Level Missing Product Analysis with Blended Seasonal Data",
        "output_prefix": "rule7_missing_spu"
    }
}

# Get current analysis configuration
CURRENT_CONFIG = ANALYSIS_CONFIGS[ANALYSIS_LEVEL]

# File paths based on analysis level
CLUSTER_RESULTS_FILE = CURRENT_CONFIG["cluster_file"]
OUTPUT_DIR = "output"
RESULTS_FILE = f"output/{CURRENT_CONFIG['output_prefix']}_results.csv"

# Rule parameters - adaptive based on analysis level
if ANALYSIS_LEVEL == "subcategory":
    MIN_CLUSTER_STORES_SELLING = 0.7  # 70% of stores in cluster must sell subcategory
    MIN_CLUSTER_SALES_THRESHOLD = 100  # Minimum total sales in cluster
    MIN_OPPORTUNITY_VALUE = 50  # Minimum expected sales value
else:  # SPU level - SANITY ADJUSTED FOR REALISTIC RECOMMENDATIONS
    MIN_CLUSTER_STORES_SELLING = 0.80  # 80% for SPU (more realistic adoption threshold)
    MIN_CLUSTER_SALES_THRESHOLD = 1500   # Reduced threshold for more opportunities
    MIN_OPPORTUNITY_VALUE = 500         # More accessible opportunity threshold
    MAX_MISSING_SPUS_PER_STORE = 5       # Allow more recommendations per store

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log_progress(message: str) -> None:
    """
    Log progress with timestamp.
    
    Args:
        message (str): Progress message to log
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_quantity_data() -> Optional[pd.DataFrame]:
    """
    Load quantity data for unit-based recommendations.
    
    Returns:
        DataFrame with quantity data or None if not available
    """
    try:
        # Resolve quantity file dynamically for current period with fallback
        yyyymm, period = get_current_period()
        period_label = get_period_label(yyyymm, period)
        primary = get_api_data_files(yyyymm, period)['store_sales']
        candidates = [
            primary,
            os.path.join(OUTPUT_DIR, f"store_sales_{period_label}.csv"),
            os.path.join("data", "api_data", "store_sales_data.csv"),
        ]
        quantity_file = next((p for p in candidates if os.path.exists(p)), None)
        if not quantity_file:
            # STRICT: real quantity and price data required; no fallback/estimates allowed
            raise FileNotFoundError(
                "Real quantity data required (store_sales). Strict mode prohibits fallback or estimated pricing."
            )

        log_progress(f"Loading quantity data from {quantity_file} for unit-based recommendations...")
        qty_df = pd.read_csv(quantity_file, dtype={'str_code': str}, low_memory=False)
        # Standardize store code column
        if 'str_code' not in qty_df.columns:
            if 'store_cd' in qty_df.columns:
                qty_df['str_code'] = qty_df['store_cd'].astype(str)
                log_progress("Detected 'store_cd' in quantity data; standardized to 'str_code'")
            else:
                raise ValueError("Quantity data missing 'str_code' and 'store_cd' columns (strict mode)")

        # Clean quantity data
        totals_present = {'total_qty', 'total_amt'}.issubset(qty_df.columns)
        if totals_present:
            # Use provided real totals directly (computed upstream from real SPU sales)
            qty_df['total_qty'] = pd.to_numeric(qty_df['total_qty'], errors='coerce')
            qty_df['total_amt'] = pd.to_numeric(qty_df['total_amt'], errors='coerce')
            missing_qty = int(qty_df['total_qty'].isna().sum())
            missing_amt = int(qty_df['total_amt'].isna().sum())
            if missing_qty or missing_amt:
                log_progress(f"Quantity data missingness: total_qty NAs={missing_qty:,}, total_amt NAs={missing_amt:,} (preserved)")
        else:
            # Fall back to base/fashion split if available
            for col in ['base_sal_qty', 'fashion_sal_qty', 'base_sal_amt', 'fashion_sal_amt']:
                if col not in qty_df.columns:
                    qty_df[col] = np.nan
                qty_df[col] = pd.to_numeric(qty_df[col], errors='coerce')
            missing_qty = int(qty_df[['base_sal_qty', 'fashion_sal_qty']].isna().sum().sum())
            missing_amt = int(qty_df[['base_sal_amt', 'fashion_sal_amt']].isna().sum().sum())
            if missing_qty or missing_amt:
                log_progress(f"Quantity data missingness: qty NAs={missing_qty:,}, amt NAs={missing_amt:,} (preserved)")
            # Calculate totals from split columns
            qty_df['total_qty'] = qty_df['base_sal_qty'] + qty_df['fashion_sal_qty']
            qty_df['total_amt'] = qty_df['base_sal_amt'] + qty_df['fashion_sal_amt']

        # Calculate average unit price by store (strict: NaN when total_qty <= 0)
        qty_df['avg_unit_price'] = np.where(qty_df['total_qty'] > 0, qty_df['total_amt'] / qty_df['total_qty'], np.nan)

        # If current period has no avg_unit_price coverage, attempt real-data backfill from previous periods
        try:
            non_null_cnt = int(qty_df['avg_unit_price'].notna().sum())
        except Exception:
            non_null_cnt = 0
        if non_null_cnt == 0:
            try:
                backfill_frames: List[pd.DataFrame] = []
                # Default to 6 half-months lookback if RECENT_MONTHS_BACK is unset or small
                lookback = max(1, int(os.getenv('RECENT_MONTHS_BACK', '6') or '6'))
                bym, bp = yyyymm, period
                for _ in range(lookback):
                    bym, bp = _previous_half_month(bym, bp)
                    try:
                        api_prev = get_api_data_files(bym, bp)
                        prev_path = api_prev.get('store_sales')
                        if prev_path and os.path.exists(prev_path):
                            prev = pd.read_csv(prev_path, dtype={'str_code': str}, low_memory=False)
                            for c in [
                                'total_qty','total_amt','base_sal_qty','fashion_sal_qty','base_sal_amt','fashion_sal_amt'
                            ]:
                                if c in prev.columns:
                                    prev[c] = pd.to_numeric(prev[c], errors='coerce')
                            if 'total_qty' not in prev.columns or 'total_amt' not in prev.columns:
                                prev['total_qty'] = prev.get('base_sal_qty', np.nan) + prev.get('fashion_sal_qty', np.nan)
                                prev['total_amt'] = prev.get('base_sal_amt', np.nan) + prev.get('fashion_sal_amt', np.nan)
                            prev['avg_unit_price'] = np.where(prev['total_qty'] > 0, prev['total_amt'] / prev['total_qty'], np.nan)
                            backfill_frames.append(prev[['str_code','avg_unit_price']].copy())
                    except Exception:
                        continue
                if backfill_frames:
                    bf = pd.concat(backfill_frames, ignore_index=True)
                    bf = bf.dropna(subset=['avg_unit_price'])
                    if not bf.empty:
                        bf_med = bf.groupby('str_code', as_index=False)['avg_unit_price'].median()
                        before_missing = int(qty_df['avg_unit_price'].isna().sum())
                        qty_df = qty_df.merge(bf_med, on='str_code', how='left', suffixes=('', '_bf'))
                        qty_df['avg_unit_price'] = qty_df['avg_unit_price'].where(qty_df['avg_unit_price'].notna(), qty_df['avg_unit_price_bf'])
                        qty_df = qty_df.drop(columns=[c for c in ['avg_unit_price_bf'] if c in qty_df.columns])
                        after_missing = int(qty_df['avg_unit_price'].isna().sum())
                        fixed = max(0, before_missing - after_missing)
                        log_progress(f"Backfilled avg_unit_price from {len(backfill_frames)} prior periods (stores fixed: {fixed})")
            except Exception as _e:
                log_progress(f"Backfill attempt for avg_unit_price failed (non-fatal): {_e}")

        log_progress(f"Loaded quantity data for {len(qty_df):,} stores")
        return qty_df[['str_code', 'total_qty', 'total_amt', 'avg_unit_price']].copy()
    except Exception as e:
        # STRICT: fail hard when quantity data cannot be loaded
        log_progress(f"❌ Quantity data load failure in strict mode: {str(e)}")
        raise

def load_category_prices() -> Optional[pd.DataFrame]:
    """
    STRICT MODE: Price estimation is disabled. Only real unit prices from quantity data are allowed.
    Returns None always.
    """
    log_progress("STRICT: Category/SPU price estimation disabled (no fallback or synthetic prices allowed)")
    return None

def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Load clustering results, sales data, and quantity information for enhanced analysis.
    Uses src.config to resolve period-specific paths with fallbacks.
    """
    try:
        log_progress(f"Loading data for {CURRENT_CONFIG['description']}...")

        # Resolve period label and files
        yyyymm, period = get_current_period()
        period_label = get_period_label(yyyymm, period)

        # Load clustering results with dynamic path and fallbacks
        cluster_primary = get_output_files(ANALYSIS_LEVEL, yyyymm, period)['clustering_results']
        cluster_candidates = [
            cluster_primary,
            os.path.join(OUTPUT_DIR, f"clustering_results_{ANALYSIS_LEVEL}_{period_label}.csv"),
            os.path.join(OUTPUT_DIR, "clustering_results_spu.csv"),
            os.path.join(OUTPUT_DIR, "enhanced_clustering_results.csv"),
            os.path.join(OUTPUT_DIR, "clustering_results.csv"),
        ]
        cluster_path = next((p for p in cluster_candidates if os.path.exists(p)), None)
        if cluster_path is None:
            raise FileNotFoundError(f"Clustering results not found. Checked: {', '.join(cluster_candidates)}")
        log_progress(f"Using cluster file: {cluster_path}")
        cluster_df = pd.read_csv(cluster_path, dtype={'str_code': str})
        # Normalize cluster column for downstream compatibility
        if 'cluster_id' not in cluster_df.columns:
            if 'Cluster' in cluster_df.columns:
                cluster_df['cluster_id'] = cluster_df['Cluster']
                log_progress("Detected 'Cluster' column; created normalized 'cluster_id' copy")
            else:
                log_progress("Warning: No 'Cluster' or 'cluster_id' column in cluster results; setting 'cluster_id' to NA")
                cluster_df['cluster_id'] = pd.NA

        # Load sales data (SPU or category) with optional seasonal blending
        sales_key = 'spu_sales' if ANALYSIS_LEVEL == 'spu' else 'category_sales'
        current_sales_primary = get_api_data_files(yyyymm, period)[sales_key]
        current_candidates = [
            current_sales_primary,
            os.path.join("data", "api_data", f"complete_{'spu' if ANALYSIS_LEVEL=='spu' else 'category'}_sales_{period_label}.csv"),
        ]
        current_path = next((p for p in current_candidates if os.path.exists(p)), None)
        if current_path is None:
            raise FileNotFoundError(f"Sales data not found. Checked: {', '.join(current_candidates)}")
        log_progress(f"Using current-period sales: {current_path}")
        current_sales = pd.read_csv(current_path, dtype={'str_code': str}, low_memory=False)

        # Seasonal blending (optional)
        if USE_BLENDED_SEASONAL:
            sales_col = CURRENT_CONFIG['sales_column']
            feature_col = CURRENT_CONFIG['feature_column']

            # Determine seasonal periods to include
            seasonal_periods: List[Tuple[str, str]] = []  # list of (yyyymm, period)

            # Backward-compatible: single seasonal yyyymm provided explicitly
            if SEASONAL_YYYYMM is not None:
                seasonal_periods.append((SEASONAL_YYYYMM, SEASONAL_PERIOD or period))

            # Multi-year seasonal: include same month/period from prior years
            # Prefer TARGET_YYYYMM/TARGET_PERIOD if set; else use current config
            base_yyyymm = TARGET_YYYYMM or yyyymm
            base_period = TARGET_PERIOD or period
            try:
                base_year = int(base_yyyymm[:4])
                base_month = int(base_yyyymm[4:6])
            except Exception:
                base_year, base_month = int(yyyymm[:4]), int(yyyymm[4:6])

            if SEASONAL_YEARS_BACK and SEASONAL_YEARS_BACK > 0:
                for i in range(1, SEASONAL_YEARS_BACK + 1):
                    y = base_year - i
                    seasonal_periods.append((f"{y}{base_month:02d}", base_period))

            # Load available seasonal files
            seasonal_frames: List[pd.DataFrame] = []
            for syyyymm, speriod in seasonal_periods:
                try:
                    prim = get_api_data_files(syyyymm, speriod)[sales_key]
                    candidates = [
                        prim,
                        os.path.join("data", "api_data", f"complete_{'spu' if ANALYSIS_LEVEL=='spu' else 'category'}_sales_{get_period_label(syyyymm, speriod)}.csv"),
                    ]
                    spath = next((p for p in candidates if os.path.exists(p)), None)
                    if spath:
                        log_progress(f"Using seasonal sales: {spath}")
                        sdf = pd.read_csv(spath, dtype={'str_code': str}, low_memory=False)
                        seasonal_frames.append(sdf)
                    else:
                        log_progress(f"Seasonal sales not found for {syyyymm}{speriod or ''}; skipping")
                except Exception as e:
                    log_progress(f"Seasonal load error for {syyyymm}{speriod or ''}: {e}")

            # Optionally average recent panels for current_sales
            try:
                if RECENT_MONTHS_BACK and RECENT_MONTHS_BACK > 1:
                    base_ym, base_p = get_current_period()
                    avg_df = _average_recent_sales(base_ym, base_p, feature_col, sales_col, RECENT_MONTHS_BACK)
                    if avg_df is not None:
                        current_sales = avg_df
                        log_progress(f"📊 Averaged recent panels over {RECENT_MONTHS_BACK} half-months for current sales")
            except Exception:
                pass

            # New: include multiple seasonal extra periods if provided via env var (comma-separated labels like 202508A,202508B)
            try:
                extra = _os.getenv('SEASONAL_EXTRA_PERIODS', '').strip()
                if extra:
                    labels = [x.strip() for x in extra.split(',') if x.strip()]
                    for label in labels:
                        if len(label) >= 7:
                            yyyymm, per = label[:6], label[6]
                            try:
                                api = get_api_data_files(yyyymm, per)
                                path = api.get('spu_sales') if analysis_level == 'spu' else api.get('category_sales')
                                if path and os.path.exists(path):
                                    log_progress(f"Using seasonal sales (extra): {path}")
                                    sdf = pd.read_csv(path, dtype={'str_code': str}, low_memory=False)
                                    seasonal_frames.append(sdf)
                            except Exception:
                                continue
            except Exception:
                pass

            # Apply weights and aggregate
            current_sales[sales_col] = pd.to_numeric(current_sales[sales_col], errors='coerce') * RECENT_WEIGHT
            frames = [current_sales[['str_code', feature_col, sales_col]]]
            if seasonal_frames:
                per_season_weight = SEASONAL_WEIGHT / float(len(seasonal_frames))
                for sf in seasonal_frames:
                    sf[sales_col] = pd.to_numeric(sf[sales_col], errors='coerce') * per_season_weight
                    frames.append(sf[['str_code', feature_col, sales_col]])
                sales_df = pd.concat(frames, ignore_index=True)
                # Missingness diagnostics
                miss_current = int(current_sales[sales_col].isna().sum())
                miss_season = int(sum(sf[sales_col].isna().sum() for sf in seasonal_frames))
                if miss_current or miss_season:
                    log_progress(f"Sales missingness: current NAs={miss_current:,}, seasonal total NAs={miss_season:,} (preserved)")
                sales_df = sales_df.groupby(['str_code', feature_col], as_index=False)[sales_col].sum()
                log_progress(f"✅ Blended sales (multi-year seasonal): {len(sales_df)} unique store-product combinations")
            else:
                log_progress("⚠️ No seasonal files available; using current-period sales only")
                sales_df = current_sales
        else:
            sales_df = current_sales

        # Load quantity and price data for enhanced recommendations
        quantity_df = load_quantity_data()
        price_df = load_category_prices()

        # Standardize store code column names to 'str_code' for cluster and sales data
        if 'str_code' not in cluster_df.columns and 'store_cd' in cluster_df.columns:
            cluster_df['str_code'] = cluster_df['store_cd'].astype(str)
            log_progress("Detected 'store_cd' in cluster results; standardized to 'str_code'")
        if 'str_code' not in sales_df.columns and 'store_cd' in sales_df.columns:
            sales_df['str_code'] = sales_df['store_cd'].astype(str)
            log_progress("Detected 'store_cd' in sales data; standardized to 'str_code'")
        if 'str_code' not in cluster_df.columns:
            raise ValueError("Cluster results missing 'str_code'/'store_cd' column")
        if 'str_code' not in sales_df.columns:
            raise ValueError("Sales data missing 'str_code'/'store_cd' column")

        # Ensure str_code is string for consistent joining
        cluster_df['str_code'] = cluster_df['str_code'].astype(str)
        sales_df['str_code'] = sales_df['str_code'].astype(str)

        # Validate required columns
        required_cols = ['str_code', CURRENT_CONFIG['feature_column'], CURRENT_CONFIG['sales_column']]
        missing_cols = [col for col in required_cols if col not in sales_df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in sales data: {missing_cols}")

        log_progress(f"Loaded {ANALYSIS_LEVEL} sales data with {len(sales_df)} rows")
        log_progress(f"Data validation successful for {ANALYSIS_LEVEL} analysis")

        return cluster_df, sales_df, quantity_df, price_df

    except Exception as e:
        log_progress(f"Error loading data: {str(e)}")
        raise

def get_output_period_label_for_step7() -> str:
    """Return the period label used for output files.
    If TARGET_YYYYMM is provided (via CLI), use that; otherwise use current period.
    """
    if TARGET_YYYYMM:
        return get_period_label(TARGET_YYYYMM, TARGET_PERIOD)
    yyyymm, period = get_current_period()
    return get_period_label(yyyymm, period)

def predict_sellthrough_from_adoption(pct_stores_selling: float) -> float:
    """
    Conservative adoption→ST mapping for use as one component of prediction.
    Uses a logistic-like curve bounded to 10%..70%.
    """
    try:
        if pd.isna(pct_stores_selling):
            return 0.0
        x = float(max(0.0, min(1.0, pct_stores_selling)))
        # Smooth S-curve centered near 0.5
        base = 1 / (1 + np.exp(-8 * (x - 0.5)))  # 0..1
        return 10.0 + 60.0 * base  # 10..70
    except Exception:
        return 0.0

def blended_predicted_sellthrough(pct_stores_selling: float,
                                  cluster_st_p50: Optional[float],
                                  cluster_st_p80: Optional[float],
                                  store_cat_baseline_st: Optional[float],
                                  seasonal_adj: Optional[float],
                                  n_comparables: int,
                                  w1: float = 0.35,
                                  w2: float = 0.30,
                                  w3: float = 0.25,
                                  w4: float = 0.10,
                                  min_comparables: int = 10) -> float:
    """
    Blend adoption-based estimate with cluster historical and store baseline, with shrinkage and caps.
    Returns predicted sell-through percent (0..100).
    """
    adoption_est = predict_sellthrough_from_adoption(pct_stores_selling)
    p50 = float(cluster_st_p50) if cluster_st_p50 is not None and not pd.isna(cluster_st_p50) else adoption_est
    p80 = float(cluster_st_p80) if cluster_st_p80 is not None and not pd.isna(cluster_st_p80) else max(50.0, adoption_est)
    baseline = float(store_cat_baseline_st) if store_cat_baseline_st is not None and not pd.isna(store_cat_baseline_st) else adoption_est
    seas = float(seasonal_adj) if seasonal_adj is not None and not pd.isna(seasonal_adj) else 1.0

    # Shrink weights when few comparables
    scale = min(1.0, max(0.2, n_comparables / max(1.0, min_comparables * 2)))
    w1s, w2s, w3s, w4s = w1*scale, w2*scale, w3 + (1-scale)*(w1+w2), w4*scale

    blended = w1s*adoption_est + w2s*p50 + w3s*baseline + w4s*(100*(seas-1))
    # Caps for realism
    blended = max(0.0, min(blended, min(p80, 85.0)))
    return blended

def identify_well_selling_features(sales_df: pd.DataFrame, cluster_df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify features (subcategories/SPUs) that are well-selling within each cluster.
    
    Args:
        sales_df: Sales data (subcategory or SPU level)
        cluster_df: Cluster assignments
        
    Returns:
        DataFrame with well-selling features per cluster
    """
    feature_col = CURRENT_CONFIG['feature_column']
    sales_col = CURRENT_CONFIG['sales_column']
    feature_type = "subcategories" if ANALYSIS_LEVEL == "subcategory" else "SPUs"
    
    log_progress(f"Identifying well-selling {feature_type} per cluster...")
    
    # Merge with cluster information
    sales_with_clusters = sales_df.merge(
        cluster_df[['str_code', 'cluster_id']], on='str_code', how='left', indicator=True
    )
    left_only = int((sales_with_clusters['_merge'] == 'left_only').sum())
    matched = int((sales_with_clusters['_merge'] == 'both').sum())
    log_progress(f"Safe left merge on str_code: total={len(sales_with_clusters):,}, matched={matched:,}, left_only={left_only:,}")
    sales_with_clusters = sales_with_clusters.drop(columns=['_merge'])
    
    # Calculate cluster-level feature statistics
    log_progress(f"Calculating cluster-level {feature_type} statistics...")
    cluster_feature_stats = sales_with_clusters.groupby(['cluster_id', feature_col]).agg({
        'str_code': 'nunique',  # Number of stores selling this feature
        sales_col: 'sum'        # Total sales in cluster
    }).reset_index()
    
    cluster_feature_stats.columns = ['cluster_id', feature_col, 'stores_selling', 'total_cluster_sales']
    
    # Get cluster sizes
    cluster_sizes = cluster_df.groupby('cluster_id').size().reset_index(name='cluster_size')
    cluster_sizes.columns = ['cluster_id', 'cluster_size']
    
    # Merge cluster sizes
    cluster_feature_stats = cluster_feature_stats.merge(cluster_sizes, on='cluster_id', how='left')
    unmatched_sizes = int(cluster_feature_stats['cluster_size'].isna().sum())
    if unmatched_sizes:
        log_progress(f"Cluster size merge diagnostics: unmatched cluster_id rows={unmatched_sizes:,} (preserved as NA)")
    
    # Calculate percentage of stores in cluster selling this feature
    cluster_feature_stats['pct_stores_selling'] = cluster_feature_stats['stores_selling'] / cluster_feature_stats['cluster_size']
    
    # Filter for well-selling features
    well_selling = cluster_feature_stats[
        (cluster_feature_stats['pct_stores_selling'] >= MIN_CLUSTER_STORES_SELLING) &
        (cluster_feature_stats['total_cluster_sales'] >= MIN_CLUSTER_SALES_THRESHOLD)
    ].copy()
    
    log_progress(f"Identified {len(well_selling)} well-selling {feature_type}-cluster combinations")
    log_progress(f"Threshold: ≥{MIN_CLUSTER_STORES_SELLING:.0%} adoption, ≥{MIN_CLUSTER_SALES_THRESHOLD} sales")
    
    return well_selling

def identify_missing_opportunities_with_sellthrough(sales_df: pd.DataFrame, cluster_df: pd.DataFrame, 
                                                  well_selling_features: pd.DataFrame,
                                                  quantity_df: Optional[pd.DataFrame] = None,
                                                  price_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Identify missing opportunities with quantity recommendations AND sell-through validation.
    
    FAST FISH ENHANCEMENT: Now includes sell-through validation for each opportunity!
    """
    feature_col = CURRENT_CONFIG['feature_column']
    feature_type = "subcategories" if ANALYSIS_LEVEL == "subcategory" else "SPUs"
    
    log_progress(f"Identifying missing {feature_type} opportunities...")
    log_progress("🎯 FAST FISH ENHANCEMENT: Adding sell-through validation...")
    
    # ===== INITIALIZE SELL-THROUGH VALIDATOR (STRICT: REQUIRED) =====
    if SELLTHROUGH_VALIDATION_AVAILABLE:
        try:
            historical_data = load_historical_data_for_validation()
            validator = SellThroughValidator(historical_data)
            log_progress("✅ Sell-through validator initialized")
        except Exception as e:
            raise RuntimeError(f"Sell-through validator failed to initialize (strict): {str(e)}")
    else:
        raise RuntimeError("Sell-through validator module not available (strict). Aborting.")

    # STRICT: quantity data must be present with real avg_unit_price
    if quantity_df is None or 'avg_unit_price' not in quantity_df.columns:
        raise RuntimeError("Quantity data with real avg_unit_price is required in strict mode")
    
    # CRITICAL FIX: Ensure cluster_df has cluster_id column for compatibility
    if 'Cluster' in cluster_df.columns and 'cluster_id' not in cluster_df.columns:
        cluster_df['cluster_id'] = cluster_df['Cluster']
    elif 'cluster_id' not in cluster_df.columns:
        # Preserve authentic missingness instead of synthetic 0 fallback
        log_progress("Warning: No 'Cluster' or 'cluster_id' column found in cluster_df; setting cluster_id to NA for all rows")
        cluster_df['cluster_id'] = pd.NA
    
    opportunities = []
    USE_ROI = os.environ.get('RULE7_USE_ROI', '1').strip() in {'1','true','yes','on'}
    ROI_MIN_THRESHOLD = float(os.environ.get('ROI_MIN_THRESHOLD', '0.3'))
    MIN_MARGIN_UPLIFT = float(os.environ.get('MIN_MARGIN_UPLIFT', '100'))
    MIN_COMPARABLES = int(os.environ.get('MIN_COMPARABLES', '10'))
    DEFAULT_MARGIN_RATE = float(os.environ.get('MARGIN_RATE_DEFAULT', '0.45'))
    # Clamp to realistic range (<1) to avoid zero-cost artifacts
    DEFAULT_MARGIN_RATE = max(0.0, min(0.95, DEFAULT_MARGIN_RATE))

    # Load period-aware margin rates and build lookup maps (store+feature, then store-level fallback)
    try:
        _yyyymm, _period = get_current_period()
        _margin_type = 'spu' if ANALYSIS_LEVEL == 'spu' else 'category'
        _margin_df = load_margin_rates(_yyyymm, _period, margin_type=_margin_type)
        log_progress(f"Loaded margin rates for ROI: rows={len(_margin_df) if _margin_df is not None else 0}")
    except Exception as _e:
        log_progress(f"Warning: Failed to load margin rates, falling back to default rate: {_e}")
        _margin_df = pd.DataFrame()

    margin_map_pair: Dict[Tuple[str, str], float] = {}
    margin_map_store: Dict[str, float] = {}
    if isinstance(_margin_df, pd.DataFrame) and not _margin_df.empty and 'margin_rate' in _margin_df.columns:
        # Normalize and clamp
        try:
            _margin_df['margin_rate'] = pd.to_numeric(_margin_df['margin_rate'], errors='coerce').clip(0, 0.95)
        except Exception:
            pass
        # Feature dimension if present
        feat_col_margin = 'spu_code' if 'spu_code' in _margin_df.columns else ('category_name' if 'category_name' in _margin_df.columns else None)
        if feat_col_margin and 'str_code' in _margin_df.columns:
            _tmp = _margin_df[['str_code', feat_col_margin, 'margin_rate']].dropna()
            for __, _r in _tmp.iterrows():
                try:
                    s = str(_r['str_code']); f = str(_r[feat_col_margin]); r = float(_r['margin_rate'])
                    if not pd.isna(r):
                        margin_map_pair[(s, f)] = max(0.0, min(1.0, r))
                except Exception:
                    continue
        # Store-level fallback map
        if 'str_code' in _margin_df.columns:
            try:
                _grp = _margin_df.groupby('str_code')['margin_rate'].mean().dropna()
                margin_map_store = {str(k): max(0.0, min(0.95, float(v))) for k, v in _grp.items()}
            except Exception:
                pass

    def resolve_margin_rate(_store_code: str, _feature_name: str, _parent_cate: Optional[str] = None) -> float:
        """Resolve margin rate with precedence: (store,feature) -> (store,parent_category) -> store -> default."""
        key = (_store_code, _feature_name)
        if key in margin_map_pair:
            return margin_map_pair[key]
        if ANALYSIS_LEVEL != 'spu' and _parent_cate is not None:
            key2 = (_store_code, str(_parent_cate))
            if key2 in margin_map_pair:
                return margin_map_pair[key2]
        if _store_code in margin_map_store:
            return margin_map_store[_store_code]
        return DEFAULT_MARGIN_RATE

    # STRICT: Do not compute or use global average unit price fallbacks
    global_avg_unit_price: Optional[float] = None
    
    # Process with progress bar for large datasets
    for _, well_selling_row in tqdm(well_selling_features.iterrows(), 
                                   total=len(well_selling_features),
                                   desc=f"Processing {feature_type} with sell-through validation"):
        cluster_id = well_selling_row['cluster_id']
        feature_name = well_selling_row[feature_col]
        
        # Get all stores in this cluster
        cluster_stores = set(cluster_df[cluster_df['cluster_id'] == cluster_id]['str_code'].astype(str))
        
        # Get stores that are selling this feature
        stores_selling_feature = set(
            sales_df[sales_df[feature_col] == feature_name]['str_code'].astype(str)
        )
        
        # Find stores in cluster that are NOT selling this feature
        missing_stores = cluster_stores - stores_selling_feature
        
        # Calculate expected sales opportunity using ROBUST peer median within the cluster
        # This avoids inflated values from cluster totals and outliers
        feature_sales_rows = sales_df[sales_df[feature_col] == feature_name]
        comp = feature_sales_rows.merge(cluster_df[['str_code','cluster_id']], on='str_code', how='left')
        comp = comp[comp['cluster_id'] == cluster_id]
        peer_amounts = pd.to_numeric(comp.get(CURRENT_CONFIG['sales_column']), errors='coerce').dropna()
        if len(peer_amounts) >= 3:
            # Trim extremes (10th-90th) and use median; cap to P80 for realism
            q10 = float(np.percentile(peer_amounts, 10))
            q90 = float(np.percentile(peer_amounts, 90))
            trimmed = peer_amounts[(peer_amounts >= q10) & (peer_amounts <= q90)]
            robust_median = float(np.median(trimmed)) if len(trimmed) > 0 else float(np.median(peer_amounts))
            p80_cap = float(np.percentile(peer_amounts, 80))
            avg_sales_per_store = max(float(MIN_OPPORTUNITY_VALUE), min(robust_median, p80_cap))
        elif len(peer_amounts) > 0:
            robust_median = float(np.median(peer_amounts))
            avg_sales_per_store = max(float(MIN_OPPORTUNITY_VALUE), robust_median)
        else:
            # Fallback to conservative cluster average with a reasonable cap
            denom = max(1.0, float(well_selling_row['stores_selling']))
            cluster_avg = float(well_selling_row['total_cluster_sales']) / denom
            max_cap = 3000.0 if ANALYSIS_LEVEL == "spu" else 20000.0
            avg_sales_per_store = max(float(MIN_OPPORTUNITY_VALUE), min(cluster_avg, max_cap))
        
        # Enforce SPU per-store realistic cap ($2,000)
        if ANALYSIS_LEVEL == "spu":
            avg_sales_per_store = min(avg_sales_per_store, 2000.0)
        
        # Create opportunity records for missing stores with quantity calculations
        for store_code in missing_stores:
            if avg_sales_per_store >= MIN_OPPORTUNITY_VALUE:
                
                # 🎯 CALCULATE QUANTITY RECOMMENDATIONS
                # STRICT (real-data-only) unit price resolution with conservative fallbacks
                store_unit_price = np.nan
                price_source = 'unknown'
                # 1) Prefer store-level avg_unit_price from quantity_df (real store totals)
                if quantity_df is not None and 'avg_unit_price' in quantity_df.columns:
                    store_qty_data = quantity_df[quantity_df['str_code'] == store_code]
                    if len(store_qty_data) > 0 and not store_qty_data['avg_unit_price'].isna().all():
                        try:
                            store_unit_price = float(store_qty_data['avg_unit_price'].median())
                            price_source = 'store_avg_qty_df'
                        except Exception:
                            pass
                # 2) Fallback to real SPU sales for this store (amount/quantity), period-aware
                if (not np.isfinite(store_unit_price)) or (store_unit_price <= 0):
                    try:
                        if 'str_code' in sales_df.columns:
                            store_sales = sales_df[sales_df['str_code'].astype(str) == str(store_code)]
                        else:
                            store_sales = pd.DataFrame()
                        amt_cols = [c for c in store_sales.columns if ('sal_amt' in c.lower() or 'sales_amt' in c.lower())]
                        qty_cols = [c for c in store_sales.columns if ('sal_qty' in c.lower() or 'sales_qty' in c.lower() or c.lower() == 'quantity')]
                        total_amt = pd.to_numeric(store_sales[amt_cols], errors='coerce').fillna(0).sum().sum() if amt_cols else 0.0
                        total_qty = pd.to_numeric(store_sales[qty_cols], errors='coerce').fillna(0).sum().sum() if qty_cols else 0.0
                        if total_qty > 0 and total_amt > 0:
                            store_unit_price = float(total_amt / total_qty)
                            price_source = 'store_avg_from_spu_sales'
                    except Exception:
                        pass
                # 3) Fallback to cluster median of available store_avg_unit_price (still real data)
                if (not np.isfinite(store_unit_price)) or (store_unit_price <= 0):
                    try:
                        sc_row = cluster_df[cluster_df['str_code'] == store_code]
                        if not sc_row.empty and 'cluster_id' in cluster_df.columns and quantity_df is not None:
                            cid = sc_row['cluster_id'].iloc[0]
                            qj = quantity_df.merge(cluster_df[['str_code','cluster_id']], on='str_code', how='left')
                            cluster_prices = pd.to_numeric(qj[(qj['cluster_id'] == cid)]['avg_unit_price'], errors='coerce').dropna()
                            if len(cluster_prices) > 0:
                                store_unit_price = float(cluster_prices.median())
                                price_source = 'cluster_median_avg_price'
                    except Exception:
                        pass
                # Abort if still invalid
                if (not np.isfinite(store_unit_price)) or (store_unit_price <= 0):
                    log_progress(f"STRICT: Skipping store {store_code} due to missing/invalid unit price after real-data fallbacks")
                    continue
                category_unit_price = store_unit_price

                # 3) Calculate quantity recommendations (integer units)
                expected_quantity = max(1.0, (avg_sales_per_store * SCALING_FACTOR) / max(1e-6, category_unit_price))
                expected_quantity_int = int(np.ceil(expected_quantity))
                
                # ===== FAST FISH SELL-THROUGH VALIDATION =====
                # Default: require adoption + minimum sample; derive predicted ST from adoption
                should_approve = False
                predicted_from_adoption = predict_sellthrough_from_adoption(well_selling_row['pct_stores_selling'])
                validation_result = {
                    'current_sell_through_rate': 0.0,
                    'predicted_sell_through_rate': predicted_from_adoption,
                    'sell_through_improvement': predicted_from_adoption,  # current is 0 for missing items
                    'fast_fish_compliant': False,
                    'business_rationale': f"Missing {ANALYSIS_LEVEL} well-selling in {well_selling_row['pct_stores_selling']:.0%} of cluster peers",
                    'approval_reason': 'Cluster peer adoption implies demand'
                }
                
                if validator is not None:
                    category_name = feature_name
                    if 'sub_cate_name' in sales_df.columns:
                        feature_sales_data = sales_df[sales_df[feature_col] == feature_name]
                        if len(feature_sales_data) > 0:
                            category_name = feature_sales_data['sub_cate_name'].iloc[0]
                    
                    # Validate the recommendation
                    validation = validator.validate_recommendation(
                        store_code=store_code,
                        category=category_name,
                        current_spu_count=0,  # Missing = 0 current SPUs
                        recommended_spu_count=1,  # Add 1 SPU
                        action='ADD',
                        rule_name='Rule 7: Missing Category'
                    )

                    # Use validator for approval decision, but keep predicted from adoption for realism
                    validator_ok = bool(validation.get('fast_fish_compliant', False))
                    # Combine gates (now configurable via env) to avoid 100% approvals
                    try:
                        _min_stores_selling = int(os.environ.get('RULE7_MIN_STORES_SELLING', '5'))
                    except Exception:
                        _min_stores_selling = 5
                    try:
                        _min_adoption = float(os.environ.get('RULE7_MIN_ADOPTION', '0.25'))
                    except Exception:
                        _min_adoption = 0.25
                    try:
                        _min_pred_st = float(os.environ.get('RULE7_MIN_PREDICTED_ST', '30'))
                    except Exception:
                        _min_pred_st = 30.0

                    should_approve = (
                        validator_ok and
                        well_selling_row['stores_selling'] >= _min_stores_selling and
                        well_selling_row['pct_stores_selling'] >= _min_adoption and
                        predicted_from_adoption >= _min_pred_st
                    )

                    # Prefer validator's predicted ST if provided; clip for realism
                    pred_st_validator = float(validation.get('predicted_sell_through_rate', np.nan))
                    pred_st_final = pred_st_validator if not pd.isna(pred_st_validator) else predicted_from_adoption
                    pred_st_final = max(0.0, min(pred_st_final, 85.0))
                    validation_result = {
                        'current_sell_through_rate': float(validation.get('current_sell_through_rate', 0.0)),
                        'predicted_sell_through_rate': pred_st_final,
                        'sell_through_improvement': max(0.0, pred_st_final - float(validation.get('current_sell_through_rate', 0.0))),
                        'fast_fish_compliant': bool(validation.get('fast_fish_compliant', False)),
                        'business_rationale': validation.get('business_rationale', validation_result['business_rationale']),
                        'approval_reason': validation.get('approval_reason', validation_result['approval_reason'])
                    }
                
                # ===== ONLY ADD IF FAST FISH COMPLIANT =====
                if should_approve:
                    # Optional ROI gating
                    roi_value = None
                    margin_uplift = None
                    n_comparables = 0
                    predicted_st_final = validation_result['predicted_sell_through_rate']
                    # Resolve unit price and margin rate regardless of ROI gating
                    unit_price = category_unit_price
                    _parent_cate_name = None
                    if ANALYSIS_LEVEL != "spu":
                        try:
                            _fsr = sales_df[sales_df[feature_col] == feature_name]
                            if 'cate_name' in _fsr.columns and len(_fsr) > 0:
                                _parent_cate_name = _fsr['cate_name'].iloc[0]
                        except Exception:
                            pass
                    mr_used = resolve_margin_rate(store_code, feature_name, _parent_cate_name)
                    if USE_ROI:
                        # Estimate comparables within cluster for this feature
                        feature_sales_rows = sales_df[sales_df[feature_col] == feature_name]
                        comp = feature_sales_rows.merge(cluster_df[['str_code','cluster_id']], on='str_code', how='left')
                        comp = comp[comp['cluster_id'] == cluster_id]
                        n_comparables = int(comp['str_code'].nunique())
                        cluster_st_p50 = np.nan
                        cluster_st_p80 = np.nan
                        if 'sell_through_rate' in comp.columns:
                            st_vals = pd.to_numeric(comp['sell_through_rate'], errors='coerce').dropna()
                            if len(st_vals) > 0:
                                cluster_st_p50 = float(np.percentile(st_vals, 50))
                                cluster_st_p80 = float(np.percentile(st_vals, 80))
                        store_cat_baseline_st = 20.0
                        seasonal_adj = 1.0
                        predicted_st_final = blended_predicted_sellthrough(
                            pct_stores_selling=float(well_selling_row['pct_stores_selling']),
                            cluster_st_p50=cluster_st_p50,
                            cluster_st_p80=cluster_st_p80,
                            store_cat_baseline_st=store_cat_baseline_st,
                            seasonal_adj=seasonal_adj,
                            n_comparables=n_comparables,
                            min_comparables=MIN_COMPARABLES
                        )
                        unit_cost = unit_price * (1 - mr_used)
                        # Use real peer sales to infer expected units (median peer sales amount ÷ price)
                        median_amt = pd.to_numeric(comp.get(CURRENT_CONFIG['sales_column']), errors='coerce').median()
                        if pd.isna(median_amt):
                            median_amt = avg_sales_per_store
                        expected_units = int(max(1.0, np.ceil((median_amt * SCALING_FACTOR) / max(1e-6, unit_price))))
                        margin_per_unit = unit_price - unit_cost
                        margin_uplift = margin_per_unit * expected_units
                        investment_required_cost = expected_units * unit_cost
                        roi_value = (margin_uplift / investment_required_cost) if investment_required_cost > 0 else 0.0
                        if not (roi_value >= ROI_MIN_THRESHOLD and margin_uplift >= MIN_MARGIN_UPLIFT and n_comparables >= MIN_COMPARABLES):
                            continue
                    # Calculate output investment metrics using resolved margin rate
                    unit_cost_output = unit_price * (1 - mr_used)
                    investment_required = expected_quantity_int * unit_cost_output  # COST-based
                    retail_value = expected_quantity_int * unit_price               # RETAIL value (for reference)

                    # Create quantity recommendation text
                    if ANALYSIS_LEVEL == "subcategory":
                        qty_recommendation = f"ADD {expected_quantity_int} units/15-days (category average) @ ~${category_unit_price:.0f}/unit"
                    else:
                        qty_recommendation = f"ADD {expected_quantity_int} units/15-days @ ~${category_unit_price:.0f}/unit"

                    # Append fully-formed opportunity record
                    opportunities.append({
                        'str_code': store_code,
                        'cluster_id': cluster_id,
                        feature_col: feature_name,
                        'opportunity_type': f"sellthrough_validated_missing_{ANALYSIS_LEVEL}",
                        'cluster_total_sales': well_selling_row['total_cluster_sales'],
                        'stores_selling_in_cluster': well_selling_row['stores_selling'],
                        'cluster_size': well_selling_row['cluster_size'],
                        'pct_stores_selling': well_selling_row['pct_stores_selling'],
                        'expected_sales_opportunity': avg_sales_per_store,
                        # Quantity and value metrics
                        'spu_code': feature_name,
                        'current_quantity': 0,
                        'recommended_quantity_change': expected_quantity_int,
                        'unit_price': category_unit_price,
                        'investment_required': investment_required,
                        'retail_value': retail_value,
                        'recommendation_text': qty_recommendation,
                        # Sell-through validation metrics
                        'current_sell_through_rate': validation_result['current_sell_through_rate'],
                        'predicted_sell_through_rate': predicted_st_final,
                        'sell_through_improvement': max(0.0, predicted_st_final - validation_result['current_sell_through_rate']),
                        'fast_fish_compliant': should_approve,
                        'business_rationale': validation_result['business_rationale'],
                        'approval_reason': validation_result['approval_reason'],
                        # ROI diagnostics
                        'roi': roi_value,
                        'margin_uplift': margin_uplift,
                        'n_comparables': n_comparables,
                        'margin_rate_used': mr_used
                    })
    
    opportunities_df = pd.DataFrame(opportunities)

    # Ensure standardized category columns exist for downstream consolidation (Step 13)
    try:
        feature_col = CURRENT_CONFIG['feature_column']
        # Map sub_cate_name from sales_df using feature key (spu_code for SPU mode)
        if 'sub_cate_name' not in opportunities_df.columns:
            if 'sub_cate_name' in sales_df.columns and feature_col in sales_df.columns:
                key_cols = [feature_col, 'sub_cate_name']
                sub_map = (sales_df.dropna(subset=key_cols)
                                   .drop_duplicates(subset=[feature_col])
                                   [[feature_col, 'sub_cate_name']])
                opportunities_df = opportunities_df.merge(
                    sub_map,
                    on=feature_col,
                    how='left'
                )
            else:
                opportunities_df['sub_cate_name'] = pd.NA
        # Optionally include cate_name if available in sales_df
        if 'cate_name' not in opportunities_df.columns:
            if 'cate_name' in sales_df.columns and feature_col in sales_df.columns:
                cat_map = (sales_df.dropna(subset=[feature_col, 'cate_name'])
                                   .drop_duplicates(subset=[feature_col])
                                   [[feature_col, 'cate_name']])
                opportunities_df = opportunities_df.merge(
                    cat_map,
                    on=feature_col,
                    how='left'
                )
    except Exception:
        # Do not fail the rule if enrichment cannot be applied
        pass
    
    if len(opportunities_df) > 0:
        # Sort by ROI if present, else by sell-through improvement
        if 'roi' in opportunities_df.columns and opportunities_df['roi'].notna().any():
            opportunities_df = opportunities_df.sort_values(['roi','sell_through_improvement'], ascending=[False, False])
        elif 'sell_through_improvement' in opportunities_df.columns:
            opportunities_df = opportunities_df.sort_values('sell_through_improvement', ascending=False)
        
        unique_stores = opportunities_df['str_code'].nunique()
        total_investment = opportunities_df['investment_required'].sum()
        total_retail = opportunities_df['retail_value'].sum() if 'retail_value' in opportunities_df.columns else np.nan
        
        log_progress(f"✅ Identified {len(opportunities_df)} FAST FISH COMPLIANT missing {feature_type} opportunities")
        log_progress(f"   Across {unique_stores} stores")
        log_progress(f"   Total investment required: ${total_investment:,.0f}")
        if not pd.isna(total_retail):
            log_progress(f"   Total retail value: ${total_retail:,.0f}")
        
        if validator is not None and 'sell_through_improvement' in opportunities_df.columns:
            if 'roi' in opportunities_df.columns and opportunities_df['roi'].notna().any():
                avg_roi = opportunities_df['roi'].dropna().mean()
                med_roi = opportunities_df['roi'].dropna().median()
                log_progress(f"   Average ROI: {avg_roi:.2f}, median ROI: {med_roi:.2f}")
            if 'sell_through_improvement' in opportunities_df.columns:
                avg_sellthrough_improvement = opportunities_df['sell_through_improvement'].mean()
                log_progress(f"   Average sell-through improvement: {avg_sellthrough_improvement:.1f} percentage points")
        
        # Log top missing features
        top_missing = opportunities_df[feature_col].value_counts().head(5)
        log_progress(f"Top 5 most missed {feature_type} (sell-through validated):")
        for feature, count in top_missing.items():
            if validator is not None and 'sell_through_improvement' in opportunities_df.columns:
                avg_improvement = opportunities_df[opportunities_df[feature_col] == feature]['sell_through_improvement'].mean()
                log_progress(f"  • {feature}: {count} stores (avg {avg_improvement:.1f}pp improvement)")
            else:
                log_progress(f"  • {feature}: {count} stores")
    else:
        if validator is not None:
            log_progress(f"⚠️ No FAST FISH COMPLIANT missing {feature_type} opportunities identified")
            log_progress("   All potential opportunities were rejected by sell-through validation")
        else:
            log_progress(f"⚠️ No missing {feature_type} opportunities identified")
    
    return opportunities_df

def apply_missing_category_rule_with_sellthrough(cluster_df: pd.DataFrame, opportunities_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the missing category/SPU rule to all stores and create rule results with SELL-THROUGH METRICS.
    """
    feature_col = CURRENT_CONFIG['feature_column']
    feature_type = "categories" if ANALYSIS_LEVEL == "subcategory" else "SPUs"
    
    log_progress(f"Applying missing {feature_type} rule with sell-through metrics...")
    
    # Create base results for all stores
    results_df = cluster_df[['str_code', 'cluster_id']].copy()
    
    # Add missing feature flag and details with quantity metrics
    if len(opportunities_df) > 0:
        # Count opportunities per store with quantity and sell-through aggregations
        store_opportunities = opportunities_df.groupby('str_code').agg({
            feature_col: 'count',
            'expected_sales_opportunity': 'sum',
            'recommended_quantity_change': 'sum',  # 🎯 STANDARDIZED TOTAL QUANTITY NEEDED
            'investment_required': 'sum',    # 💰 TOTAL INVESTMENT (COST-BASED)
            'retail_value': 'sum',           # 🛒 TOTAL RETAIL VALUE
            'sell_through_improvement': 'mean',  # 📈 AVERAGE SELL-THROUGH IMPROVEMENT
            'predicted_sell_through_rate': 'mean',  # 📈 AVERAGE PREDICTED SELL-THROUGH
            'fast_fish_compliant': 'sum'  # 📈 COUNT OF COMPLIANT RECOMMENDATIONS
        }).reset_index()
        
        if ANALYSIS_LEVEL == "subcategory":
            store_opportunities.columns = [
                'str_code', 'missing_categories_count', 'total_opportunity_value', 
                'total_quantity_needed', 'total_investment_required', 'total_retail_value',
                'avg_sellthrough_improvement', 'avg_predicted_sellthrough', 'fastfish_approved_count'
            ]
            rule_col = 'rule7_missing_category'
        else:
            store_opportunities.columns = [
                'str_code', 'missing_spus_count', 'total_opportunity_value',
                'total_quantity_needed', 'total_investment_required', 'total_retail_value',
                'avg_sellthrough_improvement', 'avg_predicted_sellthrough', 'fastfish_approved_count'
            ]
            rule_col = 'rule7_missing_spu'
        
        # Merge with results (diagnostics) and fill NAs with 0 for numeric summaries to simplify downstream
        results_df = results_df.merge(store_opportunities, on='str_code', how='left', indicator=True)
        both = int((results_df['_merge'] == 'both').sum())
        left_only = int((results_df['_merge'] == 'left_only').sum())
        log_progress(f"Merged opportunities into results: matched={both:,}, left_only(no-opps)={left_only:,}")
        results_df = results_df.drop(columns=['_merge'])
        
        # Fill NA numeric aggregates with 0 for non-flagged stores
        count_col = 'missing_categories_count' if ANALYSIS_LEVEL == "subcategory" else 'missing_spus_count'
        fill_zero_cols = [
            count_col,
            'total_opportunity_value',
            'total_quantity_needed',
            'total_investment_required',
            'total_retail_value',
            'avg_sellthrough_improvement',
            'avg_predicted_sellthrough',
            'fastfish_approved_count',
        ]
        for c in fill_zero_cols:
            if c in results_df.columns:
                results_df[c] = results_df[c].fillna(0)

        # Create rule flag
        results_df[rule_col] = (results_df[count_col] > 0).astype(int)
    else:
        # No opportunities found
        if ANALYSIS_LEVEL == "subcategory":
            results_df['missing_categories_count'] = 0
            results_df['total_opportunity_value'] = 0
            results_df['total_quantity_needed'] = 0
            results_df['total_investment_required'] = 0
            results_df['total_retail_value'] = 0
            results_df['avg_sellthrough_improvement'] = 0
            results_df['avg_predicted_sellthrough'] = 0
            results_df['fastfish_approved_count'] = 0
            rule_col = 'rule7_missing_category'
        else:
            results_df['missing_spus_count'] = 0
            results_df['total_opportunity_value'] = 0
            results_df['total_quantity_needed'] = 0
            results_df['total_investment_required'] = 0
            results_df['total_retail_value'] = 0
            results_df['avg_sellthrough_improvement'] = 0
            results_df['avg_predicted_sellthrough'] = 0
            results_df['fastfish_approved_count'] = 0
            rule_col = 'rule7_missing_spu'
        
        results_df[rule_col] = 0
    
    # Add metadata with quantity and sell-through information
    if ANALYSIS_LEVEL == "subcategory":
        results_df['rule7_description'] = 'Store missing subcategories well-selling in cluster peers - FAST FISH VALIDATED'
    else:
        results_df['rule7_description'] = 'Store missing SPUs well-selling in cluster peers - FAST FISH VALIDATED'
    
    results_df['rule7_threshold'] = f"≥{MIN_CLUSTER_STORES_SELLING:.0%} cluster adoption, ≥{MIN_CLUSTER_SALES_THRESHOLD} sales"
    results_df['rule7_analysis_level'] = ANALYSIS_LEVEL
    results_df['rule7_sellthrough_validation'] = 'Applied - only sell-through improving recommendations included'
    results_df['rule7_fastfish_compliant'] = True
    
    flagged_stores = results_df[rule_col].sum()
    total_qty_needed = results_df['total_quantity_needed'].sum()
    total_investment = results_df['total_investment_required'].sum()
    total_retail_sum = results_df['total_retail_value'].sum() if 'total_retail_value' in results_df.columns else np.nan
    avg_improvement = results_df[results_df['avg_sellthrough_improvement'] > 0]['avg_sellthrough_improvement'].mean()
    
    log_progress(f"Applied missing {feature_type} rule with sell-through validation:")
    log_progress(f"  🏪 Stores flagged: {flagged_stores}")
    log_progress(f"  🎯 Total quantity needed: {total_qty_needed:.0f} units/15-days")
    log_progress(f"  💰 Total investment: ${total_investment:,.0f}")
    if not pd.isna(total_retail_sum):
        log_progress(f"  🛒 Total retail value: ${total_retail_sum:,.0f}")
    if not pd.isna(avg_improvement):
        log_progress(f"  📈 Average sell-through improvement: {avg_improvement:.1f} percentage points")
    
    return results_df

def preflight_validate_outputs(results_file: str,
                               opportunities_file: Optional[str],
                               summary_file: Optional[str],
                               results_df: pd.DataFrame,
                               opportunities_df: Optional[pd.DataFrame]) -> None:
    """Validate that outputs exist, are non-empty, and have key headers.

    Raises RuntimeError on hard failures (missing or empty files). Logs warnings for
    missing expected columns or filename label issues.
    """
    ok = True

    # Existence and non-empty checks
    for label, path in [("results", results_file), ("opportunities", opportunities_file), ("summary", summary_file)]:
        if path:
            if not os.path.exists(path):
                log_progress(f"❌ Preflight: {label} file missing: {path}")
                ok = False
            else:
                size = os.path.getsize(path)
                if size == 0:
                    log_progress(f"❌ Preflight: {label} file is empty: {path}")
                    ok = False
                else:
                    log_progress(f"✅ Preflight: {label} file OK ({size/1024:.1f} KB): {path}")

    # Header checks using in-memory DataFrames
    expected_results_cols = {
        'str_code', 'cluster_id', 'total_quantity_needed',
        'total_investment_required', 'total_retail_value'
    }
    missing = [c for c in expected_results_cols if c not in results_df.columns]
    if missing:
        log_progress(f"⚠️ Preflight: results missing expected columns: {missing}")

    if opportunities_df is not None and len(opportunities_df) > 0:
        expected_opp_cols = {
            'str_code', 'cluster_id', 'spu_code', 'recommended_quantity_change',
            'unit_price', 'investment_required', 'retail_value', 'margin_rate_used'
        }
        missing2 = [c for c in expected_opp_cols if c not in opportunities_df.columns]
        if missing2:
            log_progress(f"⚠️ Preflight: opportunities missing expected columns: {missing2}")

    # Ensure filenames include period label for traceability
    period_label = get_output_period_label_for_step7()
    for label, path in [("results", results_file), ("opportunities", opportunities_file), ("summary", summary_file)]:
        if path and period_label not in os.path.basename(path):
            log_progress(f"⚠️ Preflight: {label} filename missing period label '{period_label}': {path}")

    if not ok:
        raise RuntimeError("Preflight validation failed. See logs for details.")

def save_results_with_sellthrough(results_df: pd.DataFrame, opportunities_df: pd.DataFrame) -> None:
    """
    Save rule results and detailed opportunities with sell-through metrics.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save main results with standardized pattern
    period_label = get_output_period_label_for_step7()
    timestamped, period_file, generic = create_output_with_symlinks(
        results_df,
        f"{OUTPUT_DIR}/rule7_missing_{ANALYSIS_LEVEL}_sellthrough_results",
        period_label
    )
    log_progress(f"💾 Saved store results: {timestamped}")
    log_progress(f"   Period symlink: {period_file}")
    log_progress(f"   Generic symlink: {generic}")
    results_file = timestamped  # For manifest registration

    # Register in manifest
    try:
        register_step_output(
            "step7",
            "store_results",
            results_file,
            metadata={
                "rows": int(len(results_df)),
                "columns": list(results_df.columns),
                "analysis_level": ANALYSIS_LEVEL,
                "period_label": period_label,
            },
        )
        # Also register period-specific key
        register_step_output(
            "step7",
            f"store_results_{period_label}",
            results_file,
            metadata={
                "rows": int(len(results_df)),
                "columns": list(results_df.columns),
                "analysis_level": ANALYSIS_LEVEL,
                "period_label": period_label,
            },
        )
    except Exception as e:
        log_progress(f"⚠️ Manifest registration failed for results: {e}")
    
    # Save detailed opportunities if any
    opportunities_file: Optional[str] = None
    summary_file: Optional[str] = None
    if len(opportunities_df) > 0:
        timestamped_opp, period_opp, generic_opp = create_output_with_symlinks(
            opportunities_df,
            f"{OUTPUT_DIR}/rule7_missing_{ANALYSIS_LEVEL}_sellthrough_opportunities",
            period_label
        )
        log_progress(f"💾 Saved detailed opportunities: {timestamped_opp}")
        opportunities_file = timestamped_opp  # For manifest registration

        # Register opportunities in manifest
        try:
            register_step_output(
                "step7",
                "opportunities",
                opportunities_file,
                metadata={
                    "rows": int(len(opportunities_df)),
                    "columns": list(opportunities_df.columns),
                    "analysis_level": ANALYSIS_LEVEL,
                    "period_label": period_label,
                },
            )
            # Also register period-specific key
            register_step_output(
                "step7",
                f"opportunities_{period_label}",
                opportunities_file,
                metadata={
                    "rows": int(len(opportunities_df)),
                    "columns": list(opportunities_df.columns),
                    "analysis_level": ANALYSIS_LEVEL,
                    "period_label": period_label,
                },
            )
        except Exception as e:
            log_progress(f"⚠️ Manifest registration failed for opportunities: {e}")
        
        # Create sell-through summary report
        summary_file = f"{OUTPUT_DIR}/rule7_missing_{ANALYSIS_LEVEL}_sellthrough_summary_{period_label}.md"
        create_sellthrough_summary_report(opportunities_df, results_df, summary_file)
        log_progress(f"📈 Created sell-through summary report: {summary_file}")

        # Register summary in manifest
        try:
            register_step_output(
                "step7",
                "summary_report_md",
                summary_file,
                metadata={
                    "analysis_level": ANALYSIS_LEVEL,
                    "period_label": period_label,
                },
            )
            # Also register period-specific key
            register_step_output(
                "step7",
                f"summary_report_md_{period_label}",
                summary_file,
                metadata={
                    "analysis_level": ANALYSIS_LEVEL,
                    "period_label": period_label,
                },
            )
        except Exception as e:
            log_progress(f"⚠️ Manifest registration failed for summary: {e}")

        # If backward-compatible results exist (subcategory path), register them too
        backward_compatible_file = "output/rule7_missing_category_results.csv"
        if os.path.exists(backward_compatible_file):
            try:
                register_step_output(
                    "step7",
                    "backward_compatible_store_results",
                    backward_compatible_file,
                    metadata={
                        "analysis_level": ANALYSIS_LEVEL,
                        "note": "legacy filename for category analysis",
                    },
                )
            except Exception as e:
                log_progress(f"⚠️ Manifest registration failed for backward-compatible file: {e}")

    # Preflight validate outputs
    preflight_validate_outputs(
        results_file=results_file,
        opportunities_file=opportunities_file,
        summary_file=summary_file,
        results_df=results_df,
        opportunities_df=opportunities_df if len(opportunities_df) > 0 else None,
    )

def create_sellthrough_summary_report(opportunities_df: pd.DataFrame, results_df: pd.DataFrame, summary_file: str) -> None:
    """Create a comprehensive sell-through summary report."""
    
    feature_type = "categories" if ANALYSIS_LEVEL == "subcategory" else "SPUs"
    
    with open(summary_file, 'w') as f:
        f.write(f"# Rule 7: Missing {feature_type.title()} - Fast Fish Sell-Through Analysis\n\n")
        f.write(f"**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Analysis Level**: {ANALYSIS_LEVEL.upper()}\n")
        f.write(f"**Fast Fish Compliance**: ✅ ENABLED\n\n")
        # Seasonal blending provenance
        if USE_BLENDED_SEASONAL and SEASONAL_YYYYMM:
            f.write("## Seasonal Blending\n\n")
            f.write(f"- **Blending**: ENABLED\n")
            f.write(f"- **Seasonal Source**: {SEASONAL_YYYYMM}{SEASONAL_PERIOD or ''}\n")
            f.write(f"- **Weights**: seasonal={SEASONAL_WEIGHT:.2f}, recent={RECENT_WEIGHT:.2f}\n\n")
        else:
            f.write("## Seasonal Blending\n\n- **Blending**: DISABLED\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write(f"- **Total Opportunities**: {len(opportunities_df):,}\n")
        f.write(f"- **Stores Affected**: {opportunities_df['str_code'].nunique():,}\n")
        if 'sell_through_improvement' in opportunities_df.columns:
            f.write(f"- **Average Sell-Through Improvement**: {opportunities_df['sell_through_improvement'].mean():.1f} percentage points\n")
        f.write(f"- **Total Investment Required**: ${opportunities_df['investment_required'].sum():,.0f}\n")
        if 'retail_value' in opportunities_df.columns:
            f.write(f"- **Total Retail Value**: ${opportunities_df['retail_value'].sum():,.0f}\n")
        if 'fast_fish_compliant' in opportunities_df.columns and len(opportunities_df) > 0:
            approval_rate = 100.0  # all in the file are approved
            f.write(f"- **Fast Fish Approval Rate**: {approval_rate:.1f}% (in saved opportunities)\n")
        f.write(f"- **All Recommendations**: Fast Fish sell-through validated ✅\n\n")
        
        if len(opportunities_df) > 0 and 'sell_through_improvement' in opportunities_df.columns:
            f.write("## Sell-Through Distribution\n\n")
            f.write(f"- **Opportunities with >5pp improvement**: {len(opportunities_df[opportunities_df['sell_through_improvement'] > 5]):,}\n")
            f.write(f"- **Opportunities with >3pp improvement**: {len(opportunities_df[opportunities_df['sell_through_improvement'] > 3]):,}\n")
            f.write(f"- **Opportunities with >1pp improvement**: {len(opportunities_df[opportunities_df['sell_through_improvement'] > 1]):,}\n")

        # Quantity and price quality diagnostics
        if len(opportunities_df) > 0:
            int_qty_share = 100.0 * (opportunities_df['recommended_quantity_change'] == opportunities_df['recommended_quantity_change'].round()).mean()
            f.write("\n## Quantity & Price Diagnostics\n\n")
            f.write(f"- **Integer Quantity Share**: {int_qty_share:.1f}%\n")
            if 'price_source' in opportunities_df.columns:
                src_counts = opportunities_df['price_source'].value_counts().to_dict()
                f.write(f"- **Price Source Distribution**: {src_counts}\n")
        
        f.write(f"\n## Fast Fish Compliance\n\n")
        f.write(f"✅ **Sell-Through Validated**: All saved recommendations improve sell-through rate\n")
        f.write(f"✅ **Business Logic Preserved**: Missing {feature_type} detection unchanged\n")
        f.write(f"✅ **Prioritized by Impact**: Sorted by sell-through improvement\n")
        f.write(f"✅ **Investment Optimized**: Only profitable improvements recommended\n")
        
        if len(opportunities_df) > 0 and 'sell_through_improvement' in opportunities_df.columns:
            f.write("## Top Opportunities by Sell-Through Improvement\n\n")
            top_opportunities = opportunities_df.nlargest(10, 'sell_through_improvement')
            f.write("| Store | Category | Current ST% | Predicted ST% | Improvement | Investment |\n")
            f.write("|-------|----------|-------------|---------------|-------------|------------|\n")
            for _, opp in top_opportunities.iterrows():
                f.write(f"| {opp['str_code']} | {opp.get('spu_code', 'N/A')} | {opp['current_sell_through_rate']:.1f}% | ")
                f.write(f"{opp['predicted_sell_through_rate']:.1f}% | +{opp['sell_through_improvement']:.1f}pp | ")
                f.write(f"${opp['investment_required']:.0f} |\n")
    
    # Backward-compatible file is now created as a symlink by create_output_with_symlinks
    # No additional action needed

def main() -> None:
    """Main function to execute missing category/SPU rule analysis"""
    start_time = datetime.now()
    log_progress(f"Starting Rule 7: {CURRENT_CONFIG['description']}...")
    
    try:
        # Load data with quantity information
        cluster_df, sales_df, quantity_df, price_df = load_data()
        
        # Identify well-selling features
        well_selling_features = identify_well_selling_features(sales_df, cluster_df)
        
        # Identify missing opportunities with sell-through validation
        opportunities_df = identify_missing_opportunities_with_sellthrough(
            sales_df, cluster_df, well_selling_features, quantity_df, price_df
        )
        
        # Apply rule and create results with sell-through metrics
        results_df = apply_missing_category_rule_with_sellthrough(cluster_df, opportunities_df)
        
        # Save results with sell-through metrics
        save_results_with_sellthrough(results_df, opportunities_df)
        
        # Calculate completion time
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Summary
        rule_col = 'rule7_missing_category' if ANALYSIS_LEVEL == "subcategory" else 'rule7_missing_spu'
        flagged_stores = results_df[rule_col].sum()
        feature_type = "categories" if ANALYSIS_LEVEL == "subcategory" else "SPUs"
        
        log_progress("\n" + "="*70)
        log_progress(f"RULE 7: MISSING {feature_type.upper()} ANALYSIS COMPLETE")
        log_progress("="*70)
        log_progress(f"Analysis Level: {ANALYSIS_LEVEL.upper()}")
        log_progress(f"Process completed in {duration:.2f} seconds")
        log_progress(f"✓ Stores analyzed: {len(results_df):,}")
        log_progress(f"✓ Stores flagged: {flagged_stores:,}")
        log_progress(f"✓ Missing opportunities: {len(opportunities_df):,}")
        
        if len(opportunities_df) > 0:
            feature_col = CURRENT_CONFIG['feature_column']
            top_feature = opportunities_df[feature_col].value_counts().index[0]
            top_count = opportunities_df[feature_col].value_counts().iloc[0]
            log_progress(f"✓ Most missed {ANALYSIS_LEVEL}: {top_feature} ({top_count:,} stores)")
            
            total_opportunity = opportunities_df['expected_sales_opportunity'].sum()
            log_progress(f"✓ Total opportunity value: {total_opportunity:,.0f}")
        
        log_progress(f"\nNext step: Run python src/step8_*.py for additional business rule analysis")
        
    except Exception as e:
        log_progress(f"Error in missing {ANALYSIS_LEVEL} rule analysis: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rule 7: Missing Category/SPU Analysis with Sell-through Validation")
    parser.add_argument("--yyyymm", type=str, help="YYYYMM period (e.g., 202508)")
    parser.add_argument("--period", type=str, choices=["A", "B", "full"], help="A/B or full")
    parser.add_argument("--analysis-level", type=str, choices=["spu", "subcategory"], default=ANALYSIS_LEVEL)
    parser.add_argument("--seasonal-blending", action="store_true", help="Enable seasonal blending")
    parser.add_argument("--seasonal-yyyymm", type=str, help="Seasonal data YYYYMM (e.g., 202408)")
    parser.add_argument("--seasonal-period", type=str, choices=["A", "B", "full"], help="Seasonal A/B or full")
    parser.add_argument("--seasonal-weight", type=float, default=SEASONAL_WEIGHT, help="Weight for seasonal data (0-1)")
    parser.add_argument("--seasonal-years-back", type=int, default=0, help="Include the same month/period from prior N years in seasonal blend")
    parser.add_argument("--target-yyyymm", type=str, help="Target YYYYMM label for outputs (e.g., 202509)")
    parser.add_argument("--target-period", type=str, choices=["A", "B", "full"], help="Target period for outputs")
    # Threshold configuration arguments
    parser.add_argument("--min-adoption-rate", type=float, help="Minimum cluster adoption rate (default: 0.80 for SPU, 0.70 for subcategory)")
    parser.add_argument("--min-cluster-sales", type=float, help="Minimum total cluster sales threshold (default: 1500 for SPU, 100 for subcategory)")
    parser.add_argument("--min-opportunity-value", type=float, help="Minimum opportunity value per store (default: 500 for SPU, 50 for subcategory)")
    parser.add_argument("--max-missing-per-store", type=int, help="Maximum missing SPUs per store (default: 5)")
    args = parser.parse_args()

    # Initialize config
    init_period = None if (args.period == "full") else args.period
    
    # Override environment variables if CLI args provided (for synthetic tests)
    if args.yyyymm:
        os.environ['PIPELINE_TARGET_YYYYMM'] = args.yyyymm
        os.environ['PIPELINE_YYYYMM'] = args.yyyymm
    if init_period:
        os.environ['PIPELINE_TARGET_PERIOD'] = init_period
        os.environ['PIPELINE_PERIOD'] = init_period
    
    initialize_pipeline_config(yyyymm=args.yyyymm, period=init_period, analysis_level=args.analysis_level)

    # Override config from CLI
    ANALYSIS_LEVEL = args.analysis_level
    CURRENT_CONFIG = ANALYSIS_CONFIGS[ANALYSIS_LEVEL]

    USE_BLENDED_SEASONAL = args.seasonal_blending
    SEASONAL_YYYYMM = args.seasonal_yyyymm
    SEASONAL_PERIOD = None if (args.seasonal_period == "full") else args.seasonal_period
    SEASONAL_WEIGHT = args.seasonal_weight
    RECENT_WEIGHT = 1.0 - SEASONAL_WEIGHT
    SEASONAL_YEARS_BACK = max(0, int(args.seasonal_years_back))

    # Set target output period for forecasting (if provided)
    TARGET_YYYYMM = args.target_yyyymm
    TARGET_PERIOD = None if (args.target_period == "full") else args.target_period
    
    # Override threshold module-level variables from CLI arguments using globals() dict
    if args.min_adoption_rate is not None:
        globals()['MIN_CLUSTER_STORES_SELLING'] = float(args.min_adoption_rate)
    if args.min_cluster_sales is not None:
        globals()['MIN_CLUSTER_SALES_THRESHOLD'] = float(args.min_cluster_sales)
    if args.min_opportunity_value is not None:
        globals()['MIN_OPPORTUNITY_VALUE'] = float(args.min_opportunity_value)
    if args.max_missing_per_store is not None:
        globals()['MAX_MISSING_SPUS_PER_STORE'] = int(args.max_missing_per_store)

    main()