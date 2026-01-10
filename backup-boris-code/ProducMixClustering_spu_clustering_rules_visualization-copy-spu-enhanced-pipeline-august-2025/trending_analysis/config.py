#!/usr/bin/env python3
"""
Shared Configuration Module for Product Mix Clustering Pipeline

This module provides centralized configuration management for file paths,
periods, and other settings used across all pipeline steps. It ensures
consistency when switching between different time periods and analysis levels.

Author: Data Pipeline
Date: 2025-06-16
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime

# ——— GLOBAL CONFIGURATION ———

# Current analysis period (can be overridden by environment variables or command line)
DEFAULT_YYYYMM = "202506B"  # June 2025
DEFAULT_PERIOD = "A"       # "A" for first half, "B" for second half, None for full month

# Enhanced Analysis level configuration with hierarchical support
DEFAULT_ANALYSIS_LEVEL = "category"  # Options: "category" (default), "spu"
SECONDARY_ANALYSIS_LEVEL = "spu"     # Secondary analysis for dual processing

# Unified Hierarchical Analysis Configuration (replaces bloated dual analysis)
UNIFIED_ANALYSIS_CONFIG = {
    'default_view': 'category',  # Users start with category view
    'available_views': ['overall', 'cluster', 'store', 'category', 'spu'],
    'hierarchical_navigation': True,
    'single_pipeline': True,  # One pipeline generates all levels
    'validation_required': True,
    'business_rules': [7, 8, 9, 10, 11, 12],  # Applied once to all levels
    'output_format': 'hierarchical_json'  # Single file with all levels
}

# ——— ENHANCEMENT CONFIGURATIONS ———

# Quantity data integration configuration
QUANTITY_DATA_CONFIG = {
    'base_sal_qty_field': 'base_sal_qty',
    'fashion_sal_qty_field': 'fashion_sal_qty', 
    'enable_real_pricing': True,
    'price_range': (20, 150),  # RMB realistic pricing range
    'enable_investment_calc': True,
    'min_investment_threshold': 200,  # RMB
    'max_recommendations_per_store': 15,
    'min_opportunity_score': 0.20,
    'min_z_score_threshold': 1.5
}

# Trend analysis configuration
TREND_ANALYSIS_CONFIG = {
    'enable_comprehensive_trends': True,  # ENABLED for comprehensive trend analysis
    'data_sources': ['sales', 'weather', 'cluster', 'fashion'],
    'output_formats': ['standard', 'fashion_enhanced', 'comprehensive'],
    'trend_dimensions': 10,
    'enable_business_friendly_language': True,
    'enable_confidence_scoring': True,
    'enable_fashion_insights': True,  # ENABLED for fashion trend analysis
    'currency_labeling': '¥',  # RMB currency symbol
    'weather_data_file': 'data/weather_data.csv',
    'fashion_data_file': 'output/fashion_enhanced_suggestions.csv',
    'sales_trends_file': 'output/sales_performance_trends.csv'
}

# Analysis Hierarchy (5 levels)
ANALYSIS_HIERARCHY = {
    'overall': {
        'level': 0,
        'aggregates': ['cluster', 'store', 'category', 'spu'],
        'metrics': ['total_revenue', 'total_stores', 'total_categories', 'total_spus'],
        'view_focus': 'executive_dashboard'
    },
    'cluster': {
        'level': 1,
        'aggregates': ['store', 'category', 'spu'],
        'metrics': ['cluster_revenue', 'store_count', 'avg_revenue_per_store'],
        'view_focus': 'regional_strategy'
    },
    'store': {
        'level': 2,
        'aggregates': ['category', 'spu'],
        'metrics': ['store_revenue', 'category_count', 'spu_count'],
        'view_focus': 'store_management'
    },
    'category': {
        'level': 3,
        'aggregates': ['spu'],
        'metrics': ['category_revenue', 'spu_count', 'avg_unit_price'],
        'view_focus': 'category_strategy'
    },
    'spu': {
        'level': 4,
        'aggregates': [],
        'metrics': ['spu_revenue', 'store_count', 'unit_price'],
        'view_focus': 'product_optimization'
    }
}

# Directory paths
DATA_DIR = "data"
API_DATA_DIR = os.path.join(DATA_DIR, "api_data")
OUTPUT_DIR = "output"
DOCS_DIR = "docs"
VALIDATION_DIR = os.path.join(OUTPUT_DIR, "validation")

# Create validation directory
def ensure_validation_directory():
    """Ensure validation directory exists for testing outputs"""
    os.makedirs(VALIDATION_DIR, exist_ok=True)
    return VALIDATION_DIR

# ——— PERIOD MANAGEMENT ———

def get_period_label(yyyymm: str, period: Optional[str] = None) -> str:
    """
    Generate a period label for file naming.
    
    Args:
        yyyymm: Year-month in YYYYMM format
        period: Period indicator ("A" for first half, "B" for second half, None for full month)
        
    Returns:
        String label for the period (e.g., "202506A", "202506B", "202506")
    """
    # Handle case where yyyymm already includes period (e.g., "202506B")
    if period is None and len(yyyymm) == 7 and yyyymm[-1] in ['A', 'B']:
        return yyyymm
    elif period:
        # Extract base yyyymm if it already has a period suffix
        base_yyyymm = yyyymm[:6] if len(yyyymm) == 7 and yyyymm[-1] in ['A', 'B'] else yyyymm
        return f"{base_yyyymm}{period}"
    return yyyymm

def get_current_period() -> tuple[str, Optional[str]]:
    """
    Get the current analysis period from environment variables or defaults.
    
    Returns:
        Tuple of (yyyymm, period)
    """
    yyyymm = os.environ.get('PIPELINE_YYYYMM', DEFAULT_YYYYMM)
    period = os.environ.get('PIPELINE_PERIOD', DEFAULT_PERIOD)
    
    # Handle 'full' period specification
    if period == 'full':
        period = None
    
    return yyyymm, period

def set_current_period(yyyymm: str, period: Optional[str] = None) -> None:
    """
    Set the current analysis period via environment variables.
    
    Args:
        yyyymm: Year-month in YYYYMM format
        period: Period indicator ("A" for first half, "B" for second half, None for full month)
    """
    os.environ['PIPELINE_YYYYMM'] = yyyymm
    os.environ['PIPELINE_PERIOD'] = period or 'full'

# ——— FILE PATH MANAGEMENT ———

def get_api_data_files(yyyymm: Optional[str] = None, period: Optional[str] = None) -> Dict[str, str]:
    """
    Get API data file paths for the specified period.
    
    Args:
        yyyymm: Year-month in YYYYMM format (defaults to current period)
        period: Period indicator (defaults to current period)
        
    Returns:
        Dictionary of file type to file path mappings
    """
    if yyyymm is None or period is None:
        current_yyyymm, current_period = get_current_period()
        yyyymm = yyyymm or current_yyyymm
        period = period if period is not None else current_period
    
    period_label = get_period_label(yyyymm, period)
    
    return {
        'store_config': os.path.join(API_DATA_DIR, f"store_config_{period_label}.csv"),
        'store_sales': os.path.join(API_DATA_DIR, f"store_sales_{period_label}.csv"),
        'category_sales': os.path.join(API_DATA_DIR, f"complete_category_sales_{period_label}.csv"),
        'spu_sales': os.path.join(API_DATA_DIR, f"complete_spu_sales_detailed_{period_label}.csv"),
        'processed_stores': os.path.join(API_DATA_DIR, f"processed_stores_{period_label}.txt")
    }

def get_output_files(analysis_level: str = DEFAULT_ANALYSIS_LEVEL, 
                    yyyymm: Optional[str] = None, 
                    period: Optional[str] = None) -> Dict[str, str]:
    """
    Get output file paths for the specified analysis level and period.
    
    Args:
        analysis_level: Analysis level ("subcategory" or "spu")
        yyyymm: Year-month in YYYYMM format (defaults to current period)
        period: Period indicator (defaults to current period)
        
    Returns:
        Dictionary of file type to file path mappings
    """
    if yyyymm is None or period is None:
        current_yyyymm, current_period = get_current_period()
        yyyymm = yyyymm or current_yyyymm
        period = period if period is not None else current_period
    
    period_label = get_period_label(yyyymm, period)
    
    return {
        'clustering_results': os.path.join(OUTPUT_DIR, f"clustering_results_{analysis_level}_{period_label}.csv"),
        'cluster_profiles': os.path.join(OUTPUT_DIR, f"cluster_profiles_{analysis_level}_{period_label}.csv"),
        'store_coordinates': os.path.join(DATA_DIR, f"store_coordinates_extended_{period_label}.csv"),
        'spu_mapping': os.path.join(DATA_DIR, f"spu_store_mapping_{period_label}.csv"),
        'spu_metadata': os.path.join(DATA_DIR, f"spu_metadata_{period_label}.csv"),
        'matrix_file': os.path.join(DATA_DIR, f"store_{analysis_level}_matrix_{period_label}.csv")
    }

# ——— BACKWARD COMPATIBILITY ———

def get_legacy_file_paths() -> Dict[str, str]:
    """
    Get legacy file paths for backward compatibility.
    These are the original file names without period labels.
    
    Returns:
        Dictionary of legacy file paths
    """
    return {
        'category_sales_legacy': os.path.join(API_DATA_DIR, "complete_category_sales_202506B.csv"),
        'spu_sales_legacy': os.path.join(API_DATA_DIR, "complete_spu_sales_202506B.csv"),
        'clustering_results_legacy': os.path.join(OUTPUT_DIR, "clustering_results.csv"),
        'store_coordinates_legacy': os.path.join(DATA_DIR, "store_coordinates_extended.csv")
    }

def ensure_backward_compatibility() -> None:
    """
    Create symbolic links or copies for backward compatibility with legacy file names.
    This ensures existing scripts continue to work while new scripts use period-specific names.
    """
    current_yyyymm, current_period = get_current_period()
    api_files = get_api_data_files(current_yyyymm, current_period)
    legacy_files = get_legacy_file_paths()
    
    # Create backward compatibility links for key files
    compatibility_mappings = [
        (api_files['category_sales'], legacy_files['category_sales_legacy']),
        (api_files['spu_sales'], legacy_files['spu_sales_legacy']),
        (api_files['store_config'], os.path.join(API_DATA_DIR, "store_config_data.csv")),
        (api_files['store_sales'], os.path.join(API_DATA_DIR, "store_sales_data.csv")),
    ]
    
    for source_file, target_file in compatibility_mappings:
        if os.path.exists(source_file):
            try:
                # Create a copy for compatibility (safer than symlinks on all systems)
                import shutil
                shutil.copy2(source_file, target_file)
                print(f"[CONFIG] Created compatibility file: {os.path.basename(target_file)}")
            except Exception as e:
                print(f"[CONFIG] Warning: Could not create compatibility file {target_file}: {e}")
        else:
            print(f"[CONFIG] Warning: Source file not found for compatibility: {source_file}")

def update_legacy_file_references() -> None:
    """
    Update hardcoded file references in pipeline steps to use current period files.
    This function can be called to ensure all steps use the correct period-specific files.
    """
    current_yyyymm, current_period = get_current_period()
    period_label = get_period_label(current_yyyymm, current_period)
    
    print(f"[CONFIG] Pipeline configured for period: {period_label}")
    print(f"[CONFIG] All steps will use files with period suffix: {period_label}")
    
    # Set environment variables that steps can check
    os.environ['PIPELINE_PERIOD_LABEL'] = period_label
    os.environ['PIPELINE_CATEGORY_FILE'] = get_api_data_files(current_yyyymm, current_period)['category_sales']
    os.environ['PIPELINE_SPU_FILE'] = get_api_data_files(current_yyyymm, current_period)['spu_sales']

# ——— CONFIGURATION VALIDATION ———

def validate_configuration() -> bool:
    """
    Validate that the current configuration is valid and files exist.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    current_yyyymm, current_period = get_current_period()
    
    # Validate period format
    if len(current_yyyymm) != 6 or not current_yyyymm.isdigit():
        print(f"[ERROR] Invalid YYYYMM format: {current_yyyymm}")
        return False
    
    if current_period and current_period not in ['A', 'B']:
        print(f"[ERROR] Invalid period: {current_period}")
        return False
    
    # Check if required directories exist
    required_dirs = [DATA_DIR, API_DATA_DIR, OUTPUT_DIR]
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"[ERROR] Required directory does not exist: {dir_path}")
            return False
    
    return True

