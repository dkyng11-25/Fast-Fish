"""
Matrix Processor

Handles data filtering, matrix creation, and normalization for clustering analysis.
Supports both subcategory-level and SPU-level matrix creation with memory management.
"""

import pandas as pd
import numpy as np
import os
from typing import Tuple, List, Optional
from datetime import datetime

from core.logger import PipelineLogger


class MatrixProcessor:
    """
    Processor for creating and normalizing matrices for clustering analysis.
    """
    
    def __init__(self, logger: PipelineLogger):
        from ..config_new.output_config import get_output_config

        self.logger = logger
        self.class_name = "MatrixProcessor"
        self.output_config = get_output_config()
        
        # Matrix creation parameters
        self.min_stores_per_subcategory = 5
        self.min_subcategories_per_store = 3
        self.min_stores_per_spu = 3
        self.min_spus_per_store = 10
        self.min_spu_sales_amount = 1.0
        self.max_spu_count = 1000  # Limit SPU matrix size for memory management
    
    def filter_subcategory_data(self, df: pd.DataFrame, anomaly_stores: List[str]) -> pd.DataFrame:
        """
        Filter subcategory data based on prevalence and store criteria.
        
        Args:
            df: Raw subcategory data
            anomaly_stores: List of anomalous store codes to exclude
            
        Returns:
            Filtered subcategory data
        """
        self.logger.info("Processing subcategory-level data", self.class_name)
        self.logger.info(f"Loaded subcategory data with {len(df):,} rows and {df['str_code'].nunique()} stores", self.class_name)
        
        # Filter subcategories that appear in at least MIN_STORES_PER_SUBCATEGORY stores
        subcategory_counts = df['sub_cate_name'].value_counts()
        valid_subcategories = subcategory_counts[subcategory_counts >= self.min_stores_per_subcategory].index
        df_filtered = df[df['sub_cate_name'].isin(valid_subcategories)]
        
        self.logger.info(f"Found {len(valid_subcategories)} subcategories that appear in at least {self.min_stores_per_subcategory} stores", self.class_name)
        self.logger.info(f"Filtered subcategory data has {len(df_filtered):,} rows and {df_filtered['str_code'].nunique()} stores", self.class_name)
        
        # Filter stores that have at least MIN_SUBCATEGORIES_PER_STORE subcategories
        store_subcategory_counts = df_filtered['str_code'].value_counts()
        valid_stores = store_subcategory_counts[store_subcategory_counts >= self.min_subcategories_per_store].index
        df_filtered = df_filtered[df_filtered['str_code'].isin(valid_stores)]
        
        self.logger.info(f"Found {len(valid_stores)} stores with at least {self.min_subcategories_per_store} subcategories", self.class_name)
        self.logger.info(f"Filtered subcategory data has {len(df_filtered):,} rows", self.class_name)
        
        # Remove anomaly stores
        df_filtered = df_filtered[~df_filtered['str_code'].isin(anomaly_stores)]
        self.logger.info(f"Removed {len(anomaly_stores)} anomaly stores from the dataset", self.class_name)
        self.logger.info(f"Dataset now contains {df_filtered['str_code'].nunique()} stores", self.class_name)
        
        return df_filtered
    
    def filter_spu_data(self, df: pd.DataFrame, anomaly_stores: List[str]) -> pd.DataFrame:
        """
        Filter SPU data based on prevalence and store criteria.
        
        Args:
            df: Raw SPU data
            anomaly_stores: List of anomalous store codes to exclude
            
        Returns:
            Filtered SPU data
        """
        self.logger.info("Filtering SPUs based on prevalence and sales volume", self.class_name)
        
        # Filter SPUs by prevalence (appear in at least MIN_STORES_PER_SPU stores)
        spu_store_counts = df['spu_code'].value_counts()
        spus_by_prevalence = spu_store_counts[spu_store_counts >= self.min_stores_per_spu].index
        
        # Filter SPUs by sales volume (total sales across all stores)
        spu_sales_totals = df.groupby('spu_code')['spu_sales_amt'].sum()
        sales_threshold = spu_sales_totals.quantile(0.1)  # Bottom 10% threshold
        spus_by_sales = spu_sales_totals[spu_sales_totals >= sales_threshold].index
        
        # Combine both criteria
        valid_spus = set(spus_by_prevalence) & set(spus_by_sales)
        
        self.logger.info(f"SPU filtering results:", self.class_name)
        self.logger.info(f"  • SPUs by prevalence (≥{self.min_stores_per_spu} stores): {len(spus_by_prevalence)}", self.class_name)
        self.logger.info(f"  • SPUs by sales volume (≥{sales_threshold:.0f}): {len(spus_by_sales)}", self.class_name)
        self.logger.info(f"  • Final SPUs to keep: {len(valid_spus)}", self.class_name)
        
        df_filtered = df[df['spu_code'].isin(valid_spus)]
        self.logger.info(f"Filtered SPU data has {len(df_filtered):,} rows from {df_filtered['str_code'].nunique()} stores", self.class_name)
        
        # Filter stores that have at least MIN_SPUS_PER_STORE SPUs
        store_spu_counts = df_filtered['str_code'].value_counts()
        valid_stores = store_spu_counts[store_spu_counts >= self.min_spus_per_store].index
        df_filtered = df_filtered[df_filtered['str_code'].isin(valid_stores)]
        
        self.logger.info(f"Found {len(valid_stores)} stores with at least {self.min_spus_per_store} SPUs", self.class_name)
        self.logger.info(f"Filtered SPU data has {len(df_filtered):,} rows", self.class_name)
        
        # Remove anomaly stores
        df_filtered = df_filtered[~df_filtered['str_code'].isin(anomaly_stores)]
        self.logger.info(f"Removed {len(anomaly_stores)} anomaly stores from the dataset", self.class_name)
        self.logger.info(f"Dataset now contains {df_filtered['str_code'].nunique()} stores", self.class_name)
        
        return df_filtered
    
    def create_matrix(self, df: pd.DataFrame, index_col: str, columns_col: str, values_col: str, matrix_type: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Create and normalize a pivot matrix from the data.
        
        Args:
            df: Input data
            index_col: Column to use as index (stores)
            columns_col: Column to use as columns (products)
            values_col: Column to use as values (sales)
            matrix_type: Type of matrix for logging
            
        Returns:
            Tuple of (original_matrix, normalized_matrix)
        """
        unique_products = df[columns_col].nunique()
        unique_stores = df[index_col].nunique()
        
        # Check if we need to limit SPU count for memory management
        if matrix_type.startswith('spu') and unique_products > self.max_spu_count:
            self.logger.info(f"Estimated {matrix_type} matrix size: {unique_stores * unique_products / 1024**2:.1f} MB ({unique_stores} stores × {unique_products} SPUs)", self.class_name)
            self.logger.info(f"SPU count ({unique_products}) exceeds limit ({self.max_spu_count})", self.class_name)
            self.logger.info(f"Creating limited SPU matrix and category-aggregated matrix", self.class_name)
            
            # Create limited SPU matrix
            self.logger.info("Creating SPU pivot matrix", self.class_name)
            self.logger.info(f"Limiting to top {self.max_spu_count} SPUs by sales volume for memory management", self.class_name)
            
            # Get top SPUs by total sales
            top_spus = df.groupby(columns_col)[values_col].sum().nlargest(self.max_spu_count).index
            df_limited = df[df[columns_col].isin(top_spus)]
            self.logger.info(f"Filtered to {len(df_limited):,} records with top {self.max_spu_count} SPUs", self.class_name)
            
            self.logger.info("Creating pivot table (this may take a few minutes for large datasets)", self.class_name)
            matrix = df_limited.pivot_table(index=index_col, columns=columns_col, values=values_col, fill_value=0, aggfunc='sum')
            matrix_type = f"{matrix_type}_limited"
            
        else:
            self.logger.info(f"Creating {matrix_type} pivot matrix", self.class_name)
            self.logger.info("Creating pivot table (this may take a few minutes for large datasets)", self.class_name)
            matrix = df.pivot_table(index=index_col, columns=columns_col, values=values_col, fill_value=0, aggfunc='sum')
        
        self.logger.info(f"Created {matrix_type} matrix with {matrix.shape[0]} stores and {matrix.shape[1]} {columns_col.replace('_', ' ')}s", self.class_name)
        
        # Normalize the matrix
        self.logger.info(f"Normalizing {matrix_type} matrix", self.class_name)
        normalized_matrix = matrix.div(matrix.sum(axis=1), axis=0).fillna(0)
        self.logger.info(f"Normalized {matrix_type} matrix", self.class_name)
        
        return matrix, normalized_matrix
    
    def create_category_aggregated_matrix(self, spu_df: pd.DataFrame, anomaly_stores: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Create category-aggregated matrix from SPU data.
        
        Args:
            spu_df: SPU sales data
            anomaly_stores: List of anomalous store codes to exclude
            
        Returns:
            Tuple of (original_matrix, normalized_matrix)
        """
        self.logger.info("Creating category-aggregated SPU matrix", self.class_name)
        
        # Remove anomaly stores
        spu_df_clean = spu_df[~spu_df['str_code'].isin(anomaly_stores)]
        
        # Aggregate SPU sales by category
        category_agg = spu_df_clean.groupby(['str_code', 'cate_name'])['spu_sales_amt'].sum().reset_index()
        
        # Create category matrix
        category_matrix = category_agg.pivot_table(index='str_code', columns='cate_name', values='spu_sales_amt', fill_value=0, aggfunc='sum')
        self.logger.info(f"Created category-aggregated matrix with {category_matrix.shape[0]} stores and {category_matrix.shape[1]} categories", self.class_name)
        
        # Normalize the matrix
        self.logger.info("Normalizing category-aggregated matrix", self.class_name)
        normalized_category_matrix = category_matrix.div(category_matrix.sum(axis=1), axis=0).fillna(0)
        self.logger.info("Normalized category-aggregated matrix", self.class_name)
        
        return category_matrix, normalized_category_matrix
    
    def save_matrix_files(self, original_matrix: pd.DataFrame, normalized_matrix: pd.DataFrame, matrix_type: str) -> None:
        """
        Save matrix files and related data.
        
        Args:
            original_matrix: Original matrix
            normalized_matrix: Normalized matrix
            matrix_type: Type of matrix for file naming
        """
        # Ensure output directory exists
        os.makedirs(self.output_config.step3_output_dir, exist_ok=True)

        # Save matrices
        original_file = self.output_config.get_step3_file_path(f"store_{matrix_type}_matrix.csv")
        normalized_file = self.output_config.get_step3_file_path(f"normalized_{matrix_type}_matrix.csv")

        original_matrix.to_csv(original_file)
        self.logger.info(f"Saved original {matrix_type} matrix to {original_file}", self.class_name)

        normalized_matrix.to_csv(normalized_file)
        self.logger.info(f"Saved normalized {matrix_type} matrix to {normalized_file}", self.class_name)

        # Save store list
        store_list_file = self.output_config.get_step3_file_path(f"{matrix_type}_store_list.txt")
        with open(store_list_file, 'w') as f:
            for store in original_matrix.index:
                f.write(f"{store}\n")
        self.logger.info(f"Saved {matrix_type} store list to {store_list_file}", self.class_name)

        # Save product list
        if matrix_type == "subcategory":
            product_list_file = self.output_config.get_step3_file_path("subcategory_list.txt")
        elif matrix_type == "category_agg":
            product_list_file = self.output_config.get_step3_file_path("category_list.txt")
        else:
            product_list_file = self.output_config.get_step3_file_path("category_list.txt")  # For SPU matrices, save category list

        with open(product_list_file, 'w') as f:
            for product in original_matrix.columns:
                f.write(f"{product}\n")
        self.logger.info(f"Saved {matrix_type.replace('_', ' ')} list to {product_list_file}", self.class_name)
    
    def get_memory_usage(self, df: pd.DataFrame) -> str:
        """
        Get memory usage of DataFrame in MB.
        
        Args:
            df: DataFrame to check
            
        Returns:
            String representation of memory usage
        """
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        return f"{memory_mb:.1f} MB"
