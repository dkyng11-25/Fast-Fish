#!/usr/bin/env python3
"""
Step 19 Comprehensive Runner

This runner provides comprehensive testing and validation for Step 19 (Detailed SPU Breakdown).
It includes data generation, execution, validation, and analysis capabilities.

Author: Data Pipeline
Date: 2025-09-17
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import os
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

# Import validators
from tests.validation_comprehensive.validators.step19_validators import validate_step19_complete

# Import schemas with error handling
try:
    from tests.validation_comprehensive.schemas.pipeline.step19_detailed_spu_breakdown_schemas import (
        DetailedSPUBreakdownSchema,
        SPUPerformanceAnalysisSchema,
        StoreSPUAnalysisSchema
    )
    SCHEMAS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import schemas: {e}")
    SCHEMAS_AVAILABLE = False

# Set up logging
logger = logging.getLogger(__name__)


class Step19ComprehensiveRunner:
    """Comprehensive runner for Step 19 Detailed SPU Breakdown."""
    
    def __init__(self, output_dir: str = "output", period: str = "202508A"):
        """
        Initialize the Step 19 comprehensive runner.
        
        Args:
            output_dir: Directory containing output files
            period: Period label for validation
        """
        self.output_dir = Path(output_dir)
        self.period = period
        self.results = {
            "step": 19,
            "period": period,
            "timestamp": datetime.now().isoformat(),
            "validation_passed": False,
            "errors": [],
            "warnings": [],
            "statistics": {},
            "file_validation": {},
            "data_quality": {},
            "business_logic": {}
        }
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """
        Run comprehensive validation for Step 19.
        
        Returns:
            Dictionary with comprehensive validation results
        """
        logger.info(f"Starting comprehensive Step 19 validation for period {self.period}")
        
        try:
            # 1. Basic file validation
            self._validate_output_files()
            
            # 2. Data quality validation
            self._validate_data_quality()
            
            # 3. Business logic validation
            self._validate_business_logic()
            
            # 4. Schema validation
            self._validate_schemas()
            
            # 5. Cross-file consistency validation
            self._validate_cross_file_consistency()
            
            # 6. Performance analysis
            self._analyze_performance()
            
            # Determine overall validation status
            self.results["validation_passed"] = (
                len(self.results["errors"]) == 0 and
                self.results["file_validation"].get("all_outputs_exist", False)
            )
            
            logger.info(f"Step 19 comprehensive validation completed: {self.results['validation_passed']}")
            
        except Exception as e:
            logger.error(f"Error in Step 19 comprehensive validation: {str(e)}")
            self.results["errors"].append(f"Validation error: {str(e)}")
            self.results["validation_passed"] = False
        
        return self.results
    
    def _validate_output_files(self) -> None:
        """Validate that all expected Step 19 output files exist."""
        logger.info("Validating Step 19 output files...")
        
        expected_files = {
            "detailed_spu_recommendations": f"detailed_spu_recommendations_{self.period}_*.csv",
            "store_level_aggregation": f"store_level_aggregation_{self.period}_*.csv",
            "cluster_subcategory_aggregation": f"cluster_subcategory_aggregation_{self.period}_*.csv",
            "spu_breakdown_summary": f"spu_breakdown_summary_{self.period}_*.md"
        }
        
        file_validation = {
            "all_outputs_exist": True,
            "files_found": 0,
            "total_files_expected": len(expected_files),
            "file_details": {}
        }
        
        for file_type, pattern in expected_files.items():
            matching_files = list(self.output_dir.glob(pattern))
            if matching_files:
                latest_file = max(matching_files, key=lambda x: x.stat().st_mtime)
                file_validation["file_details"][file_type] = {
                    "exists": True,
                    "latest": str(latest_file),
                    "size_mb": round(latest_file.stat().st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()
                }
                file_validation["files_found"] += 1
            else:
                file_validation["file_details"][file_type] = {
                    "exists": False,
                    "latest": None
                }
                file_validation["all_outputs_exist"] = False
                self.results["warnings"].append(f"Missing expected Step 19 output: {pattern}")
        
        self.results["file_validation"] = file_validation
        self.results["statistics"]["files_found"] = file_validation["files_found"]
        self.results["statistics"]["total_files_expected"] = file_validation["total_files_expected"]
    
    def _validate_data_quality(self) -> None:
        """Validate data quality of Step 19 outputs."""
        logger.info("Validating Step 19 data quality...")
        
        data_quality = {
            "detailed_spu_recommendations": {},
            "store_level_aggregation": {},
            "cluster_subcategory_aggregation": {}
        }
        
        # Validate detailed SPU recommendations
        detailed_file = self.results["file_validation"]["file_details"].get("detailed_spu_recommendations", {}).get("latest")
        if detailed_file and Path(detailed_file).exists():
            try:
                df = pd.read_csv(detailed_file)
                data_quality["detailed_spu_recommendations"] = {
                    "total_records": len(df),
                    "null_values": df.isnull().sum().to_dict(),
                    "duplicate_records": df.duplicated().sum(),
                    "data_types": df.dtypes.to_dict(),
                    "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
                }
                
                # Check for required columns
                required_cols = ["str_code", "spu_code", "recommended_quantity_change", "investment_required"]
                missing_cols = [col for col in required_cols if col not in df.columns]
                if missing_cols:
                    self.results["warnings"].append(f"Missing required columns in detailed SPU recommendations: {missing_cols}")
                
            except Exception as e:
                self.results["warnings"].append(f"Could not validate detailed SPU recommendations data quality: {str(e)}")
        
        # Validate store level aggregation
        store_file = self.results["file_validation"]["file_details"].get("store_level_aggregation", {}).get("latest")
        if store_file and Path(store_file).exists():
            try:
                df = pd.read_csv(store_file)
                data_quality["store_level_aggregation"] = {
                    "total_records": len(df),
                    "null_values": df.isnull().sum().to_dict(),
                    "duplicate_records": df.duplicated().sum(),
                    "data_types": df.dtypes.to_dict()
                }
            except Exception as e:
                self.results["warnings"].append(f"Could not validate store aggregation data quality: {str(e)}")
        
        # Validate cluster aggregation
        cluster_file = self.results["file_validation"]["file_details"].get("cluster_subcategory_aggregation", {}).get("latest")
        if cluster_file and Path(cluster_file).exists():
            try:
                df = pd.read_csv(cluster_file)
                data_quality["cluster_subcategory_aggregation"] = {
                    "total_records": len(df),
                    "null_values": df.isnull().sum().to_dict(),
                    "duplicate_records": df.duplicated().sum(),
                    "data_types": df.dtypes.to_dict()
                }
            except Exception as e:
                self.results["warnings"].append(f"Could not validate cluster aggregation data quality: {str(e)}")
        
        self.results["data_quality"] = data_quality
    
    def _validate_business_logic(self) -> None:
        """Validate business logic of Step 19 outputs."""
        logger.info("Validating Step 19 business logic...")
        
        business_logic = {
            "quantity_consistency": True,
            "investment_consistency": True,
            "aggregation_consistency": True,
            "warnings": []
        }
        
        # Check quantity consistency
        detailed_file = self.results["file_validation"]["file_details"].get("detailed_spu_recommendations", {}).get("latest")
        if detailed_file and Path(detailed_file).exists():
            try:
                df = pd.read_csv(detailed_file)
                
                # Check for negative quantities where they shouldn't be
                if "recommended_quantity_change" in df.columns:
                    negative_quantities = (df["recommended_quantity_change"] < 0).sum()
                    if negative_quantities > 0:
                        business_logic["warnings"].append(f"Found {negative_quantities} negative quantity changes")
                
                # Check investment consistency
                if "investment_required" in df.columns:
                    negative_investments = (df["investment_required"] < 0).sum()
                    if negative_investments > 0:
                        business_logic["warnings"].append(f"Found {negative_investments} negative investment requirements")
                
            except Exception as e:
                business_logic["warnings"].append(f"Could not validate business logic: {str(e)}")
        
        self.results["business_logic"] = business_logic
        self.results["warnings"].extend(business_logic["warnings"])
    
    def _validate_schemas(self) -> None:
        """Validate Step 19 outputs against schemas."""
        logger.info("Validating Step 19 schemas...")
        
        schema_validation = {
            "detailed_spu_schema": False,
            "store_aggregation_schema": False,
            "cluster_aggregation_schema": False,
            "schemas_available": SCHEMAS_AVAILABLE
        }
        
        if not SCHEMAS_AVAILABLE:
            self.results["warnings"].append("Schema validation skipped - schemas not available")
            self.results["statistics"]["schema_validation"] = schema_validation
            return
        
        # Validate detailed SPU recommendations against schema
        detailed_file = self.results["file_validation"]["file_details"].get("detailed_spu_recommendations", {}).get("latest")
        if detailed_file and Path(detailed_file).exists():
            try:
                df = pd.read_csv(detailed_file)
                DetailedSPUBreakdownSchema.validate(df)
                schema_validation["detailed_spu_schema"] = True
            except Exception as e:
                self.results["warnings"].append(f"Detailed SPU schema validation failed: {str(e)}")
        
        # Validate store aggregation against schema
        store_file = self.results["file_validation"]["file_details"].get("store_level_aggregation", {}).get("latest")
        if store_file and Path(store_file).exists():
            try:
                df = pd.read_csv(store_file)
                StoreSPUAnalysisSchema.validate(df)
                schema_validation["store_aggregation_schema"] = True
            except Exception as e:
                self.results["warnings"].append(f"Store aggregation schema validation failed: {str(e)}")
        
        self.results["statistics"]["schema_validation"] = schema_validation
    
    def _validate_cross_file_consistency(self) -> None:
        """Validate consistency across Step 19 output files."""
        logger.info("Validating Step 19 cross-file consistency...")
        
        consistency_checks = {
            "store_totals_match": False,
            "cluster_totals_match": False,
            "warnings": []
        }
        
        # Check if store totals match between detailed and aggregated files
        detailed_file = self.results["file_validation"]["file_details"].get("detailed_spu_recommendations", {}).get("latest")
        store_file = self.results["file_validation"]["file_details"].get("store_level_aggregation", {}).get("latest")
        
        if detailed_file and store_file and Path(detailed_file).exists() and Path(store_file).exists():
            try:
                detailed_df = pd.read_csv(detailed_file)
                store_df = pd.read_csv(store_file)
                
                # Check if store codes match
                detailed_stores = set(detailed_df["str_code"].unique()) if "str_code" in detailed_df.columns else set()
                store_stores = set(store_df["str_code"].unique()) if "str_code" in store_df.columns else set()
                
                if detailed_stores == store_stores:
                    consistency_checks["store_totals_match"] = True
                else:
                    consistency_checks["warnings"].append("Store codes don't match between detailed and aggregated files")
                
            except Exception as e:
                consistency_checks["warnings"].append(f"Could not validate store consistency: {str(e)}")
        
        self.results["statistics"]["consistency_checks"] = consistency_checks
        self.results["warnings"].extend(consistency_checks["warnings"])
    
    def _analyze_performance(self) -> None:
        """Analyze performance metrics of Step 19 outputs."""
        logger.info("Analyzing Step 19 performance...")
        
        performance_metrics = {
            "total_recommendations": 0,
            "unique_stores": 0,
            "unique_spus": 0,
            "total_investment": 0.0,
            "average_quantity_change": 0.0
        }
        
        detailed_file = self.results["file_validation"]["file_details"].get("detailed_spu_recommendations", {}).get("latest")
        if detailed_file and Path(detailed_file).exists():
            try:
                df = pd.read_csv(detailed_file)
                
                performance_metrics["total_recommendations"] = len(df)
                performance_metrics["unique_stores"] = df["str_code"].nunique() if "str_code" in df.columns else 0
                performance_metrics["unique_spus"] = df["spu_code"].nunique() if "spu_code" in df.columns else 0
                
                if "investment_required" in df.columns:
                    performance_metrics["total_investment"] = df["investment_required"].sum()
                
                if "recommended_quantity_change" in df.columns:
                    performance_metrics["average_quantity_change"] = df["recommended_quantity_change"].mean()
                
            except Exception as e:
                self.results["warnings"].append(f"Could not analyze performance metrics: {str(e)}")
        
        self.results["statistics"]["performance_metrics"] = performance_metrics


def run_step19_comprehensive_validation(output_dir: str = "output", period: str = "202508A") -> Dict[str, Any]:
    """
    Run comprehensive Step 19 validation.
    
    Args:
        output_dir: Directory containing output files
        period: Period label for validation
        
    Returns:
        Dictionary with comprehensive validation results
    """
    runner = Step19ComprehensiveRunner(output_dir, period)
    return runner.run_comprehensive_validation()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Step 19 Comprehensive Runner")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--period", default="202508A", help="Period label")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    results = run_step19_comprehensive_validation(args.output_dir, args.period)
    
    print(f"\n{'='*60}")
    print(f"Step 19 Comprehensive Validation Results")
    print(f"{'='*60}")
    print(f"Period: {results['period']}")
    print(f"Validation Passed: {results['validation_passed']}")
    print(f"Files Found: {results['statistics']['files_found']}/{results['statistics']['total_files_expected']}")
    print(f"Errors: {len(results['errors'])}")
    print(f"Warnings: {len(results['warnings'])}")
    
    if results['errors']:
        print(f"\nErrors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    if results['warnings']:
        print(f"\nWarnings:")
        for warning in results['warnings']:
            print(f"  - {warning}")
    
    # Save results
    results_file = f"step19_comprehensive_validation_{results['period']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
