"""
Step 7 Execution Test with Synthetic Data
==========================================

Actually runs Step 7 with minimal synthetic data and verifies timestamped outputs.
"""

import os
import shutil
import subprocess
from pathlib import Path
import pandas as pd
import pytest
import re
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "src"


def create_synthetic_data(sandbox: Path):
    """Create minimal synthetic data for Step 7"""
    data_dir = sandbox / "data" / "api_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create minimal SPU sales data with all required columns
    spu_sales = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003'] * 10,
        'spu_code': [f'SPU{i:03d}' for i in range(30)],
        'sub_cate_name': ['T恤', '裤子', '外套'] * 10,
        'sales_qty': [10, 20, 15] * 10,
        'sales_amt': [100, 200, 150] * 10,
        'spu_sales_qty': [10, 20, 15] * 10,
        'spu_sales_amt': [100, 200, 150] * 10,
    })
    spu_sales.to_csv(data_dir / "complete_spu_sales_202510A.csv", index=False)
    
    # Create store sales (required by Step 7)
    store_sales = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003'] * 10,
        'spu_code': [f'SPU{i:03d}' for i in range(30)],
        'sub_cate_name': ['T恤', '裤子', '外套'] * 10,
        'sales_qty': [10, 20, 15] * 10,
        'sales_amt': [100, 200, 150] * 10,
        'unit_price': [10.0, 10.0, 10.0] * 10,
    })
    store_sales.to_csv(data_dir / "store_sales_202510A.csv", index=False)
    
    # Create minimal store config
    store_config = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003'],
        'str_name': ['Store 1', 'Store 2', 'Store 3'],
        'cluster_id': [1, 1, 2],
    })
    store_config.to_csv(data_dir / "store_config_202510A.csv", index=False)
    
    # Create clustering results
    clustering = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003'],
        'Cluster': [1, 1, 2],
    })
    (sandbox / "output").mkdir(exist_ok=True)
    clustering.to_csv(sandbox / "output" / "clustering_results_spu.csv", index=False)


def test_step7_creates_timestamped_outputs(tmp_path):
    """Test that Step 7 creates timestamped outputs with symlinks"""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    
    # Copy src to sandbox
    src_target = sandbox / "src"
    shutil.copytree(SRC_ROOT, src_target)
    
    # Create synthetic data
    create_synthetic_data(sandbox)
    
    # Create stub manifest
    stub_manifest = """
class _DummyManifest:
    def __init__(self):
        self.manifest = {}

def get_manifest():
    return _DummyManifest()

def register_step_output(*args, **kwargs):
    return None

def get_step_input(*args, **kwargs):
    return None
"""
    (src_target / "pipeline_manifest.py").write_text(stub_manifest)
    
    # Run Step 7
    env = os.environ.copy()
    env['PYTHONPATH'] = str(sandbox)
    env['PIPELINE_TARGET_YYYYMM'] = '202510'
    env['PIPELINE_TARGET_PERIOD'] = 'A'
    
    result = subprocess.run(
        ['python3', str(src_target / 'step7_missing_category_rule.py'),
         '--target-yyyymm', '202510',
         '--target-period', 'A'],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    print("STDOUT:", result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    if result.returncode != 0:
        print("STDERR:", result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
    
    assert result.returncode == 0, f"Step 7 failed with return code {result.returncode}"
    
    # Check for timestamped output
    output_dir = sandbox / "output"
    timestamp_pattern = re.compile(r'rule7_missing_spu_sellthrough_results_202510A_\d{8}_\d{6}\.csv')
    
    timestamped_files = [f for f in output_dir.glob("rule7_*.csv") 
                         if timestamp_pattern.match(f.name)]
    
    assert len(timestamped_files) > 0, "No timestamped output file found"
    
    timestamped_file = timestamped_files[0]
    print(f"✅ Found timestamped file: {timestamped_file.name}")
    
    # Check for period symlink
    period_symlink = output_dir / "rule7_missing_spu_sellthrough_results_202510A.csv"
    assert period_symlink.exists(), "Period-labeled symlink not found"
    assert period_symlink.is_symlink(), "Period-labeled file should be a symlink"
    
    # Check for generic symlink
    generic_symlink = output_dir / "rule7_missing_spu_sellthrough_results.csv"
    assert generic_symlink.exists(), "Generic symlink not found"
    assert generic_symlink.is_symlink(), "Generic file should be a symlink"
    
    # Verify symlinks point to timestamped file
    period_target = os.readlink(period_symlink)
    assert timestamped_file.name in period_target, \
        f"Period symlink should point to timestamped file, got: {period_target}"
    
    generic_target = os.readlink(generic_symlink)
    assert timestamped_file.name in generic_target, \
        f"Generic symlink should point to timestamped file, got: {generic_target}"
    
    # Verify file has content
    df = pd.read_csv(timestamped_file)
    assert len(df) > 0, "Output file should have data"
    
    print(f"✅ Step 7 test passed!")
    print(f"   Timestamped: {timestamped_file.name}")
    print(f"   Period symlink: {period_symlink.name} -> {period_target}")
    print(f"   Generic symlink: {generic_symlink.name} -> {generic_target}")
    print(f"   Output rows: {len(df)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
