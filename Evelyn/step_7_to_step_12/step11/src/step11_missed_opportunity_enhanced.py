"""
Step 11 Enhanced: Missed Sales Opportunity with 6 Improvement Axes

This module implements the repolished Step 11 with all 6 improvement axes:
- Axis A: Baseline Gate (Hard Eligibility Constraint)
- Axis B: Store Affinity Score (Soft Modifier)
- Axis C: Customer Mix Consistency Check (Confidence Penalty)
- Axis D: Weather/Seasonal Context (Rationale-Only)
- Axis E: Opportunity Tiering (Clear Confidence Buckets)
- Axis F: Suggestion-Only Safeguard (Decision Tree Lock)

Per Customer Requirement:
- Step 11 is SUGGESTION-ONLY and does NOT override Step 7-10 decisions
- Step 11 does NOT alter baseline inventory from Step 7-9
- Step 11 does NOT conflict with Step 10 overcapacity reductions
- All outputs are framed as "growth opportunities" or "exploratory upside"

CRITICAL: Core logic (top performer definition, quantity ratio logic,
opportunity identification mechanism) is PRESERVED - not modified.

Author: Data Pipeline Team
Date: January 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import json

import sys
STEP11_PATH = Path(__file__).parent
sys.path.insert(0, str(STEP11_PATH))

from step11_config import (
    Step11Config,
    DEFAULT_CONFIG,
    OpportunityTier,
    AffinityLevel,
    SUGGESTION_ONLY_STATEMENTS,
    validate_config_against_requirements,
)
from step11_baseline_gate import (
    load_step7_eligibility,
    load_step8_adjustments,
    load_step9_increases,
    load_step10_reductions,
    apply_baseline_gate,
)
from step11_affinity_scorer import apply_affinity_scoring
from step11_opportunity_tiering import apply_opportunity_tiering


def print_suggestion_only_safeguard():
    """
    Print Axis F: Suggestion-Only Safeguard statements.
    
    AXIS F: Decision Tree Lock - ensures Step 11 never violates client rules.
    """
    print("\n" + "="*70)
    print("🔒 AXIS F: SUGGESTION-ONLY SAFEGUARD")
    print("="*70)
    for statement in SUGGESTION_ONLY_STATEMENTS:
        print(f"   ✓ {statement}")
    print("="*70 + "\n")


def generate_opportunity_candidates(
    allocation_df: pd.DataFrame,
    cluster_df: pd.DataFrame,
    config: Step11Config = DEFAULT_CONFIG
) -> pd.DataFrame:
    """
    Generate opportunity candidates using ORIGINAL Step 11 logic.
    
    CRITICAL: This function preserves the original core logic:
    - Top performer definition (unchanged)
    - Quantity ratio logic (unchanged)
    - Opportunity identification mechanism (unchanged)
    
    Args:
        allocation_df: SPU allocation data
        cluster_df: Cluster assignments
        config: Step 11 configuration
    
    Returns:
        DataFrame of opportunity candidates
    """
    print("\n📊 Generating opportunity candidates (original logic preserved)...")
    
    # Merge cluster info
    df = allocation_df.merge(cluster_df, on='str_code', how='left')
    
    # Normalize cluster column
    if 'cluster' in df.columns and 'cluster_id' not in df.columns:
        df['cluster_id'] = df['cluster']
    if 'Cluster' in df.columns and 'cluster_id' not in df.columns:
        df['cluster_id'] = df['Cluster']
    
    # Calculate cluster sizes
    cluster_sizes = df.groupby('cluster_id')['str_code'].nunique().reset_index()
    cluster_sizes.columns = ['cluster_id', 'total_stores_in_cluster']
    
    # Filter valid clusters
    valid_clusters = cluster_sizes[
        cluster_sizes['total_stores_in_cluster'] >= config.min_cluster_stores
    ]['cluster_id'].tolist()
    
    df_valid = df[df['cluster_id'].isin(valid_clusters)].copy()
    print(f"   Valid clusters: {len(valid_clusters)}")
    
    # Calculate SPU performance within clusters (ORIGINAL LOGIC)
    spu_performance = df_valid.groupby(['cluster_id', 'spu_code']).agg({
        'current_spu_count': ['sum', 'mean'],
        'str_code': 'nunique',
    }).reset_index()
    spu_performance.columns = ['cluster_id', 'spu_code', 'total_qty', 'avg_qty', 'stores_selling']
    
    # Filter to SPUs sold by multiple stores (ORIGINAL LOGIC)
    spu_performance = spu_performance[
        spu_performance['stores_selling'] >= config.min_stores_selling
    ].copy()
    
    # Calculate percentile rank (ORIGINAL LOGIC)
    spu_performance['sales_percentile'] = spu_performance.groupby('cluster_id')['total_qty'].rank(pct=True)
    
    # Identify top performers (ORIGINAL LOGIC)
    top_performers = spu_performance[
        spu_performance['sales_percentile'] >= config.top_performer_threshold
    ].copy()
    
    # Merge cluster sizes
    top_performers = top_performers.merge(cluster_sizes, on='cluster_id', how='left')
    
    # Calculate adoption rate (ORIGINAL LOGIC)
    top_performers['adoption_rate'] = top_performers['stores_selling'] / top_performers['total_stores_in_cluster']
    
    print(f"   Top performers identified: {len(top_performers):,}")
    
    # Find stores missing top performers (ORIGINAL LOGIC)
    opportunities = []
    for _, top_row in top_performers.iterrows():
        cluster_id = top_row['cluster_id']
        spu_code = top_row['spu_code']
        
        # Get all stores in cluster
        cluster_stores = df_valid[df_valid['cluster_id'] == cluster_id]['str_code'].unique()
        
        # Get stores that have this SPU
        stores_with_spu = df_valid[
            (df_valid['cluster_id'] == cluster_id) & 
            (df_valid['spu_code'] == spu_code)
        ]['str_code'].unique()
        
        # Find missing stores
        missing_stores = set(cluster_stores) - set(stores_with_spu)
        
        for store in missing_stores:
            # Get store info
            store_info = df_valid[df_valid['str_code'] == store].iloc[0] if len(df_valid[df_valid['str_code'] == store]) > 0 else None
            
            opportunities.append({
                'str_code': store,
                'spu_code': spu_code,
                'cluster_id': cluster_id,
                'recommendation_type': 'ADD_NEW',
                'spu_avg_qty_per_store': top_row['avg_qty'],
                'spu_adoption_rate_in_cluster': top_row['adoption_rate'],
                'spu_sales_percentile': top_row['sales_percentile'],
                'stores_selling_in_cluster': top_row['stores_selling'],
                'total_stores_in_cluster': top_row['total_stores_in_cluster'],
                'recommended_quantity_change': top_row['avg_qty'],
                'opportunity_score': top_row['sales_percentile'] * top_row['adoption_rate'],
                'sub_cate_name': store_info['sub_cate_name'] if store_info is not None else '',
                'category_type': store_info.get('category_type', '') if store_info is not None else '',
            })
    
    opportunities_df = pd.DataFrame(opportunities)
    print(f"   Raw opportunities: {len(opportunities_df):,}")
    
    # Apply selectivity filters (ORIGINAL LOGIC)
    if not opportunities_df.empty:
        opportunities_df = opportunities_df[
            opportunities_df['spu_adoption_rate_in_cluster'] >= config.min_adoption_rate
        ].copy()
        print(f"   After adoption filter: {len(opportunities_df):,}")
        
        opportunities_df = opportunities_df[
            opportunities_df['opportunity_score'] >= config.min_opportunity_score
        ].copy()
        print(f"   After opportunity score filter: {len(opportunities_df):,}")
    
    return opportunities_df


def run_step11_enhanced(
    allocation_df: pd.DataFrame,
    cluster_df: pd.DataFrame,
    store_sales_df: Optional[pd.DataFrame] = None,
    step7_path: Optional[Path] = None,
    step8_path: Optional[Path] = None,
    step9_path: Optional[Path] = None,
    step10_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    period_label: str = "202506A",
    config: Step11Config = DEFAULT_CONFIG
) -> pd.DataFrame:
    """
    Run enhanced Step 11 with all 6 improvement axes.
    
    Args:
        allocation_df: SPU allocation data
        cluster_df: Cluster assignments
        store_sales_df: Store sales data with customer mix (optional)
        step7_path: Path to Step 7 output
        step8_path: Path to Step 8 output
        step9_path: Path to Step 9 output
        step10_path: Path to Step 10 output
        output_path: Path to save results
        period_label: Current period
        config: Step 11 configuration
    
    Returns:
        DataFrame with enhanced opportunities
    """
    print("\n" + "="*70)
    print("STEP 11 ENHANCED: MISSED SALES OPPORTUNITY")
    print("with 6 Improvement Axes (A-F)")
    print("="*70)
    print(f"Period: {period_label}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Axis F: Print suggestion-only safeguard
    print_suggestion_only_safeguard()
    
    # Validate configuration
    config_checks = validate_config_against_requirements()
    print("📋 Configuration validation:")
    for check, passed in config_checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
    
    # Generate opportunity candidates (ORIGINAL LOGIC PRESERVED)
    opportunities_df = generate_opportunity_candidates(allocation_df, cluster_df, config)
    
    if opportunities_df.empty:
        print("\n⚠️ No opportunities found")
        return pd.DataFrame()
    
    # Load Step 7-10 outputs for baseline gate
    step7_df = load_step7_eligibility(step7_path)
    step8_df = load_step8_adjustments(step8_path)
    step9_df = load_step9_increases(step9_path)
    step10_df = load_step10_reductions(step10_path)
    
    # Axis A: Apply baseline gate
    eligible_df, blocked_df, gate_summary = apply_baseline_gate(
        opportunities_df, step7_df, step8_df, step9_df, step10_df, config
    )
    
    if eligible_df.empty:
        print("\n⚠️ No opportunities passed baseline gate")
        return pd.DataFrame()
    
    # Axis B & C: Apply affinity scoring
    if store_sales_df is not None and not store_sales_df.empty:
        eligible_df = apply_affinity_scoring(eligible_df, store_sales_df, config)
    else:
        # Default affinity when no store sales data
        eligible_df['affinity_level'] = AffinityLevel.MODERATE.value
        eligible_df['affinity_score'] = 0.5
        eligible_df['consistency_penalty'] = 0.0
        eligible_df['affinity_explanation'] = "Store sales data not available"
        eligible_df['consistency_explanation'] = "No consistency check performed"
    
    # Axis D & E: Apply opportunity tiering
    eligible_df = apply_opportunity_tiering(eligible_df, period_label, config)
    
    # Add suggestion-only framing (Axis F)
    eligible_df['recommendation_framing'] = 'Growth Opportunity'
    eligible_df['is_mandatory'] = False
    eligible_df['step11_note'] = (
        "This is a SUGGESTION ONLY. Step 11 does not alter baseline inventory "
        "and does not conflict with Step 10 reductions."
    )
    
    # Sort by tier and score
    tier_order = {
        OpportunityTier.HIGH_CONFIDENCE.value: 0,
        OpportunityTier.MEDIUM_CONFIDENCE.value: 1,
        OpportunityTier.EXPLORATORY.value: 2,
    }
    eligible_df['tier_order'] = eligible_df['opportunity_tier'].map(tier_order)
    eligible_df = eligible_df.sort_values(
        ['tier_order', 'tier_score'], 
        ascending=[True, False]
    ).drop(columns=['tier_order'])
    
    # Summary
    print("\n" + "="*70)
    print("STEP 11 ENHANCED RESULTS")
    print("="*70)
    print(f"Total opportunities: {len(eligible_df):,}")
    print(f"Blocked by baseline gate: {len(blocked_df):,}")
    
    tier_counts = eligible_df['opportunity_tier'].value_counts()
    print("\nOpportunity Tiers:")
    for tier, count in tier_counts.items():
        print(f"   {tier}: {count:,}")
    
    # Save results
    if output_path:
        eligible_df.to_csv(output_path, index=False)
        print(f"\n💾 Saved: {output_path}")
        
        # Save blocked records
        blocked_path = output_path.parent / "step11_blocked_by_baseline_gate.csv"
        if not blocked_df.empty:
            blocked_df.to_csv(blocked_path, index=False)
            print(f"💾 Saved blocked: {blocked_path}")
    
    return eligible_df
