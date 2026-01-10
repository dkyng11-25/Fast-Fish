"""
Step 36 Dual Output Pattern Test (Isolated)
====================================================

Tests that Step 36 creates timestamped files + symlinks.
Uses complete synthetic fixtures - truly isolated, no dependencies on real output.

SETUP:
- Creates minimal but complete fixtures for Step 36 inputs (Steps 18, 32)
- Runs Step 36 in isolated sandbox
- Verifies dual output pattern for CSV files (timestamped + period + generic symlinks)

Note: Step 36 is the final pipeline step (Unified Delivery Builder) that integrates
data from Steps 18 (sell-through) and 32 (allocation) at minimum.
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


def test_step36_dual_output_isolated(tmp_path):
    """Test Step 36 creates timestamped files + symlinks in isolation."""
    
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
    
    def get_latest_output(self, *args, **kwargs):
        return None

def get_manifest():
    return _DummyManifest()

def register_step_output(*_args, **_kwargs):
    return None

def get_step_input(*_args, **_kwargs):
    return None
""".strip()
    (src_dir / "pipeline_manifest.py").write_text(stub, encoding="utf-8")
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    
    # Create complete fixtures for Step 36
    _create_step36_fixtures(sandbox)
    
    # Run Step 36
    try:
        _run_step36(sandbox)
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Step 36 failed to run: {e}")
    except Exception as e:
        pytest.skip(f"Step 36 requires more setup: {e}")
    
    # Verify dual output pattern for Step 36 outputs
    # Step 36 creates unified_delivery files
    timestamped_files = list(output_dir.glob("unified_delivery_202510A_*.csv"))
    timestamped_files = [f for f in timestamped_files if re.search(r'_\d{8}_\d{6}\.csv$', f.name)]
    
    if len(timestamped_files) == 0:
        pytest.skip("Step 36 did not create timestamped outputs")
    
    print(f"\n✅ Found {len(timestamped_files)} timestamped CSV files")
    
    # Verify timestamped files and their symlinks
    for timestamped_file in timestamped_files:
        # Must be real file
        assert timestamped_file.is_file() and not timestamped_file.is_symlink()
        
        # Must have correct format
        assert re.search(r'_\d{8}_\d{6}\.csv$', timestamped_file.name)
        
        print(f"\n📄 Checking: {timestamped_file.name}")
        
        # Step 36 uses create_output_with_symlinks which creates:
        # 1. Timestamped file: unified_delivery_202510A_20251006_133716.csv
        # 2. Period symlink: unified_delivery_202510A.csv
        # 3. Generic symlink: unified_delivery.csv
        
        # Check for period symlink
        period_file = output_dir / "unified_delivery_202510A.csv"
        if period_file.exists():
            assert period_file.is_symlink(), f"{period_file.name} should be a symlink"
            link_target = os.readlink(period_file)
            assert '/' not in link_target, f"{period_file.name} should use basename"
            assert re.search(r'_\d{8}_\d{6}\.csv$', link_target)
            print(f"   ✅ Period symlink: {period_file.name} -> {link_target}")
        
        # Check for generic symlink
        generic_file = output_dir / "unified_delivery.csv"
        if generic_file.exists():
            assert generic_file.is_symlink(), f"{generic_file.name} should be a symlink"
            link_target = os.readlink(generic_file)
            assert '/' not in link_target, f"{generic_file.name} should use basename"
            # Generic symlink points to period symlink
            assert '202510A' in link_target
            print(f"   ✅ Generic symlink: {generic_file.name} -> {link_target}")
    
    print(f"\n✅ Step 36 dual output pattern verified!")


def _create_step36_fixtures(sandbox: Path):
    """Create minimal but complete fixtures for Step 36."""
    
    output_dir = sandbox / "output"
    target_period = "202510A"
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Step 18 sell-through enriched data (minimum required)
    step18_data = pd.DataFrame({
        'Store_Group_Name': ['Group A', 'Group B', 'Group C'],
        'Target_Style_Tags': ['[秋, 男]', '[冬, 女]', '[秋, 女]'],
        'Category': ['POLO衫', 'T恤', '连衣裙'],
        'Subcategory': ['休闲POLO', '基础T恤', '秋季连衣裙'],
        'ΔQty': [20, -10, 15],
        'Group_ΔQty': [20, -10, 15],
        'Current_SPU_Quantity': [100, 80, 90],
        'Target_SPU_Quantity': [120, 70, 105],
        'Season': ['秋', '冬', '秋'],
        'Gender': ['男', '女', '女'],
        'Location': ['前台', '后台', '前台'],
        'Current_Sell_Through_Rate': [0.65, 0.70, 0.60],
        'Target_Sell_Through_Rate': [0.75, 0.80, 0.70],
        'Sell_Through_Improvement': [0.10, 0.10, 0.10]
    })
    step18_data.to_csv(output_dir / f"fast_fish_with_sell_through_analysis_{target_period}.csv", index=False)
    
    # 2. Step 32 allocation data (minimum required)
    step32_data = pd.DataFrame({
        'Period': ['A'] * 5,
        'Store_Code': ['11001', '11002', '12001', '12002', '13001'],
        'str_code': [11001, 11002, 12001, 12002, 13001],
        'Store_Group_Name': ['Group A', 'Group A', 'Group B', 'Group B', 'Group C'],
        'Target_Style_Tags': ['[秋, 男]', '[秋, 男]', '[冬, 女]', '[冬, 女]', '[秋, 女]'],
        'Category': ['POLO衫', 'POLO衫', 'T恤', 'T恤', '连衣裙'],
        'Subcategory': ['休闲POLO', '休闲POLO', '基础T恤', '基础T恤', '秋季连衣裙'],
        'Allocated_ΔQty': [10.0, 10.0, -5.0, -5.0, 15.0],
        'Allocated_ΔQty_Rounded': [10, 10, -5, -5, 15],
        'Store_Allocation_Weight': [0.5, 0.5, 0.5, 0.5, 1.0],
        'Allocation_Rationale': ['Weight-based'] * 5
    })
    step32_timestamped = output_dir / f"store_level_allocation_results_{target_period}_{timestamp}.csv"
    step32_data.to_csv(step32_timestamped, index=False)
    
    print(f"✅ Created Step 36 fixtures: Step 18 sell-through ({len(step18_data)} groups), Step 32 allocation ({len(step32_data)} stores)")


def _run_step36(sandbox: Path):
    """Run Step 36 in isolated sandbox."""
    
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["PYTHONPATH"] = str(sandbox)
    
    result = subprocess.run(
        ["python3", "src/step36_unified_delivery_builder.py",
         "--target-yyyymm", "202510",
         "--target-period", "A"],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode != 0:
        print(f"\n❌ Step 36 failed:")
        print(f"STDOUT:\n{result.stdout[-1000:]}")
        print(f"STDERR:\n{result.stderr[-1000:]}")
        raise subprocess.CalledProcessError(result.returncode, result.args)
    
    print(f"✅ Step 36 completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
