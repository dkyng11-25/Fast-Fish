#!/usr/bin/env python3
"""
Step 28 Scenario Analyzer Validators

This module contains validators for scenario analysis validation from Step 28.

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

def validate_step28_complete(
    output_base_dir: str = "tests/test_output"
) -> Dict[str, Any]:
    """
    Validates the outputs of Step 28: Scenario Analyzer.
    Checks for scenario analysis results, reports, and recommendations.
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
    
    # Expected output files (with period patterns)
    expected_patterns = {
        "scenario_results": f"{output_dir}/scenario_analysis_results_*.json",
        "scenario_report": f"{output_dir}/scenario_analysis_results_*_report.md"
    }

    for file_type, pattern in expected_patterns.items():
        candidate_files = sorted(glob.glob(str(pattern)), key=os.path.getctime, reverse=True)
        
        file_validation = {"exists": False, "count": len(candidate_files)}
        
        if candidate_files:
            file_path = candidate_files[0]
            file_validation["exists"] = True
            file_validation["latest"] = str(file_path)
            file_validation["size_bytes"] = Path(file_path).stat().st_size
            file_validation["size_mb"] = round(file_validation["size_bytes"] / (1024 * 1024), 3)
            
            if file_validation["size_bytes"] == 0:
                validation_results["validation_passed"] = False
                validation_results["warnings"].append(f"Empty file found: {file_type}")
            else:
                # Validate file content based on type
                try:
                    if file_path.endswith('.json'):
                        with open(file_path, 'r') as f:
                            json_data = json.load(f)
                        file_validation["json_keys"] = list(json_data.keys())
                        
                        # Validate JSON structure
                        if "analysis_metadata" not in json_data:
                            validation_results["warnings"].append(f"Missing analysis_metadata in {file_type}")
                        if "scenario_results" not in json_data:
                            validation_results["warnings"].append(f"Missing scenario_results in {file_type}")
                        
                        # Check for baseline_metrics in analysis_metadata
                        baseline_metrics = None
                        if "analysis_metadata" in json_data and "baseline_metrics" in json_data["analysis_metadata"]:
                            baseline_metrics = json_data["analysis_metadata"]["baseline_metrics"]
                        elif "baseline_metrics" in json_data:
                            baseline_metrics = json_data["baseline_metrics"]
                        else:
                            validation_results["warnings"].append(f"Missing baseline_metrics in {file_type}")
                        
                        # Validate baseline metrics structure
                        if baseline_metrics:
                            baseline = baseline_metrics
                            required_baseline_keys = ["total_products", "total_sales_amount", "avg_sell_through_rate"]
                            missing_baseline_keys = [key for key in required_baseline_keys if key not in baseline]
                            if missing_baseline_keys:
                                validation_results["warnings"].append(f"Missing baseline metrics keys: {missing_baseline_keys}")
                            
                            # Validate baseline metrics values
                            if "total_products" in baseline and baseline["total_products"] <= 0:
                                validation_results["warnings"].append("total_products should be positive")
                            if "total_sales_amount" in baseline and baseline["total_sales_amount"] < 0:
                                validation_results["warnings"].append("total_sales_amount should be non-negative")
                            if "avg_sell_through_rate" in baseline and (baseline["avg_sell_through_rate"] < 0 or baseline["avg_sell_through_rate"] > 100):
                                validation_results["warnings"].append("avg_sell_through_rate should be between 0 and 100")
                        
                        file_validation["scenarios_analyzed"] = json_data.get("analysis_metadata", {}).get("total_scenarios_analyzed", 0)
                        file_validation["baseline_products"] = json_data.get("baseline_metrics", {}).get("total_products", 0)
                        file_validation["baseline_sales"] = json_data.get("baseline_metrics", {}).get("total_sales_amount", 0)
                        
                    elif file_path.endswith('.md'):
                        content = Path(file_path).read_text()
                        file_validation["content_length"] = len(content)
                        file_validation["content_preview"] = content[:200] + "..." if len(content) > 200 else content
                        
                        # Check for key content
                        if "scenario" not in content.lower():
                            validation_results["warnings"].append(f"Missing scenario content in {file_type}")
                        if "analysis" not in content.lower():
                            validation_results["warnings"].append(f"Missing analysis content in {file_type}")
                            
                    elif file_path.endswith('.csv'):
                        df = pd.read_csv(file_path)
                        file_validation["rows"] = len(df)
                        file_validation["columns"] = list(df.columns)
                        
                        if df.empty:
                            validation_results["validation_passed"] = False
                            validation_results["warnings"].append(f"CSV file is empty: {file_type}")
                        else:
                            # Validate scenario recommendations structure
                            expected_cols = ["scenario_id", "scenario_name", "revenue_change_pct", "priority_level"]
                            missing_cols = [col for col in expected_cols if col not in df.columns]
                            if missing_cols:
                                validation_results["warnings"].append(f"Missing expected columns in {file_type}: {missing_cols}")
                            
                            # Validate data quality
                            if "revenue_change_pct" in df.columns:
                                if not df["revenue_change_pct"].dtype in ['int64', 'float64']:
                                    validation_results["warnings"].append("revenue_change_pct should be numeric")
                            
                            if "priority_level" in df.columns:
                                valid_priorities = ["HIGH", "MEDIUM", "LOW"]
                                invalid_priorities = df[~df["priority_level"].isin(valid_priorities)]["priority_level"].unique()
                                if len(invalid_priorities) > 0:
                                    validation_results["warnings"].append(f"Invalid priority levels found: {invalid_priorities}")
                            
                            file_validation["unique_scenarios"] = df["scenario_id"].nunique() if "scenario_id" in df.columns else 0
                            file_validation["priority_distribution"] = df["priority_level"].value_counts().to_dict() if "priority_level" in df.columns else {}
                            
                except Exception as e:
                    validation_results["validation_passed"] = False
                    validation_results["errors"].append(f"Error reading {file_type}: {str(e)}")
        else:
            validation_results["validation_passed"] = False
            validation_results["warnings"].append(f"Missing expected Step 28 output: {file_type}")
        
        validation_results["files"][file_type] = file_validation

    # Overall validation summary
    validation_results["statistics"]["total_file_types_expected"] = len(expected_patterns)
    validation_results["statistics"]["file_types_found"] = sum(1 for f in validation_results["files"].values() if f["exists"])
    validation_results["statistics"]["validation_timestamp"] = datetime.now().isoformat()
    
    return validation_results

