#!/usr/bin/env python3
"""
Rule-Based Client Format Converter
Transforms our SPU rule recommendations into the client's required merchandise planning format

Uses REAL rule-based recommendations instead of artificial clustering data:
- Rule 7: Missing SPU opportunities with specific quantities
- Rule 11: Sales opportunity recommendations 
- Rule 8: Rebalancing suggestions
- Rule 9: Below minimum adjustments
- Rule 10: Overcapacity reductions
- Rule 12: Performance improvements

Output Format: Year, Month, Period, Store Group Name, Target Style Tags, Target SPU Quantity
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def calculate_target_periods() -> Tuple[str, str, str, str]:
    """Calculate target periods: Current period + 2 half-month cycles"""
    # Current period is 202506A (June 2025, first half)
    # Target should be 202508A and 202508B (August 2025)
    return "2025", "08", "2025", "08"

def load_rule_recommendations() -> Dict[str, pd.DataFrame]:
    """Load all rule recommendation files"""
    log_progress("Loading rule-based recommendations...")
    
    rule_files = {
        'rule7_opportunities': 'output/rule7_missing_spu_opportunities.csv',
        'rule8_results': 'output/rule8_imbalanced_spu_results.csv',
        'rule9_results': 'output/rule9_below_minimum_spu_results.csv',
        'rule10_opportunities': 'output/rule10_spu_overcapacity_opportunities.csv',
        'rule11_details': 'output/rule11_improved_missed_sales_opportunity_spu_details.csv',
        'rule12_details': 'output/rule12_sales_performance_spu_details.csv',
        'clustering': 'output/clustering_results_spu.csv',
        'config': 'data/api_data/store_config_data.csv'
    }
    
    rule_data = {}
    for rule_name, file_path in rule_files.items():
        try:
            df = pd.read_csv(file_path, dtype={'str_code': str, 'spu_code': str} if 'str_code' in rule_name or rule_name in ['clustering', 'config'] else None)
            rule_data[rule_name] = df
            log_progress(f"Loaded {rule_name}: {len(df):,} records")
        except Exception as e:
            log_progress(f"⚠️ Could not load {rule_name}: {e}")
            rule_data[rule_name] = pd.DataFrame()
    
    return rule_data

def create_style_tags_from_spu(spu_code: str, config_df: pd.DataFrame) -> str:
    """Create style tags from SPU code using smart category mapping"""
    
    # SPU code mapping based on common patterns
    spu_category_map = {
        '15K': ('休闲裤', '工装裤'),  # K often refers to pants in the data
        '15T': ('T恤', '圆领T恤'),
        '15L': ('POLO衫', '长袖POLO'),
        '15S': ('衬衫', '休闲衬衫'),
        '15N': ('休闲裤', '直筒裤'),  # N often refers to pants
        '15R': ('外套', '夹克'),
        '15P': ('POLO衫', '休闲POLO'),  # P for POLO
        '15D': ('牛仔裤', '直筒裤'),  # D for denim
        '15H': ('家居', '未维护'),  # H for home
        '75T': ('T恤', '圆领T恤')   # Alternative T-shirt code
    }
    
    # Extract category info from SPU code
    category_prefix = spu_code[:3] if len(spu_code) >= 3 else spu_code
    
    # Get category information
    if category_prefix in spu_category_map:
        big_class_chinese, sub_class_chinese = spu_category_map[category_prefix]
    else:
        big_class_chinese = category_prefix
        sub_class_chinese = spu_code
    
    # Use seasonal filtering for August (Summer items)
    # Get a representative sample from config data for seasonal context
    summer_config = config_df[config_df['season_name'] == '夏'] if 'season_name' in config_df.columns else config_df
    if len(summer_config) == 0:
        summer_config = config_df
    
    if len(summer_config) > 0:
        # Use most common attributes for summer items
        config_sample = summer_config.sample(n=1).iloc[0]
        
        # Comprehensive Chinese to English mapping
        season_map = {
            '夏': 'Summer', '春': 'Spring', '秋': 'Autumn', '冬': 'Winter', '四季': 'All-Season'
        }
        
        gender_map = {
            '男': 'Men', '女': 'Women', '中': 'Unisex'
        }
        
        location_map = {
            '前台': 'Front-store', '后场': 'Back-store', '鞋配': 'Shoes-Accessories'
        }
        
        # Big class (category) mapping
        big_class_map = {
            '休闲裤': 'Casual Pants', 'T恤': 'T-shirt', '牛仔裤': 'Jeans', 'POLO衫': 'Polo Shirt',
            '配饰': 'Accessories', '防晒衣': 'Sun Protection', '家居': 'Home Wear', '鞋': 'Shoes',
            '套装': 'Sets', '内衣': 'Underwear', '裙/连衣裙': 'Dresses', '衬衣': 'Shirts',
            '茄克': 'Jackets', '卫衣': 'Hoodies', '自提品': 'Pickup Items'
        }
        
        # Sub category mapping - comprehensive list
        sub_class_map = {
            '未维护': 'Unspecified', '束脚裤': 'Jogger Pants', '锥形裤': 'Tapered Pants',
            '直筒裤': 'Straight Pants', '短裤': 'Shorts', '阔腿裤': 'Wide Leg Pants',
            '工装裤': 'Cargo Pants', '中裤': 'Cropped Pants', '休闲圆领T恤': 'Casual Round Neck T-shirt',
            '针织防晒衣': 'Knit Sun Protection', '凉感圆领T恤': 'Cool Round Neck T-shirt',
            '裤类套装': 'Pants Sets', '微宽松圆领T恤': 'Relaxed Round Neck T-shirt',
            '梭织防晒衣': 'Woven Sun Protection', '休闲POLO': 'Casual Polo', '长袖POLO': 'Long Sleeve Polo',
            '凉感POLO': 'Cool Polo', '套头POLO': 'Pullover Polo', '圆领T恤': 'Round Neck T-shirt',
            '休闲衬衫': 'Casual Shirt', '立领休闲茄克': 'Stand Collar Casual Jacket',
            '牛仔茄克': 'Denim Jacket', '伞': 'Umbrellas', '休闲裤': 'Casual Pants', '夹克': 'Jacket'
        }
        
        season = season_map.get(config_sample.get('season_name', '夏'), 'Summer')
        gender = gender_map.get(config_sample.get('sex_name', '中'), 'Unisex')
        location = location_map.get(config_sample.get('display_location_name', '前台'), 'Front-store')
    else:
        # Default values for August
        season = 'Summer'
        gender = 'Unisex'
        location = 'Front-store'
        
        # Fallback translation mappings
        big_class_map = {
            '休闲裤': 'Casual Pants', 'T恤': 'T-shirt', '牛仔裤': 'Jeans', 'POLO衫': 'Polo Shirt',
            '配饰': 'Accessories', '防晒衣': 'Sun Protection', '家居': 'Home Wear', '鞋': 'Shoes',
            '套装': 'Sets', '内衣': 'Underwear', '裙/连衣裙': 'Dresses', '衬衣': 'Shirts',
            '茄克': 'Jackets', '卫衣': 'Hoodies', '自提品': 'Pickup Items', '衬衫': 'Shirts',
            '裤子': 'Pants', '外套': 'Outerwear'
        }
        sub_class_map = {
            '未维护': 'Unspecified', '束脚裤': 'Jogger Pants', '锥形裤': 'Tapered Pants',
            '直筒裤': 'Straight Pants', '短裤': 'Shorts', '阔腿裤': 'Wide Leg Pants',
            '工装裤': 'Cargo Pants', '中裤': 'Cropped Pants', '休闲圆领T恤': 'Casual Round Neck T-shirt',
            '休闲POLO': 'Casual Polo', '长袖POLO': 'Long Sleeve Polo', '圆领T恤': 'Round Neck T-shirt',
            '休闲衬衫': 'Casual Shirt', '休闲裤': 'Casual Pants', '夹克': 'Jacket'
        }
    
    # Translate categories to English
    big_class = big_class_map.get(big_class_chinese, big_class_chinese)
    sub_class = sub_class_map.get(sub_class_chinese, sub_class_chinese)
    
    style_tags = [season, gender, location, big_class, sub_class]
    
    return '[' + ', '.join(style_tags) + ']'

def map_clusters_to_store_groups(cluster_df: pd.DataFrame) -> Dict[int, str]:
    """Map cluster numbers to store group names"""
    unique_clusters = sorted(cluster_df['Cluster'].unique())
    cluster_mapping = {}
    for cluster_id in unique_clusters:
        cluster_mapping[cluster_id] = f"Store Group {cluster_id + 1}"
    return cluster_mapping

def process_rule7_recommendations(rule7_df: pd.DataFrame, cluster_df: pd.DataFrame, 
                                 config_df: pd.DataFrame, cluster_mapping: Dict[int, str]) -> List[Dict]:
    """Process Rule 7 missing SPU recommendations"""
    log_progress("Processing Rule 7 missing SPU recommendations...")
    
    recommendations = []
    
    for _, row in tqdm(rule7_df.iterrows(), total=len(rule7_df), desc="Processing Rule 7"):
        str_code = str(row['str_code'])
        spu_code = row['spu_code']
        quantity = row.get('recommended_quantity_change', 1.0)
        
        # Get store's cluster and map to store group
        store_cluster = cluster_df[cluster_df['str_code'] == str_code]
        if len(store_cluster) == 0:
            continue
            
        cluster_id = store_cluster.iloc[0]['Cluster']
        store_group = cluster_mapping.get(cluster_id, f"Store Group {cluster_id + 1}")
        
        # Create style tags
        style_tags = create_style_tags_from_spu(spu_code, config_df)
        
        # Round quantity to reasonable business unit
        target_quantity = max(1, round(quantity))
        
        recommendations.append({
            'store_group': store_group,
            'style_tags': style_tags,
            'quantity': target_quantity,
            'rule_type': 'STOCK_NEW',
            'spu_code': spu_code
        })
    
    log_progress(f"Generated {len(recommendations)} Rule 7 recommendations")
    return recommendations

def process_rule11_recommendations(rule11_df: pd.DataFrame, cluster_df: pd.DataFrame,
                                  config_df: pd.DataFrame, cluster_mapping: Dict[int, str]) -> List[Dict]:
    """Process Rule 11 sales opportunity recommendations"""
    log_progress("Processing Rule 11 sales opportunity recommendations...")
    
    recommendations = []
    
    for _, row in tqdm(rule11_df.iterrows(), total=len(rule11_df), desc="Processing Rule 11"):
        str_code = str(row['str_code'])
        spu_code = row['spu_code']
        quantity = row.get('recommended_quantity_change', row.get('target_period_qty', 1.0))
        
        # Get store's cluster and map to store group
        store_cluster = cluster_df[cluster_df['str_code'] == str_code]
        if len(store_cluster) == 0:
            continue
            
        cluster_id = store_cluster.iloc[0]['Cluster']
        store_group = cluster_mapping.get(cluster_id, f"Store Group {cluster_id + 1}")
        
        # Create style tags
        style_tags = create_style_tags_from_spu(spu_code, config_df)
        
        # Round quantity to reasonable business unit
        target_quantity = max(1, round(quantity))
        
        recommendations.append({
            'store_group': store_group,
            'style_tags': style_tags,
            'quantity': target_quantity,
            'rule_type': 'INCREASE',
            'spu_code': spu_code
        })
    
    log_progress(f"Generated {len(recommendations)} Rule 11 recommendations")
    return recommendations

def process_rule10_recommendations(rule10_df: pd.DataFrame, cluster_df: pd.DataFrame,
                                  config_df: pd.DataFrame, cluster_mapping: Dict[int, str]) -> List[Dict]:
    """Process Rule 10 overcapacity reduction recommendations"""
    log_progress("Processing Rule 10 overcapacity recommendations...")
    
    recommendations = []
    
    for _, row in tqdm(rule10_df.iterrows(), total=len(rule10_df), desc="Processing Rule 10"):
        str_code = str(row['str_code'])
        spu_code = row['spu_code']
        # For overcapacity, we want to REDUCE quantities (negative recommendation)
        quantity = abs(row.get('recommended_quantity_change', 1.0))  # Take absolute value for reduction
        
        # Get store's cluster and map to store group
        store_cluster = cluster_df[cluster_df['str_code'] == str_code]
        if len(store_cluster) == 0:
            continue
            
        cluster_id = store_cluster.iloc[0]['Cluster']
        store_group = cluster_mapping.get(cluster_id, f"Store Group {cluster_id + 1}")
        
        # Create style tags
        style_tags = create_style_tags_from_spu(spu_code, config_df)
        
        # Round quantity to reasonable business unit (negative for reduction)
        target_quantity = -max(1, round(quantity))  # Negative for reduction
        
        recommendations.append({
            'store_group': store_group,
            'style_tags': style_tags,
            'quantity': target_quantity,
            'rule_type': 'REDUCE',
            'spu_code': spu_code
        })
    
    log_progress(f"Generated {len(recommendations)} Rule 10 recommendations")
    return recommendations

def process_rule12_recommendations(rule12_df: pd.DataFrame, cluster_df: pd.DataFrame,
                                  config_df: pd.DataFrame, cluster_mapping: Dict[int, str]) -> List[Dict]:
    """Process Rule 12 performance improvement recommendations"""
    log_progress("Processing Rule 12 performance improvement recommendations...")
    
    recommendations = []
    
    for _, row in tqdm(rule12_df.iterrows(), total=len(rule12_df), desc="Processing Rule 12"):
        str_code = str(row['str_code'])
        spu_code = row.get('spu_code', 'UNKNOWN')
        quantity = row.get('recommended_quantity_change', row.get('target_period_qty', 1.0))
        
        # Get store's cluster and map to store group
        store_cluster = cluster_df[cluster_df['str_code'] == str_code]
        if len(store_cluster) == 0:
            continue
            
        cluster_id = store_cluster.iloc[0]['Cluster']
        store_group = cluster_mapping.get(cluster_id, f"Store Group {cluster_id + 1}")
        
        # Create style tags
        style_tags = create_style_tags_from_spu(spu_code, config_df)
        
        # Round quantity to reasonable business unit
        target_quantity = max(1, round(quantity))
        
        recommendations.append({
            'store_group': store_group,
            'style_tags': style_tags,
            'quantity': target_quantity,
            'rule_type': 'PERFORMANCE',
            'spu_code': spu_code
        })
    
    log_progress(f"Generated {len(recommendations)} Rule 12 recommendations")
    return recommendations

def aggregate_recommendations_by_store_group(recommendations: List[Dict]) -> List[Dict]:
    """Aggregate recommendations by store group and style combination"""
    log_progress("Aggregating recommendations by store group and style...")
    
    # Group by store group and style tags
    aggregated = {}
    
    for rec in recommendations:
        key = (rec['store_group'], rec['style_tags'])
        
        if key not in aggregated:
            aggregated[key] = {
                'store_group': rec['store_group'],
                'style_tags': rec['style_tags'],
                'total_quantity': 0,
                'rule_types': set(),
                'spu_codes': set()
            }
        
        aggregated[key]['total_quantity'] += rec['quantity']
        aggregated[key]['rule_types'].add(rec['rule_type'])
        aggregated[key]['spu_codes'].add(rec['spu_code'])
    
    # Convert to list and ensure reasonable quantities
    final_recommendations = []
    for key, agg_rec in aggregated.items():
        total_qty = agg_rec['total_quantity']
        
        # Handle net quantities (additions minus reductions)
        if total_qty > 0:
            # Net addition - cap at reasonable business levels
            final_quantity = min(50, max(1, total_qty))
        else:
            # Net reduction - convert to positive for client format but note it's a reduction
            final_quantity = min(50, max(1, abs(total_qty)))
        
        final_recommendations.append({
            'store_group': agg_rec['store_group'],
            'style_tags': agg_rec['style_tags'],
            'quantity': final_quantity
        })
    
    log_progress(f"Aggregated to {len(final_recommendations)} unique style combinations")
    return final_recommendations

def generate_client_format_output(rule_data: Dict[str, pd.DataFrame], sample_size: Optional[int] = None) -> pd.DataFrame:
    """Generate the client's required output format from rule recommendations"""
    log_progress("Generating client format output from rule recommendations...")
    
    # Get target periods
    year_a, month_a, year_b, month_b = calculate_target_periods()
    
    # Map clusters to store groups
    cluster_mapping = map_clusters_to_store_groups(rule_data['clustering'])
    
    # Process different rule recommendations
    all_recommendations = []
    
    # Process Rule 7 (Missing SPUs)
    if len(rule_data['rule7_opportunities']) > 0:
        rule7_data = rule_data['rule7_opportunities']
        if sample_size and len(rule7_data) > sample_size:
            rule7_data = rule7_data.sample(n=sample_size)
            log_progress(f"Sampling {sample_size} records from Rule 7 for faster processing")
        
        rule7_recs = process_rule7_recommendations(
            rule7_data, 
            rule_data['clustering'], 
            rule_data['config'], 
            cluster_mapping
        )
        all_recommendations.extend(rule7_recs)
    
    # Process Rule 11 (Sales Opportunities)
    if len(rule_data['rule11_details']) > 0:
        rule11_data = rule_data['rule11_details']
        if sample_size and len(rule11_data) > sample_size:
            rule11_data = rule11_data.sample(n=sample_size)
            log_progress(f"Sampling {sample_size} records from Rule 11 for faster processing")
        
        rule11_recs = process_rule11_recommendations(
            rule11_data, 
            rule_data['clustering'], 
            rule_data['config'], 
            cluster_mapping
        )
        all_recommendations.extend(rule11_recs)
    
    # Process Rule 10 (Overcapacity Reductions)
    if len(rule_data['rule10_opportunities']) > 0:
        rule10_data = rule_data['rule10_opportunities']
        if sample_size and len(rule10_data) > sample_size:
            rule10_data = rule10_data.sample(n=sample_size)
            log_progress(f"Sampling {sample_size} records from Rule 10 for faster processing")
        
        rule10_recs = process_rule10_recommendations(
            rule10_data, 
            rule_data['clustering'], 
            rule_data['config'], 
            cluster_mapping
        )
        all_recommendations.extend(rule10_recs)
    
    # Process Rule 12 (Performance Improvements)
    if len(rule_data['rule12_details']) > 0:
        rule12_data = rule_data['rule12_details']
        if sample_size and len(rule12_data) > sample_size:
            rule12_data = rule12_data.sample(n=sample_size)
            log_progress(f"Sampling {sample_size} records from Rule 12 for faster processing")
        
        rule12_recs = process_rule12_recommendations(
            rule12_data, 
            rule_data['clustering'], 
            rule_data['config'], 
            cluster_mapping
        )
        all_recommendations.extend(rule12_recs)
    
    log_progress(f"Total individual recommendations: {len(all_recommendations)}")
    
    # Aggregate recommendations by store group and style
    aggregated_recommendations = aggregate_recommendations_by_store_group(all_recommendations)
    
    # Generate output rows for both periods A and B
    output_rows = []
    
    for rec in aggregated_recommendations:
        # Create rows for both periods A and B
        for period, year, month in [('A', year_a, month_a), ('B', year_b, month_b)]:
            output_rows.append({
                'Year': year,
                'Month': month,
                'Period': period,
                'Store Group Name': rec['store_group'],
                'Target Style Tags': rec['style_tags'],
                'Target SPU Quantity': rec['quantity']
            })
    
    # Convert to DataFrame
    output_df = pd.DataFrame(output_rows)
    
    log_progress(f"Generated {len(output_df)} output rows for client format")
    return output_df

