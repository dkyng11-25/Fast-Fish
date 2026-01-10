#!/usr/bin/env python3
"""
Step 18 Validation Runner

Handles validation of results validation from Step 18 of the pipeline.

Author: Data Pipeline
Date: 2025-01-03
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)


def validate_step18_validate_results(period: str = "202508A", 
                                           data_dir: str = "../output") -> Dict[str, Any]:
    """
    Validate Step 18 results validation output.
    
    Args:
        period: Period label for validation
        data_dir: Directory containing output files
        
    Returns:
        Dictionary with validation results
    """
    logger.info(f"Starting Step 18 validation for period {period}")
    
    results = {
        "step": 18,
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
            'main_output': f"validate_results_{period}.csv",
            'summary_output': f"validate_results_summary_{period}.csv",
            'log_file': f"validate_results_log_{period}.log"
        }
        
        # Validate each file
        for file_type, filename in expected_files.items():
            file_path = data_path / filename
            if file_path.exists():
                logger.info(f"Validating {file_type}: {file_path}")
                try:
                    if file_type == 'log_file':
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
                        if file_type == 'main_output':
                            required_cols = ['str_code', 'result_metric', 'value']
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
        
        logger.info(f"Step 18 validation completed. Passed: {results['validation_passed']}")
        
    except Exception as e:
        logger.error(f"Error during Step 18 validation: {str(e)}")
        results["errors"].append(f"Validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def run_step18_validation(period: str = "202508A") -> Dict[str, Any]:
    """
    Run Step 18 validation.
    
    Args:
        period: Period label for validation
        
    Returns:
        Dictionary with validation results
    """
    return validate_step18_validate_results(period)


if __name__ == "__main__":
    # Run validation when script is executed directly
    import sys
    
    period = sys.argv[1] if len(sys.argv) > 1 else "202508A"
    
    results = run_step18_validation(period)
    
    print(f"Step 18 validation results:")
    print(f"  Period: {results['period']}")
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
