#!/usr/bin/env python3
from __future__ import annotations
"""
Shared Configuration Module for Product Mix Clustering Pipeline

This module provides centralized configuration management for file paths,
periods, and other settings used across all pipeline steps. It ensures
consistency when switching between different time periods and analysis levels.

Author: Data Pipeline
Date: 2025-06-16
"""

import os
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

# ——— GLOBAL CONFIGURATION ———

# Current analysis period (configurable via environment variables)
# Provide sensible defaults that can be overridden
DEFAULT_YYYYMM = "202509"  # Default to September 2025
DEFAULT_PERIOD: Optional[str] = "A"  # "A" for first half, "B" for second half, None for full month

# Analysis level configuration
DEFAULT_ANALYSIS_LEVEL = "subcategory"  # Options: "subcategory", "spu"

# Directory paths
DATA_DIR = "data"
API_DATA_DIR = os.path.join(DATA_DIR, "api_data")
OUTPUT_DIR = "output"
DOCS_DIR = "docs"

# Forbidden synthetic combined filenames (global guard)
FORBIDDEN_COMBINED_SUFFIXES = [
    "complete_spu_sales_2025Q2_combined.csv",
    "complete_category_sales_2025Q2_combined.csv",
    "store_config_2025Q2_combined.csv",
    "_combined.csv",
]

# Keep legacy constant names to avoid NameError in old code paths, but disable their use
COMPLETE_SPU_SALES_FILE = None  # forbidden
COMPLETE_CATEGORY_SALES_FILE = None  # forbidden
STORE_CONFIG_FILE = None  # forbidden
COMPLETE_SPU_SALES_FILE_202408 = None  # forbidden legacy
COMPLETE_CATEGORY_SALES_FILE_202408 = None  # forbidden legacy

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
    if period:
        return f"{yyyymm}{period}"
    return yyyymm

def get_current_period() -> tuple[Optional[str], Optional[str]]:
    """
    Get the current analysis period from environment variables or defaults.
    
    Returns:
        Tuple of (yyyymm, period)
    """
    # Prefer explicit target variables first
    yyyymm = os.environ.get('PIPELINE_TARGET_YYYYMM') or os.environ.get('PIPELINE_YYYYMM') or (DEFAULT_YYYYMM or None)
    period = os.environ.get('PIPELINE_TARGET_PERIOD') or os.environ.get('PIPELINE_PERIOD') or DEFAULT_PERIOD
    
    # Handle 'full' period specification
    if period == 'full':
        period = None
    
    return yyyymm, period

# ——— HALF-MONTH PERIOD SEQUENCE GENERATORS ———

def _prev_half_period(yyyymm: str, half: str) -> tuple[str, str]:
    """Return the previous half-month period relative to (yyyymm, half).
    If half == 'A', move to previous month's 'B'. If half == 'B', move to same month's 'A'.
    Handles year/month rollovers.
    """
    if len(yyyymm) != 6 or not yyyymm.isdigit():
        raise ValueError(f"Invalid YYYYMM format: {yyyymm}")
    year = int(yyyymm[:4])
    month = int(yyyymm[4:])
    if half not in ("A", "B"):
        raise ValueError(f"Invalid half period: {half}")

    if half == "A":
        # Go to previous month 'B'
        month -= 1
        if month == 0:
            month = 12
            year -= 1
        return f"{year:04d}{month:02d}", "B"
    else:
        # 'B' -> same month 'A'
        return yyyymm, "A"

