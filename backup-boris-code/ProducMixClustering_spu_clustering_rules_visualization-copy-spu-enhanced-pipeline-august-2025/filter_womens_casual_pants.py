#!/usr/bin/env python3
"""
Comprehensive Women's Casual Pants Filter Script
================================================

This script filters the Fast Fish style attributes CSV file to extract only 
women's casual pants records with the specified output format.

Author: AI Assistant
Date: 2025-07-15
"""

import pandas as pd
import sys
import os
from datetime import datetime

def validate_file_exists(file_path):
    """Validate that the input file exists."""
    if not os.path.exists(file_path):
        print(f"ERROR: File '{file_path}' not found!")
        sys.exit(1)
    return True

def determine_suggested_action(current_spu, target_spu):
    """
    Determine the suggested action based on current vs target SPU quantities.
    
    Args:
        current_spu (int): Current SPU quantity
        target_spu (int): Target SPU quantity
    
    Returns:
        str: Suggested action
    """
    if target_spu > current_spu:
        return "Increase"
    elif target_spu < current_spu:
        return "Decrease"
    else:
        return "Maintain"

def convert_period_to_readable(period):
    """Convert period code to readable format."""
    period_map = {
        'A': 'First Half',
        'B': 'Second Half'
    }
    return period_map.get(period, period)

def extract_style_subcategory(style_tags):
    """
    Extract the subcategory from style tags.
    
    Args:
        style_tags (str): Style tags in format "[Season, Gender, Location, Category, Subcategory]"
    
    Returns:
        str: Subcategory name
    """
    try:
        # Remove brackets and split by comma
        tags = style_tags.strip('[]').split(', ')
        if len(tags) >= 5:
            return tags[4]  # Subcategory is the 5th element
        else:
            return "Unknown"
    except:
        return "Unknown"

def filter_womens_casual_pants(input_file, output_file=None):
    """
    Filter the CSV file for women's casual pants and generate formatted output.
    
    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output CSV file (optional)
    
    Returns:
        pd.DataFrame: Filtered dataframe
    """
    
    print("🔍 Starting Women's Casual Pants Filter Analysis")
    print("=" * 60)
    
    # Validate input file
    validate_file_exists(input_file)
    
    # Read the CSV file
    print(f"📊 Reading data from: {input_file}")
    try:
        df = pd.read_csv(input_file)
        print(f"✅ Successfully loaded {len(df):,} total records")
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        sys.exit(1)
    
    # Display column information
    print(f"\n📋 Dataset contains {len(df.columns)} columns:")
    for i, col in enumerate(df.columns[:10], 1):
        print(f"   {i:2d}. {col}")
    if len(df.columns) > 10:
        print(f"   ... and {len(df.columns) - 10} more columns")
    
    # Filter for women's casual pants
    print(f"\n🔍 Filtering for women's casual pants...")
    
    # Create filter condition
    womens_casual_pants_mask = (
        df['Target_Style_Tags'].str.contains('Women', case=False, na=False) &
        df['Target_Style_Tags'].str.contains('Casual Pants', case=False, na=False)
    )
    
    filtered_df = df[womens_casual_pants_mask].copy()
    
    print(f"✅ Found {len(filtered_df):,} women's casual pants records")
    
    if len(filtered_df) == 0:
        print("⚠️  No women's casual pants records found!")
        return pd.DataFrame()
    
    # Add suggested action column
    print("📝 Calculating suggested actions...")
    filtered_df['Suggested_Action'] = filtered_df.apply(
        lambda row: determine_suggested_action(row['Current_SPU_Quantity'], row['Target_SPU_Quantity']),
        axis=1
    )
    
    # Convert period to readable format
    filtered_df['Period_Readable'] = filtered_df['Period'].apply(convert_period_to_readable)
    
    # Extract subcategory for better understanding
    filtered_df['Subcategory'] = filtered_df['Target_Style_Tags'].apply(extract_style_subcategory)
    
    # Create the final output dataframe with requested columns
    output_df = pd.DataFrame({
        'Year': filtered_df['Year'],
        'Month': filtered_df['Month'],
        'Period': filtered_df['Period_Readable'],
        'Store_Group': filtered_df['Store_Group_Name'],
        'Style_Tags': filtered_df['Target_Style_Tags'],
        'Target_SPU_Quantity': filtered_df['Target_SPU_Quantity'],
        'Current_SPU_Quantity': filtered_df['Current_SPU_Quantity'],
        'Suggested_Action': filtered_df['Suggested_Action']
    })
    
    # Display summary statistics
    print("\n📊 ANALYSIS SUMMARY")
    print("=" * 40)
    print(f"Total women's casual pants records: {len(output_df):,}")
    print(f"Unique store groups: {output_df['Store_Group'].nunique()}")
    print(f"Date range: {output_df['Year'].min()}-{output_df['Month'].min():02d} to {output_df['Year'].max()}-{output_df['Month'].max():02d}")
    
    # Action distribution
    action_counts = output_df['Suggested_Action'].value_counts()
    print(f"\n📈 SUGGESTED ACTIONS:")
    for action, count in action_counts.items():
        percentage = (count / len(output_df)) * 100
        print(f"   {action}: {count:,} records ({percentage:.1f}%)")
    
    # Subcategory distribution
    subcategory_counts = filtered_df['Subcategory'].value_counts()
    print(f"\n👕 SUBCATEGORY BREAKDOWN:")
    for subcat, count in subcategory_counts.head(10).items():
        percentage = (count / len(filtered_df)) * 100
        print(f"   {subcat}: {count:,} records ({percentage:.1f}%)")
    
    # Store group distribution (top 10)
    store_group_counts = output_df['Store_Group'].value_counts()
    print(f"\n🏪 TOP 10 STORE GROUPS:")
    for store_group, count in store_group_counts.head(10).items():
        percentage = (count / len(output_df)) * 100
        print(f"   {store_group}: {count:,} records ({percentage:.1f}%)")
    
    # Quantity analysis
    print(f"\n📊 QUANTITY ANALYSIS:")
    print(f"   Current SPU Range: {output_df['Current_SPU_Quantity'].min()} - {output_df['Current_SPU_Quantity'].max()}")
    print(f"   Target SPU Range: {output_df['Target_SPU_Quantity'].min()} - {output_df['Target_SPU_Quantity'].max()}")
    print(f"   Average Current SPU: {output_df['Current_SPU_Quantity'].mean():.1f}")
    print(f"   Average Target SPU: {output_df['Target_SPU_Quantity'].mean():.1f}")
    
    # Save output file
    if output_file:
        print(f"\n💾 Saving filtered data to: {output_file}")
        try:
            output_df.to_csv(output_file, index=False)
            print(f"✅ Successfully saved {len(output_df):,} records")
        except Exception as e:
            print(f"❌ Error saving file: {e}")
    
    return output_df

def main():
    """Main function to run the filtering process."""
    input_file = "fast_fish_with_complete_style_attributes_20250715_105659.csv"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"womens_casual_pants_filtered_{timestamp}.csv"
    
    print("🚀 Women's Casual Pants Filter Script")
    print("=" * 60)
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Processing time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run the filtering process
    result_df = filter_womens_casual_pants(input_file, output_file)
    
    if len(result_df) > 0:
        print(f"\n✅ PROCESSING COMPLETE!")
        print(f"📄 Output saved to: {output_file}")
        print(f"📊 Records processed: {len(result_df):,}")
        
        # Display first few records as preview
        print(f"\n📋 PREVIEW (First 5 records):")
        print(result_df.head().to_string(index=False))
    else:
        print(f"\n⚠️  No records found matching criteria")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main() 