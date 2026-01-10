import pandas as pd
#!/usr/bin/env python3
"""
Temperature Validation Schemas

This module contains temperature-related validation schemas including basic temperature,
feels-like temperature, temperature bands, and calculation schemas.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera.pandas as pa
from pandera.typing import Series


class TemperatureSchema(pa.DataFrameModel):
    """Schema for temperature validation with comprehensive ranges."""
    
    temperature_2m: Series[float] = pa.Field(
        nullable=True, 
        ge=-50.0,  # Extreme cold (Siberia/Arctic conditions)
        le=60.0    # Extreme heat (desert conditions)
    )
    
    # Additional temperature fields for comprehensive validation
    temperature_min: Series[float] = pa.Field(
        nullable=True,
        ge=-60.0,  # Record cold temperatures
        le=50.0
    )
    
    temperature_max: Series[float] = pa.Field(
        nullable=True,
        ge=-40.0,
        le=70.0    # Record hot temperatures
    )
    
    temperature_avg: Series[float] = pa.Field(
        nullable=True,
        ge=-30.0,
        le=50.0
    )


class FeelsLikeTemperatureSchema(pa.DataFrameModel):
    """Schema for feels-like temperature calculation output."""
    
    # Store identification
    store_code: Series[int] = pa.Field(ge=10000, le=99999)
    
    # Elevation data
    elevation: Series[float] = pa.Field(ge=0.0, le=9000.0)  # Altitude in meters
    
    # Average weather metrics
    avg_temperature: Series[float] = pa.Field(ge=-50.0, le=60.0)  # Average temperature in °C
    avg_humidity: Series[float] = pa.Field(ge=0.0, le=100.0)  # Average humidity in %
    avg_wind_speed_kmh: Series[float] = pa.Field(ge=0.0, le=200.0)  # Average wind speed in km/h
    avg_pressure: Series[float] = pa.Field(ge=800.0, le=1100.0)  # Average pressure in hPa
    
    # Feels-like temperature metrics
    feels_like_temperature: Series[float] = pa.Field(ge=-60.0, le=70.0)  # Overall feels-like temperature
    min_feels_like: Series[float] = pa.Field(ge=-80.0, le=70.0)  # Minimum feels-like temperature
    max_feels_like: Series[float] = pa.Field(ge=-60.0, le=80.0)  # Maximum feels-like temperature
    
    # Seasonal feels-like temperature (configurable column name)
    feels_like_temperature_q3q4_seasonal: Series[float] = pa.Field(
        nullable=True, 
        ge=-60.0, 
        le=70.0
    )  # Seasonal feels-like temperature
    
    # Condition hours
    cold_condition_hours: Series[int] = pa.Field(ge=0)  # Hours with cold conditions
    hot_condition_hours: Series[int] = pa.Field(ge=0)  # Hours with hot conditions
    moderate_condition_hours: Series[int] = pa.Field(ge=0)  # Hours with moderate conditions
    
    # Temperature bands
    temperature_band: Series[str] = pa.Field(nullable=True)  # Temperature band label
    temperature_band_q3q4_seasonal: Series[str] = pa.Field(nullable=True)  # Seasonal temperature band


class TemperatureBandsSchema(pa.DataFrameModel):
    """Schema for temperature bands summary output."""
    
    # Temperature band information
    Temperature_Band: Series[str] = pa.Field(nullable=True)  # Band label (e.g., "10°C to 15°C")
    Store_Count: Series[int] = pa.Field(ge=0)  # Number of stores in this band
    Min_Temp: Series[float] = pa.Field(ge=-60.0, le=70.0)  # Minimum temperature in band
    Max_Temp: Series[float] = pa.Field(ge=-60.0, le=70.0)  # Maximum temperature in band
    Avg_Temp: Series[float] = pa.Field(ge=-60.0, le=70.0)  # Average temperature in band


class FeelsLikeCalculationSchema(pa.DataFrameModel):
    """Schema for comprehensive feels-like temperature calculation validation."""
    
    # Store identification
    store_code: Series[int] = pa.Field(ge=10000, le=99999)
    
    # Weather data
    temperature: Series[float] = pa.Field(ge=-50.0, le=60.0)
    humidity: Series[float] = pa.Field(ge=0.0, le=100.0)
    wind_speed: Series[float] = pa.Field(ge=0.0, le=200.0)
    pressure: Series[float] = pa.Field(ge=800.0, le=1100.0)
    
    # Calculated feels-like temperature
    feels_like: Series[float] = pa.Field(ge=-60.0, le=70.0)
    
    # Heat index components
    heat_index: Series[float] = pa.Field(nullable=True, ge=-50.0, le=80.0)
    
    # Wind chill components
    wind_chill: Series[float] = pa.Field(nullable=True, ge=-80.0, le=20.0)
    
    # Humidity adjustment
    humidity_adjustment: Series[float] = pa.Field(nullable=True, ge=-10.0, le=10.0)
    
    # Wind adjustment
    wind_adjustment: Series[float] = pa.Field(nullable=True, ge=-15.0, le=5.0)
    
    # Pressure adjustment
    pressure_adjustment: Series[float] = pa.Field(nullable=True, ge=-5.0, le=5.0)
    
    # Final calculation components
    base_temperature: Series[float] = pa.Field(ge=-50.0, le=60.0)
    total_adjustment: Series[float] = pa.Field(ge=-20.0, le=20.0)
    
    # Quality metrics
    calculation_confidence: Series[float] = pa.Field(ge=0.0, le=1.0)
    data_completeness: Series[float] = pa.Field(ge=0.0, le=1.0)

