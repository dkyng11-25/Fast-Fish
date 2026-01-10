import pandas as pd
"""
Pandera schemas for Step 17: Augment Recommendations

This module defines comprehensive data validation schemas for Step 17 outputs,
including augmented recommendations and historical data integration.
"""

import pandera.pandas as pa
from pandera.typing import Series
from typing import Optional


class Step17AugmentedSchema(pa.DataFrameModel):
    """Schema for Step 17 augmented recommendations file"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    spu_code: Series[str] = pa.Field(description="SPU code identifier")
    cluster_id: Series[str] = pa.Field(description="Cluster identifier")
    sub_cate_name: Series[str] = pa.Field(description="Subcategory name")
    big_class_name: Series[str] = pa.Field(description="Big class name")
    season_name: Series[str] = pa.Field(description="Season name")
    sex_name: Series[str] = pa.Field(description="Sex name")
    display_location_name: Series[str] = pa.Field(description="Display location name")
    
    # Historical data fields
    historical_sales_amt: Series[float] = pa.Field(ge=0, nullable=True, description="Historical sales amount")
    historical_quantity: Series[float] = pa.Field(ge=0, nullable=True, description="Historical quantity")
    historical_sell_through_rate: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Historical sell-through rate")
    
    # Current period data
    current_sales_amt: Series[float] = pa.Field(ge=0, nullable=True, description="Current sales amount")
    current_quantity: Series[float] = pa.Field(ge=0, nullable=True, description="Current quantity")
    current_sell_through_rate: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Current sell-through rate")
    
    # STR calculation fields
    str_calculation_method: Series[str] = pa.Field(description="STR calculation method used")
    str_confidence_score: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="STR confidence score")
    str_trend_direction: Series[str] = pa.Field(nullable=True, description="STR trend direction")
    str_period_comparison: Series[str] = pa.Field(nullable=True, description="STR period comparison")
    
    # Augmentation fields
    augmentation_type: Series[str] = pa.Field(description="Type of augmentation applied")
    augmentation_confidence: Series[float] = pa.Field(ge=0, le=1, description="Augmentation confidence score")
    historical_weight: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Weight given to historical data")
    trend_weight: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Weight given to trend data")
    
    # Recommendation fields
    recommended_quantity_change: Series[float] = pa.Field(nullable=True, description="Recommended quantity change")
    recommended_sales_impact: Series[float] = pa.Field(nullable=True, description="Recommended sales impact")
    business_rationale: Series[str] = pa.Field(nullable=True, description="Business rationale")
    risk_assessment: Series[str] = pa.Field(nullable=True, description="Risk assessment")
    
    # Client compliance fields
    client_compliant: Series[str] = pa.Field(description="Client compliance status")
    approval_status: Series[str] = pa.Field(nullable=True, description="Approval status")
    implementation_priority: Series[str] = pa.Field(nullable=True, description="Implementation priority")
    
    # Metadata fields
    created_at: Series[str] = pa.Field(description="Creation timestamp")
    updated_at: Series[str] = pa.Field(description="Last update timestamp")
    data_source: Series[str] = pa.Field(description="Data source identifier")
    validation_status: Series[str] = pa.Field(description="Validation status")


class Step17SummarySchema(pa.DataFrameModel):
    """Schema for Step 17 summary file (store-level aggregated results)"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    cluster_id: Series[str] = pa.Field(description="Cluster identifier")
    
    # Augmentation summary
    total_augmented_spus: Series[int] = pa.Field(ge=0, description="Total augmented SPUs")
    historical_data_available: Series[int] = pa.Field(ge=0, description="SPUs with historical data")
    trend_data_available: Series[int] = pa.Field(ge=0, description="SPUs with trend data")
    
    # STR calculation summary
    avg_str_confidence: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Average STR confidence")
    str_calculation_success_rate: Series[float] = pa.Field(ge=0, le=1, description="STR calculation success rate")
    
    # Augmentation summary
    avg_augmentation_confidence: Series[float] = pa.Field(ge=0, le=1, description="Average augmentation confidence")
    augmentation_success_rate: Series[float] = pa.Field(ge=0, le=1, description="Augmentation success rate")
    
    # Recommendation summary
    total_recommended_changes: Series[float] = pa.Field(nullable=True, description="Total recommended changes")
    total_sales_impact: Series[float] = pa.Field(nullable=True, description="Total sales impact")
    high_priority_recommendations: Series[int] = pa.Field(ge=0, description="High priority recommendations")
    
    # Client compliance summary
    client_compliant_rate: Series[float] = pa.Field(ge=0, le=1, description="Client compliance rate")
    approval_rate: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Approval rate")
    
    # Metadata
    created_at: Series[str] = pa.Field(description="Creation timestamp")
    data_quality_score: Series[float] = pa.Field(ge=0, le=1, description="Data quality score")


class Step17HistoricalDataSchema(pa.DataFrameModel):
    """Schema for Step 17 historical data file"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    spu_code: Series[str] = pa.Field(description="SPU code identifier")
    period: Series[str] = pa.Field(description="Historical period")
    
    # Historical metrics
    sales_amt: Series[float] = pa.Field(ge=0, nullable=True, description="Historical sales amount")
    quantity: Series[float] = pa.Field(ge=0, nullable=True, description="Historical quantity")
    sell_through_rate: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Historical sell-through rate")
    
    # Trend indicators
    trend_direction: Series[str] = pa.Field(nullable=True, description="Trend direction")
    trend_strength: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Trend strength")
    seasonal_factor: Series[float] = pa.Field(ge=0, nullable=True, description="Seasonal factor")
    
    # Data quality
    data_quality_score: Series[float] = pa.Field(ge=0, le=1, description="Data quality score")
    completeness_score: Series[float] = pa.Field(ge=0, le=1, description="Completeness score")
    
    # Metadata
    created_at: Series[str] = pa.Field(description="Creation timestamp")
    data_source: Series[str] = pa.Field(description="Data source identifier")


class Step17TrendDataSchema(pa.DataFrameModel):
    """Schema for Step 17 trend data file"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    spu_code: Series[str] = pa.Field(description="SPU code identifier")
    
    # Trend analysis
    trend_period: Series[str] = pa.Field(description="Trend analysis period")
    trend_direction: Series[str] = pa.Field(description="Trend direction")
    trend_strength: Series[float] = pa.Field(ge=0, le=1, description="Trend strength")
    trend_confidence: Series[float] = pa.Field(ge=0, le=1, description="Trend confidence")
    
    # Seasonal analysis
    seasonal_pattern: Series[str] = pa.Field(nullable=True, description="Seasonal pattern")
    seasonal_strength: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Seasonal strength")
    peak_period: Series[str] = pa.Field(nullable=True, description="Peak period")
    low_period: Series[str] = pa.Field(nullable=True, description="Low period")
    
    # Predictive indicators
    predicted_next_period_sales: Series[float] = pa.Field(ge=0, nullable=True, description="Predicted next period sales")
    predicted_next_period_quantity: Series[float] = pa.Field(ge=0, nullable=True, description="Predicted next period quantity")
    prediction_confidence: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Prediction confidence")
    
    # Metadata
    created_at: Series[str] = pa.Field(description="Creation timestamp")
    analysis_method: Series[str] = pa.Field(description="Analysis method used")
    data_quality_score: Series[float] = pa.Field(ge=0, le=1, description="Data quality score")




