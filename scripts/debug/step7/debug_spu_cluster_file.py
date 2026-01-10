#!/usr/bin/env python3
"""Verify that using SPU cluster file explains the 121 features."""

import sys
sys.path.insert(0, '/Users/borislavdzodzo/Desktop/Dev/ais-163-refactor-step-7/src')

import fireducks.pandas as pd

print("=" * 80)
print("ROOT CAUSE VERIFICATION: SPU vs Subcategory Cluster Files")
print("=" * 80)
print()

# Load sales data
sales_df = pd.read_csv('data/api_data/complete_category_sales_202510A.csv', dtype={'str_code': str})

# Load WRONG cluster file (SPU - what legacy loaded)
cluster_spu = pd.read_csv('output/clustering_results_spu.csv', dtype={'str_code': str})
if 'Cluster' in cluster_spu.columns:
    cluster_spu['cluster_id'] = cluster_spu['Cluster']

# Load CORRECT cluster file (Subcategory - what refactored loaded)
cluster_subcat = pd.read_csv('output/clustering_results_subcategory.csv', dtype={'str_code': str})
if 'Cluster' in cluster_subcat.columns:
    cluster_subcat['cluster_id'] = cluster_subcat['Cluster']

print("CLUSTER FILE COMPARISON:")
print(f"SPU cluster file: {len(cluster_spu)} stores")
print(f"Subcategory cluster file: {len(cluster_subcat)} stores")
print()

feature_col = 'sub_cate_name'
sales_col = 'sal_amt'

# Test with SPU cluster file (WRONG - what legacy used)
print("=" * 80)
print("SCENARIO 1: Using SPU cluster file (LEGACY BEHAVIOR - WRONG!)")
print("=" * 80)

sales_with_spu = sales_df.merge(cluster_spu[['str_code', 'cluster_id']], on='str_code', how='left', indicator=True)
print(f"Merge results:")
print(f"  Total: {len(sales_with_spu)}")
print(f"  Matched: {(sales_with_spu['_merge'] == 'both').sum()}")
print(f"  Left only: {(sales_with_spu['_merge'] == 'left_only').sum()}")
print()

# Only keep matched records
sales_with_spu_matched = sales_with_spu[sales_with_spu['_merge'] == 'both'].copy()

# Group by cluster and feature
cluster_features_spu = sales_with_spu_matched.groupby(['cluster_id', feature_col]).agg({
    'str_code': 'nunique',
    sales_col: 'sum'
}).reset_index()
cluster_features_spu.columns = ['cluster_id', feature_col, 'stores_selling', 'total_cluster_sales']

# Add cluster sizes
cluster_sizes_spu = cluster_spu.groupby('cluster_id').size().reset_index(name='cluster_size')
cluster_features_spu = cluster_features_spu.merge(cluster_sizes_spu, on='cluster_id', how='left')
cluster_features_spu['pct_stores_selling'] = cluster_features_spu['stores_selling'] / cluster_features_spu['cluster_size']

# Apply thresholds
MIN_ADOPTION = 0.70
MIN_SALES = 100.0

both_pass_spu = cluster_features_spu[
    (cluster_features_spu['pct_stores_selling'] >= MIN_ADOPTION) &
    (cluster_features_spu['total_cluster_sales'] >= MIN_SALES)
]

print(f"Cluster-feature combinations: {len(cluster_features_spu)}")
print(f"Passing thresholds (≥70%, ≥$100): {len(both_pass_spu)}")
print()

# Test with Subcategory cluster file (CORRECT - what refactored used)
print("=" * 80)
print("SCENARIO 2: Using Subcategory cluster file (REFACTORED BEHAVIOR - CORRECT!)")
print("=" * 80)

sales_with_subcat = sales_df.merge(cluster_subcat[['str_code', 'cluster_id']], on='str_code', how='inner')
print(f"Merge results: {len(sales_with_subcat)} records (all matched)")
print()

# Group by cluster and feature
cluster_features_subcat = sales_with_subcat.groupby(['cluster_id', feature_col]).agg({
    'str_code': 'nunique',
    sales_col: 'sum'
}).reset_index()
cluster_features_subcat.columns = ['cluster_id', feature_col, 'stores_selling', 'total_cluster_sales']

# Add cluster sizes
cluster_sizes_subcat = cluster_subcat.groupby('cluster_id').size().reset_index(name='cluster_size')
cluster_features_subcat = cluster_features_subcat.merge(cluster_sizes_subcat, on='cluster_id', how='left')
cluster_features_subcat['pct_stores_selling'] = cluster_features_subcat['stores_selling'] / cluster_features_subcat['cluster_size']

# Apply thresholds
both_pass_subcat = cluster_features_subcat[
    (cluster_features_subcat['pct_stores_selling'] >= MIN_ADOPTION) &
    (cluster_features_subcat['total_cluster_sales'] >= MIN_SALES)
]

print(f"Cluster-feature combinations: {len(cluster_features_subcat)}")
print(f"Passing thresholds (≥70%, ≥$100): {len(both_pass_subcat)}")
print()

# Summary
print("=" * 80)
print("SUMMARY - ROOT CAUSE IDENTIFIED!")
print("=" * 80)
print(f"Legacy (SPU cluster file): {len(both_pass_spu)} features")
print(f"Refactored (Subcategory cluster file): {len(both_pass_subcat)} features")
print()

if len(both_pass_spu) == 121:
    print("✅ CONFIRMED: Using SPU cluster file produces 121 features (legacy behavior)")
else:
    print(f"⚠️  SPU cluster produces {len(both_pass_spu)} features, not 121")

if len(both_pass_subcat) == 2470:
    print("✅ CONFIRMED: Using Subcategory cluster file produces 2,470 features (refactored behavior)")
else:
    print(f"⚠️  Subcategory cluster produces {len(both_pass_subcat)} features, not 2,470")
