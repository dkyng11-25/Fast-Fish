#!/usr/bin/env python3
"""
Comprehensive Validation Runner

This module provides comprehensive validation using EDA insights and multiple
time periods to ensure robust data validation across different scenarios.

Author: Data Pipeline
Date: 2025-01-03
"""

import logging
import os
import glob
from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd
import numpy as np

from ..eda_validator import EDAValidator
from ..schemas.comprehensive_schemas import (
    get_comprehensive_store_config_schema,
    get_comprehensive_spu_sales_schema,
    get_comprehensive_weather_schema,
    get_comprehensive_clustering_schema,
    get_comprehensive_matrix_schema
)
from ..validators import validate_file_flexible

logger = logging.getLogger(__name__)

class ComprehensiveValidationRunner:
    """
    Comprehensive validation runner that uses EDA insights for robust validation.
    """
    
    def __init__(self, eda_results_path: str = "output/eda_reports/comprehensive_analysis_results.json"):
        self.eda_results_path = eda_results_path
        self.eda_validator = EDAValidator()
        self.validation_results = {}
        
    def run_eda_analysis(self) -> Dict[str, Any]:
        """Run comprehensive EDA analysis across multiple time periods."""
        logger.info("Running comprehensive EDA analysis...")
        return self.eda_validator.run_comprehensive_analysis()
    
    def validate_step1_comprehensive(self) -> Dict[str, Any]:
        """Comprehensive validation for Step 1 (API data download)."""
        logger.info("Starting comprehensive Step 1 validation...")
        
        # Run EDA analysis if not already done
        if not os.path.exists(self.eda_results_path):
            self.run_eda_analysis()
        
        results = {}
        
        # Validate store config data across multiple periods
        store_config_files = self._find_files_by_pattern("data/api_data/store_config_*.csv")
        for file_path in store_config_files:
            period = self._extract_period_from_path(file_path)
            logger.info(f"Validating store config for period {period}")
            
            try:
                schema = get_comprehensive_store_config_schema()
                result = validate_file_flexible(file_path, schema)
                results[f"store_config_{period}"] = result
                
                # Additional EDA-based validation
                eda_result = self._validate_with_eda_insights(file_path, 'store_config', period)
                results[f"store_config_{period}_eda"] = eda_result
                
            except Exception as e:
                logger.error(f"Error validating {file_path}: {e}")
                results[f"store_config_{period}"] = {'status': 'error', 'error': str(e)}
        
        # Validate SPU sales data across multiple periods
        spu_sales_files = self._find_files_by_pattern("data/api_data/complete_spu_sales_*.csv")
        for file_path in spu_sales_files:
            period = self._extract_period_from_path(file_path)
            logger.info(f"Validating SPU sales for period {period}")
            
            try:
                schema = get_comprehensive_spu_sales_schema()
                result = validate_file_flexible(file_path, schema)
                results[f"spu_sales_{period}"] = result
                
                # Additional EDA-based validation
                eda_result = self._validate_with_eda_insights(file_path, 'spu_sales', period)
                results[f"spu_sales_{period}_eda"] = eda_result
                
            except Exception as e:
                logger.error(f"Error validating {file_path}: {e}")
                results[f"spu_sales_{period}"] = {'status': 'error', 'error': str(e)}
        
        self.validation_results['step1'] = results
        return results
    
    def _find_files_by_pattern(self, pattern: str) -> List[str]:
        """Find files matching a pattern."""
        files = glob.glob(pattern)
        return [f for f in files if os.path.exists(f)]
    
    def _extract_period_from_path(self, file_path: str) -> str:
        """Extract period from file path."""
        filename = os.path.basename(file_path)
        if '_' in filename:
            parts = filename.split('_')
            for part in parts:
                if len(part) == 7 and part[6] in ['A', 'B']:
                    return part
        return 'unknown'
    
    def _validate_with_eda_insights(self, file_path: str, file_type: str, period: str) -> Dict[str, Any]:
        """Validate file using EDA insights."""
        try:
            df = pd.read_csv(file_path, low_memory=False)
            
            # Basic data quality checks
            quality_checks = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'null_percentage': (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100,
                'duplicate_rows': df.duplicated().sum(),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024
            }
            
            return {
                'status': 'valid',
                'quality_checks': quality_checks
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def validate_step2_comprehensive(self) -> Dict[str, Any]:
        """Comprehensive validation for Step 2 (Coordinate extraction)."""
        logger.info("Starting comprehensive Step 2 validation...")
        results = {}
        
        # Validate coordinate files
        coordinate_files = self._find_files_by_pattern("output/store_coordinates_*.csv")
        for file_path in coordinate_files:
            period = self._extract_period_from_path(file_path)
            logger.info(f"Validating coordinates for period {period}")
            
            try:
                schema = get_comprehensive_store_config_schema()
                result = validate_file_flexible(file_path, schema)
                results[f"coordinates_{period}"] = result
            except Exception as e:
                logger.error(f"Error validating {file_path}: {e}")
                results[f"coordinates_{period}"] = {'status': 'error', 'error': str(e)}
        
        return results
    
    def validate_step3_comprehensive(self) -> Dict[str, Any]:
        """Comprehensive validation for Step 3 (Matrix preparation)."""
        logger.info("Starting comprehensive Step 3 validation...")
        results = {}
        
        # Validate matrix files
        matrix_files = {
            'subcategory': "data/store_subcategory_matrix.csv",
            'spu': "data/store_spu_limited_matrix.csv", 
            'category': "data/store_category_agg_matrix.csv"
        }
        
        for matrix_type, file_path in matrix_files.items():
            if os.path.exists(file_path):
                logger.info(f"Validating {matrix_type} matrix: {file_path}")
                try:
                    schema = get_comprehensive_matrix_schema()
                    result = validate_file_flexible(file_path, schema)
                    results[f"{matrix_type}_matrix"] = result
                except Exception as e:
                    logger.error(f"Error validating {file_path}: {e}")
                    results[f"{matrix_type}_matrix"] = {'status': 'error', 'error': str(e)}
        
        return results
    
    def validate_step4_comprehensive(self) -> Dict[str, Any]:
        """Comprehensive validation for Step 4 (Weather data)."""
        logger.info("Starting comprehensive Step 4 validation...")
        results = {}
        
        # Validate weather files
        weather_files = self._find_files_by_pattern("output/weather_data/*.csv")
        for file_path in weather_files:
            period = self._extract_period_from_path(file_path)
            logger.info(f"Validating weather data for period {period}")
            
            try:
                schema = get_comprehensive_weather_schema()
                result = validate_file_flexible(file_path, schema)
                results[f"weather_{period}"] = result
            except Exception as e:
                logger.error(f"Error validating {file_path}: {e}")
                results[f"weather_{period}"] = {'status': 'error', 'error': str(e)}
        
        # Validate store altitudes
        altitude_file = "output/store_altitudes.csv"
        if os.path.exists(altitude_file):
            logger.info(f"Validating store altitudes: {altitude_file}")
            try:
                result = validate_file_flexible(altitude_file, ComprehensiveStoreConfigSchema)
                results['store_altitudes'] = result
            except Exception as e:
                logger.error(f"Error validating {altitude_file}: {e}")
                results['store_altitudes'] = {'status': 'error', 'error': str(e)}
        
        return results
    
    def validate_step5_comprehensive(self) -> Dict[str, Any]:
        """Comprehensive validation for Step 5 (Feels-like temperature)."""
        logger.info("Starting comprehensive Step 5 validation...")
        results = {}
        
        # Validate feels-like temperature files
        temp_files = self._find_files_by_pattern("output/feels_like_temperature_*.csv")
        for file_path in temp_files:
            period = self._extract_period_from_path(file_path)
            logger.info(f"Validating feels-like temperature for period {period}")
            
            try:
                schema = get_comprehensive_weather_schema()
                result = validate_file_flexible(file_path, schema)
                results[f"feels_like_{period}"] = result
            except Exception as e:
                logger.error(f"Error validating {file_path}: {e}")
                results[f"feels_like_{period}"] = {'status': 'error', 'error': str(e)}
        
        return results
    
    def validate_step6_comprehensive(self) -> Dict[str, Any]:
        """Comprehensive validation for Step 6 (Cluster analysis)."""
        logger.info("Starting comprehensive Step 6 validation...")
        results = {}
        
        # Validate clustering results
        cluster_files = self._find_files_by_pattern("output/clustering_results_*.csv")
        for file_path in cluster_files:
            period = self._extract_period_from_path(file_path)
            logger.info(f"Validating clustering results for period {period}")
            
            try:
                schema = get_comprehensive_clustering_schema()
                result = validate_file_flexible(file_path, schema)
                results[f"clustering_{period}"] = result
            except Exception as e:
                logger.error(f"Error validating {file_path}: {e}")
                results[f"clustering_{period}"] = {'status': 'error', 'error': str(e)}
        
        return results

    def run_all_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation for all steps."""
        logger.info("Starting comprehensive validation for all steps...")
        
        all_results = {}
        
        # Run EDA analysis first
        eda_results = self.run_eda_analysis()
        all_results['eda_analysis'] = eda_results
        
        # Validate each step
        all_results['step1'] = self.validate_step1_comprehensive()
        all_results['step2'] = self.validate_step2_comprehensive()
        all_results['step3'] = self.validate_step3_comprehensive()
        all_results['step4'] = self.validate_step4_comprehensive()
        all_results['step5'] = self.validate_step5_comprehensive()
        all_results['step6'] = self.validate_step6_comprehensive()
        
        # Generate summary report
        summary = self._generate_validation_summary(all_results)
        all_results['summary'] = summary
        
        return all_results
    
    def _generate_validation_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate validation summary report."""
        summary = {
            'total_steps_validated': 6,
            'steps_with_errors': 0,
            'total_files_validated': 0,
            'total_files_passed': 0,
            'total_files_failed': 0,
            'step_summaries': {}
        }
        
        for step, step_results in results.items():
            if step == 'eda_analysis' or step == 'summary':
                continue
                
            step_summary = {
                'files_validated': 0,
                'files_passed': 0,
                'files_failed': 0,
                'errors': []
            }
            
            for file_key, file_result in step_results.items():
                if isinstance(file_result, dict):
                    step_summary['files_validated'] += 1
                    if file_result.get('status') == 'valid':
                        step_summary['files_passed'] += 1
                    else:
                        step_summary['files_failed'] += 1
                        if 'error' in file_result:
                            step_summary['errors'].append(file_result['error'])
            
            summary['step_summaries'][step] = step_summary
            summary['total_files_validated'] += step_summary['files_validated']
            summary['total_files_passed'] += step_summary['files_passed']
            summary['total_files_failed'] += step_summary['files_failed']
            
            if step_summary['files_failed'] > 0:
                summary['steps_with_errors'] += 1
        
        return summary


def run_comprehensive_validation():
    """Run comprehensive validation for all steps."""
    runner = ComprehensiveValidationRunner()
    return runner.run_all_comprehensive_validation()


if __name__ == "__main__":
    results = run_comprehensive_validation()
    print("Comprehensive validation complete!")
    print(f"Summary: {results['summary']}")