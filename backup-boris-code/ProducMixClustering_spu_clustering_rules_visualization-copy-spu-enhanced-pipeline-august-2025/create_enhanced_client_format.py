#!/usr/bin/env python3
"""
Create Enhanced Client Format with SPU IDs and Store Details

This script creates an improved client format file that includes:
1. Dedicated SPU ID column
2. Consistent English-only style tags
3. Store-level details and group allocation information
4. Clean, parseable format for business systems
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re
import os
from typing import Dict, List, Tuple

def extract_spu_id(style_tag: str) -> str:
    """Extract SPU ID from style tag."""
    # Look for patterns like: 140, 25V, 15C8042, etc.
    patterns = [
        r'(\d{2,3}[A-Z]\d{4})',  # 15C8042
        r'(\d{2,3}[A-Z]\d{3})',  # 25V001
        r'(\d{2,3}[A-Z])',       # 25V
        r'(\d{3,4})',            # 140, 1234
    ]
    
    for pattern in patterns:
        match = re.search(pattern, style_tag)
        if match:
            return match.group(1)
    
    return "UNKNOWN"

def clean_style_tags(style_tag: str) -> str:
    """Clean style tags to ensure English-only format."""
    
    # Enhanced translation dictionary
    translations = {
        # Categories
        '休闲圆领T恤': 'Casual Round Neck T-shirt',
        '凉感圆领T恤': 'Cool Touch Round Neck T-shirt',
        '无袖T恤': 'Sleeveless T-shirt',
        '休闲POLO': 'Casual Polo',
        '凉感POLO': 'Cool Touch Polo',
        '休闲衬衣': 'Casual Shirt',
        '直筒裤': 'Straight Pants',
        '锥形裤': 'Tapered Pants',
        '束脚裤': 'Jogger Pants',
        '喇叭裤': 'Flare Pants',
        '阔腿裤': 'Wide Leg Pants',
        '中裤': 'Mid-length Pants',
        '短裤': 'Shorts',
        '工装裤': 'Cargo Pants',
        '牛仔裤': 'Jeans',
        '连衣裙': 'Dress',
        'X版连衣裙': 'Oversized Dress',
        '背带裙': 'Suspender Dress',
        '潮鞋': 'Trendy Shoes',
        '内衣': 'Underwear',
        '卫衣': 'Hoodie',
        '圆领卫衣': 'Round Neck Hoodie',
        '针织防晒衣': 'Knit Sun Protection Jacket',
        '衬衫': 'Shirt',
        # Seasons
        '夏': 'Summer',
        '春': 'Spring',
        '秋': 'Autumn',
        '冬': 'Winter',
        # Gender
        '男': 'Men',
        '女': 'Women',
        '中': 'Unisex',
    }
    
    # Apply translations
    cleaned = style_tag
    for chinese, english in translations.items():
        cleaned = cleaned.replace(chinese, english)
    
    # Remove remaining Chinese characters and SPU codes
    cleaned = re.sub(r'[\u4e00-\u9fff]', '', cleaned)  # Remove Chinese
    cleaned = re.sub(r'_[^,\]]*', '', cleaned)  # Remove _patterns
    cleaned = re.sub(r'\d{2,4}[A-Z]?\d*', '', cleaned)  # Remove SPU codes
    cleaned = re.sub(r',\s*,', ',', cleaned)  # Remove double commas
    cleaned = re.sub(r',\s*\]', ']', cleaned)  # Clean up endings
    
    return cleaned

def create_enhanced_client_format() -> None:
    """Create enhanced client format with SPU IDs and store details."""
    
    print("🚀 CREATING ENHANCED CLIENT FORMAT")
    print("=" * 60)
    
    # Load necessary data files
    print("📁 Loading data files...")
    
    # Load the original client format
    client_file = "output/rule_based_client_format_merchandise_planning_BACKUP_20250629_090258.csv"
    if not os.path.exists(client_file):
        print(f"❌ Client format file not found: {client_file}")
        return
    
    df = pd.read_csv(client_file)
    
    # Load clustering results for store-level details
    clustering_file = "output/clustering_results_spu.csv"
    if os.path.exists(clustering_file):
        cluster_df = pd.read_csv(clustering_file)
        print(f"✅ Loaded clustering data: {len(cluster_df)} stores")
    else:
        print("⚠️ Clustering file not found, will use group-level only")
        cluster_df = None
    
    print(f"📊 Processing {len(df):,} recommendations...")
    
    # Extract SPU IDs
    print("🔍 Extracting SPU IDs...")
    df['SPU_ID'] = df['Target Style Tags'].apply(extract_spu_id)
    
    # Clean style tags
    print("🧹 Cleaning style tags...")
    df['Clean_Style_Tags'] = df['Target Style Tags'].apply(clean_style_tags)
    
    # Add store-level information if available
    if cluster_df is not None:
        # Create store group to store mapping
        print("🏪 Adding store-level details...")
        
        # Group stores by cluster
        store_groups = {}
        for _, row in cluster_df.iterrows():
            cluster_id = row['Cluster']
            store_code = row['str_code']
            group_name = f"Store Group {cluster_id + 1}"
            
            if group_name not in store_groups:
                store_groups[group_name] = []
            store_groups[group_name].append(store_code)
        
        # Add store details to each recommendation
        enhanced_records = []
        
        for _, row in df.iterrows():
            store_group = row['Store Group Name']
            if store_group in store_groups:
                stores_in_group = store_groups[store_group]
                
                # Create a record for each store in the group
                for store_code in stores_in_group:
                    enhanced_record = {
                        'Year': row['Year'],
                        'Month': row['Month'],
                        'Period': row['Period'],
                        'Store_Group_Name': store_group,
                        'Store_Code': store_code,
                        'SPU_ID': row['SPU_ID'],
                        'Target_Style_Tags': row['Clean_Style_Tags'],
                        'Target_SPU_Quantity': row['Target SPU Quantity'],
                        'Group_Total_Stores': len(stores_in_group),
                        'Allocation_Type': 'Group_Based'
                    }
                    enhanced_records.append(enhanced_record)
            else:
                # Keep original record if no store mapping
                enhanced_record = {
                    'Year': row['Year'],
                    'Month': row['Month'],
                    'Period': row['Period'],
                    'Store_Group_Name': row['Store Group Name'],
                    'Store_Code': 'GROUP_LEVEL',
                    'SPU_ID': row['SPU_ID'],
                    'Target_Style_Tags': row['Clean_Style_Tags'],
                    'Target_SPU_Quantity': row['Target SPU Quantity'],
                    'Group_Total_Stores': 0,
                    'Allocation_Type': 'Group_Only'
                }
                enhanced_records.append(enhanced_record)
        
        enhanced_df = pd.DataFrame(enhanced_records)
        
    else:
        # No clustering data - enhance existing format
        enhanced_df = df.copy()
        enhanced_df['Store_Code'] = 'GROUP_LEVEL'
        enhanced_df['SPU_ID'] = enhanced_df['SPU_ID']
        enhanced_df['Target_Style_Tags'] = enhanced_df['Clean_Style_Tags']
        enhanced_df['Group_Total_Stores'] = 0
        enhanced_df['Allocation_Type'] = 'Group_Only'
        enhanced_df = enhanced_df.rename(columns={'Store Group Name': 'Store_Group_Name'})
    
    # Apply quantity filtering (35-unit cap as recommended)
    print("🔧 Applying quantity filtering...")
    enhanced_df['Target_SPU_Quantity'] = enhanced_df['Target_SPU_Quantity'].clip(upper=35)
    
    # Reorder columns for client format
    final_columns = [
        'Year',
        'Month', 
        'Period',
        'Store_Group_Name',
        'Store_Code',
        'SPU_ID',
        'Target_Style_Tags',
        'Target_SPU_Quantity',
        'Group_Total_Stores',
        'Allocation_Type'
    ]
    
    enhanced_df = enhanced_df[final_columns]
    
    # Save enhanced file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output/enhanced_client_format_merchandise_planning_{timestamp}.csv"
    
    enhanced_df.to_csv(output_file, index=False)
    
    # Statistics
    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    
    print(f"\n✅ ENHANCED CLIENT FORMAT CREATED:")
    print(f"   • File: {output_file}")
    print(f"   • Size: {file_size_mb:.1f} MB")
    print(f"   • Records: {len(enhanced_df):,}")
    print(f"   • Unique SPU IDs: {enhanced_df['SPU_ID'].nunique():,}")
    print(f"   • Store Groups: {enhanced_df['Store_Group_Name'].nunique()}")
    print(f"   • Individual Stores: {enhanced_df['Store_Code'].nunique()}")
    
    # Sample output
    print(f"\n📋 SAMPLE ENHANCED OUTPUT:")
    sample = enhanced_df.head(3)
    for _, row in sample.iterrows():
        print(f"   • Store {row['Store_Code']} ({row['Store_Group_Name']})")
        print(f"     SPU: {row['SPU_ID']} | {row['Target_Style_Tags']}")
        print(f"     Quantity: {row['Target_SPU_Quantity']} units | Group has {row['Group_Total_Stores']} stores")
    
    # Quality checks
    print(f"\n🔍 QUALITY CHECKS:")
    spu_unknown = (enhanced_df['SPU_ID'] == 'UNKNOWN').sum()
    chinese_remaining = enhanced_df['Target_Style_Tags'].str.contains(r'[\u4e00-\u9fff]', na=False).sum()
    
    print(f"   • SPU IDs extracted: {enhanced_df['SPU_ID'].nunique():,} unique IDs")
    print(f"   • Unknown SPU IDs: {spu_unknown:,} ({spu_unknown/len(enhanced_df)*100:.1f}%)")
    print(f"   • Chinese characters remaining: {chinese_remaining:,} ({chinese_remaining/len(enhanced_df)*100:.1f}%)")
    print(f"   • Quantity range: {enhanced_df['Target_SPU_Quantity'].min()}-{enhanced_df['Target_SPU_Quantity'].max()}")
    
    print(f"\n🎯 ENHANCEMENTS DELIVERED:")
    print(f"   ✅ Dedicated SPU_ID column")
    print(f"   ✅ Cleaned English-only style tags")
    print(f"   ✅ Store-level details (when available)")
    print(f"   ✅ Group allocation information")
    print(f"   ✅ Quantity filtering applied (max 35 units)")
    print(f"   ✅ Ready for FF delivery")
    
    print("=" * 60)

if __name__ == "__main__":
    create_enhanced_client_format() 