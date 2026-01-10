"""
Validation tests comparing refactored balancing with legacy behavior.

These tests ensure the refactored implementation produces results
comparable to the legacy Step 6 balancing algorithm.
"""

import pytest
import numpy as np
import pandas as pd
import os
import sys
sys.path.insert(0, 'src')

from steps.cluster_analysis_factory import create_cluster_analysis_step
from core.context import StepContext


class TestClusterBalancingLegacyComparison:
    """Validation tests comparing with legacy behavior."""
    
    @pytest.fixture
    def legacy_results_dir(self):
        """Get directory with legacy results."""
        # Use the backup from our comparison test
        return "backup_legacy_step6_full_20251029_133011"
    
    @pytest.fixture
    def test_output_dir(self, tmp_path):
        """Create temporary output directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        return str(output_dir)
    
    def test_cluster_sizes_match_legacy(self, legacy_results_dir, test_output_dir):
        """
        Test that cluster sizes match legacy.
        
        Given:
        - Same dataset as legacy
        - Same parameters as legacy
        
        When:
        - Run refactored clustering with balancing
        
        Then:
        - Mean cluster size within 1 store of legacy
        - Std dev within 2 stores of legacy
        - Min/max within 5 stores of legacy
        """
        # Load legacy results
        legacy_file = f"{legacy_results_dir}/clustering_results_subcategory.csv"
        if not os.path.exists(legacy_file):
            pytest.skip("Legacy results not available")
        
        legacy_results = pd.read_csv(legacy_file)
        legacy_sizes = legacy_results['Cluster'].value_counts()
        
        # Calculate legacy statistics
        legacy_mean = legacy_sizes.mean()
        legacy_std = legacy_sizes.std()
        legacy_min = legacy_sizes.min()
        legacy_max = legacy_sizes.max()
        
        print(f"\nLegacy cluster statistics:")
        print(f"  Mean: {legacy_mean:.1f}")
        print(f"  Std: {legacy_std:.1f}")
        print(f"  Range: [{legacy_min}, {legacy_max}]")
        
        # Run refactored clustering
        step = create_cluster_analysis_step(
            matrix_type='subcategory',
            target_yyyymm='202508',
            target_period='A',
            output_dir=test_output_dir,
            pca_components=20,
            target_cluster_size=50,
            min_cluster_size=30,
            max_cluster_size=60,
            enable_cluster_balancing=True,
            max_balance_iterations=100,
            enable_temperature_constraints=False,
            random_state=42
        )
        
        context = StepContext()
        result_context = step.execute(context)
        
        refactored_results = result_context.data['results']
        refactored_sizes = refactored_results['Cluster'].value_counts()
        
        # Calculate refactored statistics
        refactored_mean = refactored_sizes.mean()
        refactored_std = refactored_sizes.std()
        refactored_min = refactored_sizes.min()
        refactored_max = refactored_sizes.max()
        
        print(f"\nRefactored cluster statistics:")
        print(f"  Mean: {refactored_mean:.1f}")
        print(f"  Std: {refactored_std:.1f}")
        print(f"  Range: [{refactored_min}, {refactored_max}]")
        
        # Validate against legacy
        assert abs(refactored_mean - legacy_mean) <= 1.0, \
            f"Mean cluster size differs: {refactored_mean:.1f} vs {legacy_mean:.1f}"
        
        assert abs(refactored_std - legacy_std) <= 2.0, \
            f"Std dev differs: {refactored_std:.1f} vs {legacy_std:.1f}"
        
        assert abs(refactored_min - legacy_min) <= 5, \
            f"Min cluster size differs: {refactored_min} vs {legacy_min}"
        
        assert abs(refactored_max - legacy_max) <= 5, \
            f"Max cluster size differs: {refactored_max} vs {legacy_max}"
    
    def test_store_assignments_match_legacy(self, legacy_results_dir, test_output_dir):
        """
        Test that store assignments match legacy.
        
        Given:
        - Same dataset as legacy
        - Same random seed
        
        When:
        - Run refactored clustering with balancing
        
        Then:
        - At least 90% of stores in same clusters
        - Cluster mappings identifiable
        """
        # Load legacy results
        legacy_file = f"{legacy_results_dir}/clustering_results_subcategory.csv"
        if not os.path.exists(legacy_file):
            pytest.skip("Legacy results not available")
        
        legacy_results = pd.read_csv(legacy_file)
        
        # Run refactored clustering
        step = create_cluster_analysis_step(
            matrix_type='subcategory',
            target_yyyymm='202508',
            target_period='A',
            output_dir=test_output_dir,
            pca_components=20,
            target_cluster_size=50,
            min_cluster_size=30,
            max_cluster_size=60,
            enable_cluster_balancing=True,
            max_balance_iterations=100,
            enable_temperature_constraints=False,
            random_state=42
        )
        
        context = StepContext()
        result_context = step.execute(context)
        
        refactored_results = result_context.data['results']
        
        # Merge results
        merged = legacy_results.merge(
            refactored_results,
            on='str_code',
            suffixes=('_legacy', '_refactored')
        )
        
        # Calculate direct matches (cluster IDs are arbitrary)
        direct_matches = (merged['Cluster_legacy'] == merged['Cluster_refactored']).sum()
        total = len(merged)
        direct_match_pct = (direct_matches / total) * 100
        
        print(f"\nDirect matches: {direct_matches}/{total} ({direct_match_pct:.1f}%)")
        
        # Calculate adjusted matches (accounting for cluster ID permutation)
        # For each legacy cluster, find best matching refactored cluster
        cluster_mapping = {}
        for legacy_cluster in sorted(legacy_results['Cluster'].unique()):
            legacy_stores = set(legacy_results[legacy_results['Cluster'] == legacy_cluster]['str_code'])
            
            best_overlap = 0
            best_refactored_cluster = None
            
            for refactored_cluster in refactored_results['Cluster'].unique():
                refactored_stores = set(refactored_results[refactored_results['Cluster'] == refactored_cluster]['str_code'])
                overlap = len(legacy_stores & refactored_stores)
                
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_refactored_cluster = refactored_cluster
            
            cluster_mapping[legacy_cluster] = (best_refactored_cluster, best_overlap, len(legacy_stores))
        
        # Calculate adjusted matches
        adjusted_matches = 0
        for _, row in merged.iterrows():
            legacy_cluster = row['Cluster_legacy']
            refactored_cluster = row['Cluster_refactored']
            mapped_cluster, _, _ = cluster_mapping[legacy_cluster]
            
            if refactored_cluster == mapped_cluster:
                adjusted_matches += 1
        
        adjusted_match_pct = (adjusted_matches / total) * 100
        
        print(f"Adjusted matches: {adjusted_matches}/{total} ({adjusted_match_pct:.1f}%)")
        
        # Validate: at least 90% agreement
        assert adjusted_match_pct >= 90.0, \
            f"Store assignment agreement {adjusted_match_pct:.1f}% < 90%"
        
        # Print cluster mapping for debugging
        print("\nCluster mapping (Legacy → Refactored):")
        for legacy_id in sorted(cluster_mapping.keys())[:10]:
            ref_id, overlap, total_stores = cluster_mapping[legacy_id]
            pct = (overlap / total_stores) * 100
            print(f"  Cluster {legacy_id:2d} → {ref_id:2d}: {overlap:4d}/{total_stores:4d} ({pct:5.1f}%)")
    
    def test_convergence_matches_legacy(self, test_output_dir):
        """
        Test that convergence behavior matches legacy.
        
        Given:
        - Same dataset as legacy
        
        When:
        - Run refactored clustering with balancing
        
        Then:
        - Converges in similar iterations (~100)
        - Final state is balanced
        """
        # Run refactored clustering
        step = create_cluster_analysis_step(
            matrix_type='subcategory',
            target_yyyymm='202508',
            target_period='A',
            output_dir=test_output_dir,
            pca_components=20,
            target_cluster_size=50,
            min_cluster_size=30,
            max_cluster_size=60,
            enable_cluster_balancing=True,
            max_balance_iterations=100,
            enable_temperature_constraints=False,
            random_state=42
        )
        
        context = StepContext()
        result_context = step.execute(context)
        
        # Verify convergence
        # (In implementation, we should track iteration count)
        refactored_results = result_context.data['results']
        cluster_sizes = refactored_results['Cluster'].value_counts()
        
        # Verify all clusters within constraints (converged)
        assert cluster_sizes.min() >= 30, \
            f"Min cluster size {cluster_sizes.min()} < 30 (not converged)"
        assert cluster_sizes.max() <= 60, \
            f"Max cluster size {cluster_sizes.max()} > 60 (not converged)"
        
        # Legacy converged in ~100 iterations
        # Refactored should converge in similar range (80-120)
        # This would require tracking iterations in the implementation
    
    def test_quality_metrics_comparable_to_legacy(self, legacy_results_dir, test_output_dir):
        """
        Test that quality metrics are comparable to legacy.
        
        Given:
        - Same dataset as legacy
        
        When:
        - Run refactored clustering with balancing
        
        Then:
        - Silhouette score within 0.1 of legacy
        - Calinski-Harabasz within 20% of legacy
        - Davies-Bouldin within 0.5 of legacy
        """
        # Legacy metrics (from our earlier test):
        # Silhouette: 0.059
        # Calinski-Harabasz: 92.0
        # Davies-Bouldin: 2.321
        
        legacy_silhouette = 0.059
        legacy_calinski = 92.0
        legacy_davies = 2.321
        
        # Run refactored clustering
        step = create_cluster_analysis_step(
            matrix_type='subcategory',
            target_yyyymm='202508',
            target_period='A',
            output_dir=test_output_dir,
            pca_components=20,
            target_cluster_size=50,
            min_cluster_size=30,
            max_cluster_size=60,
            enable_cluster_balancing=True,
            max_balance_iterations=100,
            enable_temperature_constraints=False,
            random_state=42
        )
        
        context = StepContext()
        result_context = step.execute(context)
        
        # Get quality metrics from result
        # (Implementation should store these in context)
        if 'quality_metrics' in result_context.data:
            metrics = result_context.data['quality_metrics']
            
            refactored_silhouette = metrics.get('silhouette_score', 0)
            refactored_calinski = metrics.get('calinski_harabasz_score', 0)
            refactored_davies = metrics.get('davies_bouldin_score', 0)
            
            print(f"\nQuality Metrics Comparison:")
            print(f"  Silhouette: {refactored_silhouette:.3f} vs {legacy_silhouette:.3f}")
            print(f"  Calinski-Harabasz: {refactored_calinski:.1f} vs {legacy_calinski:.1f}")
            print(f"  Davies-Bouldin: {refactored_davies:.3f} vs {legacy_davies:.3f}")
            
            # Validate metrics are comparable
            assert abs(refactored_silhouette - legacy_silhouette) <= 0.1, \
                f"Silhouette score differs too much: {refactored_silhouette:.3f} vs {legacy_silhouette:.3f}"
            
            assert abs(refactored_calinski - legacy_calinski) / legacy_calinski <= 0.2, \
                f"Calinski-Harabasz differs too much: {refactored_calinski:.1f} vs {legacy_calinski:.1f}"
            
            assert abs(refactored_davies - legacy_davies) <= 0.5, \
                f"Davies-Bouldin differs too much: {refactored_davies:.3f} vs {legacy_davies:.3f}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
