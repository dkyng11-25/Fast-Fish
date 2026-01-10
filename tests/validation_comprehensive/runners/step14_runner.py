"""
Step 14 Validation Runner: Enhanced Fast Fish Format

This module provides comprehensive validation for Step 14 Fast Fish format outputs,
ensuring complete outputFormat.md compliance and data quality.
"""

import pandas as pd
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import logging
from datetime import datetime
import json
import re

# Import schemas - handle both direct and relative imports
try:
    from ..schemas.step14_schemas import (
        FastFishFormatSchema,
        FastFishValidationSchema,
        FastFishMismatchSchema,
        InputConsolidatedResultsSchema,
        InputClusterMappingSchema,
        CommonColumns
    )
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "schemas"))
    from step14_schemas import (
        FastFishFormatSchema,
        FastFishValidationSchema,
        FastFishMismatchSchema,
        InputConsolidatedResultsSchema,
        InputClusterMappingSchema,
        CommonColumns
    )

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_step14_fast_fish_format(period: str = "202508A") -> Dict[str, Any]:
    """
    Comprehensive validation for Step 14 Fast Fish format outputs.
    
    Args:
        period: Period to validate (e.g., "202508A")
        
    Returns:
        Dictionary with validation results and metrics
    """
    results = {
        "step": 14,
        "period": period,
        "timestamp": datetime.now().isoformat(),
        "validation_status": "PASSED",
        "errors": [],
        "warnings": [],
        "metrics": {},
        "data_quality": {}
    }
    
    try:
        # Define file paths
        base_path = Path("../output")
        fast_fish_file = base_path / f"enhanced_fast_fish_format_{period}.csv"
        validation_file = base_path / f"enhanced_fast_fish_validation_{period}.json"
        mismatch_file = base_path / f"enhanced_fast_fish_dim_mismatches_{period}.csv"
        
        # Validate main Fast Fish format
        if fast_fish_file.exists():
            fast_fish_results = validate_fast_fish_format(fast_fish_file, period)
            results["fast_fish_format"] = fast_fish_results
        else:
            results["errors"].append(f"Fast Fish format file not found: {fast_fish_file}")
            results["validation_status"] = "FAILED"
        
        # Validate validation metadata
        if validation_file.exists():
            validation_results = validate_validation_metadata(validation_file, period)
            results["validation_metadata"] = validation_results
        
        # Validate mismatch report (if exists)
        if mismatch_file.exists():
            mismatch_results = validate_mismatch_report(mismatch_file, period)
            results["mismatch_report"] = mismatch_results
        
        # Cross-validation with Step 13 inputs
        if fast_fish_file.exists():
            cross_validation = validate_cross_reference_consistency(fast_fish_file, period)
            results["cross_validation"] = cross_validation
        
        # Data quality assessment
        results["data_quality"] = assess_fast_fish_data_quality(results)
        
        # Calculate overall metrics
        results["metrics"] = calculate_fast_fish_metrics(results)
        
    except Exception as e:
        logger.error(f"Error in Step 14 validation: {str(e)}")
        results["errors"].append(f"Validation error: {str(e)}")
        results["validation_status"] = "FAILED"
    
    return results


def validate_fast_fish_format(file_path: Path, period: str) -> Dict[str, Any]:
    """Validate main Fast Fish format output."""
    results = {"status": "PASSED", "errors": [], "warnings": [], "metrics": {}}
    
    try:
        # Load data
        df = pd.read_csv(file_path)
        logger.info(f"Loaded Fast Fish format: {len(df)} rows")
        
        # Schema validation
        try:
            FastFishFormatSchema.validate(df)
            logger.info("Fast Fish format schema validation passed")
        except Exception as e:
            results["errors"].append(f"Schema validation failed: {str(e)}")
            results["status"] = "FAILED"
        
        # Period consistency check
        period_consistency = validate_period_consistency(df, period)
        results.update(period_consistency)
        
        # Mathematical consistency validation
        math_consistency = validate_mathematical_consistency(df)
        results.update(math_consistency)
        
        # Percentage validation
        percentage_validation = validate_percentage_consistency(df)
        results.update(percentage_validation)
        
        # Dimensional parsing validation
        dimensional_validation = validate_dimensional_parsing(df)
        results.update(dimensional_validation)
        
        # Temperature validation
        temperature_validation = validate_temperature_data(df)
        results.update(temperature_validation)
        
        # Business logic validation
        business_logic = validate_fast_fish_business_logic(df)
        results.update(business_logic)
        
        # Calculate metrics
        results["metrics"] = {
            "total_records": len(df),
            "unique_store_groups": df["Store_Group_Name"].nunique(),
            "unique_categories": df["Category"].nunique() if "Category" in df.columns else 0,
            "unique_subcategories": df["Subcategory"].nunique() if "Subcategory" in df.columns else 0,
            "total_current_spus": df["Current_SPU_Quantity"].sum(),
            "total_target_spus": df["Target_SPU_Quantity"].sum(),
            "total_delta_quantity": df["ΔQty"].sum(),
            "avg_delta_quantity": df["ΔQty"].mean(),
            "avg_men_percentage": df["men_percentage"].mean(),
            "avg_women_percentage": df["women_percentage"].mean(),
            "avg_unisex_percentage": df["unisex_percentage"].mean(),
            "avg_front_store_percentage": df["front_store_percentage"].mean(),
            "avg_back_store_percentage": df["back_store_percentage"].mean(),
            "avg_summer_percentage": df["summer_percentage"].mean(),
            "avg_spring_percentage": df["spring_percentage"].mean(),
            "avg_autumn_percentage": df["autumn_percentage"].mean(),
            "avg_winter_percentage": df["winter_percentage"].mean()
        }
        
    except Exception as e:
        results["errors"].append(f"Error validating Fast Fish format: {str(e)}")
        results["status"] = "FAILED"
    
    return results


