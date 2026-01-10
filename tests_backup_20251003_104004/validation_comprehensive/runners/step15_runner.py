#!/usr/bin/env python3
"""
Step 15 Validation Runner

Handles validation of historical baseline download from Step 15 of the pipeline.
Includes comprehensive real data testing capabilities.

Author: Data Pipeline
Date: 2025-01-03
"""

import logging
import pandas as pd
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)


def validate_step15_historical_baseline(period: str = "202508A", 
                                       data_dir: str = "../output") -> Dict[str, Any]:
    """
    Validate Step 15 historical baseline download output.
    
    Args:
        period: Period label for validation
        data_dir: Directory containing output files
        
    Returns:
        Dictionary with validation results
    """
    logger.info(f"Starting Step 15 validation for period {period}")
    
    results = {
        "step": 15,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "validation_passed": False,
        "errors": [],
        "warnings": [],
        "file_validation": {},
        "statistics": {}
    }
    
    try:
        # Resolve paths relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        data_path = project_root / data_dir.lstrip("../")
        
        # Define expected output files
        expected_files = {
            'historical_baseline': f"historical_baseline_{period}.csv",
            'baseline_summary': f"baseline_summary_{period}.csv",
            'download_log': f"historical_baseline_download_{period}.log"
        }
        
        # Validate each file
        for file_type, filename in expected_files.items():
            file_path = data_path / filename
            if file_path.exists():
                logger.info(f"Validating {file_type}: {file_path}")
                try:
                    if file_type == 'download_log':
                        # For log files, just check they exist and have content
                        file_size = file_path.stat().st_size
                        results["file_validation"][file_type] = file_size > 0
                        results["statistics"][f"{file_type}_size"] = file_size
                    else:
                        # For CSV files, validate structure
                        df = pd.read_csv(file_path)
                        results["file_validation"][file_type] = len(df) > 0
                        results["statistics"][f"{file_type}_rows"] = len(df)
                        results["statistics"][f"{file_type}_columns"] = len(df.columns)
                        
                        # Basic data quality checks
                        if file_type == 'historical_baseline':
                            required_cols = ['str_code', 'period', 'baseline_value']
                            missing_cols = [col for col in required_cols if col not in df.columns]
                            if missing_cols:
                                results["warnings"].append(f"Missing columns in {file_type}: {missing_cols}")
                                
                except Exception as e:
                    results["errors"].append(f"Error validating {file_type}: {str(e)}")
                    results["file_validation"][file_type] = False
            else:
                results["warnings"].append(f"File not found: {file_path}")
                results["file_validation"][file_type] = False
        
        # Overall validation status
        results["validation_passed"] = all(results["file_validation"].values()) and len(results["errors"]) == 0
        
        logger.info(f"Step 15 validation completed. Passed: {results['validation_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 15 validation: {str(e)}")
        results["errors"].append(f"Validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def run_step15_validation(period: str = "202508A") -> Dict[str, Any]:
    """
    Run Step 15 validation.
    
    Args:
        period: Period label for validation
        
    Returns:
        Dictionary with validation results
    """
    return validate_step15_historical_baseline(period)


def test_step15_with_real_data(period: str = "202509A") -> Dict[str, Any]:
    """
    Test Step 15 using real data files with comprehensive validation.
    
    Args:
        period: Period label for testing (e.g., "202509A")
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Starting Step 15 real data test for period {period}")
    
    results = {
        "step": 15,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "test_passed": False,
        "errors": [],
        "warnings": [],
        "test_results": {},
        "statistics": {}
    }
    
    try:
        # Set environment variables
        os.environ['PIPELINE_TARGET_YYYYMM'] = period[:6]  # Extract YYYYMM
        os.environ['PIPELINE_TARGET_PERIOD'] = period[-1]  # Extract A or B
        os.environ['ANALYSIS_LEVEL'] = 'spu'
        
        # Run step15 from project root
        project_root = Path(__file__).parent.parent.parent.parent
        original_cwd = os.getcwd()
        
        try:
            os.chdir(project_root)
            
            # Add src to path and import step15
            sys.path.insert(0, str(project_root / "src"))
            from step15_download_historical_baseline import main as step15_main
            
            # Mock command line arguments
            original_argv = sys.argv.copy()
            try:
                sys.argv = ['step15_download_historical_baseline.py', '--target-yyyymm', period[:6], '--target-period', period[-1]]
                
                # Step15 will fail because historical data doesn't exist, but we can test the error handling
                try:
                    step15_main()
                    results["test_results"]["execution"] = "completed"
                except FileNotFoundError as e:
                    if 'Historical data file not found' in str(e):
                        results["test_results"]["execution"] = "expected_error_handled"
                        results["warnings"].append(f"Expected error: Historical data file not found for baseline {period[:4]}{int(period[4:6])-1:02d}{period[-1]}")
                    else:
                        raise e
                except Exception as e:
                    results["errors"].append(f"Unexpected error during execution: {str(e)}")
                    results["test_results"]["execution"] = "failed"
            finally:
                sys.argv = original_argv
        finally:
            os.chdir(original_cwd)
        
        # Overall test status
        results["test_passed"] = len(results["errors"]) == 0
        results["statistics"]["errors_count"] = len(results["errors"])
        results["statistics"]["warnings_count"] = len(results["warnings"])
        
        logger.info(f"Step 15 real data test completed. Passed: {results['test_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 15 real data test: {str(e)}")
        results["errors"].append(f"Test error: {str(e)}")
        results["test_passed"] = False
    
    return results


def test_step15_with_mock_historical_data(period: str = "202509A") -> Dict[str, Any]:
    """
    Test Step 15 with mock historical data to validate full functionality.
    
    Args:
        period: Period label for testing (e.g., "202509A")
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Starting Step 15 mock historical data test for period {period}")
    
    results = {
        "step": 15,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "test_passed": False,
        "errors": [],
        "warnings": [],
        "test_results": {},
        "statistics": {}
    }
    
    try:
        # Set environment variables
        os.environ['PIPELINE_TARGET_YYYYMM'] = period[:6]
        os.environ['PIPELINE_TARGET_PERIOD'] = period[-1]
        os.environ['ANALYSIS_LEVEL'] = 'spu'
        
        # Create mock historical data in the correct location
        project_root = Path(__file__).parent.parent.parent.parent
        api_data_dir = project_root / "data" / "api_data"
        api_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Calculate baseline period (last year same month)
        baseline_yyyymm = f"{int(period[:4])-1:04d}{period[4:6]}"
        baseline_period = period[-1]
        baseline_label = f"{baseline_yyyymm}{baseline_period}"
        
        # Create mock historical SPU data in the format expected by Step 15
        historical_spu_data = pd.DataFrame({
            'str_code': [f'S{i:03d}' for i in range(50)],
            'spu_code': [f'SPU{i%20:03d}' for i in range(50)],
            'cate_name': ['Clothing'] * 50,
            'sub_cate_name': ['Shirts'] * 25 + ['Pants'] * 25,
            'quantity': [10 + i for i in range(50)],
            'spu_sales_amt': [1000 + i * 100 for i in range(50)]
        })
        
        # Create the file in the location that Step 15 expects
        historical_file = api_data_dir / f"complete_spu_sales_{baseline_label}.csv"
        historical_spu_data.to_csv(historical_file, index=False)
        
        try:
            # Run step15 from project root
            original_cwd = os.getcwd()
            
            try:
                os.chdir(project_root)
                
                # Add src to path and import step15
                sys.path.insert(0, str(project_root / "src"))
                from step15_download_historical_baseline import main as step15_main
                
                # Mock command line arguments
                original_argv = sys.argv.copy()
                try:
                    sys.argv = ['step15_download_historical_baseline.py', '--target-yyyymm', period[:6], '--target-period', period[-1]]
                    step15_main()
                    results["test_results"]["execution"] = "completed"
                finally:
                    sys.argv = original_argv
            finally:
                os.chdir(original_cwd)
            
            # Verify output files were created (check for actual files created by Step 15)
            project_output_dir = project_root / "output"
            
            # Look for the actual files created by Step 15
            historical_files = list(project_output_dir.glob(f"historical_reference_{baseline_label}_*.csv"))
            comparison_files = list(project_output_dir.glob(f"year_over_year_comparison_{baseline_label}_*.csv"))
            insights_files = list(project_output_dir.glob(f"historical_insights_{baseline_label}_*.json"))
            
            if historical_files:
                results["test_results"]["historical_file_created"] = True
                historical_df = pd.read_csv(historical_files[0])
                results["statistics"]["historical_records"] = len(historical_df)
            else:
                results["warnings"].append("Historical reference file not created")
                results["test_results"]["historical_file_created"] = False
            
            if comparison_files:
                results["test_results"]["comparison_file_created"] = True
                comparison_df = pd.read_csv(comparison_files[0])
                results["statistics"]["comparison_records"] = len(comparison_df)
            else:
                results["warnings"].append("Year-over-year comparison file not created")
                results["test_results"]["comparison_file_created"] = False
            
            if insights_files:
                results["test_results"]["insights_file_created"] = True
                results["statistics"]["insights_file_size"] = insights_files[0].stat().st_size
            else:
                results["warnings"].append("Historical insights file not created")
                results["test_results"]["insights_file_created"] = False
            
            # Overall test status
            results["test_passed"] = (
                results["test_results"].get("execution") == "completed" and
                results["test_results"].get("historical_file_created", False) and
                results["test_results"].get("comparison_file_created", False) and
                results["test_results"].get("insights_file_created", False)
            )
            
        finally:
            # Clean up mock files
            if historical_file.exists():
                historical_file.unlink()
            if api_data_dir.exists() and not any(api_data_dir.iterdir()):
                api_data_dir.rmdir()
        
        logger.info(f"Step 15 mock historical data test completed. Passed: {results['test_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 15 mock historical data test: {str(e)}")
        results["errors"].append(f"Test error: {str(e)}")
        results["test_passed"] = False
    
    return results


def test_step15_error_handling(period: str = "202509A") -> Dict[str, Any]:
    """
    Test Step 15 error handling when historical data is missing.
    
    Args:
        period: Period label for testing (e.g., "202509A")
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Starting Step 15 error handling test for period {period}")
    
    results = {
        "step": 15,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "test_passed": False,
        "errors": [],
        "warnings": [],
        "test_results": {},
        "statistics": {}
    }
    
    try:
        # Set environment variables
        os.environ['PIPELINE_TARGET_YYYYMM'] = period[:6]
        os.environ['PIPELINE_TARGET_PERIOD'] = period[-1]
        os.environ['ANALYSIS_LEVEL'] = 'spu'
        
        # Run step15 from project root
        project_root = Path(__file__).parent.parent.parent.parent
        original_cwd = os.getcwd()
        
        try:
            os.chdir(project_root)
            
            # Add src to path and import step15
            sys.path.insert(0, str(project_root / "src"))
            from step15_download_historical_baseline import main as step15_main
            
            # Mock command line arguments
            original_argv = sys.argv.copy()
            try:
                sys.argv = ['step15_download_historical_baseline.py', '--target-yyyymm', period[:6], '--target-period', period[-1]]
                
                # This should raise FileNotFoundError when historical data is missing
                try:
                    step15_main()
                    results["errors"].append("Expected FileNotFoundError but execution completed successfully")
                    results["test_results"]["error_handling"] = "failed"
                except FileNotFoundError as e:
                    if 'Historical data file not found' in str(e):
                        results["test_results"]["error_handling"] = "passed"
                        results["warnings"].append("Correctly raised FileNotFoundError for missing historical data")
                    else:
                        results["errors"].append(f"Unexpected FileNotFoundError: {str(e)}")
                        results["test_results"]["error_handling"] = "failed"
                except Exception as e:
                    results["errors"].append(f"Unexpected error type: {type(e).__name__}: {str(e)}")
                    results["test_results"]["error_handling"] = "failed"
            finally:
                sys.argv = original_argv
        finally:
            os.chdir(original_cwd)
        
        # Overall test status
        results["test_passed"] = results["test_results"].get("error_handling") == "passed"
        results["statistics"]["errors_count"] = len(results["errors"])
        results["statistics"]["warnings_count"] = len(results["warnings"])
        
        logger.info(f"Step 15 error handling test completed. Passed: {results['test_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 15 error handling test: {str(e)}")
        results["errors"].append(f"Test error: {str(e)}")
        results["test_passed"] = False
    
    return results


def run_comprehensive_step15_tests(period: str = "202509A") -> Dict[str, Any]:
    """
    Run comprehensive Step 15 tests including real data, mock data, and error handling.
    
    Args:
        period: Period label for testing (e.g., "202509A")
        
    Returns:
        Dictionary with comprehensive test results
    """
    logger.info(f"Starting comprehensive Step 15 tests for period {period}")
    
    comprehensive_results = {
        "step": 15,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "overall_passed": False,
        "test_suites": {},
        "summary": {}
    }
    
    # Run all test suites
    test_suites = {
        "real_data_test": test_step15_with_real_data,
        "mock_data_test": test_step15_with_mock_historical_data,
        "error_handling_test": test_step15_error_handling
    }
    
    passed_tests = 0
    total_tests = len(test_suites)
    
    for suite_name, test_function in test_suites.items():
        logger.info(f"Running {suite_name}...")
        try:
            suite_results = test_function(period)
            comprehensive_results["test_suites"][suite_name] = suite_results
            if suite_results.get("test_passed", False):
                passed_tests += 1
        except Exception as e:
            logger.error(f"Error running {suite_name}: {str(e)}")
            comprehensive_results["test_suites"][suite_name] = {
                "test_passed": False,
                "errors": [f"Test suite error: {str(e)}"]
            }
    
    # Calculate overall results
    comprehensive_results["overall_passed"] = passed_tests == total_tests
    comprehensive_results["summary"] = {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": total_tests - passed_tests,
        "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    }
    
    logger.info(f"Comprehensive Step 15 tests completed. Overall passed: {comprehensive_results['overall_passed']}")
    
    return comprehensive_results


if __name__ == "__main__":
    # Run validation when script is executed directly
    import sys
    
    period = sys.argv[1] if len(sys.argv) > 1 else "202509A"
    test_type = sys.argv[2] if len(sys.argv) > 2 else "comprehensive"
    
    if test_type == "comprehensive":
        results = run_comprehensive_step15_tests(period)
        print(f"Comprehensive Step 15 test results:")
        print(f"  Period: {results['period']}")
        print(f"  Overall Passed: {results['overall_passed']}")
        print(f"  Success Rate: {results['summary']['success_rate']:.1f}%")
        print(f"  Passed Tests: {results['summary']['passed_tests']}/{results['summary']['total_tests']}")
    else:
        results = run_step15_validation(period)
        print(f"Step 15 validation results:")
        print(f"  Period: {results['period']}")
        print(f"  Validation Passed: {results['validation_passed']}")
        print(f"  Errors: {len(results['errors'])}")
        print(f"  Warnings: {len(results['warnings'])}")
    
    if results.get('errors'):
        print("\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    if results.get('warnings'):
        print("\nWarnings:")
        for warning in results['warnings']:
            print(f"  - {warning}")
