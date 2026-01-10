import pandas as pd
#!/usr/bin/env python3
"""
Matrix Validation Schemas

This module contains schemas for matrix preparation and validation.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera.pandas as pa
from pandera.typing import Series


class StoreMatrixSchema(pa.DataFrameModel):
    """Base schema for store-product matrices from Step 3."""

    # Store codes as index (validated separately)
    # Product columns are dynamic and validated by matrix type
    pass


class SubcategoryMatrixSchema(StoreMatrixSchema):
    """Schema for subcategory matrix from Step 3."""

    # All columns should be subcategory names (strings)
    # Values should be normalized (0.0 to 1.0) or non-negative sales amounts
    pass  # Dynamic validation handled in validators


class SPUMatrixSchema(StoreMatrixSchema):
    """Schema for SPU matrix from Step 3."""

    # All columns should be SPU codes (strings)
    # Values should be normalized (0.0 to 1.0) or non-negative sales amounts
    pass  # Dynamic validation handled in validators


class CategoryAggregatedMatrixSchema(StoreMatrixSchema):
    """Schema for category-aggregated matrix from Step 3."""

    # All columns should be category names (strings)
    # Values should be normalized (0.0 to 1.0) or non-negative sales amounts
    pass  # Dynamic validation handled in validators

