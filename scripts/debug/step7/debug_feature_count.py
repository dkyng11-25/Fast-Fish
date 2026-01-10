#!/usr/bin/env python3
"""Debug script to compare feature counts between legacy and refactored."""

import sys
sys.path.insert(0, '/Users/borislavdzodzo/Desktop/Dev/ais-163-refactor-step-7/src')

import fireducks.pandas as pd

# Load the same data both versions use
sales_df = pd.read_csv('data/api_data/complete_category_sales_202510A.csv', dtype={'str_code': str})
cluster_df = pd.read_csv('output/clustering_results_subcategory.csv', dtype={'str_code': str})

# Normalize cluster column
if 'Cluster' in cluster_df.columns and 'cluster_id' not in cluster_df.columns:
    cluster_df['cluster_id'] = cluster_df['Cluster']

print(f"Sales data: {len(sales_df)} records")
print(f"Cluster data: {len(cluster_df)} stores")
print(f"Sales columns: {list(sales_df.columns)}")
print()

# Check for duplicates in sales
feature_col = 'sub_cate_name'
sales_col = 'sal_amt'

print("=== SALES DATA ANALYSIS ===")
print(f"Unique store-subcategory combinations: {sales_df.groupby(['str_code', feature_col]).ngroups}")
print(f"Total rows: {len(sales_df)}")
print(f"Difference: {len(sales_df) - sales_df.groupby(['str_code', feature_col]).ngroups} duplicate combinations")
print()

# Aggregate like legacy does
sales_agg = sales_df.groupby(['str_code', feature_col], as_index=False)[sales_col].sum()
print(f"After aggregation (legacy style): {len(sales_agg)} rows")
print()

# Merge with clusters
sales_with_clusters = sales_df.merge(cluster_df[['str_code', 'cluster_id']], on='str_code', how='inner')
print(f"Sales merged with clusters (refactored style): {len(sales_with_clusters)} records")

sales_agg_with_clusters = sales_agg.merge(cluster_df[['str_code', 'cluster_id']], on='str_code', how='inner')
print(f"Aggregated sales merged with clusters (legacy style): {len(sales_agg_with_clusters)} records")
print()

# Group by cluster and feature
print("=== CLUSTER-FEATURE COMBINATIONS ===")
cluster_features_refactored = sales_with_clusters.groupby(['cluster_id', feature_col]).agg({
    'str_code': 'nunique',
    sales_col: 'sum'
}).reset_index()
print(f"Refactored groupby result: {len(cluster_features_refactored)} cluster-feature combinations")

cluster_features_legacy = sales_agg_with_clusters.groupby(['cluster_id', feature_col]).agg({
    'str_code': 'nunique',
    sales_col: 'sum'
}).reset_index()
print(f"Legacy groupby result: {len(cluster_features_legacy)} cluster-feature combinations")
print()

# Check if they're the same
if len(cluster_features_refactored) == len(cluster_features_legacy):
    print("✅ SAME NUMBER OF CLUSTER-FEATURE COMBINATIONS!")
else:
    print(f"❌ DIFFERENT: {len(cluster_features_refactored)} vs {len(cluster_features_legacy)}")
    print(f"   Difference: {len(cluster_features_refactored) - len(cluster_features_legacy)}")
