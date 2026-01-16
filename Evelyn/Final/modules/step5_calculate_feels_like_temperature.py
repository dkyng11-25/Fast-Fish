#!/usr/bin/env python3
"""
Step 5: Calculate Feels-Like Temperature for Stores

This step combines all weather data, calculates feels-like temperature for each store,
and creates temperature bands for clustering constraints.

Author: Data Pipeline
Date: 2025-06-09
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from typing import Dict, List
from tqdm import tqdm
import logging

# Configuration
WEATHER_DATA_DIR = "output/weather_data"
ALTITUDE_FILE = "output/store_altitudes.csv"
OUTPUT_FILE = "output/stores_with_feels_like_temperature.csv"
TEMPERATURE_BANDS_FILE = "output/temperature_bands.csv"

# Physical constants for calculations
Rd, cp, rho0 = 287.05, 1005.0, 1.225   # J/(kg·K), J/(kg·K), kg/m³

# Temperature band configuration (5-degree Celsius bands)
TEMPERATURE_BAND_SIZE = 5  # degrees Celsius

# Create output directory
os.makedirs("output", exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output/feels_like_calculation.log'),
        logging.StreamHandler()
    ]
)

def log_progress(message: str) -> None:
    """Log progress with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    logging.info(message)

def _rho_air(T_c: np.ndarray, p_hpa: np.ndarray) -> np.ndarray:
    """Calculate air density (kg/m³) from temperature (°C) and pressure (hPa)."""
    return (p_hpa*100) / (Rd*(T_c + 273.15))

def wind_chill(T_c: np.ndarray, V_kmh: np.ndarray, rho: np.ndarray) -> np.ndarray:
    """Calculate wind-chill temperature, corrected for air density."""
    V_eff = V_kmh * np.sqrt(rho / rho0)
    V16 = np.power(V_eff, 0.16)
    return 13.12 + 0.6215*T_c - 11.37*V16 + 0.3965*T_c*V16

def heat_index(T_c: np.ndarray, RH: np.ndarray) -> np.ndarray:
    """Calculate heat index from temperature and relative humidity."""
    T_f = T_c*9/5 + 32
    HI_f = (-42.379 + 2.04901523*T_f + 10.14333127*RH
            - 0.22475541*T_f*RH - 0.00683783*T_f**2
            - 0.05481717*RH**2 + 0.00122874*T_f**2*RH
            + 0.00085282*T_f*RH**2 - 0.00000199*T_f**2*RH**2)
    return (HI_f - 32) * 5/9

def apparent_temp_steadman(T_c: np.ndarray, RH: np.ndarray, v_ms: np.ndarray, 
                          p_hpa: np.ndarray, rad_sw: np.ndarray, rad_dr: np.ndarray, 
                          rad_df: np.ndarray, rad_lw: np.ndarray, rho: np.ndarray) -> np.ndarray:
    """
    Calculate Steadman's apparent temperature for moderate conditions.
    
    Args:
        T_c: Temperature in Celsius
        RH: Relative humidity in %
        v_ms: Wind speed in m/s
        p_hpa: Pressure in hPa
        rad_sw, rad_dr, rad_df, rad_lw: Radiation components in W/m²
        rho: Air density in kg/m³
    """
    e = (RH/100) * 6.112 * np.exp(17.67*T_c / (T_c + 243.5))
    v_e = v_ms * np.sqrt(rho / rho0)
    R_n = rad_sw + rad_dr + rad_df + rad_lw
    return T_c + 0.348*e - 0.70*v_e + 0.70*R_n/(rho*cp) - 4.25

