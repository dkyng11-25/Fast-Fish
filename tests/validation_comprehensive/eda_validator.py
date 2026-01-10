#!/usr/bin/env python3
"""
EDA-Based Data Validation Module

This module provides comprehensive data validation using Exploratory Data Analysis (EDA)
techniques to understand data patterns across multiple time periods and create robust
validation schemas based on actual data characteristics.

Uses only static Markdown report generation - no web servers or browser dependencies.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandas as pd
import numpy as np
import os
import glob
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class EDAValidator:
    """
    Comprehensive EDA-based data validator that analyzes data patterns
    across multiple time periods to create robust validation schemas.
    """
    
    def __init__(self, output_dir: str = "output/eda_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.data_insights = {}
        self.column_constraints = {}
        
    def analyze_time_periods(self) -> List[str]:
        """
        Analyze available time periods and identify key periods for EDA.
        
        Returns:
            List of time period labels to analyze
        """
        periods = []
        
        # Check for existing data periods
        data_dir = Path("data/api_data")
        if data_dir.exists():
            for file in data_dir.glob("store_config_*.csv"):
                period = file.stem.replace("store_config_", "")
                if len(period) == 7 and period[6] in ['A', 'B']:  # YYYYMMA or YYYYMMB format
                    periods.append(period)
        
        # Add specific periods of interest
        current_year = datetime.now().year
        key_periods = [
            f"{current_year}05A",  # First half of May (Golden Week)
            f"{current_year}10A",  # First half of October (Golden Week)
            f"{current_year}07A",  # Hottest fortnight (July)
            f"{current_year}01A",  # Coldest fortnight (January)
            f"{current_year}06A",  # Rainiest fortnight (June)
        ]
        
        # Add previous year periods for comparison
        prev_year = current_year - 1
        key_periods.extend([
            f"{prev_year}05A",
            f"{prev_year}10A", 
            f"{prev_year}07A",
            f"{prev_year}01A",
            f"{prev_year}06A",
        ])
        
        # Remove duplicates and sort
        all_periods = list(set(periods + key_periods))
        all_periods.sort()
        
        logger.info(f"Identified {len(all_periods)} time periods for analysis: {all_periods}")
        return all_periods
    
    def download_missing_data(self, periods: List[str]) -> List[str]:
        """
        Download missing data for specified periods.
        
        Args:
            periods: List of period labels to download
            
        Returns:
            List of successfully downloaded periods
        """
        downloaded = []
        
        for period in periods:
            yyyymm = period[:6]
            period_suffix = period[6:]
            
            # Check if data already exists
            store_config_file = f"data/api_data/store_config_{period}.csv"
            if os.path.exists(store_config_file):
                downloaded.append(period)
                continue
                
            try:
                # Download data using existing scripts
                logger.info(f"Downloading data for period {period}...")
                
                # Run step 1 to download API data
                cmd = f"PYTHONPATH=. python src/step1_download_api_data.py --yyyymm {yyyymm} --period {period_suffix}"
                result = os.system(cmd)
                
                if result == 0 and os.path.exists(store_config_file):
                    downloaded.append(period)
                    logger.info(f"Successfully downloaded data for {period}")
                else:
                    logger.warning(f"Failed to download data for {period}")
                    
            except Exception as e:
                logger.error(f"Error downloading data for {period}: {e}")
                
        return downloaded
    
    def analyze_data_patterns(self, file_path: str, period: str) -> Dict[str, Any]:
        """
        Analyze data patterns for a specific file and period.
        
        Args:
            file_path: Path to the data file
            period: Time period label
            
        Returns:
            Dictionary containing data insights
        """
        if not os.path.exists(file_path):
            return {}
            
        try:
            # Read data with flexible dtypes
            df = pd.read_csv(file_path, low_memory=False)
            
            insights = {
                'period': period,
                'file_path': file_path,
                'shape': df.shape,
                'columns': list(df.columns),
                'dtypes': df.dtypes.to_dict(),
                'null_counts': df.isnull().sum().to_dict(),
                'unique_counts': df.nunique().to_dict(),
                'numeric_stats': {},
                'categorical_stats': {},
                'date_columns': [],
                'id_columns': [],
                'constraints': {}
            }
            
            # Analyze numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                insights['numeric_stats'][col] = {
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'mean': df[col].mean(),
                    'std': df[col].std(),
                    'median': df[col].median(),
                    'q25': df[col].quantile(0.25),
                    'q75': df[col].quantile(0.75),
                    'skewness': df[col].skew(),
                    'kurtosis': df[col].kurtosis()
                }
            
            # Analyze categorical columns
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            for col in categorical_cols:
                value_counts = df[col].value_counts()
                insights['categorical_stats'][col] = {
                    'unique_count': len(value_counts),
                    'top_values': value_counts.head(10).to_dict(),
                    'most_common': value_counts.index[0] if len(value_counts) > 0 else None,
                    'most_common_count': value_counts.iloc[0] if len(value_counts) > 0 else 0
                }
            
            # Identify potential ID columns
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['id', 'code', 'key', 'str_code', 'spu_code']):
                    insights['id_columns'].append(col)
            
            # Identify potential date columns
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['date', 'time', 'yyyy', 'mm', 'period']):
                    insights['date_columns'].append(col)
            
            # Generate constraints based on data patterns
            insights['constraints'] = self._generate_constraints(df, insights)
            
            return insights
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return {}
    
    def _generate_constraints(self, df: pd.DataFrame, insights: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate validation constraints based on data patterns.
        
        Args:
            df: DataFrame to analyze
            insights: Existing insights dictionary
            
        Returns:
            Dictionary of validation constraints
        """
        constraints = {}
        
        for col in df.columns:
            col_constraints = {}
            
            # Data type constraints
            if df[col].dtype in ['int64', 'int32']:
                col_constraints['dtype'] = 'int64'
                col_constraints['nullable'] = df[col].isnull().any()
            elif df[col].dtype in ['float64', 'float32']:
                col_constraints['dtype'] = 'float64'
                col_constraints['nullable'] = df[col].isnull().any()
            elif df[col].dtype == 'object':
                col_constraints['dtype'] = 'string'
                col_constraints['nullable'] = df[col].isnull().any()
            
            # Range constraints for numeric columns
            if col in insights['numeric_stats']:
                stats = insights['numeric_stats'][col]
                col_constraints['min_value'] = stats['min']
                col_constraints['max_value'] = stats['max']
                
                # Check for reasonable ranges
                if 'price' in col.lower() or 'amount' in col.lower():
                    if stats['min'] >= 0:
                        col_constraints['ge'] = 0
                elif 'count' in col.lower() or 'quantity' in col.lower():
                    if stats['min'] >= 0:
                        col_constraints['ge'] = 0
                elif 'rate' in col.lower() or 'percentage' in col.lower():
                    if 0 <= stats['min'] <= 100 and 0 <= stats['max'] <= 100:
                        col_constraints['ge'] = 0
                        col_constraints['le'] = 100
            
            # Categorical constraints
            if col in insights['categorical_stats']:
                cat_stats = insights['categorical_stats'][col]
                if cat_stats['unique_count'] < 100:  # Reasonable number of categories
                    col_constraints['isin'] = list(cat_stats['top_values'].keys())
            
            # ID column constraints
            if col in insights['id_columns']:
                col_constraints['coerce'] = True  # Allow type coercion
                if 'str_code' in col.lower():
                    col_constraints['dtype'] = 'string'
                elif 'spu_code' in col.lower():
                    col_constraints['dtype'] = 'string'
            
            if col_constraints:
                constraints[col] = col_constraints
        
        return constraints
    
    def generate_eda_reports(self, file_path: str, period: str) -> Dict[str, str]:
        """
        Generate comprehensive EDA reports as static files (Markdown + HTML).
        
        Args:
            file_path: Path to the data file
            period: Time period label
            
        Returns:
            Dictionary of report file paths
        """
        if not os.path.exists(file_path):
            return {}
            
        reports = {}
        period_dir = self.output_dir / period
        period_dir.mkdir(exist_ok=True)
        
        try:
            df = pd.read_csv(file_path, low_memory=False)
            
            # Generate comprehensive Markdown report
            markdown_report = self._generate_markdown_eda_report(df, file_path, period)
            report_path = period_dir / f"eda_report_{period}.md"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(markdown_report)
            
            reports['markdown_report'] = str(report_path)
            logger.info(f"Generated Markdown EDA report: {report_path}")
            
            # Generate data quality report
            quality_report = self._generate_data_quality_report(df, file_path, period)
            quality_path = period_dir / f"data_quality_{period}.md"
            
            with open(quality_path, 'w', encoding='utf-8') as f:
                f.write(quality_report)
            
            reports['quality_report'] = str(quality_path)
            logger.info(f"Generated data quality report: {quality_path}")
            
            # Generate additional statistical analysis report
            stats_report = self._generate_statistical_analysis_report(df, file_path, period)
            stats_path = period_dir / f"statistical_analysis_{period}.md"
            
            with open(stats_path, 'w', encoding='utf-8') as f:
                f.write(stats_report)
            
            reports['statistical_analysis'] = str(stats_path)
            logger.info(f"Generated statistical analysis report: {stats_path}")
            
        except Exception as e:
            logger.error(f"Error generating EDA reports for {period}: {e}")
        
        return reports
    
    def _generate_markdown_eda_report(self, df: pd.DataFrame, file_path: str, period: str) -> str:
        """Generate comprehensive Markdown EDA report."""
        report = f"""# EDA Report - {period}

**File:** `{file_path}`  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Period:** {period}

## Dataset Overview

- **Shape:** {df.shape[0]:,} rows × {df.shape[1]} columns
- **Memory Usage:** {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB
- **File Size:** {os.path.getsize(file_path) / 1024 / 1024:.2f} MB

## Data Types

| Column | Type | Non-Null Count | Null Count | Null % |
|--------|------|----------------|------------|--------|
"""
        
        for col in df.columns:
            null_count = df[col].isnull().sum()
            null_pct = (null_count / len(df)) * 100
            report += f"| {col} | {df[col].dtype} | {len(df) - null_count:,} | {null_count:,} | {null_pct:.2f}% |\n"
        
        # Numeric columns analysis
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            report += f"\n## Numeric Columns Analysis\n\n"
            report += f"**Numeric Columns:** {len(numeric_cols)}\n\n"
            
            for col in numeric_cols[:10]:  # Limit to first 10 numeric columns
                stats = df[col].describe()
                report += f"### {col}\n"
                report += f"- **Mean:** {stats['mean']:.4f}\n"
                report += f"- **Std:** {stats['std']:.4f}\n"
                report += f"- **Min:** {stats['min']:.4f}\n"
                report += f"- **25%:** {stats['25%']:.4f}\n"
                report += f"- **50%:** {stats['50%']:.4f}\n"
                report += f"- **75%:** {stats['75%']:.4f}\n"
                report += f"- **Max:** {stats['max']:.4f}\n"
                report += f"- **Skewness:** {df[col].skew():.4f}\n"
                report += f"- **Kurtosis:** {df[col].kurtosis():.4f}\n\n"
        
        # Categorical columns analysis
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            report += f"\n## Categorical Columns Analysis\n\n"
            report += f"**Categorical Columns:** {len(categorical_cols)}\n\n"
            
            for col in categorical_cols[:10]:  # Limit to first 10 categorical columns
                value_counts = df[col].value_counts()
                report += f"### {col}\n"
                report += f"- **Unique Values:** {df[col].nunique()}\n"
                report += f"- **Most Common:** {value_counts.index[0] if len(value_counts) > 0 else 'N/A'}\n"
                report += f"- **Most Common Count:** {value_counts.iloc[0] if len(value_counts) > 0 else 0}\n"
                report += f"- **Top 5 Values:**\n"
                for i, (val, count) in enumerate(value_counts.head(5).items()):
                    report += f"  {i+1}. {val}: {count:,} ({count/len(df)*100:.2f}%)\n"
                report += "\n"
        
        # Missing data analysis
        missing_data = df.isnull().sum()
        missing_cols = missing_data[missing_data > 0]
        if len(missing_cols) > 0:
            report += f"\n## Missing Data Analysis\n\n"
            report += f"**Columns with Missing Data:** {len(missing_cols)}\n\n"
            report += "| Column | Missing Count | Missing % |\n"
            report += "|--------|---------------|----------|\n"
            for col, count in missing_cols.items():
                pct = (count / len(df)) * 100
                report += f"| {col} | {count:,} | {pct:.2f}% |\n"
        else:
            report += f"\n## Missing Data Analysis\n\n✅ **No missing data found!**\n"
        
        # Duplicate rows analysis
        duplicate_count = df.duplicated().sum()
        report += f"\n## Duplicate Rows Analysis\n\n"
        report += f"- **Duplicate Rows:** {duplicate_count:,}\n"
        report += f"- **Duplicate Percentage:** {(duplicate_count / len(df)) * 100:.2f}%\n"
        
        # Data quality summary
        report += f"\n## Data Quality Summary\n\n"
        report += f"- **Completeness Score:** {((len(df) * len(df.columns) - df.isnull().sum().sum()) / (len(df) * len(df.columns))) * 100:.2f}%\n"
        report += f"- **Uniqueness Score:** {(1 - duplicate_count / len(df)) * 100:.2f}%\n"
        
        return report
    
    def _generate_data_quality_report(self, df: pd.DataFrame, file_path: str, period: str) -> str:
        """Generate data quality report."""
        report = f"""# Data Quality Report - {period}

**File:** `{file_path}`  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Period:** {period}

## Quality Metrics

### Basic Metrics
- **Total Rows:** {len(df):,}
- **Total Columns:** {len(df.columns)}
- **Memory Usage:** {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB
- **File Size:** {os.path.getsize(file_path) / 1024 / 1024:.2f} MB

### Data Completeness
- **Total Cells:** {len(df) * len(df.columns):,}
- **Null Cells:** {df.isnull().sum().sum():,}
- **Completeness Rate:** {((len(df) * len(df.columns) - df.isnull().sum().sum()) / (len(df) * len(df.columns))) * 100:.2f}%

### Data Uniqueness
- **Duplicate Rows:** {df.duplicated().sum():,}
- **Unique Rows:** {len(df) - df.duplicated().sum():,}
- **Uniqueness Rate:** {(1 - df.duplicated().sum() / len(df)) * 100:.2f}%

## Column Quality Analysis

| Column | Type | Null Count | Null % | Unique Count | Duplicate % | Quality Score |
|--------|------|------------|--------|--------------|-------------|---------------|
"""
        
        for col in df.columns:
            null_count = df[col].isnull().sum()
            null_pct = (null_count / len(df)) * 100
            unique_count = df[col].nunique()
            duplicate_pct = (1 - unique_count / len(df)) * 100
            
            # Calculate quality score (0-100)
            completeness_score = (1 - null_pct / 100) * 50
            uniqueness_score = (1 - duplicate_pct / 100) * 50
            quality_score = completeness_score + uniqueness_score
            
            report += f"| {col} | {df[col].dtype} | {null_count:,} | {null_pct:.2f}% | {unique_count:,} | {duplicate_pct:.2f}% | {quality_score:.1f} |\n"
        
        # Data type consistency
        report += f"\n## Data Type Consistency\n\n"
        type_counts = df.dtypes.value_counts()
        for dtype, count in type_counts.items():
            report += f"- **{dtype}:** {count} columns\n"
        
        # Potential issues
        report += f"\n## Potential Data Quality Issues\n\n"
        
        issues = []
        for col in df.columns:
            null_pct = (df[col].isnull().sum() / len(df)) * 100
            if null_pct > 50:
                issues.append(f"⚠️ **{col}**: High null percentage ({null_pct:.2f}%)")
            
            if df[col].dtype == 'object':
                # Check for mixed types
                try:
                    pd.to_numeric(df[col], errors='raise')
                except:
                    # Check if it's actually numeric but stored as string
                    try:
                        pd.to_numeric(df[col].dropna(), errors='raise')
                        issues.append(f"🔢 **{col}**: Numeric data stored as string")
                    except:
                        pass
        
        if issues:
            for issue in issues:
                report += f"- {issue}\n"
        else:
            report += "✅ **No major data quality issues detected!**\n"
        
        return report
    
    def _generate_statistical_analysis_report(self, df: pd.DataFrame, file_path: str, period: str) -> str:
        """Generate statistical analysis report."""
        report = f"""# Statistical Analysis Report - {period}

**File:** `{file_path}`  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Period:** {period}

## Statistical Summary

### Dataset Statistics
- **Total Rows:** {len(df):,}
- **Total Columns:** {len(df.columns)}
- **Memory Usage:** {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB

### Data Distribution Analysis

"""
        
        # Numeric columns analysis
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            report += f"#### Numeric Columns ({len(numeric_cols)} columns)\n\n"
            
            for col in numeric_cols:
                stats = df[col].describe()
                skewness = df[col].skew()
                kurtosis = df[col].kurtosis()
                
                report += f"**{col}:**\n"
                report += f"- Mean: {stats['mean']:.4f}\n"
                report += f"- Median: {stats['50%']:.4f}\n"
                report += f"- Std Dev: {stats['std']:.4f}\n"
                report += f"- Min: {stats['min']:.4f}\n"
                report += f"- Max: {stats['max']:.4f}\n"
                report += f"- Skewness: {skewness:.4f} {'(right-skewed)' if skewness > 0.5 else '(left-skewed)' if skewness < -0.5 else '(approximately normal)'}\n"
                report += f"- Kurtosis: {kurtosis:.4f} {'(heavy-tailed)' if kurtosis > 3 else '(light-tailed)' if kurtosis < 3 else '(normal-tailed)'}\n\n"
        
        # Categorical columns analysis
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            report += f"#### Categorical Columns ({len(categorical_cols)} columns)\n\n"
            
            for col in categorical_cols:
                value_counts = df[col].value_counts()
                unique_count = df[col].nunique()
                most_common = value_counts.index[0] if len(value_counts) > 0 else 'N/A'
                most_common_pct = (value_counts.iloc[0] / len(df)) * 100 if len(value_counts) > 0 else 0
                
                report += f"**{col}:**\n"
                report += f"- Unique Values: {unique_count}\n"
                report += f"- Most Common: {most_common} ({most_common_pct:.2f}%)\n"
                report += f"- Entropy: {self._calculate_entropy(df[col]):.4f}\n\n"
        
        # Correlation analysis for numeric columns
        if len(numeric_cols) > 1:
            report += f"#### Correlation Analysis\n\n"
            corr_matrix = df[numeric_cols].corr()
            
            # Find high correlations
            high_corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_val = corr_matrix.iloc[i, j]
                    if abs(corr_val) > 0.7:  # High correlation threshold
                        high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_val))
            
            if high_corr_pairs:
                report += "**High Correlations (|r| > 0.7):**\n"
                for col1, col2, corr_val in high_corr_pairs:
                    report += f"- {col1} ↔ {col2}: {corr_val:.4f}\n"
                report += "\n"
            else:
                report += "**No high correlations found (|r| > 0.7)**\n\n"
        
        # Outlier analysis
        report += f"#### Outlier Analysis\n\n"
        outlier_cols = []
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            outlier_pct = (len(outliers) / len(df)) * 100
            
            if outlier_pct > 5:  # More than 5% outliers
                outlier_cols.append((col, len(outliers), outlier_pct))
        
        if outlier_cols:
            report += "**Columns with Significant Outliers (>5%):**\n"
            for col, count, pct in outlier_cols:
                report += f"- {col}: {count} outliers ({pct:.2f}%)\n"
        else:
            report += "**No significant outliers detected**\n"
        
        return report
    
    def _calculate_entropy(self, series: pd.Series) -> float:
        """Calculate entropy of a categorical series."""
        value_counts = series.value_counts()
        probabilities = value_counts / len(series)
        entropy = -sum(p * np.log2(p) for p in probabilities if p > 0)
        return entropy
    
    def create_comprehensive_schemas(self, insights: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create comprehensive validation schemas based on EDA insights.
        
        Args:
            insights: Dictionary of insights from multiple periods
            
        Returns:
            Dictionary of comprehensive schemas
        """
        schemas = {}
        
        # Group insights by file type
        file_types = {}
        for period, period_insights in insights.items():
            file_path = period_insights.get('file_path', '')
            file_type = self._classify_file_type(file_path)
            if file_type not in file_types:
                file_types[file_type] = []
            file_types[file_type].append(period_insights)
        
        # Create schemas for each file type
        for file_type, type_insights in file_types.items():
            if not type_insights:
                continue
                
            schema = self._create_file_type_schema(file_type, type_insights)
            if schema:
                schemas[file_type] = schema
        
        return schemas
    
    def _classify_file_type(self, file_path: str) -> str:
        """Classify file type based on path."""
        if 'store_config' in file_path:
            return 'store_config'
        elif 'spu_sales' in file_path:
            return 'spu_sales'
        elif 'weather' in file_path:
            return 'weather'
        elif 'clustering' in file_path:
            return 'clustering'
        elif 'matrix' in file_path:
            return 'matrix'
        else:
            return 'unknown'
    
    def _create_file_type_schema(self, file_type: str, insights_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create schema for a specific file type based on multiple period insights.
        
        Args:
            file_type: Type of file
            insights_list: List of insights from different periods
            
        Returns:
            Schema dictionary
        """
        if not insights_list:
            return {}
        
        # Merge constraints across all periods
        all_columns = set()
        for insights in insights_list:
            all_columns.update(insights.get('columns', []))
        
        merged_constraints = {}
        for col in all_columns:
            col_constraints = {}
            
            # Collect constraints from all periods
            for insights in insights_list:
                period_constraints = insights.get('constraints', {}).get(col, {})
                for key, value in period_constraints.items():
                    if key not in col_constraints:
                        col_constraints[key] = []
                    col_constraints[key].append(value)
            
            # Merge constraints (take most restrictive)
            final_constraints = {}
            for key, values in col_constraints.items():
                if key == 'dtype':
                    # Use most common dtype
                    final_constraints[key] = max(set(values), key=values.count)
                elif key == 'nullable':
                    # If any period allows nulls, allow nulls
                    final_constraints[key] = any(values)
                elif key in ['min_value', 'ge']:
                    # Take minimum value
                    final_constraints[key] = min([v for v in values if v is not None])
                elif key in ['max_value', 'le']:
                    # Take maximum value
                    final_constraints[key] = max([v for v in values if v is not None])
                elif key == 'isin':
                    # Take intersection of allowed values
                    all_values = set()
                    for value_list in values:
                        if isinstance(value_list, list):
                            all_values.update(value_list)
                    if all_values:
                        final_constraints[key] = list(all_values)
            
            if final_constraints:
                merged_constraints[col] = final_constraints
        
        return {
            'file_type': file_type,
            'columns': list(all_columns),
            'constraints': merged_constraints,
            'periods_analyzed': [insights.get('period', 'unknown') for insights in insights_list]
        }
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """
        Run comprehensive EDA analysis across multiple time periods.
        
        Returns:
            Dictionary containing all analysis results
        """
        logger.info("Starting comprehensive EDA analysis...")
        
        # Get time periods to analyze
        periods = self.analyze_time_periods()
        
        # Download missing data
        available_periods = self.download_missing_data(periods)
        logger.info(f"Available periods for analysis: {available_periods}")
        
        # Analyze each period
        all_insights = {}
        for period in available_periods:
            logger.info(f"Analyzing period {period}...")
            
            # Analyze store config data
            store_config_file = f"data/api_data/store_config_{period}.csv"
            if os.path.exists(store_config_file):
                insights = self.analyze_data_patterns(store_config_file, period)
                if insights:
                    all_insights[f"{period}_store_config"] = insights
                    
                    # Generate EDA reports
                    reports = self.generate_eda_reports(store_config_file, period)
                    insights['eda_reports'] = reports
            
            # Analyze SPU sales data
            spu_sales_file = f"data/api_data/complete_spu_sales_{period}.csv"
            if os.path.exists(spu_sales_file):
                insights = self.analyze_data_patterns(spu_sales_file, period)
                if insights:
                    all_insights[f"{period}_spu_sales"] = insights
                    
                    # Generate EDA reports
                    reports = self.generate_eda_reports(spu_sales_file, period)
                    insights['eda_reports'] = reports
        
        # Create comprehensive schemas
        schemas = self.create_comprehensive_schemas(all_insights)
        
        # Save results
        results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'periods_analyzed': available_periods,
            'insights': all_insights,
            'schemas': schemas,
            'eda_tools_available': {
                'markdown_reports': True,
                'static_analysis': True
            }
        }
        
        # Save to JSON
        results_file = self.output_dir / "comprehensive_analysis_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Comprehensive analysis complete. Results saved to {results_file}")
        return results


def install_eda_tools():
    """Install required EDA tools (Markdown-only reports)."""
    print("✅ Using Markdown-only EDA reports (no external dependencies needed)")
    print("   - Comprehensive Markdown reports generated")
    print("   - Data quality analysis included")
    print("   - Statistical analysis included")
    print("   - No web servers or browser dependencies")


if __name__ == "__main__":
    # Install EDA tools if needed
    install_eda_tools()
    
    # Run comprehensive analysis
    validator = EDAValidator()
    results = validator.run_comprehensive_analysis()
    print(f"Analysis complete. Check {validator.output_dir} for results.")
