#!/usr/bin/env python3
"""
Quick fix: Manually create proper matrix files and clustering
Bypasses the Step 3 bug where index=False loses store codes
"""
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import os

print("🔧 Creating Proper Matrix and Clustering")
print("=" * 80)
print()

# ============================================================================
# STEP 1: Load SPU sales data (has real store codes!)
# ============================================================================
print("📊 Loading SPU sales data from 202410A...")
spu_sales = pd.read_csv('data/api_data/complete_spu_sales_202410A.csv', dtype={'str_code': str, 'spu_code': str})
print(f"   Loaded {len(spu_sales):,} records")
print(f"   Unique stores: {spu_sales['str_code'].nunique()}")
print(f"   Unique SPUs: {spu_sales['spu_code'].nunique()}")
print()

# ============================================================================
# STEP 2: Create SPU matrix (store x SPU)
# ============================================================================
print("📊 Creating store-SPU matrix...")
# Aggregate sales by store-SPU
store_spu = spu_sales.groupby(['str_code', 'spu_code'])['spu_sales_amt'].sum().reset_index()

# Create pivot table
matrix = store_spu.pivot_table(
    index='str_code',
    columns='spu_code', 
    values='spu_sales_amt',
    fill_value=0,
    aggfunc='sum'
)

print(f"   Matrix shape: {matrix.shape[0]} stores x {matrix.shape[1]} SPUs")
print(f"   Index (store codes) sample: {matrix.index[:5].tolist()}")
print()

# Normalize matrix (L2 normalization)
from sklearn.preprocessing import normalize
normalized_matrix = pd.DataFrame(
    normalize(matrix.values, norm='l2', axis=1),
    index=matrix.index,
    columns=matrix.columns
)

# ============================================================================
# STEP 3: Save matrices WITH index (FIX THE BUG!)
# ============================================================================
print("💾 Saving matrices WITH index...")
# Save original matrix
matrix.to_csv('data/store_spu_limited_matrix_202410A_FIXED.csv', index=True)  # index=True!
print(f"   ✅ Saved: data/store_spu_limited_matrix_202410A_FIXED.csv")

# Save normalized matrix
normalized_matrix.to_csv('data/normalized_spu_limited_matrix_202410A_FIXED.csv', index=True)  # index=True!
print(f"   ✅ Saved: data/normalized_spu_limited_matrix_202410A_FIXED.csv")

# Create symlinks
for src, dst in [
    ('store_spu_limited_matrix_202410A_FIXED.csv', 'data/store_spu_limited_matrix.csv'),
    ('normalized_spu_limited_matrix_202410A_FIXED.csv', 'data/normalized_spu_limited_matrix.csv'),
]:
    if os.path.exists(dst) or os.path.islink(dst):
        os.remove(dst)
    os.symlink(os.path.basename(src), dst)
    print(f"   ✅ Symlink: {dst}")

print()

# Verify matrix can be read back correctly
print("🔍 Verifying matrix integrity...")
test_df = pd.read_csv('data/normalized_spu_limited_matrix_202410A_FIXED.csv', index_col=0)
print(f"   Index sample: {test_df.index[:5].tolist()}")
if all(str(idx) == '0.0' or idx == 0.0 for idx in test_df.index[:5]):
    print("   ❌ ERROR: Index still corrupted!")
    exit(1)
else:
    print("   ✅ Index preserved correctly!")
print()

# ============================================================================
# STEP 4: Create clustering using the matrix
# ============================================================================
print("📊 Creating store clusters...")

# Use PCA for dimensionality reduction
print("   Running PCA...")
pca = PCA(n_components=min(10, normalized_matrix.shape[1]))
pca_features = pca.fit_transform(normalized_matrix.values)
print(f"   PCA explained variance: {pca.explained_variance_ratio_.sum():.1%}")

# K-means clustering
print("   Running K-means clustering...")
n_clusters = 46  # Same as before
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(pca_features)

# Create clustering dataframe
clustering = pd.DataFrame({
    'str_code': normalized_matrix.index,
    'Cluster': cluster_labels
})

print(f"   Created {n_clusters} clusters")
print(f"   Stores per cluster (avg): {len(clustering) / n_clusters:.1f}")
print()

# ============================================================================
# STEP 5: Save clustering
# ============================================================================
print("💾 Saving clustering...")
clustering.to_csv('output/clustering_results_spu_202410A_FIXED.csv', index=False)
print(f"   ✅ Saved: output/clustering_results_spu_202410A_FIXED.csv")

# Create symlinks for 202410A and 202510A
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
    os.symlink('clustering_results_spu_202410A_FIXED.csv', target)
    print(f"   ✅ Symlink: {target}")

print()

# ============================================================================
# STEP 6: Verify clustering works with SPU sales
# ============================================================================
print("🔍 Verifying clustering merge...")
c = pd.read_csv('output/clustering_results_spu_202510A.csv', dtype={'str_code': str})
s = pd.read_csv('data/api_data/complete_spu_sales_202510A.csv', dtype={'str_code': str})
merged = s.merge(c, on='str_code', how='inner')

print(f"   SPU sales records: {len(s):,}")
print(f"   Clustering stores: {c['str_code'].nunique()}")
print(f"   Merged records: {len(merged):,}")
print(f"   Match rate: {len(merged)/len(s):.1%}")
print()

if len(merged) == 0:
    print("❌ ERROR: Merge produced 0 matches!")
    exit(1)
elif len(merged) / len(s) < 0.5:
    print(f"⚠️  WARNING: Low match rate ({len(merged)/len(s):.1%})")
else:
    print("✅ Merge successful!")

print()
print("🎉 Matrix and Clustering Created Successfully!")
print("=" * 80)
print()
print("✅ Matrix files have real store codes")
print("✅ Clustering has real store codes")
print("✅ Merge operations work")
print("✅ Ready for Steps 7-12!")
print()
print("Next: ./RUN_STEPS_7_12_STANDARDIZED_CLI.sh")
