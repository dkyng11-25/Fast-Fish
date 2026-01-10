#!/usr/bin/env python3
"""
Step 32 Store Allocation Validation Schemas

This module contains schemas for store allocation validation from Step 32.

Author: Data Pipeline
Date: 2025-01-16
"""

import pandera as pa
from pandera.typing import Series


class StoreLevelAllocationResultsSchema(pa.DataFrameModel):
    """Schema for store level allocation results from Step 32 - matches expected CSV structure."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    store_group: Series[str] = pa.Field()
    
    # Product identification
    spu_code: Series[str] = pa.Field()
    category: Series[str] = pa.Field()
    subcategory: Series[str] = pa.Field()
    
    # Allocation inputs
    group_level_recommendation: Series[float] = pa.Field()
    store_sales_weight: Series[float] = pa.Field(ge=0.0, le=1.0)
    store_capacity_weight: Series[float] = pa.Field(ge=0.0, le=1.0)
    store_suitability_weight: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Allocation calculation
    combined_weight: Series[float] = pa.Field(ge=0.0, le=1.0)
    allocated_quantity: Series[float] = pa.Field(ge=0.0)
    allocation_percentage: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Current state
    current_quantity: Series[float] = pa.Field(ge=0.0)
    quantity_change: Series[float] = pa.Field()
    change_type: Series[str] = pa.Field()  # "INCREASE", "DECREASE", "MAINTAIN"
    
    # Business context
    store_sales_performance: Series[float] = pa.Field(ge=0.0, nullable=True)
    store_capacity: Series[float] = pa.Field(ge=0.0, nullable=True)
    product_suitability_score: Series[float] = pa.Field(ge=0.0, le=1.0, nullable=True)
    
    # Allocation validation
    allocation_reason: Series[str] = pa.Field()
    allocation_confidence: Series[float] = pa.Field(ge=0.0, le=1.0)
    validation_status: Series[str] = pa.Field()  # "VALID", "WARNING", "ERROR"


class StoreAllocationSummarySchema(pa.DataFrameModel):
    """Schema for store allocation summary from Step 32."""
    
    # Summary metadata
    summary_timestamp: Series[str] = pa.Field()
    analysis_period: Series[str] = pa.Field()
    total_stores_allocated: Series[int] = pa.Field(ge=0)
    total_products_allocated: Series[int] = pa.Field(ge=0)
    
    # Allocation statistics
    total_quantity_allocated: Series[float] = pa.Field(ge=0.0)
    total_increases: Series[int] = pa.Field(ge=0)
    total_decreases: Series[int] = pa.Field(ge=0)
    total_maintains: Series[int] = pa.Field(ge=0)
    
    # Weight distribution
    avg_sales_weight: Series[float] = pa.Field(ge=0.0, le=1.0)
    avg_capacity_weight: Series[float] = pa.Field(ge=0.0, le=1.0)
    avg_suitability_weight: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Allocation quality
    avg_allocation_confidence: Series[float] = pa.Field(ge=0.0, le=1.0)
    valid_allocations: Series[int] = pa.Field(ge=0)
    warning_allocations: Series[int] = pa.Field(ge=0)
    error_allocations: Series[int] = pa.Field(ge=0)
    
    # Business impact
    expected_revenue_impact: Series[float] = pa.Field(nullable=True)
    inventory_turnover_impact: Series[float] = pa.Field(nullable=True)
    capacity_utilization_impact: Series[float] = pa.Field(nullable=True)


class StoreAllocationValidationSchema(pa.DataFrameModel):
    """Schema for store allocation validation from Step 32."""
    
    # Validation metadata
    validation_timestamp: Series[str] = pa.Field()
    validation_type: Series[str] = pa.Field()  # "ALLOCATION", "WEIGHT", "CONSTRAINT"
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    
    # Validation checks
    weight_sum_valid: Series[bool] = pa.Field()
    allocation_positive: Series[bool] = pa.Field()
    capacity_constraint_satisfied: Series[bool] = pa.Field()
    business_rule_compliant: Series[bool] = pa.Field()
    
    # Validation scores
    weight_consistency_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    allocation_accuracy_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    constraint_compliance_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    overall_validation_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Validation issues
    validation_issues: Series[str] = pa.Field(nullable=True)  # JSON string
    warning_messages: Series[str] = pa.Field(nullable=True)  # JSON string
    error_messages: Series[str] = pa.Field(nullable=True)  # JSON string
    
    # Recommendations
    improvement_suggestions: Series[str] = pa.Field(nullable=True)  # JSON string
    priority_level: Series[str] = pa.Field()  # "HIGH", "MEDIUM", "LOW"


class StoreAllocationAddsSchema(pa.DataFrameModel):
    """Schema for store allocation adds from Step 32."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    store_group: Series[str] = pa.Field()
    
    # Product identification
    spu_code: Series[str] = pa.Field()
    category: Series[str] = pa.Field()
    subcategory: Series[str] = pa.Field()
    
    # Addition details
    quantity_to_add: Series[float] = pa.Field(ge=0.0)
    current_quantity: Series[float] = pa.Field(ge=0.0)
    new_quantity: Series[float] = pa.Field(ge=0.0)
    
    # Addition rationale
    addition_reason: Series[str] = pa.Field()
    priority_score: Series[float] = pa.Field(ge=0.0, le=10.0)
    expected_impact: Series[float] = pa.Field(nullable=True)
    
    # Implementation details
    implementation_priority: Series[str] = pa.Field()  # "HIGH", "MEDIUM", "LOW"
    expected_timeline: Series[str] = pa.Field()  # e.g., "1-2 weeks"
    required_investment: Series[float] = pa.Field(ge=0.0, nullable=True)


class StoreAllocationReducesSchema(pa.DataFrameModel):
    """Schema for store allocation reduces from Step 32."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    store_group: Series[str] = pa.Field()
    
    # Product identification
    spu_code: Series[str] = pa.Field()
    category: Series[str] = pa.Field()
    subcategory: Series[str] = pa.Field()
    
    # Reduction details
    quantity_to_reduce: Series[float] = pa.Field(ge=0.0)
    current_quantity: Series[float] = pa.Field(ge=0.0)
    new_quantity: Series[float] = pa.Field(ge=0.0)
    
    # Reduction rationale
    reduction_reason: Series[str] = pa.Field()
    priority_score: Series[float] = pa.Field(ge=0.0, le=10.0)
    expected_impact: Series[float] = pa.Field(nullable=True)
    
    # Implementation details
    implementation_priority: Series[str] = pa.Field()  # "HIGH", "MEDIUM", "LOW"
    expected_timeline: Series[str] = pa.Field()  # e.g., "1-2 weeks"
    cost_savings: Series[float] = pa.Field(ge=0.0, nullable=True)


