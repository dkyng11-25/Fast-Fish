#!/usr/bin/env python3
"""
Focused audit script to check the main extraction CSV for data quality issues.
Specifically checks for:
1. Rule 10 duplicate entries (same store+SPU)
2. Unrealistic unit quantities 
3. Data consistency and quality
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from collections import defaultdict, Counter

def audit_extraction_csv() -> None:
    """Perform comprehensive audit of the main extraction CSV."""
    
    csv_file = 'output/all_rule_suggestions.csv'
    print(f"🔍 Auditing: {csv_file}")
    print("=" * 80)
    
    try:
        df = pd.read_csv(csv_file)
        print(f"✅ Loaded: {len(df):,} total records")
        print(f"📊 Columns: {list(df.columns)}")
        
        # Rule distribution
        print(f"\n📊 RULE DISTRIBUTION:")
        rule_dist = df['rule'].value_counts()
        for rule, count in rule_dist.items():
            print(f"   {rule}: {count:,} records ({count/len(df)*100:.1f}%)")
        
        # Check for Rule 10 duplicates specifically
        print(f"\n🔍 RULE 10 DUPLICATE ANALYSIS:")
        rule10_data = df[df['rule'].str.contains('Rule 10', na=False)]
        
        if len(rule10_data) > 0:
            print(f"   Total Rule 10 records: {len(rule10_data):,}")
            
            # Check for duplicates by store+SPU
            rule10_groups = rule10_data.groupby(['store_code', 'spu_code']).size()
            duplicates = rule10_groups[rule10_groups > 1]
            
            print(f"   Unique store+SPU combinations: {len(rule10_groups):,}")
            print(f"   Duplicate store+SPU combinations: {len(duplicates):,}")
            
            if len(duplicates) > 0:
                print(f"⚠️  FOUND {len(duplicates)} DUPLICATE RULE 10 COMBINATIONS!")
                print("   Top 10 examples:")
                for i, ((store, spu), count) in enumerate(duplicates.head(10).items()):
                    print(f"     {i+1}. Store {store}, SPU {spu}: {count} records")
                    sample = rule10_data[(rule10_data['store_code'] == store) & 
                                       (rule10_data['spu_code'] == spu)]
                    for _, row in sample.iterrows():
                        print(f"        Current: {row['current_quantity']:.2f}, "
                              f"Change: {row['recommended_quantity_change']:.2f}, "
                              f"Investment: ${row['investment_required']:.2f}")
            else:
                print("✅ No Rule 10 duplicates found!")
        
        # Check quantities across all rules
        print(f"\n📊 QUANTITY ANALYSIS:")
        
        # Overall quantity statistics
        qty_stats = df['current_quantity'].describe()
        print(f"   Current Quantity Statistics:")
        print(f"     Min: {qty_stats['min']:.2f}")
        print(f"     Max: {qty_stats['max']:.2f}")
        print(f"     Mean: {qty_stats['mean']:.2f}")
        print(f"     75th percentile: {qty_stats['75%']:.2f}")
        
        # Check for unrealistic quantities
        thresholds = [50, 100, 200, 500, 1000]
        print(f"\n   Records with high quantities:")
        for threshold in thresholds:
            high_qty = df[df['current_quantity'] > threshold]
            print(f"     > {threshold} units: {len(high_qty):,} records ({len(high_qty)/len(df)*100:.2f}%)")
        
        # Detailed analysis of highest quantities
        print(f"\n   TOP 20 HIGHEST QUANTITIES:")
        top_quantities = df.nlargest(20, 'current_quantity')
        for i, (_, row) in enumerate(top_quantities.iterrows()):
            print(f"     {i+1:2d}. Store {row['store_code']}, SPU {row['spu_code']}: "
                  f"{row['current_quantity']:.1f} units ({row['rule']})")
        
        # Quantity distribution by rule
        print(f"\n📊 QUANTITY DISTRIBUTION BY RULE:")
        for rule in df['rule'].unique():
            rule_data = df[df['rule'] == rule]
            stats = rule_data['current_quantity'].describe()
            over_100 = (rule_data['current_quantity'] > 100).sum()
            over_50 = (rule_data['current_quantity'] > 50).sum()
            print(f"   {rule}:")
            print(f"     Count: {len(rule_data):,}, Max: {stats['max']:.1f}, "
                  f"Mean: {stats['mean']:.1f}, >50: {over_50}, >100: {over_100}")
        
        # Unit price analysis
        print(f"\n💰 UNIT PRICE ANALYSIS:")
        price_stats = df['unit_price'].describe()
        print(f"   Price Statistics:")
        print(f"     Min: ${price_stats['min']:.2f}")
        print(f"     Max: ${price_stats['max']:.2f}")
        print(f"     Mean: ${price_stats['mean']:.2f}")
        
        # Check for unusual prices
        low_prices = df[df['unit_price'] < 10]
        high_prices = df[df['unit_price'] > 500]
        print(f"   Unusual prices:")
        print(f"     < $10: {len(low_prices):,} records")
        print(f"     > $500: {len(high_prices):,} records")
        
        # Investment analysis
        print(f"\n💰 INVESTMENT ANALYSIS:")
        total_investment = df['investment_required'].sum()
        print(f"   Total Investment: ${total_investment:,.2f}")
        
        investment_by_rule = df.groupby('rule')['investment_required'].sum().sort_values(ascending=False)
        print(f"   Investment by rule:")
        for rule, amount in investment_by_rule.items():
            print(f"     {rule}: ${amount:,.2f}")
        
        # Check investment calculation accuracy
        print(f"\n🔍 INVESTMENT CALCULATION CHECK:")
        df['calculated_investment'] = df['recommended_quantity_change'] * df['unit_price']
        df['investment_diff'] = abs(df['calculated_investment'] - df['investment_required'])
        incorrect = df[df['investment_diff'] > 0.01]  # Allow for rounding
        
        if len(incorrect) > 0:
            print(f"⚠️  Found {len(incorrect):,} records with incorrect investment calculations")
            print("   Top 5 examples:")
            for i, (_, row) in enumerate(incorrect.head(5).iterrows()):
                print(f"     {i+1}. Store {row['store_code']}, SPU {row['spu_code']}: "
                      f"Expected ${row['calculated_investment']:.2f}, "
                      f"Got ${row['investment_required']:.2f}")
        else:
            print("✅ All investment calculations are correct!")
        
        # Store and SPU coverage
        print(f"\n📍 COVERAGE ANALYSIS:")
        unique_stores = df['store_code'].nunique()
        unique_spus = df['spu_code'].nunique()
        print(f"   Unique stores: {unique_stores:,}")
        print(f"   Unique SPUs: {unique_spus:,}")
        
        # Rules per store
        rules_per_store = df.groupby('store_code')['rule'].nunique()
        print(f"   Rules per store distribution:")
        rule_counts = rules_per_store.value_counts().sort_index()
        for num_rules, store_count in rule_counts.items():
            print(f"     {num_rules} rules: {store_count:,} stores")
        
        # Action analysis
        print(f"\n🎯 ACTION ANALYSIS:")
        action_dist = df['action'].value_counts()
        for action, count in action_dist.items():
            print(f"   {action}: {count:,} records ({count/len(df)*100:.1f}%)")
        
        # Final summary
        print(f"\n" + "=" * 80)
        print(f"📊 AUDIT SUMMARY")
        print(f"=" * 80)
        
        issues_found = []
        
        # Check for duplicates
        if len(duplicates) > 0:
            issues_found.append(f"{len(duplicates)} Rule 10 duplicate store+SPU combinations")
        
        # Check for very high quantities (potential currency amounts)
        very_high = df[df['current_quantity'] > 200]
        if len(very_high) > 0:
            issues_found.append(f"{len(very_high)} records with >200 units (potentially unrealistic)")
        
        # Check for negative investments (should only be Rule 10)
        negative_investment = df[df['investment_required'] < 0]
        non_rule10_negative = negative_investment[~negative_investment['rule'].str.contains('Rule 10', na=False)]
        if len(non_rule10_negative) > 0:
            issues_found.append(f"{len(non_rule10_negative)} non-Rule 10 records with negative investment")
        
        if len(issues_found) == 0:
            print("🎉 NO CRITICAL ISSUES FOUND!")
            print("   ✅ No Rule 10 duplicates")
            print("   ✅ Quantities appear realistic")
            print("   ✅ Investment calculations correct")
        else:
            print("⚠️  ISSUES FOUND:")
            for issue in issues_found:
                print(f"   • {issue}")
        
        print(f"\n📈 DATA QUALITY SCORE: {max(0, 100 - len(issues_found)*20)}/100")
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")

def main():
    """Run the focused audit."""
    print("🚀 Starting Focused Audit of Extraction CSV")
    audit_extraction_csv()

if __name__ == "__main__":
    main() 