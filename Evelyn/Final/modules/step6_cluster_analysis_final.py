#!/usr/bin/env python3
"""
Step 6: Final Optimized Cluster Analysis
=========================================

This module implements the FINAL optimized clustering pipeline with ALL improvements:

C3 Improvements (Baseline 1):
- I1: Store Profile Features (str_type, sal_type, traffic)
- I2: Fixed Cluster Count (30 clusters)

Final Improvements (A + B + C):
- A: Block-wise Feature Architecture (separate PCA per block)
- B: Alternative Normalization (log-transform + row normalization)
- C: Algorithm Optimization (L2 normalization + optimized KMeans)

Expected Results:
- Silhouette Score: ~0.3754 (vs 0.0478 baseline = +685% improvement)
- Cluster Count: 30 (compliant with 20-40 requirement)
- Cluster Size Range: 26-177 (well-balanced)

Author: Fast Fish Data Science Team
Date: 2026-01
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
import os
from typing import Tuple, Dict, Optional
from datetime import datetime
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

# Cluster Configuration (I2: Fixed at 30)
N_CLUSTERS = 30

# Block-wise PCA Configuration (Improvement A)
SPU_PCA_COMPONENTS = 30
SPU_WEIGHT = 0.7
STORE_WEIGHT = 0.3

# KMeans Optimization (Improvement C)
KMEANS_N_INIT = 20
KMEANS_MAX_ITER = 500
RANDOM_STATE = 42

# Feature Configuration
TOP_SPU_COUNT = 1000


def log_progress(message: str) -> None:
    """Log progress with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


# =============================================================================
# DATA LOADING
# =============================================================================

def load_spu_sales(data_path: Path, period: str) -> pd.DataFrame:
    """Load SPU sales data."""
    spu_file = data_path / f'complete_spu_sales_{period}.csv'
    spu_sales = pd.read_csv(spu_file)
    spu_sales['str_code'] = spu_sales['str_code'].astype(str)
    spu_sales['spu_code'] = spu_sales['spu_code'].astype(str)
    log_progress(f"Loaded {len(spu_sales):,} SPU records")
    return spu_sales


def load_store_sales(data_path: Path, period: str) -> pd.DataFrame:
    """Load store sales data with store features."""
    store_file = data_path / f'store_sales_{period}.csv'
    store_sales = pd.read_csv(store_file)
    store_sales['str_code'] = store_sales['str_code'].astype(str)
    log_progress(f"Loaded {store_sales['str_code'].nunique()} stores")
    return store_sales


# =============================================================================
# IMPROVEMENT B: ALTERNATIVE NORMALIZATION
# =============================================================================

def create_spu_matrix_with_log_normalization(spu_sales: pd.DataFrame) -> pd.DataFrame:
    """
    Create SPU matrix with Improvement B: Log-transform + Row Normalization.
    
    This reduces skewness from high-volume SPUs and focuses on product mix patterns.
    """
    log_progress("Creating SPU matrix with log-transform normalization (Improvement B)...")
    
    # Create pivot matrix
    matrix = spu_sales.pivot_table(
        index='str_code',
        columns='spu_code',
        values='spu_sales_amt',
        aggfunc='sum',
        fill_value=0
    )
    
    # Keep top SPUs by total sales
    top_spus = matrix.sum().nlargest(TOP_SPU_COUNT).index
    matrix = matrix[top_spus]
    
    # Improvement B: Log-transform to reduce skewness
    log_matrix = np.log1p(matrix)
    
    # Row-wise normalization (focus on mix, not volume)
    normalized = log_matrix.div(log_matrix.sum(axis=1), axis=0).fillna(0)
    
    log_progress(f"  Matrix shape: {normalized.shape}")
    return normalized


# =============================================================================
# IMPROVEMENT I1: STORE PROFILE FEATURES
# =============================================================================

