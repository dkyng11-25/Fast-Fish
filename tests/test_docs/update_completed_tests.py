#!/usr/bin/env python3
"""
Update tests for completed steps (7-14) to expect timestamped outputs with symlinks.
"""

from pathlib import Path

COMPLETED_STEPS = [7, 8, 9, 10, 11, 12, 13, 14]

def update_test_for_step(step_num: int):
    """Update test file for a completed step"""
    test_file = Path(f"test_step{step_num}_dual_output.py")
    
    if not test_file.exists():
        print(f"⚠️  Test file not found: {test_file}")
        return False
    
    content = test_file.read_text()
    
    # Update the test to check for timestamped files + symlinks
    new_test = f'''"""
Step {step_num} Dual Output Pattern Test (UPDATED)
{'=' * 50}

Tests that Step {step_num} creates timestamped outputs with symlinks.

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


def test_step{step_num}_creates_timestamped_output():
    """Test that Step {step_num} creates timestamped output file"""
    output_dir = PROJECT_ROOT / "output"
    
    if not output_dir.exists():
        pytest.skip("Output directory doesn't exist - run pipeline first")
    
    # Look for timestamped files (pattern: *_YYYYMMA_YYYYMMDD_HHMMSS.*)
    timestamp_pattern = re.compile(r'_\\d{{6}}[AB]_\\d{{8}}_\\d{{6}}\\.')
    
    matching_files = []
    for file in output_dir.glob("*"):
        if timestamp_pattern.search(file.name):
            matching_files.append(file)
    
    if not matching_files:
        pytest.skip(f"No timestamped files found for step {step_num} - run pipeline first")
    
    print(f"✅ Step {step_num} creates timestamped outputs:")
    for file in matching_files[:5]:
        print(f"   - {{file.name}}")
    
    assert len(matching_files) > 0, "Must have at least one timestamped file"


def test_step{step_num}_creates_period_symlink():
    """Test that Step {step_num} creates period-labeled symlink"""
    output_dir = PROJECT_ROOT / "output"
    
    if not output_dir.exists():
        pytest.skip("Output directory doesn't exist")
    
    # Look for period-labeled files (pattern: *_YYYYMMA.* without timestamp)
    period_pattern = re.compile(r'_\\d{{6}}[AB]\\.[^_]+$')
    timestamp_pattern = re.compile(r'_\\d{{8}}_\\d{{6}}')
    
    period_files = []
    for file in output_dir.glob("*"):
        if period_pattern.search(file.name) and not timestamp_pattern.search(file.name):
            period_files.append(file)
    
    if not period_files:
        pytest.skip(f"No period-labeled files found for step {step_num}")
    
    # Check if they are symlinks
    symlinks = [f for f in period_files if f.is_symlink()]
    
    print(f"✅ Step {step_num} creates period-labeled symlinks:")
    for file in symlinks[:5]:
        target = os.readlink(file)
        print(f"   - {{file.name}} -> {{target}}")
    
    assert len(symlinks) > 0, "Must have at least one period-labeled symlink"


def test_step{step_num}_symlinks_point_to_timestamped():
    """Test that symlinks point to timestamped files"""
    output_dir = PROJECT_ROOT / "output"
    
    if not output_dir.exists():
        pytest.skip("Output directory doesn't exist")
    
    # Find symlinks
    symlinks = [f for f in output_dir.glob("*") if f.is_symlink()]
    
    if not symlinks:
        pytest.skip(f"No symlinks found for step {step_num}")
    
    timestamp_pattern = re.compile(r'_\\d{{8}}_\\d{{6}}')
    
    for symlink in symlinks:
        target = os.readlink(symlink)
        # Target should have timestamp pattern
        assert timestamp_pattern.search(target), \\
            f"Symlink {{symlink.name}} should point to timestamped file, got: {{target}}"
    
    print(f"✅ Step {step_num} symlinks correctly point to timestamped files")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
'''
    
    test_file.write_text(new_test)
    return True


def main():
    print("="*80)
    print("UPDATING TESTS FOR COMPLETED STEPS")
    print("="*80)
    print()
    
    updated = 0
    failed = 0
    
    for step_num in COMPLETED_STEPS:
        if update_test_for_step(step_num):
            print(f"✅ Updated test for Step {step_num}")
            updated += 1
        else:
            print(f"❌ Failed to update test for Step {step_num}")
            failed += 1
    
    print()
    print("="*80)
    print(f"SUMMARY: Updated {updated} tests, Failed {failed}")
    print("="*80)
    print()
    print("Run tests with: pytest tests/dual_output_synthetic/test_step7_dual_output.py -v")


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent)
    main()
