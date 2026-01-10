#!/usr/bin/env python3
"""
Repository for data validation logic (Part of Over-engineered Modular Implementation - NOT RECOMMENDED).

⚠️ WARNING: This repository is part of an overly complex modular implementation that is not recommended for use.
Use src/steps/extract_coordinates.py for testing or src/step2_extract_coordinates.py for production instead.

This repository handles validation of coordinate and SPU data,
ensuring data quality and completeness to match legacy behavior.

RECOMMENDED ALTERNATIVE: Use src/steps/extract_coordinates.py for testing or src/step2_extract_coordinates.py for production.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import pandas as pd

from src.repositories.base import ReadOnlyRepository
from src.core.logger import PipelineLogger
from src.core.exceptions import DataValidationError


class ValidationRepository(ReadOnlyRepository):
    """Repository for data validation logic."""

    def __init__(self, logger: PipelineLogger):
        super().__init__(logger)

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all validation rules."""
        # This repository doesn't use get_all in the traditional sense
        # Instead, it provides validation services
        raise NotImplementedError("Use validate_coordinate_data or validate_spu_data instead")

    def validate_coordinate_data(self, coordinates_df: pd.DataFrame) -> Dict[str, Any]:
        """Validate coordinate data format and completeness."""
        validation_result = {
            'is_valid': True,
            'error_message': None,
            'missing_coordinates': [],
            'coverage_percentage': 100.0
        }

        if coordinates_df.empty:
            validation_result.update({
                'is_valid': False,
                'error_message': "No coordinate data provided"
            })
            return validation_result

        # Check required columns
        required_columns = ['str_code', 'longitude', 'latitude']
        missing_columns = [col for col in required_columns if col not in coordinates_df.columns]
        if missing_columns:
            validation_result.update({
                'is_valid': False,
                'error_message': f"Missing required columns: {missing_columns}"
            })
            return validation_result

        # Check data types
        if not pd.api.types.is_numeric_dtype(coordinates_df['longitude']):
            validation_result.update({
                'is_valid': False,
                'error_message': "Longitude column must be numeric"
            })
            return validation_result

        if not pd.api.types.is_numeric_dtype(coordinates_df['latitude']):
            validation_result.update({
                'is_valid': False,
                'error_message': "Latitude column must be numeric"
            })
            return validation_result

        # Check coordinate ranges
        invalid_longitudes = coordinates_df[
            (coordinates_df['longitude'] < -180) | (coordinates_df['longitude'] > 180)
        ]
        if not invalid_longitudes.empty:
            validation_result.update({
                'is_valid': False,
                'error_message': f"Invalid longitude values found: {len(invalid_longitudes)} records"
            })
            return validation_result

        invalid_latitudes = coordinates_df[
            (coordinates_df['latitude'] < -90) | (coordinates_df['latitude'] > 90)
        ]
        if not invalid_latitudes.empty:
            validation_result.update({
                'is_valid': False,
                'error_message': f"Invalid latitude values found: {len(invalid_latitudes)} records"
            })
            return validation_result

        # Check for duplicates
        duplicates = coordinates_df.duplicated(subset=['str_code'], keep=False)
        if duplicates.any():
            duplicate_stores = coordinates_df[duplicates]['str_code'].unique()
            self.logger.warning(f"Found duplicate coordinates for stores: {list(duplicate_stores)}", self.repo_name)

        # Check for empty store codes
        empty_stores = coordinates_df['str_code'].astype(str).str.strip() == ''
        if empty_stores.any():
            validation_result.update({
                'is_valid': False,
                'error_message': f"Empty store codes found: {empty_stores.sum()} records"
            })
            return validation_result

        self.logger.info(f"Coordinate validation passed: {len(coordinates_df)} stores with valid coordinates", self.repo_name)
        return validation_result

    def validate_spu_data(self, spu_mapping: pd.DataFrame, coordinates_df: pd.DataFrame) -> Dict[str, Any]:
        """Validate SPU data consistency with coordinates."""
        validation_result = {
            'is_valid': True,
            'overlap': 0,
            'missing_coords': [],
            'extra_coords': [],
            'coverage_percentage': 0.0
        }

        if spu_mapping.empty:
            validation_result.update({
                'is_valid': False,
                'error_message': "No SPU mapping data provided"
            })
            return validation_result

        if coordinates_df.empty:
            validation_result.update({
                'is_valid': False,
                'error_message': "No coordinate data provided for SPU validation"
            })
            return validation_result

        # Check required columns in SPU mapping
        required_spu_columns = ['spu_code', 'str_code', 'str_name', 'cate_name', 'sub_cate_name', 'spu_sales_amt']
        missing_spu_columns = [col for col in required_spu_columns if col not in spu_mapping.columns]
        if missing_spu_columns:
            validation_result.update({
                'is_valid': False,
                'error_message': f"Missing SPU columns: {missing_spu_columns}"
            })
            return validation_result

        # Check for empty SPU codes or store codes
        empty_spu_codes = spu_mapping['spu_code'].astype(str).str.strip() == ''
        empty_store_codes = spu_mapping['str_code'].astype(str).str.strip() == ''

        if empty_spu_codes.any():
            validation_result.update({
                'is_valid': False,
                'error_message': f"Empty SPU codes found: {empty_spu_codes.sum()} records"
            })
            return validation_result

        if empty_store_codes.any():
            validation_result.update({
                'is_valid': False,
                'error_message': f"Empty store codes found: {empty_store_codes.sum()} records"
            })
            return validation_result

        # Validate overlap between SPU stores and coordinate stores
        spu_stores = set(spu_mapping['str_code'].unique())
        coord_stores = set(coordinates_df['str_code'].unique())

        missing_coords = list(spu_stores - coord_stores)
        extra_coords = list(coord_stores - spu_stores)
        overlap = len(spu_stores & coord_stores)

        validation_result.update({
            'overlap': overlap,
            'missing_coords': missing_coords,
            'extra_coords': extra_coords,
            'coverage_percentage': (overlap / len(spu_stores) * 100) if spu_stores else 0.0
        })

        if missing_coords:
            self.logger.warning(f"{len(missing_coords)} stores in SPU data don't have coordinates", self.repo_name)

        if extra_coords:
            self.logger.info(f"{len(extra_coords)} stores have coordinates but no SPU data", self.repo_name)

        self.logger.info(f"SPU data validation: {overlap}/{len(spu_stores)} stores have both coordinates and SPU data ({validation_result['coverage_percentage']:.1f}%)", self.repo_name)

        return validation_result

    def validate_data_availability(self, period_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that sufficient data is available for analysis."""
        validation_result = {
            'is_valid': True,
            'error_message': None,
            'periods_with_data': 0,
            'periods_with_coordinates': 0,
            'best_period': None,
            'max_coordinate_count': 0
        }

        if not period_data_list:
            validation_result.update({
                'is_valid': False,
                'error_message': "No period data available"
            })
            return validation_result

        periods_with_coordinates = 0
        best_period = None
        max_coordinate_count = 0

        for period_info in period_data_list:
            yyyymm = period_info['yyyymm']
            half = period_info['half']

            # Check if period has coordinate data
            coordinate_count = period_info.get('coordinate_count', 0)
            if coordinate_count > 0:
                periods_with_coordinates += 1
                if coordinate_count > max_coordinate_count:
                    max_coordinate_count = coordinate_count
                    best_period = period_info

        validation_result.update({
            'periods_with_data': len(period_data_list),
            'periods_with_coordinates': periods_with_coordinates,
            'best_period': best_period,
            'max_coordinate_count': max_coordinate_count
        })

        if periods_with_coordinates == 0:
            validation_result.update({
                'is_valid': False,
                'error_message': "No periods contain valid coordinate data. Per policy, placeholders are prohibited. Ensure real coordinates are available in at least one target period and rerun."
            })
            return validation_result

        if max_coordinate_count == 0:
            validation_result.update({
                'is_valid': False,
                'error_message': "No valid source found to extract store coordinates. Per policy, placeholders are prohibited. Provide real coordinates in API data and rerun."
            })
            return validation_result

        self.logger.info(f"Data availability validation: {periods_with_coordinates}/{len(period_data_list)} periods have coordinates, best period has {max_coordinate_count} coordinates", self.repo_name)

        return validation_result
