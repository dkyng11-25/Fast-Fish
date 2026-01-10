#!/usr/bin/env python3
"""
Step 16: Create Comparison Tables
================================

Generate Excel-compatible comparison tables for:
- Historical 202408A vs Current 202508A
- Year-over-year growth metrics
- Performance benchmarks for Fast Fish analysis

Pipeline Flow:
Step 15 → Step 16 → Step 17 → Step 18
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import logging
from typing import Dict, List, Tuple
def get_actual_store_group(store_code: str) -> str:
    """Get actual store group from clustering results."""
    cluster_file = "output/clustering_results_spu.csv"
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



# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load both historical and current data."""
    
    # Load historical data
    historical_file = "../data/api_data/complete_spu_sales_202408A.csv"
    current_file = "../data/api_data/complete_spu_sales_202508A.csv"
    
    logger.info(f"Loading historical data: {historical_file}")
    historical_df = pd.read_csv(historical_file, dtype={'str_code': str, 'spu_code': str})
    
    logger.info(f"Loading current data: {current_file}")
    current_df = pd.read_csv(current_file, dtype={'str_code': str, 'spu_code': str})
    
    return historical_df, current_df

def create_store_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Create store groups using consistent logic."""
    df_with_groups = df.copy()
    df_with_groups['store_group'] = df_with_groups['str_code'].apply(
        lambda x: get_actual_store_group(str(x))
    )
    return df_with_groups

def create_summary_comparison(historical_df: pd.DataFrame, current_df: pd.DataFrame) -> pd.DataFrame:
    """Create high-level summary comparison."""
    
    logger.info("Creating summary comparison...")
    
    # Historical summary
    hist_summary = {
        'Period': '202408A (August 2024 H1)',
        'Total_Records': len(historical_df),
        'Unique_Stores': historical_df['str_code'].nunique(),
        'Unique_SPUs': historical_df['spu_code'].nunique(),
        'Unique_Categories': historical_df['cate_name'].nunique(),
        'Unique_SubCategories': historical_df['sub_cate_name'].nunique(),
        'Total_Sales_Amount': historical_df['spu_sales_amt'].sum(),
        'Total_Quantity': historical_df['quantity'].sum(),
        'Avg_Sales_Per_SPU': historical_df['spu_sales_amt'].sum() / historical_df['spu_code'].nunique(),
        'Avg_Quantity_Per_SPU': historical_df['quantity'].sum() / historical_df['spu_code'].nunique(),
        'Avg_Unit_Price': historical_df['spu_sales_amt'].sum() / historical_df['quantity'].sum()
    }
    
    # Current summary
    curr_summary = {
        'Period': '202506B (June 2025 H2)',
        'Total_Records': len(current_df),
        'Unique_Stores': current_df['str_code'].nunique(),
        'Unique_SPUs': current_df['spu_code'].nunique(),
        'Unique_Categories': current_df['cate_name'].nunique(),
        'Unique_SubCategories': current_df['sub_cate_name'].nunique(),
        'Total_Sales_Amount': current_df['spu_sales_amt'].sum(),
        'Total_Quantity': current_df['quantity'].sum(),
        'Avg_Sales_Per_SPU': current_df['spu_sales_amt'].sum() / current_df['spu_code'].nunique(),
        'Avg_Quantity_Per_SPU': current_df['quantity'].sum() / current_df['spu_code'].nunique(),
        'Avg_Unit_Price': current_df['spu_sales_amt'].sum() / current_df['quantity'].sum()
    }
    
    # Create comparison DataFrame
    comparison_df = pd.DataFrame([hist_summary, curr_summary])
    
    # Calculate changes
    changes = {}
    for col in ['Total_Records', 'Unique_Stores', 'Unique_SPUs', 'Unique_Categories', 
                'Unique_SubCategories', 'Total_Sales_Amount', 'Total_Quantity', 
                'Avg_Sales_Per_SPU', 'Avg_Quantity_Per_SPU', 'Avg_Unit_Price']:
        hist_val = comparison_df.iloc[0][col]
        curr_val = comparison_df.iloc[1][col]
        change = curr_val - hist_val
        change_pct = (change / hist_val * 100) if hist_val != 0 else 0
        changes[col] = change
        changes[f'{col}_Pct'] = change_pct
    
    # Add change row
    changes['Period'] = 'Change (Current - Historical)'
    comparison_df = pd.concat([comparison_df, pd.DataFrame([changes])], ignore_index=True)
    
    return comparison_df

def create_category_comparison(historical_df: pd.DataFrame, current_df: pd.DataFrame) -> pd.DataFrame:
    """Create category-level comparison."""
    
    logger.info("Creating category comparison...")
    
    # Historical category analysis
    hist_cat = historical_df.groupby('cate_name').agg({
        'spu_code': 'nunique',
        'spu_sales_amt': 'sum',
        'quantity': 'sum',
        'str_code': 'nunique'
    }).reset_index()
    hist_cat.columns = ['Category', 'Historical_SPU_Count', 'Historical_Sales', 'Historical_Quantity', 'Historical_Stores']
    hist_cat['Historical_Avg_Sales_Per_SPU'] = hist_cat['Historical_Sales'] / hist_cat['Historical_SPU_Count']
    
    # Current category analysis
    curr_cat = current_df.groupby('cate_name').agg({
        'spu_code': 'nunique',
        'spu_sales_amt': 'sum',
        'quantity': 'sum',
        'str_code': 'nunique'
    }).reset_index()
    curr_cat.columns = ['Category', 'Current_SPU_Count', 'Current_Sales', 'Current_Quantity', 'Current_Stores']
    curr_cat['Current_Avg_Sales_Per_SPU'] = curr_cat['Current_Sales'] / curr_cat['Current_SPU_Count']
    
    # Merge and calculate changes
    category_comparison = hist_cat.merge(curr_cat, on='Category', how='outer').fillna(0)
    
    category_comparison['SPU_Count_Change'] = category_comparison['Current_SPU_Count'] - category_comparison['Historical_SPU_Count']
    category_comparison['SPU_Count_Change_Pct'] = (category_comparison['SPU_Count_Change'] / category_comparison['Historical_SPU_Count'] * 100).round(1)
    
    category_comparison['Sales_Change'] = category_comparison['Current_Sales'] - category_comparison['Historical_Sales']
    category_comparison['Sales_Change_Pct'] = (category_comparison['Sales_Change'] / category_comparison['Historical_Sales'] * 100).round(1)
    
    category_comparison['Avg_Sales_Per_SPU_Change'] = category_comparison['Current_Avg_Sales_Per_SPU'] - category_comparison['Historical_Avg_Sales_Per_SPU']
    category_comparison['Avg_Sales_Per_SPU_Change_Pct'] = (category_comparison['Avg_Sales_Per_SPU_Change'] / category_comparison['Historical_Avg_Sales_Per_SPU'] * 100).round(1)
    
    # Sort by historical sales
    category_comparison = category_comparison.sort_values('Historical_Sales', ascending=False)
    
    return category_comparison

def create_store_group_comparison(historical_df: pd.DataFrame, current_df: pd.DataFrame) -> pd.DataFrame:
    """Create store group comparison."""
    
    logger.info("Creating store group comparison...")
    
    # Add store groups
    historical_grouped = create_store_groups(historical_df)
    current_grouped = create_store_groups(current_df)
    
    # Historical store group analysis
    hist_sg = historical_grouped.groupby('store_group').agg({
        'spu_code': 'nunique',
        'spu_sales_amt': 'sum',
        'quantity': 'sum',
        'str_code': 'nunique'
    }).reset_index()
    hist_sg.columns = ['Store_Group', 'Historical_SPU_Count', 'Historical_Sales', 'Historical_Quantity', 'Historical_Stores']
    hist_sg['Historical_Avg_Sales_Per_SPU'] = hist_sg['Historical_Sales'] / hist_sg['Historical_SPU_Count']
    
    # Current store group analysis
    curr_sg = current_grouped.groupby('store_group').agg({
        'spu_code': 'nunique',
        'spu_sales_amt': 'sum',
        'quantity': 'sum',
        'str_code': 'nunique'
    }).reset_index()
    curr_sg.columns = ['Store_Group', 'Current_SPU_Count', 'Current_Sales', 'Current_Quantity', 'Current_Stores']
    curr_sg['Current_Avg_Sales_Per_SPU'] = curr_sg['Current_Sales'] / curr_sg['Current_SPU_Count']
    
    # Merge and calculate changes
    sg_comparison = hist_sg.merge(curr_sg, on='Store_Group', how='outer').fillna(0)
    
    sg_comparison['SPU_Count_Change'] = sg_comparison['Current_SPU_Count'] - sg_comparison['Historical_SPU_Count']
    sg_comparison['SPU_Count_Change_Pct'] = (sg_comparison['SPU_Count_Change'] / sg_comparison['Historical_SPU_Count'] * 100).round(1)
    
    sg_comparison['Sales_Change'] = sg_comparison['Current_Sales'] - sg_comparison['Historical_Sales']
    sg_comparison['Sales_Change_Pct'] = (sg_comparison['Sales_Change'] / sg_comparison['Historical_Sales'] * 100).round(1)
    
    # Sort by store group
    sg_comparison = sg_comparison.sort_values('Store_Group')
    
    return sg_comparison

def create_top_performers_analysis(historical_df: pd.DataFrame, current_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Create top performers analysis."""
    
    logger.info("Creating top performers analysis...")
    
    results = {}
    
    # Top SPUs by sales (historical)
    hist_top_spus = historical_df.groupby('spu_code').agg({
        'spu_sales_amt': 'sum',
        'quantity': 'sum',
        'str_code': 'nunique'
    }).reset_index()
    hist_top_spus['avg_sales_per_store'] = hist_top_spus['spu_sales_amt'] / hist_top_spus['str_code']
    hist_top_spus = hist_top_spus.sort_values('spu_sales_amt', ascending=False).head(20)
    hist_top_spus['Period'] = '202408A_Historical'
    results['top_spus_historical'] = hist_top_spus
    
    # Top SPUs by sales (current)
    curr_top_spus = current_df.groupby('spu_code').agg({
        'spu_sales_amt': 'sum',
        'quantity': 'sum',
        'str_code': 'nunique'
    }).reset_index()
    curr_top_spus['avg_sales_per_store'] = curr_top_spus['spu_sales_amt'] / curr_top_spus['str_code']
    curr_top_spus = curr_top_spus.sort_values('spu_sales_amt', ascending=False).head(20)
    curr_top_spus['Period'] = '202506B_Current'
    results['top_spus_current'] = curr_top_spus
    
    # Top categories by growth
    hist_cat_totals = historical_df.groupby('cate_name')['spu_sales_amt'].sum()
    curr_cat_totals = current_df.groupby('cate_name')['spu_sales_amt'].sum()
    
    category_growth = pd.DataFrame({
        'Category': hist_cat_totals.index,
        'Historical_Sales': hist_cat_totals.values,
        'Current_Sales': curr_cat_totals.reindex(hist_cat_totals.index, fill_value=0).values
    })
    category_growth['Growth'] = category_growth['Current_Sales'] - category_growth['Historical_Sales']
    category_growth['Growth_Pct'] = (category_growth['Growth'] / category_growth['Historical_Sales'] * 100).round(1)
    category_growth = category_growth.sort_values('Growth_Pct', ascending=False)
    results['category_growth'] = category_growth
    
    return results

