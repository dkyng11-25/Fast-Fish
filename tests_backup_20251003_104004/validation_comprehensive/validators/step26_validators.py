#!/usr/bin/env python3
"""
Step 26 Price Elasticity Analyzer Validators

This module contains validators for price elasticity analysis validation from Step 26.

Author: Data Pipeline
Date: 2025-01-16
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import os
import glob
from datetime import datetime
import json

logger = logging.getLogger(__name__)

def validate_step26_complete(
    output_base_dir: str = "tests/test_output"
) -> Dict[str, Any]:
    """
    Validates the outputs of Step 26: Price Elasticity Analyzer.
    Checks for price band analysis, substitution elasticity matrix, and reports.
    """
    validation_results = {
        "validation_passed": False,  # Default to False - requires real data validation
        "files": {},
        "errors": ["No real data validation performed"],
        "warnings": ["Using default validation - real data required"],
        "statistics": {
            "validation_type": "default",
            "data_source": "unknown",
            "reliability": "low"
        }
    }

    output_dir = Path(output_base_dir)
    
    # Expected output files
    expected_files = {
        "price_band_analysis": f"{output_dir}/price_band_analysis.csv",
        "substitution_elasticity_matrix": f"{output_dir}/substitution_elasticity_matrix.csv",
        "price_elasticity_analysis_report": f"{output_dir}/price_elasticity_analysis_report.md",
        "price_elasticity_summary": f"{output_dir}/price_elasticity_summary.json"
    }

    for file_type, file_path in expected_files.items():
        file_validation = {"exists": False, "path": str(file_path)}
        
        if Path(file_path).exists():
            file_validation["exists"] = True
            file_validation["size_bytes"] = Path(file_path).stat().st_size
            file_validation["size_mb"] = round(file_validation["size_bytes"] / (1024 * 1024), 3)
            
            if file_validation["size_bytes"] == 0:
                validation_results["validation_passed"] = False
                validation_results["warnings"].append(f"Empty file found: {file_type}")
            else:
                # Validate file content based on type
                try:
                    if file_path.endswith('.csv'):
                        df = pd.read_csv(file_path)
                        file_validation["rows"] = len(df)
                        file_validation["columns"] = list(df.columns)
                        
                        if df.empty:
                            validation_results["validation_passed"] = False
                            validation_results["warnings"].append(f"CSV file is empty: {file_type}")
                        else:
                            # Validate specific columns based on file type
                            if file_type == "price_band_analysis":
                                expected_cols = ["spu_code", "avg_unit_price", "price_band", "product_role"]
                                missing_cols = [col for col in expected_cols if col not in df.columns]
                                if missing_cols:
                                    validation_results["warnings"].append(f"Missing expected columns in {file_type}: {missing_cols}")
                                
                                # Validate data quality
                                if "avg_unit_price" in df.columns:
                                    if not df["avg_unit_price"].dtype in ['int64', 'float64']:
                                        validation_results["warnings"].append("avg_unit_price should be numeric")
                                    if (df["avg_unit_price"] < 0).any():
                                        validation_results["warnings"].append("Found negative avg_unit_price values")
                                
                                if "price_band" in df.columns:
                                    valid_bands = ["ECONOMY", "VALUE", "PREMIUM", "LUXURY"]  # Updated to match actual data
                                    invalid_bands = df[~df["price_band"].isin(valid_bands)]["price_band"].unique()
                                    if len(invalid_bands) > 0:
                                        validation_results["warnings"].append(f"Invalid price bands found: {invalid_bands}")
                                
                                file_validation["unique_products"] = df["spu_code"].nunique() if "spu_code" in df.columns else 0
                                file_validation["price_bands"] = df["price_band"].value_counts().to_dict() if "price_band" in df.columns else {}
                                
                            elif file_type == "substitution_elasticity_matrix":
                                expected_cols = ["product_1", "product_2", "substitution_score", "relationship_strength"]
                                missing_cols = [col for col in expected_cols if col not in df.columns]
                                if missing_cols:
                                    validation_results["warnings"].append(f"Missing expected columns in {file_type}: {missing_cols}")
                                
                                # Validate substitution scores
                                if "substitution_score" in df.columns:
                                    if not df["substitution_score"].dtype in ['int64', 'float64']:
                                        validation_results["warnings"].append("substitution_score should be numeric")
                                    if (df["substitution_score"] < -1.0).any() or (df["substitution_score"] > 1.0).any():
                                        validation_results["warnings"].append("substitution_score should be between -1.0 and 1.0")
                                
                                file_validation["total_pairs"] = len(df)
                                file_validation["relationship_types"] = df["relationship_strength"].value_counts().to_dict() if "relationship_strength" in df.columns else {}
                                
                    elif file_path.endswith('.json'):
                        with open(file_path, 'r') as f:
                            json_data = json.load(f)
                        file_validation["json_keys"] = list(json_data.keys())
                        
                        # Validate JSON structure
                        if "analysis_metadata" not in json_data:
                            validation_results["warnings"].append("Missing analysis_metadata in JSON file")
                        if "price_band_distribution" not in json_data:
                            validation_results["warnings"].append("Missing price_band_distribution in JSON file")
                            
                    # For .md files, just check existence and size
                    elif file_path.endswith('.md'):
                        file_validation["content_preview"] = Path(file_path).read_text()[:200] + "..." if Path(file_path).stat().st_size > 200 else Path(file_path).read_text()
                        
                except Exception as e:
                    validation_results["validation_passed"] = False
                    validation_results["errors"].append(f"Error reading {file_type}: {str(e)}")
        else:
            validation_results["validation_passed"] = False
            validation_results["warnings"].append(f"Missing expected Step 26 output: {file_type}")
        
        validation_results["files"][file_type] = file_validation

    # Overall validation summary
    validation_results["statistics"]["total_files_expected"] = len(expected_files)
    validation_results["statistics"]["files_found"] = sum(1 for f in validation_results["files"].values() if f["exists"])
    validation_results["statistics"]["validation_timestamp"] = datetime.now().isoformat()
    
    return validation_results

def validate_price_band_analysis(file_path: str) -> Dict[str, Any]:
    """
    Validates price band analysis CSV file specifically.
    """
    validation_results = {
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        df = pd.read_csv(file_path)
        
        # Check required columns
        required_columns = ["spu_code", "avg_unit_price", "price_band", "product_role"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            validation_results["validation_passed"] = False
            validation_results["errors"].append(f"Missing required columns: {missing_columns}")
            return validation_results
        
        # Validate data types
        if not df["avg_unit_price"].dtype in ['int64', 'float64']:
            validation_results["validation_passed"] = False
            validation_results["errors"].append("avg_unit_price should be numeric")
        
        # Validate price bands
        valid_bands = ["ECONOMY", "VALUE", "PREMIUM", "LUXURY"]  # Updated to match actual data
        invalid_bands = df[~df["price_band"].isin(valid_bands)]["price_band"].unique()
        if len(invalid_bands) > 0:
            validation_results["warnings"].append(f"Invalid price bands found: {invalid_bands}")
        
        # Validate product roles
        valid_roles = ["CORE", "SEASONAL", "FILLER", "CLEARANCE"]
        invalid_roles = df[~df["product_role"].isin(valid_roles)]["product_role"].unique()
        if len(invalid_roles) > 0:
            validation_results["warnings"].append(f"Invalid product roles found: {invalid_roles}")
        
        # Validate price ranges
        if (df["avg_unit_price"] < 0).any():
            validation_results["validation_passed"] = False
            validation_results["errors"].append("Found negative avg_unit_price values")
        
        # Statistics
        validation_results["statistics"]["total_products"] = len(df)
        validation_results["statistics"]["unique_products"] = df["spu_code"].nunique()
        validation_results["statistics"]["price_band_distribution"] = df["price_band"].value_counts().to_dict()
        validation_results["statistics"]["product_role_distribution"] = df["product_role"].value_counts().to_dict()
        validation_results["statistics"]["avg_price"] = df["avg_unit_price"].mean()
        validation_results["statistics"]["price_range"] = f"{df['avg_unit_price'].min():.2f} - {df['avg_unit_price'].max():.2f}"
        
    except Exception as e:
        validation_results["validation_passed"] = False
        validation_results["errors"].append(f"Error reading file: {str(e)}")
    
    return validation_results

def validate_substitution_elasticity_matrix(file_path: str) -> Dict[str, Any]:
    """
    Validates substitution elasticity matrix CSV file specifically.
    """
    validation_results = {
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        df = pd.read_csv(file_path)
        
        # Check required columns
        required_columns = ["product_1", "product_2", "substitution_score", "relationship_strength"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            validation_results["validation_passed"] = False
            validation_results["errors"].append(f"Missing required columns: {missing_columns}")
            return validation_results
        
        # Validate substitution scores
        if not df["substitution_score"].dtype in ['int64', 'float64']:
            validation_results["validation_passed"] = False
            validation_results["errors"].append("substitution_score should be numeric")
        
        # Validate score ranges
        if (df["substitution_score"] < -1.0).any() or (df["substitution_score"] > 1.0).any():
            validation_results["warnings"].append("substitution_score should be between -1.0 and 1.0")
        
        # Validate relationship strength values
        valid_relationships = ["Strong Substitutes", "Moderate Substitutes", "Weak Substitutes", "Independent", "Complements"]
        invalid_relationships = df[~df["relationship_strength"].isin(valid_relationships)]["relationship_strength"].unique()
        if len(invalid_relationships) > 0:
            validation_results["warnings"].append(f"Invalid relationship strength values found: {invalid_relationships}")
        
        # Statistics
        validation_results["statistics"]["total_pairs"] = len(df)
        validation_results["statistics"]["unique_products"] = len(set(df["product_1"].tolist() + df["product_2"].tolist()))
        validation_results["statistics"]["relationship_distribution"] = df["relationship_strength"].value_counts().to_dict()
        validation_results["statistics"]["avg_substitution_score"] = df["substitution_score"].mean()
        validation_results["statistics"]["score_range"] = f"{df['substitution_score'].min():.3f} - {df['substitution_score'].max():.3f}"
        
    except Exception as e:
        validation_results["validation_passed"] = False
        validation_results["errors"].append(f"Error reading file: {str(e)}")
    
    return validation_results

if __name__ == "__main__":
    # Test the validator
    print("Testing Step 26 Price Elasticity Validator...")
    results = validate_step26_complete("output")
    print(f"Validation passed: {results['validation_passed']}")
    print(f"Files found: {results['statistics']['files_found']}/{results['statistics']['total_files_expected']}")
    if results['errors']:
        print(f"Errors: {results['errors']}")
    if results['warnings']:
        print(f"Warnings: {results['warnings']}")
