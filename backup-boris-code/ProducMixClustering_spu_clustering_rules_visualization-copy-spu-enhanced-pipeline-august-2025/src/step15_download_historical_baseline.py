#!/usr/bin/env python3
"""
Step 15: Download Historical Baseline (202408A)
==============================================

Analyze August 2024 first half data to create historical baselines
for comparison with current 202508A analysis.

This provides:
- Historical SPU counts by Store Group × Sub-Category
- Historical sales performance metrics
- Year-over-year comparison baselines
- Historical reference for Fast Fish recommendations

Pipeline Flow:
Step 14 → Step 15 → Step 16 → Step 17 → Step 18
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
from typing import Dict, List, Tuple
import logging
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

def load_historical_data() -> pd.DataFrame:
    """Load the 202408A historical SPU data."""
    try:
        # Load the historical SPU sales data
        historical_file = "../data/api_data/complete_spu_sales_202408A.csv"
        
        if not os.path.exists(historical_file):
            raise FileNotFoundError(f"Historical data file not found: {historical_file}")
        
        logger.info(f"Loading historical data from: {historical_file}")
        df = pd.read_csv(historical_file, dtype={'str_code': str, 'spu_code': str})
        
        logger.info(f"Loaded {len(df):,} historical SPU sales records")
        logger.info(f"Historical period: August 2024 first half")
        logger.info(f"Categories: {df['cate_name'].nunique()}")
        logger.info(f"Sub-categories: {df['sub_cate_name'].nunique()}")
        logger.info(f"Stores: {df['str_code'].nunique()}")
        logger.info(f"SPUs: {df['spu_code'].nunique()}")
        
        return df
        
    except Exception as e:
        logger.error(f"Error loading historical data: {e}")
        raise

def create_store_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Create store groups using same logic as current analysis."""
    df_with_groups = df.copy()
    
    # Use same store grouping logic as main analysis
    df_with_groups['store_group'] = df_with_groups['str_code'].apply(
        lambda x: get_actual_store_group(str(x))
    )
    
    return df_with_groups

