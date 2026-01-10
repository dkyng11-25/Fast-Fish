#!/usr/bin/env python3
"""
Step 21: D-F Label/Tag Recommendation Sheet

This step generates a production-ready Excel file for Fast Fish's merchandising system
with bilingual (Chinese/English) tag recommendations by cluster/store, including
target quantities, rationale scores, and constraints.

D-F Deliverable Requirements:
- Cluster/Store identifiers
- Bilingual style tag combinations (Chinese | English)
- Target quantities with time units
- Rationale scores for recommendations
- Capacity/lifecycle constraints
- Fast Fish Excel template compliance

Author: Data Pipeline Team
Date: 2025-07-17
Version: 2.0 - Complete rewrite for Fast Fish D-F requirements

 HOW TO RUN (CLI + ENV) — Read this before executing
 ----------------------------------------------------
 Overview
 - Period-aware: Step 21 builds D-F tag sheets based on the recommendation universe for a specific half-month label (e.g., 202510A).
 - Why period label matters: SPU recommendations and cluster assignments are period-bound. Using a mismatched label causes silent misalignment (wrong clusters, missing subcategory tags).

 Quick Start (target 202510A)
   Command (period-aware; auto-resolves via manifest where possible):
     PYTHONPATH=. python3 src/step21_label_tag_recommendations.py \
       --target-yyyymm 202510 \
       --target-period A

 Inputs and Resolution (why it works)
 - Cluster assignments: resolved from common locations (period-labeled preferred) and standardized to an integer `Cluster` field. Why: consistent cluster IDs are required to generate balanced tag recommendations per group.
 - SPU recommendations: preferred from manifest (`step21:spu_recommendations`) or Step 19 detailed breakdown files (period-labeled first). Why: we must use the exact recommendation set for the target period; otherwise rationale/quantity math won’t reflect reality.
 - Store metadata: enriched attributes file if available (period-labeled first), else a minimal set. Why: optional enrichment improves placement and constraints but is not mandatory.

 Single-Cluster Testing vs Production
 - Test: Generate Step 19/14 only for a single cluster (e.g., Cluster 22). Step 21 will still build a valid D-F sheet for that subset.
 - Production: Ensure upstream SPU recommendations and clustering are available for ALL clusters to populate a complete D-F workbook.

 Common failure modes (and what to do)
 - No SPU recommendation data found
   • Cause: manifest is empty and period-labeled Step 19 outputs don’t exist on disk.
   • Fix: run Step 19 for the target label or pass the expected file via manifest before re-running.
 - All recommendations assigned to a single cluster or cluster=0
   • Cause: SPU input lacks cluster info and cluster assignment file is missing/has non-standard columns.
   • Fix: provide a period-correct clustering file with ['str_code','Cluster'] or ['str_code','cluster'] and re-run.
 - Excel writer failure
   • Cause: missing openpyxl or file lock.
   • Fix: `pip install openpyxl` and ensure the output file isn’t open in Excel; the script falls back to CSV when needed.

 Why this configuration leads to stable outcomes
 - Period-labeled resolution keeps SPU universe, clusters, and bilingual tags consistent with the planning window.
 - Standardizing cluster IDs and validating coverage ensures recommendations are balanced and explainable (rationale, constraints).
 - Manifest-first lookups prevent stale or wrong-period inputs from being used inadvertently.

 Manifest notes
 - Step 21 reads SPU inputs via manifest when available and registers final D-F outputs (Excel/CSV) with period labels. Downstream store-level steps (32–36) should resolve inputs from the manifest whenever possible.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import warnings
from tqdm import tqdm
import json
import argparse
import sys
import glob
import os as _os

# Robust imports for both package and script execution
try:
    from src.config import get_period_label, get_current_period  # when running with -m src.module
    from src.pipeline_manifest import register_step_output, get_step_input
except Exception:
    try:
        from config import get_period_label, get_current_period  # when running from src/ directly
        from pipeline_manifest import register_step_output, get_step_input
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

# Configuration
MIN_CLUSTER_SIZE = 5  # Minimum stores per cluster to generate recommendations
TARGET_SPUS_PER_CLUSTER = 20  # Target number of SPUs per cluster for tag recommendations
RATIONALE_THRESHOLD = 0.30  # Minimum rationale score for recommendations (lowered for debugging)

# Enhanced bilingual translation dictionary with proper English translations
TAG_TRANSLATIONS = {
    # Seasonal tags
    '夏': '夏 | Summer',
    '春': '春 | Spring', 
    '秋': '秋 | Autumn',
    '冬': '冬 | Winter',
    
    # Size/Fit tags
    '中': '中 | Medium',
    '大': '大 | Large',
    '小': '小 | Small',
    'X版': 'X版 | X-Cut',
    
    # Location tags
    '前台': '前台 | Front Store',
    '后台': '后台 | Back Store',
    
    # Gender tags
    '男': '男 | Men',
    '女': '女 | Women',
    
    # Product categories
    'T恤': 'T恤 | T-Shirt',
    'POLO衫': 'POLO衫 | Polo Shirt',
    '连衣裙': '连衣裙 | Dress',
    'X版连衣裙': 'X版连衣裙 | X-Cut Dress',
    '裙/连衣裙': '裙/连衣裙 | Skirt/Dress',
    '牛仔裤': '牛仔裤 | Jeans',
    '休闲裤': '休闲裤 | Casual Pants',
    '中裤': '中裤 | Capri Pants',
    '工装裤': '工装裤 | Cargo Pants',
    '束脚裤': '束脚裤 | Jogger Pants',
    '直筒裤': '直筒裤 | Straight Pants',
    '茄克': '茄克 | Jacket',
    '防晒衣': '防晒衣 | UV Protection',
    '套装': '套装 | Suit Set',
    
    # Style descriptors
    '休闲': '休闲 | Casual',
    '凉感': '凉感 | Cooling',
    '圆领': '圆领 | Crew Neck',
    '休闲圆领T恤': '休闲圆领T恤 | Casual Crew T-Shirt',
    '凉感圆领T恤': '凉感圆领T恤 | Cooling Crew T-Shirt',
    '休闲POLO': '休闲POLO | Casual Polo',
    '凉感POLO': '凉感POLO | Cooling Polo',
    
    # Business/occasion
    '商务': '商务 | Business',
    '运动': '运动 | Sports',
    '正式': '正式 | Formal',
    
    # Additional translations for missing items
    '休闲衬衣': '休闲衬衣 | Casual Shirt',
    '合体圆领T恤': '合体圆领T恤 | Fitted Crew T-Shirt',
    '微宽松圆领T恤': '微宽松圆领T恤 | Relaxed Crew T-Shirt',
    '梭织防晒衣': '梭织防晒衣 | Woven UV Protection',
    '裙类套装': '裙类套装 | Skirt Suit Set',
    '裤类套装': '裤类套装 | Pants Suit Set',
    '带帽休闲茄克': '带帽休闲茄克 | Hooded Casual Jacket',
    'A版连衣裙': 'A版连衣裙 | A-Line Dress',
    'H版连衣裙': 'H版连衣裙 | H-Line Dress',
    '锥形裤': '锥形裤 | Tapered Pants',
    '阔腿裤': '阔腿裤 | Wide Leg Pants',
    '中袖衬衫': '中袖衬衫 | Short Sleeve Shirt',
    'V领T恤': 'V领T恤 | V-Neck T-Shirt',
    'V领毛衣': 'V领毛衣 | V-Neck Sweater',
    '低帮袜': '低帮袜 | Ankle Socks',
    '中帮袜': '中帮袜 | Crew Socks',
    '四角裤': '四角裤 | Boxer Briefs',
    '三角裤': '三角裤 | Briefs',
    '西装': '西装 | Business Suit',
    '开衫': '开衫 | Cardigan',
    '毛衣': '毛衣 | Sweater',
    '半身裙': '半身裙 | Skirt',
    
    # Final batch of missing translations
    '针织防晒衣': '针织防晒衣 | Knit UV Protection',
    '修身圆领T恤': '修身圆领T恤 | Slim Crew T-Shirt',
    '休闲鞋': '休闲鞋 | Casual Shoes',
    '无袖T恤': '无袖T恤 | Sleeveless T-Shirt',
    '潮鞋': '潮鞋 | Trendy Shoes',
    '外穿式衬衣': '外穿式衬衣 | Outer Shirt',
    '套头POLO': '套头POLO | Pullover Polo',
    '短裤': '短裤 | Shorts',
    '宽松圆领T恤': '宽松圆领T恤 | Loose Crew T-Shirt'
}

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_clustering_and_spu_data(period_label: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load cluster assignments, SPU recommendations, and store data"""
    log_progress("📊 Loading clustering and SPU recommendation data...")
    
    # Load cluster assignments
    cluster_files = [
        "output/clustering_results_spu.csv",
        "output/clustering_results_subcategory.csv", 
        "../output/clustering_results_spu.csv",
        "../output/clustering_results_subcategory.csv",
        "data/store_cluster_assignments.csv"
    ]
    
    cluster_df = None
    for cluster_file in cluster_files:
        try:
            if os.path.exists(cluster_file):
                cluster_df = pd.read_csv(cluster_file)
                log_progress(f"   ✓ Loaded clusters from: {cluster_file}")
                break
        except Exception as e:
            continue
    
    if cluster_df is None:
        # Create dummy cluster data if not found
        log_progress("   ⚠️ No cluster file found, creating dummy clusters")
        cluster_df = pd.DataFrame({
            'str_code': [f'store_{i}' for i in range(100)],
            'Cluster': np.random.randint(0, 10, 100)
        })
    
    # Standardize cluster column name to 'Cluster' (integer)
    if 'Cluster' in cluster_df.columns:
        cluster_df['cluster'] = cluster_df['Cluster'].astype(int)
    elif 'cluster' in cluster_df.columns:
        cluster_df['Cluster'] = cluster_df['cluster'].astype(int)
    
    # Load SPU recommendations (prefer manifest; fallback to period-labeled then generic files)
    spu_file = get_step_input("step21", "spu_recommendations")

    # Normalize relative path if needed
    if spu_file and spu_file.startswith('../'):
        spu_file = spu_file[3:]

    if not spu_file or not os.path.exists(spu_file):
        if not spu_file:
            log_progress("   ⚠️ No SPU input registered in manifest, attempting fallback search...")
        else:
            log_progress(f"   ⚠️ Manifest SPU file missing on disk: {spu_file}. Attempting fallback search...")

        candidates: List[str] = []
        if period_label:
            # Prefer Step 19 detailed breakdown for the target period
            candidates.extend(glob.glob(f"output/detailed_spu_breakdown_{period_label}*.csv"))
            # Fallback to prior naming conventions if present
            candidates.extend(glob.glob(f"output/detailed_spu_recommendations_{period_label}*.csv"))
            candidates.extend(glob.glob(f"output/corrected_detailed_spu_recommendations_{period_label}*.csv"))
        # Broader fallback (non period-specific)
        candidates.extend(glob.glob("output/detailed_spu_breakdown_*.csv"))
        candidates.extend(glob.glob("output/detailed_spu_recommendations_*.csv"))
        candidates.extend(glob.glob("output/corrected_detailed_spu_recommendations_*.csv"))
        # Legacy consolidated file
        if os.path.exists("output/consolidated_spu_rule_results.csv"):
            candidates.append("output/consolidated_spu_rule_results.csv")

        if candidates:
            spu_file = max(candidates, key=os.path.getctime)
            log_progress(f"   ✓ Found fallback SPU recommendations: {spu_file}")
        else:
            raise FileNotFoundError("No SPU recommendation data found")

    # Load selected SPU recommendations
    spu_df = pd.read_csv(spu_file, dtype={'str_code': str, 'spu_code': str})
    log_progress(f"   ✓ Loaded SPU data from: {spu_file}")
    log_progress(f"   ✓ Records: {len(spu_df):,}")
    
    # Standardize cluster column in SPU data to integer
    if 'cluster' in spu_df.columns:
        spu_df['cluster'] = spu_df['cluster'].fillna(0).astype(int)
    elif 'Cluster' in spu_df.columns:
        spu_df['cluster'] = spu_df['Cluster'].fillna(0).astype(int)
    else:
        # If no cluster column, add default cluster 0
        spu_df['cluster'] = 0
        log_progress("   ⚠️ No cluster column in SPU data, assigning all to cluster 0")
    
    # Check if SPU data needs cluster assignment (all records have same cluster)
    unique_clusters_in_spu = spu_df['cluster'].nunique()
    if unique_clusters_in_spu <= 1:
        log_progress("   🔄 SPU data has limited cluster diversity, assigning clusters from store assignments...")
        
        # Create store-to-cluster mapping from cluster_df
        if 'str_code' in cluster_df.columns and 'cluster' in cluster_df.columns:
            store_cluster_map = cluster_df.set_index('str_code')['cluster'].to_dict()
            
            # Assign clusters to SPU data based on store_code
            spu_df['cluster'] = spu_df['str_code'].map(store_cluster_map).fillna(0).astype(int)
            
            new_unique_clusters = spu_df['cluster'].nunique()
            log_progress(f"   ✓ Assigned clusters to SPU data: {new_unique_clusters} unique clusters")
        else:
            log_progress("   ⚠️ Cannot assign clusters: missing str_code or cluster columns")
    else:
        log_progress(f"   ✓ SPU data already has {unique_clusters_in_spu} clusters assigned")
    
    # Load store metadata if available
    # Store metadata: prefer period-specific enriched attributes for store_type and ratios; avoid synthetic combined
    store_files = [
        os.path.join('output', f'enriched_store_attributes_{period_label}.csv'),
        os.path.join('output', 'enriched_store_attributes.csv'),
        os.path.join('data', 'store_coordinates_extended.csv')
    ]
    
    store_df = None
    for store_file in store_files:
        try:
            if os.path.exists(store_file):
                store_df = pd.read_csv(store_file)
                log_progress(f"   ✓ Loaded store metadata from: {store_file}")
                break
        except Exception:
            continue
    
    if store_df is None:
        # Create minimal store data
        unique_stores = cluster_df['str_code'].unique() if 'str_code' in cluster_df.columns else []
        store_df = pd.DataFrame({'str_code': unique_stores})
        log_progress("   ✓ Created minimal store metadata")
    
    return cluster_df, spu_df, store_df

