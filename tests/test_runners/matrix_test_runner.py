"""
Test runner for Step 3 matrix preparation testing.

This module provides a comprehensive test runner for matrix preparation functionality.
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
import time

class MatrixTestRunner:
    """Test runner for matrix preparation functionality."""
    
    def __init__(self, test_data_dir: str = "tests/test_data"):
        self.test_data_dir = test_data_dir
        self.results = {}
        
    def setup_test_environment(self) -> bool:
        """
        Set up test environment with sample data.
        
        Returns:
            True if setup successful
        """
        try:
            # Generate test data if needed
            from tests.data_generators.matrix_test_data import save_test_data
            save_test_data(self.test_data_dir)
            
            print(f"✅ Test environment set up in {self.test_data_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to set up test environment: {e}")
            return False
    
    def run_matrix_preparation_test(self) -> Dict[str, any]:
        """
        Run matrix preparation with test data.
        
        Returns:
            Test results dictionary
        """
        start_time = time.time()
        
        try:
            # Run the matrix preparation step
            result = subprocess.run([
                sys.executable, "src/test_refactored_step3.py"
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
            
            execution_time = time.time() - start_time
            
            return {
                'success': result.returncode == 0,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'execution_time': execution_time
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Test timed out after 5 minutes',
                'execution_time': time.time() - start_time
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def validate_outputs(self) -> Dict[str, any]:
        """
        Validate the generated matrix outputs.
        
        Returns:
            Validation results
        """
        try:
            from tests.utils.matrix_validation import validate_matrix_preparation_output
            return validate_matrix_preparation_output()
            
        except Exception as e:
            return {
                'overall': {'valid': False, 'errors': 1, 'warnings': 0},
                'error': f'Validation failed: {str(e)}'
            }
    
    def run_comprehensive_test(self) -> Dict[str, any]:
        """
        Run comprehensive matrix preparation test.
        
        Returns:
            Complete test results
        """
        print("🧪 Running comprehensive matrix preparation test...")
        
        # Setup test environment
        setup_success = self.setup_test_environment()
        if not setup_success:
            return {'overall_success': False, 'error': 'Test environment setup failed'}
        
        # Run matrix preparation
        print("🔄 Running matrix preparation...")
        test_result = self.run_matrix_preparation_test()
        
        if not test_result['success']:
            return {
                'overall_success': False,
                'error': test_result.get('error', 'Matrix preparation failed'),
                'details': test_result
            }
        
        # Validate outputs
        print("✅ Validating outputs...")
        validation_result = self.validate_outputs()
        
        # Compile final results
        overall_success = (
            test_result['success'] and 
            validation_result.get('overall', {}).get('valid', False)
        )
        
        return {
            'overall_success': overall_success,
            'execution_time': test_result['execution_time'],
            'test_result': test_result,
            'validation_result': validation_result
        }
    
    def cleanup_test_data(self) -> None:
        """Clean up test-generated data files."""
        test_files = [
            'data/store_subcategory_matrix.csv',
            'data/normalized_subcategory_matrix.csv',
            'data/store_spu_limited_matrix.csv',
            'data/normalized_spu_limited_matrix.csv',
            'data/store_category_agg_matrix.csv',
            'data/normalized_category_agg_matrix.csv'
        ]
        
        for file_path in test_files:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️ Cleaned up: {file_path}")

def run_matrix_tests() -> Dict[str, any]:
    """
    Convenience function to run all matrix tests.
    
    Returns:
        Test results
    """
    runner = MatrixTestRunner()
    return runner.run_comprehensive_test()

if __name__ == "__main__":
    results = run_matrix_tests()
    
    print("\n" + "="*60)
    print("MATRIX PREPARATION TEST RESULTS")
    print("="*60)
    
    if results['overall_success']:
        print("✅ ALL TESTS PASSED")
        print(f"   Execution time: {results['execution_time']:.2f} seconds")
        
        # Show validation details
        validation = results['validation_result']
        print(f"   Validation errors: {validation['overall']['errors']}")
        print(f"   Validation warnings: {validation['overall']['warnings']}")
        
    else:
        print("❌ TESTS FAILED")
        print(f"   Error: {results.get('error', 'Unknown error')}")
        
        if 'test_result' in results:
            test_result = results['test_result']
            if 'stderr' in test_result and test_result['stderr']:
                print(f"   stderr: {test_result['stderr'][:500]}...")
    
    print("="*60)