def analyze_historical_spu_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze historical SPU counts by Store Group × Sub-Category."""
    
    logger.info("Analyzing historical SPU counts by Store Group × Sub-Category...")
    
    # Group by Store Group × Sub-Category and count distinct SPUs
    historical_counts = df.groupby(['store_group', 'cate_name', 'sub_cate_name']).agg({
        'spu_code': 'nunique',
        'quantity': 'sum',
        'spu_sales_amt': 'sum',
        'str_code': 'nunique'
    }).reset_index()
    
    historical_counts.columns = ['store_group', 'category', 'sub_category', 'historical_spu_count', 
                                'historical_total_quantity', 'historical_total_sales', 'historical_store_count']
    
    # Calculate performance metrics
    historical_counts['historical_avg_sales_per_spu'] = historical_counts['historical_total_sales'] / historical_counts['historical_spu_count']
    historical_counts['historical_avg_quantity_per_spu'] = historical_counts['historical_total_quantity'] / historical_counts['historical_spu_count']
    historical_counts['historical_sales_per_store'] = historical_counts['historical_total_sales'] / historical_counts['historical_store_count']
    
    logger.info(f"Found {len(historical_counts)} historical Store Group × Sub-Category combinations")
    
    return historical_counts

def load_current_analysis() -> pd.DataFrame:
    """Load the current Fast Fish analysis for comparison."""
    try:
        # Load the most recent Fast Fish analysis from Step 14
        current_file = "../output/fast_fish_spu_count_recommendations_20250708_101111.csv"
        
        if not os.path.exists(current_file):
            logger.warning("Current analysis file not found, will create historical reference only")
            return None
        
        logger.info(f"Loading current analysis from: {current_file}")
        df = pd.read_csv(current_file)
        
        # Parse the Target_Style_Tags to separate category and sub_category
        df[['category', 'sub_category']] = df['Target_Style_Tags'].str.split(' | ', expand=True)
        
        logger.info(f"Loaded {len(df)} current recommendations")
        
        return df
        
    except Exception as e:
        logger.warning(f"Could not load current analysis: {e}")
        return None

def create_year_over_year_comparison(historical_df: pd.DataFrame, current_df: pd.DataFrame = None) -> pd.DataFrame:
    """Create year-over-year comparison between 202408A and current analysis."""
    
    logger.info("Creating year-over-year comparison...")
    
    if current_df is None:
        logger.info("No current analysis available, creating historical reference only")
        comparison_df = historical_df.copy()
        comparison_df['period'] = '202408A_Historical'
        return comparison_df
    
    # Merge historical and current data
    comparison_df = historical_df.merge(
        current_df[['Store_Group_Name', 'category', 'sub_category', 'Current_SPU_Quantity', 
                   'Target_SPU_Quantity', 'Stores_In_Group_Selling_This_Category', 
                   'Total_Current_Sales', 'Avg_Sales_Per_SPU']],
        left_on=['store_group', 'category', 'sub_category'],
        right_on=['Store_Group_Name', 'category', 'sub_category'],
        how='outer',
        suffixes=('_historical', '_current')
    )
    
    # Calculate year-over-year changes
    comparison_df['yoy_spu_count_change'] = comparison_df['Current_SPU_Quantity'] - comparison_df['historical_spu_count']
    comparison_df['yoy_spu_count_change_pct'] = (comparison_df['yoy_spu_count_change'] / comparison_df['historical_spu_count'] * 100).round(1)
    
    comparison_df['yoy_sales_change'] = comparison_df['Total_Current_Sales'] - comparison_df['historical_total_sales']
    comparison_df['yoy_sales_change_pct'] = (comparison_df['yoy_sales_change'] / comparison_df['historical_total_sales'] * 100).round(1)
    
    comparison_df['yoy_avg_sales_per_spu_change'] = comparison_df['Avg_Sales_Per_SPU'] - comparison_df['historical_avg_sales_per_spu']
    comparison_df['yoy_avg_sales_per_spu_change_pct'] = (comparison_df['yoy_avg_sales_per_spu_change'] / comparison_df['historical_avg_sales_per_spu'] * 100).round(1)
    
    logger.info(f"Created year-over-year comparison for {len(comparison_df)} combinations")
    
    return comparison_df

def create_historical_fast_fish_format(historical_df: pd.DataFrame) -> pd.DataFrame:
    """Create Fast Fish format using historical data as baseline."""
    
    logger.info("Creating historical Fast Fish format...")
    
    # Create historical recommendations using same logic
    output_df = pd.DataFrame({
        'Year': 2024,
        'Month': 7,
        'Period': 'A',
        'Store_Group_Name': historical_df['store_group'],
        'Target_Style_Tags': historical_df['category'] + ' | ' + historical_df['sub_category'],
        'Historical_SPU_Quantity': historical_df['historical_spu_count'],
        'Historical_Total_Sales': historical_df['historical_total_sales'].round(2),
        'Historical_Avg_Sales_Per_SPU': historical_df['historical_avg_sales_per_spu'].round(2),
        'Historical_Store_Count': historical_df['historical_store_count'],
        'Historical_Total_Quantity': historical_df['historical_total_quantity'].round(1),
        'Historical_Sales_Per_Store': historical_df['historical_sales_per_store'].round(2)
    })
    
    # Filter for meaningful historical data
    output_df = output_df[
        (output_df['Historical_SPU_Quantity'] >= 1) &
        (output_df['Historical_Store_Count'] >= 2)
    ].copy()
    
    # Sort by store group and sales
    output_df = output_df.sort_values(['Store_Group_Name', 'Historical_Total_Sales'], ascending=[True, False])
    
    logger.info(f"Created {len(output_df)} historical Fast Fish format records")
    
    return output_df

def generate_historical_insights(historical_df: pd.DataFrame) -> Dict:
    """Generate key insights from historical data."""
    
    insights = {
        'total_combinations': int(len(historical_df)),
        'unique_store_groups': int(historical_df['store_group'].nunique()),
        'unique_categories': int(historical_df['category'].nunique()),
        'unique_subcategories': int(historical_df['sub_category'].nunique()),
        'total_historical_spus': int(historical_df['historical_spu_count'].sum()),
        'avg_spus_per_combination': float(historical_df['historical_spu_count'].mean()),
        'total_historical_sales': float(historical_df['historical_total_sales'].sum()),
        'avg_sales_per_spu_overall': float((historical_df['historical_total_sales'].sum() / historical_df['historical_spu_count'].sum())),
        'top_performing_categories': [],
        'top_performing_store_groups': []
    }
    
    # Top performing categories by average sales per SPU
    category_performance = historical_df.groupby('category').agg({
        'historical_total_sales': 'sum',
        'historical_spu_count': 'sum'
    })
    category_performance['avg_sales_per_spu'] = category_performance['historical_total_sales'] / category_performance['historical_spu_count']
    top_categories = category_performance.sort_values('avg_sales_per_spu', ascending=False).head(5)
    
    insights['top_performing_categories'] = [
        {'category': cat, 'avg_sales_per_spu': float(row['avg_sales_per_spu'])}
        for cat, row in top_categories.iterrows()
    ]
    
    # Top performing store groups
    group_performance = historical_df.groupby('store_group').agg({
        'historical_total_sales': 'sum',
        'historical_spu_count': 'sum'
    })
    group_performance['avg_sales_per_spu'] = group_performance['historical_total_sales'] / group_performance['historical_spu_count']
    top_groups = group_performance.sort_values('avg_sales_per_spu', ascending=False).head(5)
    
    insights['top_performing_store_groups'] = [
        {'store_group': group, 'avg_sales_per_spu': float(row['avg_sales_per_spu'])}
        for group, row in top_groups.iterrows()
    ]
    
    return insights

def save_results(historical_ff_df: pd.DataFrame, comparison_df: pd.DataFrame, insights: Dict) -> List[str]:
    """Save all historical analysis results."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_files = []
    
    # Ensure output directory exists
    os.makedirs("../output", exist_ok=True)
    
    # Save historical Fast Fish format
    historical_ff_file = f"../output/historical_reference_202408A_{timestamp}.csv"
    historical_ff_df.to_csv(historical_ff_file, index=False)
    output_files.append(historical_ff_file)
    logger.info(f"Saved historical Fast Fish format to: {historical_ff_file}")
    
    # Save year-over-year comparison
    comparison_file = f"../output/year_over_year_comparison_{timestamp}.csv"
    comparison_df.to_csv(comparison_file, index=False)
    output_files.append(comparison_file)
    logger.info(f"Saved year-over-year comparison to: {comparison_file}")
    
    # Save insights
    insights_file = f"../output/historical_insights_202408A_{timestamp}.json"
    with open(insights_file, 'w') as f:
        json.dump(insights, f, indent=2)
    output_files.append(insights_file)
    logger.info(f"Saved historical insights to: {insights_file}")
    
    # Print summary
    print(f"\n=== STEP 15: HISTORICAL REFERENCE ANALYSIS (202408A) ===")
    print(f"Analysis period: August 2024 first half")
    print(f"Total combinations: {insights['total_combinations']:,}")
    print(f"Store groups: {insights['unique_store_groups']}")
    print(f"Sub-categories: {insights['unique_subcategories']}")
    print(f"Historical SPUs: {insights['total_historical_spus']:,}")
    print(f"Historical sales: ¥{insights['total_historical_sales']:,.0f}")
    print(f"Avg sales per SPU: ¥{insights['avg_sales_per_spu_overall']:.2f}")
    print(f"\nTop performing categories (202408A):")
    for cat in insights['top_performing_categories'][:3]:
        print(f"  • {cat['category']}: ¥{cat['avg_sales_per_spu']:.0f} avg per SPU")
    print(f"\nOutput files: {len(output_files)} files created")
    
    return output_files

def main():
    """Main execution function."""
    
    logger.info("Starting Step 15: Historical Reference Analysis for 202408A...")
    
    try:
        # Load historical data
        historical_df = load_historical_data()
        
        # Create store groups
        historical_grouped_df = create_store_groups(historical_df)
        
        # Analyze historical SPU counts
        historical_analysis = analyze_historical_spu_counts(historical_grouped_df)
        
        # Load current analysis for comparison
        current_analysis = load_current_analysis()
        
        # Create year-over-year comparison
        comparison_df = create_year_over_year_comparison(historical_analysis, current_analysis)
        
        # Create historical Fast Fish format
        historical_ff_df = create_historical_fast_fish_format(historical_analysis)
        
        # Generate insights
        insights = generate_historical_insights(historical_analysis)
        
        # Save results
        output_files = save_results(historical_ff_df, comparison_df, insights)
        
        logger.info("Step 15: Historical Reference Analysis completed successfully!")
        
        return output_files
        
    except Exception as e:
        logger.error(f"Error in Step 15: {e}")
        raise

if __name__ == "__main__":
    main()