def validate_validation_metadata(file_path: Path, period: str) -> Dict[str, Any]:
    """Validate validation metadata JSON file."""
    results = {"status": "PASSED", "errors": [], "warnings": [], "metrics": {}}
    
    try:
        # Load JSON data
        with open(file_path, 'r') as f:
            validation_data = json.load(f)
        
        # Validate structure
        required_fields = ["validation_timestamp", "period_label", "total_records", "validation_status"]
        for field in required_fields:
            if field not in validation_data:
                results["errors"].append(f"Missing required field in validation metadata: {field}")
                results["status"] = "FAILED"
        
        # Check validation status
        if validation_data.get("validation_status") != "PASSED":
            results["warnings"].append(f"Validation status indicates issues: {validation_data.get('validation_status')}")
        
        # Calculate metrics
        results["metrics"] = {
            "validation_timestamp": validation_data.get("validation_timestamp"),
            "period_label": validation_data.get("period_label"),
            "total_records": validation_data.get("total_records", 0),
            "validation_status": validation_data.get("validation_status"),
            "schema_validation_passed": validation_data.get("schema_validation_passed", False),
            "dimensional_parsing_passed": validation_data.get("dimensional_parsing_passed", False),
            "mathematical_consistency_passed": validation_data.get("mathematical_consistency_passed", False)
        }
        
    except Exception as e:
        results["errors"].append(f"Error validating validation metadata: {str(e)}")
        results["status"] = "FAILED"
    
    return results


def validate_mismatch_report(file_path: Path, period: str) -> Dict[str, Any]:
    """Validate dimensional mismatch report."""
    results = {"status": "PASSED", "errors": [], "warnings": [], "metrics": {}}
    
    try:
        # Load data
        df = pd.read_csv(file_path)
        logger.info(f"Loaded mismatch report: {len(df)} rows")
        
        # Schema validation
        try:
            FastFishMismatchSchema.validate(df)
            logger.info("Mismatch report schema validation passed")
        except Exception as e:
            results["errors"].append(f"Schema validation failed: {str(e)}")
            results["status"] = "FAILED"
        
        # Calculate metrics
        results["metrics"] = {
            "total_mismatches": len(df),
            "mismatch_types": df["mismatch_type"].value_counts().to_dict(),
            "severity_distribution": df["severity"].value_counts().to_dict(),
            "avg_parsing_confidence": df["parsing_confidence"].mean() if "parsing_confidence" in df.columns else None
        }
        
    except Exception as e:
        results["errors"].append(f"Error validating mismatch report: {str(e)}")
        results["status"] = "FAILED"
    
    return results


def validate_period_consistency(df: pd.DataFrame, expected_period: str) -> Dict[str, Any]:
    """Validate period consistency across all records."""
    results = {"errors": [], "warnings": []}
    
    try:
        # Check Period column consistency
        if "Period" in df.columns:
            unique_periods = df["Period"].unique()
            if len(unique_periods) > 1:
                results["warnings"].append(f"Multiple periods found: {unique_periods}")
            elif expected_period[-1] not in unique_periods:
                results["warnings"].append(f"Expected period {expected_period[-1]} not found in data")
        
        # Check Year and Month consistency
        if "Year" in df.columns and "Month" in df.columns:
            unique_years = df["Year"].unique()
            unique_months = df["Month"].unique()
            if len(unique_years) > 1:
                results["warnings"].append(f"Multiple years found: {unique_years}")
            if len(unique_months) > 1:
                results["warnings"].append(f"Multiple months found: {unique_months}")
        
    except Exception as e:
        results["errors"].append(f"Error checking period consistency: {str(e)}")
    
    return results


