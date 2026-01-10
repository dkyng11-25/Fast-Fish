import pandas as pd
#!/usr/bin/env python3
"""
Step 10 and Step 12 Pipeline Schemas

This module defines Pandera schemas for Step 10 (SPU Assortment Optimization) 
and Step 12 (Sales Performance Rule) validation.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series


class SPUAssortmentOptimizationSchema(pa.DataFrameModel):
    """Schema for Step 10: SPU Assortment Optimization outputs."""
    
    str_code: Series[str] = pa.Field(nullable=False, description="Store code identifier")
    spu_code: Series[str] = pa.Field(nullable=False, description="SPU code identifier")
    cluster_id: Series[int] = pa.Field(nullable=False, description="Cluster identifier")
    current_allocation: Series[float] = pa.Field(nullable=True, description="Current allocation amount")
    optimal_allocation: Series[float] = pa.Field(nullable=True, description="Optimal allocation amount")
    allocation_gap: Series[float] = pa.Field(nullable=True, description="Gap between current and optimal allocation")
    optimization_priority: Series[str] = pa.Field(nullable=True, description="Optimization priority level")
    expected_impact: Series[float] = pa.Field(nullable=True, description="Expected impact percentage")
    implementation_cost: Series[float] = pa.Field(nullable=True, description="Implementation cost")
    current_performance: Series[float] = pa.Field(nullable=True, description="Current performance score")
    target_performance: Series[float] = pa.Field(nullable=True, description="Target performance score")


class SalesPerformanceRuleSchema(pa.DataFrameModel):
    """Schema for Step 12: Sales Performance Rule outputs."""
    
    str_code: Series[str] = pa.Field(nullable=False, description="Store code identifier")
    spu_code: Series[str] = pa.Field(nullable=False, description="SPU code identifier")
    cluster_id: Series[int] = pa.Field(nullable=False, description="Cluster identifier")
    current_sales: Series[float] = pa.Field(nullable=True, description="Current sales amount")
    top_performer_sales: Series[float] = pa.Field(nullable=True, description="Top performer sales amount")
    performance_gap: Series[float] = pa.Field(nullable=True, description="Performance gap amount")
    performance_tier: Series[str] = pa.Field(nullable=True, description="Performance tier classification")
    sales_velocity: Series[float] = pa.Field(nullable=True, description="Sales velocity metric")
    market_share: Series[float] = pa.Field(nullable=True, description="Market share percentage")
    recommended_action: Series[str] = pa.Field(nullable=True, description="Recommended action to improve performance")
    priority_score: Series[float] = pa.Field(nullable=True, description="Priority score for action")
    expected_improvement: Series[float] = pa.Field(nullable=True, description="Expected improvement percentage")