def save_excel_analysis(summary_df: pd.DataFrame, category_df: pd.DataFrame, 
                       store_group_df: pd.DataFrame, top_performers: Dict[str, pd.DataFrame]) -> str:
    """Save comprehensive Excel analysis."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_file = f"../output/spreadsheet_comparison_analysis_{timestamp}.xlsx"
    
    logger.info(f"Saving Excel analysis to: {excel_file}")
    
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Summary comparison
        summary_df.to_excel(writer, sheet_name='Summary_Comparison', index=False)
        
        # Category comparison
        category_df.to_excel(writer, sheet_name='Category_Comparison', index=False)
        
        # Store group comparison
        store_group_df.to_excel(writer, sheet_name='Store_Group_Comparison', index=False)
        
        # Top performers
        top_performers['top_spus_historical'].to_excel(writer, sheet_name='Top_SPUs_Historical', index=False)
        top_performers['top_spus_current'].to_excel(writer, sheet_name='Top_SPUs_Current', index=False)
        top_performers['category_growth'].to_excel(writer, sheet_name='Category_Growth', index=False)
    
    logger.info(f"Excel analysis saved: {excel_file}")
    return excel_file

def main():
    """Main execution function."""
    
    logger.info("Starting Step 16: Spreadsheet Comparison Analysis...")
    
    try:
        # Load data
        historical_df, current_df = load_data()
        
        # Create summary comparison
        summary_comparison = create_summary_comparison(historical_df, current_df)
        
        # Create category comparison
        category_comparison = create_category_comparison(historical_df, current_df)
        
        # Create store group comparison
        store_group_comparison = create_store_group_comparison(historical_df, current_df)
        
        # Create top performers analysis
        top_performers = create_top_performers_analysis(historical_df, current_df)
        
        # Save Excel analysis
        excel_file = save_excel_analysis(summary_comparison, category_comparison, 
                                       store_group_comparison, top_performers)
        
        # Print summary
        print(f"\n=== STEP 16: SPREADSHEET COMPARISON ANALYSIS ===")
        print(f"Historical period: 202408A (August 2024 H1)")
        print(f"Current period: 202506B (June 2025 H2)")
        print(f"")
        print(f"Summary metrics:")
        print(f"  Historical SPUs: {summary_comparison.iloc[0]['Unique_SPUs']:,}")
        print(f"  Current SPUs: {summary_comparison.iloc[1]['Unique_SPUs']:,}")
        print(f"  SPU Change: {summary_comparison.iloc[2]['Unique_SPUs']:+.0f}")
        print(f"")
        print(f"  Historical Sales: ¥{summary_comparison.iloc[0]['Total_Sales_Amount']:,.0f}")
        print(f"  Current Sales: ¥{summary_comparison.iloc[1]['Total_Sales_Amount']:,.0f}")
        print(f"  Sales Change: ¥{summary_comparison.iloc[2]['Total_Sales_Amount']:+,.0f}")
        print(f"")
        print(f"Excel file created: {excel_file}")
        
        logger.info("Step 16: Spreadsheet Comparison Analysis completed successfully!")
        
        return excel_file
        
    except Exception as e:
        logger.error(f"Error in Step 16: {e}")
        raise

if __name__ == "__main__":
    main()
