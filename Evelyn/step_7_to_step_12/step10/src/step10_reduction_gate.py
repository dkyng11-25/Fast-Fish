"""
Step 10 Reduction Gate: Prior Increase Protection

This module implements the CRITICAL reduction eligibility gate that ensures
SPUs increased by Step 7, 8, or 9 are NOT reduced by Step 10.

⚠️ CRITICAL RULE (from customer requirements):
Any SPU that was increased or flagged for increase in Step 7, 8, or 9
❌ MUST NOT be reduced in Step 10.

This rule must be:
- Explicitly implemented in code (this module)
- Clearly documented in the Step 10 report
- Verifiable in sample runs

Author: Data Pipeline Team
Date: January 2026
"""

import pandas as pd
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

from step10_config import (
    Step10Config,
    DEFAULT_CONFIG,
    is_core_subcategory,
)


class ReductionEligibility(Enum):
    """Eligibility status for reduction in Step 10."""
    ELIGIBLE_FOR_REDUCTION = "ELIGIBLE_FOR_REDUCTION"
    BLOCKED_STEP7_INCREASE = "BLOCKED_STEP7_INCREASE"
    BLOCKED_STEP8_INCREASE = "BLOCKED_STEP8_INCREASE"
    BLOCKED_STEP9_INCREASE = "BLOCKED_STEP9_INCREASE"
    BLOCKED_CORE_SUBCATEGORY = "BLOCKED_CORE_SUBCATEGORY"
    BLOCKED_INELIGIBLE = "BLOCKED_INELIGIBLE"


@dataclass
class ReductionGateResult:
    """Result of reduction eligibility check."""
    eligibility: ReductionEligibility
    reason: str
    can_reduce: bool
    
    # Prior step flags
    step7_increase: bool
    step8_increase: bool
    step9_increase: bool
    
    # Metadata
    is_core_subcategory: bool
    eligibility_status: str
    
    # Reduction cap (if eligible)
    max_reduction_percentage: float


def check_reduction_eligibility(
    str_code: str,
    spu_code: str,
    category_name: Optional[str],
    eligibility_status: str,
    step7_recommended: bool = False,
    step8_adjusted: bool = False,
    step9_applied: bool = False,
    config: Step10Config = DEFAULT_CONFIG
) -> ReductionGateResult:
    """
    Check if an SPU × Store is eligible for reduction in Step 10.
    
    ⚠️ CRITICAL RULE:
    reduction_allowed = NOT(step7_increase OR step8_increase OR step9_increase)
    
    Args:
        str_code: Store code
        spu_code: SPU code
        category_name: Product category (for core subcategory check)
        eligibility_status: From Step 7 (ELIGIBLE/INELIGIBLE/UNKNOWN)
        step7_recommended: Whether Step 7 recommended adding this SPU
        step8_adjusted: Whether Step 8 adjusted this SPU (increase)
        step9_applied: Whether Step 9 applied an increase
        config: Step 10 configuration
    
    Returns:
        ReductionGateResult with eligibility status and reason
    """
    is_core = is_core_subcategory(category_name)
    
    # Base result template
    base_result = {
        'step7_increase': step7_recommended,
        'step8_increase': step8_adjusted,
        'step9_increase': step9_applied,
        'is_core_subcategory': is_core,
        'eligibility_status': eligibility_status,
        'max_reduction_percentage': config.max_reduction_percentage,
    }
    
    # ⚠️ CRITICAL CHECK: Prior increases block reduction
    if config.respect_prior_increases:
        # Check Step 7 increase
        if step7_recommended:
            return ReductionGateResult(
                eligibility=ReductionEligibility.BLOCKED_STEP7_INCREASE,
                reason="SPU was recommended for addition by Step 7 - cannot reduce",
                can_reduce=False,
                **base_result
            )
        
        # Check Step 8 increase
        if step8_adjusted:
            return ReductionGateResult(
                eligibility=ReductionEligibility.BLOCKED_STEP8_INCREASE,
                reason="SPU was adjusted (increased) by Step 8 - cannot reduce",
                can_reduce=False,
                **base_result
            )
        
        # Check Step 9 increase
        if step9_applied:
            return ReductionGateResult(
                eligibility=ReductionEligibility.BLOCKED_STEP9_INCREASE,
                reason="SPU was increased by Step 9 (below minimum) - cannot reduce",
                can_reduce=False,
                **base_result
            )
    
    # Check eligibility status (INELIGIBLE items shouldn't be reduced either)
    if eligibility_status == 'INELIGIBLE':
        return ReductionGateResult(
            eligibility=ReductionEligibility.BLOCKED_INELIGIBLE,
            reason="SPU is ineligible (per Step 7) - no reduction needed",
            can_reduce=False,
            **base_result
        )
    
    # Core subcategory protection (reduced cap, not blocked)
    if is_core and config.protect_core_subcategories:
        base_result['max_reduction_percentage'] = config.core_subcategory_max_reduction
        return ReductionGateResult(
            eligibility=ReductionEligibility.ELIGIBLE_FOR_REDUCTION,
            reason=f"Core subcategory - reduced cap ({config.core_subcategory_max_reduction:.0%})",
            can_reduce=True,
            **base_result
        )
    
    # Eligible for reduction
    return ReductionGateResult(
        eligibility=ReductionEligibility.ELIGIBLE_FOR_REDUCTION,
        reason="No prior increases - eligible for reduction",
        can_reduce=True,
        **base_result
    )


