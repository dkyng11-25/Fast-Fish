#!/usr/bin/env python3
"""
Extract Filtered Outliers - Show What Was Changed

This script identifies and saves the specific outliers that were filtered out
in both the Filtered (35-unit cap) and Conservative (25-unit cap) versions.
"""

import pandas as pd
from datetime import datetime
import os

def extract_filtered_outliers() -> None:
    """Extract and save the outliers that were filtered out in both versions."""
    
    print("🔍 EXTRACTING FILTERED OUTLIERS")
    print("=" * 50)
    
    # Load the original file
    original_file = "output/rule_based_client_format_merchandise_planning_BACKUP_20250629_090258.csv"
    
    if not os.path.exists(original_file):
        print(f"❌ Original file not found: {original_file}")
        return
    
    print(f"📁 Loading original file: {original_file}")
    df = pd.read_csv(original_file)
    
    # Define thresholds
    FILTERED_THRESHOLD = 35
    CONSERVATIVE_THRESHOLD = 25
    
    print(f"\n📊 ORIGINAL FILE ANALYSIS:")
    print(f"   • Total records: {len(df):,}")
    print(f"   • Quantity range: {df['Target SPU Quantity'].min()}-{df['Target SPU Quantity'].max()}")
    print(f"   • Records > {FILTERED_THRESHOLD}: {(df['Target SPU Quantity'] > FILTERED_THRESHOLD).sum():,}")
    print(f"   • Records > {CONSERVATIVE_THRESHOLD}: {(df['Target SPU Quantity'] > CONSERVATIVE_THRESHOLD).sum():,}")
    
    # Extract Filtered version outliers (>35 units)
    filtered_outliers = df[df['Target SPU Quantity'] > FILTERED_THRESHOLD].copy()
    filtered_outliers['Original_Quantity'] = filtered_outliers['Target SPU Quantity']
    filtered_outliers['Filtered_Quantity'] = FILTERED_THRESHOLD
    filtered_outliers['Quantity_Reduction'] = filtered_outliers['Original_Quantity'] - filtered_outliers['Filtered_Quantity']
    
    # Extract Conservative version outliers (>25 units)
    conservative_outliers = df[df['Target SPU Quantity'] > CONSERVATIVE_THRESHOLD].copy()
    conservative_outliers['Original_Quantity'] = conservative_outliers['Target SPU Quantity']
    conservative_outliers['Conservative_Quantity'] = conservative_outliers['Target SPU Quantity'].clip(upper=CONSERVATIVE_THRESHOLD)
    conservative_outliers['Quantity_Reduction'] = conservative_outliers['Original_Quantity'] - conservative_outliers['Conservative_Quantity']
    
    # Save Filtered outliers
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    filtered_outliers_file = f"output/filtered_outliers_35_cap_{timestamp}.csv"
    filtered_outliers_cols = ['Year', 'Month', 'Period', 'Store Group Name', 'Target Style Tags', 
                             'Original_Quantity', 'Filtered_Quantity', 'Quantity_Reduction']
    filtered_outliers[filtered_outliers_cols].to_csv(filtered_outliers_file, index=False)
    
    # Save Conservative outliers
    conservative_outliers_file = f"output/conservative_outliers_25_cap_{timestamp}.csv"
    conservative_outliers_cols = ['Year', 'Month', 'Period', 'Store Group Name', 'Target Style Tags',
                                 'Original_Quantity', 'Conservative_Quantity', 'Quantity_Reduction']
    conservative_outliers[conservative_outliers_cols].to_csv(conservative_outliers_file, index=False)
    
    print(f"\n🔧 FILTERED VERSION OUTLIERS (>35 units):")
    print(f"   • Records affected: {len(filtered_outliers):,}")
    print(f"   • Total quantity reduced: {filtered_outliers['Quantity_Reduction'].sum():,}")
    print(f"   • Average reduction per record: {filtered_outliers['Quantity_Reduction'].mean():.1f}")
    print(f"   • File saved: {filtered_outliers_file}")
    
    print(f"\n🛡️ CONSERVATIVE VERSION OUTLIERS (>25 units):")
    print(f"   • Records affected: {len(conservative_outliers):,}")
    print(f"   • Total quantity reduced: {conservative_outliers['Quantity_Reduction'].sum():,}")
    print(f"   • Average reduction per record: {conservative_outliers['Quantity_Reduction'].mean():.1f}")
    print(f"   • File saved: {conservative_outliers_file}")
    
    # Analyze patterns in outliers
    print(f"\n📈 OUTLIER PATTERNS ANALYSIS:")
    
    # Filtered outliers analysis
    print(f"\n🔧 Filtered Outliers (>35 units) - Top Patterns:")
    filtered_store_groups = filtered_outliers['Store Group Name'].value_counts().head(5)
    print("   Top Store Groups:")
    for store_group, count in filtered_store_groups.items():
        print(f"     • {store_group}: {count:,} outliers")
    
    # Most common style tags in filtered outliers
    filtered_style_patterns = filtered_outliers['Target Style Tags'].value_counts().head(3)
    print("   Top Style Tag Patterns:")
    for style, count in filtered_style_patterns.items():
        print(f"     • {style}: {count:,} cases")
    
    # Conservative outliers analysis
    print(f"\n🛡️ Conservative Outliers (>25 units) - Top Patterns:")
    conservative_store_groups = conservative_outliers['Store Group Name'].value_counts().head(5)
    print("   Top Store Groups:")
    for store_group, count in conservative_store_groups.items():
        print(f"     • {store_group}: {count:,} outliers")
    
    # Quantity distribution analysis
    print(f"\n📊 QUANTITY DISTRIBUTION IN OUTLIERS:")
    
    # Filtered outliers quantity distribution
    filtered_qty_dist = filtered_outliers['Original_Quantity'].value_counts().sort_index()
    print(f"   Filtered Outliers by Original Quantity:")
    for qty, count in filtered_qty_dist.items():
        print(f"     • {qty} units: {count:,} cases")
    
    # Show sample outliers
    print(f"\n📋 SAMPLE FILTERED OUTLIERS:")
    sample_filtered = filtered_outliers.head(5)
    for _, row in sample_filtered.iterrows():
        print(f"   • {row['Store Group Name']}: {row['Target Style Tags']}")
        print(f"     Original: {row['Original_Quantity']} → Filtered: {row['Filtered_Quantity']} (reduced by {row['Quantity_Reduction']})")
    
    print(f"\n📋 SAMPLE CONSERVATIVE OUTLIERS:")
    sample_conservative = conservative_outliers.head(5)
    for _, row in sample_conservative.iterrows():
        print(f"   • {row['Store Group Name']}: {row['Target Style Tags']}")
        print(f"     Original: {row['Original_Quantity']} → Conservative: {row['Conservative_Quantity']} (reduced by {row['Quantity_Reduction']})")
    
    # Summary statistics
    print(f"\n📈 SUMMARY STATISTICS:")
    print(f"   • Original total quantity: {df['Target SPU Quantity'].sum():,}")
    print(f"   • Filtered version reduces by: {filtered_outliers['Quantity_Reduction'].sum():,} units")
    print(f"   • Conservative version reduces by: {conservative_outliers['Quantity_Reduction'].sum():,} units")
    print(f"   • Percentage of records affected (Filtered): {len(filtered_outliers)/len(df)*100:.1f}%")
    print(f"   • Percentage of records affected (Conservative): {len(conservative_outliers)/len(df)*100:.1f}%")
    
    print(f"\n✅ OUTLIER EXTRACTION COMPLETE!")
    print(f"   • Filtered outliers file: {filtered_outliers_file}")
    print(f"   • Conservative outliers file: {conservative_outliers_file}")
    print("=" * 50)

if __name__ == "__main__":
    extract_filtered_outliers() 