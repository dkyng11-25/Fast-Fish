#!/usr/bin/env python3
"""
Modular Comprehensive Validation Runner

This module provides a modular, step-specific validation system that reduces
complexity by focusing on targeted analysis rather than comprehensive analysis
of all files. Each step has its own EDA analyzer.

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

from ..eda import StepEDAFactory
from ..schemas.comprehensive_schemas import (
    get_comprehensive_store_config_schema,
    get_comprehensive_spu_sales_schema,
    get_comprehensive_weather_schema,
    get_comprehensive_clustering_schema,
    get_comprehensive_matrix_schema
)
from ..validators import validate_file_flexible

logger = logging.getLogger(__name__)

class ModularComprehensiveRunner:
    """
    Modular comprehensive validation runner that uses step-specific EDA analyzers.
    
    This approach reduces complexity by:
    1. Focusing on step-specific analysis rather than comprehensive analysis
    2. Using targeted file discovery instead of analyzing all files
    3. Providing modular, maintainable code structure
    4. Reducing memory usage and processing time
    """
    
    def __init__(self, output_dir: str = "output/eda_reports"):
        self.output_dir = output_dir
        self.validation_results = {}
        self.eda_factory = StepEDAFactory()
        
    def validate_step(self, step_name: str, period: str) -> Dict[str, Any]:
        """
        Validate a specific step for a given period.
        
        Args:
            step_name: Name of the step to validate (e.g., 'step1', 'step2')
            period: Time period to validate (e.g., '202508A')
            
        Returns:
            Validation results dictionary
        """
        logger.info(f"Starting modular validation for {step_name} period {period}")
        
        # Run step-specific EDA analysis
        eda_results = self.eda_factory.analyze_step(step_name, period, self.output_dir)
        
        if 'error' in eda_results:
            logger.error(f"EDA analysis failed for {step_name}: {eda_results['error']}")
            return {'error': eda_results['error']}
        
        # Run step-specific validation
        validation_results = self._run_step_validation(step_name, period, eda_results)
        
        # Combine results
        combined_results = {
            'step': step_name,
            'period': period,
            'eda_results': eda_results,
            'validation_results': validation_results,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        # Save results
        self._save_step_results(step_name, period, combined_results)
        
        return combined_results
    
    def validate_multiple_steps(self, steps: List[str], period: str) -> Dict[str, Any]:
        """
        Validate multiple steps for a given period.
        
        Args:
            steps: List of step names to validate
            period: Time period to validate
            
        Returns:
            Dictionary mapping step names to validation results
        """
        logger.info(f"Starting modular validation for steps {steps} period {period}")
        
        all_results = {}
        
        for step_name in steps:
            try:
                step_results = self.validate_step(step_name, period)
                all_results[step_name] = step_results
            except Exception as e:
                logger.error(f"Error validating {step_name}: {e}")
                all_results[step_name] = {'error': str(e)}
        
        return all_results
    
    def _run_step_validation(self, step_name: str, period: str, eda_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run validation for a specific step based on EDA results.
        
        Args:
            step_name: Name of the step
            period: Time period
            eda_results: EDA analysis results
            
        Returns:
            Validation results
        """
        validation_results = {
            'step': step_name,
            'period': period,
            'files_validated': [],
            'validation_summary': {},
            'errors': []
        }
        
        # Get target files for this step
        target_files = self._get_step_target_files(step_name, period)
        
        for file_path in target_files:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                continue
            
            try:
                # Get appropriate schema for this step
                schema = self._get_step_schema(step_name)
                if not schema:
                    logger.warning(f"No schema available for {step_name}")
                    continue
                
                # Validate file
                file_validation = validate_file_flexible(file_path, schema)
                validation_results['files_validated'].append(file_path)
                validation_results['validation_summary'][file_path] = file_validation
                
            except Exception as e:
                logger.error(f"Error validating {file_path}: {e}")
                validation_results['errors'].append(f"{file_path}: {str(e)}")
        
        return validation_results
    
    def _get_step_target_files(self, step_name: str, period: str) -> List[str]:
        """
        Get target files for a specific step and period.
        
        Args:
            step_name: Name of the step
            period: Time period
            
        Returns:
            List of target file paths
        """
        # Create a temporary analyzer to get target files
        analyzer = self.eda_factory.create_analyzer(step_name, self.output_dir)
        if not analyzer:
            return []
        
        return analyzer.get_target_files(period)
    
    def _get_step_schema(self, step_name: str):
        """
        Get the appropriate schema for a step.
        
        Args:
            step_name: Name of the step
            
        Returns:
            Pandera schema or None
        """
        schema_mapping = {
            'step1': get_comprehensive_store_config_schema,
            'step2': get_comprehensive_spu_sales_schema,
            'step3': get_comprehensive_clustering_schema,
            'step4': get_comprehensive_weather_schema,
            'step5': get_comprehensive_matrix_schema,
            'step6': get_comprehensive_matrix_schema
        }
        
        schema_func = schema_mapping.get(step_name)
        if schema_func:
            try:
                return schema_func()
            except Exception as e:
                logger.error(f"Error getting schema for {step_name}: {e}")
                return None
        
        return None
    
    def _save_step_results(self, step_name: str, period: str, results: Dict[str, Any]) -> str:
        """
        Save step validation results.
        
        Args:
            step_name: Name of the step
            period: Time period
            results: Results to save
            
        Returns:
            Path to saved file
        """
        results_dir = Path(self.output_dir) / "validation_results"
        results_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{step_name}_{period}_validation.json"
        results_path = results_dir / filename
        
        import json
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Saved {step_name} validation results to {results_path}")
        return str(results_path)
    
    def get_supported_steps(self) -> List[str]:
        """
        Get list of supported pipeline steps.
        
        Returns:
            List of supported step names
        """
        return self.eda_factory.get_supported_steps()
    
    def run_targeted_analysis(self, step_name: str, period: str, specific_files: List[str] = None) -> Dict[str, Any]:
        """
        Run targeted analysis for specific files within a step.
        
        Args:
            step_name: Name of the step
            period: Time period
            specific_files: Optional list of specific files to analyze
            
        Returns:
            Analysis results
        """
        logger.info(f"Running targeted analysis for {step_name} period {period}")
        
        analyzer = self.eda_factory.create_analyzer(step_name, self.output_dir)
        if not analyzer:
            return {'error': f'No analyzer available for step {step_name}'}
        
        if specific_files:
            # Analyze specific files
            results = {}
            for file_path in specific_files:
                if os.path.exists(file_path):
                    file_insights = analyzer.analyze_file_patterns(file_path, period)
                    results[file_path] = file_insights
                else:
                    results[file_path] = {'error': 'File not found'}
            
            return {
                'step': step_name,
                'period': period,
                'targeted_files': specific_files,
                'analysis_results': results
            }
        else:
            # Run full step analysis
            return analyzer.analyze_period(period)
    
    def generate_comprehensive_report(self, results: Dict[str, Any]) -> str:
        """
        Generate a comprehensive report from validation results.
        
        Args:
            results: Validation results dictionary
            
        Returns:
            Markdown report content
        """
        report = f"""# Modular Comprehensive Validation Report

**Generated:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

This report contains validation results from the modular comprehensive validation system,
which focuses on step-specific analysis rather than comprehensive analysis of all files.

## Validation Results

"""
        
        for step_name, step_results in results.items():
            if 'error' in step_results:
                report += f"### {step_name.upper()}\n\n"
                report += f"❌ **Error:** {step_results['error']}\n\n"
                continue
            
            report += f"### {step_name.upper()}\n\n"
            report += f"**Period:** {step_results.get('period', 'N/A')}\n"
            report += f"**Files Validated:** {len(step_results.get('validation_results', {}).get('files_validated', []))}\n"
            
            if 'validation_results' in step_results:
                validation = step_results['validation_results']
                if validation.get('errors'):
                    report += f"**Errors:** {len(validation['errors'])}\n"
                    for error in validation['errors']:
                        report += f"- {error}\n"
                else:
                    report += "✅ **No validation errors**\n"
            
            report += "\n"
        
        return report


def run_modular_validation(step_name: str, period: str, output_dir: str = "output/eda_reports") -> Dict[str, Any]:
    """
    Convenience function to run modular validation for a single step.
    
    Args:
        step_name: Name of the step to validate
        period: Time period to validate
        output_dir: Output directory for reports
        
    Returns:
        Validation results
    """
    runner = ModularComprehensiveRunner(output_dir)
    return runner.validate_step(step_name, period)


def run_multiple_steps_validation(steps: List[str], period: str, output_dir: str = "output/eda_reports") -> Dict[str, Any]:
    """
    Convenience function to run modular validation for multiple steps.
    
    Args:
        steps: List of step names to validate
        period: Time period to validate
        output_dir: Output directory for reports
        
    Returns:
        Validation results
    """
    runner = ModularComprehensiveRunner(output_dir)
    return runner.validate_multiple_steps(steps, period)
