"""
Step 13 Synthetic Test Fixtures

This module creates complete, realistic synthetic fixtures for Step 13 testing.
Fixtures are based on real data patterns but are completely synthetic.

Usage:
    from fixtures import create_complete_step13_fixtures
    create_complete_step13_fixtures(sandbox_path, period_label="202510A")
"""

import pandas as pd
import numpy as np
from pathlib import Path


def create_complete_step13_fixtures(sandbox: Path, period_label: str = "202510A"):
    """
    Create complete synthetic fixtures for Step 13 testing.
    
    This creates:
    1. Clustering data (store -> cluster mapping)
    2. SPU sales data (historical sales by store/SPU/subcategory)
    3. Rule 7-12 output files (recommendations from each rule)
    
    All data is synthetic but follows real data patterns.
    
    Args:
        sandbox: Path to sandbox directory
        period_label: Period label (e.g., "202510A")
    """
    output_dir = sandbox / "output"
    data_dir = sandbox / "data" / "api_data"
    output_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract YYYYMM from period_label
    yyyymm = period_label[:6]
    period = period_label[6:] if len(period_label) > 6 else "A"
    
    # Define synthetic stores and clusters
    stores = [f"S{i:03d}" for i in range(1, 21)]  # 20 stores
    clusters = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4]  # 5 clusters
    
    # Define realistic subcategories (Chinese apparel categories)
    subcategories = [
        "圆领T恤", "V领T恤", "POLO衫",  # T-shirts
        "直筒裤", "锥形裤", "阔腿裤", "工装裤", "束脚裤", "短裤",  # Pants
        "圆领卫衣", "连帽卫衣",  # Sweatshirts
        "羽绒马夹", "棉服",  # Outerwear
        "运动鞋", "休闲鞋"  # Shoes
    ]
    
    # Define SPU codes
    spus = [f"SPU{i:04d}" for i in range(1, 51)]  # 50 SPUs
    
    print(f"Creating fixtures for {len(stores)} stores, {len(subcategories)} subcategories, {len(spus)} SPUs")
    
    # 1. Create clustering data
    _create_clustering_data(output_dir, stores, clusters, period_label)
    
    # 2. Create SPU sales data (historical period)
    historical_period = f"{int(yyyymm)-100}A"  # Previous year, same period
    _create_spu_sales_data(data_dir, stores, subcategories, spus, historical_period)
    
    # 3. Create rule output files
    _create_rule_outputs(output_dir, stores, clusters, subcategories, spus, period_label, yyyymm, period)
    
    print(f"✅ Complete fixtures created in {sandbox}")


def _create_clustering_data(output_dir: Path, stores: list, clusters: list, period_label: str):
    """Create clustering results file."""
    clustering = pd.DataFrame({
        'str_code': stores,
        'Cluster': clusters
    })
    
    output_file = output_dir / f"clustering_results_spu_{period_label}.csv"
    clustering.to_csv(output_file, index=False)
    print(f"  ✓ Created clustering: {output_file.name} ({len(clustering)} stores)")


def _create_spu_sales_data(data_dir: Path, stores: list, subcategories: list, spus: list, period_label: str):
    """Create SPU sales data (historical)."""
    np.random.seed(42)  # For reproducibility
    
    # Create sales records for each store
    sales_data = []
    for store in stores:
        # Each store sells a random subset of subcategories
        num_subcats = np.random.randint(8, 15)
        store_subcats = np.random.choice(subcategories, size=num_subcats, replace=False)
        
        for subcat in store_subcats:
            # Each subcategory has 1-3 SPUs
            num_spus = np.random.randint(1, 4)
            subcat_spus = np.random.choice(spus, size=num_spus, replace=False)
            
            for spu in subcat_spus:
                # Generate realistic sales data
                quantity = np.random.uniform(5, 50)
                unit_price = np.random.uniform(50, 300)
                sales_amt = quantity * unit_price
                
                sales_data.append({
                    'str_code': store,
                    'str_name': f"Store_{store}",
                    'cate_name': _get_category(subcat),
                    'sub_cate_name': subcat,
                    'spu_code': spu,
                    'spu_sales_amt': sales_amt,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'investment_per_unit': unit_price
                })
    
    sales_df = pd.DataFrame(sales_data)
    output_file = data_dir / f"complete_spu_sales_{period_label}.csv"
    sales_df.to_csv(output_file, index=False)
    print(f"  ✓ Created SPU sales: {output_file.name} ({len(sales_df)} records)")


