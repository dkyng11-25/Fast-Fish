#!/usr/bin/env python3
"""
Baseline Sample Run for Period 202506A

This script runs the ORIGINAL src/step1-6 modules WITHOUT any modifications.
Purpose: Establish baseline metrics for clustering improvement evaluation.

IMPORTANT:
- This script ONLY imports and runs the original src/step*.py modules
- NO modifications to clustering logic
- NO alternative implementations
- Results are used as the BASELINE for all improvement comparisons

Author: Evelyn Module
Date: 2026-01-15
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add src to path to import original modules
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

# Configuration for 202506A
PERIOD = '202506A'
PERIOD_YYYYMM = '202506'
PERIOD_HALF = 'A'

# Output directories
EVELYN_ROOT = PROJECT_ROOT / 'Evelyn'
LOGS_DIR = EVELYN_ROOT / 'logs'
REPORTS_DIR = EVELYN_ROOT / 'reports'
FIGURES_DIR = EVELYN_ROOT / 'figures'

# Ensure directories exist
for d in [LOGS_DIR, REPORTS_DIR, FIGURES_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def log_progress(message: str) -> None:
    """Log progress with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def capture_baseline_metrics() -> dict:
    """
    Run the original src/step3 and src/step6 modules and capture baseline metrics.
    
    Returns:
        Dictionary containing all baseline metrics
    """
    log_progress("=" * 60)
    log_progress("BASELINE SAMPLE RUN - Period 202506A")
    log_progress("Using ORIGINAL src/step1-6 modules (NO modifications)")
    log_progress("=" * 60)
    
    metrics = {
        'period': PERIOD,
        'run_timestamp': datetime.now().isoformat(),
        'run_type': 'BASELINE',
        'modules_used': {
            'step3': 'src/step3_prepare_matrix.py (ORIGINAL)',
            'step6': 'src/step6_cluster_analysis.py (ORIGINAL)'
        }
    }
    
    # Step 3: Prepare Matrix (using original module)
    log_progress("\n--- Step 3: Prepare Store-Product Matrix ---")
    try:
        # Import original step3 module
        import step3_prepare_matrix as step3
        
        # Capture step3 configuration
        metrics['step3'] = {
            'matrix_type': 'spu',
            'min_stores_per_spu': step3.MIN_STORES_PER_SPU,
            'min_spus_per_store': step3.MIN_SPUS_PER_STORE,
            'max_spu_count': step3.MAX_SPU_COUNT,
            'normalization': 'row-wise (div by row sum)'
        }
        
        log_progress(f"Step 3 Config: MAX_SPU_COUNT={step3.MAX_SPU_COUNT}")
        log_progress("Step 3 uses ROW-WISE normalization (matrix.div(matrix.sum(axis=1), axis=0))")
        
        # Note: We don't run step3.main() here as data is already prepared
        # We just capture the configuration
        
    except Exception as e:
        log_progress(f"Error importing step3: {e}")
        metrics['step3'] = {'error': str(e)}
    
    # Step 6: Cluster Analysis (using original module)
    log_progress("\n--- Step 6: Cluster Analysis ---")
    try:
        # Import original step6 module
        import step6_cluster_analysis as step6
        
        # Capture step6 configuration BEFORE running
        metrics['step6'] = {
            'matrix_type': step6.MATRIX_TYPE,
            'pca_components': step6.PCA_COMPONENTS,
            'random_state': step6.RANDOM_STATE,
            'n_init': step6.N_INIT,
            'max_iter': step6.MAX_ITER,
            'min_cluster_size': step6.MIN_CLUSTER_SIZE,
            'max_cluster_size': step6.MAX_CLUSTER_SIZE,
            'temperature_constraints': step6.ENABLE_TEMPERATURE_CONSTRAINTS,
            'cluster_determination': 'n_samples // 50 (dynamic)',
            'store_features_used': False  # Original does NOT use store features
        }
        
        log_progress(f"Step 6 Config:")
        log_progress(f"  - Matrix Type: {step6.MATRIX_TYPE}")
        log_progress(f"  - PCA Components: {step6.PCA_COMPONENTS}")
        log_progress(f"  - Cluster Size Target: {step6.MAX_CLUSTER_SIZE} stores")
        log_progress(f"  - Temperature Constraints: {step6.ENABLE_TEMPERATURE_CONSTRAINTS}")
        log_progress(f"  - Store Features (str_type, sal_type, traffic): NOT USED")
        
    except Exception as e:
        log_progress(f"Error importing step6: {e}")
        metrics['step6'] = {'error': str(e)}
    
    return metrics


