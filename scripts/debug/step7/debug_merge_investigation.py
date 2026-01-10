#!/usr/bin/env python3
"""Investigate why legacy and refactored get different merge results."""

import sys
sys.path.insert(0, '/Users/borislavdzodzo/Desktop/Dev/ais-163-refactor-step-7/src')

import fireducks.pandas as pd

print("=" * 80)
print("MERGE INVESTIGATION: Why different results?")
print("=" * 80)
print()

# Load the data
print("Loading data...")
sales_df = pd.read_csv('data/api_data/complete_category_sales_202510A.csv', dtype={'str_code': str})
cluster_df = pd.read_csv('output/clustering_results_subcategory.csv', dtype={'str_code': str})

# Normalize cluster column
if 'Cluster' in cluster_df.columns and 'cluster_id' not in cluster_df.columns:
    cluster_df['cluster_id'] = cluster_df['Cluster']

print(f"Sales data: {len(sales_df)} records")
print(f"Sales unique stores: {sales_df['str_code'].nunique()}")
print(f"Cluster data: {len(cluster_df)} stores")
print(f"Cluster unique stores: {cluster_df['str_code'].nunique()}")
print()

# Check store code overlap
sales_stores = set(sales_df['str_code'].unique())
cluster_stores = set(cluster_df['str_code'].unique())

print("=" * 80)
print("STORE CODE OVERLAP ANALYSIS")
print("=" * 80)
print(f"Stores in sales data: {len(sales_stores)}")
print(f"Stores in cluster data: {len(cluster_stores)}")
print(f"Stores in BOTH: {len(sales_stores & cluster_stores)}")
print(f"Stores ONLY in sales: {len(sales_stores - cluster_stores)}")
print(f"Stores ONLY in cluster: {len(cluster_stores - sales_stores)}")
print()

# Show examples of mismatched stores
only_in_sales = list(sales_stores - cluster_stores)[:10]
only_in_cluster = list(cluster_stores - sales_stores)[:10]

print("Examples of stores ONLY in sales (not in cluster):")
print(only_in_sales)
print()

print("Examples of stores ONLY in cluster (not in sales):")
print(only_in_cluster)
print()

# Try different merge strategies
print("=" * 80)
print("MERGE STRATEGY COMPARISON")
print("=" * 80)

# LEFT merge (what legacy uses)
left_merge = sales_df.merge(
    cluster_df[['str_code', 'cluster_id']], 
    on='str_code', 
    how='left',
    indicator=True
)
print(f"LEFT merge (legacy style):")
print(f"  Total records: {len(left_merge)}")
print(f"  Both matched: {(left_merge['_merge'] == 'both').sum()}")
print(f"  Left only: {(left_merge['_merge'] == 'left_only').sum()}")
print()

# INNER merge (what refactored uses)
inner_merge = sales_df.merge(
    cluster_df[['str_code', 'cluster_id']], 
    on='str_code', 
    how='inner'
)
print(f"INNER merge (refactored style):")
print(f"  Total records: {len(inner_merge)}")
print(f"  Unique stores: {inner_merge['str_code'].nunique()}")
print()

# Check if the issue is data type mismatch
print("=" * 80)
print("DATA TYPE ANALYSIS")
print("=" * 80)
print(f"Sales str_code dtype: {sales_df['str_code'].dtype}")
print(f"Cluster str_code dtype: {cluster_df['str_code'].dtype}")
print()

# Check for whitespace or formatting issues
print("Sample str_code values from sales:")
print(sales_df['str_code'].head(10).tolist())
print()

print("Sample str_code values from cluster:")
print(cluster_df['str_code'].head(10).tolist())
print()

# Check if there are any null values
print("=" * 80)
print("NULL VALUE CHECK")
print("=" * 80)
print(f"Null str_code in sales: {sales_df['str_code'].isna().sum()}")
print(f"Null str_code in cluster: {cluster_df['str_code'].isna().sum()}")
print()

# Final summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Expected matched records (stores in both): {len(sales_stores & cluster_stores)}")
print(f"Actual INNER merge records: {len(inner_merge)}")
print(f"Actual LEFT merge 'both' records: {(left_merge['_merge'] == 'both').sum()}")
print()

if len(inner_merge) == len(sales_df):
    print("⚠️  WARNING: INNER merge returned ALL sales records!")
    print("   This suggests ALL sales stores are in the cluster file.")
    print("   But the legacy log says only 18,659 matched out of 725,251.")
    print("   Something is VERY different between legacy and refactored data!")
elif len(inner_merge) < 100000:
    print("✅ INNER merge correctly filtered to matched stores only.")
    print(f"   This matches the legacy behavior ({len(inner_merge)} records).")