def apply_reduction_gate(
    overcapacity_df: pd.DataFrame,
    step7_df: pd.DataFrame,
    step8_df: pd.DataFrame,
    step9_df: pd.DataFrame,
    config: Step10Config = DEFAULT_CONFIG
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """
    Apply reduction eligibility gate to overcapacity candidates.
    
    This is the main integration point that merges Step 7-9 outputs
    and filters out SPUs that should not be reduced.
    
    Args:
        overcapacity_df: Overcapacity candidates from Step 10 detection
        step7_df: Step 7 output (eligibility + recommendations)
        step8_df: Step 8 output (adjustments)
        step9_df: Step 9 output (below minimum increases)
        config: Step 10 configuration
    
    Returns:
        Tuple of (eligible_df, blocked_df, summary_stats)
    """
    print("\n🔒 APPLYING REDUCTION ELIGIBILITY GATE")
    print("=" * 60)
    print("⚠️ CRITICAL RULE: SPUs increased by Step 7/8/9 CANNOT be reduced")
    
    df = overcapacity_df.copy()
    df['str_code'] = df['str_code'].astype(str)
    if 'spu_code' in df.columns:
        df['spu_code'] = df['spu_code'].astype(str)
    
    # Initialize flags
    df['step7_increase'] = False
    df['step8_increase'] = False
    df['step9_increase'] = False
    
    # Merge Step 7 recommendations (ADD recommendations)
    if not step7_df.empty:
        step7_df = step7_df.copy()
        step7_df['str_code'] = step7_df['str_code'].astype(str)
        if 'spu_code' in step7_df.columns:
            step7_df['spu_code'] = step7_df['spu_code'].astype(str)
        
        # Identify Step 7 ADD recommendations
        if 'recommendation' in step7_df.columns:
            step7_adds = step7_df[step7_df['recommendation'] == 'ADD'][['str_code', 'spu_code']].drop_duplicates()
        elif 'eligibility_status' in step7_df.columns:
            step7_adds = step7_df[step7_df['eligibility_status'] == 'ELIGIBLE'][['str_code', 'spu_code']].drop_duplicates()
        else:
            step7_adds = pd.DataFrame()
        
        if not step7_adds.empty:
            step7_adds['_step7_flag'] = True
            df = df.merge(step7_adds, on=['str_code', 'spu_code'], how='left')
            df['step7_increase'] = df['_step7_flag'].fillna(False)
            df = df.drop(columns=['_step7_flag'], errors='ignore')
    
    # Merge Step 8 adjustments (increases only)
    if not step8_df.empty:
        step8_df = step8_df.copy()
        step8_df['str_code'] = step8_df['str_code'].astype(str)
        if 'spu_code' in step8_df.columns:
            step8_df['spu_code'] = step8_df['spu_code'].astype(str)
        
        # Identify Step 8 increases
        if 'recommended_quantity_change' in step8_df.columns:
            step8_increases = step8_df[step8_df['recommended_quantity_change'] > 0][['str_code', 'spu_code']].drop_duplicates()
        elif 'is_imbalanced' in step8_df.columns:
            step8_increases = step8_df[step8_df['is_imbalanced'] == True][['str_code', 'spu_code']].drop_duplicates()
        else:
            step8_increases = pd.DataFrame()
        
        if not step8_increases.empty:
            step8_increases['_step8_flag'] = True
            df = df.merge(step8_increases, on=['str_code', 'spu_code'], how='left')
            df['step8_increase'] = df['_step8_flag'].fillna(False)
            df = df.drop(columns=['_step8_flag'], errors='ignore')
    
    # Merge Step 9 increases
    if not step9_df.empty:
        step9_df = step9_df.copy()
        step9_df['str_code'] = step9_df['str_code'].astype(str)
        if 'spu_code' in step9_df.columns:
            step9_df['spu_code'] = step9_df['spu_code'].astype(str)
        
        # Identify Step 9 increases
        if 'rule9_applied' in step9_df.columns:
            step9_increases = step9_df[step9_df['rule9_applied'] == True][['str_code', 'spu_code']].drop_duplicates()
        elif 'recommended_quantity_change' in step9_df.columns:
            step9_increases = step9_df[step9_df['recommended_quantity_change'] > 0][['str_code', 'spu_code']].drop_duplicates()
        else:
            step9_increases = pd.DataFrame()
        
        if not step9_increases.empty:
            step9_increases['_step9_flag'] = True
            df = df.merge(step9_increases, on=['str_code', 'spu_code'], how='left')
            df['step9_increase'] = df['_step9_flag'].fillna(False)
            df = df.drop(columns=['_step9_flag'], errors='ignore')
    
    # Apply reduction gate
    df['reduction_allowed'] = ~(df['step7_increase'] | df['step8_increase'] | df['step9_increase'])
    
    # Add reason column
    def get_block_reason(row):
        if row['step7_increase']:
            return "BLOCKED: Step 7 recommended addition"
        if row['step8_increase']:
            return "BLOCKED: Step 8 adjusted (increased)"
        if row['step9_increase']:
            return "BLOCKED: Step 9 applied increase"
        return "ELIGIBLE: No prior increases"
    
    df['reduction_gate_reason'] = df.apply(get_block_reason, axis=1)
    
    # Split into eligible and blocked
    eligible_df = df[df['reduction_allowed'] == True].copy()
    blocked_df = df[df['reduction_allowed'] == False].copy()
    
    # Summary statistics
    summary = {
        'total_candidates': len(df),
        'eligible_for_reduction': len(eligible_df),
        'blocked_total': len(blocked_df),
        'blocked_by_step7': int(df['step7_increase'].sum()),
        'blocked_by_step8': int(df['step8_increase'].sum()),
        'blocked_by_step9': int(df['step9_increase'].sum()),
        'reduction_gate_compliance': True,
    }
    
    print(f"\n📊 REDUCTION GATE RESULTS:")
    print(f"   Total overcapacity candidates: {summary['total_candidates']:,}")
    print(f"   ✅ Eligible for reduction: {summary['eligible_for_reduction']:,}")
    print(f"   ❌ Blocked (total): {summary['blocked_total']:,}")
    print(f"      - Blocked by Step 7: {summary['blocked_by_step7']:,}")
    print(f"      - Blocked by Step 8: {summary['blocked_by_step8']:,}")
    print(f"      - Blocked by Step 9: {summary['blocked_by_step9']:,}")
    print(f"\n✅ CRITICAL RULE ENFORCED: No SPU increased by Step 7/8/9 will be reduced")
    
    return eligible_df, blocked_df, summary
