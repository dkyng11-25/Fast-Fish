"""
Test for Issue #2: No Nested Directory Structure

This test verifies that weather files are saved to the correct location
without creating nested weather_data/weather_data/ directories.

Issue: Files were being saved to output/weather_data/weather_data/
Fix: Files now save to output/weather_data/ directly

Author: Data Pipeline Team
Date: 2025-10-28
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import pandas as pd

from core.logger import PipelineLogger
from repositories.weather_file_repository import WeatherFileRepository


class TestNoNestedDirectories:
    """Test that weather files are saved without nested directory structure."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return PipelineLogger("TestNoNested")
    
    def test_no_nested_weather_data_directory(self, temp_dir, logger):
        """
        Test that WeatherFileRepository does NOT create nested weather_data folders.
        
        Issue: Repository was creating output/weather_data/weather_data/
        Expected: Repository should use output/weather_data/ directly
        """
        # Create repository with output_dir that already includes "weather_data"
        output_dir = Path(temp_dir) / "output" / "weather_data"
        repo = WeatherFileRepository(
            output_dir=str(output_dir),
            logger=logger
        )
        
        # Verify the weather_dir is the same as output_dir (no nesting)
        assert repo.weather_dir == output_dir, \
            f"weather_dir should equal output_dir, got {repo.weather_dir}"
        
        # Verify no nested "weather_data" folder was created
        nested_dir = output_dir / "weather_data"
        assert not nested_dir.exists(), \
            f"Nested weather_data directory should NOT exist: {nested_dir}"
    
    def test_files_saved_to_correct_location(self, temp_dir, logger):
        """
        Test that weather files are saved to the correct location without nesting.
        
        Files should be saved to: output/weather_data/weather_data_*.csv
        NOT to: output/weather_data/weather_data/weather_data_*.csv
        """
        # Setup
        output_dir = Path(temp_dir) / "output" / "weather_data"
        repo = WeatherFileRepository(
            output_dir=str(output_dir),
            logger=logger
        )
        
        # Create test weather data
        weather_df = pd.DataFrame({
            'time': ['2025-08-01 00:00:00'],
            'temperature_2m': [25.0],
            'relative_humidity_2m': [60.0],
            'wind_speed_10m': [5.0],
            'pressure_msl': [1013.0],
            'terrestrial_radiation': [100.0]
        })
        
        # Save file
        store_code = "11014"
        latitude = 39.835836
        longitude = 116.289163
        period_label = "20250801_to_20250815"
        
        repo.save_weather_file(
            weather_df=weather_df,
            store_code=store_code,
            latitude=latitude,
            longitude=longitude,
            period_label=period_label
        )
        
        # Verify file is in correct location (not nested)
        expected_file = output_dir / f"weather_data_{store_code}_{longitude}_{latitude}_{period_label}.csv"
        assert expected_file.exists(), \
            f"File should exist at {expected_file}"
        
        # Verify file is NOT in nested location
        nested_dir = output_dir / "weather_data"
        nested_file = nested_dir / f"weather_data_{store_code}_{longitude}_{latitude}_{period_label}.csv"
        assert not nested_file.exists(), \
            f"File should NOT exist in nested location: {nested_file}"
    
    def test_directory_structure_is_flat(self, temp_dir, logger):
        """
        Test that the directory structure is flat (no subdirectories).
        
        Expected structure:
        output/
          weather_data/
            weather_data_11014_*.csv
            weather_data_11041_*.csv
        
        NOT:
        output/
          weather_data/
            weather_data/  ← This should NOT exist
              weather_data_11014_*.csv
        """
        # Setup
        output_dir = Path(temp_dir) / "output" / "weather_data"
        repo = WeatherFileRepository(
            output_dir=str(output_dir),
            logger=logger
        )
        
        # Save multiple files
        weather_df = pd.DataFrame({
            'time': ['2025-08-01 00:00:00'],
            'temperature_2m': [25.0],
            'relative_humidity_2m': [60.0],
            'wind_speed_10m': [5.0],
            'pressure_msl': [1013.0],
            'terrestrial_radiation': [100.0]
        })
        
        stores = [
            ("11014", 39.835836, 116.289163),
            ("11041", 39.698799, 115.984970),
            ("11050", 40.123456, 116.456789)
        ]
        
        for store_code, lat, lon in stores:
            repo.save_weather_file(
                weather_df=weather_df,
                store_code=store_code,
                latitude=lat,
                longitude=lon,
                period_label="20250801_to_20250815"
            )
        
        # Verify all files are in output_dir (not nested)
        files_in_output = list(output_dir.glob("weather_data_*.csv"))
        assert len(files_in_output) == 3, \
            f"Should have 3 files in {output_dir}, found {len(files_in_output)}"
        
        # Verify no nested weather_data directory exists
        nested_dir = output_dir / "weather_data"
        assert not nested_dir.exists(), \
            f"Nested directory should NOT exist: {nested_dir}"
        
        # Verify no subdirectories exist at all
        subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) == 0, \
            f"No subdirectories should exist in {output_dir}, found: {subdirs}"
    
    def test_repository_initialization_path(self, temp_dir, logger):
        """
        Test that repository correctly interprets the output_dir parameter.
        
        When factory passes "output/weather_data", repository should use it as-is,
        not add another "weather_data" folder.
        """
        # Test with path that already includes "weather_data"
        output_dir = Path(temp_dir) / "output" / "weather_data"
        repo = WeatherFileRepository(
            output_dir=str(output_dir),
            logger=logger
        )
        
        # weather_dir should be the same as output_dir
        assert repo.weather_dir == output_dir, \
            "weather_dir should equal output_dir (no additional nesting)"
        
        # output_dir should also equal weather_dir
        assert repo.output_dir == output_dir, \
            "output_dir should equal weather_dir"
        
        # They should be the exact same Path object
        assert repo.weather_dir == repo.output_dir, \
            "weather_dir and output_dir should be identical"


