import pandas as pd
"""
Pandera schemas for Step 14: Enhanced Fast Fish Format

This module defines comprehensive data validation schemas for Step 14 outputs,
ensuring complete outputFormat.md compliance and data quality.
"""

import pandera.pandas as pa
from pandera.typing import Series, DataFrame
from typing import Optional


class FastFishFormatSchema(pa.DataFrameModel):
    """Schema for Enhanced Fast Fish Format output."""
    
    # Basic identification
    Year: Series[int] = pa.Field(description="Year")
    Month: Series[int] = pa.Field(description="Month")
    Period: Series[str] = pa.Field(description="Period (A, B, or full)")
    Store_Group_Name: Series[str] = pa.Field(description="Store group name")
    Target_Style_Tags: Series[str] = pa.Field(description="Target style tags as string")
    
    # Quantity fields
    Current_SPU_Quantity: Series[int] = pa.Field(description="Current SPU quantity")
    Target_SPU_Quantity: Series[int] = pa.Field(description="Target SPU quantity")
    ΔQty: Series[int] = pa.Field(description="Quantity difference (Target - Current)")
    
    # Rationale and benefit
    Data_Based_Rationale: Series[str] = pa.Field(description="Data-based rationale", nullable=True)
    Expected_Benefit: Series[str] = pa.Field(description="Expected benefit", nullable=True)
    
    # Store and sales metrics
    Stores_In_Group_Selling_This_Category: Series[int] = pa.Field(description="Number of stores selling this category")
    Total_Current_Sales: Series[float] = pa.Field(description="Total current sales")
    Avg_Sales_Per_SPU: Series[float] = pa.Field(description="Average sales per SPU")
    
    # Customer mix percentages
    men_percentage: Series[float] = pa.Field(description="Men percentage")
    women_percentage: Series[float] = pa.Field(description="Women percentage")
    unisex_percentage: Series[float] = pa.Field(description="Unisex percentage")
    
    # Display location percentages
    front_store_percentage: Series[float] = pa.Field(description="Front store percentage")
    back_store_percentage: Series[float] = pa.Field(description="Back store percentage")
    
    # Seasonal percentages
    summer_percentage: Series[float] = pa.Field(description="Summer percentage")
    spring_percentage: Series[float] = pa.Field(description="Spring percentage")
    autumn_percentage: Series[float] = pa.Field(description="Autumn percentage")
    winter_percentage: Series[float] = pa.Field(description="Winter percentage")
    
    # Location and temperature
    Display_Location: Series[str] = pa.Field(description="Display location")
    Temp_14d_Avg: Series[float] = pa.Field(description="14-day average temperature", nullable=True)
    FeelsLike_Temp_Period_Avg: Series[float] = pa.Field(description="Feels like temperature period average", nullable=True)
    
    # Historical sell-through
    Historical_ST: Series[float] = pa.Field(description="Historical sell-through rate", nullable=True)
    Historical_Sell_Through_Rate: Series[float] = pa.Field(description="Historical sell-through rate (explicit)", nullable=True)
    
    # Dimensional components
    Season: Series[str] = pa.Field(description="Season", nullable=True)
    Gender: Series[str] = pa.Field(description="Gender", nullable=True)
    Location: Series[str] = pa.Field(description="Location", nullable=True)
    Category: Series[str] = pa.Field(description="Category", nullable=True)
    Subcategory: Series[str] = pa.Field(description="Subcategory", nullable=True)
    
    # Store group details
    Store_Codes_In_Group: Series[str] = pa.Field(description="Store codes in group")
    Store_Count_In_Group: Series[int] = pa.Field(description="Store count in group")
    
    # Optimization and suitability
    Optimization_Target: Series[str] = pa.Field(description="Optimization target")
    Temperature_Suitability: Series[str] = pa.Field(description="Temperature suitability", nullable=True)
    
    # Parsed components
    Parsed_Season: Series[str] = pa.Field(description="Parsed season", nullable=True)
    Parsed_Gender: Series[str] = pa.Field(description="Parsed gender", nullable=True)
    Parsed_Location: Series[str] = pa.Field(description="Parsed location", nullable=True)
    Parsed_Category: Series[str] = pa.Field(description="Parsed category", nullable=True)
    Parsed_Subcategory: Series[str] = pa.Field(description="Parsed subcategory", nullable=True)


class FastFishValidationSchema(pa.DataFrameModel):
    """Schema for Fast Fish validation metadata."""
    
    # Basic validation fields
    validation_timestamp: Series[str] = pa.Field(description="Validation timestamp")
    period_label: Series[str] = pa.Field(description="Period label")
    total_records: Series[int] = pa.Field(description="Total records validated")
    validation_status: Series[str] = pa.Field(description="Validation status")
    
    # Data quality metrics
    schema_validation_passed: Series[bool] = pa.Field(description="Schema validation passed")
    dimensional_parsing_passed: Series[bool] = pa.Field(description="Dimensional parsing passed")
    mathematical_consistency_passed: Series[bool] = pa.Field(description="Mathematical consistency passed")
    
    # Error and warning counts
    total_errors: Series[int] = pa.Field(description="Total errors")
    total_warnings: Series[int] = pa.Field(description="Total warnings")
    
    # Specific validation results
    percentage_sum_validation: Series[bool] = pa.Field(description="Percentage sum validation passed")
    quantity_consistency_validation: Series[bool] = pa.Field(description="Quantity consistency validation passed")
    temperature_range_validation: Series[bool] = pa.Field(description="Temperature range validation passed")


