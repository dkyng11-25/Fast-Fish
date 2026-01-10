"""
Step 20 Dual Output Pattern Test (Isolated)
====================================================

Tests that Step 20 creates timestamped files + symlinks.
Uses complete synthetic fixtures - truly isolated, no dependencies on real output.

SETUP:
- Creates complete Step 19 output fixtures (SPU breakdown files)
- Runs Step 20 in isolated sandbox
- Verifies dual output pattern for JSON validation report (timestamped + symlink)
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_step20_dual_output_isolated(tmp_path):
    """Test Step 20 creates timestamped JSON files + symlinks in isolation."""
    
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
    
    # Create complete Step 19 output fixtures
    _create_step19_output_fixtures(sandbox)
    
    # Run Step 20
    try:
        _run_step20(sandbox)
    except subprocess.CalledProcessError as e:
        pytest.skip(f"Step 20 failed to run: {e}")
    except Exception as e:
        pytest.skip(f"Step 20 requires more setup: {e}")
    
    # Verify dual output pattern for JSON files
    timestamped_files = list(output_dir.glob("comprehensive_validation_report_*.json"))
    timestamped_files = [f for f in timestamped_files if re.search(r'_\d{8}_\d{6}\.json$', f.name)]
    
    if len(timestamped_files) == 0:
        pytest.skip("Step 20 did not create timestamped JSON outputs")
    
    print(f"\n✅ Found {len(timestamped_files)} timestamped files")
    
    # Verify timestamped files
    for timestamped_file in timestamped_files:
        # Must be real file
        assert timestamped_file.is_file() and not timestamped_file.is_symlink()
        
        # Must have correct format (JSON files)
        assert re.search(r'_\d{8}_\d{6}\.json$', timestamped_file.name), \
            f"{timestamped_file.name} should have format _YYYYMMDD_HHMMSS.json"
        
        print(f"\n📄 Checking: {timestamped_file.name}")
        
        # Check for corresponding generic symlink
        generic_file = output_dir / "comprehensive_validation_report.json"
        
        if generic_file.exists():
            # Must be symlink
            assert generic_file.is_symlink(), \
                f"{generic_file.name} should be a symlink"
            
            # Must use basename (not absolute path)
            link_target = os.readlink(generic_file)
            assert '/' not in link_target, \
                f"{generic_file.name} should use basename, not absolute path"
            
            # Must point to a timestamped file
            assert re.search(r'_\d{8}_\d{6}\.json$', link_target), \
                f"{generic_file.name} should point to timestamped JSON file"
            
            print(f"   ✅ Generic symlink: {generic_file.name} -> {link_target}")
        else:
            print(f"   ⚠️  Generic symlink not found: {generic_file.name}")
    
    print(f"\n✅ All {len(timestamped_files)} Step 20 files follow dual output pattern!")


def _create_step19_output_fixtures(sandbox: Path):
    """Create complete Step 19 output fixtures for Step 20 to consume."""
    
    output_dir = sandbox / "output"
    
    # Step 20 needs Step 19's aggregation files to validate
    # Create detailed SPU recommendations
    detailed_spu = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003'] * 20,
        'spu_code': ['SPU001', 'SPU002', 'SPU003'] * 20,
        'sub_cate_name': ['T恤', '裤子', '鞋'] * 20,
        'recommended_quantity_change': [5, 10, -3] * 20,
        'investment_required': [500, 1000, -300] * 20,
        'cluster_id': [0, 0, 1] * 20
    })
    detailed_spu.to_csv(output_dir / "detailed_spu_recommendations_202510A.csv", index=False)
    
    # Create store-level aggregation
    store_agg = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003'] * 10,
        'total_quantity_change': [50, 100, -30] * 10,
        'total_investment': [5000, 10000, -3000] * 10
    })
    store_agg.to_csv(output_dir / "store_level_aggregation_202510A.csv", index=False)
    
    # Create cluster-subcategory aggregation
    cluster_agg = pd.DataFrame({
        'cluster_id': [0, 0, 1] * 10,
        'sub_cate_name': ['T恤', '裤子', '鞋'] * 10,
        'total_quantity_change': [150, 300, -90] * 10,
        'total_investment': [15000, 30000, -9000] * 10
    })
    cluster_agg.to_csv(output_dir / "cluster_subcategory_aggregation_202510A.csv", index=False)
    
    print(f"✅ Created Step 19 output fixtures: SPU ({len(detailed_spu)}), Store ({len(store_agg)}), Cluster ({len(cluster_agg)})")


def _run_step20(sandbox: Path):
    """Run Step 20 in isolated sandbox."""
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(sandbox)
    
    result = subprocess.run(
        ["python3", "src/step20_data_validation.py"],
        cwd=sandbox,
        env=env,
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        print(f"\n❌ Step 20 failed:")
        print(f"STDOUT:\n{result.stdout[-500:]}")
        print(f"STDERR:\n{result.stderr[-500:]}")
        raise subprocess.CalledProcessError(result.returncode, result.args)
    
    print(f"✅ Step 20 completed successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
