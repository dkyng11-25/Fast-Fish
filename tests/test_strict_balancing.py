"""
Tests for strict balancing mode (min=max=target).

These tests verify that the refactored Step 6 matches legacy's strict
balancing behavior where min_cluster_size = max_cluster_size = target_cluster_size = 50.

All tests should FAIL initially until defaults are changed to match legacy.
"""

import pytest
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, 'src')

from steps.cluster_analysis_step import ClusterAnalysisStep, ClusterConfig
from steps.cluster_analysis_factory import create_cluster_analysis_step
from core.context import StepContext
from core.logger import PipelineLogger
from unittest.mock import Mock


class TestStrictBalancing:
    """Test suite for strict balancing (min=max=target)."""
    
    @pytest.fixture
    def step_with_strict_balancing(self):
        """Create step with strict balancing (min=max=50)."""
        config = ClusterConfig(
            matrix_type='subcategory',
            pca_components=10,
            target_cluster_size=50,
            min_cluster_size=50,  # STRICT: same as target
            max_cluster_size=50,  # STRICT: same as target
            enable_temperature_constraints=False,
            enable_cluster_balancing=True,
            output_dir='output',
            max_balance_iterations=100,
            random_state=42
        )
        
        # Create mock repositories
        matrix_repo = Mock()
        temperature_repo = Mock()
        clustering_results_repo = Mock()
        cluster_profiles_repo = Mock()
        per_cluster_metrics_repo = Mock()
        logger = PipelineLogger("Test")
        
        return ClusterAnalysisStep(
            matrix_repo=matrix_repo,
            temperature_repo=temperature_repo,
            clustering_results_repo=clustering_results_repo,
            cluster_profiles_repo=cluster_profiles_repo,
            per_cluster_metrics_repo=per_cluster_metrics_repo,
            config=config,
            logger=logger
        )
    
    def test_strict_balancing_enforces_exact_size(self, step_with_strict_balancing):
        """
        Test that min=max=target produces clusters at exactly target size.
        
        Given: 200 stores, target=50, min=50, max=50, 4 clusters
        When: Apply balancing
        Then: All 4 clusters have exactly 50 stores, std dev = 0.0
        """
        np.random.seed(42)
        pca_features = pd.DataFrame(np.random.randn(200, 10))
        
        # Create initial labels (unbalanced)
        initial_labels = np.random.randint(0, 4, size=200)
        
        # Apply balancing
        balanced_labels = step_with_strict_balancing._balance_clusters(
            pca_df=pca_features,
            initial_labels=initial_labels
        )
        
        # Check results
        cluster_sizes = np.bincount(balanced_labels, minlength=4)
        
        assert len(cluster_sizes) == 4, "Should have 4 clusters"
        assert all(size == 50 for size in cluster_sizes), \
            f"All clusters should be exactly 50, got {cluster_sizes}"
        assert cluster_sizes.std() == 0.0, \
            f"Std dev should be 0.0, got {cluster_sizes.std()}"
    
    def test_strict_balancing_minimizes_std_dev(self, step_with_strict_balancing):
        """
        Test that strict balancing produces minimal std dev.
        
        Given: 2274 stores (legacy dataset size), 46 clusters
        When: Apply balancing with min=max=50
        Then: Std dev < 5.0, most clusters at 50, one remainder at 24
        """
        np.random.seed(42)
        pca_features = pd.DataFrame(np.random.randn(2274, 10))
        
        # Create initial labels
        initial_labels = np.random.randint(0, 46, size=2274)
        
        # Apply balancing
        balanced_labels = step_with_strict_balancing._balance_clusters(
            pca_df=pca_features,
            initial_labels=initial_labels
        )
        
        # Check results
        cluster_sizes = np.bincount(balanced_labels, minlength=46)
        non_zero_sizes = cluster_sizes[cluster_sizes > 0]
        
        mean_size = non_zero_sizes.mean()
        std_dev = non_zero_sizes.std()
        
        print(f"\nCluster sizes: min={non_zero_sizes.min()}, max={non_zero_sizes.max()}, mean={mean_size:.1f}, std={std_dev:.1f}")
        print(f"Distribution: {np.bincount(non_zero_sizes)}")
        
        # Assertions
        assert mean_size == pytest.approx(49.4, abs=0.1), \
            f"Mean should be ~49.4, got {mean_size:.1f}"
        assert std_dev < 5.0, \
            f"Std dev should be <5.0 (legacy is 3.8), got {std_dev:.1f}"
        
        # Check distribution: should have most clusters at 50
        # (Synthetic data may not match exactly due to random seed)
        clusters_at_50 = np.sum(non_zero_sizes == 50)
        assert clusters_at_50 >= 35, \
            f"Should have most clusters at 50, got {clusters_at_50}"
    
    def test_default_parameters_match_legacy(self):
        """
        Test that factory defaults match legacy configuration.
        
        Given: Create step with NO parameters (all defaults)
        When: Check configuration
        Then: target=50, min=50, max=50
        """
        step = create_cluster_analysis_step(
            matrix_type='subcategory',
            target_yyyymm='202508',
            target_period='A'
            # NO other parameters - use all defaults
        )
        
        config = step.config
        
        assert config.target_cluster_size == 50, \
            f"Default target should be 50, got {config.target_cluster_size}"
        assert config.min_cluster_size == 50, \
            f"Default min should be 50 (matching legacy), got {config.min_cluster_size}"
        assert config.max_cluster_size == 50, \
            f"Default max should be 50 (matching legacy), got {config.max_cluster_size}"
    
    def test_factory_defaults_produce_tight_clustering(self):
        """
        Test that using factory defaults produces tight clustering.
        
        Given: 2274 stores, default parameters
        When: Run clustering
        Then: Std dev < 5.0, matches legacy
        """
        # This test requires real data, so we'll skip if not available
        import os
        if not os.path.exists('data/normalized_subcategory_matrix.csv'):
            pytest.skip("Real data not available")
        
        step = create_cluster_analysis_step(
            matrix_type='subcategory',
            target_yyyymm='202508',
            target_period='A'
            # Use all defaults
        )
        
        context = StepContext()
        result_context = step.execute(context)
        
        results = result_context.data['results']
        cluster_sizes = results['Cluster'].value_counts()
        
        std_dev = cluster_sizes.std()
        
        print(f"\nWith defaults: mean={cluster_sizes.mean():.1f}, std={std_dev:.1f}")
        
        assert std_dev < 5.0, \
            f"Default behavior should produce std dev <5.0, got {std_dev:.1f}"
    
    def test_default_std_dev_below_5(self, step_with_strict_balancing):
        """
        Test that default behavior produces std dev <5.
        
        Given: Large dataset (1000+ stores), default parameters
        When: Run clustering with balancing
        Then: Std dev < 5.0
        """
        np.random.seed(42)
        pca_features = pd.DataFrame(np.random.randn(1000, 10))
        
        # Create initial labels (20 clusters)
        initial_labels = np.random.randint(0, 20, size=1000)
        
        # Apply balancing
        balanced_labels = step_with_strict_balancing._balance_clusters(
            pca_df=pca_features,
            initial_labels=initial_labels
        )
        
        # Check std dev
        cluster_sizes = np.bincount(balanced_labels, minlength=20)
        non_zero_sizes = cluster_sizes[cluster_sizes > 0]
        std_dev = non_zero_sizes.std()
        
        print(f"\n1000 stores: mean={non_zero_sizes.mean():.1f}, std={std_dev:.1f}")
        
        assert std_dev < 5.0, \
            f"Std dev should be <5.0, got {std_dev:.1f}"
    
    def test_std_dev_matches_legacy(self):
        """
        Test that std dev matches legacy on same dataset.
        
        Given: 2274 stores (exact legacy dataset), 46 clusters
        When: Run clustering with defaults
        Then: Std dev within 1.0 of legacy (3.8)
        """
        # This test requires real data
        import os
        if not os.path.exists('data/normalized_subcategory_matrix.csv'):
            pytest.skip("Real data not available")
        
        step = create_cluster_analysis_step(
            matrix_type='subcategory',
            target_yyyymm='202508',
            target_period='A'
        )
        
        context = StepContext()
        result_context = step.execute(context)
        
        results = result_context.data['results']
        cluster_sizes = results['Cluster'].value_counts()
        std_dev = cluster_sizes.std()
        
        legacy_std_dev = 3.8
        
        print(f"\nLegacy std dev: {legacy_std_dev}")
        print(f"Refactored std dev: {std_dev:.1f}")
        
        assert abs(std_dev - legacy_std_dev) <= 1.0, \
            f"Std dev should be within ±1.0 of legacy ({legacy_std_dev}), got {std_dev:.1f}"
    
    def test_cluster_distribution_matches_legacy(self):
        """
        Test that cluster size distribution matches legacy.
        
        Given: 2274 stores, 46 clusters
        When: Run clustering
        Then: 45 clusters at 50, 1 at 24
        """
        import os
        if not os.path.exists('data/normalized_subcategory_matrix.csv'):
            pytest.skip("Real data not available")
        
        step = create_cluster_analysis_step(
            matrix_type='subcategory',
            target_yyyymm='202508',
            target_period='A'
        )
        
        context = StepContext()
        result_context = step.execute(context)
        
        results = result_context.data['results']
        cluster_sizes = results['Cluster'].value_counts()
        
        # Count clusters at exactly 50
        clusters_at_50 = (cluster_sizes == 50).sum()
        
        print(f"\nClusters at exactly 50: {clusters_at_50}/46")
        print(f"Distribution: {cluster_sizes.value_counts().sort_index()}")
        
        # Should have ~45 at 50 (97.8%)
        assert clusters_at_50 >= 40, \
            f"Should have ~45 clusters at 50, got {clusters_at_50}"
    
    def test_45_of_46_clusters_at_exactly_50(self):
        """
        Test that 45 out of 46 clusters are exactly 50 stores.
        
        Given: 2274 stores, 46 clusters
        When: Run clustering
        Then: 45 clusters at exactly 50 (97.8%)
        """
        import os
        if not os.path.exists('data/normalized_subcategory_matrix.csv'):
            pytest.skip("Real data not available")
        
        step = create_cluster_analysis_step(
            matrix_type='subcategory',
            target_yyyymm='202508',
            target_period='A'
        )
        
        context = StepContext()
        result_context = step.execute(context)
        
        results = result_context.data['results']
        cluster_sizes = results['Cluster'].value_counts()
        
        clusters_at_50 = (cluster_sizes == 50).sum()
        percentage = (clusters_at_50 / 46) * 100
        
        print(f"\nClusters at 50: {clusters_at_50}/46 ({percentage:.1f}%)")
        
        assert clusters_at_50 == 45, \
            f"Should have exactly 45 clusters at 50, got {clusters_at_50}"
        assert percentage >= 95.0, \
            f"Should have ≥95% at target size, got {percentage:.1f}%"
    
    def test_flexible_mode_still_works(self):
        """
        Test that flexible mode (min != max) still works if explicitly set.
        
        Given: Explicitly set min=30, max=60
        When: Run clustering
        Then: Clusters within [30, 60], std dev may be higher
        """
        np.random.seed(42)
        pca_features = pd.DataFrame(np.random.randn(2274, 10))
        
        # Create config with FLEXIBLE mode (explicitly set)
        config = ClusterConfig(
            matrix_type='subcategory',
            pca_components=10,
            target_cluster_size=50,
            min_cluster_size=30,  # FLEXIBLE
            max_cluster_size=60,  # FLEXIBLE
            enable_temperature_constraints=False,
            enable_cluster_balancing=True,
            output_dir='output',
            max_balance_iterations=100,
            random_state=42
        )
        
        matrix_repo = Mock()
        temperature_repo = Mock()
        clustering_results_repo = Mock()
        cluster_profiles_repo = Mock()
        per_cluster_metrics_repo = Mock()
        logger = PipelineLogger("Test")
        
        step = ClusterAnalysisStep(
            matrix_repo=matrix_repo,
            temperature_repo=temperature_repo,
            clustering_results_repo=clustering_results_repo,
            cluster_profiles_repo=cluster_profiles_repo,
            per_cluster_metrics_repo=per_cluster_metrics_repo,
            config=config,
            logger=logger
        )
        
        initial_labels = np.random.randint(0, 46, size=2274)
        balanced_labels = step._balance_clusters(pca_features, initial_labels)
        
        cluster_sizes = np.bincount(balanced_labels, minlength=46)
        non_zero_sizes = cluster_sizes[cluster_sizes > 0]
        
        # Check range
        assert non_zero_sizes.min() >= 30, \
            f"Min should be ≥30, got {non_zero_sizes.min()}"
        assert non_zero_sizes.max() <= 60, \
            f"Max should be ≤60, got {non_zero_sizes.max()}"
        
        print(f"\nFlexible mode: min={non_zero_sizes.min()}, max={non_zero_sizes.max()}, std={non_zero_sizes.std():.1f}")
        print("✅ Flexible mode still works when explicitly requested")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
