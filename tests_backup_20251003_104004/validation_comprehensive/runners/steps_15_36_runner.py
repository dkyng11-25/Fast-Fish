#!/usr/bin/env python3
"""
Validation Runner for Steps 15-36: Advanced Pipeline Steps

This module provides comprehensive validation for the advanced pipeline steps (15-36)
including historical analysis, dashboards, merchandising optimization, and delivery systems.

Author: Data Pipeline
Date: 2025-01-03
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

# Import common validation utilities
from ..validators import validate_file, validate_dataframe, validate_with_quality_checks
from ..schemas import (
    # Common schemas
    StoreCodeSchema, SPUCodeSchema, SubcategorySchema, ClusterIdSchema,
    SalesAmountSchema, QuantitySchema, PriceSchema, CountSchema,
    # Time schemas
    PeriodSchema, YearSchema, MonthSchema,
    # Product schemas
    ProductClassificationSchema, SalesSummarySchema,
    # Advanced schemas (to be defined)
    HistoricalAnalysisSchema, DashboardSchema, MerchandisingSchema,
    DeliverySchema, OptimizationSchema
)

logger = logging.getLogger(__name__)

class Steps15_36Validator:
    """Comprehensive validator for advanced pipeline steps (15-36)."""
    
    def __init__(self, period: str = "202508A", output_dir: str = "../../output"):
        """Initialize the validator."""
        self.period = period
        self.output_dir = Path(output_dir)
        self.results = {}
        
    def validate_step15_historical_baseline(self) -> Dict[str, Any]:
        """Validate Step 15: Download Historical Baseline."""
        logger.info("Validating Step 15: Historical Baseline Download")
        
        results = {
            'step': 'step15',
            'period': self.period,
            'status': 'pending',
            'files_checked': 0,
            'files_valid': 0,
            'validation_errors': [],
            'warnings': []
        }
        
        # Expected output files for Step 15
        expected_files = [
            f'historical_baseline_{self.period}.csv',
            f'historical_insights_{self.period}.json',
            f'baseline_comparison_{self.period}.csv'
        ]
        
        for filename in expected_files:
            file_path = self.output_dir / filename
            results['files_checked'] += 1
            
            if not file_path.exists():
                results['validation_errors'].append(f"Missing file: {filename}")
                continue
                
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                    if df.empty:
                        results['warnings'].append(f"File {filename} is empty")
                        continue
                    
                    # Validate historical baseline schema
                    self._validate_historical_baseline_schema(df, filename)
                    results['files_valid'] += 1
                    
                elif filename.endswith('.json'):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    self._validate_historical_insights(data, filename)
                    results['files_valid'] += 1
                    
            except Exception as e:
                results['validation_errors'].append(f"Validation error in {filename}: {str(e)}")
        
        results['status'] = 'passed' if results['files_valid'] == results['files_checked'] else 'failed'
        return results
    
    def validate_step16_comparison_tables(self) -> Dict[str, Any]:
        """Validate Step 16: Create Comparison Tables."""
        logger.info("Validating Step 16: Comparison Tables")
        
        results = {
            'step': 'step16',
            'period': self.period,
            'status': 'pending',
            'files_checked': 0,
            'files_valid': 0,
            'validation_errors': [],
            'warnings': []
        }
        
        expected_files = [
            f'comparison_tables_{self.period}.xlsx',
            f'comparison_summary_{self.period}.csv',
            f'comparison_metrics_{self.period}.json'
        ]
        
        for filename in expected_files:
            file_path = self.output_dir / filename
            results['files_checked'] += 1
            
            if not file_path.exists():
                results['validation_errors'].append(f"Missing file: {filename}")
                continue
                
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                    self._validate_comparison_schema(df, filename)
                    results['files_valid'] += 1
                elif filename.endswith('.xlsx'):
                    # Excel file validation
                    self._validate_excel_file(file_path, filename)
                    results['files_valid'] += 1
                elif filename.endswith('.json'):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    self._validate_comparison_metrics(data, filename)
                    results['files_valid'] += 1
                    
            except Exception as e:
                results['validation_errors'].append(f"Validation error in {filename}: {str(e)}")
        
        results['status'] = 'passed' if results['files_valid'] == results['files_checked'] else 'failed'
        return results
    
    def validate_step17_augment_recommendations(self) -> Dict[str, Any]:
        """Validate Step 17: Augment Recommendations."""
        logger.info("Validating Step 17: Augment Recommendations")
        
        results = {
            'step': 'step17',
            'period': self.period,
            'status': 'pending',
            'files_checked': 0,
            'files_valid': 0,
            'validation_errors': [],
            'warnings': []
        }
        
        expected_files = [
            f'augmented_recommendations_{self.period}.csv',
            f'recommendation_metadata_{self.period}.json',
            f'recommendation_quality_{self.period}.csv'
        ]
        
        for filename in expected_files:
            file_path = self.output_dir / filename
            results['files_checked'] += 1
            
            if not file_path.exists():
                results['validation_errors'].append(f"Missing file: {filename}")
                continue
                
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                    self._validate_recommendation_schema(df, filename)
                    results['files_valid'] += 1
                elif filename.endswith('.json'):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    self._validate_recommendation_metadata(data, filename)
                    results['files_valid'] += 1
                    
            except Exception as e:
                results['validation_errors'].append(f"Validation error in {filename}: {str(e)}")
        
        results['status'] = 'passed' if results['files_valid'] == results['files_checked'] else 'failed'
        return results
    
    def validate_step18_validate_results(self) -> Dict[str, Any]:
        """Validate Step 18: Validate Results."""
        logger.info("Validating Step 18: Validate Results")
        
        results = {
            'step': 'step18',
            'period': self.period,
            'status': 'pending',
            'files_checked': 0,
            'files_valid': 0,
            'validation_errors': [],
            'warnings': []
        }
        
        expected_files = [
            f'validation_report_{self.period}.json',
            f'validation_summary_{self.period}.csv',
            f'validation_details_{self.period}.xlsx'
        ]
        
        for filename in expected_files:
            file_path = self.output_dir / filename
            results['files_checked'] += 1
            
            if not file_path.exists():
                results['validation_errors'].append(f"Missing file: {filename}")
                continue
                
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                    self._validate_validation_summary_schema(df, filename)
                    results['files_valid'] += 1
                elif filename.endswith('.json'):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    self._validate_validation_report(data, filename)
                    results['files_valid'] += 1
                elif filename.endswith('.xlsx'):
                    self._validate_excel_file(file_path, filename)
                    results['files_valid'] += 1
                    
            except Exception as e:
                results['validation_errors'].append(f"Validation error in {filename}: {str(e)}")
        
        results['status'] = 'passed' if results['files_valid'] == results['files_checked'] else 'failed'
        return results
    
    def validate_step19_detailed_spu_breakdown(self) -> Dict[str, Any]:
        """Validate Step 19: Detailed SPU Breakdown."""
        logger.info("Validating Step 19: Detailed SPU Breakdown")
        
        results = {
            'step': 'step19',
            'period': self.period,
            'status': 'pending',
            'files_checked': 0,
            'files_valid': 0,
            'validation_errors': [],
            'warnings': []
        }
        
        expected_files = [
            f'detailed_spu_breakdown_{self.period}.csv',
            f'spu_breakdown_summary_{self.period}.md',
            f'spu_performance_metrics_{self.period}.json'
        ]
        
        for filename in expected_files:
            file_path = self.output_dir / filename
            results['files_checked'] += 1
            
            if not file_path.exists():
                results['validation_errors'].append(f"Missing file: {filename}")
                continue
                
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                    self._validate_spu_breakdown_schema(df, filename)
                    results['files_valid'] += 1
                elif filename.endswith('.md'):
                    # Markdown file validation
                    self._validate_markdown_file(file_path, filename)
                    results['files_valid'] += 1
                elif filename.endswith('.json'):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    self._validate_spu_metrics(data, filename)
                    results['files_valid'] += 1
                    
            except Exception as e:
                results['validation_errors'].append(f"Validation error in {filename}: {str(e)}")
        
        results['status'] = 'passed' if results['files_valid'] == results['files_checked'] else 'failed'
        return results
    
    def validate_step20_data_validation(self) -> Dict[str, Any]:
        """Validate Step 20: Data Validation."""
        logger.info("Validating Step 20: Data Validation")
        
        results = {
            'step': 'step20',
            'period': self.period,
            'status': 'pending',
            'files_checked': 0,
            'files_valid': 0,
            'validation_errors': [],
            'warnings': []
        }
        
        expected_files = [
            f'data_validation_report_{self.period}.json',
            f'data_quality_metrics_{self.period}.csv',
            f'validation_errors_{self.period}.csv'
        ]
        
        for filename in expected_files:
            file_path = self.output_dir / filename
            results['files_checked'] += 1
            
            if not file_path.exists():
                results['validation_errors'].append(f"Missing file: {filename}")
                continue
                
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                    self._validate_data_quality_schema(df, filename)
                    results['files_valid'] += 1
                elif filename.endswith('.json'):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    self._validate_data_validation_report(data, filename)
                    results['files_valid'] += 1
                    
            except Exception as e:
                results['validation_errors'].append(f"Validation error in {filename}: {str(e)}")
        
        results['status'] = 'passed' if results['files_valid'] == results['files_checked'] else 'failed'
        return results
    
    def validate_steps_21_24_labeling_analysis(self) -> Dict[str, Any]:
        """Validate Steps 21-24: Labeling and Analysis."""
        logger.info("Validating Steps 21-24: Labeling and Analysis")
        
        results = {
            'step': 'steps_21_24',
            'period': self.period,
            'status': 'pending',
            'files_checked': 0,
            'files_valid': 0,
            'validation_errors': [],
            'warnings': []
        }
        
        expected_files = [
            f'label_tag_recommendations_{self.period}.csv',
            f'store_attribute_enrichment_{self.period}.csv',
            f'clustering_features_{self.period}.csv',
            f'comprehensive_cluster_labels_{self.period}.csv',
            f'cluster_labeling_summary_{self.period}.json'
        ]
        
        for filename in expected_files:
            file_path = self.output_dir / filename
            results['files_checked'] += 1
            
            if not file_path.exists():
                results['validation_errors'].append(f"Missing file: {filename}")
                continue
                
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                    self._validate_labeling_schema(df, filename)
                    results['files_valid'] += 1
                elif filename.endswith('.json'):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    self._validate_cluster_labeling_summary(data, filename)
                    results['files_valid'] += 1
                    
            except Exception as e:
                results['validation_errors'].append(f"Validation error in {filename}: {str(e)}")
        
        results['status'] = 'passed' if results['files_valid'] == results['files_checked'] else 'failed'
        return results
    
    def validate_steps_25_29_analysis_optimization(self) -> Dict[str, Any]:
        """Validate Steps 25-29: Analysis and Optimization."""
        logger.info("Validating Steps 25-29: Analysis and Optimization")
        
        results = {
            'step': 'steps_25_29',
            'period': self.period,
            'status': 'pending',
            'files_checked': 0,
            'files_valid': 0,
            'validation_errors': [],
            'warnings': []
        }
        
        expected_files = [
            f'product_role_classifier_{self.period}.csv',
            f'price_elasticity_analysis_{self.period}.csv',
            f'gap_matrix_{self.period}.csv',
            f'scenario_analysis_{self.period}.csv',
            f'supply_demand_gap_{self.period}.csv'
        ]
        
        for filename in expected_files:
            file_path = self.output_dir / filename
            results['files_checked'] += 1
            
            if not file_path.exists():
                results['validation_errors'].append(f"Missing file: {filename}")
                continue
                
            try:
                df = pd.read_csv(file_path)
                self._validate_analysis_schema(df, filename)
                results['files_valid'] += 1
                    
            except Exception as e:
                results['validation_errors'].append(f"Validation error in {filename}: {str(e)}")
        
        results['status'] = 'passed' if results['files_valid'] == results['files_checked'] else 'failed'
        return results
    
    def validate_steps_30_36_merchandising_delivery(self) -> Dict[str, Any]:
        """Validate Steps 30-36: Merchandising and Delivery."""
        logger.info("Validating Steps 30-36: Merchandising and Delivery")
        
        results = {
            'step': 'steps_30_36',
            'period': self.period,
            'status': 'pending',
            'files_checked': 0,
            'files_valid': 0,
            'validation_errors': [],
            'warnings': []
        }
        
        expected_files = [
            f'sellthrough_optimization_{self.period}.csv',
            f'gap_analysis_workbook_{self.period}.xlsx',
            f'enhanced_store_clustering_{self.period}.csv',
            f'store_allocation_{self.period}.csv',
            f'store_level_merchandising_{self.period}.csv',
            f'cluster_level_merchandising_{self.period}.csv',
            f'unified_delivery_{self.period}.csv',
            f'customer_delivery_format_{self.period}.csv'
        ]
        
        for filename in expected_files:
            file_path = self.output_dir / filename
            results['files_checked'] += 1
            
            if not file_path.exists():
                results['validation_errors'].append(f"Missing file: {filename}")
                continue
                
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                    self._validate_merchandising_schema(df, filename)
                    results['files_valid'] += 1
                elif filename.endswith('.xlsx'):
                    self._validate_excel_file(file_path, filename)
                    results['files_valid'] += 1
                    
            except Exception as e:
                results['validation_errors'].append(f"Validation error in {filename}: {str(e)}")
        
        results['status'] = 'passed' if results['files_valid'] == results['files_checked'] else 'failed'
        return results
    
    # Schema validation methods
    def _validate_historical_baseline_schema(self, df: pd.DataFrame, filename: str) -> None:
        """Validate historical baseline schema."""
        required_cols = ['str_code', 'period', 'baseline_value', 'current_value', 'change_pct']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in {filename}: {missing_cols}")
        
        # Validate data types and ranges
        if 'change_pct' in df.columns:
            if not df['change_pct'].between(-100, 1000).all():
                raise ValueError(f"Invalid change_pct values in {filename}")
    
    def _validate_historical_insights(self, data: dict, filename: str) -> None:
        """Validate historical insights JSON."""
        required_keys = ['period', 'insights', 'metrics', 'summary']
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise ValueError(f"Missing required keys in {filename}: {missing_keys}")
    
    def _validate_comparison_schema(self, df: pd.DataFrame, filename: str) -> None:
        """Validate comparison table schema."""
        required_cols = ['str_code', 'metric_name', 'current_value', 'baseline_value', 'comparison']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in {filename}: {missing_cols}")
    
    def _validate_excel_file(self, file_path: Path, filename: str) -> None:
        """Validate Excel file exists and is readable."""
        try:
            pd.read_excel(file_path, sheet_name=None)
        except Exception as e:
            raise ValueError(f"Cannot read Excel file {filename}: {str(e)}")
    
    def _validate_recommendation_schema(self, df: pd.DataFrame, filename: str) -> None:
        """Validate recommendation schema."""
        required_cols = ['str_code', 'spu_code', 'recommendation_type', 'priority', 'confidence']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in {filename}: {missing_cols}")
    
    def _validate_recommendation_metadata(self, data: dict, filename: str) -> None:
        """Validate recommendation metadata JSON."""
        required_keys = ['total_recommendations', 'by_type', 'by_priority', 'quality_metrics']
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise ValueError(f"Missing required keys in {filename}: {missing_keys}")
    
    def _validate_validation_summary_schema(self, df: pd.DataFrame, filename: str) -> None:
        """Validate validation summary schema."""
        required_cols = ['validation_type', 'status', 'count', 'percentage']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in {filename}: {missing_cols}")
    
    def _validate_validation_report(self, data: dict, filename: str) -> None:
        """Validate validation report JSON."""
        required_keys = ['overall_status', 'validation_results', 'summary', 'timestamp']
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise ValueError(f"Missing required keys in {filename}: {missing_keys}")
    
    def _validate_spu_breakdown_schema(self, df: pd.DataFrame, filename: str) -> None:
        """Validate SPU breakdown schema."""
        required_cols = ['spu_code', 'str_code', 'category', 'subcategory', 'performance_metrics']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in {filename}: {missing_cols}")
    
    def _validate_markdown_file(self, file_path: Path, filename: str) -> None:
        """Validate markdown file exists and has content."""
        if file_path.stat().st_size == 0:
            raise ValueError(f"Markdown file {filename} is empty")
    
    def _validate_spu_metrics(self, data: dict, filename: str) -> None:
        """Validate SPU metrics JSON."""
        required_keys = ['total_spus', 'performance_distribution', 'top_performers', 'metrics']
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise ValueError(f"Missing required keys in {filename}: {missing_keys}")
    
    def _validate_data_quality_schema(self, df: pd.DataFrame, filename: str) -> None:
        """Validate data quality schema."""
        required_cols = ['metric_name', 'value', 'threshold', 'status', 'description']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in {filename}: {missing_cols}")
    
    def _validate_data_validation_report(self, data: dict, filename: str) -> None:
        """Validate data validation report JSON."""
        required_keys = ['validation_summary', 'quality_metrics', 'issues', 'recommendations']
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise ValueError(f"Missing required keys in {filename}: {missing_keys}")
    
    def _validate_labeling_schema(self, df: pd.DataFrame, filename: str) -> None:
        """Validate labeling schema."""
        required_cols = ['str_code', 'label_type', 'label_value', 'confidence', 'source']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in {filename}: {missing_cols}")
    
    def _validate_cluster_labeling_summary(self, data: dict, filename: str) -> None:
        """Validate cluster labeling summary JSON."""
        required_keys = ['total_clusters', 'labeling_coverage', 'label_distribution', 'quality_metrics']
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            raise ValueError(f"Missing required keys in {filename}: {missing_keys}")
    
    def _validate_analysis_schema(self, df: pd.DataFrame, filename: str) -> None:
        """Validate analysis schema."""
        required_cols = ['str_code', 'spu_code', 'analysis_type', 'value', 'confidence']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in {filename}: {missing_cols}")
    
    def _validate_merchandising_schema(self, df: pd.DataFrame, filename: str) -> None:
        """Validate merchandising schema."""
        required_cols = ['str_code', 'spu_code', 'recommendation', 'priority', 'impact']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in {filename}: {missing_cols}")


# Convenience functions for individual step validation
def validate_step15_historical_baseline(period: str = "202508A") -> Dict[str, Any]:
    """Validate Step 15: Historical Baseline."""
    validator = Steps15_36Validator(period)
    return validator.validate_step15_historical_baseline()

def validate_step16_comparison_tables(period: str = "202508A") -> Dict[str, Any]:
    """Validate Step 16: Comparison Tables."""
    validator = Steps15_36Validator(period)
    return validator.validate_step16_comparison_tables()

def validate_step17_augment_recommendations(period: str = "202508A") -> Dict[str, Any]:
    """Validate Step 17: Augment Recommendations."""
    validator = Steps15_36Validator(period)
    return validator.validate_step17_augment_recommendations()

def validate_step18_validate_results(period: str = "202508A") -> Dict[str, Any]:
    """Validate Step 18: Validate Results."""
    validator = Steps15_36Validator(period)
    return validator.validate_step18_validate_results()

def validate_step19_detailed_spu_breakdown(period: str = "202508A") -> Dict[str, Any]:
    """Validate Step 19: Detailed SPU Breakdown."""
    validator = Steps15_36Validator(period)
    return validator.validate_step19_detailed_spu_breakdown()

def validate_step20_data_validation(period: str = "202508A") -> Dict[str, Any]:
    """Validate Step 20: Data Validation."""
    validator = Steps15_36Validator(period)
    return validator.validate_step20_data_validation()

def validate_steps_21_24_labeling_analysis(period: str = "202508A") -> Dict[str, Any]:
    """Validate Steps 21-24: Labeling and Analysis."""
    validator = Steps15_36Validator(period)
    return validator.validate_steps_21_24_labeling_analysis()

def validate_steps_25_29_analysis_optimization(period: str = "202508A") -> Dict[str, Any]:
    """Validate Steps 25-29: Analysis and Optimization."""
    validator = Steps15_36Validator(period)
    return validator.validate_steps_25_29_analysis_optimization()

def validate_steps_30_36_merchandising_delivery(period: str = "202508A") -> Dict[str, Any]:
    """Validate Steps 30-36: Merchandising and Delivery."""
    validator = Steps15_36Validator(period)
    return validator.validate_steps_30_36_merchandising_delivery()

def run_steps_15_36_validation(period: str = "202508A") -> Dict[str, Any]:
    """Run comprehensive validation for steps 15-36."""
    logger.info(f"Running comprehensive validation for steps 15-36 (period: {period})")
    
    validator = Steps15_36Validator(period)
    
    # Run all validations
    results = {
        'period': period,
        'timestamp': datetime.now().isoformat(),
        'steps': {},
        'summary': {}
    }
    
    # Individual step validations
    step_validators = [
        ('step15', validator.validate_step15_historical_baseline),
        ('step16', validator.validate_step16_comparison_tables),
        ('step17', validator.validate_step17_augment_recommendations),
        ('step18', validator.validate_step18_validate_results),
        ('step19', validator.validate_step19_detailed_spu_breakdown),
        ('step20', validator.validate_step20_data_validation),
        ('steps_21_24', validator.validate_steps_21_24_labeling_analysis),
        ('steps_25_29', validator.validate_steps_25_29_analysis_optimization),
        ('steps_30_36', validator.validate_steps_30_36_merchandising_delivery)
    ]
    
    total_steps = len(step_validators)
    passed_steps = 0
    failed_steps = 0
    
    for step_name, validator_func in step_validators:
        logger.info(f"Validating {step_name}...")
        step_result = validator_func()
        results['steps'][step_name] = step_result
        
        if step_result['status'] == 'passed':
            passed_steps += 1
        else:
            failed_steps += 1
    
    # Generate summary
    results['summary'] = {
        'total_steps': total_steps,
        'passed_steps': passed_steps,
        'failed_steps': failed_steps,
        'success_rate': (passed_steps / total_steps) * 100 if total_steps > 0 else 0,
        'overall_status': 'passed' if failed_steps == 0 else 'failed'
    }
    
    logger.info(f"Steps 15-36 validation completed: {results['summary']['success_rate']:.1f}% success rate")
    return results






