"""Cluster analyzer component for identifying well-selling features."""

import fireducks.pandas as pd
from typing import List
from .config import MissingCategoryConfig


class ClusterAnalyzer:
    """
    Identifies well-selling features per cluster.
    
    A feature is considered "well-selling" in a cluster if:
    1. Enough stores in the cluster are selling it (adoption threshold)
    2. Total sales across the cluster meet minimum threshold
    """
    
    def __init__(self, config: MissingCategoryConfig, logger):
        """
        Initialize cluster analyzer.
        
        Args:
            config: Configuration for the analysis
            logger: Pipeline logger instance
        """
        self.config = config
        self.logger = logger
    
    def identify_well_selling_features(
        self,
        sales_df: pd.DataFrame,
        cluster_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Identify features that are well-selling in each cluster.
        
        Args:
            sales_df: Sales data with str_code, feature, sal_amt
            cluster_df: Clustering data with str_code, cluster_id
            
        Returns:
            DataFrame with well-selling features per cluster:
            - cluster_id
            - feature (sub_cate_name or spu_code)
            - stores_selling (count)
            - total_cluster_sales (sum)
            - pct_stores_selling (percentage)
            - cluster_size (total stores in cluster)
        """
        self.logger.info("Identifying well-selling features per cluster...")
        
        feature_col = self.config.feature_column
        
        # Validate inputs
        if feature_col not in sales_df.columns:
            raise ValueError(
                f"Sales data missing feature column: {feature_col}. "
                f"Available columns: {list(sales_df.columns)}"
            )
        
        # Merge sales with clusters
        merged = pd.merge(
            sales_df,
            cluster_df[['str_code', 'cluster_id']],
            on='str_code',
            how='inner'
        )
        
        self.logger.info(
            f"Merged sales with clusters: {len(merged)} records, "
            f"{merged['cluster_id'].nunique()} clusters"
        )
        
        # Calculate cluster sizes
        cluster_sizes = cluster_df.groupby('cluster_id').size().reset_index(name='cluster_size')
        
        # Group by cluster and feature
        cluster_features = merged.groupby(['cluster_id', feature_col]).agg({
            'str_code': 'nunique',  # Stores selling this feature
            'sal_amt': 'sum'         # Total sales
        }).reset_index()
        
        cluster_features = cluster_features.rename(columns={
            'str_code': 'stores_selling',
            'sal_amt': 'total_cluster_sales'
        })
        
        # Add cluster sizes
        cluster_features = pd.merge(
            cluster_features,
            cluster_sizes,
            on='cluster_id',
            how='left'
        )
        
        # Calculate percentage of stores selling
        cluster_features['pct_stores_selling'] = (
            cluster_features['stores_selling'] / cluster_features['cluster_size']
        )
        
        # Apply thresholds
        well_selling = self._apply_thresholds(cluster_features)
        
        self.logger.info(
            f"Well-selling features identified: {len(well_selling)} "
            f"feature-cluster combinations across {well_selling['cluster_id'].nunique()} clusters"
        )
        
        # Log statistics
        if len(well_selling) > 0:
            avg_adoption = well_selling['pct_stores_selling'].mean()
            avg_sales = well_selling['total_cluster_sales'].mean()
            self.logger.info(
                f"Average adoption: {avg_adoption:.1%}, "
                f"Average sales: ${avg_sales:,.0f}"
            )
        
        return well_selling
    
    def _apply_thresholds(self, cluster_features: pd.DataFrame) -> pd.DataFrame:
        """
        Apply adoption and sales thresholds to filter well-selling features.
        
        Args:
            cluster_features: DataFrame with cluster-feature metrics
            
        Returns:
            Filtered DataFrame with only well-selling features
        """
        initial_count = len(cluster_features)
        
        # Filter by adoption threshold
        filtered = cluster_features[
            cluster_features['pct_stores_selling'] >= self.config.min_cluster_stores_selling
        ].copy()
        
        adoption_filtered = initial_count - len(filtered)
        
        # Filter by sales threshold
        filtered = filtered[
            filtered['total_cluster_sales'] >= self.config.min_cluster_sales_threshold
        ].copy()
        
        sales_filtered = (initial_count - adoption_filtered) - len(filtered)
        
        self.logger.info(
            f"Threshold filtering: {initial_count} → {len(filtered)} features. "
            f"Filtered: {adoption_filtered} by adoption "
            f"({self.config.min_cluster_stores_selling:.0%}), "
            f"{sales_filtered} by sales (${self.config.min_cluster_sales_threshold:,.0f})"
        )
        
        return filtered
    
    def get_cluster_summary(
        self,
        well_selling_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Generate summary statistics per cluster.
        
        Args:
            well_selling_df: DataFrame with well-selling features
            
        Returns:
            DataFrame with cluster-level summary:
            - cluster_id
            - num_well_selling_features
            - avg_adoption_rate
            - total_sales
        """
        if len(well_selling_df) == 0:
            return pd.DataFrame(columns=[
                'cluster_id', 'num_well_selling_features',
                'avg_adoption_rate', 'total_sales'
            ])
        
        summary = well_selling_df.groupby('cluster_id').agg({
            self.config.feature_column: 'count',
            'pct_stores_selling': 'mean',
            'total_cluster_sales': 'sum'
        }).reset_index()
        
        summary = summary.rename(columns={
            self.config.feature_column: 'num_well_selling_features',
            'pct_stores_selling': 'avg_adoption_rate',
            'total_cluster_sales': 'total_sales'
        })
        
        return summary
