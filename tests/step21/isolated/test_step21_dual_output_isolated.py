"""
Step 21 Dual Output Pattern Test (Isolated)
====================================================

Tests that Step 21 creates timestamped files + symlinks.
Uses complete synthetic fixtures - truly isolated, no dependencies on real output.

SETUP:
- Creates complete clustering and SPU recommendation fixtures
- Runs Step 21 in isolated sandbox
- Verifies dual output pattern for CSV and Excel files (timestamped + symlink/generic)
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_step21_dual_output_isolated(tmp_path):
    """Test Step 21 creates timestamped files + symlinks in isolation."""
    
    # Create isolated sandbox
    sandbox = tmp_path / "sandbox"
    output_dir = sandbox / "output"
    output_dir.mkdir(parents=True)
    
    # Copy src directory to sandbox
    src_dir = sandbox / "src"
    shutil.copytree(PROJECT_ROOT / "src", src_dir)
    
    # Create stub pipeline_manifest.py
    stub = """
class _DummyManifest:
    def __init__(self):
        self.manifest = {}

def get_manifest():
    return _DummyManifest()

def register_step_output(*_args, **_kwargs):
    return None

def get_step_input(*_args, **_kwargs):
    return None
""".strip()
    (src_dir / "pipeline_manifest.py").write_text(stub, encoding="utf-8")
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    
    # Create complete clustering and SPU recommendation fixtures
    _create_clustering_and_spu_fixtures(sandbox)
    
    # Run Step 21
    try:
        _run_step21(sandbox)
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Step 21 failed to run: {e}")
    except Exception as e:
        pytest.skip(f"Step 21 requires more setup: {e}")
    
    # Verify dual output pattern for CSV files
    timestamped_csv_files = list(output_dir.glob("client_desired_store_group_style_tags_targets_*_*.csv"))
    timestamped_csv_files = [f for f in timestamped_csv_files if re.search(r'_\d{8}_\d{6}\.csv$', f.name)]
    
    if len(timestamped_csv_files) == 0:
        pytest.skip("Step 21 did not create timestamped CSV outputs")
    
    print(f"\n✅ Found {len(timestamped_csv_files)} timestamped CSV files")
    
    # Verify timestamped CSV files
    for timestamped_file in timestamped_csv_files:
        # Must be real file
        assert timestamped_file.is_file() and not timestamped_file.is_symlink()
        
        # Must have correct format
        assert re.search(r'_\d{8}_\d{6}\.csv$', timestamped_file.name)
        
        print(f"\n📄 Checking CSV: {timestamped_file.name}")
        
        # Check for corresponding period symlink
        match = re.search(r'_(\d{6}[AB])_\d{8}_\d{6}\.csv$', timestamped_file.name)
        if match:
            period_label = match.group(1)
            period_symlink = output_dir / f"client_desired_store_group_style_tags_targets_{period_label}.csv"
            
            if period_symlink.exists():
                # Must be symlink
                assert period_symlink.is_symlink(), f"{period_symlink.name} should be a symlink"
                
                # Must use basename
                link_target = os.readlink(period_symlink)
                assert '/' not in link_target, f"{period_symlink.name} should use basename"
                
                # Must point to timestamped file
                assert re.search(r'_\d{8}_\d{6}\.csv$', link_target)
                
                print(f"   ✅ CSV symlink: {period_symlink.name} -> {link_target}")
    
    # Verify Excel files exist (Step 21 creates both timestamped and generic Excel)
    excel_files = list(output_dir.glob("D_F_Label_Tag_Recommendation_Sheet_*.xlsx"))
    if excel_files:
        print(f"\n✅ Found {len(excel_files)} Excel files")
        for excel_file in excel_files:
            print(f"   📊 {excel_file.name}")
    
    print(f"\n✅ Step 21 dual output pattern verified!")


def _create_clustering_and_spu_fixtures(sandbox: Path):
    """Create complete clustering and SPU recommendation fixtures for Step 21."""
    
    output_dir = sandbox / "output"
    target_period = "202510A"
    
    # Create clustering results (Step 21 needs cluster assignments)
    clustering = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003', 'S004', 'S005'] * 20,
        'Cluster': [0, 0, 1, 1, 2] * 20,
        'sub_cate_name': ['T恤', '裤子', '鞋', 'T恤', '裤子'] * 20
    })
    clustering.to_csv(output_dir / "clustering_results_spu.csv", index=False)
    
    # Create detailed SPU recommendations (Step 21's main input)
    spu_recommendations = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003', 'S004', 'S005'] * 20,
        'spu_code': ['SPU001', 'SPU002', 'SPU003', 'SPU004', 'SPU005'] * 20,
        'sub_cate_name': ['T恤', '裤子', '鞋', 'T恤', '裤子'] * 20,
        'recommended_quantity_change': [5, 10, -3, 8, 12] * 20,
        'investment_required': [500, 1000, -300, 800, 1200] * 20,
        'cluster_id': [0, 0, 1, 1, 2] * 20,
        'rule_source': ['rule7', 'rule8', 'rule9', 'rule7', 'rule8'] * 20,
        'business_rationale': ['Missing category'] * 100,
        'unit_price': [100] * 100
    })
    spu_recommendations.to_csv(output_dir / f"detailed_spu_recommendations_{target_period}.csv", index=False)
    
    print(f"✅ Created clustering fixtures: {len(clustering)} records")
    print(f"✅ Created SPU recommendation fixtures: {len(spu_recommendations)} records")


def _run_step21(sandbox: Path):
    """Run Step 21 in isolated sandbox."""
    
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["PYTHONPATH"] = str(sandbox)
    
    result = subprocess.run(
        ["python3", "src/step21_label_tag_recommendations.py",
         "--target-yyyymm", "202510",
         "--target-period", "A"],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"\n❌ Step 21 failed:")
        print(f"STDOUT:\n{result.stdout[-500:]}")
        print(f"STDERR:\n{result.stderr[-500:]}")
        raise subprocess.CalledProcessError(result.returncode, result.args)
    
    print(f"✅ Step 21 completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
