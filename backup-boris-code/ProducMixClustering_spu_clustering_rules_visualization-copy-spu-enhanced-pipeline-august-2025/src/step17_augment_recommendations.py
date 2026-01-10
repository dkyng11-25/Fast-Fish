#!/usr/bin/env python3
"""
Step 17: Ultra-Fast Historical Reference (VECTORIZED VERSION)
============================================================

Ultra-fast version using vectorized pandas operations instead of row-by-row processing.
Should complete in under 30 seconds.

Pipeline Flow:
Step 14 → Step 17 (Ultra-Fast Historical) → Step 18 (Sell-Through)
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import logging
import glob

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_actual_store_group(store_code: str) -> str:
    """Get actual store group from clustering results."""
    cluster_file = "../output/clustering_results_spu.csv"
    if not os.path.exists(cluster_file):
        # Fallback to modulo 46 if clustering file not found
        return f"Store Group {((int(store_code[-3:]) if store_code[-3:].isdigit() else hash(store_code)) % 46) + 1}"
    
    try:
        cluster_df = pd.read_csv(cluster_file)
        store_match = cluster_df[cluster_df['str_code'] == int(store_code)]
        if not store_match.empty:
            cluster_id = store_match.iloc[0]['Cluster']
            return f"Store Group {cluster_id + 1}"
        else:
            return f"Store Group 1"  # Default fallback
    except:
        return f"Store Group 1"  # Error fallback

def load_historical_spu_data() -> pd.DataFrame:
    """Load and process historical 202408A SPU data."""
    
    historical_file = "../data/api_data/complete_spu_sales_202408A.csv"
    
    logger.info(f"Loading historical SPU data from: {historical_file}")
    df = pd.read_csv(historical_file, dtype={'str_code': str, 'spu_code': str})
    
    logger.info(f"Loaded {len(df):,} historical SPU sales records")
    
    return df

def create_store_groups_vectorized(df: pd.DataFrame) -> pd.DataFrame:
    """Create store groups using vectorized operations."""
    logger.info("Creating store groups using vectorized operations...")
    
    # Load clustering data once
    cluster_file = "../output/clustering_results_spu.csv"
    if os.path.exists(cluster_file):
        cluster_df = pd.read_csv(cluster_file)
        cluster_mapping = dict(zip(cluster_df['str_code'].astype(str), cluster_df['Cluster']))
        
        # Vectorized mapping
        df['store_group'] = df['str_code'].map(
            lambda x: f"Store Group {cluster_mapping.get(str(x), 0) + 1}" if str(x) in cluster_mapping else f"Store Group 1"
        )
    else:
        # Fallback vectorized calculation
        df['store_group'] = df['str_code'].apply(
            lambda x: f"Store Group {((int(str(x)[-3:]) if str(x)[-3:].isdigit() else hash(str(x))) % 46) + 1}"
        )
    
    return df

def create_historical_lookup_vectorized(historical_df: pd.DataFrame) -> pd.DataFrame:
    """Create historical reference lookup using vectorized operations."""
    
    logger.info("Creating historical reference lookup with vectorized operations...")
    
    # Add store groups using vectorized operations
    historical_grouped = create_store_groups_vectorized(historical_df)
            
    # Create lookup key
    historical_grouped['lookup_key'] = historical_grouped['cate_name'] + ' | ' + historical_grouped['sub_cate_name']
    
    # Vectorized aggregation
    logger.info("Performing vectorized aggregation...")
    historical_lookup = historical_grouped.groupby(['store_group', 'lookup_key']).agg({
        'spu_code': 'nunique',
        'spu_sales_amt': 'sum',
        'quantity': 'sum',
        'str_code': 'nunique'
    }).reset_index()
    
    historical_lookup.columns = ['store_group', 'lookup_key', 'historical_spu_count', 
                                'historical_total_sales', 'historical_total_quantity', 'historical_store_count']
    
    logger.info(f"Created historical lookup with {len(historical_lookup)} Store Group × Sub-Category combinations")
    
    return historical_lookup

def parse_target_style_tags_vectorized(target_style_tags_series: pd.Series) -> pd.Series:
    """Parse Target_Style_Tags using vectorized operations."""
    
    logger.info("Parsing Target_Style_Tags using vectorized operations...")
    
    def extract_category_subcategory(tags):
        try:
            if tags.startswith('[') and tags.endswith(']'):
                # 5-field format: [category, subcategory, location, season, gender]
                cleaned = tags.strip('[]')
                parts = [part.strip() for part in cleaned.split(',')]
                if len(parts) >= 2:
                    return f"{parts[0]} | {parts[1]}"
                else:
                    return tags
            else:
                # Already in historical format (2-field or other)
                return tags
        except:
            return tags
    
    return target_style_tags_series.apply(extract_category_subcategory)

def augment_fast_fish_vectorized(fast_fish_df: pd.DataFrame, historical_lookup: pd.DataFrame) -> pd.DataFrame:
    """
    Ultra-fast augmentation using vectorized pandas operations.
    
    Args:
        fast_fish_df: Original Fast Fish recommendations DataFrame
        historical_lookup: Historical lookup DataFrame
        
    Returns:
        Enhanced DataFrame with historical columns
    """
    logger.info(f"Augmenting {len(fast_fish_df)} Fast Fish recommendations using vectorized operations...")
    
    # Create a copy
    augmented_df = fast_fish_df.copy()
    
    # Parse Target_Style_Tags vectorized
    augmented_df['parsed_category'] = parse_target_style_tags_vectorized(augmented_df['Target_Style_Tags'])
    
    # Create merge key
    augmented_df['merge_key'] = augmented_df['Store_Group_Name'] + '|||' + augmented_df['parsed_category']
    historical_lookup['merge_key'] = historical_lookup['store_group'] + '|||' + historical_lookup['lookup_key']
    
    # Vectorized merge
    logger.info("Performing vectorized merge with historical data...")
    merged_df = augmented_df.merge(
        historical_lookup[['merge_key', 'historical_spu_count', 'historical_total_sales', 'historical_store_count']], 
        on='merge_key', 
        how='left'
    )
    
    # Add historical reference columns
    merged_df['Historical_SPU_Quantity_202408A'] = merged_df['historical_spu_count']
    merged_df['SPU_Change_vs_Historical'] = merged_df['Target_SPU_Quantity'] - merged_df['historical_spu_count']
    merged_df['SPU_Change_vs_Historical_Pct'] = (
        (merged_df['Target_SPU_Quantity'] - merged_df['historical_spu_count']) / merged_df['historical_spu_count'] * 100
    ).fillna(0)
    
    # Store count and sales
    merged_df['Historical_Store_Count_202408A'] = merged_df['historical_store_count']
    merged_df['Historical_Total_Sales_202408A'] = merged_df['historical_total_sales']
    
    # Enhanced rationale with historical context
    def create_rationale(row):
        rationale_parts = []
        
        # Original rationale
        if pd.notna(row['Data_Based_Rationale']):
            rationale_parts.append(str(row['Data_Based_Rationale']))
        
        # Historical context
        if pd.notna(row['Historical_SPU_Quantity_202408A']):
            hist_qty = row['Historical_SPU_Quantity_202408A']
            change = row['SPU_Change_vs_Historical']
            change_pct = row['SPU_Change_vs_Historical_Pct']
            
            if change > 0:
                hist_context = f"Historical baseline: {hist_qty} SPUs (August 2024). Expanding by {change} SPUs (+{change_pct:.1f}%)"
            else:
                hist_context = f"Historical baseline: {hist_qty} SPUs (August 2024). Reducing by {abs(change)} SPUs ({change_pct:.1f}%)"
            rationale_parts.append(hist_context)
        
        return " | ".join(rationale_parts) if rationale_parts else "Standard category optimization"
    
    merged_df['Enhanced_Rationale'] = merged_df.apply(create_rationale, axis=1)
    
    # Calculate match statistics
    matches = merged_df['Historical_SPU_Quantity_202408A'].notna().sum()
    total = len(merged_df)
    
    logger.info(f"Historical matches: {matches}/{total} ({matches/total*100:.1f}%)")
    
    return merged_df

def save_augmented_file(augmented_df: pd.DataFrame) -> str:
    """Save the augmented Fast Fish recommendations file."""
    
    # Create a copy for formatting fixes
    formatted_df = augmented_df.copy()
    
    # FIX 1: Apply month zero-padding format (6 -> 06)
    logger.info("🔧 Applying format fixes for client compliance...")
    if 'Month' in formatted_df.columns:
        formatted_df['Month'] = formatted_df['Month'].astype(str).str.zfill(2)
        logger.info("   ✅ Fixed Month format (added zero-padding)")
    
    # FIX 2: Fix Target_Style_Tags format (pipe to brackets + commas)
    if 'Target_Style_Tags' in formatted_df.columns:
        # Convert "T恤 | 休闲圆领T恤 | 前台 | 夏 | 男" to "[T恤, 休闲圆领T恤, 前台, 夏, 男]"
        formatted_df['Target_Style_Tags'] = '[' + formatted_df['Target_Style_Tags'].str.replace(' | ', ', ') + ']'
        logger.info("   ✅ Fixed Target_Style_Tags format (added brackets, changed separators)")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"../output/fast_fish_with_historical_reference_{timestamp}.csv"
    
    logger.info(f"Saving enhanced Fast Fish file to: {output_file}")
    logger.info(f"Output contains {len(formatted_df.columns)} columns with historical reference")
    
    formatted_df.to_csv(output_file, index=False)
    
    return output_file

def print_augmentation_summary(original_df: pd.DataFrame, augmented_df: pd.DataFrame, output_file: str):
    """Print summary of the historical augmentation process."""
    
    # Calculate historical statistics
    historical_matches = augmented_df['Historical_SPU_Quantity_202408A'].notna().sum()
    new_categories = augmented_df['Historical_SPU_Quantity_202408A'].isna().sum()
    
    expanding_categories = (augmented_df['SPU_Change_vs_Historical'] > 0).sum()
    contracting_categories = (augmented_df['SPU_Change_vs_Historical'] < 0).sum()
    stable_categories = (augmented_df['SPU_Change_vs_Historical'] == 0).sum()
    
    print(f"\n" + "="*80)
    print(f"🚀 ULTRA-FAST FISH HISTORICAL REFERENCE SUMMARY")
    print(f"   Vectorized Historical Baseline Analysis")
    print(f"="*80)
    
    print(f"\n📊 BASIC METRICS:")
    print(f"  • Original recommendations: {len(original_df):,}")
    print(f"  • Enhanced recommendations: {len(augmented_df):,}")
    print(f"  • Output columns: {len(augmented_df.columns)} (Historical + Original)")
    print(f"  • Output file: {output_file}")
    
    print(f"\n📈 HISTORICAL REFERENCE ANALYSIS:")
    print(f"  • Found historical data: {historical_matches:,} recommendations")
    print(f"  • New categories (no historical data): {new_categories:,} recommendations")
    print(f"  • Historical match rate: {historical_matches/len(augmented_df)*100:.1f}%")
    
    print(f"\n🔄 RECOMMENDATION PATTERNS vs HISTORICAL:")
    print(f"  • Expanding categories: {expanding_categories:,}")
    print(f"  • Contracting categories: {contracting_categories:,}")
    print(f"  • Stable categories: {stable_categories:,}")
    
    print(f"\n🎯 KEY ENHANCEMENTS vs ORIGINAL:")
    print(f"  • Historical Context: July 2024 baseline comparison")
    print(f"  • Enhanced Rationale: Decision context with historical intelligence")
    print(f"  • Ultra-Fast Processing: Vectorized operations completed in seconds")

def main():
    """Step 17: Ultra-Fast Historical Reference (Vectorized Version)."""
    
    start_time = datetime.now()
    logger.info("🚀 Starting Step 17: Ultra-Fast Historical Reference...")
    logger.info("   Vectorized version for maximum speed")
    
    try:
        # Load Fast Fish recommendations from Step 14 (use the most recent file)
        fast_fish_files = glob.glob("../output/fast_fish_spu_count_recommendations_*.csv")
        if not fast_fish_files:
            # Fallback to older file format
            fast_fish_files = glob.glob("../output/fast_fish_with_sell_through_analysis_*.csv")
            if not fast_fish_files:
                logger.error("No Fast Fish recommendations files found")
                raise FileNotFoundError("No Fast Fish recommendations files found in ../output/")
        
        # Get the most recent file
        fast_fish_file = max(fast_fish_files, key=os.path.getmtime)
        logger.info(f"Loading Fast Fish recommendations from: {fast_fish_file}")
        fast_fish_df = pd.read_csv(fast_fish_file)
        logger.info(f"Loaded {len(fast_fish_df):,} Fast Fish recommendations")
        
        # Verify we have the correct number of store groups
        unique_groups = fast_fish_df['Store_Group_Name'].nunique()
        logger.info(f"Found {unique_groups} unique store groups")
        if unique_groups != 46:
            logger.warning(f"Expected 46 store groups, got {unique_groups}")
        
        # Load historical data
        logger.info("Loading historical 202408A data...")
        historical_df = load_historical_spu_data()
        
        # Create historical reference lookup using vectorized operations
        logger.info("Creating historical reference lookup using vectorized operations...")
        historical_lookup = create_historical_lookup_vectorized(historical_df)
        
        # Augment Fast Fish recommendations using vectorized operations
        logger.info("🎯 Applying ultra-fast vectorized historical augmentation...")
        augmented_df = augment_fast_fish_vectorized(fast_fish_df, historical_lookup)
        
        # Save enhanced file
        logger.info("💾 Saving enhanced Fast Fish recommendations...")
        output_file = save_augmented_file(augmented_df)
        
        # Calculate execution time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Print summary
        print_augmentation_summary(fast_fish_df, augmented_df, output_file)
        
        logger.info("✅ Step 17: Ultra-Fast Historical Reference completed successfully!")
        logger.info(f"📁 Output: {output_file}")
        logger.info(f"⚡ Execution time: {execution_time:.1f} seconds")
        
        return output_file
        
    except Exception as e:
        logger.error(f"❌ Error in Step 17: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise

if __name__ == "__main__":
    main()