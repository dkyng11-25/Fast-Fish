#!/usr/bin/env python3
"""
Step 2: Extract Store Coordinates and Create SPU Mappings

This step extracts store coordinates from API data and creates mappings
for both subcategory-level and SPU-level analysis.

For SPU-level analysis, this step also creates:
- SPU-to-store mappings
- SPU metadata for downstream processing
- Store-level coordinates (unchanged from subcategory analysis)

Author: Data Pipeline
Date: 2025-06-14
"""

import pandas as pd
import os
import sys
import re
from typing import Tuple, List, Dict, Set, Optional
from datetime import datetime
from tqdm import tqdm

# Import configuration system
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import get_api_data_files, get_current_period, get_period_label

# Get current period configuration
current_yyyymm, current_period = get_current_period()
api_files = get_api_data_files(current_yyyymm, current_period)

# Configuration - now uses dynamic file paths
CATEGORY_FILE = api_files['category_sales']
SPU_FILE = api_files['spu_sales']
SALES_DATA_FILE = api_files['store_sales']
OUTPUT_FILE = "data/store_coordinates_extended.csv"
SPU_MAPPING_FILE = "data/spu_store_mapping.csv"
SPU_METADATA_FILE = "data/spu_metadata.csv"
STORE_CODES_FILE = "data/store_codes.csv"

# Create necessary directories
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

def log_progress(message: str) -> None:
    """
    Log progress with timestamp and debug information.
    
    Args:
        message (str): Progress message to log
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def create_spu_mappings(spu_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create SPU-to-store mappings and SPU metadata from SPU sales data.
    
    Args:
        spu_df (pd.DataFrame): SPU sales data
        
    Returns:
        Tuple containing SPU mapping DataFrame and SPU metadata DataFrame
    """
    log_progress("Creating SPU mappings and metadata...")
    
    print(f"[DEBUG] Processing {len(spu_df):,} SPU records")
    
    # Create SPU-store mapping (one row per SPU-store combination)
    spu_mapping = spu_df[['spu_code', 'str_code', 'str_name', 'cate_name', 'sub_cate_name', 'spu_sales_amt']].copy()
    spu_mapping = spu_mapping.drop_duplicates()
    
    log_progress(f"Created SPU-store mapping with {len(spu_mapping):,} unique SPU-store combinations")
    
    # Create SPU metadata (one row per unique SPU)
    spu_metadata = spu_df.groupby(['spu_code', 'cate_name', 'sub_cate_name']).agg({
        'str_code': 'nunique',  # Number of stores selling this SPU
        'spu_sales_amt': ['sum', 'mean', 'std']  # Sales statistics
    }).reset_index()
    
    # Flatten column names
    spu_metadata.columns = ['spu_code', 'cate_name', 'sub_cate_name', 'store_count', 'total_sales', 'avg_sales', 'std_sales']
    spu_metadata['std_sales'] = spu_metadata['std_sales'].fillna(0)
    
    log_progress(f"Created SPU metadata for {len(spu_metadata):,} unique SPUs")
    
    # Debug: Show SPU distribution by category
    category_counts = spu_metadata.groupby('cate_name')['spu_code'].count().sort_values(ascending=False)
    print(f"[DEBUG] SPU distribution by category:")
    for category, count in category_counts.head(10).items():
        print(f"[DEBUG]   {category}: {count} SPUs")
    
    return spu_mapping, spu_metadata

