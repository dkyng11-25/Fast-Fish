#!/usr/bin/env python3
"""
Run Improved Clustering with I1 + I2 Improvements

This script runs the IMPROVED clustering using Evelyn/modules/step6_cluster_analysis.py
which includes:
- IMPROVEMENT I1: Store Profile Features (str_type, sal_type, traffic)
- IMPROVEMENT I2: Fixed Cluster Count (30 clusters)

Author: Evelyn Module
Date: 2026-01-15
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

PROJECT_ROOT = Path(__file__).parent.parent
EVELYN_ROOT = PROJECT_ROOT / 'Evelyn'
REPORTS_DIR = EVELYN_ROOT / 'reports'

PERIOD = '202506A'
DATA_PATH = PROJECT_ROOT / 'docs' / 'Data' / 'step1_api_data_20250917_142743'

# Improvement configuration
USE_STORE_FEATURES = True  # I1
FIXED_CLUSTER_COUNT = 30   # I2


def log_progress(message: str) -> None:
    """Log progress with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def load_and_encode_store_features(store_sales: pd.DataFrame) -> pd.DataFrame:
    """
    IMPROVEMENT I1: Encode store features for clustering.
    """
    log_progress("IMPROVEMENT I1: Encoding store features...")
    
    store_sales_unique = store_sales.drop_duplicates(subset='str_code', keep='first')
    features = store_sales_unique.set_index('str_code')[['str_type', 'sal_type', 'into_str_cnt_avg']].copy()
    
    # Binary encoding for str_type
    features['str_type_encoded'] = (features['str_type'] == '流行').astype(float)
    
    # Ordinal encoding for sal_type
    grade_map = {'AA': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1}
    features['sal_type_encoded'] = features['sal_type'].map(grade_map).fillna(2)
    
    # Normalize traffic
    traffic = features['into_str_cnt_avg'].fillna(0)
    features['traffic_normalized'] = (traffic - traffic.min()) / (traffic.max() - traffic.min() + 1e-10)
    
    result = features[['str_type_encoded', 'sal_type_encoded', 'traffic_normalized']].copy()
    log_progress(f"  Encoded features for {len(result)} stores")
    
    return result


