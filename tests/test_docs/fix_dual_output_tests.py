#!/usr/bin/env python3
"""
Fix dual output tests to allow BOTH period-labeled AND timestamped files.

The correct behavior is:
- Period-labeled files (e.g., file_202510A.csv) MUST exist (no timestamp)
- Timestamped files (e.g., file_202510A_20251002_134500.csv) MAY exist (optional)
- Tests should PASS if period-labeled file exists, regardless of timestamped files
"""

from pathlib import Path
import re

def fix_test_file(filepath: Path):
    """Fix a single test file's assertion logic"""
    
    content = filepath.read_text()
    
    # Pattern to find and replace
    old_pattern = """    # Verify NO files have timestamp pattern
    timestamp_pattern = r'_\\d{8}_\\d{6}'
    
    for file in matching_files:
        # File should have period label
        assert re.search(r'_\\d{6}[AB]', file.name), \\
            f"❌ File should have period label: {file.name}"
        
        # File should NOT have timestamp
        assert not re.search(timestamp_pattern, file.name), \\
            f"❌ File should NOT have timestamp: {file.name}\""""
    
    new_pattern = """    # Verify period-labeled files exist WITHOUT timestamp
    timestamp_pattern = r'_\\d{8}_\\d{6}'
    period_pattern = r'_\\d{6}[AB]'
    
    # Find period-labeled files (no timestamp)
    period_files = [f for f in matching_files 
                    if re.search(period_pattern, f.name) 
                    and not re.search(timestamp_pattern, f.name)]
    
    # Find timestamped files (optional)
    timestamped_files = [f for f in matching_files 
                         if re.search(timestamp_pattern, f.name)]
    
    # MUST have at least one period-labeled file (no timestamp)
    assert len(period_files) > 0, \\
        f"❌ No period-labeled files found (expected pattern: *_YYYYMMA.ext)"
    
    # Timestamped files are OPTIONAL (allowed but not required)
    if timestamped_files:
        print(f"   Note: {len(timestamped_files)} timestamped file(s) also exist (for audit)")\""""
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        filepath.write_text(content)
        return True
    return False


def main():
    test_dir = Path(__file__).parent
    
    print("="*80)
    print("FIXING DUAL OUTPUT TESTS")
    print("="*80)
    print()
    
    fixed = 0
    skipped = 0
    
    for test_file in sorted(test_dir.glob("test_step*_dual_output.py")):
        if fix_test_file(test_file):
            print(f"✅ Fixed: {test_file.name}")
            fixed += 1
        else:
            print(f"⏭️  Skipped: {test_file.name} (already fixed or different pattern)")
            skipped += 1
    
    print()
    print("="*80)
    print(f"SUMMARY: Fixed {fixed} files, Skipped {skipped} files")
    print("="*80)
    print()
    print("Run tests again with: pytest tests/dual_output_synthetic/ -v")


if __name__ == "__main__":
    main()