def encode_store_features(store_sales: pd.DataFrame) -> pd.DataFrame:
    """
    Encode store features (Improvement I1).
    
    Features:
    - str_type: Binary (流行=1, 基础=0)
    - sal_type: Ordinal (AA=5, A=4, B=3, C=2, D=1)
    - traffic: Min-max normalized
    - temperature: Min-max normalized
    """
    log_progress("Encoding store features (Improvement I1)...")
    
    # Get unique stores
    store_unique = store_sales.drop_duplicates(subset='str_code', keep='first')
    
    # Extract features
    features = store_unique.set_index('str_code')[
        ['str_type', 'sal_type', 'into_str_cnt_avg', 'avg_temp']
    ].copy()
    
    # Binary encoding for str_type
    features['str_type_enc'] = (features['str_type'] == '流行').astype(float)
    
    # Ordinal encoding for sal_type
    grade_map = {'AA': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1}
    features['sal_type_enc'] = features['sal_type'].map(grade_map).fillna(2)
    
    # Min-max normalize traffic
    traffic = features['into_str_cnt_avg'].fillna(0)
    features['traffic_norm'] = (traffic - traffic.min()) / (traffic.max() - traffic.min() + 1e-10)
    
    # Min-max normalize temperature
    temp = features['avg_temp'].fillna(features['avg_temp'].median())
    features['temp_norm'] = (temp - temp.min()) / (temp.max() - temp.min() + 1e-10)
    
    result = features[['str_type_enc', 'sal_type_enc', 'traffic_norm', 'temp_norm']]
    log_progress(f"  Encoded {len(result)} stores with 4 features")
    
    return result


# =============================================================================
# IMPROVEMENT A: BLOCK-WISE PCA ARCHITECTURE
# =============================================================================

def apply_blockwise_pca(
    spu_matrix: pd.DataFrame,
    store_features: pd.DataFrame
) -> Tuple[np.ndarray, pd.Index, Dict]:
    """
    Apply block-wise PCA (Improvement A).
    
    Block 1: SPU Mix -> PCA to 30 components (70% weight)
    Block 2: Store Profile -> Standardize, keep all 4 features (30% weight)
    """
    log_progress("Applying block-wise PCA (Improvement A)...")
    
    # Align indices
    common_stores = spu_matrix.index.intersection(store_features.index)
    spu_block = spu_matrix.loc[common_stores]
    store_block = store_features.loc[common_stores]
    
    log_progress(f"  Common stores: {len(common_stores)}")
    
    # Block 1: SPU features -> PCA
    pca_spu = PCA(n_components=SPU_PCA_COMPONENTS, random_state=RANDOM_STATE)
    spu_pca = pca_spu.fit_transform(spu_block)
    spu_variance = pca_spu.explained_variance_ratio_.sum()
    log_progress(f"  SPU Block: {spu_block.shape[1]} -> {SPU_PCA_COMPONENTS} components ({spu_variance:.1%} variance)")
    
    # Block 2: Store features -> Standardize
    scaler = StandardScaler()
    store_scaled = scaler.fit_transform(store_block)
    log_progress(f"  Store Block: {store_block.shape[1]} features (standardized)")
    
    # Combine with weighting
    spu_weighted = spu_pca * SPU_WEIGHT
    store_weighted = store_scaled * STORE_WEIGHT
    combined = np.hstack([spu_weighted, store_weighted])
    
    log_progress(f"  Combined: {combined.shape[1]} features ({SPU_PCA_COMPONENTS} SPU + 4 Store)")
    
    metadata = {
        'spu_variance_explained': spu_variance,
        'spu_components': SPU_PCA_COMPONENTS,
        'store_features': 4,
        'total_features': combined.shape[1],
        'n_stores': len(common_stores)
    }
    
    return combined, common_stores, metadata


# =============================================================================
# IMPROVEMENT C: ALGORITHM OPTIMIZATION
# =============================================================================

