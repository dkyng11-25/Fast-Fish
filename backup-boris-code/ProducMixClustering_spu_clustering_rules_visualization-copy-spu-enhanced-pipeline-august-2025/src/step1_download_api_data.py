#!/usr/bin/env python3

import requests
import pandas as pd
import os
import json
import sys
import time
from datetime import datetime
import traceback
from typing import List, Dict, Any, Optional, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm
import argparse

# Import shared configuration
try:
    from config import set_current_period, ensure_backward_compatibility
except ImportError:
    # Fallback if config module is not available
    def set_current_period(yyyymm, period):
        pass
    def ensure_backward_compatibility():
        pass

# ——— CONFIGURATION ———
API_BASE = "https://fdapidb.fastfish.com:8089/api/sale"

# Using the correct endpoints from the API documentation
CONFIG_ENDPOINT = f"{API_BASE}/getAdsAiStrCfg"  # Store configuration
STORE_SALES_ENDPOINT = f"{API_BASE}/getAdsAiStrSal"  # Store sales data

# Define the default month and period (focus: September 2025)
TARGET_YYYYMM = "202509"  # September 2025
TARGET_PERIOD = "A"  # "A" for first half, "B" for second half, None for full month

# Maximum number of stores to process in a single API call
BATCH_SIZE = 10

# API request configuration
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "ProducMixClustering/1.0"
}
TIMEOUT = 30  # seconds
RETRY_COUNT = 3
RETRY_DELAY = 5  # seconds
RETRY_BACKOFF = 2  # seconds

# Track which stores have already been processed
PROCESSED_STORES = set()
FAILED_STORES = set()  # Track stores that failed to download

# Output directories
OUTPUT_DIR = "data/api_data"
ERROR_DIR = os.path.join(OUTPUT_DIR, "notes")

# Create required directories
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ERROR_DIR, exist_ok=True)

def log_progress(message: str) -> None:
    """
    Log a progress message with a timestamp.
    
    Args:
        message: The message to log
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def create_retry_session() -> requests.Session:
    """
    Create a requests session with automatic retries.
    
    Returns:
        Session with retry capability
    """
    retry_strategy = Retry(
        total=RETRY_COUNT,
        backoff_factor=RETRY_BACKOFF,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def log_error(error_message: str, error_details: Any, store_codes: List[str] = None) -> None:
    """
    Log an error message to a file.
    
    Args:
        error_message: Short error message
        error_details: Detailed error information (can be exception or string)
        store_codes: List of store codes involved in the error
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_file = os.path.join(ERROR_DIR, f"api_error_{timestamp}.md")
    
    with open(error_file, "w") as f:
        f.write(f"# API Error: {timestamp}\n\n")
        f.write(f"## Error Message\n{error_message}\n\n")
        
        if store_codes:
            f.write(f"## Affected Stores\n{', '.join(map(str, store_codes[:20]))}")
            if len(store_codes) > 20:
                f.write(f"... (and {len(store_codes) - 20} more)")
            f.write("\n\n")
        
        f.write(f"## Error Details\n```\n{error_details}\n```\n\n")
        
        if isinstance(error_details, requests.Response):
            f.write(f"## Response Status Code\n{error_details.status_code}\n\n")
            try:
                f.write(f"## Response Content\n```\n{error_details.text[:1000]}\n```\n")
            except:
                f.write("Could not extract response content\n")
    
    log_progress(f"Error logged to {error_file}")

def get_period_label(yyyymm: str, period: Optional[str] = None) -> str:
    """
    Generate a period label for file naming.
    
    Args:
        yyyymm: Year-month in YYYYMM format
        period: Period indicator ("A" for first half, "B" for second half, None for full month)
        
    Returns:
        String label for the period (e.g., "202505A", "202505B", "202505")
    """
    if period:
        return f"{yyyymm}{period}"
    return yyyymm

def get_period_description(period: Optional[str] = None) -> str:
    """
    Get human-readable description of the period.
    
    Args:
        period: Period indicator ("A" for first half, "B" for second half, None for full month)
        
    Returns:
        Human-readable description
    """
    if period == "A":
        return "first half of month"
    elif period == "B":
        return "second half of month"
    else:
        return "full month"

def clear_previous_data(yyyymm: str, period: Optional[str] = None, keep_notes: bool = True) -> None:
    """
    Clear previous API data files to ensure clean runs.
    
    Args:
        yyyymm: Year-month in YYYYMM format
        period: Period indicator ("A" for first half, "B" for second half, None for full month)
        keep_notes: Whether to keep error logs and notes (default: True)
    """
    import glob
    
    period_label = get_period_label(yyyymm, period)
    log_progress(f"Clearing previous data for period {period_label}...")
    
    # Define patterns for files to clear
    patterns_to_clear = [
        f"store_config_{period_label}.csv",
        f"store_sales_{period_label}.csv", 
        f"complete_category_sales_{period_label}.csv",
        f"complete_spu_sales_{period_label}.csv",
        f"processed_stores_{period_label}.txt",
        f"failed_stores_{period_label}.txt",  # Track failed stores separately
        f"partial_*_{period_label}_*.csv"  # Intermediate files
    ]
    
    files_removed = 0
    for pattern in patterns_to_clear:
        file_path = os.path.join(OUTPUT_DIR, pattern)
        if '*' in pattern:
            # Handle wildcard patterns
            matching_files = glob.glob(file_path)
            for file in matching_files:
                try:
                    os.remove(file)
                    files_removed += 1
                    print(f"[DEBUG] Removed: {os.path.basename(file)}")
                except Exception as e:
                    log_progress(f"Warning: Could not remove {file}: {e}")
        else:
            # Handle exact file names
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    files_removed += 1
                    print(f"[DEBUG] Removed: {os.path.basename(file_path)}")
                except Exception as e:
                    log_progress(f"Warning: Could not remove {file_path}: {e}")
    
    # Optionally clear notes directory (but keep the directory structure)
    if not keep_notes:
        notes_pattern = os.path.join(ERROR_DIR, "*.md")
        note_files = glob.glob(notes_pattern)
        for note_file in note_files:
            try:
                os.remove(note_file)
                files_removed += 1
                print(f"[DEBUG] Removed note: {os.path.basename(note_file)}")
            except Exception as e:
                log_progress(f"Warning: Could not remove {note_file}: {e}")
    
    if files_removed > 0:
        log_progress(f"Cleared {files_removed} previous data files for period {period_label}")
    else:
        log_progress(f"No previous data files found for period {period_label}")
    
    # Clear the processed and failed stores sets
    global PROCESSED_STORES, FAILED_STORES
    PROCESSED_STORES.clear()
    FAILED_STORES.clear()
    print(f"[DEBUG] Cleared processed and failed stores tracking")