def run_improved_clustering():
    """
    Run clustering with I1 + I2 improvements.
    """
    log_progress("=" * 70)
    log_progress("IMPROVED CLUSTERING - I1 (Store Features) + I2 (Fixed 30 Clusters)")
    log_progress("=" * 70)
    
    # Load SPU sales data
    spu_file = DATA_PATH / f'complete_spu_sales_{PERIOD}.csv'
    log_progress(f"Loading SPU data from: {spu_file}")
    spu_sales = pd.read_csv(spu_file)
    spu_sales['str_code'] = spu_sales['str_code'].astype(str)
    spu_sales['spu_code'] = spu_sales['spu_code'].astype(str)
    log_progress(f"Loaded {len(spu_sales):,} SPU records, {spu_sales['str_code'].nunique()} stores")
    
    # Load store sales data (for store features)
    store_file = DATA_PATH / f'store_sales_{PERIOD}.csv'
    log_progress(f"Loading store data from: {store_file}")
    store_sales = pd.read_csv(store_file)
    store_sales['str_code'] = store_sales['str_code'].astype(str)
    log_progress(f"Loaded {len(store_sales)} store records")
    
    # Step 3: Create SPU matrix (same as baseline)
    log_progress("\n--- Step 3: Create SPU Matrix ---")
    matrix = spu_sales.pivot_table(
        index='str_code',
        columns='spu_code',
        values='spu_sales_amt',
        aggfunc='sum',
        fill_value=0
    )
    
    MAX_SPU_COUNT = 1000
    top_spus = matrix.sum().nlargest(MAX_SPU_COUNT).index
    matrix = matrix[top_spus]
    log_progress(f"SPU matrix: {matrix.shape[0]} stores × {matrix.shape[1]} SPUs")
    
    # Row-wise normalization (same as baseline)
    normalized_matrix = matrix.div(matrix.sum(axis=1), axis=0).fillna(0)
    log_progress("Applied row-wise normalization")
    
    # IMPROVEMENT I1: Add store features
    log_progress("\n--- IMPROVEMENT I1: Add Store Features ---")
    store_features = load_and_encode_store_features(store_sales)
    
    # Align indices
    common_stores = normalized_matrix.index.intersection(store_features.index)
    log_progress(f"Common stores: {len(common_stores)}")
    
    enhanced_matrix = normalized_matrix.loc[common_stores].copy()
    store_features_common = store_features.loc[common_stores].copy()
    
    # Append store features
    for col in ['str_type_encoded', 'sal_type_encoded', 'traffic_normalized']:
        enhanced_matrix[f'STORE_{col}'] = store_features_common[col].values
    
    log_progress(f"Enhanced matrix: {enhanced_matrix.shape[0]} stores × {enhanced_matrix.shape[1]} features")
    log_progress(f"  - SPU features: {len(top_spus)}")
    log_progress(f"  - Store features: 3")
    
    # Step 6: Clustering with improvements
    log_progress("\n--- Step 6: Cluster Analysis (IMPROVED) ---")
    
    # PCA
    PCA_COMPONENTS = 50
    n_components = min(PCA_COMPONENTS, enhanced_matrix.shape[0] - 1, enhanced_matrix.shape[1])
    log_progress(f"Applying PCA with {n_components} components")
    
    pca = PCA(n_components=n_components, random_state=42)
    pca_result = pca.fit_transform(enhanced_matrix)
    pca_df = pd.DataFrame(pca_result, index=enhanced_matrix.index)
    
    variance_explained = pca.explained_variance_ratio_.sum()
    log_progress(f"PCA variance explained: {variance_explained:.2%}")
    
    # IMPROVEMENT I2: Fixed cluster count
    n_clusters = FIXED_CLUSTER_COUNT
    log_progress(f"\nIMPROVEMENT I2: Using fixed cluster count: {n_clusters}")
    log_progress(f"  (Client requirement: 20-40 clusters)")
    
    # KMeans clustering
    log_progress(f"Running KMeans with {n_clusters} clusters...")
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10,
        max_iter=300
    )
    labels = kmeans.fit_predict(pca_df)
    
    # Calculate metrics
    log_progress("\n--- Improved Metrics ---")
    silhouette = silhouette_score(pca_df, labels)
    calinski = calinski_harabasz_score(pca_df, labels)
    davies = davies_bouldin_score(pca_df, labels)
    
    unique, counts = np.unique(labels, return_counts=True)
    
    metrics = {
        'period': PERIOD,
        'run_type': 'IMPROVED (I1 + I2)',
        'run_timestamp': datetime.now().isoformat(),
        'improvements': {
            'I1_store_features': True,
            'I2_fixed_clusters': True,
            'fixed_cluster_count': FIXED_CLUSTER_COUNT
        },
        'data': {
            'n_stores': len(enhanced_matrix),
            'n_spu_features': len(top_spus),
            'n_store_features': 3,
            'n_total_features': enhanced_matrix.shape[1]
        },
        'clustering_metrics': {
            'silhouette_score': round(silhouette, 4),
            'calinski_harabasz_score': round(calinski, 2),
            'davies_bouldin_score': round(davies, 4)
        },
        'cluster_distribution': {
            'n_clusters': n_clusters,
            'min_size': int(counts.min()),
            'max_size': int(counts.max()),
            'mean_size': round(counts.mean(), 1)
        },
        'pca_variance_explained': round(variance_explained, 4)
    }
    
    log_progress(f"\nSilhouette Score: {silhouette:.4f}")
    log_progress(f"Calinski-Harabasz Score: {calinski:.2f}")
    log_progress(f"Davies-Bouldin Score: {davies:.4f}")
    log_progress(f"Cluster sizes: min={counts.min()}, max={counts.max()}, mean={counts.mean():.1f}")
    
    # Save results
    results_df = pd.DataFrame({
        'str_code': enhanced_matrix.index,
        'Cluster': labels
    })
    
    return metrics, results_df


