#!/usr/bin/env python3
"""
Validation Utilities Package

This package contains specialized validation utilities for different aspects of data validation.
Each module focuses on specific validation patterns to improve maintainability.

Author: Data Pipeline
Date: 2025-01-03
"""

# Import all validator functions for backward compatibility
from .core_validators import (
    validate_dataframe,
    validate_dataframe_flexible,
    validate_file,
    validate_file_flexible,
    validate_multiple_files
)

from .summary_validators import (
    get_validation_summary,
    log_validation_summary
)

from .quality_validators import (
    safe_validate,
    validate_with_quality_checks
)

from .domain_validators import (
    validate_time_series_continuity,
    validate_coordinate_consistency,
    validate_sales_consistency
)

__all__ = [
    # Core validators
    'validate_dataframe',
    'validate_dataframe_flexible',
    'validate_file',
    'validate_file_flexible',
    'validate_multiple_files',
    
    # Summary validators
    'get_validation_summary',
    'log_validation_summary',
    
    # Quality validators
    'safe_validate',
    'validate_with_quality_checks',
    
    # Domain validators
    'validate_time_series_continuity',
    'validate_coordinate_consistency',
    'validate_sales_consistency'
]

