import pandas as pd
#!/usr/bin/env python3
"""
Step 15 Historical Baseline Validation Schemas

This module contains schemas for historical baseline validation from Step 15.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series


class HistoricalBaselineSchema(pa.DataFrameModel):
    """Schema for historical baseline data from Step 15."""
    
    # Time information
    baseline_year: Series[int] = pa.Field(ge=2010, le=2040)
    baseline_month: Series[int] = pa.Field(ge=1, le=12)
    baseline_period: Series[str] = pa.Field()
    
    # Store information
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    store_group: Series[str] = pa.Field()
    
    # Category information
    sub_cate_name: Series[str] = pa.Field()
    category_name: Series[str] = pa.Field()
    
    # Historical metrics
    historical_spu_count: Series[int] = pa.Field(ge=0)
    historical_sales: Series[float] = pa.Field(ge=0.0)
    historical_quantity: Series[float] = pa.Field(ge=0.0)
    
    # Performance metrics
    historical_sell_through_rate: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    historical_avg_price: Series[float] = pa.Field(ge=0.0, nullable=True)
    
    # Comparison metrics
    yoy_sales_change: Series[float] = pa.Field(nullable=True)
    yoy_quantity_change: Series[float] = pa.Field(nullable=True)
    yoy_spu_count_change: Series[float] = pa.Field(nullable=True)


class HistoricalSPUCountSchema(pa.DataFrameModel):
    """Schema for historical SPU counts by store group and category."""
    
    store_group: Series[str] = pa.Field()
    sub_cate_name: Series[str] = pa.Field()
    historical_spu_count: Series[int] = pa.Field(ge=0)
    current_spu_count: Series[int] = pa.Field(ge=0)
    spu_count_change: Series[int] = pa.Field()
    spu_count_change_pct: Series[float] = pa.Field(nullable=True)


class HistoricalSalesPerformanceSchema(pa.DataFrameModel):
    """Schema for historical sales performance metrics."""
    
    store_group: Series[str] = pa.Field()
    sub_cate_name: Series[str] = pa.Field()
    historical_total_sales: Series[float] = pa.Field(ge=0.0)
    current_total_sales: Series[float] = pa.Field(ge=0.0)
    sales_change: Series[float] = pa.Field()
    sales_change_pct: Series[float] = pa.Field(nullable=True)
    
    historical_avg_sales_per_spu: Series[float] = pa.Field(ge=0.0)
    current_avg_sales_per_spu: Series[float] = pa.Field(ge=0.0)
    avg_sales_change: Series[float] = pa.Field(nullable=True)
