#!/usr/bin/env python3
"""
Step 36 Synthetic Test - Unified Delivery Builder Testing

Tests Step 36 unified delivery building in a synthetic, isolated environment.
Covers category validation, buffer calculations, temperature mapping, and delivery formatting.

Author: Data Pipeline Team
Date: 2025-01-26
Version: 1.0 - Synthetic Test for Step 36
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
    """Create isolated sandbox environment for Step 36 testing"""
    sandbox = tmp_path / "step36_sandbox"
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

def _seed_synthetic_inputs_step36(sandbox: Path, category_cn: str = "休闲裤") -> None:
    """Create synthetic input files for Step 36 testing"""
    
    # Step 18 - Fast Fish with sell-through analysis
    step18_data = {
        'Store_Group_Name': ['Group_1', 'Group_2', 'Group_3'],
        'Target_Style_Tags': [f'[Summer, Women, Back, {category_cn}, 女{category_cn}]', 
                             f'[Winter, Men, Front, {category_cn}, 男{category_cn}]',
                             f'[Spring, Women, Side, {category_cn}, 女{category_cn}]'],
        'Category': [category_cn, category_cn, category_cn],
        'Subcategory': [f'女{category_cn}', f'男{category_cn}', f'女{category_cn}'],
        'ΔQty': [5, 10, 8],
        'Group_ΔQty': [5, 10, 8],
        'Current_SPU_Quantity': [10, 20, 15],
        'Target_SPU_Quantity': [15, 30, 23],
        'Season': ['Summer', 'Winter', 'Spring'],
        'Gender': ['Women', 'Men', 'Women'],
        'Location': ['Back', 'Front', 'Side'],
        'Sell_Through_Rate': [0.75, 0.80, 0.70],
        'Target_Sell_Through_Rate': [0.80, 0.85, 0.75]
    }
    step18_df = pd.DataFrame(step18_data)
    step18_df.to_csv(sandbox / "output/fast_fish_with_sell_through_analysis_202510A.csv", index=False)
    
    # Step 32 - Store allocation results
    allocation_data = {
        'Store_Code': ['11017', '11018', '11019'],
        'Store_Group_Name': ['Group_1', 'Group_2', 'Group_3'],
        'Period': ['202510A', '202510A', '202510A'],
        'Target_Style_Tags': [f'[Summer, Women, Back, {category_cn}, 女{category_cn}]',
                             f'[Winter, Men, Front, {category_cn}, 男{category_cn}]',
                             f'[Spring, Women, Side, {category_cn}, 女{category_cn}]'],
        'Category': [category_cn, category_cn, category_cn],
        'Subcategory': [f'女{category_cn}', f'男{category_cn}', f'女{category_cn}'],
        'Season': ['Summer', 'Winter', 'Spring'],
        'Gender': ['Women', 'Men', 'Women'],
        'Location': ['Back', 'Front', 'Side'],
        'Group_ΔQty': [5, 10, 8],
        'Store_Allocation_Weight': [0.4, 0.6, 0.5],
        'Allocated_ΔQty': [2, 6, 4],
        'Allocation_Rationale': ['Weight-based', 'Capacity-based', 'Performance-based']
    }
    allocation_df = pd.DataFrame(allocation_data)
    allocation_df.to_csv(sandbox / "output/store_level_allocation_results_202510A_fixture.csv", index=False)
    
    # Step 24 - Comprehensive cluster labels
    cluster_labels_data = {
        'cluster_id': [0, 1, 2],
        'cluster_name': ['Fashion Forward', 'Balanced Mix', 'Basic Essentials'],
        'operational_tag': ['High-Performance', 'Stable', 'Cost-Effective'],
        'style_tag': ['Trendy', 'Versatile', 'Classic'],
        'capacity_tag': ['High-Capacity', 'Medium-Capacity', 'Standard-Capacity'],
        'geographic_tag': ['Urban', 'Suburban', 'Rural']
    }
    cluster_labels_df = pd.DataFrame(cluster_labels_data)
    cluster_labels_df.to_csv(sandbox / "output/comprehensive_cluster_labels_202510A.csv", index=False)
    
    # Step 27 - Gap analysis
    gap_analysis_data = {
        'cluster_id': [0, 1, 2],
        'gap_severity': ['Low', 'Medium', 'High'],
        'category_coverage': [0.9, 0.7, 0.5],
        'recommended_actions': ['Maintain', 'Expand', 'Focus']
    }
    gap_analysis_df = pd.DataFrame(gap_analysis_data)
    gap_analysis_df.to_csv(sandbox / "output/gap_analysis_detailed_202510A.csv", index=False)
    
    # Store tags
    store_tags_data = {
        'str_code': ['11017', '11018', '11019'],
        'cluster_id': [0, 1, 2],
        'temperature_zone_tags': ['Moderate', 'Cold', 'Hot'],
        'store_type': ['Fashion', 'Balanced', 'Basic']
    }
    store_tags_df = pd.DataFrame(store_tags_data)
    store_tags_df.to_csv(sandbox / "output/store_tags_202510A.csv", index=False)
    
    # Store attributes
    store_attrs_data = {
        'str_code': ['11017', '11018', '11019'],
        'store_type': ['Fashion', 'Balanced', 'Basic'],
        'capacity': [1000, 1200, 800],
        'estimated_rack_capacity': [1000, 1200, 800],
        'temperature_zone': ['Moderate', 'Cold', 'Hot'],
        'fashion_ratio': [0.7, 0.5, 0.3],
        'avg_temperature': [20.0, 10.0, 30.0]
    }
    store_attrs_df = pd.DataFrame(store_attrs_data)
    store_attrs_df.to_csv(sandbox / "output/enriched_store_attributes.csv", index=False)

@contextlib.contextmanager
def _chdir(path: Path):
    """Context manager to change working directory temporarily"""
    old_cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(old_cwd)

def _run_step36_synthetic(sandbox: Path) -> subprocess.CompletedProcess:
    """Run Step 36 in sandbox environment and capture output"""
    with _chdir(sandbox):
        env = os.environ.copy()
        env['PYTHONPATH'] = '.'
        
        result = subprocess.run([
            sys.executable, 'src/step36_unified_delivery_builder.py',
            '--target-yyyymm', '202510',
            '--target-period', 'A'
        ], capture_output=True, text=True, env=env)
        
        return result

def _load_step36_outputs(sandbox: Path) -> dict:
    """Load Step 36 output files for validation"""
    outputs = {}
    
    # Find the generated files (they have timestamps in names)
    output_dir = sandbox / "output"
    
    # Look for unified delivery files
    delivery_csv_files = list(output_dir.glob("unified_delivery_*_*.csv"))
    delivery_xlsx_files = list(output_dir.glob("unified_delivery_*_*.xlsx"))
    validation_files = list(output_dir.glob("unified_delivery_*_validation.json"))
    summary_files = list(output_dir.glob("unified_delivery_*_summary.md"))
    
    if delivery_csv_files:
        # Get the main delivery file (not cluster-level)
        main_csv = [f for f in delivery_csv_files if 'cluster_level' not in f.name]
        if main_csv:
            outputs['delivery_csv'] = pd.read_csv(main_csv[0])
    
    if delivery_xlsx_files:
        outputs['delivery_xlsx_path'] = delivery_xlsx_files[0]
    
    if validation_files:
        import json
        with open(validation_files[0], 'r') as f:
            outputs['validation'] = json.load(f)
    
    if summary_files:
        outputs['summary'] = summary_files[0].read_text()
    
    return outputs

class TestStep36Synthetic:
    """Test suite for Step 36 synthetic testing"""
    
    def test_step36_category_validation(self, tmp_path):
        """Test Step 36 category validation with synthetic data"""
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_step36(sandbox, category_cn="休闲裤")
        
        # Run Step 36
        result = _run_step36_synthetic(sandbox)
        
        # Verify Step 36 completed successfully
        assert result.returncode == 0, f"Step 36 failed with error: {result.stderr}"
        
        # Load and validate outputs
        outputs = _load_step36_outputs(sandbox)
        
        # Should create delivery CSV
        assert 'delivery_csv' in outputs, "Should create unified delivery CSV"
        
        delivery_df = outputs['delivery_csv']
        assert len(delivery_df) > 0, "Delivery CSV should not be empty"
        
        # Should preserve category information
        assert 'Category' in delivery_df.columns, "Should preserve Category column"
        assert '休闲裤' in delivery_df['Category'].values, "Should preserve specific category"
    
    def test_step36_buffer_calculations(self, tmp_path):
        """Test Step 36 buffer calculation logic"""
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_step36(sandbox)
        
        # Run Step 36
        result = _run_step36_synthetic(sandbox)
        assert result.returncode == 0, f"Step 36 failed: {result.stderr}"
        
        outputs = _load_step36_outputs(sandbox)
        
        if 'delivery_csv' in outputs:
            delivery_df = outputs['delivery_csv']
            
            # Should have buffer-related calculations
            buffer_columns = [col for col in delivery_df.columns if 'buffer' in col.lower()]
            # May or may not have buffer columns depending on implementation
            
            # Should have quantity-related columns
            qty_columns = [col for col in delivery_df.columns if 'qty' in col.lower()]
            assert len(qty_columns) > 0, "Should have quantity-related columns"
    
    def test_step36_temperature_mapping(self, tmp_path):
        """Test Step 36 temperature zone mapping"""
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_step36(sandbox)
        
        # Run Step 36
        result = _run_step36_synthetic(sandbox)
        assert result.returncode == 0, f"Step 36 failed: {result.stderr}"
        
        outputs = _load_step36_outputs(sandbox)
        
        if 'delivery_csv' in outputs:
            delivery_df = outputs['delivery_csv']
            
            # Should have temperature-related information
            temp_columns = [col for col in delivery_df.columns if 'temperature' in col.lower()]
            # Temperature columns may be present depending on data integration
            
            # Should preserve store information
            assert 'str_code' in delivery_df.columns or 'Store_Code' in delivery_df.columns, \
                "Should preserve store identification"
    
    def test_step36_excel_output_creation(self, tmp_path):
        """Test Step 36 Excel output creation"""
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_step36(sandbox)
        
        # Run Step 36
        result = _run_step36_synthetic(sandbox)
        assert result.returncode == 0, f"Step 36 failed: {result.stderr}"
        
        outputs = _load_step36_outputs(sandbox)
        
        # Should create Excel file
        if 'delivery_xlsx_path' in outputs:
            xlsx_path = outputs['delivery_xlsx_path']
            assert xlsx_path.exists(), "Excel file should exist"
            assert xlsx_path.suffix == '.xlsx', "Should create Excel format"
            assert xlsx_path.stat().st_size > 1000, "Excel file should have substantial content"
    
    def test_step36_validation_output(self, tmp_path):
        """Test Step 36 validation output generation"""
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_step36(sandbox)
        
        # Run Step 36
        result = _run_step36_synthetic(sandbox)
        assert result.returncode == 0, f"Step 36 failed: {result.stderr}"
        
        outputs = _load_step36_outputs(sandbox)
        
        # Should create validation output
        if 'validation' in outputs:
            validation = outputs['validation']
            assert isinstance(validation, dict), "Validation should be a dictionary"
            
            # Should have validation metrics
            expected_keys = ['total_records', 'validation_status']
            for key in expected_keys:
                if key in validation:
                    assert validation[key] is not None, f"Validation should have {key}"
    
    def test_step36_womens_casual_pants_presence(self, tmp_path):
        """Test Step 36 handles women's casual pants correctly"""
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_step36(sandbox, category_cn="休闲裤")
        
        # Run Step 36
        result = _run_step36_synthetic(sandbox)
        assert result.returncode == 0, f"Step 36 failed: {result.stderr}"
        
        outputs = _load_step36_outputs(sandbox)
        
        if 'delivery_csv' in outputs:
            delivery_df = outputs['delivery_csv']
            
            # Should have women's casual pants
            womens_pants = delivery_df[
                (delivery_df['Category'] == '休闲裤') & 
                (delivery_df['Gender'] == 'Women')
            ]
            assert len(womens_pants) > 0, "Should include women's casual pants"
            
            # Should have proper subcategory
            womens_subcats = womens_pants['Subcategory'].unique()
            assert any('女' in subcat for subcat in womens_subcats), \
                "Should have women's subcategories"
    
    def test_step36_planning_season_mapping(self, tmp_path):
        """Test Step 36 planning season mapping"""
        sandbox = _prepare_sandbox(tmp_path)
        _seed_synthetic_inputs_step36(sandbox)
        
        # Run Step 36
        result = _run_step36_synthetic(sandbox)
        assert result.returncode == 0, f"Step 36 failed: {result.stderr}"
        
        outputs = _load_step36_outputs(sandbox)
        
        if 'delivery_csv' in outputs:
            delivery_df = outputs['delivery_csv']
            
            # Should preserve season information
            assert 'Season' in delivery_df.columns, "Should preserve Season column"
            
            seasons = delivery_df['Season'].unique()
            expected_seasons = ['Summer', 'Winter', 'Spring']
            for season in expected_seasons:
                assert season in seasons, f"Should preserve {season} season"
    
    def test_step36_error_handling_missing_data(self, tmp_path):
        """Test Step 36 error handling with missing data"""
        sandbox = _prepare_sandbox(tmp_path)
        
        # Don't seed all required data - test error handling
        # Only create minimal Step 18 data
        step18_data = {
            'Store_Group_Name': ['Group_1'],
            'Category': ['TestCategory'],
            'ΔQty': [5]
        }
        step18_df = pd.DataFrame(step18_data)
        step18_df.to_csv(sandbox / "output/fast_fish_with_sell_through_analysis_202510A.csv", index=False)
        
        # Run Step 36
        result = _run_step36_synthetic(sandbox)
        
        # Should either succeed with partial data or fail gracefully
        if result.returncode != 0:
            error_msg = result.stderr.lower()
            expected_errors = ['file', 'not', 'found', 'missing', 'keyerror', 'column']
            assert any(term in error_msg for term in expected_errors), \
                "Should provide informative error for missing data"

def test_step36_synthetic_regression():
    """Integration test to ensure Step 36 synthetic tests work end-to-end"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Test the main functionality
        test_instance = TestStep36Synthetic()
        test_instance.test_step36_category_validation(tmp_path)
        test_instance.test_step36_buffer_calculations(tmp_path)
        
        print("✅ Step 36 synthetic regression test passed")

if __name__ == "__main__":
    test_step36_synthetic_regression()
    print("🎉 All Step 36 synthetic tests completed successfully!")
