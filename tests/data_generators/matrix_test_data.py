"""
Matrix test data generator for Step 3 testing.

This module provides utilities for generating test data for matrix preparation testing.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import os

def generate_test_store_coordinates(num_stores: int = 50) -> pd.DataFrame:
    """
    Generate test store coordinates data.
    
    Args:
        num_stores: Number of stores to generate
        
    Returns:
        DataFrame with store coordinates
    """
    np.random.seed(42)  # For reproducible results
    
    stores = []
    for i in range(1, num_stores + 1):
        store_code = f"TEST{i:03d}"
        # Generate coordinates around Beijing area
        longitude = 116.4074 + np.random.normal(0, 0.1)  # Around Beijing
        latitude = 39.9042 + np.random.normal(0, 0.1)    # Around Beijing
        
        stores.append({
            'str_code': store_code,
            'longitude': round(longitude, 6),
            'latitude': round(latitude, 6)
        })
    
    return pd.DataFrame(stores)

def generate_test_category_data(stores: List[str], num_categories: int = 20) -> pd.DataFrame:
    """
    Generate test category sales data.
    
    Args:
        stores: List of store codes
        num_categories: Number of categories to generate
        
    Returns:
        DataFrame with category sales data
    """
    np.random.seed(42)
    
    data = []
    categories = [f"CAT{i:02d}" for i in range(1, num_categories + 1)]
    
    for store in stores:
        for category in categories:
            # Generate realistic sales amounts
            base_sales = np.random.lognormal(8, 1)  # Log-normal distribution for sales
            
            data.append({
                'str_code': store,
                'str_name': f"Store {store}",
                'cate_name': category,
                'sub_cate_name': f"{category}_SUB",
                'sal_amt': round(base_sales, 2)
            })
    
    return pd.DataFrame(data)

def generate_test_spu_data(stores: List[str], num_spus: int = 200) -> pd.DataFrame:
    """
    Generate test SPU sales data.
    
    Args:
        stores: List of store codes
        num_spus: Number of SPUs to generate
        
    Returns:
        DataFrame with SPU sales data
    """
    np.random.seed(42)
    
    data = []
    spus = [f"SPU{i:04d}" for i in range(1, num_spus + 1)]
    
    for store in stores:
        # Each store sells a random subset of SPUs
        store_spus = np.random.choice(spus, size=np.random.randint(50, 150), replace=False)
        
        for spu in store_spus:
            # Generate realistic SPU sales and quantities
            spu_sales = np.random.lognormal(6, 0.8)
            quantity = np.random.poisson(10) + 1
            
            data.append({
                'str_code': store,
                'str_name': f"Store {store}",
                'cate_name': f"CAT{(int(spu[3:]) % 20) + 1:02d}",
                'sub_cate_name': f"CAT{(int(spu[3:]) % 20) + 1:02d}_SUB",
                'spu_code': spu,
                'spu_sales_amt': round(spu_sales, 2),
                'quantity': quantity
            })
    
    return pd.DataFrame(data)

def save_test_data(output_dir: str = "tests/test_data") -> None:
    """
    Save all test data to files for testing.
    
    Args:
        output_dir: Directory to save test data
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate test data
    stores_df = generate_test_store_coordinates(50)
    category_df = generate_test_category_data(stores_df['str_code'].tolist(), 20)
    spu_df = generate_test_spu_data(stores_df['str_code'].tolist(), 200)
    
    # Save to files
    stores_df.to_csv(f"{output_dir}/test_store_coordinates.csv", index=False)
    category_df.to_csv(f"{output_dir}/test_category_sales.csv", index=False)
    spu_df.to_csv(f"{output_dir}/test_spu_sales.csv", index=False)
    
    print(f"Test data saved to {output_dir}/")
    print(f"  - Stores: {len(stores_df)} stores")
    print(f"  - Categories: {len(category_df)} records")
    print(f"  - SPUs: {len(spu_df)} records")

def load_test_data(data_dir: str = "tests/test_data") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load test data for matrix preparation testing.
    
    Args:
        data_dir: Directory containing test data
        
    Returns:
        Tuple of (stores_df, category_df, spu_df)
    """
    stores_file = f"{data_dir}/test_store_coordinates.csv"
    category_file = f"{data_dir}/test_category_sales.csv"
    spu_file = f"{data_dir}/test_spu_sales.csv"
    
    if not all(os.path.exists(f) for f in [stores_file, category_file, spu_file]):
        print("Test data not found, generating...")
        save_test_data(data_dir)
    
    stores_df = pd.read_csv(stores_file)
    category_df = pd.read_csv(category_file)
    spu_df = pd.read_csv(spu_file)
    
    return stores_df, category_df, spu_df

if __name__ == "__main__":
    save_test_data()
