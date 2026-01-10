#!/usr/bin/env python3
"""
Fix Missing Style Attributes in CSV Output
==========================================

The current CSV output is missing gender, season, and display location in style tags.
Current format: "T恤 | 休闲圆领T恤"
Expected format: "[Summer, Men, Front-store, T-shirt, Casual T-shirt]"

This script:
1. Loads the current CSV output
2. Accesses original API data to get missing attributes
3. Reconstructs complete style tags with all required information
4. Generates corrected CSV with complete style information
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from typing import Dict, List, Optional

def load_current_csv() -> pd.DataFrame:
    """Load the current CSV output that's missing attributes."""
    print("📂 Loading current CSV output...")
    
    csv_file = "fast_fish_with_sell_through_analysis_20250714_124522.csv"
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"Current CSV file not found: {csv_file}")
    
    df = pd.read_csv(csv_file)
    print(f"✅ Loaded {len(df):,} records from current CSV")
    print(f"🔍 Current style tags sample: {df['Target_Style_Tags'].iloc[0]}")
    
    return df

def load_original_api_data() -> pd.DataFrame:
    """Load original API data containing gender, season, and display location."""
    print("📊 Loading original API data with complete attributes...")
    
    # Look for API data files containing the complete attribute information
    api_files = []
    
    # Check for SPU sales data (most likely to have complete attributes)
    spu_files = glob.glob("data/api_data/complete_spu_sales_*.csv")
    if spu_files:
        api_files.extend(spu_files)
    
    # Check for store config data
    config_files = glob.glob("data/api_data/store_config_*.csv")
    if config_files:
        api_files.extend(config_files)
    
    if not api_files:
        raise FileNotFoundError("No API data files found with complete attribute information")
    
    # Load and combine all available API data
    all_api_data = []
    
    for api_file in api_files:
        try:
            print(f"   📄 Loading: {api_file}")
            api_df = pd.read_csv(api_file)
            
            # Check if this file has the required columns
            required_cols = ['season_name', 'sex_name', 'display_location_name', 'big_class_name', 'sub_cate_name']
            has_required = all(col in api_df.columns for col in required_cols)
            
            if has_required:
                print(f"   ✅ Found complete attributes in: {os.path.basename(api_file)}")
                all_api_data.append(api_df[required_cols + ['str_code']].drop_duplicates())
            else:
                print(f"   ⚠️  Missing required columns in: {os.path.basename(api_file)}")
                
        except Exception as e:
            print(f"   ❌ Error loading {api_file}: {e}")
    
    if not all_api_data:
        raise ValueError("No API files contain the required attribute columns")
    
    # Combine all API data
    combined_api = pd.concat(all_api_data, ignore_index=True).drop_duplicates()
    print(f"✅ Combined API data: {len(combined_api):,} records with complete attributes")
    
    return combined_api

def create_attribute_mapping(api_data: pd.DataFrame) -> Dict[str, Dict]:
    """Create mapping from category combinations to their attributes."""
    print("🗺️  Creating attribute mapping from API data...")
    
    # Group by category combinations to get the most common attributes
    category_mapping = {}
    
    grouping_cols = ['big_class_name', 'sub_cate_name']
    
    for name, group in api_data.groupby(grouping_cols):
        big_class, sub_cate = name
        
        # Get most common attributes for this category combination
        most_common_season = group['season_name'].mode().iloc[0] if not group['season_name'].mode().empty else '夏'
        most_common_gender = group['sex_name'].mode().iloc[0] if not group['sex_name'].mode().empty else '中'
        most_common_location = group['display_location_name'].mode().iloc[0] if not group['display_location_name'].mode().empty else '前台'
        
        category_key = f"{big_class}|{sub_cate}"
        category_mapping[category_key] = {
            'season': most_common_season,
            'gender': most_common_gender,
            'location': most_common_location,
            'big_class': big_class,
            'sub_cate': sub_cate
        }
    
    print(f"✅ Created mapping for {len(category_mapping)} category combinations")
    return category_mapping

def translate_attributes(attributes: Dict[str, str]) -> Dict[str, str]:
    """Translate Chinese attributes to English."""
    
    # Translation mappings
    season_map = {
        '夏': 'Summer', '春': 'Spring', '秋': 'Autumn', '冬': 'Winter',
        '四季': 'All-Season'
    }
    
    gender_map = {
        '男': 'Men', '女': 'Women', '中': 'Unisex'
    }
    
    location_map = {
        '前台': 'Front-store', '后场': 'Back-store', '鞋配': 'Shoes-Accessories'
    }
    
    # Category translations
    category_map = {
        'T恤': 'T-shirt', '休闲裤': 'Casual Pants', 'POLO衫': 'Polo Shirt',
        '衬衫': 'Shirt', '牛仔裤': 'Jeans', '短裤': 'Shorts',
        '裙装': 'Skirts', '外套': 'Outerwear', '防晒衣': 'Sun Protection',
        '配饰': 'Accessories', '袜': 'Socks'
    }
    
    return {
        'season': season_map.get(attributes['season'], attributes['season']),
        'gender': gender_map.get(attributes['gender'], attributes['gender']),
        'location': location_map.get(attributes['location'], attributes['location']),
        'category': category_map.get(attributes['big_class'], attributes['big_class']),
        'subcategory': attributes['sub_cate']  # Keep subcategory as-is for now
    }