def _get_category(subcategory: str) -> str:
    """Map subcategory to category."""
    if any(x in subcategory for x in ["T恤", "POLO"]):
        return "T恤"
    elif any(x in subcategory for x in ["裤"]):
        return "裤子"
    elif any(x in subcategory for x in ["卫衣"]):
        return "卫衣"
    elif any(x in subcategory for x in ["羽绒", "棉服"]):
        return "外套"
    elif any(x in subcategory for x in ["鞋"]):
        return "鞋"
    return "其他"


def _create_rule_outputs(output_dir: Path, stores: list, clusters: list, subcategories: list, 
                         spus: list, period_label: str, yyyymm: str, period: str):
    """Create rule 7-12 output files."""
    np.random.seed(42)
    
    # Rule 7: Missing Category/SPU (most common rule)
    rule7_data = []
    for i, store in enumerate(stores):
        # Each store gets 5-10 recommendations
        num_recs = np.random.randint(5, 11)
        for _ in range(num_recs):
            subcat = np.random.choice(subcategories)
            spu = np.random.choice(spus)
            qty = np.random.randint(5, 20)
            price = np.random.uniform(50, 300)
            
            rule7_data.append({
                'str_code': store,
                'spu_code': spu,
                'sub_cate_name': subcat,
                'cluster_id': clusters[i],
                'recommended_quantity_change': qty,
                'investment_required': qty * price,
                'unit_price': price,
                'business_rationale': f"Missing {subcat} in store",
                'approval_reason': "Peer stores selling well",
                'fast_fish_compliant': True,
                'opportunity_type': "missing_category",
                'period_label': period_label,
                'target_yyyymm': yyyymm,
                'target_period': period
            })
    
    rule7_df = pd.DataFrame(rule7_data)
    rule7_file = output_dir / f"rule7_missing_spu_sellthrough_results_{period_label}.csv"
    rule7_df.to_csv(rule7_file, index=False)
    print(f"  ✓ Created Rule 7: {rule7_file.name} ({len(rule7_df)} recommendations)")
    
    # Rule 8: Imbalanced Allocation (fewer recommendations)
    rule8_data = []
    for i, store in enumerate(stores[:5]):  # Only first 5 stores
        subcat = np.random.choice(subcategories)
        spu = np.random.choice(spus)
        qty = np.random.randint(2, 8)
        price = np.random.uniform(50, 300)
        
        rule8_data.append({
            'str_code': store,
            'spu_code': spu,
            'sub_cate_name': subcat,
            'cluster_id': clusters[i],
            'recommended_quantity_change': qty,
            'investment_required': qty * price,
            'unit_price': price,
            'business_rationale': "Imbalanced allocation detected",
            'approval_reason': "Rebalance needed",
            'fast_fish_compliant': True,
            'opportunity_type': "imbalanced",
            'period_label': period_label,
            'target_yyyymm': yyyymm,
            'target_period': period
        })
    
    rule8_df = pd.DataFrame(rule8_data)
    rule8_file = output_dir / f"rule8_imbalanced_spu_results_{period_label}.csv"
    rule8_df.to_csv(rule8_file, index=False)
    print(f"  ✓ Created Rule 8: {rule8_file.name} ({len(rule8_df)} recommendations)")
    
    # Rule 9: Below Minimum (fewer recommendations)
    rule9_data = []
    for i, store in enumerate(stores[:8]):  # First 8 stores
        subcat = np.random.choice(subcategories)
        spu = np.random.choice(spus)
        qty = np.random.randint(3, 10)
        price = np.random.uniform(50, 300)
        
        rule9_data.append({
            'str_code': store,
            'spu_code': spu,
            'sub_cate_name': subcat,
            'cluster_id': clusters[i],
            'recommended_quantity_change': qty,
            'investment_required': qty * price,
            'unit_price': price,
            'business_rationale': "Below minimum threshold",
            'approval_reason': "Increase to minimum",
            'fast_fish_compliant': True,
            'opportunity_type': "below_minimum",
            'period_label': period_label,
            'target_yyyymm': yyyymm,
            'target_period': period
        })
    
    rule9_df = pd.DataFrame(rule9_data)
    rule9_file = output_dir / f"rule9_below_minimum_spu_sellthrough_results_{period_label}.csv"
    rule9_df.to_csv(rule9_file, index=False)
    print(f"  ✓ Created Rule 9: {rule9_file.name} ({len(rule9_df)} recommendations)")
    
    # Rule 10: Overcapacity (reductions)
    rule10_df = pd.DataFrame({
        'str_code': stores,
        'cluster_id': clusters,
        'rule10_spu_overcapacity': False,
        'rule10_overcapacity_count': 0,
        'rule10_total_excess_spus': 0,
        'rule10_avg_overcapacity_pct': 0.0,
        'rule10_reduction_recommended_count': 0,
        'rule10_total_quantity_reduction': 0,
        'rule10_total_cost_savings': 0.0,
        'recommended_quantity_change': 0,
        'investment_required': 0.0,
        'business_rationale': "No overcapacity detected",
        'approval_reason': "N/A",
        'fast_fish_compliant': True,
        'opportunity_type': "overcapacity",
        'period_label': period_label,
        'target_yyyymm': yyyymm,
        'target_period': period
    })
    rule10_file = output_dir / f"rule10_smart_overcapacity_results_{period_label}.csv"
    rule10_df.to_csv(rule10_file, index=False)
    print(f"  ✓ Created Rule 10: {rule10_file.name} ({len(rule10_df)} records)")
    
    # Rule 11: Missed Sales Opportunity
    rule11_df = pd.DataFrame({
        'str_code': stores,
        'cluster_id': clusters,
        'rule11_missed_sales_opportunity': False,
        'rule11_missing_top_performers_count': 0,
        'rule11_avg_opportunity_score': 0.0,
        'rule11_potential_sales_increase': 0.0,
        'rule11_total_recommended_period_sales': 0.0,
        'rule11_total_recommended_period_qty': 0,
        'investment_required': 0.0,
        'recommended_quantity_change': 0,
        'business_rationale': "No missed opportunities",
        'approval_reason': "N/A",
        'fast_fish_compliant': True,
        'opportunity_type': "missed_sales",
        'period_label': period_label,
        'target_yyyymm': yyyymm,
        'target_period': period
    })
    rule11_file = output_dir / f"rule11_improved_missed_sales_opportunity_spu_results_{period_label}.csv"
    rule11_df.to_csv(rule11_file, index=False)
    print(f"  ✓ Created Rule 11: {rule11_file.name} ({len(rule11_df)} records)")
    
    # Rule 12: Sales Performance
    rule12_df = pd.DataFrame({
        'str_code': stores,
        'cluster_id': clusters,
        'avg_opportunity_z_score': 0.0,
        'total_opportunity_value': 0.0,
        'categories_analyzed': 0,
        'top_quartile_categories': 0,
        'total_quantity_increase_needed': 0,
        'total_investment_required': 0.0,
        'total_current_quantity': 0,
        'quantity_opportunities_count': 0,
        'has_quantity_recommendations': False,
        'store_performance_level': "average",
        'rule12_top_performer': False,
        'rule12_performing_well': False,
        'rule12_some_opportunity': False,
        'rule12_good_opportunity': False,
        'rule12_major_opportunity': False,
        'rule12_quantity_increase_recommended': 0,
        'rule12_description': "No significant opportunities",
        'rule12_analysis_method': "z_score",
        'rule_flag': False,
        'opportunity_type': "sales_performance",
        'unit_price': 0.0,
        'fast_fish_compliant': True,
        'business_rationale': "Performance adequate",
        'approval_reason': "N/A",
        'investment_required': 0.0,
        'recommended_quantity_change': 0,
        'period_label': period_label,
        'target_yyyymm': yyyymm,
        'target_period': period
    })
    rule12_file = output_dir / f"rule12_sales_performance_spu_results_{period_label}.csv"
    rule12_df.to_csv(rule12_file, index=False)
    print(f"  ✓ Created Rule 12: {rule12_file.name} ({len(rule12_df)} records)")


if __name__ == "__main__":
    # Test fixture creation
    from pathlib import Path
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        sandbox = Path(tmpdir) / "test_sandbox"
        sandbox.mkdir()
        create_complete_step13_fixtures(sandbox, "202510A")
        print("\n✅ Fixture creation test successful!")
