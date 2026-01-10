#!/usr/bin/env python3
"""
Domain-Specific Validation Functions

This module contains domain-specific validation functions for time series, coordinates, and sales data.

Author: Data Pipeline
Date: 2025-01-03
"""

import pandas as pd
import logging
from typing import Dict, Any

# Set up logging
logger = logging.getLogger(__name__)


def validate_time_series_continuity(df: pd.DataFrame, time_column: str = 'time') -> Dict[str, Any]:
    """
    Validate time series continuity for weather data.
    
    Args:
        df: DataFrame with time series data
        time_column: Name of the time column
    
    Returns:
        Dictionary with continuity analysis
    """
    if time_column not in df.columns:
        return {'error': f'Time column {time_column} not found'}
    
    try:
        df_time = df.copy()
        df_time[time_column] = pd.to_datetime(df_time[time_column])
        time_diff = df_time[time_column].diff().dropna()
        expected_hourly = pd.Timedelta(hours=1)
        
        # Check if most intervals are hourly (allow some gaps)
        hourly_intervals = (time_diff == expected_hourly).sum()
        
        return {
            'total_intervals': len(time_diff),
            'hourly_intervals': hourly_intervals,
            'continuity_pct': hourly_intervals / len(time_diff) * 100,
            'gaps': len(time_diff) - hourly_intervals,
            'expected_frequency': 'hourly'
        }
    except Exception as e:
        return {'error': f'Time series analysis failed: {str(e)}'}


def validate_coordinate_consistency(df: pd.DataFrame, lat_col: str = 'latitude', lon_col: str = 'longitude') -> Dict[str, Any]:
    """
    Validate coordinate consistency for geographic data.
    
    Args:
        df: DataFrame with coordinate data
        lat_col: Name of the latitude column
        lon_col: Name of the longitude column
    
    Returns:
        Dictionary with coordinate analysis
    """
    if lat_col not in df.columns or lon_col not in df.columns:
        return {'error': f'Coordinate columns {lat_col} or {lon_col} not found'}
    
    try:
        unique_lat = df[lat_col].nunique()
        unique_lon = df[lon_col].nunique()
        
        return {
            'unique_latitudes': unique_lat,
            'unique_longitudes': unique_lon,
            'consistent_location': unique_lat == 1 and unique_lon == 1,
            'coordinate_pairs': df[[lat_col, lon_col]].drop_duplicates().shape[0]
        }
    except Exception as e:
        return {'error': f'Coordinate analysis failed: {str(e)}'}


def validate_sales_consistency(category_df: pd.DataFrame, spu_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate sales consistency between category and SPU data.
    
    Args:
        category_df: Category sales DataFrame
        spu_df: SPU sales DataFrame
    
    Returns:
        Dictionary with consistency analysis
    """
    try:
        # Check store code consistency
        category_stores = set(category_df['str_code'].astype(str))
        spu_stores = set(spu_df['str_code'].astype(str))
        
        # Check sales amount consistency
        category_total = category_df['sal_amt'].sum()
        spu_total = spu_df['spu_sales_amt'].sum()
        
        return {
            'store_consistency': {
                'category_stores': len(category_stores),
                'spu_stores': len(spu_stores),
                'common_stores': len(category_stores & spu_stores),
                'category_only': len(category_stores - spu_stores),
                'spu_only': len(spu_stores - category_stores)
            },
            'sales_consistency': {
                'category_total': category_total,
                'spu_total': spu_total,
                'difference': abs(category_total - spu_total),
                'difference_pct': abs(category_total - spu_total) / category_total * 100 if category_total > 0 else 0
            }
        }
    except Exception as e:
        return {'error': f'Sales consistency analysis failed: {str(e)}'}

