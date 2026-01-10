#!/usr/bin/env python3
"""
Step 3: Prepare Store-Product Matrices for Clustering

This step creates normalized matrices for both subcategory-level and SPU-level analysis.
It handles data filtering, normalization, and matrix creation for downstream clustering.

Author: Data Pipeline
Date: 2025-06-14
"""

import pandas as pd
import numpy as np
import os
import sys
from typing import Tuple, List, Dict, Optional
from datetime import datetime
from tqdm import tqdm
import warnings

# Suppress pandas warnings
warnings.filterwarnings('ignore')

# Import configuration system
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import get_api_data_files, get_current_period, get_period_label

# Get current period configuration
current_yyyymm, current_period = get_current_period()
api_files = get_api_data_files(current_yyyymm, current_period)

# Configuration - now uses dynamic file paths
CATEGORY_FILE = api_files['category_sales']
SPU_FILE = api_files['spu_sales']
COORDINATES_FILE = "data/store_coordinates_extended.csv"

# Matrix creation parameters
MIN_STORES_PER_SUBCATEGORY = 5
MIN_SUBCATEGORIES_PER_STORE = 3
MIN_STORES_PER_SPU = 3
MIN_SPUS_PER_STORE = 3
MIN_SPU_SALES_AMOUNT = 1.0
MAX_SPU_COUNT = 5000  # Increase SPU cap to include more products across stores

# Anomaly detection parameters
ANOMALY_LAT = 21.9178
ANOMALY_LON = 110.854

# Create necessary directories
os.makedirs("data", exist_ok=True)