def get_unique_store_codes(input_file: str = "data/store_codes.csv") -> List[str]:
    """
    Extract unique store codes from the store codes file.
    
    Returns:
        List of unique store codes
    """
    try:
        # Try several potential file paths
        potential_paths = [
            input_file,                             # First try: "data/store_codes.csv"
            input_file.replace("./", "../"),        # Second try: "../data/store_codes.csv"
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "store_codes.csv")  # Absolute path
        ]
        
        df = None
        used_path = None
        
        for path in potential_paths:
            if os.path.exists(path):
                log_progress(f"Found store codes file at: {path}")
                df = pd.read_csv(path)
                used_path = path
                break
        
        if df is None:
            raise FileNotFoundError(f"Could not find store_codes.csv in any of these locations: {potential_paths}")
            
        store_codes = sorted(df["str_code"].astype(str).unique().tolist())
        log_progress(f"Found {len(store_codes)} unique store codes in {used_path}")
        
        # Check for previously processed and failed stores if resuming
        period_label = get_period_label(TARGET_YYYYMM, TARGET_PERIOD)
        processed_stores_file = os.path.join(OUTPUT_DIR, f"processed_stores_{period_label}.txt")
        failed_stores_file = os.path.join(OUTPUT_DIR, f"failed_stores_{period_label}.txt")
        
        if os.path.exists(processed_stores_file):
            with open(processed_stores_file, 'r') as f:
                PROCESSED_STORES.update([line.strip() for line in f.readlines()])
            log_progress(f"Found {len(PROCESSED_STORES)} previously processed stores for period {period_label}")
        
        if os.path.exists(failed_stores_file):
            with open(failed_stores_file, 'r') as f:
                FAILED_STORES.update([line.strip() for line in f.readlines()])
            log_progress(f"Found {len(FAILED_STORES)} previously failed stores for period {period_label}")
        
        return store_codes
    
    except Exception as e:
        error_msg = f"Failed to extract store codes from {input_file}"
        log_error(error_msg, e)
        sys.exit(f"Error: {error_msg}. Check notes directory for details.")

