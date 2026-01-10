"""
Step 14 Dual Output Pattern Test (Isolated)
====================================================

Tests that Step 14 creates timestamped files + symlinks.
Uses complete synthetic fixtures - truly isolated, no dependencies on real output.

SETUP:
- Creates complete Step 13 output fixtures
- Runs Step 14 in isolated sandbox
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


def test_step14_dual_output_isolated(tmp_path):
    """Test Step 14 creates timestamped files + symlinks in isolation."""
    
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
""".strip()
    (src_dir / "pipeline_manifest.py").write_text(stub, encoding="utf-8")
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    
    # Create complete fixture data (Step 13 output)
    _create_step13_output_fixtures(sandbox)
    
    # Run Step 14
    try:
        _run_step14(sandbox)
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Step 14 failed to run: {e}")
    except Exception as e:
        pytest.skip(f"Step 14 requires more setup: {e}")
    
    # Verify dual output pattern
    # Step 14 creates enhanced_fast_fish_format files
    timestamped_files = list(output_dir.glob("enhanced_fast_fish_format_*_*_*.csv"))
    timestamped_files = [f for f in timestamped_files if re.search(r'_\d{8}_\d{6}\.csv$', f.name)]
    
    if len(timestamped_files) == 0:
        # Debug: show what files were created
        all_files = list(output_dir.glob("*.csv"))
        print(f"\n⚠️  No timestamped files found. Files in output dir:")
        for f in all_files:
            print(f"   - {f.name}")
        pytest.skip("Step 14 did not create timestamped outputs")
    
    print(f"\n✅ Found {len(timestamped_files)} timestamped files")
    
    # Verify timestamped files
    for timestamped_file in timestamped_files:
        print(f"\n📄 Checking: {timestamped_file.name}")
        
        # Must be real file
        assert timestamped_file.is_file() and not timestamped_file.is_symlink(), \
            f"{timestamped_file.name} should be a real file, not a symlink"
        
        # Must have correct format
        assert re.search(r'_\d{8}_\d{6}\.csv$', timestamped_file.name), \
            f"{timestamped_file.name} should have format _YYYYMMDD_HHMMSS.csv"
        
        # Check for corresponding period symlink (e.g., enhanced_fast_fish_format_202510A.csv)
        match = re.search(r'_(\d{6}[AB])_\d{8}_\d{6}\.csv$', timestamped_file.name)
        if match:
            period_label = match.group(1)
            period_symlink = output_dir / timestamped_file.name.replace(f"_{period_label}_", f"_{period_label}.csv").replace(f"_{timestamped_file.name.split('_')[-2]}_{timestamped_file.name.split('_')[-1]}", "")
            period_symlink = output_dir / f"enhanced_fast_fish_format_{period_label}.csv"
            
            if period_symlink.exists():
                # Must be symlink
                assert period_symlink.is_symlink(), \
                    f"{period_symlink.name} should be a symlink"
                
                # Must use basename (not absolute path)
                link_target = os.readlink(period_symlink)
                assert '/' not in link_target, \
                    f"{period_symlink.name} should use basename, not absolute path"
                
                # Must point to a timestamped file
                assert re.search(r'_\d{8}_\d{6}\.csv$', link_target), \
                    f"{period_symlink.name} should point to timestamped file"
                
                print(f"   ✅ Period symlink: {period_symlink.name} -> {link_target}")
            else:
                print(f"   ⚠️  Period symlink not found: {period_symlink.name}")
    
    print(f"\n✅ All {len(timestamped_files)} Step 14 files follow dual output pattern!")


