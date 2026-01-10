#!/usr/bin/env python3
"""Debug script to understand threshold filtering differences."""

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

print(f"Total cluster-feature combinations: {len(cluster_features)}")
print()

# Apply thresholds
MIN_ADOPTION = 0.70
MIN_SALES = 100.0

print(f"Thresholds: ≥{MIN_ADOPTION:.0%} adoption, ≥${MIN_SALES:.0f} sales")
print()

# Check each threshold separately
adoption_pass = cluster_features[cluster_features['pct_stores_selling'] >= MIN_ADOPTION]
print(f"Pass adoption threshold (≥{MIN_ADOPTION:.0%}): {len(adoption_pass)}")

sales_pass = cluster_features[cluster_features['total_cluster_sales'] >= MIN_SALES]
print(f"Pass sales threshold (≥${MIN_SALES:.0f}): {len(sales_pass)}")

both_pass = cluster_features[
    (cluster_features['pct_stores_selling'] >= MIN_ADOPTION) &
    (cluster_features['total_cluster_sales'] >= MIN_SALES)
]
print(f"Pass BOTH thresholds: {len(both_pass)}")
print()

# Show distribution
print("=== ADOPTION RATE DISTRIBUTION ===")
print(cluster_features['pct_stores_selling'].describe())
print()

print("=== SALES DISTRIBUTION ===")
print(cluster_features['total_cluster_sales'].describe())
print()

# Show some examples that pass/fail
print("=== EXAMPLES THAT PASS ===")
print(both_pass.head(10))
print()

print("=== EXAMPLES THAT FAIL (high adoption but low sales) ===")
fail_sales = cluster_features[
    (cluster_features['pct_stores_selling'] >= MIN_ADOPTION) &
    (cluster_features['total_cluster_sales'] < MIN_SALES)
]
print(f"Count: {len(fail_sales)}")
if len(fail_sales) > 0:
    print(fail_sales.head(10))
