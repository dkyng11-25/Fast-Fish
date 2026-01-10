"""
Test Step 2B Dual Output Pattern
=================================

Tests that Step 2B creates timestamped files + symlinks correctly.
This test validates the dual output pattern implementation, not the business logic.
"""

import os
import re
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = PROJECT_ROOT / "output"


def test_step2b_dual_output_files_exist():
    """Test that Step 2B created timestamped output files."""
    
    # Look for Step 2B seasonal outputs
    patterns = [
        "seasonal_store_profiles__*.csv",
        "seasonal_category_patterns__*.csv",
        "seasonal_clustering_features__*.csv",
    ]
    
    timestamped_files = []
    for pattern in patterns:
        files = list(OUTPUT_DIR.glob(pattern))
        # Match files with double underscore and timestamp
        timestamped_files.extend([f for f in files if re.search(r'__\d{8}_\d{6}\.csv$', f.name)])
    
    if len(timestamped_files) == 0:
        pytest.skip("No Step 2B outputs found. Run Step 2B first.")
    
    print(f"\n✅ Found {len(timestamped_files)} Step 2B timestamped files")
    
    # Verify each is a real file
    for f in timestamped_files:
        assert f.is_file() and not f.is_symlink(), f"{f.name} should be a real file"
        assert re.search(r'__\d{8}_\d{6}\.csv$', f.name), f"{f.name} has wrong timestamp format"
        print(f"  ✅ {f.name}")


def test_step2b_creates_symlinks():
    """Test that Step 2B creates generic symlinks."""
    
    # Look for Step 2B timestamped files
    patterns = [
        "seasonal_store_profiles__*.csv",
        "seasonal_category_patterns__*.csv",
        "seasonal_clustering_features__*.csv",
    ]
    
    timestamped_files = []
    for pattern in patterns:
        files = list(OUTPUT_DIR.glob(pattern))
        timestamped_files.extend([f for f in files if re.search(r'__\d{8}_\d{6}\.csv$', f.name)])
    
    if len(timestamped_files) == 0:
        pytest.skip("No Step 2B outputs found")
    
    symlinks_found = 0
    for timestamped_file in timestamped_files:
        # Get generic filename (remove timestamp)
        generic_name = re.sub(r'__\d{8}_\d{6}\.csv$', '_.csv', timestamped_file.name)
        generic_file = OUTPUT_DIR / generic_name
        
        if generic_file.exists():
            assert generic_file.is_symlink(), f"{generic_file.name} should be a symlink"
            
            # Verify it points to a timestamped file
            link_target = os.readlink(generic_file)
            assert '/' not in link_target, f"Symlink should use basename: {link_target}"
            assert re.search(r'__\d{8}_\d{6}\.csv$', link_target), f"Symlink target has wrong format: {link_target}"
            
            symlinks_found += 1
            print(f"✅ {generic_file.name} -> {link_target}")
    
    if symlinks_found > 0:
        print(f"\n✅ Step 2B: {symlinks_found} symlinks verified")
    else:
        pytest.skip(f"No symlinks found for Step 2B (may not have been run yet)")


def test_step2b_symlink_targets_correct():
    """Test that Step 2B symlinks point to the correct timestamped files."""
    
    # Check specific symlinks
    expected_symlinks = [
        ("seasonal_store_profiles_.csv", "seasonal_store_profiles__"),
        ("seasonal_category_patterns_.csv", "seasonal_category_patterns__"),
        ("seasonal_clustering_features_.csv", "seasonal_clustering_features__"),
    ]
    
    verified = 0
    for symlink_name, expected_prefix in expected_symlinks:
        symlink_path = OUTPUT_DIR / symlink_name
        
        if symlink_path.exists() and symlink_path.is_symlink():
            link_target = os.readlink(symlink_path)
            
            # Verify target starts with expected prefix
            assert link_target.startswith(expected_prefix), \
                f"{symlink_name} should point to {expected_prefix}*, got {link_target}"
            
            # Verify target has timestamp
            assert re.search(r'__\d{8}_\d{6}\.csv$', link_target), \
                f"Target should have timestamp: {link_target}"
            
            # Verify target file exists
            target_path = OUTPUT_DIR / link_target
            assert target_path.exists(), f"Symlink target doesn't exist: {link_target}"
            
            verified += 1
            print(f"✅ {symlink_name} -> {link_target}")
    
    if verified == 0:
        pytest.skip("No Step 2B symlinks found")
    
    print(f"\n✅ Verified {verified} Step 2B symlinks")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
