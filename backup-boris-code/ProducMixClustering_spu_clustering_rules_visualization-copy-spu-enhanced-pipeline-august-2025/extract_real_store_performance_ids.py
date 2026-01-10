#!/usr/bin/env python3
"""
Extract Real Store Performance IDs from Rule 12 Analysis
=======================================================

This script provides the ACTUAL store performance distribution and specific store IDs
based on our Rule 12 sales performance analysis, not the presentation placeholder numbers.

Boss's Question: "Is there a way to see what these store IDs are?"
Answer: Yes! Here are the real store performance categories and their specific store IDs.
"""

import pandas as pd
import numpy as np
import os
from typing import Dict, List, Tuple

def load_rule12_data() -> pd.DataFrame:
    """Load Rule 12 sales performance data."""
    print("🔍 Looking for Rule 12 sales performance data...")
    
    # Try the results file first (store-level aggregated data)
    results_file = "output/rule12_sales_performance_spu_results.csv"
    if os.path.exists(results_file):
        print(f"✓ Found Rule 12 results: {results_file}")
        df = pd.read_csv(results_file)
        print(f"✓ Loaded {len(df):,} stores with performance classifications")
        return df
    
    # Fallback to details file
    details_file = "output/rule12_sales_performance_spu_details.csv"
    if os.path.exists(details_file):
        print(f"✓ Found Rule 12 details: {details_file}")
        df = pd.read_csv(details_file)
        # Aggregate to store level
        store_level = df.groupby('str_code').agg({
            'performance_level': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else 'unknown',
            'opportunity_gap_z_score': 'mean',
            'opportunity_value': 'sum'
        }).reset_index()
        print(f"✓ Aggregated to {len(store_level):,} stores")
        return store_level
    
    print("❌ Rule 12 data not found")
    return pd.DataFrame()

