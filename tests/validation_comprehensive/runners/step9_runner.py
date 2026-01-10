"""
Step 9 Validation Runner: Below Minimum Rule with Positive-Only Quantity Increases

This module provides comprehensive validation for Step 9 outputs including:
- Results file validation (store-level aggregated results)
- Opportunities file validation (detailed opportunity information)
- Summary file validation (aggregated statistics)
- Input data validation (clustering, store config, quantity data)
- Business logic validation (positive-only quantities, below minimum detection)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
import os # Added os import

# Import schemas - handle both direct and relative imports
try:
    from ..schemas.step9_schemas import (
        Step9ResultsSchema,
        Step9OpportunitiesSchema,
        Step9SummarySchema,
        Step9InputClusteringSchema,
        Step9InputStoreConfigSchema,
        Step9InputQuantitySchema,
        validate_step9_results,
        validate_step9_opportunities,
        validate_step9_summary,
        validate_step9_inputs,
        validate_positive_only_quantities,
        validate_below_minimum_logic
    )
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "schemas"))
    from step9_schemas import (
        Step9ResultsSchema,
        Step9OpportunitiesSchema,
        Step9SummarySchema,
        Step9InputClusteringSchema,
        Step9InputStoreConfigSchema,
        Step9InputQuantitySchema,
        validate_step9_results,
        validate_step9_opportunities,
        validate_step9_summary,
        validate_step9_inputs,
        validate_positive_only_quantities,
        validate_below_minimum_logic
    )

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_step9_comprehensive(period: str = "202509A", # Changed default period
                                analysis_level: str = "spu",
                                output_dir: str = "output") -> Dict[str, Any]: # Changed data_dir to output_dir, default to "output"
    """
    Comprehensive validation for Step 9: Below Minimum Rule
    
    Args:
        period: Period label for validation (e.g., "202509A")
        analysis_level: Analysis level ("spu" or "subcategory")
        output_dir: Directory containing output files (relative to project root)
        
    Returns:
        Dictionary containing validation results and statistics
    """
    logger.info(f"Starting Step 9 comprehensive validation for period {period}, level {analysis_level}")
    
    results = {
        "step": 9,
        "period": period,
        "analysis_level": analysis_level,
        "timestamp": datetime.now().isoformat(),
        "validation_passed": False,
        "errors": [],
        "warnings": [],
        "statistics": {},
        "file_validation": {},
        "business_logic_validation": {}
    }
    
    try:
        # Resolve paths relative to project root
        project_root = Path(__file__).parent.parent.parent.parent
        output_path = project_root / output_dir # Corrected path resolution
        
        # Results file
        results_file = output_path / f"rule9_below_minimum_spu_sellthrough_results_{period}.csv"
        if not results_file.exists():
            results_file = output_path / f"rule9_below_minimum_spu_sellthrough_results.csv"
        
        # Opportunities file
        opportunities_file = output_path / f"rule9_below_minimum_spu_sellthrough_opportunities_{period}.csv"
        if not opportunities_file.exists():
            opportunities_file = output_path / f"rule9_below_minimum_spu_sellthrough_opportunities.csv"
        
        # Summary file
        summary_file = output_path / f"rule9_below_minimum_spu_sellthrough_summary_{period}.md"
        if not summary_file.exists():
            summary_file = output_path / f"rule9_below_minimum_spu_sellthrough_summary.md"
        
        # Validate results file
        if results_file.exists():
            logger.info(f"Validating results file: {results_file}")
            results_df = pd.read_csv(results_file)
            results["file_validation"]["results"] = validate_step9_results(results_df)
            results["statistics"]["results_rows"] = len(results_df)
            results["statistics"]["results_columns"] = len(results_df.columns)
        else:
            results["errors"].append(f"Results file not found: {results_file}")
            results["file_validation"]["results"] = False
        
        # Validate opportunities file
        if opportunities_file.exists():
            logger.info(f"Validating opportunities file: {opportunities_file}")
            opportunities_df = pd.read_csv(opportunities_file)
            results["file_validation"]["opportunities"] = validate_step9_opportunities(opportunities_df)
            results["statistics"]["opportunities_rows"] = len(opportunities_df)
            results["statistics"]["opportunities_columns"] = len(opportunities_df.columns)
        else:
            results["errors"].append(f"Opportunities file not found: {opportunities_file}")
            results["file_validation"]["opportunities"] = False
        
        # Check summary file
        if summary_file.exists():
            logger.info(f"Summary file found: {summary_file}")
            results["file_validation"]["summary"] = True
        else:
            results["warnings"].append(f"Summary file not found: {summary_file}")
            results["file_validation"]["summary"] = False
        
        # Business logic validation if data is available
        if results["file_validation"]["results"] and results["file_validation"]["opportunities"]:
            logger.info("Performing business logic validation")
            business_logic_results = validate_step9_business_logic(results_df, opportunities_df, analysis_level)
            results["business_logic_validation"] = business_logic_results
        
        # Overall validation status
        results["validation_passed"] = all([
            results["file_validation"]["results"],
            results["file_validation"]["opportunities"]
        ]) and len(results["errors"]) == 0
        
        logger.info(f"Step 9 validation completed. Passed: {results['validation_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 9 validation: {str(e)}")
        results["errors"].append(f"Validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_step9_business_logic(results_df: pd.DataFrame, 
                                 opportunities_df: pd.DataFrame, 
                                 analysis_level: str) -> Dict[str, Any]:
    """
    Validate Step 9 business logic and constraints
    
    Args:
        results_df: Results dataframe
        opportunities_df: Opportunities dataframe
        analysis_level: Analysis level ("spu" or "subcategory")
        
    Returns:
        Dictionary containing business logic validation results
    """
    validation_results = {
        "positive_quantity_validation": {},
        "below_minimum_detection": {},
        "unit_rate_validation": {},
        "investment_calculation": {},
        "severity_tier_validation": {},
        "fast_fish_validation": {}
    }
    
    try:
        # Positive quantity validation (critical for Step 9)
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
        
        # Below minimum detection validation
        if "below_minimum" in results_df.columns:
            below_min_cases = results_df[results_df["below_minimum"] == True]
            validation_results["below_minimum_detection"] = {
                "total_below_minimum": len(below_min_cases),
                "below_minimum_percentage": len(below_min_cases) / len(results_df) * 100,
                "logic_validation": validate_below_minimum_logic(results_df)
            }
        
        # Unit rate validation
        if "unit_rate" in results_df.columns and "minimum_unit_rate" in results_df.columns:
            unit_rates = results_df["unit_rate"].dropna()
            min_rates = results_df["minimum_unit_rate"].dropna()
            validation_results["unit_rate_validation"] = {
                "min_unit_rate": float(unit_rates.min()),
                "max_unit_rate": float(unit_rates.max()),
                "mean_unit_rate": float(unit_rates.mean()),
                "min_threshold": float(min_rates.min()),
                "max_threshold": float(min_rates.max()),
                "mean_threshold": float(min_rates.mean()),
                "below_threshold_count": int((unit_rates < min_rates).sum())
            }
        
        # Investment calculation validation
        if "investment_required" in results_df.columns and "unit_price" in results_df.columns:
            investments = results_df["investment_required"].dropna()
            unit_prices = results_df["unit_price"].dropna()
            validation_results["investment_calculation"] = {
                "total_investment": float(investments.sum()),
                "min_investment": float(investments.min()),
                "max_investment": float(investments.max()),
                "mean_investment": float(investments.mean()),
                "min_unit_price": float(unit_prices.min()),
                "max_unit_price": float(unit_prices.max()),
                "mean_unit_price": float(unit_prices.mean())
            }
        
        # Severity tier validation
        if "severity_tier" in results_df.columns:
            severity_tiers = results_df["severity_tier"].value_counts()
            validation_results["severity_tier_validation"] = {
                "tier_counts": severity_tiers.to_dict(),
                "unique_tiers": len(severity_tiers),
                "has_high_severity": "high" in severity_tiers.index.str.lower()
            }
        
        # Fast Fish validation status
        if "validation_status" in opportunities_df.columns:
            validation_status = opportunities_df["validation_status"].value_counts()
            validation_results["fast_fish_validation"] = {
                "status_counts": validation_status.to_dict(),
                "total_validated": len(opportunities_df[opportunities_df["validation_status"].notna()]),
                "validation_coverage": len(opportunities_df[opportunities_df["validation_status"].notna()]) / len(opportunities_df) * 100
            }
        
        # Analysis level specific validation
        if analysis_level == "spu":
            # SPU-specific constraints
            if "spu_code" in opportunities_df.columns:
                unique_spus = opportunities_df["spu_code"].nunique()
                validation_results["spu_validation"] = {
                    "unique_spus": unique_spus,
                    "has_spu_codes": unique_spus > 0
                }
        
        elif analysis_level == "subcategory":
            # Subcategory-specific validation
            if "sub_cate_name" in opportunities_df.columns:
                unique_subcats = opportunities_df["sub_cate_name"].nunique()
                validation_results["subcategory_validation"] = {
                    "unique_subcategories": unique_subcats,
                    "has_subcategories": unique_subcats > 0
                }
        
    except Exception as e:
        logger.error(f"Error in business logic validation: {str(e)}")
        validation_results["error"] = str(e)
    
    return validation_results


def validate_step9_inputs_comprehensive(period: str = "202509A", # Changed default period
                                      data_dir: str = "data", # Changed data_dir to "data"
                                      output_dir: str = "output") -> Dict[str, Any]: # Changed output_dir to "output"
    """
    Comprehensive validation for Step 9 input data
    
    Args:
        period: Period label for validation
        data_dir: Directory containing input data files (relative to project root)
        output_dir: Directory containing clustering results (relative to project root)
        
    Returns:
        Dictionary containing input validation results
    """
    logger.info(f"Starting Step 9 input validation for period {period}")
    
    results = {
        "step": 9,
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
        data_path = project_root / data_dir # Corrected path resolution
        output_path = project_root / output_dir # Corrected path resolution
        
        # Check clustering results
        clustering_file = output_path / "clustering_results_spu.csv"
        if not clustering_file.exists():
            clustering_file = output_path / "clustering_results_subcategory.csv"
        
        if clustering_file.exists():
            logger.info(f"Validating clustering file: {clustering_file}")
            clustering_df = pd.read_csv(clustering_file)
            results["file_validation"]["clustering"] = validate_step9_inputs(
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
        
        logger.info(f"Step 9 input validation completed. Passed: {results['validation_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 9 input validation: {str(e)}")
        results["errors"].append(f"Input validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def run_step9_validation(period: str = "202509A", # Changed default period
                        analysis_level: str = "spu",
                        validate_inputs: bool = True) -> Dict[str, Any]:
    """
    Main function to run Step 9 validation
    
    Args:
        period: Period label for validation
        analysis_level: Analysis level ("spu" or "subcategory")
        validate_inputs: Whether to validate input data
        
    Returns:
        Dictionary containing complete validation results
    """
    logger.info(f"Running Step 9 validation for period {period}, level {analysis_level}")
    
    # Change to project root directory
    project_root = Path(__file__).parent.parent.parent.parent
    original_cwd = os.getcwd()
    os.chdir(project_root)
    
    try:
        # Run comprehensive validation
        results = validate_step9_comprehensive(period, analysis_level)
        
        # Run input validation if requested
        if validate_inputs:
            input_results = validate_step9_inputs_comprehensive(period)
            results["input_validation"] = input_results
        
        return results
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    # Run validation when script is executed directly
    import sys
    
    period = sys.argv[1] if len(sys.argv) > 1 else "202509A"
    analysis_level = sys.argv[2] if len(sys.argv) > 2 else "spu"
    
    results = run_step9_validation(period, analysis_level)
    
    print(f"Step 9 validation results:")
    print(f"  Period: {results['period']}")
    print(f"  Analysis Level: {results['analysis_level']}")
    print(f"  Validation Passed: {results['validation_passed']}")
    print(f"  Errors: {len(results['errors'])}")
    print(f"  Warnings: {len(results['warnings'])}")
    
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    if results['warnings']:
        print("\nWarnings:")
        for warning in results['warnings']:
            print(f"  - {warning}")
