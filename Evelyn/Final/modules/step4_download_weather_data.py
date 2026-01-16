#!/usr/bin/env python3
"""
Step 4: Download Weather Data for Store Locations

This step downloads historical weather data for each store location using
the coordinates extracted in step2_extract_coordinates.py.

IMPORTANT: Weather data is time-dependent and filenames include time periods
to avoid confusion between different date ranges.

Time Period Management:
- Weather data files are named: weather_data_{store_code}_{lon}_{lat}_{time_period}.csv
- Time periods are labeled as: YYYYMMDD_to_YYYYMMDD (e.g., 20250501_to_20250531)
- Altitude data is time-independent and shared across all time periods

Configuration:
- Edit WEATHER_START_DATE and WEATHER_END_DATE constants to change time period
- Or use command-line arguments: --start-date YYYY-MM-DD --end-date YYYY-MM-DD

Usage Examples:
- python step4_download_weather_data.py                    # Use configured dates
- python step4_download_weather_data.py --start-date 2025-03-01 --end-date 2025-03-31
- python step4_download_weather_data.py --list-periods     # Show existing data
- python step4_download_weather_data.py --info 20250301_to_20250331  # Show period info

Features:
- Automatic detection of existing data for specific time periods
- Altitude data caching (downloaded once, reused for all time periods)
- Progress monitoring with tqdm
- Comprehensive logging and error handling
- Rate limiting and retry logic for API calls

Author: Data Pipeline
Date: 2025-06-10
"""

import requests
import pandas as pd
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Set
import os
import glob
import random
import logging
from tqdm import tqdm
import argparse

# Configuration
STORE_COORDINATES_FILE = "data/store_coordinates_extended.csv"
OUTPUT_DIR = "output/weather_data"
ALTITUDE_OUTPUT = "output/store_altitudes.csv"

# Weather data time period configuration
WEATHER_START_DATE = "2025-06-16"
WEATHER_END_DATE = "2025-06-30"
WEATHER_PERIOD_LABEL = f"{WEATHER_START_DATE.replace('-', '')}_to_{WEATHER_END_DATE.replace('-', '')}"  # e.g., "20250501_to_20250531"

# Rate limiting constants
MIN_DELAY = 0.5
MAX_DELAY = 1.5
RATE_LIMIT_BACKOFF_MIN = 5
RATE_LIMIT_BACKOFF_MAX = 20
MAX_RETRIES = 3

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("output", exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output/weather_download.log'),
        logging.StreamHandler()
    ]
)

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    logging.info(message)

def get_random_delay() -> float:
    """Get a random delay between MIN_DELAY and MAX_DELAY seconds."""
    return random.uniform(MIN_DELAY, MAX_DELAY)

def get_rate_limit_backoff(attempt: int) -> float:
    """Get exponential backoff time when rate limited."""
    base_delay = min(RATE_LIMIT_BACKOFF_MAX, 
                    RATE_LIMIT_BACKOFF_MIN * (1.5 ** attempt))
    return random.uniform(base_delay, base_delay * 1.2)

def get_downloaded_stores(time_period: Optional[str] = None) -> Set[str]:
    """
    Get list of stores that have already been downloaded for a specific time period.
    
    Args:
        time_period (Optional[str]): Specific time period to check for, if None uses current period
    
    Returns:
        Set[str]: Set of store codes that already have weather data files for the time period
    """
    if time_period is None:
        time_period = WEATHER_PERIOD_LABEL
    
    # Updated pattern to include time period
    pattern = os.path.join(OUTPUT_DIR, f'weather_data_*_{time_period}.csv')
    files = glob.glob(pattern)
    
    downloaded_stores = set()
    for file in files:
        filename = os.path.basename(file)
        # Extract store code from filename format: weather_data_{store_code}_{longitude}_{latitude}_{time_period}.csv
        parts = filename.replace('weather_data_', '').replace(f'_{time_period}.csv', '').split('_')
        if len(parts) >= 3:  # Should have at least store_code, longitude, latitude
            store_code = parts[0]
            downloaded_stores.add(store_code)
    
    return downloaded_stores

