import pandas as pd
#!/usr/bin/env python3
"""
Time-related Validation Schemas

This module contains validation schemas for time-related data including
time series, periods, and date ranges.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera.pandas as pa
from pandera.typing import Series


class TimeSeriesSchema(pa.DataFrameModel):
    """Schema for time series data validation."""
    
    time: Series[str] = pa.Field(nullable=True)
    yyyy: Series[int] = pa.Field(ge=2010, le=2040)  # Year range: 2010-2040
    mm: Series[int] = pa.Field(nullable=True, ge=1, le=12)  # Month: 1-12


class PeriodSchema(pa.DataFrameModel):
    """Schema for period validation with enhanced constraints."""
    
    yyyy: Series[int] = pa.Field(ge=2010, le=2040)  # Year range: 2010-2040
    mm: Series[int] = pa.Field(ge=1, le=12)  # Month: 1-12
    mm_type: Series[str] = pa.Field(nullable=True, isin=[
        '1A', '1B', '2A', '2B', '3A', '3B', '4A', '4B', 
        '5A', '5B', '6A', '6B', '7A', '7B', '8A', '8B',
        '9A', '9B', '10A', '10B', '11A', '11B', '12A', '12B'
    ])


class YearSchema(pa.DataFrameModel):
    """Schema for year validation."""
    
    year: Series[int] = pa.Field(ge=2010, le=2040, description="Year in range 2010-2040")


class MonthSchema(pa.DataFrameModel):
    """Schema for month validation."""
    
    month: Series[int] = pa.Field(ge=1, le=12, description="Month in range 1-12")


class DateRangeSchema(pa.DataFrameModel):
    """Schema for date range validation."""
    
    start_date: Series[str] = pa.Field(nullable=True)
    end_date: Series[str] = pa.Field(nullable=True)
    period_days: Series[int] = pa.Field(nullable=True, ge=1, le=31)  # Reasonable period length


__all__ = [
    'TimeSeriesSchema',
    'PeriodSchema', 
    'YearSchema',
    'MonthSchema',
    'DateRangeSchema'
]

