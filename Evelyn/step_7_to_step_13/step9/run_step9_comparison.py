"""
Step 9 Comparison Script: Original vs Enhanced

This script runs a comparison between the original Step 9 logic and the
enhanced version with customer deviation guardrails.

Uses the same dataset as Step 7 and Step 8 (202506A) for consistency.

Author: Data Pipeline Team
Date: January 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
import sys

# Add parent paths for imports
STEP9_PATH = Path(__file__).parent
STEP7_PATH = STEP9_PATH.parent / "step7"
sys.path.insert(0, str(STEP9_PATH))
sys.path.insert(0, str(STEP7_PATH))

from step9_config import Step9Config, DEFAULT_CONFIG, CORE_SUBCATEGORIES
from step9_minimum_evaluator import BelowMinimumStatus
from step9_below_minimum_enhanced import run_step9_enhanced


def generate_simulated_data(n_records: int = 1000, seed: int = 42) -> pd.DataFrame:
    """
    Generate simulated allocation data for comparison.
    
    Uses same categories and distribution as Step 7/8 for consistency.
    """
    np.random.seed(seed)
    
    # Product categories (same as Step 7/8)
    categories = {
        'winter': ['羽绒服', '棉服', '毛呢大衣'],
        'transition': ['夹克', '针织衫'],
        'summer': ['T恤', '短裤', '短袖'],
        'all_season': ['内衣', '配饰'],
        'core': ['直筒裤', '束脚裤', '锥形裤'],  # Core subcategories
    }
    
    all_categories = []
    for cat_type, cats in categories.items():
        all_categories.extend([(c, cat_type) for c in cats])
    
    # Generate records
    records = []
    for i in range(n_records):
        cat, cat_type = all_categories[i % len(all_categories)]
        cluster_id = np.random.randint(1, 6)
        
        # Simulate quantity (some below minimum)
        if np.random.random() < 0.3:  # 30% below minimum
            quantity = np.random.uniform(0.1, 0.9)
        else:
            quantity = np.random.uniform(1.0, 5.0)
        
        # Simulate eligibility based on category type and period (June = summer)
        if cat_type == 'winter':
            eligibility = 'INELIGIBLE'
        elif cat_type == 'transition':
            eligibility = 'INELIGIBLE'
        elif cat_type == 'core':
            eligibility = 'ELIGIBLE'  # Core always eligible
        else:
            eligibility = 'ELIGIBLE'
        
        # Simulate Step 8 adjustment (10% adjusted)
        adjusted_by_step8 = np.random.random() < 0.1
        
        # Simulate sell-through
        recent_sales = np.random.uniform(0, 10) if np.random.random() > 0.2 else 0
        sell_through_rate = np.random.uniform(0, 0.8) if recent_sales > 0 else 0
        
        records.append({
            'str_code': f'S{1000 + i % 100:05d}',
            'spu_code': f'SPU_{cat[:3].upper()}_{i:04d}',
            'sub_cate_name': cat,
            'category_type': cat_type,
            'cluster_id': cluster_id,
            'quantity': quantity,
            'eligibility_status': eligibility,
            'adjusted_by_step8': adjusted_by_step8,
            'recent_sales_units': recent_sales,
            'sell_through_rate': sell_through_rate,
        })
    
    return pd.DataFrame(records)


def run_original_step9_logic(df: pd.DataFrame, config: Step9Config) -> pd.DataFrame:
    """
    Simulate original Step 9 logic (without decision tree integration).
    
    Original logic:
    - No eligibility check
    - No Step 8 skip
    - Simple below minimum detection
    """
    results = df.copy()
    
    # Original: Just check if below minimum threshold
    results['original_below_minimum'] = results['quantity'] < config.global_minimum_unit_rate
    results['original_recommended_increase'] = np.where(
        results['original_below_minimum'],
        np.maximum(config.global_minimum_unit_rate - results['quantity'], config.min_boost_quantity),
        0
    )
    results['original_recommended_increase'] = np.ceil(results['original_recommended_increase']).astype(int)
    
    return results


def create_comparison_visualizations(
    original_df: pd.DataFrame,
    enhanced_df: pd.DataFrame,
    output_dir: Path
):
    """Create comparison visualizations with clear English labels."""
    
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.rcParams['font.size'] = 11
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12
    
    # Figure 1: Recommendation Count Comparison
    fig, ax = plt.subplots(figsize=(12, 7))
    
    original_count = original_df['original_below_minimum'].sum()
    enhanced_count = len(enhanced_df[enhanced_df['status'] == 'BELOW_MINIMUM'])
    skipped_step8 = len(enhanced_df[enhanced_df['status'] == 'SKIPPED_STEP8'])
    skipped_ineligible = len(enhanced_df[enhanced_df['status'] == 'SKIPPED_INELIGIBLE'])
    skipped_no_demand = len(enhanced_df[enhanced_df['status'] == 'SKIPPED_NO_DEMAND'])
    
    categories = ['Original Step 9', 'Enhanced Step 9']
    below_min = [original_count, enhanced_count]
    skipped = [0, skipped_step8 + skipped_ineligible + skipped_no_demand]
    
    x = np.arange(len(categories))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, below_min, width, label='Below Minimum (Flagged)', color='#e74c3c')
    bars2 = ax.bar(x + width/2, skipped, width, label='Skipped (Decision Tree)', color='#95a5a6')
    
    ax.set_xlabel('Step 9 Version', fontweight='bold')
    ax.set_ylabel('Number of SPU x Store Combinations', fontweight='bold')
    ax.set_title('Step 9: Original vs Enhanced Comparison\n(Period: 202506A - June 2025)', 
                 fontweight='bold', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    
    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{int(height)}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    ha='center', va='bottom', fontweight='bold')
    
    for bar in bars2:
        height = bar.get_height()
        if height > 0:
            ax.annotate(f'{int(height)}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        ha='center', va='bottom', fontweight='bold')
    
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    fig.savefig(output_dir / 'step9_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Figure 2: Decision Tree Breakdown
    fig, ax = plt.subplots(figsize=(10, 8))
    
    status_counts = enhanced_df['status'].value_counts()
    labels = []
    sizes = []
    colors = ['#e74c3c', '#2ecc71', '#3498db', '#f39c12', '#9b59b6']
    
    status_labels = {
        'BELOW_MINIMUM': 'Below Minimum\n(Action Required)',
        'ABOVE_MINIMUM': 'Above Minimum\n(No Action)',
        'SKIPPED_STEP8': 'Skipped\n(Already Adjusted by Step 8)',
        'SKIPPED_INELIGIBLE': 'Skipped\n(Ineligible per Step 7)',
        'SKIPPED_NO_DEMAND': 'Skipped\n(No Demand Signal)',
    }
    
    for status in ['BELOW_MINIMUM', 'ABOVE_MINIMUM', 'SKIPPED_STEP8', 
                   'SKIPPED_INELIGIBLE', 'SKIPPED_NO_DEMAND']:
        if status in status_counts:
            labels.append(status_labels.get(status, status))
            sizes.append(status_counts[status])
    
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%',
        colors=colors[:len(sizes)], startangle=90
    )
    ax.set_title('Step 9 Enhanced: Decision Tree Breakdown\n(Period: 202506A)', 
                 fontweight='bold', fontsize=14)
    
    plt.tight_layout()
    fig.savefig(output_dir / 'step9_decision_tree_breakdown.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Figure 3: Core Subcategory Protection
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Group by category type
    category_analysis = enhanced_df.groupby('category_type').agg({
        'status': lambda x: (x == 'BELOW_MINIMUM').sum(),
        'is_core_subcategory': 'sum',
        'str_code': 'count'
    }).reset_index()
    category_analysis.columns = ['Category Type', 'Below Minimum', 'Core Protected', 'Total']
    
    # Translate category types to English
    cat_labels = {
        'winter': 'Winter Items',
        'transition': 'Transition Items', 
        'summer': 'Summer Items',
        'all_season': 'All-Season Items',
        'core': 'Core Subcategories'
    }
    category_analysis['Category Type'] = category_analysis['Category Type'].map(cat_labels)
    
    x = np.arange(len(category_analysis))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, category_analysis['Total'], width, 
                   label='Total Records', color='#3498db', alpha=0.7)
    bars2 = ax.bar(x + width/2, category_analysis['Below Minimum'], width,
                   label='Below Minimum (Flagged)', color='#e74c3c')
    
    ax.set_xlabel('Product Category', fontweight='bold')
    ax.set_ylabel('Number of Records', fontweight='bold')
    ax.set_title('Step 9: Category-wise Analysis\n(Core Subcategories Always Evaluated)', 
                 fontweight='bold', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(category_analysis['Category Type'], rotation=15, ha='right')
    ax.legend()
    
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    fig.savefig(output_dir / 'step9_category_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Visualizations saved to {output_dir}")


def main():
    """Run Step 9 comparison."""
    print("="*70)
    print("STEP 9 COMPARISON: ORIGINAL VS ENHANCED")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Period: 202506A (June 2025)")
    
    # Setup paths
    output_dir = STEP9_PATH
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(exist_ok=True)
    
    # Generate simulated data (same as Step 7/8)
    print("\n📊 Generating simulated data...")
    allocation_df = generate_simulated_data(n_records=1000, seed=42)
    print(f"   Generated {len(allocation_df):,} records")
    
    # Run original Step 9 logic
    print("\n🔄 Running original Step 9 logic...")
    original_df = run_original_step9_logic(allocation_df, DEFAULT_CONFIG)
    original_flagged = original_df['original_below_minimum'].sum()
    print(f"   Original flagged: {original_flagged:,}")
    
    # Save simulated eligibility and Step 8 data for enhanced run
    eligibility_path = output_dir / "simulated_step7_eligibility.csv"
    step8_path = output_dir / "simulated_step8_results.csv"
    cluster_path = output_dir / "simulated_clusters.csv"
    
    # Create simulated Step 7 eligibility
    eligibility_df = allocation_df[['str_code', 'spu_code', 'eligibility_status']].copy()
    eligibility_df.to_csv(eligibility_path, index=False)
    
    # Create simulated Step 8 results
    step8_df = allocation_df[['str_code', 'spu_code', 'adjusted_by_step8']].copy()
    step8_df['is_imbalanced'] = step8_df['adjusted_by_step8']
    step8_df.to_csv(step8_path, index=False)
    
    # Create simulated clusters
    cluster_df = allocation_df[['str_code', 'cluster_id']].drop_duplicates()
    cluster_df.to_csv(cluster_path, index=False)
    
    # Run enhanced Step 9
    print("\n🚀 Running enhanced Step 9...")
    enhanced_results_path = output_dir / "enhanced_step9_results.csv"
    
    enhanced_df, opportunities_df = run_step9_enhanced(
        allocation_df=allocation_df,
        step7_eligibility_path=str(eligibility_path),
        step8_output_path=str(step8_path),
        cluster_path=str(cluster_path),
        output_path=str(enhanced_results_path),
        period_label="202506A",
        config=DEFAULT_CONFIG
    )
    
    # Save original results
    original_path = output_dir / "original_step9_results.csv"
    original_df.to_csv(original_path, index=False)
    print(f"\n💾 Saved original results: {original_path}")
    
    # Create visualizations
    print("\n📈 Creating visualizations...")
    create_comparison_visualizations(original_df, enhanced_df, figures_dir)
    
    # Print comparison summary
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    
    original_flagged = original_df['original_below_minimum'].sum()
    enhanced_flagged = len(enhanced_df[enhanced_df['status'] == 'BELOW_MINIMUM'])
    
    print(f"\n📊 Below Minimum Detection:")
    print(f"   Original Step 9: {original_flagged:,} flagged")
    print(f"   Enhanced Step 9: {enhanced_flagged:,} flagged")
    print(f"   Reduction: {original_flagged - enhanced_flagged:,} ({100*(original_flagged - enhanced_flagged)/original_flagged:.1f}%)")
    
    print(f"\n📊 Decision Tree Filtering:")
    for status in ['SKIPPED_STEP8', 'SKIPPED_INELIGIBLE', 'SKIPPED_NO_DEMAND']:
        count = len(enhanced_df[enhanced_df['status'] == status])
        print(f"   {status}: {count:,}")
    
    print(f"\n📊 Core Subcategory Protection:")
    core_in_opportunities = opportunities_df['is_core_subcategory'].sum() if len(opportunities_df) > 0 else 0
    print(f"   Core subcategories in opportunities: {core_in_opportunities:,}")
    
    print(f"\n✅ Comparison complete!")
    print(f"   Results saved to: {output_dir}")
    
    return enhanced_df, opportunities_df


if __name__ == "__main__":
    main()
