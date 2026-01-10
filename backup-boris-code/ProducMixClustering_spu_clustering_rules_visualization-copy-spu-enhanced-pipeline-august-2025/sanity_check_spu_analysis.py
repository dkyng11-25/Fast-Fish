#!/usr/bin/env python3
"""
Sanity Check for SPU Count Analysis
===================================

Manually verify the analysis for specific store and sub-category combinations
to ensure our algorithm is working correctly.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
def get_actual_store_group(store_code: str) -> str:
    """Get actual store group from clustering results."""
    cluster_file = "output/clustering_results_spu.csv"
    if not os.path.exists(cluster_file):
        # Fallback to modulo 46 if clustering file not found
        return f"Store Group {((int(store_code[-3:]) if store_code[-3:].isdigit() else hash(store_code)) % 46) + 1}"
    
    try:
        cluster_df = pd.read_csv(cluster_file)
        store_match = cluster_df[cluster_df['str_code'] == int(store_code)]
        if not store_match.empty:
            cluster_id = store_match.iloc[0]['Cluster']
            return f"Store Group {cluster_id + 1}"
        else:
            return f"Store Group 1"  # Default fallback
    except:
        return f"Store Group 1"  # Error fallback



def load_api_data() -> pd.DataFrame:
    """Load the API data."""
    print("Loading API data...")
    df = pd.read_csv("data/api_data/complete_spu_sales_202506B.csv", dtype={'str_code': str, 'spu_code': str})
    print(f"Loaded {len(df):,} records")
    return df

def create_store_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Create store groups (same logic as main script)."""
    df_with_groups = df.copy()
    df_with_groups['store_group'] = df_with_groups['str_code'].apply(
        lambda x: get_actual_store_group(str(x))
    )
    return df_with_groups

def analyze_specific_case(df: pd.DataFrame, store_code: str, category: str, sub_category: str) -> Dict:
    """Analyze a specific store, category, sub-category combination."""
    
    print(f"\n{'='*80}")
    print(f"SANITY CHECK: Store {store_code} × {category}|{sub_category}")
    print(f"{'='*80}")
    
    # Filter for this specific case
    case_data = df[
        (df['str_code'] == store_code) & 
        (df['cate_name'] == category) & 
        (df['sub_cate_name'] == sub_category)
    ].copy()
    
    if len(case_data) == 0:
        print(f"❌ No data found for Store {store_code} × {category}|{sub_category}")
        return {}
    
    print(f"📊 Found {len(case_data)} sales records")
    
    # Basic analysis
    unique_spus = case_data['spu_code'].nunique()
    total_sales = case_data['spu_sales_amt'].sum()
    total_quantity = case_data['quantity'].sum()
    avg_sales_per_spu = total_sales / unique_spus if unique_spus > 0 else 0
    
    print(f"   • Unique SPU codes: {unique_spus}")
    print(f"   • Total sales: ¥{total_sales:,.2f}")
    print(f"   • Total quantity: {total_quantity:.1f}")
    print(f"   • Average sales per SPU: ¥{avg_sales_per_spu:,.2f}")
    
    # Show the actual SPU codes and their performance
    spu_performance = case_data.groupby('spu_code').agg({
        'spu_sales_amt': 'sum',
        'quantity': 'sum'
    }).sort_values('spu_sales_amt', ascending=False)
    
    print(f"\n📋 SPU Performance Breakdown:")
    print(f"{'SPU Code':<12} {'Sales (¥)':<12} {'Quantity':<10}")
    print("-" * 35)
    for spu, row in spu_performance.head(10).iterrows():
        print(f"{spu:<12} {row['spu_sales_amt']:<12.2f} {row['quantity']:<10.1f}")
    
    if len(spu_performance) > 10:
        print(f"... and {len(spu_performance) - 10} more SPUs")
    
    return {
        'store_code': store_code,
        'category': category,
        'sub_category': sub_category,
        'unique_spus': unique_spus,
        'total_sales': total_sales,
        'total_quantity': total_quantity,
        'avg_sales_per_spu': avg_sales_per_spu,
        'spu_performance': spu_performance
    }

