"""
Step 12 Scaling Engine

AXIS B: Controlled Scaling Logic (No Re-eligibility)
AXIS C: Multi-factor Scaling (Within Bounds)
AXIS D: Hard Safety Caps

This module calculates the recommended adjustment quantity for Step 11 candidates.
It does NOT re-decide eligibility - only magnitude decisions.

Scaling Sequence:
1. Confirm SPU ∈ Step 11 candidates (already done by input filtering)
2. Confirm SPU was NOT forcibly increased in Step 9
3. Confirm SPU was NOT recently reduced in Step 10
4. Apply scaling only if gap exceeds documented threshold
5. Apply multi-factor modulation (traffic, affinity)
6. Apply hard safety caps

Author: Data Pipeline Team
Date: January 2026
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from step12_config import Step12Config, DEFAULT_CONFIG, ScalingTier


@dataclass
class ScalingResult:
    """Result of scaling calculation for a single SPU-store pair."""
    store_code: str
    spu_code: str
    
    # Input metrics
    performance_gap: float
    gap_ratio: float
    current_quantity: float
    cluster_median: float
    
    # Scaling factors
    base_scaling: float
    affinity_modifier: float
    traffic_modifier: float
    step9_dampener: float
    
    # Output
    raw_adjustment: float
    capped_adjustment: float
    final_adjustment: float
    
    # Caps applied
    cap_applied: str
    scaling_tier: ScalingTier
    
    # Traceability
    scaling_explanation: str


def check_step9_conflict(
    store_code: str,
    spu_code: str,
    step9_df: pd.DataFrame
) -> Tuple[bool, float]:
    """
    Check if Step 9 already applied a below-minimum boost.
    
    Returns:
        Tuple of (was_boosted, dampening_factor)
    """
    if step9_df.empty:
        return False, 1.0
    
    match = step9_df[
        (step9_df['str_code'] == store_code) &
        (step9_df['spu_code'] == spu_code)
    ]
    
    if match.empty:
        return False, 1.0
    
    # Check if Step 9 applied a boost
    if 'rule9_applied' in match.columns:
        was_boosted = match['rule9_applied'].iloc[0] == True
        if was_boosted:
            return True, 0.5  # Apply 50% dampening
    
    return False, 1.0


def check_step10_conflict(
    store_code: str,
    spu_code: str,
    step10_df: pd.DataFrame
) -> bool:
    """
    Check if Step 10 flagged this SPU for reduction.
    
    Returns:
        True if Step 10 reduced this SPU (BLOCK scaling)
    """
    if step10_df.empty:
        return False
    
    match = step10_df[
        (step10_df['str_code'] == store_code) &
        (step10_df['spu_code'] == spu_code)
    ]
    
    if match.empty:
        return False
    
    # Check if Step 10 applied a reduction
    if 'rule10_applied' in match.columns:
        return match['rule10_applied'].iloc[0] == True
    
    return False


def calculate_affinity_modifier(
    woman_cnt: float,
    male_cnt: float,
    spu_gender: str,
    config: Step12Config = DEFAULT_CONFIG
) -> float:
    """
    Calculate affinity modifier based on store traffic composition.
    
    AXIS C: Multi-factor Scaling - uses existing data only.
    
    Args:
        woman_cnt: woman_into_str_cnt_avg
        male_cnt: male_into_str_cnt_avg
        spu_gender: SPU target gender
        config: Step 12 configuration
    
    Returns:
        Modifier between (1 - max_dampener) and (1 + max_boost)
    """
    total = woman_cnt + male_cnt
    if total <= 0:
        return 1.0  # Neutral when no data
    
    female_ratio = woman_cnt / total
    
    # Calculate alignment
    if spu_gender in ['女', 'female', 'Female']:
        alignment = female_ratio
    elif spu_gender in ['男', 'male', 'Male']:
        alignment = 1 - female_ratio
    else:
        alignment = 0.5  # Neutral for unisex
    
    # Convert alignment to modifier
    # High alignment (>0.6) = boost, Low alignment (<0.4) = dampen
    if alignment >= 0.6:
        modifier = 1.0 + (alignment - 0.6) * config.affinity_boost_max / 0.4
    elif alignment <= 0.4:
        modifier = 1.0 - (0.4 - alignment) * config.traffic_dampener_max / 0.4
    else:
        modifier = 1.0
    
    return max(0.5, min(1.3, modifier))  # Bound between 0.5x and 1.3x


def calculate_scaling_adjustment(
    gap_df: pd.DataFrame,
    step9_df: pd.DataFrame,
    step10_df: pd.DataFrame,
    store_traffic_df: Optional[pd.DataFrame] = None,
    config: Step12Config = DEFAULT_CONFIG
) -> pd.DataFrame:
    """
    Calculate scaling adjustments for all candidates with performance gaps.
    
    AXIS B: Controlled Scaling Logic
    AXIS C: Multi-factor Scaling
    AXIS D: Hard Safety Caps
    
    Args:
        gap_df: Candidates with calculated performance gaps
        step9_df: Step 9 output for conflict checking
        step10_df: Step 10 output for conflict checking
        store_traffic_df: Store traffic data for affinity modulation
        config: Step 12 configuration
    
    Returns:
        DataFrame with scaling adjustments
    """
    print("\n⚙️ Calculating scaling adjustments (Axis B, C, D)...")
    print(f"   Input candidates with gaps: {len(gap_df):,}")
    
    if gap_df.empty:
        return pd.DataFrame()
    
    # Prepare traffic lookup
    traffic_lookup = {}
    if store_traffic_df is not None and not store_traffic_df.empty:
        for _, row in store_traffic_df.iterrows():
            traffic_lookup[row['str_code']] = {
                'woman_cnt': row.get('woman_into_str_cnt_avg', 0),
                'male_cnt': row.get('male_into_str_cnt_avg', 0),
            }
    
    results = []
    blocked_by_step9 = 0
    blocked_by_step10 = 0
    
    for _, row in gap_df.iterrows():
        store_code = row['str_code']
        spu_code = row['spu_code']
        
        # Check Step 10 conflict (BLOCK if reduced)
        if config.block_if_step10_reduced:
            if check_step10_conflict(store_code, spu_code, step10_df):
                blocked_by_step10 += 1
                continue
        
        # Check Step 9 conflict (DAMPEN if boosted)
        step9_boosted, step9_dampener = check_step9_conflict(
            store_code, spu_code, step9_df
        )
        if step9_boosted:
            blocked_by_step9 += 1
            # Don't block, but apply dampening
        
        # Get gap metrics
        performance_gap = row['performance_gap']
        gap_ratio = row['gap_ratio']
        current_qty = row.get('store_sales', row.get('current_spu_count', 0))
        cluster_median = row.get('cluster_median', current_qty)
        
        # Base scaling: percentage of gap to close
        base_scaling = performance_gap * config.base_scaling_factor
        
        # Apply affinity modifier (Axis C)
        traffic_data = traffic_lookup.get(store_code, {})
        spu_gender = row.get('sex_name', 'unisex')
        affinity_modifier = calculate_affinity_modifier(
            traffic_data.get('woman_cnt', 0),
            traffic_data.get('male_cnt', 0),
            spu_gender,
            config
        )
        
        # Apply Step 9 dampener
        raw_adjustment = base_scaling * affinity_modifier * step9_dampener
        
        # Apply Hard Safety Caps (Axis D)
        cap_applied = "none"
        capped_adjustment = raw_adjustment
        
        # Cap 1: Max % of current quantity
        max_by_current = current_qty * config.max_increase_pct_of_current
        if capped_adjustment > max_by_current and max_by_current > 0:
            capped_adjustment = max_by_current
            cap_applied = "max_pct_current"
        
        # Cap 2: Max % of cluster median
        max_by_median = cluster_median * config.max_increase_pct_of_cluster_median
        if capped_adjustment > max_by_median and max_by_median > 0:
            capped_adjustment = max_by_median
            cap_applied = "max_pct_median"
        
        # Cap 3: Absolute maximum
        if capped_adjustment > config.max_absolute_increase:
            capped_adjustment = config.max_absolute_increase
            cap_applied = "max_absolute"
        
        # Minimum threshold
        if capped_adjustment < config.min_increase_quantity:
            continue  # Skip if below minimum
        
        # Determine scaling tier
        if capped_adjustment <= 5:
            scaling_tier = ScalingTier.MINIMAL
        elif capped_adjustment <= 15:
            scaling_tier = ScalingTier.MODERATE
        else:
            scaling_tier = ScalingTier.AGGRESSIVE
        
        # Generate explanation
        explanation_parts = [
            f"Gap: {performance_gap:.1f} units ({gap_ratio:.1%} below P75)",
            f"Base scaling: {base_scaling:.1f}",
            f"Affinity modifier: {affinity_modifier:.2f}x",
        ]
        if step9_boosted:
            explanation_parts.append(f"Step 9 dampener: {step9_dampener:.2f}x")
        if cap_applied != "none":
            explanation_parts.append(f"Cap applied: {cap_applied}")
        
        scaling_explanation = " | ".join(explanation_parts)
        
        # Build result row
        result_row = row.to_dict()
        result_row.update({
            'base_scaling': base_scaling,
            'affinity_modifier': affinity_modifier,
            'step9_dampener': step9_dampener,
            'step9_boosted': step9_boosted,
            'raw_adjustment': raw_adjustment,
            'capped_adjustment': capped_adjustment,
            'recommended_adjustment_quantity': capped_adjustment,
            'cap_applied': cap_applied,
            'scaling_tier': scaling_tier.value,
            'scaling_explanation': scaling_explanation,
        })
        
        results.append(result_row)
    
    print(f"   Blocked by Step 10 reduction: {blocked_by_step10:,}")
    print(f"   Dampened by Step 9 boost: {blocked_by_step9:,}")
    print(f"   Final scaling recommendations: {len(results):,}")
    
    if not results:
        return pd.DataFrame()
    
    result_df = pd.DataFrame(results)
    
    # Summary by tier
    tier_counts = result_df['scaling_tier'].value_counts()
    print("\n   Scaling tier distribution:")
    for tier, count in tier_counts.items():
        print(f"      - {tier}: {count:,}")
    
    return result_df
