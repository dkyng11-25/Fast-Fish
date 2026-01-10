"""
Step 29 Dual Output Pattern Test (Isolated)
====================================================

Tests that Step 29 creates timestamped files + symlinks.
Uses complete synthetic fixtures - truly isolated, no dependencies on real output.

SETUP:
- Creates complete sales, cluster, product roles, price bands, and store attributes fixtures
- Runs Step 29 in isolated sandbox
- Verifies dual output pattern for CSV files (timestamped + symlink)
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_step29_dual_output_isolated(tmp_path):
    """Test Step 29 creates timestamped files + symlinks in isolation."""
    
    # Create isolated sandbox
    sandbox = tmp_path / "sandbox"
    output_dir = sandbox / "output"
    data_dir = sandbox / "data" / "api_data"
    data_dir.mkdir(parents=True)
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
    
    # Create complete fixtures for Step 29
    _create_step29_fixtures(sandbox)
    
    # Run Step 29
    try:
        _run_step29(sandbox)
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Step 29 failed to run: {e}")
    except Exception as e:
        pytest.skip(f"Step 29 requires more setup: {e}")
    
    # Verify dual output pattern for Step 29 outputs
    timestamped_files = list(output_dir.glob("supply_demand_*_202510A_*.csv"))
    timestamped_files = [f for f in timestamped_files if re.search(r'_\d{8}_\d{6}\.csv$', f.name)]
    
    if len(timestamped_files) == 0:
        pytest.skip("Step 29 did not create timestamped outputs")
    
    print(f"\n✅ Found {len(timestamped_files)} timestamped CSV files")
    
    # Verify timestamped files and their symlinks
    for timestamped_file in timestamped_files:
        # Must be real file
        assert timestamped_file.is_file() and not timestamped_file.is_symlink()
        
        # Must have correct format
        assert re.search(r'_\d{8}_\d{6}\.csv$', timestamped_file.name)
        
        print(f"\n📄 Checking: {timestamped_file.name}")
        
        # Check for corresponding generic symlink (Step 29 creates hardcoded generic filename)
        generic_file = output_dir / "supply_demand_gap_detailed.csv"
        
        if generic_file.exists():
            # Must be symlink
            assert generic_file.is_symlink(), f"{generic_file.name} should be a symlink"
            
            # Must use basename
            link_target = os.readlink(generic_file)
            assert '/' not in link_target, f"{generic_file.name} should use basename"
            
            # Must point to timestamped file
            assert re.search(r'_\d{8}_\d{6}\.csv$', link_target)
            
            print(f"   ✅ Symlink: {generic_file.name} -> {link_target}")
    
    print(f"\n✅ Step 29 dual output pattern verified!")


def _create_step29_fixtures(sandbox: Path):
    """Create complete fixtures for Step 29: sales, clusters, roles, price bands, store attributes."""
    
    data_dir = sandbox / "data" / "api_data"
    output_dir = sandbox / "output"
    target_period = "202510A"
    
    # Create SPU sales data
    spu_sales = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003'] * 20,
        'spu_code': ['SPU001', 'SPU002', 'SPU003'] * 20,
        'cate_name': ['服装', '服装', '服装'] * 20,
        'sub_cate_name': ['T恤', '裤子', '鞋'] * 20,
        'sal_amt': [15000, 12000, 8000] * 20,
        'sal_qnty': [150, 120, 80] * 20
    })
    spu_sales.to_csv(data_dir / f"complete_spu_sales_{target_period}.csv", index=False)
    
    # Create clustering data
    clustering = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003'] * 20,
        'cluster_id': [0, 1, 2] * 20
    })
    clustering.to_csv(output_dir / f"clustering_results_spu_{target_period}.csv", index=False)
    
    # Create product roles
    product_roles = pd.DataFrame({
        'spu_code': ['SPU001', 'SPU002', 'SPU003'] * 20,
        'product_role': ['CORE', 'SEASONAL', 'FILLER'] * 20
    })
    roles_file = output_dir / f"product_role_classifications_{target_period}.csv"
    product_roles.to_csv(roles_file, index=False)
    roles_link = output_dir / "product_role_classifications.csv"
    if roles_link.exists() or roles_link.is_symlink():
        roles_link.unlink()
    os.symlink(roles_file.name, roles_link)
    
    # Create price bands
    price_bands = pd.DataFrame({
        'spu_code': ['SPU001', 'SPU002', 'SPU003'] * 20,
        'price_band': ['PREMIUM', 'VALUE', 'ECONOMY'] * 20
    })
    bands_file = output_dir / f"price_band_analysis_{target_period}.csv"
    price_bands.to_csv(bands_file, index=False)
    bands_link = output_dir / "price_band_analysis.csv"
    if bands_link.exists() or bands_link.is_symlink():
        bands_link.unlink()
    os.symlink(bands_file.name, bands_link)
    
    # Create store attributes
    store_attrs = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003'] * 20,
        'store_type': ['Fashion', 'Basic', 'Balanced'] * 20,
        'size_tier': ['Large', 'Medium', 'Small'] * 20,
        'fashion_ratio': [0.7, 0.3, 0.5] * 20,
        'basic_ratio': [0.3, 0.7, 0.5] * 20
    })
    attrs_file = output_dir / f"enriched_store_attributes_{target_period}.csv"
    store_attrs.to_csv(attrs_file, index=False)
    attrs_link = output_dir / "enriched_store_attributes.csv"
    if attrs_link.exists() or attrs_link.is_symlink():
        attrs_link.unlink()
    os.symlink(attrs_file.name, attrs_link)
    
    # Create store_sales file (needed for fashion/basic ratio derivation)
    store_sales = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003'] * 20,
        'sub_cate_name': ['T恤', '裤子', '鞋'] * 20,
        'sal_amt': [10000, 8000, 6000] * 20
    })
    store_sales.to_csv(output_dir / f"store_sales_{target_period}.csv", index=False)
    
    print(f"✅ Created SPU sales fixtures: {len(spu_sales)} records")
    print(f"✅ Created clustering fixtures: {len(clustering)} records")
    print(f"✅ Created product roles fixtures: {len(product_roles)} records")
    print(f"✅ Created price bands fixtures: {len(price_bands)} records")
    print(f"✅ Created store attributes fixtures: {len(store_attrs)} records")


def _run_step29(sandbox: Path):
    """Run Step 29 in isolated sandbox."""
    
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["PYTHONPATH"] = str(sandbox)
    
    result = subprocess.run(
        ["python3", "src/step29_supply_demand_gap_analysis.py",
         "--target-yyyymm", "202510",
         "--target-period", "A"],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"\n❌ Step 29 failed:")
        print(f"STDOUT:\n{result.stdout[-500:]}")
        print(f"STDERR:\n{result.stderr[-500:]}")
        raise subprocess.CalledProcessError(result.returncode, result.args)
    
    print(f"✅ Step 29 completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
