#!/usr/bin/env python3
"""
Step 2B: Year-over-Year Multi-Period Data Consolidation & Seasonal Feature Engineering
=====================================================================================

This step consolidates year-over-year seasonal data into meaningful features for clustering analysis.
It processes a whitelist of current and historical half-month periods defined in INPUT_PERIODS.

Input: 12 explicitly whitelisted periods (current + prior year) configured in INPUT_PERIODS.

Output: Consolidated year-over-year seasonal features for enhanced clustering

Features Created:
- Year-over-year seasonal comparison patterns
- Store-level seasonal sales trends (current vs historical)
- Category preference evolution across seasons
- Seasonal volatility and consistency metrics
- Weather-adjusted performance patterns
- Cross-year growth and decline patterns

Author: Enhanced Clustering Pipeline
Date: 2025-07-21
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')
import argparse
from src.output_utils import create_output_with_symlinks

# Configuration - Year-over-Year Multi-Period Analysis
INPUT_PERIODS = [
    # Explicit whitelist per user requirement
    '202508A', '202507A', '202507B', '202506A', '202506B', '202505B',
    '202409A', '202409B', '202410A', '202410B', '202411A', '202408B'
]
OUTPUT_DIR = "output"
DATA_DIR = "data"

# Seasonal definitions for year-over-year analysis
SEASONAL_CONFIG = {
    'period_mapping': {
        # Current periods (2025) - late Spring to Summer progression
        '202505B': {'month': 'May', 'half': 'Second', 'year': '2025', 'season': 'Spring', 'season_progress': 0.00},
        '202506A': {'month': 'June', 'half': 'First',  'year': '2025', 'season': 'Summer', 'season_progress': 0.17},
        '202506B': {'month': 'June', 'half': 'Second', 'year': '2025', 'season': 'Summer', 'season_progress': 0.33},
        '202507A': {'month': 'July', 'half': 'First',  'year': '2025', 'season': 'Summer', 'season_progress': 0.50},
        '202507B': {'month': 'July', 'half': 'Second', 'year': '2025', 'season': 'Summer', 'season_progress': 0.67},
        '202508A': {'month': 'August','half': 'First',  'year': '2025', 'season': 'Summer', 'season_progress': 0.83},

        # Historical periods (2024) - late Summer to Fall progression
        '202408B': {'month': 'August',  'half': 'Second', 'year': '2024', 'season': 'Summer', 'season_progress': 1.00},
        '202409A': {'month': 'September','half': 'First',  'year': '2024', 'season': 'Fall',   'season_progress': 1.17},
        '202409B': {'month': 'September','half': 'Second', 'year': '2024', 'season': 'Fall',   'season_progress': 1.33},
        '202410A': {'month': 'October', 'half': 'First',  'year': '2024', 'season': 'Fall',   'season_progress': 1.50},
        '202410B': {'month': 'October', 'half': 'Second', 'year': '2024', 'season': 'Fall',   'season_progress': 1.67},
        '202411A': {'month': 'November','half': 'First',  'year': '2024', 'season': 'Fall',   'season_progress': 1.83},
    }
}

def infer_season_info(period: str) -> Dict[str, object]:
    """
    Fallback season info for periods not present in SEASONAL_CONFIG['period_mapping'].
    Provides a reasonable season label and a continuous season_progress value
    aligned with the existing scale used in the config.

    Scale conventions used here (approximate, consistent with existing values):
      - Summer:   JunA=0.17, JunB=0.33, JulA=0.50, JulB=0.67, AugA=0.83, AugB=1.00
      - Fall:     SepA=1.17, SepB=1.33, OctA=1.50, OctB=1.67, NovA=1.83, NovB=2.00
      - Winter:   DecA=2.17, DecB=2.33, JanA=2.50, JanB=2.67, FebA=2.83, FebB=3.00
      - Spring:   MarA=3.17, MarB=3.33, AprA=3.50, AprB=3.67, MayA=3.83, MayB=4.00
    """
    yyyymm = period[:6]
    half = period[6:] if len(period) > 6 else 'A'
    month = int(yyyymm[4:6])

    # Determine season and base offset
    if month in (6, 7, 8):
        season = 'Summer'
        # Map months within season
        base_map = {6: 0.17, 7: 0.50, 8: 0.83}
    elif month in (9, 10, 11):
        season = 'Fall'
        base_map = {9: 1.17, 10: 1.50, 11: 1.83}
    elif month in (12, 1, 2):
        season = 'Winter'
        # Treat Jan/Feb with a continued progression
        base_map = {12: 2.17, 1: 2.50, 2: 2.83}
    else:  # 3,4,5
        season = 'Spring'
        base_map = {3: 3.17, 4: 3.50, 5: 3.83}

    base = base_map.get(month, 0.0)
    # Add half offset: A ~ +0.00, B ~ +0.16/0.17
    half_offset = 0.16 if half == 'B' else 0.00
    season_progress = round(base + half_offset, 2)

    return {
        'month': yyyymm[4:6],
        'half': 'First' if half == 'A' else 'Second',
        'year': yyyymm[:4],
        'season': season,
        'season_progress': season_progress,
    }

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_multi_period_data() -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Load all 6 periods of data into organized structure.
    
    Returns:
        Dictionary organized as {period: {data_type: DataFrame}}
    """
    log_progress(f"📥 Loading multi-period dataset (periods: {len(INPUT_PERIODS)})...")
    
    data_structure = {}
    
    for period in INPUT_PERIODS:
        log_progress(f"Loading period {period}...")
        period_data = {}
        
        # Load the three main data files for each period
        files_to_load = {
            'category_sales': f'complete_category_sales_{period}.csv',
            'spu_sales': f'complete_spu_sales_{period}.csv', 
            'store_config': f'store_config_{period}.csv'
        }
        
        for data_type, filename in files_to_load.items():
            filepath = os.path.join(DATA_DIR, "api_data", filename)
            if os.path.exists(filepath):
                try:
                    df = pd.read_csv(filepath, dtype={'str_code': str})
                    period_data[data_type] = df
                    log_progress(f"  ✅ {data_type}: {len(df):,} records")
                except Exception as e:
                    log_progress(f"  ❌ Failed to load {filename}: {e}")
                    period_data[data_type] = pd.DataFrame()
            else:
                log_progress(f"  ⚠️ Missing file: {filename}")
                period_data[data_type] = pd.DataFrame()
        
        data_structure[period] = period_data
    
    log_progress(f"✅ Loaded data for {len(data_structure)} periods")
    return data_structure

