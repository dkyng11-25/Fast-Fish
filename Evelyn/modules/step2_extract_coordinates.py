#!/usr/bin/env python3
"""
Step 2: Extract Store Coordinates and Create SPU Mappings (Multi-Period Enhanced)

This step extracts store coordinates from ALL periods in the last 3 months and creates 
comprehensive mappings for both subcategory-level and SPU-level analysis.

Enhanced to scan multiple periods to ensure we capture all stores that appear
across the seasonal analysis window.

For SPU-level analysis, this step also creates:
- SPU-to-store mappings (across all periods)
- SPU metadata for downstream processing
- Store-level coordinates (from most complete period)

Author: Data Pipeline
Date: 2025-07-20

 HOW TO RUN (CLI + ENV) — Read this before executing
 ----------------------------------------------------
 Overview
 - Multi-period: this step scans a window of half-month periods (defaults to last 3 months plus YoY anchors) to find the most complete coordinates and to build comprehensive SPU mappings.
 - Why multi-period: coordinates may be missing in some halves; scanning a window maximizes realistic store coverage and SPU mapping fidelity for downstream analysis.

 Quick Start (default 3-month window)
   Command:
     PYTHONPATH=. python3 src/step2_extract_coordinates.py

   Controls (ENV):
   - COORDS_MONTHS_BACK=N (default 3) → controls window size
   - WEATHER_MONTHS_BACK is used as fallback if COORDS_MONTHS_BACK not set

 Why period purity matters
 - Coordinates and SPU mappings must be derived from real, period-labeled API files (e.g., `store_sales_YYYYMMP.csv`, `complete_spu_sales_YYYYMMP.csv`).
 - Fabricating or aliasing months/halves creates false coverage and breaks downstream joins. This script forbids placeholders and will error if no real coordinates are found.

 Common failure modes (and what to do)
 - "Required coordinates not found" errors
   • Cause: No target period contains real `long_lat` values.
   • Fix: re-run Step 1 for at least one period in the window where coordinates are present; verify `long_lat` is a comma-separated pair and not blank.
 - SPU mapping created but low coverage
   • Cause: scanning window too small; SPU sales not present in many periods.
   • Fix: increase `COORDS_MONTHS_BACK` to extend the window, or ensure Step 1 SPU files exist across more halves.
 - Dtype mismatch on `str_code`
   • Cause: mixing int and str types across files.
   • Fix: keep `str_code` as string everywhere (this script enforces string typing when combining datasets).

 Manifest and standards notes
 - Outputs: `data/store_coordinates_extended.csv`, `data/spu_store_mapping.csv`, `data/spu_metadata.csv`.
 - Period-specific coordinates may also be saved via `get_output_files()` for downstream steps expecting a period path.
 - Follow output naming standards (rule files, consistent `str_code`, `cluster_id` vs `Cluster` standardization downstream).
"""

import pandas as pd
import os
import sys
import re
from typing import Tuple, List, Dict, Set, Optional
from datetime import datetime, timedelta
from tqdm import tqdm

# Import dual output utility
from output_utils import create_output_with_symlinks

# Import configuration system
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import get_api_data_files, get_current_period, get_period_label
from config import get_output_files

# 과거 N개월을 반월 (A/B) 단위로 쪼개서 가져오기 
# e.g. 202304B, 2 months -> 202304B, 202304A, 202303B, 202303A
def last_n_half_months(yyyymm: str, half: str, n_months: int) -> List[Tuple[str, str]]:
    """
    Helper: last N months in half-month steps ending at (yyyymm, half).
    Returns a chronological list of (yyyymm, half) tuples.
    """
    result: List[Tuple[str, str]] = []
    total_halves = n_months * 2
    y = int(yyyymm[:4])
    m = int(yyyymm[4:6])
    h = half
    for _ in range(total_halves):
        result.append((f"{y:04d}{m:02d}", h))
        if h == 'B':
            h = 'A'
        else:
            h = 'B'
            m -= 1
            if m < 1:
                m = 12
                y -= 1
    result.reverse()
    return result

