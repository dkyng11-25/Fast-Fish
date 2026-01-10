#!/usr/bin/env python3
"""
Tests for Step5Factory

Tests that the factory correctly creates Step 5 instances with all dependencies.

Created: 2025-10-27
Purpose: Verify Fix #4 - Factory repository wiring
"""

import pytest
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from factories.step5_factory import create_feels_like_temperature_step
from steps.feels_like_temperature_step import FeelsLikeTemperatureStep
from repositories.weather_data_repository import WeatherDataRepository
from repositories.weather_file_repository import WeatherFileRepository
from repositories.csv_repository import CsvFileRepository
from repositories.json_repository import ProgressTrackingRepository
from core.logger import PipelineLogger


class TestStep5Factory:
    """Test Step5Factory creates valid instances."""
    
    def test_factory_creates_step_instance(self):
        """Test that factory creates a FeelsLikeTemperatureStep instance."""
        step = create_feels_like_temperature_step(
            target_yyyymm='202508',
            target_period='A'
        )
        
        assert step is not None
        assert isinstance(step, FeelsLikeTemperatureStep)
    
    def test_factory_creates_logger_if_not_provided(self):
        """Test that factory creates a logger if none is provided."""
        step = create_feels_like_temperature_step(
            target_yyyymm='202508',
            target_period='A',
            logger=None  # Explicitly pass None
        )
        
        assert step.logger is not None
        assert isinstance(step.logger, PipelineLogger)
    
    def test_factory_uses_provided_logger(self):
        """Test that factory uses provided logger."""
        custom_logger = PipelineLogger("CustomLogger")
        
        step = create_feels_like_temperature_step(
            target_yyyymm='202508',
            target_period='A',
            logger=custom_logger
        )
        
        assert step.logger is custom_logger
    
    def test_step_has_weather_data_repository(self):
        """Test that step has WeatherDataRepository instance."""
        step = create_feels_like_temperature_step(
            target_yyyymm='202508',
            target_period='A'
        )
        
        assert hasattr(step, 'weather_data_repo')
        assert step.weather_data_repo is not None
        assert isinstance(step.weather_data_repo, WeatherDataRepository)
    
    def test_step_has_altitude_repository(self):
        """Test that step has altitude repository."""
        step = create_feels_like_temperature_step(
            target_yyyymm='202508',
            target_period='A'
        )
        
        assert hasattr(step, 'altitude_repo')
        assert step.altitude_repo is not None
        assert isinstance(step.altitude_repo, CsvFileRepository)
    
    def test_step_has_output_repository(self):
        """Test that step has output repository."""
        step = create_feels_like_temperature_step(
            target_yyyymm='202508',
            target_period='A'
        )
        
        assert hasattr(step, 'output_repo')
        assert step.output_repo is not None
        assert isinstance(step.output_repo, CsvFileRepository)
    
    def test_step_has_configuration(self):
        """Test that step has configuration object."""
        step = create_feels_like_temperature_step(
            target_yyyymm='202508',
            target_period='A'
        )
        
        assert hasattr(step, 'config')
        assert step.config is not None
        
        # Check configuration has expected attributes
        assert hasattr(step.config, 'seasonal_focus_months')
        assert hasattr(step.config, 'lookback_years')
        assert hasattr(step.config, 'temperature_band_size')
    
    def test_weather_data_repo_has_all_dependencies(self):
        """Test that WeatherDataRepository has all required dependencies."""
        step = create_feels_like_temperature_step(
            target_yyyymm='202508',
            target_period='A'
        )
        
        weather_repo = step.weather_data_repo
        
        # Should have all required repositories
        assert hasattr(weather_repo, 'coordinates_repo')
        assert hasattr(weather_repo, 'weather_api_repo')
        assert hasattr(weather_repo, 'weather_file_repo')
        assert hasattr(weather_repo, 'altitude_repo')
        assert hasattr(weather_repo, 'progress_repo')
        
        # All should be not None
        assert weather_repo.coordinates_repo is not None
        assert weather_repo.weather_api_repo is not None
        assert weather_repo.weather_file_repo is not None
        assert weather_repo.altitude_repo is not None
        assert weather_repo.progress_repo is not None
    
    def test_weather_file_repo_has_correct_output_dir(self):
        """Test that WeatherFileRepository has correct output directory."""
        step = create_feels_like_temperature_step(
            target_yyyymm='202508',
            target_period='A'
        )
        
        weather_file_repo = step.weather_data_repo.weather_file_repo
        
        assert isinstance(weather_file_repo, WeatherFileRepository)
        
        # Check that weather_dir is set correctly
        assert hasattr(weather_file_repo, 'weather_dir')
        # After fix: weather_dir should be "output/weather_data" (not nested)
        # Factory passes "output/weather_data", repository uses it directly
        assert 'output' in str(weather_file_repo.weather_dir)
        # weather_dir should equal output_dir (no nesting)
        assert weather_file_repo.weather_dir == weather_file_repo.output_dir
    
    def test_coordinates_repo_has_correct_file_path(self):
        """Test that coordinates repository has correct file path."""
        step = create_feels_like_temperature_step(
            target_yyyymm='202508',
            target_period='A'
        )
        
        coords_repo = step.weather_data_repo.coordinates_repo
        
        assert isinstance(coords_repo, CsvFileRepository)
        assert hasattr(coords_repo, 'file_path')
        # Should point to a coordinates file
        assert 'coordinates' in str(coords_repo.file_path).lower() or \
               'store' in str(coords_repo.file_path).lower()
    
    def test_progress_repo_has_correct_file_path(self):
        """Test that progress repository has correct file path."""
        step = create_feels_like_temperature_step(
            target_yyyymm='202508',
            target_period='A'
        )
        
        progress_repo = step.weather_data_repo.progress_repo
        
        assert isinstance(progress_repo, ProgressTrackingRepository)
        assert hasattr(progress_repo, 'file_path')
        # Should point to a JSON file
        assert str(progress_repo.file_path).endswith('.json')
    
    def test_step_has_target_period_set(self):
        """Test that step has target period set correctly."""
        step = create_feels_like_temperature_step(
            target_yyyymm='202508',
            target_period='A'
        )
        
        assert hasattr(step, 'target_yyyymm')
        assert hasattr(step, 'target_period')
        assert step.target_yyyymm == '202508'
        assert step.target_period == 'A'
    
    def test_step_has_correct_step_metadata(self):
        """Test that step has correct metadata."""
        step = create_feels_like_temperature_step(
            target_yyyymm='202508',
            target_period='A'
        )
        
        assert hasattr(step, 'step_name')
        assert hasattr(step, 'step_number')
        assert step.step_number == 5
        assert 'temperature' in step.step_name.lower() or \
               'feels' in step.step_name.lower()
    
    def test_factory_creates_different_instances(self):
        """Test that factory creates different instances each time."""
        step1 = create_feels_like_temperature_step(
            target_yyyymm='202508',
            target_period='A'
        )
        
        step2 = create_feels_like_temperature_step(
            target_yyyymm='202508',
            target_period='A'
        )
        
        assert step1 is not step2
        assert step1.weather_data_repo is not step2.weather_data_repo
    
    def test_factory_works_with_different_periods(self):
        """Test that factory works with different target periods."""
        periods = [
            ('202508', 'A'),
            ('202508', 'B'),
            ('202507', 'A'),
        ]
        
        for yyyymm, period in periods:
            step = create_feels_like_temperature_step(
                target_yyyymm=yyyymm,
                target_period=period
            )
            
            assert step.target_yyyymm == yyyymm
            assert step.target_period == period
    
    def test_configuration_has_correct_defaults(self):
        """Test that configuration has correct default values."""
        step = create_feels_like_temperature_step(
            target_yyyymm='202508',
            target_period='A'
        )
        
        config = step.config
        
        # Check expected defaults
        assert config.seasonal_focus_months == [9, 11], \
            "Should focus on September and November"
        assert config.lookback_years == 2, \
            "Should look back 2 years"
        assert config.temperature_band_size == 5, \
            "Should use 5-degree bands"
    
    def test_all_repositories_share_same_logger(self):
        """Test that all repositories share the same logger instance."""
        logger = PipelineLogger("TestLogger")
        
        step = create_feels_like_temperature_step(
            target_yyyymm='202508',
            target_period='A',
            logger=logger
        )
        
        # All repositories should use the same logger
        assert step.logger is logger
        assert step.weather_data_repo.logger is logger
        assert step.altitude_repo.logger is logger
        assert step.output_repo.logger is logger


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