def create_store_seasonal_profiles(multi_period_data: Dict[str, Dict[str, pd.DataFrame]]) -> pd.DataFrame:
    """
    Create store-level seasonal profiles from 3-month data.
    
    Args:
        multi_period_data: Multi-period data structure
        
    Returns:
        DataFrame with store seasonal features
    """
    log_progress("🔄 Creating store seasonal profiles...")
    
    store_profiles = []
    
    # Get unique stores across all periods
    all_stores = set()
    for period_data in multi_period_data.values():
        if 'category_sales' in period_data and not period_data['category_sales'].empty:
            all_stores.update(period_data['category_sales']['str_code'].unique())
    
    log_progress(f"Processing {len(all_stores)} unique stores...")
    
    for store_code in tqdm(all_stores, desc="Creating store profiles"):
        store_profile = {'str_code': store_code}
        
        # Collect store data across all periods
        store_periods = []
        total_sales_by_period = []
        category_counts_by_period = []
        spu_counts_by_period = []
        
        for period in INPUT_PERIODS:
            period_data = multi_period_data[period]
            
            # Category sales for this store in this period
            if 'category_sales' in period_data and not period_data['category_sales'].empty:
                store_categories = period_data['category_sales'][
                    period_data['category_sales']['str_code'] == store_code
                ]
                
                if not store_categories.empty:
                    period_sales = store_categories['sal_amt'].sum() if 'sal_amt' in store_categories.columns else 0
                    period_categories = store_categories['sub_cate_name'].nunique() if 'sub_cate_name' in store_categories.columns else 0
                else:
                    period_sales = 0
                    period_categories = 0
            else:
                period_sales = 0
                period_categories = 0
            
            # SPU data for this store in this period
            if 'spu_sales' in period_data and not period_data['spu_sales'].empty:
                store_spus = period_data['spu_sales'][
                    period_data['spu_sales']['str_code'] == store_code
                ]
                period_spus = store_spus['spu_code'].nunique() if not store_spus.empty and 'spu_code' in store_spus.columns else 0
            else:
                period_spus = 0
            
            store_periods.append(period)
            total_sales_by_period.append(period_sales)
            category_counts_by_period.append(period_categories)
            spu_counts_by_period.append(period_spus)
        
        # Calculate seasonal features
        sales_array = np.array(total_sales_by_period)
        
        # Basic metrics
        store_profile['total_3month_sales'] = sales_array.sum()
        store_profile['avg_period_sales'] = sales_array.mean()
        store_profile['sales_volatility'] = sales_array.std() / (sales_array.mean() + 1)  # Coefficient of variation
        
        # Trend analysis
        if len(sales_array) > 1:
            # Simple linear trend (slope)
            x = np.arange(len(sales_array))
            if sales_array.sum() > 0:
                trend_coef = np.polyfit(x, sales_array, 1)[0]
                store_profile['sales_trend'] = trend_coef
            else:
                store_profile['sales_trend'] = 0.0
        else:
            store_profile['sales_trend'] = 0.0
        
        # Category and SPU metrics
        store_profile['avg_categories_per_period'] = np.mean(category_counts_by_period)
        store_profile['avg_spus_per_period'] = np.mean(spu_counts_by_period)
        store_profile['category_stability'] = 1.0 - (np.std(category_counts_by_period) / (np.mean(category_counts_by_period) + 1))
        
        # Early vs Late season performance
        early_sales = sales_array[:3].sum()  # May-June first halves  
        late_sales = sales_array[3:].sum()   # June second half - July
        total_sales = sales_array.sum()
        
        if total_sales > 0:
            store_profile['early_season_ratio'] = early_sales / total_sales
            store_profile['late_season_ratio'] = late_sales / total_sales
        else:
            store_profile['early_season_ratio'] = 0.33
            store_profile['late_season_ratio'] = 0.67
        
        # Performance classification
        if store_profile['total_3month_sales'] > np.percentile([p['total_3month_sales'] for p in store_profiles if 'total_3month_sales' in p] + [store_profile['total_3month_sales']], 75):
            store_profile['performance_tier'] = 'High'
        elif store_profile['total_3month_sales'] > np.percentile([p['total_3month_sales'] for p in store_profiles if 'total_3month_sales' in p] + [store_profile['total_3month_sales']], 50):
            store_profile['performance_tier'] = 'Medium'
        else:
            store_profile['performance_tier'] = 'Low'
        
        store_profiles.append(store_profile)
    
    profiles_df = pd.DataFrame(store_profiles)
    log_progress(f"✅ Created seasonal profiles for {len(profiles_df)} stores")
    
    return profiles_df

