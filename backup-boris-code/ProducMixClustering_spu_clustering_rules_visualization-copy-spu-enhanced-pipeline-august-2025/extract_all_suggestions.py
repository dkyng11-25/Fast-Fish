#!/usr/bin/env python3
"""
Extract All Rule Suggestions to CSV
Creates a CSV with one row per rule-store-SPU-adjustment combination
"""

import os
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from tqdm import tqdm

def load_rule_files() -> Dict[str, pd.DataFrame]:
    """Load all rule detail files"""
    rule_files = {
        'Rule 7 - Missing SPU': 'output/rule7_missing_spu_opportunities.csv',
        'Rule 8 - Imbalanced': 'output/rule8_imbalanced_spu_cases.csv', 
        'Rule 9 - Below Minimum': 'output/rule9_below_minimum_spu_cases.csv',
        'Rule 10 - Overcapacity': 'output/rule10_spu_overcapacity_opportunities.csv',
        'Rule 11 - Missed Sales': 'output/rule11_improved_missed_sales_opportunity_spu_details.csv',
        'Rule 12 - Performance': 'output/rule12_sales_performance_spu_details.csv'
    }
    
    data = {}
    for rule_name, file_path in rule_files.items():
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            data[rule_name] = df
            print(f"✓ Loaded {rule_name}: {len(df)} records")
        else:
            print(f"✗ File not found: {file_path}")
            data[rule_name] = pd.DataFrame()
    
    return data