def validate_scenario_results_json(file_path: str) -> Dict[str, Any]:
    """
    Validates scenario results JSON file specifically.
    """
    validation_results = {
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        with open(file_path, 'r') as f:
            json_data = json.load(f)
        
        # Check required top-level keys
        required_keys = ["analysis_metadata", "scenario_results"]
        missing_keys = [key for key in required_keys if key not in json_data]
        if missing_keys:
            validation_results["validation_passed"] = False
            validation_results["errors"].append(f"Missing required keys: {missing_keys}")
            return validation_results
        
        # Validate analysis metadata
        metadata = json_data.get("analysis_metadata", {})
        if "total_scenarios_analyzed" not in metadata:
            validation_results["warnings"].append("Missing total_scenarios_analyzed in analysis_metadata")
        if "analysis_timestamp" not in metadata:
            validation_results["warnings"].append("Missing analysis_timestamp in analysis_metadata")
        
        # Check for baseline_metrics in analysis_metadata
        baseline = None
        if "baseline_metrics" in metadata:
            baseline = metadata["baseline_metrics"]
        elif "baseline_metrics" in json_data:
            baseline = json_data["baseline_metrics"]
        else:
            validation_results["warnings"].append("Missing baseline_metrics")
            baseline = {}
        required_baseline_keys = ["total_products", "total_sales_amount", "avg_sell_through_rate"]
        missing_baseline_keys = [key for key in required_baseline_keys if key not in baseline]
        if missing_baseline_keys:
            validation_results["warnings"].append(f"Missing baseline metrics: {missing_baseline_keys}")
        
        # Validate baseline values
        if "total_products" in baseline and baseline["total_products"] <= 0:
            validation_results["validation_passed"] = False
            validation_results["errors"].append("total_products should be positive")
        
        if "total_sales_amount" in baseline and baseline["total_sales_amount"] < 0:
            validation_results["validation_passed"] = False
            validation_results["errors"].append("total_sales_amount should be non-negative")
        
        if "avg_sell_through_rate" in baseline:
            rate = baseline["avg_sell_through_rate"]
            if rate < 0 or rate > 100:
                validation_results["validation_passed"] = False
                validation_results["errors"].append("avg_sell_through_rate should be between 0 and 100")
        
        # Validate scenario results
        scenarios = json_data.get("scenario_results", [])
        if not isinstance(scenarios, list):
            validation_results["warnings"].append("scenario_results should be a list")
        else:
            validation_results["statistics"]["total_scenarios"] = len(scenarios)
            
            # Validate each scenario
            for i, scenario in enumerate(scenarios):
                if not isinstance(scenario, dict):
                    validation_results["warnings"].append(f"Scenario {i} is not a dictionary")
                    continue
                
                if "scenario_id" not in scenario:
                    validation_results["warnings"].append(f"Scenario {i} missing scenario_id")
                if "scenario_name" not in scenario:
                    validation_results["warnings"].append(f"Scenario {i} missing scenario_name")
        
        # Statistics
        validation_results["statistics"]["scenarios_analyzed"] = metadata.get("total_scenarios_analyzed", 0)
        validation_results["statistics"]["baseline_products"] = baseline.get("total_products", 0)
        validation_results["statistics"]["baseline_sales"] = baseline.get("total_sales_amount", 0)
        validation_results["statistics"]["baseline_sellthrough"] = baseline.get("avg_sell_through_rate", 0)
        
    except Exception as e:
        validation_results["validation_passed"] = False
        validation_results["errors"].append(f"Error reading file: {str(e)}")
    
    return validation_results

if __name__ == "__main__":
    # Test the validator
    print("Testing Step 28 Scenario Analyzer Validator...")
    results = validate_step28_complete("output")
    print(f"Validation passed: {results['validation_passed']}")
    print(f"File types found: {results['statistics']['file_types_found']}/{results['statistics']['total_file_types_expected']}")
    if results['errors']:
        print(f"Errors: {results['errors']}")
    if results['warnings']:
        print(f"Warnings: {results['warnings']}")
    
    # Test specific JSON validation
    json_files = glob.glob("output/scenario_analysis_results_*.json")
    if json_files:
        print(f"\nTesting specific JSON validation on {json_files[0]}...")
        json_results = validate_scenario_results_json(json_files[0])
        print(f"JSON validation passed: {json_results['validation_passed']}")
        if json_results['errors']:
            print(f"JSON errors: {json_results['errors']}")
        if json_results['warnings']:
            print(f"JSON warnings: {json_results['warnings']}")
        print(f"Statistics: {json_results['statistics']}")