def create_category_seasonal_patterns(multi_period_data: Dict[str, Dict[str, pd.DataFrame]]) -> pd.DataFrame:
    """
    Create category-level seasonal patterns from 3-month data.
    
    Args:
        multi_period_data: Multi-period data structure
        
    Returns:
        DataFrame with category seasonal patterns
    """
    log_progress("🔄 Creating category seasonal patterns...")
    
    # Combine all category sales data
    all_category_data = []
    
    for period in INPUT_PERIODS:
        period_data = multi_period_data[period]
        if 'category_sales' in period_data and not period_data['category_sales'].empty:
            df = period_data['category_sales'].copy()
            df['period'] = period
            # Use configured mapping if available; otherwise fall back to inferred season info
            mapping = SEASONAL_CONFIG['period_mapping']
            if period in mapping:
                df['season_progress'] = mapping[period]['season_progress']
            else:
                df['season_progress'] = infer_season_info(period)['season_progress']
            all_category_data.append(df)
    
    if not all_category_data:
        log_progress("⚠️ No category data found")
        return pd.DataFrame()
    
    combined_categories = pd.concat(all_category_data, ignore_index=True)
    
    # Create category seasonal patterns
    category_patterns = combined_categories.groupby(['sub_cate_name', 'period']).agg({
        'sal_amt': ['sum', 'mean', 'count'],
        'str_code': 'nunique'
    }).reset_index()
    
    # Flatten column names
    category_patterns.columns = ['sub_cate_name', 'period', 'total_sales', 'avg_sales', 'transaction_count', 'store_count']
    
    log_progress(f"✅ Created seasonal patterns for {category_patterns['sub_cate_name'].nunique()} categories")
    
    return category_patterns

