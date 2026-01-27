"""
Step 9 Enhanced: Below Minimum SPU Rule with Customer Deviation Guardrails

This module implements the refactored Step 9 with strict adherence to customer
requirements and deviation guardrails.

Key Features:
- Decision tree integration (Step 7 eligibility → Step 8 skip → Step 9)
- Core subcategory protection (always evaluated)
- 3-level minimum fallback (manual → cluster P10 → global)
- Sell-through validation gate
- Conservative quantity increase (never decrease, never negative)
- Full explainability in output

Per Customer Requirements:
- E-04: Core subcategories must be included
- E-05: Stay within ±20% of manual/historical
- E-06: Never decrease, no negative quantities
- I-01, I-02: Full explainability
- I-05: Business priorities override algorithms

Author: Data Pipeline Team
Date: January 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from dataclasses import asdict

import sys
STEP7_PATH = Path(__file__).parent.parent / "step7"
sys.path.insert(0, str(STEP7_PATH))

from step9_config import (
    Step9Config,
    DEFAULT_CONFIG,
    CORE_SUBCATEGORIES,
    is_core_subcategory,
    validate_config_against_requirements,
)
from step9_minimum_evaluator import (
    BelowMinimumStatus,
    BelowMinimumResult,
    evaluate_below_minimum,
    validate_no_negatives,
)


def load_step7_eligibility(step7_output_path: str) -> pd.DataFrame:
    """Load Step 7 eligibility output."""
    print(f"📂 Loading Step 7 eligibility: {step7_output_path}")
    
    if not Path(step7_output_path).exists():
        print(f"⚠️ Step 7 output not found, using UNKNOWN for all")
        return pd.DataFrame()
    
    df = pd.read_csv(step7_output_path, dtype={'str_code': str, 'spu_code': str})
    
    if 'eligibility_status' not in df.columns:
        df['eligibility_status'] = 'UNKNOWN'
    
    print(f"   Loaded {len(df):,} eligibility records")
    return df


def load_step8_adjustments(step8_output_path: str) -> pd.DataFrame:
    """Load Step 8 adjustment flags."""
    print(f"📂 Loading Step 8 adjustments: {step8_output_path}")
    
    if not Path(step8_output_path).exists():
        print(f"⚠️ Step 8 output not found, assuming no adjustments")
        return pd.DataFrame()
    
    df = pd.read_csv(step8_output_path, dtype={'str_code': str, 'spu_code': str})
    
    # Mark adjusted records
    if 'is_imbalanced' in df.columns:
        df['adjusted_by_step8'] = df['is_imbalanced'].fillna(False)
    elif 'recommended_change' in df.columns:
        df['adjusted_by_step8'] = df['recommended_change'].fillna(0) != 0
    else:
        df['adjusted_by_step8'] = False
    
    print(f"   Loaded {len(df):,} Step 8 records")
    adjusted_count = df['adjusted_by_step8'].sum()
    print(f"   Adjusted by Step 8: {adjusted_count:,}")
    
    return df


def prepare_input_data(
    allocation_df: pd.DataFrame,
    eligibility_df: pd.DataFrame,
    step8_df: pd.DataFrame,
    cluster_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Prepare input data by merging eligibility and Step 8 flags.
    
    This implements the decision tree integration:
    - Merge eligibility from Step 7
    - Merge adjustment flags from Step 8
    - Add cluster information for P10 calculation
    """
    print("\n🔗 Preparing input data with decision tree integration...")
    
    df = allocation_df.copy()
    df['str_code'] = df['str_code'].astype(str)
    if 'spu_code' in df.columns:
        df['spu_code'] = df['spu_code'].astype(str)
    
    # Merge eligibility from Step 7
    if not eligibility_df.empty:
        elig_cols = ['str_code', 'spu_code', 'eligibility_status']
        elig_cols = [c for c in elig_cols if c in eligibility_df.columns]
        if len(elig_cols) >= 2:
            df = df.merge(
                eligibility_df[elig_cols].drop_duplicates(),
                on=['str_code', 'spu_code'] if 'spu_code' in elig_cols else ['str_code'],
                how='left'
            )
    
    if 'eligibility_status' not in df.columns:
        df['eligibility_status'] = 'UNKNOWN'
    df['eligibility_status'] = df['eligibility_status'].fillna('UNKNOWN')
    
    # Merge Step 8 adjustment flags
    if not step8_df.empty:
        step8_cols = ['str_code', 'spu_code', 'adjusted_by_step8']
        step8_cols = [c for c in step8_cols if c in step8_df.columns]
        if len(step8_cols) >= 2:
            df = df.merge(
                step8_df[step8_cols].drop_duplicates(),
                on=['str_code', 'spu_code'] if 'spu_code' in step8_cols else ['str_code'],
                how='left'
            )
    
    if 'adjusted_by_step8' not in df.columns:
        df['adjusted_by_step8'] = False
    df['adjusted_by_step8'] = df['adjusted_by_step8'].fillna(False)
    
    # Merge cluster information
    if not cluster_df.empty:
        cluster_df['str_code'] = cluster_df['str_code'].astype(str)
        cluster_col = 'cluster_id' if 'cluster_id' in cluster_df.columns else 'Cluster'
        if cluster_col in cluster_df.columns:
            df = df.merge(
                cluster_df[['str_code', cluster_col]].drop_duplicates(),
                on='str_code',
                how='left'
            )
            if cluster_col != 'cluster_id':
                df['cluster_id'] = df[cluster_col]
    
    print(f"   Prepared {len(df):,} records")
    print(f"   Eligibility distribution: {df['eligibility_status'].value_counts().to_dict()}")
    print(f"   Adjusted by Step 8: {df['adjusted_by_step8'].sum():,}")
    
    return df


