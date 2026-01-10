"""Data loading component for Missing Category/SPU Rule."""

import fireducks.pandas as pd
from typing import Optional, Tuple
from .config import MissingCategoryConfig


class DataLoader:
    """
    Loads and prepares data for missing category analysis.
    
    Responsibilities:
    - Load clustering data with normalization
    - Load sales data with optional seasonal blending
    - Load quantity data with price backfilling
    - Load margin rates for ROI calculation
    """
    
    def __init__(
        self,
        cluster_repo,
        sales_repo,
        quantity_repo,
        margin_repo,
        config: MissingCategoryConfig,
        logger
    ):
        """
        Initialize data loader.
        
        Args:
            cluster_repo: Repository for clustering data
            sales_repo: Repository for sales data
            quantity_repo: Repository for quantity data
            margin_repo: Repository for margin data
            config: Configuration for the analysis
            logger: Pipeline logger instance
        """
        self.cluster_repo = cluster_repo
        self.sales_repo = sales_repo
        self.quantity_repo = quantity_repo
        self.margin_repo = margin_repo
        self.config = config
        self.logger = logger
    
    def load_clustering_data(self) -> pd.DataFrame:
        """
        Load clustering results.
        
        Returns:
            DataFrame with clustering assignments (str_code, cluster_id)
        """
        self.logger.info("Loading clustering data...")
        
        df = self.cluster_repo.load_clustering_results(
            self.config.period_label,
            self.config.analysis_level
        )
        
        # Normalize column names: "Cluster" → "cluster_id"
        if 'Cluster' in df.columns and 'cluster_id' not in df.columns:
            df = df.rename(columns={'Cluster': 'cluster_id'})
            self.logger.info("Normalized 'Cluster' column to 'cluster_id'")
        
        # Ensure required columns
        required_cols = ['str_code', 'cluster_id']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(
                f"Clustering data missing required columns: {missing_cols}"
            )
        
        return df
    
    def load_sales_data(self) -> pd.DataFrame:
        """
        Load sales data with optional seasonal blending.
        
        If seasonal blending is enabled, loads both current and seasonal data
        and blends them with configured weights.
        
        Returns:
            DataFrame with sales data
        """
        self.logger.info("Loading sales data...")
        
        # Load current period sales
        current_sales = self.sales_repo.load_current_sales(
            self.config.period_label,
            self.config.analysis_level
        )
        
        # If seasonal blending disabled, return current sales
        if not self.config.use_blended_seasonal:
            self.logger.info("Seasonal blending disabled, using current sales only")
            return current_sales
        
        # Load seasonal sales
        seasonal_sales = self.sales_repo.load_seasonal_sales(
            self.config.period_label,
            self.config.seasonal_years_back
        )
        
        # If seasonal data not available, return current sales
        if seasonal_sales is None:
            self.logger.warning(
                "Seasonal data not available, using current sales only"
            )
            return current_sales
        
        # Blend current and seasonal sales
        blended_sales = self._blend_sales_data(current_sales, seasonal_sales)
        
        return blended_sales
    
    def _blend_sales_data(
        self,
        current_df: pd.DataFrame,
        seasonal_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Blend current and seasonal sales data with configured weights.
        
        Args:
            current_df: Current period sales data
            seasonal_df: Seasonal period sales data
            
        Returns:
            DataFrame with blended sales data
        """
        self.logger.info(
            f"Blending sales data: "
            f"{self.config.recent_weight:.0%} current + "
            f"{self.config.seasonal_weight:.0%} seasonal"
        )
        
        # Identify feature column
        feature_col = self.config.feature_column
        
        # Ensure both DataFrames have the feature column
        if feature_col not in current_df.columns:
            raise ValueError(
                f"Current sales missing feature column: {feature_col}"
            )
        if feature_col not in seasonal_df.columns:
            raise ValueError(
                f"Seasonal sales missing feature column: {feature_col}"
            )
        
        # Merge on store and feature
        merge_cols = ['str_code', feature_col]
        
        # Prepare current data
        current_sales = current_df[merge_cols + ['sal_amt']].copy()
        current_sales = current_sales.rename(columns={'sal_amt': 'current_sales'})
        
        # Prepare seasonal data
        seasonal_sales = seasonal_df[merge_cols + ['sal_amt']].copy()
        seasonal_sales = seasonal_sales.rename(columns={'sal_amt': 'seasonal_sales'})
        
        # Merge
        blended = pd.merge(
            current_sales,
            seasonal_sales,
            on=merge_cols,
            how='outer'
        )
        
        # Fill missing values with 0
        blended['current_sales'] = blended['current_sales'].fillna(0)
        blended['seasonal_sales'] = blended['seasonal_sales'].fillna(0)
        
        # Calculate blended sales
        blended['sal_amt'] = (
            blended['current_sales'] * self.config.recent_weight +
            blended['seasonal_sales'] * self.config.seasonal_weight
        )
        
        # Keep only necessary columns
        result = blended[merge_cols + ['sal_amt']].copy()
        
        self.logger.info(
            f"Blended sales: {len(result)} records, "
            f"{result['str_code'].nunique()} stores, "
            f"{result[feature_col].nunique()} {self.config.analysis_level}s"
        )
        
        # Log blending statistics
        total_current = current_sales['current_sales'].sum()
        total_seasonal = seasonal_sales['seasonal_sales'].sum()
        total_blended = result['sal_amt'].sum()
        
        self.logger.info(
            f"Sales totals: Current=${total_current:,.0f}, "
            f"Seasonal=${total_seasonal:,.0f}, "
            f"Blended=${total_blended:,.0f}"
        )
        
        return result
    
    def load_quantity_data(self) -> pd.DataFrame:
        """
        Load quantity data with price information.
        
        Returns:
            DataFrame with quantity and price data
        """
        self.logger.info("Loading quantity data...")
        
        # Load from repository
        df = self.quantity_repo.load_quantity_data(self.config.period_label)
        
        # Ensure required columns
        required_cols = ['str_code', self.config.feature_column, 'avg_unit_price']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            self.logger.warning(
                f"Quantity data missing columns: {missing_cols}. "
                f"Available columns: {list(df.columns)}"
            )
        
        return df
    
    def load_margin_rates(self) -> pd.DataFrame:
        """
        Load margin rates for ROI calculation.
        
        Returns:
            DataFrame with margin rates
        """
        if not self.config.use_roi:
            self.logger.info("ROI calculation disabled, skipping margin data load")
            return pd.DataFrame()
        
        self.logger.info("Loading margin rates...")
        
        # Load from repository
        period_label = self.config.period_label or f"{self.config.target_yyyymm}{self.config.target_period}"
        df = self.margin_repo.load_margin_rates(period_label)
        
        return df
    
    def load_all_data(self) -> dict:
        """
        Load all required data for analysis.
        
        Convenience method that loads all data sources.
        
        Returns:
            Dictionary with all loaded DataFrames:
            - cluster_df: Clustering assignments
            - sales_df: Sales data (possibly blended)
            - quantity_df: Quantity and price data
            - margin_df: Margin rates (if ROI enabled)
        """
        self.logger.info("Loading all data sources...")
        
        data = {
            'cluster_df': self.load_clustering_data(),
            'sales_df': self.load_sales_data(),
            'quantity_df': self.load_quantity_data(),
            'margin_df': self.load_margin_rates()
        }
        
        self.logger.info("All data sources loaded successfully")
        
        return data
