#!/usr/bin/env python3
"""
Step 18 (TEST): Add Sell-Through Rate Analysis
=======================================

Add client-requested sell-through rate calculations with 3 new columns:
1. SPU_Store_Days_Inventory (recommendation calculation)
2. SPU_Store_Days_Sales (historical sales)
3. Sell_Through_Rate (combining the two)

Formula:
Sell-Through Rate = SPU-store-day with sales / SPU-store-day with inventory

Example:
- 6 SPUs × 40 stores × 15 days = 3,600 SPU-store-days inventory
- 4 SPUs sold/day × 40 stores × 15 days = 2,400 SPU-store-days sales  
- Sell-Through Rate = 2,400 ÷ 3,600 = 66.7%

Pipeline Flow:
Step 17 → Step 18 (Sell-Through Rate Enhancement)
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
import glob
import os
from typing import Tuple, Dict

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_files() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load the augmented file from Step 17 and historical API data."""
    
    # EXPLICIT FILE PATH - No more risky glob patterns!
    from pipeline_manifest import get_step_input
    
    # Get exact file path from manifest
    augmented_file = get_step_input("step18", "augmented_recommendations")
    if not augmented_file:
        logger.error("❌ No augmented file registered in pipeline manifest!")
        logger.error("💡 Make sure Step 17 completed successfully and registered its output")
        raise FileNotFoundError("Augmented file not found in pipeline manifest")
    
    logger.info(f"✅ Loading augmented file from manifest: {augmented_file}")
    augmented_df = pd.read_csv(augmented_file)
    
    # Load historical source data for sales calculations
    historical_file = "data/api_data/complete_spu_sales_2025Q2_combined.csv"
    logger.info(f"Loading historical API data: {historical_file}")
    historical_df = pd.read_csv(historical_file, dtype={'str_code': str, 'spu_code': str})
    
    # Filter to May 2025 periods for historical baseline
    if 'source_period' in historical_df.columns:
        may_periods = historical_df['source_period'].str.contains('202505', na=False)
        historical_df = historical_df[may_periods]
        logger.info(f"Filtered to May 2025 baseline: {len(historical_df):,} records")
    
    return augmented_df, historical_df

def create_store_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Create store groups using consistent logic."""
    df_with_groups = df.copy()
    df_with_groups['store_group'] = df_with_groups['str_code'].apply(
        lambda x: f"Store Group {((int(str(x)[-3:]) if str(x)[-3:].isdigit() else hash(str(x))) % 20) + 1}"
    )
    return df_with_groups

def calculate_historical_sales_data(historical_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate historical sales data per store group and category combination.
    
    Args:
        historical_df: Raw API data with sales information
        
    Returns:
        DataFrame with aggregated sales data per store group/category
    """
    logger.info("Calculating historical sales data for sell-through analysis...")
    
    # Add store groups to historical data
    historical_with_groups = create_store_groups(historical_df)
    
    # Calculate sales per SPU per store per day (assuming API data is for 15-day period)
    PERIOD_DAYS = 15  # Half-month period
    
    # Group by store_group, category, and sub_category
    sales_summary = historical_with_groups.groupby(['store_group', 'cate_name', 'sub_cate_name']).agg({
        'str_code': 'nunique',  # Number of stores in group selling this category
        'spu_code': 'nunique',  # Number of unique SPUs sold
        'spu_sales_amt': 'sum',  # Total sales amount
        'quantity': 'sum'       # Total quantity sold
    }).reset_index()
    
    # Calculate daily sales metrics
    sales_summary['stores_in_group'] = sales_summary['str_code']
    sales_summary['total_sales_amount'] = sales_summary['spu_sales_amt']
    sales_summary['total_quantity_sold'] = sales_summary['quantity']
    
    # Calculate average daily SPU sales per store
    sales_summary['avg_daily_spus_sold_per_store'] = (
        sales_summary['total_quantity_sold'] / 
        (sales_summary['stores_in_group'] * PERIOD_DAYS)
    )
    
    # Calculate SPU-store-days with sales for the period
    sales_summary['spu_store_days_sales'] = (
        sales_summary['avg_daily_spus_sold_per_store'] * 
        sales_summary['stores_in_group'] * 
        PERIOD_DAYS
    )
    
    logger.info(f"Processed {len(sales_summary)} store group/category combinations")
    
    return sales_summary[['store_group', 'cate_name', 'sub_cate_name', 'stores_in_group', 
                         'avg_daily_spus_sold_per_store', 'spu_store_days_sales', 
                         'total_sales_amount', 'total_quantity_sold']]

