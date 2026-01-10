import pandas as pd
#!/usr/bin/env python3
"""
Step 22 Store Attribute Enrichment Validation Schemas

This module contains schemas for store attribute enrichment validation from Step 22.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series


class StoreAttributeEnrichmentSchema(pa.DataFrameModel):
    """Schema for store attribute enrichment from Step 22."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    store_name: Series[str] = pa.Field(nullable=True)
    store_group: Series[str] = pa.Field()
    
    # Geographic attributes
    latitude: Series[float] = pa.Field(ge=-90.0, le=90.0, nullable=True)
    longitude: Series[float] = pa.Field(ge=-180.0, le=180.0, nullable=True)
    city: Series[str] = pa.Field(nullable=True)
    province: Series[str] = pa.Field(nullable=True)
    region: Series[str] = pa.Field(nullable=True)
    
    # Demographic attributes
    population_density: Series[str] = pa.Field(nullable=True)  # "urban", "suburban", "rural"
    income_level: Series[str] = pa.Field(nullable=True)  # "low", "medium", "high"
    age_demographics: Series[str] = pa.Field(nullable=True)  # "young", "middle_aged", "senior", "mixed"
    
    # Store characteristics
    store_size: Series[str] = pa.Field(nullable=True)  # "small", "medium", "large"
    store_type: Series[str] = pa.Field(nullable=True)  # "flagship", "standard", "outlet"
    location_type: Series[str] = pa.Field(nullable=True)  # "mall", "street", "airport", "station"
    
    # Business attributes
    opening_date: Series[str] = pa.Field(nullable=True)
    store_age_years: Series[float] = pa.Field(ge=0.0, nullable=True)
    renovation_date: Series[str] = pa.Field(nullable=True)
    
    # Performance attributes
    performance_tier: Series[str] = pa.Field(nullable=True)  # "A", "B", "C", "D"
    sales_volume_tier: Series[str] = pa.Field(nullable=True)  # "high", "medium", "low"
    customer_traffic_level: Series[str] = pa.Field(nullable=True)  # "high", "medium", "low"
    
    # Competitive attributes
    competitor_density: Series[str] = pa.Field(nullable=True)  # "high", "medium", "low"
    market_saturation: Series[str] = pa.Field(nullable=True)  # "high", "medium", "low"
    competitive_intensity: Series[float] = pa.Field(ge=0.0, le=10.0, nullable=True)
    
    # Enrichment metadata
    enrichment_date: Series[str] = pa.Field()
    enrichment_source: Series[str] = pa.Field()
    enrichment_confidence: Series[float] = pa.Field(ge=0.0, le=1.0)
    data_quality_score: Series[float] = pa.Field(ge=0.0, le=1.0)


class StoreDemographicAnalysisSchema(pa.DataFrameModel):
    """Schema for store demographic analysis."""
    
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    store_group: Series[str] = pa.Field()
    
    # Customer demographics
    primary_customer_age_group: Series[str] = pa.Field(nullable=True)
    secondary_customer_age_group: Series[str] = pa.Field(nullable=True)
    gender_distribution: Series[str] = pa.Field(nullable=True)  # "male_dominant", "female_dominant", "balanced"
    
    # Income analysis
    average_household_income: Series[float] = pa.Field(ge=0.0, nullable=True)
    income_distribution: Series[str] = pa.Field(nullable=True)  # "low_income", "middle_income", "high_income"
    
    # Lifestyle attributes
    lifestyle_segments: Series[str] = pa.Field(nullable=True)  # "fashion_forward", "value_conscious", "luxury_seeking"
    shopping_behavior: Series[str] = pa.Field(nullable=True)  # "frequent", "occasional", "seasonal"
    
    # Market potential
    market_potential_score: Series[float] = pa.Field(ge=0.0, le=10.0, nullable=True)
    growth_potential: Series[str] = pa.Field(nullable=True)  # "high", "medium", "low"
    expansion_opportunity: Series[bool] = pa.Field(nullable=True)
    
    # Analysis metadata
    analysis_date: Series[str] = pa.Field()
    data_freshness: Series[int] = pa.Field(ge=0)  # days since last update
    analysis_confidence: Series[float] = pa.Field(ge=0.0, le=1.0)


class StorePerformanceEnrichmentSchema(pa.DataFrameModel):
    """Schema for store performance enrichment data."""
    
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    store_group: Series[str] = pa.Field()
    
    # Sales performance
    total_sales: Series[float] = pa.Field(ge=0.0)
    sales_per_sqm: Series[float] = pa.Field(ge=0.0, nullable=True)
    sales_growth_rate: Series[float] = pa.Field(nullable=True)
    
    # Customer metrics
    customer_count: Series[int] = pa.Field(ge=0, nullable=True)
    avg_transaction_value: Series[float] = pa.Field(ge=0.0, nullable=True)
    customer_retention_rate: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    
    # Inventory metrics
    inventory_turnover: Series[float] = pa.Field(ge=0.0, nullable=True)
    stock_accuracy: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    markdown_rate: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    
    # Operational metrics
    staff_count: Series[int] = pa.Field(ge=0, nullable=True)
    operating_hours: Series[str] = pa.Field(nullable=True)
    peak_hours: Series[str] = pa.Field(nullable=True)
    
    # Performance ranking
    performance_rank: Series[int] = pa.Field(ge=1, nullable=True)
    performance_percentile: Series[float] = pa.Field(ge=0.0, le=100.0, nullable=True)
    
    # Enrichment metadata
    enrichment_timestamp: Series[str] = pa.Field()
    data_source: Series[str] = pa.Field()
    enrichment_method: Series[str] = pa.Field()
