#!/usr/bin/env python3
"""
Step 5 EDA Analyzer

This module provides EDA analysis specifically for Step 5 (feature engineering),
focusing on engineered features and data transformations.

Author: Data Pipeline
Date: 2025-01-03
"""

import os
import logging
from typing import Dict, List, Any
from .base_analyzer import BaseEDAAnalyzer

logger = logging.getLogger(__name__)

class Step5EDAAnalyzer(BaseEDAAnalyzer):
    """EDA analyzer for Step 5 (feature engineering)."""
    
    def __init__(self, output_dir: str = "output/eda_reports"):
        super().__init__("step5", output_dir)
    
    def get_target_files(self, period: str) -> List[str]:
        """Get target files for Step 5 analysis."""
        target_files = []
        
        # Look for feature engineering files
        feature_files = [
            f"data/features/engineered_features_{period}.csv",
            f"output/features/engineered_features_{period}.csv",
            f"data/feature_engineering_{period}.csv",
            f"output/feature_engineering_{period}.csv"
        ]
        
        for file_path in feature_files:
            if os.path.exists(file_path):
                target_files.append(file_path)
        
        return target_files
    
    def analyze_file_patterns(self, file_path: str, period: str) -> Dict[str, Any]:
        """Analyze patterns specific to Step 5 data."""
        insights = self.get_common_data_insights(file_path)
        if not insights:
            return {}
        
        insights.update({
            'file_type': 'engineered_features',
            'period': period,
            'step_specific_analysis': self._analyze_feature_patterns(file_path)
        })
        
        return insights
    
    def _analyze_feature_patterns(self, file_path: str) -> Dict[str, Any]:
        """Analyze feature engineering patterns."""
        import pandas as pd
        
        try:
            df = pd.read_csv(file_path, low_memory=False)
            
            return {
                'data_quality': self.calculate_data_quality_metrics(df),
                'feature_validation': self._validate_feature_rules(df),
                'feature_analysis': self._analyze_features(df)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing feature patterns for {file_path}: {e}")
            return {'error': str(e)}
    
    def _validate_feature_rules(self, df) -> Dict[str, Any]:
        """Validate feature engineering business rules."""
        validation_results = {
            'passed_rules': [],
            'failed_rules': [],
            'warnings': []
        }
        
        # Check for engineered features
        engineered_cols = [col for col in df.columns if any(keyword in col.lower() for keyword in ['_feat', '_engineered', '_derived', '_calculated'])]
        
        if engineered_cols:
            validation_results['passed_rules'].append(f"Found {len(engineered_cols)} engineered features")
        else:
            validation_results['warnings'].append("No obvious engineered features found")
        
        # Check for feature consistency
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            validation_results['passed_rules'].append(f"Found {len(numeric_cols)} numeric features")
        
        return validation_results
    
    def _analyze_features(self, df) -> Dict[str, Any]:
        """Analyze feature characteristics."""
        return {
            'total_features': len(df.columns),
            'numeric_features': len(df.select_dtypes(include=['number']).columns),
            'categorical_features': len(df.select_dtypes(include=['object']).columns),
            'feature_correlation': self._analyze_feature_correlation(df)
        }
    
    def _analyze_feature_correlation(self, df) -> Dict[str, Any]:
        """Analyze feature correlations."""
        import pandas as pd
        
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) < 2:
            return {'error': 'Not enough numeric features for correlation analysis'}
        
        corr_matrix = df[numeric_cols].corr()
        
        # Find high correlations
        high_corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.7:
                    high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_val))
        
        return {
            'high_correlations': high_corr_pairs,
            'avg_correlation': corr_matrix.abs().mean().mean()
        }
    
    def generate_step_constraints(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Generate validation constraints specific to Step 5."""
        return {
            'engineered_features': {
                'dtype': 'float64',
                'nullable': True
            }
        }
    
    def _add_step_specific_analysis(self, insights: Dict[str, Any]) -> str:
        """Add Step 5 specific analysis to the report."""
        report = "\n## Step 5 Specific Analysis\n\n"
        report += "### Feature Engineering Quality\n\n"
        
        for file_path, file_insights in insights.get('insights', {}).items():
            if 'error' in file_insights:
                continue
            
            if 'step_specific_analysis' in file_insights:
                analysis = file_insights['step_specific_analysis']
                
                if 'feature_analysis' in analysis:
                    feature_analysis = analysis['feature_analysis']
                    report += f"**Feature Summary:**\n"
                    report += f"- Total features: {feature_analysis.get('total_features', 'N/A')}\n"
                    report += f"- Numeric features: {feature_analysis.get('numeric_features', 'N/A')}\n"
                    report += f"- Categorical features: {feature_analysis.get('categorical_features', 'N/A')}\n\n"
        
        return report
