import pandas as pd
#!/usr/bin/env python3
"""
Step 13 Consolidated Rules Validation Schemas

This module contains schemas for consolidated SPU rules validation from Step 13.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series


class ConsolidatedSPURulesSchema(pa.DataFrameModel):
    """Schema for consolidated SPU rules from Step 13."""
    
    # Store and product identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    spu_code: Series[str] = pa.Field()
    sub_cate_name: Series[str] = pa.Field()
    
    # Recommendations
    recommended_quantity_change: Series[float] = pa.Field()
    rule_source: Series[str] = pa.Field()
    cluster: Series[int] = pa.Field(ge=0, le=50)
    
    # Current state
    current_quantity: Series[float] = pa.Field(ge=0.0, nullable=True)
    
    # Investment and pricing
    investment_required: Series[float] = pa.Field(nullable=True)
    unit_price: Series[float] = pa.Field(ge=0.0, nullable=True)
    
    # Business information
    business_rationale: Series[str] = pa.Field()
    opportunity_score: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)

