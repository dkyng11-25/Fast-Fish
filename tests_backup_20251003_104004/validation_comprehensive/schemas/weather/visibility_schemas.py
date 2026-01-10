import pandas as pd
#!/usr/bin/env python3
"""
Visibility Validation Schemas

This module contains visibility validation schemas.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera.pandas as pa
from pandera.typing import Series


class VisibilitySchema(pa.DataFrameModel):
    """Schema for visibility validation."""
    
    visibility: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=50.0   # km
    )
    
    visibility_min: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=50.0
    )
    
    visibility_max: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=50.0
    )

