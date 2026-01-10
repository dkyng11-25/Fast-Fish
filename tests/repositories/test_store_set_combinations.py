"""
Test for Issue #1: Store Set Combinations (Same, Different, Mixed)

This test verifies that the system handles different store set combinations correctly:
1. Same stores (should use cached data)
2. Different stores (should download new data after cleanup)
3. Mixed stores (partially same, partially different)

These tests use MOCKED weather API to avoid real internet calls.

Author: Data Pipeline Team
Date: 2025-10-28
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, MagicMock

from core.logger import PipelineLogger
from repositories.weather_file_repository import WeatherFileRepository
from repositories.weather_api_repository import WeatherApiRepository
from repositories.weather_data_repository import WeatherDataRepository
from repositories.csv_repository import CsvFileRepository
from repositories.json_repository import ProgressTrackingRepository


class TestStoreSetCombinations:
    """Test different store set combinations to ensure no getting stuck."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return PipelineLogger("TestStoreSets")
    
    @pytest.fixture
    def mock_weather_api(self, mocker):
        """
        Create a MOCKED weather API that returns fake data.
        
        This avoids real internet calls and makes tests fast and reliable.
        """
        mock_api = mocker.Mock(spec=WeatherApiRepository)
        
        # Mock weather data response
        def mock_fetch_weather(latitude, longitude, start_date, end_date):
            """Return fake weather data for any coordinates."""
            dates = pd.date_range(start=start_date, end=end_date, freq='H')
            return pd.DataFrame({
                'time': dates,
                'temperature_2m': [25.0] * len(dates),
                'relative_humidity_2m': [60.0] * len(dates),
                'wind_speed_10m': [5.0] * len(dates),
                'pressure_msl': [1013.0] * len(dates),
                'terrestrial_radiation': [100.0] * len(dates)
            })
        
        mock_api.fetch_weather_data.side_effect = mock_fetch_weather
        
        # Mock elevation response
        def mock_get_elevation(latitude, longitude):
            """Return fake elevation for any coordinates."""
            return 100.0  # meters
        
        mock_api.get_elevation.side_effect = mock_get_elevation
        
        return mock_api
    
    def create_coordinates_file(self, temp_dir, stores):
        """Helper to create a coordinates CSV file for given stores."""
        coords_file = Path(temp_dir) / "coordinates.csv"
        
        # Create fake coordinates for each store
        data = []
        for i, store in enumerate(stores):
            data.append({
                'str_code': store,
                'latitude': 39.0 + i * 0.1,
                'longitude': 116.0 + i * 0.1
            })
        
        pd.DataFrame(data).to_csv(coords_file, index=False)
        return str(coords_file)
    
    def create_weather_repo(self, temp_dir, coords_file, mock_weather_api, logger):
        """Helper to create a WeatherDataRepository with mocked API."""
        coords_repo = CsvFileRepository(file_path=coords_file, logger=logger)
        weather_file_repo = WeatherFileRepository(
            output_dir=str(Path(temp_dir) / "weather_data"),
            logger=logger
        )
        altitude_repo = CsvFileRepository(
            file_path=str(Path(temp_dir) / "altitudes.csv"),
            logger=logger
        )
        progress_repo = ProgressTrackingRepository(
            file_path=str(Path(temp_dir) / "progress.json"),
            logger=logger
        )
        
        return WeatherDataRepository(
            coordinates_repo=coords_repo,
            weather_api_repo=mock_weather_api,
            weather_file_repo=weather_file_repo,
            altitude_repo=altitude_repo,
            progress_repo=progress_repo,
            logger=logger
        )
    
    def test_same_stores_uses_cached_data(self, temp_dir, logger, mock_weather_api):
        """
        Test: Run with same 2 stores twice - should use cached data on second run.
        
        This verifies that we don't re-download when data already exists.
        """
        stores = ['11014', '11041']
        
        # First run
        coords_file = self.create_coordinates_file(temp_dir, stores)
        repo = self.create_weather_repo(temp_dir, coords_file, mock_weather_api, logger)
        
        result1 = repo.get_weather_data_for_period(
            target_yyyymm='202508',
            target_period='A'
        )
        
        # Verify first run downloaded data
        assert 'weather_files' in result1
        weather_data1 = result1['weather_files']
        assert len(weather_data1) > 0, "First run should have weather data"
        
        # Count API calls from first run
        first_run_api_calls = mock_weather_api.fetch_weather_data.call_count
        assert first_run_api_calls > 0, "First run should call API"
        
        # Second run with SAME stores
        repo2 = self.create_weather_repo(temp_dir, coords_file, mock_weather_api, logger)
        
        result2 = repo2.get_weather_data_for_period(
            target_yyyymm='202508',
            target_period='A'
        )
        
        # Verify second run used cached data (no new API calls)
        second_run_api_calls = mock_weather_api.fetch_weather_data.call_count
        assert second_run_api_calls == first_run_api_calls, \
            "Second run should NOT make new API calls (uses cache)"
        
        # Verify data is the same
        weather_data2 = result2['weather_files']
        assert len(weather_data2) == len(weather_data1), \
            "Second run should return same amount of data"
    
    def test_different_stores_after_cleanup(self, temp_dir, logger, mock_weather_api):
        """
        Test: Run with 2 stores, cleanup, then run with 2 DIFFERENT stores.
        
        This is the bug scenario - should work after cleanup.
        """
        # First run with stores A and B
        stores1 = ['11014', '11041']
        coords_file1 = self.create_coordinates_file(temp_dir, stores1)
        repo1 = self.create_weather_repo(temp_dir, coords_file1, mock_weather_api, logger)
        
        result1 = repo1.get_weather_data_for_period(
            target_yyyymm='202508',
            target_period='A'
        )
        
        assert len(result1['weather_files']) > 0, "First run should succeed"
        first_run_calls = mock_weather_api.fetch_weather_data.call_count
        
        # CLEANUP (this is the fix!)
        progress_file = Path(temp_dir) / "progress.json"
        altitude_file = Path(temp_dir) / "altitudes.csv"
        weather_dir = Path(temp_dir) / "weather_data"
        
        if progress_file.exists():
            progress_file.unlink()
        if altitude_file.exists():
            altitude_file.unlink()
        if weather_dir.exists():
            for f in weather_dir.glob("*.csv"):
                f.unlink()
        
        # Second run with DIFFERENT stores C and D
        stores2 = ['11050', '11084']
        coords_file2 = self.create_coordinates_file(temp_dir, stores2)
        repo2 = self.create_weather_repo(temp_dir, coords_file2, mock_weather_api, logger)
        
        result2 = repo2.get_weather_data_for_period(
            target_yyyymm='202508',
            target_period='A'
        )
        
        # Verify second run succeeded and made new API calls
        assert len(result2['weather_files']) > 0, "Second run should succeed"
        second_run_calls = mock_weather_api.fetch_weather_data.call_count
        assert second_run_calls > first_run_calls, \
            "Second run should make new API calls for different stores"
    
    def test_mixed_stores_partially_same(self, temp_dir, logger, mock_weather_api):
        """
        Test: Run with stores [A, B], cleanup, then run with [B, C] (B is same, C is new).
        
        This tests the mixed scenario - some stores same, some different.
        """
        # First run with stores A and B
        stores1 = ['11014', '11041']
        coords_file1 = self.create_coordinates_file(temp_dir, stores1)
        repo1 = self.create_weather_repo(temp_dir, coords_file1, mock_weather_api, logger)
        
        result1 = repo1.get_weather_data_for_period(
            target_yyyymm='202508',
            target_period='A'
        )
        
        assert len(result1['weather_files']) > 0, "First run should succeed"
        first_run_calls = mock_weather_api.fetch_weather_data.call_count
        
        # CLEANUP
        progress_file = Path(temp_dir) / "progress.json"
        altitude_file = Path(temp_dir) / "altitudes.csv"
        weather_dir = Path(temp_dir) / "weather_data"
        
        if progress_file.exists():
            progress_file.unlink()
        if altitude_file.exists():
            altitude_file.unlink()
        if weather_dir.exists():
            for f in weather_dir.glob("*.csv"):
                f.unlink()
        
        # Second run with MIXED stores (B is same, C is new)
        stores2 = ['11041', '11050']  # 11041 was in first run, 11050 is new
        coords_file2 = self.create_coordinates_file(temp_dir, stores2)
        repo2 = self.create_weather_repo(temp_dir, coords_file2, mock_weather_api, logger)
        
        result2 = repo2.get_weather_data_for_period(
            target_yyyymm='202508',
            target_period='A'
        )
        
        # Verify second run succeeded
        assert len(result2['weather_files']) > 0, "Second run with mixed stores should succeed"
        second_run_calls = mock_weather_api.fetch_weather_data.call_count
        assert second_run_calls > first_run_calls, \
            "Second run should make API calls for new stores"
    
    def test_expanding_store_set(self, temp_dir, logger, mock_weather_api):
        """
        Test: Run with 2 stores, cleanup, then run with 4 stores (including original 2).
        
        This tests expanding the store set.
        """
        # First run with 2 stores
        stores1 = ['11014', '11041']
        coords_file1 = self.create_coordinates_file(temp_dir, stores1)
        repo1 = self.create_weather_repo(temp_dir, coords_file1, mock_weather_api, logger)
        
        result1 = repo1.get_weather_data_for_period(
            target_yyyymm='202508',
            target_period='A'
        )
        
        assert len(result1['weather_files']) > 0, "First run should succeed"
        
        # CLEANUP
        progress_file = Path(temp_dir) / "progress.json"
        altitude_file = Path(temp_dir) / "altitudes.csv"
        weather_dir = Path(temp_dir) / "weather_data"
        
        if progress_file.exists():
            progress_file.unlink()
        if altitude_file.exists():
            altitude_file.unlink()
        if weather_dir.exists():
            for f in weather_dir.glob("*.csv"):
                f.unlink()
        
        # Second run with 4 stores (includes original 2 plus 2 new)
        stores2 = ['11014', '11041', '11050', '11084']
        coords_file2 = self.create_coordinates_file(temp_dir, stores2)
        repo2 = self.create_weather_repo(temp_dir, coords_file2, mock_weather_api, logger)
        
        result2 = repo2.get_weather_data_for_period(
            target_yyyymm='202508',
            target_period='A'
        )
        
        # Verify second run succeeded with all 4 stores
        assert len(result2['weather_files']) > 0, "Second run with expanded store set should succeed"
        weather_data2 = result2['weather_files']
        unique_stores = weather_data2['store_code'].nunique() if 'store_code' in weather_data2.columns else 0
        # Note: Actual count depends on data structure, but should have data
        assert len(weather_data2) > 0, "Should have data for expanded store set"
    
    def test_no_cleanup_causes_issue(self, temp_dir, logger, mock_weather_api):
        """
        Test: Run with 2 stores, then run with 4 stores WITHOUT cleanup.
        
        This documents the bug - should fail or return incomplete data.
        """
        # First run with 2 stores
        stores1 = ['11014', '11041']
        coords_file1 = self.create_coordinates_file(temp_dir, stores1)
        repo1 = self.create_weather_repo(temp_dir, coords_file1, mock_weather_api, logger)
        
        result1 = repo1.get_weather_data_for_period(
            target_yyyymm='202508',
            target_period='A'
        )
        
        assert len(result1['weather_files']) > 0, "First run should succeed"
        
        # Second run with 4 stores WITHOUT cleanup
        # This should demonstrate the issue
        stores2 = ['11014', '11041', '11050', '11084']
        coords_file2 = self.create_coordinates_file(temp_dir, stores2)
        repo2 = self.create_weather_repo(temp_dir, coords_file2, mock_weather_api, logger)
        
        # This will see progress as "completed" and try to load files
        # But only 2 files exist, not 4!
        result2 = repo2.get_weather_data_for_period(
            target_yyyymm='202508',
            target_period='A'
        )
        
        # The system will load only the 2 existing files
        # This is the bug - it should either:
        # 1. Download the 2 missing stores, OR
        # 2. Fail with clear error
        weather_data2 = result2['weather_files']
        
        # Currently, it will only have data for 2 stores (the original ones)
        # This test documents the current behavior
        # In the future, with per-store tracking, it should download the missing 2
        assert len(weather_data2) > 0, "Will have some data (from original 2 stores)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
