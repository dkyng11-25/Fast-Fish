#!/usr/bin/env python3
"""
Comprehensive audit script to check data quality across all rule files.
Verifies:
1. No duplicate Rule 10 entries (same store+SPU)
2. Realistic unit quantities (not currency amounts)
3. Column standardization
4. Investment calculations
5. Data consistency across consolidated results
"""

import pandas as pd
import numpy as np
import os
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import glob
from tqdm import tqdm

def audit_rule_file(rule_file: str, rule_number: int) -> Dict[str, Any]:
    """
    Audit a single rule file for data quality issues.
    
    Args:
        rule_file (str): Path to the rule file
        rule_number (int): Rule number (7-12)
    
    Returns:
        Dict[str, Any]: Audit results for this rule
    """
    print(f"\n🔍 Auditing Rule {rule_number}: {rule_file}")
    
    if not os.path.exists(rule_file):
        return {
            'rule_number': rule_number,
            'file_exists': False,
            'error': f"File not found: {rule_file}"
        }
    
    try:
        df = pd.read_csv(rule_file)
        
        audit_results = {
            'rule_number': rule_number,
            'file_exists': True,
            'total_records': len(df),
            'columns': list(df.columns),
            'missing_standard_columns': [],
            'duplicate_store_spu': 0,
            'unrealistic_quantities': [],
            'investment_issues': [],
            'unit_price_issues': [],
            'sample_records': df.head(3).to_dict('records') if len(df) > 0 else []
        }
        
        # Check for standard columns
        expected_columns = ['str_code', 'spu_code', 'current_quantity', 
                          'recommended_quantity_change', 'unit_price', 'investment_required']
        
        for col in expected_columns:
            if col not in df.columns:
                audit_results['missing_standard_columns'].append(col)
        
        # Check for duplicates (same store + SPU combination)
        if 'str_code' in df.columns and 'spu_code' in df.columns:
            duplicates = df.groupby(['str_code', 'spu_code']).size()
            duplicate_count = (duplicates > 1).sum()
            audit_results['duplicate_store_spu'] = duplicate_count
            
            if duplicate_count > 0:
                print(f"⚠️  Found {duplicate_count} duplicate store+SPU combinations in Rule {rule_number}")
                # Show examples of duplicates
                duplicate_examples = duplicates[duplicates > 1].head(5)
                for (store, spu), count in duplicate_examples.items():
                    print(f"   Store {store}, SPU {spu}: {count} records")
                    sample_dups = df[(df['str_code'] == store) & (df['spu_code'] == spu)]
                    print(f"   Sample: {sample_dups[['current_quantity', 'recommended_quantity_change']].values.tolist()}")
        
        # Check for unrealistic quantities (potential currency amounts used as quantities)
        if 'current_quantity' in df.columns:
            high_quantities = df[df['current_quantity'] > 100]  # More than 100 units is suspicious
            if len(high_quantities) > 0:
                audit_results['unrealistic_quantities'] = [
                    {
                        'store': row['str_code'],
                        'spu': row['spu_code'],
                        'current_qty': row['current_quantity'],
                        'change': row.get('recommended_quantity_change', 'N/A')
                    }
                    for _, row in high_quantities.head(10).iterrows()
                ]
                print(f"⚠️  Found {len(high_quantities)} records with quantities > 100 units")
        
        # Check unit prices
        if 'unit_price' in df.columns:
            unit_prices = df['unit_price'].dropna()
            if len(unit_prices) > 0:
                low_prices = unit_prices[unit_prices < 10]  # Less than $10
                high_prices = unit_prices[unit_prices > 1000]  # More than $1000
                
                if len(low_prices) > 0:
                    audit_results['unit_price_issues'].append(f"{len(low_prices)} prices < $10")
                if len(high_prices) > 0:
                    audit_results['unit_price_issues'].append(f"{len(high_prices)} prices > $1000")
                
                print(f"   Unit prices: ${unit_prices.min():.2f} - ${unit_prices.max():.2f} (avg: ${unit_prices.mean():.2f})")
        
        # Check investment calculations
        if all(col in df.columns for col in ['recommended_quantity_change', 'unit_price', 'investment_required']):
            df_calc = df.dropna(subset=['recommended_quantity_change', 'unit_price', 'investment_required'])
            if len(df_calc) > 0:
                calculated_investment = df_calc['recommended_quantity_change'] * df_calc['unit_price']
                investment_diff = abs(calculated_investment - df_calc['investment_required'])
                incorrect_investments = investment_diff > 0.01  # Allow for rounding
                
                if incorrect_investments.sum() > 0:
                    audit_results['investment_issues'].append(f"{incorrect_investments.sum()} incorrect investment calculations")
                    print(f"⚠️  Found {incorrect_investments.sum()} incorrect investment calculations")
        
        return audit_results
        
    except Exception as e:
        return {
            'rule_number': rule_number,
            'file_exists': True,
            'error': str(e)
        }

