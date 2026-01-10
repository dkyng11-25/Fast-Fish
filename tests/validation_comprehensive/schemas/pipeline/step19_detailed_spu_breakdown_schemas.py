import pandas as pd
#!/usr/bin/env python3
"""
Step 19 Detailed SPU Breakdown Validation Schemas

This module contains schemas for detailed SPU breakdown validation from Step 19.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series


class DetailedSPUBreakdownSchema(pa.DataFrameModel):
    """Schema for detailed SPU breakdown from Step 19."""
    
    # SPU identification
    spu_code: Series[str] = pa.Field()
    spu_name: Series[str] = pa.Field(nullable=True)
    sub_cate_name: Series[str] = pa.Field()
    category_name: Series[str] = pa.Field()
    
    # Store information
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    store_group: Series[str] = pa.Field()
    cluster: Series[int] = pa.Field(ge=0, le=50)
    
    # Current state
    current_quantity: Series[float] = pa.Field(ge=0.0)
    current_sales: Series[float] = pa.Field(ge=0.0)
    current_price: Series[float] = pa.Field(ge=0.0, nullable=True)
    
    # Performance metrics
    sell_through_rate: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    sales_velocity: Series[float] = pa.Field(ge=0.0, nullable=True)
    inventory_turnover: Series[float] = pa.Field(ge=0.0, nullable=True)
    
    # Historical comparison
    historical_quantity: Series[float] = pa.Field(ge=0.0, nullable=True)
    historical_sales: Series[float] = pa.Field(ge=0.0, nullable=True)
    quantity_change: Series[float] = pa.Field(nullable=True)
    sales_change: Series[float] = pa.Field(nullable=True)
    
    # Recommendations
    recommended_quantity: Series[float] = pa.Field(ge=0.0, nullable=True)
    quantity_adjustment: Series[float] = pa.Field(nullable=True)
    recommendation_confidence: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    
    # Business context
    market_demand: Series[str] = pa.Field(nullable=True)  # "high", "medium", "low"
    seasonal_factor: Series[float] = pa.Field(ge=0.0, le=2.0, nullable=True)
    competitive_position: Series[str] = pa.Field(nullable=True)  # "strong", "moderate", "weak"
    
    # Financial impact
    expected_revenue_impact: Series[float] = pa.Field(nullable=True)
    investment_required: Series[float] = pa.Field(ge=0.0, nullable=True)
    expected_roi: Series[float] = pa.Field(nullable=True)


class SPUPerformanceAnalysisSchema(pa.DataFrameModel):
    """Schema for SPU performance analysis."""
    
    spu_code: Series[str] = pa.Field()
    sub_cate_name: Series[str] = pa.Field()
    
    # Performance ranking
    performance_rank: Series[int] = pa.Field(ge=1, nullable=True)
    performance_percentile: Series[float] = pa.Field(ge=0.0, le=100.0, nullable=True)
    
    # Sales metrics
    total_sales: Series[float] = pa.Field(ge=0.0)
    avg_sales_per_store: Series[float] = pa.Field(ge=0.0)
    sales_growth_rate: Series[float] = pa.Field(nullable=True)
    
    # Store coverage
    stores_selling: Series[int] = pa.Field(ge=0)
    store_coverage_pct: Series[float] = pa.Field(ge=0.0, le=100.0, nullable=True)
    
    # Market position
    market_share: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    competitive_index: Series[float] = pa.Field(ge=0.0, le=10.0, nullable=True)
    
    # Trend analysis
    trend_direction: Series[str] = pa.Field(nullable=True)  # "up", "down", "stable"
    trend_strength: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    trend_confidence: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)


class StoreSPUAnalysisSchema(pa.DataFrameModel):
    """Schema for store-level SPU analysis."""
    
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    store_group: Series[str] = pa.Field()
    cluster: Series[int] = pa.Field(ge=0, le=50)
    
    # SPU portfolio metrics
    total_spus: Series[int] = pa.Field(ge=0)
    active_spus: Series[int] = pa.Field(ge=0)
    spu_diversity_index: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    
    # Performance metrics
    total_sales: Series[float] = pa.Field(ge=0.0)
    avg_sales_per_spu: Series[float] = pa.Field(ge=0.0, nullable=True)
    top_performing_spus: Series[int] = pa.Field(ge=0)
    
    # Optimization opportunities
    underperforming_spus: Series[int] = pa.Field(ge=0)
    optimization_potential: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    recommended_actions: Series[str] = pa.Field(nullable=True)
    
    # Store characteristics
    store_size_category: Series[str] = pa.Field(nullable=True)  # "small", "medium", "large"
    location_type: Series[str] = pa.Field(nullable=True)  # "urban", "suburban", "rural"
    customer_demographics: Series[str] = pa.Field(nullable=True)
