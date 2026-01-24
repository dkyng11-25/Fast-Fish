#!/usr/bin/env python3
"""
SPU Eligibility Evaluator for Step 7

This module provides explicit eligibility evaluation at SPU × Store × Period level.
The eligibility status is surfaced as an explicit output for downstream modules.

ELIGIBILITY STATUS:
- ELIGIBLE: SPU's climate & season bands align with store's feel-like temperature and period
- INELIGIBLE: Clear mismatch (e.g., winter-only SPU in hot period/store)
- UNKNOWN: Insufficient signal (conservatively treated downstream)

Author: Data Pipeline Team
Date: January 2026
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List
import pandas as pd
import numpy as np

from climate_config import (
    TemperatureBand,
    SeasonPhase,
    CATEGORY_TEMPERATURE_MAPPING,
    TEMPERATURE_THRESHOLDS,
    MONTH_TO_SEASON,
    SEASON_APPROPRIATE_BANDS,
)


class EligibilityStatus(Enum):
    """Explicit eligibility status for SPU × Store × Period."""
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    UNKNOWN = "UNKNOWN"


@dataclass
class EligibilityResult:
    """Complete eligibility evaluation result."""
    status: EligibilityStatus
    reason: str
    climate_match: bool
    season_match: bool
    store_temperature: Optional[float]
    spu_temperature_band: str
    current_season: str
    

def get_spu_temperature_band(category_name: Optional[str]) -> TemperatureBand:
    """
    Determine the temperature band for an SPU based on its category.
    
    Args:
        category_name: Product category name (sub_cate_name)
    
    Returns:
        TemperatureBand enum value
    """
    if category_name is None:
        return TemperatureBand.ALL_SEASON
    
    if category_name in CATEGORY_TEMPERATURE_MAPPING:
        return CATEGORY_TEMPERATURE_MAPPING[category_name]
    
    for keyword, band in CATEGORY_TEMPERATURE_MAPPING.items():
        if keyword in category_name or category_name in keyword:
            return band
    
    return TemperatureBand.ALL_SEASON


def get_current_season(period_label: str) -> SeasonPhase:
    """
    Determine the current season phase from a period label.
    
    Args:
        period_label: Period in format YYYYMMA or YYYYMMB (e.g., "202506A")
    
    Returns:
        SeasonPhase enum value
    """
    try:
        month = int(period_label[4:6])
        return MONTH_TO_SEASON.get(month, SeasonPhase.SPRING_TRANSITION)
    except (ValueError, IndexError):
        return SeasonPhase.SPRING_TRANSITION


def temperature_matches_band(temperature: float, band: TemperatureBand) -> bool:
    """Check if a temperature value falls within a temperature band."""
    if band == TemperatureBand.ALL_SEASON:
        return True
    min_temp, max_temp = TEMPERATURE_THRESHOLDS[band]
    return min_temp <= temperature < max_temp


def is_season_appropriate(spu_band: TemperatureBand, current_season: SeasonPhase) -> bool:
    """Check if an SPU's temperature band is appropriate for the current season."""
    if spu_band == TemperatureBand.ALL_SEASON:
        return True
    appropriate_bands = SEASON_APPROPRIATE_BANDS.get(current_season, [TemperatureBand.ALL_SEASON])
    return spu_band in appropriate_bands


def evaluate_eligibility(
    store_temperature: Optional[float],
    category_name: Optional[str],
    period_label: str
) -> EligibilityResult:
    """
    Evaluate SPU eligibility for a specific store and period.
    
    This is the core eligibility evaluation function that determines whether
    an SPU should be considered for recommendations at a given store.
    
    Args:
        store_temperature: Current feels-like temperature at store (None if unavailable)
        category_name: Product category name (sub_cate_name)
        period_label: Current period (e.g., "202506A")
    
    Returns:
        EligibilityResult with status, reason, and component flags
    """
    spu_band = get_spu_temperature_band(category_name)
    current_season = get_current_season(period_label)
    
    # Handle ALL_SEASON products - always eligible
    if spu_band == TemperatureBand.ALL_SEASON:
        return EligibilityResult(
            status=EligibilityStatus.ELIGIBLE,
            reason="All-season product, no climate/time restriction",
            climate_match=True,
            season_match=True,
            store_temperature=store_temperature,
            spu_temperature_band=spu_band.value,
            current_season=current_season.value
        )
    
    # Evaluate season match (time gate)
    season_match = is_season_appropriate(spu_band, current_season)
    
    # Evaluate climate match (temperature gate)
    if store_temperature is None or pd.isna(store_temperature):
        # No temperature data - UNKNOWN status
        if not season_match:
            return EligibilityResult(
                status=EligibilityStatus.INELIGIBLE,
                reason=f"Season mismatch: {spu_band.value} products not appropriate for {current_season.value}",
                climate_match=False,  # Unknown, but conservative
                season_match=False,
                store_temperature=None,
                spu_temperature_band=spu_band.value,
                current_season=current_season.value
            )
        return EligibilityResult(
            status=EligibilityStatus.UNKNOWN,
            reason="Temperature data unavailable, season match OK",
            climate_match=False,  # Unknown
            season_match=True,
            store_temperature=None,
            spu_temperature_band=spu_band.value,
            current_season=current_season.value
        )
    
    climate_match = temperature_matches_band(store_temperature, spu_band)
    
    # Determine final eligibility
    if season_match and climate_match:
        return EligibilityResult(
            status=EligibilityStatus.ELIGIBLE,
            reason=f"Climate ({store_temperature:.1f}°C) and season ({current_season.value}) match {spu_band.value} band",
            climate_match=True,
            season_match=True,
            store_temperature=store_temperature,
            spu_temperature_band=spu_band.value,
            current_season=current_season.value
        )
    elif not season_match:
        return EligibilityResult(
            status=EligibilityStatus.INELIGIBLE,
            reason=f"Season mismatch: {spu_band.value} products not appropriate for {current_season.value}",
            climate_match=climate_match,
            season_match=False,
            store_temperature=store_temperature,
            spu_temperature_band=spu_band.value,
            current_season=current_season.value
        )
    else:  # season_match but not climate_match
        min_t, max_t = TEMPERATURE_THRESHOLDS[spu_band]
        return EligibilityResult(
            status=EligibilityStatus.INELIGIBLE,
            reason=f"Climate mismatch: store {store_temperature:.1f}°C outside {spu_band.value} band ({min_t}-{max_t}°C)",
            climate_match=False,
            season_match=True,
            store_temperature=store_temperature,
            spu_temperature_band=spu_band.value,
            current_season=current_season.value
        )


