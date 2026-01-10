#!/usr/bin/env python3
"""
Weather File Repository - Manages weather data file operations

Purpose: Handle saving and retrieving weather data CSV files for individual stores and periods.

This repository manages the file system operations for weather data, including:
- Saving weather data to CSV files with proper naming conventions
- Checking which stores have already been downloaded for a period
- Managing the weather_data output directory structure

Author: Data Pipeline
Date: 2025-10-10
"""

from __future__ import annotations
from typing import Set, Optional
from pathlib import Path
import pandas as pd

from src.core.logger import PipelineLogger
from repositories.base import Repository


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class WeatherFileError(Exception):
    """Raised when weather file operations fail."""
    pass


# ============================================================================
# WEATHER FILE REPOSITORY
# ============================================================================

class WeatherFileRepository(Repository):
    """
    Repository for weather data file management.
    
    This repository handles all file system operations for weather data,
    including saving individual store weather files and checking download status.
    """
    
    # Constants
    WEATHER_DATA_DIR = "output/weather_data"
    FILE_NAME_PATTERN = "weather_{store_code}_{lat}_{lon}_{period}.csv"
    
    def __init__(
        self,
        output_dir: str,
        logger: PipelineLogger
    ):
        """
        Initialize Weather File Repository.
        
        Args:
            output_dir: Base output directory path
            logger: Pipeline logger
        """
        super().__init__(logger)
        # Use output_dir directly - don't nest another weather_data folder
        # The factory already passes "output/weather_data" as output_dir
        self.output_dir = Path(output_dir)
        self.weather_dir = self.output_dir
        
        # Ensure directory exists
        self.weather_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(
            f"Weather file repository initialized: {self.weather_dir}",
            self.repo_name
        )
    
    # ========================================================================
    # PUBLIC METHODS
    # ========================================================================
    
    def save_weather_file(
        self,
        weather_df: pd.DataFrame,
        store_code: str,
        latitude: float,
        longitude: float,
        period_label: str
    ) -> str:
        """
        Save weather data to CSV file.
        
        Args:
            weather_df: Weather data DataFrame
            store_code: Store identifier
            latitude: Store latitude
            longitude: Store longitude
            period_label: Period label (e.g., "20250101_to_20250115")
            
        Returns:
            str: Path to saved file
            
        Raises:
            WeatherFileError: If file save fails
        """
        try:
            # Generate filename
            filename = self._generate_filename(
                store_code,
                latitude,
                longitude,
                period_label
            )
            
            file_path = self.weather_dir / filename
            
            # Save to CSV
            weather_df.to_csv(file_path, index=False)
            
            self.logger.debug(
                f"Saved weather file: {filename}",
                self.repo_name
            )
            
            return str(file_path)
            
        except Exception as e:
            error_msg = f"Failed to save weather file for {store_code}: {str(e)}"
            self.logger.error(error_msg, self.repo_name)
            raise WeatherFileError(error_msg) from e
    
    def get_downloaded_stores_for_period(
        self,
        period_label: str
    ) -> Set[str]:
        """
        Get set of stores already downloaded for a period.
        
        Args:
            period_label: Period label (e.g., "20250101_to_20250115")
            
        Returns:
            Set of store codes that have been downloaded
        """
        try:
            downloaded_stores = set()
            
            # Search for files matching the period
            pattern = f"weather_*_{period_label}.csv"
            
            for file_path in self.weather_dir.glob(pattern):
                # Extract store code from filename
                # Format: weather_{store_code}_{lat}_{lon}_{period}.csv
                parts = file_path.stem.split('_')
                if len(parts) >= 2:
                    store_code = parts[1]
                    downloaded_stores.add(store_code)
            
            self.logger.debug(
                f"Found {len(downloaded_stores)} downloaded stores for period {period_label}",
                self.repo_name
            )
            
            return downloaded_stores
            
        except Exception as e:
            self.logger.warning(
                f"Error checking downloaded stores: {str(e)}",
                self.repo_name
            )
            # Return empty set on error (safe fallback)
            return set()
    
    def load_weather_file(
        self,
        store_code: str,
        latitude: float,
        longitude: float,
        period_label: str
    ) -> Optional[pd.DataFrame]:
        """
        Load weather data from CSV file.
        
        Args:
            store_code: Store identifier
            latitude: Store latitude
            longitude: Store longitude
            period_label: Period label (e.g., "20250101_to_20250115")
            
        Returns:
            pd.DataFrame or None: Weather data or None if file doesn't exist
            
        Raises:
            WeatherFileError: If file exists but cannot be loaded
        """
        try:
            filename = self._generate_filename(
                store_code,
                latitude,
                longitude,
                period_label
            )
            
            file_path = self.weather_dir / filename
            
            if not file_path.exists():
                return None
            
            weather_df = pd.read_csv(file_path)
            
            self.logger.debug(
                f"Loaded weather file: {filename}",
                self.repo_name
            )
            
            return weather_df
            
        except Exception as e:
            error_msg = f"Failed to load weather file for {store_code}: {str(e)}"
            self.logger.error(error_msg, self.repo_name)
            raise WeatherFileError(error_msg) from e
    
    def get_all_weather_files(self) -> list[str]:
        """
        Get list of all weather data files.
        
        Returns:
            List of file paths
        """
        try:
            files = [str(f) for f in self.weather_dir.glob("weather_*.csv")]
            
            self.logger.debug(
                f"Found {len(files)} weather files",
                self.repo_name
            )
            
            return files
            
        except Exception as e:
            self.logger.warning(
                f"Error listing weather files: {str(e)}",
                self.repo_name
            )
            return []
    
    def delete_weather_file(
        self,
        store_code: str,
        latitude: float,
        longitude: float,
        period_label: str
    ) -> bool:
        """
        Delete weather data file.
        
        Args:
            store_code: Store identifier
            latitude: Store latitude
            longitude: Store longitude
            period_label: Period label (e.g., "20250101_to_20250115")
            
        Returns:
            bool: True if file was deleted, False if it didn't exist
            
        Raises:
            WeatherFileError: If file exists but cannot be deleted
        """
        try:
            filename = self._generate_filename(
                store_code,
                latitude,
                longitude,
                period_label
            )
            
            file_path = self.weather_dir / filename
            
            if not file_path.exists():
                return False
            
            file_path.unlink()
            
            self.logger.debug(
                f"Deleted weather file: {filename}",
                self.repo_name
            )
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to delete weather file for {store_code}: {str(e)}"
            self.logger.error(error_msg, self.repo_name)
            raise WeatherFileError(error_msg) from e
    
    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================
    
    def _generate_filename(
        self,
        store_code: str,
        latitude: float,
        longitude: float,
        period_label: str
    ) -> str:
        """
        Generate standardized filename for weather data.
        
        Format matches OLD Step 4:
        weather_data_{store_code}_{longitude:.6f}_{latitude:.6f}_{period_label}.csv
        
        Args:
            store_code: Store identifier
            latitude: Store latitude
            longitude: Store longitude
            period_label: Period label (e.g., "20250101_to_20250115")
            
        Returns:
            str: Filename
        """
        # Format: weather_data_{store}_{lon:.6f}_{lat:.6f}_{period}.csv
        # Note: Longitude BEFORE latitude (OLD Step 4 format)
        # Note: 6 decimal places (not 4)
        # Note: Dots in coordinates (not underscores)
        return f"weather_data_{store_code}_{longitude:.6f}_{latitude:.6f}_{period_label}.csv"
    
    def get_all(self) -> pd.DataFrame:
        """Get all weather files (implements abstract method from Repository)."""
        self.logger.warning(
            "get_all() not applicable for WeatherFileRepository - use get_all_weather_files() instead",
            self.repo_name
        )
        return pd.DataFrame()
    
    def save(self, data: pd.DataFrame) -> None:
        """Not applicable - use save_weather_file instead (implements abstract method)."""
        self.logger.warning(
            "save() not applicable for WeatherFileRepository - use save_weather_file() instead",
            self.repo_name
        )
