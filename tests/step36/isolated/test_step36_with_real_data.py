"""
Step 36 Test with Real Pipeline Data
=====================================

This test uses REAL pipeline output as fixtures to understand what Step 36 needs.
"""

import shutil
import subprocess
from pathlib import Path
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_step36_with_real_pipeline_data(tmp_path):
    """Test Step 36 using real pipeline output as fixtures"""
    
    # Create sandbox
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    output_dir = sandbox / "output"
    output_dir.mkdir()
    
    # Copy Step 36 source
    src_dir = sandbox / "src"
    shutil.copytree(PROJECT_ROOT / "src", src_dir)
    
    # Copy REAL pipeline output files
    real_output = PROJECT_ROOT / "output"
    
    # Required files for Step 36 (use glob patterns for timestamped files)
    required_file_patterns = [
        # Step 14: Enhanced Fast Fish (fallback if Step 18 not found)
        "enhanced_fast_fish_format_202510A.csv",
        # Step 32: Store allocation (find any timestamped version)
        "store_level_allocation_results_202510A_*.csv",
    ]
    
    # Optional files
    optional_files = [
        # Step 18: Sell-through analysis (preferred over Step 14)
        # "fast_fish_with_sell_through_analysis_202510A_*.csv",  # if exists
        # Step 33: Store metadata
        # "store_level_plugin_output_202510A_*.csv",  # if exists
    ]
    
    print("\n📋 Copying real pipeline files to sandbox:")
    copied_files = {}
    
    for pattern in required_file_patterns:
        # Find files matching pattern (handles wildcards)
        matching_files = list(real_output.glob(pattern))
        
        if matching_files:
            # Use the first (or most recent) matching file
            src_file = matching_files[0]
            # Resolve symlinks to get actual file
            if src_file.is_symlink():
                src_file = src_file.resolve()
            
            # Copy with original filename (not pattern)
            dest_name = src_file.name
            shutil.copy(src_file, output_dir / dest_name)
            print(f"  ✓ Copied: {dest_name}")
            
            # Track for manifest
            copied_files[pattern] = dest_name
        else:
            print(f"  ✗ Missing: {pattern}")
            pytest.skip(f"Required file not found: {pattern}")
    
    # Use environment variable overrides to point to copied files
    print("\n📝 Setting up environment overrides...")
    env = {
        **subprocess.os.environ,
        'STEP36_OVERRIDE_ALLOC': str(output_dir / copied_files.get('store_level_allocation_results_202510A_*.csv', '')),
    }
    
    # Step 36 prefers Step 18, but we can use Step 14 file as Step 18 override
    if 'enhanced_fast_fish_format_202510A.csv' in copied_files:
        step14_file = output_dir / copied_files['enhanced_fast_fish_format_202510A.csv']
        env['STEP36_OVERRIDE_STEP18'] = str(step14_file)  # Use Step 18 override for Step 14 file
        print(f"  ✓ STEP36_OVERRIDE_STEP18={step14_file.name}")
    
    print(f"  ✓ STEP36_OVERRIDE_ALLOC={copied_files.get('store_level_allocation_results_202510A_*.csv', '')}")
    
    # Run Step 36
    print("\n🚀 Running Step 36 with real data...")
    result = subprocess.run(
        ['python3', 'src/step36_unified_delivery_builder.py', 
         '--target-yyyymm', '202510', 
         '--target-period', 'A'],
        cwd=sandbox,
        capture_output=True,
        text=True,
        env=env
    )
    
    print(f"\n📤 Step 36 Output:")
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    
    if result.returncode != 0:
        print(f"\n❌ Step 36 Error:")
        print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
    
    assert result.returncode == 0, f"Step 36 failed with real data: {result.stderr}"
    
    # Check what was created
    print("\n📁 Output files created:")
    output_files = list(output_dir.glob("unified_delivery_*.csv"))
    for f in output_files:
        size = f.stat().st_size
        print(f"  ✓ {f.name} ({size:,} bytes)")
    
    # Load and inspect the output (use main file, not auxiliary files)
    if output_files:
        # Find the main unified_delivery file (not top_adds/top_reduces/cluster_level)
        main_files = [f for f in output_files if not any(x in f.name for x in ['top_adds', 'top_reduces', 'cluster_level', 'reconciliation'])]
        if not main_files:
            pytest.fail("No main unified_delivery file found")
        
        delivery_file = main_files[0]
        print(f"\n📄 Reading main file: {delivery_file.name}")
        df = pd.read_csv(delivery_file)
        
        print(f"\n📊 Output DataFrame:")
        print(f"  Rows: {len(df):,}")
        print(f"  Columns: {len(df.columns)}")
        print(f"\n  Sample columns:")
        for col in list(df.columns)[:10]:
            print(f"    - {col}")
        
        if len(df) > 0:
            print(f"\n  Sample data (first row):")
            for col in ['Category', 'Subcategory', 'Season', 'Gender']:
                if col in df.columns:
                    print(f"    {col}: {df[col].iloc[0]}")
        
        # This is what we learn!
        assert len(df) > 0, "Output should have data with real pipeline files"
        
        # Check for key columns
        expected_cols = ['Category', 'Store_Code', 'Allocated_ΔQty']
        for col in expected_cols:
            assert col in df.columns, f"Expected column {col} in output"
        
        print("\n✅ Step 36 successfully processed real pipeline data!")
        print(f"   Created {len(df):,} rows of delivery data")
    else:
        pytest.fail("No unified_delivery output files created")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
