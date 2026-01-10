"""
Sales data generator for test data.

This module provides functions to generate test data for sales transactions,
following the same patterns and constraints as production data.
"""
import random
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Sales patterns by day of week (0=Monday, 6=Sunday)
WEEKLY_PATTERN = {
    0: 0.9,  # Monday
    1: 0.95,  # Tuesday
    2: 1.0,   # Wednesday
    3: 1.05,  # Thursday
    4: 1.1,   # Friday
    5: 1.3,   # Saturday
    6: 1.2    # Sunday
}

def generate_sales_transactions(
    stores: pd.DataFrame,
    spus: pd.DataFrame,
    start_date: str,
    end_date: str,
    avg_daily_transactions: int = 100,
    seasonality: bool = True
) -> pd.DataFrame:
    """Generate sales transaction data.
    
    Args:
        stores: DataFrame of stores
        spus: DataFrame of SPUs
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
        avg_daily_transactions: Average number of transactions per day
        seasonality: Whether to apply weekly seasonality
        
    Returns:
        DataFrame with sales transaction data
    """
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    transactions = []
    
    # Group SPUs by category for more realistic sales patterns
    spus_by_category = spus.groupby('cate_name')
    
    for date in date_range:
        # Apply weekly seasonality
        day_of_week = date.weekday()
        daily_factor = WEEKLY_PATTERN.get(day_of_week, 1.0)
        
        # Add some random variation
        daily_variation = random.uniform(0.8, 1.2)
        daily_transactions = int(avg_daily_transactions * daily_factor * daily_variation)
        
        for _ in range(max(1, daily_transactions)):
            # Select a random store
            store = stores.sample(1).iloc[0]
            
            # Select 1-5 SPUs for this transaction
            n_items = random.choices(
                [1, 2, 3, 4, 5],
                weights=[0.4, 0.3, 0.15, 0.1, 0.05]
            )[0]
            
            # Get SPUs, with preference for the same category
            category = random.choice(spus['cate_name'].unique())
            category_spus = spus[spus['cate_name'] == category]
            selected_spus = category_spus.sample(min(len(category_spus), n_items))
            
            # Generate transaction timestamp within the day
            hour = random.randint(9, 21)  # Store hours 9am-9pm
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            timestamp = datetime.combine(
                date.date(),
                datetime.min.time()
            ) + timedelta(hours=hour, minutes=minute, seconds=second)
            
            for _, spu in selected_spus.iterrows():
                # Generate quantity with occasional bulk purchases
                if random.random() < 0.9:  # 90% single item purchases
                    quantity = 1
                else:
                    quantity = random.randint(2, 10)
                
                # Apply discount with some probability
                if random.random() < 0.3:  # 30% chance of discount
                    discount = round(random.uniform(0.7, 0.95), 2)  # 5-30% off
                else:
                    discount = 1.0
                
                price = spu['base_price'] * discount
                
                transactions.append({
                    'transaction_id': f"TXN{timestamp.strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}",
                    'transaction_time': timestamp,
                    'str_code': store['str_code'],
                    'spu_code': spu['spu_code'],
                    'quantity': quantity,
                    'unit_price': round(price, 2),
                    'total_amount': round(quantity * price, 2),
                    'discount_rate': round(1 - discount, 2) if discount < 1.0 else 0.0,
                    'payment_method': random.choice(['CASH', 'CREDIT_CARD', 'MOBILE_PAY']),
                    'member_id': f"M{random.randint(10000000, 99999999)}" if random.random() > 0.3 else None
                })
    
    return pd.DataFrame(transactions)

