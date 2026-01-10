#!/usr/bin/env python3
"""
Aggregation Business Analysis - Determining if aggregation provides good advice or misleading artifacts
"""

import pandas as pd
import numpy as np

def analyze_aggregation_business_value():
    """Analyze whether aggregation provides meaningful business advice."""
    
    print("🔍 AGGREGATION BUSINESS VALUE ANALYSIS")
    print("=" * 70)
    
    # Load data
    main_df = pd.read_csv('output/all_rule_suggestions.csv')
    rule10_df = pd.read_csv('output/rule10_spu_overcapacity_opportunities.csv')
    
    # Focus on top cases for detailed analysis
    top_cases = main_df[main_df['current_quantity'] > 1000].nlargest(5, 'current_quantity')
    
    print("📊 BUSINESS SCENARIO ANALYSIS")
    print("-" * 50)
    
    for idx, (_, case) in enumerate(top_cases.iterrows()):
        store_code = case['store_code']
        quantity = case['current_quantity']
        spu_pattern = case['spu_code'].split('_')[1] if '_' in case['spu_code'] else 'Unknown'
        
        print(f"\n🏪 CASE {idx+1}: Store {store_code} - {quantity:.1f} T-shirts")
        
        # Get detailed breakdown
        variants = rule10_df[
            (rule10_df['str_code'].astype(str) == str(store_code)) & 
            (rule10_df['sub_cate_name'] == spu_pattern)
        ]
        
        if len(variants) > 0:
            print(f"   📋 VARIANT BREAKDOWN:")
            total_check = 0
            for _, variant in variants.iterrows():
                gender = variant['sex_name']
                location = variant['display_location_name']
                var_qty = variant['current_quantity']
                reduction = variant['constrained_reduction']
                total_check += var_qty
                
                print(f"      • {gender} {location}: {var_qty:.1f} units → reduce by {reduction:.1f}")
            
            print(f"   ✓ Total check: {total_check:.1f} ≈ {quantity:.1f}")
            
            # Business analysis questions
            print(f"\n   🤔 BUSINESS QUESTIONS:")
            
            # Question 1: Are variants truly independent?
            print(f"   Q1: Are these truly independent inventory decisions?")
            unique_genders = variants['sex_name'].nunique()
            unique_locations = variants['display_location_name'].nunique()
            
            if unique_genders > 1 and unique_locations > 1:
                print(f"       → INDEPENDENT: {unique_genders} genders × {unique_locations} locations")
                print(f"       → Each variant serves different customer segments")
                independence_score = 8
            elif unique_genders > 1:
                print(f"       → SEMI-INDEPENDENT: {unique_genders} genders, same location")
                print(f"       → Gender variants serve different customers")
                independence_score = 6
            else:
                print(f"       → DEPENDENT: Same gender, different locations")
                print(f"       → Location variants are display choices, not customer segments")
                independence_score = 3
            
            # Question 2: Can reductions be made independently?
            print(f"\n   Q2: Can reductions be made independently per variant?")
            avg_reduction_pct = (variants['constrained_reduction'] / variants['current_quantity']).mean()
            
            if unique_genders > 1:
                print(f"       → YES: Gender variants can be reduced independently")
                print(f"       → Manager can reduce men's vs women's inventory separately")
                reduction_independence = 8
            else:
                print(f"       → MAYBE: Location variants might need coordinated reduction")
                print(f"       → Front/back display might need to stay balanced")
                reduction_independence = 5
            
            # Question 3: Is the total reduction realistic?
            total_reduction = variants['constrained_reduction'].sum()
            total_reduction_pct = total_reduction / quantity
            
            print(f"\n   Q3: Is total reduction of {total_reduction:.1f} units ({total_reduction_pct:.1%}) realistic?")
            
            if total_reduction_pct > 0.5:
                print(f"       → EXTREME: >50% reduction seems drastic")
                realistic_score = 3
            elif total_reduction_pct > 0.3:
                print(f"       → HIGH: 30-50% reduction is significant but possible")
                realistic_score = 6
            else:
                print(f"       → REASONABLE: <30% reduction is manageable")
                realistic_score = 8
            
            # Question 4: Business implementation feasibility
            print(f"\n   Q4: How would a store manager implement this advice?")
            
            if unique_genders > 1:
                print(f"       → CLEAR ACTION: Reduce specific gender categories")
                print(f"       → Manager can target men's vs women's T-shirts")
                implementation_score = 8
            else:
                print(f"       → UNCLEAR ACTION: Reduce display locations?")
                print(f"       → Manager might be confused about front vs back")
                implementation_score = 4
            
            # Overall business value score
            business_value = (independence_score + reduction_independence + realistic_score + implementation_score) / 4
            
            print(f"\n   📊 BUSINESS VALUE ASSESSMENT:")
            print(f"      Independence: {independence_score}/10")
            print(f"      Reduction feasibility: {reduction_independence}/10") 
            print(f"      Realistic scale: {realistic_score}/10")
            print(f"      Implementation clarity: {implementation_score}/10")
            print(f"      OVERALL BUSINESS VALUE: {business_value:.1f}/10")
            
            if business_value >= 7:
                print(f"      ✅ GOOD ADVICE: Aggregation provides meaningful guidance")
            elif business_value >= 5:
                print(f"      ⚠️  MIXED VALUE: Some useful guidance, some confusion")
            else:
                print(f"      ❌ MISLEADING: Aggregation creates more confusion than value")
    
    # Overall aggregation assessment
    print(f"\n" + "=" * 70)
    print(f"🎯 OVERALL AGGREGATION ASSESSMENT")
    print("=" * 70)
    
    # Test different aggregation scenarios
    scenarios = analyze_aggregation_scenarios(rule10_df)
    
    print(f"\n📊 AGGREGATION SCENARIOS ANALYSIS:")
    for scenario_name, data in scenarios.items():
        print(f"\n{scenario_name}:")
        print(f"   Cases: {data['count']}")
        print(f"   Avg variants per case: {data['avg_variants']:.1f}")
        print(f"   Business clarity: {data['clarity']}")
        print(f"   Implementation difficulty: {data['difficulty']}")
    
    # Final recommendation
    generate_aggregation_recommendation(scenarios)

