#!/usr/bin/env python3
"""
Step 3: Final Optimized Matrix Preparation
==========================================

This module prepares the store-product matrix with final optimizations:

Improvements Applied:
- Improvement B: Log-transform + Row Normalization
  - Reduces skewness from high-volume SPUs
  - Focuses on product mix patterns rather than absolute volumes

Key Features:
- Creates normalized SPU matrix for clustering
- Applies log transformation before row normalization
- Maintains compatibility with downstream clustering

Author: Fast Fish Data Science Team
Date: 2026-01
"""

import pandas as pd
import numpy as np
import os
from typing import Tuple, Optional
from datetime import datetime
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

TOP_SPU_COUNT = 1000  # Number of top SPUs to include


def log_progress(message: str) -> None:
    """Log progress with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


# =============================================================================
# MATRIX CREATION
# =============================================================================

def load_spu_sales(data_path: Path, period: str) -> pd.DataFrame:
    """Load SPU sales data from file."""
    spu_file = data_path / f'complete_spu_sales_{period}.csv'
    
    if not spu_file.exists():
        raise FileNotFoundError(f"SPU sales file not found: {spu_file}")
    
    spu_sales = pd.read_csv(spu_file)
    spu_sales['str_code'] = spu_sales['str_code'].astype(str)
    spu_sales['spu_code'] = spu_sales['spu_code'].astype(str)
    
    log_progress(f"Loaded {len(spu_sales):,} SPU records from {spu_file.name}")
    return spu_sales


def create_spu_matrix(spu_sales: pd.DataFrame) -> pd.DataFrame:
    """
    Create store × SPU matrix from sales data.
    
    Args:
        spu_sales: DataFrame with str_code, spu_code, spu_sales_amt
        
    Returns:
        Pivot matrix with stores as rows, SPUs as columns
    """
    log_progress("Creating SPU matrix...")
    
    matrix = spu_sales.pivot_table(
        index='str_code',
        columns='spu_code',
        values='spu_sales_amt',
        aggfunc='sum',
        fill_value=0
    )
    
    log_progress(f"  Raw matrix shape: {matrix.shape}")
    return matrix


def filter_top_spus(matrix: pd.DataFrame, top_n: int = TOP_SPU_COUNT) -> pd.DataFrame:
    """
    Filter to top N SPUs by total sales.
    
    Args:
        matrix: Store × SPU matrix
        top_n: Number of top SPUs to keep
        
    Returns:
        Filtered matrix with only top SPUs
    """
    top_spus = matrix.sum().nlargest(top_n).index
    filtered = matrix[top_spus]
    
    log_progress(f"  Filtered to top {top_n} SPUs: {filtered.shape}")
    return filtered


def apply_baseline_normalization(matrix: pd.DataFrame) -> pd.DataFrame:
    """
    Apply baseline row-wise normalization (original method).
    
    Each row is divided by its sum, focusing on product mix.
    """
    normalized = matrix.div(matrix.sum(axis=1), axis=0).fillna(0)
    log_progress("  Applied baseline row-wise normalization")
    return normalized


def apply_log_row_normalization(matrix: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Improvement B: Log-transform + Row Normalization.
    
    1. Log-transform: log(1 + x) to reduce skewness
    2. Row-normalize: divide by row sum to focus on mix
    
    This reduces the impact of high-volume SPUs and creates
    more balanced feature representations.
    """
    # Log-transform to reduce skewness
    log_matrix = np.log1p(matrix)
    
    # Row-wise normalization
    normalized = log_matrix.div(log_matrix.sum(axis=1), axis=0).fillna(0)
    
    log_progress("  Applied log-transform + row normalization (Improvement B)")
    return normalized


# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def prepare_matrix_baseline(
    data_path: Path,
    period: str,
    output_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare matrix using baseline method (for comparison).
    
    Args:
        data_path: Path to data directory
        period: Period code (e.g., '202506A')
        output_path: Optional path to save output
        
    Returns:
        Tuple of (normalized_matrix, original_matrix)
    """
    log_progress("="*60)
    log_progress("BASELINE MATRIX PREPARATION")
    log_progress("="*60)
    
    spu_sales = load_spu_sales(data_path, period)
    matrix = create_spu_matrix(spu_sales)
    filtered = filter_top_spus(matrix)
    normalized = apply_baseline_normalization(filtered)
    
    if output_path:
        output_path.mkdir(parents=True, exist_ok=True)
        normalized.to_csv(output_path / f'normalized_spu_matrix_baseline_{period}.csv')
        filtered.to_csv(output_path / f'original_spu_matrix_{period}.csv')
        log_progress(f"Saved matrices to {output_path}")
    
    return normalized, filtered


def prepare_matrix_final(
    data_path: Path,
    period: str,
    output_path: Optional[Path] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare matrix using final optimized method (Improvement B).
    
    Args:
        data_path: Path to data directory
        period: Period code (e.g., '202506A')
        output_path: Optional path to save output
        
    Returns:
        Tuple of (normalized_matrix, original_matrix)
    """
    log_progress("="*60)
    log_progress("FINAL OPTIMIZED MATRIX PREPARATION (Improvement B)")
    log_progress("="*60)
    
    spu_sales = load_spu_sales(data_path, period)
    matrix = create_spu_matrix(spu_sales)
    filtered = filter_top_spus(matrix)
    normalized = apply_log_row_normalization(filtered)
    
    if output_path:
        output_path.mkdir(parents=True, exist_ok=True)
        normalized.to_csv(output_path / f'normalized_spu_matrix_final_{period}.csv')
        filtered.to_csv(output_path / f'original_spu_matrix_{period}.csv')
        log_progress(f"Saved matrices to {output_path}")
    
    return normalized, filtered


if __name__ == '__main__':
    # Example usage
    PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
    DATA_PATH = PROJECT_ROOT / 'docs' / 'Data' / 'step1_api_data_20250917_142743'
    OUTPUT_PATH = PROJECT_ROOT / 'Evelyn' / 'Final' / 'output'
    
    # Run final optimized preparation
    normalized, original = prepare_matrix_final(DATA_PATH, '202506A', OUTPUT_PATH)
    print(f"\nMatrix shape: {normalized.shape}")
