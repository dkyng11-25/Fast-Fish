#!/usr/bin/env python3
"""
Comprehensive Outlier Analysis Script
Compiles a detailed list of stores and SPUs with strange outliers.
Analyzes patterns, source data, and provides business context for investigation.
"""

import pandas as pd
import numpy as np
import json
import os
from typing import Dict, List, Tuple, Any
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_outliers() -> None:
    """Comprehensive outlier analysis and compilation."""
    
    print("🔍 COMPREHENSIVE OUTLIER ANALYSIS")
    print("=" * 80)
    
    # Load the main extraction CSV
    csv_file = 'output/all_rule_suggestions.csv'
    df = pd.read_csv(csv_file)
    
    # Load Rule 10 detailed data
    rule10_file = 'output/rule10_spu_overcapacity_opportunities.csv'
    rule10_df = pd.read_csv(rule10_file)
    
    print(f"✅ Loaded {len(df):,} total suggestions")
    print(f"✅ Loaded {len(rule10_df):,} Rule 10 detailed records")
    
    # Define outlier thresholds
    thresholds = {
        'high_quantity': 200,      # >200 units suspicious
        'extreme_quantity': 500,   # >500 units very suspicious  
        'massive_quantity': 1000,  # >1000 units requires investigation
        'high_investment': 10000,  # >$10k investment per suggestion
        'extreme_investment': 50000 # >$50k investment per suggestion
    }
    
    outliers = {
        'high_quantity': [],
        'extreme_quantity': [],
        'massive_quantity': [],
        'high_investment': [],
        'extreme_investment': [],
        'rule10_breakdown': [],
        'source_data_analysis': []
    }
    
    # 1. QUANTITY OUTLIERS
    print(f"\n📊 ANALYZING QUANTITY OUTLIERS")
    print("-" * 50)
    
    for threshold_name, threshold_value in [
        ('high_quantity', thresholds['high_quantity']),
        ('extreme_quantity', thresholds['extreme_quantity']),
        ('massive_quantity', thresholds['massive_quantity'])
    ]:
        
        high_qty = df[df['current_quantity'] > threshold_value].copy()
        print(f"   {threshold_name.replace('_', ' ').title()}: {len(high_qty)} cases (>{threshold_value} units)")
        
        if len(high_qty) > 0:
            # Add analysis columns
            high_qty['item_type'] = high_qty['spu_code'].str.split('_').str[1]
            high_qty['sales_value'] = high_qty['current_quantity'] * high_qty['unit_price']
            
            # Compile outlier details
            for _, row in high_qty.iterrows():
                outlier_record = {
                    'threshold_type': threshold_name,
                    'rule': row['rule'],
                    'store_code': row['store_code'],
                    'spu_code': row['spu_code'],
                    'item_type': row['item_type'],
                    'current_quantity': row['current_quantity'],
                    'unit_price': row['unit_price'],
                    'sales_value': row['sales_value'],
                    'investment_required': row['investment_required'],
                    'action': row['action'],
                    'recommended_change': row['recommended_quantity_change']
                }
                outliers[threshold_name].append(outlier_record)
    
    # 2. INVESTMENT OUTLIERS
    print(f"\n💰 ANALYZING INVESTMENT OUTLIERS")
    print("-" * 50)
    
    for threshold_name, threshold_value in [
        ('high_investment', thresholds['high_investment']),
        ('extreme_investment', thresholds['extreme_investment'])
    ]:
        
        high_inv = df[abs(df['investment_required']) > threshold_value].copy()
        print(f"   {threshold_name.replace('_', ' ').title()}: {len(high_inv)} cases (>${threshold_value:,})")
        
        if len(high_inv) > 0:
            high_inv['item_type'] = high_inv['spu_code'].str.split('_').str[1]
            high_inv['abs_investment'] = abs(high_inv['investment_required'])
            
            for _, row in high_inv.iterrows():
                outlier_record = {
                    'threshold_type': threshold_name,
                    'rule': row['rule'],
                    'store_code': row['store_code'],
                    'spu_code': row['spu_code'],
                    'item_type': row['item_type'],
                    'current_quantity': row['current_quantity'],
                    'unit_price': row['unit_price'],
                    'investment_required': row['investment_required'],
                    'abs_investment': row['abs_investment'],
                    'action': row['action']
                }
                outliers[threshold_name].append(outlier_record)
    
    # 3. RULE 10 DETAILED BREAKDOWN ANALYSIS
    print(f"\n🔍 ANALYZING RULE 10 BREAKDOWN PATTERNS")
    print("-" * 50)
    
    # Focus on extreme Rule 10 cases
    rule10_extreme = df[(df['rule'].str.contains('Rule 10')) & (df['current_quantity'] > 500)].copy()
    print(f"   Rule 10 extreme cases (>500 units): {len(rule10_extreme)}")
    
    for _, row in rule10_extreme.iterrows():
        store_code = row['store_code']
        spu_pattern = row['spu_code'].split('_')[1] if '_' in row['spu_code'] else 'Unknown'
        
        # Find all Rule 10 detailed records for this store-SPU
        detailed_records = rule10_df[
            (rule10_df['str_code'].astype(str) == str(store_code)) & 
            (rule10_df['sub_cate_name'] == spu_pattern)
        ]
        
        if len(detailed_records) > 0:
            # Analyze the breakdown
            breakdown_analysis = {
                'store_code': store_code,
                'spu_pattern': spu_pattern,
                'total_quantity_in_extraction': row['current_quantity'],
                'total_records_in_rule10': len(detailed_records),
                'gender_breakdown': detailed_records['sex_name'].value_counts().to_dict(),
                'location_breakdown': detailed_records['display_location_name'].value_counts().to_dict(),
                'quantity_breakdown': [],
                'sales_amount_breakdown': [],
                'total_sales_amount': 0
            }
            
            # Detailed breakdown of each record
            for _, detail_row in detailed_records.iterrows():
                try:
                    # Parse JSON sales data
                    sales_data = json.loads(detail_row['sty_sal_amt']) if pd.notna(detail_row['sty_sal_amt']) else {}
                    total_sales = sum(float(v) for v in sales_data.values() if v > 0)
                    
                    record_detail = {
                        'gender': detail_row['sex_name'],
                        'location': detail_row['display_location_name'],
                        'current_quantity': detail_row['current_quantity'],
                        'total_sales_amount': total_sales,
                        'spu_count': detail_row['spus_with_sales'],
                        'reduction_recommended': detail_row['constrained_reduction']
                    }
                    
                    breakdown_analysis['quantity_breakdown'].append(record_detail)
                    breakdown_analysis['total_sales_amount'] += total_sales
                    
                except (json.JSONDecodeError, TypeError, ValueError):
                    continue
            
            outliers['rule10_breakdown'].append(breakdown_analysis)
    
    # 4. SOURCE DATA INVESTIGATION
    print(f"\n🔍 INVESTIGATING SOURCE DATA PATTERNS")
    print("-" * 50)
    
    # Load source SPU sales data
    source_files = [
        'data/api_data/complete_spu_sales_202506A.csv',
        'data/spu_store_mapping.csv'
    ]
    
    source_data_issues = []
    
    for source_file in source_files:
        if os.path.exists(source_file):
            try:
                source_df = pd.read_csv(source_file)
                print(f"   Analyzing {source_file}: {len(source_df):,} records")
                
                # Look for suspicious patterns in source data
                if 'spu_sales_amt' in source_df.columns:
                    # Check for very high sales amounts that match our outliers
                    high_sales = source_df[source_df['spu_sales_amt'] > 2000]
                    
                    if len(high_sales) > 0:
                        print(f"     Found {len(high_sales)} records with sales >$2000")
                        
                        # Check if these match our outlier stores
                        for _, row in high_sales.head(20).iterrows():  # Top 20 cases
                            source_issue = {
                                'source_file': source_file,
                                'store_code': row.get('str_code', 'Unknown'),
                                'spu_code': row.get('spu_code', 'Unknown'),
                                'item_type': row.get('sub_cate_name', 'Unknown'),
                                'sales_amount': row['spu_sales_amt'],
                                'quantity_in_source': row.get('quantity', 'N/A'),
                                'unit_price_in_source': row.get('unit_price', 'N/A'),
                                'matches_outlier': False  # Will check later
                            }
                            
                            # Check if this matches any of our quantity outliers
                            matching_outliers = df[
                                (df['store_code'].astype(str) == str(row.get('str_code', ''))) &
                                (df['current_quantity'] > 500)
                            ]
                            
                            if len(matching_outliers) > 0:
                                source_issue['matches_outlier'] = True
                                source_issue['outlier_quantity'] = matching_outliers['current_quantity'].iloc[0]
                            
                            source_data_issues.append(source_issue)
                
            except Exception as e:
                print(f"     Error analyzing {source_file}: {e}")
    
    outliers['source_data_analysis'] = source_data_issues
    
    # 5. COMPILE COMPREHENSIVE REPORT
    print(f"\n📋 COMPILING COMPREHENSIVE OUTLIER REPORT")
    print("-" * 50)
    
    # Create summary statistics
    summary_stats = {
        'total_suggestions': len(df),
        'total_outliers': len(outliers['high_quantity']) + len(outliers['high_investment']),
        'quantity_outliers': {
            'high': len(outliers['high_quantity']),
            'extreme': len(outliers['extreme_quantity']),
            'massive': len(outliers['massive_quantity'])
        },
        'investment_outliers': {
            'high': len(outliers['high_investment']),
            'extreme': len(outliers['extreme_investment'])
        },
        'rule10_breakdown_cases': len(outliers['rule10_breakdown']),
        'source_data_issues': len(outliers['source_data_analysis'])
    }
    
    # Save detailed outlier data
    save_outlier_reports(outliers, summary_stats)
    
    # Generate summary
    generate_outlier_summary(outliers, summary_stats)

