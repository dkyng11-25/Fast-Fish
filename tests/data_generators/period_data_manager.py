#!/usr/bin/env python3
"""
Period Data Manager

Manages multiple period data for testing following USER_NOTE.md requirements:
- Detects available periods
- Downloads missing data when needed
- Manages period-specific subset data
- Provides fallback mechanisms
"""

import os
import sys
import pandas as pd
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.data_generators.subset_generator import SubsetDataGenerator

logger = logging.getLogger(__name__)


class PeriodDataManager:
    """Manages multiple period data for testing."""
    
    def __init__(self, project_root: Path):
        """Initialize the period data manager."""
        self.project_root = project_root
        self.data_dir = project_root / "data"
        self.output_dir = project_root / "output"
        self.test_data_dir = project_root / "tests" / "test_data"
        
        # Ensure directories exist
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize subset generator
        self.subset_generator = SubsetDataGenerator(project_root)
        
        # Available periods (in order of preference)
        self.available_periods = ['202509A', '202508A', '202508B', '202508C']
    
    def detect_available_periods(self) -> List[str]:
        """
        Detect available periods from existing data.
        
        Returns:
            List of available periods
        """
        logger.info("Detecting available periods")
        
        available = []
        
        # Check for clustering results (indicates processed data)
        clustering_files = list(self.output_dir.glob("clustering_results_*.csv"))
        for file in clustering_files:
            # Extract period from filename
            if "_spu_" in file.name:
                period = file.name.replace("clustering_results_spu_", "").replace(".csv", "")
                if period and period not in available:
                    available.append(period)
        
        # Check for raw data files
        data_files = list(self.data_dir.glob("*_2025*.csv"))
        for file in data_files:
            # Extract period from filename
            parts = file.stem.split("_")
            for part in parts:
                if part.startswith("2025") and len(part) >= 6:
                    period = part
                    if period not in available:
                        available.append(period)
        
        # Sort by preference
        available = [p for p in self.available_periods if p in available]
        
        logger.info(f"Detected available periods: {available}")
        return available
    
    def get_best_available_period(self) -> Optional[str]:
        """
        Get the best available period for testing.
        
        Returns:
            Best available period or None
        """
        available = self.detect_available_periods()
        
        if not available:
            logger.warning("No available periods detected")
            return None
        
        # Return the first available period (highest preference)
        best_period = available[0]
        logger.info(f"Best available period: {best_period}")
        return best_period
    
    def ensure_period_data(self, period: str) -> bool:
        """
        Ensure data is available for a specific period.
        
        Args:
            period: Data period
            
        Returns:
            True if data is available, False otherwise
        """
        logger.info(f"Ensuring data for period {period}")
        
        # Check if data already exists
        if self._check_period_data_exists(period):
            logger.info(f"Data already exists for period {period}")
            return True
        
        # Try to download data
        if self._download_period_data(period):
            logger.info(f"Successfully downloaded data for period {period}")
            return True
        
        logger.warning(f"Could not obtain data for period {period}")
        return False
    
    def _check_period_data_exists(self, period: str) -> bool:
        """Check if data exists for a period."""
        # Check for key files
        key_files = [
            self.output_dir / f"clustering_results_spu_{period}.csv",
            self.data_dir / f"complete_spu_sales_{period}.csv",
            self.data_dir / f"stores_{period}.csv"
        ]
        
        # Check if at least one key file exists
        return any(f.exists() for f in key_files)
    
    def _download_period_data(self, period: str) -> bool:
        """
        Download data for a specific period.
        
        Args:
            period: Data period
            
        Returns:
            True if download successful, False otherwise
        """
        logger.info(f"Attempting to download data for period {period}")
        
        try:
            # Try to run data download scripts
            # This would depend on your specific data download implementation
            # For now, we'll just log that we would attempt download
            
            # Example: Run data download script
            # cmd = [sys.executable, "scripts/download_data.py", "--period", period]
            # result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            # return result.returncode == 0
            
            logger.info(f"Data download for period {period} would be attempted here")
            return False  # Placeholder - implement actual download logic
            
        except Exception as e:
            logger.error(f"Failed to download data for period {period}: {e}")
            return False
    
    def setup_test_data_for_period(self, period: str) -> bool:
        """
        Setup complete test data for a period.
        
        Args:
            period: Data period
            
        Returns:
            True if setup successful, False otherwise
        """
        logger.info(f"Setting up test data for period {period}")
        
        try:
            # Ensure period data exists
            if not self.ensure_period_data(period):
                logger.error(f"Could not obtain data for period {period}")
                return False
            
            # Generate subset data
            if not self.subset_generator.ensure_test_data(period):
                logger.error(f"Could not generate subset data for period {period}")
                return False
            
            logger.info(f"Successfully set up test data for period {period}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup test data for period {period}: {e}")
            return False
    
    def setup_all_available_periods(self) -> Dict[str, bool]:
        """
        Setup test data for all available periods.
        
        Returns:
            Dictionary mapping periods to setup success status
        """
        logger.info("Setting up test data for all available periods")
        
        available_periods = self.detect_available_periods()
        results = {}
        
        for period in available_periods:
            logger.info(f"Setting up test data for period {period}")
            results[period] = self.setup_test_data_for_period(period)
        
        successful = sum(results.values())
        logger.info(f"Successfully set up test data for {successful}/{len(available_periods)} periods")
        
        return results
    
    def get_test_data_status(self) -> Dict[str, Dict[str, bool]]:
        """
        Get status of test data for all periods.
        
        Returns:
            Dictionary with test data status
        """
        logger.info("Checking test data status")
        
        status = {}
        available_periods = self.detect_available_periods()
        
        for period in available_periods:
            period_status = {
                'raw_data_exists': self._check_period_data_exists(period),
                'subset_data_exists': self._check_subset_data_exists(period),
                'cluster_data_exists': self._check_cluster_data_exists(period),
                'subsample_data_exists': self._check_subsample_data_exists(period)
            }
            status[period] = period_status
        
        return status
    
    def _check_subset_data_exists(self, period: str) -> bool:
        """Check if subset data exists for a period."""
        subset_file = self.test_data_dir / f"generated_store_subset_{period}.csv"
        return subset_file.exists()
    
    def _check_cluster_data_exists(self, period: str) -> bool:
        """Check if cluster data exists for a period."""
        cluster_file = self.test_data_dir / f"generated_cluster_subset_{period}.csv"
        return cluster_file.exists()
    
    def _check_subsample_data_exists(self, period: str) -> bool:
        """Check if subsample data exists for a period."""
        subsample_file = self.test_data_dir / f"generated_subsample_{period}.csv"
        return subsample_file.exists()
    
    def cleanup_old_data(self, keep_periods: List[str] = None) -> int:
        """
        Clean up old test data, keeping specified periods.
        
        Args:
            keep_periods: List of periods to keep
            
        Returns:
            Number of files cleaned up
        """
        if keep_periods is None:
            keep_periods = self.available_periods[:2]  # Keep top 2 periods
        
        logger.info(f"Cleaning up old data, keeping periods: {keep_periods}")
        
        cleaned_count = 0
        
        # Clean up generated test data
        for file in self.test_data_dir.glob("generated_*.csv"):
            # Extract period from filename
            period = None
            for p in self.available_periods:
                if p in file.name:
                    period = p
                    break
            
            if period and period not in keep_periods:
                file.unlink()
                cleaned_count += 1
                logger.info(f"Cleaned up old data file: {file.name}")
        
        logger.info(f"Cleaned up {cleaned_count} old data files")
        return cleaned_count


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage period data for testing")
    parser.add_argument("--detect", action="store_true", help="Detect available periods")
    parser.add_argument("--setup", help="Setup test data for specific period")
    parser.add_argument("--setup-all", action="store_true", help="Setup test data for all periods")
    parser.add_argument("--status", action="store_true", help="Show test data status")
    parser.add_argument("--cleanup", action="store_true", help="Clean up old data")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize manager
    manager = PeriodDataManager(Path(__file__).parent.parent.parent)
    
    try:
        if args.detect:
            periods = manager.detect_available_periods()
            print(f"Available periods: {periods}")
            
        elif args.setup:
            success = manager.setup_test_data_for_period(args.setup)
            print(f"Setup for period {args.setup}: {'Success' if success else 'Failed'}")
            
        elif args.setup_all:
            results = manager.setup_all_available_periods()
            print("Setup results:")
            for period, success in results.items():
                print(f"  {period}: {'Success' if success else 'Failed'}")
                
        elif args.status:
            status = manager.get_test_data_status()
            print("Test data status:")
            for period, period_status in status.items():
                print(f"  {period}:")
                for data_type, exists in period_status.items():
                    print(f"    {data_type}: {'✓' if exists else '✗'}")
                    
        elif args.cleanup:
            cleaned = manager.cleanup_old_data()
            print(f"Cleaned up {cleaned} old data files")
            
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()




