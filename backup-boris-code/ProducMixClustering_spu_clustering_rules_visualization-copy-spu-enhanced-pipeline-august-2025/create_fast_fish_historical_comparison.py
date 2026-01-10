#!/usr/bin/env python3
"""
Fast Fish Historical Comparison
==============================

Create a comprehensive historical comparison report for Fast Fish
comparing 202407A (July 2024) baseline with current 202506B recommendations.

This provides the exact metrics Fast Fish needs for their analysis:
- Historical SPU count baselines by Store Group × Sub-Category
- Current recommendations vs historical performance
- Growth/decline patterns
- Business rationale for changes
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import os
from typing import Dict, List, Tuple
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_historical_baseline() -> pd.DataFrame:
    """Load the historical baseline analysis we just created."""
    
    # Find the most recent historical reference file
    historical_files = [f for f in os.listdir('output') if f.startswith('historical_reference_202407A_')]
    if not historical_files:
        raise FileNotFoundError("No historical reference files found. Run create_historical_reference_analysis.py first.")
    
    latest_file = sorted(historical_files)[-1]
    historical_path = f"output/{latest_file}"
    
    logger.info(f"Loading historical baseline from: {historical_path}")
    df = pd.read_csv(historical_path)
    
    return df

def load_current_recommendations() -> pd.DataFrame:
    """Load the current Fast Fish recommendations."""
    
    current_file = "output/fast_fish_spu_count_recommendations_20250702_124006.csv"
    
    if not os.path.exists(current_file):
        raise FileNotFoundError(f"Current recommendations file not found: {current_file}")
    
    logger.info(f"Loading current recommendations from: {current_file}")
    df = pd.read_csv(current_file)
    
    return df

def create_comprehensive_comparison(historical_df: pd.DataFrame, current_df: pd.DataFrame) -> pd.DataFrame:
    """Create comprehensive comparison between historical and current data."""
    
    logger.info("Creating comprehensive Fast Fish comparison...")
    
    # Parse current recommendations
    current_df[["category", "sub_category"]] = current_df["Target_Style_Tags"].str.split(" | ", expand=True, n=1)
    
    # Merge historical and current data
    comparison_df = historical_df.merge(
        current_df[['Store_Group_Name', 'category', 'sub_category', 'Current_SPU_Quantity', 
                   'Target_SPU_Quantity', 'Stores_In_Group_Selling_This_Category', 
                   'Total_Current_Sales', 'Avg_Sales_Per_SPU', 'Data_Based_Rationale']],
        left_on=['Store_Group_Name', 'Target_Style_Tags'],
        right_on=['Store_Group_Name', 'Target_Style_Tags'],
        how='outer',
        suffixes=('_historical', '_current')
    )
    
    # Calculate performance metrics
    comparison_df['Historical_vs_Current_SPU_Change'] = comparison_df['Current_SPU_Quantity'] - comparison_df['Historical_SPU_Quantity']
    comparison_df['Historical_vs_Current_SPU_Change_Pct'] = (
        comparison_df['Historical_vs_Current_SPU_Change'] / comparison_df['Historical_SPU_Quantity'] * 100
    ).round(1)
    
    comparison_df['Historical_vs_Target_SPU_Change'] = comparison_df['Target_SPU_Quantity'] - comparison_df['Historical_SPU_Quantity']
    comparison_df['Historical_vs_Target_SPU_Change_Pct'] = (
        comparison_df['Historical_vs_Target_SPU_Change'] / comparison_df['Historical_SPU_Quantity'] * 100
    ).round(1)
    
    comparison_df['Sales_Performance_vs_Historical'] = comparison_df['Total_Current_Sales'] - comparison_df['Historical_Total_Sales']
    comparison_df['Sales_Performance_vs_Historical_Pct'] = (
        comparison_df['Sales_Performance_vs_Historical'] / comparison_df['Historical_Total_Sales'] * 100
    ).round(1)
    
    # Create business insights
    comparison_df['Business_Insight'] = comparison_df.apply(create_business_insight, axis=1)
    
    # Sort by store group and historical sales
    comparison_df = comparison_df.sort_values(['Store_Group_Name', 'Historical_Total_Sales'], ascending=[True, False])
    
    return comparison_df

def create_business_insight(row) -> str:
    """Create business insight based on historical vs current performance."""
    
    hist_spus = row.get('Historical_SPU_Quantity', 0)
    curr_spus = row.get('Current_SPU_Quantity', 0)
    target_spus = row.get('Target_SPU_Quantity', 0)
    hist_sales = row.get('Historical_Total_Sales', 0)
    curr_sales = row.get('Total_Current_Sales', 0)
    
    insights = []
    
    # SPU count analysis
    if pd.notna(hist_spus) and pd.notna(target_spus):
        spu_change = target_spus - hist_spus
        if spu_change > 0:
            insights.append(f"Expand by {spu_change} SPUs (+{spu_change/hist_spus*100:.1f}%)")
        elif spu_change < 0:
            insights.append(f"Reduce by {abs(spu_change)} SPUs ({spu_change/hist_spus*100:.1f}%)")
        else:
            insights.append("Maintain current SPU count")
    
    # Sales performance analysis
    if pd.notna(hist_sales) and pd.notna(curr_sales):
        sales_change = curr_sales - hist_sales
        if sales_change > 0:
            insights.append(f"Sales up ¥{sales_change:,.0f} (+{sales_change/hist_sales*100:.1f}%)")
        elif sales_change < 0:
            insights.append(f"Sales down ¥{abs(sales_change):,.0f} ({sales_change/hist_sales*100:.1f}%)")
    
    # Historical performance context
    if pd.notna(hist_spus) and hist_spus > 0:
        hist_avg_sales = hist_sales / hist_spus if hist_sales > 0 else 0
        if hist_avg_sales > 5000:
            insights.append("High historical performer")
        elif hist_avg_sales > 2000:
            insights.append("Moderate historical performer")
        else:
            insights.append("Low historical performer")
    
    return " | ".join(insights) if insights else "No historical data"

def create_executive_summary(comparison_df: pd.DataFrame) -> Dict:
    """Create executive summary for Fast Fish management."""
    
    logger.info("Creating executive summary...")
    
    # Filter for valid comparisons
    valid_comparisons = comparison_df[
        (comparison_df['Historical_SPU_Quantity'].notna()) & 
        (comparison_df['Target_SPU_Quantity'].notna())
    ]
    
    summary = {
        'analysis_date': datetime.now().strftime('%Y-%m-%d'),
        'historical_period': '202407A (July 2024 H1)',
        'current_period': '202506B (June 2025 H2)',
        'total_combinations_analyzed': len(valid_comparisons),
        'store_groups_analyzed': valid_comparisons['Store_Group_Name'].nunique(),
        'sub_categories_analyzed': valid_comparisons['Target_Style_Tags'].nunique(),
        
        # Historical baseline metrics
        'historical_total_spus': int(valid_comparisons['Historical_SPU_Quantity'].sum()),
        'historical_total_sales': float(valid_comparisons['Historical_Total_Sales'].sum()),
        'historical_avg_sales_per_spu': float(valid_comparisons['Historical_Total_Sales'].sum() / valid_comparisons['Historical_SPU_Quantity'].sum()),
        
        # Current performance metrics
        'current_total_spus': int(valid_comparisons['Current_SPU_Quantity'].sum()),
        'current_total_sales': float(valid_comparisons['Total_Current_Sales'].sum()),
        'current_avg_sales_per_spu': float(valid_comparisons['Total_Current_Sales'].sum() / valid_comparisons['Current_SPU_Quantity'].sum()),
        
        # Target recommendations
        'target_total_spus': int(valid_comparisons['Target_SPU_Quantity'].sum()),
        'net_spu_change_vs_historical': int(valid_comparisons['Target_SPU_Quantity'].sum() - valid_comparisons['Historical_SPU_Quantity'].sum()),
        'net_spu_change_vs_current': int(valid_comparisons['Target_SPU_Quantity'].sum() - valid_comparisons['Current_SPU_Quantity'].sum()),
        
        # Performance insights
        'categories_expanding': len(valid_comparisons[valid_comparisons['Historical_vs_Target_SPU_Change'] > 0]),
        'categories_contracting': len(valid_comparisons[valid_comparisons['Historical_vs_Target_SPU_Change'] < 0]),
        'categories_stable': len(valid_comparisons[valid_comparisons['Historical_vs_Target_SPU_Change'] == 0]),
        
        # Top performers
        'top_growth_categories': [],
        'top_decline_categories': [],
        'top_historical_performers': []
    }
    
    # Top growth categories
    growth_categories = valid_comparisons[valid_comparisons['Historical_vs_Target_SPU_Change'] > 0].nlargest(5, 'Historical_vs_Target_SPU_Change')
    summary['top_growth_categories'] = [
        {
            'store_group': row['Store_Group_Name'],
            'category': row['Target_Style_Tags'],
            'historical_spus': int(row['Historical_SPU_Quantity']),
            'target_spus': int(row['Target_SPU_Quantity']),
            'growth': int(row['Historical_vs_Target_SPU_Change']),
            'growth_pct': float(row['Historical_vs_Target_SPU_Change_Pct'])
        }
        for _, row in growth_categories.iterrows()
    ]
    
    # Top decline categories
    decline_categories = valid_comparisons[valid_comparisons['Historical_vs_Target_SPU_Change'] < 0].nsmallest(5, 'Historical_vs_Target_SPU_Change')
    summary['top_decline_categories'] = [
        {
            'store_group': row['Store_Group_Name'],
            'category': row['Target_Style_Tags'],
            'historical_spus': int(row['Historical_SPU_Quantity']),
            'target_spus': int(row['Target_SPU_Quantity']),
            'decline': int(row['Historical_vs_Target_SPU_Change']),
            'decline_pct': float(row['Historical_vs_Target_SPU_Change_Pct'])
        }
        for _, row in decline_categories.iterrows()
    ]
    
    # Top historical performers
    top_performers = valid_comparisons.nlargest(10, 'Historical_Total_Sales')
    summary['top_historical_performers'] = [
        {
            'store_group': row['Store_Group_Name'],
            'category': row['Target_Style_Tags'],
            'historical_sales': float(row['Historical_Total_Sales']),
            'historical_spus': int(row['Historical_SPU_Quantity']),
            'avg_sales_per_spu': float(row['Historical_Avg_Sales_Per_SPU']),
            'recommendation': 'Expand' if row['Historical_vs_Target_SPU_Change'] > 0 else 'Maintain' if row['Historical_vs_Target_SPU_Change'] == 0 else 'Reduce'
        }
        for _, row in top_performers.iterrows()
    ]
    
    return summary

def save_fast_fish_analysis(comparison_df: pd.DataFrame, summary: Dict) -> List[str]:
    """Save comprehensive Fast Fish analysis."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_files = []
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Save comprehensive comparison
    comparison_file = f"output/fast_fish_historical_comparison_{timestamp}.csv"
    comparison_df.to_csv(comparison_file, index=False)
    output_files.append(comparison_file)
    logger.info(f"Saved Fast Fish comparison to: {comparison_file}")
    
    # Save executive summary
    summary_file = f"output/fast_fish_executive_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    output_files.append(summary_file)
    logger.info(f"Saved executive summary to: {summary_file}")
    
    # Create simplified CSV for Fast Fish review
    simplified_df = comparison_df[[
        'Store_Group_Name', 'Target_Style_Tags', 
        'Historical_SPU_Quantity', 'Current_SPU_Quantity', 'Target_SPU_Quantity',
        'Historical_Total_Sales', 'Total_Current_Sales',
        'Historical_vs_Target_SPU_Change', 'Historical_vs_Target_SPU_Change_Pct',
        'Sales_Performance_vs_Historical_Pct', 'Business_Insight'
    ]].copy()
    
    simplified_file = f"output/fast_fish_simplified_comparison_{timestamp}.csv"
    simplified_df.to_csv(simplified_file, index=False)
    output_files.append(simplified_file)
    logger.info(f"Saved simplified comparison to: {simplified_file}")
    
    return output_files

