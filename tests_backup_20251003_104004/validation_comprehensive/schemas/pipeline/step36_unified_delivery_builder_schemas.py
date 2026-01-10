#!/usr/bin/env python3
"""
Step 36 Unified Delivery Builder Validation Schemas

This module contains schemas for unified delivery builder validation from Step 36.

Author: Data Pipeline
Date: 2025-01-16
"""

import pandera as pa
from pandera.typing import Series


class UnifiedDeliveryCSVSchema(pa.DataFrameModel):
    """Schema for unified delivery CSV output from Step 36 - matches expected CSV structure."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    store_group: Series[str] = pa.Field()
    store_name: Series[str] = pa.Field(nullable=True)
    
    # Product identification
    spu_code: Series[str] = pa.Field()
    spu_name: Series[str] = pa.Field(nullable=True)
    category: Series[str] = pa.Field()
    subcategory: Series[str] = pa.Field()
    
    # Current state
    current_quantity: Series[float] = pa.Field(ge=0.0)
    current_sales: Series[float] = pa.Field(ge=0.0)
    current_sellthrough_rate: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Recommendations
    recommended_quantity: Series[float] = pa.Field(ge=0.0)
    quantity_change: Series[float] = pa.Field()
    change_type: Series[str] = pa.Field()  # "INCREASE", "DECREASE", "MAINTAIN"
    
    # Business context
    product_role: Series[str] = pa.Field()  # "CORE", "SEASONAL", "FILLER", "CLEARANCE"
    price_band: Series[str] = pa.Field()  # "BUDGET", "VALUE", "PREMIUM", "LUXURY"
    style_orientation: Series[str] = pa.Field()  # "Fashion", "Basic", "Mixed"
    
    # Store attributes
    store_size: Series[str] = pa.Field(nullable=True)  # "Small", "Medium", "Large"
    location_type: Series[str] = pa.Field(nullable=True)  # "Urban", "Suburban", "Rural"
    customer_demographics: Series[str] = pa.Field(nullable=True)  # JSON string
    
    # Performance metrics
    sales_performance: Series[float] = pa.Field(ge=0.0, nullable=True)
    inventory_turnover: Series[float] = pa.Field(ge=0.0, nullable=True)
    capacity_utilization: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    
    # Business impact
    expected_revenue_impact: Series[float] = pa.Field(nullable=True)
    investment_required: Series[float] = pa.Field(ge=0.0, nullable=True)
    expected_roi: Series[float] = pa.Field(nullable=True)
    
    # Implementation details
    priority_level: Series[str] = pa.Field()  # "HIGH", "MEDIUM", "LOW"
    implementation_complexity: Series[str] = pa.Field()  # "LOW", "MEDIUM", "HIGH"
    expected_timeline: Series[str] = pa.Field()  # e.g., "1-3 months"
    
    # Quality assurance
    data_quality_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    validation_status: Series[str] = pa.Field()  # "VALID", "WARNING", "ERROR"
    last_updated: Series[str] = pa.Field()


class UnifiedDeliveryExcelSchema(pa.DataFrameModel):
    """Schema for unified delivery Excel output from Step 36 - matches expected Excel structure."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    store_group: Series[str] = pa.Field()
    store_name: Series[str] = pa.Field(nullable=True)
    
    # Product identification
    spu_code: Series[str] = pa.Field()
    spu_name: Series[str] = pa.Field(nullable=True)
    category: Series[str] = pa.Field()
    subcategory: Series[str] = pa.Field()
    
    # Current state
    current_quantity: Series[float] = pa.Field(ge=0.0)
    current_sales: Series[float] = pa.Field(ge=0.0)
    current_sellthrough_rate: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Recommendations
    recommended_quantity: Series[float] = pa.Field(ge=0.0)
    quantity_change: Series[float] = pa.Field()
    change_type: Series[str] = pa.Field()  # "INCREASE", "DECREASE", "MAINTAIN"
    
    # Business context
    product_role: Series[str] = pa.Field()  # "CORE", "SEASONAL", "FILLER", "CLEARANCE"
    price_band: Series[str] = pa.Field()  # "BUDGET", "VALUE", "PREMIUM", "LUXURY"
    style_orientation: Series[str] = pa.Field()  # "Fashion", "Basic", "Mixed"
    
    # Store attributes
    store_size: Series[str] = pa.Field(nullable=True)  # "Small", "Medium", "Large"
    location_type: Series[str] = pa.Field(nullable=True)  # "Urban", "Suburban", "Rural"
    customer_demographics: Series[str] = pa.Field(nullable=True)  # JSON string
    
    # Performance metrics
    sales_performance: Series[float] = pa.Field(ge=0.0, nullable=True)
    inventory_turnover: Series[float] = pa.Field(ge=0.0, nullable=True)
    capacity_utilization: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    
    # Business impact
    expected_revenue_impact: Series[float] = pa.Field(nullable=True)
    investment_required: Series[float] = pa.Field(ge=0.0, nullable=True)
    expected_roi: Series[float] = pa.Field(nullable=True)
    
    # Implementation details
    priority_level: Series[str] = pa.Field()  # "HIGH", "MEDIUM", "LOW"
    implementation_complexity: Series[str] = pa.Field()  # "LOW", "MEDIUM", "HIGH"
    expected_timeline: Series[str] = pa.Field()  # e.g., "1-3 months"
    
    # Quality assurance
    data_quality_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    validation_status: Series[str] = pa.Field()  # "VALID", "WARNING", "ERROR"
    last_updated: Series[str] = pa.Field()


