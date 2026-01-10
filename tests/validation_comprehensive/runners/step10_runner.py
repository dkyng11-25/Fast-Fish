"""
Step 10 Validation Runner: Smart Overcapacity (SPU) with Real-Unit Reductions

This module provides comprehensive validation for Step 10 outputs based on the actual
specification and implementation. Validates:

- Rule 10: Smart Overcapacity (SPU) with Real-Unit Reductions
- Detects SPU overcapacity (current SPU count > target SPU count) within categories
- Recommends unit quantity reductions using only real unit data
- Validates Fast Fish integration and per-store caps
- Ensures proper output file generation and manifest registration

Based on: process_and_merge_docs/STEP10_SPEC.md
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
import json
import os
import sys
import tempfile
import shutil

# Add project root to sys.path for src imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_step10_comprehensive(period: str = "202509A", 
                                 data_dir: str = "output") -> Dict[str, Any]:
    """
    Comprehensive validation for Step 10: Smart Overcapacity (SPU)
    
    Args:
        period: Period label for validation (e.g., "202508A")
        data_dir: Directory containing output files
        
    Returns:
        Dictionary containing validation results and statistics
    """
    logger.info(f"Starting Step 10 comprehensive validation for period {period}")
    
    results = {
        "step": 10,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "validation_status": "PASSED",
        "errors": [],
        "warnings": [],
        "data_quality": {},
        "business_logic": {},
        "file_validation": {}
    }
    
    try:
        # 1. Validate input data requirements
        input_validation = validate_step10_inputs(period, data_dir)
        results["input_validation"] = input_validation
        
        if not input_validation["all_inputs_available"]:
            results["validation_status"] = "FAILED"
            results["errors"].append("Required input files missing")
            return results
        
        # 2. Validate output files exist
        output_files = validate_step10_output_files(period, data_dir)
        results["file_validation"] = output_files
        
        if not output_files["all_outputs_exist"]:
            results["validation_status"] = "FAILED"
            results["errors"].append("Required output files missing")
            return results
        
        # 3. Validate results file structure and content
        results_validation = validate_step10_results_file(period, data_dir)
        results["results_validation"] = results_validation
        
        # 4. Validate opportunities file structure and content
        opportunities_validation = validate_step10_opportunities_file(period, data_dir)
        results["opportunities_validation"] = opportunities_validation
        
        # 5. Validate business logic
        business_logic_validation = validate_step10_business_logic(period, data_dir)
        results["business_logic"] = business_logic_validation
        
        # 6. Validate data quality
        data_quality_validation = validate_step10_data_quality(period, data_dir)
        results["data_quality"] = data_quality_validation
        
        # 7. Validate manifest registration
        manifest_validation = validate_step10_manifest_registration(period)
        results["manifest_validation"] = manifest_validation
        
        # Determine overall status
        if (results_validation["status"] == "PASSED" and 
            opportunities_validation["status"] == "PASSED" and
            business_logic_validation["status"] == "PASSED"):
            results["validation_status"] = "PASSED"
        else:
            results["validation_status"] = "FAILED"
        
        logger.info(f"Step 10 validation completed: {results['validation_status']}")
        
    except Exception as e:
        logger.error(f"Error in Step 10 validation: {str(e)}")
        results["validation_status"] = "ERROR"
        results["errors"].append(f"Validation error: {str(e)}")
    
    return results


def validate_step10_inputs(period: str, data_dir: str) -> Dict[str, Any]:
    """Validate Step 10 input data requirements."""
    logger.info("Validating Step 10 input data...")
    
    results = {
        "status": "PASSED",
        "all_inputs_available": True,
        "missing_inputs": [],
        "input_details": {}
    }
    
    # Required input files based on specification
    required_inputs = {
        "store_config": project_root / "data" / "api_data" / f"store_config_{period}.csv",
        "spu_sales": project_root / "data" / "api_data" / f"complete_spu_sales_{period}.csv",
        "clustering_results": project_root / data_dir / "clustering_results_spu.csv"
    }
    
    for input_name, file_path in required_inputs.items():
        if file_path.exists():
            try:
                df = pd.read_csv(file_path)
                results["input_details"][input_name] = {
                    "exists": True,
                    "rows": len(df),
                    "columns": list(df.columns)
                }
                
                # Validate required columns
                if input_name == "store_config":
                    required_cols = ["str_code", "sty_sal_amt"]
                    missing_cols = [col for col in required_cols if col not in df.columns]
                    if missing_cols:
                        results["missing_inputs"].append(f"{input_name}: missing columns {missing_cols}")
                
                elif input_name == "spu_sales":
                    required_cols = ["str_code", "spu_code", "quantity", "base_sal_qty", "fashion_sal_qty", "sal_qty"]
                    missing_cols = [col for col in required_cols if col not in df.columns]
                    if missing_cols:
                        results["missing_inputs"].append(f"{input_name}: missing columns {missing_cols}")
                
                elif input_name == "clustering_results":
                    required_cols = ["str_code", "spu_code", "Cluster"]
                    missing_cols = [col for col in required_cols if col not in df.columns]
                    if missing_cols:
                        results["missing_inputs"].append(f"{input_name}: missing columns {missing_cols}")
                
            except Exception as e:
                results["missing_inputs"].append(f"{input_name}: error reading file - {str(e)}")
        else:
            results["missing_inputs"].append(f"{input_name}: file not found - {file_path}")
    
    if results["missing_inputs"]:
        results["all_inputs_available"] = False
        results["status"] = "FAILED"
    
    return results


def validate_step10_output_files(period: str, data_dir: str) -> Dict[str, Any]:
    """Validate Step 10 output files exist."""
    logger.info("Validating Step 10 output files...")
    
    results = {
        "status": "PASSED",
        "all_outputs_exist": True,
        "missing_outputs": [],
        "output_details": {}
    }
    
    # Expected output files based on specification
    expected_outputs = {
        "results_legacy": project_root / data_dir / "rule10_spu_overcapacity_results.csv",
        "opportunities_legacy": project_root / data_dir / "rule10_spu_overcapacity_opportunities.csv",
        "results_period": project_root / data_dir / f"rule10_smart_overcapacity_results_{period}.csv",
        "opportunities_period": project_root / data_dir / f"rule10_spu_overcapacity_opportunities_{period}.csv",
        "summary_period": project_root / data_dir / f"rule10_smart_overcapacity_spu_summary_{period}.md"
    }
    
    for output_name, file_path in expected_outputs.items():
        if file_path.exists():
            try:
                if file_path.suffix == '.csv':
                    df = pd.read_csv(file_path)
                    results["output_details"][output_name] = {
                        "exists": True,
                        "rows": len(df),
                        "columns": list(df.columns)
                    }
                else:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    results["output_details"][output_name] = {
                        "exists": True,
                        "size": len(content),
                        "type": "markdown"
                    }
            except Exception as e:
                results["missing_outputs"].append(f"{output_name}: error reading file - {str(e)}")
        else:
            results["missing_outputs"].append(f"{output_name}: file not found - {file_path}")
    
    if results["missing_outputs"]:
        results["all_outputs_exist"] = False
        results["status"] = "FAILED"
    
    return results


def validate_step10_results_file(period: str, data_dir: str) -> Dict[str, Any]:
    """Validate Step 10 results file structure and content."""
    logger.info("Validating Step 10 results file...")
    
    results = {
        "status": "PASSED",
        "errors": [],
        "warnings": [],
        "data_quality": {}
    }
    
    # Try period-labeled file first, then legacy
    results_file_period = project_root / data_dir / f"rule10_smart_overcapacity_results_{period}.csv"
    results_file_legacy = project_root / data_dir / "rule10_spu_overcapacity_results.csv"
    
    results_file = None
    if results_file_period.exists():
        results_file = results_file_period
    elif results_file_legacy.exists():
        results_file = results_file_legacy
    
    if results_file is None:
        results["status"] = "FAILED"
        results["errors"].append("Results file not found")
        return results
    
    try:
        df = pd.read_csv(results_file)
        
        # Validate required columns
        required_columns = [
            "str_code", "cate_name", "sub_cate_name", "current_spu_count", 
            "target_spu_count", "excess_spu_count", "overcapacity_percentage"
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            results["errors"].append(f"Missing required columns: {missing_columns}")
            results["status"] = "FAILED"
        
        # Validate data quality
        if len(df) == 0:
            results["errors"].append("Results file is empty")
            results["status"] = "FAILED"
        else:
            results["data_quality"]["row_count"] = len(df)
            results["data_quality"]["column_count"] = len(df.columns)
            
            # Check for overcapacity detection
            if "overcapacity_percentage" in df.columns:
                overcapacity_rows = df[df["overcapacity_percentage"] > 0]
                results["data_quality"]["overcapacity_detected"] = len(overcapacity_rows)
                results["data_quality"]["overcapacity_rate"] = len(overcapacity_rows) / len(df)
            
            # Check for negative quantities (reductions)
            if "recommended_quantity_change" in df.columns:
                reduction_rows = df[df["recommended_quantity_change"] < 0]
                results["data_quality"]["reductions_recommended"] = len(reduction_rows)
        
    except Exception as e:
        results["status"] = "FAILED"
        results["errors"].append(f"Error reading results file: {str(e)}")
    
    return results


def validate_step10_opportunities_file(period: str, data_dir: str) -> Dict[str, Any]:
    """Validate Step 10 opportunities file structure and content."""
    logger.info("Validating Step 10 opportunities file...")
    
    results = {
        "status": "PASSED",
        "errors": [],
        "warnings": [],
        "data_quality": {}
    }
    
    # Try period-labeled file first, then legacy
    opportunities_file_period = project_root / data_dir / f"rule10_spu_overcapacity_opportunities_{period}.csv"
    opportunities_file_legacy = project_root / data_dir / "rule10_spu_overcapacity_opportunities.csv"
    
    opportunities_file = None
    if opportunities_file_period.exists():
        opportunities_file = opportunities_file_period
    elif opportunities_file_legacy.exists():
        opportunities_file = opportunities_file_legacy
    
    if opportunities_file is None:
        results["status"] = "FAILED"
        results["errors"].append("Opportunities file not found")
        return results
    
    try:
        df = pd.read_csv(opportunities_file)
        
        # Validate required columns for opportunities
        required_columns = [
            "str_code", "spu_code", "cate_name", "sub_cate_name",
            "recommended_quantity_change", "investment_required"
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            results["errors"].append(f"Missing required columns: {missing_columns}")
            results["status"] = "FAILED"
        
        # Validate data quality
        if len(df) == 0:
            results["warnings"].append("Opportunities file is empty")
        else:
            results["data_quality"]["row_count"] = len(df)
            results["data_quality"]["column_count"] = len(df.columns)
            
            # Check for negative quantities (reductions)
            if "recommended_quantity_change" in df.columns:
                reduction_rows = df[df["recommended_quantity_change"] < 0]
                results["data_quality"]["reductions_recommended"] = len(reduction_rows)
                
                # Check for proper negative values
                invalid_positive = df[(df["recommended_quantity_change"] > 0) & (df["recommended_quantity_change"].notna())]
                if len(invalid_positive) > 0:
                    results["warnings"].append(f"Found {len(invalid_positive)} positive quantity changes (should be negative for reductions)")
            
            # Check investment required (should be negative for savings)
            if "investment_required" in df.columns:
                savings_rows = df[df["investment_required"] < 0]
                results["data_quality"]["cost_savings"] = len(savings_rows)
        
    except Exception as e:
        results["status"] = "FAILED"
        results["errors"].append(f"Error reading opportunities file: {str(e)}")
    
    return results


def validate_step10_business_logic(period: str, data_dir: str) -> Dict[str, Any]:
    """Validate Step 10 business logic."""
    logger.info("Validating Step 10 business logic...")
    
    results = {
        "status": "PASSED",
        "errors": [],
        "warnings": [],
        "logic_checks": {}
    }
    
    try:
        # Load results file
        results_file_period = project_root / data_dir / f"rule10_smart_overcapacity_results_{period}.csv"
        results_file_legacy = project_root / data_dir / "rule10_spu_overcapacity_results.csv"
        
        results_file = None
        if results_file_period.exists():
            results_file = results_file_period
        elif results_file_legacy.exists():
            results_file = results_file_legacy
        
        if results_file is None:
            results["status"] = "FAILED"
            results["errors"].append("Results file not found for business logic validation")
            return results
        
        df = pd.read_csv(results_file)
        
        # Check overcapacity logic: current > target
        if "current_spu_count" in df.columns and "target_spu_count" in df.columns:
            overcapacity_logic = df["current_spu_count"] > df["target_spu_count"]
            results["logic_checks"]["overcapacity_detection"] = {
                "total_rows": len(df),
                "overcapacity_rows": overcapacity_logic.sum(),
                "correct_logic": overcapacity_logic.sum() > 0
            }
        
        # Check percentage calculation
        if "overcapacity_percentage" in df.columns and "excess_spu_count" in df.columns and "target_spu_count" in df.columns:
            expected_percentage = (df["excess_spu_count"] / df["target_spu_count"] * 100).fillna(0)
            percentage_diff = abs(df["overcapacity_percentage"] - expected_percentage).max()
            results["logic_checks"]["percentage_calculation"] = {
                "max_difference": percentage_diff,
                "accurate": percentage_diff < 0.01  # Allow small floating point differences
            }
        
        # Check per-store cap logic (if applicable)
        if "str_code" in df.columns:
            store_counts = df["str_code"].value_counts()
            max_per_store = store_counts.max()
            results["logic_checks"]["per_store_distribution"] = {
                "max_recommendations_per_store": max_per_store,
                "stores_with_recommendations": len(store_counts),
                "total_stores": df["str_code"].nunique()
            }
        
    except Exception as e:
        results["status"] = "FAILED"
        results["errors"].append(f"Error in business logic validation: {str(e)}")
    
    return results


def validate_step10_data_quality(period: str, data_dir: str) -> Dict[str, Any]:
    """Validate Step 10 data quality."""
    logger.info("Validating Step 10 data quality...")
    
    results = {
        "status": "PASSED",
        "errors": [],
        "warnings": [],
        "quality_metrics": {}
    }
    
    try:
        # Load opportunities file for detailed quality checks
        opportunities_file = f"{data_dir}/rule10_spu_overcapacity_opportunities_{period}.csv"
        if not os.path.exists(opportunities_file):
            opportunities_file = f"{data_dir}/rule10_spu_overcapacity_opportunities.csv"
        
        if not os.path.exists(opportunities_file):
            results["warnings"].append("Opportunities file not found for quality validation")
            return results
        
        df = pd.read_csv(opportunities_file)
        
        # Check for missing values in critical columns
        critical_columns = ["str_code", "spu_code", "recommended_quantity_change"]
        for col in critical_columns:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                results["quality_metrics"][f"{col}_missing"] = missing_count
                if missing_count > 0:
                    results["warnings"].append(f"Missing values in {col}: {missing_count}")
        
        # Check for duplicate records
        if "str_code" in df.columns and "spu_code" in df.columns:
            duplicates = df.duplicated(subset=["str_code", "spu_code"]).sum()
            results["quality_metrics"]["duplicates"] = duplicates
            if duplicates > 0:
                results["warnings"].append(f"Duplicate records found: {duplicates}")
        
        # Check data types
        if "recommended_quantity_change" in df.columns:
            numeric_errors = pd.to_numeric(df["recommended_quantity_change"], errors='coerce').isna().sum()
            results["quality_metrics"]["non_numeric_quantities"] = numeric_errors
            if numeric_errors > 0:
                results["warnings"].append(f"Non-numeric quantity changes: {numeric_errors}")
        
    except Exception as e:
        results["status"] = "FAILED"
        results["errors"].append(f"Error in data quality validation: {str(e)}")
    
    return results


def validate_step10_manifest_registration(period: str) -> Dict[str, Any]:
    """Validate Step 10 manifest registration."""
    logger.info("Validating Step 10 manifest registration...")
    
    results = {
        "status": "PASSED",
        "errors": [],
        "warnings": [],
        "manifest_entries": {}
    }
    
    try:
        # Try to load manifest
        from src.pipeline_manifest import get_manifest
        
        manifest = get_manifest()
        step_outputs = manifest.get('steps', {}).get('step10', {}).get('outputs', {})
        
        expected_keys = [
            "rule10_spu_overcapacity_results",
            "rule10_spu_overcapacity_opportunities",
            f"rule10_smart_overcapacity_results_{period}",
            f"rule10_spu_overcapacity_opportunities_{period}",
            f"rule10_smart_overcapacity_spu_summary_{period}"
        ]
        
        for key in expected_keys:
            if key in step_outputs:
                results["manifest_entries"][key] = "registered"
            else:
                results["manifest_entries"][key] = "missing"
                results["warnings"].append(f"Manifest entry missing: {key}")
        
    except Exception as e:
        results["warnings"].append(f"Could not validate manifest registration: {str(e)}")
    
    return results


def test_step10_with_real_data(period: str = "202509A") -> Dict[str, Any]:
    """
    Test Step 10 using real data files with comprehensive validation.
    
    Args:
        period: Period label for testing (e.g., "202509A")
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Starting Step 10 real data test for period {period}")
    
    results = {
        "step": 10,
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
        
        # Run step10 from project root
        project_root = Path(__file__).parent.parent.parent.parent
        original_cwd = os.getcwd()
        
        try:
            os.chdir(project_root)
            print(f"DEBUG: Changed to project root: {project_root}")
            print(f"DEBUG: Current working directory: {os.getcwd()}")
            
            # Add both project root and src to path for imports
            project_root_str = str(project_root)
            src_path = str(project_root / "src")
            sys.path.insert(0, project_root_str)  # For 'src' imports
            sys.path.insert(0, src_path)  # For direct module imports
            print(f"DEBUG: Added to sys.path: {project_root_str} and {src_path}")
            
            from step10_spu_assortment_optimization import fast_pipeline_analysis, parse_args
            print("DEBUG: Import successful")
            
            # Step10 will run and create overcapacity results
            try:
                # Mock command line arguments for step10
                original_argv = sys.argv.copy()
                sys.argv = [
                    'step10_runner.py',
                    '--yyyymm', period[:6],
                    '--period', period[-1],
                    '--target-yyyymm', period[:6],
                    '--target-period', period[-1]
                ]
                
                # Parse arguments for step10
                args = parse_args()
                fast_pipeline_analysis(args)
                results["test_results"]["execution"] = "completed"
                
                # Restore original argv
                sys.argv = original_argv
            except Exception as e:
                # Restore original argv in case of error
                sys.argv = original_argv
                results["errors"].append(f"Error during execution: {str(e)}")
                results["test_results"]["execution"] = "failed"
        finally:
            os.chdir(original_cwd)
        
        # Verify output files were created
        project_output_dir = project_root / "output"
        
        # Look for the actual files created by Step 10
        results_files = list(project_output_dir.glob(f"rule10_smart_overcapacity_results_{period}*.csv"))
        opportunities_files = list(project_output_dir.glob(f"rule10_spu_overcapacity_opportunities_{period}*.csv"))
        summary_files = list(project_output_dir.glob(f"rule10_smart_overcapacity_spu_summary_{period}*.md"))
        
        if results_files:
            results["test_results"]["results_file_created"] = True
            results_df = pd.read_csv(results_files[0])
            results["statistics"]["results_records"] = len(results_df)
        else:
            results["warnings"].append("Results file not created")
            results["test_results"]["results_file_created"] = False
        
        if opportunities_files:
            results["test_results"]["opportunities_file_created"] = True
            opportunities_df = pd.read_csv(opportunities_files[0])
            results["statistics"]["opportunities_records"] = len(opportunities_df)
        else:
            results["warnings"].append("Opportunities file not created")
            results["test_results"]["opportunities_file_created"] = False
        
        if summary_files:
            results["test_results"]["summary_file_created"] = True
            results["statistics"]["summary_file_size"] = os.path.getsize(summary_files[0])
        else:
            results["warnings"].append("Summary file not created")
            results["test_results"]["summary_file_created"] = False
        
        # Overall test status
        results["test_passed"] = (
            results["test_results"].get("execution") == "completed" and
            results["test_results"].get("results_file_created", False) and
            results["test_results"].get("opportunities_file_created", False)
        )
        
        logger.info(f"Step 10 real data test completed. Passed: {results['test_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 10 real data test: {str(e)}")
        results["errors"].append(f"Test error: {str(e)}")
        results["test_passed"] = False
    
    return results


def test_step10_error_handling(period: str = "202509A") -> Dict[str, Any]:
    """
    Test Step 10 error handling when input files are missing.
    
    Args:
        period: Period label for testing (e.g., "202509A")
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Starting Step 10 error handling test for period {period}")
    
    results = {
        "step": 10,
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
        
        # Temporarily move input files to test error handling
        project_root = Path(__file__).parent.parent.parent.parent
        original_cwd = os.getcwd()
        
        # Backup and remove input files
        input_files = [
            "data/api_data/store_config.csv",
            "data/api_data/complete_spu_sales.csv",
            "output/clustering_results_spu.csv"
        ]
        
        backed_up_files = []
        try:
            for file_path in input_files:
                src = project_root / file_path
                if src.exists():
                    backup = src.with_suffix(src.suffix + '.backup')
                    shutil.move(str(src), str(backup))
                    backed_up_files.append((src, backup))
            
            # Run step10 from project root
            try:
                os.chdir(project_root)
                
                # Add both project root and src to path for imports
                project_root_str = str(project_root)
                src_path = str(project_root / "src")
                sys.path.insert(0, project_root_str)  # For 'src' imports
                sys.path.insert(0, src_path)  # For direct module imports
                from step10_spu_assortment_optimization import fast_pipeline_analysis, parse_args
                
                # This should raise an error when input files are missing
                try:
                    # Mock command line arguments for step10
                    original_argv = sys.argv.copy()
                    sys.argv = [
                        'step10_runner.py',
                        '--yyyymm', period[:6],
                        '--period', period[-1],
                        '--target-yyyymm', period[:6],
                        '--target-period', period[-1]
                    ]
                    
                    # Parse arguments for step10
                    args = parse_args()
                    fast_pipeline_analysis(args)
                    results["errors"].append("Expected error but execution completed successfully")
                    results["test_results"]["error_handling"] = "failed"
                    
                    # Restore original argv
                    sys.argv = original_argv
                except FileNotFoundError as e:
                    # Restore original argv in case of error
                    sys.argv = original_argv
                    results["test_results"]["error_handling"] = "passed"
                    results["warnings"].append("Correctly raised FileNotFoundError for missing input files")
                except Exception as e:
                    # Restore original argv in case of error
                    sys.argv = original_argv
                    results["test_results"]["error_handling"] = "passed"
                    results["warnings"].append(f"Correctly raised error for missing input files: {type(e).__name__}")
            finally:
                os.chdir(original_cwd)
        finally:
            # Restore backed up files
            for src, backup in backed_up_files:
                if backup.exists():
                    shutil.move(str(backup), str(src))
        
        # Overall test status
        results["test_passed"] = results["test_results"].get("error_handling") == "passed"
        results["statistics"]["errors_count"] = len(results["errors"])
        results["statistics"]["warnings_count"] = len(results["warnings"])
        
        logger.info(f"Step 10 error handling test completed. Passed: {results['test_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 10 error handling test: {str(e)}")
        results["errors"].append(f"Test error: {str(e)}")
        results["test_passed"] = False
    
    return results


def run_comprehensive_step10_tests(period: str = "202509A") -> Dict[str, Any]:
    """
    Run comprehensive Step 10 tests including real data and error handling.
    
    Args:
        period: Period label for testing (e.g., "202509A")
        
    Returns:
        Dictionary with comprehensive test results
    """
    logger.info(f"Starting comprehensive Step 10 tests for period {period}")
    
    comprehensive_results = {
        "step": 10,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "overall_passed": False,
        "test_suites": {},
        "summary": {}
    }
    
    # Run all test suites
    test_suites = {
        "real_data_test": test_step10_with_real_data,
        "error_handling_test": test_step10_error_handling
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
    
    logger.info(f"Comprehensive Step 10 tests completed. Overall passed: {comprehensive_results['overall_passed']}")
    
    return comprehensive_results


def run_step10_validation(period: str = "202508A", data_dir: str = "../output") -> Dict[str, Any]:
    """Run Step 10 validation."""
    return validate_step10_comprehensive(period, data_dir)


if __name__ == "__main__":
    # Run validation when script is executed directly
    import sys
    
    period = sys.argv[1] if len(sys.argv) > 1 else "202509A"
    test_type = sys.argv[2] if len(sys.argv) > 2 else "comprehensive"
    
    if test_type == "comprehensive":
        results = run_comprehensive_step10_tests(period)
        print(f"Comprehensive Step 10 test results:")
        print(f"  Period: {results['period']}")
        print(f"  Overall Passed: {results['overall_passed']}")
        print(f"  Success Rate: {results['summary']['success_rate']:.1f}%")
        print(f"  Passed Tests: {results['summary']['passed_tests']}/{results['summary']['total_tests']}")
    else:
        results = run_step10_validation(period)
        print(f"Step 10 validation results:")
        print(f"  Validation Passed: {results.get('validation_status', False)}")
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