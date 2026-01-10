#!/usr/bin/env python3
"""
Step 6: Cluster Analysis Schemas

Validation schemas for Step 6 - Cluster Analysis for Subcategory and SPU-Level Data.
This step performs clustering analysis on matrices created in Step 3.

Author: Data Pipeline
Date: 2025-09-16
"""

import pandas as pd
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
import numpy as np


class ClusteringInputSchema(BaseModel):
    """Schema for clustering input data validation"""
    str_code: str = Field(..., description="Store code")
    matrix_data: Dict[str, float] = Field(..., description="Matrix data for clustering")
    analysis_level: str = Field(..., description="Analysis level: spu, subcategory, or category_aggregated")
    
    @field_validator('analysis_level')
    @classmethod
    def validate_analysis_level(cls, value):
        valid_levels = ['spu', 'subcategory', 'category_aggregated']
        if value not in valid_levels:
            raise ValueError(f'Analysis level must be one of: {valid_levels}')
        return value


class ClusteringResultsSchema(BaseModel):
    """Schema for clustering results validation"""
    str_code: str = Field(..., description="Store code")
    cluster_id: int = Field(..., ge=0, description="Cluster ID")
    cluster: str = Field(..., description="Cluster label")
    analysis_level: str = Field(..., description="Analysis level used")
    period_label: str = Field(..., description="Period label")
    silhouette_score: Optional[float] = Field(None, ge=-1, le=1, description="Silhouette score for this store")
    distance_to_centroid: Optional[float] = Field(None, ge=0, description="Distance to cluster centroid")
    
    @field_validator('cluster')
    @classmethod
    def validate_cluster_label(cls, value):
        if not value or not value.strip():
            raise ValueError('Cluster label cannot be empty')
        return value.strip()


class ClusterProfilesSchema(BaseModel):
    """Schema for cluster profile validation"""
    cluster_id: int = Field(..., ge=0, description="Cluster ID")
    cluster: str = Field(..., description="Cluster label")
    cluster_size: int = Field(..., ge=1, description="Number of stores in cluster")
    analysis_level: str = Field(..., description="Analysis level")
    period_label: str = Field(..., description="Period label")
    silhouette_score: float = Field(..., ge=-1, le=1, description="Cluster silhouette score")
    calinski_harabasz_score: Optional[float] = Field(None, ge=0, description="Calinski-Harabasz score")
    davies_bouldin_score: Optional[float] = Field(None, ge=0, description="Davies-Bouldin score")
    inertia: Optional[float] = Field(None, ge=0, description="Cluster inertia")
    
    @field_validator('cluster_size')
    @classmethod
    def validate_cluster_size(cls, value):
        if value < 2:
            raise ValueError('Cluster size must be at least 2')
        return value


class PerClusterMetricsSchema(BaseModel):
    """Schema for per-cluster metrics validation"""
    cluster_id: int = Field(..., ge=0, description="Cluster ID")
    metric_name: str = Field(..., description="Metric name")
    metric_value: float = Field(..., description="Metric value")
    metric_type: str = Field(..., description="Metric type: internal, external, or stability")
    
    @field_validator('metric_type')
    @classmethod
    def validate_metric_type(cls, value):
        valid_types = ['internal', 'external', 'stability', 'quality']
        if value not in valid_types:
            raise ValueError(f'Metric type must be one of: {valid_types}')
        return value


class ClusteringParametersSchema(BaseModel):
    """Schema for clustering parameters validation"""
    n_clusters: int = Field(..., ge=2, le=50, description="Number of clusters")
    algorithm: str = Field(..., description="Clustering algorithm used")
    random_state: Optional[int] = Field(None, ge=0, description="Random state for reproducibility")
    max_iter: int = Field(..., ge=10, le=1000, description="Maximum iterations")
    tolerance: float = Field(..., ge=1e-6, le=1e-1, description="Convergence tolerance")
    temperature_aware: bool = Field(default=False, description="Whether temperature-aware clustering was used")
    
    @field_validator('algorithm')
    @classmethod
    def validate_algorithm(cls, value):
        valid_algorithms = ['kmeans', 'kmeans++', 'hierarchical', 'dbscan', 'gaussian_mixture']
        if value not in valid_algorithms:
            raise ValueError(f'Algorithm must be one of: {valid_algorithms}')
        return value


