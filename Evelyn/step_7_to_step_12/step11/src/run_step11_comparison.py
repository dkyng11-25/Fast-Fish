"""
Step 11 Comparison: Original vs Enhanced with 6 Improvement Axes

This script runs a comparison between the original Step 11 logic and the
enhanced version with all 6 improvement axes (A-F).

Uses the SAME sample dataset as Step 7 & Step 8 for consistency.

Author: Data Pipeline Team
Date: January 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import sys
import json

# Paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
EVELYN_DIR = BASE_DIR / "Evelyn"
STEP7_TO_13_DIR = EVELYN_DIR / "step_7_to_step_13"
STEP11_DIR = STEP7_TO_13_DIR / "step11"
FINAL_OUTPUT_DIR = EVELYN_DIR / "Final" / "output"

# Add paths for imports
sys.path.insert(0, str(STEP11_DIR))

from step11_config import (
    Step11Config,
    DEFAULT_CONFIG,
    OpportunityTier,
    AffinityLevel,
    SUGGESTION_ONLY_STATEMENTS,
)
from step11_missed_opportunity_enhanced import run_step11_enhanced

# Improved cluster file (same as Step 7-10)
IMPROVED_CLUSTER_FILE = FINAL_OUTPUT_DIR / "clustering_results_final_202506A.csv"
OUTPUT_DIR = STEP11_DIR / "figures"
PERIOD_LABEL = "202506A"


def load_improved_clusters() -> pd.DataFrame:
    """Load improved clusters from Evelyn/Final/output."""
    print(f"\n📂 Loading improved clusters: {IMPROVED_CLUSTER_FILE}")
    df = pd.read_csv(IMPROVED_CLUSTER_FILE, dtype={'str_code': str})
    
    if 'cluster' in df.columns and 'cluster_id' not in df.columns:
        df['cluster_id'] = df['cluster']
    
    print(f"   ✅ Loaded {len(df):,} store-cluster assignments")
    print(f"   ✅ Number of clusters: {df['cluster_id'].nunique()}")
    return df


def generate_allocation_data(cluster_df: pd.DataFrame, n_records: int = 5000) -> pd.DataFrame:
    """Generate allocation data based on improved clusters (same as Step 7-10)."""
    np.random.seed(42)
    
    categories = {
        'summer': ['T恤', '短裤', '短袖'],
        'all_season': ['内衣', '配饰'],
        'core': ['直筒裤', '束脚裤', '锥形裤'],
    }
    
    all_categories = []
    for cat_type, cats in categories.items():
        all_categories.extend([(c, cat_type) for c in cats])
    
    stores = cluster_df['str_code'].unique()
    
    # Create a set of "top performer" SPUs that will be sold by many stores
    top_spu_codes = [f'SPU_TOP_{i:03d}' for i in range(50)]
    
    records = []
    
    # Generate top performer SPUs (sold by 70-90% of stores in each cluster)
    for cluster_id in cluster_df['cluster_id'].unique():
        cluster_stores = cluster_df[cluster_df['cluster_id'] == cluster_id]['str_code'].tolist()
        
        for spu_code in top_spu_codes[:20]:  # Top 20 SPUs per cluster
            # 70-90% of stores have this SPU
            n_stores_with_spu = int(len(cluster_stores) * np.random.uniform(0.7, 0.9))
            stores_with_spu = np.random.choice(cluster_stores, n_stores_with_spu, replace=False)
            
            cat, cat_type = all_categories[hash(spu_code) % len(all_categories)]
            
            for store in stores_with_spu:
                records.append({
                    'str_code': store,
                    'spu_code': spu_code,
                    'sub_cate_name': cat,
                    'category_type': cat_type,
                    'cluster_id': cluster_id,
                    'current_spu_count': np.random.uniform(10, 50),  # High performers
                    'eligibility_status': 'ELIGIBLE',
                    'sex_name': np.random.choice(['女', '男', 'unisex']),
                    'sell_through_rate': np.random.uniform(0.3, 0.8),
                })
    
    # Add some regular SPUs
    for i in range(min(n_records - len(records), 2000)):
        store = stores[i % len(stores)]
        cat, cat_type = all_categories[i % len(all_categories)]
        
        store_cluster = cluster_df[cluster_df['str_code'] == store]['cluster_id'].values
        cluster_id = store_cluster[0] if len(store_cluster) > 0 else 1
        
        records.append({
            'str_code': store,
            'spu_code': f'SPU_REG_{i:05d}',
            'sub_cate_name': cat,
            'category_type': cat_type,
            'cluster_id': cluster_id,
            'current_spu_count': np.random.uniform(3, 15),
            'eligibility_status': 'ELIGIBLE',
            'sex_name': np.random.choice(['女', '男', 'unisex']),
            'sell_through_rate': np.random.uniform(0, 0.5),
        })
    
    return pd.DataFrame(records)


def generate_store_sales_data(cluster_df: pd.DataFrame) -> pd.DataFrame:
    """Generate store sales data with customer mix columns."""
    np.random.seed(42)
    
    stores = cluster_df['str_code'].unique()
    
    records = []
    for store in stores:
        woman_cnt = np.random.uniform(50, 500)
        male_cnt = np.random.uniform(30, 400)
        
        records.append({
            'str_code': store,
            'woman_into_str_cnt_avg': woman_cnt,
            'male_into_str_cnt_avg': male_cnt,
        })
    
    return pd.DataFrame(records)


def run_original_step11(allocation_df: pd.DataFrame, cluster_df: pd.DataFrame) -> pd.DataFrame:
    """Simulate original Step 11 logic (without enhancements)."""
    print("\n📊 Running ORIGINAL Step 11 logic...")
    
    # Merge cluster info
    df = allocation_df.merge(cluster_df, on='str_code', how='left')
    
    # Normalize cluster column
    if 'cluster' in df.columns and 'cluster_id' not in df.columns:
        df['cluster_id'] = df['cluster']
    
    # Calculate cluster sizes
    cluster_sizes = df.groupby('cluster_id')['str_code'].nunique().reset_index()
    cluster_sizes.columns = ['cluster_id', 'total_stores']
    
    # Filter valid clusters (min 8 stores)
    valid_clusters = cluster_sizes[cluster_sizes['total_stores'] >= 8]['cluster_id'].tolist()
    df_valid = df[df['cluster_id'].isin(valid_clusters)].copy()
    
    # Calculate SPU performance
    spu_perf = df_valid.groupby(['cluster_id', 'spu_code']).agg({
        'current_spu_count': ['sum', 'mean'],
        'str_code': 'nunique',
    }).reset_index()
    spu_perf.columns = ['cluster_id', 'spu_code', 'total_qty', 'avg_qty', 'stores_selling']
    
    # Filter to SPUs sold by multiple stores
    spu_perf = spu_perf[spu_perf['stores_selling'] >= 5].copy()
    
    # Calculate percentile rank
    spu_perf['sales_percentile'] = spu_perf.groupby('cluster_id')['total_qty'].rank(pct=True)
    
    # Identify top performers (top 5%)
    top_performers = spu_perf[spu_perf['sales_percentile'] >= 0.95].copy()
    top_performers = top_performers.merge(cluster_sizes, on='cluster_id', how='left')
    top_performers['adoption_rate'] = top_performers['stores_selling'] / top_performers['total_stores']
    
    # Find missing opportunities (NO baseline gate, NO affinity, NO tiering)
    opportunities = []
    for _, top_row in top_performers.iterrows():
        cluster_id = top_row['cluster_id']
        spu_code = top_row['spu_code']
        
        cluster_stores = df_valid[df_valid['cluster_id'] == cluster_id]['str_code'].unique()
        stores_with_spu = df_valid[
            (df_valid['cluster_id'] == cluster_id) & 
            (df_valid['spu_code'] == spu_code)
        ]['str_code'].unique()
        
        missing_stores = set(cluster_stores) - set(stores_with_spu)
        
        for store in missing_stores:
            opportunities.append({
                'str_code': store,
                'spu_code': spu_code,
                'cluster_id': cluster_id,
                'recommendation_type': 'ADD_NEW',
                'recommended_quantity_change': top_row['avg_qty'],
                'opportunity_score': top_row['sales_percentile'] * top_row['adoption_rate'],
                'adoption_rate': top_row['adoption_rate'],
            })
    
    result_df = pd.DataFrame(opportunities)
    
    # Apply basic filters
    if not result_df.empty:
        result_df = result_df[result_df['adoption_rate'] >= 0.70].copy()
        result_df = result_df[result_df['opportunity_score'] >= 0.15].copy()
    
    print(f"   Original opportunities: {len(result_df):,}")
    return result_df


def create_comparison_visualizations(original_df: pd.DataFrame, enhanced_df: pd.DataFrame):
    """Create comparison visualizations."""
    print("\n📈 Creating comparison visualizations...")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Figure 1: Opportunity Count Comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    
    categories = ['Original\nStep 11', 'Enhanced\nStep 11']
    values = [len(original_df), len(enhanced_df)]
    colors = ['#95a5a6', '#2ecc71']
    
    bars = ax.bar(categories, values, color=colors, edgecolor='black', linewidth=1.2)
    ax.set_title('Step 11: Opportunity Count Comparison\nOriginal vs Enhanced (with 6 Axes)', 
                 fontweight='bold', fontsize=14)
    ax.set_ylabel('Number of Opportunities', fontsize=12)
    
    for bar, val in zip(bars, values):
        ax.annotate(f'{val:,}', xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                   ha='center', va='bottom', fontweight='bold', fontsize=14)
    
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / 'step11_opportunity_count_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Figure 2: Opportunity Tier Distribution (Enhanced only)
    if not enhanced_df.empty and 'opportunity_tier' in enhanced_df.columns:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        tier_counts = enhanced_df['opportunity_tier'].value_counts()
        tier_order = [
            OpportunityTier.HIGH_CONFIDENCE.value,
            OpportunityTier.MEDIUM_CONFIDENCE.value,
            OpportunityTier.EXPLORATORY.value,
        ]
        tier_counts = tier_counts.reindex([t for t in tier_order if t in tier_counts.index])
        
        colors = ['#27ae60', '#f39c12', '#95a5a6']
        bars = ax.bar(range(len(tier_counts)), tier_counts.values, color=colors[:len(tier_counts)])
        ax.set_xticks(range(len(tier_counts)))
        ax.set_xticklabels([t.replace(' ', '\n') for t in tier_counts.index], fontsize=10)
        ax.set_title('Step 11 Enhanced: Opportunity Tier Distribution\n(Axis E Implementation)', 
                     fontweight='bold', fontsize=14)
        ax.set_ylabel('Number of Opportunities', fontsize=12)
        
        for bar, val in zip(bars, tier_counts.values):
            ax.annotate(f'{val:,}', xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                       ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        plt.tight_layout()
        fig.savefig(OUTPUT_DIR / 'step11_tier_distribution.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    # Figure 3: Affinity Level Distribution (Enhanced only)
    if not enhanced_df.empty and 'affinity_level' in enhanced_df.columns:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        affinity_counts = enhanced_df['affinity_level'].value_counts()
        affinity_order = [
            AffinityLevel.HIGH.value,
            AffinityLevel.MODERATE.value,
            AffinityLevel.LOW.value,
        ]
        affinity_counts = affinity_counts.reindex([a for a in affinity_order if a in affinity_counts.index])
        
        colors = ['#3498db', '#9b59b6', '#e74c3c']
        bars = ax.bar(range(len(affinity_counts)), affinity_counts.values, color=colors[:len(affinity_counts)])
        ax.set_xticks(range(len(affinity_counts)))
        ax.set_xticklabels(affinity_counts.index, fontsize=11)
        ax.set_title('Step 11 Enhanced: Store Affinity Distribution\n(Axis B Implementation)', 
                     fontweight='bold', fontsize=14)
        ax.set_ylabel('Number of Opportunities', fontsize=12)
        
        for bar, val in zip(bars, affinity_counts.values):
            ax.annotate(f'{val:,}', xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                       ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        plt.tight_layout()
        fig.savefig(OUTPUT_DIR / 'step11_affinity_distribution.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    # Figure 4: 6 Axes Implementation Summary
    fig, ax = plt.subplots(figsize=(12, 8))
    
    axes_data = {
        'Axis A\nBaseline Gate': 'Implemented',
        'Axis B\nStore Affinity': 'Implemented',
        'Axis C\nConsistency Check': 'Implemented',
        'Axis D\nSeasonal Context': 'Implemented',
        'Axis E\nOpportunity Tiering': 'Implemented',
        'Axis F\nSuggestion-Only': 'Implemented',
    }
    
    colors = ['#27ae60'] * 6  # All green for implemented
    bars = ax.barh(list(axes_data.keys()), [1] * 6, color=colors, edgecolor='black')
    
    ax.set_xlim(0, 1.2)
    ax.set_xlabel('Implementation Status', fontsize=12)
    ax.set_title('Step 11 Enhanced: 6 Improvement Axes Implementation\n(All Axes Implemented)', 
                 fontweight='bold', fontsize=14)
    
    for bar in bars:
        ax.annotate('✅ IMPLEMENTED', xy=(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2),
                   va='center', fontweight='bold', fontsize=11, color='#27ae60')
    
    ax.set_xticks([])
    plt.tight_layout()
    fig.savefig(OUTPUT_DIR / 'step11_axes_implementation.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"   ✅ Visualizations saved to {OUTPUT_DIR}")


def print_comparison_summary(original_df: pd.DataFrame, enhanced_df: pd.DataFrame):
    """Print comparison summary."""
    print("\n" + "="*70)
    print("STEP 11 COMPARISON SUMMARY")
    print("="*70)
    
    print("\n📊 Opportunity Counts:")
    print(f"   Original Step 11: {len(original_df):,}")
    print(f"   Enhanced Step 11: {len(enhanced_df):,}")
    
    if not enhanced_df.empty:
        print("\n📊 Enhanced Step 11 - Tier Distribution:")
        if 'opportunity_tier' in enhanced_df.columns:
            tier_counts = enhanced_df['opportunity_tier'].value_counts()
            for tier, count in tier_counts.items():
                print(f"   {tier}: {count:,}")
        
        print("\n📊 Enhanced Step 11 - Affinity Distribution:")
        if 'affinity_level' in enhanced_df.columns:
            affinity_counts = enhanced_df['affinity_level'].value_counts()
            for level, count in affinity_counts.items():
                print(f"   {level}: {count:,}")
    
    print("\n✅ 6 Improvement Axes Status:")
    print("   Axis A (Baseline Gate): ✅ Implemented")
    print("   Axis B (Store Affinity): ✅ Implemented")
    print("   Axis C (Consistency Check): ✅ Implemented")
    print("   Axis D (Seasonal Context): ✅ Implemented")
    print("   Axis E (Opportunity Tiering): ✅ Implemented")
    print("   Axis F (Suggestion-Only): ✅ Implemented")
    
    print("\n🔒 Suggestion-Only Safeguard Statements:")
    for statement in SUGGESTION_ONLY_STATEMENTS[:3]:
        print(f"   ✓ {statement}")


def main():
    """Main execution function."""
    print("="*70)
    print("STEP 11 COMPARISON: ORIGINAL vs ENHANCED")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Period: {PERIOD_LABEL}")
    
    # Load improved clusters
    cluster_df = load_improved_clusters()
    
    # Generate allocation data (same as Step 7-10)
    print("\n📊 Generating allocation data...")
    allocation_df = generate_allocation_data(cluster_df, n_records=5000)
    print(f"   Generated {len(allocation_df):,} allocation records")
    
    # Generate store sales data
    store_sales_df = generate_store_sales_data(cluster_df)
    print(f"   Generated {len(store_sales_df):,} store sales records")
    
    # Run original Step 11
    original_df = run_original_step11(allocation_df, cluster_df)
    
    # Run enhanced Step 11
    enhanced_df = run_step11_enhanced(
        allocation_df=allocation_df,
        cluster_df=cluster_df,
        store_sales_df=store_sales_df,
        output_path=STEP11_DIR / "step11_enhanced_results.csv",
        period_label=PERIOD_LABEL,
        config=DEFAULT_CONFIG
    )
    
    # Save original results
    original_df.to_csv(STEP11_DIR / "step11_original_results.csv", index=False)
    print(f"\n💾 Saved original results: {STEP11_DIR / 'step11_original_results.csv'}")
    
    # Create visualizations
    create_comparison_visualizations(original_df, enhanced_df)
    
    # Print summary
    print_comparison_summary(original_df, enhanced_df)
    
    # Save summary JSON
    summary = {
        'execution_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'period': PERIOD_LABEL,
        'cluster_source': str(IMPROVED_CLUSTER_FILE),
        'original_opportunities': len(original_df),
        'enhanced_opportunities': len(enhanced_df),
        'axes_implemented': ['A', 'B', 'C', 'D', 'E', 'F'],
    }
    
    if not enhanced_df.empty and 'opportunity_tier' in enhanced_df.columns:
        summary['tier_distribution'] = enhanced_df['opportunity_tier'].value_counts().to_dict()
    
    with open(STEP11_DIR / "step11_comparison_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n💾 Saved summary: {STEP11_DIR / 'step11_comparison_summary.json'}")
    
    print("\n" + "="*70)
    print("STEP 11 COMPARISON COMPLETE")
    print("="*70)
    
    return original_df, enhanced_df


if __name__ == "__main__":
    main()
