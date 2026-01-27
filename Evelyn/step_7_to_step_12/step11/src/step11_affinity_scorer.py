"""
Step 11 Store Affinity Scorer: Soft Modifier for Prioritization

AXIS B: Store Affinity Score Implementation
AXIS C: Customer Mix Consistency Check Implementation

This module implements:
- Store Affinity Score based on customer mix alignment (Axis B)
- Customer Mix Consistency Check for confidence penalty (Axis C)

Per Customer Requirement:
- Affinity Score MUST NOT create or remove opportunities
- Affinity Score MUST NOT change quantities
- Affinity Score CAN affect: Ranking, Confidence labeling, Explanation text
- Consistency Check is a RISK signal, not a preference signal

Author: Data Pipeline Team
Date: January 2026
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from step11_config import (
    Step11Config,
    DEFAULT_CONFIG,
    AffinityLevel,
    calculate_affinity_level,
    calculate_consistency_penalty,
)


@dataclass
class AffinityResult:
    """Result of affinity scoring for a store-SPU pair."""
    affinity_level: AffinityLevel
    affinity_score: float
    consistency_penalty: float
    adjusted_confidence: float
    affinity_explanation: str
    consistency_explanation: str


def calculate_store_affinity(
    store_data: Dict,
    spu_data: Dict,
    top_performer_data: Optional[Dict] = None,
    config: Step11Config = DEFAULT_CONFIG
) -> AffinityResult:
    """
    Calculate store affinity and consistency penalty for a store-SPU pair.
    
    AXIS B: Store Affinity Score (Soft Modifier)
    AXIS C: Customer Mix Consistency Check (Confidence Penalty)
    
    Args:
        store_data: Store information including customer mix
        spu_data: SPU information including gender target
        top_performer_data: Top performer store data for consistency check
        config: Step 11 configuration
    
    Returns:
        AffinityResult with affinity level, score, penalty, and explanations
    """
    # Extract customer mix data
    woman_cnt = store_data.get('woman_into_str_cnt_avg', 0) or 0
    male_cnt = store_data.get('male_into_str_cnt_avg', 0) or 0
    total_cnt = woman_cnt + male_cnt
    
    # Extract SPU gender target
    sex_name = spu_data.get('sex_name', '')
    if sex_name in ['女', 'female', 'Female', 'F']:
        spu_gender_target = '女'
    elif sex_name in ['男', 'male', 'Male', 'M']:
        spu_gender_target = '男'
    else:
        spu_gender_target = 'unisex'
    
    # Calculate affinity level (Axis B)
    affinity_level = calculate_affinity_level(
        woman_cnt, male_cnt, spu_gender_target, config
    )
    
    # Calculate affinity score (0-1)
    if total_cnt > 0:
        if spu_gender_target == '女':
            affinity_score = woman_cnt / total_cnt
        elif spu_gender_target == '男':
            affinity_score = male_cnt / total_cnt
        else:
            affinity_score = 0.5  # Neutral for unisex
    else:
        affinity_score = 0.5  # Default when no data
    
    # Generate affinity explanation
    affinity_explanation = _generate_affinity_explanation(
        affinity_level, affinity_score, spu_gender_target, woman_cnt, male_cnt
    )
    
    # Calculate consistency penalty (Axis C)
    consistency_penalty = 0.0
    consistency_explanation = "No consistency check data available"
    
    if top_performer_data:
        top_woman_cnt = top_performer_data.get('woman_into_str_cnt_avg', 0) or 0
        top_male_cnt = top_performer_data.get('male_into_str_cnt_avg', 0) or 0
        top_total = top_woman_cnt + top_male_cnt
        
        if top_total > 0 and total_cnt > 0:
            top_female_ratio = top_woman_cnt / top_total
            store_female_ratio = woman_cnt / total_cnt
            
            consistency_penalty = calculate_consistency_penalty(
                top_female_ratio, store_female_ratio, config
            )
            
            consistency_explanation = _generate_consistency_explanation(
                consistency_penalty, top_female_ratio, store_female_ratio
            )
    
    # Calculate adjusted confidence
    adjusted_confidence = affinity_score * (1 - consistency_penalty)
    
    return AffinityResult(
        affinity_level=affinity_level,
        affinity_score=affinity_score,
        consistency_penalty=consistency_penalty,
        adjusted_confidence=adjusted_confidence,
        affinity_explanation=affinity_explanation,
        consistency_explanation=consistency_explanation
    )


def _generate_affinity_explanation(
    affinity_level: AffinityLevel,
    affinity_score: float,
    spu_gender_target: str,
    woman_cnt: float,
    male_cnt: float
) -> str:
    """Generate human-readable affinity explanation."""
    total = woman_cnt + male_cnt
    if total <= 0:
        return f"{affinity_level.value}: No customer mix data available"
    
    female_pct = (woman_cnt / total) * 100
    male_pct = (male_cnt / total) * 100
    
    if spu_gender_target == '女':
        return (
            f"{affinity_level.value}: Store has {female_pct:.0f}% female customers, "
            f"aligning with female-targeted product (score: {affinity_score:.2f})"
        )
    elif spu_gender_target == '男':
        return (
            f"{affinity_level.value}: Store has {male_pct:.0f}% male customers, "
            f"aligning with male-targeted product (score: {affinity_score:.2f})"
        )
    else:
        return (
            f"{affinity_level.value}: Unisex product with balanced customer mix "
            f"({female_pct:.0f}% female, {male_pct:.0f}% male)"
        )


def _generate_consistency_explanation(
    penalty: float,
    top_female_ratio: float,
    store_female_ratio: float
) -> str:
    """Generate human-readable consistency explanation."""
    mismatch = abs(top_female_ratio - store_female_ratio) * 100
    
    if penalty == 0:
        return (
            f"Customer mix consistent with top performers "
            f"(mismatch: {mismatch:.0f}%, no penalty)"
        )
    else:
        return (
            f"Customer mix differs from top performers "
            f"(mismatch: {mismatch:.0f}%, confidence penalty: {penalty:.0%})"
        )


def apply_affinity_scoring(
    opportunities_df: pd.DataFrame,
    store_sales_df: pd.DataFrame,
    config: Step11Config = DEFAULT_CONFIG
) -> pd.DataFrame:
    """
    Apply affinity scoring to all opportunities.
    
    AXIS B & C: Adds affinity level, score, and consistency penalty.
    
    Args:
        opportunities_df: Opportunities that passed baseline gate
        store_sales_df: Store sales data with customer mix columns
        config: Step 11 configuration
    
    Returns:
        DataFrame with affinity columns added
    """
    print("\n🎯 Applying Store Affinity Scoring (Axis B & C)...")
    
    if opportunities_df.empty:
        return opportunities_df
    
    # Merge store customer mix data
    customer_mix_cols = ['str_code', 'woman_into_str_cnt_avg', 'male_into_str_cnt_avg']
    available_cols = [c for c in customer_mix_cols if c in store_sales_df.columns]
    
    if len(available_cols) < 3:
        print("   ⚠️ Customer mix columns not available, using default affinity")
        opportunities_df['affinity_level'] = AffinityLevel.MODERATE.value
        opportunities_df['affinity_score'] = 0.5
        opportunities_df['consistency_penalty'] = 0.0
        opportunities_df['affinity_explanation'] = "Customer mix data not available"
        opportunities_df['consistency_explanation'] = "No consistency check performed"
        return opportunities_df
    
    # Merge customer mix data
    store_mix = store_sales_df[available_cols].drop_duplicates()
    opportunities_df = opportunities_df.merge(store_mix, on='str_code', how='left')
    
    # Fill missing values
    opportunities_df['woman_into_str_cnt_avg'] = opportunities_df['woman_into_str_cnt_avg'].fillna(0)
    opportunities_df['male_into_str_cnt_avg'] = opportunities_df['male_into_str_cnt_avg'].fillna(0)
    
    # Calculate affinity for each row
    affinity_results = []
    for _, row in opportunities_df.iterrows():
        store_data = {
            'woman_into_str_cnt_avg': row.get('woman_into_str_cnt_avg', 0),
            'male_into_str_cnt_avg': row.get('male_into_str_cnt_avg', 0),
        }
        spu_data = {
            'sex_name': row.get('sex_name', ''),
        }
        
        result = calculate_store_affinity(store_data, spu_data, None, config)
        affinity_results.append({
            'affinity_level': result.affinity_level.value,
            'affinity_score': result.affinity_score,
            'consistency_penalty': result.consistency_penalty,
            'adjusted_confidence': result.adjusted_confidence,
            'affinity_explanation': result.affinity_explanation,
            'consistency_explanation': result.consistency_explanation,
        })
    
    # Add results to dataframe
    affinity_df = pd.DataFrame(affinity_results)
    for col in affinity_df.columns:
        opportunities_df[col] = affinity_df[col].values
    
    # Summary
    high_affinity = (opportunities_df['affinity_level'] == AffinityLevel.HIGH.value).sum()
    moderate_affinity = (opportunities_df['affinity_level'] == AffinityLevel.MODERATE.value).sum()
    low_affinity = (opportunities_df['affinity_level'] == AffinityLevel.LOW.value).sum()
    
    print(f"   Affinity distribution:")
    print(f"      - High affinity: {high_affinity:,}")
    print(f"      - Moderate affinity: {moderate_affinity:,}")
    print(f"      - Low affinity: {low_affinity:,}")
    
    return opportunities_df
