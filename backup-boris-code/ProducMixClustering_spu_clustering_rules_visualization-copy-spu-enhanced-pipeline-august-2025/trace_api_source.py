#!/usr/bin/env python3
"""
Trace API Source - Check if giant T-shirt numbers exist in original API data
"""

import pandas as pd
import json
import os
from typing import Dict, List

def trace_api_source():
    """Trace Store 51198 T-shirt data back to original API files."""
    
    print("🔍 TRACING STORE 51198 T-SHIRT DATA TO API SOURCE")
    print("=" * 70)
    
    store_code = 51198
    spu_pattern = '休闲圆领T恤'
    
    # First, let's see what we calculated
    print("📊 OUR CALCULATED RESULTS:")
    print("-" * 40)
    
    rule10_df = pd.read_csv('output/rule10_spu_overcapacity_opportunities.csv')
    our_variants = rule10_df[
        (rule10_df['str_code'] == store_code) & 
        (rule10_df['sub_cate_name'] == spu_pattern)
    ]
    
    our_total = our_variants['current_quantity'].sum()
    print(f"Our calculated total: {our_total:.1f} T-shirts")
    print(f"Number of variants: {len(our_variants)}")
    
    for _, variant in our_variants.iterrows():
        gender = variant['sex_name']
        location = variant['display_location_name']
        qty = variant['current_quantity']
        print(f"  {gender} {location}: {qty:.1f} units")
    
    # Now let's check the original API data files
    print(f"\n🔍 CHECKING ORIGINAL API DATA FILES:")
    print("-" * 40)
    
    api_data_dir = 'data/api_data'
    api_files = []
    
    if os.path.exists(api_data_dir):
        for file in os.listdir(api_data_dir):
            if file.endswith('.csv'):
                api_files.append(os.path.join(api_data_dir, file))
    
    print(f"Found {len(api_files)} API data files to check")
    
    total_found_records = 0
    total_api_quantity = 0
    total_api_sales = 0
    api_records = []
    
    for api_file in api_files:
        print(f"\n📁 Checking: {os.path.basename(api_file)}")
        
        try:
            df = pd.read_csv(api_file)
            print(f"   Total records in file: {len(df):,}")
            
            # Look for Store 51198 records
            store_records = df[df['str_code'] == store_code]
            print(f"   Records for Store {store_code}: {len(store_records)}")
            
            if len(store_records) > 0:
                # Look for T-shirt records
                if 'sub_cate_name' in df.columns:
                    tshirt_records = store_records[store_records['sub_cate_name'] == spu_pattern]
                    print(f"   T-shirt records: {len(tshirt_records)}")
                    
                    if len(tshirt_records) > 0:
                        print(f"   📋 T-SHIRT RECORDS FOUND:")
                        
                        for _, record in tshirt_records.iterrows():
                            total_found_records += 1
                            
                            # Extract key fields
                            gender = record.get('sex_name', 'Unknown')
                            location = record.get('display_location_name', 'Unknown')
                            
                            # Check different quantity fields
                            quantity_fields = ['quantity', 'current_quantity', 'spu_quantity']
                            quantity_found = None
                            for field in quantity_fields:
                                if field in record and pd.notna(record[field]):
                                    quantity_found = record[field]
                                    break
                            
                            # Check sales amount
                            sales_amount = 0
                            if 'spu_sales_amt' in record and pd.notna(record['spu_sales_amt']):
                                sales_amount = record['spu_sales_amt']
                                total_api_sales += sales_amount
                            
                            if quantity_found is not None:
                                total_api_quantity += quantity_found
                            
                            print(f"      • {gender} {location}:")
                            print(f"        Quantity: {quantity_found}")
                            print(f"        Sales Amount: ${sales_amount:,.2f}")
                            
                            # Store for detailed analysis
                            api_records.append({
                                'file': os.path.basename(api_file),
                                'gender': gender,
                                'location': location,
                                'quantity': quantity_found,
                                'sales_amount': sales_amount,
                                'record': record.to_dict()
                            })
                else:
                    print(f"   ⚠️  No 'sub_cate_name' column found")
            
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
    
    # Summary comparison
    print(f"\n" + "=" * 70)
    print(f"📊 API vs CALCULATED COMPARISON")
    print("=" * 70)
    
    print(f"API Data Found:")
    print(f"  Total records: {total_found_records}")
    print(f"  Total quantity: {total_api_quantity}")
    print(f"  Total sales: ${total_api_sales:,.0f}")
    
    print(f"\nOur Calculations:")
    print(f"  Total records: {len(our_variants)}")
    print(f"  Total quantity: {our_total:.1f}")
    
    print(f"\n🔍 ANALYSIS:")
    
    if total_found_records == 0:
        print("❌ NO API RECORDS FOUND")
        print("   This suggests the data might be processed/transformed")
        print("   The giant numbers might be calculation artifacts")
    elif abs(total_api_quantity - our_total) < 1:
        print("✅ PERFECT MATCH")
        print("   API data matches our calculations exactly")
        print("   The giant numbers are REAL in the source data")
    elif total_api_quantity > 0:
        print("⚠️  PARTIAL MATCH")
        print(f"   API quantity: {total_api_quantity}")
        print(f"   Our quantity: {our_total:.1f}")
        print(f"   Difference: {abs(total_api_quantity - our_total):.1f}")
        print("   There might be processing differences")
    else:
        print("❓ UNCLEAR")
        print("   Found records but no clear quantity data")
    
    # Detailed record analysis
    if api_records:
        print(f"\n📋 DETAILED API RECORD ANALYSIS:")
        print("-" * 50)
        
        for i, record in enumerate(api_records):
            print(f"\nRecord {i+1} from {record['file']}:")
            print(f"  Gender: {record['gender']}")
            print(f"  Location: {record['location']}")
            print(f"  Quantity: {record['quantity']}")
            print(f"  Sales: ${record['sales_amount']:,.2f}")
            
            # Check if sales amount suspiciously matches quantity
            if record['quantity'] and record['sales_amount']:
                if abs(record['quantity'] - record['sales_amount']) < 10:
                    print(f"  🚨 SUSPICIOUS: Quantity ≈ Sales Amount!")
                    print(f"      This suggests quantity might actually be sales amount")
                
                if record['sales_amount'] > 1000:
                    unit_price = record['sales_amount'] / record['quantity'] if record['quantity'] > 0 else 0
                    print(f"  💰 Unit price: ${unit_price:.2f}")
                    
                    if unit_price < 5 or unit_price > 200:
                        print(f"  ⚠️  Unusual unit price - might indicate data issue")
    
    # Check if we can find the source transformation
    print(f"\n🔍 CHECKING SOURCE TRANSFORMATION:")
    print("-" * 50)
    
    # Look for mapping files or transformation logs
    mapping_files = [
        'data/spu_store_mapping.csv',
        'data/complete_spu_sales_mapping.csv'
    ]
    
    for mapping_file in mapping_files:
        if os.path.exists(mapping_file):
            print(f"\n📁 Checking mapping file: {os.path.basename(mapping_file)}")
            try:
                mapping_df = pd.read_csv(mapping_file)
                store_mapping = mapping_df[mapping_df['str_code'] == store_code]
                
                if len(store_mapping) > 0:
                    print(f"   Found {len(store_mapping)} records for Store {store_code}")
                    
                    if 'sub_cate_name' in mapping_df.columns:
                        tshirt_mapping = store_mapping[store_mapping['sub_cate_name'] == spu_pattern]
                        if len(tshirt_mapping) > 0:
                            print(f"   Found {len(tshirt_mapping)} T-shirt mapping records")
                            
                            for _, record in tshirt_mapping.head(3).iterrows():
                                qty = record.get('quantity', record.get('spu_quantity', 'N/A'))
                                sales = record.get('spu_sales_amt', 'N/A')
                                print(f"     Qty: {qty}, Sales: ${sales}")
                
            except Exception as e:
                print(f"   Error: {e}")
    
    print(f"\n🎯 FINAL VERDICT:")
    print("-" * 30)
    
    if total_found_records > 0 and abs(total_api_quantity - our_total) < 1:
        print("✅ THE GIANT NUMBERS ARE REAL")
        print("   Store 51198 genuinely has 2,333+ T-shirts in the API data")
        print("   Our processing pipeline is working correctly")
    elif total_found_records == 0:
        print("❌ CANNOT FIND SOURCE DATA")
        print("   Need to check if API files are the original source")
        print("   Or if there's another data source we're missing")
    else:
        print("⚠️  PROCESSING ARTIFACT SUSPECTED")
        print("   Discrepancies suggest transformation issues")
        print("   Need to investigate the processing pipeline")

if __name__ == "__main__":
    trace_api_source() 