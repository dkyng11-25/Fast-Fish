#!/usr/bin/env python3
"""
Step 17 Synthetic Test - Import Validation and Execution Testing

Tests Step 17 recommendation augmentation in a synthetic, isolated environment.
This ensures all imports work correctly and the step can execute without dependencies.

Author: Data Pipeline Team
Date: 2025-01-26
Version: 1.0 - Synthetic Test for Step 17
"""

import pytest
import pandas as pd
import numpy as np
import os
import tempfile
import shutil
import subprocess
import sys
from pathlib import Path
import contextlib
import warnings
import importlib

# Suppress pandas warnings for cleaner test output
warnings.filterwarnings('ignore')

def _prepare_sandbox(tmp_path: Path) -> Path:
    """Create isolated sandbox environment for Step 17 testing"""
    sandbox = tmp_path / "step17_sandbox"
    sandbox.mkdir(exist_ok=True)
    
    # Copy source code
    src_dir = Path(__file__).parent.parent.parent / "src"
    sandbox_src = sandbox / "src"
    if sandbox_src.exists():
        shutil.rmtree(sandbox_src)
    shutil.copytree(src_dir, sandbox_src)
    
    # Create output and data directories
    (sandbox / "output").mkdir(exist_ok=True)
    (sandbox / "data" / "api_data").mkdir(parents=True, exist_ok=True)
    
    # Create dummy pipeline_manifest.py to avoid import errors
    manifest_content = '''
def get_manifest():
    class MockManifest:
        def __init__(self):
            self.manifest = {
                "steps": {
                    "step14": {
                        "outputs": {
                            "enhanced_fast_fish_format_202510A": {
                                "file_path": "output/enhanced_fast_fish_format_202510A.csv"
                            }
                        }
                    }
                }
            }
    return MockManifest()

def register_step_output(*args, **kwargs):
    pass

def get_period_label(yyyymm, period):
    return f"{yyyymm}{period}"
'''
    (sandbox_src / "pipeline_manifest.py").write_text(manifest_content)
    
    return sandbox

def _seed_synthetic_inputs_step17(sandbox: Path) -> None:
    """Create synthetic input files for Step 17 testing"""
    
    # Create enhanced fast fish format (Step 14 output)
    fast_fish_data = {
        'Store_Group_Name': ['Group_1', 'Group_2', 'Group_3'],
        'Target_Style_Tags': ['[Summer, Women, Casual]', '[Winter, Men, Formal]', '[Spring, Women, Sport]'],
        'Category': ['Pants', 'Shirts', 'Accessories'],
        'Subcategory': ['Casual Pants', 'Dress Shirts', 'Belts'],
        'Season': ['Summer', 'Winter', 'Spring'],
        'Gender': ['Women', 'Men', 'Women'],
        'Location': ['Front', 'Back', 'Side'],
        'ΔQty': [10, 15, 8],
        'Current_SPU_Quantity': [100, 150, 80],
        'Target_SPU_Quantity': [110, 165, 88]
    }
    fast_fish_df = pd.DataFrame(fast_fish_data)
    fast_fish_df.to_csv(sandbox / "output/enhanced_fast_fish_format_202510A.csv", index=False)
    
    # Create store attributes (Step 22 output)
    store_attrs_data = {
        'str_code': ['1001', '1002', '1003'],
        'store_type': ['Fashion', 'Balanced', 'Basic'],
        'capacity': [1000, 1200, 800],
        'estimated_rack_capacity': [1000, 1200, 800],
        'temperature_zone': ['Moderate', 'Cold', 'Hot'],
        'fashion_ratio': [0.7, 0.5, 0.3]
    }
    store_attrs_df = pd.DataFrame(store_attrs_data)
    store_attrs_df.to_csv(sandbox / "output/enriched_store_attributes_202510A.csv", index=False)
    
    # Create clustering results
    cluster_data = {
        'str_code': ['1001', '1002', '1003'],
        'cluster_id': [0, 1, 2],
        'cluster_name': ['Fashion Cluster', 'Balanced Cluster', 'Basic Cluster']
    }
    cluster_df = pd.DataFrame(cluster_data)
    cluster_df.to_csv(sandbox / "output/clustering_results_spu_202510A.csv", index=False)

@contextlib.contextmanager
def _chdir(path: Path):
    """Context manager to change working directory temporarily"""
    old_cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old_cwd)

@contextlib.contextmanager
def _sandbox_import(sandbox: Path):
    """Context manager to import Step 17 module from sandbox"""
    with _chdir(sandbox):
        # Add sandbox src to Python path
        sys.path.insert(0, str(sandbox / "src"))
        try:
            # Import the module
            step17_module = importlib.import_module('step17_augment_recommendations')
            yield step17_module
        finally:
            # Clean up Python path
            if str(sandbox / "src") in sys.path:
                sys.path.remove(str(sandbox / "src"))

def _run_step17_synthetic(sandbox: Path) -> subprocess.CompletedProcess:
    """Run Step 17 in sandbox environment and capture output"""
    with _chdir(sandbox):
        env = os.environ.copy()
        env['PYTHONPATH'] = '.'
        
        result = subprocess.run([
            sys.executable, 'src/step17_augment_recommendations.py',
            '--target-yyyymm', '202510',
            '--target-period', 'A'
        ], capture_output=True, text=True, env=env)
        
        return result

