"""
Realistic test data generator based on production data patterns.

This module provides functions to generate test data that closely resembles
production data in terms of structure, distributions, and relationships.
"""
import os
import random
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

# Base paths
DATA_DIR = Path(__file__).parents[3] / 'data'

class RealisticDataGenerator:
    """Generate realistic test data based on production patterns."""
    
    def __init__(self, random_seed: int = 42):
        """Initialize the data generator with optional random seed."""
        self.rng = np.random.RandomState(random_seed)
        self._load_reference_data()
        
    def _load_reference_data(self) -> None:
        """Load and preprocess reference data from production."""
        # Load store data
        store_codes_path = DATA_DIR / 'store_codes.csv'
        if not store_codes_path.exists():
            # If store_codes.csv doesn't exist, create a minimal version
            self.stores = pd.DataFrame({
                'str_code': [f'STR{i:04d}' for i in range(1, 101)],
                'store_name': [f'Store {i}' for i in range(1, 101)],
                'region': np.random.choice(['North', 'South', 'East', 'West'], 100),
                'store_type': np.random.choice(['A', 'B', 'C'], 100, p=[0.5, 0.3, 0.2])
            })
        else:
            self.stores = pd.read_csv(store_codes_path)
        
        # Load category data if available
        if (DATA_DIR / 'category_list.txt').exists():
            with open(DATA_DIR / 'category_list.txt', 'r') as f:
                self.categories = [line.strip() for line in f if line.strip()]
        else:
            self.categories = [f'category_{i:02d}' for i in range(1, 21)]
            
        # Load subcategory data if available
        if (DATA_DIR / 'subcategory_list.txt').exists():
            with open(DATA_DIR / 'subcategory_list.txt', 'r') as f:
                self.subcategories = [line.strip() for line in f if line.strip()]
        else:
            self.subcategories = [f'subcat_{i:03d}' for i in range(1, 51)]
    
    def generate_stores(self, n_stores: int = 100) -> pd.DataFrame:
        """Generate realistic store data."""
        # Use real store codes if available, otherwise generate
        if len(self.stores) > 0:
            store_codes = self.stores['str_code'].sample(
                min(n_stores, len(self.stores)), 
                random_state=self.rng
            ).tolist()
        else:
            store_codes = [f'store_{i:05d}' for i in range(1, n_stores + 1)]
        
        # Generate store attributes
        regions = ['North', 'South', 'East', 'West']
        store_types = ['A', 'B', 'C', 'D']
        
        stores = pd.DataFrame({
            'str_code': store_codes,
            'store_name': [f'Store {code}' for code in store_codes],
            'region': self.rng.choice(regions, size=len(store_codes)),
            'store_type': self.rng.choice(store_types, size=len(store_codes), p=[0.4, 0.3, 0.2, 0.1]),
            'size_sqm': self.rng.normal(200, 50, len(store_codes)).astype(int),
            'opening_date': [
                (datetime.now() - timedelta(days=self.rng.randint(365, 365*5))).strftime('%Y-%m-%d')
                for _ in range(len(store_codes))
            ]
        })
        
        return stores
    
    def generate_products(self, n_products: int = 1000) -> pd.DataFrame:
        """Generate realistic product data matching production format."""
        # Generate product codes in the format seen in production (e.g., '0A00002')
        product_codes = [f'{i:06d}' for i in range(1, n_products + 1)]
        
        # Assign categories and subcategories - using actual values seen in production
        categories = ['样衣']  # Using the actual category seen in production
        subcategories = ['长袖衬衫', '套头卫衣', '圆领卫衣']  # Actual subcategories seen
        
        # Generate product attributes matching the production format
        products = pd.DataFrame({
            'spu_code': product_codes,
            'cate_name': self.rng.choice(categories, size=n_products),
            'sub_cate_name': self.rng.choice(subcategories, size=n_products, 
                                          p=[0.4, 0.3, 0.3]),  # Adjust weights as needed
        })
        
        # Add store count (number of stores carrying this SPU)
        products['store_count'] = np.clip(
            self.rng.lognormal(3, 0.8, n_products).astype(int),
            1,  # At least 1 store
            len(self.stores) if hasattr(self, 'stores') else 100  # At most all stores
        )
        
        # Generate sales statistics
        products['total_sales'] = np.clip(
            self.rng.lognormal(10, 1.5, n_products),
            1000,  # Minimum total sales
            1000000  # Maximum total sales
        ).round(2)
        
        products['avg_sales'] = products['total_sales'] / products['store_count']
        products['std_sales'] = products['avg_sales'] * self.rng.uniform(0.5, 2.0, n_products)
        
        # Add period count (number of periods with sales data)
        products['period_count'] = self.rng.poisson(12, n_products) + 1  # At least 1 period
        
        return products
    
    def generate_sales(
        self, 
        stores: pd.DataFrame, 
        products: pd.DataFrame,
        start_date: str = '2024-01-01',
        end_date: str = '2024-12-31',
        avg_daily_transactions: int = 1000
    ) -> pd.DataFrame:
        """Generate realistic sales transactions matching production format."""
        date_range = pd.date_range(start_date, end_date, freq='D')
        transactions = []
        
        # Create a mapping of which products are sold in which stores
        store_product_map = {}
        for _, product in products.iterrows():
            # Select stores that carry this product
            n_stores = int(product['store_count'])
            store_sample = stores.sample(
                n=min(n_stores, len(stores)),
                replace=False,
                random_state=self.rng
            )
            store_product_map[product['spu_code']] = set(store_sample['str_code'])
        
        # Generate daily transactions
        for date in date_range:
            # Vary transaction volume by day of week and month
            day_factor = self._get_day_factor(date.weekday())
            month_factor = 1.0 + (date.month - 6) * 0.1  # Higher in summer months
            n_transactions = int(avg_daily_transactions * day_factor * month_factor * self.rng.uniform(0.8, 1.2))
            
            # Generate transactions
            for _ in range(n_transactions):
                # Select a random product
                product = products.sample(1, random_state=self.rng).iloc[0]
                
                # Select a store that carries this product
                valid_stores = store_product_map[product['spu_code']]
                if not valid_stores:
                    continue
                    
                store_id = self.rng.choice(list(valid_stores))
                
                # Generate sale quantity (zero-inflated poisson)
                if self.rng.random() < 0.4:  # 40% chance of no sale
                    continue
                    
                base_qty = product['avg_sales'] / 30  # Daily average
                quantity = max(1, int(self.rng.poisson(base_qty * 0.5) + 1))
                
                # Calculate sale amount (with some randomness)
                sale_amount = product['avg_sales'] * quantity * self.rng.uniform(0.8, 1.2)
                
                transactions.append({
                    'str_code': store_id,
                    'spu_code': product['spu_code'],
                    'cate_name': product['cate_name'],
                    'sub_cate_name': product['sub_cate_name'],
                    'sal_qty': quantity,
                    'sal_amt': round(sale_amount, 2),
                    'sale_date': date.strftime('%Y-%m-%d')
                })
        
        # Convert to DataFrame and aggregate by store, product, and date
        sales_df = pd.DataFrame(transactions)
        if not sales_df.empty:
            sales_df = sales_df.groupby(
                ['str_code', 'spu_code', 'cate_name', 'sub_cate_name', 'sale_date']
            ).agg({
                'sal_qty': 'sum',
                'sal_amt': 'sum'
            }).reset_index()
            
            # Add derived metrics
            sales_df['unit_price'] = (sales_df['sal_amt'] / sales_df['sal_qty']).round(2)
        else:
            # Return empty DataFrame with correct columns
            sales_df = pd.DataFrame(columns=[
                'str_code', 'spu_code', 'cate_name', 'sub_cate_name', 'sale_date',
                'sal_qty', 'sal_amt', 'unit_price'
            ])
        
        return sales_df
    
    def _get_day_factor(self, weekday: int) -> float:
        """Get sales multiplier based on day of week."""
        factors = {
            0: 0.9,   # Monday
            1: 0.95,  # Tuesday
            2: 1.0,   # Wednesday
            3: 1.05,  # Thursday
            4: 1.1,   # Friday
            5: 1.3,   # Saturday
            6: 1.2    # Sunday
        }
        return factors.get(weekday, 1.0)
    
    def _get_weights(self, n: int, power: float = 1.5) -> np.ndarray:
        """Generate weights following a power law distribution."""
        weights = np.array([1 / (i ** power) for i in range(1, n + 1)])
        return weights / weights.sum()


