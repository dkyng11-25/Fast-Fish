#!/usr/bin/env python3
"""Check if 121 is the number of unique subcategories."""

import sys
sys.path.insert(0, '/Users/borislavdzodzo/Desktop/Dev/ais-163-refactor-step-7/src')

import fireducks.pandas as pd

# Load data
sales_df = pd.read_csv('data/api_data/complete_category_sales_202510A.csv', dtype={'str_code': str})
cluster_df = pd.read_csv('output/clustering_results_subcategory.csv', dtype={'str_code': str})

# Normalize
if 'Cluster' in cluster_df.columns:
    cluster_df['cluster_id'] = cluster_df['Cluster']

feature_col = 'sub_cate_name'
sales_col = 'sal_amt'

# Merge and group
sales_with_clusters = sales_df.merge(cluster_df[['str_code', 'cluster_id']], on='str_code', how='inner')
cluster_features = sales_with_clusters.groupby(['cluster_id', feature_col]).agg({
    'str_code': 'nunique',
    sales_col: 'sum'
}).reset_index()
cluster_features.columns = ['cluster_id', feature_col, 'stores_selling', 'total_cluster_sales']

# Add cluster sizes
cluster_sizes = cluster_df.groupby('cluster_id').size().reset_index(name='cluster_size')
cluster_features = cluster_features.merge(cluster_sizes, on='cluster_id', how='left')

# Calculate percentage
cluster_features['pct_stores_selling'] = cluster_features['stores_selling'] / cluster_features['cluster_size']

# Apply thresholds
MIN_ADOPTION = 0.70
MIN_SALES = 100.0

both_pass = cluster_features[
    (cluster_features['pct_stores_selling'] >= MIN_ADOPTION) &
    (cluster_features['total_cluster_sales'] >= MIN_SALES)
]

print(f"Total cluster-feature combinations passing thresholds: {len(both_pass)}")
print(f"Unique subcategories in those combinations: {both_pass[feature_col].nunique()}")
print(f"Unique clusters in those combinations: {both_pass['cluster_id'].nunique()}")
print()

print("Maybe the legacy is counting unique subcategories, not combinations?")
print(f"If so, 121 would mean 121 unique subcategories across all clusters.")
