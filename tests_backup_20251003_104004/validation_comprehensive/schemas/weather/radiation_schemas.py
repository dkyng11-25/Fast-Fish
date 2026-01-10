import pandas as pd
#!/usr/bin/env python3
"""
Radiation Validation Schemas

This module contains solar radiation validation schemas.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera.pandas as pa
from pandera.typing import Series


class RadiationSchema(pa.DataFrameModel):
    """Schema for solar radiation metrics validation."""
    
    direct_radiation: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=1500.0  # Maximum solar radiation
    )
    
    diffuse_radiation: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=500.0
    )
    
    direct_normal_irradiance: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=1500.0
    )
    
    terrestrial_radiation: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=1500.0  # Increased based on actual data observations
    )
    
    shortwave_radiation: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=1500.0
    )
    
    et0_fao_evapotranspiration: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=20.0   # mm/day
    )