def generate_test_dataset(
    output_dir: Path,
    n_stores: int = 50,
    n_products: int = 500,
    start_date: str = '2024-01-01',
    end_date: str = '2024-03-31',
    random_seed: int = 42
) -> Dict[str, Path]:
    """
    Generate a complete test dataset with realistic patterns.
    
    Args:
        output_dir: Directory to save the generated files
        n_stores: Number of stores to generate
        n_products: Number of products to generate
        start_date: Start date for sales data
        end_date: End date for sales data
        random_seed: Random seed for reproducibility
        
    Returns:
        Dictionary mapping file names to their paths
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize generator
    gen = RealisticDataGenerator(random_seed=random_seed)
    
    # Generate data
    stores = gen.generate_stores(n_stores)
    products = gen.generate_products(n_products)
    sales = gen.generate_sales(stores, products, start_date, end_date)
    
    # Save files
    files = {}
    for name, df in [
        ('stores.csv', stores),
        ('products.csv', products),
        ('sales.csv', sales)
    ]:
        path = output_dir / name
        df.to_csv(path, index=False)
        files[name] = path
    
    return files


if __name__ == "__main__":
    # Example usage
    output_dir = Path(__file__).parent.parent / 'test_data' / 'generated'
    generate_test_dataset(output_dir)