def calculate_cluster_p10_rates(df: pd.DataFrame, quantity_col: str = 'quantity') -> Dict[int, float]:
    """Calculate 10th percentile unit rates per cluster."""
    if 'cluster_id' not in df.columns or quantity_col not in df.columns:
        return {}
    
    p10_rates = {}
    for cluster_id, group in df.groupby('cluster_id'):
        if len(group) >= 5:  # Minimum cluster size
            p10 = group[quantity_col].quantile(0.10)
            if pd.notna(p10) and p10 > 0:
                p10_rates[cluster_id] = float(p10)
    
    return p10_rates


def run_step9_enhanced(
    allocation_df: pd.DataFrame,
    step7_eligibility_path: str,
    step8_output_path: str,
    cluster_path: str,
    output_path: str,
    period_label: str = "202506A",
    config: Step9Config = DEFAULT_CONFIG
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run enhanced Step 9 with customer deviation guardrails.
    
    Args:
        allocation_df: SPU allocation data
        step7_eligibility_path: Path to Step 7 eligibility output
        step8_output_path: Path to Step 8 output
        cluster_path: Path to clustering results
        output_path: Path to save results
        period_label: Current period
        config: Step 9 configuration
    
    Returns:
        Tuple of (results_df, opportunities_df)
    """
    print("\n" + "="*70)
    print("STEP 9 ENHANCED: BELOW MINIMUM SPU RULE")
    print("With Customer Deviation Guardrails")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Period: {period_label}")
    
    # Validate configuration against requirements
    config_checks = validate_config_against_requirements()
    print(f"\n📋 Configuration Validation:")
    for check, passed in config_checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}: {passed}")
    
    # Load dependencies
    eligibility_df = load_step7_eligibility(step7_eligibility_path)
    step8_df = load_step8_adjustments(step8_output_path)
    
    cluster_df = pd.DataFrame()
    if Path(cluster_path).exists():
        cluster_df = pd.read_csv(cluster_path, dtype={'str_code': str})
        print(f"📂 Loaded {len(cluster_df):,} cluster assignments")
    
    # Prepare input data
    df = prepare_input_data(allocation_df, eligibility_df, step8_df, cluster_df)
    
    # Calculate cluster P10 rates for 3-level fallback
    quantity_col = 'quantity' if 'quantity' in df.columns else 'unit_rate'
    if quantity_col not in df.columns:
        df[quantity_col] = 0.0
    
    cluster_p10_rates = calculate_cluster_p10_rates(df, quantity_col)
    print(f"\n📊 Cluster P10 rates calculated for {len(cluster_p10_rates)} clusters")
    
    # Evaluate each SPU × Store
    print(f"\n🔍 Evaluating {len(df):,} SPU × Store combinations...")
    
    results: List[Dict] = []
    
    for idx, row in df.iterrows():
        # Get cluster P10 for this record
        cluster_id = row.get('cluster_id')
        cluster_p10 = cluster_p10_rates.get(cluster_id) if pd.notna(cluster_id) else None
        
        # Evaluate below minimum
        result = evaluate_below_minimum(
            str_code=str(row['str_code']),
            spu_code=str(row.get('spu_code', '')),
            current_quantity=float(row.get(quantity_col, 0) or 0),
            category_name=row.get('sub_cate_name'),
            eligibility_status=str(row.get('eligibility_status', 'UNKNOWN')),
            adjusted_by_step8=bool(row.get('adjusted_by_step8', False)),
            cluster_p10_rate=cluster_p10,
            recent_sales_units=row.get('recent_sales_units'),
            sell_through_rate=row.get('sell_through_rate'),
            config=config
        )
        
        # Convert to dict and add identifiers
        result_dict = asdict(result)
        result_dict['str_code'] = row['str_code']
        result_dict['spu_code'] = row.get('spu_code', '')
        result_dict['sub_cate_name'] = row.get('sub_cate_name', '')
        result_dict['category_type'] = row.get('category_type', '')
        result_dict['cluster_id'] = cluster_id
        result_dict['status'] = result.status.value
        
        results.append(result_dict)
    
    results_df = pd.DataFrame(results)
    
    # Validate no negatives (per E-06)
    validation = validate_no_negatives([
        BelowMinimumResult(**{k: v for k, v in r.items() 
                             if k in BelowMinimumResult.__dataclass_fields__})
        for r in results if r.get('rule9_applied', False)
    ])
    
    print(f"\n✅ Validation (E-06 - No Negatives):")
    print(f"   Total evaluated: {validation['total_results']}")
    print(f"   Negative count: {validation['negative_count']}")
    print(f"   Requirement met: {validation['requirement_E06_met']}")
    
    # Extract opportunities (below minimum cases)
    opportunities_df = results_df[
        results_df['status'] == BelowMinimumStatus.BELOW_MINIMUM.value
    ].copy()
    
    # Summary statistics
    print(f"\n📊 STEP 9 RESULTS SUMMARY:")
    status_counts = results_df['status'].value_counts()
    for status, count in status_counts.items():
        pct = 100 * count / len(results_df)
        print(f"   {status}: {count:,} ({pct:.1f}%)")
    
    print(f"\n   Below minimum opportunities: {len(opportunities_df):,}")
    if len(opportunities_df) > 0:
        total_increase = opportunities_df['recommended_quantity_change'].sum()
        print(f"   Total recommended increase: {total_increase:,} units")
        print(f"   Core subcategories in opportunities: "
              f"{opportunities_df['is_core_subcategory'].sum():,}")
    
    # Save results
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_df.to_csv(output_path, index=False)
    print(f"\n💾 Saved results: {output_path}")
    
    opp_path = str(output_path).replace('.csv', '_opportunities.csv')
    opportunities_df.to_csv(opp_path, index=False)
    print(f"💾 Saved opportunities: {opp_path}")
    
    return results_df, opportunities_df


if __name__ == "__main__":
    print("Step 9 Enhanced - Run via run_step9_comparison.py for sample execution")
