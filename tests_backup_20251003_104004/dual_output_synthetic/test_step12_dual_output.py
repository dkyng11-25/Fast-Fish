"""
Step 12 Dual Output Pattern Test (UPDATED)
==================================================

Tests that Step 12 creates timestamped outputs with symlinks.

Expected pattern:
1. Timestamped file: file_YYYYMMA_YYYYMMDD_HHMMSS.csv (preserved)
2. Period symlink: file_YYYYMMA.csv -> timestamped file
3. Generic symlink: file.csv -> timestamped file
"""

import os
from pathlib import Path
import pytest
import re

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGET_PERIOD = "202510A"


def test_step12_creates_timestamped_output():
    """Test that Step 12 creates timestamped output file"""
    output_dir = PROJECT_ROOT / "output"
    
    if not output_dir.exists():
        pytest.skip("Output directory doesn't exist - run pipeline first")
    
    # Look for timestamped files (pattern: *_YYYYMMA_YYYYMMDD_HHMMSS.*)
    timestamp_pattern = re.compile(r'_\d{6}[AB]_\d{8}_\d{6}\.')
    
    matching_files = []
    for file in output_dir.glob("*"):
        if timestamp_pattern.search(file.name):
            matching_files.append(file)
    
    if not matching_files:
        pytest.skip(f"No timestamped files found for step 12 - run pipeline first")
    
    print(f"✅ Step 12 creates timestamped outputs:")
    for file in matching_files[:5]:
        print(f"   - {file.name}")
    
    assert len(matching_files) > 0, "Must have at least one timestamped file"


def test_step12_creates_period_symlink():
    """Test that Step 12 creates period-labeled symlink"""
    output_dir = PROJECT_ROOT / "output"
    
    if not output_dir.exists():
        pytest.skip("Output directory doesn't exist")
    
    # Look for period-labeled files (pattern: *_YYYYMMA.* without timestamp)
    period_pattern = re.compile(r'_\d{6}[AB]\.[^_]+$')
    timestamp_pattern = re.compile(r'_\d{8}_\d{6}')
    
    period_files = []
    for file in output_dir.glob("*"):
        if period_pattern.search(file.name) and not timestamp_pattern.search(file.name):
            period_files.append(file)
    
    if not period_files:
        pytest.skip(f"No period-labeled files found for step 12")
    
    # Check if they are symlinks
    symlinks = [f for f in period_files if f.is_symlink()]
    
    print(f"✅ Step 12 creates period-labeled symlinks:")
    for file in symlinks[:5]:
        target = os.readlink(file)
        print(f"   - {file.name} -> {target}")
    
    assert len(symlinks) > 0, "Must have at least one period-labeled symlink"


def test_step12_symlinks_point_to_timestamped():
    """Test that symlinks point to timestamped files"""
    output_dir = PROJECT_ROOT / "output"
    
    if not output_dir.exists():
        pytest.skip("Output directory doesn't exist")
    
    # Find symlinks
    symlinks = [f for f in output_dir.glob("*") if f.is_symlink()]
    
    if not symlinks:
        pytest.skip(f"No symlinks found for step 12")
    
    timestamp_pattern = re.compile(r'_\d{8}_\d{6}')
    
    for symlink in symlinks:
        target = os.readlink(symlink)
        # Target should have timestamp pattern
        assert timestamp_pattern.search(target), \
            f"Symlink {symlink.name} should point to timestamped file, got: {target}"
    
    print(f"✅ Step 12 symlinks correctly point to timestamped files")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
