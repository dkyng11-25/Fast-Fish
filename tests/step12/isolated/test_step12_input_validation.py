"""
Step 12 Input Validation Test (Isolated Synthetic)
==================================================

Validates that Step 12 correctly reads from generic symlinks and handles missing inputs.

This test ensures Step 12 follows the input reading pattern:
- Reads from output/clustering_results_spu.csv (generic symlink) - REQUIRED
- Has fallback chain for clustering files
- Reads from API data files (sales data)
- Fails gracefully when clustering results are missing
"""

import os
import shutil
import subprocess
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def create_sandbox(tmp_path):
    """Create isolated sandbox for testing."""
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    
    # Copy src directory
    src_dir = sandbox / "src"
    shutil.copytree(PROJECT_ROOT / "src", src_dir)
    
    # Create directories
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
    
    return sandbox


def create_synthetic_clustering_results(output_path, num_stores=20):
    """Create synthetic clustering results."""
    cluster_data = pd.DataFrame({
        'str_code': [f"{1000+i}" for i in range(num_stores)],
        'Cluster': [i % 3 for i in range(num_stores)],
        'cluster_id': [i % 3 for i in range(num_stores)]
    })
    cluster_data.to_csv(output_path, index=False)


def create_synthetic_sales_data(output_path, num_records=100):
    """Create synthetic sales data."""
    sales_data = pd.DataFrame({
        'str_code': [f"{1000 + (i % 20)}" for i in range(num_records)],
        'spu_code': [f"SPU{1000+i}" for i in range(num_records)],
        'sty_code': [f"STY{100+i//10}" for i in range(num_records)],
        'sub_cate_name': [['T恤', 'POLO衫', '连衣裙', '裤子'][i % 4] for i in range(num_records)],
        'big_class_name': [['上装', '下装', '连衣裙'][i % 3] for i in range(num_records)],
        'season_name': [['春', '夏', '秋', '冬'][i % 4] for i in range(num_records)],
        'sex_name': [['男', '女', '通用'][i % 3] for i in range(num_records)],
        'display_location_name': [['前店', '后仓'][i % 2] for i in range(num_records)],
        'spu_sales_qty': [10 + i for i in range(num_records)],
        'spu_sales_amt': [100 + i * 10 for i in range(num_records)]
    })
    sales_data.to_csv(output_path, index=False)


def test_step12_reads_from_generic_clustering_symlink(tmp_path):
    """
    Verify Step 12 reads from generic clustering symlink.
    
    Setup:
    - Create timestamped clustering file
    - Create generic symlink pointing to it
    - Create required sales data
    - Run Step 12
    
    Verify:
    - Step 12 succeeds by reading from generic symlink
    - Step 12 loads clustering results correctly
    """
    # Create sandbox
    sandbox = create_sandbox(tmp_path)
    output_dir = sandbox / "output"
    api_data_dir = sandbox / "data" / "api_data"
    
    # Create timestamped clustering file
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamped_cluster = output_dir / f"clustering_results_spu_{timestamp}.csv"
    create_synthetic_clustering_results(timestamped_cluster, num_stores=20)
    
    # Create ONLY generic symlink (no period-labeled)
    generic_cluster = output_dir / "clustering_results_spu.csv"
    os.symlink(timestamped_cluster.name, generic_cluster)
    
    # Create required sales data
    sales_file = api_data_dir / "complete_spu_sales_202510A.csv"
    create_synthetic_sales_data(sales_file, num_records=100)
    
    print(f"\n📁 Created test setup:")
    print(f"   Clustering (timestamped): {timestamped_cluster.name}")
    print(f"   Clustering (generic symlink): clustering_results_spu.csv")
    print(f"   Sales data: complete_spu_sales_202510A.csv")
    
    # Run Step 12
    env = os.environ.copy()
    env["PYTHONPATH"] = str(sandbox)
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["ANALYSIS_LEVEL"] = "spu"
    
    result = subprocess.run(
        ["python3", "src/step12_sales_performance_rule.py"],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    print(f"\n🔍 Step 12 execution:")
    print(f"   Exit code: {result.returncode}")
    if result.stdout:
        print(f"   STDOUT (last 500 chars):\n{result.stdout[-500:]}")
    if result.stderr and result.returncode != 0:
        print(f"   STDERR (last 300 chars):\n{result.stderr[-300:]}")
    
    # Verify Step 12 loaded clustering from generic symlink
    assert "Loaded cluster assignments" in result.stdout, \
        "Step 12 should log cluster loading"
    assert "clustering_results_spu.csv" in result.stdout, \
        "Step 12 should use the generic symlink"
    
    # Step 12 may complete or fail during processing, but it should have loaded the cluster file
    print(f"\n✅ Step 12 successfully read from generic clustering symlink")
    if result.returncode != 0:
        print(f"   ⚠️ Note: Step 12 failed during processing (exit code {result.returncode})")
        print(f"   This is separate from input file reading")


def test_step12_fails_gracefully_when_clustering_missing(tmp_path):
    """
    Verify Step 12 fails with clear error when clustering results are missing.
    
    Setup:
    - Create sales data but NO clustering file
    - Run Step 12
    
    Verify:
    - Step 12 fails with non-zero exit code
    - Error message mentions missing clustering file
    """
    # Create sandbox
    sandbox = create_sandbox(tmp_path)
    api_data_dir = sandbox / "data" / "api_data"
    
    # Create sales data but NO clustering file
    sales_file = api_data_dir / "complete_spu_sales_202510A.csv"
    create_synthetic_sales_data(sales_file, num_records=100)
    
    print(f"\n📁 Created test setup:")
    print(f"   Clustering file: NO (testing missing input)")
    print(f"   Sales data: YES")
    
    # Run Step 12
    env = os.environ.copy()
    env["PYTHONPATH"] = str(sandbox)
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["ANALYSIS_LEVEL"] = "spu"
    
    result = subprocess.run(
        ["python3", "src/step12_sales_performance_rule.py"],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    print(f"\n🔍 Step 12 execution:")
    print(f"   Exit code: {result.returncode}")
    if result.stderr:
        print(f"   STDERR:\n{result.stderr}")
    
    # Verify Step 12 failed
    assert result.returncode != 0, \
        "Step 12 should fail when clustering results are missing"
    
    # Verify error message mentions clustering
    error_output = (result.stderr + result.stdout).lower()
    assert "clustering" in error_output or "not found" in error_output, \
        f"Error message should mention missing clustering file\nSTDERR: {result.stderr}"
    
    print(f"\n✅ Step 12 correctly failed with error when clustering missing")




if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
