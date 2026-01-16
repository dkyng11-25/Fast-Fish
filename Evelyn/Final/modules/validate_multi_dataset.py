#!/usr/bin/env python3
"""
Multi-Dataset Validation Script
================================

Validates the final optimized clustering pipeline across multiple datasets
to confirm improvements are generalizable, not overfitted to 202506A.

Datasets tested:
- 202506A (primary sample)
- 202505A (previous month)
- 202408A (year-over-year comparison)
- 202410A (fall season)

Author: Fast Fish Data Science Team
Date: 2026-01
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, normalize
import json
import warnings
warnings.filterwarnings('ignore')

SCRIPT_DIR = Path(__file__).parent
FINAL_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = FINAL_DIR.parent.parent
DATA_PATH = PROJECT_ROOT / 'docs' / 'Data' / 'step1_api_data_20250917_142743'
OUTPUT_DIR = FINAL_DIR / 'output'

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def log_progress(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def run_baseline_0(spu_sales):
    """Baseline 0: Original pipeline."""
    matrix = spu_sales.pivot_table(
        index='str_code', columns='spu_code', values='spu_sales_amt',
        aggfunc='sum', fill_value=0
    )
    top_spus = matrix.sum().nlargest(1000).index
    matrix = matrix[top_spus]
    normalized = matrix.div(matrix.sum(axis=1), axis=0).fillna(0)
    
    pca = PCA(n_components=min(50, normalized.shape[1]-1), random_state=42)
    pca_result = pca.fit_transform(normalized)
    pca_df = pd.DataFrame(pca_result, index=normalized.index)
    
    n_clusters = min(len(pca_df) // 50 + 1, len(pca_df) - 1)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(pca_df)
    
    silhouette = silhouette_score(pca_df, labels)
    unique, counts = np.unique(labels, return_counts=True)
    
    return {
        'silhouette': round(silhouette, 4),
        'n_clusters': n_clusters,
        'cluster_sizes': {'min': int(counts.min()), 'max': int(counts.max())}
    }


def run_final_improvements(spu_sales, store_sales):
    """Final: All improvements A + B + C."""
    matrix = spu_sales.pivot_table(
        index='str_code', columns='spu_code', values='spu_sales_amt',
        aggfunc='sum', fill_value=0
    )
    top_spus = matrix.sum().nlargest(1000).index
    matrix = matrix[top_spus]
    log_matrix = np.log1p(matrix)
    spu_normalized = log_matrix.div(log_matrix.sum(axis=1), axis=0).fillna(0)
    
    store_unique = store_sales.drop_duplicates(subset='str_code', keep='first')
    store_features = store_unique.set_index('str_code')[['str_type', 'sal_type', 'into_str_cnt_avg', 'avg_temp']].copy()
    store_features['str_type_enc'] = (store_features['str_type'] == '流行').astype(float)
    grade_map = {'AA': 5, 'A': 4, 'B': 3, 'C': 2, 'D': 1}
    store_features['sal_type_enc'] = store_features['sal_type'].map(grade_map).fillna(2)
    traffic = store_features['into_str_cnt_avg'].fillna(0)
    store_features['traffic_norm'] = (traffic - traffic.min()) / (traffic.max() - traffic.min() + 1e-10)
    temp = store_features['avg_temp'].fillna(store_features['avg_temp'].median() if not store_features['avg_temp'].isna().all() else 20)
    store_features['temp_norm'] = (temp - temp.min()) / (temp.max() - temp.min() + 1e-10)
    
    common = spu_normalized.index.intersection(store_features.index)
    if len(common) < 50:
        return None
    
    spu_block = spu_normalized.loc[common]
    store_block = store_features.loc[common][['str_type_enc', 'sal_type_enc', 'traffic_norm', 'temp_norm']]
    
    n_components = min(30, spu_block.shape[1]-1, len(common)-1)
    pca_spu = PCA(n_components=n_components, random_state=42)
    spu_pca = pca_spu.fit_transform(spu_block)
    
    scaler_store = StandardScaler()
    store_scaled = scaler_store.fit_transform(store_block)
    
    spu_weighted = spu_pca * 0.7
    store_weighted = store_scaled * 0.3
    combined = np.hstack([spu_weighted, store_weighted])
    
    combined_l2 = normalize(combined, norm='l2')
    combined_df = pd.DataFrame(combined_l2, index=common)
    
    n_clusters = min(30, len(common) - 1)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=20, max_iter=500)
    labels = kmeans.fit_predict(combined_df)
    
    silhouette = silhouette_score(combined_df, labels)
    unique, counts = np.unique(labels, return_counts=True)
    
    return {
        'silhouette': round(silhouette, 4),
        'n_clusters': n_clusters,
        'cluster_sizes': {'min': int(counts.min()), 'max': int(counts.max())},
        'n_stores': len(common)
    }


def validate_dataset(period: str):
    """Validate a single dataset."""
    spu_file = DATA_PATH / f'complete_spu_sales_{period}.csv'
    store_file = DATA_PATH / f'store_sales_{period}.csv'
    
    if not spu_file.exists() or not store_file.exists():
        return None
    
    try:
        spu_sales = pd.read_csv(spu_file)
        spu_sales['str_code'] = spu_sales['str_code'].astype(str)
        spu_sales['spu_code'] = spu_sales['spu_code'].astype(str)
        
        store_sales = pd.read_csv(store_file)
        store_sales['str_code'] = store_sales['str_code'].astype(str)
        
        if len(spu_sales) < 1000:
            return None
        
        baseline = run_baseline_0(spu_sales)
        final = run_final_improvements(spu_sales, store_sales)
        
        if final is None:
            return None
        
        improvement = round((final['silhouette'] - baseline['silhouette']) / baseline['silhouette'] * 100, 1)
        
        return {
            'period': period,
            'baseline': baseline,
            'final': final,
            'improvement_percent': improvement
        }
    except Exception as e:
        log_progress(f"Error processing {period}: {e}")
        return None


def main():
    """Run validation across multiple datasets."""
    log_progress("="*70)
    log_progress("MULTI-DATASET VALIDATION")
    log_progress("="*70)
    
    # Datasets to validate
    periods = ['202506A', '202505A', '202408A', '202410A', '202507A', '202409A']
    
    results = []
    for period in periods:
        log_progress(f"\nValidating {period}...")
        result = validate_dataset(period)
        if result:
            results.append(result)
            log_progress(f"  Baseline: {result['baseline']['silhouette']:.4f}")
            log_progress(f"  Final:    {result['final']['silhouette']:.4f}")
            log_progress(f"  Improvement: +{result['improvement_percent']:.1f}%")
    
    # Save results
    output = {
        'generated': datetime.now().isoformat(),
        'datasets_validated': len(results),
        'results': results,
        'summary': {
            'avg_baseline_silhouette': round(np.mean([r['baseline']['silhouette'] for r in results]), 4),
            'avg_final_silhouette': round(np.mean([r['final']['silhouette'] for r in results]), 4),
            'avg_improvement_percent': round(np.mean([r['improvement_percent'] for r in results]), 1),
            'min_improvement_percent': round(min([r['improvement_percent'] for r in results]), 1),
            'max_improvement_percent': round(max([r['improvement_percent'] for r in results]), 1)
        }
    }
    
    with open(OUTPUT_DIR / 'MULTI_DATASET_VALIDATION.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    log_progress("\n" + "="*70)
    log_progress("VALIDATION SUMMARY")
    log_progress("="*70)
    print(f"\nDatasets validated: {len(results)}")
    print(f"Average baseline silhouette: {output['summary']['avg_baseline_silhouette']:.4f}")
    print(f"Average final silhouette: {output['summary']['avg_final_silhouette']:.4f}")
    print(f"Average improvement: +{output['summary']['avg_improvement_percent']:.1f}%")
    print(f"Improvement range: +{output['summary']['min_improvement_percent']:.1f}% to +{output['summary']['max_improvement_percent']:.1f}%")
    
    return output


if __name__ == '__main__':
    main()