def generate_clustering_features(store_profiles: pd.DataFrame, category_patterns: pd.DataFrame) -> pd.DataFrame:
    """
    Generate final clustering features from seasonal profiles.
    
    Args:
        store_profiles: Store seasonal profiles
        category_patterns: Category seasonal patterns
        
    Returns:
        DataFrame ready for clustering
    """
    log_progress("🔄 Generating final clustering features...")
    
    # Start with store profiles as base
    clustering_features = store_profiles.copy()
    
    # Add derived features for clustering
    
    # Normalize sales metrics (log transform for skewed data)
    clustering_features['log_total_sales'] = np.log1p(clustering_features['total_3month_sales'])
    clustering_features['log_avg_sales'] = np.log1p(clustering_features['avg_period_sales'])
    
    # Create composite scores
    clustering_features['consistency_score'] = (
        clustering_features['category_stability'] * 0.5 + 
        (1 - clustering_features['sales_volatility'].clip(0, 1)) * 0.5
    )
    
    clustering_features['growth_score'] = np.tanh(clustering_features['sales_trend'] / 1000)  # Normalized growth
    
    # Seasonal balance score (how balanced early vs late season)
    clustering_features['seasonal_balance'] = 1 - abs(clustering_features['early_season_ratio'] - 0.5) * 2
    
    # Select final clustering columns
    clustering_columns = [
        'str_code',
        'log_total_sales',
        'log_avg_sales', 
        'sales_volatility',
        'sales_trend',
        'avg_categories_per_period',
        'avg_spus_per_period',
        'consistency_score',
        'growth_score',
        'seasonal_balance',
        'early_season_ratio',
        'late_season_ratio'
    ]
    
    final_features = clustering_features[clustering_columns].copy()
    
    # Handle any remaining NaN values
    final_features = final_features.fillna(0)
    
    log_progress(f"✅ Generated clustering features for {len(final_features)} stores")
    log_progress(f"Features: {list(final_features.columns[1:])}")  # Exclude str_code
    
    return final_features

