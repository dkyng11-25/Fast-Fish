#!/usr/bin/env python3
"""
Step 3: Prepare Store-Product Matrices for Clustering (Year-over-Year Enhanced)

This step creates normalized matrices for both subcategory-level and SPU-level analysis
using comprehensive year-over-year data aggregation. It handles data filtering, 
normalization, and matrix creation for downstream clustering.

Enhanced to use all 12 periods from year-over-year analysis to create robust product matrices
that capture comprehensive store-product relationships across both current (2025) and 
historical (2024) seasonal windows for advanced comparative clustering.

Author: Data Pipeline
Date: 2025-07-21
"""

import pandas as pd
import numpy as np
import os
import sys
from typing import Tuple, List, Dict, Optional
from datetime import datetime, timedelta
from tqdm import tqdm
import warnings

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# Import dual output utility
from output_utils import create_output_with_symlinks

# Import configuration system
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import get_api_data_files, get_current_period, get_period_label, get_period_windows_config

def _step_half(yyyymm: str, period: Optional[str], steps: int) -> Tuple[str, str]:
    """Step half-month periods forward/backward by integer steps."""
    p = (period or 'A')
    year = int(yyyymm[:4])
    month = int(yyyymm[4:])
    # Map (year, month, period) -> absolute half-step index
    idx = year * 24 + (month - 1) * 2 + (0 if p == 'A' else 1)
    idx += steps
    # Map absolute half-step index back -> (year, month, period)
    new_year = idx // 24
    rem = idx % 24
    new_month = rem // 2 + 1
    new_period = 'A' if (rem % 2 == 0) else 'B'
    return f"{new_year:04d}{new_month:02d}", new_period

def last_n_half_months(n: int, end_yyyymm: str, end_period: Optional[str], inclusive: bool = True) -> List[Tuple[str, str]]:
    """Return last N half-months ending at (end_yyyymm, end_period) in chronological order."""
    start_offset = 0 if inclusive else 1
    items: List[Tuple[str, str]] = []
    for k in range(n):
        y, p = _step_half(end_yyyymm, end_period, steps=-(k + start_offset))
        items.append((y, p))
    items.reverse()  # chronological order
    return items

def next_n_half_months(n: int, start_yyyymm: str, start_period: Optional[str], inclusive: bool = True) -> List[Tuple[str, str]]:
    """Return next N half-months starting from (start_yyyymm, start_period)."""
    start_step = 0 if inclusive else 1
    items: List[Tuple[str, str]] = []
    for k in range(n):
        y, p = _step_half(start_yyyymm, start_period, steps=(k + start_step))
        items.append((y, p))
    return items

def get_year_over_year_periods() -> List[Tuple[str, str]]:
    """
    Get the year-over-year periods that were downloaded for seasonal analysis.

    Exposes helpers as attributes for backward compatibility:
      • get_year_over_year_periods.last_n_half_months
      • get_year_over_year_periods.next_n_half_months
      • get_year_over_year_periods._step_half

    Returns:
        List of (yyyymm, period) tuples matching our downloaded data
    """
    # Determine base (current) period from configuration
    curr_yyyymm, curr_period = get_current_period()

    # Load window configuration (with env overrides)
    win_cfg = get_period_windows_config()

    # Compute current window offsets
    if win_cfg.get('current_offsets'):
        current_offsets = list(win_cfg['current_offsets'])
    else:
        n = max(0, int(win_cfg.get('current_window_size', 6)))
        if n == 0:
            current_offsets = []
        elif n == 1:
            current_offsets = [0]
        else:
            # Include 0 and +1, then fill remaining with negatives descending
            neg_needed = n - 2
            negatives = [-(neg_needed - i) for i in range(neg_needed)]  # e.g., n=6 -> [-4,-3,-2,-1]
            current_offsets = negatives + [0, 1]

    # Compute YoY window offsets
    if win_cfg.get('yoy_offsets'):
        yoy_offsets = list(win_cfg['yoy_offsets'])
    else:
        m = max(0, int(win_cfg.get('yoy_window_size', 6)))
        lag = int(win_cfg.get('yoy_lag_half_steps', 24))
        shift = int(win_cfg.get('yoy_shift_after_lag', 3))
        yoy_offsets = [(-lag + shift + i) for i in range(m)]

    # Build windows
    current_window = [_step_half(curr_yyyymm, curr_period, steps=o) for o in current_offsets]
    yoy_window = [_step_half(curr_yyyymm, curr_period, steps=o) for o in yoy_offsets]

    # Log configuration and selections
    try:
        # log_progress is defined later in this module; safe to call at runtime
        labels_current = [f"{y}{p}" for y, p in current_window]
        labels_yoy = [f"{y}{p}" for y, p in yoy_window]
        log_progress("Period window configuration:")
        log_progress(f"  • Current offsets: {current_offsets} -> {labels_current}")
        log_progress(f"  • YoY offsets:     {yoy_offsets} -> {labels_yoy}")
    except Exception:
        pass

    return current_window + yoy_window

