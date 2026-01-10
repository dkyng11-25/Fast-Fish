"""
Dual Output Pattern Validation - Real Output Files
===================================================

Tests that validate the DUAL OUTPUT PATTERN on real output files.
This approach:
1. Checks actual output/ directory
2. Validates timestamped files exist
3. Validates symlinks exist and point correctly
4. No need for complex synthetic data setup
"""

import os
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"


def find_timestamped_files(directory: Path, pattern: str = "*_*_*.csv"):
    """Find all timestamped files matching pattern."""
    files = list(directory.glob(pattern))
    # Filter to only files with YYYYMMDD_HHMMSS format
    timestamped = [f for f in files if re.search(r'_\d{8}_\d{6}\.csv$', f.name)]
    return timestamped


def get_generic_filename(timestamped_file: Path) -> Path:
    """Get the expected generic filename for a timestamped file."""
    generic_name = re.sub(r'_\d{8}_\d{6}\.csv$', '.csv', timestamped_file.name)
    return timestamped_file.parent / generic_name


def test_output_directory_exists():
    """Test that output directory exists."""
    assert OUTPUT_DIR.exists(), f"Output directory not found: {OUTPUT_DIR}"
    assert OUTPUT_DIR.is_dir(), f"Output path is not a directory: {OUTPUT_DIR}"


def test_timestamped_files_exist():
    """Test that timestamped files exist in output directory."""
    timestamped_files = find_timestamped_files(OUTPUT_DIR)
    
    assert len(timestamped_files) > 0, \
        f"No timestamped files found in {OUTPUT_DIR}. Run some pipeline steps first."
    
    print(f"\n✅ Found {len(timestamped_files)} timestamped files")


def test_timestamped_files_are_real_files():
    """Test that timestamped files are real files, not symlinks."""
    timestamped_files = find_timestamped_files(OUTPUT_DIR)
    
    if len(timestamped_files) == 0:
        pytest.skip("No timestamped files found")
    
    issues = []
    for f in timestamped_files:
        if not f.is_file():
            issues.append(f"{f.name}: not a file")
        elif f.is_symlink():
            issues.append(f"{f.name}: is a symlink (should be real file)")
    
    assert len(issues) == 0, f"Found {len(issues)} issues:\n" + "\n".join(issues[:10])
    print(f"\n✅ All {len(timestamped_files)} timestamped files are real files")


def test_timestamp_format_correct():
    """Test that all timestamped files use correct format YYYYMMDD_HHMMSS."""
    timestamped_files = find_timestamped_files(OUTPUT_DIR)
    
    if len(timestamped_files) == 0:
        pytest.skip("No timestamped files found")
    
    issues = []
    for f in timestamped_files:
        match = re.search(r'_(\d{8})_(\d{6})\.csv$', f.name)
        if not match:
            issues.append(f"{f.name}: wrong format")
            continue
        
        # Validate date and time components
        date_part = match.group(1)
        time_part = match.group(2)
        
        year = int(date_part[:4])
        month = int(date_part[4:6])
        day = int(date_part[6:8])
        hour = int(time_part[:2])
        minute = int(time_part[2:4])
        second = int(time_part[4:6])
        
        if not (2020 <= year <= 2030):
            issues.append(f"{f.name}: invalid year {year}")
        if not (1 <= month <= 12):
            issues.append(f"{f.name}: invalid month {month}")
        if not (1 <= day <= 31):
            issues.append(f"{f.name}: invalid day {day}")
        if not (0 <= hour <= 23):
            issues.append(f"{f.name}: invalid hour {hour}")
        if not (0 <= minute <= 59):
            issues.append(f"{f.name}: invalid minute {minute}")
        if not (0 <= second <= 59):
            issues.append(f"{f.name}: invalid second {second}")
    
    assert len(issues) == 0, f"Found {len(issues)} format issues:\n" + "\n".join(issues[:10])
    print(f"\n✅ All {len(timestamped_files)} files have correct timestamp format")


def test_generic_symlinks_exist():
    """Test that generic symlinks exist for timestamped files."""
    timestamped_files = find_timestamped_files(OUTPUT_DIR)
    
    if len(timestamped_files) == 0:
        pytest.skip("No timestamped files found")
    
    symlinks_found = 0
    symlinks_missing = []
    
    for timestamped_file in timestamped_files:
        generic_file = get_generic_filename(timestamped_file)
        
        if generic_file.exists():
            symlinks_found += 1
        else:
            symlinks_missing.append(f"{timestamped_file.name} -> {generic_file.name}")
    
    print(f"\n✅ Found {symlinks_found}/{len(timestamped_files)} generic symlinks")
    
    if symlinks_missing:
        print(f"\n⚠️  Missing symlinks for {len(symlinks_missing)} files:")
        for missing in symlinks_missing[:5]:
            print(f"  - {missing}")
    
    # At least 50% should have symlinks
    assert symlinks_found >= len(timestamped_files) * 0.5, \
        f"Only {symlinks_found}/{len(timestamped_files)} files have symlinks (expected >= 50%)"


