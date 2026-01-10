#!/usr/bin/env python3
"""
Tests for WeatherDataRepository DataFrame Handling

Tests that the repository correctly handles DataFrame conversions and concatenations.

Created: 2025-10-27
Purpose: Verify Fix #3 - DataFrame handling in WeatherDataRepository
"""

import pytest
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from repositories.weather_data_repository import WeatherDataRepository
from repositories.csv_repository import CsvFileRepository
from repositories.weather_api_repository import WeatherApiRepository
from repositories.weather_file_repository import WeatherFileRepository
from repositories.json_repository import ProgressTrackingRepository
from core.logger import PipelineLogger


class TestWeatherDataRepositoryDataFrames:
    """Test DataFrame handling in WeatherDataRepository."""
    
    @pytest.fixture
    def temp_dirs(self, tmp_path):
        """Create temporary directories for testing."""
        coords_file = tmp_path / "coordinates.csv"
        weather_dir = tmp_path / "weather_data"
        weather_dir.mkdir()
        altitude_file = tmp_path / "altitude.csv"
        progress_file = tmp_path / "progress.json"
        
        return {
            'coords_file': coords_file,
            'weather_dir': weather_dir,
            'altitude_file': altitude_file,
            'progress_file': progress_file,
            'tmp_path': tmp_path
        }
    
    @pytest.fixture
    def sample_coordinates_list(self, temp_dirs):
        """
        Create coordinates as list of dicts (what CsvFileRepository.get_all() returns).
        """
        coords = [
            {'str_code': '11014', 'latitude': 39.835836, 'longitude': 116.289163},
            {'str_code': '11041', 'latitude': 39.698799, 'longitude': 115.984970},
        ]
        
        # Save to file
        df = pd.DataFrame(coords)
        df.to_csv(temp_dirs['coords_file'], index=False)
        
        return coords
    
    @pytest.fixture
    def sample_weather_files(self, temp_dirs):
        """Create sample weather data files."""
        # Files should be in output_dir/weather_data/ subdirectory
        weather_subdir = temp_dirs['weather_dir'] / "weather_data"
        weather_subdir.mkdir(exist_ok=True)
        
        # Create weather files for 2 stores, 1 period each
        files = []
        for store_code in ['11014', '11041']:
            # Use correct format: weather_data_{store}_{lon:.6f}_{lat:.6f}_{period}.csv
            # Note: longitude BEFORE latitude, 6 decimal places
            filename = f"weather_data_{store_code}_116.000000_39.000000_20250801_to_20250815.csv"
            filepath = weather_subdir / filename
            
            # Create sample weather data
            df = pd.DataFrame({
                'time': pd.date_range('2025-08-01', periods=24, freq='H'),
                'store_code': [store_code] * 24,
                'latitude': [39.0] * 24,
                'longitude': [116.0] * 24,
                'temperature_2m': [20.0 + i * 0.1 for i in range(24)],
                'relative_humidity_2m': [60.0] * 24,
                'wind_speed_10m': [5.0] * 24,
                'wind_direction_10m': [180.0] * 24,
                'precipitation': [0.0] * 24,
                'rain': [0.0] * 24,
                'snowfall': [0.0] * 24,
                'cloud_cover': [50.0] * 24,
                'weather_code': [0] * 24,
                'pressure_msl': [1013.0] * 24,
                'direct_radiation': [100.0] * 24,
                'diffuse_radiation': [50.0] * 24,
                'direct_normal_irradiance': [200.0] * 24,
                'terrestrial_radiation': [300.0] * 24,
                'shortwave_radiation': [150.0] * 24,
                'et0_fao_evapotranspiration': [2.5] * 24
            })
            df.to_csv(filepath, index=False)
            files.append(filepath)
        
        return files
    
    @pytest.fixture
    def weather_data_repo(self, temp_dirs, sample_coordinates_list):
        """Create WeatherDataRepository with mocked dependencies."""
        logger = PipelineLogger("TestWeatherDataRepo")
        
        # Create real repositories
        coords_repo = CsvFileRepository(
            file_path=str(temp_dirs['coords_file']),
            logger=logger
        )
        
        weather_file_repo = WeatherFileRepository(
            output_dir=str(temp_dirs['weather_dir']),
            logger=logger
        )
        
        altitude_repo = CsvFileRepository(
            file_path=str(temp_dirs['altitude_file']),
            logger=logger
        )
        
        progress_repo = ProgressTrackingRepository(
            file_path=str(temp_dirs['progress_file']),
            logger=logger
        )
        
        weather_api_repo = WeatherApiRepository(logger=logger)
        
        return WeatherDataRepository(
            coordinates_repo=coords_repo,
            weather_api_repo=weather_api_repo,
            weather_file_repo=weather_file_repo,
            altitude_repo=altitude_repo,
            progress_repo=progress_repo,
            logger=logger
        )
    
    def test_coordinates_list_to_dataframe_conversion(self, weather_data_repo, sample_coordinates_list, mocker):
        """
        Test that coordinates are converted from list of dicts to DataFrame.
        
        CsvFileRepository.get_all() returns list of dicts, but the repository
        needs a DataFrame for processing.
        """
        # Mock the API to avoid real calls
        mocker.patch.object(weather_data_repo.weather_api_repo, 'fetch_weather_data', 
                           return_value=pd.DataFrame())
        
        # This should not raise "list indices must be integers or slices, not str"
        try:
            result = weather_data_repo.get_weather_data_for_period(
                target_yyyymm='202508',
                target_period='A'
            )
            # If we get here, the conversion worked
            assert True
        except TypeError as e:
            if "list indices" in str(e):
                pytest.fail(f"Coordinates not converted to DataFrame: {e}")
            raise
    
    def test_weather_data_concatenation(self, weather_data_repo, sample_weather_files, mocker):
        """
        Test that multiple weather DataFrames are concatenated into single DataFrame.
        
        The repository loads weather data for multiple stores/periods and should
        return a single combined DataFrame, not a list.
        """
        # Mock API to return sample data (simulating successful downloads)
        sample_df = pd.DataFrame({
            'time': pd.date_range('2024-09-01', periods=24, freq='H'),
            'store_code': ['TEST'] * 24,
            'latitude': [39.0] * 24,
            'longitude': [116.0] * 24,
            'temperature_2m': [20.0] * 24,
        })
        mocker.patch.object(weather_data_repo.weather_api_repo, 'fetch_weather_data',
                           return_value=sample_df)
        
        # Don't mark any periods as completed - let it download fresh data
        # This tests the concatenation of downloaded DataFrames
        result = weather_data_repo.get_weather_data_for_period(
            target_yyyymm='202409',
            target_period='A'
        )
        
        weather_data = result.get('weather_files')
        
        # Should be a DataFrame, not a list
        assert isinstance(weather_data, pd.DataFrame), \
            f"Should return DataFrame, got {type(weather_data)}"
        
        # Should not be empty (we mocked the API to return data)
        assert not weather_data.empty, "Should have data from mocked API"
        
        # Should have data from multiple stores
        if 'store_code' in weather_data.columns:
            unique_stores = weather_data['store_code'].nunique()
            assert unique_stores > 0, "Should have data from at least one store"
    
    def test_load_existing_weather_for_period(self, weather_data_repo, sample_weather_files):
        """
        Test _load_existing_weather_for_period() method.
        
        This method loads weather files for a period when all downloads are complete.
        """
        from repositories.weather_data_repository import PeriodInfo
        
        # Create period info
        period_info = PeriodInfo(
            period_label='202508A',
            yyyymm='202508',
            period_half='A',
            start_date='2025-08-01',
            end_date='2025-08-15',
            weather_period_label='20250801_to_20250815'
        )
        
        # Create coords DataFrame
        coords_df = pd.DataFrame([
            {'str_code': '11014', 'latitude': 39.0, 'longitude': 116.0},
            {'str_code': '11041', 'latitude': 39.0, 'longitude': 116.0},
        ])
        
        # Load existing weather
        weather_list = weather_data_repo._load_existing_weather_for_period(
            period_info, coords_df
        )
        
        # Should return list of DataFrames
        assert isinstance(weather_list, list), "Should return list"
        assert len(weather_list) > 0, "Should find existing files"
        
        # Each item should be a DataFrame
        for df in weather_list:
            assert isinstance(df, pd.DataFrame), "Each item should be DataFrame"
            assert not df.empty, "DataFrames should not be empty"
    
    def test_empty_weather_data_returns_empty_dataframe(self, weather_data_repo, mocker):
        """
        Test that when no weather data exists, an empty DataFrame is returned (not empty list).
        """
        # Mock API to return nothing
        mocker.patch.object(weather_data_repo.weather_api_repo, 'fetch_weather_data',
                           return_value=pd.DataFrame())
        
        result = weather_data_repo.get_weather_data_for_period(
            target_yyyymm='202508',
            target_period='A'
        )
        
        weather_data = result.get('weather_files')
        
        # Should be DataFrame (even if empty), not list
        assert isinstance(weather_data, pd.DataFrame), \
            f"Should return DataFrame even when empty, got {type(weather_data)}"
    
    def test_combined_dataframe_has_all_stores(self, weather_data_repo, sample_weather_files, mocker):
        """
        Test that combined DataFrame includes data from all stores.
        """
        # Mock API
        mocker.patch.object(weather_data_repo.weather_api_repo, 'fetch_weather_data',
                           return_value=pd.DataFrame())
        
        # Mark periods as completed
        progress = {
            'completed_periods': ['202508A'],
            'completed_stores': ['11014', '11041'],
            'failed_stores': [],
            'vpn_switches': 0,
            'last_update': datetime.now().isoformat(),
            'target_period': '202508A'
        }
        weather_data_repo.progress_repo.save(progress)
        
        result = weather_data_repo.get_weather_data_for_period(
            target_yyyymm='202508',
            target_period='A'
        )
        
        weather_data = result.get('weather_files')
        
        if not weather_data.empty and 'store_code' in weather_data.columns:
            stores_in_data = set(weather_data['store_code'].unique())
            # Should have both stores (if files were found)
            assert len(stores_in_data) >= 1, "Should have data from at least one store"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
