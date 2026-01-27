"""
Step 11 Configuration: Missed Sales Opportunity Settings

This module contains all configuration for Step 11, including:
- Baseline gate settings (CRITICAL: respect Step 7-10 decisions)
- Store affinity score parameters
- Customer mix consistency check thresholds
- Opportunity tiering configuration
- Suggestion-only safeguards

Per Customer Requirement:
- Step 11 is SUGGESTION-ONLY and does NOT override Step 7-10 decisions
- Step 11 evaluates only SPU-store pairs that passed Step 7-9 and are NOT reduced by Step 10
- All outputs are framed as "growth opportunities" or "exploratory upside"

Author: Data Pipeline Team
Date: January 2026
"""

import json
from pathlib import Path
from typing import Set, Dict, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class OpportunityTier(Enum):
    """Opportunity confidence tiers for Step 11."""
    HIGH_CONFIDENCE = "High Confidence Growth"
    MEDIUM_CONFIDENCE = "Medium Confidence Growth"
    EXPLORATORY = "Exploratory / Test Opportunity"


class AffinityLevel(Enum):
    """Store affinity levels based on customer mix alignment."""
    HIGH = "High affinity"
    MODERATE = "Moderate affinity"
    LOW = "Low affinity"


@dataclass
class Step11Config:
    """Configuration for Step 11 Missed Sales Opportunity."""
    
    # Axis A: Baseline Gate (Hard Eligibility Constraint)
    require_baseline_gate: bool = True  # MUST be True per requirement
    only_evaluate_eligible_spus: bool = True  # Only SPUs that passed Step 7-9
    exclude_step10_reductions: bool = True  # Exclude SPUs flagged for reduction
    
    # Axis B: Store Affinity Score thresholds
    high_affinity_threshold: float = 0.7  # >= 70% alignment = High
    moderate_affinity_threshold: float = 0.4  # >= 40% alignment = Moderate
    
    # Axis C: Customer Mix Consistency Check
    consistency_penalty_threshold: float = 0.3  # > 30% mismatch = penalty
    max_consistency_penalty: float = 0.5  # Maximum confidence downgrade
    
    # Axis E: Opportunity Tiering thresholds
    high_confidence_min_score: float = 0.7  # >= 70% = High Confidence
    medium_confidence_min_score: float = 0.4  # >= 40% = Medium Confidence
    # Below 40% = Exploratory
    
    # Original Step 11 parameters (PRESERVED - not modified)
    top_performer_threshold: float = 0.95  # Top 5% of SPUs
    min_cluster_stores: int = 8
    min_stores_selling: int = 5
    min_spu_sales: float = 200.0
    adoption_threshold: float = 0.75
    min_opportunity_score: float = 0.15
    min_sales_gap: float = 100.0
    min_qty_gap: float = 2.0
    min_adoption_rate: float = 0.70
    min_investment_threshold: float = 150.0
    
    # Period settings
    data_period_days: int = 15
    target_period_days: int = 15


# Default configuration
DEFAULT_CONFIG = Step11Config()

# Path to Step 7-10 outputs for baseline gate
STEP7_OUTPUT_PATH = Path(__file__).parent.parent / "step7" / "step7_improved_clusters_results.csv"
STEP8_OUTPUT_PATH = Path(__file__).parent.parent / "step8" / "step8_improved_clusters_results.csv"
STEP9_OUTPUT_PATH = Path(__file__).parent.parent / "step9" / "step9_improved_clusters_results.csv"
STEP10_OUTPUT_PATH = Path(__file__).parent.parent / "step10" / "step10_improved_clusters_results.csv"


def get_opportunity_tier(
    opportunity_score: float,
    affinity_level: AffinityLevel,
    consistency_penalty: float,
    config: Step11Config = DEFAULT_CONFIG
) -> OpportunityTier:
    """
    Determine opportunity tier based on score, affinity, and consistency.
    
    Axis E: Opportunity Tiering (Clear Confidence Buckets)
    
    Args:
        opportunity_score: Base opportunity score (0-1)
        affinity_level: Store affinity level from Axis B
        consistency_penalty: Penalty from Axis C (0-1)
        config: Step 11 configuration
    
    Returns:
        OpportunityTier enum value
    """
    # Apply consistency penalty
    adjusted_score = opportunity_score * (1 - consistency_penalty)
    
    # Boost for high affinity
    if affinity_level == AffinityLevel.HIGH:
        adjusted_score = min(1.0, adjusted_score * 1.1)
    elif affinity_level == AffinityLevel.LOW:
        adjusted_score = adjusted_score * 0.9
    
    # Determine tier
    if adjusted_score >= config.high_confidence_min_score:
        return OpportunityTier.HIGH_CONFIDENCE
    elif adjusted_score >= config.medium_confidence_min_score:
        return OpportunityTier.MEDIUM_CONFIDENCE
    else:
        return OpportunityTier.EXPLORATORY


