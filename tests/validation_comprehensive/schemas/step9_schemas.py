import pandas as pd
"""
Pandera schemas for Step 9: Below Minimum Rule with Positive-Only Quantity Increases

This module defines comprehensive data validation schemas for Step 9 outputs,
including results, opportunities, and summary files.
"""

import pandera.pandas as pa
from pandera.typing import Series
from typing import Optional


class Step9ResultsSchema(pa.DataFrameModel):
    """Schema for Step 9 results file (store-level aggregated results)"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    cluster_id: Series[str] = pa.Field(description="Cluster identifier")
    below_minimum_spus_count: Series[float] = pa.Field(ge=0, nullable=True, description="Count of below minimum SPUs")
    total_increase_needed: Series[float] = pa.Field(ge=0, nullable=True, description="Total increase needed")
    avg_current_count: Series[float] = pa.Field(ge=0, nullable=True, description="Average current count")
    total_quantity_change: Series[float] = pa.Field(ge=0, nullable=True, description="Total quantity change")
    total_investment: Series[float] = pa.Field(ge=0, nullable=True, description="Total investment")
    rule9_below_minimum_spu: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Rule flag for below minimum SPU")
    investment_required: Series[float] = pa.Field(ge=0, nullable=True, description="Investment required")
    recommended_quantity_change: Series[float] = pa.Field(ge=0, nullable=True, description="Recommended quantity change")
    business_rationale: Series[str] = pa.Field(nullable=True, description="Business rationale")
    approval_reason: Series[str] = pa.Field(nullable=True, description="Approval reason")
    fast_fish_compliant: Series[str] = pa.Field(nullable=True, description="Fast Fish compliance status")
    opportunity_type: Series[str] = pa.Field(nullable=True, description="Opportunity type")
    rule9_description: Series[str] = pa.Field(nullable=True, description="Rule 9 description")
    rule9_threshold: Series[str] = pa.Field(nullable=True, description="Rule 9 threshold")
    rule9_analysis_level: Series[str] = pa.Field(nullable=True, description="Rule 9 analysis level")
    rule9_fix_applied: Series[str] = pa.Field(nullable=True, description="Rule 9 fix applied status")
    
    class Config:
        coerce = True


class Step9OpportunitiesSchema(pa.DataFrameModel):
    """Schema for Step 9 opportunities file (detailed opportunity information)"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    season_name: Series[str] = pa.Field(description="Season name")
    sex_name: Series[str] = pa.Field(description="Sex name")
    display_location_name: Series[str] = pa.Field(description="Display location name")
    big_class_name: Series[str] = pa.Field(description="Big class name")
    sub_cate_name: Series[str] = pa.Field(description="Subcategory name")
    sty_code: Series[str] = pa.Field(description="Style code")
    spu_sales_amt: Series[float] = pa.Field(ge=0, description="SPU sales amount")
    Cluster: Series[str] = pa.Field(description="Cluster identifier")
    spu_code: Series[str] = pa.Field(description="SPU code")
    quantity: Series[float] = pa.Field(ge=0, description="Current quantity")
    unit_price: Series[float] = pa.Field(ge=0, nullable=True, description="Unit price")
    unit_rate: Series[float] = pa.Field(ge=0, description="Unit rate")
    style_count: Series[int] = pa.Field(ge=0, description="Style count")
    recommended_target: Series[float] = pa.Field(ge=0, description="Recommended target")
    increase_needed: Series[float] = pa.Field(ge=0, description="Increase needed")
    issue_type: Series[str] = pa.Field(description="Issue type")
    issue_severity: Series[str] = pa.Field(description="Issue severity")
    current_quantity: Series[float] = pa.Field(ge=0, description="Current quantity")
    target_quantity: Series[float] = pa.Field(ge=0, description="Target quantity")
    recommended_quantity_change_raw: Series[float] = pa.Field(description="Raw recommended quantity change")
    recommended_quantity_change: Series[float] = pa.Field(ge=0, description="Recommended quantity change")
    investment_required: Series[float] = pa.Field(ge=0, nullable=True, description="Investment required")
    current_sell_through_rate: Series[float] = pa.Field(ge=0, le=100, description="Current sell-through rate")
    predicted_sell_through_rate: Series[float] = pa.Field(ge=0, le=100, description="Predicted sell-through rate")
    sell_through_improvement: Series[float] = pa.Field(ge=0, description="Sell-through improvement")
    fast_fish_compliant: Series[str] = pa.Field(description="Fast Fish compliance status")
    business_rationale: Series[str] = pa.Field(description="Business rationale")
    approval_reason: Series[str] = pa.Field(description="Approval reason")
    recommended_action: Series[str] = pa.Field(description="Recommended action")
    recommendation_text: Series[str] = pa.Field(description="Recommendation text")
    
    class Config:
        coerce = True


class Step9SummarySchema(pa.DataFrameModel):
    """Schema for Step 9 summary file (aggregated statistics)"""
    
    total_stores: Series[int] = pa.Field(ge=0, description="Total number of stores analyzed")
    below_minimum_stores: Series[int] = pa.Field(ge=0, description="Number of stores with below-minimum cases")
    total_opportunities: Series[int] = pa.Field(ge=0, description="Total number of opportunities identified")
    total_investment_required: Series[float] = pa.Field(ge=0, description="Total investment required")
    average_unit_price: Series[float] = pa.Field(ge=0, nullable=True, description="Average unit price")
    severity_distribution: Series[str] = pa.Field(description="Distribution of severity tiers")
    validation_coverage: Series[float] = pa.Field(ge=0, le=1, description="Fast Fish validation coverage")
    
    class Config:
        coerce = True


