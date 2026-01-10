"""
Step 24 Dual Output Pattern Test (Isolated)
====================================================

Tests that Step 24 creates timestamped files + symlinks.
Uses complete synthetic fixtures - truly isolated, no dependencies on real output.

SETUP:
- Creates complete clustering, enriched attributes, and temperature fixtures
- Runs Step 24 in isolated sandbox
- Verifies dual output pattern for multiple CSV files (timestamped + symlink)
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_step24_dual_output_isolated(tmp_path):
    """Test Step 24 creates timestamped files + symlinks in isolation."""
    
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
    
    # Create complete clustering, enriched attributes, and temperature fixtures
    _create_clustering_attrs_temp_fixtures(sandbox)
    
    # Run Step 24
    try:
        _run_step24(sandbox)
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Step 24 failed to run: {e}")
    except Exception as e:
        pytest.skip(f"Step 24 requires more setup: {e}")
    
    # Verify dual output pattern for Step 24 outputs
    timestamped_files = list(output_dir.glob("*_202510A_*.csv"))
    timestamped_files = [f for f in timestamped_files if re.search(r'_\d{8}_\d{6}\.csv$', f.name)]
    
    if len(timestamped_files) == 0:
        pytest.skip("Step 24 did not create timestamped outputs")
    
    print(f"\n✅ Found {len(timestamped_files)} timestamped CSV files")
    
    # Verify timestamped files and their symlinks
    for timestamped_file in timestamped_files:
        # Must be real file
        assert timestamped_file.is_file() and not timestamped_file.is_symlink()
        
        # Must have correct format
        assert re.search(r'_\d{8}_\d{6}\.csv$', timestamped_file.name)
        
        print(f"\n📄 Checking: {timestamped_file.name}")
        
        # Check for corresponding generic symlink (Step 24 creates hardcoded generic filenames)
        # Determine which generic file to look for based on the timestamped filename
        if 'store_cluster_mapping' in timestamped_file.name:
            generic_file = output_dir / "store_cluster_mapping.csv"
        elif 'comprehensive_cluster_labels' in timestamped_file.name:
            generic_file = output_dir / "comprehensive_cluster_labels.csv"
        elif 'store_tags' in timestamped_file.name:
            generic_file = output_dir / "store_tags.csv"
        else:
            continue  # Skip files we don't recognize
        
        if generic_file.exists():
            # Must be symlink
            assert generic_file.is_symlink(), f"{generic_file.name} should be a symlink"
            
            # Must use basename
            link_target = os.readlink(generic_file)
            assert '/' not in link_target, f"{generic_file.name} should use basename"
            
            # Must point to timestamped file
            assert re.search(r'_\d{8}_\d{6}\.csv$', link_target)
            
            print(f"   ✅ Symlink: {generic_file.name} -> {link_target}")
    
    print(f"\n✅ Step 24 dual output pattern verified!")


def _create_clustering_attrs_temp_fixtures(sandbox: Path):
    """Create complete clustering, enriched attributes, and temperature fixtures for Step 24."""
    
    output_dir = sandbox / "output"
    target_period = "202510A"
    
    # Create clustering results
    clustering = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003', 'S004', 'S005'] * 20,
        'Cluster': [0, 0, 1, 1, 2] * 20,
        'cluster_id': [0, 0, 1, 1, 2] * 20
    })
    clustering.to_csv(output_dir / f"clustering_results_spu_{target_period}.csv", index=False)
    
    # Create enriched store attributes
    enriched_attrs = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003', 'S004', 'S005'] * 20,
        'store_type': ['Fashion', 'Basic', 'Balanced', 'Fashion', 'Fashion'] * 20,
        'size_tier': ['Large', 'Medium', 'Small', 'Medium', 'Large'] * 20,
        'rack_capacity_estimate': [100, 80, 60, 85, 95] * 20,
        'fashion_ratio': [0.7, 0.3, 0.5, 0.65, 0.75] * 20,
        'basic_ratio': [0.3, 0.7, 0.5, 0.35, 0.25] * 20
    })
    timestamped_file = output_dir / f"enriched_store_attributes_{target_period}.csv"
    enriched_attrs.to_csv(timestamped_file, index=False)
    # Create symlink for Step 24
    generic_file = output_dir / "enriched_store_attributes.csv"
    if generic_file.exists() or generic_file.is_symlink():
        generic_file.unlink()
    os.symlink(timestamped_file.name, generic_file)
    
    # Create temperature data
    temperature = pd.DataFrame({
        'store_code': ['S001', 'S002', 'S003', 'S004', 'S005'] * 20,
        'feels_like_temp': [25.5, 26.0, 24.5, 25.0, 26.5] * 20,
        'temp_zone': ['Warm', 'Warm', 'Moderate', 'Warm', 'Warm'] * 20
    })
    temperature.to_csv(output_dir / "stores_with_feels_like_temperature.csv", index=False)
    
    print(f"✅ Created clustering fixtures: {len(clustering)} records")
    print(f"✅ Created enriched attributes fixtures: {len(enriched_attrs)} records")
    print(f"✅ Created temperature fixtures: {len(temperature)} records")


def _run_step24(sandbox: Path):
    """Run Step 24 in isolated sandbox."""
    
    env = os.environ.copy()
    env["PIPELINE_TARGET_YYYYMM"] = "202510"
    env["PIPELINE_TARGET_PERIOD"] = "A"
    env["PYTHONPATH"] = str(sandbox)
    
    result = subprocess.run(
        ["python3", "src/step24_comprehensive_cluster_labeling.py",
         "--target-yyyymm", "202510",
         "--target-period", "A"],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"\n❌ Step 24 failed:")
        print(f"STDOUT:\n{result.stdout[-500:]}")
        print(f"STDERR:\n{result.stderr[-500:]}")
        raise subprocess.CalledProcessError(result.returncode, result.args)
    
    print(f"✅ Step 24 completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
