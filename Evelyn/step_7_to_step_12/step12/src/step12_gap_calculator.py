"""
Step 12 Performance Gap Calculator

AXIS A: Clear Performance Gap Definition

This module calculates performance gaps for Step 11-approved candidates ONLY.
It does NOT identify new opportunities - that's Step 11's responsibility.

Performance Gap Definition:
- Difference between store-level normalized sales metrics
- Compared against cluster-level peer benchmark (P75)
- Uses existing metrics only (no new client-unapproved KPIs)

Why This Gap Indicates Underperformance:
- Store sells less of this SPU than 75% of cluster peers
- Gap represents missed sales potential within similar stores
- Scaling is justified because Step 11 already validated growth potential

Author: Data Pipeline Team
Date: January 2026
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from step12_config import Step12Config, DEFAULT_CONFIG


@dataclass
class PerformanceGapResult:
    """Result of performance gap calculation for a single SPU-store pair."""
    store_code: str
    spu_code: str
    cluster_id: int
    
    # Gap metrics
    store_sales: float
    cluster_p75_sales: float
    cluster_median_sales: float
    cluster_mean_sales: float
    performance_gap: float  # P75 - store_sales
    gap_ratio: float        # gap / P75
    
    # Context
    cluster_size: int
    store_rank_in_cluster: int
    percentile_in_cluster: float
    
    # Explanation
    gap_explanation: str


def calculate_cluster_benchmarks(
    sales_df: pd.DataFrame,
    cluster_col: str = 'cluster_id',
    spu_col: str = 'spu_code',
    sales_col: str = 'current_spu_count',
    config: Step12Config = DEFAULT_CONFIG
) -> pd.DataFrame:
    """
    Calculate cluster-level benchmarks for each SPU.
    
    Args:
        sales_df: Sales data with cluster assignments
        cluster_col: Column name for cluster ID
        spu_col: Column name for SPU code
        sales_col: Column name for sales/quantity metric
        config: Step 12 configuration
    
    Returns:
        DataFrame with cluster benchmarks per SPU
    """
    print("\n📊 Calculating cluster benchmarks (Axis A)...")
    
    # Group by cluster and SPU to get benchmarks
    benchmarks = sales_df.groupby([cluster_col, spu_col]).agg({
        sales_col: ['mean', 'median', 'std', 'count',
                    lambda x: np.percentile(x, config.cluster_percentile_benchmark)]
    }).reset_index()
    
    # Flatten column names
    benchmarks.columns = [
        cluster_col, spu_col,
        'cluster_mean', 'cluster_median', 'cluster_std', 
        'cluster_size', 'cluster_p75'
    ]
    
    # Filter to clusters with sufficient size
    benchmarks = benchmarks[
        benchmarks['cluster_size'] >= config.min_cluster_size
    ].copy()
    
    print(f"   Calculated benchmarks for {len(benchmarks):,} cluster-SPU combinations")
    print(f"   Clusters with >= {config.min_cluster_size} stores: {benchmarks[cluster_col].nunique()}")
    
    return benchmarks


def calculate_performance_gaps(
    candidates_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    cluster_col: str = 'cluster_id',
    store_col: str = 'str_code',
    spu_col: str = 'spu_code',
    sales_col: str = 'current_spu_count',
    config: Step12Config = DEFAULT_CONFIG
) -> pd.DataFrame:
    """
    Calculate performance gaps for Step 11 candidates.
    
    CRITICAL: This function ONLY processes SPUs already in candidates_df.
    It does NOT identify new opportunities.
    
    Args:
        candidates_df: Step 11 approved candidates (REQUIRED)
        sales_df: Current sales data with cluster assignments
        cluster_col: Column name for cluster ID
        store_col: Column name for store code
        spu_col: Column name for SPU code
        sales_col: Column name for sales/quantity metric
        config: Step 12 configuration
    
    Returns:
        DataFrame with performance gaps for each candidate
    """
    print("\n📊 Calculating performance gaps for Step 11 candidates...")
    print(f"   Input candidates: {len(candidates_df):,}")
    
    if candidates_df.empty:
        print("   ⚠️ No Step 11 candidates provided - returning empty")
        return pd.DataFrame()
    
    # Calculate cluster benchmarks
    benchmarks = calculate_cluster_benchmarks(
        sales_df, cluster_col, spu_col, sales_col, config
    )
    
    # Merge candidates with current sales data
    # This ensures we only process Step 11 candidates
    candidates_with_sales = candidates_df.merge(
        sales_df[[store_col, spu_col, cluster_col, sales_col]].drop_duplicates(),
        on=[store_col, spu_col],
        how='left',
        suffixes=('', '_current')
    )
    
    # Use cluster_id from candidates if available
    if cluster_col not in candidates_with_sales.columns:
        if f'{cluster_col}_current' in candidates_with_sales.columns:
            candidates_with_sales[cluster_col] = candidates_with_sales[f'{cluster_col}_current']
    
    # Merge with benchmarks
    candidates_with_benchmarks = candidates_with_sales.merge(
        benchmarks,
        on=[cluster_col, spu_col],
        how='left'
    )
    
    # Calculate performance gaps
    # Gap = P75 benchmark - store's current sales
    # Positive gap = store is underperforming vs peers
    candidates_with_benchmarks['store_sales'] = candidates_with_benchmarks[sales_col].fillna(0)
    candidates_with_benchmarks['performance_gap'] = (
        candidates_with_benchmarks['cluster_p75'] - 
        candidates_with_benchmarks['store_sales']
    )
    
    # Calculate gap ratio (normalized gap)
    candidates_with_benchmarks['gap_ratio'] = np.where(
        candidates_with_benchmarks['cluster_p75'] > 0,
        candidates_with_benchmarks['performance_gap'] / candidates_with_benchmarks['cluster_p75'],
        0
    )
    
    # Calculate store's percentile within cluster
    def calc_percentile_rank(group):
        if len(group) < 2:
            return pd.Series([50.0] * len(group), index=group.index)
        return group['store_sales'].rank(pct=True) * 100
    
    candidates_with_benchmarks['percentile_in_cluster'] = (
        candidates_with_benchmarks.groupby([cluster_col, spu_col])
        .apply(calc_percentile_rank)
        .reset_index(level=[0, 1], drop=True)
    )
    
    # Generate gap explanation
    def generate_gap_explanation(row):
        if pd.isna(row['performance_gap']):
            return "No benchmark data available"
        
        gap = row['performance_gap']
        gap_ratio = row['gap_ratio']
        percentile = row.get('percentile_in_cluster', 50)
        
        if gap <= 0:
            return f"Store exceeds P75 benchmark (top {100-percentile:.0f}% performer)"
        elif gap_ratio < 0.1:
            return f"Minor gap ({gap_ratio:.1%}) - store near P75 benchmark"
        elif gap_ratio < 0.3:
            return f"Moderate gap ({gap_ratio:.1%}) - store at P{percentile:.0f}"
        else:
            return f"Significant gap ({gap_ratio:.1%}) - store at P{percentile:.0f}, scaling justified"
    
    candidates_with_benchmarks['gap_explanation'] = candidates_with_benchmarks.apply(
        generate_gap_explanation, axis=1
    )
    
    # Filter to candidates with meaningful gaps
    valid_gaps = candidates_with_benchmarks[
        (candidates_with_benchmarks['performance_gap'].notna()) &
        (candidates_with_benchmarks['gap_ratio'] >= config.min_gap_threshold)
    ].copy()
    
    print(f"   Candidates with valid benchmarks: {len(candidates_with_benchmarks):,}")
    print(f"   Candidates with gap >= {config.min_gap_threshold:.0%}: {len(valid_gaps):,}")
    
    # Summary statistics
    if not valid_gaps.empty:
        avg_gap = valid_gaps['performance_gap'].mean()
        avg_ratio = valid_gaps['gap_ratio'].mean()
        print(f"   Average performance gap: {avg_gap:.2f}")
        print(f"   Average gap ratio: {avg_ratio:.1%}")
    
    return valid_gaps
