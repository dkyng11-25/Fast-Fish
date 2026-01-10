import pandas as pd
#!/usr/bin/env python3
"""
Pressure Validation Schemas

This module contains atmospheric pressure validation schemas.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera.pandas as pa
from pandera.typing import Series


class PressureSchema(pa.DataFrameModel):
    """Schema for atmospheric pressure validation."""
    
    pressure_msl: Series[float] = pa.Field(
        nullable=True,
        ge=800.0,  # Extreme low pressure (hurricanes)
        le=1100.0  # Extreme high pressure (anticyclones)
    )
    
    # Additional pressure metrics
    pressure_surface: Series[float] = pa.Field(
        nullable=True,
        ge=800.0,
        le=1100.0
    )
    
    pressure_tendency: Series[float] = pa.Field(
        nullable=True,
        ge=-10.0,  # Rapid pressure drop
        le=10.0    # Rapid pressure rise
    )

