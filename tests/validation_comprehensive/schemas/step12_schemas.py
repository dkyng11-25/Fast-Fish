import pandas as pd
"""
Pandera schemas for Step 12: Sales Performance (Subcategory/SPU) with Real-Unit, Incremental Quantity Recommendations

This module defines comprehensive data validation schemas for Step 12 outputs,
including results and details files.
"""

import pandera.pandas as pa
from pandera.typing import Series
from typing import Optional


class Step12ResultsSchema(pa.DataFrameModel):
    """Schema for Step 12 results file (store-level aggregated results)"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    cluster_id: Series[str] = pa.Field(description="Cluster identifier")
    avg_opportunity_z_score: Series[float] = pa.Field(nullable=True, description="Average opportunity Z-score")
    total_opportunity_value: Series[float] = pa.Field(ge=0, nullable=True, description="Total opportunity value")
    categories_analyzed: Series[float] = pa.Field(ge=0, nullable=True, description="Number of categories analyzed")
    top_quartile_categories: Series[float] = pa.Field(ge=0, nullable=True, description="Number of top quartile categories")
    total_quantity_increase_needed: Series[float] = pa.Field(ge=0, nullable=True, description="Total quantity increase needed")
    total_investment_required: Series[float] = pa.Field(ge=0, nullable=True, description="Total investment required")
    total_current_quantity: Series[float] = pa.Field(ge=0, nullable=True, description="Total current quantity")
    quantity_opportunities_count: Series[float] = pa.Field(ge=0, nullable=True, description="Number of quantity opportunities")
    has_quantity_recommendations: Series[bool] = pa.Field(nullable=True, description="Boolean flag for quantity recommendations")
    store_performance_level: Series[str] = pa.Field(nullable=True, description="Store performance level classification")
    rule12_top_performer: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Rule flag for top performer")
    rule12_performing_well: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Rule flag for performing well")
    rule12_some_opportunity: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Rule flag for some opportunity")
    rule12_good_opportunity: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Rule flag for good opportunity")
    rule12_major_opportunity: Series[float] = pa.Field(ge=0, le=1, nullable=True, description="Rule flag for major opportunity")
    rule12_quantity_increase_recommended: Series[bool] = pa.Field(nullable=True, description="Rule flag for quantity increase recommended")
    rule12_description: Series[str] = pa.Field(nullable=True, description="Rule description")
    rule12_analysis_method: Series[str] = pa.Field(nullable=True, description="Analysis method")
    rule_flag: Series[str] = pa.Field(nullable=True, description="Rule flag")
    opportunity_type: Series[str] = pa.Field(nullable=True, description="Type of opportunity")
    unit_price: Series[float] = pa.Field(ge=0, nullable=True, description="Unit price")
    fast_fish_compliant: Series[str] = pa.Field(nullable=True, description="Fast Fish validation compliance")
    business_rationale: Series[str] = pa.Field(nullable=True, description="Business rationale")
    approval_reason: Series[str] = pa.Field(nullable=True, description="Approval reason")
    investment_required: Series[float] = pa.Field(ge=0, nullable=True, description="Investment required")
    recommended_quantity_change: Series[float] = pa.Field(ge=0, nullable=True, description="Recommended quantity change (positive for increases)")
    period_label: Series[str] = pa.Field(nullable=True, description="Period label")
    target_yyyymm: Series[str] = pa.Field(nullable=True, description="Target year-month")
    target_period: Series[str] = pa.Field(nullable=True, description="Target period")
    
    class Config:
        coerce = True


class Step12DetailsSchema(pa.DataFrameModel):
    """Schema for Step 12 details file (detailed opportunity information)"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    cluster_id: Series[str] = pa.Field(description="Cluster identifier")
    category_key: Series[str] = pa.Field(description="Category grouping key")
    spu_sales: Series[float] = pa.Field(ge=0, description="SPU sales amount")
    sub_cate_name: Series[str] = pa.Field(description="Subcategory name")
    spu_code: Series[str] = pa.Field(description="SPU code")
    opportunity_gap: Series[float] = pa.Field(description="Opportunity gap")
    cluster_top_quartile: Series[float] = pa.Field(ge=0, description="Cluster top quartile value")
    cluster_size: Series[int] = pa.Field(ge=1, description="Cluster size")
    opportunity_gap_z_score: Series[float] = pa.Field(description="Opportunity gap Z-score")
    performance_level: Series[str] = pa.Field(description="Performance level classification")
    rule12_top_performer: Series[float] = pa.Field(ge=0, le=1, description="Rule flag for top performer")
    rule12_performing_well: Series[float] = pa.Field(ge=0, le=1, description="Rule flag for performing well")
    rule12_some_opportunity: Series[float] = pa.Field(ge=0, le=1, description="Rule flag for some opportunity")
    rule12_good_opportunity: Series[float] = pa.Field(ge=0, le=1, description="Rule flag for good opportunity")
    rule12_major_opportunity: Series[float] = pa.Field(ge=0, le=1, description="Rule flag for major opportunity")
    opportunity_value: Series[float] = pa.Field(ge=0, description="Opportunity value")
    exceeds_top_quartile: Series[float] = pa.Field(ge=0, le=1, description="Boolean flag for exceeding top quartile")
    current_quantity: Series[float] = pa.Field(ge=0, description="Current quantity")
    recommended_quantity_increase: Series[float] = pa.Field(ge=0, description="Recommended quantity increase")
    recommended_quantity_change: Series[float] = pa.Field(ge=0, description="Recommended quantity change (positive)")
    unit_price: Series[float] = pa.Field(ge=0, description="Unit price")
    investment_required: Series[float] = pa.Field(ge=0, description="Investment required")
    recommendation_text: Series[str] = pa.Field(description="Recommendation text")
    quantity_recommendation_text: Series[str] = pa.Field(description="Quantity recommendation text")
    opportunity_score: Series[float] = pa.Field(ge=0, description="Opportunity score")
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


