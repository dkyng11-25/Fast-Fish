#!/usr/bin/env python3
"""
Comprehensive Test Runner for Duplicate Column Fixes

Runs all synthetic tests for Steps 29 and 31 duplicate column handling.
This ensures our fixes work correctly and prevents regression.

Author: Data Pipeline Team
Date: 2025-01-26
Version: 1.0 - Duplicate Column Test Suite
"""

import sys
import subprocess
import time
from pathlib import Path
import tempfile

def run_test_module(module_path: Path, test_name: str) -> bool:
    """Run a specific test module and return success status"""
    print(f"\n🧪 Running {test_name}...")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Run the test module
        result = subprocess.run([
            sys.executable, str(module_path)
        ], capture_output=True, text=True, cwd=module_path.parent.parent.parent)
        
        execution_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {test_name} PASSED ({execution_time:.2f}s)")
            if result.stdout:
                print(f"📝 Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {test_name} FAILED ({execution_time:.2f}s)")
            print(f"📝 Error: {result.stderr}")
            if result.stdout:
                print(f"📝 Output: {result.stdout}")
            return False
            
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"💥 {test_name} CRASHED ({execution_time:.2f}s)")
        print(f"📝 Exception: {str(e)}")
        return False

def run_pytest_tests(test_dir: Path, test_name: str) -> bool:
    """Run pytest tests in a directory"""
    print(f"\n🧪 Running {test_name} with pytest...")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', str(test_dir), '-v'
        ], capture_output=True, text=True, cwd=test_dir.parent.parent)
        
        execution_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {test_name} PASSED ({execution_time:.2f}s)")
            print(f"📝 Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {test_name} FAILED ({execution_time:.2f}s)")
            print(f"📝 Error: {result.stderr}")
            if result.stdout:
                print(f"📝 Output: {result.stdout}")
            return False
            
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"💥 {test_name} CRASHED ({execution_time:.2f}s)")
        print(f"📝 Exception: {str(e)}")
        return False

def main():
    """Main test runner function"""
    print("🚀 Starting Duplicate Column Fix Test Suite")
    print("=" * 80)
    print("Testing Steps 29 and 31 duplicate column detection and removal fixes")
    print("=" * 80)
    
    # Get the test directory
    test_root = Path(__file__).parent
    
    # Define test modules to run
    test_modules = [
        # Step 29 Tests
        (test_root / "step29_synthetic" / "test_step29_synthetic_duplicate_columns.py", 
         "Step 29 - Duplicate Column Detection"),
        (test_root / "step29_synthetic" / "test_step29_synthetic_edge_cases.py", 
         "Step 29 - Edge Cases"),
        
        # Step 31 Tests
        (test_root / "step31_synthetic" / "test_step31_synthetic_duplicate_columns.py", 
         "Step 31 - Duplicate Column Detection"),
    ]
    
    # Track results
    results = []
    total_start_time = time.time()
    
    # Run individual test modules
    for module_path, test_name in test_modules:
        if module_path.exists():
            success = run_test_module(module_path, test_name)
            results.append((test_name, success))
        else:
            print(f"⚠️ Test module not found: {module_path}")
            results.append((test_name, False))
    
    # Run pytest tests if available
    step29_dir = test_root / "step29_synthetic"
    step31_dir = test_root / "step31_synthetic"
    
    if step29_dir.exists():
        success = run_pytest_tests(step29_dir, "Step 29 - Pytest Suite")
        results.append(("Step 29 - Pytest Suite", success))
    
    if step31_dir.exists():
        success = run_pytest_tests(step31_dir, "Step 31 - Pytest Suite")
        results.append(("Step 31 - Pytest Suite", success))
    
    # Print final results
    total_time = time.time() - total_start_time
    print("\n" + "=" * 80)
    print("🏁 DUPLICATE COLUMN FIX TEST RESULTS")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status:<12} {test_name}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print("-" * 80)
    print(f"📊 Summary: {passed} passed, {failed} failed")
    print(f"⏱️ Total execution time: {total_time:.2f}s")
    
    if failed == 0:
        print("\n🎉 ALL DUPLICATE COLUMN TESTS PASSED!")
        print("✅ Steps 29 and 31 duplicate column fixes are working correctly")
        print("✅ Regression protection is in place")
        return 0
    else:
        print(f"\n💥 {failed} TEST(S) FAILED!")
        print("❌ Duplicate column fixes may have issues")
        print("❌ Please review the failed tests above")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