# Attach helpers to function object for code that may access nested helpers as attributes
get_year_over_year_periods.last_n_half_months = last_n_half_months  # type: ignore[attr-defined]
get_year_over_year_periods.next_n_half_months = next_n_half_months  # type: ignore[attr-defined]
get_year_over_year_periods._step_half = _step_half  # type: ignore[attr-defined]

def load_multi_period_data() -> Tuple[List[pd.DataFrame], List[pd.DataFrame]]:
    """
    Load year-over-year multi-period category and SPU data from all available periods.
    
    Returns:
        Tuple of (category_dataframes_list, spu_dataframes_list)
    """
    log_progress("🔍 Loading year-over-year multi-period data for comprehensive matrices...")
    
    periods = get_year_over_year_periods()
    log_progress(f"Loading data from {len(periods)} periods: {[f'{p[0]}{p[1]}' for p in periods]}")
    
    all_category_dfs = []
    all_spu_dfs = []
    
    for yyyymm, period in periods:
        period_label = f"{yyyymm}{period}"
        log_progress(f"Loading period {period_label}...")
        
        # Check for category data
        potential_category_paths = [
            f"data/api_data/complete_category_sales_{period_label}.csv",
            f"output/complete_category_sales_{period_label}.csv",
        ]
        
        # Check for SPU data  
        potential_spu_paths = [
            f"data/api_data/complete_spu_sales_{period_label}.csv",
            f"output/complete_spu_sales_{period_label}.csv",
        ]
        
        # Load category data if available
        category_df = None
        for path in potential_category_paths:
            if os.path.exists(path):
                try:
                    category_df = pd.read_csv(path, low_memory=False)
                    log_progress(f"  📊 Found category data: {len(category_df):,} records, {category_df['str_code'].nunique()} stores")
                    # Add period identifier
                    category_df['period'] = period_label
                    all_category_dfs.append(category_df)
                    break
                except Exception as e:
                    log_progress(f"  ❌ Error reading {path}: {str(e)}")
        
        # Load SPU data if available
        spu_df = None
        for path in potential_spu_paths:
            if os.path.exists(path):
                try:
                    spu_df = pd.read_csv(path, low_memory=False)
                    log_progress(f"  🛍️  Found SPU data: {len(spu_df):,} records, {spu_df['str_code'].nunique()} stores")
                    # Add period identifier
                    spu_df['period'] = period_label
                    all_spu_dfs.append(spu_df)
                    break
                except Exception as e:
                    log_progress(f"  ❌ Error reading {path}: {str(e)}")
    
    log_progress(f"✅ Loaded {len(all_category_dfs)} periods with category data")
    log_progress(f"✅ Loaded {len(all_spu_dfs)} periods with SPU data")
    
    return all_category_dfs, all_spu_dfs

# Get current period configuration (for backwards compatibility)
current_yyyymm, current_period = get_current_period()
api_files = get_api_data_files(current_yyyymm, current_period)

# Configuration - now supports multi-period aggregation
CATEGORY_FILE = api_files['category_sales']  # Fallback for single period
SPU_FILE = api_files['spu_sales']  # Fallback for single period
COORDINATES_FILE = "data/store_coordinates_extended.csv"

