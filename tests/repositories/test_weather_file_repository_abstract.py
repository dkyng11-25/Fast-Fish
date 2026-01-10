#!/usr/bin/env python3
"""
Tests for WeatherFileRepository Abstract Method Implementations

Tests that the repository can be instantiated and that the abstract methods
from the base Repository class are properly implemented.

Created: 2025-10-27
Purpose: Verify Fix #2 - Abstract method implementations
"""

import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from repositories.weather_file_repository import WeatherFileRepository
from core.logger import PipelineLogger


class TestWeatherFileRepositoryAbstractMethods:
    """Test abstract method implementations."""
    
    @pytest.fixture
    def weather_repo(self, tmp_path):
        """Create WeatherFileRepository instance."""
        logger = PipelineLogger("TestWeatherRepo")
        return WeatherFileRepository(
            output_dir=str(tmp_path / "weather_data"),
            logger=logger
        )
    
    def test_repository_can_be_instantiated(self, tmp_path):
        """
        Test that WeatherFileRepository can be instantiated.
        
        This would fail if abstract methods were not implemented.
        """
        logger = PipelineLogger("TestWeatherRepo")
        
        # Should not raise TypeError about abstract methods
        repo = WeatherFileRepository(
            output_dir=str(tmp_path / "weather_data"),
            logger=logger
        )
        
        assert repo is not None
        assert isinstance(repo, WeatherFileRepository)
    
    def test_get_all_returns_empty_dataframe(self, weather_repo):
        """
        Test that get_all() returns an empty DataFrame.
        
        This method is not applicable for weather file repository
        (weather data is accessed per store/period, not as a single dataset).
        """
        result = weather_repo.get_all()
        
        assert isinstance(result, pd.DataFrame), "Should return DataFrame"
        assert result.empty, "Should return empty DataFrame"
        assert len(result) == 0, "Should have no rows"
    
    def test_get_all_logs_warning(self, weather_repo, caplog):
        """Test that get_all() logs a warning about not being applicable."""
        import logging
        caplog.set_level(logging.WARNING)
        
        weather_repo.get_all()
        
        # Check that warning was logged
        assert any("not applicable" in record.message.lower() 
                  for record in caplog.records), \
            "Should log warning about get_all() not being applicable"
    
    def test_save_does_not_raise_error(self, weather_repo):
        """
        Test that save() can be called without raising an error.
        
        This method is not applicable for weather file repository
        (use save_weather_file() instead).
        """
        dummy_data = pd.DataFrame({'col1': [1, 2, 3]})
        
        # Should not raise an error
        try:
            weather_repo.save(dummy_data)
        except Exception as e:
            pytest.fail(f"save() should not raise error, got: {e}")
    
    def test_save_logs_warning(self, weather_repo, caplog):
        """Test that save() logs a warning about not being applicable."""
        import logging
        caplog.set_level(logging.WARNING)
        
        dummy_data = pd.DataFrame({'col1': [1, 2, 3]})
        weather_repo.save(dummy_data)
        
        # Check that warning was logged
        assert any("not applicable" in record.message.lower() 
                  for record in caplog.records), \
            "Should log warning about save() not being applicable"
        
        assert any("save_weather_file" in record.message.lower() 
                  for record in caplog.records), \
            "Should suggest using save_weather_file() instead"
    
    def test_repository_has_proper_methods(self, weather_repo):
        """Test that repository has the expected public methods."""
        # Should have the weather-specific methods
        assert hasattr(weather_repo, 'save_weather_file'), \
            "Should have save_weather_file() method"
        assert hasattr(weather_repo, 'load_weather_file'), \
            "Should have load_weather_file() method"
        assert hasattr(weather_repo, 'get_downloaded_stores_for_period'), \
            "Should have get_downloaded_stores_for_period() method"
        
        # Should have the abstract methods (even if not applicable)
        assert hasattr(weather_repo, 'get_all'), \
            "Should have get_all() method"
        assert hasattr(weather_repo, 'save'), \
            "Should have save() method"
    
    def test_get_all_is_callable(self, weather_repo):
        """Test that get_all() is callable."""
        assert callable(weather_repo.get_all), \
            "get_all() should be callable"
    
    def test_save_is_callable(self, weather_repo):
        """Test that save() is callable."""
        assert callable(weather_repo.save), \
            "save() should be callable"
    
    def test_abstract_methods_dont_break_inheritance(self, tmp_path):
        """
        Test that implementing abstract methods doesn't break inheritance.
        
        The repository should still work as a Repository subclass.
        """
        from repositories.base import Repository
        
        logger = PipelineLogger("TestWeatherRepo")
        repo = WeatherFileRepository(
            output_dir=str(tmp_path / "weather_data"),
            logger=logger
        )
        
        # Should be instance of base Repository
        assert isinstance(repo, Repository), \
            "Should be instance of Repository base class"
    
    def test_multiple_instantiations(self, tmp_path):
        """
        Test that multiple instances can be created.
        
        This ensures the abstract method implementations don't cause
        issues with multiple instantiations.
        """
        logger = PipelineLogger("TestWeatherRepo")
        
        repo1 = WeatherFileRepository(
            output_dir=str(tmp_path / "weather_data_1"),
            logger=logger
        )
        
        repo2 = WeatherFileRepository(
            output_dir=str(tmp_path / "weather_data_2"),
            logger=logger
        )
        
        assert repo1 is not repo2
        assert repo1.weather_dir != repo2.weather_dir


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
