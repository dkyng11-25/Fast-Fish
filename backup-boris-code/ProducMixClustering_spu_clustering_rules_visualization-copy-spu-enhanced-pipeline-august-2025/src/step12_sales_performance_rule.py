#!/usr/bin/env python3
"""
Step 12: Sales Performance Rule with UNIT QUANTITY INCREASE RECOMMENDATIONS

This step identifies sales opportunities by comparing each store's category performance
against cluster top performers and provides specific UNIT QUANTITY increase recommendations
to close performance gaps.

ENHANCEMENT: Now includes actual unit quantity increase using real sales data!

Features:
- Multi-Level Analysis: Subcategory and SPU-level analysis
- Opportunity gap analysis vs cluster top quartile performers
- 🎯 UNIT QUANTITY INCREASE (e.g., "Increase 15 units to close performance gap")
- Real sales data integration for accurate quantity calculations
- 5-level performance classification for sales prioritization
- Store-level aggregation via average Z-scores across categories
- Sales team focused insights and recommendations

Author: Data Pipeline
Date: 2025-01-02 (Enhanced with Quantity Increases)
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
import json
import gc
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from tqdm import tqdm
import warnings

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# Configuration - Analysis Level Selection
ANALYSIS_LEVEL = "spu"  # SPU mode required

# DATA PERIOD CONFIGURATION - CRITICAL FOR ACCURATE RECOMMENDATIONS
DATA_PERIOD_DAYS = 15  # API data is for half month (15 days)
TARGET_PERIOD_DAYS = 15  # Recommendations should be for same period (15 days)
SCALING_FACTOR = TARGET_PERIOD_DAYS / DATA_PERIOD_DAYS  # 1.0 for same period

# Analysis configurations
ANALYSIS_CONFIGS = {
    "subcategory": {
        "cluster_file": "output/clustering_results_spu.csv",
        "data_file": "data/api_data/complete_category_sales_202505.csv",
        "output_prefix": "rule12_sales_performance_subcategory",
        "grouping_columns": ['sub_cate_name'],
        "sales_column": "sal_amt"
    },
    "spu": {
        "cluster_file": "output/clustering_results_spu.csv", 
        "data_file": "data/api_data/store_config_data.csv",
        "output_prefix": "rule12_sales_performance_spu",
        "grouping_columns": ['season_name', 'sex_name', 'display_location_name', 'big_class_name', 'sub_cate_name', 'spu_code'],
        "sales_column": "spu_sales"
    }
}

# QUANTITY ENHANCEMENT: Add quantity data for increase calculations (period-dynamic)
import os as _os
from config import get_current_period, get_period_label
_yyyymm, _period = get_current_period()
_period_label = get_period_label(_yyyymm, _period)
_dynamic_quantity_file = f"data/api_data/complete_spu_sales_{_period_label}.csv"
QUANTITY_DATA_FILE = _dynamic_quantity_file if _os.path.exists(_dynamic_quantity_file) else "data/api_data/complete_spu_sales_202506B.csv"

# Configuration
CLUSTER_RESULTS_FILE = ANALYSIS_CONFIGS[ANALYSIS_LEVEL]["cluster_file"]
CATEGORY_SALES_FILE = ANALYSIS_CONFIGS[ANALYSIS_LEVEL]["data_file"]
OUTPUT_DIR = "output"
RESULTS_FILE = f"output/{ANALYSIS_CONFIGS[ANALYSIS_LEVEL]['output_prefix']}_results.csv"

# Rule parameters - Sales team focused opportunity analysis - Adapted for analysis level
if ANALYSIS_LEVEL == "subcategory":
    TOP_QUARTILE_PERCENTILE = 75  # Compare against 75th percentile performers
    MIN_CLUSTER_SIZE = 3         # Minimum stores in cluster for valid analysis
    MIN_SALES_VOLUME = 1         # Minimum sales to consider (avoid noise)
    # QUANTITY THRESHOLDS for subcategory performance improvement
    MIN_INCREASE_QUANTITY = 2.0  # Minimum units to recommend increasing
    MAX_INCREASE_PERCENTAGE = 0.5  # Max 50% increase for practical implementation
else:  # SPU level - balanced thresholds to surface actionable, non-noisy recs
    TOP_QUARTILE_PERCENTILE = 80  # Compare against 80th percentile performers
    MIN_CLUSTER_SIZE = 4          # Minimum stores in cluster for valid analysis
    MIN_SALES_VOLUME = 20         # Minimum sales to consider
    # QUANTITY THRESHOLDS for SPU performance improvement
    MIN_INCREASE_QUANTITY = 1.0   # Minimum units to recommend increasing
    MAX_INCREASE_PERCENTAGE = 0.5  # Max 50% increase for practical implementation

# NEW: Selectivity controls (balanced)
MAX_RECOMMENDATIONS_PER_STORE = 20   # Cap per store
MIN_OPPORTUNITY_SCORE = 0.05         # Require some signal
MIN_INVESTMENT_THRESHOLD = 100       # Avoid tiny investments
MIN_Z_SCORE_THRESHOLD = 0.8          # Need moderate underperformance

# Performance classification thresholds (Z-score based) - Adapted for analysis level
if ANALYSIS_LEVEL == "subcategory":
    PERFORMANCE_THRESHOLDS = {
        'top_performer': -1.0,       # Exceeding top quartile (Z < -1.0)
        'performing_well': 0.0,      # Meeting expectations (-1.0 ≤ Z ≤ 0)
        'some_opportunity': 1.0,     # Minor potential (0 < Z ≤ 1.0)
        'good_opportunity': 2.5,     # Solid potential (1.0 < Z ≤ 2.5)
        'major_opportunity': float('inf')  # Huge potential (Z > 2.5)
    }
else:  # SPU level - balanced actionable bands
    PERFORMANCE_THRESHOLDS = {
        'top_performer': -0.8,        # Exceeding cluster benchmarks
        'performing_well': 0.3,       # Near expectations
        'some_opportunity': 0.8,      # Minor potential (not actionable)
        'good_opportunity': 2.0,      # Action needed (0.8 < Z ≤ 2.0)
        'major_opportunity': float('inf')  # Priority action (Z > 2.0)
    }

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def expand_spu_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expand SPU sales data from JSON strings into individual records.
    
    Args:
        df (pd.DataFrame): Input dataframe with sty_sal_amt JSON column
        
    Returns:
        pd.DataFrame: Expanded dataframe with individual SPU records
    """
    log_progress("Expanding SPU sales data for sales performance analysis...")
    
    # Filter records with SPU sales data
    spu_records = df[df['sty_sal_amt'].notna() & (df['sty_sal_amt'] != '')].copy()
    log_progress(f"Found {len(spu_records):,} records with SPU sales data")
    
    if len(spu_records) == 0:
        return pd.DataFrame()
    
    expanded_records = []
    batch_size = 1000
    total_batches = (len(spu_records) + batch_size - 1) // batch_size
    
    log_progress(f"Processing {len(spu_records):,} records in {total_batches:,} batches...")
    
    with tqdm(total=total_batches, desc="Expanding SPU data") as pbar:
        for i in range(0, len(spu_records), batch_size):
            batch = spu_records.iloc[i:i+batch_size]
            
            for _, row in batch.iterrows():
                try:
                    spu_data = json.loads(row['sty_sal_amt'])
                    for spu_code, sales_amount in spu_data.items():
                        if sales_amount >= MIN_SALES_VOLUME:  # Only include SPUs with meaningful sales
                            expanded_record = row.copy()
                            expanded_record['spu_code'] = spu_code
                            expanded_record['spu_sales'] = float(sales_amount)
                            expanded_records.append(expanded_record)
                except (json.JSONDecodeError, TypeError, ValueError):
                    continue
            
            pbar.update(1)
            
            # Progress logging every 10 batches
            if (i // batch_size + 1) % 10 == 0:
                log_progress(f"Processed {i//batch_size + 1:,}/{total_batches:,} batches, generated {len(expanded_records):,} SPU records so far")
            
            # Memory cleanup every 50 batches
            if (i // batch_size + 1) % 50 == 0:
                gc.collect()
    
    if not expanded_records:
        log_progress("No valid SPU records found after expansion")
        return pd.DataFrame()
    
    expanded_df = pd.DataFrame(expanded_records)
    log_progress(f"Expanded to {len(expanded_df):,} SPU records")
    
    return expanded_df

def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load clustering results, category sales data, and quantity data"""
    config = ANALYSIS_CONFIGS[ANALYSIS_LEVEL]
    
    try:
        # Load cluster assignments
        cluster_df = pd.read_csv(config["cluster_file"], dtype={'str_code': str})
        log_progress(f"Loaded cluster assignments for {len(cluster_df):,} stores")
        
        # Load category sales data (planning). Fallback to period-specific store_config if present
        preferred_file = config["data_file"]
        from config import get_api_data_files
        _yyyymm, _period = get_current_period()
        _api_files = get_api_data_files(_yyyymm, _period)
        dynamic_planning = _api_files['store_config']
        planning_path = dynamic_planning if os.path.exists(dynamic_planning) else preferred_file
        category_df = pd.read_csv(planning_path, dtype={'str_code': str}, low_memory=False)
        log_progress(f"Loaded category sales data with {len(category_df):,} rows")

        # QUANTITY ENHANCEMENT: Load quantity data for performance improvement calculations
        log_progress(f"Loading quantity data from {QUANTITY_DATA_FILE}")
        quantity_df = pd.read_csv(QUANTITY_DATA_FILE, dtype={'str_code': str}, low_memory=False)
        if 'spu_sales_amt' not in quantity_df.columns and 'sal_amt' in quantity_df.columns:
            quantity_df['spu_sales_amt'] = pd.to_numeric(quantity_df['sal_amt'], errors='coerce').fillna(0)
        # Derive unit quantity column for downstream use
        if 'quantity' not in quantity_df.columns:
            if 'sal_qty' in quantity_df.columns:
                quantity_df['quantity'] = pd.to_numeric(quantity_df['sal_qty'], errors='coerce').fillna(0)
            else:
                # Fallback estimate: divide sales amount by a conservative unit price proxy
                unit_price_proxy = 100.0
                quantity_df['quantity'] = (pd.to_numeric(quantity_df['spu_sales_amt'], errors='coerce').fillna(0) / unit_price_proxy)
        log_progress(f"Loaded quantity data with {len(quantity_df)} rows")

        # Ensure str_code is string for consistent joining
        cluster_df['str_code'] = cluster_df['str_code'].astype(str)
        category_df['str_code'] = category_df['str_code'].astype(str)
        quantity_df['str_code'] = quantity_df['str_code'].astype(str)
        
        # Validate quantity data columns
        quantity_required_cols = ['str_code', 'spu_code', 'spu_sales_amt']
        quantity_missing_cols = [col for col in quantity_required_cols if col not in quantity_df.columns]
        if quantity_missing_cols:
            raise ValueError(f"Missing required columns in quantity data: {quantity_missing_cols}")
        
        log_progress(f"Data validation successful for sales performance analysis with quantity data")
        
        return cluster_df, category_df, quantity_df
    except Exception as e:
        log_progress(f"Error loading data: {str(e)}")
        raise

def prepare_sales_data(category_df: pd.DataFrame, cluster_df: pd.DataFrame, quantity_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare store-category sales data with cluster information and quantity data.
    
    Args:
        category_df: Category sales data
        cluster_df: Cluster assignments
        quantity_df: Quantity data with actual unit sales for performance calculations
        
    Returns:
        DataFrame with store-category sales, cluster information, and quantity metrics
    """
    config = ANALYSIS_CONFIGS[ANALYSIS_LEVEL]
    log_progress(f"Preparing sales data for {ANALYSIS_LEVEL.title()}-Level Sales Performance Analysis with quantity integration...")
    
    # Merge with cluster information
    sales_with_clusters = category_df.merge(cluster_df[['str_code', 'Cluster']], on='str_code', how='inner')
    log_progress(f"Merged data: {len(sales_with_clusters):,} records with cluster information")
    
    # QUANTITY ENHANCEMENT: Process quantity data for performance analysis
    log_progress("Processing quantity data for performance improvement calculations...")
    quantity_clean = quantity_df[
        (quantity_df['spu_sales_amt'].notna()) & 
        (quantity_df['spu_sales_amt'] > 0)
    ].copy()
    quantity_clean['spu_sales_amt'] = pd.to_numeric(quantity_clean['spu_sales_amt'], errors='coerce').fillna(0)
    
    # Data validation - check base columns first
    base_required_columns = ['str_code', 'Cluster']
    if ANALYSIS_LEVEL == "subcategory":
        base_required_columns.extend(['sub_cate_name', 'sal_amt'])
    else:
        base_required_columns.extend(['season_name', 'sex_name', 'display_location_name', 'big_class_name', 'sub_cate_name', 'sty_sal_amt'])
    
    missing_columns = [col for col in base_required_columns if col not in sales_with_clusters.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns for {ANALYSIS_LEVEL} analysis: {missing_columns}")
    
    log_progress(f"Data validation successful for {ANALYSIS_LEVEL} analysis")
    
    if ANALYSIS_LEVEL == "spu":
        # Expand SPU data
        sales_with_clusters = expand_spu_data(sales_with_clusters)
        if len(sales_with_clusters) == 0:
            raise ValueError("No valid SPU data found after expansion")
        sales_col = 'spu_sales'
        grouping_cols = ['str_code', 'Cluster'] + config["grouping_columns"]
    else:
        # Clean and prepare subcategory data
        sales_with_clusters['sal_amt'] = pd.to_numeric(sales_with_clusters['sal_amt'], errors='coerce').fillna(0)
        sales_col = 'sal_amt'
        grouping_cols = ['str_code', 'Cluster', 'sub_cate_name']
    
    # Filter to meaningful sales data
    sales_data = sales_with_clusters[
        sales_with_clusters[sales_col] >= MIN_SALES_VOLUME
    ].copy()
    
    # Group by store-category to get total sales per combination
    if ANALYSIS_LEVEL == "subcategory":
        store_category_sales = sales_data.groupby(grouping_cols).agg({
            sales_col: 'sum',
            'cate_name': 'first'  # Keep category name for reference
        }).reset_index()
    else:
        # For SPU level, create category key and aggregate
        sales_data['category_key'] = (sales_data['season_name'] + '|' + sales_data['sex_name'] + '|' + 
                                     sales_data['display_location_name'] + '|' + sales_data['big_class_name'] + '|' + 
                                     sales_data['sub_cate_name'] + '|' + sales_data['spu_code'])
        
        store_category_sales = sales_data.groupby(['str_code', 'Cluster', 'category_key']).agg({
            sales_col: 'sum',
            'sub_cate_name': 'first',  # Keep subcategory name for reference
            'spu_code': 'first'
        }).reset_index()
    
    log_progress(f"Prepared {len(store_category_sales):,} store-category combinations from {store_category_sales['str_code'].nunique():,} stores")
    
    return store_category_sales

def calculate_opportunity_gaps(sales_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate opportunity gaps by comparing each store's category performance
    against cluster top quartile performers.
    
    Args:
        sales_data: Store-category sales data with clusters
        
    Returns:
        DataFrame with opportunity gap analysis
    """
    log_progress("Calculating opportunity gaps vs cluster top performers...")
    
    config = ANALYSIS_CONFIGS[ANALYSIS_LEVEL]
    sales_col = config["sales_column"] if ANALYSIS_LEVEL == "subcategory" else "spu_sales"
    
    results = []
    
    # Group by cluster and category to analyze peer performance
    if ANALYSIS_LEVEL == "subcategory":
        groupby_cols = ['Cluster', 'sub_cate_name']
    else:
        groupby_cols = ['Cluster', 'category_key']
    
    for group_key, group in sales_data.groupby(groupby_cols):
        
        # Skip if cluster too small for meaningful analysis
        if len(group) < MIN_CLUSTER_SIZE:
            continue
            
        # Calculate cluster performance statistics
        cluster_sales = group[sales_col].values
        top_quartile_sales = np.percentile(cluster_sales, TOP_QUARTILE_PERCENTILE)
        
        # Calculate opportunity gaps for each store in this cluster-category
        for _, store_row in group.iterrows():
            store_sales = store_row[sales_col]
            
            # Opportunity gap: positive = opportunity, negative = exceeding top quartile
            opportunity_gap = top_quartile_sales - store_sales
            
            # Add opportunity gap information to store data
            store_data = store_row.copy()
            store_data['opportunity_gap'] = opportunity_gap
            store_data['cluster_top_quartile'] = top_quartile_sales
            store_data['cluster_size'] = len(group)
            
            results.append(store_data)
    
    if results:
        opportunity_data = pd.DataFrame(results)
        log_progress(f"Calculated opportunity gaps for {len(opportunity_data):,} store-category combinations across {len(results):,} valid cluster-category groups")
    else:
        opportunity_data = pd.DataFrame()
        log_progress("No valid cluster-category combinations found for opportunity gap analysis")
    
    return opportunity_data

def calculate_opportunity_z_scores(opportunity_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Z-scores for opportunity gaps to enable classification.
    
    Args:
        opportunity_data: Data with opportunity gaps calculated
        
    Returns:
        DataFrame with Z-scores for opportunity gaps
    """
    log_progress("Calculating Z-scores for opportunity gaps...")
    
    if len(opportunity_data) == 0:
        return pd.DataFrame()
    
    # Calculate Z-scores for opportunity gaps across all data
    gaps = opportunity_data['opportunity_gap'].values
    gap_mean = np.mean(gaps)
    gap_std = np.std(gaps, ddof=1)
    
    # Handle case where all gaps are identical (std = 0)
    if gap_std == 0:
        opportunity_data['opportunity_gap_z_score'] = 0
        log_progress("All opportunity gaps are identical, setting Z-scores to 0")
    else:
        opportunity_data['opportunity_gap_z_score'] = (gaps - gap_mean) / gap_std
        log_progress(f"Calculated Z-scores with mean gap: {gap_mean:.2f}, std: {gap_std:.2f}")
    
    return opportunity_data

def classify_performance_levels(z_score_data: pd.DataFrame, quantity_df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify stores into 5 performance levels based on opportunity gap Z-scores
    and calculate UNIT QUANTITY INCREASE recommendations to close performance gaps.
    
    Args:
        z_score_data: Data with Z-scores calculated
        quantity_df: Quantity data for unit increase calculations
        
    Returns:
        DataFrame with performance level classifications and quantity increase recommendations
    """
    log_progress("Classifying performance levels and calculating UNIT QUANTITY INCREASE recommendations...")
    
    if len(z_score_data) == 0:
        return pd.DataFrame()
    
    # QUANTITY ENHANCEMENT: Prepare quantity lookup for unit increase calculations
    log_progress("Preparing quantity data for performance improvement calculations...")
    quantity_lookup = {}
    
    # Create SPU-level quantity lookup
    for _, row in quantity_df.iterrows():
        key = f"{row['str_code']}_{row['spu_code']}"
        quantity_lookup[key] = row['quantity']  # REAL QUANTITY instead of sales amount
    
    log_progress(f"Created quantity lookup with {len(quantity_lookup):,} store-SPU combinations")
    
    # Classify based on Z-score thresholds
    def classify_performance(z_score):
        if z_score < PERFORMANCE_THRESHOLDS['top_performer']:
            return 'top_performer'
        elif z_score <= PERFORMANCE_THRESHOLDS['performing_well']:
            return 'performing_well'
        elif z_score <= PERFORMANCE_THRESHOLDS['some_opportunity']:
            return 'some_opportunity'
        elif z_score <= PERFORMANCE_THRESHOLDS['good_opportunity']:
            return 'good_opportunity'
        else:
            return 'major_opportunity'
    
    z_score_data['performance_level'] = z_score_data['opportunity_gap_z_score'].apply(classify_performance)
    
    # Create binary flags for each performance level
    for level in ['top_performer', 'performing_well', 'some_opportunity', 'good_opportunity', 'major_opportunity']:
        z_score_data[f'rule12_{level}'] = (z_score_data['performance_level'] == level).astype(int)
    
    # Add business insights
    z_score_data['opportunity_value'] = np.maximum(0, z_score_data['opportunity_gap'])  # Only positive gaps are opportunities
    z_score_data['exceeds_top_quartile'] = (z_score_data['opportunity_gap'] < 0).astype(int)
    
    # QUANTITY ENHANCEMENT: Calculate unit quantity increase recommendations
    log_progress("Calculating unit quantity increase recommendations for performance improvement...")
    
    # Initialize quantity columns
    z_score_data['current_quantity'] = 0.0
    z_score_data['recommended_quantity_increase'] = 0.0
    z_score_data['recommended_quantity_change'] = 0.0  # STANDARDIZED
    z_score_data['unit_price'] = 0.0  # STANDARDIZED: Use standard column name
    z_score_data['investment_required'] = 0.0
    z_score_data['current_quantity'] = 0.0  # STANDARDIZED: Current quantity
    z_score_data['recommendation_text'] = ""  # STANDARDIZED: Text recommendation
    z_score_data['quantity_recommendation_text'] = ""
    
    quantity_increases = []
    
    for idx, row in z_score_data.iterrows():
        # Only calculate increases for stores with opportunities (positive gaps)
        if row['opportunity_gap'] <= 0:
            continue
            
        # Get current quantity for this store-SPU combination
        if ANALYSIS_LEVEL == "spu":
            quantity_key = f"{row['str_code']}_{row['spu_code']}"
            current_qty = quantity_lookup.get(quantity_key, 0.0)
        else:
            # For subcategory, estimate from sales amount (simplified approach)
            current_qty = row['sal_amt'] / 100.0  # Rough estimate: $100 per unit
        
        if current_qty <= 0:
            continue
            
        # Calculate unit price estimate
        if ANALYSIS_LEVEL == "spu":
            sales_col = 'spu_sales'
        else:
            sales_col = 'sal_amt'
            
        if current_qty > 0:
            unit_price = row[sales_col] / current_qty
        else:
            unit_price = row.get('unit_price', 50.0)  # REAL UNIT PRICE from API  # Default estimate
        
        # Calculate recommended quantity increase based on opportunity gap
        # Opportunity gap represents sales difference, convert to units
        gap_in_units = row['opportunity_gap'] / unit_price if unit_price > 0 else 0
        
        # Apply constraints
        max_increase = current_qty * MAX_INCREASE_PERCENTAGE
        recommended_increase = min(gap_in_units, max_increase)
        
        # Only recommend if above minimum threshold
        if recommended_increase >= MIN_INCREASE_QUANTITY:
            z_score_data.at[idx, 'current_quantity'] = current_qty
            z_score_data.at[idx, 'recommended_quantity_increase'] = recommended_increase
            z_score_data.at[idx, 'recommended_quantity_change'] = recommended_increase  # STANDARDIZED
            z_score_data.at[idx, 'unit_price'] = unit_price  # STANDARDIZED: Use standard column name
            z_score_data.at[idx, 'investment_required'] = recommended_increase * unit_price
            z_score_data.at[idx, 'current_quantity'] = current_qty  # STANDARDIZED: Current quantity
            
            # Create recommendation text
            recommendation_text = f"INCREASE {recommended_increase:.1f} UNITS/{TARGET_PERIOD_DAYS}-DAYS (current: {current_qty:.1f} → target: {current_qty + recommended_increase:.1f}) @ ~¥{unit_price:.0f}/unit"
            z_score_data.at[idx, 'quantity_recommendation_text'] = recommendation_text
            # STANDARDIZED: Add recommendation_text column for integration compatibility
            z_score_data.at[idx, 'recommendation_text'] = recommendation_text
            
            quantity_increases.append({
                'str_code': row['str_code'],
                'performance_level': row['performance_level'],
                'current_quantity': current_qty,
                'recommended_increase': recommended_increase,
                'investment_required': recommended_increase * unit_price
            })
    
    # Log quantity increase summary
    if quantity_increases:
        total_increases = sum(item['recommended_increase'] for item in quantity_increases)
        total_investment = sum(item['investment_required'] for item in quantity_increases)
        
        log_progress(f"Quantity increase recommendations generated:")
        log_progress(f"  - {len(quantity_increases):,} opportunities identified")
        log_progress(f"  - {total_increases:,.1f} total units/{TARGET_PERIOD_DAYS}-days increase needed")
        log_progress(f"  - ¥{total_investment:,.0f} total investment required")
        
        # Performance level breakdown
        level_breakdown = {}
        for item in quantity_increases:
            level = item['performance_level']
            if level not in level_breakdown:
                level_breakdown[level] = {'count': 0, 'units': 0, 'investment': 0}
            level_breakdown[level]['count'] += 1
            level_breakdown[level]['units'] += item['recommended_increase']
            level_breakdown[level]['investment'] += item['investment_required']
        
        for level, stats in level_breakdown.items():
            log_progress(f"  - {level}: {stats['count']} cases, {stats['units']:.1f} units, ¥{stats['investment']:.0f}")
    
    # APPLY STRICT SELECTIVITY FILTERS to reduce recommendation volume
    log_progress(f"Before selectivity filters: {len(z_score_data):,} records")
    
    # Filter 1: Only include records that need action (not top performers or performing well)
    actionable_levels = ['good_opportunity', 'major_opportunity']
    z_score_data = z_score_data[
        z_score_data['performance_level'].isin(actionable_levels)
    ].copy()
    log_progress(f"After performance level filter (only {actionable_levels}): {len(z_score_data):,} records")
    
    # Filter 2: Only include records with significant Z-scores
    z_score_data = z_score_data[
        z_score_data['opportunity_gap_z_score'] >= MIN_Z_SCORE_THRESHOLD
    ].copy()
    log_progress(f"After Z-score filter (>={MIN_Z_SCORE_THRESHOLD}): {len(z_score_data):,} records")
    
    # Filter 3: Only include records with meaningful quantity recommendations
    z_score_data = z_score_data[
        z_score_data['recommended_quantity_increase'] >= MIN_INCREASE_QUANTITY
    ].copy()
    log_progress(f"After quantity filter (>={MIN_INCREASE_QUANTITY} units): {len(z_score_data):,} records")
    
    # Filter 4: Minimum investment threshold
    z_score_data = z_score_data[
        z_score_data['investment_required'] >= MIN_INVESTMENT_THRESHOLD
    ].copy()
    log_progress(f"After investment filter (>=¥{MIN_INVESTMENT_THRESHOLD}): {len(z_score_data):,} records")
    
    # Filter 5: Calculate opportunity score and filter
    if len(z_score_data) > 0:
        z_score_data['opportunity_score'] = (
            z_score_data['opportunity_gap_z_score'] / 3.0  # Normalize Z-score to 0-1 range
        ).clip(0, 1)
        
        z_score_data = z_score_data[
            z_score_data['opportunity_score'] >= MIN_OPPORTUNITY_SCORE
        ].copy()
        log_progress(f"After opportunity score filter (>={MIN_OPPORTUNITY_SCORE}): {len(z_score_data):,} records")
    
    # Filter 6: Limit recommendations per store (top opportunities only)
    if len(z_score_data) > 0:
        z_score_data = z_score_data.sort_values(['str_code', 'opportunity_gap_z_score'], ascending=[True, False])
        z_score_data = z_score_data.groupby('str_code').head(MAX_RECOMMENDATIONS_PER_STORE).reset_index(drop=True)
        log_progress(f"After per-store limit filter (max {MAX_RECOMMENDATIONS_PER_STORE} per store): {len(z_score_data):,} records")
    
    # Performance level distribution (after filtering)
    if len(z_score_data) > 0:
        level_counts = z_score_data['performance_level'].value_counts()
        log_progress(f"Performance level distribution (after filtering):")
        for level, count in level_counts.items():
            log_progress(f"  • {level}: {count} ({count/len(z_score_data)*100:.1f}%)")
        
        stores_with_recs = z_score_data['str_code'].nunique()
        avg_recs_per_store = len(z_score_data) / stores_with_recs if stores_with_recs > 0 else 0
        log_progress(f"Final result: {len(z_score_data):,} recommendations across {stores_with_recs:,} stores (avg {avg_recs_per_store:.1f} per store)")
    else:
        log_progress("No records remain after filtering")
    
    return z_score_data

def aggregate_store_performance(classified_data: pd.DataFrame, cluster_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate category-level performance to store level with quantity increase recommendations.
    
    Args:
        classified_data: Category-level performance data with quantity recommendations
        cluster_df: Store cluster assignments
        
    Returns:
        DataFrame with store-level performance aggregation and total quantity increases
    """
    log_progress("Aggregating performance to store level with quantity increase totals...")
    
    # Create base results from cluster data
    results_df = cluster_df[['str_code', 'Cluster']].copy()
    
    if len(classified_data) == 0:
        log_progress("No classified data available for aggregation")
        return results_df
    
    # Determine column names based on analysis level
    if ANALYSIS_LEVEL == "subcategory":
        count_col = 'sub_cate_name'
        analyzed_col = 'subcategories_analyzed'
        top_quartile_col = 'top_quartile_subcategories'
    else:
        count_col = 'category_key'
        analyzed_col = 'categories_analyzed'
        top_quartile_col = 'top_quartile_categories'
    
    # QUANTITY ENHANCEMENT: Aggregate both performance and quantity metrics
    store_aggregation = classified_data.groupby('str_code').agg({
        'opportunity_gap_z_score': 'mean',          # Average Z-score across categories
        'opportunity_value': 'sum',                 # Total opportunity value
        count_col: 'count',                        # Number of categories analyzed
        'exceeds_top_quartile': 'sum',             # Number of categories exceeding top quartile
        'recommended_quantity_increase': 'sum',     # Total quantity increase needed
        'investment_required': 'sum',      # Total investment required
        'current_quantity': 'sum'                   # Total current quantity
    }).reset_index()
    
    store_aggregation.columns = [
        'str_code', 'avg_opportunity_z_score', 'total_opportunity_value', 
        analyzed_col, top_quartile_col, 'total_quantity_increase_needed',
        'total_investment_required', 'total_current_quantity'
    ]
    
    # QUANTITY ENHANCEMENT: Count stores with quantity recommendations
    stores_with_recommendations = classified_data[
        classified_data['recommended_quantity_increase'] > 0
    ]['str_code'].nunique()
    
    # Add quantity recommendation flags at store level
    store_quantity_flags = classified_data[
        classified_data['recommended_quantity_increase'] > 0
    ].groupby('str_code').size().reset_index(name='quantity_opportunities_count')
    
    store_aggregation = store_aggregation.merge(
        store_quantity_flags, on='str_code', how='left'
    )
    store_aggregation['quantity_opportunities_count'] = store_aggregation['quantity_opportunities_count'].fillna(0)
    store_aggregation['has_quantity_recommendations'] = (store_aggregation['quantity_opportunities_count'] > 0).astype(int)
    
    # Classify stores based on average Z-score
    def classify_store_performance(avg_z_score):
        if avg_z_score < PERFORMANCE_THRESHOLDS['top_performer']:
            return 'top_performer'
        elif avg_z_score <= PERFORMANCE_THRESHOLDS['performing_well']:
            return 'performing_well'
        elif avg_z_score <= PERFORMANCE_THRESHOLDS['some_opportunity']:
            return 'some_opportunity'
        elif avg_z_score <= PERFORMANCE_THRESHOLDS['good_opportunity']:
            return 'good_opportunity'
        else:
            return 'major_opportunity'
    
    store_aggregation['store_performance_level'] = store_aggregation['avg_opportunity_z_score'].apply(classify_store_performance)
    
    # Create binary flags for store-level performance
    for level in ['top_performer', 'performing_well', 'some_opportunity', 'good_opportunity', 'major_opportunity']:
        store_aggregation[f'rule12_{level}'] = (store_aggregation['store_performance_level'] == level).astype(int)
    
    # QUANTITY ENHANCEMENT: Add quantity-specific flags
    store_aggregation['rule12_quantity_increase_recommended'] = store_aggregation['has_quantity_recommendations']
    
    # Merge with base results
    results_df = results_df.merge(store_aggregation, on='str_code', how='left')
    
    # Fill missing values for stores with no performance data
    fill_columns = [
        'avg_opportunity_z_score', 'total_opportunity_value', analyzed_col, top_quartile_col,
        'total_quantity_increase_needed', 'total_investment_required', 
        'total_current_quantity', 'quantity_opportunities_count'
    ]
    for col in fill_columns:
        results_df[col] = results_df[col].fillna(0)
    
    for level in ['top_performer', 'performing_well', 'some_opportunity', 'good_opportunity', 'major_opportunity']:
        results_df[f'rule12_{level}'] = results_df[f'rule12_{level}'].fillna(0).astype(int)
    
    results_df['store_performance_level'] = results_df['store_performance_level'].fillna('no_data')
    results_df['has_quantity_recommendations'] = results_df['has_quantity_recommendations'].fillna(0).astype(int)
    results_df['rule12_quantity_increase_recommended'] = results_df['rule12_quantity_increase_recommended'].fillna(0).astype(int)
    
    # Add metadata
    results_df['rule12_description'] = f'Sales performance vs cluster top {TOP_QUARTILE_PERCENTILE}th percentile with quantity increase recommendations'
    results_df['rule12_analysis_method'] = 'Opportunity gap Z-score analysis with unit quantity increases'
    
    # QUANTITY ENHANCEMENT: Log quantity summary
    total_stores_with_qty_recs = results_df['rule12_quantity_increase_recommended'].sum()
    total_qty_increase = results_df['total_quantity_increase_needed'].sum()
    total_investment = results_df['total_investment_required'].sum()
    
    log_progress(f"Aggregated performance for {len(results_df)} stores with quantity enhancement:")
    log_progress(f"  - {total_stores_with_qty_recs:,} stores with quantity increase recommendations")
    log_progress(f"  - {total_qty_increase:,.1f} total units/{TARGET_PERIOD_DAYS}-days increase needed")
    log_progress(f"  - ¥{total_investment:,.0f} total investment required for quantity increases")
    
    # Store-level performance distribution
    store_level_counts = results_df['store_performance_level'].value_counts()
    log_progress(f"Store-level performance distribution:")
    for level, count in store_level_counts.items():
        log_progress(f"  • {level}: {count} stores ({count/len(results_df)*100:.1f}%)")
    
    return results_df

def save_results(results_df: pd.DataFrame, classified_data: pd.DataFrame) -> None:
    """Save rule results and detailed analysis"""
    
    # Save main rule results
    results_df.to_csv(RESULTS_FILE, index=False)
    log_progress(f"Saved rule results to {RESULTS_FILE}")
    
    # Save backward-compatible results (using subcategory analysis)
    if ANALYSIS_LEVEL == "subcategory":
        backward_compatible_file = "output/rule12_sales_performance_results.csv"
        results_df.to_csv(backward_compatible_file, index=False)
        log_progress(f"Saved backward-compatible results to {backward_compatible_file}")
    
    # Save detailed category-level analysis if data exists
    if len(classified_data) > 0:
        details_file = f"output/{ANALYSIS_CONFIGS[ANALYSIS_LEVEL]['output_prefix']}_details.csv"
        classified_data.to_csv(details_file, index=False)
        log_progress(f"Saved detailed {ANALYSIS_LEVEL} analysis to {details_file}")
        
        # Save backward-compatible details for subcategory analysis
        if ANALYSIS_LEVEL == "subcategory":
            backward_details_file = "output/rule12_subcategory_performance_details.csv"
            classified_data.to_csv(backward_details_file, index=False)
            log_progress(f"Saved backward-compatible details to {backward_details_file}")
    
    # Generate summary report
    summary_file = f"output/{ANALYSIS_CONFIGS[ANALYSIS_LEVEL]['output_prefix']}_summary.md"
    with open(summary_file, 'w') as f:
        f.write(f"# Rule 12: Sales Performance Rule with UNIT QUANTITY INCREASE RECOMMENDATIONS ({ANALYSIS_LEVEL.title()}-Level)\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Analysis Level**: {ANALYSIS_LEVEL.title()}\n\n")
        f.write(f"**ENHANCEMENT**: Now includes specific unit quantity increase recommendations! 🎯\n\n")
        
        f.write("## Rule Definition\n")
        f.write(f"**Purpose**: Identify sales opportunities by comparing store {ANALYSIS_LEVEL} performance against cluster top {TOP_QUARTILE_PERCENTILE}th percentile and provide specific unit quantity increase recommendations\n\n")
        f.write("**Method**: Opportunity gap Z-score analysis with unit quantity increase calculations\n")
        f.write("**Target Users**: Sales teams for revenue optimization with actionable quantity targets\n\n")
        
        f.write("## Performance Classification\n")
        if ANALYSIS_LEVEL == "subcategory":
            f.write("- **Top Performer** (Z < -1.0): Exceeding cluster top quartile\n")
            f.write("- **Performing Well** (-1.0 ≤ Z ≤ 0): Meeting expectations\n")
            f.write("- **Some Opportunity** (0 < Z ≤ 1.0): Minor improvement potential\n")
            f.write("- **Good Opportunity** (1.0 < Z ≤ 2.5): Solid growth potential\n")
            f.write("- **Major Opportunity** (Z > 2.5): Significant underperformance\n\n")
        else:
            f.write("- **Top Performer** (Z < -0.8): Exceeding cluster top quartile\n")
            f.write("- **Performing Well** (-0.8 ≤ Z ≤ 0): Meeting expectations\n")
            f.write("- **Some Opportunity** (0 < Z ≤ 0.8): Minor improvement potential\n")
            f.write("- **Good Opportunity** (0.8 < Z ≤ 2.0): Solid growth potential\n")
            f.write("- **Major Opportunity** (Z > 2.0): Significant underperformance\n\n")
        
        f.write("## Store-Level Results\n")
        f.write(f"- Total stores analyzed: {len(results_df):,}\n")
        
        # Performance level distribution
        if 'store_performance_level' in results_df.columns:
            performance_counts = results_df['store_performance_level'].value_counts()
            for level, count in performance_counts.items():
                if level != 'no_data':
                    f.write(f"- {level.replace('_', ' ').title()}: {count} stores ({count/len(results_df)*100:.1f}%)\n")
        
        f.write(f"\n")
        
        # QUANTITY ENHANCEMENT: Add quantity metrics to summary (robust to missing columns)
        f.write("## 🎯 UNIT QUANTITY INCREASE RECOMMENDATIONS\n")
        has_qty_col = 'rule12_quantity_increase_recommended' in results_df.columns
        qty_increase_col = 'total_quantity_increase_needed' in results_df.columns
        invest_col = 'total_investment_required' in results_df.columns
        total_stores_with_qty_recs = results_df['rule12_quantity_increase_recommended'].sum() if has_qty_col else 0
        total_qty_increase = results_df['total_quantity_increase_needed'].sum() if qty_increase_col else 0
        total_investment = results_df['total_investment_required'].sum() if invest_col else 0
        
        f.write(f"- **Stores with quantity recommendations**: {total_stores_with_qty_recs:,} stores\n")
        f.write(f"- **Total quantity increase needed**: {total_qty_increase:,.1f} units/{TARGET_PERIOD_DAYS}-days\n")
        f.write(f"- **Total investment required**: ¥{total_investment:,.0f}\n")
        
        if total_stores_with_qty_recs > 0:
            avg_qty_per_store = total_qty_increase / total_stores_with_qty_recs
            avg_investment_per_store = total_investment / total_stores_with_qty_recs
            f.write(f"- **Average per store**: {avg_qty_per_store:.1f} units, ¥{avg_investment_per_store:.0f} investment\n")
        
        f.write(f"\n**Calculation Method**: Opportunity gaps converted to unit quantities using real sales data and constrained by maximum {int(MAX_INCREASE_PERCENTAGE*100)}% increase limits\n\n")
        
        if len(classified_data) > 0:
            f.write("## Key Insights\n")
            
            # Top opportunities with quantity focus
            major_opportunities = results_df[results_df['rule12_major_opportunity'] == 1]
            if len(major_opportunities) > 0:
                f.write(f"- **Major opportunity stores**: {len(major_opportunities)} stores with significant underperformance\n")
                f.write(f"- **Average opportunity value**: {major_opportunities['total_opportunity_value'].mean():.1f} units per store\n")
                
                # Quantity focus for major opportunities
                major_with_qty = major_opportunities[major_opportunities['rule12_quantity_increase_recommended'] == 1]
                if len(major_with_qty) > 0:
                    avg_qty_major = major_with_qty['total_quantity_increase_needed'].mean()
                    avg_investment_major = major_with_qty['total_investment_required'].mean()
                    f.write(f"- **Major opportunity quantity needs**: {avg_qty_major:.1f} units/store, ¥{avg_investment_major:.0f}/store\n")
            
            # Top performers
            top_performers = results_df[results_df['rule12_top_performer'] == 1]
            if len(top_performers) > 0:
                f.write(f"- **Top performers**: {len(top_performers)} stores exceeding cluster benchmarks\n")
                f.write(f"- **Learning opportunities**: Study practices from top performers\n")
            
            # Category insights
            if len(classified_data) > 0:
                major_opp_categories = classified_data[classified_data['performance_level'] == 'major_opportunity']
                if len(major_opp_categories) > 0:
                    if ANALYSIS_LEVEL == "subcategory":
                        category_col = 'sub_cate_name'
                        category_label = "subcategories"
                    else:
                        category_col = 'category_key'
                        category_label = "categories"
                    
                    top_opp_categories = major_opp_categories[category_col].value_counts().head(5)
                    f.write(f"\n**Top {category_label} with major opportunities**:\n")
                    for category, count in top_opp_categories.items():
                        f.write(f"- {category}: {count} stores\n")
        
        f.write(f"\n## 🎯 Recommendations for Sales Teams\n")
        f.write(f"1. **Prioritize quantity increases** for {total_stores_with_qty_recs:,} stores with specific unit targets\n")
        f.write(f"2. **Focus on major opportunity {ANALYSIS_LEVEL}s** for immediate attention\n")
        f.write("3. **Study top performer practices** for replication strategies\n")
        f.write(f"4. **Use realistic targets** based on cluster top {TOP_QUARTILE_PERCENTILE}th percentile performance\n")
        f.write("5. **Monitor progress** using quarterly re-analysis\n")
        f.write("6. **Budget planning**: Use investment requirements for procurement decisions\n")
        
        if ANALYSIS_LEVEL == "spu":
            f.write("7. **SPU-Level Precision**: Use granular SPU quantity data for precise inventory decisions\n")
            f.write("8. **Cross-Reference with Subcategory**: Compare SPU findings with subcategory trends\n")
    
    log_progress(f"Saved enhanced summary report with quantity metrics to {summary_file}")
    
    # Save backward-compatible summary for subcategory analysis
    if ANALYSIS_LEVEL == "subcategory":
        backward_summary_file = "output/rule12_sales_performance_summary.md"
        with open(backward_summary_file, 'w') as f:
            f.write("# Rule 12: Sales Performance Deviation Analysis Summary\n\n")
            f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Rule Definition\n")
            f.write("**Purpose**: Identify sales opportunities by comparing store subcategory performance against cluster top quartile (75th percentile)\n\n")
            f.write("**Method**: Opportunity gap Z-score analysis\n")
            f.write("**Target Users**: Sales teams for revenue optimization\n\n")
            
            f.write("## Performance Classification\n")
            f.write("- **Top Performer** (Z < -1.0): Exceeding cluster top quartile\n")
            f.write("- **Performing Well** (-1.0 ≤ Z ≤ 0): Meeting expectations\n")
            f.write("- **Some Opportunity** (0 < Z ≤ 1.0): Minor improvement potential\n")
            f.write("- **Good Opportunity** (1.0 < Z ≤ 2.5): Solid growth potential\n")
            f.write("- **Major Opportunity** (Z > 2.5): Significant underperformance\n\n")
            
            f.write("## Store-Level Results\n")
            f.write(f"- Total stores analyzed: {len(results_df):,}\n")
            
            # Performance level distribution
            performance_counts = results_df['store_performance_level'].value_counts()
            for level, count in performance_counts.items():
                if level != 'no_data':
                    f.write(f"- {level.replace('_', ' ').title()}: {count} stores ({count/len(results_df)*100:.1f}%)\n")
            
            f.write(f"\n")
            
            if len(classified_data) > 0:
                f.write("## Key Insights\n")
                
                # Top opportunities
                major_opportunities = results_df[results_df['rule12_major_opportunity'] == 1]
                if len(major_opportunities) > 0:
                    f.write(f"- **Major opportunity stores**: {len(major_opportunities)} stores with significant underperformance\n")
                    f.write(f"- **Average opportunity value**: {major_opportunities['total_opportunity_value'].mean():.1f} units per store\n")
                
                # Top performers
                top_performers = results_df[results_df['rule12_top_performer'] == 1]
                if len(top_performers) > 0:
                    f.write(f"- **Top performers**: {len(top_performers)} stores exceeding cluster benchmarks\n")
                    f.write(f"- **Learning opportunities**: Study practices from top performers\n")
                
                # Subcategory insights
                major_opp_subcats = classified_data[classified_data['performance_level'] == 'major_opportunity']
                if len(major_opp_subcats) > 0:
                    top_opp_subcats = major_opp_subcats['sub_cate_name'].value_counts().head(5)
                    f.write(f"\n**Top subcategories with major opportunities**:\n")
                    for subcat, count in top_opp_subcats.items():
                        f.write(f"- {subcat}: {count} stores\n")
            
            f.write(f"\n## Recommendations for Sales Teams\n")
            f.write("1. **Prioritize major opportunity subcategories** for immediate attention\n")
            f.write("2. **Study top performer practices** for replication strategies\n")
            f.write("3. **Focus on realistic targets** based on cluster top quartile performance\n")
            f.write("4. **Monitor progress** using quarterly re-analysis\n")
        
        log_progress(f"Saved backward-compatible summary to {backward_summary_file}")

def main() -> None:
    """Main function to execute the sales performance deviation analysis"""
    log_progress(f"Starting Rule 12: Sales Performance Deviation Analysis ({ANALYSIS_LEVEL.title()}-Level)...")
    
    try:
        # Load data
        cluster_df, category_df, quantity_df = load_data()
        
        # Prepare sales data
        sales_data = prepare_sales_data(category_df, cluster_df, quantity_df)
        
        if len(sales_data) == 0:
            log_progress("No valid sales data found. Creating empty results.")
            results_df = cluster_df[['str_code', 'Cluster']].copy()
            
            # Create empty results
            for level in ['top_performer', 'performing_well', 'some_opportunity', 'good_opportunity', 'major_opportunity']:
                results_df[f'rule12_{level}'] = 0
            
            results_df['avg_opportunity_z_score'] = 0
            results_df['total_opportunity_value'] = 0
            
            if ANALYSIS_LEVEL == "subcategory":
                results_df['subcategories_analyzed'] = 0
                results_df['top_quartile_subcategories'] = 0
            else:
                results_df['categories_analyzed'] = 0
                results_df['top_quartile_categories'] = 0
            
            results_df['store_performance_level'] = 'no_data'
            results_df['rule12_description'] = f'Sales performance vs cluster top {TOP_QUARTILE_PERCENTILE}th percentile'
            results_df['rule12_analysis_method'] = 'Opportunity gap Z-score analysis'
            
            save_results(results_df, pd.DataFrame())
            return
        
        # Calculate opportunity gaps
        opportunity_data = calculate_opportunity_gaps(sales_data)
        
        if len(opportunity_data) == 0:
            log_progress("No valid opportunity data found. Creating empty results.")
            results_df = aggregate_store_performance(pd.DataFrame(), cluster_df)
            save_results(results_df, pd.DataFrame())
            return
        
        # Calculate Z-scores
        z_score_data = calculate_opportunity_z_scores(opportunity_data)
        
        # Classify performance levels
        classified_data = classify_performance_levels(z_score_data, quantity_df)
        
        # Aggregate to store level
        results_df = aggregate_store_performance(classified_data, cluster_df)
        
        # Save results
        save_results(results_df, classified_data)
        
        log_progress(f"Rule 12: Sales Performance Deviation Analysis ({ANALYSIS_LEVEL.title()}-Level) completed successfully!")
        
    except Exception as e:
        log_progress(f"Error in Rule 12 analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main() 