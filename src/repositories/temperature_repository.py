"""
Temperature Repository - Data access for temperature data

Provides access to store temperature data for temperature-aware clustering.

Author: Data Pipeline Team
Date: 2025-10-22
"""

import pandas as pd
import os
from typing import Optional
from pathlib import Path


class TemperatureRepository:
    """Repository for temperature data access."""
    
    DEFAULT_TEMPERATURE_FILE = "output/stores_with_feels_like_temperature.csv"
    
    def __init__(
        self, 
        base_path: str = ".",
        temperature_file: Optional[str] = None,
        preferred_band_column: str = "temperature_band_q3q4_seasonal"
    ):
        """
        Initialize the TemperatureRepository.
        
        Args:
            base_path: Base path for data files (default: current directory)
            temperature_file: Path to temperature file (default: uses DEFAULT_TEMPERATURE_FILE)
            preferred_band_column: Preferred temperature band column name
        """
        self.base_path = Path(base_path)
        self.temperature_file = temperature_file or self.DEFAULT_TEMPERATURE_FILE
        self.preferred_band_column = preferred_band_column
    
    def get_temperature_data(self) -> Optional[pd.DataFrame]:
        """
        Load temperature data if available.
        
        Returns:
            DataFrame with temperature data, or None if not found
            
        Notes:
            - Handles both 'str_code' and 'store_code' column names
            - Sets preferred temperature band column
            - Returns None if file doesn't exist (graceful degradation)
        """
        file_path = self.base_path / self.temperature_file
        
        if not file_path.exists():
            return None
        
        try:
            temp_df = pd.read_csv(file_path)
            
            # Handle both possible column names for store identification
            if 'str_code' in temp_df.columns:
                temp_df.set_index('str_code', inplace=True)
            elif 'store_code' in temp_df.columns:
                temp_df.set_index('store_code', inplace=True)
            else:
                raise ValueError("Temperature data must have either 'str_code' or 'store_code' column")
            
            # Identify temperature band column
            if self.preferred_band_column in temp_df.columns:
                band_col = self.preferred_band_column
            elif 'temperature_band' in temp_df.columns:
                band_col = 'temperature_band'
            else:
                raise ValueError("Temperature data must have a temperature band column")
            
            # Store band column name for reference
            temp_df['__band_col__'] = band_col
            
            return temp_df
            
        except Exception as e:
            # Log error but return None for graceful degradation
            print(f"Warning: Could not load temperature data: {str(e)}")
            return None