def generate_half_month_periods_backward_from_label(start_label: str, count: int, include_start: bool = True) -> List[str]:
    """Generate a list of half-month period labels stepping backward from start_label.

    Args:
        start_label: Combined period label like '202507A' or '202507B'.
        count: Number of half-month periods to return.
        include_start: If True, include start_label as the latest element.

    Returns:
        List of labels in chronological order (oldest -> newest), ending at start_label
        if include_start is True; otherwise ending at the half-month immediately before.
    """
    if not isinstance(start_label, str) or len(start_label) not in (6, 7):
        raise ValueError(f"Invalid start_label: {start_label}")

    if len(start_label) == 6:
        # If only YYYYMM provided, default to 'B' (second half)
        start_yyyymm, start_half = start_label, "B"
    else:
        start_yyyymm, start_half = start_label[:6], start_label[6:]

    labels_rev: List[str] = []
    cur_yyyymm, cur_half = start_yyyymm, start_half

    # Optionally skip including the start period itself
    if not include_start:
        cur_yyyymm, cur_half = _prev_half_period(cur_yyyymm, cur_half)

    while len(labels_rev) < count:
        labels_rev.append(f"{cur_yyyymm}{cur_half}")
        cur_yyyymm, cur_half = _prev_half_period(cur_yyyymm, cur_half)

    return list(reversed(labels_rev))

def generate_half_month_periods_backward(start_yyyymm: str, start_period: Optional[str], count: int, include_start: bool = True) -> List[str]:
    """Generate half-month period sequence stepping backward using separate inputs.

    Convenience wrapper around generate_half_month_periods_backward_from_label.
    If start_period is None, defaults to 'B'.
    """
    half = start_period or "B"
    return generate_half_month_periods_backward_from_label(f"{start_yyyymm}{half}", count, include_start=include_start)

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
    
    paths = {
        'store_config': os.path.join(API_DATA_DIR, f"store_config_{period_label}.csv"),
        'store_sales': os.path.join(API_DATA_DIR, f"store_sales_{period_label}.csv"),
        'category_sales': os.path.join(API_DATA_DIR, f"complete_category_sales_{period_label}.csv"),
        'spu_sales': os.path.join(API_DATA_DIR, f"complete_spu_sales_{period_label}.csv"),
        'processed_stores': os.path.join(API_DATA_DIR, f"processed_stores_{period_label}.txt")
    }
    # Global guard: forbid combined synthetic files
    for key, path in paths.items():
        if any(path.endswith(suf) for suf in FORBIDDEN_COMBINED_SUFFIXES):
            raise RuntimeError(f"Forbidden combined file resolved by get_api_data_files: {path}")
    return paths

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

# ——— PERIOD WINDOW CONFIGURATION ———

def _parse_int_list_env(var_name: str) -> Optional[List[int]]:
    """Parse a comma-separated list of integers from environment variable.
    Returns None if not set or invalid."""
    raw = os.environ.get(var_name)
    if not raw:
        return None
    try:
        items = [s.strip() for s in raw.split(',') if s.strip()]
        return [int(x) for x in items]
    except Exception:
        print(f"[CONFIG] Warning: Could not parse {var_name}='{raw}'. Expected comma-separated integers.")
        return None