def perform_optimized_clustering(
    features: np.ndarray,
    store_index: pd.Index
) -> Tuple[np.ndarray, pd.DataFrame, Dict]:
    """
    Perform optimized KMeans clustering (Improvement C).
    
    - L2 normalization for cosine-style distance
    - Increased n_init for stability
    - More iterations for convergence
    """
    log_progress("Performing optimized clustering (Improvement C)...")
    
    # L2 normalize for cosine-style behavior
    features_l2 = normalize(features, norm='l2')
    log_progress("  Applied L2 normalization")
    
    # Create DataFrame for metrics
    features_df = pd.DataFrame(features_l2, index=store_index)
    
    # Optimized KMeans
    kmeans = KMeans(
        n_clusters=N_CLUSTERS,
        random_state=RANDOM_STATE,
        n_init=KMEANS_N_INIT,
        max_iter=KMEANS_MAX_ITER,
        algorithm='lloyd'
    )
    labels = kmeans.fit_predict(features_df)
    
    log_progress(f"  KMeans: n_clusters={N_CLUSTERS}, n_init={KMEANS_N_INIT}, max_iter={KMEANS_MAX_ITER}")
    
    # Calculate metrics
    silhouette = silhouette_score(features_df, labels)
    calinski = calinski_harabasz_score(features_df, labels)
    davies = davies_bouldin_score(features_df, labels)
    
    unique, counts = np.unique(labels, return_counts=True)
    
    metrics = {
        'silhouette_score': round(silhouette, 4),
        'calinski_harabasz': round(calinski, 2),
        'davies_bouldin': round(davies, 4),
        'n_clusters': N_CLUSTERS,
        'cluster_sizes': {
            'min': int(counts.min()),
            'max': int(counts.max()),
            'mean': round(counts.mean(), 1),
            'std': round(counts.std(), 1)
        }
    }
    
    log_progress(f"  Silhouette: {silhouette:.4f}")
    log_progress(f"  Cluster sizes: {counts.min()}-{counts.max()} (mean: {counts.mean():.1f})")
    
    return labels, features_df, metrics


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_final_clustering(
    data_path: Path,
    period: str,
    output_path: Optional[Path] = None
) -> Dict:
    """
    Run the complete final optimized clustering pipeline.
    
    Implements ALL improvements:
    - I1: Store Profile Features
    - I2: Fixed Cluster Count (30)
    - A: Block-wise PCA Architecture
    - B: Log-transform + Row Normalization
    - C: L2 Normalization + Optimized KMeans
    
    Args:
        data_path: Path to data directory
        period: Period code (e.g., '202506A')
        output_path: Optional path for output files
        
    Returns:
        Dictionary with results and metrics
    """
    log_progress("="*70)
    log_progress("FINAL OPTIMIZED CLUSTERING PIPELINE")
    log_progress("="*70)
    log_progress(f"Period: {period}")
    log_progress(f"Improvements: I1 + I2 + A + B + C")
    log_progress("="*70)
    
    # Load data
    spu_sales = load_spu_sales(data_path, period)
    store_sales = load_store_sales(data_path, period)
    
    # Improvement B: Create SPU matrix with log normalization
    spu_matrix = create_spu_matrix_with_log_normalization(spu_sales)
    
    # Improvement I1: Encode store features
    store_features = encode_store_features(store_sales)
    
    # Improvement A: Block-wise PCA
    combined_features, store_index, pca_metadata = apply_blockwise_pca(
        spu_matrix, store_features
    )
    
    # Improvement C: Optimized clustering
    labels, features_df, clustering_metrics = perform_optimized_clustering(
        combined_features, store_index
    )
    
    # Create results DataFrame
    results_df = pd.DataFrame({
        'str_code': store_index,
        'cluster': labels
    })
    
    # Save results if output path provided
    if output_path:
        output_path.mkdir(parents=True, exist_ok=True)
        results_file = output_path / f'clustering_results_final_{period}.csv'
        results_df.to_csv(results_file, index=False)
        log_progress(f"Saved results to {results_file}")
    
    # Summary
    log_progress("\n" + "="*70)
    log_progress("CLUSTERING COMPLETE")
    log_progress("="*70)
    log_progress(f"Silhouette Score: {clustering_metrics['silhouette_score']:.4f}")
    log_progress(f"Clusters: {clustering_metrics['n_clusters']}")
    log_progress(f"Size Range: {clustering_metrics['cluster_sizes']['min']}-{clustering_metrics['cluster_sizes']['max']}")
    
    return {
        'period': period,
        'results': results_df,
        'features': features_df,
        'labels': labels,
        'metrics': clustering_metrics,
        'pca_metadata': pca_metadata,
        'improvements': ['I1', 'I2', 'A', 'B', 'C']
    }


if __name__ == '__main__':
    # Example usage
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    DATA_PATH = PROJECT_ROOT / 'docs' / 'Data' / 'step1_api_data_20250917_142743'
    OUTPUT_PATH = PROJECT_ROOT / 'Evelyn' / 'Final' / 'output'
    
    results = run_final_clustering(DATA_PATH, '202506A', OUTPUT_PATH)
    print(f"\nFinal Silhouette: {results['metrics']['silhouette_score']}")