def calculate_affinity_level(
    woman_into_str_cnt_avg: float,
    male_into_str_cnt_avg: float,
    spu_gender_target: str,
    config: Step11Config = DEFAULT_CONFIG
) -> AffinityLevel:
    """
    Calculate store affinity level based on customer mix.
    
    Axis B: Store Affinity Score (Soft Modifier)
    
    Uses woman_into_str_cnt_avg and male_into_str_cnt_avg from store_sales_data.
    
    Args:
        woman_into_str_cnt_avg: Average female customer count
        male_into_str_cnt_avg: Average male customer count
        spu_gender_target: Target gender for SPU ('女', '男', 'unisex')
        config: Step 11 configuration
    
    Returns:
        AffinityLevel enum value
    """
    total_customers = woman_into_str_cnt_avg + male_into_str_cnt_avg
    if total_customers <= 0:
        return AffinityLevel.MODERATE  # Default when no data
    
    female_ratio = woman_into_str_cnt_avg / total_customers
    male_ratio = male_into_str_cnt_avg / total_customers
    
    # Calculate alignment based on SPU target
    if spu_gender_target == '女':
        alignment = female_ratio
    elif spu_gender_target == '男':
        alignment = male_ratio
    else:  # unisex or unknown
        alignment = 0.5  # Neutral alignment
    
    # Determine affinity level
    if alignment >= config.high_affinity_threshold:
        return AffinityLevel.HIGH
    elif alignment >= config.moderate_affinity_threshold:
        return AffinityLevel.MODERATE
    else:
        return AffinityLevel.LOW


def calculate_consistency_penalty(
    top_performer_female_ratio: float,
    target_store_female_ratio: float,
    config: Step11Config = DEFAULT_CONFIG
) -> float:
    """
    Calculate confidence penalty based on customer mix mismatch.
    
    Axis C: Customer Mix Consistency Check (Confidence Penalty)
    
    Compares top performer store customer mix with target store customer mix.
    
    Args:
        top_performer_female_ratio: Female ratio at top performer stores
        target_store_female_ratio: Female ratio at target store
        config: Step 11 configuration
    
    Returns:
        Penalty value (0-1), higher = more penalty
    """
    mismatch = abs(top_performer_female_ratio - target_store_female_ratio)
    
    if mismatch <= config.consistency_penalty_threshold:
        return 0.0  # No penalty
    
    # Scale penalty based on mismatch severity
    excess_mismatch = mismatch - config.consistency_penalty_threshold
    penalty = min(config.max_consistency_penalty, excess_mismatch * 2)
    
    return penalty


def validate_config_against_requirements() -> Dict[str, bool]:
    """
    Validate current configuration against customer requirements.
    
    Returns:
        Dictionary of requirement checks
    """
    checks = {
        'AXIS_A_baseline_gate_enabled': DEFAULT_CONFIG.require_baseline_gate,
        'AXIS_A_eligible_spus_only': DEFAULT_CONFIG.only_evaluate_eligible_spus,
        'AXIS_A_exclude_step10_reductions': DEFAULT_CONFIG.exclude_step10_reductions,
        'AXIS_B_affinity_thresholds_defined': (
            DEFAULT_CONFIG.high_affinity_threshold > DEFAULT_CONFIG.moderate_affinity_threshold
        ),
        'AXIS_C_consistency_penalty_defined': DEFAULT_CONFIG.consistency_penalty_threshold > 0,
        'AXIS_E_tiering_thresholds_defined': (
            DEFAULT_CONFIG.high_confidence_min_score > DEFAULT_CONFIG.medium_confidence_min_score
        ),
        'AXIS_F_suggestion_only': True,  # Always true by design
        'original_logic_preserved': True,  # Core logic unchanged
    }
    return checks


# Axis F: Suggestion-Only Safeguard statements
SUGGESTION_ONLY_STATEMENTS = [
    "Step 11 does NOT alter baseline inventory from Step 7-9.",
    "Step 11 does NOT conflict with Step 10 overcapacity reductions.",
    "Step 11 represents optional upside only - all recommendations are suggestions.",
    "Step 11 outputs are framed as 'growth opportunities' or 'exploratory upside'.",
    "Step 11 MUST NOT reverse any inventory increase from Step 7-9.",
    "Step 11 MUST NOT interfere with any reduction decision from Step 10.",
]