def analyze_store_group_case(df: pd.DataFrame, store_group: str, category: str, sub_category: str) -> Dict:
    """Analyze a store group × category × sub-category combination."""
    
    print(f"\n{'='*80}")
    print(f"STORE GROUP ANALYSIS: {store_group} × {category}|{sub_category}")
    print(f"{'='*80}")
    
    # Filter for this store group and category combination
    group_data = df[
        (df['store_group'] == store_group) & 
        (df['cate_name'] == category) & 
        (df['sub_cate_name'] == sub_category)
    ].copy()
    
    if len(group_data) == 0:
        print(f"❌ No data found for {store_group} × {category}|{sub_category}")
        return {}
    
    print(f"📊 Found {len(group_data)} sales records")
    
    # Store group analysis
    unique_stores = group_data['str_code'].nunique()
    unique_spus = group_data['spu_code'].nunique()
    total_sales = group_data['spu_sales_amt'].sum()
    total_quantity = group_data['quantity'].sum()
    avg_sales_per_spu = total_sales / unique_spus if unique_spus > 0 else 0
    
    print(f"   • Stores in group selling this category: {unique_stores}")
    print(f"   • Unique SPU codes across group: {unique_spus}")
    print(f"   • Total sales across group: ¥{total_sales:,.2f}")
    print(f"   • Total quantity across group: {total_quantity:.1f}")
    print(f"   • Average sales per SPU: ¥{avg_sales_per_spu:,.2f}")
    
    # Show store breakdown
    store_breakdown = group_data.groupby(['str_code', 'str_name']).agg({
        'spu_code': 'nunique',
        'spu_sales_amt': 'sum',
        'quantity': 'sum'
    }).sort_values('spu_sales_amt', ascending=False)
    
    print(f"\n🏪 Store Breakdown (Top 10):")
    print(f"{'Store Code':<12} {'Store Name':<15} {'SPUs':<6} {'Sales (¥)':<12} {'Quantity':<10}")
    print("-" * 65)
    for (store_code, store_name), row in store_breakdown.head(10).iterrows():
        print(f"{store_code:<12} {store_name[:14]:<15} {row['spu_code']:<6} {row['spu_sales_amt']:<12.2f} {row['quantity']:<10.1f}")
    
    # Algorithm logic simulation
    print(f"\n🤖 Algorithm Logic:")
    if avg_sales_per_spu > 1000:
        performance = "High-performing"
        if unique_stores > 10:
            recommendation = f"Expand by up to 3 SPUs (20% cap: {int(unique_spus * 1.2)})"
        else:
            recommendation = f"Expand by up to 2 SPUs (15% cap: {int(unique_spus * 1.15)})"
    elif avg_sales_per_spu > 500:
        performance = "Medium-performing"
        recommendation = f"Slight expansion (5% cap: {int(unique_spus * 1.05)})"
    else:
        performance = "Low-performing"
        if unique_spus > 5:
            recommendation = f"Focus strategy - reduce to {max(3, int(unique_spus * 0.8))} SPUs"
        else:
            recommendation = "Keep minimal assortment"
    
    print(f"   • Performance: {performance} (¥{avg_sales_per_spu:,.0f} avg per SPU)")
    print(f"   • Store group size: {'Large' if unique_stores > 10 else 'Small'} ({unique_stores} stores)")
    print(f"   • Recommendation: {recommendation}")
    
    return {
        'store_group': store_group,
        'category': category,
        'sub_category': sub_category,
        'unique_stores': unique_stores,
        'unique_spus': unique_spus,
        'total_sales': total_sales,
        'avg_sales_per_spu': avg_sales_per_spu,
        'performance': performance,
        'recommendation': recommendation
    }

def compare_with_output(store_group: str, category: str, sub_category: str):
    """Compare our manual analysis with the generated output."""
    
    print(f"\n🔍 COMPARING WITH GENERATED OUTPUT:")
    
    # Load the generated output
    try:
        output_df = pd.read_csv("output/fast_fish_spu_count_recommendations_20250702_124006.csv")
        
        # Find the matching row
        target_style = f"{category} | {sub_category}"
        match = output_df[
            (output_df['Store_Group_Name'] == store_group) & 
            (output_df['Target_Style_Tags'] == target_style)
        ]
        
        if len(match) > 0:
            row = match.iloc[0]
            print(f"   ✅ Found matching recommendation:")
            print(f"      • Current SPU Quantity: {row['Current_SPU_Quantity']}")
            print(f"      • Target SPU Quantity: {row['Target_SPU_Quantity']}")
            print(f"      • Stores in Group: {row['Stores_In_Group_Selling_This_Category']}")
            print(f"      • Total Sales: ¥{row['Total_Current_Sales']:,.2f}")
            print(f"      • Avg Sales per SPU: ¥{row['Avg_Sales_Per_SPU']:,.2f}")
            print(f"      • Rationale: {row['Data_Based_Rationale'][:100]}...")
        else:
            print(f"   ❌ No matching recommendation found in output")
            
    except Exception as e:
        print(f"   ❌ Error loading output file: {e}")

def main():
    """Run sanity checks."""
    
    print("🔍 SPU COUNT ANALYSIS SANITY CHECK")
    print("=" * 50)
    
    # Load data
    df = load_api_data()
    df_with_groups = create_store_groups(df)
    
    # Test cases
    test_cases = [
        {
            'store_code': '11003',
            'category': '休闲裤',
            'sub_category': '直筒裤'
        },
        {
            'store_code': '11003', 
            'category': '配饰',
            'sub_category': '低帮袜'
        }
    ]
    
    # Analyze individual stores first
    for case in test_cases:
        analyze_specific_case(df_with_groups, **case)
    
    # Then analyze at store group level
    print(f"\n{'='*100}")
    print("STORE GROUP LEVEL ANALYSIS")
    print(f"{'='*100}")
    
    # Find which store group store 11003 belongs to
    store_11003_group = df_with_groups[df_with_groups['str_code'] == '11003']['store_group'].iloc[0]
    print(f"📍 Store 11003 belongs to: {store_11003_group}")
    
    group_test_cases = [
        {
            'store_group': store_11003_group,
            'category': '休闲裤',
            'sub_category': '直筒裤'
        },
        {
            'store_group': store_11003_group,
            'category': '配饰', 
            'sub_category': '低帮袜'
        }
    ]
    
    for case in group_test_cases:
        analyze_store_group_case(df_with_groups, **case)
        compare_with_output(**case)

if __name__ == "__main__":
    main() 