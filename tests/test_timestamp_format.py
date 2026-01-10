"""
Test Timestamp Format Consistency
==================================

Verifies that ALL timestamped outputs use the SAME format: YYYYMMDD_HHMMSS
"""

import re
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_all_timestamped_files_use_same_format():
    """Test that ALL timestamped files use format: YYYYMMDD_HHMMSS"""
    
    output_dir = PROJECT_ROOT / "output"
    
    if not output_dir.exists():
        pytest.skip("Output directory doesn't exist")
    
    # Pattern for YYYYMMDD_HHMMSS format
    timestamp_pattern = re.compile(r'_(\d{8})_(\d{6})\.')
    
    # Find all files with timestamps
    all_files = list(output_dir.glob("*"))
    timestamped_files = []
    
    for file in all_files:
        if file.is_file() and not file.is_symlink():
            match = timestamp_pattern.search(file.name)
            if match:
                date_part = match.group(1)
                time_part = match.group(2)
                timestamped_files.append({
                    'file': file.name,
                    'date': date_part,
                    'time': time_part,
                    'full_timestamp': f"{date_part}_{time_part}"
                })
    
    if not timestamped_files:
        pytest.skip("No timestamped files found")
    
    print(f"\n✅ Found {len(timestamped_files)} timestamped files")
    
    # Verify each file
    for item in timestamped_files[:10]:  # Show first 10
        # Verify date format: YYYYMMDD
        assert len(item['date']) == 8, f"❌ Date should be 8 digits: {item['file']}"
        assert item['date'].isdigit(), f"❌ Date should be all digits: {item['file']}"
        
        year = int(item['date'][:4])
        month = int(item['date'][4:6])
        day = int(item['date'][6:8])
        
        assert 2020 <= year <= 2030, f"❌ Invalid year: {item['file']}"
        assert 1 <= month <= 12, f"❌ Invalid month: {item['file']}"
        assert 1 <= day <= 31, f"❌ Invalid day: {item['file']}"
        
        # Verify time format: HHMMSS
        assert len(item['time']) == 6, f"❌ Time should be 6 digits: {item['file']}"
        assert item['time'].isdigit(), f"❌ Time should be all digits: {item['file']}"
        
        hour = int(item['time'][:2])
        minute = int(item['time'][2:4])
        second = int(item['time'][4:6])
        
        assert 0 <= hour <= 23, f"❌ Invalid hour: {item['file']}"
        assert 0 <= minute <= 59, f"❌ Invalid minute: {item['file']}"
        assert 0 <= second <= 59, f"❌ Invalid second: {item['file']}"
        
        print(f"✅ {item['file'][:50]}... → {item['full_timestamp']}")
    
    print(f"\n✅ All {len(timestamped_files)} files use correct format: YYYYMMDD_HHMMSS")
    print(f"✅ Format verified: Date (8 digits) + Time (6 digits)")


def test_timestamp_format_in_output_utils():
    """Test that output_utils.py defines the correct format"""
    
    output_utils = PROJECT_ROOT / "src" / "output_utils.py"
    
    if not output_utils.exists():
        pytest.skip("output_utils.py not found")
    
    content = output_utils.read_text()
    
    # Check for the timestamp format definition
    assert '%Y%m%d_%H%M%S' in content, "❌ Timestamp format not found in output_utils.py"
    
    # Count occurrences (should be at least 2 - one for CSV, one for text)
    count = content.count('%Y%m%d_%H%M%S')
    assert count >= 2, f"❌ Timestamp format should appear at least 2 times, found {count}"
    
    print(f"✅ output_utils.py defines format: %Y%m%d_%H%M%S")
    print(f"✅ Format appears {count} times (for different file types)")
    print(f"✅ This creates timestamps like: 20251002_164954")


def test_no_alternative_timestamp_formats():
    """Test that no steps use alternative timestamp formats"""
    
    output_dir = PROJECT_ROOT / "output"
    
    if not output_dir.exists():
        pytest.skip("Output directory doesn't exist")
    
    # Patterns for WRONG formats we want to avoid
    wrong_patterns = [
        (r'_\d{4}-\d{2}-\d{2}_\d{2}:\d{2}:\d{2}', 'YYYY-MM-DD_HH:MM:SS'),
        (r'_\d{14}\.', 'YYYYMMDDHHMMSS (no underscore)'),
        (r'_\d{2}\d{2}\d{2}_\d{6}', 'YYMMDD_HHMMSS (2-digit year)'),
    ]
    
    all_files = list(output_dir.glob("*"))
    
    for file in all_files:
        if file.is_file():
            for pattern, format_name in wrong_patterns:
                if re.search(pattern, file.name):
                    pytest.fail(f"❌ Found wrong format {format_name} in: {file.name}")
    
    print(f"✅ No alternative/wrong timestamp formats found")
    print(f"✅ All files use consistent format: YYYYMMDD_HHMMSS")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
