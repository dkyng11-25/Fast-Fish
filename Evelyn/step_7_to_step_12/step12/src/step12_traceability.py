"""
Step 12 Decision Traceability

AXIS E: Decision Traceability

For every recommendation, this module generates a structured explanation:
- Why this SPU was scaled
- Which peer benchmark it lagged
- Which factors affected the final quantity
- Why the result does NOT conflict with Steps 9-11

Author: Data Pipeline Team
Date: January 2026
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

from step12_config import Step12Config, DEFAULT_CONFIG, STEP12_BOUNDARY_STATEMENTS


@dataclass
class TraceabilityRecord:
    """Complete traceability record for a single scaling decision."""
    store_code: str
    spu_code: str
    cluster_id: int
    
    # Step 11 validation
    step11_candidate: bool
    step11_opportunity_score: float
    step11_tier: str
    
    # Performance gap justification
    store_sales: float
    cluster_p75: float
    cluster_median: float
    performance_gap: float
    gap_ratio: float
    gap_justification: str
    
    # Scaling factors
    base_scaling: float
    affinity_modifier: float
    step9_dampener: float
    cap_applied: str
    
    # Final recommendation
    recommended_adjustment: float
    scaling_tier: str
    
    # Conflict verification
    step9_conflict: str
    step10_conflict: str
    no_conflict_reason: str
    
    # Full explanation
    full_explanation: str


def generate_gap_justification(row: pd.Series) -> str:
    """Generate justification for why the gap indicates underperformance."""
    gap = row.get('performance_gap', 0)
    gap_ratio = row.get('gap_ratio', 0)
    percentile = row.get('percentile_in_cluster', 50)
    cluster_size = row.get('cluster_size', 0)
    
    if gap <= 0:
        return "Store exceeds cluster P75 benchmark - no scaling needed"
    
    justification = (
        f"Store sells {gap:.1f} fewer units than cluster P75 benchmark "
        f"(gap ratio: {gap_ratio:.1%}). "
        f"Store ranks at P{percentile:.0f} among {cluster_size} cluster peers. "
        f"Scaling is justified because Step 11 validated this as a growth candidate."
    )
    return justification


def generate_no_conflict_reason(row: pd.Series) -> str:
    """Generate explanation for why this does NOT conflict with Steps 9-11."""
    reasons = []
    
    # Step 11 validation
    reasons.append("✓ SPU is Step 11-approved growth candidate")
    
    # Step 9 check
    if row.get('step9_boosted', False):
        reasons.append("✓ Step 9 boost detected - 50% dampening applied (no conflict)")
    else:
        reasons.append("✓ No Step 9 below-minimum boost applied")
    
    # Step 10 check (if we got here, it wasn't blocked)
    reasons.append("✓ Not flagged for Step 10 reduction")
    
    # Scaling bounds
    cap = row.get('cap_applied', 'none')
    if cap != 'none':
        reasons.append(f"✓ Safety cap applied: {cap}")
    else:
        reasons.append("✓ Within all safety bounds")
    
    return " | ".join(reasons)


def generate_full_explanation(row: pd.Series) -> str:
    """Generate complete explanation for the scaling decision."""
    parts = []
    
    # Part 1: Why this SPU was scaled
    parts.append(f"WHY SCALED: Step 11 identified this as a {row.get('opportunity_tier', 'growth')} opportunity")
    
    # Part 2: Which benchmark it lagged
    gap = row.get('performance_gap', 0)
    p75 = row.get('cluster_p75', 0)
    parts.append(f"BENCHMARK LAG: Store sells {gap:.1f} units below cluster P75 ({p75:.1f})")
    
    # Part 3: Factors affecting quantity
    factors = []
    factors.append(f"base={row.get('base_scaling', 0):.1f}")
    factors.append(f"affinity={row.get('affinity_modifier', 1):.2f}x")
    if row.get('step9_boosted', False):
        factors.append(f"step9_dampen={row.get('step9_dampener', 1):.2f}x")
    parts.append(f"FACTORS: {', '.join(factors)}")
    
    # Part 4: Final recommendation
    adj = row.get('recommended_adjustment_quantity', 0)
    tier = row.get('scaling_tier', 'Unknown')
    parts.append(f"RECOMMENDATION: +{adj:.1f} units ({tier})")
    
    # Part 5: No conflict statement
    parts.append(f"NO CONFLICT: {generate_no_conflict_reason(row)}")
    
    return " || ".join(parts)


def add_traceability(
    scaling_df: pd.DataFrame,
    step11_df: pd.DataFrame,
    config: Step12Config = DEFAULT_CONFIG
) -> pd.DataFrame:
    """
    Add full traceability columns to scaling results.
    
    Args:
        scaling_df: Scaling results from step12_scaling_engine
        step11_df: Step 11 output for validation
        config: Step 12 configuration
    
    Returns:
        DataFrame with traceability columns added
    """
    print("\n📋 Adding decision traceability (Axis E)...")
    
    if scaling_df.empty:
        return scaling_df
    
    # Merge Step 11 info for traceability
    if not step11_df.empty:
        step11_cols = ['str_code', 'spu_code']
        if 'opportunity_tier' in step11_df.columns:
            step11_cols.append('opportunity_tier')
        if 'opportunity_score' in step11_df.columns:
            step11_cols.append('opportunity_score')
        if 'tier_score' in step11_df.columns:
            step11_cols.append('tier_score')
        
        scaling_df = scaling_df.merge(
            step11_df[step11_cols].drop_duplicates(),
            on=['str_code', 'spu_code'],
            how='left',
            suffixes=('', '_step11')
        )
    
    # Add traceability columns
    scaling_df['step11_validated'] = True  # All records are Step 11 candidates
    scaling_df['gap_justification'] = scaling_df.apply(generate_gap_justification, axis=1)
    scaling_df['no_conflict_reason'] = scaling_df.apply(generate_no_conflict_reason, axis=1)
    scaling_df['full_explanation'] = scaling_df.apply(generate_full_explanation, axis=1)
    
    # Add boundary statement
    scaling_df['step12_boundary_note'] = (
        "Step 12 scales ONLY Step 11-approved SPUs. "
        "It does NOT decide whether to scale - only how much."
    )
    
    print(f"   Added traceability to {len(scaling_df):,} records")
    
    return scaling_df


def generate_traceability_summary(scaling_df: pd.DataFrame) -> Dict:
    """Generate summary statistics for traceability report."""
    if scaling_df.empty:
        return {'total_recommendations': 0}
    
    summary = {
        'total_recommendations': len(scaling_df),
        'total_adjustment_units': scaling_df['recommended_adjustment_quantity'].sum(),
        'avg_adjustment': scaling_df['recommended_adjustment_quantity'].mean(),
        'step9_dampened_count': scaling_df['step9_boosted'].sum() if 'step9_boosted' in scaling_df.columns else 0,
        'caps_applied': scaling_df['cap_applied'].value_counts().to_dict(),
        'scaling_tiers': scaling_df['scaling_tier'].value_counts().to_dict(),
    }
    
    return summary