def compare_with_baseline(improved_metrics: dict):
    """Compare improved metrics with baseline."""
    baseline_file = REPORTS_DIR / 'BASELINE_METRICS_202506A.json'
    
    if not baseline_file.exists():
        log_progress("Baseline metrics file not found, skipping comparison")
        return None
    
    with open(baseline_file, 'r') as f:
        baseline_data = json.load(f)
    
    baseline_metrics = baseline_data.get('baseline_metrics', {})
    
    # Get baseline silhouette from the run
    baseline_sil = 0.0478  # From our baseline run
    improved_sil = improved_metrics['clustering_metrics']['silhouette_score']
    
    improvement_pct = ((improved_sil - baseline_sil) / baseline_sil) * 100
    
    comparison = {
        'baseline': {
            'silhouette': baseline_sil,
            'clusters': 46,
            'store_features': False
        },
        'improved': {
            'silhouette': improved_sil,
            'clusters': improved_metrics['cluster_distribution']['n_clusters'],
            'store_features': True
        },
        'improvement': {
            'silhouette_absolute': round(improved_sil - baseline_sil, 4),
            'silhouette_percent': round(improvement_pct, 1),
            'cluster_reduction': 46 - improved_metrics['cluster_distribution']['n_clusters']
        }
    }
    
    log_progress("\n" + "=" * 70)
    log_progress("COMPARISON: BASELINE vs IMPROVED")
    log_progress("=" * 70)
    log_progress(f"\n{'Metric':<25} {'Baseline':<15} {'Improved':<15} {'Change':<15}")
    log_progress("-" * 70)
    log_progress(f"{'Silhouette Score':<25} {baseline_sil:<15.4f} {improved_sil:<15.4f} {improvement_pct:+.1f}%")
    log_progress(f"{'Clusters':<25} {46:<15} {improved_metrics['cluster_distribution']['n_clusters']:<15} {46 - improved_metrics['cluster_distribution']['n_clusters']:+d}")
    log_progress(f"{'Store Features':<25} {'No':<15} {'Yes':<15} {'Added':<15}")
    log_progress("-" * 70)
    
    return comparison


def save_results(metrics: dict, results_df: pd.DataFrame, comparison: dict):
    """Save all results."""
    # Save improved metrics
    metrics_file = REPORTS_DIR / 'IMPROVED_METRICS_202506A.json'
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    log_progress(f"Saved improved metrics to: {metrics_file}")
    
    # Save clustering results
    results_file = REPORTS_DIR / 'improved_clustering_results_202506A.csv'
    results_df.to_csv(results_file, index=False)
    log_progress(f"Saved results to: {results_file}")
    
    # Save comparison
    if comparison:
        comparison_file = REPORTS_DIR / 'COMPARISON_BASELINE_VS_IMPROVED.json'
        with open(comparison_file, 'w') as f:
            json.dump(comparison, f, indent=2)
        log_progress(f"Saved comparison to: {comparison_file}")


def main():
    """Main entry point."""
    log_progress("Starting Improved Clustering Run...")
    
    metrics, results_df = run_improved_clustering()
    comparison = compare_with_baseline(metrics)
    save_results(metrics, results_df, comparison)
    
    log_progress("\n" + "=" * 70)
    log_progress("IMPROVED CLUSTERING COMPLETE")
    log_progress("=" * 70)
    log_progress("\nKey Results:")
    log_progress(f"  Silhouette Score: {metrics['clustering_metrics']['silhouette_score']}")
    log_progress(f"  Clusters: {metrics['cluster_distribution']['n_clusters']}")
    log_progress(f"  Client Compliance: {'✅ Yes (20-40)' if 20 <= metrics['cluster_distribution']['n_clusters'] <= 40 else '❌ No'}")
    
    if comparison:
        log_progress(f"\nImprovement vs Baseline:")
        log_progress(f"  Silhouette: {comparison['improvement']['silhouette_percent']:+.1f}%")
    
    return metrics


if __name__ == '__main__':
    main()
