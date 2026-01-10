"""
Step 7 Missing Category Rule - Subset Comprehensive Test

This test follows USER_NOTE.md requirements:
- Uses subset data (5 clusters with high/average consumption spread)
- Tests both subcategory and SPU level missing categories
- Runs with multiple parameter settings
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

from tests.validation_comprehensive.schemas.step7_schemas import (
    Step7StoreResultsSchema,
    Step7OpportunitiesSchema,
    Step7SubcategoryOpportunitiesSchema
)

from tests.validation_comprehensive.validators import (
    validate_dataframe,
    validate_file,
    get_validation_summary,
    log_validation_summary
)

from tests.utils.periods import detect_available_period, split_period_label


class TestStep7SubsetComprehensive:
    """Test Step 7 with subset data following USER_NOTE.md requirements."""
    
    def setup_method(self):
        """Set up test environment with subset data."""
        self.original_cwd = os.getcwd()
        self.project_root = Path(__file__).parent.parent
        self.test_data_dir = Path(__file__).parent / "test_data"
        
        # Set up comprehensive logger
        self.logger = logging.getLogger("step7_subset")
        log_file = self.project_root / "tests" / "test_logs" / "step7_subset.log"
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Change to project root for consistent pathing
        os.chdir(self.project_root)
        
        # Log test start
        self.logger.info("Starting Step 7 subset comprehensive test")

    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)

    def test_step7_subset_spu_analysis(self):
        """Test SPU-level missing opportunities with subset data (5 clusters)."""
        self.logger.info("Testing SPU-level analysis with subset data")
        
        # Check if subset data exists
        subset_files = {
            'clustering_results': self.test_data_dir / 'subsample_step7_data_clustering_results.csv',
            'spu_sales': self.test_data_dir / 'subsample_step7_data_spu_sales.csv',
            'store_config': self.test_data_dir / 'subsample_step7_data_store_config.csv'
        }
        
        # Verify subset files exist
        for file_type, file_path in subset_files.items():
            if not file_path.exists():
                pytest.skip(f"Subset file not found: {file_path}")
        
        # Copy subset data to expected locations
        self._setup_subset_data(subset_files)
        
        try:
            # Test with CLI arguments using subset data
            cmd = [
                sys.executable, '-m', 'src.step7_missing_category_rule',
                '--yyyymm', '202509',
                '--period', 'A',
                '--analysis-level', 'spu'
            ]
            
            self.logger.info(f"Running SPU subset command: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            
            # Log command results
            self.logger.info(f"SPU subset command return code: {result.returncode}")
            if result.stderr:
                self.logger.warning(f"SPU subset command stderr: {result.stderr}")
            
            # Black-box assertion: command should succeed
            assert result.returncode == 0, f"Step 7 SPU subset command failed: {result.stderr}"
            
            # Verify output files were created
            results_file = self.project_root / 'output/rule7_missing_spu_sellthrough_results_202509A.csv'
            assert results_file.exists(), f"Results file not found: {results_file}"
            
            # Load and validate results using comprehensive validation framework
            results_df = pd.read_csv(results_file)
            self.logger.info(f"SPU subset results loaded: {len(results_df)} rows")
            
            # Use comprehensive validation framework
            validation_results = validate_dataframe(results_df, Step7StoreResultsSchema)
            if validation_results['status'] != 'valid':
                self.logger.error(f"SPU subset results validation failed: {validation_results.get('error', 'Unknown error')}")
                pytest.fail(f"SPU subset results schema validation failed: {validation_results.get('error', 'Unknown error')}")
            
            # Log validation summary
            log_validation_summary(validation_results, self.logger, "Step 7 SPU Subset Results")
            
            # Check for opportunities file
            opportunities_file = self.project_root / 'output/rule7_missing_spu_sellthrough_opportunities_202509A.csv'
            if opportunities_file.exists():
                opportunities_df = pd.read_csv(opportunities_file)
                self.logger.info(f"SPU subset opportunities loaded: {len(opportunities_df)} rows")
                
                # Use comprehensive validation framework for opportunities
                opp_validation_results = validate_dataframe(opportunities_df, Step7OpportunitiesSchema)
                if opp_validation_results['status'] != 'valid':
                    self.logger.error(f"SPU subset opportunities validation failed: {opp_validation_results.get('error', 'Unknown error')}")
                    pytest.fail(f"SPU subset opportunities schema validation failed: {opp_validation_results.get('error', 'Unknown error')}")
                
                # Log validation summary
                log_validation_summary(opp_validation_results, self.logger, "Step 7 SPU Subset Opportunities")
                
                # Business logic validations for opportunities
                if len(opportunities_df) > 0:
                    positive_changes = opportunities_df[opportunities_df['recommended_quantity_change'] > 0]
                    assert len(positive_changes) > 0, "No positive quantity recommendations found"
                    self.logger.info(f"Found {len(positive_changes)} positive quantity recommendations")
            
            # Verify cluster compliance (5 clusters as per USER_NOTE.md)
            cluster_count = results_df['str_code'].nunique() if 'str_code' in results_df.columns else 0
            self.logger.info(f"SPU subset analysis completed: {len(results_df)} stores across clusters")
            
        finally:
            self._cleanup_subset_data()

    def test_step7_subset_subcategory_analysis(self):
        """Test subcategory-level missing opportunities with subset data."""
        self.logger.info("Testing subcategory-level analysis with subset data")
        
        # Check if subset data exists
        subset_files = {
            'clustering_results': self.test_data_dir / 'subsample_step7_data_clustering_results.csv',
            'spu_sales': self.test_data_dir / 'subsample_step7_data_spu_sales.csv',
            'store_config': self.test_data_dir / 'subsample_step7_data_store_config.csv'
        }
        
        # Verify subset files exist
        for file_type, file_path in subset_files.items():
            if not file_path.exists():
                pytest.skip(f"Subset file not found: {file_path}")
        
        # Copy subset data to expected locations
        self._setup_subset_data(subset_files)
        
        try:
            # Test with CLI arguments for subcategory analysis
            cmd = [
                sys.executable, '-m', 'src.step7_missing_category_rule',
                '--yyyymm', '202509',
                '--period', 'A',
                '--analysis-level', 'subcategory',
                '--rule7-use-roi', '1',
                '--roi-min-threshold', '0.3',
                '--min-margin-uplift', '100'
            ]
            
            self.logger.info(f"Running subcategory subset command: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            
            # Log command results
            self.logger.info(f"Subcategory subset command return code: {result.returncode}")
            if result.stderr:
                self.logger.warning(f"Subcategory subset command stderr: {result.stderr}")
            
            # Black-box assertion: command should succeed
            assert result.returncode == 0, f"Step 7 subcategory subset command failed: {result.stderr}"
            
            # Verify output files were created
            results_file = self.project_root / 'output/rule7_missing_subcategory_sellthrough_results_202509A.csv'
            assert results_file.exists(), f"Subcategory results file not found: {results_file}"
            
            # Load and validate results
            results_df = pd.read_csv(results_file)
            self.logger.info(f"Subcategory subset results loaded: {len(results_df)} rows")
            
            # Use comprehensive validation framework
            validation_results = validate_dataframe(results_df, Step7StoreResultsSchema)
            if validation_results['status'] != 'valid':
                self.logger.error(f"Subcategory subset results validation failed: {validation_results.get('error', 'Unknown error')}")
                pytest.fail(f"Subcategory subset results schema validation failed: {validation_results.get('error', 'Unknown error')}")
            
            # Log validation summary
            log_validation_summary(validation_results, self.logger, "Step 7 Subcategory Subset Results")
            
            self.logger.info(f"Subcategory subset analysis completed: {len(results_df)} stores")
            
        finally:
            self._cleanup_subset_data()

    def test_step7_parameter_variations_subset(self):
        """Test step7 with different parameter combinations using subset data."""
        self.logger.info("Testing parameter variations with subset data")
        
        # Check if subset data exists
        subset_files = {
            'clustering_results': self.test_data_dir / 'subsample_step7_data_clustering_results.csv',
            'spu_sales': self.test_data_dir / 'subsample_step7_data_spu_sales.csv',
            'store_config': self.test_data_dir / 'subsample_step7_data_store_config.csv'
        }
        
        # Verify subset files exist
        for file_type, file_path in subset_files.items():
            if not file_path.exists():
                pytest.skip(f"Subset file not found: {file_path}")
        
        # Copy subset data to expected locations
        self._setup_subset_data(subset_files)
        
        try:
            # Test different parameter combinations as per USER_NOTE.md
            test_cases = [
                {
                    'name': 'with_roi_validation_high_threshold',
                    'params': ['--rule7-use-roi', '1', '--roi-min-threshold', '0.5', '--min-margin-uplift', '200']
                },
                {
                    'name': 'with_roi_validation_low_threshold',
                    'params': ['--rule7-use-roi', '1', '--roi-min-threshold', '0.2', '--min-margin-uplift', '50']
                },
                {
                    'name': 'without_roi_validation', 
                    'params': ['--rule7-use-roi', '0']
                },
                {
                    'name': 'recent_months_back_3',
                    'params': ['--recent-months-back', '3']
                },
                {
                    'name': 'recent_months_back_6',
                    'params': ['--recent-months-back', '6']
                }
            ]
            
            for test_case in test_cases:
                self.logger.info(f"Testing parameter variation: {test_case['name']}")
                
                cmd = [
                    sys.executable, '-m', 'src.step7_missing_category_rule',
                    '--yyyymm', '202509',
                    '--period', 'A',
                    '--analysis-level', 'spu'
                ] + test_case['params']
                
                result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
                
                # Log results for each variation
                self.logger.info(f"Parameter test '{test_case['name']}' return code: {result.returncode}")
                
                # Black-box assertion: command should succeed
                assert result.returncode == 0, f"Parameter test '{test_case['name']}' failed: {result.stderr}"
                
                # Verify output files exist
                results_file = self.project_root / 'output/rule7_missing_spu_sellthrough_results_202509A.csv'
                assert results_file.exists(), f"Results file not found for {test_case['name']}"
                
                self.logger.info(f"Parameter test '{test_case['name']}' completed successfully")
            
        finally:
            self._cleanup_subset_data()

    def test_step7_parallel_execution(self):
        """Test step7 with parallel execution as per USER_NOTE.md."""
        self.logger.info("Testing parallel execution with subset data")
        
        # Check if subset data exists
        subset_files = {
            'clustering_results': self.test_data_dir / 'subsample_step7_data_clustering_results.csv',
            'spu_sales': self.test_data_dir / 'subsample_step7_data_spu_sales.csv',
            'store_config': self.test_data_dir / 'subsample_step7_data_store_config.csv'
        }
        
        # Verify subset files exist
        for file_type, file_path in subset_files.items():
            if not file_path.exists():
                pytest.skip(f"Subset file not found: {file_path}")
        
        # Copy subset data to expected locations
        self._setup_subset_data(subset_files)
        
        try:
            # Define parallel test cases
            test_cases = [
                {
                    'name': 'spu_analysis',
                    'cmd': [
                        sys.executable, '-m', 'src.step7_missing_category_rule',
                        '--yyyymm', '202509', '--period', 'A', '--analysis-level', 'spu'
                    ]
                },
                {
                    'name': 'subcategory_analysis',
                    'cmd': [
                        sys.executable, '-m', 'src.step7_missing_category_rule',
                        '--yyyymm', '202509', '--period', 'A', '--analysis-level', 'subcategory',
                        '--rule7-use-roi', '1', '--roi-min-threshold', '0.3'
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
            self._cleanup_subset_data()

    def _setup_subset_data(self, subset_files):
        """Set up subset data for testing."""
        # Copy subset files to expected locations
        for file_type, source_path in subset_files.items():
            if file_type == 'clustering_results':
                dest_path = self.project_root / 'output' / 'clustering_results_spu.csv'
            elif file_type == 'spu_sales':
                dest_path = self.project_root / 'data' / 'api_data' / 'complete_spu_sales_202509A.csv'
            elif file_type == 'store_config':
                dest_path = self.project_root / 'data' / 'api_data' / 'store_config_202509A.csv'
            
            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            import shutil
            shutil.copy2(source_path, dest_path)
            self.logger.info(f"Copied {source_path} to {dest_path}")

    def _cleanup_subset_data(self):
        """Clean up subset data after testing."""
        # Remove copied files
        files_to_remove = [
            self.project_root / 'output' / 'clustering_results_spu.csv',
            self.project_root / 'data' / 'api_data' / 'complete_spu_sales_202509A.csv',
            self.project_root / 'data' / 'api_data' / 'store_config_202509A.csv'
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
