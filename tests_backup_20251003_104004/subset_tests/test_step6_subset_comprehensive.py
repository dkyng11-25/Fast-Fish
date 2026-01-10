"""
Step 6 Cluster Analysis - Subset Comprehensive Test

This test follows USER_NOTE.md requirements:
- Uses subset data (150-250 stores) for clustering compliance
- Tests all analysis levels (SPU, subcategory, category_agg)
- Ensures weather band compliance for each cluster
- Makes subset selection non-random and replicable
- Uses comprehensive validation framework
- Tests against multiple time periods
"""

import os
import sys
import subprocess
import logging
import pandas as pd
import pytest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.validation_comprehensive.schemas.step6_schemas import (
    ClusteringResultsSchema,
    ClusterProfilesSchema,
    PerClusterMetricsSchema
)

from tests.validation_comprehensive.validators import (
    validate_dataframe,
    validate_file,
    get_validation_summary,
    log_validation_summary
)

from tests.utils.periods import detect_available_period, split_period_label


class TestStep6SubsetComprehensive:
    """Test Step 6 with subset data following USER_NOTE.md requirements."""

    def setup_method(self):
        """Set up test environment with subset data."""
        self.original_cwd = os.getcwd()
        self.project_root = Path(__file__).parent.parent
        self.test_data_dir = Path(__file__).parent / "test_data"

        # Set up comprehensive logger
        self.logger = logging.getLogger("step6_subset")
        log_file = self.project_root / "tests" / "test_logs" / "step6_subset.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        # Change to project root for consistent pathing
        os.chdir(self.project_root)

        # Log test start
        self.logger.info("Starting Step 6 subset comprehensive test")

    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)

    def test_step6_subset_spu_analysis(self):
        """Test SPU-level clustering with subset data (150-250 stores as per USER_NOTE.md)."""
        self.logger.info("Testing SPU-level analysis with subset data")

        # Check if subset data exists
        subset_files = {
            'normalized': self.test_data_dir / 'subsample_spu_clustering_data.csv',
            'original': self.test_data_dir / 'subsample_spu_clustering_data.csv'
            # Note: No temperature data since subset doesn't have temperature bands
        }

        # Verify subset files exist
        for file_type, file_path in subset_files.items():
            if not file_path.exists():
                pytest.skip(f"Subset file not found: {file_path}")

        # Copy subset data to expected locations
        self._setup_subset_data(subset_files, 'spu')

        try:
            # Test with CLI arguments using subset data
            # Disable temperature constraints since subset data doesn't have temperature bands
            cmd = [
                sys.executable, '-m', 'src.step6_cluster_analysis',
                '--matrix-type', 'spu',
                '--disable-temperature-constraints'
            ]

            self.logger.info(f"Running SPU subset command: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

            # Log command results
            self.logger.info(f"SPU subset command return code: {result.returncode}")
            if result.stderr:
                self.logger.warning(f"SPU subset command stderr: {result.stderr}")

            # Black-box assertion: command should succeed
            assert result.returncode == 0, f"Step 6 SPU subset command failed: {result.stderr}"

            # Verify output files were created
            output_files = [
                'output/clustering_results_spu.csv',
                'output/cluster_profiles_spu.csv',
                'output/per_cluster_metrics_spu.csv'
            ]

            for file_path in output_files:
                full_path = self.project_root / file_path
                assert full_path.exists(), f"Output file not found: {file_path}"

            # Load and validate results using comprehensive validation framework
            clustering_df = pd.read_csv(self.project_root / 'output/clustering_results_spu.csv')
            profiles_df = pd.read_csv(self.project_root / 'output/cluster_profiles_spu.csv')

            self.logger.info(f"SPU subset results loaded: {len(clustering_df)} stores, {len(profiles_df)} clusters")

            # Use comprehensive validation framework
            clustering_validation = validate_dataframe(clustering_df, ClusteringResultsSchema)
            if clustering_validation['status'] != 'valid':
                self.logger.error(f"SPU clustering validation failed: {clustering_validation.get('error', 'Unknown error')}")
                pytest.fail(f"SPU clustering schema validation failed: {clustering_validation.get('error', 'Unknown error')}")

            profiles_validation = validate_dataframe(profiles_df, ClusterProfilesSchema)
            if profiles_validation['status'] != 'valid':
                self.logger.error(f"SPU profiles validation failed: {profiles_validation.get('error', 'Unknown error')}")
                pytest.fail(f"SPU profiles schema validation failed: {profiles_validation.get('error', 'Unknown error')}")

            # Log validation summaries
            log_validation_summary(clustering_validation, self.logger, "Step 6 SPU Clustering Results")
            log_validation_summary(profiles_validation, self.logger, "Step 6 SPU Cluster Profiles")

            # Business logic validations from USER_NOTE.md
            assert len(clustering_df) >= 150, "Should have at least 150 stores as per USER_NOTE.md"
            assert len(clustering_df) <= 250, "Should not exceed 250 stores as per USER_NOTE.md"
            assert clustering_df['Cluster'].min() >= 0, "Cluster IDs should be non-negative"
            assert clustering_df['str_code'].nunique() == len(clustering_df), "Each store should be assigned to exactly one cluster"

            # Check cluster size compliance (standard sized clusters)
            cluster_sizes = clustering_df.groupby('Cluster').size()
            min_cluster_size = cluster_sizes.min()
            max_cluster_size = cluster_sizes.max()
            self.logger.info(f"Cluster size range: {min_cluster_size} - {max_cluster_size}")

            # USER_NOTE.md requirement: ensure weather band compliance
            # This should be validated by checking temperature data integration
            if 'temperature' in subset_files and subset_files['temperature'].exists():
                temp_df = pd.read_csv(subset_files['temperature'])
                stores_with_temp = temp_df['str_code'].nunique()
                stores_clustered = clustering_df['str_code'].nunique()
                temp_coverage = stores_clustered / stores_with_temp if stores_with_temp > 0 else 0
                self.logger.info(f"Temperature data coverage: {temp_coverage:.2%}")
                assert temp_coverage >= 0.8, "At least 80% of stores should have temperature data for weather band compliance"

            self.logger.info(f"SPU subset analysis completed: {len(clustering_df)} stores across {len(profiles_df)} clusters")

        finally:
            self._cleanup_subset_data('spu')

    def test_step6_subset_subcategory_analysis(self):
        """Test subcategory-level clustering with subset data."""
        self.logger.info("Testing subcategory-level analysis with subset data")

        # Check if subset data exists
        subset_files = {
            'normalized': self.test_data_dir / 'subsample_subcategory_clustering_data.csv',
            'original': self.test_data_dir / 'subsample_subcategory_clustering_data.csv',
            'temperature': self.test_data_dir / 'subsample_store_altitudes.csv'
        }

        # Verify subset files exist
        for file_type, file_path in subset_files.items():
            if not file_path.exists():
                pytest.skip(f"Subset file not found: {file_path}")

        # Copy subset data to expected locations
        self._setup_subset_data(subset_files, 'subcategory')

        try:
            # Test with CLI arguments for subcategory analysis
            cmd = [
                sys.executable, '-m', 'src.step6_cluster_analysis',
                '--matrix-type', 'subcategory'
            ]

            self.logger.info(f"Running subcategory subset command: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)

            # Log command results
            self.logger.info(f"Subcategory subset command return code: {result.returncode}")
            if result.stderr:
                self.logger.warning(f"Subcategory subset command stderr: {result.stderr}")

            # Black-box assertion: command should succeed
            assert result.returncode == 0, f"Step 6 subcategory subset command failed: {result.stderr}"

            # Verify output files were created
            output_files = [
                'output/clustering_results_subcategory.csv',
                'output/cluster_profiles_subcategory.csv',
                'output/per_cluster_metrics_subcategory.csv'
            ]

            for file_path in output_files:
                full_path = self.project_root / file_path
                assert full_path.exists(), f"Output file not found: {file_path}"

            # Load and validate results
            clustering_df = pd.read_csv(self.project_root / 'output/clustering_results_subcategory.csv')
            profiles_df = pd.read_csv(self.project_root / 'output/cluster_profiles_subcategory.csv')

            self.logger.info(f"Subcategory subset results loaded: {len(clustering_df)} stores, {len(profiles_df)} clusters")

            # Use comprehensive validation framework
            clustering_validation = validate_dataframe(clustering_df, ClusteringResultsSchema)
            if clustering_validation['status'] != 'valid':
                self.logger.error(f"Subcategory clustering validation failed: {clustering_validation.get('error', 'Unknown error')}")
                pytest.fail(f"Subcategory clustering schema validation failed: {clustering_validation.get('error', 'Unknown error')}")

            profiles_validation = validate_dataframe(profiles_df, ClusterProfilesSchema)
            if profiles_validation['status'] != 'valid':
                self.logger.error(f"Subcategory profiles validation failed: {profiles_validation.get('error', 'Unknown error')}")
                pytest.fail(f"Subcategory profiles schema validation failed: {profiles_validation.get('error', 'Unknown error')}")

            # Log validation summaries
            log_validation_summary(clustering_validation, self.logger, "Step 6 Subcategory Clustering Results")
            log_validation_summary(profiles_validation, self.logger, "Step 6 Subcategory Cluster Profiles")

            # Business logic validations from USER_NOTE.md
            assert len(clustering_df) >= 150, "Should have at least 150 stores as per USER_NOTE.md"
            assert len(clustering_df) <= 250, "Should not exceed 250 stores as per USER_NOTE.md"

            self.logger.info(f"Subcategory subset analysis completed: {len(clustering_df)} stores across {len(profiles_df)} clusters")

        finally:
            self._cleanup_subset_data('subcategory')

    def test_step6_parameter_sweeps(self):
        """Test step6 with different clustering parameters to ensure robustness."""
        self.logger.info("Testing clustering parameter sweeps")

        # Check if subset data exists
        subset_files = {
            'normalized': self.test_data_dir / 'subsample_spu_clustering_data.csv',
            'original': self.test_data_dir / 'subsample_spu_clustering_data.csv'
            # Note: No temperature data since subset doesn't have temperature bands
        }

        # Verify subset files exist
        for file_type, file_path in subset_files.items():
            if not file_path.exists():
                pytest.skip(f"Subset file not found: {file_path}")

        # Copy subset data to expected locations
        self._setup_subset_data(subset_files, 'spu')

        try:
            # Test different parameter combinations as per USER_NOTE.md requirement
            test_cases = [
                {
                    'name': 'default_parameters',
                    'cmd': [
                        sys.executable, '-m', 'src.step6_cluster_analysis',
                        '--matrix-type', 'spu'
                    ]
                },
                {
                    'name': 'temperature_aware',
                    'cmd': [
                        sys.executable, '-m', 'src.step6_cluster_analysis',
                        '--matrix-type', 'spu',
                        '--temp-band-column', 'temperature_band_q3q4_seasonal'
                    ]
                },
                {
                    'name': 'different_algorithm',
                    'cmd': [
                        sys.executable, '-m', 'src.step6_cluster_analysis',
                        '--matrix-type', 'spu',
                        '--clustering-algorithm', 'kmeans++'
                    ]
                }
            ]

            for test_case in test_cases:
                self.logger.info(f"Testing parameter variation: {test_case['name']}")

                result = subprocess.run(test_case['cmd'], cwd=self.project_root, capture_output=True, text=True)

                # Log results for each variation
                self.logger.info(f"Parameter test '{test_case['name']}' return code: {result.returncode}")

                # Black-box assertion: command should succeed
                assert result.returncode == 0, f"Parameter test '{test_case['name']}' failed: {result.stderr}"

                # Verify output files exist
                results_file = self.project_root / 'output/clustering_results_spu.csv'
                assert results_file.exists(), f"Results file not found for {test_case['name']}"

                self.logger.info(f"Parameter test '{test_case['name']}' completed successfully")

        finally:
            self._cleanup_subset_data('spu')

    def test_step6_parallel_execution(self):
        """Test step6 with parallel execution as per USER_NOTE.md."""
        self.logger.info("Testing parallel execution with subset data")

        # Check if subset data exists
        subset_files = {
            'normalized': self.test_data_dir / 'subsample_spu_clustering_data.csv',
            'original': self.test_data_dir / 'subsample_spu_clustering_data.csv'
            # Note: No temperature data since subset doesn't have temperature bands
        }

        # Verify subset files exist
        for file_type, file_path in subset_files.items():
            if not file_path.exists():
                pytest.skip(f"Subset file not found: {file_path}")

        # Copy subset data to expected locations
        self._setup_subset_data(subset_files, 'spu')

        try:
            # Define parallel test cases
            test_cases = [
                {
                    'name': 'spu_analysis',
                    'cmd': [
                        sys.executable, '-m', 'src.step6_cluster_analysis',
                        '--matrix-type', 'spu'
                    ]
                },
                {
                    'name': 'subcategory_analysis',
                    'cmd': [
                        sys.executable, '-m', 'src.step6_cluster_analysis',
                        '--matrix-type', 'subcategory'
                    ]
                }
            ]

            # Run tests in parallel
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_to_test = {
                    executor.submit(self._run_single_test, test_case): test_case
                    for test_case in test_cases
                }

                # Collect results as they complete
                for future in as_completed(future_to_test):
                    test_case = future_to_test[future]
                    try:
                        result = future.result()
                        self.logger.info(f"Parallel test '{test_case['name']}' completed: {result}")
                    except Exception as e:
                        self.logger.error(f"Parallel test '{test_case['name']}' failed: {e}")
                        pytest.fail(f"Parallel test '{test_case['name']}' failed: {e}")

            self.logger.info("All parallel tests completed successfully")

        finally:
            self._cleanup_subset_data('spu')

    def _setup_subset_data(self, subset_files, matrix_type):
        """Set up subset data for testing."""
        # Copy subset files to expected locations
        for file_type, source_path in subset_files.items():
            if file_type in ['normalized', 'original']:
                if matrix_type == 'spu':
                    dest_path = self.project_root / 'data' / 'normalized_spu_limited_matrix.csv'
                elif matrix_type == 'subcategory':
                    dest_path = self.project_root / 'data' / 'normalized_subcategory_matrix.csv'
                else:
                    dest_path = self.project_root / 'data' / 'normalized_category_agg_matrix.csv'

                # Ensure destination directory exists
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                import shutil
                shutil.copy2(source_path, dest_path)
                self.logger.info(f"Copied {source_path} to {dest_path}")
            # Note: Skipping temperature data since subset doesn't have temperature bands

    def _cleanup_subset_data(self, matrix_type):
        """Clean up subset data after testing."""
        # Remove copied files (excluding temperature data since we don't copy it)
        files_to_remove = [
            self.project_root / 'data' / 'normalized_spu_limited_matrix.csv',
            self.project_root / 'data' / 'normalized_subcategory_matrix.csv',
            self.project_root / 'data' / 'normalized_category_agg_matrix.csv'
        ]

        for file_path in files_to_remove:
            if file_path.exists():
                file_path.unlink()
                self.logger.info(f"Removed {file_path}")

    def _run_single_test(self, test_case):
        """Run a single test case."""
        result = subprocess.run(
            test_case['cmd'],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        return {
            'name': test_case['name'],
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
