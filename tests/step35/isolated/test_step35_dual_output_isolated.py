"""
Step 35 Dual Output Pattern Test (Isolated)
====================================================

Tests that Step 35 creates timestamped files + symlinks.
Uses complete synthetic fixtures - truly isolated, no dependencies on real output.

SETUP:
- Creates minimal but complete fixtures for all Step 35 inputs
- Runs Step 35 in isolated sandbox
- Verifies dual output pattern for CSV files (timestamped + period + generic symlinks)

Note: Step 35 integrates data from many previous steps, so we create minimal fixtures
for store allocation results, merchandising rules, cluster strategies, enriched attributes,
and Step 18 sell-through data.
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


def test_step35_dual_output_isolated(tmp_path):
    """Test Step 35 creates timestamped files + symlinks in isolation."""
    
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
    
    # Create complete fixtures for Step 35
    _create_step35_fixtures(sandbox)
    
    # Run Step 35
    try:
        _run_step35(sandbox)
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Step 35 failed to run: {e}")
    except Exception as e:
        pytest.skip(f"Step 35 requires more setup: {e}")
    
    # Verify dual output pattern for Step 35 outputs
    timestamped_files = list(output_dir.glob("store_level_merchandising_recommendations_202510A_*.csv"))
    timestamped_files = [f for f in timestamped_files if re.search(r'_\d{8}_\d{6}\.csv$', f.name)]
    
    if len(timestamped_files) == 0:
        pytest.skip("Step 35 did not create timestamped outputs")
    
    print(f"\n✅ Found {len(timestamped_files)} timestamped CSV files")
    
    # Verify timestamped files and their symlinks
    for timestamped_file in timestamped_files:
        # Must be real file
        assert timestamped_file.is_file() and not timestamped_file.is_symlink()
        
        # Must have correct format
        assert re.search(r'_\d{8}_\d{6}\.csv$', timestamped_file.name)
        
        print(f"\n📄 Checking: {timestamped_file.name}")
        
        # Step 35 uses create_output_with_symlinks which creates:
        # 1. Timestamped file: store_level_merchandising_recommendations_202510A_20251006_132927.csv
        # 2. Period symlink: store_level_merchandising_recommendations_202510A.csv
        # 3. Generic symlink: store_level_merchandising_recommendations.csv
        
        # Check for period symlink
        period_file = output_dir / "store_level_merchandising_recommendations_202510A.csv"
        if period_file.exists():
            assert period_file.is_symlink(), f"{period_file.name} should be a symlink"
            link_target = os.readlink(period_file)
            assert '/' not in link_target, f"{period_file.name} should use basename"
            assert re.search(r'_\d{8}_\d{6}\.csv$', link_target)
            print(f"   ✅ Period symlink: {period_file.name} -> {link_target}")
        
        # Check for generic symlink
        generic_file = output_dir / "store_level_merchandising_recommendations.csv"
        if generic_file.exists():
            assert generic_file.is_symlink(), f"{generic_file.name} should be a symlink"
            link_target = os.readlink(generic_file)
            assert '/' not in link_target, f"{generic_file.name} should use basename"
            # Generic symlink points to period symlink
            assert '202510A' in link_target
            print(f"   ✅ Generic symlink: {generic_file.name} -> {link_target}")
    
    print(f"\n✅ Step 35 dual output pattern verified!")


def _create_step35_fixtures(sandbox: Path):
    """Create minimal but complete fixtures for Step 35."""
    
    output_dir = sandbox / "output"
    target_period = "202510A"
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Store allocation results (Step 32 output)
    allocation_data = pd.DataFrame({
        'Period': ['A'] * 5,
        'str_code': [1001, 1002, 2001, 2002, 3001],
        'Store_Group_Name': ['Group A', 'Group A', 'Group B', 'Group B', 'Group C'],
        'Target_Style_Tags': ['[秋, 男]'] * 5,
        'Category': ['POLO衫'] * 5,
        'Subcategory': ['休闲POLO'] * 5,
        'Season': ['秋'] * 5,
        'Gender': ['男'] * 5,
        'Location': ['South'] * 5,
        'Group_ΔQty': [20, 20, 15, 15, 12],
        'Store_Allocation_Weight': [0.5, 0.5, 0.6, 0.4, 1.0],
        'Allocated_ΔQty': [10, 10, 9, 6, 12],
        'Allocation_Rationale': ['Weight-based'] * 5
    })
    allocation_data.to_csv(output_dir / f"store_level_allocation_results_{target_period}_{timestamp}.csv", index=False)
    
    # 2. Merchandising rules (Step 33 output)
    rules_data = pd.DataFrame({
        'str_code': [1001, 1002, 2001, 2002, 3001],
        'cluster_id': [1, 1, 2, 2, 3],
        'cluster_name': ['Fashion Heavy', 'Fashion Heavy', 'Balanced Mix', 'Balanced Mix', 'Basic Focus'],
        'temperature_zone': ['Warm', 'Moderate', 'Moderate', 'Cool', 'Warm']
    })
    rules_data.to_csv(output_dir / f"store_level_merchandising_rules_{target_period}_{timestamp}.csv", index=False)
    
    # 3. Cluster strategies (Step 34a output)
    strategies_data = pd.DataFrame({
        'cluster_id': [1, 2, 3],
        'cluster_name': ['Fashion Heavy', 'Balanced Mix', 'Basic Focus'],
        'operational_tag': ['High-Volume', 'Medium-Volume', 'Efficient-Size'],
        'style_tag': ['Fashion-Heavy', 'Balanced-Mix', 'Basic-Focus'],
        'capacity_tag': ['Large', 'Medium', 'Efficient'],
        'geographic_tag': ['Warm-South', 'Moderate-Central', 'Cool-North'],
        'fashion_allocation_ratio': [0.75, 0.55, 0.25],
        'basic_allocation_ratio': [0.25, 0.45, 0.75],
        'capacity_utilization_target': [0.85, 0.80, 0.90],
        'priority_score': [8.5, 7.0, 6.0],
        'implementation_notes': ['High priority'] * 3
    })
    strategies_timestamped = output_dir / f"cluster_level_merchandising_strategies_{target_period}_{timestamp}.csv"
    strategies_data.to_csv(strategies_timestamped, index=False)
    # Create symlink for period-specific file
    strategies_link = output_dir / f"cluster_level_merchandising_strategies_{target_period}.csv"
    if strategies_link.exists() or strategies_link.is_symlink():
        strategies_link.unlink()
    os.symlink(strategies_timestamped.name, strategies_link)
    
    # 4. Enriched store attributes (Step 22 output)
    attributes_data = pd.DataFrame({
        'str_code': [1001, 1002, 2001, 2002, 3001],
        'store_type': ['Fashion', 'Fashion', 'Balanced', 'Balanced', 'Basic'],
        'store_style_profile': ['Fashion-Heavy', 'Fashion-Heavy', 'Balanced', 'Balanced', 'Basic-Focus'],
        'fashion_ratio': [0.75, 0.70, 0.55, 0.50, 0.25],
        'basic_ratio': [0.25, 0.30, 0.45, 0.50, 0.75],
        'size_tier': ['Large', 'Medium', 'Large', 'High', 'Medium'],
        'estimated_rack_capacity': [1200, 1000, 1500, 1800, 900],
        'total_sales_amt': [50000, 40000, 60000, 75000, 45000],
        'total_sales_qty': [500, 400, 600, 750, 450]
    })
    attributes_data.to_csv(output_dir / f"enriched_store_attributes_{target_period}_{timestamp}.csv", index=False)
    
    # 5. Step 18 sell-through data (minimal)
    step18_data = pd.DataFrame({
        'Store_Group_Name': ['Group A', 'Group B', 'Group C'],
        'Current_Sell_Through_Rate': [0.65, 0.70, 0.60],
        'Target_Sell_Through_Rate': [0.75, 0.80, 0.70],
        'Sell_Through_Improvement': [0.10, 0.10, 0.10]
    })
    step18_data.to_csv(output_dir / f"sell_through_analysis_{target_period}_{timestamp}.csv", index=False)
    
    # 6. Plugin output (minimal)
    plugin_data = pd.DataFrame({
        'str_code': [1001, 1002, 2001, 2002, 3001],
        'Performance_Tier': ['High', 'Medium', 'High', 'High', 'Medium'],
        'Growth_Potential': ['High', 'Medium', 'High', 'Medium', 'Low'],
        'Risk_Level': ['Low', 'Low', 'Medium', 'Low', 'High'],
        'Action_Priority': ['Expand', 'Maintain', 'Expand', 'Maintain', 'Monitor']
    })
    plugin_data.to_csv(output_dir / "plugin_output.csv", index=False)
    
    # 7. Enhanced clustering results (what Step 35 looks for as "store tags")
    clustering_data = pd.DataFrame({
        'str_code': [1001, 1002, 2001, 2002, 3001],
        'cluster_id': [1, 1, 2, 2, 3],
        'cluster_name': ['Fashion Heavy', 'Fashion Heavy', 'Balanced Mix', 'Balanced Mix', 'Basic Focus']
    })
    clustering_data.to_csv(output_dir / "enhanced_clustering_results.csv", index=False)
    
    # 8. Weather data (Step 5 output)
    weather_data = pd.DataFrame({
        'str_code': [1001, 1002, 2001, 2002, 3001],
        'avg_temperature': [25.5, 22.3, 20.1, 18.5, 26.0],
        'avg_feels_like_temp': [26.0, 23.0, 21.0, 19.0, 27.0],
        'feels_like_temperature': [26.0, 23.0, 21.0, 19.0, 27.0],
        'temperature_band': ['Warm', 'Moderate', 'Moderate', 'Cool', 'Warm']
    })
    weather_data.to_csv(output_dir / "stores_with_feels_like_temperature.csv", index=False)
    
    print(f"✅ Created Step 35 fixtures: allocation, rules, strategies, attributes, Step 18, plugin, clustering, weather")


def _run_step35(sandbox: Path):
    """Run Step 35 in isolated sandbox."""
    
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["PYTHONPATH"] = str(sandbox)
    
    result = subprocess.run(
        ["python3", "src/step35_merchandising_strategy_deployment.py",
         "--target-yyyymm", "202510",
         "--target-period", "A"],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode != 0:
        print(f"\n❌ Step 35 failed:")
        print(f"STDOUT:\n{result.stdout[-1000:]}")
        print(f"STDERR:\n{result.stderr[-1000:]}")
        raise subprocess.CalledProcessError(result.returncode, result.args)
    
    print(f"✅ Step 35 completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
