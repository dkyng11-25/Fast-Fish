import pandas as pd
"""
Pandera schemas for Step 8: Imbalanced Allocation Rule with Quantity Rebalancing

This module defines comprehensive data validation schemas for Step 8 outputs,
including results, cases, and z-score analysis files.
"""

import pandera.pandas as pa
from pandera.typing import Series
from typing import Optional


class Step8ResultsSchema(pa.DataFrameModel):
    """Schema for Step 8 results file (store-level aggregated results) - matches actual output structure"""
    
    # Core identifiers
    str_code: Series[str] = pa.Field(description="Store code identifier")
    cluster_id: Series[int] = pa.Field(description="Cluster identifier") # Changed back to cluster_id: int to match renamed column
    
    # Step 8 specific fields
    imbalanced_spus_count: Series[int] = pa.Field(ge=0, nullable=True, description="Count of imbalanced SPUs") 
    avg_z_score: Series[int] = pa.Field(nullable=True, description="Average Z-score") 
    avg_abs_z_score: Series[int] = pa.Field(ge=0, nullable=True, description="Average absolute Z-score") 
    total_adjustment_needed: Series[int] = pa.Field(nullable=True, description="Total adjustment needed") 
    over_allocated_count: Series[int] = pa.Field(ge=0, nullable=True, description="Count of over-allocated items") 
    under_allocated_count: Series[int] = pa.Field(ge=0, nullable=True, description="Count of under-allocated items") 
    
    # Rule fields
    rule8_imbalanced_spu: Series[int] = pa.Field(ge=0, le=1, description="Rule 8 imbalanced SPU flag") 
    rule8_description: Series[str] = pa.Field(nullable=True, description="Rule 8 description")
    rule8_threshold: Series[float] = pa.Field(nullable=True, description="Rule 8 threshold") 
    rule8_analysis_level: Series[str] = pa.Field(nullable=True, description="Rule 8 analysis level")
    
    class Config:
        coerce = True


class Step8CasesSchema(pa.DataFrameModel):
    """Schema for Step 8 cases file (detailed case information) - matches actual output structure"""
    
    # Core identifiers
    str_code: Series[object] = pa.Field(nullable=True, description="Store code identifier") 
    # Removed: str_name
    # Removed: cate_name
    # Removed: sub_cate_name
    # Removed: spu_code
    # Removed: spu_sales_amt (as per latest df.info())
    # Removed: quantity
    # Removed: unit_price
    # Removed: investment_per_unit
    # Removed: Cluster
    # Removed: sty_code
    
    # Only the columns present in the empty file, all nullable and object type
    category_key: Series[object] = pa.Field(nullable=True, description="Category grouping key")
    z_score: Series[object] = pa.Field(nullable=True, description="Z-score")
    imbalance_type: Series[object] = pa.Field(nullable=True, description="Type of imbalance")
    
    class Config:
        coerce = True


class Step8ZScoreAnalysisSchema(pa.DataFrameModel):
    """Schema for Step 8 z-score analysis file (cluster-level statistics) - matches actual output structure"""
    
    # Core identifiers
    str_code: Series[object] = pa.Field(nullable=True, description="Store code identifier")
    Cluster: Series[object] = pa.Field(nullable=True, description="Cluster identifier")
    # Removed: str_name
    # Removed: cate_name
    # Removed: sub_cate_name
    # Removed: spu_code
    # Removed: spu_sales_amt
    # Removed: quantity
    # Removed: unit_price
    # Removed: investment_per_unit
    
    # Only the columns present in the empty file, all nullable and object type
    category_key: Series[object] = pa.Field(nullable=True, description="Category grouping key") 
    allocation_value: Series[object] = pa.Field(nullable=True, description="Allocation value") 
    z_score: Series[object] = pa.Field(nullable=True, description="Z-score") 
    cluster_mean: Series[object] = pa.Field(nullable=True, description="Cluster mean") 
    cluster_std: Series[object] = pa.Field(nullable=True, description="Cluster standard deviation") 
    cluster_size: Series[object] = pa.Field(nullable=True, description="Cluster size") 
    
    class Config:
        coerce = True