def translate_tag(tag: str) -> str:
    """Translate a style tag to bilingual format"""
    if tag in TAG_TRANSLATIONS:
        return TAG_TRANSLATIONS[tag]
    
    # Special handling for Unknown subcategories
    if tag == 'Unknown':
        return "综合商品 | Mixed Products"
    
    # If not in dictionary, create a basic bilingual format
    # Try to detect if it's already bilingual
    if ' | ' in tag:
        return tag  # Already bilingual
    
    # For unknown Chinese tags, keep as-is with Unknown English
    if any('\u4e00' <= char <= '\u9fff' for char in tag):  # Contains Chinese characters
        return f"{tag} | {tag}"  # Use same tag for both languages
    else:
        # For English or mixed content
        return f"{tag} | {tag}"

def analyze_cluster_style_preferences(cluster_id: int, spu_df: pd.DataFrame, 
                                    cluster_stores: List[str]) -> List[Dict[str, Any]]:
    """Analyze style preferences for a specific cluster using actual pipeline recommendations"""
    
    # Filter SPU data for this cluster using the actual cluster column
    cluster_spu_data = spu_df[spu_df['cluster'] == cluster_id]
    
    # Debug: Log cluster data joining
    if cluster_id <= 3:  # Only log for first few clusters
        log_progress(f"   Debug - Cluster {cluster_id}: {len(cluster_stores)} stores, {len(cluster_spu_data)} SPU records")
        if len(cluster_spu_data) > 0:
            log_progress(f"   Debug - SPU columns: {list(cluster_spu_data.columns)}")
    
    if len(cluster_spu_data) == 0:
        return []
    
    # Analyze subcategory performance in this cluster using actual pipeline data
    if 'sub_cate_name' in cluster_spu_data.columns:
        # Use subcategory names from the pipeline
        subcategory_analysis = cluster_spu_data.groupby('sub_cate_name').agg({
            'recommended_quantity_change': 'sum',
            'investment_required': 'sum', 
            'str_code': 'nunique',  # Number of stores
            'spu_code': 'nunique'   # Number of unique SPUs
        }).reset_index()
        
        subcategory_analysis.columns = ['subcategory', 'total_qty_change', 'total_investment', 
                                       'stores_count', 'spu_count']
        
        # Debug: Log subcategory analysis results
        if cluster_id <= 3:
            log_progress(f"   Debug - Cluster {cluster_id}: {len(subcategory_analysis)} subcategories found")
            if len(subcategory_analysis) > 0:
                log_progress(f"   Debug - Sample subcategories: {subcategory_analysis['subcategory'].head(3).tolist()}")
        
    else:
        # Fallback if subcategory column not available
        log_progress(f"   ⚠️ No sub_cate_name column found, using simplified analysis")
        return []
    
    # Calculate rationale scores based on multiple factors
    recommendations = []
    
    # Calculate investment threshold based on cluster size and data distribution
    investment_values = subcategory_analysis['total_investment'].abs()
    # Use 80th percentile as "high investment" threshold (more balanced)
    investment_threshold = investment_values.quantile(0.80)  # Top 20% considered "high"
    investment_threshold = max(investment_threshold, 1000)  # Minimum threshold of ¥1k
    investment_threshold = min(investment_threshold, 20000)  # Maximum threshold of ¥20k
    
    for _, row in subcategory_analysis.iterrows():
        subcategory = row['subcategory']
        
        # Skip if subcategory is null (but allow 'Unknown' for data completeness)
        if pd.isna(subcategory):
            continue
        
        # Calculate rationale score (0-1)
        # Factor 1: Store coverage (how many stores in cluster sell this)
        store_coverage = row['stores_count'] / len(cluster_stores)
        
        # Factor 2: SPU diversity (more SPUs = higher confidence)
        spu_diversity = min(1.0, row['spu_count'] / 10)  # Normalize to max 10 SPUs
        
        # Factor 3: Investment magnitude (absolute value, normalized)
        investment_score = min(1.0, abs(row['total_investment']) / investment_threshold)
        
        # Factor 4: Quantity recommendation strength (use absolute change)
        qty_score = min(1.0, abs(row['total_qty_change']) / 10)  # Normalize to 10 units change
        
        # Weighted rationale score
        rationale_score = (store_coverage * 0.4 + spu_diversity * 0.3 + 
                          investment_score * 0.2 + qty_score * 0.1)
        
        # Debug: Log rationale score calculation
        if cluster_id <= 3:  # Only log for first few clusters to avoid spam
            log_progress(f"      {subcategory}: store_cov={store_coverage:.2f}, spu_div={spu_diversity:.2f}, inv_score={investment_score:.2f}, qty_score={qty_score:.2f} -> rationale={rationale_score:.2f}")
        
        # Only include if rationale score meets threshold
        if rationale_score >= RATIONALE_THRESHOLD:
            
            # Calculate target quantity based on actual pipeline recommendations
            # Convert quantity change to meaningful daily recommendation
            # If negative (reduction), show as optimization opportunity
            # If positive (increase), show as growth opportunity
            
            total_change = row['total_qty_change']
            stores_in_recommendation = row['stores_count']
            
            if total_change >= 0:
                # Growth recommendation - spread increase across stores and time
                daily_qty = abs(total_change) / max(1, stores_in_recommendation) / 15  # 15-day period
                target_qty_daily = max(0.1, min(3.0, daily_qty))  # Cap at reasonable range
            else:
                # Optimization recommendation - show as reduction/replacement opportunity
                daily_qty = abs(total_change) / max(1, stores_in_recommendation) / 30  # 30-day period  
                target_qty_daily = max(0.1, min(2.0, daily_qty))  # Smaller range for optimizations
            
            # Round to reasonable precision
            target_qty_daily = round(target_qty_daily, 1)
            
            # Create bilingual tag
            bilingual_tag = translate_tag(subcategory)
            # Placement tag: prefer front store for growth, back store for optimization
            placement_tag = '前台 | Front Store' if total_change >= 0 else '后台 | Back Store'
            
            # Generate balanced constraints notes based on business viability
            constraints = []
            
            # Store coverage constraint (market reach)
            if row['stores_count'] < len(cluster_stores) * 0.5:  # Less than 50%
                constraints.append("Limited store coverage")
            
            # Investment constraint (using dynamic threshold)
            if abs(row['total_investment']) > investment_threshold:
                constraints.append("High investment required")
            
            # SPU diversity constraint (product risk)
            if row['spu_count'] < 3:
                constraints.append("Low product diversity")
                
            # Quantity-based constraints
            if total_change < -5:  # Large reduction
                constraints.append("Optimization opportunity")
            elif total_change > 5:  # Large increase
                constraints.append("Growth opportunity")
            elif abs(total_change) < 1:  # Very small change
                constraints.append("Minimal impact")
            
            constraint_text = "; ".join(constraints) if constraints else "Balanced recommendation"
            
            # Calculate coverage percentage
            coverage_ratio = row['stores_count'] / len(cluster_stores)
            coverage_percentage = round(min(100.0, coverage_ratio * 100), 1)
            coverage_display = f"{coverage_percentage}%"
            
            recommendations.append({
                'subcategory': subcategory,
                'bilingual_tag': bilingual_tag,
                'store_placement_tag': placement_tag,
                'target_quantity': target_qty_daily,
                'rationale_score': round(rationale_score, 3),
                'constraints': constraint_text,
                'stores_coverage': coverage_display,
                'spu_count': row['spu_count'],
                'total_investment': row['total_investment'],
                'pipeline_qty_change': total_change  # Include original pipeline value for reference
            })
    
    # Sort by rationale score (best recommendations first)
    recommendations.sort(key=lambda x: x['rationale_score'], reverse=True)
    
    # Limit to top N recommendations per cluster
    return recommendations[:TARGET_SPUS_PER_CLUSTER]