class MatrixValidationSchema(BaseModel):
    """Schema for matrix validation"""
    matrix_type: str = Field(..., description="Type of matrix: spu, subcategory, or category_aggregated")
    matrix_shape: List[int] = Field(..., min_length=2, max_length=2, description="Matrix dimensions [rows, cols]")
    missing_values: int = Field(..., ge=0, description="Number of missing values")
    zero_values: int = Field(..., ge=0, description="Number of zero values")
    data_range: List[float] = Field(..., min_length=2, max_length=2, description="Data range [min, max]")
    sparsity: float = Field(..., ge=0, le=1, description="Matrix sparsity (0=dense, 1=sparse)")
    
    @field_validator('matrix_shape')
    @classmethod
    def validate_matrix_shape(cls, value):
        if len(value) != 2 or value[0] <= 0 or value[1] <= 0:
            raise ValueError('Matrix shape must be [rows, cols] with positive dimensions')
        return value


class Step6InputSchema(BaseModel):
    """Schema for Step 6 input validation"""
    matrix_data: List[ClusteringInputSchema] = Field(..., min_length=1, description="Matrix data for clustering")
    clustering_params: ClusteringParametersSchema = Field(..., description="Clustering parameters")
    matrix_validation: MatrixValidationSchema = Field(..., description="Matrix validation results")
    temperature_data: Optional[List[Dict[str, Any]]] = Field(None, description="Optional temperature data")
    
    @field_validator('matrix_data')
    @classmethod
    def validate_matrix_data_consistency(cls, value):
        if not value:
            raise ValueError('Matrix data cannot be empty')
        
        # Check all records have same analysis level
        analysis_levels = set(record.analysis_level for record in value)
        if len(analysis_levels) > 1:
            raise ValueError('All matrix data must have the same analysis level')
        
        return value


class Step6OutputSchema(BaseModel):
    """Schema for Step 6 output validation"""
    clustering_results: List[ClusteringResultsSchema] = Field(..., min_length=1, description="Clustering results")
    cluster_profiles: List[ClusterProfilesSchema] = Field(..., min_length=1, description="Cluster profiles")
    cluster_metrics: List[PerClusterMetricsSchema] = Field(..., min_length=1, description="Cluster metrics")
    clustering_summary: Dict[str, Any] = Field(..., description="Clustering summary statistics")
    
    @field_validator('clustering_results')
    @classmethod
    def validate_clustering_consistency(cls, value):
        if not value:
            raise ValueError('Clustering results cannot be empty')
        
        # Check cluster IDs are valid
        cluster_ids = [record.cluster_id for record in value]
        if min(cluster_ids) < 0:
            raise ValueError('Cluster IDs must be non-negative')
        
        return value


class Step6ValidationSchema(BaseModel):
    """Schema for Step 6 validation results"""
    validation_passed: bool = Field(..., description="Whether validation passed")
    input_validation: Dict[str, Any] = Field(..., description="Input validation results")
    output_validation: Dict[str, Any] = Field(..., description="Output validation results")
    clustering_validation: Dict[str, Any] = Field(..., description="Clustering validation results")
    matrix_validation: Dict[str, Any] = Field(..., description="Matrix validation results")
    file_validation: Dict[str, Any] = Field(..., description="File validation results")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    statistics: Dict[str, Any] = Field(..., description="Validation statistics")


class ClusteringVisualizationSchema(BaseModel):
    """Schema for clustering visualization data"""
    cluster_id: int = Field(..., ge=0, description="Cluster ID")
    x_coordinate: float = Field(..., description="X coordinate for visualization")
    y_coordinate: float = Field(..., description="Y coordinate for visualization")
    z_coordinate: Optional[float] = Field(None, description="Z coordinate for 3D visualization")
    color_value: Optional[float] = Field(None, description="Color value for visualization")
    size_value: Optional[float] = Field(None, description="Size value for visualization")
    store_codes: List[str] = Field(..., min_length=1, description="Store codes in this cluster")


# Export all schemas
__all__ = [
    'ClusteringInputSchema',
    'ClusteringResultsSchema',
    'ClusterProfilesSchema',
    'PerClusterMetricsSchema',
    'ClusteringParametersSchema',
    'MatrixValidationSchema',
    'Step6InputSchema',
    'Step6OutputSchema',
    'Step6ValidationSchema',
    'ClusteringVisualizationSchema'
]
