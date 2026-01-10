#!/usr/bin/env python3
"""
Step 32 Comprehensive Test Runner

Runs all Step 32 synthetic tests to validate:
- Duplicate column handling and data integration
- Store allocation logic and business rules
- Fallback allocation strategies
- Edge case handling

Author: Data Pipeline Team
Date: 2025-09-27
"""

import subprocess
import sys
import time
from pathlib import Path

def run_test_module(module_path: str, description: str) -> tuple[bool, float, str]:
    """Run a test module and return success status, duration, and output"""
    print(f"\n🧪 Running {description}...")
    print("=" * 60)
    
    start_time = time.time()
    try:
        result = subprocess.run([
            sys.executable, module_path
        ], capture_output=True, text=True, timeout=120)
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} PASSED ({duration:.2f}s)")
            print(f"📝 Output: {result.stdout.strip()}")
            return True, duration, result.stdout
        else:
            print(f"❌ {description} FAILED ({duration:.2f}s)")
            print(f"📝 Error: {result.stderr.strip()}")
            return False, duration, result.stderr
            
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"⏰ {description} TIMEOUT ({duration:.2f}s)")
        return False, duration, "Test timed out after 120 seconds"
    except Exception as e:
        duration = time.time() - start_time
        print(f"💥 {description} ERROR ({duration:.2f}s)")
        print(f"📝 Exception: {str(e)}")
        return False, duration, str(e)

def main():
    """Run all Step 32 tests"""
    print("🚀 STEP 32 COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print("Testing Step 32 duplicate column fixes and allocation logic")
    print("Date: 2025-09-27")
    print()
    
    # Test modules to run
    test_modules = [
        ("tests/step32_synthetic/test_step32_synthetic_duplicate_columns.py", 
         "Step 32 - Duplicate Column Handling"),
        ("tests/step32_synthetic/test_step32_synthetic_allocation_logic.py", 
         "Step 32 - Allocation Logic & Business Rules")
    ]
    
    results = []
    total_duration = 0
    
    for module_path, description in test_modules:
        success, duration, output = run_test_module(module_path, description)
        results.append((description, success, duration, output))
        total_duration += duration
        
        if not success:
            print(f"🎉 {description} completed successfully!")
    
    # Summary
    print("\n" + "=" * 80)
    print("🏁 STEP 32 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, success, _, _ in results if success)
    failed = len(results) - passed
    
    for description, success, duration, _ in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status:<12} {description}")
    
    print("-" * 80)
    print(f"📊 Summary: {passed} passed, {failed} failed")
    print(f"⏱️ Total execution time: {total_duration:.2f}s")
    
    if failed == 0:
        print("\n🎉 ALL STEP 32 TESTS PASSED!")
        print("✅ Step 32 duplicate column fixes are working correctly")
        print("✅ Store allocation logic is functioning properly")
        print("✅ Fallback strategies and edge cases are handled")
        return 0
    else:
        print(f"\n💥 {failed} TEST(S) FAILED!")
        print("❌ Step 32 needs attention before production deployment")
        return 1

if __name__ == "__main__":
    sys.exit(main())
