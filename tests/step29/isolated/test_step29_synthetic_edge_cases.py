#!/usr/bin/env python3
"""
Step 29 Synthetic Test - Edge Cases and Data Integration

Tests edge cases and complex data integration scenarios for Step 29.
Focuses on testing the robustness of our duplicate column fixes under various conditions.

Author: Data Pipeline Team
Date: 2025-01-26
Version: 1.0 - Edge Case Testing
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

# Suppress pandas warnings for cleaner test output
warnings.filterwarnings('ignore')

def _prepare_sandbox(tmp_path: Path) -> Path:
    """Create isolated sandbox environment for Step 29 testing"""
    sandbox = tmp_path / "step29_sandbox"
    sandbox.mkdir(exist_ok=True)
    
    # Copy source code
    src_dir = Path(__file__).parent.parent.parent.parent / "src"
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
'''
    (sandbox_src / "pipeline_manifest.py").write_text(manifest_content)
    
    return sandbox

@contextlib.contextmanager
def _chdir(path: Path):
    """Context manager to change working directory temporarily"""
    old_cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old_cwd)

def _run_step29(sandbox: Path) -> subprocess.CompletedProcess:
    """Run Step 29 in sandbox environment and capture output"""
    with _chdir(sandbox):
        env = os.environ.copy()
        env['PYTHONPATH'] = '.'
        
        result = subprocess.run([
            sys.executable, 'src/step29_supply_demand_gap_analysis.py',
            '--target-yyyymm', '202510',
            '--target-period', 'A'
        ], capture_output=True, text=True, env=env)
        
        return result

class TestStep29EdgeCases:
    """Test suite for Step 29 edge cases and complex scenarios"""
    
    def test_empty_dataframes_with_duplicates(self, tmp_path):
        """Test handling of empty DataFrames that still have duplicate column structure"""
        sandbox = _prepare_sandbox(tmp_path)
        
        # Create empty sales data (without cluster_id)
        sales_df = pd.DataFrame(columns=['spu_code', 'str_code', 'fashion_sal_amt', 'basic_sal_amt', 
                                       'fashion_sal_qty', 'basic_sal_qty'])
        sales_df.to_csv(sandbox / "data/api_data/complete_spu_sales_202510A.csv", index=False)
        
        # Empty cluster data with cluster_id
        cluster_df = pd.DataFrame(columns=['str_code', 'Cluster', 'cluster_id'])
        cluster_df.to_csv(sandbox / "output/clustering_results_spu_202510A.csv", index=False)
        
        # Empty other required files
        for filename, columns in [
            ("product_role_classifications.csv", ['spu_code', 'product_role', 'category', 'subcategory']),
            ("price_band_analysis.csv", ['spu_code', 'price_band', 'avg_unit_price']),
            ("enriched_store_attributes_202510A_20250926_220259.csv", ['str_code', 'store_type', 'capacity'])
        ]:
            empty_df = pd.DataFrame(columns=columns)
            empty_df.to_csv(sandbox / f"output/{filename}", index=False)
        
        # Run Step 29
        result = _run_step29(sandbox)
        
        # Should handle empty data gracefully
        assert result.returncode == 0, f"Step 29 should handle empty data: {result.stderr}"
        
        # Should still create output files even with empty input
        output_dir = sandbox / "output"
        gap_files = list(output_dir.glob("supply_demand_gap_*"))
        assert len(gap_files) > 0, "Should create output files even with empty input"
    
    def test_single_row_with_multiple_duplicates(self, tmp_path):
        """Test handling of single-row DataFrames with multiple duplicate columns"""
        sandbox = _prepare_sandbox(tmp_path)
        
        # Single row with some duplicate columns (but not cluster_id)
        sales_data = {
            'spu_code': ['SPU001'],
            'str_code': ['1001'],
            'fashion_sal_amt': [1000],
            'basic_sal_amt': [500],
            'fashion_sal_qty': [10],
            'basic_sal_qty': [5]
            # Removed cluster_id - this should come from cluster merge
        }
        sales_df = pd.DataFrame(sales_data)
        sales_df.to_csv(sandbox / "data/api_data/complete_spu_sales_202510A.csv", index=False)
        
        # Single row cluster data with duplicates
        cluster_data = {
            'str_code': ['1001'],
            'Cluster': [0],
            'cluster_id': [0],
            'cluster_id_alt': [0],
            'cluster_name': ['Test Cluster'],
            'cluster_name_dup': ['Test Cluster']
        }
        cluster_df = pd.DataFrame(cluster_data)
        cluster_df.to_csv(sandbox / "output/clustering_results_spu_202510A.csv", index=False)
        
        # Single row other files
        roles_data = {
            'spu_code': ['SPU001'],
            'product_role': ['CORE'],
            'category': ['Pants'],
            'subcategory': ['Casual']
        }
        roles_df = pd.DataFrame(roles_data)
        roles_df.to_csv(sandbox / "output/product_role_classifications.csv", index=False)
        
        price_data = {
            'spu_code': ['SPU001'],
            'price_band': ['VALUE'],
            'avg_unit_price': [100.0]
        }
        price_df = pd.DataFrame(price_data)
        price_df.to_csv(sandbox / "output/price_band_analysis.csv", index=False)
        
        store_attrs_data = {
            'str_code': ['1001'],
            'store_type': ['Fashion'],
            'capacity': [1000],
            'estimated_rack_capacity': [1000]  # Required by downstream steps
        }
        store_attrs_df = pd.DataFrame(store_attrs_data)
        store_attrs_df.to_csv(sandbox / "output/enriched_store_attributes_202510A_20250926_220259.csv", index=False)
        
        # Run Step 29
        result = _run_step29(sandbox)
        
        # Should handle single row with many duplicates
        assert result.returncode == 0, f"Step 29 should handle single row with duplicates: {result.stderr}"
        
        # Should detect and remove duplicate columns
        assert "⚠️ Removing duplicate columns" in result.stdout, \
            "Should detect duplicate columns"
    
    def test_mismatched_column_types_with_duplicates(self, tmp_path):
        """Test handling of duplicate columns with different data types"""
        sandbox = _prepare_sandbox(tmp_path)
        
        # Sales data with mixed types in some columns
        sales_data = {
            'spu_code': ['SPU001', 'SPU002'],
            'str_code': ['1001', '1002'],
            'fashion_sal_amt': [1000.0, 1500.0],
            'basic_sal_amt': [500.0, 300.0],
            'fashion_sal_qty': [10, 15],
            'basic_sal_qty': [5, 3]
            # Removed cluster_id - this should come from cluster merge
        }
        sales_df = pd.DataFrame(sales_data)
        sales_df.to_csv(sandbox / "data/api_data/complete_spu_sales_202510A.csv", index=False)
        
        # Cluster data with mixed types
        cluster_data = {
            'str_code': ['1001', '1002'],
            'Cluster': [0, 2],  # Integer
            'cluster_id': ['0', '2'],  # String - different type
            'cluster_id_float': [0.0, 2.0]  # Float - another type
        }
        cluster_df = pd.DataFrame(cluster_data)
        cluster_df.to_csv(sandbox / "output/clustering_results_spu_202510A.csv", index=False)
        
        # Create other required files
        roles_data = {
            'spu_code': ['SPU001', 'SPU002'],
            'product_role': ['CORE', 'SEASONAL'],
            'category': ['Pants', 'Tops'],
            'subcategory': ['Casual', 'T-Shirt']
        }
        roles_df = pd.DataFrame(roles_data)
        roles_df.to_csv(sandbox / "output/product_role_classifications.csv", index=False)
        
        price_data = {
            'spu_code': ['SPU001', 'SPU002'],
            'price_band': ['VALUE', 'PREMIUM'],
            'avg_unit_price': [100.0, 150.0]
        }
        price_df = pd.DataFrame(price_data)
        price_df.to_csv(sandbox / "output/price_band_analysis.csv", index=False)
        
        store_attrs_data = {
            'str_code': ['1001', '1002'],
            'store_type': ['Fashion', 'Basic'],
            'capacity': [1000, 1200],
            'estimated_rack_capacity': [1000, 1200]  # Required by downstream steps
        }
        store_attrs_df = pd.DataFrame(store_attrs_data)
        store_attrs_df.to_csv(sandbox / "output/enriched_store_attributes_202510A_20250926_220259.csv", index=False)
        
        # Run Step 29
        result = _run_step29(sandbox)
        
        # Should handle mixed type duplicates gracefully
        assert result.returncode == 0, f"Step 29 should handle mixed type duplicates: {result.stderr}"
        
        # Should detect duplicate columns regardless of type
        assert "⚠️ Removing duplicate columns" in result.stdout, \
            "Should detect duplicate columns with different types"
    
    def test_large_number_of_duplicate_columns(self, tmp_path):
        """Test performance with a large number of duplicate columns"""
        sandbox = _prepare_sandbox(tmp_path)
        
        # Create data with many duplicate columns
        base_data = {
            'spu_code': ['SPU001', 'SPU002'],
            'str_code': ['1001', '1002'],
            'fashion_sal_amt': [1000, 1500],
            'basic_sal_amt': [500, 300],
            'fashion_sal_qty': [10, 15],
            'basic_sal_qty': [5, 3]
        }
        
        # Add many duplicate non-cluster columns to sales data
        for i in range(20):
            base_data[f'sales_metric_dup_{i}'] = [100 + i, 200 + i]
        
        sales_df = pd.DataFrame(base_data)
        sales_df.to_csv(sandbox / "data/api_data/complete_spu_sales_202510A.csv", index=False)
        
        # Cluster data with many duplicates
        cluster_base = {
            'str_code': ['1001', '1002'],
            'Cluster': [0, 2],
            'cluster_id': [0, 2]  # Main cluster_id column
        }
        
        # Add many duplicate cluster columns
        for i in range(15):
            cluster_base[f'cluster_id_variant_{i}'] = [0, 2]
        
        cluster_df = pd.DataFrame(cluster_base)
        cluster_df.to_csv(sandbox / "output/clustering_results_spu_202510A.csv", index=False)
        
        # Create minimal other required files
        roles_data = {
            'spu_code': ['SPU001', 'SPU002'],
            'product_role': ['CORE', 'SEASONAL'],
            'category': ['Pants', 'Tops'],
            'subcategory': ['Casual', 'T-Shirt']
        }
        roles_df = pd.DataFrame(roles_data)
        roles_df.to_csv(sandbox / "output/product_role_classifications.csv", index=False)
        
        price_data = {
            'spu_code': ['SPU001', 'SPU002'],
            'price_band': ['VALUE', 'PREMIUM'],
            'avg_unit_price': [100.0, 150.0]
        }
        price_df = pd.DataFrame(price_data)
        price_df.to_csv(sandbox / "output/price_band_analysis.csv", index=False)
        
        store_attrs_data = {
            'str_code': ['1001', '1002'],
            'store_type': ['Fashion', 'Basic'],
            'capacity': [1000, 1200],
            'estimated_rack_capacity': [1000, 1200]  # Required by downstream steps
        }
        store_attrs_df = pd.DataFrame(store_attrs_data)
        store_attrs_df.to_csv(sandbox / "output/enriched_store_attributes_202510A_20250926_220259.csv", index=False)
        
        # Run Step 29
        result = _run_step29(sandbox)
        
        # Should handle large number of duplicates efficiently
        assert result.returncode == 0, f"Step 29 should handle many duplicates: {result.stderr}"
        
        # Should detect and report duplicate removal
        assert "⚠️ Removing duplicate columns" in result.stdout, \
            "Should detect many duplicate columns"

def test_step29_edge_cases_regression():
    """Integration test for Step 29 edge cases"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Test various edge cases
        test_instance = TestStep29EdgeCases()
        test_instance.test_single_row_with_multiple_duplicates(tmp_path)
        test_instance.test_mismatched_column_types_with_duplicates(tmp_path)
        
        print("✅ Step 29 edge cases regression test passed")

if __name__ == "__main__":
    test_step29_edge_cases_regression()
    print("🎉 All Step 29 edge case tests completed successfully!")
