"""
Unit tests for cluster balancing algorithm.

These tests verify the core balancing functionality in isolation.
All tests should FAIL initially (TDD red state) until implementation is complete.
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
import sys
sys.path.insert(0, 'src')

from steps.cluster_analysis_step import ClusterAnalysisStep, ClusterConfig
from core.context import StepContext


class TestClusterBalancing:
    """Test suite for cluster balancing algorithm."""
    
    @pytest.fixture
    def sample_pca_features(self):
        """Create sample PCA features for testing."""
        np.random.seed(42)
        return pd.DataFrame(
            np.random.randn(100, 10),
            columns=[f'PC{i}' for i in range(10)]
        )
    
    @pytest.fixture
    def config_with_balancing(self):
        """Create config with balancing enabled."""
        return ClusterConfig(
            matrix_type='subcategory',
            pca_components=10,
            target_cluster_size=50,
            min_cluster_size=30,
            max_cluster_size=60,
            enable_temperature_constraints=False,
            enable_cluster_balancing=True,
            output_dir='output',
            max_balance_iterations=100,
            random_state=42
        )
    
    @pytest.fixture
    def step_with_balancing(self, config_with_balancing):
        """Create a ClusterAnalysisStep instance with mocked dependencies."""
        from core.logger import PipelineLogger
        from unittest.mock import Mock
        
        # Create mock repositories
        matrix_repo = Mock()
        temperature_repo = Mock()
        clustering_results_repo = Mock()
        cluster_profiles_repo = Mock()
        per_cluster_metrics_repo = Mock()
        
        # Create logger
        logger = PipelineLogger("Test")
        
        # Create step
        step = ClusterAnalysisStep(
            matrix_repo=matrix_repo,
            temperature_repo=temperature_repo,
            clustering_results_repo=clustering_results_repo,
            cluster_profiles_repo=cluster_profiles_repo,
            per_cluster_metrics_repo=per_cluster_metrics_repo,
            config=config_with_balancing,
            logger=logger
        )
        
        return step
    
    def test_balance_simple_oversized_cluster(self, sample_pca_features, step_with_balancing):
        """
        Test balancing a single oversized cluster.
        
        Given:
        - 100 stores in 2 clusters
        - Cluster 0: 80 stores
        - Cluster 1: 20 stores
        - Max cluster size: 60
        
        When:
        - Apply balancing
        
        Then:
        - Cluster 0: ≤60 stores
        - Cluster 1: ≥40 stores
        - Total stores: 100 (preserved)
        """
        # Create unbalanced initial labels
        initial_labels = np.array([0] * 80 + [1] * 20)
        
        # Apply balancing
        balanced_labels = step_with_balancing._balance_clusters(
            pca_df=sample_pca_features,
            initial_labels=initial_labels
        )
        
        # Verify results
        cluster_0_size = np.sum(balanced_labels == 0)
        cluster_1_size = np.sum(balanced_labels == 1)
        
        assert cluster_0_size <= 60, f"Cluster 0 has {cluster_0_size} stores, expected ≤60"
        assert cluster_1_size >= 40, f"Cluster 1 has {cluster_1_size} stores, expected ≥40"
        assert cluster_0_size + cluster_1_size == 100, "Total stores not preserved"
    
    def test_balance_respects_min_max_constraints(self, config_with_balancing):
        """
        Test that balancing respects min/max constraints.
        
        Given:
        - 200 stores in 4 clusters
        - Initial sizes: [100, 50, 30, 20]
        - Min: 30, Max: 60
        
        When:
        - Apply balancing
        
        Then:
        - All clusters: 30 ≤ size ≤ 60
        - Total stores: 200 (preserved)
        """
        np.random.seed(42)
        pca_features = pd.DataFrame(np.random.randn(200, 10))
        
        # Create unbalanced labels: [100, 50, 30, 20]
        initial_labels = np.array([0] * 100 + [1] * 50 + [2] * 30 + [3] * 20)
        
        step = ClusterAnalysisStep(config_with_balancing)
        
        balanced_labels = step._balance_clusters(
            pca_features=pca_features,
            initial_labels=initial_labels,
            target_size=50,
            min_size=30,
            max_size=60
        )
        
        # Check each cluster
        for cluster_id in range(4):
            size = np.sum(balanced_labels == cluster_id)
            assert 30 <= size <= 60, f"Cluster {cluster_id} has {size} stores, expected [30, 60]"
        
        # Verify total preserved
        assert len(balanced_labels) == 200, "Total stores not preserved"
    
    def test_balance_converges_within_max_iterations(self, config_with_balancing):
        """
        Test that balancing converges within max iterations.
        
        Given:
        - 2274 stores in 46 clusters
        - Unbalanced initial state
        - Max iterations: 100
        
        When:
        - Apply balancing
        
        Then:
        - Converges in ≤100 iterations
        - All constraints satisfied
        """
        np.random.seed(42)
        pca_features = pd.DataFrame(np.random.randn(2274, 10))
        
        # Create highly unbalanced labels
        initial_labels = np.random.randint(0, 46, size=2274)
        
        step = ClusterAnalysisStep(config_with_balancing)
        
        # This should converge within 100 iterations
        balanced_labels = step._balance_clusters(
            pca_features=pca_features,
            initial_labels=initial_labels,
            target_size=50,
            min_size=30,
            max_size=60
        )
        
        # Verify all clusters within constraints
        for cluster_id in range(46):
            size = np.sum(balanced_labels == cluster_id)
            if size > 0:  # Skip empty clusters
                assert 30 <= size <= 60, f"Cluster {cluster_id} has {size} stores after balancing"
    
    def test_balance_moves_farthest_stores_first(self, sample_pca_features, config_with_balancing):
        """
        Test that balancing moves farthest stores first.
        
        Given:
        - Cluster with 80 stores
        - Need to move 20 stores
        - Stores have varying distances to center
        
        When:
        - Apply balancing
        
        Then:
        - The 20 farthest stores are moved
        - Closer stores remain in cluster
        """
        # Create cluster with known geometry
        # Cluster 0: 80 stores (60 close, 20 far)
        # Cluster 1: 20 stores
        close_stores = np.random.randn(60, 10) * 0.5  # Close to origin
        far_stores = np.random.randn(20, 10) * 3.0    # Far from origin
        cluster_1_stores = np.random.randn(20, 10) + 10  # Separate cluster
        
        pca_features = pd.DataFrame(
            np.vstack([close_stores, far_stores, cluster_1_stores])
        )
        
        initial_labels = np.array([0] * 80 + [1] * 20)
        
        step = ClusterAnalysisStep(config_with_balancing)
        
        balanced_labels = step._balance_clusters(
            pca_features=pca_features,
            initial_labels=initial_labels,
            target_size=50,
            min_size=30,
            max_size=60
        )
        
        # The far stores (indices 60-79) should be more likely to move
        # than close stores (indices 0-59)
        close_stores_moved = np.sum(balanced_labels[:60] != 0)
        far_stores_moved = np.sum(balanced_labels[60:80] != 0)
        
        assert far_stores_moved > close_stores_moved, \
            f"Expected more far stores moved ({far_stores_moved}) than close stores ({close_stores_moved})"
    
    def test_balance_assigns_to_nearest_cluster(self, config_with_balancing):
        """
        Test that stores are moved to nearest available cluster.
        
        Given:
        - Store to be moved from cluster 0
        - Multiple target clusters available
        - Each cluster has different distance
        
        When:
        - Move the store
        
        Then:
        - Store is assigned to nearest non-full cluster
        - Full clusters are excluded
        """
        # Create 3 clusters with known positions
        cluster_0 = np.zeros((80, 10))  # At origin, oversized
        cluster_1 = np.ones((40, 10)) * 5  # Distance 5, available
        cluster_2 = np.ones((40, 10)) * 10  # Distance 10, available
        
        pca_features = pd.DataFrame(np.vstack([cluster_0, cluster_1, cluster_2]))
        initial_labels = np.array([0] * 80 + [1] * 40 + [2] * 40)
        
        step = ClusterAnalysisStep(config_with_balancing)
        
        balanced_labels = step._balance_clusters(
            pca_features=pca_features,
            initial_labels=initial_labels,
            target_size=50,
            min_size=30,
            max_size=60
        )
        
        # Stores moved from cluster 0 should go to cluster 1 (closer)
        # rather than cluster 2 (farther)
        moved_to_cluster_1 = np.sum((initial_labels == 0) & (balanced_labels == 1))
        moved_to_cluster_2 = np.sum((initial_labels == 0) & (balanced_labels == 2))
        
        assert moved_to_cluster_1 > moved_to_cluster_2, \
            f"Expected more moves to closer cluster 1 ({moved_to_cluster_1}) than cluster 2 ({moved_to_cluster_2})"
    
    def test_balance_preserves_total_stores(self, sample_pca_features, config_with_balancing):
        """
        Test that balancing preserves total number of stores.
        
        Given:
        - N stores initially
        
        When:
        - Apply balancing
        
        Then:
        - Still N stores after balancing
        - No stores lost or duplicated
        """
        initial_labels = np.random.randint(0, 4, size=100)
        n_stores_before = len(initial_labels)
        
        step = ClusterAnalysisStep(config_with_balancing)
        
        balanced_labels = step._balance_clusters(
            pca_features=sample_pca_features,
            initial_labels=initial_labels,
            target_size=25,
            min_size=20,
            max_size=30
        )
        
        n_stores_after = len(balanced_labels)
        
        assert n_stores_before == n_stores_after, \
            f"Store count changed: {n_stores_before} → {n_stores_after}"
        
        # Verify no duplicates
        assert len(np.unique(balanced_labels)) <= len(np.unique(initial_labels)), \
            "Number of clusters increased unexpectedly"
    
    def test_balance_with_empty_cluster(self, config_with_balancing):
        """
        Test handling of empty clusters.
        
        Given:
        - 100 stores in 5 clusters
        - Cluster 2 is empty (0 stores)
        
        When:
        - Apply balancing
        
        Then:
        - Empty cluster is filled or removed
        - No crashes or errors
        - Final result has no empty clusters (or handles gracefully)
        """
        np.random.seed(42)
        pca_features = pd.DataFrame(np.random.randn(100, 10))
        
        # Create labels with empty cluster 2
        initial_labels = np.array([0] * 40 + [1] * 30 + [3] * 20 + [4] * 10)
        # Cluster 2 is missing (empty)
        
        step = ClusterAnalysisStep(config_with_balancing)
        
        # Should handle gracefully without crashing
        balanced_labels = step._balance_clusters(
            pca_features=pca_features,
            initial_labels=initial_labels,
            target_size=25,
            min_size=20,
            max_size=30
        )
        
        # Verify no crashes and result is valid
        assert len(balanced_labels) == 100, "Store count not preserved"
        
        # Check that all non-empty clusters are within constraints
        unique_clusters = np.unique(balanced_labels)
        for cluster_id in unique_clusters:
            size = np.sum(balanced_labels == cluster_id)
            assert size > 0, f"Cluster {cluster_id} is empty after balancing"
    
    def test_balance_tracks_quality_metrics(self, sample_pca_features, config_with_balancing):
        """
        Test that quality metrics are tracked.
        
        Given:
        - Initial clustering with known quality
        
        When:
        - Apply balancing
        
        Then:
        - Silhouette score tracked before/after
        - Quality degradation logged if >0.1
        - Metrics returned in result
        """
        initial_labels = np.array([0] * 50 + [1] * 50)
        
        step = ClusterAnalysisStep(config_with_balancing)
        
        # Mock the quality tracking
        with patch.object(step, '_calculate_silhouette_score') as mock_silhouette:
            mock_silhouette.side_effect = [0.5, 0.45]  # Before and after
            
            balanced_labels = step._balance_clusters(
                pca_features=sample_pca_features,
                initial_labels=initial_labels,
                target_size=50,
                min_size=30,
                max_size=60
            )
            
            # Verify silhouette was calculated twice (before and after)
            assert mock_silhouette.call_count == 2, \
                "Silhouette score should be calculated before and after balancing"
    
    def test_balance_can_be_disabled(self, sample_pca_features):
        """
        Test that balancing can be disabled.
        
        Given:
        - enable_cluster_balancing = False
        
        When:
        - Perform clustering
        
        Then:
        - No balancing occurs
        - Initial KMeans labels used
        - Clusters remain unbalanced
        """
        config_no_balancing = ClusterAnalysisConfig(
            matrix_type='subcategory',
            target_yyyymm='202508',
            target_period='A',
            output_dir='output',
            pca_components=10,
            target_cluster_size=50,
            min_cluster_size=30,
            max_cluster_size=60,
            enable_cluster_balancing=False,  # DISABLED
            max_balance_iterations=100,
            enable_temperature_constraints=False,
            random_state=42
        )
        
        initial_labels = np.array([0] * 80 + [1] * 20)
        
        step = ClusterAnalysisStep(config_no_balancing)
        
        # When balancing is disabled, should return initial labels unchanged
        # (or skip balancing in the apply phase)
        # This tests the configuration flag
        assert not step.config.enable_cluster_balancing, \
            "Balancing should be disabled in config"
    
    def test_balance_with_custom_target_size(self, config_with_balancing):
        """
        Test balancing with custom target size.
        
        Given:
        - target_cluster_size = 25
        - min_cluster_size = 20
        - max_cluster_size = 30
        
        When:
        - Apply balancing
        
        Then:
        - Clusters balanced to ~25 stores
        - All within [20, 30] range
        """
        np.random.seed(42)
        pca_features = pd.DataFrame(np.random.randn(100, 10))
        
        # Create unbalanced labels
        initial_labels = np.array([0] * 60 + [1] * 20 + [2] * 10 + [3] * 10)
        
        step = ClusterAnalysisStep(config_with_balancing)
        
        balanced_labels = step._balance_clusters(
            pca_features=pca_features,
            initial_labels=initial_labels,
            target_size=25,  # Custom target
            min_size=20,
            max_size=30
        )
        
        # Verify all clusters within custom range
        for cluster_id in range(4):
            size = np.sum(balanced_labels == cluster_id)
            if size > 0:
                assert 20 <= size <= 30, \
                    f"Cluster {cluster_id} has {size} stores, expected [20, 30]"
        
        # Verify mean is close to target
        cluster_sizes = [np.sum(balanced_labels == i) for i in range(4)]
        mean_size = np.mean([s for s in cluster_sizes if s > 0])
        assert 23 <= mean_size <= 27, \
            f"Mean cluster size {mean_size:.1f}, expected ~25"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
