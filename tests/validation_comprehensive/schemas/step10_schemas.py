import pandas as pd
"""
Pandera schemas for Step 10: Smart Overcapacity (SPU) with Real-Unit Reductions

This module defines comprehensive data validation schemas for Step 10 outputs,
including results and opportunities files.
"""

import pandera.pandas as pa
from pandera.typing import Series
from typing import Optional


class Step10ResultsSchema(pa.DataFrameModel):
    """Schema for Step 10 results file (store-level aggregated results)"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    cluster_id: Series[str] = pa.Field(description="Cluster identifier")
    rule10_spu_overcapacity: Series[int] = pa.Field(ge=0, le=1, description="Rule flag (1 if overcapacity detected)")
    rule10_overcapacity_count: Series[int] = pa.Field(ge=0, description="Number of SPUs with overcapacity")
    rule10_total_excess_spus: Series[float] = pa.Field(ge=0, description="Total excess SPU count")
    rule10_avg_overcapacity_pct: Series[float] = pa.Field(ge=0, description="Average overcapacity percentage")
    rule10_reduction_recommended_count: Series[int] = pa.Field(ge=0, description="Number of SPUs recommended for reduction")
    rule10_total_quantity_reduction: Series[float] = pa.Field(ge=0, description="Total quantity reduction recommended")
    rule10_total_cost_savings: Series[float] = pa.Field(ge=0, description="Total cost savings from reductions")
    recommended_quantity_change: Series[float] = pa.Field(le=0, description="Recommended quantity change (negative for reductions)")
    investment_required: Series[float] = pa.Field(le=0, description="Investment required (negative for savings)")
    business_rationale: Series[str] = pa.Field(description="Business rationale for recommendations")
    approval_reason: Series[str] = pa.Field(description="Approval reason")
    fast_fish_compliant: Series[bool] = pa.Field(description="Fast Fish validation compliance")
    opportunity_type: Series[str] = pa.Field(description="Type of opportunity")
    period_label: Series[str] = pa.Field(description="Period label")
    target_yyyymm: Series[str] = pa.Field(description="Target year-month")
    target_period: Series[str] = pa.Field(description="Target period")
    
    class Config:
        coerce = True


class Step10OpportunitiesSchema(pa.DataFrameModel):
    """Schema for Step 10 opportunities file (detailed opportunity information)"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    str_name: Series[str] = pa.Field(description="Store name")
    Cluster: Series[str] = pa.Field(description="Cluster name")
    season_name: Series[str] = pa.Field(description="Season name")
    sex_name: Series[str] = pa.Field(description="Sex name")
    display_location_name: Series[str] = pa.Field(description="Display location name")
    big_class_name: Series[str] = pa.Field(description="Big class name")
    sub_cate_name: Series[str] = pa.Field(description="Subcategory name")
    yyyy: Series[int] = pa.Field(description="Year")
    mm: Series[int] = pa.Field(ge=1, le=12, description="Month")
    mm_type: Series[str] = pa.Field(description="Month type")
    sal_amt: Series[float] = pa.Field(description="Sales amount (can be negative for returns/adjustments)")
    sty_sal_amt: Series[float] = pa.Field(ge=0, description="Style sales amount")
    category_current_spu_count: Series[float] = pa.Field(ge=0, description="Current SPU count in category")
    category_target_spu_count: Series[float] = pa.Field(ge=0, description="Target SPU count in category")
    category_excess_spu_count: Series[float] = pa.Field(ge=0, description="Excess SPU count in category")
    category_overcapacity_percentage: Series[float] = pa.Field(ge=0, description="Overcapacity percentage")
    category_total_sales: Series[float] = pa.Field(ge=0, description="Total sales in category")
    spu_code: Series[str] = pa.Field(description="SPU code")
    spu_sales: Series[float] = pa.Field(ge=0, description="SPU sales amount")
    spu_sales_share: Series[float] = pa.Field(ge=0, le=1, description="SPU sales share")
    overcapacity_percentage: Series[float] = pa.Field(ge=0, description="SPU overcapacity percentage")
    excess_spu_count: Series[float] = pa.Field(ge=0, description="Excess SPU count")
    quantity: Series[float] = pa.Field(ge=0, description="Quantity")
    spu_sales_amt: Series[float] = pa.Field(ge=0, description="SPU sales amount")
    quantity_real: Series[float] = pa.Field(ge=0, description="Real quantity")
    unit_price: Series[float] = pa.Field(ge=0, description="Unit price")
    current_quantity: Series[float] = pa.Field(ge=0, description="Current quantity")
    potential_reduction: Series[float] = pa.Field(ge=0, description="Potential reduction")
    constrained_reduction: Series[float] = pa.Field(ge=0, description="Constrained reduction")
    recommend_reduction: Series[bool] = pa.Field(description="Whether to recommend reduction")
    recommended_quantity_change: Series[float] = pa.Field(le=0, description="Recommended quantity change (negative)")
    margin_rate: Series[float] = pa.Field(ge=0, le=1, description="Margin rate")
    retail_value: Series[float] = pa.Field(ge=0, description="Retail value")
    investment_required: Series[float] = pa.Field(le=0, description="Investment required (negative for savings)")
    estimated_cost_savings: Series[float] = pa.Field(ge=0, description="Estimated cost savings")
    margin_per_unit: Series[float] = pa.Field(description="Margin per unit")
    expected_margin_uplift: Series[float] = pa.Field(description="Expected margin uplift")
    roi_percentage: Series[float] = pa.Field(description="ROI percentage")
    recommendation_text: Series[str] = pa.Field(description="Recommendation text")
    _v_curr_cnt: Series[float] = pa.Field(ge=0, description="Current count for validation")
    _v_rec_cnt: Series[float] = pa.Field(ge=0, description="Recommended count for validation")
    current_sell_through_rate: Series[float] = pa.Field(ge=0, le=100, description="Current sell-through rate")
    predicted_sell_through_rate: Series[float] = pa.Field(ge=0, le=100, description="Predicted sell-through rate")
    sell_through_improvement: Series[float] = pa.Field(description="Sell-through improvement")
    fast_fish_compliant: Series[bool] = pa.Field(description="Fast Fish compliance")
    business_rationale: Series[str] = pa.Field(description="Business rationale")
    approval_reason: Series[str] = pa.Field(description="Approval reason")
    period_label: Series[str] = pa.Field(description="Period label")
    target_yyyymm: Series[str] = pa.Field(description="Target year-month")
    target_period: Series[str] = pa.Field(description="Target period")
    opportunity_type: Series[str] = pa.Field(description="Opportunity type")
    
    class Config:
        coerce = True