def print_executive_summary(summary: Dict):
    """Print executive summary for immediate review."""
    
    print(f"\n=== FAST FISH HISTORICAL COMPARISON ANALYSIS ===")
    print(f"Analysis Date: {summary['analysis_date']}")
    print(f"Historical Baseline: {summary['historical_period']}")
    print(f"Current Period: {summary['current_period']}")
    print(f"")
    print(f"SCOPE:")
    print(f"  • {summary['total_combinations_analyzed']:,} Store Group × Sub-Category combinations")
    print(f"  • {summary['store_groups_analyzed']} store groups analyzed")
    print(f"  • {summary['sub_categories_analyzed']} sub-categories analyzed")
    print(f"")
    print(f"HISTORICAL BASELINE (202407A):")
    print(f"  • Total SPUs: {summary['historical_total_spus']:,}")
    print(f"  • Total Sales: ¥{summary['historical_total_sales']:,.0f}")
    print(f"  • Avg Sales per SPU: ¥{summary['historical_avg_sales_per_spu']:,.0f}")
    print(f"")
    print(f"CURRENT PERFORMANCE (202506B):")
    print(f"  • Total SPUs: {summary['current_total_spus']:,}")
    print(f"  • Total Sales: ¥{summary['current_total_sales']:,.0f}")
    print(f"  • Avg Sales per SPU: ¥{summary['current_avg_sales_per_spu']:,.0f}")
    print(f"")
    print(f"RECOMMENDATIONS:")
    print(f"  • Target SPUs: {summary['target_total_spus']:,}")
    print(f"  • Change vs Historical: {summary['net_spu_change_vs_historical']:+,} SPUs")
    print(f"  • Change vs Current: {summary['net_spu_change_vs_current']:+,} SPUs")
    print(f"")
    print(f"CATEGORY CHANGES:")
    print(f"  • Expanding: {summary['categories_expanding']} categories")
    print(f"  • Contracting: {summary['categories_contracting']} categories")
    print(f"  • Stable: {summary['categories_stable']} categories")
    print(f"")
    print(f"TOP GROWTH OPPORTUNITIES:")
    for i, cat in enumerate(summary['top_growth_categories'][:3], 1):
        print(f"  {i}. {cat['store_group']} - {cat['category']}")
        print(f"     Historical: {cat['historical_spus']} → Target: {cat['target_spus']} (+{cat['growth']} SPUs, +{cat['growth_pct']:.1f}%)")
    print(f"")
    print(f"Files created: {len(output_files)} analysis files")

def main():
    """Main execution function."""
    
    logger.info("Starting Fast Fish Historical Comparison Analysis...")
    
    try:
        # Load data
        historical_df = load_historical_baseline()
        current_df = load_current_recommendations()
        
        # Create comprehensive comparison
        comparison_df = create_comprehensive_comparison(historical_df, current_df)
        
        # Create executive summary
        summary = create_executive_summary(comparison_df)
        
        # Save analysis
        output_files = save_fast_fish_analysis(comparison_df, summary)
        
        # Print summary
        print_executive_summary(summary)
        
        logger.info("Fast Fish Historical Comparison Analysis completed successfully!")
        
        return output_files
        
    except Exception as e:
        logger.error(f"Error in Fast Fish analysis: {e}")
        raise

if __name__ == "__main__":
    main()
