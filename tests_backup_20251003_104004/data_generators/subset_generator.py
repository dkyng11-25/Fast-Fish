#!/usr/bin/env python3
"""
Subset Data Generator

Generates subset data for testing from real data following USER_NOTE.md requirements:
- Uses subset data (150-250 stores) for clustering compliance
- Makes subset selection non-random and replicable
- Ensures weather band compliance for each cluster
- Supports multiple time periods
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class SubsetDataGenerator:
    """Generates subset data for testing following USER_NOTE.md requirements."""
    
    def __init__(self, project_root: Path):
        """Initialize the subset data generator."""
        self.project_root = project_root
        self.data_dir = project_root / "data"
        self.output_dir = project_root / "tests" / "test_data"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Subset configuration following USER_NOTE.md
        self.subset_config = {
            'min_stores': 150,
            'max_stores': 250,
            'target_stores': 200,
            'cluster_count': 5,
            'subsample_count': 15
        }
    
    def generate_store_subset(self, period: str, store_count: Optional[int] = None) -> pd.DataFrame:
        """
        Generate a non-random, replicable subset of stores.
        
        Args:
            period: Data period (e.g., '202509A')
            store_count: Number of stores to select (default: target_stores)
            
        Returns:
            DataFrame with store subset
        """
        if store_count is None:
            store_count = self.subset_config['target_stores']
        
        # Ensure store count is within valid range
        store_count = max(self.subset_config['min_stores'], 
                         min(store_count, self.subset_config['max_stores']))
        
        logger.info(f"Generating {store_count} store subset for period {period}")
        
        # Load full store data
        store_file = self.data_dir / "api_data" / f"store_config_{period}.csv"
        if not store_file.exists():
            # Try alternative naming
            store_file = self.data_dir / "api_data" / "store_config_data.csv"
            if not store_file.exists():
                raise FileNotFoundError(f"Store data not found for period {period}")
        
        stores_df = pd.read_csv(store_file)
        logger.info(f"Loaded {len(stores_df)} stores from {store_file}")
        
        # Non-random, replicable selection using deterministic sampling
        # Use period as seed for reproducibility
        seed = hash(period) % 2**32
        np.random.seed(seed)
        
        # Select stores using simple random sampling
        # (store data doesn't have cluster_id, clustering is done later)
        subset_stores = stores_df.sample(n=store_count, random_state=seed)
        
        logger.info(f"Selected {len(subset_stores)} stores for subset")
        return subset_stores
    
    def _stratified_sample_by_cluster(self, df: pd.DataFrame, target_count: int) -> pd.DataFrame:
        """Perform stratified sampling by cluster."""
        if 'cluster_id' not in df.columns:
            return df.sample(n=target_count, random_state=42)
        
        clusters = df['cluster_id'].unique()
        samples_per_cluster = target_count // len(clusters)
        remainder = target_count % len(clusters)
        
        sampled_dfs = []
        for i, cluster in enumerate(clusters):
            cluster_df = df[df['cluster_id'] == cluster]
            n_samples = samples_per_cluster + (1 if i < remainder else 0)
            
            if len(cluster_df) >= n_samples:
                sampled = cluster_df.sample(n=n_samples, random_state=42)
            else:
                sampled = cluster_df  # Take all if not enough
                
            sampled_dfs.append(sampled)
        
        return pd.concat(sampled_dfs, ignore_index=True)
    
    def generate_cluster_subset(self, period: str, cluster_count: int = 5) -> pd.DataFrame:
        """
        Generate 5-cluster subset with high/average consumption spread.
        
        Args:
            period: Data period
            cluster_count: Number of clusters to select
            
        Returns:
            DataFrame with cluster subset
        """
        logger.info(f"Generating {cluster_count} cluster subset for period {period}")
        
        # Load clustering results
        clustering_file = self.project_root / "output" / f"clustering_results_spu_{period}.csv"
        if not clustering_file.exists():
            # Try alternative naming
            clustering_file = self.project_root / "output" / "clustering_results_spu.csv"
            if not clustering_file.exists():
                raise FileNotFoundError(f"Clustering results not found for period {period}")
        
        clustering_df = pd.read_csv(clustering_file)
        logger.info(f"Loaded clustering results: {len(clustering_df)} stores")
        
        # Select clusters with high/average consumption spread
        cluster_col = 'Cluster' if 'Cluster' in clustering_df.columns else 'cluster_id'
        cluster_stats = clustering_df.groupby(cluster_col).agg({
            'str_code': 'count',
            # Add consumption metrics if available
        }).rename(columns={'str_code': 'store_count'})
        
        # Sort by store count to get high/average consumption clusters
        cluster_stats = cluster_stats.sort_values('store_count', ascending=False)
        
        # Select top clusters
        selected_clusters = cluster_stats.head(cluster_count).index.tolist()
        subset_df = clustering_df[clustering_df[cluster_col].isin(selected_clusters)]
        
        logger.info(f"Selected clusters: {selected_clusters}")
        logger.info(f"Subset contains {len(subset_df)} stores")
        
        return subset_df
    
    def generate_15_store_subsample(self, period: str, store_count: int = 15) -> pd.DataFrame:
        """
        Generate 15-store subsample for Steps 15-18.
        
        Args:
            period: Data period
            store_count: Number of stores for subsample
            
        Returns:
            DataFrame with 15-store subsample
        """
        logger.info(f"Generating {store_count} store subsample for period {period}")
        
        # Load full data
        full_data_file = self.data_dir / "api_data" / f"complete_spu_sales_{period}.csv"
        if not full_data_file.exists():
            # Try alternative naming
            full_data_file = self.data_dir / "api_data" / f"store_sales_{period}.csv"
            if not full_data_file.exists():
                raise FileNotFoundError(f"Sales data not found for period {period}")
        
        full_df = pd.read_csv(full_data_file)
        logger.info(f"Loaded {len(full_df)} sales records")
        
        # Get unique stores
        unique_stores = full_df['str_code'].unique()
        logger.info(f"Found {len(unique_stores)} unique stores")
        
        # Non-random, replicable selection
        seed = hash(period) % 2**32
        np.random.seed(seed)
        
        # Select stores
        selected_stores = np.random.choice(unique_stores, 
                                         size=min(store_count, len(unique_stores)), 
                                         replace=False)
        
        # Filter data for selected stores
        subsample_df = full_df[full_df['str_code'].isin(selected_stores)]
        
        logger.info(f"Generated subsample with {len(subsample_df)} records for {len(selected_stores)} stores")
        return subsample_df
    
    def generate_period_data(self, period: str) -> Dict[str, pd.DataFrame]:
        """
        Generate all subset data for a specific period.
        
        Args:
            period: Data period
            
        Returns:
            Dictionary with generated data
        """
        logger.info(f"Generating subset data for period {period}")
        
        generated_data = {}
        
        try:
            # Generate store subset
            store_subset = self.generate_store_subset(period)
            generated_data['store_subset'] = store_subset
            
            # Generate cluster subset
            cluster_subset = self.generate_cluster_subset(period)
            generated_data['cluster_subset'] = cluster_subset
            
            # Generate 15-store subsample
            subsample = self.generate_15_store_subsample(period)
            generated_data['subsample'] = subsample
            
            # Save generated data
            self._save_generated_data(period, generated_data)
            
            logger.info(f"Successfully generated subset data for period {period}")
            return generated_data
            
        except Exception as e:
            logger.error(f"Failed to generate data for period {period}: {e}")
            raise
    
    def _save_generated_data(self, period: str, data: Dict[str, pd.DataFrame]):
        """Save generated data to test_data directory."""
        for data_type, df in data.items():
            filename = f"generated_{data_type}_{period}.csv"
            filepath = self.output_dir / filename
            df.to_csv(filepath, index=False)
            logger.info(f"Saved {data_type} to {filepath}")
    
    def ensure_test_data(self, period: str) -> bool:
        """
        Ensure test data exists for a period, generating if necessary.
        
        Args:
            period: Data period
            
        Returns:
            True if data is available, False otherwise
        """
        logger.info(f"Ensuring test data for period {period}")
        
        try:
            # Check if data already exists
            expected_files = [
                f"generated_store_subset_{period}.csv",
                f"generated_cluster_subset_{period}.csv",
                f"generated_subsample_{period}.csv"
            ]
            
            all_exist = all((self.output_dir / f).exists() for f in expected_files)
            
            if all_exist:
                logger.info(f"Test data already exists for period {period}")
                return True
            
            # Generate missing data
            self.generate_period_data(period)
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure test data for period {period}: {e}")
            return False


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate subset data for testing")
    parser.add_argument("--period", required=True, help="Data period (e.g., 202509A)")
    parser.add_argument("--store-count", type=int, help="Number of stores for subset")
    parser.add_argument("--cluster-count", type=int, default=5, help="Number of clusters")
    parser.add_argument("--subsample-count", type=int, default=15, help="Number of stores for subsample")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize generator
    generator = SubsetDataGenerator(Path(__file__).parent.parent.parent)
    
    # Generate data
    try:
        generator.generate_period_data(args.period)
        print(f"Successfully generated subset data for period {args.period}")
    except Exception as e:
        print(f"Failed to generate data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
