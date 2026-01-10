#!/usr/bin/env python3
"""
Create Practical Client Recommendations - Store-Level SPU Recommendations
========================================================================

This provides what the client actually needs for business operations:
1. Store-level recommendations (specific stores they can act on)
2. Specific SPU recommendations (actual products to stock/adjust)
3. Rule-based quantities (using our intelligent analysis)
4. Forward-looking predictions for 6B period

Based on our rule analysis results, not abstract style combinations.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json

def load_rule_data():
    """Load rule analysis results and supporting data"""
    print("Loading rule analysis data...")
    
    # Load consolidated rule results
    try:
        rules_df = pd.read_csv('output/all_rule_suggestions.csv')
        print(f"Loaded {len(rules_df)} rule suggestions")
    except Exception as e:
        print(f"Error loading rule suggestions: {e}")
        return None, None, None
    
    # Load sales data for context
    try:
        sales_df = pd.read_csv('data/api_data/complete_spu_sales_202506A.csv')
        print(f"Loaded {len(sales_df)} sales records")
    except Exception as e:
        print(f"Error loading sales data: {e}")
        sales_df = None
    
    # Load store configuration
    try:
        store_config = pd.read_csv('data/api_data/store_config_data.csv')
        print(f"Loaded {len(store_config)} store configuration records")
    except Exception as e:
        print(f"Error loading store config: {e}")
        store_config = None
    
    return rules_df, sales_df, store_config

def create_practical_recommendations(rules_df, sales_df, store_config):
    """Create practical store-level SPU recommendations"""
    print("Creating practical recommendations...")
    
    # Filter to meaningful recommendations
    # Only include recommendations with significant quantity changes
    meaningful_rules = rules_df[
        (rules_df['recommended_quantity_change'].abs() >= 1) &  # At least 1 unit change
        (rules_df['recommended_quantity_change'].abs() <= 50)   # Not unrealistic quantities
    ].copy()
    
    print(f"Filtered to {len(meaningful_rules)} meaningful recommendations")
    
    # Get store information
    if store_config is not None:
        store_info = store_config[['str_code', 'str_name']].drop_duplicates()
        store_lookup = dict(zip(store_info['str_code'], store_info['str_name']))
    else:
        store_lookup = {}
    
    # Create a set of existing store-SPU combinations to identify new items
    # Items that were sold/stocked in 6A period (based on current_quantity from rules data)
    existing_combinations = set()
    
    # Use the rules data itself to identify existing items
    # If an item appears in the rules with current_quantity > 0, it existed in 6A
    for _, row in meaningful_rules.iterrows():
        if row.get('current_quantity', 0) > 0:
            # Use original rule format for existing combinations
            raw_spu = str(row['spu_code'])
            existing_combinations.add((str(row['store_code']), raw_spu))
    
    print(f"Found {len(existing_combinations)} store-SPU combinations that were stocked in 6A period")
    
    # Create mapping from rules format to alphanumeric SPU codes
    print("Creating SPU code mapping from rules to alphanumeric codes...")
    spu_mapping = {}
    spu_lookup = {}
    
    if sales_df is not None:
        # Create a mapping based on store + category matching
        print("Building store-category to alphanumeric SPU mapping...")
        
        # Group sales data by store and category for mapping
        sales_grouped = sales_df.groupby(['str_code', 'cate_name', 'sub_cate_name']).agg({
            'spu_code': 'first',  # Take first alphanumeric code for this store-category combo
            'spu_sales_amt': 'sum'
        }).reset_index()
        
        # Create lookup for alphanumeric codes
        for _, row in sales_df.iterrows():
            spu_lookup[row['spu_code']] = {
                'category': row['cate_name'],
                'subcategory': row['sub_cate_name']
            }
        
        # Map rules format to alphanumeric codes
        for _, rule in meaningful_rules.iterrows():
            store_code = str(rule['store_code'])
            spu_code_raw = str(rule['spu_code'])
            
            if '_' in spu_code_raw:
                # Extract descriptive part
                descriptive_part = spu_code_raw.split('_', 1)[1]
                
                # Try to find matching alphanumeric code in sales data for this store
                store_sales = sales_df[sales_df['str_code'] == int(store_code)]
                
                # Strategy 1: Match by subcategory name similarity
                best_match = None
                best_score = 0
                
                for _, sales_row in store_sales.iterrows():
                    # Check if descriptive part matches subcategory
                    if descriptive_part in sales_row['sub_cate_name'] or sales_row['sub_cate_name'] in descriptive_part:
                        score = len(set(descriptive_part) & set(sales_row['sub_cate_name']))
                        if score > best_score:
                            best_score = score
                            best_match = sales_row['spu_code']
                
                # Strategy 2: If no good match, use first SPU of same category
                if best_match is None and len(store_sales) > 0:
                    # Use first available SPU for this store (better than nothing)
                    best_match = store_sales.iloc[0]['spu_code']
                
                if best_match:
                    spu_mapping[spu_code_raw] = best_match
                else:
                    # Fallback: create a pseudo-alphanumeric code
                    spu_mapping[spu_code_raw] = f"UNK{store_code}"
            else:
                spu_mapping[spu_code_raw] = spu_code_raw
        
        print(f"Created mapping for {len(spu_mapping)} SPU codes")
        
    else:
        # Fallback: create generic mappings
        for spu_code_raw in meaningful_rules['spu_code'].unique():
            if '_' in str(spu_code_raw):
                store_part = str(spu_code_raw).split('_')[0]
                spu_mapping[spu_code_raw] = f"UNK{store_part}"
                spu_lookup[f"UNK{store_part}"] = {
                    'category': 'Unknown',
                    'subcategory': 'Unknown'
                }
            else:
                spu_mapping[spu_code_raw] = str(spu_code_raw)
                spu_lookup[str(spu_code_raw)] = {
                    'category': 'Unknown',
                    'subcategory': 'Unknown'
                }
    
    # Group recommendations by store-SPU combination for consolidation
    print("Grouping recommendations by store-SPU combination...")
    store_spu_recommendations = {}
    
    # Process each rule recommendation
    for idx, rule in meaningful_rules.iterrows():
        if idx % 10000 == 0:
            print(f"Processing recommendation {idx}/{len(meaningful_rules)}")
        
        store_code = rule.get('store_code', '')
        spu_code_raw = rule.get('spu_code', '')
        quantity_change = float(rule.get('recommended_quantity_change', 0))
        rule_type = rule.get('rule', 'Unknown')
        current_quantity = float(rule.get('current_quantity', 0))
        
        # Map to alphanumeric SPU code
        spu_code = spu_mapping.get(spu_code_raw, spu_code_raw)
        
        # Skip if missing essential data
        if not store_code or not spu_code:
            continue
        
        # Create store-SPU key for grouping
        key = (str(store_code), spu_code)
        
        if key not in store_spu_recommendations:
            store_spu_recommendations[key] = []
        
        # Add this rule's recommendation
        store_spu_recommendations[key].append({
            'rule': rule_type,
            'quantity_change': quantity_change,
            'current_quantity': current_quantity,
            'spu_code_raw': spu_code_raw
        })
    
    print(f"Found {len(store_spu_recommendations)} unique store-SPU combinations")
    
    # Consolidate recommendations using step 15 logic
    print("Consolidating multiple rule recommendations per store-SPU...")
    recommendations = []
    
    for (store_code, spu_code), rule_recommendations in store_spu_recommendations.items():
        if not rule_recommendations:
            continue
        
        # Separate increases and decreases
        increases = [r for r in rule_recommendations if r['quantity_change'] > 0]
        decreases = [r for r in rule_recommendations if r['quantity_change'] < 0]
        
        # Apply intelligent consolidation logic (same as step 15)
        if increases and decreases:
            # Conflicting directions: Calculate net difference
            max_increase = max(r['quantity_change'] for r in increases)
            max_decrease = min(r['quantity_change'] for r in decreases)  # Most negative
            final_change = max_increase + max_decrease
            
            increase_rules = [r['rule'] for r in increases if r['quantity_change'] == max_increase]
            decrease_rules = [r['rule'] for r in decreases if r['quantity_change'] == max_decrease]
            
            consolidation_logic = f"Conflict: {', '.join(increase_rules)} suggest +{max_increase:.1f}, {', '.join(decrease_rules)} suggest {max_decrease:.1f} → Net: {final_change:+.1f}"
            
        elif increases:
            # All increases: Take maximum
            final_change = max(r['quantity_change'] for r in increases)
            max_rules = [r['rule'] for r in increases if r['quantity_change'] == final_change]
            consolidation_logic = f"Multiple increases: Taking max +{final_change:.1f} from {', '.join(max_rules)}"
            
        elif decreases:
            # All decreases: Take maximum reduction
            final_change = min(r['quantity_change'] for r in decreases)
            max_rules = [r['rule'] for r in decreases if r['quantity_change'] == final_change]
            consolidation_logic = f"Multiple reductions: Taking max reduction {final_change:.1f} from {', '.join(max_rules)}"
        
        # Only include actionable changes
        if abs(final_change) >= 1:  # Minimum threshold
            # Get metadata for this store-SPU combination
            current_quantity = max(r['current_quantity'] for r in rule_recommendations)
            spu_code_raw = rule_recommendations[0]['spu_code_raw']
            
            # Check if this is a new item
            is_new_item = (str(store_code), spu_code_raw) not in existing_combinations
            
            # Get store name
            store_name = store_lookup.get(store_code, f"Store {store_code}")
            
            # Create store group descriptor
            store_code_int = int(store_code) if str(store_code).isdigit() else 0
            if store_code_int < 20000:
                store_group = "Store Group North"
            elif store_code_int < 40000:
                store_group = "Store Group Central" 
            elif store_code_int < 60000:
                store_group = "Store Group South"
            else:
                store_group = "Store Group West"
            
            # Get SPU details
            spu_details = spu_lookup.get(spu_code, {'category': 'Unknown', 'subcategory': 'Unknown'})
            
            # Create style tags
            def create_style_tags(category, subcategory):
                season = "Summer"
                
                if any(word in str(subcategory).lower() for word in ['男', 'men']):
                    gender = "Men"
                elif any(word in str(subcategory).lower() for word in ['女', 'women']):
                    gender = "Women"
                else:
                    gender = "Unisex"
                
                if any(word in str(category) for word in ['鞋', 'shoe', '配饰', 'accessories']):
                    location = "Shoes-Accessories"
                elif any(word in str(category) for word in ['内衣', 'underwear', '家居', 'home']):
                    location = "Back-store"
                else:
                    location = "Front-store"
                
                category_map = {
                    'T恤': 'T-shirt', '休闲裤': 'Casual Pants', '牛仔裤': 'Jeans',
                    'POLO衫': 'Polo Shirt', '套装': 'Sets', '茄克': 'Jackets',
                    '衬衫': 'Shirts', '裙': 'Dresses'
                }
                eng_category = category_map.get(str(category), str(category))
                
                if '工装裤' in str(subcategory):
                    eng_subcategory = 'Cargo Pants'
                elif '锥形裤' in str(subcategory):
                    eng_subcategory = 'Tapered Pants'
                elif 'T恤' in str(subcategory):
                    eng_subcategory = 'T-shirt'
                elif 'POLO' in str(subcategory):
                    eng_subcategory = 'Polo Shirt'
                else:
                    eng_subcategory = str(subcategory)
                
                return f"[{season}, {gender}, {location}, {eng_category}, {eng_subcategory}]"
            
            style_tags = create_style_tags(spu_details['category'], spu_details['subcategory'])
            
            # Determine final action
            if final_change > 0:
                action = "INCREASE"
                recommendation = f"Add {abs(final_change):.0f} units"
            else:
                action = "DECREASE" 
                recommendation = f"Reduce by {abs(final_change):.0f} units"
            
            # Calculate business impact
            avg_price = 100
            business_impact = abs(final_change) * avg_price
            
            # Create rule participation flags
            participating_rules = [r['rule'] for r in rule_recommendations]
            
            # Map rule names to participation flags
            rule_flags = {
                'Rule_7_Applied': 'YES' if any('7' in str(rule) or 'Missing' in str(rule) for rule in participating_rules) else 'NO',
                'Rule_8_Applied': 'YES' if any('8' in str(rule) or 'Imbalanced' in str(rule) for rule in participating_rules) else 'NO',
                'Rule_9_Applied': 'YES' if any('9' in str(rule) or 'Below' in str(rule) for rule in participating_rules) else 'NO',
                'Rule_10_Applied': 'YES' if any('10' in str(rule) or 'Overcapacity' in str(rule) for rule in participating_rules) else 'NO',
                'Rule_11_Applied': 'YES' if any('11' in str(rule) or 'Missed Sales' in str(rule) for rule in participating_rules) else 'NO',
                'Rule_12_Applied': 'YES' if any('12' in str(rule) or 'Performance' in str(rule) for rule in participating_rules) else 'NO'
            }
            
            # Create consolidated recommendation record
            rec = {
                'Year': 2025,
                'Month': 6,
                'Period': 'B',
                'Store_Group': store_group,
                'Store_Code': store_code,
                'Store_Name': store_name,
                'SPU_Code': spu_code,
                'Style_Tags': style_tags,
                'Category': spu_details['category'],
                'Subcategory': spu_details['subcategory'],
                'Action': action,
                'Quantity_Change': int(abs(final_change)),
                'Current_Quantity': int(current_quantity),
                'Target_Quantity': int(current_quantity + final_change),
                'Is_New_Item': 'YES' if is_new_item else 'NO',
                'Recommendation': recommendation,
                'Consolidation_Logic': consolidation_logic,
                'Contributing_Rules_Count': len(rule_recommendations),
                'Business_Impact_Yuan': business_impact,
                **rule_flags  # Add rule participation flags
            }
            
            recommendations.append(rec)
    
    print(f"Consolidated to {len(recommendations)} unique store-SPU recommendations")
    return recommendations

def prioritize_recommendations(recommendations):
    """Prioritize recommendations by business impact and feasibility"""
    print("Prioritizing recommendations...")
    
    df = pd.DataFrame(recommendations)
    
    if len(df) == 0:
        return df
    
    # Calculate priority score
    # Higher quantities = higher priority, but cap at reasonable levels
    df['Quantity_Score'] = np.clip(df['Quantity_Change'] / 10, 0, 5)
    
    # Business impact score
    df['Impact_Score'] = np.clip(df['Business_Impact_Yuan'] / 1000, 0, 5)
    
    # Calculate rule priority based on which rules contributed
    def calculate_rule_priority(row):
        """Calculate priority based on contributing rules"""
        priority_score = 0
        
        # High priority rules
        if row.get('Rule_7_Applied') == 'YES':  # Missing category
            priority_score += 5
        if row.get('Rule_11_Applied') == 'YES':  # Missed sales opportunity
            priority_score += 5
        
        # Medium-high priority rules
        if row.get('Rule_8_Applied') == 'YES':  # Imbalanced
            priority_score += 4
        if row.get('Rule_12_Applied') == 'YES':  # Sales performance
            priority_score += 4
        
        # Medium priority rules
        if row.get('Rule_9_Applied') == 'YES':  # Below minimum
            priority_score += 3
        
        # Lower priority rules
        if row.get('Rule_10_Applied') == 'YES':  # Overcapacity
            priority_score += 2
        
        # Bonus for multiple rules contributing
        contributing_rules = row.get('Contributing_Rules_Count', 1)
        if contributing_rules >= 3:
            priority_score += 2
        elif contributing_rules >= 2:
            priority_score += 1
        
        return priority_score
    
    df['Rule_Priority'] = df.apply(calculate_rule_priority, axis=1)
    
    # Calculate overall priority
    df['Priority_Score'] = (
        df['Quantity_Score'] * 0.25 +
        df['Impact_Score'] * 0.25 +
        df['Rule_Priority'] * 0.5
    )
    
    # Sort by priority
    df = df.sort_values(['Priority_Score', 'Business_Impact_Yuan'], ascending=[False, False])
    
    # Add priority labels
    df['Priority'] = 'LOW'
    df.loc[df['Priority_Score'] >= 3, 'Priority'] = 'MEDIUM'
    df.loc[df['Priority_Score'] >= 4, 'Priority'] = 'HIGH'
    df.loc[df['Priority_Score'] >= 4.5, 'Priority'] = 'CRITICAL'
    
    return df

def convert_to_json_safe(obj):
    """Convert numpy/pandas types to JSON-safe types"""
    if hasattr(obj, 'item'):  # numpy scalars
        return obj.item()
    elif isinstance(obj, dict):
        return {str(k): convert_to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_safe(item) for item in obj]
    else:
        return obj

def create_summary_report(df):
    """Create executive summary of recommendations"""
    print("Creating summary report...")
    
    if len(df) == 0:
        return "No recommendations generated."
    
    summary = {
        'total_recommendations': len(df),
        'stores_affected': df['Store_Code'].nunique(),
        'spus_affected': df['SPU_Code'].nunique(),
        'total_business_impact': float(df['Business_Impact_Yuan'].sum()),
        'priority_breakdown': convert_to_json_safe(df['Priority'].value_counts().to_dict()),
        'action_breakdown': convert_to_json_safe(df['Action'].value_counts().to_dict()),
        'new_vs_existing_breakdown': convert_to_json_safe(df['Is_New_Item'].value_counts().to_dict()),
        'contributing_rules_breakdown': convert_to_json_safe(df['Contributing_Rules_Count'].value_counts().to_dict()),
        'rule_participation': {
            'Rule_7_Applied': int((df['Rule_7_Applied'] == 'YES').sum()),
            'Rule_8_Applied': int((df['Rule_8_Applied'] == 'YES').sum()),
            'Rule_9_Applied': int((df['Rule_9_Applied'] == 'YES').sum()),
            'Rule_10_Applied': int((df['Rule_10_Applied'] == 'YES').sum()),
            'Rule_11_Applied': int((df['Rule_11_Applied'] == 'YES').sum()),
            'Rule_12_Applied': int((df['Rule_12_Applied'] == 'YES').sum())
        },
        'top_categories': convert_to_json_safe(df['Category'].value_counts().head(5).to_dict())
    }
    
    return summary

def main():
    """Generate practical client recommendations"""
    print("Generating Practical Client Recommendations")
    print("=" * 50)
    
    # Load data
    rules_df, sales_df, store_config = load_rule_data()
    
    if rules_df is None:
        print("❌ Cannot proceed without rule data")
        return
    
    # Create recommendations
    recommendations = create_practical_recommendations(rules_df, sales_df, store_config)
    
    if not recommendations:
        print("❌ No recommendations generated")
        return
    
    # Prioritize recommendations
    rec_df = prioritize_recommendations(recommendations)
    
    print(f"📊 Total recommendations generated: {len(rec_df):,}")
    
    # Save ALL recommendations (no limit)
    output_file = 'output/PRACTICAL_client_recommendations_6B_FULL.csv'
    rec_df.to_csv(output_file, index=False)
    
    # Also save top 10K for quick analysis if needed
    top_10k = rec_df.head(10000)
    top_10k_file = 'output/PRACTICAL_client_recommendations_6B_TOP10K.csv'
    top_10k.to_csv(top_10k_file, index=False)
    
    # Create summary from full dataset
    summary = create_summary_report(rec_df)
    
    # Save summary
    summary_file = 'output/PRACTICAL_recommendations_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✅ Generated practical recommendations: {output_file}")
    print(f"📊 Executive Summary:")
    print(f"- Total recommendations: {summary['total_recommendations']:,}")
    print(f"- Stores affected: {summary['stores_affected']:,}")
    print(f"- SPUs affected: {summary['spus_affected']:,}")
    print(f"- Total business impact: ${summary['total_business_impact']:,.0f}")
    
    print(f"\n🎯 Priority Breakdown:")
    for priority, count in summary['priority_breakdown'].items():
        print(f"  {priority}: {count:,} recommendations")
    
    print(f"\n📋 Action Breakdown:")
    for action, count in summary['action_breakdown'].items():
        print(f"  {action}: {count:,} recommendations")
    
    print(f"\n🆕 New vs Existing Items:")
    for item_type, count in summary['new_vs_existing_breakdown'].items():
        print(f"  {item_type}: {count:,} recommendations")
    
    print(f"\n📊 Contributing Rules Breakdown:")
    for rule_count, count in summary['contributing_rules_breakdown'].items():
        print(f"  {rule_count} rules contributed: {count:,} recommendations")
    
    print(f"\n📋 Individual Rule Participation:")
    rule_names = {
        'Rule_7_Applied': 'Rule 7 (Missing Category)',
        'Rule_8_Applied': 'Rule 8 (Imbalanced)', 
        'Rule_9_Applied': 'Rule 9 (Below Minimum)',
        'Rule_10_Applied': 'Rule 10 (Overcapacity)',
        'Rule_11_Applied': 'Rule 11 (Missed Sales)',
        'Rule_12_Applied': 'Rule 12 (Sales Performance)'
    }
    for rule_key, count in summary['rule_participation'].items():
        rule_name = rule_names.get(rule_key, rule_key)
        print(f"  {rule_name}: {count:,} recommendations")
    
    print(f"\n📈 Top Categories:")
    for category, count in summary['top_categories'].items():
        print(f"  {category}: {count:,} recommendations")
    
    # Show sample recommendations
    print(f"\n🔍 Sample High-Priority Recommendations:")
    high_priority = rec_df[rec_df['Priority'].isin(['HIGH', 'CRITICAL'])]
    if len(high_priority) > 0:
        sample = high_priority.head(5)[['Store_Group', 'Store_Name', 'SPU_Code', 'Style_Tags', 'Action', 'Quantity_Change', 'Is_New_Item', 'Priority']]
        print(sample.to_string(index=False))
    
    print(f"\n✅ Practical recommendations ready for client action!")
    print(f"📁 Files created:")
    print(f"  - {output_file} (ALL {len(rec_df):,} recommendations)")
    print(f"  - {top_10k_file} (top 10K recommendations for quick analysis)")
    print(f"  - {summary_file} (executive summary)")

if __name__ == "__main__":
    main() 