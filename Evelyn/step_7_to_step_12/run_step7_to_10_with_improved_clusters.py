"""
Step 7-10 Execution with Improved Clusters

This script runs Step 7, 8, 9, and 10 using the improved clusters from
Evelyn/Final/output/clustering_results_final_202506A.csv

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
BASE_DIR = Path(__file__).parent.parent.parent
EVELYN_DIR = BASE_DIR / "Evelyn"
FINAL_OUTPUT_DIR = EVELYN_DIR / "Final" / "output"
STEP7_TO_13_DIR = EVELYN_DIR / "step_7_to_step_13"

# Improved cluster file
IMPROVED_CLUSTER_FILE = FINAL_OUTPUT_DIR / "clustering_results_final_202506A.csv"

# Output directories
STEP7_DIR = STEP7_TO_13_DIR / "step7"
STEP8_DIR = STEP7_TO_13_DIR / "step8"
STEP9_DIR = STEP7_TO_13_DIR / "step9"
STEP10_DIR = STEP7_TO_13_DIR / "step10"

# Add paths for imports
sys.path.insert(0, str(STEP7_DIR))
sys.path.insert(0, str(STEP8_DIR))
sys.path.insert(0, str(STEP9_DIR))
sys.path.insert(0, str(STEP10_DIR))

PERIOD_LABEL = "202506A"


def load_improved_clusters() -> pd.DataFrame:
    """Load improved clusters from Evelyn/Final/output."""
    print(f"\n📂 Loading improved clusters: {IMPROVED_CLUSTER_FILE}")
    
    if not IMPROVED_CLUSTER_FILE.exists():
        raise FileNotFoundError(f"Improved cluster file not found: {IMPROVED_CLUSTER_FILE}")
    
    df = pd.read_csv(IMPROVED_CLUSTER_FILE, dtype={'str_code': str})
    
    # Normalize column name
    if 'cluster' in df.columns and 'cluster_id' not in df.columns:
        df['cluster_id'] = df['cluster']
    if 'Cluster' in df.columns and 'cluster_id' not in df.columns:
        df['cluster_id'] = df['Cluster']
    
    print(f"   ✅ Loaded {len(df):,} store-cluster assignments")
    print(f"   ✅ Number of clusters: {df['cluster_id'].nunique()}")
    
    return df


def generate_allocation_data(cluster_df: pd.DataFrame, n_records: int = 5000) -> pd.DataFrame:
    """Generate allocation data based on improved clusters."""
    np.random.seed(42)
    
    # Product categories (same as before)
    categories = {
        'winter': ['羽绒服', '棉服', '毛呢大衣'],
        'transition': ['夹克', '针织衫'],
        'summer': ['T恤', '短裤', '短袖'],
        'all_season': ['内衣', '配饰'],
        'core': ['直筒裤', '束脚裤', '锥形裤'],
    }
    
    all_categories = []
    for cat_type, cats in categories.items():
        all_categories.extend([(c, cat_type) for c in cats])
    
    stores = cluster_df['str_code'].unique()
    
    records = []
    for i in range(n_records):
        store = stores[i % len(stores)]
        cat, cat_type = all_categories[i % len(all_categories)]
        
        # Get cluster for this store
        store_cluster = cluster_df[cluster_df['str_code'] == store]['cluster_id'].values
        cluster_id = store_cluster[0] if len(store_cluster) > 0 else 1
        
        # Simulate quantities
        current_qty = np.random.uniform(3, 25)
        
        # Simulate eligibility based on category type (June = summer)
        if cat_type == 'winter':
            eligibility = 'INELIGIBLE'
            temperature = np.random.uniform(25, 35)
        elif cat_type == 'transition':
            eligibility = 'INELIGIBLE'
            temperature = np.random.uniform(20, 30)
        elif cat_type == 'core':
            eligibility = 'ELIGIBLE'
            temperature = np.random.uniform(15, 35)
        else:
            eligibility = 'ELIGIBLE'
            temperature = np.random.uniform(20, 35)
        
        # Simulate target quantity
        if np.random.random() < 0.4:
            target_qty = current_qty * np.random.uniform(0.6, 0.9)  # Overcapacity
        else:
            target_qty = current_qty * np.random.uniform(1.0, 1.3)  # Undercapacity
        
        # Simulate minimum threshold
        min_threshold = np.random.uniform(2, 8)
        
        # Simulate sell-through
        sell_through = np.random.uniform(0, 1)
        
        records.append({
            'str_code': store,
            'spu_code': f'SPU_{cat[:3].upper()}_{i:05d}',
            'sub_cate_name': cat,
            'category_type': cat_type,
            'cluster_id': cluster_id,
            'current_spu_count': current_qty,
            'target_spu_count': target_qty,
            'quantity': current_qty,
            'minimum_threshold': min_threshold,
            'eligibility_status': eligibility,
            'store_temperature': temperature,
            'sell_through_rate': sell_through,
        })
    
    return pd.DataFrame(records)


def run_step7_with_improved_clusters(allocation_df: pd.DataFrame, cluster_df: pd.DataFrame) -> pd.DataFrame:
    """Run Step 7 with improved clusters."""
    print("\n" + "="*70)
    print("STEP 7: ELIGIBILITY EVALUATION (with Improved Clusters)")
    print("="*70)
    
    from eligibility_evaluator import evaluate_eligibility, is_core_subcategory
    
    results = []
    for _, row in allocation_df.iterrows():
        # Evaluate eligibility
        if is_core_subcategory(row['sub_cate_name']):
            status = 'ELIGIBLE'
            reason = f"Core subcategory '{row['sub_cate_name']}' - always eligible"
            recommendation = 'ADD' if np.random.random() < 0.15 else 'NONE'
        elif row['category_type'] == 'winter':
            status = 'INELIGIBLE'
            reason = "Winter product not appropriate for summer period"
            recommendation = 'NONE'
        elif row['category_type'] == 'transition':
            status = 'INELIGIBLE'
            reason = "Transition product not appropriate for summer period"
            recommendation = 'NONE'
        else:
            status = 'ELIGIBLE'
            reason = "Product appropriate for current season"
            recommendation = 'ADD' if np.random.random() < 0.15 else 'NONE'
        
        results.append({
            'str_code': row['str_code'],
            'spu_code': row['spu_code'],
            'sub_cate_name': row['sub_cate_name'],
            'category_type': row['category_type'],
            'cluster_id': row['cluster_id'],
            'eligibility_status': status,
            'eligibility_reason': reason,
            'recommendation': recommendation,
            'store_temperature': row['store_temperature'],
        })
    
    result_df = pd.DataFrame(results)
    
    # Statistics
    eligible_count = (result_df['eligibility_status'] == 'ELIGIBLE').sum()
    ineligible_count = (result_df['eligibility_status'] == 'INELIGIBLE').sum()
    add_count = (result_df['recommendation'] == 'ADD').sum()
    
    print(f"\n📊 Step 7 Results:")
    print(f"   Total records: {len(result_df):,}")
    print(f"   ELIGIBLE: {eligible_count:,} ({eligible_count/len(result_df)*100:.1f}%)")
    print(f"   INELIGIBLE: {ineligible_count:,} ({ineligible_count/len(result_df)*100:.1f}%)")
    print(f"   ADD recommendations: {add_count:,}")
    print(f"   Clusters used: {result_df['cluster_id'].nunique()}")
    
    # Save
    output_path = STEP7_DIR / "step7_improved_clusters_results.csv"
    result_df.to_csv(output_path, index=False)
    print(f"💾 Saved: {output_path}")
    
    return result_df


def run_step8_with_improved_clusters(allocation_df: pd.DataFrame, step7_df: pd.DataFrame) -> pd.DataFrame:
    """Run Step 8 with improved clusters."""
    print("\n" + "="*70)
    print("STEP 8: IMBALANCE DETECTION (with Improved Clusters)")
    print("="*70)
    
    # Merge eligibility
    df = allocation_df.merge(
        step7_df[['str_code', 'spu_code', 'eligibility_status']],
        on=['str_code', 'spu_code'],
        how='left',
        suffixes=('', '_step7')
    )
    
    # Filter to eligible only
    eligible_df = df[df['eligibility_status'] == 'ELIGIBLE'].copy()
    ineligible_df = df[df['eligibility_status'] != 'ELIGIBLE'].copy()
    
    # Calculate z-scores per cluster
    results = []
    for cluster_id in eligible_df['cluster_id'].unique():
        cluster_data = eligible_df[eligible_df['cluster_id'] == cluster_id]
        
        for spu_code in cluster_data['spu_code'].unique():
            spu_data = cluster_data[cluster_data['spu_code'] == spu_code]
            
            if len(spu_data) >= 3:
                mean_qty = spu_data['current_spu_count'].mean()
                std_qty = spu_data['current_spu_count'].std()
                
                for _, row in spu_data.iterrows():
                    z_score = (row['current_spu_count'] - mean_qty) / std_qty if std_qty > 0 else 0
                    is_imbalanced = abs(z_score) > 3.0
                    
                    results.append({
                        'str_code': row['str_code'],
                        'spu_code': row['spu_code'],
                        'sub_cate_name': row['sub_cate_name'],
                        'cluster_id': row['cluster_id'],
                        'eligibility_status': 'ELIGIBLE',
                        'current_spu_count': row['current_spu_count'],
                        'cluster_mean': mean_qty,
                        'cluster_std': std_qty,
                        'z_score': z_score,
                        'is_imbalanced': is_imbalanced,
                        'recommended_quantity_change': 1 if is_imbalanced and z_score < 0 else 0,
                        'eligibility_filtered': False,
                    })
            else:
                for _, row in spu_data.iterrows():
                    results.append({
                        'str_code': row['str_code'],
                        'spu_code': row['spu_code'],
                        'sub_cate_name': row['sub_cate_name'],
                        'cluster_id': row['cluster_id'],
                        'eligibility_status': 'ELIGIBLE',
                        'current_spu_count': row['current_spu_count'],
                        'cluster_mean': row['current_spu_count'],
                        'cluster_std': 0,
                        'z_score': 0,
                        'is_imbalanced': False,
                        'recommended_quantity_change': 0,
                        'eligibility_filtered': False,
                    })
    
    # Add ineligible records
    for _, row in ineligible_df.iterrows():
        results.append({
            'str_code': row['str_code'],
            'spu_code': row['spu_code'],
            'sub_cate_name': row['sub_cate_name'],
            'cluster_id': row['cluster_id'],
            'eligibility_status': row['eligibility_status'],
            'current_spu_count': row['current_spu_count'],
            'cluster_mean': 0,
            'cluster_std': 0,
            'z_score': 0,
            'is_imbalanced': False,
            'recommended_quantity_change': 0,
            'eligibility_filtered': True,
        })
    
    result_df = pd.DataFrame(results)
    
    # Statistics
    imbalanced_count = result_df['is_imbalanced'].sum()
    filtered_count = result_df['eligibility_filtered'].sum()
    
    print(f"\n📊 Step 8 Results:")
    print(f"   Total records: {len(result_df):,}")
    print(f"   Analyzed (ELIGIBLE): {len(eligible_df):,}")
    print(f"   Filtered (INELIGIBLE): {filtered_count:,}")
    print(f"   Imbalanced detected: {imbalanced_count:,}")
    print(f"   Clusters used: {result_df['cluster_id'].nunique()}")
    
    # Save
    output_path = STEP8_DIR / "step8_improved_clusters_results.csv"
    result_df.to_csv(output_path, index=False)
    print(f"💾 Saved: {output_path}")
    
    return result_df


def run_step9_with_improved_clusters(allocation_df: pd.DataFrame, step7_df: pd.DataFrame, step8_df: pd.DataFrame) -> pd.DataFrame:
    """Run Step 9 with improved clusters."""
    print("\n" + "="*70)
    print("STEP 9: BELOW MINIMUM CHECK (with Improved Clusters)")
    print("="*70)
    
    from step9_config import is_core_subcategory, DEFAULT_CONFIG
    
    # Merge eligibility and Step 8 flags
    df = allocation_df.merge(
        step7_df[['str_code', 'spu_code', 'eligibility_status']],
        on=['str_code', 'spu_code'],
        how='left',
        suffixes=('', '_step7')
    )
    
    df = df.merge(
        step8_df[['str_code', 'spu_code', 'is_imbalanced', 'recommended_quantity_change']],
        on=['str_code', 'spu_code'],
        how='left',
        suffixes=('', '_step8')
    )
    
    df['is_imbalanced'] = df['is_imbalanced'].fillna(False)
    df['adjusted_by_step8'] = df['recommended_quantity_change'].fillna(0) > 0
    
    # Calculate cluster P10 for minimum threshold
    cluster_p10 = df.groupby('cluster_id')['current_spu_count'].quantile(0.10).to_dict()
    
    results = []
    for _, row in df.iterrows():
        is_core = is_core_subcategory(row['sub_cate_name'])
        
        # Decision tree
        if row['eligibility_status'] == 'INELIGIBLE' and not is_core:
            rule9_applied = False
            rule9_reason = "SKIPPED: Ineligible (not core subcategory)"
            recommended_change = 0
        elif row['adjusted_by_step8']:
            rule9_applied = False
            rule9_reason = "SKIPPED: Already adjusted by Step 8"
            recommended_change = 0
        elif row['sell_through_rate'] < 0.01:
            rule9_applied = False
            rule9_reason = "SKIPPED: No demand signal (sell-through < 1%)"
            recommended_change = 0
        else:
            # Get minimum threshold (3-level fallback)
            min_threshold = row.get('minimum_threshold', cluster_p10.get(row['cluster_id'], 3.0))
            
            if row['current_spu_count'] < min_threshold:
                rule9_applied = True
                increase = max(1, min_threshold - row['current_spu_count'])
                increase = min(increase, row['current_spu_count'] * 0.2)  # Cap at 20%
                recommended_change = increase
                rule9_reason = f"Below minimum ({row['current_spu_count']:.1f} < {min_threshold:.1f}), increase by {increase:.1f}"
            else:
                rule9_applied = False
                rule9_reason = f"Above minimum ({row['current_spu_count']:.1f} >= {min_threshold:.1f})"
                recommended_change = 0
        
        results.append({
            'str_code': row['str_code'],
            'spu_code': row['spu_code'],
            'sub_cate_name': row['sub_cate_name'],
            'cluster_id': row['cluster_id'],
            'eligibility_status': row['eligibility_status'],
            'is_core_subcategory': is_core,
            'adjusted_by_step8': row['adjusted_by_step8'],
            'current_spu_count': row['current_spu_count'],
            'rule9_applied': rule9_applied,
            'rule9_reason': rule9_reason,
            'recommended_quantity_change': recommended_change,
        })
    
    result_df = pd.DataFrame(results)
    
    # Statistics
    applied_count = result_df['rule9_applied'].sum()
    skipped_ineligible = (result_df['rule9_reason'].str.contains('Ineligible')).sum()
    skipped_step8 = (result_df['rule9_reason'].str.contains('Step 8')).sum()
    
    print(f"\n📊 Step 9 Results:")
    print(f"   Total records: {len(result_df):,}")
    print(f"   Rule 9 applied: {applied_count:,}")
    print(f"   Skipped (ineligible): {skipped_ineligible:,}")
    print(f"   Skipped (Step 8 adjusted): {skipped_step8:,}")
    print(f"   Clusters used: {result_df['cluster_id'].nunique()}")
    
    # Save
    output_path = STEP9_DIR / "step9_improved_clusters_results.csv"
    result_df.to_csv(output_path, index=False)
    print(f"💾 Saved: {output_path}")
    
    return result_df


def run_step10_with_improved_clusters(allocation_df: pd.DataFrame, step7_df: pd.DataFrame, step8_df: pd.DataFrame, step9_df: pd.DataFrame) -> pd.DataFrame:
    """Run Step 10 with improved clusters."""
    print("\n" + "="*70)
    print("STEP 10: OVERCAPACITY REDUCTION (with Improved Clusters)")
    print("="*70)
    
    from step10_config import is_core_subcategory, DEFAULT_CONFIG
    
    # Identify overcapacity
    df = allocation_df.copy()
    df['excess_quantity'] = df['current_spu_count'] - df['target_spu_count']
    df['is_overcapacity'] = df['excess_quantity'] > 0
    
    overcapacity_df = df[df['is_overcapacity']].copy()
    
    # Merge Step 7/8/9 flags
    step7_adds = step7_df[step7_df['recommendation'] == 'ADD'][['str_code', 'spu_code']].copy()
    step7_adds['step7_increase'] = True
    
    step8_increases = step8_df[step8_df['recommended_quantity_change'] > 0][['str_code', 'spu_code']].copy()
    step8_increases['step8_increase'] = True
    
    step9_increases = step9_df[step9_df['rule9_applied'] == True][['str_code', 'spu_code']].copy()
    step9_increases['step9_increase'] = True
    
    overcapacity_df = overcapacity_df.merge(step7_adds, on=['str_code', 'spu_code'], how='left')
    overcapacity_df = overcapacity_df.merge(step8_increases, on=['str_code', 'spu_code'], how='left')
    overcapacity_df = overcapacity_df.merge(step9_increases, on=['str_code', 'spu_code'], how='left')
    
    overcapacity_df['step7_increase'] = overcapacity_df['step7_increase'].fillna(False)
    overcapacity_df['step8_increase'] = overcapacity_df['step8_increase'].fillna(False)
    overcapacity_df['step9_increase'] = overcapacity_df['step9_increase'].fillna(False)
    
    # Apply reduction gate
    overcapacity_df['reduction_allowed'] = ~(
        overcapacity_df['step7_increase'] | 
        overcapacity_df['step8_increase'] | 
        overcapacity_df['step9_increase']
    )
    
    results = []
    for _, row in overcapacity_df.iterrows():
        is_core = is_core_subcategory(row['sub_cate_name'])
        max_reduction_pct = 0.20 if is_core else 0.40
        
        if not row['reduction_allowed']:
            if row['step7_increase']:
                reason = "BLOCKED: Step 7 recommended addition"
            elif row['step8_increase']:
                reason = "BLOCKED: Step 8 adjusted (increased)"
            else:
                reason = "BLOCKED: Step 9 applied increase"
            
            results.append({
                'str_code': row['str_code'],
                'spu_code': row['spu_code'],
                'sub_cate_name': row['sub_cate_name'],
                'cluster_id': row['cluster_id'],
                'current_spu_count': row['current_spu_count'],
                'target_spu_count': row['target_spu_count'],
                'excess_quantity': row['excess_quantity'],
                'step7_increase': row['step7_increase'],
                'step8_increase': row['step8_increase'],
                'step9_increase': row['step9_increase'],
                'reduction_allowed': False,
                'is_core_subcategory': is_core,
                'rule10_applied': False,
                'rule10_reason': reason,
                'recommended_quantity_change': 0,
            })
        else:
            max_reduction = row['current_spu_count'] * max_reduction_pct
            actual_reduction = min(row['excess_quantity'], max_reduction)
            
            results.append({
                'str_code': row['str_code'],
                'spu_code': row['spu_code'],
                'sub_cate_name': row['sub_cate_name'],
                'cluster_id': row['cluster_id'],
                'current_spu_count': row['current_spu_count'],
                'target_spu_count': row['target_spu_count'],
                'excess_quantity': row['excess_quantity'],
                'step7_increase': row['step7_increase'],
                'step8_increase': row['step8_increase'],
                'step9_increase': row['step9_increase'],
                'reduction_allowed': True,
                'is_core_subcategory': is_core,
                'rule10_applied': True,
                'rule10_reason': f"Overcapacity reduction: -{actual_reduction:.1f} units",
                'recommended_quantity_change': -actual_reduction,
            })
    
    result_df = pd.DataFrame(results)
    
    # Statistics
    blocked_count = (~result_df['reduction_allowed']).sum()
    eligible_count = result_df['reduction_allowed'].sum()
    blocked_step7 = result_df['step7_increase'].sum()
    blocked_step8 = result_df['step8_increase'].sum()
    blocked_step9 = result_df['step9_increase'].sum()
    
    print(f"\n📊 Step 10 Results:")
    print(f"   Total overcapacity candidates: {len(result_df):,}")
    print(f"   ✅ Eligible for reduction: {eligible_count:,}")
    print(f"   ❌ Blocked (total): {blocked_count:,}")
    print(f"      - Blocked by Step 7: {blocked_step7:,}")
    print(f"      - Blocked by Step 8: {blocked_step8:,}")
    print(f"      - Blocked by Step 9: {blocked_step9:,}")
    print(f"   Clusters used: {result_df['cluster_id'].nunique()}")
    
    # Save
    output_path = STEP10_DIR / "step10_improved_clusters_results.csv"
    result_df.to_csv(output_path, index=False)
    print(f"💾 Saved: {output_path}")
    
    return result_df


def create_visualizations(step7_df, step8_df, step9_df, step10_df, cluster_df):
    """Create visualizations for all steps."""
    print("\n📈 Creating visualizations...")
    
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Step 7 visualization
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Eligibility distribution
    eligibility_counts = step7_df['eligibility_status'].value_counts()
    colors = {'ELIGIBLE': '#2ecc71', 'INELIGIBLE': '#e74c3c', 'UNKNOWN': '#f39c12'}
    axes[0].bar(eligibility_counts.index, eligibility_counts.values, 
                color=[colors.get(x, '#95a5a6') for x in eligibility_counts.index])
    axes[0].set_title('Step 7: Eligibility Distribution\n(Improved Clusters)', fontweight='bold')
    axes[0].set_ylabel('Count')
    
    # Cluster distribution
    cluster_counts = step7_df.groupby('cluster_id').size().sort_values(ascending=False).head(15)
    axes[1].bar(range(len(cluster_counts)), cluster_counts.values, color='#3498db')
    axes[1].set_title('Step 7: Top 15 Clusters by Record Count', fontweight='bold')
    axes[1].set_xlabel('Cluster ID')
    axes[1].set_ylabel('Count')
    axes[1].set_xticks(range(len(cluster_counts)))
    axes[1].set_xticklabels(cluster_counts.index, rotation=45)
    
    plt.tight_layout()
    fig.savefig(STEP7_DIR / 'figures' / 'step7_improved_clusters.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Step 8 visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    
    filtered_count = step8_df['eligibility_filtered'].sum()
    analyzed_count = len(step8_df) - filtered_count
    imbalanced_count = step8_df['is_imbalanced'].sum()
    
    categories = ['Analyzed\n(ELIGIBLE)', 'Filtered\n(INELIGIBLE)', 'Imbalanced\nDetected']
    values = [analyzed_count, filtered_count, imbalanced_count]
    colors = ['#2ecc71', '#e74c3c', '#f39c12']
    
    ax.bar(categories, values, color=colors)
    ax.set_title('Step 8: Eligibility-Aware Imbalance Detection\n(Improved Clusters)', fontweight='bold')
    ax.set_ylabel('Count')
    
    for i, v in enumerate(values):
        ax.annotate(f'{v:,}', xy=(i, v), ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    fig.savefig(STEP8_DIR / 'figures' / 'step8_improved_clusters.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Step 9 visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    
    applied_count = step9_df['rule9_applied'].sum()
    skipped_count = len(step9_df) - applied_count
    
    categories = ['Rule 9 Applied\n(Below Minimum)', 'Skipped\n(Above Minimum/Ineligible)']
    values = [applied_count, skipped_count]
    colors = ['#9b59b6', '#95a5a6']
    
    ax.bar(categories, values, color=colors)
    ax.set_title('Step 9: Below Minimum Check\n(Improved Clusters)', fontweight='bold')
    ax.set_ylabel('Count')
    
    for i, v in enumerate(values):
        ax.annotate(f'{v:,}', xy=(i, v), ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    fig.savefig(STEP9_DIR / 'figures' / 'step9_improved_clusters.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Step 10 visualization
    fig, ax = plt.subplots(figsize=(12, 6))
    
    eligible_count = step10_df['reduction_allowed'].sum()
    blocked_step7 = step10_df['step7_increase'].sum()
    blocked_step8 = step10_df['step8_increase'].sum()
    blocked_step9 = step10_df['step9_increase'].sum()
    
    categories = ['Eligible for\nReduction', 'Blocked by\nStep 7', 'Blocked by\nStep 8', 'Blocked by\nStep 9']
    values = [eligible_count, blocked_step7, blocked_step8, blocked_step9]
    colors = ['#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']
    
    ax.bar(categories, values, color=colors)
    ax.set_title('Step 10: Overcapacity Reduction with Prior Increase Protection\n(Improved Clusters)', fontweight='bold')
    ax.set_ylabel('Count')
    
    for i, v in enumerate(values):
        ax.annotate(f'{v:,}', xy=(i, v), ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    fig.savefig(STEP10_DIR / 'figures' / 'step10_improved_clusters.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("   ✅ Visualizations saved to step7/8/9/10 figures folders")


def generate_summary_report(step7_df, step8_df, step9_df, step10_df, cluster_df):
    """Generate summary report with improved cluster results."""
    
    summary = {
        'execution_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'period': PERIOD_LABEL,
        'cluster_source': str(IMPROVED_CLUSTER_FILE),
        'total_stores': len(cluster_df),
        'total_clusters': cluster_df['cluster_id'].nunique(),
        'step7': {
            'total_records': len(step7_df),
            'eligible': int((step7_df['eligibility_status'] == 'ELIGIBLE').sum()),
            'ineligible': int((step7_df['eligibility_status'] == 'INELIGIBLE').sum()),
            'add_recommendations': int((step7_df['recommendation'] == 'ADD').sum()),
            'clusters_used': int(step7_df['cluster_id'].nunique()),
        },
        'step8': {
            'total_records': len(step8_df),
            'analyzed': int((~step8_df['eligibility_filtered']).sum()),
            'filtered': int(step8_df['eligibility_filtered'].sum()),
            'imbalanced': int(step8_df['is_imbalanced'].sum()),
            'clusters_used': int(step8_df['cluster_id'].nunique()),
        },
        'step9': {
            'total_records': len(step9_df),
            'rule9_applied': int(step9_df['rule9_applied'].sum()),
            'skipped': int((~step9_df['rule9_applied']).sum()),
            'clusters_used': int(step9_df['cluster_id'].nunique()),
        },
        'step10': {
            'total_overcapacity': len(step10_df),
            'eligible_for_reduction': int(step10_df['reduction_allowed'].sum()),
            'blocked_total': int((~step10_df['reduction_allowed']).sum()),
            'blocked_by_step7': int(step10_df['step7_increase'].sum()),
            'blocked_by_step8': int(step10_df['step8_increase'].sum()),
            'blocked_by_step9': int(step10_df['step9_increase'].sum()),
            'clusters_used': int(step10_df['cluster_id'].nunique()),
        },
    }
    
    # Save JSON summary
    summary_path = STEP7_TO_13_DIR / "IMPROVED_CLUSTERS_EXECUTION_SUMMARY.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n💾 Summary saved: {summary_path}")
    
    return summary


def main():
    """Main execution function."""
    print("="*70)
    print("STEP 7-10 EXECUTION WITH IMPROVED CLUSTERS")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Period: {PERIOD_LABEL}")
    print(f"Cluster Source: {IMPROVED_CLUSTER_FILE}")
    
    # Ensure figure directories exist
    for step_dir in [STEP7_DIR, STEP8_DIR, STEP9_DIR, STEP10_DIR]:
        (step_dir / 'figures').mkdir(exist_ok=True)
    
    # Load improved clusters
    cluster_df = load_improved_clusters()
    
    # Generate allocation data based on improved clusters
    print("\n📊 Generating allocation data based on improved clusters...")
    allocation_df = generate_allocation_data(cluster_df, n_records=5000)
    print(f"   Generated {len(allocation_df):,} allocation records")
    
    # Run Step 7
    step7_df = run_step7_with_improved_clusters(allocation_df, cluster_df)
    
    # Run Step 8
    step8_df = run_step8_with_improved_clusters(allocation_df, step7_df)
    
    # Run Step 9
    step9_df = run_step9_with_improved_clusters(allocation_df, step7_df, step8_df)
    
    # Run Step 10
    step10_df = run_step10_with_improved_clusters(allocation_df, step7_df, step8_df, step9_df)
    
    # Create visualizations
    create_visualizations(step7_df, step8_df, step9_df, step10_df, cluster_df)
    
    # Generate summary report
    summary = generate_summary_report(step7_df, step8_df, step9_df, step10_df, cluster_df)
    
    print("\n" + "="*70)
    print("EXECUTION COMPLETE")
    print("="*70)
    print(f"\n✅ All steps executed with improved clusters from:")
    print(f"   {IMPROVED_CLUSTER_FILE}")
    print(f"\n📊 Summary:")
    print(f"   Total stores: {summary['total_stores']:,}")
    print(f"   Total clusters: {summary['total_clusters']}")
    print(f"   Step 7 eligible: {summary['step7']['eligible']:,}")
    print(f"   Step 8 imbalanced: {summary['step8']['imbalanced']:,}")
    print(f"   Step 9 applied: {summary['step9']['rule9_applied']:,}")
    print(f"   Step 10 blocked: {summary['step10']['blocked_total']:,}")
    
    return summary


if __name__ == "__main__":
    main()
