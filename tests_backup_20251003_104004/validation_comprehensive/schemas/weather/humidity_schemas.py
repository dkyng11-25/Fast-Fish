import pandas as pd
#!/usr/bin/env python3
"""
Humidity Validation Schemas

This module contains humidity-related validation schemas.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera.pandas as pa
from pandera.typing import Series


class HumiditySchema(pa.DataFrameModel):
    """Schema for humidity validation."""
    
    relative_humidity_2m: Series[int] = pa.Field(
        nullable=True,
        ge=0,
        le=100    # Percentage
    )
    
    # Additional humidity metrics
    absolute_humidity: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=50.0   # g/m³
    )
    
    dew_point: Series[float] = pa.Field(
        nullable=True,
        ge=-50.0,
        le=40.0   # Celsius
    )