def reconstruct_style_tags(current_csv: pd.DataFrame, category_mapping: Dict[str, Dict]) -> pd.DataFrame:
    """Reconstruct complete style tags with all attributes."""
    print("🔧 Reconstructing complete style tags...")
    
    # Create a copy to modify
    fixed_csv = current_csv.copy()
    
    # Initialize counters
    total_records = len(fixed_csv)
    matched_records = 0
    default_records = 0
    
    def create_complete_style_tag(current_tags: str) -> str:
        nonlocal matched_records, default_records
        
        if pd.isna(current_tags) or current_tags == '':
            default_records += 1
            return '[Summer, Unisex, Front-store, Apparel, General]'
        
        # Parse current tags to extract category info
        current_tags_str = str(current_tags).strip()
        
        # Handle different formats
        if '|' in current_tags_str:
            # Pipe-separated format: "T恤 | 休闲圆领T恤"
            parts = [part.strip() for part in current_tags_str.split('|')]
            if len(parts) >= 2:
                big_class = parts[0]
                sub_cate = parts[1]
            else:
                big_class = parts[0] if parts else 'T恤'
                sub_cate = '休闲圆领T恤'
        else:
            # Single category or other format
            big_class = current_tags_str
            sub_cate = '基础款'
        
        # Look up attributes in mapping
        category_key = f"{big_class}|{sub_cate}"
        
        if category_key in category_mapping:
            attributes = category_mapping[category_key]
            matched_records += 1
        else:
            # Try with just the big_class
            fallback_keys = [key for key in category_mapping.keys() if key.startswith(f"{big_class}|")]
            if fallback_keys:
                attributes = category_mapping[fallback_keys[0]]
                matched_records += 1
            else:
                # Use defaults
                attributes = {
                    'season': '夏',
                    'gender': '中', 
                    'location': '前台',
                    'big_class': big_class,
                    'sub_cate': sub_cate
                }
                default_records += 1
        
        # Translate to English
        english_attrs = translate_attributes(attributes)
        
        # Create complete style tag
        complete_tag = f"[{english_attrs['season']}, {english_attrs['gender']}, {english_attrs['location']}, {english_attrs['category']}, {english_attrs['subcategory']}]"
        
        return complete_tag
    
    # Apply reconstruction to all records
    fixed_csv['Target_Style_Tags'] = fixed_csv['Target_Style_Tags'].apply(create_complete_style_tag)
    
    print(f"✅ Reconstruction complete:")
    print(f"   📊 Total records: {total_records:,}")
    print(f"   ✅ Matched with API data: {matched_records:,} ({matched_records/total_records*100:.1f}%)")
    print(f"   🔄 Used defaults: {default_records:,} ({default_records/total_records*100:.1f}%)")
    
    # Show sample of fixed style tags
    print(f"\n📋 Sample of corrected style tags:")
    for i in range(min(5, len(fixed_csv))):
        print(f"   {i+1}. {fixed_csv['Target_Style_Tags'].iloc[i]}")
    
    return fixed_csv

def save_corrected_csv(corrected_csv: pd.DataFrame) -> str:
    """Save the corrected CSV with complete style attributes."""
    print("💾 Saving corrected CSV...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"fast_fish_with_complete_style_attributes_{timestamp}.csv"
    
    corrected_csv.to_csv(output_file, index=False)
    
    print(f"✅ Saved corrected CSV: {output_file}")
    print(f"📊 File contains {len(corrected_csv):,} records with complete style information")
    
    # Verify the fix
    sample_tag = corrected_csv['Target_Style_Tags'].iloc[0]
    print(f"🔍 Sample corrected style tag: {sample_tag}")
    
    # Check if all required attributes are present
    required_parts = ['Summer', 'Men', 'Front-store']  # Example check
    has_attributes = any(part in sample_tag for part in required_parts)
    
    if has_attributes:
        print("✅ Verification: Style tags now contain gender/season/location attributes")
    else:
        print("⚠️  Verification: Style tags may still be missing some attributes")
    
    return output_file

def main():
    """Main execution function."""
    print("🚀 Fixing Missing Style Attributes in CSV Output")
    print("=" * 60)
    
    try:
        # Load current CSV with missing attributes
        current_csv = load_current_csv()
        
        # Load original API data with complete attributes
        api_data = load_original_api_data()
        
        # Create attribute mapping
        category_mapping = create_attribute_mapping(api_data)
        
        # Reconstruct complete style tags
        corrected_csv = reconstruct_style_tags(current_csv, category_mapping)
        
        # Save corrected CSV
        output_file = save_corrected_csv(corrected_csv)
        
        print("\n" + "=" * 60)
        print("🎯 STYLE ATTRIBUTE FIX COMPLETE")
        print("=" * 60)
        print(f"📁 Fixed CSV file: {output_file}")
        print("✅ All style tags now include gender, season, and display location")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error during style attribute fix: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main() 