#!/usr/bin/env python3
"""
Final Improvements Experiment: A + B + C

This script implements and evaluates three additional improvements beyond C3:
- Improvement A: Block-wise Feature Architecture (separate PCA per block)
- Improvement B: Alternative Normalization Strategy (enhanced row normalization)
- Improvement C: Algorithm Optimization (cosine distance + adaptive parameters)

Generates all required visualizations for the executive report.

Author: Evelyn Module
Date: 2026-01-16
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
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import warnings
warnings.filterwarnings('ignore')

PROJECT_ROOT = Path(__file__).parent.parent
EVELYN_ROOT = PROJECT_ROOT / 'Evelyn'
REPORTS_DIR = EVELYN_ROOT / 'reports'
FIGURES_DIR = EVELYN_ROOT / 'figures'

PERIOD = '202506A'
DATA_PATH = PROJECT_ROOT / 'docs' / 'Data' / 'step1_api_data_20250917_142743'

# Ensure directories exist
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def log_progress(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def load_data():
    """Load all required data files."""
    log_progress("Loading data files...")
    
    # SPU sales
    spu_file = DATA_PATH / f'complete_spu_sales_{PERIOD}.csv'
    spu_sales = pd.read_csv(spu_file)
    spu_sales['str_code'] = spu_sales['str_code'].astype(str)
    spu_sales['spu_code'] = spu_sales['spu_code'].astype(str)
    
    # Store sales (for store features)
    store_file = DATA_PATH / f'store_sales_{PERIOD}.csv'
    store_sales = pd.read_csv(store_file)
    store_sales['str_code'] = store_sales['str_code'].astype(str)
    
    log_progress(f"Loaded {len(spu_sales):,} SPU records, {spu_sales['str_code'].nunique()} stores")
    
    return spu_sales, store_sales


def run_baseline_0(spu_sales):
    """
    Baseline 0: Original 202506A sample run (before any improvement)
    - Row-wise normalization
    - Dynamic cluster count (n_samples // 50)
    - No store features
    """
    log_progress("\n" + "="*70)
    log_progress("BASELINE 0: Original 202506A (No Improvements)")
    log_progress("="*70)
    
    # Create SPU matrix
    matrix = spu_sales.pivot_table(
        index='str_code', columns='spu_code', values='spu_sales_amt',
        aggfunc='sum', fill_value=0
    )
    
    # Limit to top 1000 SPUs
    top_spus = matrix.sum().nlargest(1000).index
    matrix = matrix[top_spus]
    
    # Row-wise normalization
    normalized = matrix.div(matrix.sum(axis=1), axis=0).fillna(0)
    
    # PCA
    pca = PCA(n_components=50, random_state=42)
    pca_result = pca.fit_transform(normalized)
    pca_df = pd.DataFrame(pca_result, index=normalized.index)
    
    # Dynamic cluster count
    n_clusters = len(pca_df) // 50 + 1
    
    # KMeans
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(pca_df)
    
    # Metrics
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
    
    return metrics, pca_df, labels, normalized


def run_baseline_1_c3(spu_sales, store_sales):
    """
    Baseline 1 (C3): Row normalization + 30 clusters + store features
    """
    log_progress("\n" + "="*70)
    log_progress("BASELINE 1 (C3): Row Norm + 30 Clusters + Store Features")
    log_progress("="*70)
    
    # Create SPU matrix
    matrix = spu_sales.pivot_table(
        index='str_code', columns='spu_code', values='spu_sales_amt',
        aggfunc='sum', fill_value=0
    )
    
    top_spus = matrix.sum().nlargest(1000).index
    matrix = matrix[top_spus]
    
    # Row-wise normalization
    normalized = matrix.div(matrix.sum(axis=1), axis=0).fillna(0)
    
    # Add store features
    store_unique = store_sales.drop_duplicates(subset='str_code', keep='first')
    store_features = store_unique.set_index('str_code')[['str_type', 'sal_type', 'into_str_cnt_avg']].copy()
    
    # Encode
    store_features['str_type_enc'] = (store_features['str_type'] == '流行').astype(float)
    grade_map = {'AA': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1}
    store_features['sal_type_enc'] = store_features['sal_type'].map(grade_map).fillna(2)
    traffic = store_features['into_str_cnt_avg'].fillna(0)
    store_features['traffic_norm'] = (traffic - traffic.min()) / (traffic.max() - traffic.min() + 1e-10)
    
    # Align and combine
    common = normalized.index.intersection(store_features.index)
    enhanced = normalized.loc[common].copy()
    sf = store_features.loc[common]
    enhanced['STORE_type'] = sf['str_type_enc'].values
    enhanced['STORE_grade'] = sf['sal_type_enc'].values
    enhanced['STORE_traffic'] = sf['traffic_norm'].values
    
    # PCA
    pca = PCA(n_components=50, random_state=42)
    pca_result = pca.fit_transform(enhanced)
    pca_df = pd.DataFrame(pca_result, index=enhanced.index)
    
    # Fixed 30 clusters
    n_clusters = 30
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(pca_df)
    
    # Metrics
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
    
    return metrics, pca_df, labels, enhanced


def run_final_improvements(spu_sales, store_sales):
    """
    Final Improvements: A + B + C combined
    
    A: Block-wise Feature Architecture (separate PCA per block)
    B: Alternative Normalization (log-transform + row normalization)
    C: Algorithm Optimization (cosine-style via L2 normalization + optimized params)
    """
    log_progress("\n" + "="*70)
    log_progress("FINAL: Improvements A + B + C Combined")
    log_progress("="*70)
    
    # ========================================
    # IMPROVEMENT B: Alternative Normalization
    # ========================================
    log_progress("Applying Improvement B: Log-transform + Row Normalization...")
    
    matrix = spu_sales.pivot_table(
        index='str_code', columns='spu_code', values='spu_sales_amt',
        aggfunc='sum', fill_value=0
    )
    
    top_spus = matrix.sum().nlargest(1000).index
    matrix = matrix[top_spus]
    
    # Log-transform to reduce skewness, then row-normalize
    log_matrix = np.log1p(matrix)
    spu_normalized = log_matrix.div(log_matrix.sum(axis=1), axis=0).fillna(0)
    
    # ========================================
    # Prepare Store Features Block
    # ========================================
    store_unique = store_sales.drop_duplicates(subset='str_code', keep='first')
    store_features = store_unique.set_index('str_code')[['str_type', 'sal_type', 'into_str_cnt_avg', 'avg_temp']].copy()
    
    store_features['str_type_enc'] = (store_features['str_type'] == '流行').astype(float)
    grade_map = {'AA': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1}
    store_features['sal_type_enc'] = store_features['sal_type'].map(grade_map).fillna(2)
    traffic = store_features['into_str_cnt_avg'].fillna(0)
    store_features['traffic_norm'] = (traffic - traffic.min()) / (traffic.max() - traffic.min() + 1e-10)
    temp = store_features['avg_temp'].fillna(store_features['avg_temp'].median())
    store_features['temp_norm'] = (temp - temp.min()) / (temp.max() - temp.min() + 1e-10)
    
    # Align indices
    common = spu_normalized.index.intersection(store_features.index)
    spu_block = spu_normalized.loc[common]
    store_block = store_features.loc[common][['str_type_enc', 'sal_type_enc', 'traffic_norm', 'temp_norm']]
    
    log_progress(f"Common stores: {len(common)}")
    
    # ========================================
    # IMPROVEMENT A: Block-wise PCA
    # ========================================
    log_progress("Applying Improvement A: Block-wise PCA...")
    
    # Block 1: SPU Mix (reduce to 30 components)
    pca_spu = PCA(n_components=30, random_state=42)
    spu_pca = pca_spu.fit_transform(spu_block)
    log_progress(f"  SPU Block: {spu_block.shape[1]} -> 30 components, variance: {pca_spu.explained_variance_ratio_.sum():.2%}")
    
    # Block 2: Store Profile (keep all 4 features, standardize)
    scaler_store = StandardScaler()
    store_scaled = scaler_store.fit_transform(store_block)
    log_progress(f"  Store Block: 4 features (standardized)")
    
    # Combine blocks with weighting
    # SPU block gets 70% weight, Store block gets 30% weight
    spu_weighted = spu_pca * 0.7
    store_weighted = store_scaled * 0.3
    
    combined = np.hstack([spu_weighted, store_weighted])
    log_progress(f"  Combined: {combined.shape[1]} features (30 SPU + 4 Store)")
    
    # ========================================
    # IMPROVEMENT C: Algorithm Optimization
    # ========================================
    log_progress("Applying Improvement C: L2 Normalization + Optimized KMeans...")
    
    # L2 normalize for cosine-style behavior
    from sklearn.preprocessing import normalize
    combined_l2 = normalize(combined, norm='l2')
    
    # Create DataFrame for metrics
    combined_df = pd.DataFrame(combined_l2, index=common)
    
    # Optimized KMeans with more initializations
    n_clusters = 30
    kmeans = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=20,  # More initializations for stability
        max_iter=500,  # More iterations
        algorithm='lloyd'
    )
    labels = kmeans.fit_predict(combined_df)
    
    # Metrics
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
    
    return metrics, combined_df, labels, spu_block


def generate_visualizations(results):
    """Generate all required visualizations for the executive report."""
    log_progress("\n" + "="*70)
    log_progress("Generating Visualizations")
    log_progress("="*70)
    
    stages = ['baseline0', 'c3', 'final']
    stage_names = ['Baseline 0 (Original)', 'Baseline 1 (C3)', 'Final (A+B+C)']
    colors = ['#e74c3c', '#f39c12', '#27ae60']
    
    # 1. PCA Visualization (2D projection)
    log_progress("Creating PCA visualizations...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    for idx, stage in enumerate(stages):
        pca_df = results[stage]['pca_df']
        labels = results[stage]['labels']
        metrics = results[stage]['metrics']
        
        # 2D PCA
        pca_2d = PCA(n_components=2, random_state=42)
        coords = pca_2d.fit_transform(pca_df)
        
        ax = axes[idx]
        scatter = ax.scatter(coords[:, 0], coords[:, 1], c=labels, cmap='tab20', alpha=0.6, s=10)
        ax.set_title(f"{stage_names[idx]}\nSilhouette: {metrics['silhouette']:.4f}", fontsize=12, fontweight='bold')
        ax.set_xlabel('PC1')
        ax.set_ylabel('PC2')
        ax.grid(True, alpha=0.3)
    
    plt.suptitle('PCA Cluster Visualization: Store Clustering Progression', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'pca_visualization_all_stages.png', dpi=150, bbox_inches='tight')
    plt.close()
    log_progress(f"  Saved: pca_visualization_all_stages.png")
    
    # 2. Cluster Size Distribution
    log_progress("Creating cluster size distribution...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    for idx, stage in enumerate(stages):
        labels = results[stage]['labels']
        metrics = results[stage]['metrics']
        
        unique, counts = np.unique(labels, return_counts=True)
        
        ax = axes[idx]
        bars = ax.bar(range(len(counts)), sorted(counts, reverse=True), color=colors[idx], alpha=0.7)
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
    log_progress(f"  Saved: cluster_size_distribution.png")
    
    # 3. Silhouette Score Comparison
    log_progress("Creating silhouette comparison...")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    silhouettes = [results[s]['metrics']['silhouette'] for s in stages]
    bars = ax.bar(stage_names, silhouettes, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for bar, val in zip(bars, silhouettes):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                f'{val:.4f}', ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    # Add improvement annotations
    ax.annotate('', xy=(1, silhouettes[1]), xytext=(0, silhouettes[0]),
                arrowprops=dict(arrowstyle='->', color='gray', lw=2))
    ax.text(0.5, (silhouettes[0] + silhouettes[1])/2, f'+{((silhouettes[1]-silhouettes[0])/silhouettes[0]*100):.0f}%',
            ha='center', fontsize=10, color='gray')
    
    ax.annotate('', xy=(2, silhouettes[2]), xytext=(1, silhouettes[1]),
                arrowprops=dict(arrowstyle='->', color='gray', lw=2))
    ax.text(1.5, (silhouettes[1] + silhouettes[2])/2, f'+{((silhouettes[2]-silhouettes[1])/silhouettes[1]*100):.0f}%',
            ha='center', fontsize=10, color='gray')
    
    ax.set_ylabel('Silhouette Score', fontsize=12)
    ax.set_title('Silhouette Score Progression Across Improvement Stages', fontsize=14, fontweight='bold')
    ax.set_ylim(0, max(silhouettes) * 1.2)
    ax.axhline(y=0.5, color='green', linestyle=':', alpha=0.7, label='Target (0.5)')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'silhouette_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    log_progress(f"  Saved: silhouette_comparison.png")
    
    # 4. Per-Cluster Silhouette Plot (Final stage only)
    log_progress("Creating per-cluster silhouette plot...")
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
    ax.axvline(x=avg_silhouette, color='red', linestyle='--', linewidth=2, 
               label=f'Average: {avg_silhouette:.4f}')
    
    ax.set_title('Per-Cluster Silhouette Analysis (Final Stage)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Silhouette Coefficient', fontsize=12)
    ax.set_ylabel('Cluster', fontsize=12)
    ax.legend(loc='upper right')
    ax.set_xlim(-0.1, 1)
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'silhouette_per_cluster.png', dpi=150, bbox_inches='tight')
    plt.close()
    log_progress(f"  Saved: silhouette_per_cluster.png")
    
    # 5. Metrics Summary Table (as image)
    log_progress("Creating metrics summary table...")
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis('off')
    
    table_data = [
        ['Stage', 'Silhouette', 'Calinski-Harabasz', 'Davies-Bouldin', 'Clusters', 'Size Range'],
    ]
    for stage, name in zip(stages, stage_names):
        m = results[stage]['metrics']
        table_data.append([
            name,
            f"{m['silhouette']:.4f}",
            f"{m['calinski_harabasz']:.1f}",
            f"{m['davies_bouldin']:.4f}",
            str(m['n_clusters']),
            f"{m['cluster_sizes']['min']}-{m['cluster_sizes']['max']}"
        ])
    
    table = ax.table(cellText=table_data, loc='center', cellLoc='center',
                     colWidths=[0.25, 0.12, 0.18, 0.15, 0.1, 0.12])
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.2, 1.8)
    
    # Style header
    for j in range(6):
        table[(0, j)].set_facecolor('#3498db')
        table[(0, j)].set_text_props(color='white', fontweight='bold')
    
    # Highlight best silhouette
    table[(3, 1)].set_facecolor('#27ae60')
    table[(3, 1)].set_text_props(color='white', fontweight='bold')
    
    plt.title('Clustering Metrics Comparison Summary', fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'metrics_summary_table.png', dpi=150, bbox_inches='tight')
    plt.close()
    log_progress(f"  Saved: metrics_summary_table.png")
    
    log_progress("All visualizations generated successfully!")


def save_final_metrics(results):
    """Save final metrics to JSON."""
    final_metrics = {
        'generated': datetime.now().isoformat(),
        'period': PERIOD,
        'stages': {}
    }
    
    for stage in ['baseline0', 'c3', 'final']:
        final_metrics['stages'][stage] = results[stage]['metrics']
    
    # Calculate improvements
    b0 = results['baseline0']['metrics']['silhouette']
    c3 = results['c3']['metrics']['silhouette']
    final = results['final']['metrics']['silhouette']
    
    final_metrics['improvements'] = {
        'baseline0_to_c3': {
            'absolute': round(c3 - b0, 4),
            'percent': round((c3 - b0) / b0 * 100, 1)
        },
        'c3_to_final': {
            'absolute': round(final - c3, 4),
            'percent': round((final - c3) / c3 * 100, 1)
        },
        'baseline0_to_final': {
            'absolute': round(final - b0, 4),
            'percent': round((final - b0) / b0 * 100, 1)
        }
    }
    
    with open(REPORTS_DIR / 'FINAL_METRICS_ALL_STAGES.json', 'w') as f:
        json.dump(final_metrics, f, indent=2)
    
    log_progress(f"Saved final metrics to FINAL_METRICS_ALL_STAGES.json")
    
    return final_metrics


def main():
    """Main entry point."""
    log_progress("="*70)
    log_progress("FINAL IMPROVEMENTS EXPERIMENT")
    log_progress("="*70)
    
    # Load data
    spu_sales, store_sales = load_data()
    
    # Run all stages
    results = {}
    
    # Baseline 0
    m0, pca0, labels0, _ = run_baseline_0(spu_sales)
    results['baseline0'] = {'metrics': m0, 'pca_df': pca0, 'labels': labels0}
    
    # Baseline 1 (C3)
    m1, pca1, labels1, _ = run_baseline_1_c3(spu_sales, store_sales)
    results['c3'] = {'metrics': m1, 'pca_df': pca1, 'labels': labels1}
    
    # Final (A+B+C)
    m2, pca2, labels2, _ = run_final_improvements(spu_sales, store_sales)
    results['final'] = {'metrics': m2, 'pca_df': pca2, 'labels': labels2}
    
    # Generate visualizations
    generate_visualizations(results)
    
    # Save metrics
    final_metrics = save_final_metrics(results)
    
    # Print summary
    log_progress("\n" + "="*70)
    log_progress("EXPERIMENT COMPLETE - SUMMARY")
    log_progress("="*70)
    
    print("\n" + "-"*70)
    print(f"{'Stage':<25} {'Silhouette':<12} {'Clusters':<10} {'Size Range':<15}")
    print("-"*70)
    for stage, name in [('baseline0', 'Baseline 0 (Original)'), ('c3', 'Baseline 1 (C3)'), ('final', 'Final (A+B+C)')]:
        m = results[stage]['metrics']
        print(f"{name:<25} {m['silhouette']:<12.4f} {m['n_clusters']:<10} {m['cluster_sizes']['min']}-{m['cluster_sizes']['max']:<15}")
    print("-"*70)
    
    print(f"\nImprovement Summary:")
    print(f"  Baseline 0 → C3:    +{final_metrics['improvements']['baseline0_to_c3']['percent']:.1f}%")
    print(f"  C3 → Final:         +{final_metrics['improvements']['c3_to_final']['percent']:.1f}%")
    print(f"  Baseline 0 → Final: +{final_metrics['improvements']['baseline0_to_final']['percent']:.1f}%")
    
    return results, final_metrics


if __name__ == '__main__':
    main()
