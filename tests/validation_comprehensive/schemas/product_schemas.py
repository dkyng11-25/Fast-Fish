import pandas as pd
#!/usr/bin/env python3
"""
Product and Sales Validation Schemas

This module contains validation schemas for product data, sales data,
and store configuration information.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera.pandas as pa
from pandera.typing import Series
from .common_schemas import (
    StoreCodeSchema, SalesAmountSchema, QuantitySchema, 
    PriceSchema, CountSchema, CategoricalSchema
)
from .time_schemas import PeriodSchema


class ProductClassificationSchema(pa.DataFrameModel):
    """Schema for product classification validation."""
    
    # Product classification
    big_class_name: Series[str] = pa.Field(nullable=True)
    sub_cate_name: Series[str] = pa.Field(nullable=True)
    cate_name: Series[str] = pa.Field(nullable=True)
    spu_code: Series[str] = pa.Field(nullable=True)
    
    # Display and location
    display_location_name: Series[str] = pa.Field(nullable=True)
    ext_sty_detail: Series[str] = pa.Field(nullable=True)


class StoreConfigSchema(pa.DataFrameModel):
    """Schema for store configuration data from API."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    str_name: Series[str] = pa.Field(nullable=True)
    
    # Product classification
    big_class_name: Series[str] = pa.Field(nullable=True)
    sub_cate_name: Series[str] = pa.Field(nullable=True)
    display_location_name: Series[str] = pa.Field(nullable=True)
    ext_sty_detail: Series[str] = pa.Field(nullable=True)
    
    # Time and categorical data
    yyyy: Series[int] = pa.Field(ge=2010, le=2040)
    mm: Series[int] = pa.Field(nullable=True, ge=1, le=12)
    mm_type: Series[str] = pa.Field(nullable=True, isin=[
        '1A', '1B', '2A', '2B', '3A', '3B', '4A', '4B', 
        '5A', '5B', '6A', '6B', '7A', '7B', '8A', '8B',
        '9A', '9B', '10A', '10B', '11A', '11B', '12A', '12B'
    ])
    season_name: Series[str] = pa.Field(nullable=True, isin=['春', '夏', '秋', '冬', '四季'])
    sex_name: Series[str] = pa.Field(nullable=True, isin=['男', '女', '中'])
    
    # Sales and style data
    sal_amt: Series[float] = pa.Field(nullable=True)
    sty_sal_amt: Series[str] = pa.Field(nullable=True)  # JSON string format
    
    # Count data
    ext_sty_cnt_avg: Series[float] = pa.Field(nullable=True, ge=0)
    ext_sty_cnt_end: Series[float] = pa.Field(nullable=True, ge=0)
    target_sty_cnt_avg: Series[float] = pa.Field(nullable=True, ge=0)
    target_sty_cnt_end: Series[float] = pa.Field(nullable=True, ge=0)


class CategorySalesSchema(pa.DataFrameModel):
    """Schema for processed category sales data."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    str_name: Series[str] = pa.Field(nullable=True)
    
    # Product classification
    cate_name: Series[str] = pa.Field(nullable=True)
    sub_cate_name: Series[str] = pa.Field(nullable=True)
    
    # Sales data
    sal_amt: Series[float] = pa.Field(nullable=True)
    store_unit_price: Series[float] = pa.Field(nullable=True, ge=0)  # Price always positive
    estimated_quantity: Series[float] = pa.Field(nullable=True, ge=-50, le=1000)  # Allow returns but reasonable range


class SPUSalesSchema(pa.DataFrameModel):
    """Schema for detailed SPU sales data."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    str_name: Series[str] = pa.Field(nullable=True)
    
    # Product classification
    cate_name: Series[str] = pa.Field(nullable=True)
    sub_cate_name: Series[str] = pa.Field(nullable=True)
    spu_code: Series[str] = pa.Field(nullable=True)
    
    # Sales data
    spu_sales_amt: Series[float] = pa.Field(nullable=True)
    quantity: Series[float] = pa.Field(nullable=True, ge=-50, le=450)  # Allow returns but reasonable range
    unit_price: Series[float] = pa.Field(nullable=True, ge=0)  # Price always positive
    investment_per_unit: Series[float] = pa.Field(nullable=True, ge=0)  # Investment always positive


class SalesSummarySchema(pa.DataFrameModel):
    """Schema for sales summary data with enhanced validation."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    
    # Sales metrics
    base_sal_qty: Series[float] = pa.Field(nullable=True, ge=0.0)
    fashion_sal_qty: Series[float] = pa.Field(nullable=True, ge=0.0)
    base_sal_amt: Series[float] = pa.Field(nullable=True, ge=0.0)
    fashion_sal_amt: Series[float] = pa.Field(nullable=True, ge=0.0)
    
    # Average sales amount
    sal_amt_avg: Series[float] = pa.Field(nullable=True, ge=0.0)
    
    # Period information
    yyyy: Series[int] = pa.Field(ge=2010, le=2040)
    mm: Series[int] = pa.Field(ge=1, le=12)
    mm_type: Series[str] = pa.Field(nullable=True, isin=[
        '1A', '1B', '2A', '2B', '3A', '3B', '4A', '4B', 
        '5A', '5B', '6A', '6B', '7A', '7B', '8A', '8B',
        '9A', '9B', '10A', '10B', '11A', '11B', '12A', '12B'
    ])


class InventorySchema(pa.DataFrameModel):
    """Schema for inventory data validation."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    
    # Inventory counts
    ext_sty_cnt_avg: Series[float] = pa.Field(nullable=True, ge=0)
    ext_sty_cnt_end: Series[float] = pa.Field(nullable=True, ge=0)
    target_sty_cnt_avg: Series[float] = pa.Field(nullable=True, ge=0)
    target_sty_cnt_end: Series[float] = pa.Field(nullable=True, ge=0)
    
    # Additional inventory metrics
    inventory_turnover: Series[float] = pa.Field(nullable=True, ge=0.0, le=100.0)
    stock_ratio: Series[float] = pa.Field(nullable=True, ge=0.0, le=10.0)
    out_of_stock_rate: Series[float] = pa.Field(nullable=True, ge=0.0, le=100.0)

