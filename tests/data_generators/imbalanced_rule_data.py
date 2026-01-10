"""
Data generators for imbalanced rule tests.

This module provides functions to generate test data for imbalanced rule testing,
following the project's test requirements and data structure guidelines.
"""
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from pathlib import Path


def generate_base_cluster_data(n_stores: int = 20) -> pd.DataFrame:
    """Generate base cluster data for testing.
    
    Args:
        n_stores: Number of stores to generate data for
        
    Returns:
        DataFrame with columns: ['str_code', 'cluster_id', 'store_name']
    """
    np.random.seed(42)
    return pd.DataFrame({
        'str_code': [f'store_{i:03d}' for i in range(1, n_stores + 1)],
        'cluster_id': [f'cluster_{i%3 + 1}' for i in range(n_stores)],
        'store_name': [f'Store {i}' for i in range(1, n_stores + 1)]
    })


def generate_sales_data(n_stores: int = 10, n_products: int = 5) -> pd.DataFrame:
    """Generate sales data for testing.
    
    Args:
        n_stores: Number of stores
        n_products: Number of products per store
        
    Returns:
        DataFrame with sales data
    """
    np.random.seed(42)
    data = []
    
    for store_id in range(1, n_stores + 1):
        for product_id in range(1, n_products + 1):
            unit_price = np.random.uniform(20, 150)
            base_qty = np.random.randint(1, 10)
            fashion_qty = np.random.randint(1, 5)
            total_qty = base_qty + fashion_qty
            
            data.append({
                'str_code': f'store_{store_id:03d}',
                'spu_code': f'spu_{product_id:03d}',
                'sub_cate_name': f'category_{product_id}',
                'cate_name': f'category_{product_id // 2 + 1}',
                'sal_amt': unit_price * total_qty,
                'sal_qty': total_qty,
                'unit_price': unit_price,
                'sty_sal_amt': unit_price * total_qty,
                'base_sal_qty': base_qty,
                'fashion_sal_qty': fashion_qty,
                'target_qty': total_qty,
                'current_qty': total_qty,
                'store_name': f'Store {store_id}',
                'region': 'North' if store_id <= 5 else 'South'
            })
    
    return pd.DataFrame(data)


def generate_quantity_data(n_stores: int = 10, n_products: int = 5) -> pd.DataFrame:
    """Generate quantity data for testing.
    
    Args:
        n_stores: Number of stores
        n_products: Number of products
        
    Returns:
        DataFrame with quantity data
    """
    np.random.seed(42)
    data = []
    
    for store_id in range(1, n_stores + 1):
        for product_id in range(1, n_products + 1):
            data.append({
                'str_code': f'store_{store_id:03d}',
                'spu_code': f'spu_{product_id:03d}',
                'current_quantity': np.random.randint(1, 100),
                'min_quantity': np.random.randint(1, 50),
                'max_quantity': np.random.randint(50, 200)
            })
    
    return pd.DataFrame(data)


def save_test_data(output_dir: Path):
    """Save test data to the specified directory.
    
    Args:
        output_dir: Directory to save test data
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate and save base data
    cluster_data = generate_base_cluster_data()
    sales_data = generate_sales_data()
    quantity_data = generate_quantity_data()
    
    cluster_data.to_csv(output_dir / 'base' / 'cluster_data.csv', index=False)
    sales_data.to_csv(output_dir / 'base' / 'sales_data.csv', index=False)
    quantity_data.to_csv(output_dir / 'base' / 'quantity_data.csv', index=False)
    
    # Generate and save scenario data
    # Single cluster scenario
    single_cluster = cluster_data.copy()
    single_cluster['cluster_id'] = 'A'
    single_cluster.to_csv(output_dir / 'scenarios' / 'single_cluster' / 'cluster_data.csv', index=False)
    
    # Extreme Z-scores scenario
    extreme_sales = sales_data.copy()
    extreme_sales.loc[extreme_sales['spu_code'] == 'spu_001', 'sal_qty'] *= 100
    extreme_sales.to_csv(output_dir / 'scenarios' / 'extreme_z_scores' / 'sales_data.csv', index=False)
    
    # Low variance scenario
    low_var_quantity = quantity_data.copy()
    low_var_quantity['current_quantity'] = 10
    low_var_quantity['min_quantity'] = 9
    low_var_quantity['max_quantity'] = 11
    low_var_quantity.to_csv(output_dir / 'scenarios' / 'low_variance' / 'quantity_data.csv', index=False)


if __name__ == "__main__":
    test_data_dir = Path(__file__).parent.parent / 'step08_imbalanced_rule' / 'test_data'
    save_test_data(test_data_dir)
