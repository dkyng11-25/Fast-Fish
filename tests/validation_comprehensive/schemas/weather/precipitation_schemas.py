import pandas as pd
#!/usr/bin/env python3
"""
Precipitation Validation Schemas

This module contains precipitation-related validation schemas.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera.pandas as pa
from pandera.typing import Series


class PrecipitationSchema(pa.DataFrameModel):
    """Schema for precipitation validation with comprehensive ranges."""
    
    precipitation: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=500.0  # Extreme daily precipitation (tropical storms)
    )
    
    rain: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=500.0
    )
    
    snowfall: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=200.0  # Extreme daily snowfall
    )
    
    # Additional precipitation metrics
    precipitation_probability: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=100.0  # Percentage
    )
    
    precipitation_intensity: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=50.0   # mm/hour
    )

