#!/usr/bin/env python3
"""
Fix Chinese Format for Compliance
=================================

Keep Chinese text but convert from pipe-separated format to bracket format for compliance.
"""

import pandas as pd
import os
from datetime import datetime

def fix_chinese_format():
    """Fix format while keeping Chinese text - convert pipe-separated to bracket format."""
    
    # Use the original output file (before translation)
    input_file = "../output/fast_fish_with_sell_through_analysis_20250714_095923.csv"
    
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return
    
    print(f"📂 Loading original file: {input_file}")
    df = pd.read_csv(input_file)
    
    print(f"📊 Loaded {len(df):,} records")
    print(f"📅 Current year values: {df['Year'].unique()}")
    print(f"📅 Current month values: {df['Month'].unique()}")
    
    # Fix year format - add brackets
    df['Year'] = '[' + df['Year'].astype(str) + ']'
    
    # Fix month format - zero-pad to 2 digits
    df['Month'] = df['Month'].astype(int).astype(str).str.zfill(2)
    
    # Fix style tags format - convert pipe-separated to bracket format (keep Chinese)
    def convert_pipe_to_bracket(style_text):
        """Convert pipe-separated Chinese text to bracket format."""
        if pd.isna(style_text) or style_text == '':
            return ''
        
        # Split by pipe and clean up
        parts = [part.strip() for part in str(style_text).split('|') if part.strip()]
        
        # Join with commas and wrap in brackets
        if parts:
            return '[' + ', '.join(parts) + ']'
        else:
            return ''
    
    print(f"🔄 Converting style tags from pipe-separated to bracket format...")
    df['Target_Style_Tags'] = df['Target_Style_Tags'].apply(convert_pipe_to_bracket)
    
    print(f"✅ Updated year values: {df['Year'].unique()}")
    print(f"✅ Updated month values: {df['Month'].unique()}")
    
    # Show sample style tag conversion
    sample_styles = df['Target_Style_Tags'].dropna().head(3).tolist()
    print(f"✅ Sample style tags format:")
    for i, style in enumerate(sample_styles[:2]):
        if len(style) > 60:
            style = style[:60] + "..."
        print(f"   {i+1}. {style}")
    
    # Generate output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"../output/fast_fish_chinese_compliant_{timestamp}.csv"
    
    # Save the corrected file
    df.to_csv(output_file, index=False)
    
    print(f"💾 Saved Chinese compliant file: {output_file}")
    print(f"📊 Final record count: {len(df):,}")
    
    # Quick validation
    print(f"\n🔍 FINAL VALIDATION:")
    print(f"   Year format: {df['Year'].iloc[0]} ✅")
    print(f"   Month format: {df['Month'].iloc[0]} ✅")
    print(f"   Period format: {df['Period'].iloc[0]} ✅")
    
    sample_style = df['Target_Style_Tags'].iloc[0]
    if len(sample_style) > 50:
        sample_style = sample_style[:50] + "..."
    print(f"   Style tags format: {sample_style} ✅")
    
    print(f"\n🎉 CHINESE FORMAT COMPLIANCE COMPLETED!")
    return output_file

if __name__ == "__main__":
    fix_chinese_format() 