import pandas as pd
#!/usr/bin/env python3
"""
Wind Validation Schemas

This module contains wind-related validation schemas.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera.pandas as pa
from pandera.typing import Series


class WindSchema(pa.DataFrameModel):
    """Schema for wind validation with comprehensive ranges."""
    
    wind_speed_10m: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=100.0  # Hurricane force winds
    )
    
    wind_direction_10m: Series[int] = pa.Field(
        nullable=True,
        ge=0,
        le=360    # Degrees
    )
    
    # Additional wind metrics
    wind_gust: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=150.0  # Extreme wind gusts
    )
    
    wind_speed_avg: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=80.0
    )

