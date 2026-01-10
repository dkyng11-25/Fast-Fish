#!/usr/bin/env python3
"""
Comprehensive Sanity Check for SPU Count Analysis
================================================

Test diverse cases:
- Small vs Large store groups
- Low vs Medium vs High performing categories
- Different sub-categories
"""

import pandas as pd
import numpy as np

def load_and_prepare_data():
    """Load and prepare data with store groups."""
    print("Loading API data...")
    df = pd.read_csv("data/api_data/complete_spu_sales_202506B.csv", dtype={'str_code': str, 'spu_code': str})
    df['store_group'] = df['str_code'].apply(
        lambda x: f"Store Group {((int(str(x)[-3:]) if str(x)[-3:].isdigit() else hash(str(x))) % 20) + 1}"
    )
    print(f"Loaded {len(df):,} records")
    return df

def analyze_test_case(df, store_group, category, sub_category, case_name):
    """Analyze a specific test case."""
    
    print(f"\n{'='*80}")
    print(f"TEST CASE: {case_name}")
    print(f"Store Group: {store_group} × Category: {category}|{sub_category}")
    print(f"{'='*80}")
    
    # Filter data
    case_data = df[
        (df['store_group'] == store_group) & 
        (df['cate_name'] == category) & 
        (df['sub_cate_name'] == sub_category)
    ].copy()
    
    if len(case_data) == 0:
        print(f"❌ No data found")
        return None
    
    # Calculate metrics
    unique_stores = case_data['str_code'].nunique()
    unique_spus = case_data['spu_code'].nunique()
    total_sales = case_data['spu_sales_amt'].sum()
    avg_sales_per_spu = total_sales / unique_spus if unique_spus > 0 else 0
    
    print(f"📊 Data Summary:")
    print(f"   • Records: {len(case_data):,}")
    print(f"   • Stores: {unique_stores}")
    print(f"   • SPU codes: {unique_spus}")
    print(f"   • Total sales: ¥{total_sales:,.2f}")
    print(f"   • Avg sales per SPU: ¥{avg_sales_per_spu:,.2f}")
    
    # Determine performance level
    if avg_sales_per_spu > 1000:
        performance = "HIGH"
        color = "🟢"
    elif avg_sales_per_spu > 500:
        performance = "MEDIUM"
        color = "🟡"
    else:
        performance = "LOW"
        color = "🔴"
    
    # Determine store group size
    if unique_stores > 10:
        group_size = "LARGE"
        size_icon = "🏢"
    else:
        group_size = "SMALL"
        size_icon = "🏪"
    
    print(f"   • Performance: {color} {performance} (¥{avg_sales_per_spu:,.0f} avg per SPU)")
    print(f"   • Group size: {size_icon} {group_size} ({unique_stores} stores)")
    
    # Apply algorithm logic
    current_spus = unique_spus
    
    if avg_sales_per_spu > 1000:  # High performing
        if unique_stores > 10:  # Large group
            target_spus = min(current_spus + 3, int(current_spus * 1.2))
            logic = "High perf + Large group → Expand by up to 3 SPUs"
        else:  # Small group
            target_spus = min(current_spus + 2, int(current_spus * 1.15))
            logic = "High perf + Small group → Expand by up to 2 SPUs"
    elif avg_sales_per_spu > 500:  # Medium performing
        target_spus = max(current_spus, int(current_spus * 1.05))
        logic = "Medium perf → Slight expansion (5%)"
    else:  # Low performing
        if current_spus > 5:
            target_spus = max(3, int(current_spus * 0.8))
            logic = "Low perf → Focus strategy (reduce by 20%)"
        else:
            target_spus = current_spus
            logic = "Low perf → Keep minimal assortment"
    
    change = target_spus - current_spus
    
    print(f"🤖 Algorithm Logic: {logic}")
    print(f"   • Current SPUs: {current_spus}")
    print(f"   • Target SPUs: {target_spus}")
    print(f"   • Change: {change:+d}")
    
    # Check against generated output
    try:
        output_df = pd.read_csv("output/fast_fish_spu_count_recommendations_20250702_124006.csv")
        target_style = f"{category} | {sub_category}"
        match = output_df[
            (output_df['Store_Group_Name'] == store_group) & 
            (output_df['Target_Style_Tags'] == target_style)
        ]
        
        if len(match) > 0:
            row = match.iloc[0]
            output_current = row['Current_SPU_Quantity']
            output_target = row['Target_SPU_Quantity']
            output_stores = row['Stores_In_Group_Selling_This_Category']
            output_sales = row['Total_Current_Sales']
            output_avg = row['Avg_Sales_Per_SPU']
            
            # Verify matches
            current_match = output_current == current_spus
            target_match = output_target == target_spus
            stores_match = output_stores == unique_stores
            sales_match = abs(output_sales - total_sales) < 1.0  # Allow small rounding differences
            avg_match = abs(output_avg - avg_sales_per_spu) < 1.0
            
            all_match = all([current_match, target_match, stores_match, sales_match, avg_match])
            
            print(f"🔍 Output Verification: {'✅ PASS' if all_match else '❌ FAIL'}")
            if not all_match:
                print(f"   • Current SPUs: {current_spus} vs {output_current} {'✅' if current_match else '❌'}")
                print(f"   • Target SPUs: {target_spus} vs {output_target} {'✅' if target_match else '❌'}")
                print(f"   • Stores: {unique_stores} vs {output_stores} {'✅' if stores_match else '❌'}")
                print(f"   • Sales: ¥{total_sales:.2f} vs ¥{output_sales:.2f} {'✅' if sales_match else '❌'}")
                print(f"   • Avg per SPU: ¥{avg_sales_per_spu:.2f} vs ¥{output_avg:.2f} {'✅' if avg_match else '❌'}")
            else:
                print(f"   • All metrics match the generated output perfectly!")
        else:
            print(f"🔍 Output Verification: ❌ No matching recommendation found")
            
    except Exception as e:
        print(f"🔍 Output Verification: ❌ Error loading output: {e}")
    
    return {
        'case_name': case_name,
        'store_group': store_group,
        'category': category,
        'sub_category': sub_category,
        'unique_stores': unique_stores,
        'unique_spus': unique_spus,
        'total_sales': total_sales,
        'avg_sales_per_spu': avg_sales_per_spu,
        'performance': performance,
        'group_size': group_size,
        'current_spus': current_spus,
        'target_spus': target_spus,
        'change': change
    }

