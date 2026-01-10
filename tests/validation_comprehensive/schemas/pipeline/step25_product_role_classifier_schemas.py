#!/usr/bin/env python3
"""
Step 25 Product Role Classifier Validation Schemas

This module contains schemas for product role classification validation from Step 25.

Author: Data Pipeline
Date: 2025-01-16
"""

import pandera as pa
from pandera.typing import Series


class ProductRoleClassificationSchema(pa.DataFrameModel):
    """Schema for product role classifications from Step 25 - matches actual CSV output structure."""
    
    # Product identification
    spu_code: Series[str] = pa.Field()
    product_role: Series[str] = pa.Field()  # "CORE", "SEASONAL", "FILLER", "CLEARANCE"
    confidence_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    rationale: Series[str] = pa.Field()
    
    # Performance metrics
    total_sales: Series[float] = pa.Field(ge=0.0)
    store_coverage: Series[float] = pa.Field(ge=0.0, le=1.0)
    fashion_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    consistency_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Product categorization
    category: Series[str] = pa.Field()
    subcategory: Series[str] = pa.Field()
    
    # Cluster analysis
    dominant_cluster: Series[int] = pa.Field(ge=0, le=50)
    clusters_present: Series[int] = pa.Field(ge=1)
    cluster_distribution: Series[str] = pa.Field()  # "wide", "focused", "single"


class ProductRoleAnalysisReportSchema(pa.DataFrameModel):
    """Schema for product role analysis report from Step 25."""
    
    # Report metadata
    report_timestamp: Series[str] = pa.Field()
    total_products_analyzed: Series[int] = pa.Field(ge=0)
    analysis_period: Series[str] = pa.Field()
    
    # Role distribution
    core_count: Series[int] = pa.Field(ge=0)
    seasonal_count: Series[int] = pa.Field(ge=0)
    filler_count: Series[int] = pa.Field(ge=0)
    clearance_count: Series[int] = pa.Field(ge=0)
    
    # Performance metrics
    avg_confidence_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    avg_total_sales: Series[float] = pa.Field(ge=0.0)
    avg_store_coverage: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Category analysis
    top_performing_category: Series[str] = pa.Field()
    category_role_distribution: Series[str] = pa.Field()  # JSON string
    
    # Cluster analysis
    most_diverse_cluster: Series[int] = pa.Field(ge=0, le=50)
    cluster_role_concentration: Series[str] = pa.Field()  # JSON string


class ProductRoleSummarySchema(pa.DataFrameModel):
    """Schema for product role summary JSON from Step 25."""
    
    # Summary metadata
    summary_timestamp: Series[str] = pa.Field()
    total_products: Series[int] = pa.Field(ge=0)
    analysis_completed: Series[bool] = pa.Field()
    
    # Role statistics
    role_distribution: Series[str] = pa.Field()  # JSON string with role counts
    confidence_distribution: Series[str] = pa.Field()  # JSON string with confidence ranges
    
    # Performance insights
    top_performers: Series[str] = pa.Field()  # JSON string with top SPU codes
    optimization_opportunities: Series[str] = pa.Field()  # JSON string with recommendations
    
    # Data quality
    validation_passed: Series[bool] = pa.Field()
    data_quality_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    missing_data_count: Series[int] = pa.Field(ge=0)


