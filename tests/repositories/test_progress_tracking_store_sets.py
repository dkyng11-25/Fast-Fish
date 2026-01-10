"""
Test for Issue #1: Progress Tracking with Different Store Sets

This test verifies that progress tracking correctly handles different store sets
and doesn't cause failures when running with a different number of stores.

Issue: Running with 2 stores, then 100 stores fails because progress says
       period is "completed" but only 2 stores have data.

Author: Data Pipeline Team
Date: 2025-10-28
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import pandas as pd
from datetime import datetime

from core.logger import PipelineLogger
from repositories.weather_file_repository import WeatherFileRepository
from repositories.weather_data_repository import WeatherDataRepository
from repositories.csv_repository import CsvFileRepository
from repositories.json_repository import ProgressTrackingRepository
from repositories.weather_api_repository import WeatherApiRepository


class TestProgressTrackingWithDifferentStoreSets:
    """Test progress tracking behavior with different store sets."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return PipelineLogger("TestProgress")
    
    def test_progress_marks_period_completed_after_download(self, temp_dir, logger):
        """
        Test that progress correctly marks a period as completed.
        
        This is the first part of the issue - progress tracking works correctly
        for the initial run.
        """
        # Setup
        progress_file = Path(temp_dir) / "progress.json"
        progress_repo = ProgressTrackingRepository(
            file_path=str(progress_file),
            logger=logger
        )
        
        # Simulate downloading 2 stores
        progress_data = {
            'completed_periods': ['202508A'],
            'current_period': '202508A',
            'completed_stores': ['11014', '11041'],
            'failed_stores': [],
            'vpn_switches': 0,
            'last_update': datetime.now().isoformat()
        }
        
        progress_repo.save(progress_data)
        
        # Verify progress was saved
        loaded = progress_repo.load()
        assert '202508A' in loaded['completed_periods'], \
            "Period should be marked as completed"
        assert len(loaded['completed_stores']) == 2, \
            "Should have 2 completed stores"
    
    def test_progress_shows_only_completed_stores(self, temp_dir, logger):
        """
        Test that progress accurately reflects which stores are completed.
        
        This is the core of Issue #1 - progress says period is "completed"
        but only tracks specific stores.
        """
        # Setup
        progress_file = Path(temp_dir) / "progress.json"
        progress_repo = ProgressTrackingRepository(
            file_path=str(progress_file),
            logger=logger
        )
        
        # First run: 2 stores
        progress_data = {
            'completed_periods': ['202508A'],
            'current_period': '202508A',
            'completed_stores': ['11014', '11041'],  # ← Only 2 stores!
            'failed_stores': [],
            'vpn_switches': 0,
            'last_update': datetime.now().isoformat()
        }
        
        progress_repo.save(progress_data)
        
        # Load and verify
        loaded = progress_repo.load()
        
        # Period is marked as "completed"
        assert '202508A' in loaded['completed_periods'], \
            "Period marked as completed"
        
        # But only 2 stores are actually completed
        assert len(loaded['completed_stores']) == 2, \
            "Only 2 stores completed"
        
        # This is the issue: If we now try to run with 100 stores,
        # the system sees period as "completed" and assumes all 100 stores are done!
        # But only 2 stores have data!
    
    def test_issue_different_store_sets_cause_mismatch(self, temp_dir, logger):
        """
        Test that demonstrates Issue #1: Different store sets cause data mismatch.
        
        Scenario:
        1. Run with 2 stores → Success, progress marks period as "completed"
        2. Run with 100 stores → System thinks all 100 are done, but only 2 have data
        3. Result: Failure when trying to load 100 stores
        
        This test documents the issue (not a fix, just demonstrates the problem).
        """
        # Setup
        weather_dir = Path(temp_dir) / "weather_data"
        weather_dir.mkdir(parents=True, exist_ok=True)
        
        progress_file = Path(temp_dir) / "progress.json"
        progress_repo = ProgressTrackingRepository(
            file_path=str(progress_file),
            logger=logger
        )
        
        # First run: Download 2 stores
        first_run_stores = ['11014', '11041']
        
        # Create weather files for 2 stores
        for store in first_run_stores:
            file_path = weather_dir / f"weather_data_{store}_116.0_39.0_20250801_to_20250815.csv"
            pd.DataFrame({'time': ['2025-08-01'], 'temperature_2m': [25.0]}).to_csv(file_path, index=False)
        
        # Mark progress as completed
        progress_data = {
            'completed_periods': ['202508A'],  # ← Period marked as done!
            'current_period': '202508A',
            'completed_stores': first_run_stores,  # ← Only 2 stores
            'failed_stores': [],
            'vpn_switches': 0,
            'last_update': datetime.now().isoformat()
        }
        progress_repo.save(progress_data)
        
        # Second run: Try to load 100 stores
        second_run_stores = first_run_stores + [f"store_{i}" for i in range(3, 101)]
        
        # Check how many files actually exist
        existing_files = list(weather_dir.glob("weather_data_*.csv"))
        assert len(existing_files) == 2, \
            f"Only 2 files exist, but we're trying to load {len(second_run_stores)} stores"
        
        # This is the issue: Progress says period is "completed",
        # but we only have 2/100 files!
        loaded_progress = progress_repo.load()
        assert '202508A' in loaded_progress['completed_periods'], \
            "Progress says period is completed"
        assert len(loaded_progress['completed_stores']) == 2, \
            "But only 2 stores are actually completed"
        
        # If we try to load all 100 stores, we'll only find 2 files
        # This causes the "No weather data returned" error!
    
    def test_cleanup_fixes_the_issue(self, temp_dir, logger):
        """
        Test that cleanup (deleting progress file) fixes Issue #1.
        
        This is the workaround we discovered:
        1. Delete progress file
        2. Delete old data
        3. Run again → Success
        """
        # Setup
        weather_dir = Path(temp_dir) / "weather_data"
        weather_dir.mkdir(parents=True, exist_ok=True)
        
        progress_file = Path(temp_dir) / "progress.json"
        progress_repo = ProgressTrackingRepository(
            file_path=str(progress_file),
            logger=logger
        )
        
        # First run: 2 stores (creates the problem)
        progress_data = {
            'completed_periods': ['202508A'],
            'current_period': '202508A',
            'completed_stores': ['11014', '11041'],
            'failed_stores': [],
            'vpn_switches': 0,
            'last_update': datetime.now().isoformat()
        }
        progress_repo.save(progress_data)
        
        # Create 2 weather files
        for store in ['11014', '11041']:
            file_path = weather_dir / f"weather_data_{store}_116.0_39.0_20250801_to_20250815.csv"
            pd.DataFrame({'time': ['2025-08-01'], 'temperature_2m': [25.0]}).to_csv(file_path, index=False)
        
        # Verify the problem exists
        assert progress_file.exists(), "Progress file exists (problem state)"
        assert len(list(weather_dir.glob("*.csv"))) == 2, "Only 2 files exist"
        
        # CLEANUP (the fix!)
        progress_file.unlink()  # Delete progress file
        for f in weather_dir.glob("*.csv"):
            f.unlink()  # Delete old weather files
        
        # Verify cleanup worked
        assert not progress_file.exists(), "Progress file deleted"
        assert len(list(weather_dir.glob("*.csv"))) == 0, "Weather files deleted"
        
        # Now we can run with 100 stores (fresh start)
        # Progress will be empty (returns default structure), so it will download all 100 stores
        new_progress = progress_repo.load()
        # After cleanup, load() returns default structure (not saved data)
        assert len(new_progress.get('completed_periods', [])) == 0, \
            "Progress is empty after cleanup"
        assert len(new_progress.get('completed_stores', [])) == 0, \
            "No completed stores after cleanup"


