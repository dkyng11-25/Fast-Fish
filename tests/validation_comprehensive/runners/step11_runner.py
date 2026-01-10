"""
Step 11 Validation Runner: Missed Sales Opportunity (SPU) with Real-Unit, Incremental Quantity Recommendations

This module provides comprehensive validation for Step 11 outputs including:
- Results file validation (store-level aggregated results)
- Details file validation (detailed opportunity information)
- Top performers file validation (cluster-category top performers)
- Input data validation (clustering, quantity data)
- Business logic validation (opportunity detection, positive quantities, top performer logic)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
import os
import sys
import tempfile
import shutil

# Import schemas - handle both direct and relative imports
try:
    from ..schemas.step11_schemas import (
        Step11ResultsSchema,
        Step11DetailsSchema,
        Step11TopPerformersSchema,
        Step11InputClusteringSchema,
        Step11InputQuantitySchema,
        validate_step11_results,
        validate_step11_details,
        validate_step11_top_performers,
        validate_step11_inputs,
        validate_positive_quantities,
        validate_opportunity_detection_logic,
        validate_top_performer_logic
    )
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "schemas"))
    from step11_schemas import (
        Step11ResultsSchema,
        Step11DetailsSchema,
        Step11TopPerformersSchema,
        Step11InputClusteringSchema,
        Step11InputQuantitySchema,
        validate_step11_results,
        validate_step11_details,
        validate_step11_top_performers,
        validate_step11_inputs,
        validate_positive_quantities,
        validate_opportunity_detection_logic,
        validate_top_performer_logic
    )

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_step11_comprehensive(period: str = "202508A", 
                                 data_dir: str = "../output") -> Dict[str, Any]:
    """
    Comprehensive validation for Step 11: Missed Sales Opportunity (SPU)
    
    Args:
        period: Period label for validation (e.g., "202508A")
        data_dir: Directory containing output files
        
    Returns:
        Dictionary containing validation results and statistics
    """
    logger.info(f"Starting Step 11 comprehensive validation for period {period}")
    
    results = {
        "step": 11,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "validation_passed": False,
        "errors": [],
        "warnings": [],
        "statistics": {},
        "file_validation": {},
        "business_logic_validation": {}
    }
    
    try:
        # Define file paths
        data_path = Path(data_dir)
        
        # Results file (try both legacy and period-labeled versions)
        results_file = data_path / f"rule11_improved_missed_sales_opportunity_spu_results_{period}.csv"
        if not results_file.exists():
            results_file = data_path / "rule11_improved_missed_sales_opportunity_spu_results.csv"
        
        # Details file (try both legacy and period-labeled versions)
        details_file = data_path / f"rule11_improved_missed_sales_opportunity_spu_details_{period}.csv"
        if not details_file.exists():
            details_file = data_path / "rule11_improved_missed_sales_opportunity_spu_details.csv"
        
        # Top performers file (try both legacy and period-labeled versions)
        top_performers_file = data_path / f"rule11_improved_top_performers_by_cluster_category_{period}.csv"
        if not top_performers_file.exists():
            top_performers_file = data_path / "rule11_improved_top_performers_by_cluster_category.csv"
        
        # Summary file
        summary_file = data_path / f"rule11_improved_missed_sales_opportunity_spu_summary_{period}.md"
        if not summary_file.exists():
            summary_file = data_path / "rule11_improved_missed_sales_opportunity_spu_summary.md"
        
        # Validate results file
        if results_file.exists():
            logger.info(f"Validating results file: {results_file}")
            results_df = pd.read_csv(results_file)
            results["file_validation"]["results"] = validate_step11_results(results_df)
            results["statistics"]["results_rows"] = len(results_df)
            results["statistics"]["results_columns"] = len(results_df.columns)
        else:
            results["errors"].append(f"Results file not found: {results_file}")
            results["file_validation"]["results"] = False
        
        # Validate details file
        if details_file.exists():
            logger.info(f"Validating details file: {details_file}")
            details_df = pd.read_csv(details_file)
            results["file_validation"]["details"] = validate_step11_details(details_df)
            results["statistics"]["details_rows"] = len(details_df)
            results["statistics"]["details_columns"] = len(details_df.columns)
        else:
            results["errors"].append(f"Details file not found: {details_file}")
            results["file_validation"]["details"] = False
        
        # Validate top performers file
        if top_performers_file.exists():
            logger.info(f"Validating top performers file: {top_performers_file}")
            top_performers_df = pd.read_csv(top_performers_file)
            results["file_validation"]["top_performers"] = validate_step11_top_performers(top_performers_df)
            results["statistics"]["top_performers_rows"] = len(top_performers_df)
            results["statistics"]["top_performers_columns"] = len(top_performers_df.columns)
        else:
            results["warnings"].append(f"Top performers file not found: {top_performers_file}")
            results["file_validation"]["top_performers"] = False
        
        # Check summary file
        if summary_file.exists():
            logger.info(f"Summary file found: {summary_file}")
            results["file_validation"]["summary"] = True
        else:
            results["warnings"].append(f"Summary file not found: {summary_file}")
            results["file_validation"]["summary"] = False
        
        # Business logic validation if data is available
        if results["file_validation"]["results"] and results["file_validation"]["details"]:
            logger.info("Performing business logic validation")
            business_logic_results = validate_step11_business_logic(results_df, details_df, top_performers_df if results["file_validation"]["top_performers"] else None)
            results["business_logic_validation"] = business_logic_results
        
        # Overall validation status
        results["validation_passed"] = all([
            results["file_validation"]["results"],
            results["file_validation"]["details"]
        ]) and len(results["errors"]) == 0
        
        logger.info(f"Step 11 validation completed. Passed: {results['validation_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 11 validation: {str(e)}")
        results["errors"].append(f"Validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_step11_business_logic(results_df: pd.DataFrame, 
                                  details_df: pd.DataFrame, 
                                  top_performers_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Validate Step 11 business logic and constraints
    
    Args:
        results_df: Results dataframe
        details_df: Details dataframe
        top_performers_df: Top performers dataframe (optional)
        
    Returns:
        Dictionary containing business logic validation results
    """
    validation_results = {
        "positive_quantity_validation": {},
        "opportunity_detection": {},
        "top_performer_validation": {},
        "investment_validation": {},
        "fast_fish_validation": {},
        "recommendation_type_validation": {}
    }
    
    try:
        # Positive quantity validation (critical for Step 11 - increases only)
        if "recommended_quantity_change" in results_df.columns:
            quantity_changes = results_df["recommended_quantity_change"].dropna()
            validation_results["positive_quantity_validation"] = {
                "all_positive": bool((quantity_changes >= 0).all()),
                "min_change": float(quantity_changes.min()),
                "max_change": float(quantity_changes.max()),
                "mean_change": float(quantity_changes.mean()),
                "total_changes": len(quantity_changes),
                "positive_changes": int((quantity_changes > 0).sum()),
                "zero_changes": int((quantity_changes == 0).sum())
            }
        
        # Opportunity detection validation
        if "rule11_missed_sales_opportunity" in results_df.columns:
            opportunity_stores = results_df[results_df["rule11_missed_sales_opportunity"] == 1]
            validation_results["opportunity_detection"] = {
                "total_stores": len(results_df),
                "opportunity_stores": len(opportunity_stores),
                "opportunity_percentage": len(opportunity_stores) / len(results_df) * 100,
                "logic_validation": validate_opportunity_detection_logic(details_df)
            }
        
        # Top performer validation
        if top_performers_df is not None and len(top_performers_df) > 0:
            validation_results["top_performer_validation"] = {
                "total_top_performers": len(top_performers_df),
                "unique_clusters": top_performers_df["cluster"].nunique(),
                "unique_categories": top_performers_df["category_key"].nunique(),
                "unique_spus": top_performers_df["spu_code"].nunique(),
                "logic_validation": validate_top_performer_logic(top_performers_df)
            }
        
        # Investment validation
        if "investment_required" in results_df.columns:
            investments = results_df["investment_required"].dropna()
            validation_results["investment_validation"] = {
                "total_investment": float(investments.sum()),
                "min_investment": float(investments.min()),
                "max_investment": float(investments.max()),
                "mean_investment": float(investments.mean()),
                "positive_investments": int((investments > 0).sum())
            }
        
        # Fast Fish validation status
        if "fast_fish_compliant" in details_df.columns:
            fast_fish_status = details_df["fast_fish_compliant"].value_counts()
            validation_results["fast_fish_validation"] = {
                "compliant_count": int(fast_fish_status.get(True, 0)),
                "non_compliant_count": int(fast_fish_status.get(False, 0)),
                "total_opportunities": len(details_df),
                "compliance_rate": int(fast_fish_status.get(True, 0)) / len(details_df) * 100
            }
        
        # Recommendation type validation
        if "recommendation_type" in details_df.columns:
            recommendation_types = details_df["recommendation_type"].value_counts()
            validation_results["recommendation_type_validation"] = {
                "type_counts": recommendation_types.to_dict(),
                "has_add_new": "ADD_NEW" in recommendation_types.index,
                "has_increase_existing": "INCREASE_EXISTING" in recommendation_types.index,
                "total_recommendations": len(details_df)
            }
        
        # SPU-level validation
        if "spu_code" in details_df.columns:
            unique_spus = details_df["spu_code"].nunique()
            validation_results["spu_validation"] = {
                "unique_spus": unique_spus,
                "has_spu_codes": unique_spus > 0
            }
        
        # Category-level validation
        if "sub_cate_name" in details_df.columns:
            unique_categories = details_df["sub_cate_name"].nunique()
            validation_results["category_validation"] = {
                "unique_categories": unique_categories,
                "has_categories": unique_categories > 0
            }
        
        # Opportunity score validation
        if "opportunity_score" in details_df.columns:
            opportunity_scores = details_df["opportunity_score"].dropna()
            validation_results["opportunity_score_validation"] = {
                "min_score": float(opportunity_scores.min()),
                "max_score": float(opportunity_scores.max()),
                "mean_score": float(opportunity_scores.mean()),
                "high_score_count": int((opportunity_scores >= 0.5).sum())
            }
        
    except Exception as e:
        logger.error(f"Error in business logic validation: {str(e)}")
        validation_results["error"] = str(e)
    
    return validation_results