def validate_and_clean_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Apply validation and cleaning to weather data.
    
    Args:
        data: Weather data to validate and clean
        
    Returns:
        pd.DataFrame: Cleaned data with values capped at reasonable limits
    """
    # Create a copy to avoid modifying the original data
    data = data.copy()
    
    # Define reasonable limits for weather parameters
    limits = {
        'temperature_2m': (-50, 50),  # °C
        'relative_humidity_2m': (0, 100),  # %
        'wind_speed_10m': (0, 25),  # m/s (cap at 25 m/s, about 90 km/h)
        'pressure_msl': (900, 1100),  # hPa
        'shortwave_radiation': (0, 1500),  # W/m²
        'direct_radiation': (0, 1200),  # W/m²
        'diffuse_radiation': (0, 800),  # W/m²
        'terrestrial_radiation': (-100, 500),  # W/m²
    }
    
    # Apply limits and log suspicious values
    log_progress("Data validation report:")
    for col, (min_val, max_val) in limits.items():
        if col in data.columns:
            # Count values outside limits
            outliers = data[~data[col].between(min_val, max_val)]
            if len(outliers) > 0:
                log_progress(f"{col} outliers ({len(outliers)} values): Min: {data[col].min():.2f}, Max: {data[col].max():.2f}")
            
            # Cap values at limits
            data[col] = data[col].clip(min_val, max_val)
    
    return data

def load_weather_data() -> pd.DataFrame:
    """Load and combine all weather data files."""
    log_progress("Loading weather data files...")
    
    pattern = os.path.join(WEATHER_DATA_DIR, 'weather_data_*.csv')
    weather_files = glob.glob(pattern)
    
    if not weather_files:
        raise FileNotFoundError(f"No weather data files found in {WEATHER_DATA_DIR}")
    
    log_progress(f"Found {len(weather_files)} weather data files")
    
    all_data = []
    for file in tqdm(weather_files, desc="Loading weather files"):
        try:
            df = pd.read_csv(file)
            all_data.append(df)
        except Exception as e:
            log_progress(f"Error loading {file}: {str(e)}")
    
    if not all_data:
        raise ValueError("No valid weather data files could be loaded")
    
    combined_data = pd.concat(all_data, ignore_index=True)
    log_progress(f"Combined weather data: {len(combined_data):,} records from {combined_data['store_code'].nunique()} stores")
    
    return combined_data

def calculate_feels_like_temperature(weather_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate feels like temperature using different formulas based on conditions.
    
    Args:
        weather_df (pd.DataFrame): Combined weather data with hourly records
        
    Returns:
        pd.DataFrame: Data with added feels_like_temperature column
    """
    log_progress("Calculating feels-like temperatures...")
    
    # Validate and clean input data
    log_progress("Validating and cleaning data...")
    weather_df = validate_and_clean_data(weather_df)
    
    # Get required columns as numpy arrays for faster computation
    T = weather_df['temperature_2m'].to_numpy()
    RH = weather_df['relative_humidity_2m'].to_numpy()
    v_raw = weather_df['wind_speed_10m'].to_numpy()
    P = weather_df['pressure_msl'].to_numpy()
    
    # Convert wind speed (assuming input is in m/s)
    v_kmh, v_ms = v_raw * 3.6, v_raw  # convert m/s to km/h for v_kmh
    
    # Get altitudes and calculate station pressure
    # Load altitude data to get elevations
    if os.path.exists(ALTITUDE_FILE):
        altitude_df = pd.read_csv(ALTITUDE_FILE)
        altitude_dict = dict(zip(altitude_df['store_code'].astype(str), altitude_df['altitude_meters']))
        weather_df['elevation'] = weather_df['store_code'].astype(str).map(altitude_dict).fillna(0)
    else:
        weather_df['elevation'] = 0
        log_progress("Warning: No altitude data found, using sea level (0m) for all stores")
    
    h = weather_df['elevation'].to_numpy()
    P_sta = P * np.power(1 - 2.25577e-5*h, 5.25588)
    
    # Calculate air density
    rho = _rho_air(T, P_sta)
    
    # Initialize feels like temperature array
    AT = np.empty_like(T, dtype=float)
    
    # Create condition masks
    mask_cold = (T <= 10) & (v_kmh >= 4.8)
    mask_hot = (T >= 27) & (RH >= 40)
    mask_mid = ~(mask_cold | mask_hot)
    
    # Calculate feels like temperature for each condition
    log_progress("Calculating feels like temperatures...")
    log_progress(f"Cold conditions (wind chill): {mask_cold.sum():,} values")
    log_progress(f"Hot conditions (heat index): {mask_hot.sum():,} values")
    log_progress(f"Moderate conditions (Steadman): {mask_mid.sum():,} values")
    
    # 1. Wind chill for cold conditions
    if mask_cold.any():
        AT[mask_cold] = wind_chill(T[mask_cold], v_kmh[mask_cold], rho[mask_cold])
    
        # 2. Heat index for hot conditions
    if mask_hot.any():
        AT[mask_hot] = heat_index(T[mask_hot], RH[mask_hot])
    
    # 3. Steadman apparent temperature for moderate conditions
    if mask_mid.any():
        AT[mask_mid] = apparent_temp_steadman(
            T_c=T[mask_mid],
            RH=RH[mask_mid],
            v_ms=v_ms[mask_mid],
            p_hpa=P_sta[mask_mid],
            rad_sw=weather_df.loc[mask_mid, 'shortwave_radiation'].to_numpy(),
            rad_dr=weather_df.loc[mask_mid, 'direct_radiation'].to_numpy(),
            rad_df=weather_df.loc[mask_mid, 'diffuse_radiation'].to_numpy(),
            rad_lw=weather_df.loc[mask_mid, 'terrestrial_radiation'].to_numpy(),
            rho=rho[mask_mid]
        )
    
    # Add feels like temperature to data
    weather_df['feels_like_C'] = AT
    
    # Print summary statistics
    log_progress("Feels like temperature summary:")
    log_progress(f"Average difference from actual temperature: {(weather_df['feels_like_C'] - weather_df['temperature_2m']).mean():.2f}°C")
    log_progress(f"Maximum feels like: {weather_df['feels_like_C'].max():.2f}°C")
    log_progress(f"Minimum feels like: {weather_df['feels_like_C'].min():.2f}°C")
    
    # Now aggregate by store to get average feels-like temperature per store
    log_progress("Aggregating feels-like temperatures by store...")
    
    store_results = []
    for store_code in tqdm(weather_df['store_code'].unique(), desc="Processing stores"):
        store_data = weather_df[weather_df['store_code'] == store_code]
        
        store_results.append({
            'store_code': store_code,
            'elevation': store_data['elevation'].iloc[0],
            'avg_temperature': store_data['temperature_2m'].mean(),
            'avg_humidity': store_data['relative_humidity_2m'].mean(),
            'avg_wind_speed_kmh': store_data['wind_speed_10m'].mean() * 3.6,
            'avg_pressure': store_data['pressure_msl'].mean(),
            'feels_like_temperature': store_data['feels_like_C'].mean(),
            'min_feels_like': store_data['feels_like_C'].min(),
            'max_feels_like': store_data['feels_like_C'].max(),
            'cold_condition_hours': mask_cold[weather_df['store_code'] == store_code].sum(),
            'hot_condition_hours': mask_hot[weather_df['store_code'] == store_code].sum(),
            'moderate_condition_hours': mask_mid[weather_df['store_code'] == store_code].sum()
        })
    
    return pd.DataFrame(store_results)