def find_rule_files() -> Dict[int, str]:
    """Find all available rule files."""
    rule_files = {}
    
    # Pattern to match rule files
    patterns = [
        'output/rule*_results.csv',
        'output/rule*_opportunities.csv', 
        'output/rule*_cases.csv',
        'output/rule*_details.csv'
    ]
    
    for pattern in patterns:
        files = glob.glob(pattern)
        for file in files:
            # Extract rule number from filename
            filename = os.path.basename(file)
            if 'rule' in filename:
                try:
                    rule_num = int(filename.split('rule')[1].split('_')[0])
                    if rule_num not in rule_files:
                        rule_files[rule_num] = file
                except:
                    continue
    
    return rule_files

def check_extraction_csv() -> Dict[str, Any]:
    """Check the main extraction CSV file."""
    print("\n🔍 Auditing Main Extraction CSV")
    
    csv_file = 'output/all_rule_suggestions.csv'
    if not os.path.exists(csv_file):
        return {'error': 'Extraction CSV not found'}
    
    try:
        df = pd.read_csv(csv_file)
        print(f"✅ Main CSV: {len(df):,} total records")
        
        # Rule distribution
        rule_dist = df['rule_type'].value_counts()
        print("\n📊 Rule Distribution:")
        for rule, count in rule_dist.items():
            print(f"   {rule}: {count:,} records ({count/len(df)*100:.1f}%)")
        
        # Check for Rule 10 duplicates specifically
        rule10_data = df[df['rule_type'] == 'Rule 10']
        if len(rule10_data) > 0:
            rule10_duplicates = rule10_data.groupby(['str_code', 'spu_code']).size()
            rule10_duplicate_count = (rule10_duplicates > 1).sum()
            print(f"\n🔍 Rule 10 Analysis:")
            print(f"   Total Rule 10 records: {len(rule10_data):,}")
            print(f"   Duplicate store+SPU combinations: {rule10_duplicate_count}")
            
            if rule10_duplicate_count > 0:
                print("   Examples of duplicates:")
                for (store, spu), count in rule10_duplicates[rule10_duplicates > 1].head(5).items():
                    print(f"     Store {store}, SPU {spu}: {count} records")
                    sample_dups = rule10_data[(rule10_data['str_code'] == store) & (rule10_data['spu_code'] == spu)]
                    print(f"     Details: {sample_dups[['current_quantity', 'recommended_quantity_change', 'unit_price']].values.tolist()}")
        
        # Check unit quantities across all rules
        print(f"\n📊 Quantity Analysis:")
        high_qty = df[df['current_quantity'] > 100]
        if len(high_qty) > 0:
            print(f"⚠️  High Quantities (>100 units): {len(high_qty)} records")
            print("   Top 10 highest quantities:")
            top_high = high_qty.nlargest(10, 'current_quantity')
            for _, row in top_high.iterrows():
                print(f"     Store {row['str_code']}, SPU {row['spu_code']}: {row['current_quantity']:.1f} units ({row['rule_type']})")
        else:
            print("✅ No unrealistic quantities found (all ≤ 100 units)")
        
        # Check quantity distribution by rule
        print(f"\n📊 Quantity Distribution by Rule:")
        for rule in df['rule_type'].unique():
            rule_data = df[df['rule_type'] == rule]
            max_qty = rule_data['current_quantity'].max()
            mean_qty = rule_data['current_quantity'].mean()
            over_100 = (rule_data['current_quantity'] > 100).sum()
            print(f"   {rule}: Max={max_qty:.1f}, Mean={mean_qty:.1f}, >100 units: {over_100}")
        
        # Investment summary
        total_investment = df['investment_required'].sum()
        print(f"\n💰 Total Investment: ${total_investment:,.2f}")
        
        investment_by_rule = df.groupby('rule_type')['investment_required'].sum()
        print("   Investment by rule:")
        for rule, amount in investment_by_rule.items():
            print(f"     {rule}: ${amount:,.2f}")
        
        return {
            'total_records': len(df),
            'rule_distribution': rule_dist.to_dict(),
            'rule10_duplicates': rule10_duplicate_count if 'rule10_duplicate_count' in locals() else 0,
            'high_quantities': len(high_qty),
            'total_investment': total_investment
        }
        
    except Exception as e:
        return {'error': str(e)}

