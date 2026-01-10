import pandas as pd
#!/usr/bin/env python3
"""
Step 11 Missed Sales Validation Schemas

This module contains schemas for missed sales opportunity validation from Step 11.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series


class MissedSalesOpportunitySchema(pa.DataFrameModel):
    """Schema for missed sales opportunity results from Step 11."""
    
    # Store and cluster identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    
    # Opportunity metrics
    rule11_missed_sales_opportunity: Series[int] = pa.Field(ge=0, le=1)
    rule11_missing_top_performers_count: Series[int] = pa.Field(ge=0)
    rule11_avg_opportunity_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    rule11_potential_sales_increase: Series[float] = pa.Field(ge=0.0)
    
    # Recommendations
    rule11_total_recommended_period_sales: Series[float] = pa.Field(ge=0.0)
    rule11_total_recommended_period_qty: Series[float] = pa.Field(ge=0.0)
    investment_required: Series[float] = pa.Field(ge=0.0)
    recommended_quantity_change: Series[float] = pa.Field()
    
    # Business information
    business_rationale: Series[str] = pa.Field()
    approval_reason: Series[str] = pa.Field()
    fast_fish_compliant: Series[bool] = pa.Field()
    opportunity_type: Series[str] = pa.Field()

