#!/usr/bin/env python3
"""
Step 18: Sell-Through Rate Analysis with Progress Bars
======================================================

Add sell-through rate calculations to the augmented Fast Fish recommendations.
Now includes progress bars for better user experience.

Pipeline Flow:
Step 17 → Step 18 (Sell-Through Analysis) → Final Output

Calculations:
1. SPU-Store-Days Inventory = Target SPU Quantity × Stores in Group × Period Days
2. SPU-Store-Days Sales = Historical daily sales × Stores in Group × Period Days  
3. Sell-Through Rate = (SPU-Store-Days Sales / SPU-Store-Days Inventory) × 100%
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import logging
import glob
from typing import Tuple
from tqdm import tqdm

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_actual_store_group(store_code: str) -> str:
    """Get actual store group from clustering results."""
    cluster_file = "../output/clustering_results_spu.csv"
    if not os.path.exists(cluster_file):
        # Fallback to modulo 46 if clustering file not found
        return f"Store Group {((int(store_code[-3:]) if store_code[-3:].isdigit() else hash(store_code)) % 46) + 1}"
    
    try:
        cluster_df = pd.read_csv(cluster_file)
        store_match = cluster_df[cluster_df['str_code'] == int(store_code)]
        if not store_match.empty:
            cluster_id = store_match.iloc[0]['Cluster']
            return f"Store Group {cluster_id + 1}"
        else:
            return f"Store Group 1"  # Default fallback
    except:
        return f"Store Group 1"  # Error fallback

def load_files() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load the augmented file from Step 17 and historical API data."""
    
    # Find the most recent augmented Fast Fish file from Step 17
    augmented_files = glob.glob("../output/fast_fish_with_enhanced_trending_*.csv")
    if not augmented_files:
        # Fallback to fixed trending files
        augmented_files = glob.glob("../output/fast_fish_with_fixed_trending_*.csv")
        if not augmented_files:
            # Fallback to other formats
            augmented_files = glob.glob("../output/fast_fish_with_historical_and_trending_hybrid_*.csv")
            if not augmented_files:
                augmented_files = glob.glob("../output/fast_fish_with_historical_reference_*.csv")
                if not augmented_files:
                    raise FileNotFoundError("No augmented Fast Fish files found in ../output/")
    
    augmented_file = max(augmented_files, key=os.path.getmtime)
    logger.info(f"Loading augmented file: {augmented_file}")
    augmented_df = pd.read_csv(augmented_file)
    
    # Load historical source data for sales calculations
    historical_file = "../data/api_data/complete_spu_sales_202408A.csv"
    logger.info(f"Loading historical API data: {historical_file}")
    historical_df = pd.read_csv(historical_file, dtype={'str_code': str, 'spu_code': str})
    
    return augmented_df, historical_df

def create_store_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Create store groups using same logic as Fast Fish analysis."""
    df_with_groups = df.copy()
    df_with_groups['store_group'] = df_with_groups['str_code'].apply(
        lambda x: f"Store Group {((int(str(x)[-3:]) if str(x)[-3:].isdigit() else hash(str(x))) % 46) + 1}"
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
    print("🏢 Adding store groups to historical data...")
    historical_with_groups = create_store_groups(historical_df)
    
    # Calculate sales per SPU per store per day (assuming API data is for 15-day period)
    PERIOD_DAYS = 15  # Half-month period
    
    # Group by store_group, category, and sub_category with progress bar
    print("📊 Aggregating sales data by store group and category...")
    tqdm.pandas(desc="Processing historical sales")
    
    sales_summary = historical_with_groups.groupby(['store_group', 'cate_name', 'sub_cate_name']).agg({
        'str_code': 'nunique',  # Number of stores in group selling this category
        'spu_code': 'nunique',  # Number of unique SPUs sold
        'spu_sales_amt': 'sum',  # Total sales amount
        'quantity': 'sum'       # Total quantity sold
    }).reset_index()
    
    print(f"✅ Processed {len(sales_summary):,} store group × category combinations")
    
    # Calculate daily sales metrics
    print("🧮 Calculating daily sales metrics...")
    sales_summary['stores_in_group'] = sales_summary['str_code']
    sales_summary['total_sales_amount'] = sales_summary['spu_sales_amt']
    sales_summary['total_quantity_sold'] = sales_summary['quantity']
    
    # Calculate average daily SPU sales per store
    sales_summary['avg_daily_spus_sold_per_store'] = (
        sales_summary['total_quantity_sold'] / 
        (sales_summary['stores_in_group'] * PERIOD_DAYS)
    )
    
    # Calculate SPU-store-days sales (total SPUs sold across all stores in group over period)
    sales_summary['spu_store_days_sales'] = sales_summary['total_quantity_sold']
    
    # Create lookup keys for matching
    sales_summary['lookup_key'] = sales_summary['cate_name'] + ' | ' + sales_summary['sub_cate_name']
    
    logger.info(f"Calculated historical sales data for {len(sales_summary)} store group × category combinations")
    
    return sales_summary

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
    
    # Process each row with progress bar
    print(f"🔄 Processing {len(enhanced_df):,} recommendations for sell-through analysis...")
    
    for idx, row in tqdm(enhanced_df.iterrows(), total=len(enhanced_df), desc="📊 Adding sell-through calculations"):
        store_group = row['Store_Group_Name']
        style_tags = row['Target_Style_Tags']
        target_spu_quantity = row['Target_SPU_Quantity']
        stores_in_group = row['Stores_In_Group_Selling_This_Category']
        
        try:
            # Remove brackets and split by commas
            tags_clean = style_tags.strip('[]')
            tags_list = [tag.strip() for tag in tags_clean.split(',')]
            
            if len(tags_list) >= 2:
                category = tags_list[0].strip()
                sub_category = tags_list[1].strip()
            else:
                # Fallback for different formats
                if '|' in style_tags:
                    parts = style_tags.split('|')
                    category = parts[0].strip()
                    sub_category = parts[1].strip() if len(parts) > 1 else category
        else:
                    category = style_tags.strip('[]')
                    sub_category = category
                    
        except Exception as e:
            logger.warning(f"Could not parse style tags '{style_tags}': {e}")
            continue
        
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
        
        # CALCULATION 3: Sell-Through Rate
        # Formula: SPU-store-day with sales / SPU-store-day with inventory
        if spu_store_days_inventory > 0:
            spu_store_days_sales_final = enhanced_df.at[idx, 'SPU_Store_Days_Sales']
            sell_through_rate = (spu_store_days_sales_final / spu_store_days_inventory) * 100  # Convert to percentage
            enhanced_df.at[idx, 'Sell_Through_Rate'] = min(sell_through_rate, 100.0)  # Cap at 100%
        else:
            enhanced_df.at[idx, 'Sell_Through_Rate'] = 0.0
    
    logger.info(f"✅ Added sell-through calculations to {len(enhanced_df)} recommendations")
    
    return enhanced_df

def save_enhanced_file(enhanced_df: pd.DataFrame) -> str:
    """Save the enhanced file with sell-through rate calculations."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"../output/fast_fish_with_sell_through_analysis_{timestamp}.csv"
    
    logger.info(f"Saving enhanced file with sell-through analysis to: {output_file}")
    enhanced_df.to_csv(output_file, index=False)
    
    return output_file

