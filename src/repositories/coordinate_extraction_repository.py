#!/usr/bin/env python3
"""
Repository for extracting and validating store coordinates (Part of Over-engineered Modular Implementation - NOT RECOMMENDED).

⚠️ WARNING: This repository is part of an overly complex modular implementation that is not recommended for use.
Use src/steps/extract_coordinates.py for testing or src/step2_extract_coordinates.py for production instead.

This repository handles coordinate extraction from store sales data,
including validation and filtering of coordinate data to match legacy behavior.

RECOMMENDED ALTERNATIVE: Use src/steps/extract_coordinates.py for testing or src/step2_extract_coordinates.py for production.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import os

from src.repositories.base import ReadOnlyRepository
from src.core.logger import PipelineLogger
from src.core.exceptions import DataValidationError


@dataclass
class CoordinateData:
    """Data structure for coordinate information."""
    str_code: str
    longitude: float
    latitude: float


@dataclass
class ValidationResult:
    """Result of coordinate validation."""
    is_valid: bool
    error_message: Optional[str] = None
    missing_coordinates: List[str] = None
    coverage_percentage: float = 0.0


class CoordinateExtractionRepository(ReadOnlyRepository):
    """Repository for extracting and validating store coordinates."""

    # Constants
    COORDINATE_PRECISION = 6

    def __init__(self, base_data_path: str, logger: PipelineLogger):
        super().__init__(logger)
        self.base_data_path = base_data_path

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all extracted and validated coordinates."""
        # This repository doesn't use get_all in the traditional sense
        # Instead, it provides coordinate extraction services
        raise NotImplementedError("Use extract_coordinates_from_period or validate_coordinates instead")

    def extract_coordinates_from_period(self, yyyymm: str, half: str) -> List[CoordinateData]:
        """Extract coordinates from a specific period (matches legacy logic)."""
        period_label = f"{yyyymm}{half}"
        coordinates = []

        # Match legacy behavior: try multiple file paths for each data type
        search_paths = [
            self.base_data_path,  # data/api_data
            os.path.join(os.path.dirname(self.base_data_path), "output")  # output
        ]

        # Try to load store sales data with coordinates (matches legacy patterns)
        store_data = None
        potential_store_paths = [
            f"store_sales_{period_label}.csv",
            f"store_sales_data_{period_label}.csv"  # Alternative pattern from legacy
        ]

        for search_path in search_paths:
            if store_data is not None:
                break
            for filename in potential_store_paths:
                file_path = os.path.join(search_path, filename)
                if os.path.exists(file_path):
                    try:
                        store_data = pd.read_csv(file_path)
                        self.logger.info(f"Loaded store data from {file_path}", self.repo_name)
                        break
                    except Exception as e:
                        self.logger.warning(f"Error reading {file_path}: {str(e)}", self.repo_name)

        if store_data is None or 'long_lat' not in store_data.columns:
            self.logger.warning(f"No coordinate data found for period {period_label}", self.repo_name)
            return coordinates

        # Extract coordinates using legacy logic
        for _, row in store_data.iterrows():
            try:
                # The format is "longitude,latitude" (matches legacy)
                if pd.notna(row['long_lat']):
                    coord_str = str(row['long_lat']).strip()
                    if ',' in coord_str:
                        parts = coord_str.split(',')
                        if len(parts) == 2:
                            longitude, latitude = float(parts[0]), float(parts[1])
                            coordinates.append(CoordinateData(
                                str_code=str(row['str_code']),
                                longitude=longitude,
                                latitude=latitude
                            ))
            except Exception as e:
                self.logger.warning(f"Error parsing coordinates for store {row.get('str_code', 'unknown')}: {str(e)}", self.repo_name)

        self.logger.info(f"Extracted {len(coordinates)} valid coordinates from period {period_label}", self.repo_name)
        return coordinates

    def validate_coordinates(self, coordinates: List[CoordinateData], total_stores: int = None) -> ValidationResult:
        """Validate coordinate data format and completeness (matches legacy validation)."""
        if not coordinates:
            return ValidationResult(
                is_valid=False,
                error_message="No valid coordinates found",
                coverage_percentage=0.0
            )

        # Check coordinate ranges (basic validation)
        valid_coordinates = []
        invalid_coordinates = []

        for coord in coordinates:
            if self._is_valid_coordinate(coord):
                valid_coordinates.append(coord)
            else:
                invalid_coordinates.append(coord.str_code)

        if not valid_coordinates:
            return ValidationResult(
                is_valid=False,
                error_message="No valid coordinates after validation",
                missing_coordinates=invalid_coordinates,
                coverage_percentage=0.0
            )

        # Calculate coverage percentage
        coverage_percentage = (len(valid_coordinates) / total_stores * 100) if total_stores else 100.0

        return ValidationResult(
            is_valid=True,
            missing_coordinates=invalid_coordinates,
            coverage_percentage=coverage_percentage
        )

    def _is_valid_coordinate(self, coord: CoordinateData) -> bool:
        """Check if coordinate is within valid ranges."""
        # Basic validation: longitude between -180 and 180, latitude between -90 and 90
        return (-180 <= coord.longitude <= 180 and
                -90 <= coord.latitude <= 90)

    def find_best_period(self, period_data_list: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the period with maximum valid coordinates (matches legacy logic)."""
        if not period_data_list:
            return None

        best_period = None
        best_count = 0

        for period_info in period_data_list:
            yyyymm = period_info['yyyymm']
            half = period_info['half']
            coordinate_count = period_info.get('coordinate_count', 0)

            # Use the pre-calculated coordinate count for efficiency (like legacy)
            if coordinate_count > best_count:
                best_count = coordinate_count
                best_period = period_info

        if best_period:
            # Handle both dictionary and Mock object access
            yyyymm = getattr(best_period, 'yyyymm', 'unknown')
            half = getattr(best_period, 'half', 'unknown')
            self.logger.info(f"Selected best period: {yyyymm}{half} with {best_count} coordinates", self.repo_name)

        return best_period

    def create_coordinate_dataframe(self, coordinates: List[CoordinateData]) -> pd.DataFrame:
        """Create a pandas DataFrame from coordinate data (matches legacy schema)."""
        if not coordinates:
            return pd.DataFrame(columns=['str_code', 'longitude', 'latitude'])

        data = {
            'str_code': [coord.str_code for coord in coordinates],
            'longitude': [coord.longitude for coord in coordinates],
            'latitude': [coord.latitude for coord in coordinates]
        }

        df = pd.DataFrame(data)
        # Ensure string store codes (matches legacy)
        df['str_code'] = df['str_code'].astype(str)

        return df

    def extract_coordinates_from_dataframe(self, sales_df: pd.DataFrame) -> List[CoordinateData]:
        """Extract coordinates from a sales DataFrame (for testing scenarios)."""
        coordinates = []

        # Check if the DataFrame has coordinate data
        if 'long_lat' not in sales_df.columns:
            return coordinates

        # Extract coordinates from each row
        for _, row in sales_df.iterrows():
            try:
                str_code = str(row.get('str_code', ''))
                long_lat = str(row.get('long_lat', ''))

                if long_lat and ',' in long_lat:
                    parts = long_lat.split(',')
                    if len(parts) == 2:
                        longitude = float(parts[0].strip())
                        latitude = float(parts[1].strip())

                        if self._is_valid_coordinate(longitude, latitude):
                            coordinates.append(CoordinateData(
                                str_code=str_code,
                                longitude=round(longitude, self.COORDINATE_PRECISION),
                                latitude=round(latitude, self.COORDINATE_PRECISION)
                            ))
            except Exception as e:
                self.logger.debug(f"Failed to extract coordinates from row: {e}", self.repo_name)
                continue

        # Remove duplicates
        seen = set()
        unique_coordinates = []
        for coord in coordinates:
            coord_key = (coord.str_code, coord.longitude, coord.latitude)
            if coord_key not in seen:
                seen.add(coord_key)
                unique_coordinates.append(coord)

        self.logger.info(f"Extracted {len(unique_coordinates)} valid coordinates from DataFrame", self.repo_name)
        return unique_coordinates
