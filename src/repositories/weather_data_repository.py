#!/usr/bin/env python3
"""
Weather Data Repository

Purpose: Retrieve and manage weather data for store locations across multiple time periods.

This repository was converted from Step 4 because it only performs data retrieval
with no business logic. The actual temperature processing happens in Step 5.

CRITICAL: SINGLE PERIOD DESIGN
================================
This repository downloads weather data for ONE PERIOD at a time.

**Design Philosophy:**
- Each run downloads ONE target period only (e.g., 202508A = Aug 1-15, 2025)
- For multiple periods, the orchestrator should call this step multiple times
- This keeps the step simple, focused, and composable

**Target Period Definition:**
- The target period is the specific period you want weather data for
- Example: 202508A = August 1-15, 2025
- Example: 202508B = August 16-31, 2025

**Handling Current/Future Periods:**
- If target period is in the future: Skipped with warning
- If target period is current (today is within range): Downloads up to today
- If target period is past: Downloads full period data

**Example Workflow:**
```
Target: 202508A (August 2025, first half)
Today: August 10, 2025

Result: Downloads Aug 1-10, 2025 (partial, up to today)
```

**For Multiple Periods:**
An orchestrator can call this step multiple times:
```python
# Download 3 months of data
download_weather("202506", "A")  # June 1-15
download_weather("202506", "B")  # June 16-30
download_weather("202507", "A")  # July 1-15
download_weather("202507", "B")  # July 16-31
download_weather("202508", "A")  # August 1-15
download_weather("202508", "B")  # August 16-31
```

**Why Single Period?**
1. Simpler logic - one period, one responsibility
2. Composable - orchestrator controls multi-period strategy
3. Matches legacy Step 4 behavior (one date range per run)
4. Easier to test and debug
5. Clear separation of concerns

Author: Data Pipeline
Date: 2025-10-10
Updated: 2025-10-28 (Changed from multi-period to single-period design)
"""

from __future__ import annotations
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, date
import calendar
import time
import random
import pandas as pd

from src.core.logger import PipelineLogger
from repositories.base import Repository
from repositories import (
    WeatherApiRepository,
    CsvFileRepository,
    JsonFileRepository,
    ProgressTrackingRepository
)
from repositories.weather_file_repository import WeatherFileRepository


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class WeatherDataError(Exception):
    """Raised when weather data operations fail."""
    pass


# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

@dataclass
class PeriodInfo:
    """Information about a time period for weather data."""
    period_label: str  # e.g., "202505A"
    yyyymm: str  # e.g., "202505"
    period_half: str  # "A" or "B"
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    weather_period_label: str  # YYYYMMDD_to_YYYYMMDD


@dataclass
class DownloadStats:
    """Statistics for a download session."""
    successful_downloads: int = 0
    failed_downloads: int = 0
    consecutive_failures: int = 0
    stores_processed_since_vpn: int = 0


@dataclass
class WeatherDataConfig:
    """Configuration for weather data retrieval."""
    months_back: int = 3
    stores_per_vpn_batch: int = 50
    min_delay: float = 0.5
    max_delay: float = 1.5
    rate_limit_backoff_min: float = 5.0
    rate_limit_backoff_max: float = 20.0
    max_retries: int = 3
    vpn_switch_threshold: int = 5
    timezone: str = 'Asia/Shanghai'
    enable_vpn_switching: bool = False


# ============================================================================
# WEATHER DATA REPOSITORY
# ============================================================================

