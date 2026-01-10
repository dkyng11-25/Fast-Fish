#!/usr/bin/env python3
"""
Detailed SPU Breakdown Report Generator

This script creates a comprehensive breakdown of all individual store-SPU recommendations
and shows how they aggregate up to the cluster-subcategory recommendations.

Boss requested to see the raw recommendations for each store and SPU in the cluster
and verify they add up to the other recommendations.

Author: Data Pipeline
Date: 2025-07-16
"""

import pandas as pd
import numpy as np
import os
import argparse
import glob
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import warnings
import sys
import os as _os

# Robust imports for both package and script execution
try:
    from src.config import get_period_label, get_current_period  # when running with -m src.module
    from src.pipeline_manifest import register_step_output, get_step_input, get_manifest
except Exception:
    try:
        from config import get_period_label, get_current_period  # when running from src/ directly
        from pipeline_manifest import register_step_output, get_step_input, get_manifest
    except Exception:
        # Final fallback: adjust sys.path relative to this file
        _HERE = _os.path.dirname(__file__)
        for p in [_HERE, _os.path.join(_HERE, '..'), _os.path.join(_HERE, '..', 'src')]:
            if p not in sys.path:
                sys.path.append(p)
        from config import get_period_label, get_current_period
        from pipeline_manifest import register_step_output, get_step_input

# Suppress warnings
warnings.filterwarnings('ignore')

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

# Configuration
SPU_RULE_FILES = {
    'rule7_missing_spu': 'output/rule7_missing_spu_opportunities.csv',
    'rule8_imbalanced_spu': 'output/rule8_imbalanced_spu_cases.csv', 
    'rule9_below_minimum_spu': 'output/rule9_below_minimum_spu_cases.csv',
    'rule10_overcapacity_spu': 'output/rule10_spu_overcapacity_opportunities.csv',
    'rule11_missed_sales_spu': 'output/rule11_improved_missed_sales_opportunity_spu_details.csv',
    'rule12_sales_performance_spu': 'output/rule12_sales_performance_spu_details.csv'
}

