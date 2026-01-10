#!/usr/bin/env python3
"""
Step 37 Customer Delivery Formatter Validation Schemas

This module contains schemas for customer delivery formatter validation from Step 37.

Author: Data Pipeline
Date: 2025-01-16
"""

import pandera as pa
from pandera.typing import Series


class CustomerDeliveryFormattedSchema(pa.DataFrameModel):
    """Schema for customer delivery formatted output from Step 37 - matches expected CSV structure."""
    
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


class CustomerDeliverySummarySchema(pa.DataFrameModel):
    """Schema for customer delivery summary from Step 37."""
    
    # Summary metadata
    summary_timestamp: Series[str] = pa.Field()
    analysis_period: Series[str] = pa.Field()
    total_stores_processed: Series[int] = pa.Field(ge=0)
    total_products_processed: Series[int] = pa.Field(ge=0)
    
    # Recommendation summary
    total_increases: Series[int] = pa.Field(ge=0)
    total_decreases: Series[int] = pa.Field(ge=0)
    total_maintains: Series[int] = pa.Field(ge=0)
    
    # Business impact summary
    total_expected_revenue_impact: Series[float] = pa.Field(nullable=True)
    total_investment_required: Series[float] = pa.Field(ge=0.0, nullable=True)
    avg_expected_roi: Series[float] = pa.Field(nullable=True)
    
    # Priority distribution
    high_priority_recommendations: Series[int] = pa.Field(ge=0)
    medium_priority_recommendations: Series[int] = pa.Field(ge=0)
    low_priority_recommendations: Series[int] = pa.Field(ge=0)
    
    # Implementation timeline
    immediate_actions: Series[int] = pa.Field(ge=0)  # 1-2 weeks
    short_term_actions: Series[int] = pa.Field(ge=0)  # 1-3 months
    long_term_actions: Series[int] = pa.Field(ge=0)  # 3+ months
    
    # Quality metrics
    avg_data_quality_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    valid_recommendations: Series[int] = pa.Field(ge=0)
    warning_recommendations: Series[int] = pa.Field(ge=0)
    error_recommendations: Series[int] = pa.Field(ge=0)
    
    # Success metrics
    expected_sellthrough_improvement: Series[float] = pa.Field(nullable=True)
    expected_inventory_optimization: Series[float] = pa.Field(nullable=True)
    expected_customer_satisfaction_impact: Series[float] = pa.Field(nullable=True)


class CustomerDeliveryValidationSchema(pa.DataFrameModel):
    """Schema for customer delivery validation from Step 37."""
    
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


class CustomerDeliveryReportSchema(pa.DataFrameModel):
    """Schema for customer delivery report from Step 37."""
    
    # Report metadata
    report_timestamp: Series[str] = pa.Field()
    analysis_period: Series[str] = pa.Field()
    report_type: Series[str] = pa.Field()  # "EXECUTIVE", "OPERATIONAL", "TECHNICAL"
    
    # Executive summary
    total_recommendations: Series[int] = pa.Field(ge=0)
    high_priority_recommendations: Series[int] = pa.Field(ge=0)
    expected_business_impact: Series[str] = pa.Field()  # JSON string
    
    # Operational details
    store_level_breakdown: Series[str] = pa.Field()  # JSON string
    product_level_breakdown: Series[str] = pa.Field()  # JSON string
    cluster_level_breakdown: Series[str] = pa.Field()  # JSON string
    
    # Implementation guidance
    implementation_roadmap: Series[str] = pa.Field()  # JSON string
    resource_requirements: Series[str] = pa.Field()  # JSON string
    success_metrics: Series[str] = pa.Field()  # JSON string
    
    # Risk assessment
    implementation_risks: Series[str] = pa.Field()  # JSON string
    mitigation_strategies: Series[str] = pa.Field()  # JSON string
    contingency_plans: Series[str] = pa.Field()  # JSON string
    
    # Quality assurance
    data_quality_assessment: Series[str] = pa.Field()  # JSON string
    validation_results: Series[str] = pa.Field()  # JSON string
    quality_improvements: Series[str] = pa.Field()  # JSON string


class CustomerDeliveryMetricsSchema(pa.DataFrameModel):
    """Schema for customer delivery metrics from Step 37."""
    
    # Metrics identification
    metric_name: Series[str] = pa.Field()
    metric_type: Series[str] = pa.Field()  # "PERFORMANCE", "QUALITY", "BUSINESS", "OPERATIONAL"
    metric_category: Series[str] = pa.Field()  # "SALES", "INVENTORY", "CUSTOMER", "FINANCIAL"
    
    # Metric values
    current_value: Series[float] = pa.Field()
    target_value: Series[float] = pa.Field(nullable=True)
    baseline_value: Series[float] = pa.Field(nullable=True)
    
    # Metric analysis
    improvement: Series[float] = pa.Field(nullable=True)
    improvement_pct: Series[float] = pa.Field(ge=0.0, nullable=True)
    trend_direction: Series[str] = pa.Field(nullable=True)  # "UP", "DOWN", "STABLE"
    
    # Metric quality
    confidence_level: Series[float] = pa.Field(ge=0.0, le=1.0)
    data_quality_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    statistical_significance: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Metric context
    unit_of_measure: Series[str] = pa.Field()
    calculation_method: Series[str] = pa.Field()
    last_updated: Series[str] = pa.Field()
    
    # Business impact
    business_impact: Series[str] = pa.Field(nullable=True)  # JSON string
    action_required: Series[str] = pa.Field(nullable=True)
    priority_level: Series[str] = pa.Field(nullable=True)  # "HIGH", "MEDIUM", "LOW"