def log_progress(message: str) -> None:
    """
    Log progress with timestamp.
    
    Args:
        message (str): Progress message to log
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_subcategory_data() -> pd.DataFrame:
    """
    Load subcategory-level sales data.
    
    Returns:
        pd.DataFrame: Subcategory sales data
    """
    try:
        # Try multiple possible locations for the API data
        possible_paths = [
            CATEGORY_FILE,
            os.path.join("../data/api_data", os.path.basename(CATEGORY_FILE)),
            os.path.join("data/api_data", os.path.basename(CATEGORY_FILE)),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/api_data", os.path.basename(CATEGORY_FILE)),
            "data/api_data/complete_category_sales_202505.csv"  # Legacy fallback
        ]
        
        df = None
        loaded_path = None
        
        # Try each possible path
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    df = pd.read_csv(path, low_memory=False)
                    loaded_path = path
                    break
            except Exception:
                continue
                
        if df is None:
            raise FileNotFoundError(f"Could not find subcategory data file: {CATEGORY_FILE}")
        
        log_progress(f"Loaded subcategory data from {loaded_path} with {len(df):,} rows and {df['str_code'].nunique()} stores")
        return df
        
    except Exception as e:
        log_progress(f"Error loading subcategory data: {str(e)}")
        raise

def load_spu_data() -> Optional[pd.DataFrame]:
    """
    Load SPU-level sales data if available.
    
    Returns:
        Optional[pd.DataFrame]: SPU sales data or None if not available
    """
    try:
        # Try multiple possible locations for the SPU data
        possible_paths = [
            SPU_FILE,
            os.path.join("../data/api_data", os.path.basename(SPU_FILE)),
            os.path.join("data/api_data", os.path.basename(SPU_FILE)),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/api_data", os.path.basename(SPU_FILE)),
            "data/api_data/complete_spu_sales_202505.csv"  # Legacy fallback
        ]
        
        df = None
        loaded_path = None
        
        # Try each possible path
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    df = pd.read_csv(path, low_memory=False)
                    loaded_path = path
                    break
            except Exception:
                continue
        
        if df is None:
            log_progress(f"SPU data file not found at {SPU_FILE}")
            return None
        
        # Clean and validate SPU data (support both sal_amt and spu_sales_amt)
        if 'spu_sales_amt' in df.columns:
            df['spu_sales_amt'] = pd.to_numeric(df['spu_sales_amt'], errors='coerce').fillna(0)
        elif 'sal_amt' in df.columns:
            df['spu_sales_amt'] = pd.to_numeric(df['sal_amt'], errors='coerce').fillna(0)
        else:
            df['spu_sales_amt'] = 0
        df = df[df['spu_sales_amt'] >= MIN_SPU_SALES_AMOUNT]  # Filter minimum sales
        
        log_progress(f"Loaded SPU data from {loaded_path} with {len(df):,} records from {df['str_code'].nunique()} stores, {df['spu_code'].nunique()} SPUs")
        
        print(f"[DEBUG] SPU data memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
        
        return df
        
    except Exception as e:
        log_progress(f"Error loading SPU data: {str(e)}")
        return None

def load_coordinates() -> pd.DataFrame:
    """
    Load store coordinates data.
    
    Returns:
        pd.DataFrame: Store coordinates
    """
    try:
        coords_df = pd.read_csv(COORDINATES_FILE)
        log_progress(f"Loaded coordinates for {len(coords_df)} stores")
        return coords_df
    except Exception as e:
        log_progress(f"Error loading coordinates: {str(e)}")
        raise

def identify_anomaly_stores(coords_df: pd.DataFrame) -> List[str]:
    """
    Identify stores with anomalous coordinates.
    
    Args:
        coords_df (pd.DataFrame): Store coordinates DataFrame
        
    Returns:
        List[str]: List of anomalous store codes
    """
    anomaly_stores = coords_df[
        (coords_df['latitude'] == ANOMALY_LAT) & 
        (coords_df['longitude'] == ANOMALY_LON)
    ]['str_code'].tolist()
    
    log_progress(f"Identified {len(anomaly_stores)} stores with anomalous coordinates at ({ANOMALY_LAT}, {ANOMALY_LON})")
    return anomaly_stores

def filter_subcategory_data(df: pd.DataFrame, anomaly_stores: List[str]) -> pd.DataFrame:
    """
    Filter subcategory data based on prevalence and store criteria.
    
    Args:
        df (pd.DataFrame): Raw subcategory data
        anomaly_stores (List[str]): List of anomalous store codes to exclude
        
    Returns:
        pd.DataFrame: Filtered subcategory data
    """
    log_progress("=== PROCESSING SUBCATEGORY-LEVEL DATA ===")
    log_progress(f"Loaded subcategory data from {CATEGORY_FILE} with {len(df):,} rows and {df['str_code'].nunique()} stores")
    
    # Filter subcategories that appear in at least MIN_STORES_PER_SUBCATEGORY stores
    subcategory_counts = df['sub_cate_name'].value_counts()
    valid_subcategories = subcategory_counts[subcategory_counts >= MIN_STORES_PER_SUBCATEGORY].index
    df_filtered = df[df['sub_cate_name'].isin(valid_subcategories)]
    
    log_progress(f"Found {len(valid_subcategories)} subcategories that appear in at least {MIN_STORES_PER_SUBCATEGORY} stores")
    log_progress(f"Filtered subcategory data has {len(df_filtered):,} rows and {df_filtered['str_code'].nunique()} stores")
    
    # Filter stores that have at least MIN_SUBCATEGORIES_PER_STORE subcategories
    store_subcategory_counts = df_filtered['str_code'].value_counts()
    valid_stores = store_subcategory_counts[store_subcategory_counts >= MIN_SUBCATEGORIES_PER_STORE].index
    df_filtered = df_filtered[df_filtered['str_code'].isin(valid_stores)]
    
    log_progress(f"Found {len(valid_stores)} stores with at least {MIN_SUBCATEGORIES_PER_STORE} subcategories")
    log_progress(f"Filtered subcategory data has {len(df_filtered):,} rows")
    
    # Remove anomaly stores
    df_filtered = df_filtered[~df_filtered['str_code'].isin(anomaly_stores)]
    log_progress(f"Removed {len(anomaly_stores)} anomaly stores from the dataset")
    log_progress(f"Dataset now contains {df_filtered['str_code'].nunique()} stores")
    
    return df_filtered

def filter_spu_data(df: pd.DataFrame, anomaly_stores: List[str]) -> pd.DataFrame:
    """
    Filter SPU data based on prevalence and store criteria.
    
    Args:
        df (pd.DataFrame): Raw SPU data
        anomaly_stores (List[str]): List of anomalous store codes to exclude
        
    Returns:
        pd.DataFrame: Filtered SPU data
    """
    log_progress("Filtering SPUs based on prevalence and sales volume...")
    
    # Filter SPUs by prevalence (appear in at least MIN_STORES_PER_SPU stores)
    spu_store_counts = df['spu_code'].value_counts()
    spus_by_prevalence = spu_store_counts[spu_store_counts >= MIN_STORES_PER_SPU].index
    
    # Filter SPUs by sales volume (total sales across all stores)
    spu_sales_totals = df.groupby('spu_code')['spu_sales_amt'].sum()
    sales_threshold = spu_sales_totals.quantile(0.1)  # Bottom 10% threshold
    spus_by_sales = spu_sales_totals[spu_sales_totals >= sales_threshold].index
    
    # Combine both criteria
    valid_spus = set(spus_by_prevalence) & set(spus_by_sales)
    
    log_progress(f"SPU filtering results:")
    log_progress(f"  • SPUs by prevalence (≥{MIN_STORES_PER_SPU} stores): {len(spus_by_prevalence)}")
    log_progress(f"  • SPUs by sales volume (≥{sales_threshold:.0f}): {len(spus_by_sales)}")
    log_progress(f"  • Final SPUs to keep: {len(valid_spus)}")
    
    df_filtered = df[df['spu_code'].isin(valid_spus)]
    log_progress(f"Filtered SPU data has {len(df_filtered):,} rows from {df_filtered['str_code'].nunique()} stores")
    
    # Filter stores that have at least MIN_SPUS_PER_STORE SPUs
    store_spu_counts = df_filtered['str_code'].value_counts()
    valid_stores = store_spu_counts[store_spu_counts >= MIN_SPUS_PER_STORE].index
    df_filtered = df_filtered[df_filtered['str_code'].isin(valid_stores)]
    
    log_progress(f"Found {len(valid_stores)} stores with at least {MIN_SPUS_PER_STORE} SPUs")
    log_progress(f"Filtered SPU data has {len(df_filtered):,} rows")
    
    # Remove anomaly stores
    df_filtered = df_filtered[~df_filtered['str_code'].isin(anomaly_stores)]
    log_progress(f"Removed {len(anomaly_stores)} anomaly stores from the dataset")
    log_progress(f"Dataset now contains {df_filtered['str_code'].nunique()} stores")
    
    return df_filtered

def create_matrix(df: pd.DataFrame, index_col: str, columns_col: str, values_col: str, matrix_type: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create and normalize a pivot matrix from the data.
    
    Args:
        df (pd.DataFrame): Input data
        index_col (str): Column to use as index (stores)
        columns_col (str): Column to use as columns (products)
        values_col (str): Column to use as values (sales)
        matrix_type (str): Type of matrix for logging
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: Original and normalized matrices
    """
    unique_products = df[columns_col].nunique()
    unique_stores = df[index_col].nunique()
    
    # Check if we need to limit SPU count for memory management
    if matrix_type.startswith('spu') and unique_products > MAX_SPU_COUNT:
        log_progress(f"Estimated {matrix_type} matrix size: {unique_stores * unique_products / 1024**2:.1f} MB ({unique_stores} stores × {unique_products} SPUs)")
        log_progress(f"SPU count ({unique_products}) exceeds limit ({MAX_SPU_COUNT})")
        log_progress(f"Creating limited SPU matrix and category-aggregated matrix...")
        
        # Create limited SPU matrix
        log_progress("Creating SPU pivot matrix...")
        log_progress(f"Limiting to top {MAX_SPU_COUNT} SPUs by sales volume for memory management")
        
        # Get top SPUs by total sales
        top_spus = df.groupby(columns_col)[values_col].sum().nlargest(MAX_SPU_COUNT).index
        df_limited = df[df[columns_col].isin(top_spus)]
        log_progress(f"Filtered to {len(df_limited):,} records with top {MAX_SPU_COUNT} SPUs")
        
        log_progress("Creating pivot table (this may take a few minutes for large datasets)...")
        matrix = df_limited.pivot_table(index=index_col, columns=columns_col, values=values_col, fill_value=0, aggfunc='sum')
        matrix_type = f"{matrix_type}_limited"
        
        # Also create category-aggregated matrix
        create_category_aggregated_matrix(df, anomaly_stores=[])
        
    else:
        log_progress(f"Creating {matrix_type} pivot matrix...")
        log_progress("Creating pivot table (this may take a few minutes for large datasets)...")
        matrix = df.pivot_table(index=index_col, columns=columns_col, values=values_col, fill_value=0, aggfunc='sum')
    
    log_progress(f"Created {matrix_type} matrix with {matrix.shape[0]} stores and {matrix.shape[1]} {columns_col.replace('_', ' ')}s")
    
    # Normalize the matrix
    log_progress(f"Normalizing {matrix_type} matrix...")
    normalized_matrix = matrix.div(matrix.sum(axis=1), axis=0).fillna(0)
    log_progress(f"Normalized {matrix_type} matrix")
    
    return matrix, normalized_matrix

