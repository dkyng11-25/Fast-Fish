import pandas as pd
#!/usr/bin/env python3
"""
Step 8 Imbalanced SPU Validation Schemas

This module contains schemas for imbalanced SPU rule validation from Step 8.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series


class ImbalancedSPURuleSchema(pa.DataFrameModel):
    """Schema for imbalanced SPU rule results from Step 8."""
    
    # Store and cluster identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    
    # Imbalance metrics
    imbalanced_spus_count: Series[float] = pa.Field(ge=0.0, nullable=True)
    avg_z_score: Series[float] = pa.Field(nullable=True)
    avg_abs_z_score: Series[float] = pa.Field(ge=0.0, nullable=True)
    total_adjustment_needed: Series[float] = pa.Field(nullable=True)
    
    # Allocation metrics
    over_allocated_count: Series[float] = pa.Field(ge=0.0, nullable=True)
    under_allocated_count: Series[float] = pa.Field(ge=0.0, nullable=True)
    rebalancing_recommended_count: Series[float] = pa.Field(ge=0.0, nullable=True)
    
    # Adjustment requirements
    total_quantity_adjustment_needed: Series[float] = pa.Field(nullable=True)
    total_rebalance_units: Series[float] = pa.Field(ge=0.0, nullable=True)
    total_rebalance_investment: Series[float] = pa.Field(nullable=True)
    
    # Rule information
    rule8_imbalanced_spu: Series[int] = pa.Field(ge=0, le=1)
    recommended_quantity_change: Series[float] = pa.Field(nullable=True)
    investment_required: Series[float] = pa.Field(nullable=True)
    business_rationale: Series[str] = pa.Field()
    approval_reason: Series[str] = pa.Field()
    fast_fish_compliant: Series[bool] = pa.Field()
    opportunity_type: Series[str] = pa.Field()
    rule8_description: Series[str] = pa.Field()
    rule8_threshold: Series[str] = pa.Field()
    rule8_analysis_level: Series[str] = pa.Field()