def create_temperature_bands(feels_like_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create temperature bands for clustering constraints.
    
    Args:
        feels_like_df (pd.DataFrame): DataFrame with feels-like temperatures
        
    Returns:
        pd.DataFrame: DataFrame with temperature bands added
    """
    log_progress("Creating temperature bands...")
    
    df = feels_like_df.copy()
    
    # Create temperature bands based on feels-like temperature
    min_temp = df['feels_like_temperature'].min()
    max_temp = df['feels_like_temperature'].max()
    
    log_progress(f"Temperature range: {min_temp:.1f}°C to {max_temp:.1f}°C")
    
    # Create band boundaries (round to nearest TEMPERATURE_BAND_SIZE)
    min_band = int(np.floor(min_temp / TEMPERATURE_BAND_SIZE) * TEMPERATURE_BAND_SIZE)
    max_band = int(np.ceil(max_temp / TEMPERATURE_BAND_SIZE) * TEMPERATURE_BAND_SIZE)
    
    # Create band labels
    def get_temperature_band(temp: float) -> str:
        """Get temperature band label for a given temperature."""
        band_lower = int(np.floor(temp / TEMPERATURE_BAND_SIZE) * TEMPERATURE_BAND_SIZE)
        band_upper = band_lower + TEMPERATURE_BAND_SIZE
        return f"{band_lower}°C to {band_upper}°C"
    
    # Apply temperature bands
    df['temperature_band'] = df['feels_like_temperature'].apply(get_temperature_band)
    
    # Log band statistics
    band_counts = df['temperature_band'].value_counts().sort_index()
    log_progress("Temperature band distribution:")
    for band, count in band_counts.items():
        log_progress(f"  • {band}: {count} stores")
    
    # Save band summary
    band_summary = pd.DataFrame({
        'Temperature_Band': band_counts.index,
        'Store_Count': band_counts.values,
        'Min_Temp': [df[df['temperature_band'] == band]['feels_like_temperature'].min() 
                    for band in band_counts.index],
        'Max_Temp': [df[df['temperature_band'] == band]['feels_like_temperature'].max() 
                    for band in band_counts.index],
        'Avg_Temp': [df[df['temperature_band'] == band]['feels_like_temperature'].mean() 
                    for band in band_counts.index]
    })
    
    band_summary.to_csv(TEMPERATURE_BANDS_FILE, index=False)
    log_progress(f"Saved temperature band summary to {TEMPERATURE_BANDS_FILE}")
    
    return df

def main() -> None:
    """Main function to calculate feels-like temperature and create bands."""
    start_time = datetime.now()
    log_progress("Starting Feels-Like Temperature Calculation...")
    
    try:
        # Check if weather data exists
        if not os.path.exists(WEATHER_DATA_DIR):
            log_progress(f"Weather data directory {WEATHER_DATA_DIR} not found.")
            log_progress("Please run step4_download_weather_data.py first")
            return
        
        # Check if altitude data exists
        if not os.path.exists(ALTITUDE_FILE):
            log_progress(f"Altitude file {ALTITUDE_FILE} not found.")
            log_progress("Please run step4_download_weather_data.py first")
            return
        
        # Load weather data
        weather_df = load_weather_data()
        
        # Calculate feels-like temperatures
        feels_like_df = calculate_feels_like_temperature(weather_df)
        
        # Create temperature bands
        final_df = create_temperature_bands(feels_like_df)
        
        # Save results
        final_df.to_csv(OUTPUT_FILE, index=False)
        log_progress(f"Saved feels-like temperature data to {OUTPUT_FILE}")
        
        # Summary statistics
        log_progress("\n=== SUMMARY ===")
        log_progress(f"Processed {len(final_df)} stores")
        log_progress(f"Temperature range: {final_df['feels_like_temperature'].min():.1f}°C to {final_df['feels_like_temperature'].max():.1f}°C")
        log_progress(f"Number of temperature bands: {final_df['temperature_band'].nunique()}")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        log_progress(f"Completed in {execution_time:.1f} seconds")
        
        log_progress("\nNext step: Run python src/step6_cluster_analysis.py for temperature-aware clustering")
        
    except Exception as e:
        log_progress(f"Error in feels-like temperature calculation: {str(e)}")
        raise

if __name__ == "__main__":
    main() 