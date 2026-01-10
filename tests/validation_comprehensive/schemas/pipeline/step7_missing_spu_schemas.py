import pandas as pd
#!/usr/bin/env python3
"""
Step 7 Missing SPU Validation Schemas

This module contains schemas for missing SPU rule validation from Step 7.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series


class MissingSPURuleSchema(pa.DataFrameModel):
    """Schema for missing SPU rule results from Step 7."""
    
    # Store and cluster identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    
    # Missing SPU metrics
    missing_spus_count: Series[float] = pa.Field(ge=0.0)
    total_opportunity_value: Series[float] = pa.Field(ge=0.0)
    total_quantity_needed: Series[float] = pa.Field(ge=0.0)
    total_investment_required: Series[float] = pa.Field(ge=0.0)
    
    # Performance metrics
    avg_sellthrough_improvement: Series[float] = pa.Field()
    avg_predicted_sellthrough: Series[float] = pa.Field(ge=0.0, le=100.0)
    fastfish_approved_count: Series[float] = pa.Field(ge=0.0)
    
    # Rule information
    rule7_missing_spu: Series[int] = pa.Field(ge=0, le=1)
    rule7_description: Series[str] = pa.Field()
    rule7_threshold: Series[str] = pa.Field()
    rule7_analysis_level: Series[str] = pa.Field()
    rule7_sellthrough_validation: Series[str] = pa.Field()
    rule7_fastfish_compliant: Series[bool] = pa.Field()

