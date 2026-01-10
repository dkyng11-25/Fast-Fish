#!/usr/bin/env python3
"""Check if September data gives us 121 features."""

import sys
sys.path.insert(0, '/Users/borislavdzodzo/Desktop/Dev/ais-163-refactor-step-7/src')

import fireducks.pandas as pd

# Load SEPTEMBER data (what legacy uses)
sales_df = pd.read_csv('data/api_data/complete_category_sales_202509A.csv', dtype={'str_code': str})
cluster_df = pd.read_csv('output/clustering_results_subcategory.csv', dtype={'str_code': str})

# Normalize
if 'Cluster' in cluster_df.columns:
    cluster_df['cluster_id'] = cluster_df['Cluster']

feature_col = 'sub_cate_name'
sales_col = 'sal_amt'

print("=== SEPTEMBER DATA (202509A) ===")
print(f"Sales records: {len(sales_df)}")

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

print(f"Total cluster-feature combinations: {len(cluster_features)}")

# Apply thresholds
MIN_ADOPTION = 0.70
MIN_SALES = 100.0

both_pass = cluster_features[
    (cluster_features['pct_stores_selling'] >= MIN_ADOPTION) &
    (cluster_features['total_cluster_sales'] >= MIN_SALES)
]
print(f"Pass BOTH thresholds (≥70%, ≥$100): {len(both_pass)}")
print()

# Now check October data
print("=== OCTOBER DATA (202510A) ===")
sales_df_oct = pd.read_csv('data/api_data/complete_category_sales_202510A.csv', dtype={'str_code': str})
print(f"Sales records: {len(sales_df_oct)}")

sales_with_clusters_oct = sales_df_oct.merge(cluster_df[['str_code', 'cluster_id']], on='str_code', how='inner')
cluster_features_oct = sales_with_clusters_oct.groupby(['cluster_id', feature_col]).agg({
    'str_code': 'nunique',
    sales_col: 'sum'
}).reset_index()
cluster_features_oct.columns = ['cluster_id', feature_col, 'stores_selling', 'total_cluster_sales']
cluster_features_oct = cluster_features_oct.merge(cluster_sizes, on='cluster_id', how='left')
cluster_features_oct['pct_stores_selling'] = cluster_features_oct['stores_selling'] / cluster_features_oct['cluster_size']

print(f"Total cluster-feature combinations: {len(cluster_features_oct)}")

both_pass_oct = cluster_features_oct[
    (cluster_features_oct['pct_stores_selling'] >= MIN_ADOPTION) &
    (cluster_features_oct['total_cluster_sales'] >= MIN_SALES)
]
print(f"Pass BOTH thresholds (≥70%, ≥$100): {len(both_pass_oct)}")
