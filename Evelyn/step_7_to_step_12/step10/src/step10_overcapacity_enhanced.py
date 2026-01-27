"""
Step 10 Enhanced: Overcapacity Reduction with Prior Increase Protection

This module implements the refactored Step 10 with strict adherence to
the layered decision system (Step 7 → Step 8 → Step 9 → Step 10).

⚠️ CRITICAL RULE:
Step 10 is a CLEANUP layer applied AFTER needs are satisfied.
Any SPU increased by Step 7, 8, or 9 MUST NOT be reduced.

Key Features:
- Reduction eligibility gate (respects Step 7-9 increases)
- Core subcategory protection (reduced cap, not blocked)
- Full explainability in output
- Integration with decision tree

Author: Data Pipeline Team
Date: January 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime
from dataclasses import asdict

import sys
STEP10_PATH = Path(__file__).parent
STEP9_PATH = STEP10_PATH.parent / "step9"
STEP7_PATH = STEP10_PATH.parent / "step7"
sys.path.insert(0, str(STEP10_PATH))
sys.path.insert(0, str(STEP9_PATH))
sys.path.insert(0, str(STEP7_PATH))

from step10_config import (
    Step10Config,
    DEFAULT_CONFIG,
    CORE_SUBCATEGORIES,
    is_core_subcategory,
    validate_config_against_requirements,
)
from step10_reduction_gate import (
    ReductionEligibility,
    check_reduction_eligibility,
    apply_reduction_gate,
)


def load_step7_output(step7_path: str) -> pd.DataFrame:
    """Load Step 7 eligibility and recommendation output."""
    print(f"📂 Loading Step 7 output: {step7_path}")
    
    if not Path(step7_path).exists():
        print(f"⚠️ Step 7 output not found")
        return pd.DataFrame()
    
    df = pd.read_csv(step7_path, dtype={'str_code': str, 'spu_code': str})
    print(f"   Loaded {len(df):,} Step 7 records")
    return df


def load_step8_output(step8_path: str) -> pd.DataFrame:
    """Load Step 8 adjustment output."""
    print(f"📂 Loading Step 8 output: {step8_path}")
    
    if not Path(step8_path).exists():
        print(f"⚠️ Step 8 output not found")
        return pd.DataFrame()
    
    df = pd.read_csv(step8_path, dtype={'str_code': str, 'spu_code': str})
    print(f"   Loaded {len(df):,} Step 8 records")
    return df


def load_step9_output(step9_path: str) -> pd.DataFrame:
    """Load Step 9 below minimum output."""
    print(f"📂 Loading Step 9 output: {step9_path}")
    
    if not Path(step9_path).exists():
        print(f"⚠️ Step 9 output not found")
        return pd.DataFrame()
    
    df = pd.read_csv(step9_path, dtype={'str_code': str, 'spu_code': str})
    print(f"   Loaded {len(df):,} Step 9 records")
    return df


def detect_overcapacity(
    allocation_df: pd.DataFrame,
    config: Step10Config = DEFAULT_CONFIG
) -> pd.DataFrame:
    """
    Detect overcapacity SPUs (current > target).
    
    This is the base overcapacity detection before applying the reduction gate.
    """
    print("\n🔍 Detecting overcapacity candidates...")
    
    df = allocation_df.copy()
    
    # Ensure required columns
    if 'current_spu_count' not in df.columns:
        df['current_spu_count'] = df.get('quantity', 0)
    if 'target_spu_count' not in df.columns:
        df['target_spu_count'] = df.get('target_quantity', df['current_spu_count'] * 0.8)
    
    # Calculate overcapacity
    df['excess_quantity'] = df['current_spu_count'] - df['target_spu_count']
    df['is_overcapacity'] = df['excess_quantity'] > 0
    
    # Calculate potential reduction
    df['potential_reduction'] = np.maximum(0, df['excess_quantity'])
    df['max_reduction'] = df['current_spu_count'] * config.max_reduction_percentage
    df['constrained_reduction'] = np.minimum(df['potential_reduction'], df['max_reduction'])
    
    # Filter to overcapacity cases
    overcapacity_df = df[df['is_overcapacity']].copy()
    
    print(f"   Found {len(overcapacity_df):,} overcapacity candidates")
    
    return overcapacity_df


def run_step10_enhanced(
    allocation_df: pd.DataFrame,
    step7_output_path: str,
    step8_output_path: str,
    step9_output_path: str,
    output_path: str,
    period_label: str = "202506A",
    config: Step10Config = DEFAULT_CONFIG
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Run enhanced Step 10 with reduction eligibility gate.
    
    Args:
        allocation_df: SPU allocation data
        step7_output_path: Path to Step 7 output
        step8_output_path: Path to Step 8 output
        step9_output_path: Path to Step 9 output
        output_path: Path to save results
        period_label: Current period
        config: Step 10 configuration
    
    Returns:
        Tuple of (all_results_df, eligible_reductions_df, blocked_df)
    """
    print("\n" + "="*70)
    print("STEP 10 ENHANCED: OVERCAPACITY REDUCTION")
    print("With Prior Increase Protection (Step 7-9 Integration)")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Period: {period_label}")
    
    # Validate configuration against requirements
    config_checks = validate_config_against_requirements()
    print(f"\n📋 Configuration Validation:")
    for check, passed in config_checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}: {passed}")
    
    # CRITICAL: Verify respect_prior_increases is True
    if not config.respect_prior_increases:
        print("\n❌ CRITICAL ERROR: respect_prior_increases must be True!")
        print("   This violates customer requirement.")
        raise ValueError("Configuration violation: respect_prior_increases must be True")
    
    # Load Step 7-9 outputs
    step7_df = load_step7_output(step7_output_path)
    step8_df = load_step8_output(step8_output_path)
    step9_df = load_step9_output(step9_output_path)
    
    # Detect overcapacity candidates
    overcapacity_df = detect_overcapacity(allocation_df, config)
    
    if len(overcapacity_df) == 0:
        print("\n✅ No overcapacity candidates found")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    # Apply reduction eligibility gate (CRITICAL)
    eligible_df, blocked_df, gate_summary = apply_reduction_gate(
        overcapacity_df=overcapacity_df,
        step7_df=step7_df,
        step8_df=step8_df,
        step9_df=step9_df,
        config=config
    )
    
    # Apply core subcategory protection to eligible reductions
    if len(eligible_df) > 0 and config.protect_core_subcategories:
        print("\n🛡️ Applying core subcategory protection...")
        
        if 'sub_cate_name' in eligible_df.columns:
            eligible_df['is_core_subcategory'] = eligible_df['sub_cate_name'].apply(is_core_subcategory)
            
            # Reduce cap for core subcategories
            core_mask = eligible_df['is_core_subcategory']
            eligible_df.loc[core_mask, 'max_reduction'] = (
                eligible_df.loc[core_mask, 'current_spu_count'] * config.core_subcategory_max_reduction
            )
            eligible_df.loc[core_mask, 'constrained_reduction'] = np.minimum(
                eligible_df.loc[core_mask, 'potential_reduction'],
                eligible_df.loc[core_mask, 'max_reduction']
            )
            
            core_count = core_mask.sum()
            print(f"   Core subcategories with reduced cap: {core_count:,}")
    
    # Calculate final recommendations
    if len(eligible_df) > 0:
        eligible_df['recommended_quantity_change'] = -eligible_df['constrained_reduction']
        eligible_df['rule10_applied'] = True
        eligible_df['rule10_reason'] = eligible_df.apply(
            lambda r: f"Overcapacity reduction: -{r['constrained_reduction']:.1f} units "
                      f"(excess: {r['excess_quantity']:.1f})",
            axis=1
        )
    
    # Add rule10_applied = False to blocked records
    if len(blocked_df) > 0:
        blocked_df['recommended_quantity_change'] = 0
        blocked_df['rule10_applied'] = False
        blocked_df['rule10_reason'] = blocked_df['reduction_gate_reason']
    
    # Combine all results
    all_results = pd.concat([eligible_df, blocked_df], ignore_index=True)
    
    # Summary statistics
    print(f"\n📊 STEP 10 RESULTS SUMMARY:")
    print(f"   Total overcapacity candidates: {len(all_results):,}")
    print(f"   ✅ Eligible for reduction: {len(eligible_df):,}")
    print(f"   ❌ Blocked (prior increases): {len(blocked_df):,}")
    
    if len(eligible_df) > 0:
        total_reduction = -eligible_df['recommended_quantity_change'].sum()
        print(f"   Total recommended reduction: {total_reduction:,.1f} units")
    
    # Save results
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_results.to_csv(output_path, index=False)
    print(f"\n💾 Saved all results: {output_path}")
    
    eligible_path = str(output_path).replace('.csv', '_eligible.csv')
    eligible_df.to_csv(eligible_path, index=False)
    print(f"💾 Saved eligible reductions: {eligible_path}")
    
    blocked_path = str(output_path).replace('.csv', '_blocked.csv')
    blocked_df.to_csv(blocked_path, index=False)
    print(f"💾 Saved blocked records: {blocked_path}")
    
    return all_results, eligible_df, blocked_df


if __name__ == "__main__":
    print("Step 10 Enhanced - Run via run_step10_comparison.py for sample execution")
