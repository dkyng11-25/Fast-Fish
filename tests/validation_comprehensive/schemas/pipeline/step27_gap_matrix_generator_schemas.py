#!/usr/bin/env python3
"""
Step 27 Gap Matrix Generator Validation Schemas

This module contains schemas for gap matrix generation validation from Step 27.

Author: Data Pipeline
Date: 2025-01-16
"""

import pandera as pa
from pandera.typing import Series


class GapMatrixSchema(pa.DataFrameModel):
    """Schema for gap matrix Excel output from Step 27 - matches actual Excel structure."""
    
    # Cluster identification
    cluster_id: Series[str] = pa.Field(alias="Cluster_ID")
    total_products: Series[int] = pa.Field(alias="Total_Products", ge=0)
    total_stores: Series[int] = pa.Field(alias="Total_Stores", ge=0)
    
    # CORE role analysis
    core_current_pct: Series[float] = pa.Field(alias="CORE_Current_%", ge=0.0, le=100.0)
    core_gap: Series[float] = pa.Field(alias="CORE_Gap")
    core_status: Series[str] = pa.Field(alias="CORE_Status")  # "OPTIMAL", "CRITICAL", "EXCESS"
    
    # SEASONAL role analysis
    seasonal_current_pct: Series[float] = pa.Field(alias="SEASONAL_Current_%", ge=0.0, le=100.0)
    seasonal_gap: Series[float] = pa.Field(alias="SEASONAL_Gap")
    seasonal_status: Series[str] = pa.Field(alias="SEASONAL_Status")  # "OPTIMAL", "CRITICAL", "EXCESS"
    
    # FILLER role analysis
    filler_current_pct: Series[float] = pa.Field(alias="FILLER_Current_%", ge=0.0, le=100.0)
    filler_gap: Series[float] = pa.Field(alias="FILLER_Gap")
    filler_status: Series[str] = pa.Field(alias="FILLER_Status")  # "OPTIMAL", "CRITICAL", "EXCESS"
    
    # CLEARANCE role analysis
    clearance_current_pct: Series[float] = pa.Field(alias="CLEARANCE_Current_%", ge=0.0, le=100.0)
    clearance_gap: Series[float] = pa.Field(alias="CLEARANCE_Gap")
    clearance_status: Series[str] = pa.Field(alias="CLEARANCE_Status")  # "OPTIMAL", "CRITICAL", "EXCESS"


class GapAnalysisDetailedSchema(pa.DataFrameModel):
    """Schema for detailed gap analysis CSV from Step 27."""
    
    # Cluster and product identification
    cluster_id: Series[str] = pa.Field()
    spu_code: Series[str] = pa.Field()
    product_role: Series[str] = pa.Field()  # "CORE", "SEASONAL", "FILLER", "CLEARANCE"
    
    # Current state
    current_quantity: Series[float] = pa.Field(ge=0.0)
    current_percentage: Series[float] = pa.Field(ge=0.0, le=100.0)
    
    # Gap analysis
    target_percentage: Series[float] = pa.Field(ge=0.0, le=100.0)
    gap_percentage: Series[float] = pa.Field()
    gap_status: Series[str] = pa.Field()  # "OPTIMAL", "CRITICAL", "EXCESS"
    
    # Recommendations
    recommended_action: Series[str] = pa.Field()  # "INCREASE", "DECREASE", "MAINTAIN"
    priority_level: Series[str] = pa.Field()  # "HIGH", "MEDIUM", "LOW"
    estimated_impact: Series[float] = pa.Field(nullable=True)
    
    # Business context
    store_count: Series[int] = pa.Field(ge=0)
    sales_performance: Series[float] = pa.Field(ge=0.0, nullable=True)
    inventory_turnover: Series[float] = pa.Field(ge=0.0, nullable=True)


class GapMatrixAnalysisReportSchema(pa.DataFrameModel):
    """Schema for gap matrix analysis report from Step 27."""
    
    # Report metadata
    report_timestamp: Series[str] = pa.Field()
    analysis_period: Series[str] = pa.Field()
    total_clusters_analyzed: Series[int] = pa.Field(ge=0)
    
    # Overall gap summary
    total_gaps_identified: Series[int] = pa.Field(ge=0)
    critical_gaps: Series[int] = pa.Field(ge=0)
    optimal_clusters: Series[int] = pa.Field(ge=0)
    
    # Role-specific insights
    core_gap_summary: Series[str] = pa.Field()  # JSON string
    seasonal_gap_summary: Series[str] = pa.Field()  # JSON string
    filler_gap_summary: Series[str] = pa.Field()  # JSON string
    clearance_gap_summary: Series[str] = pa.Field()  # JSON string
    
    # Recommendations
    top_priority_clusters: Series[str] = pa.Field()  # JSON string
    recommended_actions: Series[str] = pa.Field()  # JSON string
    expected_impact: Series[str] = pa.Field()  # JSON string


class GapMatrixSummarySchema(pa.DataFrameModel):
    """Schema for gap matrix summary JSON from Step 27."""
    
    # Summary metadata
    summary_timestamp: Series[str] = pa.Field()
    analysis_completed: Series[bool] = pa.Field()
    data_quality_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Gap statistics
    total_clusters: Series[int] = pa.Field(ge=0)
    clusters_with_gaps: Series[int] = pa.Field(ge=0)
    average_gap_magnitude: Series[float] = pa.Field()
    
    # Role distribution
    role_distribution: Series[str] = pa.Field()  # JSON string
    gap_distribution: Series[str] = pa.Field()  # JSON string
    
    # Performance metrics
    optimization_potential: Series[float] = pa.Field(ge=0.0, le=1.0)
    critical_issues_count: Series[int] = pa.Field(ge=0)
    recommended_actions_count: Series[int] = pa.Field(ge=0)


