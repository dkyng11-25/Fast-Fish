"""
Store data generator for test data.

This module provides functions to generate test data for stores,
following the same patterns and constraints as production data.
"""
import random
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

# Sample store data patterns based on production data
STORE_REGIONS = [
    'East China', 'North China', 'South China',
    'Central China', 'West China', 'Northeast China'
]

STORE_TIERS = ['S', 'A', 'B', 'C']

def generate_store_code() -> str:
    """Generate a valid store code following production patterns.
    
    Returns:
        A 5-digit store code as a string
    """
    # Based on observation, store codes are 5-digit numbers
    return f"{random.randint(10000, 99999):05d}"

def generate_store_metadata(store_code: Optional[str] = None) -> Dict[str, Any]:
    """Generate metadata for a single store.
    
    Args:
        store_code: Optional store code to use. If None, a random one will be generated.
        
    Returns:
        Dictionary containing store metadata
    """
    if store_code is None:
        store_code = generate_store_code()
    
    return {
        'str_code': store_code,
        'region': random.choice(STORE_REGIONS),
        'tier': random.choice(STORE_TIERS),
        'opening_date': pd.Timestamp('2020-01-01') + pd.Timedelta(days=random.randint(0, 365*3)),
        'floor_area': random.uniform(50, 300),  # Square meters
        'is_active': random.choices([True, False], weights=[0.9, 0.1])[0],
        'latitude': round(random.uniform(0, 90), 4),
        'longitude': round(random.uniform(0, 180), 4),
    }

def generate_stores(n: int = 10) -> pd.DataFrame:
    """Generate a DataFrame of store metadata.
    
    Args:
        n: Number of stores to generate
        
    Returns:
        DataFrame with store metadata
    """
    # Ensure unique store codes
    store_codes = set()
    while len(store_codes) < n:
        store_codes.add(generate_store_code())
    
    stores = [generate_store_metadata(store_code) for store_code in store_codes]
    return pd.DataFrame(stores)

def load_sample_store_data() -> pd.DataFrame:
    """Load a sample of real store data for testing.
    
    This function should be used to load a small, representative sample of
    production store data for testing purposes.
    
    Returns:
        DataFrame with sample store data
    """
    # In a real implementation, this would load from a test data file
    # For now, generate synthetic data that matches the schema
    return generate_stores(100)

def validate_store_data(df: pd.DataFrame) -> List[str]:
    """Validate store data against expected schema and constraints.
    
    Args:
        df: DataFrame containing store data
        
    Returns:
        List of validation error messages, empty if valid
    """
    errors = []
    
    # Check required columns
    required_columns = {'str_code', 'region', 'tier', 'opening_date', 'floor_area', 'is_active'}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}")
    
    # Validate store codes
    if 'str_code' in df.columns:
        invalid_store_codes = df[~df['str_code'].astype(str).str.match(r'^\d{5}$')]
        if not invalid_store_codes.empty:
            errors.append(f"Invalid store code format: {invalid_store_codes['str_code'].tolist()}")
    
    # Validate region values
    if 'region' in df.columns and not set(df['region'].unique()).issubset(set(STORE_REGIONS)):
        errors.append(f"Invalid region values. Must be one of: {', '.join(STORE_REGIONS)}")
    
    # Validate tier values
    if 'tier' in df.columns and not set(df['tier'].unique()).issubset(set(STORE_TIERS)):
        errors.append(f"Invalid tier values. Must be one of: {', '.join(STORE_TIERS)}")
    
    return errors

def generate_temperature_data(stores: pd.DataFrame, temperature_bands: List[str] = None) -> pd.DataFrame:
    """
    Generate simulated temperature data for stores.

    Args:
        stores (pd.DataFrame): DataFrame of stores with 'str_code'.
        temperature_bands (List[str], optional): List of possible temperature band labels. 
                                                Defaults to a predefined list if None.

    Returns:
        pd.DataFrame: DataFrame with store codes and simulated temperature bands, 
                      latitude, and longitude.
    """
    if temperature_bands is None:
        temperature_bands = [
            "tropical", "subtropical", "temperate", "cold", "polar"
        ]
    
    temp_data = stores[['str_code', 'latitude', 'longitude']].copy()
    temp_data['temperature_band_q3q4_seasonal'] = np.random.choice(
        temperature_bands, size=len(stores)
    )
    return temp_data

def generate_all_store_data(n_stores: int = 100) -> Dict[str, pd.DataFrame]:
    """
    Generate a complete set of store-related test data including metadata and temperature.

    Args:
        n_stores (int): Number of stores to generate.

    Returns:
        Dict[str, pd.DataFrame]: A dictionary containing DataFrames for 
                                 'stores' and 'stores_with_feels_like_temperature'.
    """
    stores = generate_stores(n_stores)
    stores_with_coords_temp = generate_temperature_data(stores) # Reuse generate_stores for base
    
    return {
        'stores': stores,
        'stores_with_feels_like_temperature': stores_with_coords_temp
    }
