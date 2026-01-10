#!/usr/bin/env python3
"""
Tests for WeatherFileRepository Filename Generation

Tests that the filename format matches the OLD Step 4 format exactly.
This is critical for loading existing weather data files.

Created: 2025-10-27
Purpose: Verify Fix #1 - Filename format compatibility
"""

import pytest
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from repositories.weather_file_repository import WeatherFileRepository
from core.logger import PipelineLogger


class TestWeatherFileRepositoryFilename:
    """Test filename generation matches OLD Step 4 format."""
    
    @pytest.fixture
    def weather_repo(self, tmp_path):
        """Create WeatherFileRepository instance."""
        logger = PipelineLogger("TestWeatherRepo")
        return WeatherFileRepository(
            output_dir=str(tmp_path / "weather_data"),
            logger=logger
        )
    
    def test_filename_format_matches_old_step4(self, weather_repo):
        """
        Test that generated filename matches OLD Step 4 format exactly.
        
        OLD Step 4 format:
        weather_data_{store_code}_{longitude:.6f}_{latitude:.6f}_{period_label}.csv
        """
        store_code = "11014"
        latitude = 39.835836
        longitude = 116.289163
        period_label = "20250801_to_20250815"
        
        filename = weather_repo._generate_filename(
            store_code=store_code,
            latitude=latitude,
            longitude=longitude,
            period_label=period_label
        )
        
        expected = "weather_data_11014_116.289163_39.835836_20250801_to_20250815.csv"
        assert filename == expected, f"Expected {expected}, got {filename}"
    
    def test_coordinate_order_longitude_first(self, weather_repo):
        """Test that longitude comes before latitude in filename."""
        filename = weather_repo._generate_filename(
            store_code="TEST",
            latitude=39.0,
            longitude=116.0,
            period_label="20250101_to_20250115"
        )
        
        # Extract coordinates from filename
        parts = filename.split('_')
        # Format: weather_data_{store}_{lon}_{lat}_{period}.csv
        # parts[0] = 'weather', parts[1] = 'data', parts[2] = store
        # parts[3] = lon, parts[4] = lat
        lon_in_filename = float(parts[3])
        lat_in_filename = float(parts[4])
        
        assert lon_in_filename == 116.0, "Longitude should be first coordinate"
        assert lat_in_filename == 39.0, "Latitude should be second coordinate"
    
    def test_coordinate_precision_six_decimals(self, weather_repo):
        """Test that coordinates are formatted with 6 decimal places."""
        filename = weather_repo._generate_filename(
            store_code="TEST",
            latitude=39.123456789,  # More than 6 decimals
            longitude=116.987654321,
            period_label="20250101_to_20250115"
        )
        
        # Check that coordinates are truncated to 6 decimals
        assert "116.987654" in filename, "Longitude should have 6 decimal places"
        assert "39.123457" in filename, "Latitude should have 6 decimal places (rounded)"
    
    def test_coordinates_use_dots_not_underscores(self, weather_repo):
        """Test that coordinates use dots (.) not underscores (_)."""
        filename = weather_repo._generate_filename(
            store_code="TEST",
            latitude=39.5,
            longitude=116.5,
            period_label="20250101_to_20250115"
        )
        
        # Should contain "116.5" and "39.5", not "116_5" or "39_5"
        assert "116.5" in filename or "116.500000" in filename
        assert "39.5" in filename or "39.500000" in filename
        assert "116_5" not in filename
        assert "39_5" not in filename
    
    def test_filename_starts_with_weather_data(self, weather_repo):
        """Test that filename starts with 'weather_data_'."""
        filename = weather_repo._generate_filename(
            store_code="TEST",
            latitude=39.0,
            longitude=116.0,
            period_label="20250101_to_20250115"
        )
        
        assert filename.startswith("weather_data_"), \
            f"Filename should start with 'weather_data_', got: {filename}"
    
    def test_filename_ends_with_csv(self, weather_repo):
        """Test that filename ends with '.csv'."""
        filename = weather_repo._generate_filename(
            store_code="TEST",
            latitude=39.0,
            longitude=116.0,
            period_label="20250101_to_20250115"
        )
        
        assert filename.endswith(".csv"), \
            f"Filename should end with '.csv', got: {filename}"
    
    def test_filename_with_negative_coordinates(self, weather_repo):
        """Test filename generation with negative coordinates."""
        filename = weather_repo._generate_filename(
            store_code="TEST",
            latitude=-33.868820,  # Sydney
            longitude=151.209290,
            period_label="20250101_to_20250115"
        )
        
        # Should handle negative coordinates correctly
        assert "151.209290" in filename
        assert "-33.868820" in filename
        expected = "weather_data_TEST_151.209290_-33.868820_20250101_to_20250115.csv"
        assert filename == expected
    
    def test_filename_compatibility_with_existing_files(self, tmp_path, weather_repo):
        """
        Test that generated filenames can find existing files from OLD Step 4.
        
        This is the critical integration test - can we load files created by OLD Step 4?
        """
        # Create a file with OLD Step 4 format
        weather_dir = tmp_path / "weather_data"
        weather_dir.mkdir(exist_ok=True)
        
        old_step4_filename = "weather_data_11014_116.289163_39.835836_20240901_to_20240915.csv"
        old_file = weather_dir / old_step4_filename
        old_file.write_text("time,temperature_2m,store_code\n2024-09-01,20.5,11014\n")
        
        # Generate filename using repository
        generated_filename = weather_repo._generate_filename(
            store_code="11014",
            latitude=39.835836,
            longitude=116.289163,
            period_label="20240901_to_20240915"
        )
        
        # Should match exactly
        assert generated_filename == old_step4_filename
        
        # Should be able to find the file
        generated_path = weather_dir / generated_filename
        assert generated_path.exists(), "Generated filename should match existing file"
        assert generated_path.read_text() == old_file.read_text()
    
    def test_multiple_stores_unique_filenames(self, weather_repo):
        """Test that different stores get unique filenames."""
        stores = [
            ("11014", 39.835836, 116.289163),
            ("11041", 39.698799, 115.984970),
            ("11052", 40.123456, 117.123456),
        ]
        
        filenames = set()
        for store_code, lat, lon in stores:
            filename = weather_repo._generate_filename(
                store_code=store_code,
                latitude=lat,
                longitude=lon,
                period_label="20250101_to_20250115"
            )
            filenames.add(filename)
        
        assert len(filenames) == 3, "Each store should have unique filename"
    
    def test_same_store_different_periods_unique_filenames(self, weather_repo):
        """Test that same store with different periods gets unique filenames."""
        periods = [
            "20250101_to_20250115",
            "20250116_to_20250131",
            "20250201_to_20250215",
        ]
        
        filenames = set()
        for period in periods:
            filename = weather_repo._generate_filename(
                store_code="11014",
                latitude=39.835836,
                longitude=116.289163,
                period_label=period
            )
            filenames.add(filename)
        
        assert len(filenames) == 3, "Each period should have unique filename"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