# ——— UTILITY FUNCTIONS ———

def get_period_description(period: Optional[str] = None) -> str:
    """
    Get human-readable description of the period.
    
    Args:
        period: Period indicator ("A" for first half, "B" for second half, None for full month)
        
    Returns:
        Human-readable description
    """
    if period == "A":
        return "first half of month"
    elif period == "B":
        return "second half of month"
    else:
        return "full month"

def log_current_configuration() -> None:
    """Log the current pipeline configuration for debugging."""
    current_yyyymm, current_period = get_current_period()
    period_desc = get_period_description(current_period)
    
    print(f"[CONFIG] Current Period: {current_yyyymm} ({period_desc})")
    print(f"[CONFIG] Period Label: {get_period_label(current_yyyymm, current_period)}")
    print(f"[CONFIG] API Data Directory: {API_DATA_DIR}")
    print(f"[CONFIG] Output Directory: {OUTPUT_DIR}")

# ——— INITIALIZATION ———

def initialize_pipeline_config(yyyymm: Optional[str] = None, 
                              period: Optional[str] = None,
                              analysis_level: Optional[str] = None) -> None:
    """
    Initialize pipeline configuration with specified parameters.
    
    Args:
        yyyymm: Year-month in YYYYMM format
        period: Period indicator ("A" for first half, "B" for second half, None for full month)
        analysis_level: Analysis level ("subcategory" or "spu")
    """
    if yyyymm or period:
        set_current_period(yyyymm or DEFAULT_YYYYMM, period)
    
    if analysis_level:
        os.environ['PIPELINE_ANALYSIS_LEVEL'] = analysis_level
    
    # Validate configuration
    if not validate_configuration():
        raise ValueError("Invalid pipeline configuration")
    
    # Log configuration
    log_current_configuration()
    
    # Ensure directories exist
    os.makedirs(API_DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# ——— ANALYSIS HIERARCHY CONFIGURATION ———

# Analysis hierarchy levels for unified engine
ANALYSIS_HIERARCHY = {
    'overall': {'level': 0, 'name': 'Overall Portfolio'},
    'stores': {'level': 1, 'name': 'Store-Level Analysis'},
    'categories': {'level': 2, 'name': 'Category-Level Analysis'},
    'spus': {'level': 3, 'name': 'SPU-Level Analysis'},
    'clusters': {'level': 4, 'name': 'Cluster-Level Analysis'}
}

# Trend analysis configuration
TREND_ANALYSIS_CONFIG = {
    'enable_comprehensive_analysis': True,
    'enable_fashion_insights': True,
    'enable_weather_integration': True,
    'enable_cluster_integration': True,
    'confidence_threshold': 0.7,
    'trend_dimensions': 10
}

# ——— MODULE INITIALIZATION ———

# Initialize with defaults when module is imported
if __name__ != "__main__":
    try:
        initialize_pipeline_config()
    except Exception as e:
        print(f"[WARNING] Could not initialize pipeline config: {e}") 