class Step10InputClusteringSchema(pa.DataFrameModel):
    """Schema for Step 10 input clustering results"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    Cluster: Series[str] = pa.Field(description="Cluster identifier")
    
    class Config:
        coerce = True


class Step10InputStoreConfigSchema(pa.DataFrameModel):
    """Schema for Step 10 input store configuration data"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    sty_sal_amt: Series[str] = pa.Field(description="Style sales amount JSON-like content")
    season_name: Series[str] = pa.Field(description="Season name")
    sex_name: Series[str] = pa.Field(description="Sex name")
    display_location_name: Series[str] = pa.Field(description="Display location name")
    big_class_name: Series[str] = pa.Field(description="Big class name")
    sub_cate_name: Series[str] = pa.Field(description="Subcategory name")
    
    class Config:
        coerce = True


class Step10InputQuantitySchema(pa.DataFrameModel):
    """Schema for Step 10 input quantity data"""
    
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
class CommonStep10Schemas:
    """Common column schemas for Step 10 validation"""
    
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
        """Quantity change column schema (negative for reductions)"""
        return pa.Field(le=0, description="Quantity change (negative for reductions)")
    
    @staticmethod
    def get_investment_required_schema() -> pa.Field:
        """Investment required column schema (negative for savings)"""
        return pa.Field(le=0, description="Investment required (negative for savings)")
    
    @staticmethod
    def get_overcapacity_percentage_schema() -> pa.Field:
        """Overcapacity percentage column schema"""
        return pa.Field(ge=0, description="Overcapacity percentage")
    
    @staticmethod
    def get_sell_through_rate_schema() -> pa.Field:
        """Sell-through rate column schema"""
        return pa.Field(ge=0, le=100, description="Sell-through rate percentage")


# Validation functions
def validate_step10_results(df: 'pd.DataFrame') -> bool:
    """Validate Step 10 results data"""
    try:
        Step10ResultsSchema.validate(df)
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 10 results validation failed: {e}")
        return False


def validate_step10_opportunities(df: 'pd.DataFrame') -> bool:
    """Validate Step 10 opportunities data"""
    try:
        Step10OpportunitiesSchema.validate(df)
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 10 opportunities validation failed: {e}")
        return False


def validate_step10_inputs(clustering_df: 'pd.DataFrame', 
                          store_config_df: 'pd.DataFrame', 
                          quantity_df: 'pd.DataFrame') -> bool:
    """Validate Step 10 input data"""
    try:
        # Only validate clustering data if it's not empty
        if not clustering_df.empty:
            print(f"Validating clustering data: {clustering_df.shape}, columns: {list(clustering_df.columns)}")
            Step10InputClusteringSchema.validate(clustering_df)
            print("Clustering validation passed")
        
        # Only validate store config data if it's not empty
        if not store_config_df.empty:
            print(f"Validating store config data: {store_config_df.shape}, columns: {list(store_config_df.columns)}")
            Step10InputStoreConfigSchema.validate(store_config_df)
            print("Store config validation passed")
        
        # Only validate quantity data if it's not empty
        if not quantity_df.empty:
            print(f"Validating quantity data: {quantity_df.shape}, columns: {list(quantity_df.columns)}")
            Step10InputQuantitySchema.validate(quantity_df)
            print("Quantity validation passed")
        
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 10 input validation failed: {e}")
        return False


def validate_negative_quantities(df: 'pd.DataFrame', quantity_column: str = "recommended_quantity_change") -> bool:
    """Validate that all quantity changes are negative (Step 10 specific - reductions only)"""
    try:
        if quantity_column in df.columns:
            quantities = df[quantity_column].dropna()
            return bool((quantities <= 0).all())
        return True
    except Exception as e:
        print(f"Negative quantity validation failed: {e}")
        return False


def validate_overcapacity_logic(df: pd.DataFrame) -> bool:
    """Validate overcapacity detection logic"""
    try:
        if "category_current_spu_count" in df.columns and "category_target_spu_count" in df.columns:
            current_counts = df["category_current_spu_count"]
            target_counts = df["category_target_spu_count"]
            
            # All cases should have current > target for overcapacity
            return bool((current_counts > target_counts).all())
        return True
    except Exception as e:
        print(f"Overcapacity logic validation failed: {e}")
        return False


def validate_cost_savings_logic(df: pd.DataFrame) -> bool:
    """Validate cost savings logic (investment_required should be negative)"""
    try:
        if "investment_required" in df.columns:
            investments = df["investment_required"].dropna()
            return bool((investments <= 0).all())
        return True
    except Exception as e:
        print(f"Cost savings logic validation failed: {e}")
        return False

__all__ = [
    'Step10ResultsSchema',
    'Step10OpportunitiesSchema',
    'Step10InputClusteringSchema',
    'Step10InputStoreConfigSchema',
    'Step10InputQuantitySchema',
]
