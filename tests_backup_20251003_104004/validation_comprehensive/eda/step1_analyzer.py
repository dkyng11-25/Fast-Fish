#!/usr/bin/env python3
"""
Step 1 EDA Analyzer

This module provides EDA analysis specifically for Step 1 (API data download),
focusing on store config and SPU sales data patterns.

Author: Data Pipeline
Date: 2025-01-03
"""

import os
import logging
from typing import Dict, List, Any
from .base_analyzer import BaseEDAAnalyzer

logger = logging.getLogger(__name__)

class Step1EDAAnalyzer(BaseEDAAnalyzer):
    """
    EDA analyzer for Step 1 (API data download).
    
    Focuses on analyzing store configuration and SPU sales data patterns
    to understand data structure and quality for API downloads.
    """
    
    def __init__(self, output_dir: str = "output/eda_reports"):
        super().__init__("step1", output_dir)
    
    def get_target_files(self, period: str) -> List[str]:
        """
        Get target files for Step 1 analysis.
        
        Args:
            period: Time period (e.g., '202508A')
            
        Returns:
            List of file paths to analyze
        """
        target_files = []
        
        # Store config file
        store_config_file = f"data/api_data/store_config_{period}.csv"
        if os.path.exists(store_config_file):
            target_files.append(store_config_file)
        
        # SPU sales file
        spu_sales_file = f"data/api_data/complete_spu_sales_{period}.csv"
        if os.path.exists(spu_sales_file):
            target_files.append(spu_sales_file)
        
        return target_files
    
    def analyze_file_patterns(self, file_path: str, period: str) -> Dict[str, Any]:
        """
        Analyze patterns specific to Step 1 data.
        
        Args:
            file_path: Path to the data file
            period: Time period
            
        Returns:
            Dictionary containing step-specific insights
        """
        insights = self.get_common_data_insights(file_path)
        if not insights:
            return {}
        
        # Add step-specific analysis
        insights.update({
            'file_type': self._classify_file_type(file_path),
            'period': period,
            'step_specific_analysis': self._analyze_step1_patterns(file_path)
        })
        
        return insights
    
    def _classify_file_type(self, file_path: str) -> str:
        """Classify the type of Step 1 file."""
        if 'store_config' in file_path:
            return 'store_config'
        elif 'spu_sales' in file_path:
            return 'spu_sales'
        else:
            return 'unknown'
    
    def _analyze_step1_patterns(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze Step 1 specific patterns.
        
        Args:
            file_path: Path to the data file
            
        Returns:
            Step-specific analysis results
        """
        import pandas as pd
        
        try:
            df = pd.read_csv(file_path, low_memory=False)
            file_type = self._classify_file_type(file_path)
            
            analysis = {
                'file_type': file_type,
                'data_quality': self.calculate_data_quality_metrics(df),
                'column_analysis': self._analyze_step1_columns(df, file_type),
                'business_rules_validation': self._validate_step1_business_rules(df, file_type)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing Step 1 patterns for {file_path}: {e}")
            return {'error': str(e)}
    
    def _analyze_step1_columns(self, df, file_type: str) -> Dict[str, Any]:
        """
        Analyze columns specific to Step 1 data types.
        
        Args:
            df: DataFrame to analyze
            file_type: Type of file (store_config or spu_sales)
            
        Returns:
            Column analysis results
        """
        column_analysis = {}
        
        if file_type == 'store_config':
            # Analyze store config specific columns
            column_analysis = {
                'required_columns': ['str_code', 'store_name', 'region', 'city'],
                'present_required': [col for col in ['str_code', 'store_name', 'region', 'city'] if col in df.columns],
                'missing_required': [col for col in ['str_code', 'store_name', 'region', 'city'] if col not in df.columns],
                'id_column_analysis': self._analyze_id_columns(df, 'str_code'),
                'geographic_columns': self._analyze_geographic_columns(df)
            }
        
        elif file_type == 'spu_sales':
            # Analyze SPU sales specific columns
            column_analysis = {
                'required_columns': ['str_code', 'spu_code', 'sales_quantity', 'sales_amount'],
                'present_required': [col for col in ['str_code', 'spu_code', 'sales_quantity', 'sales_amount'] if col in df.columns],
                'missing_required': [col for col in ['str_code', 'spu_code', 'sales_quantity', 'sales_amount'] if col not in df.columns],
                'id_column_analysis': self._analyze_id_columns(df, 'spu_code'),
                'sales_columns': self._analyze_sales_columns(df)
            }
        
        return column_analysis
    
    def _analyze_id_columns(self, df, expected_id_col: str) -> Dict[str, Any]:
        """
        Analyze ID column patterns.
        
        Args:
            df: DataFrame to analyze
            expected_id_col: Expected ID column name
            
        Returns:
            ID column analysis
        """
        if expected_id_col not in df.columns:
            return {'error': f'Expected ID column {expected_id_col} not found'}
        
        id_series = df[expected_id_col]
        
        return {
            'total_records': len(id_series),
            'unique_values': id_series.nunique(),
            'duplicate_count': len(id_series) - id_series.nunique(),
            'null_count': id_series.isnull().sum(),
            'data_type': str(id_series.dtype),
            'sample_values': id_series.dropna().head(5).tolist()
        }
    
    def _analyze_geographic_columns(self, df) -> Dict[str, Any]:
        """
        Analyze geographic columns in store config.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Geographic column analysis
        """
        geo_columns = ['region', 'city', 'province', 'state']
        present_geo_cols = [col for col in geo_columns if col in df.columns]
        
        analysis = {
            'present_columns': present_geo_cols,
            'region_analysis': {},
            'city_analysis': {}
        }
        
        if 'region' in df.columns:
            analysis['region_analysis'] = {
                'unique_regions': df['region'].nunique(),
                'top_regions': df['region'].value_counts().head(5).to_dict()
            }
        
        if 'city' in df.columns:
            analysis['city_analysis'] = {
                'unique_cities': df['city'].nunique(),
                'top_cities': df['city'].value_counts().head(5).to_dict()
            }
        
        return analysis
    
    def _analyze_sales_columns(self, df) -> Dict[str, Any]:
        """
        Analyze sales columns in SPU sales data.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Sales column analysis
        """
        sales_columns = ['sales_quantity', 'sales_amount', 'unit_price']
        present_sales_cols = [col for col in sales_columns if col in df.columns]
        
        analysis = {
            'present_columns': present_sales_cols,
            'quantity_analysis': {},
            'amount_analysis': {}
        }
        
        if 'sales_quantity' in df.columns:
            qty_series = df['sales_quantity']
            analysis['quantity_analysis'] = {
                'total_quantity': qty_series.sum(),
                'avg_quantity': qty_series.mean(),
                'min_quantity': qty_series.min(),
                'max_quantity': qty_series.max(),
                'zero_quantity_count': (qty_series == 0).sum(),
                'negative_quantity_count': (qty_series < 0).sum()
            }
        
        if 'sales_amount' in df.columns:
            amt_series = df['sales_amount']
            analysis['amount_analysis'] = {
                'total_amount': amt_series.sum(),
                'avg_amount': amt_series.mean(),
                'min_amount': amt_series.min(),
                'max_amount': amt_series.max(),
                'zero_amount_count': (amt_series == 0).sum(),
                'negative_amount_count': (amt_series < 0).sum()
            }
        
        return analysis
    
    def _validate_step1_business_rules(self, df, file_type: str) -> Dict[str, Any]:
        """
        Validate Step 1 business rules.
        
        Args:
            df: DataFrame to validate
            file_type: Type of file
            
        Returns:
            Business rule validation results
        """
        validation_results = {
            'passed_rules': [],
            'failed_rules': [],
            'warnings': []
        }
        
        if file_type == 'store_config':
            # Store config business rules
            if 'str_code' in df.columns:
                if df['str_code'].isnull().any():
                    validation_results['failed_rules'].append("Store codes cannot be null")
                else:
                    validation_results['passed_rules'].append("All store codes are present")
                
                if df['str_code'].duplicated().any():
                    validation_results['failed_rules'].append("Duplicate store codes found")
                else:
                    validation_results['passed_rules'].append("All store codes are unique")
        
        elif file_type == 'spu_sales':
            # SPU sales business rules
            if 'sales_quantity' in df.columns:
                if (df['sales_quantity'] < 0).any():
                    validation_results['failed_rules'].append("Negative sales quantities found")
                else:
                    validation_results['passed_rules'].append("All sales quantities are non-negative")
            
            if 'sales_amount' in df.columns:
                if (df['sales_amount'] < 0).any():
                    validation_results['failed_rules'].append("Negative sales amounts found")
                else:
                    validation_results['passed_rules'].append("All sales amounts are non-negative")
        
        return validation_results
    
    def generate_step_constraints(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate validation constraints specific to Step 1.
        
        Args:
            insights: Analysis insights
            
        Returns:
            Dictionary of validation constraints
        """
        constraints = {}
        
        for file_path, file_insights in insights.items():
            if 'error' in file_insights:
                continue
            
            file_type = file_insights.get('file_type', 'unknown')
            if file_type == 'store_config':
                constraints.update(self._generate_store_config_constraints(file_insights))
            elif file_type == 'spu_sales':
                constraints.update(self._generate_spu_sales_constraints(file_insights))
        
        return constraints
    
    def _generate_store_config_constraints(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Generate constraints for store config data."""
        return {
            'str_code': {
                'dtype': 'string',
                'nullable': False,
                'coerce': True
            },
            'store_name': {
                'dtype': 'string',
                'nullable': False
            },
            'region': {
                'dtype': 'string',
                'nullable': True
            },
            'city': {
                'dtype': 'string',
                'nullable': True
            }
        }
    
    def _generate_spu_sales_constraints(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Generate constraints for SPU sales data."""
        return {
            'str_code': {
                'dtype': 'string',
                'nullable': False,
                'coerce': True
            },
            'spu_code': {
                'dtype': 'string',
                'nullable': False,
                'coerce': True
            },
            'sales_quantity': {
                'dtype': 'float64',
                'nullable': True,
                'ge': 0
            },
            'sales_amount': {
                'dtype': 'float64',
                'nullable': True,
                'ge': 0
            }
        }
    
    def _add_step_specific_analysis(self, insights: Dict[str, Any]) -> str:
        """
        Add Step 1 specific analysis to the report.
        
        Args:
            insights: Analysis insights
            
        Returns:
            Additional report content
        """
        report = "\n## Step 1 Specific Analysis\n\n"
        
        # Add file type analysis
        for file_path, file_insights in insights.get('insights', {}).items():
            if 'error' in file_insights:
                continue
            
            file_type = file_insights.get('file_type', 'unknown')
            report += f"### {file_type.upper()} Analysis\n\n"
            
            if 'step_specific_analysis' in file_insights:
                analysis = file_insights['step_specific_analysis']
                
                # Data quality summary
                if 'data_quality' in analysis:
                    quality = analysis['data_quality']
                    report += f"**Data Quality:**\n"
                    report += f"- Completeness: {quality.get('completeness', 0):.2f}%\n"
                    report += f"- Uniqueness: {quality.get('uniqueness', 0):.2f}%\n\n"
                
                # Business rules validation
                if 'business_rules_validation' in analysis:
                    rules = analysis['business_rules_validation']
                    report += f"**Business Rules Validation:**\n"
                    for rule in rules.get('passed_rules', []):
                        report += f"- ✅ {rule}\n"
                    for rule in rules.get('failed_rules', []):
                        report += f"- ❌ {rule}\n"
                    for warning in rules.get('warnings', []):
                        report += f"- ⚠️ {warning}\n"
                    report += "\n"
        
        return report