def add_sell_through_calculations(augmented_df: pd.DataFrame, sales_data: pd.DataFrame) -> pd.DataFrame:
    """
    Add the 3 new sell-through rate columns to the augmented DataFrame.
    
    Args:
        augmented_df: Enhanced recommendations from Step 17
        sales_data: Historical sales data for calculations
        
    Returns:
        DataFrame with new sell-through rate columns added
    """
    logger.info("Adding sell-through rate calculations...")
    
    # Create a copy for modifications
    enhanced_df = augmented_df.copy()
    
    # Constants
    PERIOD_DAYS = 15  # Half-month period as specified by client
    
    # Initialize new columns
    enhanced_df['SPU_Store_Days_Inventory'] = 0.0
    enhanced_df['SPU_Store_Days_Sales'] = 0.0
    enhanced_df['Sell_Through_Rate'] = 0.0
    enhanced_df['Historical_Avg_Daily_SPUs_Sold_Per_Store'] = 0.0
    
    # Process each row
    for idx, row in enhanced_df.iterrows():
        store_group = row['Store_Group_Name']
        style_tags = row['Target_Style_Tags']
        target_spu_quantity = row['Target_SPU_Quantity']
        stores_in_group = row['Stores_In_Group_Selling_This_Category']
        
        # Parse category from Target_Style_Tags: [[夏, 女, 前台, POLO衫, 套头POLO]]
        try:
            # Remove outer brackets and split by commas
            tags_clean = style_tags.strip('[]')
            # Handle the nested bracket format
            if tags_clean.startswith('[') and tags_clean.endswith(']'):
                tags_clean = tags_clean[1:-1]
            tags_list = [tag.strip().strip('"\'') for tag in tags_clean.split(',')]
            
            # Extract category and subcategory from the correct positions
            # Format: [season, gender, location, cate_name, sub_cate_name]
            if len(tags_list) >= 5:
                category = tags_list[3].strip()  # 4th element is cate_name
                sub_category = tags_list[4].strip().rstrip(']')  # 5th element is sub_cate_name
            else:
                # Fallback for different formats
                if '|' in style_tags:
                    parts = style_tags.split('|')
                    category = parts[0].strip()
                    sub_category = parts[1].strip() if len(parts) > 1 else category
                else:
                    category = 'Unknown'
                    sub_category = 'Unknown'
                    logger.warning(f"Unexpected Target_Style_Tags format: {style_tags}")
                    
        except Exception as e:
            logger.warning(f"Could not parse style tags '{style_tags}': {e}")
            # Set default values and continue processing
            category = 'Unknown'
            sub_category = 'Unknown'
        
        # CALCULATION 1: SPU-Store-Days Inventory (Recommendation)
        # Formula: Target SPU Quantity × Stores in Group × Period Days
        spu_store_days_inventory = target_spu_quantity * stores_in_group * PERIOD_DAYS
        enhanced_df.at[idx, 'SPU_Store_Days_Inventory'] = spu_store_days_inventory
        
        # CALCULATION 2: SPU-Store-Days Sales (Historical)
        # Look up historical sales data for this store group + category combination
        sales_match = sales_data[
            (sales_data['store_group'] == store_group) &
            (sales_data['cate_name'] == category) &
            (sales_data['sub_cate_name'] == sub_category)
        ]
        
        if len(sales_match) > 0:
            historical_sales_data = sales_match.iloc[0]
            spu_store_days_sales = historical_sales_data['spu_store_days_sales']
            avg_daily_spus_sold = historical_sales_data['avg_daily_spus_sold_per_store']
            
            enhanced_df.at[idx, 'SPU_Store_Days_Sales'] = spu_store_days_sales
            enhanced_df.at[idx, 'Historical_Avg_Daily_SPUs_Sold_Per_Store'] = avg_daily_spus_sold
        else:
            # No historical data - use conservative estimate based on current performance
            logger.debug(f"No historical sales data for {store_group} - {category} | {sub_category}")
            
            # Estimate based on current average sales per SPU if available
            if pd.notna(row.get('Avg_Sales_Per_SPU', 0)) and row.get('Avg_Sales_Per_SPU', 0) > 0:
                # Estimate SPUs sold per day based on current performance
                avg_sales_per_spu = row['Avg_Sales_Per_SPU']
                # Conservative estimate: assume 1 unit sold per ¥100 sales per day
                estimated_daily_spus_per_store = max(1.0, avg_sales_per_spu / 100.0 / PERIOD_DAYS)
                spu_store_days_sales = estimated_daily_spus_per_store * stores_in_group * PERIOD_DAYS
                
                enhanced_df.at[idx, 'SPU_Store_Days_Sales'] = spu_store_days_sales
                enhanced_df.at[idx, 'Historical_Avg_Daily_SPUs_Sold_Per_Store'] = estimated_daily_spus_per_store
            else:
                enhanced_df.at[idx, 'SPU_Store_Days_Sales'] = 0.0
                enhanced_df.at[idx, 'Historical_Avg_Daily_SPUs_Sold_Per_Store'] = 0.0
        
        # CALCULATION 3: Sell-Through Rate
        # Formula: SPU-store-day with sales / SPU-store-day with inventory
        if spu_store_days_inventory > 0:
            spu_store_days_sales_final = enhanced_df.at[idx, 'SPU_Store_Days_Sales']
            sell_through_rate = (spu_store_days_sales_final / spu_store_days_inventory) * 100  # Convert to percentage
            enhanced_df.at[idx, 'Sell_Through_Rate'] = min(sell_through_rate, 100.0)  # Cap at 100%
        else:
            enhanced_df.at[idx, 'Sell_Through_Rate'] = 0.0
    
    # Log summary statistics
    valid_rates = enhanced_df[enhanced_df['Sell_Through_Rate'] > 0]['Sell_Through_Rate']
    if len(valid_rates) > 0:
        logger.info(f"Sell-through rate summary:")
        logger.info(f"  Records with rates: {len(valid_rates):,}")
        logger.info(f"  Average rate: {valid_rates.mean():.1f}%")
        logger.info(f"  Median rate: {valid_rates.median():.1f}%")
        logger.info(f"  Range: {valid_rates.min():.1f}% - {valid_rates.max():.1f}%")
    
    return enhanced_df