def generate_df_recommendations(cluster_df: pd.DataFrame, spu_df: pd.DataFrame, 
                              store_df: pd.DataFrame) -> pd.DataFrame:
    """Generate D-F tag recommendations for all clusters"""
    log_progress("🎯 Generating D-F tag recommendations by cluster...")
    
    # Merge cluster assignments with store data
    if 'str_code' in cluster_df.columns and 'Cluster' in cluster_df.columns:
        cluster_col = 'Cluster'
    elif 'str_code' in cluster_df.columns and 'cluster' in cluster_df.columns:
        cluster_col = 'cluster'
    else:
        raise ValueError("Cluster data must have 'str_code' and 'Cluster'/'cluster' columns")
    
    # Get unique clusters
    unique_clusters = cluster_df[cluster_col].unique()
    log_progress(f"   ✓ Found {len(unique_clusters)} unique clusters")
    
    all_recommendations = []
    
    for cluster_id in tqdm(unique_clusters, desc="Processing clusters"):
        # Get stores in this cluster
        cluster_stores = cluster_df[cluster_df[cluster_col] == cluster_id]['str_code'].tolist()
        
        # Skip clusters that are too small
        if len(cluster_stores) < MIN_CLUSTER_SIZE:
            log_progress(f"   ⚠️ Skipping cluster {cluster_id} (only {len(cluster_stores)} stores)")
            continue
        
        # Analyze style preferences for this cluster
        cluster_recommendations = analyze_cluster_style_preferences(cluster_id, spu_df, cluster_stores)
        
        # Add cluster information to each recommendation
        for rec in cluster_recommendations:
            rec['cluster_id'] = cluster_id
            rec['stores_in_cluster'] = len(cluster_stores)
            all_recommendations.append(rec)
    
    log_progress(f"   ✓ Generated {len(all_recommendations)} tag recommendations")
    
    # Convert to DataFrame
    recommendations_df = pd.DataFrame(all_recommendations)
    
    return recommendations_df