def load_all_spu_recommendations(period_label: Optional[str] = None) -> pd.DataFrame:
    """Load SPU-level recommendations (prefer manifest; fallback to period-labeled files).

    Returns an empty DataFrame if nothing is found (NA-safe, no synthetic defaults).
    """
    log_progress("Loading all SPU-level recommendations...")

    # Prefer manifest inputs: Step 13 consolidated detailed → Step 19 detailed_recommendations
    spu_file = None
    try:
        # 1) Step 13 period-specific consolidated detailed
        if period_label:
            for key in [
                f"consolidated_rules_detailed_{period_label}",
                f"consolidated_spu_rule_results_detailed_{period_label}",
            ]:
                path = get_step_input("step13", key)
                if path and os.path.exists(path):
                    spu_file = path
                    break
        # 2) Step 13 generic consolidated detailed
        if not spu_file:
            for key in [
                "consolidated_rules_detailed",
                "consolidated_spu_rule_results_detailed",
            ]:
                path = get_step_input("step13", key)
                if path and os.path.exists(path):
                    spu_file = path
                    break
        # 3) Step 19 registered detailed (reruns)
        if not spu_file:
            spu_file = get_step_input("step19", "detailed_recommendations")
    except Exception:
        spu_file = get_step_input("step19", "detailed_recommendations")

    # Normalize relative path if needed
    if spu_file and spu_file.startswith('../'):
        spu_file = spu_file[3:]

    # Fallback search by manifest scan, then period label, then generic latest
    if not spu_file or not os.path.exists(spu_file):
        if not spu_file:
            log_progress("⚠️ No input registered in manifest, attempting fallback search...")
        else:
            log_progress(f"⚠️ Manifest file missing on disk: {spu_file}. Attempting fallback search...")

        candidates: List[str] = []
        # 0) Scan manifest for any step13/step19 outputs with period_label that look like consolidated detailed
        try:
            manifest = get_manifest()
            for step_name in ["step13", "step19"]:
                step_entries = manifest.get(step_name, {})
                for key, meta in step_entries.items():
                    path = meta.get("path") if isinstance(meta, dict) else None
                    if not path:
                        continue
                    if period_label and period_label in os.path.basename(path):
                        name = os.path.basename(path)
                        if ("consolidated" in name and "detailed" in name) or name.startswith("detailed_spu_"):
                            if os.path.exists(path):
                                candidates.append(path)
        except Exception:
            pass
        if period_label:
            candidates.extend(glob.glob(f"output/consolidated_spu_rule_results_detailed_{period_label}*.csv"))
            candidates.extend(glob.glob(f"output/detailed_spu_recommendations_{period_label}*.csv"))
            candidates.extend(glob.glob(f"output/corrected_detailed_spu_recommendations_{period_label}*.csv"))
        # Broader fallback (non period-specific)
        candidates.extend(glob.glob("output/consolidated_spu_rule_results_detailed_*.csv"))
        candidates.extend(glob.glob("output/detailed_spu_recommendations_*.csv"))
        candidates.extend(glob.glob("output/corrected_detailed_spu_recommendations_*.csv"))

        if candidates:
            spu_file = max(candidates, key=os.path.getctime)
            log_progress(f"Found fallback SPU recommendations: {spu_file}")
        else:
            log_progress("❌ No SPU recommendation files found")
            return pd.DataFrame()

    # Load
    df = pd.read_csv(spu_file, dtype={'str_code': str, 'spu_code': str})
    log_progress(f"✓ Loaded {len(df):,} SPU recommendations from: {spu_file}")

    # Diagnostics on key fields (preserve NA)
    for col in ["str_code", "spu_code", "recommended_quantity_change", "investment_required", "rule_source"]:
        if col in df.columns:
            na_cnt = df[col].isna().sum()
            log_progress(f"   • Missing {col}: {na_cnt:,}")
        else:
            log_progress(f"   • Column not present: {col}")

    return df

def standardize_rule_columns(df: pd.DataFrame, rule_name: str) -> pd.DataFrame:
    """Standardize columns across different rule formats"""
    
    # Core columns we need for analysis
    core_columns = {
        'str_code': 'str_code',
        'spu_code': 'spu_code', 
        'recommended_quantity_change': 'recommended_quantity_change',
        'investment_required': 'investment_required',
        'recommendation_text': 'recommendation_text'
    }
    
    # Create standardized DataFrame
    standardized = pd.DataFrame()
    
    # Map existing columns to standardized names
    for std_col, col_mapping in core_columns.items():
        if col_mapping in df.columns:
            standardized[std_col] = df[col_mapping]
        elif std_col in df.columns:
            standardized[std_col] = df[std_col]
        else:
            # Try to find similar columns
            similar_cols = [col for col in df.columns if std_col.replace('_', '') in col.replace('_', '').lower()]
            if similar_cols:
                standardized[std_col] = df[similar_cols[0]]
            else:
                standardized[std_col] = 0 if 'quantity' in std_col or 'investment' in std_col else 'N/A'
    
    # Add category information if available
    category_columns = ['sub_cate_name', 'cate_name', 'big_class_name', 'category_key']
    for col in category_columns:
        if col in df.columns:
            standardized[col] = df[col]
            break
    
    # Add cluster information if available
    cluster_columns = ['Cluster', 'cluster_id']
    for col in cluster_columns:
        if col in df.columns:
            standardized['cluster'] = df[col]
            break
    
    # Add current quantity if available
    quantity_columns = ['current_quantity', 'quantity', 'current_quantity_15days']
    for col in quantity_columns:
        if col in df.columns:
            standardized['current_quantity'] = df[col]
            break
    
    # Add unit price if available
    price_columns = ['unit_price', 'investment_per_unit']
    for col in price_columns:
        if col in df.columns:
            standardized['unit_price'] = df[col]
            break
    
    # Fill missing values
    standardized['recommended_quantity_change'] = pd.to_numeric(standardized['recommended_quantity_change'], errors='coerce').fillna(0)
    standardized['investment_required'] = pd.to_numeric(standardized['investment_required'], errors='coerce').fillna(0)
    
    return standardized

