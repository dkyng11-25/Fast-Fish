#!/usr/bin/env python3
"""
Step 8 Enhanced: Eligibility-Aware Imbalanced Allocation Rule

This module improves Step 8 by filtering imbalance calculations to only include
SPUs with eligibility_status == ELIGIBLE from Step 7.

DESIGN PRINCIPLE:
- Preserve original Step 8 z-score formula and thresholds
- Only change WHO is included in imbalance calculation (filtering)
- Do NOT change HOW imbalance is calculated

ENHANCEMENT SUMMARY:
- Load Step 7 eligibility output
- Filter to ELIGIBLE SPUs only before peer comparison
- Exclude INELIGIBLE and UNKNOWN SPUs from z-score calculation
- Preserve all original business logic and thresholds

Author: Data Pipeline Team
Date: January 2026
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Add parent path for imports
STEP7_PATH = Path(__file__).parent.parent.parent / "step7_step13" / "step7"
sys.path.insert(0, str(STEP7_PATH))

from eligibility_evaluator import EligibilityStatus


# =============================================================================
# CONFIGURATION (Preserved from original Step 8)
# =============================================================================

# Z-Score thresholds (UNCHANGED from original)
Z_SCORE_THRESHOLD = 3.0  # SPU level - top 10-15% outliers
MIN_CLUSTER_SIZE = 5     # Minimum stores for valid z-score
MIN_ALLOCATION_THRESHOLD = 0.05  # Minimum allocation to consider

# Quantity thresholds (UNCHANGED from original)
MIN_REBALANCE_QUANTITY = 5.0  # Minimum units to recommend
MAX_REBALANCE_PERCENTAGE = 0.3  # Max 30% of current allocation


@dataclass
class ImbalanceResult:
    """Result of imbalance analysis for a single SPU × Store."""
    str_code: str
    spu_code: str
    cluster_id: int
    current_quantity: float
    cluster_mean: float
    cluster_std: float
    z_score: float
    is_imbalanced: bool
    recommended_change: float
    eligibility_status: str
    eligibility_filtered: bool  # True if this SPU was filtered due to eligibility


# =============================================================================
# ELIGIBILITY FILTERING
# =============================================================================

def load_step7_eligibility(step7_output_file: str) -> pd.DataFrame:
    """
    Load Step 7 output with eligibility status.
    
    Args:
        step7_output_file: Path to Step 7 enhanced output CSV
    
    Returns:
        DataFrame with eligibility columns
    """
    print(f"📂 Loading Step 7 eligibility data: {step7_output_file}")
    
    if not os.path.exists(step7_output_file):
        print(f"⚠️ Step 7 output not found: {step7_output_file}")
        return pd.DataFrame()
    
    df = pd.read_csv(step7_output_file, dtype={'str_code': str, 'spu_code': str})
    
    # Ensure eligibility columns exist
    if 'eligibility_status' not in df.columns:
        print("⚠️ eligibility_status column not found in Step 7 output")
        df['eligibility_status'] = EligibilityStatus.UNKNOWN.value
    
    print(f"   Loaded {len(df):,} records")
    
    # Summary
    status_counts = df['eligibility_status'].value_counts()
    print(f"   Eligibility distribution:")
    for status, count in status_counts.items():
        print(f"      {status}: {count:,}")
    
    return df


def filter_eligible_spus(
    imbalance_data: pd.DataFrame,
    eligibility_data: pd.DataFrame,
    store_column: str = 'str_code',
    spu_column: str = 'spu_code'
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Filter imbalance data to only include ELIGIBLE SPUs.
    
    This is the key enhancement: only SPUs that passed Step 7's climate
    and time gates are included in imbalance calculations.
    
    Args:
        imbalance_data: DataFrame with SPU allocation data
        eligibility_data: DataFrame with eligibility_status from Step 7
        store_column: Column name for store identifier
        spu_column: Column name for SPU identifier
    
    Returns:
        Tuple of (eligible_df, excluded_df)
    """
    print("\n🔍 Applying eligibility-based filtering...")
    
    original_count = len(imbalance_data)
    
    if eligibility_data.empty:
        print("   ⚠️ No eligibility data available - using all SPUs (fallback)")
        return imbalance_data, pd.DataFrame()
    
    # Create eligibility lookup
    eligibility_lookup = eligibility_data[[store_column, spu_column, 'eligibility_status']].drop_duplicates()
    
    # Merge eligibility into imbalance data
    merged = imbalance_data.merge(
        eligibility_lookup,
        on=[store_column, spu_column],
        how='left'
    )
    
    # Fill missing eligibility as UNKNOWN
    merged['eligibility_status'] = merged['eligibility_status'].fillna(EligibilityStatus.UNKNOWN.value)
    
    # Filter to ELIGIBLE only
    eligible_df = merged[merged['eligibility_status'] == EligibilityStatus.ELIGIBLE.value].copy()
    excluded_df = merged[merged['eligibility_status'] != EligibilityStatus.ELIGIBLE.value].copy()
    
    eligible_count = len(eligible_df)
    excluded_count = len(excluded_df)
    
    print(f"   Original SPU × Store combinations: {original_count:,}")
    print(f"   ✅ ELIGIBLE (included in z-score): {eligible_count:,} ({100*eligible_count/original_count:.1f}%)")
    print(f"   ❌ EXCLUDED (INELIGIBLE/UNKNOWN): {excluded_count:,} ({100*excluded_count/original_count:.1f}%)")
    
    return eligible_df, excluded_df