def validate_step11_inputs_comprehensive(period: str = "202508A",
                                       data_dir: str = "../data",
                                       output_dir: str = "../output") -> Dict[str, Any]:
    """
    Comprehensive validation for Step 11 input data
    
    Args:
        period: Period label for validation
        data_dir: Directory containing input data files
        output_dir: Directory containing clustering results
        
    Returns:
        Dictionary containing input validation results
    """
    logger.info(f"Starting Step 11 input validation for period {period}")
    
    results = {
        "step": 11,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "validation_passed": False,
        "errors": [],
        "warnings": [],
        "file_validation": {},
        "data_quality": {}
    }
    
    try:
        # Resolve paths relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        data_path = project_root / data_dir.lstrip("../")
        output_path = project_root / output_dir.lstrip("../")
        
        # Check clustering results
        clustering_file = output_path / "clustering_results_spu.csv"
        if not clustering_file.exists():
            clustering_file = output_path / "clustering_results_subcategory.csv"
        
        if clustering_file.exists():
            logger.info(f"Validating clustering file: {clustering_file}")
            clustering_df = pd.read_csv(clustering_file)
            results["file_validation"]["clustering"] = validate_step11_inputs(
                clustering_df, pd.DataFrame()
            )
            results["data_quality"]["clustering_rows"] = len(clustering_df)
            results["data_quality"]["clustering_columns"] = len(clustering_df.columns)
        else:
            results["errors"].append(f"Clustering file not found: {clustering_file}")
            results["file_validation"]["clustering"] = False
        
        # Check quantity data file
        quantity_file = data_path / f"complete_spu_sales_{period}.csv"
        if quantity_file.exists():
            logger.info(f"Validating quantity file: {quantity_file}")
            quantity_df = pd.read_csv(quantity_file)
            results["file_validation"]["quantity"] = True
            results["data_quality"]["quantity_rows"] = len(quantity_df)
            results["data_quality"]["quantity_columns"] = len(quantity_df.columns)
        else:
            results["warnings"].append(f"Quantity file not found: {quantity_file}")
            results["file_validation"]["quantity"] = False
        
        # Overall validation status - only require clustering validation to pass
        # Quantity file is optional for this validation
        results["validation_passed"] = results["file_validation"]["clustering"] and len(results["errors"]) == 0
        
        logger.info(f"Step 11 input validation completed. Passed: {results['validation_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 11 input validation: {str(e)}")
        results["errors"].append(f"Input validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def test_step11_with_real_data(period: str = "202509A") -> Dict[str, Any]:
    """
    Test Step 11 using real data files with comprehensive validation.
    
    Args:
        period: Period label for testing (e.g., "202509A")
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Starting Step 11 real data test for period {period}")
    
    results = {
        "step": 11,
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
        
        # Run step11 from project root
        project_root = Path(__file__).parent.parent.parent.parent
        original_cwd = os.getcwd()
        
        try:
            os.chdir(project_root)
            
            # Add src to path and import step11
            sys.path.insert(0, str(project_root / "src"))
            from step11_missed_sales_opportunity import main as step11_main
            
            # Step11 will run and create missed sales opportunity results
            try:
                step11_main(testing_mode=False, period_label=period)
                results["test_results"]["execution"] = "completed"
            except Exception as e:
                results["errors"].append(f"Error during execution: {str(e)}")
                results["test_results"]["execution"] = "failed"
        finally:
            os.chdir(original_cwd)
        
        # Verify output files were created
        project_output_dir = project_root / "output"
        
        # Look for the actual files created by Step 11
        results_files = list(project_output_dir.glob(f"rule11_improved_missed_sales_opportunity_spu_results_{period}*.csv"))
        details_files = list(project_output_dir.glob(f"rule11_improved_missed_sales_opportunity_spu_details_{period}*.csv"))
        top_performers_files = list(project_output_dir.glob(f"rule11_improved_top_performers_by_cluster_category_{period}*.csv"))
        summary_files = list(project_output_dir.glob(f"rule11_improved_missed_sales_opportunity_spu_summary_{period}*.md"))
        
        if results_files:
            results["test_results"]["results_file_created"] = True
            results_df = pd.read_csv(results_files[0])
            results["statistics"]["results_records"] = len(results_df)
        else:
            results["warnings"].append("Results file not created")
            results["test_results"]["results_file_created"] = False
        
        if details_files:
            results["test_results"]["details_file_created"] = True
            details_df = pd.read_csv(details_files[0])
            results["statistics"]["details_records"] = len(details_df)
        else:
            results["warnings"].append("Details file not created")
            results["test_results"]["details_file_created"] = False
        
        if top_performers_files:
            results["test_results"]["top_performers_file_created"] = True
            top_performers_df = pd.read_csv(top_performers_files[0])
            results["statistics"]["top_performers_records"] = len(top_performers_df)
        else:
            results["warnings"].append("Top performers file not created")
            results["test_results"]["top_performers_file_created"] = False
        
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
            results["test_results"].get("details_file_created", False)
        )
        
        logger.info(f"Step 11 real data test completed. Passed: {results['test_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 11 real data test: {str(e)}")
        results["errors"].append(f"Test error: {str(e)}")
        results["test_passed"] = False
    
    return results


def test_step11_error_handling(period: str = "202509A") -> Dict[str, Any]:
    """
    Test Step 11 error handling when input files are missing.
    
    Args:
        period: Period label for testing (e.g., "202509A")
        
    Returns:
        Dictionary with test results
    """
    logger.info(f"Starting Step 11 error handling test for period {period}")
    
    results = {
        "step": 11,
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
            
            # Run step11 from project root
            try:
                os.chdir(project_root)
                
                # Add src to path and import step11
                sys.path.insert(0, str(project_root / "src"))
                from step11_missed_sales_opportunity import main as step11_main
                
                # This should raise an error when input files are missing
                try:
                    step11_main(testing_mode=False, period_label=period)
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
        finally:
            # Restore backed up files
            for src, backup in backed_up_files:
                if backup.exists():
                    shutil.move(str(backup), str(src))
        
        # Overall test status
        results["test_passed"] = results["test_results"].get("error_handling") == "passed"
        results["statistics"]["errors_count"] = len(results["errors"])
        results["statistics"]["warnings_count"] = len(results["warnings"])
        
        logger.info(f"Step 11 error handling test completed. Passed: {results['test_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 11 error handling test: {str(e)}")
        results["errors"].append(f"Test error: {str(e)}")
        results["test_passed"] = False
    
    return results


def run_comprehensive_step11_tests(period: str = "202509A") -> Dict[str, Any]:
    """
    Run comprehensive Step 11 tests including real data and error handling.
    
    Args:
        period: Period label for testing (e.g., "202509A")
        
    Returns:
        Dictionary with comprehensive test results
    """
    logger.info(f"Starting comprehensive Step 11 tests for period {period}")
    
    comprehensive_results = {
        "step": 11,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "overall_passed": False,
        "test_suites": {},
        "summary": {}
    }
    
    # Run all test suites
    test_suites = {
        "real_data_test": test_step11_with_real_data,
        "error_handling_test": test_step11_error_handling
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
    
    logger.info(f"Comprehensive Step 11 tests completed. Overall passed: {comprehensive_results['overall_passed']}")
    
    return comprehensive_results


def run_step11_validation(period: str = "202508A", 
                         validate_inputs: bool = True) -> Dict[str, Any]:
    """
    Main function to run Step 11 validation
    
    Args:
        period: Period label for validation
        validate_inputs: Whether to validate input data
        
    Returns:
        Dictionary containing complete validation results
    """
    logger.info(f"Running Step 11 validation for period {period}")
    
    # Run comprehensive validation
    results = validate_step11_comprehensive(period)
    
    # Run input validation if requested
    if validate_inputs:
        input_results = validate_step11_inputs_comprehensive(period)
        results["input_validation"] = input_results
    
    return results


if __name__ == "__main__":
    # Run validation when script is executed directly
    import sys
    
    period = sys.argv[1] if len(sys.argv) > 1 else "202509A"
    test_type = sys.argv[2] if len(sys.argv) > 2 else "comprehensive"
    
    if test_type == "comprehensive":
        results = run_comprehensive_step11_tests(period)
        print(f"Comprehensive Step 11 test results:")
        print(f"  Period: {results['period']}")
        print(f"  Overall Passed: {results['overall_passed']}")
        print(f"  Success Rate: {results['summary']['success_rate']:.1f}%")
        print(f"  Passed Tests: {results['summary']['passed_tests']}/{results['summary']['total_tests']}")
    else:
        results = run_step11_validation(period)
        print(f"Step 11 validation results:")
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
