"""
Step 9 Minimum Evaluator: Below Minimum Detection Logic

This module contains the core logic for evaluating whether an SPU is below
minimum threshold and calculating conservative quantity increases.

Key Features:
- 3-level fallback for minimum threshold (manual → cluster P10 → global)
- Sell-through validation gate
- Conservative quantity increase (minimum of candidates)
- Never decrease, never negative

Per Customer Requirements:
- E-06: Never decrease below minimum, no negative quantities
- E-05: Stay within ±20% of manual/historical baseline
- I-03: Conservative allocation preferred over aggressive

Author: Data Pipeline Team
Date: January 2026
"""

import numpy as np
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from step9_config import (
    Step9Config,
    DEFAULT_CONFIG,
    MinimumReferenceSource,
    get_minimum_reference,
    is_core_subcategory,
)


class BelowMinimumStatus(Enum):
    """Status of below minimum evaluation."""
    BELOW_MINIMUM = "BELOW_MINIMUM"
    ABOVE_MINIMUM = "ABOVE_MINIMUM"
    SKIPPED_STEP8 = "SKIPPED_STEP8"
    SKIPPED_INELIGIBLE = "SKIPPED_INELIGIBLE"
    SKIPPED_NO_DEMAND = "SKIPPED_NO_DEMAND"


@dataclass
class BelowMinimumResult:
    """Result of below minimum evaluation for a single SPU × Store."""
    status: BelowMinimumStatus
    reason: str
    
    # Input values
    current_quantity: float
    minimum_threshold: float
    minimum_reference_source: str
    
    # Recommendation (only if BELOW_MINIMUM)
    recommended_increase: float
    recommended_quantity_change: int  # Ceiled integer
    
    # Validation flags
    sell_through_valid: bool
    eligibility_status: str
    adjusted_by_step8: bool
    is_core_subcategory: bool
    
    # Metadata for explainability
    rule9_applied: bool
    rule9_reason: str


def evaluate_sell_through(
    recent_sales_units: Optional[float],
    sell_through_rate: Optional[float],
    cluster_median_sellthrough: Optional[float],
    config: Step9Config = DEFAULT_CONFIG
) -> tuple:
    """
    Validate sell-through signal before recommending increase.
    
    Per requirement: Step 9 MUST NOT increase SPUs that show zero demand signal.
    
    Args:
        recent_sales_units: Recent sales in units
        sell_through_rate: Current sell-through rate
        cluster_median_sellthrough: Cluster median for comparison
    
    Returns:
        Tuple of (is_valid, reason)
    """
    # Check for any demand signal
    has_sales = recent_sales_units is not None and recent_sales_units > 0
    
    # Check sell-through rate against cluster median
    has_sellthrough = False
    if sell_through_rate is not None and cluster_median_sellthrough is not None:
        has_sellthrough = sell_through_rate >= (cluster_median_sellthrough * 0.5)
    elif sell_through_rate is not None:
        has_sellthrough = sell_through_rate > config.min_sell_through_rate
    
    if has_sales or has_sellthrough:
        return (True, "Demand signal detected")
    
    return (False, "No demand signal - zero sales and low sell-through")


def calculate_conservative_increase(
    current_quantity: float,
    minimum_threshold: float,
    historical_baseline: Optional[float] = None,
    case_pack_size: Optional[int] = None,
    remaining_capacity: Optional[float] = None,
    config: Step9Config = DEFAULT_CONFIG
) -> int:
    """
    Calculate conservative quantity increase using minimum of candidates.
    
    Per requirement: Generate multiple conservative candidates, choose minimum.
    
    Candidate sources:
    1. Gap to minimum threshold
    2. Historical smallest successful increase (if available)
    3. Case pack / logistics unit (if available)
    4. % of remaining store capacity (if available)
    5. Max 20% of historical baseline (per E-05)
    
    Args:
        current_quantity: Current allocation
        minimum_threshold: Target minimum
        historical_baseline: Historical allocation for ±20% cap
        case_pack_size: Logistics unit size
        remaining_capacity: Store remaining capacity
        config: Step 9 configuration
    
    Returns:
        Conservative increase amount (ceiled integer, always positive)
    """
    candidates: List[float] = []
    
    # Candidate 1: Gap to minimum threshold
    gap = minimum_threshold - current_quantity
    if gap > 0:
        candidates.append(gap)
    
    # Candidate 2: Minimum boost quantity (floor)
    candidates.append(config.min_boost_quantity)
    
    # Candidate 3: Case pack size (if available)
    if case_pack_size is not None and case_pack_size > 0:
        candidates.append(float(case_pack_size))
    
    # Candidate 4: % of remaining capacity (if available)
    if remaining_capacity is not None and remaining_capacity > 0:
        capacity_based = remaining_capacity * 0.1  # 10% of remaining
        if capacity_based > 0:
            candidates.append(capacity_based)
    
    # Candidate 5: Max 20% of historical baseline (per E-05)
    if historical_baseline is not None and historical_baseline > 0:
        max_increase = historical_baseline * config.max_increase_percentage
        candidates.append(max_increase)
    
    # Choose minimum positive value
    positive_candidates = [c for c in candidates if c > 0]
    
    if not positive_candidates:
        # Fallback to minimum boost
        return int(np.ceil(config.min_boost_quantity))
    
    recommended = min(positive_candidates)
    
    # Ceil to integer for operational feasibility
    return max(1, int(np.ceil(recommended)))