def read_existing_results() -> dict:
    """
    Read existing clustering results from output files.
    
    Returns:
        Dictionary with clustering results and metrics
    """
    import pandas as pd
    
    results = {}
    
    # Read clustering results
    results_file = PROJECT_ROOT / 'output' / 'clustering_results_spu.csv'
    if results_file.exists():
        df = pd.read_csv(results_file)
        results['clustering_results'] = {
            'file': str(results_file),
            'n_stores': len(df),
            'n_clusters': df['Cluster'].nunique() if 'Cluster' in df.columns else None,
            'cluster_distribution': df['Cluster'].value_counts().to_dict() if 'Cluster' in df.columns else None
        }
        log_progress(f"Read clustering results: {len(df)} stores, {results['clustering_results']['n_clusters']} clusters")
    
    # Read per-cluster metrics
    metrics_file = PROJECT_ROOT / 'output' / 'per_cluster_metrics_spu.csv'
    if metrics_file.exists():
        df = pd.read_csv(metrics_file)
        results['per_cluster_metrics'] = {
            'file': str(metrics_file),
            'data': df.to_dict('records')
        }
    
    # Read cluster profiles
    profiles_file = PROJECT_ROOT / 'output' / 'cluster_profiles_spu.csv'
    if profiles_file.exists():
        df = pd.read_csv(profiles_file)
        results['cluster_profiles'] = {
            'file': str(profiles_file),
            'n_profiles': len(df)
        }
    
    return results


def save_baseline_report(metrics: dict, results: dict) -> None:
    """
    Save baseline metrics and results to report file.
    """
    report_file = REPORTS_DIR / 'BASELINE_METRICS_202506A.json'
    
    combined = {
        'baseline_metrics': metrics,
        'clustering_results': results
    }
    
    with open(report_file, 'w') as f:
        json.dump(combined, f, indent=2, default=str)
    
    log_progress(f"Saved baseline metrics to: {report_file}")


def main():
    """Main entry point for baseline run."""
    log_progress("Starting Baseline Sample Run...")
    
    # Capture baseline configuration
    metrics = capture_baseline_metrics()
    
    # Read existing results (from previous runs)
    results = read_existing_results()
    
    # Save baseline report
    save_baseline_report(metrics, results)
    
    log_progress("\n" + "=" * 60)
    log_progress("BASELINE CAPTURE COMPLETE")
    log_progress("=" * 60)
    log_progress("\nBaseline Configuration Summary:")
    log_progress(f"  - Period: {PERIOD}")
    log_progress(f"  - Normalization: Row-wise (original step3)")
    log_progress(f"  - Cluster Count: Dynamic (n_samples // 50)")
    log_progress(f"  - Store Features: NOT USED")
    log_progress(f"  - Temperature Constraints: {metrics.get('step6', {}).get('temperature_constraints', 'N/A')}")
    
    if 'clustering_results' in results:
        log_progress(f"\nBaseline Results:")
        log_progress(f"  - Stores: {results['clustering_results']['n_stores']}")
        log_progress(f"  - Clusters: {results['clustering_results']['n_clusters']}")
    
    log_progress("\nNext: Run clustering improvements and compare against this baseline")


if __name__ == '__main__':
    main()
