import pandas as pd
"""
Pandera schemas for Step 13: Consolidate All SPU-Level Rule Results

This module defines comprehensive data validation schemas for Step 13 outputs,
ensuring data quality and consistency across all consolidation levels.
"""

import pandera.pandas as pa
from pandera.typing import Series, DataFrame
from typing import Optional


class StoreLevelResultsSchema(pa.DataFrameModel):
    """Schema for store-level consolidated results."""
    
    str_code: Series[str] = pa.Field(description="Store code")
    rule_source: Series[str] = pa.Field(description="Source rule identifier")
    total_quantity_change: Series[float] = pa.Field(description="Total quantity change for store")
    total_investment: Series[float] = pa.Field(description="Total investment required")
    affected_spus: Series[int] = pa.Field(description="Number of affected SPUs")
    total_current_quantity: Series[float] = pa.Field(description="Total current quantity")
    period_label: Series[str] = pa.Field(description="Period label (e.g., 202508A)")
    target_yyyymm: Series[str] = pa.Field(description="Target year-month (e.g., 202508)")
    target_period: Series[str] = pa.Field(description="Target period (A, B, or full)")


class DetailedSPUResultsSchema(pa.DataFrameModel):
    """Schema for detailed SPU-level consolidated results."""
    
    str_code: Series[str] = pa.Field(description="Store code")
    spu_code: Series[str] = pa.Field(description="SPU code")
    sub_cate_name: Series[str] = pa.Field(description="Subcategory name", nullable=True)
    recommended_quantity_change: Series[float] = pa.Field(description="Recommended quantity change")
    rule_source: Series[str] = pa.Field(description="Source rule identifier")
    cluster: Series[int] = pa.Field(description="Cluster ID")
    current_quantity: Series[float] = pa.Field(description="Current quantity")
    investment_required: Series[float] = pa.Field(description="Investment required")
    unit_price: Series[float] = pa.Field(description="Unit price")
    business_rationale: Series[str] = pa.Field(description="Business rationale", nullable=True)
    opportunity_score: Series[float] = pa.Field(description="Opportunity score", nullable=True)
    period_label: Series[str] = pa.Field(description="Period label")
    target_yyyymm: Series[str] = pa.Field(description="Target year-month")
    target_period: Series[str] = pa.Field(description="Target period")


class ClusterSubcategoryResultsSchema(pa.DataFrameModel):
    """Schema for cluster-subcategory aggregated results."""
    
    cluster: Series[int] = pa.Field(description="Cluster ID")
    subcategory: Series[str] = pa.Field(description="Subcategory name")
    stores_affected: Series[int] = pa.Field(description="Number of stores affected")
    unique_spus: Series[int] = pa.Field(description="Number of unique SPUs")
    total_quantity_change: Series[float] = pa.Field(description="Total quantity change")
    total_investment: Series[float] = pa.Field(description="Total investment")
    period_label: Series[str] = pa.Field(description="Period label")
    target_yyyymm: Series[str] = pa.Field(description="Target year-month")
    target_period: Series[str] = pa.Field(description="Target period")


class SeasonalFeaturesSchema(pa.DataFrameModel):
    """Schema for seasonal features analysis results."""
    
    # Note: This schema will be defined based on actual seasonal features output
    # Placeholder for now - will be updated when seasonal features structure is known
    period_label: Series[str] = pa.Field(description="Period label")
    target_yyyymm: Series[str] = pa.Field(description="Target year-month")
    target_period: Series[str] = pa.Field(description="Target period")


# Common column schemas for reuse
class CommonColumns:
    """Common column schemas used across Step 13 outputs."""
    
    PERIOD_LABEL = pa.Field(description="Period label (e.g., 202508A)")
    TARGET_YYYYMM = pa.Field(description="Target year-month (e.g., 202508)")
    TARGET_PERIOD = pa.Field(description="Target period (A, B, or full)")
    STR_CODE = pa.Field(description="Store code")
    SPU_CODE = pa.Field(description="SPU code")
    RULE_SOURCE = pa.Field(description="Source rule identifier")
    CLUSTER = pa.Field(description="Cluster ID")
    QUANTITY_CHANGE = pa.Field(description="Quantity change")
    INVESTMENT = pa.Field(description="Investment amount")
    UNIT_PRICE = pa.Field(description="Unit price")


# Table schemas for input validation
class InputRuleResultsSchema(pa.DataFrameModel):
    """Schema for individual rule result inputs."""
    
    str_code: Series[str] = pa.Field(description="Store code")
    spu_code: Series[str] = pa.Field(description="SPU code")
    recommended_quantity_change: Series[float] = pa.Field(description="Recommended quantity change")
    rule_source: Series[str] = pa.Field(description="Source rule identifier")
    cluster: Series[int] = pa.Field(description="Cluster ID")
    current_quantity: Series[float] = pa.Field(description="Current quantity")
    investment_required: Series[float] = pa.Field(description="Investment required")
    unit_price: Series[float] = pa.Field(description="Unit price")
    business_rationale: Series[str] = pa.Field(description="Business rationale", nullable=True)
    opportunity_score: Series[float] = pa.Field(description="Opportunity score", nullable=True)






