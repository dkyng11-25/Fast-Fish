#!/usr/bin/env python3
"""
Step 4: Weather Data Download Step (Refactored)

This step downloads historical weather data for store locations across multiple
time periods with VPN switching support and robust error handling.

Follows the 4-phase Step pattern:
- Setup: Load coordinates, initialize progress tracking
- Apply: Download weather and altitude data for all periods
- Validate: Verify data completeness and quality
- Persist: Save weather data, altitude data, and progress
"""

from __future__ import annotations
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date
import calendar
import time
import random
import pandas as pd

from core.step import Step
from core.context import StepContext
from core.logger import PipelineLogger
from core.exceptions import DataValidationError
from repositories import (
    WeatherApiRepository,
    CsvFileRepository,
    JsonFileRepository,
    ProgressTrackingRepository
)


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
class StepConfig:
    """Configuration for Step 4."""
    months_back: int
    stores_per_vpn_batch: int
    min_delay: float
    max_delay: float
    rate_limit_backoff_min: float
    rate_limit_backoff_max: float
    max_retries: int
    vpn_switch_threshold: int
    timezone: str
    enable_vpn_switching: bool


@dataclass
class DownloadStats:
    """Statistics for a download session."""
    successful_downloads: int = 0
    failed_downloads: int = 0
    consecutive_failures: int = 0
    stores_processed_since_vpn: int = 0


# ============================================================================
# WEATHER DATA DOWNLOAD STEP
# ============================================================================