def get_elevation(latitude: float, longitude: float) -> float:
    """
    Get elevation for coordinates using Open-Meteo elevation API.
    
    Args:
        latitude (float): Latitude coordinate in decimal degrees
        longitude (float): Longitude coordinate in decimal degrees
        
    Returns:
        float: Elevation in meters above sea level, returns 0.0 if API call fails
    """
    try:
        print(f"[DEBUG] Fetching elevation for coordinates: lat={latitude:.6f}, lon={longitude:.6f}")
        
        params = {
            'latitude': latitude,
            'longitude': longitude
        }
        response = requests.get('https://api.open-meteo.com/v1/elevation', params=params)
        response.raise_for_status()
        data = response.json()
        
        print(f"[DEBUG] Elevation API response received for lat={latitude:.6f}, lon={longitude:.6f}")
        
        if 'elevation' in data and data['elevation']:
            elevation = data['elevation'][0]
            print(f"[DEBUG] Retrieved elevation: {elevation}m for lat={latitude:.6f}, lon={longitude:.6f}")
            return elevation
    except Exception as e:
        print(f"[DEBUG] Could not get elevation for {latitude}, {longitude}: {str(e)}")
        logging.warning(f"Could not get elevation for {latitude}, {longitude}: {str(e)}")
    
    print(f"[DEBUG] Returning default elevation 0.0m for lat={latitude:.6f}, lon={longitude:.6f}")
    return 0.0