def analyze_rule12_performance(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze the Rule 12 performance classifications."""
    print("\n📊 Analyzing Rule 12 Performance Classifications:")
    
    # Map performance levels to readable categories
    performance_mapping = {
        'top_performer': 'Top Performers',
        'performing_well': 'Performing Well', 
        'some_opportunity': 'Growth Opportunity',
        'good_opportunity': 'Growth Opportunity',
        'major_opportunity': 'Optimization Needed'
    }
    
    # Create readable performance category
    if 'store_performance_level' in df.columns:
        df['performance_category'] = df['store_performance_level'].map(performance_mapping)
    elif 'performance_level' in df.columns:
        df['performance_category'] = df['performance_level'].map(performance_mapping)
    else:
        print("❌ No performance level column found")
        return df
    
    # Fill any unmapped values
    df['performance_category'] = df['performance_category'].fillna('Unknown')
    
    # Show distribution
    print("📈 REAL Store Performance Distribution:")
    category_counts = df['performance_category'].value_counts()
    total_stores = len(df)
    
    for category, count in category_counts.items():
        percentage = (count / total_stores) * 100
        print(f"   {category}: {count:,} stores ({percentage:.1f}%)")
    
    return df

def create_store_id_files(performance_data: pd.DataFrame, source_method: str) -> None:
    """Create files with specific store IDs for each performance category."""
    print(f"\n🏪 Creating Store ID Files (Source: {source_method}):")
    print("=" * 60)
    
    store_id_col = 'str_code'
    
    for category in ['Top Performers', 'Performing Well', 'Growth Opportunity', 'Optimization Needed']:
        stores_in_category = performance_data[performance_data['performance_category'] == category][store_id_col].tolist()
        
        print(f"\n{category}: {len(stores_in_category)} stores")
        print("-" * 40)
        
        if stores_in_category:
            # Show first 10 store IDs as a sample
            sample_stores = stores_in_category[:10]
            print(f"Sample Store IDs: {sample_stores}")
            
            if len(stores_in_category) > 10:
                print(f"... and {len(stores_in_category) - 10} more stores")
            
            # Save full list to file
            filename = f"real_store_list_{category.lower().replace(' ', '_')}.txt"
            with open(filename, 'w') as f:
                f.write(f"REAL STORE PERFORMANCE ANALYSIS\n")
                f.write(f"Source Method: {source_method}\n")
                f.write(f"Generated: {pd.Timestamp.now()}\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"{category} - {len(stores_in_category)} stores\n")
                f.write("-" * 40 + "\n\n")
                
                f.write("STORE IDs:\n")
                for i, store_id in enumerate(stores_in_category, 1):
                    f.write(f"{i:4d}. {store_id}\n")
                
                f.write(f"\n\nBUSINESS CONTEXT:\n")
                if category == "Top Performers":
                    f.write("These stores consistently exceed cluster benchmarks (Z-score < -0.8).\n")
                    f.write("Action: Study their best practices for replication across network.\n")
                    f.write("Characteristics: Minimal improvement recommendations needed.\n")
                elif category == "Performing Well":
                    f.write("These stores meet expectations with stable performance (-0.8 ≤ Z-score ≤ 0).\n")
                    f.write("Action: Maintain current strategies, monitor for consistency.\n")
                    f.write("Characteristics: Operating within normal performance ranges.\n")
                elif category == "Growth Opportunity":
                    f.write("These stores have significant potential for improvement (0 < Z-score ≤ 2.0).\n")
                    f.write("Action: Focus improvement initiatives and resource allocation here.\n")
                    f.write("Characteristics: Underperforming vs cluster peers but recoverable.\n")
                elif category == "Optimization Needed":
                    f.write("These stores require immediate attention (Z-score > 2.0).\n")
                    f.write("Action: Implement urgent optimization measures and support.\n")
                    f.write("Characteristics: Significantly underperforming, high investment needs.\n")
                
                # Add performance metrics if available
                category_data = performance_data[performance_data['performance_category'] == category]
                if 'avg_opportunity_z_score' in category_data.columns:
                    avg_z_score = category_data['avg_opportunity_z_score'].mean()
                    f.write(f"\nAVERAGE Z-SCORE: {avg_z_score:.2f}\n")
                
                if 'total_opportunity_value' in category_data.columns:
                    avg_opportunity = category_data['total_opportunity_value'].mean()
                    f.write(f"AVERAGE OPPORTUNITY VALUE: ¥{avg_opportunity:,.0f}\n")
                
                if 'total_investment_required' in category_data.columns:
                    avg_investment = category_data['total_investment_required'].mean()
                    f.write(f"AVERAGE INVESTMENT REQUIRED: ¥{avg_investment:,.0f}\n")
            
            print(f"✓ Full list saved to: {filename}")
        else:
            print("No stores in this category")

def create_performance_summary(df: pd.DataFrame) -> None:
    """Create a detailed performance summary."""
    print("\n" + "=" * 80)
    print("DETAILED PERFORMANCE ANALYSIS")
    print("=" * 80)
    
    # Overall statistics
    total_stores = len(df)
    print(f"Total Stores Analyzed: {total_stores:,}")
    
    if 'avg_opportunity_z_score' in df.columns:
        avg_z_score = df['avg_opportunity_z_score'].mean()
        print(f"Average Z-Score: {avg_z_score:.2f}")
    
    if 'total_investment_required' in df.columns:
        total_investment = df['total_investment_required'].sum()
        print(f"Total Investment Required: ¥{total_investment:,.0f}")
    
    if 'total_quantity_increase_needed' in df.columns:
        total_quantity = df['total_quantity_increase_needed'].sum()
        print(f"Total Quantity Increase Needed: {total_quantity:,.0f} units")
    
    # Performance distribution details
    print(f"\nPERFORMANCE DISTRIBUTION DETAILS:")
    category_stats = df.groupby('performance_category').agg({
        'str_code': 'count',
        'avg_opportunity_z_score': 'mean' if 'avg_opportunity_z_score' in df.columns else lambda x: 0,
        'total_investment_required': 'mean' if 'total_investment_required' in df.columns else lambda x: 0
    }).reset_index()
    
    for _, row in category_stats.iterrows():
        category = row['performance_category']
        count = row['str_code']
        percentage = (count / total_stores) * 100
        avg_z = row.get('avg_opportunity_z_score', 0)
        avg_inv = row.get('total_investment_required', 0)
        
        print(f"\n{category}:")
        print(f"  Count: {count:,} stores ({percentage:.1f}%)")
        if avg_z != 0:
            print(f"  Avg Z-Score: {avg_z:.2f}")
        if avg_inv != 0:
            print(f"  Avg Investment: ¥{avg_inv:,.0f}")

def create_boss_summary() -> None:
    """Create a comprehensive summary for the boss."""
    print("\n" + "=" * 80)
    print("ANSWER TO BOSS'S QUESTION")
    print("=" * 80)
    print("""
BOSS ASKED: "Is there a way to see what these store IDs are?"

ANSWER: Yes! I've extracted the REAL store performance data and specific store IDs
from our Rule 12 sales performance analysis.

KEY FINDINGS:
✓ Real performance distribution based on statistical Z-score analysis
✓ Each store compared against cluster peer benchmarks (90th percentile)
✓ Performance categories defined by rigorous mathematical thresholds
✓ Specific store IDs extracted for each performance tier

FILES CREATED:
📁 real_store_list_top_performers.txt     - Stores exceeding benchmarks
📁 real_store_list_performing_well.txt    - Stores meeting expectations  
📁 real_store_list_growth_opportunity.txt - Stores with improvement potential
📁 real_store_list_optimization_needed.txt - Stores requiring urgent attention

METHODOLOGY:
Our Rule 12 analysis uses opportunity gap Z-score analysis:
• Compares each store's sales vs cluster top 90th percentile performers
• Calculates Z-scores: (Store_Gap - Cluster_Mean) / Cluster_StdDev
• Categories based on statistical significance thresholds
• Includes specific quantity increase recommendations and investment requirements

BUSINESS IMPACT:
Each file contains actionable store lists with:
- Specific store IDs for targeted interventions
- Performance context and recommended actions
- Investment requirements and opportunity values
- Statistical backing for prioritization decisions
""")

def main():
    """Main execution function."""
    print("🎯 Real Store Performance Analysis - Extract Actual Store IDs")
    print("=" * 75)
    
    # Load Rule 12 performance data
    rule12_data = load_rule12_data()
    if rule12_data.empty:
        print("❌ No Rule 12 performance data available")
        return
    
    # Analyze performance classifications
    performance_data = analyze_rule12_performance(rule12_data)
    
    # Create store ID files
    create_store_id_files(performance_data, "Rule 12 Sales Performance Analysis")
    
    # Create detailed summary
    create_performance_summary(performance_data)
    
    # Create boss response
    create_boss_summary()
    
    print(f"\n✅ Real store performance analysis complete!")
    print(f"📁 Store ID files created with rigorous statistical classifications")

if __name__ == "__main__":
    main() 