# Matrix creation parameters
MIN_STORES_PER_SUBCATEGORY = 5
MIN_SUBCATEGORIES_PER_STORE = 3
MIN_STORES_PER_SPU = 3
MIN_SPUS_PER_STORE = 10
MIN_SPU_SALES_AMOUNT = 1.0
MAX_SPU_COUNT = 1000  # Limit SPU matrix size for memory management

# Anomaly detection parameters
ANOMALY_LAT = 21.9178
ANOMALY_LON = 110.854

# Create necessary directories
os.makedirs("data", exist_ok=True)

def log_progress(message: str) -> None:
    """
    Log progress with timestamp and debug information.
    
    Args:
        message (str): Progress message to log
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_subcategory_data() -> pd.DataFrame:
    """
    Load and aggregate subcategory-level sales data from multiple periods.
    
    Returns:
        pd.DataFrame: Aggregated subcategory sales data
    """
    try:
        all_category_dfs, _ = load_multi_period_data()
        
        if not all_category_dfs:
            # Fallback to single period if multi-period fails
            log_progress("⚠️  No multi-period data found, falling back to single period...")
            return load_single_period_subcategory_data()
        
        # Combine all category data
        combined_df = pd.concat(all_category_dfs, ignore_index=True)
        
        # Normalize column names and dtypes
        combined_df['str_code'] = combined_df['str_code'].astype(str)
        value_col = 'sal_amt' if 'sal_amt' in combined_df.columns else ('sub_cate_sales_amt' if 'sub_cate_sales_amt' in combined_df.columns else None)
        if value_col is None:
            raise ValueError(f"Subcategory sales column not found. Expected one of ['sal_amt','sub_cate_sales_amt'], got: {list(combined_df.columns)}")
        
        # Aggregate by store and subcategory across all periods
        log_progress("🔄 Aggregating subcategory data across all periods...")
        aggregated_df = combined_df.groupby(['str_code', 'str_name', 'cate_name', 'sub_cate_name']).agg({
            value_col: 'sum',  # Total sales across all periods
            'period': 'count'  # Number of periods this combination appears in
        }).reset_index()
        
        # Rename columns for consistency
        aggregated_df = aggregated_df.rename(columns={'period': 'period_count', value_col: 'sal_amt'})
        
        log_progress(f"✅ Aggregated subcategory data: {len(aggregated_df):,} records from {aggregated_df['str_code'].nunique()} stores")
        log_progress(f"Subcategories found: {aggregated_df['sub_cate_name'].nunique()}")
        
        return aggregated_df
        
    except Exception as e:
        log_progress(f"❌ Error loading multi-period subcategory data: {str(e)}")
        log_progress("Falling back to single period data...")
        return load_single_period_subcategory_data()

def load_single_period_subcategory_data() -> pd.DataFrame:
    """
    Fallback method to load single-period subcategory data.
    
    Returns:
        pd.DataFrame: Single-period subcategory sales data
    """
    try:
        # Try multiple possible locations for the API data
        possible_paths = [
            CATEGORY_FILE,
            os.path.join("../data/api_data", os.path.basename(CATEGORY_FILE)),
            os.path.join("data/api_data", os.path.basename(CATEGORY_FILE)),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/api_data", os.path.basename(CATEGORY_FILE)),
            "data/api_data/complete_category_sales_202505A.csv"  # Use best period as fallback
        ]
        
        df = None
        loaded_path = None
        
        # Try each possible path
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    df = pd.read_csv(path, low_memory=False)
                    loaded_path = path
                    break
            except Exception:
                continue
                
        if df is None:
            raise FileNotFoundError(f"Could not find subcategory data file: {CATEGORY_FILE}")
        
        log_progress(f"Loaded single-period subcategory data from {loaded_path} with {len(df):,} rows and {df['str_code'].nunique()} stores")
        # Normalize columns
        df['str_code'] = df['str_code'].astype(str)
        if 'sal_amt' not in df.columns and 'sub_cate_sales_amt' in df.columns:
            df = df.rename(columns={'sub_cate_sales_amt': 'sal_amt'})
        return df
        
    except Exception as e:
        log_progress(f"Error loading subcategory data: {str(e)}")
        raise

def load_spu_data() -> Optional[pd.DataFrame]:
    """
    Load and aggregate SPU-level sales data from multiple periods.
    
    Returns:
        Optional[pd.DataFrame]: Aggregated SPU sales data or None if not available
    """
    try:
        _, all_spu_dfs = load_multi_period_data()
        
        if not all_spu_dfs:
            # Fallback to single period if multi-period fails
            log_progress("⚠️  No multi-period SPU data found, falling back to single period...")
            return load_single_period_spu_data()
        
        # Combine all SPU data
        combined_df = pd.concat(all_spu_dfs, ignore_index=True)
        # Normalize key dtypes
        combined_df['str_code'] = combined_df['str_code'].astype(str)
        combined_df['spu_code'] = combined_df['spu_code'].astype(str)
        
        # Aggregate by store and SPU across all periods
        log_progress("🔄 Aggregating SPU data across all periods...")
        aggregated_df = combined_df.groupby(['str_code', 'str_name', 'cate_name', 'sub_cate_name', 'spu_code']).agg({
            'spu_sales_amt': 'sum',  # Total sales across all periods
            'quantity': 'sum',  # Total quantity across all periods
            'period': 'count'  # Number of periods this combination appears in
        }).reset_index()
        
        # Calculate aggregated unit price
        aggregated_df['unit_price'] = aggregated_df['spu_sales_amt'] / aggregated_df['quantity'].replace(0, np.nan)
        aggregated_df['unit_price'] = aggregated_df['unit_price'].fillna(0)
        
        # Rename columns for consistency
        aggregated_df = aggregated_df.rename(columns={'period': 'period_count'})
        
        log_progress(f"✅ Aggregated SPU data: {len(aggregated_df):,} records from {aggregated_df['str_code'].nunique()} stores")
        log_progress(f"SPUs found: {aggregated_df['spu_code'].nunique()}")
        
        return aggregated_df
        
    except Exception as e:
        log_progress(f"❌ Error loading multi-period SPU data: {str(e)}")
        log_progress("Falling back to single period data...")
        return load_single_period_spu_data()

def load_single_period_spu_data() -> Optional[pd.DataFrame]:
    """
    Fallback method to load single-period SPU data.
    
    Returns:
        Optional[pd.DataFrame]: Single-period SPU sales data
    """
    try:
        # Try multiple possible locations for the SPU data
        possible_paths = [
            SPU_FILE,
            os.path.join("../data/api_data", os.path.basename(SPU_FILE)),
            os.path.join("data/api_data", os.path.basename(SPU_FILE)),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/api_data", os.path.basename(SPU_FILE)),
            "data/api_data/complete_spu_sales_202505A.csv"  # Use best period as fallback
        ]
        
        df = None
        loaded_path = None
        
        # Try each possible path
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    df = pd.read_csv(path, low_memory=False)
                    loaded_path = path
                    break
            except Exception:
                continue
        
        if df is None:
            log_progress("No SPU data file found - skipping SPU analysis")
            return None
        
        log_progress(f"Loaded single-period SPU data from {loaded_path} with {len(df):,} records from {df['str_code'].nunique()} stores, {df['spu_code'].nunique()} SPUs")
        # Normalize key dtypes
        df['str_code'] = df['str_code'].astype(str)
        df['spu_code'] = df['spu_code'].astype(str)
        return df
        
    except Exception as e:
        log_progress(f"Error loading SPU data: {str(e)}")
        return None

def get_memory_usage(df: pd.DataFrame) -> str:
    """
    Get memory usage of DataFrame in MB.
    
    Args:
        df: DataFrame to check
        
    Returns:
        String representation of memory usage
    """
    memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    return f"{memory_mb:.1f} MB"

def load_coordinates() -> pd.DataFrame:
    """
    Load store coordinates data.
    
    Returns:
        pd.DataFrame: Store coordinates
    
    Raises:
        FileNotFoundError: If coordinates file is missing
    """
    if not os.path.exists(COORDINATES_FILE):
        raise FileNotFoundError(
            f"Store coordinates file not found: {COORDINATES_FILE}\n"
            f"Run Step 2 first to generate store coordinates."
        )
    
    try:
        coords_df = pd.read_csv(COORDINATES_FILE)
        log_progress(f"Loaded coordinates for {len(coords_df)} stores")
        return coords_df
    except Exception as e:
        raise RuntimeError(
            f"Error loading coordinates from {COORDINATES_FILE}: {str(e)}\n"
            f"The file exists but cannot be read. Check file format and permissions."
        )

def identify_anomalous_stores(coords_df: pd.DataFrame) -> List[str]:
    """
    Identify stores with anomalous coordinates that might be data quality issues.
    
    Args:
        coords_df: Store coordinates DataFrame
        
    Returns:
        List of store codes with anomalous coordinates
    """
    if coords_df.empty:
        return []
        
    # Identify stores at the specific anomaly location
    anomaly_stores = coords_df[
        (abs(coords_df['latitude'] - ANOMALY_LAT) < 0.001) & 
        (abs(coords_df['longitude'] - ANOMALY_LON) < 0.001)
    ]['str_code'].tolist()
    
    log_progress(f"Identified {len(anomaly_stores)} stores with anomalous coordinates at ({ANOMALY_LAT}, {ANOMALY_LON})")
    
    return anomaly_stores

def filter_subcategory_data(df: pd.DataFrame, anomaly_stores: List[str]) -> pd.DataFrame:
    """
    Filter subcategory data based on prevalence and store criteria.
    
    Args:
        df (pd.DataFrame): Raw subcategory data
        anomaly_stores (List[str]): List of anomalous store codes to exclude
        
    Returns:
        pd.DataFrame: Filtered subcategory data
    """
    log_progress("=== PROCESSING SUBCATEGORY-LEVEL DATA ===")
    log_progress(f"Loaded subcategory data from {CATEGORY_FILE} with {len(df):,} rows and {df['str_code'].nunique()} stores")
    
    # Filter subcategories that appear in at least MIN_STORES_PER_SUBCATEGORY stores
    subcategory_counts = df['sub_cate_name'].value_counts()
    valid_subcategories = subcategory_counts[subcategory_counts >= MIN_STORES_PER_SUBCATEGORY].index
    df_filtered = df[df['sub_cate_name'].isin(valid_subcategories)]
    
    log_progress(f"Found {len(valid_subcategories)} subcategories that appear in at least {MIN_STORES_PER_SUBCATEGORY} stores")
    log_progress(f"Filtered subcategory data has {len(df_filtered):,} rows and {df_filtered['str_code'].nunique()} stores")
    
    # Filter stores that have at least MIN_SUBCATEGORIES_PER_STORE subcategories
    store_subcategory_counts = df_filtered['str_code'].value_counts()
    valid_stores = store_subcategory_counts[store_subcategory_counts >= MIN_SUBCATEGORIES_PER_STORE].index
    df_filtered = df_filtered[df_filtered['str_code'].isin(valid_stores)]
    
    log_progress(f"Found {len(valid_stores)} stores with at least {MIN_SUBCATEGORIES_PER_STORE} subcategories")
    log_progress(f"Filtered subcategory data has {len(df_filtered):,} rows")
    
    # Remove anomaly stores
    df_filtered = df_filtered[~df_filtered['str_code'].isin(anomaly_stores)]
    log_progress(f"Removed {len(anomaly_stores)} anomaly stores from the dataset")
    log_progress(f"Dataset now contains {df_filtered['str_code'].nunique()} stores")
    
    return df_filtered

def filter_spu_data(df: pd.DataFrame, anomaly_stores: List[str]) -> pd.DataFrame:
    """
    Filter SPU data based on prevalence and store criteria.
    
    Args:
        df (pd.DataFrame): Raw SPU data
        anomaly_stores (List[str]): List of anomalous store codes to exclude
        
    Returns:
        pd.DataFrame: Filtered SPU data
    """
    log_progress("Filtering SPUs based on prevalence and sales volume...")
    
    # Filter SPUs by prevalence (appear in at least MIN_STORES_PER_SPU stores)
    spu_store_counts = df['spu_code'].value_counts()
    spus_by_prevalence = spu_store_counts[spu_store_counts >= MIN_STORES_PER_SPU].index
    
    # Filter SPUs by sales volume (total sales across all stores)
    spu_sales_totals = df.groupby('spu_code')['spu_sales_amt'].sum()
    sales_threshold = spu_sales_totals.quantile(0.1)  # Bottom 10% threshold
    spus_by_sales = spu_sales_totals[spu_sales_totals >= sales_threshold].index
    
    # Combine both criteria
    valid_spus = set(spus_by_prevalence) & set(spus_by_sales)
    
    log_progress(f"SPU filtering results:")
    log_progress(f"  • SPUs by prevalence (≥{MIN_STORES_PER_SPU} stores): {len(spus_by_prevalence)}")
    log_progress(f"  • SPUs by sales volume (≥{sales_threshold:.0f}): {len(spus_by_sales)}")
    log_progress(f"  • Final SPUs to keep: {len(valid_spus)}")
    
    df_filtered = df[df['spu_code'].isin(valid_spus)]
    log_progress(f"Filtered SPU data has {len(df_filtered):,} rows from {df_filtered['str_code'].nunique()} stores")
    
    # Filter stores that have at least MIN_SPUS_PER_STORE SPUs
    store_spu_counts = df_filtered['str_code'].value_counts()
    valid_stores = store_spu_counts[store_spu_counts >= MIN_SPUS_PER_STORE].index
    df_filtered = df_filtered[df_filtered['str_code'].isin(valid_stores)]
    
    log_progress(f"Found {len(valid_stores)} stores with at least {MIN_SPUS_PER_STORE} SPUs")
    log_progress(f"Filtered SPU data has {len(df_filtered):,} rows")
    
    # Remove anomaly stores
    df_filtered = df_filtered[~df_filtered['str_code'].isin(anomaly_stores)]
    log_progress(f"Removed {len(anomaly_stores)} anomaly stores from the dataset")
    log_progress(f"Dataset now contains {df_filtered['str_code'].nunique()} stores")
    
    return df_filtered

def create_matrix(df: pd.DataFrame, index_col: str, columns_col: str, values_col: str, matrix_type: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create and normalize a pivot matrix from the data.
    
    Args:
        df (pd.DataFrame): Input data
        index_col (str): Column to use as index (stores)
        columns_col (str): Column to use as columns (products)
        values_col (str): Column to use as values (sales)
        matrix_type (str): Type of matrix for logging
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: Original and normalized matrices
    """
    unique_products = df[columns_col].nunique()
    unique_stores = df[index_col].nunique()
    
    # Check if we need to limit SPU count for memory management
    if matrix_type.startswith('spu') and unique_products > MAX_SPU_COUNT:
        log_progress(f"Estimated {matrix_type} matrix size: {unique_stores * unique_products / 1024**2:.1f} MB ({unique_stores} stores × {unique_products} SPUs)")
        log_progress(f"SPU count ({unique_products}) exceeds limit ({MAX_SPU_COUNT})")
        log_progress(f"Creating limited SPU matrix and category-aggregated matrix...")
        
        # Create limited SPU matrix
        log_progress("Creating SPU pivot matrix...")
        log_progress(f"Limiting to top {MAX_SPU_COUNT} SPUs by sales volume for memory management")
        
        # Get top SPUs by total sales
        top_spus = df.groupby(columns_col)[values_col].sum().nlargest(MAX_SPU_COUNT).index
        df_limited = df[df[columns_col].isin(top_spus)]
        log_progress(f"Filtered to {len(df_limited):,} records with top {MAX_SPU_COUNT} SPUs")
        
        log_progress("Creating pivot table (this may take a few minutes for large datasets)...")
        matrix = df_limited.pivot_table(index=index_col, columns=columns_col, values=values_col, fill_value=0, aggfunc='sum')
        matrix_type = f"{matrix_type}_limited"
        
        # Also create category-aggregated matrix
        create_category_aggregated_matrix(df, anomaly_stores=[])
        
    else:
        log_progress(f"Creating {matrix_type} pivot matrix...")
        log_progress("Creating pivot table (this may take a few minutes for large datasets)...")
        matrix = df.pivot_table(index=index_col, columns=columns_col, values=values_col, fill_value=0, aggfunc='sum')
    
    log_progress(f"Created {matrix_type} matrix with {matrix.shape[0]} stores and {matrix.shape[1]} {columns_col.replace('_', ' ')}s")
    
    # Normalize the matrix
    log_progress(f"Normalizing {matrix_type} matrix...")
    normalized_matrix = matrix.div(matrix.sum(axis=1), axis=0).fillna(0)
    log_progress(f"Normalized {matrix_type} matrix")
    
    return matrix, normalized_matrix

