import pandas as pd
#!/usr/bin/env python3
"""
Seasonal Data Validation Schemas

This module contains schemas for seasonal data consolidation and analysis.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera.pandas as pa
from pandera.typing import Series


class SeasonalStoreProfilesSchema(pa.DataFrameModel):
    """Schema for seasonal store profiles output from Step 2B."""

    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)

    # Sales metrics
    total_3month_sales: Series[float] = pa.Field()  # Can be negative for returns
    avg_period_sales: Series[float] = pa.Field()    # Can be negative for returns
    sales_volatility: Series[float] = pa.Field(ge=0.0)  # Coefficient of variation
    sales_trend: Series[float] = pa.Field()  # Can be negative for declining trends

    # Category and SPU metrics
    avg_categories_per_period: Series[float] = pa.Field(ge=0.0)
    avg_spus_per_period: Series[float] = pa.Field(ge=0.0)
    category_stability: Series[float] = pa.Field()  # Can be negative for poor stability

    # Seasonal ratios
    early_season_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    late_season_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)

    # Performance classification
    performance_tier: Series[str] = pa.Field(isin=['High', 'Medium', 'Low'])


class SeasonalCategoryPatternsSchema(pa.DataFrameModel):
    """Schema for seasonal category patterns output from Step 2B."""

    # Product classification
    sub_cate_name: Series[str] = pa.Field(coerce=True)
    period: Series[str] = pa.Field(coerce=True)  # Period identifier like "202504B"

    # Sales metrics
    total_sales: Series[float] = pa.Field()  # Can be negative for returns
    avg_sales: Series[float] = pa.Field()    # Can be negative for returns
    transaction_count: Series[int] = pa.Field(ge=0)
    store_count: Series[int] = pa.Field(ge=1)


class SeasonalClusteringFeaturesSchema(pa.DataFrameModel):
    """Schema for seasonal clustering features output from Step 2B."""

    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)

    # Log-transformed sales features
    log_total_sales: Series[float] = pa.Field(ge=0.0)  # log1p transformation ensures non-negative
    log_avg_sales: Series[float] = pa.Field(ge=0.0)

    # Sales characteristics
    sales_volatility: Series[float] = pa.Field(ge=0.0)
    sales_trend: Series[float] = pa.Field()  # Can be negative for declining trends

    # Product diversity
    avg_categories_per_period: Series[float] = pa.Field(ge=0.0)
    avg_spus_per_period: Series[float] = pa.Field(ge=0.0)

    # Composite scores
    consistency_score: Series[float] = pa.Field()  # Can be negative for poor consistency
    growth_score: Series[float] = pa.Field()  # Can be negative for declining growth
    seasonal_balance: Series[float] = pa.Field(ge=0.0, le=1.0)

    # Seasonal ratios
    early_season_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    late_season_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)