def main():
    """Run comprehensive audit of all rule files and results."""
    print("🚀 Starting Comprehensive Audit of SPU Rule Files")
    print("=" * 60)
    
    # Auto-discover rule files
    rule_files = find_rule_files()
    print(f"📋 Found rule files: {list(rule_files.keys())}")
    
    all_audit_results = {}
    
    # Audit individual rule files
    print("\n📋 PHASE 1: Individual Rule File Audit")
    for rule_num, file_path in rule_files.items():
        audit_result = audit_rule_file(file_path, rule_num)
        all_audit_results[f'rule_{rule_num}'] = audit_result
    
    # Audit main extraction CSV
    print("\n📋 PHASE 2: Main Extraction CSV Audit")
    extraction_audit = check_extraction_csv()
    all_audit_results['extraction'] = extraction_audit
    
    # Summary report
    print("\n" + "=" * 60)
    print("📊 AUDIT SUMMARY REPORT")
    print("=" * 60)
    
    total_issues = 0
    
    for rule_num in sorted(rule_files.keys()):
        rule_key = f'rule_{rule_num}'
        if rule_key in all_audit_results:
            result = all_audit_results[rule_key]
            if result['file_exists']:
                issues = []
                if result.get('duplicate_store_spu', 0) > 0:
                    issues.append(f"{result['duplicate_store_spu']} duplicates")
                if result.get('unrealistic_quantities'):
                    issues.append(f"{len(result['unrealistic_quantities'])} high quantities")
                if result.get('missing_standard_columns'):
                    issues.append(f"missing columns: {result['missing_standard_columns']}")
                if result.get('investment_issues'):
                    issues.append("investment calculation errors")
                
                if issues:
                    print(f"⚠️  Rule {rule_num}: {', '.join(issues)}")
                    total_issues += len(issues)
                else:
                    print(f"✅ Rule {rule_num}: No issues found")
            else:
                print(f"❌ Rule {rule_num}: File not found")
                total_issues += 1
    
    if 'extraction' in all_audit_results and 'error' not in all_audit_results['extraction']:
        ext_result = all_audit_results['extraction']
        if ext_result.get('rule10_duplicates', 0) > 0:
            print(f"⚠️  Extraction CSV: {ext_result['rule10_duplicates']} Rule 10 duplicates")
            total_issues += 1
        if ext_result.get('high_quantities', 0) > 0:
            print(f"⚠️  Extraction CSV: {ext_result['high_quantities']} high quantities")
            total_issues += 1
    
    print(f"\n🎯 FINAL RESULT: {total_issues} issues found")
    
    if total_issues == 0:
        print("🎉 All checks passed! Data quality looks good.")
    else:
        print("🔧 Issues found that may need attention.")
    
    # Save detailed audit report
    import json
    with open('comprehensive_audit_report.json', 'w') as f:
        json.dump(all_audit_results, f, indent=2, default=str)
    print(f"\n📄 Detailed audit report saved to: comprehensive_audit_report.json")

if __name__ == "__main__":
    main() 