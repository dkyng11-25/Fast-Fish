#!/usr/bin/env python3
"""
Simple Top 10 Offenders Analysis - Fast version with key insights
"""

import pandas as pd
import numpy as np
import os

def quick_analysis():
    """Quick analysis of top 10 offenders."""
    
    print("🔍 QUICK TOP 10 OFFENDERS ANALYSIS")
    print("=" * 60)
    
    # Load main data
    main_df = pd.read_csv('output/all_rule_suggestions.csv')
    rule10_df = pd.read_csv('output/rule10_spu_overcapacity_opportunities.csv')
    
    # Get top 10 cases
    top_10 = main_df[main_df['current_quantity'] > 1000].nlargest(10, 'current_quantity')
    
    print(f"✅ Analyzing top 10 most extreme cases")
    
    # Define simple postulates
    postulates = {
        'P1': 'Aggregation of multiple variants',
        'P2': 'High sales volume store', 
        'P3': 'Data quality issue',
        'P4': 'Special store characteristics',
        'P5': 'Seasonal accumulation',
        'P6': 'Calculation error'
    }
    
    results = []
    
    print(f"\n📊 CASE-BY-CASE ANALYSIS:")
    print("-" * 60)
    
    for idx, (_, case) in enumerate(top_10.iterrows()):
        store_code = case['store_code']
        quantity = case['current_quantity']
        unit_price = case['unit_price']
        spu_pattern = case['spu_code'].split('_')[1] if '_' in case['spu_code'] else 'Unknown'
        
        print(f"\n🔍 CASE {idx+1}: Store {store_code}")
        print(f"   Quantity: {quantity:.1f} units")
        print(f"   Item: {spu_pattern}")
        print(f"   Unit Price: ${unit_price:.2f}")
        print(f"   Total Value: ${quantity * unit_price:,.0f}")
        
        # Test each postulate quickly
        scores = {}
        
        # P1: Aggregation Effect
        rule10_records = rule10_df[
            (rule10_df['str_code'].astype(str) == str(store_code)) & 
            (rule10_df['sub_cate_name'] == spu_pattern)
        ]
        
        if len(rule10_records) > 1:
            gender_count = rule10_records['sex_name'].nunique()
            location_count = rule10_records['display_location_name'].nunique()
            quantity_sum = rule10_records['current_quantity'].sum()
            
            p1_score = 0
            if len(rule10_records) > 1: p1_score += 3
            if gender_count > 1: p1_score += 2
            if location_count > 1: p1_score += 2
            if abs(quantity_sum - quantity) < 1: p1_score += 3
            
            scores['P1'] = p1_score
            print(f"   P1 - Aggregation: {p1_score}/10 ({len(rule10_records)} variants, {gender_count} genders)")
        else:
            scores['P1'] = 0
            print(f"   P1 - Aggregation: 0/10 (no variants found)")
        
        # P2: High Sales Volume (simplified)
        store_activity = rule10_df[rule10_df['str_code'].astype(str) == str(store_code)]
        if len(store_activity) > 0:
            unique_spus = store_activity['sub_cate_name'].nunique()
            avg_qty = store_activity['current_quantity'].mean()
            
            p2_score = 0
            if unique_spus > 20: p2_score += 3
            if len(store_activity) > 50: p2_score += 2
            if avg_qty > 300: p2_score += 2
            
            scores['P2'] = p2_score
            print(f"   P2 - High Sales: {p2_score}/10 ({unique_spus} SPU types, avg {avg_qty:.1f})")
        else:
            scores['P2'] = 0
            print(f"   P2 - High Sales: 0/10 (no store data)")
        
        # P3: Data Quality Issue
        p3_score = 0
        if 1000 < quantity < 3000 and quantity % 100 < 10:
            p3_score += 4
        if spu_pattern == '休闲圆领T恤' and quantity > 1500:
            p3_score += 3
        if unit_price == 20.00:
            p3_score += 2
        
        scores['P3'] = p3_score
        print(f"   P3 - Data Quality: {p3_score}/10 (currency-like: {1000 < quantity < 3000})")
        
        # P4: Store Characteristics
        p4_score = scores['P2']  # Similar to P2 but different interpretation
        scores['P4'] = p4_score
        print(f"   P4 - Store Special: {p4_score}/10 (based on activity)")
        
        # P5: Seasonal
        p5_score = 0
        if spu_pattern == '休闲圆领T恤':
            p5_score += 3
        
        scores['P5'] = p5_score
        print(f"   P5 - Seasonal: {p5_score}/10 (T-shirt: {spu_pattern == '休闲圆领T恤'})")
        
        # P6: Calculation Error
        p6_score = p3_score  # Similar indicators
        scores['P6'] = p6_score
        print(f"   P6 - Calculation: {p6_score}/10 (similar to data quality)")
        
        # Determine top postulate
        best_postulate = max(scores.items(), key=lambda x: x[1])
        print(f"   🎯 MOST LIKELY: {best_postulate[0]} - {postulates[best_postulate[0]]} ({best_postulate[1]}/10)")
        
        # Store result
        result = {
            'case': f"Case_{idx+1}",
            'store': store_code,
            'quantity': quantity,
            'item': spu_pattern,
            'unit_price': unit_price,
            'total_value': quantity * unit_price,
            **scores,
            'top_postulate': best_postulate[0],
            'top_score': best_postulate[1]
        }
        results.append(result)
    
    # Create summary matrix
    print(f"\n" + "=" * 80)
    print(f"📊 POSTULATE vs CASE MATRIX")
    print("=" * 80)
    
    print(f"\n{'Case':<8} {'Store':<8} {'P1':<4} {'P2':<4} {'P3':<4} {'P4':<4} {'P5':<4} {'P6':<4} {'Winner':<12}")
    print("-" * 75)
    
    for result in results:
        scores_str = f"{result['P1']:2d}  {result['P2']:2d}  {result['P3']:2d}  {result['P4']:2d}  {result['P5']:2d}  {result['P6']:2d}"
        winner = f"{result['top_postulate']}({result['top_score']})"
        print(f"{result['case']:<8} {result['store']:<8} {scores_str} {winner:<12}")
    
    # Summary insights
    print(f"\n📈 KEY INSIGHTS:")
    print("-" * 40)
    
    # Count winners
    winner_counts = {}
    for result in results:
        winner = result['top_postulate']
        winner_counts[winner] = winner_counts.get(winner, 0) + 1
    
    print(f"Most common explanations:")
    for postulate, count in sorted(winner_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {postulate} - {postulates[postulate]}: {count} cases")
    
    # Average scores
    print(f"\nAverage scores across all cases:")
    for p_id in ['P1', 'P2', 'P3', 'P4', 'P5', 'P6']:
        avg_score = np.mean([r[p_id] for r in results])
        print(f"   {p_id} - {postulates[p_id]}: {avg_score:.1f}/10")
    
    # Specific patterns
    print(f"\nSpecific patterns observed:")
    t_shirt_cases = [r for r in results if r['item'] == '休闲圆领T恤']
    print(f"   • {len(t_shirt_cases)}/10 cases are T-shirts")
    
    exact_20_cases = [r for r in results if r['unit_price'] == 20.00]
    print(f"   • {len(exact_20_cases)}/10 cases have exactly $20.00 unit price")
    
    high_p1_cases = [r for r in results if r['P1'] >= 7]
    print(f"   • {len(high_p1_cases)}/10 cases show strong aggregation evidence")
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv('output/quick_offenders_analysis.csv', index=False)
    print(f"\n💾 Results saved to: output/quick_offenders_analysis.csv")

if __name__ == "__main__":
    quick_analysis()
    print("\n✅ Quick analysis complete!") 