def extract_coordinates_from_api_data() -> None:
    """
    Extract store coordinates from API data and create SPU mappings.
    Supports both subcategory-level and SPU-level analysis.
    """
    log_progress("Extracting coordinates and creating SPU mappings...")
    
    # Try to find various API data sources
    potential_sales_paths = [
        SALES_DATA_FILE,  # Standard path
        SALES_DATA_FILE.replace("../", ""),  # Without ../ prefix
        os.path.join("../../", SALES_DATA_FILE.replace("../", "")),  # From deeper directory
        os.path.join("data/api_data", os.path.basename(SALES_DATA_FILE)),  # From project root
        "data/api_data/store_sales_data.csv"  # Legacy fallback
    ]
    
    # Try to load store sales data with coordinates
    sales_df = None
    for path in potential_sales_paths:
        if os.path.exists(path):
            try:
                log_progress(f"Found store sales data at {path}")
                sales_df = pd.read_csv(path)
                break
            except Exception as e:
                log_progress(f"Error reading {path}: {str(e)}")
    
    if sales_df is not None and 'long_lat' in sales_df.columns:
        log_progress(f"Found long_lat coordinates in store sales data")
        
        # Get unique store codes and their coordinates
        unique_stores = sales_df.drop_duplicates(subset=['str_code'])[['str_code', 'long_lat']]
        log_progress(f"Found {len(unique_stores)} unique stores with coordinates")
        
        # Extract longitude and latitude from the "long_lat" column
        coordinates = []
        for _, row in tqdm(unique_stores.iterrows(), total=len(unique_stores), desc="Processing coordinates"):
            try:
                # The format is "longitude,latitude"
                if pd.notna(row['long_lat']):
                    parts = row['long_lat'].split(',')
                    if len(parts) == 2:
                        longitude, latitude = float(parts[0]), float(parts[1])
                        coordinates.append({
                            'str_code': row['str_code'],
                            'longitude': longitude,
                            'latitude': latitude
                        })
            except Exception as e:
                log_progress(f"Error parsing coordinates for store {row['str_code']}: {str(e)}")
        
        # Create dataframe and save
        coords_df = pd.DataFrame(coordinates)
        log_progress(f"Extracted coordinates for {len(coords_df)} stores")
        
        # Save coordinates file
        coords_df.to_csv(OUTPUT_FILE, index=False)
        log_progress(f"Saved coordinates to {OUTPUT_FILE}")
        
        # Process SPU-level data if available
        process_spu_data(coords_df)
        return
    
    # If we couldn't find coordinates in store_sales_data.csv, try other approaches
    log_progress("Attempting to get store list from category data...")
    
    # Try to find the category sales data
    potential_category_paths = [
        CATEGORY_FILE,  # Standard path
        CATEGORY_FILE.replace("../", ""),  # Without ../ prefix
        os.path.join("../../", CATEGORY_FILE.replace("../", "")),  # From deeper directory
        os.path.join("data/api_data", os.path.basename(CATEGORY_FILE)),  # From project root
        "data/api_data/complete_category_sales_202505.csv"  # Legacy fallback
    ]
    
    # Try to load category sales data
    category_df = None
    for path in potential_category_paths:
        if os.path.exists(path):
            try:
                log_progress(f"Found category sales data at {path}")
                category_df = pd.read_csv(path)
                break
            except Exception as e:
                log_progress(f"Error reading {path}: {str(e)}")
    
    # If we have category data, extract store codes
    if category_df is not None and 'str_code' in category_df.columns:
        store_codes = category_df['str_code'].unique()
        log_progress(f"Found {len(store_codes)} unique stores in category data")
        
        # Create a simple dataframe with default coordinates
        coords_df = pd.DataFrame({
            'str_code': store_codes,
            'latitude': 35.0,  # Default values for China
            'longitude': 105.0
        })
        
        # Save coordinates file
        coords_df.to_csv(OUTPUT_FILE, index=False)
        log_progress(f"Saved coordinates with default values to {OUTPUT_FILE}")
        
        # Process SPU-level data if available
        process_spu_data(coords_df)
        return
    
    # If we can't find data from API results, look for store_codes.csv
    log_progress("Warning: Could not find any data source to extract store codes")
    
    if os.path.exists(STORE_CODES_FILE):
        log_progress(f"Using store codes from {STORE_CODES_FILE}")
        try:
            store_codes_df = pd.read_csv(STORE_CODES_FILE)
            if 'str_code' in store_codes_df.columns:
                # Create a dataframe with default coordinates
                coords_df = pd.DataFrame({
                    'str_code': store_codes_df['str_code'],
                    'latitude': 35.0,  # Default values for China
                    'longitude': 105.0
                })
                
                # Save coordinates file
                coords_df.to_csv(OUTPUT_FILE, index=False)
                log_progress(f"Saved coordinates with default values to {OUTPUT_FILE}")
                
                # Process SPU-level data if available
                process_spu_data(coords_df)
                return
        except Exception as e:
            log_progress(f"Error reading {STORE_CODES_FILE}: {str(e)}")
    
    # If all else fails, create an empty file
    log_progress("Creating empty coordinates file with just the header.")
    with open(OUTPUT_FILE, 'w') as f:
        f.write("str_code,latitude,longitude\n")
    log_progress(f"Created empty coordinates file at {OUTPUT_FILE}")