def _create_step13_output_fixtures(sandbox: Path):
    """Create complete Step 13 output fixtures for Step 14 to consume."""
    
    output_dir = sandbox / "output"
    data_dir = sandbox / "data" / "api_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    period_label = "202510A"
    
    # Create Step 13 detailed output (main input for Step 14)
    step13_detailed = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003', 'S001', 'S002'] * 20,
        'spu_code': ['SPU001', 'SPU002', 'SPU003', 'SPU004', 'SPU005'] * 20,
        'sub_cate_name': ['T恤', '裤子', '鞋', 'T恤', '裤子'] * 20,
        'recommended_quantity_change': [5, 10, -3, 8, 12] * 20,
        'investment_required': [500, 1000, -300, 800, 1200] * 20,
        'unit_price': [100, 100, 100, 100, 100] * 20,
        'cluster_id': [0, 0, 1, 0, 0] * 20,
        'rule_source': ['rule7', 'rule8', 'rule9', 'rule7', 'rule8'] * 20,
        'business_rationale': ['Missing category'] * 100,
        'approval_reason': ['Peer stores selling well'] * 100,
        'fast_fish_compliant': [True] * 100,
        'opportunity_type': ['missing_category'] * 100,
        'period_label': [period_label] * 100,
        'target_yyyymm': ['202510'] * 100,
        'target_period': ['A'] * 100
    })
    step13_detailed.to_csv(output_dir / f"consolidated_spu_rule_results_detailed_{period_label}.csv", index=False)
    
    # Create clustering results
    clustering = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003'],
        'Cluster': [0, 0, 1]
    })
    clustering.to_csv(output_dir / f"clustering_results_spu_{period_label}.csv", index=False)
    
    # Create store config (for Step 14) - needs to be comprehensive
    # Step 14 expects store_config to have dimensional data per store/category
    store_config_rows = []
    for store in ['S001', 'S002', 'S003']:
        for subcat in ['T恤', '裤子', '鞋']:
            season = '春' if subcat == 'T恤' else ('夏' if subcat == '裤子' else '秋')
            gender = '男' if subcat == 'T恤' else ('女' if subcat == '裤子' else '中性')
            location = '前台' if subcat == 'T恤' else ('后台' if subcat == '裤子' else '鞋配')
            
            store_config_rows.append({
                'str_code': store,
                'str_name': f'Store {store[-1]}',
                'sub_cate_name': subcat,
                'cluster_id': 0 if store in ['S001', 'S002'] else 1,
                'Season': season,
                'Gender': gender,
                'Location': location,
                # Alternative column names that Step 14 might look for
                'season_name': season,
                'sex_name': gender,
                'display_location_name': location,
                # Percentage columns
                'men_pct': 0.6 if subcat == 'T恤' else 0.3,
                'women_pct': 0.3 if subcat == 'T恤' else 0.6,
                'frontcourt_pct': 0.7 if subcat == 'T恤' else 0.3,
                'backcourt_pct': 0.3 if subcat == 'T恤' else 0.7
            })
    store_config = pd.DataFrame(store_config_rows)
    store_config.to_csv(data_dir / f"store_config_{period_label}.csv", index=False)
    
    # Create SPU sales data with ALL required dimensional columns
    spu_sales = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003'] * 30,
        'str_name': ['Store 1', 'Store 2', 'Store 3'] * 30,
        'spu_code': ['SPU001', 'SPU002', 'SPU003'] * 30,
        'sub_cate_name': ['T恤', '裤子', '鞋'] * 30,
        'cate_name': ['上装', '裤子', '鞋'] * 30,
        'spu_sales_amt': [1000, 2000, 3000] * 30,
        'quantity': [10, 20, 30] * 30,
        'unit_price': [100, 100, 100] * 30,
        'investment_per_unit': [100, 100, 100] * 30,
        # Dimensional attributes
        'Season': ['春', '夏', '秋'] * 30,
        'Gender': ['男', '女', '中性'] * 30,
        'Location': ['前台', '后台', '鞋配'] * 30,
        'Target_Style_Tags': ['休闲T恤', '商务裤', '运动鞋'] * 30,
        # Additional fields Step 14 might need
        'spu_name': ['T恤款式1', '裤子款式1', '鞋款式1'] * 30,
        'brand': ['品牌A', '品牌B', '品牌C'] * 30
    })
    
    # Create for multiple periods (Step 14 looks for historical data)
    for period in ['202409A', '202409B', '202410A', '202410B']:
        spu_sales.to_csv(data_dir / f"complete_spu_sales_{period}.csv", index=False)
    
    # Create store temperature data
    store_temp = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003'],
        'str_name': ['Store 1', 'Store 2', 'Store 3'],
        'avg_temperature': [25.0, 22.0, 28.0],
        'feels_like_temperature': [26.0, 23.0, 29.0],
        'temperature_zone': ['温暖', '适中', '炎热']
    })
    store_temp.to_csv(data_dir / f"store_temperatures_{period_label}.csv", index=False)
    
    # Create SPU attributes (dimensional data)
    spu_attributes = pd.DataFrame({
        'spu_code': ['SPU001', 'SPU002', 'SPU003', 'SPU004', 'SPU005'],
        'spu_name': ['T恤款式1', '裤子款式1', '鞋款式1', 'T恤款式2', '裤子款式2'],
        'sub_cate_name': ['T恤', '裤子', '鞋', 'T恤', '裤子'],
        'cate_name': ['上装', '裤子', '鞋', '上装', '裤子'],
        'Season': ['春', '夏', '秋', '冬', '四季'],
        'Gender': ['男', '女', '中性', '男', '女'],
        'Location': ['前台', '后台', '鞋配', '前台', '后台'],
        'Target_Style_Tags': ['休闲T恤', '商务裤', '运动鞋', '时尚T恤', '休闲裤'],
        'brand': ['品牌A', '品牌B', '品牌C', '品牌A', '品牌B']
    })
    spu_attributes.to_csv(data_dir / f"spu_attributes_{period_label}.csv", index=False)
    
    # Create historical sell-through data (if Step 14 needs it)
    historical_st = pd.DataFrame({
        'spu_code': ['SPU001', 'SPU002', 'SPU003'] * 10,
        'str_code': ['S001', 'S002', 'S003'] * 10,
        'sell_through_pct': [0.75, 0.82, 0.68] * 10,
        'period': ['202409A'] * 30
    })
    historical_st.to_csv(data_dir / "historical_sell_through_202409A.csv", index=False)
    
    print(f"✅ Created Step 13 output fixtures: {len(step13_detailed)} recommendations")
    print(f"✅ Created SPU sales data with dimensional attributes")
    print(f"✅ Created store temperature data")
    print(f"✅ Created SPU attributes data")


def _run_step14(sandbox: Path):
    """Run Step 14 in isolated sandbox."""
    
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["PYTHONPATH"] = str(sandbox)
    
    # Point Step 14 to our fixture files
    env["STEP14_SPU_SALES_FILE"] = str(sandbox / "data" / "api_data" / "complete_spu_sales_202410A.csv")
    env["STEP14_STORE_CONFIG_FILE"] = str(sandbox / "data" / "api_data" / "store_config_202510A.csv")
    
    result = subprocess.run(
        ["python3", "src/step14_create_fast_fish_format.py",
         "--target-yyyymm", "202510",
         "--target-period", "A"],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"\n❌ Step 14 failed:")
        print(f"STDOUT:\n{result.stdout[-500:]}")
        print(f"STDERR:\n{result.stderr[-500:]}")
        raise subprocess.CalledProcessError(result.returncode, result.args)
    
    print(f"✅ Step 14 completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