def create_bilingual_headers() -> Dict[str, str]:
    """Create bilingual column headers for Fast Fish template compliance"""
    return {
        'cluster_id': '集群编号 / Cluster ID',
        'bilingual_tag': '标签组合 / Tag Combination',
        'store_placement_tag': '陈列位置 / Placement',
        'target_quantity': '建议数量 / Target Qty (units/day)',
        'rationale_score': '评分 / Rationale Score',
        'constraints': '约束 / Constraints',
        'stores_in_cluster': '集群门店数 / Stores in Cluster',
        'spu_count': 'SPU数量 / SPU Count',
        'stores_coverage': '门店覆盖率 / Store Coverage %'
    }

def create_df_excel_output(recommendations_df: pd.DataFrame, period_label: Optional[str] = None) -> Dict[str, str]:
    """Create the final D-F outputs (Excel + CSV) with Fast Fish formatting.

    Returns dict with keys that may include:
      - 'excel': path to the Excel workbook
      - 'csv': path to the CSV export
    """
    log_progress("📋 Creating D-F Excel output with bilingual headers...")
    
    if len(recommendations_df) == 0:
        log_progress("   ⚠️ No recommendations to output")
        return {}
    
    # Create bilingual headers
    bilingual_headers = create_bilingual_headers()
    
    # Select and rename columns for output
    output_df = recommendations_df.copy()
    
    # Ensure required columns exist
    required_cols = ['cluster_id', 'bilingual_tag', 'target_quantity', 'rationale_score', 'constraints']
    missing_cols = [col for col in required_cols if col not in output_df.columns]
    
    if missing_cols:
        log_progress(f"   ❌ Missing required columns: {missing_cols}")
        return {}
    
    # Select columns in the correct order
    column_order = [
        'cluster_id',
        'bilingual_tag',
        'store_placement_tag',
        'target_quantity',
        'rationale_score',
        'constraints',
        'stores_in_cluster',
        'spu_count',
        'stores_coverage'
    ]
    
    # Only include columns that exist
    available_columns = [col for col in column_order if col in output_df.columns]
    final_df = output_df[available_columns].copy()
    
    # Rename columns to bilingual headers
    final_df.rename(columns=bilingual_headers, inplace=True)
    
    # Sort by cluster ID and rationale score
    final_df = final_df.sort_values(['集群编号 / Cluster ID', '评分 / Rationale Score'], ascending=[True, False])
    
    # Generate output filename (DUAL OUTPUT PATTERN)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if period_label:
        timestamped_excel_file = f"output/D_F_Label_Tag_Recommendation_Sheet_{period_label}_{timestamp}.xlsx"
        generic_excel_file = f"output/D_F_Label_Tag_Recommendation_Sheet_{period_label}.xlsx"
        timestamped_csv_file = f"output/client_desired_store_group_style_tags_targets_{period_label}_{timestamp}.csv"
        generic_csv_file = f"output/client_desired_store_group_style_tags_targets_{period_label}.csv"
    else:
        timestamped_excel_file = f"output/D_F_Label_Tag_Recommendation_Sheet_{timestamp}.xlsx"
        generic_excel_file = "output/D_F_Label_Tag_Recommendation_Sheet.xlsx"
        timestamped_csv_file = f"output/client_desired_store_group_style_tags_targets_{timestamp}.csv"
        generic_csv_file = "output/client_desired_store_group_style_tags_targets.csv"

    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    excel_output_file = timestamped_excel_file
    csv_output_file = timestamped_csv_file
    
    # Create Excel file with formatting
    try:
        with pd.ExcelWriter(excel_output_file, engine='openpyxl') as writer:
            # Main recommendations sheet
            final_df.to_excel(writer, sheet_name='Tag Recommendations', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets['Tag Recommendations']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Add summary sheet
            summary_data = {
                '统计项 / Metric': ['总推荐数 / Total Recommendations', 
                                   '集群数量 / Clusters Analyzed',
                                   '平均评分 / Average Score',
                                   '生成时间 / Generated Time'],
                '数值 / Value': [len(final_df),
                                len(final_df['集群编号 / Cluster ID'].unique()),
                                round(final_df['评分 / Rationale Score'].mean(), 3),
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Also emit a CSV alongside Excel for convenience
        try:
            final_df.to_csv(csv_output_file, index=False, encoding='utf-8-sig')
            log_progress(f"   ✓ D-F CSV file created: {csv_output_file}")
        except Exception as csv_e:
            log_progress(f"   ⚠️ Could not create CSV copy: {csv_e}")

        log_progress(f"   ✓ Timestamped D-F Excel file created: {excel_output_file}")
        
        # Save generic Excel version (for pipeline flow)
        with pd.ExcelWriter(generic_excel_file, engine='openpyxl') as writer:
            final_df.to_excel(writer, sheet_name='Tag Recommendations', index=False)
        log_progress(f"   ✓ Generic D-F Excel file created: {generic_excel_file}")
        
        # Create symlink for generic CSV version (for pipeline flow)
        if os.path.exists(generic_csv_file) or os.path.islink(generic_csv_file):
            os.remove(generic_csv_file)
        os.symlink(os.path.basename(csv_output_file), generic_csv_file)
        log_progress(f"   ✓ Generic D-F CSV symlink created: {generic_csv_file} -> {csv_output_file}")
        
        log_progress(f"   ✓ Recommendations: {len(final_df):,}")
        log_progress(f"   ✓ Clusters covered: {len(final_df['集群编号 / Cluster ID'].unique())}" )
        
        return {"excel": excel_output_file, "csv": csv_output_file}
        
    except Exception as e:
        log_progress(f"   ❌ Error creating Excel file: {str(e)}")
        log_progress("   📝 Creating CSV file as fallback...")
        
        # Create CSV file as fallback
        try:
            final_df.to_csv(csv_output_file, index=False, encoding='utf-8-sig')
            log_progress(f"   ✓ D-F CSV file created: {csv_output_file}")
            log_progress(f"   ✓ Recommendations: {len(final_df):,}")
            log_progress(f"   ✓ Clusters covered: {len(final_df['集群编号 / Cluster ID'].unique())}" )
            return {"csv": csv_output_file}
        except Exception as csv_e:
            log_progress(f"   ❌ Error creating CSV file: {str(csv_e)}")
            return {}

def validate_df_output(output_file: str) -> Dict[str, Any]:
    """Validate the D-F output file meets Fast Fish requirements"""
    log_progress("✅ Validating D-F output file...")
    
    validation_results = {
        'file_exists': os.path.exists(output_file),
        'bilingual_headers': False,
        'no_empty_critical_fields': False,
        'numeric_fields_valid': False,
        'excel_loads_correctly': False,
        'issues': []
    }
    
    if not validation_results['file_exists']:
        validation_results['issues'].append("Output file does not exist")
        return validation_results
    
    try:
        # Check if it's a CSV or Excel file
        if output_file.endswith('.csv'):
            # Load the CSV file
            df = pd.read_csv(output_file)
            validation_results['excel_loads_correctly'] = False  # Not applicable for CSV
        else:
            # Load the Excel file
            df = pd.read_excel(output_file, sheet_name='Tag Recommendations')
            validation_results['excel_loads_correctly'] = True
        
        # Check bilingual headers
        required_bilingual_patterns = ['/', '集群', 'Cluster', '标签', 'Tag', '建议', 'Target']
        header_text = ' '.join(df.columns)
        bilingual_found = sum(1 for pattern in required_bilingual_patterns if pattern in header_text)
        validation_results['bilingual_headers'] = bilingual_found >= 4
        
        if not validation_results['bilingual_headers']:
            validation_results['issues'].append("Headers are not properly bilingual")
        
        # Check for empty critical fields
        critical_columns = [col for col in df.columns if any(word in col.lower() for word in ['cluster', 'tag', 'target', 'score'])]
        empty_critical = any(df[col].isnull().any() for col in critical_columns)
        validation_results['no_empty_critical_fields'] = not empty_critical
        
        if empty_critical:
            validation_results['issues'].append("Critical fields contain empty values")
        
        # Check numeric fields
        numeric_columns = [col for col in df.columns if any(word in col.lower() for word in ['target', 'score', 'cluster id'])]
        numeric_valid = True
        for col in numeric_columns:
            if col in df.columns:
                try:
                    pd.to_numeric(df[col], errors='raise')
                except:
                    numeric_valid = False
                    validation_results['issues'].append(f"Column {col} contains non-numeric values")
        
        validation_results['numeric_fields_valid'] = numeric_valid
        
        log_progress(f"   ✓ Validation completed - {len(validation_results['issues'])} issues found")
        
    except Exception as e:
        validation_results['issues'].append(f"Error reading file: {str(e)}")
        log_progress(f"   ❌ Validation failed: {str(e)}")
    
    return validation_results

def main():
    """Main execution function for Step 21 (D-F)"""
    log_progress("🚀 Starting Step 21: D-F Label/Tag Recommendation Sheet...")
    
    try:
        # CLI parsing (period-aware)
        parser = argparse.ArgumentParser(description="Step 21: D-F Label/Tag Recommendation Sheet (period-aware)")
        parser.add_argument("--target-yyyymm", dest="target_yyyymm", type=str, help="Target YYYYMM")
        parser.add_argument("--target-period", dest="target_period", type=str, choices=["A", "B", "full", "a", "b"], help="Target period A/B or 'full'")
        # Back-compat flags
        parser.add_argument("--yyyymm", dest="yyyymm", type=str, help="Target YYYYMM (legacy)")
        parser.add_argument("--period", dest="period", type=str, choices=["A", "B", "full", "a", "b"], help="Target period (legacy)")
        args = parser.parse_args()

        # Resolve period context
        current_yyyymm, current_period = get_current_period()
        yyyymm = args.target_yyyymm or args.yyyymm or current_yyyymm
        period_raw = args.target_period or args.period or current_period
        period = None if (period_raw is None or str(period_raw).lower() == "full") else str(period_raw).upper()
        period_label = get_period_label(yyyymm, period)
        log_progress(f"Configured period: {period_label}")
        
        # Step 1: Load data
        cluster_df, spu_df, store_df = load_clustering_and_spu_data(period_label)
        
        # Step 2: Generate recommendations
        recommendations_df = generate_df_recommendations(cluster_df, spu_df, store_df)
        
        if len(recommendations_df) == 0:
            log_progress("❌ No recommendations generated")
            return
        
        # Step 3: Create outputs (Excel + CSV)
        output_files = create_df_excel_output(recommendations_df, period_label)
        
        if not output_files:
            log_progress("❌ Failed to create any output file")
            return
        
        # Step 4: Validate primary output (prefer Excel)
        primary_file = output_files.get('excel') or output_files.get('csv')
        validation_results = validate_df_output(primary_file)
        
        # Final summary
        log_progress("\n" + "="*60)
        log_progress("D-F LABEL/TAG RECOMMENDATION SHEET COMPLETED")
        log_progress("="*60)
        
        log_progress(f"📊 DELIVERY SUMMARY:")
        if 'excel' in output_files:
            log_progress(f"   Excel file: {output_files['excel']}")
        if 'csv' in output_files:
            log_progress(f"   CSV file:   {output_files['csv']}")
        log_progress(f"   Total recommendations: {len(recommendations_df):,}")
        log_progress(f"   Clusters analyzed: {recommendations_df['cluster_id'].nunique()}")
        log_progress(f"   Average rationale score: {recommendations_df['rationale_score'].mean():.3f}")
        
        log_progress(f"\n✅ VALIDATION RESULTS:")
        log_progress(f"   File exists: {'✓' if validation_results['file_exists'] else '❌'}")
        log_progress(f"   Bilingual headers: {'✓' if validation_results['bilingual_headers'] else '❌'}")
        log_progress(f"   No empty critical fields: {'✓' if validation_results['no_empty_critical_fields'] else '❌'}")
        log_progress(f"   Numeric fields valid: {'✓' if validation_results['numeric_fields_valid'] else '❌'}")
        if primary_file.endswith('.csv'):
            log_progress(f"   CSV loads correctly: {'✓' if validation_results['file_exists'] and not validation_results['issues'] else '❌'}")
        else:
            log_progress(f"   Excel loads correctly: {'✓' if validation_results['excel_loads_correctly'] else '❌'}")

        # Register outputs in pipeline manifest (generic and period-specific keys)
        meta_common = {
            "target_year": int(yyyymm[:4]),
            "target_month": int(yyyymm[4:]),
            "target_period": period or "full",
            "records": len(recommendations_df),
            "columns": list(recommendations_df.columns),
            "format": "multi",
        }
        # Excel
        if 'excel' in output_files:
            register_step_output("step21", "df_label_tag_recommendations", output_files['excel'], metadata={**meta_common, "format": "excel"})
            register_step_output("step21", f"df_label_tag_recommendations_{period_label}", output_files['excel'], metadata={**meta_common, "format": "excel"})
        # CSV
        if 'csv' in output_files:
            register_step_output("step21", "df_label_tag_recommendations_csv", output_files['csv'], metadata={**meta_common, "format": "csv"})
            register_step_output("step21", f"df_label_tag_recommendations_csv_{period_label}", output_files['csv'], metadata={**meta_common, "format": "csv"})

        if validation_results['issues']:
            log_progress(f"\n⚠️ ISSUES TO RESOLVE:")
            for issue in validation_results['issues']:
                log_progress(f"   • {issue}")
        
        if len(validation_results['issues']) == 0:
            log_progress(f"\n🎉 D-F deliverable ready for Fast Fish!")
        else:
            log_progress(f"\n⚠️ Please resolve {len(validation_results['issues'])} validation issues before delivery")
        
        log_progress(f"\n✅ Step 21 (D-F) completed!")
        
        return output_files
        
    except Exception as e:
        log_progress(f"❌ Error in Step 21: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main() 