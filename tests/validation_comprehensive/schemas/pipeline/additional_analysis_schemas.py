import pandas as pd
#!/usr/bin/env python3
"""
Additional Analysis Validation Schemas

This module contains schemas for additional analysis and variety metrics.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series
from typing import Optional


class ClusterStyleVarietySchema(pa.DataFrameModel):
    """Schema for cluster style variety expectations from Step 6."""
    
    # Cluster identification
    Cluster: Series[int] = pa.Field(ge=0, le=50)
    
    # Style variety metrics
    Style_Variety_Score: Series[float] = pa.Field(ge=0.0, le=1.0)
    Expected_Styles_Count: Series[int] = pa.Field(ge=1)
    Current_Styles_Count: Series[int] = pa.Field(ge=0)
    Style_Gap: Series[int] = pa.Field()
    
    # Additional metrics
    Style_Diversity_Index: Optional[Series[float]] = pa.Field(ge=0.0, le=1.0)
    Top_Style_Categories: Optional[Series[str]] = pa.Field()


class ClusterSubcategoryVarietySchema(pa.DataFrameModel):
    """Schema for cluster subcategory variety expectations from Step 6."""
    
    # Cluster identification
    Cluster: Series[int] = pa.Field(ge=0, le=50)
    
    # Subcategory variety metrics
    Subcategory_Variety_Score: Series[float] = pa.Field(ge=0.0, le=1.0)
    Expected_Subcategories_Count: Series[int] = pa.Field(ge=1)
    Current_Subcategories_Count: Series[int] = pa.Field(ge=0)
    Subcategory_Gap: Series[int] = pa.Field()
    
    # Additional metrics
    Subcategory_Diversity_Index: Optional[Series[float]] = pa.Field(ge=0.0, le=1.0)
    Top_Subcategories: Optional[Series[str]] = pa.Field()


class TopPerformersByClusterSchema(pa.DataFrameModel):
    """Schema for top performers by cluster category from Step 11."""
    
    # Cluster and category identification
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    category: Series[str] = pa.Field()
    
    # Performance metrics
    top_performers_count: Series[int] = pa.Field(ge=0)
    avg_performance_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    total_sales: Series[float] = pa.Field()
    avg_sales_per_performer: Series[float] = pa.Field()
    
    # Additional information
    top_performer_spus: Optional[Series[str]] = pa.Field()
    performance_trend: Optional[Series[str]] = pa.Field()

