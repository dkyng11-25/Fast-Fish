#!/usr/bin/env python3
"""
Baseline Step 6 Runner - Execute ORIGINAL src/step6_cluster_analysis.py

This script runs the ORIGINAL step6 module to capture baseline clustering metrics.
NO modifications to the original module - just execution and metric capture.

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
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

PERIOD = '202506A'
DATA_PATH = PROJECT_ROOT / 'docs' / 'Data' / 'step1_api_data_20250917_142743'
EVELYN_ROOT = PROJECT_ROOT / 'Evelyn'
REPORTS_DIR = EVELYN_ROOT / 'reports'
LOGS_DIR = EVELYN_ROOT / 'logs'


def log_progress(message: str) -> None:
    """Log progress with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def run_baseline_clustering():
    """
    Run baseline clustering using the EXACT same logic as src/step6_cluster_analysis.py.
    
    This replicates the original step6 logic WITHOUT modifications to capture baseline metrics.
    """
    log_progress("=" * 70)
    log_progress("BASELINE CLUSTERING - Using ORIGINAL src/step6 Logic")
    log_progress("=" * 70)
    
    # Load SPU sales data
    spu_file = DATA_PATH / f'complete_spu_sales_{PERIOD}.csv'
    log_progress(f"Loading SPU data from: {spu_file}")
    spu_sales = pd.read_csv(spu_file)
    spu_sales['str_code'] = spu_sales['str_code'].astype(str)
    spu_sales['spu_code'] = spu_sales['spu_code'].astype(str)
    log_progress(f"Loaded {len(spu_sales):,} SPU records, {spu_sales['str_code'].nunique()} stores")
    
    # Step 3 Logic: Create SPU matrix (ORIGINAL)
    log_progress("\n--- Step 3: Create SPU Matrix (ORIGINAL LOGIC) ---")
    
    # Pivot to store × SPU matrix
    matrix = spu_sales.pivot_table(
        index='str_code',
        columns='spu_code',
        values='spu_sales_amt',
        aggfunc='sum',
        fill_value=0
    )
    log_progress(f"Raw matrix: {matrix.shape[0]} stores × {matrix.shape[1]} SPUs")
    
    # Limit to top 1000 SPUs (ORIGINAL step3 logic)
    MAX_SPU_COUNT = 1000
    top_spus = matrix.sum().nlargest(MAX_SPU_COUNT).index
    matrix = matrix[top_spus]
    log_progress(f"Limited to top {MAX_SPU_COUNT} SPUs: {matrix.shape}")
    
    # ORIGINAL step3 normalization: ROW-WISE (div by row sum)
    # From src/step3_prepare_matrix.py line 605:
    # normalized_matrix = matrix.div(matrix.sum(axis=1), axis=0).fillna(0)
    normalized_matrix = matrix.div(matrix.sum(axis=1), axis=0).fillna(0)
    log_progress("Applied ROW-WISE normalization (original step3)")
    
    # Step 6 Logic: Clustering (ORIGINAL)
    log_progress("\n--- Step 6: Cluster Analysis (ORIGINAL LOGIC) ---")
    
    # PCA configuration (ORIGINAL)
    PCA_COMPONENTS = 50
    n_components = min(PCA_COMPONENTS, normalized_matrix.shape[0] - 1, normalized_matrix.shape[1])
    log_progress(f"Applying PCA with {n_components} components")
    
    pca = PCA(n_components=n_components, random_state=42)
    pca_result = pca.fit_transform(normalized_matrix)
    pca_df = pd.DataFrame(pca_result, index=normalized_matrix.index)
    
    variance_explained = pca.explained_variance_ratio_.sum()
    log_progress(f"PCA variance explained: {variance_explained:.2%}")
    
    # Determine cluster count (ORIGINAL logic: n_samples // 50)
    n_samples = pca_df.shape[0]
    n_clusters = n_samples // 50
    if n_samples % 50 != 0:
        n_clusters += 1
    log_progress(f"Cluster count: {n_clusters} (n_samples={n_samples} // 50)")
    
    # KMeans clustering (ORIGINAL)
    log_progress(f"Running KMeans with {n_clusters} clusters...")
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10,
        max_iter=300
    )
    labels = kmeans.fit_predict(pca_df)
    
    # Calculate metrics
    log_progress("\n--- Baseline Metrics ---")
    silhouette = silhouette_score(pca_df, labels)
    calinski = calinski_harabasz_score(pca_df, labels)
    davies = davies_bouldin_score(pca_df, labels)
    
    # Cluster size distribution
    unique, counts = np.unique(labels, return_counts=True)
    
    metrics = {
        'period': PERIOD,
        'run_type': 'BASELINE',
        'run_timestamp': datetime.now().isoformat(),
        'data': {
            'n_stores': n_samples,
            'n_spus': len(top_spus),
            'spu_records': len(spu_sales)
        },
        'step3_config': {
            'normalization': 'row-wise (div by row sum)',
            'max_spu_count': MAX_SPU_COUNT
        },
        'step6_config': {
            'pca_components': n_components,
            'cluster_determination': 'n_samples // 50',
            'n_clusters': n_clusters,
            'random_state': 42,
            'n_init': 10,
            'max_iter': 300,
            'store_features_used': False
        },
        'clustering_metrics': {
            'silhouette_score': round(silhouette, 4),
            'calinski_harabasz_score': round(calinski, 2),
            'davies_bouldin_score': round(davies, 4)
        },
        'cluster_distribution': {
            'min_size': int(counts.min()),
            'max_size': int(counts.max()),
            'mean_size': round(counts.mean(), 1),
            'std_size': round(counts.std(), 1)
        },
        'pca_variance_explained': round(variance_explained, 4)
    }
    
    log_progress(f"\nSilhouette Score: {silhouette:.4f}")
    log_progress(f"Calinski-Harabasz Score: {calinski:.2f}")
    log_progress(f"Davies-Bouldin Score: {davies:.4f}")
    log_progress(f"Cluster sizes: min={counts.min()}, max={counts.max()}, mean={counts.mean():.1f}")
    
    # Save results
    results_df = pd.DataFrame({
        'str_code': normalized_matrix.index,
        'Cluster': labels
    })
    
    return metrics, results_df, pca_df, labels