def extract_rule7_suggestions(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Extract Rule 7 - Missing SPU suggestions"""
    suggestions = []
    
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing Rule 7"):
        if pd.notna(row.get('recommended_quantity_change', 0)) and float(row.get('recommended_quantity_change', 0)) > 0:
            suggestions.append({
                'rule': 'Rule 7 - Missing SPU',
                'store_code': str(row['str_code']),
                'spu_code': str(row['spu_code']),
                'current_quantity': 0.0,  # Missing SPUs start at 0
                'recommended_quantity_change': float(row['recommended_quantity_change']),
                'target_quantity': float(row['recommended_quantity_change']),
                'unit_price': float(row.get('unit_price', 0)),
                'investment_required': float(row.get('investment_required', 0)),
                'action': 'ADD',
                'reason': 'Missing SPU opportunity',
                'rule_explanation': f"Add {row['recommended_quantity_change']:.1f} units (missing SPU)"
            })
    
    return suggestions

def extract_rule8_suggestions(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Extract Rule 8 - Imbalanced suggestions (includes both increases and decreases)"""
    suggestions = []
    
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing Rule 8"):
        if pd.notna(row.get('recommended_quantity_change', 0)):
            qty_change = float(row.get('recommended_quantity_change', 0))
            if qty_change != 0:  # Any change (including negative)
                suggestions.append({
                    'rule': 'Rule 8 - Imbalanced',
                    'store_code': str(row['str_code']),
                    'spu_code': str(row['spu_code']),
                    'current_quantity': float(row.get('current_quantity', 0)),
                    'recommended_quantity_change': qty_change,
                    'target_quantity': float(row.get('current_quantity', 0)) + qty_change,
                    'unit_price': float(row.get('unit_price', 0)),
                    'investment_required': float(row.get('investment_required', 0)),
                    'action': 'INCREASE' if qty_change > 0 else 'REDUCE',
                    'reason': 'Imbalanced assortment',
                    'rule_explanation': f"Adjust by {qty_change:+.1f} units (rebalancing imbalance)"
                })
    
    return suggestions

def extract_rule9_suggestions(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Extract Rule 9 - Below Minimum suggestions"""
    suggestions = []
    
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing Rule 9"):
        action = str(row.get('recommended_action', ''))
        if action != 'DISCONTINUE' and pd.notna(row.get('recommended_quantity_change', 0)):
            qty_change = float(row.get('recommended_quantity_change', 0))
            if qty_change > 0:  # Only increases
                suggestions.append({
                    'rule': 'Rule 9 - Below Minimum',
                    'store_code': str(row['str_code']),
                    'spu_code': str(row['spu_code']),
                    'current_quantity': float(row.get('current_quantity', 0)),
                    'recommended_quantity_change': qty_change,
                    'target_quantity': float(row.get('target_quantity', 0)),
                    'unit_price': float(row.get('unit_price', 0)),
                    'investment_required': float(row.get('investment_required', 0)),
                    'action': 'INCREASE',
                    'reason': 'Below minimum variety',
                    'rule_explanation': f"Increase by {qty_change:.1f} units (below minimum)"
                })
    
    return suggestions

def extract_rule10_suggestions(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Extract Rule 10 - Overcapacity suggestions (reductions) - AGGREGATED by store-SPU"""
    suggestions = []
    
    # CRITICAL FIX: Aggregate by store_code + spu_code (combine gender records)
    print("  🔧 Aggregating Rule 10 by store-SPU to avoid gender duplicates...")
    
    rule10_filtered = df[pd.notna(df['recommended_quantity_change']) & (df['recommended_quantity_change'] < 0)].copy()
    
    if len(rule10_filtered) == 0:
        return suggestions
    
    # Group by store + SPU and aggregate
    aggregated = rule10_filtered.groupby(['str_code', 'spu_code']).agg({
        'current_quantity': 'sum',  # Total current quantity across genders
        'recommended_quantity_change': 'sum',  # Total reduction across genders
        'unit_price': 'mean',  # Average unit price
        'investment_required': 'sum',  # Total cost savings
        'overcapacity_percentage': 'mean'  # Average overcapacity percentage
    }).reset_index()
    
    for _, row in tqdm(aggregated.iterrows(), total=len(aggregated), desc="Processing Rule 10 (Aggregated)"):
        qty_change = float(row['recommended_quantity_change'])
        suggestions.append({
            'rule': 'Rule 10 - Overcapacity',
            'store_code': str(row['str_code']),
            'spu_code': str(row['spu_code']),
            'current_quantity': float(row['current_quantity']),
            'recommended_quantity_change': qty_change,
            'target_quantity': float(row['current_quantity']) + qty_change,
            'unit_price': float(row['unit_price']),
            'investment_required': float(row['investment_required']),  # Negative (cost savings)
            'action': 'REDUCE',
            'reason': 'Overcapacity reduction (aggregated across genders)',
            'rule_explanation': f"Reduce by {abs(qty_change):.1f} units total (overcapacity: {row['overcapacity_percentage']:.1f}%)"
        })
    
    print(f"  ✅ Aggregated {len(rule10_filtered)} records → {len(aggregated)} unique store-SPU suggestions")
    return suggestions

def extract_rule11_suggestions(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Extract Rule 11 - Missed Sales suggestions"""
    suggestions = []
    
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing Rule 11"):
        if pd.notna(row.get('recommended_quantity_change', 0)) and float(row.get('recommended_quantity_change', 0)) > 0:
            suggestions.append({
                'rule': 'Rule 11 - Missed Sales',
                'store_code': str(row['str_code']),
                'spu_code': str(row['spu_code']),
                'current_quantity': float(row.get('current_quantity', 0)),
                'recommended_quantity_change': float(row['recommended_quantity_change']),
                'target_quantity': float(row.get('current_quantity', 0)) + float(row['recommended_quantity_change']),
                'unit_price': float(row.get('unit_price', 0)),
                'investment_required': float(row.get('investment_required', 0)),
                'action': 'ADD',
                'reason': 'Missed sales opportunity',
                'rule_explanation': f"Add {row['recommended_quantity_change']:.1f} units (opportunity score: {row.get('opportunity_score', 0):.2f})"
            })
    
    return suggestions

def extract_rule12_suggestions(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Extract Rule 12 - Performance suggestions"""
    suggestions = []
    
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing Rule 12"):
        # Only include opportunities (not already performing well)
        if (not bool(row.get('rule12_top_performer', False)) and 
            not bool(row.get('rule12_performing_well', False)) and
            pd.notna(row.get('recommended_quantity_change', 0)) and 
            float(row.get('recommended_quantity_change', 0)) > 0):
            
            suggestions.append({
                'rule': 'Rule 12 - Performance',
                'store_code': str(row['str_code']),
                'spu_code': str(row['spu_code']),
                'current_quantity': float(row.get('current_quantity', 0)),
                'recommended_quantity_change': float(row['recommended_quantity_change']),
                'target_quantity': float(row.get('current_quantity', 0)) + float(row['recommended_quantity_change']),
                'unit_price': float(row.get('unit_price', 0)),
                'investment_required': float(row.get('investment_required', 0)),
                'action': 'IMPROVE',
                'reason': 'Performance improvement',
                'rule_explanation': f"Increase by {row['recommended_quantity_change']:.1f} units (performance level: {row.get('performance_level', 'N/A')})"
            })
    
    return suggestions

def create_all_suggestions_csv():
    """Create comprehensive CSV with all rule suggestions"""
    print("🔍 Loading rule files...")
    rule_data = load_rule_files()
    
    all_suggestions = []
    
    # Extract suggestions from each rule
    if not rule_data['Rule 7 - Missing SPU'].empty:
        suggestions = extract_rule7_suggestions(rule_data['Rule 7 - Missing SPU'])
        all_suggestions.extend(suggestions)
        print(f"✓ Rule 7: {len(suggestions)} suggestions")
    
    if not rule_data['Rule 8 - Imbalanced'].empty:
        suggestions = extract_rule8_suggestions(rule_data['Rule 8 - Imbalanced'])
        all_suggestions.extend(suggestions)
        print(f"✓ Rule 8: {len(suggestions)} suggestions")
    
    if not rule_data['Rule 9 - Below Minimum'].empty:
        suggestions = extract_rule9_suggestions(rule_data['Rule 9 - Below Minimum'])
        all_suggestions.extend(suggestions)
        print(f"✓ Rule 9: {len(suggestions)} suggestions")
    
    if not rule_data['Rule 10 - Overcapacity'].empty:
        suggestions = extract_rule10_suggestions(rule_data['Rule 10 - Overcapacity'])
        all_suggestions.extend(suggestions)
        print(f"✓ Rule 10: {len(suggestions)} suggestions")
    
    if not rule_data['Rule 11 - Missed Sales'].empty:
        suggestions = extract_rule11_suggestions(rule_data['Rule 11 - Missed Sales'])
        all_suggestions.extend(suggestions)
        print(f"✓ Rule 11: {len(suggestions)} suggestions")
    
    if not rule_data['Rule 12 - Performance'].empty:
        suggestions = extract_rule12_suggestions(rule_data['Rule 12 - Performance'])
        all_suggestions.extend(suggestions)
        print(f"✓ Rule 12: {len(suggestions)} suggestions")
    
    # Convert to DataFrame
    if all_suggestions:
        df = pd.DataFrame(all_suggestions)
        
        # Reorder columns for clarity
        column_order = [
            'rule', 'store_code', 'spu_code', 'action', 'reason',
            'current_quantity', 'recommended_quantity_change', 'target_quantity',
            'unit_price', 'investment_required', 'rule_explanation'
        ]
        df = df[column_order]
        
        # Sort by rule, store, then SPU
        df = df.sort_values(['rule', 'store_code', 'spu_code'])
        
        # Save to CSV
        output_file = 'output/all_rule_suggestions.csv'
        df.to_csv(output_file, index=False)
        
        print(f"\n✅ All suggestions saved to: {output_file}")
        print(f"📊 Total suggestions: {len(df)}")
        print(f"🏪 Unique stores: {df['store_code'].nunique()}")
        print(f"📦 Unique SPUs: {df['spu_code'].nunique()}")
        
        # Print rule breakdown
        print("\n📋 Rule Breakdown:")
        rule_counts = df['rule'].value_counts()
        for rule, count in rule_counts.items():
            print(f"   {rule}: {count} suggestions")
        
        # Print investment summary
        print(f"\n💰 Total Investment Required: ${df['investment_required'].sum():,.0f}")
        print(f"📈 Average Investment per Suggestion: ${df['investment_required'].mean():.0f}")
        
        return df
    else:
        print("❌ No suggestions found!")
        return pd.DataFrame()

if __name__ == "__main__":
    create_all_suggestions_csv() 