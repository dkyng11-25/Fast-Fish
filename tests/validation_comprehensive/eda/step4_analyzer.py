#!/usr/bin/env python3
"""
Step 4 EDA Analyzer

This module provides EDA analysis specifically for Step 4 (weather data integration),
focusing on weather data patterns and store altitude data.

Author: Data Pipeline
Date: 2025-01-03
"""

import os
import logging
from typing import Dict, List, Any
from .base_analyzer import BaseEDAAnalyzer

logger = logging.getLogger(__name__)

class Step4EDAAnalyzer(BaseEDAAnalyzer):
    """EDA analyzer for Step 4 (weather data integration)."""
    
    def __init__(self, output_dir: str = "output/eda_reports"):
        super().__init__("step4", output_dir)
    
    def get_target_files(self, period: str) -> List[str]:
        """Get target files for Step 4 analysis."""
        target_files = []
        
        # Look for weather and altitude files
        weather_files = [
            f"data/weather_data/weather_{period}.csv",
            f"output/weather_data/weather_{period}.csv",
            f"output/store_altitudes.csv",
            f"data/store_altitudes.csv"
        ]
        
        for file_path in weather_files:
            if os.path.exists(file_path):
                target_files.append(file_path)
        
        return target_files
    
    def analyze_file_patterns(self, file_path: str, period: str) -> Dict[str, Any]:
        """Analyze patterns specific to Step 4 data."""
        insights = self.get_common_data_insights(file_path)
        if not insights:
            return {}
        
        file_type = self._classify_file_type(file_path)
        insights.update({
            'file_type': file_type,
            'period': period,
            'step_specific_analysis': self._analyze_weather_patterns(file_path, file_type)
        })
        
        return insights
    
    def _classify_file_type(self, file_path: str) -> str:
        """Classify the type of Step 4 file."""
        if 'weather' in file_path:
            return 'weather_data'
        elif 'altitude' in file_path:
            return 'altitude_data'
        else:
            return 'unknown'
    
    def _analyze_weather_patterns(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Analyze weather specific patterns."""
        import pandas as pd
        
        try:
            df = pd.read_csv(file_path, low_memory=False)
            
            if file_type == 'weather_data':
                return self._analyze_weather_data(df)
            elif file_type == 'altitude_data':
                return self._analyze_altitude_data(df)
            else:
                return {'error': f'Unknown file type: {file_type}'}
                
        except Exception as e:
            logger.error(f"Error analyzing weather patterns for {file_path}: {e}")
            return {'error': str(e)}
    
    def _analyze_weather_data(self, df) -> Dict[str, Any]:
        """Analyze weather data."""
        return {
            'data_quality': self.calculate_data_quality_metrics(df),
            'weather_validation': self._validate_weather_rules(df),
            'weather_analysis': self._analyze_weather_metrics(df)
        }
    
    def _analyze_altitude_data(self, df) -> Dict[str, Any]:
        """Analyze altitude data."""
        return {
            'data_quality': self.calculate_data_quality_metrics(df),
            'altitude_validation': self._validate_altitude_rules(df),
            'altitude_analysis': self._analyze_altitude_metrics(df)
        }
    
    def _validate_weather_rules(self, df) -> Dict[str, Any]:
        """Validate weather data business rules."""
        validation_results = {
            'passed_rules': [],
            'failed_rules': [],
            'warnings': []
        }
        
        # Check for required weather columns
        weather_cols = ['temperature', 'humidity', 'precipitation']
        present_cols = [col for col in weather_cols if col in df.columns]
        
        if present_cols:
            validation_results['passed_rules'].append(f"Found weather columns: {present_cols}")
        else:
            validation_results['failed_rules'].append("No weather columns found")
        
        return validation_results
    
    def _validate_altitude_rules(self, df) -> Dict[str, Any]:
        """Validate altitude data business rules."""
        validation_results = {
            'passed_rules': [],
            'failed_rules': [],
            'warnings': []
        }
        
        # Check for altitude column
        altitude_cols = [col for col in df.columns if 'altitude' in col.lower()]
        if altitude_cols:
            validation_results['passed_rules'].append(f"Found altitude columns: {altitude_cols}")
        else:
            validation_results['failed_rules'].append("No altitude columns found")
        
        return validation_results
    
    def _analyze_weather_metrics(self, df) -> Dict[str, Any]:
        """Analyze weather metrics."""
        analysis = {}
        
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            analysis[col] = {
                'min': df[col].min(),
                'max': df[col].max(),
                'mean': df[col].mean(),
                'std': df[col].std()
            }
        
        return analysis
    
    def _analyze_altitude_metrics(self, df) -> Dict[str, Any]:
        """Analyze altitude metrics."""
        analysis = {}
        
        altitude_cols = [col for col in df.columns if 'altitude' in col.lower()]
        for col in altitude_cols:
            if df[col].dtype in ['int64', 'float64']:
                analysis[col] = {
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'mean': df[col].mean(),
                    'std': df[col].std()
                }
        
        return analysis
    
    def generate_step_constraints(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Generate validation constraints specific to Step 4."""
        return {
            'weather_data': {
                'dtype': 'float64',
                'nullable': True
            },
            'altitude_data': {
                'dtype': 'float64',
                'nullable': True,
                'ge': 0
            }
        }
    
    def _add_step_specific_analysis(self, insights: Dict[str, Any]) -> str:
        """Add Step 4 specific analysis to the report."""
        report = "\n## Step 4 Specific Analysis\n\n"
        report += "### Weather Data Integration Quality\n\n"
        
        for file_path, file_insights in insights.get('insights', {}).items():
            if 'error' in file_insights:
                continue
            
            file_type = file_insights.get('file_type', 'unknown')
            report += f"#### {file_type.upper()} Analysis\n\n"
            
            if 'step_specific_analysis' in file_insights:
                analysis = file_insights['step_specific_analysis']
                
                if 'weather_analysis' in analysis:
                    weather_analysis = analysis['weather_analysis']
                    report += f"**Weather Metrics:**\n"
                    for metric, values in weather_analysis.items():
                        report += f"- {metric}: min={values.get('min', 'N/A'):.2f}, max={values.get('max', 'N/A'):.2f}\n"
                    report += "\n"
        
        return report