def save_seasonal_clustering_data(store_profiles: pd.DataFrame, category_patterns: pd.DataFrame, 
                                 clustering_features: pd.DataFrame) -> None:
    """
    Save all generated seasonal data for clustering.
    
    Args:
        store_profiles: Store seasonal profiles
        category_patterns: Category seasonal patterns  
        clustering_features: Final clustering features
    """
    log_progress("💾 Saving seasonal clustering data...")
    
    # Save files using dual output pattern
    files_saved = []
    
    # Store profiles
    timestamped, symlink, generic = create_output_with_symlinks(
        store_profiles,
        os.path.join(OUTPUT_DIR, "seasonal_store_profiles"),
        ""  # No period label for seasonal data
    )
    files_saved.append(timestamped)
    
    # Category patterns
    timestamped, symlink, generic = create_output_with_symlinks(
        category_patterns,
        os.path.join(OUTPUT_DIR, "seasonal_category_patterns"),
        ""  # No period label for seasonal data
    )
    files_saved.append(timestamped)
    
    # Final clustering features
    timestamped, symlink, generic = create_output_with_symlinks(
        clustering_features,
        os.path.join(OUTPUT_DIR, "seasonal_clustering_features"),
        ""  # No period label for seasonal data
    )
    files_saved.append(timestamped)
    
    # Also create consolidated_seasonal_features.csv for backward compatibility
    standard_features_file = os.path.join(OUTPUT_DIR, "consolidated_seasonal_features.csv")
    clustering_features.to_csv(standard_features_file, index=False)
    files_saved.append(standard_features_file)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save metadata
    metadata = {
        'creation_time': timestamp,
        'input_periods': INPUT_PERIODS,
        'total_stores': len(clustering_features),
        'feature_columns': list(clustering_features.columns[1:]),  # Exclude str_code
        'files_created': files_saved
    }
    
    metadata_file = os.path.join(OUTPUT_DIR, f"seasonal_clustering_metadata_{timestamp}.json")
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    log_progress("✅ Saved seasonal clustering data:")
    for file in files_saved:
        log_progress(f"  • {os.path.basename(file)}")

def main():
    """Main execution function"""
    log_progress("🚀 Starting Step 2B: Multi-Period Data Consolidation & Seasonal Feature Engineering")
    
    try:
        # Optional CLI to override INPUT_PERIODS without editing source
        parser = argparse.ArgumentParser(description="Step 2B seasonal consolidation")
        parser.add_argument(
            "--periods",
            type=str,
            help="Comma-separated list of half-month periods to include (e.g., 202409A,202409B,202410A,202410B)"
        )
        args, _ = parser.parse_known_args()

        if args.periods:
            periods = [p.strip() for p in args.periods.split(',') if p.strip()]
            if periods:
                log_progress(f"🔧 Overriding INPUT_PERIODS via CLI with {len(periods)} periods")
                global INPUT_PERIODS
                INPUT_PERIODS = periods
            else:
                log_progress("⚠️ --periods provided but no valid tokens parsed; using default INPUT_PERIODS")
        
        # Load multi-period data
        multi_period_data = load_multi_period_data()
        
        # Create store seasonal profiles
        store_profiles = create_store_seasonal_profiles(multi_period_data)
        
        # Create category seasonal patterns
        category_patterns = create_category_seasonal_patterns(multi_period_data)
        
        # Generate final clustering features
        clustering_features = generate_clustering_features(store_profiles, category_patterns)
        
        # Save all data
        save_seasonal_clustering_data(store_profiles, category_patterns, clustering_features)
        
        log_progress("🎉 Step 2B completed successfully!")
        log_progress(f"Ready for enhanced clustering with {len(clustering_features)} stores and {len(clustering_features.columns)-1} features")
        
        # Summary statistics
        log_progress("\n📊 Seasonal Data Summary:")
        log_progress(f"  • Total 3-month sales range: ¥{clustering_features['log_total_sales'].min():.0f} - ¥{clustering_features['log_total_sales'].max():.0f}")
        log_progress(f"  • Average volatility: {store_profiles['sales_volatility'].mean():.3f}")
        log_progress(f"  • Stores with positive growth: {(store_profiles['sales_trend'] > 0).sum()}")
        log_progress(f"  • Categories identified: {category_patterns['sub_cate_name'].nunique() if not category_patterns.empty else 0}")
        
    except Exception as e:
        log_progress(f"❌ Step 2 failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 