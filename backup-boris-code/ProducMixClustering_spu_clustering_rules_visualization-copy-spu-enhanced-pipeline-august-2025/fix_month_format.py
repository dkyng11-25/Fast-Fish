#!/usr/bin/env python3
"""
Fix Month Format in Fast Fish Output
===================================

Convert single digit months (8) to zero-padded format (08) for client compliance.
"""

import pandas as pd
import os
from datetime import datetime

def fix_month_format():
    """Fix month format from single digit to zero-padded."""
    
    # Find the most recent output file
    input_file = "../output/fast_fish_with_sell_through_analysis_20250714_095923.csv"
    
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return
    
    print(f"📂 Loading file: {input_file}")
    df = pd.read_csv(input_file)
    
    print(f"📊 Loaded {len(df):,} records")
    print(f"📅 Current month values: {df['Month'].unique()}")
    
    # Fix month format - convert to zero-padded string
    df['Month'] = df['Month'].astype(str).str.zfill(2)
    
    print(f"✅ Fixed month values: {df['Month'].unique()}")
    
    # Save the fixed file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"../output/fast_fish_month_fixed_{timestamp}.csv"
    
    df.to_csv(output_file, index=False)
    print(f"💾 Saved fixed file: {output_file}")
    
    # Verify the fix
    print(f"\n🔍 Verification:")
    print(f"  Original file size: {os.path.getsize(input_file):,} bytes")
    print(f"  Fixed file size: {os.path.getsize(output_file):,} bytes")
    print(f"  Records: {len(df):,}")
    
    # Show sample of fixed data
    print(f"\n📋 Sample of fixed data:")
    print(df[['Year', 'Month', 'Period', 'Store_Group_Name', 'Target_SPU_Quantity']].head(3))
    
    return output_file

if __name__ == "__main__":
    fix_month_format() 