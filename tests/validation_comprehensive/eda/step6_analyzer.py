#!/usr/bin/env python3
"""
Step 6 EDA Analyzer

This module provides EDA analysis specifically for Step 6 (model training),
focusing on training data and model performance patterns.

Author: Data Pipeline
Date: 2025-01-03
"""

import os
import logging
from typing import Dict, List, Any
from .base_analyzer import BaseEDAAnalyzer

logger = logging.getLogger(__name__)

class Step6EDAAnalyzer(BaseEDAAnalyzer):
    """EDA analyzer for Step 6 (model training)."""
    
    def __init__(self, output_dir: str = "output/eda_reports"):
        super().__init__("step6", output_dir)
    
    def get_target_files(self, period: str) -> List[str]:
        """Get target files for Step 6 analysis."""
        target_files = []
        
        # Look for model training files
        model_files = [
            f"data/training_data/training_{period}.csv",
            f"output/training_data/training_{period}.csv",
            f"data/model_data/model_{period}.csv",
            f"output/model_data/model_{period}.csv"
        ]
        
        for file_path in model_files:
            if os.path.exists(file_path):
                target_files.append(file_path)
        
        return target_files
    
    def analyze_file_patterns(self, file_path: str, period: str) -> Dict[str, Any]:
        """Analyze patterns specific to Step 6 data."""
        insights = self.get_common_data_insights(file_path)
        if not insights:
            return {}
        
        file_type = self._classify_file_type(file_path)
        insights.update({
            'file_type': file_type,
            'period': period,
            'step_specific_analysis': self._analyze_model_patterns(file_path, file_type)
        })
        
        return insights
    
    def _classify_file_type(self, file_path: str) -> str:
        """Classify the type of Step 6 file."""
        if 'training' in file_path:
            return 'training_data'
        elif 'model' in file_path:
            return 'model_data'
        else:
            return 'unknown'
    
    def _analyze_model_patterns(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Analyze model training patterns."""
        import pandas as pd
        
        try:
            df = pd.read_csv(file_path, low_memory=False)
            
            if file_type == 'training_data':
                return self._analyze_training_data(df)
            elif file_type == 'model_data':
                return self._analyze_model_data(df)
            else:
                return {'error': f'Unknown file type: {file_type}'}
                
        except Exception as e:
            logger.error(f"Error analyzing model patterns for {file_path}: {e}")
            return {'error': str(e)}
    
    def _analyze_training_data(self, df) -> Dict[str, Any]:
        """Analyze training data."""
        return {
            'data_quality': self.calculate_data_quality_metrics(df),
            'training_validation': self._validate_training_rules(df),
            'training_analysis': self._analyze_training_characteristics(df)
        }
    
    def _analyze_model_data(self, df) -> Dict[str, Any]:
        """Analyze model data."""
        return {
            'data_quality': self.calculate_data_quality_metrics(df),
            'model_validation': self._validate_model_rules(df),
            'model_analysis': self._analyze_model_characteristics(df)
        }
    
    def _validate_training_rules(self, df) -> Dict[str, Any]:
        """Validate training data business rules."""
        validation_results = {
            'passed_rules': [],
            'failed_rules': [],
            'warnings': []
        }
        
        # Check for target variable
        target_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['target', 'label', 'y', 'outcome'])]
        
        if target_cols:
            validation_results['passed_rules'].append(f"Found target variables: {target_cols}")
        else:
            validation_results['warnings'].append("No obvious target variables found")
        
        # Check data balance
        if target_cols:
            target_col = target_cols[0]
            if df[target_col].dtype in ['int64', 'float64']:
                value_counts = df[target_col].value_counts()
                if len(value_counts) > 1:
                    balance_ratio = value_counts.min() / value_counts.max()
                    if balance_ratio < 0.1:
                        validation_results['warnings'].append(f"Imbalanced target variable (ratio: {balance_ratio:.3f})")
                    else:
                        validation_results['passed_rules'].append(f"Balanced target variable (ratio: {balance_ratio:.3f})")
        
        return validation_results
    
    def _validate_model_rules(self, df) -> Dict[str, Any]:
        """Validate model data business rules."""
        validation_results = {
            'passed_rules': [],
            'failed_rules': [],
            'warnings': []
        }
        
        # Check for model performance metrics
        metric_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['accuracy', 'precision', 'recall', 'f1', 'score', 'metric'])]
        
        if metric_cols:
            validation_results['passed_rules'].append(f"Found performance metrics: {metric_cols}")
        else:
            validation_results['warnings'].append("No obvious performance metrics found")
        
        return validation_results
    
    def _analyze_training_characteristics(self, df) -> Dict[str, Any]:
        """Analyze training data characteristics."""
        return {
            'sample_size': len(df),
            'feature_count': len(df.columns),
            'data_distribution': self._analyze_data_distribution(df)
        }
    
    def _analyze_model_characteristics(self, df) -> Dict[str, Any]:
        """Analyze model characteristics."""
        return {
            'model_count': len(df),
            'metric_count': len([col for col in df.columns if 'metric' in col.lower() or 'score' in col.lower()]),
            'performance_summary': self._analyze_performance_metrics(df)
        }
    
    def _analyze_data_distribution(self, df) -> Dict[str, Any]:
        """Analyze data distribution."""
        numeric_cols = df.select_dtypes(include=['number']).columns
        distribution_info = {}
        
        for col in numeric_cols[:5]:  # Limit to first 5 numeric columns
            distribution_info[col] = {
                'mean': df[col].mean(),
                'std': df[col].std(),
                'skewness': df[col].skew()
            }
        
        return distribution_info
    
    def _analyze_performance_metrics(self, df) -> Dict[str, Any]:
        """Analyze performance metrics."""
        metric_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['accuracy', 'precision', 'recall', 'f1', 'score'])]
        
        if not metric_cols:
            return {'error': 'No performance metrics found'}
        
        performance_summary = {}
        for col in metric_cols:
            if df[col].dtype in ['int64', 'float64']:
                performance_summary[col] = {
                    'mean': df[col].mean(),
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'std': df[col].std()
                }
        
        return performance_summary
    
    def generate_step_constraints(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Generate validation constraints specific to Step 6."""
        return {
            'training_data': {
                'dtype': 'float64',
                'nullable': True
            },
            'model_data': {
                'dtype': 'float64',
                'nullable': True
            }
        }
    
    def _add_step_specific_analysis(self, insights: Dict[str, Any]) -> str:
        """Add Step 6 specific analysis to the report."""
        report = "\n## Step 6 Specific Analysis\n\n"
        report += "### Model Training Quality\n\n"
        
        for file_path, file_insights in insights.get('insights', {}).items():
            if 'error' in file_insights:
                continue
            
            file_type = file_insights.get('file_type', 'unknown')
            report += f"#### {file_type.upper()} Analysis\n\n"
            
            if 'step_specific_analysis' in file_insights:
                analysis = file_insights['step_specific_analysis']
                
                if file_type == 'training_data' and 'training_analysis' in analysis:
                    training_analysis = analysis['training_analysis']
                    report += f"**Training Characteristics:**\n"
                    report += f"- Sample size: {training_analysis.get('sample_size', 'N/A')}\n"
                    report += f"- Feature count: {training_analysis.get('feature_count', 'N/A')}\n\n"
                
                elif file_type == 'model_data' and 'model_analysis' in analysis:
                    model_analysis = analysis['model_analysis']
                    report += f"**Model Characteristics:**\n"
                    report += f"- Model count: {model_analysis.get('model_count', 'N/A')}\n"
                    report += f"- Metric count: {model_analysis.get('metric_count', 'N/A')}\n\n"
        
        return report
