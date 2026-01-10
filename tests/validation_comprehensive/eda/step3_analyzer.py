#!/usr/bin/env python3
"""
Step 3 EDA Analyzer

This module provides EDA analysis specifically for Step 3 (clustering analysis),
focusing on clustering results and matrix data patterns.

Author: Data Pipeline
Date: 2025-01-03
"""

import os
import logging
from typing import Dict, List, Any
from .base_analyzer import BaseEDAAnalyzer

logger = logging.getLogger(__name__)

class Step3EDAAnalyzer(BaseEDAAnalyzer):
    """
    EDA analyzer for Step 3 (clustering analysis).
    
    Focuses on analyzing clustering results and matrix data patterns
    to understand clustering quality and data relationships.
    """
    
    def __init__(self, output_dir: str = "output/eda_reports"):
        super().__init__("step3", output_dir)
    
    def get_target_files(self, period: str) -> List[str]:
        """Get target files for Step 3 analysis."""
        target_files = []
        
        # Look for clustering and matrix files
        clustering_files = [
            f"data/clustering_results_{period}.csv",
            f"output/clustering_results_{period}.csv",
            f"data/matrix_data_{period}.csv",
            f"output/matrix_data_{period}.csv"
        ]
        
        for file_path in clustering_files:
            if os.path.exists(file_path):
                target_files.append(file_path)
        
        return target_files
    
    def analyze_file_patterns(self, file_path: str, period: str) -> Dict[str, Any]:
        """Analyze patterns specific to Step 3 data."""
        insights = self.get_common_data_insights(file_path)
        if not insights:
            return {}
        
        file_type = self._classify_file_type(file_path)
        insights.update({
            'file_type': file_type,
            'period': period,
            'step_specific_analysis': self._analyze_clustering_patterns(file_path, file_type)
        })
        
        return insights
    
    def _classify_file_type(self, file_path: str) -> str:
        """Classify the type of Step 3 file."""
        if 'clustering' in file_path:
            return 'clustering_results'
        elif 'matrix' in file_path:
            return 'matrix_data'
        else:
            return 'unknown'
    
    def _analyze_clustering_patterns(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Analyze clustering specific patterns."""
        import pandas as pd
        
        try:
            df = pd.read_csv(file_path, low_memory=False)
            
            if file_type == 'clustering_results':
                return self._analyze_clustering_results(df)
            elif file_type == 'matrix_data':
                return self._analyze_matrix_data(df)
            else:
                return {'error': f'Unknown file type: {file_type}'}
                
        except Exception as e:
            logger.error(f"Error analyzing clustering patterns for {file_path}: {e}")
            return {'error': str(e)}
    
    def _analyze_clustering_results(self, df) -> Dict[str, Any]:
        """Analyze clustering results data."""
        analysis = {
            'data_quality': self.calculate_data_quality_metrics(df),
            'clustering_validation': self._validate_clustering_rules(df),
            'cluster_analysis': self._analyze_clusters(df)
        }
        
        return analysis
    
    def _analyze_matrix_data(self, df) -> Dict[str, Any]:
        """Analyze matrix data."""
        analysis = {
            'data_quality': self.calculate_data_quality_metrics(df),
            'matrix_validation': self._validate_matrix_rules(df),
            'matrix_analysis': self._analyze_matrix_structure(df)
        }
        
        return analysis
    
    def _validate_clustering_rules(self, df) -> Dict[str, Any]:
        """Validate clustering business rules."""
        validation_results = {
            'passed_rules': [],
            'failed_rules': [],
            'warnings': []
        }
        
        # Check for cluster column
        cluster_cols = [col for col in df.columns if 'cluster' in col.lower()]
        if not cluster_cols:
            validation_results['failed_rules'].append("No cluster column found")
        else:
            validation_results['passed_rules'].append(f"Found cluster columns: {cluster_cols}")
        
        # Check cluster distribution
        if cluster_cols:
            cluster_col = cluster_cols[0]
            cluster_counts = df[cluster_col].value_counts()
            if len(cluster_counts) < 2:
                validation_results['warnings'].append("Only one cluster found")
            else:
                validation_results['passed_rules'].append(f"Found {len(cluster_counts)} clusters")
        
        return validation_results
    
    def _validate_matrix_rules(self, df) -> Dict[str, Any]:
        """Validate matrix data business rules."""
        validation_results = {
            'passed_rules': [],
            'failed_rules': [],
            'warnings': []
        }
        
        # Check if matrix is square-ish
        if df.shape[0] != df.shape[1]:
            validation_results['warnings'].append("Matrix is not square")
        else:
            validation_results['passed_rules'].append("Matrix is square")
        
        # Check for numeric data
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) != len(df.columns):
            validation_results['warnings'].append("Non-numeric columns found in matrix")
        else:
            validation_results['passed_rules'].append("All matrix columns are numeric")
        
        return validation_results
    
    def _analyze_clusters(self, df) -> Dict[str, Any]:
        """Analyze cluster characteristics."""
        cluster_cols = [col for col in df.columns if 'cluster' in col.lower()]
        if not cluster_cols:
            return {'error': 'No cluster columns found'}
        
        cluster_col = cluster_cols[0]
        cluster_counts = df[cluster_col].value_counts()
        
        return {
            'num_clusters': len(cluster_counts),
            'cluster_sizes': cluster_counts.to_dict(),
            'largest_cluster': cluster_counts.index[0],
            'smallest_cluster': cluster_counts.index[-1],
            'cluster_balance': cluster_counts.std() / cluster_counts.mean()
        }
    
    def _analyze_matrix_structure(self, df) -> Dict[str, Any]:
        """Analyze matrix structure."""
        return {
            'dimensions': df.shape,
            'is_square': df.shape[0] == df.shape[1],
            'numeric_columns': len(df.select_dtypes(include=['number']).columns),
            'sparsity': (df == 0).sum().sum() / (df.shape[0] * df.shape[1])
        }
    
    def generate_step_constraints(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Generate validation constraints specific to Step 3."""
        constraints = {}
        
        for file_path, file_insights in insights.items():
            if 'error' in file_insights:
                continue
            
            file_type = file_insights.get('file_type', 'unknown')
            if file_type == 'clustering_results':
                constraints.update(self._generate_clustering_constraints())
            elif file_type == 'matrix_data':
                constraints.update(self._generate_matrix_constraints())
        
        return constraints
    
    def _generate_clustering_constraints(self) -> Dict[str, Any]:
        """Generate constraints for clustering results."""
        return {
            'cluster_id': {
                'dtype': 'int64',
                'nullable': False,
                'ge': 0
            }
        }
    
    def _generate_matrix_constraints(self) -> Dict[str, Any]:
        """Generate constraints for matrix data."""
        return {
            'matrix_values': {
                'dtype': 'float64',
                'nullable': True
            }
        }
    
    def _add_step_specific_analysis(self, insights: Dict[str, Any]) -> str:
        """Add Step 3 specific analysis to the report."""
        report = "\n## Step 3 Specific Analysis\n\n"
        report += "### Clustering Analysis Quality\n\n"
        
        for file_path, file_insights in insights.get('insights', {}).items():
            if 'error' in file_insights:
                continue
            
            file_type = file_insights.get('file_type', 'unknown')
            report += f"#### {file_type.upper()} Analysis\n\n"
            
            if 'step_specific_analysis' in file_insights:
                analysis = file_insights['step_specific_analysis']
                
                if file_type == 'clustering_results' and 'cluster_analysis' in analysis:
                    cluster_analysis = analysis['cluster_analysis']
                    report += f"**Cluster Distribution:**\n"
                    report += f"- Number of clusters: {cluster_analysis.get('num_clusters', 'N/A')}\n"
                    report += f"- Cluster balance: {cluster_analysis.get('cluster_balance', 'N/A'):.4f}\n\n"
                
                elif file_type == 'matrix_data' and 'matrix_analysis' in analysis:
                    matrix_analysis = analysis['matrix_analysis']
                    report += f"**Matrix Structure:**\n"
                    report += f"- Dimensions: {matrix_analysis.get('dimensions', 'N/A')}\n"
                    report += f"- Is square: {matrix_analysis.get('is_square', 'N/A')}\n"
                    report += f"- Sparsity: {matrix_analysis.get('sparsity', 'N/A'):.4f}\n\n"
        
        return report