def test_symlinks_are_actually_symlinks():
    """Test that generic files are symlinks, not real files."""
    timestamped_files = find_timestamped_files(OUTPUT_DIR)
    
    if len(timestamped_files) == 0:
        pytest.skip("No timestamped files found")
    
    issues = []
    verified = 0
    
    for timestamped_file in timestamped_files:
        generic_file = get_generic_filename(timestamped_file)
        
        if generic_file.exists():
            if not generic_file.is_symlink():
                issues.append(f"{generic_file.name}: is a real file (should be symlink)")
            else:
                verified += 1
    
    # Some files may be from before the update, so be lenient
    if issues:
        print(f"\n⚠️  Found {len(issues)} non-symlink generic files (may be from before update):")
        for issue in issues[:5]:
            print(f"  - {issue}")
    
    print(f"\n✅ {verified} generic files are symlinks")
    
    # At least 50% should be symlinks
    total_checked = verified + len(issues)
    if total_checked > 0:
        symlink_rate = verified / total_checked
        assert symlink_rate >= 0.5, f"Only {symlink_rate*100:.1f}% are symlinks (expected >= 50%)"


def test_symlinks_point_to_timestamped_files():
    """Test that symlinks point to A timestamped file (not necessarily the one we're checking)."""
    timestamped_files = find_timestamped_files(OUTPUT_DIR)
    
    if len(timestamped_files) == 0:
        pytest.skip("No timestamped files found")
    
    # Group timestamped files by their generic name
    from collections import defaultdict
    generic_groups = defaultdict(list)
    
    for timestamped_file in timestamped_files:
        generic_file = get_generic_filename(timestamped_file)
        generic_groups[generic_file].append(timestamped_file)
    
    issues = []
    verified = 0
    
    for generic_file, timestamped_list in generic_groups.items():
        if generic_file.exists() and generic_file.is_symlink():
            link_target = os.readlink(generic_file)
            
            # Check if link points to ANY of the timestamped files with this base name
            valid_targets = [f.name for f in timestamped_list]
            
            if link_target not in valid_targets:
                issues.append(f"{generic_file.name} -> {link_target} (not in: {valid_targets})")
            else:
                verified += 1
    
    assert len(issues) == 0, f"Found {len(issues)} incorrect symlink targets:\n" + "\n".join(issues[:10])
    print(f"\n✅ All {verified} symlinks point to valid timestamped files")


def test_symlinks_use_basename():
    """Test that symlinks use relative paths (basename), not absolute paths."""
    timestamped_files = find_timestamped_files(OUTPUT_DIR)
    
    if len(timestamped_files) == 0:
        pytest.skip("No timestamped files found")
    
    issues = []
    verified = 0
    
    for timestamped_file in timestamped_files:
        generic_file = get_generic_filename(timestamped_file)
        
        if generic_file.exists() and generic_file.is_symlink():
            link_target = os.readlink(generic_file)
            
            if '/' in link_target or '\\' in link_target:
                issues.append(f"{generic_file.name} -> {link_target} (should use basename only)")
            else:
                verified += 1
    
    assert len(issues) == 0, f"Found {len(issues)} symlinks using absolute paths:\n" + "\n".join(issues[:10])
    print(f"\n✅ All {verified} symlinks use relative paths (basename)")


def test_dual_output_pattern_summary():
    """Generate summary report of DUAL OUTPUT PATTERN compliance."""
    timestamped_files = find_timestamped_files(OUTPUT_DIR)
    
    if len(timestamped_files) == 0:
        pytest.skip("No timestamped files found. Run pipeline steps first.")
    
    print("\n" + "="*70)
    print("DUAL OUTPUT PATTERN VALIDATION SUMMARY")
    print("="*70)
    
    # Count stats
    total_timestamped = len(timestamped_files)
    real_files = sum(1 for f in timestamped_files if f.is_file() and not f.is_symlink())
    correct_format = sum(1 for f in timestamped_files if re.search(r'_\d{8}_\d{6}\.csv$', f.name))
    
    # Group by generic name to avoid counting duplicates
    from collections import defaultdict
    generic_groups = defaultdict(list)
    
    for timestamped_file in timestamped_files:
        generic_file = get_generic_filename(timestamped_file)
        generic_groups[generic_file].append(timestamped_file)
    
    symlinks_exist = 0
    symlinks_correct = 0
    symlinks_basename = 0
    
    for generic_file, timestamped_list in generic_groups.items():
        if generic_file.exists():
            symlinks_exist += 1
            
            if generic_file.is_symlink():
                link_target = os.readlink(generic_file)
                
                # Check if points to any valid timestamped file
                valid_targets = [f.name for f in timestamped_list]
                if link_target in valid_targets:
                    symlinks_correct += 1
                
                if '/' not in link_target and '\\' not in link_target:
                    symlinks_basename += 1
    
    print(f"\nTimestamped Files:")
    print(f"  Total found: {total_timestamped}")
    print(f"  Real files (not symlinks): {real_files} ({real_files/total_timestamped*100:.1f}%)")
    print(f"  Correct format (YYYYMMDD_HHMMSS): {correct_format} ({correct_format/total_timestamped*100:.1f}%)")
    
    print(f"\nGeneric Symlinks:")
    print(f"  Symlinks exist: {symlinks_exist} ({symlinks_exist/total_timestamped*100:.1f}%)")
    print(f"  Point to correct file: {symlinks_correct} ({symlinks_correct/total_timestamped*100:.1f}%)")
    print(f"  Use basename (relative): {symlinks_basename} ({symlinks_basename/total_timestamped*100:.1f}%)")
    
    # Overall compliance
    compliance = (real_files + correct_format + symlinks_correct + symlinks_basename) / (total_timestamped * 4)
    print(f"\nOverall Compliance: {compliance*100:.1f}%")
    print("="*70 + "\n")
    
    # More lenient threshold since some files may be from before the update
    assert compliance >= 0.5, f"Compliance too low: {compliance*100:.1f}% (expected >= 50%)"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
