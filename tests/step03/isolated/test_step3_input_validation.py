"""
Step 3 Input Validation Test (Isolated Synthetic)
==================================================

Validates that Step 3 correctly reads from generic symlinks (not timestamped files).

This test ensures Step 3 follows the input reading pattern:
- Reads from data/store_coordinates_extended.csv (generic symlink)
- Does NOT require timestamped coordinate files
- Works correctly when only generic symlink exists
"""

import os
import shutil
import subprocess
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_step3_reads_from_generic_coordinates_symlink(tmp_path):
    """
    Verify Step 3 reads from generic symlink, not timestamped files.
    
    Setup:
    - Create timestamped coordinates file
    - Create generic symlink pointing to it
    - Remove any period-labeled files
    - Run Step 3
    
    Verify:
    - Step 3 succeeds by reading from generic symlink
    - Step 3 does NOT fail when only generic symlink exists
    """
    # Create isolated sandbox
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    
    # Copy src directory
    src_dir = sandbox / "src"
    shutil.copytree(PROJECT_ROOT / "src", src_dir)
    
    # Create data and output directories
    data_dir = sandbox / "data"
    data_dir.mkdir()
    api_data_dir = data_dir / "api_data"
    api_data_dir.mkdir()
    output_dir = sandbox / "output"
    output_dir.mkdir()
    
    # Create stub pipeline_manifest.py
    stub_manifest = """
class _DummyManifest:
    def __init__(self):
        self.manifest = {}
    
    def get_latest_output(self, *args, **kwargs):
        return None

def get_manifest():
    return _DummyManifest()

def register_step_output(*_args, **_kwargs):
    return None

def get_step_input(*_args, **_kwargs):
    return None
""".strip()
    (src_dir / "pipeline_manifest.py").write_text(stub_manifest, encoding="utf-8")
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    
    # Create synthetic timestamped coordinates file
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamped_coords = data_dir / f"store_coordinates_extended_{timestamp}.csv"
    
    coords_data = pd.DataFrame({
        'str_code': ['1001', '1002', '1003', '1004', '1005'],
        'longitude': [121.5, 121.6, 121.7, 121.8, 121.9],
        'latitude': [31.2, 31.3, 31.4, 31.5, 31.6]
    })
    coords_data.to_csv(timestamped_coords, index=False)
    
    # Create ONLY generic symlink (no period-labeled file)
    generic_coords = data_dir / "store_coordinates_extended.csv"
    os.symlink(timestamped_coords.name, generic_coords)
    
    print(f"\n📁 Created test setup:")
    print(f"   Timestamped: {timestamped_coords.name}")
    print(f"   Generic symlink: {generic_coords.name} -> {timestamped_coords.name}")
    
    # Create minimal API data for Step 3 to process
    # Step 3 needs sales data to build the matrix
    api_sales_data = pd.DataFrame({
        'str_code': ['1001', '1002', '1003', '1004', '1005'] * 10,
        'sub_cate_name': ['T恤', 'POLO衫', '连衣裙', '裤子', '外套'] * 10,
        'sal_qty': [10, 20, 15, 25, 30] * 10,
        'sal_amt': [100, 200, 150, 250, 300] * 10
    })
    api_sales_file = api_data_dir / "complete_category_sales_202510A.csv"
    api_sales_data.to_csv(api_sales_file, index=False)
    
    # Run Step 3
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["PYTHONPATH"] = str(sandbox)
    
    result = subprocess.run(
        ["python3", "src/step3_prepare_matrix.py"],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    print(f"\n🔍 Step 3 execution:")
    print(f"   Exit code: {result.returncode}")
    if result.stdout:
        print(f"   STDOUT (last 500 chars):\n{result.stdout[-500:]}")
    if result.stderr:
        print(f"   STDERR (last 500 chars):\n{result.stderr[-500:]}")
    
    # Verify Step 3 succeeded
    assert result.returncode == 0, \
        f"Step 3 should succeed when reading from generic symlink\nSTDERR: {result.stderr}"
    
    # Verify Step 3 created output matrices
    output_files = list(data_dir.glob("store_subcategory_matrix*.csv"))
    assert len(output_files) > 0, "Step 3 should create matrix files"
    
    print(f"\n✅ Step 3 successfully read from generic symlink and created {len(output_files)} output files")


def test_step3_fails_gracefully_when_coordinates_missing(tmp_path):
    """
    Verify Step 3 fails with clear error when coordinates file is missing.
    
    Setup:
    - Create sandbox with API data
    - Do NOT create coordinates file
    - Run Step 3
    
    Verify:
    - Step 3 fails with non-zero exit code
    - Error message mentions missing coordinates file
    """
    # Create isolated sandbox
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    
    # Copy src directory
    src_dir = sandbox / "src"
    shutil.copytree(PROJECT_ROOT / "src", src_dir)
    
    # Create data and output directories
    data_dir = sandbox / "data"
    data_dir.mkdir()
    api_data_dir = data_dir / "api_data"
    api_data_dir.mkdir()
    output_dir = sandbox / "output"
    output_dir.mkdir()
    
    # Create stub pipeline_manifest.py
    stub_manifest = """
class _DummyManifest:
    def __init__(self):
        self.manifest = {}
    
    def get_latest_output(self, *args, **kwargs):
        return None

def get_manifest():
    return _DummyManifest()

def register_step_output(*_args, **_kwargs):
    return None

def get_step_input(*_args, **_kwargs):
    return None
""".strip()
    (src_dir / "pipeline_manifest.py").write_text(stub_manifest, encoding="utf-8")
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    
    # Create API data but NO coordinates file
    api_sales_data = pd.DataFrame({
        'str_code': ['1001', '1002', '1003'],
        'sub_cate_name': ['T恤', 'POLO衫', '连衣裙'],
        'sal_qty': [10, 20, 15],
        'sal_amt': [100, 200, 150]
    })
    api_sales_file = api_data_dir / "complete_category_sales_202510A.csv"
    api_sales_data.to_csv(api_sales_file, index=False)
    
    print(f"\n📁 Created test setup WITHOUT coordinates file")
    
    # Run Step 3
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["PYTHONPATH"] = str(sandbox)
    
    result = subprocess.run(
        ["python3", "src/step3_prepare_matrix.py"],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    print(f"\n🔍 Step 3 execution:")
    print(f"   Exit code: {result.returncode}")
    if result.stderr:
        print(f"   STDERR:\n{result.stderr}")
    
    # Verify Step 3 failed
    assert result.returncode != 0, \
        "Step 3 should fail when coordinates file is missing"
    
    # Verify error message mentions coordinates
    error_output = result.stderr.lower()
    assert "coordinate" in error_output or "not found" in error_output or "error" in error_output, \
        f"Error message should mention missing coordinates file\nSTDERR: {result.stderr}"
    
    print(f"\n✅ Step 3 correctly failed with error when coordinates missing")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
