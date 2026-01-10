#!/usr/bin/env python3
"""
Re-create clustering with OPTIMAL cluster count for 53 stores
Rule of thumb: sqrt(n/2) clusters for n stores
For 53 stores: sqrt(53/2) ≈ 5 clusters
"""
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import normalize
import os

print("🔧 Re-creating Clustering with Optimal Cluster Count")
print("=" * 80)
print()

# Load SPU sales
spu_sales = pd.read_csv('data/api_data/complete_spu_sales_202410A.csv', dtype={'str_code': str, 'spu_code': str})
print(f"📊 Loaded {len(spu_sales):,} SPU sales records")
print(f"   Unique stores: {spu_sales['str_code'].nunique()}")
print()

# Create matrix
store_spu = spu_sales.groupby(['str_code', 'spu_code'])['spu_sales_amt'].sum().reset_index()
matrix = store_spu.pivot_table(
    index='str_code',
    columns='spu_code',
    values='spu_sales_amt',
    fill_value=0,
    aggfunc='sum'
)

print(f"📊 Matrix: {matrix.shape[0]} stores × {matrix.shape[1]} SPUs")
print()

# Normalize
normalized_matrix = pd.DataFrame(
    normalize(matrix.values, norm='l2', axis=1),
    index=matrix.index,
    columns=matrix.columns
)

# Try different cluster counts
n_stores = len(matrix)
cluster_options = [
    (5, "Optimal (sqrt(n/2))"),
    (8, "Conservative (more stores/cluster)"),
    (10, "Moderate"),
    (15, "Aggressive")
]

print("🧪 Testing Different Cluster Counts")
print("=" * 80)
print()

results = []
for n_clusters, description in cluster_options:
    # PCA
    pca = PCA(n_components=min(10, normalized_matrix.shape[1]))
    pca_features = pca.fit_transform(normalized_matrix.values)
    
    # K-means
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(pca_features)
    
    # Stats
    cluster_sizes = pd.Series(labels).value_counts()
    avg_size = n_stores / n_clusters
    min_size = cluster_sizes.min()
    max_size = cluster_sizes.max()
    single_store_clusters = (cluster_sizes == 1).sum()
    
    results.append({
        'n_clusters': n_clusters,
        'description': description,
        'avg_size': avg_size,
        'min_size': min_size,
        'max_size': max_size,
        'single_store': single_store_clusters,
        'labels': labels
    })
    
    print(f"✅ {n_clusters} clusters ({description}):")
    print(f"   Avg stores/cluster: {avg_size:.1f}")
    print(f"   Min: {min_size}, Max: {max_size}")
    print(f"   Single-store clusters: {single_store_clusters}")
    print()

# Choose best option (fewest single-store clusters, reasonable avg size)
best = min(results, key=lambda x: (x['single_store'], -x['avg_size']))
print(f"🎯 RECOMMENDED: {best['n_clusters']} clusters ({best['description']})")
print(f"   Avg: {best['avg_size']:.1f} stores/cluster")
print(f"   Single-store clusters: {best['single_store']}")
print()

# Ask user which to use
print("📋 Options:")
for i, r in enumerate(results):
    print(f"   {i+1}. {r['n_clusters']} clusters - avg {r['avg_size']:.1f} stores/cluster, {r['single_store']} single-store")

print()
choice = input("Choose option (1-4) or press Enter for recommended: ").strip()

if choice == "":
    selected = best
elif choice.isdigit() and 1 <= int(choice) <= len(results):
    selected = results[int(choice) - 1]
else:
    print("Invalid choice, using recommended")
    selected = best

print()
print(f"✅ Creating clustering with {selected['n_clusters']} clusters...")

# Create clustering dataframe
clustering = pd.DataFrame({
    'str_code': normalized_matrix.index,
    'Cluster': selected['labels']
})

# Save
output_file = f"output/clustering_results_spu_202410A_OPTIMAL_{selected['n_clusters']}.csv"
clustering.to_csv(output_file, index=False)
print(f"   ✅ Saved: {output_file}")

# Update symlinks
for target in [
    'output/clustering_results_spu_202410A.csv',
    'output/clustering_results_spu_202510A.csv',
    'output/clustering_results_spu.csv',
    'output/clustering_results_subcategory_202410A.csv',
    'output/clustering_results_subcategory_202510A.csv',
    'output/clustering_results_subcategory.csv',
]:
    if os.path.exists(target) or os.path.islink(target):
        os.remove(target)
    os.symlink(os.path.basename(output_file), target)
    print(f"   ✅ Symlink: {target}")

print()

# Verify
c = pd.read_csv('output/clustering_results_spu_202510A.csv', dtype={'str_code': str})
s = pd.read_csv('data/api_data/complete_spu_sales_202510A.csv', dtype={'str_code': str})
merged = s.merge(c, on='str_code', how='inner')

print("🔍 Verification:")
print(f"   Merge: {len(merged):,} / {len(s):,} records ({len(merged)/len(s):.1%})")
print(f"   Clusters: {c['Cluster'].nunique()}")
print(f"   Stores per cluster: {len(c) / c['Cluster'].nunique():.1f} avg")
print()

# Analyze cluster-SPU combinations
merged_with_cluster = s.merge(c, on='str_code', how='inner')
cluster_spu = merged_with_cluster.groupby(['Cluster', 'spu_code']).size().reset_index(name='stores')

print("📊 Cluster-SPU Combinations:")
print(f"   Total: {len(cluster_spu):,}")
print(f"   1 store: {(cluster_spu['stores'] == 1).sum():,} ({(cluster_spu['stores'] == 1).sum()/len(cluster_spu):.1%})")
print(f"   2+ stores: {(cluster_spu['stores'] >= 2).sum():,} ({(cluster_spu['stores'] >= 2).sum()/len(cluster_spu):.1%})")
print(f"   3+ stores: {(cluster_spu['stores'] >= 3).sum():,} ({(cluster_spu['stores'] >= 3).sum()/len(cluster_spu):.1%})")
print(f"   5+ stores: {(cluster_spu['stores'] >= 5).sum():,} ({(cluster_spu['stores'] >= 5).sum()/len(cluster_spu):.1%})")
print()

print("🎉 Optimal Clustering Created!")
print("=" * 80)
print()
print("Next: Re-run Steps 7-12 with new clustering")
print("  ./RUN_STEPS_7_12_STANDARDIZED_CLI.sh")
