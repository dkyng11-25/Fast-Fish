import pandas as pd
#!/usr/bin/env python3
"""
Step 14 Fast Fish Validation Schemas

This module contains schemas for Fast Fish format validation from Step 14.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera as pa
from pandera.typing import Series


class FastFishFormatSchema(pa.DataFrameModel):
    """Schema for Fast Fish format output from Step 14."""
    
    # Time information
    Year: Series[int] = pa.Field(ge=2010, le=2040)
    Month: Series[int] = pa.Field(ge=1, le=12)
    Period: Series[str] = pa.Field()
    
    # Store group information
    Store_Group_Name: Series[str] = pa.Field()
    Store_Codes_In_Group: Series[str] = pa.Field()
    Store_Count_In_Group: Series[int] = pa.Field(ge=1)
    
    # SPU information
    Target_Style_Tags: Series[str] = pa.Field()
    Current_SPU_Quantity: Series[int] = pa.Field(ge=0)
    Target_SPU_Quantity: Series[int] = pa.Field(ge=0)
    ΔQty: Series[int] = pa.Field()
    
    # Business information
    Data_Based_Rationale: Series[str] = pa.Field()
    Expected_Benefit: Series[str] = pa.Field(nullable=True)
    Optimization_Target: Series[str] = pa.Field()
    
    # Sales metrics
    Stores_In_Group_Selling_This_Category: Series[int] = pa.Field(ge=0)
    Total_Current_Sales: Series[float] = pa.Field()
    Avg_Sales_Per_SPU: Series[float] = pa.Field()
    
    # Demographics
    men_percentage: Series[float] = pa.Field(ge=0.0, le=100.0)
    women_percentage: Series[float] = pa.Field(ge=0.0, le=100.0)
    unisex_percentage: Series[float] = pa.Field(ge=0.0, le=100.0)
    
    # Location distribution
    front_store_percentage: Series[float] = pa.Field(ge=0.0, le=100.0)
    back_store_percentage: Series[float] = pa.Field(ge=0.0, le=100.0)
    
    # Seasonal distribution
    summer_percentage: Series[float] = pa.Field(ge=0.0, le=100.0)
    spring_percentage: Series[float] = pa.Field(ge=0.0, le=100.0)
    autumn_percentage: Series[float] = pa.Field(ge=0.0, le=100.0)
    winter_percentage: Series[float] = pa.Field(ge=0.0, le=100.0)
    
    # Display and weather
    Display_Location: Series[str] = pa.Field(nullable=True)
    Temp_14d_Avg: Series[float] = pa.Field(ge=-50.0, le=60.0)
    FeelsLike_Temp_Period_Avg: Series[float] = pa.Field(ge=-50.0, le=60.0)
    
    # Performance metrics
    Historical_ST: Series[float] = pa.Field(ge=0.0, le=100.0)
    Historical_Sell_Through_Rate: Series[float] = pa.Field(ge=0.0, le=100.0, nullable=True)
    
    # Categorical information
    Season: Series[str] = pa.Field(nullable=True)
    Gender: Series[str] = pa.Field(nullable=True)
    Location: Series[str] = pa.Field(nullable=True)
    Category: Series[str] = pa.Field(nullable=True)
    Subcategory: Series[str] = pa.Field(nullable=True)
    
    # Parsed information
    Temperature_Suitability: Series[str] = pa.Field(nullable=True)
    Parsed_Season: Series[str] = pa.Field(nullable=True)
    Parsed_Gender: Series[str] = pa.Field(nullable=True)
    Parsed_Location: Series[str] = pa.Field(nullable=True)
    Parsed_Category: Series[str] = pa.Field(nullable=True)
    Parsed_Subcategory: Series[str] = pa.Field(nullable=True)