def save_outlier_reports(outliers: Dict[str, List], summary_stats: Dict) -> None:
    """Save detailed outlier reports to CSV files."""
    
    print("💾 Saving detailed outlier reports...")
    
    # 1. Quantity Outliers Report
    all_qty_outliers = []
    for threshold in ['high_quantity', 'extreme_quantity', 'massive_quantity']:
        all_qty_outliers.extend(outliers[threshold])
    
    if all_qty_outliers:
        qty_df = pd.DataFrame(all_qty_outliers)
        qty_df = qty_df.sort_values('current_quantity', ascending=False)
        qty_df.to_csv('output/quantity_outliers_detailed.csv', index=False)
        print(f"   ✅ Quantity outliers: output/quantity_outliers_detailed.csv ({len(qty_df)} records)")
    
    # 2. Investment Outliers Report
    all_inv_outliers = []
    for threshold in ['high_investment', 'extreme_investment']:
        all_inv_outliers.extend(outliers[threshold])
    
    if all_inv_outliers:
        inv_df = pd.DataFrame(all_inv_outliers)
        inv_df = inv_df.sort_values('abs_investment', ascending=False)
        inv_df.to_csv('output/investment_outliers_detailed.csv', index=False)
        print(f"   ✅ Investment outliers: output/investment_outliers_detailed.csv ({len(inv_df)} records)")
    
    # 3. Rule 10 Breakdown Analysis
    if outliers['rule10_breakdown']:
        # Flatten the breakdown data for CSV
        breakdown_records = []
        for breakdown in outliers['rule10_breakdown']:
            base_record = {
                'store_code': breakdown['store_code'],
                'spu_pattern': breakdown['spu_pattern'],
                'total_quantity_in_extraction': breakdown['total_quantity_in_extraction'],
                'total_records_in_rule10': breakdown['total_records_in_rule10'],
                'total_sales_amount': breakdown['total_sales_amount']
            }
            
            # Add gender breakdown
            for gender, count in breakdown['gender_breakdown'].items():
                base_record[f'gender_{gender}_count'] = count
            
            # Add location breakdown  
            for location, count in breakdown['location_breakdown'].items():
                base_record[f'location_{location}_count'] = count
            
            breakdown_records.append(base_record)
        
        breakdown_df = pd.DataFrame(breakdown_records)
        breakdown_df.to_csv('output/rule10_breakdown_analysis.csv', index=False)
        print(f"   ✅ Rule 10 breakdown: output/rule10_breakdown_analysis.csv ({len(breakdown_df)} records)")
        
        # Also save detailed breakdown
        detailed_breakdown = []
        for breakdown in outliers['rule10_breakdown']:
            for detail in breakdown['quantity_breakdown']:
                record = {
                    'store_code': breakdown['store_code'],
                    'spu_pattern': breakdown['spu_pattern'],
                    **detail
                }
                detailed_breakdown.append(record)
        
        if detailed_breakdown:
            detail_df = pd.DataFrame(detailed_breakdown)
            detail_df.to_csv('output/rule10_detailed_breakdown.csv', index=False)
            print(f"   ✅ Rule 10 detailed breakdown: output/rule10_detailed_breakdown.csv ({len(detail_df)} records)")
    
    # 4. Source Data Issues
    if outliers['source_data_analysis']:
        source_df = pd.DataFrame(outliers['source_data_analysis'])
        source_df = source_df.sort_values('sales_amount', ascending=False)
        source_df.to_csv('output/source_data_issues.csv', index=False)
        print(f"   ✅ Source data issues: output/source_data_issues.csv ({len(source_df)} records)")
    
    # 5. Summary Statistics
    import json
    with open('output/outlier_summary_stats.json', 'w') as f:
        json.dump(summary_stats, f, indent=2)
    print(f"   ✅ Summary statistics: output/outlier_summary_stats.json")

