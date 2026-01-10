#!/usr/bin/env python3
"""
Step 31 Synthetic Test - Duplicate Column Detection and Removal

Tests the duplicate column fixes we implemented in Step 31 gap analysis workbook generation.
This test creates synthetic data that reproduces the duplicate column issue and verifies
that our fixes handle it correctly.

Author: Data Pipeline Team
Date: 2025-01-26
Version: 1.0 - Synthetic Test for Duplicate Column Fixes
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
import json

# Suppress pandas warnings for cleaner test output
warnings.filterwarnings('ignore')

def _prepare_sandbox(tmp_path: Path) -> Path:
    """Create isolated sandbox environment for Step 31 testing"""
    sandbox = tmp_path / "step31_sandbox"
    sandbox.mkdir()
    
    # Copy source code
    src_dir = Path(__file__).parent.parent.parent / "src"
    sandbox_src = sandbox / "src"
    shutil.copytree(src_dir, sandbox_src)
    
    # Create output and data directories
    (sandbox / "output").mkdir()
    (sandbox / "data" / "api_data").mkdir(parents=True)
    
    # Create dummy pipeline_manifest.py to avoid import errors
    manifest_content = '''
def get_manifest():
    class MockManifest:
        def __init__(self):
            self.manifest = {
                "steps": {
                    "step29": {
                        "outputs": {
                            "supply_demand_gap_detailed_202510A": {
                                "file_path": "output/supply_demand_gap_detailed_202510A_test.csv"
                            }
                        }
                    }
                }
            }
    return MockManifest()

def register_step_output(*args, **kwargs):
    pass
'''
    (sandbox_src / "pipeline_manifest.py").write_text(manifest_content)
    
    return sandbox

def _seed_synthetic_inputs_with_duplicates(sandbox: Path) -> None:
    """Create synthetic input files that will cause duplicate column issues in Step 31"""
    
    # Create sales data
    sales_data = {
        'spu_code': ['SPU001', 'SPU002', 'SPU003', 'SPU001', 'SPU002'],
        'str_code': ['1001', '1001', '1002', '1002', '1003'],
        'fashion_sal_amt': [1000, 1500, 800, 1200, 900],
        'basic_sal_amt': [500, 300, 400, 600, 350],
        'fashion_sal_qty': [10, 15, 8, 12, 9],
        'basic_sal_qty': [5, 3, 4, 6, 4]
    }
    sales_df = pd.DataFrame(sales_data)
    sales_df.to_csv(sandbox / "data/api_data/complete_spu_sales_202510A.csv", index=False)
    
    # Create cluster data with duplicate columns (the main issue)
    cluster_data = {
        'str_code': ['1001', '1002', '1003'],
        'Cluster': [0, 2, 4],  # Original column name
        'cluster_id': [0, 2, 4]  # Duplicate column that causes the merge issue
    }
    cluster_df = pd.DataFrame(cluster_data)
    cluster_df.to_csv(sandbox / "output/clustering_results_spu_202510A.csv", index=False)
    
    # Create product roles data
    roles_data = {
        'spu_code': ['SPU001', 'SPU002', 'SPU003'],
        'product_role': ['CORE', 'SEASONAL', 'FILLER'],
        'category': ['Pants', 'Tops', 'Accessories'],
        'subcategory': ['Casual Pants', 'T-Shirts', 'Belts']
    }
    roles_df = pd.DataFrame(roles_data)
    roles_df.to_csv(sandbox / "output/product_role_classifications.csv", index=False)
    
    # Create price bands data
    price_data = {
        'spu_code': ['SPU001', 'SPU002', 'SPU003'],
        'price_band': ['VALUE', 'PREMIUM', 'ECONOMY'],
        'avg_unit_price': [100.0, 150.0, 80.0]
    }
    price_df = pd.DataFrame(price_data)
    price_df.to_csv(sandbox / "output/price_band_analysis.csv", index=False)
    
    # Create store attributes data
    store_attrs_data = {
        'str_code': ['1001', '1002', '1003'],
        'store_type': ['Fashion', 'Balanced', 'Basic'],
        'capacity': [1000, 1200, 800],
        'estimated_rack_capacity': [1000, 1200, 800],  # Required by Step 31
        'temperature_zone': ['Moderate', 'Cold', 'Hot']
    }
    store_attrs_df = pd.DataFrame(store_attrs_data)
    store_attrs_df.to_csv(sandbox / "output/enriched_store_attributes.csv", index=False)
    
    # Create Step 29 supply-demand gap data (with potential duplicate columns)
    supply_demand_data = {
        'cluster_id': [0, 2, 4],
        'overall_gap_severity': ['critical', 'moderate', 'significant'],
        'category_diversity': [0.8, 0.6, 0.7],
        'subcategory_diversity': [0.9, 0.5, 0.8],
        'category_concentration': [0.3, 0.4, 0.2],
        'dominant_category': ['Pants', 'Tops', 'Accessories'],
        'dominant_category_share': [0.6, 0.7, 0.5],
        'fashion_ratio': [70.0, 60.0, 80.0],
        'basic_ratio': [30.0, 40.0, 20.0],
        'fashion_gap': ['moderate', 'low', 'high'],
        'style_gap_severity': ['moderate', 'low', 'critical'],
        'capacity_utilization': [0.85, 0.75, 0.90],
        'capacity_pressure': ['high', 'medium', 'high'],
        'cluster_id_duplicate': [0, 2, 4]  # This will cause duplicate column issue
    }
    supply_demand_df = pd.DataFrame(supply_demand_data)
    supply_demand_df.to_csv(sandbox / "output/supply_demand_gap_detailed_202510A_test.csv", index=False)

@contextlib.contextmanager
def _chdir(path: Path):
    """Context manager to change working directory temporarily"""
    old_cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old_cwd)

def _run_step31_with_duplicates(sandbox: Path) -> subprocess.CompletedProcess:
    """Run Step 31 in sandbox environment and capture output"""
    with _chdir(sandbox):
        env = os.environ.copy()
        env['PYTHONPATH'] = '.'
        
        result = subprocess.run([
            sys.executable, 'src/step31_gap_analysis_workbook.py',
            '--target-yyyymm', '202510',
            '--target-period', 'A'
        ], capture_output=True, text=True, env=env)
        
        return result

def _load_step31_outputs(sandbox: Path) -> dict:
    """Load Step 31 output files for validation"""
    outputs = {}
    
    # Find the generated files (they have timestamps in names)
    output_dir = sandbox / "output"
    
    # Look for gap analysis workbook files
    workbook_files = list(output_dir.glob("gap_analysis_workbook_*.xlsx"))
    coverage_files = list(output_dir.glob("cluster_coverage_matrix_*.csv"))
    summary_files = list(output_dir.glob("gap_workbook_executive_summary_*.json"))
    data_files = list(output_dir.glob("gap_analysis_workbook_data_*.csv"))
    
    if workbook_files:
        outputs['workbook_path'] = workbook_files[0]
    if coverage_files:
        outputs['coverage'] = pd.read_csv(coverage_files[0])
    if summary_files:
        with open(summary_files[0], 'r') as f:
            outputs['summary'] = json.load(f)
    if data_files:
        outputs['data'] = pd.read_csv(data_files[0])
    
    return outputs

class TestStep31DuplicateColumns:
    """Test suite for Step 31 duplicate column handling"""
    
    def test_duplicate_column_detection_and_removal(self, tmp_path):
        """Test that Step 31 detects and removes duplicate columns correctly"""
        # Prepare sandbox with duplicate column data
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_with_duplicates(sandbox)
        
        # Run Step 31
        result = _run_step31_with_duplicates(sandbox)
        
        # Verify Step 31 completed successfully
        assert result.returncode == 0, f"Step 31 failed with error: {result.stderr}"
        
        # Verify duplicate column detection message appears in output
        assert "⚠️ Removing duplicate columns" in result.stdout, \
            "Expected duplicate column detection message not found in output"
        
        # Load and validate outputs
        outputs = _load_step31_outputs(sandbox)
        
        # Verify outputs were created
        assert 'coverage' in outputs, "Coverage matrix output not created"
        assert 'summary' in outputs, "Summary output not created"
        assert 'data' in outputs, "Data output not created"
        
        # Verify data structure integrity
        coverage_df = outputs['coverage']
        assert len(coverage_df) > 0, "Coverage output should contain analysis results"
        
        # Verify no duplicate columns in final outputs
        assert not coverage_df.columns.duplicated().any(), \
            "Coverage output should not contain duplicate columns"
        
        data_df = outputs['data']
        assert not data_df.columns.duplicated().any(), \
            "Data output should not contain duplicate columns"
    
    def test_integrated_dataset_creation_with_duplicates(self, tmp_path):
        """Test that integrated dataset creation handles duplicate columns correctly"""
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_with_duplicates(sandbox)
        
        # Run Step 31
        result = _run_step31_with_duplicates(sandbox)
        assert result.returncode == 0, f"Step 31 failed: {result.stderr}"
        
        outputs = _load_step31_outputs(sandbox)
        
        # Verify that workbook was created successfully
        assert 'workbook_path' in outputs, "Excel workbook should be created"
        assert outputs['workbook_path'].exists(), "Excel workbook file should exist"
        
        # Verify summary contains expected structure
        assert 'summary' in outputs
        summary = outputs['summary']
        
        # Check key summary fields (handle different output formats)
        clusters_analyzed_key = 'clusters_analyzed' if 'clusters_analyzed' in summary else 'total_clusters_analyzed'
        if 'analysis_metadata' in summary:
            # New format with nested structure
            assert clusters_analyzed_key in summary or 'analysis_metadata' in summary
            if 'analysis_metadata' in summary:
                clusters_count = summary['analysis_metadata'].get('total_clusters_analyzed', 0)
            else:
                clusters_count = summary.get(clusters_analyzed_key, 0)
        else:
            # Old format
            assert clusters_analyzed_key in summary
            clusters_count = summary[clusters_analyzed_key]
        
        # Verify clusters were analyzed
        assert clusters_count > 0, "Should have analyzed at least one cluster"
    
    def test_multiple_dataframe_merge_resilience(self, tmp_path):
        """Test that multiple DataFrame merges handle various duplicate column scenarios"""
        sandbox = _prepare_sandbox(tmp_path)
        
        # Create complex duplicate scenario across multiple input files
        sales_data = {
            'spu_code': ['SPU001', 'SPU002'],
            'str_code': ['1001', '1002'],
            'fashion_sal_amt': [1000, 1500],
            'basic_sal_amt': [500, 300]
            # Removed cluster_id - this should come from cluster merge
        }
        sales_df = pd.DataFrame(sales_data)
        sales_df.to_csv(sandbox / "data/api_data/complete_spu_sales_202510A.csv", index=False)
        
        # Cluster data with multiple potential duplicates
        cluster_data = {
            'str_code': ['1001', '1002'],
            'Cluster': [0, 2],
            'cluster_id': [0, 2],  # Duplicate with sales
            'cluster_name': ['Fashion', 'Basic']
        }
        cluster_df = pd.DataFrame(cluster_data)
        cluster_df.to_csv(sandbox / "output/clustering_results_spu_202510A.csv", index=False)
        
        # Roles data
        roles_data = {
            'spu_code': ['SPU001', 'SPU002'],
            'product_role': ['CORE', 'SEASONAL'],
            'category': ['Pants', 'Tops'],
            'subcategory': ['Casual', 'T-Shirt']
        }
        roles_df = pd.DataFrame(roles_data)
        roles_df.to_csv(sandbox / "output/product_role_classifications.csv", index=False)
        
        # Price data
        price_data = {
            'spu_code': ['SPU001', 'SPU002'],
            'price_band': ['VALUE', 'PREMIUM'],
            'avg_unit_price': [100.0, 150.0]
        }
        price_df = pd.DataFrame(price_data)
        price_df.to_csv(sandbox / "output/price_band_analysis.csv", index=False)
        
        # Store attributes
        store_attrs_data = {
            'str_code': ['1001', '1002'],
            'store_type': ['Fashion', 'Basic'],
            'capacity': [1000, 1200],
            'estimated_rack_capacity': [1000, 1200]  # Required by Step 31
        }
        store_attrs_df = pd.DataFrame(store_attrs_data)
        store_attrs_df.to_csv(sandbox / "output/enriched_store_attributes.csv", index=False)
        
        # Supply-demand data with multiple duplicate columns
        supply_demand_data = {
            'cluster_id': [0, 2],
            'overall_gap_severity': ['critical', 'moderate'],
            'category_diversity': [0.8, 0.6],
            'cluster_id_dup1': [0, 2],  # Multiple duplicates
            'cluster_id_dup2': [0, 2],
            'fashion_ratio': [70.0, 60.0]
        }
        supply_demand_df = pd.DataFrame(supply_demand_data)
        supply_demand_df.to_csv(sandbox / "output/supply_demand_gap_detailed_202510A_test.csv", index=False)
        
        # Run Step 31
        result = _run_step31_with_duplicates(sandbox)
        
        # Should complete successfully despite multiple duplicate columns
        assert result.returncode == 0, f"Step 31 should handle multiple duplicates: {result.stderr}"
        
        # Should detect and report duplicate removals
        duplicate_messages = result.stdout.count("⚠️ Removing duplicate columns")
        assert duplicate_messages > 0, "Should detect duplicate columns"
        
        # Verify outputs are still created correctly
        outputs = _load_step31_outputs(sandbox)
        assert 'data' in outputs, "Should create data output despite duplicates"
        
        data_df = outputs['data']
        assert not data_df.columns.duplicated().any(), \
            "Final data output must not have duplicate columns"
    
    def test_excel_workbook_creation_with_duplicates(self, tmp_path):
        """Test that Excel workbook creation works correctly despite duplicate columns"""
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_with_duplicates(sandbox)
        
        # Run Step 31
        result = _run_step31_with_duplicates(sandbox)
        assert result.returncode == 0, f"Step 31 failed: {result.stderr}"
        
        outputs = _load_step31_outputs(sandbox)
        
        # Verify Excel workbook was created
        assert 'workbook_path' in outputs, "Excel workbook should be created"
        workbook_path = outputs['workbook_path']
        assert workbook_path.exists(), "Excel workbook file should exist"
        assert workbook_path.suffix == '.xlsx', "Should create Excel format file"
        
        # Verify file size is reasonable (not empty)
        assert workbook_path.stat().st_size > 1000, "Excel file should have substantial content"

def test_step31_duplicate_column_regression():
    """Integration test to ensure Step 31 duplicate column fixes work end-to-end"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Test the main duplicate column scenario
        test_instance = TestStep31DuplicateColumns()
        test_instance.test_duplicate_column_detection_and_removal(tmp_path)
        
        print("✅ Step 31 duplicate column regression test passed")

if __name__ == "__main__":
    test_step31_duplicate_column_regression()
    print("🎉 All Step 31 synthetic tests completed successfully!")
