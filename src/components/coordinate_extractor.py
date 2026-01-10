#!/usr/bin/env python3
"""
Coordinate Extractor Module (Part of Over-engineered Modular Implementation - NOT RECOMMENDED)

⚠️ WARNING: This module is part of an overly complex modular implementation that is not recommended for use.
Use src/steps/extract_coordinates.py for testing or src/step2_extract_coordinates.py for production instead.

Purpose: Extract and validate store coordinates from API data with comprehensive
validation and synthetic data support. This module handles the coordinate-specific
logic separately from SPU metadata processing for better modularity.

Standards Compliance: Follows code design standards with repository pattern,
comprehensive validation, and proper error handling.

RECOMMENDED ALTERNATIVE: Use src/steps/extract_coordinates.py for testing or src/step2_extract_coordinates.py for production.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
from tqdm import tqdm

from core.logger import PipelineLogger
from core.exceptions import DataValidationError
from repositories.base import Repository


@dataclass
class CoordinateExtractionResult:
    """Result of coordinate extraction operation."""
    coordinates_df: pd.DataFrame
    validation_summary: Dict[str, Any]
    processing_metadata: Dict[str, Any]


@dataclass
class CoordinateValidationData:
    """Comprehensive coordinate validation results."""
    original_count: int
    valid_count: int
    invalid_count: int
    validation_errors: List[str]
    validated_coordinates: pd.DataFrame
    coordinate_ranges: Dict[str, Tuple[float, float]]
    synthetic_data_detected: bool


class CoordinateExtractor:
    """
    Extract and validate store coordinates from API data.

    Purpose: Handle all coordinate-specific processing including parsing,
    validation, and quality assessment. This class focuses solely on coordinate
    data extraction and validation, maintaining separation of concerns from
    SPU metadata processing.
    """

    # Coordinate format specifications
    COORDINATE_COLUMN = "long_lat"
    LONGITUDE_RANGE = (-180.0, 180.0)
    LATITUDE_RANGE = (-90.0, 90.0)
    COORDINATE_PRECISION = 6

    def __init__(self, logger: PipelineLogger):
        """
        Initialize the coordinate extractor.

        Args:
            logger: Pipeline logger for consistent logging
        """
        self.logger = logger
        self.class_name = self.__class__.__name__

    def extract_coordinates(self, sales_df: pd.DataFrame) -> CoordinateExtractionResult:
        """
        Extract and validate coordinates from sales data.

        Purpose: Parse coordinate information from API data, validate ranges,
        and provide comprehensive validation results. Handles both real API
        data and synthetic test data formats.

        Args:
            sales_df: Sales DataFrame containing coordinate information

        Returns:
            CoordinateExtractionResult with validated coordinates and metadata

        Raises:
            DataValidationError: If critical coordinate validation fails
        """
        self.logger.info("Starting coordinate extraction and validation", self.class_name)

        # Extract raw coordinates
        raw_coordinates = self._parse_coordinates_from_sales(sales_df)

        if raw_coordinates.empty:
            raise DataValidationError("No coordinate data found in sales records")

        # Perform comprehensive validation
        validation_data = self._validate_coordinate_data(raw_coordinates)

        # Create final result
        result = CoordinateExtractionResult(
            coordinates_df=validation_data.validated_coordinates,
            validation_summary=self._create_validation_summary(validation_data),
            processing_metadata={
                'total_records_processed': len(sales_df),
                'raw_coordinates_found': validation_data.original_count,
                'valid_coordinates': validation_data.valid_count,
                'synthetic_data_detected': validation_data.synthetic_data_detected
            }
        )

        self.logger.info(f"Extracted and validated {len(result.coordinates_df)} coordinates", self.class_name)
        return result

    def _parse_coordinates_from_sales(self, sales_df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse coordinate data from sales DataFrame.

        Purpose: Extract coordinate information from multiple possible formats:
        - Standard API format: "longitude,latitude" string
        - Synthetic data format: individual longitude/latitude columns
        - Enhanced metadata: elevation, accuracy, source information

        Args:
            sales_df: Sales DataFrame with coordinate information

        Returns:
            DataFrame with parsed coordinate data
        """
        coordinates = []

        # Check available coordinate formats
        has_long_lat_column = self.COORDINATE_COLUMN in sales_df.columns
        has_individual_columns = 'longitude' in sales_df.columns and 'latitude' in sales_df.columns

        if not has_long_lat_column and not has_individual_columns:
            self.logger.warning("No coordinate columns found", self.class_name)
            return pd.DataFrame()

        for _, row in tqdm(sales_df.iterrows(), total=len(sales_df), desc="Parsing coordinates"):
            try:
                str_code = str(row.get('str_code', ''))
                longitude, latitude = None, None

                # Try individual columns first (synthetic data format)
                if has_individual_columns:
                    try:
                        longitude = float(row.get('longitude', 0))
                        latitude = float(row.get('latitude', 0))
                    except (ValueError, TypeError):
                        pass

                # Fall back to long_lat column parsing
                if longitude is None and has_long_lat_column:
                    coord_string = str(row.get(self.COORDINATE_COLUMN, '')).strip()
                    if coord_string and ',' in coord_string:
                        parts = coord_string.split(',')
                        if len(parts) == 2:
                            try:
                                longitude = float(parts[0].strip())
                                latitude = float(parts[1].strip())
                            except (ValueError, TypeError):
                                pass

                # Validate and add coordinate
                if longitude is not None and latitude is not None:
                    if self._is_valid_coordinate(longitude, latitude):
                        coordinate_record = {
                            'str_code': str_code,
                            'longitude': round(longitude, self.COORDINATE_PRECISION),
                            'latitude': round(latitude, self.COORDINATE_PRECISION)
                        }

                        # Add enhanced coordinate metadata
                        self._add_coordinate_metadata(coordinate_record, row, sales_df.columns)
                        coordinates.append(coordinate_record)

            except Exception as e:
                self.logger.debug(f"Failed to process coordinates for store {str_code}: {e}", self.class_name)
                continue

        # Remove duplicates and return
        coords_df = pd.DataFrame(coordinates)
        if not coords_df.empty:
            coords_df = coords_df.drop_duplicates(subset=['str_code'])

        self.logger.info(f"Parsed {len(coords_df)} coordinate records", self.class_name)
        return coords_df

    def _is_valid_coordinate(self, longitude: float, latitude: float) -> bool:
        """Validate coordinate ranges."""
        return (self.LONGITUDE_RANGE[0] <= longitude <= self.LONGITUDE_RANGE[1] and
                self.LATITUDE_RANGE[0] <= latitude <= self.LATITUDE_RANGE[1])

    def _add_coordinate_metadata(self, coordinate_record: Dict[str, Any],
                                row: pd.Series, available_columns: List[str]) -> None:
        """Add enhanced coordinate metadata."""
        # Add coordinate quality indicators
        for col in available_columns:
            if col.startswith('coord_') or col in ['elevation', 'accuracy', 'source', 'precision']:
                try:
                    coordinate_record[col] = row.get(col)
                except:
                    pass

    def _validate_coordinate_data(self, coords_df: pd.DataFrame) -> CoordinateValidationData:
        """
        Perform comprehensive coordinate validation.

        Purpose: Validate coordinate data quality including range checks,
        format validation, and synthetic data detection. Provides detailed
        validation results for downstream processing.

        Args:
            coords_df: Coordinate DataFrame to validate

        Returns:
            CoordinateValidationData with comprehensive validation results
        """
        validation_errors = []
        validated_coordinates = []
        original_count = len(coords_df)

        # Check for synthetic data indicators
        synthetic_data_detected = self._detect_synthetic_data(coords_df)

        for idx, row in coords_df.iterrows():
            try:
                str_code = str(row.get('str_code', ''))

                # Validate longitude
                longitude = float(row.get('longitude', 0))
                if not (self.LONGITUDE_RANGE[0] <= longitude <= self.LONGITUDE_RANGE[1]):
                    validation_errors.append(f"Store {str_code}: longitude {longitude} out of range")
                    continue

                # Validate latitude
                latitude = float(row.get('latitude', 0))
                if not (self.LATITUDE_RANGE[0] <= latitude <= self.LATITUDE_RANGE[1]):
                    validation_errors.append(f"Store {str_code}: latitude {latitude} out of range")
                    continue

                # Enhanced synthetic data validation
                if synthetic_data_detected:
                    if longitude == 0.0 and latitude == 0.0:
                        validation_errors.append(f"Store {str_code}: null island coordinates not allowed")
                        continue

                    if abs(longitude) < 0.001 or abs(latitude) < 0.001:
                        validation_errors.append(f"Store {str_code}: coordinates too close to origin")
                        continue

                # Create validated coordinate record
                validated_coordinates.append({
                    'str_code': str_code,
                    'longitude': round(longitude, self.COORDINATE_PRECISION),
                    'latitude': round(latitude, self.COORDINATE_PRECISION),
                    'validation_status': 'valid',
                    'synthetic_data': synthetic_data_detected
                })

            except (ValueError, TypeError) as e:
                validation_errors.append(f"Store {row.get('str_code', 'unknown')}: invalid format - {e}")
                continue
            except Exception as e:
                validation_errors.append(f"Store {row.get('str_code', 'unknown')}: unexpected error - {e}")
                continue

        # Check for duplicates in validated coordinates
        if validated_coordinates:
            validated_df = pd.DataFrame(validated_coordinates)
            duplicates = validated_df.duplicated(subset=['str_code']).sum()
            if duplicates > 0:
                validation_errors.append(f"Found {duplicates} duplicate store coordinates")

        return CoordinateValidationData(
            original_count=original_count,
            valid_count=len(validated_coordinates),
            invalid_count=len(validation_errors),
            validation_errors=validation_errors,
            validated_coordinates=pd.DataFrame(validated_coordinates) if validated_coordinates else pd.DataFrame(),
            coordinate_ranges={
                'longitude': self.LONGITUDE_RANGE,
                'latitude': self.LATITUDE_RANGE
            },
            synthetic_data_detected=synthetic_data_detected
        )

    def _detect_synthetic_data(self, coords_df: pd.DataFrame) -> bool:
        """Detect if coordinate data appears to be synthetic/test data."""
        synthetic_indicators = ['synthetic', 'test', 'mock', 'sample', 'demo']

        # Check column values for synthetic indicators
        for col in coords_df.columns:
            for val in coords_df[col].astype(str).str.lower():
                if any(indicator in val for indicator in synthetic_indicators):
                    return True

        return False

    def _create_validation_summary(self, validation_data: CoordinateValidationData) -> Dict[str, Any]:
        """Create a summary of validation results."""
        return {
            'total_coordinates_processed': validation_data.original_count,
            'valid_coordinates': validation_data.valid_count,
            'validation_errors': len(validation_data.validation_errors),
            'synthetic_data_detected': validation_data.synthetic_data_detected,
            'coordinate_ranges': validation_data.coordinate_ranges,
            'validation_success_rate': (validation_data.valid_count / validation_data.original_count * 100)
                if validation_data.original_count > 0 else 0
        }
