#!/usr/bin/env python3
"""
Step 29 Supply-Demand Gap Analysis Validation Schemas

This module contains schemas for supply-demand gap analysis validation from Step 29.

Author: Data Pipeline
Date: 2025-01-16
"""

import pandera as pa
from pandera.typing import Series


class SPUVarietyGapsAnalysisSchema(pa.DataFrameModel):
    """Schema for SPU variety gaps analysis from Step 29 - matches actual CSV output structure."""
    
    # Store and cluster identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    cluster: Series[int] = pa.Field(ge=0, le=50)
    
    # Product categorization
    big_class_name: Series[str] = pa.Field()  # Category name
    sub_cate_name: Series[str] = pa.Field()  # Subcategory name
    display_location_name: Series[str] = pa.Field()  # Display location
    sex_name: Series[str] = pa.Field()  # Gender
    season_name: Series[str] = pa.Field()  # Season
    temperature_band: Series[str] = pa.Field()  # Temperature band
    
    # Gap analysis
    missing_spu_count: Series[float] = pa.Field(ge=0.0)
    recommendation: Series[str] = pa.Field()
    priority: Series[str] = pa.Field()  # Priority level
    
    # Analysis metadata
    date: Series[str] = pa.Field()  # Analysis period


class GapAnalysisDetailedSchema(pa.DataFrameModel):
    """Schema for detailed gap analysis from Step 29 - matches actual CSV output structure."""
    
    # Cluster identification
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    total_products: Series[int] = pa.Field(ge=0)
    total_stores: Series[int] = pa.Field(ge=0)
    
    # CORE role analysis
    core_count: Series[int] = pa.Field(ge=0)
    core_percentage: Series[float] = pa.Field(ge=0.0, le=100.0)
    core_gap: Series[float] = pa.Field()
    core_gap_severity: Series[str] = pa.Field()  # "CRITICAL", "OPTIMAL", "EXCESS"
    
    # SEASONAL role analysis
    seasonal_count: Series[int] = pa.Field(ge=0)
    seasonal_percentage: Series[float] = pa.Field(ge=0.0, le=100.0)
    seasonal_gap: Series[float] = pa.Field()
    seasonal_gap_severity: Series[str] = pa.Field()  # "CRITICAL", "OPTIMAL", "EXCESS"
    
    # FILLER role analysis
    filler_count: Series[int] = pa.Field(ge=0)
    filler_percentage: Series[float] = pa.Field(ge=0.0, le=100.0)
    filler_gap: Series[float] = pa.Field()
    filler_gap_severity: Series[str] = pa.Field()  # "CRITICAL", "OPTIMAL", "EXCESS"
    
    # CLEARANCE role analysis
    clearance_count: Series[int] = pa.Field(ge=0)
    clearance_percentage: Series[float] = pa.Field(ge=0.0, le=100.0)
    clearance_gap: Series[float] = pa.Field()
    clearance_gap_severity: Series[str] = pa.Field()  # "CRITICAL", "OPTIMAL", "EXCESS"
    
    # Product diversity
    category_count: Series[int] = pa.Field(ge=0)
    subcategory_count: Series[int] = pa.Field(ge=0)


class SupplyDemandGapReportSchema(pa.DataFrameModel):
    """Schema for supply-demand gap analysis report from Step 29."""
    
    # Report metadata
    report_timestamp: Series[str] = pa.Field()
    analysis_period: Series[str] = pa.Field()
    total_clusters_analyzed: Series[int] = pa.Field(ge=0)
    
    # Overall gap summary
    total_gaps_identified: Series[int] = pa.Field(ge=0)
    critical_gaps: Series[int] = pa.Field(ge=0)
    optimal_clusters: Series[int] = pa.Field(ge=0)
    
    # Role-specific gap analysis
    core_gap_summary: Series[str] = pa.Field()  # JSON string
    seasonal_gap_summary: Series[str] = pa.Field()  # JSON string
    filler_gap_summary: Series[str] = pa.Field()  # JSON string
    clearance_gap_summary: Series[str] = pa.Field()  # JSON string
    
    # Category and subcategory gaps
    category_gaps: Series[str] = pa.Field()  # JSON string
    subcategory_gaps: Series[str] = pa.Field()  # JSON string
    
    # Price band gaps
    price_band_gaps: Series[str] = pa.Field()  # JSON string
    
    # Style orientation gaps
    fashion_basic_gaps: Series[str] = pa.Field()  # JSON string
    
    # Capacity utilization gaps
    capacity_utilization_gaps: Series[str] = pa.Field()  # JSON string
    
    # Recommendations
    top_priority_gaps: Series[str] = pa.Field()  # JSON string
    recommended_actions: Series[str] = pa.Field()  # JSON string
    expected_impact: Series[str] = pa.Field()  # JSON string


class SupplyDemandGapSummarySchema(pa.DataFrameModel):
    """Schema for supply-demand gap summary JSON from Step 29."""
    
    # Summary metadata
    summary_timestamp: Series[str] = pa.Field()
    analysis_completed: Series[bool] = pa.Field()
    data_quality_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Gap statistics
    total_clusters: Series[int] = pa.Field(ge=0)
    clusters_with_gaps: Series[int] = pa.Field(ge=0)
    average_gap_magnitude: Series[float] = pa.Field()
    
    # Role distribution gaps
    role_gap_distribution: Series[str] = pa.Field()  # JSON string
    
    # Category gaps
    category_gap_distribution: Series[str] = pa.Field()  # JSON string
    
    # Price band gaps
    price_band_gap_distribution: Series[str] = pa.Field()  # JSON string
    
    # Style gaps
    style_gap_distribution: Series[str] = pa.Field()  # JSON string
    
    # Performance metrics
    gap_severity_distribution: Series[str] = pa.Field()  # JSON string
    optimization_potential: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Business impact
    revenue_impact_estimate: Series[float] = pa.Field(nullable=True)
    inventory_optimization_potential: Series[float] = pa.Field(ge=0.0, le=1.0)
    customer_satisfaction_impact: Series[str] = pa.Field()  # JSON string


class ClusterGapAnalysisSchema(pa.DataFrameModel):
    """Schema for individual cluster gap analysis from Step 29."""
    
    # Cluster identification
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    cluster_name: Series[str] = pa.Field(nullable=True)
    cluster_size: Series[int] = pa.Field(ge=0)
    
    # Gap severity by role
    core_gap_severity: Series[str] = pa.Field()
    seasonal_gap_severity: Series[str] = pa.Field()
    filler_gap_severity: Series[str] = pa.Field()
    clearance_gap_severity: Series[str] = pa.Field()
    
    # Overall cluster assessment
    overall_gap_severity: Series[str] = pa.Field()  # "CRITICAL", "MODERATE", "OPTIMAL"
    gap_priority_score: Series[float] = pa.Field(ge=0.0, le=10.0)
    
    # Recommendations
    primary_recommendation: Series[str] = pa.Field()
    secondary_recommendations: Series[str] = pa.Field()  # JSON string
    implementation_priority: Series[str] = pa.Field()  # "high", "medium", "low"
    
    # Business impact
    expected_revenue_impact: Series[float] = pa.Field(nullable=True)
    required_investment: Series[float] = pa.Field(ge=0.0, nullable=True)
    expected_roi: Series[float] = pa.Field(nullable=True)


