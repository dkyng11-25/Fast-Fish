#!/usr/bin/env python3
"""
Analyze where clusters are lost in the pipeline
"""
import pandas as pd
import os

def check_file_clusters(filepath, cluster_col='cluster_id', description=""):
    """Check how many clusters are in a file"""
    if not os.path.exists(filepath):
        print(f"  ❌ {description}: FILE NOT FOUND - {filepath}")
        return None
    
    try:
        df = pd.read_csv(filepath, dtype={'str_code': str})
        
        # Try different cluster column names
        cluster_cols = ['cluster_id', 'Cluster', 'cluster', 'store_group', 'Store Group']
        found_col = None
        for col in cluster_cols:
            if col in df.columns:
                found_col = col
                break
        
        if found_col:
            unique_clusters = df[found_col].nunique()
            total_rows = len(df)
            print(f"  ✅ {description}: {unique_clusters} clusters, {total_rows:,} rows")
            print(f"     File: {os.path.basename(filepath)}")
            return unique_clusters
        else:
            print(f"  ⚠️  {description}: No cluster column found")
            print(f"     Columns: {list(df.columns)[:10]}")
            return None
    except Exception as e:
        print(f"  ❌ {description}: ERROR - {e}")
        return None

print("="*80)
print("🔍 CLUSTER DROP-OFF ANALYSIS")
print("="*80)
print()

print("📊 STEP 6: Clustering Results")
check_file_clusters("output/clustering_results_spu.csv", description="Step 6 Clustering")
print()

print("�� STEP 13: Consolidated SPU Rules")
check_file_clusters("output/consolidated_spu_rule_results_detailed_202510A.csv", description="Step 13 Detailed")
check_file_clusters("output/consolidated_spu_rule_results.csv", description="Step 13 Store Summary")
print()

print("📊 STEP 14: Fast Fish Format")
check_file_clusters("output/enhanced_fast_fish_format_202510A.csv", description="Step 14 Enhanced Fast Fish")
print()

print("📊 STEP 17: Augmented Recommendations")
check_file_clusters("output/fast_fish_with_historical_and_cluster_trending_analysis_202510A.csv", description="Step 17 Augmented")
print()

print("📊 STEP 18: Sell-Through Analysis")
check_file_clusters("output/fast_fish_with_sell_through_analysis_202510A.csv", description="Step 18 Sell-Through")
print()

print("📊 STEP 19: Detailed SPU Breakdown")
check_file_clusters("output/detailed_spu_recommendations_202510A.csv", description="Step 19 Detailed SPU")
check_file_clusters("output/cluster_subcategory_aggregation_202510A.csv", description="Step 19 Cluster Aggregation")
print()

print("📊 STEP 22: Store Attribute Enrichment")
check_file_clusters("output/enriched_store_attributes_202510A.csv", description="Step 22 Enriched Stores")
print()

print("📊 STEP 24: Comprehensive Cluster Labeling")
check_file_clusters("output/comprehensive_cluster_labels.csv", description="Step 24 Cluster Labels")
print()

print("📊 STEP 25: Product Role Classification")
check_file_clusters("output/product_role_classifications_202510A.csv", description="Step 25 Product Roles")
print()

print("📊 STEP 27: Gap Matrix")
check_file_clusters("output/gap_analysis_detailed_202510A.csv", description="Step 27 Gap Analysis")
print()

print("="*80)
print("🎯 ANALYSIS COMPLETE")
print("="*80)