def save_baseline_results(metrics: dict, results_df: pd.DataFrame):
    """Save baseline results to files."""
    # Save metrics JSON
    metrics_file = REPORTS_DIR / 'BASELINE_METRICS_202506A.json'
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    log_progress(f"Saved metrics to: {metrics_file}")
    
    # Save clustering results
    results_file = REPORTS_DIR / 'baseline_clustering_results_202506A.csv'
    results_df.to_csv(results_file, index=False)
    log_progress(f"Saved results to: {results_file}")


def main():
    """Main entry point."""
    log_progress("Starting Baseline Clustering Run...")
    
    metrics, results_df, pca_df, labels = run_baseline_clustering()
    save_baseline_results(metrics, results_df)
    
    log_progress("\n" + "=" * 70)
    log_progress("BASELINE RUN COMPLETE")
    log_progress("=" * 70)
    log_progress("\nKey Baseline Metrics:")
    log_progress(f"  Silhouette Score: {metrics['clustering_metrics']['silhouette_score']}")
    log_progress(f"  Calinski-Harabasz: {metrics['clustering_metrics']['calinski_harabasz_score']}")
    log_progress(f"  Davies-Bouldin: {metrics['clustering_metrics']['davies_bouldin_score']}")
    log_progress(f"  Clusters: {metrics['step6_config']['n_clusters']}")
    log_progress(f"  Stores: {metrics['data']['n_stores']}")
    log_progress("\nConfiguration (ORIGINAL):")
    log_progress(f"  Normalization: {metrics['step3_config']['normalization']}")
    log_progress(f"  Cluster Count: {metrics['step6_config']['cluster_determination']}")
    log_progress(f"  Store Features: {metrics['step6_config']['store_features_used']}")
    
    return metrics


if __name__ == '__main__':
    main()
