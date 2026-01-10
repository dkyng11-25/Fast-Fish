#!/usr/bin/env python3
"""
Repository for discovering and filtering available data periods.

This repository handles the complex logic for determining which periods to process,
including year-over-year calculations and period filtering to match legacy behavior.

⚠️ NOTE: This repository is used by the over-engineered modular implementation in steps/extract_coordinates_step.py.
For production use, consider src/step2_extract_coordinates.py (enhanced legacy) or src/steps/extract_coordinates.py (test-compatible).
"""

from __future__ import annotations
from typing import List, Tuple, Set, Optional, Dict, Any
import os
import glob
import pandas as pd
from datetime import datetime

from src.repositories.base import ReadOnlyRepository
from src.core.logger import PipelineLogger


class PeriodDiscoveryRepository(ReadOnlyRepository):
    """Repository for discovering and filtering available data periods."""

    def __init__(self, base_data_path: str, logger: PipelineLogger):
        super().__init__(logger)
        self.base_data_path = base_data_path

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all available periods matching legacy behavior."""
        # First get all available periods
        available_periods = self._discover_available_periods()
        self.logger.info(f"Found {len(available_periods)} available periods: {[f'{p[0]}{p[1]}' for p in available_periods]}", self.repo_name)

        # Then filter based on year-over-year logic
        target_periods = self._get_target_periods()
        self.logger.info(f"Target periods: {len(target_periods)} periods", self.repo_name)

        # Return only periods that are both available and in target set
        filtered_periods = self._filter_periods(available_periods, target_periods)
        self.logger.info(f"Filtered to {len(filtered_periods)} matching periods: {[f'{p[0]}{p[1]}' for p in filtered_periods]}", self.repo_name)

        # Count coordinates for each period (like legacy implementation does)
        period_info_list = []
        for p in filtered_periods:
            yyyymm, half = p[0], p[1]
            coordinate_count = self._count_coordinates_for_period(yyyymm, half)
            period_info_list.append({
                'yyyymm': yyyymm,
                'half': half,
                'coordinate_count': coordinate_count
            })

        return period_info_list

    def _discover_available_periods(self) -> List[Tuple[str, str]]:
        """Discover all available periods from file patterns (matches legacy behavior)."""
        found_periods: Set[Tuple[str, str]] = set()

        # Match legacy behavior: check both data/api_data and output directories
        search_paths = [
            self.base_data_path,  # data/api_data
            os.path.join(os.path.dirname(self.base_data_path), "output")  # output
        ]

        # Match legacy file patterns
        patterns = [
            "store_sales_*.csv",
            "store_sales_data_*.csv",  # Alternative pattern from legacy
            "complete_category_sales_*.csv",
            "complete_spu_sales_*.csv"
        ]

        for search_path in search_paths:
            if os.path.exists(search_path):
                for pattern in patterns:
                    full_pattern = os.path.join(search_path, pattern)
                    for file_path in glob.glob(full_pattern):
                        filename = os.path.basename(file_path)
                        period_part = self._extract_period_from_filename(filename)
                        if period_part:
                            yyyymm = period_part[:6]
                            half = period_part[6:] if len(period_part) > 6 else "A"
                            found_periods.add((yyyymm, half))

        periods = sorted(found_periods, key=lambda x: (x[0], x[1]))
        self.logger.info(f"Found {len(periods)} available periods: {[f'{p[0]}{p[1]}' for p in periods]}", self.repo_name)
        return periods

    def _extract_period_from_filename(self, filename: str) -> Optional[str]:
        """Extract period from filename (matches legacy logic)."""
        if filename.startswith("store_sales_"):
            return filename.replace("store_sales_", "").replace(".csv", "")
        elif filename.startswith("store_sales_data_"):
            return filename.replace("store_sales_data_", "").replace(".csv", "")
        elif filename.startswith("complete_category_sales_"):
            return filename.replace("complete_category_sales_", "").replace(".csv", "")
        elif filename.startswith("complete_spu_sales_"):
            return filename.replace("complete_spu_sales_", "").replace(".csv", "")
        return None

    def _get_target_periods(self) -> Set[str]:
        """Get target periods based on year-over-year logic (matches legacy)."""
        # Get environment variables (matches legacy logic)
        months_back = int(os.environ.get('COORDS_MONTHS_BACK', os.environ.get('WEATHER_MONTHS_BACK', '3')))

        # Get current period from config (matches legacy)
        try:
            from src.config import get_current_period
            base_yyyymm, base_period = get_current_period()
        except (ImportError, Exception):
            # Fallback if config not available
            current_period = os.environ.get('CURRENT_PERIOD', '202509A')
            base_yyyymm = current_period[:6]
            base_period = current_period[6:] or 'A'

        # Check if we have a valid current period (matches legacy fallback behavior)
        if not base_yyyymm or not base_period:
            # Legacy fallback: if no current period configured, use all available periods
            self.logger.warning("No current period configured, using all available periods", self.repo_name)
            available_periods = self._discover_available_periods()
            return set(f'{p[0]}{p[1]}' for p in available_periods)

        # Normalize: treat None/full as 'B' to include full month end
        base_half = base_period if base_period in ['A', 'B'] else 'B'

        # Calculate year-over-year periods (matches legacy helpers)
        current_periods = self._last_n_half_months(base_yyyymm, base_half, months_back)
        yoy_periods = self._next_n_months_last_year(base_yyyymm, months_back)

        target_periods = current_periods + yoy_periods
        target_period_set = set(f'{p[0]}{p[1]}' for p in target_periods)

        self.logger.info(f"Target periods: {[f'{p[0]}{p[1]}' for p in target_periods]}", self.repo_name)
        return target_period_set

    def _filter_periods(self, available_periods: List[Tuple[str, str]], target_periods: Set[str]) -> List[Tuple[str, str]]:
        """Filter available periods to only those in target set."""
        matching_periods = [p for p in available_periods if f'{p[0]}{p[1]}' in target_periods]
        self.logger.info(f"Filtered to {len(matching_periods)} matching periods: {[f'{p[0]}{p[1]}' for p in matching_periods]}", self.repo_name)
        return matching_periods

    def _last_n_half_months(self, yyyymm: str, half: str, n_months: int) -> List[Tuple[str, str]]:
        """Helper: last N months in half-month steps ending at (yyyymm, half)."""
        result: List[Tuple[str, str]] = []
        total_halves = n_months * 2
        y = int(yyyymm[:4])
        m = int(yyyymm[4:6])
        h = half
        for _ in range(total_halves):
            result.append((f"{y:04d}{m:02d}", h))
            if h == 'B':
                h = 'A'
            else:
                h = 'B'
                m -= 1
                if m < 1:
                    m = 12
                    y -= 1
        result.reverse()
        return result

    def _count_coordinates_for_period(self, yyyymm: str, half: str) -> int:
        """Count valid coordinates for a specific period (matches legacy behavior)."""
        period_label = f"{yyyymm}{half}"

        # Try to find store sales data with coordinates (like legacy implementation)
        potential_paths = [
            os.path.join(self.base_data_path, f"store_sales_{period_label}.csv"),
            os.path.join(os.path.dirname(self.base_data_path), "output", f"store_sales_{period_label}.csv"),
            os.path.join(self.base_data_path, f"store_sales_data_{period_label}.csv")
        ]

        for path in potential_paths:
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path)
                    if 'long_lat' in df.columns:
                        # Count only rows with non-empty, valid coordinate strings (like legacy)
                        coord_series = df['long_lat'].astype(str)
                        valid_mask = coord_series.str.contains(',', na=False) & (coord_series.str.strip() != '')
                        stores_with_coords = df.loc[valid_mask]
                        unique_stores = stores_with_coords.drop_duplicates(subset=['str_code'])
                        return len(unique_stores)
                except Exception as e:
                    self.logger.debug(f"Error reading {path}: {e}", self.repo_name)

        # If no coordinates found, return 0
        return 0

    def _next_n_months_last_year(self, yyyymm: str, n_months: int) -> List[Tuple[str, str]]:
        """Helper: next N months from previous year, returning both A and B halves for each month."""
        result: List[Tuple[str, str]] = []
        y = int(yyyymm[:4]) - 1
        m = int(yyyymm[4:6])
        for _ in range(n_months):
            result.append((f"{y:04d}{m:02d}", 'A'))
            result.append((f"{y:04d}{m:02d}", 'B'))
            m += 1
            if m > 12:
                m = 1
                y += 1
        return result
