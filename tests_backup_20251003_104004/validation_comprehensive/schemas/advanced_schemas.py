import pandas as pd
#!/usr/bin/env python3
"""
Advanced Schemas for Steps 15-36

This module provides comprehensive pandera schemas for the advanced pipeline steps (15-36)
including historical analysis, dashboards, merchandising optimization, and delivery systems.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series, DataFrame
from typing import Optional, List, Dict, Any
import pandas as pd

# Import common schemas
from .common_schemas import (
    StoreCodeSchema, SalesAmountSchema, QuantitySchema, PriceSchema, CountSchema
)
from .time_schemas import PeriodSchema

# Define missing common schemas
class SPUCodeSchema(pa.DataFrameModel):
    """Schema for SPU code validation."""
    spu_code: Series[str] = pa.Field(description="SPU code identifier")

class SubcategorySchema(pa.DataFrameModel):
    """Schema for subcategory validation."""
    sub_cate_name: Series[str] = pa.Field(description="Subcategory name")

class ClusterIdSchema(pa.DataFrameModel):
    """Schema for cluster ID validation."""
    cluster_id: Series[int] = pa.Field(ge=1, description="Cluster identifier")

# ============================================================================
# STEP 15: HISTORICAL BASELINE SCHEMAS
# ============================================================================

class HistoricalBaselineSchema(pa.DataFrameModel):
    """Schema for historical baseline data."""
    str_code: Series[str] = pa.Field(description="Store code")
    period: Series[str] = pa.Field(description="Period identifier")
    baseline_value: Series[float] = pa.Field(ge=0, description="Baseline value")
    current_value: Series[float] = pa.Field(ge=0, description="Current value")
    change_pct: Series[float] = pa.Field(ge=-100, le=1000, description="Change percentage")
    confidence: Series[float] = pa.Field(ge=0, le=1, description="Confidence score")
    data_quality: Series[str] = pa.Field(description="Data quality indicator")

class HistoricalInsightsSchema(pa.DataFrameModel):
    """Schema for historical insights data."""
    period: Series[str] = pa.Field(description="Period identifier")
    insight_type: Series[str] = pa.Field(description="Type of insight")
    insight_value: Series[float] = pa.Field(description="Insight value")
    significance: Series[str] = pa.Field(description="Significance level")
    trend_direction: Series[str] = pa.Field(description="Trend direction")


class HistoricalAnalysisSchema(pa.DataFrameModel):
    """Schema for historical analysis data."""
    str_code: Series[str] = pa.Field(description="Store code")
    period: Series[str] = pa.Field(description="Period identifier")
    analysis_type: Series[str] = pa.Field(description="Type of analysis")
    analysis_value: Series[float] = pa.Field(description="Analysis value")
    trend: Series[str] = pa.Field(description="Trend direction")
    significance: Series[float] = pa.Field(ge=0, le=1, description="Statistical significance")

# ============================================================================
# STEP 16: COMPARISON TABLES SCHEMAS
# ============================================================================

class ComparisonTableSchema(pa.DataFrameModel):
    """Schema for comparison table data."""
    str_code: Series[str] = pa.Field(description="Store code")
    metric_name: Series[str] = pa.Field(description="Metric name")
    current_value: Series[float] = pa.Field(description="Current value")
    baseline_value: Series[float] = pa.Field(description="Baseline value")
    comparison: Series[str] = pa.Field(description="Comparison result")
    variance_pct: Series[float] = pa.Field(ge=-100, le=1000, description="Variance percentage")
    significance: Series[str] = pa.Field(description="Statistical significance")

class ComparisonMetricsSchema(pa.DataFrameModel):
    """Schema for comparison metrics."""
    metric_category: Series[str] = pa.Field(description="Metric category")
    total_stores: Series[int] = pa.Field(ge=0, description="Total stores")
    improved_stores: Series[int] = pa.Field(ge=0, description="Improved stores")
    declined_stores: Series[int] = pa.Field(ge=0, description="Declined stores")
    improvement_rate: Series[float] = pa.Field(ge=0, le=100, description="Improvement rate")

# ============================================================================
# STEP 17: AUGMENT RECOMMENDATIONS SCHEMAS
# ============================================================================

class AugmentedRecommendationSchema(pa.DataFrameModel):
    """Schema for augmented recommendations."""
    str_code: Series[str] = pa.Field(description="Store code")
    spu_code: Series[str] = pa.Field(description="SPU code")
    recommendation_type: Series[str] = pa.Field(description="Type of recommendation")
    priority: Series[str] = pa.Field(description="Priority level")
    confidence: Series[float] = pa.Field(ge=0, le=1, description="Confidence score")
    impact_score: Series[float] = pa.Field(ge=0, le=10, description="Impact score")
    implementation_cost: Series[float] = pa.Field(ge=0, description="Implementation cost")
    expected_roi: Series[float] = pa.Field(description="Expected ROI")

class RecommendationMetadataSchema(pa.DataFrameModel):
    """Schema for recommendation metadata."""
    recommendation_id: Series[str] = pa.Field(description="Recommendation ID")
    category: Series[str] = pa.Field(description="Recommendation category")
    subcategory: Series[str] = pa.Field(description="Recommendation subcategory")
    complexity: Series[str] = pa.Field(description="Implementation complexity")
    timeframe: Series[str] = pa.Field(description="Implementation timeframe")

# ============================================================================
# STEP 18: VALIDATE RESULTS SCHEMAS
# ============================================================================

class ValidationSummarySchema(pa.DataFrameModel):
    """Schema for validation summary."""
    validation_type: Series[str] = pa.Field(description="Type of validation")
    status: Series[str] = pa.Field(description="Validation status")
    count: Series[int] = pa.Field(ge=0, description="Count of items")
    percentage: Series[float] = pa.Field(ge=0, le=100, description="Percentage")
    threshold: Series[float] = pa.Field(ge=0, le=100, description="Threshold value")
    passed: Series[bool] = pa.Field(description="Whether validation passed")

class ValidationDetailsSchema(pa.DataFrameModel):
    """Schema for validation details."""
    validation_id: Series[str] = pa.Field(description="Validation ID")
    entity_type: Series[str] = pa.Field(description="Entity type")
    entity_id: Series[str] = pa.Field(description="Entity ID")
    validation_rule: Series[str] = pa.Field(description="Validation rule")
    actual_value: Series[float] = pa.Field(description="Actual value")
    expected_value: Series[float] = pa.Field(description="Expected value")
    deviation: Series[float] = pa.Field(description="Deviation from expected")

# ============================================================================
# STEP 19: DETAILED SPU BREAKDOWN SCHEMAS
# ============================================================================

class DetailedSPUBreakdownSchema(pa.DataFrameModel):
    """Schema for detailed SPU breakdown."""
    spu_code: Series[str] = pa.Field(description="SPU code")
    str_code: Series[str] = pa.Field(description="Store code")
    category: Series[str] = pa.Field(description="Product category")
    subcategory: Series[str] = pa.Field(description="Product subcategory")
    performance_metrics: Series[str] = pa.Field(description="Performance metrics")
    sales_volume: Series[float] = pa.Field(ge=0, description="Sales volume")
    revenue: Series[float] = pa.Field(ge=0, description="Revenue")
    margin: Series[float] = pa.Field(description="Profit margin")
    sell_through_rate: Series[float] = pa.Field(ge=0, le=100, description="Sell-through rate")

class SPUPerformanceMetricsSchema(pa.DataFrameModel):
    """Schema for SPU performance metrics."""
    spu_code: Series[str] = pa.Field(description="SPU code")
    metric_name: Series[str] = pa.Field(description="Metric name")
    metric_value: Series[float] = pa.Field(description="Metric value")
    percentile_rank: Series[float] = pa.Field(ge=0, le=100, description="Percentile rank")
    benchmark_value: Series[float] = pa.Field(description="Benchmark value")
    performance_tier: Series[str] = pa.Field(description="Performance tier")

# ============================================================================
# STEP 20: DATA VALIDATION SCHEMAS
# ============================================================================

class DataQualityMetricsSchema(pa.DataFrameModel):
    """Schema for data quality metrics."""
    metric_name: Series[str] = pa.Field(description="Metric name")
    value: Series[float] = pa.Field(description="Metric value")
    threshold: Series[float] = pa.Field(description="Threshold value")
    status: Series[str] = pa.Field(description="Status (pass/fail)")
    description: Series[str] = pa.Field(description="Description")
    severity: Series[str] = pa.Field(description="Severity level")

class DataValidationErrorsSchema(pa.DataFrameModel):
    """Schema for data validation errors."""
    error_id: Series[str] = pa.Field(description="Error ID")
    error_type: Series[str] = pa.Field(description="Error type")
    entity_type: Series[str] = pa.Field(description="Entity type")
    entity_id: Series[str] = pa.Field(description="Entity ID")
    error_message: Series[str] = pa.Field(description="Error message")
    severity: Series[str] = pa.Field(description="Severity level")
    resolution: Series[str] = pa.Field(description="Resolution suggestion")

# ============================================================================
# STEPS 21-24: LABELING AND ANALYSIS SCHEMAS
# ============================================================================

class LabelTagRecommendationSchema(pa.DataFrameModel):
    """Schema for label tag recommendations."""
    str_code: Series[str] = pa.Field(description="Store code")
    label_type: Series[str] = pa.Field(description="Label type")
    label_value: Series[str] = pa.Field(description="Label value")
    confidence: Series[float] = pa.Field(ge=0, le=1, description="Confidence score")
    source: Series[str] = pa.Field(description="Source of recommendation")
    priority: Series[str] = pa.Field(description="Priority level")
    implementation_status: Series[str] = pa.Field(description="Implementation status")

class StoreAttributeEnrichmentSchema(pa.DataFrameModel):
    """Schema for store attribute enrichment."""
    str_code: Series[str] = pa.Field(description="Store code")
    attribute_name: Series[str] = pa.Field(description="Attribute name")
    attribute_value: Series[str] = pa.Field(description="Attribute value")
    enrichment_source: Series[str] = pa.Field(description="Enrichment source")
    confidence: Series[float] = pa.Field(ge=0, le=1, description="Confidence score")
    last_updated: Series[str] = pa.Field(description="Last updated timestamp")

class ClusteringFeaturesSchema(pa.DataFrameModel):
    """Schema for clustering features."""
    str_code: Series[str] = pa.Field(description="Store code")
    feature_name: Series[str] = pa.Field(description="Feature name")
    feature_value: Series[float] = pa.Field(description="Feature value")
    feature_type: Series[str] = pa.Field(description="Feature type")
    importance_score: Series[float] = pa.Field(ge=0, le=1, description="Importance score")
    normalized_value: Series[float] = pa.Field(ge=0, le=1, description="Normalized value")

class ComprehensiveClusterLabelsSchema(pa.DataFrameModel):
    """Schema for comprehensive cluster labels."""
    str_code: Series[str] = pa.Field(description="Store code")
    cluster_id: Series[int] = pa.Field(ge=1, description="Cluster ID")
    cluster_name: Series[str] = pa.Field(description="Cluster name")
    label_category: Series[str] = pa.Field(description="Label category")
    label_value: Series[str] = pa.Field(description="Label value")
    confidence: Series[float] = pa.Field(ge=0, le=1, description="Confidence score")
    label_source: Series[str] = pa.Field(description="Label source")

# ============================================================================
# STEPS 25-29: ANALYSIS AND OPTIMIZATION SCHEMAS
# ============================================================================

class ProductRoleClassifierSchema(pa.DataFrameModel):
    """Schema for product role classifier."""
    spu_code: Series[str] = pa.Field(description="SPU code")
    str_code: Series[str] = pa.Field(description="Store code")
    product_role: Series[str] = pa.Field(description="Product role")
    role_confidence: Series[float] = pa.Field(ge=0, le=1, description="Role confidence")
    performance_tier: Series[str] = pa.Field(description="Performance tier")
    strategic_importance: Series[str] = pa.Field(description="Strategic importance")
    lifecycle_stage: Series[str] = pa.Field(description="Lifecycle stage")

class PriceElasticityAnalysisSchema(pa.DataFrameModel):
    """Schema for price elasticity analysis."""
    spu_code: Series[str] = pa.Field(description="SPU code")
    str_code: Series[str] = pa.Field(description="Store code")
    current_price: Series[float] = pa.Field(gt=0, description="Current price")
    elasticity_coefficient: Series[float] = pa.Field(description="Elasticity coefficient")
    price_sensitivity: Series[str] = pa.Field(description="Price sensitivity level")
    optimal_price: Series[float] = pa.Field(gt=0, description="Optimal price")
    price_change_impact: Series[float] = pa.Field(description="Price change impact")

class GapMatrixSchema(pa.DataFrameModel):
    """Schema for gap matrix analysis."""
    str_code: Series[str] = pa.Field(description="Store code")
    spu_code: Series[str] = pa.Field(description="SPU code")
    gap_type: Series[str] = pa.Field(description="Gap type")
    current_value: Series[float] = pa.Field(description="Current value")
    target_value: Series[float] = pa.Field(description="Target value")
    gap_size: Series[float] = pa.Field(description="Gap size")
    gap_priority: Series[str] = pa.Field(description="Gap priority")
    gap_impact: Series[float] = pa.Field(description="Gap impact")

class ScenarioAnalysisSchema(pa.DataFrameModel):
    """Schema for scenario analysis."""
    scenario_id: Series[str] = pa.Field(description="Scenario ID")
    scenario_name: Series[str] = pa.Field(description="Scenario name")
    scenario_type: Series[str] = pa.Field(description="Scenario type")
    probability: Series[float] = pa.Field(ge=0, le=1, description="Probability")
    impact_score: Series[float] = pa.Field(ge=0, le=10, description="Impact score")
    risk_level: Series[str] = pa.Field(description="Risk level")
    mitigation_strategy: Series[str] = pa.Field(description="Mitigation strategy")

class SupplyDemandGapSchema(pa.DataFrameModel):
    """Schema for supply-demand gap analysis."""
    str_code: Series[str] = pa.Field(description="Store code")
    spu_code: Series[str] = pa.Field(description="SPU code")
    demand_forecast: Series[float] = pa.Field(ge=0, description="Demand forecast")
    supply_capacity: Series[float] = pa.Field(ge=0, description="Supply capacity")
    gap_amount: Series[float] = pa.Field(description="Gap amount")
    gap_type: Series[str] = pa.Field(description="Gap type (shortage/surplus)")
    urgency_level: Series[str] = pa.Field(description="Urgency level")
    recommended_action: Series[str] = pa.Field(description="Recommended action")

# ============================================================================
# STEPS 30-36: MERCHANDISING AND DELIVERY SCHEMAS
# ============================================================================

class OptimizationSchema(pa.DataFrameModel):
    """Schema for general optimization data."""
    str_code: Series[str] = pa.Field(description="Store code")
    spu_code: Series[str] = pa.Field(description="SPU code")
    optimization_type: Series[str] = pa.Field(description="Optimization type")
    current_value: Series[float] = pa.Field(description="Current value")
    target_value: Series[float] = pa.Field(description="Target value")
    optimization_potential: Series[float] = pa.Field(ge=0, description="Optimization potential")
    status: Series[str] = pa.Field(description="Optimization status")


class SellthroughOptimizationSchema(pa.DataFrameModel):
    """Schema for sellthrough optimization."""
    str_code: Series[str] = pa.Field(description="Store code")
    spu_code: Series[str] = pa.Field(description="SPU code")
    current_sellthrough: Series[float] = pa.Field(ge=0, le=100, description="Current sellthrough rate")
    target_sellthrough: Series[float] = pa.Field(ge=0, le=100, description="Target sellthrough rate")
    optimization_potential: Series[float] = pa.Field(ge=0, description="Optimization potential")
    recommended_action: Series[str] = pa.Field(description="Recommended action")
    expected_improvement: Series[float] = pa.Field(description="Expected improvement")
    implementation_cost: Series[float] = pa.Field(ge=0, description="Implementation cost")

class GapAnalysisWorkbookSchema(pa.DataFrameModel):
    """Schema for gap analysis workbook."""
    analysis_id: Series[str] = pa.Field(description="Analysis ID")
    str_code: Series[str] = pa.Field(description="Store code")
    analysis_type: Series[str] = pa.Field(description="Analysis type")
    gap_category: Series[str] = pa.Field(description="Gap category")
    current_state: Series[float] = pa.Field(description="Current state")
    target_state: Series[float] = pa.Field(description="Target state")
    gap_size: Series[float] = pa.Field(description="Gap size")
    priority_score: Series[float] = pa.Field(ge=0, le=10, description="Priority score")

class EnhancedStoreClusteringSchema(pa.DataFrameModel):
    """Schema for enhanced store clustering."""
    str_code: Series[str] = pa.Field(description="Store code")
    cluster_id: Series[int] = pa.Field(ge=1, description="Cluster ID")
    cluster_name: Series[str] = pa.Field(description="Cluster name")
    cluster_type: Series[str] = pa.Field(description="Cluster type")
    similarity_score: Series[float] = pa.Field(ge=0, le=1, description="Similarity score")
    cluster_stability: Series[str] = pa.Field(description="Cluster stability")
    migration_risk: Series[str] = pa.Field(description="Migration risk")

class StoreAllocationSchema(pa.DataFrameModel):
    """Schema for store allocation."""
    str_code: Series[str] = pa.Field(description="Store code")
    spu_code: Series[str] = pa.Field(description="SPU code")
    current_allocation: Series[float] = pa.Field(ge=0, description="Current allocation")
    optimal_allocation: Series[float] = pa.Field(ge=0, description="Optimal allocation")
    allocation_gap: Series[float] = pa.Field(description="Allocation gap")
    allocation_priority: Series[str] = pa.Field(description="Allocation priority")
    reallocation_cost: Series[float] = pa.Field(ge=0, description="Reallocation cost")


class MerchandisingSchema(pa.DataFrameModel):
    """Schema for general merchandising data."""
    str_code: Series[str] = pa.Field(description="Store code")
    spu_code: Series[str] = pa.Field(description="SPU code")
    merchandising_type: Series[str] = pa.Field(description="Merchandising type")
    merchandising_value: Series[float] = pa.Field(description="Merchandising value")
    priority: Series[int] = pa.Field(ge=1, le=10, description="Priority level")
    status: Series[str] = pa.Field(description="Status")


class StoreLevelMerchandisingSchema(pa.DataFrameModel):
    """Schema for store-level merchandising."""
    str_code: Series[str] = pa.Field(description="Store code")
    merchandising_rule: Series[str] = pa.Field(description="Merchandising rule")
    rule_priority: Series[str] = pa.Field(description="Rule priority")
    current_implementation: Series[str] = pa.Field(description="Current implementation")
    recommended_implementation: Series[str] = pa.Field(description="Recommended implementation")
    expected_impact: Series[float] = pa.Field(description="Expected impact")
    implementation_timeline: Series[str] = pa.Field(description="Implementation timeline")

class ClusterLevelMerchandisingSchema(pa.DataFrameModel):
    """Schema for cluster-level merchandising."""
    cluster_id: Series[int] = pa.Field(ge=1, description="Cluster ID")
    cluster_name: Series[str] = pa.Field(description="Cluster name")
    merchandising_strategy: Series[str] = pa.Field(description="Merchandising strategy")
    strategy_priority: Series[str] = pa.Field(description="Strategy priority")
    current_performance: Series[float] = pa.Field(description="Current performance")
    target_performance: Series[float] = pa.Field(description="Target performance")
    performance_gap: Series[float] = pa.Field(description="Performance gap")


class DeliverySchema(pa.DataFrameModel):
    """Schema for general delivery data."""
    delivery_id: Series[str] = pa.Field(description="Delivery ID")
    str_code: Series[str] = pa.Field(description="Store code")
    spu_code: Series[str] = pa.Field(description="SPU code")
    delivery_type: Series[str] = pa.Field(description="Delivery type")
    delivery_status: Series[str] = pa.Field(description="Delivery status")
    delivery_date: Series[str] = pa.Field(description="Delivery date")
    quantity: Series[float] = pa.Field(ge=0, description="Delivery quantity")


class UnifiedDeliverySchema(pa.DataFrameModel):
    """Schema for unified delivery system."""
    delivery_id: Series[str] = pa.Field(description="Delivery ID")
    str_code: Series[str] = pa.Field(description="Store code")
    delivery_type: Series[str] = pa.Field(description="Delivery type")
    delivery_priority: Series[str] = pa.Field(description="Delivery priority")
    delivery_status: Series[str] = pa.Field(description="Delivery status")
    delivery_timeline: Series[str] = pa.Field(description="Delivery timeline")
    delivery_cost: Series[float] = pa.Field(ge=0, description="Delivery cost")

class CustomerDeliveryFormatSchema(pa.DataFrameModel):
    """Schema for customer delivery format."""
    delivery_id: Series[str] = pa.Field(description="Delivery ID")
    customer_id: Series[str] = pa.Field(description="Customer ID")
    str_code: Series[str] = pa.Field(description="Store code")
    delivery_format: Series[str] = pa.Field(description="Delivery format")
    delivery_content: Series[str] = pa.Field(description="Delivery content")
    delivery_metadata: Series[str] = pa.Field(description="Delivery metadata")
    delivery_timestamp: Series[str] = pa.Field(description="Delivery timestamp")

# ============================================================================
# DASHBOARD AND VISUALIZATION SCHEMAS
# ============================================================================

class DashboardSchema(pa.DataFrameModel):
    """Schema for dashboard configuration."""
    dashboard_id: Series[str] = pa.Field(description="Dashboard ID")
    dashboard_name: Series[str] = pa.Field(description="Dashboard name")
    dashboard_type: Series[str] = pa.Field(description="Dashboard type")
    configuration: Series[str] = pa.Field(description="Dashboard configuration JSON")
    created_at: Series[str] = pa.Field(description="Creation timestamp")
    updated_at: Series[str] = pa.Field(description="Last update timestamp")


class DashboardDataSchema(pa.DataFrameModel):
    """Schema for dashboard data."""
    dashboard_id: Series[str] = pa.Field(description="Dashboard ID")
    widget_type: Series[str] = pa.Field(description="Widget type")
    data_source: Series[str] = pa.Field(description="Data source")
    metric_name: Series[str] = pa.Field(description="Metric name")
    metric_value: Series[float] = pa.Field(description="Metric value")
    visualization_type: Series[str] = pa.Field(description="Visualization type")
    refresh_frequency: Series[str] = pa.Field(description="Refresh frequency")

class InteractiveMapDataSchema(pa.DataFrameModel):
    """Schema for interactive map data."""
    str_code: Series[str] = pa.Field(description="Store code")
    latitude: Series[float] = pa.Field(ge=-90, le=90, description="Latitude")
    longitude: Series[float] = pa.Field(ge=-180, le=180, description="Longitude")
    cluster_id: Series[int] = pa.Field(ge=1, description="Cluster ID")
    performance_score: Series[float] = pa.Field(ge=0, le=10, description="Performance score")
    map_marker_type: Series[str] = pa.Field(description="Map marker type")
    popup_content: Series[str] = pa.Field(description="Popup content")

# ============================================================================
# EXPORT ALL SCHEMAS
# ============================================================================

__all__ = [
    # Common schemas
    'SPUCodeSchema',
    'SubcategorySchema', 
    'ClusterIdSchema',
    
    # Step 15
    'HistoricalBaselineSchema',
    'HistoricalInsightsSchema',
    'HistoricalAnalysisSchema',
    
    # Step 16
    'ComparisonTableSchema',
    'ComparisonMetricsSchema',
    
    # Step 17
    'AugmentedRecommendationSchema',
    'RecommendationMetadataSchema',
    
    # Step 18
    'ValidationSummarySchema',
    'ValidationDetailsSchema',
    
    # Step 19
    'DetailedSPUBreakdownSchema',
    'SPUPerformanceMetricsSchema',
    
    # Step 20
    'DataQualityMetricsSchema',
    'DataValidationErrorsSchema',
    
    # Steps 21-24
    'LabelTagRecommendationSchema',
    'StoreAttributeEnrichmentSchema',
    'ClusteringFeaturesSchema',
    'ComprehensiveClusterLabelsSchema',
    
    # Steps 25-29
    'ProductRoleClassifierSchema',
    'PriceElasticityAnalysisSchema',
    'GapMatrixSchema',
    'ScenarioAnalysisSchema',
    'SupplyDemandGapSchema',
    
    # Steps 30-36
    'OptimizationSchema',
    'SellthroughOptimizationSchema',
    'GapAnalysisWorkbookSchema',
    'EnhancedStoreClusteringSchema',
    'StoreAllocationSchema',
    'MerchandisingSchema',
    'StoreLevelMerchandisingSchema',
    'ClusterLevelMerchandisingSchema',
    'DeliverySchema',
    'UnifiedDeliverySchema',
    'CustomerDeliveryFormatSchema',
    
    # Dashboard and Visualization
    'DashboardSchema',
    'DashboardDataSchema',
    'InteractiveMapDataSchema'
]