# 작년 같은 달로부터 앞으로 N개월 (각 달에 대해 A/B 둘 다 포함) > 작년 시즌성 비교용 구간 
# e.g. 202304, 2 months -> 202204A, 202204B, 202205A, 202205B
def next_n_months_last_year(yyyymm: str, n_months: int) -> List[Tuple[str, str]]:
    """
    Helper: next N months from previous year, returning both A and B halves for each month.
    """
    result: List[Tuple[str, str]] = []
    y = int(yyyymm[:4]) - 1
    m = int(yyyymm[4:6])
    for _ in range(n_months):
        result.append((f"{y:04d}{m:02d}", 'A'))
        result.append((f"{y:04d}{m:02d}", 'B'))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return result

# 기준 날짜에 대해서 과거 N개월 + 작년 같은 달로부터 N개월 후 함께 리턴 
# Cluestering feature window 
def get_year_over_year_periods() -> List[Tuple[str, str]]:
    """
    Build dynamic list of (yyyymm, half) tuples based on current base period and window.
    Matches Step 4's dynamic generation: last N months up to base (A/B halves)
    plus next N months from same time last year (both A and B for each month).

    Exposes helpers as attributes for backward compatibility:
      • get_year_over_year_periods.last_n_half_months
      • get_year_over_year_periods.next_n_months_last_year
    """
    # Window size (accept COORDS_MONTHS_BACK for step2, fallback to WEATHER_MONTHS_BACK)
    months_back = int(os.environ.get('COORDS_MONTHS_BACK', os.environ.get('WEATHER_MONTHS_BACK', '3')))

    base_yyyymm, base_period = get_current_period()
    # Normalize: treat None/full as 'B' to include full month end
    base_half = base_period if base_period in ['A', 'B'] else 'B'

    current_periods = last_n_half_months(base_yyyymm, base_half, months_back)
    yoy_periods = next_n_months_last_year(base_yyyymm, months_back)
    return current_periods + yoy_periods

# Attach helpers to function object for code that mistakenly accesses nested helpers as attributes
get_year_over_year_periods.last_n_half_months = last_n_half_months  # type: ignore[attr-defined]
get_year_over_year_periods.next_n_months_last_year = next_n_months_last_year  # type: ignore[attr-defined]

# 모든 파일 스캔 후 존재하는 기간 리스트업 
def get_all_available_periods() -> List[Tuple[str, str]]:
    """
    Discover available periods by scanning both category and store sales files
    in output/ and data/api_data/.
    """
    import glob

    found: Set[Tuple[str, str]] = set()

    patterns = [
        "output/complete_category_sales_*.csv",
        "data/api_data/complete_category_sales_*.csv",
        "output/store_sales_*.csv",
        "data/api_data/store_sales_*.csv",
    ]

    for pattern in patterns:
        for file_path in glob.glob(pattern):
            filename = os.path.basename(file_path)
            # Handle both prefixes
            if filename.startswith("complete_category_sales_"):
                period_part = filename.replace("complete_category_sales_", "").replace(".csv", "")
            elif filename.startswith("store_sales_"):
                period_part = filename.replace("store_sales_", "").replace(".csv", "")
            else:
                continue

            if len(period_part) >= 6:
                yyyymm = period_part[:6]
                half = period_part[6:] if len(period_part) > 6 else "A"
                found.add((yyyymm, half))

    periods = sorted(found, key=lambda x: (x[0], x[1]))
    return periods