class Step8InputClusteringSchema(pa.DataFrameModel):
    """Schema for Step 8 input clustering results - matches actual input structure"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    Cluster: Series[str] = pa.Field(description="Cluster identifier")
    
    class Config:
        coerce = True


class Step8InputStoreConfigSchema(pa.DataFrameModel):
    """Schema for Step 8 input store configuration data"""
    
    str_code: Series[str] = pa.Field(description="Store code identifier")
    target_sty_cnt_avg: Series[float] = pa.Field(ge=0, nullable=True, description="Target style count average")
    sty_sal_amt: Series[float] = pa.Field(ge=0, nullable=True, description="Style sales amount")
    season_name: Series[str] = pa.Field(description="Season name")
    sex_name: Series[str] = pa.Field(description="Sex name")
    display_location_name: Series[str] = pa.Field(description="Display location name")
    big_class_name: Series[str] = pa.Field(description="Big class name")
    sub_cate_name: Series[str] = pa.Field(description="Subcategory name")
    sty_code: Series[str] = pa.Field(nullable=True, description="Style code")
    
    class Config:
        coerce = True


class Step8InputQuantitySchema(pa.DataFrameModel):
    """Schema for Step 8 input quantity data"""
    
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
class CommonStep8Schemas:
    """Common column schemas for Step 8 validation"""
    
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
    def get_allocation_value_schema() -> pa.Field:
        """Allocation value column schema"""
        return pa.Field(ge=0, description="Allocation value")
    
    @staticmethod
    def get_quantity_schema() -> pa.Field:
        """Quantity column schema"""
        return pa.Field(ge=0, description="Quantity value")
    
    @staticmethod
    def get_z_score_schema() -> pa.Field:
        """Z-score column schema"""
        return pa.Field(description="Z-score value")
    
    @staticmethod
    def get_severity_tier_schema() -> pa.Field:
        """Severity tier column schema"""
        return pa.Field(description="Severity classification")


# Validation functions
def validate_step8_results(df: 'pd.DataFrame') -> bool:
    """Validate Step 8 results data"""
    try:
        Step8ResultsSchema.validate(df)
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 8 results validation failed: {e}")
        return False


def validate_step8_cases(df: 'pd.DataFrame') -> bool:
    """Validate Step 8 cases data"""
    try:
        Step8CasesSchema.validate(df)
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 8 cases validation failed: {e}")
        return False


def validate_step8_z_score_analysis(df: 'pd.DataFrame') -> bool:
    """Validate Step 8 z-score analysis data"""
    try:
        Step8ZScoreAnalysisSchema.validate(df)
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 8 z-score analysis validation failed: {e}")
        return False


def validate_step8_inputs(clustering_df: 'pd.DataFrame', 
                         store_config_df: 'pd.DataFrame', 
                         quantity_df: 'pd.DataFrame') -> bool:
    """Validate Step 8 input data"""
    try:
        # Only validate clustering data if it's not empty
        if not clustering_df.empty:
            Step8InputClusteringSchema.validate(clustering_df)
        
        # Only validate store config data if it's not empty
        if not store_config_df.empty:
            Step8InputStoreConfigSchema.validate(store_config_df)
        
        # Only validate quantity data if it's not empty
        if not quantity_df.empty:
            Step8InputQuantitySchema.validate(quantity_df)
        
        return True
    except pa.errors.SchemaError as e:
        print(f"Step 8 input validation failed: {e}")
        return False

__all__ = [
    'Step8ResultsSchema',
    'Step8CasesSchema',
    'Step8ZScoreAnalysisSchema',
    'Step8InputClusteringSchema',
    'Step8InputStoreConfigSchema',
    'Step8InputQuantitySchema',
]
