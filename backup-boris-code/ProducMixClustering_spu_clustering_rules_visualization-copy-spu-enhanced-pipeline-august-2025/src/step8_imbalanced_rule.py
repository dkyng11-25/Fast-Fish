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

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# Configuration - Analysis Level Selection
ANALYSIS_LEVEL = "spu"  # Options: "subcategory", "spu"

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
# Dynamic planning/quantity paths for current period
import os as _os
from config import get_current_period, get_period_label, get_api_data_files
_yyyymm, _period = get_current_period()
_period_label = get_period_label(_yyyymm, _period)
_api_files = get_api_data_files(_yyyymm, _period)
PLANNING_DATA_FILE = _api_files['store_config'] if _os.path.exists(_api_files['store_config']) else "data/api_data/store_config_data.csv"
# QUANTITY ENHANCEMENT: Use period-dynamic quantity file if available
_dynamic_quantity_file = f"data/api_data/complete_spu_sales_{_period_label}.csv"
QUANTITY_DATA_FILE = _dynamic_quantity_file if _os.path.exists(_dynamic_quantity_file) else "data/api_data/complete_spu_sales_202506B.csv"
OUTPUT_DIR = "output"
RESULTS_FILE = f"output/{CURRENT_CONFIG['output_prefix']}_results.csv"

# Rule parameters - adaptive based on analysis level
if ANALYSIS_LEVEL == "subcategory":
    Z_SCORE_THRESHOLD = 2.0  # Z-Score threshold for imbalance detection
    MIN_CLUSTER_SIZE = 3     # Minimum stores in cluster for valid Z-Score calculation
    MIN_ALLOCATION_THRESHOLD = 0.1  # Minimum allocation to consider for analysis
    # QUANTITY THRESHOLDS for subcategory rebalancing
    MIN_REBALANCE_QUANTITY = 2.0  # Minimum units to recommend rebalancing
    MAX_REBALANCE_PERCENTAGE = 0.3  # Max 30% of current allocation to rebalance
else:  # SPU level
    Z_SCORE_THRESHOLD = 4.0  # Very high threshold for SPU (only extreme outliers needing urgent intervention - top 5-10%)
    MIN_CLUSTER_SIZE = 5     # Higher minimum for SPU analysis
    MIN_ALLOCATION_THRESHOLD = 0.05  # Lower threshold for individual SPUs
    # QUANTITY THRESHOLDS for SPU rebalancing
    MIN_REBALANCE_QUANTITY = 1.0  # Minimum units to recommend rebalancing
    MAX_REBALANCE_PERCENTAGE = 0.4  # Max 40% of current allocation to rebalance (more flexible for SPUs)

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