def create_category_aggregated_matrix(spu_df: pd.DataFrame, anomaly_stores: List[str]) -> None:
    """
    Create category-aggregated matrix from SPU data.
    
    Args:
        spu_df (pd.DataFrame): SPU sales data
        anomaly_stores (List[str]): List of anomalous store codes to exclude
    """
    log_progress("Creating category-aggregated SPU matrix...")
    
    # Remove anomaly stores
    spu_df_clean = spu_df[~spu_df['str_code'].isin(anomaly_stores)]
    
    # Aggregate SPU sales by category
    category_agg = spu_df_clean.groupby(['str_code', 'cate_name'])['spu_sales_amt'].sum().reset_index()
    
    # Create category matrix
    category_matrix = category_agg.pivot_table(index='str_code', columns='cate_name', values='spu_sales_amt', fill_value=0, aggfunc='sum')
    log_progress(f"Created category-aggregated matrix with {category_matrix.shape[0]} stores and {category_matrix.shape[1]} categories")
    
    # Normalize the matrix
    log_progress("Normalizing category-aggregated matrix...")
    normalized_category_matrix = category_matrix.div(category_matrix.sum(axis=1), axis=0).fillna(0)
    log_progress("Normalized category-aggregated matrix")
    
    # Save matrices
    save_matrix_files(category_matrix, normalized_category_matrix, "category_agg")

