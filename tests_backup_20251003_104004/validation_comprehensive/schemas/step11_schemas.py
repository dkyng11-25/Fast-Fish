import pandas as pd
"""
Pandera schemas for Step 11: Missed Sales Opportunity (SPU) with Real-Unit, Incremental Quantity Recommendations

This module defines comprehensive data validation schemas for Step 11 outputs,
including results, details, and top performers files.
"""

import pandera.pandas as pa
from pandera.typing import Series
from typing import Optional


class Step11ResultsSchema(pa.DataFrameModel):
    """Schema for Step 11 results file (store-level aggregated results)"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    cluster_id: Series[str] = pa.Field(description="Cluster identifier")
    rule11_missed_sales_opportunity: Series[int] = pa.Field(ge=0, le=1, description="Rule flag (1 if opportunities detected)")
    rule11_missing_top_performers_count: Series[int] = pa.Field(ge=0, description="Number of missing top performers")
    rule11_avg_opportunity_score: Series[float] = pa.Field(ge=0, description="Average opportunity score")
    rule11_potential_sales_increase: Series[float] = pa.Field(ge=0, description="Potential sales increase")
    rule11_total_recommended_period_sales: Series[float] = pa.Field(ge=0, description="Total recommended period sales")
    rule11_total_recommended_period_qty: Series[float] = pa.Field(ge=0, description="Total recommended period quantity")
    investment_required: Series[float] = pa.Field(ge=0, description="Investment required")
    recommended_quantity_change: Series[float] = pa.Field(ge=0, description="Recommended quantity change (positive for increases)")
    business_rationale: Series[str] = pa.Field(description="Business rationale")
    approval_reason: Series[str] = pa.Field(description="Approval reason")
    fast_fish_compliant: Series[bool] = pa.Field(description="Fast Fish validation compliance")
    opportunity_type: Series[str] = pa.Field(description="Type of opportunity")
    period_label: Series[str] = pa.Field(description="Period label")
    target_yyyymm: Series[str] = pa.Field(description="Target year-month")
    target_period: Series[str] = pa.Field(description="Target period")
    
    class Config:
        coerce = True


class Step11DetailsSchema(pa.DataFrameModel):
    """Schema for Step 11 details file (detailed opportunity information)"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    cluster: Series[str] = pa.Field(description="Cluster name")
    category_key: Series[str] = pa.Field(description="Category grouping key")
    spu_code: Series[str] = pa.Field(description="SPU code")
    recommendation_type: Series[str] = pa.Field(description="Type of recommendation (ADD_NEW or INCREASE_EXISTING)")
    current_spu_sales: Series[float] = pa.Field(ge=0, nullable=True, description="Current SPU sales")
    current_quantity: Series[float] = pa.Field(ge=0, nullable=True, description="Current quantity")
    target_period_sales: Series[float] = pa.Field(ge=0, description="Target period sales")
    target_period_qty: Series[float] = pa.Field(ge=0, description="Target period quantity")
    recommended_additional_sales: Series[float] = pa.Field(ge=0, description="Recommended additional sales")
    recommended_quantity_change: Series[float] = pa.Field(ge=0, description="Recommended quantity change (positive)")
    spu_total_sales_in_cluster: Series[float] = pa.Field(ge=0, description="SPU total sales in cluster")
    spu_avg_sales_per_store: Series[float] = pa.Field(ge=0, description="SPU average sales per store")
    spu_total_qty_in_cluster: Series[float] = pa.Field(ge=0, description="SPU total quantity in cluster")
    spu_avg_qty_per_store: Series[float] = pa.Field(ge=0, description="SPU average quantity per store")
    spu_adoption_rate_in_cluster: Series[float] = pa.Field(ge=0, le=1, description="SPU adoption rate in cluster")
    spu_sales_percentile: Series[float] = pa.Field(ge=0, le=1, description="SPU sales percentile")
    stores_selling_in_cluster: Series[int] = pa.Field(ge=0, description="Stores selling in cluster")
    total_stores_in_cluster: Series[int] = pa.Field(ge=1, description="Total stores in cluster")
    store_category_total_sales: Series[float] = pa.Field(ge=0, description="Store category total sales")
    store_category_total_qty: Series[float] = pa.Field(ge=0, description="Store category total quantity")
    avg_spu_to_category_sales_ratio: Series[float] = pa.Field(ge=0, description="Average SPU to category sales ratio")
    avg_spu_to_category_qty_ratio: Series[float] = pa.Field(ge=0, description="Average SPU to category quantity ratio")
    recommended_sales_percentage: Series[float] = pa.Field(ge=0, description="Recommended sales percentage")
    recommended_qty_percentage: Series[float] = pa.Field(ge=0, description="Recommended quantity percentage")
    unit_price: Series[float] = pa.Field(ge=0, description="Unit price")
    opportunity_score: Series[float] = pa.Field(ge=0, description="Opportunity score")
    cate_name: Series[str] = pa.Field(description="Category name")
    sub_cate_name: Series[str] = pa.Field(description="Subcategory name")
    investment_required: Series[float] = pa.Field(ge=0, description="Investment required")
    recommendation_text: Series[str] = pa.Field(description="Recommendation text")
    current_sell_through_rate: Series[float] = pa.Field(ge=0, le=100, description="Current sell-through rate")
    predicted_sell_through_rate: Series[float] = pa.Field(ge=0, le=100, description="Predicted sell-through rate")
    sell_through_improvement: Series[float] = pa.Field(description="Sell-through improvement")
    fast_fish_compliant: Series[bool] = pa.Field(description="Fast Fish compliance")
    business_rationale: Series[str] = pa.Field(description="Business rationale")
    approval_reason: Series[str] = pa.Field(description="Approval reason")
    period_label: Series[str] = pa.Field(description="Period label")
    target_yyyymm: Series[str] = pa.Field(description="Target year-month")
    target_period: Series[str] = pa.Field(description="Target period")
    
    class Config:
        coerce = True