class TestProgressTrackingRecommendations:
    """Tests for recommended improvements to progress tracking."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def logger(self):
        """Create a test logger."""
        return PipelineLogger("TestRecommendations")
    
    def test_per_store_progress_tracking_concept(self, temp_dir, logger):
        """
        Test concept: Per-store progress tracking (recommended improvement).
        
        Instead of marking period as "completed", track which specific stores
        are completed. This would fix Issue #1 permanently.
        
        This is a conceptual test showing how it SHOULD work.
        """
        # Setup
        progress_file = Path(temp_dir) / "progress.json"
        progress_repo = ProgressTrackingRepository(
            file_path=str(progress_file),
            logger=logger
        )
        
        # Better progress structure (per-store tracking)
        better_progress = {
            'periods': {
                '202508A': {
                    'completed_stores': ['11014', '11041'],  # ← Specific stores
                    'total_stores_attempted': 2,
                    'last_update': datetime.now().isoformat()
                }
            }
        }
        
        progress_repo.save(better_progress)
        
        # Now when we run with 100 stores:
        # 1. Load progress
        # 2. See that only 2 stores are completed for this period
        # 3. Download the other 98 stores
        # 4. Update progress with all 100 stores
        
        loaded = progress_repo.load()
        completed_for_period = loaded['periods']['202508A']['completed_stores']
        
        # We know exactly which stores are done
        assert len(completed_for_period) == 2, "2 stores completed"
        
        # We can calculate which stores are missing
        all_stores = ['11014', '11041'] + [f"store_{i}" for i in range(3, 101)]
        missing_stores = [s for s in all_stores if s not in completed_for_period]
        
        assert len(missing_stores) == 98, "98 stores need to be downloaded"
        
        # This is the better approach - no manual cleanup needed!
    
    def test_cleanup_flag_concept(self, temp_dir, logger):
        """
        Test concept: --clean flag (recommended improvement).
        
        Add a flag to automatically cleanup before running.
        This would make the workaround automatic.
        
        This is a conceptual test showing how it SHOULD work.
        """
        # Setup
        progress_file = Path(temp_dir) / "progress.json"
        weather_dir = Path(temp_dir) / "weather_data"
        weather_dir.mkdir(parents=True, exist_ok=True)
        
        # Create old data
        progress_repo = ProgressTrackingRepository(
            file_path=str(progress_file),
            logger=logger
        )
        progress_repo.save({
            'completed_periods': ['202508A'],
            'completed_stores': ['11014', '11041']
        })
        
        # Create old files
        old_file = weather_dir / "weather_data_11014_116.0_39.0_20250801_to_20250815.csv"
        pd.DataFrame({'time': ['2025-08-01']}).to_csv(old_file, index=False)
        
        # Verify old data exists
        assert progress_file.exists(), "Old progress exists"
        assert old_file.exists(), "Old weather file exists"
        
        # Simulate --clean flag behavior
        def cleanup_before_run(progress_path, weather_path):
            """This is what --clean flag would do."""
            # Delete progress
            if progress_path.exists():
                progress_path.unlink()
            
            # Delete weather files
            for f in weather_path.glob("*.csv"):
                f.unlink()
        
        # Run cleanup
        cleanup_before_run(progress_file, weather_dir)
        
        # Verify cleanup worked
        assert not progress_file.exists(), "Progress cleaned"
        assert not old_file.exists(), "Weather files cleaned"
        
        # Now we can run fresh
        # This is what --clean flag would enable


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
