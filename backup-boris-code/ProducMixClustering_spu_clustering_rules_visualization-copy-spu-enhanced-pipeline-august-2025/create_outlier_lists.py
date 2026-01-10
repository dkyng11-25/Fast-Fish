#!/usr/bin/env python3
"""
Create Outlier Lists - Simplified version to extract key outliers
"""

import pandas as pd
import numpy as np

def create_outlier_lists():
    """Create comprehensive outlier lists."""
    
    print("🔍 Creating Outlier Lists")
    print("=" * 50)
    
    # Load the main extraction CSV
    csv_file = 'output/all_rule_suggestions.csv'
    df = pd.read_csv(csv_file)
    
    print(f"✅ Loaded {len(df):,} total suggestions")
    
    # 1. MASSIVE QUANTITY OUTLIERS (>1000 units)
    massive_qty = df[df['current_quantity'] > 1000].copy()
    massive_qty['item_type'] = massive_qty['spu_code'].str.split('_').str[1]
    massive_qty['sales_value'] = massive_qty['current_quantity'] * massive_qty['unit_price']
    massive_qty = massive_qty.sort_values('current_quantity', ascending=False)
    
    print(f"📊 Massive Quantity Outliers (>1000 units): {len(massive_qty)}")
    
    # 2. EXTREME QUANTITY OUTLIERS (>500 units)
    extreme_qty = df[df['current_quantity'] > 500].copy()
    extreme_qty['item_type'] = extreme_qty['spu_code'].str.split('_').str[1]
    extreme_qty['sales_value'] = extreme_qty['current_quantity'] * extreme_qty['unit_price']
    extreme_qty = extreme_qty.sort_values('current_quantity', ascending=False)
    
    print(f"📊 Extreme Quantity Outliers (>500 units): {len(extreme_qty)}")
    
    # 3. HIGH QUANTITY OUTLIERS (>200 units)
    high_qty = df[df['current_quantity'] > 200].copy()
    high_qty['item_type'] = high_qty['spu_code'].str.split('_').str[1]
    high_qty['sales_value'] = high_qty['current_quantity'] * high_qty['unit_price']
    high_qty = high_qty.sort_values('current_quantity', ascending=False)
    
    print(f"📊 High Quantity Outliers (>200 units): {len(high_qty)}")
    
    # 4. HIGH INVESTMENT OUTLIERS (>$10k)
    high_inv = df[abs(df['investment_required']) > 10000].copy()
    high_inv['item_type'] = high_inv['spu_code'].str.split('_').str[1]
    high_inv['abs_investment'] = abs(high_inv['investment_required'])
    high_inv = high_inv.sort_values('abs_investment', ascending=False)
    
    print(f"💰 High Investment Outliers (>$10k): {len(high_inv)}")
    
    # Save the outlier lists
    print(f"\n💾 Saving outlier lists...")
    
    # Save massive quantity outliers
    if len(massive_qty) > 0:
        massive_qty.to_csv('output/massive_quantity_outliers.csv', index=False)
        print(f"   ✅ Massive quantity outliers saved: {len(massive_qty)} records")
    
    # Save extreme quantity outliers
    if len(extreme_qty) > 0:
        extreme_qty.to_csv('output/extreme_quantity_outliers.csv', index=False)
        print(f"   ✅ Extreme quantity outliers saved: {len(extreme_qty)} records")
    
    # Save high quantity outliers
    if len(high_qty) > 0:
        high_qty.to_csv('output/high_quantity_outliers.csv', index=False)
        print(f"   ✅ High quantity outliers saved: {len(high_qty)} records")
    
    # Save high investment outliers
    if len(high_inv) > 0:
        high_inv.to_csv('output/high_investment_outliers.csv', index=False)
        print(f"   ✅ High investment outliers saved: {len(high_inv)} records")
    
    # Create summary of top outliers
    print(f"\n🚨 TOP 20 MASSIVE QUANTITY OUTLIERS:")
    print("=" * 80)
    for i, (_, row) in enumerate(massive_qty.head(20).iterrows()):
        print(f"{i+1:2d}. Store {row['store_code']}, {row['item_type']}: "
              f"{row['current_quantity']:.1f} units, ${row['unit_price']:.2f}/unit, "
              f"${row['sales_value']:,.0f} total value")
    
    # Store and SPU patterns
    print(f"\n📊 STORE PATTERNS IN MASSIVE OUTLIERS:")
    store_counts = massive_qty['store_code'].value_counts()
    print(f"   Top 10 stores with most massive outliers:")
    for i, (store, count) in enumerate(store_counts.head(10).items()):
        print(f"   {i+1:2d}. Store {store}: {count} massive outliers")
    
    print(f"\n📊 SPU PATTERNS IN MASSIVE OUTLIERS:")
    spu_counts = massive_qty['item_type'].value_counts()
    print(f"   Item types with massive outliers:")
    for item_type, count in spu_counts.items():
        print(f"   • {item_type}: {count} cases")
    
    # Rule breakdown
    print(f"\n📊 RULE BREAKDOWN IN MASSIVE OUTLIERS:")
    rule_counts = massive_qty['rule'].value_counts()
    for rule, count in rule_counts.items():
        print(f"   • {rule}: {count} cases")
    
    return massive_qty, extreme_qty, high_qty, high_inv

if __name__ == "__main__":
    create_outlier_lists()
    print("\n✅ Outlier lists created successfully!") 