def scan_all_periods_for_data() -> Tuple[pd.DataFrame, List[pd.DataFrame], List[pd.DataFrame]]:
    """
    Scan all year-over-year periods to find the most comprehensive dataset.
    
    Returns:
        Tuple of (best_coordinates_df, all_spu_dataframes, all_category_dataframes)
    """
    log_progress("🔍 Scanning all year-over-year periods for comprehensive store data...")
    
    # First try our specific year-over-year periods
    # 이론적으로 사용하고 싶은 기간 (기준 기간에 대한 과거 N개월 + 작년 같은 달로부터 N개월 후)
    periods = get_year_over_year_periods()
    log_progress(f"Target periods: {[f'{p[0]}{p[1]}' for p in periods]}")
    
    # Also check what's actually available
    available_periods = get_all_available_periods()
    # 실제로 파일이 존재하는 기간 
    log_progress(f"Available periods: {[f'{p[0]}{p[1]}' for p in available_periods]}")
    
    # Use available periods that match our targets
    target_period_set = set(f'{p[0]}{p[1]}' for p in periods)
    available_period_set = set(f'{p[0]}{p[1]}' for p in available_periods)

    # 이론적으로 사용하고 싶은 기간과 실제로 파일이 존재하는 기간의 교집합
    matching_periods = target_period_set.intersection(available_period_set)
    periods_to_scan = [p for p in available_periods if f'{p[0]}{p[1]}' in matching_periods]

    log_progress(f"Scanning {len(periods_to_scan)} matching periods: {[f'{p[0]}{p[1]}' for p in periods_to_scan]}")

    best_coords_df = None
    best_coords_count = 0
    best_period = None

    all_spu_dfs = []

    # If no matching periods found, try legacy fallback
    if not periods_to_scan:
        log_progress("No matching periods found, trying legacy combined files...")
        legacy_coords_df = _load_legacy_combined_coordinates()
        if legacy_coords_df is not None:
            best_coords_df = legacy_coords_df
            best_coords_count = len(legacy_coords_df)
            best_period = "legacy_combined"
            log_progress(f"✅ Found {best_coords_count} stores in legacy combined coordinates")

        # Also try to load legacy SPU data
        legacy_spu_dfs = _load_legacy_combined_spu_data()
        if legacy_spu_dfs:
            all_spu_dfs.extend(legacy_spu_dfs)
            log_progress(f"✅ Loaded SPU data from {len(legacy_spu_dfs)} legacy files")
    all_category_dfs = []
    
    for yyyymm, period in periods_to_scan:
        period_label = f"{yyyymm}{period}"
        log_progress(f"Scanning period {period_label}...")
        
        # Check for store sales data with coordinates
        potential_sales_paths = [
            f"data/api_data/store_sales_{period_label}.csv",
            f"output/store_sales_{period_label}.csv",
            f"data/api_data/store_sales_data_{period_label}.csv",
        ]
        
        # Check for category data
        potential_category_paths = [
            f"data/api_data/complete_category_sales_{period_label}.csv",
            f"output/complete_category_sales_{period_label}.csv",
        ]
        
        # Check for SPU data  
        potential_spu_paths = [
            f"data/api_data/complete_spu_sales_{period_label}.csv",
            f"output/complete_spu_sales_{period_label}.csv",
        ]
        
        # Try to load store sales data with coordinates
        sales_df = None
        for path in potential_sales_paths:
            if os.path.exists(path):
                try:
                    sales_df = pd.read_csv(path)
                    if 'long_lat' in sales_df.columns:
                        # Count only rows with non-empty, valid coordinate strings
                        coord_series = sales_df['long_lat'].astype(str)
                        valid_mask = coord_series.str.contains(',', na=False) & (coord_series.str.strip() != '')
                        stores_with_coords = sales_df.loc[valid_mask]
                        unique_stores = stores_with_coords.drop_duplicates(subset=['str_code'])
                        store_count = len(unique_stores)
                        log_progress(f"  📍 Found {store_count} stores with valid coordinates in {path}")

                        if store_count > best_coords_count:
                            best_coords_df = unique_stores[['str_code', 'long_lat']].copy()
                            best_coords_count = store_count
                            best_period = period_label
                            log_progress(f"  ⭐ New best period for coordinates: {period_label} ({store_count} stores)")
                        break
                except Exception as e:
                    log_progress(f"  ❌ Error reading {path}: {str(e)}")
        
        # Load category data if available
        category_df = None
        for path in potential_category_paths:
            if os.path.exists(path):
                try:
                    category_df = pd.read_csv(path)
                    log_progress(f"  📊 Found category data: {len(category_df)} records, {category_df['str_code'].nunique()} stores")
                    all_category_dfs.append(category_df)
                    break
                except Exception as e:
                    log_progress(f"  ❌ Error reading {path}: {str(e)}")
        
        # Load SPU data if available
        spu_df = None
        for path in potential_spu_paths:
            if os.path.exists(path):
                try:
                    spu_df = pd.read_csv(path)
                    log_progress(f"  🛍️  Found SPU data: {len(spu_df)} records, {spu_df['str_code'].nunique()} stores")
                    all_spu_dfs.append(spu_df)
                    break
                except Exception as e:
                    log_progress(f"  ❌ Error reading {path}: {str(e)}")
    
    if best_coords_df is not None:
        log_progress(f"✅ Best coordinates found in period {best_period} with {best_coords_count} stores")
    else:
        log_progress("⚠️  No coordinate data found in any period")
    
    log_progress(f"✅ Found {len(all_category_dfs)} periods with category data")
    log_progress(f"✅ Found {len(all_spu_dfs)} periods with SPU data")
    
    return best_coords_df, all_spu_dfs, all_category_dfs

