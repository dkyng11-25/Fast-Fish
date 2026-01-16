#!/usr/bin/env python3
"""
Final Pipeline Runner
=====================

This script runs the complete final optimized clustering pipeline and generates
all visualizations for the executive report.

Usage:
    python run_final_pipeline.py

Output:
    - Clustering results CSV
    - Metrics JSON
    - All visualizations (PNG)

Author: Fast Fish Data Science Team
Date: 2026-01
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.metrics import silhouette_samples
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, normalize
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import warnings
warnings.filterwarnings('ignore')

# Path configuration
SCRIPT_DIR = Path(__file__).parent
FINAL_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = FINAL_DIR.parent.parent
DATA_PATH = PROJECT_ROOT / 'docs' / 'Data' / 'step1_api_data_20250917_142743'
OUTPUT_DIR = FINAL_DIR / 'output'
FIGURES_DIR = FINAL_DIR / 'figures'

PERIOD = '202506A'

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def log_progress(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def load_data():
    """Load all required data files."""
    log_progress("Loading data files...")
    
    spu_file = DATA_PATH / f'complete_spu_sales_{PERIOD}.csv'
    spu_sales = pd.read_csv(spu_file)
    spu_sales['str_code'] = spu_sales['str_code'].astype(str)
    spu_sales['spu_code'] = spu_sales['spu_code'].astype(str)
    
    store_file = DATA_PATH / f'store_sales_{PERIOD}.csv'
    store_sales = pd.read_csv(store_file)
    store_sales['str_code'] = store_sales['str_code'].astype(str)
    
    log_progress(f"Loaded {len(spu_sales):,} SPU records, {spu_sales['str_code'].nunique()} stores")
    return spu_sales, store_sales


def run_baseline_0(spu_sales):
    """Baseline 0: Original pipeline (no improvements)."""
    log_progress("\n" + "="*70)
    log_progress("BASELINE 0: Original (No Improvements)")
    log_progress("="*70)
    
    matrix = spu_sales.pivot_table(
        index='str_code', columns='spu_code', values='spu_sales_amt',
        aggfunc='sum', fill_value=0
    )
    top_spus = matrix.sum().nlargest(1000).index
    matrix = matrix[top_spus]
    normalized = matrix.div(matrix.sum(axis=1), axis=0).fillna(0)
    
    pca = PCA(n_components=50, random_state=42)
    pca_result = pca.fit_transform(normalized)
    pca_df = pd.DataFrame(pca_result, index=normalized.index)
    
    n_clusters = len(pca_df) // 50 + 1
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(pca_df)
    
    silhouette = silhouette_score(pca_df, labels)
    calinski = calinski_harabasz_score(pca_df, labels)
    davies = davies_bouldin_score(pca_df, labels)
    unique, counts = np.unique(labels, return_counts=True)
    
    metrics = {
        'stage': 'Baseline 0 (Original)',
        'silhouette': round(silhouette, 4),
        'calinski_harabasz': round(calinski, 2),
        'davies_bouldin': round(davies, 4),
        'n_clusters': n_clusters,
        'cluster_sizes': {'min': int(counts.min()), 'max': int(counts.max()), 'mean': round(counts.mean(), 1)},
        'pca_variance': round(pca.explained_variance_ratio_.sum(), 4)
    }
    
    log_progress(f"Silhouette: {silhouette:.4f}, Clusters: {n_clusters}")
    return metrics, pca_df, labels


def run_baseline_1_c3(spu_sales, store_sales):
    """Baseline 1 (C3): Row norm + 30 clusters + store features."""
    log_progress("\n" + "="*70)
    log_progress("BASELINE 1 (C3): Row Norm + 30 Clusters + Store Features")
    log_progress("="*70)
    
    matrix = spu_sales.pivot_table(
        index='str_code', columns='spu_code', values='spu_sales_amt',
        aggfunc='sum', fill_value=0
    )
    top_spus = matrix.sum().nlargest(1000).index
    matrix = matrix[top_spus]
    normalized = matrix.div(matrix.sum(axis=1), axis=0).fillna(0)
    
    store_unique = store_sales.drop_duplicates(subset='str_code', keep='first')
    store_features = store_unique.set_index('str_code')[['str_type', 'sal_type', 'into_str_cnt_avg']].copy()
    store_features['str_type_enc'] = (store_features['str_type'] == '流行').astype(float)
    grade_map = {'AA': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1}
    store_features['sal_type_enc'] = store_features['sal_type'].map(grade_map).fillna(2)
    traffic = store_features['into_str_cnt_avg'].fillna(0)
    store_features['traffic_norm'] = (traffic - traffic.min()) / (traffic.max() - traffic.min() + 1e-10)
    
    common = normalized.index.intersection(store_features.index)
    enhanced = normalized.loc[common].copy()
    sf = store_features.loc[common]
    enhanced['STORE_type'] = sf['str_type_enc'].values
    enhanced['STORE_grade'] = sf['sal_type_enc'].values
    enhanced['STORE_traffic'] = sf['traffic_norm'].values
    
    pca = PCA(n_components=50, random_state=42)
    pca_result = pca.fit_transform(enhanced)
    pca_df = pd.DataFrame(pca_result, index=enhanced.index)
    
    n_clusters = 30
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(pca_df)
    
    silhouette = silhouette_score(pca_df, labels)
    calinski = calinski_harabasz_score(pca_df, labels)
    davies = davies_bouldin_score(pca_df, labels)
    unique, counts = np.unique(labels, return_counts=True)
    
    metrics = {
        'stage': 'Baseline 1 (C3)',
        'silhouette': round(silhouette, 4),
        'calinski_harabasz': round(calinski, 2),
        'davies_bouldin': round(davies, 4),
        'n_clusters': n_clusters,
        'cluster_sizes': {'min': int(counts.min()), 'max': int(counts.max()), 'mean': round(counts.mean(), 1)},
        'pca_variance': round(pca.explained_variance_ratio_.sum(), 4)
    }
    
    log_progress(f"Silhouette: {silhouette:.4f}, Clusters: {n_clusters}")
    return metrics, pca_df, labels


def run_final_improvements(spu_sales, store_sales):
    """Final: All improvements A + B + C combined."""
    log_progress("\n" + "="*70)
    log_progress("FINAL: Improvements A + B + C Combined")
    log_progress("="*70)
    
    # Improvement B: Log-transform + Row Normalization
    matrix = spu_sales.pivot_table(
        index='str_code', columns='spu_code', values='spu_sales_amt',
        aggfunc='sum', fill_value=0
    )
    top_spus = matrix.sum().nlargest(1000).index
    matrix = matrix[top_spus]
    log_matrix = np.log1p(matrix)
    spu_normalized = log_matrix.div(log_matrix.sum(axis=1), axis=0).fillna(0)
    
    # Store features with temperature
    store_unique = store_sales.drop_duplicates(subset='str_code', keep='first')
    store_features = store_unique.set_index('str_code')[['str_type', 'sal_type', 'into_str_cnt_avg', 'avg_temp']].copy()
    store_features['str_type_enc'] = (store_features['str_type'] == '流行').astype(float)
    grade_map = {'AA': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1}
    store_features['sal_type_enc'] = store_features['sal_type'].map(grade_map).fillna(2)
    traffic = store_features['into_str_cnt_avg'].fillna(0)
    store_features['traffic_norm'] = (traffic - traffic.min()) / (traffic.max() - traffic.min() + 1e-10)
    temp = store_features['avg_temp'].fillna(store_features['avg_temp'].median())
    store_features['temp_norm'] = (temp - temp.min()) / (temp.max() - temp.min() + 1e-10)
    
    common = spu_normalized.index.intersection(store_features.index)
    spu_block = spu_normalized.loc[common]
    store_block = store_features.loc[common][['str_type_enc', 'sal_type_enc', 'traffic_norm', 'temp_norm']]
    
    # Improvement A: Block-wise PCA
    pca_spu = PCA(n_components=30, random_state=42)
    spu_pca = pca_spu.fit_transform(spu_block)
    
    scaler_store = StandardScaler()
    store_scaled = scaler_store.fit_transform(store_block)
    
    spu_weighted = spu_pca * 0.7
    store_weighted = store_scaled * 0.3
    combined = np.hstack([spu_weighted, store_weighted])
    
    # Improvement C: L2 Normalization + Optimized KMeans
    combined_l2 = normalize(combined, norm='l2')
    combined_df = pd.DataFrame(combined_l2, index=common)
    
    n_clusters = 30
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=20, max_iter=500, algorithm='lloyd')
    labels = kmeans.fit_predict(combined_df)
    
    silhouette = silhouette_score(combined_df, labels)
    calinski = calinski_harabasz_score(combined_df, labels)
    davies = davies_bouldin_score(combined_df, labels)
    unique, counts = np.unique(labels, return_counts=True)
    
    metrics = {
        'stage': 'Final (A+B+C)',
        'silhouette': round(silhouette, 4),
        'calinski_harabasz': round(calinski, 2),
        'davies_bouldin': round(davies, 4),
        'n_clusters': n_clusters,
        'cluster_sizes': {'min': int(counts.min()), 'max': int(counts.max()), 'mean': round(counts.mean(), 1)},
        'improvements': {
            'A': 'Block-wise PCA (SPU 30 + Store 4)',
            'B': 'Log-transform + Row Normalization',
            'C': 'L2 Normalization + Optimized KMeans (n_init=20)'
        }
    }
    
    log_progress(f"Silhouette: {silhouette:.4f}, Clusters: {n_clusters}")
    return metrics, combined_df, labels


def generate_visualizations(results):
    """Generate all visualizations."""
    log_progress("\n" + "="*70)
    log_progress("Generating Visualizations")
    log_progress("="*70)
    
    stages = ['baseline0', 'c3', 'final']
    stage_names = ['Baseline 0 (Original)', 'Baseline 1 (C3)', 'Final (A+B+C)']
    colors = ['#e74c3c', '#f39c12', '#27ae60']
    
    # 1. PCA Visualization
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for idx, stage in enumerate(stages):
        pca_df = results[stage]['pca_df']
        labels = results[stage]['labels']
        metrics = results[stage]['metrics']
        
        pca_2d = PCA(n_components=2, random_state=42)
        coords = pca_2d.fit_transform(pca_df)
        
        ax = axes[idx]
        ax.scatter(coords[:, 0], coords[:, 1], c=labels, cmap='tab20', alpha=0.6, s=10)
        ax.set_title(f"{stage_names[idx]}\nSilhouette: {metrics['silhouette']:.4f}", fontsize=12, fontweight='bold')
        ax.set_xlabel('PC1')
        ax.set_ylabel('PC2')
        ax.grid(True, alpha=0.3)
    
    plt.suptitle('PCA Cluster Visualization: Store Clustering Progression', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'pca_visualization_all_stages.png', dpi=150, bbox_inches='tight')
    plt.close()
    log_progress("  Saved: pca_visualization_all_stages.png")
    
    # 2. Cluster Size Distribution
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for idx, stage in enumerate(stages):
        labels = results[stage]['labels']
        unique, counts = np.unique(labels, return_counts=True)
        
        ax = axes[idx]
        ax.bar(range(len(counts)), sorted(counts, reverse=True), color=colors[idx], alpha=0.7)
        ax.axhline(y=np.mean(counts), color='black', linestyle='--', label=f'Mean: {np.mean(counts):.1f}')
        ax.set_title(f"{stage_names[idx]}\n{len(unique)} clusters, range: {counts.min()}-{counts.max()}", fontsize=11, fontweight='bold')
        ax.set_xlabel('Cluster Rank')
        ax.set_ylabel('Store Count')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.suptitle('Cluster Size Distribution: Balance Comparison', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'cluster_size_distribution.png', dpi=150, bbox_inches='tight')
    plt.close()
    log_progress("  Saved: cluster_size_distribution.png")
    
    # 3. Silhouette Comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    silhouettes = [results[s]['metrics']['silhouette'] for s in stages]
    bars = ax.bar(stage_names, silhouettes, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    for bar, val in zip(bars, silhouettes):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                f'{val:.4f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    ax.set_ylabel('Silhouette Score', fontsize=12)
    ax.set_title('Silhouette Score Progression Across Improvement Stages', fontsize=14, fontweight='bold')
    ax.set_ylim(0, max(silhouettes) * 1.2)
    ax.axhline(y=0.5, color='green', linestyle=':', alpha=0.7, label='Target (0.5)')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'silhouette_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    log_progress("  Saved: silhouette_comparison.png")
    
    # 4. Per-Cluster Silhouette
    fig, ax = plt.subplots(figsize=(12, 8))
    pca_df = results['final']['pca_df']
    labels = results['final']['labels']
    sample_silhouettes = silhouette_samples(pca_df, labels)
    n_clusters = len(np.unique(labels))
    
    y_lower = 10
    for i in range(n_clusters):
        cluster_silhouettes = sample_silhouettes[labels == i]
        cluster_silhouettes.sort()
        size = len(cluster_silhouettes)
        y_upper = y_lower + size
        color = plt.cm.tab20(i / n_clusters)
        ax.fill_betweenx(np.arange(y_lower, y_upper), 0, cluster_silhouettes, 
                         facecolor=color, edgecolor=color, alpha=0.7)
        ax.text(-0.05, y_lower + 0.5 * size, str(i), fontsize=8)
        y_lower = y_upper + 10
    
    avg_silhouette = np.mean(sample_silhouettes)
    ax.axvline(x=avg_silhouette, color='red', linestyle='--', linewidth=2, label=f'Average: {avg_silhouette:.4f}')
    ax.set_title('Per-Cluster Silhouette Analysis (Final Stage)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Silhouette Coefficient', fontsize=12)
    ax.set_ylabel('Cluster', fontsize=12)
    ax.legend(loc='upper right')
    ax.set_xlim(-0.1, 1)
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'silhouette_per_cluster.png', dpi=150, bbox_inches='tight')
    plt.close()
    log_progress("  Saved: silhouette_per_cluster.png")
    
    # 5. Metrics Summary Table
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis('off')
    
    table_data = [['Stage', 'Silhouette', 'Calinski-Harabasz', 'Davies-Bouldin', 'Clusters', 'Size Range']]
    for stage, name in zip(stages, stage_names):
        m = results[stage]['metrics']
        table_data.append([
            name, f"{m['silhouette']:.4f}", f"{m['calinski_harabasz']:.1f}",
            f"{m['davies_bouldin']:.4f}", str(m['n_clusters']),
            f"{m['cluster_sizes']['min']}-{m['cluster_sizes']['max']}"
        ])
    
    table = ax.table(cellText=table_data, loc='center', cellLoc='center',
                     colWidths=[0.25, 0.12, 0.18, 0.15, 0.1, 0.12])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 1.8)
    
    for j in range(6):
        table[(0, j)].set_facecolor('#3498db')
        table[(0, j)].set_text_props(color='white', fontweight='bold')
    table[(3, 1)].set_facecolor('#27ae60')
    table[(3, 1)].set_text_props(color='white', fontweight='bold')
    
    plt.title('Clustering Metrics Comparison Summary', fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'metrics_summary_table.png', dpi=150, bbox_inches='tight')
    plt.close()
    log_progress("  Saved: metrics_summary_table.png")


def save_results(results):
    """Save metrics and results."""
    final_metrics = {
        'generated': datetime.now().isoformat(),
        'period': PERIOD,
        'stages': {stage: results[stage]['metrics'] for stage in ['baseline0', 'c3', 'final']}
    }
    
    b0 = results['baseline0']['metrics']['silhouette']
    c3 = results['c3']['metrics']['silhouette']
    final = results['final']['metrics']['silhouette']
    
    final_metrics['improvements'] = {
        'baseline0_to_c3': {'absolute': round(c3 - b0, 4), 'percent': round((c3 - b0) / b0 * 100, 1)},
        'c3_to_final': {'absolute': round(final - c3, 4), 'percent': round((final - c3) / c3 * 100, 1)},
        'baseline0_to_final': {'absolute': round(final - b0, 4), 'percent': round((final - b0) / b0 * 100, 1)}
    }
    
    with open(OUTPUT_DIR / 'FINAL_METRICS_ALL_STAGES.json', 'w') as f:
        json.dump(final_metrics, f, indent=2)
    
    # Save clustering results
    final_results = pd.DataFrame({
        'str_code': results['final']['pca_df'].index,
        'cluster': results['final']['labels']
    })
    final_results.to_csv(OUTPUT_DIR / f'clustering_results_final_{PERIOD}.csv', index=False)
    
    log_progress(f"Saved metrics and results to {OUTPUT_DIR}")
    return final_metrics


def main():
    """Main entry point."""
    log_progress("="*70)
    log_progress("FINAL PIPELINE RUNNER")
    log_progress("="*70)
    
    spu_sales, store_sales = load_data()
    
    results = {}
    m0, pca0, labels0 = run_baseline_0(spu_sales)
    results['baseline0'] = {'metrics': m0, 'pca_df': pca0, 'labels': labels0}
    
    m1, pca1, labels1 = run_baseline_1_c3(spu_sales, store_sales)
    results['c3'] = {'metrics': m1, 'pca_df': pca1, 'labels': labels1}
    
    m2, pca2, labels2 = run_final_improvements(spu_sales, store_sales)
    results['final'] = {'metrics': m2, 'pca_df': pca2, 'labels': labels2}
    
    generate_visualizations(results)
    final_metrics = save_results(results)
    
    log_progress("\n" + "="*70)
    log_progress("COMPLETE - SUMMARY")
    log_progress("="*70)
    print(f"\nImprovement: Baseline 0 → Final: +{final_metrics['improvements']['baseline0_to_final']['percent']:.1f}%")
    print(f"Final Silhouette: {results['final']['metrics']['silhouette']:.4f}")
    
    return results


if __name__ == '__main__':
    main()
