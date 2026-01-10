import pandas as pd
#!/usr/bin/env python3
"""
Step 6 Clustering Validation Schemas

This module contains schemas for cluster analysis and validation from Step 6.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series
from typing import Optional


class ClusterProfilesSchema(pa.DataFrameModel):
    """Schema for cluster profiles output from Step 6."""
    
    # Cluster identification
    Cluster: Series[int] = pa.Field(ge=0, le=50)  # Cluster ID
    Size: Series[int] = pa.Field(ge=1)  # Number of stores in cluster
    
    # Store information
    Stores: Series[str] = pa.Field()  # Store codes (comma-separated)
    
    # Sales metrics
    Total_Sales: Series[float] = pa.Field()  # Can be negative for returns
    Avg_Sales_Per_Store: Series[float] = pa.Field()  # Can be negative
    Sales_Std: Series[float] = pa.Field(ge=0.0)  # Standard deviation is always non-negative
    
    # Optional fields that may or may not be present
    Top_SPUs: Optional[Series[str]] = pa.Field()  # Top SPUs (comma-separated)
    Top_Subcategories: Optional[Series[str]] = pa.Field()  # Top subcategories
    Top_Categories: Optional[Series[str]] = pa.Field()  # Top categories


class ClusteringResultsSchema(pa.DataFrameModel):
    """Schema for clustering results output from Step 6."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    
    # Cluster assignment
    Cluster: Series[int] = pa.Field(ge=0, le=50)


class PerClusterMetricsSchema(pa.DataFrameModel):
    """Schema for per-cluster metrics output from Step 6."""
    
    # Cluster identification
    Cluster: Series[int] = pa.Field(ge=0, le=50)
    
    # Clustering quality metrics
    Cohesion_Score: Series[float] = pa.Field()  # Can be negative for poor clusters
    Separation_Score: Series[float] = pa.Field()  # Can be negative
    Overall_Quality: Series[float] = pa.Field()  # Can be negative
    
    # Additional metrics
    Silhouette_Score: Optional[Series[float]] = pa.Field(ge=-1.0, le=1.0)
    Inertia: Optional[Series[float]] = pa.Field(ge=0.0)

