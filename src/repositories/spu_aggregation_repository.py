#!/usr/bin/env python3
"""
Repository for aggregating and processing SPU sales data (Part of Over-engineered Modular Implementation - NOT RECOMMENDED).

⚠️ WARNING: This repository is part of an overly complex modular implementation that is not recommended for use.
Use src/steps/extract_coordinates.py for testing or src/step2_extract_coordinates.py for production instead.

This repository handles SPU data aggregation from multiple periods,
creating comprehensive mappings and metadata to match legacy behavior.

RECOMMENDED ALTERNATIVE: Use src/steps/extract_coordinates.py for testing or src/step2_extract_coordinates.py for production.
"""

from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import os

from src.repositories.base import ReadOnlyRepository
from src.core.logger import PipelineLogger


class SpuAggregationRepository(ReadOnlyRepository):
    """Repository for aggregating and processing SPU sales data."""

    def __init__(self, base_data_path: str, logger: PipelineLogger):
        super().__init__(logger)
        self.base_data_path = base_data_path

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all SPU data from available periods."""
        # This repository doesn't use get_all in the traditional sense
        # Instead, it provides SPU aggregation services
        raise NotImplementedError("Use aggregate_spu_data_from_periods instead")

    def aggregate_spu_data_from_periods(self, period_data_list: List[Dict[str, Any]], coord_stores: Optional[Set[str]] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Aggregate SPU data from multiple periods (matches legacy behavior).

        Returns:
            Tuple of (spu_mapping_df, spu_metadata_df)
        """
        # Combine SPU data from all periods (no mock data - matches legacy)
        all_spu_data = []

        for period_info in period_data_list:
            yyyymm = period_info['yyyymm']
            half = period_info['half']

            spu_data = self._load_spu_data_for_period(yyyymm, half)
            if spu_data is not None and not spu_data.empty:
                spu_data = spu_data.copy()
                spu_data['period'] = f"{yyyymm}{half}"
                all_spu_data.append(spu_data)

        if not all_spu_data:
            self.logger.warning("No SPU data found across any periods", self.repo_name)
            return pd.DataFrame(), pd.DataFrame()

        # Combine all SPU data (matches legacy logic)
        combined_spu_df = pd.concat(all_spu_data, ignore_index=True)

        # Normalize key identifiers to string type (matches legacy)
        if 'str_code' in combined_spu_df.columns:
            combined_spu_df['str_code'] = combined_spu_df['str_code'].astype(str)
        if 'spu_code' in combined_spu_df.columns:
            combined_spu_df['spu_code'] = combined_spu_df['spu_code'].astype(str)

        total_records = len(combined_spu_df)
        self.logger.info(f"Processing {total_records:,} SPU records across {len(all_spu_data)} periods", self.repo_name)

        # Create comprehensive SPU-store mapping (unique combinations across all periods - matches legacy)
        spu_mapping = combined_spu_df[['spu_code', 'str_code', 'str_name', 'cate_name', 'sub_cate_name', 'spu_sales_amt']].copy()

        # Filter to only include stores that have coordinates (matches legacy behavior)
        # This ensures SPU mappings are consistent with coordinate data availability
        if coord_stores:
            spu_mapping = spu_mapping[spu_mapping['str_code'].isin(coord_stores)].copy()
            self.logger.info(f"Filtered SPU data to {len(spu_mapping)} records for {len(coord_stores)} stores with coordinates", self.repo_name)

        spu_mapping = spu_mapping.drop_duplicates(subset=['spu_code', 'str_code'])  # Unique SPU-store pairs

        self.logger.info(f"Created SPU-store mapping with {len(spu_mapping):,} unique combinations", self.repo_name)

        # Create comprehensive SPU metadata (aggregated across all periods - matches legacy)
        # Use the filtered SPU data to ensure metadata is consistent with coordinate availability
        metadata_df = combined_spu_df
        if coord_stores:
            metadata_df = combined_spu_df[combined_spu_df['str_code'].isin(coord_stores)].copy()
            self.logger.info(f"Filtered SPU metadata to {len(metadata_df)} records for {len(coord_stores)} stores with coordinates", self.repo_name)

        spu_metadata = metadata_df.groupby(['spu_code', 'cate_name', 'sub_cate_name']).agg({
            'str_code': 'nunique',  # Number of unique stores selling this SPU
            'spu_sales_amt': ['sum', 'mean', 'std', 'count']  # Comprehensive sales statistics
        }).reset_index()

        # Flatten column names (matches legacy)
        spu_metadata.columns = ['spu_code', 'cate_name', 'sub_cate_name', 'store_count', 'total_sales', 'avg_sales', 'std_sales', 'period_count']
        spu_metadata['std_sales'] = spu_metadata['std_sales'].fillna(0)

        self.logger.info(f"Created SPU metadata for {len(spu_metadata):,} unique SPUs", self.repo_name)

        # Debug statistics (matches legacy)
        if len(spu_metadata) > 0:
            category_counts = spu_metadata.groupby('cate_name')['spu_code'].count().sort_values(ascending=False)
            self.logger.info(f"SPU distribution by category: {dict(category_counts.head(10))}", self.repo_name)

            unique_stores_all_periods = combined_spu_df['str_code'].nunique()
            unique_spus_all_periods = combined_spu_df['spu_code'].nunique()

            self.logger.info(f"Multi-period statistics: {unique_stores_all_periods} stores, {unique_spus_all_periods} SPUs", self.repo_name)
            self.logger.info(f"Average records per period: {total_records / len(all_spu_data):.0f}", self.repo_name)

        return spu_mapping, spu_metadata

    def _load_spu_data_for_period(self, yyyymm: str, half: str) -> Optional[pd.DataFrame]:
        """Load SPU data for a specific period (matches legacy file patterns)."""
        period_label = f"{yyyymm}{half}"

        # Match legacy behavior: try multiple file paths for SPU data
        search_paths = [
            self.base_data_path,  # data/api_data
            os.path.join(os.path.dirname(self.base_data_path), "output")  # output
        ]

        # Try to load SPU data (matches legacy patterns)
        for search_path in search_paths:
            spu_file = os.path.join(search_path, f"complete_spu_sales_{period_label}.csv")
            if os.path.exists(spu_file):
                try:
                    spu_data = pd.read_csv(spu_file)
                    self.logger.info(f"Loaded SPU data from {spu_file}: {len(spu_data)} records, {spu_data['str_code'].nunique()} stores", self.repo_name)
                    return spu_data
                except Exception as e:
                    self.logger.warning(f"Error reading {spu_file}: {str(e)}", self.repo_name)

        self.logger.warning(f"No SPU data found for period {period_label}", self.repo_name)
        return None

    def validate_spu_data(self, spu_mapping: pd.DataFrame, coordinates_df: pd.DataFrame) -> Dict[str, Any]:
        """Validate SPU data consistency with coordinates (matches legacy validation)."""
        if spu_mapping.empty or coordinates_df.empty:
            return {'overlap': 0, 'missing_coords': [], 'extra_coords': []}

        # Validate that all stores in comprehensive SPU data have coordinates (matches legacy)
        combined_spu_stores = set(spu_mapping['str_code'].unique())
        coord_stores = set(coordinates_df['str_code'].unique())

        missing_coords = list(combined_spu_stores - coord_stores)
        extra_coords = list(coord_stores - combined_spu_stores)

        overlap = len(combined_spu_stores & coord_stores)

        validation_result = {
            'overlap': overlap,
            'missing_coords': missing_coords,
            'extra_coords': extra_coords,
            'coverage_percentage': (overlap / len(combined_spu_stores) * 100) if combined_spu_stores else 0.0
        }

        if missing_coords:
            self.logger.warning(f"{len(missing_coords)} stores in SPU data don't have coordinates", self.repo_name)
        if extra_coords:
            self.logger.info(f"{len(extra_coords)} stores have coordinates but no SPU data", self.repo_name)

        self.logger.info(f"SPU data coverage: {overlap}/{len(combined_spu_stores)} stores ({validation_result['coverage_percentage']:.1f}%)", self.repo_name)

        return validation_result
