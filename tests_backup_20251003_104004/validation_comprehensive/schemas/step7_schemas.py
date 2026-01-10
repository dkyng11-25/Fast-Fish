import pandas as pd
#!/usr/bin/env python3
"""
Step 7 Validation Schemas

This module defines comprehensive pandera schemas for Step 7: Missing Category/SPU Rule
with Quantity Recommendations and Fast Fish Sell-Through Validation.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera.pandas as pa
from pandera.typing import Series
from typing import Optional, Union

# Import common schemas - handle both direct and relative imports
try:
    from .common_schemas import StoreCodeSchema, SalesAmountSchema, QuantitySchema, PriceSchema
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from common_schemas import StoreCodeSchema, SalesAmountSchema, QuantitySchema, PriceSchema

# ============================================================================
# INPUT SCHEMAS
# ============================================================================

class Step7ClusteringInputSchema(pa.DataFrameModel):
    """Schema for clustering results input to Step 7."""
    str_code: Series[int] = pa.Field(description="Store code identifier")
    Cluster: Series[str] = pa.Field(description="Cluster identifier")

class Step7SPUSalesInputSchema(pa.DataFrameModel):
    """Schema for SPU sales data input to Step 7."""
    str_code: Series[int] = pa.Field(description="Store code identifier")
    spu_code: Series[str] = pa.Field(description="SPU code identifier")
    spu_sales_amt: Series[float] = pa.Field(description="SPU sales amount")

class Step7CategorySalesInputSchema(pa.DataFrameModel):
    """Schema for category sales data input to Step 7."""
    str_code: Series[int] = pa.Field(description="Store code identifier")
    sub_cate_name: Series[str] = pa.Field(description="Subcategory name")
    sal_amt: Series[float] = pa.Field(description="Sales amount")

class Step7QuantityInputSchema(pa.DataFrameModel):
    """Schema for quantity data input to Step 7."""
    str_code: Series[int] = pa.Field(description="Store code identifier")
    base_sal_qty: Series[float] = pa.Field(ge=0, description="Base sales quantity")
    fashion_sal_qty: Series[float] = pa.Field(ge=0, description="Fashion sales quantity")
    base_sal_amt: Series[float] = pa.Field(description="Base sales amount")
    fashion_sal_amt: Series[float] = pa.Field(description="Fashion sales amount")

# ============================================================================
# OUTPUT SCHEMAS
# ============================================================================

class Step7StoreResultsSchema(pa.DataFrameModel):
    """Schema for Step 7 store-level results output - matches actual output structure."""
    str_code: Series[str] = pa.Field(description="Store code identifier")
    cluster_id: Series[int] = pa.Field(description="Cluster identifier")
    missing_spus_count: Series[int] = pa.Field(ge=0, description="Count of missing SPUs")
    total_opportunity_value: Series[int] = pa.Field(description="Total opportunity value")
    total_quantity_needed: Series[int] = pa.Field(description="Total quantity needed")
    total_investment_required: Series[int] = pa.Field(description="Total investment required")
    total_retail_value: Series[int] = pa.Field(description="Total retail value")
    avg_sellthrough_improvement: Series[int] = pa.Field(description="Average sell-through improvement percentage")
    avg_predicted_sellthrough: Series[int] = pa.Field(description="Average predicted sell-through percentage")
    fastfish_approved_count: Series[int] = pa.Field(description="Count of Fast Fish approved opportunities")
    rule7_missing_spu: Series[int] = pa.Field(description="Rule 7 missing SPU flag")
    rule7_description: Series[str] = pa.Field(description="Rule 7 description")
    rule7_threshold: Series[str] = pa.Field(description="Rule 7 threshold description")
    rule7_analysis_level: Series[str] = pa.Field(description="Rule 7 analysis level")
    rule7_sellthrough_validation: Series[str] = pa.Field(description="Rule 7 sell-through validation status")
    rule7_fastfish_compliant: Series[bool] = pa.Field(description="Rule 7 Fast Fish compliance status")

class Step7OpportunitiesSchema(pa.DataFrameModel):
    """Schema for Step 7 opportunities detail output."""
    str_code: Series[str] = pa.Field(description="Store code identifier")
    cluster_id: Series[float] = pa.Field(ge=0, description="Cluster identifier")
    spu_code: Series[str] = pa.Field(description="SPU code identifier")
    opportunity_type: Series[str] = pa.Field(description="Type of opportunity")
    cluster_total_sales: Series[float] = pa.Field(ge=0, description="Total sales in cluster")
    stores_selling_in_cluster: Series[int] = pa.Field(ge=0, description="Number of stores selling in cluster")
    cluster_size: Series[int] = pa.Field(ge=0, description="Total cluster size")
    pct_stores_selling: Series[float] = pa.Field(ge=0, le=100, description="Percentage of stores selling")
    expected_sales_opportunity: Series[float] = pa.Field(ge=0, description="Expected sales opportunity")
    current_quantity: Series[float] = pa.Field(ge=0, description="Current quantity")
    recommended_quantity_change: Series[float] = pa.Field(description="Recommended quantity change")
    unit_price: Series[float] = pa.Field(gt=0, description="Unit price")
    investment_required: Series[float] = pa.Field(ge=0, description="Investment required")
    recommendation_text: Series[str] = pa.Field(description="Recommendation text")
    price_source: Series[str] = pa.Field(description="Price source")
    current_sell_through_rate: Series[float] = pa.Field(ge=0, le=100, description="Current sell-through rate")
    predicted_sell_through_rate: Series[float] = pa.Field(ge=0, le=100, description="Predicted sell-through rate")
    sell_through_improvement: Series[float] = pa.Field(description="Sell-through improvement")
    fast_fish_compliant: Series[bool] = pa.Field(description="Fast Fish compliance flag")
    business_rationale: Series[str] = pa.Field(description="Business rationale")
    approval_reason: Series[str] = pa.Field(description="Approval reason")
    roi: Series[float] = pa.Field(description="Return on investment")
    margin_uplift: Series[float] = pa.Field(description="Margin uplift")
    n_comparables: Series[int] = pa.Field(ge=0, description="Number of comparables")

class Step7SubcategoryOpportunitiesSchema(pa.DataFrameModel):
    """Schema for Step 7 subcategory opportunities detail output."""
    str_code: Series[str] = pa.Field(description="Store code identifier")
    cluster_id: Series[float] = pa.Field(ge=0, description="Cluster identifier")
    sub_cate_name: Series[str] = pa.Field(description="Subcategory name")
    opportunity_type: Series[str] = pa.Field(description="Type of opportunity")
    cluster_total_sales: Series[float] = pa.Field(ge=0, description="Total sales in cluster")
    stores_selling_in_cluster: Series[int] = pa.Field(ge=0, description="Number of stores selling in cluster")
    cluster_size: Series[int] = pa.Field(ge=0, description="Total cluster size")
    pct_stores_selling: Series[float] = pa.Field(ge=0, le=100, description="Percentage of stores selling")
    expected_sales_opportunity: Series[float] = pa.Field(ge=0, description="Expected sales opportunity")
    current_quantity: Series[float] = pa.Field(ge=0, description="Current quantity")
    recommended_quantity_change: Series[float] = pa.Field(description="Recommended quantity change")
    unit_price: Series[float] = pa.Field(gt=0, description="Unit price")
    investment_required: Series[float] = pa.Field(ge=0, description="Investment required")
    recommendation_text: Series[str] = pa.Field(description="Recommendation text")
    price_source: Series[str] = pa.Field(description="Price source")
    current_sell_through_rate: Series[float] = pa.Field(ge=0, le=100, description="Current sell-through rate")
    predicted_sell_through_rate: Series[float] = pa.Field(ge=0, le=100, description="Predicted sell-through rate")
    sell_through_improvement: Series[float] = pa.Field(description="Sell-through improvement")
    fast_fish_compliant: Series[bool] = pa.Field(description="Fast Fish compliance flag")
    business_rationale: Series[str] = pa.Field(description="Business rationale")
    approval_reason: Series[str] = pa.Field(description="Approval reason")
    roi: Series[float] = pa.Field(description="Return on investment")
    margin_uplift: Series[float] = pa.Field(description="Margin uplift")
    n_comparables: Series[int] = pa.Field(ge=0, description="Number of comparables")

# ============================================================================
# BUSINESS LOGIC VALIDATION SCHEMAS
# ============================================================================

class Step7BusinessLogicSchema(pa.DataFrameModel):
    """Schema for Step 7 business logic validation."""
    str_code: Series[str] = pa.Field(description="Store code identifier")
    cluster_id: Series[int] = pa.Field(ge=0, description="Cluster identifier")
    
    # Business rule validations
    missing_count_positive: Series[bool] = pa.Field(description="Missing count should be positive when opportunities exist")
    opportunity_value_positive: Series[bool] = pa.Field(description="Opportunity value should be positive when opportunities exist")
    quantity_needed_positive: Series[bool] = pa.Field(description="Quantity needed should be positive when opportunities exist")
    investment_positive: Series[bool] = pa.Field(description="Investment should be positive when opportunities exist")
    sellthrough_improvement_valid: Series[bool] = pa.Field(description="Sell-through improvement should be valid")
    fastfish_approved_reasonable: Series[bool] = pa.Field(description="Fast Fish approved count should be reasonable")

# ============================================================================
# PERIOD FLEXIBILITY SCHEMAS
# ============================================================================

class Step7PeriodFlexibleSchema(pa.DataFrameModel):
    """Schema for Step 7 with period flexibility."""
    period_label: Series[str] = pa.Field(description="Period label (e.g., 202508A)")
    analysis_level: Series[str] = pa.Field(description="Analysis level (spu or subcategory)")
    validation_timestamp: Series[str] = pa.Field(description="Validation timestamp")
    data_quality_score: Series[float] = pa.Field(ge=0, le=100, description="Data quality score")

# ============================================================================
# EXPORT ALL SCHEMAS
# ============================================================================

__all__ = [
    # Input schemas
    'Step7ClusteringInputSchema',
    'Step7SPUSalesInputSchema',
    'Step7CategorySalesInputSchema',
    'Step7QuantityInputSchema',
    
    # Output schemas
    'Step7StoreResultsSchema',
    'Step7OpportunitiesSchema',
    'Step7SubcategoryOpportunitiesSchema',
    
    # Business logic schemas
    'Step7BusinessLogicSchema',
    
    # Period flexibility schemas
    'Step7PeriodFlexibleSchema'
]
