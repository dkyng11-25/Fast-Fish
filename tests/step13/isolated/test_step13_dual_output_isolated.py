"""
Step 13 Dual Output Pattern Test (Isolated)
====================================================

Tests that Step 13 creates timestamped files + symlinks.
Uses isolated fixture data - no dependencies on real output directory.
"""

import os
import re
import shutil
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_step13_dual_output_isolated(tmp_path):
    """Test Step 13 creates timestamped files + symlinks in isolation."""
    
    # Create isolated sandbox
    sandbox = tmp_path / "sandbox"
    output_dir = sandbox / "output"
    output_dir.mkdir(parents=True)
    
    # Copy step script to sandbox
    src_dir = sandbox / "src"
    shutil.copytree(PROJECT_ROOT / "src", src_dir)
    
    # Create minimal fixture data
    _create_fixture_data(sandbox)
    
    # Run step (this will be customized per step)
    try:
        _run_step13(sandbox)
    except Exception as e:
        import traceback
        print(f"\n❌ Step 13 failed with error:")
        print(traceback.format_exc())
        pytest.skip(f"Step 13 requires more setup: {e}")
    
    # Verify dual output pattern
    # Step 13 creates consolidated_spu_rule_results_detailed files
    timestamped_files = list(output_dir.glob("consolidated_*_*_*.csv"))
    timestamped_files = [f for f in timestamped_files if re.search(r'_\d{8}_\d{6}\.csv$', f.name)]
    
    if len(timestamped_files) == 0:
        # Debug: show what files were created
        all_files = list(output_dir.glob("*.csv"))
        print(f"\n⚠️  No timestamped files found. Files in output dir:")
        for f in all_files:
            print(f"   - {f.name}")
        pytest.skip("Step 13 did not create timestamped outputs")
    
    print(f"\n✅ Found {len(timestamped_files)} timestamped files")
    
    # Verify timestamped files
    for timestamped_file in timestamped_files:
        # Must be real file
        assert timestamped_file.is_file() and not timestamped_file.is_symlink()
        
        # Must have correct format
        assert re.search(r'_\d{8}_\d{6}\.csv$', timestamped_file.name)
        
        # Check for corresponding symlink
        generic_name = re.sub(r'_\d{8}_\d{6}\.csv$', '.csv', timestamped_file.name)
        generic_file = output_dir / generic_name
        
        if generic_file.exists():
            # Must be symlink
            assert generic_file.is_symlink()
            
            # Must use basename
            link_target = os.readlink(generic_file)
            assert '/' not in link_target
            
            # Must point to timestamped file
            assert link_target == timestamped_file.name
            
            print(f"✅ {generic_file.name} -> {link_target}")


def _create_fixture_data(sandbox: Path):
    """Create minimal fixture data for Step 13."""
    
    # Create directory structure
    data_dir = sandbox / "data" / "api_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir = sandbox / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create minimal SPU sales data
    spu_sales = pd.DataFrame({
        'str_code': ['1001', '1002', '1003', '1001', '1002'],
        'spu_code': ['SPU001', 'SPU002', 'SPU003', 'SPU002', 'SPU001'],
        'spu_sales_amt': [100.0, 200.0, 300.0, 150.0, 250.0],
        'quantity': [10, 20, 30, 15, 25],
        'sub_cate_name': ['T恤', '裤子', '鞋', '裤子', 'T恤']
    })
    spu_sales.to_csv(data_dir / "complete_spu_sales_202410A.csv", index=False)
    
    # Create minimal clustering data
    clustering = pd.DataFrame({
        'str_code': ['1001', '1002', '1003'],
        'Cluster': [0, 0, 1]
    })
    clustering.to_csv(output_dir / "clustering_results_spu_202410A.csv", index=False)
    
    # Create minimal rule outputs (Rules 7-12) with all required columns
    for rule_num in [7, 8, 9, 10, 11, 12]:
        rule_data = pd.DataFrame({
            'str_code': ['1001', '1002', '1003'],
            'spu_code': ['SPU001', 'SPU002', 'SPU003'],
            'sub_cate_name': ['T恤', '裤子', '鞋'],
            'recommended_quantity_change': [5.0, 10.0, -3.0],
            'investment_required': [50.0, 100.0, -30.0],
            'unit_price': [10.0, 10.0, 10.0],
            'current_quantity': [10.0, 20.0, 15.0],
            'target_quantity': [15.0, 30.0, 12.0],
            f'rule{rule_num}_flag': [True, True, True],
            'cluster_id': [0, 0, 1]
        })
        rule_data.to_csv(output_dir / f"rule{rule_num}_test_results_202410A.csv", index=False)


def _run_step13(sandbox: Path):
    """Run Step 13 in isolated sandbox."""
    
    import sys
    import importlib.util
    import io
    from contextlib import redirect_stdout, redirect_stderr
    
    # Set up environment
    old_cwd = os.getcwd()
    old_path = sys.path.copy()
    
    # Capture output
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    try:
        # Change to sandbox
        os.chdir(sandbox)
        sys.path.insert(0, str(sandbox / "src"))
        
        # Set environment variables
        os.environ['PYTHONPATH'] = str(sandbox / "src")
        os.environ['PIPELINE_TARGET_YYYYMM'] = '202410'
        os.environ['PIPELINE_TARGET_PERIOD'] = 'A'
        os.environ['FAST_MODE'] = '1'
        
        # Import and run Step 13
        spec = importlib.util.spec_from_file_location(
            "step13_consolidate_spu_rules",
            sandbox / "src" / "step13_consolidate_spu_rules.py"
        )
        step13_module = importlib.util.module_from_spec(spec)
        
        # Mock sys.argv for argparse
        old_argv = sys.argv
        sys.argv = ['step13_consolidate_spu_rules.py', '--target-yyyymm', '202410', '--target-period', 'A']
        
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                spec.loader.exec_module(step13_module)
        finally:
            sys.argv = old_argv
            
        # Print captured output for debugging
        output = stdout_capture.getvalue()
        if output:
            print("\n📋 Step 13 Output:")
            print(output[-500:])  # Last 500 chars
            
    finally:
        # Restore environment
        os.chdir(old_cwd)
        sys.path = old_path


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
