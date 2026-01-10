#!/usr/bin/env python3
"""
Step 15: Historical Baseline Download Schemas

Validation schemas for Step 15 - Download Historical Baseline Data.
This step downloads and processes historical baseline data for comparison analysis.

Author: Data Pipeline
Date: 2025-09-16
"""

import pandas as pd
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
import numpy as np


class HistoricalBaselineSchema(BaseModel):
    """Schema for historical baseline data validation"""
    str_code: str = Field(..., description="Store code")
    period: str = Field(..., description="Historical period")
    baseline_sales: float = Field(..., ge=0, description="Baseline sales amount")
    baseline_quantity: Optional[int] = Field(None, ge=0, description="Baseline quantity")
    category: str = Field(..., description="Product category")
    subcategory: Optional[str] = Field(None, description="Product subcategory")
    spu_code: Optional[str] = Field(None, description="SPU code if applicable")
    year: int = Field(..., ge=2020, le=2025, description="Year of baseline data")
    month: int = Field(..., ge=1, le=12, description="Month of baseline data")
    
    @field_validator('period')
    @classmethod
    def validate_period_format(cls, value):
        if not value or len(value) < 6:
            raise ValueError('Period must be at least 6 characters (YYYYMM)')
        return value


class HistoricalInsightsSchema(BaseModel):
    """Schema for historical insights validation"""
    str_code: str = Field(..., description="Store code")
    insight_type: str = Field(..., description="Type of insight")
    insight_value: float = Field(..., description="Insight value")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Confidence score")
    trend_direction: Optional[str] = Field(None, description="Trend direction")
    comparison_period: str = Field(..., description="Period being compared")
    
    @field_validator('insight_type')
    @classmethod
    def validate_insight_type(cls, value):
        valid_types = ['sales_trend', 'seasonal_pattern', 'growth_rate', 'volatility', 'peak_performance']
        if value not in valid_types:
            raise ValueError(f'Insight type must be one of: {valid_types}')
        return value
    
    @field_validator('trend_direction')
    @classmethod
    def validate_trend_direction(cls, value):
        if value is not None:
            valid_directions = ['increasing', 'decreasing', 'stable', 'volatile']
            if value not in valid_directions:
                raise ValueError(f'Trend direction must be one of: {valid_directions}')
        return value


class BaselineComparisonSchema(BaseModel):
    """Schema for baseline comparison validation"""
    str_code: str = Field(..., description="Store code")
    current_period: str = Field(..., description="Current period")
    historical_period: str = Field(..., description="Historical period")
    current_sales: float = Field(..., ge=0, description="Current period sales")
    historical_sales: float = Field(..., ge=0, description="Historical period sales")
    sales_change: float = Field(..., description="Sales change amount")
    sales_change_pct: float = Field(..., description="Sales change percentage")
    performance_indicator: str = Field(..., description="Performance indicator")
    
    @field_validator('performance_indicator')
    @classmethod
    def validate_performance_indicator(cls, value):
        valid_indicators = ['outperforming', 'underperforming', 'stable', 'volatile', 'trending_up', 'trending_down']
        if value not in valid_indicators:
            raise ValueError(f'Performance indicator must be one of: {valid_indicators}')
        return value


class Step15InputSchema(BaseModel):
    """Schema for Step 15 input validation"""
    target_period: str = Field(..., description="Target period for analysis")
    historical_periods: List[str] = Field(..., min_length=1, description="Historical periods to download")
    analysis_level: str = Field(..., description="Analysis level: spu, subcategory, or category")
    store_codes: List[str] = Field(..., min_length=1, description="Store codes to analyze")
    download_parameters: Dict[str, Any] = Field(..., description="Download parameters")
    
    @field_validator('analysis_level')
    @classmethod
    def validate_analysis_level(cls, value):
        valid_levels = ['spu', 'subcategory', 'category']
        if value not in valid_levels:
            raise ValueError(f'Analysis level must be one of: {valid_levels}')
        return value


class Step15OutputSchema(BaseModel):
    """Schema for Step 15 output validation"""
    historical_baseline: List[HistoricalBaselineSchema] = Field(..., min_length=1, description="Historical baseline data")
    historical_insights: List[HistoricalInsightsSchema] = Field(..., min_length=1, description="Historical insights")
    baseline_comparisons: List[BaselineComparisonSchema] = Field(..., min_length=1, description="Baseline comparisons")
    download_summary: Dict[str, Any] = Field(..., description="Download summary statistics")
    
    @field_validator('historical_baseline')
    @classmethod
    def validate_baseline_data(cls, value):
        if not value:
            raise ValueError('Historical baseline data cannot be empty')
        
        # Check for reasonable data ranges
        for record in value:
            if record.baseline_sales < 0:
                raise ValueError('Baseline sales cannot be negative')
        
        return value


class Step15ValidationSchema(BaseModel):
    """Schema for Step 15 validation results"""
    validation_passed: bool = Field(..., description="Whether validation passed")
    input_validation: Dict[str, Any] = Field(..., description="Input validation results")
    output_validation: Dict[str, Any] = Field(..., description="Output validation results")
    download_validation: Dict[str, Any] = Field(..., description="Download validation results")
    data_quality_validation: Dict[str, Any] = Field(..., description="Data quality validation results")
    file_validation: Dict[str, Any] = Field(..., description="File validation results")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    statistics: Dict[str, Any] = Field(..., description="Validation statistics")


class HistoricalDataQualitySchema(BaseModel):
    """Schema for historical data quality validation"""
    period: str = Field(..., description="Data period")
    completeness_score: float = Field(..., ge=0, le=1, description="Data completeness score")
    consistency_score: float = Field(..., ge=0, le=1, description="Data consistency score")
    accuracy_score: float = Field(..., ge=0, le=1, description="Data accuracy score")
    missing_data_count: int = Field(..., ge=0, description="Number of missing data points")
    outlier_count: int = Field(..., ge=0, description="Number of outliers detected")
    quality_issues: List[str] = Field(default_factory=list, description="Data quality issues")
    
    @field_validator('completeness_score')
    @classmethod
    def validate_completeness_score(cls, value):
        if value < 0.5:
            raise ValueError('Completeness score should be at least 0.5 for reliable analysis')
        return value


# Export all schemas
__all__ = [
    'HistoricalBaselineSchema',
    'HistoricalInsightsSchema',
    'BaselineComparisonSchema',
    'Step15InputSchema',
    'Step15OutputSchema',
    'Step15ValidationSchema',
    'HistoricalDataQualitySchema'
]
