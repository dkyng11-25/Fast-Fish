"""
Step 11 Opportunity Tiering: Clear Confidence Buckets

AXIS E: Opportunity Tiering Implementation
AXIS D: Weather/Seasonal Context (Rationale-Only)

This module implements:
- Opportunity tiering into High/Medium/Exploratory confidence buckets (Axis E)
- Weather/seasonal context for rationale (Axis D - explanatory only)

Per Customer Requirement:
- Each opportunity must be classified into a tier
- Tiering uses: peer adoption, affinity score, consistency check, sell-through
- Weather/seasonal signals are EXPLANATORY CONTEXT ONLY
- Weather MUST NOT trigger recommendations or change quantities

Author: Data Pipeline Team
Date: January 2026
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

from step11_config import (
    Step11Config,
    DEFAULT_CONFIG,
    OpportunityTier,
    AffinityLevel,
    get_opportunity_tier,
)


@dataclass
class TieringResult:
    """Result of opportunity tiering."""
    tier: OpportunityTier
    tier_score: float
    tier_justification: str
    seasonal_context: str


def calculate_tier_score(
    opportunity_score: float,
    adoption_rate: float,
    affinity_score: float,
    consistency_penalty: float,
    sell_through_rate: Optional[float] = None,
    config: Step11Config = DEFAULT_CONFIG
) -> float:
    """
    Calculate composite tier score for opportunity classification.
    
    Tiering Inputs (Allowed):
    - Peer adoption strength
    - Store Affinity Score (Axis B)
    - Consistency Check (Axis C)
    - Sell-through validation (if available)
    
    Args:
        opportunity_score: Base opportunity score
        adoption_rate: SPU adoption rate in cluster
        affinity_score: Store affinity score (0-1)
        consistency_penalty: Consistency penalty (0-1)
        sell_through_rate: Optional sell-through rate
        config: Step 11 configuration
    
    Returns:
        Composite tier score (0-1)
    """
    # Base score from opportunity and adoption
    base_score = (opportunity_score * 0.4) + (adoption_rate * 0.3)
    
    # Affinity contribution
    affinity_contribution = affinity_score * 0.2
    
    # Sell-through contribution (if available)
    if sell_through_rate is not None and sell_through_rate > 0:
        sellthrough_contribution = min(1.0, sell_through_rate) * 0.1
    else:
        sellthrough_contribution = 0.05  # Neutral when unavailable
    
    # Apply consistency penalty
    raw_score = base_score + affinity_contribution + sellthrough_contribution
    final_score = raw_score * (1 - consistency_penalty)
    
    return min(1.0, max(0.0, final_score))


def classify_opportunity_tier(
    tier_score: float,
    affinity_level: AffinityLevel,
    consistency_penalty: float,
    config: Step11Config = DEFAULT_CONFIG
) -> OpportunityTier:
    """
    Classify opportunity into confidence tier.
    
    AXIS E: Opportunity Tiering (Clear Confidence Buckets)
    
    Required Tiers:
    - High Confidence Growth
    - Medium Confidence Growth
    - Exploratory / Test Opportunity
    
    Args:
        tier_score: Composite tier score
        affinity_level: Store affinity level
        consistency_penalty: Consistency penalty
        config: Step 11 configuration
    
    Returns:
        OpportunityTier enum value
    """
    return get_opportunity_tier(
        tier_score, affinity_level, consistency_penalty, config
    )


def generate_tier_justification(
    tier: OpportunityTier,
    tier_score: float,
    adoption_rate: float,
    affinity_level: AffinityLevel,
    consistency_penalty: float
) -> str:
    """
    Generate short justification for tier classification.
    
    Args:
        tier: Assigned opportunity tier
        tier_score: Composite tier score
        adoption_rate: SPU adoption rate
        affinity_level: Store affinity level
        consistency_penalty: Consistency penalty
    
    Returns:
        Human-readable justification string
    """
    justification_parts = []
    
    # Adoption strength
    if adoption_rate >= 0.8:
        justification_parts.append("strong peer adoption (80%+)")
    elif adoption_rate >= 0.6:
        justification_parts.append("moderate peer adoption")
    else:
        justification_parts.append("limited peer adoption")
    
    # Affinity
    justification_parts.append(f"{affinity_level.value.lower()}")
    
    # Consistency
    if consistency_penalty > 0.3:
        justification_parts.append("significant customer mix mismatch")
    elif consistency_penalty > 0:
        justification_parts.append("minor customer mix difference")
    
    return f"{tier.value}: {', '.join(justification_parts)} (score: {tier_score:.2f})"


def generate_seasonal_context(
    period_label: str,
    category_name: Optional[str] = None
) -> str:
    """
    Generate seasonal context for rationale.
    
    AXIS D: Weather/Seasonal Context (Rationale-Only)
    
    CRITICAL: This is EXPLANATORY CONTEXT ONLY.
    Weather and seasonal signals MUST NOT:
    - Trigger recommendations
    - Change quantities
    
    Args:
        period_label: Current period (e.g., "202506A")
        category_name: Optional product category
    
    Returns:
        Seasonal context string for explanation
    """
    # Parse period
    try:
        year = int(period_label[:4])
        month = int(period_label[4:6])
    except (ValueError, IndexError):
        return "Seasonal context: Period not parseable"
    
    # Determine season
    if month in [12, 1, 2]:
        season = "winter"
        season_desc = "Winter season - cold weather products typically in demand"
    elif month in [3, 4, 5]:
        season = "spring"
        season_desc = "Spring transition - lighter clothing gaining momentum"
    elif month in [6, 7, 8]:
        season = "summer"
        season_desc = "Summer season - warm weather products at peak demand"
    else:
        season = "fall"
        season_desc = "Fall transition - preparing for cooler weather"
    
    # Add category context if available
    if category_name:
        return f"Seasonal context ({season}): {season_desc}. Category: {category_name}"
    
    return f"Seasonal context ({season}): {season_desc}"


def apply_opportunity_tiering(
    opportunities_df: pd.DataFrame,
    period_label: str = "202506A",
    config: Step11Config = DEFAULT_CONFIG
) -> pd.DataFrame:
    """
    Apply opportunity tiering to all opportunities.
    
    AXIS E: Adds tier classification and justification.
    AXIS D: Adds seasonal context (rationale only).
    
    Args:
        opportunities_df: Opportunities with affinity scores
        period_label: Current period for seasonal context
        config: Step 11 configuration
    
    Returns:
        DataFrame with tiering columns added
    """
    print("\n📊 Applying Opportunity Tiering (Axis E)...")
    print("   Weather and seasonal signals are explanatory context only.")
    
    if opportunities_df.empty:
        return opportunities_df
    
    # Calculate tier scores and classifications
    tier_results = []
    for _, row in opportunities_df.iterrows():
        # Get required values with defaults
        opportunity_score = row.get('opportunity_score', 0.5)
        adoption_rate = row.get('spu_adoption_rate_in_cluster', 0.5)
        affinity_score = row.get('affinity_score', 0.5)
        consistency_penalty = row.get('consistency_penalty', 0.0)
        sell_through = row.get('sell_through_rate', None)
        
        # Calculate tier score
        tier_score = calculate_tier_score(
            opportunity_score, adoption_rate, affinity_score,
            consistency_penalty, sell_through, config
        )
        
        # Get affinity level
        affinity_level_str = row.get('affinity_level', AffinityLevel.MODERATE.value)
        try:
            affinity_level = AffinityLevel(affinity_level_str)
        except ValueError:
            affinity_level = AffinityLevel.MODERATE
        
        # Classify tier
        tier = classify_opportunity_tier(
            tier_score, affinity_level, consistency_penalty, config
        )
        
        # Generate justification
        justification = generate_tier_justification(
            tier, tier_score, adoption_rate, affinity_level, consistency_penalty
        )
        
        # Generate seasonal context (Axis D - rationale only)
        category = row.get('category_key', row.get('sub_cate_name', ''))
        seasonal_context = generate_seasonal_context(period_label, category)
        
        tier_results.append({
            'opportunity_tier': tier.value,
            'tier_score': tier_score,
            'tier_justification': justification,
            'seasonal_context': seasonal_context,
        })
    
    # Add results to dataframe
    tier_df = pd.DataFrame(tier_results)
    for col in tier_df.columns:
        opportunities_df[col] = tier_df[col].values
    
    # Summary
    high_count = (opportunities_df['opportunity_tier'] == OpportunityTier.HIGH_CONFIDENCE.value).sum()
    medium_count = (opportunities_df['opportunity_tier'] == OpportunityTier.MEDIUM_CONFIDENCE.value).sum()
    exploratory_count = (opportunities_df['opportunity_tier'] == OpportunityTier.EXPLORATORY.value).sum()
    
    print(f"   Tier distribution:")
    print(f"      - {OpportunityTier.HIGH_CONFIDENCE.value}: {high_count:,}")
    print(f"      - {OpportunityTier.MEDIUM_CONFIDENCE.value}: {medium_count:,}")
    print(f"      - {OpportunityTier.EXPLORATORY.value}: {exploratory_count:,}")
    
    return opportunities_df