def process_spu_data(coords_df: pd.DataFrame) -> None:
    """
    Process SPU-level data to create mappings and metadata.
    
    Args:
        coords_df (pd.DataFrame): Store coordinates DataFrame
    """
    log_progress("Processing SPU-level data...")
    
    # Check if SPU data file exists
    if not os.path.exists(SPU_FILE):
        log_progress(f"SPU data file not found at {SPU_FILE}")
        log_progress("SPU-level processing skipped - only subcategory-level analysis available")
        return
    
    try:
        # Load SPU data
        log_progress(f"Loading SPU data from {SPU_FILE}")
        spu_df = pd.read_csv(SPU_FILE)
        log_progress(f"Loaded {len(spu_df):,} SPU records")
        
        print(f"[DEBUG] SPU data columns: {list(spu_df.columns)}")
        print(f"[DEBUG] SPU data shape: {spu_df.shape}")
        print(f"[DEBUG] Unique stores in SPU data: {spu_df['str_code'].nunique()}")
        print(f"[DEBUG] Unique SPUs: {spu_df['spu_code'].nunique()}")
        
        # Create SPU mappings and metadata
        spu_mapping, spu_metadata = create_spu_mappings(spu_df)
        
        # Save SPU mapping file
        spu_mapping.to_csv(SPU_MAPPING_FILE, index=False)
        log_progress(f"Saved SPU-store mapping to {SPU_MAPPING_FILE}")
        
        # Save SPU metadata file
        spu_metadata.to_csv(SPU_METADATA_FILE, index=False)
        log_progress(f"Saved SPU metadata to {SPU_METADATA_FILE}")
        
        # Validate that all stores in SPU data have coordinates
        spu_stores = set(spu_df['str_code'].unique())
        coord_stores = set(coords_df['str_code'].unique())
        
        missing_coords = spu_stores - coord_stores
        if missing_coords:
            log_progress(f"Warning: {len(missing_coords)} stores in SPU data don't have coordinates")
        else:
            log_progress("✓ All stores in SPU data have coordinates")
        
        # Summary statistics
        log_progress("\n=== SPU DATA SUMMARY ===")
        log_progress(f"Total SPU records: {len(spu_df):,}")
        log_progress(f"Unique SPUs: {spu_df['spu_code'].nunique():,}")
        log_progress(f"Unique stores: {spu_df['str_code'].nunique():,}")
        log_progress(f"Unique categories: {spu_df['cate_name'].nunique()}")
        log_progress(f"Unique subcategories: {spu_df['sub_cate_name'].nunique()}")
        log_progress(f"Average SPUs per store: {len(spu_df) / spu_df['str_code'].nunique():.1f}")
        log_progress(f"Average stores per SPU: {len(spu_df) / spu_df['spu_code'].nunique():.1f}")
        
    except Exception as e:
        log_progress(f"Error processing SPU data: {str(e)}")
        log_progress("SPU-level processing failed - only subcategory-level analysis available")

def main() -> None:
    """Main function to extract coordinates and create SPU mappings."""
    start_time = datetime.now()
    log_progress("Starting Step 2: Extract Coordinates and Create SPU Mappings...")
    
    # Log current configuration
    period_label = get_period_label(current_yyyymm, current_period)
    log_progress(f"Using period: {period_label}")
    log_progress(f"Category file: {CATEGORY_FILE}")
    log_progress(f"SPU file: {SPU_FILE}")
    log_progress(f"Sales file: {SALES_DATA_FILE}")
    
    try:
        extract_coordinates_from_api_data()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        log_progress(f"Step 2 completed successfully in {execution_time:.1f} seconds")
        
        # Check output files
        output_files = [OUTPUT_FILE, SPU_MAPPING_FILE, SPU_METADATA_FILE]
        log_progress("\n=== OUTPUT FILES ===")
        for file_path in output_files:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                log_progress(f"✓ {file_path} ({file_size:.1f} MB)")
            else:
                log_progress(f"✗ {file_path} (not created)")
        
        log_progress("\nNext step: Run python src/step3_prepare_matrix.py for matrix preparation")
        
    except Exception as e:
        log_progress(f"Error in Step 2: {str(e)}")
        raise

if __name__ == "__main__":
    main() 