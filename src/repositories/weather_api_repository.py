#!/usr/bin/env python3
"""
Weather API Repository - Handles Open-Meteo API interactions

This repository abstracts all weather data API calls, including:
- Historical weather data from Open-Meteo Archive API
- Elevation data from Open-Meteo Elevation API
"""

from typing import Dict, Optional
import requests
import pandas as pd
from src.core.logger import PipelineLogger
from .base import Repository


class WeatherApiError(Exception):
    """Raised when weather API calls fail."""
    pass


class WeatherApiRepository(Repository):
    """Repository for Open-Meteo weather and elevation APIs."""
    
    # API Configuration
    WEATHER_API_URL = 'https://archive-api.open-meteo.com/v1/archive'
    ELEVATION_API_URL = 'https://api.open-meteo.com/v1/elevation'
    DEFAULT_TIMEOUT = 30
    
    # Weather variables to request
    HOURLY_VARIABLES = [
        'temperature_2m',
        'relative_humidity_2m',
        'wind_speed_10m',
        'wind_direction_10m',
        'precipitation',
        'rain',
        'snowfall',
        'cloud_cover',
        'weather_code',
        'pressure_msl',
        'direct_radiation',
        'diffuse_radiation',
        'direct_normal_irradiance',
        'terrestrial_radiation',
        'shortwave_radiation',
        'et0_fao_evapotranspiration'
    ]
    
    def __init__(self, logger: PipelineLogger, timezone: str = 'Asia/Shanghai'):
        """
        Initialize Weather API repository.
        
        Args:
            logger: PipelineLogger instance for logging
            timezone: Timezone for weather data (default: Asia/Shanghai)
        """
        super().__init__(logger)
        self.timezone = timezone
    
    def fetch_weather_data(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        store_code: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Fetch historical weather data for a location and date range.
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            store_code: Optional store code to add to result
            
        Returns:
            pd.DataFrame: Hourly weather data with all variables
            
        Raises:
            WeatherApiError: If API call fails
        """
        self.logger.info(
            f"Fetching weather data for lat={latitude:.4f}, lon={longitude:.4f}, "
            f"dates={start_date} to {end_date}",
            self.repo_name
        )
        
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'hourly': ','.join(self.HOURLY_VARIABLES),
            'timezone': self.timezone,
            'start_date': start_date,
            'end_date': end_date,
            'models': 'best_match'
        }
        
        try:
            response = requests.get(
                self.WEATHER_API_URL,
                params=params,
                timeout=self.DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'hourly' not in data:
                raise WeatherApiError("No hourly data in API response")
            
            df = pd.DataFrame(data['hourly'])
            
            # Verify all required columns are present
            missing_columns = [col for col in self.HOURLY_VARIABLES if col not in df.columns]
            if missing_columns:
                raise WeatherApiError(f"Missing required columns: {missing_columns}")
            
            # Add store information if provided
            if store_code:
                df['store_code'] = store_code
            df['latitude'] = latitude
            df['longitude'] = longitude
            
            self.logger.info(
                f"Successfully fetched {len(df)} hourly records",
                self.repo_name
            )
            
            return df
            
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if hasattr(e, 'response') else 'unknown'
            body = e.response.text[:500] if hasattr(e, 'response') else ''
            self.logger.error(
                f"HTTP error {status} fetching weather data: {body}",
                self.repo_name
            )
            raise WeatherApiError(f"HTTP {status}: {body}") from e
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {str(e)}", self.repo_name)
            raise WeatherApiError(f"Request failed: {str(e)}") from e
            
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}", self.repo_name)
            raise WeatherApiError(f"Unexpected error: {str(e)}") from e
    
    def get_elevation(self, latitude: float, longitude: float) -> float:
        """
        Get elevation for coordinates using Open-Meteo Elevation API.
        
        Args:
            latitude: Latitude in decimal degrees
            longitude: Longitude in decimal degrees
            
        Returns:
            float: Elevation in meters above sea level
            
        Raises:
            WeatherApiError: If API call fails
        """
        self.logger.debug(
            f"Fetching elevation for lat={latitude:.6f}, lon={longitude:.6f}",
            self.repo_name
        )
        
        params = {
            'latitude': latitude,
            'longitude': longitude
        }
        
        try:
            response = requests.get(
                self.ELEVATION_API_URL,
                params=params,
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            
            if 'elevation' in data and data['elevation']:
                elevation = data['elevation'][0]
                self.logger.debug(
                    f"Retrieved elevation: {elevation}m",
                    self.repo_name
                )
                return elevation
            else:
                self.logger.warning(
                    f"No elevation data in response, returning 0.0",
                    self.repo_name
                )
                return 0.0
                
        except Exception as e:
            self.logger.warning(
                f"Could not get elevation: {str(e)}, returning 0.0",
                self.repo_name
            )
            return 0.0
    
    def check_rate_limit(self, response: requests.Response) -> bool:
        """
        Check if response indicates rate limiting.
        
        Args:
            response: HTTP response object
            
        Returns:
            bool: True if rate limited (HTTP 429)
        """
        return response.status_code == 429
    
    def get_all(self):
        """Not applicable for API repository - data is fetched on demand."""
        raise NotImplementedError("WeatherApiRepository does not support get_all()")
    
    def save(self, data: pd.DataFrame) -> None:
        """Not applicable for API repository - data is not persisted here."""
        raise NotImplementedError("WeatherApiRepository does not support save()")