def save_matrix_files(original_matrix: pd.DataFrame, normalized_matrix: pd.DataFrame, matrix_type: str) -> None:
    """
    Save matrix files and related data.
    
    Args:
        original_matrix (pd.DataFrame): Original matrix
        normalized_matrix (pd.DataFrame): Normalized matrix
        matrix_type (str): Type of matrix for file naming
    """
    # Save matrices with DUAL OUTPUT PATTERN using utility
    # Get period label
    try:
        cur_yyyymm, cur_period = get_current_period()
        period_label = get_period_label(cur_yyyymm, cur_period) if cur_yyyymm and cur_period else ""
    except Exception:
        period_label = ""
    
    # Original matrix
    timestamped_original, period_original, generic_original = create_output_with_symlinks(
        original_matrix,
        f"data/store_{matrix_type}_matrix",
        period_label
    )
    log_progress(f"💾 Saved original {matrix_type} matrix:")
    log_progress(f"   Timestamped: {timestamped_original}")
    log_progress(f"   Generic symlink: {generic_original}")
    
    # Normalized matrix
    timestamped_normalized, period_normalized, generic_normalized = create_output_with_symlinks(
        normalized_matrix,
        f"data/normalized_{matrix_type}_matrix",
        period_label
    )
    log_progress(f"💾 Saved normalized {matrix_type} matrix:")
    log_progress(f"   Timestamped: {timestamped_normalized}")
    log_progress(f"   Generic symlink: {generic_normalized}")
    
    original_file = timestamped_original
    normalized_file = timestamped_normalized
    
    # Save store list
    store_list_file = f"data/{matrix_type}_store_list.txt"
    with open(store_list_file, 'w') as f:
        for store in original_matrix.index:
            f.write(f"{store}\n")
    log_progress(f"Saved {matrix_type} store list to {store_list_file}")
    
    # Save product list
    if matrix_type == "subcategory":
        product_list_file = "data/subcategory_list.txt"
    elif matrix_type == "category_agg":
        product_list_file = "data/category_list.txt"
    else:
        product_list_file = "data/category_list.txt"  # For SPU matrices, save category list
    
    with open(product_list_file, 'w') as f:
        for product in original_matrix.columns:
            f.write(f"{product}\n")
    log_progress(f"Saved {matrix_type.replace('_', ' ')} list to {product_list_file}")

