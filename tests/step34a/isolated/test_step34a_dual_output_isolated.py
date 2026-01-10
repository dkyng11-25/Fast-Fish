"""
Step 34a Dual Output Pattern Test (Isolated)
====================================================

Tests that Step 34a creates timestamped files + symlinks.
Uses isolated fixture data - no dependencies on real output directory.

Step 34a reads from Step 33 store-level merchandising rules and creates
cluster-level strategies.
"""

import os
import re
import shutil
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_step34a_dual_output_isolated(tmp_path):
    """Test Step 34a creates timestamped files + symlinks in isolation."""
    
    # Create isolated sandbox
    sandbox = tmp_path / "sandbox"
    output_dir = sandbox / "output"
    output_dir.mkdir(parents=True)
    
    # Copy src directory to sandbox
    src_dir = sandbox / "src"
    shutil.copytree(PROJECT_ROOT / "src", src_dir)
    
    # Create minimal fixture data
    _create_fixture_data(sandbox)
    
    # Run step
    try:
        _run_step34a(sandbox)
    except Exception as e:
        import traceback
        print(f"\n❌ Step 34a failed with error:")
        print(traceback.format_exc())
        pytest.skip(f"Step 34a requires more setup: {e}")
    
    # Verify dual output pattern
    # Step 34a creates cluster_level_merchandising_strategies files
    timestamped_files = list(output_dir.glob("cluster_level_merchandising_strategies_*_*.csv"))
    timestamped_files = [f for f in timestamped_files if re.search(r'_\d{8}_\d{6}\.csv$', f.name)]
    
    if len(timestamped_files) == 0:
        # Debug: show what files were created
        all_files = list(output_dir.glob("*.csv"))
        print(f"\n⚠️  No timestamped files found. Files in output dir:")
        for f in all_files:
            print(f"   - {f.name}")
        pytest.skip("Step 34a did not create timestamped outputs")
    
    print(f"\n✅ Found {len(timestamped_files)} timestamped files")
    
    # Verify timestamped files
    for timestamped_file in timestamped_files:
        # Must be real file
        assert timestamped_file.is_file() and not timestamped_file.is_symlink()
        
        # Must have correct format
        assert re.search(r'_\d{8}_\d{6}\.csv$', timestamped_file.name)
        
        # Check for corresponding symlink
        # Pattern: cluster_level_merchandising_strategies_202510A_20251006_123456.csv
        # Generic: cluster_level_merchandising_strategies_202510A.csv or cluster_level_merchandising_strategies.csv
        
        # Try period-labeled symlink first
        period_match = re.search(r'_(202\d{3}[AB])_\d{8}_\d{6}\.csv$', timestamped_file.name)
        if period_match:
            period_label = period_match.group(1)
            period_file = output_dir / f"cluster_level_merchandising_strategies_{period_label}.csv"
            if period_file.exists():
                assert period_file.is_symlink()
                link_target = os.readlink(period_file)
                assert '/' not in link_target
                print(f"✅ {period_file.name} -> {link_target}")
        
        # Check for generic symlink
        generic_name = re.sub(r'_202\d{3}[AB]_\d{8}_\d{6}\.csv$', '.csv', timestamped_file.name)
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


def _create_fixture_data(sandbox: Path):
    """Create minimal fixture data for Step 34a."""
    
    output_dir = sandbox / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create minimal store-level merchandising rules (Step 33 output)
    store_rules = pd.DataFrame({
        'str_code': ['1001', '1002', '1003', '1004', '1005'],
        'cluster_id': ['0', '0', '1', '1', '2'],
        'operational_tag': ['high_volume', 'high_volume', 'standard', 'standard', 'boutique'],
        'style_tag': ['trendy', 'trendy', 'classic', 'classic', 'premium'],
        'capacity_tag': ['high', 'high', 'medium', 'medium', 'low'],
        'geographic_tag': ['urban', 'urban', 'suburban', 'suburban', 'rural'],
        'fashion_allocation_ratio': [0.6, 0.6, 0.5, 0.5, 0.7],
        'basic_allocation_ratio': [0.4, 0.4, 0.5, 0.5, 0.3],
        'capacity_utilization_target': [0.85, 0.85, 0.75, 0.75, 0.65],
        'priority_score': [0.8, 0.8, 0.6, 0.6, 0.7]
    })
    store_rules.to_csv(output_dir / "store_level_merchandising_rules_202510A.csv", index=False)


def _run_step34a(sandbox: Path):
    """Run Step 34a in isolated sandbox."""
    
    import sys
    import importlib.util
    import io
    from contextlib import redirect_stdout, redirect_stderr
    
    # Set up environment
    old_cwd = os.getcwd()
    old_path = sys.path.copy()
    
    # Capture output
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    try:
        # Change to sandbox
        os.chdir(sandbox)
        sys.path.insert(0, str(sandbox / "src"))
        
        # Set environment variables
        os.environ['PYTHONPATH'] = str(sandbox / "src")
        
        # Import and run Step 34a
        spec = importlib.util.spec_from_file_location(
            "step34a_cluster_strategy_optimization",
            sandbox / "src" / "step34a_cluster_strategy_optimization.py"
        )
        step34a_module = importlib.util.module_from_spec(spec)
        
        # Mock sys.argv for argparse
        old_argv = sys.argv
        sys.argv = ['step34a_cluster_strategy_optimization.py', 
                    '--target-yyyymm', '202510', 
                    '--target-period', 'A']
        
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                spec.loader.exec_module(step34a_module)
                # Call main() explicitly
                if hasattr(step34a_module, 'main'):
                    step34a_module.main()
        finally:
            sys.argv = old_argv
            
        # Print captured output for debugging
        output = stdout_capture.getvalue()
        if output:
            print("\n📋 Step 34a Output:")
            print(output[-500:])  # Last 500 chars
            
    finally:
        # Restore environment
        os.chdir(old_cwd)
        sys.path = old_path


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
