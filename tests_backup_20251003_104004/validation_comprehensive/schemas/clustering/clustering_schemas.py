import pandas as pd
#!/usr/bin/env python3
"""
Clustering Validation Schemas

This module contains schemas for cluster analysis and validation.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera.pandas as pa
from pandera.typing import Series


class ClusteringResultsSchema(pa.DataFrameModel):
    """Schema for clustering results output from Step 6."""

    # Store identification
    str_code: Series[str] = pa.Field(coerce=True)

    # Cluster assignment
    Cluster: Series[int] = pa.Field(ge=0)  # Cluster IDs start from 0


class ClusterProfilesSchema(pa.DataFrameModel):
    """Schema for cluster profiles output from Step 6."""

    # Cluster identification
    Cluster: Series[int] = pa.Field(ge=0)

    # Cluster characteristics
    Size: Series[int] = pa.Field(ge=1)  # At least 1 store per cluster
    Stores: Series[str] = pa.Field(nullable=True)  # Comma-separated store codes

    # Top features (content varies by matrix type - not all may be present)
    Top_Subcategories: Series[str] = pa.Field(nullable=True)
    Top_SPUs: Series[str] = pa.Field(nullable=True)
    Top_Categories: Series[str] = pa.Field(nullable=True)

    # Sales statistics
    Total_Sales: Series[float] = pa.Field()  # Can be negative for returns
    Avg_Sales_Per_Store: Series[float] = pa.Field()  # Can be negative for returns
    Sales_Std: Series[float] = pa.Field(ge=0.0)  # Standard deviation is always non-negative


class PerClusterMetricsSchema(pa.DataFrameModel):
    """Schema for per-cluster metrics output from Step 6."""

    # Cluster identification
    Cluster: Series[int] = pa.Field(ge=0)

    # Cluster size
    Size: Series[int] = pa.Field(ge=1)

    # Quality metrics
    Avg_Silhouette: Series[float] = pa.Field(ge=-1.0, le=1.0)  # Silhouette score range
    Avg_Distance_to_Center: Series[float] = pa.Field(ge=0.0)
    Std_Distance_to_Center: Series[float] = pa.Field(ge=0.0)
    Min_Distance_to_Other_Centers: Series[float] = pa.Field(ge=0.0)

    # Density and quality scores
    Density: Series[float] = pa.Field(ge=0.0)
    Cohesion_Score: Series[float] = pa.Field()  # Can be negative for poor cohesion
    Separation_Score: Series[float] = pa.Field()  # Can be negative for poor separation
    Overall_Quality: Series[float] = pa.Field()  # Can be negative for poor quality

