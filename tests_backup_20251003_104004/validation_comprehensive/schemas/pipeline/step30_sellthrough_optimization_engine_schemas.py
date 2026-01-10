#!/usr/bin/env python3
"""
Step 30 Sellthrough Optimization Engine Validation Schemas

This module contains schemas for sellthrough optimization validation from Step 30.

Author: Data Pipeline
Date: 2025-01-16
"""

import pandera as pa
from pandera.typing import Series


class SellthroughOptimizationResultsSchema(pa.DataFrameModel):
    """Schema for sellthrough optimization results JSON from Step 30 - matches actual JSON structure."""
    
    # Optimization metadata
    optimization_timestamp: Series[str] = pa.Field()
    analysis_period: Series[str] = pa.Field()
    optimization_method: Series[str] = pa.Field()  # "linear_programming", "genetic_algorithm", etc.
    
    # Baseline performance metrics
    baseline_total_clusters: Series[int] = pa.Field(ge=0)
    baseline_total_stores: Series[int] = pa.Field(ge=0)
    baseline_total_products: Series[int] = pa.Field(ge=0)
    baseline_total_sales_amt: Series[float] = pa.Field(ge=0.0)
    baseline_weighted_avg_sellthrough_rate: Series[float] = pa.Field(ge=0.0, le=1.0)
    baseline_avg_capacity_utilization: Series[float] = pa.Field(ge=0.0, le=1.0)
    baseline_avg_products_per_store: Series[float] = pa.Field(ge=0.0)
    
    # Optimized performance metrics
    optimized_total_clusters: Series[int] = pa.Field(ge=0)
    optimized_total_stores: Series[int] = pa.Field(ge=0)
    optimized_total_products: Series[int] = pa.Field(ge=0)
    optimized_total_sales_amt: Series[float] = pa.Field(ge=0.0)
    optimized_weighted_avg_sellthrough_rate: Series[float] = pa.Field(ge=0.0, le=1.0)
    optimized_avg_capacity_utilization: Series[float] = pa.Field(ge=0.0, le=1.0)
    optimized_avg_products_per_store: Series[float] = pa.Field(ge=0.0)
    
    # Improvement metrics
    sellthrough_improvement: Series[float] = pa.Field(ge=0.0)
    capacity_utilization_improvement: Series[float] = pa.Field(ge=0.0)
    revenue_improvement: Series[float] = pa.Field(ge=0.0)
    
    # Optimization details
    optimization_status: Series[str] = pa.Field()  # "success", "partial", "failed"
    optimization_time_seconds: Series[float] = pa.Field(ge=0.0)
    iterations_completed: Series[int] = pa.Field(ge=0)
    convergence_achieved: Series[bool] = pa.Field()


class SellthroughOptimizationReportSchema(pa.DataFrameModel):
    """Schema for sellthrough optimization report from Step 30."""
    
    # Report metadata
    report_timestamp: Series[str] = pa.Field()
    analysis_period: Series[str] = pa.Field()
    optimization_engine_version: Series[str] = pa.Field()
    
    # Optimization summary
    total_scenarios_tested: Series[int] = pa.Field(ge=0)
    successful_optimizations: Series[int] = pa.Field(ge=0)
    failed_optimizations: Series[int] = pa.Field(ge=0)
    
    # Performance improvements
    avg_sellthrough_improvement: Series[float] = pa.Field(ge=0.0)
    max_sellthrough_improvement: Series[float] = pa.Field(ge=0.0)
    avg_capacity_improvement: Series[float] = pa.Field(ge=0.0)
    avg_revenue_improvement: Series[float] = pa.Field(ge=0.0)
    
    # Cluster-level improvements
    cluster_improvements: Series[str] = pa.Field()  # JSON string
    store_improvements: Series[str] = pa.Field()  # JSON string
    product_improvements: Series[str] = pa.Field()  # JSON string
    
    # Recommendations
    top_recommendations: Series[str] = pa.Field()  # JSON string
    implementation_priority: Series[str] = pa.Field()  # JSON string
    expected_roi: Series[float] = pa.Field(nullable=True)


class BeforeAfterOptimizationComparisonSchema(pa.DataFrameModel):
    """Schema for before/after optimization comparison from Step 30."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    cluster_id: Series[int] = pa.Field(ge=0, le=50)
    
    # Product identification
    spu_code: Series[str] = pa.Field()
    category: Series[str] = pa.Field()
    subcategory: Series[str] = pa.Field()
    
    # Before optimization
    before_quantity: Series[float] = pa.Field(ge=0.0)
    before_sellthrough_rate: Series[float] = pa.Field(ge=0.0, le=1.0)
    before_sales_amount: Series[float] = pa.Field(ge=0.0)
    before_capacity_utilization: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # After optimization
    after_quantity: Series[float] = pa.Field(ge=0.0)
    after_sellthrough_rate: Series[float] = pa.Field(ge=0.0, le=1.0)
    after_sales_amount: Series[float] = pa.Field(ge=0.0)
    after_capacity_utilization: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Changes
    quantity_change: Series[float] = pa.Field()
    sellthrough_change: Series[float] = pa.Field()
    sales_change: Series[float] = pa.Field()
    capacity_change: Series[float] = pa.Field()
    
    # Optimization impact
    improvement_score: Series[float] = pa.Field(ge=0.0, le=10.0)
    optimization_priority: Series[str] = pa.Field()  # "high", "medium", "low"
    recommendation: Series[str] = pa.Field()


class OptimizationConstraintsSchema(pa.DataFrameModel):
    """Schema for optimization constraints from Step 30."""
    
    # Constraint identification
    constraint_id: Series[str] = pa.Field()
    constraint_type: Series[str] = pa.Field()  # "inventory", "capacity", "category_mix", "business_rule"
    constraint_name: Series[str] = pa.Field()
    
    # Constraint parameters
    min_value: Series[float] = pa.Field(nullable=True)
    max_value: Series[float] = pa.Field(nullable=True)
    target_value: Series[float] = pa.Field(nullable=True)
    weight: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Constraint status
    is_active: Series[bool] = pa.Field()
    is_violated: Series[bool] = pa.Field()
    violation_severity: Series[float] = pa.Field(ge=0.0, le=10.0)
    
    # Constraint scope
    applies_to_clusters: Series[str] = pa.Field()  # JSON string
    applies_to_stores: Series[str] = pa.Field()  # JSON string
    applies_to_products: Series[str] = pa.Field()  # JSON string
    
    # Constraint impact
    impact_on_objective: Series[float] = pa.Field()
    relaxation_penalty: Series[float] = pa.Field(ge=0.0)


class OptimizationMetricsSchema(pa.DataFrameModel):
    """Schema for optimization metrics from Step 30."""
    
    # Metric identification
    metric_name: Series[str] = pa.Field()
    metric_type: Series[str] = pa.Field()  # "objective", "constraint", "performance"
    metric_category: Series[str] = pa.Field()  # "sellthrough", "capacity", "revenue", "inventory"
    
    # Metric values
    baseline_value: Series[float] = pa.Field()
    optimized_value: Series[float] = pa.Field()
    improvement: Series[float] = pa.Field()
    improvement_pct: Series[float] = pa.Field(ge=0.0)
    
    # Metric quality
    confidence_level: Series[float] = pa.Field(ge=0.0, le=1.0)
    data_quality_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    statistical_significance: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Metric context
    unit_of_measure: Series[str] = pa.Field()
    calculation_method: Series[str] = pa.Field()
    last_updated: Series[str] = pa.Field()