def get_period_windows_config() -> Dict[str, Any]:
    """
    Get configuration for current and YoY period windows.

    Environment variables supported (all optional):
      - PIPELINE_CURRENT_WINDOW_SIZE: int, default 6
      - PIPELINE_YOY_WINDOW_SIZE: int, default 6
      - PIPELINE_YOY_LAG_HALF_STEPS: int, default 24 (half-months ~ 1 year)
      - PIPELINE_YOY_SHIFT_AFTER_LAG: int, default 3 (start offset after last year's same half)
      - PIPELINE_CURRENT_OFFSETS: comma-separated ints (overrides computed current window offsets)
      - PIPELINE_YOY_OFFSETS: comma-separated ints (overrides computed YoY offsets)

    Returns:
      Dict with keys: current_window_size, yoy_window_size, yoy_lag_half_steps,
      yoy_shift_after_lag, current_offsets, yoy_offsets
    """
    current_window_size = int(os.environ.get('PIPELINE_CURRENT_WINDOW_SIZE', '6'))
    yoy_window_size = int(os.environ.get('PIPELINE_YOY_WINDOW_SIZE', '6'))
    yoy_lag_half_steps = int(os.environ.get('PIPELINE_YOY_LAG_HALF_STEPS', '24'))
    yoy_shift_after_lag = int(os.environ.get('PIPELINE_YOY_SHIFT_AFTER_LAG', '3'))

    current_offsets = _parse_int_list_env('PIPELINE_CURRENT_OFFSETS')
    yoy_offsets = _parse_int_list_env('PIPELINE_YOY_OFFSETS')

    return {
        'current_window_size': current_window_size,
        'yoy_window_size': yoy_window_size,
        'yoy_lag_half_steps': yoy_lag_half_steps,
        'yoy_shift_after_lag': yoy_shift_after_lag,
        'current_offsets': current_offsets,
        'yoy_offsets': yoy_offsets,
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
        'category_sales_legacy': os.path.join(API_DATA_DIR, "complete_category_sales_202505.csv"),
        'spu_sales_legacy': os.path.join(API_DATA_DIR, "complete_spu_sales_202505.csv"),
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
    # If not set, skip strict validation (steps provide CLI args)
    if not current_yyyymm:
        return True
    
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
    if current_yyyymm:
        period_desc = get_period_description(current_period)
        print(f"[CONFIG] Current Period: {current_yyyymm} ({period_desc})")
        print(f"[CONFIG] Period Label: {get_period_label(current_yyyymm, current_period)}")
    else:
        print("[CONFIG] Current Period: unset (provide via CLI --target-yyyymm/--target-period or env)")
    print(f"[CONFIG] API Data Directory: {API_DATA_DIR}")
    print(f"[CONFIG] Output Directory: {OUTPUT_DIR}")
    # Window configuration
    try:
        _win = get_period_windows_config()
        print(
            "[CONFIG] Period windows: current_size=", _win['current_window_size'],
            ", yoy_size=", _win['yoy_window_size'],
            ", yoy_lag=", _win['yoy_lag_half_steps'],
            ", yoy_shift=", _win['yoy_shift_after_lag'],
        )
        if _win['current_offsets']:
            print(f"[CONFIG] Current offsets override: {_win['current_offsets']}")
        if _win['yoy_offsets']:
            print(f"[CONFIG] YoY offsets override: {_win['yoy_offsets']}")
    except Exception as _e:
        print(f"[CONFIG] Warning logging window config: {_e}")

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

# ——— PERIOD-AWARE REAL SALES LOADING (NO SYNTHETIC DATA) ———

def _resolve_period_label(yyyymm: Optional[str], period: Optional[str]) -> str:
    current_yyyymm, current_period = get_current_period()
    use_yyyymm = yyyymm or current_yyyymm
    use_period = period if period is not None else current_period
    return get_period_label(use_yyyymm, use_period)

def resolve_sales_candidates(period_label: str) -> List[str]:
    """Return ordered candidate paths for period-specific sales files.
    Priority strictly avoids synthetic combined files.
    Order:
      1) output/store_sales_{period_label}.csv (Step 1 store-level splits)
      2) output/complete_spu_sales_{period_label}.csv (Step 1 SPU-level)
      3) data/api_data/complete_spu_sales_{period_label}.csv (raw API export)
    """
    return [
        os.path.join(OUTPUT_DIR, f"store_sales_{period_label}.csv"),
        os.path.join(OUTPUT_DIR, f"complete_spu_sales_{period_label}.csv"),
        os.path.join(API_DATA_DIR, f"complete_spu_sales_{period_label}.csv"),
    ]

def _is_combined_synthetic(path: str) -> bool:
    return path.endswith("complete_spu_sales_2025Q2_combined.csv") or path.endswith("complete_category_sales_2025Q2_combined.csv") or path.endswith("store_config_2025Q2_combined.csv")

def _detect_constant_half_split(df) -> bool:
    """Detects near-constant 50/50 fashion/basic ratios (synthetic signature).
    Uses amount if available, else quantity. Returns True if suspiciously flat.
    """
    import pandas as pd  # local import to avoid global dependency if unused
    frac_series = None
    if {'fashion_sal_amt','basic_sal_amt'}.issubset(df.columns):
        denom = pd.to_numeric(df['fashion_sal_amt'], errors='coerce') + pd.to_numeric(df['basic_sal_amt'], errors='coerce')
        with pd.option_context('mode.use_inf_as_na', True):
            frac_series = (pd.to_numeric(df['fashion_sal_amt'], errors='coerce') / denom).dropna()
    elif {'fashion_sal_qty','basic_sal_qty'}.issubset(df.columns):
        denom = pd.to_numeric(df['fashion_sal_qty'], errors='coerce') + pd.to_numeric(df['basic_sal_qty'], errors='coerce')
        with pd.option_context('mode.use_inf_as_na', True):
            frac_series = (pd.to_numeric(df['fashion_sal_qty'], errors='coerce') / denom).dropna()
    if frac_series is None or frac_series.empty:
        return False
    mean = frac_series.mean()
    std = frac_series.std()
    return abs(mean - 0.5) < 0.02 and (std < 0.02)

def load_enriched_store_attributes(period_label: Optional[str] = None) -> Tuple[Optional[str], Any]:
    """Load enriched store attributes for the given period if available; else latest.
    Returns (path, df) where path may be None if not found.
    """
    import glob
    import pandas as pd
    candidates: List[str] = []
    if period_label:
        candidates.extend(sorted(glob.glob(os.path.join(OUTPUT_DIR, f"enriched_store_attributes_{period_label}_*.csv"))))
        candidates.append(os.path.join(OUTPUT_DIR, f"enriched_store_attributes_{period_label}.csv"))
    # Latest fallback
    candidates.extend(sorted(glob.glob(os.path.join(OUTPUT_DIR, "enriched_store_attributes_*.csv"))))
    candidates.append(os.path.join(OUTPUT_DIR, "enriched_store_attributes.csv"))
    for path in candidates:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, dtype={'str_code': str})
                return path, df
            except Exception:
                continue
    return None, None

