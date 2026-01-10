#!/usr/bin/env python3
"""
Complete Synthetic Test Runner - ALL STEPS

Runs ALL synthetic tests across the entire pipeline, including the previously
missed steps (2B, 6, 7, 14) that were not in the original test runner.

This provides comprehensive coverage of all synthetic test suites:
- Step 2B: Consolidate Seasonal Data
- Step 6: Cluster Analysis  
- Step 7: Missing Category Rule
- Step 13: Consolidate SPU Rules
- Step 14: Enhanced Fast Fish Format
- Step 17: Augment Fast Fish Recommendations
- Step 29: Supply-Demand Gap Analysis
- Step 31: Gap Analysis Workbook
- Step 32: Store Allocation
- Step 36: Unified Delivery Builder

Author: Data Pipeline Team
Date: 2025-10-02
Version: 2.0 - Complete Coverage of All Synthetic Tests
"""

import sys
import subprocess
import time
from pathlib import Path

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
                # Show summary for passed tests
                lines = result.stdout.strip().split('\n')
                summary_lines = [line for line in lines[-3:] if 'passed' in line or 'failed' in line]
                for line in summary_lines:
                    if line.strip():
                        print(f"📝 {line.strip()}")
            return True
        else:
            print(f"❌ {test_name} FAILED ({execution_time:.2f}s)")
            if result.stderr:
                print(f"📝 Error: {result.stderr.strip()}")
            if result.stdout:
                # Show last few lines for failures
                lines = result.stdout.strip().split('\n')
                for line in lines[-5:]:
                    if line.strip() and ('FAILED' in line or 'ERROR' in line or 'failed' in line):
                        print(f"📝 {line.strip()}")
            return False
            
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"💥 {test_name} CRASHED ({execution_time:.2f}s)")
        print(f"📝 Exception: {str(e)}")
        return False

def run_pytest_suite(test_dir: Path, test_name: str) -> bool:
    """Run a pytest suite and return success status"""
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
    print("🚀 COMPLETE SYNTHETIC TEST SUITE - ALL STEPS")
    print("=" * 80)
    print("Testing ALL synthetic test suites across the entire pipeline")
    print("Includes previously missed steps: 2B, 6, 7, 14")
    print("=" * 80)
    
    # Get the test directory
    test_root = Path(__file__).parent
    
    # Define ALL test modules to run (individual test files)
    test_modules = [
        # Step 2B Tests (previously missed)
        (test_root / "step2b_synthetic" / "test_step2b_synthetic_isolated.py", 
         "Step 2B - Consolidate Seasonal Data"),
        
        # Step 6 Tests (previously missed)
        (test_root / "step6_synthetic" / "test_step6_synthetic_clustering.py", 
         "Step 6 - Cluster Analysis"),
        
        # Step 7 Tests (previously missed)
        (test_root / "step7_synthetic" / "test_step7_synthetic_missing_category.py", 
         "Step 7 - Missing Category Rule"),
        (test_root / "step7_synthetic" / "test_step7_synthetic_fixture_based.py", 
         "Step 7 - Fixture Based Tests"),
        
        # Step 13 Tests (established)
        (test_root / "step13_synthetic" / "test_step13_synthetic_regression.py", 
         "Step 13 - Regression Tests"),
        
        # Step 14 Tests (previously missed)
        (test_root / "step14_synthetic" / "test_step14_synthetic_coverage.py", 
         "Step 14 - Enhanced Fast Fish Format"),
        
        # Step 17 Tests (established)
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
        
        # Step 32 Tests (established)
        (test_root / "step32_synthetic" / "test_step32_synthetic_date_logic_and_allocation.py", 
         "Step 32 - Date Logic & Allocation Tests"),
        
        # Step 36 Tests (established)
        (test_root / "step36_synthetic" / "test_step36_synthetic_unified_delivery.py", 
         "Step 36 - Unified Delivery Tests"),
    ]
    
    # Define ALL pytest test directories
    pytest_dirs = [
        (test_root / "step2b_synthetic", "Step 2B - Pytest Suite"),
        (test_root / "step6_synthetic", "Step 6 - Pytest Suite"),
        (test_root / "step7_synthetic", "Step 7 - Pytest Suite"),
        (test_root / "step13_synthetic", "Step 13 - Complete Pytest Suite"),
        (test_root / "step14_synthetic", "Step 14 - Pytest Suite"),
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
            results.append((test_name, success, "module"))
            if success:
                print(f"🎉 {test_name} completed successfully!")
        else:
            print(f"⚠️ {test_name} - Test file not found: {module_path}")
            results.append((test_name, False, "module"))
    
    # Run pytest suites
    print("\n📋 PHASE 2: Pytest Suite Execution")
    print("=" * 60)
    
    for test_dir, test_name in pytest_dirs:
        if test_dir.exists():
            success = run_pytest_suite(test_dir, test_name)
            results.append((test_name, success, "pytest"))
        else:
            print(f"⚠️ {test_name} - Test directory not found: {test_dir}")
            results.append((test_name, False, "pytest"))
    
    # Summary
    total_execution_time = time.time() - total_start_time
    
    print("\n" + "=" * 80)
    print("🏁 COMPLETE SYNTHETIC TEST SUITE RESULTS")
    print("=" * 80)
    
    # Separate results by type
    module_results = [(name, success) for name, success, test_type in results if test_type == "module"]
    pytest_results = [(name, success) for name, success, test_type in results if test_type == "pytest"]
    
    print("\n📋 Individual Module Results:")
    print("-" * 40)
    for test_name, success in module_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status:<12} {test_name}")
    
    print("\n📋 Pytest Suite Results:")
    print("-" * 40)
    for test_name, success in pytest_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status:<12} {test_name}")
    
    # Overall summary
    total_passed = sum(1 for _, success, _ in results if success)
    total_failed = len(results) - total_passed
    
    print("-" * 80)
    print(f"📊 Summary: {total_passed} passed, {total_failed} failed")
    print(f"⏱️ Total execution time: {total_execution_time:.2f}s")
    
    print(f"\n📈 Test Coverage Summary:")
    print(f"   ✅ Step 2B: Consolidate Seasonal Data")
    print(f"   ✅ Step 6: Cluster Analysis")
    print(f"   ✅ Step 7: Missing Category Rule")
    print(f"   ✅ Step 13: Complete synthetic test suite")
    print(f"   ✅ Step 14: Enhanced Fast Fish Format")
    print(f"   ✅ Step 17: Import/execution synthetic tests")
    print(f"   ✅ Step 29: Duplicate column fix tests")
    print(f"   ✅ Step 31: Duplicate column fix tests")
    print(f"   ✅ Step 32: Date logic synthetic tests")
    print(f"   ✅ Step 36: Unified delivery synthetic tests")
    
    if total_failed == 0:
        print("\n🎉 ALL SYNTHETIC TESTS PASSED!")
        print("✅ Complete synthetic test coverage validated")
        print("✅ All pipeline steps have regression protection")
        return 0
    else:
        print(f"\n💥 {total_failed} TEST(S) FAILED!")
        print("❌ Some synthetic tests have issues")
        print("❌ Please review the failed tests above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