def save_enhanced_file(enhanced_df: pd.DataFrame) -> str:
    """Save the enhanced file with sell-through rate analysis."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"output/fast_fish_with_sell_through_analysis_{timestamp}.csv"
    
    logger.info(f"Saving enhanced file with sell-through analysis to: {output_file}")
    logger.info(f"Output contains {len(enhanced_df.columns)} columns including sell-through metrics")
    
    enhanced_df.to_csv(output_file, index=False)
    
    return output_file

def print_analysis_summary(enhanced_df: pd.DataFrame):
    """Print comprehensive analysis summary."""
    
    print("\n" + "="*80)
    print("SELL-THROUGH RATE ANALYSIS SUMMARY")
    print("="*80)
    
    total_records = len(enhanced_df)
    records_with_rates = len(enhanced_df[enhanced_df['Sell_Through_Rate'] > 0])
    
    print(f"📊 Total Records: {total_records:,}")
    print(f"📈 Records with Sell-Through Rates: {records_with_rates:,} ({records_with_rates/total_records*100:.1f}%)")
    
    if records_with_rates > 0:
        valid_rates = enhanced_df[enhanced_df['Sell_Through_Rate'] > 0]
        
        print(f"\n🎯 SELL-THROUGH RATE STATISTICS:")
        print(f"   Average: {valid_rates['Sell_Through_Rate'].mean():.1f}%")
        print(f"   Median:  {valid_rates['Sell_Through_Rate'].median():.1f}%")
        print(f"   Min:     {valid_rates['Sell_Through_Rate'].min():.1f}%")
        print(f"   Max:     {valid_rates['Sell_Through_Rate'].max():.1f}%")
        
        # Rate distribution
        print(f"\n📊 SELL-THROUGH RATE DISTRIBUTION:")
        rate_bins = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]
        for min_rate, max_rate in rate_bins:
            count = len(valid_rates[
                (valid_rates['Sell_Through_Rate'] >= min_rate) & 
                (valid_rates['Sell_Through_Rate'] < max_rate)
            ])
            pct = count / records_with_rates * 100 if records_with_rates > 0 else 0
            print(f"   {min_rate:2d}-{max_rate:2d}%: {count:4d} records ({pct:4.1f}%)")
        
        # Top and bottom performers
        print(f"\n🏆 TOP 5 HIGHEST SELL-THROUGH RATES:")
        top_5 = valid_rates.nlargest(5, 'Sell_Through_Rate')[
            ['Store_Group_Name', 'Target_Style_Tags', 'Target_SPU_Quantity', 'Sell_Through_Rate']
        ]
        for _, row in top_5.iterrows():
            tags_short = row['Target_Style_Tags'][:50] + "..." if len(str(row['Target_Style_Tags'])) > 50 else row['Target_Style_Tags']
            print(f"   {row['Sell_Through_Rate']:5.1f}% - {row['Store_Group_Name']} - {tags_short}")
        
        print(f"\n⚠️  BOTTOM 5 LOWEST SELL-THROUGH RATES:")
        bottom_5 = valid_rates.nsmallest(5, 'Sell_Through_Rate')[
            ['Store_Group_Name', 'Target_Style_Tags', 'Target_SPU_Quantity', 'Sell_Through_Rate']
        ]
        for _, row in bottom_5.iterrows():
            tags_short = row['Target_Style_Tags'][:50] + "..." if len(str(row['Target_Style_Tags'])) > 50 else row['Target_Style_Tags']
            print(f"   {row['Sell_Through_Rate']:5.1f}% - {row['Store_Group_Name']} - {tags_short}")
    
    print(f"\n💡 NEW COLUMNS ADDED:")
    print(f"   • SPU_Store_Days_Inventory: Target SPU Quantity × Stores × 15 days")
    print(f"   • SPU_Store_Days_Sales: Historical daily SPU sales × Stores × 15 days")  
    print(f"   • Sell_Through_Rate: (Sales ÷ Inventory) × 100%")
    print(f"   • Historical_Avg_Daily_SPUs_Sold_Per_Store: Average SPUs sold per store per day")
    
    print("\n" + "="*80)

def main():
    """Main execution function."""
    
    try:
        print("🚀 Starting Step 18: Sell-Through Rate Analysis")
        print("=" * 60)
        
        # Load files
        print("📂 Loading files...")
        augmented_df, historical_df = load_files()
        print(f"✅ Loaded augmented file: {len(augmented_df):,} records")
        print(f"✅ Loaded historical data: {len(historical_df):,} records")
        
        # Calculate historical sales data
        print("\n📊 Processing historical sales data...")
        sales_data = calculate_historical_sales_data(historical_df)
        print(f"✅ Processed sales data for {len(sales_data):,} store group/category combinations")
        
        # Add sell-through calculations
        print("\n🧮 Adding sell-through rate calculations...")
        enhanced_df = add_sell_through_calculations(augmented_df, sales_data)
        print(f"✅ Enhanced {len(enhanced_df):,} records with sell-through metrics")
        
        # Save enhanced file
        print("\n💾 Saving enhanced file...")
        output_file = save_enhanced_file(enhanced_df)
        print(f"✅ Saved to: {output_file}")
        
        # Print analysis summary
        print_analysis_summary(enhanced_df)
        
        print(f"\n🎉 Step 18 completed successfully!")
        print(f"📁 Output: {output_file}")
        print(f"📊 Total records: {len(enhanced_df):,}")
        print(f"📈 Columns: {len(enhanced_df.columns)} (including new sell-through metrics)")
        
        return output_file
        
    except Exception as e:
        logger.error(f"Step 18 failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
