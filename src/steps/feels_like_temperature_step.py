"""
Step 5: Calculate Feels-Like Temperature for Stores

This step calculates feels-like temperature for all stores using weather data
and creates temperature bands for clustering constraints.

Author: Data Pipeline Team
Date: 2025-10-10
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from datetime import datetime
import os
from pathlib import Path
from core.step import Step
from core.context import StepContext
from core.logger import PipelineLogger
from core.exceptions import DataValidationError


@dataclass
class FeelsLikeConfig:
    """Configuration for feels-like temperature calculation."""
    seasonal_focus_months: List[int]
    lookback_years: int
    seasonal_band_column: str
    seasonal_feels_like_column: str
    temperature_band_size: int
    
    # Physical constants
    Rd: float = 287.05  # J/(kg·K) - Gas constant for dry air
    cp: float = 1005.0  # J/(kg·K) - Specific heat capacity
    rho0: float = 1.225  # kg/m³ - Reference air density at sea level


class FeelsLikeTemperatureStep(Step):
    """
    Step 5: Calculate feels-like temperature for stores.
    
    This step:
    1. Loads weather data and altitude data
    2. Calculates feels-like temperature using appropriate formulas
    3. Creates temperature bands for clustering
    4. Saves results for downstream steps
    """
    
    def __init__(
        self,
        weather_data_repo,  # WeatherDataRepository
        altitude_repo,      # CsvFileRepository
        temperature_output_repo,  # CsvFileRepository
        bands_output_repo,        # CsvFileRepository
        config: FeelsLikeConfig,
        logger: PipelineLogger,
        step_name: str = "Feels-Like Temperature",
        step_number: int = 5,
        target_yyyymm: Optional[str] = None,
        target_period: Optional[str] = None
    ):
        """
        Initialize the FeelsLikeTemperatureStep.
        
        Args:
            weather_data_repo: Repository for weather data access
            altitude_repo: Repository for altitude data
            temperature_output_repo: Repository for temperature output (period-specific)
            bands_output_repo: Repository for bands output (period-specific)
            config: Configuration for temperature calculations
            logger: Pipeline logger
            step_name: Name of the step
            step_number: Step number in pipeline
            target_yyyymm: Target year-month (e.g., "202506")
            target_period: Target period (e.g., "A" or "B")
            
        Note: Follows Steps 1 & 2 pattern - separate repository per output file.
        """
        super().__init__(logger, step_name, step_number)
        self.weather_data_repo = weather_data_repo
        self.altitude_repo = altitude_repo
        self.temperature_output_repo = temperature_output_repo
        self.bands_output_repo = bands_output_repo
        self.config = config
        self.target_yyyymm = target_yyyymm
        self.target_period = target_period
    
    def setup(self, context: StepContext) -> StepContext:
        """
        Load weather data and altitude data.
        
        Args:
            context: Step context
            
        Returns:
            Updated context with loaded data
        """
        self.logger.info("Loading weather and altitude data...")
        
        # Load weather data using repository
        weather_result = self.weather_data_repo.get_weather_data_for_period(
            target_yyyymm=self.target_yyyymm,
            target_period=self.target_period
        )
        
        weather_data = weather_result.get('weather_files')
        altitude_data = weather_result.get('altitude_data')
        
        if weather_data is None or weather_data.empty:
            raise DataValidationError("No weather data loaded")
        
        self.logger.info(f"Loaded weather data: {len(weather_data)} records from {weather_data['store_code'].nunique()} stores")
        
        # Store in context
        context.data = {
            'weather_data': weather_data,
            'altitude_data': altitude_data,
            'periods': weather_result.get('periods', [])
        }
        
        return context
    
    def apply(self, context: StepContext) -> StepContext:
        """
        Calculate feels-like temperatures and create temperature bands.
        
        Args:
            context: Step context with loaded data
            
        Returns:
            Updated context with calculated temperatures
        """
        weather_data = context.data['weather_data']
        altitude_data = context.data['altitude_data']
        
        self.logger.info("Calculating feels-like temperatures...")
        
        # Step 1: Validate and clean data
        weather_data = self._validate_and_clean_data(weather_data)
        
        # Step 2: Merge altitude data
        weather_data = self._merge_altitude_data(weather_data, altitude_data)
        
        # Step 3: Calculate feels-like temperature
        weather_data = self._calculate_feels_like_temperature(weather_data)
        
        # Step 4: Aggregate by store
        store_results = self._aggregate_by_store(weather_data)
        
        # Step 5: Create temperature bands
        store_results = self._create_temperature_bands(store_results)
        
        # Store results in context
        context.data['processed_weather'] = store_results
        context.data['temperature_bands'] = self._create_band_summary(store_results)
        
        self.logger.info(f"Calculated feels-like temperatures for {len(store_results)} stores")
        
        return context
    
    def validate(self, context: StepContext) -> None:
        """
        Validate calculation results.
        
        Args:
            context: Step context with calculated data
            
        Raises:
            DataValidationError: If validation fails
        """
        processed_weather = context.data.get('processed_weather')
        
        if processed_weather is None or processed_weather.empty:
            raise DataValidationError("No processed weather data")
        
        # Check for required columns
        required_cols = ['store_code', 'feels_like_temperature', 'temperature_band']
        missing_cols = [col for col in required_cols if col not in processed_weather.columns]
        
        if missing_cols:
            raise DataValidationError(f"Missing required columns: {missing_cols}")
        
        # Check for null values in critical columns
        null_counts = processed_weather[required_cols].isnull().sum()
        if null_counts.any():
            raise DataValidationError(f"Null values found in critical columns: {null_counts[null_counts > 0].to_dict()}")
        
        self.logger.info(f"Validation passed: {len(processed_weather)} stores with valid data")
    
    def persist(self, context: StepContext) -> StepContext:
        """
        Persist phase: Save temperature calculation results.
        
        Saves two output files:
        1. stores_with_feels_like_temperature_{period}.csv - Main temperature data
        2. temperature_bands_{period}.csv - Temperature band summary
        
        Also creates generic symlinks for backward compatibility:
        - stores_with_feels_like_temperature.csv -> period-specific file
        - temperature_bands.csv -> period-specific file
        
        Uses separate repositories for each file following the refactored pattern
        (Steps 1 & 2). Period is included in filename for explicit tracking.
        
        Args:
            context: Step context with results to save
            
        Returns:
            Updated context
        """
        from pathlib import Path
        
        processed_weather = context.data['processed_weather']
        temperature_bands = context.data['temperature_bands']
        
        # Save main temperature data (repository has full path with period)
        self.temperature_output_repo.save(processed_weather)
        self.logger.info(f"Saved temperature data: {self.temperature_output_repo.file_path}")
        
        # Save temperature bands summary (repository has full path with period)
        self.bands_output_repo.save(temperature_bands)
        self.logger.info(f"Saved temperature bands: {self.bands_output_repo.file_path}")
        
        # Create generic symlinks for backward compatibility
        self._create_generic_symlink(
            self.temperature_output_repo.file_path,
            "output/stores_with_feels_like_temperature.csv"
        )
        self._create_generic_symlink(
            self.bands_output_repo.file_path,
            "output/temperature_bands.csv"
        )
        
        # Log summary statistics
        self.logger.info(f"Temperature range: {processed_weather['feels_like_temperature'].min():.1f}°C to {processed_weather['feels_like_temperature'].max():.1f}°C")
        self.logger.info(f"Number of temperature bands: {processed_weather['temperature_band'].nunique()}")
        self.logger.info(f"Persisted results for {len(processed_weather)} stores")
        
        return context
    
    def _create_generic_symlink(self, source_file: str, generic_file: str) -> None:
        """
        Create symlink from generic filename to period-specific file.
        
        For backward compatibility with steps expecting generic filenames.
        
        Args:
            source_file: Period-specific file path (e.g., file_202506A.csv)
            generic_file: Generic file path (e.g., file.csv)
        """
        source_path = Path(source_file)
        generic_path = Path(generic_file)
        
        if not source_path.exists():
            self.logger.warning(f"Source file doesn't exist: {source_file}")
            return
        
        # Remove existing symlink or file
        if generic_path.exists() or generic_path.is_symlink():
            generic_path.unlink()
        
        # Create symlink (relative path for portability)
        generic_path.symlink_to(source_path.name)
        self.logger.info(f"Created symlink: {generic_file} -> {source_path.name}")
    
    # ========================================================================
    # Private Helper Methods
    # ========================================================================
    
    def _validate_and_clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean weather data.
        
        Args:
            data: Raw weather data
            
        Returns:
            Cleaned weather data
        """
        data = data.copy()
        
        # Define reasonable limits
        limits = {
            'temperature_2m': (-50, 50),
            'relative_humidity_2m': (0, 100),
            'wind_speed_10m': (0, 25),
            'pressure_msl': (900, 1100),
            'shortwave_radiation': (0, 1500),
            'direct_radiation': (0, 1200),
            'diffuse_radiation': (0, 800),
            'terrestrial_radiation': (-100, 500)
        }
        
        # Apply limits
        for col, (min_val, max_val) in limits.items():
            if col in data.columns:
                outliers = data[~data[col].between(min_val, max_val)]
                if len(outliers) > 0:
                    self.logger.info(f"Clipping {len(outliers)} outliers in {col}")
                data[col] = data[col].clip(min_val, max_val)
        
        return data
    
    def _merge_altitude_data(self, weather_data: pd.DataFrame, altitude_data: pd.DataFrame) -> pd.DataFrame:
        """
        Merge altitude data with weather data.
        
        Args:
            weather_data: Weather data
            altitude_data: Altitude data
            
        Returns:
            Weather data with altitude information
        """
        if altitude_data is None or altitude_data.empty:
            self.logger.info("WARNING: No altitude data available, using 0m elevation")
            weather_data['elevation'] = 0
            return weather_data
        
        # Create altitude mapping
        altitude_dict = dict(zip(
            altitude_data['store_code'].astype(str),
            altitude_data['altitude_meters']
        ))
        
        # Map to weather data
        weather_data['elevation'] = weather_data['store_code'].astype(str).map(altitude_dict).fillna(0)
        
        return weather_data
    
    def _calculate_feels_like_temperature(self, weather_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate feels-like temperature using appropriate formulas.
        
        Args:
            weather_data: Weather data with all required fields
            
        Returns:
            Weather data with feels_like_C column added
        """
        # Extract required columns
        T = weather_data['temperature_2m'].to_numpy()
        RH = weather_data['relative_humidity_2m'].to_numpy()
        v_raw = weather_data['wind_speed_10m'].to_numpy()
        P = weather_data['pressure_msl'].to_numpy()
        h = weather_data['elevation'].to_numpy()
        
        # Convert wind speed
        v_kmh = v_raw * 3.6  # m/s to km/h
        v_ms = v_raw
        
        # Calculate station pressure
        P_sta = P * np.power(1 - 2.25577e-5 * h, 5.25588)
        
        # Calculate air density
        rho = self._calculate_air_density(T, P_sta)
        
        # Initialize feels-like temperature array
        AT = np.empty_like(T, dtype=float)
        
        # Create condition masks
        mask_cold = (T <= 10) & (v_kmh >= 4.8)
        mask_hot = (T >= 27) & (RH >= 40)
        mask_mid = ~(mask_cold | mask_hot)
        
        self.logger.info(f"Cold conditions: {mask_cold.sum()} records")
        self.logger.info(f"Hot conditions: {mask_hot.sum()} records")
        self.logger.info(f"Moderate conditions: {mask_mid.sum()} records")
        
        # Calculate feels-like temperature for each condition
        if mask_cold.any():
            AT[mask_cold] = self._wind_chill(T[mask_cold], v_kmh[mask_cold], rho[mask_cold])
        
        if mask_hot.any():
            AT[mask_hot] = self._heat_index(T[mask_hot], RH[mask_hot])
        
        if mask_mid.any():
            AT[mask_mid] = self._steadman_apparent_temp(
                T[mask_mid], RH[mask_mid], v_ms[mask_mid], P_sta[mask_mid],
                weather_data.loc[mask_mid, 'shortwave_radiation'].to_numpy(),
                weather_data.loc[mask_mid, 'direct_radiation'].to_numpy(),
                weather_data.loc[mask_mid, 'diffuse_radiation'].to_numpy(),
                weather_data.loc[mask_mid, 'terrestrial_radiation'].to_numpy(),
                rho[mask_mid]
            )
        
        # Add to dataframe
        weather_data['feels_like_C'] = AT
        
        return weather_data
    
    def _calculate_air_density(self, T_c: np.ndarray, p_hpa: np.ndarray) -> np.ndarray:
        """Calculate air density from temperature and pressure."""
        return (p_hpa * 100) / (self.config.Rd * (T_c + 273.15))
    
    def _wind_chill(self, T_c: np.ndarray, V_kmh: np.ndarray, rho: np.ndarray) -> np.ndarray:
        """Calculate wind-chill temperature with air density correction."""
        V_eff = V_kmh * np.sqrt(rho / self.config.rho0)
        V16 = np.power(V_eff, 0.16)
        return 13.12 + 0.6215*T_c - 11.37*V16 + 0.3965*T_c*V16
    
    def _heat_index(self, T_c: np.ndarray, RH: np.ndarray) -> np.ndarray:
        """Calculate heat index from temperature and relative humidity."""
        T_f = T_c * 9/5 + 32
        HI_f = (-42.379 + 2.04901523*T_f + 10.14333127*RH
                - 0.22475541*T_f*RH - 0.00683783*T_f**2
                - 0.05481717*RH**2 + 0.00122874*T_f**2*RH
                + 0.00085282*T_f*RH**2 - 0.00000199*T_f**2*RH**2)
        return (HI_f - 32) * 5/9
    
    def _steadman_apparent_temp(
        self, T_c: np.ndarray, RH: np.ndarray, v_ms: np.ndarray,
        p_hpa: np.ndarray, rad_sw: np.ndarray, rad_dr: np.ndarray,
        rad_df: np.ndarray, rad_lw: np.ndarray, rho: np.ndarray
    ) -> np.ndarray:
        """Calculate Steadman's apparent temperature."""
        e = (RH/100) * 6.112 * np.exp(17.67*T_c / (T_c + 243.5))
        v_e = v_ms * np.sqrt(rho / self.config.rho0)
        R_n = rad_sw + rad_dr + rad_df + rad_lw
        return T_c + 0.348*e - 0.70*v_e + 0.70*R_n/(rho*self.config.cp) - 4.25
    
    def _aggregate_by_store(self, weather_data: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregate weather data by store.
        
        Args:
            weather_data: Weather data with feels-like temperatures
            
        Returns:
            Store-level aggregated data with all required columns
        """
        # Extract year/month for seasonal filtering
        weather_data = self._extract_year_month(weather_data)
        
        # Calculate seasonal subset
        seasonal_data = self._filter_seasonal_data(weather_data)
        seasonal_means = seasonal_data.groupby('store_code')['feels_like_C'].mean().to_dict() if not seasonal_data.empty else {}
        
        # Create condition masks for tracking hours
        v_kmh = weather_data['wind_speed_10m'] * 3.6
        mask_cold = (weather_data['temperature_2m'] <= 10) & (v_kmh >= 4.8)
        mask_hot = (weather_data['temperature_2m'] >= 27) & (weather_data['relative_humidity_2m'] >= 40)
        mask_mid = ~(mask_cold | mask_hot)
        
        store_results = []
        
        for store_code in weather_data['store_code'].unique():
            store_data = weather_data[weather_data['store_code'] == store_code]
            store_mask = weather_data['store_code'] == store_code
            
            store_results.append({
                'store_code': store_code,
                'elevation': store_data['elevation'].iloc[0],
                'avg_temperature': store_data['temperature_2m'].mean(),
                'avg_humidity': store_data['relative_humidity_2m'].mean(),
                'avg_wind_speed_kmh': store_data['wind_speed_10m'].mean() * 3.6,
                'avg_pressure': store_data['pressure_msl'].mean(),
                'feels_like_temperature': store_data['feels_like_C'].mean(),
                self.config.seasonal_feels_like_column: seasonal_means.get(store_code, np.nan),
                'min_feels_like': store_data['feels_like_C'].min(),
                'max_feels_like': store_data['feels_like_C'].max(),
                'cold_condition_hours': mask_cold[store_mask].sum(),
                'hot_condition_hours': mask_hot[store_mask].sum(),
                'moderate_condition_hours': mask_mid[store_mask].sum()
            })
        
        return pd.DataFrame(store_results)
    
    def _create_temperature_bands(self, feels_like_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create temperature bands for clustering (overall and seasonal).
        
        Args:
            feels_like_df: DataFrame with feels-like temperatures
            
        Returns:
            DataFrame with temperature bands added
        """
        df = feels_like_df.copy()
        
        # Create band labels
        def get_temperature_band(temp: float) -> str:
            if pd.isna(temp):
                return np.nan
            band_lower = int(np.floor(temp / self.config.temperature_band_size) * self.config.temperature_band_size)
            band_upper = band_lower + self.config.temperature_band_size
            return f"{band_lower}°C to {band_upper}°C"
        
        # Create overall temperature band
        df['temperature_band'] = df['feels_like_temperature'].apply(get_temperature_band)
        
        # Create seasonal temperature band if seasonal data exists
        seasonal_col = self.config.seasonal_feels_like_column
        seasonal_band_col = self.config.seasonal_band_column
        
        if seasonal_col in df.columns and df[seasonal_col].notna().any():
            df[seasonal_band_col] = df[seasonal_col].apply(get_temperature_band)
            seasonal_band_count = df[seasonal_band_col].notna().sum()
            self.logger.info(f"Created seasonal temperature bands: {seasonal_band_count} stores with seasonal data")
        
        # Log band distribution
        band_counts = df['temperature_band'].value_counts().sort_index()
        self.logger.info("Temperature band distribution:")
        for band, count in band_counts.items():
            self.logger.info(f"  {band}: {count} stores")
        
        return df
    
    def _filter_seasonal_data(self, weather_data: pd.DataFrame) -> pd.DataFrame:
        """
        Filter weather data for seasonal focus months (Sep, Nov).
        
        Args:
            weather_data: Weather data with year/month columns
            
        Returns:
            Filtered seasonal data
        """
        # Check if year/month columns exist
        if 'year' not in weather_data.columns or 'month' not in weather_data.columns:
            self.logger.info("No year/month columns for seasonal filtering")
            return pd.DataFrame()
        
        # Filter for seasonal focus months
        seasonal_months = self.config.seasonal_focus_months  # [9, 11]
        
        if not seasonal_months:
            return pd.DataFrame()
        
        # Get recent years
        available_years = sorted(weather_data['year'].dropna().unique())
        if not available_years:
            return pd.DataFrame()
        
        selected_years = list(reversed(available_years))[:self.config.lookback_years]
        
        # Filter data
        year_mask = weather_data['year'].isin(selected_years)
        month_mask = weather_data['month'].isin(seasonal_months)
        
        seasonal_data = weather_data[year_mask & month_mask]
        
        if seasonal_data.empty:
            # Fallback: use focus months across all years
            seasonal_data = weather_data[weather_data['month'].isin(seasonal_months)]
        
        self.logger.info(f"Filtered seasonal data: {len(seasonal_data)} records from months {seasonal_months}")
        
        return seasonal_data
    
    def _extract_year_month(self, weather_data: pd.DataFrame) -> pd.DataFrame:
        """
        Extract year and month from datetime column.
        
        Args:
            weather_data: Weather data with time column
            
        Returns:
            Weather data with year and month columns added
        """
        if 'year' in weather_data.columns and 'month' in weather_data.columns:
            return weather_data
        
        if 'time' in weather_data.columns:
            try:
                weather_data['year'] = pd.to_datetime(weather_data['time']).dt.year
                weather_data['month'] = pd.to_datetime(weather_data['time']).dt.month
                self.logger.info("Extracted year and month from time column")
            except Exception as e:
                self.logger.info(f"Could not extract year/month from time column: {e}")
        
        return weather_data
    
    def _create_band_summary(self, feels_like_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create temperature band summary statistics.
        
        Args:
            feels_like_df: DataFrame with temperature bands
            
        Returns:
            Band summary DataFrame
        """
        band_counts = feels_like_df['temperature_band'].value_counts().sort_index()
        
        summary = pd.DataFrame({
            'Temperature_Band': band_counts.index,
            'Store_Count': band_counts.values,
            'Min_Temp': [feels_like_df[feels_like_df['temperature_band'] == band]['feels_like_temperature'].min()
                        for band in band_counts.index],
            'Max_Temp': [feels_like_df[feels_like_df['temperature_band'] == band]['feels_like_temperature'].max()
                        for band in band_counts.index],
            'Avg_Temp': [feels_like_df[feels_like_df['temperature_band'] == band]['feels_like_temperature'].mean()
                        for band in band_counts.index]
        })
        
        return summary