# Get current period configuration (for backwards compatibility)
current_yyyymm, current_period = get_current_period()
api_files = get_api_data_files(current_yyyymm, current_period)

# Configuration - now supports multi-period scanning
CATEGORY_FILE = api_files['category_sales']  # Fallback for single period
SPU_FILE = api_files['spu_sales']  # Fallback for single period
SALES_DATA_FILE = api_files['store_sales']  # Fallback for single period
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

def create_comprehensive_spu_mappings(all_spu_dfs: List[pd.DataFrame]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create comprehensive SPU-to-store mappings and SPU metadata from all periods.
    
    Args:
        all_spu_dfs: List of SPU sales DataFrames from all periods
        
    Returns:
        Tuple containing comprehensive SPU mapping DataFrame and SPU metadata DataFrame
    """
    if not all_spu_dfs:
        log_progress("No SPU data found across any periods")
        return pd.DataFrame(), pd.DataFrame()
    
    log_progress("Creating comprehensive SPU mappings from all periods...")
    
    # Combine all SPU data
    combined_spu_df = pd.concat(all_spu_dfs, ignore_index=True)
    # Normalize key identifiers to string type
    if 'str_code' in combined_spu_df.columns:
        combined_spu_df['str_code'] = combined_spu_df['str_code'].astype(str)
    if 'spu_code' in combined_spu_df.columns:
        combined_spu_df['spu_code'] = combined_spu_df['spu_code'].astype(str)
    total_records = len(combined_spu_df)
    
    print(f"[DEBUG] Processing {total_records:,} SPU records across {len(all_spu_dfs)} periods")
    
    # Create comprehensive SPU-store mapping (unique combinations across all periods)
    spu_mapping = combined_spu_df[['spu_code', 'str_code', 'str_name', 'cate_name', 'sub_cate_name', 'spu_sales_amt']].copy()
    spu_mapping = spu_mapping.drop_duplicates(subset=['spu_code', 'str_code'])  # Unique SPU-store pairs
    
    log_progress(f"Created comprehensive SPU-store mapping with {len(spu_mapping):,} unique SPU-store combinations")
    
    # Create comprehensive SPU metadata (aggregated across all periods)
    spu_metadata = combined_spu_df.groupby(['spu_code', 'cate_name', 'sub_cate_name']).agg({
        'str_code': 'nunique',  # Number of unique stores selling this SPU
        'spu_sales_amt': ['sum', 'mean', 'std', 'count']  # Comprehensive sales statistics
    }).reset_index()
    
    # Flatten column names
    spu_metadata.columns = ['spu_code', 'cate_name', 'sub_cate_name', 'store_count', 'total_sales', 'avg_sales', 'std_sales', 'period_count']
    spu_metadata['std_sales'] = spu_metadata['std_sales'].fillna(0)
    
    log_progress(f"Created comprehensive SPU metadata for {len(spu_metadata):,} unique SPUs")
    
    # Debug: Show SPU distribution by category
    category_counts = spu_metadata.groupby('cate_name')['spu_code'].count().sort_values(ascending=False)
    print(f"[DEBUG] Comprehensive SPU distribution by category:")
    for category, count in category_counts.head(10).items():
        print(f"[DEBUG]   {category}: {count} SPUs")
    
    # Show multi-period statistics
    unique_stores_all_periods = combined_spu_df['str_code'].nunique()
    unique_spus_all_periods = combined_spu_df['spu_code'].nunique()
    
    print(f"[DEBUG] Multi-period statistics:")
    print(f"[DEBUG]   Unique stores across all periods: {unique_stores_all_periods}")
    print(f"[DEBUG]   Unique SPUs across all periods: {unique_spus_all_periods}")
    print(f"[DEBUG]   Average records per period: {total_records / len(all_spu_dfs):.0f}")
    
    return spu_mapping, spu_metadata

def extract_coordinates_from_api_data() -> None:
    """
    Extract store coordinates from ALL API data periods and create comprehensive SPU mappings.
    Enhanced to scan multiple periods for maximum store coverage.
    """
    log_progress("🚀 Extracting coordinates and creating comprehensive mappings from all periods...")
    
    # Scan all periods for the most complete dataset
    best_coords_df, all_spu_dfs, all_category_dfs = scan_all_periods_for_data()
    
    coords_df = None
    
    if best_coords_df is not None and 'long_lat' in best_coords_df.columns:
        log_progress(f"✅ Using coordinates from best period with {len(best_coords_df)} stores")
        
        # Extract longitude and latitude from the "long_lat" column
        coordinates = []
        for _, row in tqdm(best_coords_df.iterrows(), total=len(best_coords_df), desc="Processing coordinates"):
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
        # Ensure DataFrame has expected columns even if empty
        coords_df = pd.DataFrame(coordinates, columns=['str_code', 'longitude', 'latitude'])
        # Ensure string store codes
        coords_df['str_code'] = coords_df['str_code'].astype(str)
        log_progress(f"✅ Extracted coordinates for {len(coords_df)} stores")
        
        # Save coordinates file with DUAL OUTPUT PATTERN using utility
        try:
            cur_yyyymm, cur_period = get_current_period()
            period_label = get_period_label(cur_yyyymm, cur_period) if cur_yyyymm and cur_period else ""
        except Exception:
            period_label = ""
        
        timestamped_file, period_file, generic_file = create_output_with_symlinks(
            coords_df,
            OUTPUT_FILE.replace('.csv', ''),
            period_label
        )
        log_progress(f"💾 Saved coordinates:")
        log_progress(f"   Timestamped: {timestamped_file}")
        log_progress(f"   Period symlink: {period_file}")
        log_progress(f"   Generic symlink: {generic_file}")
        
    elif all_category_dfs:
        raise RuntimeError(
            "Required coordinates not found in API sales data ('long_lat' missing). "
            "Per policy, placeholders are prohibited. Ensure real coordinates are available in at least one target period and rerun."
        )
    else:
        raise RuntimeError(
            "No valid source found to extract store coordinates. "
            "Per policy, placeholders are prohibited. Provide real coordinates in API data and rerun."
        )
    
    # Process comprehensive SPU data if available
    if all_spu_dfs and coords_df is not None:
        process_comprehensive_spu_data(coords_df, all_spu_dfs)

def process_comprehensive_spu_data(coords_df: pd.DataFrame, all_spu_dfs: List[pd.DataFrame]) -> None:
    """
    Process comprehensive SPU-level data from all periods to create mappings and metadata.
    
    Args:
        coords_df: Store coordinates DataFrame
        all_spu_dfs: List of SPU DataFrames from all periods
    """
    log_progress("🛍️  Processing comprehensive SPU-level data from all periods...")
    
    try:
        # Create comprehensive SPU mappings and metadata
        spu_mapping, spu_metadata = create_comprehensive_spu_mappings(all_spu_dfs)
        if spu_mapping.empty:
            log_progress("⚠️  No SPU data to process")
            return
        
        # Save comprehensive SPU-store mapping with DUAL OUTPUT PATTERN using utility
        try:
            cur_yyyymm, cur_period = get_current_period()
            period_label = get_period_label(cur_yyyymm, cur_period) if cur_yyyymm and cur_period else ""
        except Exception:
            period_label = ""
        
        timestamped_mapping, period_mapping, generic_mapping = create_output_with_symlinks(
            spu_mapping,
            SPU_MAPPING_FILE.replace('.csv', ''),
            period_label
        )
        log_progress(f"💾 Saved SPU-store mapping: {timestamped_mapping}")
        
        # Save comprehensive SPU metadata file with DUAL OUTPUT PATTERN using utility
        try:
            cur_yyyymm, cur_period = get_current_period()
            period_label = get_period_label(cur_yyyymm, cur_period) if cur_yyyymm and cur_period else ""
        except Exception:
            period_label = ""
        
        timestamped_metadata, period_metadata, generic_metadata = create_output_with_symlinks(
            spu_metadata,
            SPU_METADATA_FILE.replace('.csv', ''),
            period_label
        )
        log_progress(f"💾 Saved SPU metadata: {timestamped_metadata}")
        
        # Validate that all stores in comprehensive SPU data have coordinates
        combined_spu_df = pd.concat(all_spu_dfs, ignore_index=True)
        if 'str_code' in combined_spu_df.columns:
            combined_spu_df['str_code'] = combined_spu_df['str_code'].astype(str)
        spu_stores = set(combined_spu_df['str_code'].unique())
        coord_stores = set(coords_df['str_code'].unique())
        
        missing_coords = spu_stores - coord_stores
        extra_coords = coord_stores - spu_stores
        
        if missing_coords:
            log_progress(f"⚠️  {len(missing_coords)} stores in SPU data don't have coordinates")
        if extra_coords:
            log_progress(f"ℹ️  {len(extra_coords)} stores have coordinates but no SPU data")
        
        overlap = len(spu_stores & coord_stores)
        log_progress(f"✅ {overlap} stores have both coordinates and SPU data")
        
        # Comprehensive summary statistics
        log_progress("\n🎯 === COMPREHENSIVE MULTI-PERIOD SPU DATA SUMMARY ===")
        log_progress(f"Total SPU records across all periods: {len(combined_spu_df):,}")
        log_progress(f"Unique SPUs across all periods: {combined_spu_df['spu_code'].nunique():,}")
        log_progress(f"Unique stores across all periods: {combined_spu_df['str_code'].nunique():,}")
        log_progress(f"Unique categories: {combined_spu_df['cate_name'].nunique()}")
        log_progress(f"Unique subcategories: {combined_spu_df['sub_cate_name'].nunique()}")
        log_progress(f"Periods analyzed: {len(all_spu_dfs)}")
        log_progress(f"Stores with coordinates: {len(coords_df)}")
        log_progress(f"Data coverage: {overlap}/{len(spu_stores)} stores ({100*overlap/len(spu_stores):.1f}%)")
        
    except Exception as e:
        log_progress(f"❌ Error processing comprehensive SPU data: {str(e)}")
        log_progress("SPU-level processing failed - only store coordinates available")

def main() -> None:
    """Main function to extract coordinates and create comprehensive SPU mappings."""
    start_time = datetime.now()
    log_progress("🚀 Starting Step 2: Enhanced Year-over-Year Coordinate Extraction & SPU Mapping...")
    
    # Log current configuration
    current_yyyymm, current_period = get_current_period()
    period_label = get_period_label(current_yyyymm, current_period)
    log_progress(f"Base period configuration: {period_label}")
    log_progress(f"Multi-period mode: Scanning year-over-year periods for comprehensive coverage")
    
    try:
        extract_coordinates_from_api_data()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        log_progress(f"✅ Step 2 completed successfully in {execution_time:.1f} seconds")
        
        # Check output files
        output_files = [OUTPUT_FILE, SPU_MAPPING_FILE, SPU_METADATA_FILE]
        log_progress("\n📁 === OUTPUT FILES ===")
        for file_path in output_files:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                log_progress(f"✅ {file_path} ({file_size:.1f} MB)")
            else:
                log_progress(f"❌ {file_path} (not created)")
        
        log_progress("\n🎯 Next step: Run python src/step3_prepare_matrix.py for distance matrix preparation")
        
    except Exception as e:
        log_progress(f"❌ Error in Step 2: {str(e)}")
        raise


def _load_legacy_combined_coordinates() -> Optional[pd.DataFrame]:
    """
    Load coordinates from legacy combined files as fallback.

    Returns:
        DataFrame with store coordinates from legacy files, or None if not found
    """
    import glob

    # Try legacy combined store sales file (main fallback)
    legacy_patterns = [
        "data/api_data/store_sales_data.csv",
        "output/store_sales_data.csv",
    ]

    for pattern in legacy_patterns:
        matching_files = glob.glob(pattern)
        for file_path in matching_files:
            try:
                log_progress(f"Trying legacy coordinates from: {file_path}")
                df = pd.read_csv(file_path)

                if 'long_lat' in df.columns and 'str_code' in df.columns:
                    # Extract unique store codes with coordinates
                    coords_df = df[['str_code', 'long_lat']].drop_duplicates()
                    coords_df = coords_df[coords_df['long_lat'].notna() & (coords_df['long_lat'] != '')]

                    if not coords_df.empty:
                        log_progress(f"✅ Found {len(coords_df)} stores with coordinates in {file_path}")
                        return coords_df
                else:
                    log_progress(f"⚠️  File {file_path} missing required columns (str_code, long_lat)")

            except Exception as e:
                log_progress(f"❌ Error loading legacy coordinates from {file_path}: {e}")

    log_progress("No valid legacy coordinate data found")
    return None


def _load_legacy_combined_spu_data() -> List[pd.DataFrame]:
    """
    Load SPU data from legacy combined files as fallback.

    Returns:
        List of SPU DataFrames from legacy files
    """
    import glob

    legacy_patterns = [
        "data/api_data/complete_spu_sales_*.csv",
        "output/complete_spu_sales_*.csv",
    ]

    spu_dataframes = []

    for pattern in legacy_patterns:
        matching_files = glob.glob(pattern)
        for file_path in matching_files:
            try:
                log_progress(f"Trying legacy SPU data from: {file_path}")
                df = pd.read_csv(file_path)

                # Ensure required columns exist
                required_columns = ['str_code', 'spu_code', 'cate_name', 'sub_cate_name']
                missing_columns = [col for col in required_columns if col not in df.columns]

                if missing_columns:
                    log_progress(f"⚠️  Legacy SPU file {file_path} missing columns: {missing_columns}")
                    continue

                spu_dataframes.append(df)
                log_progress(f"✅ Loaded {len(df)} SPU records from {file_path}")

            except Exception as e:
                log_progress(f"❌ Error loading legacy SPU data from {file_path}: {e}")

    return spu_dataframes


if __name__ == "__main__":
    main() 