#!/usr/bin/env python3
"""
Step 26 Price Elasticity Analyzer Validation Schemas

This module contains schemas for price elasticity analysis validation from Step 26.

Author: Data Pipeline
Date: 2025-01-16
"""

import pandera as pa
from pandera.typing import Series


class PriceBandAnalysisSchema(pa.DataFrameModel):
    """Schema for price band analysis from Step 26 - matches actual CSV output structure."""
    
    # Product identification
    spu_code: Series[str] = pa.Field()
    avg_unit_price: Series[float] = pa.Field(ge=0.0)
    price_std: Series[float] = pa.Field(ge=0.0, nullable=True)
    price_observations: Series[int] = pa.Field(ge=1)
    
    # Sales metrics
    total_sales_amount: Series[float] = pa.Field(ge=0.0)
    total_sales_quantity: Series[float] = pa.Field(ge=0.0)
    
    # Price band classification
    price_band: Series[str] = pa.Field()  # "VALUE", "PREMIUM", "LUXURY", "BUDGET"
    price_band_range: Series[str] = pa.Field()  # e.g., "¥52-73"
    
    # Product context
    product_role: Series[str] = pa.Field()  # "CORE", "SEASONAL", "FILLER", "CLEARANCE"
    category: Series[str] = pa.Field()
    subcategory: Series[str] = pa.Field()
    
    # Price analysis
    price_vs_role_avg: Series[float] = pa.Field()  # Price deviation from role average


class SubstitutionElasticityMatrixSchema(pa.DataFrameModel):
    """Schema for substitution elasticity matrix from Step 26 - matches actual CSV output structure."""
    
    # Product pair identification
    product_1: Series[str] = pa.Field()
    product_2: Series[str] = pa.Field()
    category: Series[str] = pa.Field()
    common_stores: Series[int] = pa.Field(ge=1)
    
    # Correlation analysis
    price_correlation: Series[float] = pa.Field(ge=-1.0, le=1.0)
    quantity_correlation: Series[float] = pa.Field(ge=-1.0, le=1.0)
    substitution_score: Series[float] = pa.Field(ge=-1.0, le=1.0)
    
    # Relationship classification
    relationship_strength: Series[str] = pa.Field()  # "Strong Substitutes", "Moderate Substitutes", "Weak Substitutes", "Independent", "Complements"
    
    # Price and quantity differences
    avg_price_diff: Series[float] = pa.Field()
    avg_quantity_diff: Series[float] = pa.Field()


class PriceElasticityAnalysisReportSchema(pa.DataFrameModel):
    """Schema for price elasticity analysis report from Step 26."""
    
    # Report metadata
    report_timestamp: Series[str] = pa.Field()
    analysis_period: Series[str] = pa.Field()
    total_products_analyzed: Series[int] = pa.Field(ge=0)
    
    # Price band distribution
    value_products: Series[int] = pa.Field(ge=0)
    premium_products: Series[int] = pa.Field(ge=0)
    luxury_products: Series[int] = pa.Field(ge=0)
    budget_products: Series[int] = pa.Field(ge=0)
    
    # Elasticity insights
    total_product_pairs: Series[int] = pa.Field(ge=0)
    strong_substitutes: Series[int] = pa.Field(ge=0)
    moderate_substitutes: Series[int] = pa.Field(ge=0)
    weak_substitutes: Series[int] = pa.Field(ge=0)
    independent_products: Series[int] = pa.Field(ge=0)
    complementary_products: Series[int] = pa.Field(ge=0)
    
    # Price analysis
    avg_price: Series[float] = pa.Field(ge=0.0)
    price_std: Series[float] = pa.Field(ge=0.0)
    price_range: Series[str] = pa.Field()  # e.g., "¥15-150"
    
    # Category insights
    top_price_elastic_categories: Series[str] = pa.Field()  # JSON string
    price_band_recommendations: Series[str] = pa.Field()  # JSON string


class PriceElasticitySummarySchema(pa.DataFrameModel):
    """Schema for price elasticity summary JSON from Step 26."""
    
    # Summary metadata
    summary_timestamp: Series[str] = pa.Field()
    analysis_completed: Series[bool] = pa.Field()
    data_quality_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Price band statistics
    total_products: Series[int] = pa.Field(ge=0)
    price_bands_distribution: Series[str] = pa.Field()  # JSON string
    
    # Elasticity statistics
    total_pairs_analyzed: Series[int] = pa.Field(ge=0)
    substitution_relationships: Series[str] = pa.Field()  # JSON string
    
    # Performance metrics
    avg_substitution_score: Series[float] = pa.Field(ge=-1.0, le=1.0)
    price_correlation_strength: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Business insights
    pricing_opportunities: Series[str] = pa.Field()  # JSON string
    substitution_risks: Series[str] = pa.Field()  # JSON string


