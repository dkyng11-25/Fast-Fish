"""
SPU (Standard Product Unit) data generator for test data.

This module provides functions to generate test data for products (SPUs),
following the same patterns and constraints as production data.
"""
import random
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Sample product categories and subcategories based on production data
PRODUCT_CATEGORIES = {
    '样衣': ['长袖衬衫', '套头卫衣', '圆领卫衣', '长裤', '短裤', '连衣裙', '半身裙', '外套'],
    '鞋类': ['运动鞋', '休闲鞋', '皮鞋', '凉鞋', '靴子'],
    '配饰': ['帽子', '围巾', '手套', '皮带', '袜子']
}

def generate_spu_code() -> str:
    """Generate a valid SPU code following production patterns.
    
    Returns:
        A 7-character alphanumeric SPU code
    """
    # Based on observation, SPU codes are 7-character alphanumeric strings
    # starting with a letter followed by 6 digits
    letter = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    numbers = ''.join(random.choices('0123456789', k=6))
    return f"{letter}{numbers}"

def generate_spu_metadata(spu_code: Optional[str] = None) -> Dict[str, Any]:
    """Generate metadata for a single SPU.
    
    Args:
        spu_code: Optional SPU code to use. If None, a random one will be generated.
        
    Returns:
        Dictionary containing SPU metadata
    """
    if spu_code is None:
        spu_code = generate_spu_code()
    
    # Select a random category and subcategory
    category = random.choice(list(PRODUCT_CATEGORIES.keys()))
    subcategory = random.choice(PRODUCT_CATEGORIES[category])
    
    return {
        'spu_code': spu_code,
        'cate_name': category,
        'sub_cate_name': subcategory,
        'introduction_date': pd.Timestamp('2020-01-01') + pd.Timedelta(days=random.randint(0, 365*3)),
        'base_price': round(random.uniform(50, 1000), 2),
        'is_active': random.choices([True, False], weights=[0.8, 0.2])[0]
    }

def generate_spus(n: int = 10) -> pd.DataFrame:
    """Generate a DataFrame of SPU metadata.
    
    Args:
        n: Number of SPUs to generate
        
    Returns:
        DataFrame with SPU metadata
    """
    # Ensure unique SPU codes
    spu_codes = set()
    while len(spu_codes) < n:
        spu_codes.add(generate_spu_code())
    
    spus = [generate_spu_metadata(spu_code) for spu_code in spu_codes]
    return pd.DataFrame(spus)

def generate_sales_data(
    stores: pd.DataFrame,
    spus: pd.DataFrame,
    start_date: str = '2023-01-01',
    end_date: str = '2023-12-31',
    sales_per_day_per_store: int = 10
) -> pd.DataFrame:
    """Generate sales data for stores and SPUs.
    
    Args:
        stores: DataFrame of stores
        spus: DataFrame of SPUs
        start_date: Start date for sales data
        end_date: End date for sales data
        sales_per_day_per_store: Average number of sales per day per store
        
    Returns:
        DataFrame with sales data
    """
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    sales_data = []
    
    for date in date_range:
        for _, store in stores.iterrows():
            # Randomly select SPUs for this store and date
            selected_spus = spus.sample(n=min(len(spus), sales_per_day_per_store))
            
            for _, spu in selected_spus.iterrows():
                # Generate random quantity sold (1-5 items)
                quantity = random.choices(
                    [1, 2, 3, 4, 5],
                    weights=[0.4, 0.3, 0.15, 0.1, 0.05]
                )[0]
                
                # Add some random variation to the price
                price = spu['base_price'] * random.uniform(0.8, 1.2)
                
                sales_data.append({
                    'sale_date': date,
                    'str_code': store['str_code'],
                    'spu_code': spu['spu_code'],
                    'quantity': quantity,
                    'sales_amount': round(quantity * price, 2),
                    'discount': round(random.uniform(0.7, 1.0), 2)
                })
    
    return pd.DataFrame(sales_data)

def generate_cluster_assignments(
    stores: pd.DataFrame,
    n_clusters: int = 5,
    random_state: int = 42
) -> pd.DataFrame:
    """Generate cluster assignments for stores.
    
    Args:
        stores: DataFrame of stores
        n_clusters: Number of clusters to create
        random_state: Random seed for reproducibility
        
    Returns:
        DataFrame with cluster assignments
    """
    # Ensure reproducibility
    random.seed(random_state)
    np.random.seed(random_state)
    
    # Simple random assignment for now
    # In a real implementation, this could use actual clustering
    clusters = [f'CLUSTER_{i+1:02d}' for i in range(n_clusters)]
    
    return pd.DataFrame({
        'str_code': stores['str_code'].copy(),
        'cluster': np.random.choice(clusters, size=len(stores))
    })

def load_sample_spu_data() -> pd.DataFrame:
    """Load a sample of real SPU data for testing.
    
    This function should be used to load a small, representative sample of
    production SPU data for testing purposes.
    
    Returns:
        DataFrame with sample SPU data
    """
    # In a real implementation, this would load from a test data file
    # For now, generate synthetic data that matches the schema
    return generate_spus(100)

def validate_spu_data(df: pd.DataFrame) -> List[str]:
    """Validate SPU data against expected schema and constraints.
    
    Args:
        df: DataFrame containing SPU data
        
    Returns:
        List of validation error messages, empty if valid
    """
    errors = []
    
    # Check required columns
    required_columns = {'spu_code', 'cate_name', 'sub_cate_name', 'base_price'}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}")
    
    # Validate SPU codes
    if 'spu_code' in df.columns:
        invalid_spu_codes = df[~df['spu_code'].astype(str).str.match(r'^[A-Z]\d{6}$')]
        if not invalid_spu_codes.empty:
            errors.append(f"Invalid SPU code format: {invalid_spu_codes['spu_code'].tolist()}")
    
    # Validate categories and subcategories
    if 'cate_name' in df.columns and 'sub_cate_name' in df.columns:
        valid_categories = set(PRODUCT_CATEGORIES.keys())
        invalid_categories = set(df['cate_name']) - valid_categories
        
        if invalid_categories:
            errors.append(f"Invalid categories: {', '.join(invalid_categories)}")
        
        # Check subcategories
        for category, subcategories in PRODUCT_CATEGORIES.items():
            cat_spus = df[df['cate_name'] == category]
            if not cat_spus.empty:
                invalid_subcats = set(cat_spus['sub_cate_name']) - set(subcategories)
                if invalid_subcats:
                    errors.append(
                        f"Invalid subcategories for {category}: {', '.join(invalid_subcats)}"
                    )
    
    # Validate prices
    if 'base_price' in df.columns:
        if (df['base_price'] <= 0).any():
            errors.append("All prices must be positive")
    
    return errors
