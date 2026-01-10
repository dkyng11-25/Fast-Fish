#!/usr/bin/env python3
"""
Test: Verify Weather Data Repository Doesn't Load Duplicate Records

This test ensures that when loading existing weather files, the repository
only loads files for the REQUESTED periods, not all files in the directory.

Created: 2025-10-28
Purpose: Prevent duplicate data bug (Issue: loaded 2x data causing wrong temperatures)
"""

import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from repositories.weather_data_repository import WeatherDataRepository, PeriodInfo
from repositories.csv_repository import CsvFileRepository
from repositories.weather_api_repository import WeatherApiRepository
from repositories.weather_file_repository import WeatherFileRepository
from repositories.json_repository import ProgressTrackingRepository
from core.logger import PipelineLogger


class TestWeatherDataNoDuplicates:
    """Test that weather data repository doesn't load duplicate records."""
    
    @pytest.fixture
    def temp_dirs(self, tmp_path):
        """Create temporary directories for testing."""
        coords_file = tmp_path / "coordinates.csv"
        weather_dir = tmp_path / "weather_data"
        weather_dir.mkdir()
        (weather_dir / "weather_data").mkdir()  # Subdirectory for actual files
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
    def sample_coordinates(self, temp_dirs):
        """Create sample coordinates file."""
        coords = pd.DataFrame([
            {'str_code': '11014', 'latitude': 39.835836, 'longitude': 116.289163},
            {'str_code': '11041', 'latitude': 39.698799, 'longitude': 115.984970},
        ])
        coords.to_csv(temp_dirs['coords_file'], index=False)
        return coords
    
    @pytest.fixture
    def weather_files_multiple_periods(self, temp_dirs):
        """
        Create weather files for MULTIPLE periods to simulate:
        - Current run: 3 periods (Sep, Oct, Nov 2024)
        - Previous run: 3 periods (Jun, Jul, Aug 2024) - should NOT be loaded!
        """
        weather_subdir = temp_dirs['weather_dir'] / "weather_data"
        
        # Create files for CURRENT periods (should be loaded)
        current_periods = [
            ('202409A', '20240901_to_20240915'),
            ('202410A', '20241001_to_20241015'),
            ('202411A', '20241101_to_20241115'),
        ]
        
        # Create files for PREVIOUS periods (should NOT be loaded)
        previous_periods = [
            ('202406A', '20240601_to_20240615'),
            ('202407A', '20240701_to_20240715'),
            ('202408A', '20240801_to_20240815'),
        ]
        
        all_files = []
        
        # Create current period files
        store_coords = {
            '11014': (116.289163, 39.835836),
            '11041': (115.984970, 39.698799),
        }
        
        for period_label, weather_label in current_periods:
            for store_code, (lon, lat) in store_coords.items():
                filename = f"weather_data_{store_code}_{lon:.6f}_{lat:.6f}_{weather_label}.csv"
                filepath = weather_subdir / filename
                
                # Create sample data (10 records per file)
                df = pd.DataFrame({
                    'time': pd.date_range('2024-09-01', periods=10, freq='H'),
                    'store_code': [store_code] * 10,
                    'temperature_2m': [20.0] * 10,
                })
                df.to_csv(filepath, index=False)
                all_files.append(filepath)
        
        # Create previous period files (these should NOT be loaded!)
        for period_label, weather_label in previous_periods:
            for store_code, (lon, lat) in store_coords.items():
                filename = f"weather_data_{store_code}_{lon:.6f}_{lat:.6f}_{weather_label}.csv"
                filepath = weather_subdir / filename
                
                # Create sample data (10 records per file)
                df = pd.DataFrame({
                    'time': pd.date_range('2024-06-01', periods=10, freq='H'),
                    'store_code': [store_code] * 10,
                    'temperature_2m': [25.0] * 10,  # Different temperature to detect if loaded
                })
                df.to_csv(filepath, index=False)
                all_files.append(filepath)
        
        return {
            'current_files': 6,  # 3 periods × 2 stores
            'previous_files': 6,  # 3 periods × 2 stores
            'total_files': 12,
            'expected_records_if_correct': 60,  # 6 files × 10 records
            'expected_records_if_bug': 120,  # 12 files × 10 records (BUG!)
        }
    
    @pytest.fixture
    def weather_data_repo(self, temp_dirs, sample_coordinates):
        """Create WeatherDataRepository with mocked dependencies."""
        logger = PipelineLogger("TestWeatherDataRepo")
        
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
    
    def test_only_loads_requested_periods_not_all_files(
        self, weather_data_repo, weather_files_multiple_periods, mocker
    ):
        """
        CRITICAL TEST: Verify repository only loads files for REQUESTED periods.
        
        Bug: Repository was loading ALL CSV files in directory with glob("*.csv")
        Fix: Repository should only load files for the specific periods requested
        
        Test Setup:
        - 12 files total in directory (6 current + 6 previous)
        - Request only 3 current periods
        - Should load ONLY 6 files (not all 12!)
        """
        # Mock API to avoid real calls
        mocker.patch.object(weather_data_repo.weather_api_repo, 'fetch_weather_data',
                           return_value=pd.DataFrame())
        
        # Mark all CURRENT periods as completed
        from datetime import datetime
        progress = {
            'completed_periods': ['202409A', '202410A', '202411A'],
            'completed_stores': ['11014', '11041'],
            'failed_stores': [],
            'vpn_switches': 0,
            'last_update': datetime.now().isoformat(),
            'target_period': '202409A'
        }
        weather_data_repo.progress_repo.save(progress)
        
        # Request weather data for target period
        # SINGLE PERIOD DESIGN: This should generate 1 period and load ONLY those 2 files
        result = weather_data_repo.get_weather_data_for_period(
            target_yyyymm='202409',
            target_period='A'
        )
        
        weather_data = result.get('weather_files')
        
        # Verify it's a DataFrame
        assert isinstance(weather_data, pd.DataFrame), \
            f"Should return DataFrame, got {type(weather_data)}"
        
        # CRITICAL CHECK: Should have 20 records (2 files × 10 records) for SINGLE period
        # NOT 120 records (12 files × 10 records) which would indicate loading all files!
        # SINGLE PERIOD DESIGN: Only loads the requested period (202409A)
        expected_records = 20  # 2 stores × 10 records per file
        buggy_records = weather_files_multiple_periods['expected_records_if_bug']
        
        assert len(weather_data) == expected_records, \
            f"BUG DETECTED! Loaded {len(weather_data)} records. " \
            f"Expected {expected_records} (single period) but got {buggy_records} (bug: loading all files!)"
        
        # Verify we're loading the correct period data
        # Target period (202409A) has temperature=20.0
        # Previous periods had temperature=25.0
        if len(weather_data) > 0:
            avg_temp = weather_data['temperature_2m'].mean()
            assert avg_temp == 20.0, \
                f"Loaded wrong period data! Average temp {avg_temp}°C (expected 20.0°C for 202409A)"
    
    def test_load_existing_weather_for_period_only_loads_specific_period(
        self, weather_data_repo, weather_files_multiple_periods
    ):
        """
        Test the _load_existing_weather_for_period() helper method.
        
        This method should load ONLY files for the specified period,
        not all files in the directory.
        """
        # Create period info for ONE period
        period_info = PeriodInfo(
            period_label='202409A',
            yyyymm='202409',
            period_half='A',
            start_date='2024-09-01',
            end_date='2024-09-15',
            weather_period_label='20240901_to_20240915'
        )
        
        # Create coords DataFrame
        coords_df = pd.DataFrame([
            {'str_code': '11014', 'latitude': 39.835836, 'longitude': 116.289163},
            {'str_code': '11041', 'latitude': 39.698799, 'longitude': 115.984970},
        ])
        
        # Load weather for this ONE period
        weather_list = weather_data_repo._load_existing_weather_for_period(
            period_info, coords_df
        )
        
        # Should return list of DataFrames
        assert isinstance(weather_list, list), "Should return list"
        
        # Should load ONLY 2 files (1 period × 2 stores)
        assert len(weather_list) == 2, \
            f"Should load 2 files for 1 period, got {len(weather_list)}"
        
        # Each DataFrame should have 10 records
        for df in weather_list:
            assert isinstance(df, pd.DataFrame), "Each item should be DataFrame"
            assert len(df) == 10, f"Each file should have 10 records, got {len(df)}"
            assert df['temperature_2m'].mean() == 20.0, \
                "Should load current period data (temp=20.0), not previous (temp=25.0)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
