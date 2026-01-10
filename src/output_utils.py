"""
Output Utilities for Standardized Pipeline Outputs
===================================================

This module provides utilities for creating standardized output files
with timestamps and symlinks across all pipeline steps.

Standard Pattern:
1. PRIMARY: file_YYYYMMA_YYYYMMDD_HHMMSS.csv (timestamped, preserved)
2. SYMLINK: file_YYYYMMA.csv -> timestamped file (for downstream)
3. SYMLINK: file.csv -> timestamped file (for backward compatibility)
"""

import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional, Union


def create_output_with_symlinks(
    df: pd.DataFrame,
    base_path: str,
    period_label: str,
    file_extension: str = ".csv",
    create_generic: bool = True,
    **save_kwargs
) -> Tuple[str, str, Optional[str]]:
    """
    Create timestamped output file with period-labeled and generic symlinks.
    
    This is the STANDARD way to save pipeline outputs. It ensures:
    - All runs are preserved (timestamped files)
    - Downstream steps work (period-labeled symlink)
    - Backward compatibility (generic symlink)
    
    Args:
        df: DataFrame to save
        base_path: Base path without extension (e.g., "output/rule10_results")
        period_label: Period label (e.g., "202510A")
        file_extension: File extension (default: ".csv")
        create_generic: Whether to create generic symlink (default: True)
        **save_kwargs: Additional arguments passed to save function
    
    Returns:
        tuple: (timestamped_file, period_file, generic_file)
               generic_file is None if create_generic=False
    
    Example:
        >>> df = pd.DataFrame({'a': [1, 2, 3]})
        >>> timestamped, period, generic = create_output_with_symlinks(
        ...     df, "output/rule10_results", "202510A"
        ... )
        >>> # Creates:
        >>> # - output/rule10_results_202510A_20251002_135757.csv (real file)
        >>> # - output/rule10_results_202510A.csv (symlink)
        >>> # - output/rule10_results.csv (symlink)
    """
    # Ensure output directory exists
    base_dir = os.path.dirname(base_path)
    if base_dir:
        os.makedirs(base_dir, exist_ok=True)
    
    # 1. Create timestamped file (PRIMARY - preserved across runs)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamped_file = f"{base_path}_{period_label}_{timestamp}{file_extension}"
    
    # Determine if we should save the index
    # Matrix files need to preserve the index (store codes)
    save_index = 'matrix' in base_path.lower()
    
    # Save based on file extension
    if file_extension == ".csv":
        df.to_csv(timestamped_file, index=save_index, **save_kwargs)
    elif file_extension in [".xlsx", ".xls"]:
        df.to_excel(timestamped_file, index=save_index, **save_kwargs)
    elif file_extension == ".json":
        df.to_json(timestamped_file, orient="records", indent=2, **save_kwargs)
    elif file_extension == ".parquet":
        df.to_parquet(timestamped_file, index=save_index, **save_kwargs)
    else:
        raise ValueError(f"Unsupported file extension: {file_extension}")
    
    # 2. Create period-labeled symlink (for downstream steps)
    period_file = f"{base_path}_{period_label}{file_extension}"
    _create_symlink(timestamped_file, period_file)
    
    # 3. Create generic symlink (for backward compatibility)
    generic_file = None
    if create_generic:
        generic_file = f"{base_path}{file_extension}"
        _create_symlink(timestamped_file, generic_file)
    
    return timestamped_file, period_file, generic_file


def save_text_with_symlinks(
    content: str,
    base_path: str,
    period_label: str,
    file_extension: str = ".md",
    create_generic: bool = True
) -> Tuple[str, str, Optional[str]]:
    """
    Save text content with timestamped file and symlinks.
    
    Similar to create_output_with_symlinks but for text files (MD, JSON, etc.)
    
    Args:
        content: Text content to save
        base_path: Base path without extension
        period_label: Period label (e.g., "202510A")
        file_extension: File extension (default: ".md")
        create_generic: Whether to create generic symlink (default: True)
    
    Returns:
        tuple: (timestamped_file, period_file, generic_file)
    """
    # Ensure output directory exists
    base_dir = os.path.dirname(base_path)
    if base_dir:
        os.makedirs(base_dir, exist_ok=True)
    
    # 1. Create timestamped file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamped_file = f"{base_path}_{period_label}_{timestamp}{file_extension}"
    
    with open(timestamped_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 2. Create period-labeled symlink
    period_file = f"{base_path}_{period_label}{file_extension}"
    _create_symlink(timestamped_file, period_file)
    
    # 3. Create generic symlink
    generic_file = None
    if create_generic:
        generic_file = f"{base_path}{file_extension}"
        _create_symlink(timestamped_file, generic_file)
    
    return timestamped_file, period_file, generic_file


def _create_symlink(source: str, target: str) -> None:
    """
    Create a symlink, removing existing file/symlink if necessary.
    
    Args:
        source: Source file (must exist)
        target: Target symlink path
    """
    # Remove existing target if it exists
    if os.path.exists(target) or os.path.islink(target):
        os.remove(target)
    
    # Create symlink (relative path for portability)
    source_basename = os.path.basename(source)
    target_dir = os.path.dirname(target)
    
    if target_dir:
        # If target is in a subdirectory, use relative path
        os.symlink(source_basename, target)
    else:
        # If target is in same directory, use basename
        os.symlink(source_basename, target)


def get_latest_output(
    base_path: str,
    period_label: str,
    file_extension: str = ".csv"
) -> Optional[str]:
    """
    Get the latest timestamped output file for a given base path and period.
    
    Args:
        base_path: Base path without extension
        period_label: Period label (e.g., "202510A")
        file_extension: File extension (default: ".csv")
    
    Returns:
        Path to latest timestamped file, or None if not found
    
    Example:
        >>> latest = get_latest_output("output/rule10_results", "202510A")
        >>> # Returns: output/rule10_results_202510A_20251002_135757.csv
    """
    import glob
    
    pattern = f"{base_path}_{period_label}_*{file_extension}"
    matching_files = glob.glob(pattern)
    
    if not matching_files:
        return None
    
    # Sort by filename (timestamp is in filename, so this works)
    return sorted(matching_files)[-1]


def cleanup_old_outputs(
    base_path: str,
    period_label: str,
    file_extension: str = ".csv",
    keep_last_n: int = 5
) -> int:
    """
    Clean up old timestamped output files, keeping only the most recent N.
    
    Args:
        base_path: Base path without extension
        period_label: Period label (e.g., "202510A")
        file_extension: File extension (default: ".csv")
        keep_last_n: Number of recent files to keep (default: 5)
    
    Returns:
        Number of files deleted
    
    Example:
        >>> deleted = cleanup_old_outputs("output/rule10_results", "202510A", keep_last_n=3)
        >>> print(f"Deleted {deleted} old files")
    """
    import glob
    
    pattern = f"{base_path}_{period_label}_*{file_extension}"
    matching_files = sorted(glob.glob(pattern))
    
    if len(matching_files) <= keep_last_n:
        return 0
    
    # Delete oldest files
    files_to_delete = matching_files[:-keep_last_n]
    for file_path in files_to_delete:
        os.remove(file_path)
    
    return len(files_to_delete)


# Backward compatibility aliases
create_timestamped_output = create_output_with_symlinks
save_with_symlinks = create_output_with_symlinks
