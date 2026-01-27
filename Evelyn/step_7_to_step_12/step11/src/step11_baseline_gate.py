"""
Step 11 Baseline Gate: Hard Eligibility Constraint

AXIS A: Baseline Gate Implementation

This module implements the baseline gate that ensures Step 11 only evaluates
SPU-store pairs that have already passed through Step 7-9 and are NOT flagged
for reduction in Step 10.

Per Customer Requirement:
- Step 11 evaluates only after baseline inventory alignment is completed
- This is an ELIGIBILITY GATE, not a scoring adjustment
- SPUs increased by Step 7-9 MUST NOT be reduced by Step 11
- SPUs reduced by Step 10 MUST NOT be recommended for increase by Step 11

Author: Data Pipeline Team
Date: January 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Optional
from dataclasses import dataclass

from step11_config import (
    Step11Config,
    DEFAULT_CONFIG,
    STEP7_OUTPUT_PATH,
    STEP8_OUTPUT_PATH,
    STEP9_OUTPUT_PATH,
    STEP10_OUTPUT_PATH,
)


@dataclass
class BaselineGateResult:
    """Result of baseline gate evaluation."""
    passed: bool
    reason: str
    step7_eligible: bool
    step8_adjusted: bool
    step9_applied: bool
    step10_reduced: bool


def load_step7_eligibility(path: Optional[Path] = None) -> pd.DataFrame:
    """Load Step 7 eligibility output."""
    path = path or STEP7_OUTPUT_PATH
    if not path.exists():
        print(f"⚠️ Step 7 output not found: {path}")
        return pd.DataFrame()
    
    df = pd.read_csv(path, dtype={'str_code': str, 'spu_code': str})
    print(f"📂 Loaded Step 7 eligibility: {len(df):,} records")
    return df


def load_step8_adjustments(path: Optional[Path] = None) -> pd.DataFrame:
    """Load Step 8 adjustment output."""
    path = path or STEP8_OUTPUT_PATH
    if not path.exists():
        print(f"⚠️ Step 8 output not found: {path}")
        return pd.DataFrame()
    
    df = pd.read_csv(path, dtype={'str_code': str, 'spu_code': str})
    print(f"📂 Loaded Step 8 adjustments: {len(df):,} records")
    return df


def load_step9_increases(path: Optional[Path] = None) -> pd.DataFrame:
    """Load Step 9 increase output."""
    path = path or STEP9_OUTPUT_PATH
    if not path.exists():
        print(f"⚠️ Step 9 output not found: {path}")
        return pd.DataFrame()
    
    df = pd.read_csv(path, dtype={'str_code': str, 'spu_code': str})
    print(f"📂 Loaded Step 9 increases: {len(df):,} records")
    return df


def load_step10_reductions(path: Optional[Path] = None) -> pd.DataFrame:
    """Load Step 10 reduction output."""
    path = path or STEP10_OUTPUT_PATH
    if not path.exists():
        print(f"⚠️ Step 10 output not found: {path}")
        return pd.DataFrame()
    
    df = pd.read_csv(path, dtype={'str_code': str, 'spu_code': str})
    print(f"📂 Loaded Step 10 reductions: {len(df):,} records")
    return df


def evaluate_baseline_gate(
    str_code: str,
    spu_code: str,
    step7_df: pd.DataFrame,
    step8_df: pd.DataFrame,
    step9_df: pd.DataFrame,
    step10_df: pd.DataFrame,
    config: Step11Config = DEFAULT_CONFIG
) -> BaselineGateResult:
    """
    Evaluate baseline gate for a single SPU-store pair.
    
    AXIS A: Baseline Gate (Hard Eligibility Constraint)
    
    Step 11 logic MUST only evaluate SPU-store pairs that:
    1. Have already passed through Step 7-9
    2. Are NOT flagged for reduction in Step 10
    
    Args:
        str_code: Store code
        spu_code: SPU code
        step7_df: Step 7 eligibility output
        step8_df: Step 8 adjustment output
        step9_df: Step 9 increase output
        step10_df: Step 10 reduction output
        config: Step 11 configuration
    
    Returns:
        BaselineGateResult with pass/fail status and reason
    """
    # Check Step 7 eligibility
    step7_eligible = False
    if not step7_df.empty:
        step7_match = step7_df[
            (step7_df['str_code'] == str_code) & 
            (step7_df['spu_code'] == spu_code)
        ]
        if not step7_match.empty:
            status = step7_match['eligibility_status'].iloc[0]
            step7_eligible = status in ['ELIGIBLE', 'UNKNOWN']
    
    # Check Step 8 adjustment
    step8_adjusted = False
    if not step8_df.empty:
        step8_match = step8_df[
            (step8_df['str_code'] == str_code) & 
            (step8_df['spu_code'] == spu_code)
        ]
        if not step8_match.empty:
            if 'recommended_quantity_change' in step8_match.columns:
                change = step8_match['recommended_quantity_change'].iloc[0]
                step8_adjusted = change > 0 if pd.notna(change) else False
    
    # Check Step 9 increase
    step9_applied = False
    if not step9_df.empty:
        step9_match = step9_df[
            (step9_df['str_code'] == str_code) & 
            (step9_df['spu_code'] == spu_code)
        ]
        if not step9_match.empty:
            if 'rule9_applied' in step9_match.columns:
                step9_applied = step9_match['rule9_applied'].iloc[0] == True
    
    # Check Step 10 reduction (CRITICAL: must exclude)
    step10_reduced = False
    if not step10_df.empty:
        step10_match = step10_df[
            (step10_df['str_code'] == str_code) & 
            (step10_df['spu_code'] == spu_code)
        ]
        if not step10_match.empty:
            if 'rule10_applied' in step10_match.columns:
                step10_reduced = step10_match['rule10_applied'].iloc[0] == True
    
    # Apply baseline gate logic
    if not config.require_baseline_gate:
        return BaselineGateResult(
            passed=True,
            reason="Baseline gate disabled",
            step7_eligible=step7_eligible,
            step8_adjusted=step8_adjusted,
            step9_applied=step9_applied,
            step10_reduced=step10_reduced
        )
    
    # CRITICAL: Exclude Step 10 reductions
    if config.exclude_step10_reductions and step10_reduced:
        return BaselineGateResult(
            passed=False,
            reason="BLOCKED: Step 10 reduction applied - cannot recommend increase",
            step7_eligible=step7_eligible,
            step8_adjusted=step8_adjusted,
            step9_applied=step9_applied,
            step10_reduced=step10_reduced
        )
    
    # Check eligibility requirement
    if config.only_evaluate_eligible_spus and not step7_eligible:
        return BaselineGateResult(
            passed=False,
            reason="BLOCKED: Not eligible per Step 7 (INELIGIBLE status)",
            step7_eligible=step7_eligible,
            step8_adjusted=step8_adjusted,
            step9_applied=step9_applied,
            step10_reduced=step10_reduced
        )
    
    # Passed all gates
    return BaselineGateResult(
        passed=True,
        reason="Passed baseline gate - eligible for Step 11 evaluation",
        step7_eligible=step7_eligible,
        step8_adjusted=step8_adjusted,
        step9_applied=step9_applied,
        step10_reduced=step10_reduced
    )


def apply_baseline_gate(
    opportunities_df: pd.DataFrame,
    step7_df: pd.DataFrame,
    step8_df: pd.DataFrame,
    step9_df: pd.DataFrame,
    step10_df: pd.DataFrame,
    config: Step11Config = DEFAULT_CONFIG
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """
    Apply baseline gate to all opportunity candidates.
    
    Args:
        opportunities_df: Candidate opportunities from Step 11 detection
        step7_df: Step 7 eligibility output
        step8_df: Step 8 adjustment output
        step9_df: Step 9 increase output
        step10_df: Step 10 reduction output
        config: Step 11 configuration
    
    Returns:
        Tuple of (eligible_df, blocked_df, summary_stats)
    """
    print("\n🚦 Applying Baseline Gate (Axis A)...")
    print("   Step 11 evaluates only after baseline inventory alignment is completed.")
    
    if opportunities_df.empty:
        return pd.DataFrame(), pd.DataFrame(), {'total': 0, 'passed': 0, 'blocked': 0}
    
    # Merge Step 7 eligibility
    if not step7_df.empty and 'eligibility_status' in step7_df.columns:
        opportunities_df = opportunities_df.merge(
            step7_df[['str_code', 'spu_code', 'eligibility_status']].drop_duplicates(),
            on=['str_code', 'spu_code'],
            how='left'
        )
        opportunities_df['eligibility_status'] = opportunities_df['eligibility_status'].fillna('UNKNOWN')
    else:
        opportunities_df['eligibility_status'] = 'UNKNOWN'
    
    # Merge Step 10 reduction flags
    if not step10_df.empty and 'rule10_applied' in step10_df.columns:
        step10_flags = step10_df[['str_code', 'spu_code', 'rule10_applied']].drop_duplicates()
        step10_flags = step10_flags.rename(columns={'rule10_applied': 'step10_reduced'})
        opportunities_df = opportunities_df.merge(
            step10_flags,
            on=['str_code', 'spu_code'],
            how='left'
        )
        opportunities_df['step10_reduced'] = opportunities_df['step10_reduced'].fillna(False)
    else:
        opportunities_df['step10_reduced'] = False
    
    # Apply gate logic
    opportunities_df['baseline_gate_passed'] = (
        (opportunities_df['eligibility_status'].isin(['ELIGIBLE', 'UNKNOWN'])) &
        (~opportunities_df['step10_reduced'])
    )
    
    # Generate gate reason
    def get_gate_reason(row):
        if row['step10_reduced']:
            return "BLOCKED: Step 10 reduction applied"
        if row['eligibility_status'] == 'INELIGIBLE':
            return "BLOCKED: Not eligible per Step 7"
        return "Passed baseline gate"
    
    opportunities_df['baseline_gate_reason'] = opportunities_df.apply(get_gate_reason, axis=1)
    
    # Split into eligible and blocked
    eligible_df = opportunities_df[opportunities_df['baseline_gate_passed']].copy()
    blocked_df = opportunities_df[~opportunities_df['baseline_gate_passed']].copy()
    
    # Summary statistics
    summary = {
        'total': len(opportunities_df),
        'passed': len(eligible_df),
        'blocked': len(blocked_df),
        'blocked_by_step10': (opportunities_df['step10_reduced']).sum(),
        'blocked_by_ineligible': (opportunities_df['eligibility_status'] == 'INELIGIBLE').sum(),
    }
    
    print(f"   ✅ Passed baseline gate: {summary['passed']:,}")
    print(f"   ❌ Blocked (total): {summary['blocked']:,}")
    print(f"      - Blocked by Step 10 reduction: {summary['blocked_by_step10']:,}")
    print(f"      - Blocked by ineligibility: {summary['blocked_by_ineligible']:,}")
    
    return eligible_df, blocked_df, summary
