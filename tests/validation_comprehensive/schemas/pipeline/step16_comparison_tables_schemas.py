import pandas as pd
#!/usr/bin/env python3
"""
Step 16 Comparison Tables Validation Schemas

This module contains schemas for comparison tables validation from Step 16.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series


class ComparisonTableSchema(pa.DataFrameModel):
    """Schema for comparison tables from Step 16."""
    
    # Store group information
    store_group: Series[str] = pa.Field()
    store_count: Series[int] = pa.Field(ge=1)
    
    # Category information
    sub_cate_name: Series[str] = pa.Field()
    category_name: Series[str] = pa.Field()
    
    # Current period metrics
    current_spu_count: Series[int] = pa.Field(ge=0)
    current_sales: Series[float] = pa.Field(ge=0.0)
    current_quantity: Series[float] = pa.Field(ge=0.0)
    current_avg_price: Series[float] = pa.Field(ge=0.0, nullable=True)
    
    # Historical period metrics
    historical_spu_count: Series[int] = pa.Field(ge=0)
    historical_sales: Series[float] = pa.Field(ge=0.0)
    historical_quantity: Series[float] = pa.Field(ge=0.0)
    historical_avg_price: Series[float] = pa.Field(ge=0.0, nullable=True)
    
    # Change metrics
    spu_count_change: Series[int] = pa.Field()
    spu_count_change_pct: Series[float] = pa.Field(nullable=True)
    sales_change: Series[float] = pa.Field()
    sales_change_pct: Series[float] = pa.Field(nullable=True)
    quantity_change: Series[float] = pa.Field()
    quantity_change_pct: Series[float] = pa.Field(nullable=True)
    
    # Performance indicators
    performance_trend: Series[str] = pa.Field()  # "improving", "declining", "stable"
    recommendation_priority: Series[str] = pa.Field()  # "high", "medium", "low"


class StoreGroupComparisonSchema(pa.DataFrameModel):
    """Schema for store group comparison data."""
    
    store_group: Series[str] = pa.Field()
    store_count: Series[int] = pa.Field(ge=1)
    
    # Total metrics
    total_current_sales: Series[float] = pa.Field(ge=0.0)
    total_historical_sales: Series[float] = pa.Field(ge=0.0)
    total_sales_change: Series[float] = pa.Field()
    total_sales_change_pct: Series[float] = pa.Field(nullable=True)
    
    # Category diversity
    current_category_count: Series[int] = pa.Field(ge=0)
    historical_category_count: Series[int] = pa.Field(ge=0)
    category_diversity_change: Series[int] = pa.Field()
    
    # Performance ranking
    current_performance_rank: Series[int] = pa.Field(ge=1, nullable=True)
    historical_performance_rank: Series[int] = pa.Field(ge=1, nullable=True)
    rank_change: Series[int] = pa.Field(nullable=True)


class CategoryComparisonSchema(pa.DataFrameModel):
    """Schema for category comparison data."""
    
    sub_cate_name: Series[str] = pa.Field()
    category_name: Series[str] = pa.Field()
    
    # Store coverage
    stores_selling_current: Series[int] = pa.Field(ge=0)
    stores_selling_historical: Series[int] = pa.Field(ge=0)
    store_coverage_change: Series[int] = pa.Field()
    store_coverage_change_pct: Series[float] = pa.Field(nullable=True)
    
    # Performance metrics
    avg_sales_per_store_current: Series[float] = pa.Field(ge=0.0)
    avg_sales_per_store_historical: Series[float] = pa.Field(ge=0.0)
    avg_sales_per_store_change: Series[float] = pa.Field()
    
    # Market share
    current_market_share: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    historical_market_share: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    market_share_change: Series[float] = pa.Field(nullable=True)