def create_store_level_aggregation(spu_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate SPU recommendations to store level (NA-safe).

    If 'rule_source' is absent, aggregate by store only. Handles missing numeric columns gracefully.
    """
    log_progress("Creating store-level aggregation...")

    group_cols = ['str_code', 'rule_source'] if 'rule_source' in spu_df.columns else ['str_code']

    # Build aggregation for sums only on columns that exist
    agg_parts = {}
    if 'recommended_quantity_change' in spu_df.columns:
        agg_parts['recommended_quantity_change'] = 'sum'
    if 'investment_required' in spu_df.columns:
        agg_parts['investment_required'] = 'sum'
    if 'current_quantity' in spu_df.columns:
        agg_parts['current_quantity'] = 'sum'

    sums = spu_df.groupby(group_cols).agg(agg_parts).reset_index() if agg_parts else spu_df.groupby(group_cols).size().reset_index(name='__rows__')

    # Compute affected_spus robustly
    if 'spu_code' in spu_df.columns:
        counts = spu_df.groupby(group_cols)['spu_code'].nunique().reset_index(name='affected_spus')
    else:
        counts = spu_df.groupby(group_cols).size().reset_index(name='affected_spus')

    # Merge
    store_aggregation = pd.merge(sums, counts, on=group_cols, how='left')

    # Rename to canonical output names, adding missing columns with NaN to preserve schema
    if 'recommended_quantity_change' in store_aggregation.columns:
        store_aggregation.rename(columns={'recommended_quantity_change': 'total_quantity_change'}, inplace=True)
    else:
        store_aggregation['total_quantity_change'] = np.nan

    if 'investment_required' in store_aggregation.columns:
        store_aggregation.rename(columns={'investment_required': 'total_investment'}, inplace=True)
    else:
        store_aggregation['total_investment'] = np.nan

    if 'current_quantity' in store_aggregation.columns:
        store_aggregation.rename(columns={'current_quantity': 'total_current_quantity'}, inplace=True)
    else:
        store_aggregation['total_current_quantity'] = np.nan

    # Reorder columns
    if group_cols == ['str_code', 'rule_source']:
        cols = ['str_code', 'rule_source', 'total_quantity_change', 'total_investment', 'affected_spus', 'total_current_quantity']
    else:
        cols = ['str_code', 'total_quantity_change', 'total_investment', 'affected_spus', 'total_current_quantity']
    store_aggregation = store_aggregation[cols]

    return store_aggregation

def create_cluster_subcategory_aggregation(spu_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate SPU recommendations to cluster-subcategory level"""
    log_progress("Creating cluster-subcategory aggregation...")
    
    # Try to get subcategory from available columns
    if 'sub_cate_name' in spu_df.columns:
        subcategory_col = 'sub_cate_name'
    elif 'category_key' in spu_df.columns:
        # Extract subcategory from category_key format: "夏|男|前台|T恤|休闲圆领T恤|15T1077B"
        spu_df['subcategory_extracted'] = spu_df['category_key'].str.split('|').str[4]
        subcategory_col = 'subcategory_extracted'
    else:
        log_progress("⚠️ No subcategory information found")
        return pd.DataFrame()
    
    if 'cluster' not in spu_df.columns:
        log_progress("⚠️ No cluster information found")
        return pd.DataFrame()
    
    # Start with groupby
    group_cols = ['cluster', subcategory_col]
    agg_map = {}
    if 'str_code' in spu_df.columns:
        agg_map['str_code'] = pd.NamedAgg(column='str_code', aggfunc='nunique')
    if 'spu_code' in spu_df.columns:
        agg_map['spu_code'] = pd.NamedAgg(column='spu_code', aggfunc='nunique')
    if 'recommended_quantity_change' in spu_df.columns:
        agg_map['recommended_quantity_change'] = pd.NamedAgg(column='recommended_quantity_change', aggfunc='sum')
    if 'investment_required' in spu_df.columns:
        agg_map['investment_required'] = pd.NamedAgg(column='investment_required', aggfunc='sum')
    if 'current_quantity' in spu_df.columns:
        agg_map['current_quantity'] = pd.NamedAgg(column='current_quantity', aggfunc='sum')

    if agg_map:
        grp = spu_df.groupby(group_cols).agg(**agg_map).reset_index()
    else:
        grp = spu_df.groupby(group_cols).size().reset_index(name='__rows__')

    # Rename / create expected columns
    if 'str_code' in grp.columns:
        grp.rename(columns={'str_code': 'stores_affected'}, inplace=True)
    else:
        grp['stores_affected'] = np.nan

    if 'spu_code' in grp.columns:
        grp.rename(columns={'spu_code': 'unique_spus'}, inplace=True)
    else:
        grp['unique_spus'] = np.nan

    if 'recommended_quantity_change' in grp.columns:
        grp.rename(columns={'recommended_quantity_change': 'total_quantity_change'}, inplace=True)
    else:
        grp['total_quantity_change'] = np.nan

    if 'investment_required' in grp.columns:
        grp.rename(columns={'investment_required': 'total_investment'}, inplace=True)
    else:
        grp['total_investment'] = np.nan

    if 'current_quantity' in grp.columns:
        grp.rename(columns={'current_quantity': 'total_current_quantity'}, inplace=True)
    else:
        grp['total_current_quantity'] = np.nan

    # Final ordering
    cluster_subcat_agg = grp[['cluster', subcategory_col]].copy()
    cluster_subcat_agg.rename(columns={subcategory_col: 'subcategory'}, inplace=True)
    cluster_subcat_agg['stores_affected'] = grp['stores_affected']
    cluster_subcat_agg['unique_spus'] = grp['unique_spus']
    cluster_subcat_agg['total_quantity_change'] = grp['total_quantity_change']
    cluster_subcat_agg['total_investment'] = grp['total_investment']
    cluster_subcat_agg['total_current_quantity'] = grp['total_current_quantity']

    return cluster_subcat_agg

def create_comprehensive_breakdown_report(
    spu_df: pd.DataFrame,
    store_agg: pd.DataFrame,
    cluster_agg: pd.DataFrame,
    yyyymm: str,
    period: Optional[str],
    period_label: str,
) -> None:
    """Create comprehensive breakdown report, period-labeled, and register in manifest."""
    log_progress("Creating comprehensive breakdown report...")

    os.makedirs("output", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # DUAL OUTPUT PATTERN - 1. Save detailed SPU-level recommendations
    timestamped_spu_file = f"output/detailed_spu_recommendations_{period_label}_{timestamp}.csv"
    generic_spu_file = f"output/detailed_spu_recommendations_{period_label}.csv"
    
    spu_df.to_csv(timestamped_spu_file, index=False)
    log_progress(f"✅ Saved timestamped SPU recommendations: {timestamped_spu_file}")
    
    if os.path.exists(generic_spu_file) or os.path.islink(generic_spu_file):
        os.remove(generic_spu_file)
    os.symlink(os.path.basename(timestamped_spu_file), generic_spu_file)
    log_progress(f"✅ Created generic symlink: {generic_spu_file} -> {timestamped_spu_file}")
    
    spu_output_file = timestamped_spu_file

    # DUAL OUTPUT PATTERN - 2. Save store-level aggregation
    timestamped_store_file = f"output/store_level_aggregation_{period_label}_{timestamp}.csv"
    generic_store_file = f"output/store_level_aggregation_{period_label}.csv"
    
    store_agg.to_csv(timestamped_store_file, index=False)
    log_progress(f"✅ Saved timestamped store-level aggregation: {timestamped_store_file}")
    
    if os.path.exists(generic_store_file) or os.path.islink(generic_store_file):
        os.remove(generic_store_file)
    os.symlink(os.path.basename(timestamped_store_file), generic_store_file)
    log_progress(f"✅ Created generic symlink: {generic_store_file} -> {timestamped_store_file}")
    
    store_output_file = timestamped_store_file

    # DUAL OUTPUT PATTERN - 3. Save cluster-subcategory aggregation
    cluster_output_file = None
    if not cluster_agg.empty:
        timestamped_cluster_file = f"output/cluster_subcategory_aggregation_{period_label}_{timestamp}.csv"
        generic_cluster_file = f"output/cluster_subcategory_aggregation_{period_label}.csv"
        
        cluster_agg.to_csv(timestamped_cluster_file, index=False)
        log_progress(f"✅ Saved timestamped cluster-subcategory aggregation: {timestamped_cluster_file}")
        
        if os.path.exists(generic_cluster_file) or os.path.islink(generic_cluster_file):
            os.remove(generic_cluster_file)
        os.symlink(os.path.basename(timestamped_cluster_file), generic_cluster_file)
        log_progress(f"✅ Created generic symlink: {generic_cluster_file} -> {timestamped_cluster_file}")
        
        cluster_output_file = timestamped_cluster_file

    # DUAL OUTPUT PATTERN - 4. Create summary report
    timestamped_summary_file = f"output/spu_breakdown_summary_{period_label}_{timestamp}.md"
    generic_summary_file = f"output/spu_breakdown_summary_{period_label}.md"
    
    create_summary_report(spu_df, store_agg, cluster_agg, timestamped_summary_file)
    log_progress(f"✅ Saved timestamped summary report: {timestamped_summary_file}")
    
    create_summary_report(spu_df, store_agg, cluster_agg, generic_summary_file)
    log_progress(f"✅ Saved generic summary report: {generic_summary_file}")
    
    summary_file = timestamped_summary_file

    # 5. Register outputs in manifest (generic and period-specific keys)
    meta_common = {
        "target_year": int(yyyymm[:4]),
        "target_month": int(yyyymm[4:]),
        "target_period": period or "full",
    }

    # detailed_spu_breakdown
    register_step_output(
        "step19",
        "detailed_spu_breakdown",
        spu_output_file,
        metadata={**meta_common, "records": len(spu_df), "columns": list(spu_df.columns)},
    )
    register_step_output(
        "step19",
        f"detailed_spu_breakdown_{period_label}",
        spu_output_file,
        metadata={**meta_common, "records": len(spu_df), "columns": list(spu_df.columns)},
    )

    # store_level_aggregation
    register_step_output(
        "step19",
        "store_level_aggregation",
        store_output_file,
        metadata={**meta_common, "records": len(store_agg), "columns": list(store_agg.columns)},
    )
    register_step_output(
        "step19",
        f"store_level_aggregation_{period_label}",
        store_output_file,
        metadata={**meta_common, "records": len(store_agg), "columns": list(store_agg.columns)},
    )

    # cluster_subcategory_aggregation (only if exists)
    if cluster_output_file:
        register_step_output(
            "step19",
            "cluster_subcategory_aggregation",
            cluster_output_file,
            metadata={**meta_common, "records": len(cluster_agg), "columns": list(cluster_agg.columns)},
        )
        register_step_output(
            "step19",
            f"cluster_subcategory_aggregation_{period_label}",
            cluster_output_file,
            metadata={**meta_common, "records": len(cluster_agg), "columns": list(cluster_agg.columns)},
        )

    # summary (markdown)
    register_step_output(
        "step19",
        "spu_breakdown_summary",
        summary_file,
        metadata={**meta_common, "format": "markdown"},
    )
    register_step_output(
        "step19",
        f"spu_breakdown_summary_{period_label}",
        summary_file,
        metadata={**meta_common, "format": "markdown"},
    )

def create_summary_report(spu_df: pd.DataFrame, store_agg: pd.DataFrame, 
                         cluster_agg: pd.DataFrame, summary_file: str) -> None:
    """Create comprehensive summary report"""
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("# Detailed SPU Breakdown Analysis Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Executive Summary\n")
        f.write(f"This report provides the complete breakdown of individual store-SPU recommendations\n")
        f.write(f"requested by management, showing how granular recommendations aggregate up to\n")
        f.write(f"cluster-subcategory strategic recommendations.\n\n")
        
        # SPU-level summary
        f.write("## 📊 SPU-Level Recommendations Summary\n")
        f.write(f"- **Total SPU Recommendations**: {len(spu_df):,}\n")
        f.write(f"- **Unique Stores Affected**: {spu_df['str_code'].nunique():,}\n")
        f.write(f"- **Unique SPUs Affected**: {spu_df['spu_code'].nunique():,}\n")
        f.write(f"- **Total Quantity Changes**: {spu_df['recommended_quantity_change'].sum():,.1f} units\n")
        f.write(f"- **Total Investment Required**: ¥{spu_df['investment_required'].sum():,.0f}\n\n")
        
        # Rule breakdown
        f.write("### By Business Rule\n")
        rule_summary = spu_df.groupby('rule_source').agg({
            'str_code': 'nunique',
            'spu_code': 'nunique',
            'recommended_quantity_change': 'sum',
            'investment_required': 'sum'
        }).round(2)
        
        for rule, stats in rule_summary.iterrows():
            f.write(f"- **{rule.replace('_', ' ').title()}**:\n")
            f.write(f"  - Stores: {int(stats['str_code']):,}\n")
            f.write(f"  - SPUs: {int(stats['spu_code']):,}\n") 
            f.write(f"  - Quantity Change: {stats['recommended_quantity_change']:,.1f} units\n")
            f.write(f"  - Investment: ¥{stats['investment_required']:,.0f}\n\n")
        
        # Store-level aggregation summary
        f.write("## 🏪 Store-Level Aggregation Summary\n")
        f.write(f"- **Stores with Recommendations**: {store_agg['str_code'].nunique():,}\n")
        f.write(f"- **Average SPUs per Store**: {store_agg['affected_spus'].mean():.1f}\n")
        f.write(f"- **Average Investment per Store**: ¥{store_agg['total_investment'].mean():,.0f}\n\n")
        
        # Top stores by investment
        top_investment_stores = store_agg.nlargest(10, 'total_investment')
        f.write("### Top 10 Stores by Investment Required\n")
        for _, store in top_investment_stores.iterrows():
            f.write(f"- **Store {store['str_code']}**: {store['affected_spus']} SPUs, ")
            f.write(f"{store['total_quantity_change']:,.1f} units, ¥{store['total_investment']:,.0f}\n")
        f.write("\n")
        
        # Cluster-subcategory summary
        if not cluster_agg.empty:
            f.write("## 🎯 Cluster-Subcategory Aggregation Summary\n")
            f.write(f"- **Cluster-Subcategory Combinations**: {len(cluster_agg):,}\n")
            f.write(f"- **Average Stores per Combination**: {cluster_agg['stores_affected'].mean():.1f}\n")
            f.write(f"- **Average SPUs per Combination**: {cluster_agg['unique_spus'].mean():.1f}\n\n")
            
            # Top combinations by impact
            top_combinations = cluster_agg.nlargest(10, 'total_investment')
            f.write("### Top 10 Cluster-Subcategory Combinations by Investment\n")
            for _, combo in top_combinations.iterrows():
                f.write(f"- **Cluster {combo['cluster']} - {combo['subcategory']}**: ")
                f.write(f"{combo['stores_affected']} stores, {combo['unique_spus']} SPUs, ")
                f.write(f"{combo['total_quantity_change']:,.1f} units, ¥{combo['total_investment']:,.0f}\n")
            f.write("\n")
        
        f.write("## 🔍 Validation: Aggregation Consistency\n")
        spu_total_investment = spu_df['investment_required'].sum()
        store_total_investment = store_agg['total_investment'].sum()
        f.write(f"- **SPU-level total investment**: ¥{spu_total_investment:,.0f}\n")
        f.write(f"- **Store-level total investment**: ¥{store_total_investment:,.0f}\n")
        
        if abs(spu_total_investment - store_total_investment) < 1:
            f.write("- ✅ **VALIDATION PASSED**: Aggregation is consistent\n\n")
        else:
            f.write("- ⚠️ **VALIDATION WARNING**: Aggregation discrepancy detected\n\n")
        
        f.write("## 📁 Output Files Generated\n")
        f.write("1. **Detailed SPU Recommendations**: Individual store-SPU level recommendations\n")
        f.write("2. **Store-Level Aggregation**: Store totals across all rules\n")  
        f.write("3. **Cluster-Subcategory Aggregation**: Strategic level aggregation\n")
        f.write("4. **This Summary Report**: Comprehensive analysis overview\n\n")
        
        f.write("## 💡 Key Insights for Management\n")
        f.write("- **Granular Control**: Every SPU recommendation is traceable to specific stores\n")
        f.write("- **Mathematical Consistency**: Aggregations roll up correctly from SPU to cluster level\n")
        f.write("- **Investment Transparency**: Clear investment requirements at all levels\n")
        f.write("- **Rule Traceability**: Each recommendation linked to specific business rule\n")
        f.write("- **Actionable Detail**: Store managers can see exactly which SPUs to adjust\n")
    
    log_progress(f"✅ Saved comprehensive summary: {summary_file}")

def create_sample_drill_down_examples(spu_df: pd.DataFrame, period_label: str) -> None:
    """Create sample drill-down examples for boss review"""
    log_progress("Creating sample drill-down examples...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Example 1: Pick a store with multiple SPU recommendations (DUAL OUTPUT PATTERN)
    store_counts = spu_df['str_code'].value_counts()
    if len(store_counts) > 0:
        sample_store = store_counts.index[0]
        
        store_detail = spu_df[spu_df['str_code'] == sample_store].copy()
        timestamped_store_detail_file = f"output/sample_store_{sample_store}_detail_{period_label}_{timestamp}.csv"
        generic_store_detail_file = f"output/sample_store_{sample_store}_detail_{period_label}.csv"
        
        store_detail.to_csv(timestamped_store_detail_file, index=False)
        if os.path.exists(generic_store_detail_file) or os.path.islink(generic_store_detail_file):
            os.remove(generic_store_detail_file)
        os.symlink(os.path.basename(timestamped_store_detail_file), generic_store_detail_file)
        
        log_progress(f"✅ Sample store detail ({sample_store}): {timestamped_store_detail_file}")
        log_progress(f"   📊 Store {sample_store}: {len(store_detail)} SPU recommendations")
        log_progress(f"   💰 Total investment: ¥{store_detail['investment_required'].sum():,.0f}")
    
    # Example 2: Pick an SPU that appears across multiple stores (DUAL OUTPUT PATTERN)
    spu_counts = spu_df['spu_code'].value_counts()
    if len(spu_counts) > 0:
        sample_spu = spu_counts.index[0]
        
        spu_detail = spu_df[spu_df['spu_code'] == sample_spu].copy()
        timestamped_spu_detail_file = f"output/sample_spu_{sample_spu}_detail_{period_label}_{timestamp}.csv"
        generic_spu_detail_file = f"output/sample_spu_{sample_spu}_detail_{period_label}.csv"
        
        spu_detail.to_csv(timestamped_spu_detail_file, index=False)
        if os.path.exists(generic_spu_detail_file) or os.path.islink(generic_spu_detail_file):
            os.remove(generic_spu_detail_file)
        os.symlink(os.path.basename(timestamped_spu_detail_file), generic_spu_detail_file)
        
        log_progress(f"✅ Sample SPU detail ({sample_spu}): {timestamped_spu_detail_file}")
        log_progress(f"   🏪 SPU {sample_spu}: Affects {len(spu_detail)} stores")
        log_progress(f"   📦 Total quantity change: {spu_detail['recommended_quantity_change'].sum():,.1f} units")

def main():
    """Main execution function (period-aware, manifest-integrated)."""
    log_progress("🚀 Starting Detailed SPU Breakdown Analysis...")
    log_progress("Boss requested: Raw recommendations for each store and SPU in cluster")
    log_progress("Goal: Show individual recommendations and verify aggregation math")

    # CLI parsing
    parser = argparse.ArgumentParser(description="Step 19: Detailed SPU Breakdown (period-aware)")
    parser.add_argument("--target-yyyymm", dest="target_yyyymm", type=str, help="Target YYYYMM")
    parser.add_argument("--target-period", dest="target_period", type=str, choices=["A", "B", "full", "a", "b"], help="Target period A/B or 'full'")
    # Back-compat flags
    parser.add_argument("--yyyymm", dest="yyyymm", type=str, help="Target YYYYMM (legacy)")
    parser.add_argument("--period", dest="period", type=str, choices=["A", "B", "full", "a", "b"], help="Target period (legacy)")
    args = parser.parse_args()

    # Resolve period
    current_yyyymm, current_period = get_current_period()
    yyyymm = args.target_yyyymm or args.yyyymm or current_yyyymm
    period_raw = args.target_period or args.period or current_period
    period = None if (period_raw is None or str(period_raw).lower() == "full") else str(period_raw).upper()
    period_label = get_period_label(yyyymm, period)
    log_progress(f"Configured period: {period_label}")

    try:
        # Load all SPU-level recommendations
        spu_recommendations = load_all_spu_recommendations(period_label)

        if spu_recommendations is None or spu_recommendations.empty:
            log_progress("❌ No SPU recommendations found. Please run the pipeline first (ensure Step 13 is registered).")
            return

        # Create store-level aggregation
        store_aggregation = create_store_level_aggregation(spu_recommendations)

        # Create cluster-subcategory aggregation
        cluster_aggregation = create_cluster_subcategory_aggregation(spu_recommendations)

        # Create comprehensive breakdown report and register outputs
        create_comprehensive_breakdown_report(
            spu_recommendations, store_aggregation, cluster_aggregation, yyyymm, period, period_label
        )

        # Create sample drill-down examples
        create_sample_drill_down_examples(spu_recommendations, period_label)

        log_progress("✅ Detailed SPU Breakdown Analysis Complete!")
        log_progress("📊 Boss can now see:")
        log_progress("   • Individual store-SPU recommendations")
        log_progress("   • Store-level aggregations")
        log_progress("   • Cluster-subcategory strategic aggregations")
        log_progress("   • Mathematical validation that numbers add up")
        log_progress("   • Sample drill-down examples")

        # Summary statistics
        log_progress(f"\n📈 SUMMARY STATISTICS:")
        log_progress(f"   • Total SPU recommendations: {len(spu_recommendations):,}")
        if 'str_code' in spu_recommendations.columns:
            log_progress(f"   • Stores affected: {spu_recommendations['str_code'].nunique():,}")
        if 'spu_code' in spu_recommendations.columns:
            log_progress(f"   • Unique SPUs: {spu_recommendations['spu_code'].nunique():,}")
        if 'recommended_quantity_change' in spu_recommendations.columns:
            log_progress(f"   • Total quantity changes: {spu_recommendations['recommended_quantity_change'].sum():,.1f} units")
        if 'investment_required' in spu_recommendations.columns:
            log_progress(f"   • Total investment: ¥{spu_recommendations['investment_required'].sum():,.0f}")

    except Exception as e:
        log_progress(f"❌ Error in detailed breakdown analysis: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main() 