# =============================================================================
# Z-SCORE CALCULATION (UNCHANGED LOGIC)
# =============================================================================

def calculate_cluster_zscore(
    df: pd.DataFrame,
    cluster_column: str = 'cluster_id',
    quantity_column: str = 'quantity',
    store_column: str = 'str_code',
    spu_column: str = 'spu_code'
) -> pd.DataFrame:
    """
    Calculate z-scores for SPU allocations within each cluster.
    
    IMPORTANT: This function's logic is UNCHANGED from original Step 8.
    Only the input data is filtered to ELIGIBLE SPUs.
    
    Args:
        df: DataFrame with SPU allocation data (already filtered to ELIGIBLE)
        cluster_column: Column name for cluster identifier
        quantity_column: Column name for quantity/allocation
        store_column: Column name for store identifier
        spu_column: Column name for SPU identifier
    
    Returns:
        DataFrame with z-score calculations
    """
    print("\n📊 Calculating z-scores (original Step 8 logic)...")
    
    result_df = df.copy()
    
    # Calculate cluster-level statistics for each SPU
    cluster_stats = df.groupby([cluster_column, spu_column])[quantity_column].agg(['mean', 'std', 'count']).reset_index()
    cluster_stats.columns = [cluster_column, spu_column, 'cluster_mean', 'cluster_std', 'cluster_count']
    
    # Merge statistics back
    result_df = result_df.merge(cluster_stats, on=[cluster_column, spu_column], how='left')
    
    # Calculate z-score (UNCHANGED FORMULA)
    # z = (x - mean) / std
    result_df['z_score'] = np.where(
        (result_df['cluster_std'] > 0) & (result_df['cluster_count'] >= MIN_CLUSTER_SIZE),
        (result_df[quantity_column] - result_df['cluster_mean']) / result_df['cluster_std'],
        0  # No z-score if insufficient data
    )
    
    # Flag imbalanced allocations (UNCHANGED THRESHOLD)
    result_df['is_imbalanced'] = np.abs(result_df['z_score']) > Z_SCORE_THRESHOLD
    
    # Calculate recommended change (UNCHANGED LOGIC)
    result_df['recommended_change'] = np.where(
        result_df['is_imbalanced'],
        result_df['cluster_mean'] - result_df[quantity_column],
        0
    )
    
    # Cap recommended change (UNCHANGED LOGIC)
    result_df['recommended_change'] = np.clip(
        result_df['recommended_change'],
        -result_df[quantity_column] * MAX_REBALANCE_PERCENTAGE,
        result_df[quantity_column] * MAX_REBALANCE_PERCENTAGE
    )
    
    # Filter to minimum rebalance quantity (UNCHANGED THRESHOLD)
    result_df.loc[np.abs(result_df['recommended_change']) < MIN_REBALANCE_QUANTITY, 'recommended_change'] = 0
    
    imbalanced_count = result_df['is_imbalanced'].sum()
    actionable_count = (result_df['recommended_change'] != 0).sum()
    
    print(f"   Total records analyzed: {len(result_df):,}")
    print(f"   Imbalanced (|z| > {Z_SCORE_THRESHOLD}): {imbalanced_count:,}")
    print(f"   Actionable recommendations: {actionable_count:,}")
    
    return result_df


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def run_eligibility_aware_step8(
    allocation_data_file: str,
    step7_eligibility_file: str,
    cluster_file: str,
    output_file: str,
    period_label: str = "202506A"
) -> pd.DataFrame:
    """
    Run the eligibility-aware Step 8 imbalance analysis.
    
    This is the main entry point for the enhanced module.
    
    Args:
        allocation_data_file: Path to SPU allocation data
        step7_eligibility_file: Path to Step 7 enhanced output with eligibility
        cluster_file: Path to clustering results
        output_file: Path to save enhanced results
        period_label: Current period (e.g., "202506A")
    
    Returns:
        Enhanced imbalance analysis DataFrame
    """
    print("\n" + "="*70)
    print("STEP 8 ENHANCED: ELIGIBILITY-AWARE IMBALANCED ALLOCATION RULE")
    print("="*70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Period: {period_label}")
    print(f"\n⚠️ KEY CHANGE: Only ELIGIBLE SPUs from Step 7 are included in z-score calculation")
    print(f"   Z-score formula: UNCHANGED")
    print(f"   Thresholds: UNCHANGED (z > {Z_SCORE_THRESHOLD})")
    print(f"   Business logic: UNCHANGED")
    
    # Load allocation data
    print(f"\n📂 Loading allocation data: {allocation_data_file}")
    if not os.path.exists(allocation_data_file):
        raise FileNotFoundError(f"Allocation data not found: {allocation_data_file}")
    
    allocation_df = pd.read_csv(allocation_data_file, dtype={'str_code': str, 'spu_code': str})
    print(f"   Loaded {len(allocation_df):,} allocation records")
    
    # Load cluster assignments
    print(f"\n📂 Loading cluster assignments: {cluster_file}")
    if not os.path.exists(cluster_file):
        raise FileNotFoundError(f"Cluster file not found: {cluster_file}")
    
    cluster_df = pd.read_csv(cluster_file, dtype={'str_code': str})
    if 'Cluster' in cluster_df.columns and 'cluster_id' not in cluster_df.columns:
        cluster_df['cluster_id'] = cluster_df['Cluster']
    print(f"   Loaded {len(cluster_df):,} cluster assignments")
    
    # Merge cluster info
    allocation_df = allocation_df.merge(
        cluster_df[['str_code', 'cluster_id']],
        on='str_code',
        how='left'
    )
    
    # Load Step 7 eligibility
    eligibility_df = load_step7_eligibility(step7_eligibility_file)
    
    # Apply eligibility filtering
    eligible_df, excluded_df = filter_eligible_spus(allocation_df, eligibility_df)
    
    # Calculate z-scores on ELIGIBLE SPUs only
    if len(eligible_df) > 0:
        result_df = calculate_cluster_zscore(eligible_df)
    else:
        print("⚠️ No eligible SPUs found - returning empty result")
        result_df = pd.DataFrame()
    
    # Add excluded SPUs back with eligibility_filtered flag
    if len(excluded_df) > 0:
        excluded_df['z_score'] = np.nan
        excluded_df['is_imbalanced'] = False
        excluded_df['recommended_change'] = 0
        excluded_df['cluster_mean'] = np.nan
        excluded_df['cluster_std'] = np.nan
        excluded_df['cluster_count'] = 0
        excluded_df['eligibility_filtered'] = True
        
        if len(result_df) > 0:
            result_df['eligibility_filtered'] = False
            result_df = pd.concat([result_df, excluded_df], ignore_index=True)
        else:
            result_df = excluded_df
    
    # Save results
    print(f"\n💾 Saving enhanced results: {output_file}")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    result_df.to_csv(output_file, index=False)
    print(f"   Saved {len(result_df):,} records")
    
    # Summary
    print("\n" + "="*70)
    print("STEP 8 ENHANCEMENT COMPLETE")
    print("="*70)
    
    if len(result_df) > 0:
        eligible_analyzed = len(result_df[result_df['eligibility_filtered'] == False]) if 'eligibility_filtered' in result_df.columns else len(result_df)
        imbalanced = result_df['is_imbalanced'].sum() if 'is_imbalanced' in result_df.columns else 0
        actionable = (result_df['recommended_change'] != 0).sum() if 'recommended_change' in result_df.columns else 0
        
        print(f"\n📊 FINAL SUMMARY:")
        print(f"   Total SPU × Store combinations: {len(result_df):,}")
        print(f"   Eligible (analyzed for imbalance): {eligible_analyzed:,}")
        print(f"   Imbalanced detections: {imbalanced:,}")
        print(f"   Actionable recommendations: {actionable:,}")
    
    return result_df


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 8 Enhanced: Eligibility-Aware Imbalance Rule")
    parser.add_argument("--allocation-data", default="output/sample_run_202506A/step1_spu_sales.csv")
    parser.add_argument("--step7-eligibility", default="Evelyn/step7_step13/step7/enhanced_step7_results.csv")
    parser.add_argument("--cluster-file", default="output/sample_run_202506A/step6_clustering_results.csv")
    parser.add_argument("--output", default="Evelyn/step_7_to_step_13/step8/step8_eligibility_aware_results.csv")
    parser.add_argument("--period", default="202506A")
    args = parser.parse_args()
    
    run_eligibility_aware_step8(
        args.allocation_data,
        args.step7_eligibility,
        args.cluster_file,
        args.output,
        args.period
    )
