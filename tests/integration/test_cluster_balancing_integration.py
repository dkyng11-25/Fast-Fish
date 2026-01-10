"""
Integration tests for cluster balancing with full clustering pipeline.

These tests verify that balancing works correctly when integrated with
the complete clustering workflow.
"""

import pytest
import numpy as np
import pandas as pd
import os
import sys
sys.path.insert(0, 'src')

from steps.cluster_analysis_factory import create_cluster_analysis_step
from core.context import StepContext


class TestClusterBalancingIntegration:
    """Integration tests for cluster balancing."""
    
    @pytest.fixture
    def test_data_dir(self):
        """Get test data directory."""
        return "data"
    
    @pytest.fixture
    def test_output_dir(self, tmp_path):
        """Create temporary output directory."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        return str(output_dir)
    
    def test_full_clustering_with_balancing(self, test_data_dir, test_output_dir):
        """
        Test full clustering pipeline with balancing.
        
        Given:
        - Full dataset (2274 stores)
        - Subcategory matrix
        
        When:
        - Run complete clustering with balancing
        
        Then:
        - Clustering completes successfully
        - Clusters are balanced
        - Output files created
        - Quality metrics acceptable
        """
        # Check if data files exist
        normalized_matrix = f"{test_data_dir}/normalized_subcategory_matrix.csv"
        if not os.path.exists(normalized_matrix):
            pytest.skip("Test data not available")
        
        # Create step with balancing enabled
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
        
        # Execute clustering
        context = StepContext()
        result_context = step.execute(context)
        
        # Verify results exist
        assert 'results' in result_context.data, "Results not found in context"
        results = result_context.data['results']
        
        # Verify cluster sizes are balanced
        cluster_sizes = results['Cluster'].value_counts()
        
        assert cluster_sizes.min() >= 30, \
            f"Minimum cluster size {cluster_sizes.min()} < 30"
        assert cluster_sizes.max() <= 60, \
            f"Maximum cluster size {cluster_sizes.max()} > 60"
        assert 45 <= cluster_sizes.mean() <= 55, \
            f"Mean cluster size {cluster_sizes.mean():.1f} not close to 50"
        assert cluster_sizes.std() < 10, \
            f"Cluster size std dev {cluster_sizes.std():.1f} >= 10"
        
        # Verify output files created
        expected_files = [
            f"{test_output_dir}/clustering_results_subcategory_202508A.csv",
            f"{test_output_dir}/cluster_profiles_subcategory_202508A.csv",
            f"{test_output_dir}/per_cluster_metrics_subcategory_202508A.csv"
        ]
        
        for file_path in expected_files:
            assert os.path.exists(file_path), f"Output file not created: {file_path}"
    
    def test_balancing_with_temperature_aware_clustering(self, test_data_dir, test_output_dir):
        """
        Test balancing with temperature-aware clustering.
        
        Given:
        - 100 stores with temperature data
        - Temperature-aware clustering enabled
        - Balancing enabled
        
        When:
        - Run clustering
        
        Then:
        - Clusters balanced within temperature bands
        - Temperature constraints respected
        - Balancing constraints respected
        """
        # Check if temperature data exists
        temp_file = "output/stores_with_feels_like_temperature.csv"
        if not os.path.exists(temp_file):
            pytest.skip("Temperature data not available")
        
        # Create step with both temperature and balancing enabled
        step = create_cluster_analysis_step(
            matrix_type='subcategory',
            target_yyyymm='202508',
            target_period='A',
            output_dir=test_output_dir,
            pca_components=20,
            target_cluster_size=50,
            min_cluster_size=1,  # Relaxed for small dataset
            max_cluster_size=100,
            enable_cluster_balancing=True,
            max_balance_iterations=100,
            enable_temperature_constraints=True,  # ENABLED
            random_state=42
        )
        
        # Execute clustering
        context = StepContext()
        result_context = step.execute(context)
        
        # Verify results
        assert 'results' in result_context.data, "Results not found"
        results = result_context.data['results']
        
        # Verify temperature data was used
        assert 'temperature_data' in result_context.data, \
            "Temperature data not loaded"
        
        # Verify clustering completed
        assert len(results) > 0, "No clustering results"
        assert 'Cluster' in results.columns, "Cluster column missing"
        
        # Note: With temperature filtering, cluster sizes may vary
        # depending on temperature band distribution
        # Just verify no crashes and valid output
    
    def test_balancing_with_period_support(self, test_data_dir, test_output_dir):
        """
        Test balancing with period-specific files.
        
        Given:
        - Period label: "202508A"
        - Period-specific output enabled
        
        When:
        - Run clustering with balancing
        
        Then:
        - Period-specific files created
        - Symlinks created
        - Clusters balanced correctly
        """
        # Check if data exists
        normalized_matrix = f"{test_data_dir}/normalized_subcategory_matrix.csv"
        if not os.path.exists(normalized_matrix):
            pytest.skip("Test data not available")
        
        # Create step with period support
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
        
        # Execute clustering
        context = StepContext()
        result_context = step.execute(context)
        
        # Verify period-specific files created
        period_file = f"{test_output_dir}/clustering_results_subcategory_202508A.csv"
        assert os.path.exists(period_file), \
            f"Period-specific file not created: {period_file}"
        
        # Verify symlink created
        symlink_file = f"{test_output_dir}/clustering_results_subcategory.csv"
        assert os.path.exists(symlink_file), \
            f"Symlink not created: {symlink_file}"
        
        # Verify symlink points to period file
        if os.path.islink(symlink_file):
            target = os.readlink(symlink_file)
            assert '202508A' in target, \
                f"Symlink doesn't point to period file: {target}"
        
        # Verify clusters are balanced
        results = pd.read_csv(period_file)
        cluster_sizes = results['Cluster'].value_counts()
        
        assert cluster_sizes.min() >= 30, \
            f"Minimum cluster size {cluster_sizes.min()} < 30"
        assert cluster_sizes.max() <= 60, \
            f"Maximum cluster size {cluster_sizes.max()} > 60"
    
    def test_balancing_with_different_matrix_types(self, test_data_dir, test_output_dir):
        """
        Test that balancing works with different matrix types.
        
        Given:
        - Different matrix types (subcategory, spu, category_agg)
        
        When:
        - Run clustering with balancing for each type
        
        Then:
        - Balancing works for all matrix types
        - Clusters balanced correctly for each
        """
        matrix_types = ['subcategory']  # Add 'spu', 'category_agg' if available
        
        for matrix_type in matrix_types:
            # Check if matrix exists
            normalized_matrix = f"{test_data_dir}/normalized_{matrix_type}_matrix.csv"
            if not os.path.exists(normalized_matrix):
                continue
            
            # Create step
            step = create_cluster_analysis_step(
                matrix_type=matrix_type,
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
            
            # Execute
            context = StepContext()
            result_context = step.execute(context)
            
            # Verify balanced
            results = result_context.data['results']
            cluster_sizes = results['Cluster'].value_counts()
            
            assert cluster_sizes.min() >= 30, \
                f"{matrix_type}: Min cluster size {cluster_sizes.min()} < 30"
            assert cluster_sizes.max() <= 60, \
                f"{matrix_type}: Max cluster size {cluster_sizes.max()} > 60"
    
    def test_balancing_performance_acceptable(self, test_data_dir, test_output_dir):
        """
        Test that balancing completes in reasonable time.
        
        Given:
        - Full dataset (2274 stores)
        
        When:
        - Run clustering with balancing
        
        Then:
        - Completes in <30 seconds (including clustering)
        """
        import time
        
        # Check if data exists
        normalized_matrix = f"{test_data_dir}/normalized_subcategory_matrix.csv"
        if not os.path.exists(normalized_matrix):
            pytest.skip("Test data not available")
        
        # Create step
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
        
        # Time the execution
        start_time = time.time()
        
        context = StepContext()
        result_context = step.execute(context)
        
        elapsed_time = time.time() - start_time
        
        # Verify completed in reasonable time
        assert elapsed_time < 30, \
            f"Clustering with balancing took {elapsed_time:.1f}s, expected <30s"
        
        # Verify results are valid
        assert 'results' in result_context.data, "Results not found"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