def load_sales_df_with_fashion_basic(yyyymm: Optional[str], period: Optional[str], *, require_spu_level: bool = True, required_cols: Optional[List[str]] = None) -> Tuple[str, Any]:
    """Load period-specific sales data and ensure fashion/basic amounts at SPU level without synthetic combined inputs.

    Strategy:
      - Prefer SPU-level from Step 1 (output/complete_spu_sales_{period}.csv).
      - If SPU-level lacks fashion/basic columns, derive them by allocating SPU sales using store-level fashion ratios from enriched attributes (Step 22) or Step 1 store_sales.
      - Forbid any use of 2025Q2 combined synthetic files.

    Returns: (source_path, df)
    """
    import pandas as pd
    period_label = _resolve_period_label(yyyymm, period)
    # 1) Attempt to load SPU-level directly
    spu_candidates = [
        os.path.join(OUTPUT_DIR, f"complete_spu_sales_{period_label}.csv"),
        os.path.join(API_DATA_DIR, f"complete_spu_sales_{period_label}.csv"),
    ]
    for path in spu_candidates:
        if os.path.exists(path):
            df = pd.read_csv(path, dtype={'str_code': str})
            if _is_combined_synthetic(path):
                raise RuntimeError(f"Synthetic combined file is forbidden: {path}")
            # Ensure SPU-level and required cols
            if 'spu_code' not in df.columns:
                continue
            # If fashion/basic present and not constant 50/50, use as-is
            if {'fashion_sal_amt','basic_sal_amt'}.issubset(df.columns) and not _detect_constant_half_split(df):
                if required_cols:
                    missing = [c for c in required_cols if c not in df.columns]
                    if missing:
                        raise ValueError(f"Missing required columns in sales data: {missing} from {path}")
                return path, df
            # Otherwise derive from store ratios
            ratio_path, enriched = load_enriched_store_attributes(period_label)
            if enriched is None or 'str_code' not in enriched.columns or 'fashion_ratio' not in enriched.columns:
                # build from store_sales directly
                store_path = os.path.join(OUTPUT_DIR, f"store_sales_{period_label}.csv")
                if not os.path.exists(store_path):
                    raise FileNotFoundError(f"Missing enriched attributes and store_sales for ratio derivation: looked for {ratio_path or 'enriched not found'} and {store_path}")
                store_df = pd.read_csv(store_path, dtype={'str_code': str})
                # compute per-store fashion ratio from amounts
                if not {'fashion_sal_amt','base_sal_amt'}.issubset(store_df.columns):
                    raise ValueError("Store sales missing fashion/base amount columns for ratio derivation")
                store_df['total_amt'] = pd.to_numeric(store_df['fashion_sal_amt'], errors='coerce').fillna(0) + pd.to_numeric(store_df.get('base_sal_amt'), errors='coerce').fillna(0)
                store_df['fashion_ratio'] = (pd.to_numeric(store_df['fashion_sal_amt'], errors='coerce').fillna(0) / store_df['total_amt']).replace([float('inf')], 0).fillna(0)
                ratio_map = store_df.groupby('str_code')['fashion_ratio'].mean().to_dict()
            else:
                # use enriched ratio (percentage or fraction)
                fr = enriched['fashion_ratio']
                if fr.max() > 1.0:
                    fr = fr / 100.0
                ratio_map = dict(zip(enriched['str_code'].astype(str), fr))
            # allocate
            work = df.copy()
            if 'spu_sales_amt' not in work.columns:
                # try alternative column name
                alt = 'sal_amt' if 'sal_amt' in work.columns else None
                if not alt:
                    raise ValueError("SPU sales file missing 'spu_sales_amt' (or 'sal_amt') for allocation")
                work['spu_sales_amt'] = pd.to_numeric(work[alt], errors='coerce').fillna(0)
            else:
                work['spu_sales_amt'] = pd.to_numeric(work['spu_sales_amt'], errors='coerce').fillna(0)
            work['__fr'] = work['str_code'].astype(str).map(ratio_map).fillna(0.5)
            work['fashion_sal_amt'] = (work['spu_sales_amt'] * work['__fr']).round(2)
            work['basic_sal_amt'] = (work['spu_sales_amt'] - work['fashion_sal_amt']).round(2)
            work.drop(columns=['__fr'], inplace=True)
            if required_cols:
                missing = [c for c in required_cols if c not in work.columns]
                if missing:
                    raise ValueError(f"Missing required columns after allocation: {missing} from {path}")
            if _detect_constant_half_split(work):
                raise RuntimeError("Detected constant ~50/50 fashion/basic after allocation. Check input ratios (enriched/store_sales).")
            return path, work
    # 2) As a last resort, support store-level only if caller allows non-SPU
    if not require_spu_level:
        store_path = os.path.join(OUTPUT_DIR, f"store_sales_{period_label}.csv")
        if os.path.exists(store_path):
            df = pd.read_csv(store_path, dtype={'str_code': str})
            if _is_combined_synthetic(store_path):
                raise RuntimeError(f"Synthetic combined file is forbidden: {store_path}")
            if required_cols:
                missing = [c for c in required_cols if c not in df.columns]
                if missing:
                    raise ValueError(f"Missing required columns in store-level sales: {missing} from {store_path}")
            if _detect_constant_half_split(df):
                raise RuntimeError("Detected constant ~50/50 fashion/basic in store_sales. Recompute Step 22 or check API data.")
            return store_path, df
    raise FileNotFoundError(f"No valid period-specific sales files found for {period_label}. Expected Step 1 outputs in output/ or data/api_data/.")