class UnifiedDeliveryValidationSchema(pa.DataFrameModel):
    """Schema for unified delivery validation from Step 36."""
    
    # Validation metadata
    validation_timestamp: Series[str] = pa.Field()
    analysis_period: Series[str] = pa.Field()
    total_records_validated: Series[int] = pa.Field(ge=0)
    
    # Validation results
    valid_records: Series[int] = pa.Field(ge=0)
    warning_records: Series[int] = pa.Field(ge=0)
    error_records: Series[int] = pa.Field(ge=0)
    
    # Data quality metrics
    avg_data_quality_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    completeness_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    accuracy_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    consistency_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Business logic validation
    business_rule_compliance: Series[float] = pa.Field(ge=0.0, le=1.0)
    constraint_satisfaction: Series[float] = pa.Field(ge=0.0, le=1.0)
    allocation_accuracy: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Validation issues
    data_quality_issues: Series[str] = pa.Field()  # JSON string
    business_logic_issues: Series[str] = pa.Field()  # JSON string
    constraint_violations: Series[str] = pa.Field()  # JSON string
    
    # Recommendations
    improvement_suggestions: Series[str] = pa.Field()  # JSON string
    priority_actions: Series[str] = pa.Field()  # JSON string
    success_metrics: Series[str] = pa.Field()  # JSON string


class UnifiedDeliveryClusterCSVSchema(pa.DataFrameModel):
    """Schema for unified delivery cluster CSV output from Step 36."""
    
    # Cluster identification
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    cluster_name: Series[str] = pa.Field(nullable=True)
    cluster_size: Series[int] = pa.Field(ge=0)
    
    # Product identification
    spu_code: Series[str] = pa.Field()
    spu_name: Series[str] = pa.Field(nullable=True)
    category: Series[str] = pa.Field()
    subcategory: Series[str] = pa.Field()
    
    # Cluster-level recommendations
    cluster_recommended_quantity: Series[float] = pa.Field(ge=0.0)
    cluster_current_quantity: Series[float] = pa.Field(ge=0.0)
    cluster_quantity_change: Series[float] = pa.Field()
    
    # Cluster characteristics
    cluster_style_type: Series[str] = pa.Field()  # "Fashion-Heavy", "Balanced-Mix", "Basic-Focus"
    cluster_price_band: Series[str] = pa.Field()  # "Budget", "Value", "Premium", "Luxury"
    cluster_product_role: Series[str] = pa.Field()  # "CORE", "SEASONAL", "FILLER", "CLEARANCE"
    
    # Cluster performance
    cluster_avg_sales: Series[float] = pa.Field(ge=0.0, nullable=True)
    cluster_avg_sellthrough: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    cluster_avg_inventory_turnover: Series[float] = pa.Field(ge=0.0, nullable=True)
    
    # Cluster business impact
    cluster_expected_revenue_impact: Series[float] = pa.Field(nullable=True)
    cluster_investment_required: Series[float] = pa.Field(ge=0.0, nullable=True)
    cluster_expected_roi: Series[float] = pa.Field(nullable=True)
    
    # Implementation details
    cluster_priority: Series[str] = pa.Field()  # "HIGH", "MEDIUM", "LOW"
    cluster_implementation_complexity: Series[str] = pa.Field()  # "LOW", "MEDIUM", "HIGH"
    cluster_expected_timeline: Series[str] = pa.Field()  # e.g., "1-3 months"


class UnifiedDeliveryDataDictionarySchema(pa.DataFrameModel):
    """Schema for unified delivery data dictionary from Step 36."""
    
    # Field identification
    field_name: Series[str] = pa.Field()
    field_type: Series[str] = pa.Field()  # "INTEGER", "FLOAT", "STRING", "BOOLEAN", "DATE"
    field_description: Series[str] = pa.Field()
    
    # Field properties
    is_required: Series[bool] = pa.Field()
    is_nullable: Series[bool] = pa.Field()
    min_value: Series[float] = pa.Field(nullable=True)
    max_value: Series[float] = pa.Field(nullable=True)
    allowed_values: Series[str] = pa.Field(nullable=True)  # JSON string
    
    # Business context
    business_meaning: Series[str] = pa.Field()
    calculation_method: Series[str] = pa.Field(nullable=True)
    data_source: Series[str] = pa.Field(nullable=True)
    
    # Quality requirements
    validation_rules: Series[str] = pa.Field(nullable=True)  # JSON string
    quality_thresholds: Series[str] = pa.Field(nullable=True)  # JSON string
    error_handling: Series[str] = pa.Field(nullable=True)
    
    # Usage guidance
    usage_notes: Series[str] = pa.Field(nullable=True)
    examples: Series[str] = pa.Field(nullable=True)  # JSON string
    related_fields: Series[str] = pa.Field(nullable=True)  # JSON string