def evaluate_below_minimum(
    str_code: str,
    spu_code: str,
    current_quantity: float,
    category_name: Optional[str],
    eligibility_status: str,
    adjusted_by_step8: bool,
    manual_plan_minimum: Optional[float] = None,
    cluster_p10_rate: Optional[float] = None,
    recent_sales_units: Optional[float] = None,
    sell_through_rate: Optional[float] = None,
    cluster_median_sellthrough: Optional[float] = None,
    historical_baseline: Optional[float] = None,
    config: Step9Config = DEFAULT_CONFIG
) -> BelowMinimumResult:
    """
    Evaluate if an SPU × Store is below minimum and calculate recommendation.
    
    Decision Tree (per requirement):
    1. Check eligibility (INELIGIBLE → STOP)
    2. Check Step 8 adjustment (adjusted → SKIP)
    3. Check sell-through signal (no signal → SKIP)
    4. Check below minimum threshold
    5. Calculate conservative increase
    
    Args:
        str_code: Store code
        spu_code: SPU code
        current_quantity: Current allocation
        category_name: Product category (for core subcategory check)
        eligibility_status: From Step 7 (ELIGIBLE/INELIGIBLE/UNKNOWN)
        adjusted_by_step8: Whether Step 8 already adjusted this SPU
        manual_plan_minimum: Customer-provided minimum (if any)
        cluster_p10_rate: Cluster 10th percentile rate
        recent_sales_units: Recent sales for sell-through validation
        sell_through_rate: Current sell-through rate
        cluster_median_sellthrough: Cluster median for comparison
        historical_baseline: Historical allocation for ±20% cap
        config: Step 9 configuration
    
    Returns:
        BelowMinimumResult with status, recommendation, and metadata
    """
    # Check if core subcategory (always evaluate per I-05)
    is_core = is_core_subcategory(category_name)
    
    # Get minimum threshold using 3-level fallback
    minimum_threshold, min_source = get_minimum_reference(
        manual_plan_minimum, cluster_p10_rate, config
    )
    
    # Base result template
    base_result = {
        'current_quantity': current_quantity,
        'minimum_threshold': minimum_threshold,
        'minimum_reference_source': min_source.value,
        'recommended_increase': 0.0,
        'recommended_quantity_change': 0,
        'sell_through_valid': False,
        'eligibility_status': eligibility_status,
        'adjusted_by_step8': adjusted_by_step8,
        'is_core_subcategory': is_core,
        'rule9_applied': False,
        'rule9_reason': '',
    }
    
    # Decision Tree Step 1: Check eligibility
    # Per requirement: Only evaluate ELIGIBLE or UNKNOWN
    # Exception: Core subcategories are ALWAYS evaluated
    if eligibility_status == 'INELIGIBLE' and not is_core:
        return BelowMinimumResult(
            status=BelowMinimumStatus.SKIPPED_INELIGIBLE,
            reason=f"Ineligible SPU (status={eligibility_status})",
            **base_result
        )
    
    # Decision Tree Step 2: Check Step 8 adjustment
    # Per requirement: If adjusted_by_step8 == True → SKIP Step 9
    if adjusted_by_step8:
        return BelowMinimumResult(
            status=BelowMinimumStatus.SKIPPED_STEP8,
            reason="Already adjusted by Step 8 - no double counting",
            **base_result
        )
    
    # Decision Tree Step 3: Check sell-through signal
    # Per requirement: Must have demand signal to increase
    sell_through_valid, st_reason = evaluate_sell_through(
        recent_sales_units, sell_through_rate, cluster_median_sellthrough, config
    )
    base_result['sell_through_valid'] = sell_through_valid
    
    if not sell_through_valid and config.require_sell_through_signal:
        # Exception: Core subcategories may still be evaluated
        if not is_core:
            return BelowMinimumResult(
                status=BelowMinimumStatus.SKIPPED_NO_DEMAND,
                reason=f"No demand signal: {st_reason}",
                **base_result
            )
    
    # Decision Tree Step 4: Check below minimum threshold
    if current_quantity >= minimum_threshold:
        return BelowMinimumResult(
            status=BelowMinimumStatus.ABOVE_MINIMUM,
            reason=f"Current ({current_quantity:.2f}) >= minimum ({minimum_threshold:.2f})",
            **base_result
        )
    
    # Decision Tree Step 5: Calculate conservative increase
    recommended_change = calculate_conservative_increase(
        current_quantity=current_quantity,
        minimum_threshold=minimum_threshold,
        historical_baseline=historical_baseline,
        config=config
    )
    
    # CRITICAL: Ensure no negative values (per E-06)
    if recommended_change < 0:
        recommended_change = max(1, int(np.ceil(config.min_boost_quantity)))
    
    base_result['recommended_increase'] = float(recommended_change)
    base_result['recommended_quantity_change'] = recommended_change
    base_result['rule9_applied'] = True
    base_result['rule9_reason'] = (
        f"Below minimum: current={current_quantity:.2f}, "
        f"threshold={minimum_threshold:.2f} ({min_source.value}), "
        f"increase=+{recommended_change}"
    )
    
    return BelowMinimumResult(
        status=BelowMinimumStatus.BELOW_MINIMUM,
        reason=f"Below minimum threshold ({min_source.value})",
        **base_result
    )


def validate_no_negatives(results: List[BelowMinimumResult]) -> Dict[str, Any]:
    """
    Validate that no negative quantities exist in results.
    
    Per E-06: No negative configuration values.
    
    Returns:
        Validation summary
    """
    negative_count = sum(
        1 for r in results 
        if r.recommended_quantity_change < 0
    )
    
    return {
        'total_results': len(results),
        'negative_count': negative_count,
        'all_positive': negative_count == 0,
        'requirement_E06_met': negative_count == 0,
    }