def generate_daily_sales_summary(
    transactions: pd.DataFrame,
    stores: pd.DataFrame,
    spus: pd.DataFrame
) -> pd.DataFrame:
    """Generate daily sales summary from transaction data.
    
    Args:
        transactions: DataFrame of sales transactions
        stores: DataFrame of stores
        spus: DataFrame of SPUs
        
    Returns:
        DataFrame with daily sales summary
    """
    if transactions.empty:
        return pd.DataFrame()
    
    # Add date column
    transactions['sale_date'] = transactions['transaction_time'].dt.date
    
    # Join with store and SPU data
    df = transactions.merge(
        stores[['str_code', 'region', 'tier']],
        on='str_code',
        how='left'
    )
    
    df = df.merge(
        spus[['spu_code', 'cate_name', 'sub_cate_name']],
        on='spu_code',
        how='left'
    )
    
    # Group by date, store, and SPU
    summary = df.groupby([
        'sale_date',
        'str_code',
        'region',
        'tier',
        'spu_code',
        'cate_name',
        'sub_cate_name'
    ]).agg({
        'quantity': 'sum',
        'total_amount': 'sum',
        'transaction_id': 'count'
    }).reset_index()
    
    # Rename columns to match expected format
    summary = summary.rename(columns={
        'transaction_id': 'transaction_count',
        'total_amount': 'sales_amount'
    })
    
    # Add derived metrics
    summary['avg_unit_price'] = summary['sales_amount'] / summary['quantity']
    
    return summary

def generate_test_dataset(
    n_stores: int = 10,
    n_spus: int = 100,
    start_date: str = '2023-01-01',
    end_date: str = '2023-01-31',
    output_dir: Optional[str] = None
) -> Dict[str, pd.DataFrame]:
    """Generate a complete test dataset with stores, SPUs, and sales data.
    
    Args:
        n_stores: Number of stores to generate
        n_spus: Number of SPUs to generate
        start_date: Start date for sales data
        end_date: End date for sales data
        output_dir: If provided, save data to CSV files in this directory
        
    Returns:
        Dictionary with generated DataFrames
    """
    from ..data_generators import store_data, spu_data
    
    # Generate stores
    stores = store_data.generate_stores(n_stores)
    
    # Generate SPUs
    spus = spu_data.generate_spus(n_spus)
    
    # Generate sales transactions
    transactions = generate_sales_transactions(
        stores=stores,
        spus=spus,
        start_date=start_date,
        end_date=end_date,
        avg_daily_transactions=50
    )
    
    # Generate daily sales summary
    daily_sales = generate_daily_sales_summary(transactions, stores, spus)
    
    # Generate cluster assignments
    clusters = spu_data.generate_cluster_assignments(stores)
    
    result = {
        'stores': stores,
        'spus': spus,
        'transactions': transactions,
        'daily_sales': daily_sales,
        'clusters': clusters
    }
    
    # Save to CSV if output directory is provided
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for name, df in result.items():
            df.to_csv(output_path / f"{name}.csv", index=False)
    
    return result

def validate_sales_transactions(df: pd.DataFrame) -> List[str]:
    """Validate sales transaction data.
    
    Args:
        df: DataFrame containing sales transactions
        
    Returns:
        List of validation error messages, empty if valid
    """
    errors = []
    
    # Check required columns
    required_columns = {
        'transaction_id', 'transaction_time', 'str_code', 'spu_code',
        'quantity', 'unit_price', 'total_amount', 'payment_method'
    }
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}")
    
    # Validate transaction IDs
    if 'transaction_id' in df.columns:
        if df['transaction_id'].isnull().any():
            errors.append("Transaction ID cannot be null")
        if not df['transaction_id'].str.startswith('TXN').all():
            errors.append("All transaction IDs must start with 'TXN'")
    
    # Validate quantities and amounts
    numeric_columns = {'quantity', 'unit_price', 'total_amount'}
    for col in numeric_columns.intersection(df.columns):
        if pd.api.types.is_numeric_dtype(df[col]):
            if (df[col] <= 0).any():
                errors.append(f"{col} must be positive")
        else:
            errors.append(f"{col} must be numeric")
    
    # Validate payment methods
    if 'payment_method' in df.columns:
        valid_methods = {'CASH', 'CREDIT_CARD', 'MOBILE_PAY'}
        invalid_methods = set(df['payment_method'].dropna()) - valid_methods
        if invalid_methods:
            errors.append(f"Invalid payment methods: {', '.join(invalid_methods)}")
    
    return errors
