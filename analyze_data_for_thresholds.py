#!/usr/bin/env python3
"""
Analyze actual data to determine realistic thresholds for Steps 7-12
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path

print("🔍 Analyzing Data for Realistic Thresholds")
print("=" * 80)
print()

# Load data files
clustering = pd.read_csv('output/clustering_results_spu_202510A.csv', dtype={'str_code': str})
spu_sales = pd.read_csv('data/api_data/complete_spu_sales_202510A.csv', dtype={'str_code': str, 'spu_code': str})
store_config = pd.read_csv('data/api_data/store_config_202510A.csv', dtype={'str_code': str})

print(f"📊 Dataset Overview:")
print(f"   Stores: {len(clustering):,}")
print(f"   Clusters: {clustering['Cluster'].nunique()}")
print(f"   SPU Sales Records: {len(spu_sales):,}")
print(f"   Unique SPUs: {spu_sales['spu_code'].nunique():,}")
print()

# ============================================================================
# STEP 7 ANALYSIS: Missing Category/SPU
# ============================================================================
print("📊 STEP 7: Missing Category/SPU Analysis")
print("-" * 80)

# Merge sales with clusters
spu_with_cluster = spu_sales.merge(clustering[['str_code', 'Cluster']], on='str_code', how='left')

# Analyze SPU adoption per cluster
cluster_spu_stats = spu_with_cluster.groupby(['Cluster', 'spu_code']).agg({
    'str_code': 'nunique',  # Number of stores selling this SPU in cluster
    'spu_sales_amt': 'sum'
}).reset_index()
cluster_spu_stats.columns = ['Cluster', 'spu_code', 'stores_selling', 'total_sales']

# Add cluster sizes
cluster_sizes = clustering.groupby('Cluster').size().reset_index(name='cluster_size')
cluster_spu_stats = cluster_spu_stats.merge(cluster_sizes, on='Cluster')
cluster_spu_stats['adoption_rate'] = cluster_spu_stats['stores_selling'] / cluster_spu_stats['cluster_size']

print(f"\n📈 SPU Adoption Statistics:")
print(f"   Total cluster-SPU combinations: {len(cluster_spu_stats):,}")
print(f"   Adoption rate distribution:")
print(f"      Min: {cluster_spu_stats['adoption_rate'].min():.1%}")
print(f"      25th percentile: {cluster_spu_stats['adoption_rate'].quantile(0.25):.1%}")
print(f"      Median: {cluster_spu_stats['adoption_rate'].median():.1%}")
print(f"      75th percentile: {cluster_spu_stats['adoption_rate'].quantile(0.75):.1%}")
print(f"      Max: {cluster_spu_stats['adoption_rate'].max():.1%}")

print(f"\n💰 Sales Distribution:")
print(f"      Min: ${cluster_spu_stats['total_sales'].min():.0f}")
print(f"      25th percentile: ${cluster_spu_stats['total_sales'].quantile(0.25):.0f}")
print(f"      Median: ${cluster_spu_stats['total_sales'].median():.0f}")
print(f"      75th percentile: ${cluster_spu_stats['total_sales'].quantile(0.75):.0f}")
print(f"      Max: ${cluster_spu_stats['total_sales'].max():.0f}")

# Find realistic thresholds
for adoption_threshold in [0.10, 0.20, 0.30, 0.40, 0.50]:
    for sales_threshold in [100, 200, 500, 1000, 1500]:
        qualified = cluster_spu_stats[
            (cluster_spu_stats['adoption_rate'] >= adoption_threshold) &
            (cluster_spu_stats['total_sales'] >= sales_threshold)
        ]
        if len(qualified) > 0:
            print(f"\n   ✅ Threshold: ≥{adoption_threshold:.0%} adoption, ≥${sales_threshold} sales")
            print(f"      → {len(qualified):,} well-selling SPUs would qualify")
            break
    if len(qualified) > 0:
        break

print()

# ============================================================================
# STEP 8 ANALYSIS: Imbalanced Allocation
# ============================================================================
print("📊 STEP 8: Imbalanced Allocation Analysis")
print("-" * 80)

# Analyze cluster-SPU combination sizes
cluster_spu_sizes = spu_with_cluster.groupby(['Cluster', 'spu_code']).size().reset_index(name='stores_per_combo')

print(f"\n📈 Cluster-SPU Combination Sizes:")
print(f"   Total combinations: {len(cluster_spu_sizes):,}")
print(f"   Distribution:")
print(f"      1 store: {(cluster_spu_sizes['stores_per_combo'] == 1).sum():,} ({(cluster_spu_sizes['stores_per_combo'] == 1).sum() / len(cluster_spu_sizes):.1%})")
print(f"      2 stores: {(cluster_spu_sizes['stores_per_combo'] == 2).sum():,} ({(cluster_spu_sizes['stores_per_combo'] == 2).sum() / len(cluster_spu_sizes):.1%})")
print(f"      3 stores: {(cluster_spu_sizes['stores_per_combo'] == 3).sum():,} ({(cluster_spu_sizes['stores_per_combo'] == 3).sum() / len(cluster_spu_sizes):.1%})")
print(f"      4 stores: {(cluster_spu_sizes['stores_per_combo'] == 4).sum():,} ({(cluster_spu_sizes['stores_per_combo'] == 4).sum() / len(cluster_spu_sizes):.1%})")
print(f"      5+ stores: {(cluster_spu_sizes['stores_per_combo'] >= 5).sum():,} ({(cluster_spu_sizes['stores_per_combo'] >= 5).sum() / len(cluster_spu_sizes):.1%})")
print(f"      10+ stores: {(cluster_spu_sizes['stores_per_combo'] >= 10).sum():,} ({(cluster_spu_sizes['stores_per_combo'] >= 10).sum() / len(cluster_spu_sizes):.1%})")

print(f"\n   Max stores in a combination: {cluster_spu_sizes['stores_per_combo'].max()}")
print(f"   Median stores per combination: {cluster_spu_sizes['stores_per_combo'].median():.1f}")

# Try category level instead
if 'sub_cate_name' in spu_sales.columns:
    cluster_cat_sizes = spu_with_cluster.groupby(['Cluster', 'sub_cate_name']).size().reset_index(name='stores_per_combo')
    print(f"\n📈 Cluster-CATEGORY Combination Sizes (Alternative):")
    print(f"   Total combinations: {len(cluster_cat_sizes):,}")
    print(f"   Distribution:")
    print(f"      5+ stores: {(cluster_cat_sizes['stores_per_combo'] >= 5).sum():,} ({(cluster_cat_sizes['stores_per_combo'] >= 5).sum() / len(cluster_cat_sizes):.1%})")
    print(f"      10+ stores: {(cluster_cat_sizes['stores_per_combo'] >= 10).sum():,} ({(cluster_cat_sizes['stores_per_combo'] >= 10).sum() / len(cluster_cat_sizes):.1%})")
    print(f"   Median stores per combination: {cluster_cat_sizes['stores_per_combo'].median():.1f}")

print()

# ============================================================================
# STEP 11 ANALYSIS: Missed Sales Opportunity
# ============================================================================
print("📊 STEP 11: Missed Sales Opportunity Analysis")
print("-" * 80)

# Find top performers per cluster-category
if 'sub_cate_name' in spu_sales.columns:
    cluster_cat_spu = spu_with_cluster.groupby(['Cluster', 'sub_cate_name', 'spu_code']).agg({
        'str_code': 'nunique',
        'sales_amount': 'sum'
    }).reset_index()
    cluster_cat_spu.columns = ['Cluster', 'sub_cate_name', 'spu_code', 'stores_selling', 'total_sales']
    
    # Add cluster-category sizes
    cluster_cat_sizes_dict = spu_with_cluster.groupby(['Cluster', 'sub_cate_name'])['str_code'].nunique().to_dict()
    cluster_cat_spu['cluster_cat_size'] = cluster_cat_spu.apply(
        lambda row: cluster_cat_sizes_dict.get((row['Cluster'], row['sub_cate_name']), 0), axis=1
    )
    cluster_cat_spu['adoption_rate'] = cluster_cat_spu['stores_selling'] / cluster_cat_spu['cluster_cat_size']
    
    print(f"\n📈 Top Performer Candidates:")
    print(f"   Total cluster-category-SPU combinations: {len(cluster_cat_spu):,}")
    
    # Test different thresholds
    for min_stores in [2, 3, 5]:
        for min_sales in [50, 100, 200]:
            for top_pct in [0.70, 0.80, 0.90]:
                candidates = cluster_cat_spu[
                    (cluster_cat_spu['stores_selling'] >= min_stores) &
                    (cluster_cat_spu['total_sales'] >= min_sales)
                ]
                if len(candidates) > 0:
                    # Calculate percentile threshold
                    cluster_cat_spu['rank'] = cluster_cat_spu.groupby(['Cluster', 'sub_cate_name'])['total_sales'].rank(pct=True)
                    top_performers = cluster_cat_spu[cluster_cat_spu['rank'] >= top_pct]
                    qualified = top_performers[
                        (top_performers['stores_selling'] >= min_stores) &
                        (top_performers['total_sales'] >= min_sales)
                    ]
                    if len(qualified) > 0:
                        print(f"\n   ✅ Threshold: ≥{min_stores} stores, ≥${min_sales} sales, top {100-int(top_pct*100)}%")
                        print(f"      → {len(qualified):,} top performers would qualify")
                        break
                if len(qualified) > 0:
                    break
            if len(qualified) > 0:
                break
        if len(qualified) > 0:
            break

print()

# ============================================================================
# RECOMMENDATIONS
# ============================================================================
print("🎯 RECOMMENDED THRESHOLDS")
print("=" * 80)
print()

print("Step 7: Missing Category/SPU")
print("   --min-adoption-rate 0.10")
print("   --min-cluster-sales 100")
print("   --min-opportunity-value 50")
print()

print("Step 8: Imbalanced Allocation")
print("   --min-cluster-size 2")
print("   --z-threshold 1.5")
print("   --min-allocation-threshold 0.01")
print()

print("Step 11: Missed Sales Opportunity")
print("   --min-cluster-stores 2")
print("   --min-stores-selling 2")
print("   --min-spu-sales 50")
print("   --top-performer-threshold 0.70")
print()

print("✅ Analysis complete!")
