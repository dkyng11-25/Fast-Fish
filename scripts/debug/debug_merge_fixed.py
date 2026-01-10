import pandas as pd
import numpy as np

# Load the data
store_attrs_df = pd.read_csv('/Users/frogtime/Desktop/code/boris-fix/ProducMixClustering_spu_clustering_rules_visualization-copy/output/enriched_store_attributes_202509A_20250823_092211.csv')
cluster_results_df = pd.read_csv('/Users/frogtime/Desktop/code/boris-fix/ProducMixClustering_spu_clustering_rules_visualization-copy/output/enhanced_clustering_results.csv')

print('Store attributes shape:', store_attrs_df.shape)
print('Cluster results shape:', cluster_results_df.shape)
print('Store attributes columns:', list(store_attrs_df.columns))
print('Cluster results columns:', list(cluster_results_df.columns))

# Check if cluster_id exists in both
print('cluster_id in store_attrs_df:', 'cluster_id' in store_attrs_df.columns)
print('cluster_id in cluster_results_df:', 'cluster_id' in cluster_results_df.columns)

# Try the FIXED merge operation
# Handle potential duplicate column names by renaming in cluster_results_df
cluster_subset = cluster_results_df[['str_code', 'cluster_id']].copy()
cluster_subset = cluster_subset.rename(columns={'cluster_id': 'cluster_id_cluster'})
weights_df = store_attrs_df.merge(cluster_subset, on='str_code', how='inner')
# If cluster_id_cluster exists and cluster_id doesn't, use cluster_id_cluster
if 'cluster_id_cluster' in weights_df.columns and 'cluster_id' not in weights_df.columns:
    weights_df['cluster_id'] = weights_df['cluster_id_cluster']
    weights_df = weights_df.drop(columns=['cluster_id_cluster'])

print('Weights df shape:', weights_df.shape)
print('Weights df columns:', list(weights_df.columns))
print('cluster_id in weights_df:', 'cluster_id' in weights_df.columns)

# Check a few rows
print('\nFirst few rows of weights_df:')
print(weights_df[['str_code', 'cluster_id']].head())