def main():
    """Run comprehensive sanity check."""
    
    print("🔍 COMPREHENSIVE SPU COUNT ANALYSIS SANITY CHECK")
    print("=" * 60)
    
    df = load_and_prepare_data()
    
    # Define diverse test cases (using actual data that exists)
    test_cases = [
        # Low performing - negative sales (returns/adjustments)
        {
            'store_group': 'Store Group 3',
            'category': '鞋',
            'sub_category': '凉鞋',
            'case_name': 'LOW PERFORMANCE (NEGATIVE SALES)'
        },
        # Low performing - small positive sales
        {
            'store_group': 'Store Group 20',
            'category': '羽绒衣',
            'sub_category': '厚长款羽绒',
            'case_name': 'LOW PERFORMANCE (SMALL SALES)'
        },
        # Medium performing - Small group
        {
            'store_group': 'Store Group 1',
            'category': 'T恤',
            'sub_category': '速干圆领T恤',
            'case_name': 'SMALL GROUP + MEDIUM PERFORMANCE'
        },
        # Medium performing - Large group
        {
            'store_group': 'Store Group 1',
            'category': '内衣',
            'sub_category': '三角裤',
            'case_name': 'LARGE GROUP + MEDIUM PERFORMANCE'
        },
        # High performing - Large group
        {
            'store_group': 'Store Group 2',
            'category': 'POLO衫',
            'sub_category': '凉感POLO',
            'case_name': 'LARGE GROUP + HIGH PERFORMANCE'
        },
        # Our previous test case
        {
            'store_group': 'Store Group 4',
            'category': '休闲裤',
            'sub_category': '直筒裤',
            'case_name': 'PREVIOUS TEST (HIGH PERFORMANCE)'
        }
    ]
    
    results = []
    
    for case in test_cases:
        result = analyze_test_case(df, **case)
        if result:
            results.append(result)
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY OF ALL TEST CASES")
    print(f"{'='*80}")
    
    print(f"{'Case':<35} {'Group':<8} {'Perf':<6} {'Current':<8} {'Target':<8} {'Change':<8}")
    print("-" * 80)
    
    for r in results:
        print(f"{r['case_name']:<35} {r['group_size']:<8} {r['performance']:<6} {r['current_spus']:<8} {r['target_spus']:<8} {r['change']:+8}")
    
    print(f"\nTested {len(results)} diverse scenarios covering:")
    print("• Small vs Large store groups")
    print("• Low vs Medium vs High performance categories") 
    print("• Different sub-categories and business logic paths")

if __name__ == "__main__":
    main() 