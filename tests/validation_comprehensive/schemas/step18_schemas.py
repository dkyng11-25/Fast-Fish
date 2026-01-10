import pandas as pd
"""
Pandera schemas for Step 18: Validate Results

This module defines comprehensive data validation schemas for Step 18 outputs,
including sell-through validation and final results validation.
"""

import pandera.pandas as pa
from pandera.typing import Series
from typing import Optional


class Step18SellThroughSchema(pa.DataFrameModel):
    """Schema for Step 18 sell-through validation file"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    spu_code: Series[str] = pa.Field(description="SPU code identifier")
    cluster_id: Series[str] = pa.Field(description="Cluster identifier")
    sub_cate_name: Series[str] = pa.Field(description="Subcategory name")
    
    # Sell-through calculation
    sell_through_rate: Series[float] = pa.Field(ge=0, le=1, description="Calculated sell-through rate")
    sell_through_method: Series[str] = pa.Field(description="Method used for STR calculation")
    sell_through_confidence: Series[float] = pa.Field(ge=0, le=1, description="STR calculation confidence")
    
    # Input data for STR calculation
    total_sales_amt: Series[float] = pa.Field(ge=0, description="Total sales amount")
    total_quantity: Series[float] = pa.Field(ge=0, description="Total quantity")
    period_days: Series[int] = pa.Field(ge=1, description="Period duration in days")
    
    # STR validation
    str_validation_status: Series[str] = pa.Field(description="STR validation status")
    str_validation_errors: Series[str] = pa.Field(nullable=True, description="STR validation errors")
    str_quality_score: Series[float] = pa.Field(ge=0, le=1, description="STR quality score")
    
    # Business metrics
    inventory_turnover: Series[float] = pa.Field(ge=0, nullable=True, description="Inventory turnover rate")
    days_inventory: Series[float] = pa.Field(ge=0, nullable=True, description="Days in inventory")
    stockout_risk: Series[str] = pa.Field(nullable=True, description="Stockout risk level")
    
    # Compliance validation
    fast_fish_compliant: Series[str] = pa.Field(description="Fast Fish compliance status")
    client_compliant: Series[str] = pa.Field(description="Client compliance status")
    validation_passed: Series[str] = pa.Field(description="Overall validation status")
    
    # Metadata
    created_at: Series[str] = pa.Field(description="Creation timestamp")
    validated_at: Series[str] = pa.Field(description="Validation timestamp")
    data_source: Series[str] = pa.Field(description="Data source identifier")


class Step18ValidationResultsSchema(pa.DataFrameModel):
    """Schema for Step 18 validation results file"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    cluster_id: Series[str] = pa.Field(description="Cluster identifier")
    
    # Validation summary
    total_spus_validated: Series[int] = pa.Field(ge=0, description="Total SPUs validated")
    validation_passed: Series[int] = pa.Field(ge=0, description="SPUs that passed validation")
    validation_failed: Series[int] = pa.Field(ge=0, description="SPUs that failed validation")
    validation_warnings: Series[int] = pa.Field(ge=0, description="SPUs with validation warnings")
    
    # STR validation summary
    avg_str_confidence: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Average STR confidence")
    str_calculation_success_rate: Series[float] = pa.Field(ge=0, le=1, description="STR calculation success rate")
    str_validation_success_rate: Series[float] = pa.Field(ge=0, le=1, description="STR validation success rate")
    
    # Compliance summary
    fast_fish_compliance_rate: Series[float] = pa.Field(ge=0, le=1, description="Fast Fish compliance rate")
    client_compliance_rate: Series[float] = pa.Field(ge=0, le=1, description="Client compliance rate")
    overall_validation_rate: Series[float] = pa.Field(ge=0, le=1, description="Overall validation success rate")
    
    # Data quality summary
    avg_data_quality_score: Series[float] = pa.Field(ge=0, le=1, description="Average data quality score")
    completeness_score: Series[float] = pa.Field(ge=0, le=1, description="Data completeness score")
    accuracy_score: Series[float] = pa.Field(ge=0, le=1, description="Data accuracy score")
    
    # Business impact summary
    total_recommended_changes: Series[float] = pa.Field(nullable=True, description="Total recommended changes")
    total_sales_impact: Series[float] = pa.Field(nullable=True, description="Total sales impact")
    high_priority_items: Series[int] = pa.Field(ge=0, description="High priority items")
    
    # Metadata
    created_at: Series[str] = pa.Field(description="Creation timestamp")
    validation_duration: Series[float] = pa.Field(ge=0, description="Validation duration in seconds")
    validation_method: Series[str] = pa.Field(description="Validation method used")