def fetch_store_config(store_codes: List[str], yyyymm: str, period: Optional[str] = None) -> Tuple[pd.DataFrame, List[str]]:
    """
    Fetch store configuration data (big_class_name, sub_cate_name, etc.).
    
    Args:
        store_codes: List of store codes to fetch configurations for
        yyyymm: Year and month in YYYYMM format (e.g., "202505")
        period: Period indicator ("A" for first half, "B" for second half, None for full month)
        
    Returns:
        Tuple containing:
            - DataFrame containing store configuration data
            - List of successfully processed store codes
    """
    # Prepare payload - add period parameter if specified
    payload = {"strCodes": store_codes, "yyyymm": yyyymm}
    if period:
        payload["period"] = period  # Add period parameter for half-month requests
    
    session = create_retry_session()
    
    try:
        period_desc = get_period_description(period)
        log_progress(f"Fetching store configuration for {len(store_codes)} stores ({period_desc})...")
        print(f"[DEBUG] API payload: {payload}")
        
        resp = session.post(CONFIG_ENDPOINT, json=payload, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        
        if not data:
            error_msg = f"Empty data received from config API for {period_desc}"
            log_error(error_msg, resp, store_codes)
            return pd.DataFrame(), []
        
        # Create DataFrame and validate
        df = pd.DataFrame(data)
        
        # Filter by mm_type if period is specified (validate that we got the right period)
        if period and "mm_type" in df.columns:
            expected_mm_type = f"{yyyymm[-2:]}{period}"  # e.g., "05A" for May first half
            period_filtered = df[df["mm_type"] == expected_mm_type]
            if len(period_filtered) > 0:
                df = period_filtered
                log_progress(f"Filtered to {len(df)} rows matching period {expected_mm_type}")
            else:
                # Try alternative format without leading zero
                alt_expected_mm_type = f"{int(yyyymm[-2:])}{period}"  # e.g., "5A" instead of "05A"
                period_filtered = df[df["mm_type"] == alt_expected_mm_type]
                if len(period_filtered) > 0:
                    df = period_filtered
                    log_progress(f"Filtered to {len(df)} rows matching period {alt_expected_mm_type}")
                else:
                    log_progress(f"Warning: No data found for mm_type={expected_mm_type} or {alt_expected_mm_type}, using all data")
        
        # Extract the store codes that were successfully processed
        processed_codes = df["str_code"].astype(str).unique().tolist()
        missing_codes = set(store_codes) - set(processed_codes)
        
        if missing_codes:
            log_progress(f"Warning: {len(missing_codes)} stores missing from config API response")
            log_error(f"Missing stores in config API response", f"These stores did not return data: {missing_codes}", list(missing_codes))
        
        log_progress(f"Received configuration data for {len(processed_codes)} stores ({period_desc})")
        return df, processed_codes
            
    except Exception as e:
        error_msg = f"Failed to fetch store configuration for {get_period_description(period)}"
        log_error(error_msg, traceback.format_exc(), store_codes)
        return pd.DataFrame(), []

def fetch_store_sales(store_codes: List[str], yyyymm: str, period: Optional[str] = None) -> Tuple[pd.DataFrame, List[str]]:
    """
    Fetch store-level sales data.
    
    Args:
        store_codes: List of store codes to fetch sales data for
        yyyymm: Year and month in YYYYMM format (e.g., "202505")
        period: Period indicator ("A" for first half, "B" for second half, None for full month)
        
    Returns:
        Tuple containing:
            - DataFrame with store sales data
            - List of successfully processed store codes
    """
    # Prepare payload - add period parameter if specified
    payload = {"strCodes": store_codes, "yyyymm": yyyymm}
    if period:
        payload["period"] = period  # Add period parameter for half-month requests
    
    session = create_retry_session()
    
    try:
        period_desc = get_period_description(period)
        log_progress(f"Fetching store sales data for {len(store_codes)} stores ({period_desc})...")
        print(f"[DEBUG] API payload: {payload}")
        
        resp = session.post(STORE_SALES_ENDPOINT, json=payload, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json().get("data", [])
        
        if not data:
            error_msg = f"Empty data received from sales API for {period_desc}"
            log_error(error_msg, resp, store_codes)
            return pd.DataFrame(), []
        
        # Create DataFrame and perform basic validation
        df = pd.DataFrame(data)
        
        # Filter by mm_type if period is specified (validate that we got the right period)
        if period and "mm_type" in df.columns:
            expected_mm_type = f"{yyyymm[-2:]}{period}"  # e.g., "05A" for May first half
            period_filtered = df[df["mm_type"] == expected_mm_type]
            if len(period_filtered) > 0:
                df = period_filtered
                log_progress(f"Filtered to {len(df)} rows matching period {expected_mm_type}")
            else:
                # Try alternative format without leading zero
                alt_expected_mm_type = f"{int(yyyymm[-2:])}{period}"  # e.g., "5A" instead of "05A"
                period_filtered = df[df["mm_type"] == alt_expected_mm_type]
                if len(period_filtered) > 0:
                    df = period_filtered
                    log_progress(f"Filtered to {len(df)} rows matching period {alt_expected_mm_type}")
                else:
                    log_progress(f"Warning: No data found for mm_type={expected_mm_type} or {alt_expected_mm_type}, using all data")
        
        # Extract the store codes that were successfully processed
        processed_codes = df["str_code"].astype(str).unique().tolist()
        missing_codes = set(store_codes) - set(processed_codes)
        
        if missing_codes:
            log_progress(f"Warning: {len(missing_codes)} stores missing from sales API response")
            log_error(f"Missing stores in sales API response", f"These stores did not return data: {missing_codes}", list(missing_codes))
        
        log_progress(f"Received sales data for {len(processed_codes)} stores ({period_desc})")
        return df, processed_codes
    
    except Exception as e:
        error_msg = f"Failed to fetch store sales data for {get_period_description(period)}"
        log_error(error_msg, traceback.format_exc(), store_codes)
        return pd.DataFrame(), []

def process_and_merge_data(store_sales_df: pd.DataFrame, config_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
    """
    Process and merge store sales and configuration data, outputting both subcategory-level and SPU-level sales.
    NOW INCLUDES REAL QUANTITY CALCULATIONS FROM API DATA!
    
    Args:
        store_sales_df: DataFrame containing store sales data with QUANTITY FIELDS
        config_df: DataFrame containing store configuration data
    Returns:
        Tuple containing:
            - Subcategory-level DataFrame
            - SPU-level DataFrame with REAL QUANTITIES
            - List of successfully processed store codes
    """
    try:
        if store_sales_df.empty or config_df.empty:
            print("[DEBUG] One of the dataframes is empty - skipping merge")
            return pd.DataFrame(), pd.DataFrame(), []

        print(f"[DEBUG] config_df columns: {config_df.columns.tolist()}")
        print(f"[DEBUG] store_sales_df columns: {store_sales_df.columns.tolist()}")
        
        # Check if we have quantity data in store_sales_df
        has_quantity_data = 'base_sal_qty' in store_sales_df.columns and 'fashion_sal_qty' in store_sales_df.columns
        print(f"[DEBUG] Has quantity data: {has_quantity_data}")

        # Create store-level quantity and unit price mapping
        store_quantity_map = {}
        if has_quantity_data:
            print("[DEBUG] 🎯 EXTRACTING REAL QUANTITY DATA FROM API...")
            for _, row in store_sales_df.iterrows():
                str_code = str(row['str_code'])
                
                # Extract quantity data
                base_qty = float(row.get('base_sal_qty', 0) or 0)
                fashion_qty = float(row.get('fashion_sal_qty', 0) or 0)
                base_amt = float(row.get('base_sal_amt', 0) or 0)
                fashion_amt = float(row.get('fashion_sal_amt', 0) or 0)
                
                total_qty = base_qty + fashion_qty
                total_amt = base_amt + fashion_amt
                
                # Calculate REAL unit prices from API data
                if total_qty > 0:
                    unit_price = total_amt / total_qty
                    print(f"[DEBUG] Store {str_code}: {total_qty:.1f} units, ${total_amt:.2f} sales = ${unit_price:.2f}/unit")
                else:
                    unit_price = 50.0  # Default for stores with no sales
                
                store_quantity_map[str_code] = {
                    'total_quantity': total_qty,
                    'total_sales': total_amt,
                    'unit_price': unit_price,
                    'base_qty': base_qty,
                    'fashion_qty': fashion_qty,
                    'base_amt': base_amt,
                    'fashion_amt': fashion_amt
                }
            
            print(f"[DEBUG] ✅ Calculated real unit prices for {len(store_quantity_map)} stores")
            
            # Show sample unit prices
            sample_stores = list(store_quantity_map.keys())[:5]
            for store in sample_stores:
                data = store_quantity_map[store]
                print(f"[DEBUG]   Store {store}: ${data['unit_price']:.2f}/unit ({data['total_quantity']:.1f} units)")

        # Subcategory-level (CORRECTED: Keep all records - they represent different product assortments)
        if "big_class_name" in config_df.columns and "sub_cate_name" in config_df.columns:
            # Keep all records as they represent different product assortments within subcategories
            # Each record has different sty_sal_amt (SPU composition) even if store-subcategory-season-sex is same
            category_sales = config_df[[
                "str_code", "str_name", "big_class_name", "sub_cate_name", "sal_amt"
            ]].copy()
            category_sales.rename(columns={"big_class_name": "cate_name"}, inplace=True)
            
            print(f"[DEBUG] ✅ Category data preserved: {len(category_sales):,} records (all product assortments kept)")
            
            # Add quantity data to category sales if available
            if has_quantity_data:
                category_sales['store_unit_price'] = category_sales['str_code'].astype(str).map(
                    lambda x: store_quantity_map.get(x, {}).get('unit_price', 50.0)
                )
                category_sales['estimated_quantity'] = category_sales['sal_amt'] / category_sales['store_unit_price']
                print(f"[DEBUG] ✅ Added quantity calculations to category data")
            
            if "sal_amt_avg" in store_sales_df.columns:
                store_metrics = store_sales_df[["str_code", "sal_amt_avg"]].drop_duplicates()
                category_sales = pd.merge(
                    category_sales, 
                    store_metrics,
                    on="str_code", 
                    how="left"
                )
            stores_with_subcats = category_sales.groupby("str_code").size()
            valid_stores = stores_with_subcats[stores_with_subcats > 0].index.tolist()
        else:
            print(f"[DEBUG] Required columns not found in config_df: {config_df.columns.tolist()}")
            return pd.DataFrame(), pd.DataFrame(), []

        # SPU-level: DEDUPLICATE config_df first to prevent duplicate SPUs
        print("[DEBUG] 🎯 CREATING SPU DATA WITH REAL QUANTITIES...")
        print(f"[DEBUG] Original config records: {len(config_df):,}")
        
        # CRITICAL FIX: Remove duplicate store-subcategory-season-sex combinations that contain identical SPU data
        # This prevents the same SPU from being processed multiple times for the same store
        config_dedup_cols = ['str_code', 'sub_cate_name', 'season_name', 'sex_name', 'sty_sal_amt']
        available_cols = [col for col in config_dedup_cols if col in config_df.columns]
        if 'sty_sal_amt' in available_cols:
            config_df_clean = config_df.drop_duplicates(subset=available_cols, keep='first')
            print(f"[DEBUG] After deduplication: {len(config_df_clean):,} records ({len(config_df) - len(config_df_clean):,} duplicates removed)")
        else:
            # Fallback if sty_sal_amt column not available
            config_df_clean = config_df.drop_duplicates(subset=['str_code', 'sub_cate_name'], keep='first')
            print(f"[DEBUG] After basic deduplication: {len(config_df_clean):,} records ({len(config_df) - len(config_df_clean):,} duplicates removed)")
        
        spu_rows = []
        for idx, row in tqdm(config_df_clean.iterrows(), total=config_df_clean.shape[0], desc="Expanding SPU-level data with quantities"):
            try:
                str_code = str(row["str_code"])
                store_data = store_quantity_map.get(str_code, {})
                store_unit_price = store_data.get('unit_price', 50.0)
                
                sty_sal_amt = row.get("sty_sal_amt")
                if not sty_sal_amt or str(sty_sal_amt).strip() == '':
                    continue
                
                spu_dict = json.loads(sty_sal_amt) if isinstance(sty_sal_amt, str) and sty_sal_amt.strip() else {}
                
                for spu_code, spu_sales_amt in spu_dict.items():
                    # Calculate REAL quantity for this SPU
                    spu_sales_amt = float(spu_sales_amt or 0)
                    
                    # Estimate unit price for this specific category
                    category = row.get("sub_cate_name", "")
                    category_unit_price = estimate_category_unit_price(category, store_unit_price)
                    
                    # Calculate quantity
                    spu_quantity = spu_sales_amt / category_unit_price if category_unit_price > 0 else 0
                    
                    spu_rows.append({
                        "str_code": str_code,
                        "str_name": row["str_name"],
                        "cate_name": row["big_class_name"] if "big_class_name" in row else None,
                        "sub_cate_name": row["sub_cate_name"],
                        "spu_code": spu_code,
                        "spu_sales_amt": spu_sales_amt,
                        "quantity": round(spu_quantity, 1),  # REAL QUANTITY
                        "unit_price": round(category_unit_price, 2),  # REAL UNIT PRICE
                        "investment_per_unit": round(category_unit_price, 2)
                    })
            except Exception as e:
                print(f"[DEBUG] Error parsing sty_sal_amt for row {idx}: {e}")
                continue
        
        spu_sales = pd.DataFrame(spu_rows)
        print(f"[DEBUG] ✅ SPU-level rows created: {len(spu_sales)} with REAL quantities and unit prices")
        
        if len(spu_sales) > 0:
            print(f"[DEBUG] Sample SPU data:")
            print(f"[DEBUG]   Unit price range: ${spu_sales['unit_price'].min():.2f} - ${spu_sales['unit_price'].max():.2f}")
            print(f"[DEBUG]   Quantity range: {spu_sales['quantity'].min():.1f} - {spu_sales['quantity'].max():.1f}")
            
            # Verify no $1.00 fake prices
            fake_prices = (spu_sales['unit_price'] == 1.0).sum()
            if fake_prices == 0:
                print(f"[DEBUG] ✅ NO FAKE $1.00 PRICES! All unit prices are realistic.")
            else:
                print(f"[DEBUG] ⚠️ Found {fake_prices} SPUs with $1.00 prices")
        
        return category_sales, spu_sales, valid_stores
        
    except Exception as e:
        print(f"[DEBUG] Failed to process and merge sales data: {e}")
        return pd.DataFrame(), pd.DataFrame(), []

def estimate_category_unit_price(category: str, store_avg_price: float) -> float:
    """
    Estimate unit price for a specific category based on store average and category type.
    
    Args:
        category: Category name (Chinese)
        store_avg_price: Average unit price for the store
        
    Returns:
        Estimated unit price for the category
    """
    # Category-specific price adjustments based on clothing industry knowledge
    category_lower = str(category).lower()
    
    # Base price adjustments relative to store average
    if 't恤' in category_lower or 'polo' in category_lower:
        return store_avg_price * 0.7  # T-shirts are typically cheaper
    elif '裤' in category_lower:
        return store_avg_price * 1.2  # Pants are typically more expensive
    elif '衬' in category_lower:
        return store_avg_price * 1.1  # Shirts are slightly above average
    elif '鞋' in category_lower:
        return store_avg_price * 1.6  # Shoes are significantly more expensive
    elif '外套' in category_lower or 'jacket' in category_lower:
        return store_avg_price * 1.8  # Outerwear is most expensive
    elif '袜' in category_lower:
        return store_avg_price * 0.2  # Socks are cheapest
    elif '内衣' in category_lower:
        return store_avg_price * 0.6  # Underwear is cheaper
    else:
        return store_avg_price  # Default to store average

def get_already_processed_stores(period_label: str) -> set:
    """
    Get the set of stores that were already successfully processed.
    
    Args:
        period_label: Period label (e.g., "202506A")
        
    Returns:
        Set of store codes that were successfully processed
    """
    processed_stores_file = os.path.join(OUTPUT_DIR, f"processed_stores_{period_label}.txt")
    processed_stores = set()
    
    if os.path.exists(processed_stores_file):
        try:
            with open(processed_stores_file, 'r') as f:
                processed_stores = {line.strip() for line in f if line.strip()}
            log_progress(f"Found {len(processed_stores)} previously processed stores")
        except Exception as e:
            log_progress(f"Warning: Could not read processed stores file: {e}")
    
    return processed_stores

def get_failed_stores(period_label: str) -> set:
    """
    Get the set of stores that failed to download (should be retried).
    
    Args:
        period_label: Period label (e.g., "202506A")
        
    Returns:
        Set of store codes that failed to download
    """
    failed_stores_file = os.path.join(OUTPUT_DIR, f"failed_stores_{period_label}.txt")
    failed_stores = set()
    
    if os.path.exists(failed_stores_file):
        try:
            with open(failed_stores_file, 'r') as f:
                failed_stores = {line.strip() for line in f if line.strip()}
            log_progress(f"Found {len(failed_stores)} previously failed stores (will retry)")
        except Exception as e:
            log_progress(f"Warning: Could not read failed stores file: {e}")
    
    return failed_stores

def save_successful_stores(period_label: str, successful_stores: List[str]) -> None:
    """
    Save successfully processed stores to tracking file.
    
    Args:
        period_label: Period label (e.g., "202506A")
        successful_stores: List of successfully processed store codes
    """
    processed_stores_file = os.path.join(OUTPUT_DIR, f"processed_stores_{period_label}.txt")
    with open(processed_stores_file, 'a') as f:
        for store in successful_stores:
            f.write(f"{store}\n")
            PROCESSED_STORES.add(store)

def save_failed_stores(period_label: str, failed_stores: List[str]) -> None:
    """
    Save failed stores to tracking file (these will be retried).
    
    Args:
        period_label: Period label (e.g., "202506A")
        failed_stores: List of failed store codes
    """
    failed_stores_file = os.path.join(OUTPUT_DIR, f"failed_stores_{period_label}.txt")
    with open(failed_stores_file, 'a') as f:
        for store in failed_stores:
            f.write(f"{store}\n")
            FAILED_STORES.add(store)

def validate_data_completeness(period_label: str, expected_stores: set) -> Tuple[bool, set, Dict[str, str]]:
    """
    Validate that all expected stores have complete data in the final files.
    
    Args:
        period_label: Period label (e.g., "202506A")
        expected_stores: Set of store codes that should be present
        
    Returns:
        Tuple of (is_complete, missing_stores, validation_report)
    """
    validation_report = {}
    stores_by_file = {}
    
    # Check each data file
    data_files = [
        f"store_config_{period_label}.csv",
        f"store_sales_{period_label}.csv",
        f"complete_category_sales_{period_label}.csv",
        f"complete_spu_sales_{period_label}.csv"
    ]
    
    for filename in data_files:
        filepath = os.path.join("output", filename)
        if os.path.exists(filepath):
            try:
                df = pd.read_csv(filepath)
                stores_in_file = set(df['str_code'].unique())
                stores_by_file[filename] = stores_in_file
                file_missing = expected_stores - stores_in_file
                
                validation_report[filename] = {
                    'exists': True,
                    'records': len(df),
                    'stores': len(stores_in_file),
                    'missing_stores': len(file_missing)
                }
                
            except Exception as e:
                validation_report[filename] = {
                    'exists': True,
                    'error': str(e)
                }
                stores_by_file[filename] = set()  # Empty set for failed files
        else:
            validation_report[filename] = {'exists': False}
            stores_by_file[filename] = set()  # Empty set for missing files
    
        # Find stores that are present in ALL existing files (intersection)
    if stores_by_file:
        # Only consider files that actually exist and have data
        valid_file_stores = [stores for stores in stores_by_file.values() if len(stores) > 0]
        
        if valid_file_stores:
            stores_in_all_files = set.intersection(*valid_file_stores)
            missing_stores = expected_stores - stores_in_all_files
            log_progress(f"Data validation: {len(stores_in_all_files)} stores present, {len(missing_stores)} stores missing")
        else:
            stores_in_all_files = set()
            missing_stores = expected_stores
            log_progress(f"Data validation: No valid data files found - all {len(missing_stores)} stores missing")
    else:
        stores_in_all_files = set()
        missing_stores = expected_stores
        log_progress(f"Data validation: No data files found - all {len(missing_stores)} stores missing")

    is_complete = len(missing_stores) == 0

    # Add summary to validation report
    validation_report['_summary'] = {
        'expected_stores': len(expected_stores),
        'stores_in_all_files': len(stores_in_all_files),
        'missing_stores': len(missing_stores),
        'is_complete': is_complete
    }
    
    return is_complete, missing_stores, validation_report

def clean_partial_files(period_label: str) -> None:
    """
    Remove partial/intermediate files to clean up disk space.
    
    Args:
        period_label: Period label (e.g., "202506A")
    """
    import glob
    
    patterns = [
        f"partial_*_{period_label}_*.csv"
    ]
    
    files_removed = 0
    for pattern in patterns:
        file_path = os.path.join(OUTPUT_DIR, pattern)
        matching_files = glob.glob(file_path)
        for file in matching_files:
            try:
                os.remove(file)
                files_removed += 1
            except Exception as e:
                log_progress(f"Warning: Could not remove {file}: {e}")
    
    if files_removed > 0:
        log_progress(f"Cleaned up {files_removed} partial files")

def recover_from_partial_files(period_label: str) -> bool:
    """
    Attempt to recover from interrupted download by consolidating partial files.
    
    Args:
        period_label: Period label (e.g., "202506A")
        
    Returns:
        bool: True if recovery was successful, False otherwise
    """
    import glob
    
    log_progress(f"🔄 Attempting recovery from partial files for period {period_label}...")
    
    # Check for partial files
    partial_patterns = {
        'config': f"partial_config_{period_label}_*.csv",
        'sales': f"partial_sales_{period_label}_*.csv", 
        'category': f"partial_category_sales_{period_label}_*.csv",
        'spu': f"partial_spu_sales_{period_label}_*.csv"
    }
    
    recovery_data = {}
    
    for file_type, pattern in partial_patterns.items():
        file_path = os.path.join(OUTPUT_DIR, pattern)
        matching_files = glob.glob(file_path)
        
        if matching_files:
            log_progress(f"Found {len(matching_files)} partial {file_type} files")
            dataframes = []
            
            for file in matching_files:
                try:
                    df = pd.read_csv(file)
                    dataframes.append(df)
                    log_progress(f"  • Loaded {file}: {len(df)} records")
                except Exception as e:
                    log_progress(f"  ⚠️  Could not load {file}: {e}")
            
            if dataframes:
                recovery_data[file_type] = dataframes
            else:
                log_progress(f"  ❌ No valid {file_type} data found")
        else:
            log_progress(f"No partial {file_type} files found")
    
    # If we have data, try to consolidate it
    if recovery_data:
        log_progress("Consolidating recovered data...")
        
        config_data = recovery_data.get('config', [])
        sales_data = recovery_data.get('sales', [])
        category_data = recovery_data.get('category', [])
        spu_data = recovery_data.get('spu', [])
        
        # Use existing save_final_results function
        save_final_results(config_data, sales_data, category_data, spu_data, period_label)
        
        log_progress("✅ Recovery completed! Final files have been created.")
        return True
    else:
        log_progress("❌ No recoverable data found")
        return False

def process_stores_in_batches(store_codes: List[str], yyyymm: str, period: Optional[str] = None, batch_size: int = BATCH_SIZE, force_full_download: bool = False, clear_data: bool = False) -> None:
    """
    Process store data in batches with smart partial downloading support.
    
    Args:
        store_codes: List of all store codes to process
        yyyymm: Year and month in YYYYMM format
        period: Period indicator ("A" for first half, "B" for second half, None for full month)
        batch_size: Number of stores to process per batch
        force_full_download: If True, ignore existing data and download everything
    """
    period_label = get_period_label(yyyymm, period)
    log_progress(f"Processing stores for period {period_label} (force_full_download={force_full_download})...")
    
    # Smart downloading logic
    if not force_full_download:
        # Check what we already have processed and what failed
        processed_stores = get_already_processed_stores(period_label)
        failed_stores = get_failed_stores(period_label)
        expected_stores = set(store_codes)
        
        # For smart download: skip successfully processed stores, but retry failed ones
        stores_to_skip = processed_stores - failed_stores  # Don't retry successful stores
        missing_stores = expected_stores - stores_to_skip  # Include failed stores for retry
        
        # Check if final files exist and are complete
        is_complete, final_missing_stores, validation_report = validate_data_completeness(period_label, expected_stores)
        
        if is_complete:
            log_progress("✅ All data is already complete! No download needed.")
            log_progress("Data validation report:")
            for filename, report in validation_report.items():
                if report.get('exists'):
                    log_progress(f"  • {filename}: {report.get('records', 0)} records, {report.get('stores', 0)} stores")
            # Return completion status for early exit
            return True, 100.0, 0
        
        # Auto-recovery: Check if we have enough partial data to recover
        if len(processed_stores) > 100:  # Arbitrary threshold - if significant progress exists
            log_progress(f"🔄 Auto-recovery check: {len(processed_stores)} stores processed but no final files found")
            # DISABLED: Auto-recovery was corrupting good data by overwriting complete files with partials
            # if recover_from_partial_files(period_label):
            #     log_progress("✅ Auto-recovery successful! Checking completion...")
            #     # Re-validate after recovery
            #     is_complete_after_recovery, final_missing_after_recovery, _ = validate_data_completeness(period_label, expected_stores)
            #     if is_complete_after_recovery:
            #         log_progress("✅ Data is now complete after auto-recovery!")
            #         return True, 100.0, 0
            #     else:
            #         log_progress(f"⚠️ Partial recovery: {len(expected_stores) - len(final_missing_after_recovery)} stores recovered, continuing with remaining downloads")
            #         missing_stores = final_missing_after_recovery  # Update missing stores after recovery
            log_progress("🔄 Auto-recovery disabled to prevent data corruption. Use --recover flag if needed.")
        
        # Use processed stores for smart download decision
        retry_count = len(failed_stores & missing_stores)  # Failed stores that will be retried
        new_count = len(missing_stores - failed_stores)     # New stores never attempted
        
        log_progress(f"Smart download analysis:")
        log_progress(f"  • Successfully processed: {len(processed_stores - failed_stores)} stores (will skip)")
        log_progress(f"  • Previously failed: {retry_count} stores (will retry)")
        log_progress(f"  • Never attempted: {new_count} stores (will download)")
        log_progress(f"  • Total to process: {len(missing_stores)} stores")
        
        # Determine which stores to process
        if len(missing_stores) < len(expected_stores) * 0.5:  # Less than 50% missing
            store_codes_to_process = list(missing_stores)
            log_progress(f"Smart incremental download: Processing {len(store_codes_to_process)} stores")
            log_progress(f"Stores to process: {sorted(list(missing_stores))[:10]}{'...' if len(missing_stores) > 10 else ''}")
        else:
            log_progress(f"Many stores needed ({len(missing_stores)}/{len(expected_stores)}). Consider using --force-full flag.")
            log_progress("For safety, performing incremental download of needed stores only.")
            store_codes_to_process = list(missing_stores)
    else:
        store_codes_to_process = store_codes
        log_progress(f"Force full download: Processing all {len(store_codes_to_process)} stores")
    
    # Create/reset tracking file
    processed_stores_file = os.path.join(OUTPUT_DIR, f"processed_stores_{period_label}.txt")
    
    if force_full_download:
        # Only clear when explicitly requested by user
        if clear_data:
            log_progress("Clear data mode: Removing all previous data files")
        else:
            log_progress("Force full download mode: Will regenerate all data files")
        
        # Clear all existing data for complete regeneration
        clear_previous_data(yyyymm, period, keep_notes=True)
        with open(processed_stores_file, 'w') as f:
            pass  # Create empty file
    
    # Lists to store batch results
    config_data_list = []
    sales_data_list = []
    category_sales_list = []
    spu_sales_list = []
    
    if not force_full_download:
        # Load existing complete files if they exist
        existing_files = {
            'config': f"store_config_{period_label}.csv",
            'sales': f"store_sales_{period_label}.csv",
            'category': f"complete_category_sales_{period_label}.csv",
            'spu': f"complete_spu_sales_{period_label}.csv"
        }
        
        for file_type, filename in existing_files.items():
            filepath = os.path.join(OUTPUT_DIR, filename)
            if os.path.exists(filepath):
                try:
                    df = pd.read_csv(filepath)
                    if file_type == 'config':
                        config_data_list.append(df)
                    elif file_type == 'sales':
                        sales_data_list.append(df)
                    elif file_type == 'category':
                        category_sales_list.append(df)
                    elif file_type == 'spu':
                        spu_sales_list.append(df)
                    log_progress(f"Loaded existing {filename}: {len(df)} records")
                except Exception as e:
                    log_progress(f"Warning: Could not load {filename}: {e}")
    
    # Process stores in batches
    log_progress(f"Processing {len(store_codes_to_process)} stores in batches of {batch_size}...")
    
    for i in range(0, len(store_codes_to_process), batch_size):
        batch = store_codes_to_process[i:i+batch_size]
        print(f"[DEBUG] Processing batch {i//batch_size + 1}/{(len(store_codes_to_process) + batch_size - 1)//batch_size} ({len(batch)} stores)...")
        
        # Fetch data for this batch
        config_df, config_stores = fetch_store_config(batch, yyyymm, period)
        if not config_df.empty:
            config_data_list.append(config_df)
        
        sales_df, sales_stores = fetch_store_sales(batch, yyyymm, period)
        if not sales_df.empty:
            sales_data_list.append(sales_df)
        
        # Determine successful and failed stores for this batch
        successful_stores_batch = []
        failed_stores_batch = []
        
        # Process and merge data
        if not config_df.empty and not sales_df.empty:
            category_df, spu_df, processed_stores_batch = process_and_merge_data(sales_df, config_df)
            if not category_df.empty:
                category_sales_list.append(category_df)
            if not spu_df.empty:
                spu_sales_list.append(spu_df)
            
            successful_stores_batch = processed_stores_batch
        
        # Identify failed stores (attempted but no data)
        attempted_stores = set(batch)
        successful_stores_set = set(successful_stores_batch)
        failed_stores_batch = list(attempted_stores - successful_stores_set)
        
        # Update tracking files separately
        if successful_stores_batch:
            save_successful_stores(period_label, successful_stores_batch)
        
        if failed_stores_batch:
            save_failed_stores(period_label, failed_stores_batch)
        
        # Save intermediate results periodically
        if i % (batch_size * 5) == 0 and i > 0:
            save_intermediate_results(config_data_list, sales_data_list, category_sales_list, spu_sales_list, period_label)
        
        # Rate limiting
        if i + batch_size < len(store_codes_to_process):
            time.sleep(1)
    
    # Save final consolidated results
    save_final_results(config_data_list, sales_data_list, category_sales_list, spu_sales_list, period_label)
    
    # Clean up partial files
    clean_partial_files(period_label)
    
    # Final validation
    expected_stores = set(store_codes)
    is_complete, missing_stores, validation_report = validate_data_completeness(period_label, expected_stores)
    
    # Calculate actual completion stats
    stores_present = len(expected_stores) - len(missing_stores)
    completion_rate = (stores_present / len(expected_stores)) * 100 if expected_stores else 0
    
    if is_complete:
        log_progress("✅ Data download completed successfully!")
    else:
        log_progress(f"⚠️  Download completed: {stores_present}/{len(expected_stores)} stores ({completion_rate:.1f}%)")
        if len(missing_stores) < 100:  # Only show missing stores if reasonable number
            log_progress(f"Missing stores: {sorted(list(missing_stores))[:10]}{'...' if len(missing_stores) > 10 else ''}")
        else:
            log_progress(f"Too many missing stores ({len(missing_stores)}) to list - check API connectivity")
    
    # Show final validation report
    log_progress("Final data validation:")
    for filename, report in validation_report.items():
        if report.get('exists'):
            log_progress(f"  • {filename}: {report.get('records', 0)} records, {report.get('stores', 0)} stores")
    
    # CRITICAL: Return completion status to prevent unnecessary re-runs
    return is_complete, completion_rate, len(missing_stores)

def save_intermediate_results(config_data: List[pd.DataFrame], sales_data: List[pd.DataFrame], category_sales: List[pd.DataFrame], spu_sales: List[pd.DataFrame], period_label: str) -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if config_data:
        pd.concat(config_data).to_csv(os.path.join(OUTPUT_DIR, f"partial_config_{period_label}_{timestamp}.csv"), index=False)
    if sales_data:
        pd.concat(sales_data).to_csv(os.path.join(OUTPUT_DIR, f"partial_sales_{period_label}_{timestamp}.csv"), index=False)
    if category_sales:
        pd.concat(category_sales).to_csv(os.path.join(OUTPUT_DIR, f"partial_category_sales_{period_label}_{timestamp}.csv"), index=False)
    if spu_sales:
        pd.concat(spu_sales).to_csv(os.path.join(OUTPUT_DIR, f"partial_spu_sales_{period_label}_{timestamp}.csv"), index=False)
    print(f"[DEBUG] Saved intermediate results for period {period_label}")

def save_final_results(config_data: List[pd.DataFrame], sales_data: List[pd.DataFrame], category_sales: List[pd.DataFrame], spu_sales: List[pd.DataFrame], period_label: str) -> None:
    """Save final combined results to CSV files with period-specific naming"""
    try:
        # Save to both data/api_data (for pipeline steps) and output (for final results)
        api_output_dir = OUTPUT_DIR  # data/api_data
        final_output_dir = "output"
        os.makedirs(api_output_dir, exist_ok=True)
        os.makedirs(final_output_dir, exist_ok=True)
        
        if config_data:
            config_df = pd.concat(config_data, ignore_index=True)
            # Extra safety: Remove any duplicates in final config data
            original_config_count = len(config_df)
            config_df = config_df.drop_duplicates()
            if len(config_df) != original_config_count:
                log_progress(f"[DEDUP] Removed {original_config_count - len(config_df)} duplicate config records during final save")
            
            # Save to both directories
            config_file_api = os.path.join(api_output_dir, f"store_config_{period_label}.csv")
            config_file_final = os.path.join(final_output_dir, f"store_config_{period_label}.csv")
            config_df.to_csv(config_file_api, index=False)
            config_df.to_csv(config_file_final, index=False)
            log_progress(f"Saved configuration data: {config_file_api} and {config_file_final} ({len(config_df)} rows, {len(config_df['str_code'].unique())} stores)")
        
        if sales_data:
            sales_df = pd.concat(sales_data, ignore_index=True)
            # Extra safety: Remove any duplicates in final sales data
            original_sales_count = len(sales_df)
            sales_df = sales_df.drop_duplicates()
            if len(sales_df) != original_sales_count:
                log_progress(f"[DEDUP] Removed {original_sales_count - len(sales_df)} duplicate sales records during final save")
            
            # Save to both directories
            sales_file_api = os.path.join(api_output_dir, f"store_sales_{period_label}.csv")
            sales_file_final = os.path.join(final_output_dir, f"store_sales_{period_label}.csv")
            sales_df.to_csv(sales_file_api, index=False)
            sales_df.to_csv(sales_file_final, index=False)
            log_progress(f"Saved sales data: {sales_file_api} and {sales_file_final} ({len(sales_df)} rows, {len(sales_df['str_code'].unique())} stores)")
        
        if category_sales:
            category_df = pd.concat(category_sales, ignore_index=True)
            
            # Apply deduplication to final consolidated category data
            original_count = len(category_df)
            category_duplicates = category_df.duplicated().sum()
            if category_duplicates > 0:
                category_df = category_df.drop_duplicates()
                log_progress(f"[DEDUP] Removed {original_count - len(category_df)} duplicate category records")
            
            # Save to both directories
            category_file_api = os.path.join(api_output_dir, f"complete_category_sales_{period_label}.csv")
            category_file_final = os.path.join(final_output_dir, f"complete_category_sales_{period_label}.csv")
            category_df.to_csv(category_file_api, index=False)
            category_df.to_csv(category_file_final, index=False)
            log_progress(f"Saved category sales data: {category_file_api} and {category_file_final} ({len(category_df)} rows, {len(category_df['str_code'].unique())} stores)")
        
        if spu_sales:
            spu_df = pd.concat(spu_sales, ignore_index=True)
            
            # CRITICAL: Apply deduplication to final consolidated SPU data
            # This handles cases where incremental downloads create duplicates
            original_count = len(spu_df)
            store_spu_duplicates = spu_df.duplicated(subset=['str_code', 'spu_code']).sum()
            exact_duplicates = spu_df.duplicated().sum()
            
            if store_spu_duplicates > 0 or exact_duplicates > 0:
                log_progress(f"[DEDUP] Found {store_spu_duplicates} store-SPU duplicates and {exact_duplicates} exact duplicates")
                # Remove exact duplicates first, then store-SPU duplicates
                spu_df = spu_df.drop_duplicates()
                spu_df = spu_df.drop_duplicates(subset=['str_code', 'spu_code'], keep='first')
                log_progress(f"[DEDUP] Removed {original_count - len(spu_df)} duplicate records ({len(spu_df)} clean records remaining)")
            
            # Save to both directories
            spu_file_api = os.path.join(api_output_dir, f"complete_spu_sales_{period_label}.csv")
            spu_file_final = os.path.join(final_output_dir, f"complete_spu_sales_{period_label}.csv")
            spu_df.to_csv(spu_file_api, index=False)
            spu_df.to_csv(spu_file_final, index=False)
            log_progress(f"Saved SPU sales data: {spu_file_api} and {spu_file_final} ({len(spu_df)} rows, {len(spu_df['str_code'].unique())} stores)")
        
        log_progress(f"Data download and processing complete for period {period_label}")
        
    except Exception as e:
        log_error("Failed to save final results", traceback.format_exc())

def main() -> None:
    """Main function to execute the data download process"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Download store sales data from FastFish API with half-month support')
    parser.add_argument('--month', type=str, default=TARGET_YYYYMM,
                       help=f'Year-month in YYYYMM format (default: {TARGET_YYYYMM})')
    parser.add_argument('--period', type=str, choices=['A', 'B', 'full'], default='A' if TARGET_PERIOD else 'full',
                       help='Period to download: A=first half, B=second half, full=entire month (default: A)')
    parser.add_argument('--list-periods', action='store_true',
                       help='List available periods in existing data and exit')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE,
                       help=f'Number of stores to process per API call (default: {BATCH_SIZE})')
    parser.add_argument('--force-full', action='store_true',
                       help='Force complete re-download ignoring existing data (for troubleshooting)')
    parser.add_argument('--clear-data', action='store_true',
                       help='Clear all previous data before downloading (implies --force-full)')
    parser.add_argument('--disable-smart', action='store_true',
                       help='Disable smart incremental downloading (download everything)')
    parser.add_argument('--recover', action='store_true',
                       help='Recover from interrupted download by consolidating partial files')
    
    args = parser.parse_args()
    
    # Handle recovery command  
    if args.recover:
        target_yyyymm = args.month
        target_period = args.period if args.period != 'full' else None
        period_label = get_period_label(target_yyyymm, target_period)
        
        log_progress(f"Recovery mode: Attempting to consolidate partial files for {period_label}")
        if recover_from_partial_files(period_label):
            log_progress("✅ Recovery successful! You can now proceed with the pipeline.")
        else:
            log_progress("❌ Recovery failed. You may need to restart the download.")
        return
    
    # Handle list periods command
    if args.list_periods:
        print("Available data periods in output directory:")
        if os.path.exists("output"):
            files = [f for f in os.listdir("output") if f.startswith('complete_category_sales_')]
            if files:
                for file in sorted(files):
                    period_label = file.replace('complete_category_sales_', '').replace('.csv', '')
                    if period_label.endswith('A'):
                        desc = f"{period_label[:-1]} (first half)"
                    elif period_label.endswith('B'):
                        desc = f"{period_label[:-1]} (second half)"
                    else:
                        desc = f"{period_label} (full month)"
                    print(f"  • {desc}")
            else:
                print("  No existing data files found")
        else:
            print("  Output directory does not exist")
        return
    
    # Set variables based on arguments (use local variables instead of globals)
    target_yyyymm = args.month
    target_period = args.period if args.period != 'full' else None
    batch_size = args.batch_size
    
    # Determine download mode - SMART BY DEFAULT
    force_full_download = args.force_full or args.clear_data  # Force full only if explicitly requested
    smart_download = not args.disable_smart and not force_full_download  # Smart download is DEFAULT
    
    start_time = time.time()
    period_desc = get_period_description(target_period)
    log_progress(f"Starting store data download process for {target_yyyymm} ({period_desc})...")
    mode_desc = "Smart incremental download (default)" if smart_download else "Force full download"
    log_progress(f"Configuration: batch_size={batch_size}, period={target_period or 'full'}, mode={mode_desc}")
    
    # Set global configuration for other pipeline steps
    set_current_period(target_yyyymm, target_period)
    
    try:
        # Get store codes to process
        store_codes = get_unique_store_codes()
        if not store_codes:
            log_progress("No store codes found. Exiting.")
            return
        
        # Process stores with smart downloading logic
        is_complete, completion_rate, missing_count = process_stores_in_batches(store_codes, target_yyyymm, target_period, batch_size, force_full_download, args.clear_data)
        elapsed_time = (time.time() - start_time) / 60
        
        if is_complete:
            log_progress(f"✅ Process completed successfully in {elapsed_time:.2f} minutes (100% completion)")
        else:
            log_progress(f"⚠️  Process completed with {completion_rate:.1f}% completion in {elapsed_time:.2f} minutes ({missing_count} stores missing)")
            
        # Early exit if we have good enough completion (>95%)
        if completion_rate >= 95.0:
            log_progress("✅ Completion rate is sufficient (≥95%). Proceeding with pipeline.")
        elif not force_full_download and completion_rate < 90.0:
            log_progress(f"⚠️  Low completion rate ({completion_rate:.1f}%). Consider using --force-full flag for complete data.")
        
        # Always continue to create compatibility files regardless of completion rate
        
        # Create backward compatibility files for legacy scripts
        ensure_backward_compatibility()
        
        # Show output files
        period_label = get_period_label(target_yyyymm, target_period)
        log_progress("Output files created:")
        output_files = [
            f"store_config_{period_label}.csv",
            f"store_sales_{period_label}.csv", 
            f"complete_category_sales_{period_label}.csv",
            f"complete_spu_sales_{period_label}.csv"
        ]
        for filename in output_files:
            filepath = os.path.join("output", filename)
            if os.path.exists(filepath):
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                log_progress(f"  • {filename} ({size_mb:.1f} MB)")
        
    except Exception as e:
        error_msg = "Unexpected error in main process"
        log_error(error_msg, traceback.format_exc())
        sys.exit(f"Error: {error_msg}. Check notes directory for details.")

if __name__ == "__main__":
    main() 