def main() -> None:
    """Main function to prepare comprehensive multi-period clustering matrices."""
    start_time = datetime.now()
    log_progress("🚀 Starting Step 3: Enhanced Multi-Period Matrix Preparation...")
    
    # Log current configuration
    period_label = get_period_label(current_yyyymm, current_period)
    log_progress(f"Base period configuration: {period_label}")
    log_progress(f"Multi-period mode: Aggregating data from last 3 months for comprehensive matrices")
    log_progress(f"Fallback category file: {CATEGORY_FILE}")
    log_progress(f"Fallback SPU file: {SPU_FILE}")
    
    try:
        # Load coordinates and identify anomaly stores
        coords_df = load_coordinates()
        anomaly_stores = identify_anomalous_stores(coords_df)
        
        # Process subcategory-level data
        subcategory_df = load_subcategory_data()
        subcategory_filtered = filter_subcategory_data(subcategory_df, anomaly_stores)
        
        # Create subcategory matrix
        subcategory_matrix, normalized_subcategory_matrix = create_matrix(
            subcategory_filtered, 'str_code', 'sub_cate_name', 'sal_amt', 'subcategory'
        )
        
        # Save subcategory matrices
        save_matrix_files(subcategory_matrix, normalized_subcategory_matrix, "subcategory")
        
        # Save general store list (from subcategory analysis)
        with open("data/store_list.txt", 'w') as f:
            for store in subcategory_matrix.index:
                f.write(f"{store}\n")
        
        # Process SPU-level data if available
        log_progress("\n=== PROCESSING SPU-LEVEL DATA ===")
        spu_df = load_spu_data()
        
        if spu_df is not None:
            spu_filtered = filter_spu_data(spu_df, anomaly_stores)
            
            # Create SPU matrix (may be limited for memory management)
            spu_matrix, normalized_spu_matrix = create_matrix(
                spu_filtered, 'str_code', 'spu_code', 'spu_sales_amt', 'spu'
            )
            
            # Save SPU matrices
            save_matrix_files(spu_matrix, normalized_spu_matrix, "spu_limited" if spu_matrix.shape[1] <= MAX_SPU_COUNT else "spu")
            
            log_progress("✓ SPU-level matrices created successfully")
        else:
            log_progress("✗ SPU data not available - only subcategory-level analysis possible")
        
        # Final summary
        execution_time = (datetime.now() - start_time).total_seconds()
        log_progress("\n🎉 === ENHANCED STEP 3 COMPLETED SUCCESSFULLY ===")
        log_progress(f"Execution time: {execution_time:.1f} seconds")
        log_progress("✅ Multi-period product matrices created with comprehensive seasonal data")
        
        # List output files
        output_files = [
            "subcategory_list.txt", "normalized_subcategory_matrix.csv", "category_list.txt",
            "spu_limited_store_list.txt", "normalized_category_agg_matrix.csv", "store_subcategory_matrix.csv",
            "store_category_agg_matrix.csv", "store_spu_limited_matrix.csv", "category_agg_store_list.txt",
            "subcategory_store_list.txt", "store_list.txt", "normalized_spu_limited_matrix.csv"
        ]
        
        log_progress("\nOutput files created:")
        for filename in output_files:
            filepath = os.path.join("data", filename)
            if os.path.exists(filepath):
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                log_progress(f"  • {filename} ({size_mb:.1f} MB)")
        
        log_progress("\nNext step: Run python src/step6_cluster_analysis.py for clustering")
        
    except Exception as e:
        log_progress(f"Error in Step 3: {str(e)}")
        raise

if __name__ == "__main__":
    main() 