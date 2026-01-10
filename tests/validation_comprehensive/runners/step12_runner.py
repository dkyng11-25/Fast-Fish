"""
Step 12 Validation Runner: Sales Performance (Subcategory/SPU) with Real-Unit, Incremental Quantity Recommendations

This module provides comprehensive validation for Step 12 outputs including:
- Results file validation (store-level aggregated results)
- Details file validation (detailed opportunity information)
- Input data validation (clustering, store config, quantity data)
- Business logic validation (performance classification, positive quantities, Z-score logic)
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
    from ..schemas.step12_schemas import (
        Step12ResultsSchema,
        Step12DetailsSchema,
        Step12InputClusteringSchema,
        Step12InputStoreConfigSchema,
        Step12InputQuantitySchema,
        validate_step12_results,
        validate_step12_details,
        validate_step12_inputs,
        validate_positive_quantities,
        validate_performance_classification,
        validate_z_score_logic,
        validate_rule_flags_consistency
    )
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "schemas"))
    from step12_schemas import (
        Step12ResultsSchema,
        Step12DetailsSchema,
        Step12InputClusteringSchema,
        Step12InputStoreConfigSchema,
        Step12InputQuantitySchema,
        validate_step12_results,
        validate_step12_details,
        validate_step12_inputs,
        validate_positive_quantities,
        validate_performance_classification,
        validate_z_score_logic,
        validate_rule_flags_consistency
    )

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_step12_comprehensive(period: str = "202508A", 
                                 data_dir: str = "../output") -> Dict[str, Any]:
    """
    Comprehensive validation for Step 12: Sales Performance (Subcategory/SPU)
    
    Args:
        period: Period label for validation (e.g., "202508A")
        data_dir: Directory containing output files
        
    Returns:
        Dictionary containing validation results and statistics
    """
    logger.info(f"Starting Step 12 comprehensive validation for period {period}")
    
    results = {
        "step": 12,
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
        results_file = data_path / f"rule12_sales_performance_spu_results_{period}.csv"
        if not results_file.exists():
            results_file = data_path / "rule12_sales_performance_spu_results.csv"
        
        # Details file (try both legacy and period-labeled versions)
        details_file = data_path / f"rule12_sales_performance_spu_details_{period}.csv"
        if not details_file.exists():
            details_file = data_path / "rule12_sales_performance_spu_details.csv"
        
        # Summary file
        summary_file = data_path / f"rule12_sales_performance_spu_summary_{period}.md"
        if not summary_file.exists():
            summary_file = data_path / "rule12_sales_performance_spu_summary.md"
        
        # Validate results file
        if results_file.exists():
            logger.info(f"Validating results file: {results_file}")
            results_df = pd.read_csv(results_file)
            results["file_validation"]["results"] = validate_step12_results(results_df)
            results["statistics"]["results_rows"] = len(results_df)
            results["statistics"]["results_columns"] = len(results_df.columns)
        else:
            results["errors"].append(f"Results file not found: {results_file}")
            results["file_validation"]["results"] = False
        
        # Validate details file
        if details_file.exists():
            logger.info(f"Validating details file: {details_file}")
            details_df = pd.read_csv(details_file)
            results["file_validation"]["details"] = validate_step12_details(details_df)
            results["statistics"]["details_rows"] = len(details_df)
            results["statistics"]["details_columns"] = len(details_df.columns)
        else:
            results["errors"].append(f"Details file not found: {details_file}")
            results["file_validation"]["details"] = False
        
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
            business_logic_results = validate_step12_business_logic(results_df, details_df)
            results["business_logic_validation"] = business_logic_results
        
        # Overall validation status
        results["validation_passed"] = all([
            results["file_validation"]["results"],
            results["file_validation"]["details"]
        ]) and len(results["errors"]) == 0
        
        logger.info(f"Step 12 validation completed. Passed: {results['validation_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 12 validation: {str(e)}")
        results["errors"].append(f"Validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_step12_business_logic(results_df: pd.DataFrame, 
                                  details_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate Step 12 business logic and constraints
    
    Args:
        results_df: Results dataframe
        details_df: Details dataframe
        
    Returns:
        Dictionary containing business logic validation results
    """
    validation_results = {
        "positive_quantity_validation": {},
        "performance_classification": {},
        "z_score_validation": {},
        "rule_flags_consistency": {},
        "investment_validation": {},
        "fast_fish_validation": {},
        "opportunity_analysis": {}
    }
    
    try:
        # Positive quantity validation (critical for Step 12 - increases only)
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
        
        # Performance classification validation
        if "store_performance_level" in results_df.columns:
            performance_levels = results_df["store_performance_level"].value_counts()
            validation_results["performance_classification"] = {
                "level_counts": performance_levels.to_dict(),
                "unique_levels": len(performance_levels),
                "logic_validation": validate_performance_classification(results_df),
                "has_top_performers": "top_performer" in performance_levels.index,
                "has_opportunities": any(level in performance_levels.index for level in ["some_opportunity", "good_opportunity", "major_opportunity"])
            }
        
        # Z-score validation
        if "avg_opportunity_z_score" in results_df.columns:
            z_scores = results_df["avg_opportunity_z_score"].dropna()
            validation_results["z_score_validation"] = {
                "min_z_score": float(z_scores.min()),
                "max_z_score": float(z_scores.max()),
                "mean_z_score": float(z_scores.mean()),
                "std_z_score": float(z_scores.std()),
                "logic_validation": validate_z_score_logic(details_df),
                "valid_range": bool((z_scores >= -5).all() and (z_scores <= 5).all())
            }
        
        # Rule flags consistency validation
        validation_results["rule_flags_consistency"] = {
            "consistency_check": validate_rule_flags_consistency(results_df)
        }
        
        # Investment validation
        if "total_investment_required" in results_df.columns:
            investments = results_df["total_investment_required"].dropna()
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
        
        # Opportunity analysis validation
        if "opportunity_value" in details_df.columns:
            opportunity_values = details_df["opportunity_value"].dropna()
            validation_results["opportunity_analysis"] = {
                "total_opportunity_value": float(opportunity_values.sum()),
                "min_opportunity_value": float(opportunity_values.min()),
                "max_opportunity_value": float(opportunity_values.max()),
                "mean_opportunity_value": float(opportunity_values.mean()),
                "high_value_opportunities": int((opportunity_values >= opportunity_values.quantile(0.8)).sum())
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
        
        # Cluster-level validation
        if "cluster_id" in details_df.columns:
            unique_clusters = details_df["cluster_id"].nunique()
            validation_results["cluster_validation"] = {
                "unique_clusters": unique_clusters,
                "has_clusters": unique_clusters > 0
            }
        
    except Exception as e:
        logger.error(f"Error in business logic validation: {str(e)}")
        validation_results["error"] = str(e)
    
    return validation_results


def validate_step12_inputs_comprehensive(period: str = "202508A",
                                       data_dir: str = "../data",
                                       output_dir: str = "../output") -> Dict[str, Any]:
    """
    Comprehensive validation for Step 12 input data
    
    Args:
        period: Period label for validation
        data_dir: Directory containing input data files
        output_dir: Directory containing clustering results
        
    Returns:
        Dictionary containing input validation results
    """
    logger.info(f"Starting Step 12 input validation for period {period}")
    
    results = {
        "step": 12,
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
            results["file_validation"]["clustering"] = validate_step12_inputs(
                clustering_df, pd.DataFrame(), pd.DataFrame()
            )
            results["data_quality"]["clustering_rows"] = len(clustering_df)
            results["data_quality"]["clustering_columns"] = len(clustering_df.columns)
        else:
            results["errors"].append(f"Clustering file not found: {clustering_file}")
            results["file_validation"]["clustering"] = False
        
        # Check store config file
        store_config_file = data_path / f"store_config_{period}.csv"
        if store_config_file.exists():
            logger.info(f"Validating store config file: {store_config_file}")
            store_config_df = pd.read_csv(store_config_file)
            results["file_validation"]["store_config"] = True
            results["data_quality"]["store_config_rows"] = len(store_config_df)
            results["data_quality"]["store_config_columns"] = len(store_config_df.columns)
        else:
            results["warnings"].append(f"Store config file not found: {store_config_file}")
            results["file_validation"]["store_config"] = False
        
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
        # Store config and quantity files are optional for this validation
        results["validation_passed"] = results["file_validation"]["clustering"] and len(results["errors"]) == 0
        
        logger.info(f"Step 12 input validation completed. Passed: {results['validation_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 12 input validation: {str(e)}")
        results["errors"].append(f"Input validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def test_step12_with_real_data(period: str = "202509A") -> Dict[str, Any]:
    """
    Test Step 12 using real data files with comprehensive validation and progress tracking.
    
    Args:
        period: Period label for testing (e.g., "202509A")
        
    Returns:
        Dictionary with test results
    """
    import time
    start_time = time.time()
    
    logger.info(f"Starting Step 12 real data test for period {period}")
    print(f"🔄 Starting Step 12 real data test for period {period}")
    
    results = {
        "step": 12,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "test_passed": False,
        "errors": [],
        "warnings": [],
        "test_results": {},
        "statistics": {},
        "execution_time": 0
    }
    
    try:
        # Set environment variables
        os.environ['PIPELINE_TARGET_YYYYMM'] = period[:6]  # Extract YYYYMM
        os.environ['PIPELINE_TARGET_PERIOD'] = period[-1]  # Extract A or B
        os.environ['ANALYSIS_LEVEL'] = 'spu'
        os.environ['SEASONAL_BLENDING'] = 'false'  # Disable seasonal blending
        
        # Run step12 from project root
        project_root = Path(__file__).parent.parent.parent.parent
        original_cwd = os.getcwd()
        
        try:
            os.chdir(project_root)
            print(f"📁 Changed to project root: {project_root}")
            
            # Add both project root and src to path for imports
            project_root_str = str(project_root)
            src_path = str(project_root / "src")
            sys.path.insert(0, project_root_str)  # For 'src' imports
            sys.path.insert(0, src_path)  # For direct module imports
            print(f"🔧 Added paths to sys.path")
            
            from step12_sales_performance_rule import main as step12_main
            print(f"✅ Imported Step 12 module")
            
            # Step12 will run and create sales performance results
            print(f"🚀 Starting Step 12 execution...")
            execution_start = time.time()
            
            try:
                step12_main(testing_mode=False, period_label=period)
                execution_time = time.time() - execution_start
                results["test_results"]["execution"] = "completed"
                results["statistics"]["execution_time_seconds"] = execution_time
                print(f"✅ Step 12 execution completed in {execution_time:.2f} seconds")
            except Exception as e:
                execution_time = time.time() - execution_start
                results["errors"].append(f"Error during execution: {str(e)}")
                results["test_results"]["execution"] = "failed"
                results["statistics"]["execution_time_seconds"] = execution_time
                print(f"❌ Step 12 execution failed after {execution_time:.2f} seconds: {str(e)}")
        finally:
            os.chdir(original_cwd)
        
        # Verify output files were created
        project_output_dir = project_root / "output"
        print(f"🔍 Checking for output files in {project_output_dir}")
        
        # Look for the actual files created by Step 12
        results_files = list(project_output_dir.glob(f"rule12_sales_performance_spu_results_{period}*.csv"))
        details_files = list(project_output_dir.glob(f"rule12_sales_performance_spu_details_{period}*.csv"))
        summary_files = list(project_output_dir.glob(f"rule12_sales_performance_spu_summary_{period}*.md"))
        
        # Also check for legacy files without period suffix
        if not results_files:
            results_files = list(project_output_dir.glob("rule12_sales_performance_spu_results.csv"))
        if not details_files:
            details_files = list(project_output_dir.glob("rule12_sales_performance_spu_details.csv"))
        if not summary_files:
            summary_files = list(project_output_dir.glob("rule12_sales_performance_spu_summary.md"))
        
        if results_files:
            results["test_results"]["results_file_created"] = True
            results_df = pd.read_csv(results_files[0])
            results["statistics"]["results_records"] = len(results_df)
            print(f"✅ Results file found: {results_files[0]} ({len(results_df)} records)")
        else:
            results["warnings"].append("Results file not created")
            results["test_results"]["results_file_created"] = False
            print(f"⚠️  Results file not found")
        
        if details_files:
            results["test_results"]["details_file_created"] = True
            details_df = pd.read_csv(details_files[0])
            results["statistics"]["details_records"] = len(details_df)
            print(f"✅ Details file found: {details_files[0]} ({len(details_df)} records)")
        else:
            results["warnings"].append("Details file not created")
            results["test_results"]["details_file_created"] = False
            print(f"⚠️  Details file not found")
        
        if summary_files:
            results["test_results"]["summary_file_created"] = True
            results["statistics"]["summary_file_size"] = os.path.getsize(summary_files[0])
            print(f"✅ Summary file found: {summary_files[0]} ({os.path.getsize(summary_files[0])} bytes)")
        else:
            results["warnings"].append("Summary file not created")
            results["test_results"]["summary_file_created"] = False
            print(f"⚠️  Summary file not found")
        
        # Overall test status
        results["test_passed"] = (
            results["test_results"].get("execution") == "completed" and
            results["test_results"].get("results_file_created", False) and
            results["test_results"].get("details_file_created", False)
        )
        
        total_time = time.time() - start_time
        results["execution_time"] = total_time
        
        if results["test_passed"]:
            print(f"🎉 Step 12 real data test PASSED in {total_time:.2f} seconds")
        else:
            print(f"❌ Step 12 real data test FAILED in {total_time:.2f} seconds")
        
        logger.info(f"Step 12 real data test completed. Passed: {results['test_passed']}")
        
    except Exception as e:
        total_time = time.time() - start_time
        results["execution_time"] = total_time
        logger.error(f"Error during Step 12 real data test: {str(e)}")
        results["errors"].append(f"Test error: {str(e)}")
        results["test_passed"] = False
        print(f"💥 Step 12 test error after {total_time:.2f} seconds: {str(e)}")
    
    return results


def test_step12_error_handling(period: str = "202509A") -> Dict[str, Any]:
    """
    Test Step 12 error handling when input files are missing.
    
    Args:
        period: Period label for testing (e.g., "202509A")
        
    Returns:
        Dictionary with test results
    """
    import time
    start_time = time.time()
    
    logger.info(f"Starting Step 12 error handling test for period {period}")
    print(f"🔄 Starting Step 12 error handling test for period {period}")
    
    results = {
        "step": 12,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "test_passed": False,
        "errors": [],
        "warnings": [],
        "test_results": {},
        "statistics": {},
        "execution_time": 0
    }
    
    try:
        # Set environment variables
        os.environ['PIPELINE_TARGET_YYYYMM'] = period[:6]
        os.environ['PIPELINE_TARGET_PERIOD'] = period[-1]
        os.environ['ANALYSIS_LEVEL'] = 'spu'
        os.environ['SEASONAL_BLENDING'] = 'false'
        
        # Temporarily move input files to test error handling
        project_root = Path(__file__).parent.parent.parent.parent
        original_cwd = os.getcwd()
        
        # Backup and remove input files
        input_files = [
            "data/api_data/complete_spu_sales.csv",
            "data/api_data/store_config.csv",
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
                    print(f"📦 Backed up: {file_path}")
            
            # Run step12 from project root
            try:
                os.chdir(project_root)
                
                # Add both project root and src to path for imports
                project_root_str = str(project_root)
                src_path = str(project_root / "src")
                sys.path.insert(0, project_root_str)  # For 'src' imports
                sys.path.insert(0, src_path)  # For direct module imports
                
                from step12_sales_performance_rule import main as step12_main
                
                # This should raise an error when input files are missing
                print(f"🚀 Testing error handling...")
                try:
                    step12_main(testing_mode=False, period_label=period)
                    results["errors"].append("Expected error but execution completed successfully")
                    results["test_results"]["error_handling"] = "failed"
                    print(f"❌ Expected error but execution completed successfully")
                except FileNotFoundError as e:
                    results["test_results"]["error_handling"] = "passed"
                    results["warnings"].append("Correctly raised FileNotFoundError for missing input files")
                    print(f"✅ Correctly raised FileNotFoundError for missing input files")
                except Exception as e:
                    results["test_results"]["error_handling"] = "passed"
                    results["warnings"].append(f"Correctly raised error for missing input files: {type(e).__name__}")
                    print(f"✅ Correctly raised error for missing input files: {type(e).__name__}")
            finally:
                os.chdir(original_cwd)
        finally:
            # Restore backed up files
            for src, backup in backed_up_files:
                if backup.exists():
                    shutil.move(str(backup), str(src))
                    print(f"🔄 Restored: {src.name}")
        
        # Overall test status
        results["test_passed"] = results["test_results"].get("error_handling") == "passed"
        results["statistics"]["errors_count"] = len(results["errors"])
        results["statistics"]["warnings_count"] = len(results["warnings"])
        
        total_time = time.time() - start_time
        results["execution_time"] = total_time
        
        if results["test_passed"]:
            print(f"🎉 Step 12 error handling test PASSED in {total_time:.2f} seconds")
        else:
            print(f"❌ Step 12 error handling test FAILED in {total_time:.2f} seconds")
        
        logger.info(f"Step 12 error handling test completed. Passed: {results['test_passed']}")
        
    except Exception as e:
        total_time = time.time() - start_time
        results["execution_time"] = total_time
        logger.error(f"Error during Step 12 error handling test: {str(e)}")
        results["errors"].append(f"Test error: {str(e)}")
        results["test_passed"] = False
        print(f"💥 Step 12 error handling test error after {total_time:.2f} seconds: {str(e)}")
    
    return results


def run_comprehensive_step12_tests(period: str = "202509A") -> Dict[str, Any]:
    """
    Run comprehensive Step 12 tests including real data and error handling with progress tracking.
    
    Args:
        period: Period label for testing (e.g., "202509A")
        
    Returns:
        Dictionary with comprehensive test results
    """
    import time
    start_time = time.time()
    
    logger.info(f"Starting comprehensive Step 12 tests for period {period}")
    print(f"🚀 Starting comprehensive Step 12 tests for period {period}")
    print(f"⏱️  Estimated total time: 2-5 minutes (based on data size)")
    
    comprehensive_results = {
        "step": 12,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "overall_passed": False,
        "test_suites": {},
        "summary": {},
        "total_execution_time": 0
    }
    
    # Run all test suites
    test_suites = {
        "real_data_test": test_step12_with_real_data,
        "error_handling_test": test_step12_error_handling
    }
    
    passed_tests = 0
    total_tests = len(test_suites)
    
    for i, (suite_name, test_function) in enumerate(test_suites.items(), 1):
        print(f"\n📋 Running test suite {i}/{total_tests}: {suite_name}")
        suite_start = time.time()
        
        logger.info(f"Running {suite_name}...")
        try:
            suite_results = test_function(period)
            comprehensive_results["test_suites"][suite_name] = suite_results
            if suite_results.get("test_passed", False):
                passed_tests += 1
                print(f"✅ {suite_name} PASSED")
            else:
                print(f"❌ {suite_name} FAILED")
            
            suite_time = time.time() - suite_start
            print(f"⏱️  {suite_name} completed in {suite_time:.2f} seconds")
            
        except Exception as e:
            suite_time = time.time() - suite_start
            logger.error(f"Error running {suite_name}: {str(e)}")
            comprehensive_results["test_suites"][suite_name] = {
                "test_passed": False,
                "errors": [f"Test suite error: {str(e)}"],
                "execution_time": suite_time
            }
            print(f"💥 {suite_name} ERROR after {suite_time:.2f} seconds: {str(e)}")
    
    # Calculate overall results
    comprehensive_results["overall_passed"] = passed_tests == total_tests
    total_time = time.time() - start_time
    comprehensive_results["total_execution_time"] = total_time
    comprehensive_results["summary"] = {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": total_tests - passed_tests,
        "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
        "total_execution_time": total_time
    }
    
    print(f"\n🏁 Comprehensive Step 12 tests completed in {total_time:.2f} seconds")
    print(f"📊 Overall passed: {comprehensive_results['overall_passed']}")
    print(f"📈 Success rate: {comprehensive_results['summary']['success_rate']:.1f}%")
    print(f"✅ Passed tests: {passed_tests}/{total_tests}")
    
    logger.info(f"Comprehensive Step 12 tests completed. Overall passed: {comprehensive_results['overall_passed']}")
    
    return comprehensive_results


def run_step12_validation(period: str = "202508A", 
                         validate_inputs: bool = True) -> Dict[str, Any]:
    """
    Main function to run Step 12 validation
    
    Args:
        period: Period label for validation
        validate_inputs: Whether to validate input data
        
    Returns:
        Dictionary containing complete validation results
    """
    logger.info(f"Running Step 12 validation for period {period}")
    
    # Run comprehensive validation
    results = validate_step12_comprehensive(period)
    
    # Run input validation if requested
    if validate_inputs:
        input_results = validate_step12_inputs_comprehensive(period)
        results["input_validation"] = input_results
    
    return results


if __name__ == "__main__":
    # Run validation when script is executed directly
    import sys
    
    period = sys.argv[1] if len(sys.argv) > 1 else "202509A"
    test_type = sys.argv[2] if len(sys.argv) > 2 else "comprehensive"
    
    if test_type == "comprehensive":
        results = run_comprehensive_step12_tests(period)
        print(f"\n📊 Comprehensive Step 12 test results:")
        print(f"  Period: {results['period']}")
        print(f"  Overall Passed: {results['overall_passed']}")
        print(f"  Success Rate: {results['summary']['success_rate']:.1f}%")
        print(f"  Passed Tests: {results['summary']['passed_tests']}/{results['summary']['total_tests']}")
        print(f"  Total Execution Time: {results['total_execution_time']:.2f} seconds")
    else:
        results = run_step12_validation(period)
        print(f"Step 12 validation results:")
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