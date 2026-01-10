"""
Step 8 Validation Runner: Imbalanced Allocation Rule with Quantity Rebalancing

This module provides comprehensive validation for Step 8 outputs including:
- Results file validation (store-level aggregated results)
- Cases file validation (detailed case information)
- Z-score analysis file validation (cluster-level statistics)
- Input data validation (clustering, store config, quantity data)
- Business logic validation (z-score calculations, quantity constraints)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime
import os

# Import schemas - handle both direct and relative imports
try:
    from ..schemas.step8_schemas import (
        Step8ResultsSchema,
        Step8CasesSchema,
        Step8ZScoreAnalysisSchema,
        Step8InputClusteringSchema,
        Step8InputStoreConfigSchema,
        Step8InputQuantitySchema,
        validate_step8_results,
        validate_step8_cases,
        validate_step8_z_score_analysis,
        validate_step8_inputs
    )
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "schemas"))
    from step8_schemas import (
        Step8ResultsSchema,
        Step8CasesSchema,
        Step8ZScoreAnalysisSchema,
        Step8InputClusteringSchema,
        Step8InputStoreConfigSchema,
        Step8InputQuantitySchema,
        validate_step8_results,
        validate_step8_cases,
        validate_step8_z_score_analysis,
        validate_step8_inputs
    )

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_step8_comprehensive(period: str = "202509A", 
                                analysis_level: str = "spu",
                                output_dir: str = "output") -> Dict[str, Any]:
    """
    Comprehensive validation for Step 8: Imbalanced Allocation Rule
    
    Args:
        period: Period label for validation (e.g., "202509A")
        analysis_level: Analysis level ("spu" or "subcategory")
        output_dir: Directory containing output files (relative to project root)
        
    Returns:
        Dictionary containing validation results and statistics
    """
    logger.info(f"Starting Step 8 comprehensive validation for period {period}, level {analysis_level}")
    
    results = {
        "step": 8,
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
        output_path = project_root / output_dir
        
        # Results file
        results_file = output_path / f"rule8_imbalanced_{analysis_level}_{period}_results.csv"
        if not results_file.exists():
            results_file = output_path / f"rule8_imbalanced_{analysis_level}_results.csv"
        
        # Cases file
        cases_file = output_path / f"rule8_imbalanced_{analysis_level}_{period}_cases.csv"
        if not cases_file.exists():
            cases_file = output_path / f"rule8_imbalanced_{analysis_level}_cases.csv"
        
        # Z-score analysis file
        zscore_file = output_path / f"rule8_imbalanced_{analysis_level}_{period}_z_score_analysis.csv"
        if not zscore_file.exists():
            zscore_file = output_path / f"rule8_imbalanced_{analysis_level}_z_score_analysis.csv"
        
        # Summary file
        summary_file = output_path / f"rule8_imbalanced_{analysis_level}_{period}_summary.md"
        if not summary_file.exists():
            summary_file = output_path / f"rule8_imbalanced_{analysis_level}_summary.md"
        
        # Validate results file
        if results_file.exists():
            logger.info(f"Validating results file: {results_file}")
            results_df = pd.read_csv(results_file)
            # Normalize column names: map alternate names to expected schema fields
            if "Cluster" in results_df.columns and "cluster_id" not in results_df.columns:
                results_df = results_df.rename(columns={"Cluster": "cluster_id"})
            if "Str_code" in results_df.columns and "str_code" not in results_df.columns:
                results_df = results_df.rename(columns={"Str_code": "str_code"})
            results["file_validation"]["results"] = validate_step8_results(results_df)
            results["statistics"]["results_rows"] = len(results_df)
            results["statistics"]["results_columns"] = len(results_df.columns)
        else:
            results["errors"].append(f"Results file not found: {results_file}")
            results["file_validation"]["results"] = False
        
        # Validate cases file
        if cases_file.exists():
            logger.info(f"Validating cases file: {cases_file}")
            cases_df = pd.read_csv(cases_file)
            # Note: cases file uses 'Cluster' not 'cluster_id' - schema expects 'Cluster'
            if "Str_code" in cases_df.columns and "str_code" not in cases_df.columns:
                cases_df = cases_df.rename(columns={"Str_code": "str_code"})
            results["file_validation"]["cases"] = validate_step8_cases(cases_df)
            results["statistics"]["cases_rows"] = len(cases_df)
            results["statistics"]["cases_columns"] = len(cases_df.columns)
        else:
            results["errors"].append(f"Cases file not found: {cases_file}")
            results["file_validation"]["cases"] = False
        
        # Validate z-score analysis file
        if zscore_file.exists():
            logger.info(f"Validating z-score analysis file: {zscore_file}")
            zscore_df = pd.read_csv(zscore_file)
            # Note: z-score file uses 'Cluster' not 'cluster_id' - schema expects 'Cluster'
            if "Str_code" in zscore_df.columns and "str_code" not in zscore_df.columns:
                zscore_df = zscore_df.rename(columns={"Str_code": "str_code"})
            results["file_validation"]["zscore_analysis"] = validate_step8_z_score_analysis(zscore_df)
            results["statistics"]["zscore_rows"] = len(zscore_df)
            results["statistics"]["zscore_columns"] = len(zscore_df.columns)
        else:
            results["errors"].append(f"Z-score analysis file not found: {zscore_file}")
            results["file_validation"]["zscore_analysis"] = False
        
        # Check summary file
        if summary_file.exists():
            logger.info(f"Summary file found: {summary_file}")
            results["file_validation"]["summary"] = True
        else:
            results["warnings"].append(f"Summary file not found: {summary_file}")
            results["file_validation"]["summary"] = False
        
        # Business logic validation if data is available
        if results["file_validation"]["results"] and results["file_validation"]["cases"]:
            logger.info("Performing business logic validation")
            business_logic_results = validate_step8_business_logic(results_df, cases_df, analysis_level)
            results["business_logic_validation"] = business_logic_results
        
        # Overall validation status
        results["validation_passed"] = all([
            results["file_validation"]["results"],
            results["file_validation"]["cases"],
            results["file_validation"]["zscore_analysis"]
        ]) and len(results["errors"]) == 0
        
        logger.info(f"Step 8 validation completed. Passed: {results['validation_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 8 validation: {str(e)}")
        results["errors"].append(f"Validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_step8_business_logic(results_df: pd.DataFrame, 
                                 cases_df: pd.DataFrame, 
                                 analysis_level: str) -> Dict[str, Any]:
    """
    Validate Step 8 business logic and constraints
    
    Args:
        results_df: Results dataframe
        cases_df: Cases dataframe
        analysis_level: Analysis level ("spu" or "subcategory")
        
    Returns:
        Dictionary containing business logic validation results
    """
    validation_results = {
        "z_score_validation": {},
        "quantity_constraints": {},
        "investment_neutrality": {},
        "severity_tier_validation": {},
        "cluster_consistency": {}
    }
    
    try:
        # Z-score validation
        if "z_score" in results_df.columns:
            z_scores = results_df["z_score"].dropna()
            validation_results["z_score_validation"] = {
                "min_z_score": float(z_scores.min()),
                "max_z_score": float(z_scores.max()),
                "mean_z_score": float(z_scores.mean()),
                "std_z_score": float(z_scores.std()),
                "valid_range": bool((z_scores >= -10).all() and (z_scores <= 10).all())
            }
        
        # Quantity constraints validation
        if "recommended_quantity_change" in results_df.columns:
            quantity_changes = results_df["recommended_quantity_change"].dropna()
            validation_results["quantity_constraints"] = {
                "min_change": float(quantity_changes.min()),
                "max_change": float(quantity_changes.max()),
                "mean_change": float(quantity_changes.mean()),
                "total_change": float(quantity_changes.sum()),
                "positive_changes": int((quantity_changes > 0).sum()),
                "negative_changes": int((quantity_changes < 0).sum()),
                "zero_changes": int((quantity_changes == 0).sum())
            }
        
        # Investment neutrality validation
        if "investment_required" in results_df.columns:
            investments = results_df["investment_required"].dropna()
            total_investment = investments.sum()
            validation_results["investment_neutrality"] = {
                "total_investment": float(total_investment),
                "is_neutral": bool(abs(total_investment) < 0.01),  # Allow small floating point errors
                "min_investment": float(investments.min()),
                "max_investment": float(investments.max())
            }
        
        # Severity tier validation
        if "severity_tier" in results_df.columns:
            severity_tiers = results_df["severity_tier"].value_counts()
            validation_results["severity_tier_validation"] = {
                "tier_counts": severity_tiers.to_dict(),
                "unique_tiers": len(severity_tiers),
                "has_high_severity": "high" in severity_tiers.index.str.lower()
            }
        
        # Cluster consistency validation
        if "cluster_id" in results_df.columns and "cluster_id" in cases_df.columns:
            results_clusters = set(results_df["cluster_id"].unique())
            cases_clusters = set(cases_df["cluster_id"].unique())
            validation_results["cluster_consistency"] = {
                "results_clusters": len(results_clusters),
                "cases_clusters": len(cases_clusters),
                "clusters_match": results_clusters == cases_clusters,
                "missing_in_cases": list(results_clusters - cases_clusters),
                "extra_in_cases": list(cases_clusters - results_clusters)
            }
        
        # Analysis level specific validation
        if analysis_level == "spu":
            # SPU-specific constraints
            if "spu_code" in cases_df.columns:
                unique_spus = cases_df["spu_code"].nunique()
                validation_results["spu_validation"] = {
                    "unique_spus": unique_spus,
                    "has_spu_codes": unique_spus > 0
                }
        
        elif analysis_level == "subcategory":
            # Subcategory-specific validation
            if "sub_cate_name" in cases_df.columns:
                unique_subcats = cases_df["sub_cate_name"].nunique()
                validation_results["subcategory_validation"] = {
                    "unique_subcategories": unique_subcats,
                    "has_subcategories": unique_subcats > 0
                }
        
    except Exception as e:
        logger.error(f"Error in business logic validation: {str(e)}")
        validation_results["error"] = str(e)
    
    return validation_results


def validate_step8_inputs_comprehensive(period: str = "202509A",
                                      data_dir: str = "data",
                                      output_dir: str = "output") -> Dict[str, Any]:
    """
    Comprehensive validation for Step 8 input data
    
    Args:
        period: Period label for validation
        data_dir: Directory containing input data files (relative to project root)
        output_dir: Directory containing clustering results (relative to project root)
        
    Returns:
        Dictionary containing input validation results
    """
    logger.info(f"Starting Step 8 input validation for period {period}")
    
    results = {
        "step": 8,
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
        data_path = project_root / data_dir
        output_path = project_root / output_dir
        
        # Check clustering results
        clustering_file = output_path / "clustering_results_spu.csv"
        if not clustering_file.exists():
            clustering_file = output_path / "clustering_results_subcategory.csv"
        
        if clustering_file.exists():
            logger.info(f"Validating clustering file: {clustering_file}")
            clustering_df = pd.read_csv(clustering_file)
            results["file_validation"]["clustering"] = validate_step8_inputs(
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
        
        logger.info(f"Step 8 input validation completed. Passed: {results['validation_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 8 input validation: {str(e)}")
        results["errors"].append(f"Input validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def run_step8_validation(period: str = "202509A", 
                        analysis_level: str = "spu",
                        validate_inputs: bool = True) -> Dict[str, Any]:
    """
    Main function to run Step 8 validation
    
    Args:
        period: Period label for validation
        analysis_level: Analysis level ("spu" or "subcategory")
        validate_inputs: Whether to validate input data
        
    Returns:
        Dictionary containing complete validation results
    """
    logger.info(f"Running Step 8 validation for period {period}, level {analysis_level}")
    
    # Change to project root directory
    project_root = Path(__file__).parent.parent.parent.parent
    original_cwd = os.getcwd()
    os.chdir(project_root)
    
    try:
        # Run comprehensive validation
        results = validate_step8_comprehensive(period, analysis_level)
        
        # Run input validation if requested
        if validate_inputs:
            input_results = validate_step8_inputs_comprehensive(period)
            results["input_validation"] = input_results
        
        return results
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    # Run validation when script is executed directly
    import sys
    
    period = sys.argv[1] if len(sys.argv) > 1 else "202509A"
    analysis_level = sys.argv[2] if len(sys.argv) > 2 else "spu"
    
    results = run_step8_validation(period, analysis_level)
    
    print(f"Step 8 validation results:")
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
