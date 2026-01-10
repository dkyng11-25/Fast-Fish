"""
Matrix Repository - Data access for clustering matrices

Provides access to normalized and original matrices for clustering analysis.
Supports multiple matrix types: SPU, subcategory, category-aggregated.

Updated 2025-10-29: Added period-specific file support with fallback to generic files.

Author: Data Pipeline Team
Date: 2025-10-22
"""

import pandas as pd
import os
from typing import Optional
from pathlib import Path


class MatrixRepository:
    """
    Repository for matrix data access.
    
    Supports period-specific files with fallback to generic files:
    - If period_label provided: Try period-specific file first, fall back to generic
    - If period_label not provided: Use generic file only (backward compatible)
    """
    
    # Matrix file paths based on type
    MATRIX_CONFIGS = {
        "subcategory": {
            "normalized": "data/normalized_subcategory_matrix.csv",
            "original": "data/store_subcategory_matrix.csv",
        },
        "spu": {
            "normalized": "data/normalized_spu_limited_matrix.csv",
            "original": "data/store_spu_limited_matrix.csv",
        },
        "category_agg": {
            "normalized": "data/normalized_category_agg_matrix.csv",
            "original": "data/store_category_agg_matrix.csv",
        }
    }
    
    def __init__(self, base_path: str = ".", period_label: Optional[str] = None):
        """
        Initialize the MatrixRepository.
        
        Args:
            base_path: Base path for data files (default: current directory)
            period_label: Optional period label (e.g., "202506A")
                         If provided, will try period-specific files first,
                         then fall back to generic files.
        """
        self.base_path = Path(base_path)
        self.period_label = period_label
    
    def get_normalized_matrix(self, matrix_type: str) -> Optional[pd.DataFrame]:
        """
        Load normalized matrix for the specified type.
        
        Supports period-specific files with fallback to generic files:
        1. If period_label provided: Try period-specific file first
        2. Fall back to generic file if period-specific doesn't exist
        3. Raise FileNotFoundError if neither exists
        
        Args:
            matrix_type: Type of matrix ("spu", "subcategory", "category_agg")
            
        Returns:
            DataFrame with normalized matrix
            
        Raises:
            ValueError: If matrix_type is invalid
            FileNotFoundError: If matrix file doesn't exist
        """
        if matrix_type not in self.MATRIX_CONFIGS:
            raise ValueError(f"Invalid matrix type: {matrix_type}. Must be one of {list(self.MATRIX_CONFIGS.keys())}")
        
        # Try period-specific file first (if period_label provided)
        if self.period_label:
            period_path = self._get_period_specific_path(matrix_type, "normalized")
            if period_path.exists():
                return pd.read_csv(period_path, index_col=0)
        
        # Fall back to generic file
        generic_path = self._get_generic_path(matrix_type, "normalized")
        if generic_path.exists():
            return pd.read_csv(generic_path, index_col=0)
        
        # Neither exists - raise error
        raise FileNotFoundError(f"Normalized matrix not found for {matrix_type}")
    
    def get_original_matrix(self, matrix_type: str) -> Optional[pd.DataFrame]:
        """
        Load original matrix for the specified type.
        
        Supports period-specific files with fallback to generic files:
        1. If period_label provided: Try period-specific file first
        2. Fall back to generic file if period-specific doesn't exist
        3. Raise FileNotFoundError if neither exists
        
        Args:
            matrix_type: Type of matrix ("spu", "subcategory", "category_agg")
            
        Returns:
            DataFrame with original matrix
            
        Raises:
            ValueError: If matrix_type is invalid
            FileNotFoundError: If matrix file doesn't exist
        """
        if matrix_type not in self.MATRIX_CONFIGS:
            raise ValueError(f"Invalid matrix type: {matrix_type}. Must be one of {list(self.MATRIX_CONFIGS.keys())}")
        
        # Try period-specific file first (if period_label provided)
        if self.period_label:
            period_path = self._get_period_specific_path(matrix_type, "original")
            if period_path.exists():
                return pd.read_csv(period_path, index_col=0)
        
        # Fall back to generic file
        generic_path = self._get_generic_path(matrix_type, "original")
        if generic_path.exists():
            return pd.read_csv(generic_path, index_col=0)
        
        # Neither exists - raise error
        raise FileNotFoundError(f"Original matrix not found for {matrix_type}")
    
    def _get_period_specific_path(self, matrix_type: str, variant: str) -> Path:
        """
        Get period-specific file path.
        
        Args:
            matrix_type: Type of matrix ("spu", "subcategory", "category_agg")
            variant: Matrix variant ("normalized" or "original")
            
        Returns:
            Path to period-specific file
            
        Example:
            "data/normalized_subcategory_matrix.csv" 
            -> "data/normalized_subcategory_matrix_202506A.csv"
        """
        base_name = self.MATRIX_CONFIGS[matrix_type][variant]
        # Insert period before .csv extension
        period_name = base_name.replace(".csv", f"_{self.period_label}.csv")
        return self.base_path / period_name
    
    def _get_generic_path(self, matrix_type: str, variant: str) -> Path:
        """
        Get generic file path.
        
        Args:
            matrix_type: Type of matrix ("spu", "subcategory", "category_agg")
            variant: Matrix variant ("normalized" or "original")
            
        Returns:
            Path to generic file
        """
        base_name = self.MATRIX_CONFIGS[matrix_type][variant]
        return self.base_path / base_name
