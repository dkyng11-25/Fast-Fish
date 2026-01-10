#!/usr/bin/env python3
"""
Step 31 Gap Analysis Workbook Validation Schemas

This module contains schemas for gap analysis workbook validation from Step 31.

Author: Data Pipeline
Date: 2025-01-16
"""

import pandera as pa
from pandera.typing import Series


class GapAnalysisWorkbookExcelSchema(pa.DataFrameModel):
    """Schema for gap analysis workbook Excel output from Step 31 - matches expected Excel structure."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    store_group: Series[str] = pa.Field()
    
    # Product identification
    spu_code: Series[str] = pa.Field()
    category: Series[str] = pa.Field()
    subcategory: Series[str] = pa.Field()
    
    # Current state
    current_quantity: Series[float] = pa.Field(ge=0.0)
    current_sales: Series[float] = pa.Field(ge=0.0)
    current_sellthrough_rate: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Gap analysis
    recommended_quantity: Series[float] = pa.Field(ge=0.0)
    quantity_gap: Series[float] = pa.Field()
    gap_severity: Series[str] = pa.Field()  # "CRITICAL", "MODERATE", "OPTIMAL"
    
    # Coverage matrix dimensions
    role_coverage: Series[str] = pa.Field()  # "CORE", "SEASONAL", "FILLER", "CLEARANCE"
    price_band_coverage: Series[str] = pa.Field()  # "BUDGET", "VALUE", "PREMIUM", "LUXURY"
    style_coverage: Series[str] = pa.Field()  # "Fashion", "Basic", "Mixed"
    season_coverage: Series[str] = pa.Field()  # "Spring", "Summer", "Fall", "Winter", "All-Season"
    gender_coverage: Series[str] = pa.Field()  # "Men", "Women", "Unisex"
    size_coverage: Series[str] = pa.Field()  # Size range coverage
    
    # Business metrics
    expected_revenue_impact: Series[float] = pa.Field(nullable=True)
    investment_required: Series[float] = pa.Field(ge=0.0, nullable=True)
    expected_roi: Series[float] = pa.Field(nullable=True)
    
    # Implementation details
    priority_level: Series[str] = pa.Field()  # "HIGH", "MEDIUM", "LOW"
    implementation_complexity: Series[str] = pa.Field()  # "LOW", "MEDIUM", "HIGH"
    expected_timeline: Series[str] = pa.Field()  # e.g., "1-3 months"


class GapAnalysisWorkbookCSVSchema(pa.DataFrameModel):
    """Schema for gap analysis workbook CSV output from Step 31."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    store_group: Series[str] = pa.Field()
    
    # Product identification
    spu_code: Series[str] = pa.Field()
    category: Series[str] = pa.Field()
    subcategory: Series[str] = pa.Field()
    
    # Gap analysis
    current_quantity: Series[float] = pa.Field(ge=0.0)
    recommended_quantity: Series[float] = pa.Field(ge=0.0)
    quantity_gap: Series[float] = pa.Field()
    gap_severity: Series[str] = pa.Field()
    
    # Coverage analysis
    role_gap: Series[float] = pa.Field()
    price_band_gap: Series[float] = pa.Field()
    style_gap: Series[float] = pa.Field()
    season_gap: Series[float] = pa.Field()
    gender_gap: Series[float] = pa.Field()
    size_gap: Series[float] = pa.Field()
    
    # Business impact
    revenue_impact: Series[float] = pa.Field(nullable=True)
    investment_required: Series[float] = pa.Field(ge=0.0, nullable=True)
    priority_score: Series[float] = pa.Field(ge=0.0, le=10.0)


class ExecutiveSummarySchema(pa.DataFrameModel):
    """Schema for executive summary JSON from Step 31."""
    
    # Summary metadata
    summary_timestamp: Series[str] = pa.Field()
    analysis_period: Series[str] = pa.Field()
    total_stores_analyzed: Series[int] = pa.Field(ge=0)
    total_products_analyzed: Series[int] = pa.Field(ge=0)
    
    # Overall gap summary
    total_gaps_identified: Series[int] = pa.Field(ge=0)
    critical_gaps: Series[int] = pa.Field(ge=0)
    moderate_gaps: Series[int] = pa.Field(ge=0)
    optimal_stores: Series[int] = pa.Field(ge=0)
    
    # Coverage matrix summary
    coverage_matrix_summary: Series[str] = pa.Field()  # JSON string
    dimension_coverage: Series[str] = pa.Field()  # JSON string
    
    # Business impact
    total_revenue_impact: Series[float] = pa.Field(nullable=True)
    total_investment_required: Series[float] = pa.Field(ge=0.0, nullable=True)
    expected_roi: Series[float] = pa.Field(nullable=True)
    
    # Recommendations
    top_priority_actions: Series[str] = pa.Field()  # JSON string
    implementation_roadmap: Series[str] = pa.Field()  # JSON string
    success_metrics: Series[str] = pa.Field()  # JSON string


class ClusterCoverageMatrixSchema(pa.DataFrameModel):
    """Schema for cluster coverage matrix from Step 31."""
    
    # Cluster identification
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    cluster_name: Series[str] = pa.Field(nullable=True)
    cluster_size: Series[int] = pa.Field(ge=0)
    
    # Coverage dimensions
    role_coverage_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    price_band_coverage_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    style_coverage_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    season_coverage_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    gender_coverage_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    size_coverage_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Overall coverage
    overall_coverage_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    coverage_grade: Series[str] = pa.Field()  # "A", "B", "C", "D", "F"
    
    # Gap analysis
    total_gaps: Series[int] = pa.Field(ge=0)
    critical_gaps: Series[int] = pa.Field(ge=0)
    gap_severity: Series[str] = pa.Field()  # "CRITICAL", "MODERATE", "OPTIMAL"
    
    # Recommendations
    primary_recommendation: Series[str] = pa.Field()
    secondary_recommendations: Series[str] = pa.Field()  # JSON string
    implementation_priority: Series[str] = pa.Field()  # "HIGH", "MEDIUM", "LOW"


class StoreLevelDisaggregationSchema(pa.DataFrameModel):
    """Schema for store-level disaggregation from Step 31."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    store_group: Series[str] = pa.Field()
    store_name: Series[str] = pa.Field(nullable=True)
    
    # Store attributes
    store_size: Series[str] = pa.Field(nullable=True)  # "Small", "Medium", "Large"
    location_type: Series[str] = pa.Field(nullable=True)  # "Urban", "Suburban", "Rural"
    customer_demographics: Series[str] = pa.Field(nullable=True)  # JSON string
    
    # Gap analysis by store
    total_gaps: Series[int] = pa.Field(ge=0)
    critical_gaps: Series[int] = pa.Field(ge=0)
    moderate_gaps: Series[int] = pa.Field(ge=0)
    gap_severity: Series[str] = pa.Field()
    
    # Store performance
    current_sales: Series[float] = pa.Field(ge=0.0)
    current_sellthrough_rate: Series[float] = pa.Field(ge=0.0, le=1.0)
    capacity_utilization: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Recommendations
    store_priority: Series[str] = pa.Field()  # "HIGH", "MEDIUM", "LOW"
    recommended_actions: Series[str] = pa.Field()  # JSON string
    expected_impact: Series[float] = pa.Field(nullable=True)