class Step18FinalResultsSchema(pa.DataFrameModel):
    """Schema for Step 18 final results file"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    spu_code: Series[str] = pa.Field(description="SPU code identifier")
    cluster_id: Series[str] = pa.Field(description="Cluster identifier")
    sub_cate_name: Series[str] = pa.Field(description="Subcategory name")
    big_class_name: Series[str] = pa.Field(description="Big class name")
    season_name: Series[str] = pa.Field(description="Season name")
    sex_name: Series[str] = pa.Field(description="Sex name")
    display_location_name: Series[str] = pa.Field(description="Display location name")
    
    # Final recommendations
    final_recommendation: Series[str] = pa.Field(description="Final recommendation")
    recommendation_confidence: Series[float] = pa.Field(ge=0, le=1, description="Recommendation confidence")
    implementation_priority: Series[str] = pa.Field(description="Implementation priority")
    
    # Quantity recommendations
    recommended_quantity_change: Series[float] = pa.Field(nullable=True, description="Recommended quantity change")
    current_quantity: Series[float] = pa.Field(ge=0, nullable=True, description="Current quantity")
    recommended_quantity: Series[float] = pa.Field(ge=0, nullable=True, description="Recommended quantity")
    
    # Sales impact
    expected_sales_impact: Series[float] = pa.Field(nullable=True, description="Expected sales impact")
    expected_sell_through_rate: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Expected sell-through rate")
    expected_inventory_turnover: Series[float] = pa.Field(ge=0, nullable=True, description="Expected inventory turnover")
    
    # Validation results
    validation_status: Series[str] = pa.Field(description="Validation status")
    validation_errors: Series[str] = pa.Field(nullable=True, description="Validation errors")
    data_quality_score: Series[float] = pa.Field(ge=0, le=1, description="Data quality score")
    
    # Compliance
    fast_fish_compliant: Series[str] = pa.Field(description="Fast Fish compliance status")
    client_compliant: Series[str] = pa.Field(description="Client compliance status")
    approval_status: Series[str] = pa.Field(nullable=True, description="Approval status")
    
    # Business rationale
    business_rationale: Series[str] = pa.Field(nullable=True, description="Business rationale")
    risk_assessment: Series[str] = pa.Field(nullable=True, description="Risk assessment")
    expected_roi: Series[float] = pa.Field(nullable=True, description="Expected ROI")
    
    # Metadata
    created_at: Series[str] = pa.Field(description="Creation timestamp")
    updated_at: Series[str] = pa.Field(description="Last update timestamp")
    data_source: Series[str] = pa.Field(description="Data source identifier")
    pipeline_version: Series[str] = pa.Field(description="Pipeline version")


class Step18SummaryReportSchema(pa.DataFrameModel):
    """Schema for Step 18 summary report file"""
    
    report_type: Series[str] = pa.Field(description="Report type")
    report_period: Series[str] = pa.Field(description="Report period")
    
    # Overall statistics
    total_stores: Series[int] = pa.Field(ge=0, description="Total stores analyzed")
    total_spus: Series[int] = pa.Field(ge=0, description="Total SPUs analyzed")
    total_clusters: Series[int] = pa.Field(ge=0, description="Total clusters analyzed")
    
    # Validation statistics
    validation_success_rate: Series[float] = pa.Field(ge=0, le=1, description="Overall validation success rate")
    str_calculation_success_rate: Series[float] = pa.Field(ge=0, le=1, description="STR calculation success rate")
    data_quality_score: Series[float] = pa.Field(ge=0, le=1, description="Overall data quality score")
    
    # Compliance statistics
    fast_fish_compliance_rate: Series[float] = pa.Field(ge=0, le=1, description="Fast Fish compliance rate")
    client_compliance_rate: Series[float] = pa.Field(ge=0, le=1, description="Client compliance rate")
    
    # Business impact
    total_recommended_changes: Series[float] = pa.Field(nullable=True, description="Total recommended changes")
    total_expected_sales_impact: Series[float] = pa.Field(nullable=True, description="Total expected sales impact")
    high_priority_recommendations: Series[int] = pa.Field(ge=0, description="High priority recommendations")
    
    # Performance metrics
    processing_time: Series[float] = pa.Field(ge=0, description="Processing time in seconds")
    memory_usage: Series[float] = pa.Field(ge=0, description="Memory usage in MB")
    error_count: Series[int] = pa.Field(ge=0, description="Error count")
    warning_count: Series[int] = pa.Field(ge=0, description="Warning count")
    
    # Metadata
    created_at: Series[str] = pa.Field(description="Creation timestamp")
    pipeline_version: Series[str] = pa.Field(description="Pipeline version")
    validation_method: Series[str] = pa.Field(description="Validation method used")
    report_status: Series[str] = pa.Field(description="Report status")