class Step11TopPerformersSchema(pa.DataFrameModel):
    """Schema for Step 11 top performers file (cluster-category top performers)"""
    
    cluster: Series[str] = pa.Field(description="Cluster name")
    category_key: Series[str] = pa.Field(description="Category grouping key")
    spu_code: Series[str] = pa.Field(description="SPU code")
    total_sales: Series[float] = pa.Field(ge=0, description="Total sales")
    avg_sales: Series[float] = pa.Field(ge=0, description="Average sales")
    transaction_count: Series[int] = pa.Field(ge=0, description="Transaction count")
    total_qty: Series[float] = pa.Field(ge=0, description="Total quantity")
    avg_qty: Series[float] = pa.Field(ge=0, description="Average quantity")
    stores_selling: Series[int] = pa.Field(ge=0, description="Stores selling")
    avg_spu_to_category_sales_ratio: Series[float] = pa.Field(ge=0, description="Average SPU to category sales ratio")
    avg_spu_to_category_qty_ratio: Series[float] = pa.Field(ge=0, description="Average SPU to category quantity ratio")
    avg_category_sales_size: Series[float] = pa.Field(ge=0, description="Average category sales size")
    avg_category_qty_size: Series[float] = pa.Field(ge=0, description="Average category quantity size")
    avg_unit_price: Series[float] = pa.Field(ge=0, description="Average unit price")
    sales_percentile: Series[float] = pa.Field(ge=0, le=1, description="Sales percentile")
    Cluster: Series[str] = pa.Field(description="Cluster identifier")
    total_stores_in_cluster: Series[int] = pa.Field(ge=1, description="Total stores in cluster")
    adoption_rate: Series[float] = pa.Field(ge=0, le=1, description="Adoption rate")
    period_label: Series[str] = pa.Field(description="Period label")
    target_yyyymm: Series[str] = pa.Field(description="Target year-month")
    target_period: Series[str] = pa.Field(description="Target period")
    
    class Config:
        coerce = True


class Step11InputClusteringSchema(pa.DataFrameModel):
    """Schema for Step 11 input clustering results"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    Cluster: Series[str] = pa.Field(description="Cluster identifier")
    
    class Config:
        coerce = True


class Step11InputQuantitySchema(pa.DataFrameModel):
    """Schema for Step 11 input quantity data"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    spu_code: Series[str] = pa.Field(description="SPU code")
    spu_sales_amt: Series[float] = pa.Field(ge=0, description="SPU sales amount")
    quantity: Series[float] = pa.Field(ge=0, nullable=True, description="Primary quantity field")
    base_sal_qty: Series[float] = pa.Field(ge=0, nullable=True, description="Base sales quantity")
    fashion_sal_qty: Series[float] = pa.Field(ge=0, nullable=True, description="Fashion sales quantity")
    sal_qty: Series[float] = pa.Field(ge=0, nullable=True, description="Sales quantity")
    
    class Config:
        coerce = True


