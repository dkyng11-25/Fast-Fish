import pandas as pd
#!/usr/bin/env python3
"""
Step 17 Augment Recommendations Validation Schemas

This module contains schemas for augmented recommendations validation from Step 17.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series


class AugmentedRecommendationsSchema(pa.DataFrameModel):
    """Schema for augmented recommendations from Step 17."""
    
    # Store and product identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    spu_code: Series[str] = pa.Field()
    sub_cate_name: Series[str] = pa.Field()
    
    # Enhanced recommendations
    original_recommendation: Series[str] = pa.Field()
    augmented_recommendation: Series[str] = pa.Field()
    recommendation_confidence: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Business context
    market_trend: Series[str] = pa.Field()  # "growing", "stable", "declining"
    seasonal_factor: Series[float] = pa.Field(ge=0.0, le=2.0, nullable=True)
    competitive_advantage: Series[str] = pa.Field(nullable=True)
    
    # Financial metrics
    expected_roi: Series[float] = pa.Field(nullable=True)
    risk_level: Series[str] = pa.Field()  # "low", "medium", "high"
    payback_period: Series[float] = pa.Field(ge=0.0, nullable=True)
    
    # Implementation details
    implementation_priority: Series[str] = pa.Field()  # "immediate", "short_term", "long_term"
    required_investment: Series[float] = pa.Field(ge=0.0)
    expected_benefit: Series[str] = pa.Field()
    
    # Validation metrics
    data_quality_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    recommendation_source: Series[str] = pa.Field()
    last_updated: Series[str] = pa.Field()


class RecommendationEnhancementSchema(pa.DataFrameModel):
    """Schema for recommendation enhancement metadata."""
    
    recommendation_id: Series[str] = pa.Field()
    enhancement_type: Series[str] = pa.Field()  # "market_analysis", "seasonal_adjustment", "competitive_analysis"
    
    # Enhancement details
    enhancement_description: Series[str] = pa.Field()
    enhancement_confidence: Series[float] = pa.Field(ge=0.0, le=1.0)
    enhancement_source: Series[str] = pa.Field()
    
    # Impact assessment
    impact_score: Series[float] = pa.Field(ge=0.0, le=10.0)
    impact_description: Series[str] = pa.Field()
    
    # Validation
    enhancement_validated: Series[bool] = pa.Field()
    validation_notes: Series[str] = pa.Field(nullable=True)


class MarketAnalysisSchema(pa.DataFrameModel):
    """Schema for market analysis data."""
    
    sub_cate_name: Series[str] = pa.Field()
    market_trend: Series[str] = pa.Field()
    trend_strength: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Market metrics
    market_size: Series[float] = pa.Field(ge=0.0, nullable=True)
    market_growth_rate: Series[float] = pa.Field(nullable=True)
    competitive_intensity: Series[str] = pa.Field()  # "low", "medium", "high"
    
    # Seasonal patterns
    seasonal_peak_month: Series[int] = pa.Field(ge=1, le=12, nullable=True)
    seasonal_trough_month: Series[int] = pa.Field(ge=1, le=12, nullable=True)
    seasonal_variation: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    
    # Data quality
    analysis_date: Series[str] = pa.Field()
    data_freshness: Series[int] = pa.Field(ge=0)  # days since last update
