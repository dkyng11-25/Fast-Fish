#!/usr/bin/env python3
"""
Step 33 Store Level Merchandising Rules Validation Schemas

This module contains schemas for store level merchandising rules validation from Step 33.

Author: Data Pipeline
Date: 2025-01-16
"""

import pandera as pa
from pandera.typing import Series


class StoreLevelMerchandisingRulesSchema(pa.DataFrameModel):
    """Schema for store level merchandising rules from Step 33 - matches expected CSV structure."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    store_group: Series[str] = pa.Field()
    store_name: Series[str] = pa.Field(nullable=True)
    
    # Store attributes
    store_size: Series[str] = pa.Field(nullable=True)  # "Small", "Medium", "Large"
    location_type: Series[str] = pa.Field(nullable=True)  # "Urban", "Suburban", "Rural"
    customer_demographics: Series[str] = pa.Field(nullable=True)  # JSON string
    
    # Style allocation rules
    fashion_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    basic_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    style_allocation_type: Series[str] = pa.Field()  # "Fashion-Heavy", "Balanced-Mix", "Basic-Focus"
    
    # Price band allocation rules
    budget_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    value_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    premium_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    luxury_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Product role allocation rules
    core_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    seasonal_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    filler_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    clearance_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Seasonal allocation rules
    spring_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    summer_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    fall_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    winter_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    all_season_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Gender allocation rules
    men_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    women_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    unisex_ratio: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Category allocation rules
    category_allocations: Series[str] = pa.Field()  # JSON string with category ratios
    subcategory_allocations: Series[str] = pa.Field()  # JSON string with subcategory ratios
    
    # Business rules
    min_inventory_turnover: Series[float] = pa.Field(ge=0.0, nullable=True)
    max_inventory_days: Series[float] = pa.Field(ge=0.0, nullable=True)
    min_sellthrough_rate: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    
    # Capacity constraints
    max_total_products: Series[int] = pa.Field(ge=0, nullable=True)
    max_products_per_category: Series[int] = pa.Field(ge=0, nullable=True)
    max_products_per_subcategory: Series[int] = pa.Field(ge=0, nullable=True)
    
    # Implementation details
    rule_priority: Series[str] = pa.Field()  # "HIGH", "MEDIUM", "LOW"
    rule_confidence: Series[float] = pa.Field(ge=0.0, le=1.0)
    last_updated: Series[str] = pa.Field()


class StoreLevelMerchandisingRulesReportSchema(pa.DataFrameModel):
    """Schema for store level merchandising rules report from Step 33."""
    
    # Report metadata
    report_timestamp: Series[str] = pa.Field()
    analysis_period: Series[str] = pa.Field()
    total_stores_analyzed: Series[int] = pa.Field(ge=0)
    total_rules_generated: Series[int] = pa.Field(ge=0)
    
    # Rule distribution
    high_priority_rules: Series[int] = pa.Field(ge=0)
    medium_priority_rules: Series[int] = pa.Field(ge=0)
    low_priority_rules: Series[int] = pa.Field(ge=0)
    
    # Style allocation summary
    fashion_heavy_stores: Series[int] = pa.Field(ge=0)
    balanced_mix_stores: Series[int] = pa.Field(ge=0)
    basic_focus_stores: Series[int] = pa.Field(ge=0)
    
    # Price band allocation summary
    budget_focused_stores: Series[int] = pa.Field(ge=0)
    value_focused_stores: Series[int] = pa.Field(ge=0)
    premium_focused_stores: Series[int] = pa.Field(ge=0)
    luxury_focused_stores: Series[int] = pa.Field(ge=0)
    
    # Product role allocation summary
    core_focused_stores: Series[int] = pa.Field(ge=0)
    seasonal_focused_stores: Series[int] = pa.Field(ge=0)
    filler_focused_stores: Series[int] = pa.Field(ge=0)
    clearance_focused_stores: Series[int] = pa.Field(ge=0)
    
    # Rule quality metrics
    avg_rule_confidence: Series[float] = pa.Field(ge=0.0, le=1.0)
    high_confidence_rules: Series[int] = pa.Field(ge=0)
    medium_confidence_rules: Series[int] = pa.Field(ge=0)
    low_confidence_rules: Series[int] = pa.Field(ge=0)
    
    # Business impact
    expected_inventory_optimization: Series[float] = pa.Field(nullable=True)
    expected_sellthrough_improvement: Series[float] = pa.Field(nullable=True)
    expected_revenue_impact: Series[float] = pa.Field(nullable=True)
    
    # Recommendations
    top_recommendations: Series[str] = pa.Field()  # JSON string
    implementation_priority: Series[str] = pa.Field()  # JSON string
    success_metrics: Series[str] = pa.Field()  # JSON string


class MerchandisingRuleValidationSchema(pa.DataFrameModel):
    """Schema for merchandising rule validation from Step 33."""
    
    # Validation metadata
    validation_timestamp: Series[str] = pa.Field()
    store_id: Series[int] = pa.Field(ge=10000, le=99999)
    rule_type: Series[str] = pa.Field()  # "STYLE", "PRICE", "ROLE", "SEASONAL", "GENDER"
    
    # Rule validation
    ratio_sum_valid: Series[bool] = pa.Field()
    ratio_range_valid: Series[bool] = pa.Field()
    business_rule_compliant: Series[bool] = pa.Field()
    constraint_satisfied: Series[bool] = pa.Field()
    
    # Validation scores
    ratio_consistency_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    business_logic_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    constraint_compliance_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    overall_validation_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Validation issues
    validation_issues: Series[str] = pa.Field(nullable=True)  # JSON string
    warning_messages: Series[str] = pa.Field(nullable=True)  # JSON string
    error_messages: Series[str] = pa.Field(nullable=True)  # JSON string
    
    # Recommendations
    improvement_suggestions: Series[str] = pa.Field(nullable=True)  # JSON string
    priority_level: Series[str] = pa.Field()  # "HIGH", "MEDIUM", "LOW"


class StoreClusterMerchandisingProfileSchema(pa.DataFrameModel):
    """Schema for store cluster merchandising profile from Step 33."""
    
    # Cluster identification
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    cluster_name: Series[str] = pa.Field(nullable=True)
    cluster_size: Series[int] = pa.Field(ge=0)
    
    # Cluster merchandising profile
    dominant_style_type: Series[str] = pa.Field()  # "Fashion-Heavy", "Balanced-Mix", "Basic-Focus"
    dominant_price_band: Series[str] = pa.Field()  # "Budget", "Value", "Premium", "Luxury"
    dominant_product_role: Series[str] = pa.Field()  # "CORE", "SEASONAL", "FILLER", "CLEARANCE"
    
    # Cluster characteristics
    avg_store_size: Series[str] = pa.Field()  # "Small", "Medium", "Large"
    dominant_location_type: Series[str] = pa.Field()  # "Urban", "Suburban", "Rural"
    customer_demographics: Series[str] = pa.Field()  # JSON string
    
    # Performance metrics
    avg_sales_performance: Series[float] = pa.Field(ge=0.0, nullable=True)
    avg_sellthrough_rate: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    avg_inventory_turnover: Series[float] = pa.Field(ge=0.0, nullable=True)
    
    # Rule recommendations
    recommended_style_allocations: Series[str] = pa.Field()  # JSON string
    recommended_price_allocations: Series[str] = pa.Field()  # JSON string
    recommended_role_allocations: Series[str] = pa.Field()  # JSON string
    
    # Implementation guidance
    implementation_priority: Series[str] = pa.Field()  # "HIGH", "MEDIUM", "LOW"
    expected_impact: Series[float] = pa.Field(nullable=True)
    implementation_complexity: Series[str] = pa.Field()  # "LOW", "MEDIUM", "HIGH"


