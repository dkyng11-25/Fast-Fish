#!/usr/bin/env python3
"""
Step 7 Enhanced: Time-Aware & Climate-Aware Missing SPU Rule

This module extends the original Step 7 logic with climate and time gating conditions
to reduce false-positive recommendations and improve seasonal alignment.

DESIGN PRINCIPLE:
- Preserve original Step 7 rule structure
- Add climate-aware and time-aware gating conditions
- Rule-based (NOT ML-driven) - climate/time act as gates, not predictors

ENHANCEMENT SUMMARY:
- Climate Gate: Only recommend SPUs appropriate for current store temperature
- Time Gate: Only recommend SPUs appropriate for current season phase
- Original adoption-based logic is PRESERVED and runs first

Author: Data Pipeline Team
Date: January 2026
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass

# Import configuration from separate module (CUPID: Composable)
from climate_config import (
    TemperatureBand,
    SeasonPhase,
    CATEGORY_TEMPERATURE_MAPPING,
    TEMPERATURE_THRESHOLDS,
    MONTH_TO_SEASON,
    SEASON_APPROPRIATE_BANDS,
)


@dataclass
class ClimateGateResult:
    """Result of climate gate evaluation."""
    passed: bool
    store_temperature: float
    spu_temperature_band: str
    reason: str


@dataclass
class TimeGateResult:
    """Result of time gate evaluation."""
    passed: bool
    current_season: str
    spu_season_appropriate: bool
    reason: str


@dataclass
class EnhancedRecommendation:
    """Enhanced recommendation with gate results."""
    str_code: str
    spu_code: str
    cluster_id: int
    cluster_adoption: float
    recommended_quantity: float
    expected_investment: float
    climate_gate: ClimateGateResult
    time_gate: TimeGateResult
    final_recommendation: str  # "ADD", "SUPPRESS_CLIMATE", "SUPPRESS_TIME"
    suppression_reason: Optional[str]


# =============================================================================
# HELPER FUNCTIONS: Climate and Time Logic
# =============================================================================

def get_spu_temperature_band(spu_code: str, category_name: Optional[str] = None) -> TemperatureBand:
    """
    Determine the temperature band for an SPU based on its category.
    
    Business Logic:
    - Each product category has an appropriate temperature range
    - If category unknown, default to ALL_SEASON (no climate restriction)
    
    Args:
        spu_code: SPU identifier
        category_name: Product category name (sub_cate_name)
    
    Returns:
        TemperatureBand enum value
    """
    if category_name is None:
        return TemperatureBand.ALL_SEASON
    
    # Check for exact match first
    if category_name in CATEGORY_TEMPERATURE_MAPPING:
        return CATEGORY_TEMPERATURE_MAPPING[category_name]
    
    # Check for partial match (category name contains keyword)
    for keyword, band in CATEGORY_TEMPERATURE_MAPPING.items():
        if keyword in category_name or category_name in keyword:
            return band
    
    # Default: no climate restriction
    return TemperatureBand.ALL_SEASON


def temperature_matches_band(temperature: float, band: TemperatureBand) -> bool:
    """
    Check if a temperature value falls within a temperature band.
    
    Args:
        temperature: Feels-like temperature in Celsius
        band: Target temperature band
    
    Returns:
        True if temperature is appropriate for the band
    """
    min_temp, max_temp = TEMPERATURE_THRESHOLDS[band]
    return min_temp <= temperature < max_temp


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


def is_season_appropriate(spu_band: TemperatureBand, current_season: SeasonPhase) -> bool:
    """
    Check if an SPU's temperature band is appropriate for the current season.
    
    Business Logic:
    - Winter items should not be recommended in summer
    - Summer items should not be recommended in winter
    - Transitional items are appropriate in transition seasons
    - All-season items are always appropriate
    
    Args:
        spu_band: SPU's temperature band
        current_season: Current season phase
    
    Returns:
        True if the SPU is season-appropriate
    """
    appropriate_bands = SEASON_APPROPRIATE_BANDS.get(current_season, [TemperatureBand.ALL_SEASON])
    return spu_band in appropriate_bands


def evaluate_climate_gate(
    store_temperature: float,
    spu_code: str,
    category_name: Optional[str] = None
) -> ClimateGateResult:
    """
    Evaluate the climate gate for a recommendation.
    
    Business Logic:
    - Get SPU's temperature band from category
    - Check if store's current temperature matches the band
    - If match: PASS (allow recommendation)
    - If no match: FAIL (suppress recommendation)
    
    Args:
        store_temperature: Current feels-like temperature at store
        spu_code: SPU identifier
        category_name: Product category name
    
    Returns:
        ClimateGateResult with pass/fail and reason
    """
    spu_band = get_spu_temperature_band(spu_code, category_name)
    
    # ALL_SEASON always passes
    if spu_band == TemperatureBand.ALL_SEASON:
        return ClimateGateResult(
            passed=True,
            store_temperature=store_temperature,
            spu_temperature_band=spu_band.value,
            reason="All-season product, no climate restriction"
        )
    
    # Check temperature match
    if temperature_matches_band(store_temperature, spu_band):
        return ClimateGateResult(
            passed=True,
            store_temperature=store_temperature,
            spu_temperature_band=spu_band.value,
            reason=f"Temperature {store_temperature:.1f}°C matches {spu_band.value} band"
        )
    else:
        min_t, max_t = TEMPERATURE_THRESHOLDS[spu_band]
        return ClimateGateResult(
            passed=False,
            store_temperature=store_temperature,
            spu_temperature_band=spu_band.value,
            reason=f"Temperature {store_temperature:.1f}°C outside {spu_band.value} band ({min_t}-{max_t}°C)"
        )


def evaluate_time_gate(
    period_label: str,
    spu_code: str,
    category_name: Optional[str] = None
) -> TimeGateResult:
    """
    Evaluate the time gate for a recommendation.
    
    Business Logic:
    - Determine current season from period
    - Get SPU's temperature band (proxy for seasonality)
    - Check if SPU is appropriate for current season
    
    Args:
        period_label: Current period (e.g., "202506A")
        spu_code: SPU identifier
        category_name: Product category name
    
    Returns:
        TimeGateResult with pass/fail and reason
    """
    current_season = get_current_season(period_label)
    spu_band = get_spu_temperature_band(spu_code, category_name)
    
    # ALL_SEASON always passes
    if spu_band == TemperatureBand.ALL_SEASON:
        return TimeGateResult(
            passed=True,
            current_season=current_season.value,
            spu_season_appropriate=True,
            reason="All-season product, no time restriction"
        )
    
    # Check season appropriateness
    if is_season_appropriate(spu_band, current_season):
        return TimeGateResult(
            passed=True,
            current_season=current_season.value,
            spu_season_appropriate=True,
            reason=f"{spu_band.value} products appropriate for {current_season.value}"
        )
    else:
        return TimeGateResult(
            passed=False,
            current_season=current_season.value,
            spu_season_appropriate=False,
            reason=f"{spu_band.value} products NOT appropriate for {current_season.value}"
        )


# =============================================================================
# MAIN PROCESSING: Enhanced Step 7 Logic
# =============================================================================

def load_temperature_data(temperature_file: str) -> Optional[pd.DataFrame]:
    """
    Load store temperature data from Step 5 output.
    
    Args:
        temperature_file: Path to temperature CSV file
    
    Returns:
        DataFrame with store temperatures, or None if unavailable
    """
    if not os.path.exists(temperature_file):
        print(f"⚠️ Temperature file not found: {temperature_file}")
        return None
    
    try:
        temp_df = pd.read_csv(temperature_file)
        
        # Standardize column names
        if 'store_code' in temp_df.columns:
            temp_df = temp_df.rename(columns={'store_code': 'str_code'})
        
        temp_df['str_code'] = temp_df['str_code'].astype(str)
        
        # Use feels_like_temp if available, otherwise avg_temp
        if 'feels_like_temp' in temp_df.columns:
            temp_df['temperature'] = temp_df['feels_like_temp']
        elif 'avg_temp' in temp_df.columns:
            temp_df['temperature'] = temp_df['avg_temp']
        else:
            print("⚠️ No temperature column found in data")
            return None
        
        print(f"✅ Loaded temperature data for {len(temp_df):,} stores")
        return temp_df[['str_code', 'temperature', 'temperature_band']].copy()
    
    except Exception as e:
        print(f"❌ Error loading temperature data: {e}")
        return None


def apply_climate_time_gates(
    original_recommendations: pd.DataFrame,
    temperature_data: Optional[pd.DataFrame],
    period_label: str,
    category_column: str = 'sub_cate_name'
) -> pd.DataFrame:
    """
    Apply climate and time gates to original Step 7 recommendations.
    
    This function PRESERVES the original recommendations and ADDS gate results.
    It does NOT modify the original logic, only adds filtering.
    
    Args:
        original_recommendations: DataFrame from original Step 7
        temperature_data: Store temperature data (optional)
        period_label: Current period (e.g., "202506A")
        category_column: Column name for product category
    
    Returns:
        Enhanced DataFrame with gate results and final recommendations
    """
    print(f"\n{'='*60}")
    print("APPLYING CLIMATE & TIME GATES TO STEP 7 RECOMMENDATIONS")
    print(f"{'='*60}")
    print(f"Period: {period_label}")
    print(f"Original recommendations: {len(original_recommendations):,}")
    
    # Initialize result columns
    enhanced_df = original_recommendations.copy()
    enhanced_df['climate_gate_passed'] = True
    enhanced_df['time_gate_passed'] = True
    enhanced_df['suppression_reason'] = None
    enhanced_df['store_temperature'] = np.nan
    enhanced_df['spu_temperature_band'] = 'All'
    enhanced_df['current_season'] = get_current_season(period_label).value
    
    # If no temperature data, skip climate gate (graceful degradation)
    if temperature_data is None:
        print("⚠️ No temperature data available - climate gate SKIPPED")
        print("   Falling back to original Step 7 logic (time gate only)")
    else:
        # Merge temperature data
        enhanced_df = enhanced_df.merge(
            temperature_data[['str_code', 'temperature']],
            on='str_code',
            how='left',
            suffixes=('', '_temp')
        )
        enhanced_df['store_temperature'] = enhanced_df['temperature']
        enhanced_df = enhanced_df.drop(columns=['temperature'], errors='ignore')
    
    # Apply gates row by row
    climate_suppressed = 0
    time_suppressed = 0
    
    for idx, row in enhanced_df.iterrows():
        spu_code = str(row.get('spu_code', ''))
        category = row.get(category_column, None)
        store_temp = row.get('store_temperature', np.nan)
        
        # Evaluate time gate (always applies)
        time_result = evaluate_time_gate(period_label, spu_code, category)
        enhanced_df.at[idx, 'time_gate_passed'] = time_result.passed
        enhanced_df.at[idx, 'spu_temperature_band'] = get_spu_temperature_band(spu_code, category).value
        
        if not time_result.passed:
            enhanced_df.at[idx, 'suppression_reason'] = time_result.reason
            time_suppressed += 1
            continue
        
        # Evaluate climate gate (only if temperature data available)
        if pd.notna(store_temp):
            climate_result = evaluate_climate_gate(store_temp, spu_code, category)
            enhanced_df.at[idx, 'climate_gate_passed'] = climate_result.passed
            
            if not climate_result.passed:
                enhanced_df.at[idx, 'suppression_reason'] = climate_result.reason
                climate_suppressed += 1
    
    # Calculate final recommendation
    enhanced_df['final_recommendation'] = 'ADD'
    enhanced_df.loc[~enhanced_df['time_gate_passed'], 'final_recommendation'] = 'SUPPRESS_TIME'
    enhanced_df.loc[~enhanced_df['climate_gate_passed'], 'final_recommendation'] = 'SUPPRESS_CLIMATE'
    
    # Summary statistics
    total = len(enhanced_df)
    approved = len(enhanced_df[enhanced_df['final_recommendation'] == 'ADD'])
    
    print(f"\n📊 GATE RESULTS:")
    print(f"   Total recommendations: {total:,}")
    print(f"   ✅ Approved (ADD): {approved:,} ({100*approved/total:.1f}%)")
    print(f"   ❌ Suppressed by TIME gate: {time_suppressed:,} ({100*time_suppressed/total:.1f}%)")
    print(f"   ❌ Suppressed by CLIMATE gate: {climate_suppressed:,} ({100*climate_suppressed/total:.1f}%)")
    print(f"{'='*60}\n")
    
    return enhanced_df


def run_enhanced_step7(
    original_results_file: str,
    temperature_file: str,
    period_label: str,
    output_file: str,
    category_column: str = 'sub_cate_name'
) -> pd.DataFrame:
    """
    Run the enhanced Step 7 with climate and time awareness.
    
    This is the main entry point for the enhanced module.
    
    Args:
        original_results_file: Path to original Step 7 results CSV
        temperature_file: Path to Step 5 temperature CSV
        period_label: Current period (e.g., "202506A")
        output_file: Path to save enhanced results
        category_column: Column name for product category
    
    Returns:
        Enhanced recommendations DataFrame
    """
    print("\n" + "="*70)
    print("STEP 7 ENHANCED: TIME-AWARE & CLIMATE-AWARE MISSING SPU RULE")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Period: {period_label}")
    print(f"Season: {get_current_season(period_label).value}")
    
    # Load original Step 7 results
    print(f"\n📂 Loading original Step 7 results: {original_results_file}")
    if not os.path.exists(original_results_file):
        raise FileNotFoundError(f"Original results not found: {original_results_file}")
    
    original_df = pd.read_csv(original_results_file, dtype={'str_code': str})
    print(f"   Loaded {len(original_df):,} recommendations")
    
    # Load temperature data
    print(f"\n🌡️ Loading temperature data: {temperature_file}")
    temp_df = load_temperature_data(temperature_file)
    
    # Apply gates
    enhanced_df = apply_climate_time_gates(
        original_df,
        temp_df,
        period_label,
        category_column
    )
    
    # Save results
    print(f"\n💾 Saving enhanced results: {output_file}")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    enhanced_df.to_csv(output_file, index=False)
    print(f"   Saved {len(enhanced_df):,} records")
    
    # Generate summary
    print("\n" + "="*70)
    print("ENHANCEMENT COMPLETE")
    print("="*70)
    
    return enhanced_df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 7 Enhanced: Time-Aware Missing SPU Rule")
    parser.add_argument("--original-results", default="output/rule7_missing_spu_results.csv")
    parser.add_argument("--temperature-file", default="output/sample_run_202506A/step5_feels_like_temperature.csv")
    parser.add_argument("--period", default="202506A")
    parser.add_argument("--output", default="output/rule7_missing_spu_time_aware_results.csv")
    args = parser.parse_args()
    run_enhanced_step7(args.original_results, args.temperature_file, args.period, args.output)
