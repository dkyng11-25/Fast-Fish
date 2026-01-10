"""
Matrix Data Repository

Handles loading and aggregation of multi-period data for matrix preparation.
Supports both category-level and SPU-level data with intelligent fallback mechanisms.
"""

import pandas as pd
import numpy as np
import os
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
import glob

from repositories.base import Repository
from src.core.logger import PipelineLogger


class MatrixDataRepository(Repository):
    """
    Repository for loading and aggregating multi-period data for matrix preparation.
    """
    
    def __init__(self, logger: PipelineLogger):
        super().__init__(logger)
        self.class_name = "MatrixDataRepository"
        
        # Matrix creation parameters
        self.min_stores_per_subcategory = 5
        self.min_subcategories_per_store = 3
        self.min_stores_per_spu = 3
        self.min_spus_per_store = 10
        self.min_spu_sales_amount = 1.0
        self.max_spu_count = 1000  # Limit SPU matrix size for memory management
        
        # Anomaly detection parameters
        self.anomaly_lat = 21.9178
        self.anomaly_lon = 110.854
    
    def load_multi_period_data(self, periods: List[Tuple[str, str]]) -> Tuple[List[pd.DataFrame], List[pd.DataFrame]]:
        """
        Load year-over-year multi-period category and SPU data from all available periods.
        
        Args:
            periods: List of (yyyymm, period) tuples to load
            
        Returns:
            Tuple of (category_dataframes_list, spu_dataframes_list)
        """
        self.logger.info(f"Loading data from {len(periods)} periods", self.class_name)
        
        all_category_dfs = []
        all_spu_dfs = []
        
        for yyyymm, period in periods:
            period_label = f"{yyyymm}{period}"
            self.logger.info(f"Loading period {period_label}", self.class_name)
            
            # Load category data
            category_df = self._load_period_category_data(period_label)
            if category_df is not None:
                all_category_dfs.append(category_df)
            
            # Load SPU data
            spu_df = self._load_period_spu_data(period_label)
            if spu_df is not None:
                all_spu_dfs.append(spu_df)
        
        self.logger.info(f"Loaded {len(all_category_dfs)} periods with category data", self.class_name)
        self.logger.info(f"Loaded {len(all_spu_dfs)} periods with SPU data", self.class_name)
        
        return all_category_dfs, all_spu_dfs
    
    def _load_period_category_data(self, period_label: str) -> Optional[pd.DataFrame]:
        """Load category data for a specific period."""
        potential_paths = [
            f"data/api_data/complete_category_sales_{period_label}.csv",
            f"output/complete_category_sales_{period_label}.csv",
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path, low_memory=False)
                    df['period'] = period_label
                    self.logger.info(f"Found category data: {len(df):,} records, {df['str_code'].nunique()} stores", self.class_name)
                    return df
                except Exception as e:
                    self.logger.warning(f"Error reading {path}: {str(e)}", self.class_name)
        
        return None
    
    def _load_period_spu_data(self, period_label: str) -> Optional[pd.DataFrame]:
        """Load SPU data for a specific period."""
        potential_paths = [
            f"data/api_data/complete_spu_sales_{period_label}.csv",
            f"output/complete_spu_sales_{period_label}.csv",
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path, low_memory=False)
                    df['period'] = period_label
                    self.logger.info(f"Found SPU data: {len(df):,} records, {df['str_code'].nunique()} stores", self.class_name)
                    return df
                except Exception as e:
                    self.logger.warning(f"Error reading {path}: {str(e)}", self.class_name)
        
        return None
    
    def load_coordinates(self) -> pd.DataFrame:
        """
        Load store coordinates data.
        
        Returns:
            DataFrame with store coordinates
        """
        coordinates_file = "data/store_coordinates_extended.csv"
        
        try:
            coords_df = pd.read_csv(coordinates_file)
            self.logger.info(f"Loaded coordinates for {len(coords_df)} stores", self.class_name)
            return coords_df
        except Exception as e:
            self.logger.warning(f"Error loading coordinates: {str(e)}", self.class_name)
            return pd.DataFrame(columns=['str_code', 'latitude', 'longitude'])
    
    def identify_anomalous_stores(self, coords_df: pd.DataFrame) -> List[str]:
        """
        Identify stores with anomalous coordinates that might be data quality issues.
        
        Args:
            coords_df: Store coordinates DataFrame
            
        Returns:
            List of store codes with anomalous coordinates
        """
        if coords_df.empty:
            return []
            
        # Identify stores at the specific anomaly location
        anomaly_stores = coords_df[
            (abs(coords_df['latitude'] - self.anomaly_lat) < 0.001) & 
            (abs(coords_df['longitude'] - self.anomaly_lon) < 0.001)
        ]['str_code'].tolist()
        
        self.logger.info(f"Identified {len(anomaly_stores)} stores with anomalous coordinates", self.class_name)
        
        return anomaly_stores
    
    def aggregate_subcategory_data(self, category_dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """
        Aggregate subcategory data across multiple periods.
        
        Args:
            category_dfs: List of category DataFrames from different periods
            
        Returns:
            Aggregated subcategory DataFrame
        """
        if not category_dfs:
            raise ValueError("No category data available for aggregation")
        
        # Combine all category data
        combined_df = pd.concat(category_dfs, ignore_index=True)
        
        # Normalize column names and dtypes
        combined_df['str_code'] = combined_df['str_code'].astype(str)
        value_col = 'sal_amt' if 'sal_amt' in combined_df.columns else 'sub_cate_sales_amt'
        
        if value_col not in combined_df.columns:
            raise ValueError(f"Subcategory sales column not found. Expected one of ['sal_amt','sub_cate_sales_amt'], got: {list(combined_df.columns)}")
        
        # Aggregate by store and subcategory across all periods
        self.logger.info("Aggregating subcategory data across all periods", self.class_name)
        aggregated_df = combined_df.groupby(['str_code', 'str_name', 'cate_name', 'sub_cate_name']).agg({
            value_col: 'sum',  # Total sales across all periods
            'period': 'count'  # Number of periods this combination appears in
        }).reset_index()
        
        # Rename columns for consistency
        aggregated_df = aggregated_df.rename(columns={'period': 'period_count', value_col: 'sal_amt'})
        
        self.logger.info(f"Aggregated subcategory data: {len(aggregated_df):,} records from {aggregated_df['str_code'].nunique()} stores", self.class_name)
        self.logger.info(f"Subcategories found: {aggregated_df['sub_cate_name'].nunique()}", self.class_name)
        
        return aggregated_df
    
    def aggregate_spu_data(self, spu_dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """
        Aggregate SPU data across multiple periods.
        
        Args:
            spu_dfs: List of SPU DataFrames from different periods
            
        Returns:
            Aggregated SPU DataFrame
        """
        if not spu_dfs:
            raise ValueError("No SPU data available for aggregation")
        
        # Combine all SPU data
        combined_df = pd.concat(spu_dfs, ignore_index=True)
        
        # Normalize key dtypes
        combined_df['str_code'] = combined_df['str_code'].astype(str)
        combined_df['spu_code'] = combined_df['spu_code'].astype(str)
        
        # Aggregate by store and SPU across all periods
        self.logger.info("Aggregating SPU data across all periods", self.class_name)
        aggregated_df = combined_df.groupby(['str_code', 'str_name', 'cate_name', 'sub_cate_name', 'spu_code']).agg({
            'spu_sales_amt': 'sum',  # Total sales across all periods
            'quantity': 'sum',  # Total quantity across all periods
            'period': 'count'  # Number of periods this combination appears in
        }).reset_index()
        
        # Calculate aggregated unit price
        aggregated_df['unit_price'] = aggregated_df['spu_sales_amt'] / aggregated_df['quantity'].replace(0, np.nan)
        aggregated_df['unit_price'] = aggregated_df['unit_price'].fillna(0)
        
        # Rename columns for consistency
        aggregated_df = aggregated_df.rename(columns={'period': 'period_count'})
        
        self.logger.info(f"Aggregated SPU data: {len(aggregated_df):,} records from {aggregated_df['str_code'].nunique()} stores", self.class_name)
        self.logger.info(f"SPUs found: {aggregated_df['spu_code'].nunique()}", self.class_name)
        
        return aggregated_df
    
    def load_single_period_fallback(self, period_label: str) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """
        Load single period data as fallback when multi-period data is not available.
        
        Args:
            period_label: Period label to load (e.g., "202509A")
            
        Returns:
            Tuple of (category_df, spu_df)
        """
        category_df = self._load_period_category_data(period_label)
        spu_df = self._load_period_spu_data(period_label)
        
        if category_df is not None:
            self.logger.info(f"Loaded single-period category data: {len(category_df):,} records", self.class_name)
        if spu_df is not None:
            self.logger.info(f"Loaded single-period SPU data: {len(spu_df):,} records", self.class_name)
        
        return category_df, spu_df

    def get_all(self) -> List[Dict[str, Any]]:
        """
        Get all data from the repository. For matrix data repository,
        this loads and aggregates data from all available periods.

        Returns:
            List of dictionaries containing aggregated data
        """
        # This method would typically load data, but for matrix preparation
        # we use the specialized loading methods instead
        # Return empty list as this repository is used differently
        return []

    def save(self, data: pd.DataFrame) -> None:
        """
        Save data to the repository. For matrix data repository,
        this is a no-op as data saving is handled by other repositories.

        Args:
            data: DataFrame to save (ignored)
        """
        # This repository is primarily for loading/aggregating data
        # Matrix saving is handled by other specialized repositories
        pass
