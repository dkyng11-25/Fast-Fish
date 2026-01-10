#!/usr/bin/env python3
"""
Sell-Through Rate Utility Functions
==================================

Shared canonical functions for sell-through rate calculations used across the pipeline.
Standardizes units, naming conventions, and calculation methods.

Key Functions:
- clip_to_unit_interval: Clip values to [0,1] range
- fraction_to_percentage: Convert 0-1 fractions to 0-100 percentages
- percentage_to_fraction: Convert 0-100 percentages to 0-1 fractions
- calculate_spu_store_day_counts: Count SPU-store-day inventory and sales correctly
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any


def clip_to_unit_interval(x) -> float:
    """Clip a numeric value to [0, 1]. Returns NaN on errors."""
    try:
        if pd.isna(x):
            return np.nan
        return float(np.clip(float(x), 0.0, 1.0))
    except Exception:
        return np.nan


def fraction_to_percentage(frac) -> float:
    """Convert fraction (0–1) to percent (0–100) with clipping and NA-safety."""
    if pd.isna(frac):
        return np.nan
    try:
        return float(np.clip(float(frac), 0.0, 1.0) * 100.0)
    except Exception:
        return np.nan


def percentage_to_fraction(pct) -> float:
    """Convert percent (0–100) to fraction (0–1) with clipping and NA-safety."""
    if pd.isna(pct):
        return np.nan
    try:
        return float(np.clip(float(pct), 0.0, 100.0) / 100.0)
    except Exception:
        return np.nan


def calculate_spu_store_day_counts(
    target_spu_quantity: float,
    stores_in_group: float,
    historical_avg_daily_sales_per_store: float,
    period_days: int = 15
) -> Tuple[float, float]:
    """
    Calculate SPU-store-day inventory and sales counts correctly.
    
    Args:
        target_spu_quantity: Recommended number of SPUs per store
        stores_in_group: Number of stores in the group
        historical_avg_daily_sales_per_store: Average daily SPUs sold per store (historical)
        period_days: Number of days in the period (default 15 for half-month)
        
    Returns:
        Tuple of (inventory_spu_store_days, sales_spu_store_days)
    """
    # SPU-Store-Days Inventory (Recommendation-based)
    # Formula: Target SPU Quantity × Stores in Group × Period Days
    inventory_spu_store_days = np.nan
    if pd.notna(target_spu_quantity) and pd.notna(stores_in_group):
        inventory_spu_store_days = target_spu_quantity * stores_in_group * period_days
    
    # SPU-Store-Days Sales (Historical-based)
    # Formula: Average daily SPUs sold per store × Stores in Group × Period Days
    sales_spu_store_days = np.nan
    if pd.notna(historical_avg_daily_sales_per_store) and pd.notna(stores_in_group):
        sales_spu_store_days = historical_avg_daily_sales_per_store * stores_in_group * period_days
    
    return inventory_spu_store_days, sales_spu_store_days


def calculate_sell_through_rate(
    sales_spu_store_days: float,
    inventory_spu_store_days: float
) -> Tuple[float, float]:
    """
    Calculate sell-through rate as fraction and percentage using official formula.
    
    Formula: SPU-store-day with sales ÷ SPU-store-day with inventory
    
    Args:
        sales_spu_store_days: SPU-store-days of actual sales
        inventory_spu_store_days: SPU-store-days of inventory exposure
        
    Returns:
        Tuple of (sell_through_rate_fraction, sell_through_rate_percentage)
    """
    # Calculate sell-through rate (fraction)
    sell_through_rate_frac = np.nan
    if pd.notna(inventory_spu_store_days) and inventory_spu_store_days > 0 and pd.notna(sales_spu_store_days):
        sell_through_rate_frac = clip_to_unit_interval(sales_spu_store_days / inventory_spu_store_days)
    
    # Convert to percentage
    sell_through_rate_pct = fraction_to_percentage(sell_through_rate_frac)
    
    return sell_through_rate_frac, sell_through_rate_pct


def validate_sell_through_rate(sell_through_rate_frac: float) -> bool:
    """Validate that sell-through rate is within acceptable bounds [0,1]."""
    if pd.isna(sell_through_rate_frac):
        return False
    try:
        return 0.0 <= float(sell_through_rate_frac) <= 1.0
    except Exception:
        return False
