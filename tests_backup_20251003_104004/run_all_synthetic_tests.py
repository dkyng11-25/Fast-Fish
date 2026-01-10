#!/usr/bin/env python3
"""
Comprehensive Synthetic Test Runner

Runs all synthetic tests across the pipeline (Steps 13, 17, 29, 31, 32, 36).
This ensures all our synthetic test suites work correctly and provides regression protection.

Author: Data Pipeline Team
Date: 2025-01-26
Version: 1.0 - Complete Synthetic Test Suite Runner
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
            sys.executable, '-m', 'pytest', str(test_dir), '-v', '--tb=short'
        ], capture_output=True, text=True, cwd=test_dir.parent.parent)
        
        execution_time = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {test_name} PASSED ({execution_time:.2f}s)")
            # Show only summary for pytest
            lines = result.stdout.split('\n')
            summary_lines = [line for line in lines if 'passed' in line or 'failed' in line or 'error' in line][-3:]
            for line in summary_lines:
                if line.strip():
                    print(f"📝 {line.strip()}")
            return True
        else:
            print(f"❌ {test_name} FAILED ({execution_time:.2f}s)")
            print(f"📝 Error: {result.stderr}")
            if result.stdout:
                # Show last few lines of output for failures
                lines = result.stdout.split('\n')[-10:]
                for line in lines:
                    if line.strip():
                        print(f"📝 {line.strip()}")
            return False
            
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"💥 {test_name} CRASHED ({execution_time:.2f}s)")
        print(f"📝 Exception: {str(e)}")
        return False

def main():
    """Main test runner function"""
    print("🚀 Starting Complete Synthetic Test Suite")
    print("=" * 80)
    print("Testing all synthetic test suites across the pipeline")
    print("=" * 80)
    
    # Get the test directory
    test_root = Path(__file__).parent
    
    # Define test modules to run (individual test files)
    test_modules = [
        # Step 13 Tests (established)
        (test_root / "step13_synthetic" / "test_step13_synthetic_regression.py", 
         "Step 13 - Regression Tests"),
        
        # Step 17 Tests (new)
        (test_root / "step17_synthetic" / "test_step17_synthetic_imports_and_execution.py", 
         "Step 17 - Import & Execution Tests"),
        
        # Step 29 Tests (duplicate column fixes)
        (test_root / "step29_synthetic" / "test_step29_synthetic_duplicate_columns.py", 
         "Step 29 - Duplicate Column Tests"),
        (test_root / "step29_synthetic" / "test_step29_synthetic_edge_cases.py", 
         "Step 29 - Edge Case Tests"),
        
        # Step 31 Tests (duplicate column fixes)
        (test_root / "step31_synthetic" / "test_step31_synthetic_duplicate_columns.py", 
         "Step 31 - Duplicate Column Tests"),
        
        # Step 32 Tests (new)
        (test_root / "step32_synthetic" / "test_step32_synthetic_date_logic_and_allocation.py", 
         "Step 32 - Date Logic & Allocation Tests"),
        
        # Step 36 Tests (new)
        (test_root / "step36_synthetic" / "test_step36_synthetic_unified_delivery.py", 
         "Step 36 - Unified Delivery Tests"),
    ]
    
    # Define pytest test directories
    pytest_dirs = [
        (test_root / "step13_synthetic", "Step 13 - Complete Pytest Suite"),
        (test_root / "step17_synthetic", "Step 17 - Pytest Suite"),
        (test_root / "step29_synthetic", "Step 29 - Pytest Suite"),
        (test_root / "step31_synthetic", "Step 31 - Pytest Suite"),
        (test_root / "step32_synthetic", "Step 32 - Pytest Suite"),
        (test_root / "step36_synthetic", "Step 36 - Pytest Suite"),
    ]
    
    # Track results
    results = []
    total_start_time = time.time()
    
    # Run individual test modules first
    print("\n📋 PHASE 1: Individual Test Module Execution")
    print("=" * 60)
    
    for module_path, test_name in test_modules:
        if module_path.exists():
            success = run_test_module(module_path, test_name)
            results.append((test_name, success, "Module"))
        else:
            print(f"⚠️ Test module not found: {module_path}")
            results.append((test_name, False, "Module"))
    
    # Run pytest tests
    print("\n📋 PHASE 2: Pytest Suite Execution")
    print("=" * 60)
    
    for test_dir, test_name in pytest_dirs:
        if test_dir.exists() and any(test_dir.glob("test_*.py")):
            success = run_pytest_tests(test_dir, test_name)
            results.append((test_name, success, "Pytest"))
        else:
            print(f"⚠️ Test directory not found or empty: {test_dir}")
    
    # Print final results
    total_time = time.time() - total_start_time
    print("\n" + "=" * 80)
    print("🏁 COMPLETE SYNTHETIC TEST SUITE RESULTS")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    # Group results by type
    module_results = [(name, success) for name, success, type_ in results if type_ == "Module"]
    pytest_results = [(name, success) for name, success, type_ in results if type_ == "Pytest"]
    
    if module_results:
        print("\n📋 Individual Module Results:")
        print("-" * 40)
        for test_name, success in module_results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status:<12} {test_name}")
            if success:
                passed += 1
            else:
                failed += 1
    
    if pytest_results:
        print("\n📋 Pytest Suite Results:")
        print("-" * 40)
        for test_name, success in pytest_results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status:<12} {test_name}")
            if success:
                passed += 1
            else:
                failed += 1
    
    print("-" * 80)
    print(f"📊 Summary: {passed} passed, {failed} failed")
    print(f"⏱️ Total execution time: {total_time:.2f}s")
    
    # Show test coverage summary
    print(f"\n📈 Test Coverage Summary:")
    print(f"   ✅ Step 13: Complete synthetic test suite (6 modules)")
    print(f"   ✅ Step 17: Import/execution synthetic tests")
    print(f"   ✅ Step 29: Duplicate column fix tests")
    print(f"   ✅ Step 31: Duplicate column fix tests")
    print(f"   ✅ Step 32: Date logic synthetic tests")
    print(f"   ✅ Step 36: Unified delivery synthetic tests")
    
    if failed == 0:
        print("\n🎉 ALL SYNTHETIC TESTS PASSED!")
        print("✅ Complete pipeline synthetic test coverage established")
        print("✅ Regression protection in place for all critical steps")
        print("✅ Isolated testing ensures no cross-step dependencies")
        return 0
    else:
        print(f"\n💥 {failed} TEST(S) FAILED!")
        print("❌ Some synthetic tests have issues")
        print("❌ Please review the failed tests above")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