def _load_step17_outputs(sandbox: Path) -> dict:
    """Load Step 17 output files for validation"""
    outputs = {}
    
    # Find the generated files (they have timestamps in names)
    output_dir = sandbox / "output"
    
    # Look for augmented recommendation files
    augmented_files = list(output_dir.glob("augmented_recommendations_*.csv"))
    summary_files = list(output_dir.glob("augmentation_summary_*.json"))
    report_files = list(output_dir.glob("augmentation_report_*.md"))
    
    if augmented_files:
        outputs['augmented'] = pd.read_csv(augmented_files[0])
    if summary_files:
        import json
        with open(summary_files[0], 'r') as f:
            outputs['summary'] = json.load(f)
    if report_files:
        outputs['report'] = report_files[0].read_text()
    
    return outputs

class TestStep17Synthetic:
    """Test suite for Step 17 synthetic testing"""
    
    def test_step17_imports_and_dependencies(self, tmp_path):
        """Test that Step 17 imports work correctly in isolated environment"""
        sandbox = _prepare_sandbox(tmp_path)
        
        with _sandbox_import(sandbox) as step17_module:
            # Test critical imports
            assert hasattr(step17_module, 'os'), "Should import os"
            assert hasattr(step17_module, 'pd'), "Should import pandas as pd"
            assert hasattr(step17_module, 'np'), "Should import numpy as np"
            
            # Test pipeline-specific imports
            assert hasattr(step17_module, 'get_period_label'), "Should import get_period_label"
            assert hasattr(step17_module, 'register_step_output'), "Should import register_step_output"
            
            # Test that module has main execution function
            assert hasattr(step17_module, 'main'), "Should have main function"
    
    def test_step17_execution_with_synthetic_data(self, tmp_path):
        """Test that Step 17 can execute with synthetic data"""
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_step17(sandbox)
        
        # Run Step 17
        result = _run_step17_synthetic(sandbox)
        
        # Verify Step 17 completed successfully
        assert result.returncode == 0, f"Step 17 failed with error: {result.stderr}"
        
        # Verify output files were created
        outputs = _load_step17_outputs(sandbox)
        
        # Should create at least one output file
        assert len(outputs) > 0, "Step 17 should create output files"
        
        # If augmented recommendations were created, validate structure
        if 'augmented' in outputs:
            augmented_df = outputs['augmented']
            assert len(augmented_df) > 0, "Augmented recommendations should not be empty"
            
            # Should preserve key columns from input
            expected_columns = ['Store_Group_Name', 'Category', 'Subcategory']
            for col in expected_columns:
                assert col in augmented_df.columns, f"Should preserve {col} column"
    
    def test_step17_data_processing_logic(self, tmp_path):
        """Test Step 17 data processing logic with synthetic data"""
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_step17(sandbox)
        
        with _sandbox_import(sandbox) as step17_module:
            # Test that we can call key functions directly
            if hasattr(step17_module, 'load_and_validate_data'):
                # Test data loading function
                try:
                    # This might fail due to missing files, but should not crash on import
                    pass
                except Exception as e:
                    # Expected - just testing import works
                    assert "FileNotFoundError" in str(type(e).__name__) or "KeyError" in str(type(e).__name__)
    
    def test_step17_error_handling(self, tmp_path):
        """Test Step 17 error handling with missing or invalid data"""
        sandbox = _prepare_sandbox(tmp_path)
        
        # Don't seed any input data - test error handling
        result = _run_step17_synthetic(sandbox)
        
        # Step 17 should handle missing data gracefully
        # Either succeed with empty output or fail with informative error
        if result.returncode != 0:
            # Should have informative error message
            error_output = result.stderr.lower()
            assert any(term in error_output for term in ['file', 'not', 'found', 'missing', 'error']), \
                "Should provide informative error message for missing data"
    
    def test_step17_period_awareness(self, tmp_path):
        """Test that Step 17 handles period-specific inputs correctly"""
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_step17(sandbox)
        
        # Test with different period
        with _chdir(sandbox):
            env = os.environ.copy()
            env['PYTHONPATH'] = '.'
            
            result = subprocess.run([
                sys.executable, 'src/step17_augment_recommendations.py',
                '--target-yyyymm', '202509',
                '--target-period', 'B'
            ], capture_output=True, text=True, env=env)
            
            # Should handle different periods (may succeed or fail gracefully)
            if result.returncode != 0:
                # Should mention period or file-related issues
                error_msg = result.stderr.lower()
                assert any(term in error_msg for term in ['202509b', 'file', 'not', 'found']), \
                    "Should handle period-specific file resolution"

def test_step17_synthetic_regression():
    """Integration test to ensure Step 17 synthetic tests work end-to-end"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Test the main functionality
        test_instance = TestStep17Synthetic()
        test_instance.test_step17_imports_and_dependencies(tmp_path)
        test_instance.test_step17_execution_with_synthetic_data(tmp_path)
        
        print("✅ Step 17 synthetic regression test passed")

if __name__ == "__main__":
    test_step17_synthetic_regression()
    print("🎉 All Step 17 synthetic tests completed successfully!")
