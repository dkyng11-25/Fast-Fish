#!/usr/bin/env python3
"""
Step 19: Detailed SPU Breakdown Schemas

Comprehensive schemas for Step 19 (Detailed SPU Breakdown Report Generator).
Based on src/step19_detailed_spu_breakdown.py docstring and actual output files.

Author: Data Pipeline
Date: 2025-09-17
"""

import pandera.pandas as pa
from pandera.typing import DataFrame, Series
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime

# Schema for detailed SPU recommendations CSV
class DetailedSPURecommendationsSchema(pa.DataFrameModel):
    """Schema for detailed SPU recommendations output."""
    
    # Core identifiers
    str_code: Series[str] = pa.Field()
    spu_code: Series[str] = pa.Field()
    subcategory: Series[str] = pa.Field()
    category: Series[str] = pa.Field()
    
    # Store and cluster info
    store_group: Series[str] = pa.Field()
    cluster_id: Series[int] = pa.Field(ge=0)
    
    # Current state
    current_quantity: Series[float] = pa.Field(ge=0)
    current_sales: Series[float] = pa.Field(ge=0)
    current_price: Series[float] = pa.Field(ge=0, nullable=True)
    
    # Recommendations
    recommended_quantity: Series[float] = pa.Field(ge=0)
    recommended_quantity_change: Series[float] = pa.Field()
    investment_required: Series[float] = pa.Field(ge=0)
    rule_source: Series[str] = pa.Field()
    
    # Performance metrics
    sell_through_rate: Series[float] = pa.Field(ge=0, le=1, nullable=True)
    days_inventory: Series[float] = pa.Field(ge=0, nullable=True)
    sales_velocity: Series[float] = pa.Field(ge=0, nullable=True)
    
    # Business context
    priority_level: Series[str] = pa.Field(nullable=True)
    confidence_score: Series[float] = pa.Field(ge=0, le=1, nullable=True)

# Schema for store level aggregation CSV
class StoreLevelAggregationSchema(pa.DataFrameModel):
    """Schema for store level aggregation output."""
    
    # Store identifiers
    str_code: Series[str] = pa.Field()
    store_group: Series[str] = pa.Field()
    cluster_id: Series[int] = pa.Field(ge=0)
    
    # Aggregated metrics
    total_spus: Series[int] = pa.Field(ge=0)
    total_current_quantity: Series[float] = pa.Field(ge=0)
    total_recommended_quantity: Series[float] = pa.Field(ge=0)
    total_investment_required: Series[float] = pa.Field(ge=0)
    
    # Performance summary
    avg_sell_through_rate: Series[float] = pa.Field(ge=0, le=1, nullable=True)
    total_sales: Series[float] = pa.Field(ge=0)
    avg_sales_per_spu: Series[float] = pa.Field(ge=0, nullable=True)
    
    # Category breakdown
    fashion_spus: Series[int] = pa.Field(ge=0)
    basic_spus: Series[int] = pa.Field(ge=0)
    fashion_ratio: Series[float] = pa.Field(ge=0, le=1, nullable=True)

# Schema for cluster subcategory aggregation CSV
class ClusterSubcategoryAggregationSchema(pa.DataFrameModel):
    """Schema for cluster subcategory aggregation output."""
    
    # Cluster and category identifiers
    cluster_id: Series[int] = pa.Field(ge=0)
    subcategory: Series[str] = pa.Field()
    category: Series[str] = pa.Field()
    
    # Store counts
    total_stores: Series[int] = pa.Field(ge=0)
    stores_with_recommendations: Series[int] = pa.Field(ge=0)
    coverage_percentage: Series[float] = pa.Field(ge=0, le=100)
    
    # Aggregated quantities
    total_current_quantity: Series[float] = pa.Field(ge=0)
    total_recommended_quantity: Series[float] = pa.Field(ge=0)
    total_quantity_change: Series[float] = pa.Field()
    total_investment_required: Series[float] = pa.Field(ge=0)
    
    # Performance metrics
    avg_sell_through_rate: Series[float] = pa.Field(ge=0, le=1, nullable=True)
    total_sales: Series[float] = pa.Field(ge=0)
    avg_sales_per_store: Series[float] = pa.Field(ge=0, nullable=True)

# Schema for SPU breakdown summary markdown
class SPUBreakdownSummarySchema(BaseModel):
    """Schema for SPU breakdown summary markdown content."""
    
    # Report metadata
    report_timestamp: datetime
    period_label: str
    total_stores: int
    total_spus: int
    total_clusters: int
    
    # Summary statistics
    total_current_quantity: float
    total_recommended_quantity: float
    total_investment_required: float
    
    # Performance metrics
    avg_sell_through_rate: Optional[float] = None
    stores_with_recommendations: int
    spus_with_recommendations: int
    
    # Top recommendations
    top_investment_spus: List[Dict[str, Any]] = []
    top_performing_stores: List[Dict[str, Any]] = []
    
    # Cluster analysis
    cluster_summary: List[Dict[str, Any]] = []

# Input schemas
class Step19InputSchema(pa.DataFrameModel):
    """Schema for Step 19 input data."""
    
    # Required input files should exist
    fast_fish_data: Series[str] = pa.Field()  # Path to fast fish data
    store_config: Series[str] = pa.Field()    # Path to store configuration
    clustering_results: Series[str] = pa.Field()  # Path to clustering results

# Output schemas
class Step19OutputSchema(BaseModel):
    """Schema for Step 19 outputs."""
    
    # File paths
    detailed_spu_recommendations: str
    store_level_aggregation: str
    cluster_subcategory_aggregation: str
    spu_breakdown_summary: str
    
    # Validation results
    validation_passed: bool
    total_stores_processed: int
    total_spus_processed: int
    total_recommendations: int
    
    # Performance metrics
    processing_time_seconds: float
    memory_usage_mb: Optional[float] = None

# Validation schemas
class Step19ValidationSchema(BaseModel):
    """Schema for Step 19 validation results."""
    
    # File validation
    files_exist: bool
    files_non_empty: bool
    file_sizes_valid: bool
    
    # Data validation
    data_consistency: bool
    aggregation_accuracy: bool
    business_logic_compliance: bool
    
    # Performance validation
    processing_successful: bool
    memory_usage_acceptable: bool
    
    # Error tracking
    errors: List[str] = []
    warnings: List[str] = []
    
    # Statistics
    validation_timestamp: datetime
    validation_duration_seconds: float

# Comprehensive validation schema
class Step19ComprehensiveSchema(BaseModel):
    """Comprehensive schema for Step 19 validation."""
    
    # Input validation
    input_validation: Step19InputSchema
    
    # Output validation
    output_validation: Step19OutputSchema
    
    # Data quality validation
    detailed_spu_validation: DetailedSPURecommendationsSchema
    store_aggregation_validation: StoreLevelAggregationSchema
    cluster_aggregation_validation: ClusterSubcategoryAggregationSchema
    summary_validation: SPUBreakdownSummarySchema
    
    # Overall validation
    validation_results: Step19ValidationSchema

__all__ = [
    'DetailedSPURecommendationsSchema',
    'StoreLevelAggregationSchema', 
    'ClusterSubcategoryAggregationSchema',
    'SPUBreakdownSummarySchema',
    'Step19InputSchema',
    'Step19OutputSchema',
    'Step19ValidationSchema',
    'Step19ComprehensiveSchema'
]
