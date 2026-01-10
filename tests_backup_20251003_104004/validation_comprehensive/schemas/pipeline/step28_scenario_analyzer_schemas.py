#!/usr/bin/env python3
"""
Step 28 Scenario Analyzer Validation Schemas

This module contains schemas for scenario analysis validation from Step 28.

Author: Data Pipeline
Date: 2025-01-16
"""

import pandera as pa
from pandera.typing import Series


class ScenarioAnalysisResultsSchema(pa.DataFrameModel):
    """Schema for scenario analysis results JSON from Step 28 - matches actual JSON structure."""
    
    # Analysis metadata
    total_scenarios_analyzed: Series[int] = pa.Field(ge=0)
    analysis_timestamp: Series[str] = pa.Field()
    
    # Baseline metrics
    total_products: Series[int] = pa.Field(ge=0)
    total_sales_amount: Series[float] = pa.Field(ge=0.0)
    total_sales_quantity: Series[float] = pa.Field(ge=0.0)
    avg_sell_through_rate: Series[float] = pa.Field(ge=0.0, le=100.0)
    avg_inventory_days: Series[float] = pa.Field(ge=0.0)
    
    # Role distribution (JSON structure)
    role_distribution: Series[str] = pa.Field()  # JSON string with role statistics
    
    # Scenario results (JSON structure)
    scenario_results: Series[str] = pa.Field()  # JSON string with scenario outcomes
    
    # Analysis summary
    analysis_summary: Series[str] = pa.Field()  # JSON string with key insights


class ScenarioAnalysisReportSchema(pa.DataFrameModel):
    """Schema for scenario analysis report from Step 28."""
    
    # Report metadata
    report_timestamp: Series[str] = pa.Field()
    analysis_period: Series[str] = pa.Field()
    target_year: Series[int] = pa.Field(ge=2020, le=2030)
    
    # Scenario overview
    total_scenarios: Series[int] = pa.Field(ge=0)
    baseline_scenario: Series[str] = pa.Field()
    optimization_scenarios: Series[str] = pa.Field()  # JSON string
    
    # Key findings
    revenue_impact: Series[str] = pa.Field()  # JSON string with revenue analysis
    inventory_impact: Series[str] = pa.Field()  # JSON string with inventory analysis
    sell_through_impact: Series[str] = pa.Field()  # JSON string with sell-through analysis
    
    # Recommendations
    top_recommendations: Series[str] = pa.Field()  # JSON string
    risk_assessment: Series[str] = pa.Field()  # JSON string
    implementation_priority: Series[str] = pa.Field()  # JSON string


class ScenarioRecommendationsSchema(pa.DataFrameModel):
    """Schema for scenario recommendations CSV from Step 28."""
    
    # Scenario identification
    scenario_id: Series[str] = pa.Field()
    scenario_name: Series[str] = pa.Field()
    scenario_type: Series[str] = pa.Field()  # "optimization", "baseline", "stress_test"
    
    # Impact metrics
    revenue_change_pct: Series[float] = pa.Field()
    inventory_change_pct: Series[float] = pa.Field()
    sell_through_change_pct: Series[float] = pa.Field()
    
    # Business metrics
    roi_estimate: Series[float] = pa.Field(nullable=True)
    payback_period_months: Series[float] = pa.Field(nullable=True)
    risk_score: Series[float] = pa.Field(ge=0.0, le=10.0)
    
    # Implementation details
    implementation_complexity: Series[str] = pa.Field()  # "low", "medium", "high"
    required_investment: Series[float] = pa.Field(ge=0.0, nullable=True)
    expected_timeline: Series[str] = pa.Field()  # e.g., "1-3 months"
    
    # Recommendations
    recommendation: Series[str] = pa.Field()
    priority_level: Series[str] = pa.Field()  # "high", "medium", "low"
    success_probability: Series[float] = pa.Field(ge=0.0, le=1.0)


class ScenarioBaselineMetricsSchema(pa.DataFrameModel):
    """Schema for baseline metrics within scenario analysis."""
    
    # Product metrics
    total_products: Series[int] = pa.Field(ge=0)
    active_products: Series[int] = pa.Field(ge=0)
    discontinued_products: Series[int] = pa.Field(ge=0)
    
    # Sales metrics
    total_sales_amount: Series[float] = pa.Field(ge=0.0)
    total_sales_quantity: Series[float] = pa.Field(ge=0.0)
    avg_unit_price: Series[float] = pa.Field(ge=0.0)
    
    # Performance metrics
    avg_sell_through_rate: Series[float] = pa.Field(ge=0.0, le=100.0)
    avg_inventory_days: Series[float] = pa.Field(ge=0.0)
    inventory_turnover: Series[float] = pa.Field(ge=0.0)
    
    # Category distribution
    category_distribution: Series[str] = pa.Field()  # JSON string
    subcategory_distribution: Series[str] = pa.Field()  # JSON string
    
    # Role distribution
    role_distribution: Series[str] = pa.Field()  # JSON string with role statistics


class ScenarioOptimizationSchema(pa.DataFrameModel):
    """Schema for optimization scenarios within scenario analysis."""
    
    # Scenario identification
    scenario_id: Series[str] = pa.Field()
    scenario_name: Series[str] = pa.Field()
    optimization_type: Series[str] = pa.Field()  # "inventory", "pricing", "assortment", "mixed"
    
    # Changes applied
    products_added: Series[int] = pa.Field(ge=0)
    products_removed: Series[int] = pa.Field(ge=0)
    products_modified: Series[int] = pa.Field(ge=0)
    
    # Impact projections
    projected_revenue_change: Series[float] = pa.Field()
    projected_inventory_change: Series[float] = pa.Field()
    projected_sell_through_change: Series[float] = pa.Field()
    
    # Confidence metrics
    confidence_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    data_quality_score: Series[float] = pa.Field(ge=0.0, le=1.0)
    model_accuracy: Series[float] = pa.Field(ge=0.0, le=1.0)
    
    # Implementation details
    implementation_cost: Series[float] = pa.Field(ge=0.0)
    implementation_time: Series[str] = pa.Field()
    success_probability: Series[float] = pa.Field(ge=0.0, le=1.0)