class Step9InputClusteringSchema(pa.DataFrameModel):
    """Schema for Step 9 input clustering results"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    Cluster: Series[str] = pa.Field(description="Cluster identifier")
    
    class Config:
        coerce = True


class Step9InputStoreConfigSchema(pa.DataFrameModel):
    """Schema for Step 9 input store configuration data"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    target_sty_cnt_avg: Series[float] = pa.Field(ge=0, nullable=True, description="Target style count average")
    sty_sal_amt: Series[str] = pa.Field(nullable=True, description="Style sales amount JSON-like content")
    season_name: Series[str] = pa.Field(description="Season name")
    sex_name: Series[str] = pa.Field(description="Sex name")
    display_location_name: Series[str] = pa.Field(description="Display location name")
    big_class_name: Series[str] = pa.Field(description="Big class name")
    sub_cate_name: Series[str] = pa.Field(description="Subcategory name")
    sty_code: Series[str] = pa.Field(nullable=True, description="Style code")
    
    class Config:
        coerce = True


class Step9InputQuantitySchema(pa.DataFrameModel):
    """Schema for Step 9 input quantity data"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    spu_code: Series[str] = pa.Field(description="SPU code")
    spu_sales_amt: Series[float] = pa.Field(ge=0, description="SPU sales amount")
    quantity: Series[float] = pa.Field(ge=0, description="Primary quantity field (required)")
    
    class Config:
        coerce = True


# Common column schemas for reuse across steps
class CommonStep9Schemas:
    """Common column schemas for Step 9 validation"""
    
    @staticmethod
    def get_store_code_schema() -> pa.Field:
        """Store code column schema"""
        return pa.Field(description="Store code identifier")
    
    @staticmethod
    def get_cluster_id_schema() -> pa.Field:
        """Cluster ID column schema"""
        return pa.Field(description="Cluster identifier")
    
    @staticmethod
    def get_category_key_schema() -> pa.Field:
        """Category key column schema"""
        return pa.Field(description="Category grouping key")
    
    @staticmethod
    def get_unit_rate_schema() -> pa.Field:
        """Unit rate column schema"""
        return pa.Field(ge=0, description="Unit rate (units per 15 days)")
    
    @staticmethod
    def get_quantity_change_schema() -> pa.Field:
        """Quantity change column schema (positive only)"""
        return pa.Field(ge=0, description="Quantity change (positive integer)")
    
    @staticmethod
    def get_investment_required_schema() -> pa.Field:
        """Investment required column schema"""
        return pa.Field(ge=0, description="Investment required")
    
    @staticmethod
    def get_severity_tier_schema() -> pa.Field:
        """Severity tier column schema"""
        return pa.Field(description="Severity classification")
    
    @staticmethod
    def get_validation_status_schema() -> pa.Field:
        """Validation status column schema"""
        return pa.Field(nullable=True, description="Fast Fish validation status")


# Validation functions
def validate_step9_results(df: 'pd.DataFrame') -> bool:
    """Validate Step 9 results data"""
    try:
        Step9ResultsSchema.validate(df)
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 9 results validation failed: {e}")
        return False


def validate_step9_opportunities(df: 'pd.DataFrame') -> bool:
    """Validate Step 9 opportunities data"""
    try:
        Step9OpportunitiesSchema.validate(df)
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 9 opportunities validation failed: {e}")
        return False


def validate_step9_summary(df: 'pd.DataFrame') -> bool:
    """Validate Step 9 summary data"""
    try:
        Step9SummarySchema.validate(df)
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 9 summary validation failed: {e}")
        return False


def validate_step9_inputs(clustering_df: 'pd.DataFrame', 
                         store_config_df: 'pd.DataFrame', 
                         quantity_df: 'pd.DataFrame') -> bool:
    """Validate Step 9 input data"""
    try:
        # Only validate clustering data if it's not empty
        if not clustering_df.empty:
            Step9InputClusteringSchema.validate(clustering_df)
        
        # Only validate store config data if it's not empty
        if not store_config_df.empty:
            Step9InputStoreConfigSchema.validate(store_config_df)
        
        # Only validate quantity data if it's not empty
        if not quantity_df.empty:
            Step9InputQuantitySchema.validate(quantity_df)
        
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 9 input validation failed: {e}")
        return False


def validate_positive_only_quantities(df: 'pd.DataFrame', quantity_column: str = "recommended_quantity_change") -> bool:
    """Validate that all quantity changes are positive (Step 9 specific)"""
    try:
        if quantity_column in df.columns:
            quantities = df[quantity_column].dropna()
            return bool((quantities >= 0).all())
        return True
    except Exception as e:
        print(f"Positive quantity validation failed: {e}")
        return False


def validate_below_minimum_logic(df: 'pd.DataFrame') -> bool:
    """Validate below minimum detection logic"""
    try:
        if "unit_rate" in df.columns and "minimum_unit_rate" in df.columns and "below_minimum" in df.columns:
            # Check that below_minimum flag is correctly set
            below_min_cases = df["below_minimum"] == True
            unit_rates = df.loc[below_min_cases, "unit_rate"]
            min_rates = df.loc[below_min_cases, "minimum_unit_rate"]
            
            # All below minimum cases should have unit_rate < minimum_unit_rate
            return bool((unit_rates < min_rates).all())
        return True
    except Exception as e:
        print(f"Below minimum logic validation failed: {e}")
        return False

__all__ = [
    'Step9ResultsSchema',
    'Step9OpportunitiesSchema',
    'Step9SummarySchema',
    'Step9InputClusteringSchema',
    'Step9InputStoreConfigSchema',
    'Step9InputQuantitySchema',
]
