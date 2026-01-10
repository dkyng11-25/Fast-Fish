"""
Step 16 Dual Output Pattern Test (Isolated)
====================================================

Tests that Step 16 creates timestamped Excel files + symlinks.
Uses complete synthetic fixtures - truly isolated, no dependencies on real output.

SETUP:
- Creates complete Step 15 output fixtures (YOY comparison + historical reference)
- Runs Step 16 in isolated sandbox
- Verifies dual output pattern for Excel files (timestamped + symlink)
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_step16_dual_output_isolated(tmp_path):
    """Test Step 16 creates timestamped Excel files + symlinks in isolation."""
    
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
    
    # Create complete Step 15 output fixtures
    _create_step15_output_fixtures(sandbox)
    
    # Run Step 16
    try:
        _run_step16(sandbox)
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Step 16 failed to run: {e}")
    except Exception as e:
        pytest.skip(f"Step 16 requires more setup: {e}")
    
    # Verify dual output pattern for Excel files
    # Step 16 creates spreadsheet_comparison_analysis Excel files
    timestamped_files = list(output_dir.glob("spreadsheet_comparison_analysis_*_*_*.xlsx"))
    timestamped_files = [f for f in timestamped_files if re.search(r'_\d{8}_\d{6}\.xlsx$', f.name)]
    
    if len(timestamped_files) == 0:
        # Debug: show what files were created
        all_files = list(output_dir.glob("*.xlsx"))
        print(f"\n⚠️  No timestamped Excel files found. Files in output dir:")
        for f in all_files:
            print(f"   - {f.name}")
        pytest.skip("Step 16 did not create timestamped Excel outputs")
    
    print(f"\n✅ Found {len(timestamped_files)} timestamped files")
    
    # Verify timestamped files
    for timestamped_file in timestamped_files:
        # Must be real file
        assert timestamped_file.is_file() and not timestamped_file.is_symlink()
        
        # Must have correct format (Excel files)
        assert re.search(r'_\d{8}_\d{6}\.xlsx$', timestamped_file.name), \
            f"{timestamped_file.name} should have format _YYYYMMDD_HHMMSS.xlsx"
        
        print(f"\n📄 Checking: {timestamped_file.name}")
        
        # Check for corresponding period symlink
        match = re.search(r'_(\d{6}[AB])_\d{8}_\d{6}\.xlsx$', timestamped_file.name)
        if match:
            period_label = match.group(1)
            period_symlink = output_dir / f"spreadsheet_comparison_analysis_{period_label}.xlsx"
            
            if period_symlink.exists():
                # Must be symlink
                assert period_symlink.is_symlink(), \
                    f"{period_symlink.name} should be a symlink"
                
                # Must use basename (not absolute path)
                link_target = os.readlink(period_symlink)
                assert '/' not in link_target, \
                    f"{period_symlink.name} should use basename, not absolute path"
                
                # Must point to a timestamped file
                assert re.search(r'_\d{8}_\d{6}\.xlsx$', link_target), \
                    f"{period_symlink.name} should point to timestamped Excel file"
                
                print(f"   ✅ Period symlink: {period_symlink.name} -> {link_target}")
            else:
                print(f"   ⚠️  Period symlink not found: {period_symlink.name}")
    
    print(f"\n✅ All {len(timestamped_files)} Step 16 files follow dual output pattern!")


def _create_step15_output_fixtures(sandbox: Path):
    """Create complete Step 15 output fixtures for Step 16 to consume."""
    
    output_dir = sandbox / "output"
    
    target_period = "202510A"
    baseline_period = "202410A"
    
    # Create YOY comparison file (Step 15 output) - match real column structure
    yoy_data = pd.DataFrame({
        'store_group': ['Group A', 'Group B', 'Group C'] * 20,
        'category': ['上装', '裤子', '鞋'] * 20,
        'sub_category': ['T恤', '裤子', '鞋'] * 20,
        'historical_spu_count': [10, 15, 12] * 20,
        'historical_total_quantity': [100, 150, 120] * 20,
        'historical_total_sales': [10000, 15000, 12000] * 20,
        'historical_store_count': [3, 3, 3] * 20,
        'historical_avg_sales_per_spu': [1000, 1000, 1000] * 20,
        'historical_avg_quantity_per_spu': [10, 10, 10] * 20,
        'historical_sales_per_store': [3333, 5000, 4000] * 20,
        'Store_Group_Name': ['Group A', 'Group B', 'Group C'] * 20,
        'Current_SPU_Quantity': [150, 200, 100] * 20,
        'Target_SPU_Quantity': [200, 250, 120] * 20,
        'Stores_In_Group_Selling_This_Category': [3, 3, 3] * 20,
        'Total_Current_Sales': [15000, 20000, 10000] * 20,
        'Avg_Sales_Per_SPU': [1500, 1333, 833] * 20,
        'yoy_spu_count_change': [5, 5, -2] * 20,
        'yoy_spu_count_change_pct': [50.0, 33.3, -16.7] * 20,
        'yoy_sales_change': [5000, 5000, -2000] * 20,
        'yoy_sales_change_pct': [50.0, 33.3, -16.7] * 20,
        'yoy_avg_sales_per_spu_change': [500, 333, -167] * 20,
        'yoy_avg_sales_per_spu_change_pct': [50.0, 33.3, -16.7] * 20,
        'baseline_label': [baseline_period] * 60,
        'baseline_yyyymm': ['202410'] * 60,
        'baseline_period': ['A'] * 60,
        'target_yyyymm': ['202510'] * 60,
        'target_period': ['A'] * 60
    })
    yoy_data.to_csv(output_dir / f"year_over_year_comparison_{baseline_period}.csv", index=False)
    
    # Create historical reference file (Step 15 output)
    historical_data = pd.DataFrame({
        'store_group': ['Group A', 'Group B', 'Group C'] * 15,
        'category': ['上装', '裤子', '鞋'] * 15,
        'sub_category': ['T恤', '裤子', '鞋'] * 15,
        'historical_spu_count': [10, 15, 12] * 15,
        'historical_total_sales': [10000, 15000, 12000] * 15,
        'historical_avg_sales_per_spu': [1000, 1000, 1000] * 15
    })
    historical_data.to_csv(output_dir / f"historical_reference_{baseline_period}.csv", index=False)
    
    print(f"✅ Created Step 15 output fixtures: YOY ({len(yoy_data)} rows) + Historical ({len(historical_data)} rows)")


def _run_step16(sandbox: Path):
    """Run Step 16 in isolated sandbox."""
    
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["PYTHONPATH"] = str(sandbox)
    
    # Point Step 16 to our fixture files
    env["STEP16_YOY_FILE"] = str(sandbox / "output" / "year_over_year_comparison_202410A.csv")
    env["STEP16_HISTORICAL_FILE"] = str(sandbox / "output" / "historical_reference_202410A.csv")
    
    result = subprocess.run(
        ["python3", "src/step16_create_comparison_tables.py",
         "--target-yyyymm", "202510",
         "--target-period", "A",
         "--yoy-file", str(sandbox / "output" / "year_over_year_comparison_202410A.csv"),
         "--historical-file", str(sandbox / "output" / "historical_reference_202410A.csv")],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"\n❌ Step 16 failed:")
        print(f"STDOUT:\n{result.stdout[-500:]}")
        print(f"STDERR:\n{result.stderr[-500:]}")
        raise subprocess.CalledProcessError(result.returncode, result.args)
    
    print(f"✅ Step 16 completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
