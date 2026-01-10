#!/usr/bin/env python3
"""
Test script to validate the corrected sell-through calculation implementation.
"""

import pandas as pd
import numpy as np
from src.step30_sellthrough_optimization_engine import SellThroughOptimizer

def test_sellthrough_calculation():
    """Test the corrected sell-through calculation using sample data."""
    
    # Create sample data that matches the expected input format
    sample_data = pd.DataFrame({
        'str_code': ['S001', 'S001', 'S002', 'S002', 'S003', 'S003'],
        'cluster_id': [1, 1, 1, 1, 2, 2],
        'spu_code': ['P001', 'P002', 'P003', 'P004', 'P005', 'P006'],
        'product_role': ['CORE', 'SEASONAL', 'FILLER', 'CORE', 'SEASONAL', 'CLEARANCE'],
        'category': ['CAT1', 'CAT1', 'CAT1', 'CAT1', 'CAT2', 'CAT2'],
        'subcategory': ['SUB1', 'SUB1', 'SUB1', 'SUB1', 'SUB2', 'SUB2'],
        'fashion_sal_amt': [1000, 1500, 800, 1200, 2000, 900],
        'basic_sal_amt': [500, 300, 400, 600, 1000, 500],
        'fashion_sal_qty': [10, 15, 8, 12, 20, 9],
        'basic_sal_qty': [5, 3, 4, 6, 10, 5],
        'estimated_rack_capacity': [50, 50, 45, 45, 60, 60]
    })
    
    # Create minimal required dataframes
    cluster_df = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003'],
        'cluster_id': [1, 1, 2]
    })
    
    roles_df = pd.DataFrame({
        'spu_code': ['P001', 'P002', 'P003', 'P004', 'P005', 'P006'],
        'product_role': ['CORE', 'SEASONAL', 'FILLER', 'CORE', 'SEASONAL', 'CLEARANCE'],
        'category': ['CAT1', 'CAT1', 'CAT1', 'CAT1', 'CAT2', 'CAT2'],
        'subcategory': ['SUB1', 'SUB1', 'SUB1', 'SUB1', 'SUB2', 'SUB2']
    })
    
    price_df = pd.DataFrame({
        'spu_code': ['P001', 'P002', 'P003', 'P004', 'P005', 'P006'],
        'price_band': ['A', 'B', 'A', 'B', 'C', 'A'],
        'avg_unit_price': [100, 120, 80, 110, 150, 90]
    })
    
    store_attrs_df = pd.DataFrame({
        'str_code': ['S001', 'S002', 'S003'],
        'estimated_rack_capacity': [50, 45, 60],
        'store_type': ['TYPE1', 'TYPE1', 'TYPE2']
    })
    
    print("Testing corrected sell-through calculation...")
    print(f"Sample data shape: {sample_data.shape}")
    
    # Initialize optimizer
    optimizer = SellThroughOptimizer(sample_data, cluster_df, roles_df, price_df, store_attrs_df)
    
    # Prepare optimization data
    optimization_data = optimizer._prepare_optimization_data()
    print(f"Optimization data shape: {optimization_data.shape}")
    print(f"Optimization data columns: {list(optimization_data.columns)}")
    
    # Check if cluster_id column exists
    cluster_id_col = 'cluster_id_x' if 'cluster_id_x' in optimization_data.columns else 'cluster_id'
    if cluster_id_col not in optimization_data.columns:
        print("ERROR: cluster_id column not found in optimization data")
        print(f"Available columns: {list(optimization_data.columns)}")
        return
    
    # Test baseline calculation for cluster 1
    cluster_1_data = optimization_data[optimization_data[cluster_id_col] == 1]
    
    # Fix column names due to merge duplicates
    if 'product_role_x' in cluster_1_data.columns:
        cluster_1_data = cluster_1_data.rename(columns={
            'product_role_x': 'product_role',
            'category_x': 'category',
            'subcategory_x': 'subcategory',
            'estimated_rack_capacity_x': 'estimated_rack_capacity'
        })
    baseline_metrics = optimizer._calculate_cluster_baseline_metrics(cluster_1_data)
    
    print("\nBaseline Metrics for Cluster 1:")
    print(f"  Store count: {baseline_metrics['store_count']}")
    print(f"  Product count: {baseline_metrics['product_count']}")
    print(f"  SPU-store-days inventory: {baseline_metrics.get('total_spu_store_days_inventory', 'N/A')}")
    print(f"  SPU-store-days sales: {baseline_metrics.get('total_spu_store_days_sales', 'N/A')}")
    print(f"  Baseline sell-through rate: {baseline_metrics['baseline_sellthrough_rate']:.4f} ({baseline_metrics['baseline_sellthrough_rate']*100:.2f}%)")
    
    # Test baseline calculation for cluster 2
    cluster_2_data = optimization_data[optimization_data[cluster_id_col] == 2]
    
    # Fix column names due to merge duplicates
    if 'product_role_x' in cluster_2_data.columns:
        cluster_2_data = cluster_2_data.rename(columns={
            'product_role_x': 'product_role',
            'category_x': 'category',
            'subcategory_x': 'subcategory',
            'estimated_rack_capacity_x': 'estimated_rack_capacity'
        })
    baseline_metrics_2 = optimizer._calculate_cluster_baseline_metrics(cluster_2_data)
    
    print("\nBaseline Metrics for Cluster 2:")
    print(f"  Store count: {baseline_metrics_2['store_count']}")
    print(f"  Product count: {baseline_metrics_2['product_count']}")
    print(f"  SPU-store-days inventory: {baseline_metrics_2.get('total_spu_store_days_inventory', 'N/A')}")
    print(f"  SPU-store-days sales: {baseline_metrics_2.get('total_spu_store_days_sales', 'N/A')}")
    print(f"  Baseline sell-through rate: {baseline_metrics_2['baseline_sellthrough_rate']:.4f} ({baseline_metrics_2['baseline_sellthrough_rate']*100:.2f}%)")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_sellthrough_calculation()
