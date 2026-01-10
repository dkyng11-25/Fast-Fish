#!/usr/bin/env python3
"""
Step 6: Cluster Analysis Validators

Validation functions for Step 6 - Cluster Analysis for Subcategory and SPU-Level Data.
Provides comprehensive validation for clustering inputs, results, and output files.

Author: Data Pipeline
Date: 2025-09-16
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score

from ..schemas.step6_schemas import (
    ClusteringInputSchema, ClusteringResultsSchema, ClusterProfilesSchema,
    PerClusterMetricsSchema, Step6InputSchema, Step6OutputSchema, Step6ValidationSchema
)

logger = logging.getLogger(__name__)


def validate_clustering_input(df: pd.DataFrame, analysis_level: str) -> Dict[str, Any]:
    """
    Validate clustering input data.
    
    Args:
        df: Input matrix DataFrame
        analysis_level: Analysis level (spu, subcategory, category_aggregated)
        
    Returns:
        Dictionary with validation results
    """
    results = {
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        # Check required columns
        required_cols = ['str_code']
        if analysis_level == 'spu':
            required_cols.extend(['spu_code', 'spu_sales_amt'])
        elif analysis_level == 'subcategory':
            required_cols.extend(['sub_cate_name', 'sal_amt'])
        elif analysis_level == 'category_aggregated':
            required_cols.extend(['cate_name', 'total_sales'])
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            results["errors"].append(f"Missing required columns for {analysis_level}: {missing_cols}")
            results["validation_passed"] = False
        
        # Check data types
        if 'str_code' in df.columns:
            if not df['str_code'].dtype == 'object':
                results["warnings"].append("Store codes should be string type")
        
        # Check for missing values
        missing_counts = df.isnull().sum()
        results["statistics"]["missing_values"] = missing_counts.to_dict()
        
        if missing_counts.sum() > 0:
            results["warnings"].append(f"Found {missing_counts.sum()} missing values")
        
        # Check data consistency
        if 'str_code' in df.columns:
            unique_stores = df['str_code'].nunique()
            results["statistics"]["unique_stores"] = unique_stores
            
            if unique_stores < 10:
                results["warnings"].append(f"Only {unique_stores} stores in clustering input")
            elif unique_stores > 10000:
                results["warnings"].append(f"Large number of stores ({unique_stores}) may impact performance")
        
        # Check sales data ranges
        sales_cols = [col for col in df.columns if 'sales' in col.lower() or 'amt' in col.lower()]
        for col in sales_cols:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                sales_stats = df[col].describe()
                results["statistics"][f"{col}_range"] = {
                    "min": sales_stats['min'],
                    "max": sales_stats['max'],
                    "mean": sales_stats['mean'],
                    "std": sales_stats['std']
                }
                
                if sales_stats['min'] < 0:
                    results["warnings"].append(f"Negative values found in {col}")
                
                if sales_stats['max'] > 1e6:
                    results["warnings"].append(f"Very large values found in {col}")
        
        # Check matrix sparsity
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            zero_count = (df[numeric_cols] == 0).sum().sum()
            total_values = len(df) * len(numeric_cols)
            sparsity = zero_count / total_values if total_values > 0 else 0
            results["statistics"]["sparsity"] = sparsity
            
            if sparsity > 0.8:
                results["warnings"].append(f"High sparsity ({sparsity:.2%}) in matrix data")
        
    except Exception as e:
        results["errors"].append(f"Clustering input validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_clustering_results(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate clustering results.
    
    Args:
        df: Clustering results DataFrame
        
    Returns:
        Dictionary with validation results
    """
    results = {
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        # Check required columns
        required_cols = ['str_code', 'cluster_id', 'cluster']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            results["errors"].append(f"Missing required columns: {missing_cols}")
            results["validation_passed"] = False
        
        # Check cluster IDs
        if 'cluster_id' in df.columns:
            cluster_ids = df['cluster_id'].unique()
            results["statistics"]["unique_clusters"] = len(cluster_ids)
            results["statistics"]["cluster_id_range"] = {
                "min": min(cluster_ids),
                "max": max(cluster_ids)
            }
            
            if min(cluster_ids) < 0:
                results["errors"].append("Cluster IDs must be non-negative")
                results["validation_passed"] = False
            
            # Check for consecutive cluster IDs
            expected_ids = set(range(len(cluster_ids)))
            actual_ids = set(cluster_ids)
            if expected_ids != actual_ids:
                results["warnings"].append("Cluster IDs are not consecutive starting from 0")
        
        # Check cluster labels
        if 'cluster' in df.columns:
            cluster_labels = df['cluster'].unique()
            results["statistics"]["unique_cluster_labels"] = len(cluster_labels)
            
            empty_labels = df['cluster'].isnull().sum()
            if empty_labels > 0:
                results["errors"].append(f"Found {empty_labels} empty cluster labels")
                results["validation_passed"] = False
        
        # Check cluster sizes
        if 'cluster_id' in df.columns:
            cluster_sizes = df['cluster_id'].value_counts()
            results["statistics"]["cluster_size_range"] = {
                "min": cluster_sizes.min(),
                "max": cluster_sizes.max(),
                "mean": cluster_sizes.mean()
            }
            
            small_clusters = cluster_sizes[cluster_sizes < 2]
            if len(small_clusters) > 0:
                results["warnings"].append(f"Found {len(small_clusters)} clusters with less than 2 stores")
            
            large_clusters = cluster_sizes[cluster_sizes > 1000]
            if len(large_clusters) > 0:
                results["warnings"].append(f"Found {len(large_clusters)} clusters with more than 1000 stores")
        
        # Check silhouette scores if available
        if 'silhouette_score' in df.columns:
            silhouette_stats = df['silhouette_score'].describe()
            results["statistics"]["silhouette_score_range"] = {
                "min": silhouette_stats['min'],
                "max": silhouette_stats['max'],
                "mean": silhouette_stats['mean']
            }
            
            low_silhouette = df[df['silhouette_score'] < 0.1]
            if len(low_silhouette) > 0:
                results["warnings"].append(f"Found {len(low_silhouette)} stores with low silhouette scores (<0.1)")
        
        # Check for duplicate stores
        if 'str_code' in df.columns:
            duplicate_stores = df['str_code'].duplicated().sum()
            if duplicate_stores > 0:
                results["errors"].append(f"Found {duplicate_stores} duplicate store codes")
                results["validation_passed"] = False
        
    except Exception as e:
        results["errors"].append(f"Clustering results validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_cluster_profiles(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate cluster profiles.
    
    Args:
        df: Cluster profiles DataFrame
        
    Returns:
        Dictionary with validation results
    """
    results = {
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        # Check required columns
        required_cols = ['cluster_id', 'cluster', 'cluster_size']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            results["errors"].append(f"Missing required columns: {missing_cols}")
            results["validation_passed"] = False
        
        # Check cluster sizes
        if 'cluster_size' in df.columns:
            size_stats = df['cluster_size'].describe()
            results["statistics"]["cluster_size_range"] = {
                "min": size_stats['min'],
                "max": size_stats['max'],
                "mean": size_stats['mean']
            }
            
            if size_stats['min'] < 2:
                results["errors"].append("Some clusters have less than 2 stores")
                results["validation_passed"] = False
        
        # Check silhouette scores
        if 'silhouette_score' in df.columns:
            silhouette_stats = df['silhouette_score'].describe()
            results["statistics"]["silhouette_score_range"] = {
                "min": silhouette_stats['min'],
                "max": silhouette_stats['max'],
                "mean": silhouette_stats['mean']
            }
            
            if silhouette_stats['mean'] < 0.3:
                results["warnings"].append("Low average silhouette score indicates poor clustering quality")
        
        # Check other quality metrics
        quality_metrics = ['calinski_harabasz_score', 'davies_bouldin_score', 'inertia']
        for metric in quality_metrics:
            if metric in df.columns:
                metric_stats = df[metric].describe()
                results["statistics"][f"{metric}_range"] = {
                    "min": metric_stats['min'],
                    "max": metric_stats['max'],
                    "mean": metric_stats['mean']
                }
        
        # Check for missing cluster profiles
        if 'cluster_id' in df.columns:
            unique_clusters = df['cluster_id'].nunique()
            results["statistics"]["unique_clusters"] = unique_clusters
            
            if unique_clusters < 2:
                results["warnings"].append("Very few clusters found")
        
    except Exception as e:
        results["errors"].append(f"Cluster profiles validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_clustering_quality(df_results: pd.DataFrame, df_profiles: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate overall clustering quality.
    
    Args:
        df_results: Clustering results DataFrame
        df_profiles: Cluster profiles DataFrame
        
    Returns:
        Dictionary with quality validation results
    """
    results = {
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        # Check cluster balance
        if 'cluster_id' in df_results.columns:
            cluster_sizes = df_results['cluster_id'].value_counts()
            size_std = cluster_sizes.std()
            size_mean = cluster_sizes.mean()
            cv = size_std / size_mean if size_mean > 0 else 0
            
            results["statistics"]["cluster_balance"] = {
                "coefficient_of_variation": cv,
                "size_std": size_std,
                "size_mean": size_mean
            }
            
            if cv > 1.0:
                results["warnings"].append("High cluster size variation indicates imbalanced clustering")
        
        # Check silhouette score distribution
        if 'silhouette_score' in df_results.columns:
            silhouette_scores = df_results['silhouette_score'].dropna()
            if len(silhouette_scores) > 0:
                mean_silhouette = silhouette_scores.mean()
                results["statistics"]["overall_silhouette"] = mean_silhouette
                
                if mean_silhouette < 0.2:
                    results["warnings"].append("Low overall silhouette score indicates poor clustering")
                elif mean_silhouette > 0.7:
                    results["warnings"].append("Very high silhouette score - check for over-clustering")
        
        # Check cluster separation
        if 'cluster_id' in df_results.columns and 'silhouette_score' in df_results.columns:
            cluster_silhouettes = df_results.groupby('cluster_id')['silhouette_score'].mean()
            results["statistics"]["cluster_silhouette_range"] = {
                "min": cluster_silhouettes.min(),
                "max": cluster_silhouettes.max(),
                "mean": cluster_silhouettes.mean()
            }
            
            low_quality_clusters = cluster_silhouettes[cluster_silhouettes < 0.1]
            if len(low_quality_clusters) > 0:
                results["warnings"].append(f"Found {len(low_quality_clusters)} clusters with low silhouette scores")
        
    except Exception as e:
        results["errors"].append(f"Clustering quality validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_step6_files(period_label: str, analysis_level: str, data_dir: str = "output") -> Dict[str, Any]:
    """
    Validate Step 6 output files.
    
    Args:
        period_label: Period label for file naming
        analysis_level: Analysis level (spu, subcategory, category_aggregated)
        data_dir: Directory containing output files
        
    Returns:
        Dictionary with file validation results
    """
    results = {
        "validation_passed": False,  # Requires real data validation
        "errors": [],
        "warnings": [],
        "files_checked": [],
        "file_validation": {}
    }
    
    try:
        data_path = Path(data_dir)
        
        # Check main output files
        expected_files = [
            f"clustering_results_{analysis_level}_{period_label}.csv",
            f"cluster_profiles_{analysis_level}_{period_label}.csv"
        ]
        
        for filename in expected_files:
            file_path = data_path / filename
            results["files_checked"].append(str(file_path))
            
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    file_results = {
                        "exists": True,
                        "rows": len(df),
                        "columns": list(df.columns),
                        "file_size_mb": file_path.stat().st_size / (1024 * 1024)
                    }
                    
                    # Validate specific file content
                    if "clustering_results" in filename:
                        validation_result = validate_clustering_results(df)
                        file_results["validation"] = validation_result
                    elif "cluster_profiles" in filename:
                        validation_result = validate_cluster_profiles(df)
                        file_results["validation"] = validation_result
                    
                    results["file_validation"][filename] = file_results
                    
                    if file_results.get("validation", {}).get("validation_passed", True) == False:
                        results["warnings"].append(f"Validation issues in {filename}")
                    
                except Exception as e:
                    results["errors"].append(f"Error reading {filename}: {str(e)}")
                    results["validation_passed"] = False
            else:
                results["errors"].append(f"Missing required file: {filename}")
                results["validation_passed"] = False
                results["file_validation"][filename] = {"exists": False}
        
        # Check for visualization files
        viz_files = list(data_path.glob(f"clustering_visualization_{analysis_level}_{period_label}.*"))
        if viz_files:
            results["files_checked"].extend([str(f) for f in viz_files])
            results["statistics"]["visualization_files_found"] = len(viz_files)
        
    except Exception as e:
        results["errors"].append(f"File validation error: {str(e)}")
        results["validation_passed"] = False
    
    return results


def validate_step6_complete(period_label: str, analysis_level: str, data_dir: str = "output") -> Step6ValidationSchema:
    """
    Complete validation for Step 6.
    
    Args:
        period_label: Period label for validation
        analysis_level: Analysis level (spu, subcategory, category_aggregated)
        data_dir: Directory containing output files
        
    Returns:
        Complete validation results
    """
    logger.info(f"Starting complete Step 6 validation for period {period_label}, level {analysis_level}")
    
    # Initialize validation results
    validation_results = {
        "validation_passed": False,  # Requires real data validation
        "input_validation": {},
        "output_validation": {},
        "clustering_validation": {},
        "matrix_validation": {},
        "file_validation": {},
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        # File validation
        file_validation = validate_step6_files(period_label, analysis_level, data_dir)
        validation_results["file_validation"] = file_validation
        validation_results["validation_passed"] = file_validation["validation_passed"]
        validation_results["errors"].extend(file_validation["errors"])
        validation_results["warnings"].extend(file_validation["warnings"])
        
        # Load and validate output data
        data_path = Path(data_dir)
        results_file = data_path / f"clustering_results_{analysis_level}_{period_label}.csv"
        profiles_file = data_path / f"cluster_profiles_{analysis_level}_{period_label}.csv"
        
        if results_file.exists() and profiles_file.exists():
            df_results = pd.read_csv(results_file)
            df_profiles = pd.read_csv(profiles_file)
            
            # Validate clustering results
            results_validation = validate_clustering_results(df_results)
            validation_results["output_validation"]["clustering_results"] = results_validation
            validation_results["statistics"]["clustering_results_records"] = len(df_results)
            
            if not results_validation["validation_passed"]:
                validation_results["validation_passed"] = False
            
            # Validate cluster profiles
            profiles_validation = validate_cluster_profiles(df_profiles)
            validation_results["output_validation"]["cluster_profiles"] = profiles_validation
            validation_results["statistics"]["cluster_profiles_records"] = len(df_profiles)
            
            if not profiles_validation["validation_passed"]:
                validation_results["validation_passed"] = False
            
            # Validate overall clustering quality
            quality_validation = validate_clustering_quality(df_results, df_profiles)
            validation_results["clustering_validation"] = quality_validation
            
            if not quality_validation["validation_passed"]:
                validation_results["validation_passed"] = False
        
        # Overall statistics
        validation_results["statistics"]["total_errors"] = len(validation_results["errors"])
        validation_results["statistics"]["total_warnings"] = len(validation_results["warnings"])
        validation_results["statistics"]["validation_timestamp"] = datetime.now().isoformat()
        
    except Exception as e:
        validation_results["errors"].append(f"Complete validation error: {str(e)}")
        validation_results["validation_passed"] = False
        logger.error(f"Step 6 validation failed: {str(e)}")
    
    return Step6ValidationSchema(**validation_results)


# Export all validators
__all__ = [
    'validate_clustering_input',
    'validate_clustering_results',
    'validate_cluster_profiles',
    'validate_clustering_quality',
    'validate_step6_files',
    'validate_step6_complete'
]