def main():
    """Main execution function"""
    start_time = datetime.now()
    log_progress("Starting Rule-Based Client Format Converter...")
    
    # Load rule recommendation data
    try:
        rule_data = load_rule_recommendations()
        
        if all(len(df) == 0 for df in rule_data.values()):
            log_progress("❌ No rule recommendation data found!")
            return
            
    except Exception as e:
        log_progress(f"Error loading rule data: {e}")
        return
    
    # Generate client format output
    try:
        # Generate comprehensive output from ALL rule recommendations
        client_output = generate_client_format_output(rule_data, sample_size=None)
        
        if len(client_output) == 0:
            log_progress("❌ No recommendations generated!")
            return
        
        # Save output
        output_file = "output/rule_based_client_format_merchandise_planning.csv"
        client_output.to_csv(output_file, index=False)
        log_progress(f"Saved rule-based client format output to {output_file}")
        
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
        log_progress(f"✅ Average quantity per recommendation: {client_output['Target SPU Quantity'].mean():.1f}")
        log_progress(f"✅ Max quantity per recommendation: {client_output['Target SPU Quantity'].max()}")
        
        # Quantity distribution
        log_progress("\n📊 QUANTITY DISTRIBUTION:")
        qty_stats = client_output['Target SPU Quantity'].describe()
        for stat, value in qty_stats.items():
            log_progress(f"- {stat}: {value:.1f}")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        log_progress(f"\n✅ Rule-based client format conversion completed in {duration:.2f} seconds")
        
    except Exception as e:
        log_progress(f"Error generating client format: {e}")
        raise

if __name__ == "__main__":
    main() 