#!/usr/bin/env python3
"""
Quantity Source Tracing Script
Traces the origin of suspicious high quantities through the pipeline:
1. Step 10 raw output files
2. Step 13 consolidated files  
3. Step 15 final processing
4. Original API data (if available)
"""

import pandas as pd
import numpy as np
import os
import glob
from typing import Dict, List, Any

def trace_suspicious_quantities() -> None:
    """Trace suspicious quantities through the pipeline."""
    
    print("🔍 TRACING SUSPICIOUS QUANTITIES THROUGH PIPELINE")
    print("=" * 80)
    
    # Define the suspicious cases we found
    suspicious_cases = [
        {'store': '51198', 'spu': '51198_休闲圆领T恤', 'quantity': 2333.5},
        {'store': '37117', 'spu': '37117_休闲圆领T恤', 'quantity': 1912.2},
        {'store': '35043', 'spu': '35043_休闲圆领T恤', 'quantity': 1853.6},
        {'store': '61060', 'spu': '61060_休闲圆领T恤', 'quantity': 1799.7},
        {'store': '61086', 'spu': '61086_休闲圆领T恤', 'quantity': 1734.2}
    ]
    
    print(f"🎯 Tracking {len(suspicious_cases)} suspicious cases:")
    for case in suspicious_cases:
        print(f"   Store {case['store']}: {case['quantity']} units of {case['spu'].split('_')[1]}")
    
    # Step 1: Check Step 10 raw output files
    print(f"\n" + "=" * 80)
    print(f"📋 STEP 1: CHECKING STEP 10 RAW OUTPUT FILES")
    print("=" * 80)
    
    step10_files = [
        'output/rule10_spu_overcapacity_results.csv',
        'output/rule10_spu_overcapacity_opportunities.csv',
        'src/data/rule10_overcapacity_spu_output.csv'
    ]
    
    step10_data = None
    for file_path in step10_files:
        if os.path.exists(file_path):
            print(f"✅ Found: {file_path}")
            try:
                df = pd.read_csv(file_path)
                print(f"   Records: {len(df):,}")
                print(f"   Columns: {list(df.columns)}")
                
                # Check for our suspicious cases
                for case in suspicious_cases:
                    if 'str_code' in df.columns and 'spu_code' in df.columns:
                        match = df[(df['str_code'].astype(str) == case['store']) & 
                                 (df['spu_code'].astype(str) == case['spu'])]
                    elif 'store_code' in df.columns and 'spu_code' in df.columns:
                        match = df[(df['store_code'].astype(str) == case['store']) & 
                                 (df['spu_code'].astype(str) == case['spu'])]
                    else:
                        print(f"   ⚠️  Cannot match - missing store/spu columns")
                        continue
                        
                    if len(match) > 0:
                        print(f"   🔍 Found {case['store']} {case['spu'].split('_')[1]}:")
                        for _, row in match.iterrows():
                            print(f"      {dict(row)}")
                        if step10_data is None:
                            step10_data = df
                
                # Show sample of high quantities in this file
                if 'current_quantity' in df.columns:
                    high_qty = df[df['current_quantity'] > 1000]
                    if len(high_qty) > 0:
                        print(f"   📊 High quantities (>1000) in this file: {len(high_qty)}")
                        print(f"      Top 5: {high_qty['current_quantity'].nlargest(5).values}")
                
            except Exception as e:
                print(f"   ❌ Error reading {file_path}: {e}")
        else:
            print(f"❌ Not found: {file_path}")
    
    # Step 2: Check if there are detailed SPU-level files
    print(f"\n" + "=" * 80)
    print(f"📋 STEP 2: SEARCHING FOR DETAILED SPU FILES")
    print("=" * 80)
    
    # Look for any files with detailed SPU data
    spu_patterns = [
        'output/*spu*detail*.csv',
        'output/*spu*opportunities*.csv', 
        'output/*overcapacity*detail*.csv',
        'src/data/*rule10*detail*.csv',
        'src/data/*overcapacity*spu*.csv'
    ]
    
    for pattern in spu_patterns:
        files = glob.glob(pattern)
        for file_path in files:
            print(f"✅ Found detailed file: {file_path}")
            try:
                df = pd.read_csv(file_path)
                print(f"   Records: {len(df):,}, Columns: {len(df.columns)}")
                
                # Check for suspicious quantities
                if 'current_quantity' in df.columns or any('quantity' in col for col in df.columns):
                    qty_cols = [col for col in df.columns if 'quantity' in col.lower()]
                    print(f"   Quantity columns: {qty_cols}")
                    
                    for qty_col in qty_cols:
                        if df[qty_col].dtype in ['float64', 'int64']:
                            high_qty = df[df[qty_col] > 1000]
                            if len(high_qty) > 0:
                                print(f"   📊 High {qty_col} (>1000): {len(high_qty)} records")
                                print(f"      Max: {df[qty_col].max():.1f}")
                                
                                # Check our specific cases
                                for case in suspicious_cases:
                                    store_cols = [col for col in df.columns if 'store' in col.lower() or 'str_code' in col]
                                    spu_cols = [col for col in df.columns if 'spu' in col.lower()]
                                    
                                    if store_cols and spu_cols:
                                        store_col = store_cols[0]
                                        spu_col = spu_cols[0]
                                        match = df[(df[store_col].astype(str) == case['store']) & 
                                                 (df[spu_col].astype(str) == case['spu'])]
                                        if len(match) > 0:
                                            print(f"   🎯 Found {case['store']} in {file_path}:")
                                            print(f"      {qty_col}: {match[qty_col].iloc[0]:.1f}")
                
            except Exception as e:
                print(f"   ❌ Error reading {file_path}: {e}")
    
    # Step 3: Check the actual Step 10 source code
    print(f"\n" + "=" * 80)
    print(f"📋 STEP 3: EXAMINING STEP 10 SOURCE CODE")
    print("=" * 80)
    
    step10_source = 'src/step10_spu_assortment_optimization.py'
    if os.path.exists(step10_source):
        print(f"✅ Found Step 10 source: {step10_source}")
        try:
            with open(step10_source, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for quantity calculations
            lines = content.split('\n')
            quantity_lines = []
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in ['quantity', 'sales_amount', 'unit_price', 'current_qty']):
                    quantity_lines.append((i+1, line.strip()))
            
            if quantity_lines:
                print(f"   📊 Found {len(quantity_lines)} lines with quantity-related calculations:")
                for line_num, line in quantity_lines[:20]:  # Show first 20
                    print(f"   {line_num:4d}: {line}")
                    
                if len(quantity_lines) > 20:
                    print(f"   ... and {len(quantity_lines) - 20} more lines")
            
            # Look for specific patterns that might cause issues
            problematic_patterns = [
                'sales_amount',
                'current_quantity = sales',
                'quantity = sales',
                'df[\'current_quantity\'] = df[\'sales',
                'realistic_unit_price'
            ]
            
            print(f"\n   🔍 Checking for problematic patterns:")
            for pattern in problematic_patterns:
                if pattern in content:
                    print(f"   ⚠️  Found pattern: '{pattern}'")
                    # Show context
                    pattern_lines = []
                    for i, line in enumerate(lines):
                        if pattern in line:
                            start = max(0, i-2)
                            end = min(len(lines), i+3)
                            context = lines[start:end]
                            print(f"      Context around line {i+1}:")
                            for j, ctx_line in enumerate(context):
                                marker = ">>>" if j == (i-start) else "   "
                                print(f"      {marker} {start+j+1:4d}: {ctx_line}")
                            print()
                else:
                    print(f"   ✅ Pattern not found: '{pattern}'")
                    
        except Exception as e:
            print(f"   ❌ Error reading source: {e}")
    else:
        print(f"❌ Step 10 source not found: {step10_source}")
    
    # Step 4: Check API data files for original sales amounts
    print(f"\n" + "=" * 80)
    print(f"📋 STEP 4: CHECKING ORIGINAL API DATA")
    print("=" * 80)
    
    api_data_patterns = [
        'data/api_data/*.csv',
        'src/data/*.csv',
        'output/weather_data/*.csv',
        'data/*.csv'
    ]
    
    for pattern in api_data_patterns:
        files = glob.glob(pattern)
        for file_path in files:
            if 'weather' in file_path.lower():
                continue  # Skip weather files
                
            print(f"📁 Checking: {file_path}")
            try:
                df = pd.read_csv(file_path)
                if len(df) > 100000:  # Large files likely contain transaction data
                    print(f"   Large file: {len(df):,} records - checking for suspicious amounts")
                    
                    # Look for columns that might contain sales amounts
                    amount_cols = [col for col in df.columns if any(keyword in col.lower() 
                                  for keyword in ['sales', 'amount', 'revenue', 'value', 'price'])]
                    
                    if amount_cols:
                        print(f"   Amount columns: {amount_cols}")
                        
                        for col in amount_cols:
                            if df[col].dtype in ['float64', 'int64']:
                                # Check if any values match our suspicious quantities
                                for case in suspicious_cases:
                                    # Check for exact matches or close matches
                                    matches = df[abs(df[col] - case['quantity']) < 0.1]
                                    if len(matches) > 0:
                                        print(f"   🎯 FOUND MATCH for {case['quantity']} in column '{col}'!")
                                        print(f"      Store context: {matches.head()}")
                                        
                                        # Check if store info is available
                                        store_cols = [c for c in df.columns if 'store' in c.lower() or 'str' in c.lower()]
                                        if store_cols:
                                            store_col = store_cols[0]
                                            store_matches = matches[matches[store_col].astype(str) == case['store']]
                                            if len(store_matches) > 0:
                                                print(f"      🎯 EXACT STORE MATCH found!")
                                                print(f"      {dict(store_matches.iloc[0])}")
                
            except Exception as e:
                print(f"   ❌ Error reading {file_path}: {e}")
    
    # Step 5: Summary and recommendations
    print(f"\n" + "=" * 80)
    print(f"🎯 SUMMARY & NEXT STEPS")
    print("=" * 80)
    
    print(f"Based on the tracing analysis:")
    print(f"1. Check if Step 10 is reading sales amounts as quantities")
    print(f"2. Verify unit price calculations in Step 10")
    print(f"3. Look for currency conversion issues")
    print(f"4. Check if aggregation is working correctly")
    print(f"5. Validate input data format expectations")

def main():
    """Run the quantity source tracing."""
    print("🚀 Starting Quantity Source Tracing")
    trace_suspicious_quantities()

if __name__ == "__main__":
    main() 