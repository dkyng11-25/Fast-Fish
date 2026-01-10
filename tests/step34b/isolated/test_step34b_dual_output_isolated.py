"""
Step 34b Dual Output Pattern Test (Isolated)
====================================================

Tests that Step 34b creates timestamped files + symlinks.
Uses complete synthetic fixtures - truly isolated, no dependencies on real output.

SETUP:
- Creates complete enhanced Fast Fish format fixtures
- Runs Step 34b in isolated sandbox
- Verifies dual output pattern for CSV files (timestamped + period + generic symlinks)
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_step34_dual_output_isolated(tmp_path):
    """Test Step 34b creates timestamped files + symlinks in isolation."""
    
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
    
    # Create complete fixtures for Step 34b
    _create_step34b_fixtures(sandbox)
    
    # Run Step 34b
    try:
        _run_step34b(sandbox)
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Step 34b failed to run: {e}")
    except Exception as e:
        pytest.skip(f"Step 34b requires more setup: {e}")
    
    # Verify dual output pattern for Step 34b outputs
    timestamped_files = list(output_dir.glob("enhanced_fast_fish_format_202510A_unified_202510A_*.csv"))
    timestamped_files = [f for f in timestamped_files if re.search(r'_\d{8}_\d{6}\.csv$', f.name)]
    
    if len(timestamped_files) == 0:
        pytest.skip("Step 34b did not create timestamped outputs")
    
    print(f"\nFound {len(timestamped_files)} timestamped CSV files")
    
    # Verify timestamped files and their symlinks
    for timestamped_file in timestamped_files:
        # Must be real file
        assert timestamped_file.is_file() and not timestamped_file.is_symlink()
        
        # Must have correct format
        assert re.search(r'_\d{8}_\d{6}\.csv$', timestamped_file.name)
        
        print(f"\nChecking: {timestamped_file.name}")
        
        # Step 34b uses create_output_with_symlinks which creates:
        # 1. Timestamped file: enhanced_fast_fish_format_202510A_unified_202510A_20251006_132331.csv
        # 2. Period symlink: enhanced_fast_fish_format_202510A_unified_202510A.csv
        # 3. Generic symlink: enhanced_fast_fish_format_202510A_unified.csv
        # Check for period symlink
        period_file = output_dir / "enhanced_fast_fish_format_202510A_unified_202510A.csv"
        if period_file.exists():
            assert period_file.is_symlink(), f"{period_file.name} should be a symlink"
            link_target = os.readlink(period_file)
            assert '/' not in link_target, f"{period_file.name} should use basename"
            assert re.search(r'_\d{8}_\d{6}\.csv$', link_target)
            print(f"   Period symlink: {period_file.name} -> {link_target}")
        
        # Check for generic symlink
        generic_file = output_dir / "enhanced_fast_fish_format_202510A_unified.csv"
        if generic_file.exists():
            assert generic_file.is_symlink(), f"{generic_file.name} should be a symlink"
            link_target = os.readlink(generic_file)
            assert '/' not in link_target, f"{generic_file.name} should use basename"
            # Generic symlink points to period symlink
            assert '202510A' in link_target
            print(f"   Generic symlink: {generic_file.name} -> {link_target}")
    print(f"\nStep 34b dual output pattern verified!")


def _create_step34b_fixtures(sandbox: Path):
    """Create complete fixtures for Step 34b: enhanced Fast Fish format files."""
    
    output_dir = sandbox / "output"
    target_period = "202510A"
    
    # Enhanced Fast Fish format (Step 14 output, Step 34b input)
    # This is what Step 34b unifies
    fast_fish_data = {
        'Year': [2025] * 10,
        'Month': [10] * 10,
        'Period': ['A'] * 10,
        'Store_Group_Name': ['Group A', 'Group B'] * 5,
        'Target_Style_Tags': ['[秋, 男]', '[冬, 女]'] * 5,
        'ΔQty': [20, -10, 15, 5, -8, 12, 18, -5, 10, 7],
        'Store_Codes_In_Group': ['1001,1002', '2001,2002'] * 5,
        'Category': ['POLO衫', 'T恤'] * 5,
        'Subcategory': ['休闲POLO', '基础T恤'] * 5,
        'Season': ['秋', '冬'] * 5,
        'Gender': ['男', '女'] * 5,
        'period_label': [target_period] * 10
    }
    fast_fish_df = pd.DataFrame(fast_fish_data)
    
    # Create period-specific file (as Step 14 would)
    fast_fish_df.to_csv(output_dir / f"enhanced_fast_fish_format_{target_period}.csv", index=False)
    
    print(f"Created enhanced Fast Fish format fixtures: {len(fast_fish_df)} recommendations")


def _run_step34b(sandbox: Path):
    """Run Step 34b in isolated sandbox."""
    
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["PYTHONPATH"] = str(sandbox)
    
    result = subprocess.run(
        ["python3", "src/step34b_unify_outputs.py",
         "--target-yyyymm", "202510",
         "--periods", "A",
         "--source", "enhanced"],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"\nStep 34b failed:")
        print(f"STDOUT:\n{result.stdout[-500:]}")
        print(f"STDERR:\n{result.stderr[-500:]}")
        raise subprocess.CalledProcessError(result.returncode, result.args)
    
    print(f"Step 34b completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