class TestDirectoryNamingRegression:
    """Regression tests to prevent nested directory bug from returning."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return PipelineLogger("TestRegression")
    
    def test_bug_does_not_return_with_weather_data_in_path(self, temp_dir, logger):
        """
        Regression test: Ensure bug doesn't return when path contains 'weather_data'.
        
        The original bug occurred because:
        1. Factory passed output_dir="output/weather_data"
        2. Repository added another "weather_data" folder
        3. Result: output/weather_data/weather_data/
        
        This test ensures the bug is fixed and doesn't return.
        """
        # This is how the factory calls it
        output_dir = Path(temp_dir) / "output" / "weather_data"
        repo = WeatherFileRepository(
            output_dir=str(output_dir),
            logger=logger
        )
        
        # The bug would create: output/weather_data/weather_data/
        buggy_nested_dir = output_dir / "weather_data"
        
        # Verify the bug is fixed
        assert not buggy_nested_dir.exists(), \
            f"BUG RETURNED! Nested directory exists: {buggy_nested_dir}"
        
        # Verify correct behavior
        assert repo.weather_dir == output_dir, \
            "Repository should use output_dir directly"
    
    def test_files_not_in_nested_location_after_save(self, temp_dir, logger):
        """
        Regression test: Verify files are NOT saved to nested location.
        
        This test saves a file and verifies it's in the correct location,
        not in a nested weather_data/weather_data/ folder.
        """
        output_dir = Path(temp_dir) / "output" / "weather_data"
        repo = WeatherFileRepository(
            output_dir=str(output_dir),
            logger=logger
        )
        
        # Save a file
        weather_df = pd.DataFrame({
            'time': ['2025-08-01 00:00:00'],
            'temperature_2m': [25.0],
            'relative_humidity_2m': [60.0],
            'wind_speed_10m': [5.0],
            'pressure_msl': [1013.0],
            'terrestrial_radiation': [100.0]
        })
        
        repo.save_weather_file(
            weather_df=weather_df,
            store_code="11014",
            latitude=39.835836,
            longitude=116.289163,
            period_label="20250801_to_20250815"
        )
        
        # Verify file is in correct location
        correct_location = output_dir / "weather_data_11014_116.289163_39.835836_20250801_to_20250815.csv"
        assert correct_location.exists(), \
            f"File should be at {correct_location}"
        
        # Verify file is NOT in buggy nested location
        buggy_nested_dir = output_dir / "weather_data"
        buggy_location = buggy_nested_dir / "weather_data_11014_116.289163_39.835836_20250801_to_20250815.csv"
        assert not buggy_location.exists(), \
            f"BUG RETURNED! File found in nested location: {buggy_location}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