def create_category_aggregated_matrix(spu_df: pd.DataFrame, anomaly_stores: List[str]) -> None:
    """
    Create category-aggregated matrix from SPU data.
    
    Args:
        spu_df (pd.DataFrame): SPU sales data
        anomaly_stores (List[str]): List of anomalous store codes to exclude
    """
    log_progress("Creating category-aggregated SPU matrix...")
    
    # Remove anomaly stores
    spu_df_clean = spu_df[~spu_df['str_code'].isin(anomaly_stores)]
    
    # Aggregate SPU sales by category
    category_agg = spu_df_clean.groupby(['str_code', 'cate_name'])['spu_sales_amt'].sum().reset_index()
    
    # Create category matrix
    category_matrix = category_agg.pivot_table(index='str_code', columns='cate_name', values='spu_sales_amt', fill_value=0, aggfunc='sum')
    log_progress(f"Created category-aggregated matrix with {category_matrix.shape[0]} stores and {category_matrix.shape[1]} categories")
    
    # Normalize the matrix
    log_progress("Normalizing category-aggregated matrix...")
    normalized_category_matrix = category_matrix.div(category_matrix.sum(axis=1), axis=0).fillna(0)
    log_progress("Normalized category-aggregated matrix")
    
    # Save matrices
    save_matrix_files(category_matrix, normalized_category_matrix, "category_agg")

