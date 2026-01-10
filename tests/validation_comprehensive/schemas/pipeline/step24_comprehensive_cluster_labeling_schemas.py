import pandas as pd
#!/usr/bin/env python3
"""
Step 24 Comprehensive Cluster Labeling Validation Schemas

This module contains schemas for comprehensive cluster labeling validation from Step 24.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series


class ComprehensiveClusterLabelingSchema(pa.DataFrameModel):
    """Schema for comprehensive cluster labeling from Step 24 - matches actual CSV output structure."""
    
    # Core cluster information (matches actual output)
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    cluster_size: Series[int] = pa.Field(ge=1)
    store_codes: Series[str] = pa.Field()  # Comma-separated store codes
    
    # Fashion/Basic analysis
    fashion_ratio: Series[float] = pa.Field(ge=0.0, le=100.0)
    basic_ratio: Series[float] = pa.Field(ge=0.0, le=100.0)
    fashion_basic_classification: Series[str] = pa.Field()
    fashion_basic_data_source: Series[str] = pa.Field()
    
    # Temperature analysis
    avg_feels_like_temp: Series[float] = pa.Field()
    temp_range: Series[str] = pa.Field()  # e.g., "12.4°C to 16.5°C"
    dominant_temp_band: Series[str] = pa.Field()
    temperature_classification: Series[str] = pa.Field()
    temperature_data_source: Series[str] = pa.Field()
    
    # Capacity analysis
    avg_estimated_capacity: Series[float] = pa.Field(ge=0.0)
    capacity_tier: Series[str] = pa.Field()
    capacity_data_source: Series[str] = pa.Field()
    
    # Silhouette analysis
    silhouette_score: Series[float] = pa.Field()
    silhouette_quality: Series[str] = pa.Field()
    silhouette_data_source: Series[str] = pa.Field()
    
    # Comprehensive labeling
    comprehensive_label: Series[str] = pa.Field()
    analysis_timestamp: Series[str] = pa.Field()
    total_data_sources: Series[int] = pa.Field(ge=1)
    brand_loyalty: Series[str] = pa.Field(nullable=True)  # "high", "medium", "low"
    
    # Product preferences
    preferred_categories: Series[str] = pa.Field(nullable=True)
    preferred_price_range: Series[str] = pa.Field(nullable=True)
    seasonal_preferences: Series[str] = pa.Field(nullable=True)
    
    # Labeling metadata
    labeling_confidence: Series[float] = pa.Field(ge=0.0, le=1.0)
    labeling_method: Series[str] = pa.Field()  # "ml", "rule_based", "hybrid", "manual"
    labeling_timestamp: Series[str] = pa.Field()
    label_validation_status: Series[str] = pa.Field()  # "validated", "pending", "failed"


class ClusterLabelAnalysisSchema(pa.DataFrameModel):
    """Schema for cluster label analysis."""
    
    # Label identification
    label_name: Series[str] = pa.Field()
    label_category: Series[str] = pa.Field()  # "geographic", "demographic", "performance", "behavioral"
    label_type: Series[str] = pa.Field()  # "primary", "secondary", "tertiary"
    
    # Label distribution
    clusters_with_label: Series[int] = pa.Field(ge=0)
    stores_with_label: Series[int] = pa.Field(ge=0)
    label_frequency: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Label quality
    label_consistency: Series[float] = pa.Field(ge=0.0, le=1.0)
    label_accuracy: Series[float] = pa.Field(ge=0.0, le=1.0)
    label_completeness: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Business impact
    business_relevance: Series[float] = pa.Field(ge=0.0, le=1.0)
    predictive_power: Series[float] = pa.Field(ge=0.0, le=1.0)
    actionability_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Label stability
    label_stability: Series[float] = pa.Field(ge=0.0, le=1.0)
    label_volatility: Series[float] = pa.Field(ge=0.0, nullable=True)
    last_updated: Series[str] = pa.Field()


class ClusterLabelingEngineSchema(pa.DataFrameModel):
    """Schema for cluster labeling engine metadata."""
    
    # Engine identification
    engine_id: Series[str] = pa.Field()
    engine_version: Series[str] = pa.Field()
    engine_type: Series[str] = pa.Field()  # "ml", "rule_based", "hybrid"
    
    # Training data
    training_clusters: Series[int] = pa.Field(ge=0)
    training_stores: Series[int] = pa.Field(ge=0)
    training_accuracy: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Performance metrics
    labeling_accuracy: Series[float] = pa.Field(ge=0.0, le=1.0)
    labeling_precision: Series[float] = pa.Field(ge=0.0, le=1.0)
    labeling_recall: Series[float] = pa.Field(ge=0.0, le=1.0)
    labeling_f1_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Model parameters
    model_parameters: Series[str] = pa.Field(nullable=True)  # JSON string
    feature_importance: Series[str] = pa.Field(nullable=True)  # JSON string
    
    # Deployment info
    deployment_date: Series[str] = pa.Field()
    last_retrained: Series[str] = pa.Field(nullable=True)
    model_status: Series[str] = pa.Field()  # "active", "deprecated", "testing"
    
    # Validation
    validation_passed: Series[bool] = pa.Field()
    validation_notes: Series[str] = pa.Field(nullable=True)
