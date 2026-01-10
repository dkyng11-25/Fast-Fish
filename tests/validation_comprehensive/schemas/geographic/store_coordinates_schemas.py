import pandas as pd
#!/usr/bin/env python3
"""
Store Coordinates Validation Schemas

This module contains schemas for store coordinates and related geographic data.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera.pandas as pa
from pandera.typing import Series


class StoreCoordinatesSchema(pa.DataFrameModel):
    """Schema for store coordinates output from Step 2."""

    # Store identification
    str_code: Series[str] = pa.Field(coerce=True)  # Will be converted to string

    # Geographic coordinates
    longitude: Series[float] = pa.Field(ge=-180.0, le=180.0)  # Valid longitude range
    latitude: Series[float] = pa.Field(ge=-90.0, le=90.0)    # Valid latitude range


class SPUStoreMappingSchema(pa.DataFrameModel):
    """Schema for SPU-store mapping output from Step 2."""

    # Product identification
    spu_code: Series[str] = pa.Field(coerce=True)

    # Store identification
    str_code: Series[str] = pa.Field(coerce=True)
    str_name: Series[str] = pa.Field(nullable=True)

    # Product classification
    cate_name: Series[str] = pa.Field(nullable=True)
    sub_cate_name: Series[str] = pa.Field(nullable=True)

    # Sales amount
    spu_sales_amt: Series[float] = pa.Field()  # Can be negative for returns


class SPUMetadataSchema(pa.DataFrameModel):
    """Schema for SPU metadata output from Step 2."""

    # Product identification
    spu_code: Series[str] = pa.Field(coerce=True)

    # Product classification
    cate_name: Series[str] = pa.Field(nullable=True)
    sub_cate_name: Series[str] = pa.Field(nullable=True)

    # Store statistics
    store_count: Series[int] = pa.Field(ge=1)  # At least 1 store

    # Sales statistics
    total_sales: Series[float] = pa.Field()  # Can be negative for returns
    avg_sales: Series[float] = pa.Field()    # Can be negative for returns
    std_sales: Series[float] = pa.Field(ge=0.0)    # Standard deviation is always non-negative
    period_count: Series[int] = pa.Field(ge=1)     # At least 1 period

