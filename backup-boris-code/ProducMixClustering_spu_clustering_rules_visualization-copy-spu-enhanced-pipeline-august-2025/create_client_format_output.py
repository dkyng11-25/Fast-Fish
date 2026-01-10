#!/usr/bin/env python3
"""
Client Format Converter
Transforms our SPU analysis results into the client's required merchandise planning format
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def calculate_target_periods() -> Tuple[str, str, str, str]:
    """Calculate target periods: Current period + 2 half-month cycles"""
    # Current period is 202506A (June 2025, first half)
    # Target should be 202508A and 202508B (August 2025)
    return "2025", "08", "2025", "08"

def map_clusters_to_store_groups(cluster_df: pd.DataFrame) -> Dict[int, str]:
    """Map cluster numbers to meaningful store group names"""
    log_progress("Mapping clusters to store group names...")
    
    unique_clusters = sorted(cluster_df['Cluster'].unique())
    cluster_mapping = {}
    for cluster_id in unique_clusters:
        cluster_mapping[cluster_id] = f"Store Group {cluster_id + 1}"
    
    log_progress(f"Created {len(cluster_mapping)} store group mappings")
    return cluster_mapping

def create_style_tag_combinations(config_df: pd.DataFrame, target_month: str = "08") -> List[Dict]:
    """Create style tag combinations from product attributes with seasonal filtering"""
    log_progress("Creating style tag combinations from product attributes...")
    
    # Filter for appropriate seasons based on target month
    if target_month in ["06", "07", "08"]:  # Summer months
        target_seasons = ['夏', '春']  # Summer and Spring
        log_progress("Filtering for Summer/Spring items (appropriate for August)")
    elif target_month in ["09", "10", "11"]:  # Autumn months  
        target_seasons = ['秋', '夏']  # Autumn and Summer
        log_progress("Filtering for Autumn/Summer items")
    elif target_month in ["12", "01", "02"]:  # Winter months
        target_seasons = ['冬', '秋']  # Winter and Autumn
        log_progress("Filtering for Winter/Autumn items")
    else:  # Spring months
        target_seasons = ['春', '冬']  # Spring and Winter
        log_progress("Filtering for Spring/Winter items")
    
    # Filter config data for appropriate seasons
    seasonal_config = config_df[config_df['season_name'].isin(target_seasons)].copy()
    log_progress(f"Filtered from {len(config_df)} to {len(seasonal_config)} records for appropriate seasons")
    
    if len(seasonal_config) == 0:
        log_progress("⚠️ No seasonal data found, using all seasons")
        seasonal_config = config_df.copy()
    
    style_combinations = []
    
    # Process each unique combination of product attributes
    grouping_cols = ['season_name', 'sex_name', 'display_location_name', 'big_class_name', 'sub_cate_name']
    
    # Group by product attributes
    grouped = seasonal_config.groupby(grouping_cols).agg({
        'str_code': 'nunique',  # Number of stores with this combination
        'sal_amt': 'sum'        # Total sales for this combination
    }).reset_index()
    
    # Filter for meaningful combinations (present in multiple stores)
    meaningful_combinations = grouped[grouped['str_code'] >= 3].copy()
    
    log_progress(f"Found {len(meaningful_combinations)} meaningful style combinations")
    
    for _, row in meaningful_combinations.iterrows():
        # Create style tag combination
        style_tags = []
        
        # Map Chinese attributes to English tags
        season_map = {'夏': 'Summer', '秋': 'Autumn', '春': 'Spring', '冬': 'Winter'}
        gender_map = {'男': 'Men', '女': 'Women', '中': 'Unisex'}
        location_map = {'前台': 'Front-store', '后场': 'Back-store'}
        
        # Add tags in order
        if row['season_name'] in season_map:
            style_tags.append(season_map[row['season_name']])
        
        if row['sex_name'] in gender_map:
            style_tags.append(gender_map[row['sex_name']])
        
        if row['display_location_name'] in location_map:
            style_tags.append(location_map[row['display_location_name']])
        
        # Add category information (keep Chinese for now)
        style_tags.append(row['big_class_name'])
        style_tags.append(row['sub_cate_name'])
        
        # Create the style tag combination string
        style_tag_combination = '[' + ', '.join(style_tags) + ']'
        
        style_combinations.append({
            'style_tags': style_tag_combination,
            'store_count': row['str_code'],
            'total_sales': row['sal_amt'],
            'season': row['season_name'],
            'gender': row['sex_name'],
            'location': row['display_location_name'],
            'category': row['big_class_name'],
            'subcategory': row['sub_cate_name']
        })
    
    return style_combinations

def generate_client_format_output(cluster_df: pd.DataFrame, consolidated_df: pd.DataFrame, 
                                 config_df: pd.DataFrame) -> pd.DataFrame:
    """Generate the client's required output format"""
    log_progress("Generating client format output...")
    
    # Get target periods
    year_a, month_a, year_b, month_b = calculate_target_periods()
    
    # Map clusters to store groups
    cluster_mapping = map_clusters_to_store_groups(cluster_df)
    
    # Create style tag combinations with seasonal filtering
    style_combinations = create_style_tag_combinations(config_df, month_a)
    
    # Generate output rows
    output_rows = []
    
    # For each cluster (store group)
    for cluster_id, store_group_name in cluster_mapping.items():
        # Get stores in this cluster
        cluster_stores = cluster_df[cluster_df['Cluster'] == cluster_id]['str_code'].tolist()
        
        if len(cluster_stores) == 0:
            continue
        
        # Filter style combinations that are relevant to this cluster
        cluster_config = config_df[config_df['str_code'].isin(cluster_stores)]
        
        if len(cluster_config) == 0:
            continue
        
        # Get top 3-5 style combinations for this cluster with seasonal filtering
        cluster_style_combos = create_style_tag_combinations(cluster_config, month_a)[:5]
        
        # Simple quantity logic for now (can be enhanced later)
        base_quantity = 4  # Default base quantity
        
        for i, style_combo in enumerate(cluster_style_combos):
            # Vary quantities slightly for different combinations
            target_quantity = max(1, base_quantity + (i % 3) - 1)
            
            # Create rows for both periods A and B
            for period, year, month in [('A', year_a, month_a), ('B', year_b, month_b)]:
                output_rows.append({
                    'Year': year,
                    'Month': month,  # Now properly formatted as "08"
                    'Period': period,
                    'Store Group Name': store_group_name,
                    'Target Style Tags': style_combo['style_tags'],
                    'Target SPU Quantity': target_quantity
                })
    
    # Convert to DataFrame
    output_df = pd.DataFrame(output_rows)
    
    log_progress(f"Generated {len(output_df)} output rows for {len(cluster_mapping)} store groups")
    return output_df

