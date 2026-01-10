#!/usr/bin/env python3
"""
High Quantity Analysis Script
Analyzes high quantity records to determine if they're legitimate or data quality issues.
Examines:
1. Item types and categories with high quantities
2. Store characteristics and patterns
3. Sales normalization to identify true outliers
4. Geographic and cluster distribution
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from collections import Counter
import re

def analyze_high_quantities() -> None:
    """Perform detailed analysis of high quantity records."""
    
    csv_file = 'output/all_rule_suggestions.csv'
    print(f"🔍 Analyzing High Quantities in: {csv_file}")
    print("=" * 80)
    
    try:
        df = pd.read_csv(csv_file)
        print(f"✅ Loaded: {len(df):,} total records")
        
        # Define high quantity thresholds for analysis
        thresholds = [100, 200, 500, 1000]
        
        for threshold in thresholds:
            print(f"\n📊 ANALYSIS FOR QUANTITIES > {threshold} UNITS")
            print("-" * 50)
            
            high_qty = df[df['current_quantity'] > threshold]
            if len(high_qty) == 0:
                print(f"   No records found above {threshold} units")
                continue
                
            print(f"   Total records: {len(high_qty):,} ({len(high_qty)/len(df)*100:.2f}% of all)")
            
            # Rule distribution
            print(f"\n   📋 Rule Distribution:")
            rule_dist = high_qty['rule'].value_counts()
            for rule, count in rule_dist.items():
                print(f"     {rule}: {count:,} records ({count/len(high_qty)*100:.1f}%)")
            
            # SPU/Item type analysis
            print(f"\n   🏷️  SPU/Item Analysis:")
            
            # Extract item types from SPU codes (after the underscore)
            high_qty['item_type'] = high_qty['spu_code'].str.split('_').str[1]
            item_types = high_qty['item_type'].value_counts()
            
            print(f"     Top 10 item types:")
            for item, count in item_types.head(10).items():
                avg_qty = high_qty[high_qty['item_type'] == item]['current_quantity'].mean()
                max_qty = high_qty[high_qty['item_type'] == item]['current_quantity'].max()
                print(f"       {item}: {count:,} records, avg: {avg_qty:.1f}, max: {max_qty:.1f}")
            
            # Store analysis
            print(f"\n   🏪 Store Analysis:")
            store_counts = high_qty['store_code'].value_counts()
            print(f"     Stores with high quantities: {len(store_counts):,}")
            print(f"     Top 10 stores by record count:")
            
            for store, count in store_counts.head(10).items():
                store_data = high_qty[high_qty['store_code'] == store]
                avg_qty = store_data['current_quantity'].mean()
                max_qty = store_data['current_quantity'].max()
                unique_items = store_data['item_type'].nunique()
                print(f"       Store {store}: {count:,} records, {unique_items} item types, "
                      f"avg: {avg_qty:.1f}, max: {max_qty:.1f}")
            
            # Price analysis for context
            print(f"\n   💰 Price Context:")
            price_stats = high_qty['unit_price'].describe()
            print(f"     Unit prices: ${price_stats['min']:.2f} - ${price_stats['max']:.2f} "
                  f"(avg: ${price_stats['mean']:.2f})")
            
            # Calculate sales value equivalent
            high_qty['sales_value_equivalent'] = high_qty['current_quantity'] * high_qty['unit_price']
            sales_stats = high_qty['sales_value_equivalent'].describe()
            print(f"     Sales value equivalent: ${sales_stats['min']:.2f} - ${sales_stats['max']:.2f} "
                  f"(avg: ${sales_stats['mean']:.2f})")
        
        # Detailed analysis of extreme outliers (>1000 units)
        print(f"\n" + "=" * 80)
        print(f"🚨 EXTREME OUTLIER ANALYSIS (>1000 UNITS)")
        print("=" * 80)
        
        extreme_outliers = df[df['current_quantity'] > 1000]
        if len(extreme_outliers) > 0:
            print(f"Found {len(extreme_outliers):,} extreme outliers")
            
            # Detailed breakdown of each extreme case
            print(f"\n📋 DETAILED BREAKDOWN:")
            for i, (_, row) in enumerate(extreme_outliers.iterrows()):
                sales_value = row['current_quantity'] * row['unit_price']
                print(f"\n   {i+1:2d}. Store {row['store_code']}")
                print(f"       SPU: {row['spu_code']}")
                print(f"       Item: {row['spu_code'].split('_')[1] if '_' in row['spu_code'] else 'Unknown'}")
                print(f"       Quantity: {row['current_quantity']:.1f} units")
                print(f"       Unit Price: ${row['unit_price']:.2f}")
                print(f"       Sales Value: ${sales_value:,.2f}")
                print(f"       Rule: {row['rule']}")
                print(f"       Action: {row['action']} by {row['recommended_quantity_change']:.1f}")
        
        # Sales normalization analysis
        print(f"\n" + "=" * 80)
        print(f"📈 SALES NORMALIZATION ANALYSIS")
        print("=" * 80)
        
        # For Rule 10 (overcapacity), we can infer sales performance from the quantities
        rule10_data = df[df['rule'].str.contains('Rule 10', na=False)].copy()
        
        if len(rule10_data) > 0:
            print(f"Analyzing {len(rule10_data):,} Rule 10 records for sales context...")
            
            # Calculate sales density (sales value per unit held)
            rule10_data['sales_density'] = rule10_data['unit_price']  # This is our proxy
            
            # Group by item type for comparison
            rule10_data['item_type'] = rule10_data['spu_code'].str.split('_').str[1]
            
            print(f"\n📊 Sales Density by Item Type (Rule 10 only):")
            item_analysis = rule10_data.groupby('item_type').agg({
                'current_quantity': ['count', 'mean', 'max'],
                'unit_price': ['mean', 'min', 'max'],
                'sales_density': 'mean'
            }).round(2)
            
            # Flatten column names
            item_analysis.columns = ['_'.join(col).strip() for col in item_analysis.columns]
            item_analysis = item_analysis.sort_values('current_quantity_mean', ascending=False)
            
            print(f"   Top 15 item types by average quantity:")
            for item in item_analysis.head(15).index:
                row = item_analysis.loc[item]
                print(f"     {item:20s}: {row['current_quantity_count']:4.0f} stores, "
                      f"avg: {row['current_quantity_mean']:6.1f} units, "
                      f"max: {row['current_quantity_max']:6.1f}, "
                      f"price: ${row['unit_price_mean']:5.2f}")
        
        # Statistical outlier detection
        print(f"\n📊 STATISTICAL OUTLIER DETECTION:")
        
        for rule in df['rule'].unique():
            rule_data = df[df['rule'] == rule]
            if len(rule_data) == 0:
                continue
                
            quantities = rule_data['current_quantity']
            
            # Calculate IQR-based outliers
            Q1 = quantities.quantile(0.25)
            Q3 = quantities.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = rule_data[quantities > upper_bound]
            extreme_outliers = rule_data[quantities > Q3 + 3 * IQR]  # 3*IQR for extreme
            
            print(f"\n   {rule}:")
            print(f"     Total records: {len(rule_data):,}")
            print(f"     Q1: {Q1:.1f}, Q3: {Q3:.1f}, IQR: {IQR:.1f}")
            print(f"     Upper bound (Q3 + 1.5*IQR): {upper_bound:.1f}")
            print(f"     Statistical outliers: {len(outliers):,} ({len(outliers)/len(rule_data)*100:.2f}%)")
            print(f"     Extreme outliers (Q3 + 3*IQR): {len(extreme_outliers):,}")
            
            if len(extreme_outliers) > 0:
                print(f"     Extreme outlier examples:")
                for _, row in extreme_outliers.head(5).iterrows():
                    item_type = row['spu_code'].split('_')[1] if '_' in row['spu_code'] else 'Unknown'
                    print(f"       Store {row['store_code']}, {item_type}: {row['current_quantity']:.1f} units")
        
        # Final assessment
        print(f"\n" + "=" * 80)
        print(f"🎯 ASSESSMENT & RECOMMENDATIONS")
        print("=" * 80)
        
        # Check if high quantities are concentrated in specific patterns
        high_qty_all = df[df['current_quantity'] > 200]
        
        if len(high_qty_all) > 0:
            # Pattern analysis
            item_concentration = high_qty_all['spu_code'].str.split('_').str[1].value_counts()
            rule_concentration = high_qty_all['rule'].value_counts()
            
            print(f"📋 Pattern Analysis for >200 units ({len(high_qty_all):,} records):")
            print(f"   Top item causing high quantities: {item_concentration.index[0]} ({item_concentration.iloc[0]:,} records)")
            print(f"   Rule with most high quantities: {rule_concentration.index[0]} ({rule_concentration.iloc[0]:,} records)")
            
            # Check if it's legitimate business pattern or data issue
            if rule_concentration.iloc[0] / len(high_qty_all) > 0.95:  # >95% from one rule
                print(f"   🔍 HIGH CONCENTRATION in one rule - possible data quality issue")
            
            if item_concentration.iloc[0] / len(high_qty_all) > 0.8:  # >80% from one item
                print(f"   🔍 HIGH CONCENTRATION in one item type - investigate further")
            
            # Sales value assessment
            avg_sales_value = (high_qty_all['current_quantity'] * high_qty_all['unit_price']).mean()
            print(f"   💰 Average sales value for high qty items: ${avg_sales_value:,.2f}")
            
            if avg_sales_value > 50000:  # >$50k inventory per item
                print(f"   ⚠️  Very high inventory values - verify if realistic for business")
        
        print(f"\n✅ Analysis complete. Review patterns above to determine data quality.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run the high quantity analysis."""
    print("🚀 Starting High Quantity Contextual Analysis")
    analyze_high_quantities()

if __name__ == "__main__":
    main() 