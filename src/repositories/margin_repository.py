"""Repository for margin rate data access."""

import fireducks.pandas as pd
from typing import Optional


class MarginRepository:
    """Repository for accessing margin rate data."""
    
    def __init__(self, csv_repo, logger):
        """
        Initialize margin repository.
        
        Args:
            csv_repo: CSV file repository for file operations
            logger: Pipeline logger instance
        """
        self.csv_repo = csv_repo
        self.logger = logger
    
    def load_margin_rates(self, period_label: str) -> pd.DataFrame:
        """
        Load margin rates for ROI calculation.
        
        Args:
            period_label: Period identifier (e.g., '202510A')
            
        Returns:
            DataFrame with margin rates by store and feature
        """
        filename = f"margin_rates_{period_label}.csv"
        
        try:
            df = self.csv_repo.load(filename)
            self.logger.info(f"Loaded margin rates from: {filename}")
            df = self._standardize_columns(df)
            
            self.logger.info(
                f"Margin rates loaded: {len(df)} records, "
                f"{df['str_code'].nunique()} stores"
            )
            
            return df
        except FileNotFoundError:
            self.logger.warning(
                f"Margin rates not found: {filename}. "
                f"ROI calculation will be limited."
            )
            # Return empty DataFrame with expected structure
            return pd.DataFrame(columns=[
                'str_code', 'sub_cate_name', 'spu_code', 'margin_rate'
            ])
    
    def build_margin_lookup(
        self,
        margin_df: pd.DataFrame,
        feature_col: str
    ) -> dict:
        """
        Build lookup dictionary for fast margin rate retrieval.
        
        Creates a two-level lookup:
        1. (store, feature) -> margin_rate
        2. (store) -> average margin_rate
        
        Args:
            margin_df: DataFrame with margin rates
            feature_col: Feature column name (sub_cate_name or spu_code)
            
        Returns:
            Dictionary with margin rate lookups
        """
        if len(margin_df) == 0:
            return {'store_feature': {}, 'store_avg': {}}
        
        # Store-feature level lookup
        store_feature_lookup = {}
        for _, row in margin_df.iterrows():
            key = (row['str_code'], row[feature_col])
            store_feature_lookup[key] = row['margin_rate']
        
        # Store average lookup
        store_avg = margin_df.groupby('str_code')['margin_rate'].mean().to_dict()
        
        self.logger.info(
            f"Built margin lookup: {len(store_feature_lookup)} store-feature pairs, "
            f"{len(store_avg)} store averages"
        )
        
        return {
            'store_feature': store_feature_lookup,
            'store_avg': store_avg
        }
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardize column names in margin data.
        
        Args:
            df: DataFrame with margin data
            
        Returns:
            DataFrame with standardized column names
        """
        # Column name mappings
        column_mappings = {
            'store_code': 'str_code',
            'subcategory_name': 'sub_cate_name',
            'subcategory': 'sub_cate_name',
            'margin': 'margin_rate',
        }
        
        # Apply mappings
        for old_name, new_name in column_mappings.items():
            if old_name in df.columns and new_name not in df.columns:
                df = df.rename(columns={old_name: new_name})
        
        # Validate required columns
        if 'margin_rate' not in df.columns:
            raise ValueError(
                f"Margin data missing 'margin_rate' column. "
                f"Available columns: {list(df.columns)}"
            )
        
        return df