def analyze_aggregation_scenarios(rule10_df):
    """Analyze different aggregation scenarios."""
    
    # Group by store and SPU to see aggregation patterns
    store_spu_groups = rule10_df.groupby(['str_code', 'sub_cate_name'])
    
    scenarios = {
        'Single Gender + Single Location': {
            'count': 0, 'avg_variants': 1, 'clarity': 'Perfect', 'difficulty': 'Easy'
        },
        'Multiple Genders + Single Location': {
            'count': 0, 'avg_variants': 0, 'clarity': 'Good', 'difficulty': 'Easy'
        },
        'Single Gender + Multiple Locations': {
            'count': 0, 'avg_variants': 0, 'clarity': 'Confusing', 'difficulty': 'Hard'
        },
        'Multiple Genders + Multiple Locations': {
            'count': 0, 'avg_variants': 0, 'clarity': 'Complex but Clear', 'difficulty': 'Medium'
        }
    }
    
    variant_counts = []
    
    for (store, spu), group in store_spu_groups:
        gender_count = group['sex_name'].nunique()
        location_count = group['display_location_name'].nunique()
        variant_count = len(group)
        variant_counts.append(variant_count)
        
        if gender_count == 1 and location_count == 1:
            scenarios['Single Gender + Single Location']['count'] += 1
        elif gender_count > 1 and location_count == 1:
            scenarios['Multiple Genders + Single Location']['count'] += 1
            scenarios['Multiple Genders + Single Location']['avg_variants'] += variant_count
        elif gender_count == 1 and location_count > 1:
            scenarios['Single Gender + Multiple Locations']['count'] += 1
            scenarios['Single Gender + Multiple Locations']['avg_variants'] += variant_count
        else:
            scenarios['Multiple Genders + Multiple Locations']['count'] += 1
            scenarios['Multiple Genders + Multiple Locations']['avg_variants'] += variant_count
    
    # Calculate averages
    for scenario_name, data in scenarios.items():
        if data['count'] > 0 and scenario_name != 'Single Gender + Single Location':
            data['avg_variants'] = data['avg_variants'] / data['count']
    
    return scenarios