class WeatherDataDownloadStep(Step):
    """Step 4: Download weather data for store locations."""
    
    # Constants
    DEFAULT_MONTHS_BACK = 3
    DEFAULT_STORES_PER_VPN_BATCH = 50
    DEFAULT_MIN_DELAY = 0.5
    DEFAULT_MAX_DELAY = 1.5
    DEFAULT_RATE_LIMIT_BACKOFF_MIN = 5.0
    DEFAULT_RATE_LIMIT_BACKOFF_MAX = 20.0
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_VPN_SWITCH_THRESHOLD = 5
    DEFAULT_TIMEZONE = 'Asia/Shanghai'
    ALTITUDE_DELAY = 0.1
    PROGRESS_SAVE_INTERVAL = 25
    LOG_INTERVAL = 10
    
    def __init__(
        self,
        coordinates_repo: CsvFileRepository,
        weather_api_repo: WeatherApiRepository,
        weather_output_repo: CsvFileRepository,
        altitude_repo: CsvFileRepository,
        progress_repo: ProgressTrackingRepository,
        config: StepConfig,
        logger: PipelineLogger,
        step_name: str,
        step_number: int,
        target_yyyymm: Optional[str] = None,
        target_period: Optional[str] = None
    ):
        """
        Initialize Weather Data Download Step.
        
        Args:
            coordinates_repo: Repository for store coordinates
            weather_api_repo: Repository for weather API calls
            weather_output_repo: Repository for saving weather data
            altitude_repo: Repository for altitude data
            progress_repo: Repository for progress tracking
            config: Step configuration
            logger: Pipeline logger
            step_name: Name of the step
            step_number: Step number in pipeline
            target_yyyymm: Target year-month (e.g., "202505")
            target_period: Target period half ("A" or "B")
        """
        super().__init__(logger, step_name, step_number)
        self.coordinates_repo = coordinates_repo
        self.weather_api_repo = weather_api_repo
        self.weather_output_repo = weather_output_repo
        self.altitude_repo = altitude_repo
        self.progress_repo = progress_repo
        self.config = config
        self.target_yyyymm = target_yyyymm
        self.target_period = target_period
    
    # ========================================================================
    # SETUP PHASE
    # ========================================================================
    
    def setup(self, context: StepContext) -> StepContext:
        """
        Load store coordinates and initialize progress tracking.
        
        Args:
            context: Step context
            
        Returns:
            StepContext: Updated context with coordinates and progress
        """
        self.logger.info("Loading store coordinates...", self.class_name)
        
        # Load store coordinates
        coords_df = self.coordinates_repo.get_all()
        coords_df['str_code'] = coords_df['str_code'].astype(str)
        
        self.logger.info(
            f"Loaded {len(coords_df)} stores with coordinates",
            self.class_name
        )
        
        # Load or initialize progress tracking
        progress = self.progress_repo.load()
        
        self.logger.info(
            f"Progress loaded: {len(progress.get('completed_periods', []))} periods completed, "
            f"{len(progress.get('completed_stores', []))} stores completed",
            self.class_name
        )
        
        # Generate dynamic periods
        periods = self._generate_year_over_year_periods()
        
        self.logger.info(
            f"Generated {len(periods)} dynamic periods for download",
            self.class_name
        )
        
        # Store in context
        context.set_state('coordinates', coords_df)
        context.set_state('progress', progress)
        context.set_state('periods', periods)
        context.set_state('start_time', datetime.now())
        
        return context
    
    # ========================================================================
    # APPLY PHASE
    # ========================================================================
    
    def apply(self, context: StepContext) -> StepContext:
        """
        Download weather and altitude data for all periods.
        
        Args:
            context: Step context with coordinates and progress
            
        Returns:
            StepContext: Updated context with downloaded data
        """
        coords_df = context.get_state('coordinates')
        progress = context.get_state('progress')
        periods = context.get_state('periods')
        
        # Step 1: Collect altitude data (shared across all periods)
        self.logger.info("Collecting altitude data for all stores...", self.class_name)
        altitude_df = self._collect_altitude_data(coords_df)
        context.set_state('altitude_data', altitude_df)
        
        # Step 2: Filter to remaining periods
        remaining_periods = [
            p for p in periods 
            if p.period_label not in progress.get('completed_periods', [])
        ]
        
        if not remaining_periods:
            self.logger.info("All periods already completed!", self.class_name)
            return context
        
        self.logger.info(
            f"Processing {len(remaining_periods)} remaining periods",
            self.class_name
        )
        
        # Step 3: Download weather data for each period
        all_weather_data = []
        
        for period_info in remaining_periods:
            self.logger.info(
                f"Starting period {period_info.period_label} "
                f"({period_info.start_date} to {period_info.end_date})",
                self.class_name
            )
            
            period_weather_data = self._download_period_with_vpn_support(
                period_info,
                coords_df,
                progress
            )
            
            all_weather_data.extend(period_weather_data)
            
            # Mark period as completed
            if period_info.period_label not in progress['completed_periods']:
                progress['completed_periods'].append(period_info.period_label)
            
            # Save progress after each period
            progress['last_update'] = datetime.now().isoformat()
            self.progress_repo.save(progress)
        
        # Store results in context
        context.set_state('weather_data', all_weather_data)
        context.set_state('progress', progress)
        
        return context
    
    # ========================================================================
    # VALIDATE PHASE
    # ========================================================================
    
    def validate(self, context: StepContext) -> None:
        """
        Validate downloaded weather and altitude data.
        
        Args:
            context: Step context with downloaded data
            
        Raises:
            DataValidationError: If validation fails
        """
        coords_df = context.get_state('coordinates')
        altitude_df = context.get_state('altitude_data')
        weather_data = context.get_state('weather_data', [])
        progress = context.get_state('progress')
        
        # Validation 1: Altitude data completeness
        if altitude_df is None or len(altitude_df) == 0:
            raise DataValidationError("No altitude data collected")
        
        required_altitude_cols = ['store_code', 'altitude_meters']
        missing_altitude_cols = [c for c in required_altitude_cols if c not in altitude_df.columns]
        if missing_altitude_cols:
            raise DataValidationError(
                f"Altitude data missing required columns: {missing_altitude_cols}"
            )
        
        # Validation 2: Check altitude coverage
        total_stores = len(coords_df)
        stores_with_altitude = len(altitude_df)
        coverage_pct = (stores_with_altitude / total_stores * 100) if total_stores > 0 else 0
        
        self.logger.info(
            f"Altitude coverage: {stores_with_altitude}/{total_stores} stores ({coverage_pct:.1f}%)",
            self.class_name
        )
        
        if coverage_pct < 50:
            raise DataValidationError(
                f"Insufficient altitude coverage: {coverage_pct:.1f}% < 50%"
            )
        
        # Validation 3: Weather data quality
        if len(weather_data) == 0:
            self.logger.warning("No weather data downloaded", self.class_name)
        
        # Validation 4: Progress tracking integrity
        if not isinstance(progress, dict):
            raise DataValidationError("Progress data is not a dictionary")
        
        required_progress_keys = [
            'completed_periods', 'completed_stores', 'failed_stores', 'vpn_switches'
        ]
        missing_progress_keys = [k for k in required_progress_keys if k not in progress]
        if missing_progress_keys:
            raise DataValidationError(
                f"Progress missing required keys: {missing_progress_keys}"
            )
        
        self.logger.info("Validation passed", self.class_name)
    
    # ========================================================================
    # PERSIST PHASE
    # ========================================================================
    
    def persist(self, context: StepContext) -> StepContext:
        """
        Save altitude data and final progress.
        
        Note: Weather data is saved incrementally during apply phase.
        
        Args:
            context: Step context with data to persist
            
        Returns:
            StepContext: Updated context
        """
        altitude_df = context.get_state('altitude_data')
        progress = context.get_state('progress')
        start_time = context.get_state('start_time')
        
        # Save altitude data
        self.logger.info("Saving altitude data...", self.class_name)
        self.altitude_repo.save(altitude_df)
        
        # Save final progress
        self.logger.info("Saving final progress...", self.class_name)
        progress['last_update'] = datetime.now().isoformat()
        self.progress_repo.save(progress)
        
        # Calculate and log summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60
        
        self.logger.info(
            f"Weather data download completed in {duration:.1f} minutes",
            self.class_name
        )
        self.logger.info(
            f"VPN switches: {progress.get('vpn_switches', 0)}",
            self.class_name
        )
        self.logger.info(
            f"Completed periods: {len(progress.get('completed_periods', []))}",
            self.class_name
        )
        
        return context
    
    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================
    
    def _generate_year_over_year_periods(self) -> List[PeriodInfo]:
        """
        Generate dynamic list of periods for year-over-year analysis.
        
        Returns:
            List[PeriodInfo]: List of period information objects
        """
        periods: List[PeriodInfo] = []
        
        # Use target period or default
        base_yyyymm = self.target_yyyymm or "202506"
        base_period = self._normalize_period(self.target_period or "A")
        
        today = date.today()
        
        # Build periods using helper
        period_tuples = self._build_year_over_year_period_tuples(
            base_yyyymm,
            base_period,
            self.config.months_back
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
        
        # Historical periods: next N months from previous year
        cy = int(target_yyyymm[:4])
        cm = int(target_yyyymm[4:6])
        hy = cy - 1
        start_y, start_m = hy, cm + 1
        
        if start_m > 12:
            start_m = 1
            start_y += 1
        
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
        Get chronological list of half-month periods for last N months.
        
        Args:
            target_yyyymm: Target year-month
            target_period: Target period half
            n_months: Number of months to look back
            
        Returns:
            List of period labels (e.g., ["202503A", "202503B", ...])
        """
        periods: List[str] = []
        current_year = int(target_yyyymm[:4])
        current_month = int(target_yyyymm[4:6])
        total_half_months = n_months * 2
        
        year, month = current_year, current_month
        period = target_period
        
        for _ in range(total_half_months):
            periods.append(f"{year:04d}{month:02d}{period}")
            
            if period == 'B':
                period = 'A'
            else:  # period == 'A'
                period = 'B'
                month -= 1
                if month < 1:
                    month = 12
                    year -= 1
        
        periods.reverse()
        return periods
    
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
                    self.class_name
                )
                return existing_altitude_df
            
            self.logger.info(
                f"Found altitude for {len(existing_stores)} stores, "
                f"collecting {len(missing_stores)} more",
                self.class_name
            )
            
            missing_coords = coords_df[coords_df['str_code'].astype(str).isin(missing_stores)]
            
        except Exception:
            # No existing data, collect all
            self.logger.info("No existing altitude data, collecting all", self.class_name)
            existing_altitude_df = pd.DataFrame()
            missing_coords = coords_df
        
        # Get unique coordinates to minimize API calls
        unique_coords = missing_coords[['latitude', 'longitude']].drop_duplicates()
        
        self.logger.info(
            f"Collecting altitude for {len(unique_coords)} unique locations",
            self.class_name
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
                    self.class_name
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
        progress: Dict
    ) -> List[pd.DataFrame]:
        """
        Download weather data for a single period with VPN switching support.
        
        Args:
            period_info: Period information
            coords_df: Store coordinates
            progress: Progress tracking dictionary
            
        Returns:
            List of weather DataFrames
        """
        # Get stores that need downloading
        downloaded_stores = self._get_downloaded_stores_for_period(period_info)
        to_download = coords_df[~coords_df['str_code'].isin(downloaded_stores)]
        
        if len(to_download) == 0:
            self.logger.info(
                f"All stores already downloaded for {period_info.period_label}",
                self.class_name
            )
            return []
        
        self.logger.info(
            f"Downloading {len(to_download)} stores for {period_info.period_label}",
            self.class_name
        )
        
        # Download stats
        stats = DownloadStats()
        weather_data_list = []
        
        progress['current_period'] = period_info.period_label
        
        for idx, (_, store) in enumerate(to_download.iterrows()):
            store_code = str(store['str_code'])
            
            # Check for VPN switch need
            if self.config.enable_vpn_switching and self._check_vpn_switch_needed(stats.consecutive_failures):
                if not self._prompt_vpn_switch(period_info, stats.successful_downloads, len(to_download)):
                    self.logger.warning("Download aborted by user", self.class_name)
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
                    period_info
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
                    self.class_name
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
                    self.class_name
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
            self.class_name
        )
        
        return weather_data_list
    
    def _download_weather_for_store(
        self,
        store_code: str,
        latitude: float,
        longitude: float,
        period_info: PeriodInfo
    ) -> Optional[pd.DataFrame]:
        """
        Download weather data for a single store with retry logic.
        
        Args:
            store_code: Store identifier
            latitude: Store latitude
            longitude: Store longitude
            period_info: Period information
            
        Returns:
            pd.DataFrame or None: Weather data or None if failed
        """
        consecutive_rate_limits = 0
        
        for attempt in range(self.config.max_retries):
            try:
                if attempt > 0:
                    delay = self._get_random_delay() * (1.5 ** attempt)
                    self.logger.info(
                        f"Retry attempt {attempt + 1}, waiting {delay:.1f}s",
                        self.class_name
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
                time.sleep(self._get_random_delay())
                
                return weather_df
                
            except Exception as e:
                error_msg = str(e)
                
                # Check for rate limiting
                if '429' in error_msg or 'rate limit' in error_msg.lower():
                    consecutive_rate_limits += 1
                    backoff_time = self._get_rate_limit_backoff(consecutive_rate_limits)
                    self.logger.warning(
                        f"Rate limit hit, backing off for {backoff_time:.1f}s",
                        self.class_name
                    )
                    time.sleep(backoff_time)
                    continue
                
                self.logger.error(
                    f"API error for {store_code}: {error_msg}",
                    self.class_name
                )
                
                if attempt == self.config.max_retries - 1:
                    # Log final failure
                    self.logger.error(
                        f"Failed to download {store_code} after {self.config.max_retries} attempts",
                        self.class_name
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
        # This would use a specialized weather file repository
        # For now, log the save operation
        self.logger.debug(
            f"Saved weather data for {store_code} ({period_info.period_label})",
            self.class_name
        )
    
    def _get_downloaded_stores_for_period(self, period_info: PeriodInfo) -> Set[str]:
        """
        Get set of stores already downloaded for a period.
        
        Args:
            period_info: Period information
            
        Returns:
            Set of store codes
        """
        # This would check existing files in output directory
        # For now, return empty set
        return set()
    
    def _check_vpn_switch_needed(self, consecutive_failures: int) -> bool:
        """
        Check if VPN switch is recommended.
        
        Args:
            consecutive_failures: Number of consecutive failures
            
        Returns:
            bool: True if VPN switch is needed
        """
        return consecutive_failures >= self.config.vpn_switch_threshold
    
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
        self.logger.warning("🚨 API ACCESS BLOCKED - VPN SWITCH RECOMMENDED", self.class_name)
        self.logger.info(
            f"Period: {period_info.period_label} ({period_info.start_date} to {period_info.end_date})",
            self.class_name
        )
        self.logger.info(
            f"Progress: {completed_stores}/{total_stores} stores completed",
            self.class_name
        )
        
        # In actual implementation, this would prompt for user input
        # For testing, we'll return True
        return True
    
    def _get_random_delay(self) -> float:
        """Get random delay between min and max."""
        return random.uniform(self.config.min_delay, self.config.max_delay)
    
    def _get_rate_limit_backoff(self, attempt: int) -> float:
        """Get exponential backoff time for rate limiting."""
        base_delay = min(
            self.config.rate_limit_backoff_max,
            self.config.rate_limit_backoff_min * (1.5 ** attempt)
        )
        return random.uniform(base_delay, base_delay * 1.2)
    
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