def download_weather_for_store(store_code: str, latitude: float, longitude: float) -> Optional[pd.DataFrame]:
    """
    Download weather data for a single store location.
    
    Args:
        store_code (str): Unique identifier for the store
        latitude (float): Latitude coordinate in decimal degrees
        longitude (float): Longitude coordinate in decimal degrees
        
    Returns:
        pd.DataFrame: DataFrame with hourly weather data, or None if download fails
    """
    log_progress(f"Processing store {store_code} (lat: {latitude:.4f}, lon: {longitude:.4f}) for period {WEATHER_PERIOD_LABEL}")
    
    print(f"[DEBUG] Starting weather data download for store {store_code} for time period {WEATHER_PERIOD_LABEL}")
    
    # Create output filename with time period
    output_file = f"weather_data_{store_code}_{longitude:.6f}_{latitude:.6f}_{WEATHER_PERIOD_LABEL}.csv"
    output_path = os.path.join(OUTPUT_DIR, output_file)
    
    # Check if file already exists
    if os.path.exists(output_path):
        print(f"[DEBUG] Weather data file already exists for {store_code} at {output_path}")
        log_progress(f"Weather data already exists for {store_code} for period {WEATHER_PERIOD_LABEL}")
        return pd.read_csv(output_path)
    
    # API request parameters with configurable dates
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'hourly': 'temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation,rain,snowfall,cloud_cover,weather_code,pressure_msl,direct_radiation,diffuse_radiation,direct_normal_irradiance,terrestrial_radiation,shortwave_radiation,et0_fao_evapotranspiration',
        'timezone': 'Asia/Shanghai',
        'start_date': WEATHER_START_DATE,
        'end_date': WEATHER_END_DATE,
        'models': 'best_match'
    }
    
    consecutive_rate_limits = 0
    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                delay = get_random_delay() * (1.5 ** attempt)
                log_progress(f"Retry attempt {attempt + 1}, waiting {delay:.1f} seconds...")
                time.sleep(delay)
            
            log_progress(f"Requesting weather data for {store_code} from Open-Meteo API...")
            response = requests.get('https://archive-api.open-meteo.com/v1/archive', params=params)
            
            if response.status_code == 429:
                consecutive_rate_limits += 1
                backoff_time = get_rate_limit_backoff(consecutive_rate_limits)
                log_progress(f"Rate limit hit, backing off for {backoff_time:.1f} seconds...")
                time.sleep(backoff_time)
                continue
            
            consecutive_rate_limits = 0
            response.raise_for_status()
            
            data = response.json()
            if 'hourly' not in data:
                raise ValueError("No hourly data in response")
                
            df = pd.DataFrame(data['hourly'])
            
            # Check for required columns
            required_columns = [
                'temperature_2m', 'relative_humidity_2m', 'wind_speed_10m', 'wind_direction_10m',
                'precipitation', 'rain', 'snowfall', 'cloud_cover', 'weather_code', 'pressure_msl',
                'direct_radiation', 'diffuse_radiation', 'direct_normal_irradiance', 'terrestrial_radiation',
                'shortwave_radiation', 'et0_fao_evapotranspiration'
            ]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
            
            # Add store information
            df['store_code'] = store_code
            df['latitude'] = latitude
            df['longitude'] = longitude
            
            # Save to file
            df.to_csv(output_path, index=False)
            log_progress(f"Saved weather data for {store_code} to {output_path}")
            
            delay = get_random_delay()
            time.sleep(delay)
            
            return df
            
        except requests.exceptions.RequestException as e:
            log_progress(f"API request failed for {store_code}: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                with open(os.path.join(OUTPUT_DIR, 'download_failed.csv'), 'a') as f:
                    f.write(f"{store_code},{latitude},{longitude},{str(e)}\n")
                return None
            continue
        except Exception as e:
            log_progress(f"Error processing {store_code}: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                with open(os.path.join(OUTPUT_DIR, 'download_failed.csv'), 'a') as f:
                    f.write(f"{store_code},{latitude},{longitude},{str(e)}\n")
                return None
            continue
    
    return None

def collect_altitudes(coords_df: pd.DataFrame) -> pd.DataFrame:
    """
    Collect altitude data for all store locations.
    
    Args:
        coords_df (pd.DataFrame): DataFrame with store coordinates
        
    Returns:
        pd.DataFrame: DataFrame with store codes and altitude data
    """
    # Check if altitude data already exists
    if os.path.exists(ALTITUDE_OUTPUT):
        log_progress(f"Altitude data already exists at {ALTITUDE_OUTPUT}, loading from file...")
        try:
            existing_altitude_df = pd.read_csv(ALTITUDE_OUTPUT)
            
            # Check if we have altitude data for all stores
            existing_stores = set(existing_altitude_df['store_code'].astype(str))
            required_stores = set(coords_df['str_code'].astype(str))
            missing_stores = required_stores - existing_stores
            
            if len(missing_stores) == 0:
                log_progress(f"All {len(existing_stores)} stores already have altitude data")
                return existing_altitude_df
            else:
                log_progress(f"Found altitude data for {len(existing_stores)} stores, need to collect for {len(missing_stores)} additional stores")
                # Filter to only missing stores for collection
                missing_coords = coords_df[coords_df['str_code'].astype(str).isin(missing_stores)]
        except Exception as e:
            log_progress(f"Error reading existing altitude data: {str(e)}, collecting all altitudes...")
            existing_altitude_df = pd.DataFrame()
            missing_coords = coords_df
    else:
        log_progress("No existing altitude data found, collecting altitude data for all store locations...")
        existing_altitude_df = pd.DataFrame()
        missing_coords = coords_df
    
    # Get unique coordinates to minimize API calls
    unique_coords = missing_coords[['latitude', 'longitude']].drop_duplicates()
    
    log_progress(f"Collecting altitude data for {len(unique_coords)} unique coordinate locations...")
    
    altitudes = []
    for i, (_, row) in enumerate(tqdm(unique_coords.iterrows(), total=len(unique_coords), desc="Collecting altitude data"), 1):
        if i % 50 == 0:  # Progress update every 50 calls
            log_progress(f"Collected altitude data for {i}/{len(unique_coords)} locations...")
            
        elevation = get_elevation(row['latitude'], row['longitude'])
        altitudes.append({
            'latitude': row['latitude'],
            'longitude': row['longitude'], 
            'altitude_meters': elevation
        })
        time.sleep(0.1)  # Small delay to be respectful to the API
    
    if altitudes:
        new_altitude_df = pd.DataFrame(altitudes)
        
        # Merge new altitude data with store codes
        new_stores_with_altitude = missing_coords.merge(
            new_altitude_df,
            on=['latitude', 'longitude'],
            how='left'
        )
        
        new_altitude_lookup = new_stores_with_altitude[['str_code', 'altitude_meters']].copy()
        new_altitude_lookup.columns = ['store_code', 'altitude_meters']
        
        # Combine with existing data if any
        if not existing_altitude_df.empty:
            combined_altitude_df = pd.concat([existing_altitude_df, new_altitude_lookup], ignore_index=True)
        else:
            combined_altitude_df = new_altitude_lookup
    else:
        combined_altitude_df = existing_altitude_df
    
    # Save the complete altitude data
    combined_altitude_df.to_csv(ALTITUDE_OUTPUT, index=False)
    log_progress(f"Saved altitude data for {len(combined_altitude_df)} stores to {ALTITUDE_OUTPUT}")
    
    return combined_altitude_df

def check_data_availability(coords_df: pd.DataFrame, time_period: Optional[str] = None) -> Dict[str, any]:
    """
    Check which stores have weather data and altitude data available for a specific time period.
    
    Args:
        coords_df (pd.DataFrame): DataFrame with store coordinates
        time_period (Optional[str]): Specific time period to check for, if None uses current period
        
    Returns:
        Dict[str, any]: Dictionary with availability status for weather and altitude data
    """
    if time_period is None:
        time_period = WEATHER_PERIOD_LABEL
    
    # Check weather data availability for specific time period
    downloaded_stores = get_downloaded_stores(time_period)
    coords_df['str_code'] = coords_df['str_code'].astype(str)
    all_stores = set(coords_df['str_code'])
    
    weather_available = downloaded_stores & all_stores  # Intersection
    weather_missing = all_stores - downloaded_stores
    
    # Check altitude data availability (altitude doesn't depend on time period)
    altitude_available = set()
    altitude_missing = all_stores.copy()
    
    if os.path.exists(ALTITUDE_OUTPUT):
        try:
            altitude_df = pd.read_csv(ALTITUDE_OUTPUT)
            altitude_available = set(altitude_df['store_code'].astype(str)) & all_stores
            altitude_missing = all_stores - altitude_available
        except Exception as e:
            log_progress(f"Warning: Could not read altitude data: {str(e)}")
    
    return {
        'total_stores': len(all_stores),
        'time_period': time_period,
        'weather_available': weather_available,
        'weather_missing': weather_missing, 
        'altitude_available': altitude_available,
        'altitude_missing': altitude_missing
    }

def list_available_time_periods() -> Dict[str, int]:
    """
    List all available time periods in the weather data directory.
    
    Returns:
        Dict[str, int]: Dictionary mapping time period labels to number of stores with data
    """
    if not os.path.exists(OUTPUT_DIR):
        return {}
    
    # Pattern to match all weather data files
    pattern = os.path.join(OUTPUT_DIR, 'weather_data_*.csv')
    files = glob.glob(pattern)
    
    time_periods = {}
    for file in files:
        filename = os.path.basename(file)
        # Extract time period from filename
        if '_to_' in filename:
            # Find the time period part (should be at the end before .csv)
            parts = filename.replace('weather_data_', '').replace('.csv', '').split('_')
            if len(parts) >= 5:  # store_code, lon, lat, date1, to, date2
                time_period = '_'.join(parts[-3:])  # Get last 3 parts: YYYYMMDD_to_YYYYMMDD
                if time_period not in time_periods:
                    time_periods[time_period] = 0
                time_periods[time_period] += 1
    
    return time_periods

def get_time_period_info(time_period: str) -> Dict[str, any]:
    """
    Get detailed information about a specific time period.
    
    Args:
        time_period (str): Time period label (e.g., "20250501_to_20250531")
        
    Returns:
        Dict[str, any]: Information about the time period including date range and store count
    """
    try:
        # Parse the time period label
        parts = time_period.split('_to_')
        if len(parts) == 2:
            start_date_str = parts[0]
            end_date_str = parts[1]
            
            # Convert to readable format
            start_date = f"{start_date_str[:4]}-{start_date_str[4:6]}-{start_date_str[6:8]}"
            end_date = f"{end_date_str[:4]}-{end_date_str[4:6]}-{end_date_str[6:8]}"
            
            # Count stores for this period
            downloaded_stores = get_downloaded_stores(time_period)
            
            return {
                'time_period_label': time_period,
                'start_date': start_date,
                'end_date': end_date,
                'store_count': len(downloaded_stores),
                'stores': downloaded_stores
            }
    except Exception as e:
        log_progress(f"Error parsing time period {time_period}: {str(e)}")
    
    return {
        'time_period_label': time_period,
        'start_date': 'Unknown',
        'end_date': 'Unknown', 
        'store_count': 0,
        'stores': set()
    }

def main() -> None:
    """Main function to download weather data"""
    start_time = datetime.now()
    log_progress("Starting Weather Data Download...")
    log_progress(f"Target time period: {WEATHER_START_DATE} to {WEATHER_END_DATE} (label: {WEATHER_PERIOD_LABEL})")
    
    # Show existing time periods for context
    existing_periods = list_available_time_periods()
    if existing_periods:
        log_progress("Existing weather data time periods:")
        for period, count in existing_periods.items():
            period_info = get_time_period_info(period)
            log_progress(f"  • {period_info['start_date']} to {period_info['end_date']}: {count} stores")
    else:
        log_progress("No existing weather data found")
    
    try:
        # Load store coordinates from existing step2 output
        log_progress("Loading store coordinates...")
        coords_df = pd.read_csv(STORE_COORDINATES_FILE)
        
        log_progress(f"Found {len(coords_df)} stores with coordinates")
        
        # Check data availability before processing
        availability = check_data_availability(coords_df)
        
        log_progress(f"Data Availability Summary for {availability['time_period']}:")
        log_progress(f"  • Total stores: {availability['total_stores']}")
        log_progress(f"  • Weather data available: {len(availability['weather_available'])}")
        log_progress(f"  • Weather data missing: {len(availability['weather_missing'])}")
        log_progress(f"  • Altitude data available: {len(availability['altitude_available'])}")
        log_progress(f"  • Altitude data missing: {len(availability['altitude_missing'])}")
        
        # Collect altitude data (will skip if already available)
        altitude_df = collect_altitudes(coords_df)
        
        # Filter to stores that need downloading
        coords_df['str_code'] = coords_df['str_code'].astype(str)
        to_download = coords_df[coords_df['str_code'].isin(availability['weather_missing'])]
        
        if len(to_download) == 0:
            log_progress(f"All stores already have weather data for period {WEATHER_PERIOD_LABEL}")
            log_progress("Weather data download completed - no additional downloads needed")
            return
        
        log_progress(f"Need to download weather data for {len(to_download)} stores for period {WEATHER_PERIOD_LABEL}")
        
        # Sample of stores to download (for transparency)
        if len(to_download) <= 10:
            sample_stores = to_download['str_code'].tolist()
        else:
            sample_stores = to_download['str_code'].head(5).tolist() + ['...'] + to_download['str_code'].tail(5).tolist()
        log_progress(f"Stores to download: {', '.join(map(str, sample_stores))}")
        
        # Download weather data for each store
        successful_downloads = 0
        failed_downloads = 0
        
        for _, store in tqdm(to_download.iterrows(), total=len(to_download), desc=f"Downloading weather data ({WEATHER_PERIOD_LABEL})"):
            result = download_weather_for_store(
                store['str_code'],
                store['latitude'],
                store['longitude']
            )
            
            if result is not None:
                successful_downloads += 1
            else:
                failed_downloads += 1
            
            total_processed = successful_downloads + failed_downloads
            if total_processed % 10 == 0:
                log_progress(f"Progress: {total_processed}/{len(to_download)} stores processed")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        log_progress(f"Weather data download completed in {duration/60:.1f} minutes")
        log_progress(f"  • Successful downloads: {successful_downloads}")
        log_progress(f"  • Failed downloads: {failed_downloads}")
        
        if successful_downloads + failed_downloads > 0:
            success_rate = (successful_downloads/(successful_downloads+failed_downloads)*100)
            log_progress(f"  • Success rate: {success_rate:.1f}%")
        
        # Final availability check
        log_progress("Final data availability check...")
        final_availability = check_data_availability(coords_df)
        log_progress(f"Final status: {len(final_availability['weather_available'])}/{final_availability['total_stores']} stores have weather data for {final_availability['time_period']}")
        
    except Exception as e:
        log_progress(f"Error in weather data download: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download weather data for store locations')
    parser.add_argument('--start-date', type=str, 
                       help='Start date in YYYY-MM-DD format (default: use configured date)')
    parser.add_argument('--end-date', type=str,
                       help='End date in YYYY-MM-DD format (default: use configured date)')
    parser.add_argument('--list-periods', action='store_true',
                       help='List existing time periods and exit')
    parser.add_argument('--info', type=str,
                       help='Show information about a specific time period')
    
    args = parser.parse_args()
    
    # Handle list periods command
    if args.list_periods:
        print("Available weather data time periods:")
        existing_periods = list_available_time_periods()
        if existing_periods:
            for period, count in existing_periods.items():
                period_info = get_time_period_info(period)
                print(f"  • {period_info['start_date']} to {period_info['end_date']}: {count} stores (label: {period})")
        else:
            print("  No existing weather data found")
        exit(0)
    
    # Handle info command
    if args.info:
        period_info = get_time_period_info(args.info)
        print(f"Time Period Information:")
        print(f"  • Label: {period_info['time_period_label']}")
        print(f"  • Date range: {period_info['start_date']} to {period_info['end_date']}")
        print(f"  • Store count: {period_info['store_count']}")
        if period_info['store_count'] > 0 and period_info['store_count'] <= 20:
            print(f"  • Stores: {', '.join(sorted(period_info['stores']))}")
        elif period_info['store_count'] > 20:
            sample_stores = sorted(list(period_info['stores']))[:10]
            print(f"  • Sample stores: {', '.join(sample_stores)}... (and {period_info['store_count']-10} more)")
        exit(0)
    
    # Override configured dates if provided
    if args.start_date:
        WEATHER_START_DATE = args.start_date
        print(f"Using custom start date: {WEATHER_START_DATE}")
    if args.end_date:
        WEATHER_END_DATE = args.end_date
        print(f"Using custom end date: {WEATHER_END_DATE}")
    
    # Recalculate period label if dates were overridden
    if args.start_date or args.end_date:
        WEATHER_PERIOD_LABEL = f"{WEATHER_START_DATE.replace('-', '')}_to_{WEATHER_END_DATE.replace('-', '')}"
        print(f"Using custom period label: {WEATHER_PERIOD_LABEL}")
    
    main() 