#!/usr/bin/env python3
"""
Create Proper Aggregated Client Format with Real Rule Recommendations

This script aggregates all business rule recommendations by cluster + style tags
and calculates realistic target SPU quantities based on the actual rule suggestions.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_cluster_mapping() -> pd.DataFrame:
    """Load store-to-cluster mapping"""
    logger.info("📍 Loading cluster mapping...")
    cluster_df = pd.read_csv('output/clustering_results.csv')
    logger.info(f"   Loaded {len(cluster_df):,} store-cluster mappings")
    return cluster_df

def load_spu_style_mapping() -> pd.DataFrame:
    """Load SPU-to-style tags mapping"""
    logger.info("🏷️ Loading SPU style mapping...")
    config_df = pd.read_csv('data/api_data/store_config_202506B.csv')
    
    # Create style tags combination
    style_columns = ['season_name', 'sex_name', 'display_location_name', 'big_class_name', 'sub_cate_name']
    config_df['style_tags'] = config_df[style_columns].apply(
        lambda row: '[' + ', '.join(row.dropna().astype(str)) + ']', axis=1
    )
    
    spu_style_mapping = config_df[['spu_code', 'style_tags']].drop_duplicates()
    logger.info(f"   Loaded {len(spu_style_mapping):,} SPU-style mappings")
    return spu_style_mapping

def load_rule_recommendations() -> pd.DataFrame:
    """Load and combine all rule recommendations"""
    logger.info("📊 Loading all rule recommendations...")
    
    all_recommendations = []
    
    # Rule 7: Missing SPU opportunities
    try:
        rule7_df = pd.read_csv('output/rule7_missing_spu_opportunities.csv')
        rule7_df['rule_type'] = 'Missing SPU'
        rule7_df['quantity_change'] = rule7_df['recommended_quantity_change']
        rule7_agg = rule7_df[['str_code', 'spu_code', 'quantity_change', 'rule_type']]
        all_recommendations.append(rule7_agg)
        logger.info(f"   Rule 7 (Missing): {len(rule7_df):,} recommendations")
    except Exception as e:
        logger.warning(f"   ⚠️ Rule 7 error: {e}")
    
    # Rule 8: Imbalanced cases
    try:
        rule8_df = pd.read_csv('output/rule8_imbalanced_spu_cases.csv')
        rule8_df['rule_type'] = 'Imbalanced'
        rule8_df['quantity_change'] = rule8_df['recommended_quantity_change']
        rule8_agg = rule8_df[['str_code', 'spu_code', 'quantity_change', 'rule_type']]
        all_recommendations.append(rule8_agg)
        logger.info(f"   Rule 8 (Imbalanced): {len(rule8_df):,} recommendations")
    except Exception as e:
        logger.warning(f"   ⚠️ Rule 8 error: {e}")
    
    # Rule 9: Below minimum cases
    try:
        rule9_df = pd.read_csv('output/rule9_below_minimum_spu_cases.csv')
        rule9_df['rule_type'] = 'Below Minimum'
        rule9_df['quantity_change'] = rule9_df['recommended_quantity_change']
        rule9_agg = rule9_df[['str_code', 'sty_code', 'quantity_change', 'rule_type']].rename(columns={'sty_code': 'spu_code'})
        all_recommendations.append(rule9_agg)
        logger.info(f"   Rule 9 (Below Min): {len(rule9_df):,} recommendations")
    except Exception as e:
        logger.warning(f"   ⚠️ Rule 9 error: {e}")
    
    # Rule 10: Overcapacity opportunities
    try:
        rule10_df = pd.read_csv('output/rule10_spu_overcapacity_opportunities.csv')
        rule10_df['rule_type'] = 'Overcapacity'
        rule10_df['quantity_change'] = rule10_df['recommended_quantity_change']
        rule10_agg = rule10_df[['str_code', 'spu_code', 'quantity_change', 'rule_type']]
        all_recommendations.append(rule10_agg)
        logger.info(f"   Rule 10 (Overcapacity): {len(rule10_df):,} recommendations")
    except Exception as e:
        logger.warning(f"   ⚠️ Rule 10 error: {e}")
    
    # Rule 11: Missed sales opportunities
    try:
        rule11_df = pd.read_csv('output/rule11_improved_missed_sales_opportunity_spu_details.csv')
        rule11_df['rule_type'] = 'Missed Sales'
        rule11_df['quantity_change'] = rule11_df['recommended_quantity_change']
        rule11_agg = rule11_df[['str_code', 'spu_code', 'quantity_change', 'rule_type']]
        all_recommendations.append(rule11_agg)
        logger.info(f"   Rule 11 (Missed Sales): {len(rule11_df):,} recommendations")
    except Exception as e:
        logger.warning(f"   ⚠️ Rule 11 error: {e}")
    
    # Rule 12: Sales performance
    try:
        rule12_df = pd.read_csv('output/rule12_sales_performance_spu_details.csv')
        rule12_df['rule_type'] = 'Performance'
        rule12_df['quantity_change'] = rule12_df['recommended_quantity_change']
        rule12_agg = rule12_df[['str_code', 'spu_code', 'quantity_change', 'rule_type']]
        all_recommendations.append(rule12_agg)
        logger.info(f"   Rule 12 (Performance): {len(rule12_df):,} recommendations")
    except Exception as e:
        logger.warning(f"   ⚠️ Rule 12 error: {e}")
    
    # Combine all recommendations
    if all_recommendations:
        combined_df = pd.concat(all_recommendations, ignore_index=True)
        logger.info(f"📈 Total combined recommendations: {len(combined_df):,}")
        return combined_df
    else:
        logger.error("❌ No rule recommendations loaded!")
        return pd.DataFrame()

def aggregate_by_cluster_and_style(recommendations_df: pd.DataFrame, 
                                 cluster_mapping: pd.DataFrame,
                                 style_mapping: pd.DataFrame) -> pd.DataFrame:
    """Aggregate recommendations by cluster and style tags"""
    logger.info("🔄 Aggregating recommendations by cluster + style...")
    
    # Add cluster information
    recommendations_with_cluster = recommendations_df.merge(
        cluster_mapping[['str_code', 'Cluster']], 
        on='str_code', 
        how='left'
    )
    
    # Add style tags information
    recommendations_with_style = recommendations_with_cluster.merge(
        style_mapping, 
        on='spu_code', 
        how='left'
    )
    
    # Remove records without cluster or style info
    clean_recommendations = recommendations_with_style.dropna(subset=['Cluster', 'style_tags'])
    logger.info(f"   Clean recommendations: {len(clean_recommendations):,}")
    
    # Aggregate by cluster + style tags
    aggregated = clean_recommendations.groupby(['Cluster', 'style_tags']).agg({
        'quantity_change': ['sum', 'mean', 'count'],
        'str_code': 'nunique',
        'spu_code': 'nunique'
    }).round(2)
    
    # Flatten column names
    aggregated.columns = ['total_quantity_change', 'avg_quantity_change', 'recommendation_count', 
                         'affected_stores', 'affected_spus']
    aggregated = aggregated.reset_index()
    
    logger.info(f"📊 Aggregated to {len(aggregated):,} cluster+style combinations")
    return aggregated

def convert_to_client_format(aggregated_df: pd.DataFrame) -> pd.DataFrame:
    """Convert aggregated data to client-required format"""
    logger.info("📋 Converting to client format...")
    
    # Calculate target SPU quantity based on recommendations
    # Use a combination of total quantity change and number of affected SPUs
    # to determine reasonable target counts
    
    def calculate_target_spu_count(row):
        total_qty = abs(row['total_quantity_change'])
        affected_spus = row['affected_spus']
        recommendation_count = row['recommendation_count']
        
        # Base calculation: more quantity changes = more SPU targets
        # But cap it to reasonable levels based on affected SPUs
        base_target = max(1, min(affected_spus, total_qty / 10))
        
        # Boost for high-impact combinations
        if total_qty > 100 and affected_spus > 5:
            base_target *= 1.5
        elif total_qty > 50 and affected_spus > 3:
            base_target *= 1.2
        
        # Ensure minimum of 1, maximum reasonable based on affected SPUs
        return max(1, min(affected_spus * 2, int(base_target)))
    
    aggregated_df['Target SPU Quantity'] = aggregated_df.apply(calculate_target_spu_count, axis=1)
    
    # Create client format
    client_format_df = pd.DataFrame({
        'Year': 2025,
        'Month': 6,
        'Period (A/B)': 'B',
        'Store Group Name': 'Cluster_' + aggregated_df['Cluster'].astype(str),
        'Target Style Tags (Combination)': aggregated_df['style_tags'],
        'Target SPU Quantity': aggregated_df['Target SPU Quantity']
    })
    
    # Sort by cluster and quantity (highest first)
    client_format_df = client_format_df.sort_values(['Store Group Name', 'Target SPU Quantity'], 
                                                   ascending=[True, False])
    
    logger.info(f"✅ Client format created: {len(client_format_df):,} records")
    
    # Print summary statistics
    qty_stats = client_format_df['Target SPU Quantity'].describe()
    logger.info(f"📊 Target SPU Quantity Stats:")
    logger.info(f"   Mean: {qty_stats['mean']:.1f}")
    logger.info(f"   Median: {qty_stats['50%']:.1f}")
    logger.info(f"   75th percentile: {qty_stats['75%']:.1f}")
    logger.info(f"   Max: {qty_stats['max']:.1f}")
    
    return client_format_df, aggregated_df

def main():
    """Main execution function"""
    logger.info("🚀 Starting proper aggregated client format creation...")
    
    try:
        # Load all necessary data
        cluster_mapping = load_cluster_mapping()
        style_mapping = load_spu_style_mapping()
        recommendations = load_rule_recommendations()
        
        if recommendations.empty:
            logger.error("❌ No recommendations loaded. Exiting.")
            return
        
        # Aggregate by cluster and style
        aggregated_data = aggregate_by_cluster_and_style(
            recommendations, cluster_mapping, style_mapping
        )
        
        # Convert to client format
        client_format_df, detailed_aggregation = convert_to_client_format(aggregated_data)
        
        # Save outputs
        client_output_path = 'output/proper_aggregated_client_format.csv'
        detailed_output_path = 'output/detailed_cluster_style_aggregation.csv'
        
        client_format_df.to_csv(client_output_path, index=False)
        detailed_aggregation.to_csv(detailed_output_path, index=False)
        
        logger.info(f"✅ Client format saved: {client_output_path}")
        logger.info(f"✅ Detailed aggregation saved: {detailed_output_path}")
        
        # Show sample output
        logger.info("\n📋 Sample client format output:")
        print(client_format_df.head(10).to_string(index=False))
        
        # Show top recommendations by quantity
        logger.info("\n🔝 Top 10 recommendations by Target SPU Quantity:")
        top_10 = client_format_df.nlargest(10, 'Target SPU Quantity')
        print(top_10.to_string(index=False))
        
    except Exception as e:
        logger.error(f"❌ Error in main execution: {e}")
        raise

if __name__ == "__main__":
    main() 