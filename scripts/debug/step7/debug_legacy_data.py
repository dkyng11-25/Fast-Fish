#!/usr/bin/env python3
"""Check what data the legacy actually loaded."""

import sys
sys.path.insert(0, '/Users/borislavdzodzo/Desktop/Dev/ais-163-refactor-step-7/src')

import fireducks.pandas as pd

print("=" * 80)
print("LEGACY DATA INVESTIGATION")
print("=" * 80)
print()

# Check September data (what legacy log said it loaded)
print("Checking September 2025 data (202509A)...")
try:
    sales_sept = pd.read_csv('data/api_data/complete_category_sales_202509A.csv', dtype={'str_code': str})
    print(f"✅ September data exists: {len(sales_sept)} records")
    print(f"   Unique stores: {sales_sept['str_code'].nunique()}")
    print(f"   Sample stores: {sales_sept['str_code'].unique()[:10].tolist()}")
except FileNotFoundError:
    print("❌ September data NOT FOUND")
print()

# Check October data (what refactored loaded)
print("Checking October 2025 data (202510A)...")
try:
    sales_oct = pd.read_csv('data/api_data/complete_category_sales_202510A.csv', dtype={'str_code': str})
    print(f"✅ October data exists: {len(sales_oct)} records")
    print(f"   Unique stores: {sales_oct['str_code'].nunique()}")
    print(f"   Sample stores: {sales_oct['str_code'].unique()[:10].tolist()}")
except FileNotFoundError:
    print("❌ October data NOT FOUND")
print()

# Load cluster data
cluster_df = pd.read_csv('output/clustering_results_subcategory.csv', dtype={'str_code': str})
if 'Cluster' in cluster_df.columns:
    cluster_df['cluster_id'] = cluster_df['Cluster']

print(f"Cluster data: {len(cluster_df)} stores")
print(f"Sample cluster stores: {cluster_df['str_code'].unique()[:10].tolist()}")
print()

# Test merge with September data
if 'sales_sept' in locals():
    print("=" * 80)
    print("TESTING MERGE WITH SEPTEMBER DATA")
    print("=" * 80)
    
    sept_merge = sales_sept.merge(
        cluster_df[['str_code', 'cluster_id']], 
        on='str_code', 
        how='left',
        indicator=True
    )
    
    print(f"Total records: {len(sept_merge)}")
    print(f"Both matched: {(sept_merge['_merge'] == 'both').sum()}")
    print(f"Left only: {(sept_merge['_merge'] == 'left_only').sum()}")
    print()
    
    # Check store overlap
    sept_stores = set(sales_sept['str_code'].unique())
    cluster_stores = set(cluster_df['str_code'].unique())
    
    print(f"Stores in September sales: {len(sept_stores)}")
    print(f"Stores in cluster: {len(cluster_stores)}")
    print(f"Stores in BOTH: {len(sept_stores & cluster_stores)}")
    print(f"Stores ONLY in September sales: {len(sept_stores - cluster_stores)}")
    
    if len(sept_stores - cluster_stores) > 0:
        print(f"\nExamples of stores in September sales but NOT in cluster:")
        print(list(sept_stores - cluster_stores)[:20])
