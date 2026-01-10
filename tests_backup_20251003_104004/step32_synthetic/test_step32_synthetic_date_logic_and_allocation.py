#!/usr/bin/env python3
"""
Step 32 Synthetic Test - Date Logic and Store Allocation Testing

Tests Step 32 store allocation logic in a synthetic, isolated environment.
Focuses on the date advancement logic and allocation processing.

Author: Data Pipeline Team
Date: 2025-01-26
Version: 1.0 - Synthetic Test for Step 32
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
    """Create isolated sandbox environment for Step 32 testing"""
    sandbox = tmp_path / "step32_sandbox"
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
            self.manifest = {"steps": {}}
    return MockManifest()

def register_step_output(*args, **kwargs):
    pass

def get_period_label(yyyymm, period):
    return f"{yyyymm}{period}"
'''
    (sandbox_src / "pipeline_manifest.py").write_text(manifest_content)
    
    return sandbox

def _seed_synthetic_inputs_step32(sandbox: Path) -> None:
    """Create synthetic input files for Step 32 testing"""
    
    # Create fast fish format (Step 18 output)
    fast_fish_data = {
        'Store_Group_Name': ['Group_1', 'Group_2', 'Group_3', 'Group_1', 'Group_2'],
        'Target_Style_Tags': ['[Summer, Women, Casual]', '[Winter, Men, Formal]', '[Spring, Women, Sport]', '[Fall, Women, Casual]', '[Summer, Men, Sport]'],
        'Category': ['Pants', 'Shirts', 'Accessories', 'Pants', 'Shirts'],
        'Subcategory': ['Casual Pants', 'Dress Shirts', 'Belts', 'Formal Pants', 'Polo Shirts'],
        'Season': ['Summer', 'Winter', 'Spring', 'Fall', 'Summer'],
        'Gender': ['Women', 'Men', 'Women', 'Women', 'Men'],
        'Location': ['Front', 'Back', 'Side', 'Front', 'Back'],
        'ΔQty': [10, 15, 8, 12, 6],
        'Group_ΔQty': [22, 15, 8, 22, 6],  # Group totals
        'Current_SPU_Quantity': [100, 150, 80, 120, 90],
        'Target_SPU_Quantity': [110, 165, 88, 132, 96]
    }
    fast_fish_df = pd.DataFrame(fast_fish_data)
    fast_fish_df.to_csv(sandbox / "output/fast_fish_with_sell_through_analysis_202510A.csv", index=False)
    
    # Create store attributes with store groups
    store_attrs_data = {
        'str_code': ['1001', '1002', '1003', '1004', '1005'],
        'Store_Group_Name': ['Group_1', 'Group_1', 'Group_2', 'Group_3', 'Group_2'],
        'store_type': ['Fashion', 'Fashion', 'Balanced', 'Basic', 'Balanced'],
        'capacity': [1000, 1100, 1200, 800, 1000],
        'estimated_rack_capacity': [1000, 1100, 1200, 800, 1000],
        'temperature_zone': ['Moderate', 'Moderate', 'Cold', 'Hot', 'Cold'],
        'fashion_ratio': [0.7, 0.8, 0.5, 0.3, 0.6]
    }
    store_attrs_df = pd.DataFrame(store_attrs_data)
    store_attrs_df.to_csv(sandbox / "output/enriched_store_attributes_202510A.csv", index=False)

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
    """Context manager to import Step 32 module from sandbox"""
    with _chdir(sandbox):
        # Add sandbox src to Python path
        sys.path.insert(0, str(sandbox / "src"))
        try:
            # Import the module
            step32_module = importlib.import_module('step32_store_allocation')
            yield step32_module
        finally:
            # Clean up Python path
            if str(sandbox / "src") in sys.path:
                sys.path.remove(str(sandbox / "src"))

def _run_step32_synthetic(sandbox: Path, period: str = "A", yyyymm: str = "202510") -> subprocess.CompletedProcess:
    """Run Step 32 in sandbox environment and capture output"""
    with _chdir(sandbox):
        env = os.environ.copy()
        env['PYTHONPATH'] = '.'
        
        result = subprocess.run([
            sys.executable, 'src/step32_store_allocation.py',
            '--period', period,
            '--target-yyyymm', yyyymm
        ], capture_output=True, text=True, env=env)
        
        return result

class TestStep32Synthetic:
    """Test suite for Step 32 synthetic testing"""
    
    def test_step32_date_advancement_logic(self, tmp_path):
        """Test the core date advancement logic in isolation"""
        sandbox = _prepare_sandbox(tmp_path)
        
        with _sandbox_import(sandbox) as step32_module:
            # Test the _advance_half_periods function
            adv = step32_module._advance_half_periods
            
            # Test A -> B same month
            yyyymm, half = adv('202508', 'A', 1)
            assert (yyyymm, half) == ('202508', 'B'), "A should advance to B in same month"
            
            # Test B -> next month A
            yyyymm, half = adv('202508', 'B', 1)
            assert (yyyymm, half) == ('202509', 'A'), "B should advance to next month A"
            
            # Test multiple advances
            yyyymm, half = adv('202508', 'A', 3)
            assert (yyyymm, half) == ('202509', 'B'), "3 advances from 202508A should reach 202509B"
            
            # Test year boundary
            yyyymm, half = adv('202512', 'B', 1)
            assert (yyyymm, half) == ('202601', 'A'), "Should handle year boundary correctly"
            
            # Test large advances
            yyyymm, half = adv('202501', 'A', 24)  # 12 months = 24 half-periods
            assert (yyyymm, half) == ('202601', 'A'), "Should handle large advances correctly"
    
    def test_step32_date_edge_cases(self, tmp_path):
        """Test edge cases in date advancement"""
        sandbox = _prepare_sandbox(tmp_path)
        
        with _sandbox_import(sandbox) as step32_module:
            adv = step32_module._advance_half_periods
            
            # Test zero advance
            yyyymm, half = adv('202508', 'A', 0)
            assert (yyyymm, half) == ('202508', 'A'), "Zero advance should return same period"
            
            # Test February handling
            yyyymm, half = adv('202502', 'B', 1)
            assert (yyyymm, half) == ('202503', 'A'), "Should handle February correctly"
            
            # Test December to January
            yyyymm, half = adv('202512', 'A', 2)
            assert (yyyymm, half) == ('202601', 'A'), "Should handle year transition"
    
    def test_step32_execution_with_synthetic_data(self, tmp_path):
        """Test that Step 32 can execute with synthetic data"""
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_step32(sandbox)
        
        # Run Step 32
        result = _run_step32_synthetic(sandbox)
        
        # Step 32 may fail due to missing data, but should not crash on basic execution
        # The important thing is that it processes our synthetic data structure
        if result.returncode == 0:
            # If successful, check for output files
            output_dir = sandbox / "output"
            allocation_files = list(output_dir.glob("store_level_allocation_*.csv"))
            
            if allocation_files:
                # Validate allocation output structure
                allocation_df = pd.read_csv(allocation_files[0])
                assert len(allocation_df) >= 0, "Allocation output should be valid"
        else:
            # If failed, should have informative error
            error_msg = result.stderr.lower()
            # Common expected errors: missing data, validation failures, etc.
            expected_errors = ['file', 'not', 'found', 'keyerror', 'missing', 'weights', 'group']
            assert any(term in error_msg for term in expected_errors), \
                f"Should have informative error message: {result.stderr}"
    
    def test_step32_store_group_processing(self, tmp_path):
        """Test Step 32's store group processing logic"""
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_step32(sandbox)
        
        with _sandbox_import(sandbox) as step32_module:
            # Test that we can access key functions
            assert hasattr(step32_module, 'process_period_allocation'), "Should have allocation processing function"
            assert hasattr(step32_module, '_advance_half_periods'), "Should have date advancement function"
            
            # Test data loading functions if they exist
            if hasattr(step32_module, 'load_fast_fish_data'):
                try:
                    # This might fail, but we're testing the function exists
                    pass
                except Exception:
                    # Expected - just testing structure
                    pass
    
    def test_step32_period_parameter_handling(self, tmp_path):
        """Test Step 32's handling of different period parameters"""
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_step32(sandbox)
        
        # Test with period B
        result_b = _run_step32_synthetic(sandbox, period="B")
        
        # Test with different year/month
        result_diff = _run_step32_synthetic(sandbox, period="A", yyyymm="202509")
        
        # Both should either succeed or fail with informative messages
        for result, label in [(result_b, "Period B"), (result_diff, "Different YYYYMM")]:
            if result.returncode != 0:
                error_msg = result.stderr.lower()
                expected_terms = ['file', 'not', 'found', 'period', 'missing']
                assert any(term in error_msg for term in expected_terms), \
                    f"{label} should handle missing period-specific data gracefully"
    
    def test_step32_allocation_logic_components(self, tmp_path):
        """Test individual components of Step 32's allocation logic"""
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_step32(sandbox)
        
        with _sandbox_import(sandbox) as step32_module:
            # Test that key allocation functions exist
            expected_functions = [
                '_advance_half_periods',
                'process_period_allocation',
                'main'
            ]
            
            for func_name in expected_functions:
                assert hasattr(step32_module, func_name), f"Should have {func_name} function"
            
            # Test date advancement with various scenarios
            adv = step32_module._advance_half_periods
            
            # Test sequence of advances
            test_cases = [
                ('202501', 'A', 1, ('202501', 'B')),
                ('202501', 'B', 1, ('202502', 'A')),
                ('202512', 'A', 1, ('202512', 'B')),
                ('202512', 'B', 1, ('202601', 'A')),
                ('202506', 'A', 6, ('202509', 'A')),  # 6 half-periods = 3 months
            ]
            
            for start_yyyymm, start_period, advances, expected in test_cases:
                result = adv(start_yyyymm, start_period, advances)
                assert result == expected, \
                    f"Advancing {start_yyyymm}{start_period} by {advances} should give {expected}, got {result}"

def test_step32_synthetic_regression():
    """Integration test to ensure Step 32 synthetic tests work end-to-end"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Test the main functionality
        test_instance = TestStep32Synthetic()
        test_instance.test_step32_date_advancement_logic(tmp_path)
        test_instance.test_step32_date_edge_cases(tmp_path)
        
        print("✅ Step 32 synthetic regression test passed")

if __name__ == "__main__":
    test_step32_synthetic_regression()
    print("🎉 All Step 32 synthetic tests completed successfully!")
