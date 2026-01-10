#!/usr/bin/env python3
"""
Test: Weather Data Repository Single Period Generation

Tests that the repository generates only ONE period per call.
This reflects the new design where multi-period downloads are handled by an orchestrator.

Created: 2025-10-28
Purpose: Ensure single-period generation logic is correct
Design: One period per call, orchestrator handles multiple periods
"""

import pytest
from datetime import date
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from repositories.weather_data_repository import WeatherDataRepository, WeatherDataConfig
from repositories.csv_repository import CsvFileRepository
from repositories.weather_api_repository import WeatherApiRepository
from repositories.weather_file_repository import WeatherFileRepository
from repositories.json_repository import ProgressTrackingRepository
from core.logger import PipelineLogger


class TestSinglePeriodGeneration:
    """Test single period generation."""
    
    @pytest.fixture
    def weather_data_repo(self, tmp_path):
        """Create minimal WeatherDataRepository for testing."""
        logger = PipelineLogger("TestSinglePeriod")
        
        # Create minimal dependencies
        coords_file = tmp_path / "coords.csv"
        coords_file.write_text("str_code,latitude,longitude\n11014,39.8,116.3\n")
        
        coords_repo = CsvFileRepository(file_path=str(coords_file), logger=logger)
        weather_file_repo = WeatherFileRepository(output_dir=str(tmp_path), logger=logger)
        altitude_repo = CsvFileRepository(file_path=str(tmp_path / "altitude.csv"), logger=logger)
        progress_repo = ProgressTrackingRepository(file_path=str(tmp_path / "progress.json"), logger=logger)
        weather_api_repo = WeatherApiRepository(logger=logger)
        
        return WeatherDataRepository(
            coordinates_repo=coords_repo,
            weather_api_repo=weather_api_repo,
            weather_file_repo=weather_file_repo,
            altitude_repo=altitude_repo,
            progress_repo=progress_repo,
            logger=logger
        )
    
    def test_generates_only_one_period(self, weather_data_repo):
        """
        Test that _generate_single_period returns exactly ONE period.
        
        This is the core design principle: one call = one period.
        """
        target_yyyymm = '202508'
        target_period = 'A'
        
        periods = weather_data_repo._generate_single_period(target_yyyymm, target_period)
        
        assert len(periods) == 1, \
            f"Should generate exactly 1 period, got {len(periods)}"
    
    def test_period_label_format(self, weather_data_repo):
        """Test that period label is formatted correctly."""
        target_yyyymm = '202508'
        target_period = 'A'
        
        periods = weather_data_repo._generate_single_period(target_yyyymm, target_period)
        
        assert periods[0].period_label == '202508A', \
            f"Period label should be '202508A', got '{periods[0].period_label}'"
    
    def test_period_A_date_range(self, weather_data_repo):
        """Test that period A covers 1st to 15th of month."""
        target_yyyymm = '202508'
        target_period = 'A'
        
        periods = weather_data_repo._generate_single_period(target_yyyymm, target_period)
        
        assert periods[0].start_date == '2025-08-01', \
            f"Period A should start on 1st, got {periods[0].start_date}"
        assert periods[0].end_date == '2025-08-15', \
            f"Period A should end on 15th, got {periods[0].end_date}"
    
    def test_period_B_date_range(self, weather_data_repo):
        """Test that period B covers 16th to end of month."""
        target_yyyymm = '202508'
        target_period = 'B'
        
        periods = weather_data_repo._generate_single_period(target_yyyymm, target_period)
        
        assert periods[0].start_date == '2025-08-16', \
            f"Period B should start on 16th, got {periods[0].start_date}"
        assert periods[0].end_date == '2025-08-31', \
            f"Period B should end on 31st (Aug has 31 days), got {periods[0].end_date}"
    
    def test_february_period_B(self, weather_data_repo):
        """Test that February period B ends on 28th/29th."""
        target_yyyymm = '202502'  # Feb 2025 (non-leap year)
        target_period = 'B'
        
        periods = weather_data_repo._generate_single_period(target_yyyymm, target_period)
        
        assert periods[0].end_date == '2025-02-28', \
            f"Feb 2025 period B should end on 28th, got {periods[0].end_date}"
    
    def test_future_period_returns_empty(self, weather_data_repo):
        """Test that future periods are skipped."""
        # Use a date far in the future
        target_yyyymm = '203001'  # January 2030
        target_period = 'A'
        
        periods = weather_data_repo._generate_single_period(target_yyyymm, target_period)
        
        assert len(periods) == 0, \
            f"Future periods should return empty list, got {len(periods)} periods"
    
    def test_weather_period_label_format(self, weather_data_repo):
        """Test that weather period label is formatted correctly."""
        target_yyyymm = '202508'
        target_period = 'A'
        
        periods = weather_data_repo._generate_single_period(target_yyyymm, target_period)
        
        expected_label = '20250801_to_20250815'
        assert periods[0].weather_period_label == expected_label, \
            f"Weather label should be '{expected_label}', got '{periods[0].weather_period_label}'"
    
    def test_multiple_calls_generate_multiple_periods(self, weather_data_repo):
        """
        Test that calling the method multiple times generates different periods.
        
        This demonstrates how an orchestrator would download multiple periods.
        """
        # Call for 3 different periods
        period1 = weather_data_repo._generate_single_period('202506', 'A')
        period2 = weather_data_repo._generate_single_period('202507', 'A')
        period3 = weather_data_repo._generate_single_period('202508', 'A')
        
        # Each call returns exactly 1 period
        assert len(period1) == 1
        assert len(period2) == 1
        assert len(period3) == 1
        
        # Periods are different
        assert period1[0].period_label == '202506A'
        assert period2[0].period_label == '202507A'
        assert period3[0].period_label == '202508A'
        
        # Total: 3 periods (from 3 calls)
        all_periods = period1 + period2 + period3
        assert len(all_periods) == 3, \
            f"3 calls should generate 3 periods total, got {len(all_periods)}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
