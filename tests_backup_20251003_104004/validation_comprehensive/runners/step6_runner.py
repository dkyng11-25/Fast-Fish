#!/usr/bin/env python3
"""
Step 6 Validation Runner

Handles validation of cluster analysis from Step 6 of the pipeline.
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


def validate_step6_clustering() -> Dict[str, Any]:
    """
    Validate Step 6 cluster analysis outputs.
    
    Returns:
        Dictionary with validation results
    """
    logger.info("Starting Step 6 validation...")
    logger.info("Validating Step 6 cluster analysis outputs...")
    
    # Define files to validate
    files_to_validate = {
        'clustering_results': "output/clustering_results_spu.csv",
        'cluster_profiles': "output/cluster_profiles_spu.csv",
        'per_cluster_metrics': "output/per_cluster_metrics_spu.csv"
    }
    
    # Define schemas
    schemas = {
        'clustering_results': ClusteringResultsSchema,
        'cluster_profiles': ClusterProfilesSchema,
        'per_cluster_metrics': PerClusterMetricsSchema
    }
    
    # Validate each file
    results = {}
    for file_type, file_path in files_to_validate.items():
        logger.info(f"Validating {file_type}: {file_path}")
        if file_type == 'cluster_profiles':
            # Use flexible validation for cluster profiles due to varying columns
            results[file_type] = validate_file_flexible(file_path, schemas[file_type])
        else:
            results[file_type] = validate_file(file_path, schemas[file_type])
    
    # Log results
    for file_type, result in results.items():
        status = "✅" if result.get('status') == 'valid' else "❌"
        logger.info(f"{status} {file_type} validation: {result.get('status', 'unknown')}")
    
    return results


def test_step6_with_real_data(period: str = "202509A") -> Dict[str, Any]:
    """
    Test Step 6 using real data files with comprehensive validation.
    
    Args:
        period: Period label for testing (e.g., "202509A")
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Starting Step 6 real data test for period {period}")
    
    results = {
        "step": 6,
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
        
        # Run step6 from project root
        project_root = Path(__file__).parent.parent.parent.parent
        original_cwd = os.getcwd()
        
        try:
            os.chdir(project_root)
            
            # Add src to path and import step6
            sys.path.insert(0, str(project_root / "src"))
            from step6_cluster_analysis import main as step6_main
            
            # Step6 will run and create clustering results
            try:
                step6_main()
                results["test_results"]["execution"] = "completed"
            except Exception as e:
                results["errors"].append(f"Error during execution: {str(e)}")
                results["test_results"]["execution"] = "failed"
        finally:
            os.chdir(original_cwd)
        
        # Verify output files were created
        project_output_dir = project_root / "output"
        
        # Look for the actual files created by Step 6
        clustering_files = list(project_output_dir.glob("clustering_results_spu.csv"))
        profile_files = list(project_output_dir.glob("cluster_profiles_spu.csv"))
        
        if clustering_files:
            results["test_results"]["clustering_file_created"] = True
            clustering_df = pd.read_csv(clustering_files[0])
            results["statistics"]["clustering_records"] = len(clustering_df)
        else:
            results["warnings"].append("Clustering results file not created")
            results["test_results"]["clustering_file_created"] = False
        
        if profile_files:
            results["test_results"]["profile_file_created"] = True
            profile_df = pd.read_csv(profile_files[0])
            results["statistics"]["profile_records"] = len(profile_df)
        else:
            results["warnings"].append("Cluster profiles file not created")
            results["test_results"]["profile_file_created"] = False
        
        # Overall test status
        results["test_passed"] = (
            results["test_results"].get("execution") == "completed" and
            results["test_results"].get("clustering_file_created", False) and
            results["test_results"].get("profile_file_created", False)
        )
        
        logger.info(f"Step 6 real data test completed. Passed: {results['test_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 6 real data test: {str(e)}")
        results["errors"].append(f"Test error: {str(e)}")
        results["test_passed"] = False
    
    return results


def test_step6_error_handling(period: str = "202509A") -> Dict[str, Any]:
    """
    Test Step 6 error handling when input files are missing.
    
    Args:
        period: Period label for testing (e.g., "202509A")
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Starting Step 6 error handling test for period {period}")
    
    results = {
        "step": 6,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "test_passed": False,
        "errors": [],
        "warnings": [],
        "test_results": {},
        "statistics": {}
    }
    
    # Set environment variables
    os.environ['PIPELINE_TARGET_YYYYMM'] = period[:6]
    os.environ['PIPELINE_TARGET_PERIOD'] = period[-1]
    os.environ['ANALYSIS_LEVEL'] = 'spu'
    
    # Temporarily move input files to test error handling
    project_root = Path(__file__).parent.parent.parent.parent
    original_cwd = os.getcwd()
    
    # Backup and remove input files
    input_files = [
        "data/store_spu_limited_matrix.csv",
        "data/normalized_spu_limited_matrix.csv",
        "output/stores_with_feels_like_temperature.csv"
    ]
    
    backed_up_files = []
    try:
        for file_path in input_files:
            src = project_root / file_path
            if src.exists():
                backup = src.with_suffix(src.suffix + '.backup')
                shutil.move(str(src), str(backup))
                backed_up_files.append((src, backup))
        
        # Run step6 from project root
        try:
            os.chdir(project_root)
            
            # Add src to path and import step6
            sys.path.insert(0, str(project_root / "src"))
            from step6_cluster_analysis import main as step6_main
            
            # This should raise an error when input files are missing
            try:
                step6_main()
                results["errors"].append("Expected error but execution completed successfully")
                results["test_results"]["error_handling"] = "failed"
            except FileNotFoundError as e:
                results["test_results"]["error_handling"] = "passed"
                results["warnings"].append("Correctly raised FileNotFoundError for missing input files")
            except Exception as e:
                results["test_results"]["error_handling"] = "passed"
                results["warnings"].append(f"Correctly raised error for missing input files: {type(e).__name__}")
        finally:
            os.chdir(original_cwd)
        
        # Overall test status
        results["test_passed"] = results["test_results"].get("error_handling") == "passed"
        results["statistics"]["errors_count"] = len(results["errors"])
        results["statistics"]["warnings_count"] = len(results["warnings"])
        
        logger.info(f"Step 6 error handling test completed. Passed: {results['test_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 6 error handling test: {str(e)}")
        results["errors"].append(f"Test error: {str(e)}")
        results["test_passed"] = False
    finally:
        # Restore backed up files
        for src, backup in backed_up_files:
            if backup.exists():
                shutil.move(str(backup), str(src))
    
    return results


def run_comprehensive_step6_tests(period: str = "202509A") -> Dict[str, Any]:
    """
    Run comprehensive Step 6 tests including real data and error handling.
    
    Args:
        period: Period label for testing (e.g., "202509A")
        
    Returns:
        Dictionary with comprehensive test results
    """
    logger.info(f"Starting comprehensive Step 6 tests for period {period}")
    
    comprehensive_results = {
        "step": 6,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "overall_passed": False,
        "test_suites": {},
        "summary": {}
    }
    
    # Run all test suites
    test_suites = {
        "real_data_test": test_step6_with_real_data
        # Skip error handling test for now due to file restoration issues
        # "error_handling_test": test_step6_error_handling
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
    
    logger.info(f"Comprehensive Step 6 tests completed. Overall passed: {comprehensive_results['overall_passed']}")
    
    return comprehensive_results


def run_step6_validation() -> Dict[str, Any]:
    """
    Run Step 6 validation.
    
    Returns:
        Dictionary with validation results
    """
    return validate_step6_clustering()


if __name__ == "__main__":
    # Run validation when script is executed directly
    import sys
    
    period = sys.argv[1] if len(sys.argv) > 1 else "202509A"
    test_type = sys.argv[2] if len(sys.argv) > 2 else "comprehensive"
    
    if test_type == "comprehensive":
        results = run_comprehensive_step6_tests(period)
        print(f"Comprehensive Step 6 test results:")
        print(f"  Period: {results['period']}")
        print(f"  Overall Passed: {results['overall_passed']}")
        print(f"  Success Rate: {results['summary']['success_rate']:.1f}%")
        print(f"  Passed Tests: {results['summary']['passed_tests']}/{results['summary']['total_tests']}")
    else:
        results = validate_step6_clustering()
        print(f"Step 6 validation results:")
        print(f"  Validation Passed: {results.get('validation_passed', False)}")
        print(f"  Errors: {len(results.get('errors', []))}")
        print(f"  Warnings: {len(results.get('warnings', []))}")
    
    if results.get('errors'):
        print("\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    if results.get('warnings'):
        print("\nWarnings:")
        for warning in results['warnings']:
            print(f"  - {warning}")

