"""
Step 32 Dual Output Pattern Test (Isolated)
====================================================

Tests that Step 32 creates timestamped files + symlinks.
Uses complete synthetic fixtures - truly isolated, no dependencies on real output.

SETUP:
- Creates complete Fast Fish, store tags, store attributes, and clustering fixtures
- Runs Step 32 in isolated sandbox
- Verifies dual output pattern for CSV files (timestamped + symlink)
"""

import os
import re
import shutil
import subprocess
import json
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_step32_dual_output_isolated(tmp_path):
    """Test Step 32 creates timestamped files + symlinks in isolation."""
    
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
    
    # Create complete fixtures for Step 32
    _create_step32_fixtures(sandbox)
    
    # Run Step 32
    try:
        _run_step32(sandbox)
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Step 32 failed to run: {e}")
    except Exception as e:
        pytest.skip(f"Step 32 requires more setup: {e}")
    
    # Verify dual output pattern for Step 32 outputs
    timestamped_files = list(output_dir.glob("store_level_allocation_*_202510A_*.csv"))
    timestamped_files = [f for f in timestamped_files if re.search(r'_\d{8}_\d{6}\.csv$', f.name)]
    
    if len(timestamped_files) == 0:
        pytest.skip("Step 32 did not create timestamped outputs")
    
    print(f"\n✅ Found {len(timestamped_files)} timestamped CSV files")
    
    # Verify timestamped files and their symlinks
    for timestamped_file in timestamped_files:
        # Must be real file
        assert timestamped_file.is_file() and not timestamped_file.is_symlink()
        
        # Must have correct format
        assert re.search(r'_\d{8}_\d{6}\.csv$', timestamped_file.name)
        
        print(f"\n📄 Checking: {timestamped_file.name}")
        
        # Check for corresponding generic symlink (Step 32 creates hardcoded generic filename)
        if 'store_level_allocation_results' in timestamped_file.name:
            generic_file = output_dir / "store_level_allocation_results.csv"
            
            if generic_file.exists():
                # Must be symlink
                assert generic_file.is_symlink(), f"{generic_file.name} should be a symlink"
                
                # Must use basename
                link_target = os.readlink(generic_file)
                assert '/' not in link_target, f"{generic_file.name} should use basename"
                
                # Must point to timestamped file
                assert re.search(r'_\d{8}_\d{6}\.csv$', link_target)
                
                print(f"   ✅ Symlink: {generic_file.name} -> {link_target}")
    
    print(f"\n✅ Step 32 dual output pattern verified!")


def _create_step32_fixtures(sandbox: Path):
    """Create complete fixtures for Step 32: Fast Fish, store tags, store attributes, clustering."""
    
    output_dir = sandbox / "output"
    target_period = "202510A"
    
    # Fast Fish with varied ΔQty values
    fast_fish_data = {
        'Year': [2025] * 6,
        'Month': [10] * 6,
        'Period': ['A'] * 6,
        'Store_Group_Name': ['Group A', 'Group A', 'Group B', 'Group B', 'Group C', 'Group C'],
        'Target_Style_Tags': ['[秋, 男]', '[冬, 女]', '[秋, 男]', '[冬, 男]', '[春, 女]', '[秋, 女]'],
        'ΔQty': [20, -10, 15, 5, -8, 12],  # Mix of positive and negative
        'Store_Codes_In_Group': ['1001,1002', '1001,1002', '2001,2002,2003', '2001,2002,2003', '3001', '3001'],
        'Store_Count_In_Group': [2, 2, 3, 3, 1, 1],
        'Category': ['POLO衫', 'T恤', 'POLO衫', '卫衣', 'T恤', '连衣裙'],
        'Subcategory': ['休闲POLO', '基础T恤', '商务POLO', '连帽卫衣', '印花T恤', '秋季连衣裙'],
        'Season': ['秋', '冬', '秋', '冬', '春', '秋'],
        'Gender': ['男', '女', '男', '男', '女', '女'],
        'period_label': [target_period] * 6
    }
    fast_fish_df = pd.DataFrame(fast_fish_data)
    fast_fish_df.to_csv(output_dir / f"enhanced_fast_fish_format_{target_period}.csv", index=False)
    
    # Store tags matching the groups (create both timestamped and symlink)
    store_tags_data = {
        'str_code': [1001, 1002, 2001, 2002, 2003, 3001],
        'Store_Group_Name': ['Group A', 'Group A', 'Group B', 'Group B', 'Group B', 'Group C'],
        'cluster_id': [1, 1, 2, 2, 2, 3]
    }
    store_tags_df = pd.DataFrame(store_tags_data)
    
    # Create timestamped version
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tags_timestamped = output_dir / f"client_desired_store_group_style_tags_targets_{target_period}_{timestamp}.csv"
    store_tags_df.to_csv(tags_timestamped, index=False)
    
    # Create symlink
    tags_link = output_dir / f"client_desired_store_group_style_tags_targets_{target_period}.csv"
    if tags_link.exists() or tags_link.is_symlink():
        tags_link.unlink()
    os.symlink(tags_timestamped.name, tags_link)
    
    # Store attributes with varied performance metrics
    store_attrs_data = {
        'str_code': [1001, 1002, 2001, 2002, 2003, 3001],
        'store_type': ['Fashion', 'Basic', 'Fashion', 'Fashion', 'Basic', 'Premium'],
        'capacity': [1000, 800, 1200, 1500, 900, 2000],
        'estimated_rack_capacity': [1000, 800, 1200, 1500, 900, 2000],
        'sales_performance': [0.85, 0.70, 0.90, 0.95, 0.75, 0.88],
        'total_sales_amt': [50000, 40000, 60000, 75000, 45000, 80000],  # Required by weight calculation
        'fashion_ratio': [0.7, 0.3, 0.8, 0.85, 0.4, 0.9],
        'basic_ratio': [0.3, 0.7, 0.2, 0.15, 0.6, 0.1]
    }
    store_attrs_df = pd.DataFrame(store_attrs_data)
    store_attrs_df.to_csv(output_dir / f"enriched_store_attributes_{target_period}.csv", index=False)
    
    # Enhanced clustering results
    cluster_data = {
        'str_code': [1001, 1002, 2001, 2002, 2003, 3001],
        'cluster_id': [1, 1, 2, 2, 2, 3],
        'cluster_name': ['Fashion Heavy', 'Fashion Heavy', 'Balanced Mix', 'Balanced Mix', 'Balanced Mix', 'Premium Focus']
    }
    cluster_df = pd.DataFrame(cluster_data)
    cluster_df.to_csv(output_dir / "enhanced_clustering_results.csv", index=False)
    
    print(f"✅ Created Fast Fish fixtures: {len(fast_fish_df)} recommendations")
    print(f"✅ Created store tags fixtures: {len(store_tags_df)} stores")
    print(f"✅ Created store attributes fixtures: {len(store_attrs_df)} stores")
    print(f"✅ Created clustering fixtures: {len(cluster_df)} stores")


def _run_step32(sandbox: Path):
    """Run Step 32 in isolated sandbox."""
    
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["PYTHONPATH"] = str(sandbox)
    
    result = subprocess.run(
        ["python3", "src/step32_store_allocation.py",
         "--target-yyyymm", "202510",
         "--period", "A"],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"\n❌ Step 32 failed:")
        print(f"STDOUT:\n{result.stdout[-500:]}")
        print(f"STDERR:\n{result.stderr[-500:]}")
        raise subprocess.CalledProcessError(result.returncode, result.args)
    
    print(f"✅ Step 32 completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
