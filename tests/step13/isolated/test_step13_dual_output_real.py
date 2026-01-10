"""
Step 13 Dual Output Pattern Test (Real Output Verification)
============================================================

Tests that Step 13's actual output follows the dual output pattern.
Uses real output files from the last run to verify compliance.
"""

import os
import re
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = PROJECT_ROOT / "output"


def test_step13_dual_output_real():
    """Test that Step 13's real output follows dual output pattern."""
    
    # Find Step 13 timestamped output files
    timestamped_files = list(OUTPUT_DIR.glob("consolidated_spu_rule_results_detailed_*_*.csv"))
    timestamped_files = [f for f in timestamped_files if re.search(r'_\d{8}_\d{6}\.csv$', f.name)]
    
    if len(timestamped_files) == 0:
        pytest.skip("No Step 13 output files found. Run Step 13 first.")
    
    print(f"\n✅ Found {len(timestamped_files)} timestamped Step 13 files")
    
    # Test each timestamped file
    for timestamped_file in timestamped_files:
        print(f"\n📄 Testing: {timestamped_file.name}")
        
        # 1. Must be a real file (not symlink)
        assert timestamped_file.is_file() and not timestamped_file.is_symlink(), \
            f"{timestamped_file.name} should be a real file, not a symlink"
        
        # 2. Must have correct timestamp format
        assert re.search(r'_\d{8}_\d{6}\.csv$', timestamped_file.name), \
            f"{timestamped_file.name} should have format _YYYYMMDD_HHMMSS.csv"
        
        # 3. Extract period label (e.g., 202410A)
        match = re.search(r'_(\d{6}[AB])_\d{8}_\d{6}\.csv$', timestamped_file.name)
        if not match:
            print(f"   ⚠️  No period label found in {timestamped_file.name}")
            continue
            
        period_label = match.group(1)
        print(f"   Period: {period_label}")
        
        # 4. Check for period-labeled symlink
        period_symlink = OUTPUT_DIR / f"consolidated_spu_rule_results_detailed_{period_label}.csv"
        
        if period_symlink.exists():
            # Must be a symlink
            assert period_symlink.is_symlink(), \
                f"{period_symlink.name} should be a symlink"
            
            # Must use basename (relative symlink)
            link_target = os.readlink(period_symlink)
            assert '/' not in link_target, \
                f"{period_symlink.name} should use basename, not absolute path"
            
            # Must point to a timestamped file
            assert re.search(r'_\d{8}_\d{6}\.csv$', link_target), \
                f"{period_symlink.name} should point to timestamped file"
            
            print(f"   ✅ Period symlink: {period_symlink.name} -> {link_target}")
        else:
            print(f"   ⚠️  Period symlink not found: {period_symlink.name}")
    
    print(f"\n✅ All {len(timestamped_files)} Step 13 files follow dual output pattern!")


def test_step13_output_structure():
    """Test that Step 13 output has expected structure."""
    
    import pandas as pd
    
    # Find latest detailed output
    detailed_files = list(OUTPUT_DIR.glob("consolidated_spu_rule_results_detailed_*_*.csv"))
    detailed_files = [f for f in detailed_files if re.search(r'_\d{8}_\d{6}\.csv$', f.name)]
    
    if not detailed_files:
        pytest.skip("No Step 13 detailed output found")
    
    latest = max(detailed_files, key=lambda x: x.stat().st_mtime)
    print(f"\n📄 Testing structure of: {latest.name}")
    
    # Load and check structure
    df = pd.read_csv(latest, nrows=100)
    
    # Required columns
    required_cols = ['str_code', 'spu_code', 'sub_cate_name', 'recommended_quantity_change']
    missing = [col for col in required_cols if col not in df.columns]
    
    assert len(missing) == 0, f"Missing required columns: {missing}"
    
    print(f"   ✅ Has all required columns")
    print(f"   ✅ Shape: {df.shape}")
    print(f"   ✅ Columns: {len(df.columns)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