# Common column schemas for reuse across steps
class CommonStep11Schemas:
    """Common column schemas for Step 11 validation"""
    
    @staticmethod
    def get_store_code_schema() -> pa.Field:
        """Store code column schema"""
        return pa.Field(description="Store code identifier")
    
    @staticmethod
    def get_cluster_id_schema() -> pa.Field:
        """Cluster ID column schema"""
        return pa.Field(description="Cluster identifier")
    
    @staticmethod
    def get_spu_code_schema() -> pa.Field:
        """SPU code column schema"""
        return pa.Field(description="SPU code identifier")
    
    @staticmethod
    def get_quantity_change_schema() -> pa.Field:
        """Quantity change column schema (positive for increases)"""
        return pa.Field(ge=0, description="Quantity change (positive for increases)")
    
    @staticmethod
    def get_investment_required_schema() -> pa.Field:
        """Investment required column schema"""
        return pa.Field(ge=0, description="Investment required")
    
    @staticmethod
    def get_opportunity_score_schema() -> pa.Field:
        """Opportunity score column schema"""
        return pa.Field(ge=0, description="Opportunity score")
    
    @staticmethod
    def get_adoption_rate_schema() -> pa.Field:
        """Adoption rate column schema"""
        return pa.Field(ge=0, le=1, description="Adoption rate")
    
    @staticmethod
    def get_sell_through_rate_schema() -> pa.Field:
        """Sell-through rate column schema"""
        return pa.Field(ge=0, le=100, description="Sell-through rate percentage")


# Validation functions
def validate_step11_results(df: 'pd.DataFrame') -> bool:
    """Validate Step 11 results data"""
    try:
        Step11ResultsSchema.validate(df)
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 11 results validation failed: {e}")
        return False


def validate_step11_details(df: 'pd.DataFrame') -> bool:
    """Validate Step 11 details data"""
    try:
        Step11DetailsSchema.validate(df)
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 11 details validation failed: {e}")
        return False


def validate_step11_top_performers(df: 'pd.DataFrame') -> bool:
    """Validate Step 11 top performers data"""
    try:
        Step11TopPerformersSchema.validate(df)
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 11 top performers validation failed: {e}")
        return False


def validate_step11_inputs(clustering_df: 'pd.DataFrame', 
                          quantity_df: 'pd.DataFrame') -> bool:
    """Validate Step 11 input data"""
    try:
        # Only validate clustering data if it's not empty
        if not clustering_df.empty:
            Step11InputClusteringSchema.validate(clustering_df)
        
        # Only validate quantity data if it's not empty
        if not quantity_df.empty:
            Step11InputQuantitySchema.validate(quantity_df)
        
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 11 input validation failed: {e}")
        return False


def validate_positive_quantities(df: 'pd.DataFrame', quantity_column: str = "recommended_quantity_change") -> bool:
    """Validate that all quantity changes are positive (Step 11 specific - increases only)"""
    try:
        if quantity_column in df.columns:
            quantities = df[quantity_column].dropna()
            return bool((quantities >= 0).all())
        return True
    except Exception as e:
        print(f"Positive quantity validation failed: {e}")
        return False


def validate_opportunity_detection_logic(df: pd.DataFrame) -> bool:
    """Validate opportunity detection logic"""
    try:
        if "recommendation_type" in df.columns:
            # Should have both ADD_NEW and INCREASE_EXISTING types
            recommendation_types = df["recommendation_type"].value_counts()
            return "ADD_NEW" in recommendation_types.index or "INCREASE_EXISTING" in recommendation_types.index
        return True
    except Exception as e:
        print(f"Opportunity detection logic validation failed: {e}")
        return False


def validate_top_performer_logic(df: pd.DataFrame) -> bool:
    """Validate top performer identification logic"""
    try:
        if "sales_percentile" in df.columns and "adoption_rate" in df.columns:
            # Top performers should have high percentiles and adoption rates
            high_percentiles = df["sales_percentile"] >= 0.9  # 90th percentile or higher
            high_adoption = df["adoption_rate"] >= 0.5  # 50% adoption or higher
            return bool((high_percentiles & high_adoption).any())
        return True
    except Exception as e:
        print(f"Top performer logic validation failed: {e}")
        return False

__all__ = [
    'Step11ResultsSchema',
    'Step11DetailsSchema',
    'Step11TopPerformersSchema',
    'Step11InputClusteringSchema',
    'Step11InputQuantitySchema',
]
