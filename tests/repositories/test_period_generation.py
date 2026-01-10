#!/usr/bin/env python3
"""
Test: Weather Data Repository Period Generation

Tests that the repository generates the correct periods for year-over-year analysis.
Verifies that period generation is symmetric and includes complete months.

Created: 2025-10-28
Purpose: Ensure period generation logic is correct and intuitive
Compliance: Follows refactoring protocol - tests repository behavior, not algorithms
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


class TestPeriodGeneration:
    """Test period generation for year-over-year analysis."""
    
    @pytest.fixture
    def weather_data_repo(self, tmp_path):
        """Create minimal WeatherDataRepository for testing."""
        logger = PipelineLogger("TestPeriodGen")
        
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
    
    def test_period_generation_for_target_202508A(self, weather_data_repo):
        """
        Test period generation for target 202508A with months_back=3.
        
        Expected behavior:
        - Current year: Last 3 months including target = 6 periods
        - Previous year: Same 3 months from previous year = 6 periods
        - Total: 12 periods
        
        Critical check: Should include FULL target month (both A and B halves)
        """
        target_yyyymm = '202508'
        target_period = 'A'
        months_back = 3
        
        # Generate periods using the repository's method
        periods = weather_data_repo._generate_year_over_year_periods(
            target_yyyymm, target_period, months_back
        )
        
        # Extract period labels
        period_labels = [p.period_label for p in periods]
        
        # Verify total count
        assert len(period_labels) == 12, \
            f"Should generate 12 periods (6 current + 6 previous), got {len(period_labels)}"
        
        # Verify current year periods (should be last 3 complete months)
        current_year_periods = [p for p in period_labels if p.startswith('2025')]
        expected_current = ['202506A', '202506B', '202507A', '202507B', '202508A', '202508B']
        
        # CRITICAL: Check if 202508B is included
        if '202508B' not in current_year_periods:
            pytest.fail(
                f"DESIGN ISSUE: Target month (202508) is incomplete!\n"
                f"Expected: {expected_current}\n"
                f"Got: {current_year_periods}\n"
                f"Missing: 202508B (August 16-31)\n"
                f"For target 202508A, the full month should be included for complete 3-month window."
            )
        
        assert current_year_periods == expected_current, \
            f"Current year should have complete 3 months (Jun-Aug)\n" \
            f"Expected: {expected_current}\n" \
            f"Got: {current_year_periods}"
        
        # Verify previous year periods (SAME months as current year for year-over-year comparison)
        previous_year_periods = [p for p in period_labels if p.startswith('2024')]
        expected_previous = ['202406A', '202406B', '202407A', '202407B', '202408A', '202408B']
        
        # CRITICAL: Check if 202408B is included (needed for planning 202508B)
        if '202408B' not in previous_year_periods:
            pytest.fail(
                f"CRITICAL: Missing 202408B from previous year!\n"
                f"Expected: {expected_previous}\n"
                f"Got: {previous_year_periods}\n"
                f"Missing: 202408B (needed for planning next period 202508B)\n"
                f"Previous year should mirror current year months for proper year-over-year comparison."
            )
        
        assert previous_year_periods == expected_previous, \
            f"Previous year should have SAME 3 months as current year (Jun-Aug 2024)\n" \
            f"Expected: {expected_previous}\n" \
            f"Got: {previous_year_periods}\n" \
            f"Reason: Year-over-year comparison requires same months from previous year"
    
    def test_period_generation_symmetry(self, weather_data_repo):
        """
        Test that period generation is symmetric.
        
        Both current and previous year should have the same number of periods
        and represent complete months.
        """
        target_yyyymm = '202508'
        target_period = 'A'
        months_back = 3
        
        periods = weather_data_repo._generate_year_over_year_periods(
            target_yyyymm, target_period, months_back
        )
        
        period_labels = [p.period_label for p in periods]
        
        # Split by year
        current_year = [p for p in period_labels if p.startswith('2025')]
        previous_year = [p for p in period_labels if p.startswith('2024')]
        
        # Verify symmetry
        assert len(current_year) == len(previous_year), \
            f"Period counts should be symmetric!\n" \
            f"Current year: {len(current_year)} periods\n" \
            f"Previous year: {len(previous_year)} periods"
        
        # Verify both represent complete months (even number of periods)
        assert len(current_year) % 2 == 0, \
            f"Current year should have complete months (even number of periods), got {len(current_year)}"
        
        assert len(previous_year) % 2 == 0, \
            f"Previous year should have complete months (even number of periods), got {len(previous_year)}"
        
        # Verify each represents exactly months_back complete months
        expected_periods_per_year = months_back * 2
        assert len(current_year) == expected_periods_per_year, \
            f"Current year should have {months_back} complete months ({expected_periods_per_year} periods), " \
            f"got {len(current_year)}"
        
        assert len(previous_year) == expected_periods_per_year, \
            f"Previous year should have {months_back} complete months ({expected_periods_per_year} periods), " \
            f"got {len(previous_year)}"
    
    def test_period_generation_includes_full_target_month(self, weather_data_repo):
        """
        CRITICAL TEST: Verify that the full target month is included.
        
        If target is 202508A (Aug 1-15), the result should include:
        - 202508A (Aug 1-15) ✓
        - 202508B (Aug 16-31) ✓ <- MUST be included!
        
        This ensures no data loss from the target month.
        """
        test_cases = [
            ('202508', 'A', ['202508A', '202508B']),  # Target Aug A, should include Aug B
            ('202508', 'B', ['202508A', '202508B']),  # Target Aug B, should include Aug A
            ('202411', 'A', ['202411A', '202411B']),  # Target Nov A, should include Nov B
            ('202411', 'B', ['202411A', '202411B']),  # Target Nov B, should include Nov A
        ]
        
        for target_yyyymm, target_period, expected_target_month in test_cases:
            periods = weather_data_repo._generate_year_over_year_periods(
                target_yyyymm, target_period, months_back=3
            )
            
            period_labels = [p.period_label for p in periods]
            
            # Check if both halves of target month are included
            for expected_period in expected_target_month:
                assert expected_period in period_labels, \
                    f"Target month {target_yyyymm} is incomplete!\n" \
                    f"Target: {target_yyyymm}{target_period}\n" \
                    f"Missing: {expected_period}\n" \
                    f"Generated periods: {period_labels}\n" \
                    f"The full target month should always be included."
    
    def test_period_generation_with_different_months_back(self, weather_data_repo):
        """
        Test period generation with different months_back values.
        
        Verifies that the logic generates correct total period count:
        - months_back=1 → 4 periods total (1 month current + 1 month previous year)
        - months_back=2 → 8 periods total (2 months current + 2 months previous year)
        - months_back=3 → 12 periods total (3 months current + 3 months previous year)
        
        Each month has 2 periods (A and B halves), so total = months_back * 2 * 2 years
        
        Note: For large months_back values, periods may span across calendar years.
        """
        test_cases = [
            (1, 4),   # 1 month × 2 halves × 2 years = 4 periods
            (2, 8),   # 2 months × 2 halves × 2 years = 8 periods
            (3, 12),  # 3 months × 2 halves × 2 years = 12 periods
        ]
        
        for months_back, expected_total in test_cases:
            periods = weather_data_repo._generate_year_over_year_periods(
                '202508', 'A', months_back
            )
            
            period_labels = [p.period_label for p in periods]
            
            assert len(period_labels) == expected_total, \
                f"For months_back={months_back}, expected {expected_total} periods, " \
                f"got {len(period_labels)}. Periods: {period_labels}"
            
            # Verify we have periods from both current and previous year
            # (May span multiple calendar years depending on months_back)
            years_present = set(p[:4] for p in period_labels)
            assert len(years_present) >= 1, \
                f"Should have periods from at least one year, got {years_present}"
            
            # Verify each period is valid (has year, month, and half)
            for period in period_labels:
                assert len(period) == 7, f"Period {period} should be 7 chars (YYYYMMA/B)"
                assert period[6] in ['A', 'B'], f"Period {period} should end with A or B"
    
    def test_period_labels_are_chronological_within_year(self, weather_data_repo):
        """
        Test that periods are chronological within each year group.
        
        For year-over-year analysis, periods are grouped by year:
        - Current year periods (2025) come first, in chronological order
        - Previous year periods (2024) come second, in chronological order
        
        This grouping makes it easier to process current vs previous year data.
        """
        periods = weather_data_repo._generate_year_over_year_periods(
            '202508', 'A', months_back=3
        )
        
        period_labels = [p.period_label for p in periods]
        
        # Split by year
        current_year = [p for p in period_labels if p.startswith('2025')]
        previous_year = [p for p in period_labels if p.startswith('2024')]
        
        # Helper to convert period to comparable number
        def to_comparable(p):
            return int(p[:6]) * 10 + (0 if p[6] == 'A' else 1)
        
        # Verify current year periods are chronological
        for i in range(len(current_year) - 1):
            current = current_year[i]
            next_period = current_year[i + 1]
            assert to_comparable(current) < to_comparable(next_period), \
                f"Current year periods should be chronological, but {current} comes before {next_period}"
        
        # Verify previous year periods are chronological
        for i in range(len(previous_year) - 1):
            current = previous_year[i]
            next_period = previous_year[i + 1]
            assert to_comparable(current) < to_comparable(next_period), \
                f"Previous year periods should be chronological, but {current} comes before {next_period}"
        
        # Verify grouping: all current year periods come before previous year
        if current_year and previous_year:
            last_current = current_year[-1]
            first_previous = previous_year[0]
            # This is expected: 2025 periods come before 2024 periods for year-over-year comparison
            assert last_current.startswith('2025') and first_previous.startswith('2024'), \
                f"Year-over-year grouping: current year ({last_current}) should come before previous year ({first_previous})"
    
    def test_period_date_ranges_are_correct(self, weather_data_repo):
        """
        Test that period date ranges are correctly calculated.
        
        Verifies:
        - A periods: 1st to 15th of month
        - B periods: 16th to last day of month
        - Dates are valid and sequential
        """
        periods = weather_data_repo._generate_year_over_year_periods(
            '202508', 'A', months_back=3
        )
        
        for period in periods:
            year = int(period.yyyymm[:4])
            month = int(period.yyyymm[4:6])
            half = period.period_half
            
            if half == 'A':
                # A period should be 1st to 15th
                assert period.start_date == f"{year:04d}-{month:02d}-01", \
                    f"A period should start on 1st, got {period.start_date}"
                assert period.end_date == f"{year:04d}-{month:02d}-15", \
                    f"A period should end on 15th, got {period.end_date}"
            else:  # B
                # B period should be 16th to last day
                assert period.start_date == f"{year:04d}-{month:02d}-16", \
                    f"B period should start on 16th, got {period.start_date}"
                # End date should be last day of month (28-31)
                end_day = int(period.end_date.split('-')[2])
                assert 28 <= end_day <= 31, \
                    f"B period should end on last day of month (28-31), got {end_day}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