def add_eligibility_to_dataframe(
    df: pd.DataFrame,
    temperature_df: Optional[pd.DataFrame],
    period_label: str,
    category_column: str = 'sub_cate_name',
    store_column: str = 'str_code'
) -> pd.DataFrame:
    """
    Add eligibility columns to a DataFrame of SPU recommendations.
    
    This function evaluates eligibility for each row and adds explicit
    eligibility columns that can be used by downstream modules.
    
    Args:
        df: DataFrame with SPU recommendations
        temperature_df: Store temperature data (optional)
        period_label: Current period (e.g., "202506A")
        category_column: Column name for product category
        store_column: Column name for store identifier
    
    Returns:
        DataFrame with added eligibility columns
    """
    result_df = df.copy()
    
    # Initialize eligibility columns
    result_df['eligibility_status'] = EligibilityStatus.UNKNOWN.value
    result_df['eligibility_reason'] = ''
    result_df['climate_match'] = False
    result_df['season_match'] = False
    result_df['store_temperature'] = np.nan
    result_df['spu_temperature_band'] = 'All'
    result_df['current_season'] = get_current_season(period_label).value
    
    # Merge temperature data if available
    if temperature_df is not None:
        temp_df = temperature_df.copy()
        if 'store_code' in temp_df.columns:
            temp_df = temp_df.rename(columns={'store_code': store_column})
        temp_df[store_column] = temp_df[store_column].astype(str)
        
        if 'feels_like_temp' in temp_df.columns:
            temp_col = 'feels_like_temp'
        elif 'temperature' in temp_df.columns:
            temp_col = 'temperature'
        elif 'avg_temp' in temp_df.columns:
            temp_col = 'avg_temp'
        else:
            temp_col = None
        
        if temp_col:
            result_df = result_df.merge(
                temp_df[[store_column, temp_col]].rename(columns={temp_col: '_temp'}),
                on=store_column,
                how='left'
            )
            result_df['store_temperature'] = result_df['_temp']
            result_df = result_df.drop(columns=['_temp'], errors='ignore')
    
    # Evaluate eligibility for each row
    for idx, row in result_df.iterrows():
        category = row.get(category_column, None)
        store_temp = row.get('store_temperature', np.nan)
        store_temp = None if pd.isna(store_temp) else float(store_temp)
        
        eligibility = evaluate_eligibility(store_temp, category, period_label)
        
        result_df.at[idx, 'eligibility_status'] = eligibility.status.value
        result_df.at[idx, 'eligibility_reason'] = eligibility.reason
        result_df.at[idx, 'climate_match'] = eligibility.climate_match
        result_df.at[idx, 'season_match'] = eligibility.season_match
        result_df.at[idx, 'spu_temperature_band'] = eligibility.spu_temperature_band
    
    return result_df


def get_eligibility_summary(df: pd.DataFrame) -> Dict[str, int]:
    """
    Get summary statistics of eligibility distribution.
    
    Args:
        df: DataFrame with eligibility_status column
    
    Returns:
        Dictionary with counts for each eligibility status
    """
    if 'eligibility_status' not in df.columns:
        return {'ELIGIBLE': 0, 'INELIGIBLE': 0, 'UNKNOWN': 0}
    
    counts = df['eligibility_status'].value_counts().to_dict()
    return {
        'ELIGIBLE': counts.get('ELIGIBLE', 0),
        'INELIGIBLE': counts.get('INELIGIBLE', 0),
        'UNKNOWN': counts.get('UNKNOWN', 0),
        'total': len(df)
    }