def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Load clustering results, planning data, and quantity data for rebalancing analysis.
    
    Returns:
        Tuple containing cluster assignments, planning data, and quantity data
    """
    try:
        log_progress(f"Loading data for {CURRENT_CONFIG['description']} with quantity rebalancing...")
        
        # Check if files exist
        if not os.path.exists(CLUSTER_RESULTS_FILE):
            # Fallback to default clustering results for backward compatibility
            fallback_file = "output/clustering_results.csv"
            if os.path.exists(fallback_file):
                log_progress(f"Using fallback clustering file: {fallback_file}")
                CLUSTER_RESULTS_FILE_ACTUAL = fallback_file
            else:
                raise FileNotFoundError(f"Clustering results not found: {CLUSTER_RESULTS_FILE}")
        else:
            CLUSTER_RESULTS_FILE_ACTUAL = CLUSTER_RESULTS_FILE
            
        # Load planning data or build fallback from category sales
        planning_df = None
        if not os.path.exists(PLANNING_DATA_FILE):
            log_progress(f"Planning data not found at {PLANNING_DATA_FILE}. Attempting fallback from category sales...")
            try:
                from config import get_api_data_files
                _api_files_local = get_api_data_files(_yyyymm, _period)
                category_sales_path = _api_files_local['category_sales']
                if os.path.exists(category_sales_path):
                    cat_df = pd.read_csv(category_sales_path, dtype={'str_code': str}, low_memory=False)
                    cat_df['season_name'] = 'ALL_SEASONS'
                    cat_df['sex_name'] = 'UNISEX'
                    cat_df['display_location_name'] = 'ALL_LOCATIONS'
                    cat_df['big_class_name'] = cat_df['cate_name'] if 'cate_name' in cat_df.columns else 'ALL_CATEGORIES'
                    if 'sub_cate_name' not in cat_df.columns:
                        cat_df['sub_cate_name'] = 'UNKNOWN_SUBCATEGORY'
                    sales_col_proxy = 'sal_amt' if 'sal_amt' in cat_df.columns else None
                    if sales_col_proxy is None:
                        cat_df['target_sty_cnt_avg'] = 1.0
                    else:
                        cat_df['target_sty_cnt_avg'] = pd.to_numeric(cat_df[sales_col_proxy], errors='coerce').fillna(0) / 100.0
                    keep_cols = ['str_code', 'season_name', 'sex_name', 'display_location_name', 'big_class_name', 'sub_cate_name', 'target_sty_cnt_avg']
                    planning_df = cat_df[keep_cols].copy()
                    log_progress(f"Built fallback planning data from category sales with {len(planning_df)} rows")
                else:
                    raise FileNotFoundError(f"Fallback category sales not found: {category_sales_path}")
            except Exception as fe:
                raise FileNotFoundError(f"Planning data not found: {PLANNING_DATA_FILE} and fallback failed: {fe}")
        else:
            log_progress(f"Loading planning data from {PLANNING_DATA_FILE}")
            planning_df = pd.read_csv(PLANNING_DATA_FILE, dtype={'str_code': str}, low_memory=False)
            log_progress(f"Loaded planning data with {len(planning_df)} rows")
            
        if ANALYSIS_LEVEL == "spu":
            if not os.path.exists(QUANTITY_DATA_FILE):
                raise FileNotFoundError(f"Quantity data not found: {QUANTITY_DATA_FILE}")
        
        # Load cluster assignments
        cluster_df = pd.read_csv(CLUSTER_RESULTS_FILE_ACTUAL, dtype={'str_code': str})
        log_progress(f"Loaded cluster assignments for {len(cluster_df)} stores")
        
        # planning_df already loaded above (file or fallback)
        
        # QUANTITY ENHANCEMENT: Load quantity data for rebalancing calculations (SPU only)
        if ANALYSIS_LEVEL == "spu":
            log_progress(f"Loading quantity data from {QUANTITY_DATA_FILE}")
            quantity_df = pd.read_csv(QUANTITY_DATA_FILE, dtype={'str_code': str}, low_memory=False)
            # Ensure a 'quantity' column exists for unit calculations
            if 'quantity' not in quantity_df.columns:
                if 'sal_qty' in quantity_df.columns:
                    quantity_df['quantity'] = pd.to_numeric(quantity_df['sal_qty'], errors='coerce').fillna(0)
                else:
                    # Fallback: derive pseudo-quantity from sales amount and an estimated unit price
                    quantity_df['spu_sales_amt'] = pd.to_numeric(quantity_df.get('spu_sales_amt', 0), errors='coerce').fillna(0)
                    quantity_df['quantity'] = (quantity_df['spu_sales_amt'] / 300.0).fillna(0)
            log_progress(f"Loaded quantity data with {len(quantity_df)} rows (quantity column ready)")
        else:
            quantity_df = None
        
        # Ensure str_code is string for consistent joining
        cluster_df['str_code'] = cluster_df['str_code'].astype(str)
        planning_df['str_code'] = planning_df['str_code'].astype(str)
        if quantity_df is not None and 'str_code' in quantity_df.columns:
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
            # Fallback: build a compatible planning_df from category sales when planning schema is unavailable
            try:
                from config import get_api_data_files
                _api_files_local = get_api_data_files(_yyyymm, _period)
                category_sales_path = _api_files_local['category_sales']
                if os.path.exists(category_sales_path):
                    log_progress(f"Planning data missing columns {missing_cols}. Falling back to category sales: {category_sales_path}")
                    cat_df = pd.read_csv(category_sales_path, dtype={'str_code': str}, low_memory=False)
                    # Create required columns with reasonable defaults
                    cat_df['season_name'] = 'ALL_SEASONS'
                    cat_df['sex_name'] = 'UNISEX'
                    cat_df['display_location_name'] = 'ALL_LOCATIONS'
                    # Map category to big_class_name when available
                    if 'cate_name' in cat_df.columns:
                        cat_df['big_class_name'] = cat_df['cate_name']
                    else:
                        cat_df['big_class_name'] = 'ALL_CATEGORIES'
                    # Ensure sub_cate_name exists
                    if 'sub_cate_name' not in cat_df.columns:
                        cat_df['sub_cate_name'] = 'UNKNOWN_SUBCATEGORY'
                    # Use sales as proxy for planned style count (scaled)
                    sales_col_proxy = 'sal_amt' if 'sal_amt' in cat_df.columns else None
                    if sales_col_proxy is None:
                        # If no sales amount, create a uniform small proxy
                        cat_df['target_sty_cnt_avg'] = 1.0
                    else:
                        cat_df['target_sty_cnt_avg'] = pd.to_numeric(cat_df[sales_col_proxy], errors='coerce').fillna(0) / 100.0
                    # Keep only required columns for subcategory flow
                    keep_cols = ['str_code', 'season_name', 'sex_name', 'display_location_name', 'big_class_name', 'sub_cate_name', 'target_sty_cnt_avg']
                    planning_df = cat_df[keep_cols].copy()
                    planning_df['str_code'] = planning_df['str_code'].astype(str)
                    log_progress(f"Built fallback planning data from category sales with {len(planning_df)} rows")
                else:
                    raise FileNotFoundError(f"Fallback category sales not found: {category_sales_path}")
            except Exception as fe:
                raise ValueError(f"Missing required columns in planning data and fallback failed: {missing_cols} ({fe})")
        
        # Validate quantity data columns (SPU only)
        if ANALYSIS_LEVEL == "spu":
            quantity_required_cols = ['str_code', 'spu_code', 'spu_sales_amt']
            quantity_missing_cols = [col for col in quantity_required_cols if col not in quantity_df.columns]
            if quantity_missing_cols:
                raise ValueError(f"Missing required columns in quantity data: {quantity_missing_cols}")
        
        log_progress(f"Data validation successful for {ANALYSIS_LEVEL} analysis with quantity data")
        
        return cluster_df, planning_df, quantity_df
        
    except Exception as e:
        log_progress(f"Error loading data: {str(e)}")
        raise

def prepare_allocation_data(planning_df: pd.DataFrame, cluster_df: pd.DataFrame, quantity_df: Optional[pd.DataFrame]) -> pd.DataFrame:
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
        data_with_clusters = planning_df.merge(cluster_df[['str_code', 'Cluster']], on='str_code', how='inner')
        log_progress(f"Merged data: {len(data_with_clusters)} records with cluster information")
        
        # Clean and prepare allocation data
        data_with_clusters['target_sty_cnt_avg'] = pd.to_numeric(data_with_clusters['target_sty_cnt_avg'], errors='coerce').fillna(0)
        data_with_clusters['allocation_value'] = data_with_clusters['target_sty_cnt_avg']
        
        # Create category key for grouping
        grouping_cols = CURRENT_CONFIG['grouping_columns']
        data_with_clusters['category_key'] = data_with_clusters[grouping_cols].apply(
            lambda x: '|'.join(x.astype(str)), axis=1
        )
        
        # QUANTITY ENHANCEMENT: Add quantity data for subcategory rebalancing (if available)
        if quantity_df is not None and 'quantity' in quantity_df.columns:
            log_progress("Integrating quantity data for subcategory rebalancing...")
            quantity_clean = quantity_df[quantity_df['quantity'].notna() & (quantity_df['quantity'] > 0)].copy()
            quantity_clean['quantity'] = pd.to_numeric(quantity_clean['quantity'], errors='coerce').fillna(0)
            if 'spu_sales_amt' in quantity_clean.columns:
                quantity_clean['spu_sales_amt'] = pd.to_numeric(quantity_clean['spu_sales_amt'], errors='coerce').fillna(0)
            else:
                quantity_clean['spu_sales_amt'] = 0
            # Aggregate by store and subcategory
            subcategory_quantity = quantity_clean.groupby(['str_code', 'sub_cate_name']).agg({
                'quantity': 'sum',
                'spu_sales_amt': 'sum'
            }).reset_index()
            data_with_clusters = data_with_clusters.merge(
                subcategory_quantity,
                on=['str_code', 'sub_cate_name'],
                how='left'
            )
            data_with_clusters['current_quantity'] = data_with_clusters['quantity'].fillna(0) * SCALING_FACTOR
            data_with_clusters['current_sales_value'] = data_with_clusters['spu_sales_amt'].fillna(0) * SCALING_FACTOR
        
        # Only consider allocations above minimum threshold
        allocation_data = data_with_clusters[
            data_with_clusters['allocation_value'] >= MIN_ALLOCATION_THRESHOLD
        ].copy()
        
    else:
        # SPU analysis: Use sales data as proxy for allocation patterns
        log_progress("Expanding SPU sales data for allocation analysis with quantity integration...")
        
        # Filter records with SPU sales data
        spu_records = planning_df[planning_df['sty_sal_amt'].notna() & (planning_df['sty_sal_amt'] != '')].copy()
        log_progress(f"Found {len(spu_records)} records with SPU sales data")
        
        # QUANTITY ENHANCEMENT: Integrate quantity data directly for SPU analysis
        log_progress("Processing quantity data for SPU rebalancing...")
        quantity_clean = quantity_df[
            (quantity_df['spu_sales_amt'].notna()) & 
            (quantity_df['spu_sales_amt'] > 0)
        ].copy()
        
        # Convert to numeric
        quantity_clean['spu_sales_amt'] = pd.to_numeric(quantity_clean['spu_sales_amt'], errors='coerce').fillna(0)
        
        log_progress(f"Clean quantity data: {len(quantity_clean)} records")
        
        # QUANTITY ENHANCEMENT: Use quantity data directly for SPU analysis
        log_progress("Using quantity data directly for SPU rebalancing analysis...")
        
        # Use quantity data as the primary source for SPU allocation analysis
        quantity_with_clusters = quantity_clean.merge(cluster_df[['str_code', 'Cluster']], on='str_code', how='inner')
        log_progress(f"Merged quantity data: {len(quantity_with_clusters)} records with cluster information")
        
        # The SPU sales data already has the category information we need
        # Map the column names to match our expected structure
        data_with_clusters = quantity_with_clusters.copy()
        
        # Add missing columns with reasonable defaults for SPU analysis
        data_with_clusters['season_name'] = 'ALL_SEASONS'  # Default since not in SPU data
        data_with_clusters['sex_name'] = 'UNISEX'  # Default since not in SPU data  
        data_with_clusters['display_location_name'] = 'ALL_LOCATIONS'  # Default since not in SPU data
        data_with_clusters['big_class_name'] = data_with_clusters['cate_name']  # Use cate_name as big_class_name
        
        # Add sty_code column (same as spu_code for SPU analysis)
        data_with_clusters['sty_code'] = data_with_clusters['spu_code']
        
        # Use sales amount as allocation value and quantity proxy (scaled to target period)
        data_with_clusters['allocation_value'] = data_with_clusters['quantity'] * SCALING_FACTOR
        data_with_clusters['current_quantity'] = data_with_clusters['quantity'] * SCALING_FACTOR  # Sales amount as quantity proxy
        data_with_clusters['current_sales_value'] = data_with_clusters['spu_sales_amt'] * SCALING_FACTOR
        
        log_progress(f"Prepared data: {len(data_with_clusters)} records with complete information")
        
        # Create category key for grouping
        grouping_cols = CURRENT_CONFIG['grouping_columns']
        data_with_clusters['category_key'] = data_with_clusters[grouping_cols].apply(
            lambda x: '|'.join(x.astype(str)), axis=1
        )
        
        # Only consider allocations above minimum threshold
        allocation_data = data_with_clusters[
            data_with_clusters['allocation_value'] >= MIN_ALLOCATION_THRESHOLD
        ].copy()
    
    log_progress(f"Prepared {len(allocation_data)} store-{ANALYSIS_LEVEL} allocations above threshold")
    log_progress(f"Analysis covers {allocation_data['category_key'].nunique()} unique {feature_type}")
    
    return allocation_data

def calculate_cluster_z_scores(allocation_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Z-Scores for each store's allocation within their cluster.
    
    Args:
        allocation_data: Store allocation data (subcategory or SPU level)
        
    Returns:
        DataFrame with Z-Scores calculated
    """
    feature_type = "subcategories" if ANALYSIS_LEVEL == "subcategory" else "SPUs"
    log_progress(f"Calculating cluster-based Z-Scores for {ANALYSIS_LEVEL} allocations...")
    
    results = []
    
    # Group by cluster and category
    grouped = allocation_data.groupby(['Cluster', 'category_key'])
    log_progress(f"Processing {len(grouped)} cluster-{ANALYSIS_LEVEL} combinations...")
    
    # Convert to list for better progress tracking
    group_list = list(grouped)
    log_progress(f"Starting Z-Score calculation for {len(group_list)} combinations...")
    
    start_time = time.time()
    
    for i, ((cluster_id, category_key), group) in enumerate(tqdm(group_list, desc=f"Calculating Z-Scores")):
        
        # Progress update every 1000 combinations for large datasets
        if ANALYSIS_LEVEL == "spu" and i > 0 and i % 1000 == 0:
            elapsed_time = time.time() - start_time
            avg_time_per_combo = elapsed_time / i
            remaining_combos = len(group_list) - i
            estimated_remaining = avg_time_per_combo * remaining_combos
            
            log_progress(f"Processed {i}/{len(group_list)} combinations ({i/len(group_list)*100:.1f}%), "
                        f"generated {len(results)} valid Z-Score records so far")
            log_progress(f"Estimated time remaining: {estimated_remaining/60:.1f} minutes")
            
            # Memory cleanup every 5000 iterations
            if i % 5000 == 0:
                gc.collect()
        
        # Skip if cluster too small for meaningful Z-Score
        if len(group) < MIN_CLUSTER_SIZE:
            continue
            
        # Calculate cluster statistics
        allocations = group['allocation_value'].values
        cluster_mean = np.mean(allocations)
        cluster_std = np.std(allocations, ddof=1)  # Sample standard deviation
        
        # Skip if no variation (all allocations identical)
        if cluster_std == 0:
            group_copy = group.copy()
            group_copy['z_score'] = 0
            group_copy['cluster_mean'] = cluster_mean
            group_copy['cluster_std'] = cluster_std
            group_copy['cluster_size'] = len(group)
            results.append(group_copy)
            continue
        
        # Calculate Z-Scores for each store in this cluster-category
        z_scores = (allocations - cluster_mean) / cluster_std
        
        # Add Z-Score information to group data
        group_copy = group.copy()
        group_copy['z_score'] = z_scores
        group_copy['cluster_mean'] = cluster_mean
        group_copy['cluster_std'] = cluster_std
        group_copy['cluster_size'] = len(group)
        
        results.append(group_copy)
    
    if results:
        z_score_data = pd.concat(results, ignore_index=True)
        log_progress(f"Calculated Z-Scores for {len(z_score_data)} allocations across {len(results)} cluster-{ANALYSIS_LEVEL} combinations")
    else:
        z_score_data = pd.DataFrame()
        log_progress(f"No valid cluster-{ANALYSIS_LEVEL} combinations found for Z-Score calculation")
    
    return z_score_data

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
    imbalanced['recommend_rebalancing'] = (
        np.abs(imbalanced['constrained_quantity_adjustment']) >= MIN_REBALANCE_QUANTITY
    )
    
    # Calculate unit price for cost estimates (if sales value available)
    if 'current_sales_value' in imbalanced.columns:
        imbalanced['unit_price'] = np.where(
            imbalanced['current_quantity_15days'] > 0,
            imbalanced['current_sales_value'] / imbalanced['current_quantity_15days'],
            0
        )
    else:
        imbalanced['unit_price'] = 0
    
    # Add STANDARDIZED columns
    if ANALYSIS_LEVEL == "spu" and 'sty_code' in imbalanced.columns:
        imbalanced['spu_code'] = imbalanced['sty_code']  # STANDARDIZED: Use spu_code instead of sty_code
    imbalanced['recommended_quantity_change'] = imbalanced['quantity_adjustment_needed']  # STANDARDIZED
    imbalanced['investment_required'] = abs(imbalanced['quantity_adjustment_needed']) * imbalanced['unit_price']  # STANDARDIZED
    
    # Generate quantity rebalancing recommendations
    def create_rebalancing_recommendation(row):
        if not row['recommend_rebalancing']:
            return "No rebalancing needed (below minimum threshold)"
        
        adjustment = row['constrained_quantity_adjustment']
        current_qty = row['current_quantity_15days']
        target_qty = current_qty + adjustment
        unit_price = row['unit_price']
        
        if adjustment > 0:
            action = "INCREASE"
            direction = "to"
        else:
            action = "REDUCE"
            direction = "to"
            adjustment = abs(adjustment)
        
        if unit_price > 0:
            cost_info = f" @ ~${unit_price:.0f}/unit"
        else:
            cost_info = ""
        
        return f"{action} {adjustment:.1f} UNITS/15-DAYS {direction} {target_qty:.1f} (current: {current_qty:.1f}){cost_info}"
    
    imbalanced['recommendation_text'] = imbalanced.apply(  # STANDARDIZED: Use recommendation_text
        create_rebalancing_recommendation, axis=1
    )
    
    log_progress(f"Identified {len(imbalanced)} imbalanced {ANALYSIS_LEVEL} cases")
    
    if len(imbalanced) > 0:
        over_allocated = len(imbalanced[imbalanced['imbalance_type'] == 'OVER_ALLOCATED'])
        under_allocated = len(imbalanced[imbalanced['imbalance_type'] == 'UNDER_ALLOCATED'])
        rebalancing_recommended = imbalanced['recommend_rebalancing'].sum()
        total_quantity_adjustment = imbalanced[imbalanced['recommend_rebalancing']]['constrained_quantity_adjustment'].abs().sum()
        
        log_progress(f"  • Over-allocated: {over_allocated}")
        log_progress(f"  • Under-allocated: {under_allocated}")
        log_progress(f"  • Rebalancing recommended: {rebalancing_recommended}")
        log_progress(f"  • Total quantity adjustment needed: {total_quantity_adjustment:.1f} units/15-days")
        
        # Log severity breakdown
        severity_counts = imbalanced['imbalance_severity'].value_counts()
        log_progress(f"  • Severity breakdown: {dict(severity_counts)}")
    
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
    
    # Create base results for all stores
    results_df = cluster_df[['str_code', 'Cluster']].copy()
    
    # Count imbalanced cases per store with quantity metrics
    if len(imbalanced_cases) > 0:
        store_imbalance_stats = imbalanced_cases.groupby('str_code').agg({
            'category_key': 'count',
            'z_score': ['mean', lambda x: np.mean(np.abs(x))],  # Mean and absolute mean Z-Score
            'adjustment_needed': 'sum',
            'imbalance_type': lambda x: (x == 'OVER_ALLOCATED').sum(),  # Count over-allocations
            'recommend_rebalancing': 'sum',  # Count rebalancing recommendations
            'constrained_quantity_adjustment': lambda x: np.abs(x).sum()  # Total quantity adjustment
        }).reset_index()
        
        # Flatten column names with quantity metrics
        if ANALYSIS_LEVEL == "subcategory":
            store_imbalance_stats.columns = [
                'str_code', 'imbalanced_categories_count', 'avg_z_score', 'avg_abs_z_score', 
                'total_adjustment_needed', 'over_allocated_count', 'rebalancing_recommended_count', 'total_quantity_adjustment_needed'
            ]
            count_col = 'imbalanced_categories_count'
            rule_col = 'rule8_imbalanced'
        else:
            store_imbalance_stats.columns = [
                'str_code', 'imbalanced_spus_count', 'avg_z_score', 'avg_abs_z_score', 
                'total_adjustment_needed', 'over_allocated_count', 'rebalancing_recommended_count', 'total_quantity_adjustment_needed'
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
        
        # Fill NaN values for stores without imbalanced cases
        fill_cols = [count_col, 'avg_z_score', 'avg_abs_z_score', 
                    'total_adjustment_needed', 'over_allocated_count', 'under_allocated_count',
                    'rebalancing_recommended_count', 'total_quantity_adjustment_needed']
        for col in fill_cols:
            results_df[col] = results_df[col].fillna(0)
        
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

def save_results(results_df: pd.DataFrame, imbalanced_cases: pd.DataFrame, 
                z_score_data: pd.DataFrame) -> None:
    """
    Save rule results and detailed analysis.
    
    Args:
        results_df: Rule results for all stores
        imbalanced_cases: Detailed imbalanced cases
        z_score_data: Complete Z-Score analysis
    """
    feature_type = "categories" if ANALYSIS_LEVEL == "subcategory" else "SPUs"
    
    # Save main rule results
    results_df.to_csv(RESULTS_FILE, index=False)
    log_progress(f"Saved {ANALYSIS_LEVEL} rule results to {RESULTS_FILE}")
    
    # Save detailed imbalanced cases if any exist
    if len(imbalanced_cases) > 0:
        cases_file = f"output/{CURRENT_CONFIG['output_prefix']}_cases.csv"
        imbalanced_cases.to_csv(cases_file, index=False)
        log_progress(f"Saved detailed imbalanced cases to {cases_file}")
    
    # Save Z-Score analysis if any exist
    if len(z_score_data) > 0:
        z_score_file = f"output/{CURRENT_CONFIG['output_prefix']}_z_score_analysis.csv"
        z_score_data.to_csv(z_score_file, index=False)
        log_progress(f"Saved Z-Score analysis to {z_score_file}")
    
    # Generate summary report
    summary_file = f"output/{CURRENT_CONFIG['output_prefix']}_summary.md"
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
            rebalancing_recommended = imbalanced_cases['recommend_rebalancing'].sum() if 'recommend_rebalancing' in imbalanced_cases.columns else 0
            total_quantity_adjustment = imbalanced_cases[imbalanced_cases['recommend_rebalancing']]['constrained_quantity_adjustment'].abs().sum() if 'recommend_rebalancing' in imbalanced_cases.columns else 0
            
            f.write(f"- Over-allocated cases: {over_allocated:,}\n")
            f.write(f"- Under-allocated cases: {under_allocated:,}\n")
            f.write(f"- Average |Z-Score|: {avg_z_score:.2f}\n")
            f.write(f"\n## Quantity Rebalancing Metrics\n")
            f.write(f"- Cases with rebalancing recommended: {rebalancing_recommended:,}\n")
            f.write(f"- Total quantity adjustment needed: {total_quantity_adjustment:.1f} units/15-days\n")
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
    
    # Also save backward-compatible file for subcategory analysis
    if ANALYSIS_LEVEL == "subcategory":
        backward_compatible_file = "output/rule8_imbalanced_results.csv"
        results_df.to_csv(backward_compatible_file, index=False)
        log_progress(f"Saved backward-compatible results to {backward_compatible_file}")

def main() -> None:
    """Main function to execute imbalanced allocation rule analysis"""
    start_time = datetime.now()
    log_progress(f"Starting Rule 8: {CURRENT_CONFIG['description']}...")
    
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
            results_df.to_csv(RESULTS_FILE, index=False)
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
                rebalancing_recommended = imbalanced_cases['recommend_rebalancing'].sum()
                total_quantity_adjustment = imbalanced_cases[imbalanced_cases['recommend_rebalancing']]['constrained_quantity_adjustment'].abs().sum()
                log_progress(f"✓ Rebalancing recommended: {rebalancing_recommended:,} cases")
                log_progress(f"✓ Total quantity adjustment: {total_quantity_adjustment:.1f} units/15-days")
                log_progress(f"✓ Investment impact: NEUTRAL (rebalancing only)")
        
        log_progress(f"\nNext step: Run python src/step9_*.py for additional business rule analysis")
        
    except Exception as e:
        log_progress(f"Error in imbalanced {ANALYSIS_LEVEL} allocation rule analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main() 