def save_matrix_files(original_matrix: pd.DataFrame, normalized_matrix: pd.DataFrame, matrix_type: str) -> None:
    """
    Save matrix files and related data.
    
    Args:
        original_matrix (pd.DataFrame): Original matrix
        normalized_matrix (pd.DataFrame): Normalized matrix
        matrix_type (str): Type of matrix for file naming
    """
    # Save matrices
    original_file = f"data/store_{matrix_type}_matrix.csv"
    normalized_file = f"data/normalized_{matrix_type}_matrix.csv"
    
    original_matrix.to_csv(original_file)
    log_progress(f"Saved original {matrix_type} matrix to {original_file}")
    
    normalized_matrix.to_csv(normalized_file)
    log_progress(f"Saved normalized {matrix_type} matrix to {normalized_file}")
    
    # Save store list
    store_list_file = f"data/{matrix_type}_store_list.txt"
    with open(store_list_file, 'w') as f:
        for store in original_matrix.index:
            f.write(f"{store}\n")
    log_progress(f"Saved {matrix_type} store list to {store_list_file}")
    
    # Save product list
    if matrix_type == "subcategory":
        product_list_file = "data/subcategory_list.txt"
    elif matrix_type == "category_agg":
        product_list_file = "data/category_list.txt"
    else:
        product_list_file = "data/category_list.txt"  # For SPU matrices, save category list
    
    with open(product_list_file, 'w') as f:
        for product in original_matrix.columns:
            f.write(f"{product}\n")
    log_progress(f"Saved {matrix_type.replace('_', ' ')} list to {product_list_file}")

