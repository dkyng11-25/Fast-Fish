import pandas as pd
#!/usr/bin/env python3
"""
Comprehensive Weather Validation Schemas

This module contains comprehensive weather validation schemas that combine multiple
weather components and include store-specific weather data.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandera.pandas as pa
from pandera.typing import Series


class WeatherMetricsSchema(pa.DataFrameModel):
    """Schema for comprehensive weather metrics validation."""
    
    # Temperature
    temperature_2m: Series[float] = pa.Field(nullable=True, ge=-50.0, le=60.0)
    
    # Humidity
    relative_humidity_2m: Series[int] = pa.Field(nullable=True, ge=0, le=100)
    
    # Wind
    wind_speed_10m: Series[float] = pa.Field(nullable=True, ge=0.0, le=100.0)
    wind_direction_10m: Series[int] = pa.Field(nullable=True, ge=0, le=360)
    
    # Precipitation
    precipitation: Series[float] = pa.Field(nullable=True, ge=0.0, le=500.0)
    rain: Series[float] = pa.Field(nullable=True, ge=0.0, le=500.0)
    snowfall: Series[float] = pa.Field(nullable=True, ge=0.0, le=200.0)
    
    # Cloud and weather
    cloud_cover: Series[int] = pa.Field(nullable=True, ge=0, le=100)
    weather_code: Series[int] = pa.Field(nullable=True, ge=0, le=99)
    
    # Pressure
    pressure_msl: Series[float] = pa.Field(nullable=True, ge=800.0, le=1100.0)


class WeatherDataSchema(pa.DataFrameModel):
    """Schema for individual store weather data files with comprehensive validation."""
    
    # Time series data
    time: Series[str] = pa.Field(nullable=True)
    
    # Weather metrics (using comprehensive ranges)
    temperature_2m: Series[float] = pa.Field(nullable=True, ge=-50.0, le=60.0)
    relative_humidity_2m: Series[int] = pa.Field(nullable=True, ge=0, le=100)
    wind_speed_10m: Series[float] = pa.Field(nullable=True, ge=0.0, le=100.0)
    wind_direction_10m: Series[int] = pa.Field(nullable=True, ge=0, le=360)
    precipitation: Series[float] = pa.Field(nullable=True, ge=0.0, le=500.0)
    rain: Series[float] = pa.Field(nullable=True, ge=0.0, le=500.0)
    snowfall: Series[float] = pa.Field(nullable=True, ge=0.0, le=200.0)
    cloud_cover: Series[int] = pa.Field(nullable=True, ge=0, le=100)
    weather_code: Series[int] = pa.Field(nullable=True, ge=0, le=99)
    pressure_msl: Series[float] = pa.Field(nullable=True, ge=800.0, le=1100.0)
    
    # Solar radiation metrics
    direct_radiation: Series[float] = pa.Field(nullable=True, ge=0.0, le=1500.0)
    diffuse_radiation: Series[float] = pa.Field(nullable=True, ge=0.0, le=500.0)
    direct_normal_irradiance: Series[float] = pa.Field(nullable=True, ge=0.0, le=1500.0)
    terrestrial_radiation: Series[float] = pa.Field(nullable=True, ge=0.0, le=1500.0)
    shortwave_radiation: Series[float] = pa.Field(nullable=True, ge=0.0, le=1500.0)
    et0_fao_evapotranspiration: Series[float] = pa.Field(nullable=True, ge=0.0, le=20.0)
    
    # Store and location data
    store_code: Series[int] = pa.Field(nullable=True)
    latitude: Series[float] = pa.Field(nullable=True, ge=-90, le=90)  # Earth latitude bounds
    longitude: Series[float] = pa.Field(nullable=True, ge=-180, le=180)  # Earth longitude bounds


class StoreAltitudeSchema(pa.DataFrameModel):
    """Schema for store altitude data."""
    
    # Store identification
    str_code: Series[int] = pa.Field(ge=10000, le=99999)
    str_name: Series[str] = pa.Field(nullable=True)
    
    # Geographic data
    latitude: Series[float] = pa.Field(nullable=True, ge=-90, le=90)  # Earth latitude bounds
    longitude: Series[float] = pa.Field(nullable=True, ge=-180, le=180)  # Earth longitude bounds
    altitude: Series[float] = pa.Field(nullable=True, ge=0, le=9000)  # Altitude: 0 to 9000m (Mount Everest)


class WeatherExtremesSchema(pa.DataFrameModel):
    """Schema for weather extremes validation based on 2024-2025 research."""
    
    # Temperature extremes
    temperature_min_extreme: Series[float] = pa.Field(
        nullable=True,
        ge=-60.0,  # Record cold (Siberia/Arctic)
        le=0.0
    )
    
    temperature_max_extreme: Series[float] = pa.Field(
        nullable=True,
        ge=40.0,
        le=70.0    # Record heat (desert conditions)
    )
    
    # Precipitation extremes
    precipitation_max_daily: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=500.0   # Extreme daily rainfall (tropical storms)
    )
    
    # Wind extremes
    wind_speed_max: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=150.0   # Hurricane force winds
    )
    
    # Pressure extremes
    pressure_min: Series[float] = pa.Field(
        nullable=True,
        ge=800.0,  # Extreme low pressure (hurricanes)
        le=1100.0
    )
    
    pressure_max: Series[float] = pa.Field(
        nullable=True,
        ge=1000.0,
        le=1100.0  # Extreme high pressure (anticyclones)
    )
    
    # Humidity extremes
    humidity_min: Series[int] = pa.Field(
        nullable=True,
        ge=0,
        le=100
    )
    
    humidity_max: Series[int] = pa.Field(
        nullable=True,
        ge=0,
        le=100
    )
    
    # Radiation extremes
    radiation_max: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=1500.0  # Maximum solar radiation
    )
    
    # Visibility extremes
    visibility_min: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=50.0    # km
    )
    
    visibility_max: Series[float] = pa.Field(
        nullable=True,
        ge=0.0,
        le=50.0    # km
    )