class WeatherDataRepository(Repository):
    """
    Repository for weather data retrieval and management.
    
    This repository orchestrates weather data download from APIs,
    manages progress tracking, handles VPN switching, and ensures
    data quality for downstream processing.
    """
    
    # Constants
    ALTITUDE_DELAY = 0.1
    PROGRESS_SAVE_INTERVAL = 25
    LOG_INTERVAL = 10
    
    def __init__(
        self,
        coordinates_repo: CsvFileRepository,
        weather_api_repo: WeatherApiRepository,
        weather_file_repo: WeatherFileRepository,
        altitude_repo: CsvFileRepository,
        progress_repo: ProgressTrackingRepository,
        logger: PipelineLogger
    ):
        """
        Initialize Weather Data Repository.
        
        Args:
            coordinates_repo: Repository for store coordinates
            weather_api_repo: Repository for weather API calls
            weather_file_repo: Repository for weather file operations
            altitude_repo: Repository for altitude data
            progress_repo: Repository for progress tracking
            logger: Pipeline logger
        """
        super().__init__(logger)
        self.coordinates_repo = coordinates_repo
        self.weather_api_repo = weather_api_repo
        self.weather_file_repo = weather_file_repo
        self.altitude_repo = altitude_repo
        self.progress_repo = progress_repo
    
    # ========================================================================
    # PUBLIC METHODS
    # ========================================================================
    
    def get_weather_data_for_period(
        self,
        target_yyyymm: str,
        target_period: str,
        config: Optional[WeatherDataConfig] = None
    ) -> Dict[str, Any]:
        """
        Retrieve weather data for stores across multiple time periods.
        
        This is the main entry point for getting weather data. It:
        1. Loads store coordinates
        2. Generates year-over-year periods for analysis
        3. Downloads weather data for all stores and periods
        4. Collects altitude data for stores
        5. Validates data completeness
        6. Returns all retrieved data
        
        Args:
            target_yyyymm: Target year-month (e.g., "202506")
            target_period: Target period half ("A" or "B")
            config: Optional configuration (uses defaults if not provided)
            
        Returns:
            Dictionary containing:
            - weather_files: List of downloaded weather file paths
            - altitude_data: DataFrame with altitude information
            - download_stats: Statistics about the download session
            - periods: List of PeriodInfo objects processed
            
        Raises:
            DataValidationError: If data validation fails
        """
        # Use default config if not provided
        if config is None:
            config = WeatherDataConfig()
        
        self.logger.info(
            f"Starting weather data retrieval for {target_yyyymm}{target_period}",
            self.repo_name
        )
        
        # Step 1: Load store coordinates
        self.logger.info("Loading store coordinates...", self.repo_name)
        coords_df = self.coordinates_repo.get_all()
        coords_df['str_code'] = coords_df['str_code'].astype(str)
        
        self.logger.info(
            f"Loaded {len(coords_df)} stores with coordinates",
            self.repo_name
        )
        
        # Step 2: Load or initialize progress tracking
        progress = self.progress_repo.load()
        
        self.logger.info(
            f"Progress loaded: {len(progress.get('completed_periods', []))} periods completed, "
            f"{len(progress.get('completed_stores', []))} stores completed",
            self.repo_name
        )
        
        # Step 3: Generate single target period
        # IMPORTANT: Only downloads ONE period at a time
        # For multiple periods, run this step multiple times with different targets
        periods = self._generate_single_period(
            target_yyyymm,
            target_period
        )
        
        self.logger.info(
            f"Target period: {periods[0].period_label if periods else 'None'}",
            self.repo_name
        )
        
        # Step 4: Collect altitude data (shared across all periods)
        self.logger.info("Collecting altitude data for all stores...", self.repo_name)
        altitude_df = self._collect_altitude_data(coords_df)
        
        # Step 5: Filter to remaining periods
        remaining_periods = [
            p for p in periods 
            if p.period_label not in progress.get('completed_periods', [])
        ]
        
        if not remaining_periods:
            self.logger.info("All periods already completed!", self.repo_name)
            # Load ONLY the weather files for the requested periods (not all files in directory)
            import pandas as pd
            
            # Use the helper method to load only files for the requested periods
            weather_data_list = []
            for period_info in periods:
                period_data = self._load_existing_weather_for_period(period_info, coords_df)
                weather_data_list.extend(period_data)
            
            self.logger.info(f"Loading {len(weather_data_list)} weather files for {len(periods)} periods", self.repo_name)
            
            # Concatenate into single DataFrame
            combined_weather_df = pd.concat(weather_data_list, ignore_index=True) if weather_data_list else pd.DataFrame()
            
            self.logger.info(f"Combined weather data: {len(combined_weather_df)} records from {len(periods)} periods", self.repo_name)
            
            return {
                'weather_files': combined_weather_df,  # Return DataFrame, not list of paths
                'altitude_data': altitude_df,
                'download_stats': DownloadStats(),
                'periods': periods
            }
        
        self.logger.info(
            f"Processing {len(remaining_periods)} remaining periods",
            self.repo_name
        )
        
        # Step 6: Download weather data for each period
        all_weather_data = []
        
        for period_info in remaining_periods:
            self.logger.info(
                f"Starting period {period_info.period_label} "
                f"({period_info.start_date} to {period_info.end_date})",
                self.repo_name
            )
            
            period_weather_data = self._download_period_with_vpn_support(
                period_info,
                coords_df,
                progress,
                config
            )
            
            all_weather_data.extend(period_weather_data)
            
            # Mark period as completed
            if period_info.period_label not in progress['completed_periods']:
                progress['completed_periods'].append(period_info.period_label)
            
            # Save progress after each period
            progress['last_update'] = datetime.now().isoformat()
            self.progress_repo.save(progress)
        
        # Step 7: Save altitude data
        self.logger.info("Saving altitude data...", self.repo_name)
        self.altitude_repo.save(altitude_df)
        
        # Step 8: Save final progress
        self.logger.info("Saving final progress...", self.repo_name)
        progress['last_update'] = datetime.now().isoformat()
        self.progress_repo.save(progress)
        
        # Step 9: Concatenate all weather DataFrames into single DataFrame
        import pandas as pd
        combined_weather_df = pd.concat(all_weather_data, ignore_index=True) if all_weather_data else pd.DataFrame()
        
        self.logger.info(f"Combined weather data: {len(combined_weather_df)} records", self.repo_name)
        
        # Return all retrieved data
        return {
            'weather_files': combined_weather_df,  # Return DataFrame, not list
            'altitude_data': altitude_df,
            'download_stats': DownloadStats(
                successful_downloads=len(all_weather_data),
                failed_downloads=len(progress.get('failed_stores', []))
            ),
            'periods': periods
        }
    
    def get_altitude_data(self, store_codes: List[str]) -> pd.DataFrame:
        """
        Get altitude data for specified stores.
        
        Args:
            store_codes: List of store codes
            
        Returns:
            DataFrame with altitude information
        """
        # TODO: Implementation
        pass
    
    def validate_weather_data(
        self,
        weather_files: List[str],
        altitude_data: pd.DataFrame,
        expected_stores: Set[str]
    ) -> Dict[str, Any]:
        """
        Validate downloaded weather data.
        
        Args:
            weather_files: List of weather file paths
            altitude_data: DataFrame with altitude data
            expected_stores: Set of expected store codes
            
        Returns:
            Dictionary with validation results
        """
        # TODO: Implementation
        pass
    
    def get_all(self) -> List[Dict[str, Any]]:
        """
        Get all weather data (required by base Repository class).
        
        Note: This repository doesn't use get_all pattern.
        Use get_weather_data_for_period() instead.
        
        Returns:
            Empty list (not applicable for this repository)
        """
        self.logger.warning(
            "get_all() called on WeatherDataRepository - use get_weather_data_for_period() instead",
            self.repo_name
        )
        return []
    
    def save(self, data: pd.DataFrame) -> None:
        """
        Save weather data (required by base Repository class).
        
        Note: This repository doesn't use save pattern.
        Weather data is saved incrementally via WeatherFileRepository.
        
        Args:
            data: DataFrame to save (ignored)
        """
        self.logger.warning(
            "save() called on WeatherDataRepository - weather data is saved incrementally",
            self.repo_name
        )
    
    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================
    
    def _generate_year_over_year_periods(
        self,
        target_yyyymm: str,
        target_period: str,
        months_back: int
    ) -> List[PeriodInfo]:
        """
        Generate dynamic list of periods for year-over-year analysis.
        
        Args:
            target_yyyymm: Target year-month
            target_period: Target period half
            months_back: Number of months to look back
            
        Returns:
            List[PeriodInfo]: List of period information objects
        """
        periods: List[PeriodInfo] = []
        
        # Normalize period
        base_period = self._normalize_period(target_period)
        
        today = date.today()
        
        # Build periods using helper
        period_tuples = self._build_year_over_year_period_tuples(
            target_yyyymm,
            base_period,
            months_back
        )
        
        for yyyymm, half, start_date, end_date in period_tuples:
            # Skip periods that start in the future
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
            except Exception:
                continue
            
            if start_dt > today:
                continue
            
            # Clamp end date to today if needed
            if end_dt > today:
                end_date = today.isoformat()
            
            period_label = f"{yyyymm}{half}"
            weather_label = f"{start_date.replace('-', '')}_to_{end_date.replace('-', '')}"
            
            periods.append(PeriodInfo(
                period_label=period_label,
                yyyymm=yyyymm,
                period_half=half,
                start_date=start_date,
                end_date=end_date,
                weather_period_label=weather_label
            ))
        
        return periods
    
    def _generate_single_period(
        self,
        target_yyyymm: str,
        target_period: str
    ) -> List[PeriodInfo]:
        """
        Generate a single period for the target date.
        
        DESIGN CHANGE: This replaces the year-over-year multi-period approach.
        Now downloads ONLY the specified target period.
        
        For multiple periods, the orchestrator should call this step multiple times
        with different target_yyyymm and target_period values.
        
        Args:
            target_yyyymm: Target year-month (e.g., "202508")
            target_period: Target period half ("A" or "B")
            
        Returns:
            List[PeriodInfo]: Single-item list with the target period
            
        Example:
            Target: 202508A
            Returns: [PeriodInfo for Aug 1-15, 2025]
        """
        periods: List[PeriodInfo] = []
        
        # Normalize period
        base_period = self._normalize_period(target_period)
        
        # Parse target year and month
        year = int(target_yyyymm[:4])
        month = int(target_yyyymm[4:6])
        
        # Calculate date range for this period
        if base_period == 'A':
            start_date = f"{year:04d}-{month:02d}-01"
            end_date = f"{year:04d}-{month:02d}-15"
        else:  # 'B'
            last_day = self._last_day_of_month(year, month)
            start_date = f"{year:04d}-{month:02d}-16"
            end_date = f"{year:04d}-{month:02d}-{last_day:02d}"
        
        # Check if period is in the future
        today = date.today()
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        except Exception as e:
            self.logger.error(f"Invalid date format: {e}", self.repo_name)
            return []
        
        # Skip if period starts in the future
        if start_dt > today:
            self.logger.warning(
                f"Target period {target_yyyymm}{base_period} is in the future, skipping",
                self.repo_name
            )
            return []
        
        # Clamp end date to today if needed (for current period)
        if end_dt > today:
            self.logger.info(
                f"Target period {target_yyyymm}{base_period} is current, using data up to today",
                self.repo_name
            )
            end_date = today.isoformat()
        
        # Create period info
        period_label = f"{target_yyyymm}{base_period}"
        weather_label = f"{start_date.replace('-', '')}_to_{end_date.replace('-', '')}"
        
        periods.append(PeriodInfo(
            period_label=period_label,
            yyyymm=target_yyyymm,
            period_half=base_period,
            start_date=start_date,
            end_date=end_date,
            weather_period_label=weather_label
        ))
        
        self.logger.info(
            f"Generated single period: {period_label} ({start_date} to {end_date})",
            self.repo_name
        )
        
        return periods
    
    def _build_year_over_year_period_tuples(
        self,
        target_yyyymm: str,
        target_period: str,
        months_back: int
    ) -> List[Tuple[str, str, str, str]]:
        """
        Build list of (yyyymm, half, start_date, end_date) tuples.
        
        Args:
            target_yyyymm: Target year-month
            target_period: Target period half
            months_back: Number of months to look back
            
        Returns:
            List of period tuples
        """
        result: List[Tuple[str, str, str, str]] = []
        
        # Current periods (last N months up to target)
        current_periods = self._get_last_n_months_periods(
            target_yyyymm,
            target_period,
            months_back
        )
        
        for per in current_periods:
            y = int(per[:4])
            m = int(per[4:6])
            h = per[6]
            
            if h == 'A':
                start_date = f"{y:04d}-{m:02d}-01"
                end_date = f"{y:04d}-{m:02d}-15"
            else:
                ld = self._last_day_of_month(y, m)
                start_date = f"{y:04d}-{m:02d}-16"
                end_date = f"{y:04d}-{m:02d}-{ld:02d}"
            
            result.append((f"{y:04d}{m:02d}", h, start_date, end_date))
        
        # Historical periods: Same N months from previous year
        # CRITICAL: We need the SAME months from previous year, not the next months
        # Example: Target 202508A → need 202408A/B (not 202409A/B)
        # Reason: For planning the next period (202508B), we need last year's equivalent (202408B)
        cy = int(target_yyyymm[:4])
        cm = int(target_yyyymm[4:6])
        hy = cy - 1
        
        # Start from the SAME month as target, but previous year
        # This gives us the historical equivalent for planning purposes
        start_y, start_m = hy, cm
        
        # Go back (months_back - 1) to get the start of the N-month window
        # This mirrors the logic in _get_last_n_months_periods
        for _ in range(months_back - 1):
            start_m -= 1
            if start_m < 1:
                start_m = 12
                start_y -= 1
        
        y, m = start_y, start_m
        for _ in range(months_back):
            # A half
            start_date_a = f"{y:04d}-{m:02d}-01"
            end_date_a = f"{y:04d}-{m:02d}-15"
            result.append((f"{y:04d}{m:02d}", 'A', start_date_a, end_date_a))
            
            # B half
            ld = self._last_day_of_month(y, m)
            start_date_b = f"{y:04d}-{m:02d}-16"
            end_date_b = f"{y:04d}-{m:02d}-{ld:02d}"
            result.append((f"{y:04d}{m:02d}", 'B', start_date_b, end_date_b))
            
            # Next month
            m += 1
            if m > 12:
                m = 1
                y += 1
        
        return result
    
    def _get_last_n_months_periods(
        self,
        target_yyyymm: str,
        target_period: str,
        n_months: int
    ) -> List[str]:
        """
        Get chronological list of half-month periods for last N complete months.
        
        CRITICAL BUSINESS LOGIC - TARGET PERIOD SEMANTICS:
        ==================================================
        The target period represents the LAST COMPLETED PERIOD. This method ensures
        we always use historical data, even when the target period is specified as
        a future date (for planning purposes).
        
        Key Behaviors:
        1. **Always includes FULL target month** (both A and B halves)
           - Ensures complete data for the target month
           - Example: Target 202508A includes both 202508A and 202508B
        
        2. **Auto-shifts future targets to previous year**
           - If target is in the future, uses last year's equivalent
           - Example: Target 202508A in Oct 2024 → uses 202408A (Aug 2024)
           - Reason: We need FULL historical data for allocation planning
        
        3. **Generates N complete months**
           - Each month has 2 periods (A and B halves)
           - Returns chronological list of period labels
        
        Why This Matters:
        -----------------
        This pipeline allocates inventory for FUTURE periods. When users specify
        a target period, they mean "the last completed period I have data for."
        We need full historical data (not partial future data) to:
        - Calculate accurate temperature patterns
        - Perform year-over-year seasonal analysis
        - Generate reliable allocation recommendations
        
        Args:
            target_yyyymm: Target year-month (e.g., "202508")
                          May be in future for planning purposes
            target_period: Target period half ("A" or "B")
            n_months: Number of complete months to include (default: 3)
            
        Returns:
            List[str]: Period labels for n_months complete months
            
        Examples:
            Target 202508A (Aug 2025), today Oct 2024, n_months=3:
            → Returns: ['202406A', '202406B', '202407A', '202407B', '202408A', '202408B']
            → (June-Aug 2024, shifted from future 2025 to historical 2024)
            
            Target 202410A (Oct 2024), today Oct 2024, n_months=3:
            → Returns: ['202408A', '202408B', '202409A', '202409B', '202410A', '202410B']
            → (Aug-Oct 2024, no shift needed as target is current/past)
        """
        periods: List[str] = []
        target_year = int(target_yyyymm[:4])
        target_month = int(target_yyyymm[4:6])
        
        # CRITICAL: Check if target is in the future
        # If target period hasn't been completed yet, we shift to previous year
        # to ensure we have FULL historical data for allocation planning
        today = date.today()
        target_date = date(target_year, target_month, 15 if target_period == 'A' else 20)
        
        # Auto-shift future targets to previous year's equivalent
        # Example: Target 202508A in Oct 2024 → use 202408A (Aug 2024)
        # Reason: Pipeline needs complete data for future allocation planning
        if target_date > today:
            target_year -= 1
            self.logger.info(
                f"Target {target_yyyymm}{target_period} is in future, using historical equivalent {target_year:04d}{target_month:02d}{target_period}",
                self.repo_name
            )
        
        # Calculate start month: go back (n_months - 1) from target
        # This ensures we get N complete months ending with the target month
        # Example: target=Aug, n_months=3 → start=June (Jun, Jul, Aug = 3 months)
        year, month = target_year, target_month
        
        # Go back (n_months - 1) months to find start month
        for _ in range(n_months - 1):
            month -= 1
            if month < 1:
                month = 12
                year -= 1
        
        # Generate N complete months (2 half-month periods per month)
        # Each month contributes both A (1-15) and B (16-end) periods
        # This ensures we have complete data for each month
        for _ in range(n_months):
            periods.append(f"{year:04d}{month:02d}A")  # First half of month
            periods.append(f"{year:04d}{month:02d}B")  # Second half of month
            
            # Move to next month
            month += 1
            if month > 12:
                month = 1
                year += 1
        
        return periods
    
    @staticmethod
    def _last_day_of_month(year: int, month: int) -> int:
        """Get last day of month."""
        return calendar.monthrange(year, month)[1]
    
    @staticmethod
    def _normalize_period(period: Optional[str]) -> str:
        """Normalize period to 'A' or 'B'."""
        if period == 'A':
            return 'A'
        return 'B'
    
    def _collect_altitude_data(self, coords_df: pd.DataFrame) -> pd.DataFrame:
        """
        Collect altitude data for all store locations.
        
        Args:
            coords_df: DataFrame with store coordinates
            
        Returns:
            pd.DataFrame: DataFrame with store codes and altitude data
        """
        # Try to load existing altitude data
        try:
            existing_altitude_df = self.altitude_repo.get_all()
            existing_stores = set(existing_altitude_df['store_code'].astype(str))
            required_stores = set(coords_df['str_code'].astype(str))
            missing_stores = required_stores - existing_stores
            
            if len(missing_stores) == 0:
                self.logger.info(
                    f"All {len(existing_stores)} stores already have altitude data",
                    self.repo_name
                )
                return existing_altitude_df
            
            self.logger.info(
                f"Found altitude for {len(existing_stores)} stores, "
                f"collecting {len(missing_stores)} more",
                self.repo_name
            )
            
            missing_coords = coords_df[coords_df['str_code'].astype(str).isin(missing_stores)]
            
        except Exception:
            # No existing data, collect all
            self.logger.info("No existing altitude data, collecting all", self.repo_name)
            existing_altitude_df = pd.DataFrame()
            missing_coords = coords_df
        
        # Get unique coordinates to minimize API calls
        unique_coords = missing_coords[['latitude', 'longitude']].drop_duplicates()
        
        self.logger.info(
            f"Collecting altitude for {len(unique_coords)} unique locations",
            self.repo_name
        )
        
        # Collect altitudes
        altitudes = []
        for i, (_, row) in enumerate(unique_coords.iterrows(), 1):
            elevation = self.weather_api_repo.get_elevation(
                row['latitude'],
                row['longitude']
            )
            
            altitudes.append({
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'altitude_meters': elevation
            })
            
            if i % 50 == 0:
                self.logger.info(
                    f"Collected altitude for {i}/{len(unique_coords)} locations",
                    self.repo_name
                )
            
            time.sleep(self.ALTITUDE_DELAY)
        
        if altitudes:
            new_altitude_df = pd.DataFrame(altitudes)
            
            # Merge with store codes
            new_stores_with_altitude = missing_coords.merge(
                new_altitude_df,
                on=['latitude', 'longitude'],
                how='left'
            )
            
            new_altitude_lookup = new_stores_with_altitude[['str_code', 'altitude_meters']].copy()
            new_altitude_lookup.columns = ['store_code', 'altitude_meters']
            
            # Combine with existing
            if not existing_altitude_df.empty:
                combined_altitude_df = pd.concat(
                    [existing_altitude_df, new_altitude_lookup],
                    ignore_index=True
                )
            else:
                combined_altitude_df = new_altitude_lookup
        else:
            combined_altitude_df = existing_altitude_df
        
        return combined_altitude_df
    
    def _download_period_with_vpn_support(
        self,
        period_info: PeriodInfo,
        coords_df: pd.DataFrame,
        progress: Dict,
        config: WeatherDataConfig
    ) -> List[pd.DataFrame]:
        """
        Download weather data for a single period with VPN switching support.
        
        Args:
            period_info: Period information
            coords_df: Store coordinates
            progress: Progress tracking dictionary
            config: Configuration object
            
        Returns:
            List of weather DataFrames
        """
        # Get stores that need downloading
        downloaded_stores = self._get_downloaded_stores_for_period(period_info)
        to_download = coords_df[~coords_df['str_code'].isin(downloaded_stores)]
        
        if len(to_download) == 0:
            self.logger.info(
                f"All stores already downloaded for {period_info.period_label}",
                self.repo_name
            )
            return []
        
        self.logger.info(
            f"Downloading {len(to_download)} stores for {period_info.period_label}",
            self.repo_name
        )
        
        # Download stats
        stats = DownloadStats()
        weather_data_list = []
        
        progress['current_period'] = period_info.period_label
        
        for idx, (_, store) in enumerate(to_download.iterrows()):
            store_code = str(store['str_code'])
            
            # Check for VPN switch need
            if config.enable_vpn_switching and self._check_vpn_switch_needed(stats.consecutive_failures, config):
                if not self._prompt_vpn_switch(period_info, stats.successful_downloads, len(to_download)):
                    self.logger.warning("Download aborted by user", self.repo_name)
                    break
                
                stats.consecutive_failures = 0
                stats.stores_processed_since_vpn = 0
                progress['vpn_switches'] += 1
                self.progress_repo.save(progress)
            
            # Download weather data for store
            try:
                weather_df = self._download_weather_for_store(
                    store_code,
                    store['latitude'],
                    store['longitude'],
                    period_info,
                    config
                )
                
                if weather_df is not None:
                    weather_data_list.append(weather_df)
                    stats.successful_downloads += 1
                    stats.consecutive_failures = 0
                    
                    if store_code not in progress['completed_stores']:
                        progress['completed_stores'].append(store_code)
                else:
                    stats.failed_downloads += 1
                    stats.consecutive_failures += 1
                    
                    if store_code not in progress['failed_stores']:
                        progress['failed_stores'].append(store_code)
                        
            except Exception as e:
                self.logger.error(
                    f"Error downloading {store_code}: {str(e)}",
                    self.repo_name
                )
                stats.failed_downloads += 1
                stats.consecutive_failures += 1
                
                if store_code not in progress['failed_stores']:
                    progress['failed_stores'].append(store_code)
            
            stats.stores_processed_since_vpn += 1
            total_processed = stats.successful_downloads + stats.failed_downloads
            
            # Log progress periodically
            if total_processed % self.LOG_INTERVAL == 0:
                self.logger.info(
                    f"Progress: {total_processed}/{len(to_download)} stores "
                    f"({stats.successful_downloads} success, {stats.failed_downloads} failed)",
                    self.repo_name
                )
            
            # Save progress periodically
            if total_processed % self.PROGRESS_SAVE_INTERVAL == 0:
                progress['last_update'] = datetime.now().isoformat()
                self.progress_repo.save(progress)
        
        # Period completion summary
        success_rate = (
            stats.successful_downloads / (stats.successful_downloads + stats.failed_downloads) * 100
            if (stats.successful_downloads + stats.failed_downloads) > 0
            else 0
        )
        
        self.logger.info(
            f"Period {period_info.period_label} completed: "
            f"{stats.successful_downloads}/{len(to_download)} successful ({success_rate:.1f}%)",
            self.repo_name
        )
        
        return weather_data_list
    
    def _download_weather_for_store(
        self,
        store_code: str,
        latitude: float,
        longitude: float,
        period_info: PeriodInfo,
        config: WeatherDataConfig
    ) -> Optional[pd.DataFrame]:
        """
        Download weather data for a single store with retry logic.
        
        Args:
            store_code: Store identifier
            latitude: Store latitude
            longitude: Store longitude
            period_info: Period information
            config: Configuration object
            
        Returns:
            pd.DataFrame or None: Weather data or None if failed
        """
        consecutive_rate_limits = 0
        
        for attempt in range(config.max_retries):
            try:
                if attempt > 0:
                    delay = self._get_random_delay(config) * (1.5 ** attempt)
                    self.logger.info(
                        f"Retry attempt {attempt + 1}, waiting {delay:.1f}s",
                        self.repo_name
                    )
                    time.sleep(delay)
                
                # Call weather API
                weather_df = self.weather_api_repo.fetch_weather_data(
                    latitude=latitude,
                    longitude=longitude,
                    start_date=period_info.start_date,
                    end_date=period_info.end_date,
                    store_code=store_code
                )
                
                # Save immediately (incremental persistence)
                self._save_weather_file(weather_df, store_code, latitude, longitude, period_info)
                
                # Apply delay between requests
                time.sleep(self._get_random_delay(config))
                
                return weather_df
                
            except Exception as e:
                error_msg = str(e)
                
                # Check for rate limiting
                if '429' in error_msg or 'rate limit' in error_msg.lower():
                    consecutive_rate_limits += 1
                    backoff_time = self._get_rate_limit_backoff(consecutive_rate_limits, config)
                    self.logger.warning(
                        f"Rate limit hit, backing off for {backoff_time:.1f}s",
                        self.repo_name
                    )
                    time.sleep(backoff_time)
                    continue
                
                self.logger.error(
                    f"API error for {store_code}: {error_msg}",
                    self.repo_name
                )
                
                if attempt == config.max_retries - 1:
                    # Log final failure
                    self.logger.error(
                        f"Failed to download {store_code} after {config.max_retries} attempts",
                        self.repo_name
                    )
                    return None
        
        return None
    
    def _save_weather_file(
        self,
        weather_df: pd.DataFrame,
        store_code: str,
        latitude: float,
        longitude: float,
        period_info: PeriodInfo
    ) -> None:
        """
        Save weather data to CSV file.
        
        Args:
            weather_df: Weather data DataFrame
            store_code: Store identifier
            latitude: Store latitude
            longitude: Store longitude
            period_info: Period information
        """
        try:
            self.weather_file_repo.save_weather_file(
                weather_df,
                store_code,
                latitude,
                longitude,
                period_info.weather_period_label
            )
            
            self.logger.debug(
                f"Saved weather data for {store_code} ({period_info.period_label})",
                self.repo_name
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to save weather file for {store_code}: {str(e)}",
                self.repo_name
            )
            raise WeatherDataError(f"Failed to save weather file for {store_code}") from e
    
    def _get_downloaded_stores_for_period(self, period_info: PeriodInfo) -> Set[str]:
        """
        Get set of stores already downloaded for a period.
        
        Args:
            period_info: Period information
            
        Returns:
            Set of store codes
        """
        try:
            return self.weather_file_repo.get_downloaded_stores_for_period(
                period_info.weather_period_label
            )
        except Exception as e:
            self.logger.warning(
                f"Error checking downloaded stores for {period_info.period_label}: {str(e)}",
                self.repo_name
            )
            # Return empty set on error (safe fallback - will re-download)
            return set()
    
    def _check_vpn_switch_needed(self, consecutive_failures: int, config: WeatherDataConfig) -> bool:
        """
        Check if VPN switch is recommended.
        
        Args:
            consecutive_failures: Number of consecutive failures
            config: Configuration object
            
        Returns:
            bool: True if VPN switch is needed
        """
        return consecutive_failures >= config.vpn_switch_threshold
    
    def _prompt_vpn_switch(
        self,
        period_info: PeriodInfo,
        completed_stores: int,
        total_stores: int
    ) -> bool:
        """
        Prompt user to switch VPN.
        
        Args:
            period_info: Current period information
            completed_stores: Number of completed stores
            total_stores: Total stores to process
            
        Returns:
            bool: True if user confirms, False to abort
        """
        self.logger.warning("🚨 API ACCESS BLOCKED - VPN SWITCH RECOMMENDED", self.repo_name)
        self.logger.info(
            f"Period: {period_info.period_label} ({period_info.start_date} to {period_info.end_date})",
            self.repo_name
        )
        self.logger.info(
            f"Progress: {completed_stores}/{total_stores} stores completed",
            self.repo_name
        )
        
        # In actual implementation, this would prompt for user input
        # For testing, we'll return True
        return True
    
    def _get_random_delay(self, config: WeatherDataConfig) -> float:
        """Get random delay between min and max."""
        return random.uniform(config.min_delay, config.max_delay)
    
    def _get_rate_limit_backoff(self, attempt: int, config: WeatherDataConfig) -> float:
        """Get exponential backoff time for rate limiting."""
        base_delay = min(
            config.rate_limit_backoff_max,
            config.rate_limit_backoff_min * (1.5 ** attempt)
        )
        return random.uniform(base_delay, base_delay * 1.2)
    
    def _load_existing_weather_for_period(
        self,
        period_info: PeriodInfo,
        coords_df: pd.DataFrame
    ) -> List[pd.DataFrame]:
        """
        Load existing weather files for a period.
        
        Args:
            period_info: Period information
            coords_df: Store coordinates DataFrame
            
        Returns:
            List of weather DataFrames
        """
        weather_data_list = []
        
        for _, row in coords_df.iterrows():
            store_code = str(row['str_code'])
            latitude = row['latitude']
            longitude = row['longitude']
            
            # Generate filename
            filename = self.weather_file_repo._generate_filename(
                store_code=store_code,
                latitude=latitude,
                longitude=longitude,
                period_label=period_info.weather_period_label
            )
            
            # Construct full path
            from pathlib import Path
            file_path = Path(self.weather_file_repo.output_dir) / "weather_data" / filename
            
            # Load if exists
            if file_path.exists():
                df = pd.read_csv(file_path)
                weather_data_list.append(df)
        
        return weather_data_list