def generate_aggregation_recommendation(scenarios):
    """Generate final recommendation on aggregation approach."""
    
    print(f"\n🎯 FINAL RECOMMENDATION")
    print("-" * 50)
    
    total_cases = sum(s['count'] for s in scenarios.values())
    multi_variant_cases = sum(s['count'] for k, s in scenarios.items() if 'Multiple' in k)
    
    print(f"📊 AGGREGATION STATISTICS:")
    print(f"   Total store-SPU combinations: {total_cases:,}")
    print(f"   Single variant cases: {scenarios['Single Gender + Single Location']['count']:,}")
    print(f"   Multi-variant cases: {multi_variant_cases:,}")
    print(f"   Multi-variant percentage: {multi_variant_cases/total_cases*100:.1f}%")
    
    print(f"\n🤔 KEY CONSIDERATIONS:")
    
    # Consider business value vs complexity
    if multi_variant_cases / total_cases > 0.3:  # >30% are multi-variant
        print(f"   • HIGH AGGREGATION IMPACT: {multi_variant_cases/total_cases*100:.1f}% of cases involve multiple variants")
        print(f"   • Aggregation significantly affects business recommendations")
    else:
        print(f"   • LOW AGGREGATION IMPACT: Only {multi_variant_cases/total_cases*100:.1f}% involve multiple variants")
        print(f"   • Most cases are straightforward single variants")
    
    # Gender vs Location aggregation value
    gender_cases = scenarios['Multiple Genders + Single Location']['count'] + scenarios['Multiple Genders + Multiple Locations']['count']
    location_cases = scenarios['Single Gender + Multiple Locations']['count'] + scenarios['Multiple Genders + Multiple Locations']['count']
    
    print(f"\n   📋 AGGREGATION TYPE ANALYSIS:")
    print(f"   • Gender aggregation cases: {gender_cases:,} (valuable for targeting)")
    print(f"   • Location aggregation cases: {location_cases:,} (potentially confusing)")
    
    print(f"\n✅ RECOMMENDATIONS:")
    
    if gender_cases > location_cases * 2:
        print(f"   1. KEEP GENDER AGGREGATION: Provides clear business value")
        print(f"      → Managers can target men's vs women's inventory")
        print(f"      → Gender variants serve different customer segments")
        
        print(f"   2. CONSIDER LOCATION DISAGGREGATION: May cause confusion")
        print(f"      → Front/back display locations might be implementation details")
        print(f"      → Consider showing location breakdown for transparency")
    else:
        print(f"   1. REVIEW AGGREGATION STRATEGY: Mixed business value")
        print(f"      → Both gender and location aggregation are significant")
        print(f"      → Need clearer business rules for when to aggregate")
    
    print(f"\n   3. IMPLEMENTATION IMPROVEMENTS:")
    print(f"      → Add variant breakdown in reports")
    print(f"      → Show 'Total across X variants' in summaries")
    print(f"      → Flag high-aggregation cases for manual review")
    print(f"      → Provide implementation guidance for multi-variant reductions")
    
    print(f"\n🎯 FINAL VERDICT:")
    if gender_cases > total_cases * 0.2:  # >20% involve gender variants
        print(f"   ✅ AGGREGATION PROVIDES BUSINESS VALUE")
        print(f"   → Gender variants represent real business decisions")
        print(f"   → Keep current approach with transparency improvements")
    else:
        print(f"   ⚠️  AGGREGATION CREATES ARTIFACTS")
        print(f"   → Most aggregation is location-based (less valuable)")
        print(f"   → Consider disaggregating or changing approach")

if __name__ == "__main__":
    analyze_aggregation_business_value()
    print("\n✅ Aggregation business analysis complete!") 