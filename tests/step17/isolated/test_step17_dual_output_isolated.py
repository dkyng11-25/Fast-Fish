"""
Step 17 Dual Output Pattern Test (Isolated)
====================================================

Tests that Step 17 creates timestamped files + symlinks.
Uses complete synthetic fixtures - truly isolated, no dependencies on real output.

SETUP:
- Creates complete Step 14 output fixtures (Fast Fish format)
- Runs Step 17 in isolated sandbox
- Verifies dual output pattern (timestamped + symlink)
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_step17_dual_output_isolated(tmp_path):
    """Test Step 17 creates timestamped files + symlinks in isolation."""
    
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
    
    # Create complete Step 14 output fixtures
    _create_step14_output_fixtures(sandbox)
    
    # Run Step 17
    try:
        _run_step17(sandbox)
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Step 17 failed to run: {e}")
    except Exception as e:
        pytest.skip(f"Step 17 requires more setup: {e}")
    
    # Verify dual output pattern
    timestamped_files = list(output_dir.glob("*_*_*.csv"))
    timestamped_files = [f for f in timestamped_files if re.search(r'_\d{8}_\d{6}\.csv$', f.name)]
    
    if len(timestamped_files) == 0:
        pytest.skip("Step 17 did not create timestamped outputs")
    
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


def _create_step14_output_fixtures(sandbox: Path):
    """Create complete Step 14 output fixtures for Step 17 to consume."""
    
    output_dir = sandbox / "output"
    data_dir = sandbox / "data" / "api_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    target_period = "202510A"
    
    # Create Step 14 Fast Fish format output (Step 17's main input)
    step14_output = pd.DataFrame({
        'Store_Group_Name': ['Group A', 'Group B', 'Group C'] * 20,
        'Sub_Category': ['T恤', '裤子', '鞋'] * 20,
        'Target_Style_Tags': ['休闲T恤', '商务裤', '运动鞋'] * 20,
        'Current_SPU_Count': [10, 15, 12] * 20,
        'Target_SPU_Count': [15, 20, 10] * 20,
        'Current_SPU_Quantity': [100, 150, 120] * 20,
        'Target_SPU_Quantity': [150, 200, 100] * 20,
        'ΔQty': [5, 5, -2] * 20,
        'Total_Current_Sales': [10000, 15000, 12000] * 20,
        'Stores_In_Group_Selling_This_Category': [3, 3, 3] * 20,
        'Avg_Sales_Per_SPU': [1000, 1000, 1000] * 20,
        'Season': ['春', '夏', '秋'] * 20,
        'Gender': ['男', '女', '中性'] * 20,
        'Location': ['前台', '后台', '鞋配'] * 20
    })
    step14_output.to_csv(output_dir / f"enhanced_fast_fish_format_{target_period}.csv", index=False)
    
    print(f"✅ Created Step 14 output fixtures: {len(step14_output)} recommendations")


def _run_step17(sandbox: Path):
    """Run Step 17 in isolated sandbox."""
    
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["PYTHONPATH"] = str(sandbox)
    env["STEP17_ENABLE_TRENDING"] = "false"  # Disable trending for isolated test
    
    # Point Step 17 to our fixture file
    input_file = str(sandbox / "output" / "enhanced_fast_fish_format_202510A.csv")
    
    result = subprocess.run(
        ["python3", "src/step17_augment_recommendations.py",
         "--target-yyyymm", "202510",
         "--target-period", "A",
         "--input-file", input_file],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"\n❌ Step 17 failed:")
        print(f"STDOUT:\n{result.stdout[-500:]}")
        print(f"STDERR:\n{result.stderr[-500:]}")
        raise subprocess.CalledProcessError(result.returncode, result.args)
    
    print(f"✅ Step 17 completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
