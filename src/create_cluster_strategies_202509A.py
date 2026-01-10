#!/usr/bin/env python3
"""
Create comprehensive cluster strategies file for 202509A period
by merging real data from comprehensive cluster labels and cluster fashion makeup.
"""

import pandas as pd
import numpy as np
import os

# Define paths
project_root = '/Users/frogtime/Desktop/code/boris-fix/ProducMixClustering_spu_clustering_rules_visualization-copy'
ff_results_dir = os.path.join(project_root, 'output', 'FF results')
output_dir = os.path.join(project_root, 'output')

# Load the comprehensive cluster labels (44 clusters)
comprehensive_labels_path = os.path.join(ff_results_dir, 'comprehensive_cluster_labels.csv')
cluster_labels_df = pd.read_csv(comprehensive_labels_path)
print(f"Loaded comprehensive cluster labels with {len(cluster_labels_df)} clusters")

# Load the cluster fashion makeup data
fashion_makeup_path = os.path.join(output_dir, 'cluster_fashion_makeup_202509A.csv')
fashion_makeup_df = pd.read_csv(fashion_makeup_path)
print(f"Loaded fashion makeup data with {len(fashion_makeup_df)} clusters")

# Display column information
print("\nCluster Labels Columns:", list(cluster_labels_df.columns))
print("Fashion Makeup Columns:", list(fashion_makeup_df.columns))

# Create cluster strategies by merging the data
# The fashion makeup file has 'Cluster' column that maps to 'cluster_id' in labels
# and 'index' column that represents the sequential index

# Rename columns in fashion makeup for clarity
fashion_makeup_df = fashion_makeup_df.rename(columns={'Cluster': 'cluster_id', 'Store_Group_Name': 'cluster_name'})

# Merge the dataframes on cluster_id
merged_df = pd.merge(cluster_labels_df, fashion_makeup_df, on='cluster_id', how='left')
print(f"\nMerged dataframe has {len(merged_df)} rows")

# Create the cluster strategies dataframe with required columns
cluster_strategies_df = pd.DataFrame()

# Basic cluster information
cluster_strategies_df['cluster_id'] = merged_df['cluster_id']
cluster_strategies_df['cluster_name'] = merged_df['cluster_name']
cluster_strategies_df['store_count'] = merged_df['cluster_size']

# Determine optimization focus based on fashion percentage
cluster_strategies_df['optimization_focus'] = np.where(
    merged_df['men_percentage'] + merged_df['women_percentage'] > 70, 
    'Fashion', 
    'Balanced'
)

# Capacity tier based on avg_estimated_capacity
cluster_strategies_df['capacity_tier'] = merged_df['capacity_tier']

# Fashion and basic allocation ratios from fashion makeup data
cluster_strategies_df['avg_fashion_allocation'] = (merged_df['men_percentage'] + merged_df['women_percentage']) / 100.0
cluster_strategies_df['avg_basic_allocation'] = merged_df['unisex_percentage'] / 100.0

# Capacity utilization target (using a standard value since not in data)
cluster_strategies_df['avg_capacity_utilization_target'] = 0.85

# Rack capacity (using avg_estimated_capacity from labels)
cluster_strategies_df['avg_rack_capacity'] = merged_df['avg_estimated_capacity']

# Priority score (using a calculated value based on cluster quality)
silhouette_scores = merged_df['silhouette_score'].abs()  # Use absolute value for scoring
cluster_strategies_df['avg_priority_score'] = (silhouette_scores * 100).clip(0, 100)  # Scale to 0-100

# Priority store distribution (simplified)
cluster_strategies_df['high_priority_stores'] = 0
cluster_strategies_df['medium_priority_stores'] = cluster_strategies_df['store_count']
cluster_strategies_df['low_priority_stores'] = 0

# High priority percentage
cluster_strategies_df['high_priority_percentage'] = 0.0

# Generate recommendations based on cluster characteristics
recommendations = []
for idx, row in merged_df.iterrows():
    recs = []
    
    # Fashion-focused recommendations
    fashion_pct = (row['men_percentage'] + row['women_percentage'])
    if fashion_pct > 70:
        recs.append("Enhance new arrival frequency for fashion-focused stores")
        recs.append("Implement dynamic pricing for seasonal fashion items")
    else:
        recs.append("Maintain balanced fashion/basic mix")
        recs.append("Implement flexible allocation based on seasonal trends")
    
    # Temperature-based recommendations
    if 'Hot' in str(row['temperature_classification']):
        recs.append("Optimize summer collection allocation for hot climate stores")
    elif 'Cool' in str(row['temperature_classification']):
        recs.append("Focus on transitional seasonal items for cool climate stores")
    
    # Capacity-based recommendations
    if row['capacity_tier'] == 'Large':
        recs.append("Deploy advanced space management strategies")
    
    recommendations.append("; ".join(recs))

cluster_strategies_df['recommendations'] = recommendations

# Save the cluster strategies file
output_path = os.path.join(output_dir, 'cluster_level_merchandising_strategies_202509A.csv')
cluster_strategies_df.to_csv(output_path, index=False)
print(f"\nCluster strategies saved to: {output_path}")

# Display summary
print("\nCluster Strategies Summary:")
print(f"- Total clusters: {len(cluster_strategies_df)}")
print(f"- Columns: {list(cluster_strategies_df.columns)}")
print("\nFirst few rows:")
print(cluster_strategies_df.head())

# Verify we have all 44 clusters
if len(cluster_strategies_df) == 44:
    print("\n✅ SUCCESS: All 44 clusters included in strategies file")
else:
    print(f"\n⚠️  WARNING: Expected 44 clusters, got {len(cluster_strategies_df)}")