class Step12InputClusteringSchema(pa.DataFrameModel):
    """Schema for Step 12 input clustering results"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    Cluster: Series[str] = pa.Field(description="Cluster identifier")
    
    class Config:
        coerce = True


class Step12InputStoreConfigSchema(pa.DataFrameModel):
    """Schema for Step 12 input store configuration data"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    sty_sal_amt: Series[str] = pa.Field(nullable=True, description="Style sales amount JSON-like content")
    season_name: Series[str] = pa.Field(description="Season name")
    sex_name: Series[str] = pa.Field(description="Sex name")
    display_location_name: Series[str] = pa.Field(description="Display location name")
    big_class_name: Series[str] = pa.Field(description="Big class name")
    sub_cate_name: Series[str] = pa.Field(description="Subcategory name")
    
    class Config:
        coerce = True


class Step12InputQuantitySchema(pa.DataFrameModel):
    """Schema for Step 12 input quantity data"""
    
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
class CommonStep12Schemas:
    """Common column schemas for Step 12 validation"""
    
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
    def get_performance_level_schema() -> pa.Field:
        """Performance level column schema"""
        return pa.Field(description="Performance level classification")
    
    @staticmethod
    def get_z_score_schema() -> pa.Field:
        """Z-score column schema"""
        return pa.Field(description="Z-score value")


# Validation functions
def validate_step12_results(df: 'pd.DataFrame') -> bool:
    """Validate Step 12 results data"""
    try:
        Step12ResultsSchema.validate(df)
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 12 results validation failed: {e}")
        return False


def validate_step12_details(df: 'pd.DataFrame') -> bool:
    """Validate Step 12 details data"""
    try:
        Step12DetailsSchema.validate(df)
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 12 details validation failed: {e}")
        return False


def validate_step12_inputs(clustering_df: 'pd.DataFrame', 
                          store_config_df: 'pd.DataFrame', 
                          quantity_df: 'pd.DataFrame') -> bool:
    """Validate Step 12 input data"""
    try:
        # Only validate clustering data if it's not empty
        if not clustering_df.empty:
            Step12InputClusteringSchema.validate(clustering_df)
        
        # Only validate store config data if it's not empty
        if not store_config_df.empty:
            Step12InputStoreConfigSchema.validate(store_config_df)
        
        # Only validate quantity data if it's not empty
        if not quantity_df.empty:
            Step12InputQuantitySchema.validate(quantity_df)
        
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 12 input validation failed: {e}")
        return False


def validate_positive_quantities(df: 'pd.DataFrame', quantity_column: str = "recommended_quantity_change") -> bool:
    """Validate that all quantity changes are positive (Step 12 specific - increases only)"""
    try:
        if quantity_column in df.columns:
            quantities = df[quantity_column].dropna()
            return bool((quantities >= 0).all())
        return True
    except Exception as e:
        print(f"Positive quantity validation failed: {e}")
        return False


def validate_performance_classification(df: pd.DataFrame) -> bool:
    """Validate 5-level performance classification logic"""
    try:
        if "performance_level" in df.columns:
            performance_levels = df["performance_level"].value_counts()
            expected_levels = ["top_performer", "performing_well", "some_opportunity", "good_opportunity", "major_opportunity"]
            return all(level in performance_levels.index for level in expected_levels)
        return True
    except Exception as e:
        print(f"Performance classification validation failed: {e}")
        return False


def validate_z_score_logic(df: pd.DataFrame) -> bool:
    """Validate Z-score calculation logic"""
    try:
        if "opportunity_gap_z_score" in df.columns and "opportunity_gap" in df.columns:
            z_scores = df["opportunity_gap_z_score"].dropna()
            opportunity_gaps = df["opportunity_gap"].dropna()
            
            # Z-scores should be normally distributed around 0
            return bool((z_scores >= -5).all() and (z_scores <= 5).all())
        return True
    except Exception as e:
        print(f"Z-score logic validation failed: {e}")
        return False


def validate_rule_flags_consistency(df: pd.DataFrame) -> bool:
    """Validate that rule flags are consistent with performance levels"""
    try:
        if "performance_level" in df.columns and "rule12_some_opportunity" in df.columns:
            some_opportunity_stores = df[df["rule12_some_opportunity"] == 1]
            if len(some_opportunity_stores) > 0:
                # All stores with some_opportunity flag should have some_opportunity performance level
                return bool((some_opportunity_stores["performance_level"] == "some_opportunity").all())
        return True
    except Exception as e:
        print(f"Rule flags consistency validation failed: {e}")
        return False

__all__ = [
    'Step12ResultsSchema',
    'Step12DetailsSchema',
    'Step12InputClusteringSchema',
    'Step12InputStoreConfigSchema',
    'Step12InputQuantitySchema',
]
