import pandas as pd
#!/usr/bin/env python3
"""
Step 9 Below Minimum Rule Validation Schemas

This module contains validation schemas for Step 9 below minimum rule outputs.
Step 9 identifies SPUs that are below minimum allocation levels and recommends
positive quantity increases to reach viable allocation levels.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series, DataFrame
from typing import Optional


class BelowMinimumRuleSchema(pa.DataFrameModel):
    """
    Schema for below minimum rule results files.
    
    This schema validates the main results file that contains store-level
    summaries of below minimum SPU cases and recommendations.
    """
    
    # Core identifiers
    str_code: Series[pa.String] = pa.Field(coerce=True, description="Store code identifier")
    cluster_id: Series[int] = pa.Field(description="Cluster assignment for the store")
    
    # Below minimum metrics
    below_minimum_spus_count: Series[pa.Float64] = pa.Field(coerce=True, ge=0, nullable=True, description="Number of SPUs below minimum threshold")
    total_increase_needed: Series[pa.Float64] = pa.Field(coerce=True, ge=0, nullable=True, description="Total increase needed in units")
    avg_current_count: Series[pa.Float64] = pa.Field(coerce=True, ge=0, nullable=True, description="Average current count per SPU")
    total_quantity_change: Series[pa.Float64] = pa.Field(coerce=True, ge=0, nullable=True, description="Total quantity change recommended")
    total_investment: Series[pa.Float64] = pa.Field(coerce=True, ge=0, nullable=True, description="Total investment required")
    
    # Rule flags and metadata
    rule9_below_minimum_spu: Series[int] = pa.Field(isin=[0, 1], description="Binary flag for below minimum SPUs")
    investment_required: Series[pa.Float64] = pa.Field(coerce=True, ge=0, nullable=True, description="Investment required (standardized column)")
    recommended_quantity_change: Series[pa.Float64] = pa.Field(coerce=True, ge=0, nullable=True, description="Recommended quantity change (standardized)")
    
    # Business rationale and approval
    business_rationale: Series[str] = pa.Field(description="Business rationale for the recommendation")
    approval_reason: Series[str] = pa.Field(description="Reason for approval")
    fast_fish_compliant: Series[bool] = pa.Field(description="Whether recommendation is Fast Fish compliant")
    opportunity_type: Series[str] = pa.Field(description="Type of opportunity identified")
    
    # Rule metadata
    rule9_description: Series[str] = pa.Field(description="Description of the rule")
    rule9_threshold: Series[str] = pa.Field(description="Threshold used for the rule")
    rule9_analysis_level: Series[str] = pa.Field(description="Analysis level (spu/subcategory)")
    rule9_fix_applied: Series[str] = pa.Field(description="Description of fixes applied")


class BelowMinimumOpportunitiesSchema(pa.DataFrameModel):
    """
    Schema for below minimum opportunities files.
    
    This schema validates the detailed opportunities file that contains
    individual SPU-level below minimum cases with specific recommendations.
    """
    
    # Core identifiers
    str_code: Series[pa.String] = pa.Field(coerce=True, description="Store code identifier")
    season_name: Series[pa.String] = pa.Field(coerce=True, description="Season name")
    sex_name: Series[pa.String] = pa.Field(coerce=True, description="Sex category")
    display_location_name: Series[pa.String] = pa.Field(coerce=True, description="Display location")
    big_class_name: Series[pa.String] = pa.Field(coerce=True, description="Big class category")
    sub_cate_name: Series[pa.String] = pa.Field(coerce=True, description="Subcategory name")
    sty_code: Series[pa.String] = pa.Field(coerce=True, description="Style/SPU code")
    Cluster: Series[int] = pa.Field(description="Cluster assignment")
    
    # Sales and quantity data
    spu_sales_amt: Series[float] = pa.Field(ge=0, description="SPU sales amount")
    unit_rate: Series[float] = pa.Field(ge=0, description="Unit rate per period")
    style_count: Series[float] = pa.Field(ge=0, description="Style count (alias for unit_rate)")
    
    # Below minimum analysis
    recommended_target: Series[float] = pa.Field(ge=0, description="Recommended target units")
    increase_needed: Series[float] = pa.Field(ge=0, description="Increase needed in units")
    issue_type: Series[str] = pa.Field(description="Type of issue identified")
    issue_severity: Series[str] = pa.Field(isin=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'], description="Severity of the issue")
    
    # Recommendations
    current_quantity: Series[float] = pa.Field(ge=0, description="Current quantity")
    target_quantity: Series[float] = pa.Field(ge=0, description="Target quantity")
    recommended_quantity_change_raw: Series[float] = pa.Field(ge=0, description="Raw quantity change needed")
    recommended_quantity_change: Series[int] = pa.Field(ge=0, description="Recommended quantity change (integer)")
    recommended_action: Series[str] = pa.Field(description="Recommended action")
    recommendation_text: Series[str] = pa.Field(description="Text description of recommendation")
    
    # Investment and pricing
    unit_price: Series[float] = pa.Field(ge=0, description="Unit price", nullable=True)
    investment_required: Series[float] = pa.Field(ge=0, description="Investment required", nullable=True)
    
    # Sell-through validation (if available)
    current_sell_through_rate: Series[float] = pa.Field(ge=0, le=100, description="Current sell-through rate (%)", nullable=True)
    predicted_sell_through_rate: Series[float] = pa.Field(ge=0, le=100, description="Predicted sell-through rate (%)", nullable=True)
    sell_through_improvement: Series[float] = pa.Field(description="Sell-through improvement (percentage points)", nullable=True)
    fast_fish_compliant: Series[bool] = pa.Field(description="Fast Fish compliance", nullable=True)
    business_rationale: Series[str] = pa.Field(description="Business rationale", nullable=True)
    approval_reason: Series[str] = pa.Field(description="Approval reason", nullable=True)
    
    # Additional metadata
    opportunity_type: Series[str] = pa.Field(description="Type of opportunity", nullable=True)


class BelowMinimumSubcategorySchema(pa.DataFrameModel):
    """
    Schema for below minimum subcategory results.
    
    This schema validates subcategory-level below minimum analysis results.
    """
    
    # Core identifiers
    str_code: Series[pa.String] = pa.Field(coerce=True, description="Store code identifier")
    cluster_id: Series[int] = pa.Field(description="Cluster assignment")
    
    # Subcategory metrics
    below_minimum_count: Series[int] = pa.Field(ge=0, description="Number of below minimum subcategories")
    total_increase_needed: Series[float] = pa.Field(ge=0, description="Total increase needed")
    avg_current_count: Series[float] = pa.Field(ge=0, description="Average current count")
    
    # Rule flags
    rule9_below_minimum: Series[int] = pa.Field(isin=[0, 1], description="Binary flag for below minimum")
    
    # Business rationale
    business_rationale: Series[str] = pa.Field(description="Business rationale")
    approval_reason: Series[str] = pa.Field(description="Approval reason")
    fast_fish_compliant: Series[bool] = pa.Field(description="Fast Fish compliance")
    opportunity_type: Series[str] = pa.Field(description="Opportunity type")
    
    # Rule metadata
    rule9_description: Series[str] = pa.Field(description="Rule description")
    rule9_threshold: Series[str] = pa.Field(description="Rule threshold")
    rule9_analysis_level: Series[str] = pa.Field(description="Analysis level")
