import pandas as pd
#!/usr/bin/env python3
"""
Common Validation Schemas

This module contains reusable validation schemas that are used across multiple pipeline steps.
These schemas define common data patterns and constraints.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera.pandas as pa
from pandera.typing import Series


class StoreCodeSchema(pa.DataFrameModel):
    """Schema for store code validation - used across multiple steps."""
    
    str_code: Series[int] = pa.Field(ge=10000, le=99999)


class GeographicSchema(pa.DataFrameModel):
    """Schema for geographic coordinate validation."""
    
    latitude: Series[float] = pa.Field(nullable=True, ge=-90, le=90)  # Earth latitude bounds
    longitude: Series[float] = pa.Field(nullable=True, ge=-180, le=180)  # Earth longitude bounds
    altitude: Series[float] = pa.Field(nullable=True, ge=0, le=9000)  # Altitude: 0 to 9000m (Mount Everest)


class SalesAmountSchema(pa.DataFrameModel):
    """Schema for sales amount validation - allows negative values for returns/adjustments."""
    
    sal_amt: Series[float] = pa.Field(nullable=True)
    spu_sales_amt: Series[float] = pa.Field(nullable=True)
    sty_sal_amt: Series[str] = pa.Field(nullable=True)  # JSON string format


class QuantitySchema(pa.DataFrameModel):
    """Schema for quantity validation - allows returns but with reasonable bounds."""
    
    quantity: Series[float] = pa.Field(nullable=True, ge=-50, le=450)  # Allow returns but reasonable range
    estimated_quantity: Series[float] = pa.Field(nullable=True, ge=-50, le=1000)  # Broader range for aggregated data


class PriceSchema(pa.DataFrameModel):
    """Schema for price validation - prices are always positive."""
    
    store_unit_price: Series[float] = pa.Field(nullable=True, ge=0)  # Price always positive
    unit_price: Series[float] = pa.Field(nullable=True, ge=0)  # Price always positive
    investment_per_unit: Series[float] = pa.Field(nullable=True, ge=0)  # Investment always positive


class CountSchema(pa.DataFrameModel):
    """Schema for count validation - counts are non-negative."""
    
    ext_sty_cnt_avg: Series[float] = pa.Field(nullable=True, ge=0)
    ext_sty_cnt_end: Series[float] = pa.Field(nullable=True, ge=0)
    target_sty_cnt_avg: Series[float] = pa.Field(nullable=True, ge=0)
    target_sty_cnt_end: Series[float] = pa.Field(nullable=True, ge=0)


class CategoricalSchema(pa.DataFrameModel):
    """Schema for categorical field validation."""
    
    # Chinese seasons
    season_name: Series[str] = pa.Field(nullable=True, isin=['春', '夏', '秋', '冬', '四季'])
    
    # Chinese gender categories  
    sex_name: Series[str] = pa.Field(nullable=True, isin=['男', '女', '中'])
    
    # Half-month periods (1A, 1B, 2A, 2B, etc.)
    mm_type: Series[str] = pa.Field(nullable=True, isin=[
        '1A', '1B', '2A', '2B', '3A', '3B', '4A', '4B', 
        '5A', '5B', '6A', '6B', '7A', '7B', '8A', '8B',
        '9A', '9B', '10A', '10B', '11A', '11B', '12A', '12B'
    ])


class StandardRuleFieldsSchema(pa.DataFrameModel):
    """Schema for standard fields that appear across all rule steps."""
    
    # Core identifiers
    str_code: Series[str] = pa.Field(description="Store code identifier")
    cluster_id: Series[str] = pa.Field(description="Cluster identifier")
    
    # Rule flags and descriptions
    rule_flag: Series[str] = pa.Field(nullable=True, description="Rule flag")
    rule_description: Series[str] = pa.Field(nullable=True, description="Rule description")
    rule_threshold: Series[str] = pa.Field(nullable=True, description="Rule threshold")
    rule_analysis_level: Series[str] = pa.Field(nullable=True, description="Analysis level")
    
    # Investment and quantity
    investment_required: Series[float] = pa.Field(nullable=True, ge=0, description="Investment required")
    recommended_quantity_change: Series[float] = pa.Field(nullable=True, description="Recommended quantity change")
    
    # Business logic
    business_rationale: Series[str] = pa.Field(nullable=True, description="Business rationale")
    approval_reason: Series[str] = pa.Field(nullable=True, description="Approval reason")
    fast_fish_compliant: Series[str] = pa.Field(nullable=True, description="Fast Fish compliance")
    opportunity_type: Series[str] = pa.Field(nullable=True, description="Type of opportunity")
    
    # Period information
    period_label: Series[str] = pa.Field(nullable=True, description="Period label")
    target_yyyymm: Series[str] = pa.Field(nullable=True, description="Target year-month")
    target_period: Series[str] = pa.Field(nullable=True, description="Target period")