def validate_mathematical_consistency(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate mathematical consistency of quantity calculations."""
    results = {"errors": [], "warnings": []}
    
    try:
        # Check ΔQty calculation
        if all(col in df.columns for col in ["Current_SPU_Quantity", "Target_SPU_Quantity", "ΔQty"]):
            calculated_delta = df["Target_SPU_Quantity"] - df["Current_SPU_Quantity"]
            delta_diff = abs(df["ΔQty"] - calculated_delta).sum()
            if delta_diff > 0:
                results["errors"].append(f"ΔQty calculation inconsistency: {delta_diff} total difference")
        
        # Check for negative quantities
        negative_current = df[df["Current_SPU_Quantity"] < 0]
        if len(negative_current) > 0:
            results["errors"].append(f"Found {len(negative_current)} records with negative current quantities")
        
        negative_target = df[df["Target_SPU_Quantity"] < 0]
        if len(negative_target) > 0:
            results["errors"].append(f"Found {len(negative_target)} records with negative target quantities")
        
    except Exception as e:
        results["errors"].append(f"Error validating mathematical consistency: {str(e)}")
    
    return results


def validate_percentage_consistency(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate percentage consistency across all percentage fields."""
    results = {"errors": [], "warnings": []}
    
    try:
        # Check customer mix percentages sum to 100%
        if all(col in df.columns for col in ["men_percentage", "women_percentage", "unisex_percentage"]):
            customer_mix_sum = df["men_percentage"] + df["women_percentage"] + df["unisex_percentage"]
            customer_mix_diff = abs(customer_mix_sum - 100).sum()
            if customer_mix_diff > 0.01:  # Allow for small floating point differences
                results["warnings"].append(f"Customer mix percentages don't sum to 100%: {customer_mix_diff:.2f} total difference")
        
        # Check display location percentages sum to 100%
        if all(col in df.columns for col in ["front_store_percentage", "back_store_percentage"]):
            location_sum = df["front_store_percentage"] + df["back_store_percentage"]
            location_diff = abs(location_sum - 100).sum()
            if location_diff > 0.01:
                results["warnings"].append(f"Display location percentages don't sum to 100%: {location_diff:.2f} total difference")
        
        # Check seasonal percentages sum to 100%
        if all(col in df.columns for col in ["summer_percentage", "spring_percentage", "autumn_percentage", "winter_percentage"]):
            seasonal_sum = df["summer_percentage"] + df["spring_percentage"] + df["autumn_percentage"] + df["winter_percentage"]
            seasonal_diff = abs(seasonal_sum - 100).sum()
            if seasonal_diff > 0.01:
                results["warnings"].append(f"Seasonal percentages don't sum to 100%: {seasonal_diff:.2f} total difference")
        
    except Exception as e:
        results["errors"].append(f"Error validating percentage consistency: {str(e)}")
    
    return results


def validate_dimensional_parsing(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate dimensional parsing of Target_Style_Tags."""
    results = {"errors": [], "warnings": []}
    
    try:
        # Check if Target_Style_Tags can be parsed
        if "Target_Style_Tags" in df.columns:
            parsing_errors = 0
            for idx, tags in enumerate(df["Target_Style_Tags"]):
                if pd.isna(tags):
                    continue
                
                # Try to parse the tags string
                try:
                    # Remove brackets and split by comma
                    clean_tags = tags.strip("[]")
                    parsed_tags = [tag.strip() for tag in clean_tags.split(",")]
                    
                    # Check if we have the expected number of components
                    if len(parsed_tags) != 5:
                        parsing_errors += 1
                        if parsing_errors <= 5:  # Limit error reporting
                            results["warnings"].append(f"Row {idx}: Expected 5 dimensional components, got {len(parsed_tags)}")
                    
                except Exception:
                    parsing_errors += 1
                    if parsing_errors <= 5:
                        results["warnings"].append(f"Row {idx}: Failed to parse Target_Style_Tags: {tags}")
            
            if parsing_errors > 5:
                results["warnings"].append(f"Total parsing errors: {parsing_errors}")
        
        # Check consistency between Target_Style_Tags and parsed components
        if all(col in df.columns for col in ["Target_Style_Tags", "Parsed_Season", "Parsed_Gender", "Parsed_Location", "Parsed_Category", "Parsed_Subcategory"]):
            consistency_errors = 0
            for idx, row in df.iterrows():
                if pd.isna(row["Target_Style_Tags"]):
                    continue
                
                # Parse the tags
                try:
                    clean_tags = row["Target_Style_Tags"].strip("[]")
                    parsed_tags = [tag.strip() for tag in clean_tags.split(",")]
                    
                    # Check consistency with parsed components
                    expected_components = [row["Parsed_Season"], row["Parsed_Gender"], row["Parsed_Location"], row["Parsed_Category"], row["Parsed_Subcategory"]]
                    if parsed_tags != expected_components:
                        consistency_errors += 1
                        if consistency_errors <= 5:
                            results["warnings"].append(f"Row {idx}: Inconsistency between Target_Style_Tags and parsed components")
                
                except Exception:
                    consistency_errors += 1
                    if consistency_errors <= 5:
                        results["warnings"].append(f"Row {idx}: Failed to parse Target_Style_Tags for consistency check")
            
            if consistency_errors > 5:
                results["warnings"].append(f"Total consistency errors: {consistency_errors}")
        
    except Exception as e:
        results["errors"].append(f"Error validating dimensional parsing: {str(e)}")
    
    return results


def validate_temperature_data(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate temperature data consistency and ranges."""
    results = {"errors": [], "warnings": []}
    
    try:
        # Check temperature range validity
        if "Temp_14d_Avg" in df.columns:
            temp_data = df["Temp_14d_Avg"].dropna()
            if len(temp_data) > 0:
                min_temp = temp_data.min()
                max_temp = temp_data.max()
                if min_temp < -50 or max_temp > 60:  # Reasonable temperature range
                    results["warnings"].append(f"Temperature data outside reasonable range: {min_temp:.1f} to {max_temp:.1f}")
        
        if "FeelsLike_Temp_Period_Avg" in df.columns:
            feels_like_data = df["FeelsLike_Temp_Period_Avg"].dropna()
            if len(feels_like_data) > 0:
                min_feels_like = feels_like_data.min()
                max_feels_like = feels_like_data.max()
                if min_feels_like < -50 or max_feels_like > 60:
                    results["warnings"].append(f"Feels like temperature data outside reasonable range: {min_feels_like:.1f} to {max_feels_like:.1f}")
        
        # Check consistency between temperature fields
        if all(col in df.columns for col in ["Temp_14d_Avg", "FeelsLike_Temp_Period_Avg"]):
            both_present = df.dropna(subset=["Temp_14d_Avg", "FeelsLike_Temp_Period_Avg"])
            if len(both_present) > 0:
                temp_diff = abs(both_present["Temp_14d_Avg"] - both_present["FeelsLike_Temp_Period_Avg"]).mean()
                if temp_diff > 10:  # Large difference between actual and feels like
                    results["warnings"].append(f"Large difference between actual and feels like temperature: {temp_diff:.1f}°C average")
        
    except Exception as e:
        results["errors"].append(f"Error validating temperature data: {str(e)}")
    
    return results


def validate_fast_fish_business_logic(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate business logic for Fast Fish format."""
    results = {"errors": [], "warnings": []}
    
    try:
        # Check for zero store counts
        zero_stores = df[df["Store_Count_In_Group"] == 0]
        if len(zero_stores) > 0:
            results["warnings"].append(f"Found {len(zero_stores)} records with zero store counts")
        
        # Check for negative sales
        negative_sales = df[df["Total_Current_Sales"] < 0]
        if len(negative_sales) > 0:
            results["warnings"].append(f"Found {len(negative_sales)} records with negative sales")
        
        # Check for extreme sales values
        if "Total_Current_Sales" in df.columns:
            extreme_sales = df[df["Total_Current_Sales"] > df["Total_Current_Sales"].quantile(0.99)]
            if len(extreme_sales) > 0:
                results["warnings"].append(f"Found {len(extreme_sales)} records with extreme sales values")
        
        # Check for missing rationale
        missing_rationale = df["Data_Based_Rationale"].isna().sum()
        if missing_rationale > 0:
            results["warnings"].append(f"Found {missing_rationale} records with missing data-based rationale")
        
    except Exception as e:
        results["errors"].append(f"Error validating Fast Fish business logic: {str(e)}")
    
    return results


def validate_cross_reference_consistency(fast_fish_file: Path, period: str) -> Dict[str, Any]:
    """Validate consistency with Step 13 inputs."""
    results = {"status": "PASSED", "errors": [], "warnings": []}
    
    try:
        # Load Fast Fish data
        fast_fish_df = pd.read_csv(fast_fish_file)
        
        # Try to load Step 13 consolidated results
        consolidated_file = Path("../output/consolidated_spu_rule_results_detailed.csv")
        if consolidated_file.exists():
            consolidated_df = pd.read_csv(consolidated_file)
            
            # Check if Fast Fish data is consistent with consolidated results
            # This is a basic check - more sophisticated validation could be added
            
            # Check if store groups in Fast Fish correspond to stores in consolidated results
            fast_fish_stores = set()
            for store_codes in fast_fish_df["Store_Codes_In_Group"]:
                if pd.notna(store_codes):
                    stores = [code.strip() for code in store_codes.split(",")]
                    fast_fish_stores.update(stores)
            
            consolidated_stores = set(consolidated_df["str_code"].unique())
            
            # Check for stores in Fast Fish that are not in consolidated results
            missing_stores = fast_fish_stores - consolidated_stores
            if missing_stores:
                results["warnings"].append(f"Found {len(missing_stores)} stores in Fast Fish format not in consolidated results")
            
            # Check for stores in consolidated results that are not in Fast Fish
            extra_stores = consolidated_stores - fast_fish_stores
            if extra_stores:
                results["warnings"].append(f"Found {len(extra_stores)} stores in consolidated results not in Fast Fish format")
        
    except Exception as e:
        results["errors"].append(f"Error validating cross-reference consistency: {str(e)}")
        results["status"] = "FAILED"
    
    return results


def assess_fast_fish_data_quality(validation_results: Dict[str, Any]) -> Dict[str, Any]:
    """Assess overall data quality for Fast Fish format."""
    quality_metrics = {
        "schema_validation_passed": True,
        "mathematical_consistency_passed": True,
        "dimensional_parsing_passed": True,
        "percentage_consistency_passed": True,
        "temperature_validation_passed": True,
        "total_errors": 0,
        "total_warnings": 0
    }
    
    # Count errors and warnings across all validation results
    for key, value in validation_results.items():
        if isinstance(value, dict) and "errors" in value:
            quality_metrics["total_errors"] += len(value["errors"])
        if isinstance(value, dict) and "warnings" in value:
            quality_metrics["total_warnings"] += len(value["warnings"])
    
    # Determine overall quality status
    if quality_metrics["total_errors"] > 0:
        quality_metrics["schema_validation_passed"] = False
        quality_metrics["mathematical_consistency_passed"] = False
        quality_metrics["dimensional_parsing_passed"] = False
        quality_metrics["percentage_consistency_passed"] = False
        quality_metrics["temperature_validation_passed"] = False
    
    return quality_metrics


def calculate_fast_fish_metrics(validation_results: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate overall Fast Fish format metrics."""
    metrics = {
        "total_records": 0,
        "unique_store_groups": 0,
        "total_current_spus": 0,
        "total_target_spus": 0,
        "total_delta_quantity": 0,
        "avg_delta_quantity": 0,
        "customer_mix_balance": 0,
        "seasonal_distribution_balance": 0,
        "temperature_coverage": 0
    }
    
    # Aggregate metrics from different validation results
    for key, value in validation_results.items():
        if isinstance(value, dict) and "metrics" in value:
            metrics.update(value["metrics"])
    
    # Calculate additional metrics
    if metrics["total_records"] > 0:
        metrics["avg_spus_per_store_group"] = metrics["total_current_spus"] / metrics["unique_store_groups"]
        metrics["delta_quantity_ratio"] = metrics["total_delta_quantity"] / metrics["total_current_spus"] if metrics["total_current_spus"] > 0 else 0
    
    return metrics


def run_step14_validation(period: str = "202508A") -> Dict[str, Any]:
    """Main entry point for Step 14 validation."""
    logger.info(f"Starting Step 14 validation for period: {period}")
    
    try:
        results = validate_step14_fast_fish_format(period)
        
        # Log results
        if results["validation_status"] == "PASSED":
            logger.info("Step 14 validation completed successfully")
        else:
            logger.warning(f"Step 14 validation completed with issues: {len(results['errors'])} errors, {len(results['warnings'])} warnings")
        
        return results
        
    except Exception as e:
        logger.error(f"Step 14 validation failed: {str(e)}")
        return {
            "step": 14,
            "period": period,
            "timestamp": datetime.now().isoformat(),
            "validation_status": "FAILED",
            "errors": [f"Validation failed: {str(e)}"],
            "warnings": [],
            "metrics": {},
            "data_quality": {}
        }
