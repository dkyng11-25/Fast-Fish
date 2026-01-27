#!/usr/bin/env python3
"""
Step 8 Comparison Script: Original vs Eligibility-Aware

This script runs both the original Step 8 logic and the enhanced eligibility-aware
version on the 202506A dataset, then generates comparison metrics and visualizations.

Author: Data Pipeline Team
Date: January 2026
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# Add paths for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
STEP7_PATH = PROJECT_ROOT / "Evelyn" / "step7_step13" / "step7"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(STEP7_PATH))

from step8_imbalanced_eligibility_aware import (
    filter_eligible_spus,
    calculate_cluster_zscore,
    Z_SCORE_THRESHOLD,
    MIN_CLUSTER_SIZE,
)
from eligibility_evaluator import EligibilityStatus

# Configuration
PERIOD_LABEL = "202506A"
OUTPUT_DIR = Path(__file__).parent / "figures"
DATA_DIR = PROJECT_ROOT / "output" / "sample_run_202506A"
STEP7_OUTPUT = PROJECT_ROOT / "Evelyn" / "step7_step13" / "step7" / "enhanced_step7_results.csv"


def generate_simulated_allocation_data(
    clustering_file: str,
    spu_sales_file: str,
    n_records: int = 1000
) -> pd.DataFrame:
    """Generate simulated allocation data for comparison."""
    print("📊 Generating simulated allocation data...")
    
    cluster_df = pd.read_csv(clustering_file, dtype={'str_code': str})
    if 'Cluster' in cluster_df.columns and 'cluster_id' not in cluster_df.columns:
        cluster_df['cluster_id'] = cluster_df['Cluster']
    
    spu_df = pd.read_csv(spu_sales_file, dtype={'str_code': str})
    
    np.random.seed(42)
    stores = cluster_df['str_code'].unique()
    
    # Product categories with seasonal characteristics
    categories = [
        {"sub_cate_name": "羽绒服", "spu_prefix": "DOWN_", "base_qty": 15, "season": "winter"},
        {"sub_cate_name": "棉服", "spu_prefix": "PADDED_", "base_qty": 12, "season": "winter"},
        {"sub_cate_name": "毛呢大衣", "spu_prefix": "WOOL_", "base_qty": 10, "season": "winter"},
        {"sub_cate_name": "夹克", "spu_prefix": "JACKET_", "base_qty": 8, "season": "transition"},
        {"sub_cate_name": "针织衫", "spu_prefix": "KNIT_", "base_qty": 10, "season": "transition"},
        {"sub_cate_name": "T恤", "spu_prefix": "TSHIRT_", "base_qty": 25, "season": "summer"},
        {"sub_cate_name": "短裤", "spu_prefix": "SHORTS_", "base_qty": 20, "season": "summer"},
        {"sub_cate_name": "短袖", "spu_prefix": "SHORT_SLV_", "base_qty": 22, "season": "summer"},
        {"sub_cate_name": "内衣", "spu_prefix": "UNDERWEAR_", "base_qty": 15, "season": "all"},
        {"sub_cate_name": "配饰", "spu_prefix": "ACCESSORY_", "base_qty": 18, "season": "all"},
    ]
    
    records = []
    for i in range(n_records):
        store = np.random.choice(stores)
        category = np.random.choice(categories)
        cluster_id = cluster_df[cluster_df['str_code'] == store]['cluster_id'].values
        cluster_id = cluster_id[0] if len(cluster_id) > 0 else np.random.randint(0, 30)
        
        # Simulate quantity with some variance
        base_qty = category['base_qty']
        quantity = max(0, int(np.random.normal(base_qty, base_qty * 0.3)))
        
        # In June, winter items should have low/zero quantity
        if category['season'] == 'winter':
            quantity = np.random.choice([0, 0, 0, 1, 2])  # Mostly 0
        
        records.append({
            'str_code': store,
            'spu_code': f"{category['spu_prefix']}{i:04d}",
            'sub_cate_name': category['sub_cate_name'],
            'cluster_id': cluster_id,
            'quantity': quantity,
            'simulated_season': category['season']
        })
    
    df = pd.DataFrame(records)
    print(f"   Generated {len(df):,} allocation records")
    return df


def run_original_step8(allocation_df: pd.DataFrame) -> pd.DataFrame:
    """Run original Step 8 logic (no eligibility filtering)."""
    print("\n📊 Running ORIGINAL Step 8 (no eligibility filtering)...")
    return calculate_cluster_zscore(allocation_df)


def run_enhanced_step8(
    allocation_df: pd.DataFrame,
    eligibility_df: pd.DataFrame
) -> pd.DataFrame:
    """Run enhanced Step 8 with eligibility filtering."""
    print("\n📊 Running ENHANCED Step 8 (eligibility-aware)...")
    
    eligible_df, excluded_df = filter_eligible_spus(allocation_df, eligibility_df)
    
    if len(eligible_df) > 0:
        result_df = calculate_cluster_zscore(eligible_df)
        result_df['eligibility_filtered'] = False
    else:
        result_df = pd.DataFrame()
    
    if len(excluded_df) > 0:
        excluded_df['z_score'] = np.nan
        excluded_df['is_imbalanced'] = False
        excluded_df['recommended_change'] = 0
        excluded_df['cluster_mean'] = np.nan
        excluded_df['cluster_std'] = np.nan
        excluded_df['cluster_count'] = 0
        excluded_df['eligibility_filtered'] = True
        
        if len(result_df) > 0:
            result_df = pd.concat([result_df, excluded_df], ignore_index=True)
        else:
            result_df = excluded_df
    
    return result_df


def create_comparison_chart(original_df: pd.DataFrame, enhanced_df: pd.DataFrame, output_path: Path):
    """Create comparison chart of imbalance detections."""
    print("\n📈 Creating comparison chart...")
    
    orig_imbalanced = original_df['is_imbalanced'].sum() if 'is_imbalanced' in original_df.columns else 0
    orig_total = len(original_df)
    
    enh_analyzed = len(enhanced_df[enhanced_df['eligibility_filtered'] == False]) if 'eligibility_filtered' in enhanced_df.columns else len(enhanced_df)
    enh_imbalanced = enhanced_df[enhanced_df['eligibility_filtered'] == False]['is_imbalanced'].sum() if 'eligibility_filtered' in enhanced_df.columns else enhanced_df['is_imbalanced'].sum()
    enh_filtered = len(enhanced_df[enhanced_df['eligibility_filtered'] == True]) if 'eligibility_filtered' in enhanced_df.columns else 0
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    categories = ['Original\nStep 8', 'Enhanced\nStep 8']
    x = np.arange(len(categories))
    width = 0.6
    
    # Original: all analyzed
    ax.bar(x[0], orig_total, width, color='#3498db', label='Analyzed')
    ax.bar(x[0], orig_imbalanced, width, color='#e74c3c', label='Imbalanced', alpha=0.8)
    
    # Enhanced: analyzed + filtered
    ax.bar(x[1], enh_analyzed, width, color='#2ecc71', label='Eligible (Analyzed)')
    ax.bar(x[1], enh_filtered, width, bottom=enh_analyzed, color='#95a5a6', label='Filtered (Ineligible)')
    ax.bar(x[1], enh_imbalanced, width, color='#e74c3c', alpha=0.8)
    
    ax.set_ylabel('Number of SPU × Store Combinations', fontsize=12)
    ax.set_title('Step 8 Imbalance Detection: Original vs Eligibility-Aware\n(Period: 202506A - June 2025)', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11)
    ax.legend(loc='upper right')
    
    # Add value labels
    ax.text(x[0], orig_total + 10, f'Total: {orig_total}', ha='center', fontsize=10)
    ax.text(x[0], orig_imbalanced/2, f'Imbal: {orig_imbalanced}', ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    ax.text(x[1], enh_analyzed/2, f'Eligible: {enh_analyzed}', ha='center', va='center', fontsize=9, color='white', fontweight='bold')
    ax.text(x[1], enh_analyzed + enh_filtered/2, f'Filtered: {enh_filtered}', ha='center', va='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path / 'step8_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"   Saved: {output_path / 'step8_comparison.png'}")


def create_false_positive_chart(original_df: pd.DataFrame, output_path: Path):
    """Create chart showing false positive reduction by category."""
    print("\n📊 Creating false positive analysis chart...")
    
    # Group by category and season
    if 'simulated_season' not in original_df.columns:
        print("   Skipping - no season data available")
        return
    
    category_stats = original_df.groupby(['sub_cate_name', 'simulated_season']).agg({
        'is_imbalanced': 'sum',
        'str_code': 'count'
    }).reset_index()
    category_stats.columns = ['Category', 'Season', 'Imbalanced', 'Total']
    category_stats['Imbalance_Rate'] = 100 * category_stats['Imbalanced'] / category_stats['Total']
    
    # Sort by season (winter first - these are false positives in June)
    season_order = {'winter': 0, 'transition': 1, 'summer': 2, 'all': 3}
    category_stats['season_order'] = category_stats['Season'].map(season_order)
    category_stats = category_stats.sort_values('season_order')
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    colors = {'winter': '#e74c3c', 'transition': '#f39c12', 'summer': '#2ecc71', 'all': '#3498db'}
    
    categories = category_stats['Category'].tolist()
    imbalance_rates = category_stats['Imbalance_Rate'].tolist()
    bar_colors = [colors[s] for s in category_stats['Season'].tolist()]
    
    bars = ax.bar(range(len(categories)), imbalance_rates, color=bar_colors)
    
    ax.set_xlabel('Product Category', fontsize=12)
    ax.set_ylabel('Imbalance Detection Rate (%)', fontsize=12)
    ax.set_title('Original Step 8: Imbalance Detection by Category\n(Red = Winter items in June = FALSE POSITIVES)', fontsize=14)
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, rotation=45, ha='right', fontsize=10)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#e74c3c', label='Winter (FALSE POSITIVES in June)'),
        Patch(facecolor='#f39c12', label='Transition'),
        Patch(facecolor='#2ecc71', label='Summer (Valid)'),
        Patch(facecolor='#3498db', label='All-Season (Valid)')
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    plt.savefig(output_path / 'false_positive_analysis.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"   Saved: {output_path / 'false_positive_analysis.png'}")


def main():
    """Run the full comparison analysis."""
    print("\n" + "="*70)
    print("STEP 8 COMPARISON: ORIGINAL VS ELIGIBILITY-AWARE")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Period: {PERIOD_LABEL}")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate simulated allocation data
    clustering_file = DATA_DIR / "step6_clustering_results.csv"
    spu_sales_file = DATA_DIR / "step1_spu_sales.csv"
    
    allocation_df = generate_simulated_allocation_data(
        str(clustering_file),
        str(spu_sales_file),
        n_records=1000
    )
    
    # Create eligibility based on simulated season (for demonstration)
    # In production, this would come from Step 7 enhanced output
    print(f"\n📂 Creating eligibility based on simulated season data...")
    eligibility_df = allocation_df.copy()
    eligibility_df['eligibility_status'] = eligibility_df['simulated_season'].apply(
        lambda s: 'ELIGIBLE' if s in ['summer', 'all'] else 'INELIGIBLE'
    )
    
    eligible_count = (eligibility_df['eligibility_status'] == 'ELIGIBLE').sum()
    ineligible_count = (eligibility_df['eligibility_status'] == 'INELIGIBLE').sum()
    print(f"   ELIGIBLE (summer/all-season): {eligible_count:,}")
    print(f"   INELIGIBLE (winter/transition): {ineligible_count:,}")
    
    # Run original Step 8
    original_results = run_original_step8(allocation_df.copy())
    
    # Run enhanced Step 8
    enhanced_results = run_enhanced_step8(allocation_df.copy(), eligibility_df)
    
    # Save results
    original_results.to_csv(OUTPUT_DIR.parent / "original_step8_results.csv", index=False)
    enhanced_results.to_csv(OUTPUT_DIR.parent / "enhanced_step8_results.csv", index=False)
    
    # Create visualizations
    create_comparison_chart(original_results, enhanced_results, OUTPUT_DIR)
    create_false_positive_chart(original_results, OUTPUT_DIR)
    
    # Print summary
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    
    orig_imbalanced = original_results['is_imbalanced'].sum()
    orig_total = len(original_results)
    
    enh_filtered = len(enhanced_results[enhanced_results['eligibility_filtered'] == True]) if 'eligibility_filtered' in enhanced_results.columns else 0
    enh_analyzed = len(enhanced_results) - enh_filtered
    enh_imbalanced = enhanced_results[enhanced_results['eligibility_filtered'] == False]['is_imbalanced'].sum() if 'eligibility_filtered' in enhanced_results.columns else enhanced_results['is_imbalanced'].sum()
    
    print(f"\nORIGINAL STEP 8:")
    print(f"   Total analyzed: {orig_total:,}")
    print(f"   Imbalanced detected: {orig_imbalanced:,} ({100*orig_imbalanced/orig_total:.1f}%)")
    
    print(f"\nENHANCED STEP 8 (Eligibility-Aware):")
    print(f"   Total records: {len(enhanced_results):,}")
    print(f"   Filtered (ineligible): {enh_filtered:,}")
    print(f"   Analyzed (eligible): {enh_analyzed:,}")
    print(f"   Imbalanced detected: {enh_imbalanced:,} ({100*enh_imbalanced/enh_analyzed:.1f}% of eligible)")
    
    print(f"\nIMPROVEMENT:")
    false_positives_removed = orig_imbalanced - enh_imbalanced
    print(f"   False positives removed: {false_positives_removed:,}")
    print(f"   Reduction in imbalance detections: {100*(orig_imbalanced-enh_imbalanced)/orig_imbalanced:.1f}%")
    
    print("\n" + "="*70)
    print("COMPARISON COMPLETE")
    print(f"Results saved to: {OUTPUT_DIR.parent}")
    print(f"Figures saved to: {OUTPUT_DIR}")
    print("="*70)
    
    return original_results, enhanced_results


if __name__ == "__main__":
    main()
