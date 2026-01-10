#!/usr/bin/env python3
"""
Step 29 Synthetic Test - Duplicate Column Detection and Removal

Tests the duplicate column fixes we implemented in Step 29 supply-demand gap analysis.
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

# Suppress pandas warnings for cleaner test output
warnings.filterwarnings('ignore')

def _prepare_sandbox(tmp_path: Path) -> Path:
    """Create isolated sandbox environment for Step 29 testing"""
    sandbox = tmp_path / "step29_sandbox"
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
            self.manifest = {"steps": {}}
    return MockManifest()

def register_step_output(*args, **kwargs):
    pass
'''
    (sandbox_src / "pipeline_manifest.py").write_text(manifest_content)
    
    return sandbox

def _seed_synthetic_inputs_with_duplicates(sandbox: Path) -> None:
    """Create synthetic input files that will cause duplicate column issues"""
    
    # Create sales data (without cluster_id - that comes from cluster merge)
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
    
    # Create cluster data with BOTH 'Cluster' and 'cluster_id' columns (duplicate issue)
    cluster_data = {
        'str_code': ['1001', '1002', '1003'],
        'Cluster': [0, 2, 4],  # Original column name
        'cluster_id': [0, 2, 4]  # Duplicate column that causes the issue
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
        'estimated_rack_capacity': [1000, 1200, 800],  # Required by downstream steps
        'temperature_zone': ['Moderate', 'Cold', 'Hot']
    }
    store_attrs_df = pd.DataFrame(store_attrs_data)
    store_attrs_df.to_csv(sandbox / "output/enriched_store_attributes_202510A_20250926_220259.csv", index=False)

@contextlib.contextmanager
def _chdir(path: Path):
    """Context manager to change working directory temporarily"""
    old_cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old_cwd)

def _run_step29_with_duplicates(sandbox: Path) -> subprocess.CompletedProcess:
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

def _load_step29_outputs(sandbox: Path) -> dict:
    """Load Step 29 output files for validation"""
    outputs = {}
    
    # Find the generated files (they have timestamps in names)
    output_dir = sandbox / "output"
    
    # Look for supply-demand gap files
    gap_detailed_files = list(output_dir.glob("supply_demand_gap_detailed_*.csv"))
    gap_summary_files = list(output_dir.glob("supply_demand_gap_summary_*.json"))
    gap_report_files = list(output_dir.glob("supply_demand_gap_analysis_report_*.md"))
    
    if gap_detailed_files:
        outputs['detailed'] = pd.read_csv(gap_detailed_files[0])
    if gap_summary_files:
        import json
        with open(gap_summary_files[0], 'r') as f:
            outputs['summary'] = json.load(f)
    if gap_report_files:
        outputs['report'] = gap_report_files[0].read_text()
    
    return outputs

class TestStep29DuplicateColumns:
    """Test suite for Step 29 duplicate column handling"""
    
    def test_duplicate_column_detection_and_removal(self, tmp_path):
        """Test that Step 29 detects and removes duplicate columns correctly"""
        # Prepare sandbox with duplicate column data
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_with_duplicates(sandbox)
        
        # Run Step 29
        result = _run_step29_with_duplicates(sandbox)
        
        # Verify Step 29 completed successfully
        assert result.returncode == 0, f"Step 29 failed with error: {result.stderr}"
        
        # Verify duplicate column detection message appears in output
        assert "⚠️ Removing duplicate columns" in result.stdout, \
            "Expected duplicate column detection message not found in output"
        
        # Verify that cluster_id duplicate was detected
        assert "cluster_id" in result.stdout, \
            "Expected cluster_id duplicate detection not found"
        
        # Load and validate outputs
        outputs = _load_step29_outputs(sandbox)
        
        # Verify outputs were created
        assert 'detailed' in outputs, "Detailed gap analysis output not created"
        assert 'summary' in outputs, "Summary output not created"
        
        # Verify data structure integrity
        detailed_df = outputs['detailed']
        assert len(detailed_df) > 0, "Detailed output should contain analysis results"
        assert 'cluster_id' in detailed_df.columns, "cluster_id column should be present in output"
        
        # Verify no duplicate columns in final output
        assert not detailed_df.columns.duplicated().any(), \
            "Final output should not contain duplicate columns"
    
    def test_data_integration_with_duplicate_columns(self, tmp_path):
        """Test that data integration works correctly despite duplicate input columns"""
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_with_duplicates(sandbox)
        
        # Run Step 29
        result = _run_step29_with_duplicates(sandbox)
        assert result.returncode == 0, f"Step 29 failed: {result.stderr}"
        
        outputs = _load_step29_outputs(sandbox)
        
        # Verify that analysis was performed on representative clusters
        assert 'summary' in outputs
        summary = outputs['summary']
        
        # Check that clusters were analyzed (handle different output formats)
        if 'analysis_metadata' in summary:
            # New format with nested structure
            clusters_count = summary['analysis_metadata'].get('total_clusters_analyzed', 0)
        else:
            # Old format
            clusters_count = summary.get('clusters_analyzed', 0)
        
        assert clusters_count > 0, "Should have analyzed at least one cluster"
        
        # Verify cluster analysis results structure
        assert 'cluster_summaries' in summary
        cluster_summaries = summary['cluster_summaries']
        
        # Each cluster should have analysis results
        for cluster_key, cluster_data in cluster_summaries.items():
            assert 'overall_severity' in cluster_data
            assert 'category_diversity' in cluster_data
            assert cluster_data['overall_severity'] in ['critical', 'significant', 'moderate']
    
    def test_merge_operations_resilience(self, tmp_path):
        """Test that DataFrame merge operations handle duplicate columns gracefully"""
        sandbox = _prepare_sandbox(tmp_path)
        
        # Create even more complex duplicate scenario
        sales_data = {
            'spu_code': ['SPU001', 'SPU002'],
            'str_code': ['1001', '1002'],
            'fashion_sal_amt': [1000, 1500],
            'basic_sal_amt': [500, 300],
            'fashion_sal_qty': [10, 15],
            'basic_sal_qty': [5, 3]
            # Removed cluster_id and product_role - these should come from merges
        }
        sales_df = pd.DataFrame(sales_data)
        sales_df.to_csv(sandbox / "data/api_data/complete_spu_sales_202510A.csv", index=False)
        
        # Cluster data with multiple duplicate columns
        cluster_data = {
            'str_code': ['1001', '1002'],
            'Cluster': [0, 2],
            'cluster_id': [0, 2],  # Duplicate 1
            'cluster_name': ['Fashion Cluster', 'Basic Cluster']
        }
        cluster_df = pd.DataFrame(cluster_data)
        cluster_df.to_csv(sandbox / "output/clustering_results_spu_202510A.csv", index=False)
        
        # Roles data with internal duplicate columns
        roles_data = {
            'spu_code': ['SPU001', 'SPU002'],
            'product_role': ['CORE', 'SEASONAL'],
            'product_role_dup': ['CORE', 'SEASONAL'],  # Internal duplicate
            'category': ['Pants', 'Tops'],
            'subcategory': ['Casual Pants', 'T-Shirts']
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
            'estimated_rack_capacity': [1000, 1200]  # Required by downstream steps
        }
        store_attrs_df = pd.DataFrame(store_attrs_data)
        store_attrs_df.to_csv(sandbox / "output/enriched_store_attributes_202510A_20250926_220259.csv", index=False)
        
        # Run Step 29
        result = _run_step29_with_duplicates(sandbox)
        
        # Should complete successfully despite multiple duplicate columns
        assert result.returncode == 0, f"Step 29 should handle multiple duplicates: {result.stderr}"
        
        # Should detect and report multiple duplicate removals
        duplicate_messages = result.stdout.count("⚠️ Removing duplicate columns")
        assert duplicate_messages > 0, "Should detect duplicate columns"
        
        # Verify outputs are still created correctly
        outputs = _load_step29_outputs(sandbox)
        assert 'detailed' in outputs, "Should create detailed output despite duplicates"
        
        detailed_df = outputs['detailed']
        assert not detailed_df.columns.duplicated().any(), \
            "Final output must not have duplicate columns"

def test_step29_duplicate_column_regression():
    """Integration test to ensure Step 29 duplicate column fixes work end-to-end"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Test the main duplicate column scenario
        test_instance = TestStep29DuplicateColumns()
        test_instance.test_duplicate_column_detection_and_removal(tmp_path)
        
        print("✅ Step 29 duplicate column regression test passed")

if __name__ == "__main__":
    test_step29_duplicate_column_regression()
    print("🎉 All Step 29 synthetic tests completed successfully!")
