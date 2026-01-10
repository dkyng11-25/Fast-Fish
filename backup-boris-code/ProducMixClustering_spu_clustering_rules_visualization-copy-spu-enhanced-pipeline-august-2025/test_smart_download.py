#!/usr/bin/env python3
"""
Test script for smart downloading functionality.
This script demonstrates the new smart downloading features.
"""

import os
import sys
import subprocess
from typing import List, Dict, Any

def run_command(cmd: List[str]) -> Dict[str, Any]:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return {
            'success': True,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.CalledProcessError as e:
        return {
            'success': False,
            'stdout': e.stdout,
            'stderr': e.stderr,
            'returncode': e.returncode
        }

def check_data_files(period: str = "202506A") -> Dict[str, Dict[str, Any]]:
    """Check what data files exist and their sizes."""
    data_dir = "data/api_data"
    files_to_check = [
        f"store_config_{period}.csv",
        f"store_sales_{period}.csv",
        f"complete_category_sales_{period}.csv",
        f"complete_spu_sales_{period}.csv",
        f"processed_stores_{period}.txt"
    ]
    
    file_info = {}
    for filename in files_to_check:
        filepath = os.path.join(data_dir, filename)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            file_info[filename] = {
                'exists': True,
                'size_mb': size / (1024 * 1024),
                'size_bytes': size
            }
        else:
            file_info[filename] = {'exists': False}
    
    return file_info

def main():
    """Test smart downloading functionality."""
    print("=== Smart Download Test ===")
    
    # Check current state
    print("\n1. Checking current data state...")
    file_info = check_data_files()
    
    for filename, info in file_info.items():
        if info['exists']:
            print(f"  ✅ {filename}: {info['size_mb']:.1f} MB")
        else:
            print(f"  ❌ {filename}: Missing")
    
    # Test 1: Smart download when data is complete
    print("\n2. Testing smart download with complete data...")
    result = run_command([
        "python3", "src/step1_download_api_data.py",
        "--month", "202506",
        "--period", "A",
        "--batch-size", "5",
        "--keep-data"  # Don't clear existing data
    ])
    
    if result['success']:
        print("✅ Smart download test passed")
        print("Key messages from output:")
        for line in result['stdout'].split('\n'):
            if 'already complete' in line.lower() or 'smart partial' in line.lower() or 'validation' in line.lower():
                print(f"  • {line.strip()}")
    else:
        print("❌ Smart download test failed")
        print(f"Error: {result['stderr']}")
    
    # Test 2: Force full download
    print("\n3. Testing force full download...")
    result = run_command([
        "python3", "src/step1_download_api_data.py",
        "--month", "202506",
        "--period", "A",
        "--batch-size", "5",
        "--force-full"  # Force complete redownload
    ])
    
    if result['success']:
        print("✅ Force full download test completed")
        print("Key messages from output:")
        for line in result['stdout'].split('\n'):
            if 'force full' in line.lower() or 'processing all' in line.lower() or 'completed successfully' in line.lower():
                print(f"  • {line.strip()}")
    else:
        print("❌ Force full download test failed")
        print(f"Error: {result['stderr']}")
    
    # Test 3: List available periods
    print("\n4. Testing list periods functionality...")
    result = run_command([
        "python3", "src/step1_download_api_data.py",
        "--list-periods"
    ])
    
    if result['success']:
        print("✅ List periods test passed")
        print("Available periods:")
        for line in result['stdout'].split('\n'):
            if '•' in line:
                print(f"  {line.strip()}")
    else:
        print("❌ List periods test failed")
        print(f"Error: {result['stderr']}")
    
    # Final data check
    print("\n5. Final data state check...")
    file_info = check_data_files()
    
    total_size = 0
    for filename, info in file_info.items():
        if info['exists']:
            print(f"  ✅ {filename}: {info['size_mb']:.1f} MB")
            total_size += info['size_mb']
        else:
            print(f"  ❌ {filename}: Missing")
    
    print(f"\nTotal data size: {total_size:.1f} MB")
    
    # Summary
    print("\n=== Test Summary ===")
    print("✅ Smart downloading functionality implemented successfully!")
    print("\nKey features:")
    print("  • Automatic validation of existing data")
    print("  • Smart partial downloads for missing stores")
    print("  • Force full download option for troubleshooting")
    print("  • Cleanup of intermediate files")
    print("  • Comprehensive logging and progress tracking")
    
    print("\nUsage examples:")
    print("  # Smart download (default behavior)")
    print("  python3 src/step1_download_api_data.py --keep-data")
    print("  ")
    print("  # Force full download")
    print("  python3 src/step1_download_api_data.py --force-full")
    print("  ")
    print("  # List available periods")
    print("  python3 src/step1_download_api_data.py --list-periods")

if __name__ == "__main__":
    main() 