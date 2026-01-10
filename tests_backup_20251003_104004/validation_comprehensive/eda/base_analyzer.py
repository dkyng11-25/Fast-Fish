#!/usr/bin/env python3
"""
Base EDA Analyzer

This module provides the base class for all step-specific EDA analyzers,
implementing common functionality and reducing code duplication.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandas as pd
import numpy as np
import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class BaseEDAAnalyzer(ABC):
    """
    Base class for step-specific EDA analyzers.
    
    Implements common functionality and provides a consistent interface
    for all step analyzers to reduce complexity and duplication.
    """
    
    def __init__(self, step_name: str, output_dir: str = "output/eda_reports"):
        self.step_name = step_name
        self.output_dir = Path(output_dir) / step_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.analysis_results = {}
        
    @abstractmethod
    def get_target_files(self, period: str) -> List[str]:
        """
        Get list of target files for this step and period.
        
        Args:
            period: Time period (e.g., '202508A')
            
        Returns:
            List of file paths to analyze
        """
        pass
    
    @abstractmethod
    def analyze_file_patterns(self, file_path: str, period: str) -> Dict[str, Any]:
        """
        Analyze patterns specific to this step's data.
        
        Args:
            file_path: Path to the data file
            period: Time period
            
        Returns:
            Dictionary containing step-specific insights
        """
        pass
    
    @abstractmethod
    def generate_step_constraints(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate validation constraints specific to this step.
        
        Args:
            insights: Analysis insights
            
        Returns:
            Dictionary of validation constraints
        """
        pass
    
    def analyze_period(self, period: str) -> Dict[str, Any]:
        """
        Analyze a specific time period for this step.
        
        Args:
            period: Time period to analyze
            
        Returns:
            Dictionary containing analysis results
        """
        logger.info(f"Analyzing {self.step_name} for period {period}")
        
        target_files = self.get_target_files(period)
        if not target_files:
            logger.warning(f"No target files found for {self.step_name} period {period}")
            return {}
        
        period_insights = {
            'step': self.step_name,
            'period': period,
            'timestamp': datetime.now().isoformat(),
            'files_analyzed': [],
            'insights': {},
            'constraints': {}
        }
        
        for file_path in target_files:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                continue
                
            try:
                file_insights = self.analyze_file_patterns(file_path, period)
                if file_insights:
                    period_insights['files_analyzed'].append(file_path)
                    period_insights['insights'][file_path] = file_insights
                    
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
                period_insights['insights'][file_path] = {'error': str(e)}
        
        # Generate step-specific constraints
        if period_insights['insights']:
            period_insights['constraints'] = self.generate_step_constraints(period_insights['insights'])
        
        # Generate reports
        self._generate_step_reports(period_insights)
        
        return period_insights
    
    def _generate_step_reports(self, insights: Dict[str, Any]) -> None:
        """
        Generate step-specific reports.
        
        Args:
            insights: Analysis insights
        """
        period = insights['period']
        report_dir = self.output_dir / period
        report_dir.mkdir(exist_ok=True)
        
        # Generate summary report
        summary_report = self._generate_summary_report(insights)
        summary_path = report_dir / f"{self.step_name}_summary_{period}.md"
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_report)
        
        logger.info(f"Generated {self.step_name} summary report: {summary_path}")
    
    def _generate_summary_report(self, insights: Dict[str, Any]) -> str:
        """
        Generate a summary report for this step.
        
        Args:
            insights: Analysis insights
            
        Returns:
            Markdown report content
        """
        period = insights['period']
        files_analyzed = insights['files_analyzed']
        
        report = f"""# {self.step_name.upper()} EDA Summary - {period}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Step:** {self.step_name}  
**Period:** {period}

## Files Analyzed

"""
        
        for file_path in files_analyzed:
            report += f"- `{file_path}`\n"
        
        if not files_analyzed:
            report += "No files were analyzed for this period.\n"
        
        # Add step-specific analysis
        report += self._add_step_specific_analysis(insights)
        
        return report
    
    def _add_step_specific_analysis(self, insights: Dict[str, Any]) -> str:
        """
        Add step-specific analysis to the report.
        Override in subclasses for step-specific content.
        
        Args:
            insights: Analysis insights
            
        Returns:
            Additional report content
        """
        return "\n## Analysis Results\n\nStep-specific analysis will be added by subclasses.\n"
    
    def get_common_data_insights(self, file_path: str) -> Dict[str, Any]:
        """
        Get common data insights (shape, dtypes, nulls, etc.).
        
        Args:
            file_path: Path to the data file
            
        Returns:
            Dictionary of common insights
        """
        if not os.path.exists(file_path):
            return {}
        
        try:
            df = pd.read_csv(file_path, low_memory=False)
            
            return {
                'shape': df.shape,
                'columns': list(df.columns),
                'dtypes': df.dtypes.to_dict(),
                'null_counts': df.isnull().sum().to_dict(),
                'unique_counts': df.nunique().to_dict(),
                'memory_usage': df.memory_usage(deep=True).sum(),
                'file_size': os.path.getsize(file_path)
            }
            
        except Exception as e:
            logger.error(f"Error getting common insights for {file_path}: {e}")
            return {}
    
    def identify_column_types(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Identify different types of columns in the dataframe.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary mapping column types to column names
        """
        column_types = {
            'numeric': [],
            'categorical': [],
            'id_columns': [],
            'date_columns': [],
            'text_columns': []
        }
        
        for col in df.columns:
            # ID columns
            if any(keyword in col.lower() for keyword in ['id', 'code', 'key', 'str_code', 'spu_code']):
                column_types['id_columns'].append(col)
            
            # Date columns
            elif any(keyword in col.lower() for keyword in ['date', 'time', 'yyyy', 'mm', 'period']):
                column_types['date_columns'].append(col)
            
            # Numeric columns
            elif df[col].dtype in ['int64', 'int32', 'float64', 'float32']:
                column_types['numeric'].append(col)
            
            # Categorical columns (object with limited unique values)
            elif df[col].dtype == 'object':
                unique_count = df[col].nunique()
                if unique_count < len(df) * 0.5:  # Less than 50% unique
                    column_types['categorical'].append(col)
                else:
                    column_types['text_columns'].append(col)
        
        return column_types
    
    def calculate_data_quality_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate common data quality metrics.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary of quality metrics
        """
        total_cells = len(df) * len(df.columns)
        null_cells = df.isnull().sum().sum()
        duplicate_rows = df.duplicated().sum()
        
        return {
            'completeness': ((total_cells - null_cells) / total_cells) * 100,
            'uniqueness': ((len(df) - duplicate_rows) / len(df)) * 100,
            'null_percentage': (null_cells / total_cells) * 100,
            'duplicate_percentage': (duplicate_rows / len(df)) * 100
        }
    
    def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """
        Save analysis results to JSON file.
        
        Args:
            results: Results to save
            filename: Optional filename (defaults to step_period.json)
            
        Returns:
            Path to saved file
        """
        if filename is None:
            period = results.get('period', 'unknown')
            filename = f"{self.step_name}_{period}.json"
        
        results_path = self.output_dir / filename
        
        import json
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Saved {self.step_name} results to {results_path}")
        return str(results_path)