def generate_outlier_summary(outliers: Dict[str, List], summary_stats: Dict) -> None:
    """Generate a comprehensive outlier summary report."""
    
    print(f"\n" + "=" * 80)
    print(f"📊 COMPREHENSIVE OUTLIER ANALYSIS SUMMARY")
    print("=" * 80)
    
    print(f"\n📈 OVERALL STATISTICS:")
    print(f"   Total suggestions analyzed: {summary_stats['total_suggestions']:,}")
    print(f"   Total outliers identified: {summary_stats['total_outliers']:,}")
    print(f"   Outlier percentage: {summary_stats['total_outliers']/summary_stats['total_suggestions']*100:.2f}%")
    
    print(f"\n📊 QUANTITY OUTLIERS:")
    print(f"   High quantity (>200 units): {summary_stats['quantity_outliers']['high']:,}")
    print(f"   Extreme quantity (>500 units): {summary_stats['quantity_outliers']['extreme']:,}")
    print(f"   Massive quantity (>1000 units): {summary_stats['quantity_outliers']['massive']:,}")
    
    print(f"\n💰 INVESTMENT OUTLIERS:")
    print(f"   High investment (>$10k): {summary_stats['investment_outliers']['high']:,}")
    print(f"   Extreme investment (>$50k): {summary_stats['investment_outliers']['extreme']:,}")
    
    print(f"\n🔍 RULE 10 ANALYSIS:")
    print(f"   Complex breakdown cases: {summary_stats['rule10_breakdown_cases']:,}")
    
    print(f"\n📋 SOURCE DATA ISSUES:")
    print(f"   Suspicious source records: {summary_stats['source_data_issues']:,}")
    
    # Top outliers by category
    if outliers['massive_quantity']:
        print(f"\n🚨 TOP 10 MASSIVE QUANTITY OUTLIERS:")
        massive_sorted = sorted(outliers['massive_quantity'], key=lambda x: x['current_quantity'], reverse=True)
        for i, outlier in enumerate(massive_sorted[:10]):
            print(f"   {i+1:2d}. Store {outlier['store_code']}, {outlier['item_type']}: "
                  f"{outlier['current_quantity']:.1f} units (${outlier['sales_value']:,.0f} value)")
    
    if outliers['rule10_breakdown']:
        print(f"\n🔍 TOP 5 COMPLEX RULE 10 BREAKDOWNS:")
        breakdown_sorted = sorted(outliers['rule10_breakdown'], 
                                key=lambda x: x['total_quantity_in_extraction'], reverse=True)
        for i, breakdown in enumerate(breakdown_sorted[:5]):
            print(f"   {i+1}. Store {breakdown['store_code']}, {breakdown['spu_pattern']}:")
            print(f"      Total quantity: {breakdown['total_quantity_in_extraction']:.1f} units")
            print(f"      Rule 10 records: {breakdown['total_records_in_rule10']}")
            print(f"      Sales amount: ${breakdown['total_sales_amount']:,.0f}")
            print(f"      Gender breakdown: {breakdown['gender_breakdown']}")
    
    print(f"\n🎯 RECOMMENDATIONS:")
    print(f"   1. Investigate massive quantity outliers (>1000 units)")
    print(f"   2. Verify source data for high sales amounts")
    print(f"   3. Check if Rule 10 breakdowns represent real business scenarios")
    print(f"   4. Consider implementing quantity caps for reasonableness")
    print(f"   5. Validate unit price calculations")
    
    print(f"\n📁 DETAILED REPORTS SAVED:")
    print(f"   • output/quantity_outliers_detailed.csv")
    print(f"   • output/investment_outliers_detailed.csv") 
    print(f"   • output/rule10_breakdown_analysis.csv")
    print(f"   • output/rule10_detailed_breakdown.csv")
    print(f"   • output/source_data_issues.csv")
    print(f"   • output/outlier_summary_stats.json")

def main():
    """Run the comprehensive outlier analysis."""
    print("🚀 Starting Comprehensive Outlier Analysis")
    analyze_outliers()
    print("\n✅ Comprehensive outlier analysis complete!")

if __name__ == "__main__":
    main() 