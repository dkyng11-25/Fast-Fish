import pandas as pd
#!/usr/bin/env python3
"""
Step 23 Update Clustering Features Validation Schemas

This module contains schemas for clustering features update validation from Step 23.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series


class ClusteringFeaturesUpdateSchema(pa.DataFrameModel):
    """Schema for clustering features update from Step 23."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    store_group: Series[str] = pa.Field()
    
    # Original clustering features
    original_cluster: Series[int] = pa.Field(ge=0, le=50)
    original_features: Series[str] = pa.Field(nullable=True)  # JSON string
    
    # Updated clustering features
    updated_cluster: Series[int] = pa.Field(ge=0, le=50)
    updated_features: Series[str] = pa.Field(nullable=True)  # JSON string
    
    # Feature changes
    feature_changes: Series[str] = pa.Field(nullable=True)  # JSON string
    features_added: Series[str] = pa.Field(nullable=True)
    features_removed: Series[str] = pa.Field(nullable=True)
    features_modified: Series[str] = pa.Field(nullable=True)
    
    # Clustering metrics
    cluster_stability_score: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    feature_importance_score: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    cluster_cohesion_score: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    
    # Update metadata
    update_timestamp: Series[str] = pa.Field()
    update_reason: Series[str] = pa.Field()
    update_method: Series[str] = pa.Field()  # "automatic", "manual", "hybrid"
    update_confidence: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Validation
    update_validated: Series[bool] = pa.Field()
    validation_notes: Series[str] = pa.Field(nullable=True)
    requires_manual_review: Series[bool] = pa.Field()


class ClusteringFeatureSchema(pa.DataFrameModel):
    """Schema for individual clustering features."""
    
    # Feature identification
    feature_name: Series[str] = pa.Field()
    feature_category: Series[str] = pa.Field()  # "sales", "demographic", "geographic", "behavioral"
    feature_type: Series[str] = pa.Field()  # "numeric", "categorical", "boolean"
    
    # Feature values
    feature_value: Series[float] = pa.Field(nullable=True)
    normalized_value: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    standardized_value: Series[float] = pa.Field(nullable=True)
    
    # Feature importance
    importance_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    feature_rank: Series[int] = pa.Field(ge=1, nullable=True)
    contribution_to_cluster: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    
    # Feature stability
    stability_score: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    volatility: Series[float] = pa.Field(ge=0.0, nullable=True)
    trend_direction: Series[str] = pa.Field(nullable=True)  # "increasing", "decreasing", "stable"
    
    # Update information
    last_updated: Series[str] = pa.Field()
    update_frequency: Series[str] = pa.Field()  # "daily", "weekly", "monthly", "quarterly"
    data_source: Series[str] = pa.Field()


class ClusterUpdateSummarySchema(pa.DataFrameModel):
    """Schema for cluster update summary."""
    
    # Update identification
    update_id: Series[str] = pa.Field()
    update_timestamp: Series[str] = pa.Field()
    update_type: Series[str] = pa.Field()  # "full", "incremental", "corrective"
    
    # Cluster statistics
    total_clusters: Series[int] = pa.Field(ge=1)
    clusters_modified: Series[int] = pa.Field(ge=0)
    clusters_added: Series[int] = pa.Field(ge=0)
    clusters_removed: Series[int] = pa.Field(ge=0)
    
    # Store statistics
    total_stores: Series[int] = pa.Field(ge=0)
    stores_reclustered: Series[int] = pa.Field(ge=0)
    stores_unchanged: Series[int] = pa.Field(ge=0)
    
    # Feature statistics
    total_features: Series[int] = pa.Field(ge=0)
    features_updated: Series[int] = pa.Field(ge=0)
    features_added: Series[int] = pa.Field(ge=0)
    features_removed: Series[int] = pa.Field(ge=0)
    
    # Quality metrics
    overall_quality_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    cluster_separation_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    cluster_cohesion_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Update status
    update_status: Series[str] = pa.Field()  # "completed", "in_progress", "failed", "pending"
    validation_status: Series[str] = pa.Field()  # "passed", "failed", "pending"
    requires_manual_review: Series[bool] = pa.Field()
    
    # Performance metrics
    update_duration_minutes: Series[float] = pa.Field(ge=0.0, nullable=True)
    memory_usage_mb: Series[float] = pa.Field(ge=0.0, nullable=True)
    cpu_usage_percent: Series[float] = pa.Field(ge=0.0, le=100.0, nullable=True)