def main() -> None:
    """Main function to prepare clustering matrices."""
    start_time = datetime.now()
    log_progress("Starting Step 3: Prepare Clustering Matrices...")
    
    # Log current configuration
    period_label = get_period_label(current_yyyymm, current_period)
    log_progress(f"Using period: {period_label}")
    log_progress(f"Category file: {CATEGORY_FILE}")
    log_progress(f"SPU file: {SPU_FILE}")
    
    try:
        # Load coordinates and identify anomaly stores
        coords_df = load_coordinates()
        anomaly_stores = identify_anomaly_stores(coords_df)
        
        # Process subcategory-level data
        subcategory_df = load_subcategory_data()
        subcategory_filtered = filter_subcategory_data(subcategory_df, anomaly_stores)
        
        # Create subcategory matrix
        subcategory_matrix, normalized_subcategory_matrix = create_matrix(
            subcategory_filtered, 'str_code', 'sub_cate_name', 'sal_amt', 'subcategory'
        )
        
        # Save subcategory matrices
        save_matrix_files(subcategory_matrix, normalized_subcategory_matrix, "subcategory")
        
        # Save general store list (from subcategory analysis)
        with open("data/store_list.txt", 'w') as f:
            for store in subcategory_matrix.index:
                f.write(f"{store}\n")
        
        # Process SPU-level data if available
        log_progress("\n=== PROCESSING SPU-LEVEL DATA ===")
        spu_df = load_spu_data()
        
        if spu_df is not None:
            spu_filtered = filter_spu_data(spu_df, anomaly_stores)
            
            # Create SPU matrix (may be limited for memory management)
            spu_matrix, normalized_spu_matrix = create_matrix(
                spu_filtered, 'str_code', 'spu_code', 'spu_sales_amt', 'spu'
            )
            
            # Save SPU matrices
            save_matrix_files(spu_matrix, normalized_spu_matrix, "spu_limited" if spu_matrix.shape[1] <= MAX_SPU_COUNT else "spu")
            
            log_progress("✓ SPU-level matrices created successfully")
        else:
            log_progress("✗ SPU data not available - only subcategory-level analysis possible")
        
        # Final summary
        execution_time = (datetime.now() - start_time).total_seconds()
        log_progress("\n=== STEP 3 COMPLETED SUCCESSFULLY ===")
        log_progress(f"Execution time: {execution_time:.1f} seconds")
        
        # List output files
        output_files = [
            "subcategory_list.txt", "normalized_subcategory_matrix.csv", "category_list.txt",
            "spu_limited_store_list.txt", "normalized_category_agg_matrix.csv", "store_subcategory_matrix.csv",
            "store_category_agg_matrix.csv", "store_spu_limited_matrix.csv", "category_agg_store_list.txt",
            "subcategory_store_list.txt", "store_list.txt", "normalized_spu_limited_matrix.csv"
        ]
        
        log_progress("\nOutput files created:")
        for filename in output_files:
            filepath = os.path.join("data", filename)
            if os.path.exists(filepath):
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                log_progress(f"  • {filename} ({size_mb:.1f} MB)")
        
        log_progress("\nNext step: Run python src/step6_cluster_analysis.py for clustering")
        
    except Exception as e:
        log_progress(f"Error in Step 3: {str(e)}")
        raise

if __name__ == "__main__":
    main() 