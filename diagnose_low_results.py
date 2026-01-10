#!/usr/bin/env python3
"""
Diagnose why Steps 7-12 produce so few results
"""
import pandas as pd
import numpy as np

print("🔍 DIAGNOSING LOW RESULTS")
print("=" * 80)
print()

# Load data
clustering = pd.read_csv('output/clustering_results_spu_202510A.csv', dtype={'str_code': str})
spu_sales = pd.read_csv('data/api_data/complete_spu_sales_202510A.csv', dtype={'str_code': str})

print("📊 DATA OVERVIEW")
print("-" * 80)
print(f"Clustering stores: {clustering['str_code'].nunique()}")
print(f"SPU sales stores: {spu_sales['str_code'].nunique()}")
print(f"SPU sales records: {len(spu_sales):,}")
print(f"Unique SPUs: {spu_sales['spu_code'].nunique()}")
print()

# Check overlap
clustering_stores = set(clustering['str_code'].unique())
sales_stores = set(spu_sales['str_code'].unique())
overlap = clustering_stores & sales_stores

print("📊 STORE OVERLAP")
print("-" * 80)
print(f"Stores in clustering: {len(clustering_stores)}")
print(f"Stores in SPU sales: {len(sales_stores)}")
print(f"Overlap: {len(overlap)} ({len(overlap)/len(clustering_stores):.1%} of clustering)")
print(f"Clustering-only stores: {len(clustering_stores - sales_stores)}")
print(f"Sales-only stores: {len(sales_stores - clustering_stores)}")
print()

if len(overlap) < len(clustering_stores):
    print("⚠️  WARNING: Not all clustering stores have sales data!")
    print(f"   Missing stores: {clustering_stores - sales_stores}")
    print()

# Merge and analyze
merged = spu_sales.merge(clustering, on='str_code', how='inner')
print("📊 MERGED DATA")
print("-" * 80)
print(f"Merged records: {len(merged):,}")
print(f"Unique stores in merge: {merged['str_code'].nunique()}")
print(f"Unique clusters: {merged['Cluster'].nunique()}")
print(f"Unique SPUs: {merged['spu_code'].nunique()}")
print()

# Cluster analysis
cluster_stats = merged.groupby('Cluster').agg({
    'str_code': 'nunique',
    'spu_code': 'nunique',
    'spu_sales_amt': 'sum'
}).rename(columns={'str_code': 'stores', 'spu_code': 'spus', 'spu_sales_amt': 'total_sales'})

print("📊 CLUSTER STATISTICS")
print("-" * 80)
print(f"Total clusters: {len(cluster_stats)}")
print(f"Stores per cluster:")
print(f"  Min: {cluster_stats['stores'].min()}")
print(f"  Max: {cluster_stats['stores'].max()}")
print(f"  Median: {cluster_stats['stores'].median():.1f}")
print(f"  Mean: {cluster_stats['stores'].mean():.1f}")
print()
print(f"Clusters with 1 store: {(cluster_stats['stores'] == 1).sum()}")
print(f"Clusters with 2+ stores: {(cluster_stats['stores'] >= 2).sum()}")
print(f"Clusters with 3+ stores: {(cluster_stats['stores'] >= 3).sum()}")
print(f"Clusters with 5+ stores: {(cluster_stats['stores'] >= 5).sum()}")
print()

