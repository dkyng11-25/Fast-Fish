import pandas as pd
#!/usr/bin/env python3
"""
Step 21 Label Tag Recommendations Validation Schemas

This module contains schemas for label tag recommendations validation from Step 21.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series


class LabelTagRecommendationsSchema(pa.DataFrameModel):
    """Schema for label tag recommendations from Step 21 - matches actual Excel output structure."""
    
    # Bilingual column names as they appear in the actual Excel output
    cluster_id: Series[int] = pa.Field(alias="集群编号 / Cluster ID", ge=0, le=50)
    tag_combination: Series[str] = pa.Field(alias="标签组合 / Tag Combination")
    placement: Series[str] = pa.Field(alias="陈列位置 / Placement")
    target_qty: Series[float] = pa.Field(alias="建议数量 / Target Qty (units/day)", ge=0.0)
    rationale_score: Series[float] = pa.Field(alias="评分 / Rationale Score", ge=0.0, le=1.0)
    constraints: Series[str] = pa.Field(alias="约束 / Constraints", nullable=True)
    stores_in_cluster: Series[int] = pa.Field(alias="集群门店数 / Stores in Cluster", ge=1)
    spu_count: Series[int] = pa.Field(alias="SPU数量 / SPU Count", ge=0)
    store_coverage_pct: Series[str] = pa.Field(alias="门店覆盖率 / Store Coverage %")
    
    # Validation
    tag_validation_status: Series[str] = pa.Field()  # "validated", "pending", "failed"
    validation_notes: Series[str] = pa.Field(nullable=True)
    last_updated: Series[str] = pa.Field()


class TagAnalysisSchema(pa.DataFrameModel):
    """Schema for tag analysis data."""
    
    tag_name: Series[str] = pa.Field()
    tag_category: Series[str] = pa.Field()  # "season", "gender", "style", "occasion", "material"
    
    # Usage metrics
    usage_count: Series[int] = pa.Field(ge=0)
    usage_frequency: Series[float] = pa.Field(ge=0.0, le=1.0)
    unique_products: Series[int] = pa.Field(ge=0)
    
    # Performance metrics
    avg_sales_with_tag: Series[float] = pa.Field(ge=0.0, nullable=True)
    avg_sales_without_tag: Series[float] = pa.Field(ge=0.0, nullable=True)
    sales_impact: Series[float] = pa.Field(nullable=True)
    
    # Search metrics
    search_frequency: Series[int] = pa.Field(ge=0, nullable=True)
    click_through_rate: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    conversion_rate: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    
    # Quality metrics
    tag_consistency: Series[float] = pa.Field(ge=0.0, le=1.0)
    tag_accuracy: Series[float] = pa.Field(ge=0.0, le=1.0)
    tag_completeness: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Recommendations
    recommended_usage: Series[str] = pa.Field(nullable=True)  # "increase", "maintain", "decrease", "remove"
    optimization_potential: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)


class TagRecommendationEngineSchema(pa.DataFrameModel):
    """Schema for tag recommendation engine metadata."""
    
    # Engine identification
    engine_id: Series[str] = pa.Field()
    engine_version: Series[str] = pa.Field()
    model_type: Series[str] = pa.Field()  # "ml", "rule_based", "hybrid"
    
    # Training data
    training_samples: Series[int] = pa.Field(ge=0)
    training_accuracy: Series[float] = pa.Field(ge=0.0, le=1.0)
    validation_accuracy: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Performance metrics
    recommendation_accuracy: Series[float] = pa.Field(ge=0.0, le=1.0)
    recommendation_precision: Series[float] = pa.Field(ge=0.0, le=1.0)
    recommendation_recall: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Model parameters
    model_parameters: Series[str] = pa.Field(nullable=True)  # JSON string
    feature_importance: Series[str] = pa.Field(nullable=True)  # JSON string
    
    # Deployment info
    deployment_date: Series[str] = pa.Field()
    last_retrained: Series[str] = pa.Field(nullable=True)
    model_status: Series[str] = pa.Field()  # "active", "deprecated", "testing"