class FastFishMismatchSchema(pa.DataFrameModel):
    """Schema for Fast Fish dimensional mismatch report."""
    
    # Record identification
    record_index: Series[int] = pa.Field(description="Record index")
    Store_Group_Name: Series[str] = pa.Field(description="Store group name")
    Target_Style_Tags: Series[str] = pa.Field(description="Original target style tags")
    
    # Mismatch details
    mismatch_type: Series[str] = pa.Field(description="Type of mismatch")
    expected_value: Series[str] = pa.Field(description="Expected value", nullable=True)
    actual_value: Series[str] = pa.Field(description="Actual value", nullable=True)
    severity: Series[str] = pa.Field(description="Mismatch severity")
    
    # Parsing details
    parsing_confidence: Series[float] = pa.Field(description="Parsing confidence score", nullable=True)
    suggested_correction: Series[str] = pa.Field(description="Suggested correction", nullable=True)


# Common column schemas for reuse
class CommonColumns:
    """Common column schemas used across Step 14 outputs."""
    
    # Basic identification
    YEAR = pa.Field(description="Year")
    MONTH = pa.Field(description="Month")
    PERIOD = pa.Field(description="Period (A, B, or full)")
    STORE_GROUP_NAME = pa.Field(description="Store group name")
    
    # Quantity fields
    CURRENT_SPU_QUANTITY = pa.Field(description="Current SPU quantity")
    TARGET_SPU_QUANTITY = pa.Field(description="Target SPU quantity")
    DELTA_QUANTITY = pa.Field(description="Quantity difference (Target - Current)")
    
    # Percentage fields
    MEN_PERCENTAGE = pa.Field(description="Men percentage")
    WOMEN_PERCENTAGE = pa.Field(description="Women percentage")
    UNISEX_PERCENTAGE = pa.Field(description="Unisex percentage")
    FRONT_STORE_PERCENTAGE = pa.Field(description="Front store percentage")
    BACK_STORE_PERCENTAGE = pa.Field(description="Back store percentage")
    
    # Seasonal percentages
    SUMMER_PERCENTAGE = pa.Field(description="Summer percentage")
    SPRING_PERCENTAGE = pa.Field(description="Spring percentage")
    AUTUMN_PERCENTAGE = pa.Field(description="Autumn percentage")
    WINTER_PERCENTAGE = pa.Field(description="Winter percentage")
    
    # Temperature fields
    TEMP_14D_AVG = pa.Field(description="14-day average temperature", nullable=True)
    FEELS_LIKE_TEMP_PERIOD_AVG = pa.Field(description="Feels like temperature period average", nullable=True)
    
    # Historical fields
    HISTORICAL_ST = pa.Field(description="Historical sell-through rate", nullable=True)
    HISTORICAL_SELL_THROUGH_RATE = pa.Field(description="Historical sell-through rate (explicit)", nullable=True)
    
    # Dimensional components
    SEASON = pa.Field(description="Season", nullable=True)
    GENDER = pa.Field(description="Gender", nullable=True)
    LOCATION = pa.Field(description="Location", nullable=True)
    CATEGORY = pa.Field(description="Category", nullable=True)
    SUBCATEGORY = pa.Field(description="Subcategory", nullable=True)


# Table schemas for input validation
class InputConsolidatedResultsSchema(pa.DataFrameModel):
    """Schema for Step 13 consolidated results input."""
    
    str_code: Series[str] = pa.Field(description="Store code")
    spu_code: Series[str] = pa.Field(description="SPU code")
    sub_cate_name: Series[str] = pa.Field(description="Subcategory name", nullable=True)
    recommended_quantity_change: Series[float] = pa.Field(description="Recommended quantity change")
    rule_source: Series[str] = pa.Field(description="Source rule identifier")
    cluster: Series[int] = pa.Field(description="Cluster ID")
    current_quantity: Series[float] = pa.Field(description="Current quantity")
    investment_required: Series[float] = pa.Field(description="Investment required")
    unit_price: Series[float] = pa.Field(description="Unit price")
    business_rationale: Series[str] = pa.Field(description="Business rationale", nullable=True)
    opportunity_score: Series[float] = pa.Field(description="Opportunity score", nullable=True)
    period_label: Series[str] = pa.Field(description="Period label")
    target_yyyymm: Series[str] = pa.Field(description="Target year-month")
    target_period: Series[str] = pa.Field(description="Target period")


class InputClusterMappingSchema(pa.DataFrameModel):
    """Schema for cluster mapping input."""
    
    spu_code: Series[str] = pa.Field(description="SPU code")
    cluster: Series[int] = pa.Field(description="Cluster ID")
    subcategory: Series[str] = pa.Field(description="Subcategory name", nullable=True)
    category: Series[str] = pa.Field(description="Category name", nullable=True)