# SPU distribution per cluster
print("📊 SPU DISTRIBUTION PER CLUSTER")
print("-" * 80)
cluster_spu = merged.groupby(['Cluster', 'spu_code']).size().reset_index(name='stores_selling')
print(f"Total cluster-SPU combinations: {len(cluster_spu):,}")
print()
print("Stores selling per cluster-SPU:")
print(f"  1 store: {(cluster_spu['stores_selling'] == 1).sum():,} ({(cluster_spu['stores_selling'] == 1).sum()/len(cluster_spu):.1%})")
print(f"  2 stores: {(cluster_spu['stores_selling'] == 2).sum():,} ({(cluster_spu['stores_selling'] == 2).sum()/len(cluster_spu):.1%})")
print(f"  3+ stores: {(cluster_spu['stores_selling'] >= 3).sum():,} ({(cluster_spu['stores_selling'] >= 3).sum()/len(cluster_spu):.1%})")
print(f"  5+ stores: {(cluster_spu['stores_selling'] >= 5).sum():,} ({(cluster_spu['stores_selling'] >= 5).sum()/len(cluster_spu):.1%})")
print()

# Sales distribution
print("📊 SALES DISTRIBUTION")
print("-" * 80)
print(f"Total sales: ${merged['spu_sales_amt'].sum():,.0f}")
print(f"Sales per SPU:")
print(f"  Min: ${merged.groupby('spu_code')['spu_sales_amt'].sum().min():.0f}")
print(f"  Median: ${merged.groupby('spu_code')['spu_sales_amt'].sum().median():.0f}")
print(f"  Mean: ${merged.groupby('spu_code')['spu_sales_amt'].sum().mean():.0f}")
print(f"  Max: ${merged.groupby('spu_code')['spu_sales_amt'].sum().max():.0f}")
print()

# Category analysis
if 'sub_cate_name' in merged.columns:
    print("📊 CATEGORY ANALYSIS")
    print("-" * 80)
    cluster_cat = merged.groupby(['Cluster', 'sub_cate_name']).agg({
        'str_code': 'nunique',
        'spu_sales_amt': 'sum'
    }).rename(columns={'str_code': 'stores'})
    
    print(f"Total cluster-category combinations: {len(cluster_cat):,}")
    print(f"Stores per cluster-category:")
    print(f"  1 store: {(cluster_cat['stores'] == 1).sum():,}")
    print(f"  2+ stores: {(cluster_cat['stores'] >= 2).sum():,}")
    print(f"  3+ stores: {(cluster_cat['stores'] >= 3).sum():,}")
    print(f"  5+ stores: {(cluster_cat['stores'] >= 5).sum():,}")
    print()

# Root cause analysis
print("🎯 ROOT CAUSE ANALYSIS")
print("=" * 80)
print()

if len(overlap) < 50:
    print("❌ ISSUE #1: Very few stores in clustering")
    print(f"   Only {len(overlap)} stores have both clustering and sales data")
    print(f"   This severely limits peer-based analysis")
    print()

if cluster_stats['stores'].median() < 2:
    print("❌ ISSUE #2: Most clusters have only 1 store")
    print(f"   Median cluster size: {cluster_stats['stores'].median():.1f}")
    print(f"   Cannot do meaningful peer comparison with 1 store")
    print()

if (cluster_spu['stores_selling'] == 1).sum() / len(cluster_spu) > 0.8:
    print("❌ ISSUE #3: Most cluster-SPU combinations have only 1 store")
    print(f"   {(cluster_spu['stores_selling'] == 1).sum()/len(cluster_spu):.1%} have 1 store")
    print(f"   Cannot identify 'well-selling' patterns with 1 store")
    print()

print("💡 RECOMMENDATIONS")
print("=" * 80)
print()
print("1. Use ALL stores from 202510A sales data for clustering")
print(f"   Current: {len(clustering_stores)} stores")
print(f"   Available: {len(sales_stores)} stores")
print(f"   Potential gain: {len(sales_stores) - len(overlap)} more stores")
print()
print("2. Use subcategory-level analysis instead of SPU-level")
print("   Categories have more stores per cluster-category combination")
print()
print("3. Lower thresholds to minimum:")
print("   - Min cluster size: 1")
print("   - Min adoption: 5-10%")
print("   - Min sales: $10-50")
print()
print("4. Consider using 202410A data directly (not 202510A)")
print("   The clustering was built from 202410A, so it matches better")
print()
