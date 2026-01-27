"""
Step 12 Enhanced: Performance Gap Scaling

CRITICAL BOUNDARY DEFINITION:
- Step 11 decides WHAT to grow (is_growth_candidate, opportunity_score)
- Step 12 decides HOW MUCH to grow (recommended_adjustment_quantity)

This module orchestrates the enhanced Step 12 with all improvement axes:
- Axis A: Clear Performance Gap Definition
- Axis B: Controlled Scaling Logic (No Re-eligibility)
- Axis C: Multi-factor Scaling (Within Bounds)
- Axis D: Hard Safety Caps
- Axis E: Decision Traceability

Step 12 MUST NOT:
- Re-decide eligibility (that's Step 11's job)
- Override Step 9 below-minimum protection
- Conflict with Step 10 overstock reduction

Author: Data Pipeline Team
Date: January 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime
import json
import sys

STEP12_PATH = Path(__file__).parent
sys.path.insert(0, str(STEP12_PATH))

from step12_config import (
    Step12Config,
    DEFAULT_CONFIG,
    STEP12_BOUNDARY_STATEMENTS,
    validate_step12_boundaries,
    STEP11_OUTPUT_PATH,
    STEP9_OUTPUT_PATH,
    STEP10_OUTPUT_PATH,
)
from step12_gap_calculator import calculate_performance_gaps
from step12_scaling_engine import calculate_scaling_adjustment
from step12_traceability import add_traceability, generate_traceability_summary


def print_boundary_statements():
    """Print Step 12 boundary statements."""
    print("\n" + "="*70)
    print("🔒 STEP 12 BOUNDARY DEFINITION")
    print("="*70)
    print("   Step 11 decides WHAT to grow")
    print("   Step 12 decides HOW MUCH to grow")
    print("-"*70)
    for statement in STEP12_BOUNDARY_STATEMENTS:
        print(f"   ✓ {statement}")
    print("="*70 + "\n")


def load_step11_candidates(path: Optional[Path] = None) -> pd.DataFrame:
    """Load Step 11 approved candidates."""
    path = path or STEP11_OUTPUT_PATH
    if not path.exists():
        print(f"⚠️ Step 11 output not found: {path}")
        return pd.DataFrame()
    
    df = pd.read_csv(path, dtype={'str_code': str, 'spu_code': str})
    print(f"📂 Loaded Step 11 candidates: {len(df):,} records")
    return df


def load_step9_output(path: Optional[Path] = None) -> pd.DataFrame:
    """Load Step 9 output for conflict checking."""
    path = path or STEP9_OUTPUT_PATH
    if not path.exists():
        print(f"⚠️ Step 9 output not found: {path}")
        return pd.DataFrame()
    
    df = pd.read_csv(path, dtype={'str_code': str, 'spu_code': str})
    print(f"📂 Loaded Step 9 output: {len(df):,} records")
    return df


def load_step10_output(path: Optional[Path] = None) -> pd.DataFrame:
    """Load Step 10 output for conflict checking."""
    path = path or STEP10_OUTPUT_PATH
    if not path.exists():
        print(f"⚠️ Step 10 output not found: {path}")
        return pd.DataFrame()
    
    df = pd.read_csv(path, dtype={'str_code': str, 'spu_code': str})
    print(f"📂 Loaded Step 10 output: {len(df):,} records")
    return df


def run_step12_enhanced(
    step11_candidates: pd.DataFrame,
    sales_df: pd.DataFrame,
    step9_df: Optional[pd.DataFrame] = None,
    step10_df: Optional[pd.DataFrame] = None,
    store_traffic_df: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None,
    config: Step12Config = DEFAULT_CONFIG
) -> pd.DataFrame:
    """
    Run enhanced Step 12 Performance Gap Scaling.
    
    CRITICAL: This function ONLY processes Step 11-approved candidates.
    It does NOT identify new opportunities.
    
    Args:
        step11_candidates: Step 11 approved candidates (REQUIRED)
        sales_df: Current sales data with cluster assignments
        step9_df: Step 9 output for conflict checking
        step10_df: Step 10 output for conflict checking
        store_traffic_df: Store traffic data for affinity modulation
        output_path: Path to save results
        config: Step 12 configuration
    
    Returns:
        DataFrame with scaling recommendations
    """
    print("\n" + "="*70)
    print("STEP 12 ENHANCED: PERFORMANCE GAP SCALING")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Print boundary statements
    print_boundary_statements()
    
    # Validate configuration
    boundary_checks = validate_step12_boundaries()
    print("📋 Boundary validation:")
    for check, passed in boundary_checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
    
    # CRITICAL: Verify Step 11 candidates provided
    if step11_candidates.empty:
        print("\n❌ ERROR: No Step 11 candidates provided!")
        print("   Step 12 MUST receive Step 11 candidates as input.")
        print("   It cannot independently identify opportunities.")
        return pd.DataFrame()
    
    print(f"\n📊 Input: {len(step11_candidates):,} Step 11-approved candidates")
    
    # Load Step 9/10 outputs if not provided
    if step9_df is None:
        step9_df = load_step9_output()
    if step10_df is None:
        step10_df = load_step10_output()
    
    # Axis A: Calculate performance gaps for Step 11 candidates
    gap_df = calculate_performance_gaps(
        candidates_df=step11_candidates,
        sales_df=sales_df,
        config=config
    )
    
    if gap_df.empty:
        print("\n⚠️ No valid performance gaps calculated")
        return pd.DataFrame()
    
    # Axis B, C, D: Calculate scaling adjustments
    scaling_df = calculate_scaling_adjustment(
        gap_df=gap_df,
        step9_df=step9_df,
        step10_df=step10_df,
        store_traffic_df=store_traffic_df,
        config=config
    )
    
    if scaling_df.empty:
        print("\n⚠️ No scaling recommendations generated")
        return pd.DataFrame()
    
    # Axis E: Add traceability
    result_df = add_traceability(
        scaling_df=scaling_df,
        step11_df=step11_candidates,
        config=config
    )
    
    # Generate summary
    summary = generate_traceability_summary(result_df)
    
    print("\n" + "="*70)
    print("STEP 12 RESULTS SUMMARY")
    print("="*70)
    print(f"Total recommendations: {summary['total_recommendations']:,}")
    print(f"Total adjustment units: {summary['total_adjustment_units']:.1f}")
    print(f"Average adjustment: {summary['avg_adjustment']:.2f} units")
    print(f"Step 9 dampened: {summary['step9_dampened_count']:,}")
    
    print("\nScaling tiers:")
    for tier, count in summary.get('scaling_tiers', {}).items():
        print(f"   - {tier}: {count:,}")
    
    print("\nCaps applied:")
    for cap, count in summary.get('caps_applied', {}).items():
        print(f"   - {cap}: {count:,}")
    
    # Save results
    if output_path:
        result_df.to_csv(output_path, index=False)
        print(f"\n💾 Saved: {output_path}")
        
        # Save summary
        summary_path = output_path.parent / "step12_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"💾 Saved summary: {summary_path}")
    
    return result_df