def print_analysis_summary(enhanced_df: pd.DataFrame):
    """Print comprehensive analysis summary."""
    
    print(f"\n" + "="*80)
    print(f"🎯 STEP 18: SELL-THROUGH RATE ANALYSIS COMPLETE")
    print(f"="*80)
    
    print(f"\n📊 BASIC METRICS:")
    print(f"  • Total recommendations: {len(enhanced_df):,}")
    print(f"  • Output columns: {len(enhanced_df.columns)}")
    
    # Sell-through rate statistics
    valid_sell_through = enhanced_df[enhanced_df['Sell_Through_Rate'] > 0]
    if len(valid_sell_through) > 0:
        avg_sell_through = valid_sell_through['Sell_Through_Rate'].mean()
        median_sell_through = valid_sell_through['Sell_Through_Rate'].median()
        max_sell_through = valid_sell_through['Sell_Through_Rate'].max()
        
        print(f"\n📈 SELL-THROUGH RATE ANALYSIS:")
        print(f"  • Recommendations with sell-through data: {len(valid_sell_through):,}")
        print(f"  • Average sell-through rate: {avg_sell_through:.1f}%")
        print(f"  • Median sell-through rate: {median_sell_through:.1f}%")
        print(f"  • Maximum sell-through rate: {max_sell_through:.1f}%")
        
        # Distribution analysis
        high_sell_through = len(valid_sell_through[valid_sell_through['Sell_Through_Rate'] >= 80])
        medium_sell_through = len(valid_sell_through[(valid_sell_through['Sell_Through_Rate'] >= 40) & (valid_sell_through['Sell_Through_Rate'] < 80)])
        low_sell_through = len(valid_sell_through[valid_sell_through['Sell_Through_Rate'] < 40])
        
        print(f"\n📊 SELL-THROUGH DISTRIBUTION:")
        print(f"  • High sell-through (≥80%): {high_sell_through:,} recommendations")
        print(f"  • Medium sell-through (40-79%): {medium_sell_through:,} recommendations")
        print(f"  • Low sell-through (<40%): {low_sell_through:,} recommendations")
    
    # Inventory analysis
    total_inventory = enhanced_df['SPU_Store_Days_Inventory'].sum()
    total_sales = enhanced_df['SPU_Store_Days_Sales'].sum()
    
    print(f"\n📦 INVENTORY ANALYSIS:")
    print(f"  • Total SPU-store-days inventory: {total_inventory:,.0f}")
    print(f"  • Total SPU-store-days sales: {total_sales:,.0f}")
    if total_inventory > 0:
        overall_sell_through = (total_sales / total_inventory) * 100
        print(f"  • Overall sell-through rate: {overall_sell_through:.1f}%")
    
    print(f"\n✅ ANALYSIS COMPLETE!")

def main():
    """Main execution function for Step 18."""
    
    start_time = datetime.now()
    
    print("🚀 Starting Step 18: Sell-Through Rate Analysis")
    print("=" * 60)
    
    try:
        # Load files
        print("📂 Loading files...")
        augmented_df, historical_df = load_files()
        
        print(f"✅ Loaded augmented file: {len(augmented_df):,} records")
        print(f"✅ Loaded historical data: {len(historical_df):,} records")
        
        # Process historical data
        print("\n📊 Processing historical sales data...")
        sales_data = calculate_historical_sales_data(historical_df)
        
        # Add sell-through calculations
        print("\n🧮 Adding sell-through rate calculations...")
        enhanced_df = add_sell_through_calculations(augmented_df, sales_data)
        
        # Save results
        print("\n💾 Saving enhanced file...")
        output_file = save_enhanced_file(enhanced_df)
        
        # Print summary
        print_analysis_summary(enhanced_df)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n⏱️ Total processing time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
        print(f"📁 Output file: {output_file}")
        
        logger.info("✅ Step 18: Sell-Through Rate Analysis completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error in Step 18: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()