def main():
    """Main execution function"""
    start_time = datetime.now()
    log_progress("Starting Client Format Converter...")
    
    # Load input data
    try:
        log_progress("Loading input data...")
        
        # Load clustering results
        cluster_df = pd.read_csv("output/clustering_results_spu.csv", dtype={'str_code': str})
        log_progress(f"Loaded clustering data: {len(cluster_df)} stores, {cluster_df['Cluster'].nunique()} clusters")
        
        # Load consolidated results
        consolidated_df = pd.read_csv("output/consolidated_spu_rule_results.csv", dtype={'str_code': str})
        log_progress(f"Loaded consolidated results: {len(consolidated_df)} stores")
        
        # Load store configuration data
        config_df = pd.read_csv("data/api_data/store_config_data.csv", dtype={'str_code': str})
        log_progress(f"Loaded configuration data: {len(config_df)} records")
        
    except Exception as e:
        log_progress(f"Error loading data: {e}")
        return
    
    # Generate client format output
    try:
        client_output = generate_client_format_output(cluster_df, consolidated_df, config_df)
        
        # Save output
        output_file = "output/client_format_merchandise_planning.csv"
        client_output.to_csv(output_file, index=False)
        log_progress(f"Saved client format output to {output_file}")
        
        # Display sample output
        log_progress("\n" + "="*80)
        log_progress("SAMPLE OUTPUT (First 10 rows):")
        log_progress("="*80)
        print(client_output.head(10).to_string(index=False))
        
        # Summary statistics
        log_progress("\n" + "="*80)
        log_progress("OUTPUT SUMMARY:")
        log_progress("="*80)
        log_progress(f"✅ Total rows generated: {len(client_output):,}")
        log_progress(f"✅ Store groups: {client_output['Store Group Name'].nunique()}")
        log_progress(f"✅ Unique style combinations: {client_output['Target Style Tags'].nunique()}")
        log_progress(f"✅ Total SPU quantity targets: {client_output['Target SPU Quantity'].sum():,}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        log_progress(f"\n✅ Client format conversion completed in {duration:.2f} seconds")
        
    except Exception as e:
        log_progress(f"Error generating client format: {e}")
        raise

if __name__ == "__main__":
    main()
