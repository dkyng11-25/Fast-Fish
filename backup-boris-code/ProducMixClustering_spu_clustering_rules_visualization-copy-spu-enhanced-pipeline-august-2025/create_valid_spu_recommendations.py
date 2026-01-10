#!/usr/bin/env python3
"""
Valid SPU Recommendations Generator
==================================

This script processes ONLY valid alphanumeric SPU codes and applies 
Step 15 consolidation logic for multiple rules on the same Store+SPU combination.

Ignores invalid store_product format codes like "13003_低帮袜".
Only processes valid codes like "15S1010".
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
from typing import Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_and_filter_valid_spus():
    """Load data and filter to ONLY valid alphanumeric SPU codes"""
    logger.info("Loading data and filtering to valid SPU codes...")
    
    # Load rule analysis results
    rules_df = pd.read_csv('output/all_rule_suggestions.csv')
    logger.info(f"Loaded {len(rules_df):,} rule suggestions")
    
    # Filter to ONLY valid alphanumeric SPU codes
    valid_spu_pattern = rules_df['spu_code'].astype(str).str.match(r'^[A-Z0-9]{6,}$')
    valid_rules = rules_df[valid_spu_pattern].copy()
    
    logger.info(f"Filtered to {len(valid_rules):,} rules with valid SPU codes ({len(valid_rules)/len(rules_df)*100:.1f}%)")
    
    # Filter to meaningful recommendations
    meaningful = valid_rules[
        (valid_rules['recommended_quantity_change'].abs() >= 1) &
        (valid_rules['recommended_quantity_change'].abs() <= 100)
    ].copy()
    
    logger.info(f"Filtered to {len(meaningful):,} meaningful recommendations")
    
    return meaningful

def consolidate_by_store_spu(meaningful_df):
    """Consolidate multiple rules for the same Store+SPU combination (Step 15 logic)"""
    logger.info("Consolidating by Store+SPU combination using Step 15 logic...")
    
    # Group by store_code + spu_code
    grouped = meaningful_df.groupby(['store_code', 'spu_code'])
    
    consolidated_list = []
    
    for (store_code, spu_code), group in grouped:
        # Get all changes for this store-SPU combination
        changes = group['recommended_quantity_change'].values
        current_quantities = group['current_quantity'].values
        rules = group['rule'].tolist()
        
        # Apply Step 15 consolidation logic
        increases = changes[changes > 0]
        decreases = changes[changes < 0]
        
        if len(increases) > 0 and len(decreases) > 0:
            # Conflicting directions: Calculate net difference
            max_increase = increases.max()
            max_decrease = decreases.min()  # Most negative
            final_change = max_increase + max_decrease
            
            increase_rules = [rules[i] for i, change in enumerate(changes) if change == max_increase]
            decrease_rules = [rules[i] for i, change in enumerate(changes) if change == max_decrease]
            
            consolidation_logic = f"Conflict: {', '.join(increase_rules)} suggest +{max_increase:.1f}, {', '.join(decrease_rules)} suggest {max_decrease:.1f} → Net: {final_change:+.1f}"
            
        elif len(increases) > 0:
            # All increases: Take maximum
            final_change = increases.max()
            max_rules = [rules[i] for i, change in enumerate(changes) if change == final_change]
            consolidation_logic = f"Multiple increases: Taking max +{final_change:.1f} from {', '.join(max_rules)}"
            
        elif len(decreases) > 0:
            # All decreases: Take maximum reduction
            final_change = decreases.min()  # Most negative
            max_rules = [rules[i] for i, change in enumerate(changes) if change == final_change]
            consolidation_logic = f"Multiple reductions: Taking max reduction {final_change:.1f} from {', '.join(max_rules)}"
        else:
            continue
        
        # Only include actionable changes
        if abs(final_change) >= 1:
            # Use the maximum current_quantity for this combination
            current_quantity = current_quantities.max()
            
            consolidated_list.append({
                'store_code': int(store_code),
                'spu_code': spu_code,
                'current_quantity': current_quantity,
                'final_change': final_change,
                'consolidation_logic': consolidation_logic,
                'rules': rules,
                'rule_count': len(rules)
            })
    
    logger.info(f"Consolidated to {len(consolidated_list):,} unique Store+SPU recommendations")
    return pd.DataFrame(consolidated_list)

def load_supporting_data():
    """Load supporting data for enrichment"""
    logger.info("Loading supporting data...")
    
    # Load sales data for category information
    try:
        sales_df = pd.read_csv('data/api_data/complete_spu_sales_202506A.csv')
        logger.info(f"Loaded {len(sales_df):,} sales records")
        
        # Create SPU lookup for categories
        spu_lookup = sales_df.groupby('spu_code').agg({
            'cate_name': 'first',
            'sub_cate_name': 'first'
        }).to_dict('index')
        
    except Exception as e:
        logger.warning(f"Could not load sales data: {e}")
        spu_lookup = {}
    
    # Load store configuration
    try:
        store_config = pd.read_csv('data/api_data/store_config_data.csv')
        logger.info(f"Loaded {len(store_config):,} store configuration records")
        
        # Create store lookup
        store_lookup = store_config.set_index('str_code')['str_name'].to_dict()
        
    except Exception as e:
        logger.warning(f"Could not load store config: {e}")
        store_lookup = {}
    
    return spu_lookup, store_lookup

def identify_existing_items(meaningful_df):
    """Identify existing items based on current_quantity > 0"""
    logger.info("Identifying existing items...")
    
    existing_items = set()
    for _, row in meaningful_df.iterrows():
        if row['current_quantity'] > 0:
            key = f"{row['store_code']}|{row['spu_code']}"
            existing_items.add(key)
    
    logger.info(f"Found {len(existing_items):,} existing Store+SPU combinations")
    return existing_items

def create_final_format(consolidated_df, spu_lookup, store_lookup, existing_items):
    """Create final client format"""
    logger.info("Creating final client format...")
    
    final_records = []
    
    for _, row in consolidated_df.iterrows():
        store_code = row['store_code']
        spu_code = row['spu_code']
        
        # Basic calculations
        target_quantity = max(0, row['current_quantity'] + row['final_change'])
        action = "INCREASE" if row['final_change'] > 0 else "DECREASE"
        recommendation = f"{'Add' if row['final_change'] > 0 else 'Reduce by'} {abs(row['final_change']):.0f} units"
        
        # Store information
        if store_code < 20000:
            store_group = "Store Group North"
        elif store_code < 40000:
            store_group = "Store Group Central"
        elif store_code < 60000:
            store_group = "Store Group South"
        else:
            store_group = "Store Group West"
        
        store_name = store_lookup.get(store_code, f"Store {store_code}")
        
        # Product information from sales data
        if spu_code in spu_lookup:
            category = spu_lookup[spu_code]['cate_name']
            subcategory = spu_lookup[spu_code]['sub_cate_name']
        else:
            category = '未知'
            subcategory = '未知'
        
        # Create style tags
        season = "Summer"
        gender = "Unisex"
        
        if any(word in str(category) for word in ['鞋', 'shoe', '配饰', 'accessories']):
            location = "Shoes-Accessories"
        elif any(word in str(category) for word in ['内衣', 'underwear', '家居', 'home']):
            location = "Back-store"
        else:
            location = "Front-store"
        
        # English translations
        category_map = {
            'T恤': 'T-shirt', '休闲裤': 'Casual Pants', '牛仔裤': 'Jeans',
            'POLO衫': 'Polo Shirt', '套装': 'Sets', '茄克': 'Jackets',
            '衬衫': 'Shirts', '裙': 'Dresses', '配饰': 'Accessories'
        }
        eng_category = category_map.get(str(category), str(category))
        
        subcategory_map = {
            '工装裤': 'Cargo Pants', '锥形裤': 'Tapered Pants', 'T恤': 'T-shirt',
            'POLO': 'Polo Shirt', '低帮袜': 'Low-cut Socks', '袜': 'Socks'
        }
        eng_subcategory = subcategory_map.get(str(subcategory), str(subcategory))
        
        style_tags = f"[{season}, {gender}, {location}, {eng_category}, {eng_subcategory}]"
        
        # Rule participation flags
        participating_rules = row['rules']
        rule_flags = {
            'Rule_7_Applied': 'YES' if any('7' in str(rule) or 'Missing' in str(rule) for rule in participating_rules) else 'NO',
            'Rule_8_Applied': 'YES' if any('8' in str(rule) or 'Imbalanced' in str(rule) for rule in participating_rules) else 'NO',
            'Rule_9_Applied': 'YES' if any('9' in str(rule) or 'Below' in str(rule) for rule in participating_rules) else 'NO',
            'Rule_10_Applied': 'YES' if any('10' in str(rule) or 'Overcapacity' in str(rule) for rule in participating_rules) else 'NO',
            'Rule_11_Applied': 'YES' if any('11' in str(rule) or 'Missed Sales' in str(rule) for rule in participating_rules) else 'NO',
            'Rule_12_Applied': 'YES' if any('12' in str(rule) or 'Performance' in str(rule) for rule in participating_rules) else 'NO'
        }
        
        # Check if new item
        item_key = f"{store_code}|{spu_code}"
        is_new_item = item_key not in existing_items
        
        # Create record
        record = {
            'Year': 2025,
            'Month': '06',
            'Period': 'B',
            'Store_Group': store_group,
            'Store_Code': store_code,
            'Store_Name': store_name,
            'SPU_Code': spu_code,  # Keep original valid SPU code
            'Style_Tags': style_tags,
            'Category': category,
            'Subcategory': subcategory,
            'Action': action,
            'Target SPU Quantity': int(target_quantity),
            'Current_Quantity': int(row['current_quantity']),
            'Is_New_Item': 'YES' if is_new_item else 'NO',
            'Recommendation': recommendation,
            'Consolidation_Logic': row['consolidation_logic'],
            'Contributing_Rules_Count': row['rule_count'],
            'Business_Impact_Yuan': int(abs(row['final_change']) * 100),
            **rule_flags
        }
        
        final_records.append(record)
    
    return pd.DataFrame(final_records)

def save_results(df):
    """Save final results"""
    logger.info("Saving results...")
    
    if len(df) == 0:
        logger.error("No recommendations to save!")
        return
    
    # Sort by business impact
    df = df.sort_values(['Business_Impact_Yuan'], ascending=False)
    
    # Save main file
    main_file = "output/VALID_SPU_client_recommendations_6B.csv"
    df.to_csv(main_file, index=False)
    logger.info(f"Saved {len(df):,} recommendations to {main_file}")
    
    # Save top 10K
    top_10k_file = "output/VALID_SPU_client_recommendations_6B_TOP10K.csv"
    df.head(10000).to_csv(top_10k_file, index=False)
    logger.info(f"Saved top 10K to {top_10k_file}")
    
    # Create summary
    summary = {
        "processing_info": {
            "timestamp": datetime.now().isoformat(),
            "total_recommendations": len(df),
            "stores_affected": df['Store_Code'].nunique(),
            "spus_affected": df['SPU_Code'].nunique(),
            "total_business_impact": float(df['Business_Impact_Yuan'].sum()),
            "only_valid_spus": True,
            "step_15_consolidation": True
        },
        "data_quality": {
            "valid_spu_codes_only": True,
            "no_store_product_format": True,
            "proper_consolidation": True
        },
        "breakdown": {
            "action_breakdown": df['Action'].value_counts().to_dict(),
            "new_vs_existing": df['Is_New_Item'].value_counts().to_dict(),
            "rule_participation": {
                f"Rule_{i}": (df[f'Rule_{i}_Applied'] == 'YES').sum() 
                for i in [7, 8, 9, 10, 11, 12]
            }
        }
    }
    
    with open("output/VALID_SPU_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Print results
    print(f"\n✅ VALID SPU PROCESSING COMPLETE!")
    print(f"📊 Total Recommendations: {len(df):,}")
    print(f"🏪 Stores Affected: {df['Store_Code'].nunique():,}")
    print(f"📦 Valid SPUs Affected: {df['SPU_Code'].nunique():,}")
    print(f"💰 Total Business Impact: ¥{df['Business_Impact_Yuan'].sum():,.2f}")
    print(f"🆕 New Items: {(df['Is_New_Item'] == 'YES').sum():,}")
    print(f"📈 Increases: {(df['Action'] == 'INCREASE').sum():,}")
    print(f"📉 Decreases: {(df['Action'] == 'DECREASE').sum():,}")
    
    # Check our test case
    test_case = df[df['Store_Code'] == 13003]
    if not test_case.empty:
        print(f"\n🔍 TEST CASE - Store 13003:")
        print(f"Total recommendations: {len(test_case)}")
        
        # Look for SPU 15S1010
        spu_15s1010 = test_case[test_case['SPU_Code'] == '15S1010']
        if not spu_15s1010.empty:
            print(f"SPU 15S1010 found:")
            cols = ['SPU_Code', 'Target SPU Quantity', 'Current_Quantity', 'Action', 'Consolidation_Logic']
            print(spu_15s1010[cols].to_string(index=False))
        else:
            print("SPU 15S1010 not found (might have been filtered out)")

def main():
    """Main execution function"""
    start_time = datetime.now()
    print("🚀 Starting VALID SPU Client Recommendation Generation")
    print("=" * 60)
    print("✅ Processing ONLY valid alphanumeric SPU codes")
    print("❌ Ignoring invalid store_product format codes")
    print("🔄 Applying Step 15 consolidation logic")
    print("=" * 60)
    
    # Load and filter to valid SPUs only
    meaningful_df = load_and_filter_valid_spus()
    
    # Consolidate by Store+SPU combination
    consolidated_df = consolidate_by_store_spu(meaningful_df)
    
    # Load supporting data
    spu_lookup, store_lookup = load_supporting_data()
    
    # Identify existing items
    existing_items = identify_existing_items(meaningful_df)
    
    # Create final format
    final_df = create_final_format(consolidated_df, spu_lookup, store_lookup, existing_items)
    
    # Save results
    save_results(final_df)
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\n🎉 Completed in {duration.total_seconds():.1f} seconds!")
    print(f"🎯 ONLY valid SPU codes processed - no invalid formats!")

if __name__ == "__main__":
    main() 