def load_margin_rates(yyyymm: Optional[str] = None, period: Optional[str] = None, 
                     margin_type: str = 'category') -> pd.DataFrame:
    """
    Load period-aware margin rates with fallback logic.
    
    Args:
        yyyymm: Year-month in YYYYMM format (defaults to current period)
        period: Period indicator (defaults to current period)
        margin_type: Type of margin rates to load ('category' or 'spu')
        
    Returns:
        DataFrame with margin rates, with fallback to default rates where real data is missing
    """
    def log_progress(message: str) -> None:
        """Simple logging function for progress messages."""
        print(f"[MARGIN] {message}")
    
    if yyyymm is None or period is None:
        current_yyyymm, current_period = get_current_period()
        yyyymm = yyyymm or current_yyyymm
        period = period if period is not None else current_period
    
    period_label = get_period_label(yyyymm, period)
    log_progress(f"Loading margin rates for period {period_label} (type: {margin_type})")
    
    # Try to derive margin rates from existing data files
    margin_df = None
    
    # 1. Try SPU-level sales data first
    if margin_type == 'spu':
        spu_files = [
            os.path.join(OUTPUT_DIR, f"complete_spu_sales_{period_label}.csv"),
            os.path.join(API_DATA_DIR, f"complete_spu_sales_{period_label}.csv"),
        ]
        
        for path in spu_files:
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path, dtype={'str_code': str, 'spu_code': str})
                    if 'spu_code' in df.columns and 'unit_price' in df.columns and 'investment_per_unit' in df.columns:
                        # Derive margin rate from unit_price and investment_per_unit
                        df['derived_margin_rate'] = np.where(
                            df['unit_price'] > 0,
                            (df['unit_price'] - df['investment_per_unit']) / df['unit_price'],
                            float(os.environ.get('MARGIN_RATE_DEFAULT', '0.45'))
                        )
                        margin_df = df[['str_code', 'spu_code', 'derived_margin_rate']].copy()
                        margin_df.columns = ['str_code', 'spu_code', 'margin_rate']
                        margin_df['margin_rate'] = margin_df['margin_rate'].clip(0, 0.95)  # Ensure valid range (<1)
                        log_progress(f"✅ Derived SPU-level margin rates from {path} ({len(margin_df)} records)")
                        break
                except Exception as e:
                    log_progress(f"⚠️ Failed to derive SPU margin rates from {path}: {e}")
    
    # 2. Try category-level sales data
    if margin_df is None:
        category_files = [
            os.path.join(OUTPUT_DIR, f"complete_category_sales_{period_label}.csv"),
            os.path.join(API_DATA_DIR, f"complete_category_sales_{period_label}.csv"),
        ]
        
        for path in category_files:
            if os.path.exists(path):
                try:
                    df = pd.read_csv(path, dtype={'str_code': str})
                    if 'cate_name' in df.columns and 'store_unit_price' in df.columns and 'estimated_quantity' in df.columns:
                        # Derive margin rate from available data (this is a simplified approach)
                        # In a real implementation, you might have actual cost data
                        df['derived_margin_rate'] = float(os.environ.get('MARGIN_RATE_DEFAULT', '0.45'))
                        margin_df = df[['str_code', 'cate_name', 'derived_margin_rate']].copy()
                        margin_df.columns = ['str_code', 'category_name', 'margin_rate']
                        margin_df['margin_rate'] = margin_df['margin_rate'].clip(0, 0.95)  # Ensure valid range (<1)
                        log_progress(f"✅ Using default category-level margin rates from {path} ({len(margin_df)} records)")
                        break
                except Exception as e:
                    log_progress(f"⚠️ Failed to load category margin rates from {path}: {e}")
    
    # 3. Fallback to store-level defaults
    if margin_df is None:
        try:
            # Create a basic margin rate dataframe with defaults
            processed_stores_path = os.path.join(API_DATA_DIR, f"processed_stores_{period_label}.txt")
            if os.path.exists(processed_stores_path):
                with open(processed_stores_path, 'r') as f:
                    store_codes = [line.strip() for line in f.readlines() if line.strip()]
                
                default_margin_rate = float(os.environ.get('MARGIN_RATE_DEFAULT', '0.45'))
                margin_df = pd.DataFrame({
                    'str_code': store_codes,
                    'margin_rate': default_margin_rate
                })
                log_progress(f"⚠️ Using default margin rate {default_margin_rate} for {len(store_codes)} stores")
        except Exception as e:
            log_progress(f"⚠️ Failed to create default margin rates: {e}")
    
    # Final fallback
    if margin_df is None:
        default_margin_rate = float(os.environ.get('MARGIN_RATE_DEFAULT', '0.45'))
        margin_df = pd.DataFrame({
            'margin_rate': [default_margin_rate]
        })
        log_progress(f"⚠️ Using global default margin rate {default_margin_rate}")
    
    return margin_df


# ——— MODULE INITIALIZATION ———

# Initialize only when explicitly requested to avoid unintended defaults
if __name__ != "__main__" and os.environ.get('PIPELINE_AUTO_INIT') == '1':
    try:
        initialize_pipeline_config()
    except Exception as e:
        print(f"[WARNING] Could not initialize pipeline config: {e}")