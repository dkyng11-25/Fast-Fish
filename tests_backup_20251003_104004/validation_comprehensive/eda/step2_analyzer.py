#!/usr/bin/env python3
"""
Step 2 EDA Analyzer

This module provides EDA analysis specifically for Step 2 (data preprocessing),
focusing on cleaned and processed data patterns.

Author: Data Pipeline
Date: 2025-01-03
"""

import os
import logging
from typing import Dict, List, Any
from .base_analyzer import BaseEDAAnalyzer

logger = logging.getLogger(__name__)

class Step2EDAAnalyzer(BaseEDAAnalyzer):
    """
    EDA analyzer for Step 2 (data preprocessing).
    
    Focuses on analyzing cleaned and processed data patterns
    to understand data quality improvements and transformations.
    """
    
    def __init__(self, output_dir: str = "output/eda_reports"):
        super().__init__("step2", output_dir)
    
    def get_target_files(self, period: str) -> List[str]:
        """Get target files for Step 2 analysis."""
        target_files = []
        
        # Look for processed data files
        processed_files = [
            f"data/processed_data/cleaned_store_config_{period}.csv",
            f"data/processed_data/cleaned_spu_sales_{period}.csv",
            f"output/processed_data/cleaned_store_config_{period}.csv",
            f"output/processed_data/cleaned_spu_sales_{period}.csv"
        ]
        
        for file_path in processed_files:
            if os.path.exists(file_path):
                target_files.append(file_path)
        
        return target_files
    
    def analyze_file_patterns(self, file_path: str, period: str) -> Dict[str, Any]:
        """Analyze patterns specific to Step 2 data."""
        insights = self.get_common_data_insights(file_path)
        if not insights:
            return {}
        
        insights.update({
            'file_type': 'processed_data',
            'period': period,
            'step_specific_analysis': self._analyze_preprocessing_patterns(file_path)
        })
        
        return insights
    
    def _analyze_preprocessing_patterns(self, file_path: str) -> Dict[str, Any]:
        """Analyze preprocessing specific patterns."""
        import pandas as pd
        
        try:
            df = pd.read_csv(file_path, low_memory=False)
            
            return {
                'data_quality': self.calculate_data_quality_metrics(df),
                'preprocessing_validation': self._validate_preprocessing_rules(df),
                'data_transformations': self._analyze_data_transformations(df)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing preprocessing patterns for {file_path}: {e}")
            return {'error': str(e)}
    
    def _validate_preprocessing_rules(self, df) -> Dict[str, Any]:
        """Validate preprocessing business rules."""
        validation_results = {
            'passed_rules': [],
            'failed_rules': [],
            'warnings': []
        }
        
        # Check for data consistency
        if df.empty:
            validation_results['failed_rules'].append("Empty dataset after preprocessing")
        else:
            validation_results['passed_rules'].append("Dataset contains data after preprocessing")
        
        # Check for excessive null values
        null_percentage = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        if null_percentage > 50:
            validation_results['failed_rules'].append(f"High null percentage: {null_percentage:.2f}%")
        else:
            validation_results['passed_rules'].append(f"Acceptable null percentage: {null_percentage:.2f}%")
        
        return validation_results
    
    def _analyze_data_transformations(self, df) -> Dict[str, Any]:
        """Analyze data transformations applied during preprocessing."""
        return {
            'shape_after_preprocessing': df.shape,
            'column_types': self.identify_column_types(df),
            'data_consistency_checks': self._check_data_consistency(df)
        }
    
    def _check_data_consistency(self, df) -> Dict[str, Any]:
        """Check data consistency after preprocessing."""
        return {
            'duplicate_rows': df.duplicated().sum(),
            'inconsistent_dtypes': self._find_inconsistent_dtypes(df),
            'outlier_columns': self._identify_outlier_columns(df)
        }
    
    def _find_inconsistent_dtypes(self, df) -> List[str]:
        """Find columns with inconsistent data types."""
        inconsistent = []
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    pd.to_numeric(df[col], errors='raise')
                    inconsistent.append(col)
                except:
                    pass
        return inconsistent
    
    def _identify_outlier_columns(self, df) -> List[str]:
        """Identify columns with significant outliers."""
        outlier_cols = []
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
            if len(outliers) > len(df) * 0.05:  # More than 5% outliers
                outlier_cols.append(col)
        
        return outlier_cols
    
    def generate_step_constraints(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Generate validation constraints specific to Step 2."""
        return {
            'processed_data': {
                'dtype': 'object',
                'nullable': True,
                'coerce': True
            }
        }
    
    def _add_step_specific_analysis(self, insights: Dict[str, Any]) -> str:
        """Add Step 2 specific analysis to the report."""
        report = "\n## Step 2 Specific Analysis\n\n"
        report += "### Data Preprocessing Quality\n\n"
        
        for file_path, file_insights in insights.get('insights', {}).items():
            if 'error' in file_insights:
                continue
            
            if 'step_specific_analysis' in file_insights:
                analysis = file_insights['step_specific_analysis']
                
                if 'preprocessing_validation' in analysis:
                    rules = analysis['preprocessing_validation']
                    report += f"**Preprocessing Validation:**\n"
                    for rule in rules.get('passed_rules', []):
                        report += f"- ✅ {rule}\n"
                    for rule in rules.get('failed_rules', []):
                        report += f"- ❌ {rule}\n"
                    report += "\n"
        
        return report
