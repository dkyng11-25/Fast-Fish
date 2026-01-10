#!/usr/bin/env python3
"""
Create Filtered Client Format Output - Remove Outliers

This script creates a cleaned version of the client format file by:
1. Capping quantities at 35 units maximum (moderate filtering)
2. Maintaining all records but with more reasonable quantities
3. Preserving the exact client format structure
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any
import os

def create_filtered_client_format() -> None:
    """Create a filtered version of the client format file without outliers."""
    
    print("🧹 CREATING FILTERED CLIENT FORMAT (NO OUTLIERS)")
    print("=" * 60)
    
    # Load the original comprehensive file
    input_file = "output/rule_based_client_format_merchandise_planning_BACKUP_20250629_090258.csv"
    
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return
    
    print(f"📁 Loading: {input_file}")
    df = pd.read_csv(input_file)
    
    # Original statistics
    original_records = len(df)
    original_total_qty = df['Target SPU Quantity'].sum()
    original_avg_qty = df['Target SPU Quantity'].mean()
    original_max_qty = df['Target SPU Quantity'].max()
    
    print(f"\n📊 ORIGINAL FILE STATISTICS:")
    print(f"   • Total records: {original_records:,}")
    print(f"   • Total SPU quantity: {original_total_qty:,}")
    print(f"   • Average quantity: {original_avg_qty:.1f}")
    print(f"   • Maximum quantity: {original_max_qty}")
    
    # Apply moderate filtering (cap at 35 units)
    QUANTITY_CAP = 35
    
    # Create filtered dataframe
    filtered_df = df.copy()
    filtered_df['Target SPU Quantity'] = filtered_df['Target SPU Quantity'].clip(upper=QUANTITY_CAP)
    
    # Calculate impact
    records_affected = (df['Target SPU Quantity'] > QUANTITY_CAP).sum()
    new_total_qty = filtered_df['Target SPU Quantity'].sum()
    new_avg_qty = filtered_df['Target SPU Quantity'].mean()
    new_max_qty = filtered_df['Target SPU Quantity'].max()
    quantity_reduction = original_total_qty - new_total_qty
    
    print(f"\n🎯 FILTERING APPLIED:")
    print(f"   • Quantity cap: {QUANTITY_CAP} units maximum")
    print(f"   • Records affected: {records_affected:,} ({records_affected/original_records*100:.1f}%)")
    print(f"   • Records preserved: {len(filtered_df):,} (100%)")
    
    print(f"\n📈 FILTERED FILE STATISTICS:")
    print(f"   • Total records: {len(filtered_df):,}")
    print(f"   • Total SPU quantity: {new_total_qty:,}")
    print(f"   • Average quantity: {new_avg_qty:.1f}")
    print(f"   • Maximum quantity: {new_max_qty}")
    print(f"   • Quantity reduction: {quantity_reduction:,} units ({quantity_reduction/original_total_qty*100:.1f}%)")
    
    # Save filtered file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output/rule_based_client_format_merchandise_planning_FILTERED_{timestamp}.csv"
    
    filtered_df.to_csv(output_file, index=False)
    
    # Get file size
    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    
    print(f"\n✅ FILTERED FILE CREATED:")
    print(f"   • File: {output_file}")
    print(f"   • Size: {file_size_mb:.1f} MB")
    print(f"   • Format: Ready for client delivery")
    
    # Verify format compliance
    print(f"\n🔍 FORMAT VERIFICATION:")
    print(f"   • Columns: {list(filtered_df.columns)}")
    print(f"   • Store Groups: {filtered_df['Store Group Name'].nunique()}")
    print(f"   • Time Periods: {filtered_df[['Year', 'Month', 'Period']].drop_duplicates().values.tolist()}")
    print(f"   • Quantity Range: {filtered_df['Target SPU Quantity'].min()}-{filtered_df['Target SPU Quantity'].max()}")
    
    # Sample output
    print(f"\n📋 SAMPLE OUTPUT:")
    sample_df = filtered_df.head(3)
    for _, row in sample_df.iterrows():
        print(f"   • {row['Store Group Name']}: {row['Target Style Tags']} → {row['Target SPU Quantity']} units")
    
    # Business impact summary
    print(f"\n💼 BUSINESS IMPACT:")
    print(f"   • More realistic quantities (max {QUANTITY_CAP} vs {original_max_qty})")
    print(f"   • Reduced extreme recommendations by {quantity_reduction:,} units")
    print(f"   • Maintained comprehensive coverage ({len(filtered_df):,} recommendations)")
    print(f"   • Preserved all store groups and product combinations")
    
    print(f"\n🎉 FILTERING COMPLETE!")
    print(f"   Filtered file ready for client delivery: {output_file}")
    print("=" * 60)

if __name__ == "__main__":
    create_filtered_client_format() 