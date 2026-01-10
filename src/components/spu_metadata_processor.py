#!/usr/bin/env python3
"""
SPU Metadata Processor Module (Part of Over-engineered Modular Implementation - NOT RECOMMENDED)

⚠️ WARNING: This module is part of an overly complex modular implementation that is not recommended for use.
Use src/steps/extract_coordinates.py for testing or src/step2_extract_coordinates.py for production instead.

Purpose: Process and aggregate SPU (Stock Keeping Unit) data from multiple periods
to create comprehensive SPU-to-store mappings and metadata. This module handles
SPU-specific logic separately from coordinate processing for better modularity.

Standards Compliance: Follows code design standards with proper separation of
concerns, comprehensive validation, and maintainable architecture.

RECOMMENDED ALTERNATIVE: Use src/steps/extract_coordinates.py for testing or src/step2_extract_coordinates.py for production.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import json
import pandas as pd
import numpy as np

from core.logger import PipelineLogger
from core.exceptions import DataValidationError


@dataclass
class SPUProcessingResult:
    """Result of SPU data processing operation."""
    spu_mapping_df: pd.DataFrame
    spu_metadata_df: pd.DataFrame
    processing_statistics: Dict[str, Any]
    data_quality_metrics: Dict[str, Any]


@dataclass
class SPUValidationData:
    """SPU data validation results."""
    total_records: int
    valid_records: int
    invalid_records: int
    validation_errors: List[str]
    data_quality_score: float
    aggregation_issues: List[str]


class SPUMetadataProcessor:
    """
    Process and aggregate SPU data from multiple periods.

    Purpose: Handle all SPU-specific processing including deduplication,
    aggregation across time periods, and metadata generation. This class
    focuses solely on SPU data processing, maintaining separation of concerns
    from coordinate extraction.
    """

    def __init__(self, logger: PipelineLogger):
        """
        Initialize the SPU metadata processor.

        Args:
            logger: Pipeline logger for consistent logging
        """
        self.logger = logger
        self.class_name = self.__class__.__name__

    def process_spu_data(self,
                        spu_dataframes: List[pd.DataFrame],
                        coordinate_stores: Optional[Set[str]] = None) -> SPUProcessingResult:
        """
        Process SPU data from multiple periods with optional coordinate filtering.

        Purpose: Combine SPU data from multiple time periods, deduplicate records,
        aggregate statistics, and create comprehensive SPU metadata. Optionally
        filters to only include stores that have valid coordinates.

        Args:
            spu_dataframes: List of SPU DataFrames from different periods
            coordinate_stores: Set of store codes with valid coordinates (optional filtering)

        Returns:
            SPUProcessingResult with processed SPU data and quality metrics

        Raises:
            DataValidationError: If SPU data validation fails critically
        """
        self.logger.info("Starting SPU data processing and aggregation", self.class_name)

        if not spu_dataframes:
            self.logger.warning("No SPU data provided for processing", self.class_name)
            return SPUProcessingResult(
                spu_mapping_df=pd.DataFrame(),
                spu_metadata_df=pd.DataFrame(),
                processing_statistics={'total_periods': 0, 'total_records': 0},
                data_quality_metrics={'validation_passed': True, 'records_processed': 0}
            )

        # Combine all SPU data
        combined_spu_df = self._combine_spu_dataframes(spu_dataframes)

        if combined_spu_df.empty:
            raise DataValidationError("No valid SPU data found after combining periods")

        # Apply coordinate filtering if specified
        if coordinate_stores:
            combined_spu_df = self._filter_by_coordinate_stores(combined_spu_df, coordinate_stores)

        # Validate and clean SPU data
        validation_data = self._validate_spu_data(combined_spu_df)

        # Check if validation passed (no critical errors)
        if len(validation_data.validation_errors) > 0:
            error_summary = "; ".join(validation_data.validation_errors[:3])
            if len(validation_data.validation_errors) > 3:
                error_summary += f" ... and {len(validation_data.validation_errors) - 3} more errors"
            raise DataValidationError(f"SPU data validation failed: {error_summary}")

        # Create SPU mappings and metadata
        spu_mapping_df = self._create_spu_mappings(combined_spu_df)
        spu_metadata_df = self._create_spu_metadata(combined_spu_df)

        # Generate processing statistics
        processing_stats = self._generate_processing_statistics(spu_dataframes, combined_spu_df)
        quality_metrics = self._generate_quality_metrics(validation_data)

        result = SPUProcessingResult(
            spu_mapping_df=spu_mapping_df,
            spu_metadata_df=spu_metadata_df,
            processing_statistics=processing_stats,
            data_quality_metrics=quality_metrics
        )

        self.logger.info(f"Processed SPU data: {len(spu_mapping_df)} mappings, {len(spu_metadata_df)} metadata records", self.class_name)
        return result

    def _combine_spu_dataframes(self, spu_dataframes: List[pd.DataFrame]) -> pd.DataFrame:
        """
        Combine SPU DataFrames from multiple periods.

        Purpose: Concatenate SPU data from different time periods while
        preserving data integrity and handling format variations.

        Args:
            spu_dataframes: List of SPU DataFrames from different periods

        Returns:
            Combined SPU DataFrame
        """
        if not spu_dataframes:
            return pd.DataFrame()

        # Combine all DataFrames
        combined_df = pd.concat(spu_dataframes, ignore_index=True)

        # Normalize key identifiers to string type
        string_columns = ['str_code', 'spu_code', 'cate_name', 'sub_cate_name']
        for col in string_columns:
            if col in combined_df.columns:
                combined_df[col] = combined_df[col].astype(str)

        # Remove completely empty rows
        combined_df = combined_df.dropna(how='all')

        self.logger.info(f"Combined {len(spu_dataframes)} periods into {len(combined_df)} SPU records", self.class_name)
        return combined_df

    def _filter_by_coordinate_stores(self, spu_df: pd.DataFrame, coordinate_stores: Set[str]) -> pd.DataFrame:
        """
        Filter SPU data to only include stores with valid coordinates.

        Purpose: Ensure SPU data consistency with coordinate data by filtering
        to only stores that have valid geographic coordinates.

        Args:
            spu_df: SPU DataFrame to filter
            coordinate_stores: Set of store codes with valid coordinates

        Returns:
            Filtered SPU DataFrame
        """
        if 'str_code' not in spu_df.columns:
            self.logger.warning("No str_code column found for coordinate filtering", self.class_name)
            return spu_df

        original_count = len(spu_df)
        filtered_df = spu_df[spu_df['str_code'].astype(str).isin(coordinate_stores)]

        filtered_count = len(filtered_df)
        self.logger.info(f"Filtered SPU data: {filtered_count}/{original_count} records for coordinate-validated stores", self.class_name)

        return filtered_df

    def _validate_spu_data(self, spu_df: pd.DataFrame) -> SPUValidationData:
        """
        Validate SPU data quality and integrity.

        Purpose: Perform comprehensive validation of SPU data including
        format checks, business logic validation, and data quality assessment.

        Args:
            spu_df: SPU DataFrame to validate

        Returns:
            SPUValidationData with validation results
        """
        validation_errors = []
        total_records = len(spu_df)

        # Check required columns
        required_columns = ['str_code', 'spu_code', 'spu_sales_amt']
        missing_columns = [col for col in required_columns if col not in spu_df.columns]
        if missing_columns:
            validation_errors.append(f"Missing required columns: {missing_columns}")

        if validation_errors:
            return SPUValidationData(
                total_records=total_records,
                valid_records=0,
                invalid_records=total_records,
                validation_errors=validation_errors,
                data_quality_score=0.0,
                aggregation_issues=["Critical column missing"]
            )

        # Validate data types and ranges
        valid_records = 0
        aggregation_issues = []

        try:
            # Check for valid SPU codes (non-empty strings)
            invalid_spu_codes = spu_df['spu_code'].astype(str).str.strip() == ''
            if invalid_spu_codes.any():
                validation_errors.append(f"Found {invalid_spu_codes.sum()} records with empty SPU codes")

            # Check for valid store codes
            invalid_store_codes = spu_df['str_code'].astype(str).str.strip() == ''
            if invalid_store_codes.any():
                validation_errors.append(f"Found {invalid_store_codes.sum()} records with empty store codes")

            # Check sales amounts (allow negative for returns)
            invalid_sales = pd.isna(spu_df['spu_sales_amt'])
            if invalid_sales.any():
                validation_errors.append(f"Found {invalid_sales.sum()} records with null sales amounts")

            # Count valid records
            valid_mask = (
                ~invalid_spu_codes &
                ~invalid_store_codes &
                ~invalid_sales
            )
            valid_records = valid_mask.sum()

            # Check for aggregation issues
            if valid_records > 0:
                # Check for reasonable sales amounts
                sales_stats = spu_df.loc[valid_mask, 'spu_sales_amt'].describe()
                if sales_stats['min'] < -1000000 or sales_stats['max'] > 1000000:
                    aggregation_issues.append("Unusual sales amount range detected")

        except Exception as e:
            validation_errors.append(f"Error during SPU validation: {e}")

        # Calculate data quality score
        quality_score = (valid_records / total_records * 100) if total_records > 0 else 0.0

        return SPUValidationData(
            total_records=total_records,
            valid_records=valid_records,
            invalid_records=total_records - valid_records,
            validation_errors=validation_errors,
            data_quality_score=quality_score,
            aggregation_issues=aggregation_issues
        )

    def _create_spu_mappings(self, spu_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create SPU-to-store mapping DataFrame.

        Purpose: Generate unique SPU-store combinations from the processed
        SPU data, ensuring no duplicate relationships.

        Args:
            spu_df: Processed SPU DataFrame

        Returns:
            SPU mapping DataFrame with unique combinations
        """
        if spu_df.empty or 'spu_code' not in spu_df.columns or 'str_code' not in spu_df.columns:
            return pd.DataFrame()

        # Create unique SPU-store combinations
        mapping_columns = ['spu_code', 'str_code', 'str_name', 'cate_name', 'sub_cate_name', 'spu_sales_amt']
        available_columns = [col for col in mapping_columns if col in spu_df.columns]

        spu_mapping = spu_df[available_columns].copy()
        spu_mapping = spu_mapping.drop_duplicates(subset=['spu_code', 'str_code'])

        self.logger.info(f"Created {len(spu_mapping)} unique SPU-store mappings", self.class_name)
        return spu_mapping

    def _create_spu_metadata(self, spu_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create comprehensive SPU metadata with aggregated statistics.

        Purpose: Generate SPU metadata by aggregating sales data across
        all periods, providing insights into SPU performance and distribution.

        Args:
            spu_df: Processed SPU DataFrame

        Returns:
            SPU metadata DataFrame with aggregated statistics
        """
        if spu_df.empty or 'spu_code' not in spu_df.columns:
            return pd.DataFrame()

        # Group by SPU and calculate statistics
        metadata = spu_df.groupby(['spu_code', 'cate_name', 'sub_cate_name']).agg({
            'str_code': 'nunique',  # Number of unique stores
            'spu_sales_amt': ['sum', 'mean', 'std', 'count']  # Sales statistics
        }).reset_index()

        # Flatten column names
        metadata.columns = ['spu_code', 'cate_name', 'sub_cate_name',
                           'store_count', 'total_sales', 'avg_sales', 'std_sales', 'period_count']

        # Handle NaN standard deviations
        metadata['std_sales'] = metadata['std_sales'].fillna(0)

        # Calculate additional metrics
        metadata['sales_volatility'] = metadata['std_sales'] / metadata['avg_sales'].replace(0, 1)
        metadata['sales_volatility'] = metadata['sales_volatility'].fillna(0)

        self.logger.info(f"Created metadata for {len(metadata)} unique SPUs", self.class_name)
        return metadata

    def _generate_processing_statistics(self,
                                      spu_dataframes: List[pd.DataFrame],
                                      combined_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive processing statistics."""
        return {
            'total_periods': len(spu_dataframes),
            'total_records': len(combined_df),
            'unique_spus': combined_df['spu_code'].nunique() if 'spu_code' in combined_df.columns else 0,
            'unique_stores': combined_df['str_code'].nunique() if 'str_code' in combined_df.columns else 0,
            'unique_categories': combined_df['cate_name'].nunique() if 'cate_name' in combined_df.columns else 0,
            'unique_subcategories': combined_df['sub_cate_name'].nunique() if 'sub_cate_name' in combined_df.columns else 0,
            'avg_records_per_period': len(combined_df) / len(spu_dataframes) if spu_dataframes else 0
        }

    def _generate_quality_metrics(self, validation_data: SPUValidationData) -> Dict[str, Any]:
        """Generate data quality metrics."""
        return {
            'validation_passed': len(validation_data.validation_errors) == 0,
            'records_processed': validation_data.total_records,
            'valid_records': validation_data.valid_records,
            'invalid_records': validation_data.invalid_records,
            'data_quality_score': validation_data.data_quality_score,
            'validation_errors_count': len(validation_data.validation_errors),
            'aggregation_issues_count': len(validation_data.aggregation_issues)
        }




