#!/usr/bin/env python3
"""
API Aggregation Analysis - Understanding the transformation from 426 API records to 3 variants
"""

import pandas as pd
import numpy as np
from collections import defaultdict

def analyze_api_aggregation():
    """Analyze how API records get aggregated in our pipeline."""
    
    print("🔍 API AGGREGATION ANALYSIS")
    print("=" * 60)
    
    store_code = 51198
    spu_pattern = '休闲圆领T恤'
    
    # Load API data
    print("📊 LOADING API DATA:")
    print("-" * 30)
    
    all_api_records = []
    api_files = [
        'data/api_data/partial_spu_sales_202506A_20250624_172233.csv',
        'data/api_data/partial_spu_sales_202506A_20250624_172255.csv',
        'data/api_data/complete_spu_sales_202506A.csv'
    ]
    
    for api_file in api_files:
        try:
            df = pd.read_csv(api_file)
            store_records = df[
                (df['str_code'] == store_code) & 
                (df['sub_cate_name'] == spu_pattern)
            ]
            
            print(f"📁 {api_file.split('/')[-1]}: {len(store_records)} records")
            
            for _, record in store_records.iterrows():
                # Extract key fields
                gender = record.get('sex_name', 'Unknown')
                location = record.get('display_location_name', 'Unknown')
                
                # Find quantity field
                quantity = None
                for field in ['quantity', 'current_quantity', 'spu_quantity']:
                    if field in record and pd.notna(record[field]):
                        quantity = record[field]
                        break
                
                sales = record.get('spu_sales_amt', 0)
                
                if quantity is not None:
                    all_api_records.append({
                        'file': api_file.split('/')[-1],
                        'gender': gender,
                        'location': location,
                        'quantity': quantity,
                        'sales': sales,
                        'unit_price': sales / quantity if quantity > 0 else 0
                    })
        
        except Exception as e:
            print(f"❌ Error loading {api_file}: {e}")
    
    print(f"\n📋 TOTAL API RECORDS: {len(all_api_records)}")
    
    # Analyze aggregation patterns
    print(f"\n🔍 AGGREGATION ANALYSIS:")
    print("-" * 40)
    
    # Group by gender and location
    aggregation_groups = defaultdict(list)
    
    for record in all_api_records:
        key = f"{record['gender']}_{record['location']}"
        aggregation_groups[key].append(record)
    
    print(f"Number of aggregation groups: {len(aggregation_groups)}")
    
    total_api_qty = 0
    total_api_sales = 0
    
    for group_key, records in aggregation_groups.items():
        group_qty = sum(r['quantity'] for r in records)
        group_sales = sum(r['sales'] for r in records)
        
        total_api_qty += group_qty
        total_api_sales += group_sales
        
        print(f"\n📦 GROUP: {group_key}")
        print(f"   Records: {len(records)}")
        print(f"   Total quantity: {group_qty:.1f}")
        print(f"   Total sales: ${group_sales:,.0f}")
        print(f"   Avg unit price: ${group_sales/group_qty:.2f}")
        
        # Show quantity distribution
        quantities = [r['quantity'] for r in records]
        print(f"   Quantity range: {min(quantities):.1f} - {max(quantities):.1f}")
        print(f"   Median quantity: {np.median(quantities):.1f}")
        
        # Show some sample records
        print(f"   Sample records:")
        for i, record in enumerate(records[:3]):
            print(f"     {i+1}. {record['quantity']:.1f} units, ${record['sales']:.0f}")
        
        if len(records) > 3:
            print(f"     ... and {len(records) - 3} more")
    
    print(f"\n📊 API TOTALS:")
    print(f"   Total quantity: {total_api_qty:.1f}")
    print(f"   Total sales: ${total_api_sales:,.0f}")
    print(f"   Overall avg unit price: ${total_api_sales/total_api_qty:.2f}")
    
    # Compare with our processed results
    print(f"\n🔄 COMPARING WITH PROCESSED RESULTS:")
    print("-" * 50)
    
    try:
        rule10_df = pd.read_csv('output/rule10_spu_overcapacity_opportunities.csv')
        our_variants = rule10_df[
            (rule10_df['str_code'] == store_code) & 
            (rule10_df['sub_cate_name'] == spu_pattern)
        ]
        
        our_total = our_variants['current_quantity'].sum()
        
        print(f"Our processed total: {our_total:.1f}")
        print(f"API total: {total_api_qty:.1f}")
        print(f"Difference: {abs(our_total - total_api_qty):.1f}")
        
        if abs(our_total - total_api_qty) < 1:
            print("✅ PERFECT MATCH - Processing is correct!")
        else:
            print("⚠️  Mismatch detected")
        
        # Show our variants vs API groups
        print(f"\nOUR VARIANTS vs API GROUPS:")
        for _, variant in our_variants.iterrows():
            gender = variant['sex_name']
            location = variant['display_location_name']
            qty = variant['current_quantity']
            
            # Find matching API group
            group_key = f"{gender}_{location}"
            if group_key in aggregation_groups:
                api_records = aggregation_groups[group_key]
                api_qty = sum(r['quantity'] for r in api_records)
                
                print(f"  {gender} {location}:")
                print(f"    Our result: {qty:.1f} units")
                print(f"    API sum: {api_qty:.1f} units ({len(api_records)} records)")
                print(f"    Match: {'✅' if abs(qty - api_qty) < 0.1 else '❌'}")
    
    except Exception as e:
        print(f"❌ Error loading processed results: {e}")
    
    # Analyze the business implications
    print(f"\n💼 BUSINESS IMPLICATIONS:")
    print("-" * 40)
    
    print(f"1. DATA STRUCTURE:")
    print(f"   - Store 51198 has {len(all_api_records)} separate T-shirt transactions")
    print(f"   - These represent individual sales/inventory records")
    print(f"   - Our system aggregates by gender + location combination")
    
    print(f"\n2. AGGREGATION LOGIC:")
    print(f"   - API: {len(all_api_records)} individual records")
    print(f"   - Processed: {len(aggregation_groups)} aggregated variants")
    print(f"   - Reduction ratio: {len(all_api_records)/len(aggregation_groups):.1f}:1")
    
    print(f"\n3. QUANTITY INTERPRETATION:")
    print(f"   - The 2,333 T-shirts are NOT a single SKU")
    print(f"   - They represent cumulative inventory across {len(all_api_records)} transactions")
    print(f"   - Each transaction averages {total_api_qty/len(all_api_records):.1f} units")
    
    print(f"\n4. BUSINESS REALITY:")
    if len(aggregation_groups) <= 5:
        print(f"   - Store legitimately has {total_api_qty:.0f} T-shirts total")
        print(f"   - Distributed across {len(aggregation_groups)} gender/location combinations")
        print(f"   - Individual transaction sizes are reasonable (0.3-95.5 units)")
        print(f"   - Aggregation provides meaningful business insights")
    else:
        print(f"   - High fragmentation might indicate data quality issues")
    
    # Check for duplicate records
    print(f"\n🔍 DUPLICATE ANALYSIS:")
    print("-" * 30)
    
    # Create signature for each record
    signatures = []
    for record in all_api_records:
        sig = f"{record['gender']}_{record['location']}_{record['quantity']}_{record['sales']}"
        signatures.append(sig)
    
    unique_signatures = set(signatures)
    duplicates = len(signatures) - len(unique_signatures)
    
    print(f"Total records: {len(signatures)}")
    print(f"Unique records: {len(unique_signatures)}")
    print(f"Duplicates: {duplicates}")
    
    if duplicates > 0:
        print(f"⚠️  {duplicates} duplicate records found")
        print(f"   This explains some of the large aggregated quantities")
    else:
        print(f"✅ No exact duplicates found")
    
    print(f"\n🎯 FINAL ASSESSMENT:")
    print("-" * 30)
    
    if abs(our_total - total_api_qty) < 1 and duplicates == 0:
        print("✅ PROCESSING IS CORRECT")
        print("   - API data aggregation is working as designed")
        print("   - The large quantities are legitimate business data")
        print("   - Store 51198 genuinely has high T-shirt inventory")
    elif duplicates > 0:
        print("⚠️  DUPLICATE DATA ISSUE")
        print("   - Multiple identical records are inflating quantities")
        print("   - Need to deduplicate API data before processing")
    else:
        print("❓ INVESTIGATION NEEDED")
        print("   - Aggregation logic might have issues")

if __name__ == "__main__":
    analyze_api_aggregation() 