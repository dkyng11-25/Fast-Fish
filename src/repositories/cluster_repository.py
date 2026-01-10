"""Repository for clustering data access."""

import fireducks.pandas as pd
from typing import Optional
from pathlib import Path


class ClusterRepository:
    """Repository for accessing clustering results."""
    
    def __init__(self, csv_repo, logger):
        """
        Initialize cluster repository.
        
        Args:
            csv_repo: CSV file repository for file operations
            logger: Pipeline logger instance
        """
        self.csv_repo = csv_repo
        self.logger = logger
    
    def load_clustering_results(self, period_label: str, analysis_level: str = 'subcategory') -> pd.DataFrame:
        """
        Load clustering results with fallback chain.
        
        Tries in order:
        1. Period-specific: clustering_results_{period_label}.csv
        2. Analysis-level specific: clustering_results_{analysis_level}.csv
        3. Generic: clustering_results.csv
        4. Legacy: cluster_results.csv
        5. Enhanced: cluster_results_enhanced.csv
        
        Args:
            period_label: Period identifier (e.g., '202510A')
            analysis_level: Analysis level ('subcategory' or 'spu')
            
        Returns:
            DataFrame with clustering results
            
        Raises:
            FileNotFoundError: If no clustering file found
        """
        filenames = [
            f"clustering_results_{period_label}.csv",
            f"clustering_results_{analysis_level}.csv",
            "clustering_results.csv",
            f"cluster_results_{period_label}.csv",
            "cluster_results.csv",
            "cluster_results_enhanced.csv"
        ]
        
        for filename in filenames:
            try:
                df = self.csv_repo.load(filename)
                self.logger.info(f"Loaded clustering results from: {filename}")
                return self._normalize_cluster_column(df)
            except FileNotFoundError:
                continue
        
        # If we get here, none of the files were found
        raise FileNotFoundError(
            f"No clustering results found. Tried:\n" +
            "\n".join(f"  - {fn}" for fn in filenames)
        )
    
    def _normalize_cluster_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize cluster column name to 'cluster_id'.
        
        Handles both 'Cluster' and 'cluster_id' column names.
        
        Args:
            df: DataFrame with clustering data
            
        Returns:
            DataFrame with normalized column name
            
        Raises:
            ValueError: If cluster_id column missing after normalization
        """
        # Rename 'Cluster' to 'cluster_id' if present
        if 'Cluster' in df.columns and 'cluster_id' not in df.columns:
            df = df.rename(columns={'Cluster': 'cluster_id'})
            self.logger.info("Normalized 'Cluster' column to 'cluster_id'")
        
        # Validate cluster_id exists
        if 'cluster_id' not in df.columns:
            raise ValueError(
                f"Clustering data missing 'cluster_id' column. "
                f"Available columns: {list(df.columns)}"
            )
        
        # Validate str_code exists
        if 'str_code' not in df.columns:
            raise ValueError(
                f"Clustering data missing 'str_code' column. "
                f"Available columns: {list(df.columns)}"
            )
        
        self.logger.info(
            f"Clustering data loaded: {len(df)} stores, "
            f"{df['cluster_id'].nunique()} clusters"
        )
        
        return df
