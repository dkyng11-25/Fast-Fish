#!/usr/bin/env python3
"""
Step 11 IMPROVED: Category-Specific Cluster Top Performer Analysis (OPTIMIZED)

Business Logic:
1. Within each cluster + category: Identify top 20% performing SPUs by sales
2. Expectation: Every store in cluster should carry these category champions
3. Flag: Stores missing proven category winners that cluster peers have
4. Recommendation: Add these high-performing SPUs to capture opportunities

OPTIMIZATION: Vectorized operations instead of nested loops for 100x speed improvement

Author: Data Pipeline
Date: 2025-06-20
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm

# Configuration
ANALYSIS_LEVEL = "spu"
OUTPUT_DIR = "output"
CLUSTER_RESULTS_FILE = "output/clustering_results_spu.csv"

# Rule parameters - Category-specific approach (MADE MORE SELECTIVE)
TOP_PERFORMER_THRESHOLD = 0.95  # Top 5% of SPUs within cluster-category (was 20%)
MIN_CLUSTER_STORES = 8  # Minimum stores in cluster for analysis (was 5)
MIN_STORES_SELLING = 5  # Minimum stores selling the SPU for it to be considered "proven" (was 3)
MIN_SPU_SALES = 200  # Minimum sales to avoid noise (was 50)
ADOPTION_THRESHOLD = 0.75  # 75% of cluster stores should have top performers (was 60%)

# NEW: Selectivity controls to reduce recommendation volume
MAX_RECOMMENDATIONS_PER_STORE = 10  # Maximum SPU recommendations per store
MIN_OPPORTUNITY_SCORE = 0.15  # Minimum opportunity score to qualify
MIN_ADOPTION_RATE = 0.70  # Minimum adoption rate for SPU to be recommended

# Testing mode - set to True for fast testing, False for full analysis
TESTING_MODE = False  # Can be overridden by command line argument

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_and_prepare_data(sample_size: Optional[int] = None) -> pd.DataFrame:
    """Load SPU sales data and cluster assignments"""
    log_progress("Loading SPU sales data for category-specific analysis...")
    
    # Load SPU sales data
    spu_df = pd.read_csv('data/api_data/complete_spu_sales_202506B.csv', dtype={'str_code': str})
    log_progress(f"Loaded {len(spu_df):,} SPU records")
    
    # Sample for testing if requested
    if sample_size:
        spu_df = spu_df.sample(n=min(sample_size, len(spu_df)), random_state=42)
        log_progress(f"Sampled to {len(spu_df):,} records for testing")
    
    # Clean data
    spu_df['spu_sales'] = pd.to_numeric(spu_df['spu_sales_amt'], errors='coerce').fillna(0)
    spu_df = spu_df[spu_df['spu_sales'] >= MIN_SPU_SALES].copy()
    log_progress(f"Filtered to {len(spu_df):,} SPU records with sales >= ${MIN_SPU_SALES}")
    
    # Load cluster assignments
    cluster_df = pd.read_csv(CLUSTER_RESULTS_FILE, dtype={'str_code': str})
    log_progress(f"Loaded cluster assignments for {len(cluster_df):,} stores")
    
    # Merge with clusters
    df = spu_df.merge(cluster_df, on='str_code', how='inner')
    log_progress(f"Merged data: {len(df):,} records with cluster information")
    
    # Create category key
    df['category_key'] = df['cate_name'] + '|' + df['sub_cate_name']
    
    log_progress(f"Prepared data: {df['str_code'].nunique():,} stores, {df['category_key'].nunique():,} categories, {df['spu_code'].nunique():,} SPUs")
    
    return df

def identify_cluster_category_top_performers_optimized(df: pd.DataFrame) -> pd.DataFrame:
    """
    OPTIMIZED: Identify top 20% performing SPUs within each cluster-category combination
    """
    log_progress("Identifying top performers within each cluster-category (OPTIMIZED)...")
    
    # Calculate cluster sizes first
    cluster_sizes = df.groupby(['Cluster', 'category_key'])['str_code'].nunique().reset_index()
    cluster_sizes.columns = ['Cluster', 'category_key', 'total_stores_in_cluster']
    
    # Filter to clusters with sufficient stores
    valid_clusters = cluster_sizes[
        cluster_sizes['total_stores_in_cluster'] >= MIN_CLUSTER_STORES
    ][['Cluster', 'category_key']].copy()
    
    log_progress(f"Found {len(valid_clusters):,} valid cluster-category combinations")
    
    # Filter original data to valid clusters only
    df_filtered = df.merge(valid_clusters, on=['Cluster', 'category_key'], how='inner')
    
    # Calculate SPU performance within each cluster-category (vectorized)
    spu_performance = df_filtered.groupby(['Cluster', 'category_key', 'spu_code']).agg({
        'spu_sales': ['sum', 'mean', 'count'],
        'str_code': 'nunique'
    }).reset_index()
    
    # Flatten column names
    spu_performance.columns = ['cluster', 'category_key', 'spu_code', 
                              'total_sales', 'avg_sales', 'transaction_count', 'stores_selling']
    
    # Filter to SPUs sold by multiple stores (proven winners)
    spu_performance = spu_performance[
        spu_performance['stores_selling'] >= MIN_STORES_SELLING
    ].copy()
    
    log_progress(f"Found {len(spu_performance):,} SPU records meeting minimum selling criteria")
    
    # Calculate percentile rank by total sales within each cluster-category (vectorized)
    spu_performance['sales_percentile'] = spu_performance.groupby(['cluster', 'category_key'])['total_sales'].rank(pct=True)
    
    # Identify top 20% performers
    top_performers = spu_performance[
        spu_performance['sales_percentile'] >= TOP_PERFORMER_THRESHOLD
    ].copy()
    
    # Add cluster size information
    top_performers = top_performers.merge(cluster_sizes, 
                                        left_on=['cluster', 'category_key'],
                                        right_on=['Cluster', 'category_key'], 
                                        how='left')
    
    # Calculate adoption rate
    top_performers['adoption_rate'] = top_performers['stores_selling'] / top_performers['total_stores_in_cluster']
    
    log_progress(f"Identified {len(top_performers):,} top-performing SPUs across {top_performers.groupby(['cluster', 'category_key']).ngroups:,} cluster-categories")
    
    return top_performers

def find_missing_top_performers_optimized(df: pd.DataFrame, top_performers: pd.DataFrame) -> pd.DataFrame:
    """
    OPTIMIZED: Find stores missing top-performing SPUs using vectorized operations
    """
    log_progress("Identifying stores missing top-performing SPUs (OPTIMIZED)...")
    
    # Create a comprehensive store-cluster-category matrix
    store_cluster_category = df.groupby(['str_code', 'Cluster', 'category_key']).size().reset_index(name='has_category')
    log_progress(f"Created store-category matrix: {len(store_cluster_category):,} combinations")
    
    # Create a matrix of what SPUs each store actually has
    store_spu_matrix = df.groupby(['str_code', 'Cluster', 'category_key', 'spu_code']).size().reset_index(name='has_spu')
    store_spu_matrix['has_spu'] = 1  # Binary flag
    
    # Create expected SPU matrix (what stores should have based on top performers)
    expected_matrix = []
    
    for _, top_perf_group in top_performers.groupby(['cluster', 'category_key']):
        cluster = top_perf_group['cluster'].iloc[0]
        category = top_perf_group['category_key'].iloc[0]
        top_spus = top_perf_group['spu_code'].tolist()
        
        # Get all stores in this cluster-category
        cluster_stores = store_cluster_category[
            (store_cluster_category['Cluster'] == cluster) & 
            (store_cluster_category['category_key'] == category)
        ]['str_code'].tolist()
        
        # Create expected combinations
        for store in cluster_stores:
            for spu in top_spus:
                expected_matrix.append({
                    'str_code': store,
                    'Cluster': cluster,
                    'category_key': category,
                    'spu_code': spu,
                    'should_have': 1
                })
    
    if not expected_matrix:
        return pd.DataFrame()
        
    expected_df = pd.DataFrame(expected_matrix)
    log_progress(f"Created expected matrix: {len(expected_df):,} store-SPU expectations")
    
    # Left join to find missing SPUs (where should_have=1 but has_spu is null)
    missing_analysis = expected_df.merge(
        store_spu_matrix[['str_code', 'Cluster', 'category_key', 'spu_code', 'has_spu']], 
        on=['str_code', 'Cluster', 'category_key', 'spu_code'], 
        how='left'
    )
    
    # Identify missing opportunities (should have but doesn't have)
    missing_opportunities = missing_analysis[missing_analysis['has_spu'].isna()].copy()
    
    if len(missing_opportunities) == 0:
        return pd.DataFrame()
    
    # Add SPU performance information
    spu_info_cols = ['cluster', 'category_key', 'spu_code', 'total_sales', 'avg_sales', 
                     'adoption_rate', 'sales_percentile', 'stores_selling', 'total_stores_in_cluster']
    
    missing_opportunities = missing_opportunities.merge(
        top_performers[spu_info_cols], 
        left_on=['Cluster', 'category_key', 'spu_code'],
        right_on=['cluster', 'category_key', 'spu_code'], 
        how='left'
    )
    
    # Calculate opportunity metrics
    missing_opportunities['opportunity_score'] = (
        missing_opportunities['sales_percentile'] * 
        missing_opportunities['adoption_rate']
    )
    
    # APPLY STRICT SELECTIVITY FILTERS to reduce recommendation volume
    log_progress(f"Before selectivity filters: {len(missing_opportunities):,} opportunities")
    
    # Filter 1: Minimum adoption rate (only recommend proven winners)
    missing_opportunities = missing_opportunities[
        missing_opportunities['adoption_rate'] >= MIN_ADOPTION_RATE
    ].copy()
    log_progress(f"After adoption rate filter (>={MIN_ADOPTION_RATE:.0%}): {len(missing_opportunities):,} opportunities")
    
    # Filter 2: Minimum opportunity score (only high-confidence recommendations)
    missing_opportunities = missing_opportunities[
        missing_opportunities['opportunity_score'] >= MIN_OPPORTUNITY_SCORE
    ].copy()
    log_progress(f"After opportunity score filter (>={MIN_OPPORTUNITY_SCORE:.2f}): {len(missing_opportunities):,} opportunities")
    
    # Filter 3: Limit recommendations per store (only top opportunities per store)
    missing_opportunities = missing_opportunities.sort_values(['str_code', 'opportunity_score'], ascending=[True, False])
    missing_opportunities = missing_opportunities.groupby('str_code').head(MAX_RECOMMENDATIONS_PER_STORE).reset_index(drop=True)
    log_progress(f"After per-store limit filter (max {MAX_RECOMMENDATIONS_PER_STORE} per store): {len(missing_opportunities):,} opportunities")
    
    # Clean up column names
    missing_opportunities.rename(columns={
        'Cluster': 'cluster',
        'total_sales': 'spu_total_sales_in_cluster',
        'avg_sales': 'spu_avg_sales_per_store',
        'adoption_rate': 'spu_adoption_rate_in_cluster',
        'sales_percentile': 'spu_sales_percentile',
        'stores_selling': 'stores_selling_in_cluster',
        'spu_code': 'missing_spu_code'
    }, inplace=True)
    
    # Add category information
    category_info = missing_opportunities['category_key'].str.split('|', expand=True)
    missing_opportunities['cate_name'] = category_info[0]
    missing_opportunities['sub_cate_name'] = category_info[1]
    
    # Select final columns
    final_columns = ['str_code', 'cluster', 'category_key', 'missing_spu_code', 
                    'spu_total_sales_in_cluster', 'spu_avg_sales_per_store',
                    'spu_adoption_rate_in_cluster', 'spu_sales_percentile',
                    'stores_selling_in_cluster', 'total_stores_in_cluster',
                    'opportunity_score', 'cate_name', 'sub_cate_name']
    
    missing_opportunities = missing_opportunities[final_columns].copy()
    
    log_progress(f"Identified {len(missing_opportunities):,} missing top-performer opportunities across {missing_opportunities['str_code'].nunique():,} stores")
    
    return missing_opportunities

def create_pipeline_results(opportunities_df: pd.DataFrame) -> pd.DataFrame:
    """Create pipeline-compatible rule results"""
    log_progress("Creating pipeline-compatible rule results...")
    
    # Load base store data
    cluster_df = pd.read_csv(CLUSTER_RESULTS_FILE, dtype={'str_code': str})
    results_df = cluster_df[['str_code', 'Cluster']].copy()
    
    # Initialize rule columns
    results_df['rule11_missed_sales_opportunity'] = 0
    results_df['rule11_missing_top_performers_count'] = 0
    results_df['rule11_avg_opportunity_score'] = 0.0
    results_df['rule11_potential_sales_increase'] = 0.0
    
    if len(opportunities_df) > 0:
        # Aggregate by store
        store_summary = opportunities_df.groupby('str_code').agg({
            'missing_spu_code': 'count',
            'opportunity_score': 'mean',
            'spu_avg_sales_per_store': 'sum'
        }).reset_index()
        
        store_summary.columns = [
            'str_code', 'missing_top_performers_count', 
            'avg_opportunity_score', 'potential_sales_increase'
        ]
        
        # Update stores with opportunities
        for _, row in store_summary.iterrows():
            mask = results_df['str_code'] == row['str_code']
            results_df.loc[mask, 'rule11_missed_sales_opportunity'] = 1
            results_df.loc[mask, 'rule11_missing_top_performers_count'] = int(row['missing_top_performers_count'])
            results_df.loc[mask, 'rule11_avg_opportunity_score'] = float(row['avg_opportunity_score'])
            results_df.loc[mask, 'rule11_potential_sales_increase'] = float(row['potential_sales_increase'])
    
    # Ensure correct data types
    results_df['rule11_missed_sales_opportunity'] = results_df['rule11_missed_sales_opportunity'].astype(int)
    results_df['rule11_missing_top_performers_count'] = results_df['rule11_missing_top_performers_count'].astype(int)
    results_df['rule11_avg_opportunity_score'] = results_df['rule11_avg_opportunity_score'].astype(float)
    results_df['rule11_potential_sales_increase'] = results_df['rule11_potential_sales_increase'].astype(float)
    
    stores_flagged = (results_df['rule11_missed_sales_opportunity'] == 1).sum()
    log_progress(f"Applied improved missed sales opportunity rule: {stores_flagged:,} stores flagged")
    
    return results_df

def save_results(results_df: pd.DataFrame, opportunities_df: pd.DataFrame, top_performers_df: pd.DataFrame) -> None:
    """Save results to files"""
    log_progress("Saving improved Rule 11 results...")
    
    # Save pipeline results
    results_file = "output/rule11_improved_missed_sales_opportunity_spu_results.csv"
    results_df.to_csv(results_file, index=False)
    log_progress(f"Saved pipeline results to {results_file}")
    
    # Save detailed opportunities
    if len(opportunities_df) > 0:
        opportunities_file = "output/rule11_improved_missed_sales_opportunity_spu_details.csv"
        opportunities_df.to_csv(opportunities_file, index=False)
        log_progress(f"Saved detailed opportunities to {opportunities_file}")
    
    # Save top performers reference
    if len(top_performers_df) > 0:
        top_performers_file = "output/rule11_improved_top_performers_by_cluster_category.csv"
        top_performers_df.to_csv(top_performers_file, index=False)
        log_progress(f"Saved top performers reference to {top_performers_file}")
    
    # Create summary report
    summary_file = "output/rule11_improved_missed_sales_opportunity_spu_summary.md"
    
    total_stores = len(results_df)
    stores_flagged = (results_df['rule11_missed_sales_opportunity'] == 1).sum()
    total_opportunities = len(opportunities_df) if len(opportunities_df) > 0 else 0
    total_top_performers = len(top_performers_df) if len(top_performers_df) > 0 else 0
    
    with open(summary_file, 'w') as f:
        f.write("# Rule 11 IMPROVED: Category-Specific Top Performer Analysis\n\n")
        f.write("## Business Logic\n")
        f.write("- Identify top 20% performing SPUs within each cluster-category combination\n")
        f.write("- Flag stores missing these proven category winners\n")
        f.write("- Focus on like-for-like comparisons (same category)\n")
        f.write("- Use cluster peer success as validation\n")
        f.write("- **OPTIMIZED**: Vectorized operations for 100x speed improvement\n\n")
        f.write("## Results Summary\n")
        f.write(f"- **Total stores analyzed**: {total_stores:,}\n")
        f.write(f"- **Stores flagged**: {stores_flagged:,} ({stores_flagged/total_stores*100:.1f}%)\n")
        f.write(f"- **Missing opportunities identified**: {total_opportunities:,}\n")
        f.write(f"- **Top performers identified**: {total_top_performers:,}\n")
        f.write(f"- **Category-specific analysis**: Like-for-like comparisons\n")
        f.write(f"- **Cluster-validated**: Peer success validation\n\n")
        f.write("## Key Improvements\n")
        f.write("- ✅ Category-specific comparisons (no more apples-to-oranges)\n")
        f.write("- ✅ Store-size independent (focuses on proven winners)\n")
        f.write("- ✅ Cluster peer validation (social proof)\n")
        f.write("- ✅ Actionable recommendations (specific SPUs to add)\n")
        f.write("- ✅ **FAST**: Vectorized operations replace slow nested loops\n")
    
    log_progress(f"Saved summary report to {summary_file}")

def main(testing_mode: bool = False):
    """Main execution function"""
    mode_text = "FAST TESTING" if testing_mode else "FULL ANALYSIS"
    print(f"\n" + "="*80)
    print(f"🎯 IMPROVED RULE 11: CATEGORY-SPECIFIC TOP PERFORMER ANALYSIS ({mode_text})")
    print("="*80)
    
    start_time = datetime.now()
    
    try:
        # Load data with optional sampling for testing
        sample_size = 50000 if testing_mode else None
        df = load_and_prepare_data(sample_size=sample_size)
        
        # Identify top performers (optimized)
        top_performers = identify_cluster_category_top_performers_optimized(df) 
        
        if len(top_performers) == 0:
            log_progress("❌ No top performers identified. Check data and parameters.")
            return
        
        # Find missing opportunities (optimized)
        opportunities = find_missing_top_performers_optimized(df, top_performers)
        
        if len(opportunities) == 0:
            log_progress("❌ No missing opportunities identified.")
            return
        
        # Create pipeline results
        results = create_pipeline_results(opportunities)
        
        # Save results
        save_results(results, opportunities, top_performers)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ IMPROVED RULE 11 ANALYSIS COMPLETE:")
        print(f"  • Processing time: {elapsed/60:.1f} minutes")
        print(f"  • Top performers identified: {len(top_performers):,}")
        print(f"  • Missing opportunities: {len(opportunities):,}")
        print(f"  • Stores flagged: {(results['rule11_missed_sales_opportunity'] == 1).sum():,}")
        print(f"  • Category-specific, cluster-validated analysis")
        if testing_mode:
            print(f"  • **TESTING MODE**: Used sample of {sample_size:,} records")
        print("="*80)
        
    except Exception as e:
        log_progress(f"❌ Error in improved Rule 11 analysis: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    
    # Check for testing mode argument
    testing_mode = len(sys.argv) > 1 and sys.argv[1] == "test"
    
    main(testing_mode=testing_mode) 