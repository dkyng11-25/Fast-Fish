#!/usr/bin/env python3
"""
Debug Trending Issue
===================

Find why our trend generation works but final output shows all 0s.
"""

import pandas as pd
import sys
sys.path.append('./src')
from src.step17_fixed_trending import generate_diverse_trend_scores, get_stores_in_group, load_historical_spu_data

def debug_trending_issue():
    """Debug the trending issue step by step."""
    
    print("🔍 DEBUGGING TRENDING ISSUE")
    print("="*50)
    
    # Load data
    print("1. Loading historical data...")
    historical_df = load_historical_spu_data()
    print(f"   ✅ Loaded {len(historical_df):,} records")
    
    # Load Fast Fish data
    print("2. Loading Fast Fish data...")
    fast_fish_file = "output/fast_fish_with_proper_trending_20250714_114118.csv"
    fast_fish_df = pd.read_csv(fast_fish_file)
    print(f"   ✅ Loaded {len(fast_fish_df):,} Fast Fish recommendations")
    
    # Check store group names
    print("3. Checking store group names...")
    unique_store_groups = fast_fish_df['Store_Group_Name'].unique()
    print(f"   ✅ Found {len(unique_store_groups)} unique store groups")
    print(f"   📋 Sample groups: {list(unique_store_groups)[:5]}")
    
    # Test trend generation for first few groups
    print("4. Testing trend generation...")
    store_group_trends = {}
    for i, store_group in enumerate(unique_store_groups[:3]):
        print(f"   🏢 Testing {store_group}...")
        stores = get_stores_in_group(store_group)
        trends = generate_diverse_trend_scores(store_group, stores, historical_df)
        store_group_trends[store_group] = trends
        print(f"      trend_sales_performance: {trends['trend_sales_performance']}")
        print(f"      trend_weather_impact: {trends['trend_weather_impact']}")
    
    # Test mapping to DataFrame
    print("5. Testing mapping to DataFrame...")
    test_df = fast_fish_df.head(10).copy()
    test_df['trend_sales_performance'] = test_df['Store_Group_Name'].map(
        lambda x: store_group_trends.get(x, {}).get('trend_sales_performance', 0)
    )
    test_df['trend_weather_impact'] = test_df['Store_Group_Name'].map(
        lambda x: store_group_trends.get(x, {}).get('trend_weather_impact', 0)
    )
    
    print("   📊 Test mapping results:")
    for idx, row in test_df.iterrows():
        print(f"      {row['Store_Group_Name']}: sales={row['trend_sales_performance']}, weather={row['trend_weather_impact']}")
        if idx >= 2:  # Only show first 3
            break
    
    # Check if trends exist in actual file
    print("6. Checking actual file columns...")
    trend_cols = [col for col in fast_fish_df.columns if 'trend_' in col]
    print(f"   📋 Trend columns in file: {trend_cols}")
    
    for col in trend_cols[:3]:  # Check first 3 trend columns
        unique_vals = fast_fish_df[col].nunique()
        val_range = f"{fast_fish_df[col].min()}-{fast_fish_df[col].max()}"
        print(f"   {col}: {unique_vals} unique values, range {val_range}")

if __name__ == "__main__":
    debug_trending_issue() 