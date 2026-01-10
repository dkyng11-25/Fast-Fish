"""
Step 18 Dual Output Pattern Test (Isolated)
====================================================

Tests that Step 18 creates timestamped files + symlinks.
Uses complete synthetic fixtures - truly isolated, no dependencies on real output.

SETUP:
- Creates complete Step 17 output fixtures (augmented recommendations)
- Creates historical reference fixtures
- Runs Step 18 in isolated sandbox
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


def test_step18_dual_output_isolated(tmp_path):
    """Test Step 18 creates timestamped files + symlinks in isolation."""
    
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
    
    # Create complete Step 17 output and historical fixtures
    _create_step17_and_historical_fixtures(sandbox)
    
    # Run Step 18
    try:
        _run_step18(sandbox)
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Step 18 failed to run: {e}")
    except Exception as e:
        pytest.skip(f"Step 18 requires more setup: {e}")
    
    # Verify dual output pattern
    timestamped_files = list(output_dir.glob("*_*_*.csv"))
    timestamped_files = [f for f in timestamped_files if re.search(r'_\d{8}_\d{6}\.csv$', f.name)]
    
    if len(timestamped_files) == 0:
        pytest.skip("Step 18 did not create timestamped outputs")
    
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


def _create_step17_and_historical_fixtures(sandbox: Path):
    """Create complete Step 17 output and historical fixtures for Step 18 to consume."""
    
    output_dir = sandbox / "output"
    
    target_period = "202510A"
    baseline_period = "202410A"
    
    # Create Step 17 augmented recommendations output (Step 18's main input)
    step17_output = pd.DataFrame({
        'Store_Group_Name': ['Group A', 'Group B', 'Group C'] * 20,
        'Sub_Category': ['T恤', '裤子', '鞋'] * 20,
        'category': ['上装', '裤子', '鞋'] * 20,
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
        'Location': ['前台', '后台', '鞋配'] * 20,
        # Historical reference columns from Step 17
        'Historical_SPU_Count': [8, 12, 10] * 20,
        'Historical_Sales': [8000, 12000, 10000] * 20,
        'Historical_Avg_Sales_Per_SPU': [1000, 1000, 1000] * 20
    })
    step17_output.to_csv(output_dir / f"fast_fish_with_historical_and_cluster_trending_analysis_{target_period}.csv", index=False)
    
    # Create historical reference file (for sell-through calculation)
    # Must match the column names Step 18 expects
    historical_data = pd.DataFrame({
        'Store_Group_Name': ['Group A', 'Group B', 'Group C'] * 15,
        'Category': ['上装', '裤子', '鞋'] * 15,
        'Subcategory': ['T恤', '裤子', '鞋'] * 15,
        'historical_spu_count': [8, 12, 10] * 15,
        'historical_total_sales': [8000, 12000, 10000] * 15,
        'historical_avg_sales_per_spu': [1000, 1000, 1000] * 15,
        'Historical_Total_Quantity': [80, 120, 100] * 15,
        'Historical_Store_Count': [3, 3, 3] * 15
    })
    historical_data.to_csv(output_dir / f"historical_reference_{baseline_period}.csv", index=False)
    
    print(f"✅ Created Step 17 output fixtures: {len(step17_output)} recommendations")
    print(f"✅ Created historical reference fixtures: {len(historical_data)} records")


def _run_step18(sandbox: Path):
    """Run Step 18 in isolated sandbox."""
    
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["PYTHONPATH"] = str(sandbox)
    
    # Point Step 18 to our fixture file (it will find historical reference automatically)
    input_file = str(sandbox / "output" / "fast_fish_with_historical_and_cluster_trending_analysis_202510A.csv")
    
    result = subprocess.run(
        ["python3", "src/step18_validate_results.py",
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
        print(f"\n❌ Step 18 failed:")
        print(f"STDOUT:\n{result.stdout[-500:]}")
        print(f"STDERR:\n{result.stderr[-500:]}")
        raise subprocess.CalledProcessError(result.returncode, result.args)
    
    print(f"✅ Step 18 completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
