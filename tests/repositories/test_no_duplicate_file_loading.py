#!/usr/bin/env python3
"""
Simple Test: Verify _load_existing_weather_for_period Only Loads Requested Period

This test verifies the fix for the duplicate data bug where the repository
was loading ALL files in the directory instead of just the requested period.

Created: 2025-10-28
Bug: Repository loaded 2x data causing 8°C temperature difference
Fix: Use _load_existing_weather_for_period() to load only specific periods
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


def test_load_existing_weather_for_period_filters_by_period(tmp_path):
    """
    CRITICAL TEST: Verify _load_existing_weather_for_period() only loads files
    for the SPECIFIC period requested, not all files in directory.
    
    Bug Scenario:
    - Directory has files for multiple periods (Sep, Oct, Nov)
    - Request only ONE period (Sep)
    - Should load ONLY Sep files, not all files!
    
    This is a UNIT TEST for the helper method that was fixed.
    """
    # Setup
    logger = PipelineLogger("Test")
    
    # Create temp directories
    coords_file = tmp_path / "coordinates.csv"
    weather_dir = tmp_path / "weather_data"
    weather_dir.mkdir()
    weather_subdir = weather_dir / "weather_data"
    weather_subdir.mkdir()
    
    # Create coordinates
    coords_df = pd.DataFrame([
        {'str_code': '11014', 'latitude': 39.835836, 'longitude': 116.289163},
        {'str_code': '11041', 'latitude': 39.698799, 'longitude': 115.984970},
    ])
    coords_df.to_csv(coords_file, index=False)
    
    # Create weather files for MULTIPLE periods
    # Period 1: Sep (should be loaded)
    for store_code, lat, lon in [('11014', 39.835836, 116.289163), ('11041', 39.698799, 115.984970)]:
        df_sep = pd.DataFrame({
            'time': pd.date_range('2024-09-01', periods=10, freq='H'),
            'store_code': [store_code] * 10,
            'temperature_2m': [20.0] * 10,  # Sep temp
        })
        filename_sep = f"weather_data_{store_code}_{lon:.6f}_{lat:.6f}_20240901_to_20240915.csv"
        df_sep.to_csv(weather_subdir / filename_sep, index=False)
    
    # Period 2: Oct (should NOT be loaded)
    for store_code, lat, lon in [('11014', 39.835836, 116.289163), ('11041', 39.698799, 115.984970)]:
        df_oct = pd.DataFrame({
            'time': pd.date_range('2024-10-01', periods=10, freq='H'),
            'store_code': [store_code] * 10,
            'temperature_2m': [15.0] * 10,  # Oct temp (different!)
        })
        filename_oct = f"weather_data_{store_code}_{lon:.6f}_{lat:.6f}_20241001_to_20241015.csv"
        df_oct.to_csv(weather_subdir / filename_oct, index=False)
    
    # Period 3: Nov (should NOT be loaded)
    for store_code, lat, lon in [('11014', 39.835836, 116.289163), ('11041', 39.698799, 115.984970)]:
        df_nov = pd.DataFrame({
            'time': pd.date_range('2024-11-01', periods=10, freq='H'),
            'store_code': [store_code] * 10,
            'temperature_2m': [10.0] * 10,  # Nov temp (different!)
        })
        filename_nov = f"weather_data_{store_code}_{lon:.6f}_{lat:.6f}_20241101_to_20241115.csv"
        df_nov.to_csv(weather_subdir / filename_nov, index=False)
    
    # Create repository
    weather_file_repo = WeatherFileRepository(
        output_dir=str(weather_dir),
        logger=logger
    )
    
    coords_repo = CsvFileRepository(file_path=str(coords_file), logger=logger)
    altitude_repo = CsvFileRepository(file_path=str(tmp_path / "altitude.csv"), logger=logger)
    progress_repo = ProgressTrackingRepository(file_path=str(tmp_path / "progress.json"), logger=logger)
    weather_api_repo = WeatherApiRepository(logger=logger)
    
    repo = WeatherDataRepository(
        coordinates_repo=coords_repo,
        weather_api_repo=weather_api_repo,
        weather_file_repo=weather_file_repo,
        altitude_repo=altitude_repo,
        progress_repo=progress_repo,
        logger=logger
    )
    
    # Test: Load ONLY September period
    period_info_sep = PeriodInfo(
        period_label='202409A',
        yyyymm='202409',
        period_half='A',
        start_date='2024-09-01',
        end_date='2024-09-15',
        weather_period_label='20240901_to_20240915'
    )
    
    # Call the method
    weather_list = repo._load_existing_weather_for_period(period_info_sep, coords_df)
    
    # Assertions
    assert len(weather_list) == 2, \
        f"Should load 2 files (1 period × 2 stores), got {len(weather_list)}"
    
    # Verify we loaded the RIGHT period (Sep, temp=20.0)
    # NOT Oct (temp=15.0) or Nov (temp=10.0)
    for df in weather_list:
        assert len(df) == 10, f"Each file should have 10 records"
        avg_temp = df['temperature_2m'].mean()
        assert avg_temp == 20.0, \
            f"Should load Sep data (temp=20.0), got temp={avg_temp}. " \
            f"This means it loaded wrong period!"
    
    # Verify total records
    total_records = sum(len(df) for df in weather_list)
    assert total_records == 20, \
        f"Should have 20 total records (2 files × 10 records), got {total_records}"
    
    print("✅ TEST PASSED: Only loaded requested period, not all files!")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
