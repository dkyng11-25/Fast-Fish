#!/usr/bin/env python3
"""
Aggregation Discrepancy Investigation

This script investigates why the cluster-subcategory aggregation totals
don't match the store-level totals, helping identify the root cause.

Author: Data Pipeline
Date: 2025-07-16
"""

import pandas as pd
import numpy as np
from datetime import datetime

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def investigate_discrepancy():
    """Investigate the aggregation discrepancy"""
    log_progress("🔍 Investigating aggregation discrepancy...")
    
    # Load the data files
    try:
        detailed_spu = pd.read_csv("output/detailed_spu_recommendations_20250716_174036.csv", dtype={'str_code': str})
        store_agg = pd.read_csv("output/store_level_aggregation_20250716_174036.csv", dtype={'str_code': str})
        cluster_agg = pd.read_csv("output/cluster_subcategory_aggregation_20250716_174036.csv")
        clustering = pd.read_csv("output/clustering_results_spu.csv", dtype={'str_code': str})
        
        log_progress(f"✓ Loaded all data files")
    except Exception as e:
        log_progress(f"❌ Error loading files: {e}")
        return
    
    # Check the totals
    spu_total_qty = detailed_spu['recommended_quantity_change'].sum()
    spu_total_inv = detailed_spu['investment_required'].sum()
    
    store_total_qty = store_agg['total_quantity_change'].sum()
    store_total_inv = store_agg['total_investment'].sum()
    
    cluster_total_qty = cluster_agg['total_quantity_change'].sum()
    cluster_total_inv = cluster_agg['total_investment'].sum()
    
    log_progress(f"\n📊 TOTALS COMPARISON:")
    log_progress(f"SPU Level:     {spu_total_qty:10.1f} units | ¥{spu_total_inv:12,.0f}")
    log_progress(f"Store Level:   {store_total_qty:10.1f} units | ¥{store_total_inv:12,.0f}")
    log_progress(f"Cluster Level: {cluster_total_qty:10.1f} units | ¥{cluster_total_inv:12,.0f}")
    log_progress(f"Difference:    {cluster_total_qty - store_total_qty:10.1f} units | ¥{cluster_total_inv - store_total_inv:12,.0f}")
    
    # Check how the cluster aggregation was created
    log_progress(f"\n🔍 CLUSTER AGGREGATION STRUCTURE:")
    log_progress(f"Cluster aggregation columns: {list(cluster_agg.columns)}")
    log_progress(f"Sample cluster aggregation records:")
    print(cluster_agg.head())
    
    # Check if there's subcategory information in the detailed SPU data
    log_progress(f"\n🔍 SPU DATA STRUCTURE:")
    log_progress(f"Detailed SPU columns: {list(detailed_spu.columns)}")
    print(detailed_spu[['str_code', 'spu_code', 'sub_cate_name', 'recommended_quantity_change', 'rule_source']].head())
    
    # Check for missing subcategory information
    missing_subcat = detailed_spu['sub_cate_name'].isna().sum()
    log_progress(f"Records with missing subcategory: {missing_subcat:,} ({missing_subcat/len(detailed_spu)*100:.1f}%)")
    
    # Manually recalculate cluster-subcategory aggregation from SPU data
    log_progress(f"\n🔧 MANUAL RECALCULATION:")
    
    # Add cluster information to SPU data
    spu_with_cluster = detailed_spu.merge(clustering[['str_code', 'Cluster']], on='str_code', how='left')
    
    # Check for missing cluster assignments
    missing_cluster = spu_with_cluster['Cluster'].isna().sum()
    log_progress(f"SPU records with missing cluster: {missing_cluster:,}")
    
    if missing_cluster > 0:
        log_progress("⚠️ Some SPU records don't have cluster assignments!")
        missing_stores = spu_with_cluster[spu_with_cluster['Cluster'].isna()]['str_code'].unique()
        log_progress(f"Stores missing cluster: {missing_stores[:10]}...")  # Show first 10
    
    # Group by cluster and subcategory
    manual_cluster_agg = spu_with_cluster.groupby(['Cluster', 'sub_cate_name']).agg({
        'str_code': 'nunique',
        'spu_code': 'nunique',
        'recommended_quantity_change': 'sum',
        'investment_required': 'sum'
    }).reset_index()
    
    manual_cluster_agg.columns = ['cluster', 'subcategory', 'stores_affected', 'unique_spus', 
                                 'total_quantity_change', 'total_investment']
    
    # Compare manual calculation with existing cluster aggregation
    manual_total_qty = manual_cluster_agg['total_quantity_change'].sum()
    manual_total_inv = manual_cluster_agg['total_investment'].sum()
    
    log_progress(f"Manual calculation: {manual_total_qty:10.1f} units | ¥{manual_total_inv:12,.0f}")
    log_progress(f"Original cluster:   {cluster_total_qty:10.1f} units | ¥{cluster_total_inv:12,.0f}")
    log_progress(f"Difference:         {manual_total_qty - cluster_total_qty:10.1f} units | ¥{manual_total_inv - cluster_total_inv:12,.0f}")
    
    # Check if the issue is in the cluster aggregation method
    log_progress(f"\n🔍 CLUSTER AGGREGATION METHOD ANALYSIS:")
    log_progress(f"Original cluster agg has {len(cluster_agg)} records")
    log_progress(f"Manual cluster agg has {len(manual_cluster_agg)} records")
    
    # Look for records that might be duplicated or missing
    if len(cluster_agg) != len(manual_cluster_agg):
        log_progress("⚠️ Different number of cluster-subcategory combinations!")
        
        # Check unique cluster-subcategory combinations
        original_combos = set(zip(cluster_agg['cluster'], cluster_agg['subcategory']))
        manual_combos = set(zip(manual_cluster_agg['cluster'], manual_cluster_agg['subcategory']))
        
        only_in_original = original_combos - manual_combos
        only_in_manual = manual_combos - original_combos
        
        if only_in_original:
            log_progress(f"Combinations only in original: {len(only_in_original)}")
            log_progress(f"Examples: {list(only_in_original)[:5]}")
        
        if only_in_manual:
            log_progress(f"Combinations only in manual: {len(only_in_manual)}")
            log_progress(f"Examples: {list(only_in_manual)[:5]}")
    
    # Check if there are records with missing subcategory that are affecting totals
    spu_missing_subcat = spu_with_cluster[spu_with_cluster['sub_cate_name'].isna()]
    if len(spu_missing_subcat) > 0:
        missing_qty = spu_missing_subcat['recommended_quantity_change'].sum()
        missing_inv = spu_missing_subcat['investment_required'].sum()
        log_progress(f"\n⚠️ MISSING SUBCATEGORY IMPACT:")
        log_progress(f"Records with missing subcategory: {len(spu_missing_subcat):,}")
        log_progress(f"Quantity from missing records: {missing_qty:.1f} units")
        log_progress(f"Investment from missing records: ¥{missing_inv:,.0f}")
        
        if abs(missing_qty) > 1 or abs(missing_inv) > 100:
            log_progress("📊 This explains part of the discrepancy!")
    
    # Save the manual calculation for comparison
    manual_cluster_agg.to_csv("output/manual_cluster_aggregation_debug.csv", index=False)
    log_progress(f"✅ Saved manual calculation: output/manual_cluster_aggregation_debug.csv")
    
    # Final diagnosis
    log_progress(f"\n🎯 DIAGNOSIS:")
    
    spu_to_store_diff = abs(spu_total_qty - store_total_qty)
    store_to_cluster_diff = abs(store_total_qty - cluster_total_qty)
    manual_to_original_diff = abs(manual_total_qty - cluster_total_qty)
    
    if spu_to_store_diff < 0.01:
        log_progress("✅ SPU → Store aggregation is correct")
    else:
        log_progress(f"⚠️ SPU → Store aggregation has {spu_to_store_diff:.2f} unit difference")
    
    if store_to_cluster_diff > 1:
        log_progress(f"❌ Store → Cluster aggregation has {store_to_cluster_diff:.1f} unit difference")
        
        if manual_to_original_diff < 1:
            log_progress("   ✅ Manual recalculation matches original - issue may be in aggregation logic")
        else:
            log_progress("   ⚠️ Manual recalculation differs from original - issue in data or method")
    
    # Check the source of cluster aggregation creation
    log_progress(f"\n🔍 RECOMMENDED ACTIONS:")
    log_progress("1. Check how cluster_subcategory_aggregation was created in Step 19")
    log_progress("2. Verify that all SPU records have proper subcategory mapping")
    log_progress("3. Ensure cluster assignments are complete for all stores")
    log_progress("4. Review the aggregation logic in create_cluster_subcategory_aggregation()")

if __name__ == "__main__":
    investigate_discrepancy() 